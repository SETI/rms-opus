import io
import ipaddress
import operator
import re
from datetime import datetime
from time import sleep
from typing import List, Optional, Iterator, NamedTuple, Iterable
from urllib.parse import urlsplit, SplitResult

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
    """Information from one line of an Apache log entry."""
    host_ip: ipaddress.IPv4Address
    user: Optional[str]
    status: int
    method: str
    url: SplitResult
    size: Optional[int]
    agent: Optional[str]
    time_string: str
    time: datetime


class LogReader(object):
    @staticmethod
    def read_logs(file_names: Iterable[str]) -> List[LogEntry]:
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
        with open(file_name, "r") as file:
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
    def __parse_line(line: str) -> Optional[LogEntry]:
        """Converts a line from an Apache log file into a LogEntry."""
        match = re.match(LOG_PATTERN, line)
        if not match:
            return None
        info = match.groupdict()
        host_ip = ipaddress.ip_address(info['host'])
        user = None if info['user'] == '-' else info['user']
        time_string = info['time']
        status = int(info['status'])
        request = info['request']
        first_space = request.find(" ")
        last_space = request.rfind(" ")
        if first_space == -1 or last_space == -1 or first_space >= last_space:
            return None
        method = request[:first_space].upper()
        url = urlsplit(request[first_space + 1:last_space])
        size = None if info['size'] == '-' else int(info['size'])
        agent = None if info['agent'] == '-' else info['agent']
        time = datetime.strptime(time_string, '%d/%b/%Y:%H:%M:%S %z')
        return LogEntry(host_ip=host_ip, user=user, status=status, method=method,
                        url=url, size=size, agent=agent, time_string=time_string, time=time)
