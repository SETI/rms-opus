# Test Suite Critique Report: the `opus_import` test suites

**Generated:** 2026-11-19

**Tree:** commit `2794cd36e8b6eab2a244e7c8a197b20095e8bfd8`, branch `db-perf-pr-26a`

**Scope:** the tests of `src/opus_import/` at that commit:

- `tests/opus_import/` (the fast, holdings-free unit tier, with its `conftest.py`,
  `_source_scan.py` and `fixtures/obs_field_values.json`), plus the root `tests/conftest.py`
  it inherits;
- `import_tests/` (the end-to-end suite against the checked-in mini-holdings fixture and a
  MySQL server: its `conftest.py`, `goldens/`, `fixtures/` and `tools/`), plus
  `tests/import_tests/` (the unit tests of those tools);
- how CI runs them: `.github/workflows/run-tests.yml` (`test` and `import-tests` jobs) and
  the `[tool.pytest.ini_options]` / `[tool.coverage.*]` tables of `pyproject.toml`.

**Out of scope:** tests of `opus_app`, `opus_log_analyzer`, `opus_support`, `opus_config`;
`integration_tests/`; the code and the documentation themselves (judged here only as far as
needed to say whether the tests test them).

**Standards applied:** `.cursor/skills/critique-test-suite/SKILL.md` (workflow, checklist,
output template); `.cursor/rules/python_testing.mdc` (primary); `.cursor/rules/python.mdc`;
`CLAUDE.md`; `docs/dev_guide_testing.rst`. The repository ships no `logging.mdc`,
`logging_nav.mdc` or `filecache.mdc`, so per the skill the logging-convention and
file-access checks that depend on them are skipped, not reported.

**Old vs new:** "new" below means a test file, tool or setting added or changed by the
database-performance work, measured with
`git diff --name-status origin/main...HEAD -- tests/opus_import import_tests tests/import_tests`
(37 Python files added, 22 modified). "Pre-existing" means `origin/main` already had it.

## Status at a124e126

This section records which findings commit `a124e126` (branch `db-perf-pr-26`) has fixed.
The findings below were written against `2794cd36` and are kept as written, with that
tree's line numbers; the line numbers in this section are `a124e126`'s. Every status was
checked by reading the tests, the CI workflow and the code at `a124e126`, not taken from
commit messages.

Four squash merges reached the branch after the critiqued tree, and the evidence names the
one that made each fix: `acb22dd4` (`[DB · PR-26a]`), `c8fb9d0c` (`[DB · PR-26b]`),
`56b917e7` (`[DB · PR-26c]`) and `a124e126` (`[DB · PR-26d]`). `2794cd36` is a commit of
the PR-26a branch from before its squash, so it is not an ancestor of `a124e126`; the merge
base is `0eb24745`. `git diff --stat 2794cd36 a124e126 -- import_tests tests/import_tests
.github` lists only `import_tests/goldens/param_info.tsv`, `import_tests/test_generations.py`,
`import_tests/test_schema_version.py` and `import_tests/test_unit_layers.py`.

Status keys: **Fixed**, the gap is closed as the recommendation asked; **Partly fixed**,
with what remains; **Open**, with where the gap is at `a124e126`.

| ID | Status | Evidence at `a124e126` |
| --- | --- | --- |
| T1 | **Partly fixed** | `56b917e7`, with the comment refined in `a124e126`. `fail_under` is 79 (`pyproject.toml:336`), and its comment (`:321-335`) states the rule and names the command that regenerates the figure in place of the stale counts. Remaining: the `test` job still runs the unit tier without coverage (`.github/workflows/run-tests.yml:129`), only `pytest import_tests` is measured (`:195-199`), and nothing combines the two tiers or gates their union. |
| T2 | **Partly fixed** | `56b917e7`. Parametrized tests on a one-column harness (`tests/opus_import/test_do_import_obs.py:177`) cover each FLAG spelling and an invalid one, a VARCHAR value of another type and one too long, an unparsable REAL and INT, a missed sentinel, values below and above the bounds with and without `val_set_invalid_to_null`, a NULL in a NOT NULL column, an ordinary value, and a field method reported failed (`:203-310`), asserting the stored value and the logged text and level. Remaining: every one of them replaces `import_run_field_function`, so its own missing-method and raising branches (`src/opus_import/steps/do_import_obs.py:478-497`) are still not executed by the unit tier (the run below). The import tier was not re-run. |
| T3 | **Open** | `src/opus_import/import_util.py` is unchanged, and no test calls `yield_import_bundle_ids`: its three references in the unit tier replace it (`tests/opus_import/conftest.py:445`, `test_queue_importer.py:47`, `test_bundle_registry.py:294`). |
| T4 | **Open** | `make_context(**kwargs: Any)` is at `tests/opus_import/conftest.py:123`; `RegistryDB`'s `read_rows(columns=...)`, `quote_identifier(name)`, `delete_rows` and static `named_lock_holder` (`:220`, `:238`, `:289`, `:348`) keep the four disagreements; `_RecordingDB` is still defined in four modules. |
| T5 | **Fixed** | `56b917e7`. `import_tests/test_unit_layers.py` runs against MySQL `--requeue`'s hold, delete and move of a failed bundle (`:286`), `set_next_id` on a table holding rows (`:307`), the index-space budget's query (`:323`), the reads of `generation_problem`, which replaced `generation_command_problem`, for each `opus_import --check` action the deploy chain asks (`:346`), and a bounded-wait rename's lowered and restored `lock_wait_timeout` (`:375`). The `upsert_row` tests remain, as does the method, which still has no caller in `src/` (`grep -rnw upsert_row src/`); the recommendation drops them only with the method. Whether the finding's other listed functions are still reached only by fakes was not re-measured, since the import tier was not run. |
| T6 | **Open** | `import_tests/test_goldens.py` is unchanged: `reimport` (`:267`) still re-imports into `main_run.schema`. |
| T7 | **Open** | `import_tests/tools/obs_execution.py` is unchanged; `DEFAULT_REPORT` (`:29`) is still the checkout root's `coverage.json`, read with no freshness check. |
| T8 | **Open** | The `.pth` name is still fixed (`import_tests/tools/build_run.py:60`), and `[tool.coverage.run]` still leaves the data file in the checkout root. |
| T9 | **Open** | `subprocess.run` at `import_tests/tools/build_run.py:547` and `:582` and `communicate()` at `:982` still have no timeout; `import_tests/test_coordinator.py:351` still asserts the 5 s bound. |
| T10 | **Open** | `import_tests/test_recorder_rules.py` and the database-free tests of `import_tests/test_unit_layers.py` (`:55-133`) are still in the database tier. |
| T11 | **Open** | `pytest.importorskip('MySQLdb')` remains at `tests/opus_import/test_importdb_mysql.py:32`, `test_fresh_import.py:39`, `test_table_swap.py:19` and `test_generations.py:156`. |
| T12 | **Open** | The finding's command now prints 19 lines, of 112 `pytest.raises` uses (`grep -rn 'pytest.raises(' tests/opus_import import_tests tests/import_tests \| wc -l`); one, `tests/opus_import/test_generations.py:696`, has `match=` on its next line, so 18 still assert only the type. |
| T13 | **Open** | The finding's command now gives 104; `tests/opus_import/test_coordinator.py` is unchanged. |
| T14 | **Open** | `tests/opus_import/test_fresh_import.py` and `test_import_pool.py` are unchanged. |
| T15 | **Open** | The guards remain, among them `import_tests/test_generations.py:296-297`, `:596` and `:702` and `import_tests/test_negative_cases.py:108`. |
| T16 | **Open** | `tests/opus_import/test_obs_field_annotations.py` is unchanged. |
| T17 | **Open** | `ls tests/opus_import/test_*.py \| wc -l` gives 35 files, still in one directory. |
| T18 | **Open** | The stated reason is unchanged at `.github/workflows/run-tests.yml:192-193` and `docs/dev_guide_testing.rst:108`; `import_tests/conftest.py` is unchanged. |

**Totals:** 1 Fixed (T5), 2 Partly fixed (T1, T2), 15 Open.

**Unit tier at `a124e126`**, measured with this report's unit-tier command (its Method
table), restricted to the files under `src/opus_import/`: 1207 tests passed, executing
8,490 of 12,128 `opus_import` statements (70.00%), 66.27% with statements and branches,
against 69.06% and 65.08% at `2794cd36`. The import tier was not re-run, so the import and
union columns of the coverage headline are not re-measured.

