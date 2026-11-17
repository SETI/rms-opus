"""Tests for the dump and the load that copy a database to a second server.

``database/dump_db.sh`` and ``database/load_db.sh`` run from a copy of the chain whose
``deploy.env`` reader is a stand-in setting the database variables, with a fake
``mysqldump`` and a fake ``mysql`` first on ``PATH`` that record their arguments and what
they were given to read.
"""

from __future__ import annotations

import shlex
import subprocess  # nosec B404
from typing import TYPE_CHECKING

import pytest

from opus_deploy import scripts

from .conftest import BASH, write_recorder

if TYPE_CHECKING:
    from pathlib import Path

#: What the fake mysqldump writes, and so what the dump file holds.
_DUMP_TEXT = 'CREATE TABLE obs_general_rows (id INT);'

#: The connection arguments both scripts give, from the stand-in deploy.env.
_CREDENTIALS = '-uopus -psecret'


def _run_database_script(tmp_path: Path, script: str, *arguments: str) -> tuple[int, str, str]:
    """Run one of the database scripts with a stand-in deploy.env and faked clients.

    Parameters:
        tmp_path: A scratch directory. Its ``dumps`` directory is OPUS_DB_DUMP_DIR.
        script: ``dump_db.sh`` or ``load_db.sh``.
        arguments: The script's arguments.

    Returns:
        The script's status, everything it printed, and the record of each client call:
        a line of the client's name and arguments, followed by a line holding what it
        read on its standard input (``mysql`` only).
    """
    chain = tmp_path / 'chain'
    scripts.write_scripts(chain)
    settings = {
        'OPUS_DB_DUMP_DIR': str(tmp_path / 'dumps'),
        'OPUS_DB_HOST': 'db.local',
        'OPUS_PEER_DB_HOST': 'peer.local',
        'OPUS_DB_USER': 'opus',
        'OPUS_DB_PASSWORD': 'secret',
    }
    (chain / 'import_and_deploy' / '_read_deploy_env.sh').write_text(
        ''.join(f'{name}={shlex.quote(value)}\n' for name, value in settings.items()),
        encoding='utf-8',
    )
    fake_bin = tmp_path / 'bin'
    fake_bin.mkdir()
    calls = tmp_path / 'calls'
    write_recorder(fake_bin / 'mysqldump', calls, f'echo {shlex.quote(_DUMP_TEXT)}')
    write_recorder(fake_bin / 'mysql', calls, f'echo "$(cat)" >> {shlex.quote(str(calls))}')
    assert BASH is not None
    finished = subprocess.run(  # nosec B603 - bash and the packaged script
        [BASH, str(chain / 'database' / script), *arguments],
        env={'PATH': f'{fake_bin}:/usr/bin:/bin'},
        capture_output=True,
        text=True,
        check=False,
    )
    ran = calls.read_text(encoding='utf-8') if calls.exists() else ''
    return finished.returncode, finished.stdout + finished.stderr, ran


@pytest.mark.skipif(BASH is None, reason='needs bash')
def test_the_dump_is_one_consistent_snapshot_without_table_locks(tmp_path: Path) -> None:
    """``--single-transaction``, so a served database can be dumped while it takes
    writes, and ``--column-statistics``, so its histograms reach the copy, into
    ``<database>.sql`` in the dump directory."""
    status, output, ran = _run_database_script(tmp_path, 'dump_db.sh', 'opus3_served')
    assert status == 0, output
    assert ran == (
        f'mysqldump --single-transaction --column-statistics {_CREDENTIALS} '
        '-h db.local opus3_served\n'
    )
    dumped = (tmp_path / 'dumps' / 'opus3_served.sql').read_text(encoding='utf-8')
    assert dumped == f'{_DUMP_TEXT}\n'


