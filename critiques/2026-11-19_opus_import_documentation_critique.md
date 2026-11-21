# Documentation Critique Report: the OPUS Import Pipeline

**Generated:** 2026-11-19

**Subject:** commit `2794cd36e8b6eab2a244e7c8a197b20095e8bfd8` on branch `db-perf-pr-26a`,
compared with `origin/main` at `0d4482ad` (the merge base).

**Scope:** everything at HEAD that documents the import:

- the developer-guide import chapters `docs/dev_guide_import*.rst`;
- the import material elsewhere in `docs/`: `dev_guide_database_schema.rst`,
  `dev_guide_testing.rst`, `dev_guide_benchmarks.rst`, `dev_guide_config.rst`,
  `dev_guide_layout.rst` and `dev_guide_table_schemas.rst`;
- the user guide's `user_guide_installation.rst`, `user_guide_deployment.rst` and
  `user_guide_database_server.rst`, where they cover running imports;
- the generated `api_opus_import*.rst` reference pages;
- the docstrings, comments and argparse help strings in `src/opus_import/`;
- `src/opus_deploy/server/README.txt` and `deploy.env.template`, where they cover the import;
- the `[import]` table of `src/opus_config/opus.toml.template`.

**Out of scope:** the public web API guide; the `opus_app` and log-analyzer material; the
code and tests themselves, which other reviewers cover; and the top-level `README.md`,
which says nothing specific about the import.

**Rules applied:**

- `CLAUDE.md`, two rules in particular:
  - a comment or docstring describes the code as it is now, never how it came to be;
  - a countable claim is measured, or not made.
- The house rules for guides and READMEs:
  - no issue, PR, branch or plan references;
  - no history words;
  - say what the code does, not what it does not do;
  - no counts that will drift as the data grows;
  - no absolute paths outside the repository.
- `.cursor/rules/doc_python.mdc`, `doc_dev_guide.mdc` and `doc_user_guide.mdc`.
- `doc_readme.mdc` was not applied, because the README is out of scope.
- `doc_how_to.mdc` exists, but `docs/` has no how-to articles (`ls docs | grep -i how`
  prints nothing), so there was nothing to check against it.

**Method:**

1. Read `.cursor/skills/critique-documentation/SKILL.md` and the five `doc_*.mdc` rules.
2. Built the documentation into a scratch directory, with `PYTHONPATH` and `OPUS_CONFIG`
   unset:

   ```text
   venv-head/bin/sphinx-build -W -n --keep-going -b html -d <scratch>/doctrees docs <scratch>/html
   ```

3. Read the import chapters and checked their behavioral claims against the code:
   - defaults, option names and help text against `cli.py` and `import_all.py`;
   - state names against `bundle_registry.py`, `schema_version.py` and `generations.py`;
   - column names against `table_schemas/*.json`;
   - step order and failure handling against `cli.main`;
   - logging behavior against the installed `pdslogger`;
   - id allocation against `do_import_mult.py`.
4. Scanned every `def` and `class` in `src/opus_import` with an AST script for docstring
   coverage.
5. Grepped for history words, issue/PR/plan references, bare API symbols, and lines over the
   width limit.
6. For each finding, decided whether its lines changed on this branch: ran `git blame` on the
   cited lines, then `git merge-base --is-ancestor <commit> origin/main` on each blamed
   commit. In the findings:
   - **branch** means at least one cited line comes from a commit that is not on `origin/main`;
   - **main** means every cited line was already on `main`.
7. Did not open anything under `critiques/` or `plans/`.

## Status at a124e126

This section records which findings commit `a124e126` (branch `db-perf-pr-26`) has fixed.
The findings below were written against `2794cd36` and are kept as written, with that
tree's line numbers; the line numbers in this section are `a124e126`'s. Every status was
checked by reading the pages, docstrings and code at `a124e126`, not taken from commit
messages.

Four squash merges reached the branch after the critiqued tree, and the evidence names the
one that made each fix: `acb22dd4` (`[DB · PR-26a]`), `c8fb9d0c` (`[DB · PR-26b]`),
`56b917e7` (`[DB · PR-26c]`) and `a124e126` (`[DB · PR-26d]`). `2794cd36` is a commit of
the PR-26a branch from before its squash, so it is not an ancestor of `a124e126`; the merge
base is `0eb24745`. Where a fix's commit is named, the old text is present at the commit
before it and absent from it, checked with `git show <commit>:<path> | grep`.

Status keys: **Fixed**, the passage now matches the code or is gone; **Partly fixed**, with
what remains; **Open**, with where the passage is at `a124e126`.

