.. _dev_guide_deployment:

Deployment and Operations
=========================

:ref:`dev_guide_installation` brings an installation up by hand and
:ref:`dev_guide_web_server` puts a server in front of it. This chapter is what happens
after that: the Node's own deploy chain, the two things that always have to happen when a
database changes, the runbook for replacing one, and the cron jobs that keep the log
reports current.

.. _deployment_server:

The Node's production arrangement
---------------------------------

``scripts/server/import_and_deploy/`` holds the scripts that deploy a new database or a
new release on the Node's servers.

**A deployed installation is not a checkout.** It is a directory holding a virtual
environment with the released ``rms-opus`` distribution installed **from PyPI**, the
``opus.toml`` that installation reads, and the ``wsgi.py`` symlink Apache points at.
Nothing on the server builds from source. The one checkout a server keeps is the one
holding these scripts, which is also where the deploy configuration lives.

The layout makes the served directory a symbolic link to a per-database directory, so
that swapping databases is a link change rather than a copy:

::

    /opus/src/rms-opus            -> rms-opus_<database name>
    /opus/src/rms-opus_<database name>/
        opus_venv/                # the virtual environment; rms-opus is installed here
        opus.toml                 # this installation's configuration, mode 0600
        wsgi.py                   # symlink into opus_venv/.../site-packages/opus_app/

Underneath the installation root the deploy chain also expects, or creates, five
directories: ``src/`` for the per-database installations above, ``opus_logs/`` for the
web application's log, ``downloads/`` and ``manifests/`` for the cart archives, and
``static_media/`` for the collected static files.

The scripts
-----------

``deploy_new_code_and_database.sh <database name> [<version spec>]``
    A full deploy. It stops Apache and memcached, removes any existing installation
    directory for that database, builds a new one -- virtual environment, ``pip
    install``, generated ``opus.toml``, ``wsgi.py`` symlink -- moves the served link onto
    it, then runs the migration, ``collectstatic``, the cache clear and the dictionary
    and auxiliary-table rebuild, and starts memcached and Apache again.

``deploy_new_code_only.sh [<version spec>]``
    Upgrades the existing installation **in place** with ``pip install --upgrade``,
    reusing its ``opus.toml``, because only a full deploy knows which database to name in
    one. It re-points the ``wsgi.py`` symlink, runs the migration -- not optional, since
    upgrading to the newest release can cross a Django version that adds a contrib
    migration -- collects the static files, clears the cache, and rebuilds
    ``param_info``, ``partables``, ``table_names`` and the dictionary.

    **It refuses to run against anything that is not an installation this chain
    created**: a git checkout at that path, a missing virtual environment, or a missing
    ``opus.toml``. An in-place upgrade of any of those would leave a half-converted
    installation, so the refusal names the full deploy as the way across.

``run_full_opus_import.sh [<version spec>]``
    Runs a complete import into a brand-new schema, which is the first half of bringing
    up a new database. It builds its own installation under a timestamped directory, so
    the import runs against the release being deployed rather than against whatever is
    currently serving; then it dumps the finished database and loads it onto the Node's
    other server. It runs detached and mails the log when it finishes.

The optional argument of all three is a **PEP 440 version specifier** appended to the
distribution name -- ``==3.23.0`` for a particular release, omitted for the newest.

``scripts/server/database/`` holds four scripts that dump a database from one of the two
servers and load it onto the other. ``scripts/import/clone_database.sh`` copies one
database to another on the same server.

.. _dev_guide_deployment_config:

Deploy configuration
--------------------

The deploy chain has its own configuration, separate from the application's, and the
separation is deliberate.

