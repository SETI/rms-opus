import argparse
import ipaddress
from typing import List, Optional

from LogEntry import LogReader
from LogParser import LogParser
from SessionInfo import SessionInfoGenerator
from SlugInfo import SlugMap

DEFAULT_FIELDS_PREFIX = 'https://tools.pds-rings.seti.org'


def main(arguments: Optional[List[str]] = None) -> None:
    def parse_ignored_ips(x):
        return [ipaddress.ip_network(address, strict=False) for address in x.split(',')]

    parser = argparse.ArgumentParser(description='Process log files.')

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--realtime', '--interactive', '-i', '-r', action='store_true',
                       help='Watch a single log file in realtime')
    group.add_argument('--batch', '-b', action='store_true',
                       help='Print a report on one or more completed log files')
    group.add_argument('--summary', '-s', action='store_true',
                       help='Print a batch report sorted by ip')
    group.add_argument('--show_slugs', action='store_true', dest='show_slugs')
    group.add_argument('--xxfake', action='store_true', help=argparse.SUPPRESS, dest='fake')  # For testing only

    parser.add_argument('--api-host-url', default=DEFAULT_FIELDS_PREFIX, metavar='URL', dest='api_host_url',
                        help='base url to access the information')
    parser.add_argument('--reverse-dns', '--dns', action='store_true', dest='reverse_dns',
                        help='Attempt to resolve the real host name')
    parser.add_argument('--ignore-ip', '-x', default=[], action="append", metavar='cidrlist', dest='ignore_ip',
                        type=parse_ignored_ips,
                        help='list of ips to ignore.  May be specified multiple times')
    parser.add_argument('--session-timeout', default=60, type=int, metavar="minutes", dest='session_timeout')

    # TODO(fy): Temporary hack for when I don't have internet access
    parser.add_argument('--xxlocal_slugs', action="store_const", const="file:///users/fy/SETI/pds-opus",
                        dest='api_host_url', help=argparse.SUPPRESS)

    parser.add_argument('log_files', nargs=argparse.REMAINDER, help='log files')
    args = parser.parse_args(arguments)

    slugs = SlugMap(args.api_host_url)
    # args.ignored_ip comes out as a list of lists, and it needs to be flattened.
    ignored_ips = [ip for arg_list in args.ignore_ip for ip in arg_list]
    session_info_generator = SessionInfoGenerator(slugs, ignored_ips)
    log_parser = LogParser(session_info_generator, args.reverse_dns, args.session_timeout)

    if args.realtime:
        if len(args.log_files) != 1:
            raise Exception("Must specify exactly one file for batch mode.")
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
        elif args.show_slugs:
            log_parser.show_slugs(log_entries_list)
        elif args.fake:
            log_parser.run_realtime(iter(log_entries_list))


if __name__ == '__main__':
    main()
