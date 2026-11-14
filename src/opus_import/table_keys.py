"""The keys a table schema declares, and which of them a table is created with.

A table schema declares most of its keys on its columns: ``field_key`` is ``"primary"``,
``"unique"``, ``"foreign"`` (with ``field_key_foreign`` naming the referenced table and
column) or true for a plain key. A foreign key may instead be a table-level entry,
``{"foreign_key": {"columns": [...], "references": ["<table>", "<column>", ...],
"on_delete": "cascade" | "restrict"}}``, which is how one says what deleting the row it
references does; ``on_delete`` is optional and ``"restrict"`` when absent. A key over
several columns is a table-level entry too: ``{"primary_key": [...]}``,
``{"unique": [...]}`` or ``{"key": [...]}`` for a plain key, each listing its columns in
order. ``{"fulltext": [...]}`` declares a ``FULLTEXT`` index, which the brand builds with
the ngram parser (`NGRAM_TOKEN_SIZE`) for the web application's autocomplete; the column
keeps any B-tree key it declares beside it. `declared_keys` reads all of
them as `TableKey` values, which the brand renders and which compare by kind,
ordered columns and, for a foreign key, what it references and does on delete -- never by
name, because the server names an unnamed key itself.

The observation and mult tables (`is_key_filtered_table`) are created, on both write
paths, with only the keys a load needs (`create_time_keys`): the primary key, every
unique key, and the keys the per-bundle delete reads, so that a load maintains as few
indexes as it can. Finalization adds the rest (`add_secondary_indexes`) once, after the
last bundle, each ``FULLTEXT`` index first.
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

KeyKind = Literal['primary', 'unique', 'key', 'foreign', 'fulltext']
"""The kind of a key -- the primary key, a unique key, a plain key, a foreign key or a
``FULLTEXT`` index."""

OnDelete = Literal['cascade', 'restrict']
"""What deleting a referenced row does to the rows a foreign key ties to it."""

#: The ``on_delete`` values a table-level ``foreign_key`` entry may hold.
ON_DELETE_VALUES: tuple[OnDelete, ...] = ('cascade', 'restrict')

#: What a foreign key does on delete when its entry does not say.
DEFAULT_ON_DELETE: OnDelete = 'restrict'

#: The table-name prefixes of the tables the import creates with only the keys a load
#: needs: the observation tables the bundle steps write, and the mult tables.
KEY_FILTERED_TABLE_PREFIXES = ('obs_', 'mult_')

#: The column the per-bundle delete selects ``obs_general``'s rows by, read through a plain
#: key whose only column it is.
BUNDLE_DELETE_COLUMN = 'bundle_id'

#: The column the per-bundle delete reaches every other observation table's rows by,
#: joining ``obs_general`` on it; a table whose primary key does not start with it is
#: read through a plain key whose only column it is.
OBSERVATION_DELETE_COLUMN = 'obs_general_id'

#: The token size, in characters, of the ngram parser the ``FULLTEXT`` indexes are built
#: with: the server's ``ngram_token_size``, which finalization requires and the web
#: application's queries assume. A word of the search shorter than this has no token.
NGRAM_TOKEN_SIZE = 2

#: The widest column, in declared characters, a ``FULLTEXT`` entry is declared on: an
#: ngram index stores a token for nearly every character of every value, so on a wider
#: column (a file path, a note) it would outweigh the table, and the column keeps
#: ``LIKE``.
FULLTEXT_MAX_WIDTH = 100

#: How a log line names each kind of key but a foreign key, which names what it
#: references as well.
KEY_LABELS: dict[KeyKind, str] = {
    'primary': 'PRIMARY KEY',
    'unique': 'UNIQUE KEY',
    'key': 'KEY',
    'fulltext': 'FULLTEXT KEY',
}


def is_bundle_keyed_table(table_name: str) -> bool:
    """Return whether the per-bundle delete selects a table's rows by ``bundle_id``.

    Parameters:
        table_name: The table's raw name.

    Returns:
        True for ``obs_general`` alone: the delete reaches every other observation
        table's rows by joining ``obs_general`` on ``obs_general_id``.
    """
    return table_name.lower() == 'obs_general'


@dataclass(frozen=True)
class TableKey:
    """One key of one table, as a schema declares it or the server reports it.

    Two keys are the same key when their kind, their columns in order and, for a foreign
    key, what they reference and what they do on delete agree; a key's name never enters
    the comparison.

    Attributes:
        kind: What the key is.
        columns: The key's columns, in order.
        references: For a foreign key, the referenced table and its columns, in order;
            None for every other kind.
        on_delete: For a foreign key, what deleting a referenced row does; meaningless
            for every other kind, which keeps the default.
    """

    kind: KeyKind
    columns: tuple[str, ...]
    references: tuple[str, tuple[str, ...]] | None = None
    on_delete: OnDelete = DEFAULT_ON_DELETE

    def describe(self) -> str:
        """Return the key as a log line names it, such as ``KEY (time1)``.

        Returns:
            The kind and the columns, and for a foreign key what it references.
        """
        columns = ', '.join(self.columns)
        if self.kind == 'foreign':
            assert self.references is not None
            table, referenced = self.references
            described = f'FOREIGN KEY ({columns}) REFERENCES {table} ({", ".join(referenced)})'
            if self.on_delete != DEFAULT_ON_DELETE:
                described += f' ON DELETE {self.on_delete.upper()}'
            return described
        return f'{KEY_LABELS[self.kind]} ({columns})'


def is_key_filtered_table(table_name: str) -> bool:
    """Return whether the import creates a table with only the keys a load needs.

    Parameters:
        table_name: The table's raw name.

    Returns:
        True for an observation table or a mult table.
    """
    return table_name.lower().startswith(KEY_FILTERED_TABLE_PREFIXES)


def _table_level_foreign_key(entry: SchemaColumn) -> TableKey:
    """Return the foreign key a table-level ``foreign_key`` entry declares.

    Parameters:
        entry: The entry's ``foreign_key`` value.

    Returns:
        The key.

    Raises:
        ValueError: If the entry names no columns, does not name a table and as many
            columns as it has, or holds an ``on_delete`` that is not one of
            `ON_DELETE_VALUES`.
    """
    columns = tuple(entry.get('columns') or ())
    references = tuple(entry.get('references') or ())
    if not columns or len(references) != len(columns) + 1:
        raise ValueError(f'foreign_key {entry!r}: names a table and a column for each column')
    on_delete = entry.get('on_delete', DEFAULT_ON_DELETE)
    if on_delete not in ON_DELETE_VALUES:
        raise ValueError(f'foreign_key {entry!r}: unknown on_delete {on_delete!r}')
    return TableKey('foreign', columns, (references[0], references[1:]), on_delete)


#: The table-level entries that declare a primary, unique, plain or ``FULLTEXT`` key over
#: listed columns, and the kind of key each declares.
TABLE_LEVEL_KEY_KINDS: dict[str, KeyKind] = {
    'primary_key': 'primary',
    'unique': 'unique',
    'key': 'key',
    'fulltext': 'fulltext',
}


def _table_level_key(entry_name: str, columns: object) -> TableKey:
    """Return the key a table-level ``primary_key``, ``unique``, ``key`` or ``fulltext`` entry
    declares.

    Parameters:
        entry_name: The entry's name, a key of `TABLE_LEVEL_KEY_KINDS`.
        columns: The entry's value.

    Returns:
        The key.

    Raises:
        ValueError: If the value is not a non-empty list of column names.
    """
    if (
        not isinstance(columns, list)
        or not columns
        or not all(isinstance(column, str) for column in columns)
    ):
        raise ValueError(f'{entry_name} {columns!r}: a key lists its columns by name')
    return TableKey(TABLE_LEVEL_KEY_KINDS[entry_name], tuple(columns))


def declared_keys(schema: Sequence[SchemaColumn]) -> list[TableKey]:
    """Return the keys a table schema declares, in the order of its entries.

    Parameters:
        schema: The table schema.

    Returns:
        One key per column whose ``field_key`` declares one, and one per table-level
        ``foreign_key``, ``primary_key``, ``unique``, ``key`` or ``fulltext`` entry. Other
        entries without
        ``field_name`` (constraints, and ``param_info`` rows of another table) declare
        none.

    Raises:
        ValueError: If a ``field_key`` is not one of the values a schema may hold, a
            foreign key does not name its table and column, or a table-level key does
            not list its columns.
    """
    keys: list[TableKey] = []
    for column in schema:
        if 'foreign_key' in column:
            keys.append(_table_level_foreign_key(column['foreign_key']))
            continue
        level_entry = next((name for name in TABLE_LEVEL_KEY_KINDS if name in column), None)
        if level_entry is not None:
            keys.append(_table_level_key(level_entry, column[level_entry]))
            continue
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


def _delete_keys(table_name: str, keys: Sequence[TableKey]) -> list[TableKey]:
    """Return the declared keys the per-bundle delete reads.

    Parameters:
        table_name: The table's raw name.
        keys: Its declared keys.

    Returns:
        For ``obs_general`` (`is_bundle_keyed_table`), each plain key whose only column is
        `BUNDLE_DELETE_COLUMN`; for any other observation table, each plain key whose only
        column is `OBSERVATION_DELETE_COLUMN`, which a table declares when its primary key
        does not start with that column; for any other table, none.
    """
    if is_bundle_keyed_table(table_name):
        column = BUNDLE_DELETE_COLUMN
    elif table_name.lower().startswith('obs_'):
        column = OBSERVATION_DELETE_COLUMN
    else:
        return []
    return [key for key in keys if key.kind == 'key' and key.columns == (column,)]


def create_time_keys(table_name: str, schema: Sequence[SchemaColumn]) -> list[TableKey]:
    """Return the keys the import creates a table with, in column order.

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
    delete_keys = _delete_keys(table_name, keys)
    return [key for key in keys if key.kind in ('primary', 'unique') or key in delete_keys]


