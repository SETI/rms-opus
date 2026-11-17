"""Tests for the incremental update's scripts, and the full import that shares its end.

Each script runs with its helpers stubbed and its commands faked (`run_deploy`), and these
tests pin its own sequence: what the operator's command starts, what the update runs
against the served schema, and the copy to a second server both run scripts end with.
"""

from __future__ import annotations

import fcntl
import re
import subprocess  # nosec B404
from typing import TYPE_CHECKING

import pytest

from opus_deploy import scripts

from .conftest import BASH, opus_dir, run_deploy, write_recorder

if TYPE_CHECKING:
    from pathlib import Path

#: The operator's command, the script it detaches, and the internal script, in the chain.
_COMMAND = 'import_and_deploy/run_incremental_opus_update.sh'
_WRAPPER = 'import_and_deploy/_incremental_opus_update_wrapper.sh'
_FULL_WRAPPER = 'import_and_deploy/_full_opus_import_wrapper.sh'
_UPDATE = 'import_and_deploy/_run_incremental_opus_update.sh'
_FULL_IMPORT = 'import_and_deploy/_run_full_opus_import.sh'

#: The usage line the operator's command prints.
_USAGE = (
    'Usage: run_incremental_opus_update.sh [<version_spec>] '
    '[--drop <bundle>[,<bundle>...]] [<bundle> ...]'
)

#: A deploy.env that dumps and loads onto a peer.
_WITH_PEER = {'OPUS_DB_DUMP_DIR': 'dumps', 'OPUS_PEER_DB_HOST': 'peer.example'}

#: The name the run scripts give a new schema.
_NEW_SCHEMA = re.compile(r'opus3_\d{8}T\d{6}_\d+')


@pytest.mark.skipif(BASH is None, reason='needs bash')
@pytest.mark.parametrize('arguments', [(), ('==3.25.0',)], ids=['nothing', 'only-a-version'])
def test_the_command_without_a_bundle_prints_the_usage_and_runs_nothing(
    tmp_path: Path, arguments: tuple[str, ...]
) -> None:
    """The usage line, a non-zero exit, and no detached update.

    The fake ``nohup`` inherits the script's standard error, so the run returns only once
    a call the script made to it has been recorded.
    """
    status, output, ran = run_deploy(tmp_path, _COMMAND, *arguments)
    assert status == 1
    assert output.strip() == _USAGE
    assert ran == []


@pytest.mark.skipif(BASH is None, reason='needs bash')
def test_the_command_detaches_the_update_with_its_arguments(tmp_path: Path) -> None:
    """The wrapper runs under nohup with every argument, and the log's path is printed."""
    status, output, ran = run_deploy(
        tmp_path, _COMMAND, '==3.25.0', 'COISS_2001', '--drop', 'COISS_2002'
    )
    assert status == 0, output
    assert ran == [f'nohup {tmp_path}/chain/{_WRAPPER} ==3.25.0 COISS_2001 --drop COISS_2002']
    assert re.search(rf'^Log file: {tmp_path}/opus_update\.\w+\.log$', output, re.M) is not None


@pytest.mark.skipif(BASH is None, reason='needs bash')
@pytest.mark.parametrize(
    ('status', 'result'), [(0, 'succeeded'), (1, 'FAILED')], ids=['succeeded', 'failed']
)
def test_the_wrapper_mails_the_log_with_the_result(
    tmp_path: Path, status: int, result: str
) -> None:
    """The internal script's output goes to the log, which is mailed under its result."""
    chain = tmp_path / 'chain'
    scripts.write_scripts(chain)
    calls = tmp_path / 'calls'
    write_recorder(chain / _UPDATE, calls, f'echo "update output"; exit {status}')
    fake_bin = tmp_path / 'bin'
    fake_bin.mkdir()
    write_recorder(fake_bin / 'mail', calls)
    log = tmp_path / 'update.log'
    environment = {
        'PATH': f'{fake_bin}:/usr/bin:/bin',
        'IMPORT_SCRIPT_DIR': str(chain / 'import_and_deploy'),
        'NOHUP_LOGFILE': str(log),
        'OPUS_IMPORT_MAIL_TO': 'ops@example.org',
    }
    assert BASH is not None
    subprocess.run(  # nosec B603 - bash and the packaged script
        [BASH, str(chain / _WRAPPER), 'COISS_2001'], env=environment, check=False
    )
    assert calls.read_text(encoding='utf-8').splitlines() == [
        '_run_incremental_opus_update.sh COISS_2001',
        f'mail -s OPUS incremental update {result} ops@example.org',
    ]
    assert log.read_text(encoding='utf-8') == 'update output\n'


