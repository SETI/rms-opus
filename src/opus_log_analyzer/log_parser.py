"""Grouping log entries into per-host sessions, and rendering them.

This is the generic half of the analyzer: it knows about hosts, sessions and
timeouts, and nothing about the site being analyzed. What an individual request
means is decided by the `AbstractConfiguration` the caller supplies, which is
also what renders the HTML report.

A session is a run of one host's requests with no gap longer than the session
timeout, and one that the configuration reports no icon flags for is discarded
as having done nothing.
"""

from __future__ import annotations

import datetime
import ipaddress
import itertools
import string
import sys
from collections import deque
from collections.abc import Iterator
from ipaddress import IPv4Address
from pathlib import Path
from typing import Any, NamedTuple, TextIO

from opus_log_analyzer.abstract_configuration import (
    AbstractConfiguration,
    AbstractSessionInfo,
    LogId,
)
from opus_log_analyzer.ip_to_host_converter import IpToHostConverter
from opus_log_analyzer.log_entry import LogEntry


class LiveSession(NamedTuple):
    """Used by LogParser.run_realtime to keep track of active session"""

    host_ip: IPv4Address
    session_info: AbstractSessionInfo
    start_time_string: str
    start_time: datetime.datetime
    timeout: datetime.datetime

    def with_timeout(self, timeout: datetime.datetime) -> LiveSession:
        """Return a copy of this session with a new expiry.

        Parameters:
            timeout: When the session should now expire.
        """
        return self._replace(timeout=timeout)


class Entry(NamedTuple):
    """One request within a session, with what the configuration made of it.

    `data` is the lines the report prints for this request, and `opus_url` is
    the site URL it corresponds to, where the configuration recognized one.
    """

    log_entry: LogEntry
    relative_start_time: datetime.timedelta
    data: list[str]
    opus_url: str | None
    id: LogId

    def target_url(self) -> str:
        """The full URL this request asked for."""
        return self.log_entry.url.geturl()


class Session(NamedTuple):
    """One host's uninterrupted run of activity, and what it did.

    `id` is a short base-36 label unique within a run, used to name the session
    in the report.
    """

    host_ip: IPv4Address
    entries: list[Entry]
    session_info: AbstractSessionInfo
    id: str

    def start_time(self) -> datetime.datetime:
        """When the session's first request arrived."""
        return self.entries[0].log_entry.time

    def duration(self) -> datetime.timedelta:
        """How long the session lasted, first request to last."""
        return self.entries[-1].log_entry.time - self.entries[0].log_entry.time

    @property
    def total_time(self) -> datetime.timedelta:
        """How long the session lasted; the same value as `duration`."""
        return self.duration()

    def __hash__(self) -> int:
        """Hash on the session id."""
        return hash(self.id)

    def __eq__(self, other: Any) -> bool:
        """Compare on the session id.

        This does not do what it says: the right-hand side is the builtin `id`
        rather than `other.id`, so the comparison is always False and no session
        equals any other, including itself. `__hash__` is correct, which is what
        makes it damaging -- a set of sessions never de-duplicates.
        """
        # Issue #1464 tracks the fix; log-analyzer behavior is out of scope for
        # this modernization (plan rev 7.14), so it is recorded rather than
        # changed.
        return isinstance(other, Session) and self.id == id  # type: ignore[comparison-overlap]

    def __repr__(self) -> str:
        """Render the session as its id, host and start time."""
        return f'<Session#{self.id} {self.host_ip} @ {self.start_time()}>'


class HostInfo(NamedTuple):
    """One host and its sessions, as the report groups them.

    `name` is the reverse-DNS name where one was found and reverse lookup is
    enabled, otherwise None, in which case the report shows the address.
    """

    ip: IPv4Address
    name: str | None
    sessions: list[Session]

    @property
    def total_time(self) -> datetime.timedelta:
        """The sum of this host's session durations, ignoring the gaps between."""
        return sum((session.duration() for session in self.sessions), datetime.timedelta(0))

    def start_time(self) -> datetime.datetime:
        """When this host's first session began."""
        return self.sessions[0].start_time()


