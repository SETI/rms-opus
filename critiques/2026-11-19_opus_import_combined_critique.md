# Combined critique: the OPUS import pipeline (`src/opus_import/`)

- **Date:** 2026-11-19
- **Tree:** commit `2794cd36e8b6eab2a244e7c8a197b20095e8bfd8`, branch `db-perf-pr-26a`. The
  comparison base for "new" and "pre-existing" is `origin/main` at `0d4482ad`, the merge base.
- **Scope:** the import pipeline across its code (`src/opus_import/`), its tests
  (`tests/opus_import/`, `tests/import_tests/`, `import_tests/` and how CI runs them) and its
  documentation (the `docs/dev_guide_import*.rst` chapters, the import parts of the other
  guides, the generated API pages, docstrings, help text, and the deploy chain's
  `README.txt`). `opus_config` and `opus_support` appear only where the import depends on
  them.
- **Source reports**, in `critiques/` beside this one:
  - `2026-11-19_opus_import_codebase_analysis.md`: code, findings C1-C29.
  - `2026-11-19_opus_import_test_suite_critique.md`: tests, findings T1-T18.
  - `2026-11-19_opus_import_documentation_critique.md`: documentation, findings D1-D33.
- **Method:** the three reports were written independently against this tree. This report
  merges findings that are one defect, or where one causes another, and gives each merged
  item a new id (X1-X72). Every critical and high item, and every merge, was re-verified
  against the source at this tree rather than taken from the reports. Where that check
  changed a report's claim, the item says so. Coverage figures come from the import suite's
  coverage report at HEAD, with its data file outside the checkout, and from the test
  critique's clean unit-tier run.

## Status at a124e126

This section records which items commit `a124e126` (branch `db-perf-pr-26`) has fixed. The
items below were written against `2794cd36` and are kept as written, with that tree's line
numbers; the line numbers in this section are `a124e126`'s. Every status was checked by
reading the code, tests and documentation at `a124e126`, not taken from commit messages.
Each source report carries its own status section with the per-finding evidence; this
table rolls those up, and where an item merges source findings whose statuses differ, it
says which part remains.

Four squash merges reached the branch after the critiqued tree: `acb22dd4`
(`[DB · PR-26a]`), `c8fb9d0c` (`[DB · PR-26b]`), `56b917e7` (`[DB · PR-26c]`) and
`a124e126` (`[DB · PR-26d]`). `2794cd36` is a commit of the PR-26a branch from before its
squash, so it is not an ancestor of `a124e126`; the merge base is `0eb24745`.

