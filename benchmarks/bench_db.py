"""Measure the schema an import built: sizes, indexes, plans, and index usage.

It first empties the search tables with the side's own reset option, because the
per-search tables an earlier web run left are not part of what the import built. Then
it runs ``ANALYZE TABLE`` on every table and sets
``information_schema_stats_expiry = 0`` on its connection, so nothing it reads comes
from stale statistics. Then it records, per table and for the schema: data and index
bytes and the exact row count, the index count, and the largest mult id of each mult
field (``MAX(id)`` of each per-field ``mult_`` table, or of each field's ``mult`` rows);
the schema's index bytes including InnoDB's ``FULLTEXT`` auxiliary tablespaces,
which ``information_schema.TABLES`` leaves out; the schema's total beside
``innodb_buffer_pool_size``; the size of ``preview_images``, in ``obs_preview`` or, on a
schema without that table, in ``obs_general``; and the index-usage snapshot.

``--dump-queries`` captures the statements each web scenario's requests issue against
this side's own schema (`benchmarks.query_capture`) into the session's scratch
directory, and replays them at once, planning each one (`plan_metrics`). The capture is
served by one gunicorn worker with one thread, so that the lookups the application
loads into a process or a thread on first use are captured with the same requests every
time. ``--commit-capture`` also
copies the capture to ``scenarios/queries.sql``, the committed copy for a reader.

``--resort-probe``, with ``--dump-queries``, then times the broad search's re-sort in two
shapes on the replay's connection (`benchmarks.resort_probe`): as the application issued
it, and generated from the built search's ``search_results`` rows. Its statements are
written to no capture. A probe whose shapes did not both return the built search's
non-zero result count is recorded, and then the command exits with an error.

``--ascii-columns`` counts, for every column whose form type is ``STRING``, the values
that do not survive conversion to ASCII.

Example::

    python -m benchmarks.bench_db --scale test --side before --pr PR-nn --session a \\
        --python venv-head/bin/python --repo-root . --dump-queries --resort-probe \\
        --ascii-columns
"""

from __future__ import annotations

import argparse
import contextlib
import shutil
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

from benchmarks import query_capture, resort_probe
from benchmarks.app_servers import MemcachedServer
from benchmarks.bench_server import (
    MysqlServer,
    load_server_config,
    query,
    quote_identifier,
    reexec_with_socket,
    server_environment,
    write_opus_config,
)
from benchmarks.bench_web import (
    Client,
    RequestTiming,
    WebBench,
    WebRunError,
    reset_search_tables,
    run_sequence,
    side_schema,
)
from benchmarks.results import (
    REPO_ROOT,
    SCALES,
    SCENARIOS_DIR,
    SIDES,
    Label,
    append_runs,
    host_environment,
    make_label,
    median,
    new_run,
    scenario_hash,
)
from benchmarks.sides import Side, Spelling, require_no_pythonpath
from benchmarks.web_scenarios import Request, Scenario, load_web_config
from import_tests.tools import build_run

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence

#: The committed copy of the newest capture, for a reader; nothing replays it.
COMMITTED_CAPTURE = SCENARIOS_DIR / 'queries.sql'


#: The table holding every mult field's values, and the table naming the fields.
MULT_TABLE = 'mult'
MULT_FIELD_TABLE = 'mult_field'


def _tables_with_column(connection: Any, schema: str, column: str) -> set[str]:
    """Return the tables of a schema that have a column of a given name."""
    return {
        str(row[0])
        for row in query(
            connection,
            'SELECT TABLE_NAME FROM information_schema.COLUMNS '
            'WHERE TABLE_SCHEMA = %s AND COLUMN_NAME = %s',
            [schema, column],
        )
    }


