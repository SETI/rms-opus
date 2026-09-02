.. _user_guide_installation:

Installing OPUS on a Server
===========================

This chapter brings a complete OPUS server up from nothing.

**Almost none of it is done by hand.** The distribution ships the scripts that install
OPUS, import the holdings and deploy the result, and ``opus_deploy_scripts`` writes them
onto the server. What you do by hand is create one virtual environment, write them out,
and fill in one file of settings; the scripts do the rest, and they are the same scripts
that upgrade the server afterwards.

There is nothing to clone and nothing to build. Every installation the scripts create is
a virtual environment with the released ``rms-opus`` distribution in it, from PyPI.

For a **development checkout** rather than a server, read :ref:`dev_guide_environment`
instead; it is shorter, and it installs from source.

.. _user_guide_installation_shape:

How a server is put together
----------------------------

``/opt/opus`` throughout this guide is **the location it recommends, not one OPUS
requires**: nothing in OPUS or in the scripts has a built-in path. The installation root
is whatever ``OPUS_DIR`` in ``deploy.env`` says, the deploy directory is wherever you
write the scripts out, and either can be anywhere the OPUS account can read and write --
``/srv/opus``, ``/var/lib/opus``, a mounted volume. Substitute your own throughout, or
keep these if you have no reason to prefer another.

Two directories, and neither is inside the other's business.

