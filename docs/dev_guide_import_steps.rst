.. _dev_guide_import_steps:

The Import Steps
================

:mod:`opus_import.steps` holds thirteen modules. Nine of them are steps -- each driven
by its own command-line option -- and four are the internals of the largest step,
:mod:`~opus_import.steps.do_import`, which is big enough to live in five files. This
chapter walks all thirteen.

:ref:`dev_guide_import` gives the shape of a run; :ref:`dev_guide_import_running` gives
the options. Nothing here is optional reading if you are changing the pipeline: the
order the steps run in is forced by foreign keys and by what each one needs to already
exist, and getting it wrong produces a database that looks fine and is not.

The order, and what forces it
-----------------------------

.. mermaid::

    flowchart TD
        C1[do_cart:<br/>create the empty cart table]
        C2[do_django:<br/>drop cache_*, reset user_searches]
        I[do_import:<br/>the observation import,<br/>and the copy to permanent]
        P[do_param_info]
        PT[do_partables]
        TN[do_table_names]
        UM[do_update_mult_info]
        V[do_validate]
        C3[do_cart, second attempt<br/>if the first was deferred]
        D[do_dictionary]

        C1 --> C2 --> I
        I --> P --> PT --> TN --> UM --> V --> C3 --> D

* **The cart and cache cleanup comes first** because a ``cart`` row carries a foreign
  key onto ``obs_general``, so the cart has to be emptied before the permanent tables
  are rebuilt underneath it.
* **The auxiliary tables come after the import** because each is derived from which
  permanent tables exist and from their schemas.
* **The dictionary comes last** because nothing else depends on it.
* ``--drop-permanent-tables`` moves the first part: :mod:`opus_import.cli` skips the
  leading cleanup, because dropping the permanent tables would drop the cart again, and
  :func:`~opus_import.steps.do_import.do_import_steps` performs it after the drop
  instead.

The steps
---------

.. _dev_guide_import_steps_do_cart:

:mod:`opus_import.steps.do_cart`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Creates the empty ``cart`` table the web application fills as users select products.
Option: ``--create-cart``.

:func:`~opus_import.steps.do_cart.create_cart` drops the permanent ``cart`` and creates
it again from ``cart.json``. **It is created directly in the permanent namespace**:
there is nothing to import into it, and it starts empty on every run.

The chicken and egg is worth knowing. ``cart`` has a foreign key onto ``obs_general``,
so it cannot be created before ``obs_general`` exists -- and it has to be emptied
before ``obs_general`` is rebuilt, or the rebuild trips the constraint. When
``obs_general`` is not there yet, this step sets
:attr:`~opus_import.context.ImportContext.try_cart_later` and logs a warning;
:func:`opus_import.cli.main` then makes one more attempt after the import. A second
failure is an error.

.. _dev_guide_import_steps_do_django:

:mod:`opus_import.steps.do_django`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Discards the tables the web application caches search results in. Option:
``--drop-cache-tables``.

:func:`~opus_import.steps.do_django.drop_cache_tables` drops every table whose name
starts with ``cache_`` -- found **by prefix**, across both namespaces, because a cache
table is named after a row of ``user_searches`` rather than defined by a schema -- and
then drops and recreates ``user_searches`` empty in the permanent namespace.

An import changes what a search returns, so every cached result is stale the moment it
finishes.

.. _dev_guide_import_steps_do_import:

:mod:`opus_import.steps.do_import`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The observation import. Option: ``--import``, plus everything that implies it. It also
owns the work for three options that are **not** steps of their own --
``--drop-permanent-tables``, ``--delete-import-bundles`` and
``--analyze-permanent-tables`` -- because each has to happen at a particular point in
this sequence.

:func:`~opus_import.steps.do_import.do_import_steps` is the whole sequence, and it runs
whether or not ``--import`` was given, because it is where the copy and the drops live.
In order:

1. Reset the per-run caches:
   :attr:`~opus_import.context.ImportContext.import_has_bad_data`,
   :attr:`~opus_import.context.ImportContext.max_table_id_cache` and
   :attr:`~opus_import.context.ImportContext.created_import_mult_tables`.
2. Expand the bundle descriptors into a list of bundle ids.
3. **Drop the old import tables**, under ``--drop-old-import-tables`` unless
   ``--leave-old-import-tables`` overrides it.
4. **Drop the permanent tables**, under ``--drop-permanent-tables`` **and**
   ``--scorched-earth`` together. This has to happen before the import so that there
   are no vestigial ``mult_`` tables and the row ids restart from zero. The cart and
   cache cleanup that :mod:`opus_import.cli` skipped is performed here, after the drop.
