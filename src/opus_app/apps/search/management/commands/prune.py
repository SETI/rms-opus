"""``opus_manage prune``: remove old searches, expired sessions, and orphaned cart rows.

``search_results`` holds every search's results, so it grows with every new search a
user makes. This command bounds it, and removes, in this order and only as much as it
must:

1. **Searches, least recently used first,** until ``search_results`` holds no more than
   ``--max-rows`` rows, and in any case every search unused for ``--unused-days`` days,
   so a busy server is pruned harder than a quiet one. For each, its hash-keyed cache
   entry is deleted first and then its ``user_searches`` row, so that a request
   arriving meanwhile registers the search afresh under a new id; then its rows of
   ``search_results``, in chunks. A search another request is building right now is
   skipped. Rows a removed search left behind, because an earlier prune stopped part
   way, are removed first.
2. **Expired sessions**, through Django's own ``clearsessions``.
3. **Cart rows whose session no longer exists.**

``--stats`` reports the table's size and what a prune would remove, and ``--dry-run``
lists it search by search; neither changes anything. Ids are never reused within a
schema, so the other cache entries keyed by a removed search's id are unreachable and
age out on their own.
"""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any, NamedTuple

from django.conf import settings
from django.contrib.sessions.models import Session
from django.core.cache import cache
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.utils import timezone

from opus_app.apps.search.views import search_number_cache_key

if TYPE_CHECKING:
    from argparse import ArgumentParser
    from collections.abc import Sequence

#: How many days a search may go unused before it is pruned, by default.
DEFAULT_UNUSED_DAYS = 30

#: The rows of ``search_results`` one statement deletes.
DELETE_CHUNK_ROWS = 100_000

#: Every search, least recently used first.
_SEARCHES_SQL = (
    'SELECT id, search_hash, COALESCE(result_count, 0), last_used_at FROM user_searches '
    'ORDER BY last_used_at, id'
)

#: The searches ``search_results`` holds rows of, read through its primary key's prefix.
_RESULT_SEARCH_IDS_SQL = 'SELECT DISTINCT search_id FROM search_results'

#: Every search's id.
_SEARCH_IDS_SQL = 'SELECT id FROM user_searches'

#: Takes a search's row to remove it, unless a search build holds it.
_LOCK_SEARCH_SQL = 'SELECT id FROM user_searches WHERE id = %s FOR UPDATE SKIP LOCKED'

_DELETE_SEARCH_SQL = 'DELETE FROM user_searches WHERE id = %s'

_DELETE_RESULTS_CHUNK_SQL = 'DELETE FROM search_results WHERE search_id = %s LIMIT %s'

_COUNT_RESULTS_SQL = 'SELECT COUNT(*) FROM search_results'

_COUNT_SEARCHES_SQL = 'SELECT COUNT(*) FROM user_searches'

#: The size of ``search_results`` on disk, from the server's own statistics.
_TABLE_BYTES_SQL = (
    'SELECT DATA_LENGTH, INDEX_LENGTH FROM information_schema.TABLES '
    "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'search_results'"
)

#: Cart rows of sessions that no longer exist.
_DELETE_ORPHAN_CARTS_SQL = (
    'DELETE c FROM cart AS c LEFT JOIN django_session AS s ON s.session_key = c.session_id '
    'WHERE s.session_key IS NULL'
)


class StoredSearch(NamedTuple):
    """One ``user_searches`` row, as the pruner chooses among them."""

    search_id: int
    search_hash: bytes
    rows: int
    last_used_at: datetime.datetime


def searches_to_prune(
    searches: Sequence[StoredSearch], max_rows: int, unused_before: datetime.datetime
) -> list[StoredSearch]:
    """Return the searches a prune removes.

    Parameters:
        searches: Every search, least recently used first.
        max_rows: The rows ``search_results`` may hold afterward.
        unused_before: The time before which a search's last use makes it stale.

    Returns:
        The least recently used searches, in order, as far as needed to leave no more
        than `max_rows` rows and no stale search.
    """
    remaining = sum(search.rows for search in searches)
    chosen = []
    for search in searches:
        if remaining <= max_rows and search.last_used_at >= unused_before:
            break
        chosen.append(search)
        remaining -= search.rows
    return chosen


