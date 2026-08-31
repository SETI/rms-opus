.. _dev_guide_webapp:

The Web Application: Theory of Operation
========================================

:mod:`opus_app` is the Django project that serves the OPUS user interface and the public
web API out of the database an import wrote. It **reads** that database and never writes
an ``obs_`` table. What it does create is temporary: the per-search ``cache_*`` tables,
a few short-lived tables the results and cart queries build, the ``cart`` rows a session
selects, and the tables Django's own contrib apps own.

This chapter is the *why*. The chapters after it are the *what*:
:ref:`dev_guide_webapp_running` is how to run it, :ref:`dev_guide_webapp_tools` is the
machinery every app shares, :ref:`dev_guide_webapp_search`,
:ref:`dev_guide_webapp_results` and :ref:`dev_guide_webapp_ui` walk the eight apps, and
:ref:`dev_guide_webapp_extending` is how to add to them.

.. _dev_guide_webapp_lifecycle:

The request lifecycle
---------------------

.. mermaid::

    flowchart TD
        R([HTTP request]) --> M[MIDDLEWARE:<br/>cache, gzip, common, session,<br/>auth, CSRF, messages,<br/>StripWhitespaceMiddleware]
        M --> U[opus_app.urls:<br/>each app contributes its routes,<br/>mounted at / and at /opus/]
        U --> V[the view, wrapped in api_view]
        V --> P[url_to_search_params:<br/>the query string becomes<br/>selections and extras]
        P --> Q[get_user_query_table:<br/>find or build cache_NNN<br/>for this search]
        Q --> S[sql_builder.Select:<br/>join obs_, mult_ and the cache table]
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
:ref:`dev_guide_web_server`).

**2. One OPUS-authored middleware.** Everything in ``MIDDLEWARE`` but the last entry is
Django's own. :class:`~opus_app.apps.tools.opus_middleware.StripWhitespaceMiddleware`
strips leading and trailing whitespace from a text response, which the templates
generate a great deal of.

**3. Every routed handler is wrapped in**
:func:`~opus_app.apps.tools.app_utils.api_view`. It is the single place a failure
becomes a status code, and it is described in :ref:`dev_guide_webapp_errors` below.

**4. A search becomes a cache table.**
:func:`~opus_app.apps.search.views.url_to_search_params` turns the query string into two
dictionaries, and :func:`~opus_app.apps.search.views.get_user_query_table` turns those
into a ``cache_NNN`` table holding the ids of the matching observations in sort order.
:ref:`dev_guide_webapp_search_flow` below is the whole of it.

**5. The wide joins are assembled, not written.**
:mod:`opus_app.apps.tools.sql_builder` builds every statement that joins the ``obs_``
tables to each other, to the ``mult_`` tables holding their enumerated values, and to a
cache table whose name is computed at runtime. It is the one module allowed to turn
Python values into SQL text.

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

:func:`~opus_app.apps.search.views.set_user_search_number` hashes the selections, the
qtypes, the units and the order, and looks the four hashes up in ``user_searches``. That
table's unique key over the four is what makes a search's number stable, so the same
search from a different session reuses the same cache table.

**The write is deliberately optimistic**: rather than looking a row up and creating it if
absent -- which leaves a window for two processes to create it at once -- it inserts and
lets the unique constraint reject the loser, which then reads the winner's row. An absent
hash is stored as the literal string ``'NONE'``, because MySQL treats NULLs in a unique
index as distinct and a NULL would defeat the deduplication entirely.

Unused qtypes and units are stripped before hashing, so a qtype for a field that is not
being searched does not make the search look different.

Step 3: the cache table is built
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:func:`~opus_app.apps.search.views.get_user_query_table` turns that number into
``cache_NNN`` and, unless the memory cache already says the table exists, runs
:func:`~opus_app.apps.search.views.construct_query_string` and creates the table from
its result. Two columns:

.. code-block:: text

    sort_order  INT NOT NULL AUTO_INCREMENT, PRIMARY KEY(sort_order)
    id          INT UNSIGNED, UNIQUE KEY(id)

``sort_order`` gives the result ordering and ``id`` joins back to ``obs_general``. The
SELECT that fills it has exactly one output column: ``obs_general.id``.

**Two processes racing to build the same table is expected and handled.** The second
one's ``CREATE TABLE`` either fails immediately with "table already exists", or blocks on
the first one's lock and then fails the same way once it is finished -- and either way
the table is now there, so the error is caught and the name returned. Any other database
error is logged and returns None, which the caller turns into a 500.

Step 4: everything downstream joins against it
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A page of results, a count, a set of file URLs and a list of product types are four
queries over one cached search rather than four searches.
:func:`~opus_app.apps.search.views.search_cache_join_condition` builds the join:
``obs_general`` joins on its own primary key, and every other ``obs_`` table on the
``obs_general_id`` it carries.

The results reader adds one more level of indirection.
:func:`~opus_app.apps.results.views.get_search_results_chunk` creates a **temporary
table** holding just the page's slice of the cache table -- ``sort_order`` and ``id``,
with the ``LIMIT`` and ``OFFSET`` applied -- and joins the wide query to that instead, so
the ordering and the paging are settled before the joins run. It drops the temporary
table in the same call.

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

**memcached**, through Django's cache framework, when it is available; Django's
local-memory cache stands in when it is not. :mod:`opus_app.settings` decides at import
time, and it decides *twice*: first whether ``pymemcache`` can be imported, then whether
a connection to it can actually be made. Every key OPUS builds is
``CACHE_SERVER_PREFIX + CACHE_KEY_PREFIX + ...``, where the first comes from the
configuration and the second is ``'opus:'`` plus the database schema name -- which is
what lets several OPUS installations share one memcached. Losing this cache costs speed
and nothing else.

**The** ``cache_NNN`` **tables**, which are real tables in the OPUS database. Losing one
costs the time to rebuild it. The import drops them all, because an import changes what a
search means.

**Process-local dictionaries.** Two matter: the ``param_info`` lookup in
:mod:`opus_app.apps.search.views` and the mult-label lookup in
:mod:`opus_app.apps.tools.db_utils`. Both are module-level dictionaries private to each
worker process, **unbounded, and never cleared** -- there is no invalidation path in
either. So **nothing running outside a worker can clear them**,
``clear_django_cache`` included, which empties the shared Django cache and nothing else.
A change to ``param_info`` needs the application restarted.

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
wide joins a search needs are built by :mod:`opus_app.apps.tools.sql_builder` instead,
because they join a dynamically named cache table that has no model at all -- and
because they are far clearer as SQL than as ORM expressions.

Four tables have hand-written models elsewhere as well, in the app that owns them:
:class:`~opus_app.apps.paraminfo.models.ParamInfo`,
:class:`~opus_app.apps.cart.models.Cart`, and the two dictionary models in
:mod:`opus_app.apps.tools.dictionary`. The generated file carries a ``ZZ``-prefixed
duplicate of each, which is the generator's way of saying "a model exists for this table
and nothing should use it".

**Every OPUS model is unmanaged.** The tables are created by the import pipeline, so
there are no OPUS migrations; ``django-admin migrate`` creates only Django's own contrib
tables.

Where to go next
----------------

:ref:`dev_guide_webapp_running`
    Running it, in development and under a WSGI server.

:ref:`dev_guide_webapp_tools`
    The shared machinery: ``api_view``, the SQL builder, the file lookups.

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
