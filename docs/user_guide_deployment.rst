.. _user_guide_deployment:

Deployment and Operations
=========================

:ref:`user_guide_installation` brings an installation up by hand and
:ref:`user_guide_web_server` puts a server in front of it. This chapter is what happens
after that: the Node's own deploy chain, the two things that always have to happen when a
database changes, the runbook for replacing one, and the cron jobs that keep the log
reports current.

.. _deployment_server:

The Node's production arrangement
---------------------------------

The deploy chain is a set of shell scripts that ship inside the distribution.
``opus_deploy_scripts`` writes them out::

    opus_deploy_scripts --directory /opt/opus/deploy

A plain-text ``README.txt`` is written with them, holding the same steps this chapter
gives, so that the instructions are beside the scripts on the server -- readable there
with ``less``, rather than only here.

**Write them somewhere outside every OPUS installation, and run them from there.** A
deploy installs a new ``rms-opus``, and these scripts are part of ``rms-opus``: a script
running from inside the environment being replaced would be rewritten while bash was
still reading it. The copy is also where the deploy's own configuration goes, in
``secrets/deploy.env`` beside it, so credentials do not live in a directory a deploy
replaces. Paths below are relative to that copy.

Being part of the distribution, the chain also *changes* with it, so a copy is refreshed
as part of deploying a new release rather than left where it was; see
:ref:`the order of operations <user_guide_deployment_refresh>`.

**A deployed installation is not a checkout.** It is a directory holding a virtual
environment with the released ``rms-opus`` distribution installed **from PyPI**, the
``opus.toml`` that installation reads, and the ``wsgi.py`` symlink Apache points at.
Nothing on the server builds from source, and nothing on the server needs a checkout.

**Every deploy builds a new installation and switches to it.** Nothing is ever upgraded
in place, and two symbolic links say which installation is which:

::

    /opt/opus/staged/<database>_<timestamp>/
        opus_venv/                # the virtual environment; rms-opus is installed here
        opus.toml                 # this installation's configuration, mode 0600
        wsgi.py                   # symlink into opus_venv/.../site-packages/opus_app/
    /opt/opus/deployed  -> staged/<database>_<timestamp>   # what Apache serves
    /opt/opus/import    -> staged/<database>_<timestamp>   # what an import is using

That shape is what makes a deploy safe to run against a live site, and it follows from
one fact about OPUS: **a release that changes the table schemas cannot read a database
an earlier release imported.** Every OPUS table is created by the import pipeline from
the JSON schemas that ship with a release, so the code and the database it was built by
have to move together, and a deploy that changed either one under a running site would
serve one release's code against another release's database for as long as it took to
finish.

So the import that builds a new database runs under an installation of the new release,
built alongside the running one and touching nothing it uses; the deploy that switches to
it moves the ``deployed`` symlink with a single rename, empties the shared cache, and
restarts the workers. A failure before that moment leaves the site serving exactly what it
was serving, and the previous installation is still on disk afterwards, so going back is
another switch rather than a rebuild.

Underneath the installation root the deploy chain also expects, or creates, these
directories: ``staged/`` for the installations above, ``opus_logs/`` for the web
application's log, ``import_logs/`` for one directory per import run, ``downloads/`` and
``manifests/`` for the cart archives, and ``static_media/`` for the collected static
files.

.. _user_guide_deployment_order:

The order of operations
-----------------------

