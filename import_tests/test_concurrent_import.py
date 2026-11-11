"""Several import processes writing one schema at once, and the registration they share.

The fixture's bundles are registered once, in the main run's order, and three
``opus_import --join`` processes then import them from the bundle registry's queue at the
same time, each with a configuration and a log directory of its own, as importers on
three computers would have. Each holds every bundle it claims for a few seconds first
(``OPUS_IMPORT_FAULT=hold_after_claim:<seconds>``), so the three are certain to hold
bundles at once. The schema is then finished as the main run's is, and compared with the
main run's, which one process imported a bundle at a time.
"""

from __future__ import annotations

import datetime
import difflib
import os
import re
import subprocess  # nosec B404
import sys
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING

import pytest

from import_tests.tools import build_run, fixture_layout, golden_io
from opus_import import import_fault, importdb
from opus_import.steps import do_import, do_import_tables, do_register

if TYPE_CHECKING:
    from pathlib import Path

    from import_tests.tools.golden_io import DatabaseCredentials

#: How many importers run at once.
IMPORTERS = 3

#: How long each importer holds a bundle after claiming it, in seconds.
HOLD_SECONDS = 5

#: Each importer's ``[import]`` keys: loads split across several transactions and
#: observations computed by a small pool, as the main run's are, at a pool size that keeps
#: three importers' workers modest.
_IMPORTER_KEYS = {'transaction_rows': 7, 'workers': 2, 'worker_rows': 5}

#: A pipeline log record's time and message.
_RECORD_RE = re.compile(
    r'^(?P<time>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+) \| [^|]+\|-*\| [A-Z]+ \| (?P<message>.*)$'
)


@dataclass
class JoinRun:
    """The fixture imported by several importers at once, then finished.

    Attributes:
        schema: The schema they imported into.
        registered: What the registration did.
        importers: Each importer's log directory, in start order.
        imported: What each importer did, in the same order.
        closing: What each closing invocation did, in order.
    """

    schema: str
    registered: build_run.StepResult
    importers: list[Path]
    imported: list[build_run.StepResult]
    closing: list[build_run.StepResult]


@pytest.fixture(scope='module')
def join_run(
    main_run: build_run.ImportRun,
    db_credentials: DatabaseCredentials,
    created_schemas: list[str],
) -> JoinRun:
    """Register the fixture's bundles, import them with three importers, and finish.

    Returns:
        The run.
    """
    schema = fixture_layout.schema_name(os.getpid(), 'join')
    created_schemas.append(schema)
    paths = [build_run.sibling_paths(main_run, f'join_{number}') for number in range(IMPORTERS)]
    for importer in paths:
        importer.log_dir.mkdir(parents=True, exist_ok=True)
        build_run.write_opus_config(importer, schema, db_credentials, extra_import=_IMPORTER_KEYS)
    config_file = paths[0].config_file
    registered = build_run.run_pipeline_step(
        config_file, [*build_run.REGISTER_ARGS, ','.join(main_run.bundles)]
    )
    hold = f'{do_import.HOLD_AFTER_CLAIM_FAULT_SITE}:{HOLD_SECONDS}'
    imported = build_run.run_concurrently(
        [importer.config_file for importer in paths],
        build_run.JOIN_ARGS,
        extra_environment={import_fault.IMPORT_FAULT_ENV_VAR: hold},
    )
    closing = [
        build_run.run_pipeline_step(config_file, build_run.AUX_ARGS),
        build_run.run_pipeline_step(config_file, build_run.DICTIONARY_ARGS),
        build_run.run_migrate(config_file),
        build_run.run_pipeline_step(config_file, build_run.VALIDATE_ARGS),
        build_run.run_pipeline_step(config_file, build_run.VERSION_ARGS),
    ]
    return JoinRun(schema, registered, [p.log_dir for p in paths], imported, closing)


def _records(log_dir: Path) -> list[tuple[datetime.datetime, str]]:
    """Return every record of a log directory's information logs, with its time."""
    records = []
    for log in build_run.import_logs(log_dir):
        for line in log.read_text(encoding='utf-8').splitlines():
            match = _RECORD_RE.match(line)
            if match is not None:
                time = datetime.datetime.fromisoformat(match['time'])
                records.append((time, match['message'].strip()))
    return records


def test_every_invocation_succeeds_and_logs_no_error(join_run: JoinRun) -> None:
    """The registration, every importer, and every closing step exit cleanly."""
    for result in [join_run.registered, *join_run.imported, *join_run.closing]:
        assert result.returncode == 0, (result.arguments, result.stderr[-2000:])
    for log_dir in join_run.importers:
        errors = log_dir / build_run.ERRORS_LOG
        assert not errors.exists() or errors.read_text(encoding='utf-8') == ''


