"""Tests for the ``--update-mult-info`` step.

The step reads the packaged table schemas and writes to the database, so the database is
replaced by a recorder and the step is driven against the real schemas. That is the
point of the test rather than an accident of it: the fault it guards against was a
disagreement between the shape the schemas hold and the shape the step read out of them,
which a hand-written schema fixture could not have shown.
"""

from typing import Any

import pytest

from opus_import import import_util, mult_fields
from opus_import.context import ImportContext
from opus_import.mult_fields import MultFieldInfo
from opus_import.steps import do_update_mult_info

from .conftest import RecordingLogger, make_context


class _RecordingDatabase:
    """An `importdb` stand-in holding some fields' ids, recording every write."""

    def __init__(self, stored: dict[int, set[int]]) -> None:
        self._stored = stored
        self.updates: list[tuple[int, int, dict[str, Any]]] = []
        self.inserts: list[dict[str, Any]] = []
        self.group_upserts: list[dict[str, Any]] = []
        self.rank_reads: list[tuple[str, str | None, list[Any] | None]] = []

    def quote_identifier(self, name: str) -> str:
        return f'`{name}`'

    def read_rows(
        self,
        table_name: str,
        column_names: list[str],
        where: str | None = None,
        where_params: list[Any] | None = None,
    ) -> list[tuple[Any, ...]]:
        if table_name == 'mult' and list(column_names) == ['id']:
            assert where == '`field_id`=%s'
            assert where_params is not None
            return [(row_id,) for row_id in sorted(self._stored.get(where_params[0], set()))]
        self.rank_reads.append((table_name, where, where_params))
        return []

    def update_row(
        self,
        table_name: str,
        row: dict[str, Any],
        where: str,
        where_params: list[Any] | None = None,
    ) -> None:
        assert table_name == 'mult'
        assert where == '`field_id`=%s AND `id`=%s'
        assert where_params is not None
        self.updates.append((where_params[0], where_params[1], row))

    def insert_rows(self, table_name: str, rows: list[dict[str, Any]]) -> None:
        assert table_name == 'mult'
        self.inserts += rows

    def upsert_rows(self, table_name: str, key_name: str, rows: list[dict[str, Any]]) -> None:
        if table_name == 'mult_group':
            self.group_upserts += rows


def _field_ids() -> dict[str, MultFieldInfo]:
    """Return a numbering of every packaged mult field, as `ensure_mult_fields` makes."""
    return {
        name: MultFieldInfo(field_id, column.pinned)
        for field_id, (name, column) in enumerate(
            mult_fields.packaged_mult_columns().items(), start=1
        )
    }


def _run(stored: dict[str, set[int]]) -> tuple[_RecordingDatabase, RecordingLogger]:
    """Run the step with each named field holding the given ids."""
    fields = _field_ids()
    db = _RecordingDatabase({fields[name].field_id: ids for name, ids in stored.items()})
    logger = RecordingLogger()
    ctx: ImportContext = make_context(logger=logger, db=db)
    ctx.mult_fields = fields
    do_update_mult_info.update_mult_info(ctx)
    return db, logger


def _packaged_options(name: str) -> list[list[Any]]:
    """Return the ``mult_options`` the packaged schema pins for one field."""
    options: list[list[Any]] = mult_fields.packaged_mult_columns()[name].entry['mult_options']
    return options


def _all_ids(name: str) -> set[int]:
    """Return every id a pinned field's list gives."""
    return {option[0] for option in _packaged_options(name)}


def test_a_preprogrammed_field_is_updated_row_for_row() -> None:
    """Every packaged entry produces one update, keyed by the id the schema gives it.

    Driving it against the real ``obs_general.instrument_id`` options is what pins the
    step to the shape the schemas hold.
    """
    db, logger = _run({'obs_general.instrument_id': _all_ids('obs_general.instrument_id')})

    options = _packaged_options('obs_general.instrument_id')
    field_id = _field_ids()['obs_general.instrument_id'].field_id
    assert [(field, row_id) for field, row_id, _row in db.updates] == [
        (field_id, option[0]) for option in options
    ]
    assert db.inserts == []
    assert logger.messages_at('error') == []


def test_every_pinned_presentation_column_is_written() -> None:
    """A row carries the label, the pin, the display flag and the grouping.

    Indexed by position rather than through `MultOption`: decoding the expectation with
    the same NamedTuple the code under test decodes with would make this pass for any
    transposition inside it.
    """
    db, _logger = _run({'obs_general.instrument_id': _all_ids('obs_general.instrument_id')})

    by_id = {row_id: row for _field, row_id, row in db.updates}
    options = _packaged_options('obs_general.instrument_id')
    assert [o for o in options if o[5] is not None], 'no instrument_id value is grouped'
    for row_id, _value, label, pin, display, grouping, _group_pin in options:
        assert by_id[row_id] == {
            'label': str(label),
            'pin': pin,
            'display': display,
            'grouping': grouping,
        }


