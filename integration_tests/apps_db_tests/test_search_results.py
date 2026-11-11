"""Tests for a search's build into ``search_results``, and for ``opus_manage prune``.

These need the database: the build's serialization is a row lock, and the pruner's work
is rows of ``user_searches``, ``search_results``, ``django_session`` and ``cart``. What
is worth pinning, and why:

* **Concurrent requests for one new search build it once.** The second waits on the
  first's row lock and reads its committed count, so both answer the same count and
  ``search_results`` holds the search's rows once.
* **A build that fails leaves the search unbuilt.** Its rows and its count are written
  in one transaction, so an exception part way rolls both back, and the session's lock
  wait is restored whatever happened.
* **A build waits for another only as long as it is allowed.** A wait that times out
  answers None, which the views turn into an HTTP 500.
* **A pruned search registers afresh.** The cache can still name a search the pruner
  removed; the search is then registered again under a new id.
* **The pruner removes what it should and nothing else.**
* **Selecting two surface geometry bodies keeps an observation once.** An observation
  with geometry for both has a row of the surface geometry table for each, and
  ``search_results`` holds an observation once per search.

These tests require the following volumes, imported in this order:
COISS_2002,COISS_2008,COISS_2111,COUVIS_0002,GO_0017,VGISS_6210,VGISS_8201,
HSTI1_2003
"""

from __future__ import annotations

import contextlib
import datetime
import io
import threading
import time
from collections.abc import Callable, Iterator
from typing import Any
from unittest import TestCase, mock

from django.conf import settings
from django.contrib.sessions.models import Session
from django.core.cache import cache, caches
from django.core.management import CommandError, call_command
from django.db import connection, connections, transaction
from django.db.models import Count
from django.utils import timezone

from opus_app.apps.search import views as search_views
from opus_app.apps.search.management.commands import prune
from opus_app.apps.search.models import ObsSurfaceGeometryTarget
from opus_app.apps.search.views import (
    get_search_results,
    search_hash,
    search_number_cache_key,
    url_to_search_params,
)
from opus_app.apps.tools.import_constants import mult_table

#: The query string of the search these tests build: Cassini ISS observations of Saturn.
_SEARCH = 'instrument=Cassini+ISS&planet=Saturn'

#: The statement a build writes its results with.
_INSERT_PREFIX = 'INSERT INTO `search_results`'

#: The statement a build takes its search's row lock with.
_LOCK_PREFIX = (
    'SELECT result_count, results_built_at, search_hash FROM user_searches WHERE id = %s FOR UPDATE'
)

#: The statement a build records its count with.
_FINISH_PREFIX = 'UPDATE user_searches SET result_count'


def _search(query: str = _SEARCH) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return a query string parsed as the views parse it."""
    from django.http import QueryDict

    selections, extras = url_to_search_params(QueryDict(query))
    assert selections is not None
    assert extras is not None
    return selections, extras


def _row(search_id: int) -> tuple[Any, ...] | None:
    """Return a search's count and build time, or None if it has no row."""
    with connection.cursor() as cursor:
        cursor.execute(
            'SELECT result_count, results_built_at FROM user_searches WHERE id = %s', [search_id]
        )
        row = cursor.fetchone()
    return None if row is None else tuple(row)


def _result_rows(search_id: int) -> int:
    """Return how many rows of ``search_results`` a search holds."""
    with connection.cursor() as cursor:
        cursor.execute('SELECT COUNT(*) FROM search_results WHERE search_id = %s', [search_id])
        return int(cursor.fetchone()[0])


def _lock_wait() -> int:
    """Return this connection's ``innodb_lock_wait_timeout``."""
    with connection.cursor() as cursor:
        cursor.execute('SELECT @@SESSION.innodb_lock_wait_timeout')
        return int(cursor.fetchone()[0])


def _run_in_thread(target: Callable[[], Any]) -> Callable[[], Any]:
    """Return a callable that runs `target` on its own connection and closes it after."""

    def run() -> Any:
        try:
            return target()
        finally:
            connections.close_all()
            caches.close_all()

    return run


