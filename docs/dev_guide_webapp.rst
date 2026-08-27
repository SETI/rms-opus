.. _dev_guide_webapp:

The Web Application
===================

:mod:`opus_app` is the Django project that serves the OPUS user interface and the
public web API out of the database an import wrote. It reads that database and never
writes an ``obs_`` table. What it does create is temporary: the per-search ``cache_*``
tables, a few short-lived tables the results and cart queries build, and the tables
Django's own contrib apps own.

Project modules
---------------

:mod:`opus_app.settings`
    Every Django setting, plus the OPUS-specific constants the apps read from
    ``django.conf.settings`` -- the default columns, the sort order, the download
    limits, the qtypes each field type allows. It reads the installation's TOML file
    through :mod:`opus_config`, so importing it needs ``OPUS_CONFIG`` set.

:mod:`opus_app.urls`
    The URL map. Each app contributes its own routes, and the whole set is mounted
    twice: at the site root and under the ``opus/`` prefix a development server uses.

:mod:`opus_app.wsgi`
    What a WSGI server loads.

``opus_app.clear_django_cache``
    A deployment helper, run as ``python -m opus_app.clear_django_cache``. It calls
    ``settings.configure()`` in its module body, so it must never be imported by
    anything -- which is why it is the one module the API reference leaves out.

The apps
--------

:mod:`opus_app.apps.ui`
    The single page the browser loads, and the calls that keep it up to date: the
    search form's widgets and menus, the Details tab, the notification banner, and
    URL normalization.

:mod:`opus_app.apps.search`
    The search itself. It turns a query string into a set of constraints, builds or
    finds the ``cache_NNN`` table of matching observation ids, and answers the
    string-choice and normalization calls the search form makes while a user types.

:mod:`opus_app.apps.results`
    Everything that reads from a completed search: pages of metadata, the URLs of the
    data and preview files, and the download archives.

:mod:`opus_app.apps.metadata`
    What is *searchable* rather than what was found: result counts, the values a
    multiple-choice field can take, the endpoints of a numeric range, and the
    description of every metadata field.

:mod:`opus_app.apps.cart`
    The user's cart and recycle bin, and the zipped downloads built from them.

:mod:`opus_app.apps.help`
    The About, Bundles, FAQ, Getting Started, Welcome and Citing pages. All but the
    Welcome page can be returned as HTML or as a PDF; the Welcome page's route carries
    no format at all and its view takes none.

:mod:`opus_app.apps.paraminfo`
    The ``param_info`` model -- the description of every searchable field -- and the
    label logic that qualifies a field's name with the body, mission or instrument it
    belongs to. The ``table_names`` model it reads alongside lives in the generated
    ``search/models.py`` with the rest of the tables.

:mod:`opus_app.apps.tools`
    What the other apps share: the ``api_view`` decorator, the SQL builder, the
    database helpers, the data-dictionary lookup, and the text of every error message
    the API returns.

Models
------

``src/opus_app/apps/search/models.py`` holds one Django model per OPUS table --
including one per ``mult_`` table -- and is **generated**, by
``scripts/models/create_opus_models.sh``, from a populated database. A hand edit to it
does not survive the next regeneration, which is why it is excluded from ruff and
carries no docstrings. Add a column by adding it to the table's schema
(:ref:`dev_guide_table_schemas`) and regenerating.

The generated models are used for the queries that read a single row or a small set.
The wide joins a search needs are built by
:mod:`opus_app.apps.tools.sql_builder` instead, because they join a dynamically named
cache table that has no model at all.

Answering a search
------------------

:ref:`dev_guide_architecture` has the diagram; the contracts are:

1. :func:`~opus_app.apps.search.views.url_to_search_params` parses the query string
   into ``selections`` (what to constrain) and ``extras`` (qtypes, units, sort order).
   **The shape of a value in either dictionary depends on the mode flags it was
   called with**, which is why they are annotated as ``Any`` and why its docstring
   spells the shapes out.
2. :func:`~opus_app.apps.search.views.get_user_query_table` maps a set of constraints
   to a ``cache_NNN`` table. The mapping is recorded in ``user_searches``, so the same
   search from a different session reuses the same table, and the table name is also
   held in the memory cache once its existence is certain. Two processes racing to
   build the same table is expected and handled.
3. Everything downstream joins against that table. A page of results, a count and a
   set of file URLs are three queries over one cached search rather than three
   searches.

Errors
------

Three status codes, and which one a failure gets is decided in one place -- the
``api_view`` wrapper described in :ref:`dev_guide_architecture`:

* **400** for a request that is wrong: an unknown field, an unparseable value, an
  unsupported unit or query type, a missing required parameter. Raised as
  :class:`~opus_app.apps.tools.app_utils.Http400Error` from wherever the fault is
  found.
* **404** for a URL naming something that does not exist -- an entry point OPUS does
  not serve, or an OPUS ID that matches no observation.
* **500** for a failure while answering an otherwise valid request. Always logged with
  its traceback.

The message texts all live in :mod:`opus_app.apps.tools.app_utils` rather than at the
sites that raise them, so that the same fault reads the same way wherever it is found.

Caching
-------

Three layers, and they fail differently:

* **memcached**, through Django's cache framework, when it is available; Django's
  local-memory cache stands in when it is not. Every key is built as
  ``CACHE_SERVER_PREFIX + CACHE_KEY_PREFIX + ...`` -- the first from the
  configuration's ``cache_server_prefix``, the second ``'opus:'`` and the database
  schema name -- which is what lets several OPUS installations share one memcached.
  Losing the cache costs speed and nothing else.
* **The** ``cache_NNN`` **tables**, which are real tables in the OPUS database. Losing
  one costs the time to rebuild it.
* **Process-local dictionaries**, notably the ``param_info`` lookup, which is read
  once and kept. A change to ``param_info`` therefore needs the application restarted
  or the cache cleared -- which is what ``clear_django_cache`` is for.

Static files and templates
--------------------------

``src/opus_app/static/`` and ``src/opus_app/templates/`` ship in the wheel, and so do
each app's own ``templates/`` directories. The public URL prefix for static files is
``/static_media/``, which is deliberate and long-standing even though the directory is
now named ``static/``.

The front end is plain JavaScript and CSS with no build step. ``opus.js`` is the entry
point; it drives the tabs, the search form and the results table, and talks to the
private ``__api/`` and ``__cart/`` endpoints.

API reference
-------------

:doc:`api_opus_app`
