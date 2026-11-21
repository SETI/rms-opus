# Codebase analysis: `src/opus_import/`

- **Date:** 2026-11-19
- **Tree analyzed:** commit `2794cd36e8b6eab2a244e7c8a197b20095e8bfd8`, branch `db-perf-pr-26a`.
  The comparison base is `origin/main` at `0d4482adfd23c47dfdeb02775181707c50354464`, which is
  also the merge base. `git diff --shortstat origin/main...HEAD -- src/opus_import` reports
  125 files changed, 18388 insertions and 5246 deletions.
- **Scope:** all of `src/opus_import/` at HEAD: the CLI and `opus_import_all`, the
  coordinator, the bundle registry and importer table, generations, the step modules, the
  database layer (`importdb/`), the fork pool, and the obs class hierarchy. Each finding says
  whether its code changed against `origin/main` (**new**) or was already on `origin/main`
  (**pre-existing**). `opus_config` and `opus_support` are considered only where
  `opus_import` depends on them.
- **Out of scope:** `opus_app`, `opus_log_analyzer`, the front end, and the test and
  documentation trees. Separate reviewers cover tests and documentation, so they appear
  here only where they bear on a code finding (coverage, untested paths).
- **Standards applied:** `.cursor/rules/python.mdc`, `python_testing.mdc`, `security.mdc`,
  `dependency_management.mdc` and `doc_python.mdc`, cited by filename. Repository waivers
  come from `CLAUDE.md` and `docs/dev_guide_conventions.rst`. Those waivers are: public web
  API compatibility, which does not apply to the import pipeline; bandit `B101` skipped
  repository-wide; and no individual docstrings for the `field_obs_*` methods.
- **Method:** the workflow and dimensions of `.cursor/skills/python-codebase-analysis/SKILL.md`.
  - **Tools.** `ruff check`, `ruff format --check`, `mypy` (strict, from `pyproject.toml`),
    `bandit -r src/opus_import`, `vulture src/opus_import`, all from `venv-head/bin/`.
  - **Coverage.** The unit suite (`pytest tests/opus_import --cov=opus_import --cov-branch`)
    and the import suite's coverage report at HEAD, with its data file outside the
    checkout (`pytest import_tests --cov=opus_import --cov-branch`, run against MySQL).
  - **Measurements.** Function lengths, parameter shapes and duplicate bodies were measured
    with `ast` scripts over the tree.
  - **Reading.** The core orchestration modules were read in full: coordinator, bundle
    registry, importer table, recovery, table swap, the generation switch, the import
    loop and the pool. The database layer and the obs hierarchy were read in depth.
  - **Verification.** Every finding below was checked against the cited source.
  - **Independence.** Nothing under `critiques/` or `plans/` was read.

Line counts include docstrings unless a finding says otherwise. Paths are relative to the
repository root.

## Status at a124e126

This section records which findings commit `a124e126` (branch `db-perf-pr-26`) has fixed.
The findings below were written against `2794cd36` and are kept as written, with that
tree's line numbers; the line numbers in this section are `a124e126`'s. Every status was
checked by reading the code at `a124e126`, not taken from commit messages.

Four squash merges reached the branch after the analyzed tree, and the evidence names the
one that made each fix: `acb22dd4` (`[DB · PR-26a]`), `c8fb9d0c` (`[DB · PR-26b]`),
`56b917e7` (`[DB · PR-26c]`) and `a124e126` (`[DB · PR-26d]`). `2794cd36` is a commit of
the PR-26a branch from before its squash, so it is not an ancestor of `a124e126`
(`git merge-base --is-ancestor 2794cd36 a124e126` fails); the merge base is `0eb24745`.

Status keys: **Fixed**, the defect is gone and any test the finding asked for exists;
**Partly fixed**, with what remains; **Open**, with where the defect is at `a124e126`.

