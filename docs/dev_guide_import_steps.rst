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
        C1[do_cart:<br/>create the empty cart table]
        C2[do_django:<br/>drop cache_*, reset user_searches]
        I[do_import:<br/>the observation import,<br/>and the copy to permanent]
        K[do_indexes:<br/>the secondary keys]
        DU[do_duplicate_ids:<br/>one copy of each OPUS ID]
        P[do_param_info]
        PT[do_partables]
        TN[do_table_names]
        A[analyze the tables]
        UM[do_update_mult_info]
        V[do_validate]
        C3[do_cart, second attempt<br/>if the first was deferred]
        D[do_dictionary]
        SV[do_schema_version]

        C1 --> C2 --> I
        I --> K --> DU --> P --> PT --> TN --> A --> UM --> V --> C3 --> D --> SV

* **The cart and cache cleanup comes first** because a ``cart`` row carries a foreign
  key onto ``obs_general``, so the cart has to be emptied before the permanent tables
  are rebuilt underneath it.
* **The keys come right after the import**, and the foreign keys after every other key,
  because a fresh import loads its tables without them; the duplicate step follows,
  because it finds the copies through the key on ``opus_id`` and deletes them through
  the keys on ``obs_general_id``.
* **The auxiliary tables come after the import** because each is derived from which
  permanent tables exist and from their schemas.
* **The tables are analyzed after the auxiliary tables**, so that the statistics count
  every table's rows.
* **The dictionary comes after them** because nothing else depends on it.
* **The schema version comes last** because its row is what makes the schema
  servable, so it is written only once everything else, validation included, has run.
* ``--drop-permanent-tables`` moves the first part: :mod:`opus_import.cli` skips the
  leading cleanup, because dropping the permanent tables would drop the cart again, and
  :func:`~opus_import.steps.do_import.do_import_steps` performs it after the drop
  instead.

The steps
---------

.. _dev_guide_import_steps_do_cart:

opus_import.steps.do_cart
~~~~~~~~~~~~~~~~~~~~~~~~~

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

opus_import.steps.do_django
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Discards the tables the web application caches search results in. Option:
``--drop-cache-tables``.

:func:`~opus_import.steps.do_django.drop_cache_tables` drops every table whose name
starts with ``cache_`` -- found **by prefix**, across both namespaces, because a cache
table is named after a row of ``user_searches`` rather than defined by a schema -- and
then drops and recreates ``user_searches`` empty in the permanent namespace.

An import changes what a search returns, so every cached result is stale the moment it
finishes.

.. _dev_guide_import_steps_do_import:

opus_import.steps.do_import
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The observation import. Option: ``--import``, plus everything that implies it. It also
owns the work for options that are **not** steps of their own --
``--drop-permanent-tables`` and ``--delete-import-bundles`` -- because each has to happen
at a particular point in this sequence.

**The path.** An invocation that imports bundles first reads the target schema's state
(:func:`~opus_import.steps.do_import.choose_import_path`) and logs one line naming the
path it takes, the schema and its version:

* **no** ``schema_version`` **row, and none of the secondary keys finalization adds** on
  any permanent observation table -- an empty schema, or one a fresh import is part way
  through, since a full import runs one invocation per bundle group: the **fresh
  import**. It sets ``ImportDBSuper.direct``, under
  which the import namespace names the permanent observation and ``mult_`` tables, so
  every bundle is written straight to them, and creates each of those tables with only
  the keys a load needs (:ref:`dev_guide_import_db_keys`);
* **a version row**: the **import tables**, staged in the import namespace and copied
  over the permanent tables at the end;
* **no version row but such a key**: a finalization that was interrupted. The import is
  refused with a fatal message naming ``--finalize``, before anything is written, and
  the invocation exits with failure. A finalization-only invocation completes it, since
  every finalization step is idempotent; ``--drop-permanent-tables --scorched-earth``
  starts over.

:mod:`opus_import.cli` chooses before its first write; an invocation that erases the
schema first chooses after the erase.

:func:`~opus_import.steps.do_import.do_import_steps` is the whole sequence, and it runs
whether or not ``--import`` was given, because it is where the copy and the drops live.
In order:

