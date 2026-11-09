"""The keys a table schema declares, and which of them a fresh import creates when.

A table schema declares its keys on its columns: ``field_key`` is ``"primary"``,
``"unique"``, ``"foreign"`` (with ``field_key_foreign`` naming the referenced table and
column) or true for a plain key. `declared_keys` reads them as `TableKey` values, which
the brand renders and which compare by kind and ordered columns, never by name, because
the server names an unnamed key itself.

On a fresh import the observation and mult tables (`is_key_filtered_table`) are created
with only the keys a load needs (`create_time_keys`): the primary key, every unique key,
and the keys the per-bundle delete reads, so that a load maintains as few indexes as it
can. Finalization adds the rest (`add_secondary_indexes`) once, after the last bundle.
The two are complements over a filtered table's keys, apart from the plain key
`add_secondary_indexes` adds under a foreign-key column no key of its own leads, so that
the foreign key finds its index already built. Every other table is created with every
key it declares.

A ``{"constraint": ...}`` entry is rendered raw by the brand and is part of no key list
here; it is always created with its table.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from collections.abc import Sequence

    from opus_import.importdb.super import SchemaColumn

KeyKind = Literal['primary', 'unique', 'key', 'foreign']
"""The kind of a key -- the primary key, a unique key, a plain key or a foreign key."""

#: The table-name prefixes of the tables a fresh import creates with only the keys a load
#: needs: the observation tables the bundle steps write, and the mult tables.
KEY_FILTERED_TABLE_PREFIXES = ('obs_', 'mult_')

#: The columns the per-bundle delete selects a table's rows by, each read through a plain
#: key whose only column it is.
DELETE_READ_COLUMNS = ('bundle_id',)


@dataclass(frozen=True)
class TableKey:
    """One key of one table, as a schema declares it or the server reports it.

    Two keys are the same key when their kind, their columns in order and, for a foreign
    key, what they reference agree; a key's name never enters the comparison.

    Attributes:
        kind: What the key is.
        columns: The key's columns, in order.
        references: For a foreign key, the referenced table and its columns, in order;
            None for every other kind.
    """

    kind: KeyKind
    columns: tuple[str, ...]
    references: tuple[str, tuple[str, ...]] | None = None

    def describe(self) -> str:
        """Return the key as a log line names it, such as ``KEY (time1)``.

        Returns:
            The kind and the columns, and for a foreign key what it references.
        """
        columns = ', '.join(self.columns)
        if self.kind == 'foreign':
            assert self.references is not None
            table, referenced = self.references
            return f'FOREIGN KEY ({columns}) REFERENCES {table} ({", ".join(referenced)})'
        label = {'primary': 'PRIMARY KEY', 'unique': 'UNIQUE KEY', 'key': 'KEY'}[self.kind]
        return f'{label} ({columns})'


def is_key_filtered_table(table_name: str) -> bool:
    """Return whether a fresh import creates a table with only the keys a load needs.

    Parameters:
        table_name: The table's raw name.

    Returns:
        True for an observation table or a mult table.
    """
    return table_name.lower().startswith(KEY_FILTERED_TABLE_PREFIXES)


def declared_keys(schema: Sequence[SchemaColumn]) -> list[TableKey]:
    """Return the keys a table schema declares on its columns, in column order.

    Parameters:
        schema: The table schema.

    Returns:
        One key per column whose ``field_key`` declares one. Entries without
        ``field_name`` (constraints, and ``param_info`` rows of another table) declare
        none.

    Raises:
        ValueError: If a ``field_key`` is not one of the values a schema may hold, or a
            foreign key does not name its table and column.
    """
    keys: list[TableKey] = []
    for column in schema:
        if 'field_name' not in column:
            continue
        field_key = column.get('field_key', False)
        if field_key is False or field_key is None:
            continue
        columns = (column['field_name'],)
        if field_key is True:
            keys.append(TableKey('key', columns))
        elif field_key in ('primary', 'unique'):
            keys.append(TableKey(field_key, columns))
        elif field_key == 'foreign':
            foreign = column.get('field_key_foreign')
            if not foreign or len(foreign) != 2:
                raise ValueError(f'{columns[0]}: a foreign key names its table and column')
            keys.append(TableKey('foreign', columns, (foreign[0], (foreign[1],))))
        else:
            raise ValueError(f'{columns[0]}: unknown field_key {field_key!r}')
    return keys


def _delete_keys(keys: Sequence[TableKey]) -> list[TableKey]:
    """Return the declared keys the per-bundle delete reads.

    Parameters:
        keys: A table's declared keys.

    Returns:
        Each plain key whose only column is one the delete selects rows by.
    """
    return [
        key
        for key in keys
        if key.kind == 'key' and len(key.columns) == 1 and key.columns[0] in DELETE_READ_COLUMNS
    ]


def create_time_keys(table_name: str, schema: Sequence[SchemaColumn]) -> list[TableKey]:
    """Return the keys a fresh import creates a table with, in column order.

    Parameters:
        table_name: The table's raw name.
        schema: Its schema.

    Returns:
        For an observation or mult table, its primary key, its unique keys and the keys
        the per-bundle delete reads; for any other table, every key it declares.
    """
    keys = declared_keys(schema)
    if not is_key_filtered_table(table_name):
        return keys
    delete_keys = _delete_keys(keys)
    return [key for key in keys if key.kind in ('primary', 'unique') or key in delete_keys]


def add_secondary_indexes(table_name: str, schema: Sequence[SchemaColumn]) -> list[TableKey]:
    """Return the keys finalization adds to a table a fresh import created.

    These are every declared key `create_time_keys` leaves out, in column order, then, for
    each foreign-key column that no key leads, a plain key on that column, so that the
    foreign key, which needs an index whose first column is its own, finds one built
    rather than creating it implicitly while foreign keys are added one at a time.

    Parameters:
        table_name: The table's raw name.
        schema: Its schema.

    Returns:
        The keys, plain keys before foreign keys; none for a table that is not an
        observation or mult table, which is created with every key it declares.
    """
    if not is_key_filtered_table(table_name):
        return []
    keys = declared_keys(schema)
    kept = create_time_keys(table_name, schema)
    rest = [key for key in keys if key not in kept]
    led = {key.columns[0] for key in keys if key.kind != 'foreign'}
    supporting = [
        TableKey('key', key.columns)
        for key in rest
        if key.kind == 'foreign' and key.columns[0] not in led
    ]
    plain = [key for key in rest if key.kind != 'foreign']
    foreign = [key for key in rest if key.kind == 'foreign']
    return [*plain, *supporting, *foreign]
