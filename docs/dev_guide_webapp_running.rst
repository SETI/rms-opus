.. _dev_guide_webapp_running:

Running the Web Application
===========================

The web application needs a database an import has already populated. Everything below
assumes one; :ref:`dev_guide_import_running` is how to get one, and
:ref:`user_guide_installation` is how to bring up a server from nothing.

The environment
---------------

**One variable.**

``OPUS_CONFIG``
    The path of this installation's TOML file. Every OPUS process needs it, and there is
    no default location on purpose: a machine hosting several installations gives each
    one its own file, and a process started without the variable stops with an error
    naming the variable rather than quietly picking up a neighbor's database. Importing
    :mod:`opus_app.settings` reads it, so a missing or invalid file fails at startup
    rather than at the first request.

``DJANGO_SETTINGS_MODULE`` is the variable you do **not** have to set. Django can be told
which settings module to use only through the environment, so everything that starts
Django here names it for you: ``opus_manage``, the checkout's ``manage.py``,
:mod:`opus_app.wsgi` for every WSGI server, ``pyproject.toml`` for pytest, and
``docs/conf.py`` for the documentation build. It is needed only for bare ``django-admin``,
which is Django's entry point rather than one of ours.

Nothing else is read from the environment. The only :data:`os.environ` access in the whole
package is those two settings-module lines, in :mod:`opus_app.wsgi` and
:mod:`opus_app.manage`; every value a deployment can vary -- credentials, hosts, paths,
log levels, the fault-injection knobs -- comes from the configuration file, and
:ref:`user_guide_installation` tabulates every key.

.. _dev_guide_webapp_command_line:

Running it from the command line
--------------------------------

Django management commands are how the application is administered: creating its contrib
tables, gathering its static files, opening a shell with the models loaded, and running
the development server. There are three ways to reach them. The first two are the same
program under two names; the third is Django's own command, and is the only one that
needs a second environment variable.

**From an installation** -- a ``pip install`` with no checkout anywhere -- the command is
``opus_manage``::

    export OPUS_CONFIG=/opt/opus/opus.toml
    opus_manage migrate
    opus_manage runserver

**From a checkout**, ``manage.py`` in the repository root does the same thing, and is
what a developer normally types::

    export OPUS_CONFIG=$PWD/opus.toml
    python manage.py migrate
    python manage.py runserver

``manage.py`` calls :func:`opus_app.manage.main`, which is what ``opus_manage`` runs, so
the two cannot drift; ``tests/opus_packaging/test_console_scripts.py`` runs both and
compares them.

**With ``django-admin``**, if you would rather use Django's own command, name the settings
module yourself::

    OPUS_CONFIG=/opt/opus/opus.toml \
    DJANGO_SETTINGS_MODULE=opus_app.settings \
    django-admin migrate

That is the only form that needs the second variable, and it is why ``opus_manage``
exists: an installed OPUS has no ``manage.py`` -- it is a checkout's file and is not in
the wheel -- so without it every deployment would have to export a Django variable to run
a Django command, and forgetting it produces an error about Django rather than about
OPUS.

``runserver`` listens on ``127.0.0.1:8000`` unless told otherwise (``opus_manage
runserver 0.0.0.0:8080``). It is Django's development server: single-process, restarting
itself on every file change, and **not what serves the public site** -- that is a WSGI
server behind nginx or Apache, described below and in :ref:`user_guide_web_server`.

Then open ``http://127.0.0.1:8000/opus/``, or ask the API a question directly::

    $ curl -s 'http://127.0.0.1:8000/api/meta/result_count.json?planet=Saturn'
    {"data": [{"result_count": 17119}]}

The number depends on what has been imported into the database this installation names;
that it answers at all is the check.

Two things about what those commands do:

**The site is served twice.** ``http://127.0.0.1:8000/opus/`` and
``http://127.0.0.1:8000/`` are the same application, because :mod:`opus_app.urls` mounts
every route at both. The ``opus/`` prefix is there for the development server, which has
no web server in front of it.

**``migrate`` creates only Django's own contrib tables** -- session, auth, contenttypes
and admin. Every OPUS table comes from an import instead, which is why there are no OPUS
migrations, and why ``migrate`` on a database an import has already populated has nothing
to do the second time.

The commands worth knowing
--------------------------

