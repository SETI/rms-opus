.. _dev_guide_testing:

Testing
=======

There are three test suites. They are split by **what each one needs to run**, rather than
by a marker, so that the split cannot be defeated by a test that forgets to declare
itself:

``tests/``
    The holdings-free suite. It needs no database and no PDS files. ``pytest`` with no
    arguments runs this one and nothing else, because ``testpaths`` in ``pyproject.toml``
    names it.

``import_tests/``
    The import pipeline, end to end, against a few megabytes of real archive metadata
    checked into the repository. It needs a MySQL server, but no PDS holdings and no
    database anyone prepared. :ref:`dev_guide_import_fixture` describes the fixture it
    runs against.

``integration_tests/``
    What OPUS *answers*, checked against a database a real import has populated. It needs
    that database, and some of its tests need the PDS holdings behind it, so it runs on a
    machine at the Ring-Moon Systems Node.

The second and third are asked for by name. That is what keeps the everyday ``pytest``
fast and offline.

.. _dev_guide_testing_opus_config:

What every run needs first
--------------------------

**Set** ``OPUS_CONFIG`` **before running any of them**, including the suites that never
touch a database::

    export OPUS_CONFIG=$PWD/tests/fixtures/opus_ci.toml

``tests/fixtures/opus_ci.toml`` is a checked-in dummy configuration: its credentials
connect to nothing and the paths it names are under ``/tmp``. Point the variable at a real
installation's file only when running the integration suite.

It is needed for every run, and not only for the tests that use Django, because
``pyproject.toml`` names ``opus_app.settings`` as the Django settings module for pytest.
``pytest-django`` imports that module once when the session starts, and importing it reads
the OPUS configuration file -- so a session that collects nothing but
``tests/opus_support`` still reads it. Without the variable, pytest stops during startup
with :exc:`~opus_config.config.ConfigError` naming it, before a single test runs.

Running the holdings-free suite
-------------------------------

::

    pytest                                   # the whole suite
    pytest -n auto --dist loadscope          # the same, in parallel, as CI runs it
    pytest tests/opus_support/test_units.py  # one file
    pytest -k parse_form_type                # one test by name

It takes seconds, needs nothing installed but the ``dev`` extra, and is what to run while
working on anything.

``--dist loadscope`` keeps each test module on one worker, which matters for the modules
that mock time or share a fixture.

Warnings are errors here, so a third-party deprecation cannot rot unnoticed. Admitting one
that cannot be fixed here means adding a narrowly-scoped ``filterwarnings`` entry to
``pyproject.toml``, with a comment saying which package raises it and why.

Coverage is deliberately **not** measured by this suite; `Two coverage configurations`_
says which run measures what, and why ``pytest --cov`` on its own needs
``--cov-fail-under=0``.

Running the import suite
------------------------

``pytest import_tests`` needs a MySQL server and nothing else -- no holdings, no import,
no prepared database.

It looks for that server in two places. ``OPUS_TEST_DB_HOST``, ``OPUS_TEST_DB_USER`` and
``OPUS_TEST_DB_PASSWORD`` name one for the suite alone, and are read as a set: if any of
the three is set, the environment is what describes the server, and the other two default
to ``root`` with no password on ``127.0.0.1``. If none of them is set, the host, user and
password come from the ``[database]`` table of the ``OPUS_CONFIG`` file -- which every run
of the suite already has, since ``pytest-django`` configures Django from it at collection
-- so a configuration that already names your own MySQL server needs no second set of
variables.

Only the host, user and password are taken from that file; the schema it names is never
touched. Each run creates schemas named ``opus_import_test_<pid>`` and drops every one of
them when the session ends, pass or fail, so nothing is left on the server to clean up.

There is no third source, and no guessing between the two. With ``OPUS_CONFIG`` pointing
at ``tests/fixtures/opus_ci.toml`` -- which is what ``scripts/run-all-checks.sh`` sets
when you have not exported one -- the suite tries to connect as that dummy configuration's
``opus_ci_user`` and fails rather than falling back to ``root``, and a file that cannot be
read at all stops the session outright. Export a real configuration, or the three
variables, to run against something else.

It runs serially: the run is one long import followed by fast assertions, so ``-n`` buys
nothing, and a session-scoped fixture under xdist would run the import once per worker
into the same schema.