class Command(BaseCommand):
    """Remove old searches, expired sessions, and the cart rows of vanished sessions."""

    help = (
        'Remove the least recently used searches until search_results holds no more '
        'than --max-rows rows and none is unused for --unused-days days, then expired '
        'sessions, then cart rows whose session is gone.'
    )

    def add_arguments(self, parser: ArgumentParser) -> None:
        """Declare the command's options.

        Parameters:
            parser: The command's argument parser.
        """
        parser.add_argument(
            '--max-rows',
            type=int,
            default=settings.SEARCH_RESULTS_MAX_ROWS,
            help='The rows search_results may hold afterward '
            '(default [django] search_results_max_rows, %(default)s)',
        )
        parser.add_argument(
            '--unused-days',
            type=int,
            default=DEFAULT_UNUSED_DAYS,
            help='Prune every search unused for this many days (default %(default)s)',
        )
        mode = parser.add_mutually_exclusive_group()
        mode.add_argument(
            '--stats',
            action='store_true',
            help="Report search_results' size and what a prune would remove; change nothing",
        )
        mode.add_argument(
            '--dry-run',
            action='store_true',
            help='List the searches a prune would remove; change nothing',
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """Prune, or report what a prune would do.

        Parameters:
            *args: Unused.
            **options: The parsed options.

        Raises:
            CommandError: If ``--max-rows`` is negative or ``--unused-days`` below 1.
        """
        max_rows: int = options['max_rows']
        unused_days: int = options['unused_days']
        if max_rows < 0:
            raise CommandError(f'--max-rows must be at least 0, not {max_rows}')
        if unused_days < 1:
            raise CommandError(f'--unused-days must be at least 1, not {unused_days}')
        unused_before = timezone.now() - datetime.timedelta(days=unused_days)
        searches = _read_searches()
        chosen = searches_to_prune(searches, max_rows, unused_before)
        chosen_rows = sum(search.rows for search in chosen)

        if options['stats']:
            self._report_stats(searches, chosen, chosen_rows)
            return
        if options['dry_run']:
            for search in chosen:
                self.stdout.write(
                    f'Would prune search {search.search_id}: {search.rows} rows, '
                    f'last used {search.last_used_at.isoformat()}'
                )
            self.stdout.write(f'Would prune {len(chosen)} searches holding {chosen_rows} rows')
            return

        orphans = _delete_orphan_results()
        self.stdout.write(f'Removed the rows of {orphans} searches already removed')
        pruned = skipped = pruned_rows = 0
        for search in chosen:
            if _delete_search(search):
                pruned += 1
                pruned_rows += search.rows
            else:
                skipped += 1
        self.stdout.write(
            f'Pruned {pruned} searches holding {pruned_rows} rows; skipped {skipped} being built'
        )

        expired = Session.objects.filter(expire_date__lt=timezone.now()).count()
        call_command('clearsessions')
        self.stdout.write(f'Cleared {expired} expired sessions')

        with connection.cursor() as cursor:
            cursor.execute(_DELETE_ORPHAN_CARTS_SQL)
            carts = cursor.rowcount
        self.stdout.write(f'Removed {carts} cart rows of sessions that no longer exist')

    def _report_stats(
        self, searches: Sequence[StoredSearch], chosen: Sequence[StoredSearch], chosen_rows: int
    ) -> None:
        """Write what ``--stats`` reports.

        Parameters:
            searches: Every search.
            chosen: The searches a prune would remove.
            chosen_rows: Their rows.
        """
        with connection.cursor() as cursor:
            cursor.execute(_COUNT_RESULTS_SQL)
            (rows,) = cursor.fetchone()
            cursor.execute(_COUNT_SEARCHES_SQL)
            (search_count,) = cursor.fetchone()
            cursor.execute(_TABLE_BYTES_SQL)
            data_bytes, index_bytes = cursor.fetchone()
        total_bytes = int(data_bytes) + int(index_bytes)
        self.stdout.write(f'search_results rows: {rows}')
        self.stdout.write(f'Searches: {search_count}')
        self.stdout.write(
            f'search_results bytes: {data_bytes} data, {index_bytes} index, '
            f'{total_bytes / rows if rows else 0:.1f} per row'
        )
        self.stdout.write(f'A prune would remove {len(chosen)} searches holding {chosen_rows} rows')
        self.stdout.write(
            f'It would leave {len(searches) - len(chosen)} searches holding '
            f'{sum(search.rows for search in searches) - chosen_rows} rows'
        )


def _read_searches() -> list[StoredSearch]:
    """Return every search, least recently used first."""
    with connection.cursor() as cursor:
        cursor.execute(_SEARCHES_SQL)
        return [
            StoredSearch(int(search_id), bytes(digest), int(rows), _aware(last_used_at))
            for search_id, digest, rows, last_used_at in cursor.fetchall()
        ]


def _aware(value: datetime.datetime) -> datetime.datetime:
    """Return a time read from a ``DATETIME`` column, which holds UTC, as an aware time."""
    if timezone.is_aware(value):
        return value
    return value.replace(tzinfo=datetime.UTC)


def _delete_search(search: StoredSearch) -> bool:
    """Remove one search: its cache entry, its row, then its results in chunks.

    Parameters:
        search: The search.

    Returns:
        False if a search build holds the search's row, which is then left alone.
    """
    with transaction.atomic(), connection.cursor() as cursor:
        cursor.execute(_LOCK_SEARCH_SQL, [search.search_id])
        if cursor.fetchone() is None:
            return False
        cache.delete(search_number_cache_key(search.search_hash))
        cursor.execute(_DELETE_SEARCH_SQL, [search.search_id])
    _delete_results(search.search_id)
    return True


def _delete_results(search_id: int) -> None:
    """Delete a search's rows of ``search_results``, a chunk per statement."""
    with connection.cursor() as cursor:
        while True:
            cursor.execute(_DELETE_RESULTS_CHUNK_SQL, [search_id, DELETE_CHUNK_ROWS])
            if cursor.rowcount < DELETE_CHUNK_ROWS:
                return


def _delete_orphan_results() -> int:
    """Delete the rows of searches whose ``user_searches`` row is gone.

    Returns:
        How many such searches there were.
    """
    with connection.cursor() as cursor:
        cursor.execute(_RESULT_SEARCH_IDS_SQL)
        holding = {int(row[0]) for row in cursor.fetchall()}
        cursor.execute(_SEARCH_IDS_SQL)
        registered = {int(row[0]) for row in cursor.fetchall()}
    orphans = sorted(holding - registered)
    for search_id in orphans:
        _delete_results(search_id)
    return len(orphans)
