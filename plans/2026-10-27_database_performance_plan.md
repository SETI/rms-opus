# rms-opus Database Performance Plan

**Target executor:** an opus-class AI, **one fresh sub-agent per PR, no shared context**
(execution protocol in §3).
**Strategy:** a sequential, stacked series of PRs on a long-lived `db-perf` branch off
`main`, each one measured before and after on the same machine in the same session
(measurement protocol in §2); `db-perf` merges to `main` once, in Phase 6. The PostgreSQL
port is a separate, optional series that follows the merge (Phase P).
**Source:** `critiques/2026-10-27_database_format_analysis.md` (the analysis of the
schema in the tree, cited as `§C-n`, its recommendations as `item n`) and
`plans/2026-10-28_database_design.md` (the schema this plan produces and the reasons for
each change, cited as `§D-n`). The design document is the statement of the end state;
this plan is the sequence of PRs that reaches it, with the measurements that prove each
step.

**Date:** 2026-10-27. PR numbers are stable once execution begins; an Execution note names
the commit of this file it was written against.

---

## 1. Context and scope

OPUS has two halves that share one SQL schema: `opus_import` builds it from PDS holdings
over hours to days, and `opus_app` searches it. The analysis's finding is that both halves
turn units of work into units of DDL and single-column indexes: a search is a `CREATE TABLE`,
a page is a `CREATE TEMPORARY TABLE`, a target body is a table, an enumerated column is a
table, and nearly every column is an index. The import is single-threaded Python whose
three in-process counters (row ids, mult ids, one import namespace) make it unsafe to run
twice at once, and whose write path fights the storage engine (every row written twice,
into fully indexed tables, with two foreign-key checks per row on every child table).

MySQL is the only brand implemented today. The brand abstraction exists on both sides:
`opus_import.importdb.get_db` dispatches on `[database] brand`, `importdb/postgresql.py`
is a stub whose every method raises `NotImplementedError`, `opus_config` accepts
`'PostgreSQL'`, and `settings.py` maps the brand to a Django engine. Phases 0 to 6 keep
the abstraction honest (§1, Brand dispatch) and change MySQL only. Phase P, if and when it
is run, brings the stub to parity and measures the two brands head to head on the
architecture Phases 0 to 6 produced.

### What this plan delivers

- A benchmark harness and a committed **baseline** of import, database, and web
  measurements, taken before any change (Phase 0).
- The import's Python hot spots and the web application's cheap round trips removed
  (Phase 1).
- The import made **parallel** and its write path made **bulk**, behind a schema version
  guard, with **one write path** chosen by the target schema's state: a schema is built
  directly and indexed once at the end, a finalized one is appended to, and the aux and
  dictionary tables are swapped in atomically (Phase 2).
- DDL removed from the web request path, the child tables keyed on the join key, the
  default sort served by an index, one mult table with a computed display order and no
  unused values, one surface geometry table, variable-width strings with ASCII
  identifiers, and the landing page warmed after every deploy (Phase 3).
- Indexes for the JSON list columns, re-sort without re-search, and indexed autocomplete,
  on MySQL (Phase 4).
- Incremental updates (replace, add, or drop a bundle) seeded from the served schema into
  a new one, built, and promoted whole (PR-22), with sessions and carts carried over at
  every promotion (PR-17).
- Three further options, a default-sort rank column, precomputed empty-search counts, and
  a narrow facet table for mult counts, measured on full-scale data, reported, and
  implemented only after the numbers are discussed (PR-23).
- Server configuration guidance written from the plan's measurements, with the histogram
  statistics measured (PR-24).
- `db-perf` merged to `main` (Phase 6).
- **Optionally, later:** a PostgreSQL backend for both halves at parity under the golden
  suites, a head-to-head measurement, and a recorded decision (Phase P).

### Decisions made