| ID | Status | Evidence at `a124e126` |
|---|---|---|
| C1 | **Fixed** | `c8fb9d0c`. The recovery reads the version row itself (`src/opus_import/steps/do_recover.py:197`) and, on a schema that has one, registers as a writer before the delete and exits as one after it (`:199-204`, `:231-232`), so a pending generation's served rows are retired rather than deleted, in whichever context the recovery runs. `import_tests/test_generations.py:462` kills a `--join` importer holding a bundle of a pending generation, recovers it with `opus_import_all --status --recover`, and finds the served rows unchanged; `tests/opus_import/test_do_recover.py:178` and `:213` cover the unit paths. `Coordinator._context` (`src/opus_import/coordinator.py:443`) still builds a context without the generation state; that structural cause is C5. |
| C2 | **Fixed** | `c8fb9d0c`. `_commit` and `_rollback` raise `ImportDBError` from the driver's error (`src/opus_import/importdb/mysql.py:2568-2593`), as do `_set_foreign_key_checks` (`:1759`) and the `lock_wait_timeout` set and restore (`:1112`, `:1137`). `ImportDBSuper._restoring` (`src/opus_import/importdb/super.py:1134`) keeps the body's failure and notes a failed restore on it; `foreign_keys_unchecked` (`:1130`) and `_execute_waiting_for_locks` use it. Tests: `tests/opus_import/test_importdb_mysql.py:1581` (a commit that meets a deadlock is run again by `retrying()`), `:1597`, `:1630`, `:1654`. The translation is made at each call site: `_execute` (`super.py:343`) still translates nothing itself, so C8's single helper is still open. |
| C3 | **Open** | `find src/opus_import -name '*.py' \| xargs wc -l`: `importdb/mysql.py` 2909 lines, `importdb/super.py` 1756, `cli.py` 1566, `steps/do_import.py` 1022. |
| C4 | **Open** | `grep -c 'raise NotImplementedError' src/opus_import/importdb/super.py` gives 52; `importdb/postgresql.py` and the commented branch at `importdb/__init__.py:117-121` remain; `grep -c MYSQLDB_AVAILABLE src/opus_import/importdb/mysql.py` gives 19. |
| C5 | **Open** | `git diff 2794cd36 a124e126 -- src/opus_import/context.py` prints nothing; `grep -rnE '^\s*assert (ctx\.)?db is not None' src/opus_import \| wc -l` gives 104. |
| C6 | **Open** | An `ast` scan of `src/opus_import` finds 17 functions over 100 lines. `cli.main` (`cli.py:1082`) is 485 lines, `_create_argument_parser` 423 and `import_observation_table` 382; `grep -c` finds the limits dictionary 9 times in `cli.py`. |
| C7 | **Fixed** | `c8fb9d0c`. Every finishing step runs through `_run_finishing_step` (`src/opus_import/cli.py:934-960`), which records it failed when it returns `False`, raises `CacheFlushError`, or logs an error or fatal message while it runs; a failed step refuses `--write-schema-version` and fails the invocation unless `--ignore-errors` (`:1527-1534`). Tests: `tests/opus_import/test_cli.py:671` and `:692` (a cart step that logs "Unable to create cart" leaves the schema unmarked). |
| C8 | **Open** | `grep -c "except MySQLdb.Error as e:" src/opus_import/importdb/mysql.py` gives 35; the inline `packet_size = 1000` is at `mysql.py:1859` and `:2282`; `grep -c "if self.logger:"` gives 23 in `mysql.py` and 5 in `super.py`. |
| C9 | **Open** | Unchanged: `get_db` (`importdb/__init__.py:58`), both `__init__`s (`importdb/super.py:262`, `importdb/mysql.py:340`), `update_mult_table` (`steps/do_import_mult.py:456`). |
| C10 | **Open** | `ImportDBMySQL.__init__` is unchanged: it connects at `importdb/mysql.py:426`, and its later failures raise without closing the connection. |
| C11 | **Open** | `stream_select` commits unconditionally (`importdb/mysql.py:2476`), `carry_over_sessions` commits or rolls back unconditionally (`:1708`, `:1710`), and `increment_counter` raises after its `UPDATE` (`:2702-2705`). |
| C12 | **Open** | `SELECT GET_LOCK(%s, -1)` at `importdb/mysql.py:2653`; the `RELEASE_LOCK` results are ignored at `:2667` and `:2874`. |
| C13 | **Open** | `grep -rnE '^\s*assert ' src/opus_import --include=*.py \| wc -l` gives 276; the three fewer are the `assert obs_row is not None` lines C22's fix removed. The data asserts cited remain at `importdb/mysql.py:2017` and `steps/do_import_pool.py:300`. |
| C14 | **Open** | Unchanged at `importdb/mysql.py:1007`, `:1022`, `:1041` and `:1202` (`condition.replace('%s', ...)`). |
| C15 | **Open** | `src/opus_import/coordinator.py` and `import_all.py:115-116` are unchanged; the literals remain at the lines cited. |
| C16 | **Open** | `bundle_registry.py` and `steps/do_register.py` are unchanged. |
| C17 | **Open** | `sys.exit(-1)` at `import_util.py:319`; `open()` without `encoding=` at `import_util.py:401` and `steps/do_import_index.py:243`. |
| C18 | **Open** | Every cited site remains: `importdb/postgresql.py:13-14`, `importdb/__init__.py:26` and `:117-121`, `importdb/mysql.py:732-734` and `:834`, and the always-true `fill_*` callbacks of `steps/do_partables.py` and `steps/do_table_names.py`. The commented `Pds4File.require_shelves(True)` stays at `cli.py:1065`; `a124e126` rewrote its comment to state the condition for enabling it. |
| C19 | **Partly fixed** | The three untested behaviors now have tests: recovery with a pending generation (`import_tests/test_generations.py:462`), a commit failure inside `retrying()` (`tests/opus_import/test_importdb_mysql.py:1581`), and a cart step that logs an error before `--write-schema-version` (`tests/opus_import/test_cli.py:692`). Remaining: the PDS4 and HST obs classes have no fixture rows (`tests/fixtures/` is unchanged), and nothing tests `ImportDBMySQL.__init__`'s failure branches, of which the unit tier still misses 54 statements in lines 406-579 (the run below). The import suite was not re-run, so its per-module figures are not re-measured. |
| C20 | **Open** | `mysqlclient`, `rms-pdslogger` and `rms-pdstable` still have no version floor (`pyproject.toml:15`, `:32`, `:33`). |
| C21 | **Open** | `import_fault.py` is unchanged, and `grep -n OPUS_IMPORT_FAULT src/opus_import/cli.py` prints nothing, so nothing warns when the variable is set. |
| C22 | **Fixed** | `c8fb9d0c`. A GROUP column whose field method failed, or returned plain values, takes its field's absent value, and the error it logs fails the bundle (`src/opus_import/steps/do_import_obs.py:346-364`); `import_observation_table` always returns a row, and the three `assert obs_row is not None` are gone from `steps/do_import_index.py`. Both indexings are guarded (`do_import_obs.py:140`, `:377`). Tests: `tests/opus_import/test_do_import_obs.py:138`, `:151`, `:166`. |
| C23 | **Open** | `grep -rn 'cast(' src/opus_import --include=*.py \| wc -l` gives 282; `src/opus_import/obs/` is unchanged apart from `obs/field_types.py`. |
| C24 | **Open** | `import_util.py` is unchanged; the inference is at `import_util.py:410-430`. |
| C25 | **Open** | `obs/obs_base_pds3.py:69` and `:75` still test `if filespec is None`. |
| C26 | **Open** | `src/opus_import/obs/` is unchanged apart from `obs/field_types.py`, which holds none of the duplicates cited. |
| C27 | **Open** | The bundle lists are still an `if`/`elif` chain (`import_util.py:189-280`). By `wc -l`, `steps/do_import_index.py` is 982 lines, `import_util.py` 985 and `obs/obs_base.py` 963. |
| C28 | **Open** | Unchanged: `obs/obs_base.py:843`, `:880`, `:921`; `obs/obs_cassini_common.py:680`; `obs/obs_general.py:106-107`; `import_util.py:479`; the field-function wrapper's handler is now `steps/do_import_obs.py:489`. |
| C29 | **Open** | `log_unknown_target_name` (`import_util.py:941`), the preprocessing hook (`import_util.py:449-455`), the parameters `import_run_field_function` does not read (`steps/do_import_obs.py:467`) and `PlanetGroup.disp_order` (`config_targets/planet_group_mapping.py:18`) remain. |

**Totals:** 4 Fixed (C1, C2, C7, C22), 1 Partly fixed (C19), 24 Open.

**Unit tier at `a124e126`**, measured as the test critique measured it, with `PYTHONPATH`
unset and the coverage data outside the checkout:

```text
OPUS_CONFIG=$PWD/tests/fixtures/opus_ci.toml COVERAGE_FILE=<scratch>/unit.coverage \
    pytest -q tests/opus_import --cov=opus_import --cov-branch \
    --cov-report=json:<scratch>/unit_cov.json --cov-fail-under=0
```

1207 tests passed. Over the files under `src/opus_import/`, it executes 8,490 of 12,128
statements (70.00%), 66.27% with branches, against 8,313 of 12,038 (69.06%) and 65.08% at
`2794cd36`. The coverage floor is now `fail_under = 79` (`pyproject.toml:336`), raised from
74 in `56b917e7`.

## Summary

The section "Status at a124e126" above records which of these findings have since been fixed.

The import pipeline passes every mechanical gate.

- `ruff check` and `ruff format --check` are clean.
- Strict `mypy` reports no issues in 117 source files.
- bandit reports nothing beyond the repository-wide `B101` skip.
- `vulture` flags only four unused signal-handler parameters that the signature requires.
- The import suite executes 85.3% of `opus_import`'s statements.

The concurrency design is careful and well documented: the registry queue, the
importer locks, the chunk guard and recovery. The import suite covers between 84.9% and
98.0% of the statements of the coordinator, registry, importer table and recovery modules.

The most important problem is a data-integrity defect that the generations work and
the coordinator create between them. **Recovering a lost queue importer's bundle while a
generation is pending deletes the served generation's rows of that bundle (C1)**, because
the coordinator's context never loads the generation state.

Behind it sit two structural issues:

- The untyped, optional-everything `ImportContext` makes that kind of omission invisible
  to the type checker (C5).
- The database layer leaks raw driver errors past its own `ImportDBError` contract, which
  defeats the retry and outage handling built on that contract (C2).

The branch also takes three more modules past the 1000-line limit (C3). The database
layer is now 4602 lines for one implemented brand behind 52 abstract stubs (C4).

Top priorities: fix C1 and add the missing test; close the error contract (C2); then
split `importdb/mysql.py`, `importdb/super.py` and `cli.py` and give `ImportContext` typed
arguments and a non-optional database (C3, C4, C5).

## Findings at a glance

