.. _dev_guide_import_overview:

How an Import Works
===================

:mod:`opus_import` reads PDS3 volumes and PDS4 bundles and writes every OPUS table. It
is a program rather than a library: nothing outside the distribution imports it, and it
is run as ``opus_import``, the console script the distribution installs, or equivalently
as ``python -m opus_import``.

This is the *why* of the chapter. It explains what a run does and what forces it to do it
that way; the pages beside it are the *what*.

.. _dev_guide_import_what_it_does:

What a run produces
-------------------

An import run turns the index tables of a set of bundles into the whole OPUS database:

.. mermaid::
    :zoom:

    flowchart TD
        H[(PDS3 and PDS4 holdings:<br/>primary index, summary and<br/>supplemental index files, shelves)]
        BI[config_bundle_info:<br/>which obs class, which index files]
        OB[One obs class instance per bundle]
        OBS[(Observation tables:<br/>obs_*, mult, mult_field, mult_group)]
        REG[(Bundle registry:<br/>import_bundle)]
        AUX[(Auxiliary tables:<br/>param_info, table_names,<br/>partables, contexts, definitions)]
        SUP[(Support tables:<br/>cart, user_searches,<br/>search_results)]

        H --> BI
        BI --> OB
        OB -->|each bundle deleted, then loaded:<br/>a fresh import or an append| OBS
        OB -.->|each bundle's state| REG
        OBS -->|finalization| AUX
        OBS -.-> SUP

Five groups of table come out, and they are produced at different times and with
different guarantees:

**The observation tables** -- ``obs_general``, ``obs_pds``, the per-mission and
per-instrument tables, the geometry tables, ``obs_files``, and the mult tables
(``mult``, ``mult_field`` and ``mult_group``), which hold the enumerated values that go
with them. These are the imported data.

**The auxiliary tables** -- ``param_info``, ``table_names``, ``partables``,
``contexts`` and ``definitions``. These describe the search form rather than the
observations, and only ``param_info`` is really derived from what was imported; the
others come from the checked-in table schemas and configuration maps.
:ref:`dev_guide_database_schema` describes each of them.

**The support tables** -- ``cart``, ``user_searches`` and ``search_results``. The web
application owns their contents; the import only resets them, because an import changes
what a search means.

**The import's own records** -- ``import_bundle``, the bundle registry, which records
each bundle an import takes on and how far it got
(:ref:`dev_guide_import_steps_registry`), and ``schema_version``, whose one row says
which release finished the schema and whether it is ready to serve
(:ref:`dev_guide_database_schema_version`).

**Django's own contrib tables** -- sessions, auth, content types, admin. These come from
``opus_manage migrate``, not from the import. There are no OPUS migrations, because
every OPUS table is created from a table schema by the import itself.

.. _dev_guide_import_write_paths:

The two write paths
-------------------

There is one set of tables, the one the web application reads, and every import writes
into it directly. What differs is the state of the schema it writes into, which chooses
one of two paths; no option chooses (:ref:`dev_guide_import_running_paths`).

**A fresh import** is the path into a schema with no ``schema_version`` row. Such a
schema is not served -- the web application refuses it and both deploy scripts refuse to
promote it -- so there is nothing to protect while it fills. The observation tables are
created with only the keys a load needs, and finalization adds the
rest once, after the last bundle (:ref:`dev_guide_import_steps_create_indexes`), which is
far cheaper than maintaining every index row by row through every load. A failed fresh
import leaves a schema that is still not served until an import finishes it.

**An append** is the path into a schema that holds this release's version row, whether
``ready`` or left ``appending`` by an earlier append: a finished database that bundles
are being added to or replaced in. Its tables keep their indexes, and the bundles load
into them in place. Before the first bundle the append sets the row's state to
``appending``, so a web application that loads the schema refuses it and both deploy
scripts refuse to promote it until ``--write-schema-version`` sets it back to
``ready``. **An append never finalizes the schema itself**: ``--finalize``,
``--validate`` and ``--write-schema-version`` follow as invocations of their own, as
they do after a fresh import. Each finalization step then either does its work again,
because an append invalidates it -- the duplicate step, the mult step, the auxiliary
tables, the cart and search tables, ``ANALYZE`` and validation -- or finds nothing to
do, as ``--create-indexes`` does on tables that already carry every key. A table first
created by an append, because its bundle is the first to need it, is created with only
the keys a load needs and keyed by the ``--finalize`` that follows.