def add_secondary_indexes(table_name: str, schema: Sequence[SchemaColumn]) -> list[TableKey]:
    """Return the keys finalization adds to a table the import created.

    These are every declared key `create_time_keys` leaves out, in column order, then, for
    each foreign-key column that no B-tree key leads, a plain key on that column, so that
    the foreign key, which needs an index whose first column is its own, finds one built
    rather than creating it implicitly while foreign keys are added one at a time. A
    ``FULLTEXT`` index leads no B-tree key.

    Parameters:
        table_name: The table's raw name.
        schema: Its schema.

    Returns:
        The keys, ``FULLTEXT`` indexes first, then plain keys, then foreign keys; none for a
        table that is not an observation or mult table, which is created with every key
        it declares.
    """
    if not is_key_filtered_table(table_name):
        return []
    keys = declared_keys(schema)
    kept = create_time_keys(table_name, schema)
    rest = [key for key in keys if key not in kept]
    led = {key.columns[0] for key in keys if key.kind not in ('foreign', 'fulltext')}
    supporting = [
        TableKey('key', key.columns)
        for key in rest
        if key.kind == 'foreign' and key.columns[0] not in led
    ]
    fulltext = [key for key in rest if key.kind == 'fulltext']
    plain = [key for key in rest if key.kind not in ('foreign', 'fulltext')]
    foreign = [key for key in rest if key.kind == 'foreign']
    return [*fulltext, *plain, *supporting, *foreign]
