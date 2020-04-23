import datetime
import ipaddress
import itertools
import sys
from collections import deque
from ipaddress import IPv4Address
from typing import List, Iterator, Dict, NamedTuple, Optional, TextIO, Any

from abstract_configuration import AbstractConfiguration, AbstractSessionInfo
from ip_to_host_converter import IpToHostConverter
from log_entry import LogEntry


class LiveSession(NamedTuple):
    """Used by LogParser.run_realtime to keep track of active session"""
    host_ip: IPv4Address
    session_info: AbstractSessionInfo
    start_time_string: str
    start_time: datetime.datetime
    timeout: datetime.datetime

    def with_timeout(self, timeout: datetime.datetime) -> 'LiveSession':
        return self._replace(timeout=timeout)


class Entry(NamedTuple):
    log_entry: LogEntry
    relative_start_time: datetime.timedelta
    data: List[str]
    opus_url: Optional[str]

    def target_url(self) -> str:
        return self.log_entry.url.geturl()


class Session(NamedTuple):
    host_ip: IPv4Address
    entries: List[Entry]
    session_info: AbstractSessionInfo
    id: str

    def start_time(self) -> datetime.datetime:
        return self.entries[0].log_entry.time

    def duration(self) -> datetime.timedelta:
        return self.entries[-1].log_entry.time - self.entries[0].log_entry.time

    @property
    def total_time(self) -> datetime.timedelta:
        return self.duration()


class HostInfo(NamedTuple):
    ip: IPv4Address
    name: Optional[str]
    sessions: List[Session]

    def hostname(self) -> str:
        return f'{self.name} ({self.ip})' if self.name else str(self.ip)

    @property
    def total_time(self) -> datetime.timedelta:
        return sum((session.duration() for session in self.sessions), datetime.timedelta(0))

    def start_time(self) -> datetime.datetime:
        return self.sessions[0].start_time()


