"""What identifies a stored search, and the keys and settings its build relies on.

These run with no database. What is worth pinning, and why:

* **Two requests share a search exactly when four hashes of their parts agree.**
  ``user_searches`` keys a search by one SHA-256 digest; the reference it is held to is
  four MD5 hashes, of the selections, query types, units and order, with a ``'NONE'``
  sentinel for an absent part. A digest that merged two searches the four hashes keep
  apart would hand one search's results to the other; one that split a search would
  cost a rebuild and break the reference.
* **Every cache key fits memcached.** A key longer than memcached's limit is refused,
  and a request's own text could make one that long.
* **The search build runs at READ COMMITTED.** The build's ``INSERT ... SELECT`` takes no
  shared locks on what it reads only at that level, which Django's MySQL backend sets
  unless the settings say otherwise.
"""

from __future__ import annotations

import datetime
import hashlib
import json
from typing import Any

import pytest
from django.conf import settings
from django.db import DatabaseError, connection

from opus_app.apps.search.management.commands.prune import StoredSearch, searches_to_prune
from opus_app.apps.search.views import (
    search_hash,
    search_number_cache_key,
    string_choices_cache_key,
)
from opus_app.apps.tools.app_utils import sort_dictionary, strip_numeric_suffix
from opus_app.apps.tools.db_utils import is_lock_timeout_error

#: memcached's limit on a key's length, in bytes.
MEMCACHED_MAX_KEY_BYTES = 250

_ORDER = [['obs_general.time1', 'obs_general.opus_id'], [False, False]]


def _four_hashes(selections: dict[str, Any], extras: dict[str, Any]) -> tuple[str, ...]:
    """Return the reference identity of a search: four MD5 hashes with a ``'NONE'`` sentinel.

    The digest is compared with it pair by pair.
    """

    def md5(text: str) -> str:
        return hashlib.md5(text.encode(), usedforsecurity=False).hexdigest()

    def constrained(values: dict[str, Any]) -> str:
        kept = {
            name: val
            for name, val in values.items()
            if strip_numeric_suffix(name) in selections
            or strip_numeric_suffix(name) + '1' in selections
            or strip_numeric_suffix(name) + '2' in selections
        }
        return md5(json.dumps(sort_dictionary(kept))) if kept else 'NONE'

    selections_hash = md5(json.dumps(sort_dictionary(selections)))
    qtypes_hash = constrained(extras['qtypes']) if 'qtypes' in extras else 'NONE'
    units_hash = constrained(extras['units']) if 'units' in extras else 'NONE'
    order_hash = 'NONE'
    if 'order' in extras and extras['order'][0]:
        order_hash = md5(json.dumps(extras['order']))
    return selections_hash, qtypes_hash, units_hash, order_hash


_TIME = {'obs_general.time1': [-631195181.0], 'obs_general.time2': [568036837.0]}
_PLANET = {'obs_general.planet_id': ['Saturn']}

#: Requests whose identities are compared pairwise: absent, empty and unconstrained
#: query types and units, a different order, and an absent order.
_REQUESTS: list[tuple[dict[str, Any], dict[str, Any]]] = [
    ({}, {'order': _ORDER}),
    ({}, {'order': _ORDER, 'qtypes': {}, 'units': {}}),
    ({}, {'order': [[], []]}),
    ({}, {}),
    (_PLANET, {'order': _ORDER}),
    (_PLANET, {'order': _ORDER, 'qtypes': {'obs_general.time': ['any']}}),
    (_TIME, {'order': _ORDER}),
    (_TIME, {'order': _ORDER, 'qtypes': {'obs_general.time': ['any']}}),
    (_TIME, {'order': _ORDER, 'qtypes': {'obs_general.time': ['all']}}),
    (_TIME, {'order': _ORDER, 'units': {'obs_general.time': ['ymdhms']}}),
    (
        _TIME,
        {
            'order': _ORDER,
            'qtypes': {'obs_general.time': ['any']},
            'units': {'obs_general.time': ['ymdhms']},
        },
    ),
    (_TIME, {'order': [['obs_general.time1'], [True]]}),
    ({**_TIME, **_PLANET}, {'order': _ORDER}),
]


