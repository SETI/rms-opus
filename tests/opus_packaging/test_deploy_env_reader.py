"""Tests for the deploy chain's reader of ``scripts/server/secrets/deploy.env``.

``_read_deploy_env.sh`` is what every server script sources before it does anything
else, and it is the deploy's only chance to reject a bad environment *before* it stops
Apache. Its failure modes are all quiet ones: a key missing from ``deploy.env``, a key
left as the ``<PLACEHOLDER>`` the template ships, or a key present but empty. The last
of those is not hypothetical -- an unset ``OPUS_SECRET_KEY`` used to reach ``opus.toml``
as an empty string, because the file this one replaces validated seven variables and
not that one.

Like the generator tests beside them, these run the shipped script under ``bash``
rather than re-implementing what it does.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

SERVER_SCRIPTS = (
    Path(__file__).resolve().parents[2] / 'scripts' / 'server'
)
READER = SERVER_SCRIPTS / 'import_and_deploy' / '_read_deploy_env.sh'
TEMPLATE = SERVER_SCRIPTS / 'deploy.env.template'

# The keys the reader requires. Stated here so a key added to the reader without a
# line in the template -- or the reverse -- fails a test rather than a deploy.
REQUIRED_KEYS = [
    'OPUS_DIR',
    'OPUS_DB_USER',
    'OPUS_DB_PASSWORD',
    'OPUS_SECRET_KEY',
    'PDS3_HOLDINGS_DIR',
    'PDS4_HOLDINGS_DIR',
    'LAST_BLOG_UPDATE_FILE',
    'NOTIFICATION_FILE',
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
        'OPUS_DB_USER': 'opus_user',
        'OPUS_DB_PASSWORD': 'a password',
        'OPUS_SECRET_KEY': 'a-secret-key',
        'PDS3_HOLDINGS_DIR': str(pds3),
        'PDS4_HOLDINGS_DIR': str(pds4),
        'LAST_BLOG_UPDATE_FILE': str(opus_dir / 'last_update.txt'),
        'NOTIFICATION_FILE': str(opus_dir / 'notification.html'),
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
    assert key in result.stdout + result.stderr


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


def test_the_template_declares_exactly_the_keys_the_reader_requires() -> None:
    """The shipped template and the reader agree on the contract.

    A key added to one and not the other is a deploy that fails on a server, and
    nothing else compares the two files.
    """
    declared = {
        line.split('=', 1)[0]
        for line in TEMPLATE.read_text().splitlines()
        if line and not line.startswith('#') and '=' in line
    }
    assert declared == set(REQUIRED_KEYS)