**From nothing**, on a machine with the prerequisites of
:ref:`user_guide_installation_prereqs` and the holdings mounted::

    # 1. The environment the chain's own commands come from. This is not an
    #    installation that serves anything -- the chain builds those itself -- and its
    #    path is what OPUS_DEPLOY_VENV names in deploy.env below. Every script
    #    activates it for itself afterwards; this is the one time it is done by hand.
    python3.12 -m venv /opt/opus/deploy_venv
    source /opt/opus/deploy_venv/bin/activate
    python -m pip install "rms-opus==3.24.0"

    # 2. The chain, and its own configuration.
    opus_deploy_scripts --directory /opt/opus/deploy
    cd /opt/opus/deploy
    install -d -m 700 secrets
    install -m 600 deploy.env.template secrets/deploy.env
    #    ... then fill in every <PLACEHOLDER> in secrets/deploy.env. OPUS_DIR is the
    #    root everything else hangs off -- /opt/opus here -- and the scripts create
    #    what they need underneath it: staged installations, the logs, the cart
    #    archives and their manifests, and the collected static files.

    # 3. Import the holdings, under an installation of the release being deployed.
    #    Hours to days. It runs detached and mails the log when it finishes.
    ./import_and_deploy/run_full_opus_import.sh ==3.24.0

    # 4. Read that log and ERRORS.log. The database it built is named by the
    #    installation `import` now points at:
    basename "$(readlink /opt/opus/import)"

    # 5. Deploy it: build the installation that will serve, and switch to it.
    ./import_and_deploy/deploy_new_code_and_database.sh opus3_20260902T031500_12345 ==3.24.0

    # 6. Put a web server in front of /opt/opus/deployed/wsgi.py. Once, and never
    #    again: every later deploy moves that symlink rather than the vhost.

**Give steps 3 and 5 the same version specifier.** They install ``rms-opus``
separately -- the import runs under its own installation and the site is served by
another -- so leaving it off both means "the newest release" twice, which is two
different releases if one is published in between.

.. _user_guide_deployment_refresh:

**Updating a running site starts with the scripts themselves.** They ship inside the
distribution, so a copy on a server is one release's chain, and it changes between
releases like anything else. One script brings it up to the release being deployed::

    cd /opt/opus/deploy
    ./import_and_deploy/update_deploy_scripts.sh ==3.24.1

That upgrades ``rms-opus`` in the environment ``OPUS_DEPLOY_VENV`` names -- the one
these commands come from, not any installation that serves anything -- and rewrites this
directory from it, including ``CHAIN_VERSION``, the file recording which release the
scripts came from. It never touches ``secrets/``, which is not part of what ships and so
is not part of what is written. Every other script prints that version as it starts and
says so when it is deploying a different one, which is the check that this step was not
forgotten.

Then the deploy itself is one command, or two, depending on the release. When it
changes nothing about the table schemas -- a bug-fix release -- the database already
being served is still the right one::

    cd /opt/opus/deploy
    ./import_and_deploy/deploy_new_code_only.sh ==3.24.1

When it does change them, the database has to be rebuilt under the new release first,
and the two commands are the same pair as steps 3 and 5::

    cd /opt/opus/deploy
    ./import_and_deploy/run_full_opus_import.sh ==3.25.0
    #    ... read the log, check ERRORS.log, compare row counts against the served
    #    database, exercise the staged installation ...
    ./import_and_deploy/deploy_new_code_and_database.sh opus3_20260915T020000_31337 ==3.25.0

Either way the installation being replaced stays under ``staged/``, so going back is
moving the ``deployed`` symlink onto it and restarting -- there is nothing to rebuild.
Old installations are removed by hand, when the one after them has been trusted for a
while.

The scripts
-----------

``deploy_new_code_and_database.sh <database name> [<version spec>]``
    **The deploy to use whenever the database has been rebuilt**, which is every release
    that changes the table schemas. It builds a new installation under ``staged/``
    naming that database -- virtual environment, ``pip install``, generated
    ``opus.toml``, ``wsgi.py`` symlink -- creates the application's own tables
    (``opus_manage migrate``), gathers the static files and rebuilds the dictionary and
    the auxiliary tables, and only then switches: the ``deployed`` symlink is moved onto
    it, memcached is restarted, and Apache is started again. Apache is stopped for the
    switch alone, not for the build.

``deploy_new_code_only.sh [<version spec>]``
    **Only for a release that does not change the database schema** -- a bug-fix release
    against the database already being served. It reads the database name out of the
    installation currently deployed, builds a new installation at the new release naming
    that same database, runs the same migration, static-file and description-table steps,
    and switches to it the same way. It does not upgrade anything in place.

    Whether a release changed the schemas is the operator's call, from the release notes:
    a database carries no record of the release that wrote it, so nothing here can tell
    the two cases apart. When they did change, the deploy is an import under the new
    release followed by ``deploy_new_code_and_database.sh``.

