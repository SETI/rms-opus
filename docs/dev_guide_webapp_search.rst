.. _dev_guide_webapp_search:

The ``search`` App
==================

:mod:`opus_app.apps.search` holds three quite different things: the two API handlers the
search form calls while a user types, the routines that turn a search URL into SQL, and
the generated Django models for every OPUS table.

Only the first is routed. The second is imported by nearly every other app, and is the
reason this module is the largest in the project.
:ref:`dev_guide_webapp_search_flow` is the mechanism; this chapter is the code.

The routes
----------

.. list-table::
   :header-rows: 1
   :widths: 40 12 48

   * - Route
     - API
     - Handler
   * - ``__api/normalizeinput.json``
     - private
     - :func:`~opus_app.apps.search.views.api_normalize_input`
   * - ``__api/stringsearchchoices/<slug>.json``
     - private
     - :func:`~opus_app.apps.search.views.api_string_search_choices`

Both are mounted at the site root and under the ``opus/`` prefix, like every OPUS route.

:func:`~opus_app.apps.search.views.api_normalize_input`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Validates and normalizes the whole current search, one field at a time. For each
searchable slug it parses the value and, if it can, returns the value re-rendered from
the parse; if it cannot, that slug's answer is null.

It calls :func:`~opus_app.apps.search.views.url_to_search_params` with three flags
together -- errors allowed, slugs as keys, values prettified -- which is what makes it
per-field: one bad input marks one field rather than failing the request. That is what
lets the interface put one input box in an error state while the rest keep working.

It requires a ``reqno`` and echoes it back.

:func:`~opus_app.apps.search.views.api_string_search_choices`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The autocomplete dropdown for a string field: every value the field can still take,
given what the user has typed into it and given the rest of the search. Four things about
it are worth knowing.

**It removes the field being typed into from the search.** The suggestions are
constrained by the *other* search terms, not by the partial value itself -- otherwise the
list would collapse to what the user has already typed.

**It tolerates a broken regular expression**, through
``allow_regex_errors``. The front end sends half-typed regular expressions, because the
autocomplete request is timed against the keystrokes rather than against input
validation. For the same reason a ``matches`` query type is downgraded to ``contains``
while suggesting.

**It has two query strategies, and says which one it used.** The restricted one joins the
field's table to the search's cache table and is used when the cache table has fewer rows
than the configured threshold. If the cache table is larger than that, or if the
restricted query exceeds its execution-time hint, it falls back to querying the whole
database and reports ``full_search: true``. Both queries carry a
``MAX_EXECUTION_TIME`` hint, because an autocomplete that takes seconds is worse than one
that answers approximately.

**The matched portion is highlighted** by re-applying the user's pattern to each
suggestion. It uses the third-party ``regex`` module rather than :mod:`re`, because that
is closer to the ICU regular expression library MySQL uses; and a pattern that fails to
compile here is swallowed, because the highlighting is cosmetic and the results are not.

Results are cached in the Django cache, keyed by the field, a hash of the partial query,
the cache table, the query type and the limit. ``reqno`` is added after the caching, so
it is never cached.

.. _dev_guide_webapp_search_url_to_params:

Turning a URL into a search
---------------------------

:func:`~opus_app.apps.search.views.url_to_search_params`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The main routine, and the one to read first. It takes a request's query mapping and
returns the ``(selections, extras)`` pair everything downstream works in. Its own
docstring is the authoritative statement of the shapes; the summary is:

* **selections** -- keyed by qualified column name, each value a list with one entry per
  ORed clause.
* **extras** -- ``'qtypes'``, ``'units'`` and ``'order'``.

Six flags change what it does:

