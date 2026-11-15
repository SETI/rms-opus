"""Time an incremental update of a served schema, written into an import generation.

An **incremental update** writes only the changed bundles into the served schema, as an
import generation that ``obs_general``, a view, hides until the generation is switched
in. This command times one against a schema a full import built, in place: it never
copies the schema, never drops it, and never stops, starts or restarts the owned MySQL
server, so `benchmarks.bench_web` can serve the same schema from another process while
the update imports. It refuses to start the server itself: start it first with
``python -m benchmarks.bench_server start``. A side whose ``opus_import --help`` lists
no ``--begin-generation`` cannot make such an update, and is refused before anything
runs.

The **update** is these invocations of the side's ``opus_import``, each its own process
with the schema in its ``OPUS_CONFIG``: ``--begin-generation``, the bundle import of the
bundles to re-import or add, ``--delete-bundles`` of the bundles to drop when any are
given, then the side's finalization and validation options and
``--write-schema-version``, which marks the generation ready to switch. The
**switch** is ``--switch-generation`` then ``--purge-generations``. A full run records
the update and then the switch, each as a run of its own (of kinds
``generation_update`` and ``generation_switch``); ``--stop-before-switch`` records the
update alone, leaving the generation ready, and ``--switch-only`` the switch alone, of a
generation an earlier command left ready. The switch empties the search tables and
flushes the cache, so it refuses to run while anything answers on ``web.toml``'s
gunicorn or memcached port: stop ``bench_web`` first.

Each invocation's wall-clock is a metric, ``import.generation.<phase>.wall_s`` (the
phases being `UPDATE_PHASES` and `SWITCH_PHASES`), and the update's sum is
``import.generation.update.wall_s``. Each run also records, under its own prefix
(``import.generation.update`` or ``import.generation.switch_purge``), the steps its
invocations' ``--timing-json`` files name (``.phase.<step>_s``), its memory, and the
server's counters over it.

A run fails, and records nothing, when an invocation exits non-zero, when the bundle
import leaves a bundle it imports without a row in the pending generation, when a
dropped bundle still has rows in it, when the schema's version row does not show the
state each step leaves it in, or when the run's ``ERRORS.log`` is not empty at the end.

Example, the incremental group of the test scale's scenario into a complete-scale
schema, with the switch left for later::

    python -m benchmarks.bench_generation --scale complete --side after --pr PR-nn \\
        --session g --python venv-head/bin/python --repo-root . \\
        --schema bench_complete_after_a_1 --incremental-group test --stop-before-switch
"""

from __future__ import annotations