| ID | Status | Evidence at `a124e126` |
| --- | --- | --- |
| D1 | **Fixed** | `acb22dd4`. `docs/dev_guide_import_running.rst:660-662` says a count above the ceiling is lowered to it and named in the `Parallelism` line; `docs/user_guide_installation.rst:826-829` says it is lowered to it. `grep -rn "stops the import before\|exiting non-zero with a fatal message if either" docs/*.rst` prints nothing. |
| D2 | **Fixed** | `a124e126`. `src/opus_import/steps/do_finalize_mult.py:16-22`: an unpinned field's deleted id stays used, because `mult_field.last_id` never goes down; a pinned field's ids are its `mult_options` list's. |
| D3 | **Fixed** | `a124e126`. `docs/user_guide_deployment.rst:1012-1021` uses `@<branch, tag or commit>` throughout; `grep -n "db-perf\|For this branch" docs/*.rst` prints nothing. |
| D4 | **Fixed** | `a124e126`. The refusal now names the finishing steps, `opus_import --finalize`, `--import-dictionary` and `--validate`, then `--write-schema-version` (`src/opus_deploy/server/import_and_deploy/_check_schema_version.sh:36-41`), which is what `src/opus_deploy/server/README.txt:200-207` describes. |
| D5 | **Fixed** | `a124e126`. `docs/dev_guide_import_fixture.rst:161-175` describes the re-import as checking the delete-then-reload; `grep -c -i upsert docs/dev_guide_import_fixture.rst` gives 0. |
| D6 | **Partly fixed** | `c8fb9d0c`. The mult step is now in the `--finalize` help (`src/opus_import/cli.py:245`), `main`'s `Raises:` (`cli.py:1092-1107`), the `FINALIZATION_OPTIONS` comment (`src/opus_import/import_all.py:92-94`) and the running chapter's failure rule (`docs/dev_guide_import_running.rst:739-746`). Remaining: `docs/user_guide_deployment.rst:610-613` still names three failing steps, a failed `param_info` build, dictionary import or validation, and still says several steps report a failure through the log rather than the status, which `_run_finishing_step` (`cli.py:934-960`) no longer allows unless `--ignore-errors`. |
| D7 | **Fixed** | `c8fb9d0c`, by changing the code to match the sentence. `_run_finishing_step` catches `CacheFlushError`, logs it and records the step failed (`src/opus_import/cli.py:957-959`), and the invocation runs its other steps before exiting with failure, so "If emptying the cache fails, the step fails" (`docs/dev_guide_import_running.rst:441-442`) is now accurate, and the failure rule names it (`:742-746`). |
| D8 | **Fixed** | `a124e126`. `docs/dev_guide_import_db.rst:232-239` gives the command that lists the abstract members from the code, and each of the 52 names it prints appears in both the table and the diagram (checked by grepping each name in each). |
| D9 | **Fixed** | `a124e126`. `docs/dev_guide_database_schema.rst:1021` describes importers and writers, and `:1043-1044` say what `progress_at` and `state` hold for a writer. |
| D10 | **Fixed** | `c8fb9d0c`. The sentence is gone; `docs/dev_guide_import_steps.rst:1034-1036` describes the scans as they are. The defect it recorded is fixed in the same commit (combined critique X11). |
| D11 | **Fixed** | `a124e126`. "About an hour" is replaced by one measured run, 3,032 seconds with six importers sharing 24 workers at `cpu_fraction` 0.8 on the Ring-Moon Systems Node's development workstation (`docs/dev_guide_import_running.rst:823-826`, `docs/user_guide_installation.rst:444-446`); `docs/user_guide_deployment.rst:602` links to the latter, and `README.txt` states no duration. The fixture, testing, steps and database-layer figures are gone. The measurement is stated in two places, without a command or result file. |
| D12 | **Partly fixed** | `a124e126`. `docs/user_guide_installation.rst:469-475` names the running chapter's full-run section as the reference for every `opus_import_all` option, which documents each option `import_all.py` defines, and states the pass-through rule: the erase, the registration and the importers receive the options, the finishing and requeue invocations do not. Remaining: the `--help` epilog (`src/opus_import/import_all.py:436-437`) still says any other option is passed to every invocation that reads the holdings, which by the guide's own account includes the finishing and requeue invocations that do not receive them. |
| D13 | **Fixed** | `a124e126`. `docs/dev_guide_layout.rst:53-74` lists every top-level module of `src/opus_import` (each `ls src/opus_import/*.py` basename but `__init__` appears), and the steps docstring (`src/opus_import/steps/__init__.py:1-36`) names every step module; the overview now defers to the steps chapter for the reasons (`docs/dev_guide_import_overview.rst:295-296`). |
| D14 | **Fixed** | `a124e126`. `docs/dev_guide_import_steps.rst:179` says a full import runs several invocations, which may run at once. |
| D15 | **Fixed** | `a124e126`. The scorched-earth list includes `import_process` and the `__prev` tables (`docs/dev_guide_import_steps.rst:1244-1256`), and the teardown summary points to that one order (`:1205-1207`). |
| D16 | **Fixed** | `a124e126`. `docs/dev_guide_import_steps.rst:1167-1170` adds the pending-generation case. |
| D17 | **Fixed** | `a124e126`. `src/opus_import/steps/do_validate.py:741-745` names the two checks that log below error level and says neither fails the step. |
| D18 | **Fixed** | `a124e126`. `src/opus_import/steps/do_import.py:42-47` lists `do_import_pool` with the other internal modules, with no number. |
| D19 | **Fixed** | `a124e126`. `docs/dev_guide_import_config.rst:37-40` calls it the order the import creates the tables and loads their remaining rows, and points to the order they are computed in. |
| D20 | **Fixed** | `a124e126`. `docs/dev_guide_import_running.rst:36-38` names `OPUS_IMPORT_FAULT`, linked to the fault sites; step 7 (`:667-669`) adds the generation commands. |
| D21 | **Fixed** | `a124e126`. `docs/user_guide_deployment.rst:715-719` says the update builds and installs first and `--begin-generation` refuses; `:734-738` adds the stopped rebuild to `promote_generation.sh`'s refusals; `src/opus_deploy/server/README.txt:167-168` says the lock is taken right after reading `deploy.env`. |
| D22 | **Fixed** | `a124e126`. `grep -n "3\.2[0-9]\.[0-9]" src/opus_deploy/server/README.txt` prints nothing; the README uses `==<release>`. |
| D23 | **Partly fixed** | `a124e126`. The fixture and table-schema instances are gone (`grep -n -i "today\|yet\b\|was excused" docs/dev_guide_import_fixture.rst docs/dev_guide_table_schemas.rst` prints nothing), and the `cli.py` comment no longer says "today" or "once it grows them". Remaining: the comment (`src/opus_import/cli.py:1059-1065`) still describes a commented-out line and the condition for enabling it, kept in `a124e126` on purpose, where the recommendation moves the planned change to an issue. |
| D24 | **Fixed** | `a124e126`. None of the three counts is in `docs/dev_guide_import_fixture.rst` (`grep -n "62 and 83\|twelve thousand\|two dozen"` prints nothing). |
| D25 | **Fixed** | `a124e126`. None of the five sentences remains (`grep` for each prints nothing); `docs/user_guide_installation.rst:496-498` says what the scripts import and what to run instead. |
| D26 | **Open** | Left on purpose: the constants it names have no `:data:` target (combined critique X65). The finding's `grep -ohE` command still counts the literal `BUNDLE_INFO` 12 times in `docs/dev_guide_import*.rst`, and no import chapter writes it with a `:data:` role. |
| D27 | **Fixed** | `a124e126`. `docs/dev_guide_database_schema.rst:1003` says `finished_at` is `NULL` while an import of the bundle runs, and `docs/dev_guide_import_overview.rst:282-284` says the search tables are re-created and the cache flushed. The `do_django.py:5` instance was not a defect at `2794cd36`: the sentence continues on line 6, which ends with its period. |
| D28 | **Fixed** | `a124e126`. `grep -n "without this document" docs/dev_guide_database_schema.rst` prints nothing. |
| D29 | **Fixed** | `a124e126`. Each passage is restated as a rule: `docs/dev_guide_import_overview.rst:234-236` (the warnings are emptied at each bundle's start), `:317-319` (a bundle's primary indexes live in one directory), `:630-633` (`ERRORS.log` is the record a run is checked by). |
| D30 | **Fixed** | `a124e126`. `awk 'length > 100' $(git ls-files 'src/opus_import/*.py')` finds 8 lines, none in a docstring: SQL strings and comments in `importdb/mysql.py` and a message in `steps/do_schema_version.py:113`. |
| D31 | **Fixed** | `a124e126`. The comment (`docs/conf.py:259-261`) names the one function and gives the command that lists every function declaring a type parameter `T`. |
| D32 | **Fixed** | `a124e126`. `docs/dev_guide_import_overview.rst:159` and `docs/dev_guide_database_schema.rst:110` link `opus_import.generations` with a `:mod:` role. |
| D33 | **Fixed** | `a124e126`. `src/opus_import/import_all.py:6` uses `<installation>/opus.toml`, and `src/opus_deploy/server/README.txt:116-117` gives the log directory. |

