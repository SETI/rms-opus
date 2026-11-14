.. _dev_guide_benchmarks:

Benchmarks
==========

The benchmark harness under ``benchmarks/`` measures how long the import takes and how
much memory it uses, what the schema it builds weighs and how the server plans its
queries, and how long the web application takes to answer a fixed set of requests. It
measures one commit, or two commits side by side, on one machine, against servers it
starts itself. A performance claim about OPUS is made from what it records and from
nothing else.

It is not a test suite: nothing it measures passes or fails. Its own code is
unit-tested in ``tests/benchmarks/``, in the holdings-free suite.

What it measures, and at what scale
-----------------------------------

Three **scales**, each named by a file under ``benchmarks/scenarios/``:

``fixture`` (``import_fixture.toml``)
    The checked-in mini-holdings the import suite uses (:ref:`dev_guide_import_fixture`),
    built into a temporary tree and imported one bundle per invocation. Minutes, and
    needs no holdings.

``test`` (``import_test.toml``)
    The bundles ``scripts/import/import_for_tests.sh`` imports, in its order, read from
    the real holdings, in groups each imported by one invocation of the bundle-import
    step. The same database the integration suite's API goldens are pinned to.

``complete`` (``import_complete.toml``)
    Every bundle set, in the order ``opus_import_all`` registers them. Hours.

``tests/benchmarks/test_scenarios.py`` checks that the two holdings scales' groups
agree with the script and with :mod:`opus_import.import_all`.

Five commands, each run from the root of a checkout as ``python -m benchmarks.<name>``:

``bench_server``
    Creates, starts, stops and reports on the MySQL server the harness owns.

``bench_import``
    Times import runs, invocation by invocation and step by step.

``bench_db``
    Measures the schema an import built, and the plans of the statements the web
    scenarios issue.

``bench_web``
    Times the web scenarios against a gunicorn it starts, in three cache states.

``compare``
    Renders two result files as a before/after table, and computes noise floors.

The servers it owns
-------------------

The harness never uses a server it did not start, and needs no administrator access.
Three servers, all on the local machine:

* **MySQL**, from the generic Linux tarball, run from a directory in your home with
  its own data directory, socket and option file, and no TCP listener at all; the data
  root holding the socket is readable by your account alone.
  ``benchmarks/scenarios/server.toml``
  names where each lives; ``benchmarks/scenarios/my.cnf.template`` is the option file,
  and :ref:`dev_guide_benchmarks_tuning` states the rule behind every setting in it. The
  harness and everything it runs reach the server through its socket: the harness puts
  the socket in ``MYSQL_UNIX_PORT``, which the MySQL client library reads for its
  default socket, and writes an ``OPUS_CONFIG`` whose host is ``localhost`` and whose
  account is the server's ``root``, which has no password. The client library reads the variable once, when the driver is first
  imported, so each bench command starts itself again with the variable set if it was
  not.
* **memcached**, on the port ``benchmarks/scenarios/web.toml`` names, with the item
  memory it names. It is started and stopped by each command that needs it.
* **gunicorn**, running the side's web application with ``gthread`` workers, the
  worker and thread counts from ``web.toml``, and as many connections per worker as
  threads, with ``benchmarks/gunicorn_hooks.py`` as its configuration file. Each worker
  loads the application when it starts, its URLconf included: Django otherwise imports
  the URLconf, and with it every view module, on a process's first request, which would
  charge a quarter of a second to whichever measured request happened to reach a worker
  first. The same file has each worker write a line to a served log when it is ready and
  after every request it serves, naming itself and the request, which is how the
  harness knows which worker served what, and assigns any Django settings the run names
  (``--django-setting``) before the worker serves anything.

.. _dev_guide_benchmarks_tuning:

The MySQL tuning baseline
~~~~~~~~~~~~~~~~~~~~~~~~~

The harness-owned server runs ``benchmarks/scenarios/my.cnf.template``, filled in by
``benchmarks/bench_server.py`` from ``benchmarks/scenarios/server.toml``. Results are
judged against each other, not against this baseline; it exists so that every result is
measured on a server configured by stated rules rather than by MySQL's defaults for a
small machine.

The rules that MySQL's documentation gives in terms of the machine's memory are applied
to ``memory_budget_gb`` in ``server.toml`` rather than to the machine's total, because
the measuring machine runs other work too. With the budget at 24 GiB the server gets an
18 GiB buffer pool and a 14 GiB redo log; ``tests/benchmarks/test_bench_server.py``
checks one budget in each band of the documented tables.

