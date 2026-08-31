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

import ast
import json
from dataclasses import dataclass
from pathlib import Path

from import_tests.tools import fixture_layout
from opus_import.steps.do_import_obs import field_function_name

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
    That is a real category rather than a technicality: every line of such a body is one
    ``[tool.coverage.report]``'s ``exclude_lines`` removes, so there is nothing coverage
    can record and the region reads exactly like a method nobody called -- even when
    every call goes through it. In this tree that is an abstract method whose whole body
    is ``raise NotImplementedError``, and a stub inside an ``if TYPE_CHECKING:`` block;
    the rule is written against the exclusion rather than against those two shapes, so a
    body emptied by ``pragma: no cover`` or by the ``def __repr__`` entry lands in the
    same category without anyone having to notice. "Nothing to prove" and "never ran" are
    different answers, and conflating them would fill the whitelist with entries that
    could never come off it.

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


#: Where the packaged table schemas live, which is what names every dispatched method.
_SCHEMA_DIR = fixture_layout.REPO_ROOT / 'src' / 'opus_import' / 'table_schemas'

#: The trees a call to an obs method could be written in.
_SOURCE_ROOTS = ('src', 'tests', 'import_tests', 'integration_tests', 'scripts')


def dispatched_names() -> set[str]:
    """Return every obs method name the pipeline can call without naming it in source.

    The import computes a field method's name from the table and column it is filling,
    so those methods have no textual call site and are reached anyway. That rule is
    `opus_import.steps.do_import_obs.field_function_name`, and it is asked rather than
    restated, so a change to the rule changes this set with it.

    Returns:
        The method names the packaged schemas make reachable.
    """
    names = set()
    for path in sorted(_SCHEMA_DIR.glob('*.json')):
        try:
            schema = json.loads(path.read_text(encoding='utf-8'))
        except json.JSONDecodeError:
            continue
        if not isinstance(schema, list):
            continue
        for column in schema:
            if isinstance(column, dict) and column.get('field_name'):
                names.add(field_function_name(path.stem, column['field_name']))
    return names


def referenced_names() -> set[str]:
    """Return every name the shipped source mentions somewhere other than a definition.

    Read from the syntax tree rather than the text: an attribute access and a bare name
    are what a call site looks like, and a `def` line is not one.

    Returns:
        The names used anywhere under `_SOURCE_ROOTS`.
    """
    used: set[str] = set()
    for root in _SOURCE_ROOTS:
        directory = fixture_layout.REPO_ROOT / root
        if not directory.is_dir():
            continue
        for path in sorted(directory.rglob('*.py')):
            try:
                tree = ast.parse(path.read_text(encoding='utf-8'))
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Attribute):
                    used.add(node.attr)
                elif isinstance(node, ast.Name):
                    used.add(node.id)
    return used


def unreachable_entries(whitelist: list[str]) -> list[str]:
    """Return the whitelist entries naming a function nothing can call.

    "This fixture does not reach it" and "nothing reaches it" are different claims, and
    only the first belongs in the whitelist: the second is dead code, and admitting it
    here would keep it alive by explaining away the only evidence of its deadness.

    A function counts as reachable if the pipeline can dispatch to it by name, if any
    shipped source mentions it, or if it is a dunder -- those are called by the language
    rather than by name, so no call site exists to find.

    Parameters:
        whitelist: The entries to check.

    Returns:
        One entry per function with no caller of any kind, sorted.
    """
    reachable = dispatched_names() | referenced_names()
    unreachable = []
    for entry in whitelist:
        method = entry.partition(ENTRY_SEPARATOR)[2].rsplit('.', 1)[-1]
        if method.startswith('__') and method.endswith('__'):
            continue
        if method not in reachable:
            unreachable.append(entry)
    return sorted(unreachable)