| ID | Title | Severity | New / pre-existing |
|---|---|---|---|
| C1 | Coordinator recovery deletes every generation's rows of a lost importer's bundle | critical | new |
| C2 | Raw `MySQLdb.Error` escapes the `ImportDBError` contract, bypassing retry and outage handling | high | new |
| C3 | Four modules exceed the 1000-line limit, three of them newly | high | mostly new |
| C4 | A two-brand abstraction with one brand: 52 stubs, a placeholder module, a simulation mode | medium | mostly new |
| C5 | `ImportContext` is untyped where it matters and optional everywhere | high | new |
| C6 | Seventeen functions exceed 100 lines; `cli.main` grew to 413 | medium | mixed |
| C7 | A finalization step can log an error and still let the schema be marked ready | medium | new |
| C8 | Repeated driver-error and statement boilerplate in the database layer | medium | mostly new |
| C9 | Optional parameters are positional; 12-argument connection signature ×4 | medium | mixed |
| C10 | Connection leaked when `ImportDBMySQL.__init__` fails after connecting | low | pre-existing, widened |
| C11 | Transaction-unaware commits in `stream_select`, `carry_over_sessions`, `increment_counter` | low | new |
| C12 | Named locks: unbounded `GET_LOCK` wait, `RELEASE_LOCK` result ignored | low | new |
| C13 | Integrity checks written as `assert` | low | mixed |
| C14 | SQL text built from schema JSON without escaping; a placeholder filled by `str.replace` | low | mixed |
| C15 | Bundle state names repeated as raw strings | low | new |
| C16 | Observation-id space is consumed and never reclaimed | low | new |
| C17 | Library hygiene: `sys.exit` and encoding-less `open()` in library modules | low | pre-existing |
| C18 | Dead and commented-out code | low | mostly pre-existing |
| C19 | Coverage gaps where it matters | medium | mixed |
| C20 | Runtime dependencies the import relies on have no version floor | low | pre-existing |
| C21 | Test fault hooks read from the environment in production paths | low | new |
| C22 | A recoverable field error crashes the index instead of nulling the column | medium | pre-existing |
| C23 | `cast()` in place of validation at index-row boundaries | low | mostly pre-existing |
| C24 | PDS4 CSV type inference silently changes values | medium | pre-existing |
| C25 | Dead `None` check hides a missing file specification | low | pre-existing |
| C26 | Duplication across the obs classes | medium | pre-existing |
| C27 | obs structure: deep MROs, inline instrument constants | low | pre-existing |
| C28 | Broad exception handlers and data asserts in the obs classes | low | pre-existing |
| C29 | Dead helpers and naming drift | low | mixed |

By severity: 1 critical (C1), 3 high (C2, C3, C5), 9 medium (C4, C6, C7, C8, C9, C19, C22,
C24, C26), 16 low.

## 1. Structure and layout

### C3. Four modules exceed the 1000-line limit, three of them newly. Severity: high

- **Location:** `src/opus_import/importdb/mysql.py` (2871 lines),
  `src/opus_import/importdb/super.py` (1731), `src/opus_import/cli.py` (1346),
  `src/opus_import/steps/do_import.py` (1021).
- **Evidence:** measured with `find src/opus_import -name '*.py' | xargs wc -l`. On
  `origin/main` the same files are 1191, 670, 698 and 314 lines, so only `mysql.py` was
  already over the limit. python.mdc §2 says "ALWAYS keep modules under 1000 lines. Split
  larger modules into a package." `mysql.py` holds at least seven separable
  responsibilities:
  - type and DDL rendering (`create_table` 956-1088, `table_info` 762-852, key clauses
    1251-1312);
  - connection and session set-up (`__init__` 340-537, commit, rollback and error codes
    2547-2594);
  - catalogue and DDL execution (table names, drop and rename 854-955, the `obs_general`
    view 1139-1250);
  - index-build space sizing (1383-1542);
  - the `LOAD DATA` bulk loader (264-322, 1870-2086);
  - row CRUD and selects (1794-1868, 2088-2545);
  - locks and counters (2596-2676, 2779-2871).
  
  It also holds two application operations that know about `cart` and `django_session`:
  `repoint_cart` and `carry_over_sessions`, 1561-1703.
- **Recommendation:** make `importdb` a package split along those lines:
  `_ddl.py`, `_session.py`, `_catalogue.py`, `_index_budget.py` (with super's
  `_SpaceBudget` and `build_indexes`), `_bulk_load.py`, `_rows.py`, `_locks.py`.
  - Move `repoint_cart` and `carry_over_sessions` into `steps/do_generation.py` and
    `steps/do_carry_over.py`, built on the generic row primitives.
  - Split `cli.py`'s 396-line argument parser into its own module (see C6).
  - Move the queue importer (`import_from_queue` and its helpers, `do_import.py:546` to
    the end) into `steps/do_import_queue.py`.

### C4. A two-brand abstraction with one brand. Severity: medium

- **Location:** `src/opus_import/importdb/super.py`, `src/opus_import/importdb/postgresql.py`,
  `src/opus_import/importdb/__init__.py:26,117-121`, `src/opus_import/importdb/mysql.py:35-41`.
- **Evidence:**
  - `grep -c 'raise NotImplementedError' src/opus_import/importdb/super.py` gives 52
    (18 on `origin/main`). Each stub carries a full docstring, and the MySQL override
    largely repeats it.
  - The only other brand is `ImportDBPostgreSQL`, a 28-line pass-through `__init__`.
    `get_db` has no branch that returns it; the branch is commented out at
    `importdb/__init__.py:117-121`. The module is 0% covered by both suites.
  - `mysqlclient` is a hard runtime dependency (`pyproject.toml`, `dependencies`), yet
    `mysql.py` keeps a no-driver simulation mode: `grep -c MYSQLDB_AVAILABLE
    src/opus_import/importdb/mysql.py` gives 19 (7 on `origin/main`), for example
    `_commit` at 2547-2550 and `stream_select` at 2442.
  - python.mdc §2 says "ALWAYS write simple, clear code; avoid unnecessary complexity".
- **Recommendation:** decide whether a second brand is a real goal.
  - **If it is not:** fold `ImportDBSuper` into the MySQL class, or keep a
    `typing.Protocol` for the surface the steps use, and delete `postgresql.py`, the
    commented branch and the `MYSQLDB_AVAILABLE` simulation. That roughly halves
    `super.py`.
  - **If it is:** keep the ABC but use `abc.abstractmethod`, so a missing override fails
    at instantiation rather than at the first call.

### C18. Dead and commented-out code. Severity: low

- **Location:**
  - `src/opus_import/importdb/postgresql.py:13-14` (commented imports);
  - `src/opus_import/importdb/__init__.py:26` and `117-121` (commented PostgreSQL import
    and branch);
  - `src/opus_import/importdb/mysql.py:732-734` (a commented logger call);
  - `src/opus_import/cli.py` in `_prepare_holdings`, `# Pds4File.require_shelves(True)`;
  - `src/opus_import/importdb/mysql.py:834`, an `elif data_type == 'mult_list':` branch
    that MySQL's `information_schema.DATA_TYPE` can never produce;
  - `src/opus_import/steps/do_partables.py` and `src/opus_import/steps/do_table_names.py`,
    whose `fill_*` callbacks return `True` unconditionally (`grep -n "return False"` finds
    none), so `rebuild_tables_by_swap`'s failure branch is unreachable for them.
- **Evidence:** all of these except the `fill_*` shapes are on `origin/main`. The
  `require_shelves` line explains why it is commented. The rest are commented code with
  no rationale, which python.mdc §4 asks to remove.
- **Recommendation:** delete the commented blocks and the unreachable branch. Either have
  `do_partables` and `do_table_names` propagate the `bool` (see C7) or type their fill
  callbacks as returning `None`.

## 2. Best practices alignment

### C1. Coordinator recovery deletes every generation's rows of a lost importer's bundle. Severity: critical (new)

- **Location:**
  - `src/opus_import/coordinator.py:443-444`, where `Coordinator._context` builds
    `ImportContext(args=argparse.Namespace(), logger=logger)` and never calls
    `do_generation.load_generation_state`;
  - `src/opus_import/coordinator.py:754-758`, where `show_status --recover` does the same;
  - `src/opus_import/coordinator.py:485`, which calls `do_recover.recover_lost_importers`;
  - `src/opus_import/steps/do_recover.py:191`;
  - `src/opus_import/steps/do_import_tables.py:214-233`.
