"""Import every bundle set OPUS holds, dividing the work among several importers.

A full-holdings import is not one command. ``opus_import_all`` runs it from the package,
so that it is available wherever the distribution is installed::

    OPUS_CONFIG=/opt/opus/opus.toml opus_import_all --override-db-schema opus3_new

With no step named it is the **coordinator**:

1. **Prepare.** It registers every bundle the bundle sets expand to (or the ones
   ``--sets`` names), in import order, in the target schema's bundle registry, which
   fixes each bundle's number and the range its observation ids come from. With
   ``--scorched-earth`` it first erases every OPUS table in the schema. Registration
   leaves registered bundles alone, so a rerun after an interruption resumes.
2. **Divide.** ``--workers`` is the total of worker processes on this computer
   (``[import] workers`` when not given), refused above the ceiling every import
   obeys. It starts ``--importers`` importers (``[import] importers`` when not given),
   capped at that total, and divides the total among them as evenly as whole numbers
   allow (`divide`). Each importer is an ``opus_import --join`` process drawing bundles
   from the registry's queue, the largest pending first.
3. **Track.** Every few seconds it reads the registry and the importers' table
   (`opus_import.coordinator`): on a terminal it redraws a table of the running importers under a totals line; otherwise
   it logs a line per finished bundle and the totals every
   ``[import] status_interval_minutes``.
4. **Recover.** An importer whose lock is free while its row says it is running is
   lost; its bundle's rows are deleted and the bundle returns to the queue, or fails at
   its second loss (`opus_import.steps.do_recover`). A lost importer of its own is
   replaced while bundles its importers may claim are pending.
5. **Finish.** When no bundle is pending or importing and no importer anywhere is
   alive, it runs the closing sequence (``--finish``), unless a bundle failed, when it
   names each with its importer's log and leaves the schema unfinalized.

The first interrupt (Ctrl-C) drains: the importers claim nothing new and finish their
bundles, and the coordinator exits without finalizing. A second aborts: each importer
returns its bundle to the queue, and later ones do not interrupt that. Either way a rerun
resumes.

Each step also runs alone when named: ``--prepare``; ``--join``, which starts and tracks
``--importers`` importers on this computer (one by default) and never prepares or
finishes, so another computer naming the same database server, schema and holdings can
join a running import; ``--finish``; ``--requeue``; and ``--status``, which prints the
coordinator's table from any computer.

**Erasing is asked for, never the default.** ``--scorched-earth`` asks for confirmation
first, naming the schema; ``--yes`` answers for a caller that has already asked -- which is
what the Ring-Moon Systems Node's ``scripts/import/import_all.sh`` wrapper does before it
puts the run under ``nohup`` -- and is refused without ``--scorched-earth``.
"""

from __future__ import annotations

import argparse
import subprocess  # nosec B404
import sys
from dataclasses import dataclass
from typing import TYPE_CHECKING

from opus_config import MAX_WORKERS, ConfigError, get_config, resolve_parallelism
from opus_import import bundle_registry, coordinator, importdb

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    import pdslogger

    from opus_config import OpusConfig
    from opus_config.config import ImportConfig
    from opus_import.importdb.super import ImportDBSuper

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

#: The ``--importers`` value that takes the count from ``[import] importers``.
AUTO_IMPORTERS = 'auto'

#: The registry states ``--finish`` refuses to run past, and the ones of those that
#: ``--requeue`` returns to the queue.
_UNFINISHED_STATES = ('pending', 'importing', 'failed')
_REQUEUEABLE_STATES = ('importing', 'failed')


def divide(total: int, importers: int) -> list[int]:
    """Divide a total of workers among importers as evenly as whole numbers allow.

    Parameters:
        total: The workers, at least 1.
        importers: The importers, from 1 to `total`.

    Returns:
        Each importer's workers, in start order. The first ``total mod importers`` take
        one more than the rest, and together they make `total`.
    """
    share, extra = divmod(total, importers)
    return [share + 1 if index < extra else share for index in range(importers)]


