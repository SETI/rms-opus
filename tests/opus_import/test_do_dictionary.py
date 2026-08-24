"""Tests for the dictionary import step.

Only the parts of `opus_import.steps.do_dictionary` that read the packaged data files are
covered here; everything else in that module talks to a live database, which the
holdings-free suite has no access to. The database is replaced by a recorder so the
contexts reader can be driven end to end.
"""

from pathlib import Path
from typing import Any

import pytest

from opus_import import import_util
from opus_import.context import ImportContext
from opus_import.steps import do_dictionary

from .conftest import RecordingLogger, make_context


class _FakeDatabase:
    """An `importdb` stand-in that records the calls the step makes."""

    def __init__(self) -> None:
        self.created_tables: list[str] = []
        self.inserted: list[tuple[str, list[dict[str, Any]]]] = []

    def create_table(self, namespace: str, table_name: str, schema: Any,
                     ignore_if_exists: bool = True) -> bool:
        self.created_tables.append(table_name)
        return True

    def insert_rows(self, namespace: str, table_name: str,
                    rows: list[dict[str, Any]]) -> None:
        self.inserted.append((table_name, rows))


@pytest.fixture
def fake_pipeline() -> tuple[ImportContext, _FakeDatabase, RecordingLogger]:
    """Give the import step a context with a recording database and logger."""
    db = _FakeDatabase()
    logger = RecordingLogger()
    ctx = make_context(logger=logger, db=db)
    return ctx, db, logger


def _use_contexts_file(monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
                       contents: str) -> Path:
    """Write `contents` as the contexts.csv the step will read, and return its path."""
    contexts_file = tmp_path / 'contexts.csv'
    contexts_file.write_text(contents, encoding='utf-8')
    monkeypatch.setattr(import_util, 'DICTIONARY_DATA_DIR', tmp_path)
    return contexts_file


def test_create_import_contexts_table_reads_every_row(
        fake_pipeline: tuple[ImportContext, _FakeDatabase, RecordingLogger],
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """A well-formed file is turned into one row per line, with no error logged."""
    ctx, db, logger = fake_pipeline
    _use_contexts_file(monkeypatch, tmp_path,
                       'COISS,Cassini ISS,NULL\nCOVIMS,Cassini VIMS,NULL\n')

    assert do_dictionary.create_import_contexts_table(ctx) is True

    assert db.created_tables == ['contexts']
    assert db.inserted == [('contexts', [
        {'name': 'COISS', 'description': 'Cassini ISS', 'parent': 'NULL'},
        {'name': 'COVIMS', 'description': 'Cassini VIMS', 'parent': 'NULL'},
    ])]
    assert logger.messages_at('error') == []


def test_create_import_contexts_table_names_the_bad_row_and_its_file(
        fake_pipeline: tuple[ImportContext, _FakeDatabase, RecordingLogger],
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """A row without exactly three fields aborts the step, naming the file and the row.

    The message used to be an f-string missing its ``f``, so it reported the literal
    text ``Bad row in "{ctxfile}": {row}`` -- and the placeholder named a variable that
    does not exist, so simply adding the prefix would have raised `NameError` on this
    very path. Both halves are pinned here.
    """
    ctx, _db, logger = fake_pipeline
    contexts_file = _use_contexts_file(
        monkeypatch, tmp_path,
        'COISS,Cassini ISS,NULL\nCOVIMS,Cassini VIMS,NULL,EXTRA\n')

    assert do_dictionary.create_import_contexts_table(ctx) is False

    errors = logger.messages_at('error')
    assert len(errors) == 1
    assert str(contexts_file) in errors[0]
    assert "['COVIMS', 'Cassini VIMS', 'NULL', 'EXTRA']" in errors[0]
    assert '{' not in errors[0]


def test_create_import_contexts_table_inserts_nothing_when_a_row_is_bad(
        fake_pipeline: tuple[ImportContext, _FakeDatabase, RecordingLogger],
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """The step returns before writing, so a malformed file leaves the table empty."""
    ctx, db, _logger = fake_pipeline
    _use_contexts_file(monkeypatch, tmp_path, 'ONLY_TWO,FIELDS\n')

    assert do_dictionary.create_import_contexts_table(ctx) is False
    assert db.inserted == []


def test_create_import_contexts_table_reports_an_unreadable_file(
        fake_pipeline: tuple[ImportContext, _FakeDatabase, RecordingLogger],
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """A missing contexts.csv is an error naming the file, not a traceback."""
    ctx, _db, logger = fake_pipeline
    monkeypatch.setattr(import_util, 'DICTIONARY_DATA_DIR', tmp_path)

    assert do_dictionary.create_import_contexts_table(ctx) is False

    errors = logger.messages_at('error')
    assert len(errors) == 1
    assert str(tmp_path / 'contexts.csv') in errors[0]


def test_packaged_contexts_file_has_three_fields_in_every_row(
        fake_pipeline: tuple[ImportContext, _FakeDatabase, RecordingLogger]) -> None:
    """The shipped contexts.csv is well formed, so the bad-row branch never fires.

    This reads the real package data (no `DICTIONARY_DATA_DIR` override), so it is what
    keeps a future edit to contexts.csv from breaking the import step unnoticed.
    """
    ctx, db, logger = fake_pipeline

    assert do_dictionary.create_import_contexts_table(ctx) is True

    assert logger.messages_at('error') == []
    table_name, rows = db.inserted[0]
    assert table_name == 'contexts'
    assert len(rows) > 0
