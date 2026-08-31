.. _dev_guide_webapp_running:

Running the Web Application
===========================

The web application needs a database an import has already populated. Everything below
assumes one; :ref:`dev_guide_import_running` is how to get one, and
:ref:`dev_guide_installation` is how to bring up a server from nothing.

The environment
---------------

.. list-table::
   :header-rows: 1
   :widths: 32 68

   * - Variable
     - Meaning
   * - ``OPUS_CONFIG``
     - The installation's TOML file. **Required by every process**, with no default
       location. Importing :mod:`opus_app.settings` reads it, so a missing or invalid
       file fails at startup rather than at the first request.
   * - ``DJANGO_SETTINGS_MODULE``
     - ``opus_app.settings``. ``manage.py`` and :mod:`opus_app.wsgi` both set it if it
       is unset, so only ``django-admin`` and anything else running Django directly has
       to supply it.

Nothing else is read from the environment: the only :data:`os.environ` access in the
whole package is :mod:`opus_app.wsgi`'s. Every value a deployment can vary -- credentials,
hosts, paths, log levels, the fault-injection knobs -- comes from the configuration file,
and :ref:`dev_guide_installation` tabulates every key.

The development server
----------------------

:ref:`dev_guide_environment` gives the three commands for a checkout. Two things about
what they do:

**The site is served twice.** ``http://127.0.0.1:8000/opus/`` and
``http://127.0.0.1:8000/`` are the same application, because :mod:`opus_app.urls` mounts
every route at both. The ``opus/`` prefix is there for the development server, which has
no web server in front of it.

**``migrate`` creates only Django's own contrib tables** -- session, auth, contenttypes
and admin. Every OPUS table comes from an import instead, which is why there are no OPUS
migrations.

``manage.py`` is a development convenience and carries no OPUS-specific commands. The
ones worth knowing are Django's own: ``check``, ``migrate``, ``shell``,
``collectstatic``, and ``diffsettings``. **The test suites are not run through it** --
``pytest`` runs the holdings-free suite and ``pytest integration_tests`` the
live-database ones; see :ref:`dev_guide_testing`.

An installed OPUS has no ``manage.py``: it is not in the wheel. Use ``django-admin``
with both environment variables set instead.

Under a WSGI server
-------------------

:mod:`opus_app.wsgi` is the entry point. It sets ``DJANGO_SETTINGS_MODULE`` if it is
unset and builds ``application``; it does nothing to :data:`sys.path`, because the
distribution is installed and importable.

Point any WSGI server at ``opus_app.wsgi:application``. For a smoke test -- with
gunicorn installed alongside, since it is not an OPUS dependency::

    OPUS_CONFIG=/etc/opus/opus.toml gunicorn opus_app.wsgi:application

**The one thing that has to be arranged is that ``OPUS_CONFIG`` reaches the worker
process's environment.** It is read when the settings module is imported, which happens
inside the worker, long before any request. :ref:`dev_guide_web_server` gives worked
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

    OPUS_CONFIG=/etc/opus/opus.toml \
    DJANGO_SETTINGS_MODULE=opus_app.settings \
    django-admin collectstatic --noinput

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

:ref:`dev_guide_installation_prereqs` says how to install ``memcached`` and its client,
and why neither is a declared dependency. The behavior to know here is the fallback:
:mod:`opus_app.settings` decides at import time, and it decides **twice** -- whether
``pymemcache`` imports, and whether a connection to a local memcached succeeds -- falling
back to Django's per-process local-memory cache if the import fails or the connection is
**refused**. Any other connection failure, a timeout or a name that resolves oddly, is
**not caught** and stops the application at startup.

Emptying the shared cache is one module::

    OPUS_CONFIG=/etc/opus/opus.toml python -m opus_app.clear_django_cache

It imports ``CACHES`` from :mod:`opus_app.settings`, calls ``settings.configure()`` with
only that setting -- so the app registry is never loaded -- and calls ``cache.clear()``.
It does its work at import, which is why it must be run as a module and never imported,
and why the API reference leaves it out. Restarting memcached has the same effect.

That is only half of what an import requires, because the process-local caches
:ref:`dev_guide_webapp_caching` describes are out of its reach.
:ref:`dev_guide_deployment_after_import` is the full statement.

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

**The OPUS apps' own constants**, everything below the banner comment two-thirds of the
way down: the default columns, widgets and sort order; the query types each field type
allows; the four preview sizes; the paging and download limits; the archive formats; and
the slugs that appear in a URL but are not database fields.

Three details are easy to trip over. **Nothing here reads the environment** except
``OPUS_CONFIG``, by way of :mod:`opus_config`, so there is no second source of truth.
**Module-level helpers are lower-case on purpose**: Django treats every upper-case name
in this module as a setting, and its only test is :meth:`str.isupper`, which a leading
underscore does not defeat. And ``DEFAULT_AUTO_FIELD`` stays ``AutoField`` deliberately
-- it governs the nineteen OPUS models that declare no primary key as well as the contrib
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
app's records reaching the log file. There are nine entries for eight apps: the ninth,
``opus_app.apps.search.forms``, is already covered by the ``opus_app.apps.search``
prefix and changes nothing.

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
one over -- see the runbook in :ref:`dev_guide_deployment`.

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
