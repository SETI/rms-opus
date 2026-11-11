"""Import every bundle set OPUS holds, in the order a full import runs them.

A full-holdings import is not one command. It is three steps, each one or more
``opus_import`` processes, and the sequence lives in the package, so that
``opus_import_all`` is available wherever the distribution is installed::

    OPUS_CONFIG=/opt/opus/opus.toml opus_import_all --override-db-schema opus3_new

1. ``--prepare`` registers every bundle the bundle sets expand to, in import order, in
   the target schema's bundle registry, which fixes each bundle's number and the range
   its observation ids come from. With ``--scorched-earth`` it first erases every OPUS
   table in the schema.
2. ``--join`` runs one importer, which imports bundles from the registry's queue, the
   largest pending first, until none is pending. Several, on one computer or several,
   each with a configuration naming the same database server and schema and the same
   holdings, draw from one queue; ``--sets`` limits which bundles one claims.
3. ``--finish`` runs the closing sequence once every importer has exited: the
   finalization group, the dictionary, validation, and the schema version row, which
   lets the web application serve the result. It refuses while any registered bundle is
   not done.

Each step runs alone when named. With none named, ``opus_import_all`` runs all three on
one computer, with one importer. **Every invocation is a separate** ``opus_import``
**process**, and the run stops at the first one that fails.

**Erasing is asked for, never the default.** Without ``--scorched-earth`` nothing is
erased, so running ``opus_import_all`` again after an interruption registers nothing new
and imports only what is not done. ``--scorched-earth`` asks for confirmation first,
naming the schema; ``--yes`` answers for a caller that has already asked -- which is what
the Ring-Moon Systems Node's ``scripts/import/import_all.sh`` wrapper does before it puts
the run under ``nohup`` -- and is refused without ``--scorched-earth``.
"""

from __future__ import annotations

import argparse
import subprocess  # nosec B404
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

#: The bundle sets, in the order they are imported -- GALILEO and NEWHORIZONS, then the rest
#: roughly in the reverse of how long each takes. Registration numbers the bundles in this
#: order, and a bundle registered later keeps its copy of an OPUS id two bundles share.
BUNDLE_SETS = (
    'GALILEO',
    'NEWHORIZONS',
    'EBROCC',
    'uranus_occs_earthbased',
    'cassini_uvis_solarocc_beckerjarmak2023',
    'COUVIS_8xxx',
    'COVIMS_8xxx',
    'CORSS_8xxx',
    'VOYAGER',
    'HST',
    'COCIRS',
    'COISS',
    'COUVIS_0xxx',
    'COVIMS_0xxx',
)

#: What finishes the database once every bundle is in it. They are the finalization
#: group -- the secondary keys, one copy of each OPUS id, and the auxiliary tables that
#: describe the search form -- the dictionary the tooltips come from, the validation that
#: reads the result back, and the schema version row that lets the web application serve
#: the result, which comes last. None of them names a bundle.
FINALIZATION_OPTIONS = (
    '--finalize',
    '--import-dictionary',
    '--validate',
    '--write-schema-version',
)

#: The erase `--scorched-earth` asks for, run as its own invocation before registration.
#: The run has asked its own confirmation by then.
DROP_OPTIONS = ('--scorched-earth', '--yes')

#: What has to be typed to let the erase proceed. Nothing else is accepted, including
#: ``yes``: the tables it is about to drop are not recoverable.
CONFIRMATION = 'YES'

#: The registry states ``--finish`` refuses to run past, and the ones of those that
#: ``--requeue`` returns to the queue.
_UNFINISHED_STATES = ('pending', 'importing', 'failed')
_REQUEUEABLE_STATES = ('importing', 'failed')


def _override(schema: str | None) -> list[str]:
    """Return the schema override every invocation carries, or nothing."""
    return ['--override-db-schema', schema] if schema is not None else []


