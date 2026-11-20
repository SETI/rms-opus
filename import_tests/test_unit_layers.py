"""The layers under the end-to-end run: name mangling, target tables, generated SQL.

The first two need no database. The third does, and that is why it lives here rather than
beside the pure-unit suite: the point of testing the MySQL backend against a real server
is that nothing else can say the statements it generates are valid SQL for the schema the
import actually builds.
"""

from __future__ import annotations

import functools
import json
import logging
import os
from typing import TYPE_CHECKING

import pdslogger
import pytest

from import_tests.tools import fixture_layout, golden_io
from opus_import import bundle_registry, config_targets, import_util, importdb
from opus_import.cli import _create_argument_parser
from opus_import.config_data import GROUP_FORM_TYPES
from opus_import.context import ImportContext
from opus_import.importdb import mysql
from opus_import.schema_version import SCHEMA_VERSION, SCHEMA_VERSION_TABLE
from opus_import.steps import do_generation, do_import, do_import_tables

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    from import_tests.tools.golden_io import DatabaseCredentials
    from opus_import.importdb.super import ImportDBSuper

#: The suffix of the schema this module's SQL tests create for themselves. It carries the
#: same process id as the suite's other schemas, so a stray one is recognizable and
#: cannot collide with another worktree's.
_SQL_CASE = 'sql'

#: A small packaged table whose natural key the schema declares unique, which is what an
#: upsert needs: MySQL updates rather than inserts only when a unique key collides.
_UPSERT_TABLE = 'contexts'
_UPSERT_KEY = 'name'


@pytest.mark.parametrize(
    ('target_name', 'expected'),
    [
        ('S RINGS', 's____rings'),
        ('1995 S 3/S18', '1995____s____3___s18'),
        ('S7_1980S13', 's7_1980s13'),
    ],
)
def test_surface_geometry_table_name_is_a_safe_identifier(target_name: str, expected: str) -> None:
    """A target name becomes a table-name suffix with nothing a schema cannot hold.

    Surface geometry gets one table per target, so a target whose name carries a space or
    a slash decides whether the import can create its table at all. The substitutions are
    reversible rather than merely safe -- a space and a slash get different runs of
    underscores -- because the name is read back out of the table name.
    """
    assert import_util.table_name_for_sfc_target(target_name) == expected


def test_target_name_round_trips_through_its_encoding() -> None:
    """Every target OPUS knows survives the encoding its table name is built from.

    The encoding lower-cases, because a table name does, so the round trip returns the
    name in lower case. Anything else coming back means two targets could collide on one
    surface geometry table.
    """
    broken = [
        name
        for name in config_targets.TARGET_NAME_INFO
        if import_util.decode_target_name(import_util.encode_target_name(name)) != name.lower()
    ]
    assert broken == []


def test_every_target_names_a_planet_group_that_exists() -> None:
    """No target points at a planet group the search form does not define.

    A target whose group is missing would be shown under a heading with no label and no
    place in the ordering.
    """
    missing = sorted(
        {
            planet
            for planet, _class, _pretty in config_targets.TARGET_NAME_INFO.values()
            if planet is not None and planet not in config_targets.PLANET_GROUP_MAPPING
        }
    )
    assert missing == []


def test_every_mapped_spelling_resolves_to_a_known_target() -> None:
    """Every instrument spelling folds onto a target the target table describes."""
    unresolved = sorted(
        {
            target
            for target in config_targets.TARGET_NAME_MAPPING.values()
            if target not in config_targets.TARGET_NAME_INFO
        }
    )
    assert unresolved == []


def test_every_target_class_is_a_value_the_general_table_accepts() -> None:
    """No target carries a class ``obs_general`` would reject when it is stored.

    The column is an enumeration built from the schema's own options, so a class added to
    the target table and not to the schema fails at import time on the first observation
    that uses it.
    """
    schema_path = (
        fixture_layout.REPO_ROOT / 'src' / 'opus_import' / 'table_schemas' / 'obs_general.json'
    )
    schema = json.loads(schema_path.read_text(encoding='utf-8'))
    options = next(
        column['mult_options'] for column in schema if column.get('field_name') == 'target_class'
    )
    allowed = {str(option[1]) for option in options}
    unknown = sorted(
        {
            target_class
            for _planet, target_class, _pretty in config_targets.TARGET_NAME_INFO.values()
            if target_class not in allowed
        }
    )
    assert unknown == []


