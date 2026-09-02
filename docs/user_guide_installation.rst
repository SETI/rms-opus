.. _user_guide_installation:

Installing OPUS on a Server
===========================

This chapter brings up a complete OPUS installation from nothing: the prerequisites, the
distribution, the configuration file, the database, the static files, and a first import.
:ref:`user_guide_web_server` then puts a web server in front of it, and
:ref:`user_guide_deployment` describes operating it.

For a **development checkout** rather than a server, read :ref:`dev_guide_environment`
instead; it is shorter, and it installs from source.

.. _user_guide_installation_prereqs:

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

.. _user_guide_installation_install:

Installing the distribution
---------------------------

::

    python3 -m venv opus_venv
    source opus_venv/bin/activate
    python -m pip install --upgrade pip
    python -m pip install rms-opus

That installs the OPUS programs and everything they depend on. Five commands come with
it, and the rest of this guide uses them by name:

.. list-table::
   :header-rows: 1
   :widths: 32 68

   * - Command
     - What it does
   * - ``opus_config_template``
     - Writes the configuration template into the current directory, which is where
       configuring a server starts.
   * - ``opus_import``
     - The import pipeline: reads the PDS holdings and builds the OPUS database.
   * - ``opus_import_all``
     - Runs a whole full-holdings import: every bundle set, in order, and the steps
       that finish the database.
   * - ``opus_manage``
     - Administers the web application -- creating its tables, gathering its static
       files, and checking that its configuration works.
   * - ``opus_log_analyzer``
     - Turns the web server's access logs into reports on how the site is being used.
   * - ``opus_error_analyzer``
     - The same for the error log.

Every one of them, except ``opus_config_template``, needs ``OPUS_CONFIG`` set, which is
the next step.

.. _user_guide_installation_configuring:

Writing the configuration file
------------------------------

OPUS reads one TOML file and **has no default location for it**. The ``OPUS_CONFIG``
environment variable must name it in the environment of **every** OPUS process: the WSGI
server, the import pipeline, and every management command.

``opus_config_template`` writes a template to start from, with a comment on every key,
into the directory you are standing in::

    opus_config_template
    sudo install -d -m 755 /opt/opus
    sudo install -m 600 -o opus -g opus opus.toml.template /opt/opus/opus.toml
    export OPUS_CONFIG=/opt/opus/opus.toml

Then edit the copy: fill in every ``<PLACEHOLDER>``, and **set** ``debug = false`` -- the
template ships it true, which is right on a machine you are developing on and wrong for
anything reachable from outside it.

Three details in those lines matter:

* ``install`` **rather than** ``cp``. The mode is 0600 because the placeholders are about
  to be replaced by a database password and a secret key, and ``cp`` would give the file
  whatever the caller's umask allows -- world-readable under a default one.
* ``-o opus``. A **root**-owned 0600 file is unreadable to the account OPUS runs as, so
  every command below would fail on the configuration it was handed rather than on
  anything in it. ``opus`` here stands for whichever account the web application and the
  import pipeline run as; it has to exist first, because ``install -o`` fails on an
  unknown user rather than creating one. On a host with no such account, make one:
  ``sudo useradd --system --no-create-home opus``.
* **Run everything below as that account** -- with ``sudo -u opus`` or equivalent. A 0600
  file is readable by exactly one user, which is the point of the mode.

``/opt/opus`` is this guide's example location for an installation's own files -- the
configuration, and the log, download and data directories the configuration names. Any
directory the OPUS account can read works; substitute your own throughout.

The template documents every key, and OPUS validates the file as it reads it: an unknown
key, a missing key, or a value of the wrong type is reported with the table and the key
at fault rather than failing later somewhere else. A misspelled key is an **error**, not
something silently ignored. `The whole template`_ is reproduced at the end of this
chapter.

.. _user_guide_installation_keys:

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

.. _user_guide_installation_database:

Creating the database
---------------------

Two commands, and they create different tables. **Run them in this order**: the first
creates the database, and the second needs it to be there.

**First, import something.** Every table of observation metadata is created by the import
pipeline, and so is the database itself -- there is no ``CREATE DATABASE`` step, because
the pipeline creates the configured schema when it does not already exist. One small
volume is enough to bring the database into being::

    OPUS_CONFIG=/opt/opus/opus.toml opus_import --do-it-all COISS_2002

``--do-it-all`` imports the bundles named after it, copies the result over the permanent
tables, and rebuilds the auxiliary tables. Add ``--import-dictionary`` to load the
tooltips, which no aggregate option implies.

**What to name.** A bundle is named by a *descriptor*, and several can be given, comma-
or space-separated: a single bundle id (``COISS_2002``), a whole bundleset
(``COISS_2xxx``), one of the shorthands for a mission or an instrument (``CASSINI``,
``GALILEO``, ``HST``, ``VOYAGER``, ``NH``, ``COISS``, ``COUVIS`` and their relatives,
matched without regard to case), or ``ALL``, which stands for every bundleset OPUS
imports. ``opus_import --help`` lists every option, and works without a configuration
file; :ref:`dev_guide_import_running` is the complete reference.

