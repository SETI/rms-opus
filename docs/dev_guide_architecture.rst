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

    flowchart TD
        A[A bundle descriptor on the command line] --> B[config_bundle_info:<br/>which index files and which obs class]
        B --> C[pdstable / pdsfile:<br/>read the primary index and its supplements]
        C --> D[One obs class instance for the bundle]
        D --> E[For each index row:<br/>replace the metadata, then call one<br/>field_obs_table_column method per column]
        E --> F[(Import tables: imp_obs_*, imp_mult_*)]
        F --> G[(Permanent tables: obs_*, mult_*)]
        G --> H[(Auxiliary tables:<br/>param_info, table_names, partables)]

Every **imported** table is written to the import tables first -- the ones whose names
carry the ``table_temp_prefix`` from the configuration -- and copied over the permanent
tables only once the whole run has succeeded. A failed import therefore cannot leave the
web application serving half a bundle of observation metadata.
:ref:`dev_guide_import_two_namespaces` is the whole of that design.

The protection covers the imported tables and no others. ``cart`` is created directly in
the permanent namespace, and the ``cache_*`` and ``user_searches`` tables are dropped
there outright; a failed run can leave those already reset. They hold no imported data --
see :ref:`dev_guide_import_steps_do_cart` and :ref:`dev_guide_import_steps_do_django` --
which is why they are outside the copy.

The auxiliary tables come last because each needs the permanent tables to be there, but
only one of them is really derived from what was imported:

* ``param_info`` comes from the ``pi_*`` metadata in the schemas of the permanent tables
  -- so it does follow the import, but its content is the schemas'.
* ``table_names`` is built by
  :func:`~opus_import.steps.do_table_names.build_table_names_rows`, which **generates**
  the mission and instrument rows by looping the configuration maps and **enumerates
  every other table by hand**; which permanent tables exist filters the result. A table
  of a new kind with no row there gets no section, however much data it holds -- but a
  new mission or instrument table must *not* be added by hand, because it is generated
  already.
* ``partables`` comes from static configuration too: it enumerates every trigger OPUS
  knows, from the mission, instrument and host maps in :mod:`opus_import.config_data`. A
  mission that was never imported still gets a row.

:ref:`dev_guide_import_steps` states the order the steps run in and what forces it.

.. _dev_guide_architecture_obs:

The obs class hierarchy
-----------------------

The pipeline's largest structure is the family of classes that computes a column's value.
One instance is created per bundle, and
:func:`opus_import.steps.do_import_obs.import_run_field_function` calls its
``field_obs_<table>_<column>`` method once per column of each table the bundle fills.
Everything about the hierarchy exists to decide which class that call lands on.

It has five layers, root outward:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Layer
     - Answers
   * - :class:`~opus_import.obs.obs_base.ObsBase`
     - What every observation shares: the metadata, the index readers, the mult builder.
       It also *declares*, as methods that raise, the questions only a PDS version or an
       instrument can answer.
   * - The PDS-version bases
     - Where a file specification comes from, and what the time columns are called.
   * - One module per OPUS table
     - That table's field methods. Two assembly classes combine all nine so a mission
       class names one base instead of nine.
   * - One module per mission
     - What an instrument's archives share: a spacecraft clock format, an
       observation-name grammar, a mission phase.
   * - One module per bundle or volume set
     - The leaf, which knows how one particular archive spells things.

:ref:`dev_guide_import_obs` has the class diagram, the contracts and the method
resolution order -- which is not obvious, and is the usual way a newly added class
misbehaves. :ref:`dev_guide_import_obs_classes` catalogs every mission and leaf class.

.. _dev_guide_architecture_webapp:

The web application
-------------------

A request arrives at one of the routes :mod:`opus_app.urls` assembles, is answered by a
view, and -- for anything that searches -- reaches the database through a cache table
built once per distinct search.

.. mermaid::

    flowchart TD
        R([HTTP request]) --> U[opus_app.urls:<br/>each app contributes its routes]
        U --> V[The view, wrapped in api_view]
        V --> P[url_to_search_params:<br/>the query string becomes<br/>selections and extras]
        P --> Q[get_user_query_table:<br/>find or build cache_NNN<br/>for this search]
        Q --> S[sql_builder.Select:<br/>join the obs_ and mult_ tables]
        S --> D[(MySQL)]
        D --> F[Format as JSON, CSV or HTML]
        F --> RESP([HTTP response])
        V -.->|no search| F

Three parts of that flow are worth knowing before changing any of it, and each has a
chapter of its own.

**Every routed handler is wrapped in**
:func:`~opus_app.apps.tools.app_utils.api_view`. It records the call, turns an
:exc:`~opus_app.apps.tools.app_utils.Http400Error` raised anywhere inside the handler
into an HTTP 400, turns any other unhandled exception into an HTTP 500 logged with its
traceback, and applies the fault-injection knobs the configuration file carries. The
exceptions Django answers specifically are re-raised rather than absorbed, so each keeps
the response and the logging Django gives it. :ref:`dev_guide_webapp_errors` is the
detail.

**A search becomes a cache table.**
:func:`~opus_app.apps.search.views.url_to_search_params` turns the query string into the
two dictionaries the rest of the search code works with, and
:func:`~opus_app.apps.search.views.get_user_query_table` then finds or builds a
``cache_NNN`` table holding the ids of the matching observations in sort order. Every
later query -- a page of results, a count, a set of file URLs -- joins against that table
rather than re-running the search. :ref:`dev_guide_webapp_search_flow` walks all four
steps.

**The wide joins are assembled, not written.**
:mod:`opus_app.apps.tools.sql_builder` builds the statements that join the ``obs_``
tables to each other and to the ``mult_`` tables holding their enumerated values. Values
are always passed as parameters, and identifiers are validated before they are quoted.
:ref:`dev_guide_webapp_tools_sql_builder` says what that buys and where the two
exceptions are.

The eight Django apps are :ref:`dev_guide_webapp_tools`,
:ref:`dev_guide_webapp_search`, :ref:`dev_guide_webapp_results` and
:ref:`dev_guide_webapp_ui`.

The database
------------

:ref:`dev_guide_database` describes every table OPUS uses and what each column means. The
two ideas to carry into any other chapter:

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
   * - ``user_searches`` and ``cache_*``
     - the web application (reset by the import)
     - the web application
   * - Django's contrib tables
     - ``django-admin migrate``
     - Django
   * - ``search/models.py``
     - a script, from a populated database
     - the web application

Nothing in the pipeline imports :mod:`opus_app`, and nothing in the application imports
:mod:`opus_import`. The two shared packages are what they agree through:
:mod:`opus_config` for the installation's settings, and :mod:`opus_support` for the unit,
time and angle conversions both have to perform identically. :ref:`dev_guide_support`
describes both.
