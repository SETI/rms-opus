.. _dev_guide_import:

The Import Pipeline: Theory of Operation
========================================

:mod:`opus_import` reads PDS3 volumes and PDS4 bundles and writes every OPUS table. It
is a program rather than a library: nothing outside the distribution imports it, and it
is run as ``opus_import``, the console script the distribution installs, or equivalently
as ``python -m opus_import``.

This chapter is the *why*. It explains what a run does and what forces it to do it that
way. The chapters after it are the *what*: :ref:`dev_guide_import_running` is the
command-line surface, :ref:`dev_guide_import_config` is the data that says what exists,
:ref:`dev_guide_import_steps` walks every step module, :ref:`dev_guide_import_obs` and
:ref:`dev_guide_import_obs_classes` walk the class hierarchy that computes the values,
and :ref:`dev_guide_import_db` is the SQL layer underneath.

.. _dev_guide_import_what_it_does:

What a run produces
-------------------

An import run turns the index tables of a set of bundles into the whole OPUS database:

.. mermaid::

    flowchart TD
        H[(PDS3 and PDS4 holdings:<br/>primary index, summary and<br/>supplemental index files, shelves)]
        BI[config_bundle_info:<br/>which obs class, which index files]
        OB[One obs class instance per bundle]
        IMP[(Import tables:<br/>imp_obs_*, imp_mult_*)]
        PERM[(Permanent tables:<br/>obs_*, mult_*)]
        AUX[(Auxiliary tables:<br/>param_info, table_names,<br/>partables, contexts, definitions)]
        SUP[(Support tables:<br/>cart, user_searches)]

        H --> BI
        BI --> OB
        OB --> IMP
        IMP -->|only if the whole run succeeded| PERM
        PERM --> AUX
        PERM -.-> SUP

Four groups of table come out, and they are produced at different times and with
different guarantees:

**The observation tables** -- ``obs_general``, ``obs_pds``, the per-mission and
per-instrument tables, the geometry tables, ``obs_files``, and the ``mult_`` tables of
enumerated values that go with them. These are the imported data.

**The auxiliary tables** -- ``param_info``, ``table_names``, ``partables``,
``contexts`` and ``definitions``. These describe the search form rather than the
observations, and only ``param_info`` is really derived from what was imported; the
others come from the checked-in table schemas and configuration maps.
:ref:`dev_guide_database` describes each of them.

**The support tables** -- ``cart``, ``user_searches`` and the ``cache_*`` tables. The
web application owns their contents; the import only resets them, because an import
changes what a search means.

**Django's own contrib tables** -- sessions, auth, content types, admin. These come from
``django-admin migrate``, not from the import. There are no OPUS migrations, because
every OPUS table is created from a table schema by the import itself.

.. _dev_guide_import_two_namespaces:

The two namespaces
------------------

Every imported table exists twice. The **import namespace** carries the prefix the
configuration's ``table_temp_prefix`` names (``imp_`` by default), and the **permanent
namespace** carries no prefix and is what the web application reads.
:meth:`~opus_import.importdb.super.ImportDBSuper.convert_raw_to_namespace` is what turns
a bare table name into one or the other, and no step module builds a prefixed name
itself.

A run writes only the import tables. It copies them over the permanent tables at the
very end, and **only if nothing logged an error**
(:func:`~opus_import.steps.do_import.do_import_steps` skips the copy otherwise, unless
``--import-ignore-errors`` says to go ahead). This is the guarantee the whole design
rests on: a failed import cannot leave the web application serving half a bundle of
observation metadata.

The protection covers the imported tables and no others. ``cart`` is created directly in
the permanent namespace, and the ``cache_*`` and ``user_searches`` tables are dropped
there outright, so a failed run can leave those already reset. They hold no imported
data, which is why they are outside the copy.

Because the import tables survive a failure, a run can be **resumed rather than
restarted**: the per-step options let a second invocation redo only the part that
failed.

.. _dev_guide_import_context:

The run's state lives in one object
-----------------------------------

:class:`opus_import.context.ImportContext` carries everything one run shares between its
layers. Exactly one is built, by :func:`opus_import.cli.main`, and passed by hand from
there down: ``cli`` hands it to each step, the steps hand it to each other, and the obs
classes keep it as their ``_ctx``. **Nothing in the pipeline reaches for pipeline state
any other way**, and no step module has a module-level global.

Its fields fall into three groups:

**What the run was given** -- the parsed arguments, the logger, and the open database.

**Where the run currently is** -- the bundle, the 1-based index row number, and the
primary file specification. These are what
:class:`~opus_import.context.ImportLog` puts in front of every message, so a line read
out of a log names the observation that produced it. The file specification is None at
the top of each row and is filled in as soon as it has been computed.

**What the run has accumulated** -- the caches described in
:ref:`dev_guide_import_ids` and :ref:`dev_guide_import_steps_do_import_mult`, the
records of which non-repeating messages have already been logged, the Python warnings
collected since they were last reported, and
:attr:`~opus_import.context.ImportContext.import_has_bad_data`.