## Method

All commands were run from the repository root with `PYTHONPATH` unset and
`OPUS_CONFIG=$PWD/tests/fixtures/opus_ci.toml`.

| What | Command |
| --- | --- |
| Unit tier, coverage | `pytest -q tests/opus_import --cov=opus_import --cov-branch --cov-report=json:<scratch>/unit_cov_clean.json --cov-fail-under=0 --durations=40` with `COVERAGE_FILE` pointed outside the checkout (see note below) |
| Unit tier, order probes | the same suite plus `tests/import_tests` in reverse collection order (a three-line `pytest_collection_modifyitems` plugin loaded with `-p`); `-n 4 --dist load`; and each test file run alone |
| Collection counts | `pytest --collect-only -q tests/opus_import tests/import_tests` and `... import_tests` |
| Import tier at HEAD | run by the orchestrator under branch coverage (log: pass/fail and the per-file report) |
| Import tier, clean coverage | the CI log of the `Import Tests` job of run `44538438133` (commit `0eb24745`, Python 3.14), fetched with `gh run view 44538438133 --job 135610012467 --log`; its `--cov-report=term-missing` table parsed per file |
| Unit/import/union split | per-file line sets: unit = the clean unit JSON; import = HEAD statements minus the CI report's *Missing* lines; computed for the 113 `opus_import` modules whose statement count matches between the two (excluded: `cli.py`, `coordinator.py`, `import_all.py`, changed since `0eb24745`, and `config_bundle_info.py`, whose statement count differs between Python 3.13 and 3.14) |
| Function-level split | the same line sets mapped to enclosing functions with `ast` |
| Fake-vs-backend signatures | `inspect.signature` of every public `RegistryDB` method against `ImportDBMySQL` |
| Assertion and pattern counts | `grep` commands named at each finding |

**Measurement note (affects how the coverage figures were obtained).** The orchestrator's
HEAD import-tier coverage report could not be used for the unit/import split. Both
`[tool.coverage.run]` `parallel = true` sessions -- that import run and this critique's first
unit run, which overlapped in time -- used the same data file in the checkout root, and
pytest-cov combines every `.coverage.*` file it finds. The result: the first unit report read
73.59% (it absorbed import-subprocess data), the clean rerun reads 65.08%, and the import
report contains lines only the unit tier reaches (for example
`src/opus_import/import_all.py:686`, the `--dry-run` branch, which no import test invokes),
so it showed zero unit-only lines. The clean unit figures come from a rerun with an
isolated data file. The import figures come from CI. The orchestrator's report is used only
as a cross-check of the union: on the same 113 modules, that report united with the clean
unit report gives 89.77% line coverage, against 89.82% from the CI-derived computation. T17
is the finding this incident is evidence for. A later clean rerun of the import tier at
HEAD, with its data file outside the checkout, reached 10,271 of 12,038 `opus_import`
statements (85.32%; 81.80% with branches) and a gated total of 79.35% against
`fail_under = 74` (207 passed, 3 skipped, 535.74 s), in line with the CI figures used here.

## Executive summary

The section "Status at a124e126" above records which of these findings have since been fixed.

**Strengths.** This is a carefully engineered pair of suites. The unit tier (1,135 tests in
`tests/opus_import`, plus 29 in `tests/import_tests`) runs in 10.4 s under coverage,
passes in reverse order, under `-n 4 --dist load`, and file by file (0 failures in each
probe). The import tier runs the real pipeline end to end, compares every table it writes
against a golden byte for byte (`import_tests/test_goldens.py`), and guards its own
exemptions: excused tables need reasons and rows, dropped columns need derivations checked
against the database, and whitelist entries for unexecuted obs functions fail when they stop
being true. Fault injection (`OPUS_IMPORT_FAULT`) turns interrupts, kills and lock losses
into deterministic tests. Test names describe behaviour consistently, every test has a
docstring, `--strict-markers`, `--strict-config` and `filterwarnings = ["error"]` are on, and
mypy checks the tests strictly.

**Main gaps.**

1. **Coverage is measured for one tier only, and the gate is loose and documented with
   stale figures (T1).** Measured on `opus_import`, line coverage is: unit 67.40%, import
   85.32%, union 89.82%. The unit tier reaches 498 lines the import tier never does, but no
   CI job measures it or combines it with the other run. `fail_under = 74` sits 5.2 points
   under the 79.20% the gating run last measured.
2. **Two data-correctness paths have no test in either tier (T2, T3).** The per-column
   validation in `do_import_obs.import_observation_table` (VARCHAR truncation, REAL/INT
   parse failures, sentinel capture, `val_min`/`val_max` with NULL substitution, a raising
   field function) is untested. So is the command line's bundle selection
   `import_util.yield_import_bundle_ids`: shorthand expansion, the bad-descriptor fatal
   exit, the documented New Horizons ordering and `--exclude-bundles` filtering.
3. **The unit tier leans on 63 hand-written database fakes that nothing checks against the
   backend interface (T4, T5).** `make_context(**kwargs: Any)` erases the type of `db`, the
   shared `RegistryDB` already disagrees with `ImportDBMySQL` on four signatures, and
   several SQL-issuing paths (`requeue_bundles`, `set_next_id`, the index space budget) have
   only ever run against a fake.