def table_statistics(connection: Any, schema: str) -> dict[str, dict[str, int]]:
    """Return each table's sizes, exact row count and index count.

    Parameters:
        connection: The harness's connection, with fresh statistics.
        schema: The schema.

    Returns:
        Per table: ``data_bytes``, ``index_bytes``, ``rows``, ``index_count``; for a
        ``mult_`` table with an ``id`` column, in a schema that has one table per mult
        field, ``max_id``; and for ``mult``, one ``max_id.<field>`` per mult field, keyed
        by the field's qualified name from ``mult_field``, since ids are numbered per
        field.
    """
    sizes = query(
        connection,
        'SELECT TABLE_NAME, DATA_LENGTH, INDEX_LENGTH FROM information_schema.TABLES '
        "WHERE TABLE_SCHEMA = %s AND TABLE_TYPE = 'BASE TABLE' ORDER BY TABLE_NAME",
        [schema],
    )
    index_counts = dict(
        query(
            connection,
            'SELECT TABLE_NAME, COUNT(DISTINCT INDEX_NAME) FROM information_schema.STATISTICS '
            'WHERE TABLE_SCHEMA = %s GROUP BY TABLE_NAME',
            [schema],
        )
    )
    with_id = _tables_with_column(connection, schema, 'id')
    with_field_id = _tables_with_column(connection, schema, 'field_id')
    tables: dict[str, dict[str, int]] = {}
    for name, data, index in sizes:
        table = f'{quote_identifier(schema)}.{quote_identifier(str(name))}'
        entry = {
            'data_bytes': int(data),
            'index_bytes': int(index),
            'rows': int(query(connection, f'SELECT COUNT(*) FROM {table}')[0][0]),  # nosec B608 - quoted identifiers
            'index_count': int(index_counts.get(name, 0)),
        }
        if str(name) == MULT_TABLE and MULT_FIELD_TABLE in with_field_id:
            fields = f'{quote_identifier(schema)}.{quote_identifier(MULT_FIELD_TABLE)}'
            for field, maximum in query(
                connection,
                f'SELECT `f`.`qualified_name`, MAX(`m`.`id`) FROM {table} AS `m` '  # nosec B608 - quoted identifiers
                f'JOIN {fields} AS `f` ON `f`.`field_id` = `m`.`field_id` '
                'GROUP BY `f`.`qualified_name`',
            ):
                entry[f'max_id.{field}'] = int(maximum)
        elif str(name).startswith('mult_') and str(name) in with_id:
            maximum = query(connection, f'SELECT MAX(id) FROM {table}')[0][0]  # nosec B608 - quoted identifiers
            entry['max_id'] = 0 if maximum is None else int(maximum)
        tables[str(name)] = entry
    return tables


def fulltext_bytes(connection: Any, schema: str) -> int:
    """Return the allocated size of the schema's ``FULLTEXT`` auxiliary tablespaces.

    Parameters:
        connection: The harness's connection.
        schema: The schema.

    Returns:
        The bytes, zero when the schema has no ``FULLTEXT`` index.
    """
    rows = query(
        connection,
        'SELECT COALESCE(SUM(ALLOCATED_SIZE), 0) FROM information_schema.INNODB_TABLESPACES '
        'WHERE NAME LIKE %s',
        [f'{like_literal(schema)}/fts\\_%'],
    )
    return int(rows[0][0])


def like_literal(text: str) -> str:
    """Escape a string so that a ``LIKE`` pattern matches it literally.

    Parameters:
        text: The string, such as a schema name, whose ``_`` would otherwise match any
            character.

    Returns:
        The string with ``\\``, ``%`` and ``_`` escaped by MySQL's default escape
        character.
    """
    return text.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')


#: The tables that may hold ``preview_images``, in the order they are looked for: a schema
#: holds the column in ``obs_preview`` where it has that table, and in ``obs_general``
#: otherwise.
PREVIEW_TABLES = ('obs_preview', 'obs_general')


