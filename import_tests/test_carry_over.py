"""Sessions and carts carried over from a served schema into the schema a deploy promotes.

Each case copies the main run's schema twice: one copy stands for the schema being
served, holding the sessions and cart rows planted in it, and the other for the new
schema, which lacks one observation the served schema has and holds stale rows of its
own. ``opus_import --carry-over-sessions-from`` runs with the new copy as its target.
What is worth pinning, and why:

* **A cart row moves to the target's observation id, by OPUS ID, and only while its
  session lives.** The served schema's ids are another import's; a row whose observation
  the target lacks, or whose session expired, is dropped and counted.
* **The step empties the target first,** so running it again gives the same result, and
  so a rollback, which is a promotion toward the previous schema, replaces that schema's
  rows rather than adding to them.
* **It depends on neither schema's ``cart`` character sets nor on columns one release's
  ``cart`` has and another's lacks,** since the two schemas belong to different releases.
* **A source it cannot read fails before anything is written.**
"""

from __future__ import annotations

import contextlib
import datetime
from typing import TYPE_CHECKING

import pytest

from import_tests.tools import build_run, golden_io

if TYPE_CHECKING:
    from import_tests.tools.golden_io import DatabaseCredentials

#: The session the served schema's carts belong to, and one that has expired.
_LIVE, _EXPIRED = 'carry-live', 'carry-expired'

#: A session and a cart row the target holds before the carry-over, which it removes.
_STALE = 'carry-stale'

#: The character sets a release's ``cart`` identifiers may be declared in.
_CHARSETS = ('ascii', 'utf8mb4')


def _run_sql(credentials: DatabaseCredentials, schema: str, *statements: str) -> None:
    """Run statements on one connection, with foreign key checks off, and commit.

    The planted cart rows name observation ids the source does not hold, as a schema an
    earlier import numbered would; with the checks off the server takes them.
    """
    with contextlib.closing(golden_io.connect(credentials, schema)) as connection:
        with contextlib.closing(connection.cursor()) as cursor:
            cursor.execute('SET SESSION foreign_key_checks = 0')
            for statement in statements:
                cursor.execute(statement)
        connection.commit()


def _cart(credentials: DatabaseCredentials, schema: str) -> list[tuple[object, ...]]:
    """Return a schema's cart rows, without their own ids, in a stable order."""
    return golden_io.query(
        credentials,
        schema,
        'SELECT session_id, obs_general_id, opus_id, recycled FROM cart ORDER BY session_id, opus_id',
    )


def _sessions(credentials: DatabaseCredentials, schema: str) -> list[str]:
    """Return a schema's session keys, sorted."""
    rows = golden_io.query(credentials, schema, 'SELECT session_key FROM django_session')
    return sorted(str(row[0]) for row in rows)


def _identifier_charset(credentials: DatabaseCredentials, schema: str) -> str:
    """Return the character set a schema's ``cart.session_id`` is declared in."""
    rows = golden_io.query(
        credentials,
        None,
        'SELECT CHARACTER_SET_NAME FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = %s '
        "AND TABLE_NAME = 'cart' AND COLUMN_NAME = 'session_id'",
        [schema],
    )
    return str(rows[0][0])