OPUS adds no management commands of its own, so these are all Django's. Each one below
takes ``opus_manage`` or ``python manage.py`` in front of it.

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Command
     - What it is for
   * - ``check``
     - Loads the settings and every app and reports every error and warning Django's
       own checks raise, without touching the database. The fastest way to find out
       whether a configuration file is usable at all.
   * - ``migrate``
     - Creates Django's own contrib tables in the configured schema. Run once against a
       newly imported database, and again after an upgrade that crosses a Django release
       adding a contrib migration.
   * - ``collectstatic``
     - Gathers the static files into ``[paths] static_root`` for a web server to serve
       directly. See `Static files`_ below.
   * - ``runserver``
     - The development server. Never in production.
   * - ``shell``
     - A Python shell with Django configured, which is how to query the models by hand.
   * - ``diffsettings``
     - Prints the settings that differ from Django's defaults, which is the quickest way
       to see what a configuration file actually produced.

**The test suites are not run through any of them** -- ``pytest`` runs the holdings-free
suite and ``pytest integration_tests`` the live-database ones; see
:ref:`dev_guide_testing`.

``check`` reports one warning on every OPUS installation, and it is expected::

    ?: (urls.W005) URL namespace 'admin' isn't unique. You may not be able to
    reverse all URLs in this namespace

It follows from :mod:`opus_app.urls` mounting every route twice, at ``/`` and under
``/opus/``, which puts Django's admin at two paths and so in the namespace twice. Nothing
in OPUS reverses an admin URL, so the consequence the warning describes does not arise
here; ``System check identified 1 issue (0 silenced)`` is a clean run.

Under a WSGI server
-------------------

:mod:`opus_app.wsgi` is the entry point. It sets ``DJANGO_SETTINGS_MODULE`` if it is
unset and builds ``application``; it does nothing to :data:`sys.path`, because the
distribution is installed and importable.

Point any WSGI server at ``opus_app.wsgi:application``. For a smoke test -- with
gunicorn installed alongside, since it is not an OPUS dependency::

    OPUS_CONFIG=/opt/opus/opus.toml gunicorn opus_app.wsgi:application

**The one thing that has to be arranged is that ``OPUS_CONFIG`` reaches the worker
process's environment.** It is read when the settings module is imported, which happens
inside the worker, long before any request. :ref:`user_guide_web_server` gives worked
configurations for nginx with gunicorn or uWSGI, and for Apache with ``mod_wsgi``,
each of which arranges it differently.

.. _dev_guide_webapp_static:

Static files
------------

The on-disk directory is ``src/opus_app/static/``; **the public URL prefix is**
``/static_media/``, and it must stay that way -- it is hardcoded in the front end's
``opus.js``, embedded in the golden API fixtures, and aliased in the production web
server configuration.

A development installation serves them through Django's staticfiles app and needs no
further step. A server gathers them into one directory that the web server serves
directly::

    OPUS_CONFIG=/opt/opus/opus.toml opus_manage collectstatic --noinput

``--noinput`` is what the deploy scripts pass: ``collectstatic`` asks for confirmation
before overwriting, and a deploy has nobody to ask.

Two configuration keys are easy to confuse:

``static_root``
    Where ``collectstatic`` puts them. A development installation leaves it out --
    it never runs ``collectstatic`` -- and Django's own default applies.

``opus_static_root``
    The directory the help pages' PDF renderer reads assets out of. On a server it is
    the same directory as ``static_root``; in a development installation it points at
    ``.../src/opus_app/static``.

The staticfiles backend is deliberately the plain one rather than a manifest one: OPUS
cache-busts its asset URLs with a ``?version=`` suffix that
:mod:`opus_app.apps.tools.app_utils` supplies, and a manifest backend would require every
template- and JavaScript-referenced asset to survive ``collectstatic`` first.

Caching, and clearing it
------------------------

:ref:`user_guide_installation_prereqs` says how to install ``memcached`` and its client,
and why neither is a declared dependency. The behavior to know here is the fallback:
:mod:`opus_app.settings` decides at import time, and it decides **twice** -- whether
``pymemcache`` imports, and whether a connection to a local memcached succeeds -- falling
back to Django's per-process local-memory cache if the import fails or the connection is
**refused**. Any other connection failure, a timeout or a name that resolves oddly, is
**not caught** and stops the application at startup.

Emptying the shared cache is one module::

    OPUS_CONFIG=/opt/opus/opus.toml python -m opus_app.clear_django_cache

