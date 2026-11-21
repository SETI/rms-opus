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


def _one_column(
    monkeypatch: pytest.MonkeyPatch,
    column: dict[str, Any],
    value: Any,
    *,
    ok: bool = True,
) -> tuple[Any, ImportContext]:
    """Build a row of one ``COMPUTE`` column named ``v`` whose field function gives `value`,
    succeeding unless `ok` is False.

    Returns:
        The value stored, and the context whose logger recorded the run.
    """

    def field_function(
        _ctx: ImportContext, _obj: Any, _table: str, _schema: Any, _meta: Any, _field: str
    ) -> tuple[bool, Any]:
        return ok, value

    monkeypatch.setattr(do_import_obs, 'import_run_field_function', field_function)
    ctx = make_context()
    schema = [{'field_name': 'v', 'data_source': 'COMPUTE', **column}]
    row = do_import_obs.import_observation_table(ctx, object(), 'obs_test', schema, {})  # type: ignore[arg-type]
    return row['v'], ctx


@pytest.mark.parametrize(
    ('field_type', 'given', 'stored'),
    [
        ('flag_yesno', 1, 'Yes'),
        ('flag_yesno', 'n', 'No'),
        ('flag_onoff', 'ON', 'On'),
        ('flag_onoff', 0, 'Off'),
        ('flag_yesno', 'N/A', None),
        ('flag_yesno', 'UNK', None),
    ],
)
def test_a_flag_value_is_spelled_as_its_type_spells_it(
    monkeypatch: pytest.MonkeyPatch, field_type: str, given: Any, stored: Any
) -> None:
    """Each spelling of yes, no, on and off is stored in the type's one spelling, and an
    unknown is NULL, with nothing logged."""
    value, ctx = _one_column(monkeypatch, {'field_type': field_type}, given)
    assert value == stored
    assert ctx.logger.messages_at('error') == []


@pytest.mark.parametrize(
    ('column', 'given', 'stored', 'logged'),
    [
        ({'field_type': 'flag_yesno'}, 'maybe', None, 'has FLAG type but value "maybe"'),
        ({'field_type': 'varchar5'}, 12, '', 'has VARCHAR type but value "12"'),
        ({'field_type': 'varchar5'}, 'COISS2', 'COISS', 'has VARCHAR size 5 but value'),
        ({'field_type': 'real8'}, 'wide', None, 'has REAL type but "wide" is not a float'),
        ({'field_type': 'int4'}, '4.5', None, 'has INT type but "4.5" is not an int'),
        (
            {'field_type': 'real8', 'val_sentinel': [-1e32]},
            -1e32,
            None,
            'Caught sentinel value -1e+32 for column "v"',
        ),
        ({'field_type': 'real8', 'val_min': 0}, -3, None, 'has minimum value 0 but -3'),
        ({'field_type': 'real8', 'val_max': 360}, 400, None, 'has maximum value 360 but 400'),
        (
            {'field_type': 'real8', 'field_notnull': True},
            None,
            None,
            'has NULL value but NOT NULL is set',
        ),
    ],
    ids=[
        'flag',
        'varchar-type',
        'varchar-length',
        'real',
        'int',
        'sentinel',
        'minimum',
        'maximum',
        'not-null',
    ],
)
def test_a_value_its_column_cannot_hold_is_an_error_and_is_stored_as_the_column_can(
    monkeypatch: pytest.MonkeyPatch,
    column: dict[str, Any],
    given: Any,
    stored: Any,
    logged: str,
) -> None:
    """The error names the column and table, marks the import's data bad, and the value
    stored is the one the column can hold: NULL, empty, or cut to its size."""
    value, ctx = _one_column(monkeypatch, column, given)
    assert value == stored
    (error,) = ctx.logger.messages_at('error')
    assert 'Column "v"' in error or 'column "v"' in error
    assert logged in error
    assert ctx.import_has_bad_data


@pytest.mark.parametrize(
    ('column', 'given'),
    [
        ({'field_type': 'real8', 'val_min': 0, 'val_set_invalid_to_null': True}, -3),
        ({'field_type': 'real8', 'val_max': 360, 'val_set_invalid_to_null': True}, 400),
    ],
    ids=['minimum', 'maximum'],
)
def test_an_out_of_range_value_a_column_nulls_is_logged_at_debug_only(
    monkeypatch: pytest.MonkeyPatch, column: dict[str, Any], given: Any
) -> None:
    """``val_set_invalid_to_null`` stores NULL and logs no error."""
    value, ctx = _one_column(monkeypatch, column, given)
    assert value is None
    assert ctx.logger.messages_at('error') == []
    (debug,) = [msg for msg in ctx.logger.messages_at('debug') if 'substituting NULL' in msg]
    assert 'Column "v" in table "obs_test"' in debug
    assert not ctx.import_has_bad_data


def test_a_value_within_range_is_stored_as_given(monkeypatch: pytest.MonkeyPatch) -> None:
    """The bounds and the sentinel leave an ordinary value alone."""
    column = {'field_type': 'real8', 'val_min': 0, 'val_max': 360, 'val_sentinel': -1e32}
    value, ctx = _one_column(monkeypatch, column, 12.5)
    assert value == 12.5
    assert ctx.logger.messages_at('error') == []


def test_a_column_whose_field_method_failed_is_stored_null(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The failure was logged where it happened; the column is NULL."""
    value, ctx = _one_column(monkeypatch, {'field_type': 'real8'}, 'unused', ok=False)
    assert value is None
    assert ctx.logger.messages_at('error') == []
