"""How the import finds, adds and reports the values of a mult field.

A stand-in database holds one field's stored rows, so the cache, the conflict warning,
the refusal of a value outside a pinned list and the id ceiling are driven without a
server. The field ids are given, as `opus_import.mult_fields.ensure_mult_fields` would
have read them.
"""

from __future__ import annotations

from typing import Any, cast

import pytest

from opus_import.context import ImportContext
from opus_import.importdb.super import ImportDBError, ImportDBSuper
from opus_import.mult_fields import MultFieldInfo
from opus_import.steps import do_import_mult
from opus_import.steps.do_import_mult import MAX_MULT_ID, PINNED_ABSENT_ID, MultIdOverflowError
from opus_support import collation_key

from .conftest import RecordingLogger, make_context

#: The stand-in column, discovered from the data.
COLUMN: dict[str, Any] = {'field_name': 'quality', 'pi_form_type': 'GROUP'}

#: The stand-in pinned column.
PINNED: dict[str, Any] = {
    'field_name': 'kind',
    'pi_form_type': 'GROUP',
    'mult_options': [[0, 'A', 'Alpha', 10, 'Y', None, None], [1, 'B', 'Beta', 20, 'Y', None, None]],
}


#: The stand-in field ids.
QUALITY, KIND = 1, 2

Row = tuple[Any, ...]
"""A stored row: ``(id, value, label, pin, display, grouping)``."""


def _server_key(value: str) -> str:
    """Fold a value as the stand-in server's collation does: as the cache does, and ``ø``
    as ``o``, which `opus_support.collation_key` keeps apart."""
    return collation_key(value).replace('ø', 'o')


class _Server:
    """A stand-in database holding each field's ``mult`` rows, with its unique keys.

    It answers the cache's read of a field and its probe of one value, compares values
    as `_server_key` does, and records every write; an insert whose value or id the field
    holds fails as the server's keys would make it.
    """

    def __init__(self, rows: dict[int, list[Row]]) -> None:
        self.rows = {field_id: list(stored) for field_id, stored in rows.items()}
        self.upserted: list[str] = []
        self.updates: list[tuple[str, dict[str, Any], list[Any]]] = []

    @staticmethod
    def quote_identifier(name: str) -> str:
        return f'`{name}`'

    def read_rows(
        self,
        table_name: str,
        _columns: Any,
        where: str | None = None,
        params: list[Any] | None = None,
    ) -> list[Row]:
        if table_name != 'mult':
            return []
        assert where is not None
        assert params is not None
        stored = self.rows.get(params[0], [])
        if '`value`=%s' in where:
            return [row for row in stored if _server_key(row[1]) == _server_key(params[1])]
        return stored

    def insert_rows(self, table_name: str, rows: list[dict[str, Any]]) -> None:
        assert table_name == 'mult'
        for row in rows:
            stored = self.rows.setdefault(row['field_id'], [])
            if any(
                held[0] == row['id'] or _server_key(held[1]) == _server_key(row['value'])
                for held in stored
            ):
                raise ImportDBError(f'Duplicate entry for {row}')
            stored.append(
                (row['id'], row['value'], row['label'], row['pin'], row['display'], row['grouping'])
            )

    def update_row(
        self, table_name: str, row: dict[str, Any], where: str, where_params: list[Any]
    ) -> None:
        self.updates.append((table_name, row, where_params))

    def upsert_rows(self, table_name: str, _key: str, rows: list[dict[str, Any]]) -> None:
        if rows:
            self.upserted.append(table_name)


def _context(rows: list[Row] | None = None, pinned_rows: list[Row] | None = None) -> ImportContext:
    """Return a context over a server holding `rows` and `pinned_rows` for the two fields."""
    ctx = make_context()
    ctx.args.suppress_mult_messages = True
    ctx.db = cast(ImportDBSuper, _Server({QUALITY: rows or [], KIND: pinned_rows or []}))
    ctx.mult_fields = {
        'obs_x.quality': MultFieldInfo(QUALITY, pinned=False),
        'obs_x.kind': MultFieldInfo(KIND, pinned=True),
    }
    return ctx


