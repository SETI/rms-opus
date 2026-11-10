"""Time import runs step by step, one side at a time, into the harness-owned server.

A **full run** is the whole sequence a database is built with: the erase, one
bundle-import invocation per group, then the finalization, the dictionary, Django's
migration, the validation and, where the side has it, the version step, each spelled
the way the side's own ``opus_import --help`` says (`benchmarks.sides.Spelling`) and
named by its role, so two sides' metrics line up. Each run imports into a schema of
its own; the newest run's schema is kept for `benchmarks.bench_db` and
`benchmarks.bench_web`, and the older ones are dropped. A run's ``import.wall_s`` is
the sum of its invocations' wall-clocks, so nothing the harness does between them --
building the fixture tree, expanding bundle descriptors -- is counted.

The fixture scale runs through `import_tests.tools.build_run.perform_run`; the test and
complete scales run the groups of their scenario file through
`import_tests.tools.build_run.run_pipeline_step`. At test scale a full run is followed
by the scenario's largest bundle imported alone into a fresh schema, and by the
incremental group: a copy of the finished schema (`benchmarks.bench_server.clone_schema`),
the largest bundle imported into it again, and the finalization sequence after.

Two more modes serve a change measured on clones, whose only change to the schema is
made by finalization. ``--stop-before-finalization`` makes the base's run end after the
bundle imports, leaving a fresh import in progress; ``--finalize-only --reuse-schema
NAME`` copies that schema into one of the side's own and runs the side's whole
finalization sequence on it. `benchmarks.compare` then holds the two sides'
finalization times to the ceiling the comparison applies in place of the import
guards.

Every timed import starts on a **freshly restarted server**: the owned mysqld is shut
down cleanly, which flushes its dirty pages and checkpoints its redo log, and started
again, before each full run, before the largest bundle's import alone, and between the
incremental group's copy and its append. Otherwise each run would inherit the dirty
pages and the redo the runs before it left, and a session's later runs would be slower
than its first by their position alone. Each run's details record the restarts and how
long each took (``server_restarts``).

At fixture and test scale the timed runs are preceded by one **warm-up import** of the
scale's bundles, without finalization, recorded as kind ``import_warmup`` and never
compared. The server reads its own files with ``O_DIRECT``, but the import reads the
holdings through the operating system's page cache, so without it a session's first run
would read them from disk and the rest from memory. The complete scale's holdings do not
fit in the page cache, so its runs have no warm-up.

A run fails, and records nothing, when an invocation exits non-zero, when a bundle
import leaves a bundle without a row in the permanent ``obs_general`` (or, in the
incremental group, without new rows), or when the run's ``ERRORS.log`` is not empty at
the end (or was not empty at the start).

Example, one side of a floor session at fixture scale::

    python -m benchmarks.bench_import --scale fixture --side before --pr PR-nn \\
        --session a --python venv-head/bin/python --repo-root .
"""

from __future__ import annotations

import argparse
import contextlib
import functools
import json
import math
import pstats
import shutil
import subprocess  # nosec B404 - the harness runs the side's import
import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

from benchmarks import web_scenarios
from benchmarks.bench_server import (
    DB_HOST,
    DB_PASSWORD,
    DB_USER,
    MysqlServer,
    clone_schema,
    counter_deltas,
    drop_schema,
    global_status,
    load_server_config,
    parse_import_keys,
    query,
    quote_identifier,
    reexec_with_socket,
    server_environment,
    write_opus_config,
)
from benchmarks.import_scenarios import (
    ImportScenario,
    holdings_for,
    load_scenario,
    require_empty_errors_log,
)
from benchmarks.monitor import InvocationMonitor, RunFailedError
from benchmarks.results import (
    RESULTS_DIR,
    SCALES,
    SIDES,
    Label,
    append_runs,
    host_environment,
    load_result,
    make_label,
    new_run,
    scenario_hash,
)
from benchmarks.sides import Side, Spelling, require_no_pythonpath
from import_tests.tools import build_run, run_logs
from import_tests.tools.golden_io import DatabaseCredentials
from opus_config.config import DEFAULT_CPU_FRACTION, detected_cores

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

#: The server counters whose movement over a run every import result records. The
#: data, redo and flushed-page counts and the waits for a free page show whether a run
#: reached the server's sustained write limit, as does the run's peak checkpoint age
#: (`benchmarks.monitor.checkpoint_age`).
IMPORT_COUNTERS = (
    'Innodb_rows_inserted',
    'Com_commit',
    'Com_insert',
    'Innodb_data_written',
    'Innodb_os_log_written',
    'Innodb_buffer_pool_pages_flushed',
    'Innodb_buffer_pool_wait_free',
    'Innodb_buffer_pool_read_requests',
    'Innodb_buffer_pool_reads',
    'Com_create_table',
    'Com_alter_table',
)

#: How many functions a profiled run keeps, by cumulative time.
PROFILE_TOP = 20

#: What the result records as the bulk-load path while the import's log names none.
DEFAULT_BULK_LOAD_PATH = 'insert_rows packets'

#: The seconds the sampler's checkpoint-age read may wait. A read that stalls is a sample
#: missed, and must not stop the memory samples taken on the same thread.
STATUS_READ_TIMEOUT_S = 5

