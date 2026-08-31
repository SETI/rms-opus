.. _dev_guide_web_server:

Fronting OPUS with a Web Server
===============================

OPUS is a WSGI application. In production a web server sits in front of it and does three
things Django should not: it terminates HTTP, it serves the static files and the data
products directly off disk, and it starts the worker processes.

This chapter gives a worked configuration for **nginx** -- with gunicorn, and with uWSGI
-- and for **Apache with mod_wsgi**. They are worked examples rather than files to paste
unread. Throughout, ``opus`` is the account OPUS runs as, ``opus.example.org`` is the
host name, ``/opus`` is the installation root, ``/pds`` is where the holdings are
mounted, and ``/etc/opus/opus.toml`` is the configuration file; substitute your own for
each.

.. _dev_guide_web_server_contract:

What the web server has to provide
----------------------------------

Whatever server you use, five things have to be true. Each of them is a property of the
application rather than of the server, so they are the same for all three configurations
below.

**1. The WSGI entry point is** ``opus_app.wsgi:application``. For a server that imports
by module path -- gunicorn, uWSGI -- that string is enough. For ``mod_wsgi``, which takes
a **file** path, it is the installed ``wsgi.py``, inside the virtual environment's
``site-packages``.

**2.** ``OPUS_CONFIG`` **must be in the worker process's environment.** It is read when
:mod:`opus_app.settings` is imported, which happens inside the worker before any request
is served. This is the single most common way a deployment fails, and each server
arranges it differently -- see each section below.

**3. Static files are served at** ``/static_media/``, from the directory ``static_root``
names. The prefix is fixed; :ref:`dev_guide_webapp_static` says why.

**4. Data products are served at** ``/holdings/`` **and** ``/pds4-holdings/``, from the
two holdings roots. The import stores each file's path as ``holdings/...`` or
``pds4-holdings/...``, and the application prefixes it with the ``product_http_path``
setting, so those two paths must resolve on whatever host that setting names. If products
are served by a different host, point ``product_http_path`` at that host instead and omit
these locations -- but note that
:func:`~opus_app.apps.tools.file_utils.get_pds_preview_images` rewrites a PDS3 preview's
``/holdings`` to ``/pds3-holdings`` when ``product_http_path`` names a ``googleapis``
host, so a Google Cloud Storage bucket needs that third name instead.

**5. The application answers at the vhost root.** :mod:`opus_app.urls` mounts every route
twice -- at ``/`` and under ``/opus/`` -- so mounting the application at the root makes
both work, and no prefix stripping is needed. The ``opus/`` prefix is there for the
development server, which has nothing in front of it; the URL map's own comment marks it
as such. Mounting the application under a sub-path works under ``mod_wsgi``, whose
``WSGIScriptAlias`` sets ``SCRIPT_NAME`` and strips the prefix before Django sees it;
under nginx neither ``proxy_pass`` nor ``uwsgi_pass`` does that for you, and you would
have to set ``SCRIPT_NAME`` yourself. The configurations below all mount at the root,
which is what ``public_url`` and ``product_http_path`` are written for.

Two more, which are conventions rather than requirements:

* **Cart downloads** are written into ``tar_dir`` and retrieved from ``tar_file_url``. If
  that URL is on this host, the server needs a location serving that directory.
* ``allowed_hosts`` **has to name the host** the server passes through, or Django
  refuses the request.

.. _dev_guide_web_server_nginx:

nginx with gunicorn
-------------------

The arrangement most easily reproduced: nginx proxies to gunicorn over a Unix socket, and
systemd owns the gunicorn process and its environment.

The systemd unit
~~~~~~~~~~~~~~~~

**This is where** ``OPUS_CONFIG`` **is set.** systemd's ``Environment=`` puts it in the
process's own environment, which is exactly what the settings import needs.

