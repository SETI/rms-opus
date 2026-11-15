"""Tests for the switch of an incremental update's generation into the served database.

``promote_generation.sh`` runs with its helpers stubbed and its commands faked
(`run_deploy`): ``sudo`` records each service action, ``opus_import`` the switch or the
revert, and ``opus_manage`` the warm-up, all in one record, so the order is pinned.
"""

from __future__ import annotations

import fcntl
from typing import TYPE_CHECKING

import pytest

from .conftest import BASH, CACHE_SERVICE, WEB_SERVICE, opus_dir, run_deploy

if TYPE_CHECKING:
    from pathlib import Path

#: The script, inside the chain.
_SCRIPT = 'import_and_deploy/promote_generation.sh'

#: The service actions, as the fake ``sudo`` records them.
_STOP = f'sudo systemctl stop {WEB_SERVICE}'
_RESTART_CACHE = f'sudo systemctl restart {CACHE_SERVICE}'
_START = f'sudo systemctl start {WEB_SERVICE}'
_WARM = 'opus_manage warm_search'

#: The two remedies a failed switch names.
_AGAIN = 'run promote_generation.sh again, which completes the'
_REVERT = 'run promote_generation.sh --revert.'


@pytest.mark.skipif(BASH is None, reason='needs bash')
@pytest.mark.parametrize(
    ('arguments', 'step'),
    [((), '--switch-generation'), (('--revert',), '--revert-generation')],
    ids=['switch', 'revert'],
)
def test_the_step_runs_while_the_web_service_is_stopped(
    tmp_path: Path, arguments: tuple[str, ...], step: str
) -> None:
    """Stop, the switch or the revert, the cache restart, the start, then the warm-up."""
    status, output, ran = run_deploy(tmp_path, _SCRIPT, *arguments)
    assert status == 0, output
    assert ran == [_STOP, f'opus_import {step}', _RESTART_CACHE, _START, _WARM]


@pytest.mark.skipif(BASH is None, reason='needs bash')
@pytest.mark.parametrize('arguments', [(), ('--revert',)], ids=['switch', 'revert'])
def test_a_step_opus_import_would_refuse_leaves_the_web_service_up(
    tmp_path: Path, arguments: tuple[str, ...]
) -> None:
    """Asked first, a refusal stops nothing and runs nothing, and says why."""
    status, output, ran = run_deploy(
        tmp_path, _SCRIPT, *arguments, generation_refusal='no pending generation is ready'
    )
    assert status == 1
    assert ran == []
    assert 'would be refused: no pending generation is ready' in output


@pytest.mark.skipif(BASH is None, reason='needs bash')
def test_a_failed_switch_leaves_the_web_service_stopped_and_names_both_ways_on(
    tmp_path: Path,
) -> None:
    """No start, a non-zero exit, and the two remedies: run it again, or revert."""
    status, output, ran = run_deploy(tmp_path, _SCRIPT, failing_import='--switch-generation')
    assert status == 1
    assert ran == [_STOP, 'opus_import --switch-generation']
    assert _AGAIN in output
    assert _REVERT in output


@pytest.mark.skipif(BASH is None, reason='needs bash')
def test_a_failed_revert_leaves_the_web_service_stopped(tmp_path: Path) -> None:
    """The service starts only when the revert succeeds."""
    status, output, ran = run_deploy(
        tmp_path, _SCRIPT, '--revert', failing_import='--revert-generation'
    )
    assert status == 1
    assert ran == [_STOP, 'opus_import --revert-generation']
    assert 'Run promote_generation.sh --revert again' in output


@pytest.mark.skipif(BASH is None, reason='needs bash')
@pytest.mark.parametrize('arguments', [('--force',), ('--revert', 'now')], ids=['unknown', 'extra'])
def test_other_arguments_print_the_usage_and_change_nothing(
    tmp_path: Path, arguments: tuple[str, ...]
) -> None:
    """The usage line and a non-zero exit, before the web service is touched."""
    status, output, ran = run_deploy(tmp_path, _SCRIPT, *arguments)
    assert status == 1
    assert 'Usage: promote_generation.sh [--revert]' in output
    assert ran == []


@pytest.mark.skipif(BASH is None, reason='needs bash')
def test_the_switch_stops_before_anything_while_another_holds_the_lock(
    tmp_path: Path,
) -> None:
    """It changes what is served, so it runs beside no deploy and no update."""
    lock_file = opus_dir(tmp_path) / 'deploy.lock'
    lock_file.parent.mkdir(parents=True)
    with lock_file.open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        status, output, ran = run_deploy(tmp_path, _SCRIPT)
    assert status == 1
    assert ran == []
    assert f'another deploy holds {lock_file}' in output


@pytest.mark.skipif(BASH is None, reason='needs bash')
def test_the_switch_refuses_when_nothing_is_deployed(tmp_path: Path) -> None:
    """A deployed configuration that names no schema stops it before the web service."""
    status, output, ran = run_deploy(tmp_path, _SCRIPT, deployed_schema=None)
    assert status == 1
    assert ran == []
    assert 'cannot read the served schema' in output
