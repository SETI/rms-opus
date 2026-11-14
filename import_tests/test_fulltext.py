"""The ngram ``FULLTEXT`` indexes of a finished schema find what ``LIKE`` finds.

The string-choices endpoint matches a ``contains`` search of an indexed column through the
index as well as with ``LIKE`` (`opus_app.apps.tools.sql_builder.fulltext_match`). The
index narrows the rows the ``LIKE`` reads, so it must never leave out a row the ``LIKE``
alone matches. For every indexed column of the main run's schema, every value's runs of
two, three and six characters, the whole value, and those runs with their case swapped
are searched both ways, and the distinct values found must be the same. A run holding a
character the ngram parser breaks a token at, or a stopword's letter (``a`` or ``i``),
which an index built with the stopword list on drops, is among them.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

import pytest

from import_tests.tools import golden_io
from opus_app.apps.tools import sql_builder
from opus_import.schema_files import packaged_fulltext_columns
from opus_import.table_keys import NGRAM_TOKEN_SIZE

if TYPE_CHECKING:
    from import_tests.tools import build_run
    from import_tests.tools.golden_io import DatabaseCredentials

#: The lengths of the runs of each value searched for: the shortest the index holds, the
#: next, and the six characters the benchmark's autocomplete scenario types.
_RUN_LENGTHS = (NGRAM_TOKEN_SIZE, NGRAM_TOKEN_SIZE + 1, 6)


def _like_pattern(text: str) -> str:
    """Return the ``LIKE`` pattern of a ``contains`` search, as the search builds it."""
    escaped = text.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
    return f'%{escaped}%'


def _terms(values: list[str]) -> list[str]:
    """Return the texts searched for in a column holding `values`, sorted."""
    terms: set[str] = set()
    for value in values:
        terms.add(value)
        for length in _RUN_LENGTHS:
            for start in range(len(value) - length + 1):
                run = value[start : start + length]
                terms.update((run, run.swapcase()))
    return sorted(term for term in terms if term)


def _found(cursor: Any, statement: str, parameters: list[Any]) -> set[str]:
    """Return the distinct values a query finds."""
    cursor.execute(statement, parameters)
    return {str(row[0]) for row in cursor.fetchall()}


@pytest.mark.parametrize(
    ('table', 'column'),
    sorted(packaged_fulltext_columns()),
    ids=lambda value: str(value),
)
def test_the_index_finds_every_value_like_finds(
    main_run: build_run.ImportRun,
    db_credentials: DatabaseCredentials,
    table: str,
    column: str,
) -> None:
    """For each text, the full-text condition beside ``LIKE`` finds what ``LIKE`` alone finds."""
    quoted = sql_builder.column(column, table)
    like = f'SELECT DISTINCT {quoted.sql} FROM `{table}` WHERE {quoted.sql} LIKE %s'
    connection = golden_io.connect(db_credentials, main_run.schema)
    try:
        cursor = connection.cursor()
        cursor.execute(
            f'SELECT DISTINCT {quoted.sql} FROM `{table}` WHERE {quoted.sql} IS NOT NULL'
        )
        values = [str(row[0]) for row in cursor.fetchall()]
        assert values, f'{table}.{column} holds no value to search for'
        differing = []
        matched = 0
        for term in _terms(values):
            match = sql_builder.fulltext_match(quoted, term)
            if match is None:
                continue
            matched += 1
            expected = _found(cursor, like, [_like_pattern(term)])
            found = _found(cursor, f'{like} AND {match.sql}', [_like_pattern(term), *match.params])
            if found != expected:
                differing.append((term, sorted(expected - found)))
        assert differing == []
        assert matched > 0
    finally:
        connection.close()


def test_every_index_is_built_with_the_ngram_parser(
    main_run: build_run.ImportRun, db_credentials: DatabaseCredentials
) -> None:
    """Each declared index is in the schema, and the server reports the ngram parser."""
    for table, column in sorted(packaged_fulltext_columns()):
        ((_, definition),) = golden_io.query(
            db_credentials, main_run.schema, f'SHOW CREATE TABLE `{table}`'
        )
        # The server names an unnamed key after its column, with a suffix when a key of
        # that name exists.
        declared = (
            rf'FULLTEXT KEY `{column}(_\d+)?` \(`{column}`\) /\*!50100 WITH PARSER `ngram` \*/'
        )
        assert re.search(declared, str(definition)) is not None, table
