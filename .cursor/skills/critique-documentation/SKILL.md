---
name: critique-documentation
description: Analyze a project's documentation (README, user guide, developer guide, how-to articles, docstrings, and Sphinx setup) against the project's documentation rules and produce a report (no edits). Use when the user asks to critique, review, or audit the documentation, or to generate a report for fixing the docs.
---

# Critique Documentation

Analyze all of a project's documentation and produce a **report only** — do not modify any documentation files. The report is intended to be used as a prompt for an AI agent (or developer) to fix the documentation later.

## Scope

- **README** and other repo-root docs (e.g. `CONTRIBUTING`).
- **Narrative docs** under `docs/` (reStructuredText and/or Markdown): the user guide, developer guide, and how-to articles.
- **Docstrings** in the package source (the API reference is generated from them).
- **Sphinx setup**: `docs/conf.py`, the documentation `toctree` structure, and the build (warnings-as-errors and nitpicky).
- **Package:** Assume a standard Python package documented with Sphinx (e.g. `src/` package, `docs/` tree, hosted on a docs site). Adapt if the project uses a different generator.

## Project rules

If the repo contains a `.cursor/rules/` directory, treat these documentation rule files as the authoritative standard and cite them by filename in findings:

- `doc_python.mdc` — the **foundation**: documentation system, prose conventions, Sphinx `conf.py` essentials, docstrings, cross-reference completeness, and the build discipline (`-W` warnings-as-errors **and** `-n` nitpicky). Every other doc rule builds on it.
- `doc_readme.mdc` — the top-level README: badges, the docs-inclusion marker, required sections, quickstart, and links.
- `doc_user_guide.mdc` — the end-user manual: file layout, landing page + `toctree`, required content, configuration, and per-command-line-program references.
- `doc_dev_guide.mdc` — the developer/contributor manual: layout, required chapters, class diagrams, per-module prose, extension recipes, and the API reference.
- `doc_how_to.mdc` — task-focused how-to articles: structure, prerequisites, numbered steps, expected results, and troubleshooting.

Not every project ships every rule. **If a referenced rule file does not exist, ignore the corresponding part of the critique** instead of inventing a standard, and do not report the rule's absence as a finding. For example, if there is no `doc_how_to.mdc`, skip the how-to checks; if there is no `doc_dev_guide.mdc`, skip the developer-guide checks. Critique only against the doc rules that are actually present.

## Checklist for Analysis

Apply these criteria to the documentation set. Map each finding to the rule file it supports (above) and skip any area whose rule is absent.

### 1. Documentation system and build (`doc_python`)

- **Single source tree:** All docs live under one `docs/` tree with one `conf.py`; build outputs are not committed.
- **Sphinx config:** `conf.py` enables the expected extensions (autodoc, napoleon, viewcode, intersphinx, a diagram extension when diagrams are used, and a Markdown parser when Markdown is included). The source root is on `sys.path`; the version derives from package metadata; heavy/optional imports are mocked for autodoc.
- **Build cleanliness:** The docs build clean under BOTH `sphinx-build -W` (warnings-as-errors) and `sphinx-build -n` (nitpicky). Note any warnings, broken `toctree` entries, documents not in any `toctree`, or unresolved cross-references. Note `nitpick_ignore` entries that suppress symbols the project actually owns.
- **Prose conventions:** American spelling; one space after sentence-ending periods; terms defined on first use; **no time-anchored or migration framing** ("new", "legacy", "now", "recently", "backwards compatible"). No unicode smart quotes/em-dashes/arrows inside `.py` files.

### 2. Docstrings and API reference (`doc_python`, `doc_dev_guide`)

- **Coverage:** Every module, class, method, and function has a docstring. Note missing or one-line-only docstrings on public objects.
- **Format:** Google style with `Parameters:` (not `Args:`); `Returns:`/`Raises:` present where applicable; wrapped to the project width; describes observable behavior, not internals.
- **API-reference completeness:** Every public module appears in the autodoc API reference (`automodule` with `:members:`/`:undoc-members:`/`:show-inheritance:`). Note public modules missing from the reference, and thin docstrings that produce a thin reference.

