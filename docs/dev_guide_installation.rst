.. _dev_guide_installation:

Installing OPUS on a Server
===========================

This chapter brings up a complete OPUS installation from nothing: the prerequisites, the
distribution, the configuration file, the database, the static files, and a first import.
:ref:`dev_guide_web_server` then puts a web server in front of it, and
:ref:`dev_guide_deployment` describes operating it.

For a **development checkout** rather than a server, read :ref:`dev_guide_environment`
instead; it is shorter, and it installs from source.

.. _dev_guide_installation_prereqs:

Prerequisites
-------------

**Python 3.12 or later.**

**MySQL 8.0.19 or later**, with a user allowed to create and drop databases and tables.
The import pipeline creates every OPUS table itself -- and creates the schema, if it does
not exist -- and it writes its multi-row upserts with the ``AS new`` row alias that
8.0.19 added. See :ref:`dev_guide_import_db_importdb` for why that is the floor.

**The MySQL client development headers**, because the ``mysqlclient`` driver ships no
Linux wheel and is compiled during the install. On Debian or Ubuntu::

    sudo apt-get install pkg-config default-libmysqlclient-dev build-essential

**memcached and its** ``pymemcache`` **client** -- strongly recommended, and **not a
declared dependency**. An installation that skips this step runs, slowly and per process,
with the cache-flushing step of a deploy doing nothing at all.
:ref:`dev_guide_webapp_running` describes the fallback and its one sharp edge::

    sudo apt-get install memcached libmemcached-tools
    pip install pymemcache
    # watch it while OPUS runs; memcstat is in libmemcached-tools, not memcached:
    watch -n1 -d 'memcstat --servers localhost'

**wkhtmltopdf**, only for the help pages' PDF downloads. Every other page works without
it; see :ref:`dev_guide_webapp_help_app`.

**The PDS holdings**, mounted read-only, for the import pipeline. The web application
needs them only to serve product files; the import needs them to run at all. Both a PDS3
and a PDS4 root are configured, and the deploy chain checks that ``volumes/`` exists
under the first and ``bundles/`` under the second.

.. _dev_guide_installation_install:

Installing the distribution
---------------------------

::

    python3 -m venv opus_venv
    source opus_venv/bin/activate
    python -m pip install --upgrade pip
    python -m pip install rms-opus

Dependencies are declared in ``pyproject.toml`` with **floors, not pins** -- only Django
carries an upper bound, because 5.2 is the long-term-support release this application
targets. There is no lock file: a fresh install resolves each dependency to its newest
compatible release.

To reproduce one installation exactly on another machine, generate a constraints file
from a known-good one::

    # on the known-good installation
    python -m pip freeze > constraints.txt

    # on the new one
    pip install rms-opus -c constraints.txt

Nothing in the deploy chain maintains such a file; it is there for the case where
operations wants a reproducible install rather than the newest one.

**An installed OPUS is not a checkout.** It has no ``manage.py``, no ``scripts/`` and no
``opus.toml.template``; use ``django-admin`` with the environment set, and fetch the
template as below.

.. _dev_guide_installation_configuring:

Writing the configuration file
------------------------------

OPUS reads one TOML file and **has no default location for it**. The ``OPUS_CONFIG``
environment variable must name it in the environment of **every** OPUS process: the WSGI
server, the import pipeline, and every management command.

::

    curl -fsSLO https://raw.githubusercontent.com/SETI/rms-opus/main/opus.toml.template
    sudo install -d -m 755 /etc/opus
    sudo install -m 600 -o opus -g opus opus.toml.template /etc/opus/opus.toml
    export OPUS_CONFIG=/etc/opus/opus.toml

Four details in those four lines are load-bearing:

* ``-f`` **on curl.** Without it curl exits 0 on a 404 and writes the error page into the
  file the next line copies.
* ``install`` **rather than** ``cp``. The mode is 0600 because the placeholders are about
  to be replaced by a database password and a Django secret key, and ``cp`` would give
  the file whatever the caller's umask allows -- world-readable under a default one.
* ``-o opus``. A **root**-owned 0600 file is unreadable to the account OPUS runs as, so
  every command below would fail on the configuration it was handed rather than on
  anything in it. ``opus`` here stands for whichever account the WSGI daemon and the
  import pipeline run as; it has to exist first, because ``install -o`` fails on an
  unknown user rather than creating one. On a host with no such account, make one:
  ``sudo useradd --system --no-create-home opus``.
* **Run everything below as that account** -- with ``sudo -u opus`` or equivalent. A 0600
  file is readable by exactly one user, which is the point of the mode.

The template documents every key, and :mod:`opus_config` validates the file as it reads
it: an unknown key, a missing key, or a value of the wrong type is reported with the
table and the key at fault rather than failing later somewhere else. A misspelled key is
an **error**, not something silently ignored.

.. _dev_guide_installation_keys:

Every configuration key
-----------------------

