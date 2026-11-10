.. _dev_guide_architecture:

Architecture
============

OPUS is two programs joined by one database. The import pipeline writes the database from
the PDS holdings; the Django application reads it and answers requests. Nothing flows the
other way -- the web application never writes an ``obs_`` table -- and the two share only
:mod:`opus_config`, :mod:`opus_support`, and their understanding of what the tables mean.

This is the one-page map. Read it before either subsystem's chapters:
:ref:`dev_guide_import` for the pipeline, :ref:`dev_guide_webapp` for the application.

.. mermaid::
    :zoom:

    flowchart LR
        holdings[(PDS3 and PDS4 holdings)]
        import[opus_import]
        db[(MySQL: the OPUS database)]
        app[opus_app]
        user([A scientist, or a program using the API])
        logs[(Apache access logs)]
        analyzer[opus_log_analyzer]

        holdings --> import
        import --> db
        db --> app
        app --> user
        user --> app
        app --> logs
        logs --> analyzer

.. _dev_guide_architecture_import:

The import pipeline
-------------------

An import run turns one PDS index file into one row per observation in each of the tables
that observation belongs to.

.. mermaid::
    :zoom:

    flowchart TD
        A[A bundle descriptor on the command line] --> B[config_bundle_info:<br/>which index files and which obs class]
        B --> C[pdstable / pdsfile:<br/>read the primary index and its supplements]
        C --> D[One obs class instance for the bundle]
        D --> E[For each index row:<br/>replace the metadata, then call one<br/>field_obs_table_column method per column]
        E -->|each bundle deleted, then loaded:<br/>a fresh import or an append| G[(Observation tables: obs_*, mult_*)]
        G -->|finalization| H[(Auxiliary tables:<br/>param_info, table_names, partables)]

There is one set of tables, and every import writes into it. An import into a schema
that is not served yet -- one with no ``schema_version`` row -- is a **fresh import**: the
observation tables are created with only the keys a load needs, and finalization adds the
remaining keys once at the end. An import into a finished schema is an **append**, into
the tables with their keys in place; it marks the schema ``appending`` first, so a web
application that loads it refuses to serve it until finalization has run again and the
schema is marked ready. On both paths each bundle is deleted before it is loaded, and a
bundle registry keeps a schema with an unfinished bundle from being finalized or marked
ready.
:ref:`dev_guide_import_write_paths` is the whole of it.

The auxiliary tables are built after the observation tables, but only ``param_info`` is
derived from what was imported. ``table_names`` lists the observation tables that
actually exist, while ``partables`` walks the configuration maps alone, so a mission that was never
imported still gets a ``partables`` row.

:ref:`dev_guide_import_steps` states the order the steps run in, what forces each part of
it, and what each auxiliary table is built from.

.. _dev_guide_architecture_obs:

The obs class hierarchy
-----------------------

The pipeline's largest structure is the family of classes that computes a column's
value, and :ref:`dev_guide_import_obs` is where it is described. The family's shape is
five layers, root outward:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Layer
     - Answers
   * - :class:`~opus_import.obs.obs_base.ObsBase`
     - What every observation shares, plus the questions only a PDS version or an
       instrument can answer.
   * - The PDS-version bases
     - What PDS3 and PDS4 decide.
   * - One module per OPUS table
     - That table's field methods.
   * - One module per mission
     - What an instrument's archives share.
   * - One module per bundle or volume set
     - How one particular archive spells things.

:ref:`dev_guide_import_obs` has the class diagram, the contracts and the method
resolution order; :ref:`dev_guide_import_obs_classes` catalogs every mission and leaf
class.

.. _dev_guide_architecture_webapp:

The web application
-------------------

A request arrives at one of the routes :mod:`opus_app.urls` assembles, is answered by a
view, and -- for anything that searches -- reaches the database through the rows of
``search_results`` built once per distinct search.