A schema holding another release's version is imported into on neither path: it is
re-imported under the release that will serve it, starting from
``opus_import --scorched-earth --yes``.

**On both paths each bundle is deleted, then loaded.**
:func:`~opus_import.steps.do_import_tables.delete_bundle_from_obs_tables` removes the
bundle's rows from every observation table with foreign key checks on, so ``cart``'s
cascading foreign key removes the cart rows that name them; the bundle is then loaded
with the checks off, and validation's orphan count stands in for them
(:ref:`dev_guide_import_steps_do_validate`). A bundle imported again therefore replaces
its earlier rows rather than adding a second copy, and a failed bundle is repaired by
importing it again.

**The bundle registry keeps an unfinished import from being finished.** Every invocation
that imports bundles records each of them in ``import_bundle`` before the first starts,
and moves each from ``pending`` through ``importing`` to ``done``, or to ``failed`` when
it logged an error. ``--finalize`` refuses to run, and ``--write-schema-version``
refuses to mark the schema ready, while any bundle there is not ``done``. An append
resumes every bundle an earlier append left unfinished before the ones it names.
:ref:`dev_guide_import_steps_registry` gives the rules.

The other tables are not the import's to protect. Finalization's cart and search-table
steps drop and recreate ``cart``, ``user_searches`` and ``search_results`` empty, and
flush the web application's cache, because an import changes what a search means; ``--scorched-earth`` drops every table the
import creates before anything else runs.

On either path a run can be **resumed rather than restarted**: the bundles already
written stay, the registry names the ones that did not finish, and the per-step options
let a second invocation redo only the part that failed.

.. _dev_guide_import_context:

The run's state lives in one object
-----------------------------------

:class:`opus_import.context.ImportContext` carries everything one run shares between its
layers. Exactly one is built, by :func:`opus_import.cli.main`, and passed by hand from
there down: ``cli`` hands it to each step, the steps hand it to each other, and the obs
classes keep it as their ``_ctx``. **Nothing in the pipeline reaches for pipeline state
any other way.** The one step module with a module-level global is
:mod:`~opus_import.steps.do_import_pool`, which installs the context and the index's
state there for the length of one index, because a module global is what a forked worker
inherits without anything being pickled; each worker then works on its own copy of the
context, with no database and a :attr:`~opus_import.context.ImportContext.capture` in
place of one (:ref:`dev_guide_import_steps_do_import_pool`).

Its fields fall into three groups:

**What the run was given** -- the parsed arguments, the logger, the open database, and
the resolved worker counts (:attr:`~opus_import.context.ImportContext.workers`,
:attr:`~opus_import.context.ImportContext.worker_rows` and
:attr:`~opus_import.context.ImportContext.index_workers`), which :mod:`opus_import.cli`
sets once it has checked them against the ceiling
(:ref:`dev_guide_import_running_parallelism`).

**Where the run currently is** -- the bundle, the 1-based index row number, and the
primary file specification. These are what
:class:`~opus_import.context.ImportLog` puts in front of every message, so a line read
out of a log names the observation that produced it. The file specification is None at
the top of each row and is filled in as soon as it has been computed.

**What the run has accumulated** -- the caches described in
:ref:`dev_guide_import_ids` and :ref:`dev_guide_import_steps_do_import_mult`, the
records of which non-repeating messages have already been logged, the Python warnings
collected since they were last reported, the wall-clock of each step timed so far
(:attr:`~opus_import.context.ImportContext.step_timings`, which ``--timing-json``
writes), and :attr:`~opus_import.context.ImportContext.import_has_bad_data`.

Four of those are reset **per bundle**, and treating one as per run is a real bug:
:attr:`~opus_import.context.ImportContext.max_table_id_cache`,
:attr:`~opus_import.context.ImportContext.mult_table_cache`,
:attr:`~opus_import.context.ImportContext.modified_mult_tables` and
:attr:`~opus_import.context.ImportContext.bundle_has_errors`, which says whether the
bundle being imported has logged an error, beside
:attr:`~opus_import.context.ImportContext.import_has_bad_data`, which says it for the
whole run.