- **Evidence:**
  - `ImportContext.pending_generation` (`context.py:322-325`) is `None` whenever
    `generation_state` is `None`. `grep -rn load_generation_state src/opus_import` finds
    it called only from `cli.py`, `do_import.py`, `do_generation.py` and
    `do_generation_purge.py`, never from `coordinator.py`.
  - `delete_bundle_from_obs_tables` branches on that value. With a pending generation it
    retires the bundle's earlier rows (`retire_bundle_rows`, line 217) and deletes only
    the pending generation's own range (`within`, line 221). With `pending is None` it
    calls `_bundle_id_ranges(db, 'obs_general', bundle_id, within=None)` (line 233). That
    walks every `obs_general_rows` row of the bundle, whatever its `added_generation`,
    and deletes those rows and their children in every `obs_` table.
  - `--join` is a permitted writer of a pending generation: it is in `cli.py`'s
    `_WRITERS` (line 664) but not `_SOLE_WRITERS`, and `choose_import_path` sends any
    import with a pending generation down `IMPORT_PATH_GENERATION`
    (`do_import.py:170-178`). So `opus_import_all --join`, or the coordinator, can drive
    queue importers into a served schema's pending generation.
  - When one of those importers dies holding a bundle, its own delete-before-import has
    already retired the served copy. The rows are still there, `removed_generation` is set
    to the pending generation, and the served view still shows them.
  - The coordinator's recovery, or anyone's `opus_import_all --status --recover`, then
    deletes them outright. The live site loses that bundle's observations, and neither
    `--abandon-generation` nor `--revert-generation` can bring them back.
  - No test exercises recovery with a pending generation. `grep -n generation` over
    `import_tests/test_coordinator.py`, `import_tests/test_concurrent_import.py`,
    `tests/opus_import/test_do_recover.py` and `tests/opus_import/test_coordinator.py`
    finds nothing.
- **Recommendation:**
  - Load the generation state on every context that deletes, in `Coordinator._context`,
    in `_pass` after a reconnect, and in `show_status`'s recovery. Better, make
    `delete_bundle_from_obs_tables` read the version row itself rather than trust a
    cached field.
  - Add an import test: begin a generation, start a `--join` importer, kill it after its
    first chunk (the existing `hold_after_chunk` fault site), run the recovery, and assert
    that the served generation's row count for the bundle is unchanged.
  - Consider refusing `--join` with a pending generation until that test passes.
  - C5 addresses the structural cause.

### C2. Raw `MySQLdb.Error` escapes the `ImportDBError` contract. Severity: high (new)

- **Location:**
  - `src/opus_import/importdb/super.py:465-466`, where `transaction()` clears
    `_in_transaction` and then calls `_commit()`;
  - `src/opus_import/importdb/mysql.py:2547-2550`, where `_commit` is a bare
    `self.conn.commit()`;
  - `src/opus_import/importdb/mysql.py:1745-1751`, `_set_foreign_key_checks`, called from
    the `finally:` of `foreign_keys_unchecked` at `super.py:1129-1133`;
  - `src/opus_import/importdb/mysql.py:1110-1111` and `1136-1137`, where
    `_execute_waiting_for_locks` sets and restores `lock_wait_timeout` outside its
    `try`/`except`;
  - `src/opus_import/importdb/super.py:343-388`, where `_execute` does not translate
    driver errors.
- **Evidence:**
  - Every caller is written against `ImportDBError`. `retrying()` catches
    `except ImportDBError as e:` only (`super.py:513`). The coordinator's outage
    tolerance, which reconnects for `DATABASE_OUTAGE_SECONDS`, catches
    `importdb.ImportDBError` only (`coordinator.py:487`). `ImporterLock.held()` does the
    same (`import_processes.py:140-143`).
  - A failed `COMMIT` therefore escapes as `MySQLdb.OperationalError`: it is not retried,
    not logged with the last statement, and it ends the coordinator. A dropped
    connection at commit is the case the outage handling exists for, and recovery's
    `holder.transaction()` commits on every pass.
  - In `foreign_keys_unchecked`, a failure to turn checks back on replaces the body's
    exception with an unrelated driver error, so the original failure is lost. The same
    happens in the `finally:` at `mysql.py:1136-1137`.
  - All of these sites are new on this branch.
- **Recommendation:**
  - Translate driver errors in one place: `_execute`, `_commit` and `_rollback` should
    wrap `MySQLdb.Error` in `ImportDBError` with `raise ... from e`.
  - In `finally:` restorers, suppress, or log and chain, a secondary failure rather than
    let it replace the primary one, as `named_lock` already does at `mysql.py:2622-2628`.
  - Add a unit test that injects a commit failure into `retrying()`.

### C7. A finalization step can log an error and still let the schema be marked ready. Severity: medium (new)

- **Location:** `src/opus_import/cli.py`, the block of `main` from "After the import, since
  the cart's foreign key needs obs_general" through `write_schema_version`.
  - `src/opus_import/steps/do_cart.py:27-31`: `create_cart` logs an error and returns
    `None`.
  - `src/opus_import/steps/do_partables.py:160-175` and
    `src/opus_import/steps/do_table_names.py:235-250` discard
    `rebuild_tables_by_swap`'s `bool`.
- **Evidence:**
  - `main` adds a step to `failed_steps` only when it returns `False`. `do_cart`,
    `do_partables`, `do_table_names`, `do_django.reset_search_tables` and
    `analyze_all_tables` return nothing.
  - `import_has_bad_data` is consulted only in `do_import.py:480`
    (`grep -rn import_has_bad_data src/opus_import`).
  - So an invocation of `--finalize --write-schema-version` whose `create_cart` logged
    "Unable to create cart" still reaches `write_schema_version` and marks the schema
    servable.
  - `main`'s own docstring concedes that "other steps report failure through the log and
    leave the status zero".
  - python.mdc §2 asks applications to make failures predictable.
- **Recommendation:** give every step one return convention (`bool`, or raise a step
  error), and have `main` treat any `log_error` during a finishing step as a failure. A
  per-step snapshot of `ImportLog`'s error count is enough.

### C9. Optional parameters are positional. Severity: medium (mixed)

- **Location:** `src/opus_import/importdb/__init__.py:58` (`get_db`, 12 positional),
  `importdb/super.py:262` and `importdb/mysql.py:340` (both `__init__`, 11 besides
  `self`), `steps/do_import_mult.py:456` (`update_mult_table`, 10),
  `steps/do_generation.py:736` (`command_step`, 6),
  `steps/do_import_index.py:790` (`get_opus_products_rows_for_filespec`, 7).
- **Evidence:**
  - An `ast` scan over `src/opus_import` counts 74 functions, of 1895, whose
    defaulted parameters are positional rather than keyword-only. The most are in
    `obs/obs_base.py` (17), `importdb/super.py` (15) and `importdb/mysql.py` (14).
  - It counts 17 functions with more than five positional parameters besides
    `self`/`cls`. Two of those are `warnings.showwarning`-shaped handlers whose
    signature is fixed.
  - The 12-parameter connection signature is written out four times: `get_db`, both
    `__init__`s, and the call in `open_sibling_connection` at `super.py:936-948`.
  - python.mdc §2 says "Optional and configuration parameters MUST be keyword-only", and
    asks for the Receive-an-Object, Return-an-Object (RORO) pattern when a function takes
    many related values.
- **Recommendation:** introduce a frozen `ConnectionSettings` dataclass, built once from
  `OpusConfig` and passed to `get_db` and `open_sibling_connection`. Make the remaining
  flags keyword-only. For `update_mult_table`, pass a `MultValue` dataclass, which also
  makes the pool's `*values` replay (`do_import_pool.py`, `_replay`) explicit.

### C15. Bundle state names repeated as raw strings. Severity: low (new)

- **Location:** `src/opus_import/coordinator.py:118-121` (`snapshot.count("done")` and the
  like), `150`, `207`, `614`, `639`, `651`, `667`, `711`; `src/opus_import/import_all.py:115-116`.
