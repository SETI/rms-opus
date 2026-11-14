"""The packaged table schema files, where the web application reads them too.

The schemas ship inside `opus_import` and are found through :mod:`importlib.resources`,
so an installed OPUS reads them without a checkout. This module imports nothing beyond
the standard library and `opus_import.table_keys`, so the web application can read the
schemas without loading the import's own dependencies.
"""

from __future__ import annotations

import fnmatch
import functools
import json
from importlib.resources import files

from opus_import.table_keys import declared_keys

#: The packaged table schemas, as an :mod:`importlib.resources` traversable.
TABLE_SCHEMA_DIR = files('opus_import') / 'table_schemas'

#: The schema files of the observation tables, the only tables that declare a
#: ``FULLTEXT`` index.
OBSERVATION_SCHEMA_PATTERN = 'obs_*.json'


@functools.cache
def packaged_fulltext_columns() -> frozenset[tuple[str, str]]:
    """Return every column a packaged schema declares a ``FULLTEXT`` index on.

    A finalized schema carries exactly these indexes, so the web application asks for a
    full-text match only on these columns.

    Returns:
        Each column as its table and column names.
    """
    found: set[tuple[str, str]] = set()
    for entry in TABLE_SCHEMA_DIR.iterdir():
        if not entry.is_file() or not fnmatch.fnmatch(entry.name, OBSERVATION_SCHEMA_PATTERN):
            continue
        table_name = entry.name.removesuffix('.json')
        schema = json.loads(entry.read_text(encoding='utf-8'))
        found.update(
            (table_name, column)
            for key in declared_keys(schema)
            if key.kind == 'fulltext'
            for column in key.columns
        )
    return frozenset(found)
