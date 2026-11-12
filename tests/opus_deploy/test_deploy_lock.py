"""Tests for the lock that lets one deploy run at a time on a server.

Each deploy script runs with its helpers stubbed and its commands faked (`run_deploy`);
the lock is the chain's own ``_deploy_lock.sh``, taken with ``flock``.
"""

from __future__ import annotations

import fcntl
from typing import TYPE_CHECKING

import pytest

from .conftest import BASH, opus_dir, run_deploy

if TYPE_CHECKING:
    from pathlib import Path

#: Each deploy script, with arguments it accepts.
_DEPLOYS = [
    ('import_and_deploy/deploy_new_code_and_database.sh', ('opus_new', '==3.25.0')),
    ('import_and_deploy/deploy_new_code_only.sh', ('==3.25.0',)),
]
_IDS = ['code-and-database', 'code-only']


@pytest.mark.skipif(BASH is None, reason='needs bash')
@pytest.mark.parametrize(('script', 'arguments'), _DEPLOYS, ids=_IDS)
def test_a_deploy_holds_the_lock_through_its_promotion_and_releases_it(
    tmp_path: Path, script: str, arguments: tuple[str, ...]
) -> None:
    """Another process finds it held while the deploy promotes, and free once it exits."""
    status, output, ran = run_deploy(tmp_path, script, *arguments)
    assert status == 0, output
    assert ran[-1].endswith(' lock=held')
    with (opus_dir(tmp_path) / 'deploy.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)


@pytest.mark.skipif(BASH is None, reason='needs bash')
@pytest.mark.parametrize(('script', 'arguments'), _DEPLOYS, ids=_IDS)
def test_a_deploy_stops_before_anything_while_another_holds_the_lock(
    tmp_path: Path, script: str, arguments: tuple[str, ...]
) -> None:
    """It reads no served schema, builds nothing and promotes nothing, and says why."""
    lock_file = opus_dir(tmp_path) / 'deploy.lock'
    lock_file.parent.mkdir(parents=True)
    with lock_file.open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        status, output, ran = run_deploy(tmp_path, script, *arguments)
    assert status == 1
    assert ran == []
    assert f'another deploy holds {lock_file}' in output
    assert 'Sessions and carts carried over from' not in output
