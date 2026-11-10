.. _dev_guide_import_steps:

The Import Steps
================

:mod:`opus_import.steps` holds the step modules. Most are steps -- each driven by its own
command-line option -- and the rest are the internals of the largest step,
:mod:`~opus_import.steps.do_import`, which is big enough to live in several files. This
chapter walks them all.

:ref:`dev_guide_import_overview` gives the shape of a run; :ref:`dev_guide_import_running` gives
the options. Nothing here is optional reading if you are changing the pipeline: the
order the steps run in is forced by foreign keys and by what each one needs to already
exist, and getting it wrong produces a database that looks fine and is not.

The order, and what forces it
-----------------------------

.. mermaid::
    :zoom:

    flowchart TD
        SE["do_import:<br/>--scorched-earth, --delete-bundles"]
        I[do_import:<br/>the observation import]
        R{every bundle in the<br/>registry done?}
        K[do_indexes:<br/>the secondary keys]
        DU[do_duplicate_ids:<br/>one copy of each OPUS ID]
        P[do_param_info]
        PT[do_partables]
        TN[do_table_names]
        C[do_cart:<br/>recreate the empty cart table]
        DJ[do_django:<br/>reset user_searches and search_results,<br/>flush the web cache]
        A[analyze the tables]
        UM[do_update_mult_info]
        V[do_validate]
        D[do_dictionary]
        SV[do_schema_version]

        SE --> I --> R
        R -->|yes| K --> DU --> P --> PT --> TN --> C --> DJ --> A --> UM --> V --> D --> SV
        R -->|"no: --finalize refuses"| X[exit with failure]

* **The erase and the deletes come first**, inside
  :func:`~opus_import.steps.do_import.do_import_steps`: ``--scorched-earth`` so that no
  ``mult_`` table survives and the row ids start again, and ``--delete-bundles`` so that
  an import in the same invocation does not resume a bundle being removed.
* **Finalization refuses after the import and before its first step**: ``--finalize``
  exits with failure while any bundle in the bundle registry is not ``done``
  (:ref:`dev_guide_import_steps_registry`), so a refused finalization changes nothing
  and an import in the same invocation can still finish the registry first.
* **The keys come right after the import**, and the foreign keys after every other key,
  because a fresh import loads its tables without them; the duplicate step follows,
  because it finds the copies through the key on ``opus_id`` and deletes them through
  the keys on ``obs_general_id``.
* **The auxiliary tables come after the import** because each is derived from which
  observation tables exist and from their schemas.
* **The cart and search tables come after the import** because ``cart`` carries a
  foreign key onto ``obs_general``, which must exist first; a schema without it logs an
  error and gets no cart.
* **The tables are analyzed after them**, so that the statistics count every table's
  rows.
* **The dictionary comes after them** because nothing else depends on it.
* **The schema version comes last** because its row is what makes the schema
  servable, so it is written only once everything else, validation included, has run.

The steps
---------

.. _dev_guide_import_steps_do_cart:

opus_import.steps.do_cart
~~~~~~~~~~~~~~~~~~~~~~~~~

Creates the empty ``cart`` table the web application fills as users select products.
Option: ``--create-cart``, part of ``--finalize``.

:func:`~opus_import.steps.do_cart.create_cart` drops ``cart`` and creates it again from
``cart.json``. There is nothing to import into it, and it starts empty on every run.
``cart`` has a foreign key onto ``obs_general``, so it cannot be created before
``obs_general`` exists, which is why it runs after the import, in the finalization
sequence; on a schema without ``obs_general`` it logs an error and creates nothing. The
foreign key cascades on delete (:ref:`dev_guide_table_schemas`), so deleting a bundle,
on either write path or under ``--delete-bundles``, deletes the cart rows that name its
observations rather than being refused.

.. _dev_guide_import_steps_do_django:

opus_import.steps.do_django
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Resets the tables the web application keeps its searches in, and flushes its cache.

:func:`~opus_import.steps.do_django.reset_search_tables` drops ``user_searches`` and
``search_results`` (:data:`~opus_import.steps.do_django.SEARCH_TABLES`) and creates each
again empty from its schema file. The re-created ``user_searches`` hands out ids above
the highest the old one held
(:meth:`~opus_import.importdb.super.ImportDBSuper.set_next_id`), so an id a request in
flight cached across the reset names no row rather than another search's. Option:
``--reset-search-tables``, part of
``--finalize``, which runs it after ``--create-cart``. The deploy of a new database runs
it too, alongside ``--import-dictionary``, so that searches made while the staged
installation was being tried out are not served.

An import changes what a search returns, so every built search is stale the moment it
finishes.

**Every reset of the search tables flushes the web application's cache.** The cache
maps a search's hash to its ``user_searches`` id, and keys other answers by that id, so
every entry made before the reset names a search that is gone. The
flush runs :data:`~opus_import.steps.do_django.CACHE_FLUSH_COMMAND`, this interpreter on
``python -m opus_app.clear_django_cache``, in a subprocess of its own, because the
cache's configuration is the web application's; it needs only the ``OPUS_CONFIG`` the
import already has. A flush that exits with a nonzero status fails the step with
:exc:`~opus_import.steps.do_django.CacheFlushError`. A simulated run, whose database is
read-only, skips the flush.

.. _dev_guide_import_steps_do_import:

opus_import.steps.do_import
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The observation import. Option: ``--import``, which ``--do-it-all`` implies. It also
owns the work for two options that are **not** steps of their own -- ``--scorched-earth``
and ``--delete-bundles`` -- because each has to happen at a particular point in this
sequence.

