.. _dev_guide_import_running:

Running the Import Pipeline
===========================

The pipeline is one program with one command line. This chapter is the complete
surface: what to set in the environment, every option, what a run prints, how to tell
whether it worked, and what a small run and a full-holdings run each look like.

:ref:`dev_guide_import` is the theory this chapter assumes.

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
       **no default location**. See :ref:`dev_guide_installation` for how to write one.

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
   * - ``[import] table_temp_prefix``
     - The import namespace's prefix, ``imp_`` by default.

Configuration values can be overridden for one run without editing the file, with
``--override-db-schema``, ``--override-pds3-data-dir`` and ``--override-pds4-data-dir``.
Importing into a schema other than the one being served is what
``--override-db-schema`` is for, and it is how a production import is done.

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
     - ``--drop-old-import-tables``, ``--import``,
       ``--copy-import-to-permanent-tables``, ``--drop-new-import-tables``,
       ``--analyze-permanent-tables``, ``--create-param-info``, ``--create-partables``,
       ``--create-table-names``, ``--create-cart``, ``--drop-cache-tables``.
   * - ``--do-all-import``
     - ``--drop-old-import-tables``, ``--import``,
       ``--copy-import-to-permanent-tables``, ``--drop-new-import-tables``.
   * - ``--do-import-finalization``
     - ``--copy-import-to-permanent-tables``, ``--drop-new-import-tables``,
       ``--analyze-permanent-tables``, ``--create-param-info``, ``--create-partables``,
       ``--create-table-names``, ``--create-cart``, ``--drop-cache-tables``.
   * - ``--cleanup-aux-tables``
     - ``--create-param-info``, ``--create-partables``, ``--create-table-names``,
       ``--create-cart``, ``--drop-cache-tables``.

None of them implies ``--update-mult-info``, ``--validate-perm`` or
``--import-dictionary``; those are always asked for by name.

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
   * - ``--drop-old-import-tables``
     - Drop every existing import table before starting.
   * - ``--leave-old-import-tables``
     - Keep them and add to them; overrides ``--drop-old-import-tables``.
   * - ``--delete-import-bundles``
     - Delete the named bundles from the import tables.
   * - ``--import``
     - Import the named bundles. Implies ``--delete-import-bundles``.
   * - ``--copy-import-to-permanent-tables``
     - Copy the import tables over the permanent ones. Implies
       ``--delete-permanent-import-bundles``.
   * - ``--delete-permanent-import-bundles``
     - Delete from the permanent tables every bundle the import tables hold.
   * - ``--delete-permanent-bundles``
     - Delete the named bundles from the permanent tables.
   * - ``--drop-permanent-tables``
     - Delete **all** permanent tables. Requires ``--scorched-earth``.
   * - ``--scorched-earth``
     - Confirms ``--drop-permanent-tables``. Giving either without the other is a fatal
       argument error, checked before anything connects.
   * - ``--drop-new-import-tables``
     - Drop the import tables after the copy.
   * - ``--analyze-permanent-tables``
     - Recompute the permanent tables' key distributions.

Import behavior
~~~~~~~~~~~~~~~

These change what the import does with awkward data rather than which steps run.

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Option
     - Meaning
   * - ``--import-ignore-errors``
     - Copy to the permanent tables even with errors, and substitute made-up values
       where a real one cannot be determined -- an unknown target name becomes
       ``OTHER`` rather than dropping the observation. **The result is wrong on
       purpose**; it is a debugging aid.
   * - ``--import-check-duplicate-id``
     - Check for a duplicate OPUS ID across bundles. Needed for GOSSI, COUVIS and New
       Horizons, whose bundles overlap.
   * - ``--import-force-metadata-index``
     - Require a metadata index file and fail when none is available.
   * - ``--import-dont-use-row-files``
     - Do not use the metadata row files to decide whether an index or summary file
       belongs in ``obs_files``.
   * - ``--import-fake-images``
     - Pretend a browse image exists when the real file is missing.
   * - ``--import-ignore-missing-images``
     - Do not warn about a missing browse image.
   * - ``--import-ignore-geo-mismatch``
     - Do not warn when a gridless geometry column's minimum and maximum disagree.
   * - ``--import-report-missing-ring-geo``
     - Report observations that should have ring geometry and do not.
   * - ``--import-report-missing-sky-geo``
     - The same for sky geometry.
   * - ``--import-report-inventory-mismatch``
     - Report a disagreement between the inventory file and the surface geometry
       tables.
   * - ``--import-report-empty-products``
     - Report products ``rms-pdsfile`` returns under an empty key.
   * - ``--import-suppress-mult-messages``
     - Say nothing about ``mult_`` table maintenance.