class LogParser:
    """
    Code that reads through the log entries, groups them by host and by session, and prints them out in a nice format.
    """
    _configuration: AbstractConfiguration
    _session_timeout: datetime.timedelta
    _output: TextIO
    _by_ip: bool
    _ignored_ips: List[ipaddress.IPv4Network]
    _ip_to_host_converter: IpToHostConverter
    _id_generator: Iterator[str]

    def __init__(self, configuration: AbstractConfiguration, *,
                 session_timeout_minutes: int, output: str,
                 uses_html: bool, by_ip: bool,
                 ip_to_host_converter: IpToHostConverter,
                 ignored_ips: List[ipaddress.IPv4Network],
                 **_: Any):
        self._configuration = configuration
        self._session_timeout = datetime.timedelta(minutes=session_timeout_minutes)
        self._output = open(output, "w") if output else sys.stdout
        self._uses_html = uses_html
        self._by_ip = by_ip
        self._ignored_ips = ignored_ips
        self._ip_to_host_converter = ip_to_host_converter
        self._id_generator = (f'{value:X}' for value in itertools.count(100))

    def run_batch(self, log_entries: List[LogEntry]) -> None:
        print(f'Parsing input')
        all_sessions = self.__get_session_list(log_entries, self._uses_html)

        def do_grouping(by_ip: bool) -> List[HostInfo]:
            if by_ip:
                all_sessions.sort(key=lambda session: (session.host_ip, session.start_time()))
                sessions_list = [list(group)
                                 for _, group in itertools.groupby(all_sessions, lambda session: session.host_ip)]
            else:
                all_sessions.sort(key=lambda session: session.start_time())
                sessions_list = [[session] for session in all_sessions]
            host_infos = [HostInfo(ip=ip, name=self._ip_to_host_converter.convert(ip), sessions=sessions)
                          for sessions in sessions_list
                          for ip in [sessions[0].host_ip]]
            if by_ip:
                host_infos.sort(key=lambda host_info: self.__sort_key_from_ip_and_name(host_info.ip, host_info.name))
            return host_infos

        output = self._output
        print(f'Writing file {output.name}')
        if not self._uses_html:
            host_infos = do_grouping(self._by_ip)
            self.__generate_batch_text_output(host_infos)
        else:
            host_infos = do_grouping(by_ip=True)
            self.__generate_batch_html_output(host_infos)

    def run_summary(self, log_entries: List[LogEntry]) -> None:
        """Print out all slugs that have appeared in the text."""
        all_sessions = self.__get_session_list(log_entries, uses_html=False)
        self._configuration.show_summary(all_sessions, self._output)

    def run_realtime(self, log_entries: Iterator[LogEntry]) -> None:
        """
        Look at the list of log entries in real-time mode.

        Each entry is processed as it is received.  Sessions can be interrupted and then continued to show information
        appearing in other sessions.  Note that log_entries is typically a generator tailing a file.
        """
        output = self._output
        live_sessions: Dict[IPv4Address, LiveSession] = {}
        previous_host_ip: Optional[IPv4Address] = None
        need_host_separator: bool = False
        for entry in log_entries:
            if any(entry.host_ip in ipNetwork for ipNetwork in self._ignored_ips):
                continue

            current_time = entry.time
            next_timeout = current_time + self._session_timeout

            # Delete all sessions that have expired, even it it matches this one.
            expired_sessions = {session_info for session_info in live_sessions.values()
                                if session_info.timeout < current_time}
            for session in expired_sessions:
                live_sessions.pop(session.host_ip)
            if previous_host_ip not in live_sessions:
                # It's possible we just expired the most recent session.  Oh well, that happens.
                previous_host_ip = None

            if entry.host_ip in live_sessions:
                is_just_created_session = False
                # Update the timeout, whether or not we actually use this item
                current_session = live_sessions[entry.host_ip].with_timeout(next_timeout)
                live_sessions[entry.host_ip] = current_session
                session_info = current_session.session_info
                entry_info, _ = session_info.parse_log_entry(entry)
                if not entry_info:
                    continue
            else:
                is_just_created_session = True
                session_info = self._configuration.create_session_info()
                entry_info, _ = session_info.parse_log_entry(entry)
                if not entry_info:
                    continue
                current_session = LiveSession(host_ip=entry.host_ip, session_info=session_info,
                                              start_time_string=entry.time_string, start_time=entry.time,
                                              timeout=next_timeout)
                live_sessions[entry.host_ip] = current_session

            # Print out information about this entry.
            if current_session.host_ip != previous_host_ip:
                # If we're at a different host_ip, then reprint a header.  Note that timing out on a session then
                # restarting the same ip will look like a different ip because previous_host_ip is set to None.
                if need_host_separator:
                    print('\n----------\n', file=output)
                need_host_separator = True
                previous_host_ip = current_session.host_ip

                hostname_from_ip = self.__get_hostname_from_ip(current_session.host_ip)
                postscript = '' if is_just_created_session else ' CONTINUED'
                print(f'Host {hostname_from_ip}: {current_session.start_time_string}{postscript}', file=output)

            self.__print_entry_info(entry, entry_info, current_session.start_time)

    def __get_session_list(self, log_entries: List[LogEntry], uses_html: bool) -> List[Session]:
        """Group the log entries into parsed sessions."""

        sessions: List[Session] = []
        log_entries.sort(key=lambda entry: (entry.host_ip, entry.time))
        for session_host_ip, session_log_entries_iter in itertools.groupby(log_entries, lambda entry: entry.host_ip):
            if any(session_host_ip in ipNetwork for ipNetwork in self._ignored_ips):
                continue
            session_log_entries = deque(session_log_entries_iter)
            while session_log_entries:
                # If the first entry has no information, it doesn't start a session
                entry = session_log_entries.popleft()
                session_info = self._configuration.create_session_info(uses_html=uses_html)
                entry_info, opus_url = session_info.parse_log_entry(entry)
                if not entry_info:
                    continue

                session_start_time = entry.time

                def create_session_entry(log_entry: LogEntry, entry_info: List[str], opus_url: Optional[str]) -> Entry:
                    return Entry(log_entry=log_entry,
                                 relative_start_time=entry.time - session_start_time,
                                 data=entry_info, opus_url=opus_url)

                current_session_entries = [create_session_entry(entry, entry_info, opus_url)]

                # Keep on grabbing entries for as long as we have not reached a timeout.
                session_end_time = session_start_time + self._session_timeout
                while session_log_entries and session_log_entries[0].time <= session_end_time:
                    entry = session_log_entries.popleft()
                    session_end_time = entry.time + self._session_timeout
                    entry_info, opus_url = session_info.parse_log_entry(entry)
                    if entry_info:
                        current_session_entries.append(create_session_entry(entry, entry_info, opus_url))

                if session_info.get_session_flags():
                    # We ignore sessions that don't actually do anything.
                    sessions.append(Session(host_ip=session_host_ip,
                                            entries=current_session_entries,
                                            session_info=session_info,
                                            id=next(self._id_generator)))

        return sessions

    def __generate_batch_text_output(self, host_infos: List[HostInfo]) -> None:
        output = self._output
        assert not self._uses_html
        for i, host_info in enumerate(host_infos):
            if i > 0:
                print('\n----------\n', file=output)
            hostname_from_ip = f'{host_info.name, ({host_info.ip})}' if host_info.name else str(host_info.ip)
            for j, session in enumerate(host_info.sessions):
                if j > 0:
                    print(file=output)
                entries = session.entries
                print(f'Host {hostname_from_ip}: {entries[0].log_entry.time_string}', file=output)
                for entry in entries:
                    self.__print_entry_info(entry.log_entry, entry.data, session.start_time())

    def __generate_batch_html_output(self, host_infos_by_ip: List[HostInfo]) -> None:
        batch_html_generator = self._configuration.create_batch_html_generator(host_infos_by_ip)
        batch_html_generator.generate_output(self._output)

    def __print_entry_info(self, this_entry: LogEntry, this_entry_info: List[str],
                           session_start_time: datetime.datetime) -> None:
        """Print out the information for a log entry."""
        duration = this_entry.time - session_start_time
        print(f'    +{duration}: {this_entry_info[0]}', file=self._output)
        for info in this_entry_info[1:]:
            print(f'              {info}', file=self._output)

    def __get_hostname_from_ip(self, ip: IPv4Address) -> str:
        name = self._ip_to_host_converter.convert(ip)
        if name:
            return f'{name} ({ip})'
        else:
            return f'{ip}'

    @staticmethod
    def __sort_key_from_ip_and_name(ip: IPv4Address, name: Optional[str]) -> Any:
        if name:
            return 1, tuple(reversed(name.lower().split('.')))
        else:
            return 2, ip
