import argparse
import importlib
import ipaddress
import operator

from typing import List, Optional, cast

from abstract_configuration import AbstractConfiguration
from cronjob_utils import convert_cronjob_to_batchjob
from log_entry import LogReader
from log_parser import LogParser
from ip_to_host_converter import IpToHostConverter


DEFAULT_FIELDS_PREFIX = 'https://opus.pds-rings.seti.org'


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
    parser.add_argument('--configuration', dest='"opus.configuration"',
                        help="location of python configuration file")

    # TODO(fy): Temporary hack for when I don't have internet access
    parser.add_argument('--xxlocal', action="store_true", dest="uses_local", help=argparse.SUPPRESS)
    # TODO(fy): Debugging hack that shows all URLs.
    parser.add_argument('--xxshowall', action='store_true', dest='debug_show_all', help=argparse.SUPPRESS)

    parser.add_argument('log_files', nargs=argparse.REMAINDER, help='log files')
    args = parser.parse_args(arguments)

    if args.cronjob:
        # Fix up the arguments to match what everyone else wants
        convert_cronjob_to_batchjob(args, from_first_of_month=True)
        if not args.log_files:
            print("No log files found.")
            return

    # args.ignored_ip comes out as a list of lists, and it needs to be flattened.
    args.ignored_ips = [ip for arg_list in args.ignore_ip for ip in arg_list]
    # Another fake argument we need
    args.ip_to_host_converter = IpToHostConverter.get_ip_to_host_converter(args.uses_reverse_dns, args.uses_local)

    module = importlib.import_module("opus.configuration")
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


if __name__ == '__main__':
    import glob
    files = glob.glob("/users/fy/Dropbox/Shared-Frank-Yellin/logs-2020-02/*2020-02-2*")
    args = ["--output", "/Users/fy/www/save.html",
            "--batch", "--html",
            "--xxlocal", "--dns",
            *files]
    main(args)