``update_deploy_scripts.sh [<version spec>]``
    Brings this copy of the chain up to a release: it upgrades ``rms-opus`` in
    ``OPUS_DEPLOY_VENV`` and rewrites the scripts from it. **The first command of every
    upgrade**, before either deploy script.

    It rewrites the file it is running from, which is safe because
    ``opus_deploy_scripts`` replaces each file by renaming a new one over it rather than
    truncating and refilling it: the running script's own file is unlinked from the
    directory and read to its end by the process still holding it open. Truncating in
    place is what would break it -- bash reads a script as it executes it, and would
    resume at the offset it had reached inside the new text, which with a longer
    replacement is a fragment of a line.

``run_full_opus_import.sh [<version spec>]``
    Runs a complete import into a brand-new database, which is the first half of
    deploying a release that changed the schemas. It builds an installation of that
    release under ``staged/`` and points ``import`` at it, so the import runs under the
    release being deployed rather than under whatever is serving, and the result is an
    installation a deploy can switch to. The import itself is ``opus_import_all``, the
    installed command, so the order the bundle sets are imported in comes from the
    release rather than from these scripts. Then, **on a host whose name begins**
    Then, if ``OPUS_PEER_DB_HOST`` names a second server, it dumps the finished database
    and loads it there; with no peer configured it imports and stops. It runs detached,
    and mails the log to ``OPUS_IMPORT_MAIL_TO`` if that names anyone.

    When it is done, the second half is ``deploy_new_code_and_database.sh <that
    database>`` **with the same version specifier this was given**: the two install
    ``rms-opus`` separately, so leaving it off the second is how a release ends up
    serving a database another release built.

The optional argument of all three is a **PEP 440 version specifier** appended to the
distribution name -- ``==3.23.0`` for a particular release, omitted for the newest.

``database/`` holds ``dump_db.sh`` and ``load_db.sh``, which copy a finished database to
a second server: the first writes ``<database>.sql`` into ``OPUS_DB_DUMP_DIR`` from
``OPUS_DB_HOST``, the second loads it into ``OPUS_PEER_DB_HOST``. Neither knows the name
of any machine. ``run_full_opus_import.sh`` runs the pair at the end of an import when a
peer is configured, and ``scripts/import/clone_database.sh`` in the repository copies one
database to another on the same server.

.. _user_guide_deployment_config:

Deploy configuration
--------------------

The deploy chain has its own configuration, separate from the application's, and the
separation is deliberate.