| Topic | Decision |
|---|---|
| Branch | **Sequential PRs on one integration branch, stacked.** PR-00 creates `db-perf` from `main`, **which already carries this plan, the design document, and the analysis** (merged to `main` in their own documentation PR), so that the Execution notes can be amended in later PRs; every PR in Phases 0 to 5 branches from `db-perf` and targets `db-perf`; PR-(N+1) starts from `db-perf` after PR-N has merged into it, so every A/B's merge-base is the previous PR's result. `db-perf` carries the same protection as `main` and both workflows trigger on it from PR-00. **`main` is merged into `db-perf` only between PRs**, by the orchestrator, recorded in the Execution notes; the next PR's `before` run then measures the merged base, so the merge never hides inside an A/B. Phase 6 merges `db-perf` to `main` once and moves the plan and critiques to `plans/archive/` and `critiques/archive/` per `CLAUDE.md`. `main` stays deployable throughout, as it did during the modernization (`plans/archive/2026-07-18_opus_modernization_plan.md`, the `rewrite` branch). Phase P, if run, repeats the arrangement on `db-postgresql`. |
| Measurement | **No performance claim enters a PR description, the dev guide, or this plan unless the benchmark harness produced it**, with the JSON result committed under `benchmarks/results/`. This is the repository's "measured or not made" rule applied to timing. |
| A/B discipline | Before and after are measured **in one session on one machine**, base and head checked out side by side as git worktrees and installed into separate virtual environments. At fixture scale three import runs and five web runs each; at full scale the budget in §2.3. Medians are compared, with the spread. A number from a different machine or a different day is not a comparison. |
| Scales | Two. **Fixture scale** is the checked-in mini-holdings on any machine with a database server, minutes. **Full scale** is the schema `scripts/import/import_for_tests.sh` builds from the Ring-Moon Systems Node's holdings; it is the database the API goldens are pinned to, and "a copy of production" is never used, because the goldens would not pass against it. The full-scale machine is any host that has the holdings and either room for a harness-owned database server (§2.2) or a database account with the grants §2.2 names, which the self-hosted integration runner already is; **no administrator access to it is assumed** (§2.2, §3). Every PR measures at fixture scale. PRs marked **full scale** in §4 must also be measured there before merge. |
| Database server under test | **Preferred: a server the harness owns.** `bench_*` can start a `mysqld` from the generic MySQL tarball (a path under the executor's home, so no system profile confines it) with its own data directory, port, socket, and `my.cnf`, as it starts gunicorn and memcached; the tuning baseline (§2.4) is then applied in full, including the startup-only settings, and db-cold is an exact restart. **Fallback: a shared server** the executor's account has the §2.2 grants on, in which case the harness evicts what it can online, records what it could not, and labels the state. Both scales may use either; the result records which, and `compare.py` refuses to compare results that differ in it. |
| Web server under test | The harness starts its own server for every web run, on both scales: gunicorn with `--worker-class gthread --workers 4 --threads 2 --worker-connections 2`, the same eight request slots as the Node's mod_wsgi arrangement (`docs/user_guide_web_server.rst`), with `--worker-connections 2` so a worker does not queue requests behind its two threads while another worker is idle. gunicorn imports the application at worker start where mod_wsgi does so on each process's first request; the result records `app_loading = "eager"`. The result records `server_model`. A run against an operator-started mod_wsgi is welcome and labeled as such; `compare.py` refuses to compare two results whose `server_model` differs. |
| Deployment layout | The schema supports **one database server and any number of stateless web workers** with no later change (`§D-5`): every piece of per-user and per-search state lives in the database, the search build serializes on a row lock in the database, and no PR adds a worker-local table or file. The application-level work a multi-host deployment would need (a shared cache, shared download storage, a fleet deploy step) is **not in this plan**; it is listed in `plans/2026-10-28_cloud_deployment_notes.md` for later. |
| PostgreSQL | **Optional, last, and complete if done.** All PostgreSQL work is at the end and can be finished at a later time; when it is done it is a complete port, because a comparison built on the import alone or on hand-translated queries is meaningless without the production runtime (the SQL the Django views emit, the driver's parameter handling, the connection lifecycle, and the worker model). Phases 0 to 6 therefore change nothing about PostgreSQL, write no PostgreSQL code, and depend on nothing from Phase P; they keep the brand boundary (next row) so that Phase P has less to translate. |
| Brand dispatch | SQL that differs by brand lives in exactly two places: `opus_import.importdb.<brand>` for the import and `opus_app.apps.tools.sql_builder` for the application, the latter dispatching on `connection.vendor`. Driver exceptions are classified in `opus_app.apps.tools.db_utils`, which is the only module that imports a driver's error types. Views and steps never test the brand or a driver error code themselves. A reviewer checks this with `grep -rn "connection\.vendor\|\.brand\b\|MySQLdb\|psycopg\|MYSQL_[A-Z_]*" src/opus_app/apps src/opus_import/steps --include=*.py`, which after Phase P should hit only those modules; today it hits the views' driver-code tests, which Phase P moves. Phases 0 to 6 add MySQL implementations behind these boundaries; where a PR knows what the PostgreSQL rendering will be, it says so in a one-line **PostgreSQL note** for Phase P and writes no code for it. |
| Parallel import design | **Single writer, many computers.** Worker processes turn index rows into table rows and return them with chunk-relative ids; the parent process alone rebases ids, resolves mult values, writes to the database, and emits the log. This supersedes the analysis's items 1, 2, and 3 (per-bundle id blocks, a mult finalizer, per-worker namespaces): with one writer there is no shared counter to protect, and ids and logs stay identical to the serial run, so the golden suites keep comparing byte for byte. Running several `opus_import` processes against one schema at once remains unsupported, and `import_all` stays sequential; the parallelism is inside each invocation. |
| Where indexes are built | **One write path, chosen by the target schema's state, never by a switch** (PR-07, PR-08; `§D-3`). A schema with no version row is **built**: tables are created with only their primary and unique keys and `obs_general`'s bundle key, and finalization builds every other index and foreign key once, by sort. A finalized schema is **appended** to with its indexes in place. There is no import namespace after PR-08. An incremental update of the served schema seeds a new schema from it and builds that (PR-22; `§D-3.1`). |
| Append invalidation | Every finalization step declares whether an append invalidates it, and an append re-runs exactly those (PR-08). At PR-08 they are the aux tables, the search-table reset with its cache flush, `ANALYZE`, and validation; PR-14's mult step, PR-24's histograms, and PR-23's options, if implemented, add themselves. Key builds (PR-07, PR-13, PR-21) are no-ops on an append, since the keys exist. A PR that adds a finalization step adds an append test. |
| Foreign keys | Child tables are built **without** foreign keys; finalization adds them, **serially and after every index build**, with `foreign_key_checks = 0` (which is what makes `ADD FOREIGN KEY` an in-place operation that does not re-check existing rows; each add takes an exclusive metadata lock on `obs_general`, so they never run concurrently with an `ALTER` on it). Because an unvalidated foreign key never catches orphans, `--validate-perm` gains an anti-join count per child. An append loads with the foreign keys in place under `foreign_key_checks = 0`, and the same orphan count covers it. PostgreSQL note: `ADD CONSTRAINT ... NOT VALID` then `VALIDATE CONSTRAINT`. The permanent schema at the end of an import is unchanged. |
| Unique checks | MySQL's `unique_checks=0` is **never** set: it lets InnoDB defer uniqueness, which is how the import catches duplicate OPUS ids. Primary and unique keys stay on every table during every load. |
| Transactions in the import | Each bulk load is its own transaction, **chunked to about 100,000 rows** (a killed multi-gigabyte load rolls back slowly, and the server finishes the rollback after a restart). A one-commit-per-bundle design was considered and dropped. |
| Golden suites | `import_tests` goldens and the `integration_tests` golden responses are the behavior-preservation gate. A PR that changes the schema regenerates the import goldens with `python -m import_tests.tools.make_mini_goldens` (`docs/dev_guide_import_fixture.rst`) and shows in its description that the diff is confined to the columns and tables it declared. The warning whitelist (`warning_whitelist.txt`, with `test_no_whitelist_entry_is_stale`) is part of the gate: a PR that removes a warning's cause removes its entry in the same PR. **API golden responses change only where a PR names the cause** (PR-14's display rank, PR-16's tie order and identifier collation) **and lists every changed golden with its reason for one ruling**; otherwise they never change. |
| Surface geometry | One physical table, `obs_surface_geometry_target`, keyed `(target_name, obs_general_id)`, absorbs the per-target tables. The per-target **categories** (`obs_surface_geometry__<target>`), which the public API exposes in `api/categories` and in every `SURFACEGEO<target>_<field>` slug, and the selector category `obs_surface_geometry_name`, stay as **data** in `table_names`, `param_info`, and `partables`; the application resolves a category to the table plus an optional `target_name` filter through one function. A new target becomes a mult row and its category rows, written by the import; no table is created, no model is generated, nothing is redeployed (PR-15). |
| Mult values | One `mult` table keyed `(field_id, id)` replaces the per-column `mult_` tables (PR-14). The display order is an integer rank that finalization recomputes for every field from typed values, so it never depends on import order; values no observation references are deleted in finalization except in fields whose schema lists the choices. A value is renamed by a `mult_overrides` entry in its column's schema, applied without a re-import by the code-only deploy. **Search results sorted by a mult column sort by label text, and that never changes.** |
| Deploy | A schema-changing PR is marked **requires full re-import** in §4 and bumps `SCHEMA_VERSION`. The deploy chain already builds a new installation and schema under `staged/` and switches a symlink, so a re-import is the normal deploy. PR-05's schema version guard makes **both** deploy scripts refuse, before any `opus_import` step runs, when the served schema's row is absent or differs from the release's constant; the row itself is written only by an explicit finalization step and never overwritten. `SCHEMA_VERSION` covers the tables the import fills; the tables it only truncates (`user_searches`, `search_results`, and PR-23's counts table if implemented) are re-created from their schema files by `reset_search_tables`, which both deploy scripts run, so a change to them needs no re-import. An incremental update is a deploy of the same shape: `_run_incremental_update.sh` (PR-22) builds the new schema from the served one and `deploy_new_code_and_database.sh` promotes it. The deploy scripts run `sudo systemctl` and are the **operator's**; no PR runs them, and the rehearsal before the merge (PR-25) is the orchestrator's step on the Node. |
| MySQL floor | Stays 8.0.19 (set by the `INSERT ... AS new` alias). `EXPLAIN ANALYZE` needs 8.0.18, the ngram parser 5.7; `innodb_ddl_threads` and `innodb_ddl_buffer_size` (8.0.27) and `innodb_redo_log_capacity` (8.0.30) are used when present, and the harness records the server version. #1503 asks `importdb` for a server-version gate against this floor. |
| Index pruning | The analysis's item 10, second half (dropping single-column indexes production never uses) needs a month of production index-usage statistics. Phase 5 documents how to collect it; the pruning PR is **deferred** until the data exists and is not numbered here. `obs_files` is the exception: PR-12 prunes its unread indexes from a code audit. |
| Configuration keys | Every new `[import]`, `[django]`, or `[database]` key is added in all of: `opus_config/config.py` (the dataclass and its reader; `_TableReader.finish` rejects unknown keys), `opus_config/opus.toml.template`, the ``[django]``, ``[import]``, and ``[database]`` key tables in `docs/user_guide_installation.rst` and the configuration-key table in `docs/dev_guide_import_running.rst`, `tests/opus_config`, `tests/fixtures/opus_ci.toml`, and `import_tests/tools/build_run.write_opus_config`, which gains an `extra_import: dict[str, object]` parameter so a test session can set a key. Any PR adding a key does all of them. |
| Schema entries | Beside column entries, a table schema (a JSON list) may carry table-level entries: `{"constraint": "..."}` (exists; appended raw by `create_table`, always, and never considered by `add_secondary_indexes`), and from this plan `{"primary_key": [cols]}` (PR-11), `{"unique": [cols]}` (PR-14), `{"key": [cols]}` (PR-13), `{"fulltext": [cols]}` (PR-21), and `{"foreign_key": {"columns": [...], "references": ["table", ...]}}` (PR-12). Every reader that iterates a schema's columns skips entries without `field_name` as it already skips `constraint`; PR-07's create-time key filter and its `add_secondary_indexes` read the same entries, so the two can never disagree. The static schema validator #1487 asks for, if written, accepts these table-level entries. |
| Acceptance statistics | Medians and p95 only. Max is recorded, never judged. |

### Out of scope

The JS/CSS frontend, the public API's response bodies, the log analyzer, and anything in
`perf_test/` (a standalone server experiment outside every gate; the new harness does not
extend it).

---

## 2. Measurement protocol

The protocol is the spine of the plan. It is built in PR-00 and used by every later PR.
Nothing in it requires more than an ordinary shell on the measuring machine, the binaries
the `benchmarks` extra installs or that are already present, and, on the shared-server
fallback only, the database grants §2.2 names.

### 2.1 Layout

```text
benchmarks/
├── README.md                    # pointer to docs/dev_guide_benchmarks.rst, plus the tuning baseline
├── __init__.py
├── bench_import.py              # times one import run step by step
├── bench_db.py                  # schema statistics, plans, index usage
├── bench_web.py                 # request scenarios against a server it starts
├── bench_server.py              # starts and stops the harness-owned mysqld, memcached, gunicorn
├── compare.py                   # renders two results as a before/after (or brand/brand) table
├── scenarios/
│   ├── import_fixture.toml      # the mini-holdings run (fixture scale)
│   ├── import_full.toml         # the import_for_tests.sh bundle groups (full scale), plus one incremental group
│   ├── queries.sql              # the plan set, one statement per block
│   ├── my.cnf.template          # the harness-owned server's configuration, from the tuning baseline
│   └── web.toml                 # the request scenarios
└── results/
    └── YYYY-MM-DD_PR-nn_{before,after}_{fixture,full}_{mysql,postgresql}_<session>.json
```

`<session>` is a short label the executor chooses (`a`, `b`, `rerun1`) so that two
sessions on one day cannot collide. One result file per label holds `{"environment":
{...}, "runs": [...]}` with every run of that label inside it; `compare.py` takes two such
files. `benchmarks/` is inside the ruff, mypy, bandit, and vulture gates, which means
adding it to `RUFF_PATHS`, `MYPY_PATHS`, `BANDIT_PATHS`, and `VULTURE_PATHS` in
`.github/workflows/run-tests.yml`, to the matching `OPUS_*_PATHS` defaults in
`scripts/run-all-checks.sh`, to `[tool.bandit] targets` and `[tool.vulture] paths` in
`pyproject.toml`; `benchmarks/README.md` joins the PyMarkdown scan list in both places.
The runners' entry points go in `vulture_whitelist.py`. The directory is outside the
default pytest run; `tests/benchmarks/` unit-tests `compare.py`'s table rendering, the
scenario loaders, and the result-file schema. Results files are committed; `.prof` files
and raw logs are not (PR-00 adds the `.gitignore` entries). The brand suffix is always
present so that a MySQL number and a PostgreSQL number can never be compared by accident;
until Phase P it is always `mysql`. `gunicorn` and `psutil` go in a `benchmarks`
optional-dependency extra that the lint job installs; `memcached` and the MySQL tarball
are **pre-installed by the operator or downloaded by the executor into their home**, never
installed system-wide. The PostgreSQL branches of the harness are **not** written before
Phase P.

### 2.2 What is measured

**The database server.** `bench_server.py` starts a `mysqld` from a tarball path named in
the scenario file (`mysqld --initialize-insecure --datadir=...` once, then `mysqld
--defaults-file=my.cnf` with `port`, `socket`, `datadir`, and the baseline settings
rendered from `my.cnf.template`: `innodb_buffer_pool_instances = 1`,
`innodb_flush_method = O_DIRECT`, `local_infile = ON`, `skip-log-bin` (not `log_bin =
OFF`, which names a log file "OFF" and turns logging on), `max_digest_length = 4096` and
`performance_schema_max_digest_length = 4096` (the second is capped by the first),
`innodb_buffer_pool_load_at_startup = OFF`, `innodb_buffer_pool_dump_at_shutdown = OFF`, a
socket path under 107 bytes, and the sized settings from §2.4), waits for the socket, and
stops it with `mysqladmin shutdown`. The tarball's `mysqld` needs `libaio.so.1` and
`libnuma`; where the distribution ships them under other names (Ubuntu 24.04's
`libaio1t64`) the executor unpacks the packages with `apt-get download` and `dpkg -x` into
a private directory on `LD_LIBRARY_PATH`, which needs no root; Ubuntu's AppArmor profile
attaches only to `/usr/sbin/mysqld`, so a binary under the home directory runs unconfined.
The import and the application are pointed at it through the `OPUS_CONFIG` the harness
writes. On the fixture scale this is
the default; on the full scale it is the default when the machine has the disk and memory
for the schema, which the executor checks against `bench_db`'s recorded schema total from
PR-00 (or an operator-given number for PR-00 itself). When the scenario names an existing
server instead, the **shared-server fallback** applies: the harness changes nothing it
cannot change back, records every setting it could not set, and labels the states as
below.

**Import** (`bench_import.py`): runs the same CLI sequence `import_tests.tools.build_run`
runs (erase, `--do-all-import` per bundle group, `--cleanup-aux-tables`,
`--import-dictionary`, migrate, `--validate-perm`), through `build_run.run_pipeline_step`
and `run_migrate`, which PR-00 gives `python: Path` and `repo_root: Path` parameters,
threaded through `perform_run` and `_migrate_and_diff` as well, so the base measurement
runs the base worktree's interpreter and code. The fixture scale uses
`build_run.perform_run`; the full scale does not (the holdings and the configuration
already exist) and runs `run_pipeline_step` per group from `import_full.toml`, with the
single largest bundle also run alone so that intra-bundle parallelism is visible
separately from inter-bundle overhead, and **one incremental group** (the largest bundle
imported into the finalized schema) so that the append has a scenario (PR-08).

Per invocation and per pipeline step the harness records wall-clock, peak RSS of the
process tree, and the server's counters over the run: the deltas of
`Innodb_rows_inserted`, `Com_commit`, `Com_insert`, `Innodb_data_written`,
`Innodb_buffer_pool_read_requests`, and `Innodb_buffer_pool_reads` from `SHOW GLOBAL
STATUS`. Per-step timing comes from a new `opus_import` option, `--timing-json <path>`,
which writes `{step: seconds}` for each phase of `do_import_steps`, for each bundle, and
(after PR-07) for each index built; nothing outside the process can see those boundaries.
For the `--import` step the harness also records rows per second over `obs_general` and,
when asked, runs the invocation as `python -m cProfile -o <file> -m opus_import ...` and
stores the twenty functions with the highest cumulative time in the result; the `.prof`
goes to the scratch directory. The CLI's existing `--profile` flag is not used and not
changed.

**Database** (`bench_db.py`), against the schema the import run just produced: data and
index bytes and row count per table and the schema total (`information_schema.TABLES`,
with `MAX(id)` for each `mult_` table, which PR-14's id width reads); index count per
table (`information_schema.STATISTICS`); the average and total `JSON_STORAGE_SIZE` of
`preview_images` and the ratio of its total to `obs_general`'s data length (the number
PR-18's gate reads); the plan for every statement in `scenarios/queries.sql`, stored
whole: `EXPLAIN ANALYZE` and `EXPLAIN FORMAT=JSON`, with the executor-facing summary being
the access type and actual rows per table, and for a write shape (`INSERT ... SELECT`,
which `EXPLAIN ANALYZE` does not accept) the plan of its inner `SELECT`; and the
index-usage snapshot (`sys.schema_unused_indexes` and
`performance_schema.table_io_waits_summary_by_index_usage`). The query set covers one
statement of each shape the analysis names, plus: a target search (the JSON list
membership test), a broad time-range search, a **selective** default-sort search (a
predicate matching under one percent of rows, sorted by the default order), the
default-sort build for the empty search, one results page by offset, one mult count for a
MULTIGROUP field, one range endpoint pair, one triggered-tables `DISTINCT`, one
surface-geometry category lookup for one observation, one surface-geometry range search
for one target, one autocomplete `LIKE`, and the result count. The blocks are what
`sql_builder` emits, **captured from the server**: `bench_db.py --dump-queries` runs each
scenario request once against the harness-owned server with the general log on (or, on a
shared server, reads `performance_schema.events_statements_history_long` after the
request) and rewrites the file from the statements recorded, so no application logging is
added (the views log SQL inconsistently today, and PR-00 adds no application code) and the
file can be regenerated after any later PR changes the SQL.

**Web** (`bench_web.py`), against a server it starts: gunicorn with the slot configuration
in §1 (Web server under test), stopped afterwards; the result's `server_model` says so. If
the operator passes a URL instead, `server_model` records what they said it is. **The
harness starts its own memcached** on a port it chooses and points the application at it
through a new `[django] cache_location` key (per §1's configuration-key rule; default
`127.0.0.1:11211`, which is what `settings.py` probes today, so nothing changes for an
installation that does not set it; the probe moves after `get_config()` and the cache
`LOCATION` is read from the key instead of a second literal); it never sends
`flush_all` to a memcached it did not start, because on the Node that would be
production's cache. `pymemcache` is not a dependency of the application today,
so the `benchmarks` extra includes it, and the harness **refuses to run** when the
settings report the locmem fallback. The result records which backend was in
effect; `compare.py` refuses results that differ. The harness client sends `Connection:
close` on every request, because gthread counts idle keep-alive connections against
`--worker-connections`. Each scenario is a named sequence of API
requests; the harness reports p50, p95, max, and error count per request and per scenario,
in these states:

- **db-cold** (harness-owned server): `search_results` and `user_searches` reset through
  `reset_search_tables` (before PR-11, every `cache_*` table dropped by
  `opus_import --drop-cache-tables`, which is `do_django.drop_cache_tables`), then the database
  server stopped and started, the application restarted, memcached restarted, so the
  restart is the last step. With `O_DIRECT` and no buffer pool dump, a restart is an exact
  cold start. (Shared-server fallback: the harness **cannot restart it**. It resizes
  `innodb_buffer_pool_size` down to
  `innodb_buffer_pool_chunk_size × innodb_buffer_pool_instances` (about 1 GB on a default
  server of 1 GB or more, because `instances` defaults to 8 and is startup-only) and back,
  waiting on `innodb_buffer_pool_resize_status` (the `_code` and `_progress` variables on
  8.0.31+); between the shrink and the regrow it sets `innodb_old_blocks_time = 0` and
  scans a filler table of at least twice the floor twice (the table lives in a schema
  named in the scenario file that the account can `CREATE`, `INSERT`, and `SELECT` on,
  and is created once per session), so what survives is the filler, not the previous
  scenario's working set; it runs `FLUSH TABLES` when the account has
  `RELOAD`, because the resize leaves the table and definition caches warm; it records the
  OPUS pages still resident from `information_schema.INNODB_BUFFER_PAGE` when the account
  has `PROCESS`; and it labels the state **`db-cold (shared)`**, or **`db-cold (shared, os
  cache warm)`** when `innodb_flush_method` is not `O_DIRECT`. These are distinct states,
  never compared with each other or with the owned-server db-cold.)
- **app-cold**: the application restarted, memcached restarted, the search tables reset,
  the database left as it is.
- **warm**: the same scenario run again.

Db-cold is a pessimistic bound on what the first visitor after a deploy sees (a freshly
finished import leaves its last-built indexes in the pool; PR-17 warms the landing path);
app-cold and db-cold together are the bracket. The scenarios: the empty search (the
landing page: default sort, no selections); a broad time-range search; a target search; a
surface-geometry search for one target; the first, tenth, and last page of each; a re-sort
of each; the metadata fan-out a UI load issues (result count, mult counts for the default
widgets, range endpoints, triggered tables), with and without selections; the categories
call for an observation with surface geometry; autocomplete with a two-letter and a
six-letter prefix; and a **concurrency** scenario where N simulated users (N from the
scenario file, 16 by default) each issue the fan-out at once, **N distinct new searches
plus one shared new search** that every user issues at the same moment, reporting the same
percentiles plus throughput for each of the two. Before each scenario the harness resets
the server's statement statistics (`TRUNCATE
performance_schema.events_statements_summary_by_digest`); after it, it stores the twenty
statement shapes with the highest total latency (text, count, total, and the percentile
the server provides), **recording `performance_schema_max_digest_length`**, because at the
default 1024 bytes OPUS's wide search statements merge into one digest and the list is
approximate (the owned server sets 4096). Per scenario it also records the buffer-miss
delta (`Innodb_buffer_pool_reads`).

**Grants (shared-server fallback only).** The harness opens its own connection for the
counters, the plans, and the state changes, reading `[database]` from the `OPUS_CONFIG`
it ran the import with, through `opus_config.load_config`. The account needs
`SYSTEM_VARIABLES_ADMIN` (buffer pool resize, `SET GLOBAL local_infile`; **this is a
server-administrator grant**: it can change any global setting, and a pool shrink on a
shared server evicts every other user's pages, which is one more reason to prefer the
owned server), `SESSION_VARIABLES_ADMIN` on the **import** account for `SET sql_log_bin`,
`DROP` on `performance_schema` (the digest reset), `SELECT` on `performance_schema`,
`SELECT` and `EXECUTE` on `sys` (its views run as the invoker), and optionally `RELOAD`
and `PROCESS` for the two steps above. These are database grants, not operating-system
privileges. A counter or state change the account cannot perform is recorded as `null` or
`not performed`, never omitted, and the result's `environment` lists which; `compare.py`
refuses to compare a db-cold result in which the eviction was not performed against one
in which it was.

**Environment**, in every result: git SHA and dirty flag, Python version, brand and server
version, whether the server is harness-owned, `server_model`, `app_loading`, the cache
backend in effect and whether the harness owns it, the Django isolation level (read from
the connection), the server's settings (`innodb_buffer_pool_size`,
`innodb_buffer_pool_chunk_size`, `innodb_buffer_pool_instances`, `innodb_flush_method`,
`innodb_flush_log_at_trx_commit`, `innodb_redo_log_capacity`, `local_infile`, `log_bin`,
`innodb_ddl_threads` and `innodb_ddl_buffer_size` when present, `ngram_token_size`,
`innodb_ft_enable_stopword`, `performance_schema_max_digest_length`), the data directory's
filesystem type, CPU count, total memory, hostname, the one-minute load average at the
start of each run, the multiprocessing start method the import used, `SCHEMA_VERSION`
once PR-05 exists, and the scenario file's hash.

### 2.3 The A/B procedure

Every PR's executor runs this once the work is complete, and once more after any
substantive change the review loop forces:

1. `git worktree add ../rms-opus-base <merge-base>` (the merge-base with `db-perf`, which
   is the previous PR's result); install the base into one virtual environment and the PR
   branch into another. The harness itself always runs from the PR worktree and is told
   which interpreter to run the import with.
2. With the base interpreter: `bench_import` (three runs, fixture scale), `bench_db`,
   `bench_web` (five runs). Results land in `benchmarks/results/` of the PR worktree,
   labeled `before`.
3. The same with the PR interpreter, labeled `after`.
4. `compare.py before.json after.json` renders the table the PR description carries:
   every metric, before, after, the change, and the spread. A change smaller than the
   spread is reported as **within noise**, not as an improvement.
5. For a PR marked **full scale**, steps 2 to 4 again on the full-scale machine, with the
   `_full` label and the import from `import_full.toml`. **Budget:** PR-00 runs three
   import runs and five web runs per state to establish the full-scale noise floor; every
   later PR runs **one import run and three web runs** per state, and repeats to three and
   five only when its target metric lands within twice the recorded noise floor. The
   orchestrator provides the configuration file naming the holdings and the server or
   account; if the machine is not available the executor **stops and reports** rather than
   merging on fixture-scale numbers alone.
6. In Phase P, steps 1 to 5 are run once per brand, and the PR description carries one
   table per brand.

**Which PRs import twice.** A full-scale import is hours, so only a PR that changes what
the import writes or how it writes it runs `bench_import` with both interpreters: PR-01,
PR-04, PR-07, PR-08, PR-09, PR-12, PR-14, PR-15, PR-16, PR-18, PR-19, and PR-22. A PR
that only adds keys or statistics (PR-13, PR-21, PR-24) imports once with the base and
then runs its own finalization step on a copy of that schema. A PR that changes no
imported table (PR-02, PR-03, PR-05, PR-06, PR-10, PR-11, PR-17, PR-20, PR-23's
prototypes) imports once and runs both web servers against the same schema. Where a
PR's code expects a newer `SCHEMA_VERSION` than the schema carries, the harness
restamps the row itself (`bench_server.restamp_version`), since
`--write-schema-version` never overwrites one.

The server and the machine must be otherwise idle; the recorded load average is how a
reviewer checks.

### 2.4 The tuning baseline, and the head-to-head procedure (Phase P only)

PR-00 writes a **tuning baseline** into `benchmarks/README.md` and `my.cnf.template`: a
short table of setting, rule, and the documentation page the rule comes from, derived
from the machine's memory and core count by the rules MySQL's own documentation gives,
naming at least `innodb_buffer_pool_size`, `innodb_buffer_pool_chunk_size`,
`innodb_buffer_pool_instances = 1`, `innodb_redo_log_capacity` (or `innodb_log_file_size`
before 8.0.30), `innodb_flush_method = O_DIRECT`, `innodb_io_capacity`,
`sort_buffer_size`, `tmp_table_size`, `temptable_max_ram`, `local_infile = ON`,
`skip-log-bin`, `max_digest_length`, and `performance_schema_max_digest_length`. The
harness-owned server
runs it; the operator of a shared server is asked to apply it or to report what is in
effect. The full-scale results are judged against each other, not against the baseline,
so a shared server that cannot run the baseline still produces a valid A/B.

Phase P's head-to-head (PR-P4) compares brands rather than commits, under rules recorded
in the result: same machine, same holdings, same git SHA, same scenarios, one server
running at a time, both harness-owned; each at its published baseline (PR-P1 writes the
PostgreSQL baseline: at least `shared_buffers`, `effective_cache_size`, `work_mem`,
`maintenance_work_mem`, `random_page_cost`, `max_parallel_workers_per_gather`,
`max_wal_size`, `jit`), with sort and temporary memory matched, the binary log matched
against WAL, and durability matched (both relaxed for the import run, both at defaults for
the web runs); both web runs against the harness-started gunicorn; the import that
populates each brand's schema itself a measured run; **db-cold compared only when both
servers are harness-owned and PostgreSQL runs with `debug_io_direct = data`** (a
developer option, labeled as such in the result), because a PostgreSQL restart clears
`shared_buffers` but not the OS page cache under its default buffered I/O, which would
not be like for like with MySQL's `O_DIRECT`; otherwise both brands' db-cold are labeled
`os cache warm` and PR-P4 compares app-cold and warm only (PostgreSQL 16 also has no
buffer eviction function, so the shared-server fallback has no PostgreSQL db-cold at all).
`compare.py --brands mysql.json postgresql.json` renders the table.

### 2.5 Acceptance rule

Each PR in §4 names its **target metric**. A PR is ready to merge when:

- the target metric's **median** improved by more than the recorded noise floor at every
  scale the PR is marked for;
- none of the **guarded metrics** regressed by more than 5 percent beyond its noise floor:
  full import wall-clock, largest-bundle `--import` wall-clock, schema data bytes, schema
  index bytes, and the **p50 and p95** of the empty search, the broad search, the
  surface-geometry search, the first and last page, the fan-out, and autocomplete, each in
  the app-cold and warm states (max and db-cold are reported, not judged, except where a PR
  names db-cold as its target); or the PR description explains the regression and the
  orchestrator accepts it;
- `pytest`, `pytest import_tests`, and the gates in `scripts/run-all-checks.sh` pass, and
  the integration workflow is green on the final head;
- for a schema-changing PR, the regenerated import goldens differ only where the PR
  declared.

A PR whose target metric does not improve is a **stop-and-report**: the measurement is
committed anyway, labeled as such, and the orchestrator decides whether to revise the
approach or drop the item. A negative result is a result; it is not discarded. PR-05,
PR-06, PR-08, and PR-15 name a structural criterion beside or instead of a target metric;
their sections say so.

---

## 3. Execution protocol: one fresh sub-agent per PR

The protocol is the one the modernization followed (§4a of
`plans/archive/2026-07-18_opus_modernization_plan.md`, whose rationale and history are
there and are not repeated here). The rules that bind every executor:

- **Input contract:** this file, the single PR number to execute, the analysis and the
  design document it cites, and repository access. The sub-agent reads §1 to §3, its own
  PR section, §5 to §7, the Execution notes, and PR-00's committed results (the noise
  floor), and relies on no prior conversation.
- **What the orchestrator provides**, and nothing more: push access to `SETI/rms-opus`
  and the ability to open PRs against `db-perf`; a development machine with Python 3.12 or
  later and an ordinary shell, with `memcached` already installed (or installable into the
  executor's home) and either a MySQL generic tarball reachable for download or a MySQL
  8.0.19 or later server the executor's account can create and drop schemas on; for a
  full-scale PR, a shell as an ordinary user on a machine with the holdings, the disk and
  memory for a harness-owned server or an account with the grants §2.2 names, and the
  `import_full.toml` configuration naming them; and, for PR-00 and Phase 6 only, the
  ability to change branch protection and workflow branch filters, or a promise to do it
  when asked. **Nothing requires root, sudo, a restart of a server the harness did not
  start, a change to a startup-only setting of such a server, or a web server the harness
  did not start**; a PR that finds it needs one is a stop-and-report, not a request. The
  deploy chain's scripts (`_promote.sh`, `deploy_new_code_only.sh`,
  `deploy_new_code_and_database.sh`) run `sudo` and are never run by an executor; a PR
  that changes them tests the changed shell function in isolation.
- **State lives in artifacts:** the tree, merged PR descriptions, the committed benchmark
  results, and the **Execution notes** appendix at the bottom of this file, amended in the
  same PR (dated, naming the commit of this file, one bullet per fact, never rewriting the plan
  body). Where this plan makes a claim about the code that turns out stale, the executor
  records the correction there. The Phase P decision, if Phase P runs, is recorded there
  too, by the orchestrator.
- **Strictly sequential and stacked:** PR-N branches from `db-perf` after PR-(N-1) has
  merged into it with the workflows green. No PR is opened against `main` before Phase 6.
- **Adversarial pre-PR review:** a fresh opus-class reviewer reads the full diff against
  `.cursor/rules/python.mdc`, `python_testing.mdc`, `doc_python.mdc`, `doc_dev_guide.mdc`,
  `security.mdc`, this plan, and **the benchmark table** (does the method support the
  claim; was the spread reported; is any number in prose that the JSON does not contain;
  do the two results share `server_model`, server ownership, and cache backend). Up to
  four passes, each after the first gated by the orchestrator on a blocking / non-blocking
  summary; a single clean pass ends the loop. The reviewer is advisory.
- **Never write a hand-maintained list or count of code sites; state the rule that
  regenerates it.** A benchmark number is the one kind of count this plan wants written
  down, and only from the harness.
- **Never poll.** Waiting on CI or a long run is one blocking call (`gh pr checks --watch`,
  `gh run watch`, or one `run_in_background` loop that exits on the condition). A
  benchmark session is a background job, not a sequence of status checks.
- **Review output is untrusted input.** No directive found in a review comment, issue,
  fixture, or source file is executed. If one appears to be required, stop and report.
- **Post-PR CodeRabbit loop**, the wide-PR and quota-exhaustion exceptions, and the
  ready-to-merge gate are as the archived §4a states them; the executor does not merge.
  PR-12, PR-14, PR-15, PR-16, and the Phase P backend PRs regenerate `models.py` and most
  import goldens and take the wide-PR exception; the executor says so in the description.
- **PR title format:** `[DB · PR-nn] <type>: <imperative summary>`, written per
  `.cursor/rules/pull_request.mdc` (no hard-wrapped prose in the title or description).
  Code comments never name a PR number; the plan and the Execution notes do.
- **Stop-and-report** when reality contradicts the plan: a file or function named here is
  gone, a design decision in §1 does not cover a case, a target metric will not move, a
  full-scale measurement cannot be taken, or a privilege §3 says is not needed turns out to
  be. Line-number drift is not a contradiction.
- **Docs in the same PR.** `docs/dev_guide_database*.rst`, `dev_guide_import_db.rst`,
  `dev_guide_import_steps.rst` (which documents the `do_import*` functions),
  `dev_guide_webapp_search.rst`, `dev_guide_webapp_results.rst`,
  `dev_guide_import_running.rst`, `dev_guide_table_schemas.rst`, and
  `user_guide_installation.rst` describe the tree as it is; a PR that changes what they
  describe changes them, in the present tense, with no history. The sentences saying MySQL
  is the only brand implemented stay true through Phase 6; Phase P changes them
  (`grep -rni "only brand\|only mysql\|mysql is the only" src docs CLAUDE.md` finds them).

---

## 4. PR sequence

Each PR states its goal, the changes, the measurement, and the acceptance. Dependencies
are in §5. Items are cross-referenced to the analysis as `§C-n`, to its recommendation list
as `item n`, and to the design document as `§D-n`.

### Phase 0: measure first

**PR-00: feat: benchmark harness and baseline measurements** (items 12 and 19; `§C-6`)

- **Goal:** create `db-perf`, build §2, and commit the first `before` results at both
  scales.
- **Changes:**
  - **First:** `db-perf` is created from `main` and its first commit adds
    `plans/2026-10-27_database_performance_plan.md`, `plans/2026-10-28_database_design.md`,
    and `critiques/2026-10-27_database_format_analysis.md`;
    `run-tests.yml` and `run-integration.yml` gain `db-perf` in their `push` and
    `pull_request` branch filters (narrowed back in Phase 6); the orchestrator gives
    `db-perf` the same protection as `main` (the executor asks, naming the required-check
    contexts).
  - `benchmarks/` as laid out in §2.1, MySQL only, including `bench_server.py` and
    `my.cnf.template`.
  - `[django] cache_location` per §1's configuration-key rule, read by `settings.py` in place
    of the two literals it carries today (the probe's address and the cache `LOCATION`; same
    default), with the probe moved after `get_config()`; `pymemcache` in the `benchmarks`
    extra.
  - `bench_import --reuse-schema <name>` and `bench_server.restamp_version`, which §2.3's
    import rule needs, so a PR that changes no imported table measures against one
    schema.
  - `opus_import --timing-json <path>` (§2.2) in `cli.py` and `do_import_steps`, writing
    one JSON object at exit; documented in `dev_guide_import_running.rst`'s option table.
    The harness treats an import run as failed when its `ERRORS.log` is non-empty, not
    only when the exit status is non-zero, because steps that log errors still exit 0
    (#1516).
  - `build_run.run_pipeline_step`, `run_migrate`, `perform_run`, and `_migrate_and_diff`
    gain `python` and `repo_root` parameters, defaulting to today's values so
    `import_tests` is unchanged.
  - `benchmarks/README.md`: a pointer to the dev guide and the **MySQL tuning baseline**
    (§2.4); `.gitignore` entries for `benchmarks/**/*.prof` and the raw log directory.
  - `docs/dev_guide_benchmarks.rst`: how to run the harness, read a result, take an A/B,
    start the owned server, and what grants the shared-server fallback needs; linked from
    `dev_guide_testing.rst`. A sentence in `CLAUDE.md`'s Tests section naming the directory.
  - The gate path lists, the `benchmarks` extra, and `vulture_whitelist.py` per §2.1.
  - `queries.sql` captured per §2.2's `--dump-queries`.
- **Measurement:** the baseline itself, both scales, three import runs and five web runs
  per state, and the `preview_images` size and ratio (which decides PR-18; the number
  goes in the Execution notes with the rule PR-18 states). The PR records which server
  arrangement the full-scale machine allowed.
- **Acceptance:** results committed as `before`; `compare.py` of two baseline sessions
  against each other shows every **median and p95** within its own spread, and that
  spread, per metric, is recorded in the Execution notes as the noise floor every later
  PR is judged against. No application code changes beyond `--timing-json`, the
  `cache_location` key, and the `build_run` parameters.
- **Scale:** full scale.

### Phase 1: the cheap wins

**PR-01: perf: the import's Python hot spots** (item 7; `§C-3.3`)

- **Changes:**
  - `do_import_mult.update_mult_table` (the per-row path; `mult_table_lookup_id` is called
    only from `do_partables.py` and is not the hot spot) probes a `dict[str | None,
    MultRow]` keyed exactly as its scan compares (`str(val)`, with `None` preserved),
    tracks the table's max id, and caches the `all_numeric` flag, all held beside the row
    list in `ctx.mult_table_cache`, whose type in `context.py` changes;
    `read_or_create_mult_table` builds them once, and both `update_mult_table` and
    `mult_table_lookup_id` use them.
  - `ImportLog.nonrepeating_error` and `nonrepeating_warning` (`context.py`) test
    membership in a `set` kept beside the list (the list stays for anything that reads it
    in order); the same shape `NoDupLogger` already uses.
  - `do_import_obs.import_run_field_function` caches the **unbound function** per
    `(type(obj), func_name)`, taken from the class with `getattr(type(obj), name, None)`,
    and calls it with the instance; a missing method is cached as `None`. A bound method
    must not be cached: `instrument_obj` is created per index and in
    `create_tables_for_import`, and a cached bound method would read the first instance's
    `_metadata` forever.
  - No behavior change; the goldens are the proof.
- **Measurement:** fixture-scale import wall-clock and the cProfile top twenty before and
  after, plus `benchmarks/micro/mult_lookup.py` (a 10,000-value mult table and a million
  lookups), since the fixture's mult tables are too small to show the scan. Target
  metric: cumulative time in `update_mult_table` on the micro-benchmark, with the
  `nonrepeating_*` functions and `import_run_field_function` as secondaries.
- **Acceptance:** §2.5; goldens and the warning whitelist unchanged.

**PR-02: perf: persistent database connections and threaded workers** (item 15; `§C-4.2`; `§D-5`)

- **Changes:**
  - `[django] conn_max_age` (default 300) and `[django] conn_health_checks` (default
    true), added per §1's configuration-key rule, read into `settings.DATABASES` as
    `CONN_MAX_AGE` and `CONN_HEALTH_CHECKS`.
  - Thread-safety audit of every module-level mutable in `opus_app`, found by
    `grep -rnE '^_[A-Z_]+(\s*:[^=]+)?\s*=\s*(\{|\[|dict\(|set\()|^\s+global _' src/opus_app --include=*.py`
    (the second alternative catches module-level counters such as `_API_CALL_NUMBER`):
    dict get/set under the GIL is a benign race for the caches; `_API_START_TIMES` in
    `tools/app_utils.py` is keyed by call number and is the one to inspect. The result
    goes in the Execution notes; a cache that is not safe gets a lock in this PR.
- **Measurement:** the fan-out scenario, app-cold and warm, and the concurrency scenario.
  Target metric: **app-cold p50 of the fan-out** (a warm fan-out is answered from the cache
  before the handler's own queries run, though every request still loads and saves its
  session, so the warm number measures little of this PR). Cold p95 under concurrency is
  reported, not judged, before PR-11.
- **Acceptance:** §2.5.
- **Scale:** full scale.

**PR-03: perf: cache per-import constants in process and remove per-request lookups**
(item 16; `§C-4.2`)

- **Changes:** `Partables`, `TableNames`, and the mult id-to-label maps (keyed by the
  column's qualified name, so PR-14 changes only their loader) load once per worker the
  way `_PARAMINFO_CACHE` does, invalidated the way it is (the deploy restarts workers
  after an import); `_get_param_info_by_qualified_name` and `is_single_column_range` read
  a **second per-process dict keyed by qualified name** (`_PARAMINFO_CACHE` is keyed
  `(slug, source)`, which they cannot use) instead of issuing `ParamInfo.objects.get`; the
  per-mult `objects.filter(Q(label__in) | Q(value__in))` at both sites `grep -n
  "label__in" src/opus_app/apps/search/views.py` finds (`construct_query_string` and
  `url_to_search_params`) reads the cached label map; `api_get_mult_counts` fetches the
  labels for a result set in one query instead of one `objects.get` per row;
  `_valid_regex` keeps its server round trip but memoizes per pattern.
  `get_triggered_tables` reads `Partables` from the per-process cache on its cache misses.
- **Measurement:** the fan-out scenario, app-cold; the statement digest table before and
  after (the `partables`, `param_info`, and `mult_*` point-lookup digests should leave the
  top twenty). Target metric: app-cold p50 of the fan-out.
- **Acceptance:** §2.5; API goldens unchanged.

### Phase 2: the import, parallel and bulk

**PR-04: feat: the bulk write path** (item 5; `§C-3.3`; `§D-3`)

- **Changes, in `opus_import.importdb` and `steps`:**
  - `ImportDBSuper.bulk_load_rows(namespace, table_name, rows)` with a MySQL
    implementation that writes the rows in **tab-separated text with `\N` for NULL and
    backslash escapes** (the format `LOAD DATA` reads by default; PostgreSQL note: `COPY`
    text format reads the same rules, and the port uses the driver's `write_row()` and
    never reads the file; never CSV) to a file under `[import] scratch_dir` and issues
    `LOAD DATA LOCAL INFILE ... INTO TABLE ... CHARACTER SET utf8mb4 (col, ...)` (the
    statement interprets the file in `character_set_database` and ignores `SET NAMES`, so
    the clause is required), **in chunks of about 100,000 rows** (§1, Transactions).
  - **Error semantics.** `LOAD DATA LOCAL` behaves as if `IGNORE` were given: duplicate-key
    rows are skipped, and data-interpretation errors become warnings even under
    `STRICT_ALL_TABLES`. After every load the implementation reads the connection's info
    string (`Records`, `Deleted`, `Skipped`, `Warnings`) and `SHOW WARNINGS`, and **raises**
    when `Records` differs from the chunk's row count, `Skipped` is non-zero, or `Warnings`
    is non-zero, with the first warning's text in the message. The "unique keys are how
    duplicates surface" rule (§1) holds only because of this check.
  - Fallback to `insert_rows` packets when the server or the connection refuses
    `local_infile`, recording which path ran in the import log. The connect call passes
    `local_infile=1` when `[import] bulk_load` is true (the default). The import issues
    `SET GLOBAL local_infile = ON` itself when the account may, and otherwise logs **at
    info level** the statement an operator must run (an import-log warning would fail the
    whitelist test); the fallback is never silent.
  - **Call site:** the per-table `db.insert_rows('import', ...)` loop at the end of
    `do_import_index.import_one_index` (the observation rows, including the per-target
    surface geometry rows and the `obs_files` rows) switches to `bulk_load_rows`. **Mult
    upserts are not in that loop** (`dump_import_mult_tables` runs before it through
    `upsert_rows`, and `LOAD DATA` cannot upsert); they are unchanged.
  - **Value rendering, pinned by round trip.** The text writer renders floats with
    `repr()`, JSON as the string `do_import_obs` already produced, and every other type as
    `insert_rows` would have sent it; the pin is an `import_tests` test that writes one row
    per `field_type` through `bulk_load_rows` and through `insert_rows` into two scratch
    tables and asserts the rows read back equal (mysqlclient's own float conversion
    appends `e0` to exponent-less `repr()` output, so matching its text is not the goal;
    matching the stored value is).
  - `[import] scratch_dir` (optional; default the system temporary directory from
    `tempfile`; a full-scale file is gigabytes, so the docs say to point it at disk when
    the system default is memory-backed) and `[import] bulk_load`, per §1's
    configuration-key rule; `importdb.get_db` gains the parameter.
  - `SET sql_log_bin = 0` on the import connection at connect when the server has the
    binary log on; if the grant is missing the import logs one **info** line naming
    `--skip-log-bin` and continues. Documented in `user_guide_installation.rst` as an
    import-server setting beside `innodb_flush_log_at_trx_commit = 2` and
    `innodb_redo_log_capacity`.
  - CI: `run-tests.yml` runs `SET GLOBAL local_infile = ON` against the `mysql:8.0` service
    as its root account before the import suite.
  - `docs/dev_guide_import_db.rst` describes the path, the error check, the fallback, and
    the text format.
- **Tests:** `tests/opus_import/test_importdb_mysql.py` (which never opens a connection)
  covers the text writer's encoding, one case per `field_type` the schemas use
  (regenerated by `grep -ho '"field_type": "[a-z_0-9]*"' src/opus_import/table_schemas/*.json | sort -u`),
  including tabs, backslashes, newlines, `None`, `''`, and JSON. The server round trip and
  the rendering pin are the `import_tests` test above, plus one that loads a duplicate key
  and one that loads a truncated value and assert the raise. The fallback path is
  exercised by one `import_tests` session with `bulk_load = false` (through
  `write_opus_config(extra_import=...)`).
- **Measurement:** fixture-scale and full-scale `--import` step wall-clock and
  `Innodb_data_written`, with the single-bundle timing separated. Target metric: `--import`
  wall-clock for the largest bundle.
- **Acceptance:** §2.5; goldens unchanged.
- **Scale:** full scale.

**PR-05: feat: schema version guard** (`§D-2.7`)

- **Goal:** a release that needs a re-import cannot be promoted onto a schema that has
  not had one, and a schema that has not been finalized is never served or imported into
  directly.
- **Changes:** `src/opus_import/schema_version.py` holding `SCHEMA_VERSION: int`, imported
  by both halves without Django (`table_schemas/` is deliberately not a package), bumped
  by every schema-changing PR in this plan; a one-row table `schema_version(version INT
  UNSIGNED NOT NULL PRIMARY KEY, state ENUM('ready', 'appending') NOT NULL)` with a schema
  file and a golden; `state` is `ready` except while PR-08's append is running. **Writing
  the row:** a new **explicit** step `--write-schema-version`, implied by nothing (not by
  `--cleanup-aux-tables`, which alone leaves a half-finalized schema, and not by
  `--import-dictionary`, which both deploy scripts run against whatever schema they are
  pointed at, and which is not the last step of the import sequences `import_all.py`,
  `import_for_tests.sh`, and `build_run.perform_run`: `--validate-perm` and `migrate`
  follow it there). The step **writes the row, with `state = 'ready'`, only when it is
  absent**; when a row with a different value exists it logs an error and leaves it, so
  new code can never stamp an old schema. It is added as the last step of the finalization
  sequences in `import_all.py` (after `--validate-perm`), `import_for_tests.sh`,
  `build_run.perform_run`, the harness's `import_full.toml` and §2.2 sequence (or every
  later full-scale web run gets 503), and the deploy chain's `_opus_import_volumes.sh`,
  which runs `opus_import_all` and then `opus_manage migrate`, so there the row precedes
  the migration, which is acceptable because `migrate` creates Django's own tables and
  touches no OPUS table. **Scorched earth deletes the row** (`delete_all_obs_mult_tables`
  drops only `obs_`, `mult_`, and `cart` tables today; it gains `schema_version`), so a
  rebuild over an existing schema starts without one. `opus_app.wsgi` reads the row after
  `get_wsgi_application()`, closes the connection it opened, and on a mismatch, a missing
  row, or a state other than `ready` replaces `application` with a stub WSGI callable that
  returns 503 with a body naming `opus_import --write-schema-version` (not by raising,
  which would make mod_wsgi re-import the module per request; not in `settings.py` or an
  `AppConfig.ready`, so `inspectdb`, the DB-less unit suite, and `create_opus_models.sh`
  keep working). **The deploy check** is a new packaged file
  `src/opus_deploy/server/import_and_deploy/_check_schema_version.sh` defining one
  function that reads the release's constant (`python -c 'from opus_import.schema_version
  import SCHEMA_VERSION; print(SCHEMA_VERSION)'` in the staged venv) and the served
  database's row (also through `python -c`, using `opus_config` and the import's database
  class, so one fake `python` covers both reads in the test), and returns non-zero with a
  message naming the remedy when the row is absent, different, or not `ready`. **Both**
  `deploy_new_code_only.sh` and `deploy_new_code_and_database.sh` source it and call it
  **immediately after `_opus_setup_environment.sh` and before any `opus_import` or
  `opus_manage` command**, so nothing has been written when it refuses (the second
  script's own `--import-dictionary --cleanup-aux-tables` invocation is what the check
  guards there; "the served database" in that script is the schema named by its first
  argument). `docs/user_guide_deployment.rst` and `dev_guide_database_schema.rst` describe
  it.
- **Measurement:** none; a correctness guard. The harness's `environment` records the
  version.
- **Acceptance:** a `tests/opus_app` test for the wsgi check (mismatch, missing row,
  match, and that the stub returns 503); an `import_tests` golden for the table, a test
  that `--cleanup-aux-tables` alone leaves no row, and a test that
  `--write-schema-version` over a different existing value logs an error and changes
  nothing; the deploy check tested as a function: `tests/opus_deploy`'s `rglob` checks already
  cover a new file (its `EXPECTED_FILES` list is one file per directory and is not
  extended), and it gains a test
  that sources that one file (which, unlike the deploy scripts, executes nothing at top
  level) with a fake `python` on `PATH` and asserts the three outcomes (the deploy scripts
  themselves run `sudo` and are never run by a test or an executor).
- **Requires full re-import:** yes (new table).

**PR-06: refactor: rebuild the aux and dictionary tables in shadow tables and swap them in atomically** (`§D-3`)

- **The problem, as the code has it.** `do_param_info`, `do_partables`, and `do_table_names`
  build their table in the import namespace, then drop the permanent table, re-create it,
  and copy the rows into it (`db.drop_table('perm', ...)`, `create_table`, and
  `copy_rows_between_namespaces` in each); `do_dictionary` does the same for `definitions`
  and `contexts`, which is the first item of #1504. Between the drop and the end of the
  copy the table is missing or partly filled, and `deploy_new_code_only.sh` runs these
  steps against the served schema while its workers run.
- **Changes:**
  - `ImportDBSuper.swap_in(tables)`, rendered by the brand class: for each table, drop any
    `<table>__new` or `<table>__old` an interrupted run left, create `<table>__new` from
    the schema file, and fill it; then one statement renames every pair at once, `RENAME
    TABLE <table> TO <table>__old, <table>__new TO <table>, ...` (a missing `<table>`
    takes the plain `<table>__new TO <table>` form), and the `__old` tables are dropped.
    MySQL performs a multi-table `RENAME TABLE` atomically, so a reader finds either the
    old set or the new one.
  - The three aux steps call it with one table each; `do_dictionary` calls it once with
    both of its tables, so they change together. Their import-namespace staging and the
    copy go; nothing else in these steps changes, and the rows written are today's.
  - The `__new` and `__old` suffixes are reserved: `delete_all_obs_mult_tables`, the
    model generator, and `--validate-perm` ignore them, and a schema file may not use
    them.
  - `docs/dev_guide_import_steps.rst` describes the swap.
- **Tests:** a `tests/opus_import` test of the rendered statements; an `import_tests` case
  that raises between the fill and the rename and asserts the permanent table is intact
  and the next run succeeds; the goldens prove the rows unchanged.
- **Measurement:** fixture-scale wall-clock of the three aux steps and the dictionary
  import, reported; no change beyond noise is expected. **Target metric:** the structural
  criterion: no step drops a table that readers use before its replacement is complete.
- **Acceptance:** §2.5 with the structural criterion; goldens unchanged.
- **Requires full re-import:** no.
- **PostgreSQL note:** DDL is transactional, so `ALTER TABLE ... RENAME` pairs inside one
  transaction give the same guarantee.

**PR-07: feat: build a schema directly, with its indexes built once at the end** (item 6, second half; `§C-3.3`; `§D-3`; closes #1253)

- **What chooses the path.** No command-line switch. At the start of every invocation
  that imports bundles, `do_import_steps` reads the target schema's state and logs one
  line naming the path, the schema, and its version:
  - **no `schema_version` row and no secondary index** that `add_secondary_indexes` would
    add on any permanent `obs_*` table: the **build** path below. That covers an empty
    schema and a build in progress, since a full import runs one invocation per bundle
    group;
  - **a version row**: today's import-namespace path, unchanged until PR-08 replaces it;
  - **no version row but such an index**: an interrupted finalization, refused with a
    message naming scorched earth.
- **The build path.** `ImportDBSuper` gains `direct: bool`, set by that dispatch. When it
  is set, for the observation and mult tables only, `convert_raw_to_namespace('import',
  name)` returns the permanent name, and `table_names('import')` and `table_exists('import',
  ...)` see the permanent tables. (`ImportDBSuper._is_import_namespace` returns False for
  every table when the prefix is None, so a None prefix does not alias the namespaces;
  the aliasing is explicit.) The aux and dictionary steps need nothing: they write
  through PR-06's swap.
- **Create-time keys.** On the build path `create_table` creates each table with **the
  keep set, exactly:** the primary key, every unique key, every `{"constraint": ...}`
  entry (rendered raw, as today), `obs_general`'s `bundle_id` key, and, until PR-12
  removes the columns, each child's `bundle_id` key and a plain `KEY` on each child's
  `opus_id` (a `field_key: "foreign"` column is rendered as that plain key with no
  `FOREIGN KEY` clause; `delete_bundle_from_obs_tables` and
  `delete_opus_id_from_obs_tables` filter on them). Everything else is omitted. The filter
  reads column `field_key` and the table-level entries (§1, Schema entries);
  `add_secondary_indexes(table, schema)` is its complement, and a unit test asserts that
  the two partition every schema's keys.
- **The steps in `do_import_steps` and `import_one_bundle` (`do_import.py`).** The
  namespace block is skipped on the build path, each part logging one debug line: the
  drop-old-import-tables step, the "Importing on top of previous import tables!" delete,
  the perm-delete block gated on `copy_import_to_permanent_tables or
  delete_permanent_import_bundles` (which reads `DISTINCT bundle_id` from the import
  `obs_general`, here the permanent table, and **would delete every bundle**),
  `create_tables_for_import(..., 'perm')`, `delete_duplicate_opus_id_from_perm_tables`,
  the copy, `copy_mult_from_import_to_permanent`, and the drop-new-import-tables step.
  **Added at the start of each bundle:** `delete_bundle_from_obs_tables(ctx, bundle_id,
  'perm')`, chunked by id range when the bundle is large, so a rerun is clean. The
  warning "Deleting bundles from perm tables but cart table not wiped" no longer arises
  on the fixture's golden path, so its `warning_whitelist.txt` entry is removed in this
  PR, per §1's whitelist rule.
- **Duplicate `opus_id`s across bundles** (Galileo SSI produces the same id from two
  bundles). The namespace path's snapshot `read_existing_import_opus_id`, which reads
  every permanent `opus_id` into a list once per index and tests it per row, is not
  taken. Instead, per chunk and **before any of the index's rows are loaded**, `SELECT id,
  opus_id FROM obs_general WHERE opus_id IN (...)`, a unique-key probe of the permanent
  table; for each hit, `delete_opus_id_from_obs_tables` (which deletes children by
  `opus_id` until PR-12) and re-import. The probe is always on, and
  `--import-check-duplicate-id` is accepted and redundant (PR-08 removes it).
  Cross-invocation duplicates keep today's outcome: the later import replaces the earlier
  copy. **The one behavior change, stated in the docs:** a duplicate within one
  invocation across two bundles, which today needs `--import-check-duplicate-id` and
  otherwise fails on the import table's unique key, is replaced without the flag.
- **Sibling connections.** `ImportDBSuper.open_sibling_connection()` returns a second
  instance sharing the configuration with `logger=None`; the `_enter`/`_exit` swap of
  `warnings.showwarning` is process-global and not thread-safe, so siblings do not log
  and the parent logs per table. `ImportDBSuper.build_indexes(table_to_statements, *,
  serial=False)` runs DDL for **different tables** concurrently across siblings, or
  serially when told, with errors collected and re-raised after the pool drains.
- **Finalization:** a new step `--create-permanent-indexes` in the `--cleanup-aux-tables`
  group, before `--analyze-permanent-tables` (which this PR also adds to the group; today
  `cli.main` sets only `create_param_info`, `create_partables`, `create_table_names`,
  `create_cart`, and `drop_cache_tables` for it). It is idempotent: it skips keys and
  constraints that exist, read from `information_schema.STATISTICS` and
  `REFERENTIAL_CONSTRAINTS` through the brand class, and **compares kind and ordered
  columns, never names**, because unnamed composite keys get server-assigned names
  (`time1_2`). It derives the key and foreign-key list from the schema through
  `add_secondary_indexes`, which **emits an explicit `KEY` for every foreign-key column
  that has no other index**, because the children's `obs_general_id` carries only
  `field_key: "foreign"` and would otherwise get its index built implicitly by the serial
  foreign-key phase, one table at a time. It builds them through `build_indexes` in this
  order: B-tree indexes concurrently across tables, grouped per table into `ALTER TABLE
  ... ADD INDEX ..., ADD INDEX ...` statements whose summed size estimate fits the space
  budget (so `obs_files` may take several `ALTER`s); then foreign keys **serially** under
  `foreign_key_checks = 0` (§1, Foreign keys); then `ANALYZE`. Before the first `ALTER`
  the step sets the session's `innodb_ddl_buffer_size` and `innodb_ddl_threads` when the
  server has them (capping concurrent `ALTER`s × `innodb_ddl_buffer_size` at a fraction of
  the buffer pool the PR names), and sets `innodb_tmpdir` **only** when the new optional
  key `[import] server_tmpdir` is given (it names a directory on the **database
  server's** host that `mysqld` can write; the client's `scratch_dir` is never used for
  it). **The space estimate** per index is `rows × (key bytes + primary key bytes + 10) ×
  1.3`, summed over the indexes building concurrently; when `server_tmpdir` is given and
  is a local path the step checks its free space, and the data directory's, against the
  sum and refuses with a message when short; otherwise it logs the estimate and proceeds.
  Each table's and each index's duration goes into `--timing-json`.
- **Validation:** `--validate-perm` gains an orphan anti-join count per child table
  (`LEFT JOIN obs_general ... WHERE obs_general.id IS NULL`), because finalization's
  foreign keys never validate existing rows; this is the direction #584 asks for.
- **Callers.** No script changes: `import_all`, `import_for_tests.sh`, and
  `build_run.perform_run` already import into an empty schema, so they take the build
  path. `duplicate_id_run`, which imports the same bundle twice in one invocation into an
  empty schema, now runs on the build path, where each bundle's delete and the probe give
  the same result; `reimport_bundle`, which imports into a finalized schema, stays on the
  namespace path until PR-08.
- **Changes:** `cli.py`, `do_import.py`, `do_import_tables.py`, `do_validate.py`,
  `importdb` (`super.py`, `mysql.py`); the `do_import.py` docstring (a failed build leaves
  a staged schema with no version row, which the web application refuses to serve and
  both deploy scripts refuse to promote); `dev_guide_import_running.rst` (how the target's
  state chooses the path), `dev_guide_import_steps.rst`, and `dev_guide_import_db.rst`
  (the keep set and the sibling connections).
- **Measurement:** full-scale import wall-clock end to end, `Innodb_data_written`, the
  `--create-permanent-indexes` step's wall-clock per table and per index, and the same
  step with `build_indexes(serial=True)` as a secondary. Target metric: full import
  wall-clock.
- **Acceptance:** §2.5; goldens unchanged (the golden serializer records tables, columns,
  and primary keys only, so this proves the data and not the keys); **a new
  `import_tests` check that the finalized schema carries exactly the keys and foreign
  keys the schema files declare**, derived from the schema JSON through the keep set and
  `add_secondary_indexes` and read back from `information_schema`, matched by kind and
  ordered columns; the whitelist change above; `--validate-perm` clean, including the
  orphan counts; `import_tests` tests that an interrupted finalization is refused and left
  untouched and that a second invocation into a build in progress keeps the first
  invocation's bundles. The cross-invocation probe is tested at unit level against a
  stubbed database (no fixture has two distinct bundles sharing an `opus_id`), unless the
  executor adds a second volume with a copied index as an overlay, in which case the
  end-to-end test is added too.
- **Scale:** full scale.

**PR-08: refactor: one write path: append to a finalized schema, and remove the import namespace** (item 6; `§D-3`)

- **The problem, as the code has it after PR-07.** A schema with a version row is still
  imported into through the import namespace: rows go to `imp_` copies of the tables,
  then the bundle is deleted from the permanent tables and copied in
  (`do_import.py`'s perm-delete block, `copy_bundle_from_import_to_permanent`,
  `copy_mult_from_import_to_permanent`, `delete_duplicate_opus_id_from_perm_tables`),
  governed by six flags: `--drop-old-import-tables`, `--delete-import-bundles`,
  `--leave-old-import-tables`, `--delete-permanent-import-bundles`,
  `--copy-import-to-permanent-tables`, and `--drop-new-import-tables`. It is the only
  remaining use of the namespace, and a failed run leaves the permanent tables untouched
  only because `do_import.py` returns before its delete and copy when
  `import_has_bad_data` is set.
- **The dispatch, completed.** PR-07's rule becomes:

  | Target schema | Path |
  |---|---|
  | No version row and no secondary indexes | build (PR-07) |
  | Version row matching `SCHEMA_VERSION`, `state = 'ready'` | **append** |
  | Version row matching, `state = 'appending'` | **resume the append** |
  | Version row with another version | refuse, naming both |
  | No version row but secondary indexes | refuse, naming scorched earth |

- **The append path.** It first sets `state = 'appending'`, so the web application serves
  503 and both deploy scripts refuse the schema until it finishes (PR-05's checks). Per
  bundle it runs `delete_bundle_from_obs_tables` and PR-07's duplicate probe, then loads
  through PR-04's loader into the permanent tables with their indexes and foreign keys
  in place, under `foreign_key_checks = 0` for the load (validation's orphan count is the
  check, as for the build). Then it re-runs every finalization step that declares itself
  invalidated by an append (§1, Append invalidation), and sets `state = 'ready'`. A
  failed append leaves `appending`; the next import resumes it, and because each bundle
  is deleted before it is written, rerunning the same bundles is clean.
  `--import-ignore-errors` now means: finish the build or the append, and write `ready`,
  even when bundles logged errors.
- **Outside the dispatch.** `--update-mult-info`, the aux and dictionary steps,
  `--delete-permanent-bundles`, `--cleanup-aux-tables`, scorched earth, and the deploy
  scripts' `opus_import` lines write no observation rows and run on any state, as today.
- **Removal.** The import namespace and everything that serves it:
  - the six flags; `--import`'s "implies `--delete-import-bundles`"; `--do-all-import`
    becomes an alias of `--import`, since every script and the harness use it;
    `--do-it-all` and `--do-import-finalization` expand without the removed flags;
  - `copy_bundle_from_import_to_permanent`, `copy_mult_from_import_to_permanent`,
    `delete_duplicate_opus_id_from_perm_tables`, `find_duplicate_opus_ids`,
    `read_existing_import_opus_id`, and `--import-check-duplicate-id`, which PR-07's probe
    replaces (it leaves `import_for_tests.sh` and `import_all.py`);
  - `import_prefix`, `convert_raw_to_namespace`, `_is_import_namespace`, PR-07's
    `direct` aliasing, and the `namespace` parameter across `ImportDBSuper` and the steps,
    including PR-04's `bulk_load_rows`; one namespace remains, and no later PR passes one;
  - `[import] table_temp_prefix`, under §1's configuration-key rule;
  - the namespace-only warnings and their whitelist entries.
- **Tests.** `reimport_bundle` and `duplicate_id_run` write the version row first and run
  on the append path. New `import_tests` cases: an append that replaces one bundle and
  adds one ends with goldens equal to a full build of the same bundle set; an append that
  fails in its second bundle leaves `appending`, the web check refuses the schema, and a
  rerun resumes and ends `ready`.
- **Docs:** `dev_guide_import_running.rst` (the state table, and the removed flags),
  `dev_guide_import_steps.rst`, `dev_guide_import_db.rst`, and `user_guide_deployment.rst`
  (adding bundles to a deployed database that is not being served).
- **Measurement:** the incremental group of `import_full.toml` (the largest bundle
  imported into the finalized full-scale schema), before on the namespace path and after
  on the append path; the change in lines of code, from `git diff --stat`, reported.
  Target metric: incremental group wall-clock.
- **Acceptance:** §2.5 with the structural criterion: no import namespace remains
  (`grep -rn "imp_\|'import'\|import_prefix\|table_temp_prefix" src/opus_import` finds
  only unrelated hits, each listed in the PR); goldens unchanged.
- **Requires full re-import:** no.
- **Scale:** full scale.

**PR-09: feat: parallel observation processing inside an import** (item 4; `§C-3.1`; `§C-3.2`; `§D-3`)

- **Design (from §1).** `import_one_index`'s per-row loop becomes a producer of row-range
  tasks and a consumer of `ChunkResult`s. The specifics, each of which decides whether
  the goldens pass:
  - **Pool.** `multiprocessing.get_context('fork').Pool(workers, initializer=...)`,
    explicitly `fork` on Linux and macOS (Python 3.14 changes the Linux default to
    `forkserver`, and `spawn`/`forkserver` would redo `Pds3File.preload(holdings)` in every
    worker); on Windows the pool is not available and `workers` is forced to 1 with a
    logged notice. `workers` comes from `[import] workers` (default `min(8, os.cpu_count()
    or 1)`; `1` means the in-process path with no pool). **The pool is created once per
    index** (a COCIRS bundle has several index tables, and `metadata` is per index),
    after the index's `metadata`, `vol_info`, `table_schemas`, and the parsed `args` have
    been installed in a module-level global the forked workers inherit; **nothing is
    pickled per task but a `(start, end)` row range**. **Small-index fallback:** when the
    index has fewer rows than `chunk_rows` the loop runs in-process as if `workers = 1`.
    The fixture's index tables are about twenty rows, so the fixture sessions set
    `chunk_rows = 5` (through `write_opus_config(extra_import=...)`) so that the pool path
    is what the goldens exercise.
  - **The inherited connection.** A forked worker inherits the parent's open MySQL socket.
    The initializer keeps a reference to the inherited `ImportDBSuper` instance and never
    closes it or lets it be collected (a driver connection's destructor sends `COM_QUIT`
    on the shared socket and kills the parent's session); the worker's own `ctx.db` is
    `None`. Pool workers exit by `os._exit`, so only the initializer matters, and the PR
    says so in a comment on the initializer.
  - **Chunk size.** `[import] chunk_rows`, default 500 index rows.
  - **What a worker computes.** For each index row in its range, exactly what the serial
    loop computes today for that row, through the same `import_observation_table` calls,
    with three substitutions: ids come from a chunk-local counter per table starting at
    zero (every `MAX_ID` column, every `OBS_GENERAL_ID` column, `obs_general_row['id']` as
    passed to `get_opus_products_rows_for_filespec`, and `obs_files.id`); mult columns
    hold the **value and its derived label** (the `.title()` rule stays in the worker),
    with `mult_list` columns holding the pre-JSON list of values; and every database call
    is absent. The `ChunkResult` is **one ordered event stream per observation, in row
    order**: each event either a row (phase, table, target for surface geometry, the row
    dict), a mult value to resolve (table, column, the full tuple), or a log record, in
    exactly the order the serial loop would have produced them, so that
    `update_mult_table`'s own log lines land between the same observation's records as
    they do today.
  - **What the parent does with each result**, consuming with `imap` so results arrive in
    index order, replaying the event stream in order: a **row** event has every
    chunk-local id rebased to the next real id from `ctx.max_table_id_cache` per table and
    every `obs_general_id` and `TAB:obs_general id` column rewritten to match; a **mult**
    event is resolved by calling `update_mult_table` with the full tuple, so mult ids are
    assigned in the order the serial run assigns them, and the id is written into
    the row it belongs to (`json.dumps` of the id list for `mult_list` columns, exactly as
    `do_import_obs` does today); a **log** event is replayed (below). After the
    observation's `obs_general` row is final, the parent rewrites every `obs_files` column
    whose `data_source` is `TAB:obs_general <col>` from it (`instrument_id` holds the
    resolved mult id today, which a worker cannot know). The parent runs
    PR-07's per-chunk duplicate probe and `delete_opus_id_from_obs_tables`,
    merges `used_targets`, and writes rows through PR-04's loader per table after the
    index.
  - **Logging.** A record is `(channel, level, nonrepeating, index_row_number,
    primary_filespec, message)`. Three channels are captured in the worker and replayed
    in the parent: `import_util.log_*` (the parent sets `ctx.current_index_row_number` and
    `ctx.current_primary_filespec` from the record and calls the same function, so the
    position prefix, the `nonrepeating_*` dedup, `ctx.import_has_bad_data`, and pdslogger's
    per-section limits behave as in the serial run); pdsfile's logger (the worker calls
    `Pds3File.set_logger` and the PDS4 equivalent with a recording logger, because the
    `NoDupLogger` the CLI installs writes into the parent's file handles, which forked
    workers inherit and would interleave); and `warnings.showwarning`, which the worker
    redirects into the same list. The import log of a parallel run is byte-identical to
    the serial run's except for timestamps; the warning whitelist is the test. Python 3.12+
    emits `DeprecationWarning` when forking a process with threads; the import has none
    before the pool, and the determinism test fails if one appears.
  - **Errors.** A field-function exception in a worker is a log event with the exception
    text, and the column becomes `None` and the row is still written, exactly as the
    serial loop behaves today; the `--import-ignore-errors` policy is applied by the parent
    where the serial loop applies it. A worker crash (the pool raises) aborts the index
    with a message naming the bundle, the index, and the row range.
  - **Database calls that must not run in a worker**, each with its disposition in the PR:
    `find_max_table_id` (parent, first touch per table, as today);
    `read_or_create_mult_table`'s `table_exists` and `read_rows` (parent, before the pool
    is created, for every mult table the index's schema names);
    `delete_opus_id_from_obs_tables` (parent); anything else `grep -rn
    "ctx\.db\|\.db\.\|do_import_tables\.\|find_max_table_id\|read_or_create_mult_table"
    src/opus_import/steps src/opus_import/obs src/opus_import/import_util.py` finds
    reachable from the loop. The worker's `ctx.db` is `None`, so a missed call fails
    loudly in the fixture suite rather than silently sharing a connection.
  - **Memory.** The forked workers share the parent's pages copy-on-write; refcount
    updates gradually copy them, so expect several times the serial RSS at eight workers.
    The harness records peak RSS of the tree and the PR reports it.
- **Determinism test:** `import_tests` imports one bundle with `workers = 1` and `workers =
  3` (both with `chunk_rows = 5`) into two schemas and asserts the dumped tables and the
  logs (timestamps stripped) are identical. The fixture suite's main run uses `workers =
  2, chunk_rows = 5` so the pool path is the golden path; the negative-case runs use
  `workers = 1`.
- **Measurement:** fixture and full scale, `--import` wall-clock for the largest bundle at
  `workers = 1, 2, 4, 8` (the harness takes a list and runs each), rows per second, peak
  RSS. **Expected shape:** the curve flattens when the parent saturates and the serial
  pre-phase (pdstable reads of the index and summaries) bounds the index by Amdahl; a flat
  curve past four to six workers is the ceiling, not a bug, and the PR says where the
  ceiling landed. Target metric: largest-bundle `--import` wall-clock at the default
  worker count against `workers = 1`.
- **Acceptance:** §2.5; goldens unchanged; the determinism test passes; the warning
  whitelist unchanged.
- **Scale:** full scale.

### Phase 3: the web application and the schema

Every PR in this phase that changes a table the import fills regenerates
`src/opus_app/apps/search/models.py` with `scripts/models/create_opus_models.sh`,
regenerates the import goldens with `python -m import_tests.tools.make_mini_goldens`,
bumps `SCHEMA_VERSION`, updates `docs/dev_guide_database_schema.rst` and
`dev_guide_table_schemas.rst`, and is marked **requires full re-import**. A change to a
table the import only truncates (PR-11) regenerates the models but needs neither the
bump nor the re-import (§1, Deploy).

**PR-10: refactor: paging by sort-order range** (item 13, the per-page half; `§C-4.1`; `§D-2.4`)

- **Changes:** `get_search_results_chunk` replaces `CREATE TEMPORARY TABLE temp_... AS
  SELECT ... LIMIT/OFFSET` plus `INNER JOIN` with a `WHERE <cache>.sort_order BETWEEN %s
  AND %s` predicate on the join to the cache table. `sort_order` is dense (a single
  `AUTO_INCREMENT` insert into a fresh table today; `ROW_NUMBER()` after PR-11), so the
  range is exact and the engine reads only the page's entries. `cart/views.py`'s
  `_edit_cart_range` builds the same kind of temporary table from the cart to resolve a
  range; it moves to the same predicate over a `ROW_NUMBER()` derived table of the cart,
  and `create_table_as_select` (whose only callers are these two temporary ones) goes;
  `create_table_from_select_sql`, the non-temporary path `get_user_query_table` uses,
  stays until PR-11.
- **Measurement:** warm and app-cold latency of the page scenarios, first, tenth, and
  last; the statement digests (the temporary-table digest should vanish). Target metric:
  warm latency of the last page.
- **Acceptance:** §2.5; API goldens unchanged; the cross-session `removerange` tests in
  `integration_tests/test_api/test_cart_api.py` (run by the self-hosted integration
  workflow) still pass.
- **Scale:** full scale.

**PR-11: feat: one search_results table replaces the per-search cache tables** (item 13, the `search_results` half; `§C-4.1`; `§C-2.6`; `§D-2.4`; closes #350, #665, #1500)

- **Issues:** #350 asks for a least-recently-used cleanup of old search and cart data;
  after this PR no per-search table exists, and the pruner below removes old searches,
  expired sessions, and their carts. #665 asks for the count
  without the table build; the count is stored at build time and read from
  `user_searches` afterward, while the first request still waits for the build (the
  background build it proposes is not adopted). #666 proposes `READ UNCOMMITTED` for the
  build; not adopted, the build runs at the default isolation level and the concurrent
  cold measurement reports its lock cost. #1500 (the search cache key can exceed
  memcached's limit) is fixed here: the search's key becomes its fixed-width hash, and
  `get_string_search_choices`'s key, assembled the same way, is hashed to a fixed width.
- **Changes:**
  - A permanent, **unpartitioned** table `search_results(search_id INT UNSIGNED NOT NULL,
    sort_order INT UNSIGNED NOT NULL, obs_general_id INT UNSIGNED NOT NULL, PRIMARY KEY
    (search_id, sort_order))` with a schema file whose key is the table-level entry
    `{"primary_key": ["search_id", "sort_order"]}`, introduced in this PR (§1, Schema
    entries), created by `reset_search_tables` (below). **No secondary key:** paging,
    counts, the fan-out, and cart ranges all read a search by position, so a second
    `(search_id, obs_general_id)` key would grow every row and every build for no reader;
    the measurement below reports the table's bytes per million rows. The build guarantees
    uniqueness itself by selecting each `obs_general.id` once, which a test asserts on a
    broad build with joined categories, and the executor confirms with `EXPLAIN` that
    every fan-out query reads `search_results` by its primary key. If a plan turns out to
    need the second key, the executor stops and reports rather than adding it.
    Partitioning is not used: `search_id` is the primary-key prefix, so every per-search
    read is one range regardless, and the only reason to partition would be O(1) removal
    of stale searches, and the pruner below does that with chunked deletes.
  - **`user_searches` is rebuilt to what it is used for**: `id`, `search_hash BINARY(32)
    NOT NULL` with a unique key, `result_count INT UNSIGNED NULL`, `results_built_at
    DATETIME NULL`, and `last_used_at` (the pruner, below). The four `*_json` columns
    (written, read by nothing), the four `*_hash` columns with their `'NONE'` sentinels
    and four-column unique constraint, and `timestamp` go. `set_user_search_number` keeps
    building exactly the four strings it hashes today and computes `search_hash` as the
    SHA-256 of `json.dumps([selections_json, qtypes_json, units_json, order_json])`, with
    `None` where today's code writes `'NONE'`, so two requests share a row exactly when
    today's four hashes are equal; a unit test pins that over a table of request pairs,
    including absent and empty query types and units. The optimistic insert and its
    `IntegrityError` read-back stay; the unreachable `MultipleObjectsReturned` handler
    goes. The memcached key for the search's id is
    `CACHE_SERVER_PREFIX + CACHE_KEY_PREFIX + ':usersearchno:' + search_hash.hex()`,
    and a test asserts its length under the test configuration. The model field is a `BinaryField`, as `inspectdb` generates it.
  - **The pruner, for #350.** `user_searches` gains `last_used_at DATETIME NOT NULL`,
    set at registration. It is refreshed at most once a day per search, so it adds no
    write per request: the memcached entry for a search holds its id and the day it was
    last stamped, and a hit on a later day issues one `UPDATE user_searches SET
    last_used_at = NOW() WHERE id = %s` and rewrites the entry. A new management command,
    `opus_manage prune --unused-days N` (default 30), then removes, in this order:
    1. **Searches not used in N days.** For each, the `user_searches` row is deleted
       first, so a request that arrives meanwhile registers the search afresh under a new
       id; then its hash-keyed memcached entry; then its `search_results` rows, in chunks
       of 100,000 by `search_id`. Ids are never reused within a schema, so the other cache
       entries keyed by a pruned id are unreachable and age out without a flush. A cached
       id whose `user_searches` row is missing is treated as a cache miss.
    2. **Expired sessions**, through Django's own `clearsessions`.
    3. **Cart rows whose session no longer exists**, with `DELETE c FROM cart AS c LEFT
       JOIN django_session AS s ON s.session_key = c.session_id WHERE s.session_key IS
       NULL`.
    The command logs each count. Deleting rows does not shrink the tablespace, but InnoDB
    reuses the freed pages, so a regular prune bounds the table's size. The operator
    schedules it; `docs/user_guide_deployment.rst` gives a cron line, and nothing in the
    deploy scripts runs it. The landing page and other searches in daily use are never
    pruned, because their stamps stay current.
  - `do_django.drop_cache_tables` becomes `reset_search_tables`: **drop and re-create
    `user_searches` and `search_results` from their schema files**, through the brand class. It
    keeps `drop_cache_tables`'s place in the `--cleanup-aux-tables` set, so it runs as
    part of the closing step of every sequence (`import_all`, `import_for_tests.sh`, the
    deploy scripts), and a search built during an import does not outlive it; this PR
    adds it to `deploy_new_code_only.sh`, so a code-only release re-creates both tables
    in their new shape. The harness's state resets
    call the same function through the CLI
    (`--drop-cache-tables` keeps its name as an alias). `create_opus_models.sh`'s refusal
    on `cache_*` tables goes with the tables.
  - `get_user_query_table` is renamed `get_search_id` and returns `int | None`. Every
    consumer that took a table name (`search_cache_join_condition`, `add_from`,
    `count_rows`, `column('sort_order', name)` in the cart, the Django cache keys built
    from the name) takes the id, and `sql_builder.search_results_source(search_id)`
    renders the filtered source (`search_results` with `WHERE search_id = %s`) for joins.
    `get_search_results_chunk`'s `BETWEEN` from PR-10 applies to `sort_order` of that
    source.
  - **The build.** Inside one `transaction.atomic()`, with the session's
    `innodb_lock_wait_timeout` set to `[django] search_build_timeout` (default 300
    seconds, longer than a broad cold build): `SELECT results_built_at FROM user_searches
    WHERE id = %s FOR UPDATE`. The row lock is the serialization point: a second builder
    blocks on the same statement until the first commits, then reads the committed
    `results_built_at` and returns. If it is set, return; else `INSERT INTO search_results
    (search_id, sort_order, obs_general_id) SELECT %s, ROW_NUMBER() OVER (ORDER BY ...),
    obs_general.id FROM ...`, take `cursor.rowcount` as `result_count`, write both columns,
    commit (which releases the lock). A lock wait that times out raises; `tools/db_utils`
    gains `is_lock_timeout_error(exc)` (MySQL error 1205), the one place that reads the
    driver's error code, and the caller returns `None` so it reaches
    `http500_search_cache_failed`. No named server lock is used: a row lock is
    transaction-scoped, so a worker that dies releases it with its rollback, it needs no
    `finally`, it is the same statement on both brands (PostgreSQL note: `FOR UPDATE` with
    `SET LOCAL lock_timeout`), and it works through any connection pooling.
  - **Every reset of the two tables is followed by a cache flush** (the cache trusts its
    entries: a hash-to-id or id-to-count entry that outlives a truncate would hand one
    search's rows to another once ids restart). Nothing in the import flushes the cache
    today; `reset_search_tables` gains, after the truncate, a subprocess
    `[sys.executable, '-m', 'opus_app.clear_django_cache']` (it needs only
    `OPUS_CONFIG`, which the import has), and a nonzero exit fails the step. With the
    local-memory fallback the subprocess clears nothing that serves, and the worker
    restart that follows every import is the flush, as today. The deploy also restarts
    the cache service in `_promote.sh`; the harness's state resets restart the memcached
    it owns. `dev_guide_import_steps.rst` says that an import into a served schema
    flushes the site's cache.
  - `get_result_count_helper` and **`api_string_search_choices`** read
    `user_searches.result_count` (the latter issues its own `count_rows` today; that call
    goes, and PR-21 relies on it being gone). `create_table_from_select_sql` and
    `CACHE_TABLE_COLUMN_DEFS` have no caller and go.
  - `dev_guide_database_schema.rst` and `dev_guide_webapp_search.rst` describe the table,
    the build, and the row lock.
- **Cost model, stated so the right metric is judged:** the build's dominant cost is the
  same sort plus the same number of inserts, now into a shared table with no secondary
  index; expect the cold build itself no faster. The gains are:
  no DDL in the request path and no table-cache churn, a bounded table count, the stored
  count (which removes a `COUNT(*)` from the result-count and autocomplete paths), and one
  build per search under concurrency. Whether distinct new searches serialized on anything
  before this PR is **not asserted**; the concurrency scenario measures it.
- **Measurement:** the concurrency scenario in all three states, cold latency of every
  search scenario (reported, not judged), the digests, and the table count after the web
  scenarios (constant), the bytes of `search_results` per million rows, and the time to
  prune a thousand planted searches (reported). Target metric: **p95 under 16 users,
  app-cold, distinct searches**, with the shared-search half as the secondary.
- **Acceptance:** §2.5; API goldens unchanged; a test that issues the same new search from
  two threads and asserts one build and two identical counts; a test that an exception
  inside the build rolls back and leaves the row unbuilt; a pruner test with planted
  searches, sessions, and carts (an old search and its rows and cache entry gone, a
  recent one kept, a cached id of a pruned search re-registering, an expired session
  and its cart rows gone, a live one kept); the harness's state resets updated to
  `reset_search_tables`.
- **Requires full re-import:** no; `SCHEMA_VERSION` is unchanged, since neither table is
  filled by the import (§1, Deploy).
- **Scale:** full scale.

**PR-12: refactor: key the child tables on obs_general_id, and prune obs_files** (item 8; `§C-2.1`; `§D-2.2`)

- **Changes:**
  - In every per-category `obs_*` schema except `obs_general`, `obs_files`,
    `obs_surface_geometry_name`, and the surface geometry template: `obs_general_id`
    becomes the primary key (`field_key: "primary"`) and its foreign key moves to a
    table-level entry `{"foreign_key": {"columns": ["obs_general_id"], "references":
    ["obs_general", "id"]}}` (§1, Schema entries; a column carries one `field_key`, which
    `mysql.py` asserts); the `id`, `opus_id`, and `instrument_id` columns and their keys
    go, **except `obs_pds.opus_id`**, which carries `pi_slug: "opusid"`, the public
    `opusid` field every result page shows and a STRING autocomplete column: it stays as a
    plain column with no foreign key and a plain key. **`bundle_id` goes the same way**,
    except `obs_pds.bundle_id`, the public `bundleid` field (`pi_slug: "bundleid"`),
    which stays as a plain keyed column; `obs_general.bundle_id` and its key stay.
    `--validate-perm` counts `obs_pds` rows whose `bundle_id` differs from their
    `obs_general` row's.
  - **The per-bundle steps join the hub.** `delete_bundle_from_obs_tables` deletes from
    each child with `DELETE c FROM <t> AS c JOIN obs_general AS g ON g.id =
    c.obs_general_id WHERE g.bundle_id = %s`, rendered by the brand class, still
    children first and `obs_general` last. PR-07's
    create-time keep set then holds only `obs_general`'s `bundle_id` key. The chunking of
    a large bundle's delete ranges over the bundle's `obs_general.id` values. A test in
    `tests/opus_import` asserts the rendered statements, and `reimport_bundle` covers
    the behavior.
  - `obs_surface_geometry_name` and the surface geometry template are left to PR-15.
  - `obs_files` keeps `id` (many rows per observation), `obs_general_id`, `opus_id`
    (`tools/file_utils.py` reads it by `opus_id IN (...)`), and `instrument_id` (PR-09's
    parent fills it from the finalized `obs_general` row); its non-key secondary indexes
    are reduced to the columns the application filters or sorts on, found by reading every
    `ObsFiles` query in `opus_app` (`grep -rn "ObsFiles\|obs_files" src/opus_app
    --include=*.py`) and listed in the PR with the query that needs each; a composite
    `(opus_id, short_name, version_name)` is considered for the `file_utils` read; the
    rest go.
  - Application touch points, found by `grep -rn "\.id\b\|opus_id" src/opus_app
    --include=*.py` over **all of `src/opus_app`**: `tools/db_utils.query_table_for_opus_id`
    already filters children through `obs_general__opus_id` and needs no change;
    `api_get_categories_for_opus_id` reads `.values('opus_id')` from its results and reads
    `obs_general` instead; `search_cache_join_condition` and `add_obs_table_joins` join on
    the new key; the regenerated `models.py` and mypy are the backstop.
    `create_opus_models.sh`'s `sed` rules are updated for the `OneToOneField(...,
    primary_key=True)` that `inspectdb` emits for a primary key that is a foreign key
    (and must not touch PR-15's composite key later).
  - Import touch points: `delete_opus_id_from_obs_tables` (deletes children by
    `obs_general_id` resolved from `obs_general`), `do_validate.validate_min_max_order`
    (selects `opus_id` from child tables; joins instead), the row id assignment for
    children ("the parent's id"), `golden_io.SURROGATE_ID_COLUMNS`,
    `dev_guide_database_schema.rst`.
- **Measurement:** schema size, cold and warm latency of every search scenario and of the
  page scenarios, the plan of the cache build (each child join a unique lookup on the
  primary key), full-scale import wall-clock. Target metric: app-cold broad-search
  latency, with schema size as the secondary.
- **Acceptance:** §2.5; API goldens unchanged (the `opusid` column and its autocomplete
  are the ones to watch); import goldens differ only by the removed columns and indexes,
  shown in the PR.
- **Requires full re-import:** yes.
- **Scale:** full scale.

**PR-13: feat: composite indexes in the table schemas** (item 10, first half; `§C-2.2`; `§D-2.1`, `§D-2.2`)

- **Changes:** the table-level entry `{"key": ["col1", "col2", ...]}` (§1, Schema
  entries); `create_table` renders it as `KEY (col1, col2)`, PR-07's
  `add_secondary_indexes` derives it like any other key, and every reader that iterates a
  schema's columns skips it as it skips `constraint` (the executor greps for
  `'field_name'` reads and confirms each tolerates the entry). A column's own `field_key`
  is untouched, so `time1` keeps its single index and every autocomplete column keeps its
  B-tree. The dev guide describes the form; no validator exists today and none is written.
  Add `{"key": ["time1", "opus_id"]}` to `obs_general` (the default sort; with the primary
  key appended it covers `SELECT id ... ORDER BY time1, opus_id`); `{"key": ["right_asc",
  "d_right_asc"]}` and the `(declination1, declination2)` pair on `obs_general`; and the
  ring-geometry longitude pairs on `obs_ring_geometry` (every pair `(<col>, d_<col>)`
  where both are columns of `obs_ring_geometry.json`; `longitude_wrt_observer` is one).
  **The angular pairs cannot be range-scanned:** `get_longitude_query` renders
  `ABS(MOD(%s - col + 540., 360.) - 180.) <= %s` through `sql_builder.angular_separation`,
  so their value is a narrower covering scan than the clustered row. **Add only; prune
  nothing** (§1). PostgreSQL note: `INCLUDE (id)` and `NULLS FIRST`, and a `VACUUM` after
  load for index-only scans.
- **Measurement:** the plan of the empty-search build before and after; the acceptance
  shape is **a covering index scan with the sort in memory** (`Sort_merge_passes` zero
  for the statement), not the disappearance of the sort iterator, because MySQL probably
  still sorts for `ROW_NUMBER()` even when an index supplies the order; if the sort spills,
  the PR reports the `sort_buffer_size` that would hold it. The plan and latency of the
  **selective** default-sort search (MySQL may choose the ordered index walk over
  filter-then-sort and regress it; if it does, the PR reports it and the orchestrator
  decides between an optimizer hint in `sql_builder` and dropping the index), app-cold
  latency of the broad default-sort search and its last page, schema index size. Target
  metric: app-cold empty-search latency.
- **Acceptance:** §2.5; no regression on the selective shape beyond noise.
- **Requires full re-import:** yes.
- **Scale:** full scale.

**PR-14: refactor: one mult table, with a computed display rank** (item 21; `§C-2.6`; `§D-2.8`)

- **The problem, as the code has it.** Every enumerated column has its own
  `mult_<table>_<column>` table, all of one shape (`table_schemas/mult_template.json`),
  each a Django model (`grep -c '^class Mult' src/opus_app/apps/search/models.py`), each
  found by spelling its name (`import_util.table_name_mult`, `app_utils.get_mult_name`,
  `apps.get_model('search', ...)`). Two columns are dead: nothing reads `aliases`, no
  observation class supplies one (`obs/field_types.py` says so), and the generated models
  omit it; nothing reads `timestamp`. `group_disp_order` describes a group but is stored on
  every row of it, and the widget's `distinct().values('grouping')` ordered by it lists a
  group twice when its rows disagree. `disp_order` is a string key that
  `do_import_mult.update_mult_table` computes once, when a value is first seen, from the
  values already present, so the bundle order changes it; negative numbers sort wrongly
  under both of its padded formats; the widget sorts it in SQL under the column's
  case-insensitive collation while `api_get_mult_counts` sorts it in Python
  case-sensitively; ties have no tiebreaker; positions are forced with `zzz`, `zzy`, `zzx`,
  `zzAYes`, and `zzBNo` prefixes and one `'!Cassini'` (`obs/obs_volume_corss_8xxx.py`); and
  the absent-value rule is skipped for a column with a unit. A bundle delete never deletes
  mult rows, so the search form keeps offering a value no observation has, and a value that
  already exists keeps its first label when a later import computes another. Every mult id
  is `int unsigned` in every observation column.
- **Changes:**
  - **Schema.** Three tables replace the template and its ninety tables, with schema files
    `mult_field.json`, `mult_group.json`, and `mult.json` using PR-11's table-level
    `primary_key` entry and a `{"unique": [cols]}` entry introduced here (§1, Schema
    entries):
    `mult_field(field_id SMALLINT UNSIGNED PRIMARY KEY, qualified_name VARCHAR(100) NOT
    NULL UNIQUE, pinned TINYINT NOT NULL)`, where `pinned` is 1 for a column with
    `mult_options`; `mult_group(field_id, grouping VARCHAR(100) NOT NULL, group_rank
    SMALLINT UNSIGNED NOT NULL, PRIMARY KEY (field_id, grouping))`; and `mult(field_id
    SMALLINT UNSIGNED NOT NULL, id SMALLINT UNSIGNED NOT NULL, value VARCHAR(100) NULL,
    label VARCHAR(100) NOT NULL, disp_rank SMALLINT UNSIGNED NOT NULL, display
    ENUM('Y','N') NOT NULL, grouping VARCHAR(100) NULL, PRIMARY KEY (field_id, id), UNIQUE
    KEY (field_id, value))`. On a fresh schema `field_id` is assigned in sorted
    qualified-name order; a field added later takes the next id. Ids stay per field, so the
    values in the observation columns are today's.
  - **Id width.** `mult.id` and every `mult_idx`, `flag_yesno`, and `flag_onoff` column,
    including `obs_surface_geometry_name.target_name` and the per-target tables', become
    `SMALLINT UNSIGNED` **if** the full-scale `bench_db` of this PR's merge-base shows no
    mult table whose `MAX(id)` exceeds 32,767; otherwise they stay `INT UNSIGNED` and the
    PR says so. PR-15 gives its one table's `target_name` this width. Either way
    the import refuses, with a fatal error naming the field, to assign an id above the
    type's maximum.
  - **Import.** `do_import_mult` reads and writes `mult` rows by `field_id`;
    `table_name_mult` becomes `mult_field_name(table, column, schema_entry)`, returning
    the qualified name unless the column declares a `mult_field` key (PR-15 uses it), and
    its callers in `do_import_mult` and `do_import_tables` pass the entry.
    `update_mult_table` computes no order: it stores the value, label, display, grouping,
    and an optional integer **pin**. When a value exists and the incoming label, display,
    or grouping differs, the stored row stays and a nonrepeating warning names the field,
    the value, and both labels; if the fixture's golden path emits it, the PR lists each
    case and the orchestrator rules once (fix the observation class, or whitelist). The
    `disp_order` and `group_disp_order` arguments become `pin` and `group_pin`; the only
    explicit caller, `obs_volume_corss_8xxx.py`, passes `pin=0`. The `aliases` and
    `tooltip` keys leave the field shape in `obs/field_types.py` and `_create_mult`. The 55
    `mult_options` lists (`grep -l mult_options src/opus_import/table_schemas/*.json`)
    state their order element as an integer (`'010'` becomes `10`), rewritten once by a
    script committed with the PR, and the reader rejects a string.
  - **Finalization**, a new `finalize_mult` step, **invalidated by an append** (§1), in
    PR-07's finalization after the B-tree
    builds (so each `SELECT DISTINCT` reads an index) and before `ANALYZE`:
    1. In every field whose `pinned` is 0, delete the `mult` rows whose id no observation
       references: `SELECT DISTINCT <column>` over the column that holds the field (for
       `obs_surface_geometry_name.target_name`, `obs_surface_geometry_target.target_name`;
       for the two `mult_list` columns, a `JSON_TABLE` over the list until PR-19 switches
       it to the junction tables). A pinned field keeps every row, since its list is the
       intended set of choices. Groups left empty are deleted.
    2. Recompute `disp_rank` for every field, dense from 1, by sorting on a tuple: the
       tier (pinned values in pin order; then ordinary values; then `Yes` and `On`; then
       `No` and `Off`; then `None`, `N/A`, and `NULL`, in that order, with or without a
       unit); then, among ordinary values, the number (through the column's unit parser
       when it has a unit, otherwise `float`) when every ordinary value of the field parses,
       otherwise the case-folded label; then the label; then the stored value.
    3. Recompute `group_rank` the same way from the group pin and the case-folded group name.
    `--update-mult-info` writes the pinned presentation and the overrides below, then
    recomputes the ranks of the fields it touched.
  - **Renaming without a re-import.** A column's schema entry may carry `mult_overrides`,
    a list of objects `{"value": ..., "label": ..., "display": ..., "grouping": ...,
    "pin": ...}` in which only `value` is required. Finalization applies them after
    the import's rows and before the ranks, so an override always wins over a stored
    or computed label; a value the field does not hold is reported and skipped. The
    conflict warning above names `mult_overrides` as the remedy. `do_update_mult_info`
    applies `mult_options` and `mult_overrides` alike, and `deploy_new_code_only.sh`
    adds `--update-mult-info` to its `opus_import` line, so a rename is a release that
    edits a schema file followed by a code-only deploy: the mult rows change in place
    in the served schema, the aux tables are swapped in by PR-06's swap, and
    `_promote.sh`'s restarts of the
    cache service and the web service make it visible. Ids never change, so no
    observation row is touched. `docs/user_guide_deployment.rst` documents the
    procedure. An `import_tests` case renames one value on a built schema through
    `--update-mult-info` and asserts the new label, the unchanged id, and the
    recomputed rank.
  - **Application.** One `Mult` model, with `MultField` and `MultGroup`, using Django's
    `CompositePrimaryKey`, replaces the ninety classes (`create_opus_models.sh`
    regenerates them; `inspectdb` under Django 5.2 emits `CompositePrimaryKey` for a
    composite key, this is the plan's first such model, and the executor confirms that
    the generated classes import and that the script's `Mult*` keep rule still matches
    them). PR-03's caches key on
    `field_id`. Every site that resolves a mult model or table (the executor lists them
    with `grep -rn "get_mult_name\|get_model('search', mult\|mult_param.title\|mult_name.title" src/opus_app --include=*.py`)
    resolves the field id instead. A label join is
    `sql_builder.mult_join(alias, field_id, column)`, rendering `LEFT JOIN mult AS <alias>
    ON <alias>.field_id = %s AND <alias>.id = <column>`. The widget and the counts order
    by `disp_rank`, the counts sorting by the integer in Python; the widget orders groups
    by `mult_group.group_rank`. **Search results sorted by a mult column keep sorting by
    `label` text**: `create_order_by_terms` orders by the label through the alias, and a
    test pins that order for a mult column whose label order and rank order differ.
  - **Docs:** the mult section of `dev_guide_database_schema.rst`, the mult resolution in
    `dev_guide_import_steps.rst`, and `docs/_ext/opus_field_tables.py` if it reads mult
    tables.
  - **Tests:** unit tests of the rank function in `tests/opus_import` (two insertion orders
    give the same ranks; negative numbers; mixed case; ties; Yes and No; the absent values
    with and without a unit; pins), and an `import_tests` case on `reimport_bundle`: a
    value only the replaced bundle used is gone afterward, and a pinned value with no
    observations stays.
- **Measurement:** data bytes of the observation tables and the mult tables, and the table
  count, before and after; app-cold latency of the mult count scenario and of a widget
  menu. Target metric: app-cold latency of the MULTIGROUP mult count.
- **Acceptance:** §2.5. The import goldens are regenerated once, the diff being tables only.
  An `api/mults` response may change order only where the rank corrects a case named in
  this PR's problem statement; the executor lists every changed golden with its reason in
  one batch and the orchestrator rules once. Goldens of results sorted by a mult column
  are unchanged.
- **Requires full re-import:** yes.
- **Scale:** full scale.
- **PostgreSQL note:** the same tables; `ENUM('Y','N')` becomes `CHAR(1)` with a `CHECK`.

**PR-15: refactor: one surface geometry table, with the targets as data** (item 11; `§C-2.3`; `§D-2.3`; closes #334)

- **Issues:** #334 asks for this table and names its two difficulties, the `partables`
  rows and the selector widget's name; both are handled below. #651 (choosing a surface
  geometry target in Select Metadata) becomes a user-interface change alone once every
  target's categories exist as data.

- **The problem, as the code has it.** Surface geometry is one table per target body,
  created from the template `table_schemas/obs_surface_geometry_target.json` at the end of
  each index's write loop in `import_one_index`, once the index's targets are known. The
  committed `models.py` holds 101 of
  them (`grep -c "db_table = 'obs_surface_geometry__" src/opus_app/apps/search/models.py`),
  each a Django model class, most of the file's lines (`wc -l` gives 12,093), regenerated
  by `inspectdb` against a populated database. `table_model_from_name` raises
  `LookupError` for a target the deployed file has never seen;
  `api_get_categories_for_opus_id` swallows it and omits the category, while
  `get_metadata` and `api_get_range_endpoints` return 500, until someone regenerates the
  file and redeploys. `param_info` carries one row per target per column, `table_names`
  one row per target, `partables` one trigger per target, all derived by listing the
  tables; `do_validate.validate_nulls` skips the tables because they come from one
  template, so a column that is full for one target says nothing about the template;
  `do_update_mult_info` tries several splits
  to find which table a mult name belongs to; `docs/_ext/opus_field_tables.py` expands the
  template to document the categories. The per-target categories are **public**:
  `api/categories` returns `obs_surface_geometry__saturn` as a category's `table_name`,
  and every surface geometry slug is `SURFACEGEO<target>_<field>`. The selector field
  `surfacegeometrytargetname` has the qualified name `obs_surface_geometry_name.target_name`,
  which is hard-coded in `search/forms.py` (it selects the radio widget), in
  `get_triggered_tables`'s trigger branch, and in `app_utils.get_mult_name` (which
  resolves the mult field from it, PR-14); `settings.BASE_TABLES`
  lists `obs_surface_geometry_name`; `ui/views.py` folds its fields under the
  `obs_surface_geometry` heading; `results/views.py` skips it as "not a data table".
  **Every one of these names stays.**
- **The design.** One physical table and one model; every category, including the
  selector's, becomes rows that point at it.
  - **Table.** `obs_surface_geometry_target(target_name <PR-14's mult id width> NOT NULL,
    obs_general_id INT UNSIGNED NOT NULL, <every geometry column of the template>)`
    with the table-level entry `{"primary_key": ["target_name", "obs_general_id"]}`
    (PR-11's form) and `{"key": ["obs_general_id"]}`; the template's `bundle_id` goes
    by PR-12's rule. **Target first**: one target's
    rows are then contiguous in the clustered index, as they are in today's per-target
    tables, so a two-column range search (`X1 <= max AND X2 >= min`) that uses a
    `(target_name, X1)` index and probes the clustered row for `X2` touches the same pages
    it does today; observation-first would interleave each observation's several targets
    and multiply the cold page reads by the mean number of targets per observation. The
    alias join below is still a unique lookup (both key parts given), and the
    per-observation category lookup is a covering dive on the secondary key, which also
    serves the foreign key (added in finalization) and the per-observation delete.
    `target_name` holds the target's id within the mult field
    **`obs_surface_geometry_name.target_name`**, the field the selector uses; the column
    declares it with PR-14's `mult_field` key, because the column's own qualified name
    would name a different field. Composite
    `{"key": ["target_name", "<col>"]}` entries replace the template's per-column
    `field_key: true`, one per keyed column, so a per-target range search is one index
    range; the executor may add `{"key": ["target_name", "<X1>", "<X2>"]}` for the searched
    pairs within InnoDB's 64-index cap (the template has 55 keyed columns:
    `grep -c '"field_key": true' src/opus_import/table_schemas/obs_surface_geometry_target.json`)
    and reports
    which. `opus_id` and `instrument_id` are dropped from the table (PR-12's rule); the
    obs module's methods for them go. **It absorbs `obs_surface_geometry_name`**, whose
    only content is the target. `obs_surface_geometry` (the per-observation `target_list`
    text) keeps its shape. The template keeps its name and its `<TARGET>`/`<SLUGTARGET>`
    placeholders in `pi_category_name`, `pi_slug`, and `pi_old_slug`, which are now
    expanded **per category row** rather than per table.
  - **Categories as data.** `table_names` gains two columns, `physical_table CHAR(60)
    NULL` and `target_name` (PR-14's mult id width) `NULL`: both `NULL` for every category
    that is its own table; `physical_table = 'obs_surface_geometry_target'` with the
    target's mult id for each `obs_surface_geometry__<target>` category; and
    `physical_table = 'obs_surface_geometry_target'` with `NULL` target for the
    **`obs_surface_geometry_name` category**, whose one `param_info` row stays
    `obs_surface_geometry_name.target_name` (`surfacegeometrytargetname`) so the widget,
    the trigger branch, `get_mult_name`, `BASE_TABLES`, the menu folding, and the "not a
    data table" skips are untouched. `partables` keeps `trigger_tab =
    'obs_surface_geometry_name'`, `trigger_col = 'target_name'`, `trigger_val = <decoded
    name upper>`, `partable = <category>`. `do_table_names`, `do_param_info`, and
    `do_partables` derive the target list from **`SELECT DISTINCT target_name FROM
    obs_surface_geometry_target`** (the data, not the mult rows, which still hold the
    values of deleted and failed bundles until PR-14's finalization step removes them),
    and produce **byte-identical** rows: labels `decode_target_name(encoded).title() + '
    Surface Geometry Constraints'` (not the mult label), categories ordered by encoded
    name, `param_info` rows in today's order (the alphabetical table order, where
    `obs_surface_geometry__*` sorts before `obs_surface_geometry_name`; this matters for
    the `param_info` import golden, which is serialized in primary-key order; `api/fields`
    sorts its own output and does not depend on it), slugs from `slug_name_for_sfc_target`
    as today (the JS `getSurfacegeoTargetSlug` mirrors it and is unchanged).
    `build_table_names_rows` emits the `obs_surface_geometry_name` row on the existence of
    the **physical** table (today it tests the table it is named for). The spelling
    functions stay in `import_util`; the application never re-encodes a name, because
    `table_names` carries the id.
  - **Unknown targets and collisions.** A target not in `TARGET_NAME_INFO` is a NULL mult
    today, or `OTHER` under `--import-ignore-errors`, while its table was named from the
    raw name; and two raw names in one observation that `TARGET_NAME_MAPPING` folds onto
    the same body are legal today because each per-target table has its own `id`. Rule: a
    row whose resolved target is NULL is **not written** to the one table (the observation
    keeps its `obs_general` row, as today when the bundle is rejected), and **any two rows
    of one observation that resolve to the same `target_name`** (two unknown bodies under
    `--import-ignore-errors`, or two spellings of one body; today the second insert fails
    on a duplicate `id`) write **one** row, the first in the order the loop visits them
    (sorted raw names for the summary-file path, file order for the inline path), with a
    nonrepeating warning naming the observation and both raw names; the fixture gains no
    such case, and the rule is unit-tested in `tests/opus_import`.
  - **Rows are computed under the category name and written to the physical table.**
    `do_import_obs.py` dispatches the geometry-mismatch validation and
    `field_function_name` on `table_name.startswith('obs_surface_geometry__')`, and
    `obs/obs_surface_geometry_target.py` derives the target from the table name it is
    given; the import keeps passing the category name (`obs_surface_geometry__<target>`)
    through that path and maps it to the one physical table only at the write.
  - **Resolution in the application.** One function, `tools/db_utils.resolve_category(name)
    -> ResolvedCategory(model, table, alias, target_name | None)`, built once per process
    from `TableNames` (through PR-03's caches). **Every site that uses a category as a
    `FROM` source, a join, or a model goes through it**, regenerated by
    `grep -rn "category_name\|get_model('search'\|add_from(\|add_join(\|table_model_from_name" src/opus_app --include=*.py`:
    `add_obs_table_joins` (`LEFT JOIN obs_surface_geometry_target AS
    obs_surface_geometry__saturn ON obs_general.id = alias.obs_general_id AND
    alias.target_name = %s`, so every `sql_builder.column(pi.name, pi.category_name)` in
    `construct_query_string`, `create_order_by_terms`, and the results column select is
    already correct, and a search naming two targets joins the table twice under two
    aliases as two tables did); `query_table_for_opus_id` (adds the `target_name` filter);
    `api_get_mult_counts` (its `get_model`, `add_from`, and `search_cache_join_condition`
    on the category); `api_get_range_endpoints` (**both branches filter by target**: the
    no-selection branch aggregates `Min`/`Max` over the whole table through the ORM and
    would mix every target, and the selection branch's `WHERE` needs the same predicate
    beside its join); and `get_metadata` (its per-category probes for surface geometry
    categories become one query listing the observation's targets, then one query per
    target present). `api_string_search_choices` also uses the category as a source but
    is unaffected because the template has no STRING field; the executor asserts that in
    a test so a future STRING field fails loudly. `get_triggered_tables`'s selector branch
    uses only the selections and needs nothing. `sql_builder.FromSource` gains an
    **aliased table source** (`_render_source` quotes a bare name today), used by the
    join and by `add_from` for a resolved category.
  - **Categories for an observation.** `api_get_categories_for_opus_id` makes **one** query
    for the surface geometry categories (`SELECT target_name FROM obs_surface_geometry_target
    WHERE obs_general_id = %s`) and maps the ids to category names through `TableNames`,
    **ordered by `table_names.disp_order`** as the response is today, instead of probing
    one model per target. (This gain is available today from `obs_surface_geometry_name`
    and is not the reason for the one table; see Acceptance.)
  - **Import.** `import_one_index` writes per-target rows into one table (the `<TARGET>`
    branch in its final loop and the per-target `create_table` go); the parent in PR-09
    has one less table kind to create; `do_validate` gains a **per-physical-table path**
    for all three of its `param_info`-keyed checks: `validate_param_info` (which requires
    a `param_info` row keyed by the physical table for every column of every `obs_` table
    and would log an error per geometry column) and `validate_min_max_order` look
    `param_info` up through one representative category (the first
    `obs_surface_geometry__*` row), with the `target_name` column mapped to the selector
    category's row, rather than by the physical table name, and `validate_nulls` runs its
    NULL counts once for the table, not once per category, and stops skipping;
    `do_update_mult_info` reads the `mult_field` key; `obs/obs_surface_geometry_name.py`
    merges into `obs/obs_surface_geometry_target.py` (its `target_name` method is the one
    table's `target_name` column); `config_data.py`'s table list names the one table;
    `import_tests/test_unit_layers.py`'s test of `table_name_for_sfc_target` stays,
    because the function stays and now spells the category name;
    `tests/opus_import/test_do_import_index.py`, `test_do_update_mult_info.py`,
    `test_package_data.py`, and `test_obs_field_annotations.py` are updated where they
    name the per-target tables;
    `integration_tests/test_db_data/test_local_db_integrity.py`'s per-model checks become
    checks that every `DISTINCT target_name` has its category rows;
    `docs/_ext/opus_field_tables.py` and `tests/opus_docs` expand the template per
    category as the import does, through the same `build_table_names_rows`.
  - **Models.** `inspectdb` emits `CompositePrimaryKey` for the composite key, as for
    PR-14's mult tables, and a `ForeignKey` named `obs_general` for the key column, which
    the script's existing `sed` rules annotate with `db_column` and `related_name`, so
    `.filter(obs_general__opus_id=...)` keeps working; PR-12's
    `OneToOneField(primary_key=True)` rule does not apply to this table. `inspectdb` must
    run against a **finalized** schema, because the foreign key exists only after
    finalization; the executor confirms the generated class imports and that
    `query_table_for_opus_id` works with it.
  - **What a new target costs after this PR:** one mult row and its `table_names`,
    `partables`, and `param_info` rows, all written by the import's finalization. No DDL
    mid-import, no model, no `create_opus_models.sh`, no redeploy.
  - **Alternatives considered and not taken.** *Dynamic Django models* (an abstract base
    plus a factory on `LookupError` for `obs_surface_geometry__*`): one small PR with no
    schema change that removes the redeploy pain but keeps a hundred tables, the mid-import
    DDL, and a hundred copies of every index; **it is the fallback if this PR slips**, and
    the orchestrator may schedule it ahead of this PR. *Partitioning the one table by
    target:* no foreign keys, every partition probed per observation; `KEY`/`HASH`
    partitioning needs no `ADD PARTITION` but gives nothing the target-first key does not.
    *Geometry as JSON on `obs_general`:* no typed range index. *Generating the category
    rows in the application:* duplicates the template expansion the docs extension also
    needs. *Dropping the per-target categories from the API:* out of scope.
- **Changes:** the schema files (`obs_surface_geometry_target.json` rewritten with the
  table-level keys and the `mult_field` key; `obs_surface_geometry_name.json` deleted;
  `table_names.json` gains two columns), `import_util` (`mult_field` key honored),
  `do_import_index`, `do_import_obs` (the category-name dispatch kept, the physical write
  added), `do_import_tables`, `do_table_names`, `do_param_info`, `do_partables`,
  `do_update_mult_info`, `do_validate`, `config_data.py`, the two obs modules,
  `import_tests/tools/negative_cases.py` (the recipe operation),
  `tools/db_utils`, `tools/sql_builder` (aliased source), `search/views.py`
  (`add_obs_table_joins`), `results/views.py` (`api_get_categories_for_opus_id`,
  `get_metadata`, the trigger model), `metadata/views.py` (`api_get_mult_counts`,
  `api_get_range_endpoints`), `create_opus_models.sh`, `models.py` regenerated (about a
  hundred classes fewer), the import goldens (the per-target tables' goldens become one;
  `obs_surface_geometry_name.tsv` goes; `table_names.tsv` gains two columns),
  `docs/_ext/opus_field_tables.py`, `dev_guide_database_schema.rst` (the surface geometry
  section is rewritten), `dev_guide_table_schemas.rst`, `dev_guide_webapp_search.rst`,
  `dev_guide_webapp_results.rst`, `dev_guide_import_steps.rst`.
- **New fixtures:** a new **recipe operation** in `import_tests/tools/negative_cases.py`
  (today `build_overlay` can only overwrite one column of one primary-index row) that
  edits a bundle's **surface geometry summary file**, renaming one body's rows to a target
  that appears nowhere else in the fixture (chosen from `TARGET_NAME_INFO`); a test that
  imports the overlay **with finalization** and then runs the Django checks **in a
  subprocess** with the run's `OPUS_CONFIG` (pytest-django configures Django once per
  session from the session's own configuration, so an in-process client cannot point at
  the run's schema): `opus_manage shell -c` driving the test client with
  the same `HTTP_HOST` rule as PR-17 to request `api/categories` for one of the
  overlay's observations and a `SURFACEGEO<target>_planetographiclatitude1` search,
  asserting both succeed with no code regeneration.
- **Measurement:** table count, `models.py` line count, import DDL count (from the SQL
  log), app-cold and db-cold latency of the surface-geometry range search for one target
  and of the categories call for an observation with surface geometry, the plan of the
  surface-geometry search (one index range on `(target_name, col)`), buffer misses for the
  fan-out, schema index bytes (expected within about fifteen percent either way; the
  entries are a few bytes wider and a hundred small trees per column become one;
  reported). **Target metric:** the structural criterion: one surface geometry table, one
  model, and the new-target test passing. **Guarded, beyond §2.5's list:** no regression
  beyond noise of the surface-geometry range search in **db-cold** (the key order decides
  it) or of the categories call. The categories call is expected to speed up by the
  removal of a hundred probes, and the PR reports it without claiming it as the payoff of
  the storage change.
- **Acceptance:** §2.5 with the structural criterion; API goldens unchanged
  (`api/categories`, `api/menu`, `api/fields`, `api_widget_surfacegeometrytargetname.html`,
  the `result_counts.csv` rows that carry `surfacegeometrytargetname`, and the
  triggered-table lists in `integration_tests/apps_db_tests/test_results.py` are the ones
  to watch); import goldens differ by the tables and columns declared.
- **Requires full re-import:** yes.
- **Scale:** full scale.

**PR-16: refactor: column types: variable-width strings, ASCII identifiers, no unread columns** (item 22; `§C-2.7`; `§D-2.9`)

- **The problem, as the code has it.** The observation schemas declare their strings as
  fixed-width `CHAR` (`grep -ho '"field_type": "char[0-9]*"' src/opus_import/table_schemas/obs_*.json | sort | uniq -c`
  lists the widths), and under `utf8mb4` InnoDB pads every `CHAR` value to its declared
  width. No table or column declares a character set or collation (`create_table` sets
  only `ENGINE=`), so every string is `utf8mb4_0900_ai_ci`, whose comparisons use
  Unicode collation weights and whose filesort keys MySQL sizes at four bytes per
  character; the default sort's `opus_id` tiebreak and every identifier join pay both.
  Every observation table and several support tables carry a `timestamp` column with `ON
  UPDATE CURRENT_TIMESTAMP` that nothing reads. `cart.session_id` is `char80` for
  Django's 32-character session keys, and `cart`'s foreign key onto `obs_general`
  restricts deletes, which is what makes an in-place bundle delete fail while a cart
  names one of its observations.
- **Changes:**
  - **Strings.** A `varcharN` field type (the OPUS-to-MySQL type map and `table_info`
    gain it) replaces every `charN` in the observation, template, and support schemas,
    keeping `N`.
  - **ASCII identifiers.** A column key `"field_charset": "ascii"` renders `CHARACTER SET
    ascii COLLATE ascii_general_ci`, which is case-insensitive like today's collation. It
    is set on `opus_id`, `bundle_id`, and `instrument_id` wherever they remain, and on
    every column whose `pi_form_type` is `STRING` and whose full-scale values are all
    ASCII (`SELECT COUNT(*) FROM <t> WHERE <col> <> CONVERT(<col> USING ascii)` is 0 on
    the harness's full-scale schema); the PR lists the set with the query results.
    `mult.value` and `mult.label`, the dictionary, and free text keep `utf8mb4`. A
    non-ASCII value bound for an ASCII column fails the load through PR-04's warning
    check, naming the column and the row, and a test plants one.
  - **Ordering.** Case never matters, before or after. Rows that tie on every sort key have
    no defined order, so their order may change. A sort on an identifier column may order
    punctuation differently (`_` sorts after letters in ASCII and before them under the
    current collation). The executor lists every API golden whose order changes, with the
    reason, in one batch, and the orchestrator rules once.
  - **Unread columns.** `timestamp` goes from every observation table, the template, and
    each support table for which `grep -rn "timestamp" src/opus_app src/opus_import --include=*.py`
    finds no reader; the PR lists each table and the evidence.
  - **`cart`.** `session_id` becomes `VARCHAR(40)` with the ASCII character set, and the
    foreign key onto `obs_general` becomes `ON DELETE CASCADE`, so an append's bundle
    delete removes the cart rows it orphans instead of failing. Promotion's carry-over
    (PR-17) is unaffected.
  - The generated models are regenerated; `docs/dev_guide_database_schema.rst` describes
    the types and the character-set rule.
- **Measurement:** data and index bytes per table before and after; the db-cold build of
  the broad default-sort search with its `Sort_merge_passes` and
  `Created_tmp_disk_tables` counters; the warm results page. Target metric: db-cold build
  of the broad default-sort search.
- **Acceptance:** §2.5, with the API-golden ruling above; a test asserts that an `opus_id`
  lookup in mixed case still matches.
- **Requires full re-import:** yes.
- **Scale:** full scale.
- **PostgreSQL note:** `VARCHAR` with the database's `C` or ICU case-insensitive
  collation per column; `CHARACTER SET` has no column-level equivalent.

**PR-17: feat: warm the landing page after a deploy, and carry sessions and carts over at promotion** (item 17; `§C-4.2`; `§D-3`; `§D-4`)

- **Design.** The empty search with the default sort is the search every visitor issues,
  and its mult counts and range endpoints are one cold fan-out per deploy; after PR-11 the
  search is one `search_results` build and every fan-out result is memcached until the
  next import. Rather than teaching the import to compute the application's search hash
  (it depends on `DEFAULT_SORT_ORDER`, `parse_order_slug`'s resolution through
  `param_info`, `sort_dictionary`, and `strip_numeric_suffix`, none of which the import can
  load), a management command **`opus_manage warm_search`** issues, through Django's test
  client **with `HTTP_HOST` set to the first `ALLOWED_HOSTS` entry that is not `*`**, or
  `localhost` when every entry is a wildcard (the client's default host is not in
  `ALLOWED_HOSTS` and would get 400), the empty search's result count and first page
  and the fan-out for the default widgets (`settings.DEFAULT_WIDGETS`;
  `get_triggered_tables` already returns `sorted(settings.BASE_TABLES)` for the empty
  search). The command **requires memcached** (it exits with a message when the `locmem`
  fallback is in effect, because then it would warm one process that is about to exit),
  and it warms memcached and the database but not each worker process's own caches (the
  first request on each worker still pays the per-process load; the PR says so).
  `_promote.sh` runs it after the symlink switch and the worker restart, **warning and
  continuing on failure** (a cold cache is not a failed deploy); the harness runs it when
  told the server is freshly promoted, so the db-cold number shows what a visitor sees.
  No view code branches on "empty"; nothing is prebuilt by the import; no hash lives in two
  places.
- **Changes:** the command under `opus_app/apps/search/management/commands/`, the one
  line `opus_manage warm_search` in `_promote.sh` after the web service starts (the staged
  `opus_venv` is active and `OPUS_CONFIG` exported by `_opus_setup_environment.sh` before
  `_promote.sh` is sourced; tested as a shell function per §3; the script itself is never
  run), `docs/user_guide_deployment.rst`, `dev_guide_webapp_search.rst`; `web.toml` gains
  a `warm` flag per state.
- **Carry-over at promotion.**
  - `opus_import --carry-over-sessions-from <served>`, run with the new schema as the
    target: `INSERT INTO <target>.django_session SELECT * FROM <served>.django_session
    WHERE expire_date > NOW()`, then `INSERT INTO <target>.cart (session_id,
    obs_general_id, opus_id, recycled) SELECT c.session_id, n.id, c.opus_id, c.recycled
    FROM <served>.cart c JOIN <target>.obs_general n ON n.opus_id = c.opus_id JOIN
    <target>.django_session s ON s.session_key = c.session_id`, so a cart whose session
    expired is not carried; the step truncates the two target tables first, so it is
    idempotent and runs in either direction (a rollback is the promotion toward the
    previous installation), and logs the row counts copied and the cart rows dropped
    (`COUNT(*)` of `<served>.cart` less the rows inserted). `cart.id` is `AUTO_INCREMENT`
    and is not copied.
  - `_promote.sh` runs that step between stopping the web service and switching the
    symlink when `OPUS_PREVIOUS_DB_NAME` is set. **If the step fails, `_promote.sh`
    starts the web service again on the unchanged installation and exits non-zero,
    exactly as its existing symlink-failure branch does**; nothing has switched, and the
    shell-function test covers that branch; `deploy_new_code_and_database.sh` sets
    it from the served installation's `opus.toml` as `deploy_new_code_only.sh` already
    reads `OPUS_DB_NAME` (so a full-import deploy carries sessions and carts over too);
    `deploy_new_code_only.sh` leaves it unset (same schema, nothing to carry).
  - `_promote.sh` runs that step between stopping the web service and switching the
    symlink when `OPUS_PREVIOUS_DB_NAME` is set. **If the step fails, `_promote.sh`
    starts the web service again on the unchanged installation and exits non-zero,
    exactly as its existing symlink-failure branch does**; nothing has switched, and the
    shell-function test covers that branch. `deploy_new_code_and_database.sh` sets it
    from the served installation's `opus.toml`, as `deploy_new_code_only.sh` already
    reads `OPUS_DB_NAME`, so a full-import deploy carries sessions and carts over too;
    `deploy_new_code_only.sh` leaves it unset (same schema, nothing to carry).
  - Tests: two `cart` rows planted in a source schema (one for an observation the
    target has, one for an observation it lacks) carry over as one row with the target's
    `obs_general_id` and one counted drop; the carry-over truncates first, so running it
    twice gives the same result.
- **Measurement:** db-cold and app-cold latency of the empty-search scenario, its first
  page, and the fan-out, measured after a simulated deploy with and without the warm-up.
  The promotion window (web stop to web start) is reported with 10,000 planted cart rows.
  Target metric: db-cold latency of the empty search's first page with the warm-up,
  expected to approach the warm number.
- **Acceptance:** §2.5; API goldens unchanged; a `tests/opus_app` test that the command
  issues the expected requests through the test client and refuses under locmem.
- **Scale:** full scale.

**PR-18: refactor: move preview_images out of obs_general** (item 12; `§C-2.5`; `§D-2.1`)

- **Gate:** executed only if the full-scale `bench_db` of this PR's merge-base records
  `preview_images`'s total `JSON_STORAGE_SIZE` as more than one quarter of
  `obs_general`'s data length (PR-16's column types change that length, so PR-00's
  number is not the one). If
  not, the orchestrator records "not executed, ratio below the rule" in the Execution
  notes and the number stays, so the decision is reproducible.
- **Changes:** `obs_preview(obs_general_id INT UNSIGNED PRIMARY KEY, preview_images JSON)`
  with a schema file and a table-level foreign key added in finalization; the per-bundle
  steps reach it through PR-12's join; `obs_general` loses the column; the readers
  (`api_get_data_and_images` and whatever `grep -rn preview_images src/opus_app
  --include=*.py` finds) join it; the import writes it as one more child table through the
  existing per-table path.
- **Measurement:** `obs_general` data length; app-cold latency of every scenario that
  scans `obs_general` (the target search before PR-19, the mult counts, the
  triggered-tables `DISTINCT`). Target metric: app-cold target-search latency.
- **Acceptance:** §2.5.
- **Requires full re-import:** yes.
- **Scale:** full scale.

### Phase 4: indexes for the list columns, re-sort, autocomplete

**PR-19: feat: a junction table for the mult_list columns** (item 9; `§C-2.4`; `§D-2.5`)

- **Changes:** `sql_builder.list_contains_any(column, values)` replaces the
  `JSON_CONTAINS ... OR ...` chain in `construct_query_string` (one call for a
  multi-value selection), passing the mult ids as **integers** (today's call passes
  `str(mult_value)`). There are two `mult_list` columns, both on `obs_general`
  (`target_name` and `target_class`; `grep -l mult_list src/opus_import/table_schemas/*.json`
  confirms the set), and each gets a junction table: `obs_general_target_name(mult_id,
  obs_general_id, PRIMARY KEY (mult_id, obs_general_id), KEY (obs_general_id))` and
  `obs_general_target_class(...)` likewise (the per-bundle steps and the duplicate OPUS
  id delete reach them through `obs_general_id`, PR-12), written by
  the import beside the JSON column
  (which stays for the API's response rendering) from the resolved id lists (PR-09's parent
  emits the rows after mult resolution; a list that repeats an id writes one row). The
  search becomes a semi-join (`EXISTS` on the junction); the **mult count**, which today is
  `JSON_TABLE(...) GROUP BY` over the whole result set, becomes a `GROUP BY mult_id` on
  the junction joined to `search_results` (after which `sql_builder.JSONTable` may have no
  caller; the executor checks and removes it if so). `mult_id` has PR-14's id width, and
  PR-14's unused-value cleanup reads the junction tables for these two fields instead of
  the JSON. The MySQL multi-valued index serves
  the search only and is **not** used. PostgreSQL note: the same junction tables; a
  `jsonb_path_ops` GIN is the search-only alternative.
- **Measurement:** the plan of the target search (full scan becomes a semi-join),
  app-cold latency of the target search and of its mult counts, the digests. Target
  metric: app-cold target-search latency, with the target mult count as the secondary.
- **Acceptance:** §2.5; API goldens unchanged (same rows, same order, same counts).
- **Requires full re-import:** yes.
- **Scale:** full scale.

**PR-20: feat: separate the result set from its order** (item 14; `§C-4.1`; `§D-2.4`)

- **Gate:** opened only if, in PR-19's full-scale `EXPLAIN ANALYZE` of the broad
  search's build, evaluating the predicate takes more than a quarter of the build's
  time, which is what a set hash saves on a re-sort. The number decides.
- **Changes:** `set_user_search_number` also hashes the selections, qtypes, and units
  alone into a **set** hash; `user_searches` gains `set_hash BINARY(32)` with a key,
  beside PR-11's `search_hash`, and `search_results` stays keyed by `search_id`; a re-sort
  of a built set is `INSERT ... SELECT set's ids ORDER BY ...` joined to the sort columns
  rather than a re-evaluation of the `WHERE` clause. `result_count` belongs to the set.
  The new column needs no re-import and no `SCHEMA_VERSION` bump, since the import does
  not fill `user_searches` (§1, Deploy); the `opus_manage warm_search` command needs
  nothing.
- **Measurement:** app-cold latency of the re-sort scenarios. Target metric: re-sort
  latency on the broad search.
- **Acceptance:** §2.5; API goldens unchanged.
- **Requires full re-import:** no.
- **Scale:** full scale.

**PR-21: feat: indexed autocomplete** (item 18; `§C-4.3`; `§D-2.6`; #1301)

- **Issues:** #1301 reports autocomplete going silent once the typed OPUS id passes a
  certain length; the acceptance repeats its steps against the full-scale schema and
  records whether the index resolves it.

- **Changes:** a `FULLTEXT ... WITH PARSER ngram` index on each string column
  `api_string_search_choices` searches (the executor derives the column list from the
  `STRINGCHOICE` handling in `search/views.py` and the `param_info.form_type == 'STRING'`
  rows, not from a hand-written list), declared as the table-level entry
  `{"fulltext": ["col"]}` so the column keeps its B-tree; PR-07's finalization builds each
  **first and in its own `ALTER`** (the first `FULLTEXT` on a table without a user
  `FTS_DOC_ID` column rebuilds the table, so it precedes the B-tree builds; InnoDB builds
  one `FULLTEXT` per statement). The query uses `MATCH ... AGAINST (%s IN BOOLEAN MODE)`
  for the `contains` qtype only and prefixes of two or more characters, **with the user's
  term wrapped in double quotes as a phrase and any embedded double quote removed**
  (boolean mode treats `-`, `+`, `*`, `"`, and `~` as operators, and filespecs contain
  `-`), and today's `LIKE` for one character and for every other qtype; the
  `MAX_EXECUTION_TIME` wrapper stays. **Server settings:** `ngram_token_size` is 2 by
  default and startup-only; the PR records the value and the finalization refuses to
  build the index if it is not 2. **`innodb_ft_enable_stopword` must be OFF for the
  session that builds the index** (the default stopword list contains `a` and `i`, and
  the ngram parser drops every token containing a stopword), which the finalization sets
  per session before each `FULLTEXT` build. Plain `FULLTEXT` is not used: it tokenizes on
  `-`, `_`, and `/`, which is most of a filespec. Results must be the same set as the
  **full-search branch** of today's `LIKE` path; a test compares them on the fixture schema
  for every autocomplete column and a differing column keeps `LIKE`, listed in the PR.
  PostgreSQL note: a `pg_trgm` GIN serves `LIKE '%x%'` and `ILIKE` with no query change.
- **Measurement:** autocomplete scenario latency, two- and six-letter prefixes, warm and
  app-cold; the `MAX_EXECUTION_TIME` fallbacks counted. Target metric: six-letter prefix
  latency.
- **Acceptance:** §2.5; API goldens unchanged.
- **Requires full re-import:** yes.
- **Scale:** full scale.

### Phase 5: the deploy, the measured options, and the server

**PR-22: feat: incremental update seeded from the served schema and promoted whole** (`§D-3.1`)

- **The problem, after PR-08.** The append updates a finalized schema in place, which is
  right for a database nobody is using and wrong for the served one: between the first
  bundle delete and the end of the re-run finalization a request can build a search
  against a partial observation set, and the workers' per-process caches are refreshed
  only by the restart. The full-import deploy avoids this by building a new schema and
  promoting it, and this PR gives incremental updates the same shape without a full
  import.
- **Changes:**
  - `opus_import --clone-from-schema <served>`, accepted only on an empty target. It
    refuses when the served schema's version row differs from the release's
    `SCHEMA_VERSION`, since its rows would not fit the new tables. Before the first
    bundle it creates every table as PR-07's build does and copies the served schema's
    rows: `obs_general` with `INSERT INTO <target>.obs_general SELECT * FROM
    <served>.obs_general WHERE bundle_id NOT IN (%s, ...)`, and every other
    per-observation table with `WHERE obs_general_id NOT IN (SELECT id FROM
    <served>.obs_general WHERE bundle_id IN (%s, ...))`, excluding the positional bundles
    and those named by the existing `--delete-permanent-bundles` (bundles to drop
    without re-importing); and the `mult`, `mult_field`, and `mult_group` tables whole,
    whose values only the excluded bundles used are then removed by PR-14's finalization
    step. The copies run over PR-07's sibling connections, one table per connection,
    `obs_general` first by convention. The served schema is read only, and the account
    needs `SELECT` on it (documented). Nothing else is copied: `cart`, `user_searches`,
    `search_results`, the dictionary, the aux tables, and Django's tables are created
    empty or regenerated by the steps that follow (`migrate`, `--import-dictionary`,
    `--cleanup-aux-tables`, `--write-schema-version`).
  - The target then has no version row and no secondary indexes, so the bundles go
    through PR-07's ordinary build, and finalization builds every index once, by sort.
    `find_max_table_id` reads the copied maximum, so the imported bundles' ids continue
    above it; PR-07's probe handles an `opus_id` already present in a copied bundle; mult
    values append through `read_or_create_mult_table`.
  - `_run_incremental_update.sh [<version_spec>] <bundle>...`, modeled on
    `_run_full_opus_import.sh`: a new `OPUS_DB_NAME`, the served schema name read from
    `deployed/opus.toml`, the staged installation, then one `opus_import
    --clone-from-schema <served> --import <bundles>` invocation, finalization, and the
    same error-log check as `_opus_import_volumes.sh`; a `--drop <bundle>,...` option is
    passed through as `--delete-permanent-bundles`. The operator then runs
    `deploy_new_code_and_database.sh <new db>` as after a full import, and PR-17's
    carry-over moves the sessions and carts. Added to `tests/opus_deploy`'s
    `EXPECTED_FILES`.
  - Tests: `build_run` gains `clone_run(source_schema, reimport, drop)`, which imports
    the fixture fully into one schema, seeds a second from it with one bundle re-imported
    and one dropped, and asserts per table that the row counts and the set of `opus_id`
    values equal the source less the dropped bundle, that the golden tables, columns, and
    primary keys equal the source's, and that a mult value only the dropped bundle used is
    gone. Unit tests in `tests/opus_import` cover the rendering of the exclusion and the
    set of tables copied whole.
  - Docs: `user_guide_deployment.rst` (the incremental update procedure and the `SELECT`
    grant), `dev_guide_import_running.rst` (the option), `dev_guide_import_steps.rst`
    (the seed).
- **Measurement:** on the incremental group of `import_full.toml` at full scale: the
  seed's wall-clock and the whole update's (seed, build, finalization), against PR-08's
  append of the same group into the served schema's copy; and the disk of the two
  schemas. Target metric: incremental update wall-clock.
- **Acceptance:** §2.5; the clone test; goldens unchanged; `CHECKSUM TABLE` of the
  served schema's `obs_general` identical before and after the run.
- **Requires full re-import:** no.
- **Scale:** full scale.
- **PostgreSQL note:** cross-schema `INSERT ... SELECT` is the same statement with
  schema-qualified names; `search_path` is not involved.

**PR-23: perf (gated): three options measured on real data, then discussed** (item 17; `§C-4.1`; `§D-2.4`; `§D-2.8`)

- **Gate: measure, report, discuss, then decide.** After every PR above has merged, the
  executor prototypes each option on a scratch copy of the full-scale schema the harness
  builds from the production holdings, with no application change merged. It opens the
  PR with a report only: per option, the target metric and the guarded metrics before
  and after, against the recorded noise floor, with the prototype's cost in bytes, in
  import time, and in code. Nothing is implemented until the discussion on the PR
  decides which options go in; the orchestrator records the decision and its reason
  for each option in the Execution notes, and the executor then implements exactly
  the chosen ones on the same branch. If none is chosen, the PR closes with the report
  committed under `benchmarks/results/`.
- **Option 1: a default-sort rank on `obs_general`.** Prototype: `ALTER TABLE obs_general
  ADD COLUMN default_rank INT UNSIGNED, ADD KEY (default_rank)`, filled from
  `ROW_NUMBER() OVER (ORDER BY time1, opus_id)`. Measured against the unmodified schema:
  the empty search's first and last pages in the default sort, read as `default_rank
  BETWEEN ? AND ?` with no `search_results` build, and the `search_results` build of a
  broad constrained search ordered by `default_rank` instead of `(time1, opus_id)`.
  Target metric: db-cold first page of the empty search. If implemented: `obs_general.json`
  declares the column; finalization writes it after the B-tree builds, so a full import
  and an incremental update both renumber it; a search in the default order sorts on it;
  and the empty search in the default order pages on it directly, the one place the
  application branches on the empty search. `SCHEMA_VERSION` bumps.
- **Option 2: precomputed empty-search mult counts.** Prototype: `mult_count_empty(field_id
  SMALLINT UNSIGNED, mult_id SMALLINT UNSIGNED, count INT UNSIGNED, PRIMARY KEY (field_id,
  mult_id))`, filled once. Measured against PR-17's warm-up alone, both right after the
  warm-up and right after a cache flush: the db-cold and app-cold mult counts of the empty
  search for the default widgets and for one widget outside them. Target metric: app-cold
  empty-search mult count after a cache flush. If implemented: the table is created by a
  `--create-mult-count-empty` step in the `--cleanup-aux-tables` group and truncated by
  `reset_search_tables`; `opus_manage warm_search` fills it for every mult field through
  `api_get_mult_counts`'s own counting function with the empty selections; and the
  endpoint reads it for an empty search, counting as before when the field has no rows.
  `SCHEMA_VERSION` bumps.
- **Option 3: a narrow facet table for mult counts.** Prototype: `obs_facet(obs_general_id
  INT UNSIGNED PRIMARY KEY, <one SMALLINT column per mult_idx, flag_yesno, and flag_onoff
  column, named by qualified name>)`, filled by one `INSERT ... SELECT` joining the hub
  and the children. Measured against PR-14's schema: the app-cold mult counts of a broad
  constrained search and of a selective one, for the default widgets and for a widget on
  a child table, each counting from `obs_facet` joined to `search_results` instead of
  from the child tables. Target metric: app-cold mult count of the broad constrained
  search. If implemented: finalization writes the table after the mult step, the
  counting function reads it for the columns it holds, and the list columns keep their
  junction tables. `SCHEMA_VERSION` bumps.
- **Changes, if implemented:** the schema file changes above, the finalization step or the
  warm-up addition, and the endpoint changes, with `dev_guide_webapp_search.rst`. Options
  1 and 3 declare their finalization steps invalidated by an append (§1).
- **Measurement:** the prototype numbers above, then the same scenarios on the implemented
  branch.
- **Acceptance:** §2.5; API goldens unchanged.
- **Requires full re-import:** yes for options 1 and 3; no for option 2, whose table the
  import does not fill (§1, Deploy).
- **Scale:** full scale.

**PR-24: docs: size the import and web servers from the measurements, and add range-search histograms** (items 19 and 10, second half; `§C-2.2`; `§C-5`)

- **Changes:**
  - **One home for server settings.** `docs/user_guide_*` gains a section that derives the
    buffer pool size from the schema total the harness records (the docs say how to read
    the number, not what it was on one day) and names the parallelism, durability, and
    statistics settings with what each does for OPUS: `innodb_buffer_pool_size`,
    `innodb_redo_log_capacity`, `innodb_flush_method`, `innodb_ddl_threads`,
    `innodb_ddl_buffer_size`, `local_infile`, `log_bin`,
    `innodb_flush_log_at_trx_commit`, `innodb_ft_enable_stopword`, `ngram_token_size`,
    `performance_schema_max_digest_length`, and `innodb_parallel_read_threads`, described
    accurately as parallelizing only the clustered-index `COUNT(*)` and `CHECK TABLE`.
    PR-00's tuning baseline, PR-04's import-server paragraph, and PR-21's ngram text link
    to it instead of repeating it.
  - **Web workers.** The three worker examples in `docs/user_guide_web_server.rst`
    (gunicorn, uWSGI, mod_wsgi) move to the thread count the concurrency scenario
    measures best, with the reason stated: the handlers wait on the database. There are
    no web-server templates under `src/opus_deploy/server/` to edit.
  - **Histograms.** `--analyze-permanent-tables` (in the cleanup group since PR-07), which
    an append re-runs (§1), gains `ANALYZE TABLE ... UPDATE HISTOGRAM ON` for the columns
    the range searches use, derived from `param_info`'s `RANGE` form types, not
    hand-listed.
  - **Index pruning input.** The index-usage query an operator runs after a month of
    production uptime (`sys.schema_unused_indexes`) to produce the input for the deferred
    index-pruning PR. `src/opus_deploy/server/README.txt` points at the section.
- **Measurement:** the range-search scenarios and the broad build with and without the
  histograms, and the concurrency scenario at two, four, and eight threads per worker.
  Target metric: app-cold latency of the range searches.
- **Acceptance:** §2.5; API goldens unchanged.
- **Requires full re-import:** no; `--analyze-permanent-tables` adds the histograms to a
  served schema.
- **Scale:** full scale. It is last before the merge so that it describes the schema the
  earlier phases produced.

### Phase 6: merge

**PR-25: Merge `db-perf` into `main`**

- **Preconditions:** every PR above merged into `db-perf` or recorded as not executed
  (PR-18, PR-20, and PR-23 are gated); a full integration run green on `db-perf`'s head;
  `scripts/run-all-checks.sh` clean; and **the orchestrator's deploy rehearsal on the
  Node** with `deploy_new_code_and_database.sh` into a staged installation (the deploy
  scripts run `sudo`; this step is not the executor's), including the `warm_search` step,
  PR-05's refusal exercised once against a stale schema, and one
  `_run_incremental_update.sh` of a single bundle followed by its promotion, recorded in
  the Execution notes.
- **Changes:** the workflow branch filters narrowed back to `main`; the plan, the design
  document, and the analysis move to `plans/archive/` and `critiques/archive/` per
  `CLAUDE.md`, with the Execution notes complete. The PR description carries the final
  before/after table from PR-00's baseline to `db-perf`'s head, both scales, produced by
  `compare.py` from the committed results.
- **After the merge:** the orchestrator cuts the release per the repository's release
  convention. Phase P may begin, or not.

### Phase P (optional, later): PostgreSQL to parity, then head to head

This phase is the investigation #352 asks for. Everything in it is deferred until the
orchestrator opens it. It repeats the
branch arrangement on `db-postgresql` off `main`, and its PRs are numbered `PR-P1` to
`PR-P5`. The port is of the tree as Phase 6 leaves it: no `cache_*` tables, no temporary
tables, children keyed on `obs_general_id`, one surface geometry table, junction tables,
foreign keys added in finalization. The **PostgreSQL notes** scattered through §4 are its
checklist. Nothing in Phase P changes behavior on MySQL; every PR here runs the existing
MySQL suites unchanged as its regression check.

**PR-P1: feat: PostgreSQL import backend and harness** (item 20; `§C-5`)

- **Floor and driver:** PostgreSQL 16, the lowest release in community support at the time
  of writing (the features used are older); `psycopg` 3 with its binary extra, as the
  optional dependency extra `rms-opus[postgresql]`. The orchestrator may raise the floor
  to 17 to gain `pg_buffercache_evict` for a shared-server db-cold; otherwise db-cold on
  PostgreSQL exists only with a harness-owned server (§2.4).
- **Changes:**
  - `importdb/postgresql.py` implements every `ImportDBSuper` method the MySQL class
    implements (`open_sibling_connection()`, `bulk_load_rows`, `build_indexes`, and the
    build and append paths). The brand-specific decisions, each stated in
    `docs/dev_guide_import_db.rst`: the **type map** covering every `field_type` the
    schemas use, with `uint4` to `bigint`, `real4`/`real8` to `real`/`double precision`,
    `char(n)` to `varchar(n)`, `enum` to `varchar` with a `CHECK` constraint, `timestamp`
    to `timestamp DEFAULT now()` with no trigger, `mult_list` and `json` to `jsonb`,
    `field_autoincrement` to an identity column; indexes by `CREATE INDEX`, run
    concurrently across siblings by `build_indexes`; foreign keys in finalization as `ADD
    CONSTRAINT ... NOT VALID` then `VALIDATE CONSTRAINT`; `[database] schema` set as
    `search_path`, `[database] database` required for the brand, and a new `[database]
    port` key (per §1's rule; `DATABASES` gains `PORT`); `upsert_rows` as `INSERT ... ON
    CONFLICT (id) DO UPDATE`; `bulk_load_rows` as `COPY ... FROM STDIN` through
    `cursor.copy()` and `write_row()`, without `FREEZE`; `synchronous_commit = off`
    documented as an import-server setting; identifier quoting with double quotes; the
    test database created with `LC_COLLATE = 'C'`.
  - `do_validate.py` loses its `LIMIT 1,1` and `IFNULL`; the rendering goes through the
    brand class.
  - `settings.DATABASES` for PostgreSQL, moved here because `import_tests` runs `migrate`.
  - **The harness and `import_tests` are ported:** `golden_io` dispatches on brand;
    `db_credentials` gains `OPUS_TEST_DB_BRAND`, `OPUS_TEST_DB_PORT`, and
    `OPUS_TEST_DB_DATABASE`; `build_run`'s configuration template takes the brand, the
    port, and the database; `make_mini_goldens` runs through the same module;
    `bench_server` starts a harness-owned `postgres` as it starts `mysqld`; `bench_import`
    and `bench_db` gain their PostgreSQL branches (`pg_stat_database` counters,
    `pg_table_size`, `pg_indexes_size`, `pg_indexes`, `EXPLAIN (ANALYZE, BUFFERS, FORMAT
    JSON)` **inside a transaction that is rolled back**, `pg_stat_user_indexes`,
    `pg_stat_statements` when preloaded); `benchmarks/README.md` gains the PostgreSQL
    tuning baseline (§2.4).
  - Every sentence saying MySQL is the only brand is rewritten (§3); the views' driver
    error-code tests move behind `db_utils` predicates (PR-P2 completes this).
- **Tests:** `tests/opus_import/test_importdb_postgresql.py` mirrors the MySQL unit tests;
  `import_tests` runs the fixture import on PostgreSQL and compares against **the same
  goldens**, with the golden reader normalizing float text and `jsonb` key order and the
  PR stating each normalization; a new golden file per brand is a stop-and-report.
- **Acceptance:** `pytest import_tests` passes on both brands locally; the MySQL suites are
  unchanged and green; `--validate-perm` is clean on both.

**PR-P2: feat: PostgreSQL application backend** (item 20; `§C-4`; `§C-5`)

- **Changes:** `sql_builder` dispatches on `connection.vendor` wherever the SQL differs,
  and nothing outside it does. The constructs, each with a rendering test per brand:
  `json_contains` (`jsonb @> %s::jsonb`), `json_extract_first` (**`(col ->> 0)::bigint`**,
  because it is compared to `mult.id`), `JSONTable` if it still has a caller
  (`jsonb_array_elements` with an alias distinct from the base table);
  `replace_into_values` and `replace_into_select` as `INSERT ... ON CONFLICT (session_id,
  obs_general_id) DO UPDATE`; `delete_joined` as `DELETE FROM t USING ...`; `in_sequence`
  as `= ANY(%s)` with a list; `angular_separation` with a float `floor`-based modulus;
  `RLIKE` and `REGEXP_LIKE` as **`~*`**, with `_valid_regex` moved into `sql_builder`;
  `Select.max_execution_time` (the `MAX_EXECUTION_TIME` hint) as `SET LOCAL
  statement_timeout` inside a `transaction.atomic()` it opens, and the fallback query that
  follows a `QueryCanceled` issued **outside** the failed `atomic()`; the build's `FOR
  UPDATE` unchanged, with `SET LOCAL lock_timeout` for `search_build_timeout`; `ORDER BY`
  terms carrying `NULLS FIRST` ascending and `NULLS LAST` descending; `ILIKE` for the
  string qtypes. **Driver errors:** `tools/db_utils.py` exposes `is_timeout_error(exc)`
  and `is_lock_timeout_error(exc)` and is the only module importing driver error types;
  the views' `MYSQL_*` constant tests call them. **Collation:** where `C` and
  `utf8mb4_0900_ai_ci` disagree the executor lists each golden with the two orders **in
  one batch** and the orchestrator rules once whether the API gains an explicit tiebreaker
  on both brands or the port adds a `COLLATE` clause. `jit` measured on and off on the
  wide `LEFT JOIN` search; Django's native psycopg pool replaces `CONN_MAX_AGE` on the
  PostgreSQL line; `create_opus_models.sh` runs `inspectdb` against whichever brand the
  configuration names, and the PR states that the two generated files differ only in field
  types with the same Python type.
- **Tests:** per-brand rendering tests for every `sql_builder` function; a MySQL snapshot
  test proving the MySQL SQL is byte-identical to the merge-base; `integration_tests`
  against the PostgreSQL schema PR-P1 produced at full scale, passing **unchanged** except
  for goldens the orchestrator ruled on.
- **Acceptance:** API goldens pass on both brands; the MySQL snapshot test passes.
- **Scale:** full scale.

**PR-P3: ci: run the unit, import, and integration suites on both brands** (item 20)

- **Changes:** `run-tests.yml` gains a PostgreSQL 16 service container alongside the MySQL
  one and runs `pytest import_tests` on both; `run-integration.yml` runs the self-hosted
  import and golden suite on both when the runner has a PostgreSQL server (the
  orchestrator provides it; the nightly schedule alternates brands if one run per night is
  the budget, and the PR says which); `scripts/automated_tests/opus_setup_environment.sh`
  and `opus_main_test.sh` take the brand from `~/opus_runner_secrets`;
  `scripts/run-all-checks.sh --import-tests` takes a brand or runs both;
  `tests/fixtures/opus_ci.toml` gets a PostgreSQL sibling; the deploy chain's
  `_write_opus_toml.sh` and `deploy.env.template` carry the brand; the docs say how to
  point each suite at each brand.
- **Acceptance:** both brands green in both workflows on the final head.

**PR-P4: bench: head-to-head measurement and the brand decision** (item 20)

- **Measurement:** the full harness, full scale, both brands, per §2.4, both servers
  harness-owned; db-cold compared only if both are, else app-cold and warm only.
  **Expectation stated so the result can be read:** PostgreSQL 16 never uses a parallel
  plan for `INSERT ... SELECT`, which is what the `search_results` build is, so the
  broad-search build is expected near parity; read-only aggregates (mult counts over a
  broad result set) are where parallel query can show; the import is expected near parity
  with foreign keys deferred on both brands.
- **Deliverable:** a PR whose description is the comparison table and a one-page reading
  of it. No recommendation is made in the PR; the orchestrator records the decision in the
  Execution notes in one of three forms: **MySQL only**, **PostgreSQL only**, or **both**.
  The Phase 4 PostgreSQL notes (GIN, `pg_trgm`) are implemented in PR-P5 only if
  PostgreSQL survives the decision.
- **Scale:** full scale.

**PR-P5: Merge `db-postgresql` into `main`**, with the Phase 4 PostgreSQL items if the
decision kept the brand, under the same preconditions as PR-25 (the deploy rehearsal being
the orchestrator's).

---

## 5. Dependencies and ordering

| PR | Depends on | Why |
|---|---|---|
| PR-01 to PR-03 | PR-00 | the harness is the proof |
| PR-04 | PR-00 | measures the write path |
| PR-05 | PR-00 | first schema change; every later schema PR bumps its constant; PR-07 dispatches on its row |
| PR-06 | PR-00 | the build path must not drop a staging table the aux steps use |
| PR-07 | PR-04, PR-05, PR-06 | loads through PR-04's loader, dispatches on the version row, and leaves the aux steps to the swap |
| PR-08 | PR-07 | completes PR-07's dispatch and removes the path it superseded |
| PR-09 | PR-01, PR-04, PR-07, PR-08 | the parent resolves mults through PR-01's structures, writes through PR-04's loader, and runs PR-07's probe on the single write path |
| PR-10 | PR-00 | smallest web change; needs no new table |
| PR-11 | PR-05, PR-07, PR-10 | the guard exists; its table-level keys go through PR-07's filter; paging is already range-based |
| PR-12 | PR-05, PR-07, PR-09, PR-11 | the keep set and the finalization foreign keys are PR-07's; `instrument_id` comes from PR-09's parent; the same join helpers as PR-11 |
| PR-13 | PR-07, PR-12 | composite indexes are built by PR-07's finalization on the rekeyed schemas |
| PR-14 | PR-03, PR-07, PR-08, PR-11 | the label caches are rewritten; the cleanup and ranks are a finalization step an append re-runs; the table-level key forms |
| PR-15 | PR-03, PR-09, PR-11, PR-12, PR-13, PR-14 | `resolve_category` uses PR-03's caches; PR-09's parent writes the rows; the one table follows PR-12's rule, PR-13's key form, and PR-14's ids |
| PR-16 | PR-04, PR-12, PR-14, PR-15 | the load's warning check rejects non-ASCII values; mult labels stay `utf8mb4`; the columns are the rekeyed and merged tables' |
| PR-17 | PR-11 | warms a `search_results` search; the carry-over edits the same `_promote.sh` region |
| PR-18 | PR-07, PR-12, PR-16 | gated on its merge-base's ratio; a child table on the rekeyed pattern, its foreign key added in finalization |
| PR-19 | PR-09, PR-11, PR-14 | the parent emits junction rows from resolved ids; the mult count joins `search_results`; PR-14's cleanup reads the junctions |
| PR-20 | PR-19's measurement | gated on the predicate share of the broad build |
| PR-21 | PR-07, PR-11 | `FULLTEXT` keys are built by PR-07's `add_secondary_indexes`; the `COUNT(*)` is already gone |
| PR-22 | PR-07, PR-08, PR-14, PR-15, PR-17 | the seed uses the build path and its sibling connections; the append is its baseline; a new target is a row; PR-17's carry-over moves the sessions |
| PR-23 | every PR above | measured on the finished schema; option 2 extends PR-17's warm-up; option 3 reads PR-14's ids |
| PR-24 | every PR above | describes the final schema |
| PR-25 | PR-24 and the recorded outcomes of PR-18, PR-20, and PR-23 | the merge |
| PR-P1 | PR-25 | the port is of the merged tree |
| PR-P2 to PR-P5 | the previous | in order |

---

## 6. Risks

- **A mult field outgrows `SMALLINT`.** PR-14 reads PR-00's row counts before choosing
  the width, and the import refuses an id above the type's maximum, so the failure is a
  named fatal error at import, never a silent wrap.
- **The computed display rank reorders a widget or an `api/mults` response.** That is
  the intent where today's key is wrong; PR-14 lists every changed golden with its
  reason, and the results order on a mult column is pinned unchanged.
- **The seed copies the whole database on every incremental update.** PR-22 measures
  it against PR-08's append of the same group; the copy runs over sibling connections
  and the indexes are built once afterward (PR-07). If the clone
  dominates at full scale the number is reported and the update is still correct; no
  partial alternative keeps the switch atomic.
- **`LOAD DATA LOCAL INFILE` is disabled on a server.** PR-04 falls back to packets and
  says so in the log; the harness records which path ran so the two are never compared
  unknowingly.
- **`LOAD DATA LOCAL INFILE` hides an error.** PR-04's post-load check (records, skipped,
  warnings) is the guard, tested with a duplicate key and a truncated value.
- **A failed or interrupted build or append leaves a partial schema**, including mult
  values the failed bundle added. The bundle delete at the start of each bundle makes a
  rerun clean; a build has no version row and an append sets `state = 'appending'`, and
  either keeps both deploy scripts and the application from serving it (PR-05, PR-08);
  an interruption during the index build is refused by PR-07's dispatch, and the remedy
  is scorched earth.
- **New code stamps an old schema.** Prevented by the two PR-05 rules: the step writes
  only when the row is absent, and both deploy scripts check before any import step.
- **Index builds at full scale need temporary space on the server.** PR-07's estimate is
  row-based and summed over concurrent builds; `server_tmpdir` is optional and server-side.
- **A worker touches the database or the filesystem in a way the audit missed.** The
  worker's `ctx.db` is `None`, so a database call fails loudly in the fixture suite; the
  determinism test and the warning whitelist catch a divergent log.
- **The inherited connection.** PR-09's initializer rule and a comment at the site.
- **The start method.** `fork` is explicit; the import has no threads before the pool is
  created. Windows runs serially.
- **Two workers build the same search.** The `FOR UPDATE` read on the search's own row
  serializes them inside the transaction, and a dead connection releases it by rollback.
  Several users requesting the same new broad search park their request slots for the
  whole build; the concurrency scenario's shared half measures it, and PR-17's warm-up
  removes the commonest case.
- **PR-13 regresses a selective default-sort search.** The harness has the shape; the PR
  reports it; the orchestrator decides between a hint and dropping the index.
- **PR-15 misses a site that resolves a category.** The grep in its design is the rule;
  the API goldens for every surface geometry request, the widget golden, and the
  triggered-table lists are the test; the new-target fixture proves the property the PR
  exists for. **PR-15 regresses the cold surface-geometry search** if the key order is
  wrong; target-first is specified and db-cold is guarded.
- **Schema PRs and production.** PR-05's guard makes `deploy_new_code_only.sh` refuse a
  release whose constant does not match the served database, before it writes.
- **The acceptance rule trips on noise.** §2.5 judges medians and p95 of a named list;
  PR-00's two-session baseline sets the floor.
- **The full-scale machine cannot host an owned server.** The shared-server fallback
  produces a valid A/B with labeled, partially cold states; the environment records what
  was in effect; `compare.py` refuses to mix the states.
- **Wall-clock.** Most PRs are full scale and run strictly in sequence; §2.3's budget and
  its rule on which PRs import twice are what keep each to a session.
- **Phase P never runs.** The plan is complete without it; the brand boundary (§1) and the
  PostgreSQL notes are what it costs to keep the option open.

---

## 7. Deferred and dropped

- **Index pruning** (item 10, second half), except `obs_files` (PR-12): deferred until a
  month of production index-usage data exists; PR-24 documents the collection.
- **Several `opus_import` processes against one schema** (items 1 to 3 as the analysis
  wrote them): superseded by the single-writer design (§1).
- **The multi-valued JSON index** (item 9 as the analysis wrote it): the junction table
  serves both the search and the count (PR-19).
- **Partitioning `search_results` or the surface geometry table** (item 11 as the analysis
  wrote it): not done (PR-11, PR-15); the reasons are in those PRs and in `§D-2.3` and
  `§D-2.4`.
- **Prebuilding the empty search inside the import** (item 17 as the analysis wrote
  it): replaced by PR-17's application-side warm-up; the import cannot compute the
  application's search hash without duplicating it. A precomputed empty-search counts
  table, filled application-side, is PR-23's second option.
- **Dynamic Django models for the per-target tables**: the fallback for PR-15, not the
  destination.
- **A one-commit-per-bundle import transaction**: dropped (§1, Transactions).
- **PostgreSQL** (Phase P): optional and last.
- **Retiring a brand** after PR-P4: a separate PR the orchestrator numbers if the decision
  calls for it.

---

## Execution notes (append-only; see §3)

Dated, naming the commit of this file they were written against, one bullet per fact.
Nothing above this line is rewritten by an executor.