**Then create the web application's own tables.** A handful of tables belong to the
application rather than to the archive -- the ones that track a visitor's session, and
the logins for the administrative pages -- and the import does not create them. One
command does, and it is safe to run again at any time::

    OPUS_CONFIG=/opt/opus/opus.toml opus_manage migrate

**Verify the import by reading** ``ERRORS.log`` **in the** ``[paths] import_log_dir``
**directory, not by checking the exit status.** Several steps report a failure through
the log and still exit zero, so a clean run is an empty ``ERRORS.log`` rather than a zero
status; ``WARNINGS.log`` beside it is worth reading too.
:ref:`dev_guide_import_verifying` is the longer account of what to look for.

.. _user_guide_installation_static:

Collecting the static files
---------------------------

::

    OPUS_CONFIG=/opt/opus/opus.toml opus_manage collectstatic --noinput

:ref:`dev_guide_webapp_static` describes where they go, the difference between
``static_root`` and ``opus_static_root``, and why the public prefix is fixed.

.. _user_guide_installation_full_import:

The first full-holdings import
------------------------------

A complete import is hours to days, and it is not one command: the bundle sets are
imported in a particular order, two of them need an extra option, and the database is
finished by three more steps afterwards. **One installed command runs the whole
sequence**::

    export OPUS_CONFIG=/opt/opus/opus.toml
    opus_import_all --override-db-schema opus3_new

It names the database it is about to erase and asks you to type ``YES``, then runs each
step as its own ``opus_import`` process and stops at the first one that fails.

**It imports into a database of its own**, the one ``--override-db-schema`` names, rather than the one
being served: every step it runs carries ``--override-db-schema``, and a schema that does
not exist is created. That is what makes the switchover a configuration change rather than
a window of downtime. Leave ``--override-db-schema`` out and it imports into the database the
configuration file names, which on a serving installation is the one being served.

A run this long should outlive the terminal it was started from, and ``--yes`` is what
answers the confirmation in advance::

    nohup opus_import_all --yes --override-db-schema opus3_new > import_run.log 2>&1 &

**To see the sequence without running it**, ask for it::

    opus_import_all --override-db-schema opus3_new --dry-run

which prints every invocation in order: the erase, then Galileo and New Horizons -- the
two bundle sets whose bundles carry observations that appear in more than one, so they are
imported with ``--import-check-duplicate-id`` while the tables are still small -- then the
rest in roughly decreasing order of how long each takes, and finally the three steps that
finish the database: the auxiliary tables, the dictionary, and the validation. Any option
this command does not recognize is passed to every ``opus_import`` invocation it makes.

Because those three finishing steps are part of the sequence, the only thing left to run
against the new database is the web application's own tables::

    # opus_manage has no --override-db-schema: it takes the database from the configuration file,
    # so this one needs a file that names opus3_new. Run against the production
    # configuration, it would add its tables to the database being served instead.
    OPUS_CONFIG=/opt/opus/opus_new.toml opus_manage migrate

Then :ref:`user_guide_deployment_runbook` is what to do with the result: read
``ERRORS.log``, compare the new database's row counts against the one being served,
exercise it from a test installation, and only then switch over.

.. _user_guide_installation_smoke:

Checking the installation
-------------------------

Four checks, in increasing order of what they prove::

    # 1. The distribution installed and its console scripts work. Needs no configuration.
    opus_import --help
    opus_log_analyzer --help
    opus_error_analyzer --help

    # 2. The configuration file parses and validates. Loading the settings is what
    #    proves it; add --database default to open the connection as well.
    OPUS_CONFIG=/opt/opus/opus.toml opus_manage check --database default

    # 3. The application starts under a WSGI server. gunicorn is not an OPUS
    #    dependency -- install it for this check, or use whichever server you deploy.
    python -m pip install gunicorn
    OPUS_CONFIG=/opt/opus/opus.toml gunicorn opus_app.wsgi:application

    # 4. It answers. 127.0.0.1 has to be in allowed_hosts, or Django replies 400
    #    however well the application and the database are working.
    curl -s 'http://127.0.0.1:8000/api/meta/result_count.json?planet=Saturn'

If the third fails on an import error rather than a configuration one, the usual cause is
that ``OPUS_CONFIG`` did not reach the process; see :ref:`user_guide_web_server`.

Where to go next
----------------

:ref:`user_guide_web_server`
    Putting nginx or Apache in front of it.

:ref:`user_guide_deployment`
    The Node's own deploy chain, and the runbook for replacing a database.

:ref:`dev_guide_import_running`
    Every import option.

The whole template
------------------

This is what ``opus_config_template`` writes, reproduced here so that the file can be read
before anything is installed. It is the same file, included from the distribution rather
than retyped, so the two cannot drift.

.. literalinclude:: ../src/opus_config/opus.toml.template
   :language: toml
   :caption: opus.toml.template

API reference
-------------

:doc:`api_opus_config`, :doc:`api_opus_import`
