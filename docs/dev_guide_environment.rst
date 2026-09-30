.. _dev_guide_environment:

Environment Setup
=================

Prerequisites
-------------

* **Python 3.12 or later**. The test matrix runs 3.12 and 3.13.
* **MySQL 8.0.19 or later**, with a user allowed to create and drop databases. The
  import pipeline creates every OPUS table itself, and writes its multi-row upserts
  with the ``AS new`` row alias that 8.0.19 added.
* **The MySQL client development headers**, because ``mysqlclient`` ships no Linux
  wheel and is compiled during the install. On Debian or Ubuntu::

      sudo apt-get install pkg-config default-libmysqlclient-dev build-essential

* **memcached**, if you want the web application's caching to behave the way a server
  does. It is not needed to run the tests.
* **wkhtmltopdf**, only if you want the help pages' PDF downloads to work, and only a
  build with patched Qt -- see :ref:`user_guide_installation_prereqs`. Without it every
  other page still renders.
* **The PDS holdings**, only to run a real import against the archive, or the
  integration suites that need the database such an import populates. Neither
  holdings-free suite touches them: ``tests/`` needs nothing, and ``import_tests/`` runs
  the import pipeline end to end against its own checked-in fixture, needing a MySQL
  server but no holdings and no pre-populated database.

A development checkout
----------------------

::

    git clone https://github.com/SETI/rms-opus.git
    cd rms-opus
    python3 -m venv venv
    source venv/bin/activate
    pip install -e ".[dev]"

The ``dev`` extra installs the test suite's dependencies, every checking tool this
repository gates on, and (through ``rms-opus[docs]``) Sphinx and its extensions, so
one install covers everything below.

This chapter is the **development** installation. Bringing up a server -- installing the
released distribution from PyPI, writing a configuration file, creating a database and
collecting the static files -- is :ref:`user_guide_installation`, and putting a web server
in front of it is :ref:`user_guide_web_server`.

Configuration
-------------

OPUS reads one TOML file, and it has **no default location for it**: the
``OPUS_CONFIG`` environment variable must name the file in the environment of every
OPUS process -- the web server, ``manage.py``, the import pipeline and the tests. A
server running several OPUS installations gives each one its own file and its own
``OPUS_CONFIG``.

::

    opus_config_template                          # writes ./opus.toml.template
    install -m 600 opus.toml.template opus.toml
    # fill in every <PLACEHOLDER>
    export OPUS_CONFIG=$PWD/opus.toml

``opus_config_template`` is a console script the distribution installs; the template it
writes ships inside :mod:`opus_config` and documents every key. :mod:`opus_config`
validates the file as it reads it: an unknown key, a missing key, or a value of the wrong type is reported
with the table and key at fault rather than failing later somewhere else.

Environment variables
---------------------

.. list-table::
   :header-rows: 1

   * - Variable
     - Needed by
     - Default
   * - ``OPUS_CONFIG``
     - Everything: the import pipeline, the web application, the tests, the
       documentation build.
     - None. It is an error to leave it unset, except in the documentation build,
       whose ``conf.py`` falls back to ``tests/fixtures/opus_ci.toml``.
   * - ``DJANGO_SETTINGS_MODULE``
     - Bare ``django-admin``, and nothing else. Every other way of starting Django
       here names the settings module itself.
     - Set to ``opus_app.settings`` by ``opus_manage`` and ``manage.py`` (both through
       :mod:`opus_app.manage`), by ``src/opus_app/wsgi.py``, by ``pyproject.toml`` for
       pytest, and by ``docs/conf.py``. ``mypy`` reads it from ``[tool.django-stubs]``
       in ``pyproject.toml`` instead.
   * - ``COVERAGE_RCFILE``
     - The live-database suites, whose coverage gate has its own configuration.
     - Set to ``integration_tests/.coveragerc`` by
       ``scripts/automated_tests/opus_run_unittests_coverage.sh``.
   * - ``OPUS_TEST_DB_HOST``, ``OPUS_TEST_DB_USER``, ``OPUS_TEST_DB_PASSWORD``
     - ``pytest import_tests`` and the golden generator beside it
       (``python -m import_tests.tools.make_mini_goldens``), to name a MySQL server for
       the import suite alone. No OPUS program reads them.
     - None of the three. Read as a set: with none of them set, both take the host,
       user and password out of the ``OPUS_CONFIG`` file instead.

