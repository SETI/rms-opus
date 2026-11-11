.. _dev_guide_webapp_overview:

How a Request Is Served
=======================

:mod:`opus_app` **reads** the database an import wrote and never writes an ``obs_``
table. What it does write is everything the *session* produces: the ``user_searches`` row
that gives a search its number and the ``search_results`` rows that hold its results, the
``cart`` rows a session selects, and the tables Django's own contrib apps own. Only an
import and ``opus_manage prune`` remove the first two.

This is the *why* of the chapter: what happens between a request arriving and an answer
leaving, and what forces that shape. The pages beside it are the *what*.

.. _dev_guide_webapp_lifecycle:

The request lifecycle
---------------------

.. mermaid::
    :zoom:

    flowchart TD
        R([HTTP request]) --> M[MIDDLEWARE:<br/>cache update, gzip, common, session,<br/>auth, CSRF, messages, cache fetch,<br/>StripWhitespaceMiddleware]
        M --> U[opus_app.urls:<br/>each app contributes its routes,<br/>mounted at / and at /opus/]
        U --> V[the view, wrapped in api_view]
        V --> P[url_to_search_params:<br/>the query string becomes<br/>selections and extras]
        P --> Q[get_search_id:<br/>register the search, and write<br/>its results once]
        Q --> S[sql_builder.Select:<br/>join obs_, mult_ and the search's results]
        S --> D[(MySQL)]
        D --> F[render as JSON, CSV or HTML]
        F --> RESP([HTTP response])
        V -.->|nothing to search| F

Six things happen in that path, and each is worth knowing before changing any of it.

**1. Every route is served twice.** :mod:`opus_app.urls` builds one list of patterns --
the home page plus each app's own ``urls.py`` -- and mounts it at the site root **and**
under the ``opus/`` prefix. So ``/api/data.json`` and ``/opus/api/data.json`` are the
same view. The prefix exists because a development server has no web server in front of
it to strip one; production is fronted by a web server instead (see
:ref:`user_guide_web_server`).

**2. One OPUS-authored middleware.** Everything in ``MIDDLEWARE`` but the last entry is
Django's own. :class:`~opus_app.apps.tools.opus_middleware.StripWhitespaceMiddleware`
strips leading and trailing whitespace from a text response, which the templates
generate a great deal of.

**3. Every handler that answers an API call is wrapped in**
:func:`~opus_app.apps.tools.app_utils.api_view` -- directly, or through the public twin
it delegates to. It is the single place a failure becomes a status code, and it is
described in :ref:`dev_guide_webapp_errors` below. The page itself, Django's admin site
and the API guide's redirect are the routes that are not API calls and are not wrapped.

**4. A search becomes rows of** ``search_results``.
:func:`~opus_app.apps.search.views.url_to_search_params` turns the query string into two
dictionaries, and :func:`~opus_app.apps.search.views.get_search_id` turns those into the
search's number. The first time anyone makes the search, it also stores the ids of the
matching observations in ``search_results``, in sort order.
:ref:`dev_guide_webapp_search_flow` below is the whole of it.

**5. The wide joins are assembled, not written.**
:mod:`opus_app.apps.tools.sql_builder` assembles every statement that joins the ``obs_``
tables to each other, to the ``mult_`` tables holding their enumerated values, and to one
search's rows of ``search_results``. It is the one module allowed to turn Python values
into SQL text.

**6. The result is rendered in one of three formats.** JSON through
:func:`~opus_app.apps.tools.app_utils.json_response`, CSV through
:func:`~opus_app.apps.tools.app_utils.csv_response`, and HTML through a template. A
handler that is asked for a format its route does not offer raises
:exc:`~django.http.Http404`.

.. _dev_guide_webapp_two_apis:

Two APIs, one code base
-----------------------

OPUS serves two families of URL out of the same views, and the distinction runs through
every app:

**The public API** -- ``api/...``, plus a handful of unprefixed entry points. It is
documented in :ref:`api_guide`, and **backwards compatibility is preserved for it**,
against this repository's general no-back-compat policy: a URL that worked before has to
keep working. :ref:`dev_guide_conventions` records the waiver.

**The private API** -- everything beginning ``__``: ``__api/``, ``__cart/``,
``__help/``, ``__menu.json``, ``__widget/``, and the rest. These are shaped for the OPUS
front end, are not advertised, and carry no compatibility promise. Several of them are
thin wrappers around a public handler that add a ``reqno`` echo (see below) or switch on
a richer HTML rendering.

A private handler generally requires ``reqno``, an integer the front end increments per
request and expects back in the response. It is how a single-page application discards
the answer to a question it has already moved on from, and a request without one is a
400.

.. _dev_guide_webapp_search_flow:

How a search becomes rows
-------------------------

This is the central mechanism of the whole application.

Step 1: the query string becomes two dictionaries
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:func:`~opus_app.apps.search.views.url_to_search_params` is the main routine. OPUS lets
users put readable things in a URL -- ``planet=Jupiter`` rather than ``planet_id=3`` --
and this is where that is undone. It produces:

* **selections** -- what to constrain, keyed by qualified column name
  (``obs_general.planet_id``), each value a list with one entry per search clause;
* **extras** -- ``qtypes`` (how each field is compared), ``units`` (what unit each
  numeric value was given in) and ``order`` (the sort).

Three details shape everything downstream:

* **The shape of a value depends on the mode flags it was called with.** Under
  ``return_slugs`` the keys are slugs and each holds a single value rather than a list;
  under ``pretty_results`` a mult value is a joined string and a numeric value is the
  text it formats to. That is why the values are annotated as
  :data:`~typing.Any`, and why the function's own docstring spells the shapes out.
* **A slug may carry a clause number**, ``_NNN``, which is how a range or string field is
  constrained more than once with the results ORed together.
* **Values are converted to the column's default unit** before they are compared, using
  :mod:`opus_support`. A conversion that overflows marks the term invalid immediately
  rather than failing later in the query builder.

Step 2: the search gets a number
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Each distinct search has one row in ``user_searches``, and the row's ``id`` is the
search's number. Two sessions that make the same search get the same number, and so share
the same stored results.

**A search is recognized by its hash.**
:func:`~opus_app.apps.search.views.search_hash` writes the search's selections, qtypes,
units and sort order as one JSON list and takes its SHA-256 hash. Qtypes and units for
fields that are not being searched are left out first, so they cannot make two equal
searches look different. The hash is stored in the row's ``search_hash`` column, which is
a unique key.

:func:`~opus_app.apps.search.views.set_user_search_number` finds the number in three
steps:

1. It looks the hash up in the Django cache, which maps a search's hash to its number. If
   the hash is there, that is the number.
2. Otherwise it inserts a new ``user_searches`` row. If another request inserted the same
   search first, the unique key refuses the insert, and it reads that request's row
   instead. Inserting first, rather than looking for the row first and inserting if it is
   missing, means two requests can never both add the same search.
3. It stores the number in the cache, for the next request.

**The row also records when the search was last used**, in ``last_used_at``.
``opus_manage prune`` removes the searches that have gone longest without use. A request
updates the column at most once a day for each search, and the cache entry remembers the
day of the last update. The update never waits: if another request is writing the
search's results (Step 3) and so holds its row, the update is skipped
(``SELECT ... FOR UPDATE SKIP LOCKED``), and that request sets ``last_used_at`` itself.

**Without memcached**, each web worker has a cache of its own
(:ref:`dev_guide_webapp_caching`). A worker that has not seen a search before does not
find it in its cache, even when another worker has. It then tries the insert, which the
unique key refuses, and reads the row, so it gets the same number. The cost is one
refused insert for each worker and search, and up to one ``last_used_at`` update a day
for each worker rather than for the site.

Step 3: the search's results are written
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:func:`~opus_app.apps.search.views.get_search_results` reads the search's
``user_searches`` row. If its ``results_built_at`` is set, the search's results are
already stored, and its ``result_count`` is the number of results. Otherwise it writes
them into ``search_results``, one row for each observation the search matches:

.. code-block:: text

    search_id       the search's number
    sort_order      its position in the search's order: 1, 2, 3, ... with no gaps
    obs_general_id  the observation
    PRIMARY KEY (search_id, sort_order), UNIQUE KEY (search_id, obs_general_id)

Writing a search's results is one transaction:

1. ``SELECT ... FROM user_searches WHERE id = %s FOR UPDATE`` locks the search's row. If
   another request is already writing this search's results, this waits until that
   request finishes, finds ``results_built_at`` set, and uses the other request's count.
2. One ``INSERT INTO search_results ... SELECT`` runs the search and writes every row,
   numbering them with ``ROW_NUMBER() OVER (ORDER BY ...)`` in the search's order.
3. One ``UPDATE`` stores ``result_count``, ``results_built_at`` and ``last_used_at``.
4. The commit releases the lock.

So **a search's results are written once**, however many requests ask for the search at
the same moment.

**How long a request waits for the lock** is the configuration's ``[django]
search_build_timeout``, which is set as the session's ``innodb_lock_wait_timeout`` for
the transaction and restored afterwards. If the wait runs out (MySQL error 1205,
:func:`~opus_app.apps.tools.db_utils.is_lock_timeout_error`), the request answers with a
500, as it does for any other database error. If writing the results fails, or the
worker is killed partway through, the transaction rolls back and nothing is stored, so
the next request starts over. That is why ``search_build_timeout`` has to be shorter
than the web server's worker timeout (:ref:`user_guide_installation_configuring`).

Django's MySQL connections use ``READ COMMITTED``, so the ``INSERT ... SELECT`` does not
lock the ``obs_`` rows it reads.

**A number from the cache may be out of date.** ``opus_manage prune`` may have removed
the search, or an import may have emptied both tables, after the cache stored the number.
So every read of the row also checks that the row holds the search's own hash. If the row
is missing, or holds another search's hash, the cache entry is deleted and the search is
added again as in Step 2, once. The ids keep counting up across an import's reset, so an
old number never names a new search's row.

**Without memcached** this step works the same way. The lock is held in MySQL, not in the
cache, so requests in different workers still wait for each other, and a search's
results are still written once for the site.

Step 4: every later query reads the stored results
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A page of results, a set of file URLs and a list of product types each read the search's
stored rows instead of running the search again. The result count needs no query of its
own: it is the ``result_count`` stored in the search's ``user_searches`` row.

Each of those queries joins the search's rows as a derived table,
:func:`~opus_app.apps.tools.sql_builder.search_results_source`:

.. code-block:: sql

    (SELECT obs_general_id AS id, sort_order FROM search_results WHERE search_id = %s)
        AS results

MySQL merges a derived table this simple into the query around it, so the join uses
``search_results``'s own keys.
:func:`~opus_app.apps.search.views.search_results_join_condition` writes the join
condition: ``obs_general`` joins on its primary key, and every other ``obs_`` table on
its ``obs_general_id``.

A page of results is a range of ``sort_order``
(:func:`~opus_app.apps.results.views.get_search_results_chunk`). The positions run from 1
with no gaps, so rows *offset* + 1 to *offset* + *limit* are exactly one page. MySQL reads
just those rows through the ``(search_id, sort_order)`` primary key before it joins
anything, so the last page costs no more than the first.

.. _dev_guide_webapp_errors:

Errors
------

Three status codes, and which one a failure gets is decided in one place: the
:func:`~opus_app.apps.tools.app_utils.api_view` wrapper.

.. list-table::
   :header-rows: 1
   :widths: 12 88

   * - Code
     - Raised for
   * - **400**
     - A request that is wrong: an unknown field, an unparseable value, an unsupported
       unit or query type, a missing ``reqno``. Raised as
       :exc:`~opus_app.apps.tools.app_utils.Http400Error` from wherever the fault is
       found, and rendered by the wrapper into the OPUS error page.
   * - **404**
     - A URL naming something that does not exist -- an entry point OPUS does not serve,
       or an OPUS ID that matches no observation. Raised as
       :exc:`django.http.Http404`.
   * - **500**
     - A failure while answering an otherwise valid request. Always logged with its
       traceback.

The wrapper's exception handling is deliberately asymmetric:

* :exc:`django.http.Http404`, :exc:`~django.core.exceptions.BadRequest`,
  :exc:`~django.core.exceptions.PermissionDenied` and
  :exc:`~django.core.exceptions.SuspiciousOperation` are **re-raised** after being
  logged, so each keeps the response and the logging Django gives it -- a 404 keeps
  Django's own body, and a suspicious request reaches Django's security logger.
* :exc:`~opus_app.apps.tools.app_utils.Http400Error` is rendered into a 400 response and
  returned.
* Anything else is logged with its traceback and becomes a 500.

**The message texts all live in** :mod:`opus_app.apps.tools.app_utils` rather than at the
sites that raise them, so that the same fault reads the same way wherever it is found.
:ref:`dev_guide_webapp_tools` lists them.

.. _dev_guide_webapp_api_code:

The API call number
-------------------

:func:`~opus_app.apps.tools.app_utils.api_view` assigns every request a sequential
number, records the time it started, and logs the exit with the elapsed time and a
truncated rendering of the response. **A handler that needs that number declares an
``api_code`` parameter and the wrapper supplies it**; the check is made once, at
decoration time, by inspecting the handler's signature.

The number is not a session id and not a request id in any durable sense -- it is a
process-local counter, used to correlate the entry and exit lines of one call in the log
and to tag the timing log the search helpers write.

Whether anything is logged at all is decided by the ``log_api_calls`` configuration key,
which is false in every normal deployment.

.. _dev_guide_webapp_caching:

Caching
-------

Four layers, and they fail differently.

**memcached**, through Django's cache framework. It holds each search's number (Step 2)
and answers worth keeping: mult counts, range endpoints, product-type lists, the tables
a search triggers and autocomplete choices. Every key is
``CACHE_SERVER_PREFIX + CACHE_KEY_PREFIX + ...``, where the first comes from the
configuration and the second is ``'opus:'`` plus the database schema name, so several
OPUS installations can share one memcached. Almost every answer is keyed by a search's
number, and numbers are never reused, so an answer can never be read for the wrong
search. Emptying the cache costs speed and nothing else.

:mod:`opus_app.settings` decides at startup, in each worker, whether to use memcached:
it checks that ``pymemcache`` can be imported, and then that the memcached the
configuration's ``[django] cache_location`` names answers within a second. **A missing
or failed memcached never fails a request.** What happens depends on when it fails:

* **Missing when a worker starts** (not installed, not running, or not answering): the
  worker uses Django's local-memory cache instead, which belongs to that one process.
  Everything still works, but each worker computes and stores its own copy of every
  cached answer, and a worker keeps using its local memory even after memcached starts.
  Restart the workers to switch them to memcached.
* **Stopped or hung while the workers are using it:** every cache read that cannot reach
  it within a second counts as a miss, and every write is skipped (``pymemcache``'s
  ``ignore_exc``). Requests are answered from the database, uncached, so they are slower
  but correct. After a few failures a worker stops trying the server for a minute, so
  requests do not each wait for the timeout. Once memcached answers again, the workers
  use it again.
* **Emptying the cache from outside the workers** --
  ``python -m opus_app.clear_django_cache``, the import's reset of the search tables,
  ``opus_manage prune`` removing a search's entry -- runs in a process of its own. With
  no memcached it empties only that process's memory, and each worker keeps its entries
  until it is restarted. After a prune that does no harm: Step 3 notices a removed
  search. After an import, each worker goes on serving answers computed from the old data
  until it is restarted, which every deploy does.

``search_results`` **and** ``user_searches``, which are real tables in the OPUS database:
one row per distinct search in ``user_searches``, and every stored search's results in
``search_results``. Losing a search costs the time to run it again. An import empties
both tables, because it changes what a search returns, and then empties the shared
cache. ``opus_manage prune`` removes the least recently used searches, so that
``search_results`` does not grow without limit (:ref:`user_guide_deployment_prune`).

**Process-local copies.** Each worker process keeps its own copy of what only an import
changes, so that a request reads it from memory rather than from the database:

- the ``table_names``, ``partables`` and ``mult_`` tables, each read whole on first use
  by :mod:`opus_app.apps.tools.import_constants`, which also compares a label from a
  request the way the database server's case- and accent-insensitive collation does;
- the ``definitions`` table, read whole on first use by
  :mod:`opus_app.apps.tools.dictionary`;
- the ``param_info`` rows :mod:`opus_app.apps.search.views` looks up, one dictionary
  keyed by slug and one keyed by table and column, filled as rows are asked for. The
  slug dictionary is **unbounded**: it keeps a miss for every slug a request names.

The same module remembers each regular expression the database server accepted, up to a
fixed number, and asks again about one it refused. None of these copies has an
invalidation path, so **nothing running outside a worker can clear them**,
``clear_django_cache`` included, which empties the shared Django cache and nothing else.
A change to any of those tables, which every import makes, needs the workers restarted;
a restarted worker reads each table again on the first request that needs it.

**The browser.** Most handlers carry ``@never_cache``. The exceptions are deliberate and
few, and are noted where they occur.

.. _dev_guide_webapp_models:

Two kinds of model
------------------

``src/opus_app/apps/search/models.py`` holds one Django model per OPUS table --
including one per ``mult_`` table -- and is **generated**, by
``scripts/models/create_opus_models.sh``, from a populated database. A hand edit does not
survive the next regeneration, which is why it is excluded from ruff, carries no
docstrings, and is left out of the API reference. Add a column by adding it to the
table's schema (:ref:`dev_guide_table_schemas`) and regenerating.

The generated models are used for the queries that read a single row or a small set. The
wide joins a search needs are written by :mod:`opus_app.apps.tools.sql_builder` instead,
because they join one search's rows of ``search_results`` as a derived table, and no
model reads that table -- and because they are far clearer as SQL than as ORM
expressions.

Some tables have hand-written models elsewhere as well, in the app that owns them:
:class:`~opus_app.apps.paraminfo.models.ParamInfo`,
:class:`~opus_app.apps.cart.models.Cart`, and the two dictionary models in
:mod:`opus_app.apps.tools.dictionary`. The generated file carries a ``ZZ``-prefixed
duplicate of each, which is the generator's way of saying "a model exists for this table
and nothing should use it".

**Every OPUS model is unmanaged.** The tables are created by the import pipeline, so
there are no OPUS migrations; ``opus_manage migrate`` creates only Django's own contrib
tables.

Where to go next
----------------

:ref:`dev_guide_webapp_running`
    Running it, in development and under a WSGI server.

:ref:`dev_guide_webapp_tools`
    The shared machinery: :func:`~opus_app.apps.tools.app_utils.api_view`, the SQL
    builder, the file lookups.

:ref:`dev_guide_webapp_search`
    The search app, and the generated models.

:ref:`dev_guide_webapp_results`
    Reading a completed search: results, metadata and cart.

:ref:`dev_guide_webapp_ui`
    The single page, the help pages, the field descriptions and the front end.

:ref:`dev_guide_webapp_extending`
    Adding an endpoint, an app, or a format.

API reference
-------------

:doc:`api_opus_app`