**Totals:** 29 Fixed, 3 Partly fixed (D6, D12, D23), 1 Open (D26).

## Executive summary

The section "Status at a124e126" above records which of these findings have since been fixed.

**Overall.** For its size, the import documentation is unusually thorough and mostly
accurate:

- Nearly every option's default matches `opus_config.config.ImportConfig` and the argparse
  definitions.
- The state names match the code: `pending`, `importing`, `done` and `failed` for bundles;
  `ready` and `appending` for the schema; `writing`, `finalized`, `validated` and `ready`
  for a pending generation.
- Log-line prefixes such as `Import path:`, `Parallelism:` and `Claimed bundle` match.
- The generation-switch order matches `do_generation.py`.
- The fixed numbers match: id-range capacity 100 (`bundle_registry.py:70`), retry pauses
  `RETRY_SLEEPS` (`super.py:95`), refused-command exit status 3 (`do_generation.py:112`),
  and `PINNED_ABSENT_ID` 65535.
- Every module of `opus_import` is in the API reference, because `docs/_ext/opus_api_reference.py`
  walks the packages.

**Where it fails.** The defects are concentrated in material the database-performance work
wrote or touched. Three are high severity:

- Two pages still say a worker count above the ceiling stops the import. HEAD~1 (`41975e73`)
  changed that: the count is now lowered to the ceiling (D1).
- A step module's docstring says finalization frees mult ids for reuse. The counter design,
  and the guide, say the opposite (D2).
- The user guide publishes a review branch name, `@db-perf-pr-23`, as the example for a test
  server (D3).

Below those is a group of medium findings:

- a stale "upsert" description of re-import (D5);
- the mult step left out of every list of failing finishing steps (D6);
- a cache-flush failure described as failing one step, when it aborts the whole invocation (D7);
- a database-contract table that claims to be "the whole database interface" but is missing
  nine abstract methods (D8);
- a known validation bug written into the developer guide, rather than filed (D10).

**Build health.** The build passes both gates: `-W -n --keep-going` gave exit 0 with 0
warnings. The only line in the build log that matches `warning` is MyST printing its own
configuration, which contains `suppress_warnings`. `nitpicky = True` is set in
`docs/conf.py:103`, and every `nitpick_ignore` entry has a comment. One of them is broader
than it needs to be (D31).

**Docstrings.** 1110 of 2012 `def`s and `class`es have no docstring. That count comes from
an AST walk over `src/opus_import`. All but 2 are `field_obs_*` methods, which
`docs/dev_guide_conventions.rst:89` exempts by convention. The 2 are the nested `key`
functions at `src/opus_import/mult_rank.py:131,153`. No docstring uses `Args:`.

**Findings by severity.** 33 in all.

| Severity | Count | Findings |
| --- | --- | --- |
| critical | 0 | |
| high | 3 | D1-D3 |
| medium | 10 | D4-D13 |
| low | 20 | D14-D33 |

## 1. Documentation system and build (`doc_python`)

- **Build:** clean under `-W` and `-n`. The import pages render, including all five
  import-chapter Mermaid diagrams: `dev_guide_import_overview.rst:21`,
  `dev_guide_import_steps.rst:19`, `dev_guide_import_obs.rst:22`,
  `dev_guide_import_obs_classes.rst:15` and `dev_guide_import_db.rst:30`.
- **`conf.py`:** puts `src/` on `sys.path`, points `OPUS_CONFIG` at the CI dummy when it is
  unset, and generates the API pages at build time, so no module can be left out by hand.
  See D31 for one over-broad `nitpick_ignore`.
- **Prose conventions:** history words, time-anchored phrasing and negative descriptions
  remain; see D23 and D25.
- **Docstring width:** see D30.

## 2. Docstrings and API reference (`doc_python`, `doc_dev_guide`)

- **Coverage:** complete apart from the exempt field methods. See the executive summary.
- **API reference:** generated for every module, including the branch-new ones: the
  generations modules, `bundle_registry`, `coordinator`, `table_swap` and the rest.
- **Accuracy:** several docstrings contradict the code: D2, D6, D17, D18, and part of D33.
  This is where the reference is weakest, because a reader of the API pages has no prose
  chapter to cross-check against.

## 3. Cross-reference completeness (`doc_python` §5)

- Owned constants are written as inline literals rather than `:data:` roles. See D26.
- `opus_import.generations` is never cross-referenced from any guide. See D32.
- Every role that is used resolves, because nitpicky mode is clean.

## 4. README

Out of scope; no import-specific content.

## 5. User guide (`doc_user_guide`)

The user guide covers configuration thoroughly. The `[import]` keys in
`user_guide_installation.rst` and the template match `ImportConfig` key for key; I checked
this by comparing the field list in `src/opus_config/config.py` with the keys in
`opus.toml.template`. The deploy chain's sequence matches the scripts. The gaps are:

- a stale ceiling statement (D1);
- a branch name (D3);
- no option reference for `opus_import_all` (D12);
- a few incomplete lists (D6, D21).

## 6. Developer guide (`doc_dev_guide`)

The import chapters meet the layout rule:

- landing page `dev_guide_import.rst`;
- theory of operation;
- the command line;
- configuration;
- steps;
- the obs hierarchy, with a class diagram followed by narrative;
- the database layer;
- the fixture;
- extension recipes with code skeletons;
- an API pointer at the end of each chapter.

The gaps are:

- the layout tree is missing more than half of `opus_import`'s top-level modules (D13);
- the database contract table and diagram are incomplete (D8);
- the schema chapter describes `import_process` too narrowly (D9);
- the steps chapter has stale or incomplete passages (D14, D15, D16);
- there are defect notes, which the rule forbids (D10, D29).

## 7. How-to articles

There are none, so nothing was checked.

## 8. Diagrams and figures

The five Mermaid diagrams render and each has prose after it. The `ImportDBSuper` class
diagram at `docs/dev_guide_import_db.rst:33-111` is out of sync with the code (D8).

## 9. Change discipline and consistency

Most of the findings are of one kind: a branch change to the code, or to one page, that did
not reach every page or docstring repeating the same fact. Examples are D1, D2, D6, D13 and
D18. The repetition is itself a risk. The same facts are written out in several places:

- the finalization group;
- the step order;
- the import time;
- which failures stop the run.

Each copy drifts on its own.

---

## Findings

### D1. Two pages say a worker count above the ceiling stops the import; the code lowers it

**Severity:** high. **Where:** branch.

**Location:**

- `docs/dev_guide_import_running.rst:632-634`
- `docs/user_guide_installation.rst:819-821`

