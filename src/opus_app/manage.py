"""The installed distribution's Django management command.

Django's own ``django-admin`` has to be told which settings module to use, and it can
only be told through the environment. An installed OPUS has no ``manage.py`` to imply it
-- that file belongs to a checkout and is not in the wheel -- so every operator running a
management command would otherwise have to export ``DJANGO_SETTINGS_MODULE`` alongside
``OPUS_CONFIG``, and a deployment that forgot it would fail in a way that says nothing
about OPUS.

``opus_manage`` is that one line of glue and nothing else. It names the settings module
and hands the command line straight to Django, so ``OPUS_CONFIG`` is the only variable an
OPUS installation needs::

    OPUS_CONFIG=/etc/opus/opus.toml opus_manage migrate

The checkout's own ``manage.py`` calls `main` as well, so the two forms cannot drift, and
``django-admin`` with ``DJANGO_SETTINGS_MODULE`` set does the same thing for anyone who
prefers it.
"""

import os
import sys

from django.core.management import execute_from_command_line


def main() -> None:
    """Run the Django management command named on the command line.

    The subcommands are Django's own -- ``check``, ``migrate``, ``collectstatic``,
    ``shell``, ``diffsettings`` and the rest -- because OPUS adds none of its own. The
    import pipeline is ``opus_import``, and the test suites are run with ``pytest``.

    The settings module is set rather than forced, as :mod:`opus_app.wsgi` sets it: a
    value already in the environment is left alone, so a deployment can still point
    Django at a settings module of its own that imports this one.

    Raises:
        SystemExit: With a non-zero status, from Django, when the command fails or names
            a subcommand that does not exist.
    """
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'opus_app.settings')
    execute_from_command_line(sys.argv)