#: How an import log line naming the bulk-load path starts. The harness reads either
#: side's log as text rather than importing the side's code, so this repeats
#: ``opus_import.importdb.mysql.BULK_LOAD_PATH_PREFIX``, and a unit test holds the two
#: equal.
BULK_LOAD_PATH_PREFIX = 'Bulk load path: '

#: What the result records as the start method while the import reports none.
DEFAULT_START_METHOD = 'not reported by the import'

#: The roles of the finalization sequence's invocations (`Spelling.role`).
FINALIZATION_ROLES = (
    'finalize',
    'import_dictionary',
    'migrate',
    'validate',
    'write_schema_version',
)


class ImportBench:
    """Runs one side's import runs at one scale and turns them into result runs."""

    def __init__(
        self,
        *,
        server: MysqlServer,
        side: Side,
        spelling: Spelling,
        label: Label,
        scenario: ImportScenario,
        cache_location: str,
        extra_import: Mapping[str, object] | None = None,
    ) -> None:
        """Prepare to run imports.

        Parameters:
            server: The owned server, running.
            side: The side being measured.
            spelling: The side's spelling of each step.
            label: The result file's label.
            scenario: The scale's import scenario.
            cache_location: The memcached the configuration names. Nothing listens there
                during an import; the migration's settings probe it and fall back.
            extra_import: Further ``[import]`` keys every run's configuration sets, or
                None for none.
        """
        self.server = server
        self.side = side
        self.spelling = spelling
        self.label = label
        self.scenario = scenario
        self.cache_location = cache_location
        self.extra_import = dict(extra_import or {})

    @functools.cached_property
    def schema_version(self) -> int | None:
        """The side's ``SCHEMA_VERSION``, read once through its interpreter, or None."""
        return self.side.schema_version()

    def schema_name(self, index: int | str, suffix: str = '') -> str:
        """Return the schema of one run.

        Parameters:
            index: The run's index among the label's runs, or a word naming the schema.
            suffix: ``_largest`` or ``_incremental`` for the extra schemas.

        Returns:
            ``bench_<scale>_<side>_<session>_<index><suffix>``.
        """
        label = self.label
        return f'bench_{label.scale}_{label.side}_{label.session}_{index}{suffix}'

    def fresh_server(self, run: dict[str, Any], before: str) -> None:
        """Restart the owned server cleanly before a timed import, and record it.

        A clean shutdown flushes every dirty page and checkpoints the redo log, so the
        import that follows starts from the same server state as every other.

        Parameters:
            run: The result run, whose ``server_restarts`` detail gains the restart's
                wall-clock under `before`.
            before: What the restart precedes: ``run``, ``largest_alone``,
                ``incremental`` or ``finalize``.
        """
        started = time.perf_counter()
        self.server.restart()
        run['details'].setdefault('server_restarts', {})[before] = time.perf_counter() - started

    def _monitor(self, schema: str, timing_file: Path, config_file: Path) -> InvocationMonitor:
        """Return a monitor for one run into one schema.

        Parameters:
            schema: The schema the run imports into.
            timing_file: Where each invocation writes its timings.
            config_file: The ``OPUS_CONFIG`` the side's bundle expansion reads.

        Returns:
            The monitor.
        """

        def expand(groups: Sequence[str]) -> list[list[str]]:
            """Expand descriptor groups with the side's own interpreter."""
            env = self.server.client_environment(config_file)
            expanded: list[list[str]] = self.side.probe(
                ['expand', json.dumps(list(groups))], env=env
            )
            return expanded

        return InvocationMonitor(
            server=self.server,
            schema=schema,
            spelling=self.spelling,
            expand=expand,
            timing_file=None if self.spelling.timing_json is None else timing_file,
            excluded_pids=lambda: {pid for pid in (self.server.pid(),) if pid is not None},
            status_connection=functools.partial(
                self.server.connect, read_timeout=STATUS_READ_TIMEOUT_S
            ),
        )

    def _invoke(
        self,
        monitor: InvocationMonitor,
        config_file: Path,
        arguments: Sequence[str],
        *,
        profile_to: Path | None = None,
    ) -> list[dict[str, Any]] | None:
        """Run one ``opus_import`` invocation under the monitor.

        Parameters:
            monitor: The run's monitor.
            config_file: The run's configuration.
            arguments: The command line after ``-m opus_import``.
            profile_to: A ``.prof`` file to profile the invocation into, or None.

        Returns:
            The profile's top functions when profiled, else None.
        """
        monitor.step_started(arguments)
        if profile_to is None:
            result = build_run.run_pipeline_step(
                config_file, arguments, python=self.side.python, repo_root=self.side.repo_root
            )
        else:
            finished = subprocess.run(  # nosec B603 - the side's interpreter
                [
                    str(self.side.python),
                    '-m',
                    'cProfile',
                    '-o',
                    str(profile_to),
                    '-m',
                    'opus_import',
                    *arguments,
                ],
                cwd=self.side.repo_root,
                env=build_run.run_environment(config_file),
                capture_output=True,
                text=True,
                check=False,
            )
            result = build_run.StepResult(
                arguments=tuple(arguments),
                returncode=finished.returncode,
                stdout=finished.stdout,
                stderr=finished.stderr,
            )
        monitor.step_finished(result)
        return None if profile_to is None else top_functions(profile_to)

    def _migrate(self, monitor: InvocationMonitor, config_file: Path) -> None:
        """Run Django's migration under the monitor.

        Parameters:
            monitor: The run's monitor.
            config_file: The run's configuration.
        """
        monitor.step_started(build_run.MIGRATE_ARGS)
        result = build_run.run_migrate(
            config_file, python=self.side.python, repo_root=self.side.repo_root
        )
        monitor.step_finished(result)

    def _prepare(
        self, run_dir: Path, schema: str
    ) -> tuple[Path, Path, InvocationMonitor, tuple[str, ...]]:
        """Write a run's configuration in a fresh run directory, and make its monitor.

        Parameters:
            run_dir: The run's directory; anything already there is removed.
            schema: The schema the run writes.

        Returns:
            The configuration file, the run's ``ERRORS.log`` (checked empty here), the
            monitor, and the ``--timing-json`` options.
        """
        if run_dir.exists():
            shutil.rmtree(run_dir)
        pds3, pds4 = holdings_for(self.label)
        config_file = write_opus_config(
            run_dir / 'opus.toml',
            schema=schema,
            pds3_holdings=pds3,
            pds4_holdings=pds4,
            run_dir=run_dir,
            cache_location=self.cache_location,
            extra_import=self.extra_import,
        )
        errors_log = run_dir / 'logs' / build_run.ERRORS_LOG
        require_empty_errors_log(errors_log)
        timing_file = run_dir / 'timing.json'
        monitor = self._monitor(schema, timing_file, config_file)
        return config_file, errors_log, monitor, self.spelling.timing_args(timing_file)

    def _finalization(
        self, monitor: InvocationMonitor, config_file: Path, timing: Sequence[str]
    ) -> None:
        """Run the finalization sequence after the bundle imports.

        Parameters:
            monitor: The run's monitor.
            config_file: The run's configuration.
            timing: The ``--timing-json`` options, or none.
        """
        self._invoke(monitor, config_file, [self.spelling.finalize, *timing])
        self._invoke(monitor, config_file, [*build_run.DICTIONARY_ARGS, *timing])
        self._migrate(monitor, config_file)
        self._invoke(monitor, config_file, [self.spelling.validate, *timing])
        if len(self.spelling.write_schema_version) > 0:
            self._invoke(monitor, config_file, [*self.spelling.write_schema_version, *timing])

    def run_fixture(self, index: int | str, *, finalize: bool = True) -> tuple[dict[str, Any], str]:
        """Import the fixture through `build_run.perform_run`.

        Parameters:
            index: The run's index, or ``warmup``.
            finalize: False to stop after the bundle imports.

        Returns:
            The result run, and the schema it built.
        """
        run_dir = self.label.scratch_dir / f'import_{index}'
        if run_dir.exists():
            shutil.rmtree(run_dir)
        schema = self.schema_name(index)
        drop_schema(self.server, schema)
        paths = build_run.RunPaths.under(run_dir)
        require_empty_errors_log(paths.errors_log)
        timing_file = run_dir / 'timing.json'
        timing = self.spelling.timing_args(timing_file)
        monitor = self._monitor(schema, timing_file, paths.config_file)
        bundles = build_run.fixture_bundles()
        monitor.expect_groups(bundles)
        credentials = DatabaseCredentials(host=DB_HOST, user=DB_USER, password=DB_PASSWORD)
        run = new_run('import' if finalize else 'import_unfinalized')
        self.fresh_server(run, 'run')
        before = self._status()
        build_run.perform_run(
            run_dir,
            schema,
            credentials,
            bundle_groups=[[bundle] for bundle in bundles],
            finalize=finalize,
            python=self.side.python,
            repo_root=self.side.repo_root,
            drop_args=[*self.spelling.erase, *timing],
            import_args=[self.spelling.bundle_import, *timing],
            aux_args=[self.spelling.finalize, *timing],
            dictionary_args=[*build_run.DICTIONARY_ARGS, *timing],
            validate_args=[self.spelling.validate, *timing],
            version_args=(
                [*self.spelling.write_schema_version, *timing]
                if len(self.spelling.write_schema_version) > 0
                else []
            ),
            observer=monitor,
            # The suite's stated host size is left out: the harness measures this
            # machine, whose cores the import counts, and a side older than the key
            # would refuse it.
            extra_import={'cpus': None, **self.extra_import},
        )
        require_empty_errors_log(paths.errors_log, at_end=True)
        self._fill_run(run, monitor, schema, before, full=finalize, log_dir=paths.log_dir)
        return run, schema

    def run_holdings(
        self, index: int | str, *, profile: bool, finalize: bool = True
    ) -> tuple[dict[str, Any], str]:
        """Import a holdings scale's groups, then the extra test-scale groups.

        Parameters:
            index: The run's index, or ``warmup``.
            profile: Whether to profile each bundle-import invocation with cProfile.
            finalize: False to stop after the bundle imports, skipping the extra groups.

        Returns:
            The result run, and the schema it built.
        """
        scenario = self.scenario
        schema = self.schema_name(index)
        drop_schema(self.server, schema)
        run_dir = self.label.scratch_dir / f'import_{index}'
        config_file, errors_log, monitor, timing = self._prepare(run_dir, schema)
        monitor.expect_groups([group.bundles for group in scenario.groups])
        monitor.expand_groups()
        kind = 'import_profile' if profile else 'import'
        run = new_run(kind if finalize else 'import_unfinalized')
        profiles: dict[str, Any] = {}
        self.fresh_server(run, 'run')
        before = self._status()
        self._invoke(monitor, config_file, [*self.spelling.erase, *timing])
        for position, group in enumerate(scenario.groups):
            profile_to = run_dir / f'bundle_import_{position}.prof' if profile else None
            top = self._invoke(
                monitor,
                config_file,
                [self.spelling.bundle_import, *group.options, *timing, group.bundles],
                profile_to=profile_to,
            )
            if top is not None:
                profiles[group.bundles] = top
        if finalize:
            self._finalization(monitor, config_file, timing)
        require_empty_errors_log(errors_log, at_end=True)
        self._fill_run(
            run,
            monitor,
            schema,
            before,
            full=finalize,
            log_dir=errors_log.parent,
        )
        if len(profiles) > 0:
            run['details']['profile_top_cumulative'] = profiles
        if finalize and scenario.largest is not None and scenario.largest_alone:
            self._largest_alone(run, index)
        if finalize and scenario.largest is not None and scenario.incremental:
            self._incremental(run, index, schema)
        return run, schema

    def warm_up(self) -> dict[str, Any]:
        """Import the scale's bundles once, untimed, so the timed runs read warm holdings.

        The server reads its own files with ``O_DIRECT``, so every run starts on a cold
        buffer pool, but the import reads the holdings through the operating system's
        page cache. Without this the session's first run would read them from disk and
        its later runs from memory, by an amount set by whatever the computer did before
        the session.

        Returns:
            The run, of kind ``import_warmup``, which is recorded but never compared.
        """
        if self.label.scale == 'fixture':
            run, schema = self.run_fixture('warmup', finalize=False)
        else:
            run, schema = self.run_holdings('warmup', profile=False, finalize=False)
        drop_schema(self.server, schema)
        run['kind'] = 'import_warmup'
        return run

    def run_finalize_only(self, source: str) -> tuple[dict[str, Any], str]:
        """Copy an unfinalized schema into one of the side's own, and finalize the copy.

        Parameters:
            source: A schema a run stopped before finalization built.

        Returns:
            The result run, of kind ``finalize``, and the copy it finalized.
        """
        schema = self.schema_name('finalized')
        clone_s = clone_schema(self.server, source, schema, version=self.schema_version)
        run_dir = self.label.scratch_dir / 'finalize'
        config_file, errors_log, monitor, timing = self._prepare(run_dir, schema)
        run = new_run('finalize')
        self.fresh_server(run, 'finalize')
        before = self._status()
        self._finalization(monitor, config_file, timing)
        require_empty_errors_log(errors_log, at_end=True)
        self._fill_run(
            run,
            monitor,
            schema,
            before,
            full=False,
            log_dir=errors_log.parent,
        )
        run['metrics']['import.finalize_clone_s'] = clone_s
        run['details']['source_schema'] = source
        return run, schema

    def _largest_alone(self, run: dict[str, Any], index: int | str) -> None:
        """Import the largest bundle alone into a fresh schema, and record it.

        Parameters:
            run: The result run to add the metrics to.
            index: The run's index.
        """
        bundle = self.scenario.largest
        assert bundle is not None
        schema = self.schema_name(index, '_largest')
        drop_schema(self.server, schema)
        run_dir = self.label.scratch_dir / f'import_{index}_largest'
        config_file, errors_log, monitor, timing = self._prepare(run_dir, schema)
        monitor.expect_groups([bundle])
        monitor.expand_groups()
        self.fresh_server(run, 'largest_alone')
        self._invoke(monitor, config_file, [*self.spelling.erase, *timing])
        self._invoke(monitor, config_file, [self.spelling.bundle_import, *timing, bundle])
        require_empty_errors_log(errors_log, at_end=True)
        record = monitor.records[-1]
        run['metrics']['import.largest_alone.wall_s'] = record.wall_s
        run['metrics']['import.largest_alone.peak_tree_pss_kb'] = record.peak_tree_pss_kb
        run['details']['largest_alone'] = monitor.summary()
        drop_schema(self.server, schema)

    def run_sweep(self, workers: int) -> dict[str, Any]:
        """Import the largest bundle alone with a given number of workers, and record it.

        Parameters:
            workers: The ``[import] workers`` the import runs with.

        Returns:
            The result run, of kind ``import_sweep``: the import's wall-clock, its rows
            per second, and the process tree's peak PSS, with the worker count.
        """
        bundle = self.scenario.largest
        assert bundle is not None
        run = new_run('import_sweep')
        schema = self.schema_name(f'sweep_{workers}')
        drop_schema(self.server, schema)
        run_dir = self.label.scratch_dir / f'import_sweep_{workers}'
        saved = self.extra_import
        self.extra_import = {**saved, 'workers': workers}
        try:
            config_file, errors_log, monitor, timing = self._prepare(run_dir, schema)
        finally:
            self.extra_import = saved
        monitor.expect_groups([bundle])
        monitor.expand_groups()
        self.fresh_server(run, 'sweep')
        self._invoke(monitor, config_file, [*self.spelling.erase, *timing])
        self._invoke(monitor, config_file, [self.spelling.bundle_import, *timing, bundle])
        require_empty_errors_log(errors_log, at_end=True)
        record = monitor.records[-1]
        rows = self._rows(schema, bundle)
        run['metrics']['import.sweep.wall_s'] = record.wall_s
        run['metrics']['import.sweep.rows_per_s'] = rows / record.wall_s
        run['metrics']['import.sweep.peak_tree_pss_kb'] = record.peak_tree_pss_kb
        run['details'] = {'workers': workers, 'bundle': bundle, 'obs_general_rows': rows}
        drop_schema(self.server, schema)
        return run

    def _rows(self, schema: str, bundle: str) -> int:
        """Return how many ``obs_general`` rows a bundle has in a schema."""
        statement = (
            f'SELECT COUNT(*) FROM {quote_identifier(schema)}.obs_general '  # nosec B608 - quoted identifier
            'WHERE bundle_id = %s'
        )
        with contextlib.closing(self.server.connect()) as connection:
            return int(query(connection, statement, [bundle])[0][0])

    def _incremental(self, run: dict[str, Any], index: int | str, source: str) -> None:
        """Append the largest bundle to a copy of the finished schema, and finalize.

        The copy already holds the bundle, so the usual check that it has rows would
        pass whether or not the append wrote anything; the bundle's largest
        ``obs_general.id`` has to grow instead, since every row the append writes takes
        a new id.

        Parameters:
            run: The result run to add the metrics to.
            index: The run's index.
            source: The finished schema to copy.

        Raises:
            RunFailedError: If the append left the bundle's rows as they were.
        """
        bundle = self.scenario.largest
        assert bundle is not None
        schema = self.schema_name(index, '_incremental')
        clone_s = clone_schema(self.server, source, schema, version=self.schema_version)
        run_dir = self.label.scratch_dir / f'import_{index}_incremental'
        config_file, errors_log, monitor, timing = self._prepare(run_dir, schema)
        monitor.expect_groups([bundle])
        monitor.expand_groups()
        before_id = self._largest_id(schema, bundle)
        self.fresh_server(run, 'incremental')
        self._invoke(monitor, config_file, [self.spelling.bundle_import, *timing, bundle])
        after_id = self._largest_id(schema, bundle)
        if after_id <= before_id:
            raise RunFailedError(
                f'appending {bundle} to {schema} left its largest obs_general id at '
                f'{after_id} (it was {before_id}): the append wrote no rows'
            )
        self._finalization(monitor, config_file, timing)
        require_empty_errors_log(errors_log, at_end=True)
        run['metrics']['import.incremental.clone_s'] = clone_s
        run['metrics']['import.incremental.wall_s'] = sum(r.wall_s for r in monitor.records)
        run['details']['incremental'] = monitor.summary()
        drop_schema(self.server, schema)

    def _largest_id(self, schema: str, bundle: str) -> int:
        """Return a bundle's largest ``obs_general.id`` in a schema.

        Parameters:
            schema: The schema.
            bundle: The bundle.

        Returns:
            The id, or 0 when the bundle has no rows.
        """
        statement = (
            f'SELECT COALESCE(MAX(id), 0) FROM {quote_identifier(schema)}.obs_general '  # nosec B608 - quoted identifier
            'WHERE bundle_id = %s'
        )
        with contextlib.closing(self.server.connect()) as connection:
            return int(query(connection, statement, [bundle])[0][0])

    def _status(self) -> dict[str, int]:
        """Return the server's global counters now."""
        with contextlib.closing(self.server.connect()) as connection:
            return global_status(connection)

    def _fill_run(
        self,
        run: dict[str, Any],
        monitor: InvocationMonitor,
        schema: str,
        before: dict[str, int],
        *,
        full: bool,
        log_dir: Path,
    ) -> None:
        """Turn a finished run's records into its metrics and details.

        Parameters:
            run: The result run to fill.
            monitor: The run's monitor.
            schema: The schema it built.
            before: The server's counters when it started.
            full: Whether the run was a full one, which alone gets ``import.wall_s``.
            log_dir: The run's log directory, whose information-level import logs
                name the bulk-load path each invocation took.
        """
        metrics = run['metrics']
        records = monitor.records
        phases: dict[str, float] = {}
        for record in records:
            metrics[f'import.invocation.{record.name}.wall_s'] = record.wall_s
            for step, seconds in record.timings.items():
                if step != 'total':
                    phases[step] = phases.get(step, 0.0) + seconds
        for step, seconds in phases.items():
            metrics[f'import.phase.{step}_s'] = seconds
        bundle_wall = sum(r.wall_s for r in records if monitor.is_bundle_import(r.arguments))
        finalization = [r for r in records if r.name in FINALIZATION_ROLES]
        if full:
            metrics['import.wall_s'] = sum(r.wall_s for r in records)
        if bundle_wall > 0:
            metrics['import.bundle_imports.wall_s'] = bundle_wall
        if len(finalization) > 0:
            metrics['import.finalization.wall_s'] = sum(r.wall_s for r in finalization)
        # The import's memory: the opus_import processes, not Django's migration.
        importing = [r for r in records if r.name != 'migrate']
        metrics['import.peak_tree_pss_kb'] = max(r.peak_tree_pss_kb for r in importing)
        metrics['import.peak_rss_kb'] = max(r.peak_rss_kb for r in importing)
        ages = [
            r.peak_checkpoint_age_bytes for r in records if r.peak_checkpoint_age_bytes is not None
        ]
        if len(ages) > 0:
            metrics['import.server.peak_checkpoint_age_bytes'] = max(ages)
        with contextlib.closing(self.server.connect()) as connection:
            after = global_status(connection)
            by_bundle = {
                str(bundle): int(count)
                for bundle, count in query(
                    connection,
                    f'SELECT bundle_id, COUNT(*) FROM {quote_identifier(schema)}.obs_general '  # nosec B608 - quoted identifier
                    'GROUP BY bundle_id',
                )
            }
        for name, delta in counter_deltas(before, after, IMPORT_COUNTERS).items():
            metrics[f'import.server.{name}'] = delta
        rows = sum(by_bundle.values())
        if bundle_wall > 0:
            metrics['import.obs_general_rows_per_s'] = rows / bundle_wall
        details = run['details']
        details.update(monitor.summary())
        details['schema'] = schema
        details['bulk_load_paths'] = bulk_load_paths(log_dir)
        details['obs_general_rows'] = rows
        details['obs_general_rows_by_bundle'] = by_bundle
        details['bundle_count'] = len(by_bundle)
        if bundle_wall > 0 and len(by_bundle) > 0:
            self._record_largest(run, by_bundle)

    def _record_largest(self, run: dict[str, Any], by_bundle: dict[str, int]) -> None:
        """Record the largest bundle's rows and its ``--import`` time in the run.

        The time is the bundle's own ``import_bundle:<bundle>`` step from the invocation
        that imported it, so a bundle imported in a group is timed apart from the
        group's other bundles.

        Parameters:
            run: The result run, its invocations already recorded.
            by_bundle: The run's ``obs_general`` rows per bundle.
        """
        named = self.scenario.largest
        largest = named if named is not None else max(by_bundle, key=lambda b: by_bundle[b])
        run['details']['largest_bundle'] = largest
        run['details']['largest_bundle_named_by'] = 'scenario' if named is not None else 'rows'
        run['metrics']['import.largest.obs_general_rows'] = by_bundle.get(largest, 0)
        step = f'import.phase.import_bundle:{largest}_s'
        if step in run['metrics']:
            run['metrics']['import.largest.import_s'] = run['metrics'][step]