def prepare_steps(schema: str | None, erase: bool, extra_options: Sequence[str]) -> list[list[str]]:
    """Return the ``opus_import`` command lines ``--prepare`` runs, in order.

    Parameters:
        schema: The database schema to import into, or None for the one the
            configuration file names. A schema that does not exist is created by the
            first step that writes to it.
        erase: Whether to erase every OPUS table in the schema first.
        extra_options: Options added to every invocation, from this command's own
            command line.

    Returns:
        The erase, when asked for, then one registration of every bundle set, in import
        order.
    """
    override = _override(schema)
    steps = [[*DROP_OPTIONS, *override, *extra_options]] if erase else []
    steps.append(['--register-bundles', *override, *extra_options, *BUNDLE_SETS])
    return steps


def join_steps(
    schema: str | None, sets: str | None, workers: str | None, extra_options: Sequence[str]
) -> list[list[str]]:
    """Return the ``opus_import`` command line ``--join`` runs: one importer.

    Parameters:
        schema: The database schema, or None for the configuration's.
        sets: Comma-separated bundle descriptors the importer may claim, or None for any.
        workers: The importer's ``--workers``, or None for ``[import] workers``.
        extra_options: Options added to the invocation.

    Returns:
        One command line.
    """
    step = ['--join', *_override(schema)]
    if workers is not None:
        step += ['--workers', workers]
    step += [*extra_options]
    if sets is not None:
        step.append(sets)
    return [step]


def finish_steps(schema: str | None) -> list[list[str]]:
    """Return the ``opus_import`` command lines ``--finish`` runs, in order.

    Parameters:
        schema: The database schema, or None for the configuration's.

    Returns:
        One invocation per `FINALIZATION_OPTIONS` entry. They take neither a bundle nor
        the extra options, because they import nothing.
    """
    return [[option, *_override(schema)] for option in FINALIZATION_OPTIONS]


def requeue_steps(schema: str | None, bundles: Sequence[str]) -> list[list[str]]:
    """Return the ``opus_import`` command line ``--requeue`` runs.

    Parameters:
        schema: The database schema, or None for the configuration's.
        bundles: The bundle ids to return to the queue.

    Returns:
        One command line.
    """
    return [['--requeue', *_override(schema), *bundles]]


def import_steps(
    schema: str | None,
    extra_options: Sequence[str],
    *,
    erase: bool = False,
    workers: str | None = None,
) -> list[list[str]]:
    """Return every ``opus_import`` command line the default sequence runs, in order.

    Parameters:
        schema: The database schema, or None for the configuration's.
        extra_options: Options added to every invocation that reads the holdings.
        erase: Whether ``--scorched-earth`` was given.
        workers: The importer's ``--workers``, or None.

    Returns:
        ``--prepare``'s, one importer's, and ``--finish``'s command lines.
    """
    return [
        *prepare_steps(schema, erase, extra_options),
        *join_steps(schema, None, workers, extra_options),
        *finish_steps(schema),
    ]


def run_step(arguments: list[str]) -> int:
    """Run one ``opus_import`` invocation, in a process of its own.

    Parameters:
        arguments: The command line after ``python -m opus_import``.

    Returns:
        The invocation's exit status. A non-zero status stops the run; a zero one does
        not mean the step was clean, because several steps report failure through
        ``ERRORS.log`` and still exit zero.
    """
    command = [sys.executable, '-m', 'opus_import', *arguments]
    print(f'>>> {" ".join(command)}', flush=True)
    # The command is this module's own constants and the options the caller typed,
    # run without a shell, so there is nothing here for a shell to interpret.
    return subprocess.run(command, check=False).returncode  # nosec B603


def confirm(schema: str | None) -> bool:
    """Ask whether to erase the database, and read the answer.

    Parameters:
        schema: The schema the run was pointed at, or None when the configuration file's
            own schema is the one being erased.

    Returns:
        Whether `CONFIRMATION` was typed exactly.
    """
    target = schema if schema is not None else 'the schema named in $OPUS_CONFIG'
    print('*** A full import ERASES every OPUS table in the schema before it starts. ***')
    print(f'*** About to erase and re-import: {target}')
    return input(f'>>> Type {CONFIRMATION} to continue: ') == CONFIRMATION