Auxiliary tables and other steps
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Option
     - Meaning
   * - ``--create-param-info``
     - Build ``param_info``, including the copy to the permanent table.
   * - ``--create-partables``
     - Build ``partables``, the same way.
   * - ``--create-table-names``
     - Build ``table_names``, the same way.
   * - ``--update-mult-info``
     - Write the display details a schema pins for a ``mult_`` table back over the
       table the import discovered.
   * - ``--create-cart``
     - Create the ``cart`` table.
   * - ``--drop-cache-tables``
     - Drop the ``cache_*`` tables and clear ``user_searches``.
   * - ``--validate-perm``
     - Validate the permanent tables. **It reports through the log rather than through
       the exit status.**
   * - ``--import-dictionary``
     - Rebuild ``contexts`` and ``definitions`` from scratch. It runs last.

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

.. _dev_guide_import_what_a_run_does:

What a run does, in order
-------------------------

:func:`opus_import.cli.main` is short, and reading it is the quickest way to see the
whole shape. It:

1. Parses the arguments and expands the four aggregates.
2. Reads the configuration -- **after** parsing, so ``--help`` needs none.
3. Builds a ``pdslogger.PdsLogger`` and the run's
   :class:`~opus_import.context.ImportContext`, and attaches the five log destinations
   described below.
4. Installs a warning handler that collects Python warnings onto the context.
5. Rejects ``--drop-permanent-tables`` without ``--scorched-earth``, or the reverse,
   with a fatal message and a non-zero exit.
6. Configures ``rms-pdsfile`` -- shelves-only unless ``--dont-use-shelves-only`` -- and
   preloads both holdings roots. The ``rms-pdsfile`` logger is attached *after* the
   preload, so the preload's own debug output stays out of the run's log.
7. Opens the database through :func:`opus_import.importdb.get_db`, exiting non-zero if
   the connection fails.
8. Runs the cart and cache cleanup, unless ``--drop-permanent-tables`` will drop those
   tables anyway.
9. Runs :func:`opus_import.steps.do_import.do_import_steps`, exiting non-zero if it
   returns False.
10. Builds the auxiliary tables that were asked for, in the order ``param_info``,
    ``partables``, ``table_names``.
11. Runs ``--update-mult-info``, then ``--validate-perm``, then the deferred second
    attempt at the cart table, then ``--import-dictionary``.

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

Every message carries the bundle, index row number and primary file specification the
run was on when it was produced, so a line read out of a log names the observation that
caused it.

.. _dev_guide_import_verifying:

Verifying that a run succeeded
------------------------------

**The exit status is not sufficient.** A non-zero status means the run stopped; a zero
status does **not** mean it was clean. Several steps report failure through the log and
still exit zero -- a failed dictionary import and every ``--validate-perm`` finding
among them.

The check that matters is::

    test ! -s "$IMPORT_LOG_DIR/ERRORS.log"

Because ``ERRORS.log`` is appended to rather than rotated, truncate or move it before a
run whose result you are going to judge this way.

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

``--do-it-all`` imports the named bundles, copies the result over the permanent tables
and rebuilds the auxiliary tables. Add ``--import-dictionary`` if the tooltips matter
to what you are testing.

To redo only part of a failed run, name the steps individually. The import tables
survive a failure precisely so that this works::

    # the import failed partway through; retry just the copy and the aux tables
    opus_import --override-db-schema opus_scratch --do-import-finalization

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

``scripts/import/`` holds the wrappers the Node uses:

``import_all.sh``
    A full production import. It prints the schema it is about to erase and asks for
    confirmation before doing it, so that the erase cannot be aimed at the wrong
    database. It prints no row counts; comparing those is a separate query.

``import_for_tests.sh``
    The fixed bundle list the integration suite runs against -- Cassini ISS, UVIS, VIMS
    and CIRS, Galileo, Voyager, Hubble, New Horizons, and the occultation bundle sets --
    followed by ``--cleanup-aux-tables``, ``--import-dictionary``, ``manage.py
    migrate`` and ``--validate-perm``. **It begins by erasing the permanent tables**
    (``--drop-permanent-tables --scorched-earth``) and asks for confirmation first,
    printing the schema so that the erase cannot be aimed at the wrong database.

``clone_database.sh``
    Copies a database.

``find_unknown_warnings.sh``
    Filters an import log down to the warnings no known pattern accounts for, which is
    how a run's log is triaged.

``_import_all_internal.sh``
    The body ``import_all.sh`` runs once its confirmation has been given. It is the file
    that records which bundle groups get ``--import-check-duplicate-id``.

The runbook is in :ref:`dev_guide_deployment`; the short version is: import into a new
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