5. **Delete the named bundles from the import tables**, when ``--import`` or
   ``--delete-import-bundles`` was given and the import tables were not just dropped.
6. **Import each bundle** through
   :func:`~opus_import.steps.do_import.import_one_bundle`. A failure aborts the loop
   unless ``--import-ignore-errors``, and any error at all makes the function return
   False -- so the copy below never happens.
7. **Delete from the permanent tables** every bundle the import tables hold, read as
   ``SELECT DISTINCT bundle_id`` off the import ``obs_general``. ``--delete-permanent-bundles``
   separately deletes the bundles named on the command line.
8. **Copy the import tables over the permanent ones**, under
   ``--copy-import-to-permanent-tables``, in this order: create the permanent tables
   each bundle needs, delete duplicate OPUS IDs from the permanent tables, copy the
   ``mult_`` tables, then copy each bundle's ``obs_`` rows.
9. **Drop the new import tables** under ``--drop-new-import-tables``, and **analyze the
   permanent tables** under ``--analyze-permanent-tables``.

:func:`~opus_import.steps.do_import.import_one_bundle` is the per-bundle driver
described in :ref:`dev_guide_import_per_bundle`. It resets the per-bundle caches, looks
the bundle up in ``BUNDLE_INFO``, finds the primary index files and imports each one.

.. _dev_guide_import_steps_do_param_info:

:mod:`opus_import.steps.do_param_info`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Builds ``param_info``, the table that tells the web application what the search form
contains. Option: ``--create-param-info``.

One row per column that carries a ``pi_category_name``, read out of the **packaged
schema** of every permanent ``obs_`` table. A column with no ``param_info`` row is
invisible to users no matter what the import wrote into it. The row copies the ``pi_*``
keys across, and three of them are read without a default --
``pi_disp_order``, ``pi_display`` and ``pi_display_results`` -- so a column that carries
``pi_category_name`` and omits one of those fails the build rather than defaulting.

Two validations happen here rather than at the schema:

* a ``pi_form_type`` naming a unit id :func:`opus_support.units.is_valid_unit_id` does
  not recognize fails the build;
* a ``pi_ranges`` naming an entry that is not in ``param_info_ranges.json`` fails it
  too.

Every fault is collected before anything is written, so a failed build leaves the
import table empty rather than half filled, and one run reports all of them.
:func:`~opus_import.steps.do_param_info.do_param_info` copies to the permanent table
only if the build succeeded, and drops the import table either way.

This step must follow the import, because which permanent ``obs_`` tables exist is what
decides which schemas it reads.

.. _dev_guide_import_steps_do_partables:

:mod:`opus_import.steps.do_partables`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Builds ``partables``, which maps a value a user can search for onto the table of further
search parameters that value makes relevant -- choosing the Cassini mission reveals the
Cassini mission table. Option: ``--create-partables``.

A row is ``(trigger_tab, trigger_col, trigger_val, partable)``. The rows are
**generated** from the configuration maps, in four groups:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Group
     - Rows
   * - Missions
     - One per entry of ``MISSION_ID_TO_MISSION_TABLE_SFX``, triggering on
       ``obs_general.mission_id``.
   * - Instruments
     - One per entry of ``INSTRUMENT_ID_TO_MISSION_ID``, triggering on
       ``obs_general.instrument_id``. An instrument id beginning ``HST`` points at
       ``obs_mission_hubble`` instead of an instrument table, because Hubble has no
       per-instrument tables -- everything is in the mission table.
   * - Spacecraft
     - One per entry of ``INST_HOST_ID_TO_MISSION_ID``, triggering on
       ``obs_general.inst_host_id``.
   * - Surface geometry targets
     - One per ``obs_surface_geometry__*`` table that exists, triggering on
       ``obs_surface_geometry_name.target_name``.

The first three groups store a ``mult_`` row id as the trigger value, because that is
what the corresponding ``obs_general`` column holds; the surface geometry group stores
the **target name itself**, because the web side compares the user's search text to it
directly rather than running a database lookup. That asymmetry is the one thing to know
before adding a trigger of a new kind.

Because the first three groups are generated, a mission or instrument that was never
imported still gets a row.

.. _dev_guide_import_steps_do_table_names:

:mod:`opus_import.steps.do_table_names`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Builds ``table_names``, which names and orders the "Constraints" categories the search
form and the Details tab are divided into. Option: ``--create-table-names``.

:func:`~opus_import.steps.do_table_names.build_table_names_rows` is the authority on
what a category is called and what order the categories come in. It is a pure function
-- it takes a "does this table exist?" callable and the list of surface geometry tables
-- so that the documentation build and the tests can ask the same question without a
database.

