# The OPUS import pipeline: the 2026-11-19 critiques compared with the 2026-09-01 critique

**Date:** 2026-11-19

**Tree assessed:** `2794cd36e8b6eab2a244e7c8a197b20095e8bfd8` (branch `db-perf-pr-26a`), verified
with `git rev-parse HEAD`. 95 commits are reachable from it and not from the earlier
critique's tree (`git rev-list --count 2bfc2a0e..HEAD`); that tree is not an ancestor of HEAD,
because merges are squashed.

**Earlier tree:** `2bfc2a0e57d4ccb1465775e8e32a7f564d1f2bb1`. Every "before" count below that
is not quoted from the earlier critique was measured on an extract of that tree
(`git archive 2bfc2a0e`), with the same command as the "after" count.

**"New" and "pre-existing":** against `origin/main` at `0d4482ad`, the merge base of the
branch. `2bfc2a0e` is not an ancestor of `origin/main`, because merges are squashed. Between
them, `src/opus_import` differs only in `import_all.py`, `cli.py` and `obs/obs_base.py`
(`git diff --stat 2bfc2a0e origin/main -- src/opus_import`). The deploy chain
(`src/opus_deploy/`), the user guide and `docs/dev_guide_import_overview.rst` reached `main` in
`2e62a929`, after the earlier critique's tree.

Inputs compared:

| Era | Document | Scope |
| --- | --- | --- |
| Before | `2026-09-01_opus_import_codebase_analysis.md` | `src/opus_import`, `src/opus_support`, `src/opus_config`, and their tests |
| Before | `2026-09-01_documentation_critique.md`, import findings only | all documentation; 11 rows concern the import |
| After | `2026-11-19_opus_import_codebase_analysis.md` | `src/opus_import`: C1-C29 |
| After | `2026-11-19_opus_import_test_suite_critique.md` | the import's tests: T1-T18 |
| After | `2026-11-19_opus_import_documentation_critique.md` | the import's documentation: D1-D33 |
| After | `2026-11-19_opus_import_combined_critique.md` | the three above, merged: X1-X72 |

The three 2026-11-19 critiques were written by independent reviewers who read nothing under
`critiques/` or `plans/`. A separate status check classified every earlier finding against
HEAD. This report starts from that check, re-verifies its "Fixed" items and every item where
it disagrees with a new critique, and then matches the new findings to the old ones. Where a
new finding lands on the same defect as an earlier one, that is **independent rediscovery**.
It is the strongest evidence that the earlier finding was not addressed, and it is marked
below with the new id.

**Scope difference.** The earlier code critique also covered `opus_support` and
`opus_config`. Its findings about those packages alone are listed as **out of scope** and kept
out of the totals. Counts that the earlier critique took over all three packages are
re-measured over `opus_import` alone on both trees, so that like is compared with like
(section 3).

## Status at a124e126

This section records how commit `a124e126` (branch `db-perf-pr-26`) changes this
comparison. The comparison below was written against `2794cd36` and is kept as written,
with that tree's figures and line numbers. Four squash merges reached the branch after it:
`acb22dd4` (`[DB · PR-26a]`), `c8fb9d0c` (`[DB · PR-26b]`), `56b917e7` (`[DB · PR-26c]`)
and `a124e126` (`[DB · PR-26d]`). `2794cd36` is a commit of the PR-26a branch from before
its squash, so it is not an ancestor of `a124e126`; the merge base is `0eb24745`.

The statuses of the new findings come from the status sections added to the three
2026-11-19 source reports and the combined report, each checked against the tree at
`a124e126`. The earlier findings those fixes touch were re-checked at `a124e126` as well.
The counts below are counted from those tables.

### The new findings

Grouped as section 4 groups them:

| Group | Findings | Fixed | Partly fixed | Open |
| --- | ---: | ---: | ---: | ---: |
| 4.1 Branch work | 38 | 24 | 2 | 12 |
| 4.2 Older, missed | 21 | 7 | 1 | 13 |
| 4.3 On main after `2bfc2a0e` | 2 | 2 | 0 | 0 |
| 4.4 With a counterpart in the earlier critiques | 19 | 1 | 3 | 15 |
| **All** | **80** | **34** | **6** | **40** |

- **4.1.** Fixed: C1, C2, C7, T5, and D1-D4, D7-D9, D11, D13-D18, D21, D27, D28 and
  D31-D33. Partly fixed: D6 (the user guide's list of failing steps) and D12 (the
  `opus_import_all --help` epilog). Open: C4, C5, C8, C11, C12, C15, C16, C21, T8, T13,
  T14 and T15. The critical finding's defect, C1, is fixed; its structural cause, C5, is
  open.
- **4.2.** Fixed: C22, D5, D10, D19, D20, D24 and D25. Partly fixed: T2 (the missing and
  raising field method). Open: T3, C24, T7, T9, C10, C14, C20, C23, C25, T11, T16, T17
  and T18. Of the trio section 4.2 joins, the GROUP-field crash (C22) and the untested
  validation branches (most of T2) are fixed; the untested bundle selection (T3) is open.
- **4.3.** D22 and D29 are fixed.
- **4.4.** D30 is fixed. C19, T1 and D23 are partly fixed. C3, C6, C9, C13, C17, C18,
  C26, C27, C28, C29, T4, T6, T10, T12 and D26 are open.

### The earlier findings

One earlier finding is closed, so section 1's and section 2's tallies become:

| Earlier critique | Findings | Fixed | Partly fixed | Still present | Moot | Out of scope (not in totals) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2026-09-01 import codebase analysis | 53 | 6 | 10 | 29 | 2 | 6 |
| 2026-09-01 documentation critique, import rows | 11 | 1 | 2 | 7 | 0 | 0 |
| **In scope, both** | **58** | **7** | **12** | **36** | **2** | -- |

- **F2.5, docstring lines over 100 characters, the `src/opus_import` share: Still present
  → Fixed** (`a124e126`). The four docstrings are rewrapped; `awk 'length > 100' $(git
  ls-files 'src/opus_import/*.py')` finds 8 lines, none of them in a docstring. D30 had
  rediscovered it, so of the 36 findings still present, 16 were independently
  rediscovered.
- **F1.3, time-anchored wording: still Partly fixed.** The instances section 2 lists as
  remaining (`docs/dev_guide_import_fixture.rst:116`, `:120`, and "today" in
  `src/opus_import/cli.py:910-916`) are gone (`a124e126`). A grep for time-anchored words
  over the import still finds `src/opus_import/obs/obs_base_pds3.py:24`, "That's OK for
  now", present on `2bfc2a0e` too, and the comment at `src/opus_import/cli.py:1059-1065`
  still states when a commented-out line will be enabled.
- **§4.1, the fast tier: still Partly fixed.** The floor and its comment are corrected
  (below), and the unit tier reaches slightly more; it is still not measured in CI, and
  nothing combines the tiers.
- **§1.1, §1.2, §6.4, §9.2, §4.9 and the line-width strength keep their statuses**, with
  the figures below.

### Measurements the fixes changed

| Measure | `2bfc2a0e` (quoted above) | `2794cd36` | `a124e126` |
| --- | ---: | ---: | ---: |
| Coverage floor, `fail_under` | -- | 74 | 79 |
| Unit tier, `opus_import` statements | 40% | 69.06% (8,313 of 12,038) | 70.00% (8,490 of 12,128) |
| Unit tier, statements and branches | -- | 65.08% | 66.27% |
| Modules over 1,000 lines | 1 | 4 | 4 (`cli.py` 1346 → 1566 lines) |
| Functions over 100 lines | 14 | 17 | 17 (`cli.main` 413 → 485 lines) |
| `import_observation_table` length | 350 | 362 | 382 |
| `assert` statements | 195 | 279 | 276 |
| Lines over 100 characters | 4 | 12 | 8 |
| `pytest.raises` asserting only the type | 2 of 11 | 18 of 104 | 18 of 112 |

How each `a124e126` figure was measured. The structural and test counts' commands were also
run on `2794cd36` (through `git archive` or `git grep`) and reproduce that column; its
coverage figures are the test critique's clean run.

- **Floor:** `pyproject.toml:336`, raised in `56b917e7`.
- **Unit tier:** the test critique's command, with `PYTHONPATH` unset and the data file
  outside the checkout: `OPUS_CONFIG=$PWD/tests/fixtures/opus_ci.toml
  COVERAGE_FILE=<scratch>/unit.coverage pytest -q tests/opus_import --cov=opus_import
  --cov-branch --cov-report=json:<scratch>/unit_cov.json --cov-fail-under=0`, summed over
  the report's files under `src/opus_import/`. 1207 tests passed. The import suite was not
  re-run, so the import-tier, union and gated figures are not re-measured.
- **Modules and functions:** an `ast` script over `src/opus_import` counting files of more
  than 1,000 newlines and functions whose `end_lineno - lineno + 1` exceeds 100.
- **Asserts:** `grep -rnE '^\s*assert ' src/opus_import --include=*.py | wc -l`; the three
  fewer are the `assert obs_row is not None` lines C22's fix removed.
- **Long lines:** `awk 'length > 100' $(git ls-files 'src/opus_import/*.py') | wc -l`.
- **`pytest.raises`:** T12's command over `tests/opus_import`, `import_tests` and
  `tests/import_tests`, with the one call whose `match=` is on its next line counted as
  matched.

---

## Executive summary

The section "Status at a124e126" above records how the later fixes change this comparison.

### What improved

**The dependency and type-gate findings are closed.** `pyproject.toml:31` declares
`rms-pdsfile>=1.0.0`, which ships `py.typed`. No CI job installs a git branch any more
(`grep -rn "git+" .github/` finds nothing). `mypy src tests import_tests` reports no issues in
351 source files against the declared dependencies. These were the earlier critique's first
priority and two of its four High findings.

**The database layer's two named defects are fixed.** `_enter`/`_exit` became the
`_operation` context manager with `try`/`finally` (`importdb/super.py:845-862`).
`create_table` now updates its name cache outside the logging conditional
(`importdb/mysql.py:1076-1080`), with a test (`tests/opus_import/test_importdb_mysql.py:452`).
The `DELETE` truthiness risk is closed by a guard that demands either a `WHERE` clause or
`all_rows=True` (`importdb/mysql.py:2339-2342`).

**The fast tier reaches much more of the pipeline.** The earlier critique measured 40% of
`opus_import`'s statements under the unit tier. The test critique's clean run measures 69.06%
(8,313 of 12,038), and `steps/do_import.py` and `steps/do_validate.py`, which were at 4%, are
now mostly covered. `import_one_index` was halved, 612 to 334 lines.

### What got worse

Measured over `opus_import` alone on both trees (section 3):

