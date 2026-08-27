.. _dev_guide_import:

The Import Pipeline
===================

:mod:`opus_import` reads PDS3 volumes and PDS4 bundles and writes every OPUS table.
It is a program rather than a library: nothing outside the distribution imports it,
and its only entry point is ``python -m opus_import``.

Overview
--------

A run is a sequence of steps. The command line asks for the ones it wants,
:mod:`opus_import.cli` runs the requested subset in a fixed order, and each step is a
``do_*`` module under :mod:`opus_import.steps`. The order is not a preference: the
cart and cache tables have to be cleaned before the permanent tables are rebuilt
because a cart row can reference them, and the auxiliary tables have to be built after
the permanent tables because they are derived from them. :mod:`opus_import.steps`
states the whole order and what forces each part of it.

The run's state lives in one object. :class:`opus_import.context.ImportContext` carries
the parsed arguments, the open database, the loggers, and the caches a run accumulates
-- the mult tables it has read, the maximum row id per table, the warnings it has
already reported. Every step takes it as its only parameter. Nothing in the pipeline
reaches for a module-level global.

Configuration data
------------------

Three modules answer "what exists", and adding a mission, an instrument or a bundle
means editing them:

:mod:`opus_import.config_data`
    Which missions, spacecraft and instruments there are, and which mission each
    belongs to. It also holds ``TABLES_TO_POPULATE``, the kinds of table an
    observation can fill, whose mission, instrument and surface-geometry entries carry
    placeholders substituted per bundle.

:mod:`opus_import.config_bundle_info`
    ``BUNDLE_INFO``: a list of (regular expression matching a bundle id, details)
    pairs, and the only thing that makes a bundle importable at all. The details are
    the obs class that computes its rows, the PDS version, the primary index file
    names -- ``primary_index`` is a tuple, and a bundle set may name several, as
    COCIRS_0402 onwards does with three -- and two flags. Nothing here maps a
    bundle-id *prefix* to an instrument: the regular expression selects the class
    directly.

:mod:`opus_import.config_targets`
    Target names, the class each target belongs to, and the alias mapping that folds
    a label's spelling onto the name OPUS uses.

The steps
---------

:mod:`opus_import.steps.do_import`
    The observation import itself, behind ``--import`` and everything that implies
    it. It is large enough to live in five modules: ``do_import.py`` holds the main
    loop and the per-bundle driver, and four modules that are **not** steps of their
    own hold its internals -- :mod:`~opus_import.steps.do_import_tables` (creating,
    deleting and copying the ``obs_`` tables),
    :mod:`~opus_import.steps.do_import_mult` (the ``mult_`` tables),
    :mod:`~opus_import.steps.do_import_index` (one primary index file) and
    :mod:`~opus_import.steps.do_import_obs` (one row of one table).

:mod:`opus_import.steps.do_param_info`
    Builds ``param_info``, the table that tells the web application what the search
    form contains. One row per column that carries a ``pi_category_name``. A column
    with no ``param_info`` row is invisible to users no matter what the import wrote
    into it.

:mod:`opus_import.steps.do_table_names`
    Builds ``table_names``, which names and orders the "Constraints" categories. The
    set of tables is written out by hand there rather than derived from the schemas,
    so a new table needs a row adding.

:mod:`opus_import.steps.do_partables`
    Builds ``partables``, which maps a value a user can search for onto the table of
    further search parameters that value makes relevant -- choosing the Cassini
    mission reveals the Cassini mission table. The web application reads it to decide
    which sections of the search form to offer, so a mission or instrument with no row
    here has no searchable columns of its own.

:mod:`opus_import.steps.do_update_mult_info`
    Writes the display details a schema pins for a ``mult_`` table -- the label, the
    sort order, the grouping -- back over the table the import discovered, so that
    editing a schema changes a label without a re-import. It runs only under
    ``--update-mult-info``; ``--do-it-all`` does not imply it.

:mod:`opus_import.steps.do_validate`
    Checks the invariants no database constraint can express: that every user-visible
    column is described in ``param_info``, that a paired minimum and maximum are
    really in that order, and that observations sharing a filter agree about that
    filter's wavelengths. It changes nothing and it is not fatal -- see *Errors and
    warnings* below for what that means for an automated run.