.. list-table::
   :header-rows: 1
   :widths: 28 72

   * - Flag
     - Effect
   * - ``allow_errors``
     - An unparseable value becomes None and parsing continues, instead of failing the
       whole request. This is what makes per-field validation possible.
   * - ``allow_regex_errors``
     - A regular expression that the database will not accept is passed over rather than
       rejected.
   * - ``return_slugs``
     - The keys are slugs as written in the URL, and each holds one value rather than a
       list.
   * - ``pretty_results``
     - Values are rendered back to text: a mult value as a joined string, a number in the
       format and unit its column declares.
   * - ``allow_empty``
     - A term with no value on either side is kept, which is what building a search
       widget needs.

Six kinds of slug are recognized. A plain field slug; the same with a ``1`` or ``2``
suffix, for the two ends of a range; ``qtype-<slug>``, ``unit-<slug>`` and
``sourceunit-<slug>``; and any of those with a ``_NNN`` clause suffix. Anything in the
``SLUGS_NOT_IN_DB`` setting -- the paging, view, download and session parameters -- is
consumed and skipped.

Four behaviors are load-bearing:

* **``obs_pds.opus_id`` is rewritten to ``obs_general.opus_id``.** The user sees the OPUS
  ID under PDS Constraints, but searching it from the master table is far cheaper. The
  widget builder rewrites it back, so the interface never sees the substitution.
* **Both ends of a range are always recorded**, even when only one was given, so the two
  lists stay the same length and a clause's two ends cannot drift apart.
* **A slug and its previous spelling are both consumed.** Every slug the search
  resolves marks the whole family of names -- both spellings, both range ends, and the
  three prefixed forms -- as used, which is what stops a URL that mixes the two spellings
  of one field from searching it twice.
* **``sourceunit-`` exists only for the URL normalizer.** It names the unit a value is
  *written* in, where ``unit-`` names the unit it should be *converted to*. Nothing else
  should use it.

Query types and units
~~~~~~~~~~~~~~~~~~~~~

The permitted query types come from the field's form type: ``STRING_QTYPES`` --
``contains``, ``begins``, ``ends``, ``matches``, ``excludes``, ``regex`` -- for a string
field, and ``RANGE_QTYPES`` -- ``any``, ``all``, ``only`` -- for a range one. A mult field
has none. **The first entry of the list is the default**, so an unqualified string search
means "contains" and an unqualified range search means "any".

A **single-column range** -- a field whose two ends are one database column -- gets no
query type recorded at all, and supplying one other than ``any`` is an error further
down. :func:`~opus_app.apps.search.views.is_single_column_range` is the test.

Units are validated against :func:`opus_support.units.get_valid_units` for the column's
unit id, and every value is converted to the column's default unit before it is compared.
A conversion that overflows marks the term invalid immediately, so that the normalizer
can report it, rather than failing later inside the query builder.

The sort order
~~~~~~~~~~~~~~

:func:`~opus_app.apps.search.views.parse_order_slug` reads a comma-separated slug list in
which a leading ``-`` means descending. Two settings shape it: ``DEFAULT_SORT_ORDER``
supplies one when the URL has none, and ``FINAL_SORT_ORDER`` -- the OPUS ID -- is
**appended if it is not already present**, so that the ordering is always total and
paging is stable.

:func:`~opus_app.apps.search.views.create_order_by_terms` turns the parsed pair into
ORDER BY terms and reports which ``obs_`` and ``mult_`` tables they require joined. A
mult field sorts by the human-readable label in its mult table rather than by the id
stored in the row, which is why sorting can pull in a join the search itself does not
need.

.. _dev_guide_webapp_search_cache:

Building the cache table
------------------------

:func:`~opus_app.apps.search.views.set_user_search_number`
    Maps a search to a small integer through the ``user_searches`` table, as described in
    :ref:`dev_guide_webapp_search_flow`. Returns the number and whether the row was newly
    created.

:func:`~opus_app.apps.search.views.get_user_search_table_name`
    The number becomes ``cache_<n>``. One line, and the only place that name is formed.

:func:`~opus_app.apps.search.views.get_user_query_table`
    Finds or builds the table, and returns its name or None. It memoizes the name in the
    Django cache once the table's existence is certain, and handles two processes racing
    to create it.

