# The OPUS database design

**Scope:** the MySQL schema `opus_import` builds and `opus_app` serves, as the
performance plan (`plans/2026-10-27_database_performance_plan.md`) leaves it, and the
reasons for each departure from the schema in the tree at `3bb85f74`. The analysis that
motivates it is `critiques/2026-10-27_database_format_analysis.md`. Nothing here is
PostgreSQL-specific; the optional port described in the plan carries this same shape.

**Date:** 2026-10-28.

The design in one paragraph: `obs_general` stays the hub, one row per observation, and
every other `obs_*` table hangs off it on the hub's integer id and nothing else. The
things that are tables today because of a data value or a unit of work become rows: a
surface geometry target is a value in one table, not a table of its own; a search is a
set of rows in one shared results table, not a table of its own; a page is a range of
those rows, not a temporary table. Indexes are built once, after the load, by sort, and
composite where a query shape needs one. Every piece of per-user and per-search state
lives in the database, so any worker can serve any request.

---

## 1. Motivations

Four properties of the current schema drive the design.

**Units of work are units of DDL.** A search creates a table, a page creates a temporary
table, and the import creates a table for every target body it meets. DDL serializes on
the data dictionary, commits any open transaction, churns the table cache, and leaves an
unbounded number of tables behind. Over a network, each one is also a round trip. The
design removes DDL from the request path entirely and from the import's inner loop.

**Every row is written twice into fully indexed tables, with two foreign keys checked per
row.** The import writes a bundle into import-namespace copies of the tables, then copies
it into the permanent tables, and both sets carry every index the schema declares plus a
foreign key on both `obs_general_id` and the 50-character `opus_id`. The design writes a
fresh schema once, with only its primary and unique keys, and builds the rest afterward.

**Nearly every column is its own index and no query shape has a composite one.** The
default sort, the angular pairs, and the per-target searches each read more pages than a
composite index would. The design adds the composites the measured shapes need and prunes
nothing until production index-usage statistics exist.

**Data values are table names.** About a hundred `obs_surface_geometry__<target>` tables
exist because each target body got a table. Every one is a Django model class, so a
target the deployed code has never seen cannot be served until the models are regenerated
and the application is redeployed. The design keeps the per-target *categories*, which
the public API exposes, as data, and stores the rows in one table.

---

## 2. The schema

### 2.1 The hub

`obs_general` keeps its shape: `id` is the primary key and `opus_id` the unique key. It
gains composite keys for the query shapes that read it in order or by pair:

| Key | Serves |
|---|---|
| `(time1, opus_id)` | the default sort; with the clustered key appended it covers `SELECT id ... ORDER BY time1, opus_id` |
| `(right_asc, d_right_asc)` | the right ascension predicate, as a covering scan (the angular predicate is a modular expression and cannot be range-scanned) |
| `(declination1, declination2)` | the declination predicate, as an index range on `declination1` with `declination2` read from the index |

The two JSON list columns, `target_name` and `target_class`, stay for rendering responses.
Searching and counting on them move to junction tables (§2.5). The `preview_images` JSON
column moves to a one-to-one `obs_preview(obs_general_id, bundle_id, preview_images)`
table only if the measured ratio of its storage to the table's data length exceeds one
quarter; otherwise it stays. Every table with an `obs_general_id` column, the junction
tables of §2.5 and `obs_preview` included, carries `bundle_id CHAR(75) NOT NULL` with
`KEY (bundle_id)`, so the per-bundle delete, the duplicate OPUS id delete, and the
incremental copy reach every table the same way, per table on `bundle_id`.

### 2.2 The children

Every per-category `obs_*` table is keyed on the hub:

- `obs_general_id` is the primary key. The surrogate `id` goes; a child has exactly one
  row per observation, so the join key is the row locator and every child join is a
  unique lookup on the clustered index.
- The foreign key on `opus_id` goes, and so does the column, along with the copied
  `instrument_id`. One exception: `obs_pds.opus_id` stays as a plain keyed column because
  it is the public `opusid` field every result page shows and an autocomplete column.
- `bundle_id` stays, with its key; the import deletes and copies by bundle.
- The one foreign key, `obs_general_id → obs_general.id`, is declared at table level in
  the schema file and added in finalization, not at creation.

`obs_ring_geometry` additionally gets a composite key per longitude pair.