Logging goes through :attr:`~opus_import.context.ImportContext.log`, an
:class:`~opus_import.context.ImportLog` bound to the context. Its methods are the four
levels :meth:`~opus_import.context.ImportLog.error`,
:meth:`~opus_import.context.ImportLog.warning`,
:meth:`~opus_import.context.ImportLog.info` and
:meth:`~opus_import.context.ImportLog.debug`; the two
:meth:`~opus_import.context.ImportLog.nonrepeating_error` and
:meth:`~opus_import.context.ImportLog.nonrepeating_warning` variants; and
:meth:`~opus_import.context.ImportLog.unknown_target_name`, which reports a target the
configuration does not describe and names the file to edit. The step modules reach the
same operations through the ``log_*`` functions in :mod:`opus_import.import_util`, which
take the context as their first argument; both spellings are one implementation. While
the context has a :attr:`~opus_import.context.ImportContext.capture`, in a pool worker,
every one of them records the call and the position instead of logging it, deduplicating
and marking nothing, and the import's process makes the call when it replays the worker's
task.

.. _dev_guide_import_pass_structure:

The pass structure of a run
---------------------------

A run is a sequence of steps, each a ``do_*`` module under :mod:`opus_import.steps`.
The command line asks for the ones it wants and :mod:`opus_import.cli` runs the
requested subset **in a fixed order**. The order is not a preference; each part of it is
forced by something:

1. **Erase or delete**, inside :mod:`~opus_import.steps.do_import`:
   ``--scorched-earth`` drops every table the import creates, before anything else, so
   that no ``mult`` row survives and the ids start again; ``--delete-bundles``
   then deletes the named bundles.
2. **Import the observations** (:mod:`~opus_import.steps.do_import`). This is the long
   part.
3. **Add the secondary keys** (:mod:`~opus_import.steps.do_indexes`) a fresh import
   left out, foreign keys last, then **keep one copy of each OPUS ID**
   (:mod:`~opus_import.steps.do_duplicate_ids`), which finds and deletes the copies
   through those keys. ``--finalize`` refuses before this point, changing nothing,
   while any bundle in the bundle registry is not ``done``.
4. **Finalize the mult fields** (:mod:`~opus_import.steps.do_finalize_mult`): delete the
   values no observation holds, apply the schemas' ``mult_overrides``, and rank every
   field's values and groups. The duplicate step's deletions can leave a value unused,
   and ``partables`` reads the ``mult`` rows, so it comes between them.
5. **Build the auxiliary tables** (:mod:`~opus_import.steps.do_param_info`,
   :mod:`~opus_import.steps.do_partables`,
   :mod:`~opus_import.steps.do_table_names`), **recreate the cart and drop the cache
   tables** (:mod:`~opus_import.steps.do_cart`, :mod:`~opus_import.steps.do_django`),
   then analyze the tables. Each auxiliary table is derived from the imported tables --
   from which of them exist, and from their schemas -- and ``cart`` carries a foreign
   key onto ``obs_general``, so all of them must follow the import.
6. **Write the mult presentation from the schemas**
   (:mod:`~opus_import.steps.do_update_mult_info`) and **validate**
   (:mod:`~opus_import.steps.do_validate`).
7. **Load the data dictionary** (:mod:`~opus_import.steps.do_dictionary`).
8. **Mark the schema ready** (:mod:`~opus_import.steps.do_schema_version`), last,
   because its row is what makes the schema servable.

:mod:`opus_import.steps` states the whole order and what forces each part of it, and is
the authority if this summary and it ever disagree.

.. _dev_guide_import_per_bundle:

Inside one bundle
-----------------

:func:`~opus_import.steps.do_import.import_one_bundle` is the per-bundle driver. Given a
bundle id it:

1. **Looks the bundle up** in ``BUNDLE_INFO``
   (:mod:`opus_import.config_bundle_info`). An entry whose ``instrument_class`` is None
   names a bundle OPUS knows about and deliberately ignores
   (:func:`~opus_import.steps.do_import_tables.opus_imports_bundle` is False), which
   counts as success; such a bundle is never recorded in the bundle registry. A bundle
   id matching no entry is one OPUS does not know, and is an error.
2. **Resolves it to a ``pdsfile`` object** -- ``Pds3File.from_path`` or
   ``Pds4File.from_path`` -- and requires it to be a bundle.
3. **Finds the primary index files.** ``BUNDLE_INFO`` gives one or more file-name
   patterns with ``<BUNDLE>`` standing for the bundle id. The search looks through the
   bundle's ``metadata`` directories and, for PDS3, the volume's own ``INDEX`` and
   ``index`` directories. **Every index in the first directory that has one is
   imported, and no later directory is searched**, so a bundle whose indexes are split
   across directories imports only the first group.
4. **Imports each index** through
   :func:`~opus_import.steps.do_import_index.import_one_index`.

The directory listing is **sorted** before the file names are matched, and that is a
correctness requirement rather than tidiness: a bundle can have several primary indexes -- COCIRS_1xxx
has one per cube geometry -- and row ids are handed out in insertion order. Taking the
files in :func:`os.listdir` order would make every id in the database depend on how one
filesystem happened to enumerate one directory, so two imports of identical holdings on
two machines would disagree about every id.

.. _dev_guide_import_one_index:

Inside one index file
---------------------

:func:`~opus_import.steps.do_import_index.import_one_index` is where a holdings tree
becomes rows. It has two halves.

**The first half assembles the metadata.** It reads the primary index with ``pdstable``,
then *discovers* the files beside it, as described in
:ref:`dev_guide_holdings_opus_consumes`, and cross-references each one to the primary
index on the primary file specification. Ring, sky and inventory summaries have at most
one row per observation and become a dictionary keyed by file specification; a surface
geometry summary has one row per target per observation and becomes a dictionary of
dictionaries, keyed by file specification and then by target name. Both the rows and the
files' own labels are kept, because different instruments record useful values in each.

An empty associated index is reported as an **error** rather than passed over: it reads
as a successful read of a file with no rows, so without the check the whole bundle would
import silently short of that metadata.

Two bundle-level flags shape this half. ``validate_index_rows`` handles archives whose
index carries more than one row per observation: the OPUS id of every row is computed
(cheap), rows sharing an id are collected, and only for those is the id mapped back to a
file specification (expensive) to decide which row to keep. The rest are dropped with a
log line. ``temporal_camera`` is passed straight through onto the metadata for the obs
classes to read.

**The second half computes the rows.** For each index row, and for each *phase* of that
row, every table the observation belongs to gets one row computed by
:func:`~opus_import.steps.do_import_obs.import_observation_table`, through the one row
function :func:`~opus_import.steps.do_import_index.import_index_row`. Each row starts
from the metadata as it stood before the first row, so a row's result depends on that row
alone. Three things are deferred, in this order:

* the ``obs_surface_geometry__<TARGET>`` tables, because which of them exist depends on
  the targets the observations turn out to mention;
* ``obs_surface_geometry`` itself, because its target list is only known once those have
  been walked;
* ``obs_files``, because it needs the ``obs_general`` and ``obs_pds`` rows and
  contributes many rows per observation rather than one.

**The rows are computed by one process or by many, and written by one.** With
``[import] workers`` above 1, a pool of forked workers computes ranges of rows and records
every database call and log write instead of making it; the import's own process replays
each range's events in index order, where the serial loop would have made them, so the
tables, their ids and the log are the same whatever the number of workers
(:ref:`dev_guide_import_steps_do_import_pool`).

**Each finished row goes to a sink** that loads a table's rows as soon as
``[import] transaction_rows`` of them are waiting, so an index is never held in memory
whole. Once every row has been computed, the ``mult`` rows the index added go out, and
then the ``obs_`` rows still waiting, table by table in order with ``obs_general`` first.
An ``obs_`` row stores the id its value was given in the column's mult field, and a table
that filled a transaction during the index was loaded before the ``mult`` rows were
written; nothing enforces the order, because a ``mult_idx`` column carries no foreign
key, and the bundle loads with foreign key checks off.