### 3. Cross-reference completeness (`doc_python`)

- **Roles:** Every mention of a code object in narrative prose uses the correct Sphinx role (`:class:`, `:meth:`, `:func:`, `:mod:`, `:attr:`, `:data:`); `:doc:`/`:ref:` link pages and labels. Note bare CamelCase or `module.symbol` text (even in inline literals) used for API symbols.
- **Resolution:** All cross-references resolve under nitpicky mode. Note stale references to renamed/removed objects or moved pages (e.g. relative `:doc:` targets that broke when a page moved into a subdirectory).

### 4. README (`doc_readme`)

- **Format/inclusion:** Markdown; includable into Sphinx with a marker so host-only badges are excluded from the rendered docs; a single top-level title.
- **Required sections (in order):** title, grouped status badges, introduction, features, installation (Python versions, prerequisites, install command), quick start, documentation link + local build, contributing link, license.
- **Content:** Quickstart examples are runnable as written; every shipped command-line program or primary API is mentioned with a pointer to detailed docs; badge/version/entry-point claims match packaging metadata; all links resolve. The README is a summary and entry point, not a manual.

### 5. User guide (`doc_user_guide`)

- **Layout:** Lives in a dedicated `user_guide/` subdirectory; a landing page holds a short intro and a `toctree`; one chapter per feature or per command-line program; instrument/platform/format specifics in clearly named appendix pages; cross-directory `:doc:` targets are absolute, intra-guide ones relative.
- **Required content:** introduction/purpose; an overview of the workflow/pipeline; installation and setup (versions, install commands, prerequisites, environment variables, expected input/output layout); the full configuration model with precedence and defaults; API usage where applicable; examples.
- **Command-line program references:** For each program — name, one-line purpose, basic syntax, EVERY option documented (flag, argument, effect, default, env/config equivalents) grouped by purpose, positional/repeatable/value-set notes, at least one runnable example, and the schema of any structured file it consumes/emits. Note options that drift from the actual argument parser.

### 6. Developer guide (`doc_dev_guide`)

- **Layout:** Lives in a dedicated subdirectory; a landing page lists chapters in reading order, ending with the API reference and contribution guide.
- **Required chapters:** introduction (audience + package overview); annotated repository layout; environment setup (editable install, env vars, running entry points + smoke test, running the test suite with tiers/parallel/single-test, lint/type/format/docs commands and any wrapper, CI/CD, release, contribution workflow); architecture/class hierarchy; per-subsystem chapters; extending the system; coding conventions; API reference.
- **Class diagrams:** At least one class diagram showing principal classes, key members, and relationships, with abstract/dataclass markers, followed by narrative prose. Diagram stays in sync with the code; no cross-references inside the diagram block.
- **Per-module prose:** Each subsystem chapter gives an overview, per-class/per-file description with contracts (methods subclasses must implement and what they return), concrete implementations of each base, important invariants (thread-safety, shared mutable state, units/conventions), and a pointer to the API reference.
- **Extending:** A step-by-step recipe per extension point with a minimal code skeleton and registration instructions.

### 7. How-to articles (`doc_how_to`)

- **Structure:** Action-oriented title; 1-3 sentence intro; prerequisites; numbered steps (one action each, with the exact snippet/command and the observed result); an expected-results summary consistent with the per-step observations; troubleshooting of common failures; related-material links.
- **Audience/consistency:** Written for a user unfamiliar with internals; where a how-to and the user guide cover the same workflow, they are consistent and link to each other rather than duplicating detail.

### 8. Diagrams and figures (`doc_how_to`, `doc_dev_guide`)

- **Use and rendering:** Diagrams are used where a visual is clearer than prose (workflows, pipelines, architecture), placed inline near the relevant section, render in the docs build (validated in their authoring tool), and have descriptive filenames and alt text.