That plain form is the everyday one -- about two minutes, no coverage, with the three
executed-functions tests skipping because the report they read is not there. Measuring
coverage costs about two and a half times that and takes two commands;
:ref:`dev_guide_import_fixture` gives both and says when each is wanted.

.. _running-the-integration-suites:

Running the integration suite
-----------------------------

``integration_tests/`` is what proves that a change did not alter what OPUS returns. It
holds the golden-response API tests, which compare every documented API call's answer byte
for byte, and the live-database tests of the Django apps.

**It needs a database that a real import has populated**, and a few of its tests need the
PDS holdings behind that database as well. `Populating a database to run it against`_ is
how to get one. With ``OPUS_CONFIG`` naming that installation's configuration file::

    pytest integration_tests

**It is not generally runnable.** A real import reads the PDS3 and PDS4 holdings, which
are terabytes on a machine at the Ring-Moon Systems Node; without them there is no
database to run against. A developer working elsewhere runs the other two suites, and
:ref:`dev_guide_import_fixture` is what covers the import pipeline for them.

It runs **serially**, deliberately: every test shares one database, and one of them drops
the ``cache_*`` tables between tests, so ``-n`` would have workers pulling the ground out
from under each other.

Three markers describe what a test reaches for, and ``--strict-markers`` is on, so every
one of them is declared in ``pyproject.toml``:

``integration``
    Applied by ``integration_tests/conftest.py`` to everything it collects.

``holdings``
    Reads a product file out of the holdings tree, not just the database row naming it.

``livetest``
    Queries an OPUS server outside this process, rather than the application in it.

.. _dev_guide_testing_populating:

Populating a database to run it against
---------------------------------------

Two ways, and they do the same work: **by hand**, which is what to use while developing
and what shows what each step does, and **in one command**, which is what the self-hosted
CI job runs. Both need the holdings, a MySQL server, and a checkout with the distribution
installed.

The scripts divide along the same line, which is why they are in two directories:
``scripts/import/`` holds the wrappers a person runs and answers prompts from, and
``scripts/automated_tests/`` holds the unattended chain, which calls those same wrappers
with the prompts answered for it. Nothing is duplicated between them.

By hand
~~~~~~~

1. **Write a configuration file** naming a test schema -- a name you will recognize as
   disposable -- the holdings roots, and directories for logs, downloads and site data.
   ``opus_config_template`` writes the file to copy; set ``OPUS_CONFIG`` to your copy.
   :ref:`user_guide_installation_configuring` describes every key.

2. **Import the test bundles**::

       ./scripts/import/import_for_tests.sh

   It prints the schema it is about to erase and asks for confirmation before doing
   anything, which is the check that keeps it off a database you meant to keep. It then
   imports a fixed list of bundle sets -- Cassini ISS, UVIS, VIMS and CIRS, Galileo,
   Voyager, Hubble, New Horizons, and the occultation sets -- and finishes with
   ``--cleanup-aux-tables``, ``--import-dictionary``, ``manage.py migrate`` and
   ``--validate-perm``. Read ``ERRORS.log`` afterwards rather than trusting the exit
   status: several import steps report failure through the log and still exit zero.

3. **Run the suite**::

       pytest integration_tests

   To reproduce what CI measures rather than just what it asserts, run it the way
   ``scripts/automated_tests/opus_run_unittests_coverage.sh`` does -- one serial
   invocation of ``tests/opus_support``, ``tests/opus_app`` and ``integration_tests``
   together, under ``COVERAGE_RCFILE=integration_tests/.coveragerc``. `Two coverage
   configurations`_ says why all three are in one run.

In one command
~~~~~~~~~~~~~~

::

    ./scripts/automated_tests/opus_main_test.sh
    ./scripts/automated_tests/opus_check_coverage.sh

The first does the whole chain unattended: it makes a per-run directory, writes an
``opus.toml`` naming a schema of its own (``opus_test_db_<id>``, from a timestamp), runs
the import with the confirmation answered for it and gates on both the exit status and
``ERRORS.log``, runs the three suites under the integration coverage configuration, then
drops the schema and deletes the directories it made. Nothing it creates outlives it,
which is why it is safe to run on a machine that has a real database on it.

**It is not the coverage gate.** It exits 0 on a run whose coverage is 99%.
``opus_check_coverage.sh`` is the gate, and the self-hosted workflow runs it as a separate
step so that a coverage failure still reaches codecov first -- which is why reproducing CI
locally means running the second command yourself.

