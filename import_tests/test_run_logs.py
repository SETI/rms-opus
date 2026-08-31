"""The run's real gate is its log, not its exit status.

``--validate-perm`` reports every validation failure through the logger and still exits
zero, and so do several other steps, so a run is judged by what it wrote to
``ERRORS.log`` and ``WARNINGS.log``. Every warning has to be admitted by a checked-in
whitelist entry carrying a comment saying why it is benign, and an entry that admits
nothing is itself a defect -- a whitelist's whole value is that every line was justified
against a warning someone actually saw.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from import_tests.tools import fixture_layout, run_logs, whitelist_blocks

if TYPE_CHECKING:
    from import_tests.tools.build_run import ImportRun


@pytest.fixture(scope='session')
def whitelist() -> list[run_logs.WhitelistEntry]:
    """Return the checked-in warning whitelist."""
    return run_logs.read_whitelist(fixture_layout.WARNING_WHITELIST_FILE)


@pytest.fixture(scope='session')
def warning_classification(
    main_run: ImportRun, whitelist: list[run_logs.WhitelistEntry]
) -> tuple[list[str], list[run_logs.WhitelistEntry]]:
    """Return the run's unadmitted warnings and the whitelist entries nothing needed."""
    warnings = run_logs.read_messages(main_run.paths.warnings_log)
    return run_logs.classify(warnings, whitelist)


def test_no_pipeline_step_stopped(main_run: ImportRun) -> None:
    """No invocation of the pipeline exited non-zero.

    A zero status does not mean a step succeeded -- the log is what says that -- but a
    non-zero one means the step stopped, and a step that stopped before it logged
    anything leaves the log silent about it.
    """
    stopped = [
        f'{" ".join(step.arguments)} exited {step.returncode}: {step.stderr.strip()[-2000:]}'
        for step in main_run.steps
        if step.returncode != 0
    ]
    assert stopped == []


def test_no_errors_were_logged(main_run: ImportRun) -> None:
    """The run logged nothing at error level.

    The exit status cannot stand in for this: the validation step raises nothing and its
    return value is discarded, so a validation failure leaves a zero status behind.
    """
    assert run_logs.distinct(run_logs.read_messages(main_run.paths.errors_log)) == []


def test_every_warning_is_whitelisted(
    warning_classification: tuple[list[str], list[run_logs.WhitelistEntry]],
) -> None:
    """No warning the run logged is one nobody has looked at."""
    unmatched, _unused = warning_classification
    assert run_logs.distinct(unmatched) == []


def test_no_whitelist_entry_is_stale(
    warning_classification: tuple[list[str], list[run_logs.WhitelistEntry]],
) -> None:
    """Every whitelist entry admits a warning this run actually produced.

    An entry that matches nothing is a claim about the run that is no longer true, and
    leaving it in would let it admit some future warning nobody chose to accept.
    """
    _unmatched, unused = warning_classification
    assert [f'line {entry.line_number}: {entry.pattern.pattern}' for entry in unused] == []


def test_every_whitelist_entry_carries_a_reason() -> None:
    """Every whitelist entry sits in a block a comment introduces."""
    assert (
        whitelist_blocks.unexplained_entries(
            fixture_layout.WARNING_WHITELIST_FILE, run_logs.COMMENT_PREFIX
        )
        == []
    )