Four tables. A key marked optional may be left out entirely.

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
     - The host the OPUS schema lives on. Usually ``"localhost"``.
   * - ``database``
     - optional
     - MySQL ignores this and connects to ``schema`` instead. Default ``""``.
   * - ``schema``
     - yes
     - The namespace the OPUS tables live in -- the database name under MySQL. It is
       also part of every cache key.
   * - ``user``, ``password``
     - yes
     - The database account. It needs most privileges, including creating and dropping
       tables.

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
       than degrading it.
   * - ``import_log_dir``
     - yes
     - Where the import pipeline writes ``WARNINGS.log`` and ``ERRORS.log``. Must exist.
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
       applies. **Set it on a server.**
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
     - The hosts and addresses Django will serve, as an array.
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
     - Fault injection; see :ref:`dev_guide_webapp_running`. Omit it in production.
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

**Create every directory the** ``[paths]`` **section names, and make each writable by the
account OPUS runs as, before starting anything.**

.. _dev_guide_installation_database:

Creating the database
---------------------

Two steps, and they create different things.

**Django's own contrib tables** -- sessions, auth, content types, admin -- come from a
migration::

    OPUS_CONFIG=/etc/opus/opus.toml \
    DJANGO_SETTINGS_MODULE=opus_app.settings \
    django-admin migrate

**Every OPUS table comes from an import**, so there are no OPUS migrations to run and
none to write::

    OPUS_CONFIG=/etc/opus/opus.toml opus_import --do-it-all COISS_2002

The schema itself needs no ``CREATE DATABASE``: the import pipeline creates it when the
configured one does not exist.

``--do-it-all`` imports the named bundles, copies the result over the permanent tables,
and rebuilds the auxiliary tables. Add ``--import-dictionary`` to load the tooltips,
which no aggregate option implies. :ref:`dev_guide_import_running` is the full command
line.

**Verify the import by reading** ``ERRORS.log``, not by checking the exit status.
:ref:`dev_guide_import_verifying` says why.

.. _dev_guide_installation_static:

Collecting the static files
---------------------------

::

    OPUS_CONFIG=/etc/opus/opus.toml \
    DJANGO_SETTINGS_MODULE=opus_app.settings \
    django-admin collectstatic --noinput

:ref:`dev_guide_webapp_static` describes where they go, the difference between
``static_root`` and ``opus_static_root``, and why the public prefix is fixed.

.. _dev_guide_installation_full_import:

The first full-holdings import
------------------------------

A complete import is hours to days. Two things make it survivable:

**Import into a new schema rather than the one being served.**
``--override-db-schema`` points one run at a different schema without editing the
configuration, and a schema that does not exist is created. That is what makes the
switchover a configuration change rather than a window of downtime.

**Run it detached, and gate on the error log.** The Node's own wrapper,
``scripts/import/import_all.sh``, does both: it prints the schema it is about to erase
and requires the operator to type a confirmation, then runs the real work under ``nohup``.
By hand::

    export OPUS_CONFIG=/etc/opus/opus.toml
    nohup opus_import --override-db-schema opus3_new --do-it-all ALL \
        > /var/log/opus/import_run.log 2>&1 &

``ALL`` is the descriptor that expands to every bundleset OPUS imports;
:ref:`dev_guide_import_running` lists the others, and gives the smaller invocations worth
doing first.

The Node's wrappers pass ``--import-check-duplicate-id`` for two bundle groups,
Galileo and New Horizons, because their bundles carry observations that appear in more
than one. The option's own help text names a third, COUVIS, which no wrapper passes it
for; take the scripts as the record of what is actually run.

When it finishes, three more commands complete the database::

    opus_import --override-db-schema opus3_new --import-dictionary

    # django-admin has no --override-db-schema: it takes the schema from the
    # configuration file, so this one needs a file that names opus3_new. Running it
    # against the production configuration migrates the database being served.
    OPUS_CONFIG=/etc/opus/opus_new.toml \
    DJANGO_SETTINGS_MODULE=opus_app.settings django-admin migrate

    opus_import --override-db-schema opus3_new --validate-perm

and then :ref:`dev_guide_deployment_runbook` is what to do with the result: read
``ERRORS.log``, compare the new database's row counts against the one being served,
exercise it from a test installation, and only then switch over.

.. _dev_guide_installation_smoke:

Checking the installation
-------------------------

Four checks, in increasing order of what they prove::

    # 1. The distribution installed and its console scripts work. Needs no configuration.
    opus_import --help
    opus_log_analyzer --help
    opus_error_analyzer --help

    # 2. The configuration file parses and names a reachable database.
    OPUS_CONFIG=/etc/opus/opus.toml \
    DJANGO_SETTINGS_MODULE=opus_app.settings \
    django-admin check

    # 3. The application starts under a WSGI server. gunicorn is not an OPUS
    #    dependency -- install it for this check, or use whichever server you deploy.
    python -m pip install gunicorn
    OPUS_CONFIG=/etc/opus/opus.toml gunicorn opus_app.wsgi:application

    # 4. It answers.
    curl -s 'http://127.0.0.1:8000/api/meta/result_count.json?planet=Saturn'

If the third fails on an import error rather than a configuration one, the usual cause is
that ``OPUS_CONFIG`` did not reach the process; see :ref:`dev_guide_web_server`.

Where to go next
----------------

:ref:`dev_guide_web_server`
    Putting nginx or Apache in front of it.

:ref:`dev_guide_deployment`
    The Node's own deploy chain, and the runbook for replacing a database.

:ref:`dev_guide_import_running`
    Every import option.

API reference
-------------

:doc:`api_opus_config`, :doc:`api_opus_import`
