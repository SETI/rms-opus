# The OPUS database format: structure, bottlenecks, and a path to more parallelism

Date: 2026-10-27. Scope: the MySQL schema the import pipeline creates from
`src/opus_import/table_schemas/`, the way the pipeline writes it, and the way the web
application reads it. This is a static analysis of the repository at `2179d937`: the
numbers below come from the schema files, the generated models, and the golden API
responses, not from a running server. Every claim that could be measured on a populated
database says so and names the query that would measure it.

The one-paragraph version: the schema is a sound vertical partition of a very wide
observation record, and the per-search cache table is the right idea. What holds it back
is that both halves of the system turn *units of work* into *units of DDL and
single-column indexes*: a search is a `CREATE TABLE`, a page is a `CREATE TEMPORARY
TABLE`, a target body is a table, an enumerated column is a table, and nearly every
column is its own index. That design makes the import write-bound and strictly serial,
and it makes the first hit on a broad search the latency a user feels. The remedies
are mostly mechanical, and several of them unlock parallelism directly.

## 1. The model as it stands

- `obs_general` is the master table, one row per observation (the golden
  `result_count` for an unconstrained search is 1,411,270 observations). Every other
  `obs_*` table hangs off it on `obs_general_id`, one table per "Constraints" category in
  the user interface.
- Enumerated columns (`mult_idx`, `mult_list`, `flag_*`) store an integer id into a
  `mult_<table>_<column>` table. The schemas declare 89 such columns in the named
  tables, and `models.py` carries 90 `Mult*` classes.
- Surface geometry is one table **per target body**, created from a template, beside
  `obs_surface_geometry` (one row per observation, the `target_list` text) and
  `obs_surface_geometry_name` (one row per observation and target, the selector
  field); the generated models hold 101 per-target classes.
- A search becomes a `cache_NNN` table of `(sort_order, id)`; a page of results becomes
  a `TEMPORARY` slice of it; counts, mult counts, range endpoints, and triggered
  tables are all joins against it.
- The import computes every row in Python, buffers a whole index file in memory, inserts
  it into `imp_`-prefixed copies of the tables in 1000-row packets, and then copies the
  bundle into the permanent tables with `INSERT ... SELECT`.

The counts above were produced by this, run from the repository root:

```bash
python3 - <<'EOF'
import json, glob, os
D = 'src/opus_import/table_schemas/'
tot_idx = tot_cols = mults = 0
for p in sorted(glob.glob(D + 'obs_*.json')):
    cols = [c for c in json.load(open(p)) if 'field_name' in c]
    idx = sum(1 for c in cols if c.get('field_key'))
    m = sum(1 for c in cols if c['field_type'] in ('mult_idx', 'mult_list', 'flag_yesno', 'flag_onoff'))
    if p.endswith('obs_surface_geometry_target.json'):
        print('surface geo template: cols', len(cols), 'indexes', idx)
        continue
    tot_idx += idx; tot_cols += len(cols); mults += m
print('named obs tables: cols', tot_cols, 'indexes', tot_idx, 'mult columns', mults)
EOF
grep -c "db_table = 'obs_surface_geometry__" src/opus_app/apps/search/models.py
grep -c '^class Mult' src/opus_app/apps/search/models.py
```

