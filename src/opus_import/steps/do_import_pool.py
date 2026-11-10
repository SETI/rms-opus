"""Compute an index's observations in a pool of forked processes, and replay them in order.

`opus_import.steps.do_import_index` computes each index row with one function, which this
module runs either in the import's own process or, with ``workers`` above 1, across a
pool. **Single writer, many computers**: each worker computes a range of rows exactly as
the import's process would, through the same code, but records every database call and
log write on its context's `opus_import.deferred.Capture` instead of making it. The
import's process takes the workers' results in index order and replays each event where
the serial loop would have produced it -- rebasing the workers' row ids onto the real
ones, resolving each ``mult_`` value through
`opus_import.steps.do_import_mult.update_mult_table` in the serial order, and logging
each message with the position it was recorded at -- so the tables and the log come out
the same whatever the number of workers.

The pool is created once per index, after everything its rows are computed from has been
set up, and the workers inherit that state by ``fork``: nothing is sent to a worker but a
range of row numbers. A platform without ``fork`` computes in the import's process, and
so does an index with fewer rows than one task covers.
"""

from __future__ import annotations

import ctypes
import json
import multiprocessing
import os
import signal
import sys
import time
import warnings
from collections import deque
from collections.abc import Callable
from concurrent.futures import Future, ProcessPoolExecutor
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import pdsfile

from opus_import import import_util
from opus_import.deferred import Capture, DeferredJson, Event, LocalId, MultRef
from opus_import.import_fault import import_fault_argument
from opus_import.importdb.super import close_inherited_connections
from opus_import.steps import do_import_mult

if TYPE_CHECKING:
    from opus_import.context import ImportContext
    from opus_import.import_util import TableSchema

#: The test-only fault site (`opus_import.import_fault`) at which every task first sleeps
#: for the number of seconds the argument gives, so a test can find the pool's workers
#: alive.
STALL_FAULT_SITE = 'stall_worker'

#: Linux's ``prctl`` option that sends the calling process a signal when its parent dies.
PR_SET_PDEATHSIG = 1

#: Tasks each worker may have queued ahead of the one being replayed, so the import's
#: process holds a bounded number of results rather than a whole index's.
TASKS_AHEAD_PER_WORKER = 2

#: Where a computed row goes -- its table, the row, and the surface geometry target it is
#: for, or None.
RowEmitter = Callable[[str, dict[str, Any], str | None], None]

#: Computes one index row, given the context, what the index's rows are computed from, the
#: row's position, and where its rows go.
RowFunction = Callable[['ImportContext', Any, int, RowEmitter], None]

#: A task's result -- its events, and how many ids it handed out per table.
TaskResult = tuple[list[Event], dict[str, int]]


@dataclass
class _PoolState:
    """What the forked workers inherit, installed before the pool is created.

    Attributes:
        ctx: The import run's context.
        index_state: What every row of the index is computed from.
        compute_row: The function that computes one row.
        loggers: Each ``pdsfile`` class that has a logger of its own, keyed by its module
            and qualified name, with that class and its logger.
    """

    ctx: ImportContext
    index_state: Any
    compute_row: RowFunction
    loggers: dict[str, tuple[type, Any]]


#: The pool's state while an index is computed in one. A module global, because that is
#: what a forked worker inherits without anything being pickled.
_STATE: _PoolState | None = None