.. code-block:: ini

    # /etc/systemd/system/opus.service
    [Unit]
    Description=OPUS WSGI application
    After=network.target memcached.service
    Wants=memcached.service

    [Service]
    User=opus
    Group=opus
    RuntimeDirectory=opus
    WorkingDirectory=/opus

    Environment=OPUS_CONFIG=/etc/opus/opus.toml
    Environment=DJANGO_SETTINGS_MODULE=opus_app.settings

    ExecStart=/opus/src/rms-opus/opus_venv/bin/gunicorn \
        --workers 8 \
        --timeout 300 \
        --bind unix:/run/opus/opus.sock \
        --access-logfile - \
        --error-logfile - \
        opus_app.wsgi:application

    ExecReload=/bin/kill -s HUP $MAINPID
    Restart=on-failure

    [Install]
    WantedBy=multi-user.target

Two of those options are chosen rather than default. ``--timeout 300`` is generous
because building a cart archive of thousands of files is a slow request. The worker count
should be tuned to the machine; every worker holds its own copy of the process-local
caches described in :ref:`dev_guide_webapp_caching`, and **restarting the service is what
clears them**, which is why ``ExecReload`` matters after an import.

The nginx server block
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: nginx

    # /etc/nginx/sites-available/opus
    upstream opus_app {
        server unix:/run/opus/opus.sock fail_timeout=0;
    }

    server {
        listen 443 ssl;
        http2 on;                              # nginx before 1.25.1: listen 443 ssl http2;
        server_name opus.example.org;          # must appear in allowed_hosts

        ssl_certificate     /etc/ssl/certs/opus.example.org.pem;
        ssl_certificate_key /etc/ssl/private/opus.example.org.key;

        # An OPUS search URL carries every constraint, so it can be long.
        large_client_header_buffers 4 16k;

        # The static files collectstatic gathered. The prefix is fixed; the
        # directory is the static_root from opus.toml.
        location /static_media/ {
            alias /opus/static_media/;
            access_log off;
            expires 30d;
        }

        # The PDS data products. obs_files stores each path as holdings/... or
        # pds4-holdings/..., and product_http_path prefixes it with this host.
        location /holdings/ {
            alias /pds/holdings/;
            autoindex off;
        }
        location /pds4-holdings/ {
            alias /pds/pds4-holdings/;
            autoindex off;
        }

        # Cart archives, written into tar_dir and named by tar_file_url.
        location /downloads/ {
            alias /opus/downloads/;
        }

        location = /robots.txt {
            alias /opus/static_media/robots.txt;
        }

        location / {
            proxy_set_header Host              $http_host;
            proxy_set_header X-Real-IP         $remote_addr;
            proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_redirect off;
            proxy_read_timeout 300s;
            proxy_pass http://opus_app;
        }
    }

Three notes on that block:

* ``alias`` **rather than** ``root``, in all four file locations, because the URL prefix
  and the directory name differ in every one of them.
* ``proxy_read_timeout`` has to match or exceed gunicorn's ``--timeout``, for the same
  archive-building reason.
* Serving ``/holdings/`` from nginx rather than through Django is the point of the
  exercise: those are the data files, and they are large.

.. _dev_guide_web_server_uwsgi:

nginx with uWSGI
----------------

The same nginx block, with the ``location /`` replaced by:

.. code-block:: nginx

    location / {
        include uwsgi_params;
        uwsgi_pass unix:/run/opus/opus.sock;
        uwsgi_read_timeout 300s;
    }

and gunicorn replaced by a uWSGI instance. **The environment variable is set with**
``env =``, which uWSGI applies to the worker's own environment:

.. code-block:: ini

    ; /etc/uwsgi/apps-available/opus.ini
    [uwsgi]
    module = opus_app.wsgi:application

    virtualenv = /opus/src/rms-opus/opus_venv
    chdir      = /opus

    env = OPUS_CONFIG=/etc/opus/opus.toml
    env = DJANGO_SETTINGS_MODULE=opus_app.settings

    master    = true
    processes = 8
    harakiri  = 300

    socket    = /run/opus/opus.sock
    chmod-socket = 660
    uid = opus
    gid = opus
    ; uWSGI binds the socket before it drops privileges, so without this the socket
    ; stays root-owned and nginx gets a 502 on connect.
    chown-socket = opus:www-data

    vacuum       = true
    die-on-term  = true