@pytest.mark.skipif(BASH is None, reason='needs bash')
@pytest.mark.parametrize(
    ('arguments', 'target'),
    [(('opus3_served', 'opus3_copy'), 'opus3_copy'), (('opus3_served',), 'opus3_served')],
    ids=['named-target', 'dump-name'],
)
def test_the_load_creates_the_target_schema_from_the_dump(
    tmp_path: Path, arguments: tuple[str, ...], target: str
) -> None:
    """The dump of the first name is read; the second name, or the first when there is
    none, is created on the peer and loaded."""
    dumps = tmp_path / 'dumps'
    dumps.mkdir()
    (dumps / 'opus3_served.sql').write_text(f'{_DUMP_TEXT}\n', encoding='utf-8')
    status, output, ran = _run_database_script(tmp_path, 'load_db.sh', *arguments)
    assert status == 0, output
    assert ran.splitlines() == [
        f'mysql {_CREDENTIALS} -h peer.local',
        f'CREATE DATABASE {target};',
        f'mysql {_CREDENTIALS} -h peer.local {target}',
        _DUMP_TEXT,
    ]


@pytest.mark.skipif(BASH is None, reason='needs bash')
def test_the_load_drops_a_views_definer(tmp_path: Path) -> None:
    """The peer may lack the first server's account, and the view needs none."""
    dumps = tmp_path / 'dumps'
    dumps.mkdir()
    view = (
        '/*!50013 DEFINER=`opus`@`db.local` SQL SECURITY INVOKER */ '
        '/*!50001 VIEW `obs_general` AS select 1 AS `id` */;'
    )
    (dumps / 'opus3_served.sql').write_text(f'{view}\n', encoding='utf-8')
    status, output, ran = _run_database_script(tmp_path, 'load_db.sh', 'opus3_served', 'opus3_y')
    assert status == 0, output
    assert ran.splitlines()[-1] == (
        '/*!50013 SQL SECURITY INVOKER */ /*!50001 VIEW `obs_general` AS select 1 AS `id` */;'
    )


@pytest.mark.skipif(BASH is None, reason='needs bash')
def test_a_dump_given_a_name_is_written_under_it(tmp_path: Path) -> None:
    """The served database's own dump is left as it was."""
    dumps = tmp_path / 'dumps'
    dumps.mkdir()
    (dumps / 'opus3_served.sql').write_text('the recovery copy\n', encoding='utf-8')
    status, output, ran = _run_database_script(tmp_path, 'dump_db.sh', 'opus3_served', 'opus3_y')
    assert status == 0, output
    assert ran == (
        f'mysqldump --single-transaction --column-statistics {_CREDENTIALS} '
        '-h db.local opus3_served\n'
    )
    assert (dumps / 'opus3_y.sql').read_text(encoding='utf-8') == f'{_DUMP_TEXT}\n'
    assert (dumps / 'opus3_served.sql').read_text(encoding='utf-8') == 'the recovery copy\n'


@pytest.mark.skipif(BASH is None, reason='needs bash')
def test_the_load_keeps_a_rows_text_that_names_a_definer(tmp_path: Path) -> None:
    """Only the view's clause, on the line mysqldump writes it on, is dropped."""
    dumps = tmp_path / 'dumps'
    dumps.mkdir()
    row = "INSERT INTO `contexts` VALUES ('prefix DEFINER=`alice`@`localhost` suffix');"
    (dumps / 'opus3_served.sql').write_text(f'{row}\n', encoding='utf-8')
    status, output, ran = _run_database_script(tmp_path, 'load_db.sh', 'opus3_served', 'opus3_y')
    assert status == 0, output
    assert ran.splitlines()[-1] == row


@pytest.mark.skipif(BASH is None, reason='needs bash')
def test_the_load_refuses_a_dump_that_is_not_there(tmp_path: Path) -> None:
    """It names the dump it looked for and creates nothing on the peer."""
    status, output, ran = _run_database_script(tmp_path, 'load_db.sh', 'opus3_x', 'opus3_y')
    assert status == 1
    assert 'opus3_x.sql does not exist. Run dump_db.sh opus3_x first.' in output
    assert ran == ''
