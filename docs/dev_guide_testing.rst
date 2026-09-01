.. _dev_guide_testing:

Testing
=======

Three test suites, split by what each one needs rather than by marker, so that the split
cannot be defeated by a test that forgets to declare itself:

``tests/``
    The holdings-free suite. It needs no database and no PDS files, and it is what
    ``pytest`` alone runs, because ``testpaths`` in ``pyproject.toml`` names it.

``import_tests/``
    The end-to-end test of the import pipeline against the checked-in mini-holdings
    fixture. It needs a MySQL server but no PDS files. See
    :ref:`dev_guide_import_fixture` for what the fixture is and how it is regenerated.

``integration_tests/``
    The suites that need a database an import has populated and, for some of them, the
    holdings behind it. See `Running the integration suites`_.

Only the first runs by default. The other two are asked for by name, which is what keeps
``pytest`` fast and offline.

Running the tests
-----------------

::

    pytest                                   # the holdings-free suite
    pytest -n auto --dist loadscope          # the same, in parallel, as CI runs it
    pytest tests/opus_support/test_units.py  # one file
    pytest -k parse_form_type                # one test by name
    pytest --cov --cov-fail-under=0          # with coverage; see the note below
    pytest import_tests                      # the import pipeline, against MySQL
    pytest integration_tests                 # the live-database suites, serially

Every one of these needs ``OPUS_CONFIG`` set, because ``pytest-django`` configures Django
from it at collection: ``OPUS_CONFIG=tests/fixtures/opus_ci.toml`` is the checked-in dummy
configuration for anything that does not touch a real database, and
``scripts/run-all-checks.sh`` sets it for you.

``--dist loadscope`` keeps each test module on one worker, which matters for the modules
that mock time or share a fixture. The live-database suites are deliberately **not** run
in parallel: they share one database and one of them drops the cache tables between
tests.

These markers are declared, and every marker used anywhere has to be declared because
``--strict-markers`` is on: ``integration`` (applied to everything
``integration_tests/conftest.py`` collects), ``holdings`` (reads a product file out of the
holdings, not just the database row naming it) and ``livetest`` (queries an OPUS server
outside this process).

Warnings are errors. A third-party deprecation cannot rot unnoticed; adding a
narrowly-scoped ``filterwarnings`` entry, with a comment, is the way to admit one that
cannot be fixed here.

Running the import suite
------------------------

``pytest import_tests`` needs a MySQL server and nothing else -- no holdings, no import.
It reads its credentials from ``OPUS_TEST_DB_HOST``, ``OPUS_TEST_DB_USER`` and
``OPUS_TEST_DB_PASSWORD``, defaulting to ``root`` with no password on ``127.0.0.1``. Each
run creates schemas named ``opus_import_test_<pid>`` and drops every one of them when the
session ends, pass or fail.

It runs serially: the run is one long import followed by fast assertions, so ``-n`` buys
nothing, and a session-scoped fixture under xdist would run the import once per worker
into the same schema.

That plain form is the everyday one -- about two minutes, no coverage, with the three
executed-functions tests skipping because the report they read is not there. Measuring
coverage costs about two and a half times that and takes two commands;
:ref:`dev_guide_import_fixture` gives both and says when each is wanted.

.. _running-the-integration-suites:

Running the integration suites
------------------------------

These are the suites that prove what OPUS *answers*: the golden-response API tests, the
live-database Django tests, and ``opus_support`` measured together with them. They need a
database that a real import has populated, and some of them need the PDS holdings behind
it.

**Not generally runnable.** The import reads the PDS3 and PDS4 holdings trees, which are
terabytes on a machine at the Ring-Moon Systems Node. Without them you cannot populate the
database, so you cannot run these suites; the holdings-free suites above are what a
developer without that machine runs, and :ref:`dev_guide_import_fixture` is what covers
the import pipeline for everyone else.

With the holdings available, the chain is three steps and the scripts are the authority on
each:

1. **A configuration file.** ``scripts/automated_tests/opus_setup_environment.sh`` writes
   an ``opus.toml`` into the repository root, pointing at a per-run schema
   ``opus_test_db_<id>``, at ``$PDS_DROPBOX_ROOT/holdings`` and
   ``$PDS_DROPBOX_ROOT/pds4-holdings``, and at per-run log, download and data directories.
   It refuses to write the file if any interpolated value holds a control character, which
   TOML forbids inside a quoted string.

