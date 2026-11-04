# The OPUS database design

**Scope:** the MySQL schema `opus_import` fills and `opus_app` serves, as the
performance plan (`plans/2026-10-27_database_performance_plan.md`) leaves it, and the
reasons for each departure from the schema in the tree at `2179d937`. The analysis that
motivates it is `critiques/2026-10-27_database_format_analysis.md`. Nothing here is
PostgreSQL-specific; the optional port described in the plan carries this same shape.

**Date:** 2026-10-28.

The design in one paragraph: `obs_general` stays the hub, one row per observation, and
every other `obs_*` table hangs off it on the hub's integer id and nothing else. The
things that are tables today because of a data value or a unit of work become rows: a
surface geometry target is a value in one table, not a table of its own; a search is a
set of rows in one shared results table, not a table of its own; a page is a range of
those rows, not a temporary table. Indexes are created once, after the load, by sort, and
composite where a query shape needs one. Every piece of per-user and per-search state
lives in the database, so any worker can serve any request.

**Terms.** A **search build** writes a search's matching observations into `search_results`
in sort order, the first time the search is requested; later requests read those rows,
and the request doing it is the **search builder**. An import into a schema
with no version row is a **fresh import**, which creates the tables with only their
primary and unique keys and builds the other indexes once at the end; an import into a
finished schema is an **append**. An **index build** is the creation of secondary indexes.

---

## 1. Motivations

Five properties of the current schema drive the design.

**Units of work are units of DDL.** A search creates a table, a page creates a temporary
table, and the import creates a table for every target body it meets. DDL serializes on
the data dictionary, commits any open transaction, churns the table cache, and leaves an
unbounded number of tables behind. Over a network, each one is also a round trip. The
design removes DDL from the request path entirely and from the import's inner loop.

**Every row is written twice into fully indexed tables, with two foreign keys checked per
row.** The import writes a bundle into import-namespace copies of the tables, then copies
it into the permanent tables, and both sets carry every index the schema declares plus a
foreign key on both `obs_general_id` and the 50-character `opus_id`. The design writes a
fresh schema once, with only its primary and unique keys, and creates the rest afterward.

**Nearly every column is its own index and no query shape has a composite one.** The
default sort, the angular pairs, and the per-target searches each read more pages than a
composite index would, and most single-column keys are never read: in 28 days of
production traffic, most of the secondary-index bytes on the permanent tables belonged to
keys that were not read once. The design adds the composites the measured shapes need and
drops the keys production never read, keeping those the import needs.

**Data values are table names.** About a hundred `obs_surface_geometry__<target>` tables
exist because each target body got a table. Every one is a Django model class, so a
target the deployed code has never seen cannot be served until the models are regenerated
and the application is redeployed. The design keeps the per-target *categories*, which
the public API exposes, as data, and stores the rows in one table.

**Lookup values are one table per column, ordered by a string.** Each enumerated column
has its own `mult_` table and Django model. Its display order is a string computed once,
when a value is first seen, so it depends on the order bundles were imported and sorts
negative numbers wrongly, and a value whose observations are deleted stays in the search
form. The design keeps one table with an integer rank recomputed at the end of every
import, and removes values nothing references.

---

## 2. The schema

The tables and how they relate. `obs_mission_x` and `obs_instrument_x` stand for the
per-mission and per-instrument tables, which keep their shape apart from the key change
of §2.2. Row counts and sizes are left out on purpose: the plan states a number only when
its harness has measured it.

```mermaid
erDiagram
  obs_general ||--o| obs_pds : "obs_general_id"
  obs_general ||--o| obs_ring_geometry : "obs_general_id"
  obs_general ||--o| obs_wavelength : "obs_general_id"
  obs_general ||--o| obs_mission_x : "obs_general_id (one per mission)"
  obs_general ||--o| obs_instrument_x : "obs_general_id (one per instrument)"
  obs_general ||--o| obs_surface_geometry : "obs_general_id"
  obs_general ||--o{ obs_surface_geometry_target : "obs_general_id"
  obs_general ||--o{ obs_files : "obs_general_id"
  obs_general ||--o{ obs_general_target_name : "obs_general_id"
  obs_general ||--o{ obs_general_target_class : "obs_general_id"
  obs_general ||--o| obs_preview : "obs_general_id (gated)"
  mult_field ||--o{ mult : "field_id"
  mult_field ||--o{ mult_group : "field_id"
  mult ||--o{ obs_surface_geometry_target : "target_name = mult id"
  mult ||--o{ table_names : "target_name (category rows)"
  user_searches ||--o{ search_results : "search_id"
  obs_general ||--o{ search_results : "obs_general_id"
  table_names ||--o{ param_info : "category_name"
  table_names ||--o{ partables : "partable"

  obs_general {
    uint id PK
    char50 opus_id "plain key; the duplicate step keeps it unique"
    char75 bundle_id "key; the per-bundle steps join on it"
    real8 time1 "key (time1, opus_id)"
    real8 right_asc "key (right_asc, d_right_asc)"
    real8 declination1 "key (declination1, declination2)"
    json target_name "mult_list, kept for rendering"
    json target_class "mult_list, kept for rendering"
  }
  obs_pds {
    uint obs_general_id PK "FK added in finalization"
    char50 opus_id "public opusid field, plain key"
    char75 bundle_id "public bundleid field, plain key"
  }
  obs_surface_geometry_target {
    usmallint target_name PK "mult id; PK (target_name, obs_general_id)"
    uint obs_general_id PK "key (obs_general_id)"
    real8 center_distance1 "key (target_name, center_distance1, center_distance2)"
  }
  obs_files {
    uint obs_general_id PK "PK (obs_general_id, file_number); FK added in finalization"
    usmallint file_number PK "the file's position within its observation"
    char50 opus_id "kept: file_utils reads it"
    char60 instrument_id "kept"
  }
  obs_general_target_name {
    usmallint mult_id PK "PK (mult_id, obs_general_id)"
    uint obs_general_id PK "key (obs_general_id)"
  }
  search_results {
    uint search_id PK "PK (search_id, sort_order)"
    uint sort_order PK
    uint obs_general_id "UK (search_id, obs_general_id); the cart range editor probes it"
  }
  user_searches {
    uint id PK
    binary32 search_hash UK "SHA-256 of the canonical search"
    uint result_count
    datetime results_built_at
    datetime last_used_at "refreshed daily; the pruner reads it"
  }
  table_names {
    char60 table_name "category name, as the API shows it"
    char60 physical_table "NULL, or obs_surface_geometry_target"
    usmallint target_name "NULL, or the target's mult id"
  }
  schema_version {
    uint version PK
    enum state "ready or appending; only the version step writes ready"
  }
  import_bundle {
    usmallint bundle_number PK "registration order"
    varchar75 bundle_id UK
    uint first_id "the bundle's id range"
    enum state "pending, importing, done, failed; key (state, size_estimate, bundle_number)"
  }
  mult_field {
    usmallint field_id PK
    varchar100 qualified_name "UK; e.g. obs_general.planet_id"
    tinyint pinned "the schema lists the choices"
    usmallint last_id "the highest id handed out; new ids come from it"
  }
  mult {
    usmallint field_id PK "PK (field_id, id)"
    usmallint id PK
    varchar100 value "UK (field_id, value); '' for absent, never NULL"
    varchar100 label
    usmallint pin "optional fixed position"
    usmallint disp_rank "recomputed every import"
    enum display
    varchar100 grouping
  }
  mult_group {
    usmallint field_id PK "PK (field_id, grouping)"
    varchar100 grouping PK
    usmallint group_pin
    usmallint group_rank
  }
```