@pytest.mark.parametrize('first', range(len(_REQUESTS)))
@pytest.mark.parametrize('second', range(len(_REQUESTS)))
def test_two_requests_share_a_search_exactly_when_the_four_hashes_agree(
    first: int, second: int
) -> None:
    """The digest equates two requests exactly when the four hashes did."""
    (selections_a, extras_a), (selections_b, extras_b) = _REQUESTS[first], _REQUESTS[second]
    same_before = _four_hashes(selections_a, extras_a) == _four_hashes(selections_b, extras_b)
    same_now = search_hash(selections_a, extras_a) == search_hash(selections_b, extras_b)
    assert same_now == same_before


def test_the_digest_is_a_sha256_of_the_four_strings() -> None:
    """A stored digest is 32 bytes, the width of ``user_searches.search_hash``."""
    assert len(search_hash(_TIME, {'order': _ORDER})) == 32


def test_the_search_number_key_fits_memcached() -> None:
    """The key holds the digest's hex, so its length never depends on the request."""
    key = search_number_cache_key(search_hash(_TIME, {'order': _ORDER}))
    assert len(key.encode()) <= MEMCACHED_MAX_KEY_BYTES
    assert key.startswith(settings.CACHE_SERVER_PREFIX + settings.CACHE_KEY_PREFIX)


def test_the_string_choices_key_fits_memcached_whatever_was_typed() -> None:
    """A partial query far longer than memcached allows still makes a short key."""
    key = string_choices_cache_key('obs_pds.note', 'x' * 10_000, 2**31, 'contains', 100)
    assert len(key.encode()) <= MEMCACHED_MAX_KEY_BYTES
    assert key != string_choices_cache_key('obs_pds.note', 'y', 2**31, 'contains', 100)


def test_django_connects_at_read_committed() -> None:
    """The settings leave Django's MySQL default, the level the search build relies on."""
    connection.get_connection_params()
    # The MySQL backend sets the attribute; the base class does not declare it.
    assert getattr(connection, 'isolation_level', None) == 'read committed'


@pytest.mark.parametrize(
    ('exc', 'expected'),
    [
        (DatabaseError(1205, 'Lock wait timeout exceeded'), True),
        (DatabaseError(3024, 'Query execution was interrupted'), False),
        (DatabaseError(), False),
    ],
    ids=['lock-wait-timeout', 'another-error', 'no-error-number'],
)
def test_a_lock_wait_timeout_is_recognized_by_its_number(
    exc: DatabaseError, expected: bool
) -> None:
    """Only MySQL's error 1205 is a lock wait that timed out."""
    assert is_lock_timeout_error(exc) is expected


_NOW = datetime.datetime(2026, 11, 10, tzinfo=datetime.UTC)


def _search(search_id: int, rows: int, days_ago: int) -> StoredSearch:
    """Return a stored search last used some days before `_NOW`."""
    return StoredSearch(search_id, bytes(32), rows, _NOW - datetime.timedelta(days=days_ago))


_SEARCHES = [_search(1, 40, 60), _search(2, 30, 40), _search(3, 20, 10), _search(4, 10, 0)]


@pytest.mark.parametrize(
    ('max_rows', 'unused_days', 'pruned'),
    [
        (1_000, 30, [1, 2]),
        (1_000, 90, []),
        (25, 90, [1, 2, 3]),
        (30, 30, [1, 2]),
        (0, 90, [1, 2, 3, 4]),
    ],
    ids=['stale-only', 'nothing-stale-or-over', 'over-the-limit', 'stale-covers-limit', 'empty'],
)
def test_the_least_recently_used_go_first_as_far_as_needed(
    max_rows: int, unused_days: int, pruned: list[int]
) -> None:
    """Stale searches always go, and older ones go first until the rows fit."""
    chosen = searches_to_prune(_SEARCHES, max_rows, _NOW - datetime.timedelta(days=unused_days))
    assert [search.search_id for search in chosen] == pruned
