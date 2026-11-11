"""The `ImportContext` that carries one import run's state, and the log bound to it.

Several properties matter and are pinned here. The log prefixes each message with the
position the run has reached, so a line read out of an import log names the observation
that produced it. A message that would otherwise repeat once per index row is logged
once. The mult caches keep their two lifetimes -- per bundle for the fields being
filled, per run for the field ids -- and a cached field is served as the cache itself,
because callers add values through it. And two contexts share nothing, so a second run in the same process neither sees
nor corrupts the first one's caches.
"""

import argparse
import ast
import inspect
import textwrap
from typing import Any, cast

import pytest

from opus_import import import_util
from opus_import.cli import _make_warning_handler
from opus_import.context import ImportContext
from opus_import.importdb.super import ImportDBSuper
from opus_import.mult_fields import MultFieldInfo
from opus_import.obs.obs_base import ObsBase
from opus_import.steps import do_import, do_import_mult

from .conftest import RecordingLogger, make_context


@pytest.fixture
def ctx() -> ImportContext:
    """Return a context with a recording logger and no database."""
    return make_context()


def _messages(ctx: ImportContext, level: str) -> list[str]:
    """Return the messages the context's recording logger holds at `level`."""
    logger = cast(RecordingLogger, ctx.logger)
    return logger.messages_at(level)


def test_a_context_starts_with_empty_state() -> None:
    """Nothing has happened yet: no position, no bad data, and empty caches."""
    ctx = ImportContext(args=argparse.Namespace(), logger=RecordingLogger())

    assert ctx.db is None
    assert ctx.current_bundle_id is None
    assert ctx.current_index_row_number is None
    assert ctx.current_primary_filespec is None
    assert ctx.import_has_bad_data is False
    assert ctx.bundle_has_errors is False
    assert ctx.python_warning_list == []
    assert ctx.bundle_ids is None
    assert ctx.mult_table_cache == {}


def test_two_contexts_share_no_state() -> None:
    """Every mutable field is per-context, so two runs in one process cannot collide."""
    first = make_context()
    second = make_context()

    first.mult_table_cache['obs_general.mission_id'] = do_import_mult.MultFieldCache(
        'obs_general.mission_id', 1, pinned=True
    )
    first.log.nonrepeating_error('a bad thing')

    assert second.mult_table_cache == {}
    assert second.import_has_bad_data is False
    assert second.logged_import_errors == set()
    assert _messages(second, 'error') == []


@pytest.mark.parametrize(
    ('bundle', 'row', 'filespec', 'expected'),
    [
        (None, None, None, ''),
        (None, 7, 'a/b.LBL', ''),
        ('COISS_2002', None, None, '[COISS_2002] '),
        ('COISS_2002', 7, None, '[COISS_2002 index row 7] '),
        ('COISS_2002', 7, 'a/b.LBL', '[COISS_2002 index row 7 "a/b.LBL"] '),
        ('COISS_2002', None, 'a/b.LBL', '[COISS_2002 "a/b.LBL"] '),
    ],
)
def test_a_message_names_the_position_the_run_is_at(
    ctx: ImportContext, bundle: str | None, row: int | None, filespec: str | None, expected: str
) -> None:
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
def test_nothing_below_error_marks_the_import_as_bad(ctx: ImportContext, level: str) -> None:
    """Only errors abort a run; a warning is reported and the import continues."""
    getattr(ctx.log, level)('a message')

    assert ctx.import_has_bad_data is False


def test_a_nonrepeating_error_is_logged_once_however_the_position_changes(
    ctx: ImportContext,
) -> None:
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


def test_a_repeated_nonrepeating_error_still_marks_a_later_bundle(ctx: ImportContext) -> None:
    """A second bundle that repeats the first one's error has errors, though nothing is logged."""
    ctx.current_bundle_id = 'COISS_2002'
    ctx.log.nonrepeating_error('the same fault')
    ctx.bundle_has_errors = False
    ctx.current_bundle_id = 'COISS_2008'
    ctx.log.nonrepeating_error('the same fault')

    assert _messages(ctx, 'error') == ['[COISS_2002] the same fault']
    assert ctx.bundle_has_errors is True


def test_a_nonrepeating_warning_is_logged_once(ctx: ImportContext) -> None:
    """Warnings deduplicate the same way, and still do not mark the import bad."""
    ctx.log.nonrepeating_warning('the same fault')
    ctx.log.nonrepeating_warning('the same fault')
    ctx.log.nonrepeating_warning('a different fault')

    assert _messages(ctx, 'warning') == ['the same fault', 'a different fault']
    assert ctx.import_has_bad_data is False


def test_an_unknown_target_name_is_reported_once_and_names_the_file_to_edit(
    ctx: ImportContext,
) -> None:
    """The message tells the operator where to add the target, and repeats no further."""
    ctx.log.unknown_target_name('PLUTO')
    ctx.log.unknown_target_name('PLUTO')

    assert _messages(ctx, 'error') == [
        'Unknown TARGET_NAME "PLUTO" - edit config_targets/target_name_info.py'
    ]
    assert ctx.import_has_bad_data is True


@pytest.mark.parametrize(
    ('func_name', 'method_name', 'level'),
    [
        ('log_error', 'error', 'error'),
        ('log_warning', 'warning', 'warning'),
        ('log_info', 'info', 'info'),
        ('log_debug', 'debug', 'debug'),
        ('log_nonrepeating_error', 'nonrepeating_error', 'error'),
        ('log_nonrepeating_warning', 'nonrepeating_warning', 'warning'),
        ('log_unknown_target_name', 'unknown_target_name', 'error'),
    ],
)
def test_the_step_spelling_and_the_object_spelling_are_one_operation(
    func_name: str, method_name: str, level: str
) -> None:
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
        'Unknown TARGET_NAME "PLUTO" - edit config_targets/target_name_info.py',
    ]
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

    assert _messages(ctx, 'error') == [
        'Warnings found during table import of x.LBL:',
        '  first warning',
        '  second warning',
    ]
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