import argparse
import contextlib
import socket
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from benchmarks import web_scenarios
from benchmarks.bench_import import (
    DEFAULT_BULK_LOAD_PATH,
    IMPORT_COUNTERS,
    ImportBench,
    bulk_load_paths,
    file_bulk_load_path,
)
from benchmarks.bench_server import (
    ADDED_GENERATION_COLUMN,
    OBS_GENERAL_ROWS_TABLE,
    REMOVED_GENERATION_COLUMN,
    SCHEMA_VERSION_TABLE,
    MysqlServer,
    counter_deltas,
    load_server_config,
    query,
    quote_identifier,
    reexec_with_socket,
    server_environment,
)
from benchmarks.import_scenarios import load_scenario, require_empty_errors_log
from benchmarks.monitor import RunFailedError
from benchmarks.opus_config_file import parse_import_keys
from benchmarks.results import (
    GENERATION_SWITCH_KIND,
    GENERATION_UPDATE_KIND,
    SCALES,
    SIDES,
    append_runs,
    host_environment,
    make_label,
    new_run,
    scenario_hash,
)
from benchmarks.sides import (
    BEGIN_GENERATION,
    DELETE_BUNDLES,
    PURGE_GENERATIONS,
    SWITCH_GENERATION,
    Side,
    Spelling,
    require_no_pythonpath,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from benchmarks.monitor import InvocationMonitor

#: What every metric this command records begins with.
METRIC_PREFIX = 'import.generation'

#: The prefix of each run kind's own metrics: its sum, steps, memory and counters.
RUN_PREFIXES = {
    GENERATION_UPDATE_KIND: f'{METRIC_PREFIX}.update',
    GENERATION_SWITCH_KIND: f'{METRIC_PREFIX}.switch_purge',
}

#: The update's invocations, by the role `benchmarks.sides.Spelling.role` gives each, with
#: the phase its wall-clock is recorded as. The bundle import's role is ``bundle_import:``
#: and its descriptors.
UPDATE_PHASES = {
    'begin_generation': 'begin',
    'bundle_import': 'import',
    'delete_bundles': 'delete',
    'finalize': 'finalize',
    'validate': 'validate',
    'write_schema_version': 'write_schema_version',
}

#: The switch's invocations, likewise.
SWITCH_PHASES = {
    'switch_generation': 'switch',
    'purge_generations': 'purge',
}

#: The states ``schema_version.pending_state`` holds: a generation being written, and one
#: stamped ready to switch. The harness reads the schema rather than a side's code, so it
#: repeats the values.
PENDING_WRITING = 'writing'
PENDING_READY = 'ready'

#: The version-row columns that describe the generations, in the order read.
GENERATION_STATE_COLUMNS = ('generation', 'pending_generation', 'pending_state', 'revertible')

#: The seconds a check for a listening web server waits for a connection.
LISTEN_PROBE_TIMEOUT_S = 1.0


class GenerationError(Exception):
    """Raised when a side cannot make an incremental update into a generation."""


@dataclass(frozen=True)
class GenerationState:
    """What a schema's version row says about its import generations.

    Attributes:
        generation: The generation the schema serves.
        pending_generation: The generation an update is writing, or None.
        pending_state: How far it has got, or None.
        revertible: Whether a switch can still be reverted.
    """

    generation: int
    pending_generation: int | None
    pending_state: str | None
    revertible: bool


@dataclass(frozen=True)
class UpdateRequest:
    """The bundles an update changes.

    Attributes:
        bundles: The descriptors of the bundles to re-import or add, comma-separated, as
            the bundle import takes them.
        drop: The descriptors of the bundles to drop, or None to drop none.
    """

    bundles: str
    drop: str | None

    def environment(self) -> dict[str, str | None]:
        """Return the result environment's ``generation_update`` entry.

        Returns:
            The bundles and the drop list, as given.
        """
        return {'bundles': self.bundles, 'drop': self.drop}


def require_generations(spelling: Spelling) -> None:
    """Refuse a side whose import cannot make an update into a generation.

    Parameters:
        spelling: The side's spelling.

    Raises:
        GenerationError: If the side's help lists no ``--begin-generation``.
    """
    if spelling.begin_generation is None:
        raise GenerationError(
            f'this side has no {BEGIN_GENERATION}: it cannot update a schema in a generation'
        )


def phase_of(role: str) -> str:
    """Return the phase an invocation's wall-clock is recorded as.

    Parameters:
        role: The invocation's role (`benchmarks.sides.Spelling.role`).

    Returns:
        Its phase in `UPDATE_PHASES` or `SWITCH_PHASES`.

    Raises:
        RunFailedError: If the role is in neither.
    """
    name = role.split(':', 1)[0]
    phases = {**UPDATE_PHASES, **SWITCH_PHASES}
    if name not in phases:
        raise RunFailedError(f'`{role}` is not an invocation of an incremental update')
    return phases[name]


def listening(port: int) -> bool:
    """Return whether anything accepts a connection on a port of 127.0.0.1.

    Parameters:
        port: The port.

    Returns:
        True when a connection succeeds within `LISTEN_PROBE_TIMEOUT_S`.
    """
    with (
        contextlib.suppress(OSError),
        socket.create_connection(('127.0.0.1', port), LISTEN_PROBE_TIMEOUT_S),
    ):
        return True
    return False


class GenerationBench(ImportBench):
    """Runs one side's incremental update of one schema and turns it into result runs."""

    def __init__(
        self,
        *,
        schema: str,
        web_ports: Sequence[int],
        is_listening: Callable[[int], bool],
        **bench: Any,
    ) -> None:
        """Prepare to update a schema.

        Parameters:
            schema: The served schema the update writes, in place.
            web_ports: The ports ``bench_web``'s gunicorn and memcached listen on, which
                must be quiet before the switch.
            is_listening: Says whether anything listens on a port of 127.0.0.1.
            bench: `ImportBench`'s parameters.
        """
        super().__init__(**bench)
        self.schema = schema
        self.web_ports = tuple(web_ports)
        self._is_listening = is_listening

    def generation_state(self) -> GenerationState:
        """Read the schema's version row.

        Returns:
            Its generations.

        Raises:
            RunFailedError: If the row is missing or there is more than one.
        """
        columns = ', '.join(quote_identifier(column) for column in GENERATION_STATE_COLUMNS)
        table = f'{quote_identifier(self.schema)}.{quote_identifier(SCHEMA_VERSION_TABLE)}'
        statement = f'SELECT {columns} FROM {table}'  # nosec B608 - quoted identifiers
        with contextlib.closing(self.server.connect()) as connection:
            rows = query(connection, statement)
        if len(rows) != 1:
            raise RunFailedError(
                f'schema {self.schema} has {len(rows)} schema_version rows, not one'
            )
        generation, pending, state, revertible = rows[0]
        return GenerationState(
            generation=int(generation),
            pending_generation=None if pending is None else int(pending),
            pending_state=None if state is None else str(state),
            revertible=bool(revertible),
        )

    def rows_in_generation(self, bundles: Sequence[str], generation: int) -> dict[str, int]:
        """Count the observations of some bundles that one generation shows.

        Parameters:
            bundles: The bundles.
            generation: The generation.

        Returns:
            Each bundle with any row in the generation, and how many.
        """
        if len(bundles) == 0:
            return {}
        added = quote_identifier(ADDED_GENERATION_COLUMN)
        removed = quote_identifier(REMOVED_GENERATION_COLUMN)
        placeholders = ', '.join(['%s'] * len(bundles))
        statement = (
            f'SELECT bundle_id, COUNT(*) FROM {self._rows_table} '  # nosec B608 - quoted identifiers, placeholders
            f'WHERE bundle_id IN ({placeholders}) AND {added} <= %s '
            f'AND ({removed} IS NULL OR {removed} > %s) GROUP BY bundle_id'
        )
        with contextlib.closing(self.server.connect()) as connection:
            rows = query(connection, statement, [*bundles, generation, generation])
        return {str(bundle): int(count) for bundle, count in rows}

    def generation_rows(self, generation: int) -> tuple[int, int]:
        """Count the observations one generation added and the ones it retired.

        Parameters:
            generation: The generation.

        Returns:
            The rows it added, and the rows it retired.
        """
        added = quote_identifier(ADDED_GENERATION_COLUMN)
        removed = quote_identifier(REMOVED_GENERATION_COLUMN)
        statement = (
            f'SELECT COALESCE(SUM({added} = %s), 0), COALESCE(SUM({removed} = %s), 0) '  # nosec B608 - quoted identifiers
            f'FROM {self._rows_table}'
        )
        with contextlib.closing(self.server.connect()) as connection:
            rows_added, rows_retired = query(connection, statement, [generation, generation])[0]
        return int(rows_added), int(rows_retired)

    def retired_rows(self, generation: int) -> int:
        """Count the observations retired at or before a generation that are still held.

        Parameters:
            generation: The generation.

        Returns:
            The rows, which the purge deletes.
        """
        removed = quote_identifier(REMOVED_GENERATION_COLUMN)
        statement = f'SELECT COUNT(*) FROM {self._rows_table} WHERE {removed} <= %s'  # nosec B608 - quoted identifiers
        with contextlib.closing(self.server.connect()) as connection:
            return int(query(connection, statement, [generation])[0][0])

    @property
    def _rows_table(self) -> str:
        """The qualified name of the base table holding the schema's observations."""
        return f'{quote_identifier(self.schema)}.{quote_identifier(OBS_GENERAL_ROWS_TABLE)}'

    def run_update(self, update: UpdateRequest) -> dict[str, Any]:
        """Begin a generation, write the update into it, and close it ready to switch.

        Parameters:
            update: The bundles to re-import or add, and to drop.

        Returns:
            The result run, of kind `GENERATION_UPDATE_KIND`.

        Raises:
            RunFailedError: If an invocation fails, a bundle named both ways expands to a
                bundle in both lists, the bundle import leaves a bundle without rows in
                the generation, a dropped bundle keeps rows in it, or the version row
                does not show the generation begun and then ready.
        """
        run_dir = self.label.scratch_dir / 'generation_update'
        config_file, errors_log, monitor, timing = self._prepare(run_dir, self.schema)
        monitor.expect_groups([update.bundles, *([] if update.drop is None else [update.drop])])
        imported = monitor.bundles_of(update.bundles)
        dropped = [] if update.drop is None else monitor.bundles_of(update.drop)
        both = sorted(set(imported) & set(dropped))
        if len(both) > 0:
            raise RunFailedError(
                f'{both} would be both re-imported and dropped: a re-import already '
                'replaces every row of a bundle, so leave them out of the drop list'
            )
        run = new_run(GENERATION_UPDATE_KIND)
        before = self._status()
        self._invoke(monitor, config_file, [BEGIN_GENERATION, *timing])
        state = self.generation_state()
        if state.pending_generation is None or state.pending_state != PENDING_WRITING:
            raise RunFailedError(
                f'{BEGIN_GENERATION} left schema {self.schema} with pending generation '
                f'{state.pending_generation} in state {state.pending_state!r}, not '
                f'{PENDING_WRITING!r}'
            )
        pending = state.pending_generation
        monitor.generation = pending
        self._invoke(monitor, config_file, [self.spelling.bundle_import, *timing, update.bundles])
        if update.drop is not None:
            self._invoke(monitor, config_file, [DELETE_BUNDLES, *timing, update.drop])
            kept = self.rows_in_generation(dropped, pending)
            if len(kept) > 0:
                raise RunFailedError(
                    f'{DELETE_BUNDLES} left generation {pending} of {self.schema} with rows '
                    f'of {kept}'
                )
        self._invoke(monitor, config_file, [self.spelling.finalize, *timing])
        self._invoke(monitor, config_file, [self.spelling.validate, *timing])
        self._invoke(monitor, config_file, [*self.spelling.write_schema_version, *timing])
        state = self.generation_state()
        if state.pending_generation != pending or state.pending_state != PENDING_READY:
            raise RunFailedError(
                f'after the update, schema {self.schema} has pending generation '
                f'{state.pending_generation} in state {state.pending_state!r}, not '
                f'{pending} {PENDING_READY!r}'
            )
        require_empty_errors_log(errors_log, at_end=True)
        self._fill_generation_run(run, monitor, before, errors_log.parent)
        rows_added, rows_retired = self.generation_rows(pending)
        run['details'].update(
            {
                'generation': pending,
                'bundles': update.bundles,
                'bundles_imported': imported,
                'drop': update.drop,
                'bundles_dropped': dropped,
                'rows_added': rows_added,
                'rows_retired': rows_retired,
            }
        )
        return run

    def run_switch(self) -> dict[str, Any]:
        """Switch a generation stamped ready into service, then purge what it retired.

        Returns:
            The result run, of kind `GENERATION_SWITCH_KIND`.

        Raises:
            RunFailedError: If anything listens on a ``bench_web`` port, the schema has no
                generation ready to switch, an invocation fails, or the version row and
                the rows do not show the generation served and the purge done.
        """
        busy = [port for port in self.web_ports if self._is_listening(port)]
        if len(busy) > 0:
            raise RunFailedError(
                f'something listens on 127.0.0.1 port {busy}: the switch empties the search '
                'tables and flushes the cache, so stop bench_web before it'
            )
        state = self.generation_state()
        pending = state.pending_generation
        if pending is None or state.pending_state != PENDING_READY:
            raise RunFailedError(
                f'schema {self.schema} has no generation ready to switch (pending '
                f'generation {pending}, state {state.pending_state!r}): run the update first'
            )
        run_dir = self.label.scratch_dir / 'generation_switch'
        config_file, errors_log, monitor, timing = self._prepare(run_dir, self.schema)
        run = new_run(GENERATION_SWITCH_KIND)
        before = self._status()
        self._invoke(monitor, config_file, [SWITCH_GENERATION, *timing])
        state = self.generation_state()
        if state.generation != pending or state.pending_generation is not None:
            raise RunFailedError(
                f'{SWITCH_GENERATION} left schema {self.schema} serving generation '
                f'{state.generation} with {state.pending_generation} pending, not serving '
                f'{pending}'
            )
        self._invoke(monitor, config_file, [PURGE_GENERATIONS, *timing])
        state = self.generation_state()
        retired = self.retired_rows(state.generation)
        if state.revertible or retired > 0:
            raise RunFailedError(
                f'{PURGE_GENERATIONS} left schema {self.schema} revertible {state.revertible} '
                f'with {retired} retired rows'
            )
        require_empty_errors_log(errors_log, at_end=True)
        self._fill_generation_run(run, monitor, before, errors_log.parent)
        run['details']['generation'] = pending
        return run

    def _fill_generation_run(
        self,
        run: dict[str, Any],
        monitor: InvocationMonitor,
        before: dict[str, int],
        log_dir: Path,
    ) -> None:
        """Turn a finished update's or switch's records into its metrics and details.

        Parameters:
            run: The result run, of kind `GENERATION_UPDATE_KIND` or
                `GENERATION_SWITCH_KIND`.
            monitor: The run's monitor.
            before: The server's counters when it started.
            log_dir: The run's log directory, whose import logs name the bulk-load paths.
        """
        metrics = run['metrics']
        prefix = RUN_PREFIXES[run['kind']]
        records = monitor.records
        steps: dict[str, float] = {}
        for record in records:
            phase = phase_of(record.name)
            metrics[f'{METRIC_PREFIX}.{phase}.wall_s'] = record.wall_s
            for step, seconds in record.timings.items():
                if step != 'total':
                    steps[step] = steps.get(step, 0.0) + seconds
        for step, seconds in steps.items():
            metrics[f'{prefix}.phase.{step}_s'] = seconds
        metrics[f'{prefix}.wall_s'] = sum(record.wall_s for record in records)
        metrics[f'{prefix}.peak_tree_pss_kb'] = max(r.peak_tree_pss_kb for r in records)
        metrics[f'{prefix}.peak_rss_kb'] = max(r.peak_rss_kb for r in records)
        ages = [
            r.peak_checkpoint_age_bytes for r in records if r.peak_checkpoint_age_bytes is not None
        ]
        if len(ages) > 0:
            metrics[f'{prefix}.server.peak_checkpoint_age_bytes'] = max(ages)
        for name, delta in counter_deltas(before, self._status(), IMPORT_COUNTERS).items():
            metrics[f'{prefix}.server.{name}'] = delta
        details = run['details']
        details.update(monitor.summary())
        details['schema'] = self.schema
        details['bulk_load_paths'] = bulk_load_paths(log_dir)


def _parse_arguments(argv: Sequence[str] | None) -> argparse.Namespace:
    """Read the command line, and refuse combinations that measure nothing coherent.

    Parameters:
        argv: The arguments, or None for the command line's.

    Returns:
        The parsed arguments.
    """
    parser = argparse.ArgumentParser(
        prog='python -m benchmarks.bench_generation',
        description='Time an incremental update of a served schema, in place, written into an '
        'import generation and switched in.',
    )
    parser.add_argument('--scale', choices=SCALES, required=True)
    parser.add_argument('--side', choices=SIDES, required=True)
    parser.add_argument('--pr', required=True, help='the PR being measured, PR-nn')
    parser.add_argument('--session', required=True, help='the session label')
    parser.add_argument('--date', default=None, help='the session date (default today)')
    parser.add_argument('--python', type=Path, required=True, help="the side's interpreter")
    parser.add_argument('--repo-root', type=Path, required=True, help="the side's checkout")
    parser.add_argument(
        '--schema', required=True, help='the served schema to update in place, never copied'
    )
    named = parser.add_mutually_exclusive_group()
    named.add_argument(
        '--bundles',
        metavar='DESCRIPTORS',
        default=None,
        help='the bundles to re-import or add, comma-separated, as the bundle import takes them',
    )
    named.add_argument(
        '--incremental-group',
        metavar='SCALE',
        choices=SCALES,
        default=None,
        help="re-import the incremental group of SCALE's import scenario: its largest bundle",
    )
    parser.add_argument(
        '--drop',
        metavar='DESCRIPTORS',
        default=None,
        help='the bundles to drop, comma-separated, as --delete-bundles takes them',
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        '--stop-before-switch',
        action='store_true',
        help='record the update alone, leaving its generation ready to switch',
    )
    mode.add_argument(
        '--switch-only',
        action='store_true',
        help='record the switch and purge alone, of a generation an earlier update left ready',
    )
    parser.add_argument(
        '--import-key',
        metavar='KEY=VALUE',
        action='append',
        default=[],
        help="an [import] key every invocation's configuration sets; repeatable",
    )
    args = parser.parse_args(argv)
    try:
        args.import_keys = parse_import_keys(args.import_key)
    except ValueError as e:
        parser.error(str(e))
    if args.switch_only and (
        args.bundles is not None or args.incremental_group is not None or args.drop is not None
    ):
        parser.error('--switch-only switches the generation an update left; it takes no bundles')
    if not args.switch_only and args.bundles is None and args.incremental_group is None:
        parser.error('give the bundles to update: --bundles or --incremental-group')
    return args


def update_request(args: argparse.Namespace) -> UpdateRequest:
    """Return the bundles the command line asks the update to change.

    Parameters:
        args: The parsed arguments, with ``--bundles`` or ``--incremental-group`` given.

    Returns:
        The request.

    Raises:
        GenerationError: If the named scale's scenario has no incremental group.
    """
    if args.bundles is not None:
        return UpdateRequest(bundles=args.bundles, drop=args.drop)
    scenario = load_scenario(args.incremental_group)
    if scenario.largest is None or not scenario.incremental:
        raise GenerationError(f'the {args.incremental_group} scenario has no incremental group')
    return UpdateRequest(bundles=scenario.largest, drop=args.drop)


def main(argv: Sequence[str] | None = None) -> None:
    """Run the update the command line asks for and record its runs.

    Parameters:
        argv: The arguments, or None for the command line's.
    """
    args = _parse_arguments(argv)
    require_no_pythonpath()
    config, _ = load_server_config()
    reexec_with_socket(
        config, 'benchmarks.bench_generation', sys.argv[1:] if argv is None else argv
    )
    side = Side(python=args.python.absolute(), repo_root=args.repo_root.resolve())
    spelling = Spelling.from_help(side.import_help())
    try:
        require_generations(spelling)
        update = None if args.switch_only else update_request(args)
    except GenerationError as e:
        sys.exit(str(e))
    server = MysqlServer(config)
    if not server.is_running():
        sys.exit(
            'the owned MySQL server is not running: start it with '
            '`python -m benchmarks.bench_server start`; this command never starts or stops it'
        )
    label = make_label(
        pr=args.pr, side=args.side, scale=args.scale, session=args.session, date=args.date
    )
    scenario = load_scenario(args.scale)
    web = web_scenarios.load_web_config().server
    bench = GenerationBench(
        schema=args.schema,
        web_ports=(web.port, web.memcached_port),
        is_listening=listening,
        server=server,
        side=side,
        spelling=spelling,
        label=label,
        scenario=scenario,
        cache_location=web.memcached_location,
        extra_import=args.import_keys,
    )
    environment: dict[str, Any] = {
        'import_keys': args.import_keys,
        **host_environment(),
        **side.environment(),
        **server_environment(server),
        'skipped_steps': list(spelling.skipped_steps),
        'import_scenario_hash': scenario_hash([scenario.path]),
        'bulk_load_path': DEFAULT_BULK_LOAD_PATH,
        'importers': None,
        'coordinator_importers': None,
        'generation_schema': args.schema,
        'schema': args.schema,
    }
    if update is not None:
        environment['generation_update'] = update.environment()
        run = bench.run_update(update)
        environment['bulk_load_path'] = file_bulk_load_path(label, [run])
        path = append_runs(label, environment, [run])
        wall = run['metrics'][f'{RUN_PREFIXES[GENERATION_UPDATE_KIND]}.wall_s']
        sys.stdout.write(f'update: {wall:.1f} s, recorded in {path}\n')
    if not args.stop_before_switch:
        run = bench.run_switch()
        environment['bulk_load_path'] = file_bulk_load_path(label, [run])
        path = append_runs(label, environment, [run])
        switch = run['metrics'][f'{METRIC_PREFIX}.switch.wall_s']
        purge = run['metrics'][f'{METRIC_PREFIX}.purge.wall_s']
        sys.stdout.write(f'switch: {switch:.1f} s, purge: {purge:.1f} s, recorded in {path}\n')


if __name__ == '__main__':
    main()