**Evidence:**

- `dev_guide_import_running.rst:632-634` reads: "Resolves ``workers`` and ``index_workers``
  against the ceiling and logs the ``Parallelism`` line, exiting non-zero with a fatal
  message if either is above it."
- `user_guide_installation.rst:819-821` reads: "a ``workers`` or ``index_workers`` above it
  stops the import before it starts."
- The code:
  - `src/opus_config/config.py:923-925` does `if value > ceiling: capped.append(...); return ceiling`.
  - `src/opus_import/cli.py:1013-1016` logs `parallelism.describe()` and carries on.
  - Commit `41975e73`, "lower a worker count above the ceiling to it", changed this behavior.
    It updated `dev_guide_import_running.rst:98-105`, which now says "lowered to it" (so the
    page contradicts itself), and also `dev_guide_config.rst:36-41`, the template and
    `deploy.env.template`. It did not update these two passages.
- The user guide is the copy operators read.

**Recommendation:**

- `running.rst` step 5: "...and logs the ``Parallelism`` line, lowering either count above
  the ceiling to it (:ref:`dev_guide_import_running_parallelism`)."
- `installation.rst` `cpu_fraction`: "...and a ``workers`` or ``index_workers`` above it is
  lowered to it, which the run's first log line names."
- Grep `docs/` for `stops the import` and `exiting non-zero.*above`.

### D2. `do_finalize_mult` says a deleted mult id is handed out again; the counter never goes down

**Severity:** high. **Where:** branch (`4025a737`).

**Location:** `src/opus_import/steps/do_finalize_mult.py:16-18`, the module docstring. It
appears in the API reference.

**Evidence:**

- The docstring reads: "A deleted id is free again: the next value the import adds to the
  field takes the field's highest id plus one, which can be an id deleted here."
- New ids come from `mult_field.last_id` through `increment_counter`
  (`src/opus_import/steps/do_import_mult.py:556-569`). Nothing in `do_finalize_mult.py`
  touches `last_id`: `grep -n last_id src/opus_import/steps/do_finalize_mult.py` prints nothing.
- The guides say the opposite, correctly:
  - `docs/dev_guide_import_overview.rst:515-516`: "The counter only goes up, so an id it
    handed out is never handed out again, even once finalization deletes its row."
  - `dev_guide_import_overview.rst:575-577`.
  - `docs/dev_guide_import_steps.rst:722`.
- The same docstring's line 14 is 141 characters long (D30).

**Recommendation:**

- Replace the sentence with: "A deleted id stays used: the field's counter, ``mult_field.last_id``,
  never goes down, so the id is not handed out again."
- Rewrap the paragraph.

### D3. The user guide publishes a review branch as its example

**Severity:** high. **Where:** branch.

**Location:** `docs/user_guide_deployment.rst:927-936`

**Evidence:**

- The page says "For this branch, on a test server, an import and a deploy of its database
  and then an incremental update::", followed by `update_deploy_scripts.sh @db-perf-pr-23`,
  `run_full_opus_import.sh @db-perf-pr-23` and
  `deploy_new_code_and_database.sh <database> @db-perf-pr-23`.
- This names a PR branch in a guide, which `doc_user_guide.mdc` §2 and the house rule forbid.
- "this branch" is time-anchored (`doc_python.mdc` §2).
- The example breaks as soon as the branch is deleted.

**Recommendation:** use `@<branch, tag or commit>` placeholders throughout, as the sentence
just above does, and drop "For this branch".

### D4. README.txt's account of the schema-version refusal does not match the refusal

**Severity:** medium. **Where:** branch.

**Location:** `src/opus_deploy/server/README.txt:198-203`

**Evidence:**

- README.txt says a refusal "names the remedy: an import under the new release, or, for a
  database this release imported but did not finish, its finishing steps -- `opus_import
  --finalize`, `--import-dictionary` and `--validate` -- then `opus_import --write-schema-version`."
- The refusal actually prints "Re-import it under this release ... unless this release
  imported it and only the last step is missing"
  (`src/opus_deploy/server/import_and_deploy/_check_schema_version.sh:31-34`). Compare
  `src/opus_import/schema_version.py:37-39`.
- `docs/user_guide_deployment.rst:342-346` warns that stamping without `--finalize` leaves
  the indexes and the duplicate removal undone. README.txt and the message therefore give
  different remedies.

**Recommendation:**

- Make README.txt quote what the refusal says.
- Report the message's incomplete remedy to the code reviewers. It should name the four
  finishing invocations, as README.txt does.

### D5. The fixture chapter describes re-import as an "upsert"

**Severity:** medium. **Where:** main and branch. Lines 164-169 were rewritten on the branch
(`56d510f2`), which kept the word. Lines 175 and 297 are from main.

**Location:** `docs/dev_guide_import_fixture.rst:167-169`, `:175` and `:297`

**Evidence:**

- Line 168 says re-import "runs the *update* half of every upsert on the main run's schema".
- Line 175 says "which is what says the upsert updated the row it found rather than adding another".
- Line 297 says "thousand-row upsert packets".
- On both write paths the import deletes a bundle's rows and loads them again
  (`docs/dev_guide_import_overview.rst:111-120`; `src/opus_import/steps/do_import.py:457-461`).
- Mult values are inserted and never written over (`overview.rst:571-574`).
- `upsert_rows` has exactly one caller, `src/opus_import/steps/do_update_mult_info.py:137`.
  To confirm: `grep -rn "upsert" src/opus_import --include=*.py`.
- The paragraph's own lines 171-172 describe the delete-and-reload correctly, so it now
  contradicts itself.

**Recommendation:** describe the re-import case as checking the delete-then-reload. That
replacement keeps every row of the tables the bundle does not touch, ids included, and
reproduces the bundle's rows apart from their numbering. Drop "upsert" from lines 168, 175
and 297.

### D6. The mult step is missing from every list of what `--finalize` runs and what fails a run

**Severity:** medium. **Where:** branch.

**Location:**

- `src/opus_import/cli.py:241-252`, the `--finalize` help;
- `src/opus_import/cli.py:945-953`, the `main` docstring's `Raises:`;
- `docs/dev_guide_import_running.rst:710-712`;
- `docs/user_guide_deployment.rst:540-541`;
- `src/opus_import/import_all.py:91-96`, the `FINALIZATION_OPTIONS` comment.

**Evidence:**

- The mult step runs under `--finalize` (`cli.py:1208-1216`). Its failure is appended to
  `failed_steps` as "the mult step of --finalize" (`cli.py:1215`), and that makes the
  invocation exit with failure and refuse `--write-schema-version` (`cli.py:1304-1314`,
  `1332-1333`).
