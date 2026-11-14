"""Which columns the string-choices endpoint matches through an ngram ``FULLTEXT`` index.

The schemas declare each index as a ``{"fulltext": [...]}`` entry, and the endpoint reads
those entries (`opus_import.schema_files.packaged_fulltext_columns`). The entries are not a
hand-kept list: they are exactly the columns the endpoint completes -- each ``STRING``
field with a slug, read from the column its search reads
(`opus_app.apps.search.views.STRING_CHOICE_COLUMN_SUBSTITUTES`) -- whose declared width is
at most `opus_import.table_keys.FULLTEXT_MAX_WIDTH` characters. This test derives that set
and compares.
"""

from __future__ import annotations

import fnmatch
import json
from typing import Any

from opus_app.apps.search.views import STRING_CHOICE_COLUMN_SUBSTITUTES
from opus_import.importdb.mysql import MYSQL_WIDTH_FIELD_TYPE
from opus_import.schema_files import (
    OBSERVATION_SCHEMA_PATTERN,
    TABLE_SCHEMA_DIR,
    packaged_fulltext_columns,
)
from opus_import.table_keys import FULLTEXT_MAX_WIDTH


def _observation_columns() -> dict[tuple[str, str], dict[str, Any]]:
    """Return every column of every packaged observation schema, keyed by table and name."""
    columns: dict[tuple[str, str], dict[str, Any]] = {}
    for entry in TABLE_SCHEMA_DIR.iterdir():
        if not fnmatch.fnmatch(entry.name, OBSERVATION_SCHEMA_PATTERN):
            continue
        table = entry.name.removesuffix('.json')
        for column in json.loads(entry.read_text(encoding='utf-8')):
            if 'field_name' in column:
                columns[(table, column['field_name'])] = column
    return columns


def _completed_columns() -> set[tuple[str, str]]:
    """Return the column each ``STRING`` field with a slug is completed from."""
    return {
        STRING_CHOICE_COLUMN_SUBSTITUTES.get(f'{table}.{name}', (table, name))
        for (table, name), column in _observation_columns().items()
        if column.get('pi_form_type') == 'STRING' and column.get('pi_slug')
    }


def _width(column: dict[str, Any]) -> int | None:
    """Return a column's declared width in characters, or None for a type without one."""
    match = MYSQL_WIDTH_FIELD_TYPE.fullmatch(column['field_type'])
    return None if match is None else int(match[1])


def test_the_indexed_columns_are_the_completed_columns_no_wider_than_the_limit() -> None:
    """Every completed column of a declared width within the limit, and nothing else."""
    columns = _observation_columns()
    expected = set()
    for key in _completed_columns():
        width = _width(columns[key])
        if width is not None and width <= FULLTEXT_MAX_WIDTH:
            expected.add(key)
    assert packaged_fulltext_columns() == expected


def test_a_field_shown_in_one_table_is_indexed_where_its_search_reads() -> None:
    """The OPUS ID is shown in ``obs_pds`` but completed from ``obs_general``."""
    assert ('obs_general', 'opus_id') in packaged_fulltext_columns()
    assert ('obs_pds', 'opus_id') not in packaged_fulltext_columns()


def test_a_wide_completed_column_keeps_like() -> None:
    """A file specification is completed but too wide to index."""
    assert ('obs_pds', 'primary_filespec') in _completed_columns()
    assert ('obs_pds', 'primary_filespec') not in packaged_fulltext_columns()
