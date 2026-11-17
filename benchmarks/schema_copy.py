"""Copy a schema on the owned server, views included, in one of two layouts.

`clone_schema` copies every table and view of one schema into another. By default each
table is created with every key and foreign key the source's has, then filled; its
secondary keys are then built by the rows' inserts, in the order the rows arrive. With
``defer_keys`` each table is laid out the way the import lays out a schema: created with
its primary key alone, filled in primary-key order, then given its secondary keys, each
built sorted from the rows already there, and last its foreign keys
(`split_secondary_keys`). A copy whose statements are timed against another schema's is
made the second way, so both have the layout the import gives them.
"""

from __future__ import annotations

import contextlib
import graphlib
import re
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from benchmarks.app_servers import ServerError
from benchmarks.bench_server import MysqlServer, query, quote_identifier, restamp_version

if TYPE_CHECKING:
    pass

#: A plain or unique key's line in ``SHOW CREATE TABLE``, which one ``ALTER`` can add with
#: the table's other such keys.
_PLAIN_KEY_LINE = re.compile(r'\s*(?:UNIQUE\s+)?KEY\s', re.IGNORECASE)

#: A ``FULLTEXT`` or ``SPATIAL`` key's line, which InnoDB adds one per ``ALTER``.
_SEPARATE_KEY_LINE = re.compile(r'\s*(?:FULLTEXT|SPATIAL)\s+KEY\s', re.IGNORECASE)

#: A foreign key's line.
_FOREIGN_KEY_LINE = re.compile(r'\s*CONSTRAINT\s+`(?:[^`]|``)*`\s+FOREIGN\s+KEY\s', re.IGNORECASE)


@dataclass(frozen=True)
class TableLayout:
    """A table's definition with its secondary keys and foreign keys set apart.

    Attributes:
        definition: The ``CREATE TABLE`` with its columns, primary key and any other
            constraint, but none of the keys and foreign keys below.
        keys: Each plain or unique key's clause, as ``SHOW CREATE TABLE`` prints it.
        separate_keys: Each ``FULLTEXT`` or ``SPATIAL`` key's clause.
        foreign_keys: Each foreign key's clause.
    """

    definition: str
    keys: tuple[str, ...] = ()
    separate_keys: tuple[str, ...] = ()
    foreign_keys: tuple[str, ...] = ()

    def key_statements(self, table: str) -> list[str]:
        """Return the statements that add the table's secondary keys.

        Parameters:
            table: The table, quoted and qualified as the statements name it.

        Returns:
            One ``ALTER TABLE`` adding every plain and unique key, when there is one,
            then one per ``FULLTEXT`` or ``SPATIAL`` key.
        """
        statements = []
        if len(self.keys) > 0:
            statements.append(
                f'ALTER TABLE {table} ' + ', '.join(f'ADD {key}' for key in self.keys)
            )
        statements += [f'ALTER TABLE {table} ADD {key}' for key in self.separate_keys]
        return statements

    def foreign_key_statement(self, table: str) -> str | None:
        """Return the statement that adds the table's foreign keys, or None for none.

        Parameters:
            table: The table, quoted and qualified as the statement names it.

        Returns:
            One ``ALTER TABLE`` adding every foreign key.
        """
        if len(self.foreign_keys) == 0:
            return None
        return f'ALTER TABLE {table} ' + ', '.join(f'ADD {key}' for key in self.foreign_keys)


def split_secondary_keys(definition: str) -> TableLayout:
    """Set a table's secondary keys and foreign keys apart from its definition.

    Parameters:
        definition: The ``Create Table`` column of ``SHOW CREATE TABLE``, which prints each
            column, key and constraint on a line of its own.

    Returns:
        The layout: the definition without those lines (the comma of the element left
        last before the closing parenthesis removed), and each line's clause.
    """
    kept: list[str] = []
    keys: list[str] = []
    separate: list[str] = []
    foreign: list[str] = []
    for line in definition.split('\n'):
        clause = line.strip().rstrip(',').rstrip()
        if _FOREIGN_KEY_LINE.match(line):
            foreign.append(clause)
        elif _SEPARATE_KEY_LINE.match(line):
            separate.append(clause)
        elif _PLAIN_KEY_LINE.match(line):
            keys.append(clause)
        else:
            kept.append(line)
    closing = [index for index, line in enumerate(kept) if line.startswith(')')]
    if len(keys) + len(separate) + len(foreign) > 0 and len(closing) > 0 and closing[-1] > 0:
        before = closing[-1] - 1
        kept[before] = kept[before].rstrip().rstrip(',')
    return TableLayout('\n'.join(kept), tuple(keys), tuple(separate), tuple(foreign))


