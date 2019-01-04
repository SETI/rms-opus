import datetime
import functools
import socket
import textwrap
from collections import defaultdict, deque
from heapq import heapify, heappop, heappush
from ipaddress import IPv4Address
from typing import List, Iterator, Dict, NamedTuple, Optional, Deque, Iterable

import Slug
from LogEntry import LogEntry
from SessionInfo import SessionInfo, SessionInfoGenerator


class _LiveSession(NamedTuple):
    """Used by LogParser.run_realtime to keep track of active session"""
    host_ip: IPv4Address
    session_info: SessionInfo
    start_time_string: str
    start_time: datetime.datetime
    timeout: datetime.datetime

    def with_timeout(self, timeout: datetime.datetime) -> '_LiveSession':
        return self._replace(timeout=timeout)


class LogParser:
    """
    Code that reads through the log entries, groups them by host and by session, and prints them out in a nice format.
    """
    _session_info_generator: SessionInfoGenerator
    _use_reverse_dns: bool
    _session_timeout: datetime.timedelta

    def __init__(self, session_info_generator: SessionInfoGenerator, use_reverse_dns: bool,
                 session_timeout_minutes: int):
        self._session_info_generator = session_info_generator
        self._use_reverse_dns = use_reverse_dns
        self._session_timeout = datetime.timedelta(minutes=session_timeout_minutes)

    def run_batch(self, log_entries: List[LogEntry]) -> None:
        """
        Look at the list of log entries in batch mode.

        The logs are aggregated into sessions, and each complete session is printed out in order of the start
        of the session.
        """

        entries_by_host = self.__group_log_entries_by_host_ip(log_entries)

        # Create a heap whose major key is the start time of the smallest log entry for the host
        heap = [(logs[0].time, logs[0].host_ip, logs) for logs in entries_by_host.values()]
        heapify(heap)

        need_host_separator = False

        while heap:
            # Grab the smallest element of the heap, which has the earliest start time.
            session_start_time, session_host_ip, session_log_entries = heappop(heap)
            # Get session info about the earliest log entry, which is popped off the list
            session_info = self._session_info_generator.create()
            entry = session_log_entries.popleft()
            entry_info = session_info.parse_log_entry(entry)
            if not entry_info:
                # Nope.  Update the information and put back onto the heap
                if session_log_entries:
                    heappush(heap, (session_log_entries[0].time, session_host_ip, session_log_entries))
                continue

            # No problems.  We have the start of a session
            if need_host_separator:
                print('\n----------\n')
            need_host_separator = True

            hostname_from_ip = self.__get_hostname_from_ip(session_host_ip)
            print(f'Host {hostname_from_ip}: {entry.time_string}')
            self.__print_entry_info(entry, entry_info, session_start_time)

            # Keep on processing elements for as long as each entry is within the session timeout of the previous one.
            session_end_time = session_start_time + self._session_timeout
            while session_log_entries and session_log_entries[0].time <= session_end_time:
                entry = session_log_entries.popleft()
                session_end_time = entry.time + self._session_timeout
                entry_info = session_info.parse_log_entry(entry)
                if entry_info:
                    self.__print_entry_info(entry, entry_info, session_start_time)

            # If we ended because we timed out, put the remaining log entries back on the heap.
            if session_log_entries:
                heappush(heap, (session_log_entries[0].time, session_host_ip, session_log_entries))

    def run_summary(self, log_entries: List[LogEntry]) -> None:
        """
        Look at the list of log entries in summary mode.

        All the information for each host_ip are printed out together, though they are still broken into sessions when
        the user pauses for too long.
        """
        previous_host_ip: Optional[IPv4Address] = None
        entries_by_host_ip = self.__group_log_entries_by_host_ip(log_entries)

        # Look at the host ips in standard order.
        for session_host_ip in sorted(entries_by_host_ip):
            hostname_from_ip = self.__get_hostname_from_ip(session_host_ip)
            session_log_entries = entries_by_host_ip[session_host_ip]
            while session_log_entries:
                # If the first entry has no information, it doesn't start a session
                entry = session_log_entries.popleft()
                session_info = self._session_info_generator.create()
                entry_info = session_info.parse_log_entry(entry)
                if not entry_info:
                    continue

                # Start a new session
                session_start_time = entry.time
                if previous_host_ip:
                    char = '-' if previous_host_ip == session_host_ip else '*'
                    print(f'\n{char * 10}\n')
                previous_host_ip = session_host_ip

                print(f'Host {hostname_from_ip}: {entry.time_string}')
                self.__print_entry_info(entry, entry_info, session_start_time)

                # Keep on printing session information for as long as we have not reached a timeout.
                session_end_time = session_start_time + self._session_timeout
                while session_log_entries and session_log_entries[0].time <= session_end_time:
                    entry = session_log_entries.popleft()
                    session_end_time = entry.time + self._session_timeout
                    entry_info = session_info.parse_log_entry(entry)
                    if entry_info:
                        self.__print_entry_info(entry, entry_info, session_start_time)

    def show_slugs(self, log_entries: List[LogEntry]) -> None:
        entries_by_host_ip = self.__group_log_entries_by_host_ip(log_entries)

        # Look at the host ips in standard order.
        for session_host_ip, session_log_entries in entries_by_host_ip.items():
            session_info = self._session_info_generator.create()
            for entry in session_log_entries:
                session_info.parse_log_entry(entry)

        def show_info(name: str, info: Dict[str, Slug.Info]) -> None:
            result = ', '.join(
                # Use ~ as a non-breaking space for textwrap.  We replace it with a space, below
                (slug + '~[OBSOLETE]') if info[slug].flags.is_obsolete() else slug
                for slug in sorted(info, key=str.lower)
            )
            output = textwrap.fill(result, 100, initial_indent=f'{name} slugs: ', subsequent_indent='    ')
            print(output.replace('~', ' '))
        show_info("Search", SessionInfo.all_search_slugs())
        print()
        show_info("Columns", SessionInfo.all_column_slugs())

    def run_realtime(self, log_entries: Iterator[LogEntry]) -> None:
        """
        Look at the list of log entries in real-time mode.

        Each entry is processed as it is received.  Sessions can be interrupted and then continued to show information
        appearing in other sessions.  Note that log_entries is typically a generator tailing a file.
        """
        live_sessions: Dict[IPv4Address, _LiveSession] = {}
        previous_host_ip: Optional[IPv4Address] = None
        need_host_separator: bool = False
        for entry in log_entries:
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
                entry_info = session_info.parse_log_entry(entry)
                if not entry_info:
                    continue
            else:
                is_just_created_session = True
                session_info = self._session_info_generator.create()
                entry_info = session_info.parse_log_entry(entry)
                if not entry_info:
                    continue
                current_session = _LiveSession(host_ip=entry.host_ip, session_info=session_info,
                                               start_time_string=entry.time_string, start_time=entry.time,
                                               timeout=next_timeout)
                live_sessions[entry.host_ip] = current_session

            # Print out information about this entry.
            if current_session.host_ip != previous_host_ip:
                # If we're at a different host_ip, then reprint a header.  Note that timing out on a session then
                # restarting the same ip will look like a different ip because previous_host_ip is set to None.
                if need_host_separator:
                    print('\n----------\n')
                need_host_separator = True
                previous_host_ip = current_session.host_ip
                hostname_from_ip = self.__get_hostname_from_ip(current_session.host_ip)
                postscript = '' if is_just_created_session else ' CONTINUED'
                print(f'Host {hostname_from_ip}: {current_session.start_time_string}{postscript}')

            self.__print_entry_info(entry, entry_info, current_session.start_time)

    def __group_log_entries_by_host_ip(self, log_entries: Iterable[LogEntry]) -> Dict[IPv4Address, Deque[LogEntry]]:
        """
        Create a dictionary in which the keys are the host ips and the values are a deque of all the log entries for
        that host ip.
        """
        entries_by_host: Dict[IPv4Address, Deque[LogEntry]] = defaultdict(deque)
        for log_entry in log_entries:
            entries_by_host[log_entry.host_ip].append(log_entry)
        return entries_by_host

    def __print_entry_info(self, this_entry: LogEntry, this_entry_info: List[str],
                           session_start_time: datetime.datetime) -> None:
        """Print out the information for a log entry."""
        time_delta = this_entry.time - session_start_time
        print(f'    +{time_delta}: {this_entry_info[0]}')
        for info in this_entry_info[1:]:
            print(f'              {info}')

    def __get_hostname_from_ip(self, ip: IPv4Address) -> str:
        name = self.__get_host_by_address(ip) if self._use_reverse_dns else None
        if name:
            return f'{name} ({ip})'
        else:
            return f'{ip}'

    @staticmethod
    @functools.lru_cache(maxsize=None)
    def __get_host_by_address(ip: IPv4Address) -> Optional[str]:
        """Call to the socket implementation, but it catches errors and caches the results."""
        try:
            name, _, _ = socket.gethostbyaddr(str(ip))
            return name
        except OSError:
            return None
