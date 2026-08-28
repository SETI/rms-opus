"""Tests for the shell script that writes a server installation's ``opus.toml``.

``scripts/server/import_and_deploy/_write_opus_toml.sh`` is the only part of the
deploy chain that can be exercised away from a server, and it is the part whose
failures are silent: a mis-escaped password produces a file the loader rejects at
startup, and an unset variable used to produce a file the loader *accepts* with an
empty Django secret key in it.

These tests run the shipped script -- not a copy of it, and not a re-implementation of
its heredoc -- under ``bash`` with a controlled environment, then load what it wrote
through :func:`opus_config.load_config`. That is the technique the CI-side
generator's own tests use to prove the same properties, reused here.
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
    empty string and Django ran with no secret key. The explicit ``[[ ! -v ]]`` loop is
    what makes each one fatal *by name*; ``set -u`` alone would stop the run too, but
    reporting ``!_toml_var: unbound variable`` -- this script's own loop variable rather
    than the one the operator has to fix.
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


@pytest.mark.parametrize('placeholder', ['OPUS_SECRET_KEY', 'OPUS_DB_PASSWORD', 'OPUS_DIR'])
def test_an_unfilled_placeholder_is_refused(tmp_path: Path, placeholder: str) -> None:
    """A value still carrying the template's ``<PLACEHOLDER>`` is refused by name.

    The reader catches this too, but this program is deliberately runnable on its own,
    so it cannot assume it was called through the reader. Without the check a direct
    invocation writes ``password = "<OPUS_DB_PASSWORD>"`` into a file that then loads
    perfectly well -- a configuration that is wrong in a way nothing downstream objects
    to.
    """
    result = _generate(tmp_path, **{placeholder: f'<{placeholder}>'})
    assert result.returncode == 1
    assert f'{placeholder} is still the <PLACEHOLDER>' in result.stderr
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
    """The file holds the database password and the Django secret key, so it ends 0600."""
    assert _generate(tmp_path).returncode == 0
    mode = stat.S_IMODE((tmp_path / 'opus.toml').stat().st_mode)
    assert mode == 0o600, oct(mode)


@pytest.mark.skipif(
    hasattr(os, 'geteuid') and os.geteuid() == 0,
    reason='root ignores the directory permissions this test uses to strand the temp file',
)
def test_the_file_is_never_world_readable_even_briefly(
    tmp_path: Path, request: pytest.FixtureRequest
) -> None:
    """``umask 077`` guards the *write*, not just the final mode.

    The trailing ``chmod 600`` fixes the mode after the fact, so the test above passes
    with the ``( umask 077; ... )`` subshell deleted -- while the file spends the whole
    of its write world-readable with the password already in it. That window is the
    property at issue, and this is what defends it: the temporary file is created
    under a deliberately permissive umask and its mode is read before the chmod can
    hide the difference.

    Race-free, and without needing to catch the file mid-write: the destination is
    pre-created as a directory the process cannot write into, so the rename fails while
    the temporary file -- written in the parent, which is writable -- is left on disk
    carrying exactly the mode it was created with. (A *writable* directory would not
    do: ``mv file dir`` moves the file into it and succeeds.)
    """
    destination = tmp_path / 'opus.toml'
    destination.mkdir(mode=0o500)
    # Restored unconditionally: a mode-0500 directory left behind by a *failing*
    # assertion below defeats pytest's tmp_path cleanup, which then fails unrelated
    # tests in later runs. Observed, not theorised.
    request.addfinalizer(lambda: destination.chmod(0o700))

    # A pre-existing temporary file would make this measure the wrong thing, and
    # silently: `cat > file` truncates without changing the mode of a file that already
    # exists, so a stale 0600 leftover would report success while the umask was broken.
    # (Observed: a leftover from a run with the subshell deliberately removed inverted
    # this test's result.) tmp_path is fresh per test, so this asserts an invariant
    # rather than papering over one.
    leftover = Path(f'{destination}.tmp')
    assert not leftover.exists(), 'a stale temporary file would invalidate this measurement'

    env = {'PATH': os.environ.get('PATH', '/usr/bin:/bin'), **BASE_ENV}
    result = subprocess.run(
        ['bash', '-c', 'umask 000; exec "$0" "$1"', str(SCRIPT), str(destination)],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    # The rename fails, so the run fails -- what matters is the mode of what it left.
    assert result.returncode != 0
    assert leftover.exists(), 'the generator did not get as far as writing the temp file'
    mode = stat.S_IMODE(leftover.stat().st_mode)
    assert mode & 0o077 == 0, (
        f'temp file created {oct(mode)} under a permissive umask: the umask 077 '
        f'subshell is not protecting the write'
    )


@pytest.mark.skipif(
    hasattr(os, 'geteuid') and os.geteuid() == 0,
    reason='root ignores the directory permissions this test uses to strand the temp file',
)
def test_a_stale_temporary_file_does_not_keep_its_permissions(
    tmp_path: Path, request: pytest.FixtureRequest
) -> None:
    """A leftover temporary file is removed before the write, not written over.

    ``cat >`` truncates an existing file but does not change its mode, so writing over a
    world-readable leftover would keep those permissions and ``umask 077`` would protect
    nothing -- the password and the secret key would sit in a readable file until the
    trailing ``chmod``. This is the production twin of the trap found in the umask test
    one layer up, and it is why the generator ``rm -f``s first.

    It has to inspect the file *mid-flight*, for the same reason that test does: on a
    successful run the mode is renamed away and then chmod'd, so the end state is
    identical whether or not the leftover was removed. The first version of this test
    asserted the end state and passed with the ``rm -f`` deleted -- the same
    check-that-cannot-fail shape, caught by mutating the guard it was written for. So
    the destination is again a directory the process cannot write into, stranding the
    temporary file with the mode it was actually created with.
    """
    destination = tmp_path / 'opus.toml'
    destination.mkdir(mode=0o500)
    request.addfinalizer(lambda: destination.chmod(0o700))

    stale = Path(f'{destination}.tmp')
    stale.write_text('left over from an earlier run\n')
    stale.chmod(0o666)

    env = {'PATH': os.environ.get('PATH', '/usr/bin:/bin'), **BASE_ENV}
    result = subprocess.run(
        ['bash', str(SCRIPT), str(destination)],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    assert result.returncode != 0
    assert stale.exists(), 'the generator did not get as far as writing the temp file'
    mode = stat.S_IMODE(stale.stat().st_mode)
    assert mode & 0o077 == 0, (
        f'the temporary file kept the stale mode {oct(mode)}: `cat >` truncated an '
        f'existing file instead of the generator removing it first'
    )


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