| Measure | `2bfc2a0e` | HEAD |
| --- | ---: | ---: |
| Modules over 1,000 lines | 1 | 4 |
| Functions over 100 lines | 14 | 17 |
| Functions with a positional optional parameter (status check's rule) | 58 | 70 |
| `assert` statements | 195 | 279 |
| `: Any` / `-> Any` annotations | 47 | 65 |
| Lines over 100 characters | 4 | 12 |
| `import_observation_table` length | 350 | 362 |
| Database doubles in `tests/opus_import` (status check's pattern) | 5 | 49 |
| `pytest.raises` asserting only the type, import tests | 2 of 11 | 18 of 104 |

Most of this is growth: `opus_import` went from 1,537 to 1,895 functions. But the earlier
critique's structural recommendations went the other way. It asked for `mysql.py` to be split;
it is now 2,871 lines, and two more modules have joined it over the limit.

### What is new

The new critiques report 80 findings. 19 have a counterpart in the earlier critiques. Of the
other 61:

- **38 are in code or documentation the database-performance work added or changed.** They
  include the one critical finding: recovering a lost queue importer's bundle while a
  generation is pending deletes the served generation's rows (C1, combined X1). They also
  include the leak of raw driver errors past the database layer's error contract (C2), a
  finishing step that can fail and still let the schema be stamped servable (C7), and most of
  the documentation drift (D1-D4, D6-D9, D11-D18).
- **21 are older defects the earlier critiques missed**, all present on `2bfc2a0e`. The most
  significant: the per-column validation of observation values and the command line's bundle
  selection are untested in either tier (T2, T3); a failed GROUP field crashes the whole index
  (C22); the PDS4 CSV type inference rewrites values (C24); and validation silently misses a
  duplicate shared by exactly two rows (D10).
- **2 are on `origin/main` but in files added after `2bfc2a0e`**, which the earlier critiques
  could not have seen (D22, D29).

### Tallies

| Earlier critique | Findings | Fixed | Partly fixed | Still present | Moot | Out of scope (not in totals) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2026-09-01 import codebase analysis | 53 | 6 | 10 | 29 | 2 | 6 |
| 2026-09-01 documentation critique, import rows | 11 | 0 | 2 | 8 | 0 | 0 |
| **In scope, both** | **58** | **6** | **12** | **37** | **2** | -- |

The documentation critique's eleventh import row is a strength baseline (F5.2, the CLI
reference), re-measured and still true; it is not a defect and is not in the 58. Of the 37
still present, 17 were independently rediscovered. Of the 12 partly fixed, 7 had their
remaining part rediscovered.

| New critiques | Findings | Counterpart in the earlier critiques | New: branch work | New: older, missed | New: on main after `2bfc2a0e` |
| --- | ---: | ---: | ---: | ---: | ---: |
| Code (C) | 29 | 11 | 11 | 7 | 0 |
| Tests (T) | 18 | 5 | 5 | 8 | 0 |
| Documentation (D) | 33 | 3 | 22 | 6 | 2 |
| **All** | **80** | **19** | **38** | **21** | **2** |

---

## 1. The 2026-09-01 import codebase analysis

Status keys: **Fixed**; **Partly fixed** (what remains is stated); **Still present** (with the
figure at HEAD); **Moot** (the code is gone); **Out of scope** (`opus_support` or
`opus_config` only). "Rediscovered" names the 2026-11-19 finding that reports the same defect;
"site revisited" means a new finding lands on the same lines but reports a different defect.

### Classified findings

| § | Finding (severity) | Status | Evidence at HEAD | Rediscovered |
| --- | --- | --- | --- | --- |
| 1.1 | Two modules over 1,000 lines: `units.py`, `importdb/mysql.py` (Medium) | **Still present, worse** | In `opus_import`: `importdb/mysql.py` 2,871, `importdb/super.py` 1,731, `cli.py` 1,346, `steps/do_import.py` 1,021 (1 module on `2bfc2a0e`, 4 now). The suggested DDL split was not made: `create_table` is at `mysql.py:956`. The `units.py` half is out of scope. | C3 |
| 1.2 | `import_one_index` and `import_observation_table` are the least tractable code (High) | **Partly fixed** | `import_one_index` (`steps/do_import_index.py:49`) 612 → 334 lines, depth 8, after `import_index_row` was extracted. `import_observation_table` (`steps/do_import_obs.py:42`) 350 → 362 lines, depth 9. The two named extractions (duplicate-row resolution, inventory-CSV reader) are still inline. | C6 |
| 1.3 | Dead preprocessing machinery (Medium) | **Still present** | `import_util.py:449-450` (the `None` assignments), `:451-455` (commented loop), `:37` (`pdsparser`); `instruments.py:17`. | C29 |
| 1.4 | `retrieve_ra_dec.py` commented code and dead globals (Low) | **Still present** | `util/retrieve_ra_dec.py:229-252`, `:189`, `:190`. | -- |
| 1.5 | Commented-out imports around the PostgreSQL stub (Low) | **Still present** | `importdb/postgresql.py:13-14`; `importdb/__init__.py:26`, `:117-121`. The module is 0% covered by both tiers. | C18 (also C4) |
| 1.6 | `BundleInfo` keys documented twice (Low) | **Still present** | `config_bundle_info.py:44-65` against `:68-85`. | -- |
| 1 (strength) | Three non-`ALL_CAPS` module globals (Low) | **Still present** | `util/retrieve_ra_dec.py:185,189,190`, nothing else. | -- |
| 2.1 | Optional parameters not keyword-only (Medium) | **Still present, grew** | `opus_import`: 58 → 70 functions by the status check's rule, 74 by the code analysis's (section 3). The named sites are unchanged: `obs/obs_base.py:743`, `importdb/__init__.py:58`, `importdb/mysql.py:340`, `importdb/super.py:262`, `steps/do_import_mult.py:456`. | C9 |
| 2.4 | Two `open()` calls without `encoding=` (Medium) | **Still present** | `import_util.py:401`; `steps/do_import_index.py:243`. | C17 |
| 2.5 | Truthiness where `is not None` is meant, including on a `DELETE` (Medium) | **Partly fixed** | The `DELETE` risk is closed (`importdb/mysql.py:2339-2342`), and `copy_rows_between_namespaces` is gone. Remaining: `super.py:382` `if cur:`, `importdb/__init__.py:122` `if logger:`, and 28 `if self.logger:` (23 in `mysql.py`, 5 in `super.py`). | C8 (the logger checks) |
| 2.6 | Bundle-descriptor expansion written as control flow (Medium) | **Still present** | `import_util.py:189-282`, inside the 190-line `yield_import_bundle_ids`; `COISS_1xxx` at `:190,219,231`. | C27; T3 adds that it is untested |
| 2.7 | `sys.exit()` in library code (Medium) | **Still present** | `import_util.py:319`. | C17 |
| 2.8 | Broad `except Exception` around `cached_tai_from_iso` (Low) | **Still present** | `obs/obs_base.py:843`, `:880`. Mitigated: the message now includes the exception text. | C28 |
| 3.1 | The declared `rms-pdsfile` does not typecheck (High) | **Fixed** | `pyproject.toml:31` `rms-pdsfile>=1.0.0` (from `2e62a929`); the installed 1.0.0 ships `py.typed`; `mypy src tests import_tests` reports no issues in 351 source files. Re-verified. | -- |
| 3.1 (record) | A docstring claimed `pdsfile` ships `py.typed` (record) | **Fixed** | `grep -rn "py.typed" src/opus_import` finds nothing. Re-verified. | -- |
| 3.2 | 1,186 undocumented functions, all `field_*`, published bare (Medium) | **Still present** | 1,108 of 1,112 `field_*` methods have no docstring; the fall is from columns the branch removed. `docs/_ext/opus_api_reference.py:147` still emits `:undoc-members:`. The new documentation critique treats the convention as settled (see section 5). | -- |
| 3.3 | `Any` passthroughs on the obs log helpers (Low) | **Still present** | `obs/obs_base.py:937`, `:946`, `:956`. `: Any` / `-> Any` in `opus_import`: 47 → 65. | -- |
| 3 (strength) | Only 4 lines over 100 characters (Low) | **Still present, regressed** | 12 lines, all in `opus_import` (`importdb/mysql.py` ×7, `import_all.py:22`, `steps/__init__.py:5`, `steps/do_finalize_mult.py:14`, `steps/do_generation.py:818`, `steps/do_schema_version.py:113`). | D30 |
| 4.1 | The fast tier reaches under half the pipeline (High) | **Partly fixed** | Unit tier 40% → 69.06% of `opus_import` statements (clean run, 8,313 of 12,038). Still unmeasured in CI; the floor is 74 (`pyproject.toml:342`) with a stale comment; the 90% target is met only by the unmeasured union (90.30%). `import_one_index` is 0% in the unit tier and 85.0% in the import suite; `import_observation_table` 41.4% and 76.5%. | T1, C19 |
| 4.2 | `test_goldens.py` depends on its own collection order (High) | **Still present** | `import_tests/test_goldens.py:266-300`; the docstring still says "deliberately the last thing this module does" (`:278-279`). New readers in `test_mult.py` make it worse. | T6 |
| 4.4 | `config_targets` checks live only in the MySQL tier (Medium) | **Still present** | `import_tests/test_unit_layers.py:53,64,79,95,107`. | T10 |
| 4.5 | Obs-values golden regenerated into the repository with no clean-run gate (Medium) | **Still present** | `tests/opus_import/test_obs_field_annotations.py:997-1001`. The new test critique judged this acceptable (section 5). | -- |
| 4.7 | Database doubles across files, none in `conftest.py` (Medium) | **Still present, grew** | 5 → 49 classes by the status check's pattern, 63 by T4's (section 3); `_RecordingDB` is defined four times. `conftest.py:172` gained one shared double, `RegistryDB`. | T4 |
| 4.8 | `test_obs_field_annotations.py` is 1,384 lines (Medium) | **Still present** | 1,383 lines; three more test files are over 1,000. | -- |
| 4.9 | `pytest.raises` with no message asserted (Low) | **Still present, grew** | Import tests: 2 of 11 → 18 of 104. | T12 |
| 4.10 | An exact-count source test makes dead code undeletable (Low) | **Moot** | The test was removed with the code it guarded (`acd7382a`). | -- |
| 4.11 | A mutable `ImportContext` is `@functools.cache`d across tests (Low) | **Still present** | `import_tests/test_unit_layers.py:132-141`. | -- |
| 4 (note) | The `create_table` cache defect is untested (note) | **Fixed** | `tests/opus_import/test_importdb_mysql.py:452`. Re-verified. | -- |
| 5.2 | Per-row work in the insert hot path (Low) | **Partly fixed** | Observation rows go through `bulk_load_rows`, which checks `row.keys() == columns` (`importdb/mysql.py:1996`). `insert_rows` still sorts per packet and per row (`:1846`, `:1851`). | -- |
| 5.3 | Exception-driven type inference converts the column three times (Low) | **Still present** | `import_util.py:410-430`. | site revisited by C24, which finds the inference also changes values |
| 6.1 | Duplication to pull up a class (Medium) | **Partly fixed** | The delete pair is gone (`56d510f2`). `primary_filespec` ×6 and the two geometry accessors remain. The unit-converter group is out of scope. | C26 |
| 6.2 | The OPUS-MySQL type map is written twice and the copies disagree (Medium) | **Partly fixed** | Forward map is a table (`importdb/mysql.py:77-101`); the reverse gained `varchar` (`:816`). The reverse is still an `if`/`elif` chain, with the unreachable `mult_list` branch at `:834`. | C18 |
| 6.3 | `_enter`/`_exit` is not exception-safe (Medium) | **Fixed** | `_operation` with `try`/`finally` (`importdb/super.py:845-862`). Re-verified. | -- |
| 6.4 | `main()` mixes three jobs (Low) | **Partly fixed** | Option implications extracted (`cli.py:580`). Logging construction is inline; `main` is 413 lines; the limits dictionary is written 9 times. | C6 |
| 6.5 | `import_util.log_*` is a second spelling of `ImportLog` (Low) | **Still present** | `import_util.py:877-948`. | -- |
| 6.6 | A loop variable is read after its loop (Low) | **Still present** | `steps/do_import_index.py:133`. | -- |
| 6.7 | Substring containment used for a path match (Low) | **Still present** | `steps/do_import_index.py:147`. | -- |
| 7.1 | `create_table` updates its cache inside a logging conditional (Medium) | **Fixed** | `importdb/mysql.py:1076-1080`. Re-verified. | -- |
| 7.2 | Prefix stripping replaces every occurrence (Low) | **Moot** | The import prefix was removed (`56d510f2`). | -- |
| 7.3 | A `requests.Session` is never closed (Low) | **Still present** | `util/retrieve_ra_dec.py:208`. | -- |
| 8.1 | CI does not test the declared dependency set (High) | **Fixed** | No `git+` install in `.github/`; re-verified. | -- |
| 8.2 | A whole-file lint exemption (Medium) | **Still present** | `config_bundle_info.py:11` `# flake8: noqa`, still the only one. The new code analysis counted it as "one `# noqa`" without flagging it. | -- |
| 9.1 | TODO markers, four without an owner (Low) | **Still present** | 13 markers in `opus_import` Python files, 7 `TODOPDS4`; the four plain `TODO`s still have no issue. | code analysis §9 (no id) |
| 9.2 | Assertions carry load (Low) | **Still present** | `opus_import`: 195 → 279 `assert` statements. | C13 |
| 9.3 | A default-value branch in `create_table` never runs (Low) | **Partly fixed** | The branch now runs (`importdb/mysql.py:1040`); a fractional default would still be quoted. | site revisited by C14 (the default is not escaped) |
| 9.4 | Two stale internal names (Low) | **Partly fixed** | The spelling split is moot; `_operation('insert_row')` in `update_row` (`importdb/mysql.py:2112`) and `_operation('cmd')` in `general_select` (`:2418`) remain. | -- |
| 10.1 | The wheel's package data is documented but not checked (Low) | **Partly fixed** | The Package CI job installs the built wheel and asserts two data files (`.github/workflows/run-tests.yml:314-325`), as the earlier tree's CI already did. The inventory command is still run by nothing. | -- |

**Out of scope** (`opus_support` and `opus_config` only; all still present, none counted):
§2.2 message-less exceptions in `opus_support`'s parsers; §2.3 an `assert` validating
`sclk.py`'s argument; §3.4 padded regex groups in `angles.py`; §4.3 ten tests pinning an empty
message; §4.6 four float `==` comparisons in `opus_support` tests; §5.1 numpy imported for two
scalar calls in `units.py`. The `units.py` half of §1.1 and the unit-converter group of §6.1
are also out of scope. One new out-of-scope fact: `src/opus_config/config.py` is now 1,046
lines, over the limit.

### Discussion

The import critique's fixes are concentrated where it was most specific. Every finding that
named one defect in one place, with a mechanical remedy, was fixed: the dependency floor, the
CI install, the `_enter`/`_exit` pair, the name cache. Where the remedy was a refactoring of
growing code, the code grew. Of the 29 findings still present, 15 were rediscovered by the new
reviewers from a standing start. Six of those are structural: module size (§1.1), keyword-only
parameters (§2.1), bundle-descriptor control flow (§2.6), asserts (§9.2), test doubles (§4.7)
and the order-dependent golden fixture (§4.2). Four of them now have larger figures than in
September (1 → 4 modules, 58 → 70 functions, 195 → 279 asserts, 5 → 49 doubles); the
bundle-descriptor chain is the same 94 lines; and the golden fixture has gained readers.

The 14 that were not rediscovered are, with three exceptions, small and local: commented
code, a dead global, a leftover loop variable. The exceptions are §3.2, §4.5 and §8.2, where a
new reviewer saw the same thing and did not flag it (section 5).

---

## 2. The 2026-09-01 documentation critique: import findings

| Id | Finding (severity) | Status | Evidence at HEAD | Rediscovered |
| --- | --- | --- | --- | --- |
| F1.2 | `intersphinx_mapping` omits numpy (Low) | **Still present** | `docs/conf.py:163-169` maps only `python` and `django`. | -- |
| F1.3 | Time-anchored wording, import instances (Medium) | **Partly fixed** | `obs/field_types.py` no longer says "today". Remaining: `docs/dev_guide_import_fixture.rst:116`, `:120`; a new instance at `src/opus_import/cli.py:910-916`. | D23 |
| F2.1 | Undocumented `field_*` methods published bare (High) | **Still present** | A Sphinx build of HEAD's `docs` and `src` puts on the `api_opus_import.obs` page 1,108 `.field_obs_` entries (1,185 on `2bfc2a0e`); the generator is unchanged. | -- (accepted by the new reviewer; section 5) |
| F2.2 | Google-style sections missing, `src/opus_import` share (Medium) | **Still present, grew** | Missing `Parameters:` 5 → 40, `Returns:`/`Yields:` 52 → 112, `Raises:` 4 → 10 (the status check's `sections.py`). | -- |
| F2.5 | Docstring lines over 100 characters, `src/opus_import` share (Low) | **Still present, recurred** | 0 → 4 lines: `import_all.py:22`, `steps/__init__.py:5`, `steps/do_finalize_mult.py:14`, `steps/do_generation.py:818`. The import had none on `2bfc2a0e`; all four are new. | D30 |
| F2.7 | `Args:` sections in `tests/opus_import/_source_scan.py` (Low) | **Still present** | `:31,43,56,73,104`. Outside the new documentation critique's scope (`src/`). | -- |
| F3.1 | No `default_role`, `src/opus_import` share (High) | **Still present, grew** | No `default_role` in `docs/conf.py`; unresolved `py:obj` targets from `opus_import` docstrings 38 → 139 under `-D default_role=py:obj`. | -- |
| F3.2 | API symbols written as literals, import instances (Medium) | **Still present** | `docs/dev_guide_import_db.rst:737`, `dev_guide_import_fixture.rst:156`, `dev_guide_import_running.rst:1041`, `dev_guide_import_obs.rst:460`, `dev_guide_import_config.rst:357`. | -- |
| F3.3 | Constants carry no attribute docstring, so no `py:data` target; constants and private helpers written as literals (Medium) | **Still present** | `opus_import` constants 27 (25 undocumented) → 171 (29 undocumented); the long-standing registries the guides name are still undocumented, and HEAD's API pages have no anchor for `BUNDLE_INFO`, `TABLES_TO_POPULATE`, `INSTRUMENT_ID_TO_MISSION_ID` or `TARGET_NAME_INFO`. | D26 (whose claim that the targets exist is wrong; section 5) |
| F5.1 | No user guide; the import's CLI reference is in the developer guide (High) | **Partly fixed** | `docs/user_guide.rst` and four chapters exist. The CLI reference is still `dev_guide_import_running.rst`, and no user-guide chapter links to it. | -- (D12 reports the same gap for `opus_import_all`, which did not exist on `2bfc2a0e`, so it is counted as new) |
| F5.2 | `opus_import` CLI fully documented (strength baseline) | **Still true** | 51 optional and 1 positional option, all documented; `opus_import_all` 14 optional, all documented (the status check's `cli_doc.py`). | -- |

Every import-scoped documentation finding is still present or only partly fixed. The new
documentation critique rediscovered three of the ten, and found 30 more in material the
September critique did not see or did not check. Most of the documentation the branch added is
accurate, which is what the new critique's executive summary says; but the branch did not
apply the September critique's documentation-system recommendations (`default_role`,
attribute docstrings on constants, Google sections), and the counts behind those findings grew
with the code.

---

## 3. Scope reconciliation: like against like

The status check measured the earlier critique's counts over its own three-package scope; the
new code analysis measured `opus_import` alone, sometimes with a different rule. Each pair
below was re-measured on both trees with one command, so the change can be read from one
method.

| Count | Status check (3 packages) | New code analysis | Re-measured, `opus_import` only: `2bfc2a0e` → HEAD | Why the reports differ |
| --- | --- | --- | --- | --- |
| Modules over 1,000 lines | 6 at HEAD | 4 | 1 → 4 | The 6 adds `opus_support/units.py` (1,176, unchanged) and `opus_config/config.py` (1,046, new over). |
| Functions with a positional optional parameter | 68 → 80 | 74 | 58 → 70 (rule A); 58 → 74 (rule B) | Scope: the 80 adds 10 in `opus_support`. Rule: the status check counts a function only if it has a default and neither keyword-only parameters nor `*args` (rule A); the code analysis counts any function with a defaulted positional parameter (rule B). Four functions at HEAD have both kinds; none did on `2bfc2a0e`. |
| Functions over 100 lines | 17 → 20 | 17 | 14 → 17 | The status check adds 3 in `opus_support`. |
| `assert` statements | 211 → 296 | 279 | 195 → 279 | The status check adds `opus_support` (16) and `opus_config` (1). |
| `: Any` / `-> Any` | 54 → 75 | -- | 47 → 65 | Scope. |
| Lines over 100 characters | 4 → 12 | -- | 4 → 12 | None: every such line is in `opus_import`. |
| Database doubles, `tests/opus_import` | 5 → 49 | 63 (T4) | 5 → 49 (status pattern); 5 → 63 (T4 pattern) | Pattern: T4 also counts `Connection`, `Cursor` and `Server` classes and `conftest.py`. |
| `pytest.raises` asserting only the type | 3 of 43 → 20 of 134 | 18 of 104 (T12) | 2 of 11 → 18 of 104, over `tests/opus_import`, `import_tests` and `tests/import_tests` | Scope: the status check also scans `tests/opus_support` and `tests/opus_config`. Its own script over T12's scope gives 18 of 104. |
| TODO-style markers | 13 → 13 | 13 | 13 → 13 | None, once the code analysis's command is given `--include=*.py`; as written it prints 21. |
| Unit-tier coverage of `opus_import` | 65.26% statements and branches (whole `pytest` run) | 69.1% statements (8,313) | 40% (earlier critique) → 69.06% (8,313) | The status check ran the whole default suite, which reaches `opus_import` from other test directories, and reports statements and branches together. |

The module, long-function, keyword-only and `assert` counts in the last column were made with
one AST script over `src/opus_import` on each tree; the `Any` and marker counts with the
`grep` commands the reports name, restricted to `--include=*.py`; and the test counts with the
status check's scripts and patterns, run over the stated directories. Line counts are
newlines, as `wc -l` gives.

---

## 4. What the new critiques found that the earlier ones did not

### 4.1 Defects in code or documentation the database-performance work added or changed (38)

Classification follows the new reports' own "new"/"branch" labels, checked with `git show
origin/main:<path>` and `git blame` where a label was doubtful. One label was corrected: C5's
untyped `args` and optional `db` were already on `origin/main`, but the branch nearly doubled
the context (16 → 30 fields, 34 → 104 `assert db is not None`) and added the ambiguous
generation state, so it stays here.

| New id | Combined | Severity | Finding |
| --- | --- | --- | --- |
| C1 | X1 | critical | Recovery while a generation is pending deletes the served generation's rows of the bundle |
| C2 | X2 | high | Raw `MySQLdb` errors escape the `ImportDBError` contract |
| C5 | X1 | high | `ImportContext` untyped where it matters and optional everywhere (widened) |
| C4 | X13, X46 | medium | A two-brand abstraction with one brand: 52 stubs (18 on main), a simulation mode |
| C7 | X3 | medium | A finishing step can log an error and the schema still be stamped |
| C8 | X20 | medium | Repeated driver-error and statement boilerplate (overlaps §2.5's logger checks) |
| C11 | X30 | low | Transaction-unaware commits |
| C12 | X31 | low | Named locks: unbounded wait, unchecked release |
| C15 | X34 | low | Bundle state names repeated as raw strings |
| C16 | X35 | low | Observation-id space consumed and never reclaimed |
| C21 | X39 | low | Test fault hooks read from the environment in production paths |
| T5 | X15, X37 | medium | SQL paths only a fake has run |
| T8 | X44 | low | Concurrent measured runs corrupt each other's coverage data |
| T13 | X48 | low | Tests reach into private members |
| T14 | X49 | low | Verdicts depend on thread and process scheduling |
| T15 | X50 | low | Range guards where exact values are known; chained comparisons |
| D1 | X7 | high | Worker ceiling: two pages say the import stops |
| D2 | X8 | high | `do_finalize_mult` says deleted mult ids are reused |
| D3 | X9 | high | A review branch name in the user guide |
| D4 | X23 | medium | `README.txt`'s schema-version refusal does not match the refusal |
| D6 | X3 | medium | The mult step missing from every list of failing steps |
| D7 | X3 | medium | A cache-flush failure described as failing one step |
| D8 | X13 | medium | The `ImportDBSuper` contract table and diagram omit methods |
| D9 | X25 | medium | `import_process` described as queue importers only |
| D11 | X26 | medium | Timings stated without a measurement |
| D12 | X27 | medium | No user-guide reference for `opus_import_all` |
| D13 | X28 | medium | Layout tree and steps docstring incomplete |
| D14 | X54 | low | "One invocation per bundle group" |
| D15 | X55 | low | Scorched-earth list incomplete; two teardown orders |
| D16 | X56 | low | `do_schema_version` section omits the pending-generation case |
| D17 | X57 | low | `do_validate` docstring says every check logs at error level |
| D18 | X58 | low | `do_import` docstring says four modules |
| D21 | X60 | low | Small inaccuracies in the deployment chapter and `README.txt` |
| D27 | X66 | low | Garbled or imprecise sentences |
| D28 | X67 | low | A "may change without this document being updated" disclaimer |
| D31 | X70 | low | An over-broad `nitpick_ignore` |
| D32 | X71 | low | `opus_import.generations` never cross-referenced |
| D33 | X72 | low | A misleading config path; a missing log location |

By severity: 1 critical, 5 high, 12 medium, 20 low.

### 4.2 Older defects the earlier critiques missed (21)

Each was checked on the extract of `2bfc2a0e`: the cited code or text is there.

| New id | Combined | Severity | Finding | Present on `2bfc2a0e` as |
| --- | --- | --- | --- | --- |
| T2 | X5 | high | Per-column validation untested in both tiers | the same branches in `steps/do_import_obs.py` |
| T3 | X6 | high | Bundle selection untested in both tiers | `yield_import_bundle_ids` (the earlier critique raised its control flow and `sys.exit`, not its testing) |
| C22 | X5 | medium | A failed GROUP field crashes the index | `do_import_obs.py:330` and four `assert obs_row is not None` in `do_import_index.py` |
| C24 | X12 | medium | PDS4 CSV type inference changes values | `safe_pdstable_read` (the lines of §5.3) |
| D5 | X24 | medium | Re-import described as an "upsert" | `dev_guide_import_fixture.rst:167`, `:175`, `:208` |
| D10 | X11 | medium | Validation misses a duplicate shared by two rows; the guide records it | both `LIMIT 1,1` clauses in `do_validate.py`, and the sentence at `dev_guide_import_steps.rst:311` |
| T7 | X17 | medium | The obs-execution gate reads any `coverage.json` | `import_tests/tools/obs_execution.py:29` |
| T9 | X18 | medium | Pipeline subprocesses have no timeout | `run_pipeline_step`'s `subprocess.run` with no `timeout` |
| C10 | X29 | low | Connection leaked when `ImportDBMySQL.__init__` fails | `MySQLdb.connect` at `importdb/mysql.py:136`, later raises without a close |
| C14 | X33 | low | DDL fragments from schema JSON not escaped (the view `str.replace` is branch) | `importdb/mysql.py:596`, `:641`, `:670` |
| C20 | X38 | low | No version floor on three runtime dependencies | `pyproject.toml:15`, `:32`, `:33` (the earlier critique called every floor justified) |
| C23 | X40 | low | `cast()` in place of validation | 283 `cast(` calls |
| C25 | X41 | low | A dead `None` check hides a missing filespec | `obs/obs_base_pds3.py:69`, `:75` |
| T11 | X46 | low | `importorskip` on a hard dependency | `tests/opus_import/test_importdb_mysql.py:23` |
| T16 | X51 | low | One instrument driven three times | `test_obs_field_annotations.py:1008`, `:1024`, `:1038` |
| T17 | X52 | low | The unit tree does not mirror the source tree | a flat `tests/opus_import/` |
| T18 | X53 | low | The stated reason for running the import tier serially is wrong | `.github/workflows/run-tests.yml:301`, `docs/dev_guide_testing.rst:68` |
| D19 | X59 | low | `TABLES_TO_POPULATE` called the fill order | `dev_guide_import_config.rst:37` |
| D20 | X39, X60 | low | The environment claim and step 7 incomplete | `dev_guide_import_running.rst:36` (step 7 is branch) |
| D24 | X63 | low | Counts that will drift | `dev_guide_import_fixture.rst:141`, `:182`, `:244` |
| D25 | X64 | low | Passages that describe what the code does not do (the user-guide and `README.txt` instances came later) | `dev_guide_import_running.rst:372` |

By severity: 2 high, 6 medium, 13 low. The two high findings and C22 belong together: the
earlier critique measured `do_import_obs.py` at 6% under the unit tier and recommended
extractions to raise it, but neither critique looked at which branches of the validation the
import tier runs. Neither tier runs them, and one of them crashes the index.

### 4.3 On `origin/main`, in files added after `2bfc2a0e` (2)

| New id | Combined | Severity | Finding | Why the earlier critique could not see it |
| --- | --- | --- | --- | --- |
| D22 | X61 | low | `README.txt` hard-codes untagged release numbers | `src/opus_deploy/server/README.txt` arrived in `2e62a929` |
| D29 | X68 | low | Limitation notes in the overview | `docs/dev_guide_import_overview.rst` arrived in `2e62a929` |

### 4.4 Findings with a counterpart in the earlier critiques (19)

C3 (§1.1), C6 (§1.2, §6.4), C9 (§2.1), C13 (§9.2), C17 (§2.4, §2.7), C18 (§1.5, §6.2), C19
(§4.1), C26 (§6.1), C27 (§2.6), C28 (§2.8), C29 (§1.3), T1 (§4.1), T4 (§4.7), T6 (§4.2), T10
(§4.4), T12 (§4.9), D23 (F1.3), D26 (F3.3), D30 (§3 line width, F2.5). Four findings that land
on the lines of an earlier finding but report a different defect are counted as new above:
C4 (§1.5's stub), C8 (§2.5's logger checks), C14 (§9.3's default) and C24 (§5.3's inference).

---

## 5. Where the old and new records disagree

- **The database brand abstraction.** The earlier critique listed `importdb/postgresql.py`'s
  candour about being a stub as a strength. C4 calls the abstraction unnecessary complexity.
  Both are right about different trees: the stub surface was 18 methods then and is 52 now.
- **The obs-values golden regenerator (§4.5).** The earlier critique asked for a clean-run
  gate before the in-pytest regenerator writes into the repository. The new test critique
  (section 23) says it "regenerates only under an explicit `--regenerate-obs-values` flag,
  which then skips rather than passes", and raises no finding. The code is unchanged
  (`tests/opus_import/test_obs_field_annotations.py:997-1001`), so the earlier finding stands
  as still present; `python_testing.mdc` §5's rule against writing into the repository
  supports it.
- **Bare `field_*` methods in the API reference (§3.2, F2.1).** The new documentation
  critique accepts the exemption at `docs/dev_guide_conventions.rst:89` and does not flag the
  1,108 bare entries. The earlier finding was about publishing them through `:undoc-members:`,
  which is unchanged, so it stands.
- **The blanket lint exemption (§8.2).** The new code analysis counted "one `# noqa`" and
  called the tool configuration consistent. That one marker is `config_bundle_info.py:11`
  `# flake8: noqa`, which `pyproject.toml:479-486` still says does not exist. The earlier
  finding stands.
- **Dependency floors.** The earlier critique called `pyproject.toml` "the most carefully
  justified dependency file I have read". C20 finds three runtime dependencies with no floor,
  unchanged since `2bfc2a0e`. C20 is right.
- **`:data:` targets for constants (F3.3, D26).** D26 says "the targets exist, since autodoc's
  `:undoc-members:` documents module constants". HEAD's built API pages have no anchor for
  `BUNDLE_INFO`, `TABLES_TO_POPULATE`, `INSTRUMENT_ID_TO_MISSION_ID` or `TARGET_NAME_INFO`,
  while documented constants such as `OPUS_TABLE_NAMES` have one. The earlier finding was
  right; D26's recommendation needs attribute docstrings first.
- **Concurrency.** The earlier critique found no threading or multiprocessing anywhere in its
  scope, and so judged module-level mutable state safe. The branch added a fork pool
  (`steps/do_import_pool.py`) and concurrent queue importers. The new critiques review that
  design (C12, C16, T8, T14) and find it sound apart from those items; the earlier judgement no
  longer applies.
- **The status check itself.** Its §6.2 evidence places the unreachable `mult_list` branch
  at `importdb/mysql.py:832`; it is at `:834`. Its "six modules over the limit" mixes scopes
  (section 3). Neither changes a classification.