.. list-table::
   :header-rows: 1

   * - Setting
     - Value
     - Rule
     - Source
   * - ``innodb_buffer_pool_size``
     - 128 MiB below 1 GiB of budget, half the budget up to 4 GiB, three quarters above, in whole chunks
     - ``innodb_dedicated_server``'s automatic buffer pool size
     - `17.8.12 Enabling Automatic InnoDB Configuration for a Dedicated MySQL Server <https://dev.mysql.com/doc/refman/8.0/en/innodb-dedicated-server.html>`__, Table 17.8
   * - ``innodb_buffer_pool_chunk_size``
     - 128 MiB
     - The default; the pool must be a multiple of the chunk size times the instances
     - `17.8.3.1 Configuring InnoDB Buffer Pool Size <https://dev.mysql.com/doc/refman/8.0/en/innodb-buffer-pool-resize.html>`__
   * - ``innodb_buffer_pool_instances``
     - 1
     - One pool, so the cold-start state is one thing
     - `17.8.3.1 Configuring InnoDB Buffer Pool Size <https://dev.mysql.com/doc/refman/8.0/en/innodb-buffer-pool-resize.html>`__
   * - ``innodb_redo_log_capacity``
     - 100 MiB below 2 GiB of budget; ``round(0.5 × GB) × 0.5`` GiB up to 4; ``round(0.75 × GB) × 0.5`` GiB up to 10.66; ``round(0.5625 × GB)`` GiB up to 170.66; 128 GiB above
     - ``innodb_dedicated_server``'s automatic redo log capacity (8.0.30 and later)
     - `17.8.12 Enabling Automatic InnoDB Configuration for a Dedicated MySQL Server <https://dev.mysql.com/doc/refman/8.0/en/innodb-dedicated-server.html>`__, Table 17.9
   * - ``innodb_flush_method``
     - ``O_DIRECT``
     - No reads through the operating system's page cache, so a restart is a cold start
     - `InnoDB Startup Options and System Variables <https://dev.mysql.com/doc/refman/8.0/en/innodb-parameters.html#sysvar_innodb_flush_method>`__
   * - ``innodb_io_capacity``
     - 1000
     - The documentation's figure for a higher-end, bus-attached SSD
     - `17.8.7 Configuring InnoDB I/O Capacity <https://dev.mysql.com/doc/refman/8.0/en/innodb-configuring-io-capacity.html>`__
   * - ``innodb_io_capacity_max``
     - 2000
     - Twice ``innodb_io_capacity``, the documentation's starting point
     - `17.8.7 Configuring InnoDB I/O Capacity <https://dev.mysql.com/doc/refman/8.0/en/innodb-configuring-io-capacity.html>`__
   * - ``sort_buffer_size``
     - 256 KiB
     - The default
     - `Server System Variables <https://dev.mysql.com/doc/refman/8.0/en/server-system-variables.html#sysvar_sort_buffer_size>`__
   * - ``tmp_table_size``
     - 16 MiB
     - The default
     - `Server System Variables <https://dev.mysql.com/doc/refman/8.0/en/server-system-variables.html#sysvar_tmp_table_size>`__
   * - ``temptable_max_ram``
     - 1 GiB
     - The default
     - `Server System Variables <https://dev.mysql.com/doc/refman/8.0/en/server-system-variables.html#sysvar_temptable_max_ram>`__
   * - ``local_infile``
     - ``ON``
     - A bulk loader may use ``LOAD DATA LOCAL INFILE``
     - `Server System Variables <https://dev.mysql.com/doc/refman/8.0/en/server-system-variables.html#sysvar_local_infile>`__
   * - ``skip-networking``
     - set
     - No TCP listener: the harness and everything it runs connect through the socket
     - `Server System Variables <https://dev.mysql.com/doc/refman/8.0/en/server-system-variables.html#sysvar_skip_networking>`__
   * - ``mysqlx``
     - ``OFF``
     - No X Protocol listener either
     - `X Plugin Options and Variables <https://dev.mysql.com/doc/refman/8.0/en/x-plugin-options-system-variables.html#option_mysqld_mysqlx>`__
   * - ``skip-log-bin``
     - set
     - No binary log; ``log_bin = OFF`` would instead name a log file ``OFF``
     - `Binary Logging Options and Variables <https://dev.mysql.com/doc/refman/8.0/en/replication-options-binary-log.html>`__
   * - ``max_digest_length``
     - 4096
     - Long enough that wide search statements keep distinct digests
     - `Server System Variables <https://dev.mysql.com/doc/refman/8.0/en/server-system-variables.html#sysvar_max_digest_length>`__
   * - ``performance_schema_max_digest_length``
     - 4096
     - The same for the Performance Schema; capped by ``max_digest_length``
     - `Performance Schema System Variables <https://dev.mysql.com/doc/refman/8.0/en/performance-schema-system-variables.html#sysvar_performance_schema_max_digest_length>`__
   * - ``innodb_buffer_pool_load_at_startup``, ``innodb_buffer_pool_dump_at_shutdown``
     - ``OFF``
     - No buffer pool carried across a restart
     - `17.8.3.6 Saving and Restoring the Buffer Pool State <https://dev.mysql.com/doc/refman/8.0/en/innodb-preload-buffer-pool.html>`__

The template also names the server's paths (``basedir``, ``datadir``, ``socket``,
``pid-file`` and ``log-error``), which ``bench_server.py`` fills in. Every other setting
is the server's default, and every result records the values the running server reports
for the settings above and a few more (``RECORDED_SETTINGS`` in ``bench_server.py``).