### 2.1 The hub

`obs_general` keeps its shape: `id` is the primary key, and `opus_id` has a plain key,
because finalization, not a unique key, keeps OPUS ids unique (§3). It
gains composite keys for the query shapes that read it in order or by pair:

| Key | Serves |
|---|---|
| `(time1, opus_id)` | the default sort; with the clustered key appended it covers `SELECT id ... ORDER BY time1, opus_id` |
| `(right_asc, d_right_asc)` | the right ascension predicate, as a covering scan (the angular predicate is a modular expression and cannot be range-scanned) |
| `(declination1, declination2)` | the declination predicate, as an index range on `declination1` with `declination2` read from the index |

`obs_ring_geometry` gains the same kind of key, `(<col>, d_<col>)`, for each of its longitude
pairs, a covering scan for the same modular predicate.

**Which columns keep a key.** A single-column key costs a copy of its column and a write
per row, so it stays only when something reads it. It goes when production never read it
in 28 days of production index statistics (the plan's §1, Index pruning); when it leads a composite above (`time1`,
`right_asc`, `declination1`, and each ring longitude), since the composite serves it; or
when nothing can read it (neither searchable nor shown in results, and named by no code).
It stays, whatever production shows, when the import or a code path the web traffic does
not exercise reads by it (`obs_general.bundle_id` is the import's), when a foreign key
needs it, on every autocomplete column, whose prefix match reads it, when the other column of its `1`/`2` pair keeps one, and on two columns kept by
choice. Two `obs_general` columns go altogether: `primary_filespec`, which duplicates
`obs_pds.primary_filespec`, and `ring_obs_id`, with the old-format ids the API accepted. The surface geometry table keeps a key on every keyed template column (§2.3). A search on a
column without a key still answers, by a scan; the plan re-collects the statistics on
the new schema to find any search that needs one back.

The two JSON list columns, `target_name` and `target_class`, stay for rendering responses.
Searching and counting on them move to junction tables (§2.5). The `preview_images` JSON
column moves to a one-to-one `obs_preview(obs_general_id, preview_images)` table only if
the measured ratio of its storage to the table's data length exceeds one quarter;
otherwise it stays.

**The import finds a bundle's rows through `obs_general` alone**, by its `bundle_id`
key. `obs_pds` also stores `bundle_id`, because it is the public `bundleid` field (§2.2),
and the import writes both from the same bundle; validation checks that they agree. Every
other table the import writes per observation (the remaining children, the junction tables
of §2.5, `obs_preview`, and the surface geometry table) reaches its bundle through
`obs_general_id`, so the per-bundle delete, the incremental copy, and the schema clone of
§3.1 join each table to `obs_general`'s bundle key, and the duplicate step deletes by
`obs_general_id`. A table whose primary key does not start with `obs_general_id` (the
surface geometry table and the junction tables) is created with its `obs_general_id`
key, even in a fresh import, so that join reads a range of that key and never scans the
table. No table carries a 75-character column and an index for
the import's sake. `search_results` and `cart` also carry `obs_general_id` but are not
imported: the import resets `search_results` (§2.4) and re-creates `cart` empty (§3).

### 2.2 The children

Every per-category `obs_*` table is keyed on the hub:

- `obs_general_id` is the primary key. The surrogate `id` goes; a child has exactly one
  row per observation, so the join key is the row locator and every child join is a
  unique lookup on the clustered index.
- The foreign key on `opus_id` goes, and so does the column, along with the copied
  `instrument_id`, and the copied `bundle_id`. Two exceptions: `obs_pds` keeps `opus_id`
  and `bundle_id` as plain keyed columns because they are the public `opusid` and
  `bundleid` fields, shown on result pages and searched, and `obs_files` keeps `opus_id`
  and `instrument_id` (below).
- A bundle's rows in a child are found by joining `obs_general` on `obs_general_id`
  (§2.1); the join is a range on `obs_general`'s bundle key followed by primary-key
  lookups in the child.
- The one foreign key, `obs_general_id → obs_general.id`, is declared at table level in
  the schema file and added in finalization, not at creation.

`obs_ring_geometry` additionally gets a composite key per longitude pair.

Three tables have many rows per observation: the surface geometry table, one per target
(§2.3); the junction tables, one per listed value (§2.5); and `obs_files`, one per file.
`obs_files` is keyed `(obs_general_id, file_number)`, the position of the file within its
observation, which also keeps the order the file list is read in; it has no `id`. It keeps
`opus_id` (the file logic reads by it) and `instrument_id`. Its one secondary index is
`(opus_id, short_name, version_name)` for the file reads, with the download join served by
the primary key; it is the
largest table by rows, and each unused index is a full extra copy of a key column.

### 2.3 Surface geometry

One physical table replaces the per-target tables and the selector table, which is the
shape #334 asks for:

```sql
obs_surface_geometry_target(
  target_name     SMALLINT UNSIGNED NOT NULL,  -- mult id (§2.8)
  obs_general_id  INT UNSIGNED NOT NULL,
  <every geometry column of the template>,
  PRIMARY KEY (target_name, obs_general_id),
  KEY (obs_general_id),
  KEY (target_name, <X1>, <X2>)  -- per keyed, displayed range pair
  KEY (target_name, <col>)  -- per other keyed column
)
```

**Target first in the primary key**, so one target's rows are contiguous in the clustered
index as they are in a per-target table today. A search on a column with no key reads
that target's rows of the clustered index, and a one-column range search on a keyed
column uses its `(target_name, X)` index and then probes the clustered rows; with the
observation first, each observation's several targets would interleave and
multiply the cold page reads by the mean number of targets per observation. The alias
join below is still a unique lookup, and the per-observation lookup is a covering dive on
the secondary key, which also serves the foreign key and the per-observation delete.

`target_name` is the target's id within the selector's mult field,
`obs_surface_geometry_name.target_name` (§2.8), so every target has an id, a label, a
rank, and a grouping there. The template's column names that field with a `mult_field`
key, because the column's own qualified name would name a different field.

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
at the one table with no target filter. Its predicate is a semi-join (`EXISTS` on
`obs_surface_geometry_target` for the selected targets), never a join, so selecting several
targets cannot duplicate an observation. Its field keeps the qualified name
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
to the one table; on both the metadata-index and the inline path, the row's target string
is resolved to its id in the selector's mult field before the row is written. Two rows of
one observation that resolve to the same target write one row, the first in the import's
row order (sorted raw names on the summary-file path, file order on the inline path), with
a warning. A row whose target is unknown is not written.

**What a new target costs:** one mult row and its `table_names`, `partables`, and
`param_info` rows, written by finalization. No table is created, no model is generated,
nothing is redeployed; the worker restart that already follows every import refreshes
the per-process category caches. `models.py` loses about a hundred classes. Choosing a
target in Select Metadata (#651) becomes a change to the user interface alone.

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

`user_searches` holds one row per distinct search and nothing it does not use:

```sql
user_searches(
  id               INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  search_hash      BINARY(32)   NOT NULL,  -- SHA-256 of the canonical search
  result_count     INT UNSIGNED NULL,
  results_built_at DATETIME     NULL,
  last_used_at     DATETIME     NOT NULL,
  UNIQUE KEY (search_hash)
)
```

`search_hash` is one SHA-256 over the canonical selections, query types, units, and
order, with `null` for an absent part, so two requests share a row exactly when they
are the same search. The unique key is 32 bytes and is what makes two workers racing
to register the same search safe: the loser's insert fails and it reads the winner's
row. The memcached entry that maps a search to its id is keyed by the same hash in
hexadecimal, so its key has a fixed length whatever the search.

A page is `sort_order BETWEEN a AND b` on the join, exact because `ROW_NUMBER()` is dense.
The count is stored once. Partitioning is not used: `search_id` is the primary-key prefix,
so every per-search read is one range regardless. The unique key serves the cart's range
editor, which resolves an observation's position within a search, and makes a join that
duplicates an observation fail rather than repeat it on a page; every alias join in the
search build is one row per observation. A `default_rank` column on `obs_general`, the
position in the default sort, which would let the empty search page without a
search build, is evaluated on the complete holdings at the end of the plan and added only if
it measures a clear gain.

**Old searches are pruned, least recently used first, by size** (#350). A scheduled
command, which also reports the table's rows, its searches, and how many of each a prune
would remove and leave, and can show that without removing anything, removes searches
until `search_results` holds no more than a configured number of rows, and every search
unused for a set number of days in any case, so a busy server is pruned harder than a
quiet one. `last_used_at` is refreshed at most once a day per search, from the cached
entry, and skipped while the search is being built (the stamp reads its row `FOR UPDATE
SKIP LOCKED` and updates it only when that returns the row, and the search build sets
the stamp itself), so it costs no write per request and never waits on the row lock.
For each search it deletes cache entry first, then its `user_searches` row, so a new
request registers it afresh, then its result rows in chunks.
Every request reads the search's count and search build time from `user_searches` by
primary key, so a cached id whose row is gone is a miss, not a short page; only the
hash-to-id entry is cached, and ids are never reused within a schema. The same command
removes expired sessions and the carts whose session is gone. InnoDB reuses the freed
pages, so regular pruning bounds the table's size however long a schema is served.

```sql
-- the connection is at READ COMMITTED, Django's MySQL default
SET SESSION innodb_lock_wait_timeout = <search_build_timeout>  -- for the build only
BEGIN
  SELECT results_built_at FROM user_searches
    WHERE id = ? FOR UPDATE      -- the serialization point
  INSERT INTO search_results
    SELECT ?, ROW_NUMBER() OVER (ORDER BY ...), obs_general.id
    FROM obs_general LEFT JOIN ...
  UPDATE user_searches
    SET result_count = ?, results_built_at = NOW(), last_used_at = NOW()
COMMIT                            -- releases the row lock
SET SESSION innodb_lock_wait_timeout = <the value it replaced>
```

**A search is built once however many requests race for it.** Registration
commits on its own first, because a failed duplicate insert holds a shared lock until its
transaction ends. Every application connection runs at `READ COMMITTED`, the level
Django's MySQL backend sets unless told otherwise, and a test asserts it, so the `INSERT
... SELECT` takes no shared locks on the rows it reads and every statement reads the
latest committed rows. Inside one transaction the search builder reads the search's own
`user_searches` row `FOR UPDATE`; a second search builder blocks on
that row until the first commits, then sees `results_built_at` set and returns. If the row
is not yet built the search builder inserts `SELECT ?, ROW_NUMBER() OVER
(ORDER BY ...), obs_general.id FROM ...`, writes the count and both timestamps, and commits,
which releases the lock. A waiter's locking read returns the row as the builder committed
it, and the result rows are read after the transaction ends, so no reader sees the search
half built. A row lock is transaction-scoped: a worker that dies releases it with
its rollback, it is the same statement on both brands, and it works through any connection
pooling. The lock wait timeout is the session's `innodb_lock_wait_timeout`, set from
`[django] search_build_timeout` (default 270 seconds) just before the build and restored
just after it, so no other statement on a pooled connection waits that long; it is long
enough for a broad cold search build and at least 30 seconds below
the web server's worker timeout (300 seconds in every documented configuration), since
a worker killed partway through a search build rolls the search build back. A waiter
whose wait times out ends its transaction and answers with the search-cache failure
response; the search build it waited on completes, and the
next request finds it.

The application's cache trusts its entries (a hash-to-id or id-to-count hit is not
re-verified), so **every reset of these two tables is followed by a cache flush**: the
import's reset step runs the application's cache flush, the deploy restarts the cache
service after it, and the benchmark harness restarts the cache it owns. Without the flush, an
entry that outlived a truncate would hand one search's rows to another once ids restart.

The cost model is stated so the right thing is measured: the search build is the same
sort and the same number of inserts, now into a shared table with a secondary unique
index, so the cold search build itself is expected no faster. The gains are no DDL in
the request path, a bounded table count, the stored count, and one search build per
search under concurrency.

If the measured re-sort number still warrants it, `user_searches` gains a second hash
over the set alone, so a re-sort of a built set reorders its ids instead of
re-evaluating the predicate.

### 2.5 Junction tables for the list columns

Each JSON list column on `obs_general` gets a junction table written by the import from
the resolved mult ids; both are children in the sense of §2.2, with the foreign key to
`obs_general` added in finalization:

```sql
obs_general_target_name (mult_id, obs_general_id,
                         PRIMARY KEY (mult_id, obs_general_id), KEY (obs_general_id))
obs_general_target_class(the same shape)
```

A target search becomes a semi-join on the junction; the mult count, today a
`JSON_TABLE ... GROUP BY` over the whole result set, becomes a `GROUP BY mult_id` on the
junction joined to `search_results`. The JSON column stays for rendering. A
multi-valued JSON index is not used: it would serve the search but not the count.

### 2.6 Autocomplete

The string columns the autocomplete endpoint searches whose declared width is 100
characters or less get an ngram `FULLTEXT` key beside their B-tree, declared at table level
in the schema; the longer columns, file paths and notes, keep `LIKE`, since an ngram index on
them would outweigh the table. The query uses a quoted boolean
`MATCH ... AGAINST` for the `contains` type and prefixes of two or more characters, and
falls back to `LIKE` for one character, for the other types, and for any column where a
fixture comparison shows the two disagree. The stopword filter is off for the session
that builds the index, because the default list would drop every bigram containing `a`
or `i`.

### 2.7 Schema version

`schema_version(version INT UNSIGNED NOT NULL PRIMARY KEY, state ENUM('ready',
'appending') NOT NULL)`, one row.
It is written by an explicit step that every import sequence runs last, after
validation, and that is the only writer of `ready`: it inserts the row as `ready` when it
is absent, changes `appending` to `ready` when the version matches, and refuses to
overwrite a different version. Scorched earth drops the table before any other, and an
append (§3) sets it to `appending` while it runs. The web application checks it at
startup and serves 503 on a mismatch, a missing row, or a state other than `ready`; both
deploy scripts check the served schema's row before running any import or migration step.
A half-imported schema therefore cannot be served or promoted, and new code cannot stamp an
old schema.
The version covers every table the import creates, including `user_searches` and
`search_results`, which it only re-creates: the code-only deploy leaves them in place, so
a release that changes their columns is a full deploy.

### 2.8 Mult values

One table holds every enumerated value, in place of one `mult_<table>_<column>` table per
column:

```sql
mult_field(field_id       SMALLINT UNSIGNED PRIMARY KEY,
           qualified_name VARCHAR(100) NOT NULL UNIQUE,  -- e.g. obs_general.planet_id
           pinned         TINYINT NOT NULL)              -- the schema lists the choices
mult_group(field_id       SMALLINT UNSIGNED NOT NULL,
           grouping       VARCHAR(100) NOT NULL,
           group_rank     SMALLINT UNSIGNED NOT NULL,
                      group_pin      SMALLINT UNSIGNED NULL,
           PRIMARY KEY (field_id, grouping))
mult(field_id  SMALLINT UNSIGNED NOT NULL,
     id        SMALLINT UNSIGNED NOT NULL,  -- from 1; 0 is never valid
     value     VARCHAR(100) NOT NULL,       -- '' for the absent value
     label     VARCHAR(100) NOT NULL,
     pin       SMALLINT UNSIGNED NULL,
     disp_rank SMALLINT UNSIGNED NOT NULL,
     display   ENUM('Y','N') NOT NULL,
     grouping  VARCHAR(100) NULL,
     PRIMARY KEY (field_id, id),
     UNIQUE KEY (field_id, value))
```

- **Ids are per field**, so an observation column holds a small id: `SMALLINT UNSIGNED` in
  every mult column, the junction tables, and `obs_surface_geometry_target.target_name`,
  provided the largest field fits, which the plan checks against real data first. A label
  is a primary-key lookup, `JOIN mult AS m ON m.field_id = ? AND m.id = obs.column`. A
  column can name another column's field with a `mult_field` key, as the surface geometry
  table does for the selector (§2.3).
- **`disp_rank` is a dense integer per field**, computed for the whole field at the end of
  every import from typed values: pinned values first in `pin` order (pins come from the
  schema's option lists, from an observation class, or from `mult_overrides`); then
  ordinary values, numerically (the stored value through the column's unit parser when it
  has a unit, otherwise the label as a number) when every one parses and otherwise by
  case-folded label; then `Yes` and `On`; then `No` and `Off`; then the absent-value
  labels, compared case-folded, in the order `None`, `N/A`, `NULL`. Label and stored value
  break ties. The rank does not depend on the order bundles were imported, sorts negative
  numbers correctly, and is the same integer the search form and the counts sort by.
  Groups are ranked in `mult_group` by `group_pin` then case-folded name, so the planet
  groups keep their configured order. The absent value is stored as the empty string,
  never NULL, because a unique key does not deduplicate NULLs; a value outside a pinned
  field's list fails the bundle.
- **Values no observation references are deleted** at the end of every import, full or
  incremental, except in a pinned field, whose list is the intended set of choices. The
  search form therefore offers only values that return results.
- A value keeps the label, display flag, and grouping it was first stored with; an import
  that computes different ones logs a warning naming both.
- **Renaming a value needs no re-import.** A column's schema entry may list
  `mult_overrides`, each naming a value and any of its label, display flag, grouping, and
  pin. Overrides win over stored and computed labels; finalization applies them in every
  import, and the code-only deploy applies them to the served schema in place, beside
  reloading `param_info` and the dictionary, then restarts the cache and the workers; it
  rebuilds no other table. Ids never change, so no observation row is touched.
- **Search results sorted by a mult column are ordered by label text**, not by
  `disp_rank`. That is the public API's ordering and stays as it is.
- The `aliases` and `timestamp` columns of today's tables are not carried: nothing reads
  them.

One table is evaluated on the complete holdings at the end of the plan, and is added only
if the measurements, once discussed, justify it: `obs_facet`, one narrow row per
observation holding every mult id, which a count over a large result set would scan
instead of the child tables. The empty search's counts need no table: the post-deploy
warm-up puts every mult field's counts in memcached.

### 2.9 Column types

- **Strings are `VARCHAR`**, never padded `CHAR`.
- **Identifier columns are ASCII with a case-insensitive collation** (`ascii_general_ci`,
  not a binary one: the `opusid` search field and the metadata URL take ids people type, and
  case must never matter there):
  every `opus_id` and `bundle_id` column, in `cart` and `obs_files` as in the observation
  tables, `obs_files.instrument_id` (the only string `instrument_id`), and the
  string-search columns whose values are all ASCII, so a join between two of them compares
  like with like. Comparisons are cheaper and sort keys a quarter the size of `utf8mb4`'s.
  Case never matters in a lookup. Labels, mult values, the dictionary, and free text
  stay `utf8mb4`.
- **No row timestamps.** Nothing reads them.
- **`cart.session_id` fits Django's session key**, and the cart's foreign key cascades
  a deleted observation's rows away.

### 2.10 Key changes at a glance

| Table | Key | Change | Why |
|---|---|---|---|
| `obs_general` | `(time1, opus_id)` | added | the default sort, covering with the primary key appended |
| `obs_general` | `(right_asc, d_right_asc)`, `(declination1, declination2)` | added | a covering scan for the modular right ascension predicate; an index range for declination |
| `obs_ring_geometry` | `(<col>, d_<col>)` per longitude pair | added | the same, for the ring longitude pairs |
| every child `obs_*` | `PRIMARY KEY (obs_general_id)` | replaces `id` | the join key is the row locator; one unique lookup per child |
| every child `obs_*` | `FOREIGN KEY (opus_id)`, the `bundle_id` key | removed | a second 50-character key checked on every write and never used for a join; bundles are found through `obs_general` |
| every child `obs_*` | `FOREIGN KEY (obs_general_id)` | added in finalization | created without, added once, so the load pays no per-row check |
| `obs_surface_geometry_target` | `PRIMARY KEY (target_name, obs_general_id)`, `KEY (obs_general_id)` | new | per-target locality; per-observation lookup as a covering dive |
| `obs_surface_geometry_target` | `(target_name, <X1>, <X2>)` per keyed, displayed range pair and `(target_name, <col>)` per other keyed column | replaces about a hundred `KEY (col)` per column | one tree per keyed column instead of one per target; the range pairs index-only |
| every `obs_*` table | single-column keys production never read, and those leading a composite | removed | each was a full copy of its column written on every load and read by nothing; the import's keys stay |
| `obs_general_target_name`, `_class` | `PRIMARY KEY (mult_id, obs_general_id)`, `KEY (obs_general_id)` | new | semi-join for the search; grouped join for the counts |
| `mult` | `PRIMARY KEY (field_id, id)`, `UNIQUE (field_id, value)` | replaces one table per column | a label is a primary-key lookup; one model instead of ninety |
| `search_results` | `PRIMARY KEY (search_id, sort_order)`, `UNIQUE (search_id, obs_general_id)` | new | a page is one range; a position lookup is a probe |
| `user_searches` | `UNIQUE (search_hash)` | replaces the four-hash constraint | one 32-byte key per registration |
| autocomplete string columns | `FULLTEXT ... WITH PARSER ngram` | added | substring search without a scan; the B-tree stays |
| `obs_files` | `PRIMARY KEY (obs_general_id, file_number)`, `(opus_id, short_name, version_name)` | replace `id` and six single-column keys | the file list's order and the download join from the primary key; the file reads from the one secondary |
| `import_bundle` | `(state, size_estimate, bundle_number)` | new | a claim reads one entry, scanned backward, and locks only the row it claims |

### 2.11 What does not change

The rows and columns of `partables`, `param_info`, and the dictionary tables (their string
types and row timestamps follow §2.9), `cart` beyond what §2.9 states, and the public API's
response bodies, including the order of results sorted by a mult column.

---

## 3. How the schema is created

The import writes every table directly; there is no import namespace and no copy. What
it does is chosen by the target schema's state, never by a command-line switch, and the
import logs which it chose, for which schema and version:

| Target schema | The import |
|---|---|
| No version row and no secondary indexes: empty, or a fresh import still in progress | **imports fresh**: steps 2 to 5 below |
| A version row that matches the code, `ready` | **appends** (below) |
| A version row that matches the code, `appending` | **resumes the append** |
| A version row from another release | refuses, naming both versions |
| No version row but secondary indexes: an interrupted finalization | refuses `--import`; a finalization-only invocation resumes it |

A full import runs one invocation per bundle group, and every one after the first finds a
fresh import in progress and continues it. The bundle steps are chosen by this state;
finalization is an explicit step that the sequences run once at the end.

1. **Scorched earth** drops every table the import creates in the schema, which is every
   table there but Django's own: `schema_version` first, so an interrupted erase leaves a
   schema nothing serves or promotes; then the `obs_` tables, `cart`, the dictionary
   tables, the aux tables, the two search tables, the bundle registry, the importer table,
   and last the three mult tables, each table whose name no prefix rule matches named
   exactly. It runs only when asked for, and means the same in both commands:
   `opus_import --scorched-earth --yes` performs it (`--yes` is the confirmation, since
   `opus_import` never prompts), and `opus_import_all --scorched-earth` runs that before
   registering any bundle, so the full import starts from an empty schema. Without it, a
   rerun of a full import resumes from the bundles already done.
2. **Per bundle**, the observation and mult tables are created with their primary key
   and unique keys only, plus the keys the per-bundle delete reads: `obs_general`'s bundle
   key, and the `obs_general_id` key of a table whose primary key does not start with it.
   Every other table is created with all its keys. Worker
   processes turn index rows into table rows; the parent process assigns ids from the
   bundle's id range (below), resolves mult values, and loads tab-separated text with `LOAD
   DATA LOCAL INFILE` in chunks of about 100,000 rows, failing on any skipped row or
   warning (the statement would otherwise ignore duplicate keys silently). Each bundle is
   deleted from the permanent tables before it is written, so a rerun is clean. Nothing
   looks for duplicate OPUS ids while loading: two bundles' copies of one load side by
   side.
3. **Finalization** creates, by sort: `FULLTEXT` keys first, each in its own statement
   (the first one rebuilds its table); then B-tree indexes concurrently across tables,
   grouped per table within a temporary-space budget; then foreign keys serially under
   `foreign_key_checks = 0`. The key build is idempotent, comparing existing keys by kind
   and ordered columns. Then the **duplicate step**, which keeps the copy of each
   duplicated OPUS id with the highest `obs_general.id`, deletes the others from every
   table with the foreign key checks on (InnoDB cascades nothing with them off, and the
   cart's cascade must remove the deleted copy's cart rows), and logs each (a warning when
   both copies come from one bundle, which is a data error). Bundles that share OPUS ids
   (a calibrated bundle and its raw counterpart, for instance) are deleted and re-imported
   together, so a deleted copy never needs to come back, and nothing records it. Then the
   mult step, which deletes values nothing references and recomputes every rank (§2.8).
4. **Aux tables** (`param_info`, `partables`, `table_names`) are rebuilt, with the surface
   geometry categories derived from the data. `partables` and `table_names` come from the
   imported data and are written directly, since an import never runs against a served
   schema. `param_info` carries labels, tooltips, and display flags from the schema files,
   which the code-only deploy reloads into a served schema, so it is built beside the live
   table and swapped in with one atomic `RENAME TABLE`. Then `user_searches` and
   `search_results` are reset and the cache flush of §2.4 follows, and `ANALYZE` runs with
   histograms on the range-searched columns.
5. **The dictionary import, validation, and the version row.** The dictionary is reloaded
   the same way as `param_info`, also by the code-only deploy: its two tables are built
   beside the live ones and swapped together in one statement, `definitions__new` created
   with its foreign key pointing at `contexts__new`, so the key lands on the new
   `contexts`. Validation includes an orphan count per child and for `cart`, because
   finalization's foreign keys never validate existing rows. Last, the version step
   writes the version row, or turns `appending` to `ready` (§2.7).
6. **Promotion**, for a full import and an incremental update alike: the web service
   stops, the previous schema's sessions and carts are carried over into the new schema
   (unexpired `django_session` rows, and the `cart` rows of those sessions by `opus_id`,
   which `cart` already stores, to the observation's new `obs_general_id`; a cart row
   whose session expired or whose observation is gone is dropped and counted), the
   installation switches to the new schema, and the web service starts. The carry-over
   truncates its two target tables first, so it can run in either direction. If it fails,
   the web service is started again on the unchanged installation and the deploy exits
   non-zero; nothing has switched.

**Appending** adds or replaces bundles in a finalized schema that is not being served, the
way a developer adds a bundle to a deployed database. It exists because the configuration
names one schema: cloning into a new schema for every iteration would mean editing the
configuration each time, so the append keeps the schema name fixed and changes the rows in
place. The import first sets the version row's state to `appending` and marks the
bundles `pending` in the bundle registry (below), which is the one record of what the
append has still to do; new worker processes refuse
the schema and the deploy scripts refuse to promote it, while workers already running are
not stopped, because the version check runs once per worker at startup and nowhere else,
which is why an append is only for a schema that is not being served. Each bundle is
deleted, with the foreign key checks on so the cart's cascade runs, and reloaded with the
indexes and foreign keys in place. The append invocation ends there, still `appending`; as
after a fresh import, finalization is its own invocation, in which every finalization step
an append invalidates runs again (the duplicate step, the mult step, the aux tables, the search-table reset with
its cache flush, `ANALYZE`, and validation), and last the version step returns the state
to `ready`; no other step writes `ready`. A failed append stays `appending`; the next
import resumes the bundles the registry shows unfinished plus any it names, and since each
bundle is deleted before it is written, the rerun is clean. An append is not atomic, so it
is never run against a schema that is being served; §3.1 is how a served schema is
updated.

**Several processes at once.** Several `opus_import` processes, on one computer or
several, may import into one schema at the same time. Each bundle is registered once, in
`import_bundle(bundle_number, bundle_id)`, a table in the same schema as the observation
tables, with an id range: registration, in import order, gives each bundle 100 times the
row count its index label declares, starting where the previous bundle's range ends, so
ids ascend in import order and are the same on every run. That is
the only id the import allocates: every other table keys on `obs_general_id`. A process
reads each bundle's number from the registry, registering the bundle if it is absent;
registration takes the same bundle descriptors as an import (bundle ids, bundle sets,
and shorthands such as `ALL` and `CASSINI`) and numbers the bundles in import order, so
registering the whole list first makes the ids the same on every run and the later bundle
in import order has the higher number, and
a replaced bundle keeps its number. A new mult value takes the next id within its field
from a counter on the field's `mult_field` row, incremented in a transaction of its own
that holds the row for one statement; the value is then inserted with that id, and a
duplicate-key error on `(field_id, value)` means another process added it first, so its
id is read back (the id taken is left unused) and two processes meeting the same value
get the same id. Every import connection runs at `READ COMMITTED`, and the claim, the
mult-id assignment, and the per-bundle delete are retried, a bounded number of times, on a
deadlock or a lock wait timeout. When two
bundles produce the same OPUS id, **the later-registered bundle wins**: both copies
load, and finalization's duplicate step keeps the higher id, which the ranges make the
higher `bundle_number` whatever order the bundles are imported in. On a full import that
is the later bundle in import order; a re-imported bundle keeps its number, so it loses
to every bundle registered after it. No process looks for duplicates or locks anything
to avoid them. Registration itself is serialized by a named lock, which belongs to the
session: under it registration creates any registry or mult table that is absent (DDL
commits on its own, so that comes first), then in one transaction writes the ranges and
the rows every process would otherwise race to create: one `mult_field` row per field, and the
values of every field whose schema lists its choices. A process writes only the values
it meets, and inserts a value group so that a row another process wrote first is left
unchanged.

**The registry is also the work queue.** Bundles differ in size by orders of magnitude, so
work is not split into fixed parts before the run; each bundle is a unit of work handed
out at run time. Each registry row carries a size estimate (the row count its primary
index labels declare; a bundle without one is refused at registration), a state (`pending`, `importing`,
`done`, `failed`), the rows done so far, and the importer that claimed it. An **importer**
is one `opus_import` process, with its own pool of workers, that repeatedly claims the
largest pending bundle with `FOR UPDATE SKIP LOCKED`, reading one entry of the registry's
`(state, size_estimate, bundle_number)` key so that it locks only the row it claims, and
imports it, so large bundles start at once and small ones fill in at the end. Claim order changes
nothing in the result, because ids and the duplicate rule both follow `bundle_number`,
fixed at registration.

**`opus_import_all` coordinates.** It registers every bundle, starts a number of
importers on its computer with the workers asked for divided among them (one by default,
so a plain import is sequential, and never more than a configured fraction of the cores,
since the computer may also run the database server or serve other work), and tracks
every importer on
any computer through an `import_process` table, showing per importer its bundle and rows
done and in total the bundles and rows remaining. Each importer holds a MySQL named lock
for its life, so a dead importer is detected from any computer the moment its connection
drops (its pool's forked workers close the descriptors they inherit and die with it, so
none of them keeps the connection open); its bundle's rows are deleted and the bundle is requeued, and a bundle lost twice
is marked failed. When the queue is empty and no importer is alive, the coordinator
finishes the schema (finalization, the dictionary import, validation, and the version
row), unless a bundle failed. `opus_import_all --join` on another computer adds
importers to the same queue, a first Ctrl-C drains and a second aborts, and rerunning
`opus_import_all` resumes from the bundles already done.

### 3.1 Incremental update

An incremental update replaces a bundle with a new copy, adds a bundle, or drops one. A
browser sees nothing of it until it is finished, and then sees all of it at once. The
update is created as a new schema and promoted whole, exactly as a full import is:

1. **Schema clone**: the served schema less the bundles being replaced (a bundle being
   dropped is copied, then deleted, below). The
   import, given `--clone-from-schema <served>` on an empty target, creates the tables as
   step 2 does and copies the served schema's rows into them, refusing when the served
   schema's version differs from the code's: `obs_general` with `WHERE bundle_id NOT IN
   (<the bundles being replaced>)`, every other per-observation table with `WHERE
   obs_general_id NOT IN (SELECT id FROM <served>.obs_general WHERE bundle_id IN (<the
   same bundles>))`, the three mult tables whole, and the bundle registry with the replaced
   bundles set back to pending and the importer tracking reset (the importer table is
   created empty). Every bundle keeps its number and every unchanged observation its id.
   A bundle being dropped is copied with the rest and then deleted from the new schema by a
   separate bundle delete, which also removes its registry row, before finalization. The copies run over the sibling connections, one table per connection, under `READ COMMITTED` so
   the served schema's rows are not locked; values
   only the replaced or dropped bundles used are removed by finalization's mult step. Ids are
   preserved, so an unchanged observation keeps its `obs_general_id` and its mult ids. The
   served schema is only read.
2. **Import.** How the cloned tables are keyed depends on how much changes: when the
   replaced bundles hold more `obs_general` rows than a measured fraction of the schema,
   the schema clone creates bare tables, the bundles go through the ordinary fresh import,
   and finalization creates every index once, by sort; below it, the schema clone copies
   each table with its indexes in place and ends by writing the version row in the
   `appending` state, so the bundles go through the append path with the indexes up and a
   small update rebuilds nothing. A re-imported bundle keeps its number and so its id
   range, which the copy left empty; a new bundle takes the next number and so wins a
   duplicate `opus_id` against every copied bundle. New mult values append, and a new
   surface geometry target is a row, not a table (§2.3).
3. **Steps 3 to 5 as for a full import:** finalization, aux tables, dictionary,
   validation, and the version row. `cart`, `user_searches`, and `search_results` are
   created empty.
4. **Promotion** is step 6: stop, carry over, switch, start. A cart row whose
   observation no longer exists is dropped and counted in the import log, and the
   browser is not told (a decision: the cart is shorter, the badge and the listing
   agree, and no table records what was dropped). `user_searches` and
   `search_results` start empty and refill on demand; the warm-up runs after the start.

An update that only drops bundles is the schema clone with nothing excluded and nothing
imported, followed by the bundle delete. The cost is
one copy of the database per update, plus one full index build above the fraction,
measured by the plan, and the disk for two schemas, which a full-import deploy needs
already. The previous schema stays until the next update, so a rollback is step 6 run
toward it: the carry-over brings back the sessions and carts as they stand at that moment,
and only a cart row for an observation the previous schema lacks is lost.

**Why not in place, and why not a table swap.** Writing into the served schema is not
atomic: between the first bundle delete and the closing reset a request can build a search
against a partial observation set and be served from it, and the workers' per-process
caches go stale. A `RENAME TABLE` swap of staged copies inside the served schema is atomic
for the names, but it needs the same full copy, still leaves the per-process caches stale
until the restart the promotion does anyway, and leaves the old tables beside the new; it
buys nothing over a new schema and a switch. `param_info` and the dictionary are
different: they are small, rebuilt whole from the schema files, and reloaded on their own
by the code-only deploy, so each is swapped in place with one atomic `RENAME TABLE` rather
than given a new schema. `partables` and `table_names` are never rebuilt in a served
schema at all.

The import connection sets `sql_log_bin = 0` when the account may, and otherwise says so
and continues. `unique_checks` is never changed: the primary and unique keys catch the
duplicates they guard. Duplicate OPUS ids are the duplicate step's (§3).

---

## 4. How a request uses it

- **Register the search.** Hash the selections, types, units, and order into one
  `search_hash`; insert the `user_searches` row or read the existing one (the unique key
  resolves a race between workers).
- **Run the search build if needed**, under the row lock (§2.4); otherwise read
  `result_count` and the rows that exist.
- **A page** joins `obs_general` to `search_results` on `obs_general_id` with `search_id =
  ?` and `sort_order BETWEEN ? AND ?`, then LEFT JOINs each child category on
  `obs_general_id` (a unique lookup each), with surface geometry categories aliased and
  filtered by target.
  For a Saturn surface geometry column the page reads:

  ```sql
  ... FROM obs_general
  JOIN search_results r
    ON r.obs_general_id = obs_general.id
   AND r.search_id = ?
   AND r.sort_order BETWEEN ? AND ?
  LEFT JOIN obs_surface_geometry_target
         AS obs_surface_geometry__saturn
    ON obs_general.id = obs_surface_geometry__saturn.obs_general_id
   AND obs_surface_geometry__saturn.target_name = ?
  ```

- **The fan-out** (mult counts, range endpoints, triggered tables) joins `search_results`
  the same way; mult counts on list columns group the junction table, and labels and
  ranks come from `mult` by `(field_id, id)`; surface geometry
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
  registration (`user_searches`, whose unique key on the search hash resolves a race
  between two workers registering the same search), the result rows and the stored count
  (`search_results`, `user_searches`), the cart (`cart`, one row per `(session_id,
  obs_general_id)`), and Django's sessions (the database engine). A browser's next
  request can land on any worker and see the same search, the same page, and the same
  cart.
- **The search build serializes on a row lock inside a database transaction**;
  no worker holds anything across requests. The lock is released by rollback when a
  connection dies, identical on both brands, and unaffected by connection pooling or
  proxies.
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

Sessions and the cart live in the per-import schema, and every promotion, after a full
import or an incremental update, carries them into the new schema while the web service is
stopped (§3, step 6): session rows whole, cart rows by `opus_id` to the observation's new
`obs_general_id`, dropping a row whose session expired or whose observation is gone. A
cart therefore survives an update unless its observation vanished, and nothing of the
previous schema is referenced afterward. Keying the cart by `(session_id, opus_id)` in a
schema that outlives imports would remove the mapping step; it is a schema change left for
later (`plans/2026-10-28_cloud_deployment_notes.md`, §4).

Everything else a multi-host deployment would need is application and operations work,
not schema: a shared cache with fully scoped keys, shared storage for cart downloads, the
holdings on every worker, a fleet deploy step, transport settings for a managed database,
and the grants such a service withholds. Those are recorded, with what was found in the
code for each, in `plans/2026-10-28_cloud_deployment_notes.md`, and are not part of the
performance plan.