`obs_files` is the one child with many rows per observation. It keeps its own `id`,
`obs_general_id`, `opus_id` (the file logic reads by it), and `instrument_id`. Its
secondary indexes are reduced to the columns the application filters or sorts on, from a
code audit; it is the largest table by rows, and each unused index is a full extra copy of
a key column.

### 2.3 Surface geometry

One physical table replaces the per-target tables and the selector table:

```sql
obs_surface_geometry_target(
  target_name     INT UNSIGNED NOT NULL,   -- id in mult_obs_surface_geometry_name_target_name
  obs_general_id  INT UNSIGNED NOT NULL,
  bundle_id       CHAR(75)     NOT NULL,
  <every geometry column of the template>,
  PRIMARY KEY (target_name, obs_general_id),
  KEY (obs_general_id),
  KEY (bundle_id),
  KEY (target_name, <col>)  -- one per keyed column of the template
)
```

**Target first in the primary key**, so one target's rows are contiguous in the clustered
index as they are in a per-target table today. A two-column range search (`X1 <= max AND
X2 >= min`) uses the `(target_name, X1)` index and then probes the clustered row for
`X2`; with the observation first, each observation's several targets would interleave and
multiply the cold page reads by the mean number of targets per observation. The alias
join below is still a unique lookup, and the per-observation lookup is a covering dive on
the secondary key, which also serves the foreign key and the per-observation delete.

`target_name` is the id in the mult table that already exists for the selector field, so
every target already has an id, a label, a display order, and a grouping there. The
template declares that mult table's name in a `mult_table` key on the column, because
the `mult_<table>_<field>` spelling would give the wrong name.

**The categories stay as data.** `table_names`, `param_info`, and `partables` keep one
row per target (and per column, for `param_info`) with exactly today's names, labels,
slugs, and display orders, so `api/categories` keeps returning
`obs_surface_geometry__saturn` and every slug keeps its `SURFACEGEO<target>_` prefix.
`table_names` gains two columns:

| Column | For a category that is its own table | For `obs_surface_geometry__<target>` | For `obs_surface_geometry_name` |
|---|---|---|---|
| `physical_table` | `NULL` | `obs_surface_geometry_target` | `obs_surface_geometry_target` |
| `target_name` | `NULL` | the target's mult id | `NULL` |

The selector category `obs_surface_geometry_name` therefore survives as a row that points
at the one table with no target filter. Its field keeps the qualified name
`obs_surface_geometry_name.target_name`, which the form, the trigger logic, the mult-table
naming helper, the base-table list, and the menu code all spell out, and the mult table
keeps its name. Nothing hard-coded moves.

**Resolution in the application** is one function: a category resolves to a model, a
physical table, and an optional target id, from `table_names`. In SQL the category name
becomes the join alias:

```sql
LEFT JOIN obs_surface_geometry_target AS obs_surface_geometry__saturn
       ON obs_general.id = obs_surface_geometry__saturn.obs_general_id
      AND obs_surface_geometry__saturn.target_name = ?
```

so every column reference written as `category.column` is already correct, and a search
naming two targets joins the table twice under two aliases, as two tables did. Every site
that uses a category as a `FROM` source or a model (mult counts, range endpoints,
metadata, the per-observation lookup) goes through the same function, and the range
endpoints filter by target in both of their branches so that one target's endpoints are
never the union of all.

The import derives the target list from `SELECT DISTINCT target_name` over the data and
writes the category rows with the same labels, order, and slugs as today. Rows are
computed under the category name, so the per-target validation keeps running, and written
to the one table. Two rows of one observation that resolve to the same target write one
row, with a warning. A row whose target is unknown is not written.

**What a new target costs:** one mult row and its `table_names`, `partables`, and
`param_info` rows, written by finalization. No table is created, no model is generated,
nothing is redeployed; the worker restart that already follows every import refreshes
the per-process category caches. `models.py` loses about a hundred classes.

`obs_surface_geometry`, the per-observation `target_list` text, keeps its shape.

### 2.4 Search results

One permanent, unpartitioned table replaces the per-search `cache_NNN` tables and the
per-page temporary tables:

```sql
search_results(
  search_id       INT UNSIGNED NOT NULL,
  sort_order      INT UNSIGNED NOT NULL,
  obs_general_id  INT UNSIGNED NOT NULL,
  PRIMARY KEY (search_id, sort_order),
  UNIQUE KEY (search_id, obs_general_id)
)
```