:func:`~opus_app.apps.search.views.search_cache_join_condition`
    The condition that ties a table's rows to a search's results.

Turning a search into SQL
-------------------------

:func:`~opus_app.apps.search.views.construct_query_string`
    Walks the selections in sorted order -- sorted so that the SQL a given search
    produces is reproducible, which is what the golden-response suite pins -- and
    dispatches on each field's form type. It collects the ``obs_`` and ``mult_`` tables
    the clauses and the ordering need, assembles the joins, and returns the statement and
    its parameters. **The SELECT list is one column, ``obs_general.id``.**

Four builders produce the clauses:

:func:`~opus_app.apps.search.views.get_string_query`
    ``contains``, ``begins`` and ``ends`` become ``LIKE`` with the wildcards placed
    accordingly; ``matches`` becomes equality; ``excludes`` becomes ``NOT LIKE``; and
    ``regex`` becomes ``RLIKE``. **Escaping is per query type**: a backslash is escaped
    for everything but ``regex``, and the two SQL wildcards are escaped for everything but
    ``regex`` and ``matches``. Clauses are ORed.

:func:`~opus_app.apps.search.views.get_range_query`
    Three query types, each pairing one side of the user's range with one column:
    ``all`` requires the observation's range to cover the user's, ``only`` requires the
    user's to cover the observation's, and ``any`` requires them to overlap. A blank side
    contributes nothing; a term blank on both sides is omitted.

:func:`~opus_app.apps.search.views.get_longitude_query`
    The same three query types, expressed as a comparison of the **angular separation**
    between the two ranges' centers against a sum or difference of their half-widths --
    which is why the import stores a longitude's midpoint and half-span as well as its
    endpoints. A term with only one side given is handed to
    :func:`~opus_app.apps.search.views.get_range_query` instead, and a single-column
    longitude becomes a pair of plain comparisons joined by ``AND`` or, for a range that
    wraps through zero, by ``OR``.

Mult fields are handled inline in
:func:`~opus_app.apps.search.views.construct_query_string`: the user's readable labels are
looked up in the field's ``mult_`` table to get their ids, and a ``GROUP`` field becomes
an ``IN`` test while a ``MULTIGROUP`` field becomes an OR of JSON containment tests,
because it holds a list.

``_valid_regex`` is how a user's regular expression is
checked: **by asking the server**, since OPUS runs the expression through MySQL rather
than through Python, and only MySQL knows what it will accept.

.. _dev_guide_webapp_search_paraminfo_cache:

The ``param_info`` lookup, and its cache
-----------------------------------------

:func:`~opus_app.apps.search.views.get_param_info_by_slug` resolves a slug to its
:class:`~opus_app.apps.paraminfo.models.ParamInfo` row. It takes a ``source`` saying what
kind of slug it is, because the four kinds spell the same field differently:

.. list-table::
   :header-rows: 1
   :widths: 18 82

   * - Source
     - Rule
   * - ``'col'``
     - A metadata column. It may carry a ``:unit`` override, which
       ``allow_units_override`` returns alongside the row.
   * - ``'widget'``
     - A widget name, which carries a ``1`` even for a single-column range, so the
       ``1`` is stripped on a miss.
   * - ``'qtype'``
     - A query-type or unit slug, which carries no numeric suffix, so one is added on a
       miss.
   * - ``'search'``
     - A search term, which may carry either suffix.

Each lookup tries the current slug and then the ``old_slug`` column, so a bookmark
written with a previous spelling resolves.

**The results are cached in a module-level dictionary**, because the function is called
very often and each call costs at least one database query. Three properties of that
cache matter:

* It caches **misses** as well as hits, so an unknown slug is cheap the second time.
* It is **never cleared and never bounded**. There is no invalidation path anywhere in
  the repository. A change to ``param_info`` therefore needs the worker processes
  restarted -- see :ref:`dev_guide_webapp_running`.
