"""What the observation row builder does to a string bound for a ``varcharNNN`` column.

A ``varchar`` keeps the trailing spaces a fixed-width ``char`` dropped on reading, so the
builder drops them, and the database returns what it did when the columns were ``char``.
An ASCII column, ``varchar`` or ``text``, may not hold the character the web application
binds for one with no ASCII form, so the builder reports a value carrying it and removes
the character. The field function is a stand-in; what is driven is the check on its value.
"""

from typing import Any

import pytest

from opus_import.context import ImportContext
from opus_import.steps import do_import_obs
from opus_support import UNSTORED_ASCII_CHARACTER

from .conftest import make_context

#: A table of three string columns, two of them ASCII, one of those a ``text`` column.
_SCHEMA: list[dict[str, Any]] = [
    {'field_name': 'name', 'field_type': 'varchar10', 'data_source': 'COMPUTE'},
    {
        'field_name': 'code',
        'field_type': 'varchar10',
        'field_charset': 'ascii',
        'data_source': 'COMPUTE',
    },
    {
        'field_name': 'targets',
        'field_type': 'text',
        'field_charset': 'ascii',
        'data_source': 'COMPUTE',
    },
    {'field_name': 'size', 'field_type': 'uint4', 'data_source': 'COMPUTE'},
]


def _row(monkeypatch: pytest.MonkeyPatch, values: dict[str, Any]) -> tuple[Any, ImportContext]:
    """Build one row of `_SCHEMA` whose field functions return `values`.

    Returns:
        The row, and the context whose logger recorded the run.
    """

    def field_function(
        _ctx: ImportContext, _obj: Any, _table: str, _schema: Any, _meta: Any, field: str
    ) -> tuple[bool, Any]:
        return True, values[field]

    monkeypatch.setattr(do_import_obs, 'import_run_field_function', field_function)
    ctx = make_context()
    row = do_import_obs.import_observation_table(ctx, object(), 'obs_test', _SCHEMA, {})  # type: ignore[arg-type]
    return row, ctx


def test_a_strings_trailing_spaces_are_dropped(monkeypatch: pytest.MonkeyPatch) -> None:
    """Only trailing spaces go, and only from a ``varchar``: a leading space, a trailing
    tab and a ``text`` column's spaces stay."""
    values = {'name': ' Cassini  ', 'code': 'COISS\t ', 'targets': 'SATURN ', 'size': 3}
    row, ctx = _row(monkeypatch, values)
    assert row == {'name': ' Cassini', 'code': 'COISS\t', 'targets': 'SATURN ', 'size': 3}
    assert ctx.logger.messages_at('error') == []


def test_spaces_do_not_count_toward_the_width(monkeypatch: pytest.MonkeyPatch) -> None:
    """A value that fits once its trailing spaces are dropped is not too long."""
    row, ctx = _row(monkeypatch, {'name': 'abcdefghij   ', 'code': 'x', 'targets': '', 'size': 0})
    assert row['name'] == 'abcdefghij'
    assert ctx.logger.messages_at('error') == []


def test_the_unstored_character_is_refused_in_an_ascii_column(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """In an ASCII column, ``varchar`` or ``text``, it is an error naming the column, and
    the value is stored without it; elsewhere it is a character."""
    value = f'CO{UNSTORED_ASCII_CHARACTER}ISS'
    row, ctx = _row(monkeypatch, {'name': value, 'code': value, 'targets': value, 'size': 0})
    code_error, targets_error = ctx.logger.messages_at('error')
    assert 'Column "code" in table "obs_test" is ASCII' in code_error
    assert 'Column "targets" in table "obs_test" is ASCII' in targets_error
    assert row == {'name': value, 'code': 'COISS', 'targets': 'COISS', 'size': 0}


def test_strip_stored_text_reads_the_types_from_the_schema() -> None:
    """A ``varchar`` value loses its trailing spaces; any other column is left alone."""
    row = {'name': 'a  ', 'code': 'b ', 'size': 3, 'other': 'c  '}
    assert do_import_obs.strip_stored_text(row, _SCHEMA) == {
        'name': 'a',
        'code': 'b',
        'size': 3,
        'other': 'c  ',
    }