- **Evidence:** `bundle_registry.py:50-62` defines `BUNDLE_PENDING`, `BUNDLE_IMPORTING`,
  `BUNDLE_DONE` and `BUNDLE_FAILED`, and `coordinator.py:89` uses two of them. The 13
  sites above spell the same values as literals (`grep -rnE "'(pending|importing|done|failed)'"`
  plus the four double-quoted `count(...)` calls). python.mdc §2 says "NEVER hardcode
  magic constants".
- **Recommendation:** make the states a `StrEnum` in `bundle_registry`, so `BundleStatus.state`
  is typed and a misspelling is a mypy error.

### C17. Library hygiene. Severity: low (pre-existing)

- **Location:** `src/opus_import/import_util.py:319` (`sys.exit(-1)` inside
  `yield_import_bundle_ids`); `src/opus_import/import_util.py:401` and
  `src/opus_import/steps/do_import_index.py:243` (`open()` without `encoding=`).
- **Evidence:**
  - `grep -rn 'sys\.exit' src/opus_import` finds 23 calls in `cli.py`, 1 in
    `import_all.py` and 1 in `import_util.py`. Only the last is outside an entry point.
  - Both encoding-less `open` calls read CSV index files and are on `origin/main`.
  - The `print()` calls are confined to the entry points `coordinator.py`,
    `import_all.py` and `util/`.
  - The skill's library-hygiene checklist and python.mdc §2 apply.
- **Recommendation:** raise a `BundleDescriptorError` from `yield_import_bundle_ids` and
  let `cli.main` exit. Add `encoding='utf-8'` (and `newline=''` for `csv`) to both opens.

## 3. Types and static checks

### C5. `ImportContext` is untyped where it matters and optional everywhere. Severity: high (new)

- **Location:** `src/opus_import/context.py:274-306`; `src/opus_import/coordinator.py:443,754`.
- **Evidence:**
  - The dataclass has 30 annotated fields (an `ast` count). Most start as `None` and are
    filled in by whichever step runs first.
  - `args: argparse.Namespace` makes every option read `Any`.
    `grep -rnE '(ctx|_ctx)\.args\.[a-z_]+'` finds 35 reads outside `cli.py` and
    `import_all.py`. Strict mypy cannot check any of them.
  - The coordinator builds contexts with an empty `argparse.Namespace()`. A recovery path
    that one day reads `ctx.args.log_suppress_traceback`, as `import_util.py:301` and
    `481` do, would fail at run time, invisibly to the type checker.
  - `db: ImportDBSuper | None` forces narrowing at every use:
    `grep -rnE '^\s*assert (ctx\.)?db is not None' src/opus_import` counts 104.
  - `generation_state` defaults to `None`, which means both "no version row" and "never
    loaded". That ambiguity is exactly what lets C1 happen.
- **Recommendation:**
  - Replace `args` with a frozen, typed `ImportOptions` dataclass built in `cli.main`.
  - Split the context into what a run is given (options, logger, database: required at
    construction) and what it accumulates.
  - Make generation state a tri-state, or load it in the constructor, so "not loaded"
    cannot be mistaken for "none".
  - Provide `ImportContext.require_db()`, or pass `db` explicitly, instead of 104 asserts.

### C13. Integrity checks written as `assert`. Severity: low (mixed)

- **Location:** for example `src/opus_import/importdb/mysql.py:1996`
  (`assert row.keys() == columns` before a row is written to the bulk-load file) and
  `src/opus_import/steps/do_import_pool.py:300` (`assert set(id_counts) <= {'obs_general'}`).
- **Evidence:**
  - `grep -rnE '^\s*assert ' src/opus_import --include=*.py | wc -l` gives 279. Most
    narrow types (104 are `assert db is not None`; see C5), which is what the B101 waiver
    in `docs/dev_guide_conventions.rst` covers.
  - A minority guard data, and under `python -O` they vanish. A row with an extra key
    would then be loaded with that column silently dropped.
- **Recommendation:** keep `assert` for type narrowing. Turn the data-integrity checks
  into explicit `if ...: raise ImportDBError(...)` with the offending values in the
  message.

### C23 (types). `cast()` in place of validation. Severity: low (mostly pre-existing)

- **Location:** concentrated in `src/opus_import/obs/`.
- **Evidence:**
  - `grep -rn 'cast(' src/opus_import --include=*.py | wc -l` gives 282. The most are
    `obs/obs_volume_cocirs_01xxx.py` (39) and `obs_volume_vg2810.py`,
    `obs_volume_couvis_covims_occ_common.py` and `obs_volume_corss_8xxx.py` (18 each).
  - Index-row values are `Any`, and `cast(FloatField, self._index_col(...))` tells mypy
    they are floats without checking.
  - At least one cast is not needed:
    `obs/obs_bundle_cassini_iss_fring_mosaics_rsfrench2025.py:72` casts
    `self.bundle + '/' + rel.strip()`, already a `str`, to `str | None`.
  - Strict mypy passes, but at these boundaries it proves little.
- **Recommendation:** add typed accessors on the obs base (`_index_float`, `_index_str`)
  that check or convert once, and drop the per-site casts.

## 4. Testing

### C19. Coverage gaps where it matters. Severity: medium (mixed)

- **Evidence:**
  - **Unit suite** (`tests/opus_import`, 1135 tests passing): 8313 of 12038 statements
    (69.1%) and 1841 of 3564 branches (51.7%) of `opus_import`. That suite alone fails
    the `pyproject.toml` threshold of 74%, which is set for the whole repository.
  - **Import suite** (207 passed, 3 skipped): 10271 of 12038 statements (85.3%) and
    2492 of 3564 branches (69.9%). The union of the two suites' executed lines is 10870
    statements (90.3%): the unit suite reaches 599 statements the import suite does not,
    most of them in `importdb/mysql.py` (93), `steps/do_import.py` (69), `coordinator.py`
    (51) and `importdb/super.py` (50).
  - **Well covered under the import suite** (statements and branches):
    `import_processes.py` 96.1%, `do_generation_purge.py` 95.6%, `table_swap.py` 95.2%.
    The rest of the orchestration sits near the package figure: `bundle_registry.py`
    87.3%, `do_recover.py` 86.2%, `do_import_pool.py` 85.7%, `do_generation.py` 83.7%,
    `coordinator.py` 82.7%.
  - **Weakest under the import suite:**
    - `importdb/postgresql.py`: 0%.
    - `util/dump_pds_definitions.py` and `util/retrieve_ra_dec.py`: 0%. Both are
      utilities.
    - `obs/obs_bundle_cassini_iss_fring_mosaics_rsfrench2025.py` 34.3%,
      `obs/obs_cassini_common_pds4.py` 40.3%, and the HST classes
      `obs_volume_hstix_xxxx.py` 52.6%, `hstjx` 54.2%, `hstnx` 59.7%.
    - `import_util.py` 64.9% (131 statements missed).
    - `import_all.py` 73.6%, `steps/do_import_obs.py` 75.1% and `steps/do_import.py`
      75.6%.
    - `importdb/mysql.py` 79.3%. Its missed lines include nearly all of
      `ImportDBMySQL.__init__`'s failure branches (406-579), which is where C10 lives.
  - **Untested behavior:** recovery with a pending generation (C1); a commit failure
    inside `retrying()` (C2); `create_cart` on a schema without `obs_general` together
    with `--write-schema-version` (C7).
  - The tests are named by area rather than mirroring the modules (`tests/opus_import/`
    has no `test_mysql_*` split matching `importdb/`). The test reviewer covers this;
    it is noted only because it makes these gaps harder to see.
- **Recommendation:**
  - Add the three tests above first.
  - Give the PDS4 and HST obs classes fixture rows in the mini-holdings.
  - Exercise `ImportDBMySQL.__init__`'s failure paths with a fake `MySQLdb.connect`.

