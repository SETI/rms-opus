"""Discard the tables the web application caches search results in.

An import changes what a search returns, so every cached result the web application is
holding is stale once the run finishes. Both the ``cache_*`` tables and the
``user_searches`` table they are keyed by are dropped, and ``user_searches`` is created
again empty.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from opus_import import import_util

if TYPE_CHECKING:
    from opus_import.context import ImportContext


def drop_cache_tables(ctx: ImportContext) -> None:
    """Drop every ``cache_`` table and reset ``user_searches`` to empty.

    The ``cache_`` tables are named after a row of ``user_searches``, so they are found
    by prefix rather than from a schema.

    Parameters:
        ctx: The import run's context, for the open database.
    """
    import_util.log_debug(ctx, 'Dropping cache tables')
    db = ctx.db
    assert db is not None
    table_names = db.table_names('all', prefix='cache_')
    for table_name in table_names:
        db.drop_table('all', table_name)

    user_search_schema = import_util.read_schema_for_table(ctx, 'user_searches')
    # user_searches.json is packaged with opus_import, so the schema is always found.
    assert user_search_schema is not None
    db.drop_table('perm', 'user_searches')
    db.create_table('perm', 'user_searches', user_search_schema)