def _pair(
    main_run: build_run.ImportRun,
    credentials: DatabaseCredentials,
    created_schemas: list[str],
    case: str,
) -> tuple[build_run.SchemaCopy, build_run.SchemaCopy, str, int]:
    """Make the served and the new schema, and plant their rows.

    Returns:
        The served copy, the new copy, the OPUS ID both hold, and its id in the new copy.
    """
    served = build_run.copy_run_schema(main_run, credentials, created_schemas, f'{case}_served')
    new = build_run.copy_run_schema(main_run, credentials, created_schemas, f'{case}_new')
    (kept, kept_id), (gone, _gone_id) = golden_io.query(
        credentials, new.schema, 'SELECT opus_id, id FROM obs_general ORDER BY id LIMIT 2'
    )
    now = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
    later = (now + datetime.timedelta(days=1)).isoformat(sep=' ', timespec='seconds')
    earlier = (now - datetime.timedelta(days=1)).isoformat(sep=' ', timespec='seconds')
    _run_sql(credentials, new.schema, f"DELETE FROM obs_general WHERE opus_id = '{gone}'")
    _run_sql(
        credentials,
        new.schema,
        f"INSERT INTO django_session (session_key, session_data, expire_date) VALUES ('{_STALE}', '', '{later}')",
        'INSERT INTO cart (session_id, obs_general_id, opus_id, recycled) '
        f"VALUES ('{_STALE}', {kept_id}, '{kept}', 0)",
    )
    _run_sql(
        credentials,
        served.schema,
        f"INSERT INTO django_session (session_key, session_data, expire_date) VALUES ('{_LIVE}', 'data', '{later}'), "
        f"('{_EXPIRED}', 'data', '{earlier}')",
        'INSERT INTO cart (session_id, obs_general_id, opus_id, recycled) VALUES '
        f"('{_LIVE}', 900001, '{kept}', 1), ('{_LIVE}', 900002, '{gone}', 0), "
        f"('{_EXPIRED}', 900003, '{kept}', 0)",
    )
    return served, new, str(kept), int(kept_id)


@pytest.mark.parametrize('served_charset', ['same', 'other'])
def test_the_carry_over_moves_live_carts_to_the_targets_ids_and_repeats(
    main_run: build_run.ImportRun,
    db_credentials: DatabaseCredentials,
    created_schemas: list[str],
    served_charset: str,
) -> None:
    """One row carried under the target's id, two dropped and counted, twice over.

    In the ``other`` case the served schema's cart identifiers are in the other
    character set from the target's, and its cart has a column the target's lacks.
    """
    served, new, kept, kept_id = _pair(
        main_run, db_credentials, created_schemas, f'carry_{served_charset}'
    )
    if served_charset == 'other':
        target_charset = _identifier_charset(db_credentials, new.schema)
        other = next(charset for charset in _CHARSETS if charset != target_charset)
        _run_sql(
            db_credentials,
            served.schema,
            f'ALTER TABLE cart MODIFY session_id VARCHAR(80) CHARACTER SET {other} NOT NULL, '
            f'MODIFY opus_id VARCHAR(50) CHARACTER SET {other} NOT NULL, '
            'ADD COLUMN carried_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP',
        )
        assert _identifier_charset(db_credentials, served.schema) == other
    planted = _cart(db_credentials, served.schema)
    for _ in range(2):
        result = new.step('--carry-over-sessions-from', served.schema)
        assert result.returncode == 0, result.stderr[-2000:]
        assert (
            'Carried over 1 sessions and 1 cart rows; dropped 2 of the 3 cart rows' in result.stdout
        )
        assert _sessions(db_credentials, new.schema) == [_LIVE]
        assert _cart(db_credentials, new.schema) == [(_LIVE, kept_id, kept, 1)]
    assert new.errors() == ''
    assert _cart(db_credentials, served.schema) == planted
    assert sorted(_sessions(db_credentials, served.schema)) == [_EXPIRED, _LIVE]


def test_a_source_without_the_tables_fails_before_writing(
    main_run: build_run.ImportRun,
    db_credentials: DatabaseCredentials,
    created_schemas: list[str],
) -> None:
    """The target keeps its rows, and the step exits non-zero naming the failure."""
    served, new, kept, kept_id = _pair(main_run, db_credentials, created_schemas, 'carry_missing')
    _run_sql(db_credentials, served.schema, 'DROP TABLE cart')
    result = new.step('--carry-over-sessions-from', served.schema)
    assert result.returncode != 0
    assert 'Failed to carry sessions and carts over' in new.errors()
    assert _sessions(db_credentials, new.schema) == [_STALE]
    assert _cart(db_credentials, new.schema) == [(_STALE, kept_id, kept, 0)]
