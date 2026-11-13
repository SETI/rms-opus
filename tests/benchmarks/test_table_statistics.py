"""The per-table statistics `bench_db` records, the largest mult id of each field among them."""

from __future__ import annotations

from typing import Any

import pytest

from benchmarks import bench_db


def _answer(tables: dict[str, list[str]], statement: str, parameters: Any) -> list[tuple[Any, ...]]:
    """Answer one of `table_statistics`'s queries about a schema holding `tables`."""
    if 'information_schema.TABLES' in statement:
        return [(name, 100, 10) for name in tables]
    if 'information_schema.STATISTICS' in statement:
        return []
    if 'information_schema.COLUMNS' in statement:
        return [(name,) for name, columns in tables.items() if parameters[1] in columns]
    if statement.startswith('SELECT COUNT(*)'):
        return [(5,)]
    if '`qualified_name`, MAX(`m`.`id`)' in statement:
        return [('obs_general.planet_id', 8), ('obs_profile.host', 500)]
    if statement.startswith('SELECT MAX(id)'):
        return [(17,)]
    raise AssertionError(statement)


def _statistics(
    monkeypatch: pytest.MonkeyPatch, tables: dict[str, list[str]]
) -> dict[str, dict[str, int]]:
    monkeypatch.setattr(
        bench_db,
        'query',
        lambda _connection, statement, parameters=(): _answer(tables, statement, parameters),
    )
    return bench_db.table_statistics(None, 'schema')


def test_the_mult_table_records_the_largest_id_of_each_field(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Ids are numbered per field, so one maximum over every field would say nothing."""
    statistics = _statistics(
        monkeypatch,
        {
            'mult': ['field_id', 'id', 'value'],
            'mult_field': ['field_id', 'qualified_name'],
            'mult_group': ['field_id', 'grouping'],
        },
    )

    assert {key: value for key, value in statistics['mult'].items() if 'max_id' in key} == {
        'max_id.obs_general.planet_id': 8,
        'max_id.obs_profile.host': 500,
    }
    assert 'max_id' not in statistics['mult_field']
    assert 'max_id' not in statistics['mult_group']


def test_a_per_field_mult_table_records_its_largest_id(monkeypatch: pytest.MonkeyPatch) -> None:
    statistics = _statistics(monkeypatch, {'mult_obs_general_planet_id': ['id', 'value']})

    assert statistics['mult_obs_general_planet_id']['max_id'] == 17