**The set of tables is written out by hand there, not derived from the schemas**, with
two generated groups. The order it emits is:

1. ``obs_general`` -- "General Constraints", written unconditionally.
2. ``obs_pds``, ``obs_type_image``, ``obs_wavelength``, ``obs_profile``,
   ``obs_surface_geometry_name``, ``obs_surface_geometry``, each if it exists.
3. One per ``obs_surface_geometry__<TARGET>`` table, labelled from the decoded target
   name.
4. ``obs_ring_geometry``.
5. One per mission table that exists, **generated** by looping
   ``MISSION_ID_TO_MISSION_TABLE_SFX``.
6. One per instrument table that exists, **generated** by looping
   ``INSTRUMENT_ID_TO_MISSION_ID``. A Hubble instrument's row is written with
   ``display`` set to ``N``, for the same reason as in ``partables``.

``obs_files`` is deliberately absent: it holds one row per file rather than per
observation, and users never search it.

The consequence for :ref:`dev_guide_import_extending`: **a new mission or instrument
needs no change here**, because groups 5 and 6 generate its row already, and adding one
by hand would give the table a second row and a second display position. A table of a
*new kind* -- neither a mission nor an instrument table, as ``obs_wavelength`` is --
does need a row, or it has no section and its fields are invisible.

.. _dev_guide_import_steps_do_update_mult_info:

:mod:`opus_import.steps.do_update_mult_info`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Writes the display details a schema pins for a ``mult_`` table -- the label, the sort
order, the display flag, the grouping -- back over the permanent table the import
discovered, so that editing a schema changes a label without a re-import. Option:
``--update-mult-info``. **No aggregate option implies it.**

It writes ``label``, ``disp_order``, ``display``, ``grouping`` and
``group_disp_order``, and deliberately **not** ``id`` or ``value``: the id is what the
``obs_`` rows already reference, and the value is what a row means rather than how it is
shown.

The hard part is splitting a mult table's name back into its observation table and its
column, because both halves contain underscores. There is no rule that works: both
``obs_surface_geometry`` and ``obs_surface_geometry_name`` are real tables, so
``mult_obs_surface_geometry_name_target_name`` matches a schema at the shorter split and
only the longer one leaves a column that exists. The step therefore tries every split
and takes the one where the schema *and* the column both resolve.

A ``mult_options`` entry that does not carry exactly the seven values
:class:`~opus_import.import_util.MultOption` names raises :exc:`TypeError`. That is a
fault in the packaged schema, and stopping is better than writing a row built from
values that landed in the wrong columns.

.. _dev_guide_import_steps_do_validate:

:mod:`opus_import.steps.do_validate`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Checks the invariants no database constraint can express. Option: ``--validate-perm``,
which runs it against the permanent namespace. **Nothing here changes the database**,
and a failure is worth attention rather than being fatal -- the tables are already
written, and an import that produced them is not undone by a validation error.

**It reports through the logger and still exits zero**, which is why an automated import
gates on ``ERRORS.log`` rather than on the exit status.

Four checks, in this order:

:func:`~opus_import.steps.do_validate.validate_param_info`
    Every user-visible column of every ``obs_`` table has a ``param_info`` row. A list
    of exemptions covers the columns that legitimately have none: ``id``, ``timestamp``,
    ``obs_general_id``, anything beginning ``d_``, any column that has a ``d_``
    companion, ``opus_id`` outside ``obs_general``, anything beginning ``mult_``,
    ``bundle_id`` outside ``obs_pds``, ``instrument_id`` outside ``obs_general``, and
    the whole of ``obs_files``. It then looks for a duplicated
    ``(category_name, disp_order)`` among displayed parameters and for a duplicated
    ``slug``. Both duplicate scans use a subquery that skips its first match, so they
    report a value shared by three or more rows and stay silent about one shared by
    exactly two.

:func:`~opus_import.steps.do_validate.validate_nulls`
    Reports a column declared to allow NULLs in which no NULL was found, at **info**
    level rather than as an error: it is an observation about the schema rather than a
    fault in the data. The ``obs_surface_geometry__*`` tables are skipped, because they
    all come from one template.

:func:`~opus_import.steps.do_validate.validate_min_max_order`
    For every ``X1``/``X2`` pair, reports rows where ``X2 < X1``, listing the first
    hundred OPUS IDs. A ``LONG`` field is skipped, because a longitude range wraps and
    its low end legitimately exceeds its high end. A missing ``X2``, an absent
    ``param_info`` row, or more than one, is an error.

