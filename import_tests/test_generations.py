"""The incremental update of a served schema, one import generation at a time.

Each case starts from a copy of the main run's finished schema, which serves generation
1, and runs real ``opus_import`` invocations against it: ``--begin-generation``, the
re-import of one bundle and the drop of another into the pending generation, the closing
invocations, then the switch, the revert, the purge or the abandon. What a request would
see is read through the ``obs_general`` view, as the web application reads it; what the
import wrote is read from the base table, ``obs_general_rows``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

from import_tests.tools import build_run, golden_io
from opus_import import generations
from opus_import.import_fault import IMPORT_FAULT_ENV_VAR
from opus_import.steps import do_generation

if TYPE_CHECKING:
    from import_tests.tools.golden_io import DatabaseCredentials

#: The cart session the cases plant a row for.
_SESSION = 'generations'

#: The value planted in an unpinned field for an observation of the dropped bundle only.
_PLANTED_VALUE = 'PLANTED BY THE GENERATION TEST'

#: The unpinned field the value is planted in, a list column with a junction table.
_PLANTED_FIELD = 'obs_general.target_name'

#: The closing invocations of an update, in order.
_CLOSING = (build_run.AUX_ARGS, build_run.VALIDATE_ARGS, build_run.VERSION_ARGS)


def _served(credentials: DatabaseCredentials, schema: str) -> list[tuple[Any, ...]]:
    """Return every row the ``obs_general`` view shows, ordered by id."""
    return [
        tuple(row)
        for row in golden_io.query(credentials, schema, 'SELECT * FROM obs_general ORDER BY id')
    ]


def _served_without_ids(
    credentials: DatabaseCredentials, schema: str, leaving_out: str
) -> list[tuple[Any, ...]]:
    """Return the view's rows less their ids and one bundle's rows, ordered by OPUS id."""
    columns = [
        name
        for name, _type in golden_io.table_columns(credentials, schema, 'obs_general')
        if name != 'id' and name not in generations.GENERATION_COLUMNS
    ]
    listed = ', '.join(f'`{name}`' for name in columns)
    rows = golden_io.query(
        credentials,
        schema,
        f'SELECT {listed} FROM obs_general WHERE bundle_id <> %s ORDER BY opus_id',  # nosec B608
        [leaving_out],
    )
    return [tuple(row) for row in rows]


def _served_count(credentials: DatabaseCredentials, schema: str, bundle: str) -> int:
    """Return how many observations of a bundle the view shows."""
    query = 'SELECT COUNT(*) FROM obs_general WHERE bundle_id = %s'
    return int(golden_io.query(credentials, schema, query, [bundle])[0][0])


def _state(credentials: DatabaseCredentials, schema: str) -> tuple[Any, ...]:
    """Return the version row's generation columns."""
    columns = ', '.join(generations.STATE_COLUMNS)
    return tuple(golden_io.query(credentials, schema, f'SELECT {columns} FROM schema_version')[0])


def _view_has_condition(credentials: DatabaseCredentials, schema: str) -> bool:
    """Return whether the obs_general view selects rows by a condition."""
    rows = golden_io.query(
        credentials,
        None,
        'SELECT VIEW_DEFINITION FROM information_schema.VIEWS '
        "WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'obs_general'",
        [schema],
    )
    return ' where ' in str(rows[0][0]).lower()


def _cart_target(credentials: DatabaseCredentials, schema: str) -> list[int]:
    """Return the observations the planted session's cart names."""
    rows = golden_io.query(
        credentials, schema, 'SELECT obs_general_id FROM cart WHERE session_id = %s', [_SESSION]
    )
    return [int(row[0]) for row in rows]


def _plant_cart_row(credentials: DatabaseCredentials, schema: str, bundle: str) -> int:
    """Put a cart row in for a bundle's first observation, returning its id."""
    (obs_id, opus_id) = golden_io.query(
        credentials,
        schema,
        'SELECT id, opus_id FROM obs_general WHERE bundle_id = %s ORDER BY id LIMIT 1',
        [bundle],
    )[0]
    golden_io.execute(
        credentials,
        schema,
        'INSERT INTO cart (session_id, obs_general_id, opus_id, recycled) VALUES (%s, %s, %s, 0)',
        [_SESSION, obs_id, opus_id],
    )
    return int(obs_id)


