"""The pool computes an index exactly as one process does, without a server.

A stand-in row function exercises everything a real one does that a worker cannot do
itself -- row ids, ``mult_`` values, a ``mult_list`` column, surface geometry targets,
log messages deduplicated and not, and a Python warning -- and the index is computed once
in this process and once across a forked pool. Everything the import's process ends up
holding must be the same either way.
"""

from __future__ import annotations

import contextlib
import multiprocessing
import os
import time
import warnings
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any

import pytest

from opus_import import cli, deferred, import_util
from opus_import.context import ImportContext
from opus_import.deferred import Capture, DeferredJson, LocalId, MultRef
from opus_import.steps import do_import_mult, do_import_pool

from .conftest import make_context

#: The ``mult_`` column every stand-in observation fills.
PLANET = {'field_name': 'planet', 'pi_form_type': 'GROUP'}

#: The ``mult_`` column of the stand-in target's table.
TARGET = {'field_name': 'target_class', 'pi_form_type': 'GROUP'}

#: The schemas the pool looks a mult event's column up in.
SCHEMAS = {
    'obs_general': [{'field_name': 'id'}, PLANET],
    'obs_surface_geometry__<TARGET>': [{'field_name': 'id'}, TARGET],
}


class _FakeDB:
    """A stand-in answering the two questions the first id a table hands out asks."""

    def __init__(self, max_ids: dict[str, int]) -> None:
        """Hold each table's largest id; a table not given does not exist.

        Parameters:
            max_ids: The largest id per table.
        """
        self.max_ids = max_ids

    def table_exists(self, table_name: str) -> bool:
        """Say whether a table exists."""
        return table_name in self.max_ids

    def find_column_max(self, table_name: str, column: str) -> int:
        """Return a table's largest id."""
        assert column == 'id'
        return self.max_ids[table_name]


@dataclass
class _Index:
    """What the stand-in rows are computed from."""

    obs_rows: list[int]
    table_schemas: dict[str, Any] = field(default_factory=lambda: SCHEMAS)


def _compute_row(
    ctx: ImportContext, index: _Index, index_row_num: int, emit: do_import_pool.RowEmitter
) -> None:
    """Compute one stand-in observation through the pipeline's own id, mult and log calls."""
    ctx.current_index_row_number = index_row_num + 1
    ctx.current_primary_filespec = f'DATA/FILE_{index_row_num}.LBL'
    general_id = import_util.next_table_id(ctx, 'obs_general')
    planet = do_import_mult.update_mult_table(
        ctx,
        'obs_general',
        'planet',
        PLANET,
        f'P{index_row_num % 4}',
        f'Planet {index_row_num % 4}',
        disp_order=f'{index_row_num % 4:03d}',
    )
    if index_row_num % 5 == 0:
        import_util.log_nonrepeating_warning(ctx, 'a fault every fifth row shares')
    import_util.log_info(ctx, f'computed row {index_row_num}')
    if index_row_num == 7:
        warnings.warn('row seven warns', UserWarning, stacklevel=1)
    emit(
        'obs_general',
        {'id': general_id, 'planet': planet, 'planets': deferred.json_list([planet, 'S RINGS'])},
        None,
    )
    if index_row_num % 3 == 0:
        target_id = import_util.next_table_id(ctx, 'obs_surface_geometry__mimas')
        target_class = do_import_mult.update_mult_table(
            ctx,
            'obs_surface_geometry__mimas',
            'target_class',
            TARGET,
            'MOON',
            'Moon',
            disp_order='a',
        )
        emit(
            'obs_surface_geometry__mimas',
            {'id': target_id, 'obs_general_id': general_id, 'target_class': target_class},
            'MIMAS',
        )
    emit(
        'obs_files',
        {
            'id': import_util.next_table_id(ctx, 'obs_files'),
            'obs_general_id': general_id,
            'instrument_id': planet,
        },
        None,
    )


def _run(
    workers: int, worker_rows: int = 4, rows: int = 23
) -> tuple[ImportContext, list[Any], bool]:
    """Compute the stand-in index with the given pool, returning what the process holds."""
    ctx = make_context(db=_FakeDB({'obs_general': 100, 'obs_files': 1000}))
    ctx.current_bundle_id = 'TEST_0001'
    ctx.workers = workers
    ctx.worker_rows = worker_rows
    emitted: list[Any] = []
    with warnings.catch_warnings():
        warnings.simplefilter('always')
        warnings.filterwarnings(
            'ignore', message=r'This process .* is multi-threaded', category=DeprecationWarning
        )
        warnings.showwarning = cli._make_warning_handler(ctx)
        computed = do_import_pool.compute_index(
            ctx,
            _Index(list(range(rows))),
            _compute_row,
            lambda table, row, target: emitted.append((table, row, target)),
            'TEST_0001_index.lbl',
        )
    return ctx, emitted, computed


