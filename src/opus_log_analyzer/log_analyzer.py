"""The log analyzer: turn Apache access logs into a session report.

`python -m opus_log_analyzer` runs this. The work is a pipeline: `LogReader`
parses log lines, `LogParser` groups them into per-host sessions, and the
`--configuration` module interprets each session in the vocabulary of the site
being analyzed -- OPUS by default -- and renders the report.

`--batch` and `--cronjob` are the modes that run today. The other three read an
argument the parser never defines and fail before doing any work.
"""
import argparse
import glob
import importlib
import ipaddress
import operator
from enum import Enum, auto
from typing import cast

from opus_log_analyzer.abstract_configuration import AbstractConfiguration
from opus_log_analyzer.cronjob_utils import expand_globs_and_dates
from opus_log_analyzer.ip_to_host_converter import IpToHostConverter
from opus_log_analyzer.log_entry import LogEntry, LogReader
from opus_log_analyzer.log_parser import LogParser

DEFAULT_FIELDS_PREFIX = 'https://opus.pds-rings.seti.org'

# --configuration names a module, imported by name, that supplies the Configuration class
# describing the site being analyzed. The default names the packaged OPUS configuration
# by its absolute import path; a bare 'opus.configuration' resolved only while the
# analyzer was run from its own source directory, and there is no top-level `opus`
# package to fall back on (the Django project package is `opus_app`).
DEFAULT_CONFIGURATION_MODULE = 'opus_log_analyzer.opus.configuration'


class RunType(Enum):
    """Which of the analyzer's four modes a run is in."""

    BATCH = auto(),
    SUMMARY = auto(),
    REALTIME = auto(),
    FAKE_REALTIME = auto()


def _create_argument_parser() -> argparse.ArgumentParser:
    """Build the command-line parser.

    Kept separate from `main` so the shipped defaults -- notably
    `DEFAULT_CONFIGURATION_MODULE` -- can be asserted without running the
    analyzer.

    Returns:
        The parser, with `prog` set explicitly so the help text names the
        installed command rather than the file argparse was run from.
    """

    def parse_ignored_ips(x: str) -> list[ipaddress.IPv4Network]:
        """Parse one comma-separated `--ignore-ip` value into networks.

        Parameters:
            x: A comma-separated list of CIDR blocks or bare addresses.

        Returns:
            One network per element. The declared element type is IPv4 because
            the rest of this package is; `ip_network` returns an IPv6 network
            for an IPv6 argument, which then matches nothing.
        """
        return [
            ipaddress.ip_network(address, strict=False)  # type: ignore[misc]  # see docstring
            for address in x.split(',')
        ]

    # prog is explicit because argparse would otherwise name whatever file was executed:
    # `__main__.py` for `python -m opus_log_analyzer`.
    parser = argparse.ArgumentParser(prog='opus_log_analyzer', description='Process log files.')

    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument('--batch', '-b',
                       action='store_const', dest="run_type", const=RunType.BATCH,
                       help='Print a report on one or more completed log files.  The default.')
    group.add_argument('--summary',
                       action='store_const', dest="run_type", const=RunType.SUMMARY,
                       help="Show the slugs that have been used in a log file")
    group.add_argument('--cronjob',
                       action='store_const', dest="run_type", const=RunType.BATCH,
                       help="Deprecated.  Use --batch instead")
    group.add_argument('--realtime', '--interactive', '-i', '-r',
                       action='store_const', dest="run_type", const=RunType.REALTIME,
                       help='Watch a single log file in realtime')
    group.add_argument('--xxfake-realtime',
                       action='store_const', dest="run_type", const=RunType.FAKE_REALTIME,
                       help=argparse.SUPPRESS,)
    parser.set_defaults(run_type=RunType.BATCH)

    group2 = parser.add_mutually_exclusive_group()
    group2.add_argument('--by-ip', action='store_true', dest='by_ip',
                        help='Sorts batched logs by host ip')
    group2.add_argument('--by-time', action='store_false', dest='by_ip',
                        help='Sorts batched logs by session start time')

    parser.add_argument('--html', action='store_true', dest='uses_html',
                        help='Generate html output rather than text output')
    parser.add_argument('--no-sessions', action='store_true', dest='no_sessions',
                        help="Don't generate detailed session information")

    parser.add_argument('--date', '--cronjob-date', action='store', dest='date',
                        help='Date for --batch.  One of -<number>, yyyy-mm, or yyyy-mm-dd.  default is today.')

    parser.add_argument('--api-host-url', default=DEFAULT_FIELDS_PREFIX, metavar='URL', dest='api_host_url',
                        help='base url to access the information')
    parser.add_argument('--reverse-dns', '--dns', action='store_true', dest='uses_reverse_dns',
                        help='Attempt to resolve the real host name')
    parser.add_argument('--ignore-ip', '-x', default=[], action="append", metavar='cidrlist', dest='ignore_ip',
                        type=parse_ignored_ips,
                        help='list of ips to ignore.  May be specified multiple times')
    parser.add_argument('--session-timeout', default=60, type=int, metavar="minutes", dest='session_timeout_minutes',
                        help='a session ends after this period (minutes) of inactivity')
    parser.add_argument('--manifest', default=[], action='append', dest='manifests')

    parser.add_argument('--output', '-o', dest='output',
                        help="output file.  default is stdout.  For --batch, specifies the output pattern")
    parser.add_argument('--sessions-relative-directory', dest="sessions_relative_directory",
                        help="relative directory into which to store the sessions information")
    parser.add_argument('--configuration', dest='configuration_file',
                        default=DEFAULT_CONFIGURATION_MODULE,
                        help="location of python configuration file")

    # Stores DNS entries in a persistent database
    parser.add_argument('--xxdns-cache', action="store_true", dest="dns_cache", help=argparse.SUPPRESS)

    # Debugging hack that shows all log entries
    parser.add_argument('--xxshowall', action='store_true', dest='debug_show_all', help=argparse.SUPPRESS)

    # Caches the read entries into a database, rather than reading the log files anew each time.
    parser.add_argument('--xxcached_log_entry', action='store_true', dest='cached_log_entries', help=argparse.SUPPRESS)

    parser.add_argument('log_files', nargs=argparse.REMAINDER, help='log files')
    return parser