`user_searches` keeps its unique key over the four hashes (which is what makes two
workers racing to register the same search safe) and gains `result_count` and
`results_built_at`. A page is `sort_order BETWEEN a AND b` on the join, exact because
`ROW_NUMBER()` is dense. The count is stored once. Partitioning is not used: `search_id`
is the primary-key prefix, so every per-search read is one range regardless, and the
import's truncate removes stale searches; `results_built_at` is the column a later
janitor would key on.

**The build runs once per search however many requests race for it.** Inside one
transaction, the builder reads the search's own `user_searches` row `FOR UPDATE`; a
second builder blocks on that row until the first commits, then sees `results_built_at`
set and returns. If the row is unbuilt the builder inserts `SELECT ?, ROW_NUMBER() OVER
(ORDER BY ...), obs_general.id FROM ...`, writes the count and the timestamp, and commits,
which releases the lock. The transaction contains nothing before the locking read, and
the result rows are read after it commits, so a `REPEATABLE READ` snapshot can never
predate the build. A row lock is transaction-scoped: a worker that dies releases it with
its rollback, it is the same statement on both brands, and it works through any
connection pooling. The lock wait timeout is the session's `innodb_lock_wait_timeout`,
set from `[django] search_build_timeout` (default 300 seconds) to exceed a broad cold
build. A waiter whose wait times out ends its transaction and answers with the
search-cache failure response; the build it waited on completes, and the next request
finds it.

The application's cache trusts its entries (a hash-to-id or id-to-count hit is not
re-verified), so **every reset of these two tables is followed by a cache flush**: the
import's reset step runs the application's cache flush, the deploy restarts the cache
service after it, and the benchmark harness restarts the cache it owns. Without the flush, an
entry that outlived a truncate would hand one search's rows to another once ids restart.

The cost model is stated so the right thing is measured: the build is the same sort and
the same number of inserts, now into a shared table with a secondary unique index, so the
cold build itself is expected no faster. The gains are no DDL in the request path, a
bounded table count, the stored count, and one build per search under concurrency.

If the measured re-sort number still warrants it, the set and the sort get separate keys
in `user_searches`, so a re-sort of a built set reorders its ids instead of re-evaluating
the predicate.

### 2.5 Junction tables for the list columns

Each JSON list column on `obs_general` gets a junction table written by the import from
the resolved mult ids:

```sql
obs_general_target_name (mult_id, obs_general_id, bundle_id,
                         PRIMARY KEY (mult_id, obs_general_id), KEY (obs_general_id),
                         KEY (bundle_id))
obs_general_target_class(the same shape)
```

A target search becomes a semi-join on the junction; the mult count, today a
`JSON_TABLE ... GROUP BY` over the whole result set, becomes a `GROUP BY mult_id` on the
junction joined to `search_results`. The JSON column stays for rendering. A
multi-valued JSON index is not used: it would serve the search but not the count.

### 2.6 Autocomplete

The string columns the autocomplete endpoint searches get an ngram `FULLTEXT` key beside
their B-tree, declared at table level in the schema. The query uses a quoted boolean
`MATCH ... AGAINST` for the `contains` type and prefixes of two or more characters, and
falls back to `LIKE` for one character, for the other types, and for any column where a
fixture comparison shows the two disagree. The stopword filter is off for the session
that builds the index, because the default list would drop every bigram containing `a`
or `i`.

### 2.7 Schema version

`schema_version(version INT UNSIGNED NOT NULL PRIMARY KEY)`, one row. It is written by an
explicit final import step that writes only when the row is absent and refuses to
overwrite a different value; scorched earth deletes it. The web application checks it at
startup and serves 503 on a mismatch or a missing row; both deploy scripts check the
served schema's row before running any import or migration step. A half-built schema
therefore cannot be served or promoted, and new code cannot stamp an old schema.

### 2.8 What does not change

The `mult_*` tables, `cart`, `partables`, `param_info` (its shape), the dictionary tables,
and the public API's response bodies.

---

## 3. How the schema is built

The import writes a fresh schema **directly**, in an explicit direct mode, instead of
writing an import-namespace copy and copying it:

1. **Scorched earth** drops the `obs_`, `mult_`, and `cart` tables and the
   `schema_version` row.
2. **Per bundle**, tables are created with their primary key, unique keys, and the
   `bundle_id` key only. Worker processes turn index rows into table rows; the parent
   process alone assigns ids, resolves mult values, and loads tab-separated text with
   `LOAD DATA LOCAL INFILE` in chunks of about 100,000 rows, failing on any skipped row or
   warning (the statement would otherwise ignore duplicate keys silently). Each bundle is
   deleted from the permanent tables before it is written, so a rerun is clean, and an
   OPUS id already written by an earlier bundle is deleted and re-imported.
