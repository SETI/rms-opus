"""The junction tables that index the ``mult_list`` columns.

A ``mult_list`` column holds a JSON list of mult ids, since one observation can have
several values of its field (several intended targets, say). Each such column has a
junction table, named ``<table>_<column>`` (`junction_table`), with one row
``(mult_id, obs_general_id)`` for each distinct id in each observation's list. Its primary
key is ``(mult_id, obs_general_id)``, so the observations holding a value are one range of
it, and a plain key on ``obs_general_id`` lets the per-bundle steps reach a bundle's rows
by joining ``obs_general``. The JSON column stays, for the pages that show the list.

The import writes a junction table's rows beside its observation table's row, from the
same resolved ids (`junction_rows`), and creates each junction table from a schema file
of its own, as it creates every other table. The web application searches a list column
with a semi-join on its junction table and counts its values by grouping the junction
table's rows.

This module is imported by the import and by the web application, so it imports nothing
from Django and nothing that needs a configuration file.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

#: The ``field_type`` of a column holding a JSON list of mult ids.
LIST_FIELD_TYPE = 'mult_list'

#: A junction table's column holding one id of an observation's list.
JUNCTION_MULT_COLUMN = 'mult_id'

#: A junction table's column naming the observation, by its ``obs_general`` row.
JUNCTION_OBSERVATION_COLUMN = 'obs_general_id'


def junction_table(table: str, column: str) -> str:
    """Return the name of the junction table of one ``mult_list`` column.

    Parameters:
        table: The table holding the column.
        column: The column.

    Returns:
        ``<table>_<column>``, such as ``obs_general_target_name``.
    """
    return f'{table}_{column}'


def list_columns(schema: Sequence[Mapping[str, Any]]) -> list[str]:
    """Return the ``mult_list`` columns of a table schema, in schema order.

    Parameters:
        schema: The table schema.

    Returns:
        The names of the columns whose ``field_type`` is `LIST_FIELD_TYPE`.
    """
    return [
        entry['field_name']
        for entry in schema
        if 'field_name' in entry and entry.get('field_type') == LIST_FIELD_TYPE
    ]


def stored_ids(stored: Any) -> list[int]:
    """Return the distinct ids of a ``mult_list`` column's stored value, in list order.

    Parameters:
        stored: The column's value: a JSON array of ids, or None for an empty list.

    Returns:
        Each id once, in the order of its first place in the list; none for None.
    """
    if stored is None:
        return []
    return list(dict.fromkeys(int(mult_id) for mult_id in json.loads(stored)))


def junction_rows(observation_id: int, stored: Any) -> list[dict[str, int]]:
    """Return the junction table rows of one observation's ``mult_list`` value.

    A list that repeats an id gives one row for it.

    Parameters:
        observation_id: The observation's ``obs_general`` id.
        stored: The column's value, as `stored_ids` reads it.

    Returns:
        One row per distinct id, each holding `JUNCTION_MULT_COLUMN` and
        `JUNCTION_OBSERVATION_COLUMN`.
    """
    return [
        {JUNCTION_MULT_COLUMN: mult_id, JUNCTION_OBSERVATION_COLUMN: observation_id}
        for mult_id in stored_ids(stored)
    ]


def junctions(table_schemas: Mapping[str, Sequence[Mapping[str, Any]]]) -> dict[str, list[str]]:
    """Return the ``mult_list`` columns of each table that has any.

    Parameters:
        table_schemas: Table schemas keyed by table name.

    Returns:
        For each table with a ``mult_list`` column, those columns in schema order, in the
        order of `table_schemas`.
    """
    found: dict[str, list[str]] = {}
    for table, schema in table_schemas.items():
        columns = list_columns(schema)
        if columns:
            found[table] = columns
    return found