def preview_images(
    connection: Any, schema: str, statistics: Mapping[str, Mapping[str, int]]
) -> dict[str, Any] | None:
    """Return the size of ``preview_images`` beside ``obs_general``'s data.

    The column is read from the first of `PREVIEW_TABLES` the schema has, so a schema of
    either shape is measured. Both ``DATA_LENGTH`` and ``JSON_STORAGE_SIZE`` count a large
    value's off-page pages, which a scan of ``obs_general``'s other columns never reads,
    so the ratio overstates what holding the column elsewhere saves a scan.

    Parameters:
        connection: The harness's connection.
        schema: The schema.
        statistics: What `table_statistics` returned for the schema.

    Returns:
        The table holding the column, the column's average and total storage size, and
        the total's ratio to ``obs_general``'s data length; None when the schema has
        neither table.
    """
    table = next((name for name in PREVIEW_TABLES if name in statistics), None)
    if table is None:
        return None
    average, total = query(
        connection,
        'SELECT COALESCE(AVG(JSON_STORAGE_SIZE(preview_images)), 0), '
        'COALESCE(SUM(JSON_STORAGE_SIZE(preview_images)), 0) '
        f'FROM {quote_identifier(schema)}.{quote_identifier(table)}',  # nosec B608 - quoted
    )[0]
    obs_general_data_bytes = statistics.get('obs_general', {}).get('data_bytes', 0)
    return {
        'table': table,
        'average_bytes': float(average),
        'total_bytes': float(total),
        'ratio_to_obs_general_data': float(total) / obs_general_data_bytes
        if obs_general_data_bytes > 0
        else 0.0,
    }


def index_usage(connection: Any, schema: str) -> dict[str, Any]:
    """Return the index-usage snapshot for the schema.

    Parameters:
        connection: The harness's connection.
        schema: The schema.

    Returns:
        ``sys.schema_unused_indexes`` and the per-index I/O counters of
        ``performance_schema``, both limited to the schema. They count from the
        server's last start.
    """
    unused = query(
        connection,
        'SELECT object_name, index_name FROM sys.schema_unused_indexes WHERE object_schema = %s',
        [schema],
    )
    usage = query(
        connection,
        'SELECT OBJECT_NAME, INDEX_NAME, COUNT_STAR, COUNT_READ, COUNT_WRITE FROM '
        'performance_schema.table_io_waits_summary_by_index_usage WHERE OBJECT_SCHEMA = %s',
        [schema],
    )
    return {
        'unused_indexes': [[str(table), str(index)] for table, index in unused],
        'index_io': [
            [str(table), None if index is None else str(index), int(star), int(read), int(write)]
            for table, index, star, read, write in usage
        ],
    }


def ascii_columns(connection: Any, schema: str) -> dict[str, int]:
    """Count, per ``STRING`` column, the values that change when converted to ASCII.

    Parameters:
        connection: The harness's connection.
        schema: The schema, whose ``param_info`` names the columns.

    Returns:
        ``<table>.<column>`` to the count, for every column ``param_info`` gives the form
        type ``STRING`` and the schema has.
    """
    columns = query(
        connection,
        f'SELECT DISTINCT p.category_name, p.name FROM {quote_identifier(schema)}.param_info p '  # nosec B608 - quoted identifier
        'JOIN information_schema.COLUMNS c ON c.TABLE_SCHEMA = %s '
        'AND c.TABLE_NAME = p.category_name AND c.COLUMN_NAME = p.name '
        "WHERE p.form_type = 'STRING' ORDER BY p.category_name, p.name",
        [schema],
    )
    counts = {}
    for table, column in columns:
        qualified = f'{quote_identifier(schema)}.{quote_identifier(str(table))}'
        name = quote_identifier(str(column))
        count = query(
            connection,
            # Compared as bytes: under the column's collation a character can equal the
            # '?' or the ASCII letter it converts to (a fullwidth question mark does).
            f'SELECT COUNT(*) FROM {qualified} WHERE CAST({name} AS BINARY) <> '  # nosec B608 - quoted identifiers
            f'CAST(CONVERT({name} USING ascii) AS BINARY)',
        )[0][0]
        counts[f'{table}.{column}'] = int(count)
    return counts


