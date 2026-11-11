"""Reset the tables the web application keeps its searches in, and flush its cache.

An import changes what a search returns, so every search the web application has built
is stale once the run finishes. ``user_searches``, one row per distinct search, and
``search_results``, every search's ordered results, are dropped and created again empty
from their schema files.

The web application's cache trusts its entries, which name searches by their rows' ids.
So the re-created ``user_searches`` hands out ids above every id the old one held, and
an entry a request in flight writes after the reset names no row rather than another
search's; and every reset is followed by a flush of that cache, in a subprocess of its
own, since the cache's configuration is the web application's.
"""

from __future__ import annotations

import subprocess  # nosec B404 - runs this interpreter on a fixed module
import sys
from typing import TYPE_CHECKING

from opus_import import import_util

if TYPE_CHECKING:
    from opus_import.context import ImportContext

#: The tables `reset_search_tables` re-creates, each from its packaged schema.
SEARCH_TABLES = ('user_searches', 'search_results')

#: The command that empties the web application's cache. It reads ``OPUS_CONFIG``, which
#: the import's own environment carries.
CACHE_FLUSH_COMMAND = (sys.executable, '-m', 'opus_app.clear_django_cache')


class CacheFlushError(RuntimeError):
    """The web application's cache could not be flushed after the search tables' reset."""


def reset_search_tables(ctx: ImportContext) -> None:
    """Drop and re-create the search tables empty, then flush the web cache.

    Parameters:
        ctx: The import run's context, for the open database.

    Raises:
        CacheFlushError: If the flush exits with a nonzero status.
    """
    import_util.log_debug(ctx, 'Resetting the search tables')
    db = ctx.db
    assert db is not None
    last_id = (
        db.find_column_max('user_searches', 'id') if db.table_exists('user_searches') else None
    )
    for table_name in SEARCH_TABLES:
        schema = import_util.read_schema_for_table(ctx, table_name)
        # The search tables' schemas are packaged with opus_import, so each is found.
        assert schema is not None
        db.drop_table(table_name)
        db.create_table(table_name, schema)
    if last_id is not None:
        db.set_next_id('user_searches', int(last_id) + 1)

    if db.read_only:
        import_util.log_debug(ctx, '[SIM] Flushed the web cache')
        return
    flush = subprocess.run(  # nosec B603 - this interpreter and a fixed module
        CACHE_FLUSH_COMMAND, capture_output=True, text=True, check=False
    )
    if flush.returncode != 0:
        raise CacheFlushError(
            f'Flushing the web cache exited with status {flush.returncode}: {flush.stderr.strip()}'
        )
    import_util.log_debug(ctx, 'Flushed the web cache')