``scripts/server/secrets/deploy.env``
    **Shell syntax**, read by the scripts before any OPUS code exists on the machine. It
    says where to install, which database credentials to use, where the PDS holdings are,
    what Django's secret key is, and where the two site-content files live. Eight
    variables, every one of them required:

    .. list-table::
       :header-rows: 1
       :widths: 34 66

       * - Variable
         - Meaning
       * - ``OPUS_DIR``
         - The installation root, under which the chain expects or creates the five
           directories listed above.
       * - ``OPUS_DB_USER``, ``OPUS_DB_PASSWORD``
         - The MySQL account the import pipeline and the web application connect as.
       * - ``OPUS_SECRET_KEY``
         - Django's secret key for this server.
       * - ``PDS3_HOLDINGS_DIR``, ``PDS4_HOLDINGS_DIR``
         - The two holdings roots. The deploy checks that ``volumes/`` and ``bundles/``
           exist under them.
       * - ``LAST_BLOG_UPDATE_FILE``, ``NOTIFICATION_FILE``
         - The two files of site content the interface displays.

``opus.toml``
    Read by the installed application and the import pipeline at run time.
    ``_write_opus_toml.sh`` **generates it** per installation from the values above, and
    the deploy exports ``OPUS_CONFIG`` pointing at it. **On a Node server, do not
    hand-write this file**: the next deploy overwrites it. Change ``deploy.env``
    instead.

Installing the secrets file
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Copy ``scripts/server/deploy.env.template`` into ``scripts/server/secrets/``, with the
two commands the template gives at the top of itself, and then fill in every
``<PLACEHOLDER>``::

    install -d -m 700 scripts/server/secrets
    install -m 600 scripts/server/deploy.env.template scripts/server/secrets/deploy.env

**Both modes are set as the thing is created rather than afterwards.** The scripts read
this file with ``source``, i.e. they *run* it as shell code with the deploy user's
privileges, so a directory left world-writable by a permissive umask would let another
local account substitute code the deploy then executes. The directory is git-ignored.

Two validations run before a deploy touches anything:

* ``_read_deploy_env.sh`` refuses to continue if any of the eight variables is missing,
  **empty**, or still the placeholder the template ships. Emptiness is refused as well as
  absence because nothing downstream objects to an empty value -- an empty secret key is
  a well-formed TOML string, and Django starts with no secret key.
* ``_write_opus_toml.sh`` refuses a value containing a control character, because TOML
  cannot represent one inside a quoted string, and it writes the generated file under a
  restrictive umask into a temporary name before renaming it into place, so the file is
  never briefly readable while it already holds the password.

Both failures name the variable at fault, and both happen **before the deploy stops
Apache**.

``_write_opus_toml.sh`` is a separate program rather than a block inside the setup script
so that it can be run on its own against a controlled environment and its output loaded
through :func:`opus_config.config.load_config` -- which is what its unit test does. A generator
whose only exercise is a production deploy is a generator nobody has checked.

.. _dev_guide_deployment_after_import:

Two things that always have to happen
--------------------------------------

After **anything** that changes the database, and both are easy to forget:

**1. The shared Django cache has to be emptied**, because it holds result counts, mult
counts, range endpoints and product-type lists keyed by a search that now means something
else::

    OPUS_CONFIG=/etc/opus/opus.toml python -m opus_app.clear_django_cache

That module configures the cache backend and calls ``clear()``, and does nothing else.
Restarting memcached has the same effect, and is what the deploy scripts do.

**2. Every worker process has to be restarted**, because some caches are module-level
dictionaries private to a process -- the ``param_info`` lookup in
:mod:`opus_app.apps.search.views` and the mult-label lookup in
:mod:`opus_app.apps.tools.db_utils`. **Nothing running outside a worker can reach those**,
``clear_django_cache`` included, so restarting the application is the only thing that
clears them. See :ref:`dev_guide_webapp_caching`.

.. _dev_guide_deployment_runbook:

The import runbook
------------------

A production import is long -- hours to days for the full holdings -- and it replaces
what users see, so it is done deliberately.

1. **Import into a new database, not the one being served.**
   ``--override-db-schema`` points one run at a different schema without editing the
   configuration, and the pipeline creates a schema that does not exist. This is the step
   that makes everything after it reversible.
2. **Read the error log.** The import's own exit status is not the whole story:
   ``--validate-perm`` and the dictionary import both report through the log rather than
   through the status, so an automated run gates on ``ERRORS.log`` being empty.
   :ref:`dev_guide_import_verifying` is the full check.
