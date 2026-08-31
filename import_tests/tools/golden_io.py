"""The one serializer on both sides of every golden comparison.

`import_tests.tools.make_mini_goldens` writes a table through this module and the tests
read and compare through it, so the two agree on the format by construction rather than
by convention. It also holds the small amount of raw database access the suite needs,
over the same MySQLdb driver the import itself uses.

From an empty database the import is deterministic: row ids are handed out in table
order from the highest id already present. So a golden normalizes only two things, each
named and justified where it is applied: the columns MySQL fills in with the wall clock
(`TIMESTAMP_DATA_TYPE`) are dropped, and one JSON list whose order pdsfile documents as
unstable (`_UNORDERED_JSON_COLUMNS`) is sorted. Any other column that differs between two
clean runs is a defect rather than a normalization candidate.

`without_surrogate_ids` is a third normalization, and it is deliberately not part of
writing or reading a golden: only the re-import comparison uses it, because only a
re-import renumbers rows.
"""

from __future__ import annotations

import datetime
import json
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

import MySQLdb

if TYPE_CHECKING:
    from collections.abc import Sequence

#: How a NULL is spelled, which is deliberately not the empty string: a column holding
#: an empty string and one holding NULL are different facts about the import.
NULL_TOKEN = '\\N'

#: The escapes that keep one row on one line and one value in one field. They are
#: applied in this order on the way out and reversed on the way in.
_ESCAPES = (('\\', '\\\\'), ('\t', '\\t'), ('\r', '\\r'), ('\n', '\\n'))

#: The MySQL data type the goldens drop entirely. The import never writes these columns
#: -- ``do_import_obs`` skips every ``timestamp`` field -- and MySQL fills them from the
#: wall clock, so they differ between two identical runs by design.
TIMESTAMP_DATA_TYPE = 'timestamp'

#: The extension every golden file carries.
GOLDEN_EXT = '.tsv'

#: The one column the goldens reorder before comparing, and the JSON list inside it.
#:
#: ``obs_general.preview_images`` is ``PdsViewSet.to_dict()``, and pdsfile says in as many
#: words that its members come out "in the iteration order of a Python set, which is not
#: the order they were appended in and is not stable across processes". The set holds
#: objects, so the order does not follow the hash seed either: two identical imports store
#: the same images in a different order. Sorting the list makes the comparison about which
#: images an observation has rather than about which run wrote the row.
_UNORDERED_JSON_COLUMNS = {('obs_general', 'preview_images'): 'viewables'}

#: What each entry of that list is sorted by.
_UNORDERED_JSON_SORT_KEY = 'url'

#: The columns the server numbers rather than the import computing: ``id`` is the
#: auto-incremented row id and ``obs_general_id`` is the foreign key naming an
#: observation's ``obs_general`` row. They are stable across two clean runs from an empty
#: database, which is why the goldens carry them, and they are *not* stable across a
#: re-import: the pipeline hands out ids from the largest already present in either
#: namespace and only deletes the bundle's old rows afterwards, so re-importing a bundle
#: renumbers it above everything else in the table. `without_surrogate_ids` is what the
#: re-import comparison drops them with.
SURROGATE_ID_COLUMNS = frozenset({'id', 'obs_general_id'})

#: The column naming the bundle a row came from, where a table has one.
BUNDLE_COLUMN = 'bundle_id'


@dataclass(frozen=True)
class DatabaseCredentials:
    """How to reach the MySQL server a run imports into.

    Attributes:
        host: The server's host name. Use an address rather than ``localhost``: MySQLdb
            reads ``localhost`` as a request for a Unix socket, which exists on a
            developer's machine and not beside a CI service container.
        user: A user allowed to create and drop databases, because each run creates its
            own schema.
        password: That user's password.
    """

    host: str
    user: str
    password: str


def connect(credentials: DatabaseCredentials, schema: str | None) -> Any:
    """Open a connection to the server, optionally selecting a schema.

    Parameters:
        credentials: How to reach the server.
        schema: The schema to select, or None to connect without one -- which is what
            creating or dropping a database needs.

    Returns:
        The open connection. The caller closes it. The return type is deliberately
        untyped: the driver's stubs annotate neither ``cursor()`` nor the connection
        methods, so a precise type here would only move the same suppression to every
        call site.
    """
    if schema is None:
        return MySQLdb.connect(
            host=credentials.host, user=credentials.user, passwd=credentials.password
        )
    return MySQLdb.connect(
        host=credentials.host, user=credentials.user, passwd=credentials.password, db=schema
    )


