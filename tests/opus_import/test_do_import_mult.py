"""How the import finds, adds and reports the values of a mult field.

A stand-in database holds each field's stored rows and its id counter, so the cache, the
conflict warning, the refusal of a value outside a pinned list, the counter and the id
ceiling are driven without a server. The field ids are given, as registration would have
numbered them, and a pinned field's rows are stored, as registration would have written
them.
"""

from __future__ import annotations

import contextlib
from collections.abc import Callable, Iterator
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
    """A stand-in database holding each field's ``mult`` rows and counter, with its keys.

    It answers the cache's read of a field and its probe of one value, compares values
    as `_server_key` does, keeps each field's ``last_id`` counter, and records every
    write; an insert whose value or id the field holds fails as a duplicate key would.

    Attributes:
        rows: Each field's stored rows.
        last_id: Each field's counter, which starts at its highest stored id but the
            reserved absent one, as registration and the imports before leave it.
        groups: The ``mult_group`` rows written.
        updates: The ``update_row`` calls made.
        before_insert: Called with the row before each insert, to stand for another
            process writing first.
        insert_error: An error every insert raises instead, or None.
    """

    def __init__(self, rows: dict[int, list[Row]]) -> None:
        self.rows = {field_id: list(stored) for field_id, stored in rows.items()}
        self.last_id = {
            field_id: max((row[0] for row in stored if row[0] != PINNED_ABSENT_ID), default=-1)
            for field_id, stored in self.rows.items()
        }
        self.groups: list[dict[str, Any]] = []
        self.updates: list[tuple[str, dict[str, Any], list[Any]]] = []
        self.before_insert: Callable[[dict[str, Any]], None] | None = None
        self.retried: list[tuple[str, Any]] = []
        self.insert_error: ImportDBError | None = None

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

    def retrying(self, description: str, body: Callable[[], Any], expected: Any = None) -> Any:
        self.retried.append((description, expected))
        return body()

    def increment_counter(self, table_name: str, column: str, key_column: str, key: Any) -> int:
        assert (table_name, column, key_column) == ('mult_field', 'last_id', 'field_id')
        self.last_id[key] = self.last_id.get(key, -1) + 1
        return self.last_id[key]

    @contextlib.contextmanager
    def failures_expected(self) -> Iterator[None]:
        yield

    @staticmethod
    def is_duplicate_key_error(exc: BaseException) -> bool:
        return 'Duplicate' in str(exc)

    def insert_row(self, table_name: str, row: dict[str, Any]) -> None:
        assert table_name == 'mult'
        if self.before_insert is not None:
            self.before_insert(row)
        if self.insert_error is not None:
            raise self.insert_error
        stored = self.rows.setdefault(row['field_id'], [])
        if any(
            held[0] == row['id'] or _server_key(held[1]) == _server_key(row['value'])
            for held in stored
        ):
            raise ImportDBError(f'Duplicate entry for {row}')
        stored.append(
            (row['id'], row['value'], row['label'], row['pin'], row['display'], row['grouping'])
        )

    def insert_rows_keeping_existing(
        self, table_name: str, key_name: str, rows: list[dict[str, Any]]
    ) -> None:
        assert (table_name, key_name) == ('mult_group', 'field_id')
        self.groups += rows


#: The rows registration writes for `PINNED`.
PINNED_ROWS: list[Row] = [(0, 'A', 'Alpha', 10, 'Y', None), (1, 'B', 'Beta', 20, 'Y', None)]


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


def test_a_new_value_takes_the_counter_s_next_id() -> None:
    """Ids count on from the field's counter, the first being one above the highest."""
    ctx = _context([(4, 'GOOD', 'Good', None, 'Y', None)])

    assert _update(ctx, COLUMN, 'POOR', 'Poor') == 5
    assert _update(ctx, COLUMN, 'FAIR', 'Fair') == 6
    assert _update(ctx, COLUMN, 'POOR', 'Poor') == 5
    assert _server(ctx).last_id[QUALITY] == 6


def test_the_first_value_of_an_empty_field_is_id_zero() -> None:
    """A field with no rows starts at 0, as the observation columns hold today."""
    assert _update(_context(), COLUMN, 'X', 'X') == 0


