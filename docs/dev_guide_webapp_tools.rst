.. _dev_guide_webapp_tools:

The Shared Machinery: the ``tools`` App
=======================================

:mod:`opus_app.apps.tools` is what every other app shares. It is a Django app so
that its two dictionary models are registered, but it routes no URLs and serves no
pages: everything in it is called from somewhere else.

Each of its modules is covered in full below.

.. list-table::
   :header-rows: 1
   :widths: 34 66

   * - Module
     - Responsibility
   * - :mod:`~opus_app.apps.tools.app_utils`
     - The API-view decorator, the API-call log, the response builders, and the text of
       every error message the API can return.
   * - :mod:`~opus_app.apps.tools.sql_builder`
     - Assembling raw SQL from structure instead of from string concatenation.
   * - :mod:`~opus_app.apps.tools.db_utils`
     - Finding a model by table name, and the labels behind the mult ids.
   * - :mod:`~opus_app.apps.tools.import_constants`
     - Each worker's copy of the tables only an import changes.
   * - :mod:`~opus_app.apps.tools.file_utils`
     - Lookups against ``obs_files``: an observation's products, its preview images, and
       the browse products the Details tab shows.
   * - :mod:`~opus_app.apps.tools.dictionary`
     - The two data-dictionary tables and the tooltip lookup made against them.
   * - :mod:`~opus_app.apps.tools.file_size`
     - Rendering a byte count the way the cart displays it.
   * - :mod:`~opus_app.apps.tools.opus_middleware`
     - The one OPUS-authored middleware.

.. _dev_guide_webapp_tools_app_utils:

opus_app.apps.tools.app_utils
-----------------------------

Read :func:`~opus_app.apps.tools.app_utils.api_view` first. Every handler that answers
an API call is wrapped in it, and it is what turns an exception into a response, records
the call, and applies the fault-injection knobs. A handler that is a thin private wrapper
around a public one is not decorated itself; the wrapping it gets is its twin's.

:func:`~opus_app.apps.tools.app_utils.api_view`
    The decorator. At **decoration** time it inspects the handler's signature once to
    see whether it wants an ``api_code``. At **call** time it: assigns the call number and
    records the start time; supplies ``api_code`` if the handler declared it; consults the
    injected-fault roll, and runs the handler only if that returned nothing; and then
    handles the outcome as described in :ref:`dev_guide_webapp_errors`.

:exc:`~opus_app.apps.tools.app_utils.Http400Error`
    Raised by a handler when the *request itself* is malformed -- a bad slug, a
    non-numeric limit, an unknown unit. The decorator turns it into an HTTP 400 whose
    body is the OPUS error page. Contrast with :exc:`django.http.Http404`, which means a
    resource named in the URL path does not exist.

Response builders
~~~~~~~~~~~~~~~~~

:func:`~opus_app.apps.tools.app_utils.json_response`
    :func:`json.dumps` with the ``application/json`` content type.

:func:`~opus_app.apps.tools.app_utils.csv_response`
    A CSV attachment, with an optional header row. The filename is given without its
    extension.

:func:`~opus_app.apps.tools.app_utils.wrap_http500_string`
    Wraps a message in the ``<div id="info">`` the 500 body uses. **This is the one place
    in OPUS where an error message becomes raw HTML instead of going through a template,
    so it is also the one place that has to escape.** The 400 and 404 builders render
    through templates, which escape already.

The API-call log
~~~~~~~~~~~~~~~~

:func:`~opus_app.apps.tools.app_utils.enter_api_call`
    Increments the process-global call counter, records the start time, and -- only when
    ``log_api_calls`` is set -- logs the path, the keyword arguments and the query
    string.

:func:`~opus_app.apps.tools.app_utils.exit_api_call`
    Logs the elapsed time and a rendering of the response, truncated to 240 characters,
    with a binary body reported as such rather than dumped. It then applies the
    ``fake_api_delays`` sleep, **after** the log line, so a delayed response is still
    recorded at the time it was produced.

Request helpers
~~~~~~~~~~~~~~~

:func:`~opus_app.apps.tools.app_utils.get_session_id`
    The session key, creating a session if there is none. It also honors a
    ``__sessionid`` query parameter, intended for internal testing -- but **nothing
    restricts it to a test request**, so any caller can name the session a handler will
    read and write.