``secrets/deploy.env``
    **Shell syntax**, read by the scripts before any OPUS code exists on the machine. It
    holds everything about *this* server: where to install, which account to run as,
    which environment the chain's own commands come from, which database to connect to
    and as whom, where the PDS holdings are, what the site calls itself, and what to do
    with a finished database. Nothing in the scripts assumes a value for any of it --
    no host name, no URL, no path -- so the same chain runs on any server that fills
    this file in. Every variable is required except the two marked optional:

    .. list-table::
       :header-rows: 1
       :widths: 34 66

       * - Variable
         - Meaning
       * - ``OPUS_DIR``
         - The installation root, under which the chain creates everything else: the
           staged installations, the logs, the cart archives and their manifests, and
           the collected static files.
       * - ``OPUS_DEPLOY_VENV``
         - The virtual environment the chain's own commands come from -- the one
           ``opus_deploy_scripts`` was run out of. Every script activates it for
           itself, so a deploy runs the same way from a shell, from cron and under
           ``nohup``. It is not one of the installations under ``staged/``: those are
           what a deploy builds, and ``_opus_setup_environment.sh`` deactivates this
           one before activating the installation it has just built.
       * - ``OPUS_USER``
         - The Unix account OPUS runs as, and the account every script here has to be
           run as. Everything a deploy creates belongs to whoever ran it, including an
           ``opus.toml`` at mode 0600, so a deploy run as anyone else -- root, most
           easily -- builds an installation the web server cannot read. The reader
           refuses rather than letting that reach the switch.
       * - ``OPUS_DB_HOST``
         - The MySQL server this installation connects to, usually ``localhost``.
       * - ``OPUS_DB_USER``, ``OPUS_DB_PASSWORD``
         - The MySQL account the import pipeline and the web application connect as.
       * - ``OPUS_SECRET_KEY``
         - Django's secret key for this server.
       * - ``PDS3_HOLDINGS_DIR``, ``PDS4_HOLDINGS_DIR``
         - The two holdings roots. The deploy checks that ``volumes/`` and ``bundles/``
           exist under them.
       * - ``LAST_BLOG_UPDATE_FILE``, ``NOTIFICATION_FILE``
         - The two files of site content the interface displays.
       * - ``OPUS_DEBUG``
         - Django's ``DEBUG``, as the unquoted ``true`` or ``false`` TOML wants.
           ``false`` on anything reachable from outside the machine; a staging server is
           the case for ``true``.
       * - ``OPUS_ALLOWED_HOSTS``
         - Every name and address this installation answers to, separated by spaces.
           Django refuses a request whose ``Host`` header is not among them, so a name a
           proxy or a health check reaches it by belongs here as much as the public one,
           and so do ``127.0.0.1`` and ``localhost``, which is how a smoke test from the
           server itself arrives. The generator turns the list into the TOML array
           ``allowed_hosts``.
       * - ``OPUS_CACHE_PREFIX``
         - The prefix on this installation's keys in the shared cache. Two installations
           sharing one memcached need different prefixes, or each reads the other's
           answers.
       * - ``OPUS_PUBLIC_URL``, ``OPUS_PRODUCT_HTTP_PATH``, ``OPUS_VIEWMASTER_URL``,
           ``OPUS_TAR_FILE_URL``
         - What the site calls itself and where it serves things from. They appear in
           what the API returns, so they are the URLs a user's browser has to be able to
           reach rather than any internal address.
       * - ``OPUS_DB_DUMP_DIR``
         - Where ``mysqldump`` writes a finished database, and where the load reads it
           back. On two servers that copy databases to each other, a directory both can
           see.
       * - ``OPUS_PEER_DB_HOST``
         - *Optional.* The MySQL server a finished database is copied to. With a host
           here, an import ends by dumping what it built and loading it there; empty,
           the import stops when the database is built, which is what one server wants.
       * - ``OPUS_IMPORT_MAIL_TO``
         - *Optional.* Where to mail the log when an import finishes. An import runs for
           days under ``nohup``, so the mail is how anyone finds out that it ended and
           whether it ended well. Empty sends nothing and leaves the log where it was
           written.

``opus.toml``
    Read by the installed application and the import pipeline at run time.
    ``_write_opus_toml.sh`` **generates it** per installation from the values above, and
    the deploy exports ``OPUS_CONFIG`` pointing at it. **On a Node server, do not
    hand-write this file**: the next deploy overwrites it. Change ``deploy.env``
    instead.

Installing the secrets file
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Copy ``deploy.env.template`` into ``secrets/`` beside it, with the two commands the
template gives at the top of itself, and then fill in every ``<PLACEHOLDER>``::

    install -d -m 700 secrets
    install -m 600 deploy.env.template secrets/deploy.env

**Both modes are set as the thing is created rather than afterwards.** The scripts read
this file with ``source``, i.e. they *run* it as shell code with the deploy user's
privileges, so a directory left world-writable by a permissive umask would let another
local account substitute code the deploy then executes. The directory is git-ignored.

Two validations run before a deploy touches anything:

* ``_read_deploy_env.sh`` refuses to continue when the account running the deploy is not
  ``OPUS_USER``, naming both and the ``sudo -u`` that fixes it, and when ``OPUS_DEBUG``
  is neither ``true`` nor ``false``. It also refuses if any required variable is missing,
  **empty**, or still the placeholder the template ships. Emptiness is refused as well as
  absence because nothing downstream objects to an empty value -- an empty secret key is
  a well-formed TOML string, and Django starts with no secret key.
* ``_write_opus_toml.sh`` refuses a value containing a control character, because TOML
  cannot represent one inside a quoted string, and it writes the generated file under a
  restrictive umask into a temporary name before renaming it into place, so the file is
  never briefly readable while it already holds the password.