1. Reset the per-run caches:
   :attr:`~opus_import.context.ImportContext.import_has_bad_data`,
   :attr:`~opus_import.context.ImportContext.max_table_id_cache` and
   :attr:`~opus_import.context.ImportContext.created_import_mult_tables`.
2. Expand the bundle descriptors into a list of bundle ids.
3. **Drop the permanent tables**, under ``--drop-permanent-tables`` **and**
   ``--scorched-earth`` together. This has to happen before the import so that there
   are no vestigial ``mult_`` tables and the row ids restart from zero. The cart and
   cache cleanup that :mod:`opus_import.cli` skipped is performed here, after the drop.
4. **Choose the path**, as above, when ``--import`` was given and it is not chosen yet.
5. **Drop the old import tables**, under ``--drop-old-import-tables`` unless
   ``--leave-old-import-tables`` overrides it. A fresh import has none, and logs that at
   debug level instead.
6. **Delete the named bundles from the import tables**, when ``--import`` or
   ``--delete-import-bundles`` was given and the import tables were not just dropped.
   A fresh import skips it, at debug level.
7. **Import each bundle** through
   :func:`~opus_import.steps.do_import.import_one_bundle`. **A fresh import first
   deletes the bundle from the permanent tables**
   (:func:`~opus_import.steps.do_import_tables.delete_bundle_from_obs_tables`), so
   importing a bundle again, in the same invocation or a later one, replaces it rather
   than loading a second copy. A failure aborts the loop unless
   ``--import-ignore-errors``, and any error at all makes the function return False --
   so the copy below never happens.
8. **Delete from the permanent tables** every bundle the import tables hold, read as
   ``SELECT DISTINCT bundle_id`` off the import ``obs_general``. ``--delete-permanent-bundles``
   separately deletes the bundles named on the command line.
9. **Copy the import tables over the permanent ones**, under
   ``--copy-import-to-permanent-tables``, in this order: create the permanent tables
   each bundle needs, delete duplicate OPUS IDs from the permanent tables, copy the
   ``mult_`` tables, then copy each bundle's ``obs_`` rows.
10. **Drop the new import tables** under ``--drop-new-import-tables``.

Steps 8 to 10 belong to the import tables; a fresh import has already written the
permanent tables, and says so at debug level. ``--delete-permanent-bundles`` runs on
either path: on a fresh import before the first bundle is imported, otherwise before
the copy. A failed fresh import leaves a schema with no version row, which the web
application refuses to serve and both deploy scripts refuse to promote.

:func:`~opus_import.steps.do_import.import_one_bundle` is the per-bundle driver
described in :ref:`dev_guide_import_per_bundle`. It resets the per-bundle caches, looks
the bundle up in ``BUNDLE_INFO``, finds the primary index files and imports each one.

.. _dev_guide_import_steps_create_indexes:

opus_import.steps.do_indexes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Adds the secondary keys a fresh import left out. Option: ``--create-indexes``, the first
step of ``--finalize``.

:func:`~opus_import.steps.do_indexes.create_indexes` compares, for every permanent
observation and ``mult_`` table, the keys
:func:`~opus_import.table_keys.add_secondary_indexes` derives from its schema with the
keys the server reports (:meth:`~opus_import.importdb.mysql.ImportDBMySQL.read_table_keys`),
**by kind and ordered columns, never by name**, since the server names an unnamed
composite key itself (``time1_2``). Only the missing keys are added, so the step is
idempotent: after an interruption it adds what is left, and on a finished schema it
logs that every table has every key and does nothing. It then adds them in three
phases:

1. **The plain keys**, grouped per table into ``ALTER TABLE ... ADD KEY ..., ADD KEY
   ...`` statements, run for different tables at once over ``[import] index_workers``
   connections (:meth:`~opus_import.importdb.super.ImportDBSuper.build_indexes`). The
   list includes a plain key on every foreign-key column no other key leads -- each
   child's ``obs_general_id`` -- so the foreign keys find their index built rather than
   building it themselves one table at a time.
2. **The foreign keys**, one at a time with ``foreign_key_checks`` off, after every
   plain key: with the checks off, adding a foreign key is an in-place change that does
   not read the rows already there, and each one takes an exclusive lock on
   ``obs_general``. Because nothing then checks those rows, validation counts the
   orphans instead (:ref:`dev_guide_import_steps_do_validate`).
