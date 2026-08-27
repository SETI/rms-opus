.. _dev_guide_deployment:

Deployment
==========

This chapter describes what a running OPUS installation consists of and how each part
is brought up. It covers a development installation on one machine and, from
:ref:`deployment_server` onward, the Node's production arrangement.

Prerequisites
-------------

* **MySQL 8**, with a user allowed to create and drop databases -- the import pipeline
  creates every OPUS table itself.
* **memcached**, plus the ``pymemcache`` Python client. **Neither is a declared
  dependency**: :mod:`opus_app.settings` tries to import ``pymemcache`` and falls back
  to Django's local-memory cache when it is absent, so an installation that skips this
  step runs -- slowly, per process, and with the cache-flushing step below doing
  nothing at all. Install both deliberately::

      sudo apt-get install memcached libmemcached-tools
      pip install pymemcache
      # watch it while OPUS runs:
      watch -n1 -d 'memcstat --servers localhost'

  ``memcstat`` is in ``libmemcached-tools``, not in ``memcached``.

* **The MySQL client development headers**, because ``mysqlclient`` is compiled
  during the install::

      sudo apt-get install pkg-config default-libmysqlclient-dev build-essential

* **wkhtmltopdf**, only for the help pages' PDF downloads. Every other page works
  without it.
* **The PDS holdings**, mounted read-only, for the import pipeline.

Installing
----------

::

    python3 -m venv venv
    source venv/bin/activate
    pip install rms-opus

A development installation uses an editable install of a checkout instead; see
:ref:`dev_guide_environment`.

Dependencies are declared in ``pyproject.toml`` with **floors, not pins** -- only
``django`` carries an upper bound, because 5.2 is the LTS this application targets. There
is no lock file: a fresh install resolves each dependency to its newest compatible
release. To reproduce one installation exactly on another machine, generate a constraints
file from a known-good one and install against it::

    # on the known-good installation
    python -m pip freeze > constraints.txt

    # on the new one
    pip install rms-opus -c constraints.txt

Nothing in the deploy chain maintains such a file; it is there for the case where ops
wants a reproducible install rather than the newest one.

Configuring
-----------

Copy ``opus.toml.template``, fill in every ``<PLACEHOLDER>``, and export
``OPUS_CONFIG`` in the environment of **every** OPUS process -- the WSGI server, the
import pipeline, and any management command::

    curl -fsSLO https://raw.githubusercontent.com/SETI/rms-opus/main/opus.toml.template
    cp opus.toml.template /etc/opus/opus.toml
    export OPUS_CONFIG=/etc/opus/opus.toml

The template is **repository** infrastructure and is deliberately not inside the wheel:
nothing in the code reads it, and shipping it would mean extracting it through
``importlib.resources`` instead of opening a file. A ``pip``-installed server therefore
fetches it as above, or copies it from a checkout. (``-f`` is load-bearing: without it
``curl`` exits 0 on a 404 and writes the error page into the file the next line copies.)

There is no default location for the file. A server running several OPUS
installations gives each one its own file, its own ``OPUS_CONFIG``, its own database
schema and its own ``cache_server_prefix``, which is what keeps them from colliding in
the shared memcached.

That is the hand-built case. On the Node's own servers the deploy chain writes
``opus.toml`` itself, from a separate file; see :ref:`deployment_server`.

Set ``debug = false`` and a real ``secret_key`` on any installation that is reachable
from outside the machine, and make sure every directory the ``[paths]`` section names
exists and is writable by the user OPUS runs as. The web application opens its log
file during startup, so a missing log directory stops the application rather than
degrading it.

Creating the database
---------------------

Django's own contrib tables -- sessions, auth, content types, admin -- come from a
migration::

    OPUS_CONFIG=/etc/opus/opus.toml \
    DJANGO_SETTINGS_MODULE=opus_app.settings \
    django-admin migrate

Every OPUS table comes from an import instead, so there are no OPUS migrations to run
and none to write::

    OPUS_CONFIG=/etc/opus/opus.toml opus_import --do-it-all COISS_2002

``--do-it-all`` imports the named bundles, copies the result over the permanent
tables, and rebuilds the auxiliary tables. :mod:`opus_import.cli` documents the
individual steps, and ``scripts/import/`` holds the wrappers the Node uses:
``import_all.sh`` for a full production import, ``import_for_tests.sh`` for the fixed
bundle list the integration suite runs against, and ``clone_database.sh`` to copy a
database.

Collecting static files
-----------------------