#: A view definition's ``DEFINER`` clause, as ``SHOW CREATE VIEW`` prints it: the
#: account in backquotes, a backquote inside a name doubled, and the space after it.
_DEFINER_CLAUSE = re.compile(r'DEFINER=`(?:[^`]|``)*`@`(?:[^`]|``)*`\s*')

#: The quoted tokens of a view definition: a backquoted identifier, with a backquote
#: inside it doubled, and a string literal in single or double quotes, with a quote
#: inside it doubled or escaped by a backslash.
_QUOTED_TOKEN = re.compile(r"`(?:[^`]|``)*`|'(?:[^'\\]|\\.|'')*'|\"(?:[^\"\\]|\\.|\"\")*\"")


def portable_view_definition(definition: str, source: str, target: str) -> str:
    """Rewrite a view's ``SHOW CREATE VIEW`` text so that it creates the view in another schema.

    Every name the text qualifies with the source schema is qualified with the target
    instead, so the view reads the target's tables; only the identifier is rewritten, so
    a string literal holding the source's name is kept as it is. The ``DEFINER`` clause is dropped, so
    the view is defined by the account that creates it and creating it needs no privilege
    to name another account (``SET_USER_ID``); its algorithm and ``SQL SECURITY`` clause
    are kept.

    Parameters:
        definition: The ``Create View`` column of ``SHOW CREATE VIEW`` on the source.
        source: The schema the view was read from.
        target: The schema it is created in.

    Returns:
        The ``CREATE VIEW`` statement for the target.
    """
    source_name = quote_identifier(source)
    target_name = quote_identifier(target)

    def relocate(match: re.Match[str]) -> str:
        token = match.group(0)
        if token == source_name and match.string.startswith('.', match.end()):
            return target_name
        return token

    return _DEFINER_CLAUSE.sub('', _QUOTED_TOKEN.sub(relocate, definition), count=1)


def copy_views(connection: Any, source: str, target: str) -> list[str]:
    """Create every view of one schema in another, whose tables already exist.

    Each view is created from ``SHOW CREATE VIEW`` on the source, rewritten for the target
    (`portable_view_definition`), after every view of the source it reads, since MySQL
    creates a view only when what it names exists; views that read none of each other
    are created in name order.

    Parameters:
        connection: An open connection.
        source: The schema whose views are copied.
        target: The schema they are created in.

    Returns:
        The views created, in the order created.
    """
    views = [
        str(row[0])
        for row in query(
            connection,
            'SELECT TABLE_NAME FROM information_schema.TABLES '
            "WHERE TABLE_SCHEMA = %s AND TABLE_TYPE = 'VIEW' ORDER BY TABLE_NAME",
            [source],
        )
    ]
    reads: dict[str, set[str]] = {view: set() for view in views}
    for view, table in query(
        connection,
        'SELECT VIEW_NAME, TABLE_NAME FROM information_schema.VIEW_TABLE_USAGE '
        'WHERE VIEW_SCHEMA = %s AND TABLE_SCHEMA = %s',
        [source, source],
    ):
        if str(view) in reads and str(table) in reads:
            reads[str(view)].add(str(table))
    order = graphlib.TopologicalSorter(reads)
    order.prepare()
    created: list[str] = []
    while order.is_active():
        ready = sorted(order.get_ready())
        created.extend(ready)
        order.done(*ready)
    for view in created:
        definition = query(
            connection, f'SHOW CREATE VIEW {quote_identifier(source)}.{quote_identifier(view)}'
        )[0][1]
        query(connection, portable_view_definition(str(definition), source, target))
    return created


def _primary_key_columns(connection: Any, schema: str, table: str) -> list[str]:
    """Return a table's primary key columns, in key order; none for a table without one."""
    return [
        str(row[0])
        for row in query(
            connection,
            'SELECT COLUMN_NAME FROM information_schema.STATISTICS WHERE TABLE_SCHEMA = %s '
            "AND TABLE_NAME = %s AND INDEX_NAME = 'PRIMARY' ORDER BY SEQ_IN_INDEX",
            [schema, table],
        )
    ]