Where the surface geometry comes from varies. Most bundles have separate summary files
per target. Some -- COCIRS_[01]xxx among them -- carry it inline in the primary index
instead, and their obs class returns the target names from
:meth:`~opus_import.obs.obs_base.ObsBase.surface_geo_target_list` so that the same
tables are filled from the index row.

.. _dev_guide_import_one_row:

Inside one row
--------------

:func:`~opus_import.steps.do_import_obs.import_observation_table` computes one
observation's row of one table by walking that table's schema and producing one value
per column. Three kinds of entry are skipped outright: ``timestamp``, which the
database maintains itself; a column marked ``put_mults_here``, which holds another
column's mult id; and an entry with no ``field_name`` -- a ``pi_referred_slug`` entry,
which describes a search parameter rather than a column, or a table-level key.

For every other column it dispatches on the schema's ``data_source``:

.. list-table::
   :header-rows: 1

   * - ``data_source``
     - Where the value comes from
   * - ``COMPUTE``
     - The obs instance's ``field_obs_<table>_<column>`` method. This is almost every
       column.
   * - ``OBS_GENERAL_ID``
     - The ``id`` of this observation's ``obs_general`` row, which is how every other
       table hangs off it.
   * - ``MAX_ID``
     - One more than the largest id used in this table so far, from the run's
       per-table id cache.
   * - ``LONGITUDE_FIELD``
     - :meth:`~opus_import.obs.obs_base.ObsBase.compute_longitude_field`.
   * - ``D_LONGITUDE_FIELD``
     - :meth:`~opus_import.obs.obs_base.ObsBase.compute_d_longitude_field`.

The method name is produced by
:func:`~opus_import.steps.do_import_obs.field_function_name`, and that is the pipeline's
**only** rule for finding a field method: ``field_`` plus the table name plus the column
name, with every ``obs_surface_geometry__<TARGET>`` table folded onto
``obs_surface_geometry_target`` because they are all built from one template. A method
whose name that rule cannot produce is a method that is never called.

The computed value is then checked against what the schema declares, and **validation
reports rather than raises**, so one bad row does not end the run:

* a flag column's value is folded onto ``Yes``/``No`` or ``On``/``Off``; ``N/A``,
  ``UNK`` and ``NULL`` become NULL quietly, and any other unrecognized spelling becomes
  NULL and logs an error;
* a ``charNNN`` column keeps a value of the right type -- an over-long string is
  truncated, a non-string becomes the empty string -- and logs an error either way;
* a numeric column's value must parse, must not equal a ``val_sentinel``, and must lie
  between ``val_min`` and ``val_max``. It becomes NULL if it does not. A column carrying
  ``val_set_invalid_to_null`` logs an out-of-range value at **debug** level instead of
  as an error, so those are discarded silently and the run still succeeds.

Logging an error is what marks the run, and the bundle, as having produced bad data:
the bundle is recorded ``failed`` in the bundle registry, which keeps finalization and
the version step from running until it is imported again or deleted.

Finally, a column whose ``pi_form_type`` is a GROUP type has its value replaced by the
id of a ``mult`` row of its field, adding the value to the field if the field lacks it.
A ``mult_list`` column holds several values and is written as a JSON array, with a missing
value omitted rather than stored as null.

Each computed row is left on the metadata dictionary under ``<table_name>_row`` as well
as returned, which is how a later table's field methods read what an earlier one
computed. :func:`~opus_import.steps.do_import_obs.import_observation_table` installs the
dictionary there **before** computing into it, so a field method can also read what an
earlier column of its own table produced.

**A field method's exception costs one field, not the run.**
:func:`~opus_import.steps.do_import_obs.import_run_field_function` catches it, logs it
with its traceback, and returns None for that column. What makes that containment safe
is that an obs class can log but cannot reach the database; see
:ref:`dev_guide_import_obs_base`.

.. _dev_guide_import_ids:

Row ids and mult ids
--------------------

Two kinds of surrogate integer hold the database together, and neither is assigned by the
database server.

