.. _dev_guide_webapp_search:

The ``search`` App
==================

:mod:`opus_app.apps.search` holds three quite different things: the two API handlers the
search form calls while a user types, the routines that turn a search URL into SQL, and
the generated Django models for every OPUS table.

Only the first is routed. The second is imported by nearly every other app, which is why
:mod:`opus_app.apps.search.views` is one of the largest modules in the project.
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

api_normalize_input
~~~~~~~~~~~~~~~~~~~

:func:`opus_app.apps.search.views.api_normalize_input`

Validates and normalizes the whole current search, one field at a time. For each
searchable slug it parses the value and, if it can, returns the value re-rendered from
the parse; if it cannot, that slug's answer is null.

It calls :func:`~opus_app.apps.search.views.url_to_search_params` with three flags
together -- errors allowed, slugs as keys, values prettified -- which is what makes it
per-field: one bad input marks one field rather than failing the request. That is what
lets the interface put one input box in an error state while the rest keep working.

It requires a ``reqno`` and echoes it back.

api_string_search_choices
~~~~~~~~~~~~~~~~~~~~~~~~~

:func:`opus_app.apps.search.views.api_string_search_choices`

The autocomplete dropdown for a string field: every value the field can still take,
given what the user has typed into it and given the rest of the search. Five things about
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
field's table to the search's results and is used when the search has fewer results than
the configured threshold, a count it reads from the search's ``user_searches`` row. If
the search has more than that, or if the restricted query exceeds its execution-time
hint, it falls back to querying the whole database and reports ``full_search: true``.
Both queries carry a ``MAX_EXECUTION_TIME`` hint, because an autocomplete that takes
seconds is worse than one that answers approximately.

**Without the join, a** ``contains`` **search of a narrow column may read its full-text
index.** The columns with a ``FULLTEXT`` index
(:func:`~opus_import.schema_files.packaged_fulltext_columns`, :ref:`dev_guide_table_schemas`)
can be matched with ``MATCH(<column>) AGAINST (%s IN BOOLEAN MODE)`` as well as with the
``LIKE`` every string search uses (:func:`~opus_app.apps.tools.sql_builder.fulltext_match`,
added by :func:`~opus_app.apps.search.views.get_string_query` with ``fulltext``). The
phrase searched for is the longest run of letters, digits and underscores in the typed
text, in double quotes: the ngram parser breaks a token at any other character, and
boolean mode reads several of them as operators, so such a run is the part of the text the
index holds. Every value that contains the text contains the run, so the index finds every
row the ``LIKE`` would; the ``LIKE`` then keeps only the rows that contain the whole text,
so the choices are the ones the ``LIKE`` alone gives.

The two find their rows in opposite ways. ``LIKE`` walks the column's key in order and
stops once it has one more value than the limit, which is quick when many values match and
slow when few do, as it then reads the whole key; the index reads every row that holds the
run, which is quick when few do and slow when many do. So the query from every observation
runs up to three statements, each the next only when the server gives up on the one
before (:func:`~opus_app.apps.tools.db_utils.is_abandoned_query_error`: the statement ran
out of its ``MAX_EXECUTION_TIME``, or the full-text search outgrew the server's
``innodb_ft_result_cache_limit``):

1. ``LIKE`` alone, under ``STRINGCHOICE_SIMPLE_LIKE_TIME_THRESHOLD`` (50 ms by default;
   0 skips this statement, so the index is tried first);
2. the index beside the ``LIKE``, under ``STRINGCHOICE_FULL_SEARCH_TIME_THRESHOLD2``;
3. ``LIKE`` alone under ``STRINGCHOICE_FULL_SEARCH_TIME_THRESHOLD2``, the statement a
   column without an index runs, so the answer is never emptier than ``LIKE`` alone would
   give. When the server gives up on it too there are no choices.

Text with no run of two characters, any other query type, and a column without an index
run only the last of these. The restricted query, joined to the search's results, always
uses ``LIKE`` alone: its cost is bounded by the search, and the index, which reads every
matching row of the table whatever the search holds, is slower there.