Both failures name the variable at fault, but they happen at different moments. The
missing-value check runs before the deploy stops Apache; the generator runs from
``_opus_setup_environment.sh``, which is sourced **after** the stop, so a value TOML
cannot represent leaves Apache down until it is corrected. That script's own comments
record the same hazard for its other failure point, the :func:`importlib.util.find_spec`
lookup that locates Apache's WSGI target.

``_write_opus_toml.sh`` is a separate program rather than a block inside the setup script
so that it can be run on its own against a controlled environment and its output loaded
through :func:`opus_config.config.load_config` -- which is what its unit test does. A generator
whose only exercise is a production deploy is a generator nobody has checked.

.. _user_guide_deployment_after_import:

Two things that always have to happen
-------------------------------------

After **anything** that changes the database, and both are easy to forget:

**1. The shared Django cache has to be emptied**, because it holds result counts, mult
counts, range endpoints and product-type lists keyed by a search that now means something
else::

    OPUS_CONFIG=/opt/opus/opus.toml python -m opus_app.clear_django_cache

That module configures the cache backend and calls ``clear()``, and does nothing else.
Restarting memcached has the same effect, and is what the deploy scripts do.

**2. Every worker process has to be restarted**, because some caches are module-level
dictionaries private to a process -- the ``param_info`` lookup in
:mod:`opus_app.apps.search.views` and the mult-label lookup in
:mod:`opus_app.apps.tools.db_utils`. **Nothing running outside a worker can reach those**,
``clear_django_cache`` included, so restarting the application is the only thing that
clears them. See :ref:`dev_guide_webapp_caching`.

.. _user_guide_deployment_runbook:

The import runbook
------------------

A production import is long -- hours to days for the full holdings -- and it replaces
what users see, so it is done deliberately.

1. **Import into a new database, under an installation of the release being deployed.**
   ``run_full_opus_import.sh`` does both: a new installation under ``staged/``, a
   database named for the moment it started, and ``import`` pointed at the installation
   doing the work. Neither the database being served nor the installation serving it is
   touched, which is what makes every step after this one reversible.
2. **Read the error log.** The import's own exit status is not the whole story:
   ``--validate-perm`` and the dictionary import both report through the log rather than
   through the status, so an automated run gates on ``ERRORS.log`` being empty.
   :ref:`dev_guide_import_verifying` is the full check.
3. **Compare the new database against the one being served.** Both are named before
   anything is erased -- ``opus_import_all`` names the one it is about to build, and the
   Node's ``import_all.sh`` wrapper also prints the one currently serving -- so that the
   erase cannot be aimed at the wrong one. Neither prints row counts; comparing those is
   a separate query you run yourself.
4. **Exercise the new database before switching the public site to it.** The staged
   installation is a complete OPUS pointed at it, and naming its own ``opus.toml`` is
   what makes it read the new database rather than the served one::

       OPUS_CONFIG=/opt/opus/staged/<that installation>/opus.toml \
           /opt/opus/staged/<that installation>/opus_venv/bin/gunicorn \
           --bind 127.0.0.1:8001 opus_app.wsgi:application

   The public site goes on serving what it was serving throughout.
5. **Switch over** with ``deploy_new_code_and_database.sh <that database>``. It builds
   the installation the public site will use, moves the ``deployed`` symlink onto it,
   restarts memcached and starts Apache again -- and stops Apache only for that switch.
6. **Check the site, and keep the previous installation** until you are sure. It is still
   under ``staged/``, and going back to it is moving the same symlink.

**An import can be resumed rather than restarted.** The per-step options let a run redo
only the part that failed, and the import tables survive a failure precisely so that this
is possible -- see :ref:`dev_guide_import_two_namespaces`.

.. _user_guide_deployment_log_analyzer:

The log analyzer cron jobs
--------------------------

``log_analyzer/`` holds the cron templates: a nightly update, an
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

.. _user_guide_deployment_releasing:

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
     - :ref:`user_guide_deployment_after_import`.

API reference
-------------

:doc:`api_opus_config`, :doc:`api_opus_log_analyzer`