4. **The import tier has order-coupled shared state and stale inputs (T6, T7).** A
   session-scoped re-import mutates the main run's schema mid-session, and later modules
   read it. The obs-execution gate reads whatever `coverage.json` sits in the checkout root,
   however old.

**Coverage:** the 90% target of `python_testing.mdc` §9 is met only by the union of the two
tiers (89.82% line coverage on the comparable modules), which no command measures. Neither
tier alone meets it.

**Exception messages:** of the 104 `pytest.raises` uses, 70 pass `match=` and 16 capture
the exception with `as` for further assertions. The other 18 assert only the type (T12).

**Findings by severity:** 3 high (T1-T3), 5 medium (T4-T7, T9), 10 low (T8, T10-T18).

## Measured coverage headline

| Measure | Unit tier | Import tier | Union |
| --- | --- | --- | --- |
| `opus_import` lines, the 113 comparable modules | 67.40% (7,445 / 11,046) | 85.32% (9,424 / 11,046) | 89.82% (9,922 / 11,046) |
| `opus_import` lines, all modules | 69.06% (8,313 / 12,038), HEAD | 85.18% (10,251 / 12,034), `0eb24745` | -- |
| `opus_import` statements + branches | 65.08%, HEAD | -- | -- |
| Gated figure (CI `--cov`, the packages it reports) | not measured in CI | 79.20% vs `fail_under = 74` | -- |

On the comparable modules, 498 lines are reached only by the unit tier, 2,477 only by the
import tier, and 1,124 by neither.

Run times: the unit tier takes 10.43 s with coverage (slowest test 0.92 s). The import tier
took 501 s at HEAD (207 passed, 3 skipped: the three report-reading tests of
`import_tests/test_obs_execution.py`). In CI at `0eb24745` it took 647 s for 205 tests, plus
1.25 s for the 5 obs-execution tests in a second step. Its longest phase is the session
`main_run` fixture, charged as 70.75 s of setup to the first test in CI.

## Findings

### T1: Only the database tier is measured, nothing combines the tiers, and the floor is loose and documented with stale figures

- **Severity:** high
- **Location:** `.github/workflows/run-tests.yml:132-205`; `pyproject.toml`
  `[tool.coverage.report]` comment and `fail_under = 74`; `docs/dev_guide_testing.rst`
  ("Coverage is deliberately **not** measured by this suite"); `scripts/run-all-checks.sh:452-461`.
  Pre-existing structure, widened by the new tests.
- **Evidence:**
  - The `test` job runs `pytest -n auto --dist loadscope` with no `--cov`. Only
    `import-tests` measures coverage, and only for `pytest import_tests`.
    `python_testing.mdc` §9 requires coverage "measured over the ENTIRE suite, not a
    subset".
  - The unit tier reaches 498 `opus_import` lines that the import tier does not (113
    comparable modules, method above), and no gate ever sees them. The largest shares are
    `importdb/mysql.py` (98 lines), `steps/do_import.py` (69), `importdb/super.py` (54) and
    `steps/do_generation.py` (33). Whole functions are entered only by the unit tier,
    among them `do_import.requeue_bundles`, `do_generation.generation_command_problem`
    and `super._simulated_count` (22 functions in all; see T5).
  - The floor comment says the gating run "measures 74.845%: 8,691 of 11,612 statements and
    branches". It also says `opus_import.import_all` is a module "this run does not
    execute". The last gating run in CI reports `Total coverage: 79.20%` over 12,854
    statements and 3,892 branches, with `import_all.py` at 64%, because
    `import_tests/test_coordinator.py` now drives `opus_import.import_all`. That is two
    stale counted claims, against `CLAUDE.md`'s rule that such a claim is measured or not
    made.
  - With the floor at 74, a regression of up to 5.2 points in what the import tier reaches
    passes the gate.
- **Recommendation:** measure both tiers and gate the union. Run the unit tier in the
  `import-tests` job (or a new one) with `--cov --cov-append`, or give each run its own
  `COVERAGE_FILE` and `coverage combine` the two data files, then gate on the combined
  figure. Re-measure and raise `fail_under` to the combined figure rounded down. Replace
  the counted claims in the comment with the command that regenerates them.

### T2: The per-column validation of every observation value is untested in both tiers

- **Severity:** high
- **Location:** `src/opus_import/steps/do_import_obs.py:200-313` and `:455-476`, against
  `tests/opus_import/test_do_import_obs.py` (new, one test) and the whole import tier.
  Code pre-existing; gap present on `main` and still open.
- **Evidence:**
  - The function-level split puts 35 lines of `import_observation_table` and 8 lines of
    `import_run_field_function` in neither tier.
  - Statement starts never executed by either tier include:
    - the invalid FLAG value error (`:210`, `:216`);
    - a non-string bound for a VARCHAR column (`:220`, `:226`);
    - truncation of an over-long VARCHAR (`:229`, `:235`);
    - a REAL that does not parse (`:245-246`, `:252`) and an INT that does not parse
      (`:256-257`, `:263`);
    - the "sentinel missed by the PDS label" catch (`:269-270`);
    - both `val_min` and both `val_max` branches, with and without
      `val_set_invalid_to_null` (`:281-313`);
    - a field function that is missing or raises (`:462-476`).
  - These are the paths that decide whether a bad archive value becomes NULL, is truncated,
    or is stored. The goldens cannot reach them, because the fixture's values are clean.
  - `tests/opus_import/test_do_import_obs.py:55` covers only the DEL-character rule, though
    its `_row` helper (`:37`) already builds a row from a schema and field-function return
    values. That is exactly the harness the rest needs.
- **Recommendation:** add parametrized unit tests on that harness, one case per branch
  (FLAG, VARCHAR type, VARCHAR length, REAL parse, INT parse, sentinel, min/max with and
  without NULL substitution, missing method, raising method). Each should assert the
  stored value and the logged error text and level, through `RecordingLogger.messages_at`.
  This is pure logic and needs no database.

### T3: Bundle selection from the command line is untested in both tiers

- **Severity:** high
- **Location:** `src/opus_import/import_util.py:157-346` (`yield_import_bundle_ids`).
  Pre-existing gap.
- **Evidence:**
  - 91 of the function's statements are reached by neither tier. The unit tier never enters
    it: the shared `run_import_loop` helper replaces it with a lambda
    (`tests/opus_import/conftest.py:433`), and every other unit test that needs bundles
    does the same. The import tier passes bundle ids directly.
  - Unexecuted in both: the shorthand table (`ALL`, `CASSINI`, `HST`, `NH`, ...,
    `:189-280`); the PDS3-then-PDS4 validation with its "Bad bundle descriptor", "not a
    bundle or bundleset" and "not found" fatal messages and the `sys.exit(-1)`
    (`:298-319`); the New Horizons reversal that the docstring documents as what makes the
    raw bundle hold the primary filespec (`:334`); and the skip of names containing `.`
    (`:345`).
  - A typo in the shorthand table, or a broken exit path, would ship with every test green.