@pytest.mark.skipif(BASH is None, reason='needs bash')
@pytest.mark.parametrize('wrapper', [_WRAPPER, _FULL_WRAPPER], ids=['update', 'full-import'])
def test_a_wrapper_runs_from_paths_with_spaces(tmp_path: Path, wrapper: str) -> None:
    """``TMPDIR`` decides where the log goes, and a space in it, or in the chain's
    directory, neither splits the command nor makes the redirection ambiguous."""
    chain = tmp_path / 'the chain'
    scripts.write_scripts(chain)
    calls = tmp_path / 'calls'
    script = _UPDATE if wrapper == _WRAPPER else _FULL_IMPORT
    write_recorder(chain / script, calls, 'echo "run output"')
    log = tmp_path / 'a temporary directory' / 'opus update.log'
    log.parent.mkdir()
    environment = {
        'PATH': '/usr/bin:/bin',
        'IMPORT_SCRIPT_DIR': str(chain / 'import_and_deploy'),
        'NOHUP_LOGFILE': str(log),
    }
    assert BASH is not None
    finished = subprocess.run(  # nosec B603 - bash and the packaged script
        [BASH, str(chain / wrapper), 'COISS_2001'],
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert finished.returncode == 0, finished.stderr
    assert calls.read_text(encoding='utf-8').splitlines() == [
        f'{script.rsplit("/", 1)[1]} COISS_2001'
    ]
    assert log.read_text(encoding='utf-8') == 'run output\n'


@pytest.mark.skipif(BASH is None, reason='needs bash')
def test_the_update_writes_the_served_schema_then_copies_it_to_the_peer(
    tmp_path: Path,
) -> None:
    """Every invocation in order, then the dump of the served schema under a new schema
    name, which leaves a dump the operator took of it alone, and its load onto the peer
    under that name."""
    status, output, ran = run_deploy(
        tmp_path, _UPDATE, 'COISS_2001', '--drop', 'COISS_2002', deploy_env=_WITH_PEER
    )
    assert status == 0, output
    assert ran[:-2] == [
        'opus_import --begin-generation',
        'opus_import --delete-bundles COISS_2002',
        'opus_import --import COISS_2001',
        'opus_import --finalize',
        'opus_import --validate',
        'opus_import --write-schema-version',
    ]
    match = re.fullmatch(rf'dump_db\.sh served ({_NEW_SCHEMA.pattern})', ran[-2])
    assert match is not None
    assert ran[-1] == f'load_db.sh {match[1]}'


@pytest.mark.skipif(BASH is None, reason='needs bash')
@pytest.mark.parametrize(
    ('arguments', 'version_spec'),
    [(('COISS_2001',), '==3.25.0'), (('~=3.26', 'COISS_2001'), '~=3.26')],
    ids=['deployed', 'given'],
)
def test_the_update_installs_the_deployed_release_unless_given_another(
    tmp_path: Path, arguments: tuple[str, ...], version_spec: str
) -> None:
    """The generation is switched in under the deployed release, so it is the default."""
    status, output, _ran = run_deploy(tmp_path, _UPDATE, *arguments)
    assert status == 0, output
    assert re.search(rf'^Version spec: {re.escape(version_spec)}$', output, re.M) is not None


@pytest.mark.skipif(BASH is None, reason='needs bash')
@pytest.mark.parametrize(
    'release', ['', '3.25.1.dev4', '3.25.1.dev4+g1234abc'], ids=['unreadable', 'dev', 'local']
)
def test_the_update_without_a_version_refuses_a_release_pypi_cannot_install(
    tmp_path: Path, release: str
) -> None:
    """Nothing is run, and the operator is asked for a version spec."""
    status, output, ran = run_deploy(tmp_path, _UPDATE, 'COISS_2001', deployed_release=release)
    assert status == 1
    assert ran == []
    assert 'version spec of what is being served' in output
    assert 'nothing was changed' in output


@pytest.mark.skipif(BASH is None, reason='needs bash')
def test_the_update_installs_the_commit_a_git_installation_was_built_from(
    tmp_path: Path,
) -> None:
    """A development build pip recorded a git commit for is installed again from it."""
    status, output, _ran = run_deploy(
        tmp_path, _UPDATE, 'COISS_2001', deployed_release='3.25.1.dev4+g208b19c\n208b19c0'
    )
    assert status == 0, output
    assert re.search(r'^Version spec: @208b19c0$', output, re.M) is not None


@pytest.mark.skipif(BASH is None, reason='needs bash')
def test_a_failed_update_copies_nothing(tmp_path: Path) -> None:
    """The update stops at the invocation that failed, and the peer gets nothing."""
    status, _output, ran = run_deploy(
        tmp_path, _UPDATE, 'COISS_2001', failing_import='--finalize', deploy_env=_WITH_PEER
    )
    assert status != 0
    assert ran[-1] == 'opus_import --finalize'


@pytest.mark.skipif(BASH is None, reason='needs bash')
def test_a_refused_begin_advises_no_abandon(tmp_path: Path) -> None:
    """No generation was begun, so there is nothing to throw away."""
    status, output, ran = run_deploy(
        tmp_path, _UPDATE, 'COISS_2001', failing_import='--begin-generation'
    )
    assert status != 0
    assert ran == ['opus_import --begin-generation']
    assert 'No generation was begun' in output
    assert '--abandon-generation' not in output


@pytest.mark.skipif(BASH is None, reason='needs bash')
def test_the_update_stops_before_anything_while_another_holds_the_lock(
    tmp_path: Path,
) -> None:
    """It writes the served schema, so it waits for no deploy and runs beside none."""
    lock_file = opus_dir(tmp_path) / 'deploy.lock'
    lock_file.parent.mkdir(parents=True)
    with lock_file.open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        status, output, ran = run_deploy(tmp_path, _UPDATE, 'COISS_2001')
    assert status == 1
    assert ran == []
    assert f'another deploy holds {lock_file}' in output


@pytest.mark.skipif(BASH is None, reason='needs bash')
def test_the_full_import_copies_its_new_schema_under_its_own_name(tmp_path: Path) -> None:
    """The dump of the new schema, then its load onto the peer under the same name."""
    status, output, ran = run_deploy(tmp_path, _FULL_IMPORT, '==3.25.0', deploy_env=_WITH_PEER)
    assert status == 0, output
    match = re.fullmatch(rf'dump_db\.sh ({_NEW_SCHEMA.pattern}) \1', ran[-2])
    assert match is not None
    assert ran[-1] == f'load_db.sh {match[1]}'