def registry_states(schema: str | None) -> list[tuple[str, str]]:
    """Read every registered bundle's state from the target schema.

    Parameters:
        schema: The database schema, or None for the configuration's.

    Returns:
        ``(bundle, state)`` pairs in registration order; none when the schema has no
        registry.

    Raises:
        opus_import.importdb.super.ImportDBError: If the schema cannot be read, which includes
            a schema that does not exist.
    """
    # Imported here, so that --help and --dry-run need neither a configuration nor the
    # database driver.
    from opus_config import get_config
    from opus_import import bundle_registry, importdb

    config = get_config()
    db = importdb.get_db(
        config.database.brand,
        config.database.host,
        config.database.database,
        schema if schema is not None else config.database.schema,
        config.database.user,
        config.database.password,
        read_only=True,
    )
    try:
        return [(row.bundle_id, row.state) for row in bundle_registry.registered_ranges(db)]
    finally:
        db.close()


def unfinished_refusal(states: Sequence[tuple[str, str]]) -> str | None:
    """Return ``--finish``'s refusal for a registry with unfinished bundles, or None.

    Parameters:
        states: What `registry_states` returned.

    Returns:
        The message, naming each bundle that is pending, importing or failed with its
        state, and, for a failed or importing one, the command that returns it to the
        queue; None when every registered bundle is done.
    """
    lines = []
    for bundle, state in states:
        if state not in _UNFINISHED_STATES:
            continue
        line = f'  {bundle} ({state})'
        if state in _REQUEUEABLE_STATES:
            line += f': "opus_import_all --requeue {bundle}" returns it to the queue'
        lines.append(line)
    if not lines:
        return None
    return '--finish refuses to run while registered bundles are not done:\n' + '\n'.join(lines)


def _create_argument_parser() -> argparse.ArgumentParser:
    """Build ``opus_import_all``'s argument parser."""
    parser = argparse.ArgumentParser(
        prog='opus_import_all',
        description='Import every bundle set OPUS holds: register the bundles, import them '
        'from the queue, and finish the database',
        epilog='Any other option is passed to every opus_import invocation that reads the '
        'holdings.',
    )
    steps = parser.add_mutually_exclusive_group()
    steps.add_argument(
        '--prepare',
        action='store_true',
        help='register every bundle in import order (after the erase, with --scorched-earth)',
    )
    steps.add_argument(
        '--join',
        action='store_true',
        help='run one importer, which imports bundles from the queue until none is pending',
    )
    steps.add_argument(
        '--finish',
        action='store_true',
        help='finalize, import the dictionary, validate and mark the schema ready, once '
        'every registered bundle is done',
    )
    steps.add_argument(
        '--requeue',
        nargs='+',
        metavar='BUNDLE',
        help='return failed or importing bundles to the queue, after deleting their rows',
    )
    parser.add_argument(
        '--sets',
        metavar='DESC,DESC',
        help='with --join, claim only the bundles these comma-separated descriptors name',
    )
    parser.add_argument(
        '--workers',
        metavar='N',
        help="with --join, or the default sequence, the importer's opus_import --workers",
    )
    # Named exactly as the pipeline names it, and not passed through: an option this
    # parser did not recognize would reach only the steps that read the holdings and not
    # the ones that finish the database, which would finish a different database from
    # the one just imported.
    parser.add_argument(
        '--override-db-schema',
        metavar='SCHEMA',
        help='the database schema to import into, instead of the one the configuration '
        'file names; it is created if it does not exist',
    )
    parser.add_argument(
        '--scorched-earth',
        action='store_true',
        help='erase every OPUS table in the schema before registering, after asking for '
        'confirmation',
    )
    parser.add_argument(
        '--yes',
        action='store_true',
        help="answer --scorched-earth's confirmation, which running under nohup needs; "
        'refused without --scorched-earth',
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='print the steps these arguments would run, and run none of them',
    )
    return parser