@dataclass(frozen=True)
class Division:
    """How this computer's workers are divided among its importers, and why.

    Attributes:
        cores: The cores detected.
        cpu_fraction: The share of them the ceiling allows.
        ceiling: The most workers a request may ask for.
        workers: The total of workers, N.
        importers: The importers, M, at most N.
        per_importer: Each importer's workers, in start order.
    """

    cores: int
    cpu_fraction: float
    ceiling: int
    workers: int
    importers: int
    per_importer: tuple[int, ...]

    def describe(self) -> str:
        """Return the line the coordinator writes first.

        Returns:
            The cores, the fraction, the ceiling, N, M, and each importer's workers.
        """
        return (
            f'Parallelism: {self.cores} cores detected, cpu_fraction {self.cpu_fraction:g}, '
            f'ceiling {self.ceiling}; workers {self.workers} in all, importers '
            f'{self.importers}, workers per importer '
            f'{", ".join(str(count) for count in self.per_importer)}'
        )


def resolve_division(
    config: ImportConfig,
    workers: int | str | None,
    importers: int | str,
    *,
    detected: int | None = None,
) -> Division:
    """Resolve the total of workers against the ceiling, and divide it among importers.

    Parameters:
        config: The ``[import]`` table.
        workers: ``--workers``: a number, `opus_config.MAX_WORKERS` for the ceiling, or
            None for ``[import] workers``.
        importers: ``--importers``: a number, or `AUTO_IMPORTERS` for
            ``[import] importers``.
        detected: The cores to take as detected, or None to count them.

    Returns:
        The division.

    Raises:
        opus_config.config.ConfigError: If the total is above the ceiling, naming it.
    """
    parallelism = resolve_parallelism(config, workers, detected=detected)
    requested = config.importers if importers == AUTO_IMPORTERS else int(importers)
    count = min(requested, parallelism.workers)
    return Division(
        cores=parallelism.cores,
        cpu_fraction=parallelism.cpu_fraction,
        ceiling=parallelism.ceiling,
        workers=parallelism.workers,
        importers=count,
        per_importer=tuple(divide(parallelism.workers, count)),
    )


def _override(schema: str | None) -> list[str]:
    """Return the schema override every invocation carries, or nothing."""
    return ['--override-db-schema', schema] if schema is not None else []


def prepare_steps(
    schema: str | None, erase: bool, extra_options: Sequence[str], sets: str | None = None
) -> list[list[str]]:
    """Return the ``opus_import`` command lines ``--prepare`` runs, in order.

    Parameters:
        schema: The database schema to import into, or None for the one the
            configuration file names. A schema that does not exist is created by the
            first step that writes to it.
        erase: Whether to erase every OPUS table in the schema first.
        extra_options: Options added to every invocation, from this command's own
            command line.
        sets: Comma-separated bundle descriptors to register in place of `BUNDLE_SETS`,
            or None.

    Returns:
        The erase, when asked for, then one registration of every bundle set, in import
        order.
    """
    override = _override(schema)
    steps = [[*DROP_OPTIONS, *override, *extra_options]] if erase else []
    descriptors = list(BUNDLE_SETS) if sets is None else [sets]
    steps.append(['--register-bundles', *override, *extra_options, *descriptors])
    return steps


def importer_step(
    schema: str | None, workers: int, extra_options: Sequence[str], sets: str | None = None
) -> list[str]:
    """Return one importer's ``opus_import`` command line.

    Parameters:
        schema: The database schema, or None for the configuration's.
        workers: The importer's workers.
        extra_options: Options added to the invocation.
        sets: Comma-separated bundle descriptors the importer may claim, or None for any.

    Returns:
        The command line after ``python -m opus_import``.
    """
    step = ['--join', *_override(schema), '--workers', str(workers), *extra_options]
    if sets is not None:
        step.append(sets)
    return step


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


def open_target_db(
    config: OpusConfig,
    schema: str | None,
    *,
    read_only: bool,
    logger: pdslogger.PdsLogger | None = None,
) -> ImportDBSuper:
    """Open the target schema the way the import does, with no bulk load.

    Parameters:
        config: The configuration.
        schema: The schema, or None for the configuration's.
        read_only: Whether to execute no write.
        logger: Where the connection reports, or None.

    Returns:
        The open connection.
    """
    return importdb.get_db(
        config.database.brand,
        config.database.host,
        config.database.database,
        schema if schema is not None else config.database.schema,
        config.database.user,
        config.database.password,
        logger=logger,
        read_only=read_only,
        bulk_load=False,
    )


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
    db = open_target_db(get_config(), schema, read_only=True)
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


################################################################################
# THE COMMAND LINE
################################################################################