def test_a_pool_computes_what_one_process_computes() -> None:
    """Rows, ids, mult ids, the log, and the warnings are the same with three workers."""
    serial, serial_rows, serial_ok = _run(workers=1)
    pooled, pooled_rows, pooled_ok = _run(workers=3)

    assert serial_ok
    assert pooled_ok
    assert pooled_rows == serial_rows
    assert pooled.logger.messages == serial.logger.messages
    assert pooled.python_warning_list == serial.python_warning_list == ['row seven warns']
    assert pooled.max_table_id_cache == serial.max_table_id_cache
    assert pooled.mult_table_cache == serial.mult_table_cache
    assert pooled.modified_mult_tables == serial.modified_mult_tables
    assert pooled.logged_import_warnings == serial.logged_import_warnings
    assert pooled.capture is None


def test_the_rows_are_computed_in_forked_workers() -> None:
    """With more rows than one task covers, the rows come from several other processes."""

    def which_process(ctx: ImportContext, index: _Index, index_row_num: int, emit: Any) -> None:
        # Long enough that one worker cannot take every task before the others start.
        time.sleep(0.02)
        emit('obs_general', {'pid': os.getpid()}, None)

    ctx = make_context()
    ctx.workers = 3
    ctx.worker_rows = 2
    emitted: list[Any] = []
    with _forking():
        computed = do_import_pool.compute_index(
            ctx,
            _Index(list(range(40))),
            which_process,
            lambda table, row, target: emitted.append(row['pid']),
            'TEST_0001_index.lbl',
        )
    assert computed
    assert len(emitted) == 40
    assert os.getpid() not in emitted
    assert len(set(emitted)) > 1


def test_the_replayed_rows_hold_real_ids_and_no_placeholder() -> None:
    """Ids continue from the table's largest; mult ids are the serial ones; lists are JSON."""
    _ctx, rows, _ok = _run(workers=3)
    general = [row for table, row, _target in rows if table == 'obs_general']
    assert [row['id'] for row in general] == list(range(101, 124))
    assert [row['planet'] for row in general[:5]] == [0, 1, 2, 3, 0]
    assert general[1]['planets'] == '[1, "S RINGS"]'
    targets = [row for table, row, _target in rows if table == 'obs_surface_geometry__mimas']
    assert [row['id'] for row in targets] == list(range(len(targets)))
    for _table, row, _target in rows:
        assert not any(deferred.is_deferred(value) for value in row.values())


def test_a_worker_that_fails_abandons_the_index() -> None:
    """The failure is logged, naming the rows of the failed task."""

    def failing_row(ctx: ImportContext, index: _Index, index_row_num: int, emit: Any) -> None:
        if ctx.capture is not None and index_row_num == 9:
            raise RuntimeError('row nine breaks')
        _compute_row(ctx, index, index_row_num, emit)

    ctx = make_context(db=_FakeDB({'obs_general': 100, 'obs_files': 1000}))
    ctx.current_bundle_id = 'TEST_0001'
    ctx.workers = 2
    ctx.worker_rows = 4
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        computed = do_import_pool.compute_index(
            ctx, _Index(list(range(23))), failing_row, lambda *_: None, 'TEST_0001_index.lbl'
        )

    assert computed is False
    (message,) = ctx.logger.messages_at('error')
    assert message.startswith(
        '[TEST_0001] A worker failed computing rows 9 to 12 of "TEST_0001_index.lbl": '
        "RuntimeError('row nine breaks')"
    )
    assert ctx.import_has_bad_data is True


