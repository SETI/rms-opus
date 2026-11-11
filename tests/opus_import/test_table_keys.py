"""Which keys a fresh import creates with each table, and which finalization adds.

Every packaged schema is read: for an observation or mult table the keys created with
the table and the keys finalization adds must partition what the schema declares, and
the first set must hold every key the per-bundle delete reads, or each bundle's delete
would scan its tables whole.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from opus_import import import_util, table_keys
from opus_import.table_keys import TableKey

#: Where the packaged table schemas are.
TABLE_SCHEMA_DIR = Path(str(import_util.TABLE_SCHEMA_DIR))

#: Every packaged table schema.
_SCHEMAS = sorted(TABLE_SCHEMA_DIR.glob('*.json'))

#: The ones whose tables a fresh import creates with only the keys a load needs. The
#: surface geometry template stands for every per-target table, and the mult template for
#: every mult table.
_FILTERED = [
    path for path in _SCHEMAS if path.stem.startswith('obs_') or path.stem == 'mult_template'
]


def _table_name(path: Path) -> str:
    """Return the table a schema file describes, naming the templates as their tables.

    Parameters:
        path: The schema file.

    Returns:
        The raw table name.
    """
    if path.stem == 'mult_template':
        return 'mult_obs_general_planet_id'
    if path.stem == 'obs_surface_geometry_target':
        return 'obs_surface_geometry__titan'
    return path.stem


def _schema(path: Path) -> list[dict[str, object]]:
    """Return a schema file's entries.

    Parameters:
        path: The schema file.

    Returns:
        Its JSON list.
    """
    schema: list[dict[str, object]] = json.loads(path.read_text(encoding='utf-8'))
    return schema


def test_every_observation_schema_is_among_the_filtered_ones() -> None:
    """The observation schemas this suite reads are the ones the filter selects."""
    assert len(_FILTERED) > 1
    assert all(table_keys.is_key_filtered_table(_table_name(path)) for path in _FILTERED)


@pytest.mark.parametrize('path', _FILTERED, ids=lambda path: path.stem)
def test_the_two_key_sets_partition_what_the_schema_declares(path: Path) -> None:
    """Every declared key is created with the table or added by finalization, never both.

    Finalization also adds one key the schema does not declare: a plain key on
    ``obs_general_id`` for each child, whose only declaration of that column is its
    foreign key. No other undeclared key appears.
    """
    table = _table_name(path)
    schema = _schema(path)
    declared = table_keys.declared_keys(schema)
    kept = table_keys.create_time_keys(table, schema)
    added = table_keys.add_secondary_indexes(table, schema)
    child = TableKey('foreign', ('obs_general_id',), ('obs_general', ('id',))) in declared
    supporting = {TableKey('key', ('obs_general_id',))} if child else set()
    assert set(kept).isdisjoint(added)
    assert set(kept) | set(declared) == set(declared)
    assert set(added) - set(declared) == supporting
    assert set(kept) | set(added) == set(declared) | supporting


@pytest.mark.parametrize('path', _FILTERED, ids=lambda path: path.stem)
def test_the_table_is_created_with_the_keys_the_delete_reads(path: Path) -> None:
    """An observation table has a ``bundle_id`` key, and keeps it and its primary and unique keys."""
    table = _table_name(path)
    schema = _schema(path)
    kept = table_keys.create_time_keys(table, schema)
    declared = table_keys.declared_keys(schema)
    if table.startswith('obs_'):
        assert TableKey('key', ('bundle_id',)) in kept
    for key in declared:
        if key.kind in ('primary', 'unique') or key == TableKey('key', ('bundle_id',)):
            assert key in kept
    assert all(key.kind != 'foreign' for key in kept)


@pytest.mark.parametrize('path', _FILTERED, ids=lambda path: path.stem)
def test_foreign_keys_come_after_the_plain_keys_they_rely_on(path: Path) -> None:
    """Finalization's list ends with the foreign keys, each column led by a plain key first."""
    table = _table_name(path)
    schema = _schema(path)
    added = table_keys.add_secondary_indexes(table, schema)
    kinds = [key.kind for key in added]
    assert kinds == sorted(kinds, key=lambda kind: kind == 'foreign')
    kept = table_keys.create_time_keys(table, schema)
    led = {key.columns[0] for key in [*kept, *added] if key.kind != 'foreign'}
    assert all(key.columns[0] in led for key in added if key.kind == 'foreign')