def dump_queries(bench: WebBench, capture: Path) -> list[query_capture.Block]:
    """Run each scenario's requests once with the general log on, and write the capture.

    The search tables are reset once, before the first request; nothing is reset
    between scenarios, so every per-search table a statement names still exists when
    the capture is replayed.

    Parameters:
        bench: A web bench for this side, whose servers are started here.
        capture: The file to write.

    Returns:
        The captured blocks.
    """
    bench.reset('app-cold')
    connection = bench.connection
    blocks: list[query_capture.Block] = []
    query_capture.start_capture(connection)
    try:
        for scenario in bench.config.scenarios:

            def around(
                request: Request,
                url: str,
                issue: Callable[[], RequestTiming],
                scenario: Scenario = scenario,
            ) -> RequestTiming:
                """Capture the statements one request issues, as one block."""
                responses: list[RequestTiming] = []
                tag = f'{scenario.name}/{request.name}'
                blocks.append(
                    query_capture.capture_block(
                        connection, tag, url, lambda: responses.append(issue())
                    )
                )
                if responses[0].failed:
                    # A failed request's statements are not the scenario's.
                    raise WebRunError(f'{tag}: {url} answered {responses[0].status}')
                return responses[0]

            run_sequence(Client(bench.gunicorn.base_url), scenario, around=around)
    finally:
        query_capture.stop_capture(connection)
    query_capture.write_capture(capture, blocks)
    return blocks


def plan_metrics(
    entries: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, float], dict[str, list[float]]]:
    """Turn a replay's planned statements into one time and one row count per block.

    A block is compared with the other side's by its tag, never by statement, since the
    two sides may issue different statements for the same request. Its time in one
    execution is the sum of its planned statements' times in that execution, so the
    block has as many times as each statement was executed, and its metric is their
    median, with every execution's time kept in the run's samples under the metric's
    name (`benchmarks.compare` takes the spread from them). Its rows examined are the
    sum of its statements', which do not change from one execution to the next.

    Parameters:
        entries: What `benchmarks.query_capture.replay` returned.

    Returns:
        The metrics ``db.plan.<tag>.time_s`` and ``db.plan.<tag>.rows_examined``, and
        the samples: each block's time in every execution, under its time metric's name.
    """
    times: dict[str, list[float]] = {}
    rows: dict[str, float] = {}
    for entry in entries:
        plan = entry.get('plan')
        if plan is None:
            continue
        name = f'db.plan.{entry["tag"]}'
        executions = [float(value) for value in plan['times_s']]
        if name in times:
            if len(times[name]) != len(executions):
                raise ValueError(f'{name}: statements were executed different numbers of times')
            times[name] = [
                total + value for total, value in zip(times[name], executions, strict=True)
            ]
        else:
            times[name] = executions
        rows[name] = rows.get(name, 0.0) + float(plan['rows_examined'])
    metrics: dict[str, float] = {}
    samples: dict[str, list[float]] = {}
    for name, values in times.items():
        metrics[f'{name}.time_s'] = median(values)
        samples[f'{name}.time_s'] = values
        metrics[f'{name}.rows_examined'] = rows[name]
    return metrics, samples


