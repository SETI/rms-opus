"""Tests for the deploy chain's reader of its own ``secrets/deploy.env``.

``_read_deploy_env.sh`` is what every server script sources before it does anything
else, and it is the deploy's only chance to reject a bad environment *before* it stops
Apache. Its failure modes are all quiet ones: a key missing from ``deploy.env``, a key
left as the ``<PLACEHOLDER>`` the template ships, or a key present but empty. Quiet
because nothing downstream objects on its own: an empty ``OPUS_SECRET_KEY`` is a
well-formed TOML string, :func:`opus_config.load_config` reads it, and Django starts
with no secret key.

Like the generator tests beside them, these run the shipped script under ``bash``
rather than re-implementing what it does.
"""

from __future__ import annotations

import getpass
import os
import subprocess
from pathlib import Path

import pytest

SERVER_SCRIPTS = Path(__file__).resolve().parents[2] / 'src' / 'opus_deploy' / 'server'
READER = SERVER_SCRIPTS / 'import_and_deploy' / '_read_deploy_env.sh'
TEMPLATE = SERVER_SCRIPTS / 'deploy.env.template'

# The keys the reader requires. Stated here so a key added to the reader without a
# line in the template -- or the reverse -- fails a test rather than a deploy.
REQUIRED_KEYS = [
    'OPUS_DIR',
    'OPUS_DEPLOY_VENV',
    'OPUS_USER',
    'OPUS_DB_HOST',
    'OPUS_DB_USER',
    'OPUS_DB_PASSWORD',
    'OPUS_SECRET_KEY',
    'PDS3_HOLDINGS_DIR',
    'PDS4_HOLDINGS_DIR',
    'LAST_BLOG_UPDATE_FILE',
    'NOTIFICATION_FILE',
    'OPUS_DEBUG',
    'OPUS_ALLOWED_HOSTS',
    'OPUS_CACHE_PREFIX',
    'OPUS_PUBLIC_URL',
    'OPUS_PRODUCT_HTTP_PATH',
    'OPUS_VIEWMASTER_URL',
    'OPUS_TAR_FILE_URL',
    'OPUS_DB_DUMP_DIR',
]

# The keys that are optional: a server with no second server to copy a database to
# leaves the first two empty, and the reader supplies a default for the rest. It
# neither requires nor refuses any of them.
OPTIONAL_KEYS = [
    'OPUS_PEER_DB_HOST',
    'OPUS_IMPORT_MAIL_TO',
    'OPUS_PYTHON',
    'OPUS_WEB_SERVICE',
    'OPUS_CACHE_SERVICE',
]

pytestmark = pytest.mark.skipif(
    os.name != 'posix', reason='the deploy chain is bash, and runs only on the servers'
)


def _make_environment(tmp_path: Path, **overrides: str | None) -> Path:
    """Build a valid secrets directory under *tmp_path* and return it.

    The reader checks that the directories it is given exist, so they are created
    here; *overrides* replaces a value, or removes the line entirely when ``None``.
    """
    opus_dir = tmp_path / 'opus'
    pds3 = tmp_path / 'holdings'
    pds4 = tmp_path / 'pds4-holdings'
    (pds3 / 'volumes').mkdir(parents=True)
    (pds4 / 'bundles').mkdir(parents=True)
    opus_dir.mkdir()

    values: dict[str, str | None] = {
        'OPUS_DIR': str(opus_dir),
        'OPUS_DEPLOY_VENV': str(opus_dir / 'deploy_venv'),
        # The account running the tests: the reader refuses to be sourced by anyone but
        # the account deploy.env names, so this is what a valid file says here.
        'OPUS_USER': getpass.getuser(),
        'OPUS_DB_HOST': 'localhost',
        'OPUS_DB_USER': 'opus_user',
        'OPUS_DB_PASSWORD': 'a password',
        'OPUS_SECRET_KEY': 'a-secret-key',
        'PDS3_HOLDINGS_DIR': str(pds3),
        'PDS4_HOLDINGS_DIR': str(pds4),
        'LAST_BLOG_UPDATE_FILE': str(opus_dir / 'last_update.txt'),
        'NOTIFICATION_FILE': str(opus_dir / 'notification.html'),
        'OPUS_DEBUG': 'false',
        'OPUS_ALLOWED_HOSTS': '127.0.0.1 localhost opus.example.org',
        'OPUS_CACHE_PREFIX': 'production',
        'OPUS_PUBLIC_URL': 'https://opus.example.org/',
        'OPUS_PRODUCT_HTTP_PATH': 'https://opus.example.org/',
        'OPUS_VIEWMASTER_URL': 'https://viewmaster.example.org/',
        'OPUS_TAR_FILE_URL': 'https://opus.example.org/downloads/',
        'OPUS_DB_DUMP_DIR': str(opus_dir / 'dumps'),
        'OPUS_PEER_DB_HOST': '',
        'OPUS_IMPORT_MAIL_TO': '',
    }
    values.update(overrides)

    secrets = tmp_path / 'secrets'
    secrets.mkdir()
    lines = [f"{key}='{value}'" for key, value in values.items() if value is not None]
    (secrets / 'deploy.env').write_text('\n'.join(lines) + '\n')
    return secrets


