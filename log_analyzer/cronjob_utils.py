import datetime
import re
from argparse import Namespace
from pathlib import Path

import pytz


""" Common code used for parsing cronjob args """


DEFAULT_TIMEZONE = pytz.utc
# DEFAULT_TIMEZONE = pytz.timezone('US/Pacific')


def convert_cronjob_to_batchjob(args: Namespace, *, from_first_of_month: bool) -> None:
    if len(args.log_files) == 0:
        raise Exception("Must specify at least one file pattern for cronjob mode")
    log_file_patterns = args.log_files
    if not all('%' in log_file_pattern for log_file_pattern in log_file_patterns):
        raise Exception("Must specify a log file pattern, rather than a log file")

    output_file_pattern = args.output
    if not output_file_pattern:
        raise Exception("Must specify the output file pattern for cronjob mode")
    run_date = __parse_cronjob_date_arg(args)
    if from_first_of_month:
        log_files = [datetime.datetime(year=run_date.year, month=run_date.month, day=day).strftime(log_file_pattern)
                     for log_file_pattern in log_file_patterns
                     for day in range(1, run_date.day + 1)]
    else:
        log_files = [datetime.datetime(
            year=run_date.year, month=run_date.month, day=run_date.day).strftime(log_file_pattern)
                     for log_file_pattern in log_file_patterns]

    log_files = [file for file in log_files if Path(file).exists()]
    output_file = run_date.strftime(output_file_pattern)
    if log_files:
        # Create all necessary intermediate directories
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    args.log_files = log_files
    args.output = output_file
    args.batch = True


def __parse_cronjob_date_arg(args: Namespace) -> datetime.datetime:
    '''Figure out the date to use, based on the --cronjob_date argument.'''
    cronjob_date = args.cronjob_date
    # if the argument isn't present, use today
    if not cronjob_date:
        today = datetime.datetime.now(tz=DEFAULT_TIMEZONE).replace(hour=0, minute=0, second=0, microsecond=0)
        return today
    # if the argument is -<number>, then it means that many days ago
    match = re.match(r'-(\d+)', cronjob_date)
    if match:
        today = datetime.datetime.now(tz=DEFAULT_TIMEZONE).replace(hour=0, minute=0, second=0, microsecond=0)
        return today - datetime.timedelta(days=int(match.group(1)))
    # if the argument is dddd-dd, then it is a year and month, and indicates the last day of that month
    match = re.match(r'(\d\d\d\d)-(\d\d)', cronjob_date)
    if match:
        year_month = datetime.datetime(
            tzinfo=DEFAULT_TIMEZONE, year=int(match.group(1)), month=int(match.group(2)), day=1)
        sometime_following_month = year_month + datetime.timedelta(days=31)
        return sometime_following_month - datetime.timedelta(days=sometime_following_month.day)
    # if the argument is dddd-dd-dd, then treat it as year-month-day
    match = re.match(r'(\d\d\d\d)-(\d\d)-(\d\d)', cronjob_date)
    if match:
        return datetime.datetime(
            tzinfo=DEFAULT_TIMEZONE, year=int(match.group(1)), month=int(match.group(2)), day=int(match.group(3)))
    raise Exception('cronjob_date must be one of -<int>, yyyy-mm, or yyyy-mm-dd')