def _server(ctx: ImportContext) -> _Server:
    return cast(_Server, ctx.db)


def _errors(ctx: ImportContext) -> list[str]:
    return cast(RecordingLogger, ctx.logger).messages_at('error')


def _update(ctx: ImportContext, column: dict[str, Any], value: Any, label: Any, **kw: Any) -> Any:
    """Resolve one value of the stand-in table ``obs_x``."""
    return do_import_mult.update_mult_table(
        ctx, 'obs_x', column['field_name'], column, value, label, **kw
    )


def _warnings(ctx: ImportContext) -> list[str]:
    return cast(RecordingLogger, ctx.logger).messages_at('warning')


def test_a_new_value_takes_the_id_after_the_highest() -> None:
    """Ids count on from the field's highest, the first being one above it."""
    ctx = _context([(4, 'GOOD', 'Good', None, 'Y', None)])

    assert _update(ctx, COLUMN, 'POOR', 'Poor') == 5
    assert _update(ctx, COLUMN, 'FAIR', 'Fair') == 6
    assert _update(ctx, COLUMN, 'POOR', 'Poor') == 5


def test_the_first_value_of_an_empty_field_is_id_zero() -> None:
    """A field with no rows starts at 0, as the observation columns hold today."""
    assert _update(_context(), COLUMN, 'X', 'X') == 0


def test_a_value_differing_only_in_case_finds_the_stored_row() -> None:
    """The cache compares as the server's collation does, as the unique key would."""
    ctx = _context([(3, 'FAIR', 'Fair', None, 'Y', None)])

    assert _update(ctx, COLUMN, 'fair', 'Fair') == 3
    assert ctx.mult_table_cache['obs_x.quality'].new_rows == []


def test_none_is_stored_as_the_empty_string() -> None:
    """The absent value is ``''``, so a unique key deduplicates it."""
    ctx = _context([(0, '', 'N/A', None, 'Y', None)])

    assert _update(ctx, COLUMN, None, 'N/A') == 0
    assert _update(ctx, COLUMN, '', 'N/A') == 0


def test_a_different_label_keeps_the_stored_row_and_warns_once() -> None:
    """The stored presentation stays; the warning names the field, value and labels."""
    ctx = _context([(3, 'GOOD', 'Good', None, 'Y', None)])

    assert _update(ctx, COLUMN, 'GOOD', 'Excellent') == 3
    assert _update(ctx, COLUMN, 'GOOD', 'Excellent') == 3

    (message,) = _warnings(ctx)
    assert '"obs_x.quality"' in message
    assert '"GOOD"' in message
    assert '"Good"' in message
    assert '"Excellent"' in message
    assert 'mult_overrides' in message
    assert ctx.mult_table_cache['obs_x.quality'].rows[0]['label'] == 'Good'


@pytest.mark.parametrize(
    ('kw', 'differs'),
    [({'disp': 'N'}, True), ({'grouping': 'G'}, True), ({}, False)],
    ids=['display', 'grouping', 'same'],
)
def test_a_different_display_or_grouping_warns_too(kw: dict[str, Any], differs: bool) -> None:
    ctx = _context([(3, 'GOOD', 'Good', None, 'Y', None)])

    _update(ctx, COLUMN, 'GOOD', 'Good', **kw)

    assert bool(_warnings(ctx)) is differs


def test_a_value_its_column_overrides_does_not_warn() -> None:
    """A renamed value's stored label differs from the computed one on purpose."""
    column = {**COLUMN, 'mult_overrides': [{'value': 'good', 'label': 'Excellent'}]}
    ctx = _context([(3, 'GOOD', 'Excellent', None, 'Y', None)])

    assert _update(ctx, column, 'GOOD', 'Good') == 3
    assert _warnings(ctx) == []


def test_a_pinned_field_serves_its_list_and_never_warns() -> None:
    """A pinned field's presentation is its list, whatever the obs class computes."""
    ctx = _context()

    assert _update(ctx, PINNED, 'B', 'Something else') == 1
    assert _warnings(ctx) == []


