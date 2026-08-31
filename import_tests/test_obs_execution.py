"""Every obs function is proven executed by the run, or whitelisted with a reason.

This module reads the coverage report the suite's own coverage run writes, so it is asked
for on its own after that run rather than during it -- the report does not exist until
the session that produces it has ended. The workflow runs the suite once with a JSON
coverage report and then this module alone.

Running it without that report is an error rather than a skip: a check that reports
success when it cannot see its input is not a check. The command it names in that error
is a bare ``--cov`` on purpose -- naming a package there would measure a different scope
from the one ``[tool.coverage.run]`` defines and ``fail_under`` is calibrated against.
"""

from __future__ import annotations

import pytest

from import_tests.tools import fixture_layout, obs_execution, whitelist_blocks


@pytest.fixture(scope='session')
def findings() -> obs_execution.Findings:
    """Compare the coverage report with the checked-in whitelist."""
    report_path = obs_execution.DEFAULT_REPORT
    if not report_path.is_file():
        pytest.fail(
            f'{report_path} is missing. Run the suite with a JSON coverage report first: '
            'pytest import_tests --ignore=import_tests/test_obs_execution.py '
            '--cov --cov-report=json:coverage.json'
        )
    return obs_execution.check(
        obs_execution.read_report(report_path),
        obs_execution.read_whitelist(fixture_layout.UNEXECUTED_METHODS_FILE),
    )


def test_every_obs_function_executed(findings: obs_execution.Findings) -> None:
    """No obs function went unrun without a whitelist entry explaining why.

    An unrun function is a branch the sampled index rows never reached, so this is also
    the recorder's report on where its sampling is thin.
    """
    assert findings.unexplained == []


def test_no_whitelisted_function_actually_ran(findings: obs_execution.Findings) -> None:
    """No whitelist entry admits a function the run reaches after all."""
    assert findings.needless == []


def test_no_whitelist_entry_names_a_missing_function(findings: obs_execution.Findings) -> None:
    """No whitelist entry names a function that is no longer there to be reached."""
    assert findings.unknown == []


def test_every_whitelist_entry_carries_a_reason() -> None:
    """Every whitelist entry sits in a block a comment introduces."""
    assert (
        whitelist_blocks.unexplained_entries(
            fixture_layout.UNEXECUTED_METHODS_FILE, obs_execution.COMMENT_PREFIX
        )
        == []
    )