Both scripts read their machine's own settings from ``~/opus_runner_secrets``, a file that
is not in the repository. It sets ``OPUS_DB_USER`` and ``OPUS_DB_PASSWORD``, ``TEST_ROOT``
(where the per-run directories go) and ``PDS_HOLDINGS_ROOT`` (the directory holding
``holdings`` and ``pds4-holdings``). Every script that needs one of them exits rather than
continue if it is missing.

Two coverage configurations
---------------------------

**They measure different things**, and each is gated by exactly one command:

* ``[tool.coverage]`` in ``pyproject.toml`` measures :mod:`opus_support`,
  :mod:`opus_config`, :mod:`opus_import` and :mod:`opus_log_analyzer` -- the Django
  application is not in it. The ``Import Tests`` job runs ``pytest import_tests --cov``,
  and ``fail_under`` is the floor that one run has to stay at or above. Any other suite
  measured against this configuration reaches far less of those four packages, which is
  why a plain ``pytest --cov`` has to pass ``--cov-fail-under=0`` to mean anything.

* ``integration_tests/.coveragerc`` measures ``src/opus_app/apps``,
  ``integration_tests/test_api`` and ``src/opus_support``, and is gated at **100%**. That
  is why ``tests/opus_support``, ``tests/opus_app`` and ``integration_tests`` are run
  together in one invocation: the gate measures what all three reach between them, so
  dropping one deflates the figure rather than failing the run.

It is a separate file rather than another section of ``pyproject.toml`` because
coverage.py ignores ``include`` whenever ``source`` is set, so one merged configuration
would silently corrupt one gate or the other. Select it with ``COVERAGE_RCFILE``.

Running every check
-------------------

``scripts/run-all-checks.sh`` runs everything this repository gates on -- the tests and
every other check -- in parallel by default. It sets ``OPUS_CONFIG`` to the checked-in
dummy configuration itself, so a full run needs nothing but a checkout::

    ./scripts/run-all-checks.sh                 # everything
    ./scripts/run-all-checks.sh -c              # only the code checks
    ./scripts/run-all-checks.sh -d              # only Sphinx and PyMarkdown
    ./scripts/run-all-checks.sh --mypy          # one check
    ./scripts/run-all-checks.sh -s              # sequentially, for readable output
    ./scripts/run-all-checks.sh --import-tests  # everything, plus the import suite

What it runs, and what each one is configured by:

.. list-table::
   :header-rows: 1

   * - Check
     - Command
     - Configuration
   * - Lint
     - ``ruff check``
     - ``[tool.ruff]`` in ``pyproject.toml``
   * - Format
     - ``ruff format --check``
     - ``[tool.ruff.format]``; the formatter owns layout, so this fails on any
       file you have not run ``ruff format`` over
   * - Types
     - ``mypy``
     - ``[tool.mypy]``, strict over the whole repository
   * - Tests
     - ``pytest``
     - ``[tool.pytest.ini_options]``
   * - Packaging
     - ``pyroma .``
     - the ``[project]`` metadata itself
   * - Security
     - ``bandit -c pyproject.toml``
     - ``[tool.bandit]``
   * - Dead code
     - ``vulture``
     - ``[tool.vulture]`` plus ``vulture_whitelist.py``
   * - Documentation
     - ``make clean && make html SPHINXOPTS="-W -n"``, from ``docs/``
     - ``docs/conf.py``
   * - Markdown
     - ``pymarkdown scan``
     - ``[tool.pymarkdown.*]``

The tests it runs are the holdings-free suite alone; every other check reads files. The
other two suites need a server or a database, so neither is in a default run.

``--import-tests`` adds the import suite to whatever else is running -- on its own, to the
full run; alongside another ``--*`` flag, to that selection. It is opt-in because it is the
one check that needs a reachable MySQL server, and because it takes about two minutes
against the eighteen seconds everything else costs. It uses the bare form, without
coverage, and finds its server itself, from ``OPUS_TEST_DB_HOST``, ``OPUS_TEST_DB_USER``
and ``OPUS_TEST_DB_PASSWORD`` or, with none of those set, from the ``OPUS_CONFIG`` file --
which this script points at ``tests/fixtures/opus_ci.toml`` unless you exported one, and
that file's credentials are dummies. A failure fails the script, like any other check.

Each check has an ``ENABLE_*`` toggle at the top of the script, so one that is not yet
expected to pass can be switched off in one place rather than deleted.
