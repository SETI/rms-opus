"""Tests for the ``--update-mult-info`` step.

The step reads the packaged table schemas and writes to the database, so the database is
replaced by a recorder and the step is driven against the real schemas. That is the
point of the test rather than an accident of it: the fault it guards against was a
disagreement between the shape the schemas hold and the shape the step read out of them,
which a hand-written schema fixture could not have shown.
"""

from typing import Any

import pytest

from opus_import import import_util
from opus_import.context import ImportContext
from opus_import.steps import do_update_mult_info

from .conftest import RecordingLogger, make_context


class _RecordingDatabase:
    """An `importdb` stand-in that records the updates the step issues."""

    def __init__(self, table_names: list[str]) -> None:
        self._table_names = table_names
        self.updates: list[tuple[str, dict[str, Any], list[Any]]] = []

    def table_names(self, namespace: str, prefix: str | None = None) -> list[str]:
        return [name for name in self._table_names
                if prefix is None or name.startswith(prefix)]

    def quote_identifier(self, name: str) -> str:
        return f'`{name}`'

    def update_row(self, namespace: str, raw_table_name: str, row: dict[str, Any],
                   where: str, where_params: list[Any] | None = None) -> None:
        assert namespace == 'perm'
        assert where == '`id`=%s'
        assert where_params is not None
        self.updates.append((raw_table_name, row, where_params))


def _run(table_names: list[str]) -> tuple[_RecordingDatabase, RecordingLogger]:
    """Run the step over `table_names` and return the recorder and the logger."""
    db = _RecordingDatabase(table_names)
    logger = RecordingLogger()
    ctx: ImportContext = make_context(logger=logger, db=db)
    do_update_mult_info.update_mult_info(ctx)
    return db, logger


def _packaged_options(table: str, column: str) -> list[list[Any]]:
    """Return the ``mult_options`` the packaged schema pins for one column."""
    schema = import_util.read_schema_for_table(make_context(), table)
    assert schema is not None
    for entry in schema:
        if entry['field_name'] == column:
            options: list[list[Any]] = entry['mult_options']
            return options
    raise AssertionError(f'no column {column} in {table}')


def test_a_preprogrammed_table_is_updated_row_for_row() -> None:
    """Every packaged entry produces one update, keyed by the id the schema gives it.

    This is the regression test for the fault that made ``--update-mult-info``
    unusable: the step unpacked six values out of entries that carry seven, so it
    raised before writing anything at all. Driving it against the real
    ``obs_general.instrument_id`` options is what pins the two shapes together.
    """
    db, logger = _run(['mult_obs_general_instrument_id'])

    options = _packaged_options('obs_general', 'instrument_id')
    assert len(db.updates) == len(options)
    assert [where[0] for _table, _row, where in db.updates] == [o[0] for o in options]
    assert {table for table, _row, _where in db.updates} == {
        'mult_obs_general_instrument_id'}
    assert logger.messages_at('error') == []


def test_every_pinned_presentation_column_is_written() -> None:
    """A row carries the label, the sort key, the display flag and the grouping pair.

    Writing only some of them would leave a schema edit half-applied, and the grouping
    pair is the half that used to be dropped: the packaged
    ``obs_general.instrument_id`` options put the ground-based telescopes in a named
    group, which is exactly what an update that stopped at ``display`` would lose.
    """
    db, _logger = _run(['mult_obs_general_instrument_id'])

    by_id = {where[0]: row for _table, row, where in db.updates}
    options = _packaged_options('obs_general', 'instrument_id')
    grouped = [o for o in options if o[5] is not None]
    assert grouped, 'the packaged schema no longer groups any instrument_id value'

    for option in options:
        expected = import_util.MultOption(*option)
        assert by_id[expected.id] == {
            'label': str(expected.label),
            'disp_order': expected.disp_order,
            'display': expected.display,
            'grouping': expected.grouping,
            'group_disp_order': expected.group_disp_order,
        }


def test_a_column_without_pinned_options_is_left_alone() -> None:
    """A mult table the import discovered is not overwritten from the schema."""
    db, logger = _run(['mult_obs_general_target_name'])

    assert db.updates == []
    assert logger.messages_at('error') == []


def test_an_unknown_mult_table_is_reported_and_the_rest_still_run() -> None:
    """One unmatchable table name does not stop the tables after it."""
    db, logger = _run(['mult_obs_nosuchtable_x', 'mult_obs_general_instrument_id'])

    assert db.updates, 'the second table was skipped along with the first'
    assert logger.messages_at('error') == [
        'Unable to find table schema for mult "mult_obs_nosuchtable_x"']


def test_an_unknown_column_is_reported() -> None:
    """A table whose schema exists but has no such column is named in the error."""
    _db, logger = _run(['mult_obs_general_nosuchcolumn'])

    assert logger.messages_at('error') == [
        'Unable to find field "nosuchcolumn" in table "mult_obs_general_nosuchcolumn"']


def test_an_entry_of_the_wrong_length_stops_the_step(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """A schema entry that is not seven values raises rather than writing a mangled row.

    An entry one value short would otherwise leave ``group_disp_order`` unset while
    every other value landed one column too far along, which is a fault in the schema
    rather than something the step can paper over. Nothing is written before it raises.
    """
    short_entry = [0, 'COISS', 'Cassini ISS', '010', 'Y', None]
    monkeypatch.setattr(
        import_util, 'read_schema_for_table',
        lambda ctx, name, replace=None: (
            [{'field_name': 'instrument_id', 'mult_options': [short_entry]}]
            if name == 'obs_general' else None))

    db = _RecordingDatabase(['mult_obs_general_instrument_id'])
    ctx: ImportContext = make_context(logger=RecordingLogger(), db=db)

    with pytest.raises(TypeError):
        do_update_mult_info.update_mult_info(ctx)
    assert db.updates == []