3. **Compare the new database against the one being served.** ``import_all.sh`` prints
   the name of each before it asks for confirmation, so that the erase cannot be aimed at
   the wrong one; it prints no row counts, and comparing those is a separate query you run
   yourself.
4. **Point an installation at the new database and exercise it** before switching the
   public one over. That is what the per-database directory layout is for: a second
   installation with its own ``opus.toml`` can serve the new schema while the public one
   goes on serving the schema it was pointed at.
5. **Switch over**, by moving the served symlink, or by running
   ``deploy_new_code_and_database.sh`` against the new database name.
6. **Flush memcached and restart the application**, as above.

**An import can be resumed rather than restarted.** The per-step options let a run redo
only the part that failed, and the import tables survive a failure precisely so that this
is possible -- see :ref:`dev_guide_import_two_namespaces`.

.. _dev_guide_deployment_log_analyzer:

The log analyzer cron jobs
--------------------------

``scripts/server/log_analyzer/`` holds three cron templates: a nightly update, an
end-of-month report, and a full refresh over a range of months. They are **templates**:
each installation fills in the placeholders -- the virtual environment, the Apache log
directory and its file prefix, and the web directory the reports are published to -- and
installs the result in its own crontab. Nothing substitutes or runs them automatically.

They invoke the analyzer as ``opus_log_analyzer``, the console script the distribution
installs; ``python -m opus_log_analyzer`` runs the same entry point and takes the same
arguments. The nightly update is::

    #!/bin/bash
    source <VENV>/bin/activate
    rm -rf /tmp/log_analyzer_results_temp
    mkdir /tmp/log_analyzer_results_temp
    opus_log_analyzer --cronjob --html --dns \
        -o "/tmp/log_analyzer_results_temp/%Y/OPUS-log-analysis-%Y-%m.html" \
        "<APACHELOGDIR>/<PREFIX>_access_log-%Y-%m-%d"
    cp -r /tmp/log_analyzer_results_temp/* <WWW>/log_analyzer_results
    rm -rf /tmp/log_analyzer_results_temp

The end-of-month job is the same command with ``--cronjob-date -1``, and the refresh job
loops the same command over each month of a year range. The reports they write are
internal operator pages, not part of the public site. :ref:`dev_guide_log_analyzer`
describes the program.

.. _dev_guide_deployment_releasing:

Releasing
---------

The version comes from the git tag, through setuptools-scm, and is written into the
distribution at build time; nothing carries a hard-coded version string. Tags continue
the zero-padded ``v3.x`` scheme -- ``scripts/releases/add_release_tag.sh`` creates one,
and ``scripts/releases/show_version_tags.sh`` lists them.

Publishing a tagged release on GitHub triggers the PyPI publish workflow, which builds
the distributions, validates them, and uploads them. A second workflow does the same
against Test PyPI and runs only on demand. :ref:`dev_guide_environment` describes both,
and the ``Package`` job that exercises the whole release path except the upload itself on
every push.

A deploy then installs that release by version specifier, which is why the deploy scripts
take a PEP 440 specifier rather than a branch name.

Operating checklist
-------------------

.. list-table::
   :header-rows: 1
   :widths: 34 66

   * - Task
     - What to do
   * - Deploy a new release, same database
     - ``deploy_new_code_only.sh ==<version>``
   * - Deploy a new database
     - ``run_full_opus_import.sh``, verify, then
       ``deploy_new_code_and_database.sh <name>``
   * - Change a credential or a path
     - Edit ``deploy.env``, then run a deploy. Never edit ``opus.toml`` on a Node server.
   * - Change a field label or a tooltip
     - Edit the table schema, re-run ``--update-mult-info`` or ``--import-dictionary``,
       clear the cache and restart the workers.
   * - Reports look stale
     - The log-analyzer cron jobs. They are per-installation and are not deployed.
   * - Results look stale
     - :ref:`dev_guide_deployment_after_import`.
