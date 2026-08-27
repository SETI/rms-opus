.. _dev_guide_architecture:

Architecture
============

OPUS is two programs joined by one database. The import pipeline writes the database
from the PDS holdings; the Django application reads it and answers requests. Nothing
flows the other way -- the web application never writes an ``obs_`` table -- and the
two share only :mod:`opus_config`, :mod:`opus_support`, and their understanding of
what the tables mean.

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

The import pipeline
-------------------

An import run turns one PDS index file into one row per observation in each of the
tables that observation belongs to.

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

The protection covers the imported tables and no others. ``cart`` is created directly in
the permanent namespace, and the ``cache_*`` and ``user_searches`` tables are dropped
there outright; a failed run can leave those already reset. They hold no imported data --
see :mod:`opus_import.steps.do_cart` and :mod:`opus_import.steps.do_django` in
:doc:`dev_guide_import` -- which is why they are outside the copy.

The auxiliary tables come last because each needs the permanent tables to be there,
but only one of them is really derived from what was imported:

* ``param_info`` comes from the ``pi_*`` metadata in the schemas of the permanent
  tables -- so it does follow the import, but its content is the schemas'.
* ``table_names`` is built by ``build_table_names_rows`` in
  :mod:`opus_import.steps.do_table_names`, which **generates** the mission and instrument
  rows by looping the configuration maps and **enumerates every other table by hand**;
  which permanent tables exist filters the result. A table of a new kind with no row
  there gets no section, however much data it holds -- but a new mission or instrument
  table must *not* be added by hand, because it is generated already.
* ``partables`` comes from static configuration too: it enumerates every trigger OPUS
  knows, from the mission, instrument and host maps in
  :mod:`opus_import.config_data`. A mission that was never imported still gets a row.

:mod:`opus_import.steps` documents the order the steps run in and what forces it;
:ref:`dev_guide_import` walks the pieces.

The obs class hierarchy
-----------------------

The pipeline's largest structure is the family of classes that compute a column's
value. One instance is created per bundle, and
:func:`opus_import.steps.do_import_obs.import_run_field_function` calls its
``field_obs_<table>_<column>`` method once per column of each table the bundle fills.
Everything about the hierarchy exists to decide which class that call lands on.

.. mermaid::

    classDiagram
        class ObsBase {
            <<abstract>>
            #_metadata
            +opus_id
            +instrument_id()*
            +inst_host_id()*
            +mission_id()*
            +primary_filespec()*
            #_index_col(column)
            #_create_mult(col_val, ...)
        }
        class ObsBasePDS3 {
            <<abstract>>
            answers the PDS3 questions
        }
        class ObsBasePDS4 {
            <<abstract>>
            answers the PDS4 questions
        }
        class ObsGeneral {
            field_obs_general_*()
        }
        class ObsRingGeometry {
            field_obs_ring_geometry_*()
        }
        class ObsGeneralPDS3 {
            the PDS3 half of obs_general
        }
        class ObsCommonPDS3 {
            <<abstract>>
            combines every table module
        }
        class ObsCassiniCommon {
            what all Cassini shares
        }
        class ObsCassiniCommonPDS3 {
            what PDS3 Cassini shares
        }
        class ObsVolumeCOISS12xxx {
            what only COISS_1xxx/2xxx knows
        }

        ObsBase <|-- ObsBasePDS3
        ObsBase <|-- ObsBasePDS4
        ObsBase <|-- ObsGeneral
        ObsBase <|-- ObsRingGeometry
        ObsGeneral <|-- ObsGeneralPDS3
        ObsBasePDS3 <|-- ObsGeneralPDS3
        ObsGeneralPDS3 <|-- ObsCommonPDS3
        ObsRingGeometry <|-- ObsCommonPDS3
        ObsBase <|-- ObsCassiniCommon
        ObsCommonPDS3 <|-- ObsCassiniCommonPDS3
        ObsCassiniCommon <|-- ObsCassiniCommonPDS3
        ObsCassiniCommonPDS3 <|-- ObsVolumeCOISS12xxx

Every edge above is a direct base, and the diagram shows **one path** through the
tree: the real ``ObsCommonPDS3`` combines nine table modules rather than the two drawn
here, and each mission and bundle has siblings the diagram leaves out. Read the base
list off the class statement -- ``obs_common_pds3.py`` -- rather than counting edges
here, because the order that list is written in is what decides the resolution order
described below.