**The deploy directory** holds the scripts and the settings they read. It is written by
``opus_deploy_scripts``, it is not an OPUS installation, and nothing a deploy does
replaces it::

    /opt/opus/deploy/
        README.txt                     the short version of this chapter
        CHAIN_VERSION                  the release these scripts came from
        deploy.env.template            the settings file to copy
        secrets/deploy.env             ... and your filled-in copy, mode 0600
        import_and_deploy/*.sh         the import and the two deploys
        database/*.sh                  copying a database to a second server
        log_analyzer/*_template        cron templates for the log reports

**The installation root** holds what the scripts build. Every deploy creates a complete
new installation and switches to it; nothing is ever upgraded in place::

    /opt/opus/staged/<database>_<timestamp>/
        opus_venv/                 a virtualenv with the released rms-opus in it
        opus.toml                  this installation's configuration, mode 0600
        wsgi.py                    symlink to the wsgi module inside opus_venv
    /opt/opus/deployed  -> staged/<database>_<timestamp>    what the web server serves
    /opt/opus/import    -> staged/<database>_<timestamp>    what an import is using
    /opt/opus/opus_logs/       the web application's log
    /opt/opus/import_logs/     one directory per import run
    /opt/opus/downloads/       zipped cart files, and
    /opt/opus/manifests/       their manifests
    /opt/opus/static_media/    where collectstatic gathers the static files

That shape follows from one fact about OPUS: **a release that changes the table schemas
cannot read a database an earlier release imported.** Every OPUS table is created by the
import pipeline from the JSON schemas that ship with a release, so the code and the
database it built have to move together. A deploy that upgraded the running installation
would serve one release's code against another release's database for as long as it took
to finish; instead, the new installation is built beside the running one, and the switch
is a single rename of the ``deployed`` symlink.

It also means the previous installation is still on disk after a deploy, so going back is
another switch rather than a rebuild. :ref:`user_guide_deployment` is the full account.

.. _user_guide_installation_prereqs:

Prerequisites
-------------

All of these are the machine's, installed before OPUS is. The only Python packages you
install by hand are in :ref:`the next section <user_guide_installation_bootstrap>`, into a
virtual environment created there; every other Python package a server needs is installed
by the scripts, into the installations they build.

**Python 3.12 or later.** Each installation's virtual environment is built with
``python3.12`` unless ``deploy.env`` names another one in ``OPUS_PYTHON``.

**MySQL 8.0.19 or later**, with a user allowed to create and drop databases and tables.
The import pipeline creates every OPUS table itself -- and creates the schema, if it does
not exist -- and it writes its multi-row upserts with the ``AS new`` row alias that
8.0.19 added. See :ref:`dev_guide_import_db_importdb` for why that is the floor.

**The MySQL client development headers**, because the ``mysqlclient`` driver ships no
Linux wheel and is compiled during every install. On Debian or Ubuntu::

    sudo apt-get install pkg-config default-libmysqlclient-dev build-essential

**git**, because one of OPUS's dependencies is installed from its repository rather than
from PyPI: OPUS is developed against the ``rewrite`` branch of ``rms-pdsfile``, which is
what reads the holdings, and ``pip`` clones it while installing. Every installation the
deploy scripts build does this, so ``git`` is needed on the server and not only where a
checkout is::

    sudo apt-get install git

**A Unix account for OPUS**, which the web server's workers run as and which every deploy
script has to be run as. Everything a deploy creates belongs to whoever ran it, including
an ``opus.toml`` at mode 0600, so a deploy run as anyone else -- root, most easily --
builds an installation the web server cannot read. The scripts refuse rather than letting
that reach the switch. That account also needs ``sudo`` for three ``systemctl`` commands:
the switch stops the web server, restarts the cache, and starts the web server again.

This is an example of making one, on a system with ``useradd``, and of checking the
result -- ``useradd`` says nothing at all when it succeeds::

    sudo useradd --system --create-home --shell /bin/bash opus
    id opus

``opus`` is the name this guide uses, and ``OPUS_USER`` in ``deploy.env`` is what says
which account you actually chose. It needs a **shell**, because the deploys are run as
it, and a **home directory**, because ``pip`` writes a cache into one. An account that
already exists is fine: ``useradd`` will say so and change nothing.

**A web server.** :ref:`user_guide_web_server` has worked configurations for Apache with
``mod_wsgi`` and for nginx in front of gunicorn or uWSGI. Under Apache, the deploy runs
``pip install mod-wsgi`` inside each installation it builds, which compiles against
Apache's own headers::

    sudo apt-get install apache2 apache2-dev

**memcached**, strongly recommended. It is the cache several worker processes answer
from, and emptying it is how a deploy stops the new database being described by results
computed against the old one. Install the **daemon** here; the scripts install its
``pymemcache`` client into every installation they build::

    sudo apt-get install memcached libmemcached-tools

Without memcached running, OPUS falls back to Django's per-process local-memory cache: it
works, more slowly, and the cache-emptying step of a deploy has nothing shared to empty.
:ref:`dev_guide_webapp_running` describes the fallback and its one sharp edge.

Nothing else is needed to install it. **Later**, once the site is serving, this is how to
watch the cache being used -- the counters once a second, with what changed highlighted,
which is how you see requests being answered from it and a deploy emptying it::

    watch -n1 -d 'memcstat --servers localhost'

``memcstat`` comes from ``libmemcached-tools`` rather than from ``memcached``, which is
why the install line above takes both packages.

**wkhtmltopdf**, only for the help pages' PDF downloads. Every other page works without
it, and nothing else in OPUS uses it. It has to be a build **with patched Qt**: the pages
are rendered with a page-number footer, which is one of the features a build against the
system Qt does not have, so a distribution package fails on the request rather than
producing a plainer PDF. That is what a machine has to say for itself::

    $ wkhtmltopdf --version
    wkhtmltopdf 0.12.4 (with patched qt)

**Install it from the project's own release rather than from the distribution**, whose
package is the unpatched build. These are the binaries the Node runs, for Linux on
x86-64::

    cd /tmp
    wget https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.4/wkhtmltox-0.12.4_linux-generic-amd64.tar.xz
    tar xvf wkhtmltox-0.12.4_linux-generic-amd64.tar.xz
    sudo mv wkhtmltox/bin/wkhtmlto* /usr/bin/

The download and the unpacked ``wkhtmltox/`` are left behind in ``/tmp``, which is where
they can be deleted or ignored; only what was moved to ``/usr/bin`` is installed. The
glob takes ``wkhtmltoimage`` along with ``wkhtmltopdf``; they ship together, and the one
the help pages call ends up on the path either way. 0.12.4 is the release the Node runs. The project is archived, so that releases page is a fixed list rather than a moving
one; a later release from it does as well, as long as ``--version`` says patched.

**The PDS holdings**, mounted read-only. The import needs them to run at all; the web
application needs them to serve product files. Both a PDS3 and a PDS4 root are
configured, and the scripts check that ``volumes/`` exists under the first and
``bundles/`` under the second before doing anything.

**A mail transport**, only if you want the import to mail its log when it finishes. An
import runs for hours or days detached, so that mail is how anyone finds out it ended.
Without one, leave ``OPUS_IMPORT_MAIL_TO`` empty and read the log where it was written.

.. _user_guide_installation_bootstrap:

Step 1: the environment the scripts come from
---------------------------------------------

The deploy scripts are part of ``rms-opus``, so installing them means installing the
distribution once, by hand, into an environment of its own::

    # The installation root has to exist and belong to the OPUS account. Everything
    # underneath it, the scripts create.
    sudo install -d -o opus -g opus -m 755 /opt/opus

    # From here on, everything is run as that account.
    sudo -u opus -i

    python3.12 -m venv /opt/opus/deploy_venv
    source /opt/opus/deploy_venv/bin/activate
    python -m pip install --upgrade pip
    python -m pip install "rms-opus==3.24.0"

``opus`` there is the account from the prerequisites, and ``3.24.0`` the release you are
deploying.

**This environment does not serve anything.** It exists so that the scripts have commands
to run; the installations that serve and import are built by the scripts under
``staged/``. Its path is what ``OPUS_DEPLOY_VENV`` names in ``deploy.env`` below, and
every script activates it for itself -- so a deploy runs the same way from a shell, from
``cron`` and under ``nohup``, and this is the only time it is activated by hand.

Installing the distribution puts these commands on the path. The deploy scripts run most
of them for you; they are listed because the scripts' output names them, and because a
partial import or a one-off report is run directly:

.. list-table::
   :header-rows: 1
   :widths: 32 68

   * - Command
     - What it does
   * - ``opus_deploy_scripts``
     - Writes out the deploy chain. The next step.
   * - ``opus_import``
     - The import pipeline: reads the PDS holdings and builds the OPUS database.
   * - ``opus_import_all``
     - Runs a whole full-holdings import: every bundle set, in order, and the steps
       that finish the database. This is what an import deploy runs.
   * - ``opus_manage``
     - Administers the web application -- creating its tables, gathering its static
       files, and checking that its configuration works. A deploy runs it too.
   * - ``opus_config_template``
     - Writes out the annotated template of the file OPUS itself reads. On a server the
       deploy generates that file, so this is for reading rather than for filling in;
       see :ref:`user_guide_installation_configuring`.
   * - ``opus_log_analyzer``
     - Turns the web server's access logs into reports on how the site is being used.
   * - ``opus_error_analyzer``
     - The same for the error log.

Every one of them, except ``opus_config_template`` and ``opus_deploy_scripts``, reads the
configuration file named by ``OPUS_CONFIG``. The scripts export it; running one of these
commands yourself means naming the installation whose configuration you mean.

.. _user_guide_installation_scripts:

Step 2: writing out the deploy scripts
--------------------------------------

::

    opus_deploy_scripts --directory /opt/opus/deploy

That writes the scripts, a ``deploy.env.template`` to copy in the next step, a
``CHAIN_VERSION`` file recording the release they came from, and a plain-text
``README.txt`` holding the short version of this chapter -- so the instructions are
beside the scripts on the server, readable with ``less``, rather than only here.

**Write them outside every installation, and run them from there.** A deploy installs a
new ``rms-opus``, and these scripts are part of ``rms-opus``: a copy living inside an
installation being replaced would be rewritten while bash was still reading it. The
filled-in settings go beside them for the same reason -- credentials do not belong in a
directory a deploy replaces.

Being part of the distribution, the chain *changes* with it. Upgrading a server therefore
starts by bringing this directory up to the release being deployed, with one of the
scripts it contains -- :ref:`the first command of every upgrade
<user_guide_deployment_refresh>`.

.. _user_guide_installation_deploy_env:

Step 3: ``deploy.env``, the one file you fill in
------------------------------------------------

Everything about *this* server is in one file: where to install, which account to run as,
which database to connect to and as whom, where the holdings are, what the site calls
itself, and what to do with a finished database. Nothing in the scripts assumes a value
for any of it -- no host name, no URL, no path -- so the same chain runs on any server
that fills this in.

::

    cd /opt/opus/deploy
    install -d -m 700 secrets
    install -m 600 deploy.env.template secrets/deploy.env
    # ... then fill in every <PLACEHOLDER>.

**Both modes are set as the thing is created rather than afterwards**, and ``install``
rather than ``mkdir`` and ``cp`` is what does that: ``mkdir`` applies the caller's umask,
so under a permissive one the directory is created world-writable. The scripts read this
file with ``source``, i.e. they *run* it as shell code with the deploy account's
privileges, so another local account able to write it is another local account running
your deploys. It holds a database password and Django's secret key, and ``secrets/`` is
git-ignored.

It is shell syntax: ``VAR=value``, no spaces around the ``=``, and quote any value
containing a space.

.. list-table::
   :header-rows: 1
   :widths: 34 66

   * - Variable
     - Meaning
   * - ``OPUS_DIR``
     - The installation root: any directory the OPUS account owns, ``/opt/opus`` in this
       chapter. It has to exist; the scripts create everything underneath it.
   * - ``OPUS_DEPLOY_VENV``
     - The environment from step 1, which the scripts' own commands come from. Every
       script activates it for itself. It is not one of the installations under
       ``staged/``: those are what a deploy builds, and it deactivates this one before
       activating the installation it has just built.
   * - ``OPUS_USER``
     - The Unix account OPUS runs as, and the account every script has to be run as.
       Everything a deploy creates belongs to whoever ran it, including an ``opus.toml``
       at mode 0600, so a deploy run as anyone else builds an installation the web
       server cannot read. The scripts refuse rather than letting that reach the switch.
   * - ``OPUS_DB_HOST``
     - The MySQL server this installation connects to, usually ``localhost``.
   * - ``OPUS_DB_USER``, ``OPUS_DB_PASSWORD``
     - The MySQL account the import pipeline and the web application connect as. It
       needs most privileges, including creating and dropping tables.
   * - ``OPUS_SECRET_KEY``
     - Django's signing key: unique to this server, and secret.
   * - ``PDS3_HOLDINGS_DIR``, ``PDS4_HOLDINGS_DIR``
     - The two holdings roots. The scripts check that ``volumes/`` and ``bundles/``
       exist under them.
   * - ``LAST_BLOG_UPDATE_FILE``, ``NOTIFICATION_FILE``
     - The two files of site content the interface displays. Neither has to exist -- an
       absent one means there is nothing to show.
   * - ``OPUS_DEBUG``
     - Django's ``DEBUG``, as the unquoted ``true`` or ``false`` TOML wants. ``false``
       on anything reachable from outside the machine; a staging server is the case for
       ``true``.
   * - ``OPUS_ALLOWED_HOSTS``
     - Every name and address this installation answers to, separated by spaces. Django
       refuses a request whose ``Host`` header is not among them, so a name a proxy or a
       health check reaches it by belongs here as much as the public one -- and so do
       ``127.0.0.1`` and ``localhost``, which is how a smoke test from the server itself
       arrives.
   * - ``OPUS_CACHE_PREFIX``
     - The prefix on this installation's keys in the shared cache. Two installations
       sharing one memcached need different prefixes, or each reads the other's answers.
   * - ``OPUS_PUBLIC_URL``, ``OPUS_PRODUCT_HTTP_PATH``, ``OPUS_VIEWMASTER_URL``,
       ``OPUS_TAR_FILE_URL``
     - What the site calls itself and where it serves things from. They appear in what
       the API returns, so they are the URLs a user's browser has to be able to reach
       rather than any internal address. The last one is joined directly to a file name
       and needs a trailing slash.
   * - ``OPUS_DB_DUMP_DIR``
     - *Optional.* Where ``mysqldump`` writes a finished database, and where the load
       reads it back. **Empty means an import does not dump at all** -- a dump of the
       full holdings is tens of gigabytes and hours of writing, so it happens because
       this names a directory. On two servers that copy databases to each other, a
       directory both can see.
   * - ``OPUS_PYTHON``
     - *Has a default.* The Python each installation's virtualenv is built with,
       ``python3.12`` unless this names another. ``python3`` is whatever the machine
       calls its system Python, which may be older than OPUS supports, so the
       interpreter is named rather than assumed.
   * - ``OPUS_WEB_SERVICE``
     - *Has a default.* The systemd unit running the application's workers, stopped for
       the switch at the end of a deploy and started again after it. ``apache2`` unless
       this names another -- ``httpd`` on Red Hat, or whatever a gunicorn or uWSGI unit
       is called.
   * - ``OPUS_CACHE_SERVICE``
     - *Has a default.* The systemd unit holding the shared cache, restarted after the
       switch to empty it. ``memcached`` unless this names another; **empty** if there
       is no shared cache, which skips the restart.
   * - ``OPUS_PEER_DB_HOST``
     - *Optional.* The MySQL server a finished database is copied to. With a host here,
       an import ends by dumping what it built and loading it there; empty, the dump
       stays where it was written. It needs ``OPUS_DB_DUMP_DIR``, because the load
       reads what the dump wrote, and a peer with nowhere to dump to is refused before
       the import rather than after it.
   * - ``OPUS_IMPORT_MAIL_TO``
     - *Optional.* Where to mail the log when an import finishes. Empty sends nothing
       and leaves the log where it was written.

Two checks run before a deploy touches anything, and both name the variable at fault:
``_read_deploy_env.sh`` refuses a required variable that is missing, **empty**, or still
the ``<PLACEHOLDER>`` the template ships -- emptiness as well as absence, because nothing
downstream objects to an empty value, and Django starts perfectly well with no secret key
-- and it refuses to run as any account but ``OPUS_USER``.

.. _user_guide_installation_full_import:

Step 4: the first import
------------------------

::

    cd /opt/opus/deploy
    ./import_and_deploy/run_full_opus_import.sh ==3.24.0

That one command builds an installation of that release under ``staged/``, points the
``import`` symlink at it, and imports the whole archive into a database of its own named
for the moment it started. It runs **detached**, and prints the log file it is writing
to; with ``OPUS_IMPORT_MAIL_TO`` filled in, it mails that log when it ends.

A full-holdings import is **hours to days**. What it runs is ``opus_import_all``, the
installed command: every bundle set in order -- Galileo and New Horizons first, while the
tables are small, because their bundles carry observations that appear in more than one
-- then the rest in roughly decreasing order of how long each takes, and finally the
three steps that finish the database, the auxiliary tables, the dictionary and the
validation. The order lives in the release being installed rather than in the scripts, so
it cannot disagree with the code importing.

The argument is a **PEP 440 version specifier** appended to the distribution name:
``==3.24.0`` for a particular release, omitted for the newest. Give this step and step 5
the same one -- they install ``rms-opus`` separately, so leaving it off both means "the
newest release" twice, which is two different releases if one is published in between.

**Read the log rather than the exit status.** Several import steps report a failure
through the log and still exit zero, so a clean run is an empty ``ERRORS.log``::

    ls /opt/opus/import_logs/          # one directory per run, newest last
    cat /opt/opus/import_logs/<run>/ERRORS.log
    cat /opt/opus/import_logs/<run>/WARNINGS.log

:ref:`dev_guide_import_verifying` is the longer account of what to look for. The database
the run built is named by the installation ``import`` now points at::

    basename "$(readlink /opt/opus/import)"

**These scripts import the whole archive.** There is no partial-import option in them:
what they run is ``opus_import_all``, which imports every bundle set. A site that wants
only part of it -- Cassini and nothing else -- runs the pipeline directly instead, and
then deploys the database that produced::

    # A configuration of your own, naming a database of your own. This is the one
    # case where opus.toml is written by hand on a server; the deploy generates the
    # one the site actually serves from.
    opus_config_template
    install -m 600 opus.toml.template /opt/opus/partial.toml
    # ... fill it in: schema = "opus3_cassini", and the same paths deploy.env names.

    OPUS_CONFIG=/opt/opus/partial.toml opus_import --do-it-all CASSINI
    OPUS_CONFIG=/opt/opus/partial.toml opus_import --cleanup-aux-tables
    OPUS_CONFIG=/opt/opus/partial.toml opus_import --import-dictionary
    OPUS_CONFIG=/opt/opus/partial.toml opus_import --validate-perm

    # Then step 5 as usual, naming that database.
    ./import_and_deploy/deploy_new_code_and_database.sh opus3_cassini ==3.24.0

What ``--do-it-all`` takes is a *descriptor*, and several can be given, comma- or
space-separated: a bundle id (``COISS_2002``), a whole bundleset (``COISS_2xxx``), one of
the shorthands for a mission or an instrument (``CASSINI``, ``GALILEO``, ``HST``,
``VOYAGER``, ``NH``, ``COISS``, ``COUVIS`` and their relatives, matched without regard to
case), or ``ALL``. The three steps after it are what finishes a database, and a direct
invocation is the one path that does not run them for you. ``opus_import --help`` lists
every option and works without a configuration file; :ref:`dev_guide_import_running` is
the complete reference.

.. _user_guide_installation_first_deploy:

Step 5: the first deploy
------------------------

::

    ./import_and_deploy/deploy_new_code_and_database.sh opus3_20260902T031500_12345 ==3.24.0

The argument is the database from step 4. This builds the installation that will serve --
its own virtualenv, its own ``rms-opus``, a generated ``opus.toml`` naming that database,
and the ``wsgi.py`` symlink -- creates the web application's own tables, gathers the
static files, rebuilds the dictionary and the auxiliary tables, and only then switches:
the ``deployed`` symlink is moved onto it with a single rename, the cache is emptied, and
the workers are started again. **The workers are stopped for that switch alone**, not for
the build, so the site goes on serving what it was serving until the moment it changes.

It asks for your ``sudo`` password at the start rather than at the end, so that a build
does not sit waiting on a prompt nobody is watching.

Step 6: the web server
----------------------

Point a web server at ``/opt/opus/deployed/wsgi.py``, once. Every later deploy moves that
symlink rather than the web server's configuration, so this is the one step that is never
repeated. :ref:`user_guide_web_server` has the worked Apache and nginx configurations,
and the three things any of them has to arrange.

.. _user_guide_installation_smoke:

Checking the installation
-------------------------

Four checks, in increasing order of what they prove::

    # 1. The deploy switched. This is what the web server is serving.
    readlink /opt/opus/deployed

    # 2. The configuration that installation generated is valid, and the database it
    #    names can be opened. --database default is what opens the connection.
    OPUS_CONFIG=/opt/opus/deployed/opus.toml \
        /opt/opus/deployed/opus_venv/bin/opus_manage check --database default

    # 3. The application starts under a WSGI server. gunicorn is not an OPUS
    #    dependency -- install it into that installation for this check, or use
    #    whichever server you deploy.
    /opt/opus/deployed/opus_venv/bin/python -m pip install gunicorn
    OPUS_CONFIG=/opt/opus/deployed/opus.toml \
        /opt/opus/deployed/opus_venv/bin/gunicorn --bind 127.0.0.1:8001 \
        opus_app.wsgi:application

    # 4. It answers, with data. 127.0.0.1 has to be in OPUS_ALLOWED_HOSTS, or Django
    #    replies 400 however well the application and the database are working.
    curl -s 'http://127.0.0.1:8001/api/meta/result_count.json?planet=Saturn'

The same four run against a staged installation that is not deployed yet -- substitute
``staged/<that installation>`` for ``deployed`` -- which is how a new database is
exercised before the public site is switched to it. See
:ref:`user_guide_deployment_runbook`.

If the third fails on an import error rather than a configuration one, the usual cause is
that ``OPUS_CONFIG`` did not reach the process; see :ref:`user_guide_web_server`.

.. _user_guide_installation_configuring:

The configuration file OPUS reads
---------------------------------

OPUS itself reads one TOML file, named by the ``OPUS_CONFIG`` environment variable, and
there is **no default location** for it: a machine hosting several installations gives
each one its own file, and a process that guessed would quietly serve or overwrite a
neighbour's database.

**On a server the deploy writes that file**, one per installation, from the ``deploy.env``
values above, at mode 0600 inside the installation it belongs to. So this section is here
to be read rather than filled in: **do not hand-edit ``opus.toml`` on a deployed server**,
because the next deploy generates it again. Change ``deploy.env`` and run a deploy.

The four tables below are what a generated file contains, and what OPUS validates as it
reads it: an unknown key, a missing key, or a value of the wrong type is reported with
the table and the key at fault rather than failing later somewhere else. A misspelled key
is an **error**, not something silently ignored. A key marked optional may be left out
entirely.

``[database]``
~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 22 14 64

   * - Key
     - Required
     - Meaning
   * - ``brand``
     - optional
     - ``"MySQL"`` or ``"PostgreSQL"``; only MySQL is implemented. Default ``"MySQL"``.
       It selects both the import pipeline's backend and the Django database engine, so
       the two cannot disagree.
   * - ``host``
     - yes
     - The host the OPUS schema lives on. From ``OPUS_DB_HOST``.
   * - ``database``
     - optional
     - MySQL ignores this and connects to ``schema`` instead. Default ``""``.
   * - ``schema``
     - yes
     - The namespace the OPUS tables live in -- the database name under MySQL. It is
       also part of every cache key. **This is the key that says which database an
       installation serves**, and it is what a code-only deploy reads out of the
       installation it is replacing.
   * - ``user``, ``password``
     - yes
     - The database account, from ``OPUS_DB_USER`` and ``OPUS_DB_PASSWORD``.

``[paths]``
~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 26 12 62

   * - Key
     - Required
     - Meaning
   * - ``pds3_holdings``, ``pds4_holdings``
     - yes
     - The roots of the two holdings trees.
   * - ``opus_log_file``
     - yes
     - The file the web application logs to. **Its directory must already exist**: the
       application opens the file during startup, so a missing directory stops it rather
       than degrading it. The deploy creates ``opus_logs/`` under ``OPUS_DIR``.
   * - ``import_log_dir``
     - yes
     - Where the import pipeline writes ``WARNINGS.log`` and ``ERRORS.log``. Must exist.
       An import deploy makes a directory per run under ``import_logs/``.
   * - ``tar_dir``, ``manifest_dir``
     - yes
     - Where zipped cart files and their manifests are built. Both are joined directly
       to a file name, so **both need a trailing slash**.
   * - ``last_blog_update_file``, ``notification_file``
     - yes
     - Two files of site content maintained outside the repository. Neither has to exist
       -- an absent one simply means there is nothing to show.
   * - ``static_root``
     - **optional**
     - Where ``collectstatic`` gathers the static files. A development installation
       leaves it out, because it never runs ``collectstatic``, and Django's own default
       applies. A deploy always sets it.
   * - ``opus_static_root``
     - yes
     - Where the help pages' PDF renderer reads assets from. On a server this is the
       same directory as ``static_root``; in a development installation it points into
       the checkout.

``[django]``
~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 12 58

   * - Key
     - Required
     - Meaning
   * - ``secret_key``
     - yes
     - Django's signing key. It must be unique to this installation and secret.
   * - ``debug``
     - yes
     - **Never true on anything reachable from outside the machine.**
   * - ``allowed_hosts``
     - yes
     - The hosts and addresses Django will serve, as an array. The generator builds it
       from the space-separated ``OPUS_ALLOWED_HOSTS``.
   * - ``cache_server_prefix``
     - yes
     - Prepended to every cache key, which is what lets several OPUS installations share
       one memcached without colliding.
   * - ``public_url``
     - yes
     - This installation's public URL, used by the citation page.
   * - ``product_http_path``
     - yes
     - The root URL data products are retrieved from.
   * - ``viewmaster_url``
     - yes
     - The root URL of the Node's file browser, which the Details tab links into.
   * - ``tar_file_url``
     - yes
     - The root URL zipped cart files are retrieved from. Joined directly to a file
       name, so it **needs a trailing slash**.
   * - ``log_file_level``, ``log_console_level``
     - optional
     - Defaults ``"INFO"``.
   * - ``log_django_level``
     - optional
     - Default ``"WARNING"``.
   * - ``log_api_calls``
     - optional
     - A level name to log every API call at, or false. Default false.
   * - ``fake_api_delays``
     - optional
     - Fault injection; see :ref:`dev_guide_webapp_running`. A generated file never
       contains it.
   * - ``fake_error404_probability``, ``fake_error500_probability``
     - optional
     - The same. Defaults 0.

``[import]``
~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 26 12 62

   * - Key
     - Required
     - Meaning
   * - ``table_temp_prefix``
     - optional
     - The prefix of the import namespace's tables. Default ``"imp_"``. See
       :ref:`dev_guide_import_two_namespaces`.
   * - ``log_file``, ``debug_log_file``
     - yes
     - The import pipeline's own logs. Their directory must already exist.

Where to go next
----------------

:ref:`user_guide_web_server`
    Putting Apache or nginx in front of it.

:ref:`user_guide_deployment`
    Upgrading the server, replacing the database, and what must always happen after an
    import.

:ref:`dev_guide_import_running`
    Every import option.

The whole template
------------------

``opus_config_template`` writes this file, and it is what a generated ``opus.toml`` is a
filled-in version of. It documents every key, and it is reproduced here -- included from
the distribution rather than retyped, so the two cannot drift -- so that the file can be
read before anything is installed. A **development** installation is where you copy and
fill it in by hand; see :ref:`dev_guide_environment`.

.. literalinclude:: ../src/opus_config/opus.toml.template
   :language: toml
   :caption: opus.toml.template

API reference
-------------

:doc:`api_opus_config`, :doc:`api_opus_import`
