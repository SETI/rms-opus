import argparse
import datetime
import importlib
import ipaddress
import operator
import re
from argparse import Namespace
from pathlib import Path

import pytz
from typing import List, Optional, cast

from abstract_session_info import AbstractConfiguration
from log_entry import LogReader
from log_parser import LogParser
from ip_to_host_converter import IpToHostConverter

DEFAULT_FIELDS_PREFIX = 'https://tools.pds-rings.seti.org'

def main(arguments: Optional[List[str]] = None) -> None:
    def parse_ignored_ips(x: str) -> List[ipaddress.IPv4Network]:
        return [ipaddress.ip_network(address, strict=False) for address in x.split(',')]

    parser = argparse.ArgumentParser(description='Process log files.')

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--realtime', '--interactive', '-i', '-r', action='store_true',
                       help='Watch a single log file in realtime')
    group.add_argument('--batch', '-b', action='store_true',
                       help='Print a report on one or more completed log files')
    group.add_argument('--summary', action='store_true', dest='summary',
                       help="Show the slugs that have been used in a log file")
    group.add_argument('--cronjob', action='store_true', dest='cronjob',
                       help="Used by the chron job to generate a daily summary")
    group.add_argument('--xxfake-realtime', action='store_true', help=argparse.SUPPRESS, dest='fake_realtime')

    group2 = parser.add_mutually_exclusive_group()
    group2.add_argument('--by-ip', action='store_true', dest='by_ip',
                        help='Sorts batched logs by host ip')
    group2.add_argument('--by-time', action='store_false', dest='by_ip',
                        help='Sorts batched logs by session start time')

    parser.add_argument('--html', action='store_true', dest='uses_html',
                        help='Generate html output rather than text output')

    parser.add_argument('--cronjob-date', action='store', dest='cronjob_date',
                        help='Date for --cronjob.  One of -<number>, yyyy-mm, or yyyy-mm-dd.  default is today.')

    parser.add_argument('--api-host-url', default=DEFAULT_FIELDS_PREFIX, metavar='URL', dest='api_host_url',
                        help='base url to access the information')
    parser.add_argument('--reverse-dns', '--dns', action='store_true', dest='uses_reverse_dns',
                        help='Attempt to resolve the real host name')
    parser.add_argument('--ignore-ip', '-x', default=[], action="append", metavar='cidrlist', dest='ignore_ip',
                        type=parse_ignored_ips,
                        help='list of ips to ignore.  May be specified multiple times')
    parser.add_argument('--session-timeout', default=60, type=int, metavar="minutes", dest='session_timeout_minutes',
                        help='a session ends after this period (minutes) of inactivity')

    parser.add_argument('--output', '-o', dest='output',
                        help="output file.  default is stdout.  For --cronjob, specifies the output pattern")

    # TODO(fy): Temporary hack for when I don't have internet access
    parser.add_argument('--xxlocal', action="store_true", dest="uses_local", help=argparse.SUPPRESS)
    # TODO(fy): Debugging hack that shows all URLs.
    parser.add_argument('--xxshowall', action='store_true', dest='debug_show_all', help=argparse.SUPPRESS)

    parser.add_argument('log_files', nargs=argparse.REMAINDER, help='log files')
    args = parser.parse_args(arguments)

    if args.cronjob:
        # Fix up the arguments to match what everyone else wants
        convert_cronjob_to_batchjob(args)
        if not args.log_files:
            print("No log files found.")
            return

    # args.ignored_ip comes out as a list of lists, and it needs to be flattened.
    args.ignored_ips = [ip for arg_list in args.ignore_ip for ip in arg_list]
    # Another fake argument we need
    args.ip_to_host_converter = IpToHostConverter.get_ip_to_host_converter(args.uses_reverse_dns, args.uses_local)

    module = importlib.import_module("opus.session_info")
    configuration = cast(AbstractConfiguration, module.Configuration(**vars(args)))  # type: ignore
    log_parser = LogParser(configuration, **vars(args))

    if args.realtime:
        if len(args.log_files) != 1:
            raise Exception("Must specify exactly one file for real-time mode.")
        log_entries_realtime = LogReader.read_logs_from_tailed_file(args.log_files[0])
        log_parser.run_realtime(log_entries_realtime)
    else:
        if len(args.log_files) < 1:
            raise Exception("Must specify at least one log file.")
        log_entries_list = LogReader.read_logs(args.log_files)
        if args.batch:
            log_parser.run_batch(log_entries_list)
        elif args.summary:
            log_parser.run_summary(log_entries_list)
        elif args.fake_realtime:
            log_entries_list.sort(key=operator.attrgetter('time'))
            log_parser.run_realtime(iter(log_entries_list))


def convert_cronjob_to_batchjob(args: Namespace) -> None:
    if len(args.log_files) != 1:
        raise Exception("Must specify exactly one log file pattern for cronjob mode")
    log_file_pattern = args.log_files[0]
    if '%' not in log_file_pattern:
        raise Exception("Must specify a log file pattern, rather than a log file")

    output_file_pattern = args.output
    if not output_file_pattern:
        raise Exception("Must specify the output file pattern for cronjob mode")
    run_date = parse_cronjob_date_arg(args)
    log_files = [datetime.datetime(year=run_date.year, month=run_date.month, day=day).strftime(log_file_pattern)
                for day in range(1, run_date.day + 1)]
    # Rob wants me to silently ignore non-existent files.
    log_files = [file for file in log_files if Path(file).exists()]
    output_file = run_date.strftime(output_file_pattern)
    if log_files:
        # Create all necessary intermediate directories
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    args.log_files = log_files
    args.output = output_file
    args.batch = True


def parse_cronjob_date_arg(args: Namespace) -> datetime.datetime:
    '''Figure out the date to use, based on the --cronjob_date argument.'''
    cronjob_date = args.cronjob_date
    # if the argument isn't present, use today
    if not cronjob_date:
        today = datetime.datetime.now(tz=pytz.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        return today
    # if the argument is -<number>, then it means that many days ago
    match = re.match(r'-(\d+)', cronjob_date)
    if match:
        today = datetime.datetime.now(tz=pytz.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        return today - datetime.timedelta(days=int(match.group(1)))
    # if the argument is dddd-dd, then it is a year and month, and indicates the last day of that month
    match = re.match(r'(\d\d\d\d)-(\d\d)', cronjob_date)
    if match:
        year_month = datetime.datetime(tzinfo=pytz.utc, year=int(match.group(1)), month=int(match.group(2)), day=1)
        sometime_following_month = year_month + datetime.timedelta(days=31)
        return sometime_following_month - datetime.timedelta(days=sometime_following_month.day)
    # if the argument is dddd-dd-dd, then treat it as year-month-day
    match = re.match(r'(\d\d\d\d)-(\d\d)-(\d\d)', cronjob_date)
    if match:
        return datetime.datetime(
            tzinfo=pytz.utc, year=int(match.group(1)), month=int(match.group(2)), day=int(match.group(3)))
    raise Exception('cronjob_date must be one of -<int>, yyyy-mm, or yyyy-mm-dd')


if __name__ == '__main__':
    main()
