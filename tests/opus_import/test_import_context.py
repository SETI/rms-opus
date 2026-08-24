"""The `ImportContext` that carries one import run's state, and the log bound to it.

Several properties matter and are pinned here. The log prefixes each message with the
position the run has reached, so a line read out of an import log names the observation
that produced it. A message that would otherwise repeat once per index row is logged
once. The mult caches keep their two lifetimes -- per bundle for the tables being
filled, per run for the record of which import tables were created empty -- and a
cached table is served as the list itself, because callers add values by appending to
it. And two contexts share nothing, so a second run in the same process neither sees
nor corrupts the first one's caches.
"""

import argparse
import ast
import inspect
import textwrap
from typing import Any

import pytest

from opus_import import import_util
from opus_import.cli import _make_warning_handler
from opus_import.context import ImportContext
from opus_import.obs.obs_base import ObsBase
from opus_import.steps import do_import, do_import_mult

from .conftest import RecordingLogger, make_context


@pytest.fixture
def ctx() -> ImportContext:
    """Return a context with a recording logger and no database."""
    return make_context()


def _messages(ctx: ImportContext, level: str) -> list[str]:
    """Return the messages the context's recording logger holds at `level`."""
    logger: RecordingLogger = ctx.logger  # type: ignore[assignment]
    return logger.messages_at(level)


def test_a_context_starts_with_empty_state() -> None:
    """Nothing has happened yet: no position, no bad data, and empty caches."""
    ctx = ImportContext(args=argparse.Namespace(), logger=RecordingLogger())

    assert ctx.db is None
    assert ctx.current_bundle_id is None
    assert ctx.current_index_row_number is None
    assert ctx.current_primary_filespec is None
    assert ctx.import_has_bad_data is False
    assert ctx.try_cart_later is False
    assert ctx.python_warning_list == []
    assert ctx.max_table_id_cache == {}
    assert ctx.mult_table_cache == {}
    assert ctx.created_import_mult_tables == set()
    assert ctx.modified_mult_tables == set()


def test_two_contexts_share_no_state() -> None:
    """Every mutable field is per-context, so two runs in one process cannot collide."""
    first = make_context()
    second = make_context()

    first.mult_table_cache['mult_obs_general_mission_id'] = [{'id': 0}]
    first.created_import_mult_tables.add('mult_obs_general_mission_id')
    first.modified_mult_tables.add('mult_obs_general_mission_id')
    first.max_table_id_cache['obs_general'] = 17
    first.log.nonrepeating_error('a bad thing')

    assert second.mult_table_cache == {}
    assert second.created_import_mult_tables == set()
    assert second.modified_mult_tables == set()
    assert second.max_table_id_cache == {}
    assert second.import_has_bad_data is False
    assert second.logged_import_errors == []
    assert _messages(second, 'error') == []


@pytest.mark.parametrize(('bundle', 'row', 'filespec', 'expected'), [
    (None, None, None, ''),
    (None, 7, 'a/b.LBL', ''),
    ('COISS_2002', None, None, '[COISS_2002] '),
    ('COISS_2002', 7, None, '[COISS_2002 index row 7] '),
    ('COISS_2002', 7, 'a/b.LBL', '[COISS_2002 index row 7 "a/b.LBL"] '),
    ('COISS_2002', None, 'a/b.LBL', '[COISS_2002 "a/b.LBL"] '),
])
def test_a_message_names_the_position_the_run_is_at(
        ctx: ImportContext, bundle: str | None, row: int | None,
        filespec: str | None, expected: str) -> None:
    """The prefix grows as the run learns where it is, and is absent between bundles."""
    ctx.current_bundle_id = bundle
    ctx.current_index_row_number = row
    ctx.current_primary_filespec = filespec

    ctx.log.info('something happened')

    assert _messages(ctx, 'info') == [expected + 'something happened']


