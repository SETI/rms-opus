"""Tests for the copy of a finished database to a second server, run as shell functions.

``_copy_database_to_peer.sh`` is the end of both run scripts. It defines its functions
and executes nothing, so it is sourced here with ``DATABASE_SCRIPT_DIR`` naming a
directory of stand-ins for ``dump_db.sh`` and ``load_db.sh`` that record their arguments.
"""

from __future__ import annotations

import shlex
import subprocess  # nosec B404
from typing import TYPE_CHECKING

import pytest

from opus_deploy import scripts

from .conftest import BASH, defines_only_functions, write_recorder

if TYPE_CHECKING:
    from pathlib import Path

#: The file, inside the packaged chain.
_COPY = 'import_and_deploy/_copy_database_to_peer.sh'


def _run_copy(tmp_path: Path, call: str, environment: dict[str, str]) -> tuple[int, str, list[str]]:
    """Source the file with recording database scripts under ``set -e`` and run one line.

    Parameters:
        tmp_path: A scratch directory.
        call: The line to run after sourcing.
        environment: ``OPUS_DB_DUMP_DIR`` and ``OPUS_PEER_DB_HOST``, as deploy.env sets
            them.

    Returns:
        The line's status, everything it printed, and each database script it ran.
    """
    chain = tmp_path / 'chain'
    scripts.write_scripts(chain)
    database = tmp_path / 'database'
    database.mkdir()
    calls = tmp_path / 'calls'
    for name in ('dump_db.sh', 'load_db.sh'):
        write_recorder(database / name, calls)
    assert BASH is not None
    finished = subprocess.run(  # nosec B603 - bash and the packaged file
        [BASH, '-c', f'set -e; source {shlex.quote(str(chain / _COPY))}; {call}'],
        env={'PATH': '/usr/bin:/bin', 'DATABASE_SCRIPT_DIR': str(database), **environment},
        capture_output=True,
        text=True,
        check=False,
    )
    ran = calls.read_text(encoding='utf-8').splitlines() if calls.exists() else []
    return finished.returncode, finished.stdout + finished.stderr, ran


@pytest.mark.skipif(BASH is None, reason='needs bash')
@pytest.mark.parametrize(
    ('dump_dir', 'peer', 'expected'),
    [
        ('', '', []),
        ('dumps', '', ['dump_db.sh opus_source opus_target']),
        ('dumps', 'peer.example', ['dump_db.sh opus_source opus_target', 'load_db.sh opus_target']),
    ],
    ids=['no-dump-directory', 'dump-only', 'dump-and-load'],
)
def test_the_copy_does_what_deploy_env_asks(
    tmp_path: Path, dump_dir: str, peer: str, expected: list[str]
) -> None:
    """Nothing without a dump directory; the dump with one, under the target schema's
    name, so an update's dump of the served schema never replaces one taken of it under
    its own; the dump then the load onto the peer, as the target schema, with a peer as
    well."""
    status, output, ran = _run_copy(
        tmp_path,
        'copy_database_to_peer opus_source opus_target; echo CONTINUED',
        {'OPUS_DB_DUMP_DIR': dump_dir, 'OPUS_PEER_DB_HOST': peer},
    )
    assert status == 0, output
    assert ran == expected
    assert 'CONTINUED' in output


@pytest.mark.skipif(BASH is None, reason='needs bash')
def test_a_failed_dump_fails_the_copy_and_loads_nothing(tmp_path: Path) -> None:
    """The caller stops, and the peer never reads a dump that was not written."""
    status, output, _ran = _run_copy(
        tmp_path,
        'chmod -x "$DATABASE_SCRIPT_DIR/dump_db.sh"; '
        'if copy_database_to_peer opus_source opus_target; then exit 0; else exit 1; fi',
        {'OPUS_DB_DUMP_DIR': 'dumps', 'OPUS_PEER_DB_HOST': 'peer.example'},
    )
    assert status == 1
    assert 'LOAD DATABASE ON THE SECOND SERVER' not in output


@pytest.mark.skipif(BASH is None, reason='needs bash')
def test_a_new_schema_is_named_for_the_moment_and_process(tmp_path: Path) -> None:
    """``opus3_`` and the argument the run scripts make from the time and their pid."""
    status, output, _ran = _run_copy(tmp_path, 'new_schema_name 20261114T221500_42', {})
    assert status == 0, output
    assert output.strip() == 'opus3_20261114T221500_42'


def test_sourcing_the_copy_runs_nothing(tmp_path: Path) -> None:
    """Every top-level line belongs to a function definition, so the tests can source it."""
    scripts.write_scripts(tmp_path)
    assert defines_only_functions(tmp_path / _COPY)