def _plant_value(credentials: DatabaseCredentials, schema: str, bundle: str) -> None:
    """Give one observation of a bundle a target name no import produces, in its list and
    its junction table alike."""
    (field_id,) = golden_io.query(
        credentials,
        schema,
        'SELECT field_id FROM mult_field WHERE qualified_name = %s',
        [_PLANTED_FIELD],
    )[0]
    (top,) = golden_io.query(
        credentials, schema, 'SELECT MAX(id) FROM mult WHERE field_id = %s', [field_id]
    )[0]
    planted = int(top) + 1
    golden_io.execute(
        credentials,
        schema,
        'INSERT INTO mult (field_id, id, value, label, display) VALUES (%s, %s, %s, %s, %s)',
        [field_id, planted, _PLANTED_VALUE, _PLANTED_VALUE.title(), 'Y'],
    )
    (obs_id,) = golden_io.query(
        credentials,
        schema,
        'SELECT id FROM obs_general WHERE bundle_id = %s ORDER BY id LIMIT 1',
        [bundle],
    )[0]
    golden_io.execute(
        credentials,
        schema,
        'UPDATE obs_general_rows SET target_name = JSON_ARRAY_APPEND(target_name, %s, %s) '
        'WHERE id = %s',
        ['$', planted, obs_id],
    )
    golden_io.execute(
        credentials,
        schema,
        'INSERT INTO obs_general_target_name (mult_id, obs_general_id) VALUES (%s, %s)',
        [planted, obs_id],
    )


def _planted_value_kept(credentials: DatabaseCredentials, schema: str) -> bool:
    """Return whether ``mult`` still holds the planted value."""
    rows = golden_io.query(
        credentials, schema, 'SELECT 1 FROM mult WHERE value = %s', [_PLANTED_VALUE]
    )
    return len(rows) > 0


def _drop_bundle(run: build_run.ImportRun, reimported: str) -> str:
    """Return the bundle the update drops: the last of the run's bundles that is neither
    the re-imported one nor a Galileo bundle, whose OPUS IDs other bundles share."""
    return [
        bundle for bundle in run.bundles if bundle != reimported and not bundle.startswith('GO_')
    ][-1]


def _base_tables(credentials: DatabaseCredentials, schema: str) -> dict[str, str]:
    """Return the golden text of every observation table, the registry and the version row."""
    tables = [
        table
        for table in golden_io.list_tables(credentials, schema)
        if table.startswith('obs_') or table in ('import_bundle', 'schema_version', 'cart')
    ]
    return {table: golden_io.serialize_table(credentials, schema, table) for table in tables}


def _ok(result: build_run.StepResult) -> None:
    """Fail with the invocation's output unless it exited cleanly."""
    assert result.returncode == 0, (result.arguments, result.stdout[-3000:], result.stderr[-3000:])


def _update(copy: build_run.SchemaCopy, reimported: str, dropped: str) -> None:
    """Begin a generation, re-import one bundle, drop another, and close it."""
    _ok(copy.step('--begin-generation'))
    _ok(copy.step(*build_run.IMPORT_ARGS, reimported))
    _ok(copy.step('--delete-bundles', dropped))
    for arguments in _CLOSING:
        _ok(copy.step(*arguments))


@pytest.fixture
def bundles(main_run: build_run.ImportRun) -> tuple[str, str]:
    """Return the re-imported bundle and the dropped one."""
    reimported = build_run.reimport_bundle_id(main_run)
    return reimported, _drop_bundle(main_run, reimported)


def test_an_update_is_hidden_until_the_switch_and_whole_after_it(
    main_run: build_run.ImportRun,
    db_credentials: DatabaseCredentials,
    created_schemas: list[str],
    bundles: tuple[str, str],
) -> None:
    """Begin, re-import, drop and close; then switch, revert, switch again, and purge."""
    reimported, dropped = bundles
    copy = build_run.copy_run_schema(main_run, db_credentials, created_schemas, 'generation')
    schema = copy.schema
    old_cart_target = _plant_cart_row(db_credentials, schema, reimported)
    _plant_value(db_credentials, schema, dropped)
    before = _served(db_credentials, schema)
    reimported_count = _served_count(db_credentials, schema, reimported)
    dropped_count = _served_count(db_credentials, schema, dropped)
    assert reimported_count > 0
    assert dropped_count > 0
    assert not _view_has_condition(db_credentials, schema)

    _update(copy, reimported, dropped)
    assert copy.errors() == ''

    # Before the switch, nothing a request reads has changed.
    assert _view_has_condition(db_credentials, schema)
    assert _served(db_credentials, schema) == before
    assert _served_count(db_credentials, schema, reimported) == reimported_count
    assert _served_count(db_credentials, schema, dropped) == dropped_count
    assert _cart_target(db_credentials, schema) == [old_cart_target]
    assert _state(db_credentials, schema) == (
        main_run_version(db_credentials, schema),
        'ready',
        1,
        2,
        generations.PENDING_READY,
        0,
    )

    _ok(copy.step('--switch-generation'))
    after = _served_without_ids(db_credentials, schema, dropped)
    # The served rows are the full import's, ids aside, less the dropped bundle's.
    assert after == _served_without_ids(db_credentials, main_run.schema, dropped)
    assert _served_count(db_credentials, schema, reimported) == reimported_count
    assert _served_count(db_credentials, schema, dropped) == 0
    (new_target,) = _cart_target(db_credentials, schema)
    assert new_target != old_cart_target
    owner = golden_io.query(
        db_credentials, schema, 'SELECT bundle_id FROM obs_general WHERE id = %s', [new_target]
    )
    assert [tuple(row) for row in owner] == [(reimported,)]
    assert _state(db_credentials, schema)[2:] == (2, None, None, 1)
    # Switching again reports the switch done.
    _ok(copy.step('--switch-generation'))

    # A revert serves the previous generation again, cart and all.
    _ok(copy.step('--revert-generation'))
    assert _served(db_credentials, schema) == before
    assert _cart_target(db_credentials, schema) == [old_cart_target]
    assert _state(db_credentials, schema)[2:] == (1, 2, generations.PENDING_READY, 0)
    _ok(copy.step('--switch-generation'))
    assert _served_without_ids(db_credentials, schema, dropped) == after
    assert _cart_target(db_credentials, schema) == [new_target]

    # The purge leaves only the served generation's rows, and the values only they used go.
    assert _planted_value_kept(db_credentials, schema)
    _ok(copy.step('--purge-generations'))
    assert copy.errors() == ''
    retired = golden_io.query(
        db_credentials,
        schema,
        'SELECT COUNT(*) FROM obs_general_rows WHERE removed_generation IS NOT NULL',
    )
    assert int(retired[0][0]) == 0
    total = golden_io.query(db_credentials, schema, 'SELECT COUNT(*) FROM obs_general_rows')
    assert int(total[0][0]) == len(_served(db_credentials, schema))
    assert not _planted_value_kept(db_credentials, schema)
    assert not _view_has_condition(db_credentials, schema)
    assert _state(db_credentials, schema)[2:] == (2, None, None, 0)
    # A revert after the purge has started is refused.
    refused = copy.step('--revert-generation')
    assert refused.returncode == do_generation.GENERATION_REFUSED_EXIT_STATUS
    assert 'no switch is revertible' in refused.stdout


