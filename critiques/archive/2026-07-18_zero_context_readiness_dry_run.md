# Critique: Zero-Context Executor Readiness Dry Run (third pass)

- **Reviewer:** Opus-class agent (the actual executor model class), zero inherited context
- **Date:** 2026-07-18
- **Reviewed:** modernization plan rev 6 (as committed to the `rewrite` branch), read only from `PLAN.md` + `CLAUDE.md`
- **Method:** simulated the executor's kickoff ("check out `rewrite`, execute PR-01 per CLAUDE.md") without executing; assessed whether it *could* proceed with nothing but the checked-in briefing
- **Outcome:** GREEN verdict for PR-01; two minor self-containedness gaps found and fixed (§4a reading list; PR-21 README specification)

---

# Zero-Context Readiness Assessment

## (a) VERDICT for PR-01: GREEN — could start executing immediately, no blocking questions

Every resource PR-01 names was verified present and consistent:

**Template repo** `/seti/all_repos/rms-devenv/repo_template` exists and contains exactly what PR-01 copies:
- `.cursor/rules` = 17 files (matches), `.cursor/skills` = 4 skills (matches), `.vscode/` + `.cursor/` settings present
- `codecov.yml`, `.readthedocs.yaml`, `scripts/run-all-checks.sh`, `CONTRIBUTING.md`, issue/PR templates, publish workflows
- Template `run-tests.yml` has the `ruff format --check src tests` step (line 36) PR-01 must delete, and the pymarkdown scan line PR-01 must narrow — both as described
- `run-all-checks.sh` has `ENABLE_RUFF_FORMAT`/`ENABLE_MYPY` defaulting false, as the plan relies on

**Rewrite branch** carries all files PR-01 touches: `PLAN.md` + `CLAUDE.md` present; `run-app-tests.yml` (triggers `[main]`; job `Test OPUS`, matrix self-hosted-linux/3.12) and `run-lint.yml` (job `Run Lint`) — matching the required-check context claims; `.flake8`, `run_flake8.sh`, `CODING_STYLE.md`, `CODE_REVIEW_TEMPLATE.txt`, `create_all_venv.sh`, `test_all_venv.sh`, `LICENSE.md`, `requirements.in` (`django == 4.*`, consistent with the interim pin); `log_analyzer/`, `perf_test/`, `perf_test/stream_c.exe` present.

The one action flagged as possibly out of the executor's reach — updating branch-protection contexts via `gh api` — has an explicit in-plan fallback ("otherwise reported for the orchestrator to do"), so it does not block starting.

## (b) Self-containedness gaps (whole document)

Real (minor) gaps:

1. **§4a's reading list is missing two load-bearing sections.** §4a says read "§1–§3, §4's preamble, its own PR section, and §4a/§5/§6" — omitting §5a (two-coverage-config rule) and the Execution notes appendix (the only carrier of inter-PR state). CLAUDE.md's list is the correct superset. *Fix:* change §4a to "…§4a/§5/§5a/§6, and the Execution notes appendix." **[fixed]**

2. **Template access is "PR-01 only" but PR-21 still says "per template" for the README** — and the template `README.md` is never copied into the repo. *Fix:* specify the README structure via the in-repo `.cursor/rules/doc_readme.mdc` rule instead of template access. **[fixed]**

Cosmetic / not gaps:
- Numerous `file:line` claims are governed by the stop-and-report + mechanical-drift rule, so stale line numbers are handled by design.
- External human/service dependencies are all closed in-text (RTD, PyPI tokens, branch protection).
- All internal navigation resolves: every §-reference (§1, §3, §4, §4a, §5, §5a, §6) and every `PR-NN` reference (01–23) maps to an existing section.

## (c) CLAUDE.md vs PLAN.md contradictions

One real inconsistency, same as gap #1: the two briefings disagreed on the required reading set (CLAUDE.md complete; §4a omitted §5a + Execution notes). Since the assignment routes through CLAUDE.md, an executor obeying it reads everything needed — a documentation discrepancy, not an execution blocker. No other contradictions; on move/modify separation, definition-of-done, the API back-compat waiver, and the append-only Execution-notes rule, the two documents agree.

**Bottom line:** PR-01 is fully executable with zero clarifying questions. The plan is unusually self-contained; the only substantive finding is that §4a under-specified its own reading list relative to CLAUDE.md, plus a soft spot where PR-21 leaned on a template README that PR-01 never copies in. Both fixed.
