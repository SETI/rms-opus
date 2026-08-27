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
* **memcached**, which the web application caches through. On Debian or Ubuntu::

      sudo apt-get install libmemcached-dev zlib1g-dev memcached
      # watch it while OPUS runs:
      watch -n1 -d 'memcstat --servers localhost'

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

Configuring
-----------

Copy ``opus.toml.template``, fill in every ``<PLACEHOLDER>``, and export
``OPUS_CONFIG`` in the environment of **every** OPUS process -- the WSGI server, the
import pipeline, and any management command::

    cp opus.toml.template /etc/opus/opus.toml
    export OPUS_CONFIG=/etc/opus/opus.toml

There is no default location for the file. A server running several OPUS
installations gives each one its own file, its own ``OPUS_CONFIG``, its own database
schema and its own ``cache_server_prefix``, which is what keeps them from colliding in
the shared memcached.

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

    OPUS_CONFIG=/etc/opus/opus.toml python -m opus_import --do-it-all COISS_2002

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
    django-admin collectstatic

``static_root`` in the configuration is where they go, and ``opus_static_root`` is the
URL path they are served from. A development installation runs neither: it leaves
``static_root`` out of the configuration and points ``opus_static_root`` at
``.../src/opus_app/static``.

The public URL prefix is ``/static_media/`` regardless, which is long-standing and
deliberate.

Running the application
-----------------------

Production serves :mod:`opus_app.wsgi` through Apache and ``mod_wsgi``. The vhost
needs ``WSGIScriptAlias`` pointing at the installed ``opus_app/wsgi.py``, and it needs
``OPUS_CONFIG`` in the WSGI process's environment -- ``WSGIDaemonProcess`` does not
inherit the shell's.

Any other WSGI server works the same way; ``gunicorn opus_app.wsgi:application`` is
enough for a smoke test. For development, ``python manage.py runserver`` serves the
site at ``http://127.0.0.1:8000/opus/``.

.. _deployment_server:

The Node's production arrangement
---------------------------------

``scripts/server/import_and_deploy/`` holds the scripts that deploy a new database or
a new checkout on the Node's servers. They assume a layout in which the served
directory is a symbolic link to a per-database directory, so that swapping databases
is a link change rather than a copy:

::

    /opus/src/rms-opus            -> rms-opus_<database name>
    /opus/src/rms-opus_<database name>/

``deploy_new_code_and_database.sh <database name> [<branch>]`` stops Apache and
memcached, replaces the checkout, moves the link, and starts them again.
``deploy_new_code_only.sh`` does the same without changing the database.
``run_full_opus_import.sh`` runs a complete import into a new database, which is the
first half of bringing up a new one.

``scripts/server/database/`` holds the dump and load scripts used to move a database
between machines.

Two things always have to happen after a database changes, and both are easy to
forget:

* **memcached has to be flushed**, because the application caches ``param_info`` and
  the search results by key. Restarting memcached is what the deploy scripts do.
* **The application's process-local caches have to go**, which happens when Apache
  restarts. ``python -m opus_app.clear_django_cache`` clears Django's cache without a
  restart.

The log analyzer
----------------

``scripts/server/log_analyzer/`` holds three cron templates -- a nightly update, an
end-of-month report and a full refresh. They are templates: each installation fills in
the placeholders (the virtual environment, the Apache log directory and its file
prefix, and the web directory the reports are published to) and installs the result in
its own crontab. Nothing substitutes or runs them automatically. For example, the
nightly update is::

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
3. **Compare counts** against the database currently being served, which is what
   ``import_all.sh`` prints before it starts.
4. **Point an installation at the new database** and exercise it before switching the
   public one over.
5. **Flush memcached and restart the application**, as above.

An import can be resumed rather than restarted: the per-step options let a run redo
only the part that failed, and the import tables survive a failure precisely so that
this is possible.
