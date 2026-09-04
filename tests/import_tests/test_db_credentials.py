"""Tests for the server the mini-holdings suite imports into.

`import_tests.tools.db_credentials` decides which MySQL server ``pytest import_tests``
and the golden generator connect to. Nothing in the import suite itself can pin that
choice: by the time a run exists, the choice has already been made, and a wrong one shows
up as a connection error or -- worse, on a machine that has both servers -- as a run
against something other than what was asked for.

So the rules live here, in the holdings-free run, where the environment can be varied
without a database being reachable at all. `import_tests` is importable because
pytest-django puts the directory holding ``manage.py`` on ``sys.path`` at startup.
"""

from pathlib import Path

import pytest

from import_tests.tools.db_credentials import (
    DEFAULT_HOST,
    DEFAULT_USER,
    HOST_ENV_VAR,
    PASSWORD_ENV_VAR,
    USER_ENV_VAR,
    resolve_credentials,
)
from opus_config import OPUS_CONFIG_ENV_VAR, ConfigError

#: The ``[database]`` values ``tests/fixtures/opus_ci.toml`` holds, which is the file the
#: configuration cases below are resolved against.
CI_CONFIG_HOST = 'localhost'
CI_CONFIG_USER = 'opus_ci_user'
CI_CONFIG_PASSWORD = 'opus_ci_password'


@pytest.fixture
def unset_test_variables(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove the three ``OPUS_TEST_DB_*`` variables from the environment.

    Whoever is running the suite may have any of them exported, and a test of what
    happens when none is set has to hold whatever the developer's shell says.

    Parameters:
        monkeypatch: The patcher, which restores the environment afterwards.
    """
    for name in (HOST_ENV_VAR, USER_ENV_VAR, PASSWORD_ENV_VAR):
        monkeypatch.delenv(name, raising=False)


def test_environment_names_the_server(
    monkeypatch: pytest.MonkeyPatch, ci_config_path: Path
) -> None:
    """All three variables set is what CI does, and it wins over the configuration file."""
    monkeypatch.setenv(OPUS_CONFIG_ENV_VAR, str(ci_config_path))
    monkeypatch.setenv(HOST_ENV_VAR, '127.0.0.1')
    monkeypatch.setenv(USER_ENV_VAR, 'root')
    monkeypatch.setenv(PASSWORD_ENV_VAR, 'opus_import_tests')

    credentials = resolve_credentials()

    assert credentials.host == '127.0.0.1'
    assert credentials.user == 'root'
    assert credentials.password == 'opus_import_tests'


@pytest.mark.usefixtures('unset_test_variables')
@pytest.mark.parametrize('name', [HOST_ENV_VAR, USER_ENV_VAR, PASSWORD_ENV_VAR])
def test_one_variable_makes_the_environment_the_only_source(
    monkeypatch: pytest.MonkeyPatch, ci_config_path: Path, name: str
) -> None:
    """The three are read as a set, so one of them set means the file is not read.

    Reading them one at a time would pair the file's user with the environment's
    password on a machine that has both, which is a login failure whose cause is in
    neither place.
    """
    monkeypatch.setenv(OPUS_CONFIG_ENV_VAR, str(ci_config_path))
    monkeypatch.setenv(name, 'from-the-environment')

    credentials = resolve_credentials()

    assert credentials.host == ('from-the-environment' if name == HOST_ENV_VAR else DEFAULT_HOST)
    assert credentials.user == ('from-the-environment' if name == USER_ENV_VAR else DEFAULT_USER)
    assert credentials.password == ('from-the-environment' if name == PASSWORD_ENV_VAR else '')


@pytest.mark.usefixtures('unset_test_variables')
def test_configuration_file_supplies_the_server(
    monkeypatch: pytest.MonkeyPatch, ci_config_path: Path
) -> None:
    """With no variable set, the host, user and password come out of ``OPUS_CONFIG``."""
    monkeypatch.setenv(OPUS_CONFIG_ENV_VAR, str(ci_config_path))

    credentials = resolve_credentials()

    assert credentials.host == CI_CONFIG_HOST
    assert credentials.user == CI_CONFIG_USER
    assert credentials.password == CI_CONFIG_PASSWORD


@pytest.mark.usefixtures('unset_test_variables')
def test_neither_source_falls_back_to_a_local_root(monkeypatch: pytest.MonkeyPatch) -> None:
    """With nothing set at all, the suite tries a passwordless root on the loopback address.

    A run of the suite always has ``OPUS_CONFIG``, because pytest-django reads it at
    collection; the golden generator is what can be run without it.
    """
    monkeypatch.delenv(OPUS_CONFIG_ENV_VAR, raising=False)

    credentials = resolve_credentials()

    assert credentials.host == DEFAULT_HOST
    assert credentials.user == DEFAULT_USER
    assert credentials.password == ''


@pytest.mark.usefixtures('unset_test_variables')
def test_an_unreadable_configuration_file_is_an_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A file that cannot be read stops the run rather than falling back.

    The variable is what the run was pointed at. Falling back would run the suite against
    a server nobody named, which on a developer's machine is a server holding real data.
    """
    monkeypatch.setenv(OPUS_CONFIG_ENV_VAR, str(tmp_path / 'absent.toml'))

    with pytest.raises(ConfigError, match='Cannot read the OPUS configuration file'):
        resolve_credentials()