**The path.** An invocation that imports bundles first reads the target schema's state
(:func:`~opus_import.steps.do_import.choose_import_path`) and logs one line naming the
path it takes, the schema and its version
(:ref:`dev_guide_import_write_paths` gives the reasons):

* **no** ``schema_version`` **row, and none of the secondary keys finalization adds** on
  any observation or ``mult_`` table -- an empty schema, or one a fresh import is part
  way through, since a full import runs one invocation per bundle group: the **fresh
  import**. Each observation and ``mult_`` table is created with only the keys a load
  needs (:ref:`dev_guide_import_db_keys`);
* **one row, holding this release's version, in the** ``ready`` **or** ``appending``
  **state**: the **append**, into the tables with their keys in place;
* **a row of another version, more than one row, or another state**: refused, with a
  fatal message naming ``opus_import --scorched-earth --yes``, since a schema is
  re-imported under the release that will serve it;
* **no version row but such a key**: a finalization that was interrupted. The import is
  refused with a fatal message naming ``--finalize``. A finalization-only invocation
  completes it, since every finalization step is idempotent; ``--scorched-earth --yes``
  starts over.

A refusal comes before anything is written, and the invocation exits with failure.
:mod:`opus_import.cli` chooses before its first write; an invocation that erases the
schema first chooses after the erase.

:func:`~opus_import.steps.do_import.do_import_steps` is the whole sequence, and it runs
whether or not ``--import`` was given, because it is where the erase and the deletes
live. In order:

1. Reset :attr:`~opus_import.context.ImportContext.import_has_bad_data` and
   :attr:`~opus_import.context.ImportContext.max_table_id_cache`, and expand the bundle
   descriptors into a list of bundle ids.
2. **Erase the schema**, under ``--scorched-earth``, which :mod:`opus_import.cli` has
   already refused without ``--yes``. It logs the warning
   ``** DELETING EVERY OPUS TABLE IN SCHEMA <schema> **`` and drops every table the
   import creates (:func:`~opus_import.steps.do_import_tables.delete_all_opus_tables`).
   This has to happen first, so that there are no vestigial ``mult_`` tables and the row
   ids start again from 1.
3. **Delete the named bundles**, under ``--delete-bundles``: each one's rows from every
   observation table, then their rows in the bundle registry
   (:func:`~opus_import.bundle_registry.unregister_bundles`). It runs on any schema
   state. A schema whose version row is this release's version and ``ready`` is set to
   ``appending`` before the first delete, as an append sets it, since the deletion changes
   a finished schema; no other state is changed.
4. Stop here unless ``--import`` was given.
5. **Choose the path**, as above, if :mod:`opus_import.cli` has not.
6. **Record the bundles** in the bundle registry, creating its table first if the schema
   lacks it (:ref:`dev_guide_import_steps_registry`). On the append path the bundles are
   every bundle the registry holds that is not ``done``, in bundle order, followed by
   each named bundle not among them, and the version row is then set to ``appending``;
   on a fresh import they are the named bundles. A bundle OPUS skips is never recorded.
7. **Import each bundle.** It is marked ``importing`` and
   :attr:`~opus_import.context.ImportContext.bundle_has_errors` is cleared; it is deleted
   from every observation table
   (:func:`~opus_import.steps.do_import_tables.delete_bundle_from_obs_tables`) with
   foreign key checks on, so ``cart``'s cascading foreign key removes the cart rows that
   name its observations; it is imported through
   :func:`~opus_import.steps.do_import.import_one_bundle` with the checks off
   (:meth:`~opus_import.importdb.super.ImportDBSuper.foreign_keys_unchecked`), which
   validation's orphan count stands in for; and it is marked ``done``, or ``failed``
   when it logged an error, unless ``--ignore-errors``. Deleting first is what makes
   importing a bundle again, in the same invocation or a later one, replace it rather
   than load a second copy. A bundle whose import fails stops the loop, leaving the ones
   after it ``pending``, unless ``--ignore-errors``.

Any error at all makes the function return False once the loop ends, unless
``--ignore-errors``, and the invocation exits with failure. Neither path finalizes. A
failed fresh import leaves a schema with no version row and a failed append leaves one
``appending``, and a web application that loads either refuses to serve it, as both
deploy scripts refuse to promote it.

:func:`~opus_import.steps.do_import.import_one_bundle` is the per-bundle driver
described in :ref:`dev_guide_import_per_bundle`. It resets the per-bundle caches, skips
a bundle OPUS deliberately ignores
(:func:`~opus_import.steps.do_import_tables.opus_imports_bundle`), looks the bundle up
in ``BUNDLE_INFO``, finds the primary index files and imports each one. Under the
test-only fault ``OPUS_IMPORT_FAULT=log_error:<bundle>`` it logs one error inside that
bundle and carries on (:ref:`the import's fault sites <dev_guide_testing_faults>`).

.. _dev_guide_import_steps_registry:

The bundle registry: opus_import.bundle_registry
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:mod:`opus_import.bundle_registry` is the import's record of its work: one table,
``import_bundle``, holding a row per bundle and its state
(:ref:`dev_guide_database_schema_import_bundle`). Every invocation that imports bundles
creates the table when it is absent, with every key its schema declares
(:func:`~opus_import.bundle_registry.create_registry`), on both write paths, so that the
refusals below gate a fresh import as they gate an append.

A bundle moves through these states:

``pending``
    Recorded for import and not yet started.
    :func:`~opus_import.bundle_registry.register_bundles` sets every bundle an
    invocation is about to import to it, adding the rows the registry does not hold.

``importing``
    Being deleted and loaded.