Two things the gunicorn arrangement got from systemd have to be arranged here. ``/run/opus``
is created by that unit's ``RuntimeDirectory=opus``; running uWSGI instead means either
its own unit with the same line or a ``/etc/tmpfiles.d`` entry, since ``/run`` does not
survive a reboot. And ``chown-socket`` is what lets nginx reach the socket at all.

``harakiri`` is uWSGI's request timeout and plays the role gunicorn's ``--timeout``
plays above. ``touch-reload`` is worth adding if you want a file touch rather than a
service restart to recycle the workers after an import.

.. _dev_guide_web_server_apache:

Apache with mod_wsgi
--------------------

This is the Node's own arrangement. It differs from the two above in one important
respect: **mod_wsgi has no directive for a per-process environment variable**, so
``OPUS_CONFIG`` has to reach the daemon process another way.

Two things that look like they would work and do not:

* ``SetEnv OPUS_CONFIG ...`` in the vhost populates the WSGI **request** environ, which
  is long after :mod:`opus_app.wsgi` has imported the settings.
* Exporting it in the shell that runs a deploy script does not reach Apache, which is
  started by init.

What works is putting it in the environment **Apache itself starts with**. On Debian and
Ubuntu, ``apache2ctl`` sources ``/etc/apache2/envvars`` before starting the server, and
daemon processes inherit from there::

    # /etc/apache2/envvars
    export OPUS_CONFIG=/etc/opus/opus.toml

A server running several OPUS installations cannot share one such variable. Give each
its own Apache instance, or give each a wrapper module of its own that assigns
``os.environ['OPUS_CONFIG']`` **before** importing :mod:`opus_app.wsgi`. Two things about
that wrapper: the vhost's ``WSGIScriptAlias`` has to name **it** rather than ``wsgi.py``,
and it must live somewhere the deploy chain does not touch -- ``_opus_setup_environment.sh``
and ``deploy_new_code_only.sh`` both re-create ``<installation>/wsgi.py`` as a symlink on
every deploy, so a hand-written file at that path does not survive one.

.. code-block:: python

    # /etc/opus/other_wsgi.py -- outside every installation directory
    import os

    os.environ['OPUS_CONFIG'] = '/etc/opus/other.toml'

    from opus_app.wsgi import application  # noqa: E402  (must follow the assignment)

    __all__ = ['application']

The vhost
~~~~~~~~~

.. code-block:: apache

    <VirtualHost *:443>
        # ServerName must appear in the allowed_hosts setting.
        ServerName opus.example.org

        SSLEngine on
        SSLCertificateFile    /etc/ssl/certs/opus.example.org.pem
        SSLCertificateKeyFile /etc/ssl/private/opus.example.org.key

        # The daemon process. python-home is the virtual environment; the
        # application is imported inside it.
        WSGIDaemonProcess opus \
            user=opus group=opus \
            processes=4 threads=2 \
            python-home=/opus/src/rms-opus/opus_venv
        WSGIProcessGroup opus
        WSGIApplicationGroup %{GLOBAL}

        # The installed wsgi.py. See the note below about this path.
        WSGIScriptAlias / /opus/src/rms-opus/wsgi.py

        <Directory /opus/src/rms-opus>
            <Files wsgi.py>
                Require all granted
            </Files>
        </Directory>

        # The static files collectstatic gathered.
        Alias /static_media/ /opus/static_media/
        <Directory /opus/static_media>
            Require all granted
            Options -Indexes
        </Directory>

        # The PDS data products.
        Alias /holdings/ /pds/holdings/
        <Directory /pds/holdings>
            Require all granted
            Options -Indexes +FollowSymLinks
        </Directory>
        Alias /pds4-holdings/ /pds/pds4-holdings/
        <Directory /pds/pds4-holdings>
            Require all granted
            Options -Indexes +FollowSymLinks
        </Directory>

        # Cart archives.
        Alias /downloads/ /opus/downloads/
        <Directory /opus/downloads>
            Require all granted
            Options -Indexes
        </Directory>

        # Building a cart archive is slow.
        Timeout 300

        ErrorLog  ${APACHE_LOG_DIR}/opus_error.log
        CustomLog ${APACHE_LOG_DIR}/opus_access.log combined
    </VirtualHost>