**The row id.** ``obs_general`` numbers its rows in an ``id`` column, and every other
``obs_`` table has an ``obs_general_id`` naming the row this one hangs off. In most of
them that is the whole primary key, since such a table holds at most one row per
observation; ``obs_files`` adds ``file_number``, the file's position among its
observation's files; and the surface geometry name table, which holds one row per
observation and body, and the per-target tables number their rows in an ``id`` of their
own. The pipeline
assigns them all: a ``MAX_ID`` column gets one more than the largest id used in that
table so far, an ``OBS_GENERAL_ID`` column gets the id of the ``obs_general`` row this
observation already produced, and ``file_number`` counts from 1 in the order the files
are written.

The "largest so far" comes from :func:`~opus_import.import_util.find_max_table_id`, the
largest id the table holds. Each bundle is deleted before it is written, so its new rows
are numbered above every row that remains: a bundle imported again into a finished
schema is renumbered above the rest of the table, which is a documented consequence
rather than an accident, and one whose rows were the highest in the table can take the
ids its earlier rows had.

The run keeps the running maximum in
:attr:`~opus_import.context.ImportContext.max_table_id_cache` rather than querying for
each row, and clears it per bundle. **Ids therefore depend on the order rows are
produced in**, which is why the pipeline sorts every directory listing and every table
name it iterates. A pool worker cannot know the running maximum, so it numbers its ids
from zero per table within its task, and the import's process rebases them onto the
maximum as it replays the tasks in index order; the ids are the ones the serial loop
gives.

**The mult id.** A column whose value comes from a fixed set stores the id of a ``mult``
row rather than the value itself. The column's values form one mult field, named
``<table>.<column>`` unless the column's schema gives a ``mult_field`` key, and every
``mult`` row of the field carries the field's ``field_id`` from ``mult_field``. Ids are
numbered within a field: they start at zero, and a value not already there is given one
more than the field's current maximum -- unless the column's schema pins its values with
``mult_options``, in which case the ids are the ones listed and a value that is not
among them is an error. A stored row keeps its id and its value, so renaming a value
rewrites no observation row. A deleted row's id is free again: after finalization deletes
a value no observation holds, a value added later can take its id.

The field ids are numbered once in each database, over every mult field of the packaged
``obs_*.json`` schemas in order of qualified name, and a field a later release adds takes
the next id (:mod:`opus_import.mult_fields`).

Nothing enforces the reference: a ``mult_idx`` column carries **no foreign key**, so a
table's rows can be loaded before the ``mult`` rows they name are written, which happens
at the end of each index. A pool worker cannot know a value's id
either; it records the value, and the import's process resolves each one in the order
the serial loop meets them, so every value gets the id the serial loop gives it.

A ``mult_list`` column -- one an observation can have several values of -- stores a JSON
array of those ids instead, with missing values omitted rather than stored as null.

:ref:`dev_guide_import_steps_do_import_mult` describes the caching,
:ref:`dev_guide_import_steps_do_finalize_mult` the order the values are listed in, and
:ref:`dev_guide_database_schema_mult` what the tables look like.

.. _dev_guide_import_obs_dispatch:

Why there is a class hierarchy
------------------------------

One obs class instance is created per bundle, and every ``COMPUTE`` column of every
table is a method call on it. The hierarchy exists entirely to decide which class that
call lands on, so that an archive that spells something unusually overrides one method
and inherits the several hundred it agrees with.

The layering, root outward, is: what every observation shares, then what a PDS version
decides, then what one OPUS table needs, then what a mission shares, then what one
volume set or bundle knows. :ref:`dev_guide_import_obs` describes each layer, the
contract it defines, and the method resolution order that falls out.

.. _dev_guide_import_invariants:

Invariants
----------

* **Nothing is served until it is finished.** A fresh import writes a schema with no
  version row, and an append, or ``--delete-bundles`` on a finished schema, sets the row
  to ``appending`` before its first write; a web application that loads either, and both
  deploy scripts, refuse it until ``--write-schema-version`` marks it ``ready``, which it
  refuses to do while any bundle in the bundle registry is not ``done``. A step that
  wrote a finished schema before setting it ``appending`` would break the guarantee the
  design rests on. A web application already serving a schema does not check it again,
  so appends and deletions go to a schema nothing is serving.
