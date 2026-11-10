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

These tests require the following volumes, imported in this order:
COISS_2002,COISS_2008,COISS_2111,COUVIS_0002,GO_0017,VGISS_6210,VGISS_8201,
HSTI1_2003
"""

from __future__ import annotations

import datetime
import threading
import time
from collections.abc import Callable
from typing import Any
from unittest import TestCase

from django.conf import settings
from django.contrib.sessions.models import Session
from django.core.cache import cache
from django.core.management import call_command
from django.db import connection, connections, transaction
from django.utils import timezone

from opus_app.apps.search import views as search_views
from opus_app.apps.search.views import (
    get_search_results,
    search_hash,
    search_number_cache_key,
    url_to_search_params,
)

#: The query string of the search these tests build: Cassini ISS observations of Saturn.
_SEARCH = 'instrument=Cassini+ISS&planet=Saturn'

#: The statement a build writes its results with.
_INSERT_PREFIX = 'INSERT INTO `search_results`'

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

    return run


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

    def test_two_requests_for_one_new_search_build_it_once(self) -> None:
        """The second waits for the first's row lock and reads its count."""
        selections, extras = _search()
        inserts: list[str] = []
        barrier = threading.Barrier(2)

        def slow_insert(execute: Any, sql: str, params: Any, many: bool, context: Any) -> Any:
            if sql.startswith(_INSERT_PREFIX):
                inserts.append(sql)
                # Hold the row lock long enough for the other request to queue on it.
                time.sleep(1)
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
            self.assertTrue(locked.wait(30))
            self.assertIsNone(get_search_results(selections, extras))
        finally:
            release.set()
            holder.join()
        self.assertEqual(_row(search_id), (None, None))

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
            call_command('prune', unused_days=30, max_rows=10**9)

            self.assertIsNone(_row(old.search_id))
            self.assertEqual(_result_rows(old.search_id), 0)
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
