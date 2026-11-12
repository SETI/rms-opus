"""Tests for the promotion's steps, run as shell functions.

``_promote.sh`` stops and starts the web service with ``sudo`` and is never run by a
test. The steps of it that can fail on their own are functions in
``_promote_steps.sh``, which defines them and executes nothing, so it is sourced here,
under ``set -e`` as the deploy scripts run, with a fake ``opus_import`` and a fake
``opus_manage`` first on ``PATH`` and a service command that records what it was asked
to do. Each step is called the way its caller calls it.
"""

from __future__ import annotations

import shutil
import subprocess  # nosec B404
from typing import TYPE_CHECKING

import pytest

from opus_deploy import scripts

if TYPE_CHECKING:
    from pathlib import Path

#: The steps, inside the packaged chain.
_STEPS = 'import_and_deploy/_promote_steps.sh'

_BASH = shutil.which('bash')


#: How the callers run each step under ``set -e``: ``_promote.sh`` calls the carry-over in
#: an ``if`` and the warm-up on a line of its own, and ``deploy_new_code_and_database.sh``
#: exports ``previous_db_name``'s output. ``CONTINUED`` is printed when the caller goes on.
_CARRY_OVER = 'if ! carry_over_sessions opus_served; then exit 1; fi; echo CONTINUED'
_WARM = 'warm_search; echo CONTINUED'

#: What the fake ``opus_import --help`` prints when its release has the carry-over.
_HELP_WITH = '  --carry-over-sessions-from SCHEMA  Replace the sessions'
_HELP_WITHOUT = '  --create-cart  Create the cart table used by OPUS'


def _run_step(
    tmp_path: Path,
    call: str,
    *,
    import_status: int = 0,
    manage_status: int = 0,
    help_text: str = _HELP_WITH,
    help_status: int = 0,
    environment: dict[str, str] | None = None,
) -> tuple[int, str, list[str], list[str]]:
    """Source the steps with fakes under ``set -e``, as the callers do, and run one line.

    Parameters:
        tmp_path: A scratch directory.
        call: The line to run after sourcing, in the caller's form.
        import_status: What the fake ``opus_import`` exits with, except for ``--help``.
        manage_status: What the fake ``opus_manage`` exits with.
        help_text: What the fake ``opus_import --help`` prints.
        help_status: What the fake ``opus_import --help`` exits with.
        environment: Further variables to set.

    Returns:
        The line's status, everything it printed, each fake command it ran with its
        arguments (``--help`` aside), and each service action it asked for.
    """
    chain = tmp_path / 'chain'
    scripts.write_scripts(chain)
    fake_bin = tmp_path / 'bin'
    fake_bin.mkdir()
    calls = tmp_path / 'calls'
    services = tmp_path / 'services'
    for command, status in (('opus_import', import_status), ('opus_manage', manage_status)):
        fake = fake_bin / command
        fake.write_text(
            f'#!/bin/bash\nif [[ $1 == --help ]]; then echo "{help_text}"; exit {help_status}; fi\n'
            f'echo "{command} $*" >> {calls}\nexit {status}\n',
            encoding='utf-8',
        )
        fake.chmod(0o755)
    recorder = fake_bin / 'record_service'
    recorder.write_text(f'#!/bin/bash\necho "$*" >> {services}\n', encoding='utf-8')
    recorder.chmod(0o755)
    assert _BASH is not None
    finished = subprocess.run(  # nosec B603 - bash and the packaged file
        [_BASH, '-c', f'set -e; source "{chain / _STEPS}"; {call}'],
        env={
            'PATH': f'{fake_bin}:/usr/bin:/bin',
            'OPUS_SERVICE_COMMAND': str(recorder),
            'OPUS_WEB_SERVICE': 'opus-web',
            **(environment or {}),
        },
        capture_output=True,
        text=True,
        check=False,
    )
    ran = calls.read_text(encoding='utf-8').splitlines() if calls.exists() else []
    asked = services.read_text(encoding='utf-8').splitlines() if services.exists() else []
    return finished.returncode, finished.stdout + finished.stderr, ran, asked


@pytest.mark.skipif(_BASH is None, reason='needs bash')
def test_a_carry_over_that_succeeds_starts_nothing(tmp_path: Path) -> None:
    """The promotion goes on to the switch; the web service stays stopped until then."""
    status, output, ran, asked = _run_step(tmp_path, _CARRY_OVER)
    assert status == 0, output
    assert ran == ['opus_import --carry-over-sessions-from opus_served']
    assert asked == []
    assert 'CONTINUED' in output