def test_every_registered_bundle_is_one_opus_imports(
    join_run: JoinRun, main_run: build_run.ImportRun, db_credentials: DatabaseCredentials
) -> None:
    """The registry holds the fixture's bundles, numbered in the order given, every one done."""
    rows = golden_io.query(
        db_credentials,
        join_run.schema,
        'SELECT bundle_id, state FROM import_bundle ORDER BY bundle_number',
    )
    assert [str(bundle) for bundle, _state in rows] == main_run.bundles
    assert all(do_import_tables.opus_imports_bundle(str(bundle)) for bundle, _state in rows)
    assert {str(state) for _bundle, state in rows} == {'done'}


def test_each_importer_claimed_while_the_others_held_theirs(
    join_run: JoinRun, main_run: build_run.ImportRun
) -> None:
    """The first claims fall within one hold of each other, every bundle is claimed once,
    and no importer exits before the last claim, while a bundle was still pending."""
    claims: list[list[tuple[datetime.datetime, str]]] = []
    exits: list[datetime.datetime] = []
    for log_dir in join_run.importers:
        records = _records(log_dir)
        claims.append(
            [
                (time, message.removeprefix(do_import.CLAIMED_PREFIX))
                for time, message in records
                if message.startswith(do_import.CLAIMED_PREFIX)
            ]
        )
        (exit_time,) = [time for time, message in records if message == do_import.QUEUE_EMPTY_LINE]
        exits.append(exit_time)

    assert all(claimed for claimed in claims)
    firsts = [claimed[0][0] for claimed in claims]
    assert max(firsts) - min(firsts) < datetime.timedelta(seconds=HOLD_SECONDS)
    bundles = [bundle for claimed in claims for _time, bundle in claimed]
    assert sorted(bundles) == sorted(main_run.bundles)
    last_claim = max(time for claimed in claims for time, _bundle in claimed)
    assert all(exit_time >= last_claim for exit_time in exits)


def test_three_importers_import_what_one_does(
    join_run: JoinRun, main_run: build_run.ImportRun, db_credentials: DatabaseCredentials
) -> None:
    """Every goldened table matches the main run's, mult columns compared by their values.

    The observation ids come from the bundles' registered ranges, so they are equal; the
    mult ids of a field's new values follow the order the importers met them, so only the
    values they name are compared.
    """
    differences = {}
    for table in golden_io.goldened_tables(fixture_layout.GOLDENS_DIR):
        one = golden_io.serialize_table(db_credentials, main_run.schema, table, mult_values=True)
        three = golden_io.serialize_table(db_credentials, join_run.schema, table, mult_values=True)
        if one != three:
            lines = difflib.unified_diff(
                one.splitlines(), three.splitlines(), 'one', 'three', lineterm='', n=0
            )
            differences[table] = '\n'.join(list(lines)[:40])
    assert differences == {}, '\n\n'.join(f'{t}:\n{d}' for t, d in differences.items())


def test_a_label_with_no_row_count_refuses_registration(
    tmp_path_factory: pytest.TempPathFactory,
    db_credentials: DatabaseCredentials,
    created_schemas: list[str],
    subprocess_coverage: None,
) -> None:
    """Registration names the bundle and the label, and registers nothing, not even the
    bundle before it."""
    bad = 'COISS_2055'
    label = fixture_layout.PDS3_METADATA / 'COISS_2xxx' / bad / f'{bad}_index.lbl'
    root = tmp_path_factory.mktemp('mini_holdings_no_row_count')
    overlay = root / 'overlay'
    planted = (
        overlay / fixture_layout.PDS3_ROOT_NAME / label.relative_to(fixture_layout.PDS3_FIXTURE)
    )
    planted.parent.mkdir(parents=True)
    lines = label.read_text(encoding='latin-1').splitlines(keepends=True)
    planted.write_text(
        ''.join(line for line in lines if not re.match(r'\s*ROWS\s*=', line)), encoding='latin-1'
    )
    paths = build_run.RunPaths.under(root / 'run')
    build_run.build_holdings_tree(paths, overlay=overlay)
    schema = fixture_layout.schema_name(os.getpid(), 'no_row_count')
    created_schemas.append(schema)
    build_run.write_opus_config(paths, schema, db_credentials)

    refused = build_run.run_pipeline_step(
        paths.config_file, [*build_run.REGISTER_ARGS, f'COCIRS_1101,{bad}']
    )

    assert refused.returncode != 0
    assert f'Bundle {bad} cannot be registered' in refused.stdout
    assert f'{bad}_index.lbl declares no row count' in refused.stdout
    assert golden_io.query(db_credentials, schema, 'SELECT COUNT(*) FROM import_bundle') == [(0,)]