- `--create-cart` with a pending generation also fails the invocation (`cli.py:1241-1248`).
- None of the passages below has both:
  - The `--finalize` help lists `--create-indexes`, the duplicate deletion, and five more
    options, but not the mult step.
  - The `main` docstring lists `--create-indexes`, the duplicate step, `--create-param-info`,
    `--update-mult-info`, `--import-dictionary` and `--validate`.
  - `running.rst:710-712` gives the same six.
  - The user guide gives three.
  - The `import_all` comment calls finalization "the secondary keys, one copy of each OPUS
    id, and the auxiliary tables".
- `docs/dev_guide_import_running.rst:144-150` lists the group correctly.

**Recommendation:**

- Add the mult step to the help and to both docstrings.
- In the guides, say "any finishing step that fails" and link to the one list in
  `running.rst`, rather than writing the list out again.

### D7. "If emptying the cache fails, the step fails" understates the effect

**Severity:** medium. **Where:** branch.

**Location:** `docs/dev_guide_import_running.rst:439-440`

**Evidence:**

- `reset_search_tables` raises `CacheFlushError` (`src/opus_import/steps/do_django.py:67-71`).
  `cli.main` does not catch it, so it reaches the top-level handler (`cli.py:1341-1346`),
  which logs it as fatal and exits -1.
- Every later step of the invocation is therefore skipped: `--analyze-tables`,
  `--update-mult-info`, `--validate`, `--import-dictionary` and `--write-schema-version`.
- The step-failure list in `running.rst:710-712` does not mention it.

**Recommendation:** say "If emptying the cache fails, the invocation stops there with a fatal
message and a non-zero exit; the steps after it do not run."

### D8. The `ImportDBSuper` contract table and diagram leave out abstract methods

**Severity:** medium. **Where:** branch. The table is branch text; the methods are branch
additions.

**Location:** `docs/dev_guide_import_db.rst:220`, `:225-351` (the table) and `:33-111` (the
diagram).

**Evidence:**

- Line 220 says `ImportDBSuper` "declares the whole database interface".
- An AST scan of `src/opus_import/importdb/super.py` finds 52 methods whose whole body is
  `raise NotImplementedError`.
- Nine of them have no row in the table. To check: `grep -c <name>` over lines 225-351
  prints 0 for each name except `try_named_lock`, whose one hit is in another row's text:
  - `lock_row`, `set_idle_timeout`, `last_insert_id`;
  - `try_named_lock` (defined at `super.py:722`), `holds_named_lock`, `named_lock_holder`;
  - `carry_over_sessions`, `set_next_id`, `list_junction_mismatches`.
- The diagram lacks those nine, plus `release_named_lock`, `create_obs_general_view`,
  `drop_obs_general_view` and `repoint_cart`.
- The `release_named_lock` row says it frees "a lock try_named_lock took", but
  `try_named_lock` has no row of its own.

**Recommendation:**

- Add a row for each missing method, and update the diagram.
- Better: state the AST command that lists the contract instead of restating it, so the
  table cannot drift again.

### D9. The schema chapter says `import_process` records only queue importers

**Severity:** medium. **Where:** branch.

**Location:** `docs/dev_guide_database_schema.rst:1021`, and `:1043-1044` (`progress_at`,
`state`).

**Evidence:**

- The chapter says the table "records every importer, an ``opus_import --join`` process",
  and that "an importer creates it".
- `register_writer` records "an invocation that writes the schema in ``import_process``"
  (`src/opus_import/steps/do_generation.py:290-291`). `cli.py:1120-1131` calls it for every
  option in `_WRITERS` (`cli.py:662-675`) on a schema with a version row.
- `docs/dev_guide_import_running.rst:558-561` describes this correctly, so the two chapters
  disagree.

**Recommendation:** describe both kinds of row, and say what `progress_at` and `state` mean
for a writer row.

### D10. The developer guide records a known validation bug

**Severity:** medium. **Where:** main (lines 1031-1033, `2e62a929`); the surrounding
paragraph was edited on the branch.

**Location:** `docs/dev_guide_import_steps.rst:1031-1033`

**Evidence:**

- The chapter says: "Both duplicate scans use a subquery that skips its first match, so they
  report a value shared by three or more rows and stay silent about one shared by exactly two."
- The code matches: `LIMIT 1,1` inside the `EXISTS` subqueries in `validate_param_info`
  (`src/opus_import/steps/do_validate.py:237` and `:250`).
- So this is a correct description of a defect. `doc_dev_guide.mdc` §2 forbids
  "known-defect or bug notes" in the guide.

**Recommendation:**

- Remove the sentence.
- Pass the bug to the code reviewers: a pair of duplicate `(category_name, disp_order)` or
  `slug` values is never reported.

### D11. Timings and performance figures are stated without a measurement

**Severity:** medium. **Where:** branch, except the fixture lines.

**Location and evidence:**

- "About an hour" with six importers sharing 24 workers appears in four places:
  - `docs/dev_guide_import_running.rst:790`
  - `docs/user_guide_installation.rst:444`
  - `docs/user_guide_deployment.rst:529`
  - `src/opus_deploy/server/README.txt:110`

  None names a command or a result file. `dev_guide_benchmarks.rst` describes the harness
  that would measure it, but holds no result; `grep -n -i hour docs/dev_guide_benchmarks.rst`
  finds only line 32, "Hours.".
- `dev_guide_import_fixture.rst:17` says "five or six minutes" (branch).
  `dev_guide_testing.rst` says "five or six minutes against the eighteen seconds everything
  else costs".
- `docs/dev_guide_import_steps.rst:770-771` says "took over a third longer".
- `docs/dev_guide_import_db.rst:175-179` says "by up to a factor of three", "one twice as
  slow" and "seconds longer in all".

`CLAUDE.md` says a countable claim is measured or not made, and these figures will drift
with the holdings and the hardware.

**Recommendation:** either cite the benchmark result (label, command and date) once, in
`dev_guide_benchmarks.rst`, and link to it from the other pages, or keep the reasoning and
drop the numbers.

### D12. The user guide has no option reference for `opus_import_all`, and does not say that unknown options are passed on

**Severity:** medium. **Where:** branch.

**Location:** `docs/user_guide_installation.rst`, `docs/user_guide_deployment.rst`; compare
`src/opus_import/import_all.py:428-519`.

**Evidence:**

- `doc_user_guide.mdc` §3 requires every option of every installed program to be documented.
- Over `docs/user_guide_*.rst`, a loop of `grep -c -- "<option>\b"` gives 0 for each of
  `--prepare`, `--finish`, `--watch` and `--yes`.
- `opus_import_all`'s epilog says "Any other option is passed to every opus_import invocation
  that reads the holdings" (`import_all.py:428-430`). Lines 456 and 723 pass those options to
  the erase, the registration and the importers, but not to `--finish` or `--requeue`
  (`import_all.py:258-281`).
