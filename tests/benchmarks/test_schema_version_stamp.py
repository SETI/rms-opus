"""Tests for how the harness learns a side's schema version and gives a schema its row."""

from __future__ import annotations

import inspect
import sys
from pathlib import Path
from typing import Any

import pytest

from benchmarks import bench_server, bench_web
from benchmarks.bench_web import WebRunError, stamp_schema_version
from benchmarks.sides import Side, SideError, Spelling
from opus_import.schema_version import SCHEMA_VERSION

#: Help text with and without the version step.
_NEW_HELP = '--do-all-import --drop-cache-tables --validate-perm --write-schema-version'
_OLD_HELP = '--do-all-import --drop-cache-tables --validate-perm'


def _fake_python(tmp_path: Path, script: str) -> Path:
    """Write an executable that stands in for a side's interpreter.

    Parameters:
        tmp_path: Where to write it.
        script: Its shell body.

    Returns:
        Its path.
    """
    path = tmp_path / 'python'
    path.write_text(f'#!/bin/bash\n{script}\n', encoding='utf-8')
    path.chmod(0o755)
    return path


def test_a_side_reports_its_schema_version(tmp_path: Path) -> None:
    """This interpreter has the module, so it reports the constant."""
    assert Side(Path(sys.executable), tmp_path).schema_version() == SCHEMA_VERSION


def test_a_side_without_the_module_reports_none(tmp_path: Path) -> None:
    """A commit before the module has no version, which is not an error."""
    side = Side(_fake_python(tmp_path, 'echo None'), tmp_path)
    assert side.schema_version() is None


def test_a_failing_interpreter_is_an_error(tmp_path: Path) -> None:
    """Anything other than the module's absence is reported, not taken for None."""
    side = Side(_fake_python(tmp_path, 'echo broken >&2; exit 1'), tmp_path)
    with pytest.raises(SideError, match='broken'):
        side.schema_version()


def test_every_clone_states_the_version() -> None:
    """The right value depends on the side, so the parameter has no default."""
    parameter = inspect.signature(bench_server.clone_schema).parameters['version']
    assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
    assert parameter.default is inspect.Parameter.empty


class _VersionedSide:
    """A side whose version is fixed and whose import steps are recorded."""

    def __init__(self, version: int | None) -> None:
        self.version = version
        self.ran: list[list[str]] = []

    def schema_version(self) -> int | None:
        """Return the fixed version."""
        return self.version

    def run(self, arguments: list[str], *, env: Any) -> Any:
        """Record an import step, which succeeds."""
        self.ran.append(arguments)
        return type('Finished', (), {'returncode': 0, 'stderr': ''})()


def _stamp(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    side: _VersionedSide,
    *,
    has_row: bool,
    help_text: str = _NEW_HELP,
) -> tuple[int | None, list[tuple[str, int]]]:
    """Stamp a schema for `side`, with `restamp_version` recorded.

    Parameters:
        monkeypatch: The fixture.
        tmp_path: A scratch directory.
        side: The side.
        has_row: Whether the schema already has a version row.
        help_text: The side's ``opus_import --help``.

    Returns:
        What the stamp returned, and every restamp it asked for.
    """
    restamped: list[tuple[str, int]] = []

    def restamp(server: Any, schema: str, version: int) -> bool:
        restamped.append((schema, version))
        return has_row

    monkeypatch.setattr(bench_web, 'restamp_version', restamp)
    version = stamp_schema_version(
        None,  # type: ignore[arg-type]  # restamp_version is replaced
        'shared',
        side,  # type: ignore[arg-type]  # a stand-in side
        Spelling.from_help(help_text),
        {},
        tmp_path / 'ERRORS.log',
    )
    return version, restamped


def test_a_row_is_restamped_to_the_sides_version(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Two sides serving one schema each see their own version."""
    side = _VersionedSide(5)
    version, restamped = _stamp(monkeypatch, tmp_path, side, has_row=True)
    assert version == 5
    assert restamped == [('shared', 5)]
    assert side.ran == []


def test_a_schema_with_no_row_gets_one_from_the_sides_own_step(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A schema an earlier import built has no row until the side's step writes it."""
    side = _VersionedSide(5)
    _, restamped = _stamp(monkeypatch, tmp_path, side, has_row=False)
    assert restamped == [('shared', 5)]
    assert side.ran == [['-m', 'opus_import', '--write-schema-version']]


def test_a_side_with_no_version_leaves_the_schema_alone(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Code before the version checks nothing, so nothing is written for it."""
    side = _VersionedSide(None)
    version, restamped = _stamp(monkeypatch, tmp_path, side, has_row=False, help_text=_OLD_HELP)
    assert version is None
    assert restamped == []
    assert side.ran == []


def test_a_version_without_the_step_is_an_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A side that checks a row but cannot write one would serve only 503s."""
    with pytest.raises(WebRunError, match='no --write-schema-version'):
        _stamp(monkeypatch, tmp_path, _VersionedSide(5), has_row=False, help_text=_OLD_HELP)
