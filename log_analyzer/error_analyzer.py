import argparse
import datetime
import glob
import ipaddress
import itertools
import re
import sys
from bisect import bisect_left, bisect_right
from collections import deque, defaultdict
from operator import attrgetter
from typing import List, Optional, NamedTuple, Iterable, TextIO, Tuple, Dict

from LogEntry import LogReader, LogEntry

ERROR_PATTERN = re.compile(r'^\[([^\]]+)\] \[([^\]]+)\] \[([^\]]+)\] \[(client|remote) ([^\]]+):\d+\] (.*)$')

TEXT_ERROR_PATTERN = re.compile(r'^\[([^\]]+)\] (ERROR|WARNING) \[([^\]]+)\] (.*)$')

ERROR_LEEWAY = datetime.timedelta(milliseconds=20)


class ErrorEntry(NamedTuple):
    """Information from one line of an Apache log entry."""
    time: datetime.datetime
    host_ip: ipaddress.IPv4Address
    message: str
    code_location: Optional[str] = None
    severity: Optional[str] = None


class ErrorReader(object):
    _files: List[str]
    _output: TextIO
    _seen_errors: Dict[Tuple[str, ...], List[Tuple[List[ErrorEntry], List[LogEntry]]]]

    def __init__(self, files: List[str], output: TextIO):
        self._files = files
        self._output = output
        self._seen_errors = defaultdict(list)

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
            self._check_one_ip(host_ip, error_entries, log_entries)
        self._show_results()

    def _get_error_entries(self) -> List[ErrorEntry]:
        files = [file for file in self._files if "pds_error_log" in file]
        local_network = ipaddress.ip_network("10.1.0.0/24")

        def keep_error_entry(entry: ErrorEntry) -> bool:
            if entry.host_ip in local_network:
                return False
            if entry.severity and entry.message.startswith('Not Found: '):
                return False
            return True

        error_entries = self._read_error_files(files)
        return list(filter(keep_error_entry, error_entries))

    def _get_log_entries(self) -> List[LogEntry]:
        def keep_log_entry(entry: LogEntry) -> bool:
            if entry.status == 200 and entry.url.path.startswith('/static_media'):
                return False
            return True

        files = [file for file in self._files if "pds_access_log" in file]
        log_entries = LogReader.read_logs(files)
        return list(filter(keep_log_entry, log_entries))

    @staticmethod
    def _read_error_files(file_names: Iterable[str]) -> List[ErrorEntry]:
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
    def __parse_line_in_error_log(line: str) -> Optional[ErrorEntry]:
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
            time_string2, severity, code_location, message = match.groups()
            time2 = datetime.datetime.strptime(time_string2, '%d/%b/%Y %H:%M:%S')
            assert time2 == time.replace(microsecond=0, tzinfo=None)
            return ErrorEntry(time=time, host_ip=host_ip, message=message,
                              code_location=code_location, severity=severity)
        else:
            return ErrorEntry(time=time, host_ip=host_ip, message=rest)

    def _check_one_ip(self, host_ip: str, error_entries: List[ErrorEntry], log_entries: List[LogEntry]) -> None:
        error_entries_deque = deque(error_entries)
        log_entry_dates = [log_entry.time.replace(tzinfo=None) for log_entry in log_entries]

        def merge_error_entries(old_entries: List[ErrorEntry], new_entry: ErrorEntry) -> bool:
            delta = new_entry.time - old_entries[-1].time
            if delta >= ERROR_LEEWAY:
                return False
            if new_entry.message in (x.message for x in old_entries):
                return False
            return True

        while error_entries_deque:
            # Any set of error logs on the same host, in which each log is separated from the previous one by less than
            # 200ms is a single set of error logs
            these_error_entries = [error_entries_deque.popleft()]
            while error_entries_deque and merge_error_entries(these_error_entries, error_entries_deque[0]):
                these_error_entries.append(error_entries_deque.popleft())
            if not log_entries:
                these_log_entries: List[LogEntry] = []
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
            self._seen_errors[error_key].append((these_error_entries, these_log_entries))

    def _show_results(self) -> None:
        output = self._output
        seen_errors = self._seen_errors
        for key in sorted(seen_errors.keys(), key=lambda strs: (-len(seen_errors[strs]), -len(strs), strs)):
            print('\n========================\n', file=output)
            count = len(seen_errors[key])
            print(f'This error occurs { count } {"times" if count > 1 else "time"}', file=output)
            for line in key:
                print(line, file=output)
            for error_entries, log_entries in seen_errors[key]:
                print('   --- ', file=output)
                for log_entry in log_entries:
                    print(f'{log_entry.time}   {log_entry.url.geturl()}', file=output)
                if not log_entries:
                    print(f'Log entries missing', file=output)


def main(arguments: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(description='Process log files.')
    parser.add_argument('--output', '-o', type=argparse.FileType('w'), default=sys.stdout, dest='output',
                        help="output file.  default is stdout")
    parser.add_argument('files', nargs=argparse.REMAINDER, help='files')
    args = parser.parse_args(arguments)
    if not args.files:
        args.files = glob.glob("/users/fy/SETI/logs/tools.*")

    ErrorReader(args.files, args.output).run()


if __name__ == '__main__':
    main()