2. **An import.** ``scripts/import/import_for_tests.sh`` erases the permanent tables and
   imports a fixed list of bundles -- Cassini ISS, UVIS, VIMS and CIRS, Galileo, Voyager,
   Hubble, New Horizons, and the occultation bundle sets -- then runs
   ``--cleanup-aux-tables``, ``--import-dictionary``, ``manage.py migrate`` and
   ``--validate-perm``. It asks for confirmation before erasing, and it reads
   ``OPUS_CONFIG`` to find the database, printing the schema name so you can check it is a
   test one before answering. ``scripts/automated_tests/opus_import_test_database.sh``
   drives it non-interactively and gates on both the exit status and ``ERRORS.log``.

3. **The suites.** ``scripts/automated_tests/opus_run_unittests_coverage.sh`` runs
   ``tests/opus_support``, ``tests/opus_app`` and ``integration_tests`` in **one serial
   pytest invocation**, under ``COVERAGE_RCFILE=integration_tests/.coveragerc``. One run
   rather than three because the coverage gate measures all of them together; serial
   because they share one database and mutate it.

Credentials and machine paths come from ``~/opus_runner_secrets``, which every one of
those scripts sources and which is not in the repository: it sets ``OPUS_DB_USER``,
``OPUS_DB_PASSWORD``, ``TEST_ROOT`` and ``PDS_DROPBOX_ROOT``, and each script exits rather
than continue if one is missing.

``scripts/automated_tests/opus_main_test.sh`` runs the whole chain -- set up, import, test,
then drop the schema and delete the temporary directories -- and is what the self-hosted
``Run Integration Tests`` workflow invokes. **It is not the coverage gate**: it exits 0 on
a run whose coverage is 99%. ``opus_run_unittests_coverage.sh`` only measures;
``scripts/automated_tests/opus_check_coverage.sh`` is what fails a build below 100%, and
the workflow runs it as a separate step so that a coverage failure still reaches codecov
first. Reproducing CI locally means running it yourself afterwards.

Two coverage configurations
---------------------------

**They measure different things**, which is why the plain ``pytest --cov`` invocation
above passes ``--cov-fail-under=0``:

* ``[tool.coverage]`` in ``pyproject.toml`` measures :mod:`opus_support`,
  :mod:`opus_config`, :mod:`opus_import` and :mod:`opus_log_analyzer` -- the Django
  application is excluded. **Exactly one command measures it and exactly one number gates
  it**: the ``Import Tests`` job runs ``pytest import_tests --cov``, and ``fail_under`` is
  the floor that run has to stay at or above. Any other suite measured against this
  configuration reaches far less of the four packages, which is why the invocation above
  turns the gate off and why ``scripts/run-all-checks.sh`` runs no coverage at all.

* ``integration_tests/.coveragerc`` measures ``src/opus_app/apps``,
  ``integration_tests/test_api`` and ``src/opus_support``, and **is** gated, at 100%. It is
  a separate file rather than a section of ``pyproject.toml`` because coverage.py ignores
  ``include`` whenever ``source`` is set, so one merged configuration would silently
  corrupt one gate or the other. Select it with ``COVERAGE_RCFILE``.

Running the checks
------------------

``scripts/run-all-checks.sh`` runs everything this repository gates on, in parallel by
default::

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

It runs the holdings-free suite only, which is why a full run needs nothing but a
checkout: every other check reads files.

``--import-tests`` adds the import suite to whatever else is running -- on its own, to the
full run; alongside another ``--*`` flag, to that selection. It is opt-in and never part of
a default run, because it is the one check that needs a reachable MySQL server and it takes
about two minutes against the eighteen seconds everything else costs. It uses the bare
form, without coverage, and reads ``OPUS_TEST_DB_HOST``, ``OPUS_TEST_DB_USER`` and
``OPUS_TEST_DB_PASSWORD`` itself. A failure fails the script, like any other check.

Each check has an ``ENABLE_*`` toggle at the top of the script, so one that is not yet
expected to pass can be switched off in one place rather than deleted.