- **Recommendation:** unit-test it with `pdsfile`'s `from_path` monkeypatched to a small fake
  holding a few bundlesets. Assert each shorthand's expansion, the exclude list, the NH
  order, the skip of dotted names, and that bad descriptors are all logged at `fatal`
  before `SystemExit`, with message text asserted. Alternatively, drive it once from the
  import tier against the mini-holdings tree.

### T4: The database fakes are not checked against the backend interface, and already disagree with it

- **Severity:** medium
- **Location:** `tests/opus_import/conftest.py:111` (`make_context(**kwargs: Any)`) and
  `:172-363` (`RegistryDB`); duplicated `_RecordingDB(ImportDBMySQL)` in
  `tests/opus_import/test_importdb_mysql.py:66`, `test_fresh_import.py:58`,
  `test_generations.py:77` and `test_table_swap.py:27`. Mostly new: the shared
  `RegistryDB` and three of the four copies arrived with the database-performance work.
- **Evidence:**
  - `grep -rnE 'class .*(DB|Connection|Cursor|Server|Database)\b.*:' tests/opus_import`
    finds 63 fake classes. Most are duck-typed and are handed to `ImportContext.db`, which
    is typed `ImportDBSuper | None` (`src/opus_import/context.py:275`), through
    `make_context(**kwargs: Any)`. That erases the type, so mypy's strict mode never
    compares a fake with the interface it stands in for.
  - `inspect.signature` shows `RegistryDB` already diverging from `ImportDBMySQL`:
    - `read_rows(columns=...)` against the real `column_names=`;
    - `quote_identifier(name)` against the real `s`;
    - `delete_rows` lacks the real `all_rows` parameter;
    - `named_lock_holder` is a static method where the real one is an instance method.
  - A caller using the real keyword spelling fails only against the fake, and vice versa.
  - `RegistryDB.conditional_update` (`conftest.py:254-275`) and `lock_first_row`
    (`:305-324`) re-derive their semantics by splitting the production SQL text
    (`where.split(' IN (', 1)`, `'NOT IN' in where`). A change to the generated clause can
    change what the fake does without any test saying the fake is now wrong.
  - The four `_RecordingDB` copies all bypass `ImportDBMySQL.__init__` and hand-set private
    state. They already set different subsets: only `test_fresh_import.py:72-73` sets
    `_ddl_buffer_bounds` and `_ddl_buffer_size`, and only `test_fresh_import.py`,
    `test_generations.py` and `test_table_swap.py` set `_table_names` and
    `_table_info_cache`. `python_testing.mdc` §8 asks for "a minimal fake defined once in
    `conftest.py` rather than re-mocking in each test".
- **Recommendation:**
  - Type `make_context`'s `db` parameter as `ImportDBSuper | None`, so each duck-typed fake
    must either subclass the backend or be cast at one visible place.
  - Add a unit test that compares every public method signature of `RegistryDB` and the
    other shared fakes with `ImportDBSuper`/`ImportDBMySQL`, and fix the four
    disagreements.
  - Move one `_RecordingDB` into `tests/opus_import/conftest.py` with a constructor that
    sets every attribute `ImportDBMySQL.__init__` sets, except the connection.

### T5: Several SQL-issuing paths have only ever run against a fake

