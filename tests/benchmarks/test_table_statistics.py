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


# --- preview_images: in obs_preview, or in obs_general on a schema without it -------------


def _previews(
    monkeypatch: pytest.MonkeyPatch, tables: dict[str, dict[str, int]]
) -> tuple[dict[str, Any] | None, list[str]]:
    """Return what `bench_db.preview_images` records for `tables`, and what it asked."""
    statements: list[str] = []

    def answer(_connection: Any, statement: str, _parameters: Any = ()) -> list[tuple[Any, ...]]:
        statements.append(statement)
        return [(640, 6400)]

    monkeypatch.setattr(bench_db, 'query', answer)
    return bench_db.preview_images(None, 'schema', tables), statements


def test_previews_are_read_from_obs_preview_where_the_schema_has_it(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Measured beside obs_general's data, which no longer holds the column."""
    previews, statements = _previews(
        monkeypatch, {'obs_general': {'data_bytes': 12800}, 'obs_preview': {'data_bytes': 9000}}
    )

    assert previews == {
        'table': 'obs_preview',
        'average_bytes': 640.0,
        'total_bytes': 6400.0,
        'ratio_to_obs_general_data': 0.5,
    }
    assert [statement.rsplit('FROM ', 1)[1] for statement in statements] == [
        '`schema`.`obs_preview`'
    ]


def test_previews_are_read_from_obs_general_on_a_schema_without_obs_preview(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A base side before the column moved holds it in obs_general."""
    previews, statements = _previews(monkeypatch, {'obs_general': {'data_bytes': 64000}})

    assert previews is not None
    assert previews['table'] == 'obs_general'
    assert previews['ratio_to_obs_general_data'] == 0.1
    assert [statement.rsplit('FROM ', 1)[1] for statement in statements] == [
        '`schema`.`obs_general`'
    ]


def test_a_schema_without_either_table_records_no_previews(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    previews, statements = _previews(monkeypatch, {'mult': {'data_bytes': 10}})

    assert previews is None
    assert statements == []