@contextlib.contextmanager
def _holding_lock(search_id: int) -> Iterator[None]:
    """Hold a search's row lock on another connection for the duration of the block."""
    locked = threading.Event()
    release = threading.Event()

    def hold_lock() -> None:
        with transaction.atomic(), connection.cursor() as cursor:
            cursor.execute('SELECT id FROM user_searches WHERE id = %s FOR UPDATE', [search_id])
            locked.set()
            release.wait(30)

    holder = threading.Thread(target=_run_in_thread(hold_lock))
    holder.start()
    try:
        assert locked.wait(30)
        yield
    finally:
        release.set()
        holder.join()


def _last_used(search_id: int) -> datetime.datetime:
    """Return a search's ``last_used_at``."""
    with connection.cursor() as cursor:
        cursor.execute('SELECT last_used_at FROM user_searches WHERE id = %s', [search_id])
        last_used: datetime.datetime = cursor.fetchone()[0]
    return last_used


def _plant_results(search_id: int, rows: int) -> None:
    """Write rows of ``search_results`` for a search, whether or not it is registered."""
    with connection.cursor() as cursor:
        cursor.executemany(
            'INSERT INTO search_results (search_id, sort_order, obs_general_id) VALUES (%s, %s, %s)',
            [(search_id, number + 1, number + 1) for number in range(rows)],
        )


def _make_stale(search_id: int) -> None:
    """Mark a search as last used sixty days ago."""
    with connection.cursor() as cursor:
        cursor.execute(
            'UPDATE user_searches SET last_used_at = UTC_TIMESTAMP() - INTERVAL 60 DAY '
            'WHERE id = %s',
            [search_id],
        )


