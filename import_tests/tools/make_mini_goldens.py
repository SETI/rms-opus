"""Record the expected database contents from one clean run of the fixture.

Run on any machine with a MySQL server; no holdings are needed. It builds the tree, runs
the whole pipeline, and refuses to write anything unless the run was clean -- an empty
``ERRORS.log``, every warning whitelisted with no stale entries, and the expected-products
assertion satisfied. A broken run can never be blessed into the goldens.

    python -m import_tests.tools.make_mini_goldens

Regenerating the fixture with `import_tests.tools.make_mini_holdings` comes first;
regenerating the goldens comes second, and both diffs are reviewed.
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

from import_tests.tools import (
    build_run,
    expected_products,
    fixture_layout,
    golden_io,
    run_logs,
)
from import_tests.tools.golden_io import DatabaseCredentials

if TYPE_CHECKING:
    from collections.abc import Sequence

#: Where the generator reads its database credentials from when the command line does
#: not give them, which is the same place the suite reads them from.
HOST_ENV_VAR = 'OPUS_TEST_DB_HOST'
USER_ENV_VAR = 'OPUS_TEST_DB_USER'
PASSWORD_ENV_VAR = 'OPUS_TEST_DB_PASSWORD'
DEFAULT_HOST = '127.0.0.1'
DEFAULT_USER = 'root'


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    """Parse the generator's command line.

    Parameters:
        argv: The arguments, or None to read ``sys.argv``.

    Returns:
        The parsed arguments.
    """
    parser = argparse.ArgumentParser(
        prog='make_mini_goldens',
        description='Record the expected database contents from a clean fixture run',
    )
    parser.add_argument('--host', default=os.environ.get(HOST_ENV_VAR, DEFAULT_HOST))
    parser.add_argument('--user', default=os.environ.get(USER_ENV_VAR, DEFAULT_USER))
    parser.add_argument('--password', default=os.environ.get(PASSWORD_ENV_VAR, ''))
    parser.add_argument(
        '--seed-whitelist',
        action='store_true',
        help='Write every distinct warning the run logged to standard output instead of '
        'failing on the ones the whitelist does not admit, which is how a whitelist is '
        'first written',
    )
    return parser.parse_args(argv)


def check_run_is_clean(run: build_run.ImportRun, credentials: DatabaseCredentials) -> list[str]:
    """Return the reasons a run must not be blessed into the goldens.

    Everything the suite asks about the *run itself*, checked before anything is written
    rather than after: a broken run must never become the thing later runs are compared
    against. That is `import_tests.test_run_logs`' checks and the products comparison
    `import_tests.test_expected_products` makes. What is deliberately not here is what
    those modules ask about the checked-in files rather than the run -- whether every
    whitelist entry sits under a comment, whether the registry is covered -- which fail
    the suite on their own and would fail it identically before and after a regeneration.
    A step that died before it logged, and a log file that was never written at all, are
    both counted, because either would make the log checks below read an empty file and
    find nothing wrong with it.

    Parameters:
        run: The completed run.
        credentials: How to reach the database server.

    Returns:
        One line per problem, empty when the run is clean.
    """
    problems = []
    for step in run.steps:
        if step.returncode != 0:
            problems.append(
                f'{" ".join(step.arguments)} exited {step.returncode}: '
                f'{step.stderr.strip()[-2000:]}'
            )
    for path in (run.paths.errors_log, run.paths.warnings_log):
        if not path.is_file():
            problems.append(f'{path} was never written, so the run logged nowhere')

    errors = run_logs.read_messages(run.paths.errors_log)
    if len(errors) > 0:
        problems.append(f'{len(errors)} error(s) logged, first: {errors[0]}')

    warnings = run_logs.read_messages(run.paths.warnings_log)
    entries = run_logs.read_whitelist(fixture_layout.WARNING_WHITELIST_FILE)
    unmatched, unused = run_logs.classify(warnings, entries)
    for message in run_logs.distinct(unmatched):
        problems.append(f'warning not admitted by the whitelist: {message}')
    for entry in unused:
        problems.append(
            f'whitelist line {entry.line_number} matched no warning: {entry.pattern.pattern}'
        )

    missing, extra = expected_products.differences(
        expected_products.read_expected_products(),
        expected_products.read_obs_files(credentials, run.schema),
    )
    for bundle, paths in sorted(missing.items()):
        problems.append(f'{bundle} is missing {len(paths)} recorded product(s), e.g. {paths[0]}')
    for bundle, paths in sorted(extra.items()):
        problems.append(f'{bundle} imported {len(paths)} unrecorded product(s), e.g. {paths[0]}')
    return problems


def write_goldens(
    run: build_run.ImportRun, credentials: DatabaseCredentials, directory: Path
) -> list[str]:
    """Serialize every table the run left behind, replacing the goldens directory.

    Which tables are covered is a rule rather than a list: everything the schema holds
    except the tables ``manage.py migrate`` created. A table the import newly writes then
    appears as a new golden rather than escaping comparison, and one it stops writing
    leaves an orphaned file behind for review.

    Parameters:
        run: The completed run.
        credentials: How to reach the database server.
        directory: The goldens directory.

    Returns:
        The tables written, sorted.
    """
    directory.mkdir(parents=True, exist_ok=True)
    for stale in directory.glob(f'*{golden_io.GOLDEN_EXT}'):
        stale.unlink()
    tables = [
        table
        for table in golden_io.list_tables(credentials, run.schema)
        if table not in run.django_tables
    ]
    for table in tables:
        golden_io.write_golden(
            directory, table, golden_io.serialize_table(credentials, run.schema, table)
        )
    return tables


def main(argv: Sequence[str] | None = None) -> int:
    """Run the pipeline once and record its output, unless the run was not clean.

    Parameters:
        argv: The command line, or None to read ``sys.argv``.

    Returns:
        0 when the goldens were written, 1 when the run was not clean enough to bless.
    """
    args = _parse_args(argv)
    credentials = DatabaseCredentials(host=args.host, user=args.user, password=args.password)
    schema = fixture_layout.schema_name(os.getpid())
    with tempfile.TemporaryDirectory(prefix='mini_holdings_goldens_') as temporary:
        try:
            run = build_run.perform_run(Path(temporary), schema, credentials)
            if args.seed_whitelist:
                for message in run_logs.distinct(run_logs.read_messages(run.paths.warnings_log)):
                    print(message)
                return 0
            problems = check_run_is_clean(run, credentials)
            if len(problems) > 0:
                print('Refusing to write goldens; the run was not clean:')
                for problem in problems:
                    print(f'  {problem}')
                return 1
            tables = write_goldens(run, credentials, fixture_layout.GOLDENS_DIR)
            print(f'Wrote {len(tables)} goldens from {len(run.bundles)} bundles')
        finally:
            build_run.drop_schema(credentials, schema)
    return 0


if __name__ == '__main__':
    sys.exit(main())