def bulk_load_paths(log_dir: Path) -> list[str]:
    """Return the bulk-load paths a run's import logs name, each once, in the order named.

    Every invocation names its path when it connects, and again if the server refuses a
    load partway through, so a run's logs can name both.

    Parameters:
        log_dir: The run's log directory (`build_run.import_logs`).

    Returns:
        The paths, without the reason the log gives for one; empty when the side's
        import names none.
    """
    paths: list[str] = []
    for import_log in build_run.import_logs(log_dir):
        for message in run_logs.read_messages(import_log):
            if message.startswith(BULK_LOAD_PATH_PREFIX):
                path = message.removeprefix(BULK_LOAD_PATH_PREFIX).split(' (', 1)[0]
                if path not in paths:
                    paths.append(path)
    return paths


def summarize_bulk_load_paths(runs: Sequence[dict[str, Any]]) -> str:
    """Return every bulk-load path a result's runs took, for its environment.

    Parameters:
        runs: The runs, in the order they were recorded.

    Returns:
        Each path any run's logs named, once, in the order first named, joined by commas.
        A run whose logs name none took `DEFAULT_BULK_LOAD_PATH`; a run that records no
        paths at all (one that imported nothing) adds nothing. With no path from any run,
        `DEFAULT_BULK_LOAD_PATH`.
    """
    paths: list[str] = []
    for run in runs:
        named = run.get('details', {}).get('bulk_load_paths')
        if named is None:
            continue
        for path in named if len(named) > 0 else [DEFAULT_BULK_LOAD_PATH]:
            if path not in paths:
                paths.append(path)
    return ', '.join(paths) if len(paths) > 0 else DEFAULT_BULK_LOAD_PATH