class LogParser:
    """
    Code that reads through the log entries, groups them by host and by session, and prints them out in a nice format.
    """

    _configuration: AbstractConfiguration
    _session_timeout: datetime.timedelta
    _output: TextIO
    _by_ip: bool
    _ignored_ips: list[ipaddress.IPv4Network]
    _ip_to_host_converter: IpToHostConverter
    _id_generator: Iterator[str]

    def __init__(
        self,
        configuration: AbstractConfiguration,
        *,
        session_timeout_minutes: int,
        output: str,
        uses_html: bool,
        by_ip: bool,
        ip_to_host_converter: IpToHostConverter,
        ignored_ips: list[ipaddress.IPv4Network],
        **_: Any,
    ) -> None:
        """Parameters:
        configuration: Decides what each request means and renders the HTML
            report.
        session_timeout_minutes: A gap at least this long ends a session.
        output: Path to write the report to, or empty for standard output.
            Parent directories are created.
        uses_html: Whether to render HTML rather than text.
        by_ip: Whether the text report groups sessions by host. The HTML
            report always groups by host regardless.
        ip_to_host_converter: Supplies reverse-DNS names.
        ignored_ips: Networks whose requests are skipped entirely.
        **_: The rest of the parsed arguments, ignored. The caller passes the
            whole argument namespace.
        """
        self._configuration = configuration
        self._session_timeout = datetime.timedelta(minutes=session_timeout_minutes)
        if output:
            Path(output).parent.mkdir(parents=True, exist_ok=True)
        # Program-lifetime output stream (a file or stdout); not a scoped resource.
        self._output = open(output, 'w') if output else sys.stdout  # noqa: SIM115
        self._uses_html = uses_html
        self._by_ip = by_ip
        self._ignored_ips = ignored_ips
        self._ip_to_host_converter = ip_to_host_converter
        self._id_generator = (f'{self.__base36(value):>04}' for value in itertools.count(1))

    def run_batch(self, log_entries: list[LogEntry]) -> None:
        """Group every entry into sessions and write the whole report.

        Parameters:
            log_entries: The entries to report on. Sorted in place.
        """
        print('Parsing input')
        all_sessions = self.__get_session_list(log_entries, self._uses_html)

        def do_grouping(by_ip: bool) -> list[HostInfo]:
            """Collect the sessions into the report's top-level groups.

            Parameters:
                by_ip: Whether to gather all of a host's sessions under one
                    entry, ordered by host name where known and by address
                    otherwise. When False each session becomes its own entry and
                    they are ordered by start time.

            Returns:
                The groups, in report order.
            """
            if by_ip:
                all_sessions.sort(key=lambda session: (session.host_ip, session.start_time()))
                sessions_list = [
                    list(group)
                    for _, group in itertools.groupby(all_sessions, lambda session: session.host_ip)
                ]
            else:
                all_sessions.sort(key=lambda session: session.start_time())
                sessions_list = [[session] for session in all_sessions]
            host_infos = [
                HostInfo(ip=ip, name=self._ip_to_host_converter.convert(ip), sessions=sessions)
                for sessions in sessions_list
                for ip in [sessions[0].host_ip]
            ]
            if by_ip:
                host_infos.sort(
                    key=lambda host_info: self.__sort_key_from_ip_and_name(
                        host_info.ip, host_info.name
                    )
                )
            return host_infos

        output = self._output
        print(f'Writing file {output.name}')
        if not self._uses_html:
            host_infos = do_grouping(self._by_ip)
            self.__generate_batch_text_output(host_infos)
        else:
            host_infos = do_grouping(by_ip=True)
            self.__generate_batch_html_output(host_infos)

    def run_summary(self, log_entries: list[LogEntry]) -> None:
        """Print out all slugs that have appeared in the text.

        Parameters:
            log_entries: The entries to summarize. Sorted in place.
        """
        all_sessions = self.__get_session_list(log_entries, uses_html=False)
        self._configuration.show_summary(all_sessions, self._output)

    def run_realtime(self, log_entries: Iterator[LogEntry]) -> None:
        """
        Look at the list of log entries in real-time mode.

        Each entry is processed as it is received.  Sessions can be interrupted and then continued to show information
        appearing in other sessions.  Note that log_entries is typically a generator tailing a file.

        Parameters:
            log_entries: The entries as they arrive. This does not return while
                the iterator keeps yielding, which for a tailed file is forever.
        """
        output = self._output
        live_sessions: dict[IPv4Address, LiveSession] = {}
        previous_host_ip: IPv4Address | None = None
        need_host_separator: bool = False
        for entry in log_entries:
            if any(entry.host_ip in ipNetwork for ipNetwork in self._ignored_ips):
                continue

            current_time = entry.time
            next_timeout = current_time + self._session_timeout

            # Delete all sessions that have expired, even it it matches this one.
            expired_sessions = {
                session_info
                for session_info in live_sessions.values()
                if session_info.timeout < current_time
            }
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
                entry_info, _ = session_info.parse_log_entry(entry, LogId(0))
                if not entry_info:
                    continue
            else:
                is_just_created_session = True
                session_info = self._configuration.create_session_info()
                entry_info, _ = session_info.parse_log_entry(entry, LogId(0))
                if not entry_info:
                    continue
                current_session = LiveSession(
                    host_ip=entry.host_ip,
                    session_info=session_info,
                    start_time_string=entry.time_string,
                    start_time=entry.time,
                    timeout=next_timeout,
                )
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
                print(
                    f'Host {hostname_from_ip}: {current_session.start_time_string}{postscript}',
                    file=output,
                )

            self.__print_entry_info(entry, entry_info, current_session.start_time)

    def __get_session_list(self, log_entries: list[LogEntry], uses_html: bool) -> list[Session]:
        """Group the log entries into parsed sessions.

        Parameters:
            log_entries: The entries to group. Sorted in place by host and time.
            uses_html: Passed to the configuration, which renders differently
                for the HTML report.

        Returns:
            One session per run of a host's requests with no gap longer than the
            session timeout, excluding requests from an ignored network and
            sessions the configuration reports no icon flags for.
        """

        sessions: list[Session] = []
        log_entries.sort(key=lambda entry: (entry.host_ip, entry.time))
        for session_host_ip, session_log_entries_iter in itertools.groupby(
            log_entries, lambda entry: entry.host_ip
        ):
            if any(session_host_ip in ipNetwork for ipNetwork in self._ignored_ips):
                continue
            session_log_entries = deque(session_log_entries_iter)
            while session_log_entries:
                # If the first entry has no information, it doesn't start a session
                entry = session_log_entries.popleft()
                session_info = self._configuration.create_session_info(uses_html=uses_html)
                entry_id = LogId(1)
                entry_info, opus_url = session_info.parse_log_entry(entry, entry_id)
                if not entry_info:
                    continue

                session_start_time = entry.time

                def create_session_entry(
                    log_entry: LogEntry,
                    entry_info: list[str],
                    opus_url: str | None,
                    log_id: LogId,
                    session_start_time: datetime.datetime = session_start_time,
                ) -> Entry:
                    """Build one session entry, timed relative to the session start.

                    Parameters:
                        log_entry: The request.
                        entry_info: The report lines the configuration produced.
                        opus_url: The site URL the request corresponds to, if any.
                        log_id: The request's position within the session.
                        session_start_time: Bound as a default argument so each
                            closure keeps the start time of the session it was
                            created in.

                    Returns:
                        The entry.
                    """
                    return Entry(
                        log_entry=log_entry,
                        relative_start_time=log_entry.time - session_start_time,
                        data=entry_info,
                        opus_url=opus_url,
                        id=log_id,
                    )

                current_session_entries = [
                    create_session_entry(entry, entry_info, opus_url, entry_id)
                ]

                # Keep on grabbing entries for as long as we have not reached a timeout.
                session_end_time = session_start_time + self._session_timeout
                while session_log_entries and session_log_entries[0].time <= session_end_time:
                    entry = session_log_entries.popleft()
                    session_end_time = entry.time + self._session_timeout
                    entry_id = LogId(entry_id + 1)
                    entry_info, opus_url = session_info.parse_log_entry(entry, entry_id)
                    if entry_info:
                        current_session_entries.append(
                            create_session_entry(entry, entry_info, opus_url, entry_id)
                        )

                if session_info.get_icon_flags():
                    # We ignore sessions that don't actually do anything.
                    sessions.append(
                        Session(
                            host_ip=session_host_ip,
                            entries=current_session_entries,
                            session_info=session_info,
                            id=next(self._id_generator),
                        )
                    )

        return sessions

    def __generate_batch_text_output(self, host_infos: list[HostInfo]) -> None:
        """Write the text report.

        Parameters:
            host_infos: The groups, in report order.
        """
        output = self._output
        assert not self._uses_html
        for i, host_info in enumerate(host_infos):
            if i > 0:
                print('\n----------\n', file=output)
            hostname_from_ip = (
                f'{host_info.name, ({host_info.ip})}' if host_info.name else str(host_info.ip)
            )
            for j, session in enumerate(host_info.sessions):
                if j > 0:
                    print(file=output)
                entries = session.entries
                print(f'Host {hostname_from_ip}: {entries[0].log_entry.time_string}', file=output)
                for entry in entries:
                    self.__print_entry_info(entry.log_entry, entry.data, session.start_time())

    def __generate_batch_html_output(self, host_infos_by_ip: list[HostInfo]) -> None:
        """Write the HTML report, through the configuration's generator.

        Parameters:
            host_infos_by_ip: The groups, in report order.
        """
        batch_html_generator = self._configuration.create_batch_html_generator(host_infos_by_ip)
        batch_html_generator.generate_output(self._output)

    def __print_entry_info(
        self,
        this_entry: LogEntry,
        this_entry_info: list[str],
        session_start_time: datetime.datetime,
    ) -> None:
        """Print out the information for a log entry.

        Parameters:
            this_entry: The request.
            this_entry_info: The report lines for it; the first is printed
                against the elapsed time and the rest are indented under it.
            session_start_time: The time the elapsed time is measured from.
        """
        duration = this_entry.time - session_start_time
        print(f'    +{duration}: {this_entry_info[0]}', file=self._output)
        for info in this_entry_info[1:]:
            print(f'              {info}', file=self._output)

    def __get_hostname_from_ip(self, ip: IPv4Address) -> str:
        """Render an address for the report, with its host name where known.

        Parameters:
            ip: The address.

        Returns:
            `name (address)` if reverse lookup found a name, otherwise the
            address alone.
        """
        name = self._ip_to_host_converter.convert(ip)
        if name:
            return f'{name} ({ip})'
        else:
            return f'{ip}'

    @staticmethod
    def __sort_key_from_ip_and_name(ip: IPv4Address, name: str | None) -> Any:
        """Order hosts by domain name, then by address.

        Named hosts sort before unnamed ones, and are ordered by their name
        read right to left, so hosts in the same domain group together.

        Parameters:
            ip: The host's address.
            name: Its reverse-DNS name, or None.

        Returns:
            A sort key. Two keys are comparable only if the addresses in them
            are the same IP version, so sorting a mix of IPv4 and IPv6 unnamed
            hosts raises `TypeError`.
        """
        if name:
            return 1, tuple(reversed(name.lower().split('.')))
        else:
            return 2, ip

    ALPHABET36 = string.digits + string.ascii_lowercase

    @classmethod
    def __base36(cls, value: int) -> str:
        """Render a positive integer in lower-case base 36.

        Parameters:
            value: The number to render.

        Returns:
            Its base-36 digits, most significant first.

        Raises:
            AssertionError: If the value is not positive.
        """
        result: list[str] = []
        assert value > 0
        while value > 0:
            value, modulus = divmod(value, 36)
            result.append(cls.ALPHABET36[modulus])
        return ''.join(reversed(result))