:func:`~opus_import.steps.do_validate.validate_filter_wavelength_consistency`
    For every table with a ``filter_name`` or ``combined_filter`` column, checks that
    all observations sharing a filter agree about that filter's nine wavelength
    columns. ``obs_instrument_coiss`` is grouped by camera as well as by filter,
    because its two cameras carry filters of the same name. Reported as a warning.

.. _dev_guide_import_steps_do_dictionary:

:mod:`opus_import.steps.do_dictionary`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Fills ``contexts`` and ``definitions``, which is where every tooltip in the user
interface comes from. Option: ``--import-dictionary``. It is the last thing a run does.
:ref:`dev_guide_dictionary` describes the two tables and where their content comes from.

The step builds both import tables, copies them over the permanent ones only if both
builds succeeded, and drops the import tables **both before and after**, so a failed
build leaves nothing behind and the permanent tables keep what the previous run wrote.
Contexts are built and copied before definitions in both directions, because
``definitions`` has a foreign key onto ``contexts``.

Both builders collect every fault before writing anything, so a broken schema produces a
complete report and an untouched database. A failed dictionary import reports through
the log and does **not** change the run's exit status.

The four internal modules
-------------------------

These are the internals of :mod:`~opus_import.steps.do_import`. **They are not steps**:
no command-line option runs one on its own, and nothing outside ``do_import`` calls
them as a unit.

.. _dev_guide_import_steps_do_import_tables:

:mod:`opus_import.steps.do_import_tables`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Creating, deleting and copying the ``obs_`` tables.

The teardown and build orders are forced by foreign keys, and both are stated here once
so no caller has to work them out:

* **Teardown** -- every ``obs_`` table except ``obs_general``, then ``cart``, then
  ``obs_general``, then the ``mult_`` tables.
* **Build** -- the other way round.

The ``mult_`` tables come last on teardown and first on build by the pipeline's own
convention (an ``obs_`` row holds a ``mult_`` row id), not because a constraint forces
it.

Its functions:

:func:`~opus_import.steps.do_import_tables.lookup_vol_info`
    The first ``BUNDLE_INFO`` entry whose regular expression matches the whole bundle
    id, or None.

:func:`~opus_import.steps.do_import_tables.create_tables_for_import`
    Creates, in one namespace, every table a bundle needs and every ``mult_`` table its
    GROUP-typed columns need. It returns the schemas it read and the table names in
    order, which is what the index importer walks. **The
    ``obs_surface_geometry__<TARGET>`` tables are deliberately not created here**: the
    target names are not known until the observations have been read. The template
    schema is still returned, because the import needs the column names.

:func:`~opus_import.steps.do_import_tables.delete_all_obs_mult_tables`
    Drops everything in a namespace, in the four phases above.

:func:`~opus_import.steps.do_import_tables.delete_bundle_from_obs_tables`
    ``DELETE ... WHERE bundle_id = ...`` across a namespace, other tables before
    ``obs_general``.

:func:`~opus_import.steps.do_import_tables.delete_opus_id_from_obs_tables`
    The same for one OPUS ID.

:func:`~opus_import.steps.do_import_tables.find_duplicate_opus_ids` and :func:`~opus_import.steps.do_import_tables.delete_duplicate_opus_id_from_perm_tables`
    An OPUS ID present in both namespaces can only have come from two different bundles
    -- Galileo SSI is the known case. The import's copy is the one being kept, so the
    permanent one is deleted before the copy writes over it.

:func:`~opus_import.steps.do_import_tables.copy_bundle_from_import_to_permanent`
    Creates the permanent tables the bundle needs, copies each one's rows, and then
    handles the surface geometry tables specially: **their names are discovered by
    listing the import namespace**, because nothing else knows which targets the
    observations mentioned. Any permanent counterpart that does not exist is created
    from the template with the two substitutions applied.

:func:`~opus_import.steps.do_import_tables.read_existing_import_opus_id`
    The OPUS IDs already in the import ``obs_general``, for
    ``--import-check-duplicate-id``.

:func:`~opus_import.steps.do_import_tables.analyze_all_tables`
    Runs the backend's analyze over every ``obs_`` and ``mult_`` table in a namespace.
    ``cart`` and the auxiliary tables are not analyzed.

.. _dev_guide_import_steps_do_import_index:

:mod:`opus_import.steps.do_import_index`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Importing every observation one primary index file describes.
:ref:`dev_guide_import_one_index` walks it; this section names its three functions.

:func:`~opus_import.steps.do_import_index.import_one_index`
    The whole of it: read the primary index, resolve ambiguous rows, discover and
    cross-reference the associated metadata files, run the master loop, then write the
    ``mult_`` tables and the ``obs_`` tables out.

