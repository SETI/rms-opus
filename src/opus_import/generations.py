"""Import generations: the rows of ``obs_general`` a schema serves, and the ones it hides.

An incremental update writes the bundles it changes into the served schema as a new
**generation**, which no request sees until it is switched in whole
(`opus_import.steps.do_generation`). The observation rows live in the base table
``obs_general_rows``, each carrying the generation that added it, ``added_generation``,
and the one that retired it, ``removed_generation`` (NULL while no generation has). A row
is **in generation G** when ``added_generation <= G`` and ``removed_generation`` is NULL
or greater than G.

``obs_general`` is a view of the rows in the generation the schema serves, the
``generation`` column of its one ``schema_version`` row. MySQL merges the view into each
query that names it, so the web application reads ``obs_general`` as a table and cannot
miss the test. The child tables carry no generation: a request reaches a child row only
through an ``obs_general`` id.

The import reads and writes the base table. `opus_import.importdb` translates the name
``obs_general`` to ``obs_general_rows`` wherever it renders a table name
(`physical_table_name`), so every statement the import builds names the base table, and
it reports the base table under the name ``obs_general``.

This module is imported by the import and by the database layer, so it imports nothing
from Django and nothing that needs a configuration file.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from importlib.resources import files
from typing import Any

from opus_import.schema_version import SCHEMA_VERSION_TABLE

#: The view of the served generation's observations, the name every reader uses.
OBS_GENERAL_VIEW = 'obs_general'

#: The base table holding every generation's observation rows.
OBS_GENERAL_ROWS = 'obs_general_rows'

#: The column naming the generation that added a row.
ADDED_GENERATION_COLUMN = 'added_generation'

#: The column naming the generation that retired a row; NULL while none has.
REMOVED_GENERATION_COLUMN = 'removed_generation'

#: The base table's columns the view leaves out.
GENERATION_COLUMNS = (ADDED_GENERATION_COLUMN, REMOVED_GENERATION_COLUMN)

#: The ``data_source`` of the generation columns in ``obs_general.json``: the import
#: computes no value for them per row, and the loader writes the generation it imports.
GENERATION_DATA_SOURCE = 'GENERATION'

#: The generation a fresh import writes, and the one its version row serves.
FIRST_GENERATION = 1

#: ``schema_version``'s column naming the generation the web application serves.
SERVED_GENERATION_COLUMN = 'generation'

#: ``schema_version``'s column naming the generation an update is writing, or NULL.
PENDING_GENERATION_COLUMN = 'pending_generation'

#: ``schema_version``'s column saying how far the pending generation has got, or NULL.
PENDING_STATE_COLUMN = 'pending_state'

#: ``schema_version``'s column that is true from a switch until the purge starts.
REVERTIBLE_COLUMN = 'revertible'

#: The pending generation is being written, or was written after its last stamp.
PENDING_WRITING = 'writing'

#: Every step of ``--finalize`` succeeded on the pending generation.
PENDING_FINALIZED = 'finalized'

#: ``--validate`` passed on the finalized pending generation.
PENDING_VALIDATED = 'validated'

#: ``--write-schema-version`` stamped the validated pending generation; it may be switched.
PENDING_READY = 'ready'

#: ``import_bundle``'s column naming the generation that imported a bundle's copy.
REGISTRY_GENERATION_COLUMN = 'generation'

#: ``import_bundle``'s column naming the generation that retired a bundle's copy, or NULL.
RETIRED_GENERATION_COLUMN = 'retired_generation'

#: What `opus_import.importdb.lock_name` is given, after the schema, for the lock every
#: generation command holds and every writer of a pending generation takes briefly.
GENERATION_LOCK = 'generation'

#: The columns of ``schema_version`` `GenerationState` reads, in its order.
STATE_COLUMNS = (
    'version',
    'state',
    SERVED_GENERATION_COLUMN,
    PENDING_GENERATION_COLUMN,
    PENDING_STATE_COLUMN,
    REVERTIBLE_COLUMN,
)

_TABLE_SCHEMA_DIR = files('opus_import') / 'table_schemas'


def physical_table_name(table_name: str) -> str:
    """Return the table a name refers to: the base table for ``obs_general``.

    Parameters:
        table_name: A table name as the import uses it.

    Returns:
        `OBS_GENERAL_ROWS` for `OBS_GENERAL_VIEW`, the name itself otherwise.
    """
    return OBS_GENERAL_ROWS if table_name == OBS_GENERAL_VIEW else table_name


def logical_table_name(table_name: str) -> str:
    """Return the name the import uses for a table the server lists.

    Parameters:
        table_name: A base table's name, as the server reports it.

    Returns:
        `OBS_GENERAL_VIEW` for `OBS_GENERAL_ROWS`, matched without regard to case, the
        name itself otherwise.
    """
    return OBS_GENERAL_VIEW if table_name.lower() == OBS_GENERAL_ROWS else table_name


def view_columns(schema: Sequence[dict[str, Any]]) -> list[str]:
    """Return the columns the served view lists: every column but the generation columns.

    Parameters:
        schema: ``obs_general``'s table schema.

    Returns:
        The column names, in the schema's order.
    """
    return [
        str(entry['field_name'])
        for entry in schema
        if 'field_name' in entry and entry['field_name'] not in GENERATION_COLUMNS
    ]


def schema_version_table_schema() -> list[dict[str, Any]]:
    """Return the packaged schema of ``schema_version``, which the view reads."""
    text = (_TABLE_SCHEMA_DIR / f'{SCHEMA_VERSION_TABLE}.json').read_text(encoding='utf-8')
    schema: list[dict[str, Any]] = json.loads(text)
    return schema


def in_generation_condition(quote: Callable[[str], str], alias: str) -> str:
    """Return the test that a row of ``obs_general_rows`` is in a generation.

    Parameters:
        quote: The database's identifier quoting (`ImportDBSuper.quote_identifier`).
        alias: The alias the row's columns are qualified by, unquoted.

    Returns:
        The condition, with two placeholders, both the generation.
    """
    added = f'{quote(alias)}.{quote(ADDED_GENERATION_COLUMN)}'
    removed = f'{quote(alias)}.{quote(REMOVED_GENERATION_COLUMN)}'
    return f'{added} <= %s AND ({removed} IS NULL OR {removed} > %s)'


@dataclass(frozen=True)
class GenerationState:
    """A schema's one ``schema_version`` row.

    Attributes:
        version: The schema version that imported it.
        state: ``ready`` or ``appending``.
        generation: The generation the web application serves.
        pending: The generation an update is writing, or None.
        pending_state: How far it has got, one of the ``PENDING_`` constants, or None.
        revertible: Whether a switch can still be reverted, true from a switch until the
            purge starts.
    """

    version: int
    state: str
    generation: int
    pending: int | None
    pending_state: str | None
    revertible: bool

    @classmethod
    def from_row(cls, row: Sequence[Any]) -> GenerationState:
        """Return the state from a row of `STATE_COLUMNS`."""
        version, state, generation, pending, pending_state, revertible = row
        return cls(
            int(version),
            str(state),
            int(generation),
            None if pending is None else int(pending),
            None if pending_state is None else str(pending_state),
            bool(revertible),
        )

    @property
    def working_generation(self) -> int:
        """The generation an import writes and finalization works on, the pending one if
        any, otherwise the served one."""
        return self.generation if self.pending is None else self.pending