**The matched portion is highlighted** by re-applying the user's pattern to each
suggestion. It uses the third-party ``regex`` module rather than :mod:`re`, because that
is closer to the ICU regular expression library MySQL uses; and a pattern that fails to
compile here is swallowed, because the highlighting is cosmetic and the results are not.

Results are cached in the Django cache, under a key
(:func:`~opus_app.apps.search.views.string_choices_cache_key`) whose variable part is the
SHA-256 of the field, the partial query, the search's id, the query type and the limit --
hashed to a fixed width, because the partial query is the user's own text and the key
could otherwise outgrow memcached's limit on a key's length. ``reqno`` is added after the
caching, so it is never cached.

.. _dev_guide_webapp_search_url_to_params:

Turning a URL into a search
---------------------------

url_to_search_params
~~~~~~~~~~~~~~~~~~~~

:func:`opus_app.apps.search.views.url_to_search_params`

The main routine, and the one to read first. It takes a request's query mapping and
returns the ``(selections, extras)`` pair everything downstream works in. Its own
docstring is the authoritative statement of the shapes; the summary is:

* **selections** -- keyed by qualified column name, each value a list with one entry per
  ORed clause.
* **extras** -- ``'qtypes'``, ``'units'`` and ``'order'``.

Five flags change what it does:

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

Four of its behaviors are relied on elsewhere:

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
ORDER BY terms and reports which ``obs_`` tables and which ``mult`` joins they require.
A mult field sorts by the text of the label its ``mult`` row carries rather than by the
id stored in the row, and never by the row's ``disp_rank``, which is why sorting can
pull in a join the search itself does not need. The surface geometry selector,
``obs_surface_geometry_name.target_name``, is the exception: an observation has one of
its rows per body, so it sorts by
:func:`~opus_app.apps.search.views.selector_label`, one label per observation, and asks
for no join.

.. _dev_guide_webapp_search_cache:

Storing a search's results
--------------------------

:ref:`dev_guide_webapp_search_flow` explains how a search's results are stored; these are
the functions that do it.

:func:`~opus_app.apps.search.views.search_hash`
    Returns the SHA-256 hash that identifies a search: the hash of a JSON list of its
    selections, qtypes, units and sort order. Qtypes and units for fields that are not
    being searched are left out.

:func:`~opus_app.apps.search.views.set_user_search_number`
    Returns the search's number, its ``user_searches`` ``id``, adding a row if the search
    is new. It looks in the Django cache first, under
    :func:`~opus_app.apps.search.views.search_number_cache_key`. If the search is not
    there, it inserts a row, and if another request inserted the same search first, it
    reads that row instead. It updates ``last_used_at`` at most once a day, and never
    waits for a request that is writing the search's results. Returns None only when the
    other request's row was pruned before it could be read. Without memcached each worker
    has its own cache, so each worker looks the search up in the database once.

:func:`~opus_app.apps.search.views.get_search_results`
    Returns the search's number and result count, first storing its results if they are
    not stored yet, or None if either fails. ``_build_search_results`` stores them: it
    locks the search's ``user_searches`` row, writes the results with one ``INSERT INTO
    search_results ... SELECT``, and fills in ``result_count``, ``results_built_at`` and
    ``last_used_at``, all in one transaction. A second request for the same new search
    waits for the lock, for up to ``[django] search_build_timeout`` seconds, and then
    uses the first request's results. If the wait runs out it returns None, which the
    caller answers with a 500
    (:func:`~opus_app.apps.tools.app_utils.http500_search_cache_failed`). If the search's
    row is gone, or holds another search's hash, the search is added again, once. It
    must not be called inside a transaction, because adding the search and storing its
    results each commit on their own.

:func:`~opus_app.apps.search.views.get_search_id`
    The same, returning only the number. The results, metadata and cart views join the
    search's results through it, as
    :func:`~opus_app.apps.tools.sql_builder.search_results_source`.

