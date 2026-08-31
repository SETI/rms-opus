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

import os

import pytest

from import_tests.tools import fixture_layout, obs_execution, whitelist_blocks

#: What GitHub Actions sets in every step of every job. Its presence is how this module
#: tells "a developer ran the suite the quick way" from "the job that owns this gate did
#: not produce its input", which have the same symptom and opposite meanings.
CI_ENV_VAR = 'GITHUB_ACTIONS'

#: The two commands that produce the report, named in both the skip and the failure so
#: whichever one a reader hits tells them what to run.
HOW_TO_PRODUCE = (
    'pytest import_tests --ignore=import_tests/test_obs_execution.py '
    '--cov --cov-report=json:coverage.json && pytest import_tests/test_obs_execution.py'
)


@pytest.fixture(scope='session')
def findings() -> obs_execution.Findings:
    """Compare the coverage report with the checked-in whitelist.

    A missing report means two different things in two places, and this is where they are
    told apart. Locally it means the suite was run the default way, without coverage,
    which is the fast way and the one the developer guide recommends -- so these tests
    skip and say how to produce the data. Under CI it means the job that owns this gate
    stopped producing its input, so it is a failure: skipping there would let someone drop
    ``--cov`` from the workflow and silently delete the gate, which is exactly the
    check-that-cannot-fail this module exists to be.
    """
    report_path = obs_execution.DEFAULT_REPORT
    if not report_path.is_file():
        if os.environ.get(CI_ENV_VAR):
            pytest.fail(
                f'{report_path} is missing under {CI_ENV_VAR}, where this gate is '
                f'required. The job must run: {HOW_TO_PRODUCE}'
            )
        pytest.skip(
            f'{report_path} is missing, so there is nothing to check the obs layer '
            f'against. This is the default local run; to produce it: {HOW_TO_PRODUCE}'
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