@pytest.mark.skipif(_BASH is None, reason='needs bash')
def test_a_carry_over_that_fails_starts_the_web_service_and_returns_non_zero(
    tmp_path: Path,
) -> None:
    """Nothing has switched, so the installation that was serving serves again."""
    status, output, _ran, asked = _run_step(tmp_path, _CARRY_OVER, import_status=1)
    assert status == 1
    assert asked == ['start opus-web']
    assert 'could not carry sessions and carts over from opus_served' in output
    assert 'CONTINUED' not in output


@pytest.mark.skipif(_BASH is None, reason='needs bash')
def test_a_release_without_the_option_is_promoted_without_the_carry_over(
    tmp_path: Path,
) -> None:
    """Going back to an older release: a warning, no carry-over, and the promotion goes on."""
    status, output, ran, asked = _run_step(tmp_path, _CARRY_OVER, help_text=_HELP_WITHOUT)
    assert status == 0, output
    assert ran == []
    assert asked == []
    assert 'the release being promoted cannot carry sessions over' in output
    assert 'CONTINUED' in output


@pytest.mark.skipif(_BASH is None, reason='needs bash')
def test_a_help_that_fails_is_a_failed_carry_over(tmp_path: Path) -> None:
    """A failed probe does not show the option is absent, so the promotion stops and the
    installation that was serving serves again."""
    status, output, ran, asked = _run_step(tmp_path, _CARRY_OVER, help_status=1)
    assert status == 1
    assert ran == []
    assert asked == ['start opus-web']
    assert 'opus_import --help failed' in output
    assert 'cannot carry sessions over' not in output
    assert 'CONTINUED' not in output


@pytest.mark.skipif(_BASH is None, reason='needs bash')
@pytest.mark.parametrize('manage_status', [0, 1], ids=['warmed', 'failed'])
def test_the_warm_up_returns_zero_and_warns_when_it_fails(
    tmp_path: Path, manage_status: int
) -> None:
    """A cold cache is not a failed deploy, so the caller goes on under ``set -e``."""
    status, output, ran, asked = _run_step(tmp_path, _WARM, manage_status=manage_status)
    assert status == 0, output
    assert ran == ['opus_manage warm_search']
    assert asked == []
    assert ('WARNING: opus_manage warm_search failed' in output) == (manage_status != 0)
    assert 'CONTINUED' in output


@pytest.mark.skipif(_BASH is None, reason='needs bash')
@pytest.mark.parametrize(('value', 'warms'), [('false', False), ('False', True), ('', True)])
def test_the_warm_up_is_skipped_only_when_asked_with_false(
    tmp_path: Path, value: str, warms: bool
) -> None:
    """``OPUS_WARM_SEARCH=false`` skips it; any other value warms."""
    status, output, ran, _asked = _run_step(
        tmp_path, _WARM, environment={'OPUS_WARM_SEARCH': value}
    )
    assert status == 0, output
    assert (ran == ['opus_manage warm_search']) == warms
    assert 'CONTINUED' in output


def _previous(tmp_path: Path, deployed: str | None, target: str) -> str:
    """Return what ``previous_db_name`` prints for a deployed opus.toml and a target."""
    toml = tmp_path / 'deployed_opus.toml'
    if deployed is not None:
        toml.write_text(f'[database]\nschema = "{deployed}"\n', encoding='utf-8')
    status, output, _ran, _asked = _run_step(
        tmp_path,
        f'export PREVIOUS=$(previous_db_name "{toml}" "{target}"); echo "[$PREVIOUS]"',
    )
    assert status == 0, output
    return output.strip().removeprefix('[').removesuffix(']')


@pytest.mark.skipif(_BASH is None, reason='needs bash')
def test_previous_db_name_is_empty_without_a_deployed_installation(tmp_path: Path) -> None:
    """A first deploy carries nothing over."""
    assert _previous(tmp_path, None, 'opus_new') == ''


@pytest.mark.skipif(_BASH is None, reason='needs bash')
def test_previous_db_name_is_empty_for_the_schema_being_served(tmp_path: Path) -> None:
    """A redeploy of the served schema carries nothing over, which would empty it."""
    assert _previous(tmp_path, 'opus_new', 'opus_new') == ''


@pytest.mark.skipif(_BASH is None, reason='needs bash')
def test_previous_db_name_names_another_served_schema(tmp_path: Path) -> None:
    """A deploy of a new schema carries over from the one being served."""
    assert _previous(tmp_path, 'opus_old', 'opus_new') == 'opus_old'


def test_sourcing_the_steps_runs_nothing(tmp_path: Path) -> None:
    """Every top-level line belongs to a function definition, so the tests can source it."""
    scripts.write_scripts(tmp_path)
    depth = 0
    for line in (tmp_path / _STEPS).read_text(encoding='utf-8').splitlines():
        if line.strip() == '' or line.startswith('#'):
            continue
        if depth == 0:
            assert line.endswith('() {'), line
        depth += line.count('{') - line.count('}')
    assert depth == 0