``tests/fixtures/opus_ci.toml`` is a checked-in configuration holding dummy
credentials and paths under ``/tmp``. No job connects to the database it names and no
holdings are ever read, but it is not entirely inert: Django's logging configuration
opens ``paths.opus_log_file`` for writing as :mod:`opus_app.settings` is imported, which
is why every path in it that is opened sits directly under ``/tmp``. It exists so that a
job which has to import those settings -- the type check, the unit tests, the
documentation build -- has a valid configuration without needing a database.

Running the programs
--------------------

**The web application**, against a database an import has already populated::

    python manage.py migrate      # once, for Django's own contrib tables
    python manage.py runserver

Then open ``http://127.0.0.1:8000/opus/``. ``migrate`` creates only Django's session,
auth, contenttypes and admin tables; every OPUS table is created by the import
pipeline instead, so there are no OPUS migrations to run.

``manage.py`` belongs to this checkout. An installation that has only the distribution
runs the same commands as ``opus_manage migrate`` and ``opus_manage runserver``, which
is the same program under another name;
:ref:`dev_guide_webapp_command_line` gives all three forms and what each command does.

**The import pipeline**::

    opus_import --help
    opus_import --do-it-all COISS_2002

``--do-it-all`` runs the whole sequence -- import, copy to the permanent tables, and
rebuild the auxiliary tables -- for the bundles named on the command line. Every step
can also be asked for on its own; :mod:`opus_import.cli` documents the surface and
:mod:`opus_import.steps` documents the order the steps run in.

A smoke test that needs neither holdings nor a database::

    opus_import --help

**The log analyzer**::

    opus_log_analyzer --help
    opus_error_analyzer --help

**Both forms of every command.** Three of the installed commands are OPUS programs, and
each is equivalent to a ``python -m`` invocation because both reach the same ``main``:

=========================  =========================================
Console script             Equivalent module form
=========================  =========================================
``opus_import``            ``python -m opus_import``
``opus_log_analyzer``      ``python -m opus_log_analyzer``
``opus_error_analyzer``    ``python -m opus_log_analyzer.error_analyzer``
=========================  =========================================

The error analyzer names a module rather than a package because a package has one
``__main__`` and the log analyzer holds it. The console scripts are what the server
chains invoke, by name; ``tests/opus_packaging/test_console_scripts.py`` runs both
forms of each and compares them.

The rest have no ``python -m`` form, and all of them exist because an installation has no
checkout to run a script out of. ``opus_manage`` is not an OPUS program at all: it is
Django's own management command line with the settings module already named, so that an
installation needs nothing in its environment but ``OPUS_CONFIG``, and in a checkout
``manage.py`` is the same program. ``opus_config_template`` writes the configuration
template into the working directory. ``opus_import_all`` runs a full import: every bundle
set in order, each as its own ``opus_import`` process, and the three steps that finish the
database. ``opus_deploy_scripts`` writes the server deploy chain out of the distribution;
:ref:`user_guide_deployment` is what it is for.

Running the tests and the checks
--------------------------------

Three suites, split by what each needs -- the holdings-free one that ``pytest`` runs by
itself, the import pipeline against its checked-in fixture, and the suites that need a
populated database -- plus ``scripts/run-all-checks.sh``, which runs everything this
repository gates on. All of it is :ref:`dev_guide_testing`.

Building the documentation
--------------------------

::

    cd docs && make html

``scripts/read-docs.sh`` does the same build and then opens
``docs/_build/html/index.html`` with the platform's default handler. It activates the
virtual environment first (``VENV`` or ``VENV_PATH``, defaulting to ``venv/`` beside
``pyproject.toml``), which is worth knowing when ``make html`` fails on ``import
django``: that error usually means ``sphinx-build`` was found somewhere other than the
project's environment, and the fix is ``pip install -e ".[dev]"`` rather than anything
to do with Django. It is a developer convenience with no CI role -- the ``Docs`` job
and ``run-all-checks.sh`` are the gates.

``docs/Makefile`` passes ``-W`` and ``-n`` by default, which is the gate the
documentation has to pass: ``-W`` turns every warning into an error, and ``-n``
reports every cross-reference that does not resolve. ``make clean`` before ``make
html`` when a change should be checked from scratch, because Sphinx re-reads only what
it thinks changed.

Two extensions in ``docs/_ext/`` write pages into ``docs/`` before each build:

* ``opus_field_tables`` writes the API guide's metadata-field table from
  ``opus_import/table_schemas/*.json``, so that the guide's field list needs no
  database. ``tests/opus_docs/test_field_tables.py`` runs it against the packaged
  schemas.
* ``opus_api_reference`` writes one API-reference page per package and subpackage by
  walking the packages, so a module added to one of them appears in the reference
  without anything being listed by hand.

Both are idempotent and rewrite a page only when its content changes. The pages they
write are git-ignored; to change what they contain, change the generator.

The build imports every OPUS module, and the Django application's modules cannot be
imported until Django is configured, so ``conf.py`` settles ``OPUS_CONFIG`` and calls
``django.setup()`` before Sphinx reads anything. It always assigns the variable: an
existing value is resolved against the repository root -- Sphinx runs ``conf.py`` from
``docs/``, where a relative path would not be found -- and an absent one falls back to
``tests/fixtures/opus_ci.toml``.

Continuous integration
----------------------

Two workflows gate every pull request.

Both trigger the same way: on a push or a pull request against the branches their
``on:`` block names, on a daily schedule, and on demand through
``workflow_dispatch``. Read the branch list out of the workflow rather than from here.

``run-tests.yml`` runs on GitHub-hosted runners. Its jobs are **Run Lint** (ruff,
bandit, vulture, mypy, PyMarkdown), **Unit Tests** on Python 3.12 and 3.13, **Import
Tests**, **Docs** (the same ``-W -n`` Sphinx build as above), and **Package**. None of
them needs holdings; **Import Tests** is the only one that needs a database, and it
brings its own as a MySQL service container.

**Import Tests** runs the whole import pipeline against the checked-in mini-holdings
fixture -- see :ref:`dev_guide_import_fixture` -- and is the only job that measures unit
coverage. It runs the suite twice on purpose: once for the assertions and the coverage
report, and once for the module that reads that report to prove every ``obs`` function
was executed rather than merely imported, which cannot see the report until the session
that writes it has ended.

**Package** is the release path minus the upload: it builds the source distribution and
the wheel, validates them with ``twine check --strict`` and ``pyroma``, then installs
the wheel into a fresh virtual environment outside the checkout and runs all three
console scripts and the package data they read. Running it on every push is what keeps
the release from being the first thing to discover a packaging change. What it cannot
cover is the upload itself, the API tokens, and what PyPI makes of the metadata on
receipt; only a real publish exercises those.

``run-integration.yml`` runs on the Ring-Moon Systems Node's self-hosted runner, which
has the real PDS
holdings mounted. It imports a fixed set of bundles into a fresh database and then runs
the golden-response API suite, the live-database Django suites, and
``tests/opus_support`` and ``tests/opus_app`` -- all in one session, because the 100%
coverage gate measures what all of them reach together. It is what proves that a
refactor did not change what OPUS answers.

The lint, unit, import and integration jobs all install the same thing a developer does,
``pip install -e ".[dev]"`` -- **Docs** installs ``".[docs]"`` and **Package**
deliberately installs the built wheel instead of the project. No job installs from a
lock file, so the integration job logs ``pip freeze``, which is where to look when a
check that passed yesterday fails today.

Third-party actions are referenced by major tag -- ``actions/checkout@v6`` and the
rest -- which is what ``.cursor/rules/environment.mdc`` asks for. The one exception
is ``pypa/gh-action-pypi-publish@release/v1`` in the two publish workflows, a
*branch* ref rather than a tag, because it is the reference PyPA documents for its
own action. A major tag moves when its maintainer cuts a release, and a branch moves
more often still; that is the trade made deliberately, since the workflows then stay
current without anyone updating them.

Releasing
---------

The version comes from the git tag, through setuptools-scm, and is written to
``src/opus_config/_version.py`` at build time; nothing carries a hard-coded version
string. Tags continue the zero-padded ``v3.x`` scheme
(``scripts/releases/add_release_tag.sh`` creates one, and
``scripts/releases/show_version_tags.sh`` lists them). Publishing a tagged release on
GitHub triggers ``publish_to_pypi.yml``, which builds the distributions, validates them
and uploads them to PyPI with an API token. ``publish_to_test_pypi.yml`` does the same
against Test PyPI and runs only on demand, through ``workflow_dispatch``.

Neither workflow uses Trusted Publishing -- both supply a ``password`` -- so neither
needs ``id-token: write``, and both declare ``permissions: contents: read``. A change
to publish through OIDC instead would have to add that permission explicitly, and a
``permissions:`` block that omits it fails the publish at a moment nobody is watching.

Contributing
------------

See :ref:`dev_guide_contributing`.