def test_a_value_outside_a_pinned_list_is_an_error_and_gets_the_absent_value() -> None:
    """The bundle fails; under ``--ignore-errors`` the row holds the absent value's id."""
    ctx = _context()

    first = _update(ctx, PINNED, 'Z', 'Zed')
    second = _update(ctx, PINNED, 'Y', 'Why')

    assert first == second == PINNED_ABSENT_ID
    cache = ctx.mult_table_cache['obs_x.kind']
    assert cache.find('')['label'] == 'N/A'  # type: ignore[index]
    assert ctx.import_has_bad_data
    assert cast(RecordingLogger, ctx.logger).messages_at('error') == [
        'Unable to add value "Z" to preprogrammed mult field "obs_x.kind"',
        'Unable to add value "Y" to preprogrammed mult field "obs_x.kind"',
    ]


def test_a_value_outside_a_pinned_list_holding_the_absent_value_gets_its_id() -> None:
    column = {
        **PINNED,
        'mult_options': [*PINNED['mult_options'], [7, None, 'N/A', 30, 'Y', None, None]],
    }

    assert _update(_context(), column, 'Z', 'Zed') == 7


def test_an_id_above_the_type_s_maximum_is_refused_naming_the_field() -> None:
    """The import stops rather than write an id the column cannot hold."""
    ctx = _context([(MAX_MULT_ID, 'LAST', 'Last', None, 'Y', None)])
    _update(ctx, COLUMN, 'LAST', 'Last')

    with pytest.raises(MultIdOverflowError, match=r'"obs_x\.quality"'):
        _update(ctx, COLUMN, 'MORE', 'More')


def test_a_new_group_is_written_once_with_its_pin() -> None:
    """A group first met is added to ``mult_group``; one already there is not."""
    ctx = _context()

    _update(ctx, COLUMN, 'A', 'A', grouping='Saturn', group_pin=60)
    _update(ctx, COLUMN, 'B', 'B', grouping='saturn', group_pin=70)

    assert ctx.mult_table_cache['obs_x.quality'].group_rows == [
        {'field_id': 1, 'grouping': 'Saturn', 'group_pin': 60}
    ]


def test_a_lookup_finds_a_value_without_adding_it() -> None:
    ctx = _context([(3, 'FAIR', 'Fair', None, 'Y', None)])

    assert do_import_mult.mult_table_lookup_id(ctx, 'obs_x', 'quality', COLUMN, 'fair') == 3
    assert do_import_mult.mult_table_lookup_id(ctx, 'obs_x', 'quality', COLUMN, 'X') is None
    assert ctx.modified_mult_tables == set()


@pytest.mark.parametrize(
    ('kw', 'stored_group'),
    [({'pin': 3}, None), ({'grouping': 'G', 'group_pin': 2}, ('G', 1))],
    ids=['pin', 'group-pin'],
)
def test_a_different_pin_or_group_pin_warns(
    kw: dict[str, Any], stored_group: tuple[str, int] | None
) -> None:
    """The first bundle to store a value does not silently decide its pin."""
    grouping = None if stored_group is None else stored_group[0]
    ctx = _context([(3, 'GOOD', 'Good', None, 'Y', grouping)])
    cache = do_import_mult.read_or_create_mult_table(ctx, 'obs_x.quality', COLUMN)
    if stored_group is not None:
        cache.remember_group(*stored_group)

    _update(ctx, COLUMN, 'GOOD', 'Good', **kw)

    (message,) = _warnings(ctx)
    assert 'pin' in message


def test_a_value_the_cache_misses_but_the_server_holds_takes_the_server_s_id() -> None:
    """A value the key keeps apart from a stored one but the server's collation does not
    is asked of the server, so it is never given a second id the unique key refuses."""
    ctx = _context([(3, 'Ostra', 'Ostra', None, 'Y', None)])

    assert _update(ctx, COLUMN, 'Østra', 'Østra') == 3
    assert ctx.mult_table_cache['obs_x.quality'].new_rows == []