def _read(secrets: Path | str, extra: str = '') -> subprocess.CompletedProcess[str]:
    """Source the reader with ``SECRETS_DIR`` set, then run *extra* shell after it."""
    script = f'set -e\nSECRETS_DIR="{secrets}"\nsource "{READER}"\n{extra}\n'
    return subprocess.run(
        ['bash', '-c', script],
        capture_output=True,
        text=True,
        check=False,
        env={'PATH': os.environ.get('PATH', '/usr/bin:/bin')},
    )


def test_a_complete_environment_is_accepted_and_exported(tmp_path: Path) -> None:
    """A filled-in deploy.env is accepted, and every value is exported.

    Exporting matters rather than merely being set: ``_write_opus_toml.sh`` runs as
    its own process, so a variable that is only set in the sourcing shell would reach
    it as unset.
    """
    secrets = _make_environment(tmp_path)
    probe = '\n'.join(
        f'bash -c \'[[ -n "${{{key}:-}}" ]]\' || {{ echo "NOT EXPORTED: {key}"; exit 1; }}'
        for key in REQUIRED_KEYS
    )
    result = _read(secrets, probe)
    assert result.returncode == 0, result.stdout + result.stderr


def test_the_optional_peer_host_may_be_empty(tmp_path: Path) -> None:
    """A server with nothing to copy a database to leaves it empty, and is accepted.

    Every other value is refused when empty, so this one has to be excused explicitly;
    without the exception a single-server installation could not be configured at all.
    """
    secrets = _make_environment(tmp_path, OPUS_PEER_DB_HOST='')
    result = _read(secrets, 'bash -c \'[[ -z "${OPUS_PEER_DB_HOST}" ]]\'')
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize(
    ('key', 'named', 'expected'),
    [
        ('OPUS_PYTHON', None, 'python3.12'),
        ('OPUS_PYTHON', 'python3.13', 'python3.13'),
        ('OPUS_WEB_SERVICE', None, 'apache2'),
        ('OPUS_WEB_SERVICE', 'opus-gunicorn', 'opus-gunicorn'),
        ('OPUS_CACHE_SERVICE', None, 'memcached'),
        ('OPUS_CACHE_SERVICE', '', ''),
    ],
)
def test_a_defaulted_key_may_be_left_out_or_named(
    tmp_path: Path, key: str, named: str | None, expected: str
) -> None:
    """The keys with defaults may be absent, and a value in the file wins over the default.

    Absence is the case that matters: these keys were added after servers had a
    ``deploy.env``, so an existing one has to go on working. Naming one is what a
    server that differs needs -- a later Python, a unit that is not called
    ``apache2``, or no shared cache at all. The defaults are supplied here rather
    than where they are used, so that every script sees the same value and an unset
    variable can never reach ``systemctl`` as an empty argument.
    """
    secrets = _make_environment(tmp_path, **{key: named})
    result = _read(secrets, f'bash -c \'[[ "${{{key}}}" == "{expected}" ]]\'')
    assert result.returncode == 0, result.stdout + result.stderr


def test_the_deploy_refuses_to_run_as_the_wrong_account(tmp_path: Path) -> None:
    """Everything a deploy creates belongs to whoever ran it, including a 0600 file.

    Run as anyone but the account the web server's workers run as, a deploy builds an
    installation the site cannot read, and the symptom appears after the switch. The
    refusal names both accounts and the way to run it again.
    """
    secrets = _make_environment(tmp_path, OPUS_USER='definitely-not-this-account')
    result = _read(secrets)

    assert result.returncode == 1
    assert 'definitely-not-this-account' in result.stdout
    assert getpass.getuser() in result.stdout