.. mermaid::
    :zoom:

    flowchart TD
        R([HTTP request]) --> U[opus_app.urls:<br/>each app contributes its routes]
        U --> V[The view, wrapped in api_view]
        V --> P[url_to_search_params:<br/>the query string becomes<br/>selections and extras]
        P --> Q[get_search_id:<br/>register the search, and build<br/>its search_results rows once]
        Q --> S[sql_builder.Select:<br/>join the obs_ and mult_ tables]
        S --> D[(MySQL)]
        D --> F[Format as JSON, CSV or HTML]
        F --> RESP([HTTP response])
        V -.->|no search| F

Three parts of that flow are worth knowing before changing any of it, and each has a
chapter of its own.

**Every handler that answers an API call is wrapped in**
:func:`~opus_app.apps.tools.app_utils.api_view`. It records the call, turns an
:exc:`~opus_app.apps.tools.app_utils.Http400Error` raised anywhere inside the handler
into an HTTP 400, turns any other unhandled exception into an HTTP 500 logged with its
traceback, and applies the fault-injection knobs the configuration file carries. The
exceptions Django answers specifically are re-raised rather than absorbed, so each keeps
the response and the logging Django gives it. :ref:`dev_guide_webapp_errors` is the
detail.

**A search becomes rows of** ``search_results``.
:func:`~opus_app.apps.search.views.url_to_search_params` turns the query string into the
two dictionaries the rest of the search code works with, and
:func:`~opus_app.apps.search.views.get_search_id` then registers the search in
``user_searches`` and, the first time anyone makes it, writes the ids of the matching
observations into ``search_results`` in sort order. Every later query -- a page of
results, a count, a set of file URLs -- joins against those rows rather than re-running
the search. :ref:`dev_guide_webapp_search_flow` walks all four
steps.

**The wide joins are assembled, not written.**
:mod:`opus_app.apps.tools.sql_builder` builds the statements that join the ``obs_``
tables to each other and to the ``mult_`` tables holding their enumerated values. Values
are always passed as parameters, and identifiers are validated before they are quoted.
:ref:`dev_guide_webapp_tools_sql_builder` says what that buys and where the two
exceptions are.

The Django apps are described across :ref:`dev_guide_webapp_tools`,
:ref:`dev_guide_webapp_search`, :ref:`dev_guide_webapp_results` and
:ref:`dev_guide_webapp_ui`.

The database
------------

:ref:`dev_guide_database_schema` describes every table OPUS uses and what each column
means. The two ideas to carry into any other chapter:

* An ``obs_*`` table corresponds one-for-one to a "Constraints" category in the user
  interface, and a row is one observation. ``obs_general`` is the master table: every
  observation has a row there, and every other table's rows hang off it.
* A field whose value comes from a fixed set stores an integer index into a ``mult_``
  table rather than the value itself, which is what makes the checkbox searches fast.
  :ref:`dev_guide_table_schemas` describes how a column declares that.

What each subsystem owns
------------------------

The division of responsibility, in one table, because several questions turn on it:

.. list-table::
   :header-rows: 1
   :widths: 34 33 33

   * - Thing
     - Written by
     - Read by
   * - The ``obs_*`` and ``mult_*`` tables
     - the import pipeline
     - the web application
   * - ``param_info``, ``table_names``, ``partables``
     - the import pipeline
     - the web application
   * - ``contexts``, ``definitions``
     - the import pipeline
     - the web application
   * - ``cart``
     - the web application (created by the import)
     - the web application
   * - ``user_searches`` and ``search_results``
     - the web application (created and reset by the import, pruned by
       ``opus_manage prune``)
     - the web application
   * - Django's contrib tables
     - ``opus_manage migrate``
     - Django
   * - ``search/models.py``
     - a script, from a populated database
     - the web application

Nothing in the pipeline imports :mod:`opus_app`, and nothing in the application imports
:mod:`opus_import`. The two shared packages are what they agree through:
:mod:`opus_config` for the installation's settings, and :mod:`opus_support` for the unit,
time and angle conversions both have to perform identically. :ref:`dev_guide_config` and
:ref:`dev_guide_opus_support` describe them.

API reference
-------------

:doc:`api_reference`
