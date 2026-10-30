# OPUS in a multi-host deployment: notes for later

**Scope:** what would have to change in the application and its operations, beyond the
database schema, to run OPUS with one database server and several stateless web workers
behind a load balancer that sends any request to any worker. The schema itself needs no
change for that layout (`plans/2026-10-28_database_design.md`, §5). None of the items
below is part of the database performance plan; this file exists so that they are not
lost and are not mistaken for that plan's work. The port itself is #1199.

**Date:** 2026-10-28. Each item names what the code does today, in the tree at
`2179d937`, with the file, and what the multi-host layout would need. The plan's PR-00,
PR-02, PR-03, PR-05, PR-06, PR-11, PR-16, and PR-17 change some of the "Today" paragraphs;
re-read them against the tree before acting on this file.

---

## 1. The Django cache

**Today.** `settings.py` imports `pymemcache` and probes `127.0.0.1:11211` before the
configuration is loaded, catching only a refused connection; `CACHES` is PyMemcache at
that literal address with no expiry, or Django's local-memory cache per process when the
probe fails (`src/opus_app/settings.py`, the probe near the top and the `CACHES` block).
The application's own keys are `CACHE_SERVER_PREFIX + 'opus:<schema name>' + ...`, assembled
by hand at every `cache.get`/`cache.set` site, where `[django] cache_server_prefix` is the
installation's prefix (its documented purpose is letting several installations share one
memcached); the page-cache middleware (`UpdateCacheMiddleware`,
`FetchFromCacheMiddleware`, in `MIDDLEWARE`) caches whole responses under keys that use
Django's `KEY_PREFIX`, which is unset, so `cache_server_prefix` does not reach them. Cache
hits are trusted: the hash-to-search-id entry, the id-to-count entry, and the cached mult
counts and range endpoints are used without re-checking the database, which is why
`_promote.sh` restarts the cache service on every deploy.

**Multi-host.** Each worker host with its own memcached would hold its own counts and
endpoints; the per-process fallback would recompute everything once per process. The
defect is a host-local service with a silent per-process fallback, not the choice of
memcached.

- Make the backend configurable (`[django] cache_backend` as `memcached`, `redis`, or
  `locmem`, beside PR-00's `[django] cache_location`), pointing every host at one shared
  service. The `redis` backend needs the `redis` client as an optional extra.
- Set `CACHES['default']['KEY_PREFIX']` from `cache_server_prefix`, the schema name, the
  schema version, and the release's version string, so the middleware's keys are scoped
  too and two releases or two schemas never share an entry. A longer prefix shortens the
  margin #1500 measures against memcached's key limit; the plan's PR-11 hashes the key
  tail to a fixed width.
- Keep the flush on every deploy and after every reset of `user_searches` and
  `search_results` (trusted hits make a stale entry a wrong answer). `clear_django_cache`
  must gain the configured backend; today it configures `CACHES` alone and cannot reach a
  database or a per-process cache.
- Fail loudly when a configured shared backend is unreachable at startup; catch `OSError`
  with a connect timeout, not only a refused connection.
- Django's database cache backend is not a good fit: every write counts the table and culls
  at a small default size, and nothing in the import sequence creates its table.

## 2. Per-process caches and the deploy step

**Today.** `param_info` (`_PARAMINFO_CACHE`) and the mult label maps (`_PRETTY_MULT_CACHE`)
are loaded at first use in each worker process and invalidated only by a restart
(`docs/dev_guide_webapp_overview.rst`, the Caching section); `partables` and `table_names`
are read per request until PR-03 caches them the same way. `_promote.sh` stops the web
service, switches a local symlink, restarts the cache service, and starts the web service,
all with `sudo systemctl`; it runs no warm-up (PR-17 adds `opus_manage warm_search`
there). `deploy_new_code_only.sh` rebuilds `param_info`, `partables`, and `table_names`
**in the served schema while workers run**, dropping and recreating each
(`src/opus_deploy/server/import_and_deploy/deploy_new_code_only.sh`; `do_param_info`,
`do_partables`, `do_table_names`).

**Multi-host.**

- A fleet promotion step that points every host at the new schema and restarts every
  worker, atomically from the browser's point of view (§4), then runs the warm-up once;
  the session and cart carry-over of the design's §3.1 runs once in that step, not per
  host.
- The in-place aux rebuild must not happen against a schema workers are serving; the
  schema-per-import deploy already guarantees that, the code-only deploy does not
  (#1504 records the same hazard for the dictionary swap).
- PR-17's warm-up warms the shared cache and the database, not each process's own
  copies; priming those in `wsgi.py` after PR-05's schema version check (or gunicorn
  `--preload`) would remove the per-process first-request cost.
- Static files are collected per installation; a fleet wants a CDN or a collect on every
  host.

## 3. Cart downloads and the holdings

**Today.** `api_create_download` builds the archive under `TAR_FILE_PATH` and the manifest
under `MANIFEST_FILE_PATH` on the worker's own disk (its CSV and URL scratch files are
deleted after archiving) and returns a URL under `TAR_FILE_URL_PATH` the browser then
fetches (`src/opus_app/apps/cart/views.py`, the download path). Downloads read the
holdings from `PDS3_DATA_DIR` and `PDS4_DATA_DIR` (`src/opus_app/apps/tools/file_utils.py`).