``done``
    Imported without logging an error, or under ``--ignore-errors``.

``failed``
    Its import failed, or logged an error.

**A bundle OPUS skips is never recorded.**
:func:`~opus_import.steps.do_import_tables.opus_imports_bundle` is False exactly when
the bundle's ``BUNDLE_INFO`` entry exists and has no instrument class (``grep -n
"'instrument_class': None" src/opus_import/config_bundle_info.py`` lists them; the
``GALILEO`` and ``COCIRS`` shorthands expand to some), and both the import's skip and the
registration call it, so no row waits for an import that will never come. A bundle with
no entry at all is recorded, and its import fails.

**What a bundle's errors do.** A bundle has errors when its import fails or anything
logs an error while it runs: every site that marks the run as having produced bad data
(:meth:`~opus_import.context.ImportContext.mark_bad_data`) also sets
:attr:`~opus_import.context.ImportContext.bundle_has_errors`, which is cleared at the
start of each bundle. Without ``--ignore-errors`` such a bundle is ``failed``, the loop
stops at a bundle whose import fails, and the invocation exits with failure. With it,
the bundle is ``done`` despite its errors and the loop goes on: ``--ignore-errors`` is
how a debugging run reaches ``ready`` with errors.

**An unfinished registry is never finalized or marked ready.**
:func:`~opus_import.bundle_registry.unfinished_bundles` lists every bundle that is not
``done``. While it lists any, ``--finalize`` refuses to run, before its first step, so
nothing is changed, and ``--write-schema-version`` refuses to write ``ready``, neither
inserting the version row nor changing ``appending`` to ``ready``. Each refusal is a
fatal message naming every such bundle with its state, and saying to import them again
or remove them with ``--delete-bundles``; the invocation exits with failure and the
version row stays as it is, so a failed append followed by its closing invocations stays
``appending``. :mod:`opus_import.cli` checks after the invocation's own deletes and
import, which can finish the registry. With the table absent, or every bundle ``done``,
neither step is refused.

**Resuming.** A failed append leaves the schema ``appending``, the bundle it was on
``importing`` or ``failed`` and the bundles after it ``pending``. The next import on the
append path resumes every bundle that is not ``done`` and is not named, in bundle order,
before the ones it names, which keep their named order, and logs the list; because each bundle is deleted before it is written, the
rerun is clean. A fresh import resumes nothing on its own: a failed bundle is imported
again by naming it. A failed bundle's rows stay until it is next imported, which
deletes them first, or until ``--delete-bundles`` deletes them and its registry row.

``--scorched-earth`` drops ``import_bundle`` with every other table the import creates.

.. _dev_guide_import_steps_create_indexes:

opus_import.steps.do_indexes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Adds the secondary keys a fresh import left out. Option: ``--create-indexes``, the first
step of ``--finalize``.

:func:`~opus_import.steps.do_indexes.create_indexes` compares, for every observation
and ``mult_`` table, the keys
:func:`~opus_import.table_keys.add_secondary_indexes` derives from its schema with the
keys the server reports (:meth:`~opus_import.importdb.mysql.ImportDBMySQL.read_table_keys`),
**by kind and ordered columns, never by name**, since the server names an unnamed
composite key itself (``time1_2``). Only the missing keys are added, so the step is
idempotent: after an interruption it adds what is left, and on a finished schema it
logs that every table has every key and does nothing -- which is what it finds after an
append into tables that already have them, while a table the append created is keyed
here. It then adds them in three phases:

1. **The plain keys**, grouped per table into ``ALTER TABLE ... ADD KEY ..., ADD KEY
   ...`` statements, run for different tables at once over ``[import] index_workers``
   connections (:meth:`~opus_import.importdb.super.ImportDBSuper.build_indexes`), as
   :mod:`opus_import.cli` resolved it against the ceiling
   (:ref:`dev_guide_import_running_parallelism`) -- ``"max"`` is the ceiling itself. The
   list includes a plain key on every foreign-key column no other key leads -- each
   child's ``obs_general_id`` -- so the foreign keys find their index built rather than
   building it themselves one table at a time.
2. **The foreign keys**, one at a time with ``foreign_key_checks`` off, after every
   plain key: with the checks off, adding a foreign key is an in-place change that does
   not read the rows already there, and each one takes an exclusive lock on
   ``obs_general``. Because nothing then checks those rows, validation counts the
   orphans instead (:ref:`dev_guide_import_steps_do_validate`).
3. **ANALYZE** of every table that gained a key.