def execute(credentials: DatabaseCredentials, schema: str | None, statement: str) -> None:
    """Run one statement that returns no rows.

    Parameters:
        credentials: How to reach the server.
        schema: The schema to run it in, or None.
        statement: The SQL to run.
    """
    connection = connect(credentials, schema)
    try:
        cursor = connection.cursor()
        cursor.execute(statement)
        connection.commit()
    finally:
        connection.close()


def query(
    credentials: DatabaseCredentials,
    schema: str | None,
    statement: str,
    parameters: Sequence[Any] = (),
) -> list[tuple[Any, ...]]:
    """Run one query and return every row.

    Parameters:
        credentials: How to reach the server.
        schema: The schema to run it in, or None.
        statement: The SQL to run.
        parameters: The values to bind.

    Returns:
        The rows, as the driver returned them.
    """
    connection = connect(credentials, schema)
    try:
        cursor = connection.cursor()
        cursor.execute(statement, parameters)
        return list(cursor.fetchall())
    finally:
        connection.close()


def list_tables(credentials: DatabaseCredentials, schema: str) -> list[str]:
    """Return every table a schema holds, sorted.

    Parameters:
        credentials: How to reach the server.
        schema: The schema to list.

    Returns:
        The table names. An absent schema lists nothing rather than raising, which is
        what makes a before/after diff around a step that creates the schema work.
    """
    rows = query(
        credentials,
        None,
        'SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA = %s',
        [schema],
    )
    return sorted(str(row[0]) for row in rows)


def _columns(credentials: DatabaseCredentials, schema: str, table: str) -> list[tuple[str, str]]:
    """Return a table's columns in declaration order, with their data types.

    Parameters:
        credentials: How to reach the server.
        schema: The schema.
        table: The table.

    Returns:
        (column name, MySQL data type) pairs.
    """
    rows = query(
        credentials,
        None,
        'SELECT COLUMN_NAME, DATA_TYPE FROM information_schema.COLUMNS '
        'WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s ORDER BY ORDINAL_POSITION',
        [schema, table],
    )
    return [(str(row[0]), str(row[1])) for row in rows]


def _primary_key(credentials: DatabaseCredentials, schema: str, table: str) -> list[str]:
    """Return a table's primary key columns, in key order.

    Parameters:
        credentials: How to reach the server.
        schema: The schema.
        table: The table.

    Returns:
        The column names, or an empty list for a table with no primary key.
    """
    rows = query(
        credentials,
        None,
        'SELECT COLUMN_NAME FROM information_schema.KEY_COLUMN_USAGE '
        'WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s AND CONSTRAINT_NAME = %s '
        'ORDER BY ORDINAL_POSITION',
        [schema, table, 'PRIMARY'],
    )
    return [str(row[0]) for row in rows]


def encode_value(value: Any) -> str:
    """Render one database value as a golden field.

    Parameters:
        value: The value MySQLdb returned.

    Returns:
        `NULL_TOKEN` for NULL, the ISO form of a date or time, a hexadecimal literal for
        binary data, and the value's own text otherwise, with tabs, newlines and
        backslashes escaped so one row stays on one line.
    """
    if value is None:
        return NULL_TOKEN
    if isinstance(value, (bytes, bytearray)):
        return '0x' + bytes(value).hex()
    if isinstance(value, (datetime.datetime, datetime.date, datetime.time)):
        text = value.isoformat()
    else:
        # Everything else -- integers, floats, decimals, intervals -- renders through
        # str(), which round-trips a float to its shortest exact form and keeps a
        # decimal's scale.
        text = str(value)
    for raw, escaped in _ESCAPES:
        text = text.replace(raw, escaped)
    return text


def serialize_table(credentials: DatabaseCredentials, schema: str, table: str) -> str:
    """Read one table and render it as its golden text.

    Every column MySQL declares as a timestamp is dropped: the import never writes one,
    and the server fills them from the wall clock. Which columns those are is read from
    the server rather than listed here, so a new timestamp column is handled the day it
    appears. One further column is reordered rather than dropped -- see
    `_UNORDERED_JSON_COLUMNS`, which names it and says why. Nothing else is normalized:
    from an empty database every other value the import writes is the same on every run,
    and one that is not is a defect rather than a normalization candidate.

    Parameters:
        credentials: How to reach the server.
        schema: The schema to read.
        table: The table to read.

    Returns:
        A header line of column names, then one line per row, ordered by primary key.
    """
    columns = [
        name
        for name, data_type in _columns(credentials, schema, table)
        if data_type != TIMESTAMP_DATA_TYPE
    ]
    if len(columns) == 0:
        return '\n'
    key = _primary_key(credentials, schema, table)
    order_by = key if len(key) > 0 else columns
    quoted = ', '.join(f'`{name}`' for name in columns)
    ordering = ', '.join(f'`{name}`' for name in order_by)
    rows = query(credentials, schema, f'SELECT {quoted} FROM `{table}` ORDER BY {ordering}')
    lines = ['\t'.join(columns)]
    lines += [
        '\t'.join(
            encode_value(_ordered(table, column, value))
            for column, value in zip(columns, row, strict=True)
        )
        for row in rows
    ]
    return '\n'.join(lines) + '\n'