@pytest.mark.parametrize('bad', ['True', 'yes', '1', ''])
def test_a_non_boolean_debug_value_is_refused(tmp_path: Path, bad: str) -> None:
    """``debug`` is a TOML boolean, and the reader is where that is worth saying.

    The generator refuses one too, but by then a deploy has built a virtualenv and
    installed a release; here it costs one word in deploy.env.
    """
    result = _read(_make_environment(tmp_path, OPUS_DEBUG=bad))

    assert result.returncode == 1
    assert 'OPUS_DEBUG' in result.stdout


@pytest.mark.parametrize('key', REQUIRED_KEYS)
def test_a_missing_key_is_named(tmp_path: Path, key: str) -> None:
    """A key absent from deploy.env stops the deploy, and is reported as *not defined*.

    The wording is asserted, not merely the key name. A missing line and an empty
    value both stop the deploy, but they need different things from the operator --
    add the line, or fill it in -- and a test that accepts either message cannot tell
    the two checks apart. Mutation-checked: deleting the not-defined branch leaves the
    empty-value branch to catch this case, and without this assertion the suite stays
    green while the operator is told the wrong thing.
    """
    result = _read(_make_environment(tmp_path, **{key: None}))
    assert result.returncode != 0
    assert f'{key} not defined' in result.stdout


@pytest.mark.parametrize('key', REQUIRED_KEYS)
def test_an_empty_key_is_named(tmp_path: Path, key: str) -> None:
    """A key present but empty is refused too; being set to nothing is not being set."""
    result = _read(_make_environment(tmp_path, **{key: ''}))
    assert result.returncode != 0
    assert f'{key} is empty' in result.stdout


@pytest.mark.parametrize('key', REQUIRED_KEYS)
def test_an_unfilled_placeholder_is_refused(tmp_path: Path, key: str) -> None:
    """A copy of the template that was never filled in is refused, naming the key.

    Every template value is a quoted ``<PLACEHOLDER>``, so an unfilled copy sources
    without error and would otherwise reach the generator as a plausible-looking path.
    """
    result = _read(_make_environment(tmp_path, **{key: f'<{key}>'}))
    assert result.returncode != 0
    # The distinguishing wording, not just the key name: three of these keys name
    # directories, and the later existence checks echo the same key, so asserting only
    # that the name appears somewhere passes with this branch deleted.
    assert f'{key} is still the <PLACEHOLDER>' in result.stdout


def test_a_missing_file_is_reported_rather_than_ignored(tmp_path: Path) -> None:
    """No deploy.env at all is an error naming the template to copy.

    ``source`` on a missing file under ``set -e`` would stop the script anyway, but
    with a message about a file the operator has never heard of.
    """
    (tmp_path / 'secrets').mkdir()
    result = _read(tmp_path / 'secrets')
    assert result.returncode != 0
    assert 'deploy.env' in result.stdout


@pytest.mark.parametrize(
    ('key', 'subdir'), [('PDS3_HOLDINGS_DIR', 'volumes'), ('PDS4_HOLDINGS_DIR', 'bundles')]
)
def test_a_holdings_root_without_its_subdirectory_is_refused(
    tmp_path: Path, key: str, subdir: str
) -> None:
    """A holdings path that exists but is not a holdings tree is caught here.

    A typo that happens to name a real directory is the case a bare existence check
    misses, and the import would then fail bundle by bundle instead of at once.
    """
    secrets = _make_environment(tmp_path)
    wrong = tmp_path / 'not-holdings'
    wrong.mkdir()
    text = (secrets / 'deploy.env').read_text()
    line = next(ln for ln in text.splitlines() if ln.startswith(f'{key}='))
    (secrets / 'deploy.env').write_text(text.replace(line, f"{key}='{wrong}'"))

    result = _read(secrets)
    assert result.returncode != 0
    assert subdir in result.stdout


def test_the_template_declares_exactly_the_keys_the_reader_reads() -> None:
    """The shipped template and the reader agree on the contract.

    A key added to one and not the other is a deploy that fails on a server, and
    nothing else compares the two files. The optional key is part of the contract too:
    the template has to offer it, or a single-server installation would have no way to
    say so.
    """
    declared = {
        line.split('=', 1)[0]
        for line in TEMPLATE.read_text().splitlines()
        if line and not line.startswith('#') and '=' in line
    }
    assert declared == set(REQUIRED_KEYS) | set(OPTIONAL_KEYS)