Three of those have different lifetimes, and mixing them up is a real bug:
:attr:`~opus_import.context.ImportContext.max_table_id_cache`,
:attr:`~opus_import.context.ImportContext.mult_table_cache` and
:attr:`~opus_import.context.ImportContext.modified_mult_tables` are cleared **per
bundle**, while
:attr:`~opus_import.context.ImportContext.created_import_mult_tables` is cleared **per
run**.

Logging goes through :attr:`~opus_import.context.ImportContext.log`, an
:class:`~opus_import.context.ImportLog` bound to the context. It has seven methods: the
four levels :meth:`~opus_import.context.ImportLog.error`,
:meth:`~opus_import.context.ImportLog.warning`,
:meth:`~opus_import.context.ImportLog.info` and
:meth:`~opus_import.context.ImportLog.debug`; the two
:meth:`~opus_import.context.ImportLog.nonrepeating_error` and
:meth:`~opus_import.context.ImportLog.nonrepeating_warning` variants; and
:meth:`~opus_import.context.ImportLog.unknown_target_name`, which reports a target the
configuration does not describe and names the file to edit. The step modules reach the
same operations through the ``log_*`` functions in :mod:`opus_import.import_util`, which
take the context as their first argument; both spellings are one implementation.

.. _dev_guide_import_pass_structure:

The pass structure of a run
---------------------------

A run is a sequence of steps, each a ``do_*`` module under :mod:`opus_import.steps`.
The command line asks for the ones it wants and :mod:`opus_import.cli` runs the
requested subset **in a fixed order**. The order is not a preference; each part of it is
forced by something:

1. **Clean up the cart and cache tables** (:mod:`~opus_import.steps.do_cart`,
   :mod:`~opus_import.steps.do_django`). A ``cart`` row can reference an observation, so
   the cart has to be emptied before the permanent tables are rebuilt underneath it.
2. **Import the observations** (:mod:`~opus_import.steps.do_import`). This is the long
   part, and it owns the copy to the permanent namespace as well.
3. **Build the auxiliary tables** (:mod:`~opus_import.steps.do_param_info`,
   :mod:`~opus_import.steps.do_partables`,
   :mod:`~opus_import.steps.do_table_names`). Each of these is derived from the
   permanent tables -- from which of them exist, and from their schemas -- so it must
   follow the copy.
4. **Pin the mult display details** (:mod:`~opus_import.steps.do_update_mult_info`),
   **validate** (:mod:`~opus_import.steps.do_validate`), and retry the cart if creating
   it earlier failed because the permanent tables did not exist yet.
5. **Load the data dictionary** (:mod:`~opus_import.steps.do_dictionary`), last.

``--drop-permanent-tables`` reorders the first part: the leading cleanup is skipped and
:mod:`~opus_import.steps.do_import` performs it instead, after the drop, because
dropping the permanent tables also drops the cart.

:mod:`opus_import.steps` states the whole order and what forces each part of it, and is
the authority if this summary and it ever disagree.

.. _dev_guide_import_per_bundle:

Inside one bundle
-----------------

:func:`~opus_import.steps.do_import.import_one_bundle` is the per-bundle driver. Given a
bundle id it:

1. **Looks the bundle up** in ``BUNDLE_INFO``
   (:mod:`opus_import.config_bundle_info`). A bundle id matching no entry is one OPUS
   does not know, and is an error. An entry whose ``instrument_class`` is None names a
   bundle OPUS knows about and deliberately ignores, which counts as success.
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

The directory listing is **sorted** before the file names are matched, and that is
load-bearing rather than tidy: a bundle can have several primary indexes -- COCIRS_1xxx
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

**The second half is the master loop.** For each index row, and for each *phase* of that
row, every table the observation belongs to gets one row computed by
:func:`~opus_import.steps.do_import_obs.import_observation_table`. Three things are
deferred, in this order:

* the ``obs_surface_geometry__<TARGET>`` tables, because which of them exist depends on
  the targets the observations turn out to mention;
* ``obs_surface_geometry`` itself, because its target list is only known once those have
  been walked;
* ``obs_files``, because it needs the ``obs_general`` and ``obs_pds`` rows and
  contributes many rows per observation rather than one.

**Nothing is written to the database until every row of the index has been computed.**
Then the ``mult_`` tables go out, and only then the ``obs_`` tables -- because an
``obs_`` row stores the row id its value was given in the corresponding ``mult_`` table,
and that row has to exist to be looked up. Nothing enforces the order: a ``mult_idx``
column carries a plain index, not a foreign key. Within the ``obs_`` tables,
``obs_general`` goes first, and *that* one really is a foreign-key target for the rest.

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
per column. Three kinds of column are skipped outright: ``timestamp``, which the
database maintains itself; a column marked ``put_mults_here``, which holds another
column's mult id; and a ``pi_referred_slug`` entry, which describes a search parameter
rather than a column.

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