def test_a_new_value_is_written_the_moment_it_is_met() -> None:
    """The row is inserted with its field and id before the call returns."""
    ctx = _context([(3, 'GOOD', 'Good', None, 'Y', None)])

    _update(ctx, COLUMN, 'POOR', 'Poor')

    assert _server(ctx).rows[QUALITY][-1] == (4, 'POOR', 'Poor', None, 'Y', None)


def test_a_value_another_process_stored_first_takes_its_id_and_leaves_a_gap() -> None:
    """The insert meets the unique key; the stored row's id is read back and used."""
    ctx = _context([(3, 'GOOD', 'Good', None, 'Y', None)])
    server = _server(ctx)

    def other_process_first(row: dict[str, Any]) -> None:
        server.before_insert = None
        server.insert_row('mult', {**row, 'id': 9})

    server.before_insert = other_process_first

    assert _update(ctx, COLUMN, 'POOR', 'Poor') == 9
    assert _update(ctx, COLUMN, 'POOR', 'Poor') == 9
    assert [row[0] for row in server.rows[QUALITY]] == [3, 9]
    assert server.last_id[QUALITY] == 4
    assert cast(RecordingLogger, ctx.logger).messages_at('fatal') == []


def test_an_insert_that_fails_otherwise_stops_the_import_naming_the_field() -> None:
    """A failure that is not a duplicate key is fatal and raised."""
    ctx = _context()
    _server(ctx).insert_error = ImportDBError('Data too long for column')

    with pytest.raises(ImportDBError):
        _update(ctx, COLUMN, 'X', 'X')

    (message,) = cast(RecordingLogger, ctx.logger).messages_at('fatal')
    assert message.startswith('Mult field "obs_x.quality": inserting the value "X" under id 0')


def test_a_value_differing_only_in_case_finds_the_stored_row() -> None:
    """The cache compares as the server's collation does, as the unique key would."""
    ctx = _context([(3, 'FAIR', 'Fair', None, 'Y', None)])

    assert _update(ctx, COLUMN, 'fair', 'Fair') == 3
    assert len(_server(ctx).rows[QUALITY]) == 1
    assert _server(ctx).last_id[QUALITY] == 3


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


def test_a_pinned_field_serves_its_registered_rows_and_never_warns() -> None:
    """A pinned field's presentation is its list, whatever the obs class computes."""
    ctx = _context(pinned_rows=PINNED_ROWS)

    assert _update(ctx, PINNED, 'B', 'Something else') == 1
    assert _warnings(ctx) == []
    assert _server(ctx).rows[KIND] == PINNED_ROWS


def test_a_value_outside_a_pinned_list_is_an_error_and_gets_the_absent_value() -> None:
    """The bundle fails; under ``--ignore-errors`` the row holds the absent value's id."""
    ctx = _context(pinned_rows=PINNED_ROWS)

    first = _update(ctx, PINNED, 'Z', 'Zed')
    second = _update(ctx, PINNED, 'Y', 'Why')

    assert first == second == PINNED_ABSENT_ID
    assert _server(ctx).rows[KIND][-1] == (PINNED_ABSENT_ID, '', 'N/A', None, 'Y', None)
    assert _server(ctx).last_id[KIND] == 1
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
    ctx = _context(pinned_rows=[*PINNED_ROWS, (7, '', 'N/A', 30, 'Y', None)])

    assert _update(ctx, column, 'Z', 'Zed') == 7


def test_an_id_above_the_type_s_maximum_is_refused_naming_the_field() -> None:
    """The import stops rather than write an id the column cannot hold."""
    ctx = _context([(MAX_MULT_ID, 'LAST', 'Last', None, 'Y', None)])
    # The field is not pinned, so its counter reached the largest id handing it out.
    _server(ctx).last_id[QUALITY] = MAX_MULT_ID
    _update(ctx, COLUMN, 'LAST', 'Last')

    with pytest.raises(MultIdOverflowError, match=r'"obs_x\.quality"'):
        _update(ctx, COLUMN, 'MORE', 'More')


def test_a_new_group_is_written_once_with_its_pin() -> None:
    """A group first met is added to ``mult_group``; one already there is not."""
    ctx = _context()

    _update(ctx, COLUMN, 'A', 'A', grouping='Saturn', group_pin=60)
    _update(ctx, COLUMN, 'B', 'B', grouping='saturn', group_pin=70)

    assert _server(ctx).groups == [{'field_id': 1, 'grouping': 'Saturn', 'group_pin': 60}]


