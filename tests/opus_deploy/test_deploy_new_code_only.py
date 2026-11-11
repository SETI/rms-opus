"""Tests for what the code-only deploy writes to the database, with and without a flag.

The script stops a web server and installs distributions, so it never runs for real
here. It is run instead from a copy of the chain whose helper files -- the ones that read
``deploy.env``, build the installation, check the schema version and promote it -- are
replaced by stubs, with every command it runs (``sudo``, ``pip``, ``opus_manage``,
``opus_import``) a fake on ``PATH`` that records its arguments. What is left is the
script's own sequence, which is the part these tests pin.
"""

from __future__ import annotations

import shutil
import subprocess  # nosec B404
from typing import TYPE_CHECKING

import pytest

from opus_deploy import scripts

if TYPE_CHECKING:
    from pathlib import Path

#: The script, inside the chain.
_SCRIPT = 'import_and_deploy/deploy_new_code_only.sh'

#: The helpers the script sources, each replaced by a stub. The deploy.env reader names
#: the OPUS directory, the promotion records whether it would warm the landing page, and
#: the others do nothing.
_STUBBED_HELPERS = (
    '_activate_deploy_venv.sh',
    '_chain_version.sh',
    '_opus_setup_environment.sh',
)

#: The commands the script runs, each a fake that records how it was called.
_FAKE_COMMANDS = ('sudo', 'pip', 'opus_manage', 'opus_import')

_BASH = shutil.which('bash')

#: What the fake ``opus_manage migrate --plan --check`` does for each case, as Django does.
_MIGRATION_CHECKS = {
    'clean': 'echo "Planned operations:"; echo "  No planned migration operations."; exit 0',
    'pending': 'echo "Planned operations:"; echo "sessions.0002_x"; exit 1',
    'broken': 'echo "django.core.exceptions.ImproperlyConfigured: no settings" >&2; exit 1',
}


def _run_deploy(
    tmp_path: Path, *arguments: str, migration_check: str = 'clean'
) -> tuple[int, str, list[str]]:
    """Run the code-only deploy with its helpers stubbed and its commands faked.

    Parameters:
        tmp_path: A scratch directory.
        arguments: The script's arguments.
        migration_check: What ``opus_manage migrate --plan --check`` finds: ``'clean'``,
            ``'pending'`` for a migration to apply, or ``'broken'`` for a Django that
            cannot start.

    Returns:
        The script's status, everything it printed, and each faked command it ran, as
        its name and arguments.
    """
    chain = tmp_path / 'chain'
    scripts.write_scripts(chain)
    helpers = chain / 'import_and_deploy'
    opus_dir = tmp_path / 'opus'
    (opus_dir / 'deployed').mkdir(parents=True)
    (opus_dir / 'deployed' / 'opus.toml').write_text('schema = "served"\n', encoding='utf-8')
    (helpers / '_read_deploy_env.sh').write_text(f'OPUS_DIR={opus_dir}\n', encoding='utf-8')
    for helper in _STUBBED_HELPERS:
        (helpers / helper).write_text(':\n', encoding='utf-8')
    calls = tmp_path / 'calls'
    (helpers / '_promote.sh').write_text(
        f'echo "promote warm=${{OPUS_WARM_SEARCH:-true}}" >> {calls}\n', encoding='utf-8'
    )
    (helpers / '_check_schema_version.sh').write_text(
        'check_schema_version() { return 0; }\n', encoding='utf-8'
    )

    fake_bin = tmp_path / 'bin'
    fake_bin.mkdir()
    for command in _FAKE_COMMANDS:
        status = (
            f'[[ "$*" == "migrate --plan --check" ]] && {{ {_MIGRATION_CHECKS[migration_check]}; }}'
            if command == 'opus_manage'
            else ':'
        )
        fake = fake_bin / command
        fake.write_text(
            f'#!/bin/bash\necho "{command} $*" >> {calls}\n{status}\nexit 0\n', encoding='utf-8'
        )
        fake.chmod(0o755)

    assert _BASH is not None
    finished = subprocess.run(  # nosec B603 - bash and the packaged script
        [_BASH, str(chain / _SCRIPT), *arguments],
        env={'PATH': f'{fake_bin}:/usr/bin:/bin', 'HOSTNAME': 'test'},
        capture_output=True,
        text=True,
        check=False,
    )
    ran = calls.read_text(encoding='utf-8').splitlines() if calls.exists() else []
    return finished.returncode, finished.stdout + finished.stderr, ran


@pytest.mark.skipif(_BASH is None, reason='needs bash')
def test_the_plain_deploy_migrates_and_rebuilds_the_aux_tables(tmp_path: Path) -> None:
    """Without the flag, Django migrates, the four tables are rebuilt, and the mult rows
    take the release's presentation."""
    status, output, ran = _run_deploy(tmp_path, '==3.25.0')
    assert status == 0, output
    assert 'opus_manage migrate' in ran
    assert ran[-1] == 'promote warm=true'
    assert (
        'opus_import --create-param-info --create-partables --create-table-names '
        '--import-dictionary --update-mult-info'
    ) in ran


@pytest.mark.skipif(_BASH is None, reason='needs bash')
def test_no_database_writes_nothing_to_the_database(tmp_path: Path) -> None:
    """With the flag, the only database commands are ones that read."""
    status, output, ran = _run_deploy(tmp_path, '--no-database', '==3.25.0')
    assert status == 0, output
    assert [call for call in ran if call.startswith('opus_import')] == []
    assert [call for call in ran if call.startswith('opus_manage')] == [
        'opus_manage migrate --plan --check',
        'opus_manage collectstatic --noinput',
    ]
    assert 'nothing will be written to served' in output
    # The warm-up registers a search and a session, as a visitor's first requests do.
    assert ran[-1] == 'promote warm=false'


@pytest.mark.skipif(_BASH is None, reason='needs bash')
def test_no_database_refuses_a_pending_migration(tmp_path: Path) -> None:
    """A release that needs a migration cannot skip it, and is pointed at the plain deploy."""
    status, output, ran = _run_deploy(tmp_path, '--no-database', migration_check='pending')
    assert status == 1
    assert 'sessions.0002_x' in output
    assert 'Deploy this release without --no-database' in output
    assert 'opus_manage collectstatic --noinput' not in ran


@pytest.mark.skipif(_BASH is None, reason='needs bash')
def test_no_database_reports_a_django_that_cannot_start(tmp_path: Path) -> None:
    """A failed check that read no migrations is not reported as a pending one."""
    status, output, ran = _run_deploy(tmp_path, '--no-database', migration_check='broken')
    assert status == 1
    assert 'ImproperlyConfigured' in output
    assert "Cannot check Django's migrations" in output
    assert 'without --no-database' not in output
    assert 'opus_manage collectstatic --noinput' not in ran


@pytest.mark.skipif(_BASH is None, reason='needs bash')
@pytest.mark.parametrize(
    'arguments',
    [('--no-database', '==1', '==2'), ('--bogus',), ('==1', '--no-database')],
    ids=['two-specs', 'unknown-flag', 'flag-after-spec'],
)
def test_anything_else_prints_the_usage(tmp_path: Path, arguments: tuple[str, ...]) -> None:
    """The flag comes first, and at most one version spec follows it."""
    status, output, ran = _run_deploy(tmp_path, *arguments)
    assert status == 1
    assert 'Usage: deploy_new_code_only.sh [--no-database] [<version_spec>]' in output
    assert ran == []