def compute_index(
    ctx: ImportContext,
    index_state: Any,
    compute_row: RowFunction,
    emit: RowEmitter,
    index_path: str,
) -> bool:
    """Compute every row of an index, handing each computed row to `emit` in index order.

    Parameters:
        ctx: The import run's context, whose ``workers`` and ``worker_rows`` decide
            whether a pool is used.
        index_state: What every row of the index is computed from; its ``obs_rows`` are
            the rows.
        compute_row: The function that computes one row.
        emit: Where each computed row goes, with every value final.
        index_path: The primary index file, named if a worker fails.

    Returns:
        True if every row was computed. False if a worker failed, which is logged and
        leaves the rows after the failed task uncomputed.
    """
    row_count = len(index_state.obs_rows)
    workers = ctx.workers
    if workers > 1 and 'fork' not in multiprocessing.get_all_start_methods():
        import_util.log_info(
            ctx,
            f'workers {workers} needs fork, which this platform lacks; computing in one process',
        )
        workers = 1
    if workers == 1 or row_count < ctx.worker_rows:
        for index_row_num in range(row_count):
            compute_row(ctx, index_state, index_row_num, emit)
        return True
    return _compute_in_pool(ctx, index_state, compute_row, emit, index_path, workers)


def _compute_in_pool(
    ctx: ImportContext,
    index_state: Any,
    compute_row: RowFunction,
    emit: RowEmitter,
    index_path: str,
    workers: int,
) -> bool:
    """Compute an index's rows across a pool of forked workers, replaying them in order.

    Parameters:
        ctx: The import run's context.
        index_state: What every row of the index is computed from.
        compute_row: The function that computes one row.
        emit: Where each computed row goes.
        index_path: The primary index file, named if a worker fails.
        workers: The pool's size.

    Returns:
        True if every task was computed and replayed, False if one failed.
    """
    global _STATE
    row_count = len(index_state.obs_rows)
    bounds = [
        (start, min(start + ctx.worker_rows, row_count))
        for start in range(0, row_count, ctx.worker_rows)
    ]
    columns = _ColumnLookup(index_state.table_schemas)
    _STATE = _PoolState(ctx, index_state, compute_row, _pdsfile_loggers())
    executor = ProcessPoolExecutor(
        max_workers=workers,
        mp_context=multiprocessing.get_context('fork'),
        initializer=_initialize_worker,
        initargs=(os.getpid(),),
    )
    try:
        tasks = iter(bounds)
        pending: deque[tuple[tuple[int, int], Future[TaskResult]]] = deque()

        def submit_next() -> None:
            """Queue the next task, if there is one."""
            task = next(tasks, None)
            if task is not None:
                pending.append((task, executor.submit(_compute_task, task)))

        for _ in range(TASKS_AHEAD_PER_WORKER * workers):
            submit_next()
        while pending:
            (start, end), future = pending.popleft()
            try:
                result = future.result()
            except Exception as error:
                ctx.current_index_row_number = None
                ctx.current_primary_filespec = None
                import_util.log_error(
                    ctx,
                    f'A worker failed computing rows {start + 1} to {end} of "{index_path}": '
                    f'{error!r}; the index is abandoned',
                )
                return False
            _replay(ctx, result, columns, _STATE.loggers, emit)
            submit_next()
    finally:
        executor.shutdown(wait=True, cancel_futures=True)
        _STATE = None
    return True


def _initialize_worker(parent_pid: int) -> None:
    """Prepare a freshly forked worker, before its first task.

    A pool worker exits by `os._exit`, so nothing it inherited is ever closed or flushed
    on its way out, and this is the only place it deals with what it inherited:

    * every inherited database connection is let go of without a word sent on it
      (`opus_import.importdb.super.close_inherited_connections`), and the worker's
      context has no database;
    * on Linux, the kernel is asked to kill the worker when the import's process dies,
      and a worker whose parent died before that request exits at once; elsewhere a
      worker outlives a killed parent;
    * Python warnings and the ``pdsfile`` classes' loggers are recorded on the task's
      capture rather than written to the import's log files, which the worker shares.

    Parameters:
        parent_pid: The import's process, which created the pool.
    """
    assert _STATE is not None
    close_inherited_connections()
    _STATE.ctx.db = None
    if sys.platform.startswith('linux'):
        libc = ctypes.CDLL(None, use_errno=True)
        libc.prctl(PR_SET_PDEATHSIG, signal.SIGKILL)
        if os.getppid() != parent_pid:
            os._exit(1)
    warnings.showwarning = _record_warning
    for key, (owner, _logger) in _STATE.loggers.items():
        owner.LOGGER = _RecordingLogger(key)  # type: ignore[attr-defined]