:func:`~opus_app.apps.tools.app_utils.get_reqno`
    The ``reqno`` a private handler echoes back, or None when it is absent, non-integer
    or negative. Every private handler treats None as a bad request.

Slug and name helpers
~~~~~~~~~~~~~~~~~~~~~

:func:`~opus_app.apps.tools.app_utils.strip_numeric_suffix` and :func:`~opus_app.apps.tools.app_utils.get_numeric_suffix`
    A range field's two endpoints are named by the same slug with a ``1`` or ``2``
    appended; these split the two apart.

:func:`~opus_app.apps.tools.app_utils.cols_to_slug_list`
    A comma-separated slug list, or an empty list.

:func:`~opus_app.apps.tools.app_utils.mult_alias`
    The alias a statement joins the ``mult`` table under for a ``<table>.<column>``
    field: ``mult_`` and the name with its period replaced by an underscore, such as
    ``mult_obs_general_planet_id``. A statement that reads several mult columns joins
    ``mult`` once for each, so each join needs a name of its own.

:func:`~opus_app.apps.tools.app_utils.sort_dictionary`
    A copy with the keys in sorted order, which is what makes a search's hash stable.

:func:`~opus_app.apps.tools.app_utils.download_filename`
    The name of a temporary download: a fixed prefix, a timestamp, the kind of file, one
    random letter, and optionally an OPUS ID. No extension -- the caller adds one.

:func:`~opus_app.apps.tools.app_utils.get_git_version`
    Despite the name, the installed distribution's version. It is shown on the About page
    and is what the templates' ``?version=`` cache-busting suffix is built from.

The error message texts
~~~~~~~~~~~~~~~~~~~~~~~

Each function here returns one message. The ``http400_``, ``http404_`` and
``http500_`` prefix records which status the message is raised with, and each takes
the request -- or a path as a string, where no request is available.

They are here, rather than at the sites that raise them, so that the same fault reads the
same way wherever it is found, and so that changing the wording is one edit.

.. list-table::
   :header-rows: 1
   :widths: 44 56

   * - Function
     - Raised when
   * - :func:`~opus_app.apps.tools.app_utils.http400_bad_or_missing_reqno`
     - A private handler was called without a usable ``reqno``.
   * - :func:`~opus_app.apps.tools.app_utils.http400_missing_opus_id`
     - A handler that needs an OPUS ID was given none.
   * - :func:`~opus_app.apps.tools.app_utils.http400_bad_or_missing_range`
     - The cart's ``range`` argument is missing or malformed.
   * - :func:`~opus_app.apps.tools.app_utils.http400_bad_download`,
       :func:`~opus_app.apps.tools.app_utils.http400_bad_recyclebin`,
       :func:`~opus_app.apps.tools.app_utils.http400_bad_collapse`
     - A boolean-valued argument did not parse as 0 or 1.
   * - :func:`~opus_app.apps.tools.app_utils.http400_bad_limit`,
       :func:`~opus_app.apps.tools.app_utils.http400_bad_startobs`,
       :func:`~opus_app.apps.tools.app_utils.http400_bad_pageno`,
       :func:`~opus_app.apps.tools.app_utils.http400_bad_offset`
     - A paging argument is out of range or is not a number.
   * - :func:`~opus_app.apps.tools.app_utils.http400_search_params_invalid`
     - :func:`~opus_app.apps.search.views.url_to_search_params` could not parse the
       query string at all.
   * - :func:`~opus_app.apps.tools.app_utils.http400_unknown_slug`,
       :func:`~opus_app.apps.tools.app_utils.http400_unknown_units`,
       :func:`~opus_app.apps.tools.app_utils.http400_unknown_category`,
       :func:`~opus_app.apps.tools.app_utils.http400_unknown_download_file_format`
     - The request named a field, a unit, a category or an archive format OPUS does not
       have.
   * - :func:`~opus_app.apps.tools.app_utils.http404_unknown_opus_id`
     - The URL named an observation that does not exist.
   * - :func:`~opus_app.apps.tools.app_utils.http404_unknown_format`
     - A handler was reached with a format it does not produce.
   * - :func:`~opus_app.apps.tools.app_utils.http404_no_request`
     - An internal fault: a handler was called with no usable request.
   * - :func:`~opus_app.apps.tools.app_utils.http500_search_cache_failed`,
       :func:`~opus_app.apps.tools.app_utils.http500_database_error`,
       :func:`~opus_app.apps.tools.app_utils.http500_internal_error`
     - The three server-side failures. All are HTML-wrapped and escaped.
   * - :func:`~opus_app.apps.tools.app_utils.http404_fake_error`,
       :func:`~opus_app.apps.tools.app_utils.http500_fake_error`
     - The injected faults.