* **Every mult id an** ``obs_`` **row holds names a** ``mult`` **row of its field by
  the end of the index.** The ``mult`` rows an index adds are written once every row has
  been computed, before the rows still waiting are loaded, and finalization deletes only
  the values no observation holds. No database constraint enforces it.
* **A stored** ``mult`` **row keeps its id and its value.** Neither the import,
  ``--update-mult-info`` nor finalization rewrites the id or the value of a row it
  holds: a new value is inserted, never written over another row, and a list entry that
  disagrees with a stored row is an error. Renaming a value or reordering a field
  touches no observation row. A row finalization deletes frees its id for a later
  value.
* **An import computes in many processes and writes from one.** Only the import's own
  process uses the database and writes the log; pool workers compute rows and record
  what they would have written, and that process replays it in index order, so the
  result does not depend on how many workers there are
  (:ref:`dev_guide_import_steps_do_import_pool`).
* **A row's result depends on that row alone.** One obs instance serves a whole bundle,
  and its metadata dictionary is cleared and refilled from the index's pre-loop metadata
  at the start of every row -- so **no obs method may cache anything derived from it**,
  since a cache carried from one row to the next would make a row's result depend on
  which rows the same process computed before it.
  :ref:`dev_guide_import_obs_base` gives the one pattern that is allowed.
* **Row ids depend on insertion order**, so anything that changes the order rows are
  produced in changes every id. Directory listings are sorted for exactly this reason.
* **Longitudes carry two derived columns.** A ``LONG`` field stores, besides its minimum
  and maximum, the midpoint and the half-span of the range, because a longitude search
  has to handle the wrap at 360 degrees.
* **Units are the schema's business, not the field method's.** A field method returns a
  value in the column's default unit; :mod:`opus_support` is what converts to and from
  everything else, driven by the ``pi_form_type`` the schema declares.
* **The primary file specification must come from the primary index.** It is what
  finds an observation's row in every other index file and what the OPUS ID is derived
  from, so an obs class that took it from a supplemental index could not do either. Many
  of the classes say so in capitals, and no override breaks it.

.. _dev_guide_import_errors:

Errors and warnings
-------------------

A run reports through :class:`opus_import.context.ImportLog`, reached as ``ctx.log``,
and the step modules call the same operations through the ``log_*`` functions in
:mod:`opus_import.import_util`; :ref:`dev_guide_import_context` describes both and the
position prefix every message carries.

**What ends up in the error log is what gates an automated import.** The exit status is
not the whole story: :mod:`~opus_import.steps.do_validate` reports through the log
rather than through the status, so a script that only checks the status will pass a run
that found problems. Gate on ``ERRORS.log`` being empty.

The ``nonrepeating_`` variants log a given message once per run and ignore it after
that. They exist because a single systematic fault -- one column missing from one
index -- would otherwise be reported once per observation, hundreds of thousands of
times.

:attr:`~opus_import.context.ImportContext.import_has_bad_data` is the flag that makes
an import exit with failure, unless ``--ignore-errors``, and
:attr:`~opus_import.context.ImportContext.bundle_has_errors`, set with it and reset at
the start of each bundle, is what records the bundle ``failed`` in the bundle registry.
Every ``log`` error sets both, through
:meth:`~opus_import.context.ImportContext.mark_bad_data`, and a few sites set them
through it directly; they are **not** a complete record of the run's errors, because
several steps log failures straight to the underlying logger and leave them alone.

Where to go next
----------------

:ref:`dev_guide_import_running`
    Every command-line option, what a run prints, and how to verify one succeeded.

:ref:`dev_guide_import_config`
    ``BUNDLE_INFO``, the mission and instrument maps, and the target tables.

:ref:`dev_guide_import_steps`
    Every ``do_*`` module.

:ref:`dev_guide_import_obs`
    The obs class hierarchy and its contracts.

:ref:`dev_guide_import_db`
    The database layer and the shared helpers.

:ref:`dev_guide_import_extending`
    Recipes for adding a column, a bundle, an instrument or a mission.

API reference
-------------

:doc:`api_opus_import`
