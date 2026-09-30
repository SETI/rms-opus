"""Where the mini-holdings suite finds a MySQL server to import into.

The suite and the golden generator both ask this module, so a golden is regenerated
against the server the suite is checked against rather than whichever one a second set of
defaults happened to name.

Two sources, in order, and a default under both. ``OPUS_TEST_DB_HOST``,
``OPUS_TEST_DB_USER`` and
``OPUS_TEST_DB_PASSWORD`` name a server for the suite alone, which is what the CI job
sets: its MySQL is a service container holding nothing else. With none of them set, the
credentials come out of the ``[database]`` table of the configuration file ``OPUS_CONFIG``
names -- which every run of the suite already has, because ``pytest-django`` configures
Django from that file at collection, so pointing the suite at a developer's own server
costs no second set of variables.

Only the host, user and password are read from that file. The schema it names is not: a
run imports into schemas of its own, named by `import_tests.tools.fixture_layout`, and
drops every one of them when the session ends, so an installation's own data is never
what a run writes to or drops.
"""

from __future__ import annotations

import os

from import_tests.tools.golden_io import DatabaseCredentials
from opus_config import OPUS_CONFIG_ENV_VAR, load_config

#: Where the suite reads a server of its own from.
HOST_ENV_VAR = 'OPUS_TEST_DB_HOST'
USER_ENV_VAR = 'OPUS_TEST_DB_USER'
PASSWORD_ENV_VAR = 'OPUS_TEST_DB_PASSWORD'

#: What it falls back to when neither the environment nor a configuration file says. The
#: host is an address rather than ``localhost`` on purpose: MySQLdb reads ``localhost`` as
#: a request for a Unix socket, which exists on a developer's machine and not beside a CI
#: service container.
DEFAULT_HOST = '127.0.0.1'
DEFAULT_USER = 'root'


def resolve_credentials() -> DatabaseCredentials:
    """Return how to reach the MySQL server a run imports into.

    The three variables are read as a set rather than one at a time: if any of them is
    set, the environment is what describes the server and the other two take their
    defaults. Reading them individually would pair one server's user with another
    server's password on a machine that has both a configuration file and one of the
    variables exported.

    Returns:
        The credentials the environment names; the ones the ``OPUS_CONFIG`` file holds,
        when the environment names none; or `DEFAULT_HOST` and `DEFAULT_USER` with no
        password, when there is no configuration file either.

    Raises:
        ConfigError: If no test variable is set and the file ``OPUS_CONFIG`` names cannot
            be read or does not match the schema. That variable is what the run was
            pointed at, so a file that cannot be read is an error rather than a reason to
            fall back to a server nobody named.
    """
    if any(name in os.environ for name in (HOST_ENV_VAR, USER_ENV_VAR, PASSWORD_ENV_VAR)):
        return DatabaseCredentials(
            host=os.environ.get(HOST_ENV_VAR, DEFAULT_HOST),
            user=os.environ.get(USER_ENV_VAR, DEFAULT_USER),
            password=os.environ.get(PASSWORD_ENV_VAR, ''),
        )
    config_file = os.environ.get(OPUS_CONFIG_ENV_VAR)
    if config_file:
        database = load_config(config_file).database
        return DatabaseCredentials(
            host=database.host, user=database.user, password=database.password
        )
    return DatabaseCredentials(host=DEFAULT_HOST, user=DEFAULT_USER, password='')
