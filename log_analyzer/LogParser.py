import datetime
import functools
import itertools
import os
import socket
import textwrap
from collections import defaultdict, deque
from ipaddress import IPv4Address
from typing import List, Iterator, Dict, NamedTuple, Optional, Deque, Tuple, Iterable, TextIO

import django
from django.template.loader import get_template

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
    search_slug_list: List[Tuple[str, bool]]
    column_slug_list: List[Tuple[str, bool]]
    id: str

    def start_time(self) -> datetime.datetime:
        return self.entries[0].log_entry.time

    def duration(self) -> datetime.timedelta:
        return self.entries[-1].log_entry.time - self.entries[0].log_entry.time

    def slug_info(self) -> Iterable[Tuple[str, List[Tuple[str, bool]]]]:
        return ("search", self.search_slug_list), ("column", self.column_slug_list)


class HostInfo(NamedTuple):
    ip: IPv4Address
    name: Optional[str]
    sessions: List[Session]

    def hostname(self) -> str:
        return f'{self.name} ({self.ip})' if self.name else str(self.ip)

    def total_time(self) -> datetime.timedelta:
        return sum((session.duration() for session in self.sessions), datetime.timedelta(0))


class LogParser:
    """
    Code that reads through the log entries, groups them by host and by session, and prints them out in a nice format.
    """
    _session_info_generator: SessionInfoGenerator
    _uses_reverse_dns: bool
    _session_timeout: datetime.timedelta
    _output: TextIO
    _uses_local: bool
    _id_generator: Iterator[str]

    def __init__(self, session_info_generator: SessionInfoGenerator, uses_reverse_dns: bool,
                 session_timeout_minutes: int, output: TextIO, api_host_url: str, uses_html: bool,
                 uses_local: bool, **_):
        self._session_info_generator = session_info_generator
        self._uses_reverse_dns = uses_reverse_dns
        self._session_timeout = datetime.timedelta(minutes=session_timeout_minutes)
        self._output = output
        self._api_host_url = api_host_url
        self._uses_html = uses_html
        self._uses_local = uses_local
        self._id_generator = (f'{value:X}' for value in itertools.count(100))

    def run_batch_by_time(self, log_entries: List[LogEntry]) -> None:
        """
        Look at the list of log entries in batch mode.

        The logs are aggregated into sessions, and each complete session is printed out in order of the start
        of the session.
        """
        all_sessions = self.__get_session_list(log_entries, self._uses_html)
        all_sessions.sort(key=lambda session: (session.start_time(), session.host_ip))

        host_infos = [HostInfo(ip=session.host_ip,
                               name=self.__get_reverse_dns_from_ip(session.host_ip),  # may be None
                               sessions=[session])
                      for session in all_sessions]

        self.__generate_batch_output(host_infos)

    def run_batch_by_ip(self, log_entries: List[LogEntry]) -> None:
        """
         Look at the list of log entries in batch mode.

         The logs are aggregated into sessions, and the sessions are aggregated by host_ip.  The sessions are printed
         out sorted by host_ip and then by session start time.
         """
        all_sessions = self.__get_session_list(log_entries, self._uses_html)
        all_sessions.sort(key=lambda session: (session.host_ip, session.start_time()))

        host_infos: List[HostInfo] = []
        while all_sessions:
            this_host = all_sessions[0].host_ip
            next_host_start = next((i for i in range(len(all_sessions)) if all_sessions[i].host_ip != this_host),
                                   len(all_sessions))
            sessions = all_sessions[0:next_host_start]
            all_sessions = all_sessions[next_host_start:]
            host_infos.append(HostInfo(ip=this_host,
                                       name=self.__get_reverse_dns_from_ip(this_host),  # may be None
                                       sessions=sessions))
        self.__generate_batch_output(host_infos)

    def show_slugs(self, log_entries: List[LogEntry]) -> None:
        """Print out all slugs that have appeared in the text."""
        output = self._output
        all_sessions = self.__get_session_list(log_entries, False)

        def show_info(info_type: str) -> None:
            all_info: Dict[str, bool] = {}
            for session in all_sessions:
                slug_list = session.column_slug_list if info_type == 'column' else session.search_slug_list
                for slug, is_obsolete in slug_list:
                    all_info[slug] = is_obsolete
            result = ', '.join(
                # Use ~ as a non-breaking space for textwrap.  We replace it with a space, below
                (slug + '~[OBSOLETE]') if all_info[slug] else slug
                for slug in sorted(all_info, key=str.lower))

            wrapped = textwrap.fill(result, 100,
                                    initial_indent=f'{info_type.title()} slugs: ', subsequent_indent='    ')
            print(wrapped.replace('~', ' '), file=output)
        show_info("search")
        print('', file=output)
        show_info("column")

    def run_realtime(self, log_entries: Iterator[LogEntry]) -> None:
        """
        Look at the list of log entries in real-time mode.

        Each entry is processed as it is received.  Sessions can be interrupted and then continued to show information
        appearing in other sessions.  Note that log_entries is typically a generator tailing a file.
        """
        output = self._output
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
                entry_info, _ = session_info.parse_log_entry(entry)
                if not entry_info:
                    continue
            else:
                is_just_created_session = True
                session_info = self._session_info_generator.create()
                entry_info, _ = session_info.parse_log_entry(entry)
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
                    print('\n----------\n', file=output)
                need_host_separator = True
                previous_host_ip = current_session.host_ip
                hostname_from_ip = self.__get_hostname_from_ip(current_session.host_ip)
                postscript = '' if is_just_created_session else ' CONTINUED'
                print(f'Host {hostname_from_ip}: {current_session.start_time_string}{postscript}', file=output)

            self.__print_entry_info(entry, entry_info, current_session.start_time)

    def __get_session_list(self, log_entries: List[LogEntry], uses_html: bool) -> List[Session]:
        """Group the log entries into parsed sessions."""

        # First, group all the logs by host
        entries_by_host_ip: Dict[IPv4Address, Deque[LogEntry]] = defaultdict(deque)
        for log_entry in log_entries:
            entries_by_host_ip[log_entry.host_ip].append(log_entry)

        sessions: List[Session] = []
        for session_host_ip in sorted(entries_by_host_ip):
            session_log_entries = entries_by_host_ip[session_host_ip]
            while session_log_entries:
                # If the first entry has no information, it doesn't start a session
                entry = session_log_entries.popleft()
                session_info = self._session_info_generator.create(uses_html=uses_html)
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

                def slug_info(info: Dict[str, Slug.Info]) -> List[Tuple[str, bool]]:
                    return [(slug, info[slug].flags.is_obsolete()) for slug in sorted(info, key=str.lower)]

                sessions.append(Session(host_ip=session_host_ip,
                                        entries=current_session_entries,
                                        search_slug_list=slug_info(session_info.session_search_slugs),
                                        column_slug_list=slug_info(session_info.session_column_slugs),
                                        id=next(self._id_generator)))
        return sessions

    def __generate_batch_output(self, host_infos: List[HostInfo]) -> None:
        output = self._output
        print(f'Writing file {output.name}')
        if self._uses_html:
            os.environ.setdefault("DJANGO_SETTINGS_MODULE", "DjangoSettings")
            django.setup()
            summary_template = get_template('summary')
            summary_context = {'host_infos': host_infos,
                               'api_host_url': self._api_host_url,
                               'uses_local': self._uses_local}
            print(summary_template.render(summary_context), file=output)
        else:
            for i, host_info in enumerate(host_infos):
                if i > 0:
                    print('\n----------\n', file=output)
                hostname_from_ip = f"{host_info.name, ({host_info.ip})}" if host_info.name else str(host_info.ip)
                for j, session in enumerate(host_info.sessions):
                    if j > 0:
                        print(file=output)
                    entries = session.entries
                    print(f'Host {hostname_from_ip}: {entries[0].log_entry.time_string}', file=output)
                    for entry in entries:
                        self.__print_entry_info(entry.log_entry, entry.data, session.start_time())

    def __print_entry_info(self, this_entry: LogEntry, this_entry_info: List[str],
                           session_start_time: datetime.datetime) -> None:
        """Print out the information for a log entry."""
        duration = this_entry.time - session_start_time
        print(f'    +{duration}: {this_entry_info[0]}', file=self._output)
        for info in this_entry_info[1:]:
            print(f'              {info}', file=self._output)

    def __get_hostname_from_ip(self, ip: IPv4Address) -> str:
        name = self.__get_host_by_address(ip) if self._uses_reverse_dns else None
        if name:
            return f'{name} ({ip})'
        else:
            return f'{ip}'

    def __get_reverse_dns_from_ip(self, ip: IPv4Address) -> Optional[str]:
        name = self.__get_host_by_address(ip) if self._uses_reverse_dns else None
        return name

    @staticmethod
    @functools.lru_cache(maxsize=None)
    def __get_host_by_address(ip: IPv4Address) -> Optional[str]:
        """Call to the socket implementation, but it catches errors and caches the results."""
        try:
            name, _, _ = socket.gethostbyaddr(str(ip))
            return name
        except OSError:
            return None