On a server, Django's ``collectstatic`` gathers the JavaScript, CSS and images into
one directory that the web server serves directly::

    OPUS_CONFIG=/etc/opus/opus.toml \
    DJANGO_SETTINGS_MODULE=opus_app.settings \
    django-admin collectstatic --noinput

``--noinput`` is what the deploy scripts pass: ``collectstatic`` asks for confirmation
before overwriting, and a deploy has nobody to ask.

``static_root`` in the configuration is where they go; a development installation
leaves it out, because it never runs ``collectstatic``, and Django's own default
applies.

``opus_static_root`` is a different thing and is easy to confuse with it: it is the
directory the help pages' PDF renderer reads assets out of, and on a server it is the
same directory as ``static_root``. In a development installation it points at
``.../src/opus_app/static``.

The public URL prefix is ``/static_media/`` either way, which is long-standing and
deliberate.

Running the application
-----------------------

Production serves :mod:`opus_app.wsgi` through Apache and ``mod_wsgi``. The vhost
needs ``WSGIScriptAlias`` pointing at the installed ``opus_app/wsgi.py``, and it needs
``OPUS_CONFIG`` in the WSGI process's environment -- ``WSGIDaemonProcess`` does not
inherit the shell's.

The installed module lives inside the virtual environment's ``site-packages``, whose
path contains the Python minor version, so naming it directly in the vhost means
editing the vhost after every Python upgrade. On the Node's servers the deploy chain
avoids that by writing a symlink to it at a fixed path and re-pointing that symlink on
every deploy; see :ref:`deployment_server` for the path and the stanza.

Any other WSGI server works the same way; ``gunicorn opus_app.wsgi:application`` is
enough for a smoke test. For development, ``python manage.py runserver`` serves the
site at ``http://127.0.0.1:8000/opus/``.

.. _deployment_server:

The Node's production arrangement
---------------------------------

``scripts/server/import_and_deploy/`` holds the scripts that deploy a new database or
a new release on the Node's servers.

**A deployed installation is not a checkout.** It is a directory holding a virtual
environment with the released ``rms-opus`` distribution installed from PyPI, the
``opus.toml`` that installation reads, and the ``wsgi.py`` symlink Apache points at.
Nothing on the server builds from source. The one checkout a server keeps is the one
holding these scripts, which is also where ``deploy.env`` lives.

The layout makes the served directory a symbolic link to a per-database directory, so
that swapping databases is a link change rather than a copy:

::

    /opus/src/rms-opus            -> rms-opus_<database name>
    /opus/src/rms-opus_<database name>/
        opus_venv/                # the virtual environment; rms-opus is installed here
        opus.toml                 # this installation's configuration, mode 0600
        wsgi.py                   # symlink into opus_venv/.../site-packages/opus_app/

``wsgi.py`` is the fixed path the vhost names, so it survives both a release upgrade
and a Python upgrade::

    WSGIScriptAlias / /opus/src/rms-opus/wsgi.py
    WSGIDaemonProcess opus python-home=/opus/src/rms-opus/opus_venv
    WSGIProcessGroup opus

``OPUS_CONFIG`` has to reach that daemon process, and **the deploy scripts' export does
not**: they run in a shell, and Apache starts from init. mod_wsgi has no directive for
per-process environment variables either, so ``SetEnv`` in the vhost will not do it --
that populates the WSGI *request* environ, long after ``opus_app.wsgi`` has imported
settings. What works is putting it in the environment Apache itself starts with. On
Debian and Ubuntu ``apache2ctl`` sources ``/etc/apache2/envvars`` before starting the
server, and daemon processes inherit from there::

    # /etc/apache2/envvars
    export OPUS_CONFIG=/opus/src/rms-opus/opus.toml

A server running several OPUS installations cannot share one such variable; give each
its own Apache instance, or set the variable from a wrapper ``wsgi.py`` of its own that
assigns ``os.environ['OPUS_CONFIG']`` before importing :mod:`opus_app.wsgi`.

``deploy_new_code_and_database.sh <database name> [<version spec>]`` stops Apache and
memcached, builds a new installation directory with that release in it, writes its
``opus.toml``, moves the link, then migrates, collects static files and imports the
dictionary, and starts Apache and memcached again.

``deploy_new_code_only.sh [<version spec>]`` upgrades the existing installation in place
with ``pip install --upgrade`` instead, reusing its ``opus.toml`` because only a full
deploy knows which database to name in one.

The optional argument of both is a **PEP 440 version specifier** appended to the
distribution name -- ``==3.23.0`` for a particular release, omitted for the newest. It
used to be a git branch name; there is no branch to choose any more.

