"""Reading an Apache access log into structured entries.

One `LogEntry` is one line of the combined log format. `LogReader` reads a whole
file, or tails one, and silently drops any line that does not match -- a log
directory holds lines from other tools as well.
"""

import io
import ipaddress
import re
from collections.abc import Iterable, Iterator
from datetime import datetime
from time import sleep
from typing import NamedTuple
from urllib.parse import SplitResult, urlsplit

# https://gist.github.com/sumeetpareek/9644255
parts = [
    r'(?P<host>\S+)',  # host %h
    r'\S+',  # indent %l (unused)
    r'(?P<user>\S+)',  # user %u
    r'\[(?P<time>.+)\]',  # time %t
    r'"(?P<request>.*)"',  # request "%r"
    r'(?P<status>[0-9]+)',  # status %>s
    r'(?P<size>\S+)',  # size %b (careful, can be '-')
    r'"(?P<referrer>.*)"',  # referrer "%{Referer}i"
    r'"(?P<agent>.*)"',  # user agent "%{User-agent}i"
]

LOG_PATTERN = re.compile(r'\s+'.join(parts) + r'\s*\Z')


class LogEntry(NamedTuple):
    """Information from one line of an Apache log entry.

    `host_ip` is declared IPv4 because everything downstream is; an IPv6 client
    address is stored here anyway.
    """

    host_ip: ipaddress.IPv4Address
    user: str | None
    status: int
    method: str
    url: SplitResult
    size: int | None
    agent: str | None
    time_string: str
    time: datetime


class LogReader:
    """Turns Apache access-log files into `LogEntry` values."""

    @staticmethod
    def read_logs(file_names: Iterable[str]) -> list[LogEntry]:
        """Read every named log file and return the entries they parse to.

        Parameters:
            file_names: The log files to read, in the order they are read.

        Returns:
            One entry per line that matched the combined-log pattern, in file
            order. Lines that did not match are dropped without comment.
        """
        log_entries = []
        for file_name in file_names:
            print(f'Reading {file_name}')
            with open(file_name) as file:
                for log_line in file.readlines():
                    log_entry = LogReader.__parse_line(log_line)
                    if log_entry:
                        log_entries.append(log_entry)
        return log_entries

    @staticmethod
    def read_logs_from_tailed_file(file_name: str, sleep_time: float = 1.0) -> Iterator[LogEntry]:
        """Yield entries from a log file as they are written to it, forever.

        Parameters:
            file_name: The log file to follow.
            sleep_time: Seconds to wait before re-reading after reaching the end
                of the file.

        Yields:
            One entry per line that matches the combined-log pattern. The
            iterator never ends; the caller stops consuming it.
        """
        with open(file_name) as file:
            while True:
                curr_position = file.tell()
                log_line = file.readline()
                if not log_line:
                    file.seek(curr_position, io.SEEK_SET)
                    sleep(sleep_time)
                else:
                    log_entry = LogReader.__parse_line(log_line)
                    if log_entry:
                        yield log_entry

    @staticmethod
    def __parse_line(line: str) -> LogEntry | None:
        """Convert one line of an Apache log file into a `LogEntry`.

        Parameters:
            line: The raw log line.

        Returns:
            The parsed entry, or None if the line does not match the
            combined-log pattern or its request field is not
            `<method> <url> <protocol>`.

        Raises:
            ValueError: If the line matches the pattern but a field within it
                does not parse -- an address field that is not an IP address
                (which is what Apache writes under `HostnameLookups On`), a
                non-numeric size, or an unparseable timestamp. One such line
                aborts the whole run rather than being skipped.
        """
        match = re.match(LOG_PATTERN, line)
        if not match:
            return None
        info = match.groupdict()
        # ip_address returns IPv4Address | IPv6Address, while this package
        # declares IPv4 throughout. An IPv6 client address is stored here
        # regardless, which is a real limitation rather than an impossible case
        # -- see issue #1463. Resolving it means deciding what the analyzer
        # should do with IPv6, which is behavior work and out of scope
        # (plan rev 7.14), so the assumption is recorded rather than changed.
        host_ip = ipaddress.ip_address(info['host'])
        user = None if info['user'] == '-' else info['user']
        time_string = info['time']
        status = int(info['status'])
        request = info['request']
        first_space = request.find(' ')
        last_space = request.rfind(' ')
        if first_space == -1 or last_space == -1 or first_space >= last_space:
            return None
        method = request[:first_space].upper()
        url = urlsplit(request[first_space + 1 : last_space])
        size = None if info['size'] == '-' else int(info['size'])
        agent = None if info['agent'] == '-' else info['agent']
        time = datetime.strptime(time_string, '%d/%b/%Y:%H:%M:%S %z')
        return LogEntry(
            host_ip=host_ip,  # type: ignore[arg-type]  # see the note above
            user=user,
            status=status,
            method=method,
            url=url,
            size=size,
            agent=agent,
            time_string=time_string,
            time=time,
        )