def _count_or(word: str) -> Callable[[str], int | str]:
    """Return an argument type: a whole number of at least 1, or `word`.

    Parameters:
        word: The one word accepted beside a number.
    """

    def parse(text: str) -> int | str:
        """Parse one argument."""
        if text == word:
            return text
        try:
            count = int(text)
        except ValueError:
            count = 0
        if count < 1:
            raise argparse.ArgumentTypeError(
                f'must be a whole number of at least 1 or "{word}", not {text!r}'
            )
        return count

    return parse


def _create_argument_parser() -> argparse.ArgumentParser:
    """Build ``opus_import_all``'s argument parser."""
    parser = argparse.ArgumentParser(
        prog='opus_import_all',
        description='Import every bundle set OPUS holds: register the bundles, import them '
        'with several importers drawing from one queue, and finish the database',
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
        help='start --importers importers on this computer (1 by default) and track them; '
        'they draw from the queue a coordinator elsewhere prepared, and nothing is finished',
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
        help='return failed bundles, or importing ones whose importer is gone, to the '
        'queue, after deleting their rows',
    )
    steps.add_argument(
        '--status',
        action='store_true',
        help="print the coordinator's table of the importers and the totals, from any computer",
    )
    parser.add_argument(
        '--sets',
        metavar='DESC,DESC',
        help='with --join, claim only the bundles these comma-separated descriptors name; '
        'with --prepare or no step, register them in place of every bundle set',
    )
    parser.add_argument(
        '--workers',
        metavar='N',
        type=_count_or(MAX_WORKERS),
        help='the total of worker processes on this computer, divided among the importers, '
        f'or "{MAX_WORKERS}" for the ceiling; [import] workers by default',
    )
    parser.add_argument(
        '--importers',
        metavar='M',
        type=_count_or(AUTO_IMPORTERS),
        help='how many importers to start on this computer, capped at --workers: '
        f'"{AUTO_IMPORTERS}" ([import] importers, the default with no step) or a number '
        '(1 is the default with --join)',
    )
    parser.add_argument(
        '--watch',
        action='store_true',
        help='with --status, redraw the table every few seconds until interrupted',
    )
    parser.add_argument(
        '--recover',
        action='store_true',
        help='with --status, first return the bundles of lost importers to the queue',
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


def _division(parser: argparse.ArgumentParser, arguments: argparse.Namespace) -> Division:
    """Resolve the division the arguments ask for, from the configuration.

    Parameters:
        parser: The parser, whose ``error`` reports a refusal.
        arguments: The parsed arguments.

    Returns:
        The division.

    Raises:
        SystemExit: If the total of workers is above the ceiling.
    """
    default = 1 if arguments.join else AUTO_IMPORTERS
    importers = arguments.importers if arguments.importers is not None else default
    try:
        return resolve_division(get_config().import_, arguments.workers, importers)
    except ConfigError as e:
        parser.error(str(e))


def _print_plan(
    arguments: argparse.Namespace, extra_options: Sequence[str], division: Division | None
) -> None:
    """Print, for ``--dry-run``, the steps the arguments would run.

    Parameters:
        arguments: The parsed arguments.
        extra_options: The options passed through.
        division: The importers to start, or None when no importer would start.
    """
    schema = arguments.override_db_schema
    run_all = not (
        arguments.prepare
        or arguments.join
        or arguments.finish
        or arguments.requeue
        or arguments.status
    )
    if division is not None:
        print(division.describe())
    if arguments.prepare or run_all:
        registered = BUNDLE_SETS if arguments.sets is None else (arguments.sets,)
        print(
            f'prepare: {"erases" if arguments.scorched_earth else "erases nothing"}; '
            f'registers, in import order: {" ".join(registered)}'
        )
        for step in prepare_steps(schema, arguments.scorched_earth, extra_options, arguments.sets):
            print(' '.join(['opus_import', *step]))
    if division is not None:
        claimed = arguments.sets if arguments.join else None
        print(
            f'import: {division.importers} importers on this computer, tracked every '
            f'{coordinator.TRACK_SECONDS:g} seconds, a lost one replaced while bundles are pending'
        )
        for workers in division.per_importer:
            print(
                ' '.join(['opus_import', *importer_step(schema, workers, extra_options, claimed)])
            )
    if arguments.finish or run_all:
        print('finish: once every registered bundle is done')
        for step in finish_steps(schema):
            print(' '.join(['opus_import', *step]))
    if arguments.requeue:
        print('requeue:')
        for step in requeue_steps(schema, arguments.requeue):
            print(' '.join(['opus_import', *step]))
    if arguments.status:
        print("status: prints the coordinator's table" + (', watching' if arguments.watch else ''))


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


def _check_arguments(parser: argparse.ArgumentParser, arguments: argparse.Namespace) -> None:
    """Refuse the combinations of arguments that mean nothing.

    Parameters:
        parser: The parser, whose ``error`` reports a refusal.
        arguments: The parsed arguments.

    Raises:
        SystemExit: With status 2 for a refused combination.
    """
    if arguments.yes and not arguments.scorched_earth:
        parser.error(
            '--yes answers the confirmation --scorched-earth asks, and is refused without it'
        )
    step_named = (
        arguments.prepare
        or arguments.join
        or arguments.finish
        or arguments.requeue
        or arguments.status
    )
    if arguments.scorched_earth and step_named and not arguments.prepare:
        parser.error(
            '--scorched-earth erases before registering, so it goes with --prepare or no step'
        )
    if (arguments.workers or arguments.importers) and step_named and not arguments.join:
        parser.error(
            '--workers and --importers divide the importers on this computer, so they go '
            'with --join or no step'
        )
    if arguments.sets and step_named and not (arguments.join or arguments.prepare):
        parser.error(
            '--sets names bundles to register or claim, so it goes with --prepare, '
            '--join or no step'
        )
    if (arguments.watch or arguments.recover) and not arguments.status:
        parser.error('--watch and --recover go with --status')


def main() -> None:
    """Run the full-holdings import, or the one step named.

    Raises:
        SystemExit: With a non-zero status if the arguments are refused, the
            confirmation is refused, an invocation fails, naming it, a bundle failed,
            the run was interrupted, or ``--finish`` refuses. A successful run exits
            zero, which says every step ran -- not that every step was clean. Read
            ``ERRORS.log`` for that.
    """
    parser = _create_argument_parser()
    arguments, extra_options = parser.parse_known_args()
    _check_arguments(parser, arguments)
    step_named = (
        arguments.prepare
        or arguments.join
        or arguments.finish
        or arguments.requeue
        or arguments.status
    )
    starts_importers = arguments.join or not step_named
    # Resolved first, so a total above the ceiling stops the run before anything is erased.
    division = _division(parser, arguments) if starts_importers else None

    if arguments.dry_run:
        _print_plan(arguments, extra_options, division)
        return

    schema = arguments.override_db_schema
    if arguments.status:
        sys.exit(
            coordinator.show_status(
                get_config(), schema, watch=arguments.watch, recover=arguments.recover
            )
        )
    if arguments.scorched_earth and not arguments.yes and not confirm(schema):
        parser.exit(1, 'Aborting: the confirmation was not given.\n')

    if division is not None:
        print(division.describe(), flush=True)
    if arguments.requeue:
        _run(parser, requeue_steps(schema, arguments.requeue))
        return
    if arguments.prepare or not step_named:
        _run(
            parser,
            prepare_steps(schema, arguments.scorched_earth, extra_options, arguments.sets),
        )
    if division is not None:
        status = coordinate(
            schema,
            division,
            extra_options,
            finishing=not step_named,
            sets=arguments.sets if arguments.join else None,
        )
        if status != 0:
            parser.exit(status, f'{parser.prog}: stopped -- the importers did not finish\n')
    if arguments.finish or not step_named:
        _finish(parser, schema)
    if not step_named:
        print('Import is complete. Read ERRORS.log before trusting it.')


def coordinate(
    schema: str | None,
    division: Division,
    extra_options: Sequence[str],
    *,
    finishing: bool,
    sets: str | None,
) -> int:
    """Start, track and recover importers until the run is over
    (`opus_import.coordinator.Coordinator.run`).

    Parameters:
        schema: The database schema, or None for the configuration's.
        division: The importers to start.
        extra_options: Options added to every importer's invocation.
        finishing: Whether to wait for every importer anywhere, as the coordinator does.
        sets: Comma-separated bundle descriptors the importers may claim, or None.

    Returns:
        The run's exit status.
    """
    run = coordinator.Coordinator(
        get_config(), schema, division, extra_options, finishing=finishing, sets=sets
    )
    return run.run()


if __name__ == '__main__':  # pragma: no cover
    main()