The modules come in five kinds.

**The root.** :class:`~opus_import.obs.obs_base.ObsBase` owns the per-observation
metadata, the helpers that read a value out of a PDS index table, and
``_create_mult``, which builds the dictionary a group column's field method must
return. It also *declares* -- as methods that raise :exc:`NotImplementedError` -- the
handful of questions only a PDS version or a specific instrument can answer.

**The PDS-version split.** :mod:`opus_import.obs.obs_base_pds3` and
:mod:`opus_import.obs.obs_base_pds4` answer the questions a PDS version decides: where
a file specification comes from, and what the time columns are called.

**One module per OPUS table.** General, PDS, profile, wavelength, image type, ring
geometry and the three surface-geometry modules each hold that table's field methods.
Two assembly classes, :class:`~opus_import.obs.obs_common_pds3.ObsCommonPDS3` and
:class:`~opus_import.obs.obs_common_pds4.ObsCommonPDS4`, combine all of them so that a
mission class can name one base instead of nine.

**One module per mission.** Cassini, Galileo, Hubble, New Horizons and Voyager, for
what an instrument's volumes share: a spacecraft clock format, an observation-name
grammar, a mission phase.

**One module per bundle or volume set.** The leaf, which knows how one particular
archive spells things.

The method resolution order that falls out of this is not obvious, and getting it
wrong is the usual way a new class misbehaves. :mod:`opus_import.obs` is the
authoritative description: it reads the order off the tree, gives a worked example for
a Cassini ISS volume, and names the two orderings that surprise -- the PDS-version base
landing in the *middle* of the table modules rather than after them, and a mission's
PDS-version-independent half sitting *below* every table module. Read it before adding
a class, and read it rather than this summary if the two ever disagree.

The web application
-------------------

A request arrives at one of the routes :mod:`opus_app.urls` assembles, is answered by
a view, and -- for anything that searches -- reaches the database through a cache table
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

Three parts of that flow are worth knowing before changing any of it.

**Every routed handler is wrapped in**
:func:`~opus_app.apps.tools.app_utils.api_view`. It records the call, turns an
:class:`~opus_app.apps.tools.app_utils.Http400Error` raised anywhere inside the
handler into an HTTP 400, turns any other unhandled exception into an HTTP 500 logged
with its traceback, and applies the fault-injection knobs the configuration file
carries. Exceptions Django answers specifically -- :exc:`django.http.Http404`,
:exc:`~django.core.exceptions.BadRequest`,
:exc:`~django.core.exceptions.PermissionDenied` and
:exc:`~django.core.exceptions.SuspiciousOperation` -- are re-raised rather than
absorbed, so each keeps the response and the logging Django gives it. A view that needs the API call number declares an ``api_code`` parameter and
the wrapper supplies it.

**A search becomes a cache table.**
:func:`~opus_app.apps.search.views.url_to_search_params` turns the query string into
the two dictionaries the rest of the search code works with, and
:func:`~opus_app.apps.search.views.get_user_query_table` then finds or builds a
``cache_NNN`` table holding the ids of the matching observations in sort order. Every
later query -- a page of results, a count, a set of file URLs -- joins against that
table rather than re-running the search.

**The wide joins are assembled, not written.**
:mod:`opus_app.apps.tools.sql_builder` builds the statements that join the ``obs_``
tables to each other and to the ``mult_`` tables holding their enumerated values.
Values are always passed as parameters; the two places that render a value into the
statement text are ``LIMIT``/``OFFSET`` and the optimizer hint, both checked with
``isinstance(..., int)`` first, and the module's own docstring says why.

The database
------------

:ref:`dev_guide_database` describes every table OPUS uses and what each column means.
The two ideas to carry into any other chapter:

* An ``obs_*`` table corresponds one-for-one to a "Constraints" category in the user
  interface, and a row is one observation. ``obs_general`` is the master table: every
  observation has a row there, and every other table's rows hang off it.
* A field whose value comes from a fixed set stores an integer index into a
  ``mult_*`` table rather than the value itself, which is what makes the checkbox
  searches fast. :ref:`dev_guide_table_schemas` describes how a column declares that.