def test_registration_numbers_bundles_in_the_order_given(
    main_run: build_run.ImportRun,
    db_credentials: DatabaseCredentials,
    created_schemas: list[str],
) -> None:
    """The import order, not the bundle ids' order: reversed, the numbers and ranges follow."""
    schema = fixture_layout.schema_name(os.getpid(), 'register_order')
    created_schemas.append(schema)
    paths = build_run.sibling_paths(main_run, 'register_order')
    paths.log_dir.mkdir(parents=True, exist_ok=True)
    build_run.write_opus_config(paths, schema, db_credentials)
    reversed_bundles = list(reversed(main_run.bundles))

    registered = build_run.run_pipeline_step(
        paths.config_file, [*build_run.REGISTER_ARGS, ','.join(reversed_bundles)]
    )

    assert registered.returncode == 0, registered.stderr[-2000:]
    rows = golden_io.query(
        db_credentials,
        schema,
        'SELECT bundle_id, first_id, id_capacity FROM import_bundle ORDER BY bundle_number',
    )
    assert [str(bundle) for bundle, _first, _capacity in rows] == reversed_bundles
    assert [int(first) for _bundle, first, _capacity in rows] == [
        sum(int(capacity) for _b, _f, capacity in rows[:index]) for index in range(len(rows))
    ]


def _waiting_for_a_lock(credentials: DatabaseCredentials, schema: str) -> bool:
    """Return whether another session of the server is waiting in ``GET_LOCK``."""
    rows = golden_io.query(
        credentials,
        schema,
        'SELECT COUNT(*) FROM information_schema.PROCESSLIST '
        "WHERE INFO LIKE 'SELECT GET_LOCK(%%' AND ID <> CONNECTION_ID()",
    )
    return int(rows[0][0]) > 0


def test_an_importer_that_finds_nothing_waits_for_a_registration_in_progress(
    main_run: build_run.ImportRun,
    db_credentials: DatabaseCredentials,
    created_schemas: list[str],
) -> None:
    """An importer started while a registration holds its lock claims what it registers.

    The registration's lock is held from a connection of the test's own; the importer
    finds no pending bundle, waits on the lock, and the test makes one bundle pending
    before it lets go, as a registration's commit would.
    """
    copy = build_run.copy_run_schema(main_run, db_credentials, created_schemas, 'join_waits')
    bundle = main_run.bundles[-1]
    lock = importdb.lock_name(copy.schema, do_register.REGISTRATION_LOCK)
    holder = golden_io.connect(db_credentials, copy.schema)
    importer: subprocess.Popen[str] | None = None
    try:
        cursor = holder.cursor()
        cursor.execute('SELECT GET_LOCK(%s, 0)', [lock])
        assert cursor.fetchall() == ((1,),)
        importer = subprocess.Popen(  # nosec B603 - this interpreter and the pipeline's module
            [sys.executable, '-m', 'opus_import', *build_run.JOIN_ARGS],
            cwd=fixture_layout.REPO_ROOT,
            env=build_run.run_environment(copy.paths.config_file),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        deadline = time.monotonic() + 120
        while not _waiting_for_a_lock(db_credentials, copy.schema):
            assert importer.poll() is None, importer.communicate()
            assert time.monotonic() < deadline
            time.sleep(0.5)
        cursor.execute("UPDATE import_bundle SET state = 'pending' WHERE bundle_id = %s", [bundle])
        holder.commit()
        cursor.execute('SELECT RELEASE_LOCK(%s)', [lock])
        stdout, stderr = importer.communicate(timeout=600)
    finally:
        holder.close()
        if importer is not None and importer.poll() is None:
            # A failed or timed-out wait must not leave an importer writing to a schema
            # the suite's teardown drops.
            importer.kill()
            importer.communicate()

    assert importer.returncode == 0, stderr[-2000:]
    assert f'{do_import.CLAIMED_PREFIX}{bundle}' in stdout
    state = golden_io.query(
        db_credentials,
        copy.schema,
        'SELECT state FROM import_bundle WHERE bundle_id = %s',
        [bundle],
    )
    assert state == [('done',)]