@pytest.mark.parametrize('level', ['error', 'warning', 'info', 'debug'])
def test_each_level_logs_at_its_own_level(ctx: ImportContext, level: str) -> None:
    """`ImportLog` maps one method per level onto the underlying logger."""
    getattr(ctx.log, level)('a message')

    assert _messages(ctx, level) == ['a message']


def test_an_error_marks_the_import_as_having_bad_data(ctx: ImportContext) -> None:
    """`import_has_bad_data` is what aborts the run unless errors are being ignored."""
    ctx.log.error('a bad thing')

    assert ctx.import_has_bad_data is True


@pytest.mark.parametrize('level', ['warning', 'info', 'debug'])
def test_nothing_below_error_marks_the_import_as_bad(
        ctx: ImportContext, level: str) -> None:
    """Only errors abort a run; a warning is reported and the import continues."""
    getattr(ctx.log, level)('a message')

    assert ctx.import_has_bad_data is False


def test_a_nonrepeating_error_is_logged_once_however_the_position_changes(
        ctx: ImportContext) -> None:
    """Deduplication is on the message alone, which keeps a per-row fault to one line.

    A fault shared by every row of an index would otherwise be logged once per row, and
    the position prefix would make every one of those lines distinct.
    """
    ctx.current_bundle_id = 'COISS_2002'
    for row in range(1, 4):
        ctx.current_index_row_number = row
        ctx.log.nonrepeating_error('the same fault')

    assert _messages(ctx, 'error') == ['[COISS_2002 index row 1] the same fault']
    assert ctx.import_has_bad_data is True


def test_a_nonrepeating_warning_is_logged_once(ctx: ImportContext) -> None:
    """Warnings deduplicate the same way, and still do not mark the import bad."""
    ctx.log.nonrepeating_warning('the same fault')
    ctx.log.nonrepeating_warning('the same fault')
    ctx.log.nonrepeating_warning('a different fault')

    assert _messages(ctx, 'warning') == ['the same fault', 'a different fault']
    assert ctx.import_has_bad_data is False


def test_an_unknown_target_name_is_reported_once_and_names_the_file_to_edit(
        ctx: ImportContext) -> None:
    """The message tells the operator where to add the target, and repeats no further."""
    ctx.log.unknown_target_name('PLUTO')
    ctx.log.unknown_target_name('PLUTO')

    assert _messages(ctx, 'error') == [
        'Unknown TARGET_NAME "PLUTO" - edit config_targets/target_name_info.py']
    assert ctx.import_has_bad_data is True


@pytest.mark.parametrize(('func_name', 'method_name', 'level'), [
    ('log_error', 'error', 'error'),
    ('log_warning', 'warning', 'warning'),
    ('log_info', 'info', 'info'),
    ('log_debug', 'debug', 'debug'),
    ('log_nonrepeating_error', 'nonrepeating_error', 'error'),
    ('log_nonrepeating_warning', 'nonrepeating_warning', 'warning'),
    ('log_unknown_target_name', 'unknown_target_name', 'error'),
])
def test_the_step_spelling_and_the_object_spelling_are_one_operation(
        func_name: str, method_name: str, level: str) -> None:
    """``import_util.log_x(ctx, m)`` and ``ctx.log.x(m)`` do the same thing.

    The step modules use the first spelling and the obs classes the second, so a
    divergence between them would make a message's text or level depend on which layer
    produced it.
    """
    through_function = make_context()
    through_method = make_context()

    getattr(import_util, func_name)(through_function, 'a message')
    getattr(through_method.log, method_name)('a message')

    assert _messages(through_function, level) == _messages(through_method, level)
    assert len(_messages(through_function, level)) == 1
    assert through_function.import_has_bad_data == through_method.import_has_bad_data