def clone_schema(
    server: MysqlServer,
    source: str,
    target: str,
    *,
    version: int | None,
    connections: int = 4,
    defer_keys: bool = False,
) -> float:
    """Copy a schema table by table into a new one, and time the copy.

    Each table is created from ``SHOW CREATE TABLE`` on the source, which carries its
    keys and foreign keys (``CREATE TABLE ... LIKE`` does not copy foreign keys), with
    ``foreign_key_checks`` off so that tables may be created and filled in any order;
    then its rows are copied with ``INSERT ... SELECT``, naming the stored columns only,
    since MySQL computes a generated column and refuses a value for one. The copies run
    over several connections at once. Every view of the source is created in the target
    once its tables exist (`copy_views`). The target is dropped first if it exists.
    Last, a copied version row is restamped to `version` (`restamp_version`).

    With ``defer_keys``, each table is created without its secondary keys and foreign
    keys (`split_secondary_keys`) and filled in its primary key's order; once every
    table is filled, each table's secondary keys are added (over several connections at
    once), then its foreign keys, with ``foreign_key_checks`` off, as the import builds
    them after its load.

    Parameters:
        server: The owned server.
        source: The schema to copy.
        target: The new schema.
        version: The ``SCHEMA_VERSION`` of the side that will use the copy, or None to
            leave a copied version row as it was, for a side whose code has none. Every
            call states it, since the right value depends on the side.
        connections: How many tables are copied at once.
        defer_keys: Whether to lay each table out as the import does, its secondary keys
            built after its rows are in.

    Returns:
        The copy's wall-clock seconds, creation, keys, views and restamp included.

    Raises:
        ServerError: If the source has no tables.
    """
    started = time.perf_counter()
    layouts: dict[str, TableLayout] = {}
    with contextlib.closing(server.connect()) as connection:
        tables = [
            str(row[0])
            for row in query(
                connection,
                'SELECT TABLE_NAME FROM information_schema.TABLES '
                "WHERE TABLE_SCHEMA = %s AND TABLE_TYPE = 'BASE TABLE' ORDER BY TABLE_NAME",
                [source],
            )
        ]
        if len(tables) == 0:
            raise ServerError(f'schema {source!r} has no tables to clone')
        query(connection, f'DROP DATABASE IF EXISTS {quote_identifier(target)}')
        query(connection, f'CREATE DATABASE {quote_identifier(target)}')
        query(connection, 'SET SESSION foreign_key_checks = 0')
        query(connection, f'USE {quote_identifier(target)}')
        for table in tables:
            definition = str(
                query(
                    connection,
                    f'SHOW CREATE TABLE {quote_identifier(source)}.{quote_identifier(table)}',
                )[0][1]
            )
            if defer_keys:
                layouts[table] = split_secondary_keys(definition)
                definition = layouts[table].definition
            query(connection, definition)
        copy_views(connection, source, target)

    def copy(table: str) -> None:
        """Copy one table's rows on a connection of its own.

        Parameters:
            table: The table.
        """
        with contextlib.closing(server.connect()) as sibling:
            query(sibling, 'SET SESSION foreign_key_checks = 0')
            columns = ', '.join(
                quote_identifier(str(row[0]))
                for row in query(
                    sibling,
                    'SELECT COLUMN_NAME FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = %s '
                    "AND TABLE_NAME = %s AND GENERATION_EXPRESSION = '' "
                    'ORDER BY ORDINAL_POSITION',
                    [source, table],
                )
            )
            order = ''
            if defer_keys:
                primary = _primary_key_columns(sibling, source, table)
                if len(primary) > 0:
                    order = ' ORDER BY ' + ', '.join(quote_identifier(name) for name in primary)
            query(
                sibling,
                f'INSERT INTO {quote_identifier(target)}.{quote_identifier(table)} ({columns}) '  # nosec B608 - quoted identifiers
                f'SELECT {columns} FROM {quote_identifier(source)}.{quote_identifier(table)}'
                + order,
            )

    def add_keys(table: str) -> None:
        """Add one table's secondary keys on a connection of its own.

        Parameters:
            table: The table.
        """
        with contextlib.closing(server.connect()) as sibling:
            qualified = f'{quote_identifier(target)}.{quote_identifier(table)}'
            for statement in layouts[table].key_statements(qualified):
                query(sibling, statement)

    with ThreadPoolExecutor(max_workers=max(1, connections)) as pool:
        list(pool.map(copy, tables))
        if defer_keys:
            list(pool.map(add_keys, tables))
    if defer_keys:
        with contextlib.closing(server.connect()) as connection:
            query(connection, 'SET SESSION foreign_key_checks = 0')
            # A foreign key's clause names a table of its own schema unqualified.
            query(connection, f'USE {quote_identifier(target)}')
            for table in tables:
                qualified = f'{quote_identifier(target)}.{quote_identifier(table)}'
                statement = layouts[table].foreign_key_statement(qualified)
                if statement is not None:
                    query(connection, statement)
    if version is not None:
        restamp_version(server, target, version)
    return time.perf_counter() - started