:func:`~opus_import.steps.do_import_index.get_opus_products_rows_for_filespec`
    The ``obs_files`` rows for one observation: one row per file of one product type at
    one version, carrying where it lives, how big it is, its checksum, and the ordering
    the results page shows the product types in. It leaves out two kinds of file -- a
    shared index or summary file that does not list this observation, and a PDS3 file
    whose shelf metadata is missing (with a warning, because its size and checksum are
    unknown). A file that is not the current version is never checked by default.

:func:`~opus_import.steps.do_import_index.remove_opus_id_from_tables`
    Drops every row an observation contributed from the in-memory table lists, before
    any of them is written. An observation can have more than one row in a table -- one
    per target in the surface geometry tables -- so every match is removed rather than
    the first.

.. _dev_guide_import_steps_do_import_obs:

:mod:`opus_import.steps.do_import_obs`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Computing one row of one observation table. :ref:`dev_guide_import_one_row` walks the
dispatch and the validation; the three functions are:

:func:`~opus_import.steps.do_import_obs.import_observation_table`
    Walks a table's schema, obtains each column's value, checks it, replaces an
    enumerated value with its ``mult_`` row id, and assembles the row. It returns None
    only when a group column's field method returned something that is not a mult
    specification, which is not recoverable -- the whole observation is discarded.

:func:`~opus_import.steps.do_import_obs.field_function_name`
    The pipeline's only rule for finding a field method. The tests resolve the hierarchy
    against the schemas *through this function* rather than restating the rule, so
    changing it here changes what they check.

:func:`~opus_import.steps.do_import_obs.import_run_field_function`
    Calls the method and turns a missing method or an exception into a logged error and
    a None value.

.. _dev_guide_import_steps_do_import_mult:

:mod:`opus_import.steps.do_import_mult`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Reading, caching and writing the ``mult_`` tables that hold the enumerated values of
the ``obs_`` columns.

**Naming.** :func:`~opus_import.import_util.table_name_mult` builds
``mult_<table>_<column>``, both lowercased --
``mult_obs_general_planet_id``. In the import namespace it gains the prefix:
``imp_mult_obs_general_planet_id``.

**Caching, and its three lifetimes.** Every table is read once per bundle into the
context's cache and written back at the end of the bundle, so importing an index of a
hundred thousand rows does not query for the same enumeration a hundred thousand times.
Three collections track it:

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Context field
     - Lifetime and meaning
   * - :attr:`~opus_import.context.ImportContext.mult_table_cache`
     - Each table read or created during this bundle, keyed by the **raw** name. The
       returned list *is* the cache: appending to it is how a value is added. Cleared
       per bundle.
   * - :attr:`~opus_import.context.ImportContext.modified_mult_tables`
     - The tables this bundle added values to, and which therefore have to be written
       back. Cleared per bundle.
   * - :attr:`~opus_import.context.ImportContext.created_import_mult_tables`
     - The import mult tables created empty and not yet written. Cleared once per
       **run**, not per bundle.

**Which namespace a table is read from** is the part that is easy to get wrong. If an
import table already exists *and is not in* ``created_import_mult_tables``, it is read:
that means a second import run without a copy in between, so its contents are the
current ones. Otherwise the permanent table is read if it exists -- and if the import
table was created empty in this run, it is marked modified at the same time, so that
the import version gets written out. If neither exists, the cache starts empty. A column
that pins its values with ``mult_options`` short-circuits all of this and is marked
modified immediately.

**Keying and id assignment.** Lookup is a linear scan comparing the stringified value.
A new value is given ``max(existing ids) + 1``, or 0 in an empty table. A value absent
from a table whose values are pinned by ``mult_options`` is an error, and returns 0.

**The derived sort order** is where a value's position in the search form comes from
when the schema pins none. The rules, in order: a null-ish label sorts to the end
(``NULL``, then ``N/A``, then ``NONE``, via ``zzz``/``zzy``/``zzx`` prefixes) unless the
column has a unit, in which case the unit's own parser decides; a column with a unit
sorts by the parsed number, zero-padded; a table whose labels are all numeric sorts
numerically; ``Yes`` sorts before ``No`` and ``On`` before ``Off``; anything else sorts
by its label.

**Writing back.** :func:`~opus_import.steps.do_import_mult.dump_import_mult_tables`
upserts every modified table at the end of each index file.
:func:`~opus_import.steps.do_import_mult.copy_mult_from_import_to_permanent` copies
**all** of them rather than just the ones this run changed, because an earlier run or an
earlier bundle may have changed a table and nothing records that.

API reference
-------------

:doc:`api_opus_import`
