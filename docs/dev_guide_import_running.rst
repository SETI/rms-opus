.. _dev_guide_import_running:

Running the Import Pipeline
===========================

The pipeline is one program with one command line. This chapter is the complete
surface: what to set in the environment, every option, what a run prints, how to tell
whether it worked, and what a small run and a full-holdings run each look like.

:ref:`dev_guide_import_overview` is the theory this chapter assumes.

Invoking it
-----------

The distribution installs a console script, and the package has a ``__main__``. The two
reach the same :func:`opus_import.cli.main`::

    opus_import --help
    python -m opus_import --help

``--help`` works with no configuration file, because :func:`~opus_import.cli.main` does
not read one until the arguments have parsed. Everything else needs one.

The environment
---------------

.. list-table::
   :header-rows: 1

   * - Variable
     - Needed for
   * - ``OPUS_CONFIG``
     - Everything but ``--help``. It names the installation's TOML file, and there is
       **no default location**. See :ref:`user_guide_installation` for how to write one.

The pipeline reads nothing else from the environment. The database, the holdings roots
and the log locations all come from the configuration file, and the keys it uses are:

.. list-table::
   :header-rows: 1

   * - Configuration key
     - Used for
   * - ``[database] brand``, ``host``, ``database``, ``schema``, ``user``, ``password``
     - The connection :func:`opus_import.importdb.get_db` opens. The user needs to be
       able to create and drop tables.
   * - ``[paths] pds3_holdings``, ``pds4_holdings``
     - The roots ``rms-pdsfile`` is preloaded against.
   * - ``[paths] import_log_dir``
     - Where ``WARNINGS.log`` and ``ERRORS.log`` are written.
   * - ``[import] log_file``, ``debug_log_file``
     - The run's own info and debug logs.
   * - ``[import] bulk_load``, ``scratch_dir``, ``transaction_rows``
     - How the observation rows are written: whether with ``LOAD DATA LOCAL INFILE``
       (true by default), where its scratch files go (the system temporary directory by
       default), and the most rows to a transaction (100,000 by default). See
       :ref:`dev_guide_import_db_bulk_load`.
   * - ``[import] workers``, ``worker_rows``
     - How the observations of an index are computed: in how many processes (1 by
       default, the import's own process with no pool), and how many index rows one
       worker task covers (500 by default). See
       :ref:`dev_guide_import_running_parallelism`.
   * - ``[import] index_workers``, ``server_tmpdir``
     - How finalization builds the secondary indexes: on how many tables at once (1 by
       default), and in which directory on the database server's host the server sorts
       them (the server's own setting by default). See
       :ref:`dev_guide_import_steps_create_indexes`.
   * - ``[import] cpu_fraction``
     - The ceiling neither ``workers`` nor ``index_workers`` may exceed: the share of the
       cores the import counts that is allowed (0.75 by default). See
       :ref:`dev_guide_import_running_parallelism`.

Configuration values can be overridden for one run without editing the file, with
``--override-db-schema``, ``--override-pds3-data-dir``, ``--override-pds4-data-dir`` and
``--workers``. Importing into a schema other than the one being served is what
``--override-db-schema`` is for, and it is how a production import is done.

.. _dev_guide_import_running_parallelism:

How many processes a run uses
-----------------------------

``[import] workers`` and ``index_workers`` say how much of the computer a run may use.
``workers`` is how many processes compute an index's observations: 1, the default, is
the import's own process with no pool, and a larger count forks a pool of that many for
each index (:ref:`dev_guide_import_steps_do_import_pool`). ``index_workers`` is how many
tables finalization builds keys on at once, each over a connection of its own
(:ref:`dev_guide_import_steps_create_indexes`). Either may be ``"max"``, which asks for
the ceiling.

**No request takes every core**, because the database server or another user may share
the computer. The ceiling is ``max(1, floor(C * cpu_fraction))``, where C is the cores
the process may run on -- its CPU affinity set where the platform has one, so a run
confined by ``taskset`` or a container's CPU set counts only those. ``cpu_fraction`` is greater than 0 and at most 1,
0.75 by default. :func:`opus_config.config.resolve_parallelism` resolves both counts,
and a count above the ceiling is **refused**, not lowered: the run logs a fatal message
naming the count, the ceiling, the cores and the fraction, and exits non-zero before it
opens the database.

``--workers N`` replaces ``[import] workers`` for one invocation, and takes a whole
number of at least 1 or ``max``, checked against the same ceiling.

**The first line of every run's log states the parallelism**: the cores detected,
``cpu_fraction``, the ceiling, and the resolved ``workers`` and ``index_workers``, as
in::

    Parallelism: 8 cores detected, cpu_fraction 0.75, ceiling 6; workers 6, index_workers 1

An index with fewer rows than ``[import] worker_rows`` is computed in the import's own
process whatever ``workers`` says, and so is every index on a platform that cannot
``fork``, which the run reports on an info line. The tables, their ids and the log are the
same whatever the number of workers, apart from the ``Parallelism`` line.

.. _dev_guide_import_the_options:

The options
-----------

Every step of a run is switched on by its own option. Nothing happens by default: an
``opus_import`` invocation with no options reads the configuration, preloads the two
holdings roots, connects to the database, and exits having changed nothing.

Aggregates
~~~~~~~~~~

Some options are shorthands that turn several others on. They accumulate rather than
exclude one another, so giving two of them switches on the union.

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Option
     - What it implies
   * - ``--do-it-all``
     - ``--import``, then ``--finalize``, in one invocation.
   * - ``--finalize``
     - The **finalization group**: ``--create-indexes``, the duplicate step and the
       mult step (neither has an option of its own), ``--create-param-info``,
       ``--create-partables``,
       ``--create-table-names``, ``--create-cart``, ``--reset-search-tables`` and
       ``--analyze-tables``. It refuses to run while any bundle in the bundle registry is
       not ``done`` (below).

``--do-it-all`` is the one option that imports and finalizes in one invocation, a
convenience for a small run; everywhere else ``--import`` and ``--finalize`` are
invocations of their own. Its ``--finalize`` refuses as any other does, so a bundle that
failed in its import stops it before the first finalization step. Neither option implies
``--update-mult-info``, ``--validate``, ``--import-dictionary`` or
``--write-schema-version``; those are always asked for by name.

.. _dev_guide_import_running_paths:

Which path an import takes
~~~~~~~~~~~~~~~~~~~~~~~~~~

No option chooses how an invocation that imports bundles writes; the target schema's
state does (:ref:`dev_guide_import_write_paths`), and the import log says which on a line
beginning ``Import path:``, naming the schema and its version:

.. list-table::
   :header-rows: 1
   :widths: 45 55

   * - Target schema
     - Path
   * - No ``schema_version`` row, and none of the secondary keys finalization adds
     - **Fresh import**: an empty schema, or one a fresh import is part way through,
       since a full import runs one invocation per bundle group. The tables carry only
       the keys a load needs until ``--finalize`` adds the rest once.
   * - One row, of this release's version, ``ready`` or ``appending``
     - **Append**: the bundles load into the tables with their keys in place. The row is
       set to ``appending`` before the first bundle, and stays so until
       ``--write-schema-version``.
   * - A row of another version, more than one row, or a state that is neither
     - **Refused**, with a fatal message naming ``--scorched-earth --yes``: a schema is
       re-imported under the release that will serve it.
   * - No row, but some of the keys finalization adds
     - **Refused**, with a fatal message naming ``--finalize``: its finalization was
       interrupted. ``opus_import --finalize`` on its own completes it, and
       ``--scorched-earth --yes`` starts over.

A refused import changes nothing and exits with failure. On both paths each bundle is
deleted from the observation tables before it is loaded, so importing a bundle again
replaces it. Neither path finalizes on its own: ``--finalize``, ``--validate`` and
``--write-schema-version`` follow as their own invocations, or ``--do-it-all`` runs the
first of them in the same one.

**The bundle registry.** Every invocation that imports bundles records each of them in
the ``import_bundle`` table, on both paths: ``pending`` before the first bundle starts,
``importing`` while it is deleted and loaded, then ``done``, or ``failed`` when its
import failed or logged an error. A bundle whose import fails stops the invocation,
leaving the ones after it ``pending``; one that only logged an error is recorded
``failed`` and the invocation goes on to the next, exiting with failure after the last.
An append first resumes every bundle the registry holds that is not ``done`` and that it
does not name, in bundle order, then imports the ones it names, in the order named. That
order matters: of two copies of one OPUS ID, finalization keeps the one imported last.
An append with nothing to import leaves a finished schema ``ready``.

**An unfinished registry is never finalized or marked ready.** While any bundle in the
registry is not ``done``, ``--finalize`` refuses before its first step, and
``--write-schema-version`` refuses to write ``ready``; each refusal is a fatal message
naming every such bundle with its state, and the invocation exits with failure. Import
the bundle again, or remove it with ``--delete-bundles``, which also deletes its
registry row. ``--ignore-errors`` records a bundle that logged errors ``done``, which is
how a debugging run reaches ``ready`` with them.

:ref:`dev_guide_import_steps_do_import` gives the detail.

Selecting bundles
~~~~~~~~~~~~~~~~~

Bundles are named as positional arguments, comma-separated or space-separated or both.
A *descriptor* is a bundle id (``COISS_2002``), a bundleset name (``COISS_2xxx``), or
one of the shorthands :func:`~opus_import.import_util.yield_import_bundle_ids`
recognizes -- ``ALL``, ``CASSINI``, ``COISS``, ``COCIRS``, ``COUVIS``, ``COVIMS``,
``CORSS``, ``VOYAGER``, ``VGISS``, ``VGPPS``, ``VGUVS``, ``VGRSS``, ``GALILEO``,
``GOSSI``, ``HST``, ``HUBBLE``, ``NH``, ``NEWHORIZONS``, ``NHLORRI``, ``NHMVIC`` and
``EBROCC``, matched without regard to case -- each of which stands for a fixed list of
bundlesets.

``--exclude-bundles`` takes a comma-separated list of bundle ids to drop from whatever
the descriptors expanded to.

Every descriptor is validated as a PDS3 path and then as a PDS4 one, and **every** bad
descriptor is logged before the run exits, so one invocation reports all of them rather
than the first.

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Option
     - Meaning
   * - ``VOL_DESC,VOL_DESC...`` (positional)
     - The bundle descriptors to import.
   * - ``--exclude-bundles VOL_NAME,...``
     - Bundle names to exclude from importing.

Database selection
~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Option
     - Meaning
   * - ``--read-only``
     - Do not modify or create any SQL table. Every mutating statement is logged
       instead of executed.
   * - ``--override-db-schema SCHEMA``
     - Use this schema rather than the configured one.
   * - ``--override-pds3-data-dir DIR``
     - Use this PDS3 holdings root rather than the configured one.
   * - ``--override-pds4-data-dir DIR``
     - Use this PDS4 holdings root rather than the configured one.
   * - ``--dont-use-shelves-only``
     - Read the real volumes and bundles rather than the ``rms-pdsfile`` shelves.
       Without it a run calls ``use_shelves_only()`` on both ``Pds3File`` and
       ``Pds4File`` and ``require_shelves(True)`` on ``Pds3File``.

Import steps
~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Option
     - Meaning
   * - ``--import``
     - Import the named bundles, on the path the schema's state chooses. Each bundle is
       deleted from the observation tables first, so importing it again replaces it.
   * - ``--delete-bundles``
     - Delete the named bundles' rows from every observation table, and their bundle
       registry rows, before any bundle is imported. A ``ready`` schema of this release's
       version is set to ``appending`` first, and needs the closing invocations again.
   * - ``--scorched-earth``
     - Drop every table the import creates in the schema, leaving Django's own
       ``django_*`` and ``auth_*`` tables
       (:ref:`which tables, in which order <dev_guide_import_steps_scorched_earth>`) --
       before any other step. Requires ``--yes``. **This deletes all existing data.**
   * - ``--yes``
     - Confirms ``--scorched-earth``. Giving either without the other is a fatal
       argument error, checked before the database is opened. ``opus_import`` never
       prompts.
   * - ``--analyze-tables``
     - Recompute the key distributions of every ``obs_`` table and the mult tables,
       after the auxiliary, cart and search tables are created.

Parallelism
~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Option
     - Meaning
   * - ``--workers N``
     - Compute each index's observations in ``N`` processes, or ``max`` for the ceiling;
       replaces ``[import] workers``. A count above the ceiling is a fatal error
       (:ref:`dev_guide_import_running_parallelism`).

Import behavior
~~~~~~~~~~~~~~~

These change what the import does with awkward data rather than which steps run.

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Option
     - Meaning
   * - ``--ignore-errors``
     - Record a bundle ``done`` in the bundle registry even when it logs errors, so
       that ``--finalize`` and ``--write-schema-version`` accept it; go on past a
       bundle whose import failed; let a finishing step's failure leave the schema
       marked ready; and substitute made-up values where a real one cannot be
       determined -- an unknown target name becomes ``OTHER`` rather than dropping the
       observation. **The result is wrong on purpose**; it is a debugging aid.
   * - ``--force-metadata-index``
     - Require a metadata index file and fail when none is available.
   * - ``--no-row-files``
     - Do not use the metadata row files to decide whether an index or summary file
       belongs in ``obs_files``.
   * - ``--fake-images``
     - Pretend a browse image exists when the real file is missing.
   * - ``--ignore-missing-images``
     - Do not warn about a missing browse image.
   * - ``--ignore-geo-mismatch``
     - Do not warn when a gridless geometry column's minimum and maximum disagree.
   * - ``--report-missing-ring-geo``
     - Report observations that should have ring geometry and do not.
   * - ``--report-missing-sky-geo``
     - The same for sky geometry.
   * - ``--report-inventory-mismatch``
     - Report a disagreement between the inventory file and the surface geometry
       tables.
   * - ``--report-empty-products``
     - Report products ``rms-pdsfile`` returns under an empty key.
   * - ``--suppress-mult-messages``
     - Leave out the import's messages about reading a mult field and adding a value
       to one.

Auxiliary tables and other steps
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Option
     - Meaning
   * - ``--create-indexes``
     - Add every key the table schemas declare and an observation table lacks: the
       secondary keys a fresh import leaves for finalization. Different tables build at
       once over ``[import] index_workers`` connections; the foreign
       keys follow, one at a time. It does nothing on a schema that has them all. See
       :ref:`dev_guide_import_steps_create_indexes`.
   * - ``--create-param-info``
     - Build ``param_info`` beside the live table and swap it in.
   * - ``--create-partables``
     - Build ``partables``, the same way.
   * - ``--create-table-names``
     - Build ``table_names``, the same way.
   * - ``--update-mult-info``
     - Write the table schemas' ``mult_options`` lists and ``mult_overrides`` over the
       stored ``mult`` rows, and rank the fields they change again. No stored row's id
       or value changes: a list entry that disagrees with a stored row is an error, and
       then nothing is written and the invocation exits with failure. The code-only
       deploy runs it
       (:ref:`dev_guide_import_steps_do_update_mult_info`).
   * - ``--create-cart``
     - Drop and recreate the empty ``cart`` table. It needs ``obs_general``, and on a
       schema without one it logs an error and creates nothing.
   * - ``--reset-search-tables``
     - Drop and re-create the web application's search tables, ``user_searches`` and
       ``search_results``, empty from their schema files, then empty the web
       application's cache (:ref:`dev_guide_import_steps_do_django`). If emptying the
       cache fails, the step fails. Without memcached there is no shared cache to empty,
       and each web worker keeps its own until it is restarted.
   * - ``--validate``
     - Validate the imported tables. A check that logs an error keeps the invocation
       from marking the schema ready, and makes it exit with failure.
   * - ``--import-dictionary``
     - Rebuild ``contexts`` and ``definitions`` from scratch. It runs after every step
       above.
   * - ``--write-schema-version``
     - Mark the schema finished: write its ``schema_version`` row, this release's
       version in the ``ready`` state, which the web application and both deploy
       scripts require (:ref:`user_guide_deployment_schema_version`). It runs last, and
       is the last step of every sequence that finishes a database, and changes an
       append's ``appending`` to ``ready``. It never changes a version the schema already
       records: over another version it logs an error and **exits non-zero**, leaving the
       row alone. It refuses the same way while any bundle in the bundle registry is not
       ``done``.

Logging and diagnostics
~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Option
     - Meaning
   * - ``--log-sql``
     - Log every SQL statement as well.
   * - ``--no-log-pdsfile``
     - Do not log ``rms-pdsfile``'s own output.
   * - ``--log-info-limit N``
     - Suppress info messages past this many. The run continues; only the logging stops.
       ``-1``, the default, means no limit.
   * - ``--log-debug-limit N``
     - The same for debug messages.
   * - ``--log-suppress-traceback``
     - Omit tracebacks from exception reports.
   * - ``--profile``
     - Run under :mod:`cProfile` and log the cumulative statistics and callers at the
       end.
   * - ``--timing-json PATH``
     - When the run exits normally or through ``sys.exit`` (not when a signal kills it),
       write one JSON object to ``PATH`` mapping each step the run performed to its
       wall-clock seconds, plus ``total``. The steps are named as
       :meth:`~opus_import.context.ImportContext.timed` records them: each phase of
       :func:`~opus_import.steps.do_import.do_import_steps` (``scorched_earth``,
       ``delete_bundles``, ``import``), ``delete_bundle:<bundle>`` and
       ``import_bundle:<bundle>`` for each bundle, each table's and each statement's key
       build (``create_indexes:<table>``, ``create_indexes:<table>:<keys>``), and the
       auxiliary, analyze, validation, cart and dictionary steps under their option's
       name with underscores for dashes (``create_param_info``, ``analyze_tables``,
       ``validate``); ``grep -n "ctx.timed("
       src/opus_import`` lists every name. The benchmark harness
       (:ref:`dev_guide_benchmarks`) reads it; nothing else does.

.. _dev_guide_import_what_a_run_does:

What a run does, in order
-------------------------

:func:`opus_import.cli.main` is short, and reading it is the quickest way to see the
whole shape. It:

1. Parses the arguments and expands the two aggregates.
2. Reads the configuration -- **after** parsing, so ``--help`` needs none.
3. Builds a ``pdslogger.PdsLogger`` and the run's
   :class:`~opus_import.context.ImportContext`, and attaches the five log destinations
   described below.
4. Installs a warning handler that collects Python warnings onto the context.
5. Resolves ``workers`` and ``index_workers`` against the ceiling and logs the
   ``Parallelism`` line, exiting non-zero with a fatal message if either is above it
   (:ref:`dev_guide_import_running_parallelism`).
6. Rejects ``--scorched-earth`` without ``--yes``, or ``--yes`` without
   ``--scorched-earth``, with a fatal message and a non-zero exit.
7. Configures ``rms-pdsfile`` -- shelves-only unless ``--dont-use-shelves-only`` -- and
   preloads both holdings roots. The ``rms-pdsfile`` logger is attached *after* the
   preload, so the preload's own debug output stays out of the run's log.
8. Opens the database through :func:`opus_import.importdb.get_db`, exiting non-zero if
   the connection fails.
9. Chooses the import's path when the invocation imports bundles and erases nothing
   first, exiting non-zero if the import is refused
   (:ref:`dev_guide_import_running_paths`).
10. Runs :func:`opus_import.steps.do_import.do_import_steps` -- the erase under
    ``--scorched-earth``, then ``--delete-bundles``, then the import -- exiting non-zero
    if it returns False.
11. Under ``--finalize``, refuses with a fatal message and a non-zero exit, before any
    finalization step, while any bundle in the bundle registry is not ``done``.
12. Runs ``--create-indexes``, then, under ``--finalize``, the duplicate step and the
    mult step (:ref:`dev_guide_import_steps_do_finalize_mult`).
13. Builds the auxiliary tables that were asked for, in the order ``param_info``,
    ``partables``, ``table_names``, then runs ``--create-cart`` and
    ``--reset-search-tables``, then ``--analyze-tables``.
14. Runs ``--update-mult-info``, then ``--validate``, then ``--import-dictionary``.
15. Runs ``--write-schema-version``, exiting non-zero if it refuses: when a finishing
    step of the same invocation failed, when a bundle in the registry is not ``done``,
    or when the schema holds another version.

Any exception that reaches the top is logged as fatal -- with its traceback unless
``--log-suppress-traceback`` -- and the run exits non-zero. :exc:`SystemExit` and
:exc:`KeyboardInterrupt` deliberately propagate rather than being caught.

.. _dev_guide_import_logs:

The logs
--------

A run writes to five places:

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Destination
     - Contents
   * - Standard output
     - Everything, as it happens.
   * - ``[import] log_file``
     - Info level and above. The file name has the run's date and time appended before
       the extension, so a run never overwrites an earlier one.
   * - ``[import] debug_log_file``
     - Debug level and above, dated the same way.
   * - ``WARNINGS.log`` in ``[paths] import_log_dir``
     - Every warning. Appended to rather than rotated.
   * - ``ERRORS.log`` in ``[paths] import_log_dir``
     - Every error. Appended to rather than rotated.

Every message produced while a bundle is being imported carries the bundle, index row
number and primary file specification the run was on when it was produced, so a line read
out of a log names the observation that caused it. Messages from before the first bundle,
and from the steps that run over the whole database, carry none of it. A message made in
a pool worker is written by the import's own process, with the position the worker was
at, where the serial loop would have written it, so the log reads the same whatever
``[import] workers`` is.

.. _dev_guide_import_verifying:

Verifying that a run succeeded
------------------------------

**The exit status is not sufficient.** A non-zero status means the run stopped; a zero
status does **not** mean it was clean. Several steps report failure through the log and
still exit zero. These are not among them: a failed ``--create-indexes``, duplicate
step, ``--create-param-info``, ``--update-mult-info``, ``--import-dictionary`` or
``--validate`` makes the invocation exit with failure and keeps it from marking the
schema ready.

The check that matters is, with ``<import_log_dir>`` standing for the directory that
``[paths] import_log_dir`` names::

    test ! -s <import_log_dir>/ERRORS.log

It is an error-level gate. Because ``ERRORS.log`` is appended to rather than rotated,
truncate or move it before a run whose result you are going to judge this way, and read
``WARNINGS.log`` too: ``--validate`` reports some of what it finds below error level.

``WARNINGS.log`` is worth reading too, but a clean run can have warnings: an index that
legitimately names files OPUS does not import produces one, and so does an observation
whose supplemental metadata is missing. The mini-holdings suite keeps a reviewed
whitelist of the warnings a good run produces; see :ref:`dev_guide_import_fixture`.

Two more checks are worth making after a production import:

* **Row counts.** Compare ``obs_general`` in the new schema against the one being
  served. Nothing in the pipeline does this for you.
* **The auxiliary tables.** A column with no ``param_info`` row is invisible in the
  user interface however much data was written into it, and a table with no
  ``table_names`` row has no "Constraints" section at all.

.. _dev_guide_import_small_run:

A small run
-----------

One volume, into a scratch schema, is what to do while developing::

    export OPUS_CONFIG=/path/to/opus.toml
    opus_import --override-db-schema opus_scratch --do-it-all COISS_2002

``--do-it-all`` imports the named bundles, then runs ``--finalize``: the secondary keys,
one copy of each OPUS ID, and the auxiliary tables. Into an empty schema the import is a
fresh one. Add ``--import-dictionary`` if the
tooltips matter to what you are testing. The web application serves the schema only once
it has its version row, so finish with::

    opus_import --override-db-schema opus_scratch --write-schema-version

To redo only part of a failed run, name the steps individually. Every import deletes
each bundle before it writes it, so a failed bundle is imported again by naming it, and
``--finalize`` refuses until it has been::

    # COISS_2002 failed partway through; import it again, then finish
    opus_import --override-db-schema opus_scratch --import COISS_2002
    opus_import --override-db-schema opus_scratch --finalize

An interrupted ``--finalize`` is completed by running ``--finalize`` again.

Once the schema is ready, importing into it again is an append, which adds bundles or
replaces them; the schema is ``appending``, and refused by the web application, until
the closing invocations have run::

    opus_import --override-db-schema opus_scratch --import COISS_2003
    opus_import --override-db-schema opus_scratch --finalize
    opus_import --override-db-schema opus_scratch --validate
    opus_import --override-db-schema opus_scratch --write-schema-version

To see what a run *would* do without touching anything::

    opus_import --read-only --do-it-all COISS_2002

**Without holdings**, the pipeline can still be exercised end to end against the
checked-in mini-holdings fixture, which needs a MySQL server and nothing else::

    pytest import_tests

:ref:`dev_guide_import_fixture` describes what that covers and what it cannot.

.. _dev_guide_import_full_run:

A full-holdings run
-------------------

A complete import is hours to days and replaces everything a user sees, so it is done
into a new schema and switched over afterwards rather than in place.

The sequence itself is an installed command, :mod:`opus_import.import_all`, run as
``opus_import_all``: the erase, the bundle sets in the order a full import takes them,
and the four steps that finish the database, each as its own ``opus_import`` process,
stopping at the first failure. ``opus_import_all --dry-run`` prints the whole sequence
without running any of it, and :ref:`user_guide_installation_full_import` is the
operator's account of it.

``scripts/import/`` holds the wrappers the Ring-Moon Systems Node uses around that:

``import_all.sh``
    A full production import on one of the Ring-Moon Systems Node's own servers. It
    refuses to run on any
    other host, prints the database currently being served, asks for confirmation, and
    then puts ``opus_import_all --yes`` under ``nohup``. Everything it adds is specific
    to the Ring-Moon Systems Node; the import itself is the installed command.

``import_for_tests.sh``
    The fixed bundle list the integration suite runs against -- Cassini ISS, UVIS, VIMS
    and CIRS, Galileo, Voyager, Hubble, New Horizons, and the occultation bundle sets --
    followed by ``--finalize``, ``--import-dictionary``, ``manage.py migrate``,
    ``--validate`` and ``--write-schema-version``. **It begins by erasing every table the
    import creates** (``--scorched-earth --yes``) and asks for confirmation first,
    printing the schema so that the erase cannot be aimed at the wrong database.

``clone_database.sh``
    Copies a database.

``find_unknown_warnings.sh``
    Filters an import log down to the warnings no known pattern accounts for, which is
    how a run's log is triaged.

The runbook is in :ref:`user_guide_deployment`; the short version is: import into a new
schema, read ``ERRORS.log``, compare against the database being served, point a test
installation at the new one, then switch the public installation over, flush the shared
cache and restart every worker process.

Authoring tools
---------------

:mod:`opus_import.util` holds two programs that are run by hand while authoring a schema
rather than during a run. Both do their work inside a ``main`` function behind an
``if __name__ == '__main__':`` guard, so importing either one -- which the documentation
build does -- runs nothing and reaches no network.

:mod:`opus_import.util.dump_pds_definitions`
    Takes the path of a PDS index label as its single argument and prints each field's
    description, reflowed, as the ``"definition":`` line a table schema wants::

        python -m opus_import.util.dump_pds_definitions /path/to/index.lbl

:mod:`opus_import.util.retrieve_ra_dec`
    Takes no arguments. It looks each star in its own ``STARS`` table up in SIMBAD --
    one HTTP request per star -- and prints the result in the form
    ``STAR_RA_DEC`` (:mod:`opus_import.config_targets.star_ra_dec`) is written in. **Merge
    its output into that table rather than replacing the table with it**: the table
    holds entries this program's list does not, and a wholesale replacement deletes
    them. The module's own docstring gives the snippet that compares the two key sets.

API reference
-------------

:doc:`api_opus_import`