``deploy_new_code_only.sh`` refuses to run against anything that is not an installation
this chain created -- a git checkout at that path, a missing ``opus_venv``, or a missing
``opus.toml`` -- and names the full deploy as the way across. That refusal is what
carries a server over from the pre-pip arrangement: the first deploy after this change
has to be ``deploy_new_code_and_database.sh``, which builds the installation from
nothing.

``run_full_opus_import.sh`` runs a complete import into a new database, which is the
first half of bringing up a new one.

``scripts/server/database/`` holds the dump and load scripts used to move a database
between machines.

Deploy configuration
~~~~~~~~~~~~~~~~~~~~

The deploy chain has its own configuration, separate from the application's, and the
separation is deliberate:

``scripts/server/secrets/deploy.env``
    Shell syntax, read by the scripts **before any OPUS code exists on the machine**.
    It says where to install, which database credentials to use, where the PDS holdings
    are, and what Django's secret key is. Copy ``scripts/server/deploy.env.template``,
    fill in every ``<PLACEHOLDER>``, and ``chmod 600`` it; the directory is git-ignored.

``opus.toml``
    Read by the installed application and the import pipeline at run time.
    ``_write_opus_toml.sh`` **generates it** per installation from the values above, and
    the deploy exports ``OPUS_CONFIG`` pointing at it. On a Node server, do not
    hand-write this file from ``opus.toml.template`` as the section above describes: the
    next deploy overwrites it. Change ``deploy.env`` instead.

``_read_deploy_env.sh`` refuses to continue if any value is missing, empty, or still the
``<PLACEHOLDER>`` the template ships, and the generator refuses a value containing a
control character, because TOML cannot represent one inside a quoted string. Both
failures name the variable at fault, and both happen before the deploy stops Apache.

Two things always have to happen after a database changes, and both are easy to
forget:

* **The shared Django cache has to be emptied**, because it holds search results
  keyed by a search that now means something else.
  ``python -m opus_app.clear_django_cache`` does exactly this and nothing else: it
  configures ``CACHES`` and calls ``cache.clear()``. Restarting memcached has the same
  effect, and is what the deploy scripts do.
* **Every worker process has to be restarted**, because some caches are module-level
  dictionaries private to a process -- the ``param_info`` lookup in
  :mod:`opus_app.apps.search.views` and the mult-value lookup in
  :mod:`opus_app.apps.tools.db_utils`. Nothing running outside a worker can reach
  those, ``clear_django_cache`` included, so restarting Apache is the only thing that
  clears them.

The log analyzer
----------------

``scripts/server/log_analyzer/`` holds three cron templates -- a nightly update, an
end-of-month report and a full refresh. They are templates: each installation fills in
the placeholders (the virtual environment, the Apache log directory and its file
prefix, and the web directory the reports are published to) and installs the result in
its own crontab. Nothing substitutes or runs them automatically.

They invoke the analyzer as ``opus_log_analyzer``, the console script the
distribution installs; ``python -m opus_log_analyzer`` runs the same ``main`` and takes
the same arguments. For example, the nightly update is::

    #!/bin/bash
    source <VENV>/bin/activate
    rm -rf /tmp/log_analyzer_results_temp
    mkdir /tmp/log_analyzer_results_temp
    opus_log_analyzer --cronjob --html --dns \
        -o "/tmp/log_analyzer_results_temp/%Y/OPUS-log-analysis-%Y-%m.html" \
        "<APACHELOGDIR>/<PREFIX>_access_log-%Y-%m-%d"
    cp -r /tmp/log_analyzer_results_temp/* <WWW>/log_analyzer_results
    rm -rf /tmp/log_analyzer_results_temp

The reports it writes are internal operator pages, not part of the public site.

Import runbook
--------------

A production import is long -- hours to days for the full holdings -- and it replaces
what users see, so it is done deliberately:

1. **Import into a new database**, not the one being served. ``--override-db-schema``
   points one run at a different schema without editing the configuration.
2. **Read the error log.** The import's own exit status is not the whole story:
   ``--validate-perm`` reports through the log rather than through its status, so an
   automated run gates on the error log being empty.
3. **Compare the new database against the one being served.** ``import_all.sh``
   prints the name of each before it asks for confirmation, so that the erase cannot
   be aimed at the wrong one; it prints no row counts, and comparing those is a
   separate query you run yourself.
4. **Point an installation at the new database** and exercise it before switching the
   public one over.
5. **Flush memcached and restart the application**, as above.

An import can be resumed rather than restarted: the per-step options let a run redo
only the part that failed, and the import tables survive a failure precisely so that
this is possible.