- **Severity:** medium
- **Location:** `src/opus_import/steps/do_import.py:843` (`requeue_bundles`),
  `src/opus_import/importdb/mysql.py` (`set_next_id`, `_free_bytes`, `index_space_budget`,
  `_execute_waiting_for_locks`, `_load_file`, `carry_over_sessions`, `upsert_row`),
  `src/opus_import/importdb/super.py` (`_simulated_count`, `retrying`'s exhaustion).
  Mostly new code with new unit tests.
- **Evidence:**
  - Outside `obs/` and `util/`, the function-level split over the comparable modules lists
    22 functions that the unit tier enters and the import tier never does. Among them: `do_import.requeue_bundles` (21
    statements, the `--requeue` operator command); `ImportDBMySQL.set_next_id` (the
    `AUTO_INCREMENT` reset `do_django` issues only when `user_searches` holds rows, which
    the fixture's never does); `do_generation.generation_command_problem` (15 statements,
    called by the deploy chain's `promote_generation.sh`); and `super._simulated_count`.
  - Within `importdb/mysql.py`, 98 lines run only under a recording fake. That SQL is
    asserted as text, but MySQL has never parsed it in any test.
  - Conversely, `ImportDBMySQL.upsert_row` has two unit tests
    (`tests/opus_import/test_importdb_mysql.py:362-385`). The first test's docstring says the
    pipeline "does not call `upsert_row` at all", and
    `grep -rnw upsert_row src/` finds no caller. The tests keep an unused method alive
    rather than test behaviour (dead code itself is the code reviewers' concern).
- **Recommendation:** for each SQL path that only a fake has run, add one import-tier test
  that executes it against the real server, in the style of
  `import_tests/test_unit_layers.py:178-212`. Do at least `--requeue` on a failed bundle,
  `set_next_id` on a non-empty `user_searches`, and the index-space budget query. Drop the
  `upsert_row` tests if the method goes.

### T6: A session-scoped re-import mutates the main run's schema, and later modules read the mutated state

- **Severity:** medium
- **Location:** `import_tests/test_goldens.py:266-298` (the `reimport` fixture); readers in
  `import_tests/test_mult.py:131-160` and `import_tests/test_negative_cases.py:105-180`.
  The re-import was on `main`; `test_mult.py` is new and adds readers.
- **Evidence:**
  - `reimport` re-imports one bundle into `main_run.schema`, which renumbers that bundle's
    rows. Its docstring guards ordering only within its own module ("deliberately the last
    thing this module does", `:278`).
  - pytest runs modules in collection order, so `test_mult.py` and `test_negative_cases.py`
    run after `test_goldens.py` and query `main_run.schema` directly: `_unreferenced`,
    `_values` and `_row_count`. They also copy it through
    `build_run.copy_run_schema(main_run, ...)` for four cases.
  - Their assertions happen to be invariant under a re-import. But the state they inspect
    depends on selection: `pytest import_tests/test_mult.py` sees a pristine schema, the
    full suite sees a re-imported one. Any new assertion on ids, or on the re-imported
    bundle, will pass or fail depending on what else ran. That is the hidden order
    dependence `python_testing.mdc` §2 forbids.
- **Recommendation:** make `reimport` work on a copy, as the newer modules do
  (`build_run.copy_run_schema(main_run, db_credentials, created_schemas, 'reimport')`), so
  `main_run.schema` is never mutated after the session fixture returns. Add a session-end
  assertion that `main_run.schema` still matches its goldens.

### T7: The obs-execution gate reads whatever `coverage.json` is in the checkout root, however stale

- **Severity:** medium
- **Location:** `import_tests/tools/obs_execution.py:29` (`DEFAULT_REPORT = REPO_ROOT /
  'coverage.json'`), `import_tests/test_obs_execution.py:38-64`, `scripts/run-all-checks.sh:478`,
  `.gitignore:41`. Pre-existing.
- **Evidence:**
  - The fixture skips when the file is missing locally and fails under `GITHUB_ACTIONS`,
    which is sound. But when the file exists, it is used with no check that it came from
    this tree or this run: `read_report` (`obs_execution.py:61-114`) checks only for
    per-function regions.
  - `coverage.json` is git-ignored, so a leftover file is invisible to `git status`.
    `run-all-checks.sh --import-tests` runs `python -m pytest -q import_tests`, which
    collects `test_obs_execution.py` in the same session, so it reads a report from any
    earlier measured run. That includes a unit-tier `--cov-report=json:coverage.json` run,
    whose obs coverage is far lower (for example `obs/obs_volume_couvis_0xxx.py`: 21.8% of
    lines under the unit tier against 90.0% under the import tier).
  - The three report-reading tests then fail or pass on old data.
- **Recommendation:** have the fixture compare the report's `meta.timestamp` with the start
  of the pytest session and with the mtime of `src/opus_import/obs`, refusing a report
  older than either. Or have the measuring run write the report to a path the session
  names, and have `test_obs_execution.py` take that path from an option or environment
  variable rather than a fixed file.

### T8: Coverage data and the subprocess `.pth` are shared per checkout and per environment, so concurrent measured runs corrupt each other

- **Severity:** low
- **Location:** `pyproject.toml` `[tool.coverage.run]` (`parallel = true`, data file
  defaulting to the checkout root); `import_tests/tools/build_run.py:432-478`
  (`install_subprocess_coverage`, fixed name `opus_import_tests_subprocess_coverage.pth`);
  `import_tests/conftest.py:74-88`. `parallel = true` pre-existing; the `multiprocessing`
  concurrency is new.
- **Evidence:**
  - Observed during this critique (see the measurement note). An import-tier session and a
    unit-tier session overlapped in one checkout. The unit report inflated from 65.08% to
    73.59%, and the import report absorbed the unit run's lines.
  - The suite defends schemas against concurrent runs with pid-suffixed names
    (`import_tests/conftest.py:7-11`) but not its coverage data.
  - Two measured sessions in one virtual environment share the one `.pth` name, and
    whichever ends first unlinks it (`conftest.py:87-88`), silently unmeasuring the
    other's subprocesses.
- **Recommendation:** have the import-tier session set `COVERAGE_FILE` to a session
  temporary directory when it is measured, and pass it to subprocesses through
  `run_environment`. Suffix the `.pth` name with the session pid.

### T9: Pipeline subprocesses run without timeouts, and some assertions are against the wall clock

- **Severity:** medium
- **Location:** `import_tests/tools/build_run.py:547` (`run_pipeline_step`: `subprocess.run`
  with no `timeout`), `:582` (`run_migrate`), `:982` (`communicate_all`: `communicate()`
  with no timeout), used by `run_concurrently` (`:985-1046`);
  `import_tests/test_coordinator.py:351`. Pre-existing for `run_pipeline_step`; the
  concurrent helpers are new.
- **Evidence:**
  - A pipeline step that deadlocks hangs the session until the job's
    `timeout-minutes: 60` kills it, with no test named and no captured output: for
    example a lock wait, or a hold file a failed test never removed, which waits
    `HOLD_LIMIT_SECONDS = 300` per importer (`src/opus_import/import_processes.py:65`).
  - No timeout plugin is installed (`pip list` shows pytest, pytest-cov, pytest-django and
    pytest-xdist only).
  - `test_concurrent_import.py:348` and the coordinator helpers (`_TIMEOUT = 240.0`,
    `test_coordinator.py:43`) show the suite already knows how to bound waits.
  - `test_coordinator.py:351` asserts
    `time.monotonic() - killed < _LOCK_FREED_WITHIN` (5 s) on a shared CI runner.
- **Recommendation:** give `run_pipeline_step`, `run_migrate` and `communicate_all` a
  timeout derived from one module constant, and on expiry kill the process and fail with
  its captured stderr. Consider `pytest-timeout` for the import tier only. Express the 5 s
  check as the wait's own timeout (already done on the line before) and drop the second
  wall-clock assertion.

### T10: Pure, database-free tests live in the database tier

- **Severity:** low
- **Location:** `import_tests/test_recorder_rules.py` (all 22 tests; its docstring calls the
  rules "pure functions of their inputs"); `import_tests/test_unit_layers.py:45-140`
  (five functions, one parametrized over three cases, which "need no database" per its
  docstring, `:3`); the static checks in `import_tests/test_goldens.py:153-209` and
  `import_tests/test_obs_execution.py:86-106`. Pre-existing.
- **Evidence:** these run only when someone runs `pytest import_tests`. That means locally
  only with a reachable MySQL server, and in CI only in the `import-tests` job on Python
  3.14, never in the 3.12-3.15 unit matrix. `tests/import_tests/` already exists for unit
  tests of the suite's tools. `python_testing.mdc` §4 asks that the default suite hold
  everything hermetic.
- **Recommendation:** move `test_recorder_rules.py` and the database-free tests of
  `test_unit_layers.py` into `tests/import_tests/`. Move the static golden and whitelist
  consistency checks there too, since they read only checked-in files.

### T11: A module-level `importorskip` on a hard dependency can silently skip 234 unit tests

- **Severity:** low
- **Location:** `tests/opus_import/test_importdb_mysql.py:32`, `test_fresh_import.py:39`,
  `test_table_swap.py:19`, and `test_generations.py:156` (per test). The first was on
  `main`.
- **Evidence:** `mysqlclient` is a runtime dependency (`pyproject.toml:15`), so the module
  must import. The three module-level skips cover 234 collected tests
  (`pytest --collect-only` on those files). If the driver fails to build or import, the
  CI job reports a pass with skips. The `test` job's `pytest -n auto --dist loadscope`
  neither prints skip reasons nor fails on skips.
- **Recommendation:** replace the `importorskip` calls with a plain `import MySQLdb`, so a
  broken driver fails collection.

### T12: Eighteen `pytest.raises` assert only the exception type

- **Severity:** low
- **Location:** for example `tests/opus_import/test_importdb_mysql.py:301`
  (`test_quote_identifier_rejects_anything_else`, seven parametrized inputs including
  `'obs;DROP TABLE x'`, `None` and `17`) and
  `tests/opus_import/test_do_update_mult_info.py:280` (bare `TypeError`, four cases). Others
  are at `test_importdb_mysql.py:445, 523, 1130, 1187, 1201, 1303, 1350`,
  `test_do_import_mult.py:264, 509`, `test_fresh_import.py:315`,
  `test_obs_field_annotations.py:1184`, `test_generations.py:829, 1048` and
  `test_cli.py:465, 491, 516`. Mixed old and new.
- **Evidence:** `grep -rn 'pytest.raises(' tests/opus_import import_tests tests/import_tests
  | grep -v 'match=' | grep -v ' as '` gives 19 lines, one of which
  (`test_generations.py:696`) has `match=` on the next line.
  `python_testing.mdc` §7 requires asserting message content.
  - Several are compensated by a log assertion, for example `test_do_import_mult.py:267`.
  - The two named above are not. A bare `TypeError` also passes when a test fake raises
    one by accident. The identifier-quoting test cannot tell "rejected as unsafe" from
    "crashed on `None`".
- **Recommendation:** add `match=` to each: for `quote_identifier`, the rejection message;
  for `update_mult_info`, the shape message `read_mult_option` raises. Keep the log
  assertions where present.

### T13: Tests reach into private members of the code under test

- **Severity:** low
- **Location:** `tests/opus_import/test_coordinator.py` (`coordinator._pass` 12 times,
  `_starts_left` 11, `_own` 10, `_failed_starts` 4, `_failing_since` 2, `_settle` 2);
  `tests/opus_import/conftest.py:108` (`cli._create_argument_parser`); test-side writes to
  `db._table_names` and `db._table_info_cache` (T4). Mostly new.
- **Evidence:** this grep finds 101 references to `_`-prefixed members of `opus_import`
  objects in the unit tier:
  `grep -rhoE '\b(cli|coordinator|do_[a-z_]+|import_util|import_all|bundle_registry|import_processes|mysql|super|table_swap|table_keys|schema_version|db|ctx)\._[a-z][a-z_0-9]*' tests/opus_import | wc -l`.
  `test_coordinator.py` drives the coordinator one `_pass` at a time and seeds its private
  counters (for example `coordinator._failing_since = ...` at `:544`). A refactor of the
  loop breaks the tests even when behaviour is unchanged (skill §20).
- **Recommendation:** promote what tests need to a documented seam, for example a public
  `Coordinator.step()` and a constructor parameter for the clock. Alternatively, accept the
  coupling explicitly for the coordinator, whose behaviour the import tier also covers end
  to end, and say so in the module docstring.

### T14: Unit tests whose verdict depends on thread and process scheduling

- **Severity:** low
- **Location:** `tests/opus_import/test_fresh_import.py:470` and `:504`;
  `tests/opus_import/test_import_pool.py:237` and `:255`; `test_import_pool.py:362-374`
  (`_forking`). New.
- **Evidence:**
  - `assert 1 < db.most_running <= 3` requires two fake DDL statements, each sleeping
    10 ms, to overlap.
  - `assert len(set(emitted)) > 1` requires a forked pool to spread 40 tasks, each sleeping
    20 ms, across more than one worker.
  - Both are likely but not guaranteed on a loaded runner under `-n auto`.
  - `_forking` silences CPython's `DeprecationWarning` about forking a multi-threaded
    process, and the tests then fork from inside an xdist worker. That is the deadlock
    hazard the warning exists for, so the tests trade a rare hang for the warning.
- **Recommendation:** replace the sleeps with a `threading.Barrier` or `Event` that every
  participant must reach, which makes overlap certain. Run the forking tests under the
  `forkserver` context if `do_import_pool` accepts one, or isolate them in a subprocess.

### T15: Guards and ranges where the fixture would allow exact values; chained comparisons

- **Severity:** low
- **Location:** `import_tests/test_negative_cases.py:108`; `import_tests/test_generations.py:296-297, 526, 632`;
  `import_tests/test_bulk_load.py:236, 267`; `import_tests/test_parallel_import.py:249`;
  `tests/opus_import/test_obs_field_annotations.py:239-240`;
  `tests/opus_import/test_exception_control_flow.py:87`; chained comparisons at
  `tests/opus_import/test_fresh_import.py:511, 1044`, `test_import_pool.py:198` and
  `test_do_import_mult.py:342`. Mixed.
- **Evidence:**
  - The import is deterministic from an empty schema (the premise of `test_goldens.py:1-5`),
    yet these assert `> 0`, `>= 1` or `> 1000`.
  - `test_metadata_less_volume_still_imports` (`> 0`) is in any case subsumed by the
    goldens.
  - The chained comparisons check two conditions in one `assert`, which
    `python_testing.mdc` §7 forbids. ruff's PT018 catches `and`, not chains.
- **Recommendation:** assert the exact counts the goldens imply (read them from the golden
  where hard-coding would drift), and split the chained asserts.

### T16: The same instrument is driven three times to assert three parts of one result

- **Severity:** low
- **Location:** `tests/opus_import/test_obs_field_annotations.py:1007-1040`. Pre-existing.
- **Evidence:** `test_a_field_method_returns_what_it_declares`,
  `test_no_field_method_raises_on_a_complete_observation` and
  `test_the_fixture_drives_as_much_of_the_class_as_it_used_to` each call
  `_drive(instrument_id)` for every instrument and keep one element of its tuple.
  `python_testing.mdc` §7: "If two tests drive the same code path but assert on different
  parts of the result, combine them."
- **Recommendation:** cache `_drive` per instrument (a module-scoped fixture parametrized by
  instrument) or fold the three into one parametrized test with three asserts.

### T17: The unit tree does not mirror the source tree

- **Severity:** low
- **Location:** `tests/opus_import/` (35 flat `test_*.py` files) against
  `src/opus_import/{steps,obs,importdb,util,config_targets}/`. Pre-existing.
- **Evidence:** `test_do_*.py` files for `steps/` modules, `test_importdb_mysql.py` for
  `importdb/mysql.py` and `test_obs_*.py` for `obs/` all sit in one directory.
  `python_testing.mdc` §3: "the test tree parallels the package tree directory for
  directory".
- **Recommendation:** when files are next touched, move them into `steps/`, `importdb/` and
  `obs/` subdirectories. The importlib import mode already permits duplicate basenames.

### T18: The import tier's stated reason for running serially is inaccurate, and it runs on one Python

- **Severity:** low
- **Location:** `.github/workflows/run-tests.yml:192-193`, `docs/dev_guide_testing.rst:108`,
  `import_tests/conftest.py:107`, and the `import-tests` job's `python-version: 3.14`.
- **Evidence:**
  - Both texts say a session fixture under `-n` "would run the import once per worker into
    the same schema". But the schema name is
    `fixture_layout.schema_name(os.getpid())`, and every xdist worker has its own pid, so
    each worker would import into its own schema. The real costs of `-n` are N full
    imports, and the shared coverage data and `.pth` (T8). Nothing stops a developer from
    passing `-n`.
  - The tier runs only under 3.14, while the package supports 3.12-3.15 and the unit tier
    runs on all four.
- **Recommendation:** correct the stated reason. Make `import_tests/conftest.py` fail fast
  when it detects an xdist worker (`PYTEST_XDIST_WORKER`). Consider a weekly 3.12 run of
  the import tier, the floor version and the one the self-hosted integration job uses.

## 1. Return values and assertions

Assertions are mostly exact. There are 2,087 `assert` statements in the test modules of
the three trees (`grep -rnE '^\s*assert '`), and only 7 `isinstance` checks. Golden and recorded-value
comparisons dominate where output is large. Weak spots: `is not None` appears 71 times,
almost all as narrowing before a precise check (acceptable); range guards on deterministic
data (T15); and `assert succeeded`-style truthiness on boolean returns in
`test_bundle_registry.py` and `test_queue_importer.py`, which `is True` would make stricter.

## 2. Success and failure conditions

The happy paths are covered end to end by the goldens. Failure paths are strong for
generations, registry states, fault injection, recovery and lock loss, at both tiers. The
missing ones are input-validation failures: column values (T2), bundle descriptors (T3),
and SQL error paths that only a fake has raised (T5). The 1,124 lines reached by neither
tier are concentrated in `importdb/mysql.py` (122), `import_util.py` (120), the
`ObsBundleCassiniISSFRingMosaicsRSFrench2025` class (114, whitelisted because the holdings
lack that bundle), `do_import_obs.py` (43) and `do_import_index.py` (42).

## 3. Consistency

Naming is uniformly sentence-style (`test_<behaviour>`), and docstrings are universal. The
structure is consistent within a module. Fixture reuse is the weak spot: duplicated fakes
(T4) and four near-identical `_RecordingDB` classes. Assertion style mixes chained
comparisons (T15) into a suite that otherwise keeps one condition per assert.

## 4. Completeness

See the coverage headline and T1-T3, T5. Documented behaviours with no test are the New
Horizons import order (`import_util.py:166-169`, T3) and the NULL substitution of
`val_set_invalid_to_null` (T2).

## 5. Redundancy

T16 (three drives of one instrument). `test_negative_cases.py:104-108` duplicates what the
goldens assert more strictly. The same-named modules in the two tiers (`test_coordinator`,
`test_generations`, `test_fresh_import`, `test_schema_version`, `test_table_swap`) are
layered rather than redundant: the unit tier pins decisions, the import tier proves them
against MySQL.

## 6. Parallel execution

The unit tier is clean: it passes in reverse order, under `-n 4 --dist load`, and file by
file. Global state is restored (`signal_restored`, `warnings.catch_warnings`, `monkeypatch`;
the root `conftest.py` clears the configuration cache around every test). The import tier is
serial by design, with session state mutated mid-run (T6), shared coverage artifacts (T8)
and an inaccurate stated reason for running serially (T18).

## 7. Mocking and dependency isolation

`monkeypatch` is the consistent default. Patches target the lookup site (for example
`monkeypatch.setattr('opus_import.importdb.super.time.sleep', ...)`), and sleeps and clocks
are faked where retry timing matters. The isolation risk is fidelity, not leakage: 63
hand-written database fakes, unchecked against the interface (T4), some interpreting SQL
text, and SQL paths that only fakes have run (T5). Real `time.sleep` is used for overlap in
two places (T14).

## 8. Security and input validation

Identifier quoting has a parametrized injection test (`test_importdb_mysql.py:287-302`) that
asserts only the type (T12). Value validation of archive input is untested (T2). The CI
MySQL password in `run-tests.yml` is a disposable service-container credential, and
`tests/fixtures/opus_ci.toml` holds dummies.

## 9. Parameterization

Used widely: 120 `parametrize` uses (`grep -c parametrize`), with readable `ids`. The
gaps are boundary values in T2, where `val_min` and `val_max` invite exact-boundary cases,
and T3's shorthand table, an obvious parametrize candidate.

## 10. Async

Not applicable: the code uses processes and threads, not asyncio. For hang-bounding see T9.

## 11. Output and contract

Golden files pin the whole output contract of the import tier. In the unit tier,
`obs_field_values.json` pins every field method's value, and `_EXPECTED_RETURNS` pins how
many methods return. Exception contracts are asserted with `match=` or a captured value in 86 of 104
cases (T12).

## 12. Error handling

Errors are mostly told apart by type and message (`match=`), and by the log level through
`RecordingLogger.messages_at`. See T12 for the exceptions.

## 13. State and workflow

This is the strongest area. Generation states (begin, switch, revert, purge, abandon), the
registry's bundle states and schema-version states are tested for valid and refused
transitions at the unit tier, with interrupted-then-resumed variants at the import tier
(`test_generations.py`, `test_append.py`, `test_coordinator.py`). Idempotency is asserted
(`import_tests/test_schema_version.py:312`, `test_table_swap.py:112`).

## 14. Test data and fixtures

The data is realistic: real archive metadata in `tests/fixtures/mini_holdings`. Cleanup is
thorough: every schema is registered with `created_schemas` and dropped at session end; I
checked every `schema_name(` and `copy_run_schema(` call site. Autouse fixtures are two
(`_clear_config_cache`, `_opus_config`) and both are justified. Scopes are appropriate
(session for the expensive runs, module for per-case runs). Gaps: duplicated fakes (T4),
and the shared `RegistryDB` living in `conftest.py` with SQL-parsing logic that would
deserve its own tests.

## 15. Flakiness indicators

T9 (no subprocess timeouts; a 5 s wall-clock assertion), T14 (sleep-based overlap; forking
from a threaded worker), T6 (selection-dependent state). There is no unseeded randomness
(`grep -rnE 'random|uuid' tests/opus_import` finds none).

## 16. Regression and documentation

Tests describe behaviour rather than history, as `python_testing.mdc` §10 asks.
`filterwarnings = ["error"]` with no entries is in force. No deprecated public API needs a
`pytest.warns`. The one local warning suppression is the fork warning (T14).

## 17. Other

Speed is good: unit 10.4 s, import 501-647 s. Assertion messages are present where
diagnosis needs them (golden diffs are bounded, `test_goldens.py:71-101`). Test logic stays
simple except in the fakes (T4).

## 18. Code coverage

See the headline and T1. Union line coverage per module (method above) is below 80% for:

- `obs/obs_cassini_common_pds4.py`: 41.9%;
- `obs/obs_volume_hstix_xxxx.py`, `obs/obs_volume_hstjx_xxxx.py` and
  `obs/obs_volume_hstnx_xxxx.py`: 52.6%, 54.2% and 59.7%, all from the import tier;
- `obs/obs_preview.py`: 53.2%; `obs/obs_surface_geometry.py`: 52.9%;
  `obs/obs_profile_pds4.py`: 62.5%;
- `import_util.py`: 67.8% (T3);
- `steps/do_import_obs.py`: 76.2% (T2);
- the two command-line utilities `util/dump_pds_definitions.py` and
  `util/retrieve_ra_dec.py`: 18.8% and 28.6%, import-safety checks only.

The whitelisted rsfrench2025 class is excluded here, since no holdings exist for it.

## 19. Pytest markers

`--strict-markers` and `--strict-config` are on, and the three registered markers belong to
`integration_tests/`. Nothing in scope is marked: the tiers are selected by path, a
documented and justified waiver in the `[tool.pytest.ini_options]` comment. There is no
`xfail`. The only `skipif` (`import_tests/test_parallel_import.py:216`, Linux-only) is
current. The `importorskip` calls are stale (T11).

## 20. Test boundary

T13 (101 private-member references). One private import from a module
(`import_tests/test_unit_layers.py:22`, `_create_argument_parser`). No over-mocking of the
unit under test was found: fakes replace the database, never the step being tested.

## 21. Logging assertions

No `logging.mdc` exists, so convention checks are skipped. Log assertions themselves go
through `RecordingLogger` rather than `caplog`, because the pipeline logs through
`pdslogger`. Levels are routinely asserted (`messages_at('fatal')`, `('warning', ...) in
logged`). The import tier asserts clean `ERRORS.log` and `WARNINGS.log` files for the main
run (`test_run_logs.py`).

## 22. Pytest configuration

`testpaths = ["tests"]`, `--import-mode=importlib`, strict options and warnings-as-errors are
all present, and `pytest.ini` and `setup.cfg` are absent. Plugins: `pytest-xdist` is used.
`pytest-randomly` and `pytest-timeout` are absent: the latter would bound T9, the former
would turn this report's one-off order probes into a standing check.

## 23. Snapshot and golden-file testing

The goldens are committed, regenerated by `import_tests/tools/make_mini_goldens.py`, and
compared byte for byte on every CI run, so staleness fails loudly. Exemptions are
self-policing (excused tables need reasons and rows; dropped columns need non-circular
derivations checked against the database). `golden_io.EXCLUDED_TABLES` is currently empty,
so three of those guards pass vacuously until it holds an entry. The unit-tier snapshot
(`obs_field_values.json`) regenerates only under an explicit `--regenerate-obs-values` flag,
which then skips rather than passes. The two snapshots are reviewed as diffs, with no
evidence of approve-and-forget.

## Prioritized recommendations

1. **(T1)** Measure the unit tier in CI, combine it with the import tier, gate the union,
   re-derive `fail_under` from it, and replace the stale counts in the floor comment with
   the regenerating command.
2. **(T2)** Unit-test every branch of the column validation in
   `import_observation_table`, and the missing or raising field function, on the existing
   `_row` harness.
3. **(T3)** Unit-test `yield_import_bundle_ids` against a faked `pdsfile`: shorthands,
   exclusions, NH order, the dotted-name skip, and the fatal bad-descriptor path.
4. **(T4)** Type `make_context`'s `db`, add an interface-conformance test for the shared
   fakes, fix the four signature disagreements, and consolidate `_RecordingDB` in
   `conftest.py`.
5. **(T6)** Re-import into a copy, so `main_run.schema` is never mutated after the session
   fixture returns.
6. **(T5)** Add one real-server test each for `--requeue`, `set_next_id` on a non-empty
   table, and the index-space budget.
7. **(T7, T8)** Bind the obs-execution report to its producing session, and give measured
   sessions their own coverage data file and `.pth` name.
8. **(T9)** Bound every pipeline subprocess wait, and drop the second wall-clock assertion.
9. **(T10, T11, T12)** Move pure tests out of the database tier, replace the
   `importorskip` calls with imports, and add `match=` to the 18 type-only raises.
10. **(T13-T18)** The remaining low-severity items, as the files are next touched.

## Prompt for an AI agent to fix tests

You are fixing the test suites of `src/opus_import/` in the rms-opus repository, on the tree
this report names. Read this whole report first. Its findings T1-T18 are the work list, and
sections 1-23 are context. Follow `.cursor/rules/python_testing.mdc` and
`.cursor/rules/python.mdc`, and `CLAUDE.md`'s rule that a counted claim is either measured
or replaced by the command that regenerates it.

Constraints:

- Do not change production code under `src/`. Where a finding's fix would need a
  production change (a public seam for T13; removing `upsert_row` for T5), stop and report
  it instead.
- Preserve every currently passing behaviour. Add or strengthen assertions and restructure
  tests; never delete a passing assertion without replacing it with a stricter one.
- When testing an exception with a defined message, use `pytest.raises(..., match=...)` or
  `as exc_info` and assert on `str(exc_info.value)`, never the type alone.
- Every new test function is fully type-annotated, has a docstring describing the
  behaviour, asserts exactly one condition per `assert`, and uses `tmp_path` and
  `monkeypatch` for isolation.
- Coverage: measure on the **entire** suite. Run the unit tier and the import tier each
  with its own `COVERAGE_FILE`, then `coverage combine` the two, and report the per-module
  and total figure. Aim for at least 90% and almost every non-exception line covered.
  Report the measured figure with the command that produced it.

Work in this order:

1. **T2.** In `tests/opus_import/test_do_import_obs.py`, add parametrized tests over the
   existing `_row` helper, one per validation branch of
   `src/opus_import/steps/do_import_obs.py:200-313` and `:455-476`. Each asserts the stored
   value and the logged message's text and level.
2. **T3.** Add `tests/opus_import/test_bundle_selection.py`, exercising
   `import_util.yield_import_bundle_ids` with `pdsfile.pds3file.Pds3File.from_path` and
   `pdsfile.pds4file.Pds4File.from_path` monkeypatched to a fake bundleset tree.
3. **T4.** Change the `db` parameter of `make_context` in `tests/opus_import/conftest.py` to
   `ImportDBSuper | None` and fix the resulting mypy errors with real subclasses or one
   explicit `cast` per fake. Add a test comparing the public signatures of `RegistryDB`
   with `ImportDBMySQL`, and make them agree. Move one `_RecordingDB(ImportDBMySQL)` into
   the conftest and use it from the four modules.
4. **T6.** Make the `reimport` fixture in `import_tests/test_goldens.py` operate on
   `build_run.copy_run_schema(main_run, ...)`, and keep the three re-import assertions
   unchanged in meaning.
5. **T12, T15, T11.** Add `match=` to the 18 type-only raises. Replace guards with exact
   counts where the fixture is deterministic. Split chained comparisons. Replace the
   `pytest.importorskip('MySQLdb')` calls with `import MySQLdb`.
6. **T10.** Move `import_tests/test_recorder_rules.py` and the database-free tests of
   `import_tests/test_unit_layers.py` into `tests/import_tests/`.
7. **T9, T14.** Add timeouts to the subprocess helpers in `import_tests/tools/build_run.py`.
   Replace sleep-based overlap in `test_fresh_import.py` and `test_import_pool.py` with a
   barrier.

Then run `pytest` (unit tier), `pytest import_tests` against a MySQL server, and
`scripts/run-all-checks.sh`, and report the results, the combined coverage figure and any
finding you could not fix without a production change.
