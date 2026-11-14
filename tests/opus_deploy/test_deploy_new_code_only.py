"""Tests for what the code-only deploy writes to the database, with and without a flag.

The script runs with its helpers stubbed and its commands faked (`run_deploy`), and these
tests pin its own sequence.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from .conftest import BASH, run_deploy

if TYPE_CHECKING:
    from pathlib import Path

#: The script, inside the chain.
_SCRIPT = 'import_and_deploy/deploy_new_code_only.sh'


def _run_deploy(
    tmp_path: Path, *arguments: str, migration_check: str = 'clean'
) -> tuple[int, str, list[str]]:
    """Run the code-only deploy through `run_deploy`.

    Parameters:
        tmp_path: A scratch directory.
        arguments: The script's arguments.
        migration_check: What ``opus_manage migrate --plan --check`` finds, as
            `run_deploy` takes it.

    Returns:
        The script's status, everything it printed, and each faked command it ran.
    """
    return run_deploy(tmp_path, _SCRIPT, *arguments, migration_check=migration_check)


@pytest.mark.skipif(BASH is None, reason='needs bash')
def test_the_plain_deploy_migrates_and_rebuilds_the_aux_tables(tmp_path: Path) -> None:
    """Without the flag, Django migrates, the four tables are rebuilt, and the mult rows
    take the release's presentation."""
    status, output, ran = _run_deploy(tmp_path, '==3.25.0')
    assert status == 0, output
    assert 'opus_manage migrate' in ran
    assert ran[-1] == 'promote warm=true lock=held'
    assert (
        'opus_import --create-param-info --create-partables --create-table-names '
        '--import-dictionary --update-mult-info'
    ) in ran


@pytest.mark.skipif(BASH is None, reason='needs bash')
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
    assert ran[-1] == 'promote warm=false lock=held'


@pytest.mark.skipif(BASH is None, reason='needs bash')
def test_no_database_refuses_a_pending_migration(tmp_path: Path) -> None:
    """A release that needs a migration cannot skip it, and is pointed at the plain deploy."""
    status, output, ran = _run_deploy(tmp_path, '--no-database', migration_check='pending')
    assert status == 1
    assert 'sessions.0002_x' in output
    assert 'Deploy this release without --no-database' in output
    assert 'opus_manage collectstatic --noinput' not in ran


@pytest.mark.skipif(BASH is None, reason='needs bash')
def test_no_database_reports_a_django_that_cannot_start(tmp_path: Path) -> None:
    """A failed check that read no migrations is not reported as a pending one."""
    status, output, ran = _run_deploy(tmp_path, '--no-database', migration_check='broken')
    assert status == 1
    assert 'ImproperlyConfigured' in output
    assert "Cannot check Django's migrations" in output
    assert 'without --no-database' not in output
    assert 'opus_manage collectstatic --noinput' not in ran


@pytest.mark.skipif(BASH is None, reason='needs bash')
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
