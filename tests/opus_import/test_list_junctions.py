"""The junction tables of the ``mult_list`` columns, and the mult step's reading of them."""

from __future__ import annotations

from typing import Any

import pytest

from opus_import import list_junctions
from opus_import.steps import do_finalize_mult

from .conftest import make_context


def test_a_junction_table_is_named_for_its_table_and_column() -> None:
    """``obs_general.target_name``'s junction table is ``obs_general_target_name``."""
    assert list_junctions.junction_table('obs_general', 'target_name') == 'obs_general_target_name'


def test_the_list_columns_of_a_schema_are_its_mult_list_columns_in_order() -> None:
    """Table-level entries and the other column types are left out."""
    schema: list[dict[str, Any]] = [
        {'field_name': 'target_class', 'field_type': 'mult_list'},
        {'field_name': 'planet_id', 'field_type': 'mult_idx'},
        {'key': ['planet_id']},
        {'field_name': 'target_name', 'field_type': 'mult_list'},
    ]
    assert list_junctions.list_columns(schema) == ['target_class', 'target_name']


@pytest.mark.parametrize(
    ('stored', 'expected'),
    [
        (None, []),
        ('[]', []),
        ('[7]', [7]),
        ('[9, 4, 9, 2, 4]', [9, 4, 2]),
    ],
)
def test_a_stored_list_gives_each_id_once_in_list_order(stored: Any, expected: list[int]) -> None:
    """NULL is an empty list, and a repeated id is kept at its first place."""
    assert list_junctions.stored_ids(stored) == expected


def test_an_observations_list_gives_one_junction_row_per_distinct_id() -> None:
    """Each row names the id and the observation."""
    assert list_junctions.junction_rows(12, '[3, 5, 3]') == [
        {'mult_id': 3, 'obs_general_id': 12},
        {'mult_id': 5, 'obs_general_id': 12},
    ]


def test_the_junctions_name_each_table_with_list_columns() -> None:
    """A table without a ``mult_list`` column has no entry."""
    schemas = {
        'obs_general': [
            {'field_name': 'target_name', 'field_type': 'mult_list'},
            {'field_name': 'target_class', 'field_type': 'mult_list'},
        ],
        'obs_pds': [{'field_name': 'note', 'field_type': 'text'}],
    }
    assert list_junctions.junctions(schemas) == {'obs_general': ['target_name', 'target_class']}


class _ReferencesDB:
    """A stand-in answering the mult step's reads of the ids in use."""

    def __init__(self) -> None:
        """Hold the statements read."""
        self.selects: list[str] = []
        self.streams: list[str] = []

    def quote_identifier(self, name: str) -> str:
        """Backtick-quote a name."""
        return f'`{name}`'

    def table_names(self, prefix: str) -> list[str]:
        """Return obs_general and its junction tables."""
        assert prefix == 'obs_'
        return ['obs_general', 'obs_general_target_class', 'obs_general_target_name']

    def general_select(self, cmd: str, params: Any = None) -> list[tuple[int]]:
        """Answer the distinct ids of a junction table."""
        self.selects.append(cmd)
        if cmd == 'DISTINCT `mult_id` FROM `obs_general_target_name`':
            return [(3,), (8,)]
        if cmd == 'DISTINCT `mult_id` FROM `obs_general_target_class`':
            return [(1,)]
        raise AssertionError(cmd)

    def stream_select(self, cmd: str) -> list[tuple[Any, ...]]:
        """Answer the scan of obs_general's other mult columns with one row of ids."""
        self.streams.append(cmd)
        columns = cmd.split(' FROM ')[0].split(',')
        return [tuple(index + 1 for index in range(len(columns)))]


def test_the_list_columns_ids_in_use_are_read_from_their_junction_tables() -> None:
    """The mult step reads a list column's ids from its junction table, and scans
    obs_general for its other mult columns alone."""
    db = _ReferencesDB()
    used = do_finalize_mult.referenced_mult_ids(make_context(db=db))
    assert used['obs_general.target_name'] == {3, 8}
    assert used['obs_general.target_class'] == {1}
    assert len(db.streams) == 1
    assert db.streams[0].endswith(' FROM `obs_general`')
    assert '`target_name`' not in db.streams[0]
    assert '`target_class`' not in db.streams[0]
    assert '`instrument_id`' in db.streams[0]