def test_an_index_smaller_than_one_task_is_computed_in_this_process(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No pool is made for an index with fewer rows than one task covers."""
    monkeypatch.setattr(do_import_pool, '_compute_in_pool', _no_pool)
    ctx, rows, computed = _run(workers=3, worker_rows=50)
    assert computed
    assert len([row for row in rows if row[0] == 'obs_general']) == 23
    assert ctx.logger.messages_at('error') == []


def test_a_platform_without_fork_computes_in_this_process(monkeypatch: pytest.MonkeyPatch) -> None:
    """Workers need ``fork``; without it the index is computed here, and the log says why."""
    monkeypatch.setattr(do_import_pool, '_compute_in_pool', _no_pool)
    monkeypatch.setattr(multiprocessing, 'get_all_start_methods', lambda: ['spawn'])
    ctx, _rows, computed = _run(workers=3)
    assert computed
    assert ctx.logger.messages_at('info')[0] == (
        '[TEST_0001] workers 3 needs fork, which this platform lacks; computing in one process'
    )


def _drop_row(table_name: str, row: dict[str, Any], target: str | None) -> None:
    """Accept a replayed row and keep nothing."""


@contextlib.contextmanager
def _forking() -> Iterator[None]:
    """Let this test fork a pool from a process that may have threads.

    The test runner's worker processes have threads of their own, and forking one warns
    that the child may deadlock. The import forks its pool before it starts any thread,
    which the import suite's comparison of logs shows, so the warning here describes the
    test runner rather than the code under test.
    """
    with warnings.catch_warnings():
        warnings.filterwarnings(
            'ignore', message=r'This process .* is multi-threaded', category=DeprecationWarning
        )
        yield


def _no_pool(*_args: Any) -> bool:
    """Stand in for the pool, failing the test if it is reached."""
    raise AssertionError('a pool was made')


def test_a_capturing_context_records_its_log_calls_instead_of_making_them() -> None:
    """Every `ImportLog` method records, with the position, and changes nothing."""
    ctx = make_context()
    ctx.capture = Capture()
    ctx.current_index_row_number = 4
    ctx.current_primary_filespec = 'DATA/X.LBL'
    ctx.log.error('bad %s', 'thing')
    ctx.log.nonrepeating_error('once')
    ctx.log.nonrepeating_warning('twice')
    ctx.log.debug('quiet')

    assert ctx.logger.messages == []
    assert ctx.import_has_bad_data is False
    assert ctx.logged_import_errors == []
    assert ctx.capture.events == [
        ('log', 4, 'DATA/X.LBL', 'error', ('bad %s', 'thing')),
        ('log', 4, 'DATA/X.LBL', 'nonrepeating_error', ('once',)),
        ('log', 4, 'DATA/X.LBL', 'nonrepeating_warning', ('twice',)),
        ('log', 4, 'DATA/X.LBL', 'debug', ('quiet',)),
    ]


def test_a_capture_numbers_ids_per_table_from_zero() -> None:
    """A worker's ids are positions among its own task's ids for each table."""
    capture = Capture()
    assert [capture.next_id('a'), capture.next_id('b'), capture.next_id('a')] == [
        LocalId('a', 0),
        LocalId('b', 0),
        LocalId('a', 1),
    ]
    assert capture.id_counts == {'a': 2, 'b': 1}


def test_a_list_holding_a_placeholder_waits_to_become_json() -> None:
    """A ``mult_list`` is JSON at once unless one of its values is still unknown."""
    assert deferred.json_list([1, 'S RINGS']) == '[1, "S RINGS"]'
    assert deferred.json_list([MultRef(0), 2]) == DeferredJson((MultRef(0), 2))


class _Logger:
    """A logger stand-in recording the calls replayed into it."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[Any, ...], dict[str, Any]]] = []

    def warn(self, *args: Any, **kwargs: Any) -> None:
        """Record a call."""
        self.calls.append(('warn', args, kwargs))


def test_a_replayed_pdsfile_log_call_reaches_the_class_logger_it_was_made_on() -> None:
    """The call goes to the logger of the class whose logger the worker called."""
    logger = _Logger()
    ctx = make_context()
    events: list[tuple[Any, ...]] = [
        ('pdsfile', 3, 'DATA/X.LBL', 'some.Rules', 'warn', ('Missing', 'path'), {})
    ]
    do_import_pool._replay(
        ctx,
        (events, {}),
        do_import_pool._ColumnLookup(SCHEMAS),
        {'some.Rules': (object, logger)},
        _drop_row,
    )
    assert logger.calls == [('warn', ('Missing', 'path'), {})]
    assert (ctx.current_index_row_number, ctx.current_primary_filespec) == (3, 'DATA/X.LBL')


def test_a_target_tables_mult_column_is_found_in_the_template() -> None:
    """Every target's table shares the ``<TARGET>`` template's column definitions."""
    columns = do_import_pool._ColumnLookup(SCHEMAS)
    assert columns.find('obs_surface_geometry__mimas', 'target_class') is TARGET
    assert columns.find('obs_general', 'planet') is PLANET