def test_an_obs_object_logs_through_its_own_context() -> None:
    """An obs class reports through the context it was constructed with, and no other."""
    first = make_context()
    second = make_context()
    obs = ObsBase(first, bundle='COISS_2002')

    obs._log_nonrepeating_error('a bad field')
    obs._log_nonrepeating_warning('a questionable field')
    obs._log_warning('a note')
    obs._log_unknown_target_name('PLUTO')

    assert _messages(first, 'error') == [
        'a bad field',
        'Unknown TARGET_NAME "PLUTO" - edit config_targets/target_name_info.py']
    assert _messages(first, 'warning') == ['a questionable field', 'a note']
    assert second.logger.messages == []


def test_an_obs_object_prefixes_its_messages_with_the_run_position() -> None:
    """An obs message names the observation being imported, as a step message does."""
    ctx = make_context()
    ctx.current_bundle_id = 'COISS_2002'
    ctx.current_index_row_number = 42
    obs = ObsBase(ctx, bundle='COISS_2002')

    obs._log_nonrepeating_error('a bad field')

    assert _messages(ctx, 'error') == ['[COISS_2002 index row 42] a bad field']


def test_accumulated_python_warnings_are_reported_and_cleared() -> None:
    """Reporting empties the list and marks the import bad; an empty list logs nothing."""
    ctx = make_context()
    ctx.python_warning_list = ['first warning', 'second warning']

    assert import_util.log_accumulated_warnings(ctx, 'table import of x.LBL') is True

    assert _messages(ctx, 'error') == ['Warnings found during table import of x.LBL:',
                                       '  first warning', '  second warning']
    assert ctx.python_warning_list == []
    assert ctx.import_has_bad_data is True

    assert import_util.log_accumulated_warnings(ctx, 'table import of y.LBL') is False
    assert len(_messages(ctx, 'error')) == 3


def test_the_warning_handler_follows_the_list_across_a_report() -> None:
    """The handler reads the list off the context, so collection survives a report.

    Reporting the accumulated warnings replaces the list with a fresh one. A handler
    that had closed over the original list would go on appending to the discarded one
    and every later warning would be lost.
    """
    ctx = make_context()
    handler = _make_warning_handler(ctx)

    def warn(text: str) -> None:
        handler(UserWarning(text), UserWarning, 'a.py', 1, None, None)

    warn('before')
    assert ctx.python_warning_list == ['before']

    import_util.log_accumulated_warnings(ctx, 'the first table')
    assert ctx.python_warning_list == []

    warn('after')
    assert ctx.python_warning_list == ['after']


#: A preprogrammed mult column, the one shape `read_or_create_mult_table` can serve
#: without a database: the values are in the schema instead of in a table. The row is a
#: 7-tuple because a schema's `mult_options` carries no `aliases` field -- all 410 rows
#: in the packaged table_schemas are this shape, and an 8-tuple would drive the branch
#: that reads a row back from SQL instead.
_MULT_COLUMN = {'mult_options': [(0, 'COISS', 'Cassini ISS', 0, 'Y', None, None)]}


def _mult_context() -> ImportContext:
    """Return a context the mult code can run against, with its messages suppressed."""
    return make_context(args=argparse.Namespace(import_suppress_mult_messages=True))


def test_a_mult_table_is_converted_once_and_then_served_from_the_context() -> None:
    """The second read returns the cached list itself, so callers can append to it.

    `update_mult_table` adds a value by appending to the list this returns, and the
    appended value has to be visible to the next reader and to the eventual write-out.
    """
    ctx = _mult_context()

    first = do_import_mult.read_or_create_mult_table(ctx, 'mult_obs_general_x',
                                                     _MULT_COLUMN)
    second = do_import_mult.read_or_create_mult_table(ctx, 'mult_obs_general_x',
                                                      _MULT_COLUMN)

    assert first is second
    assert ctx.mult_table_cache['mult_obs_general_x'] is first
    assert [row['value'] for row in first] == ['COISS']
    # A schema row carries no aliases field, so the conversion supplies None. The length
    # check is what pins the branch: `aliases is None` alone would still hold for an
    # 8-tuple ending in None, which is the SQL-read shape this fixture must not have.
    assert len(_MULT_COLUMN['mult_options'][0]) == 7
    assert first[0]['aliases'] is None