| Id | Status | Sources | Evidence at `a124e126`, and what remains |
| --- | --- | --- | --- |
| X1 | **Partly fixed** | C1 Fixed, C19 (test) Fixed, C5 Open | `c8fb9d0c` fixed the defect: the recovery reads the version row itself and, on a schema with one, deletes as a registered writer (`src/opus_import/steps/do_recover.py:197-204`, `:231-232`), so a pending generation's served rows are retired, not deleted, whichever context recovers. `import_tests/test_generations.py:462` kills a `--join` importer in a pending generation, recovers it with `opus_import_all --status --recover` and finds the served rows intact. Remaining, C5's structural cause: `src/opus_import/context.py` is unchanged (untyped `args`, optional `db` with 104 `assert db is not None`, and `generation_state` meaning both "none" and "not loaded"), and `Coordinator._context` (`coordinator.py:443`) still builds a context without the generation state. |
| X2 | **Fixed** | C2 Fixed, C19 (test) Fixed | `c8fb9d0c`. `_commit`, `_rollback`, `_set_foreign_key_checks` and the `lock_wait_timeout` set and restore raise `ImportDBError` (`src/opus_import/importdb/mysql.py:2568-2593`, `:1759`, `:1112`, `:1137`), and `ImportDBSuper._restoring` (`importdb/super.py:1134`) keeps the body's failure. A commit that meets a deadlock is run again by `retrying()` (`tests/opus_import/test_importdb_mysql.py:1581`). |
| X3 | **Partly fixed** | C7 Fixed, D7 Fixed, C19 (test) Fixed, D6 Partly, C18 (`fill_*`) Open | `c8fb9d0c`. Every finishing step runs through `_run_finishing_step` (`src/opus_import/cli.py:934-960`), which fails it on a `False` result, a `CacheFlushError` or an error logged while it runs, and a failed step keeps `--write-schema-version` from marking the schema (`:1527-1534`; `tests/opus_import/test_cli.py:692`). The mult step is in the `--finalize` help, `main`'s docstring, the `FINALIZATION_OPTIONS` comment and the running chapter's rule (`docs/dev_guide_import_running.rst:739-746`). Remaining: `docs/user_guide_deployment.rst:610-613` still lists three failing steps and says several report failure only through the log; `steps/do_partables.py` and `steps/do_table_names.py` still discard `rebuild_tables_by_swap`'s result, whose `fill_*` callbacks always return `True`; and the finishing sequence is not a table of steps (X19). |
| X4 | **Partly fixed** | T1 Partly, C19 (gaps) Partly | `56b917e7`. `fail_under` is 79 (`pyproject.toml:336`), and the comment (`:321-335`) names the regenerating command instead of the stale counts. Remaining: the unit tier is still unmeasured in CI (`.github/workflows/run-tests.yml:129`), nothing combines the tiers or gates the union, the PDS4 and HST obs classes have no fixture rows, and `ImportDBMySQL.__init__`'s failure paths have no test. |
| X5 | **Partly fixed** | C22 Fixed, T2 Partly | `c8fb9d0c` fixed the code: a failed GROUP field takes its absent value and fails the bundle rather than the index (`src/opus_import/steps/do_import_obs.py:346-364`), the indexings are guarded (`:140`, `:377`), and the three asserts are gone from `steps/do_import_index.py`. `56b917e7` added a test per validation branch (`tests/opus_import/test_do_import_obs.py:203-310`). Remaining, T2's part: those tests replace `import_run_field_function`, so its missing-method and raising branches (`do_import_obs.py:478-497`) are still not executed by the unit tier. |
| X6 | **Open** | T3, C17, C27 Open | `src/opus_import/import_util.py` is unchanged and no test calls `yield_import_bundle_ids`. |
| X7 | **Fixed** | D1 Fixed | `acb22dd4`. `docs/dev_guide_import_running.rst:660-662`; `docs/user_guide_installation.rst:826-829`. |
| X8 | **Fixed** | D2 Fixed | `a124e126`. `src/opus_import/steps/do_finalize_mult.py:16-22`. |
| X9 | **Fixed** | D3 Fixed | `a124e126`. `docs/user_guide_deployment.rst:1012-1021`. |
| X10 | **Open** | C3, C27 Open | By `wc -l`: `importdb/mysql.py` 2909, `importdb/super.py` 1756, `cli.py` 1566, `steps/do_import.py` 1022; `steps/do_import_index.py` 982, `import_util.py` 985, `obs/obs_base.py` 963. |
| X11 | **Fixed** | D10 Fixed | `c8fb9d0c`. Neither scan has an offset (`src/opus_import/steps/do_validate.py:224-252`); the two pairs the corrected scan found are renumbered (`src/opus_import/table_schemas/obs_ring_geometry.json:2387`, `:2412`); `import_tests/test_schema_version.py:427` plants a slug two rows share and finds both named; the guide sentence is gone (`docs/dev_guide_import_steps.rst:1034-1036`). |
| X12 | **Open** | C24 Open | `import_util.py:410-430`, unchanged. |
| X13 | **Partly fixed** | D8 Fixed, C4 Open | `a124e126` fixed the guide: `docs/dev_guide_import_db.rst:232-239` gives the command that lists the contract, and each of the 52 members it prints is in the table and the diagram. Remaining, C4's part: 52 stubs, `importdb/postgresql.py` and the commented branch (`importdb/__init__.py:117-121`) are unchanged. |
| X14 | **Open** | T4 Open | `tests/opus_import/conftest.py:123`, `:220`, `:238`, `:289`, `:348`; four `_RecordingDB` copies. |
| X15 | **Fixed** | T5 Fixed | `56b917e7`. `import_tests/test_unit_layers.py:286` (`--requeue`), `:307` (`set_next_id`), `:323` (index-space budget), `:346` (`generation_problem`, which replaced `generation_command_problem`), `:375` (bounded-wait rename). |
| X16 | **Open** | T6 Open | `import_tests/test_goldens.py:267`, unchanged. |
| X17 | **Open** | T7 Open | `import_tests/tools/obs_execution.py:29`, unchanged. |
| X18 | **Open** | T9 Open | `import_tests/tools/build_run.py:547`, `:582`, `:982`; `import_tests/test_coordinator.py:351`. |
| X19 | **Open** | C6 Open | 17 functions over 100 lines by an `ast` scan; `cli.main` (`cli.py:1082`) is 485 lines. |
| X20 | **Open** | C8 Open | `grep -c "except MySQLdb.Error as e:" src/opus_import/importdb/mysql.py` gives 35; `packet_size = 1000` at `mysql.py:1859`, `:2282`. |
| X21 | **Open** | C9 Open | `importdb/__init__.py:58`, `importdb/super.py:262`, `importdb/mysql.py:340`, `steps/do_import_mult.py:456`, unchanged. |
| X22 | **Open** | C26 Open | `src/opus_import/obs/` is unchanged apart from `obs/field_types.py`. |
| X23 | **Fixed** | D4 Fixed | `a124e126`. The refusal names the finishing invocations (`src/opus_deploy/server/import_and_deploy/_check_schema_version.sh:36-41`), as `src/opus_deploy/server/README.txt:200-207` describes. |
| X24 | **Fixed** | D5 Fixed | `a124e126`. `docs/dev_guide_import_fixture.rst:161-175`; the chapter no longer says "upsert". |
| X25 | **Fixed** | D9 Fixed | `a124e126`. `docs/dev_guide_database_schema.rst:1021`, `:1043-1044`. |
| X26 | **Fixed** | D11 Fixed | `a124e126`. One measured run, 3,032 seconds with six importers sharing 24 workers (`docs/dev_guide_import_running.rst:823-826`, `docs/user_guide_installation.rst:444-446`); the other figures are gone. It names no command or result file. |
| X27 | **Partly fixed** | D12 Partly | `a124e126`. `docs/user_guide_installation.rst:469-475` names the reference and states the pass-through rule. Remaining: the `--help` epilog (`src/opus_import/import_all.py:436-437`) still says other options reach every invocation that reads the holdings. |
| X28 | **Fixed** | D13 Fixed | `a124e126`. `docs/dev_guide_layout.rst:53-74`; `src/opus_import/steps/__init__.py:1-36`. |
| X29 | **Open** | C10 Open | `importdb/mysql.py:426`, unchanged constructor. |
| X30 | **Open** | C11 Open | `importdb/mysql.py:2476`, `:1708`, `:1710`, `:2702-2705`. |
| X31 | **Open** | C12 Open | `importdb/mysql.py:2653`, `:2667`, `:2874`. |
| X32 | **Open** | C13 Open | 276 asserts (`grep -rnE '^\s*assert ' src/opus_import --include=*.py \| wc -l`); `importdb/mysql.py:2017`, `steps/do_import_pool.py:300`. |
| X33 | **Open** | C14 Open | `importdb/mysql.py:1007`, `:1022`, `:1041`, `:1202`. |
| X34 | **Open** | C15 Open | `coordinator.py` and `import_all.py:115-116`, unchanged. |
| X35 | **Open** | C16 Open | `bundle_registry.py`, `steps/do_register.py`, unchanged. |
| X36 | **Open** | C17 Open | `import_util.py:401`; `steps/do_import_index.py:243`. |
| X37 | **Open** | C18, C29, T5 (`upsert_row`) Open | Every cited site remains; `upsert_row` still has no caller in `src/`, and its unit tests remain. |
| X38 | **Open** | C20 Open | `pyproject.toml:15`, `:32`, `:33`. |
| X39 | **Partly fixed** | D20 (environment) Fixed, C21 Open | `a124e126` fixed the guide: `docs/dev_guide_import_running.rst:36-38` names `OPUS_IMPORT_FAULT`. Remaining, C21's part: nothing warns at start-up when the variable is set (`grep -n OPUS_IMPORT_FAULT src/opus_import/cli.py` prints nothing), and no second variable arms it. |
| X40 | **Open** | C23 Open | 282 `cast(` calls. |
| X41 | **Open** | C25 Open | `obs/obs_base_pds3.py:69`, `:75`. |
| X42 | **Open** | C27 Open | `src/opus_import/obs/` is unchanged apart from `obs/field_types.py`. |
| X43 | **Open** | C28 Open | `obs/obs_base.py:843`, `:880`, `:921`; `obs/obs_cassini_common.py:680`; `obs/obs_general.py:106-107`. |
| X44 | **Open** | T8 Open | `import_tests/tools/build_run.py:60`, unchanged. |
| X45 | **Open** | T10 Open | `import_tests/test_recorder_rules.py`; `import_tests/test_unit_layers.py:55-133`. |
| X46 | **Open** | T11, C4 (simulation) Open | `importorskip` at `tests/opus_import/test_importdb_mysql.py:32` and three more; 19 `MYSQLDB_AVAILABLE` in `importdb/mysql.py`. |
| X47 | **Open** | T12 Open | 18 of 112 `pytest.raises` assert only the type. |
| X48 | **Open** | T13 Open | The finding's command gives 104. |
| X49 | **Open** | T14 Open | `tests/opus_import/test_fresh_import.py`, `test_import_pool.py`, unchanged. |
| X50 | **Open** | T15 Open | `import_tests/test_generations.py:296-297`, `:596`, `:702`; `import_tests/test_negative_cases.py:108`. |
| X51 | **Open** | T16 Open | `tests/opus_import/test_obs_field_annotations.py`, unchanged. |
| X52 | **Open** | T17 Open | 35 `test_*.py` files flat in `tests/opus_import/`. |
| X53 | **Open** | T18 Open | `.github/workflows/run-tests.yml:192-193`; `docs/dev_guide_testing.rst:108`. |
| X54 | **Fixed** | D14 Fixed | `a124e126`. `docs/dev_guide_import_steps.rst:179`. |
| X55 | **Fixed** | D15 Fixed | `a124e126`. `docs/dev_guide_import_steps.rst:1205-1207`, `:1244-1256`. |
| X56 | **Fixed** | D16 Fixed | `a124e126`. `docs/dev_guide_import_steps.rst:1167-1170`. |
| X57 | **Fixed** | D17 Fixed | `a124e126`. `src/opus_import/steps/do_validate.py:741-745`. |
| X58 | **Fixed** | D18 Fixed | `a124e126`. `src/opus_import/steps/do_import.py:42-47`. |
| X59 | **Fixed** | D19 Fixed | `a124e126`. `docs/dev_guide_import_config.rst:37-40`. |
| X60 | **Fixed** | D21 Fixed, D20 (step 7) Fixed | `a124e126`. `docs/user_guide_deployment.rst:715-719`, `:734-738`; `src/opus_deploy/server/README.txt:167-168`; `docs/dev_guide_import_running.rst:667-669`. |
| X61 | **Fixed** | D22 Fixed | `a124e126`. `grep -n "3\.2[0-9]\.[0-9]" src/opus_deploy/server/README.txt` prints nothing. |
| X62 | **Partly fixed** | D23 Partly | `a124e126`. The fixture and table-schema instances are gone, and the `cli.py` comment no longer says "today". Remaining: it still describes a commented-out line and the condition for enabling it (`src/opus_import/cli.py:1059-1065`), kept on purpose, rather than an issue. |
| X63 | **Fixed** | D24 Fixed | `a124e126`. None of the three counts remains in `docs/dev_guide_import_fixture.rst`. |
| X64 | **Fixed** | D25 Fixed | `a124e126`. None of the five sentences remains; `docs/user_guide_installation.rst:496-498`. |
| X65 | **Open** | D26 Open | Left on purpose: the constants still have no attribute docstring, so no `:data:` target. |
| X66 | **Fixed** | D27 Fixed | `a124e126`. `docs/dev_guide_database_schema.rst:1003`; `docs/dev_guide_import_overview.rst:282-284`. The `do_django.py:5` instance was not a defect at `2794cd36`: its sentence ends on line 6. |
| X67 | **Fixed** | D28 Fixed | `a124e126`. The disclaimer is gone from `docs/dev_guide_database_schema.rst`. |
| X68 | **Fixed** | D29 Fixed | `a124e126`. `docs/dev_guide_import_overview.rst:234-236`, `:317-319`, `:630-633`. |
| X69 | **Fixed** | D30 Fixed | `a124e126`. `awk 'length > 100' $(git ls-files 'src/opus_import/*.py')` finds 8 lines, none in a docstring. |
| X70 | **Fixed** | D31 Fixed | `a124e126`. `docs/conf.py:259-261`. |
| X71 | **Fixed** | D32 Fixed | `a124e126`. `docs/dev_guide_import_overview.rst:159`; `docs/dev_guide_database_schema.rst:110`. |
| X72 | **Fixed** | D33 Fixed | `a124e126`. `src/opus_import/import_all.py:6`; `src/opus_deploy/server/README.txt:116-117`. |