- Neither guide says this. A grep of the user guide and `dev_guide_import_running.rst` for
  "passed on", "pass.*on to" or "unrecognized" finds nothing. This matters because
  `--override-db-schema` reaches the closing invocations only through this mechanism.
- For `opus_import`, the user guide defers to `--help` and the developer guide
  (`user_guide_installation.rst:519-521`). That is defensible, but it should be a deliberate,
  stated choice.

**Recommendation:**

- Add an `opus_import_all` reference section to the user guide, built from the argparse
  options, that states the pass-through rule.
- Or state in the user guide that `dev_guide_import_running` is the reference, and make
  that page complete. It does cover `--prepare`, `--join`, `--finish`, `--requeue`,
  `--status`, `--scorched-earth`, `--yes` and `--dry-run`.

### D13. The layout tree and the steps package docstring list less than exists

**Severity:** medium. **Where:** branch.

**Location:**

- `docs/dev_guide_layout.rst:50-71`
- `src/opus_import/steps/__init__.py:1-27`, together with
  `docs/dev_guide_import_overview.rst:293-294`

**Evidence:**

- The annotated tree lists 10 of the 24 top-level modules in `src/opus_import`
  (`ls src/opus_import/*.py | wc -l` gives 24, counting `__init__.py`).
- It leaves out `import_all` (on main), and 12 modules that are new on the branch
  (`git cat-file -e origin/main:src/opus_import/<m>.py` fails for each):
  - `bundle_registry`, `coordinator`, `generations`, `import_fault`;
  - `import_processes`, `list_junctions`, `primary_index`, `schema_version`;
  - `surface_geometry`, `table_keys`, `table_swap`, `validation_queries`.
- The branch did add `deferred.py` to the same tree.
- The steps package docstring leaves out five step modules: `do_register`, `do_recover`,
  `do_carry_over`, `do_generation` and `do_generation_purge`.
- The overview says this docstring "states the whole order and what forces each part of it,
  and is the authority if this summary and it ever disagree". It gives no reasons beyond
  "derived from the imported tables and so must follow it".
- Line 5 of the docstring is 112 characters long.

**Recommendation:**

- Add the missing modules to the tree, grouped: registry and queue, generations, keys and
  swaps, validation.
- Add the missing step modules to the steps docstring, or have the overview stop calling
  it the authority, since `dev_guide_import_steps.rst` "The order, and what forces it" is
  what actually states the reasons.

### D14. The steps chapter describes a full import as "one invocation per bundle group"

**Severity:** low. **Where:** branch.

**Location:** `docs/dev_guide_import_steps.rst:179`

**Evidence:**

- `opus_import_all` registers everything in one `--register-bundles` invocation and then
  runs `--join` importers (`src/opus_import/import_all.py:212`, `:238`).
- `docs/dev_guide_import_running.rst:176` has it right: "several invocations, which may run
  at once".

**Recommendation:** use the running chapter's wording.

### D15. The scorched-earth table list is incomplete, and the page gives two drop orders

**Severity:** low. **Where:** branch.

**Location:** `docs/dev_guide_import_steps.rst:1198-1200` and `:1236-1246`

**Evidence:**

- The exact-name list leaves out `import_process` and `param_info__prev`, `partables__prev`
  and `table_names__prev`, all of which are in `OPUS_TABLE_NAMES`
  (`src/opus_import/steps/do_import_tables.py:56-81`).
- Lines 1198-1200 give one teardown order. Lines 1242-1246, which match the code at
  `do_import_tables.py:142-152` (the view first, then `schema_version`), give another.

**Recommendation:**

- Complete the list, or refer to `:data:` `OPUS_TABLE_NAMES` instead of restating it.
- Make lines 1198-1200 point to 1242-1246.

### D16. The `do_schema_version` section leaves out the pending-generation case

**Severity:** low. **Where:** branch.

**Location:** `docs/dev_guide_import_steps.rst:1157-1166`

**Evidence:**

- The section lists four cases.
- With a pending generation, the step writes neither the version nor the state: it marks the
  generation `ready`, and refuses unless that generation is `validated`
  (`src/opus_import/steps/do_schema_version.py:94-95`, `125-146`).
- `dev_guide_import_running.rst:472-474` covers this case.

**Recommendation:** add the fifth case.

### D17. The `do_validate` docstring says every check logs at error level

**Severity:** low. **Where:** branch.

**Location:** `src/opus_import/steps/do_validate.py:741-742`

**Evidence:**

- The docstring says "each is logged at error level".
- The filter-wavelength consistency check logs at `'warning'` (`do_validate.py:458-462`).
- `docs/dev_guide_import_running.rst:722` correctly says `--validate` "reports some of what
  it finds below error level".

**Recommendation:** say which check logs as a warning, and that a warning does not fail the
step.

### D18. The `do_import` docstring names four internal modules; there are five

**Severity:** low. **Where:** main text, made stale by the branch's addition of
`do_import_pool`.

**Location:** `src/opus_import/steps/do_import.py:42-46`

**Evidence:**

- The docstring says "The per-bundle work is split across four modules" and lists tables,
  index, obs and mult.
- `do_import_pool` is the fifth: `do_import_index.py:38` imports it and `:371` calls it.
  `steps/__init__.py:22` lists it.

**Recommendation:** add `do_import_pool`, and drop the number.

### D19. The config chapter says `TABLES_TO_POPULATE` is "the order it fills them"

**Severity:** low. **Where:** main.

**Location:** `docs/dev_guide_import_config.rst:36`

**Evidence:**

- The import computes the surface-geometry tables and `obs_files` after the rest
  (`src/opus_import/steps/do_import_index.py:645-718`; `docs/dev_guide_import_overview.rst:361-368`).
- So the list is the order the tables are created and finally loaded, not the order they
  are filled.

**Recommendation:** "in the order their rows are loaded; the overview gives the order they
are computed in."

### D20. The running chapter's environment claim and step 7 are incomplete

**Severity:** low. **Where:** main (line 36); branch (lines 639-641).

**Location:** `docs/dev_guide_import_running.rst:36` and `:639-641`

**Evidence:**

- Line 36 says "The pipeline reads nothing else from the environment", but the import reads
  `OPUS_IMPORT_FAULT` (`src/opus_import/import_fault.py:31`). That variable is test-only,
  but `doc_dev_guide.mdc` §2 asks for every environment variable.
- Step 7 says only the carry-over skips the holdings. The generation commands skip them too
  (`cli.py:1082`).

**Recommendation:**

- Name `OPUS_IMPORT_FAULT`, with a link to `dev_guide_testing_faults`.
- Add "or runs a generation command" to step 7.

### D21. Small inaccuracies in the deployment chapter and README.txt

**Severity:** low. **Where:** branch.