def test_reading_a_mult_table_marks_it_modified_only_the_first_time() -> None:
    """A preprogrammed table has to be written out once, not once per read."""
    ctx = _mult_context()

    do_import_mult.read_or_create_mult_table(ctx, 'mult_obs_general_x', _MULT_COLUMN)
    assert ctx.modified_mult_tables == {'mult_obs_general_x'}

    ctx.modified_mult_tables = set()
    do_import_mult.read_or_create_mult_table(ctx, 'mult_obs_general_x', _MULT_COLUMN)

    assert ctx.modified_mult_tables == set()


def test_one_context_s_mult_cache_is_invisible_to_another() -> None:
    """Two runs in one process do not serve each other stale mult tables."""
    first = _mult_context()
    second = _mult_context()

    first_rows = do_import_mult.read_or_create_mult_table(first, 'mult_obs_general_x',
                                                          _MULT_COLUMN)
    second_rows = do_import_mult.read_or_create_mult_table(second, 'mult_obs_general_x',
                                                           _MULT_COLUMN)

    assert first_rows is not second_rows
    assert second.modified_mult_tables == {'mult_obs_general_x'}


def test_dumping_writes_only_the_modified_tables_and_clears_the_created_record() -> None:
    """A table that has been written out is no longer an empty table to skip reading."""
    ctx = _mult_context()
    written: list[tuple[str, str]] = []

    class _FakeDatabase:
        """Records the writes `dump_import_mult_tables` makes."""

        @staticmethod
        def convert_raw_to_namespace(namespace: str, raw_table_name: str) -> str:
            return f'{namespace}_{raw_table_name}'

        @staticmethod
        def upsert_rows(namespace: str, raw_table_name: str, key_name: str,
                        rows: list[dict[str, Any]]) -> None:
            written.append((namespace, raw_table_name))

    ctx.db = _FakeDatabase()
    do_import_mult.read_or_create_mult_table(ctx, 'mult_obs_general_x', _MULT_COLUMN)
    ctx.mult_table_cache['mult_obs_general_untouched'] = []
    ctx.created_import_mult_tables |= {'mult_obs_general_x',
                                       'mult_obs_general_untouched'}

    do_import_mult.dump_import_mult_tables(ctx)

    assert written == [('import', 'mult_obs_general_x')]
    assert ctx.created_import_mult_tables == {'mult_obs_general_untouched'}


def test_the_bundle_loop_clears_the_per_bundle_caches_and_not_the_per_run_one() -> None:
    """Which cache each loop resets is what keeps mult ids stable across a run.

    `created_import_mult_tables` records the import mult tables created empty and not
    yet written; clearing it per bundle would make the second bundle read an empty
    import table instead of the populated permanent one. `mult_table_cache` and
    `modified_mult_tables` are the opposite: carrying them across bundles would write
    one bundle's values into another's tables. Driving the two loops needs holdings and
    a database, so this reads the source instead -- but it fails if either reset is
    dropped or moved to the wrong loop.
    """
    assigned = {}
    for func in (do_import.import_one_bundle, do_import.do_import_steps):
        tree = ast.parse(textwrap.dedent(inspect.getsource(func)))
        assigned[func.__name__] = {
            ast.unparse(target)
            for node in ast.walk(tree) if isinstance(node, ast.Assign)
            for target in node.targets
            if ast.unparse(target).startswith('ctx.')}

    assert 'ctx.mult_table_cache' in assigned['import_one_bundle']
    assert 'ctx.modified_mult_tables' in assigned['import_one_bundle']
    assert 'ctx.created_import_mult_tables' not in assigned['import_one_bundle']

    assert 'ctx.created_import_mult_tables' in assigned['do_import_steps']