class SearchResultsTests(TestCase):
    """The search build's locking and failure, and the pruner."""

    def setUp(self) -> None:
        """Start from no stored searches, an empty cache and the configured lock wait."""
        with connection.cursor() as cursor:
            cursor.execute('DELETE FROM search_results')
            cursor.execute('DELETE FROM user_searches')
        cache.clear()
        self._timeout = settings.SEARCH_BUILD_TIMEOUT

    def tearDown(self) -> None:
        """Leave no stored search behind, and restore the build's lock wait."""
        settings.SEARCH_BUILD_TIMEOUT = self._timeout
        self.setUp()

    def test_two_selected_bodies_one_observation_has_both_of_count_it_once(self) -> None:
        """The observation is one result, and the count is the observations, not the rows."""
        both = (
            ObsSurfaceGeometryTarget.objects.values('obs_general_id')
            .annotate(bodies=Count('target_name'))
            .filter(bodies__gte=2)
            .order_by('obs_general_id')
            .first()
        )
        assert both is not None
        observation = both['obs_general_id']
        target_ids = sorted(
            ObsSurfaceGeometryTarget.objects.filter(obs_general_id=observation).values_list(
                'target_name', flat=True
            )
        )[:2]
        rows = mult_table('obs_surface_geometry_name.target_name').rows
        labels = ','.join(rows[target_id].label for target_id in target_ids)
        selections, extras = _search(f'surfacegeometrytargetname={labels}')
        built = get_search_results(selections, extras)
        assert built is not None
        search_id, count = built
        expected = (
            ObsSurfaceGeometryTarget.objects.filter(target_name__in=target_ids)
            .values('obs_general_id')
            .distinct()
            .count()
        )
        self.assertEqual(count, expected)
        self.assertEqual(_result_rows(search_id), count)
        with connection.cursor() as cursor:
            cursor.execute(
                'SELECT COUNT(*) FROM search_results WHERE search_id = %s AND obs_general_id = %s',
                [search_id, observation],
            )
            self.assertEqual(cursor.fetchone()[0], 1)

    def test_two_requests_for_one_new_search_build_it_once(self) -> None:
        """The second waits for the first's row lock and reads its count."""
        selections, extras = _search()
        inserts: list[str] = []
        locking = threading.Semaphore(0)
        barrier = threading.Barrier(2)

        def slow_insert(execute: Any, sql: str, params: Any, many: bool, context: Any) -> Any:
            if sql.startswith(_LOCK_PREFIX):
                locking.release()
            if sql.startswith(_INSERT_PREFIX):
                inserts.append(sql)
                # Hold the row lock until the other request has asked for it as well:
                # this request's own lock statement released once, the other's once.
                self.assertTrue(locking.acquire(timeout=30))
                self.assertTrue(locking.acquire(timeout=30))
                time.sleep(0.5)
            return execute(sql, params, many, context)

        def request() -> Any:
            barrier.wait()
            with connection.execute_wrapper(slow_insert):
                return get_search_results(selections, extras)

        results: list[Any] = [None, None]

        def run(index: int) -> None:
            results[index] = _run_in_thread(request)()

        threads = [threading.Thread(target=run, args=(index,)) for index in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertEqual(len(inserts), 1)
        self.assertIsNotNone(results[0])
        self.assertEqual(results[0], results[1])
        search_id, count = results[0]
        self.assertGreater(count, 0)
        stored = _row(search_id)
        assert stored is not None
        self.assertEqual(stored[0], count)
        self.assertEqual(_result_rows(search_id), count)

    def test_a_build_that_fails_leaves_the_search_unbuilt(self) -> None:
        """The rows and the count roll back together, and the lock wait is restored."""
        selections, extras = _search()
        before = _lock_wait()

        def fail_after_insert(execute: Any, sql: str, params: Any, many: bool, context: Any) -> Any:
            if sql.startswith(_FINISH_PREFIX):
                raise RuntimeError('the build dies after writing its rows')
            return execute(sql, params, many, context)

        with connection.execute_wrapper(fail_after_insert), self.assertRaises(RuntimeError):
            get_search_results(selections, extras)

        search_id = search_views.set_user_search_number(selections, extras)
        assert search_id is not None
        self.assertEqual(_row(search_id), (None, None))
        self.assertEqual(_result_rows(search_id), 0)
        self.assertEqual(_lock_wait(), before)

        # The next request builds it.
        results = get_search_results(selections, extras)
        assert results is not None
        self.assertEqual(results.search_id, search_id)
        self.assertEqual(_result_rows(search_id), results.result_count)

    def test_a_build_waiting_too_long_for_another_answers_none(self) -> None:
        """The row lock is held elsewhere past ``search_build_timeout``."""
        selections, extras = _search()
        search_id = search_views.set_user_search_number(selections, extras)
        assert search_id is not None
        settings.SEARCH_BUILD_TIMEOUT = 1
        before = _lock_wait()
        with _holding_lock(search_id):
            self.assertIsNone(get_search_results(selections, extras))
        self.assertEqual(_row(search_id), (None, None))
        self.assertEqual(_lock_wait(), before)

    def test_a_cached_id_that_is_another_searchs_row_registers_afresh(self) -> None:
        """An id a request cached across a reset can be a later search's: it is not used."""
        selections, extras = _search()
        other = get_search_results(*_search('instrument=Cassini+UVIS'))
        assert other is not None
        key = search_number_cache_key(search_hash(selections, extras))
        cache.set(key, (other.search_id, timezone.now().date().isoformat()))

        results = get_search_results(selections, extras)
        assert results is not None
        self.assertNotEqual(results.search_id, other.search_id)
        self.assertEqual(_result_rows(results.search_id), results.result_count)
        self.assertEqual(cache.get(key)[0], results.search_id)

    def test_a_search_is_not_built_inside_a_transaction(self) -> None:
        """Registration and the build each commit on their own."""
        with transaction.atomic(), self.assertRaises(AssertionError):
            get_search_results(*_search())

    def test_a_search_the_cache_names_after_a_prune_registers_afresh(self) -> None:
        """A cached id whose row is gone gives way to a new row and a new build."""
        selections, extras = _search()
        first = get_search_results(selections, extras)
        assert first is not None
        with connection.cursor() as cursor:
            cursor.execute('DELETE FROM search_results WHERE search_id = %s', [first.search_id])
            cursor.execute('DELETE FROM user_searches WHERE id = %s', [first.search_id])

        second = get_search_results(selections, extras)
        assert second is not None
        self.assertNotEqual(second.search_id, first.search_id)
        self.assertEqual(second.result_count, first.result_count)
        self.assertEqual(_result_rows(second.search_id), second.result_count)

    def test_a_search_pruned_while_its_build_waited_registers_afresh(self) -> None:
        """The row is gone when the build takes its lock, so the search starts over."""
        selections, extras = _search()
        first_id = search_views.set_user_search_number(selections, extras)
        assert first_id is not None

        def delete_row() -> None:
            with connection.cursor() as cursor:
                cursor.execute('DELETE FROM user_searches WHERE id = %s', [first_id])

        def prune_before_lock(execute: Any, sql: str, params: Any, many: bool, context: Any) -> Any:
            if sql.endswith('FOR UPDATE') and list(params) == [first_id]:
                # The pruner's delete commits on a connection of its own.
                pruner = threading.Thread(target=_run_in_thread(delete_row))
                pruner.start()
                pruner.join()
            return execute(sql, params, many, context)

        with connection.execute_wrapper(prune_before_lock):
            results = get_search_results(selections, extras)
        assert results is not None
        self.assertNotEqual(results.search_id, first_id)
        self.assertIsNone(_row(first_id))
        self.assertEqual(_result_rows(results.search_id), results.result_count)

    def test_a_cached_search_is_stamped_once_on_a_later_day(self) -> None:
        """A hit on a later day stamps the row, unless a build holds it."""
        selections, extras = _search()
        search_id = search_views.set_user_search_number(selections, extras)
        assert search_id is not None
        key = search_number_cache_key(search_hash(selections, extras))
        today = timezone.now().date().isoformat()

        _make_stale(search_id)
        cache.set(key, (search_id, '2000-01-01'))
        with _holding_lock(search_id):
            self.assertEqual(search_views.set_user_search_number(selections, extras), search_id)
        self.assertEqual(cache.get(key), (search_id, '2000-01-01'))
        stale = _last_used(search_id)

        self.assertEqual(search_views.set_user_search_number(selections, extras), search_id)
        self.assertEqual(cache.get(key), (search_id, today))
        self.assertGreater(_last_used(search_id), stale)

    def test_prune_refuses_a_negative_row_limit_and_fewer_than_one_day(self) -> None:
        """Both bounds are checked before anything is read."""
        with self.assertRaisesRegex(CommandError, '--max-rows'):
            call_command('prune', max_rows=-1, stdout=io.StringIO())
        with self.assertRaisesRegex(CommandError, '--unused-days'):
            call_command('prune', unused_days=0, stdout=io.StringIO())

    def test_prune_dry_run_reports_and_changes_nothing(self) -> None:
        """A dry run reports the table and the prune of a stale search, and keeps it."""
        selections, extras = _search()
        stale = get_search_results(selections, extras)
        assert stale is not None
        _make_stale(stale.search_id)

        output = io.StringIO()
        call_command('prune', dry_run=True, stdout=output)
        self.assertIn(f'search_results rows: {stale.result_count}', output.getvalue())
        self.assertIn('Rows of searches an earlier prune removed: 0', output.getvalue())
        self.assertIn('Searches: 1', output.getvalue())
        self.assertIn('per row', output.getvalue())
        self.assertIn(f'Searches to prune: 1, holding {stale.result_count} rows', output.getvalue())
        self.assertIn('Searches to keep: 0, holding 0 rows', output.getvalue())
        self.assertIn('Dry run: nothing was changed', output.getvalue())
        self.assertNotIn('Pruned', output.getvalue())

        self.assertEqual(_result_rows(stale.search_id), stale.result_count)
        self.assertIsNotNone(_row(stale.search_id))

    def test_prune_reports_the_table_before_it_prunes(self) -> None:
        """A real run reports the same figures first, then what it removed."""
        selections, extras = _search()
        stale = get_search_results(selections, extras)
        assert stale is not None
        _make_stale(stale.search_id)

        output = io.StringIO()
        call_command('prune', stdout=output)
        text = output.getvalue()
        self.assertLess(text.index('Searches to prune: 1'), text.index('Pruned 1 searches'))
        self.assertIsNone(_row(stale.search_id))

    def test_prune_leaves_a_removed_searchs_results_to_the_next_run(self) -> None:
        """A request that read the search just before may still read them; the next run
        removes them, chunk by chunk, along with those of searches removed earlier."""
        stale = get_search_results(*_search())
        assert stale is not None
        _make_stale(stale.search_id)
        orphan_id = stale.search_id + 1000
        _plant_results(orphan_id, 25)
        deletes: list[Any] = []

        def count_deletes(execute: Any, sql: str, params: Any, many: bool, context: Any) -> Any:
            if sql.startswith('DELETE FROM search_results'):
                deletes.append(params[0])
            return execute(sql, params, many, context)

        output = io.StringIO()
        with (
            mock.patch.object(prune, 'DELETE_CHUNK_ROWS', 10),
            connection.execute_wrapper(count_deletes),
        ):
            call_command('prune', unused_days=30, max_rows=10**9, stdout=output)
        self.assertEqual(deletes, [orphan_id] * 3)
        self.assertIn(
            'Removed the results of 1 searches an earlier prune removed', output.getvalue()
        )
        self.assertIn('Pruned 1 searches', output.getvalue())
        self.assertIsNone(_row(stale.search_id))
        self.assertEqual(_result_rows(stale.search_id), stale.result_count)

        call_command('prune', unused_days=30, max_rows=10**9, stdout=io.StringIO())
        self.assertEqual(_result_rows(stale.search_id), 0)
        self.assertEqual(_result_rows(orphan_id), 0)

    def test_prune_leaves_a_search_being_built_or_used_since_it_read_them(self) -> None:
        """A locked row is skipped, and so is one whose last use moved after the read."""
        building_id = search_views.set_user_search_number(*_search('instrument=Cassini+UVIS'))
        assert building_id is not None
        _make_stale(building_id)
        used = get_search_results(*_search())
        assert used is not None
        _make_stale(used.search_id)
        snapshot = prune._read_searches()

        with connection.cursor() as cursor:
            cursor.execute(
                'UPDATE user_searches SET last_used_at = UTC_TIMESTAMP() WHERE id = %s',
                [used.search_id],
            )
        output = io.StringIO()
        with (
            mock.patch.object(prune, '_read_searches', return_value=snapshot),
            _holding_lock(building_id),
        ):
            call_command('prune', unused_days=30, max_rows=10**9, stdout=output)

        self.assertIn('Pruned 0 searches', output.getvalue())
        self.assertIn(
            'skipped 2 whose results were being stored or that were used since', output.getvalue()
        )
        self.assertIsNotNone(_row(building_id))
        self.assertIsNotNone(_row(used.search_id))

    def test_prune_removes_old_searches_expired_sessions_and_orphaned_carts(self) -> None:
        """An old search, an expired session and its cart go; recent ones stay."""
        old_selections, old_extras = _search()
        recent_selections, recent_extras = _search('instrument=Cassini+UVIS')
        old = get_search_results(old_selections, old_extras)
        recent = get_search_results(recent_selections, recent_extras)
        assert old is not None
        assert recent is not None
        old_key = search_number_cache_key(search_hash(old_selections, old_extras))
        self.assertIsNotNone(cache.get(old_key))
        with connection.cursor() as cursor:
            cursor.execute(
                'UPDATE user_searches SET last_used_at = UTC_TIMESTAMP() - INTERVAL 60 DAY '
                'WHERE id = %s',
                [old.search_id],
            )
            cursor.execute('SELECT id, opus_id FROM obs_general ORDER BY id LIMIT 1')
            obs_id, opus_id = cursor.fetchone()

        now = timezone.now()
        Session.objects.filter(session_key__startswith='prune-').delete()
        Session.objects.create(
            session_key='prune-expired',
            session_data='',
            expire_date=now - datetime.timedelta(days=1),
        )
        Session.objects.create(
            session_key='prune-live', session_data='', expire_date=now + datetime.timedelta(days=1)
        )
        with connection.cursor() as cursor:
            for session_key in ('prune-expired', 'prune-live', 'prune-never-existed'):
                cursor.execute(
                    'INSERT INTO cart (session_id, obs_general_id, opus_id, recycled) '
                    'VALUES (%s, %s, %s, 0)',
                    [session_key, obs_id, opus_id],
                )
        try:
            call_command('prune', unused_days=30, max_rows=10**9, stdout=io.StringIO())

            self.assertIsNone(_row(old.search_id))
            self.assertIsNone(cache.get(old_key))
            self.assertIsNotNone(_row(recent.search_id))
            self.assertEqual(_result_rows(recent.search_id), recent.result_count)
            self.assertEqual(
                sorted(
                    Session.objects.filter(session_key__startswith='prune-').values_list(
                        'session_key', flat=True
                    )
                ),
                ['prune-live'],
            )
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT session_id FROM cart WHERE session_id LIKE 'prune-%%' ORDER BY session_id"
                )
                self.assertEqual([row[0] for row in cursor.fetchall()], ['prune-live'])
        finally:
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM cart WHERE session_id LIKE 'prune-%%'")
            Session.objects.filter(session_key__startswith='prune-').delete()