Setting up a machine
--------------------

Install the harness's own dependencies beside the development ones::

    pip install -e ".[dev,benchmarks]"

The ``benchmarks`` extra is gunicorn, ``psutil`` and ``pymemcache``. Without
``pymemcache`` the web application falls back to its local-memory cache, and
``bench_web`` refuses to run.

memcached has to be installed; ``server.toml`` names the binary. MySQL comes from the
generic Linux tarball for glibc 2.28, unpacked into its own directory under your home,
which is where ``server.toml``'s ``basedir`` points. On a distribution that ships the
tarball's ``libaio.so.1`` under another name -- Ubuntu 24.04's ``libaio1t64`` installs
``libaio.so.1t64`` -- make a private library directory with a link under the old name,
and point ``library_dir`` at it; no root access is involved::

    mkdir -p ~/opt/mysql/lib
    ln -s /lib/x86_64-linux-gnu/libaio.so.1t64 ~/opt/mysql/lib/libaio.so.1

Then create the data directory once, and start the server::

    python -m benchmarks.bench_server init
    python -m benchmarks.bench_server start

Every bench command starts the server itself if it is down, and stops it again when it
finishes; started by hand, it stays up until ``python -m benchmarks.bench_server stop``.
Keep ``server.toml``'s ``memory_budget_gb`` within what the machine can spare, and before
a complete-scale import check that the data directory's filesystem has room for the
whole schema.

The holdings scales read the holdings roots from ``import_test.toml`` and
``import_complete.toml``, which name them through the ``PDS_DROPBOX_ROOT`` environment
variable: set it to the directory holding ``holdings/`` and ``pds4-holdings/``.

Running one side
----------------

