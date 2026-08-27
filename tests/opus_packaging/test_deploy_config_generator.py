"""Tests for the shell script that writes a server installation's ``opus.toml``.

``scripts/server/import_and_deploy/_write_opus_toml.sh`` is the only part of the
deploy chain that can be exercised away from a server, and it is the part whose
failures are silent: a mis-escaped password produces a file the loader rejects at
startup, and an unset variable used to produce a file the loader *accepts* with an
empty Django secret key in it.

These tests run the shipped script -- not a copy of it, and not a re-implementation of
its heredoc -- under ``bash`` with a controlled environment, then load what it wrote
through :func:`opus_config.load_config`. That is the technique PR-08 used to prove the
same properties of the CI-side generator, reused here as the plan directs.
"""

from __future__ import annotations

import os
import stat
import subprocess
from pathlib import Path

import pytest

from opus_config import ConfigError, load_config

SCRIPT = (
    Path(__file__).resolve().parents[2]
    / 'scripts'
    / 'server'
    / 'import_and_deploy'
    / '_write_opus_toml.sh'
)

# A complete, valid environment. Each test copies this and changes one thing, so a
# failure names the one variable that caused it.
BASE_ENV = {
    'OPUS_DB_NAME': 'opus3_20260827T000000_1',
    'OPUS_DB_USER': 'opus_user',
    'OPUS_DB_PASSWORD': 'plain-password',
    'PDS3_HOLDINGS_DIR': '/pds/holdings',
    'PDS4_HOLDINGS_DIR': '/pds/pds4-holdings',
    'OPUS_LOG_DIR': '/opus/opus_logs',
    'OPUS_DIR': '/opus',
    'LAST_BLOG_UPDATE_FILE': '/opus/data/last_update.txt',
    'NOTIFICATION_FILE': '/opus/data/notification.html',
    'OPUS_SECRET_KEY': 'a-secret-key',
    'OPUS_DEBUG': 'false',
    'OPUS_PUBLIC_URL': 'https://opus.pds-rings.seti.org/',
    'OPUS_PRODUCT_HTTP_PATH': 'https://opus.pds-rings.seti.org/',
    'OPUS_VIEWMASTER_URL': 'https://pds-rings.seti.org/',
    'OPUS_TAR_FILE_URL': 'https://opus.pds-rings.seti.org/downloads/',
}

pytestmark = pytest.mark.skipif(
    os.name != 'posix', reason='the deploy chain is bash, and runs only on the servers'
)


def _generate(tmp_path: Path, **overrides: str) -> subprocess.CompletedProcess[str]:
    """Run the generator with ``BASE_ENV`` plus *overrides*, writing into *tmp_path*.

    The environment is built from scratch rather than inherited, so a variable the
    script needs cannot be satisfied by whatever happens to be set in the session
    running the tests -- which would make the unset-variable test pass for the wrong
    reason. PATH is kept because the script calls ``sed`` and ``mv``.
    """
    env = {'PATH': os.environ.get('PATH', '/usr/bin:/bin'), **BASE_ENV, **overrides}
    return subprocess.run(
        ['bash', str(SCRIPT), str(tmp_path / 'opus.toml')],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )


def test_the_generated_file_loads(tmp_path: Path) -> None:
    """A complete environment produces a file ``opus_config`` accepts.

    This is the property that matters most and the one a deploy discovers last: the
    generator and the loader are written independently, and nothing else compares
    them.
    """
    result = _generate(tmp_path)
    assert result.returncode == 0, result.stderr

    config = load_config(tmp_path / 'opus.toml')
    assert config.database.schema == BASE_ENV['OPUS_DB_NAME']
    assert config.database.user == BASE_ENV['OPUS_DB_USER']
    assert config.database.password == BASE_ENV['OPUS_DB_PASSWORD']
    assert config.django.secret_key == BASE_ENV['OPUS_SECRET_KEY']
    assert config.django.debug is False
    assert str(config.paths.pds3_holdings) == BASE_ENV['PDS3_HOLDINGS_DIR']
    assert str(config.paths.pds4_holdings) == BASE_ENV['PDS4_HOLDINGS_DIR']


def test_debug_true_reaches_the_loader_as_a_boolean(tmp_path: Path) -> None:
    """``OPUS_DEBUG`` is written as a TOML boolean, not as a quoted string."""
    result = _generate(tmp_path, OPUS_DEBUG='true')
    assert result.returncode == 0, result.stderr
    assert load_config(tmp_path / 'opus.toml').django.debug is True


@pytest.mark.parametrize(
    'password',
    [
        'has"a quote',
        r'has\a backslash',
        r'has"both\kinds',
        r'ends with a backslash\\',
        '"',
    ],
)
def test_a_password_needing_escaping_round_trips(tmp_path: Path, password: str) -> None:
    """The two characters a TOML basic string gives meaning to survive unchanged.

    A backslash escapes and a double quote ends the string, so an unescaped one either
    corrupts the value or makes the file unparseable. Round-tripping through the real
    loader is what distinguishes "escaped" from "escaped correctly".
    """
    result = _generate(tmp_path, OPUS_DB_PASSWORD=password)
    assert result.returncode == 0, result.stderr
    assert load_config(tmp_path / 'opus.toml').database.password == password