:func:`~opus_app.apps.search.views.search_results_join_condition`
    The condition that ties a table's rows to a search's results.

.. _dev_guide_webapp_search_warm:

Warming the common searches
---------------------------

The empty search, in the default sort, is the search every visitor starts with, and most
next choose one value of a general constraint. A search's results are built in
``search_results`` the first time anyone asks for it and its answers are cached in
memcached, and a deploy brings a database with no search built and an empty memcached, so
the first visitors after it would pay for all of them. ``opus_manage warm_search``
(:mod:`opus_app.apps.search.management.commands.warm_search`) asks for them once, from the
deploy, instead.

It asks the running site's API over HTTP, as a browser would, rather than computing cache
keys or building searches itself: a key depends on the search's hash, which depends on
``DEFAULT_SORT_ORDER``, on how ``parse_order_slug`` resolves it through ``param_info``, on
:func:`~opus_app.apps.tools.app_utils.sort_dictionary` and on
:func:`~opus_app.apps.tools.app_utils.strip_numeric_suffix`, so only the views compute it
correctly. No view knows it is being warmed, and nothing is stored that a visitor's
request would not store. Asking over HTTP also reaches the web server's workers, several at
a time, so each is past its first request (:ref:`dev_guide_webapp_search_paraminfo_cache`).

:func:`~opus_app.apps.search.management.commands.warm_search.warm_requests`
    The empty search's requests, in order: its result count; its first page through
    ``__api/dataimages.json``, as the results page asks for it; the range endpoints of each
    widget in ``DEFAULT_WIDGETS`` that is a range; the menu, which lists the triggered
    tables, for the empty search the base tables; and the mult counts of every mult field,
    the default widgets first.

:func:`~opus_app.apps.search.management.commands.warm_search.value_search_requests`
    One common search's requests, for one value of one field of
    :data:`~opus_app.apps.search.management.commands.warm_search.COMMON_SEARCH_FIELDS`:
    the same count, the first page as the results page asks for it, the default widgets'
    fan-out and menu, and the searched field's own counts, which its widget shows.

:func:`~opus_app.apps.search.management.commands.warm_search.api_fields`
    The fields, and which are mults and which ranges, from ``api/fields.json``.

:func:`~opus_app.apps.search.management.commands.warm_search.counted_values`
    A common field's values, from the empty search's counts for it, so that each is a
    value some observation holds.

The empty search's count is asked for first and alone, since it builds the results every
other request of the empty search reads; the rest are then in flight ``--parallel`` at a
time, each common search's requests in order so that its count builds its results before
its pages read them. ``--url`` names the API root; without it the command asks
``public_url`` under ``BASE_PATH``, where the web server serves the application
(:func:`~opus_app.apps.search.management.commands.warm_search.default_site_url`). A
request that does not answer 200, or gets no answer, makes it exit with failure after the
others; the deploy reports that as a warning. The built results are rows of the database,
so a search warmed under any cache backend is found built afterwards.

Turning a search into SQL
-------------------------

``_search_select``
    Walks the selections in sorted order -- sorted so that the SQL a given search
    produces is reproducible, which is what the golden-response suite pins -- and
    dispatches on each field's form type. It collects the ``obs_`` tables and the
    ``mult`` joins the clauses and the ordering need, assembles the joins, and returns a
    :class:`~opus_app.apps.tools.sql_builder.Select` with no columns and no ORDER BY,
    together with the search's order as terms. ``_build_search_results`` adds the
    columns it stores: the search's number, ``ROW_NUMBER()`` over those terms, and
    ``obs_general.id``.

:func:`~opus_app.apps.search.views.construct_query_string`
    The same search as a plain statement and its parameters: the one column
    ``obs_general.id``, ordered by the search's order.

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