@functools.cache
def _import_context() -> ImportContext:
    """Return a context carrying the pipeline's own default arguments and a quiet logger.

    Cached because a `pdslogger.PdsLogger` name can be created only once per process, and
    every test that reads a packaged schema needs a context to log through.
    """
    logger = pdslogger.PdsLogger('opus_import.import_tests')
    logger.set_level(logging.CRITICAL)
    return ImportContext(args=_create_argument_parser().parse_args([]), logger=logger)


@pytest.fixture
def import_db(
    db_credentials: DatabaseCredentials, created_schemas: list[str]
) -> Iterator[ImportDBSuper]:
    """Open the pipeline's own database object against a schema of this test's own.

    Yields:
        The database object. Its schema is created on the way in and dropped on the way
        out, so each test starts from nothing. It is registered with the session's own
        list as well, so that the one rule -- every schema a session creates is dropped
        when the session ends -- covers this schema too if this fixture's teardown never
        runs.
    """
    schema = fixture_layout.schema_name(os.getpid(), _SQL_CASE)
    if schema not in created_schemas:
        created_schemas.append(schema)
    golden_io.execute(db_credentials, None, f'DROP DATABASE IF EXISTS `{schema}`')
    db = importdb.get_db(
        'MySQL',
        db_credentials.host,
        '',
        schema,
        db_credentials.user,
        db_credentials.password,
        mult_form_types=GROUP_FORM_TYPES,
        # A logger is not optional in practice: the backend records a table it created in
        # its own name cache inside its logging branch, so an unlogged connection answers
        # `table_exists` from a cache that never learned about it.
        logger=_import_context().logger,
    )
    yield db
    golden_io.execute(db_credentials, None, f'DROP DATABASE IF EXISTS `{schema}`')


def test_the_widest_packaged_schema_creates_a_real_table(import_db: ImportDBSuper) -> None:
    """The generated ``CREATE TABLE`` for ``obs_general`` is accepted by the server.

    That schema carries every column type the generator can produce, so a type it spells
    wrongly is a syntax error here and nowhere a holdings-free unit test could see it.
    """
    ctx = _import_context()
    schema = import_util.read_schema_for_table(ctx, 'obs_general')
    assert schema is not None
    import_db.create_table('obs_general', schema)
    assert import_db.table_exists('obs_general')


def test_upsert_updates_the_row_it_finds(import_db: ImportDBSuper) -> None:
    """Writing the same key twice updates the row rather than adding a second one.

    This is the update half of the upsert the documented re-import mode runs on, and the
    half a database that starts empty never reaches.
    """
    ctx = _import_context()
    schema = import_util.read_schema_for_table(ctx, _UPSERT_TABLE)
    assert schema is not None
    import_db.create_table(_UPSERT_TABLE, schema)

    first = {_UPSERT_KEY: 'OPUS_GENERAL', 'description': 'first', 'parent': 'OPUS'}
    second = {_UPSERT_KEY: 'OPUS_GENERAL', 'description': 'second', 'parent': 'OPUS'}
    import_db.upsert_rows(_UPSERT_TABLE, _UPSERT_KEY, [first])
    import_db.upsert_rows(_UPSERT_TABLE, _UPSERT_KEY, [second])

    quoted = import_db.quote_identifier
    rows = import_db.general_select(
        f'{quoted("description")} FROM {quoted(_UPSERT_TABLE)} WHERE {quoted(_UPSERT_KEY)} = %s',
        ['OPUS_GENERAL'],
    )
    assert [row[0] for row in rows] == ['second']


