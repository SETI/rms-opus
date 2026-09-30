#!/usr/bin/env python
"""Django's command-line utility for this checkout.

It is a development convenience -- `check`, `migrate`, `shell`, `collectstatic` -- and
carries no OPUS-specific commands of its own. It is the same program as the installed
`opus_manage` command, which is what a deployment with no checkout runs: both call
`opus_app.manage.main`, so neither can drift from the other.

**The test suites are run with pytest, not through this script.** `pytest` runs the
holdings-free unit suite and `pytest integration_tests` runs the live-database suites;
the invocations, including how to point the API suite at a deployed server and how to
profile a run, are in `integration_tests/test_api/TEST_API_README.md`. `manage.py test`
is Django's own command and nothing here configures it: a bare `manage.py test`
discovers the whole repository, and pytest selects by path and by marker instead.

Every command needs `OPUS_CONFIG` set, because `opus_app.settings` reads the OPUS
configuration file and there is no default location for it. Nothing else has to be set:
`DJANGO_SETTINGS_MODULE` is what `opus_app.manage` supplies.

This file also fixes what pytest-django puts on `sys.path`: it puts the directory
holding `manage.py` there, which is how `integration_tests` and `import_tests` are
importable from the repository root.
"""

from opus_app.manage import main

if __name__ == '__main__':
    main()