**Totals:** 28 Fixed, 8 Partly fixed (X1, X3, X4, X5, X13, X27, X39, X62), 36 Open. Of
the critical and high items, X2, X7, X8 and X9 are fixed; X1 (critical) and X5 have their
defect fixed and keep the part stated; X4 is partly fixed; X6 and X10 are open.

By source report (each report's own section): code 4 Fixed, 1 Partly fixed, 24 Open; tests
1 Fixed, 2 Partly fixed, 15 Open; documentation 29 Fixed, 3 Partly fixed, 1 Open.

**Measurements the fixes changed.** The gated floor is `fail_under = 79`, from 74. The unit
tier, run with the test critique's command and restricted to `src/opus_import/`, executes
8,490 of 12,128 statements (70.00%; 66.27% with branches), against 8,313 of 12,038 (69.06%;
65.08%) at `2794cd36`. The import suite was not re-run, so its figures, the gated total and
the union in the table below are not re-measured.

## Executive summary

The section "Status at a124e126" above records which of these items have since been fixed.

**Overall.** The import pipeline is careful, heavily documented code with strong
end-to-end tests, and it passes every mechanical gate. Its defects concentrate in the
generations and queue-importer machinery the database-performance work added. The
components that delete or write observation rows do not all know which generation they
are in, and the database layer's error contract leaks. The documentation of that machinery
has drifted from it in many small places. The test suites are good at state transitions,
fault injection and golden output, but weak on input validation, and coverage is measured
for one tier only.

**Measured gates and coverage at HEAD.**

| Measure | Result | Source |
| --- | --- | --- |
| `ruff check`, `ruff format --check` | clean | code analysis |
| `mypy` (strict) | no issues in 117 source files | code analysis |
| bandit | nothing beyond the repository-wide `B101` skip | code analysis |
| `vulture src/opus_import` | four unused signal-handler parameters the signature requires | code analysis |
| Sphinx `-W -n --keep-going` | exit 0, 0 warnings | documentation critique |
| Unit tier (`tests/opus_import`) | 1,135 passed, 10.4 s | test critique |
| Unit tier, `opus_import` statements | 8,313 of 12,038 (69.06%); 65.08% with branches | test critique, clean run |
| Import suite (`pytest import_tests`) | 207 passed, 3 skipped, 535.74 s | import suite's coverage report at HEAD |
| Import suite, `opus_import` statements | 10,271 of 12,038 (85.32%); 81.80% with branches | same |
| Gated total (`fail_under = 74`, `opus_import`, `opus_support`, `opus_config`) | 79.35% | same |
| Union of the two tiers, `opus_import` statements | 10,870 of 12,038 (90.30%) | computed from the two reports above |

The 90% target of `python_testing.mdc` §9 is met only by the union, which no command or CI
job measures (X4).

**What matters most.**

1. **X1 (critical).** Recovering a lost queue importer's bundle while a generation is
   pending deletes the served generation's rows of that bundle, because the coordinator's
   context never loads the generation state. Verified by reading; not reproduced.
2. **X2.** Raw `MySQLdb` errors from `COMMIT` and from `finally:` restorers escape the
   `ImportDBError` contract that retry and outage handling are built on.
3. **X3.** A finishing step can log an error and return normally, and
   `--write-schema-version` then marks the schema servable. The guides list the failing
   steps inconsistently.
4. **X4, X5, X6.** Only the database tier is measured, against a floor documented with
   stale figures. The per-column validation of observation values and the command line's
   bundle selection run in neither tier, and a failed GROUP field crashes the index.
5. **X7, X8, X9.** Three guide and docstring statements send readers the wrong way: the
   worker ceiling, mult id reuse, and a review branch name in the user guide.

**Findings by severity (merged).** 1 critical, 8 high, 19 medium, 44 low: 72 items from 80
source findings.

## Do first

1. **X1:** load, or read, the generation state wherever recovery deletes, and add the
   pending-generation recovery test. Until then refuse `--join`, the coordinator and
   `--status --recover` on a schema with a pending generation.
2. **X2:** translate driver errors into `ImportDBError` in one place, keep the primary
   exception in `finally:` restorers, and test a commit failure inside `retrying()`.
3. **X3:** one success convention for every step. A logged error during a finishing step
   blocks `--write-schema-version`.
4. **X7, X8, X9:** one-sentence fixes to the ceiling, mult-id and branch-name passages.
5. **X4:** measure both tiers, gate the union, and re-derive the floor and its comment.
6. **X5, X6:** unit-test the column validation and bundle selection. Make a failed GROUP
   field fall back to its absent value instead of crashing the index.

## How the reports' figures reconcile

Several figures were measured by more than one report, or by a report and the status check
of the earlier critiques. They differ for the reasons below; this report uses the figure in
the "used here" column.

| Quantity | Figures | Why they differ | Used here |
| --- | --- | --- | --- |
| Unit-tier `opus_import` statements | 8,313 (69.06%, code analysis and test critique) | Both from `tests/opus_import` with an isolated coverage data file; a run sharing its data file with a concurrent run mixes in lines from forked workers and subprocesses (X44). | 8,313 |
| Import-tier `opus_import` statements | 85.32% (10,271 / 12,038) at HEAD; 85.18% (10,251 / 12,034) from CI at `0eb24745` | Different trees (three commits touching `cli.py`, `coordinator.py`, `import_all.py`) and interpreters (3.13 locally, 3.14 in CI), which also changes statement counts. | HEAD |
| Same, on the test critique's 113 comparable modules | 85.32% (9,424 / 11,046) | A different denominator that happens to give the same percentage. | -- |
| Gated total | 79.35% at HEAD; 79.20% in CI at `0eb24745` | As above; the gated total also covers `opus_support` and `opus_config` (12,938 statements at HEAD against 12,854 in CI). | HEAD |
| Lines only the unit tier reaches | 599 (all modules, HEAD); 498 (113 modules, CI-derived); 484 (113 modules, HEAD) | Scope: the 113-module set excludes `cli.py`, `coordinator.py`, `import_all.py` and `config_bundle_info.py`, which hold 115 of the 599. The remaining 14 lines come from the interpreter difference and from reconstructing CI's line sets from its term-missing report. | 599 |
| Union | 90.30% (all modules, HEAD); 89.82% (113 modules, CI-derived); 89.80% (113 modules, HEAD) | Scope, as above. | 90.30% |
| Hand-written database fakes | 63 (T4); 49 (status check) | Different `grep` patterns: T4 also counts `Connection`, `Cursor` and `Server` classes and the shared `conftest.py`. | 63 |
| `pytest.raises` asserting only the type | 18 of 104 (T12); 20 of 134 (status check) | Scope: the status check also scans `tests/opus_support` and `tests/opus_config`. Its script over T12's scope gives 18 of 104. | 18 of 104 |
| Undocumented functions | 1,110 of 2,012 `def`s and `class`es (documentation critique); 1,108 `field_*` plus 2 others (status check) | The same 1,110: the documentation critique counts classes in the denominator. | 1,110 |
| TODO-style markers | 13 (code analysis, status check) | The code analysis's command as written (`grep -rnE 'TODO\|FIXME\|XXX\|HACK' src/opus_import`) prints 21, because it also matches `XXX` placeholders in `table_schemas/*.json`. Adding `--include=*.py` gives 13. | 13 |

## Findings

Severity is the highest of the sources unless the item says otherwise. "Source" gives the
source ids; "new" or "pre-existing" is against `origin/main`.

### Critical

#### X1. Recovery while a generation is pending deletes the served generation's rows

- **Severity:** critical. C5 (high) is merged here as the structural cause; the item's
  severity is C1's.
- **Location:** `src/opus_import/coordinator.py:443-444` (`Coordinator._context`) and
  `:754-758` (`show_status --recover`); `src/opus_import/steps/do_recover.py:191`;
  `src/opus_import/steps/do_import_tables.py:213-233`; `src/opus_import/context.py:274-306`
  and `:321-325`.
- **Description:** both coordinator paths build `ImportContext(args=argparse.Namespace(),
  logger=...)` and never call `do_generation.load_generation_state`, which is called only
  from `cli.py:1104`, `steps/do_import.py:390`, `steps/do_generation.py` and
  `steps/do_generation_purge.py`. So `ctx.pending_generation` is `None`.
  `_recover_bundle` calls `delete_bundle_from_obs_tables`, which with `pending is None` skips
  `retire_bundle_rows` and walks `_bundle_id_ranges(db, 'obs_general', bundle_id, None)`.
  `quote_identifier` renders `obs_general` as `obs_general_rows`
  (`importdb/mysql.py:653-670`), so the walk covers every row of the bundle, whatever its
  generation. A `--join` importer is a permitted writer of a pending generation (`_WRITERS`,
  `cli.py:664`). It takes `IMPORT_PATH_GENERATION` (`steps/do_import.py:170-172`), and
  `import_from_queue` has no refusal for it. When such an importer dies holding a bundle, its
  own delete has retired the served copy (rows still present, `removed_generation` set), and
  the recovery then deletes those rows outright. The served site loses the bundle, and
  neither `--abandon-generation` nor `--revert-generation` restores it. The shipped
  incremental update uses `--import`, whose holds have a NULL `process_id`
  (`bundle_registry.py:384-392`), and recovery reads only holds whose `process_id` is set
  (`steps/do_recover.py:245-250`). The exposure therefore needs an operator to
  run `opus_import_all` (coordinator or `--join`) or `opus_import_all --status --recover` on
  a schema with a pending generation, and nothing refuses that. No test covers recovery with
  a pending generation. **Verified by reading the code; not reproduced.** The structural
  cause is C5: `generation_state` defaults to `None`, meaning both "no version row" and
  "never loaded"; `args` is an untyped `argparse.Namespace` (35 reads outside `cli.py` and
  `import_all.py`); and `db` is optional, so 104 `assert db is not None` narrow it. The
  context's untyped `args` and optional `db` were already on `origin/main`, with 16 fields
  and 34 such asserts. The branch grew it to 30 fields and 104 asserts, and added the
  ambiguous generation state, so C5's "new" label is only partly right.
- **Recommendation:** load the generation state in `Coordinator._context`, after `_pass`
  reconnects, and in `show_status`'s recovery. Better, have `delete_bundle_from_obs_tables`
  read the version row itself. Add the import test C1 describes: begin a generation, start a
  `--join` importer, kill it after its first chunk (`hold_after_chunk`), recover, and assert
  the served generation's row count for the bundle is unchanged. Until that test passes,
  refuse queue importers and recovery on a schema with a pending generation. Then make the
  generation state tri-state or loaded at construction, replace `args` with a typed, frozen
  options object, and make `db` required.
- **Source:** C1, C5; C19 (the missing test).

### High

#### X2. Raw driver errors escape the `ImportDBError` contract

- **Severity:** high.
- **Location:** `src/opus_import/importdb/super.py:465-466` (`transaction()` ends with a
  bare `_commit()`), `:1129-1133` (`foreign_keys_unchecked`'s `finally:`), `:343-388`
  (`_execute` does not translate); `src/opus_import/importdb/mysql.py:2547-2550` (`_commit`),
  `:1745-1751` (`_set_foreign_key_checks`), `:1110-1111` and `:1136-1137` (the
  `lock_wait_timeout` set and restore outside the `try`).
- **Description:** `retrying()` catches only `ImportDBError` (`super.py:513`), as do the
  coordinator's outage tolerance (`coordinator.py:487`) and `ImporterLock.held()`
  (`import_processes.py:140-143`). A failed `COMMIT` therefore escapes as a raw `MySQLdb`
  error: it is not retried, not logged with the last statement, and it ends the coordinator.
  A connection dropped at commit is exactly the outage those handlers exist for. In the
  `finally:` restorers, a secondary failure replaces the body's exception, so the original
  cause is lost. All of these sites are new: `origin/main` has no `transaction`,
  `retrying`, `foreign_keys_unchecked` or `_execute_waiting_for_locks`. No test injects a
  commit failure.
- **Recommendation:** translate `MySQLdb.Error` into `ImportDBError` (with `from e`) in
  `_execute`, `_commit` and `_rollback`. In `finally:` restorers, log and chain a secondary
  failure rather than raise it, as `named_lock` does (`mysql.py:2622-2628`). Add a unit test
  of `retrying()` with a failing commit. The statement helper of X20 is the natural single
  place.
- **Source:** C2; C19 (the missing test).

#### X4. Only the database tier is measured, nothing combines the tiers, and the floor is stale

- **Severity:** high.
- **Location:** `.github/workflows/run-tests.yml:129` (the `test` job, no `--cov`) and
  `:195` (`import-tests`); `pyproject.toml:321-342` (the floor comment and
  `fail_under = 74`); `docs/dev_guide_testing.rst`; `scripts/run-all-checks.sh:452-461`.
- **Description:** CI measures coverage only for `pytest import_tests`. The unit tier
  reaches 599 `opus_import` statements the import suite does not, most in
  `importdb/mysql.py` (93), `steps/do_import.py` (69), `coordinator.py` (51) and
  `importdb/super.py` (50). No gate sees them. Alone, the unit tier covers 69.06% and the
  import suite 85.32%; only the unmeasured union reaches 90.30%. The floor's comment says the
  run "measures 74.845%: 8,691 of 11,612 statements and branches" and that
  `opus_import.import_all` is a module "this run does not execute". At HEAD the run measures
  79.35%, and `import_all.py` is 64.64% covered (statements and branches), so both counted
  claims are stale. With the floor at 74, a drop of more than five points passes the gate.
  The weakest modules under the import suite are `util/dump_pds_definitions.py` and
  `util/retrieve_ra_dec.py` (0%), `importdb/postgresql.py` (0%),
  `obs/obs_cassini_common_pds4.py` (40.3%), the HST classes `obs_volume_hstix_xxxx.py`
  (52.6%), `hstjx` (54.2%) and `hstnx` (59.7%), and `import_util.py` (64.9%).
- **Recommendation:** run the unit tier under coverage in CI with its own `COVERAGE_FILE`,
  `coverage combine` it with the import suite's data, gate the combined figure, and set
  `fail_under` to it rounded down. Replace the counted claims in the comment with the
  command that regenerates them. Give the PDS4 and HST obs classes fixture rows. Exercise
  `ImportDBMySQL.__init__`'s failure paths, which both tiers miss, with a fake
  `MySQLdb.connect`.
- **Source:** T1, C19 (coverage measurement and gaps).

#### X5. Per-column validation is untested, and a failed GROUP field crashes the index

- **Severity:** high.
- **Location:** `src/opus_import/steps/do_import_obs.py:200-313`, `:335-346`, `:135`,
  `:359`, `:455-476`; `src/opus_import/steps/do_import_index.py:662`, `:711`, `:786`.
- **Description:** two views of one weak spot, the handling of a bad observation value.
  Neither tier executes the FLAG, VARCHAR-type, VARCHAR-length, REAL-parse, INT-parse,
  missed-sentinel and `val_min`/`val_max` branches (with and without
  `val_set_invalid_to_null`), nor a missing or raising field function. At HEAD, 37
  statements between lines 195 and 480 are missed by both tiers. They include line 346,
  where a GROUP column whose field failed returns `None` for the whole row. A field method
  that raises becomes `[None]` (line 146), leaving `mult_label_list` `None`, so the row is
  `None` and all three callers `assert obs_row is not None`. One bad GROUP value therefore
  raises `AssertionError`, abandons the index, and in a plain `opus_import` ends the run,
  `--ignore-errors` included. Two related `IndexError`s escape the same function:
  `mult_label[0]` (line 359) on the empty string that line 226 produces, and `ret[0]`
  (line 135) when a `mult_list` field returns `[]`. The code is pre-existing; the asserts
  were re-sited by the branch. `tests/opus_import/test_do_import_obs.py` has one test,
  though its `_row` helper is the harness the rest need.
- **Recommendation:** make a failed GROUP field fall back to the field's absent mult value,
  guard both indexings, and replace the three asserts with a logged skip of the observation.
  Add parametrized unit tests on `_row`, one per validation branch, each asserting the
  stored value and the logged text and level.
- **Source:** T2, C22.

#### X6. Bundle selection from the command line is untested, exits from library code, and is a data table written as control flow

- **Severity:** high (from T3; C17 and C27 are low).
- **Location:** `src/opus_import/import_util.py:157-346` (`yield_import_bundle_ids`),
  `:189-280` (the shorthand chain), `:319` (`sys.exit(-1)`).
- **Description:** 91 of the function's statements run in neither tier. The unit tier
  replaces it with a lambda (`tests/opus_import/conftest.py:433`) and the import tier passes
  bundle ids directly. Untested: the shorthand table, the bad-descriptor fatal messages and
  the `sys.exit(-1)`, the documented New Horizons reversal (`:334`), and the skip of dotted
  names (`:345`). The `sys.exit` is the only one in `opus_import` outside an entry point,
  and it is part of why the function is awkward to test. The shorthands are a hard-coded
  `if`/`elif` chain whose `ALL` list repeats the others. A typo in the table ships with every
  test green. Pre-existing.
- **Recommendation:** raise a descriptor error and let `cli.main` exit. Derive the lists
  from `config_bundle_info` or a module-level mapping. Unit-test the function with
  `pdsfile`'s `from_path` monkeypatched: each shorthand, the excludes, the NH order, the
  dotted-name skip, and the fatal path with its message text.
- **Source:** T3, C17 (the `sys.exit` part), C27 (the bundle-list part).

#### X7. Two pages say a worker count above the ceiling stops the import; the code lowers it

- **Severity:** high.
- **Location:** `docs/dev_guide_import_running.rst:632-634`;
  `docs/user_guide_installation.rst:819-821`.
- **Description:** both passages say the import stops. `src/opus_config/config.py:923-925`
  lowers the count to the ceiling and records it, and commit `41975e73` ("lower a worker
  count above the ceiling to it") updated other passages but not these two. The running
  chapter now contradicts its own lines 98-105. The user guide is the copy operators read.
  Branch.
- **Recommendation:** say the count is lowered to the ceiling and that the run's first log
  line names it. Grep `docs/` for the old phrasing.
- **Source:** D1.

#### X8. `do_finalize_mult` says a deleted mult id is handed out again; the counter never goes down

- **Severity:** high.
- **Location:** `src/opus_import/steps/do_finalize_mult.py:16-18`.
- **Description:** the module docstring, published in the API reference, says the next value
  "takes the field's highest id plus one, which can be an id deleted here". New ids for
  imported values come from `mult_field.last_id` through `increment_counter`
  (`steps/do_import_mult.py:556`). Nothing in `do_finalize_mult.py` touches `last_id`, and
  the guides correctly say the opposite (`docs/dev_guide_import_overview.rst:515-516`). The
  only other writer of `last_id`, `register_pinned_fields` (`do_import_mult.py:299-304`),
  serves pinned fields, whose only deletable row is `PINNED_ABSENT_ID`, which it excludes.
  Branch.
- **Recommendation:** say a deleted id stays used because the counter never goes down, and
  rewrap the paragraph (line 14 is 141 characters).
- **Source:** D2.

#### X9. The user guide publishes a review branch as its example

- **Severity:** high, as the documentation critique graded it. It is a three-line fix, so
  it is ordered after the code items.
- **Location:** `docs/user_guide_deployment.rst:927-936`.
- **Description:** "For this branch, on a test server" is followed by commands naming
  `@db-perf-pr-23`. A guide may not name a PR branch (`doc_user_guide.mdc` §2), the phrase is
  time-anchored, and the example breaks when the branch is deleted. Branch.
- **Recommendation:** use the `@<branch, tag or commit>` placeholder the sentence above
  already uses, and drop "For this branch".
- **Source:** D3.

#### X10. Four modules exceed the 1,000-line limit, three newly; three more are just under it

- **Severity:** high.
- **Location:** `src/opus_import/importdb/mysql.py` (2,871 lines), `importdb/super.py`
  (1,731), `cli.py` (1,346), `steps/do_import.py` (1,021); just under:
  `steps/do_import_index.py` (988), `import_util.py` (985), `obs/obs_base.py` (963).
- **Description:** on `origin/main` the four were 1,191, 670, 698 and 314 lines, so only
  `mysql.py` was already over (`python.mdc` §2). `mysql.py` holds at least seven separable
  responsibilities: DDL rendering, session set-up, catalogue and DDL execution, index-space
  sizing, the `LOAD DATA` loader, row CRUD, and locks and counters. It also holds two
  application operations that know about `cart` and `django_session`. Counted with
  `wc -l` over `src/opus_import`. The earlier critique's tree had one module over the limit
  in `opus_import`.
- **Recommendation:** make `importdb` a package split along those lines, move
  `repoint_cart` and `carry_over_sessions` into their steps, split `cli.py`'s 396-line
  argument parser into its own module, and move the queue importer out of `do_import.py`.
  Split `import_util.py` along the groups its docstring lists before it crosses the limit.
- **Source:** C3, C27 (the near-limit modules).

### Medium

#### X3. A finishing step can fail silently and the schema still be stamped servable; the guides list the failing steps inconsistently

- **Severity:** medium.
- **Location:** `src/opus_import/cli.py`, `main`'s finishing block through
  `write_schema_version` (`failed_steps` at `:1215`, `:1304-1314`, `:1332-1333`);
  `src/opus_import/steps/do_cart.py:27-31`; `steps/do_partables.py:160-175`;
  `steps/do_table_names.py:235-250`; `steps/do_django.py:67-71`; `cli.py:241-252` (the
  `--finalize` help) and `:945-953` (the `main` docstring); `src/opus_import/import_all.py:91-96`;
  `docs/dev_guide_import_running.rst:439-440` and `:710-712`;
  `docs/user_guide_deployment.rst:540-541`.
- **Description:** `main` counts a step as failed only when it returns `False`.
  `create_cart` logs "Unable to create cart" and returns `None`; `do_partables` and
  `do_table_names` discard `rebuild_tables_by_swap`'s result (whose own `fill_*` callbacks
  always return `True`, so its failure branch is unreachable for them).
  `reset_search_tables` and `analyze_all_tables` return nothing. So a logged error in those
  steps lets `--write-schema-version` mark the schema servable. `opus_import_all --finish`
  runs the finalization group as separate invocations and checks only exit status
  (`import_all.py:258-268`, `:587-606`). The deploy chain's `_opus_import_bundles.sh` reads
  `ERRORS.log` afterwards, but by then the version row is written. The incremental update
  checks `ERRORS.log` between invocations and is protected. The same missing convention
  shows in the documentation. The mult step, which does fail the invocation
  (`cli.py:1208-1216`), is absent from the `--finalize` help, the `main` docstring, the
  running chapter's list, the user guide's list and the `FINALIZATION_OPTIONS` comment. A
  cache-flush failure raises `CacheFlushError`, which `main` does not catch, so it ends the
  whole invocation, where the guide says only "the step fails". Branch.
- **Recommendation:** give every step one return convention (`bool`, or raise a step
  error), and have `main` treat any error logged during a finishing step as a failure. A
  per-step snapshot of `ImportLog`'s error count is enough. Express the finishing sequence
  as a table of steps (X19). Then keep one list of failing steps, in
  `dev_guide_import_running.rst`, and link to it from the help, the docstrings and the user
  guide. Correct the cache-flush sentence.
- **Source:** C7, D6, D7; C18 (the always-true `fill_*` callbacks); C19 (the missing test).

#### X11. Validation misses a duplicate shared by exactly two rows, and the guide records the bug

- **Severity:** medium.
- **Location:** `src/opus_import/steps/do_validate.py:229-237` and `:245-250`;
  `docs/dev_guide_import_steps.rst:1031-1033`.
- **Description:** both duplicate scans in `validate_param_info` (`disp_order` within a
  category, and `slug`) use `EXISTS (... AND pi1.id != pi2.id LIMIT 1,1)`. The subquery
  already excludes the row itself, so the offset skips the only match when a value is shared
  by two rows, and those duplicates are never reported. The guide describes this behaviour,
  which is a known-defect note `doc_dev_guide.mdc` §2 forbids. The documentation critique
  passed the code bug to the code reviewers, and no code finding covers it. Pre-existing:
  `git blame` attributes both lines to `2e62a929`, an ancestor of `origin/main`, and the
  earlier critique's tree `2bfc2a0e` already had both `LIMIT 1,1` clauses.
- **Recommendation:** drop the offset (`LIMIT 1`, or no limit inside `EXISTS`), add a unit
  test with a pair and a triple, and delete the sentence from the guide.
- **Source:** D10.

#### X12. The PDS4 CSV type inference silently changes values

- **Severity:** medium.
- **Location:** `src/opus_import/import_util.py:410-430` (`safe_pdstable_read`, label-less
  PDS4 path).
- **Description:** a column becomes `int` if every cell parses, else `float`, else stripped
  `str`. Zero-padded identifiers lose their zeros, and one blank cell leaves a numeric column
  as strings, so field code such as `wl / 1000.0` (`obs/obs_bundle_occ_common.py:51`) raises
  `TypeError`. The unit tier does not execute the function. These are the lines the earlier
  critique flagged for converting the column three times. Pre-existing.
- **Recommendation:** drive conversion from the column definitions the obs classes read, or
  at least map blank cells to `None` and never convert identifier columns. Add a unit test
  with padded and blank cells.
- **Source:** C24.

#### X13. A two-brand database abstraction with one brand, and a contract table that has drifted from it

- **Severity:** medium.
- **Location:** `src/opus_import/importdb/super.py` (52 `raise NotImplementedError` stubs,
  18 on `origin/main`); `importdb/postgresql.py`; `importdb/__init__.py:26`, `:117-121`;
  `docs/dev_guide_import_db.rst:220`, `:225-351` (table), `:33-111` (diagram).
- **Description:** the only other brand is a 28-line pass-through, and `get_db` has no branch
  that returns it. Each stub carries a full docstring that the MySQL override largely
  repeats. The guide's table claims to declare "the whole database interface" but has no row
  for nine of the stubs (`lock_row`, `set_idle_timeout`, `last_insert_id`,
  `try_named_lock`, `holds_named_lock`, `named_lock_holder`, `carry_over_sessions`,
  `set_next_id`, `list_junction_mismatches`), and the diagram lacks those and four more.
  Restating a growing surface by hand is what let it drift. The earlier critique listed the
  stub's candour as a strength; since then the surface has nearly tripled. Mostly branch.
- **Recommendation:** decide whether a second brand is a goal. If not, fold the ABC into the
  MySQL class or a `typing.Protocol` the steps use, and delete `postgresql.py` and the
  commented branch. If so, use `abc.abstractmethod`. Either way, replace the guide's table
  with the command that lists the contract, or generate it.
- **Source:** C4 (the abstraction), D8.

#### X14. The database fakes are not checked against the backend interface

- **Severity:** medium.
- **Location:** `tests/opus_import/conftest.py:111` (`make_context(**kwargs: Any)`),
  `:172-363` (`RegistryDB`); four `_RecordingDB(ImportDBMySQL)` copies
  (`test_importdb_mysql.py:66`, `test_fresh_import.py:58`, `test_generations.py:77`,
  `test_table_swap.py:27`).
- **Description:** 63 fake classes are handed to `ImportContext.db` through an `Any`
  parameter, so strict mypy never compares them with the interface. `RegistryDB` already
  differs from `ImportDBMySQL` on four signatures, and re-derives SQL semantics by splitting
  the production `WHERE` text. The four `_RecordingDB` copies hand-set different subsets of
  private state. Mostly branch. X1's required `db` would help here too.
- **Recommendation:** type `make_context`'s `db`, add a signature-conformance test for the
  shared fakes and fix the four disagreements, and keep one `_RecordingDB` in `conftest.py`.
- **Source:** T4.

#### X15. Several SQL-issuing paths have only run against a fake

- **Severity:** medium.
- **Location:** `src/opus_import/steps/do_import.py:843` (`requeue_bundles`);
  `importdb/mysql.py` (`set_next_id`, `_free_bytes`, `index_space_budget`,
  `_execute_waiting_for_locks`, `_load_file`, `carry_over_sessions`); `importdb/super.py`
  (`_simulated_count`, `retrying`'s exhaustion).
- **Description:** 22 functions outside `obs/` and `util/` are entered by the unit tier and
  never by the import tier, among them the `--requeue` command and
  `do_generation.generation_command_problem`, which `promote_generation.sh` calls. Their
  SQL is asserted as text but MySQL has never parsed it. Mostly branch.
- **Recommendation:** add one import-tier test each for `--requeue` on a failed bundle,
  `set_next_id` on a non-empty `user_searches`, and the index-space budget query.
- **Source:** T5 (its `upsert_row` part is in X37).

#### X16. A session-scoped re-import mutates the main run's schema, and later modules read it

- **Severity:** medium.
- **Location:** `import_tests/test_goldens.py:266-298`; readers in
  `import_tests/test_mult.py:131-160` and `import_tests/test_negative_cases.py:105-180`.
- **Description:** the `reimport` fixture renumbers a bundle in `main_run.schema`, and its
  docstring guards ordering only within its own module (`:278-279`). Later modules query and
  copy that schema, so what they see depends on which modules ran. The earlier critique
  raised the same fixture; `test_mult.py` is new and adds readers.
- **Recommendation:** re-import into `build_run.copy_run_schema(main_run, ...)`, and assert at
  session end that `main_run.schema` still matches its goldens.
- **Source:** T6.

#### X17. The obs-execution gate reads whatever `coverage.json` is in the checkout root

- **Severity:** medium.
- **Location:** `import_tests/tools/obs_execution.py:29`, `:61-114`;
  `import_tests/test_obs_execution.py:38-64`; `scripts/run-all-checks.sh:478`.
- **Description:** when the git-ignored file exists it is used with no check that it came
  from this tree or run, so a stale import-tier report, or a unit-tier one whose obs
  coverage is far lower, decides three tests. Pre-existing.
- **Recommendation:** refuse a report older than the session start or the newest file in
  `src/opus_import/obs`, or pass the report path explicitly.
- **Source:** T7.

#### X18. Pipeline subprocesses run without timeouts; one assertion is against the wall clock

- **Severity:** medium.
- **Location:** `import_tests/tools/build_run.py:547` (`run_pipeline_step`), `:582`
  (`run_migrate`), `:982` (`communicate_all`); `import_tests/test_coordinator.py:351`.
- **Description:** a deadlocked step, or a hold file a failed test left behind
  (`HOLD_LIMIT_SECONDS = 300` per importer), hangs the session until the job's 60-minute
  timeout, with no test named. `test_coordinator.py:351` asserts a 5 s bound on a shared
  runner. Pre-existing for `run_pipeline_step`; the concurrent helpers are branch.
- **Recommendation:** one module constant for subprocess timeouts; on expiry kill the process
  and fail with its stderr. Drop the second wall-clock assertion.
- **Source:** T9.

#### X19. Seventeen functions exceed 100 lines; `cli.main` grew to 413

- **Severity:** medium.
- **Location:** `src/opus_import/cli.py` (`main` 413 lines, `_create_argument_parser` 396);
  `steps/do_import_obs.py:42` (`import_observation_table`, 362); `steps/do_import_index.py:49`
  (`import_one_index`, 334); `importdb/mysql.py:340` (`__init__`, 198).
- **Description:** counted by `ast` over `src/opus_import` (14 on the earlier critique's tree).
  `import_one_index` was roughly halved on the branch; `import_observation_table` grew.
  `cli.main` repeats the limits dictionary nine times. `ImportDBMySQL.__init__`'s
  create-database branch nests seven deep.
- **Recommendation:** run `cli.main`'s finishing sequence from a table of steps (which also
  fixes X3), and move the session set-up out of `ImportDBMySQL.__init__` into a `connect()`
  factory (which also fixes X29).
- **Source:** C6.

#### X20. Repeated driver-error and statement boilerplate in the database layer

- **Severity:** medium.
- **Location:** `src/opus_import/importdb/mysql.py` (31 `except MySQLdb.Error as e:`;
  execute-and-commit at `:640-645`, `:1601-1607`, `:2134-2139`, `:2179-2183`, `:2662-2671`;
  the 1,000-row packet loop at `:1838` and `:2261`); 28 `if self.logger:` checks (23 in
  `mysql.py`, 5 in `super.py`).
- **Description:** the same three lines of log-and-wrap recur, the packet size is an inline
  magic number twice, and the logger checks exist because `logger` may be `None`. Mostly
  branch.
- **Recommendation:** one `_statement(cmd, params, *, what)` helper that executes, translates
  errors (X2) and commits outside a transaction (X30); a module constant for the packet
  size; a `NullLogger` default.
- **Source:** C8.

#### X21. Optional parameters are positional; the 12-argument connection signature is written four times

- **Severity:** medium.
- **Location:** `src/opus_import/importdb/__init__.py:58` (`get_db`); `importdb/super.py:262`
  and `importdb/mysql.py:340` (`__init__`); `importdb/super.py:936-948`
  (`open_sibling_connection`); `steps/do_import_mult.py:456` (`update_mult_table`).
- **Description:** an `ast` scan finds 74 of 1,895 `opus_import` functions with a defaulted
  positional parameter, against `python.mdc` §2's keyword-only rule. Seventeen take more than
  five positional parameters. Mixed.
- **Recommendation:** a frozen `ConnectionSettings` built once from `OpusConfig`; `*` before
  every optional group; a `MultValue` dataclass for `update_mult_table`.
- **Source:** C9.

#### X22. Duplication across the obs classes

- **Severity:** medium.
- **Location:** `primary_filespec` in six classes (`obs_cassini_common.py:627`,
  `obs_volume_ebrocc_xxxx.py:73`, `obs_volume_hubble_common.py:82`,
  `obs_volume_nhxxlo_xxxx.py:41`, `obs_volume_nhxxmv_xxxx.py:40`,
  `obs_volume_voyager_common.py:50`); `obs_base.py:473` and `:547`; the occultation flags in
  two subclasses of `ObsBundleOccCommon`.
- **Description:** an `ast` scan finds 26 exact-duplicate groups covering 66 functions, and 29
  near-duplicate groups covering 97 functions and 711 lines. Pre-existing.
- **Recommendation:** hoist each group to its nearest common base, and merge the two geometry
  accessors behind a key parameter.
- **Source:** C26.

#### X23. `README.txt`'s account of the schema-version refusal does not match the refusal

- **Severity:** medium.
- **Location:** `src/opus_deploy/server/README.txt:198-203`;
  `src/opus_deploy/server/import_and_deploy/_check_schema_version.sh:31-34`.
- **Description:** the README names four finishing invocations as the remedy; the refusal
  message names only the stamp, which `docs/user_guide_deployment.rst:342-346` warns leaves
  the finalization undone. Branch.
- **Recommendation:** have the README quote the message, and extend the message to name the
  finishing invocations.
- **Source:** D4.

#### X24. The fixture chapter describes re-import as an "upsert"

- **Severity:** medium.
- **Location:** `docs/dev_guide_import_fixture.rst:167-169`, `:175`, `:297`.
- **Description:** observation rows are deleted and loaded again on both write paths
  (`steps/do_import.py:457-461`), and the paragraph's own lines 171-172 say so. The
  documentation critique's supporting claim that `upsert_rows` has exactly one caller is
  wrong: it has two, `steps/do_update_mult_info.py:137` and `steps/do_import_mult.py:298`
  (pinned mult groups at registration). The finding stands for observation rows. Mixed.
- **Recommendation:** describe the re-import case as checking the delete-then-reload, and
  drop "upsert" where it refers to observation rows.
- **Source:** D5.

#### X25. The schema chapter says `import_process` records only queue importers

- **Severity:** medium.
- **Location:** `docs/dev_guide_database_schema.rst:1021`, `:1043-1044`.
- **Description:** `register_writer` records every invocation that writes a versioned schema
  (`steps/do_generation.py:290-291`, called from `cli.py:1120-1131`), as
  `dev_guide_import_running.rst:558-561` says. Branch.
- **Recommendation:** describe both kinds of row and what `progress_at` and `state` mean for
  a writer row.
- **Source:** D9.

#### X26. Timings and performance figures are stated without a measurement

- **Severity:** medium.
- **Location:** "about an hour" at `docs/dev_guide_import_running.rst:790`,
  `docs/user_guide_installation.rst:444`, `docs/user_guide_deployment.rst:529`,
  `src/opus_deploy/server/README.txt:110`; `docs/dev_guide_import_fixture.rst:17`;
  `docs/dev_guide_import_steps.rst:770-771`; `docs/dev_guide_import_db.rst:175-179`.
- **Description:** none names a command or result, against `CLAUDE.md`'s rule for countable
  claims. Mostly branch.
- **Recommendation:** cite one benchmark result in `dev_guide_benchmarks.rst` and link to it,
  or drop the numbers.
- **Source:** D11.

#### X27. The user guide has no option reference for `opus_import_all`

- **Severity:** medium.
- **Location:** `docs/user_guide_installation.rst`, `docs/user_guide_deployment.rst`;
  `src/opus_import/import_all.py:428-519`.
- **Description:** `--prepare`, `--finish`, `--watch` and `--yes` appear nowhere in the user
  guide, and neither guide says that unknown options are passed to the erase, the
  registration and the importers but not to `--finish` or `--requeue`. The documentation
  critique adds that `--override-db-schema` reaches the closing invocations only through
  that pass-through. That is wrong: it is `opus_import_all`'s own option, and `_override`
  adds it to every step, `finish_steps` and `requeue_steps` included
  (`import_all.py:207-209`, `:258-281`). Branch.
- **Recommendation:** add an `opus_import_all` reference to the user guide that states the
  pass-through rule, or state that `dev_guide_import_running` is the reference.
- **Source:** D12.

#### X28. The layout tree and the steps package docstring list less than exists

- **Severity:** medium.
- **Location:** `docs/dev_guide_layout.rst:50-71`; `src/opus_import/steps/__init__.py:1-27`;
  `docs/dev_guide_import_overview.rst:293-294`.
- **Description:** the tree lists 10 of 24 top-level modules (omitting `import_all` and twelve
  branch modules); the steps docstring, which the overview calls the authority on step order,
  omits five step modules. Branch.
- **Recommendation:** complete both, or stop calling the docstring the authority.
- **Source:** D13.

### Low

| Id | Location | Description | Recommendation | Source |
| --- | --- | --- | --- | --- |
| X29 | `src/opus_import/importdb/mysql.py:426`, failures at `:447-491`, `:510`, `:525-537` | `ImportDBMySQL.__init__` raises after connecting without closing the connection; the coordinator reconnects every pass during an outage. Pre-existing, widened. | Close on any failure after `connect`, or a `connect()` factory (X19). | C10 |
| X30 | `src/opus_import/importdb/mysql.py:2455`, `:1694`/`:1696`, `:2664-2667` | `stream_select` and `carry_over_sessions` commit unconditionally; `increment_counter` raises after its `UPDATE` without rolling back. Latent: today's callers run outside a transaction. Branch. | Route through the statement helper (X20); roll back before raising. | C11 |
| X31 | `src/opus_import/importdb/mysql.py:2615`, `:2629`, `:2836` | `GET_LOCK(..., -1)` waits forever; a `RELEASE_LOCK` result other than 1 passes silently. Branch. | A named finite timeout with a log line; warn on a bad release. | C12 |
| X32 | e.g. `src/opus_import/importdb/mysql.py:1996`, `steps/do_import_pool.py:300` | 279 asserts in `opus_import`; a minority guard data and vanish under `-O`. Mixed. | Keep asserts for narrowing; raise for data checks. | C13 |
| X33 | `src/opus_import/importdb/mysql.py:1007`, `:1022`, `:1041`, `:1188` | DDL fragments from schema JSON are not escaped; the view condition's placeholders are filled by `str.replace`. Not an injection path today. Mixed. | Escape the default or validate it; render the view condition from an `int`. | C14 |
| X34 | `src/opus_import/coordinator.py:118-121` and seven more lines; `import_all.py:115-116` | Bundle states spelled as string literals despite `bundle_registry.py:50-62` constants. Branch. | A `StrEnum`. | C15 |
| X35 | `src/opus_import/bundle_registry.py:65-71`, `:183-206`; `steps/do_register.py:242-249` | Id space is reserved at 100 per declared row and never reclaimed; a 0-row label gets no ids. Neither is reported before it is hit. Branch. | Log id-space use; a minimum capacity; compact during purge. | C16 |
| X36 | `src/opus_import/import_util.py:401`; `steps/do_import_index.py:243` | Two text `open()` calls without `encoding=`. Pre-existing. | `encoding='utf-8'`, `newline=''`. | C17 (the `open` part) |
| X37 | `importdb/postgresql.py:13-14`; `importdb/__init__.py:26`, `:117-121`; `importdb/mysql.py:732-734`, `:834`; `import_util.py:449-455`, `:941`; `steps/do_import_obs.py:448-451`; `config_targets/planet_group_mapping.py:18`; `importdb/mysql.py:2189` | Dead and commented-out code: commented imports and branch, an unreachable `mult_list` branch, the preprocessing hook, `log_unknown_target_name` (no caller), unused parameters, the stale `disp_order` name, and `upsert_row`, which nothing in `src/` calls but two unit tests keep alive. Mostly pre-existing. | Delete them, and the `upsert_row` tests with the method. | C18, C29, T5 (the `upsert_row` part) |
| X38 | `pyproject.toml`, `[project] dependencies` | `mysqlclient`, `rms-pdslogger` and `rms-pdstable` have no version floor, though the import uses recent API on each. Pre-existing. | Floors at the versions that introduced it. | C20 |
| X39 | `src/opus_import/import_fault.py:31`; `docs/dev_guide_import_running.rst:36` | Any process whose environment carries `OPUS_IMPORT_FAULT` fails or hangs on purpose, and the guide says the pipeline reads nothing else from the environment. Branch code, main text. | Warn at start-up when it is set, or require a second variable; name it in the guide. | C21, D20 (the environment part) |
| X40 | concentrated in `src/opus_import/obs/` | 282 `cast(` calls stand in for validation at index-row boundaries. Mostly pre-existing. | Typed accessors on the obs base. | C23 |
| X41 | `src/opus_import/obs/obs_base_pds3.py:68-77` | `if filespec is None` can never fire, so a row with no filespec columns becomes `'<bundle>/'`. Pre-existing. | Test the empty string. | C25 |
| X42 | `obs_volume_couvis_0xxx.py:286-323`, `obs_volume_covims_0xxx.py:226-232`, `obs_ring_geometry.py`, `obs_surface_geometry_target.py` | Deep MROs, inline instrument constants, 35 magic-value comparisons, exact float comparisons with longitude sentinels. Pre-existing. | Named constants module; tolerant sentinel comparisons. | C27 (the rest) |
| X43 | `obs/obs_base.py:843`, `:880`, `:921`; `obs/obs_cassini_common.py:680`; `obs/obs_general.py:106-107` | Broad `except Exception` at parse sites, and data asserts on index values. Pre-existing. | Narrow the handlers; return `None` for `None` inputs. | C28 |
| X44 | `pyproject.toml` `[tool.coverage.run]`; `import_tests/tools/build_run.py:432-478`; `import_tests/conftest.py:74-88` | Concurrent measured runs in one checkout share the data file and the subprocess `.pth`, and corrupt each other; observed during these critiques. Mixed. | Per-session `COVERAGE_FILE` and a pid-suffixed `.pth`. | T8 |
| X45 | `import_tests/test_recorder_rules.py`; `import_tests/test_unit_layers.py:45-140`; static checks in `test_goldens.py:153-209`, `test_obs_execution.py:86-106` | Database-free tests run only in the MySQL tier. Pre-existing. | Move them to `tests/import_tests/`. | T10 |
| X46 | `tests/opus_import/test_importdb_mysql.py:32`, `test_fresh_import.py:39`, `test_table_swap.py:19`, `test_generations.py:156`; `src/opus_import/importdb/mysql.py` (19 `MYSQLDB_AVAILABLE`) | The hard dependency `mysqlclient` is treated as optional: tests `importorskip` it (234 tests could skip silently) and the code keeps a no-driver simulation mode. Low: the medium part of C4 is in X13. Mixed. | Plain `import MySQLdb`; delete the simulation mode. | T11, C4 (the simulation part) |
| X47 | e.g. `tests/opus_import/test_importdb_mysql.py:301`, `test_do_update_mult_info.py:280` | 18 of 104 `pytest.raises` assert only the type. Mixed. | `match=` on each. | T12 |
| X48 | `tests/opus_import/test_coordinator.py`; `conftest.py:108` | 101 references to private members of the code under test. Mostly branch. | A public seam, or accept the coupling explicitly. | T13 |
| X49 | `tests/opus_import/test_fresh_import.py:470`, `:504`; `test_import_pool.py:237`, `:255`, `:362-374` | Verdicts depend on sleep-based overlap; forks from a threaded xdist worker with the warning silenced. Branch. | Barriers; `forkserver` or a subprocess. | T14 |
| X50 | `import_tests/test_negative_cases.py:108`; `import_tests/test_generations.py:296-297`, `:526`, `:632`; others | Range guards where the fixture allows exact values; chained comparisons. Mostly branch. | Exact counts; split the chains. | T15 |
| X51 | `tests/opus_import/test_obs_field_annotations.py:1007-1040` | Three tests drive every instrument to assert three parts of one result. Pre-existing. | Cache the drive or combine the tests. | T16 |
| X52 | `tests/opus_import/` | The unit tree does not mirror the source tree. Pre-existing. | Subdirectories when files are next touched. | T17 |
| X53 | `.github/workflows/run-tests.yml:192-193`; `docs/dev_guide_testing.rst:108`; `import_tests/conftest.py:107` | The stated reason the import tier runs serially is wrong (each xdist worker would use its own schema), and the tier runs on one Python. Pre-existing. | Correct the text; fail fast under xdist. | T18 |
| X54 | `docs/dev_guide_import_steps.rst:179` | A full import is described as "one invocation per bundle group". Branch. | Use the running chapter's wording. | D14 |
| X55 | `docs/dev_guide_import_steps.rst:1198-1200`, `:1236-1246` | The scorched-earth table list is incomplete and the page gives two teardown orders. Branch. | Refer to `OPUS_TABLE_NAMES`; one order. | D15 |
| X56 | `docs/dev_guide_import_steps.rst:1157-1166` | The `do_schema_version` section omits the pending-generation case. Branch. | Add it. | D16 |
| X57 | `src/opus_import/steps/do_validate.py:741-742` | The docstring says every check logs at error level; one logs a warning. Branch. | Name the exception. | D17 |
| X58 | `src/opus_import/steps/do_import.py:42-46` | "Split across four modules"; there are five. | Add `do_import_pool`; drop the number. | D18 |
| X59 | `docs/dev_guide_import_config.rst:36` | `TABLES_TO_POPULATE` is called the fill order; it is the load order. Pre-existing. | Reword. | D19 |
| X60 | `docs/user_guide_deployment.rst:643-645`, `:650-653`; `src/opus_deploy/server/README.txt:167-168`; `docs/dev_guide_import_running.rst:639-641` | Small inaccuracies in the deployment chapter, `README.txt` and the running chapter's step 7. Branch. | Correct each. | D21, D20 (step 7) |
| X61 | `src/opus_deploy/server/README.txt` (eleven lines) | Release numbers that do not exist as tags. On main. | `==<release>` placeholders. | D22 |
| X62 | `docs/dev_guide_import_fixture.rst:116`, `:120-123`, `:300`; `docs/dev_guide_table_schemas.rst:81`, `:412`; `src/opus_import/cli.py:910-916` | History and time-anchored wording. Mixed. | Present tense; move the planned change to an issue. | D23 |
| X63 | `docs/dev_guide_import_fixture.rst:143-145`, `:184`, `:333` | Counts that will drift. Pre-existing. | Give the command or drop the number. | D24 |
| X64 | `docs/user_guide_installation.rst:489-490`; `docs/user_guide_deployment.rst:157-158`; `README.txt:181-182`; `docs/dev_guide_import_running.rst:616`, `:732` | Sentences that describe what the code does not do. Mixed. | Positive statements. | D25 |
| X65 | `docs/dev_guide_import*.rst` | Owned constants written as literals instead of `:data:` roles. The documentation critique says the targets exist; for the constants it names they do not. HEAD's API pages have no anchor for `BUNDLE_INFO`, `TABLES_TO_POPULATE`, `INSTRUMENT_ID_TO_MISSION_ID` or `TARGET_NAME_INFO`, because those carry no attribute docstring. Roles alone would fail the nitpicky build. Mostly pre-existing. | Give the constants attribute docstrings (`#:`), then use `:data:` roles. | D26 |
| X66 | `docs/dev_guide_database_schema.rst:1003`; `src/opus_import/steps/do_django.py:5`; `docs/dev_guide_import_overview.rst:281` | Garbled or imprecise sentences. Branch. | Reword. | D27 |
| X67 | `docs/dev_guide_database_schema.rst:112` | A "may change without this document being updated" disclaimer. Branch. | Delete it. | D28 |
| X68 | `docs/dev_guide_import_overview.rst:232-235`, `:315-317`, `:629-630` | Limitation notes in a guide. On main and branch. | Issues, or design rules. | D29 |
| X69 | `src/opus_import/steps/do_finalize_mult.py:14`, `import_all.py:22`, `steps/__init__.py:5`, `steps/do_generation.py:818` | Docstring lines over 100 characters (12 lines over the limit in all). Branch. | Rewrap. | D30 |
| X70 | `docs/conf.py`, the `('py:class', 'T')` entry | Over-broad `nitpick_ignore`. Branch. | Name the one function in the comment. | D31 |
| X71 | `docs/dev_guide_import_overview.rst:141-183`; `docs/dev_guide_database_schema.rst` | `opus_import.generations` is never cross-referenced. Branch. | A `:mod:` link. | D32 |
| X72 | `src/opus_import/import_all.py:4-6`; `src/opus_deploy/server/README.txt:116` | A misleading absolute config path; a log location not given. Mixed. | `<installation>/opus.toml`; give the path. | D33 |

## Corrections to the source reports found while verifying

- **Codebase analysis, C5:** labelled new, but `ImportContext`'s untyped `args` and optional
  `db` were already on `origin/main` (16 fields, 34 `assert db is not None`). The branch widened
  it to 30 fields and 104 asserts and added the ambiguous generation state.
- **Codebase analysis, §9:** the TODO command as written prints 21, not 13; it needs
  `--include=*.py`.
- **Test critique, measurement note:** it names T17 as the finding the shared-coverage
  incident is evidence for; the finding about shared coverage data is T8.
- **Documentation critique, D5:** `upsert_rows` has two callers, not one.
- **Documentation critique, D12:** `--override-db-schema` does not depend on the
  pass-through; `_override` adds it to every step.
- **Documentation critique, D26:** the `:data:` targets for the named constants do not exist,
  so the recommendation as written would break the nitpicky build.