def _earlier_version_schema(credentials: DatabaseCredentials, schema: str) -> None:
    """Create what an earlier version's import left: obs_general a base table with a
    child referencing it, and a version row without the generation columns."""
    for statement in (
        'CREATE TABLE obs_general (id INT UNSIGNED PRIMARY KEY, bundle_id VARCHAR(20))',
        'CREATE TABLE obs_pds (obs_general_id INT UNSIGNED PRIMARY KEY, '
        'FOREIGN KEY (obs_general_id) REFERENCES obs_general (id))',
        'CREATE TABLE schema_version (version INT, state VARCHAR(20))',
        'INSERT INTO obs_general VALUES (1, "B_1")',
        'INSERT INTO obs_pds VALUES (1)',
        f'INSERT INTO schema_version VALUES ({SCHEMA_VERSION - 1}, "ready")',
    ):
        golden_io.execute(credentials, schema, statement)


def test_an_earlier_versions_schema_holds_no_generation_and_is_erased_whole(
    import_db: ImportDBSuper, db_credentials: DatabaseCredentials
) -> None:
    """Its version row is read as no generation rather than failing the read, the erase
    drops its obs_general base table, and a fresh import then creates the view in its
    place."""
    schema = import_db.db_schema
    _earlier_version_schema(db_credentials, schema)
    ctx = _import_context()
    ctx.db = import_db
    import_db.forget_table_names()
    assert do_generation.read_generation_state(import_db) is None
    do_import_tables.delete_all_opus_tables(ctx)
    assert golden_io.query(db_credentials, schema, 'SHOW FULL TABLES') == []
    table_schema = import_util.read_schema_for_table(ctx, 'obs_general')
    assert table_schema is not None
    import_db.create_table('obs_general', table_schema)
    assert sorted(golden_io.query(db_credentials, schema, 'SHOW FULL TABLES')) == [
        ('obs_general', 'VIEW'),
        ('obs_general_rows', 'BASE TABLE'),
    ]


def test_a_child_row_of_a_pending_only_observation_is_found_by_its_bundle(
    import_db: ImportDBSuper, db_credentials: DatabaseCredentials
) -> None:
    """The view hides a generation it does not serve, and the helper asks the base table,
    so a child row of an observation only a pending generation holds is reported."""
    schema = import_db.db_schema
    for statement in (
        'CREATE TABLE obs_general_rows (id INT UNSIGNED PRIMARY KEY, bundle_id VARCHAR(20), '
        'added_generation INT UNSIGNED)',
        'CREATE VIEW obs_general AS SELECT id, bundle_id FROM obs_general_rows '
        'WHERE added_generation <= 1',
        'CREATE TABLE obs_pds (obs_general_id INT UNSIGNED PRIMARY KEY)',
        'INSERT INTO obs_general_rows VALUES (7, "B_1", 2)',
        'INSERT INTO obs_pds VALUES (7)',
    ):
        golden_io.execute(db_credentials, schema, statement)
    holding = golden_io.tables_holding_bundle(
        db_credentials, schema, ['obs_general', 'obs_pds'], 'B_1'
    )
    assert holding == {'obs_general', 'obs_pds'}


def _context(db: ImportDBSuper) -> ImportContext:
    """Return a context of the pipeline's default arguments, opened on `db`."""
    ctx = ImportContext(
        args=_create_argument_parser().parse_args([]), logger=_import_context().logger
    )
    ctx.db = db
    return ctx


def test_a_requeue_returns_a_failed_bundle_to_the_queue(import_db: ImportDBSuper) -> None:
    """``--requeue``'s statements against the server: the hold it takes on a ``failed``
    bundle, the delete beneath it (a schema with no observation tables has nothing to
    delete), and the move to ``pending``."""
    ctx = _context(import_db)
    bundle_registry.create_registry(ctx)
    (row,) = bundle_registry.plan_ranges(0, [('COISS_2002', 10)], 1)
    import_db.insert_rows(bundle_registry.BUNDLE_REGISTRY_TABLE, [row])
    quoted = import_db.quote_identifier
    import_db.update_row(
        bundle_registry.BUNDLE_REGISTRY_TABLE,
        {'state': bundle_registry.BUNDLE_FAILED},
        f'{quoted("bundle_id")}=%s',
        ['COISS_2002'],
    )
    assert do_import.requeue_bundles(ctx, ['COISS_2002'])
    assert dict(bundle_registry.registered_bundles(ctx)) == {
        'COISS_2002': bundle_registry.BUNDLE_PENDING
    }


