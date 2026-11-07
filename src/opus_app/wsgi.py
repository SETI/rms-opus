"""WSGI entry point for the OPUS web application.

Point the web server at ``opus_app.wsgi:application`` (mod_wsgi's
``WSGIScriptAlias`` takes this file's installed path). The application is
importable straight from the installed distribution and needs no sys.path setup,
but ``OPUS_CONFIG`` must be set in the server's environment: it names the OPUS
configuration file, and there is no default location for it.

The schema is checked once, as this module loads (`opus_app.schema_guard`): unless
its ``schema_version`` row holds this release's version in the ``ready`` state,
``application`` answers every request 503 with a body naming the remedy. The
development server loads this module too (``WSGI_APPLICATION`` in the settings), so
it serves the same 503.
"""

import os

from django.core.wsgi import get_wsgi_application

from opus_app.schema_guard import guard

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'opus_app.settings')

application = guard(get_wsgi_application())