Each command measures one **side** -- the code installed in one virtual environment
from one checkout -- named by ``--python`` (the environment's interpreter) and
``--repo-root`` (the checkout). The harness itself always runs from the checkout being
changed, and asks each side's own ``opus_import --help`` how that side spells each step
of the sequence, so it measures older commits as well as its own. Every command refuses
to run with ``PYTHONPATH`` set, since everything it starts would import from there
rather than from the side's checkout.

Every command takes the same label options, which name the result file it writes:
``--scale``, ``--side`` (``before`` for the base, ``after`` for the change),
``--session`` (letters and digits, so that two sessions on one day differ), and
``--pr`` (the change's tag, which begins ``PR`` and a dash). A floor session on one
side, at fixture scale::

    python -m benchmarks.bench_import --scale fixture --side before --pr <tag> \
        --session a --python venv/bin/python --repo-root .
    python -m benchmarks.bench_db --scale fixture --side before --pr <tag> \
        --session a --python venv/bin/python --repo-root . --dump-queries
    python -m benchmarks.bench_web --scale fixture --side before --pr <tag> \
        --session a --python venv/bin/python --repo-root .

``bench_import`` makes the scenario's ``runs`` unless ``--runs`` says otherwise, and
``bench_web`` makes ``web.toml``'s count for the scale. ``bench_db`` and ``bench_web``
use the schema the side's newest import built, which the result file records;
``--schema`` names another.

What an import run is
~~~~~~~~~~~~~~~~~~~~~

One run is the whole sequence a database is built with -- the erase, one bundle-import
invocation per group, the finalization, the dictionary, Django's migration and the
validation -- into a schema of its own. The newest run's schema is kept; the older
ones are dropped. At fixture scale the sequence is
``import_tests.tools.build_run.perform_run``'s; at the holdings scales it is the
scenario file's groups. At test scale the run goes on to import the scenario's largest
bundle alone into a fresh schema, and to time the **incremental group**: a copy of the
finished schema, the largest bundle imported into it, and the finalization sequence.

Every timed import starts on a **freshly restarted server**: before each run, before the
largest bundle's import alone, and between the incremental group's copy and its append,
the harness shuts the owned MySQL server down cleanly, which writes out every dirty page
and checkpoints the redo log, and starts it again. Without that, each run would inherit
the dirty pages and the redo the runs before it left, and a session's later runs would
be slower than its first by their position alone. The run's details record each
restart and how long it took (``server_restarts``).

At fixture and test scale the timed runs are preceded by one **warm-up import** of the
scale's bundles, without finalization, recorded in the result file as a run of kind
``import_warmup`` and never compared. The server reads its own files with ``O_DIRECT``,
so every run starts on a cold buffer pool, but the import reads the holdings through the
operating system's page cache: without the warm-up, a session's first run would read
them from disk and its later runs from memory, by an amount that depends on what the
computer did before the session. The complete scale's holdings do not fit in the page
cache, so each of its runs reads them from disk alike, and it has no warm-up.

Each invocation's wall-clock and memory are recorded -- each process's peak resident set
and the peak, over once-a-second samples, of the process tree's summed proportional set
size -- with the step timings the invocation writes through ``--timing-json``
(:ref:`dev_guide_import_running`), and the server's counters over the run.

Some of those counters show whether a run reached the server's **sustained write limit**:
the bytes written to data files and to the redo log, the pages flushed, and the waits for
a free buffer-pool page (``Innodb_data_written``, ``Innodb_os_log_written``,
``Innodb_buffer_pool_pages_flushed`` and ``Innodb_buffer_pool_wait_free``, each as
``import.server.<counter>``). Beside them, ``import.server.peak_checkpoint_age_bytes`` is
the largest checkpoint age the server reached -- ``Innodb_redo_log_current_lsn`` less
``Innodb_redo_log_checkpoint_lsn``, sampled on the memory samples' beat -- which nears
``innodb_redo_log_capacity`` when the server is holding writes back to flush; a server
older than 8.0.30 reports neither number, and the metric is left out.

Every invocation's import log names the **bulk-load path** it took
(:ref:`dev_guide_import_db_bulk_load`). A run's details list the paths its logs name
(``bulk_load_paths``), and the result's environment records as ``bulk_load_path`` every
path any of the file's runs took, warm-up included, each once. A run whose import names
none counts as ``insert_rows packets``, the path every import took before the bulk load
existed, so a session whose runs took different paths shows both.
``--profile`` runs the holdings scales' bundle imports under :mod:`cProfile` and keeps
the twenty functions with the highest cumulative time; a profiled run is recorded
apart from the timed ones and never compared. ``--reuse-schema NAME`` imports nothing
and records ``NAME`` as the side's schema, or with ``--clone`` a timed copy of it.
``--import-key KEY=VALUE``, repeatable, adds an ``[import]`` key to every configuration
the run writes -- ``index_workers=22``, say, to time finalization's key builds over more
connections than the default -- and the result's environment records the keys as
``import_keys``. A value is written as TOML would read it: ``true`` and ``false`` as
booleans, a whole or finite decimal number as a number, and anything else as a string.
``log_file`` and ``debug_log_file`` are refused, since the harness
reads each run's logs from where it put them. A result file holds runs of one set of
keys: a run with others is refused, as a run of another commit is, and a file whose
runs record no keys takes only runs that set none. In the same way a file holds runs of
one ``--importers`` count, one ``--coordinator`` count, or neither, and a file whose runs
record no count takes only runs in one process. A side whose configuration does not
know a key refuses the file, so it is given only to a side that does.

``--workers-sweep N,N,...`` chooses an ``[import] workers`` count rather than measuring a
change. Instead of the timed runs, it imports the scenario's largest bundle alone,
without finalization, into a fresh schema on a freshly restarted server, once per count:
each count is capped at the ceiling the import itself would apply -- the counted cores
times ``cpu_fraction``, from ``--import-key`` where given and the default otherwise
(:ref:`dev_guide_import_running_parallelism`) -- and each distinct
capped count runs once, in the order first asked for. Each is recorded as a run of kind
``import_sweep`` holding the import's wall-clock, its ``obs_general`` rows per second and
the process tree's peak proportional set size, with the count in its details; a warm-up
import comes first at a scale whose timed runs have one. ``compare`` never compares a
sweep run, so give the sweep a session of its own. It takes none of ``--reuse-schema``,
``--stop-before-finalization`` and ``--profile``, and a scale whose scenario names no
largest bundle refuses it::

    python -m benchmarks.bench_import --scale test --side after --pr <tag> \
        --session sweep --python venv/bin/python --repo-root . --workers-sweep 1,2,4,8,16

``--importers N`` times an import by several queue importers instead of one process,
for a side whose ``opus_import`` has ``--join``. Each run is the side's erase, one
``opus_import --register-bundles`` of every group of the scenario in import order,
``N`` ``opus_import --join`` processes started together, and the finalization sequence.
Neither this nor ``--coordinator M`` imports the largest bundle alone or times the
incremental group, so a multi-importer run has neither measurement.
Each importer has a configuration and a log directory of its own and an equal share of
the ``workers`` total ``--import-key workers=W`` gives, or of 1 when none is given; a
total that ``N`` does not divide is refused, so the importers together use exactly the
workers a one-process run of the same total uses. Every other ``--import-key``, such as
``transaction_rows=1000``, reaches every importer. The importers' phase is recorded as
one invocation, ``join``, timed from the first importer's start to the last one's exit,
with the memory of every importer's process tree; ``import.bundle_imports.wall_s``
counts it, so the run's ``import.wall_s`` lines up with a one-process run's. The run
also records ``import.registration.wall_s`` and, in its details, the importer count,
each importer's workers, and each bundle's ``size_estimate``, its ``import_bundle`` time
from the importers' timings and its ``rows_done``. A side without ``--join`` refuses
the option and is measured as one process with the same ``--import-key workers=W``. A
scenario group that carries options of its own refuses it too, since one registration
cannot give a group options. The runs are of kind ``import`` and compare like any
other::

    python -m benchmarks.bench_import --scale test --side after --pr <tag> \
        --session a --python venv/bin/python --repo-root . \
        --importers 4 --import-key workers=8

Both kinds of run with several importers record each importer's **idle time**, from the
end of its last bundle to the exit of the run's last importer, read from the importers'
own information logs (``benchmarks/importer_logs.py``): each bundle's ``Importing``
block, and the record each importer writes as it exits. An importer that imported no
bundle was idle from its start. The run records ``import.importer_idle_s.max`` and
``import.importer_idle_s.sum``, and the per-importer list, with each importer's log and
bundles, in its details under ``importer_idle_s``.

``--coordinator M`` times the import under ``opus_import_all`` instead, for a side whose
``opus_import_all`` has ``--importers`` and ``--sets``. Each run is the side's erase,
then one ``opus_import_all --sets <groups> --importers M --workers W`` in its default
mode, which registers the scenario's groups in import order, divides the ``workers``
total ``--import-key workers=W`` gives (or 1) among the ``M`` importers it starts and
tracks, and runs its closing sequence once every bundle is done, then Django's
migration. The coordinator divides an uneven total itself, the first importers taking
one more, so any total from ``M`` up to the worker ceiling
(:ref:`dev_guide_import_running_parallelism`) is accepted; a total ``--importers`` must also
take, one every count of a comparison divides, keeps the two kinds of run alike. The
coordinator's closing sequence is ``--finalize``, ``--import-dictionary``,
``--validate`` and ``--write-schema-version``, the finalization sequence less Django's
migration, so the run adds the migration as its own invocation: the work is the same as
an ``--importers`` run's, with the migration last instead of before the validation.
``opus_import_all`` is recorded as one invocation, ``coordinator``, which
``import.wall_s`` counts with the erase and the migration. Its phases come from its own
standard output, read as it is printed
(``coordinator_phases`` in ``benchmarks/importer_logs.py``): the registration, from the
registration's command to the first importer's start, is
``import.registration.wall_s``; the importers' phase, from there to the first closing
command, is ``import.bundle_imports.wall_s``; and each closing invocation, to the next
command or the coordinator's exit, is ``import.invocation.<role>.wall_s``, which with the
migration make ``import.finalization.wall_s``. The coordinator learns that its last
importer has exited at its next reading, so its importers' phase, and its
``import.wall_s``, carry up to one tracking interval
(:data:`~opus_import.coordinator.TRACK_SECONDS`) past the last importer's exit, which a
run with ``--importers`` does not; the idle times stop at the last exit either way. The
coordinator's importers cannot be
given a timing file each, so each bundle's ``import_bundle`` time is its ``Importing``
block's elapsed time in its importer's log, which covers the same call the timing
covers. The details hold the importer count, each importer's workers as the
coordinator's first line states them, the three phases, and each bundle as an
``--importers`` run records it. A side without such an ``opus_import_all`` refuses the
option, and ``--coordinator`` takes no other mode. ``opus_import_all`` runs in a process
group of its own: a Ctrl-C reaches the harness alone, which passes each one on to it and
waits for it to exit, so the server is stopped only once its importers have drained or
aborted. For four importers sharing 20 workers::

    python -m benchmarks.bench_import --scale test --side after --pr <tag> \
        --session a --python venv/bin/python --repo-root . \
        --coordinator 4 --import-key workers=20

``--register-only`` times the registration alone: it registers every group of the
scenario into a scratch schema, which it drops afterwards, and records a run of kind
``register`` holding ``import.registration.wall_s``. Registration reads each bundle's
primary index labels, so at the complete scale this is the cost of preparing a full
import before any importer starts. It takes no other mode, and a side without
``--register-bundles`` refuses it.

**A run that fails records nothing.** It fails when an invocation exits non-zero; when
a bundle-import invocation leaves any bundle it imports without a row in
``obs_general`` (the bundles are its descriptors expanded by the side's own code, less
the ones the import deliberately skips); when the importers of an ``--importers`` or ``--coordinator`` run
leave a registered bundle that is not ``done``; when a coordinator's output does not
mark its phases; or when the run's ``ERRORS.log`` is not empty,
because several steps log an error and still exit zero. Each run starts with a log
directory of its own, and an ``ERRORS.log`` already holding anything fails it before it
starts.

What a web run is
~~~~~~~~~~~~~~~~~

Each scenario is a named sequence of requests issued one after another with one cookie
jar, as a browser issues them; ``benchmarks/web_scenarios.py`` says what each kind of
scenario in ``web.toml`` expands to. Every request carries ``Connection: close``.

One run is two passes over the scenarios. In the **db-cold** pass each scenario is
preceded by emptying the search tables with the side's own option, stopping the
application, restarting the MySQL server (with ``O_DIRECT`` and no buffer pool dump,
an exact cold start), starting the application, and restarting memcached. In the
**app-cold** pass each scenario is preceded by the same without the database restart,
and is issued twice, the second time recorded as **warm**. The application is started
without a request -- the harness waits until every worker has opened the application's
log file and reported itself ready -- because a request would fill the caches the reset
has just emptied. Every cold scenario therefore starts on workers that have served
nothing, and the harness checks the served log to be sure before issuing it.

gunicorn gives each connection to whichever worker accepts it first, so the second
issue of a scenario does not reach the same workers as the first, and a worker meeting a
request for the first time still pays that request's own first-use costs in its
process. So before the warm repetition the harness **warms every worker**: it reissues
the scenario's requests, each with the scenario's cookies, as many copies at a time as
the server has request slots, so that no one worker can take them all, until the served
log shows that every worker has served every request of the scenario, and it refuses the
run when fifty rounds do not get there. The concurrency scenario's requests are warmed
the same way before each half's warm repetition. How many rounds and requests each warm-up took is in
the run's details.

Per scenario and state the run records the wall-clock and each request's latency, the
statements executed against the schema, the twenty statement shapes with the most total
latency, the server's buffer-pool misses, connections, sort-merge passes, on-disk
temporary tables and statements stopped at the execution time limit, the schema's table
count, and the workers' peak resident set. The buffer-pool misses
(``Innodb_buffer_pool_reads``) are the reads a request waited on; they leave out the
pages InnoDB's read-ahead brought in beside them, so the run also records those
(``Innodb_buffer_pool_read_ahead``) and every page read from disk
(``Innodb_pages_read``). A cold scan that read-ahead serves shows few misses and many
pages read. A scenario in which a request fails, or
memcached evicts anything, fails the run: a failed request usually answers sooner than a
served one, so a broken scenario would time as faster, and an eviction means
``memcached_mb`` in ``web.toml`` is too small for the cache state being measured. A
statement stopped at the time limit is recorded rather than refused, since the
application sets that limit on purpose and falls back to a simpler query. The concurrency scenario has many users, each with a session
of its own, issue the fan-out at once, once with a search each and once with the same
search, each half starting from its own reset. It records the latencies of every
request, from which its 95th percentile is computed over all runs together, less the
runs whose own 95th percentile is an outlier (below).

Before starting a side's server, ``bench_web`` gives the schema the version row that
side's web application checks for: it sets the row's version to the side's
``SCHEMA_VERSION``, read through the side's interpreter, or, on a schema with no row, runs
the side's ``opus_import --write-schema-version``. Only a ``ready`` row is restamped
(``bench_server.restamp_version``): a row in any other state keeps its version, which the
import still writing the schema will finish it under, and ``bench_web`` refuses to serve
it, since only a finished import may set ``ready``. A table holding more than one row is
refused before anything is written. Two sides that serve one schema expect different
versions whenever the change raises it. A side whose code has no version checks nothing
and is left alone. ``bench_server.clone_schema`` restamps a copied ``ready`` row the same
way, to the version of the side that will use the copy, and copies any other row as it
is. ``bench_db``'s query capture stamps its schema as ``bench_web`` does before it starts
its server.

Before measuring, ``bench_web`` asks the side's settings, in the environment the workers
run in, which cache they chose: it refuses to run on the local-memory fallback or on a
memcached other than its own, and it refuses a run in which memcached answered no lookup
at all.

Two caches answer some requests before a view runs: Django's per-URL site cache, and the
views' own memcached entries. The statements-executed count is how to tell which
answered: a scenario answered entirely from a cache executes none.

**What a visitor meets after a deploy.** A deploy warms the common searches once its
workers start (:ref:`user_guide_deployment_warm_search`). ``web.toml``'s ``[warm]`` table has a
flag for each cold state, ``db-cold`` and ``app-cold``, both false; a state whose flag is
true, or that ``--warm STATE`` names (repeatable), ends its reset with the side's
``opus_manage warm_search``, asking the harness's own server, after memcached's restart
and before the scenario. The
warm-up's wall-clock is in the run's details under ``warm_search_s``, and its statements
are not counted in the scenario's, since the statement statistics are emptied after it.
A warm-up that fails fails the run.

**A branch the defaults do not take.** ``--django-setting NAME=VALUE`` (repeatable, on
``bench_web`` and on ``bench_db --dump-queries``) has every worker assign that Django
setting before it serves anything, the value typed as an ``--import-key`` value is, so a
run can measure a code path the scale's data does not reach: for example
``STRINGCHOICE_FULL_SEARCH_COUNT_THRESHOLD=1`` makes autocomplete answer from every
observation rather than from the search's results, and
``STRINGCHOICE_SIMPLE_LIKE_TIME_THRESHOLD=0`` makes that answer try the column's
full-text index first. A side whose code does not read a setting ignores it. The
result's environment records the settings as ``django_settings`` (``bench_db``'s details
as ``capture_django_settings``), and ``compare.py`` refuses two results whose settings
differ, so both sides of a comparison are given the same.

``--promotion-carts N`` times a promotion's window before each run's passes: a schema
named after the served one with ``_carry_source`` is made once, holding
``django_session`` and ``cart`` as the served schema declares them, with ``N`` cart rows
naming the served schema's first observations, ``PROMOTION_CART_ROWS_PER_SESSION`` of
them to each unexpired session, an empty copy of each of the two tables to save the
served schema's own rows into, and an empty ``bench_web_promotion_source`` table that
marks it as the harness's. Each run saves the served schema's ``cart`` and
``django_session`` into the copies and puts a row in the mark, in one transaction, then
stops the application, runs the side's ``opus_import --carry-over-sessions-from`` from
that schema into the served one, restarts memcached, and starts the application again,
recording ``web.promotion.carry_over_s``, the carry-over alone, and
``web.promotion.window_s``, from the moment the application is told to stop until it
has started again, every worker having loaded the application. Once the window has
closed, whether or not every step succeeded, the two tables' saved rows replace the ones
the carry-over wrote and the mark is emptied, in one transaction, so every run, on
either side, finds the same tables; neither the save nor the restore is in the window,
and a save that fails stops nothing and restores nothing. A row in the mark therefore
means the schema holds the only copy of the served schema's rows. The rows planted,
fewer than ``N`` when the served schema holds fewer observations, are in the environment
as ``promotion_cart_rows``; the schema is dropped when the command ends, unless a
restore failed, when it is kept and the command fails naming it.

A schema of the source's name without the mark is refused, naming it, and left as it is.
One holding the mark, left by a harness run that did not finish, is dropped before the
source is made; when the mark holds a row, the saved rows first replace the served
schema's and the mark is emptied, in one transaction, and the command says so. A restore
there that fails keeps the schema and fails the command, naming it; its ``saved_cart``
and ``saved_django_session`` hold the rows to put back.

A side without ``warm_search``, or whose ``opus_import --help`` lists no
``--carry-over-sessions-from``, skips that step, and the result's ``skipped_steps``
names it (``warm_search``, ``carry_over_sessions``). The environment records the states
that warmed as ``warm_states`` (none on a side without the command) and the cart rows
each promotion asked for as ``promotion_carts`` (none on a side without the option), and a
result file refuses web runs that differ in either, or in ``promotion_cart_rows``.

What bench_db records
~~~~~~~~~~~~~~~~~~~~~

It first empties the search tables with the side's own option, since the searches an
earlier web run stored are not part of what the import wrote. Then, after
``ANALYZE TABLE`` on every table, with the statistics cache off: each table's data
and index bytes, exact row count and index count, and the largest ``id`` of each mult
table that has an ``id`` column; the schema's totals, its ``FULLTEXT`` tablespaces, and
its size against the buffer pool; the size of ``preview_images`` beside ``obs_general``'s
data, read from ``obs_preview`` or, on a schema without that table, from
``obs_general``, and the table it was read from; and the per-index usage counters.
``--ascii-columns`` counts the non-ASCII values of every column whose form type is
``STRING``.

``--dump-queries`` runs each scenario's requests once with the server's general log on,
writes each request's statements to ``queries_<side>.sql`` in the session's scratch
directory, and replays them at once on one connection: reads are planned with ``EXPLAIN
ANALYZE`` five times and with ``EXPLAIN FORMAT=JSON``, statements that set connection
state are executed, and other writes are never run. The capture is taken from a
gunicorn of one worker with one thread rather than ``web.toml``'s: the application loads
some lookups into its process the first time a request needs them, and a thread its
database connection's settings, so with several workers which request carries those
statements would depend on which worker the request reached. With one, the same commit
captures the same statements every time. A request that fails stops the capture, since
its statements are not the scenario's.

Each request's block gives two metrics. ``time_s`` is the block's time, the sum of its
planned statements' times; each statement is executed five times, so the block has five
times, whose median is the metric and whose range over that median is its spread, with
all five kept in the run's ``samples``. ``rows_examined`` is the sum of the rows its
statements examined, which does not change between executions. Two sides' blocks are
compared by the request that issued them however their statements differ, and every
statement's plans are kept whole in the run's details. A capture names the
tables of the commit and session that made it, so it is replayed only there.
``benchmarks/scenarios/queries.sql`` is a copy kept for a reader, written by
``--commit-capture``; nothing replays it.

Result files
------------

Everything a command measures goes into the **results directory**, one file per label::

    <date>_<tag>_<side>_<scale>_mysql_<session>.json

holding ``{"format", "environment", "runs"}``. The environment records the commit and
whether the checkout had changes, the interpreter, the side's schema version (null for
code that has none), the server's version and settings,
the machine, and what the web runs ran against; a command refuses to add runs from
another commit or server to a file. Each run records its kind (``import``, ``db`` or
``web``), the one-minute load average when it started, its metrics, and its details.
A metric's name says which way is better: one ending in ``_per_s`` is better higher,
every other is better lower. Raw logs, profiles and query captures go under
``benchmarks/scratch/<session>/``, which is not committed.