def test_a_lookup_finds_a_value_without_adding_it() -> None:
    ctx = _context([(3, 'FAIR', 'Fair', None, 'Y', None)])

    assert do_import_mult.mult_table_lookup_id(ctx, 'obs_x', 'quality', COLUMN, 'fair') == 3
    assert do_import_mult.mult_table_lookup_id(ctx, 'obs_x', 'quality', COLUMN, 'X') is None
    assert len(_server(ctx).rows[QUALITY]) == 1
    assert _server(ctx).last_id[QUALITY] == 3


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
    cache = do_import_mult.read_mult_field(ctx, 'obs_x.quality', COLUMN)
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
    assert len(_server(ctx).rows[QUALITY]) == 1
    assert _server(ctx).last_id[QUALITY] == 3


def _pinned_cache(stored: list[Row]) -> do_import_mult.MultFieldCache:
    """Return the pinned field's cache holding `stored`, as registration reads it."""
    cache = do_import_mult.MultFieldCache('obs_x.kind', KIND, pinned=True)
    for row in stored:
        cache.remember(dict(zip(do_import_mult.MULT_ROW_COLUMNS, row, strict=True)))
    return cache


def test_laying_a_list_over_an_empty_field_adds_every_entry() -> None:
    """Registration inserts the list's rows a field lacks, in the list's order."""
    ctx = _context()

    changes = do_import_mult.lay_options_over(ctx, _pinned_cache([]), PINNED)

    assert [row['id'] for row in changes.new_rows] == [0, 1]
    assert changes.updated_rows == []


def test_a_list_entry_whose_id_is_stored_under_another_value_is_refused() -> None:
    """The stored row keeps its value and label; the disagreement is an error."""
    ctx = _context()
    cache = _pinned_cache([(1, 'OLD', 'Old', 20, 'Y', None)])

    changes = do_import_mult.lay_options_over(ctx, cache, PINNED)

    assert cache.by_id[1]['value'] == 'OLD'
    assert cache.by_id[1]['label'] == 'Old'
    assert changes.updated_rows == []
    assert _errors(ctx) == [
        'mult_options of mult field "obs_x.kind" gives id 1 the value "B", but the field '
        'stores "OLD" under it; the stored row stays'
    ]


def test_a_list_entry_whose_value_is_stored_under_another_id_is_refused() -> None:
    ctx = _context()
    cache = _pinned_cache([(PINNED_ABSENT_ID - 1, 'B', 'Beta', 20, 'Y', None)])

    changes = do_import_mult.lay_options_over(ctx, cache, PINNED)

    assert 1 not in cache.by_id
    assert [row['id'] for row in changes.new_rows] == [0]
    assert _errors(ctx) == [
        'mult_options of mult field "obs_x.kind" gives the value "B" id 1, but the field '
        f'stores it under id {PINNED_ABSENT_ID - 1}; the stored row stays'
    ]


def test_a_list_s_new_presentation_updates_only_the_presentation() -> None:
    """A stored row the list relabels is to be updated by id; its value is never written."""
    ctx = _context()
    cache = _pinned_cache([(0, 'A', 'Old Alpha', 10, 'Y', None), (1, 'B', 'Beta', 20, 'Y', None)])

    changes = do_import_mult.lay_options_over(ctx, cache, PINNED)

    assert changes.new_rows == []
    assert changes.updated_rows == [
        {'id': 0, 'value': 'A', 'label': 'Alpha', 'pin': 10, 'display': 'Y', 'grouping': None}
    ]


def test_the_id_the_value_and_its_group_are_each_written_in_a_retried_transaction() -> None:
    """A deadlock on any of the three writes runs that write again; a duplicate key on the
    value's insert is expected, and read back rather than retried."""
    ctx = _context()
    server = _server(ctx)

    _update(ctx, COLUMN, 'A', 'A', grouping='Saturn', group_pin=60)

    assert [description for description, _expected in server.retried] == [
        'Taking an id in mult field "obs_x.quality"',
        'Inserting a value into mult field "obs_x.quality"',
        'Inserting a group into mult field "obs_x.quality"',
    ]
    insert_expected = server.retried[1][1]
    assert insert_expected is not None
    assert insert_expected(ImportDBError('Duplicate entry'))