**Location and evidence:**

- `docs/user_guide_deployment.rst:643-645` says the incremental update "refuses to start" on
  a pending generation or an unpurged switch. In fact it builds and installs the staged
  installation first, and only `--begin-generation` refuses
  (`_incremental_opus_update_steps.sh:177`).
- `user_guide_deployment.rst:650-653` gives the reasons `promote_generation.sh` refuses, but
  leaves out `unfinished_rebuild_problem` (`src/opus_import/steps/do_generation.py:910-914`).
- `src/opus_deploy/server/README.txt:167-168` says the deploy lock is taken "before it reads
  anything". Each script reads `deploy.env` first; for example
  `deploy_new_code_and_database.sh:53-54` comes after `_read_deploy_env.sh`.
  `user_guide_deployment.rst:276-278` has this right.

**Recommendation:** correct each one as described.

### D22. README.txt hard-codes release numbers that have not been tagged

**Severity:** low. **Where:** mostly main; lines 209 and 260 are branch.

**Location:** `src/opus_deploy/server/README.txt` lines 71, 75, 114, 139, 159, 173, 184,
193, 196, 209 and 260.

**Evidence:**

- These lines use `==3.24.0`, `==3.24.1` and `==3.25.0`. To find them:
  `grep -n "3\.2[0-9]\.[0-9]" src/opus_deploy/server/README.txt`.
- `git tag --sort=-v:refname | head -1` gives `v3.23.0`, so none of those releases exists.

**Recommendation:** use `==<release>` placeholders, as the guides do.

### D23. History and time-anchored wording

**Severity:** low. **Where:** mixed, as marked.

**Location and evidence:**

- `docs/dev_guide_import_fixture.rst:116` and `:120-123` (main): "of which there are none
  today", "No table is excused today", and "``definitions`` was excused while it restated a
  checked-in data file; with that file gone it holds rows...". The last is the history the
  `CLAUDE.md` rule forbids.
- `dev_guide_import_fixture.rst:300` (main): "because production has no PDS4 shelves yet".
- `docs/dev_guide_table_schemas.rst:81` and `:412` (main): "the only one today", "what it
  reports today".
- `src/opus_import/cli.py:910-916` (branch): "so today every PDS4 existence check takes that
  fallback", "or the production tree once it grows them", and "the line below waits until
  every PDS4 bundle in the holdings has one". This comment describes a commented-out line
  and a future change.
- Not every hit is a problem. The domain uses of "new" ("a new value", "a new mission")
  and "as it now is" about MySQL renames are fine.

**Recommendation:**

- Rephrase in the present tense: "The excusal list is empty; its rules are what make an
  entry safe to add."
- Move the planned `require_shelves` change to an issue.

### D24. Counts that will drift

**Severity:** low. **Where:** main.

**Location and evidence:**

- `docs/dev_guide_import_fixture.rst:143-145`: "between 62 and 83 logical paths carry two or
  more different values". This was measured, but no command is given.
- Line 184: "about twelve thousand lines of field methods". `cat src/opus_import/obs/*.py | wc -l`
  gives 11586 lines for the whole `obs/` directory, of which field methods are only part.
- Line 333: "the two dozen the fixture keeps".

**Recommendation:** state the command that regenerates each figure, or describe without the
number ("several logical paths", "the obs layer's field methods").

### D25. Passages that describe what the code does not do

**Severity:** low. **Where:** mixed.

**Location and evidence:**