def test_obs_general_keeps_only_its_primary_key_and_bundle_key() -> None:
    """``opus_id`` is a plain key now, so it waits for finalization like the others."""
    schema = _schema(TABLE_SCHEMA_DIR / 'obs_general.json')
    assert table_keys.create_time_keys('obs_general', schema) == [
        TableKey('primary', ('id',)),
        TableKey('key', ('bundle_id',)),
    ]
    assert TableKey('key', ('opus_id',)) in table_keys.add_secondary_indexes('obs_general', schema)


def test_a_child_gains_its_foreign_key_on_obs_general_id_and_none_on_opus_id() -> None:
    """A child references ``obs_general`` by id only, through a key built before it."""
    schema = _schema(TABLE_SCHEMA_DIR / 'obs_pds.json')
    added = table_keys.add_secondary_indexes('obs_pds', schema)
    assert TableKey('key', ('obs_general_id',)) in added
    assert TableKey('foreign', ('obs_general_id',), ('obs_general', ('id',))) in added
    assert [key for key in added if key.kind == 'foreign'] == [
        TableKey('foreign', ('obs_general_id',), ('obs_general', ('id',)))
    ]


@pytest.mark.parametrize(
    'table', ['param_info', 'cart', 'definitions', 'contexts', 'search_results', 'user_searches']
)
def test_any_other_table_is_created_with_every_key_it_declares(table: str) -> None:
    """Outside the observation and mult tables nothing waits for finalization."""
    schema = _schema(TABLE_SCHEMA_DIR / f'{table}.json')
    assert table_keys.create_time_keys(table, schema) == table_keys.declared_keys(schema)
    assert table_keys.add_secondary_indexes(table, schema) == []


def test_keys_compare_by_kind_and_columns_not_name() -> None:
    """Two keys on the same columns are one key; a different kind or order is another."""
    assert TableKey('key', ('a', 'b')) == TableKey('key', ('a', 'b'))
    assert TableKey('key', ('a', 'b')) != TableKey('key', ('b', 'a'))
    assert TableKey('key', ('a',)) != TableKey('unique', ('a',))


@pytest.mark.parametrize(
    ('entry', 'message'),
    [
        ({'field_name': 'x', 'field_key': 'sideways'}, "unknown field_key 'sideways'"),
        ({'field_name': 'x', 'field_key': 'foreign'}, 'names its table and column'),
        ({'primary_key': []}, 'lists its columns by name'),
        ({'unique': 'a'}, 'lists its columns by name'),
        ({'unique': ['a', 1]}, 'lists its columns by name'),
    ],
    ids=[
        'unknown-kind',
        'foreign-without-target',
        'primary-without-columns',
        'unique-not-a-list',
        'unique-not-names',
    ],
)
def test_a_key_the_schema_cannot_declare_is_refused(entry: dict[str, object], message: str) -> None:
    """A malformed key is an error rather than a key silently left out."""
    with pytest.raises(ValueError, match=message):
        table_keys.declared_keys([entry])


def test_a_table_level_key_lists_its_columns_in_order() -> None:
    """``search_results`` keys a search's rows by position and by observation."""
    schema = _schema(TABLE_SCHEMA_DIR / 'search_results.json')
    assert table_keys.declared_keys(schema) == [
        TableKey('primary', ('search_id', 'sort_order')),
        TableKey('unique', ('search_id', 'obs_general_id')),
    ]


def test_describe_names_the_kind_and_columns() -> None:
    """The log's form of a key."""
    assert TableKey('key', ('time1', 'time2')).describe() == 'KEY (time1, time2)'
    assert TableKey('unique', ('a',)).describe() == 'UNIQUE KEY (a)'
    assert TableKey('primary', ('id',)).describe() == 'PRIMARY KEY (id)'
    assert (
        TableKey('foreign', ('obs_general_id',), ('obs_general', ('id',))).describe()
        == 'FOREIGN KEY (obs_general_id) REFERENCES obs_general (id)'
    )