def file_bulk_load_path(label: Label, new_runs: Sequence[dict[str, Any]]) -> str:
    """Return the bulk-load paths of a label's file once new runs are added to it.

    The environment is the file's, not one run's, so its entry covers every run the file
    holds as well as the ones being added (`summarize_bulk_load_paths`).

    Parameters:
        label: The label whose file the runs are added to.
        new_runs: The runs about to be added.

    Returns:
        The summary of the file's runs and the new ones.
    """
    path = RESULTS_DIR / label.file_name
    existing = load_result(path)['runs'] if path.exists() else []
    return summarize_bulk_load_paths([*existing, *new_runs])


def top_functions(profile: Path) -> list[dict[str, Any]]:
    """Return the functions with the highest cumulative time in a cProfile output file.

    Parameters:
        profile: The ``.prof`` file.

    Returns:
        Up to `PROFILE_TOP` entries, highest first, each with the function, its call
        count and its cumulative and own seconds.
    """
    stats = pstats.Stats(str(profile))
    entries = []
    for (filename, line, function), (_, calls, own, cumulative, _) in stats.stats.items():  # type: ignore[attr-defined]  # pstats keeps its table untyped
        entries.append(
            {
                'function': f'{Path(filename).name}:{line}({function})',
                'calls': calls,
                'cumulative_s': cumulative,
                'own_s': own,
            }
        )
    entries.sort(key=lambda entry: entry['cumulative_s'], reverse=True)
    return entries[:PROFILE_TOP]


