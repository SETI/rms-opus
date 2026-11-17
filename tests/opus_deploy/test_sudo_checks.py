"""Tests for the deploy scripts' checks of every ``sudo`` they run before the switch.

Each deploy script runs with its helpers stubbed and its commands faked (`run_deploy`),
with the fake ``sudo`` failing as sudo does when its password is mistyped. The service
actions of the promotion are tested beside it, in ``test_promote_steps.py`` and
``test_promote_generation.py``.
"""

from __future__ import annotations

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

#: What a deploy that stops at a refused sudo prints last.
_ABORTED = '*** ABORTING: nothing was built or switched ***'


@pytest.mark.skipif(BASH is None, reason='needs bash')
@pytest.mark.parametrize(('script', 'arguments'), _DEPLOYS, ids=_IDS)
def test_a_password_sudo_refuses_stops_the_deploy_before_it_builds(
    tmp_path: Path, script: str, arguments: tuple[str, ...]
) -> None:
    """The deploy says why and exits non-zero, having installed and promoted nothing."""
    status, output, ran = run_deploy(tmp_path, script, *arguments, failing_sudo='-v')
    assert status == 1
    assert 'sudo -v' in ran
    assert [call for call in ran if call.startswith(('pip', 'opus_', 'promote'))] == []
    assert 'sudo did not accept a password' in output
    assert _ABORTED in output


@pytest.mark.skipif(BASH is None, reason='needs bash')
@pytest.mark.parametrize(('script', 'arguments'), _DEPLOYS, ids=_IDS)
def test_a_password_sudo_accepts_goes_on_to_the_promotion(
    tmp_path: Path, script: str, arguments: tuple[str, ...]
) -> None:
    """The credentials are cached with ``sudo -v``, and the deploy goes on."""
    status, output, ran = run_deploy(tmp_path, script, *arguments)
    assert status == 0, output
    assert 'sudo -v' in ran
    assert ran[-1].startswith('promote ')


@pytest.mark.skipif(BASH is None, reason='needs bash')
def test_a_log_sudo_cannot_make_writable_stops_the_deploy(tmp_path: Path) -> None:
    """A refused ``sudo chmod`` of the application's log is said, before anything is built."""
    log = opus_dir(tmp_path) / 'opus_logs' / 'opus_log.txt'
    log.parent.mkdir(parents=True)
    log.write_text('', encoding='utf-8')
    status, output, ran = run_deploy(
        tmp_path,
        'import_and_deploy/deploy_new_code_and_database.sh',
        'opus_new',
        '==3.25.0',
        failing_sudo=f'chmod ug+w {log}',
    )
    assert status == 1
    assert [call for call in ran if call.startswith(('pip', 'opus_', 'promote'))] == []
    assert f'could not make {log} writable' in output
    assert _ABORTED in output