The results directory is ``[results] root`` in ``benchmarks/scenarios/server.toml``,
outside the repository like the servers' directories, and holds the floors files too.
Neither is committed: most of a result file is diagnostics -- every captured statement's
plan, each scenario's top statements, the index-usage snapshot -- that a reader can
regenerate from the commit it names. What a change carries is the comparison table in
its description, which names the result and floors files it came from.

Comparing two sides
-------------------

How many runs each side makes is fixed before anything is measured. Per side, and for
a web metric per state:

.. list-table::
   :header-rows: 1

   * - Metric
     - Fixture scale
     - Test scale
     - Complete scale
   * - An import metric (``bench_import``)
     - 3 runs
     - 1 run; 3 on a repeat
     - 1 run
   * - A web metric (``bench_web``)
     - 5 runs
     - 3 runs; 5 on a repeat
     - 1 run; 3 where the comparison judges one
   * - A plan time (``bench_db``)
     - 5 executions
     - 5 executions
     - 5 executions
   * - A floor session (below)
     - 3 import, 5 web
     - 3 import, 5 web
     - 1 import, 3 web

A test-scale comparison is **repeated** at the larger counts only when the change in the
metric it sets out to improve lands within twice that metric's floor; the repeat
replaces both sides' earlier runs of the metric rather than being pooled with them. The
scenario files' ``runs`` and ``web.toml``'s ``[runs]`` are the floor-session counts,
so a comparison passes ``--runs`` to each command.

