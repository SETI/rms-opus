import argparse
import datetime
import ipaddress
import itertools
import re
import sys
from bisect import bisect_left, bisect_right
from collections import defaultdict, deque
from collections.abc import Iterable
from operator import attrgetter
from typing import NamedTuple, TextIO, cast

from opus_log_analyzer.cronjob_utils import expand_globs_and_dates
from opus_log_analyzer.jinga_environment import JINJA_ENVIRONMENT
from opus_log_analyzer.log_entry import LogEntry, LogReader

ERROR_PATTERN = re.compile(r'^\[([^\]]+)\] \[([^\]]+)\] \[([^\]]+)\] \[(client|remote) ([^\]]+):\d+\] (.*)$')

TEXT_ERROR_PATTERN = re.compile(r'^\[([^\]]+)\] (ERROR|WARNING) \[([^\]]+)\] (.*)$')

ERROR_LEEWAY = datetime.timedelta(milliseconds=20)


class ErrorEntry(NamedTuple):
    """Information from one line of an Apache log entry."""
    time: datetime.datetime
    host_ip: ipaddress.IPv4Address
    message: str
    full_message: str
    code_location: str | None = None
    severity: str | None = None


class ErrorAndLog(NamedTuple):
    error_entries: list[ErrorEntry]
    log_entries: list[LogEntry]


class ErrorReader:
    _files: list[str]
    _ignored_ips: list[ipaddress.IPv4Network]
    _ignored_errors: list[str]
    _output: TextIO
    _seen_errors: dict[tuple[str, ...], list[ErrorAndLog]]
    _uses_html: bool

    def __init__(self, files: list[str], ignored_ips: list[ipaddress.IPv4Network], ignored_errors: list[str],
                 output: TextIO, uses_html: bool):
        self._files = files
        self._ignored_ips = ignored_ips
        self._ignored_errors = ignored_errors
        self._output = output
        self._seen_errors = defaultdict(list)
        self._uses_html = uses_html

    def run(self) -> None:
        error_entries = self._get_error_entries()
        error_entries.sort(key=attrgetter('host_ip', 'time'))
        errors_by_host_ip = [(host_ip, list(error_entries))
                             for host_ip, error_entries in itertools.groupby(error_entries, attrgetter("host_ip"))]

        log_entries = self._get_log_entries()
        log_entries.sort(key=attrgetter('host_ip', 'time'))
        log_entries_by_host_ip = {host_ip: list(log_entries) for host_ip, log_entries in
                                  itertools.groupby(log_entries, attrgetter('host_ip'))}
        for host_ip, error_entries in errors_by_host_ip:
            log_entries = log_entries_by_host_ip.get(host_ip, [])
            self._check_one_ip(error_entries, log_entries)
        self._show_results()

    def _get_error_entries(self) -> list[ErrorEntry]:
        files = [file for file in self._files if "error" in file]
        if not files:
            raise Exception("You must specify at least one error log.")

        error_entries = self._read_error_files(files)
        error_entries = [entry for entry in error_entries
                         # skip the ignored IPs
                         if not any(entry.host_ip in network for network in self._ignored_ips)
                         # we don't are about "URL not found" messages
                         if not self._ignore_error_message(entry)]
        return error_entries

    def _ignore_error_message(self, entry: ErrorEntry) -> bool:
        result = any(ignored_error in entry.full_message for ignored_error in self._ignored_errors)
        return result

    def _get_log_entries(self) -> list[LogEntry]:
        files = [file for file in self._files if "access" in file]
        log_entries = LogReader.read_logs(files)
        return [entry for entry in log_entries
                # Note, we don't bother filtering out ignored ips or local network.  They won't get in the way
                # We do filter out /static_media requests returning 200, because they can't possible be the cause of
                # an error message.
                if not(entry.status == 200 and entry.url.path.startswith('/static_media'))]

    @staticmethod
    def _read_error_files(file_names: Iterable[str]) -> list[ErrorEntry]:
        error_entries = []
        for file_name in sorted(file_names):
            print(f'Reading {file_name}')
            with open(file_name) as file:
                for error_line in file.readlines():
                    error_entry = ErrorReader.__parse_line_in_error_log(error_line)
                    if error_entry:
                        error_entries.append(error_entry)
        return error_entries

    @staticmethod
    def __parse_line_in_error_log(line: str) -> ErrorEntry | None:
        """Converts a line from an Apache log file into a LogEntry."""
        match = re.match(ERROR_PATTERN, line)
        if not match:
            return None
        time_string, _, _, _, location, rest = match.groups()
        # [Fri Dec 16 01:46:23 2005]
        host_ip = ipaddress.ip_address(location)
        time = datetime.datetime.strptime(time_string, '%a %b %d %H:%M:%S.%f %Y')
        match = re.match(TEXT_ERROR_PATTERN, rest)
        if match:
            _time_string2, severity, code_location, message = match.groups()
            # time2 = datetime.datetime.strptime(time_string2, '%d/%b/%Y %H:%M:%S')
            # assert time2 == time.replace(microsecond=0, tzinfo=None)
            return ErrorEntry(time=time, host_ip=host_ip, message=message,
                              code_location=code_location, severity=severity, full_message=rest)
        else:
            return ErrorEntry(time=time, host_ip=host_ip, message=rest, full_message=rest)

    def _check_one_ip(self, error_entries: list[ErrorEntry], log_entries: list[LogEntry]) -> None:
        error_entries_deque = deque(error_entries)
        log_entry_dates = [log_entry.time.replace(tzinfo=None) for log_entry in log_entries]

        def merge_error_entries(old_entries: list[ErrorEntry], new_entry: ErrorEntry) -> bool:
            # In some cases, error logs can be more than one line long.  This function returns true if the next
            # line in the error log probably belongs with the previous ones.
            delta = new_entry.time - old_entries[-1].time
            if delta >= ERROR_LEEWAY:
                return False
            return new_entry.message not in (x.message for x in old_entries)

        while error_entries_deque:
            these_error_entries = [error_entries_deque.popleft()]
            while error_entries_deque and merge_error_entries(these_error_entries, error_entries_deque[0]):
                these_error_entries.append(error_entries_deque.popleft())
            if not log_entries:
                # don't bother looking if there are no log entries
                these_log_entries: list[LogEntry] = []
            else:
                start_time = these_error_entries[0].time.replace(microsecond=0)
                end_time = these_error_entries[-1].time
                left = bisect_left(log_entry_dates, start_time)
                right = bisect_right(log_entry_dates, end_time)
                if left < right and left != len(log_entry_dates):
                    these_log_entries = log_entries[left:right]
                else:
                    these_log_entries = []
            error_key = tuple(entry.message for entry in these_error_entries)
            self._seen_errors[error_key].append(ErrorAndLog(these_error_entries, these_log_entries))

    def _show_results(self) -> None:
        seen_errors = self._seen_errors
        results: list[tuple[tuple[str, ...], int, datetime.datetime, list[list[LogEntry]]]] = []
        for key in sorted(seen_errors.keys(), key=lambda strs: (-len(seen_errors[strs]), -len(strs), strs)):
            sorted_error_and_log_pairs = sorted(seen_errors[key], key=lambda x: x.error_entries[0].time)
            min_time = sorted_error_and_log_pairs[0].error_entries[0].time
            all_sorted_log_entries = [
                sorted(log_entries, key=attrgetter('time')) for _, log_entries in sorted_error_and_log_pairs
            ]
            count = len(seen_errors[key])
            results.append((key, count, min_time, all_sorted_log_entries))

        print(f'Writing output to {self._output.name}')

        if not self._uses_html:
            self.__generate_text_output(results)
        else:
            self.__generate_html_output(results)

    def __generate_text_output(
            self,
            results: list[tuple[tuple[str, ...], int, datetime.datetime, list[list[LogEntry]]]]) -> None:
        output = self._output
        for key, count, min_time, all_sorted_log_entries in results:
            output.write('\n========================\n\n')
            if count == 1:
                output.write(f'This error occurs once at {min_time}.\n')
            else:
                output.write(f'This error occurs {count} times; the first occurrence is at {min_time}.\n')
            for line in key:
                output.write(f'{line}\n')
            for log_entries in all_sorted_log_entries:
                output.write('   --- \n')
                if log_entries:
                    output.write(f'IP: {log_entries[0].host_ip}\n')
                    for log_entry in log_entries:
                        output.write(f'{log_entry.time} {log_entry.url.geturl()}\n')
                else:
                    output.write('Log entries missing\n')

    def __generate_html_output(
            self,
            results: list[tuple[tuple[str, ...], int, datetime.datetime, list[list[LogEntry]]]]) -> None:
        template = JINJA_ENVIRONMENT.get_template('error_analysis.html')
        for result in template.generate(results=results):
            self._output.write(result)