def main_run_version(credentials: DatabaseCredentials, schema: str) -> int:
    """Return the schema's version, which an update never changes."""
    return int(golden_io.query(credentials, schema, 'SELECT version FROM schema_version')[0][0])


def test_an_abandoned_generation_leaves_the_base_tables_as_they_were(
    main_run: build_run.ImportRun,
    db_credentials: DatabaseCredentials,
    created_schemas: list[str],
    bundles: tuple[str, str],
) -> None:
    """Abandoning before the switch restores every observation table and the registry."""
    reimported, dropped = bundles
    copy = build_run.copy_run_schema(main_run, db_credentials, created_schemas, 'abandon')
    before = _base_tables(db_credentials, copy.schema)
    _ok(copy.step('--begin-generation'))
    _ok(copy.step(*build_run.IMPORT_ARGS, reimported))
    _ok(copy.step('--delete-bundles', dropped))
    _ok(copy.step(*build_run.AUX_ARGS))
    assert _base_tables(db_credentials, copy.schema) != before
    _ok(copy.step('--abandon-generation'))
    assert _base_tables(db_credentials, copy.schema) == before
    leftovers = [
        table
        for table in golden_io.list_tables(db_credentials, copy.schema)
        if table.endswith(('__new', '__prev'))
    ]
    assert leftovers == []
    assert not _view_has_condition(db_credentials, copy.schema)


def test_an_interrupted_switch_completes_when_run_again(
    main_run: build_run.ImportRun,
    db_credentials: DatabaseCredentials,
    created_schemas: list[str],
    bundles: tuple[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Killed after each of its steps in turn, the switch is completed by running it again."""
    reimported, dropped = bundles
    copy = build_run.copy_run_schema(main_run, db_credentials, created_schemas, 'switch_fault')
    _plant_cart_row(db_credentials, copy.schema, reimported)
    _update(copy, reimported, dropped)
    for step in range(1, len(do_generation.SWITCH_STEPS) + 1):
        monkeypatch.setenv(IMPORT_FAULT_ENV_VAR, f'{do_generation.SWITCH_FAULT_SITE}:{step}')
        assert copy.step('--switch-generation').returncode != 0
        assert _state(db_credentials, copy.schema)[3] == 2, step
        monkeypatch.delenv(IMPORT_FAULT_ENV_VAR)
        _ok(copy.step('--switch-generation'))
        assert _state(db_credentials, copy.schema)[2:] == (2, None, None, 1)
        assert _served_count(db_credentials, copy.schema, dropped) == 0
        swapped = golden_io.list_tables(db_credentials, copy.schema)
        assert {'param_info__prev', 'partables__prev', 'table_names__prev'} <= set(swapped)
        assert not any(table.endswith('__new') for table in swapped)
        (target,) = _cart_target(db_credentials, copy.schema)
        assert (
            golden_io.query(
                db_credentials,
                copy.schema,
                'SELECT COUNT(*) FROM obs_general WHERE id = %s',
                [target],
            )[0][0]
            == 1
        )
        _ok(copy.step('--revert-generation'))