def _parse_arguments(argv: Sequence[str] | None) -> argparse.Namespace:
    """Read the command line.

    Parameters:
        argv: The arguments, or None for the command line's.

    Returns:
        The parsed arguments.
    """
    parser = argparse.ArgumentParser(
        prog='python -m benchmarks.bench_db',
        description="Measure the schema one side's import built.",
    )
    parser.add_argument('--scale', choices=SCALES, required=True)
    parser.add_argument('--side', choices=SIDES, required=True)
    parser.add_argument('--pr', required=True)
    parser.add_argument('--session', required=True)
    parser.add_argument('--date', default=None)
    parser.add_argument('--python', type=Path, required=True)
    parser.add_argument('--repo-root', type=Path, required=True)
    parser.add_argument(
        '--schema', default=None, help="measure this schema instead of the import's"
    )
    parser.add_argument(
        '--dump-queries', action='store_true', help="capture and replay the scenarios' SQL"
    )
    parser.add_argument(
        '--commit-capture',
        action='store_true',
        help='also copy the capture to scenarios/queries.sql; only for the side whose '
        "checkout this harness runs from, and as the session's last command, since it "
        'changes that checkout',
    )
    parser.add_argument(
        '--resort-probe',
        action='store_true',
        help="time the broad search's re-sort as captured and from its built rows; "
        'needs --dump-queries',
    )
    parser.add_argument(
        '--ascii-columns', action='store_true', help='count non-ASCII STRING values'
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    """Measure the schema and record one ``db`` run.

    Parameters:
        argv: The arguments, or None for the command line's.
    """
    args = _parse_arguments(argv)
    require_no_pythonpath()
    if args.commit_capture and not args.dump_queries:
        raise SystemExit('--commit-capture copies the capture --dump-queries makes; give both')
    if args.resort_probe and not args.dump_queries:
        raise SystemExit('--resort-probe re-sorts the searches --dump-queries builds; give both')
    if args.commit_capture and args.repo_root.resolve() != REPO_ROOT:
        # The committed capture is this checkout's own SQL; another side's would be
        # committed under this commit's name.
        raise SystemExit(
            f'--commit-capture copies only a capture of this checkout ({REPO_ROOT}), not of '
            f'{args.repo_root.resolve()}'
        )
    server_config, memcached_binary = load_server_config()
    reexec_with_socket(server_config, 'benchmarks.bench_db', sys.argv[1:] if argv is None else argv)
    server = MysqlServer(server_config)
    side = Side(python=args.python.absolute(), repo_root=args.repo_root.resolve())
    label = make_label(
        pr=args.pr, side=args.side, scale=args.scale, session=args.session, date=args.date
    )
    schema, holdings = side_schema(label, args.schema)
    run = new_run('db')
    metrics, details = run['metrics'], run['details']
    environment: dict[str, Any] = {**host_environment(), **side.environment()}
    with server.running():
        environment.update(server_environment(server))
        # The per-search tables an earlier web run left behind are not part of what
        # the import built, so they are emptied before anything is measured.
        reset_config = write_opus_config(
            label.scratch_dir / 'db' / 'opus.toml',
            schema=schema,
            pds3_holdings=holdings[0],
            pds4_holdings=holdings[1],
            run_dir=label.scratch_dir / 'db',
            cache_location=load_web_config().server.memcached_location,
        )
        reset_search_tables(
            side,
            Spelling.from_help(side.import_help()),
            server.client_environment(reset_config),
            label.scratch_dir / 'db' / 'logs' / build_run.ERRORS_LOG,
        )
        with contextlib.closing(server.connect()) as connection:
            tables = [
                str(row[0])
                for row in query(
                    connection,
                    'SELECT TABLE_NAME FROM information_schema.TABLES '
                    "WHERE TABLE_SCHEMA = %s AND TABLE_TYPE = 'BASE TABLE'",
                    [schema],
                )
            ]
            for table in tables:
                query(
                    connection,
                    f'ANALYZE TABLE {quote_identifier(schema)}.{quote_identifier(table)}',
                )
            query(connection, 'SET SESSION information_schema_stats_expiry = 0')
            statistics = table_statistics(connection, schema)
            pool = int(query(connection, 'SELECT @@innodb_buffer_pool_size')[0][0])
            fts = fulltext_bytes(connection, schema)
            data = sum(entry['data_bytes'] for entry in statistics.values())
            index = sum(entry['index_bytes'] for entry in statistics.values()) + fts
            metrics['db.schema.data_bytes'] = data
            metrics['db.schema.index_bytes'] = index
            metrics['db.schema.fulltext_bytes'] = fts
            metrics['db.schema.table_count'] = len(statistics)
            metrics['db.schema.total_to_buffer_pool'] = (data + index) / pool
            for name, entry in statistics.items():
                for key, value in entry.items():
                    metrics[f'db.table.{name}.{key}'] = value
            previews = preview_images(connection, schema, statistics)
            if previews is not None:
                details['preview_images'] = previews
            details['index_usage'] = index_usage(connection, schema)
            if args.ascii_columns:
                details['ascii_columns'] = ascii_columns(connection, schema)
        details['schema'] = schema
        details['buffer_pool_bytes'] = pool
        environment['schema_bytes_beside_buffer_pool'] = {
            'schema_bytes': data + index,
            'innodb_buffer_pool_size': pool,
        }
        if args.dump_queries:
            _dump_and_replay(
                server=server,
                side=side,
                label=label,
                schema=schema,
                holdings=holdings,
                memcached_binary=memcached_binary,
                run=run,
                commit_capture=args.commit_capture,
                probe_resort=args.resort_probe,
            )
    path = append_runs(label, environment, [run])
    sys.stdout.write(f'recorded in {path}\n')
    problems = run['details'].get('resort_probe', {}).get('problems')
    if problems:
        raise SystemExit('the re-sort probe is not a valid measurement: ' + '; '.join(problems))


def _dump_and_replay(
    *,
    server: MysqlServer,
    side: Side,
    label: Label,
    schema: str,
    holdings: tuple[Path, Path],
    memcached_binary: str,
    run: dict[str, Any],
    commit_capture: bool,
    probe_resort: bool,
) -> None:
    """Capture this side's scenario SQL and replay it at once, into the run's details.

    Parameters:
        server: The owned server.
        side: The side.
        label: The result label.
        schema: The side's schema.
        holdings: The holdings roots the application is given.
        memcached_binary: The memcached program.
        run: The run to record the plans in.
        commit_capture: Whether to copy the capture to `COMMITTED_CAPTURE` as well.
        probe_resort: Whether to run `benchmarks.resort_probe.probe` after the replay, on
            its connection, into the run's metrics, samples and details.
    """
    config = load_web_config(scale=label.scale)
    memcached = MemcachedServer(
        memcached_binary, config.server.memcached_port, config.server.memcached_mb
    )
    bench = WebBench(
        server=server,
        memcached=memcached,
        side=side,
        spelling=Spelling.from_help(side.import_help()),
        label=label,
        config=config,
        schema=schema,
        holdings=holdings,
        single_worker=True,
    )
    capture = label.scratch_dir / f'queries_{label.side}.sql'
    bench.stamp_schema_version()
    memcached.start()
    try:
        bench.application_settings()
        blocks = dump_queries(bench, capture)
    finally:
        bench.gunicorn.stop()
        memcached.stop()
    with contextlib.closing(server.connect(schema)) as connection:
        entries = query_capture.replay(connection, blocks)
        if probe_resort:
            probe_metrics, probe_samples, probe_details = resort_probe.probe(connection, blocks)
            run['metrics'].update(probe_metrics)
            run['samples'].update(probe_samples)
            run['details']['resort_probe'] = probe_details
    run['details']['plans'] = entries
    run['details']['capture'] = str(capture)
    run['details']['capture_server_model'] = bench.gunicorn.server_model
    run['details']['web_scenario_hash'] = scenario_hash([config.path])
    block_metrics, block_samples = plan_metrics(entries)
    run['metrics'].update(block_metrics)
    run['samples'].update(block_samples)
    if commit_capture:
        shutil.copyfile(capture, COMMITTED_CAPTURE)


if __name__ == '__main__':
    main()
