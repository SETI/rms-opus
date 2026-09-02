"""Import every bundle set OPUS holds, in the order a full import runs them.

A full-holdings import is not one command. The bundle sets are imported one group at a
time, in a deliberate order; two of them need an extra option; and the database is
finished afterwards by three more steps. That sequence used to live in a shell script in
the repository, which meant an installed OPUS could not run it. It lives here instead, so
that ``opus_import_all`` is available wherever the distribution is installed::

    OPUS_CONFIG=/opt/opus/opus.toml opus_import_all --override-db-schema opus3_new

**Every group is a separate** ``opus_import`` **process**, as it was when this was a shell
script, and the run stops at the first one that fails. One process per group is what keeps
each group's import tables separate from the next group's, and it is what lets a failed
run be continued by hand from the group that failed.

**The run erases the permanent tables it is pointed at before it begins**, so it asks for
confirmation first, naming the schema. ``--yes`` answers for a caller that has already
asked -- which is what the Node's ``scripts/import/import_all.sh`` wrapper does before it
puts the run under ``nohup``.
"""

from __future__ import annotations

import argparse
import subprocess  # nosec B404
import sys

#: The bundle sets imported before any other, each in its own run, with
#: ``--import-check-duplicate-id``. Their bundles carry observations that appear in more
#: than one bundle, and the check is cheapest while the tables are still small.
DUPLICATE_ID_BUNDLE_SETS = ('GALILEO', 'NEWHORIZONS')

#: The rest of the bundle sets, in the order they are imported. That order is roughly the
#: reverse of how long each takes, so that a run which is going to fail on a small set
#: fails early rather than after the largest one.
BUNDLE_SETS = (
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

#: What finishes the database once every bundle set is in it. They are the auxiliary
#: tables that describe the search form, the dictionary the tooltips come from, and the
#: validation that reads the result back. None of them names a bundle.
FINALIZATION_OPTIONS = ('--cleanup-aux-tables', '--import-dictionary', '--validate-perm')

#: What the run does before it imports anything, which is to drop the permanent tables,
#: including the ones no bundle set being imported would otherwise replace.
DROP_OPTIONS = ('--drop-permanent-tables', '--scorched-earth')

#: What has to be typed to let the run proceed. Nothing else is accepted, including
#: ``yes``: the tables it is about to drop are not recoverable.
CONFIRMATION = 'YES'


def import_steps(schema: str | None, extra_options: list[str]) -> list[list[str]]:
    """Return every ``opus_import`` command line a full import runs, in order.

    Parameters:
        schema: The database schema to import into, or None to use the one the
            configuration file names. A schema that does not exist is created by the
            first step that writes to it.
        extra_options: Options added to every invocation, from this command's own
            command line.

    Returns:
        One argument list per invocation, each without the interpreter and the module
        name. The drop comes first, then the duplicate-id bundle sets, then the rest,
        then the finalization steps -- which take neither a bundle nor the extra options,
        because they import nothing.
    """
    override = ['--override-db-schema', schema] if schema is not None else []
    steps = [[*DROP_OPTIONS, *override, *extra_options]]
    steps += [
        ['--import-check-duplicate-id', '--do-all-import', *override, *extra_options, name]
        for name in DUPLICATE_ID_BUNDLE_SETS
    ]
    steps += [['--do-all-import', *override, *extra_options, name] for name in BUNDLE_SETS]
    steps += [[option, *override] for option in FINALIZATION_OPTIONS]
    return steps


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
    print('*** A full import ERASES the permanent tables before it starts. ***')
    print(f'*** About to erase and re-import: {target}')
    return input(f'>>> Type {CONFIRMATION} to continue: ') == CONFIRMATION


def main() -> None:
    """Run a full-holdings import.

    Raises:
        SystemExit: With a non-zero status if the confirmation is refused or a step
            fails, naming the step. A successful run exits zero, which says every step
            ran -- not that every step was clean. Read ``ERRORS.log`` for that.
    """
    parser = argparse.ArgumentParser(
        prog='opus_import_all',
        description='Import every bundle set OPUS holds, in the order a full import runs them',
        epilog='Any other option is passed to every opus_import invocation this runs.',
    )
    # Named exactly as the pipeline names it, and not passed through: an option this
    # parser did not recognize would reach the import steps and not the three that
    # finish the database, which would finish a different database from the one just
    # imported.
    parser.add_argument(
        '--override-db-schema',
        metavar='SCHEMA',
        help='the database schema to import into, instead of the one the configuration '
        'file names; it is created if it does not exist',
    )
    parser.add_argument(
        '--yes',
        action='store_true',
        help='do not ask for confirmation before erasing, which is what running under nohup needs',
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='print the invocations this would run, and run none of them',
    )
    arguments, extra_options = parser.parse_known_args()

    steps = import_steps(arguments.override_db_schema, extra_options)
    if arguments.dry_run:
        for step in steps:
            print(' '.join(['opus_import', *step]))
        return

    if not arguments.yes and not confirm(arguments.override_db_schema):
        parser.exit(1, 'Aborting: the confirmation was not given.\n')

    for step in steps:
        status = run_step(step)
        if status != 0:
            parser.exit(
                status if 0 < status < 256 else 1,
                f'{parser.prog}: stopped -- `opus_import {" ".join(step)}` exited {status}\n',
            )
    print('Import is complete. Read ERRORS.log before trusting it.')


if __name__ == '__main__':  # pragma: no cover
    main()