def test_each_group_s_pin_is_written_to_its_group() -> None:
    """The group pin of an entry goes to ``mult_group``, once per group."""
    db, _logger = _run({'obs_general.instrument_id': _all_ids('obs_general.instrument_id')})

    field_id = _field_ids()['obs_general.instrument_id'].field_id
    expected: dict[str, int | None] = {}
    for option in _packaged_options('obs_general.instrument_id'):
        if option[5] is not None:
            expected.setdefault(option[5], option[6])
    assert db.group_upserts == [
        {'field_id': field_id, 'grouping': grouping, 'group_pin': group_pin}
        for grouping, group_pin in expected.items()
    ]


def test_an_entry_with_no_row_is_inserted_with_its_value() -> None:
    """A value a release adds to a list in use is written, absent value as ``''``."""
    name = 'obs_profile.occ_type'
    options = _packaged_options(name)
    absent = next(option for option in options if option[1] is None)
    db, _logger = _run({name: _all_ids(name) - {absent[0]}})

    assert db.inserts == [
        {
            'field_id': _field_ids()[name].field_id,
            'id': absent[0],
            'value': '',
            'label': absent[2],
            'pin': absent[3],
            'display': absent[4],
            'grouping': absent[5],
        }
    ]


def test_a_pinned_field_the_schema_does_not_use_is_left_alone() -> None:
    """A field with no rows has no observation of this schema behind it."""
    db, _logger = _run({})

    assert db.updates == []
    assert db.inserts == []
    assert db.rank_reads == []


def test_the_fields_written_are_ranked_again_and_no_others() -> None:
    """Only the touched fields' values and groups are read for ranking."""
    db, _logger = _run({'obs_general.planet_id': _all_ids('obs_general.planet_id')})

    field_id = _field_ids()['obs_general.planet_id'].field_id
    assert db.rank_reads == [
        ('mult', '`field_id` IN (%s)', [field_id]),
        ('mult_group', '`field_id` IN (%s)', [field_id]),
    ]


def test_every_pinned_field_is_written_entry_for_entry() -> None:
    """No pinned field a real database would hold is missed or mis-read.

    Driven over every field the packaged schemas declare rather than over names chosen
    here, each holding every id its list gives, and compared by position.
    """
    columns = mult_fields.packaged_mult_columns()
    pinned = [name for name, column in columns.items() if column.pinned]
    db, logger = _run({name: _all_ids(name) for name in pinned})

    assert logger.messages_at('error') == []
    fields = _field_ids()
    expected = {}
    for name in pinned:
        for row_id, _value, label, pin, display, grouping, _gp in _packaged_options(name):
            expected[(fields[name].field_id, row_id)] = {
                'label': str(label),
                'pin': pin,
                'display': display,
                'grouping': grouping,
            }
    assert {(field, row_id): row for field, row_id, row in db.updates} == expected
    assert len(db.updates) == len(expected)


@pytest.mark.parametrize(
    'entry',
    [
        [0, 'COISS', 'Cassini ISS', 10, 'Y', None],
        [0, 'COISS', 'Cassini ISS', '010', 'Y', None, None],
        [0, 'COISS', 'Cassini ISS', 10, 'Y', 'Group', '010'],
        [0, 'COISS', 'Cassini ISS', True, 'Y', None, None],
    ],
    ids=['six values', 'a string pin', 'a string group pin', 'a boolean pin'],
)
def test_an_entry_of_the_wrong_shape_stops_the_step(
    monkeypatch: pytest.MonkeyPatch, entry: list[Any]
) -> None:
    """An entry that is not seven values, or whose order is not an integer, raises.

    Nothing is written before it raises: a row built from values that landed in the wrong
    columns, or an order read as text, is a fault in the schema.
    """
    column = mult_fields.MultColumn(
        'obs_general.instrument_id',
        'obs_general',
        {'field_name': 'instrument_id', 'mult_options': [entry]},
    )
    monkeypatch.setattr(
        mult_fields, 'packaged_mult_columns', lambda: {'obs_general.instrument_id': column}
    )
    db = _RecordingDatabase({1: {0}})
    ctx: ImportContext = make_context(logger=RecordingLogger(), db=db)
    ctx.mult_fields = {'obs_general.instrument_id': MultFieldInfo(1, pinned=True)}

    with pytest.raises(TypeError):
        do_update_mult_info.update_mult_info(ctx)
    assert db.updates == []
    assert db.inserts == []


def test_read_mult_option_names_the_seven_positions() -> None:
    """The reader returns the positions under their names."""
    option = import_util.read_mult_option([3, None, 'N/A', 40, 'Y', 'Group', 10])

    assert option == import_util.MultOption(3, None, 'N/A', 40, 'Y', 'Group', 10)