It imports ``CACHES`` from :mod:`opus_app.settings`, calls ``settings.configure()`` with
only that setting -- so the app registry is never loaded -- and calls ``cache.clear()``.
It does its work at import, which is why it must be run as a module and never imported,
and why the API reference leaves it out. Restarting memcached has the same effect.

That is only half of what an import requires, because the process-local caches
:ref:`dev_guide_webapp_caching` describes are out of its reach.
:ref:`user_guide_deployment_after_import` is the full statement.

.. _dev_guide_webapp_settings:

The settings module
-------------------

:mod:`opus_app.settings` is where every value a deployment can vary arrives, and it is
worth reading once end to end. It has three parts:

**Django's own settings**, assigned from the configuration file: the secret key, the
debug flag, the allowed hosts, the database connection, the static root, and the log
levels. The database engine is chosen from the configured *brand* through a two-entry
map, so the web application and the import pipeline cannot disagree about which database
they are talking to.

**Fixed application settings** that no deployment varies: the middleware chain, the
installed apps, the template configuration, the storage backends, the session policy and
the time zone.

**The OPUS apps' own constants**, everything below the banner comment reading *From here
on, the configuration is for the OPUS apps, not Django itself*: the default columns,
widgets and sort order; the query types each field type allows; the four preview sizes;
the paging and download limits; the archive formats; and the slugs that appear in a URL
but are not database fields.

Three details are easy to trip over. **Nothing here reads the environment** except
``OPUS_CONFIG``, by way of :mod:`opus_config`, so there is no second source of truth.
**Module-level helpers are lower-case on purpose**: Django treats every upper-case name
in this module as a setting, and its only test is :meth:`str.isupper`, which a leading
underscore does not defeat. And ``DEFAULT_AUTO_FIELD`` stays ``AutoField`` deliberately
-- it governs the OPUS models that declare no primary key as well as the contrib
tables, all of which already exist with a 32-bit ``AUTO_INCREMENT`` column.

Logging
-------

:mod:`opus_app.settings` configures two handlers: a console handler and a rotating file
handler writing to the path ``[paths] opus_log_file`` names, at 50 KB with two backups.
Their levels come from ``[django] log_file_level`` and ``log_console_level``; Django's
own loggers are separate, at ``log_django_level``.

**The application opens its log file during startup**, so a missing log directory stops
the application rather than degrading it. That is also why the checked-in CI
configuration puts every path it opens directly under ``/tmp``.

Each OPUS app has its own logger entry, and each key **must be a prefix of the app
modules' actual names** -- they call ``logging.getLogger(__name__)``, giving names like
``opus_app.apps.cart.views``. A key that prefixes no real logger silently stops that
app's records reaching the log file. One entry is redundant:
``opus_app.apps.search.forms`` is already covered by the ``opus_app.apps.search`` prefix
and changes nothing.

Setting ``log_api_calls`` to a level name logs every API call's entry and exit. It is
false in every normal deployment.

Fault injection
---------------

Three configuration keys make the server misbehave on purpose, for exercising the front
end's error handling:

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Key
     - Effect
   * - ``fake_api_delays``
     - Delay every API response by this many milliseconds. A negative value delays a
       random amount between zero and its magnitude, which is what a jittery network
       looks like. The delay is applied **after** the call is logged, so the log records
       the time the response was produced.
   * - ``fake_error404_probability``
     - The probability, from 0 to 1, that any API call is answered with an injected 404
       instead of running its handler.
   * - ``fake_error500_probability``
     - The same, for a 500.

All three default to no effect, and the two probabilities are rolled once per call,
before the handler runs.

Running against a different database
------------------------------------

The database is named in the configuration file, so pointing an installation at a
different one means a different configuration file and a different ``OPUS_CONFIG``. That
is exactly how a server exercises a newly imported database before switching the public
one over -- see the runbook in :ref:`user_guide_deployment`.

A server running several OPUS installations gives each one its own file, its own
``OPUS_CONFIG``, its own database schema and its own ``cache_server_prefix``, which is
what keeps them from colliding in a shared memcached.

Testing what it answers
-----------------------

``integration_tests/test_api/`` is the golden-response suite: it exercises the public API
against a populated database and compares the answers byte for byte. It is what proves
that a refactor did not change what OPUS returns.
:ref:`running-the-integration-suites` describes the three-step chain that populates a
database and runs it, and why it is not generally runnable without the holdings.

``tests/opus_app/`` holds the parts that need no database and runs in a bare ``pytest``.

API reference
-------------

:doc:`api_opus_app`
