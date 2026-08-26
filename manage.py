#!/usr/bin/env python
"""Django's command-line utility for this checkout.

It is a development convenience -- `check`, `migrate`, `shell`, `collectstatic` --
and is deliberately not part of the wheel; a deployed server runs `django-admin`
with `DJANGO_SETTINGS_MODULE=opus_app.settings` instead.

**The test suites are not run through this script.** `pytest` runs both of them:
`pytest` alone for the holdings-free unit suite and `pytest integration_tests` for
the live-database suites, whose invocations are in
`integration_tests/test_api/TEST_API_README.md`. `manage.py test` still exists
because it is Django's own command, but nothing configures it here: a bare
`manage.py test` discovers the whole repository, and the custom `api-*` verbs that
used to select the API suites are gone -- pytest selects by path and by marker.

Every command needs `OPUS_CONFIG` set, because `opus_app.settings` reads the OPUS
configuration file and there is no default location for it.
"""

import os
import sys

from django.core.management import execute_from_command_line

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'opus_app.settings')
    execute_from_command_line(sys.argv)
