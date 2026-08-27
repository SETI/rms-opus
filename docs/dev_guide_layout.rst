.. _dev_guide_layout:

Repository Layout
=================

The importable distribution is everything under ``src/``. Everything else --
``tests/``, ``integration_tests/``, ``scripts/``, ``docs/``, ``perf_test/`` and the
root files -- is supporting code that is not installed, with two deliberate
exceptions: ``manage.py`` at the root is a development convenience, and the package
data inside ``src/`` (table schemas, dictionary sources, templates, static assets)
ships in the wheel because the code reads it at run time through
:mod:`importlib.resources`.

The tree below annotates the directories and files a developer works in.

::

    rms-opus/
    ├── pyproject.toml            # project metadata, dependencies, and the configuration
    │                             #   of every tool: ruff, mypy, pytest, coverage,
    │                             #   bandit, vulture, pymarkdown, setuptools-scm
    ├── opus.toml.template        # the installation configuration file to copy and fill in
    ├── manage.py                 # Django's management command, for development only
    ├── requirements.in           # the dependency floors the lockfile is compiled from
    ├── requirements.txt          # the exact versions the self-hosted runner installs
    ├── vulture_whitelist.py      # names vulture cannot see are used, so it stops
    │                             #   reporting them
    ├── codecov.yml, .readthedocs.yaml
    ├── README.md, CONTRIBUTING.md, LICENSE
    ├── .cursor/rules/            # the coding and documentation standards this repository follows
    ├── .github/workflows/
    │   ├── run-tests.yml         # GitHub-hosted: lint, type check, unit tests, docs build
    │   ├── run-integration.yml   # self-hosted: full import + golden-response API suite
    │   └── publish_to_pypi.yml, publish_to_test_pypi.yml
    ├── src/
    │   ├── opus_config/          # the TOML configuration loader
    │   ├── opus_support/         # unit, time, clock, angle and orbit conversions
    │   ├── opus_import/          # the import pipeline
    │   │   ├── cli.py, __main__.py       # the command-line surface
    │   │   ├── context.py                # the per-run context every step is handed
    │   │   ├── config_data.py            # which missions, instruments and bundles exist
    │   │   ├── config_bundle_info.py     # which obs class and index files a bundle uses
    │   │   ├── config_targets/           # target names, classes and aliases
    │   │   ├── instruments.py            # per-instrument label parsing helpers
    │   │   ├── import_util.py            # helpers shared by the steps and the obs classes
    │   │   ├── importdb/                 # the SQL backend: mysql.py, postgresql.py stub
    │   │   ├── obs/                      # the obs_* class hierarchy, one row per observation
    │   │   ├── steps/                    # the do_* steps, one per command-line option
    │   │   ├── table_schemas/            # package data: the JSON that defines every OPUS table
    │   │   ├── dictionary_data/          # package data: the PDS data dictionary sources
    │   │   └── util/                     # hand-run authoring tools, not part of a run
    │   ├── opus_app/             # the Django project
    │   │   ├── settings.py, urls.py, wsgi.py
    │   │   ├── clear_django_cache.py     # a deployment helper, run as a module
    │   │   ├── apps/{search,results,metadata,ui,cart,help,paraminfo,tools}/
    │   │   ├── templates/                # package data: the project-level templates
    │   │   └── static/                   # package data: the JavaScript, CSS and images
    │   └── opus_log_analyzer/    # the log analyzer
    │       ├── log_analyzer.py, error_analyzer.py   # its two programs
    │       ├── opus/                     # what only OPUS logs need
    │       └── templates/                # package data: the Jinja report templates
    ├── tests/                    # the holdings-free suite; `pytest` alone runs this and
    │                             #   nothing else, because testpaths names it
    │   └── fixtures/opus_ci.toml # the dummy configuration every CI job runs against
    ├── integration_tests/        # the suites that need an imported database and the
    │   │                         #   holdings behind it; run them by naming this directory
    │   ├── .coveragerc           # the 100% gate's coverage configuration
    │   ├── test_api/             # the golden-response API suite
    │   ├── apps_db_tests/        # the per-app database tests
    │   └── test_db_data/, test_perf/
    ├── scripts/
    │   ├── run-all-checks.sh     # every check this repository gates on, in one command
    │   ├── automated_tests/      # what the self-hosted integration workflow runs
    │   ├── import/               # wrappers around the import pipeline
    │   ├── models/               # regenerates apps/search/models.py from the database
    │   ├── releases/             # the version-tag flow
    │   └── server/               # deployment, database dumps, log-analyzer cron templates
    ├── docs/                     # this documentation
    │   └── _ext/                 # the two build-time generators, described below
    └── perf_test/                # a standalone performance experiment, outside every gate

Part of ``docs/`` is generated rather than written:

* ``docs/_build/`` holds the rendered documentation and is never committed.
* Several pages under ``docs/`` are written by the extensions in ``docs/_ext/``
  before each build and are git-ignored: the API reference's ``automodule`` pages
  (``api_reference.rst`` and ``api_opus_*.rst``) and the API guide's metadata-field
  table (``api_guide_fields_table.rst``). Changing what they contain means changing
  the generator, not the file. See :ref:`dev_guide_environment` for how to run them.

``src/opus_app/apps/search/models.py`` is also generated -- by
``scripts/models/create_opus_models.sh``, from a populated database -- but it *is*
committed, because rebuilding it needs a database. It is excluded from ruff for the
same reason, and a hand edit to it does not survive the next regeneration.