.. _dev_guide_webapp_tools_sql_builder:

opus_app.apps.tools.sql_builder
-------------------------------

Most of the OPUS API is served by hand-written SQL rather than by the ORM, for two
reasons the module's own docstring states: the search results live in
``search_results``, which **has no Django model** and is joined as one search's rows in a
derived table (:func:`~opus_app.apps.tools.sql_builder.search_results_source`); and the
queries that join a search to its results are wide joins over the generated ``obs_*``
tables that are far clearer as SQL.

**This module is the one place allowed to turn Python values into SQL text.** Every call
site elsewhere describes the *structure* of its statement and lets this module render it,
which gives three properties uniformly:

**Identifiers are quoted and validated.**
:func:`~opus_app.apps.tools.sql_builder.quote_identifier` rejects anything outside
``[A-Za-z0-9_]`` before handing the name to the backend's quoting. Django's ``quote_name``
wraps a name in backticks but does not escape a backtick *inside* one, so validation, not
quoting, is what closes that hole -- and it matters because several identifiers are
computed at run time: the column names that come out of ``param_info``.

**Values are always parameters.** Anything that is data is rendered as a placeholder and
collected into a parameter list. There are exactly **two** exceptions, and both are
numbers that shape the statement rather than data it operates on, so both are checked
with an ``isinstance`` test against :class:`int` before being rendered literally:
``LIMIT``/``OFFSET``, and the ``MAX_EXECUTION_TIME`` optimizer hint. The hint is a
*comment*, and a server never scans a comment for placeholders; ``LIMIT`` would take a
placeholder, but the driver interpolates client-side and would quote a non-numeric value
into ``LIMIT '1'``, so the type check is the actual guarantee.

**Parameters come out in placeholder order.** A statement is rendered in a fixed clause
order and each clause contributes its parameters at the point its placeholders appear, so
a caller cannot get the ordering wrong by appending to the wrong list.

The shape of it
~~~~~~~~~~~~~~~

.. mermaid::
    :zoom:

    classDiagram
        class Expr {
            <<NamedTuple>>
            +sql
            +params
        }
        class Select {
            +add_column()
            +add_from()
            +add_from_source()
            +add_where()
            +add_group_by()
            +add_order_by()
            +limit()
            +offset()
            +build()
        }
        class FromSource {
            +source
            +joins
            +add_join()
            +append_join()
            +render()
        }
        class Join {
            +kind
            +source
            +on
            +render()
        }
        class Subquery {
            +select
            +alias
            +render()
        }
        class JSONTable {
            +source_column
            +value_column
            +alias
            +render()
        }
        class AliasedTable {
            +table
            +alias
            +render()
        }
        class ValueError {
            <<builtin>>
        }
        class SQLIdentifierError

        Select "1" *-- "many" FromSource : FROM
        FromSource "1" *-- "many" Join
        FromSource ..> Subquery : source may be
        FromSource ..> JSONTable : source may be
        FromSource ..> AliasedTable : source may be
        Join ..> Subquery : source may be
        Join ..> JSONTable : source may be
        Join ..> AliasedTable : source may be
        Subquery *-- Select
        Select ..> Expr : columns, WHERE, GROUP BY, ORDER BY
        Join ..> Expr : ON
        JSONTable ..> Expr : source column
        ValueError <|-- SQLIdentifierError

Reading it in three groups:

**The value.** :class:`~opus_app.apps.tools.sql_builder.Expr` is the whole vocabulary --
a rendered fragment of SQL and the parameters its placeholders consume. Every function in
the expression layer below returns one, and everything a statement is assembled out of is
one.