3. **Aux tables** (`param_info`, `partables`, `table_names`) are regenerated, with the
   surface geometry categories derived from the data.
4. **Finalization** builds, by sort: `FULLTEXT` keys first, each in its own statement
   (the first one rebuilds its table); then B-tree indexes concurrently across tables,
   grouped per table within a temporary-space budget; then foreign keys serially under
   `foreign_key_checks = 0`; then `ANALYZE` with histograms on the range-searched columns.
   The step is idempotent, comparing existing keys by kind and ordered columns.
5. **The dictionary import, validation, and the version row.** Validation includes an
   orphan count per child, because finalization's foreign keys never validate existing
   rows.

An incremental import into a live schema keeps today's path: import namespace (created
without secondary indexes or foreign keys, which nothing reads before the copy), copy
under `foreign_key_checks = 0`, indexes already present. Direct mode refuses to start on a
schema that carries a version row or secondary indexes.

The import connection sets `sql_log_bin = 0` when the account may, and otherwise says so
and continues. `unique_checks` is never changed: the unique keys are how duplicates
surface.

---

## 4. How a request uses it

- **Register the search.** Hash the selections, types, units, and order; insert the
  `user_searches` row or read the existing one (the unique key resolves a race between
  workers).
- **Build if needed**, under the row lock (§2.4); otherwise read `result_count` and the
  rows that exist.
- **A page** joins `obs_general` to `search_results` on `obs_general_id` with `search_id =
  ?` and `sort_order BETWEEN ? AND ?`, then LEFT JOINs each child category on
  `obs_general_id` (a unique lookup each), with surface geometry categories aliased and
  filtered by target.
- **The fan-out** (mult counts, range endpoints, triggered tables) joins `search_results`
  the same way; mult counts on list columns group the junction table; surface geometry
  categories for one observation are one query on `obs_surface_geometry_target` ordered by
  `table_names.disp_order`.
- **Autocomplete** matches the ngram index and reads the stored count instead of counting.
- **After a deploy**, a management command issues the empty search and its fan-out through
  the application's own code path, so the first visitor finds the landing page built.

---

## 5. What the schema guarantees for a multi-worker deployment

The schema is designed so that a layout with one database server and any number of
stateless web workers needs **no later schema change**. The
properties that make that true, and the one constraint:

- **Every piece of per-user and per-search state is in the database.** The search
  registration (`user_searches`, whose unique key over the four hashes resolves a race
  between two workers registering the same search), the result rows and the stored count
  (`search_results`, `user_searches`), the cart (`cart`, keyed by session id), and Django's
  sessions (the database engine). A browser's next
  request can land on any worker and see the same search, the same page, and the same
  cart.
- **The search build serializes on a row lock inside a database transaction**; no worker
  holds anything across requests. The lock is released by rollback when a connection
  dies, identical on both brands, and unaffected by connection pooling or proxies.
- **No table is worker-local.** The design adds none, and the per-search and per-page
  tables it removes (`cache_NNN`, the temporary slices) were the only ones created from a
  request.
- **The schema version is checked by each worker process at startup**, so a worker pointed
  at the wrong schema refuses to serve; a schema switch is safe for any number of workers
  that are all restarted.
- **Constraint: one writer, no read replica on the search path.** A page read from a
  replica could miss rows the writer committed a moment earlier, and the row lock is on the
  writer. Every request that touches `search_results` or `user_searches` goes to the
  writer. Read-only aggregates over the permanent `obs_*` tables could use a replica.

Sessions and the cart live in the per-import schema, so a deploy that switches schemas
starts them empty, as it does today; a cart is keyed by `obs_general_id`, which a
re-import reassigns, so a cart cannot survive an import under this schema; keying it by
`opus_id` in a schema that outlives imports would be a schema change and a product
decision (`plans/2026-10-28_cloud_deployment_notes.md`, §4). That is the present
behavior, kept deliberately.

Everything else a multi-host deployment would need is application and operations work,
not schema: a shared cache with fully scoped keys, shared storage for cart downloads, the
holdings on every worker, a fleet deploy step, transport settings for a managed database,
and the grants such a service withholds. Those are recorded, with what was found in the
code for each, in `plans/2026-10-28_cloud_deployment_notes.md`, and are not part of the
performance plan.