Measure the two sides **in one session on one machine**. Check the base out beside the
change as a second worktree, install each into its own virtual environment, and
alternate the sides' runs: ``A B B A`` for imports (repeated and cut off at the count),
each side importing into its own schema; then ``A B B A`` for web runs when both
imported, or ``A B A B`` against one shared schema when the change leaves the import
alone. A change whose only effect on the schema comes from finalization is measured on
copies instead: the base imports once with ``--stop-before-finalization``, and each
side runs ``bench_import --finalize-only --reuse-schema <that schema>``, which copies it
into a schema of the side's own and runs that side's finalization sequence on the copy;
the side's result file then names the copy, which its ``bench_db`` and ``bench_web``
measure. Then, with the shell variables ``before`` and ``after`` naming the two sides'
result files, ``floors`` the floors file of their scale, all in the results directory,
and ``target`` the metric the change sets out to improve (``--target`` may be given more
than once; a metric not named is only reported or guarded, never judged improved)::

    python -m benchmarks.compare "$before" "$after" --floors-file "$floors" --target "$target"

prints each metric's medians, change, spreads, maxima, floor (as a fraction and in the
metric's units) and verdict, for every target and guard, every metric only one side
holds, and every other metric whose change is larger than its floor; it says how many it
left out, and ``--all`` prints them too. ``compare`` refuses two results whose server model, server
ownership, cache backend or brand differ, two of different scales, the after file given
first, a target neither file holds, and a floors file of another scale or brand. Its
module docstring defines the statistics:
medians over runs, the spread as the range over the median, the change relative to the
before median, and the verdict, which counts a change as an improvement only beyond the
floor and as a regression only beyond the floor plus five percentage points.