def _compute_task(bounds: tuple[int, int]) -> TaskResult:
    """Compute one range of index rows in a worker, recording everything it produces.

    Parameters:
        bounds: The first row and one past the last, from zero.

    Returns:
        The events, in the order the serial loop would have produced them, and how many
        ids the task handed out per table.
    """
    assert _STATE is not None
    stall = import_fault_argument(STALL_FAULT_SITE)
    if stall is not None:
        time.sleep(float(stall))
    ctx = _STATE.ctx
    capture = Capture()
    ctx.capture = capture

    def record_row(table_name: str, row: dict[str, Any], target: str | None) -> None:
        """Record one computed row at the position the worker is on."""
        position = (ctx.current_index_row_number, ctx.current_primary_filespec)
        capture.row(position, table_name, row, target)

    try:
        for index_row_num in range(*bounds):
            _STATE.compute_row(ctx, _STATE.index_state, index_row_num, record_row)
    finally:
        ctx.capture = None
    return capture.events, capture.id_counts


def _replay(
    ctx: ImportContext,
    result: TaskResult,
    columns: _ColumnLookup,
    loggers: dict[str, tuple[type, Any]],
    emit: RowEmitter,
) -> None:
    """Replay one task's events in the import's process, where the serial loop made them.

    A worker's id for a table is its position among that table's ids in the task, so it
    becomes the id the table had when the task's replay began, plus that position, plus
    one; the table's cached id then advances past the task's last. A mult value is
    resolved by the call the serial loop makes, in the same order, so every value gets
    the id the serial loop gives it.

    Parameters:
        ctx: The import run's context.
        result: The task's events and per-table id counts.
        columns: Finds the column definition a mult event names.
        loggers: The ``pdsfile`` classes' loggers, keyed as the events name them.
        emit: Where each row goes, with every value final.
    """
    events, id_counts = result
    bases: dict[str, int] = {}
    mult_ids: list[Any] = []

    def base(table_name: str) -> int:
        """Return the id the table had when this task's replay began."""
        if table_name not in bases:
            if table_name not in ctx.max_table_id_cache:
                ctx.max_table_id_cache[table_name] = import_util.find_max_table_id(ctx, table_name)
            bases[table_name] = ctx.max_table_id_cache[table_name]
        return bases[table_name]

    def resolve(value: Any) -> Any:
        """Return a value with any placeholder replaced by what it stands for."""
        if isinstance(value, LocalId):
            return base(value.table) + value.number + 1
        if isinstance(value, MultRef):
            return mult_ids[value.number]
        if isinstance(value, DeferredJson):
            return json.dumps([resolve(entry) for entry in value.values])
        return value

    for event in events:
        kind, row_number, filespec = event[:3]
        ctx.current_index_row_number = row_number
        ctx.current_primary_filespec = filespec
        if kind == 'row':
            table_name, row, target = event[3:]
            emit(table_name, {key: resolve(value) for key, value in row.items()}, target)
        elif kind == 'mult':
            table_name, field_name, values = event[3:]
            column = columns.find(table_name, field_name)
            mult_ids.append(
                do_import_mult.update_mult_table(ctx, table_name, field_name, column, *values)
            )
        elif kind == 'log':
            method, args = event[3:]
            getattr(ctx.log, method)(*args)
        elif kind == 'warning':
            ctx.python_warning_list.append(event[3])
        else:
            assert kind == 'pdsfile', kind
            owner, method, args, kwargs = event[3:]
            logger = loggers[owner][1]
            getattr(logger, method)(*args, **kwargs)

    for table_name, count in id_counts.items():
        ctx.max_table_id_cache[table_name] = base(table_name) + count


