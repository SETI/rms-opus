"""WSGI entry point for the OPUS web application.

Point the web server at ``opus_app.wsgi:application`` (mod_wsgi's
``WSGIScriptAlias`` takes this file's installed path). The application is
importable straight from the installed distribution and needs no sys.path setup,
but ``OPUS_CONFIG`` must be set in the server's environment: it names the OPUS
configuration file, and there is no default location for it.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'opus_app.settings')

application = get_wsgi_application()