### 9. Change discipline and consistency (`doc_python`)

- **Stale docs:** Documentation matches the current code — no docs for removed features, no references to renamed objects, examples that still run. Note install commands, supported versions, or entry-point lists that disagree across the README, the guides, and packaging metadata.
- **Same-change updates:** New public modules have corresponding API-reference entries; renamed/removed objects have every reference updated.

## Output: Report Format

Produce a single markdown report with the following structure. Do **not** edit any documentation files; only write the report. Omit sections whose rule file is absent, and say so briefly under "Rules applied".

```markdown
# Documentation Critique Report

**Generated:** [date]
**Scope:** README, docs/ (user guide, developer guide, how-tos), docstrings, Sphinx setup
**Rules applied:** [list the doc rule files found; note any absent and therefore skipped]

## Executive summary
- Overall assessment (strengths, main gaps).
- **Build health:** Does the docs build pass under both `-W` (warnings-as-errors) and `-n` (nitpicky)? Summarize warning count and categories.
- High-priority fixes vs. nice-to-have.

## 1. Documentation system and build
[conf.py extensions, source tree, build cleanliness under -W and -n, prose conventions.]

## 2. Docstrings and API reference
[Missing/thin docstrings on public objects; format; API-reference coverage of public modules.]

## 3. Cross-reference completeness
[Bare API symbols in prose; unresolved or stale :class:/:meth:/:doc: references.]

## 4. README
[Sections present/missing; runnable quickstart; links; consistency with packaging metadata.]

## 5. User guide
[Layout; required content; configuration; per-CLI-program option coverage.]

## 6. Developer guide
[Layout; required chapters; class diagrams; per-module prose; extension recipes; API reference.]

## 7. How-to articles
[Structure; prerequisites; steps with observed results; troubleshooting; consistency with the user guide.]

## 8. Diagrams and figures
[Appropriate use, rendering, naming, alt text.]

## 9. Change discipline and consistency
[Stale docs, cross-document disagreements, missing same-change updates.]

## Recommended priorities
1. [Highest impact, feasible first step]
2. [Next]
3. [Next]

## Prompt for an AI agent to fix the documentation

[Self-contained prompt for an AI to apply the fixes. Include:
- The report sections as context.
- **Build gate:** The docs must build clean under BOTH `sphinx-build -W` and `sphinx-build -n` before the work is considered done.
- Instruction to fix documentation according to the report and the present `.cursor/rules/doc_*.mdc` rules, without changing production code behavior.
- Instruction to update every cross-reference and the README/guides in the same change when a symbol or page is renamed or moved.]
```

## Execution steps

1. **Inventory rules:** List the `.cursor/rules/doc_*.mdc` files that exist. Critique only against those; record which are absent so their checklist areas are skipped.
2. **Gather docs:** List the README and `docs/` tree (note the `toctree` structure and which pages are user guide vs. developer guide vs. how-to vs. API reference). Read `docs/conf.py`.
3. **Build:** Run `sphinx-build -W -b html docs <out>` and `sphinx-build -n -b html docs <out>` (or the project's documented build) and capture warnings. If the docs cannot be built in this environment, say so and critique statically.
4. **Read:** Sample the README, each guide landing page and representative chapters, a how-to, and a cross-section of docstrings. Grep for stale references, bare API symbols in prose, and time-anchored phrasing.
5. **Classify:** For each checklist area (1-9), note specific files, sections, and line references or short quotes, and cite the supporting doc rule.
6. **Write:** Produce the full report in the format above, including the "Prompt for an AI agent" section at the end.
7. **Do not:** Change, add, or remove any line in any documentation, source, or config file.

## When to use this skill

- User asks to "critique the documentation", "review the docs", "audit the docs", or "generate a report to fix the documentation".
- User wants a "prompt for an AI to fix the docs" based on the current documentation.
- Use the `python-codebase-analysis` skill instead for a whole-codebase audit, and `critique-test-suite` for the test suite; this skill is the documentation-specific deep dive.
