"""What the observation row builder does to a string bound for an ASCII column.

An ASCII column, ``varchar`` or ``text``, may not hold the character the web application
binds for one with no ASCII form, so the builder reports a value carrying it and removes
the character. The field function is a stand-in; what is driven is the check on its value.
"""

from typing import Any

import pytest

from opus_import.context import ImportContext
from opus_import.steps import do_import_mult, do_import_obs
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


#: A table of one GROUP column, holding a mult id, and one MULTIGROUP list column.
_GROUP_SCHEMA: list[dict[str, Any]] = [
    {
        'field_name': 'planet',
        'field_type': 'varchar40',
        'pi_form_type': 'GROUP',
        'data_source': 'COMPUTE',
    },
    {
        'field_name': 'targets',
        'field_type': 'mult_list',
        'pi_form_type': 'MULTIGROUP',
        'data_source': 'COMPUTE',
    },
]


def _mult_spec(value: str | None, label: str | None = None) -> dict[str, Any]:
    """Return a field method's full specification of one mult value."""
    return {
        'col_val': value,
        'disp_name': label,
        'disp': 'Y',
        'pin': None,
        'grouping': None,
        'group_pin': None,
    }


def _group_row(
    monkeypatch: pytest.MonkeyPatch, results: dict[str, tuple[bool, Any]]
) -> tuple[Any, ImportContext, list[tuple[str, Any, Any]]]:
    """Build one row of `_GROUP_SCHEMA` whose field functions give `results`.

    Returns:
        The row, the context, and each value given to the mult table with its label, the
        stand-in giving every value the id ``len(calls)``.
    """
    calls: list[tuple[str, Any, Any]] = []

    def field_function(
        _ctx: ImportContext, _obj: Any, _table: str, _schema: Any, _meta: Any, field: str
    ) -> tuple[bool, Any]:
        return results[field]

    def update_mult_table(
        _ctx: ImportContext,
        _table: str,
        field: str,
        _column: Any,
        val: Any,
        label: Any,
        *args: Any,
    ) -> int:
        calls.append((field, val, label))
        return len(calls)

    monkeypatch.setattr(do_import_obs, 'import_run_field_function', field_function)
    monkeypatch.setattr(do_import_mult, 'update_mult_table', update_mult_table)
    ctx = make_context()
    row = do_import_obs.import_observation_table(
        ctx,
        object(),  # type: ignore[arg-type]
        'obs_test',
        _GROUP_SCHEMA,
        {},
    )
    return row, ctx, calls


def test_a_group_column_whose_field_method_failed_takes_the_absent_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The failure was logged where it happened; the row is built, so the index goes on
    and the bundle fails, rather than the whole index stopping."""
    row, ctx, calls = _group_row(
        monkeypatch, {'planet': (False, None), 'targets': (True, [_mult_spec('SATURN')])}
    )
    assert calls == [('planet', None, 'N/A'), ('targets', 'SATURN', 'Saturn')]
    assert row['planet'] == 1
    assert ctx.logger.messages_at('error') == []


def test_a_group_column_given_plain_values_logs_and_takes_the_absent_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A single value takes the absent id; a list column given plain values holds none."""
    row, ctx, calls = _group_row(
        monkeypatch, {'planet': (True, 'SATURN'), 'targets': (True, ['A', 'B'])}
    )
    assert calls == [('planet', None, 'N/A'), ('targets', None, 'N/A'), ('targets', None, 'N/A')]
    assert row == {'planet': 1, 'targets': None}
    planet_error, targets_error = ctx.logger.messages_at('error')
    assert 'Column "planet" in table "obs_test" holds mult ids' in planet_error
    assert 'Column "targets" in table "obs_test" holds mult ids' in targets_error
    assert ctx.import_has_bad_data


def test_an_empty_value_or_list_of_a_group_column_raises_nothing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An empty string labels itself empty, and an empty list is a list column's NULL."""
    row, _ctx, calls = _group_row(
        monkeypatch, {'planet': (True, [_mult_spec('')]), 'targets': (True, [])}
    )
    assert calls == [('planet', '', '')]
    assert row == {'planet': 1, 'targets': None}