3. **ANALYZE** of every table that gained a key.

**Memory and temporary space.** Each connection's sort buffer
(``innodb_ddl_buffer_size``, where the server has it) is set to a quarter of the
server's buffer pool divided by ``index_workers``, so the builds running at once hold at
most a quarter of the pool together. The sorts write to the server's own temporary
directory unless ``[import] server_tmpdir`` names another -- a directory on the database
server's host, never the import's ``scratch_dir``. Each key's temporary space is
estimated as ``rows x (key bytes + primary key bytes + 10) x 1.3``. When the database
server runs on the same computer as the import (its host is ``localhost``,
``127.0.0.1`` or ``::1``) and ``server_tmpdir`` is given and its free space can be read,
that free space (or the data directory's, if less) is a budget the statements running at
once must fit together: a table's keys are split into as many statements as it takes,
a statement waits until it fits beside the ones running, and a key whose own estimate
exceeds the whole budget is refused with an error naming it. Otherwise each table's keys
go in one statement, and the total estimate is logged.

Each statement's and each table's wall-clock go into ``--timing-json``, as
``create_indexes:<table>:<keys>`` and ``create_indexes:<table>``, with each foreign key
as ``create_indexes:<table>:<key>``.

.. _dev_guide_import_steps_do_duplicate_ids:

opus_import.steps.do_duplicate_ids
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Keeps one copy of each OPUS ID. It has no option of its own: ``--finalize`` runs it,
after the keys.

Two bundles can produce the same OPUS ID -- Galileo SSI does, and so can a calibrated
bundle and its raw counterpart -- and ``obs_general.opus_id`` has a plain key, not a
unique one, so both copies load side by side; no import looks for them while it loads.
:func:`~opus_import.steps.do_duplicate_ids.delete_duplicate_opus_ids` finds every OPUS
ID with more than one ``obs_general`` row, **keeps the row with the highest id**, and
deletes the others' rows from every observation table by ``obs_general_id``, children
first. Row ids are handed out in import order, so the copy kept is the one imported
last: a duplicate between bundles is settled in favor of the later bundle's copy, and a
bundle imported again replaces its own earlier copy.

Each deleted copy is logged at info level when it came from a different bundle than the
copy kept, and as a **warning** when it came from the same bundle, which is a fault in
that bundle's data. The step runs with foreign-key checks on, so a row elsewhere that
references a deleted copy stops it rather than being orphaned, and ends by checking that
no OPUS ID has two rows; a failure keeps the invocation from marking the schema ready,
as a validation failure does.

.. _dev_guide_import_steps_table_swap:

Rebuilding a table by swap: opus_import.table_swap
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The three auxiliary tables and the dictionary are rebuilt on a schema the web application
may be serving -- the code-only deploy rebuilds all of them on the live database -- so
none of them is ever dropped and refilled in place. Each step builds its table as
``<table>__new`` in the permanent namespace, fills it while the live table goes on
answering, and swaps it in with one ``RENAME TABLE`` that moves the live table aside to
``<table>__old`` and the new one into its place. MySQL applies the whole statement
atomically, so a reader finds each table as it was or as it now is, never missing and
never partly filled. The ``__old`` table is dropped afterwards.

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

Nothing is written until every column has been read, so a failed build leaves
``param_info__new`` empty rather than half filled -- but the build stops at the **first**
fault, so one run reports only that one. A failed build is not swapped in: the live table
keeps what the previous run wrote. A failed build also keeps the invocation from marking the
schema ready and makes it exit with failure, as a validation failure does
(:ref:`dev_guide_import_steps_do_validate`).

This step must follow the import, because which permanent ``obs_`` tables exist is what
decides which schemas it reads.

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

opus_import.steps.do_validate
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Checks the invariants no database constraint can express. Option: ``--validate-perm``,
which runs it against the permanent namespace. **Nothing here changes the database**:
the tables are already written, and an import that produced them is not undone by a
validation error. Every check runs and logs each failure at error level, so one run
reports them all.

**A failure keeps the schema from being served.** When a check logged an error, the
invocation does not run ``--write-schema-version`` even if it was asked to, logging an
error instead, and exits with failure once its other steps have run, so
``opus_import_all`` stops before its own version step. ``--import-ignore-errors`` on
the same invocation overrides both, for a debugging run; ``opus_import_all`` never passes
it to its finishing steps.

Five checks, in this order:

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
builder stops at the first malformed line. Either way nothing is written and the
permanent tables keep what the previous run wrote. A failed dictionary import is logged,
keeps the invocation from marking the schema ready, and makes it exit with failure, as a
validation failure does (:ref:`dev_guide_import_steps_do_validate`).

.. _dev_guide_import_steps_do_schema_version:

opus_import.steps.do_schema_version
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Marks the permanent schema finished. Option: ``--write-schema-version``, which nothing
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

It is the only writer of ``ready``. ``--finalize``, ``--import-dictionary``
and ``--do-it-all`` leave the row alone, so a schema they finished is not served until
this step runs. ``--drop-permanent-tables --scorched-earth`` drops the table before any
other, so an erase that stops part way leaves no version row behind.
:ref:`dev_guide_database_schema_version` describes the table and who reads it.

The four internal modules
-------------------------

These are the internals of :mod:`~opus_import.steps.do_import`. **They are not steps**:
no command-line option runs one on its own, and nothing outside ``do_import`` calls
them as a unit.

.. _dev_guide_import_steps_do_import_tables:

opus_import.steps.do_import_tables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
    Deletes one bundle across a namespace, every other table before ``obs_general``,
    in chunks: a table's ids for the bundle are read through its ``bundle_id`` key,
    which each of these tables is created with, and each ``[import] transaction_rows``
    of them go in one statement selecting by ``bundle_id`` and a range of the table's
    own ``id``. Each statement is its own transaction, so none holds a whole large
    bundle's undo, and none reads rows outside its range -- which matters on a fresh
    import, whose tables have no other key to find a bundle's rows by until
    finalization.

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
    ``--import-check-duplicate-id`` on the import-tables path. A fresh import never
    reads them: finalization's duplicate step settles a duplicate instead
    (:ref:`dev_guide_import_steps_do_duplicate_ids`).

:func:`~opus_import.steps.do_import_tables.analyze_all_tables`
    Runs the backend's analyze over every ``obs_`` and ``mult_`` table in a namespace,
    for ``--analyze-permanent-tables``, which :mod:`opus_import.cli` runs after the
    auxiliary tables. ``cart`` and the auxiliary tables are not analyzed; each auxiliary
    table is analyzed by its swap.

.. _dev_guide_import_steps_do_import_index:

opus_import.steps.do_import_index
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
returns the id an ``obs_`` column stores,
:func:`~opus_import.steps.do_import_mult.dump_import_mult_tables` writes the modified
tables back, and
:func:`~opus_import.steps.do_import_mult.copy_mult_from_import_to_permanent` copies them
to the permanent namespace.

**Naming.** :func:`~opus_import.import_util.table_name_mult` builds
``mult_<table>_<column>``, both lowercased --
``mult_obs_general_planet_id``. In the import namespace it gains the prefix:
``imp_mult_obs_general_planet_id`` -- except on a fresh import, where the import
namespace names the permanent table itself, so the two namespaces below are one table.

**Caching, and its three lifetimes.** Every table is read once per bundle into the
context's cache and written back at the end of each index file, so importing an index of a
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
when the schema pins none. The rules, in order: a null-ish label sorts to the end,
keyed ``zzz`` for ``NULL``, ``zzy`` for ``N/A`` and ``zzx`` for ``NONE`` -- unless the
column has a unit, in which case those three sort by their own text instead; a column
with a unit sorts by the parsed number, zero-padded; a table whose labels are all
numeric sorts numerically; ``Yes`` sorts before ``No`` and ``On`` before ``Off``;
anything else sorts by its label.

**Writing back.** :func:`~opus_import.steps.do_import_mult.dump_import_mult_tables`
upserts every modified table at the end of each index file.
:func:`~opus_import.steps.do_import_mult.copy_mult_from_import_to_permanent` copies
**all** of them rather than just the ones this run changed, because an earlier run or an
earlier bundle may have changed a table and nothing records that.

API reference
-------------

:doc:`api_opus_import`