def main(arguments: list[str] | None = None) -> None:
    """Run the analyzer.

    Parameters:
        arguments: The command line, or None to read `sys.argv`.

    Raises:
        AttributeError: In any mode other than `--batch`/`--cronjob`, before any
            work is done, because the branch that handles them reads an argument
            the parser never defines.
        Exception: If real-time mode was given other than exactly one log file,
            or any other mode was given none.
    """
    args = _create_argument_parser().parse_args(arguments)

    run_type = cast(RunType, args.run_type)

    if run_type == RunType.BATCH:
        # Fix up the arguments to match what everyone else wants
        expand_globs_and_dates(args)
    elif args.glob:
        args.log_files = [file for pattern in args.log_files for file in glob.glob(pattern)]
        args.manifests = [file for pattern in args.manifests for file in glob.glob(pattern)]

    # args.ignored_ip comes out as a list of lists, and it needs to be flattened.
    args.ignored_ips = [ip for arg_list in args.ignore_ip for ip in arg_list]
    args.ip_to_host_converter = \
        IpToHostConverter.get_ip_to_host_converter(**vars(args))

    module = importlib.import_module(args.configuration_file)
    configuration = cast(AbstractConfiguration, module.Configuration(**vars(args)))
    log_parser = LogParser(configuration, **vars(args))

    if run_type == RunType.REALTIME:
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

        if run_type == RunType.BATCH:
            log_parser.run_batch(log_entries_list)
        elif run_type == RunType.SUMMARY:
            log_parser.run_summary(log_entries_list)
        elif run_type == RunType.FAKE_REALTIME:
            log_entries_list.sort(key=operator.attrgetter('time'))
            log_parser.run_realtime(iter(log_entries_list))


def handle_cached_log_entries(args: argparse.Namespace) -> list[LogEntry]:
    """Read the log entries, through a pickle cache keyed on the file names.

    Used only under the hidden `--xxcached_log_entry` flag, to make repeated
    runs over the same logs quick while developing.

    Parameters:
        args: The parsed arguments; `log_files` is read.

    Returns:
        The parsed entries, from `.logs/log-<hash>.db` if that file exists,
        otherwise freshly read and then written there. The cache is keyed on the
        sorted file names alone, so it does not notice a log file changing
        underneath it, and the path is relative to the working directory.
    """
    import hashlib

    # Imported for the self-written entry cache; see the pickle.load below.
    import pickle  # nosec B403

    log_files = sorted(args.log_files)
    hash_key = hashlib.sha256(':'.join(log_files).encode()).hexdigest()
    filename = f'.logs/log-{hash_key[:8]}.db'

    try:
        with open(filename, "rb") as data:
            print(f"Reading logs from {filename}")
            # A parsed-log-entry cache this process wrote itself, under the hidden
            # --xxcached_log_entry flag. The input is never attacker-supplied.
            return cast(list[LogEntry], pickle.load(data))  # nosec B301
    except FileNotFoundError as _e:
        pass

    result = LogReader.read_logs(args.log_files)
    with open(filename, "wb") as output:
        pickle.dump(result, output)
        print(f"Caching logs as {filename}")

    return result


if __name__ == '__main__':
    main()
