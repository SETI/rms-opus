#!/usr/bin/env python
"""Django's command-line utility for this checkout.

It is a development convenience -- `check`, `migrate`, `shell`, `collectstatic` -- and
carries no OPUS-specific commands of its own.

**The test suites are run with pytest, not through this script.** `pytest` runs the
holdings-free unit suite and `pytest integration_tests` runs the live-database suites;
the invocations, including how to point the API suite at a deployed server and how to
profile a run, are in `integration_tests/test_api/TEST_API_README.md`. `manage.py test`
is Django's own command and nothing here configures it: a bare `manage.py test`
discovers the whole repository, and pytest selects by path and by marker instead.

Every command needs `OPUS_CONFIG` set, because `opus_app.settings` reads the OPUS
configuration file and there is no default location for it.
"""

import os
import sys

from django.core.management import execute_from_command_line

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE',    'opus_app.settings')
    execute_from_command_line(sys.argv)