:mod:`opus_import.steps.do_dictionary`
    Fills the ``contexts`` and ``definitions`` tables, which is where every tooltip
    comes from. The terms come from two places: the PDS data dictionary that ships
    with the package, and the ``definition`` entries in the table schemas, which is
    where OPUS's own parameters and mult values are described. It runs only under
    ``--import-dictionary``, and it is the last thing a run does.

:mod:`opus_import.steps.do_cart`
    Creates the ``cart`` table empty, directly in the permanent namespace: there is
    nothing to import into it, and it starts empty on every run.

:mod:`opus_import.steps.do_django`
    Drops the ``cache_*`` tables the web application holds search results in, and the
    ``user_searches`` table they are keyed by, recreating the latter empty. An import
    changes what a search returns, so every cached result is stale once it finishes.

How one observation becomes a row
---------------------------------

:func:`opus_import.steps.do_import.import_one_bundle` looks through the bundle's
metadata and index directories for each of the primary index names ``BUNDLE_INFO``
gives it, and runs
:func:`opus_import.steps.do_import_index.import_one_index` once per index it finds.
That function reads the index with ``pdstable``, then **discovers** the supplemental
indexes rather than being told about them, by scanning the same directories for the
file-name endings it knows (``SUMMARY.LBL``, ``SUPPLEMENTAL_INDEX.LBL``,
``INVENTORY.LBL``). It joins each row to what it found and hands the assembled
``metadata`` dictionary to the bundle's obs class
instance -- **replacing it in place**, once per row. That is why no obs method may
cache anything derived from ``metadata``:
:attr:`~opus_import.obs.obs_base.ObsBase.opus_id` shows the pattern that is allowed,
re-deriving whenever the file specification it was computed from changes.

For each table the observation belongs to,
:func:`~opus_import.steps.do_import_obs.import_observation_table` walks that table's
schema and computes one value per column, dispatching on the column's ``data_source``
(see :ref:`dev_guide_table_schemas`). The common case is ``COMPUTE``, which calls the
``field_obs_<table>_<column>`` method of the obs class instance.

A field method's exception is treated as a bad field rather than as an aborted import:
an obs class is handed the context only so that it can log, never so that it can reach
the database. That is what lets one malformed label cost one observation rather than
the run.

Important invariants
--------------------

* **Nothing is visible until the run succeeds.** Every table is written under the
  import prefix and copied over the permanent tables at the end. Deleting the import
  tables before the copy, or copying before every bundle has been read, breaks the
  guarantee the whole design rests on.
* **The** ``mult_`` **tables go out before the** ``obs_`` **tables.** An ``obs_`` row
  stores the row id its value was given in the corresponding ``mult_`` table, so that
  row has to exist first. No database constraint enforces it.
* **An import run is single-threaded and one obs instance serves a whole bundle.**
  The instance holds the current row's metadata, so it is not safe to share.
* **Longitudes carry two derived columns.** A ``LONG`` field stores, besides its
  minimum and maximum, the midpoint and the span of the range, because a longitude
  search has to handle the wrap at 360 degrees. ``LONGITUDE_FIELD`` and
  ``D_LONGITUDE_FIELD`` are the ``data_source`` values that fill them.
* **Units are the schema's business, not the field method's.** A field method returns
  a value in the column's default unit; :mod:`opus_support` is what converts to and
  from everything else, driven by the ``pi_form_type`` the schema declares.

Errors and warnings
-------------------

A run reports through :class:`opus_import.context.ImportLog`, and what ends up in the
error log is what gates an automated import: ``--validate-perm`` does not fail a run
through its exit status, and the check that matters is whether the error log came out
empty. The ``log_nonrepeating_*`` helpers in :mod:`opus_import.import_util` exist
because a single systematic fault would otherwise be reported once per observation.

Authoring tools
---------------

:mod:`opus_import.util` holds tools that are run by hand while authoring a schema, not
during an import: ``dump_pds_definitions`` takes the path of a **PDS index label** and
prints that label's field definitions in the form a table schema's ``definition``
entries want, and ``retrieve_ra_dec`` queries SIMBAD for a star's coordinates. Both do
their work inside a ``main()`` behind an ``if __name__ == '__main__':`` guard, so
importing either one -- which the documentation build does -- runs nothing and reaches
no network.

API reference
-------------

:doc:`api_opus_import`