#: The scales whose holdings fit in the page cache, so a session's import runs are
#: preceded by one untimed warm-up import (`ImportBench.warm_up`). The complete scale's
#: do not fit, so each of its runs reads them from disk alike.
WARMED_SCALES = ('fixture', 'test')


def _parse_arguments(argv: Sequence[str] | None) -> argparse.Namespace:
    """Read the command line, and refuse combinations that measure nothing coherent.

    Parameters:
        argv: The arguments, or None for the command line's.

    Returns:
        The parsed arguments.
    """
    parser = argparse.ArgumentParser(
        prog='python -m benchmarks.bench_import',
        description='Time import runs of one side into the harness-owned MySQL server.',
    )
    parser.add_argument('--scale', choices=SCALES, required=True)
    parser.add_argument('--side', choices=SIDES, required=True)
    parser.add_argument('--pr', required=True, help='the PR being measured, PR-nn')
    parser.add_argument('--session', required=True, help='the session label')
    parser.add_argument('--date', default=None, help='the session date (default today)')
    parser.add_argument('--python', type=Path, required=True, help="the side's interpreter")
    parser.add_argument('--repo-root', type=Path, required=True, help="the side's checkout")
    parser.add_argument(
        '--runs', type=int, default=None, help="runs to make (default: the scenario's)"
    )
    parser.add_argument(
        '--profile',
        action='store_true',
        help='profile each bundle import with cProfile (test and complete scales); the '
        'run is recorded as kind import_profile, apart from the timed runs',
    )
    parser.add_argument(
        '--stop-before-finalization',
        action='store_true',
        help='end each run after the bundle imports, leaving a fresh import in progress',
    )
    parser.add_argument(
        '--reuse-schema',
        metavar='NAME',
        default=None,
        help="import nothing: record NAME as this side's schema, or with --clone a copy of "
        'it, or with --finalize-only a finalized copy of it',
    )
    parser.add_argument(
        '--clone',
        action='store_true',
        help="with --reuse-schema, copy the schema into one of this side's own and time it",
    )
    parser.add_argument(
        '--finalize-only',
        action='store_true',
        help="with --reuse-schema, copy the schema into one of this side's own and run this "
        "side's finalization sequence on the copy",
    )
    parser.add_argument(
        '--import-key',
        metavar='KEY=VALUE',
        action='append',
        default=[],
        help="an [import] key every run's configuration sets, such as index_workers=22; "
        'repeatable. A whole number or true or false is written as one, anything else as '
        'a string',
    )
    parser.add_argument(
        '--workers-sweep',
        metavar='N,N,...',
        default=None,
        help="instead of the timed runs, import the scenario's largest bundle alone once per "
        "worker count, each capped at the ceiling the side's [import] cpus and cpu_fraction "
        'give and each distinct count run once; recorded as kind import_sweep, in a session '
        'of its own, to choose a count rather than to be judged',
    )
    args = parser.parse_args(argv)
    try:
        args.import_keys = parse_import_keys(args.import_key)
    except ValueError as e:
        parser.error(str(e))
    if args.workers_sweep is not None:
        try:
            requested = [int(text) for text in args.workers_sweep.split(',')]
        except ValueError:
            parser.error('--workers-sweep takes whole numbers separated by commas')
        if any(count < 1 for count in requested):
            parser.error('--workers-sweep takes counts of at least 1')
        try:
            args.sweep_counts = sweep_counts(requested, args.import_keys)
        except ValueError as e:
            parser.error(str(e))
        if args.reuse_schema is not None or args.stop_before_finalization or args.profile:
            parser.error('--workers-sweep runs imports of its own and takes no other mode')
    if args.profile and args.scale == 'fixture':
        parser.error('--profile profiles the bundle imports of the test and complete scales')
    if (args.clone or args.finalize_only) and args.reuse_schema is None:
        parser.error('--clone and --finalize-only take the schema --reuse-schema names')
    if args.clone and args.finalize_only:
        parser.error('--finalize-only already copies the schema; leave out --clone')
    if args.reuse_schema is not None and (args.stop_before_finalization or args.profile):
        parser.error('--reuse-schema imports nothing, so it takes no import options')
    return args