## 5. Performance and resource use

### C16. Observation-id space is consumed and never reclaimed. Severity: low (new)

- **Location:** `src/opus_import/bundle_registry.py:65-71`, `183-206` (`plan_ranges`);
  `src/opus_import/steps/do_register.py:242-249`.
- **Evidence:**
  - Every new registry row reserves `ID_CAPACITY_FACTOR = 100` ids per declared row.
  - It starts at `max(row.end)` over every row, retired ones included
    (`do_register.py:243`), up to `MAX_OBSERVATION_ID = 4_294_967_295`.
  - Appends reuse a bundle's range, but every re-import into a pending generation lays
    out a new range after the highest one. Purging retired rows never lowers that
    maximum, because later ranges remain.
  - Over a schema's life between scorched-earth imports, the declared rows of all
    generation re-imports together can therefore total at most 4,294,967,295 / 100 ≈
    42.9 million before registration refuses (`RegistrationError`).
  - Separately, a label that declares 0 rows gets a range of 0 ids, so any observation
    that bundle later yields fails with `BundleIdRangeError`. `take`'s message then
    prescribes a full import.
  - Neither condition is reported before it is hit.
- **Recommendation:** log the fraction of id space used at each registration and warn at
  a threshold. Give a 0-row estimate a minimum capacity. Consider compacting the id
  space during `--purge-generations` when nothing follows the purged ranges.

### C12. Named locks: unbounded wait, unchecked release. Severity: low (new)

- **Location:** `src/opus_import/importdb/mysql.py:2615` (`SELECT GET_LOCK(%s, -1)`),
  `2629` and `2836` (`RELEASE_LOCK` results ignored).
- **Evidence:**
  - The registration lock is taken by `do_register.register_bundles`, and by every
    queue importer's `_wait_for_registration` (`do_import.py`) whenever its claim finds
    nothing. With an infinite timeout, one hung registrant blocks every importer with no
    message.
  - A `RELEASE_LOCK` returning 0 (not the holder) or NULL (no such lock) means the
    locking protocol was violated, and that passes silently.
  - Acquire and release are correctly paired, including on the exception path
    (2622-2628).
- **Recommendation:** use a finite timeout, from a named constant, with a log line naming
  the lock when it expires. Log a warning when `RELEASE_LOCK` does not return 1.

The fork pool (`steps/do_import_pool.py`) is sound:

- the work is bounded by `TASKS_AHEAD_PER_WORKER`;
- workers ignore SIGINT and die with their parent;
- the pool state is a documented module global (`_STATE`, line 102) that exists only for
  inheritance by `fork`;
- the result is collected without a timeout (`future.result()`), so a worker blocked on
  I/O stalls the import silently. The coordinator's stall warning
  (`stall_warning_minutes`) partly covers this.

## 6. Maintainability and extensibility

### C6. Seventeen functions exceed 100 lines. Severity: medium (mixed)

- **Evidence:** an `ast` scan measured these lengths, including docstrings, against the
  same functions on `origin/main`:

  | Function | Lines at HEAD | Lines on `origin/main` |
  |---|---|---|
  | `cli.main` | 413 | 252 |
  | `cli._create_argument_parser` | 396 | 362 |
  | `do_import_obs.import_observation_table` | 362 | 350 |
  | `do_import_index.import_one_index` | 334 | 612 |
  | `do_import_index.get_opus_products_rows_for_filespec` | 199 | 204 |
  | `importdb/mysql.py` `__init__` | 198 | 165 |
  | `import_util.yield_import_bundle_ids` | 190 | 190 |

  `import_one_index` was roughly halved on this branch.
  - `cli.main` repeats
    `limits={'info': args.log_info_limit, 'debug': args.log_debug_limit}` 9 times
    (`grep -c`), in a run of `logger.open` / `ctx.timed` / `logger.close` blocks.
  - `ImportDBMySQL.__init__`'s create-database branch (`mysql.py:459-484`) nests seven
    blocks deep.
- **Recommendation:**
  - Express `cli.main`'s finishing sequence as a table of steps, each with a name, an
    enabling option, a pending-generation policy and a callable, run by one loop that
    handles timing, log sections and failures. That also fixes C7.
  - Move the session set-up out of `ImportDBMySQL.__init__` into a `connect()` factory.

### C8. Repeated boilerplate in the database layer. Severity: medium (mostly new)

