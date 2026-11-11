"""The mult fields of a finished schema: pruned, renamed in place, and ranked.

Finalization deletes every value of an unpinned field that no observation holds, keeps
every value of a pinned one, and ranks every field; ``--update-mult-info`` applies a
column's ``mult_overrides`` to a finished schema and ranks the field again. Each case
that changes the schema runs against a copy of the main run's, with a configuration and
logs of its own. Which values the observations hold is read here with a query per
column, independently of the one-scan-per-table reading finalization does.
"""

from __future__ import annotations

import functools
import logging
from typing import TYPE_CHECKING, Any

import pdslogger
import pytest

from import_tests.tools import build_run, golden_io
from opus_import import importdb, mult_fields
from opus_import.cli import _create_argument_parser
from opus_import.config_data import GROUP_FORM_TYPES
from opus_import.context import ImportContext
from opus_import.steps import do_finalize_mult, do_update_mult_info
from opus_import.steps.do_import_mult import PINNED_ABSENT_ID

if TYPE_CHECKING:
    from collections.abc import Callable

    from import_tests.tools.golden_io import DatabaseCredentials

#: The unpinned field the planted value is added to.
_PLANTED_FIELD = 'obs_general.target_name'

#: The value planted in it, which no import produces.
_PLANTED_VALUE = 'PLANTED BY THE MULT TEST'

#: The pinned field whose unused values must survive finalization.
_PINNED_FIELD = 'obs_general.instrument_id'


def _field_id(credentials: DatabaseCredentials, schema: str, name: str) -> int:
    """Return a mult field's id in a schema."""
    rows = golden_io.query(
        credentials,
        schema,
        'SELECT `field_id` FROM `mult_field` WHERE `qualified_name` = %s',
        [name],
    )
    return int(rows[0][0])


def _values(credentials: DatabaseCredentials, schema: str, name: str) -> dict[str, tuple[Any, ...]]:
    """Return a field's rows, ``(id, label, disp_rank)`` keyed by value."""
    rows = golden_io.query(
        credentials,
        schema,
        'SELECT `value`, `id`, `label`, `disp_rank` FROM `mult` WHERE `field_id` = %s',
        [_field_id(credentials, schema, name)],
    )
    return {str(row[0]): tuple(row[1:]) for row in rows}


def _unreferenced(credentials: DatabaseCredentials, schema: str) -> dict[str, list[int]]:
    """Return the ids of every unpinned field that no observation column holds.

    Parameters:
        credentials: How to reach the server.
        schema: The schema.

    Returns:
        The unreferenced ids, keyed by field, for each field that has any.
    """
    tables = set(golden_io.list_tables(credentials, schema))
    found: dict[str, list[int]] = {}
    for name, column in mult_fields.packaged_mult_columns().items():
        if column.pinned:
            continue
        field_id = _field_id(credentials, schema, name)
        table, field = column.table_name, column.entry['field_name']
        if table not in tables:
            holds = 'FALSE'
        elif column.entry['field_type'] == 'mult_list':
            holds = (
                f'EXISTS (SELECT 1 FROM `{table}` AS `t`, JSON_TABLE(`t`.`{field}`, '
                "'$[*]' COLUMNS (`v` INT PATH '$')) AS `j` WHERE `j`.`v` = `m`.`id`)"
            )
        else:
            holds = f'EXISTS (SELECT 1 FROM `{table}` AS `t` WHERE `t`.`{field}` = `m`.`id`)'
        rows = golden_io.query(
            credentials,
            schema,
            f'SELECT `m`.`id` FROM `mult` AS `m` WHERE `m`.`field_id` = %s AND NOT {holds}',
            [field_id],
        )
        if rows:
            found[name] = sorted(int(row[0]) for row in rows)
    return found


def _plant(credentials: DatabaseCredentials, schema: str, bundle: str) -> int:
    """Give one observation of a bundle a target-name value no import produces.

    Returns:
        The planted value's id.
    """
    field_id = _field_id(credentials, schema, _PLANTED_FIELD)
    (top,) = golden_io.query(
        credentials, schema, 'SELECT MAX(`id`) FROM `mult` WHERE `field_id` = %s', [field_id]
    )[0]
    planted = int(top) + 1
    golden_io.execute(
        credentials,
        schema,
        'INSERT INTO `mult` (`field_id`, `id`, `value`, `label`, `display`) '
        'VALUES (%s, %s, %s, %s, %s)',
        [field_id, planted, _PLANTED_VALUE, _PLANTED_VALUE.title(), 'Y'],
    )
    golden_io.execute(
        credentials,
        schema,
        'UPDATE `obs_general` SET `target_name` = JSON_ARRAY(%s) WHERE `bundle_id` = %s '
        'ORDER BY `id` LIMIT 1',
        [planted, bundle],
    )
    return planted