**Multi-host.** The second request can land on a worker that does not have the file.
Downloads need shared storage (an object store) and a URL on it; the single-observation
download builds the archive into the response body and is unaffected, though it still
needs a writable local `TAR_FILE_PATH` and `MANIFEST_FILE_PATH`. Every worker that serves
downloads needs the holdings mounted, not only the import host.

## 4. Sessions and the cart

**Today.** Django's sessions use the database engine (`SESSION_ENGINE` is not set) with
`SESSION_SAVE_EVERY_REQUEST = True`, so every request writes a session row; `cart` is keyed
by session id and `obs_general_id`; both tables live in the per-import schema, so a deploy
that switches schemas starts them empty.

**Multi-host.**

- During a rolling restart that mixes old and new workers, a browser alternates between
  two schemas. A request that lands on the other schema finds no row for its cookie's
  key; Django then deletes the cookie if the session stays empty, or issues a new key if
  the request writes to the session, so the browser ends with a key and a cart specific
  to each schema it touched. The switch must be atomic per browser (all workers at
  once, or the load balancer flips the fleet in one step).
- `SESSION_SAVE_EVERY_REQUEST = False` removes one write per request to the shared server.
  A cache-backed session engine is not the remedy: carts are keyed by session id and would
  vanish on eviction.
- The design's promotion carries sessions and carts into the new schema in the stopped
  window (design §3, step 6), so a deploy no longer empties them. Keying the cart by
  `(session_id, opus_id)` in a schema that outlives imports would remove that copy step;
  it is a schema change left for later. The cart stays per session either way.

## 5. The database connection

**Today.** `[database]` carries brand, host, database, schema, user, and password
(`src/opus_config/config.py`); `DATABASES` has no `OPTIONS` and no `PORT`, so no TLS
parameters and the default port. Each request opens and closes its own connection
(`CONN_MAX_AGE` is not set); after PR-02 each worker thread keeps one for
`[django] conn_max_age` seconds.

**Multi-host.**

- TLS settings for a managed service: a small addition to `[database]` and
  `DATABASES['OPTIONS']`. The port is PR-P1's `[database] port`, read into
  `DATABASES['PORT']`.
- `max_connections` on the server must cover workers × processes × threads plus the import
  and the warm-up. A connection proxy or transaction-mode pooler is compatible with the
  design's search materialization, which locks the search's own row inside its transaction
  and holds nothing across statements.
- The load balancer's idle timeout bounds how long a request may wait for a
  materialization in progress; `[django] search_materialization_timeout` should stay below
  it, or the front end answers 504 while the materialization completes and the next
  request finds it done.
- No read replica on the search path (`plans/2026-10-28_database_design.md`, §5).

## 6. Managed database services

All inferred from the services' documentation, to be confirmed on the chosen one.

| Needed by the plan | RDS MySQL and Cloud SQL | Aurora MySQL 3 |
|---|---|---|
| `LOAD DATA LOCAL INFILE` | allowed when the `local_infile` parameter is on and the client sets `local_infile=1` | same |
| `SET GLOBAL local_infile` | refused (no `SYSTEM_VARIABLES_ADMIN`); the loader falls back to packets and says so | refused |
| `SET sql_log_bin = 0` | refused unless the account holds `SESSION_VARIABLES_ADMIN` (plan §2.2); the import logs and continues | binary log usually off |
| `innodb_ft_enable_stopword` per session | available | available |
| `ngram_token_size = 2` | the default; a static parameter | same |
| `performance_schema` | may be off; static; digest truncation needs `DROP` on it | same |
| `innodb_ddl_threads`, `innodb_ddl_buffer_size` | 8.0.27 and later, session-settable | from Aurora 3.04 |
| `innodb_tmpdir` | a restricted session variable and a server-side path; left unset | likely unavailable |
| `ANALYZE TABLE ... UPDATE HISTOGRAM` | table privileges suffice | same |
| `FOR UPDATE` row locks | ordinary | writer only, which the design requires anyway |

## 7. Per-host files and logs

**Today.** The notification file and the blog-update file are read per host
(`src/opus_app/apps/ui/views.py`); the API log goes to the installation's one rotating log
file (`[paths] opus_log_file`), which every worker process opens, and its call counter is
a module-level integer (`_API_CALL_NUMBER` in `src/opus_app/apps/tools/app_utils.py`).

**Multi-host.** The two files move to configuration or the database; the log analyzer
needs a shared sink and a call identifier unique across processes and hosts.