def main(argv: Sequence[str] | None = None) -> None:
    """Run the import benchmark the command line asks for and record its runs.

    Parameters:
        argv: The arguments, or None for the command line's.
    """
    args = _parse_arguments(argv)
    require_no_pythonpath()
    config, _ = load_server_config()
    reexec_with_socket(config, 'benchmarks.bench_import', sys.argv[1:] if argv is None else argv)
    server = MysqlServer(config)
    side = Side(python=args.python.absolute(), repo_root=args.repo_root.resolve())
    spelling = Spelling.from_help(side.import_help())
    label = make_label(
        pr=args.pr, side=args.side, scale=args.scale, session=args.session, date=args.date
    )
    scenario = load_scenario(args.scale)
    bench = ImportBench(
        server=server,
        side=side,
        spelling=spelling,
        label=label,
        scenario=scenario,
        cache_location=web_scenarios.load_web_config().server.memcached_location,
        extra_import=args.import_keys,
    )
    environment: dict[str, Any] = {
        'import_keys': args.import_keys,
        **host_environment(),
        **side.environment(),
        'skipped_steps': list(spelling.skipped_steps),
        'import_scenario_hash': scenario_hash([scenario.path]),
        'import_start_method': DEFAULT_START_METHOD,
        'bulk_load_path': DEFAULT_BULK_LOAD_PATH,
    }
    with server.running():
        environment.update(server_environment(server))
        if args.reuse_schema is not None:
            if args.finalize_only:
                run, schema = bench.run_finalize_only(args.reuse_schema)
            else:
                schema = args.reuse_schema
                run = new_run('import_reuse')
                if args.clone:
                    schema = bench.schema_name('clone')
                    run['metrics']['import.clone_s'] = clone_schema(
                        server, args.reuse_schema, schema, version=bench.schema_version
                    )
                run['details'] = {'reused_schema': args.reuse_schema, 'schema': schema}
            environment['schema'] = schema
            environment['bulk_load_path'] = file_bulk_load_path(label, [run])
            path = append_runs(label, environment, [run])
            sys.stdout.write(f'recorded in {path}\n')
            return
        if args.workers_sweep is not None:
            if scenario.largest is None:
                sys.exit(f'the {args.scale} scenario names no largest bundle to sweep')
            if args.scale in WARMED_SCALES:
                warm_up = bench.warm_up()
                append_runs(label, environment, [warm_up])
            for workers in args.sweep_counts:
                run = bench.run_sweep(workers)
                environment['bulk_load_path'] = file_bulk_load_path(label, [run])
                path = append_runs(label, environment, [run])
                wall = run['metrics']['import.sweep.wall_s']
                sys.stdout.write(f'workers {workers}: {wall:.1f} s, recorded in {path}\n')
            return
        finalize = not args.stop_before_finalization
        count = scenario.runs if args.runs is None else args.runs
        existing = _existing_import_runs(label)
        if args.scale in WARMED_SCALES:
            warm_up = bench.warm_up()
            environment['bulk_load_path'] = file_bulk_load_path(label, [warm_up])
            path = append_runs(label, environment, [warm_up])
            sys.stdout.write(f'warm-up import recorded in {path}\n')
        for offset in range(count):
            index = existing + offset + 1
            if args.scale == 'fixture':
                run, schema = bench.run_fixture(index, finalize=finalize)
            else:
                run, schema = bench.run_holdings(index, profile=args.profile, finalize=finalize)
            environment['schema'] = schema
            environment['bulk_load_path'] = file_bulk_load_path(label, [run])
            path = append_runs(label, environment, [run])
            if index > 1:
                drop_schema(server, bench.schema_name(index - 1))
            wall = run['metrics'].get(
                'import.wall_s', run['metrics']['import.bundle_imports.wall_s']
            )
            sys.stdout.write(f'import run {index}: {wall:.1f} s, recorded in {path}\n')