A spread leaves out an **outlying run**: one more than three robust standard deviations
(1.4826 times the median absolute deviation) from its session's median. The median every
comparison is made on is barely moved by one such run, so the run does not set the noise
either; the median itself is still taken over every run. Fewer than three runs, or runs
more than half of which equal the median, have no outliers, and session medians are never
left out.

Noise floors
------------

A **floor session** runs the full harness on one commit, with no changes in the
checkout, and ``compare`` refuses sessions of different commits. Two are taken at a scale, and
``python -m benchmarks.compare --floors <session files>`` writes that scale's floors
file into the results directory and names the metrics the two disagree on; where they disagree, check the recorded
load averages, take a third, and run the command again over all three. A metric's floor
is the largest of the sessions' spreads and of the range of their medians over the
median of those medians, a fraction of the metric's median; a metric three sessions
still disagree on is marked noisy. The file records how many runs each session left out
of its spread as outliers.

Each floor is also kept in the metric's own units (``floor_abs``): the widest range of a
session's runs, outliers left out, or the range of the session medians. Small times
scatter by a roughly fixed amount whatever their size -- a few milliseconds of scheduling
on a web request, a fraction of a millisecond on a planned statement -- so a fraction
measured on one median does not carry over to a much smaller one. The file records each
family's **jitter** (``import``, ``db`` and ``web``): the median ``floor_abs`` of its
time metrics. Sessions agree on a metric when their medians lie within the widest range
of a session's runs or, for a time metric, within its family's jitter where that is
larger. Every metric any session recorded gets a floor, and
one that some session lacks is listed, with the sessions that lack it named in the
file. A later comparison judges a metric against the largest of its floor, its absolute
noise (``floor_abs``, or for a time metric its family's jitter where that is larger)
over the before median, and the before side's own spread.

The idle rule
-------------

The measuring machine runs other work, so before any measured session check that it is
idle -- its load average and its process list -- and have its owner confirm that nothing
will be started until told; tell them when the session ends. The load average each run
records is how a reader checks afterwards.
