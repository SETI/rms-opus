"""Argument expansion shared by the two programs' cronjob modes.

A cron entry names log files by `strftime` pattern rather than by name, so the
patterns have to be resolved against a run date before anything is read. That
date comes from `--date`, which accepts a relative day count, a month, or a
day.
"""

import datetime
import glob
import re
from argparse import Namespace
from collections.abc import Sequence
from pathlib import Path

import pytz

DEFAULT_TIMEZONE = pytz.timezone('US/Pacific')


def expand_globs_and_dates(args: Namespace, *, error_analysis: bool = False) -> None:
    """Resolve the date-patterned file arguments in place, and select batch mode.

    `args.log_files`, `args.manifests`, `args.output` and
    `args.sessions_relative_directory` are read as `strftime` patterns, expanded
    against the run date and (for the first two) glob-expanded. `args.batch` is
    set, because a cronjob run is a batch run.

    Parameters:
        args: The parsed arguments, modified in place.
        error_analysis: Whether this is the error analyzer, which reports on a
            single day rather than from the start of the month to the run date,
            and has no manifests or per-session directory.

    Raises:
        Exception: If no log-file pattern was given, or none of the patterns
            matched a file.
    """
    run_date = __parse_date_argument(args)
    if not error_analysis:
        # From the beginning of the month to the specified date
        dates = [
            datetime.datetime(year=run_date.year, month=run_date.month, day=day)
            for day in range(1, run_date.day + 1)
        ]
    else:
        # Just the date
        dates = [run_date]

    def expand_and_glob_filenames(file_patterns: Sequence[str]) -> Sequence[str]:
        """Expand date patterns, then glob, over the run's dates.

        Parameters:
            file_patterns: `strftime` patterns, which may also contain glob
                metacharacters.

        Returns:
            Every distinct file matched by any pattern on any of the run's
            dates, sorted by name. A pattern matching nothing contributes
            nothing.
        """
        all_patterns = {
            date.strftime(file_pattern) for file_pattern in file_patterns for date in dates
        }
        all_files = sorted(file for pattern in all_patterns for file in glob.glob(pattern))
        return all_files

    if args.log_files:
        args.log_files = expand_and_glob_filenames(args.log_files)
        print(f'Found {len(args.log_files)} log files')
        if len(args.log_files) == 0:
            raise Exception('No log files matching pattern found')
    else:
        raise Exception('Must specify at least one file pattern for cronjob mode')

    if not error_analysis and args.manifests:
        args.manifests = expand_and_glob_filenames(args.manifests)
        print(f'Found {len(args.manifests)} manifests')

    if args.output:
        args.output = run_date.strftime(args.output)
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)

    if not error_analysis and args.sessions_relative_directory:
        args.sessions_relative_directory = run_date.strftime(args.sessions_relative_directory)

    args.batch = True


def __parse_date_argument(args: Namespace) -> datetime.datetime:
    """Figure out the date to use, based on the --date argument."""
    date = args.date
    today = datetime.datetime.now(tz=DEFAULT_TIMEZONE).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    # if the argument isn't present, use today
    if not date:
        return today
    # if the argument is -<number>, then it means that many days ago
    match = re.fullmatch(r'-(\d+)', date)
    if match:
        return today - datetime.timedelta(days=int(match.group(1)))
    # if the argument is dddd-dd, then it is a year and month, and indicates the last day of that month
    match = re.fullmatch(r'(\d\d\d\d)-(\d\d)', date)
    if match:
        year_month = datetime.datetime(
            tzinfo=DEFAULT_TIMEZONE, year=int(match.group(1)), month=int(match.group(2)), day=1
        )
        sometime_following_month = year_month + datetime.timedelta(days=31)
        return sometime_following_month - datetime.timedelta(days=sometime_following_month.day)
    # if the argument is dddd-dd-dd, then treat it as year-month-day
    match = re.fullmatch(r'(\d\d\d\d)-(\d\d)-(\d\d)', date)
    if match:
        return datetime.datetime(
            tzinfo=DEFAULT_TIMEZONE,
            year=int(match.group(1)),
            month=int(match.group(2)),
            day=int(match.group(3)),
        )
    raise Exception('date must be one of -<int>, yyyy-mm, or yyyy-mm-dd')