def test_the_main_run_holds_no_unreferenced_value(
    main_run: build_run.ImportRun, db_credentials: DatabaseCredentials
) -> None:
    """Finalization left no value of an unpinned field that no observation holds."""
    assert _unreferenced(db_credentials, main_run.schema) == {}


def test_a_pinned_field_keeps_the_values_no_observation_holds(
    main_run: build_run.ImportRun, db_credentials: DatabaseCredentials
) -> None:
    """Every entry of a pinned list is a row, used or not."""
    column = mult_fields.packaged_mult_columns()[_PINNED_FIELD]
    stored = _values(db_credentials, main_run.schema, _PINNED_FIELD)

    assert {str(option[1]) for option in column.entry['mult_options']} == set(stored)


def test_the_ranks_of_every_field_count_from_one(
    main_run: build_run.ImportRun, db_credentials: DatabaseCredentials
) -> None:
    """Each field's ranks are 1 to its number of values, and each group's likewise."""
    for table, rank in (('mult', 'disp_rank'), ('mult_group', 'group_rank')):
        rows = golden_io.query(
            db_credentials,
            main_run.schema,
            f'SELECT `field_id`, COUNT(*), MIN(`{rank}`), MAX(`{rank}`), '
            f'COUNT(DISTINCT `{rank}`) FROM `{table}` GROUP BY `field_id`',
        )
        assert rows
        for field_id, count, low, high, distinct in rows:
            assert (low, high, distinct) == (1, count, count), (table, field_id)


def test_a_value_only_the_reimported_bundle_held_is_gone_afterward(
    main_run: build_run.ImportRun,
    db_credentials: DatabaseCredentials,
    created_schemas: list[str],
) -> None:
    """Importing a bundle again and finalizing drops a value only its old rows held.

    The planted value is held by one of the bundle's observations until the bundle is
    imported again, which writes the observation's own target names back; the
    finalization that follows deletes the value, and a pinned field's unused values stay.
    """
    copy = build_run.copy_run_schema(main_run, db_credentials, created_schemas, 'mult_reimport')
    bundle = build_run.reimport_bundle_id(main_run)
    planted = _plant(db_credentials, copy.schema, bundle)
    pinned_before = _values(db_credentials, copy.schema, _PINNED_FIELD)
    assert _PLANTED_VALUE in _values(db_credentials, copy.schema, _PLANTED_FIELD)

    imported = copy.step(*build_run.IMPORT_ARGS, bundle)
    assert imported.returncode == 0, imported.stderr
    for closing in build_run.closing_steps(copy.paths.config_file):
        assert closing.returncode == 0, closing.stderr
    assert copy.errors() == ''

    after = _values(db_credentials, copy.schema, _PLANTED_FIELD)
    assert _PLANTED_VALUE not in after
    assert planted not in {row[0] for row in after.values()}
    assert _values(db_credentials, copy.schema, _PINNED_FIELD) == pinned_before
    assert _unreferenced(db_credentials, copy.schema) == {}


def test_the_finalize_after_a_delete_drops_the_values_only_that_bundle_held(
    main_run: build_run.ImportRun,
    db_credentials: DatabaseCredentials,
    created_schemas: list[str],
) -> None:
    """An append's deletion invalidates the mult step, and the next finalize runs it.

    The deletion alone leaves the bundle's values in ``mult``; the ``--finalize`` that
    follows removes those no other bundle holds.
    """
    copy = build_run.copy_run_schema(main_run, db_credentials, created_schemas, 'mult_delete')
    bundle = build_run.reimport_bundle_id(main_run)
    _plant(db_credentials, copy.schema, bundle)

    assert copy.step('--delete-bundles', bundle).returncode == 0
    assert _PLANTED_VALUE in _values(db_credentials, copy.schema, _PLANTED_FIELD)
    assert _unreferenced(db_credentials, copy.schema) != {}

    for closing in build_run.closing_steps(copy.paths.config_file):
        assert closing.returncode == 0, closing.stderr
    assert copy.errors() == ''
    assert _PLANTED_VALUE not in _values(db_credentials, copy.schema, _PLANTED_FIELD)
    assert _unreferenced(db_credentials, copy.schema) == {}


@functools.cache
def _logger() -> pdslogger.PdsLogger:
    """Return a quiet logger; a `pdslogger.PdsLogger` name can be created once a process."""
    logger = pdslogger.PdsLogger('opus_import_mult_tests')
    logger.set_level(logging.CRITICAL)
    return logger