``WSGIApplicationGroup %{GLOBAL}`` puts the application in the main interpreter, which is
what C extensions -- the MySQL driver among them -- want.

The ``wsgi.py`` path
~~~~~~~~~~~~~~~~~~~~

``WSGIScriptAlias`` takes a file path, and the installed module lives inside the virtual
environment's ``site-packages``, whose path contains the Python minor version. **Naming
it directly means editing the vhost after every Python upgrade.**

The deploy chain avoids that by writing a **symlink at a fixed path** and re-pointing it
on every deploy, which is why the vhost above names ``/opus/src/rms-opus/wsgi.py`` rather
than a path under ``site-packages``. To create one by hand::

    OPUS_WSGI=$(/opus/src/rms-opus/opus_venv/bin/python -c \
      'import importlib.util; print(importlib.util.find_spec("opus_app.wsgi").origin)')
    ln -sfn "$OPUS_WSGI" /opus/src/rms-opus/wsgi.py

:func:`importlib.util.find_spec` locates the file **without importing it**. Importing
:mod:`opus_app.wsgi` would build the application -- configuring Django and opening the log
file -- which is not something a deploy step should do.

The access log
~~~~~~~~~~~~~~

:mod:`opus_log_analyzer` reads Apache access logs in the combined format the vhost above
writes, and turns them into per-session reports of what users did. It is the only
consumer of these logs, and :ref:`dev_guide_log_analyzer` describes it. There is nothing
equivalent for nginx's own log format.

.. _dev_guide_web_server_checklist:

Checking it
-----------

In order, because each check depends on the one before. The first runs a server in
the foreground and does not return, so give it a terminal of its own and run the rest in
another::

    # The application starts and the configuration reaches it. `env` is load-bearing:
    # a default sudoers resets the environment and refuses to pass OPUS_CONFIG through.
    sudo -u opus env OPUS_CONFIG=/etc/opus/opus.toml \
        /opus/src/rms-opus/opus_venv/bin/gunicorn \
        --bind 127.0.0.1:8001 opus_app.wsgi:application

Then, in a second terminal::

    # The web server proxies to it.
    curl -sI https://opus.example.org/ | head -1

    # Static files are served by the web server, not by Django.
    curl -sI https://opus.example.org/static_media/js/opus.js | head -1

    # A data product resolves. Directory listing is off, so ask for a real file --
    # take one out of api/files below, or off the Details tab.
    curl -sI https://opus.example.org/holdings/<a logical path> | head -1

    # The application can reach the database.
    curl -s 'https://opus.example.org/api/meta/result_count.json?planet=Saturn'

    # A real search returns rows.
    curl -s 'https://opus.example.org/api/data.json?planet=Saturn&limit=2'

Common failures and what they mean:

.. list-table::
   :header-rows: 1
   :widths: 38 62

   * - Symptom
     - Cause
   * - The application will not start, with a configuration error
     - ``OPUS_CONFIG`` did not reach the worker. Under mod_wsgi this is nearly always
       ``/etc/apache2/envvars``.
   * - Every page is a 400 with "Invalid HTTP_HOST header"
     - The server's name is not in ``allowed_hosts``.
   * - The page loads unstyled and the interface does not work
     - ``/static_media/`` is not being served, or ``collectstatic`` has not been run.
   * - Every product link 404s
     - ``/holdings/`` is not aliased, or ``product_http_path`` names a host that does not
       serve it.
   * - Searches work but a cart download times out
     - The proxy or server timeout is shorter than the archive takes to build.
   * - Results are stale after an import
     - The shared cache was not flushed, or the workers were not restarted. See
       :ref:`dev_guide_deployment`.

Where to go next
----------------

:ref:`dev_guide_installation`
    What has to exist before any of this.

:ref:`dev_guide_deployment`
    The Node's deploy chain, and the runbook for replacing a database.

API reference
-------------

:doc:`api_opus_app`