def without_surrogate_ids(text: str) -> str:
    """Return a serialized table with the server-numbered columns dropped and rows sorted.

    Both go together: dropping the ids without sorting would still compare unequal,
    because the rows are serialized in primary-key order and a renumbered bundle's rows
    move to the end of it. What survives is the question this normalization exists to
    ask -- does the table hold the same rows, with the same values, as before -- and what
    it gives up is where in the id sequence those rows sit.

    Parameters:
        text: A `serialize_table` result, or a golden written from one.

    Returns:
        The same text with every `SURROGATE_ID_COLUMNS` field removed from the header and
        from every row, and the rows sorted. Text with no lines at all comes back
        unchanged: a golden is written with a header line and a serialized table always
        has one, so an empty one is a corrupted file, and returning it lets the
        comparison fail as a readable difference rather than as a traceback here.
    """
    lines = text.splitlines()
    if len(lines) == 0:
        return text
    header = lines[0].split('\t')
    keep = [index for index, name in enumerate(header) if name not in SURROGATE_ID_COLUMNS]

    def project(line: str) -> str:
        """Return one line with the surrogate id fields removed.

        Parameters:
            line: A header or row line.

        Returns:
            The line's remaining fields, tab-separated.
        """
        fields = line.split('\t')
        return '\t'.join(fields[index] for index in keep)

    return '\n'.join([project(lines[0]), *sorted(project(line) for line in lines[1:])]) + '\n'


def tables_holding_bundle(
    credentials: DatabaseCredentials, schema: str, tables: Sequence[str], bundle: str
) -> set[str]:
    """Return which of those tables carry rows belonging to one bundle.

    A table with no `BUNDLE_COLUMN` at all carries none: that is every mult table, and
    every table the dictionary and finalization steps write.

    Parameters:
        credentials: How to reach the server.
        schema: The schema to look in.
        tables: The tables to ask about.
        bundle: The bundle id.

    Returns:
        The names of the tables holding at least one of that bundle's rows.
    """
    holding = set()
    for table in tables:
        if BUNDLE_COLUMN not in [name for name, _type in _columns(credentials, schema, table)]:
            continue
        rows = query(
            credentials,
            schema,
            f'SELECT 1 FROM `{table}` WHERE `{BUNDLE_COLUMN}` = %s LIMIT 1',
            [bundle],
        )
        if len(rows) > 0:
            holding.add(table)
    return holding


def _ordered(table: str, column: str, value: Any) -> Any:
    """Return a value with the one unordered JSON list this suite knows about sorted.

    Parameters:
        table: The table the value came from.
        column: The column it came from.
        value: The value.

    Returns:
        The value unchanged, unless it is a column `_UNORDERED_JSON_COLUMNS` names, in
        which case its JSON list is re-encoded in sorted order.
    """
    list_key = _UNORDERED_JSON_COLUMNS.get((table, column))
    if list_key is None or not isinstance(value, str):
        return value
    decoded = json.loads(value)
    decoded[list_key] = sorted(
        decoded[list_key], key=lambda entry: str(entry.get(_UNORDERED_JSON_SORT_KEY, ''))
    )
    return json.dumps(decoded)


def golden_path(directory: Path, table: str) -> Path:
    """Return where one table's golden file lives.

    Parameters:
        directory: The goldens directory.
        table: The table name.

    Returns:
        The file path.
    """
    return directory / f'{table}{GOLDEN_EXT}'


def write_golden(directory: Path, table: str, text: str) -> Path:
    """Write one table's golden file.

    Parameters:
        directory: The goldens directory. It is created.
        table: The table name.
        text: The serialized table.

    Returns:
        The file written.
    """
    directory.mkdir(parents=True, exist_ok=True)
    target = golden_path(directory, table)
    target.write_text(text, encoding='utf-8')
    return target


def read_golden(directory: Path, table: str) -> str:
    """Read one table's golden file.

    Parameters:
        directory: The goldens directory.
        table: The table name.

    Returns:
        The file's text.
    """
    return golden_path(directory, table).read_text(encoding='utf-8')


def goldened_tables(directory: Path) -> list[str]:
    """Return every table the goldens cover, sorted.

    Parameters:
        directory: The goldens directory.

    Returns:
        The table names.
    """
    if not directory.is_dir():
        return []
    return sorted(path.stem for path in directory.glob(f'*{GOLDEN_EXT}'))