def _run_in_process(
    credentials: DatabaseCredentials, schema: str, step: Callable[[ImportContext], bool]
) -> bool:
    """Run one step in this process against a schema, as ``opus_import`` would.

    Parameters:
        credentials: How to reach the server.
        schema: The schema.
        step: The step.

    Returns:
        What the step returned.
    """
    ctx = ImportContext(args=_create_argument_parser().parse_args([]), logger=_logger())
    ctx.db = importdb.get_db(
        'MySQL',
        credentials.host,
        '',
        schema,
        credentials.user,
        credentials.password,
        mult_form_types=GROUP_FORM_TYPES,
        logger=_logger(),
    )
    try:
        return step(ctx)
    finally:
        ctx.db.close()


def _with_overrides(name: str, overrides: list[dict[str, Any]]) -> dict[str, Any]:
    """Return the packaged mult columns with one column given ``mult_overrides``."""
    columns = dict(mult_fields.packaged_mult_columns())
    column = columns[name]
    columns[name] = mult_fields.MultColumn(
        column.qualified_name, column.table_name, {**column.entry, 'mult_overrides': overrides}
    )
    return columns


def test_finalize_drops_what_an_override_empties_and_an_unused_pinned_absent_row(
    main_run: build_run.ImportRun,
    db_credentials: DatabaseCredentials,
    created_schemas: list[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The groups an override empties go in the same finalization, and so does a pinned
    field's absent row no observation holds; the rows its list gives stay."""
    copy = build_run.copy_run_schema(main_run, db_credentials, created_schemas, 'mult_groups')
    field_id = _field_id(db_credentials, copy.schema, _PLANTED_FIELD)
    ((group, count),) = golden_io.query(
        db_credentials,
        copy.schema,
        'SELECT `grouping`, COUNT(*) FROM `mult` WHERE `field_id` = %s AND `grouping` IS NOT NULL '
        'GROUP BY `grouping` ORDER BY COUNT(*), `grouping` LIMIT 1',
        [field_id],
    )
    moved = [
        str(row[0])
        for row in golden_io.query(
            db_credentials,
            copy.schema,
            'SELECT `value` FROM `mult` WHERE `field_id` = %s AND `grouping` = %s',
            [field_id, group],
        )
    ]
    assert len(moved) == count
    pinned_id = _field_id(db_credentials, copy.schema, _PINNED_FIELD)
    golden_io.execute(
        db_credentials,
        copy.schema,
        'INSERT INTO `mult` (`field_id`, `id`, `value`, `label`, `display`) '
        "VALUES (%s, %s, '', 'N/A', 'Y')",
        [pinned_id, PINNED_ABSENT_ID],
    )
    pinned_before = _values(db_credentials, copy.schema, _PINNED_FIELD)
    overrides = [{'value': value, 'grouping': 'Moved by the mult test'} for value in moved]
    columns = _with_overrides(_PLANTED_FIELD, overrides)
    monkeypatch.setattr(mult_fields, 'packaged_mult_columns', lambda: columns)

    assert _run_in_process(db_credentials, copy.schema, do_finalize_mult.finalize_mult)

    groups = {
        str(row[0])
        for row in golden_io.query(
            db_credentials,
            copy.schema,
            'SELECT `grouping` FROM `mult_group` WHERE `field_id` = %s',
            [field_id],
        )
    }
    assert group not in groups
    assert 'Moved by the mult test' in groups
    pinned_after = _values(db_credentials, copy.schema, _PINNED_FIELD)
    assert '' in pinned_before
    assert set(pinned_after) == set(pinned_before) - {''}


def test_update_mult_info_renames_a_value_in_place(
    main_run: build_run.ImportRun,
    db_credentials: DatabaseCredentials,
    created_schemas: list[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An override renames a value on a finished schema: new label, same id, new rank.

    The step runs in this process, against a copy, with the target-name column's schema
    entry given a ``mult_overrides`` entry, as a release that edits the schema file
    would give it.
    """
    copy = build_run.copy_run_schema(main_run, db_credentials, created_schemas, 'mult_rename')
    before = _values(db_credentials, copy.schema, _PLANTED_FIELD)
    value = 'SATURN'
    renamed = '!Renamed Saturn'
    assert before[value][2] != 1

    columns = _with_overrides(_PLANTED_FIELD, [{'value': value, 'label': renamed}])
    monkeypatch.setattr(mult_fields, 'packaged_mult_columns', lambda: columns)
    assert _run_in_process(db_credentials, copy.schema, do_update_mult_info.update_mult_info)

    after = _values(db_credentials, copy.schema, _PLANTED_FIELD)
    assert after[value][0] == before[value][0]
    assert after[value][1] == renamed
    assert after[value][2] == 1
    assert sorted(row[2] for row in after.values()) == list(range(1, len(after) + 1))
