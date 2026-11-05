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
    The bundle groups ``scripts/import/import_for_tests.sh`` imports, read from the real
    holdings. The same database the integration suite's API goldens are pinned to.

``complete`` (``import_complete.toml``)
    Every bundle set, in the order ``opus_import_all`` imports them. Hours.

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
  and ``benchmarks/README.md`` states the rule behind every sized setting in it. The
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
  harness knows which worker served what.

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
of the sequence, so it measures older commits as well as its own.

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

Each invocation's wall-clock and memory are recorded -- each process's peak resident set
and the peak, over once-a-second samples, of the process tree's summed proportional set
size -- with the step timings the invocation writes through ``--timing-json``
(:ref:`dev_guide_import_running`), and the server's counters over the run.
``--profile`` runs the holdings scales' bundle imports under :mod:`cProfile` and keeps
the twenty functions with the highest cumulative time; a profiled run is recorded
apart from the timed ones and never compared. ``--reuse-schema NAME`` imports nothing
and records ``NAME`` as the side's schema, or with ``--clone`` a timed copy of it.

**A run that fails records nothing.** It fails when an invocation exits non-zero; when
a bundle-import invocation leaves any bundle it imports without a row in the permanent
``obs_general`` (the bundles are its descriptors expanded by the side's own code, less
the ones the import deliberately skips); or when the run's ``ERRORS.log`` is not empty,
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
the same way before its warm half. How many rounds and requests each warm-up took is in
the run's details.

Per scenario and state the run records the wall-clock and each request's latency, the
errors, the statements executed against the schema, the twenty statement shapes with
the most total latency, the server's buffer-pool misses, connections, sort-merge passes
and on-disk temporary tables, memcached's evictions, the schema's table count, and the
workers' peak resident set. The concurrency scenario has many users, each with a session
of its own, issue the fan-out at once, once with a search each and once with the same
search; it records the latencies of every request, from which its 95th percentile is
computed over all runs together.

Before measuring, ``bench_web`` asks the side's settings, in the environment the workers
run in, which cache they chose: it refuses to run on the local-memory fallback or on a
memcached other than its own, and it refuses a run in which memcached answered no lookup
at all.

Two caches answer some requests before a view runs: Django's per-URL site cache, and the
views' own memcached entries. The statements-executed count is how to tell which
answered: a scenario answered entirely from a cache executes none.

What bench_db records
~~~~~~~~~~~~~~~~~~~~~

It first empties the search tables with the side's own option, since per-search tables
left by an earlier web run are not part of what the import built. Then, after
``ANALYZE TABLE`` on every table, with the statistics cache off: each table's data
and index bytes, exact row count and index count, and each ``mult_`` table's largest
id; the schema's totals, its ``FULLTEXT`` tablespaces, and its size against the buffer
pool; the size of ``obs_general.preview_images``; and the per-index usage counters.
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
captures the same statements every time.

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

Everything a command measures goes into ``benchmarks/results/``, one file per label::

    <date>_<tag>_<side>_<scale>_mysql_<session>.json

holding ``{"format", "environment", "runs"}``. The environment records the commit and
whether the checkout had changes, the interpreter, the server's version and settings,
the machine, and what the web runs ran against; a command refuses to add runs from
another commit or server to a file. Each run records its kind (``import``, ``db`` or
``web``), the one-minute load average when it started, its metrics, and its details.
A metric's name says which way is better: one ending in ``_per_s`` is better higher,
every other is better lower. Raw logs, profiles and query captures go under
``benchmarks/scratch/<session>/``, which is not committed.

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
measure. Then::

    python -m benchmarks.compare benchmarks/results/<before>.json \
        benchmarks/results/<after>.json --floors-file benchmarks/results/<floors>.json

prints every metric's medians, change, spreads, floor and verdict. ``compare`` refuses
two results whose server model, server ownership, cache backend or brand differ. Its
module docstring defines the statistics: medians over runs, the spread as the range over
the median, the change relative to the before median, and the verdict, which counts a
change as an improvement only beyond the floor and as a regression only beyond the floor
plus five percentage points.

Noise floors
------------

A **floor session** runs the full harness on one commit. Two are taken at a scale, and
``python -m benchmarks.compare --floors <session files>`` writes that scale's floors
file and names the metrics the two disagree on; where they disagree, check the recorded
load averages, take a third, and run the command again over all three. A metric's floor
is the largest of the sessions' spreads and of the range of their medians over the
median of those medians, a fraction of the metric's median; a metric three sessions
still disagree on is marked noisy. Every metric any session recorded gets a floor, and
one that some session lacks is listed, with the sessions that lack it named in the
file. A later comparison judges a metric against its floor, or against the before
side's own spread where that is larger.

The idle rule
-------------

The measuring machine runs other work, so before any measured session check that it is
idle -- its load average and its process list -- and have its owner confirm that nothing
will be started until told; tell them when the session ends. The load average each run
records is how a reader checks afterwards.