@pytest.mark.parametrize('control', ['\n', '\t', '\r', '\x0b'])
def test_a_control_character_is_refused_before_anything_is_written(
    tmp_path: Path, control: str
) -> None:
    """TOML forbids a literal control character in a quoted value, so it is rejected.

    Escaping quotes and backslashes is not enough on its own: no escape the shell can
    write smuggles a control character into a basic string. The generator refuses the
    value rather than emitting a file its own loader would reject at startup, and it
    refuses it *before* writing, so no partial file is left behind.
    """
    result = _generate(tmp_path, OPUS_DB_PASSWORD=f'pass{control}word')
    assert result.returncode == 1
    assert 'OPUS_DB_PASSWORD' in result.stderr
    assert not (tmp_path / 'opus.toml').exists()
    assert not (tmp_path / 'opus.toml.tmp').exists()


@pytest.mark.parametrize('missing', ['OPUS_SECRET_KEY', 'OPUS_DB_PASSWORD', 'OPUS_DIR'])
def test_an_unset_variable_stops_the_generator(tmp_path: Path, missing: str) -> None:
    """A variable the deploy environment forgot stops the run instead of emptying a field.

    This is the failure the old chain did not have: its reader validated seven
    variables and not ``OPUS_SECRET_KEY``, so an unset one reached opus.toml as an
    empty string and Django ran with no secret key. ``set -u`` in the generator makes
    every one of them fatal.
    """
    env = dict(BASE_ENV)
    del env[missing]
    full = {'PATH': os.environ.get('PATH', '/usr/bin:/bin'), **env}
    result = subprocess.run(
        ['bash', str(SCRIPT), str(tmp_path / 'opus.toml')],
        capture_output=True,
        text=True,
        check=False,
        env=full,
    )
    assert result.returncode != 0
    assert missing in result.stderr
    assert not (tmp_path / 'opus.toml').exists()


@pytest.mark.parametrize('empty', ['OPUS_SECRET_KEY', 'OPUS_DB_PASSWORD', 'OPUS_DB_NAME'])
def test_an_empty_variable_stops_the_generator(tmp_path: Path, empty: str) -> None:
    """A variable that is set but empty is refused as well as one that is unset.

    Being set to nothing is the shape the old failure actually took -- a deploy.env
    line present with nothing after the ``=`` -- and it writes a syntactically valid
    file, so nothing downstream would object.
    """
    result = _generate(tmp_path, **{empty: ''})
    assert result.returncode == 1
    assert empty in result.stderr
    assert not (tmp_path / 'opus.toml').exists()


@pytest.mark.parametrize('bad', ['True', 'yes', '1', 'false '])
def test_a_non_boolean_debug_value_is_refused(tmp_path: Path, bad: str) -> None:
    """``debug`` is a TOML boolean, so anything but ``true``/``false`` is refused.

    Written unchecked, ``OPUS_DEBUG=yes`` produces ``debug = yes``, which is not valid
    TOML -- a failure that would surface only when the application next started.
    """
    result = _generate(tmp_path, OPUS_DEBUG=bad)
    assert result.returncode == 1
    assert 'OPUS_DEBUG' in result.stderr
    assert not (tmp_path / 'opus.toml').exists()


def test_the_generated_file_is_not_readable_by_anyone_else(tmp_path: Path) -> None:
    """The file holds the database password and the Django secret key, so it is 0600."""
    assert _generate(tmp_path).returncode == 0
    mode = stat.S_IMODE((tmp_path / 'opus.toml').stat().st_mode)
    assert mode == 0o600, oct(mode)


def test_no_temporary_file_survives_a_successful_run(tmp_path: Path) -> None:
    """The file is written under a temporary name and *renamed*, never copied.

    The rename is what makes the write atomic, so the destination is never briefly
    present with the caller's umask while it already holds the password and the secret
    key. A copy would leave the temporary file behind -- created under ``umask 077``,
    so not a disclosure, but the leftover is the only externally visible difference
    between the two, and without this the atomicity is untested on the path that
    succeeds.
    """
    assert _generate(tmp_path).returncode == 0
    assert (tmp_path / 'opus.toml').is_file()
    assert not (tmp_path / 'opus.toml.tmp').exists()


def test_the_script_refuses_to_run_without_an_output_path(tmp_path: Path) -> None:
    """The output path is a required argument, not a default the caller can forget."""
    env = {'PATH': os.environ.get('PATH', '/usr/bin:/bin'), **BASE_ENV}
    result = subprocess.run(
        ['bash', str(SCRIPT)], capture_output=True, text=True, check=False, env=env
    )
    assert result.returncode == 2
    assert 'Usage' in result.stderr


def test_a_corrupted_value_is_reported_by_the_loader_rather_than_accepted(
    tmp_path: Path,
) -> None:
    """A file the generator did not write is rejected, which is what makes the rest mean something.

    Every test above asserts that :func:`load_config` accepts what the generator
    produced. That is only evidence if the loader can also reject: this mutates one
    generated line and confirms it does.
    """
    assert _generate(tmp_path).returncode == 0
    path = tmp_path / 'opus.toml'
    path.write_text(path.read_text().replace('debug = false', 'debug = "false"'))
    with pytest.raises(ConfigError):
        load_config(path)
