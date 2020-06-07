import argparse
import importlib
import ipaddress
import operator
import glob

from typing import List, Optional, cast

from abstract_configuration import AbstractConfiguration
from cronjob_utils import convert_cronjob_to_batchjob
from log_entry import LogReader, LogEntry
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
    parser.add_argument('--no-sessions', action='store_true', dest='no_sessions',
                        help="Don't generate detailed session information")

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
    parser.add_argument('--sessions-relative-directory', dest="sessions_relative_directory",
                        help="relative directory into which to store the sessions information")
    parser.add_argument('--configuration', dest='configuration_file', default='opus.configuration',
                        help="location of python configuration file")

    # Temporary hack for when I don't have internet access
    parser.add_argument('--xxlocal', action="store_true", dest="uses_local", help=argparse.SUPPRESS)
    # Stores DNS entries in a persistent database
    parser.add_argument('--xxdns-cache', action="store_true", dest="dns_cache", help=argparse.SUPPRESS)
    # Performs a glob() on filename arguments.  Useful when calling program from within an IDE that doesn't glob
    parser.add_argument('--xxglob', action="store_true", dest="glob", help=argparse.SUPPRESS)
    # Debugging hack that shows all log entries
    parser.add_argument('--xxshowall', action='store_true', dest='debug_show_all', help=argparse.SUPPRESS)
    # Caches the read entries into a database, rather than reading the log files anew each time.
    parser.add_argument('--xxcached_log_entry', action='store_true', dest='cached_log_entries', help=argparse.SUPPRESS)

    parser.add_argument('log_files', nargs=argparse.REMAINDER, help='log files')
    args = parser.parse_args(arguments)

    if args.cronjob:
        # Fix up the arguments to match what everyone else wants
        convert_cronjob_to_batchjob(args, from_first_of_month=True)
        if not args.log_files:
            print("No log files found.")
            return
    elif args.glob:
        args.log_files = [result for file in args.log_files for result in glob.glob(file)]

    # args.ignored_ip comes out as a list of lists, and it needs to be flattened.
    args.ignored_ips = [ip for arg_list in args.ignore_ip for ip in arg_list]
    args.ip_to_host_converter = \
        IpToHostConverter.get_ip_to_host_converter(args.uses_reverse_dns, args.uses_local, args.dns_cache)

    module = importlib.import_module(args.configuration_file)
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
        if args.cached_log_entries:
            log_entries_list = handle_cached_log_entries(args)
        else:
            log_entries_list = LogReader.read_logs(args.log_files)
        if args.batch:
            log_parser.run_batch(log_entries_list)
        elif args.summary:
            log_parser.run_summary(log_entries_list)
        elif args.fake_realtime:
            log_entries_list.sort(key=operator.attrgetter('time'))
            log_parser.run_realtime(iter(log_entries_list))


def handle_cached_log_entries(args: argparse.Namespace) -> List[LogEntry]:
    import pickle
    import hashlib

    log_files = sorted(args.log_files)
    hash = hashlib.sha256(':'.join(log_files).encode()).hexdigest()
    filename = f'log-{hash[:8]}.db'

    try:
        with open(filename, "rb") as data:
            print(f"Reading logs from {filename}")
            return cast(List[LogEntry], pickle.load(data))
    except FileNotFoundError as _e:
        pass

    result = LogReader.read_logs(args.log_files)
    with open(filename, "wb") as output:
        pickle.dump(result, output)
        print(f"Caching logs as {filename}")

    return result


if __name__ == '__main__':
    main()