**Memory and temporary space.** Before each statement, the connection's sort buffer
(``innodb_ddl_buffer_size``, where the server has it) is sized to the estimated sort of
the largest key the statement builds (the estimate below), because a buffer far larger
than the sort costs time on every index. The server holds a whole buffer for each index
it is building at once -- every index the statement adds, up to the server's
``innodb_ddl_threads`` -- so the size is never above a quarter of the server's buffer
pool divided by ``index_workers`` and by that many indexes, and the builds running at
once hold at most a quarter of the pool together. Nor is it below the server's own
setting, unless that is above the same ceiling. The sorts write to the server's own temporary directory unless ``[import]
server_tmpdir`` names another -- a directory on the database server's host, never the
import's ``scratch_dir``. Each key's temporary space is estimated as
``rows x (key bytes + primary key bytes + 10) x 1.3``, with the rows the server counts
once the table has been analyzed, which the step does first. When the database server
runs on the same computer as the import (its host is ``localhost``, ``127.0.0.1`` or
``::1``) and ``server_tmpdir`` is given and its free space can be read, that free space
(or the data directory's, if less) is a budget the statements running at once must fit
together: a table's keys are split into as many statements as it takes, a statement
waits until it fits beside the ones running, and a key whose own estimate exceeds the
whole budget is refused with an error naming it. Otherwise each table's keys go in one
statement, and the total estimate is logged.

Each statement's and each table's wall-clock go into ``--timing-json``, as
``create_indexes:<table>:<keys>`` and ``create_indexes:<table>``, with each foreign key
as ``create_indexes:<table>:<key>``.

.. _dev_guide_import_steps_do_duplicate_ids:

opus_import.steps.do_duplicate_ids
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Keeps one copy of each OPUS ID. It has no option of its own: ``--finalize`` runs it,
after the keys, and skips it when the key builds failed, since it deletes by
``obs_general_id``, which only those keys index. OPUS IDs are compared as the column's
collation compares them, so two that differ only in case are the same ID.

Two bundles can produce the same OPUS ID -- Galileo SSI does, and so can a calibrated
bundle and its raw counterpart -- and ``obs_general.opus_id`` has a plain key, not a
unique one, so both copies load side by side; no import looks for them while it loads.
:func:`~opus_import.steps.do_duplicate_ids.delete_duplicate_opus_ids` finds every OPUS
ID with more than one ``obs_general`` row, **keeps the row with the highest id**, and
deletes the others' rows from every observation table by ``obs_general_id``, children
first. Row ids are handed out in import order, so the copy kept is the one imported
last: a duplicate between bundles is settled in favor of the later bundle's copy, on a
fresh import and an append alike. This step is the only place a duplicate between
bundles is settled, and an append invalidates it, so the ``--finalize`` after every
append runs it again.

Each deleted copy is logged at info level when it came from a different bundle than the
copy kept, and as a **warning** when it came from the same bundle, which is a fault in
that bundle's data. The step runs with foreign-key checks on, so ``cart``'s cascading
foreign key removes a cart row that names a deleted copy rather than leaving it
orphaned, and ends by checking that no OPUS ID has two rows; a failure keeps the
invocation from marking the schema ready, as a validation failure does.

.. _dev_guide_import_steps_table_swap:

Rebuilding a table by swap: opus_import.table_swap
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The three auxiliary tables and the dictionary are rebuilt on a schema the web
application may be serving -- the code-only deploy rebuilds all of them on the live
database -- so none of them is ever dropped and refilled in place. Each step builds its
table as ``<table>__new``, fills it while the live table goes on answering, and swaps it
in with one ``RENAME TABLE`` that moves the live table aside to ``<table>__old`` and the
new one into its place. MySQL applies the whole statement atomically, so a reader finds
each table as it was or as it now is, never missing and never partly filled. The
``__old`` table is dropped afterwards.

:func:`~opus_import.table_swap.rebuild_tables_by_swap` is the one entry point. It takes a
set of tables, parents first, and a fill function, and:

1. drops any ``__new`` or ``__old`` table an interrupted rebuild of the same set left,
   children before parents;
2. creates every ``__new`` table, empty, from its packaged schema, with any foreign key
   from one table of the set to another pointed at the other's ``__new`` table;
3. calls the fill, which writes every row into the ``__new`` tables. A fill that returns
   False drops them again and leaves the live tables as they were;
4. analyzes each ``__new`` table. The server's persistent statistics for a table
   created empty say it has no rows, the rename carries them across, and nothing
   recomputes them soon after a bulk fill, so a table swapped in unanalyzed goes live
   with statistics that mislead the optimizer -- at fixture scale, validation against
   such a ``param_info`` took over a third longer;
5. swaps the whole set in with one rename
   (:meth:`~opus_import.importdb.mysql.ImportDBMySQL.rename_tables_atomically`), then
   drops the ``__old`` tables.

The dictionary is the set that needs step 2: ``contexts`` and ``definitions`` swap
together, and the foreign key from ``definitions__new`` onto ``contexts__new`` follows
the rename onto the live ``contexts``. The key name the server generated follows it too.

The rename waits for any transaction open on the tables it names. Each attempt lowers
the session's ``lock_wait_timeout`` to ``SWAP_LOCK_WAIT_TIMEOUT_S`` seconds, so a rename
queued behind a long reader does not in turn hold up every reader queued behind it; a
timed-out attempt is logged at info level and tried again, up to
``SWAP_RENAME_ATTEMPTS`` times, and the session's own value is restored afterwards.

.. _dev_guide_import_steps_do_param_info:

opus_import.steps.do_param_info
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Builds ``param_info``, the table that tells the web application what the search form
contains. Option: ``--create-param-info``.

Its public functions: :func:`~opus_import.steps.do_param_info.fill_param_info` writes
the rows into ``param_info__new``, and :func:`~opus_import.steps.do_param_info.do_param_info`
is the step, which rebuilds the table by swap
(:ref:`dev_guide_import_steps_table_swap`).

One row per column that carries a ``pi_category_name``, read out of the **packaged
schema** of every ``obs_`` table in the schema. A column with no ``param_info`` row is
invisible to users no matter what the import wrote into it. The row copies the ``pi_*``
keys across, and three of them are read without a default --
``pi_disp_order``, ``pi_display`` and ``pi_display_results`` -- so a column that carries
``pi_category_name`` and omits one of those fails the build rather than defaulting.

Two validations happen here rather than at the schema:

* a ``pi_form_type`` naming a unit id :func:`opus_support.units.is_valid_unit_id` does
  not recognize fails the build;
* a ``pi_ranges`` naming an entry that is not in ``param_info_ranges.json`` fails it
  too.

Nothing is written until every column has been read, so a failed build leaves
``param_info__new`` empty rather than half filled -- but the build stops at the **first**
fault, so one run reports only that one. A failed build is not swapped in: the live table
keeps what the previous run wrote. A failed build also keeps the invocation from marking the
schema ready and makes it exit with failure, as a validation failure does
(:ref:`dev_guide_import_steps_do_validate`).

This step must follow the import, because which ``obs_`` tables exist is what decides
which schemas it reads, and an append that adds a table invalidates it.

.. _dev_guide_import_steps_do_partables:

opus_import.steps.do_partables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Builds ``partables``, which maps a value a user can search for onto the table of further
search parameters that value makes relevant -- choosing the Cassini mission reveals the
Cassini mission table. Option: ``--create-partables``.

Its public functions, in the same shape as :mod:`~opus_import.steps.do_param_info`'s:
:func:`~opus_import.steps.do_partables.fill_partables` and
:func:`~opus_import.steps.do_partables.do_partables`.

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

opus_import.steps.do_table_names
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Builds ``table_names``, which names and orders the "Constraints" categories the search
form and the Details tab are divided into. Option: ``--create-table-names``.

Its public functions:
:func:`~opus_import.steps.do_table_names.build_table_names_rows`,
:func:`~opus_import.steps.do_table_names.fill_table_names` and
:func:`~opus_import.steps.do_table_names.do_table_names`.

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
3. One per ``obs_surface_geometry__<TARGET>`` table, labeled from the decoded target
   name.
4. ``obs_ring_geometry``, if it exists.
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

opus_import.steps.do_update_mult_info
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Writes the display details a schema pins for a ``mult_`` table -- the label, the sort
order, the display flag, the grouping -- back over the table the import discovered, so
that editing a schema changes a label without a re-import. Option:
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

opus_import.steps.do_validate
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Checks the invariants no database constraint can express. Option: ``--validate``.
**Nothing here changes the database**:
the tables are already written, and an import that produced them is not undone by a
validation error. Every check runs and logs each failure at error level, so one run
reports them all.

**A failure keeps the schema from being served.** When a check logged an error, the
invocation does not run ``--write-schema-version`` even if it was asked to, logging an
error instead, and exits with failure once its other steps have run, so
``opus_import_all`` stops before its own version step. ``--ignore-errors`` on
the same invocation overrides both, for a debugging run; ``opus_import_all`` never passes
it to its finishing steps.

The checks, in this order:

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
    its low end legitimately exceeds its high end, and so is a column whose
    ``param_info`` form type is NULL. A missing ``X2``, an absent
    ``param_info`` row, or more than one, is an error.

:func:`~opus_import.steps.do_validate.validate_filter_wavelength_consistency`
    For every table with a ``filter_name`` or ``combined_filter`` column, checks that
    all observations sharing a filter agree about that filter's nine wavelength
    columns. ``obs_instrument_coiss`` is grouped by camera as well as by filter,
    because its two cameras carry filters of the same name. Reported as a warning.

:func:`~opus_import.steps.do_validate.validate_orphans`
    Counts, for every observation table other than ``obs_general`` and for ``cart``,
    the rows whose ``obs_general_id`` names no ``obs_general`` row, by an anti-join. A
    foreign key added with the checks off, as finalization adds them, never reads the
    rows already there, so this is the check that it holds. Any orphan is an error.

:func:`~opus_import.steps.do_validate.validate_unique_opus_ids`
    Groups ``obs_general`` by ``opus_id`` and reports any OPUS ID more than one row
    carries, with how many there are and the first ten. ``opus_id`` carries a plain key,
    and the duplicate step of ``--finalize`` is what leaves one row per OPUS ID, so a
    schema that has not been through it can hold two. Any shared OPUS ID is an error.

.. _dev_guide_import_steps_do_dictionary:

opus_import.steps.do_dictionary
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Fills ``contexts`` and ``definitions``, which is where every tooltip in the user
interface comes from. Option: ``--import-dictionary``. Only the schema version comes
after it.
:ref:`dev_guide_dictionary` describes the two tables and where their content comes from.

Its public functions:
:func:`~opus_import.steps.do_dictionary.fill_contexts` and
:func:`~opus_import.steps.do_dictionary.fill_definitions` fill ``contexts__new`` and
``definitions__new``, and :func:`~opus_import.steps.do_dictionary.do_dictionary` is the
step.

The step rebuilds the two tables as one set by swap
(:ref:`dev_guide_import_steps_table_swap`): both are filled before either is swapped in,
and one rename swaps both, so a reader never finds the dictionary missing, partly filled
or with one table new and the other old. The definitions fill also writes the mult
tooltip contexts into ``contexts__new``, which is why the two fill functions share it.

The definitions builder collects every fault before writing anything; the contexts
builder stops at the first malformed line. Either way nothing is written and the live
tables keep what the previous run wrote. A failed dictionary import is logged,
keeps the invocation from marking the schema ready, and makes it exit with failure, as a
validation failure does (:ref:`dev_guide_import_steps_do_validate`).

.. _dev_guide_import_steps_do_schema_version:

opus_import.steps.do_schema_version
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Marks the schema finished. Option: ``--write-schema-version``, which nothing
implies: it is the last step of every sequence that finishes a database, after the
validation. It creates the one-row ``schema_version`` table when it is absent, and then,
by what the row holds:

* **no row**: inserts :data:`~opus_import.schema_version.SCHEMA_VERSION` in the
  ``ready`` state;
* **this version,** ``appending``: changes the state to ``ready``, logged at info level;
* **this version,** ``ready``: nothing, logged at debug level;
* **another version, or more than one row**: refuses. It logs an error, leaves the
  table as it is, and the run **exits non-zero**. A schema another release imported is
  re-imported under this one, never restamped.

Before any of that, :mod:`opus_import.cli` refuses the step, with a fatal message and a
non-zero exit, while any bundle in the bundle registry is not ``done``
(:ref:`dev_guide_import_steps_registry`), and when a finishing step of the same
invocation failed, unless ``--ignore-errors``; either way the row is left as it is.

It is the only writer of ``ready``. ``--finalize``, ``--import-dictionary``
and ``--do-it-all`` leave the row alone, so a schema they finished is not served until
this step runs; an append sets it to ``appending`` and leaves it so.
``--scorched-earth`` drops the table before any other, so an erase that stops part way
leaves no version row behind.
:ref:`dev_guide_database_schema_version` describes the table and who reads it.

The internal modules
--------------------

These are the internals of :mod:`~opus_import.steps.do_import`. **They are not steps**:
no command-line option runs one on its own, and nothing outside ``do_import`` calls
them as a unit.

.. _dev_guide_import_steps_do_import_tables:

opus_import.steps.do_import_tables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Creating the ``obs_`` and ``mult_`` tables, deleting from them, and dropping every table
the import creates.

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

:func:`~opus_import.steps.do_import_tables.opus_imports_bundle`
    Whether OPUS imports a bundle: False exactly when its ``BUNDLE_INFO`` entry exists
    and has no instrument class, True otherwise, a bundle with no entry included. The
    import's skip and the bundle registry both call it
    (:ref:`dev_guide_import_steps_registry`).

:func:`~opus_import.steps.do_import_tables.create_tables_for_import`
    Creates every table a bundle needs that the schema lacks, and every ``mult_`` table
    its GROUP-typed columns need. It returns the schemas it read and the table names in
    order, which is what the index importer walks. **The
    ``obs_surface_geometry__<TARGET>`` tables are deliberately not created here**: the
    target names are not known until the observations have been read, so the index
    importer's row sink creates each from the template just before it loads the first
    rows for that target. The template schema is still returned, because the import needs
    the column names.

.. _dev_guide_import_steps_scorched_earth:

:func:`~opus_import.steps.do_import_tables.delete_all_opus_tables`
    **Scorched earth**: drops every table the import creates, leaving Django's own
    (``opus_manage migrate``'s ``django_*`` and ``auth_*`` tables, ``django_session``
    among them). The tables are named by two constants, so nothing outside them is ever
    dropped, not even a table of no known name:
    :data:`~opus_import.steps.do_import_tables.OPUS_TABLE_PREFIXES` (``obs_`` and
    ``mult_``, which catch every observation and mult table however many there are)
    and
    :data:`~opus_import.steps.do_import_tables.OPUS_TABLE_NAMES`, the other tables by
    exact name -- ``schema_version``, ``cart``, ``import_bundle``, the auxiliary
    tables, the dictionary's, ``user_searches``, ``search_results``, and the ``__new``
    and ``__old`` tables
    an interrupted swap can leave (:ref:`dev_guide_import_steps_table_swap`). A step that
    creates a table outside the prefixes adds its name there. The drop order is the one
    the foreign keys allow: ``schema_version`` first, so an erase that stops part way
    leaves a schema nothing serves or promotes; every ``obs_`` table but
    ``obs_general``; ``cart``; ``obs_general``; ``definitions`` and its swap tables,
    which reference ``contexts``; every other exact name; and the ``mult_`` tables
    last.

:func:`~opus_import.steps.do_import_tables.delete_bundle_from_obs_tables`
    Deletes one bundle from every observation table, every other table before
    ``obs_general``, in chunks: a table's ids for the bundle are read through its
    ``bundle_id`` key, which each of these tables is created with, and each ``[import]
    transaction_rows`` of them go in one statement selecting by ``bundle_id`` and a
    range of the table's own ``id``. Each statement is its own transaction, so none
    holds a whole large bundle's undo, and none reads rows outside its range -- which
    matters on a fresh import, whose tables have no other key to find a bundle's rows by
    until finalization. The connection checks foreign keys while it deletes, so
    ``cart``'s cascade removes the cart rows that name the bundle's observations.

:func:`~opus_import.steps.do_import_tables.analyze_all_tables`
    Runs the backend's analyze over every ``obs_`` and ``mult_`` table, for
    ``--analyze-tables``, which :mod:`opus_import.cli` runs after the auxiliary, cart
    and search tables. ``cart`` and the auxiliary tables are not analyzed; each auxiliary
    table is analyzed by its swap.

.. _dev_guide_import_steps_do_import_index:

opus_import.steps.do_import_index
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Importing every observation one primary index file describes.
:ref:`dev_guide_import_one_index` walks it; this section names its parts.

:func:`~opus_import.steps.do_import_index.import_one_index`
    The whole of it: read the primary index, resolve ambiguous rows, discover and
    cross-reference the associated metadata files, compute every row through
    :func:`~opus_import.steps.do_import_pool.compute_index`, then write the ``mult_``
    tables and load what is left of the ``obs_`` rows. It returns False, abandoning the
    index, when a pool worker failed.

:class:`~opus_import.steps.do_import_index.IndexState`
    What every row of the index is computed from, built once the metadata is assembled
    and the tables are created: the obs instance, the metadata dictionary it reads, a
    copy of that dictionary as it stands before the first row
    (:attr:`~opus_import.steps.do_import_index.IndexState.base_metadata`), the table
    schemas and their order, the PDS version, and the index rows. A pool's workers inherit
    it by ``fork``.

:func:`~opus_import.steps.do_import_index.import_index_row`
    Computes every table's rows for one index row and hands each to a row emitter, in the
    order the tables are walked. **It first clears the metadata dictionary and refills it
    from** ``base_metadata``, so what a row computes depends on that row alone and not on
    the rows computed before it in the same process -- which is what lets any process
    compute any row. It is the one row function, run by the serial loop and by every pool
    worker alike.

:class:`~opus_import.steps.do_import_index.TableRowSink`
    Where the import's own process sends each finished row, by table. A table's rows are
    loaded as soon as ``[import] transaction_rows`` of them are waiting
    (:meth:`~opus_import.importdb.super.ImportDBSuper.bulk_load_rows`), so the import
    holds at most that many rows of a table at once rather than a whole index's; a
    surface geometry target's table is created from the template just before its first
    load. :meth:`~opus_import.steps.do_import_index.TableRowSink.finish` loads what is
    still waiting, table by table in the order walked, the targets' tables in the order
    of their target names. Tables therefore load in no fixed order relative to one
    another during the index, which the foreign keys tolerate because a bundle loads with
    their checks off (:ref:`dev_guide_import_steps_do_import`). An index that fails
    partway is taken back by
    :meth:`~opus_import.steps.do_import_index.TableRowSink.discard`, which deletes each
    table's rows from the first id the sink loaded: the index's mult values are never
    written, so a row of it left behind would hold a mult id a later bundle gives to
    another value.

:func:`~opus_import.steps.do_import_index.get_opus_products_rows_for_filespec`
    The ``obs_files`` rows for one observation: one row per file of one product type at
    one version, carrying where it lives, how big it is, its checksum, and the ordering
    the results page shows the product types in. It leaves out two kinds of file -- a
    shared index or summary file that does not list this observation, and a PDS3 file
    whose shelf metadata is missing (with a warning, because its size and checksum are
    unknown). A file that is not the current version is never checked by default.

.. _dev_guide_import_steps_do_import_pool:

opus_import.steps.do_import_pool
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Computing an index's rows in a pool of forked processes. **Many processes compute, one
writes**: the workers compute, and only the import's own process touches the database
or the log.

:func:`~opus_import.steps.do_import_pool.compute_index` is the entry point. With
:attr:`~opus_import.context.ImportContext.workers` at 1, or an index of fewer rows than
:attr:`~opus_import.context.ImportContext.worker_rows`, it runs the row function over
every row in the import's own process, handing each row straight to the sink. A platform
without the ``fork`` start method computes the same way, and says so on an info line.
Otherwise it computes in a pool:

* **The pool is created once per index**, after the index's metadata is assembled and its
  tables are created, with the ``fork`` start method named explicitly. The state the
  rows are computed from is installed in a module global before the pool exists, so the
  workers inherit it -- the context, the
  :class:`~opus_import.steps.do_import_index.IndexState`, the row function -- and nothing
  is pickled to a worker but a task: a ``(start, end)`` range of row numbers,
  ``worker_rows`` long.
* **Each worker runs the same row function** as the serial loop, over its range, with a
  :class:`~opus_import.deferred.Capture` installed on its context
  (:attr:`~opus_import.context.ImportContext.capture`). Everywhere the code would ask
  the database for something or write a message, it records an event on the capture
  instead, each event carrying the index row number and primary file specification the
  worker was at (:mod:`opus_import.deferred`):

  - a new row id (:func:`~opus_import.import_util.next_table_id`) is a
    :class:`~opus_import.deferred.LocalId`, numbered from zero per table within the task;
  - a ``mult_`` value (:func:`~opus_import.steps.do_import_mult.update_mult_table`) is
    recorded with its arguments and stands in the row as a
    :class:`~opus_import.deferred.MultRef`;
  - a ``mult_list`` column holding either is a :class:`~opus_import.deferred.DeferredJson`,
    the list before it is turned into JSON;
  - a computed row, an :class:`~opus_import.context.ImportLog` call, a Python warning,
    and a call of a ``pdsfile`` class's own logger are each recorded as they happen.

  A placeholder is not validated in
  :func:`~opus_import.steps.do_import_obs.import_observation_table`; an id has nothing to
  check.
* **The import's process takes results in index order**, keeping a bounded number of
  tasks queued ahead of the one it is replaying
  (:data:`~opus_import.steps.do_import_pool.TASKS_AHEAD_PER_WORKER` per worker), and
  **replays each task's events where the serial loop would have made them**. A
  :class:`~opus_import.deferred.LocalId` becomes the id the table had when the task's
  replay began, plus its number, plus one, and the table's cached id then moves past the
  task's last; each recorded ``mult_`` value goes through
  :func:`~opus_import.steps.do_import_mult.update_mult_table` in the serial order, so it
  gets the id the serial loop gives it; each log call is made on ``ctx.log`` with the
  recorded position, so the non-repeating variants deduplicate in the import's process
  exactly as they do serially; each Python warning is issued again with its class and
  location, against the registry of the module it came from, so the import's process's
  own filters decide whether it is shown -- a warning shown once per location is shown
  once however many workers met it -- and ``pdsfile`` calls go to the real logger. Each row then goes to the sink with every value final. **The
  tables, their ids, the** ``mult_`` **ids and the log are therefore the same whatever the
  number of workers.**
* **A worker's failure abandons the index**: the import's process logs an error naming
  the range of rows and the index file, replays nothing after it, and
  :func:`~opus_import.steps.do_import_index.import_one_index` returns False. Rows the sink
  had already loaded stay until the bundle is imported again, which deletes it first.

**What a worker does with what it inherited.** A worker exits by ``os._exit``, so nothing
it inherited is ever closed or flushed on its way out, and its initializer is the only
place it deals with it:

* every database connection the import's process had open is let go of without a byte
  sent on it (:func:`~opus_import.importdb.super.close_inherited_connections`): every
  :class:`~opus_import.importdb.super.ImportDBSuper` instance registers itself when
  created, and the worker closes each one's socket descriptor with :func:`os.close`,
  which leaves the import's session untouched, then keeps the instance referenced for the
  rest of its life, so the driver's destructor never sends its quit message on a
  descriptor number the worker may since have reused. The worker's context has no
  database at all;
* on Linux it asks the kernel (``prctl(PR_SET_PDEATHSIG, SIGKILL)``) to kill it when the
  import's process dies, and exits at once if that process died before the request.
  Elsewhere a worker outlives a killed import's process; a worker that kept an inherited
  socket open would keep the import's session alive after it, which is what closing them
  prevents;
* Python warnings and the ``pdsfile`` classes' loggers are redirected onto the task's
  capture, since the worker shares the import's log files.

**Test-only faults.** Under ``OPUS_IMPORT_FAULT=stall_worker:<seconds>`` every task
first sleeps for that many seconds, so a test can find the pool's workers alive; under
``OPUS_IMPORT_FAULT=fail_worker:<row>`` the task holding that index row, numbered from
zero, fails (:ref:`the import's fault sites <dev_guide_testing_faults>`).

.. _dev_guide_import_steps_do_import_obs:

opus_import.steps.do_import_obs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Computing one row of one observation table. :ref:`dev_guide_import_one_row` walks the
dispatch and the validation; the three functions are:

:func:`~opus_import.steps.do_import_obs.import_observation_table`
    Walks a table's schema, obtains each column's value, checks it, replaces an
    enumerated value with its ``mult_`` row id, and assembles the row. It returns None
    only when a group column's field method returned something that is not a mult
    specification, which is not recoverable -- the whole observation is discarded.

:func:`~opus_import.steps.do_import_obs.field_function_name`
    The naming rule of :ref:`dev_guide_import_one_row`. The tests resolve the hierarchy
    against the schemas *through this function* rather than restating the rule, so
    changing it here changes what they check.

:func:`~opus_import.steps.do_import_obs.import_run_field_function`
    Calls the method and turns a missing method or an exception into a logged error and
    a None value.

.. _dev_guide_import_steps_do_import_mult:

opus_import.steps.do_import_mult
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Reading, caching and writing the ``mult_`` tables that hold the enumerated values of
the ``obs_`` columns. Its public functions:
:func:`~opus_import.steps.do_import_mult.read_or_create_mult_table` fetches one table
into the run's cache, :func:`~opus_import.steps.do_import_mult.mult_table_lookup_id`
finds an existing value's row id without adding one,
:func:`~opus_import.steps.do_import_mult.update_mult_table` finds or adds a value and
returns the id an ``obs_`` column stores, and
:func:`~opus_import.steps.do_import_mult.write_mult_tables` writes the modified tables
back.

**Naming.** :func:`~opus_import.import_util.table_name_mult` builds
``mult_<table>_<column>``, both lowercased --
``mult_obs_general_planet_id``.

**Caching.** Every table is read once per bundle into the
context's cache and written back at the end of each index file, so importing an index of a
hundred thousand rows does not query for the same enumeration a hundred thousand times.
The cache lives in the import's own process: in a pool worker,
:func:`~opus_import.steps.do_import_mult.update_mult_table` reads and changes nothing,
and records its arguments for the import's process to resolve
(:ref:`dev_guide_import_steps_do_import_pool`). Two collections track it, both cleared
per bundle:

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Context field
     - Lifetime and meaning
   * - :attr:`~opus_import.context.ImportContext.mult_table_cache`
     - Each table read or created during this bundle, keyed by its name. The returned
       list *is* the cache: appending to it is how a value is added.
   * - :attr:`~opus_import.context.ImportContext.modified_mult_tables`
     - The tables this bundle added values to, and which therefore have to be written
       back.

**Reading a table.** A table that exists is read, so a bundle sees every value the
bundles before it added, on a fresh import and an append alike; a table that does not
exist yet starts the cache empty, and the import fills it as it meets values. A column
that pins its values with ``mult_options`` short-circuits this and is marked modified
immediately.

**Keying and id assignment.** Lookup is a linear scan comparing the stringified value.
A new value is given ``max(existing ids) + 1``, or 0 in an empty table. A value absent
from a table whose values are pinned by ``mult_options`` is an error, and returns 0.

**The derived sort order** is where a value's position in the search form comes from
when the schema pins none. The rules, in order: a null-ish label sorts to the end,
keyed ``zzz`` for ``NULL``, ``zzy`` for ``N/A`` and ``zzx`` for ``NONE`` -- unless the
column has a unit, in which case those three sort by their own text instead; a column
with a unit sorts by the parsed number, zero-padded; a table whose labels are all
numeric sorts numerically; ``Yes`` sorts before ``No`` and ``On`` before ``Off``;
anything else sorts by its label.

**Writing back.** :func:`~opus_import.steps.do_import_mult.write_mult_tables` upserts
every modified table at the end of each index file, once every row has been computed and
before the sink loads the ``obs_`` rows still waiting; a table whose rows filled a
transaction during the index was loaded earlier, holding ids its ``mult_`` table gains
only here. A bundle that is deleted leaves its values in the ``mult_`` tables,
where an observation of another bundle may hold them too.

API reference
-------------

:doc:`api_opus_import`
