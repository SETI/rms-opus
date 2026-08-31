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
from opus_import import config_targets, import_util, importdb
from opus_import.cli import _create_argument_parser
from opus_import.config_data import GROUP_FORM_TYPES
from opus_import.context import ImportContext

if TYPE_CHECKING:
    from collections.abc import Iterator

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
def import_db(db_credentials: DatabaseCredentials) -> Iterator[ImportDBSuper]:
    """Open the pipeline's own database object against a schema of this test's own.

    Yields:
        The database object. Its schema is created on the way in and dropped on the way
        out, so each test starts from nothing.
    """
    schema = fixture_layout.schema_name(os.getpid(), _SQL_CASE)
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
        import_prefix='imp_',
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
    import_db.create_table('perm', 'obs_general', schema)
    assert import_db.table_exists('perm', 'obs_general')


def test_upsert_updates_the_row_it_finds(import_db: ImportDBSuper) -> None:
    """Writing the same key twice updates the row rather than adding a second one.

    This is the update half of the upsert the documented re-import mode runs on, and the
    half a database that starts empty never reaches.
    """
    ctx = _import_context()
    schema = import_util.read_schema_for_table(ctx, _UPSERT_TABLE)
    assert schema is not None
    import_db.create_table('perm', _UPSERT_TABLE, schema)

    first = {_UPSERT_KEY: 'OPUS_GENERAL', 'description': 'first', 'parent': 'OPUS'}
    second = {_UPSERT_KEY: 'OPUS_GENERAL', 'description': 'second', 'parent': 'OPUS'}
    import_db.upsert_rows('perm', _UPSERT_TABLE, _UPSERT_KEY, [first])
    import_db.upsert_rows('perm', _UPSERT_TABLE, _UPSERT_KEY, [second])

    quoted = import_db.quote_identifier
    rows = import_db.general_select(
        f'{quoted("description")} FROM {quoted(_UPSERT_TABLE)} WHERE {quoted(_UPSERT_KEY)} = %s',
        ['OPUS_GENERAL'],
    )
    assert [row[0] for row in rows] == ['second']