- `docs/user_guide_installation.rst:489-490`: "There is no partial-import option in them".
- `docs/user_guide_deployment.rst:157-158`: "It does not upgrade anything in place."
- `src/opus_deploy/server/README.txt:181-182`: "Nothing need be written to the database".
- `docs/dev_guide_import_running.rst:732`: "Nothing in the pipeline does this for you".
- `dev_guide_import_running.rst:616`: "nothing else does".
- How often negative phrasing occurs: `grep -cwiE "nothing|never|does not|do not|no longer"`
  gives 81 lines in `dev_guide_import_steps.rst`, 59 in `user_guide_deployment.rst` and 55
  in `dev_guide_import_running.rst`. Many of those lines state real invariants ("never
  handed out again"), which are fine.

**Recommendation:** rewrite the purely negative sentences as positive statements, for example
"These scripts import every bundle set; to import part of the archive, run the pipeline
directly."

### D26. Owned constants written as inline literals instead of `:data:` roles

**Severity:** low. **Where:** mostly main; the steps-chapter instances are branch.

**Location and evidence:**

- `grep -ohE '``[A-Z][A-Z0-9_]{3,}``' docs/dev_guide_import*.rst | sort | uniq -c`
  counts these, among others. The counts include section titles, which are exempt.

  | Constant | Count |
  | --- | --- |
  | ``BUNDLE_INFO`` | 12 |
  | ``INSTRUMENT_ID_TO_MISSION_ID`` | 5 |
  | ``TARGET_NAME_INFO`` | 4 |
  | ``STAR_RA_DEC`` | 4 |
  | ``MISSION_ID_TO_MISSION_TABLE_SFX`` | 4 |
  | ``TARGET_NAME_MAPPING`` | 3 |
  | ``INSTRUMENT_ID_TO_INSTRUMENT_NAME`` | 3 |
  | ``INST_HOST_ID_TO_MISSION_ID`` | 3 |

- `docs/dev_guide_import_steps.rst:781` and `:784` write ``SWAP_LOCK_WAIT_TIMEOUT_S`` and
  ``SWAP_RENAME_ATTEMPTS`` as literals.
- None of the config constants above is ever written with a `:data:` role in the import
  chapters (`grep -c ":data:\`[~.a-z_]*<NAME>\`"` gives 0 for each). `doc_python.mdc` §5
  calls this a violation.

**Recommendation:** use `:data:` roles outside titles and code blocks. The targets exist,
since autodoc's `:undoc-members:` documents module constants.

### D27. Garbled or imprecise sentences

**Severity:** low. **Where:** branch.

**Location and evidence:**

- `docs/dev_guide_database_schema.rst:1003` reads "``NULL`` before the first, and
  ``finished_at`` while one is running". The intended meaning, which
  `bundle_registry.py:389,397` confirms, is that `finished_at` is NULL while an import runs.
- `src/opus_import/steps/do_django.py:5`: the module docstring's first paragraph ends
  "dropped and created again empty" with no period.
- `docs/dev_guide_import_overview.rst:281` says "drop the cache tables". `do_django` drops
  and re-creates the *search* tables, then flushes the cache.

**Recommendation:** reword each one.

### D28. A "may change without this document being updated" disclaimer

**Severity:** low. **Where:** branch.

**Location:** `docs/dev_guide_database_schema.rst:112`

**Evidence:**

- The page says: "note this may change slightly over time without this document being
  updated, so always refer to the actual database". This accepts stale documentation,
  which `doc_python.mdc` §7 forbids.
- The `DESC` listings for these tables do match `table_schemas/*.json`, so the disclaimer is
  not even needed: `obs_general`, `obs_pds`, `obs_mission_cassini`, `mult`, `mult_field`,
  `mult_group`, `schema_version` and `obs_general_target_name`.

**Recommendation:** delete the disclaimer.

### D29. Limitation notes in the overview

**Severity:** low. **Where:** main and branch.

**Location:**

- `docs/dev_guide_import_overview.rst:315-317` (only the first directory holding indexes is
  imported);
- `overview.rst:232-235` (warnings raised outside a PDS3 read are dropped at the next bundle);
- `overview.rst:629-630` (the bad-data flags are "not a complete record" because some steps
  log straight to the logger).

**Evidence:** each is phrased as behavior, but reads as a known limitation, which
`doc_dev_guide.mdc` §2 keeps out of the guide.

**Recommendation:**

- Keep the operational rule: gate on `ERRORS.log`.
- File each gap as an issue, or restate it as a design rule ("a bundle's indexes live in one
  directory").

### D30. Docstring lines over the width limit

**Severity:** low. **Where:** branch.

**Location:**

- `src/opus_import/steps/do_finalize_mult.py:14` (141 characters);
- `src/opus_import/import_all.py:22` (120);
- `src/opus_import/steps/__init__.py:5` (112);
- `src/opus_import/steps/do_generation.py:818` (102).

**Evidence:**

- `awk 'length > 100' $(git ls-files 'src/opus_import/*.py')` finds 12 lines in all. The
  other 8 are code and SQL strings.
- `line-length = 100` is set in `pyproject.toml:419`, and E501 is ignored (`pyproject.toml:477`),
  so nothing gates on this.

**Recommendation:** rewrap the four docstrings.

### D31. An over-broad `nitpick_ignore` entry

**Severity:** low. **Where:** branch.

**Location:** `docs/conf.py`, the `('py:class', 'T')` entry and its comment.

**Evidence:** the entry exists for one TypeVar in `ImportDBSuper.retrying`, but it silences
an unresolved bare `T` anywhere in the tree.

**Recommendation:** accept it, but name the one function in the comment, so that the next
`T` someone adds is noticed.

### D32. `opus_import.generations` is never cross-referenced from the guides

**Severity:** low. **Where:** branch.

**Location:**

- `docs/dev_guide_import_overview.rst:141-183`, which describes the module's contents
  without naming it;
- `docs/dev_guide_database_schema.rst`.

**Evidence:**

- A loop over every `opus_import` module, grepping `docs/dev_guide*.rst` and
  `docs/user_guide*.rst` for its dotted name, finds this one module with no mention.
- It defines `OBS_GENERAL_VIEW` and the `PENDING_*` states that the guides discuss.

**Recommendation:** add a `:mod:` link in the "Generations" section of the overview.

### D33. A misleading example path, and a missing log location

**Severity:** low. **Where:** branch, and main for part of README.txt:116.

**Location and evidence:**

- `src/opus_import/import_all.py:4-6` gives `OPUS_CONFIG` a fixed absolute path, directly
  under the server's top-level OPUS directory. No installation keeps the file there; the
  deploy writes `<OPUS_DIR>/staged/<install>/opus.toml`
  (`docs/user_guide_installation.rst:51-54`).
- `src/opus_deploy/server/README.txt:116` says to read `ERRORS.log` without saying where it
  is (`<OPUS_DIR>/import_logs/<run>/`, per `user_guide_installation.rst:480-482`).

**Recommendation:** use `<installation>/opus.toml` in the docstring, and give the log
location in README.txt.

---

## Recommended priorities

1. **Fix the stale behavior statements that send operators or developers the wrong way:**
   - D1, the ceiling (two passages);
   - D2, mult id reuse;
   - D7, cache-flush failure;
   - D6, the failing-step lists.

   Each is a sentence or two. D6 is best fixed by keeping one list in `dev_guide_import_running.rst`
   and linking to it.
2. **Take the branch name and the defect note out of the guides:** D3, and D10 (with the bug
   passed to the code reviewers).
3. **Bring the reference material level with the branch's new code:**
   - D8, the contract table and diagram, ideally generated or replaced by the command that
     lists the contract;
   - D9, `import_process`;
   - D13, the layout tree and the steps docstring;
   - D14-D16, the steps chapter.
4. **Fix the fixture chapter's upsert description (D5),** and the README.txt refusal text (D4).
5. **Decide on the `opus_import_all` reference (D12),** and document the option pass-through
   either way.
6. **Apply the evidence rule to timing and count claims (D11, D24):** cite the benchmark
   result once and link to it.
7. **Clean up the house-rule items:** D23, D25, D26, D29 and D30-D33.

## Prompt for an AI agent to fix the documentation

You are fixing the OPUS import pipeline's documentation in the rms-opus repository. The
report above lists 33 findings, D1-D33; each gives a location, the code that contradicts the
text, and a recommendation. Context:

- Apply the fixes to the documentation and to docstrings, comments and argparse help text
  only. Do not change any behavior. Two findings point at code defects, and these go to the
  code reviewers or into issues rather than into this change:
  - D4: the remedy text of `_check_schema_version.sh`;
  - D10: the `LIMIT 1,1` duplicate scans in `do_validate.validate_param_info`.
- Follow `CLAUDE.md` and `.cursor/rules/doc_python.mdc`, `doc_dev_guide.mdc` and
  `doc_user_guide.mdc`:
  - describe the software as it is, with no history words and no time anchoring;
  - no issue, PR, branch or plan references in any guide or README;
  - no known-defect notes;
  - every countable claim is measured, with its command given, or removed;
  - owned code objects in prose use Sphinx roles (`:data:`, `:func:`, `:mod:`, and so on),
    not inline literals;
  - docstrings are Google style, with `Parameters:`, wrapped to the project width.
- Where a fact is written out in several places (the finalization group, which failures stop
  a run, the full-import time), keep one authoritative copy and link to it from the others,
  so the copies cannot drift apart again.
- When you change a fact, update every page, docstring and help string that states it, in the
  same change. Use grep to find the copies; for example, D1's appear in both
  `dev_guide_import_running.rst` and `user_guide_installation.rst`.
- Work in priority order, D1-D3 first.
- **Build gate:** the documentation must build clean under BOTH `sphinx-build -W` and
  `sphinx-build -n` before the work is done. Run
  `make clean && make html SPHINXOPTS="-W -n"` from `docs/`, or `scripts/read-docs.sh`, with
  `PYTHONPATH` unset. Then run `scripts/run-all-checks.sh -d`, and `ruff check` and
  `ruff format --check` over any Python file whose docstrings you edited.