- **Evidence:**
  - `grep -c "except MySQLdb.Error as e:" src/opus_import/importdb/mysql.py` gives 31.
    Most are the same three lines: `_log_failure(...)`, then `raise ImportDBError(e) from e`.
  - The sequence "cursor, execute, read `rowcount`, `if not self._in_transaction:
    commit`" recurs at `mysql.py:640-645`, `1601-1607`, `2134-2139`, `2179-2183` and
    `2662-2671`.
  - The 1000-row packet loop is duplicated in `insert_rows` (1838) and `upsert_rows`
    (2261), with the magic number inline both times (`packet_size = 1000`).
  - `grep -c "if self.logger:"` gives 23 in `mysql.py` and 5 in `super.py`.
  - python.mdc §2 says "ALWAYS apply DRY".
- **Recommendation:**
  - Add one `_statement(cmd, params, *, what) -> cursor` helper that executes, translates
    errors (C2) and commits outside a transaction.
  - Name the packet size as a module constant.
  - Give the class a `NullLogger` default so the 28 logger checks disappear.

## 7. Security and robustness

### C14. SQL text built from schema JSON without escaping. Severity: low (mixed)

- **Location:** `src/opus_import/importdb/mysql.py:1041`
  (`field_default = "'" + field_default + "'"`), `1007` (`column['constraint']`
  verbatim), `1022` (`enum({enum_str})` verbatim), and `1188`
  (`condition.replace('%s', str(int(served)))`).
- **Evidence:**
  - All of these inputs come from packaged `table_schemas/*.json` or an `int`, so this is
    not an injection path today.
  - Identifiers are uniformly validated and backtick-quoted by `quote_identifier`
    (`\A[A-Za-z0-9_]+\Z`, `mysql.py:668`), and values are bound as parameters elsewhere.
  - A default containing `'` would produce broken DDL rather than an error naming the
    column.
  - Substituting a placeholder by `str.replace` breaks as soon as the condition gains a
    second placeholder or a literal `%s`.
  - `grep -c 'nosec B608'` gives 21 in `mysql.py` and 1 in `super.py`, each at a
    statement built from identifiers.
  - security.mdc §3 says "NEVER trust external input", and schema JSON is input to this
    layer.
- **Recommendation:** escape the default (`self.conn.literal`) or validate it against its
  type. Render the view condition from a function that takes the generation as an `int`
  rather than editing a parameterized string.
- **Secrets:** checked and clean. The password reaches the server only through
  `MySQLdb.connect(passwd=...)` (`mysql.py:429`), appears in no log line or exception
  text (`grep -n "password\|passwd"` over `importdb/`), and is never on a command line.
  The coordinator starts importers with `[sys.executable, '-m', 'opus_import', *arguments]`
  (`coordinator.py:228`), with credentials only in the `OPUS_CONFIG` file.

### C10. Connection leaked when `ImportDBMySQL.__init__` fails after connecting. Severity: low (pre-existing, widened)

- **Location:** `src/opus_import/importdb/mysql.py:426` (connect), with later failures
  raising at 447-491 (`USE` / `CREATE DATABASE`), 510 (`SELECT VERSION()`), 525-527
  (`sql_mode`), 533-535 (`READ COMMITTED`, new) and 537 (`_prepare_import_session`, new).
- **Evidence:** each raises `ImportDBError` without closing `self.conn`, and the caller
  never gets the instance to close. The coordinator reopens a connection on every pass
  during an outage (`coordinator.py:478-481`), which can accumulate leaked connections
  for up to `DATABASE_OUTAGE_SECONDS`.
- **Recommendation:** wrap everything after `connect` in `try: ... except BaseException:
  self.conn.close(); raise`, or move it into a `connect()` factory (C6).

### C11. Transaction-unaware commits. Severity: low (new, latent)

- **Location:** `src/opus_import/importdb/mysql.py:2455` (`stream_select` commits
  unconditionally), `1694`/`1696` (`carry_over_sessions` commits or rolls back
  unconditionally), `2664-2667` (`increment_counter` raises on `rowcount != 1` after
  the `UPDATE` has run, without rolling back).
- **Evidence:**
  - Every other mutating method guards with `if not self._in_transaction:` (for example
    2138, 2182).
  - Called inside `transaction()`, the first two would commit the caller's work early.
  - Outside a transaction, the third leaves the increment pending, for the next commit
    to make permanent.
  - Today's callers (`steps/do_finalize_mult.py:118`, `steps/do_carry_over.py:46`) run
    outside a transaction, so nothing is wrong yet.
- **Recommendation:** route these through the common statement helper (C8). Have
  `increment_counter` require a transaction, or roll back before raising.

### C21. Test fault hooks in production paths. Severity: low (new)

- **Location:** `src/opus_import/import_fault.py`; nine `*_FAULT_SITE` constants
  (`grep -rn "_FAULT_SITE = "`), read at eight call sites
  (`grep -rn "import_fault_argument("`) in `table_swap.py`, `do_generation.py`,
  `do_import.py`, `do_import_pool.py` and `import_processes.py`.
- **Evidence:**
  - Any production process whose environment carries `OPUS_IMPORT_FAULT` fails or hangs
    on purpose. `hold_while_present` waits up to `HOLD_LIMIT_SECONDS = 300` per site.
  - The module docstring says "Nothing outside a test sets the variable", but nothing
    enforces it.
  - These seams are what make the recovery tests possible, which is valuable.
- **Recommendation:** log a warning when the variable is set at all, at start-up in
  `cli.main`, so an accidental setting is visible in the run log. Consider requiring a
  second variable, such as `OPUS_IMPORT_TESTING=1`, to arm it.

## 8. Dependencies and tooling

### C20. No version floor on dependencies the import relies on. Severity: low (pre-existing)

- **Location:** `pyproject.toml`, `[project] dependencies`.
- **Evidence:**
  - `mysqlclient`, `rms-pdslogger` and `rms-pdstable` carry no minimum version.
  - The import uses recent API on each: `pdslogger.file_handler(..., suffix=...)` in
    `cli.py`; `MySQLdb.cursors.SSCursor` with `local_infile`; and
    `pdstable.PdsTable(..., defer_load=True)` in `primary_index.py:166`.
  - dependency_management.mdc says "Specify **minimum** compatible versions for direct
    dependencies".
- **Recommendation:** add floors at the versions that introduced the features used.

Tool configuration is otherwise consistent. mypy is strict with no `ignore_errors`
entries, and `opus_import` has one `# type: ignore[attr-defined]`
(`do_import_pool.py:238`, a monkeypatched class logger) and one `# noqa`. `ruff`'s
per-file-ignores table is empty. bandit's 32 per-line `nosec` markers (50 `B608`
mentions, 3 `B404`, 3 `B603`, by `grep -o`) each carry a reason.

## 9. Technical debt and risk

- `grep -rnE 'TODO|FIXME|XXX|HACK' src/opus_import` finds 13 markers, the same count as
  on `origin/main`. Seven are `TODOPDS4` and concern the label-less PDS4 index CSVs
  (for example `import_util.py:395-399`). They are confined to the PDS4 and occultation
  classes and are not linked to issues.
- The branch adds the generation machinery: a view over `obs_general_rows`, the
  `__new`/`__old`/`__prev` table swaps, and a multi-step, resumable switch, revert and
  purge. The design is carefully specified in its docstrings and well covered
  (section 4). The risk it adds is that every component that deletes or reads
  observation rows must know which generation it is in. C1 is the first instance found;
  C5 is the structural fix.

## 10. Packaging and distribution

- `src/opus_import/py.typed` is present. `table_schemas/*` and `dictionary_data/*` are
  declared as package data (`pyproject.toml`, `[tool.setuptools.package-data]`) and
  checked by `tests/opus_import/test_package_data.py`.
- `opus_import/__init__.py` deliberately imports nothing and has no `__all__`; its
  docstring says the package is a program with no API stability guarantee. 3 of 117
  modules declare `__all__` (`grep -rl '^__all__'`). Given that stated non-library status
  this is acceptable, but python.mdc §3 asks for `__all__`. The cheap compromise is
  `__all__` on the modules other packages import: `importdb` already has one;
  `generations`, used by the database layer, and `schema_version` do not.

## 11. obs hierarchy and utilities

This section covers `src/opus_import/obs/`, `import_util.py`, `steps/do_import_index.py`,
`steps/do_import_obs.py`, `config_targets/` and `util/`. Almost all of this code is
unchanged from `origin/main`.

### C22. A recoverable field error crashes the index instead of nulling the column. Severity: medium (pre-existing; asserts re-sited on this branch)

- **Location:** `src/opus_import/steps/do_import_obs.py:144-146`, `335-346`, `135`, `359`;
  `src/opus_import/steps/do_import_index.py:662`, `711`, `786`.
- **Evidence:**
  - `import_run_field_function` is log-and-continue. When a field method raises, the
    column becomes `[None]` (line 146).
  - For a column whose form type is in `GROUP_FORM_TYPES`, `mult_label_list` is then
    still `None`. `import_observation_table` logs "bad data type returned for mult" and
    returns `None` for the whole row (line 346).
  - All three callers then `assert obs_row is not None` (`do_import_index.py:662`, `711`,
    `786`). One bad value in one GROUP column therefore raises `AssertionError` and
    abandons the index.
  - In a plain `opus_import`, that exception reaches `cli.main`'s top-level handler and
    ends the whole run, `--ignore-errors` included. Under `python -O` the assert vanishes
    and `None` is emitted as a row.
  - Two related `IndexError`s escape the same function's error handling:
    - `mult_label[0]` (line 359) on an empty-string GROUP value. The VARCHAR check
      itself produces that value at line 226 when a value is not a `str`.
    - `ret[0]` (line 135) when a `mult_list` field returns `[]`, which its docstring
      says means NULL.
  - The `assert` in `import_one_index` is reached from an untested path:
    `import_run_field_function` is 0 of 13 statements under the unit suite.
- **Recommendation:**
  - Have a failed GROUP field fall back to the field's absent mult value, as
    `update_mult_table` does for a pinned field, rather than returning `None`.
  - Guard the two indexings (`if mult_label`, `if len(ret) == 0`).
  - Replace the three asserts with a logged skip of the observation.

### C24. The PDS4 CSV type inference silently changes values. Severity: medium (pre-existing)

- **Location:** `src/opus_import/import_util.py:410-430` (`safe_pdstable_read`, the
  label-less PDS4 path, `TODOPDS4`).
- **Evidence:**
  - Each column becomes `int` if every cell parses as one, otherwise `float` if every
    cell does, otherwise stripped `str`.
  - So zero-padded identifiers lose their zeros (`'007'` becomes `7`).
  - A single blank cell leaves an otherwise numeric column as strings. Field code such as
    `wl / 1000.0` (`obs/obs_bundle_occ_common.py:51`) then raises `TypeError` on a
    string.
  - The function is 0 of 22 statements under the unit suite.
- **Recommendation:** drive the conversion from the column definitions the obs classes
  read, or at least treat blank cells as `None` and never convert a column whose name
  marks it as an identifier. Add a unit test with padded and blank cells.

### C25. A dead `None` check hides a missing file specification. Severity: low (pre-existing)

- **Location:** `src/opus_import/obs/obs_base_pds3.py:68-77`.
- **Evidence:** when `FILE_SPECIFICATION_NAME` is absent, `filespec = path_name + filename`
  is always a `str`, so the following `if filespec is None:` can never fire. A row with
  none of the three columns becomes `'<bundle>/'` rather than logging "Index missing
  FILESPEC field(s)". This is the falsy-check confusion python.mdc §1 warns about.
- **Recommendation:** test `if filespec == '':` or `if filename == '':`.

### C26. Duplication across the obs classes. Severity: medium (pre-existing)

- **Evidence:** an `ast` scan of normalized function bodies over this section's scope,
  with docstrings stripped and at least 2 statements, finds 26 groups of exact duplicates
  covering 66 functions. With constants also normalized and at least 3 statements, it
  finds 29 near-duplicate groups covering 97 functions and 711 lines. Examples:
  - `primary_filespec`, the same body in six classes: `obs_cassini_common.py:627`,
    `obs_volume_ebrocc_xxxx.py:73`, `obs_volume_hubble_common.py:82`,
    `obs_volume_nhxxlo_xxxx.py:41`, `obs_volume_nhxxmv_xxxx.py:40`,
    `obs_volume_voyager_common.py:50`.
  - `field_obs_type_image_levels` five times (`couvis_0xxx`, `hstix`, `hstjx`, `hstnx`,
    `hstox`).
  - The occultation flags (`occ_dir`, `body_occ_flag`, `quality_score`) are identical in
    `obs_bundle_cassini_uvis_solarocc_beckerjarmak2023.py:71-90` and
    `obs_bundle_uranus_occs_earthbased.py:220-239`. Both subclass `ObsBundleOccCommon`,
    which does not define them.
  - `_ring_geo_index_col` and `_surface_geo_index_col` (`obs_base.py:473` and `547`)
    differ only in a metadata key.
  - python.mdc §2 says "ALWAYS apply DRY".
- **Recommendation:**
  - Hoist each group to the nearest common base: `primary_filespec` into the PDS3 base,
    parameterized by column, and the occultation flags into `ObsBundleOccCommon`.
  - Merge the two geometry accessors behind a key parameter.
  - The New Horizons LORRI and MVIC modules share most of their lines and could become
    one parameterized class.

### C27. obs hierarchy structure: deep MROs, inline instrument constants. Severity: low (pre-existing)

- **Evidence:**
  - Leaf classes carry 194-235 `field_obs_*` methods, with MROs of up to 20 classes (for
    example `ObsVolumeCOUVIS8xxx` and `ObsVolumeCOVIMS8xxx`), found by introspecting
    `opus_import.obs`. 124 of the 1111 field methods are one-line stubs (`return None`,
    `return self._create_mult(None)`, `raise NotImplementedError`), often overridden
    three layers deep.
  - Instrument constants are inline, for example the UVIS band widths at
    `obs_volume_couvis_0xxx.py:286-323` and the VIMS resolutions at
    `obs_volume_covims_0xxx.py:226-232`.
  - Unit conversions are repeated as literals with comments: `ruff check --select
    PLR2004` reports 35 magic-value comparisons in scope.
  - Mission bundle lists are hard-coded in an if/elif chain in
    `import_util.yield_import_bundle_ids` (`import_util.py:189-280`). The `ALL` list
    repeats the others.
  - Exact float comparisons against longitude sentinels (`== 0` and `== 360`): 9 in
    `obs_ring_geometry.py` and 4 in `obs_surface_geometry_target.py` (`grep -c "== 360"`).
  - Three modules sit just under the limit of C3: `do_import_index.py` 988 lines (888
    on `origin/main`), `import_util.py` 985 (940), `obs/obs_base.py` 963.
  - python.mdc §2 says "NEVER hardcode magic constants".
- **Recommendation:**
  - Name the instrument and unit constants (`NM_PER_MICRON` and similar) in one module.
  - Derive the bundle lists from `config_bundle_info`.
  - Compare sentinels with a tolerance.
  - Split `import_util.py` along the five groups its own docstring lists before it
    crosses 1000 lines.

### C28. Broad exception handlers and data asserts in the obs classes. Severity: low (pre-existing)

- **Location:** `obs/obs_base.py:843`, `880`, `921` (time and SCLK parsing);
  `obs/obs_cassini_common.py:680` (orbit parsing); `steps/do_import_obs.py:469`
  (the field-function wrapper); `import_util.py:479`.
- **Evidence:**
  - Each is `except Exception`. The parse sites log a nonrepeating error, so nothing is
    silent, but they also turn programming errors into data errors.
  - Separately, obs code asserts on index-derived values. For example
    `obs/obs_general.py:106-107` asserts `time1 is not None` and `time2 is not None` in
    the duration computation, so a masked time becomes an `AssertionError` traceback per
    field rather than a null.
  - python.mdc §2 says "ALWAYS catch exceptions at the smallest granularity possible".
- **Recommendation:** narrow the parse handlers to the parsers' documented exceptions
  (`ValueError`, plus whatever `julian` raises). Make the duration and similar fields
  return `None` when an input is `None`.

### C29. Dead helpers and naming drift. Severity: low (mixed)

- **Evidence:**
  - `import_util.log_unknown_target_name` (`import_util.py:941`) has no caller in `src/`
    (`grep -rnw log_unknown_target_name src/`).
  - `safe_pdstable_read_pds3`'s preprocessing hook is always `None`, and its loop is
    commented out at `import_util.py:449-455`. The branch it guards and the `pdsparser`
    import exist only for it.
  - `import_run_field_function` takes `table_schema` and `metadata` and its docstring
    says they are "Not read here" (`do_import_obs.py:448-451`).
  - New on this branch: the mult columns were renamed from display order to `pin`, but
    `PlanetGroup` still names its field `disp_order`
    (`config_targets/planet_group_mapping.py:18`), and callers pass
    `group_info['disp_order']` as `group_pin=` (`obs/obs_general.py:90`,
    `obs/obs_surface_geometry_target.py:55`).
- **Recommendation:** delete the dead helper, the hook and the unused parameters. Rename
  `PlanetGroup.disp_order` to `pin`.

## Recommended priorities

1. **C1:** load, or read, the generation state wherever recovery deletes, and add the
   pending-generation recovery test. Until then, refuse `--join` and `--status --recover`
   on a schema with a pending generation.
2. **C2:** translate every driver error into `ImportDBError` in one place, and make the
   `finally:` restorers preserve the primary exception. Add a commit-failure test for
   `retrying()`.
3. **C7:** one success convention for every step, and any logged error during a finishing
   step blocks `--write-schema-version`. Do it together with the step-table rewrite of
   `cli.main` (C6).
4. **C5:** typed `ImportOptions` in place of `argparse.Namespace`; a context whose database
   and generation state are required and loaded at construction.
5. **C3, C4, C8:** split `importdb` into a package by responsibility. Decide on the
   second brand; if there is none, fold the ABC into a Protocol and delete
   `postgresql.py` and the `MYSQLDB_AVAILABLE` simulation. Factor the statement and
   error boilerplate.
6. **C22, C24, C19:** make a failed GROUP field fall back to its absent value instead of
   crashing the index; stop the PDS4 CSV inference from rewriting values. Add PDS4 and HST
   obs fixtures and `ImportDBMySQL.__init__` failure-path tests.
7. **C26:** hoist the duplicated obs methods to their common bases.
8. **C9, C10, C11, C12:** a `ConnectionSettings` dataclass, keyword-only flags, a
   leak-free connect, transaction-aware commits, finite named-lock waits.
9. **C16:** report id-space consumption at registration.
10. **C13, C14, C15, C17, C18, C20, C21, C23, C25, C27, C28, C29:** low-severity cleanups, best scheduled with
   the module splits that touch the same code.