* It is a plain dictionary rather than an :func:`functools.lru_cache`, because several
  callers **mutate** the row they are given, so each needs its own copy.

``_get_param_info_by_qualified_name`` is the other
direction -- a ``table.column`` name to its row -- and is **not** cached.

The join helpers
----------------

:func:`~opus_app.apps.search.views.add_obs_table_joins`
    LEFT JOINs each ``obs_`` table onto ``obs_general`` on the ``obs_general_id`` it
    carries. **The joins are LEFT** because an observation with no row in one of those
    tables must still appear in the result, with that table's columns null.

:func:`~opus_app.apps.search.views.add_mult_table_joins`
    LEFT JOINs each ``mult_`` table onto the ``obs_`` column holding its id. For a
    MULTIGROUP column, which holds a JSON list, the join key is the list's first element.

.. _dev_guide_webapp_search_forms:

The search form
---------------

:mod:`opus_app.apps.search.forms` is the Django form the Search tab's widgets are built
from. :class:`~opus_app.apps.search.forms.SearchForm` is constructed with a mapping of
slug to value and grows one input per slug, choosing what kind from the field's
``param_info`` row:

* a **string** field gets a text input plus the query-type dropdown beside it;
* a **range** field gets a labelled endpoint input, and gets a query-type dropdown
  **only if it is not a single-column range**;
* a **mult** field gets a checkbox group -- except
  ``obs_surface_geometry_name.target_name``, which gets radio buttons, because a surface
  geometry search names one target.

:class:`~opus_app.apps.search.forms.MultiFloatField` is the field a range endpoint is
built from; it adds nothing to Django's own, and everything that makes the input a range
endpoint comes from the widget it is given.

The ``grouping`` argument selects which group of a mult field's values to offer, which is
how :func:`~opus_app.apps.ui.views.api_get_widget` renders a grouped checkbox list one
group at a time.

.. _dev_guide_webapp_search_models:

The generated models
--------------------

``src/opus_app/apps/search/models.py`` is **machine-written** by
``scripts/models/create_opus_models.sh`` from a populated database, and it is the largest
file in the repository. It holds 231 model classes:

* one per ``obs_`` table;
* one per ``mult_`` table;
* ``Partables``,
  ``TableNames`` and
  ``UserSearches``;
* and a ``ZZ``-prefixed model for every other table the database happens to hold -- the
  Django contrib tables, and the four OPUS tables that have hand-written models in the
  apps that own them.

**The ``ZZ`` prefix is the generator's way of saying "a model exists for this table and
nothing should use it."** The class name is otherwise the table name with each
underscore-separated segment title-cased and the underscores removed, which is exactly
the transformation the runtime lookups apply:
:func:`~opus_app.apps.tools.db_utils.table_model_from_name` and the mult lookups both
build a class name that way.

Regenerating it
~~~~~~~~~~~~~~~

``scripts/models/create_opus_models.sh``, run from the repository root against a fully
imported database. It runs Django's ``inspectdb``, **refuses to continue if any**
``cache_*`` **table is present** -- so the per-search tables can never be captured as
models -- applies the prefixing and the foreign-key repairs, and formats the result.

Consequences worth knowing:

* A hand edit does not survive the next regeneration. The file is excluded from the
  linter and carries no docstrings for the same reason, and the API reference leaves it
  out, naming it on the reference's landing page so that a reader who cannot find it is
  told why.
* **A new OPUS table does not exist to the web application until this has been run.**
* The ``cache_NNN`` tables are never modelled at all, which is the reason
  :mod:`opus_app.apps.tools.sql_builder` exists.

``UserSearches`` is the one generated model worth
reading: its unique key over the four hashes is what makes a search's cache table number
stable, and :ref:`dev_guide_webapp_search_flow` describes how that is used.

API reference
-------------

:doc:`api_opus_app.apps.search`