def main(arguments: list[str] | None = None) -> None:
    def parse_ignored_ips(x: str) -> list[ipaddress.IPv4Network]:
        return [ipaddress.ip_network(address, strict=False) for address in x.split(',')]

    # prog is explicit so the help text names the installed command whichever way the
    # module is invoked, rather than the file argparse happens to have been run from.
    parser = argparse.ArgumentParser(prog='opus_error_analyzer', description='Process log files.')
    parser.add_argument('--ignore-ip', '-x', default=[], action="append", metavar='cidrlist', dest='ignore_ip',
                        type=parse_ignored_ips,
                        help='list of ips to ignore.  May be specified multiple times')

    parser.add_argument('--output', '-o', dest='output',
                        help="output file.  default is stdout.  For --cronjob, specifies the output pattern")
    parser.add_argument('--html', action='store_true', dest='uses_html',
                        help='Generate html output rather than text output')

    parser.add_argument('--cronjob', action='store_true', dest='cronjob',
                        help="DEPRECATED")

    parser.add_argument('--date', '--cronjob-date', action='store', dest='date',
                        help='Date for batch job.  One of -<number>, yyyy-mm, or yyyy-mm-dd.  default is today.')

    parser.add_argument('--ignore-errors-file', type=argparse.FileType('r'), default=None, dest='ignore_errors_file')

    parser.add_argument('log_files', nargs=argparse.REMAINDER, help='error files')
    args = parser.parse_args(arguments)
    # args.ignored_ip comes out as a list of lists, and it needs to be flattened.
    ignored_ips = [ip for arg_list in args.ignore_ip for ip in arg_list]

    expand_globs_and_dates(args, error_analysis=True)

    if args.ignore_errors_file:
        lines = cast(TextIO, args.ignore_errors_file).readlines()
        ignored_errors = [line.strip() for line in lines if line.strip()]
    else:
        ignored_errors = []

    # Program-lifetime output stream (a file or stdout); not a scoped resource.
    output = sys.stdout if not args.output else open(args.output, "w")  # noqa: SIM115
    ErrorReader(args.log_files, ignored_ips, ignored_errors, output, args.uses_html).run()


if __name__ == '__main__':
    main()
