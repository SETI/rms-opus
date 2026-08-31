"""Prove every obs function was executed by the run, rather than merely imported.

The obs layer is ~12,000 lines of field methods, and importing it and enumerating its
methods by introspection lights up almost all of it without calling any of them. Coverage
attributes a function's ``def`` line to the enclosing module region, so a method that was
only defined reports 0% in its own region and only a real call registers.

An unexecuted method is exactly a branch the sampled rows never reached, so the report
this produces is also the recorder's guide to where the sampling is thin. The few that
the fixture cannot reach at all are whitelisted one at a time, each with a comment saying
why.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from import_tests.tools import fixture_layout

#: The tree whose functions have to be shown executed. Matched as a path suffix, because
#: a coverage report's file keys depend on where the run was started from.
OBS_PATH_MARKER = 'opus_import/obs/'

#: The coverage report the check reads, written by the suite's own coverage run.
DEFAULT_REPORT = fixture_layout.REPO_ROOT / 'coverage.json'

#: How a whitelist entry names a function: the report's own file key, then the function's
#: qualified name.
ENTRY_SEPARATOR = '::'

#: A whitelist line starting with this is a comment. Every entry carries one above it.
COMMENT_PREFIX = '#'

#: The key coverage gives the module-level region, which is not a function.
_MODULE_REGION = ''


@dataclass(frozen=True)
class ExecutionReport:
    """What one coverage report says about the obs layer.

    Attributes:
        executed: The functions with at least one executed line, as
            ``<file>::<qualname>``.
        unexecuted: The functions with none.
    """

    executed: set[str]
    unexecuted: set[str]

    @property
    def known(self) -> set[str]:
        """Every obs function the report describes."""
        return self.executed | self.unexecuted


def read_report(report_path: Path) -> ExecutionReport:
    """Read a coverage JSON report and split the obs layer's functions in two.

    A function whose region holds no measurable statements is described by neither set.
    That is a real category rather than a technicality: ``[tool.coverage.report]``
    excludes ``raise NotImplementedError``, so an abstract method whose whole body is
    that line has nothing coverage can record, and its region reads exactly like a
    method nobody called even when every subclass call goes through it. "Nothing to
    prove" and "never ran" are different answers, and conflating them would fill the
    whitelist with entries that could never come off it.

    Parameters:
        report_path: The report to read.

    Returns:
        Which obs functions ran and which did not.

    Raises:
        FileNotFoundError: If the report is not there. It is written by the coverage run
            of this suite, so its absence means the check is being asked a question
            nothing has answered.
        ValueError: If the report carries no per-function regions, which a coverage
            older than 7.6 produces.
    """
    data = json.loads(report_path.read_text(encoding='utf-8'))
    executed: set[str] = set()
    unexecuted: set[str] = set()
    saw_regions = False
    for file_key, file_data in data['files'].items():
        if OBS_PATH_MARKER not in file_key.replace('\\', '/'):
            continue
        if 'functions' not in file_data:
            continue
        saw_regions = True
        for qualname, region in file_data['functions'].items():
            if qualname == _MODULE_REGION:
                continue
            if region['summary']['num_statements'] == 0:
                continue
            name = f'{file_key}{ENTRY_SEPARATOR}{qualname}'
            if len(region['executed_lines']) > 0:
                executed.add(name)
            else:
                unexecuted.add(name)
    if not saw_regions:
        raise ValueError(
            f'{report_path} carries no per-function regions for {OBS_PATH_MARKER}; '
            'they need coverage 7.6 or newer and a run that reached the obs layer'
        )
    return ExecutionReport(executed=executed, unexecuted=unexecuted)


def read_whitelist(path: Path) -> list[str]:
    """Read the functions the fixture is not expected to reach.

    Parameters:
        path: The whitelist file.

    Returns:
        The entries, in file order.
    """
    entries = []
    for line in path.read_text(encoding='utf-8').splitlines():
        stripped = line.strip()
        if len(stripped) == 0 or stripped.startswith(COMMENT_PREFIX):
            continue
        entries.append(stripped)
    return entries


@dataclass(frozen=True)
class Findings:
    """What the check found.

    Attributes:
        unexplained: Functions that never ran and are not whitelisted.
        needless: Whitelisted functions that did run.
        unknown: Whitelisted functions the report does not describe at all, which means
            the entry names something that no longer exists.
    """

    unexplained: list[str]
    needless: list[str]
    unknown: list[str]


def check(report: ExecutionReport, whitelist: list[str]) -> Findings:
    """Compare a coverage report with the whitelist, in every direction.

    Parameters:
        report: What ran and what did not.
        whitelist: The functions the fixture is not expected to reach.

    Returns:
        The findings, all three of which are defects.
    """
    admitted = set(whitelist)
    return Findings(
        unexplained=sorted(report.unexecuted - admitted),
        needless=sorted(admitted & report.executed),
        unknown=sorted(admitted - report.known),
    )