Today it prints: 404 columns and 253 indexes across the named `obs_` tables; 85 columns
and 58 keys in the surface geometry template; 101 per-target surface geometry models;
90 mult models. So the surface geometry tables alone carry 101 × 57 ≈ 5,800 secondary
indexes (57: the template's 58 keys less its primary key), roughly twenty-three times
as many as every other `obs_` table combined.

## 2. Structural critique

### 2.1 Vertical partitioning by UI category is fine; the join keys underneath it are not

Splitting one 500-column observation into per-category tables is the right call: most
observations have rows in only a handful of them, and MySQL's row format would waste
space on NULLs otherwise. The coupling to the UI (`dev_guide_database_schema.rst`: moving
a field to another menu is a schema change) is a cost worth paying for that.

What is wrong is the key structure of the child tables. Every child table has:

- its own `id` primary key, assigned by the importer and **used by nothing**
  (`dev_guide_database_schema.rst` says so explicitly);
- a plain `KEY` on `obs_general_id`, which is the column every join uses;
- `opus_id char(50)`, `bundle_id char(75)`, and (in eleven of the twenty-one children)
  `instrument_id char(60)`, each duplicated from `obs_general`; the first two are
  indexed (`bundle_id` by its own key, `opus_id` by the index its foreign key
  creates), `instrument_id` is keyed only in `obs_general`;
- **two** foreign keys to `obs_general` — one on `obs_general_id` and one on the
  50-character `opus_id` — both `ON UPDATE CASCADE`, in every child `obs_*` schema
  (`grep -l '"field_key_foreign"' src/opus_import/table_schemas/obs_*.json` lists them).

Consequences:

1. InnoDB clusters a table on its primary key. A child table clustered on a meaningless
   `id` means the `obs_general_id` lookup is a secondary-index probe followed by a
   clustered-index probe, for every child table in every page of results.
2. Because `obs_general_id` is not declared `UNIQUE` in the children, the optimizer
   cannot know the relationship is 1:1. It therefore cannot eliminate a `LEFT JOIN`
   whose columns are not selected, and it must keep a "found one, keep looking" loop on
   every join.
3. The three redundant string columns cost up to 185 bytes per row per table (the `char`
   columns are stored variable-length under utf8mb4) plus two indexes per table. Over 123
   tables (22 named plus 101 per-target) that is the single largest contributor to index
   count outside surface geometry. The documented justification
   (`dev_guide_database_schema.rst`: "one can readily delete all metadata from a
   particular instrument without needing to join tables together") is not what the import
   relies on: its delete and copy steps filter on `bundle_id` alone, and only because they
   are done per table rather than by a cascading foreign key.
4. The `opus_id` foreign key is pure overhead: it is implied by the `obs_general_id`
   key, it forces a 200-byte index into every child, and it is checked row by row on
   every `INSERT ... SELECT` during the import-to-permanent copy.

**Fix:** make `obs_general_id` the primary key of every child table (dropping `id`),
keep one foreign key, and drop `opus_id` and `instrument_id` from the children. Keep
`bundle_id` if the per-bundle delete is wanted, or replace it with `ON DELETE CASCADE`
from `obs_general` so one `DELETE` does all 123 tables. The child rows then sit in
`obs_general` order, so the result-page join becomes a sequence of clustered lookups
with good locality.

### 2.2 "Index every column" is write amplification with little read payoff

`dev_guide_database_schema.rst` states the policy: every metadata column gets an index
until the 64-per-table limit forces exceptions. The schema format can only express
**single-column** keys (`field_key` is per column; the `constraint` escape hatch exists
but is used for three `UNIQUE` constraints and never for a composite index).

For the searches OPUS actually runs, single-column indexes on `double` columns are the
wrong shape:

- A dual-column range search (`dbmin <= usermax AND dbmax >= usermin`) touches two
  columns. MySQL will use one index, or an `index_merge`, and then filter; two separate
  indexes do not help it much more than one.
- The default sort is `time1, opus_id`. An index on `time1` alone cannot deliver that
  order without a filesort for ties; a composite `(time1, opus_id)` can, and would make
  the empty search's cache build a pure index walk.
- A longitude search uses the midpoint and half-span columns together; they are indexed
  separately.
- Every secondary index is maintained on every insert during import. The InnoDB change
  buffer softens non-unique index maintenance, but 5,800 indexes is 5,800 B-trees to
  build and keep in the buffer pool.

**Fix:** let the schema declare composite indexes (an `index` entry alongside
`constraint`), add the handful that match real query shapes, and then prune using
evidence from the production server rather than from intuition:

```sql
SELECT * FROM sys.schema_unused_indexes WHERE object_schema = DATABASE();
SELECT object_name, index_name, count_read, count_write
  FROM performance_schema.table_io_waits_summary_by_index_usage
 WHERE object_schema = DATABASE() ORDER BY count_write DESC LIMIT 50;
```

Run after a month of traffic, those two queries will say which of the 5,800 indexes
have never been read.

### 2.3 One table per surface geometry target is partitioning by data value

The 101 `obs_surface_geometry__<target>` tables are the same 85-column shape with a
different name. This has three costs:

- Discovering a new target during import requires creating a table, regenerating
  `models.py`, and adding `partables` and `table_names` rows. The table set is
  open-ended by construction.
- "Which bodies are in this observation?" is a probe of 101 tables
  (`api_get_categories_for_opus_id`).
- 101 × 57 indexes and 101 `.ibd` files for data that is one logical relation.

**Fix:** one `obs_surface_geometry_target` table (`obs_surface_geometry` and
`obs_surface_geometry_name` are taken by the target list and the selector) with a
`target_id` column and primary key `(obs_general_id, target_id)`. If per-target locality
matters for the "Saturn Surface Geometry" searches, use MySQL `PARTITION BY LIST
(target_id)`; the optimizer prunes to one partition when `target_id` is constrained, which
it always is in the UI (the "Surface Geometry Target Selector" is mandatory for those
fields). The slug scheme (`<SLUGTARGET>` substituted into field names) can stay as a
presentation layer over a `WHERE target_id = ?` clause.

### 2.4 `mult_list` columns are unindexed JSON

`target_name` and `target_class` on `obs_general` are JSON arrays of mult ids, searched
with `JSON_CONTAINS` and sorted on `JSON_EXTRACT(col, '$[0]')`. There is no index on
either, so **a search on target name — among the most common searches OPUS gets — is a
full scan of `obs_general`**, 1.4 million rows. The mult-count query for these fields
explodes the array with `JSON_TABLE` and joins the cache table, another full pass.

Two fixes, either sufficient:

- MySQL 8.0.17+ multi-valued indexes. The schema already requires 8.0.19.
  `ALTER TABLE obs_general ADD INDEX target_name_mv ((CAST(target_name AS UNSIGNED
  ARRAY)))` lets `MEMBER OF`, `JSON_CONTAINS`, and `JSON_OVERLAPS` use the index. This
  is a one-line change to `create_table` for `mult_list` columns and a one-line change
  in `sql_builder.json_contains` to prefer `MEMBER OF`.
- A junction table `obs_general_target (target_id, obs_general_id)` with the primary key
  on both columns, target first, and a second key on `obs_general_id` (a composite key
  serves lookups by its leading column only). More conventional, and the mult count
  becomes a plain `GROUP BY` without `JSON_TABLE`. Costs a join on display.

### 2.5 `preview_images` widens the master row

`obs_general.preview_images` is a JSON blob of a `PdsViewSet` carried on every master
row so the gallery needs no join. The trade is reasonable for the gallery and bad for
everything else: every join through `obs_general` — every search, every count, every
mult count — reads a clustered row that carries the blob (InnoDB stores JSON inline
until it overflows the page). Measure before moving it:

```sql
SELECT AVG(LENGTH(preview_images)), MAX(LENGTH(preview_images)) FROM obs_general;
SELECT table_name, data_length, index_length FROM information_schema.TABLES
 WHERE table_schema = DATABASE() ORDER BY data_length + index_length DESC LIMIT 20;
```

If the average is in the hundreds of bytes, move it to `obs_preview (obs_general_id PK,
preview_images)` and join it only in `api_get_data_and_images`.

### 2.6 Ninety tiny `mult_` tables and an unbounded number of `cache_` tables

Each `mult_` table is a legitimate lookup table, but ninety copies of one shape
(`table_schemas/mult_template.json`) share these problems:

- **Two columns are dead.** Nothing reads `aliases`; no observation class supplies one
  (`obs/field_types.py` says so), and the generated models omit it. Nothing reads
  `timestamp`.
- **`group_disp_order` describes a group but is stored on every row of it.** The widget
  orders `distinct()` groups by it, so a group whose rows disagree is listed twice.
- **`disp_order` is a string computed once, when a value is first seen**, by
  `do_import_mult.update_mult_table`, from the values already present. The same data
  imported in another bundle order can produce another widget order. Negative numbers
  sort wrongly under both padded formats it uses:

  ```text
  unit columns   : -5, -10, 3, 10
  plain numbers  : 3, -5, 10, -10
  ```

  The widget sorts the key in SQL under a case-insensitive collation, while
  `api_get_mult_counts` sorts it in Python case-sensitively, so the two can disagree.
  Ties have no tiebreaker, positions are forced with `zzz`, `zzy`, `zzx`, `zzAYes`, and
  `zzBNo` prefixes and one `'!Cassini'`, and the absent-value rule is skipped for a
  column with a unit.
- **Values outlive their observations.** A bundle delete never touches the mult tables,
  and a value that already exists keeps its first label when a later import computes
  another. The search form lists every row with `display = 'Y'`, so it offers values no
  observation has; selecting one returns nothing, and the counts, which group the data,
  show nothing for it.
- **Every mult id is a four-byte `int unsigned`** in every observation column.

The `cache_NNN` tables are worse: one real InnoDB table per distinct search,
never dropped until the next import. On a busy site that is tens of thousands of tables
and `.ibd` files between deploys. Table count pressures `table_open_cache` and
`table_definition_cache`, bloats the data dictionary, and makes `inspectdb`-style
tooling refuse to run (the models script checks for exactly this).

See §4.1 for the replacement; it is the single most valuable web-side change.

### 2.7 Things that are right and should stay

- Storing a longitude's midpoint and half-span alongside its endpoints, so the wrap
  search is two comparisons. Give the pair a composite index.
- Times as ET doubles, clock counts as doubles: sortable, indexable, convertible on
  the way out.
- `user_searches` keyed by four MD5 hashes with `'NONE'` sentinels, and the optimistic
  insert that lets the unique key pick a winner. This is how to deduplicate under
  concurrency.
- `param_info`, `table_names`, and `partables` as data rather than code.
- The `sql_builder` discipline — identifiers validated and quoted, values always bound.

## 3. The import: why it is slow and why it cannot run in parallel today

### 3.1 It is CPU-bound in Python, one process, one row at a time

`import_one_index` (`steps/do_import_index.py`) walks every index row, and for each row
and each table calls `import_observation_table`, which calls one
`field_<table>_<column>` method per column through `getattr` dispatch. For a Cassini ISS
observation that is on the order of 400 Python method calls plus validation per row,
before surface geometry multiplies it by the number of bodies in view. `import_all`
runs the bundle sets in sequence, one `opus_import` subprocess each. Nothing overlaps.

A `cProfile` of one mid-sized bundle (`python -m cProfile -o prof -m opus_import
--import <bundle>`) would confirm the split; the expectation from reading is that the
database is idle most of the time and the Python interpreter is the bottleneck.

### 3.2 Three shared counters make concurrent imports unsafe

If two `opus_import` processes ran at once they would corrupt each other, for three
reasons, all of which are coordination problems rather than database limits:

1. **Row ids are allocated in Python.** `MAX_ID` reads `MAX(id)` from both namespaces
   once per bundle (`import_util.find_max_table_id`, cached in
   `ctx.max_table_id_cache`, which is emptied at the start of each bundle) and then
   counts up. Two processes get the same starting
   point and collide.
2. **Mult ids are allocated in Python.** `update_mult_table` appends
   `max(id) + 1` to an in-memory copy of the mult table and `upsert_rows` it at the end
   of the index. Two processes that each discover a new target name assign the same id
   to different values; the upsert then silently keeps one of them.
3. **One import namespace.** Every process writes to the same `imp_` tables; the
   "drop old import tables" and "copy bundle to permanent" steps assume they own them.

The determinism requirement — `table_names()` must sort so "a caller handing out row
ids while iterating this would otherwise produce a different database on a different
machine" — is worth keeping, and every fix below keeps it.

### 3.3 The write path fights InnoDB

- `insert_rows` sends 1000-row `INSERT`s, and `_execute` commits each one
  (`importdb/super.py:_execute` opens a cursor and commits). With the default
  `innodb_flush_log_at_trx_commit=1` each commit is a log fsync.
- The import tables are created with every secondary index already present, so each
  insert maintains up to 58 B-trees per table. Building an index after the load is a
  sort; maintaining it during the load is a random insert per row per index.
- Every child table carries two foreign keys, checked per row, and the `opus_id` one
  compares 50-character strings.
- The permanent copy is `INSERT INTO obs_x SELECT * FROM imp_obs_x WHERE bundle_id = ?`,
  one table at a time, again into fully indexed tables with foreign keys on. A
  scorched-earth rebuild therefore inserts the whole database twice, serially.
- `mult_table_lookup_id` is a linear scan of the mult table's rows for every value of
  every row (`for entry in mult_table: if entry['value'] == val`). For target names
  that is hundreds of comparisons per observation. A `dict` keyed by value fixes it in
  five lines.

## 4. The web application: where the latency is

### 4.1 A search is DDL

`get_user_query_table` runs `CREATE TABLE cache_NNN (...) SELECT obs_general.id FROM
obs_general LEFT JOIN ... WHERE ... ORDER BY ...`. For a broad search this materializes
a million-row table, builds a unique index on `id`, and sorts — that is the latency a
user feels on the first keystroke of a search the site has not seen. Three properties
make it worse than it needs to be:

- The sort order is part of the search's identity (`order_hash` is in the unique key),
  so changing the sort of the same result set re-runs the search and builds another
  table.
- DDL takes InnoDB data-dictionary locks and syncs the tablespace file. Concurrent
  identical searches serialize on the table lock by design; concurrent *different*
  searches still contend on the dictionary.
- Every page view then runs `CREATE TEMPORARY TABLE temp_cache_NNN_<pid>_<time> AS
  SELECT sort_order, id FROM cache_NNN ORDER BY sort_order LIMIT ? OFFSET ?` and drops
  it. That is a second DDL statement per request on the busiest endpoint.

**Fix:** one table, no DDL in the request path.

```sql
CREATE TABLE search_results (
  search_id  INT UNSIGNED NOT NULL,
  sort_order INT UNSIGNED NOT NULL,
  id         INT UNSIGNED NOT NULL,
  PRIMARY KEY (search_id, sort_order),
  UNIQUE KEY (search_id, id)
) PARTITION BY HASH (search_id) PARTITIONS 64;

INSERT INTO search_results
SELECT ?, ROW_NUMBER() OVER (ORDER BY obs_general.time1, obs_general.opus_id), obs_general.id
  FROM obs_general LEFT JOIN ... WHERE ...;
```

`ROW_NUMBER()` (8.0) replaces the `AUTO_INCREMENT`-follows-`INSERT ... SELECT ... ORDER
BY` behavior the current design depends on, which works but is not something the SQL
standard promises. The page slice becomes a derived table — `JOIN (SELECT id,
sort_order FROM search_results WHERE search_id = ? ORDER BY sort_order LIMIT ? OFFSET ?)
AS page ON page.id = obs_general.id` — which MySQL materializes internally with no DDL.
`user_searches` grows a `result_count` column written from `ROW_COUNT()` at build time,
so the count endpoint never scans. Stale searches are deleted by `search_id` in a
janitor, or — if partitioned by `search_id` range instead of hash — dropped a partition
at a time.

A second, independent gain: separate the *set* from the *order*. Hash
`selections + qtypes + units` to a result set, and `order` to a sort of that set. Re-sorting
a known set is `INSERT ... SELECT ... FROM search_results JOIN obs_general ... ORDER BY`,
a sort of the matching ids rather than a re-evaluation of the predicates over the whole
database.

### 4.2 The fan-out after a search contends on eight sync workers

After a search the interface fires, in parallel: the count, `dataimages`, one
`mults/<slug>` per open checkbox widget, one `range/endpoints/<slug>` per open range
widget, and `categories`. Each is a separate request and each joins the cache table.
The documented servers run 8 gunicorn sync workers, or 4 × 2 mod_wsgi threads, so a
single user's search can occupy every worker, and a second user waits. Meanwhile each
request pays for a fresh MySQL connection: `settings.DATABASES` sets no `CONN_MAX_AGE`,
so Django opens and closes one per request.

Smaller costs on the same path, each a database round trip per request:

- `_valid_regex` asks the server whether a regular expression compiles.
- `get_triggered_tables` iterates `Partables.objects.all()` and then
  `TableNames.objects.filter(...)`, two queries over tables that change only at import.
- `api_get_mult_counts` resolves labels with one `mult_model.objects.get(id=...)` per
  distinct value returned — an N+1 — rather than one `filter(id__in=...)`.
- `api_string_search_choices` runs `COUNT(*)` over the cache table on every keystroke
  before deciding which strategy to use; `user_searches.result_count` would answer it.

### 4.3 Autocomplete is `LIKE '%x%'`

The string-choice query is `SELECT DISTINCT col ... WHERE col LIKE '%text%' ORDER BY col
LIMIT n`, guarded by a 500 ms `MAX_EXECUTION_TIME`. A leading wildcard cannot use a
B-tree index, so the guard is what makes this endpoint survivable, and it fails
toward "no suggestions." A `FULLTEXT` index on the string columns that offer
autocomplete (there are not many — `obs_pds.product_id`, `data_set_id`,
`primary_filespec`, a few mission-specific ones) turns `contains` into
`MATCH ... AGAINST` with an index, and `begins` already works with a prefix `LIKE`.
The index must use the ngram parser: the default parser tokenizes by word, drops short
and stop words, and matches a wildcard only at the start of a word, so it would lose
choices the substring `LIKE` finds, and an equivalence test against today's results
belongs with the change.

## 5. Recommendations, in the order to do them

Each entry says what it changes, what it costs, and what it unlocks. The parallelism
wins are marked. Where an open issue asks for the same thing, its number follows the
heading; several of the import entries also appear on the wishlist recorded in #1473.

### Import

1. **Allocate ids per bundle, not per process.** Give each bundle a fixed id block —
   `bundle_number * 2^24 + row_number`, both zero-based, with the bundle number taken
   from the sorted bundle list; `obs_general.id` is `uint4`, so this holds up to 256
   bundles of up to 2^24 rows, and the import refuses a bundle list or a bundle beyond
   those bounds — or reserve a block atomically from a one-row `id_sequence` table
   (`UPDATE id_sequence SET next = LAST_INSERT_ID(next + ?)`) at the start of each
   bundle. The first is deterministic given the same bundle list; the second guarantees
   uniqueness only, because blocks go out in lock-acquisition order. **Unlocks:** running
   N `opus_import` processes on disjoint bundle sets at once.
2. **Resolve mult values to ids in a single finalizer.** Workers write the *value
   string* (or a per-worker provisional id plus the string) into the import rows; a
   final serial step assigns ids in sorted-value order and rewrites the columns, or
   workers `INSERT IGNORE` values into the shared import `mult_` table and read back
   the id by value; that needs a unique key on `value` (the template declares none
   today) and a defined rule for the null value. The first keeps ids reproducible; the
   second is simpler. **Unlocks:** the same N-process import without the id collision
   in §3.2.
3. **One import prefix per worker.** The namespace machinery exists
   (`import_prefix`); make it `imp_<worker>_` and teach the copy step to walk every
   worker's namespace. **Unlocks:** item 1 and 2 without touching the step logic.
4. **Parallelize inside a bundle.** The per-row loop reads an immutable index row and
   writes to a dict; `multiprocessing.Pool.imap` over chunks of rows, each worker
   holding its own obs class instance, preserves row order and returns `(table_rows,
   discovered_mult_values, log_messages)` per chunk for the parent to merge. This is
   the biggest wall-clock win for a single large bundle because §3.1 says the Python
   is the bottleneck, and it needs items 1 and 2 only for the ids and mults inside the
   chunk results, which the parent can assign after merging.
5. **Load like a bulk loader.** `autocommit = 0` with one commit per bundle; `SET
   foreign_key_checks = 0, unique_checks = 0` for the duration; write each table's
   rows to a CSV in the scratch directory and `LOAD DATA LOCAL INFILE` it (several
   times faster than multi-row `INSERT`); create the import tables **without**
   secondary indexes and add them after the load in one `ALTER TABLE ... ADD INDEX
   ..., ADD INDEX ...` statement (InnoDB sorts; 8.0.27+ builds in parallel with
   `innodb_ddl_threads`). Set `innodb_flush_log_at_trx_commit = 2` on the import
   server for the run. Re-enabling the checks does not scan existing rows, so a
   schema loaded this way is validated before it is served: an anti-join orphan count
   per child for the foreign keys, and the unique-key probe of `opus_id` for the
   duplicates (#584 asks for the integrity checks to live in `--validate-perm`).
6. **Copy tables in parallel, or stop copying** (#1253). The import-to-permanent copy is one
   independent `INSERT ... SELECT` per table after `obs_general`; a thread pool of
   connections does them concurrently. Better: the deploy chain already builds into a
   fresh schema and switches with a symlink, which provides the same "nothing the
   public sees changes until the end" guarantee the two-namespace design exists for.
   Writing the permanent tables directly in a fresh schema, and keeping the `imp_`
   path only for incremental re-imports into a live schema, halves the write volume of
   a full rebuild.
7. **Make `mult_table_lookup_id` a dictionary lookup.** Five lines, no risk.

### Schema

8. **Rekey the child tables on `obs_general_id`** (§2.1): primary key, one foreign
   key, drop `id`, `opus_id`, and `instrument_id` from children. Requires regenerating
   `models.py` and touching `search_cache_join_condition`, `add_obs_table_joins`, and
   the delete-by-bundle step. **Payoff:** every join in the application; the sort-page
   join in particular.
9. **Multi-valued indexes on `mult_list` columns** (§2.4): one branch in
   `create_table`, `MEMBER OF` in `sql_builder`. **Payoff:** target searches stop
   scanning `obs_general`.
10. **Let the schema declare composite indexes, add `(time1, opus_id)`,
    `(right_asc, d_right_asc)`, and the ring-geometry longitude pairs, then prune the
    single-column indexes the production server says are unused** (§2.2). The pruning
    step is the one that needs a month of `performance_schema` data first.
11. **Collapse surface geometry into one partitioned table** (§2.3; #334). The largest
    schema change on the list and the one with the most moving parts (slugs,
    `partables`, `models.py`, the obs class template); do it after 8 and 10 have shown
    their effect so its payoff is measurable in isolation.
12. **Measure `preview_images`, and move it if it is wide** (§2.5).

### Web application

13. **Replace per-search tables with `search_results`** (§4.1; #350, #665) and the per-page
    temporary table with a derived table. Removes DDL from the request path, bounds
    the table count, and makes concurrent searches contend on row locks instead of
    dictionary locks. Store `result_count` in `user_searches` at build time.
14. **Separate the result set from its order** (§4.1, second paragraph), so re-sorting
    is a sort of ids rather than a re-search.
15. **Run the workers for I/O, not CPU.** The handlers wait on MySQL; `gunicorn
    --workers 4 --threads 8 --worker-class gthread` (or uWSGI `threads = 8`) lets one
    user's fan-out of a dozen requests proceed together, and `CONN_MAX_AGE = 300`
    stops each one from paying a connection handshake. Both are configuration.
16. **Cache the per-import constants in process:** `Partables`, `TableNames`, and the
    mult label maps, loaded once per worker like `_PARAMINFO_CACHE` already is. Fix
    the N+1 in `api_get_mult_counts`.
17. **Precompute the no-selection answers at import.** The mult counts, range
    endpoints, and triggered tables for an empty search are constants between
    imports; a finalization step can write them into a table the application reads
    instead of running `GROUP BY` over 1.4 million rows the first time each worker is
    asked.
18. **`FULLTEXT` on the autocomplete columns** (§4.3; #1301).

### Server

19. **Size the buffer pool to the working set** — `information_schema.TABLES` gives the
    number — and confirm `innodb_parallel_read_threads` is at its default or above; it
    parallelizes the clustered-index scans and `COUNT(*)` that the broad-search cache
    build and the empty-search count do.
20. **If a bigger step is ever on the table, it is PostgreSQL, and the stub for it is
    already in the tree** (#352). Parallel query execution, partial and covering indexes, GIN
    indexes on integer arrays (the natural type for `mult_list`), `COPY` for bulk load,
    and `UNLOGGED` tables for search results would address §2.2, §2.4, §3.3, and §4.1
    with features rather than workarounds. It is a large migration; it is listed here
    because every other recommendation on this list is also true of a PostgreSQL port,
    and nothing here depends on staying with MySQL except item 9's exact syntax.

### Lookup values

21. **One mult table with a computed display rank** (§2.6). Replace the per-column
    tables with one keyed `(field, id)`, drop the dead columns, move the group order to
    a group table, compute an integer display rank per field at the end of every import
    from typed values, delete values nothing references except where the schema lists
    the choices, and narrow the ids if the largest field allows. Results sorted by a
    mult column keep sorting by label text. **Payoff:** a widget order that does not
    depend on import order, a search form that offers only values with results, and
    ninety fewer models.

## 6. What to measure first

Because this is a reading of the code, four measurements would turn the ranking above
from reasoned to demonstrated:

1. `cProfile` of one bundle import (§3.1): the Python-versus-database split decides
   whether item 4 or item 5 comes first.
2. `information_schema.TABLES` sizes per table (§2.5, §5.19): decides the buffer pool
   and whether `preview_images` matters.
3. `sys.schema_unused_indexes` after a month (§2.2): decides which indexes go.
4. The slow query log with `long_query_time = 1` for a week, grouped by statement
   shape: expected to be dominated by `CREATE TABLE cache_` and `JSON_CONTAINS` on
   `obs_general`, which is items 13 and 9.