class _ColumnLookup:
    """Finds the column definition a mult event names, by table and column."""

    def __init__(self, table_schemas: dict[str, TableSchema]) -> None:
        """Index the index's table schemas.

        Parameters:
            table_schemas: Each table's column definitions; every surface geometry
                target's table shares the ``<TARGET>`` template's.
        """
        self._schemas = table_schemas
        self._template = next((name for name in table_schemas if '<TARGET>' in name), None)
        self._found: dict[tuple[str, str], dict[str, Any]] = {}

    def find(self, table_name: str, field_name: str) -> dict[str, Any]:
        """Return a column's definition.

        Parameters:
            table_name: The table, or a surface geometry target's table.
            field_name: The column.

        Returns:
            The column's definition, from the table's schema or the template's.
        """
        key = (table_name, field_name)
        if key not in self._found:
            schema_name = table_name
            if table_name not in self._schemas:
                assert self._template is not None, table_name
                schema_name = self._template
            self._found[key] = next(
                column
                for column in self._schemas[schema_name]
                if column.get('field_name') == field_name
            )
        return self._found[key]


def _pdsfile_loggers() -> dict[str, tuple[type, Any]]:
    """Return every ``pdsfile`` class that holds a logger of its own, with that logger.

    Returns:
        Each such class, keyed by its module and qualified name, with its logger.
    """
    found: dict[str, tuple[type, Any]] = {}
    stack: list[type] = [pdsfile.pdsfile.PdsFile]
    while stack:
        owner = stack.pop()
        stack.extend(owner.__subclasses__())
        logger = owner.__dict__.get('LOGGER')
        if logger:
            found[f'{owner.__module__}.{owner.__qualname__}'] = (owner, logger)
    return found


def _position() -> tuple[Any, Any]:
    """Return the index row number and primary filespec the worker is on."""
    assert _STATE is not None
    ctx = _STATE.ctx
    return (ctx.current_index_row_number, ctx.current_primary_filespec)


def _record_warning(
    message: Warning | str,
    category: type[Warning],
    filename: str,
    lineno: int,
    file: Any = None,
    line: str | None = None,
) -> None:
    """Record a Python warning's text on the task's capture, as the import's handler would.

    Parameters:
        message: The warning, or its text.
        category: The warning class. Not recorded.
        filename: Where the warning was raised. Not recorded.
        lineno: The line it was raised on. Not recorded.
        file: Where the standard handler would have written it. Unused.
        line: The source line, if the caller supplied one. Not recorded.
    """
    assert _STATE is not None
    capture = _STATE.ctx.capture
    if capture is not None:
        capture.warning(_position(), str(message))


def _loggable(value: Any) -> Any:
    """Return a logger argument in a form that survives the trip to the import's process.

    Parameters:
        value: The argument.

    Returns:
        The argument itself when it is a string, number, or None; its text otherwise.
    """
    if value is None or isinstance(value, (str, int, float)):
        return value
    return str(value)


class _RecordingLogger:
    """Stands in for a ``pdsfile`` class's logger in a worker, recording every call."""

    def __init__(self, owner: str) -> None:
        """Stand in for one class's logger.

        Parameters:
            owner: The class, as its module and qualified name.
        """
        self._owner = owner

    def __getattr__(self, method: str) -> Callable[..., None]:
        """Return a function that records a call of the logger method `method`.

        Parameters:
            method: The logger method.

        Returns:
            The recorder.
        """

        def record(*args: Any, **kwargs: Any) -> None:
            """Record the call on the task's capture; outside a task it is dropped."""
            assert _STATE is not None
            capture = _STATE.ctx.capture
            if capture is not None:
                capture.pdsfile_log(
                    _position(),
                    self._owner,
                    method,
                    tuple(_loggable(arg) for arg in args),
                    {key: _loggable(value) for key, value in kwargs.items()},
                )

        return record