def test_a_new_row_is_inserted_and_never_rewrites_another_row() -> None:
    """Two new values the server calls equal make the insert fail, naming the field.

    Neither stored row's value changes: the write is a plain insert, so the collision
    the server's unique key finds stops the import rather than rewriting a row.
    """
    ctx = _context([(3, 'GOOD', 'Good', None, 'Y', None)])
    _update(ctx, COLUMN, 'Øk', 'Øk')
    _update(ctx, COLUMN, 'Ok', 'Ok')

    with pytest.raises(ImportDBError):
        do_import_mult.write_mult_tables(ctx)

    assert _server(ctx).upserted == []
    assert (
        cast(RecordingLogger, ctx.logger)
        .messages_at('fatal')[0]
        .startswith('Mult field "obs_x.quality": inserting the value(s) "Øk", "Ok" failed')
    )
    assert _server(ctx).rows[QUALITY][0] == (3, 'GOOD', 'Good', None, 'Y', None)


def test_new_rows_are_inserted_with_their_field() -> None:
    ctx = _context([(3, 'GOOD', 'Good', None, 'Y', None)])
    _update(ctx, COLUMN, 'POOR', 'Poor')

    do_import_mult.write_mult_tables(ctx)

    assert _server(ctx).rows[QUALITY][-1] == (4, 'POOR', 'Poor', None, 'Y', None)
    assert ctx.modified_mult_tables == set()


def test_a_pinned_field_s_cache_holds_what_the_server_holds() -> None:
    """A pinned field's stored rows are read, so its absent row is found, not re-added."""
    ctx = _context(pinned_rows=[(PINNED_ABSENT_ID, '', 'N/A', None, 'Y', None)])

    assert _update(ctx, PINNED, 'Z', 'Zed') == PINNED_ABSENT_ID
    cache = ctx.mult_table_cache['obs_x.kind']
    assert [row['id'] for row in cache.new_rows] == [0, 1]
    assert cache.max_id == 1


def test_a_list_entry_whose_id_is_stored_under_another_value_is_refused() -> None:
    """The stored row keeps its value and label; the disagreement is an error."""
    stored = (1, 'OLD', 'Old', 20, 'Y', None)
    ctx = _context(pinned_rows=[stored])

    cache = do_import_mult.read_or_create_mult_table(ctx, 'obs_x.kind', PINNED)

    assert cache.by_id[1]['value'] == 'OLD'
    assert cache.by_id[1]['label'] == 'Old'
    assert cache.updated_rows == []
    assert _errors(ctx) == [
        'mult_options of mult field "obs_x.kind" gives id 1 the value "B", but the field '
        'stores "OLD" under it; the stored row stays'
    ]


def test_a_list_entry_whose_value_is_stored_under_another_id_is_refused() -> None:
    ctx = _context(pinned_rows=[(PINNED_ABSENT_ID - 1, 'B', 'Beta', 20, 'Y', None)])

    cache = do_import_mult.read_or_create_mult_table(ctx, 'obs_x.kind', PINNED)

    assert 1 not in cache.by_id
    assert _errors(ctx) == [
        'mult_options of mult field "obs_x.kind" gives the value "B" id 1, but the field '
        f'stores it under id {PINNED_ABSENT_ID - 1}; the stored row stays'
    ]


def test_a_list_s_new_presentation_updates_only_the_presentation() -> None:
    """A stored row the list relabels is updated by id; its value is never written."""
    ctx = _context(
        pinned_rows=[(0, 'A', 'Old Alpha', 10, 'Y', None), (1, 'B', 'Beta', 20, 'Y', None)]
    )
    cache = do_import_mult.read_or_create_mult_table(ctx, 'obs_x.kind', PINNED)
    assert cache.new_rows == []

    do_import_mult.write_mult_tables(ctx)

    assert _server(ctx).updates == [
        (
            'mult',
            {'label': 'Alpha', 'pin': 10, 'display': 'Y', 'grouping': None},
            [KIND, 0],
        )
    ]