def _print_plan(arguments: argparse.Namespace, extra_options: Sequence[str]) -> None:
    """Print, for ``--dry-run``, the steps the arguments would run.

    Parameters:
        arguments: The parsed arguments.
        extra_options: The options passed through.
    """
    schema = arguments.override_db_schema
    run_all = not (arguments.prepare or arguments.join or arguments.finish or arguments.requeue)
    if arguments.prepare or run_all:
        print(
            f'prepare: {"erases" if arguments.scorched_earth else "erases nothing"}; '
            f'registers, in import order: {" ".join(BUNDLE_SETS)}'
        )
        for step in prepare_steps(schema, arguments.scorched_earth, extra_options):
            print(' '.join(['opus_import', *step]))
    if arguments.join or run_all:
        workers = arguments.workers or '[import] workers'
        print(f'join: 1 importer, workers {workers}')
        for step in join_steps(schema, arguments.sets, arguments.workers, extra_options):
            print(' '.join(['opus_import', *step]))
    if arguments.finish or run_all:
        print('finish: once every registered bundle is done')
        for step in finish_steps(schema):
            print(' '.join(['opus_import', *step]))
    if arguments.requeue:
        print('requeue:')
        for step in requeue_steps(schema, arguments.requeue):
            print(' '.join(['opus_import', *step]))


def _run(parser: argparse.ArgumentParser, steps: list[list[str]]) -> None:
    """Run invocations in order, stopping at the first that fails.

    Parameters:
        parser: The parser, whose ``exit`` reports a failure.
        steps: The command lines.

    Raises:
        SystemExit: With the failed invocation's status, naming it.
    """
    for step in steps:
        status = run_step(step)
        if status != 0:
            parser.exit(
                status if 0 < status < 256 else 1,
                f'{parser.prog}: stopped -- `opus_import {" ".join(step)}` exited {status}\n',
            )


def _finish(parser: argparse.ArgumentParser, schema: str | None) -> None:
    """Run ``--finish``: refuse while a registered bundle is not done, else finish.

    Parameters:
        parser: The parser, whose ``exit`` reports a refusal or a failure.
        schema: The database schema, or None for the configuration's.

    Raises:
        SystemExit: With status 1 when the registry refuses, or the failed invocation's
            status.
    """
    refusal = unfinished_refusal(registry_states(schema))
    if refusal is not None:
        parser.exit(1, f'{parser.prog}: {refusal}\n')
    _run(parser, finish_steps(schema))


def main() -> None:
    """Run the full-holdings import, or the one step named.

    Raises:
        SystemExit: With a non-zero status if the arguments are refused, the
            confirmation is refused, ``--finish`` refuses, or an invocation fails, naming
            it. A successful run exits zero, which says every step ran -- not that every
            step was clean. Read ``ERRORS.log`` for that.
    """
    parser = _create_argument_parser()
    arguments, extra_options = parser.parse_known_args()
    if arguments.yes and not arguments.scorched_earth:
        parser.error(
            '--yes answers the confirmation --scorched-earth asks, and is refused without it'
        )
    step_named = arguments.prepare or arguments.join or arguments.finish or arguments.requeue
    if arguments.scorched_earth and step_named and not arguments.prepare:
        parser.error(
            '--scorched-earth erases before registering, so it goes with --prepare or no step'
        )
    if (arguments.sets or arguments.workers) and step_named and not arguments.join:
        parser.error("--sets and --workers are an importer's, so they go with --join or no step")
    if arguments.sets and not step_named:
        parser.error('--sets limits one importer of several, so it goes with --join')

    if arguments.dry_run:
        _print_plan(arguments, extra_options)
        return

    schema = arguments.override_db_schema
    if arguments.scorched_earth and not arguments.yes and not confirm(schema):
        parser.exit(1, 'Aborting: the confirmation was not given.\n')

    if arguments.requeue:
        _run(parser, requeue_steps(schema, arguments.requeue))
        return
    if arguments.prepare or not step_named:
        _run(parser, prepare_steps(schema, arguments.scorched_earth, extra_options))
    if arguments.join or not step_named:
        _run(parser, join_steps(schema, arguments.sets, arguments.workers, extra_options))
    if arguments.finish or not step_named:
        _finish(parser, schema)
    if not step_named:
        print('Import is complete. Read ERRORS.log before trusting it.')


if __name__ == '__main__':  # pragma: no cover
    main()