Mult fields are handled inline in ``_search_select``: the user's readable labels are
looked up in the worker's copy of the field's ``mult`` rows
(:func:`~opus_app.apps.tools.import_constants.mult_table`) to get their ids, and a
``GROUP`` field becomes an ``IN`` test while a ``MULTIGROUP`` field becomes an OR of JSON
containment tests, because it holds a list. The surface geometry selector,
``obs_surface_geometry_name.target_name``, is the one field whose category holds several
rows of an observation, one per body, so its test is put as ``EXISTS (SELECT 1 FROM
obs_surface_geometry_target AS obs_surface_geometry_name WHERE
obs_surface_geometry_name.obs_general_id = obs_general.id AND ... IN (...))`` and asks for
no join: a join would repeat an observation once for each selected body it has.

:func:`~opus_app.apps.search.views.selector_label` is how the selector appears as a
results column or a sort order, for the same reason: a subquery correlated with
``obs_general`` giving the alphabetically first label (``MIN`` of ``mult.label``) of the
observation's bodies -- of the bodies the search selects when it constrains the field,
of every body otherwise, as for the cart -- and NULL for an observation with none. A
mult field sorts by and shows its label, so the column and the sort agree.

``_valid_regex`` is how a user's regular expression is checked: **by asking the server**,
since OPUS runs the expression through MySQL rather than through Python, and only MySQL
knows what it will accept. Each worker remembers the patterns the server accepted, up to
``_REGEX_CACHE_SIZE`` of them, and asks again about one it refused, because a lost
connection is refused the same way a bad pattern is.

.. _dev_guide_webapp_search_paraminfo_cache:

The ``param_info`` lookup, and its cache
----------------------------------------

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
  the repository, so a change to ``param_info`` needs the worker processes restarted; see
  :ref:`user_guide_deployment_after_import`.
* It is a plain dictionary rather than an :func:`functools.lru_cache`, because several
  callers **mutate** the row they are given, so each needs its own copy.

``_get_param_info_by_qualified_name`` is the other direction -- a ``table.column`` name to
its row -- and ``is_single_column_range`` asks the same question of the name without its
numeric suffix. The slug cache cannot answer them, so they share a second module-level
dictionary keyed by table and column, which also caches misses and is never cleared.
Its keys are names the code built from rows, never from a request, so it holds at most
one entry per column and suffix. ``_get_param_info_by_qualified_name`` returns a copy, for
the same reason the slug lookup does.

The join helpers
----------------

:func:`~opus_app.apps.search.views.add_obs_table_joins`
    LEFT JOINs each category's table onto ``obs_general`` on the ``obs_general_id`` it
    carries. **The joins are LEFT** because an observation with no row in one of those
    tables must still appear in the result, with that table's columns null. A category
    is resolved by :func:`~opus_app.apps.tools.db_utils.resolve_category`, from the
    worker's copy of ``table_names``: a table is its own category, and a surface geometry
    category is ``obs_surface_geometry_target`` joined under the category's name, so that
    every ``<category>.<column>`` reference reads it. A body's category,
    ``obs_surface_geometry__<target>``, adds ``AND <category>.target_name = %s`` with the
    body's id, so a search naming two bodies joins the table twice, once for each.

:func:`~opus_app.apps.search.views.add_mult_table_joins`
    LEFT JOINs ``mult`` onto each ``obs_`` column holding a mult id, once for each
    column, under the column's alias
    (:func:`~opus_app.apps.tools.app_utils.mult_alias`), matching both the field's
    ``field_id`` and the id (:func:`~opus_app.apps.tools.sql_builder.mult_join`). For a
    MULTIGROUP column, which holds a JSON list, the join key is the list's first element.

.. _dev_guide_webapp_search_forms:

The search form
---------------

:mod:`opus_app.apps.search.forms` is the Django form the Search tab's widgets are built
from. :class:`~opus_app.apps.search.forms.SearchForm` is constructed with a mapping of
slug to value and grows one input per slug, choosing what kind from the field's
``param_info`` row:

* a **string** field gets a text input plus the query-type dropdown beside it;
* a **range** field gets a labeled endpoint input, and gets a query-type dropdown
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
``scripts/models/create_opus_models.sh`` from a populated database. Its model classes
are:

* one per ``obs_`` table;
* ``Mult``, ``MultField`` and ``MultGroup``, one per mult table;
* ``Partables``, ``TableNames`` and ``UserSearches``;
* and a ``ZZ``-prefixed model for every other table the database happens to hold -- the
  Django contrib tables, and the OPUS tables that have hand-written models in the apps
  that own them.

Four of the generated models are read through
:mod:`~opus_app.apps.tools.import_constants`:

.. py:class:: opus_app.apps.search.models.TableNames

   One row per category: its label, whether the interface shows it (``display``), its
   place in the display order (``disp_order``), and for a category that is not a table of
   its own the table its rows are in (``physical_table``) and the surface geometry body
   it keeps to (``target_name``).

.. py:class:: opus_app.apps.search.models.Partables

   One row per trigger: an observation whose ``trigger_col`` in ``trigger_tab`` holds
   ``trigger_val`` brings the table ``partable`` into its results and its metadata.

.. py:class:: opus_app.apps.search.models.MultField

   One row per mult field: its ``field_id``, its ``qualified_name`` and whether its
   values are pinned (:ref:`dev_guide_database_schema_mult`).

.. py:class:: opus_app.apps.search.models.Mult

   One row per value of a mult field, keyed by the composite primary key
   ``(field_id, id)``: the value, its label, its ``disp_rank``, whether it is displayed
   and its group. The search widget lists a field's displayed values in ``disp_rank``
   order, and its groups in the ``group_rank`` order of ``MultGroup``.

**The ``ZZ`` prefix is the generator's way of saying "a model exists for this table and
nothing should use it."** The class name is otherwise the table name with each
underscore-separated segment title-cased and the underscores removed, which is exactly
the transformation the runtime lookup applies:
:func:`~opus_app.apps.tools.db_utils.table_model_from_name` builds a class name that
way. The mult lookups use the ``Mult`` model and select a field's rows by
``field_id``.

Regenerating it
~~~~~~~~~~~~~~~

``scripts/models/create_opus_models.sh``, run from the repository root against a fully
imported database. It runs Django's ``inspectdb``, applies the prefixing and the
foreign-key repairs -- every relation to ``ObsGeneral`` is given
``related_name='%(class)s_general_id'`` and ``db_column='obs_general_id'``, whether
``inspectdb`` wrote it as a foreign key or, for a table whose primary key is
``obs_general_id``, as a one-to-one field -- makes ``UserSearches.search_hash`` a
``BinaryField`` (``inspectdb``
reads a ``BINARY`` column as text, which would not return a digest's bytes unaltered),
and formats the result.

Consequences worth knowing:

* A hand edit does not survive the next regeneration. The file is excluded from the
  linter and carries no docstrings for the same reason, and the API reference leaves it
  out, naming it on the reference's landing page so that a reader who cannot find it is
  told why.
* **A new OPUS table does not exist to the web application until this has been run.**
  A surface geometry body an import brings needs no regeneration: its category is rows
  of ``table_names``, ``param_info`` and ``partables``, read through the one
  ``ObsSurfaceGeometryTarget`` model.
* ``inspectdb`` writes a composite primary key as ``CompositePrimaryKey`` and its foreign
  key column as a ``ForeignKey`` named ``obs_general``, which the repairs above annotate,
  as in ``ObsFiles`` and ``ObsSurfaceGeometryTarget``. The foreign keys exist only once
  finalization has added them, so the database it runs against is a finalized one.
* ``search_results`` is read through no model: every query joins one search's rows of
  it as a derived table, which is the reason :mod:`opus_app.apps.tools.sql_builder`
  exists.

``UserSearches`` is the one generated model worth reading: its unique ``search_hash`` is
what makes a search's number stable, and :ref:`dev_guide_webapp_search_flow` describes
how that is used.

API reference
-------------

:doc:`api_opus_app.apps.search`