def sweep_counts(requested: Sequence[int], import_keys: Mapping[str, object]) -> list[int]:
    """Return the worker counts a sweep runs: each capped at the ceiling, each once.

    Parameters:
        requested: The counts asked for.
        import_keys: The ``[import]`` keys every run sets, whose ``cpus`` and
            ``cpu_fraction``, when given, decide the ceiling as the import does.

    Returns:
        The distinct capped counts, in the order first asked for.

    Raises:
        ValueError: If ``cpus`` is not a whole number of at least 1, or ``cpu_fraction``
            is not a number greater than 0 and at most 1.
    """
    cpus = import_keys.get('cpus')
    if cpus is not None and (isinstance(cpus, bool) or not isinstance(cpus, int) or cpus < 1):
        raise ValueError(f'--import-key cpus must be a whole number of at least 1, not {cpus!r}')
    cores = cpus if isinstance(cpus, int) else detected_cores()
    fraction = import_keys.get('cpu_fraction', DEFAULT_CPU_FRACTION)
    if (
        isinstance(fraction, bool)
        or not isinstance(fraction, (int, float))
        or not 0 < fraction <= 1
    ):
        raise ValueError(
            f'--import-key cpu_fraction must be greater than 0 and at most 1, not {fraction!r}'
        )
    ceiling = max(1, math.floor(cores * fraction))
    counts: list[int] = []
    for count in requested:
        capped = min(count, ceiling)
        if capped not in counts:
            counts.append(capped)
    return counts


def _existing_import_runs(label: Label) -> int:
    """Return how many runs that imported a schema a label's result file already holds.

    Parameters:
        label: The label.

    Returns:
        The count, zero when there is no file yet.
    """
    path = RESULTS_DIR / label.file_name
    if not path.exists():
        return 0
    kinds = {'import', 'import_profile', 'import_unfinalized'}
    return sum(1 for run in load_result(path)['runs'] if run['kind'] in kinds)


if __name__ == '__main__':
    main()