def test_the_next_id_of_a_table_that_holds_rows_is_set(import_db: ImportDBSuper) -> None:
    """The reset the search tables' re-creation issues when ``user_searches`` held rows,
    which the fixture's never does: the next row takes the id given."""
    ctx = _context(import_db)
    schema = import_util.read_schema_for_table(ctx, 'user_searches')
    assert schema is not None
    import_db.create_table('user_searches', schema)
    row = {'search_hash': b'\x00' * 32, 'last_used_at': '2026-11-20 00:00:00'}
    import_db.insert_row('user_searches', row)
    import_db.set_next_id('user_searches', 500)
    import_db.insert_row('user_searches', {**row, 'search_hash': b'\x01' * 32})
    quoted = import_db.quote_identifier
    ids = import_db.general_select(f'{quoted("id")} FROM {quoted("user_searches")} ORDER BY 1')
    assert [found[0] for found in ids] == [1, 500]


def test_the_index_space_budget_reads_the_servers_directories(
    import_db: ImportDBSuper, tmp_path: Path
) -> None:
    """On a server sharing this computer the budget is a free space the query and the
    directories give; on another, there is none."""
    budget = import_db.index_space_budget(str(tmp_path))
    if import_db.db_hostname in mysql.LOCAL_HOSTS:
        assert budget is not None
        assert budget > 0
    else:
        assert budget is None


@pytest.mark.parametrize(
    ('pending', 'action', 'problem'),
    [
        (None, do_generation.CHECK_REBUILD, None),
        (None, do_generation.CHECK_CONTINUE, 'has no pending generation to continue'),
        (2, do_generation.CHECK_REBUILD, 'generation 2 of'),
        (2, do_generation.CHECK_CONTINUE, None),
        (None, do_generation.CHECK_SWITCH, 'no pending generation is ready'),
    ],
)
def test_the_deploy_chains_checks_read_a_real_schema(
    import_db: ImportDBSuper, pending: int | None, action: str, problem: str | None
) -> None:
    """What ``opus_import --check`` asks -- the version row, the generation lock, the
    live writers and the auxiliary tables -- against the server, on a schema with no
    ``import_process`` table."""
    ctx = _context(import_db)
    schema = import_util.read_schema_for_table(ctx, SCHEMA_VERSION_TABLE)
    assert schema is not None
    import_db.create_table(SCHEMA_VERSION_TABLE, schema)
    import_db.insert_row(
        SCHEMA_VERSION_TABLE,
        {
            'version': SCHEMA_VERSION,
            'state': 'ready',
            'generation': 1,
            'pending_generation': pending,
            'pending_state': None if pending is None else 'writing',
            'revertible': 0,
        },
    )
    found = do_generation.generation_problem(import_db, action)
    if problem is None:
        assert found is None
    else:
        assert found is not None
        assert problem in found


def test_a_bounded_wait_rename_restores_the_sessions_lock_wait(import_db: ImportDBSuper) -> None:
    """The rename runs under the lowered ``lock_wait_timeout``, and the session's own value
    is put back after it."""
    ctx = _context(import_db)
    schema = import_util.read_schema_for_table(ctx, _UPSERT_TABLE)
    assert schema is not None
    import_db.create_table(_UPSERT_TABLE, schema)
    before = import_db.general_select('@@SESSION.lock_wait_timeout')
    renamed = f'{_UPSERT_TABLE}_renamed'
    import_db.rename_tables_atomically(
        [(_UPSERT_TABLE, renamed)], lock_wait_timeout_s=5, attempts=1
    )
    assert import_db.table_exists(renamed)
    assert import_db.general_select('@@SESSION.lock_wait_timeout') == before