**The sources.** :class:`~opus_app.apps.tools.sql_builder.FromSource` is one table source
and the joins hanging off it; :class:`~opus_app.apps.tools.sql_builder.Join` is one of
those joins; and a source may be a plain table name, a
:class:`~opus_app.apps.tools.sql_builder.Subquery` -- which holds a whole
:class:`~opus_app.apps.tools.sql_builder.Select` under a mandatory alias -- a
:class:`~opus_app.apps.tools.sql_builder.JSONTable`, or an
:class:`~opus_app.apps.tools.sql_builder.AliasedTable`, a table under an alias.
The :class:`~opus_app.apps.tools.sql_builder.Subquery` case is why the diagram is not a
tree: a statement can hold a statement.

**The statement.** :class:`~opus_app.apps.tools.sql_builder.Select` owns the clause
order. It and :class:`~opus_app.apps.tools.sql_builder.FromSource` are the two mutable
classes here, each accumulating what a caller adds to it.
:exc:`~opus_app.apps.tools.sql_builder.SQLIdentifierError` is raised in one place --
:func:`~opus_app.apps.tools.sql_builder.quote_identifier` -- which every function and
every ``render`` method that emits an identifier calls, so it can surface from anywhere
in the module.

The expression layer
~~~~~~~~~~~~~~~~~~~~

:class:`~opus_app.apps.tools.sql_builder.Expr` is a named tuple of rendered SQL and the
parameters its placeholders consume. Everything below returns one.

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Function
     - Renders
   * - :func:`~opus_app.apps.tools.sql_builder.column`
     - A quoted column, optionally table-qualified.
   * - :func:`~opus_app.apps.tools.sql_builder.value`
     - A placeholder with the value bound. **The only way a value enters a statement.**
   * - :func:`~opus_app.apps.tools.sql_builder.count_star`,
       :func:`~opus_app.apps.tools.sql_builder.count_distinct`,
       :func:`~opus_app.apps.tools.sql_builder.sum_of`,
       :func:`~opus_app.apps.tools.sql_builder.min_of`,
       :func:`~opus_app.apps.tools.sql_builder.max_of`
     - The five aggregates OPUS uses.
   * - :func:`~opus_app.apps.tools.sql_builder.json_contains`
     - Whether a MULTIGROUP column's JSON list holds a value. A multiple-choice field
       stores a list of mult ids, so a search for one value asks whether the list
       contains it rather than whether the column equals it.
   * - :func:`~opus_app.apps.tools.sql_builder.json_extract_first`
     - The first element of such a list, which is what a MULTIGROUP field sorts and joins
       on, since it has no single value.
   * - :func:`~opus_app.apps.tools.sql_builder.angular_separation`
     - The angular distance between a longitude column and a target longitude, mapped
       into 0 to 180 degrees. **This is what makes a search that straddles zero degrees
       work.**
   * - :func:`~opus_app.apps.tools.sql_builder.binary_op`
     - A comparison, restricted to a fixed operator set so it cannot be handed arbitrary
       SQL text.
   * - :func:`~opus_app.apps.tools.sql_builder.columns_equal`
     - A join condition. It **takes no parameters at all** and raises if either side
       carries one -- which is the property that makes a join condition safe.
   * - :func:`~opus_app.apps.tools.sql_builder.is_null`,
       :func:`~opus_app.apps.tools.sql_builder.in_values`,
       :func:`~opus_app.apps.tools.sql_builder.in_sequence`
     - Null and membership tests. The two ``IN`` forms render the same statement; one
       binds a placeholder per value, the other binds the sequence as a single parameter.
   * - :func:`~opus_app.apps.tools.sql_builder.parenthesize`,
       :func:`~opus_app.apps.tools.sql_builder.join_exprs`,
       :func:`~opus_app.apps.tools.sql_builder.combine_exprs`
     - Grouping. :func:`~opus_app.apps.tools.sql_builder.join_exprs` adds no parentheses;
       :func:`~opus_app.apps.tools.sql_builder.combine_exprs` parenthesizes each
       operand first.
   * - :func:`~opus_app.apps.tools.sql_builder.between`,
       :func:`~opus_app.apps.tools.sql_builder.sort_order_range`
     - A range test with both bounds as parameters, and the window of a table numbered
       by ``sort_order`` that a page reads.
   * - :func:`~opus_app.apps.tools.sql_builder.row_number`
     - ``ROW_NUMBER() OVER (ORDER BY ...)``, or ``ROW_NUMBER() OVER ()`` given no
       terms. It numbers a search's results as they are stored, and numbers the cart in
       a sort order the same way.