Logging an error is what marks the run as having produced bad data, and that is what
suppresses the copy to the permanent tables at the end.

Finally, a column whose ``pi_form_type`` is a GROUP type has its value replaced by a
``mult_`` table row id, adding the value to that table if it is new. A ``mult_list``
column holds several values and is written as a JSON array, with a missing value omitted
rather than stored as null.

Each computed row is left on the metadata dictionary under ``<table_name>_row`` as well
as returned -- the master loop in
:func:`~opus_import.steps.do_import_index.import_one_index` does it -- which is how a
later table's field methods read what an earlier one computed.

**A field method's exception costs one field, not the run.**
:func:`~opus_import.steps.do_import_obs.import_run_field_function` catches it, logs it
with its traceback, and returns None for that column. An obs class is handed the run
context only so that it can log, never so that it can reach the database -- which is
what makes that containment safe.

.. _dev_guide_import_ids:

Row ids and mult ids
--------------------

Two kinds of surrogate integer hold the database together, and neither is assigned by the
database server.

**The row id.** Every ``obs_`` table has an ``id`` column, and every table but
``obs_general`` also has an ``obs_general_id`` naming the row this one hangs off. The
pipeline assigns both: a ``MAX_ID`` column gets one more than the largest id used in that
table so far, and an ``OBS_GENERAL_ID`` column gets the id of the ``obs_general`` row this
observation already produced.

The "largest so far" comes from :func:`~opus_import.import_util.find_max_table_id`, which
takes the larger of the two namespaces' maxima. That is what makes a **re-import** of one
bundle safe: its new rows are numbered above everything already present in either
namespace, and its old rows are deleted only afterwards. It is also why a re-import
renumbers that bundle above the rest of the table, which is a documented consequence
rather than an accident.

The run keeps the running maximum in
:attr:`~opus_import.context.ImportContext.max_table_id_cache` rather than querying for
each row, and clears it per bundle. **Ids therefore depend on the order rows are
produced in**, which is why the pipeline sorts every directory listing and every table
name it iterates.

**The mult id.** A column whose value comes from a fixed set stores an integer index into
that column's ``mult_`` table rather than the value itself. The table is
``mult_<table>_<column>``, its ids start at zero, and a value not already there is given
one more than the current maximum -- unless the column's schema pins its values with
``mult_options``, in which case a value that is not among them is an error.

Nothing enforces the reference: a ``mult_idx`` column carries a plain index and **no
foreign key**. That is why the write order matters, and why the mult tables go out before
the ``obs_`` tables.

A ``mult_list`` column -- one an observation can have several values of -- stores a JSON
array of those ids instead, with missing values omitted rather than stored as null.

:ref:`dev_guide_import_steps_do_import_mult` describes the caching and the derived sort
order, and :ref:`dev_guide_database` describes what the tables look like.

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
contract it defines, and the method resolution order that falls out -- which is not
obvious, and is the usual way a newly added class misbehaves.

.. _dev_guide_import_invariants:

Invariants
----------

* **Nothing is visible until the run succeeds.** Every imported table is written under
  the import prefix and copied over the permanent tables at the end. Deleting the import
  tables before the copy, or copying before every bundle has been read, breaks the
  guarantee the design rests on.
* **The** ``mult_`` **tables go out before the** ``obs_`` **tables.** No database
  constraint enforces it.
* **An import run is single-threaded, and one obs instance serves a whole bundle.** The
  instance holds the current row's metadata, and
  :func:`~opus_import.steps.do_import_index.import_one_index` replaces that dictionary
  in place once per row, so **no obs method may cache anything derived from it**.
  :attr:`~opus_import.obs.obs_base.ObsBase.opus_id` shows the pattern that is allowed:
  it re-derives whenever the file specification it was computed from changes.
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
  from, so an obs class that took it from a supplemental index could not do either. Two
  of the leaf classes say so in capitals, and none of the thirteen overrides breaks it.

.. _dev_guide_import_errors:

Errors and warnings
-------------------

A run reports through :class:`opus_import.context.ImportLog`, reached as ``ctx.log``,
and the step modules call the same operations through the ``log_*`` functions in
:mod:`opus_import.import_util`. Every message is prefixed with the bundle, index row and
primary file specification the run is currently on, so a message read out of a log file
names the observation that produced it.

**What ends up in the error log is what gates an automated import.** The exit status is
not the whole story: :mod:`~opus_import.steps.do_validate` reports through the log
rather than through the status, so a script that only checks the status will pass a run
that found problems. Gate on ``ERRORS.log`` being empty.

The ``nonrepeating_`` variants log a given message once per run and ignore it after
that. They exist because a single systematic fault -- one column missing from one
index -- would otherwise be reported once per observation, hundreds of thousands of
times.

:attr:`~opus_import.context.ImportContext.import_has_bad_data` is the flag that
suppresses the copy to the permanent tables. Every ``log`` error sets it, and a few
sites set it directly; it is **not** a complete record of the run's errors, because
several steps log failures straight to the underlying logger and leave it alone.

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