#: A preprogrammed mult column, whose one row registration has stored.
_MULT_COLUMN = {'mult_options': [(0, 'COISS', 'Cassini ISS', 10, 'Y', None, None)]}

#: The field `_MULT_COLUMN`'s values belong to.
_FIELD = 'obs_general.x'


def _mult_context() -> ImportContext:
    """Return a context the mult code can run against, with its messages suppressed.

    Built from the real CLI's defaults with the one option this needs turned on,
    rather than from a namespace holding only that option: the rest of the run's
    arguments stay what a real run would have. The field ids are given, as
    `opus_import.mult_fields.ensure_mult_fields` would have read them.
    """
    ctx = make_context()
    ctx.args.suppress_mult_messages = True
    ctx.mult_fields = {_FIELD: MultFieldInfo(7, pinned=True)}
    ctx.db = cast(ImportDBSuper, _EmptyDatabase())
    return ctx


class _EmptyDatabase:
    """A database holding the one registered mult row, counting the reads of ``mult``."""

    def __init__(self) -> None:
        self.reads = 0

    @staticmethod
    def quote_identifier(name: str) -> str:
        return f'`{name}`'

    def read_rows(self, table_name: str, *_args: Any) -> list[Any]:
        if table_name != 'mult':
            return []
        self.reads += 1
        return [(0, 'COISS', 'Cassini ISS', 10, 'Y', None)]


def test_a_mult_field_is_converted_once_and_then_served_from_the_context() -> None:
    """The second read returns the cached field itself, so callers can add to it.

    `update_mult_table` adds a value through the cache this returns, and the added value
    has to be visible to the next reader and to the eventual write-out.
    """
    ctx = _mult_context()

    first = do_import_mult.read_mult_field(ctx, _FIELD, _MULT_COLUMN)
    second = do_import_mult.read_mult_field(ctx, _FIELD, _MULT_COLUMN)

    assert first is second
    assert cast(_EmptyDatabase, ctx.db).reads == 1
    assert ctx.mult_table_cache[_FIELD] is first
    assert first.field_id == 7
    assert [row['value'] for row in first.rows] == ['COISS']
    assert first.rows[0]['pin'] == 10


def test_one_context_s_mult_cache_is_invisible_to_another() -> None:
    """Two runs in one process do not serve each other stale mult fields."""
    first = _mult_context()
    second = _mult_context()

    first_rows = do_import_mult.read_mult_field(first, _FIELD, _MULT_COLUMN)
    second_rows = do_import_mult.read_mult_field(second, _FIELD, _MULT_COLUMN)

    assert first_rows is not second_rows


def test_the_bundle_loop_clears_the_per_bundle_caches_and_not_the_per_run_one() -> None:
    """Which cache each loop resets is what keeps one bundle's state out of the next.

    `mult_table_cache` and `bundle_ids` are reset per bundle: carrying the cache across
    bundles would serve one bundle another's stale values, and carrying the ids would
    give one bundle's observations ids from another's range.
    `import_has_bad_data` is reset per run, so one bad bundle fails the run. Driving the
    two loops needs holdings and a database, so this reads the source instead -- but it
    fails if either reset is dropped or moved to the wrong loop.
    """
    assigned = {}
    for func in (do_import.import_one_bundle, do_import.do_import_steps):
        tree = ast.parse(textwrap.dedent(inspect.getsource(func)))
        assigned[func.__name__] = {
            ast.unparse(target)
            for node in ast.walk(tree)
            if isinstance(node, ast.Assign)
            for target in node.targets
            if ast.unparse(target).startswith('ctx.')
        }

    assert 'ctx.mult_table_cache' in assigned['import_one_bundle']
    assert 'ctx.bundle_ids' in assigned['import_one_bundle']
    assert 'ctx.import_has_bad_data' not in assigned['import_one_bundle']

    assert 'ctx.import_has_bad_data' in assigned['do_import_steps']
    assert 'ctx.bundle_has_errors' in assigned['do_import_steps']


def test_a_timed_step_records_its_elapsed_time(
    ctx: ImportContext, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The time between entering and leaving the block is stored under the step name."""
    readings = iter([10.0, 12.5])
    monkeypatch.setattr('opus_import.context.time.perf_counter', lambda: next(readings))
    with ctx.timed('import'):
        pass
    assert ctx.step_timings == {'import': 2.5}


def test_a_step_timed_twice_accumulates(
    ctx: ImportContext, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Two blocks under one name sum rather than the second replacing the first."""
    readings = iter([0.0, 1.0, 5.0, 8.0])
    monkeypatch.setattr('opus_import.context.time.perf_counter', lambda: next(readings))
    for _ in range(2):
        with ctx.timed('create_cart'):
            pass
    assert ctx.step_timings == {'create_cart': 4.0}


def test_a_timed_step_that_raises_is_still_recorded(
    ctx: ImportContext, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A failing step's time is kept, and its exception is not swallowed."""
    readings = iter([3.0, 3.75])
    monkeypatch.setattr('opus_import.context.time.perf_counter', lambda: next(readings))
    with pytest.raises(RuntimeError, match='boom'), ctx.timed('validate'):
        raise RuntimeError('boom')
    assert ctx.step_timings == {'validate': 0.75}