:func:`~opus_app.apps.tools.sql_builder.ascii_comparable` is not an expression but the
value to bind for one: a caller's text, to be compared with a column in the ASCII
character set. MySQL refuses that comparison for text holding any other character, so the
text is folded as the accent-blind ``utf8mb4_0900_ai_ci`` compares it -- decomposed
(NFKD), its combining marks dropped -- and a character that still has no ASCII form is
replaced by ``opus_support.UNSTORED_ASCII_CHARACTER``, DEL, which the import refuses in
an ASCII column, so the comparison finds what it finds for any value the column does not
hold. A regular expression is folded with canonical decomposition alone (NFD, the
function's ``compatibility=False``): its accents still go, but a compatibility character
keeps no ASCII form, since that form may be an operator (a full-width ``．`` would become
``.``, which matches any character); it becomes DEL and matches only itself. Every
lookup by a caller's OPUS ID binds it this way, and a string search does for a column
:func:`~opus_app.apps.tools.db_utils.is_ascii_column` names
(:ref:`dev_guide_database_schema`). Code that pairs a value read from such a column with
the caller's text it was found by keys both with
:func:`~opus_app.apps.tools.sql_builder.ascii_collation_key`, the folded text without
its trailing spaces and in lower case, which two strings share exactly when the column's
``ascii_general_ci`` collation calls their folded forms equal.

The statement layer
~~~~~~~~~~~~~~~~~~~

:class:`~opus_app.apps.tools.sql_builder.Select`
    A SELECT assembled from its parts, rendered in a fixed clause order: columns, FROM
    with its joins, WHERE, GROUP BY, ORDER BY, LIMIT/OFFSET.
    :meth:`~opus_app.apps.tools.sql_builder.Select.add_from` returns the
    :class:`~opus_app.apps.tools.sql_builder.FromSource` rather than the statement, so
    that joins hang off the right source; everything else returns the statement for
    chaining. :meth:`~opus_app.apps.tools.sql_builder.Select.build` returns the SQL and
    its parameters.

:class:`~opus_app.apps.tools.sql_builder.FromSource` and :class:`~opus_app.apps.tools.sql_builder.Join`
    One table source and the joins hanging off it. A statement may have more than one
    source, rendered comma-separated -- and **the comma binds more loosely than JOIN**,
    which is what the cart's download summary and the queries that join a search to its
    results rely on. :meth:`~opus_app.apps.tools.sql_builder.FromSource.add_join` builds
    a join from its kind, source and condition;
    :meth:`~opus_app.apps.tools.sql_builder.FromSource.append_join` appends one built
    elsewhere, such as by :func:`~opus_app.apps.tools.sql_builder.mult_join`.

:class:`~opus_app.apps.tools.sql_builder.AliasedTable`
    A table joined under an alias, rendered ``<table> AS <alias>``: ``mult`` under a
    column's alias, and ``obs_surface_geometry_target`` under a surface geometry
    category's name.

:func:`~opus_app.apps.tools.sql_builder.exists`
    ``EXISTS (SELECT 1 FROM <source> WHERE <condition>)``, the form a condition on a
    table holding several rows of one observation takes, so that the observation is not
    repeated once for each row a join would match.

:func:`~opus_app.apps.tools.sql_builder.scalar_subquery`
    A :class:`~opus_app.apps.tools.sql_builder.Select` of one column and at most one row
    as a value, ``(SELECT ...)``, which may name the outer statement's tables.

:func:`~opus_app.apps.tools.sql_builder.mult_join`
    The join that reads one mult column's labels:
    ``LEFT JOIN mult AS <alias> ON <alias>.field_id = %s AND <alias>.id = <column>``,
    with the field's ``mult_field`` id as the parameter. The ``mult`` table holds every
    field's values, so a statement joins it once for each mult column it reads, each
    time under the column's alias
    (:func:`~opus_app.apps.tools.app_utils.mult_alias`), and each join reads ``mult``
    through its primary key.

:class:`~opus_app.apps.tools.sql_builder.Subquery`
    A :class:`~opus_app.apps.tools.sql_builder.Select` used as a table source, under a
    mandatory alias.

:func:`~opus_app.apps.tools.sql_builder.search_results_source`
    One search's rows of ``search_results`` as a
    :class:`~opus_app.apps.tools.sql_builder.Subquery`: ``(SELECT obs_general_id AS id,
    sort_order FROM search_results WHERE search_id = %s)`` under
    :data:`~opus_app.apps.tools.sql_builder.SEARCH_RESULTS_ALIAS`. The server merges a
    derived table this simple into the statement that names it, so a join on ``id``
    reads the table's ``(search_id, obs_general_id)`` key and a range of ``sort_order``
    its primary key.

:class:`~opus_app.apps.tools.sql_builder.JSONTable`
    Turns each element of a MULTIGROUP column's JSON list into its own row, so the
    elements can be counted. The mult-count endpoint is the caller.

:exc:`~opus_app.apps.tools.sql_builder.SQLIdentifierError`
    Raised when a name about to be used as an identifier is unsafe.

The module-level functions that render whole statements are
:func:`~opus_app.apps.tools.sql_builder.delete_from`,
:func:`~opus_app.apps.tools.sql_builder.delete_joined`,
:func:`~opus_app.apps.tools.sql_builder.insert_into_select` (which stores a search's
results in ``search_results``),
:func:`~opus_app.apps.tools.sql_builder.replace_into_values`,
:func:`~opus_app.apps.tools.sql_builder.replace_into_select` and
:func:`~opus_app.apps.tools.sql_builder.update`.

Two invariants in that list are deliberate. **A WHERE clause is required** by
:func:`~opus_app.apps.tools.sql_builder.delete_from` and
:func:`~opus_app.apps.tools.sql_builder.update`: there is no call site that empties a
table, and making it optional would let a caller emit one by leaving an argument out.
And the cart's writes go through ``REPLACE INTO`` rather than a delete followed by an
insert, because the cart table's unique key over the session and the observation turns a
concurrent second write into a replacement instead of a duplicate.

.. _dev_guide_webapp_tools_db_utils:

opus_app.apps.tools.db_utils
----------------------------

Model lookup by category name, and the labels behind the mult ids.

:func:`~opus_app.apps.tools.db_utils.table_model_from_name`
    ``obs_pds`` becomes ``ObsPds``, looked up in the ``search`` app. The return has no
    static type, because the class depends on the name.

:func:`~opus_app.apps.tools.db_utils.resolve_category`
    Where a ``param_info`` category's rows are, as a
    :class:`~opus_app.apps.tools.db_utils.ResolvedCategory`: the table's model, the table,
    the alias a statement names the table by, which is the category's name, and the
    surface geometry body's id the rows hold, or None. A category whose ``table_names``
    row names a ``physical_table`` -- every surface geometry category -- is that table
    under the category's name, with the row's ``target_name``; any other is the table of
    its name. Every view that reads a category as a source, a join or a model resolves it
    here; :meth:`~opus_app.apps.tools.db_utils.ResolvedCategory.restrict` adds a body's
    condition to a statement that reads the category. The ``table_names`` rows come from
    the worker's copy (:mod:`~opus_app.apps.tools.import_constants`).

:func:`~opus_app.apps.tools.db_utils.is_ascii_column`
    Whether a table's column is in the ASCII character set, which its generated model
    says by naming :data:`~opus_support.collation.ASCII_COLLATION` as the field's
    ``db_collation``.

:func:`~opus_app.apps.tools.db_utils.query_table_for_opus_id`
    One category's rows for one observation, filtering on ``opus_id`` for
    ``obs_general``, which holds it, and on ``obs_general``'s ``opus_id`` through the
    ``obs_general`` relation for every other table, and for a surface geometry body's
    category on the body's id as well.

:func:`~opus_app.apps.tools.db_utils.targets_for_opus_id` and :func:`~opus_app.apps.tools.db_utils.observation_has_body`
    The surface geometry bodies one observation has rows of, in one query, which answers
    for every body's category at once; the second asks it once per table and answers
    for one body's category from the result.

:func:`~opus_app.apps.tools.db_utils.lookup_pretty_value_for_mult` and :func:`~opus_app.apps.tools.db_utils.lookup_pretty_value_for_mult_list`
    A mult column stores the id of a ``mult`` row, so displaying it means a second
    lookup, which reads the worker's copy of the field's ``mult`` rows from
    :mod:`~opus_app.apps.tools.import_constants`. The field's absent value, whose stored
    value is the empty string, is reported as nothing unless the caller asks for its
    label.

The MySQL error numbers declared here for callers to match a database exception against
are ``MYSQL_TABLE_NOT_EXISTS``; ``MYSQL_EXECUTION_TIME_EXCEEDED``, which is how the
autocomplete endpoint learns its restricted query timed out; and
``MYSQL_LOCK_WAIT_TIMEOUT``, which
:func:`~opus_app.apps.tools.db_utils.is_lock_timeout_error` matches, and which is how a
request learns that it waited too long for another request storing the same search's
results.

.. _dev_guide_webapp_tools_import_constants:

opus_app.apps.tools.import_constants
------------------------------------

The ``table_names``, ``partables``, ``mult_field`` and ``mult`` tables hold the same rows
from one import to the next, so each worker process reads them on first use and answers
from memory after that: ``table_names``, ``partables`` and ``mult_field`` whole, and
``mult`` one field at a time. **Nothing here notices an import**: the deploy restarts the
workers after one (:ref:`dev_guide_webapp_caching`). A copy is built in full before it is
stored, so a thread never sees part of one; two threads that miss at once each read the
table, and one of the two equal copies is kept.

:func:`~opus_app.apps.tools.import_constants.table_names`, :func:`~opus_app.apps.tools.import_constants.displayed_table_names`, :func:`~opus_app.apps.tools.import_constants.get_table_name` and :func:`~opus_app.apps.tools.import_constants.partables`
    The rows, shared by every request in the process. A caller that sets an attribute
    on a row, as the menu does, copies it first.

:func:`~opus_app.apps.tools.import_constants.mult_field_id`
    The ``mult_field`` id of a field, by its ``<table>.<column>`` name, read from a copy
    of ``mult_field`` taken whole on first use. A name ``mult_field`` lacks raises
    :exc:`LookupError`.

:func:`~opus_app.apps.tools.import_constants.mult_table`
    One mult field's ``mult`` rows, as a
    :class:`~opus_app.apps.tools.import_constants.MultTable`, keyed by the field's
    ``<table>.<column>`` name: its rows by id, each a
    :class:`~opus_app.apps.tools.import_constants.MultRow` carrying ``id``, ``value``,
    ``label`` and ``disp_rank``, for showing a stored id as its label and for ordering
    the field's values; and its ids by label and by value, for turning a search's mult
    selection into ids. The absent value, stored as the empty string, is never a key by
    its value, and :attr:`~opus_app.apps.tools.import_constants.MultRow.is_absent` tells
    it apart. :meth:`~opus_app.apps.tools.import_constants.MultTable.ids_for` answers
    what the query ``label IN (...) OR value IN (...)`` over the field's rows answered,
    and asks the server instead when a name finds nothing or when the field holds a name
    that is not printable ASCII.

:func:`opus_support.collation.collation_key`
    **The server compares strings without regard to case or accent**
    (``utf8mb4_0900_ai_ci``), and the public API relies on it: ``planet=saturn`` finds
    the row labeled ``Saturn``. Every lookup here by a string compares the strings'
    keys. **The key is the collation only for printable ASCII**: it folds case and
    accents but does not ignore what the collation ignores, such as a soft hyphen or a
    control character, and it maps some characters onto others the collation keeps apart
    (``¨`` onto a space). Strings that are printable ASCII
    (:func:`~opus_app.apps.tools.import_constants.collates_as_key`) compare the same way
    under both. So a mult lookup goes to the server when a requested name is not printable
    ASCII, finds nothing, or searches a field that is not all printable ASCII; and
    ``get_metadata`` asks the server about a category list its copy does not match in
    full, that holds a name that is not printable ASCII, or that is looked up while a
    displayed table's label or name is not printable ASCII. The function lives in
    :mod:`opus_support` because the import keys its cache of a field's values the same
    way (:ref:`dev_guide_import_steps_do_import_mult`).

.. _dev_guide_webapp_tools_file_utils:

opus_app.apps.tools.file_utils
------------------------------

Lookups against ``obs_files``, the table listing every file of every observation. Every
function here starts from one or more OPUS IDs and returns files that belong to them.
**Nothing here writes to the database, and nothing here touches the filesystem** -- the
size and the checksum are columns the import wrote from a shelf.

:func:`~opus_app.apps.tools.file_utils.get_pds_products`
    An observation's PDS products, nested by OPUS ID, then by version, then by product
    type. ``loc_type`` selects what each entry is: ``'url'`` a public URL, ``'path'`` an
    on-disk path, ``'raw'`` a dictionary carrying both plus the checksum, the size and
    the category. A requested product type may carry ``@<version>``; a bare type matches
    the current version only, matching the download endpoint's behavior. Every requested
    OPUS ID appears in the result, keyed as the caller spelled it, even if it has no
    files. A spelling finds the stored ID it equals under the column's collation
    (:func:`~opus_app.apps.tools.sql_builder.ascii_collation_key`: any case, accents
    folded, trailing spaces ignored), so several spellings of one ID each get its files.
    The files are read newest
    version first, then by the product types' display order, and last by
    ``file_number``, so the files of one product type keep the order the import wrote
    them in.

:func:`~opus_app.apps.tools.file_utils.get_pds_preview_images`
    The preview images at one or more of the four sizes, from the JSON view set the
    import stored in ``obs_preview.preview_images``. A caller that read the JSON with
    a page of results passes it in; otherwise each observation's row is looked up by
    its OPUS ID. Each size contributes a URL,
    alternative text, a byte size and the two dimensions. A missing preview yields the
    "not found" placeholder, or is skipped entirely under ``ignore_missing``.

:func:`~opus_app.apps.tools.file_utils.get_displayed_browse_products`
    The medium and full-size browse products the Details tab shows, paired by their
    common basename. One observation can legitimately have several.

.. _dev_guide_webapp_tools_dictionary:

opus_app.apps.tools.dictionary
------------------------------

The two data-dictionary tables and the tooltip lookup against them.
:class:`~opus_app.apps.tools.dictionary.Contexts` is one namespace of terms and
:class:`~opus_app.apps.tools.dictionary.Definitions` is one term's definition within one
context; :ref:`dev_guide_dictionary` describes where their contents come from.

Both are **unmanaged**, because the import pipeline writes them and the web application
never does. Both came from Django's ``inspectdb``, and their field definitions are
reproduced verbatim: a field changed here would silently stop matching the table.

:func:`~opus_app.apps.tools.dictionary.get_definition` is the lookup, made against a
copy of ``definitions`` each worker process reads whole on first use and keeps, and
compared the way the server's collation compares
(:func:`~opus_support.collation.collation_key`).
:func:`~opus_app.apps.tools.dictionary.get_def_for_tooltip` is the tooltip's use of it: a
missing definition is logged as an error **except** under a ``MULT_`` context, because a
mult value legitimately has none.

They live in ``tools`` rather than in an app of their own because ``paraminfo``, ``ui``
and ``cart`` all use them.

.. _dev_guide_webapp_tools_file_size:

opus_app.apps.tools.file_size
-----------------------------

:func:`~opus_app.apps.tools.file_size.nice_file_size` renders a byte count the way the
cart displays it: powers of 1024, a single-letter suffix, and **the fractional part
truncated rather than rounded**, so 1,048,575 bytes reads as ``1023K`` and not ``1M``.

Its output is part of the public API -- the cart status endpoint reports it -- and it
appears in the golden response fixtures, so every string it produces is fixed rather than
a formatting choice open to revision.

.. _dev_guide_webapp_tools_middleware:

opus_app.apps.tools.opus_middleware
-----------------------------------

:class:`~opus_app.apps.tools.opus_middleware.StripWhitespaceMiddleware` is the one
OPUS-authored entry in ``MIDDLEWARE``, and it is last in the chain. It strips each line's
leading whitespace, collapses trailing whitespace to a newline, and drops blank lines from
any response whose content type is text.

Two things about it are worth knowing: a response beginning with a ``<!--NOSTRIP-->``
marker has the marker removed and is otherwise left alone, and a response carrying **no**
``Content-Type`` header at all -- which a cached 304 does not -- raises
:exc:`KeyError`, which the class documents rather than hides.

API reference
-------------

:doc:`api_opus_app.apps.tools`
