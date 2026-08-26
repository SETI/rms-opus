"""Rendering the OPUS session report as HTML.

The Jinja template drives this class rather than the other way round: everything
public below `generate_output` is a callback the template calls to ask for one
part of the report. The `generate_ordered_*` family all have the same shape --
they return the values seen across the run, each with the sessions that produced
it and a CSS class name -- so the template can render a left-hand panel that
highlights the matching log lines when a value is clicked.

`generate_output` also splits the rendered stream back into per-session files
where the configuration asks for them, keyed on markers the template emits.
"""
from __future__ import annotations

import collections
import datetime
import itertools
import math
import re
import statistics
import string
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from ipaddress import IPv4Address
from operator import attrgetter, itemgetter
from os.path import dirname
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    NamedTuple,
    TextIO,
    TypeVar,
    cast,
)

from opus_log_analyzer.abstract_configuration import AbstractBatchHtmlGenerator
from opus_log_analyzer.jinga_environment import JINJA_ENVIRONMENT
from opus_log_analyzer.log_entry import LogEntry
from opus_log_analyzer.log_parser import Entry, HostInfo, Session
from opus_log_analyzer.manifest import ManifestStatus
from opus_log_analyzer.opus.configuration_flags import Action, IconFlags

if TYPE_CHECKING:
    from opus_log_analyzer.opus.configuration import Configuration
    from opus_log_analyzer.opus.session_info import LogMarker, SessionInfo

T = TypeVar('T')

HtmlStatisticsOutput = tuple[list[tuple[T, int, list[list[Session]]]], Mapping[T, str]]


class HtmlGenerator(AbstractBatchHtmlGenerator):
    """Renders one run's sessions into the HTML report."""

    _configuration: Configuration
    _host_infos_by_ip: list[HostInfo]
    _sessions: list[Session]
    _ip_to_host_name: dict[IPv4Address, str]
    _flag_name_to_flag: dict[str, IconFlags]
    _sessions_relative_directory: str | None

    _log_entry_to_classes: dict[tuple[Session, LogMarker], set[str]]

    _class_name_generator: Iterator[str]

    def __init__(self, configuration: Configuration,
                 host_infos_by_ip: list[HostInfo]) -> None:
        """Parameters:
        configuration: The OPUS configuration this run used, consulted for
            the report's options and for the downloads that belong to no
            session.
        host_infos_by_ip: The hosts and their sessions, in report order.

        Raises:
            Exception: If the configuration's sessions directory is an absolute
                path. It is resolved against the report's own directory, so an
                absolute path would write outside it.
        """
        self._configuration = configuration
        self._host_infos_by_ip = host_infos_by_ip
        self._sessions = [session for host_info in host_infos_by_ip for session in host_info.sessions]
        self._ip_to_host_name = {host_info.ip: host_info.name for host_info in host_infos_by_ip if host_info.name}
        # __members__ rather than a comprehension over the class: a Flag
        # member's `.name` is `str | None` (a composite value has no name),
        # while __members__ is keyed by name by construction. Verified to
        # produce an identical mapping, in the same order, for IconFlags.
        self._flag_name_to_flag = dict(IconFlags.__members__)
        sessions_relative_directory = self._configuration.sessions_relative_directory
        if sessions_relative_directory:
            if sessions_relative_directory.startswith('/'):
                raise Exception('Sessions directory must not be an absolute path')
            if not sessions_relative_directory.endswith('/'):
                sessions_relative_directory += '/'
        self._sessions_relative_directory = sessions_relative_directory
        self._log_entry_to_classes = collections.defaultdict(set)
        self._class_name_generator = self.__generate_class_names()

    def generate_output(self, output: TextIO) -> None:
        """Render the report, splitting per-session pages out as they appear.

        The template marks the start and end of each session's detail with a
        line the renderer recognizes; where the configuration asked for a
        sessions directory, everything between those markers is written to its
        own file there instead of into the main report.

        Parameters:
            output: The main report file. Its directory is what the sessions
                directory is resolved against.
        """
        template = JINJA_ENVIRONMENT.get_template('log_analysis.html')
        output_generator: Iterable[str] = template.generate(context=self, host_infos_by_ip=self._host_infos_by_ip)

        def get_lines() -> Iterator[str]:
            """Yield the rendered template one non-blank, stripped line at a time.

            Yields:
                Each line of the rendered output, with surrounding whitespace
                removed and empty lines dropped. The template renders in chunks
                that need not end at a line boundary, so a partial line is held
                until the rest of it arrives.

            Raises:
                AssertionError: If the render ends mid-line.
            """
            # An iterator that breaks the results of the output_generator into lines.
            # Its job is complicated in that chunks aren't guarenteed to end with '\n'.
            leftover_text = ''
            for chunk in itertools.chain(output_generator, ['\n']):
                # The chunk may be a Markup.  We make sure to convert it to a string first.
                lines = (leftover_text + str(chunk)).split('\n')
                # line[-1] contains everything that comes after the final newline,
                # so hold it until we get more input.
                leftover_text = lines.pop()
                # Return all non-blank lines
                yield from filter(None, (line.strip() for line in lines))
            assert leftover_text == ''

        directory = (f'{dirname(output.name)}/{self._sessions_relative_directory}'
                     if self._sessions_relative_directory else None)
        if directory:
            print(f'Writing sessions to {directory}')
        current_output = output
        file_output = None

        for line in get_lines():
            if line.startswith("<<<<"):
                match = re.match(r"[<]+ ([\w\d]+) (.*)", line)
                assert match
                if directory:
                    assert file_output is None or file_output.closed
                    file_name = directory + match.group(1) + ".html"
                    Path(file_name).parent.mkdir(parents=True, exist_ok=True)
                    # Handle spans loop iterations: opened here, closed in the
                    # matching ">>>>" branch below, so a `with` block does not fit.
                    current_output = file_output = open(file_name, "w")  # noqa: SIM115
                    continue
                else:
                    line = match.group(2)
            elif line.startswith(">>>>"):
                match = re.match(r"[>]+ ([\w\d]+) (.*)", line)
                assert match
                if directory:
                    assert current_output == file_output
                    assert file_output
                    assert not file_output.closed
                    file_output.close()
                    current_output = output
                    continue
                else:
                    line = match.group(2)
            current_output.write(line)
            current_output.write("\n")

    #
    #  All public methods beyond this point are callbacks made by the Jinga2 template.
    #

    @property
    def sessions_relative_directory(self) -> str | None:
        """The directory per-session pages are written to, or None for one file.

        Relative to the report's own directory, and with a trailing separator.
        """
        return self._sessions_relative_directory

    @property
    def api_host_url(self) -> str:
        """Returns the api_host_url, indicating the base url to use for showing results"""
        return self._configuration.api_host_url

    @property
    def ip_to_host_name(self) -> dict[IPv4Address, str]:
        """Returns a dictionary that converts ips to hosts"""
        return self._ip_to_host_name

    @property
    def elide_session_details(self) -> bool:
        """True if we are to elide session details, and are only interested in the left panel"""
        return self._configuration.elide_session_info

    @property
    def sessions(self) -> Sequence[Session]:
        """Returns the list of all sessions"""
        return self._sessions

    @property
    def session_count(self) -> int:
        """Returns the number of sessions"""
        return len(self._sessions)

    def log_entry_to_classes(self, session: Session, log_entry: Entry,
                             line_number: int) -> Sequence[str]:
        """The CSS classes one report line carries, for the left panel's highlighting.

        Parameters:
            session: The session the line belongs to.
            log_entry: The request the line describes.
            line_number: Which of that request's report lines this is.

        Returns:
            The classes registered against the whole request and against this
            line specifically, sorted for readability.
        """
        # They don't need to be sorted, but it looks nicer.
        log_entries = self._log_entry_to_classes[session, log_entry.id]
        line_entries = self._log_entry_to_classes[session, (log_entry.id, line_number)]
        return sorted(log_entries.union(line_entries))

    def flag_name_to_flag(self, name: str) -> IconFlags:
        """Convert a flag name into the actual icon flag with that name """
        return self._flag_name_to_flag[name]

    def get_host_infos_by_date(self) -> list[tuple[datetime.date, list[Session]]]:
        """Group every session by the date it started on.

        Returns:
            One entry per date, most recent first, each holding that date's
            sessions ordered from latest to earliest.
        """
        host_infos_by_time = sorted(self._sessions, key=lambda session: session.start_time(), reverse=True)
        date_iterator = itertools.groupby(host_infos_by_time, lambda host_info: host_info.start_time().date())
        return [(date, list(values)) for date, values in date_iterator]

    def generate_ordered_search(self) -> HtmlStatisticsOutput[str]:
        """The search fields used across the run, most used first.

        Returns:
            The value/session/class triple described on `__collect_sessions_by_info`.
        """
        return self.__collect_sessions_by_info(lambda si: si.get_search_names_usage().items())

    def generate_ordered_metadata(self) -> HtmlStatisticsOutput[str]:
        """The metadata columns selected across the run, most used first.

        Returns:
            The value/session/class triple described on `__collect_sessions_by_info`.
        """
        return self.__collect_sessions_by_info(lambda si: si.get_metadata_names_usage())

    def generate_ordered_info_flags(self) -> HtmlStatisticsOutput[Action]:
        """Every action, with the sessions that performed it.

        Every member of `Action` appears, including those no session performed,
        so the report's action list is the same shape from run to run.

        Returns:
            The value/session/class triple described on `__collect_sessions_by_info`,
            in `Action` declaration order rather than by count.
        """

        def get_info_flags(si: SessionInfo) -> Iterable[tuple[Action, set[LogMarker]]]:
            """Yield a session's actions, adding the "did not search" marker.

            Parameters:
                si: The session.

            Yields:
                Each action the session performed with the report lines that
                show it, plus `DID_NOT_PERFORM_SEARCH` when the session
                performed no search.
            """
            info_flags = si.get_info_flags_usage()
            yield from info_flags.items()
            if Action.PERFORMED_SEARCH not in info_flags:
                yield Action.DID_NOT_PERFORM_SEARCH, set()

        return self.__collect_sessions_by_info(get_info_flags, cast(Iterable[Action], Action))

    def generate_ordered_sort_lists(self) -> HtmlStatisticsOutput[tuple[str, ...]]:
        """The sort orders used across the run, most used first.

        Returns:
            The value/session/class triple described on `__collect_sessions_by_info`.
        """
        return self.__collect_sessions_by_info(lambda si: si.get_sort_list_names_usage())

    def generate_ordered_help_files(self) -> HtmlStatisticsOutput[str]:
        """The help pages viewed across the run, most viewed first.

        Returns:
            The value/session/class triple described on `__collect_sessions_by_info`.
        """
        return self.__collect_sessions_by_info(lambda si: si.get_help_files_usage().items())

    def generate_ordered_product_types(self) -> HtmlStatisticsOutput[str]:
        """The product types downloaded across the run, most downloaded first.

        A session that requested one product type in several separate log
        entries is counted once per entry, unlike the other members of this
        family, which count each session once.

        Returns:
            The value/session/class triple described on `__collect_sessions_by_info`.
        """
        # Counts work a little bit different for product types.  So if there are n different log entries for
        # a specific product type, we want that session to appear n times.
        def get_info(si: SessionInfo) -> Iterator[tuple[str, set[LogMarker]]]:
            """Yield a session's product types, once per log entry that used each.

            Parameters:
                si: The session.

            Yields:
                The product type and the report lines that show it, repeated as
                many times as there are such lines.
            """
            return ((name, ids)
                    for name, ids in si.get_product_types_usage().items()
                    for _ in range(len(ids)))

        return self.__collect_sessions_by_info(get_info)

    def generate_ordered_unmatched_widgets(self) -> HtmlStatisticsOutput[str]:
        """The widget slugs the slug map did not recognize, most seen first.

        Returns:
            The value/session/class triple described on `__collect_sessions_by_info`.
        """
        return self.__collect_sessions_by_info(lambda si: si.get_unmatched_widgets_usage())

    def get_product_types_count(self) -> int:
        """How many product-type downloads the run's sessions made in total.

        Returns:
            The sum over sessions of that session's product-type usage count.
        """
        return sum(self.__to_session_info(session).get_product_types_usage_count() for session in self._sessions)

    class FakeSession(NamedTuple):
        """
        A Fake session has just enough methods and properties to pretend to be a session.  It has enough information
        to be used by downloads, and then passed to the Jinja code generator.  It is recognized as being fake by
        not having an actual id.
        """
        log_entry: LogEntry
        id: str = ''

        @property
        def host_ip(self) -> IPv4Address:
            """The address that made the download request."""
            return self.log_entry.host_ip

        def start_time(self) -> datetime.datetime:
            """When the download request was made."""
            return self.log_entry.time

    def generate_ordered_download_files(self) -> tuple[list[tuple[str, int, list[tuple[Session, int]]]],
                                                       dict[str, str]]:
        """Every downloaded file, with the sessions that fetched it and its size.

        Downloads that belong to no session -- a direct fetch of an archive URL
        -- are attributed to a `FakeSession` standing in for the request, one
        per address and file name, timed at the earliest such request.

        Returns:
            One entry per file name: the name, the total bytes across all
            sessions, and each session with the bytes it fetched, ordered by
            session start time; plus the file-name-to-CSS-class map the
            template highlights with.
        """
        value_to_sessions: dict[str, list[Session]] = collections.defaultdict(list)
        sizing_dict: dict[tuple[str, Session], int] = collections.defaultdict(int)
        value_to_class: dict[str, str] = collections.defaultdict(lambda: next(self._class_name_generator))

        for session in self._sessions:
            session_info = self.__to_session_info(session)

            for filename, ([size], log_ids) in session_info.get_sessioned_downloads_usage().items():
                value_to_sessions[filename].append(session)
                sizing_dict[filename, session] += size
                for log_id in log_ids:
                    class_for_file = value_to_class[filename]
                    self._log_entry_to_classes[session, log_id].add(class_for_file)

        host_ip_to_fake_session: dict[tuple[IPv4Address, str], Session] = {}
        for filename, entry in self._configuration.sessionless_downloads:
            opt_session = host_ip_to_fake_session.get((entry.host_ip, filename))
            if opt_session is None or opt_session.start_time() > entry.time:
                host_ip_to_fake_session[entry.host_ip, filename] = cast(Session, self.FakeSession(entry))

        for filename, entry in self._configuration.sessionless_downloads:
            # The following statement is a bald-faced lie.  Fortunately Python doesn't actually do type checking.
            session = host_ip_to_fake_session[entry.host_ip, filename]
            value_to_sessions[filename].append(session)
            sizing_dict[filename, session] += (entry.size or 0)
            value_to_class.get(filename)  # creates a entry, if one doesn't already exit

        def get_sessions_for_filename(filename: str) -> tuple[str, int,
                                                              list[tuple[Session, int]]]:
            """Gather one file's sessions and sizes.

            Parameters:
                filename: The downloaded file.

            Returns:
                The name, the total bytes across every session that fetched it,
                and each session with its own byte count, ordered by session
                start time.
            """
            sessions = value_to_sessions[filename]
            sessions_and_sizes = [(session, sizing_dict[filename, session]) for session in sessions]
            total_size = sum(size for _, size in sessions_and_sizes)
            sessions_and_sizes.sort(key=lambda ss: ss[0].start_time())
            return filename, total_size, sessions_and_sizes

        result = [get_sessions_for_filename(filename) for filename in value_to_sessions]
        return result, value_to_class

    def get_session_statistics(self) -> dict[str, Any]:
        """How long the run's sessions lasted.

        Returns:
            The template context: the durations themselves, their count, sum,
            mean and median, the last two rounded to whole seconds.

        Raises:
            statistics.StatisticsError: If the run produced no sessions.
        """
        data = [session.total_time for session in self._sessions]
        mean = statistics.mean(x.total_seconds() for x in data)
        median = statistics.median(x.total_seconds() for x in data)
        return {'data': data,
                    'count': len(data),
                    'sum': sum(data, datetime.timedelta(0)),
                    'mean': datetime.timedelta(seconds=round(mean)),
                    'median': datetime.timedelta(seconds=round(median))}

    def get_logged_download_statistics(self) -> dict[str, Any]:
        """How much each host downloaded of each file, across the whole run.

        Sessioned and sessionless downloads are both counted, keyed by file name
        and address rather than by session, so a host's repeat visits sum
        together.

        Returns:
            The template context for one statistics block: the values
            themselves, their count, sum, zero count, arithmetic mean, geometric
            mean and median.
        """
        sizing_dict: dict[tuple[str, IPv4Address], int] = collections.defaultdict(int)

        for session in self._sessions:
            session_info = self.__to_session_info(session)
            for filename, ([size], _log_ids) in session_info.get_sessioned_downloads_usage().items():
                sizing_dict[filename, session.host_ip] += size

        for filename, entry in self._configuration.sessionless_downloads:
            sizing_dict[filename, entry.host_ip] += (entry.size or 0)

        data = list(sizing_dict.values())
        return self.__create_statistics(data)

    def get_manifest_download_statistics(self) -> dict[str, Any]:
        """What the run's manifests say was downloaded.

        Returns:
            The manifest summary tables, plus a `statistics` entry holding the
            per-manifest byte totals summarized the same way the download
            statistics are.
        """
        result = ManifestStatus.get_statistics(self._configuration.manifests)
        result['statistics'] = self.__create_statistics(result['data'])
        return result

    @staticmethod
    def __create_statistics(data: Sequence[int]) -> dict[str, Any]:
        """Summarize a list of byte counts for the report.

        Zeros are excluded from the returned data and counted separately, and
        the geometric mean ignores them, since it is undefined at zero.

        Parameters:
            data: The byte counts.

        Returns:
            The template context for one statistics block: the values
            themselves, their count, sum, zero count, arithmetic mean, geometric
            mean and median.
        """
        if data:
            mean = int(statistics.mean(data))
            try:
                gmean = int(math.exp(statistics.mean(map(math.log, filter(None, data)))))
            except statistics.StatisticsError:
                gmean = 0
            median = int(statistics.median(data))
        else:
            mean = gmean = median = 0
        data = list(filter(None, data))
        if data:
            gmean = int(math.exp(statistics.mean(map(math.log, filter(None, data)))))

        result = {'data': data, 'count': len(data), 'sum': sum(data), 'zeros': data.count(0),
                      'mean': mean, 'gmean': gmean, 'median': median}
        return result

    @staticmethod
    def run_length_encode(values: Sequence[T]) -> list[tuple[T, int]]:
        """Given a list with consecutive duplicate elements, converts it into a run-list encoded list"""
        temp = [(value, len(list(iterable))) for value, iterable in itertools.groupby(values)]
        return temp

    def debug(self, arg: Any) -> None:
        """Useful for debugging.  The Jinga template can print out information."""
        print(arg)

    def __collect_sessions_by_info(self, func: Callable[[SessionInfo], Iterable[tuple[T, Iterable[LogMarker]]]],
                                   fixed: Iterable[T] | None = None) -> HtmlStatisticsOutput[T]:
        """Collect one kind of value across every session, for the left panel.

        Every value is also given a CSS class, and that class is registered
        against each report line the value appeared on, which is what lets the
        template highlight the lines when the value is clicked.

        Parameters:
            func: Yields a session's values, each with the report lines showing
                it.
            fixed: The values to report, in this order, rather than only those
                seen. When omitted, the values seen are reported most-used
                first, ties broken by the value itself.

        Returns:
            One entry per value: the value, how many sessions produced it, and
            those sessions grouped by host; plus the value-to-class map.
        """
        value_to_sessions: dict[T, list[Session]] = collections.defaultdict(list)
        value_to_class: dict[T, str] = collections.defaultdict(lambda: next(self._class_name_generator))
        for session in self._sessions:
            session_info = self.__to_session_info(session)
            for item, log_ids in func(session_info):
                value_to_sessions[item].append(session)
                for log_id in log_ids:
                    self._log_entry_to_classes[session, log_id].add(value_to_class[item])

        if fixed:
            result = [(item, len(value_to_sessions[item]), self.__group_sessions_by_host_id(value_to_sessions[item]))
                      for item in fixed]
        else:
            result = [(item, len(sessions), self.__group_sessions_by_host_id(sessions))
                      for item, sessions in value_to_sessions.items()]
            # Sort the outer list secondarily by whatever we're looking at, and primarily by the count of that item.
            result.sort(key=itemgetter(0))
            result.sort(key=itemgetter(1), reverse=True)
        # Bug in pycharm.  The following return result is exactly the type it's supposed to be.
        # noinspection PyTypeChecker

        return result, value_to_class

    def __group_sessions_by_host_id(self, sessions: list[Session]) -> list[list[Session]]:
        """Group sessions by host, busiest host first.

        Parameters:
            sessions: The sessions to group. Sorted in place.

        Returns:
            One list per host, each ordered by session start time, the lists
            ordered by how many sessions they hold and then by host name where
            known and address otherwise.
        """
        sessions.sort(key=lambda session: session.start_time())
        sessions.sort(key=lambda session: session.host_ip)
        grouped_sessions = [list(sessions) for _, sessions in itertools.groupby(sessions, attrgetter('host_ip'))]

        # At this point, groups are sorted by host_ip, and within each group, they are sorted by start time
        # But we want the groups sorted by length, and within length, we want them in our standard sort order
        def group_session_sort_key(sessions: list[Session]) -> tuple[int, Any]:
            """Order host groups by size, then in the report's standard host order.

            Parameters:
                sessions: One host's sessions.

            Returns:
                A sort key.
            """
            host_ip = sessions[0].host_ip
            name = self._ip_to_host_name.get(host_ip)
            return -len(sessions), self.__sort_key_from_ip_and_name(host_ip, name)

        grouped_sessions.sort(key=group_session_sort_key)
        return grouped_sessions

    @staticmethod
    def __to_session_info(session: Session) -> SessionInfo:
        """Helper function that casts session.session_info from AbstractSession to SessionInfo"""
        return cast('SessionInfo', session.session_info)

    @staticmethod
    def __sort_key_from_ip_and_name(ip: IPv4Address, name: str | None) -> Any:
        """Order hosts by domain name, then by address.

        Named hosts sort before unnamed ones, and are ordered by their name read
        right to left, so hosts in the same domain group together.

        Parameters:
            ip: The host's address.
            name: Its reverse-DNS name, or None.

        Returns:
            A sort key. Two keys are comparable only if the addresses in them
            are the same IP version, so sorting a mix of IPv4 and IPv6 unnamed
            hosts raises `TypeError`. See issue #1463.
        """
        if name:
            return 1, tuple(reversed(name.lower().split('.')))
        else:
            return 2, ip

    def __generate_class_names(self) -> Iterator[str]:
        """Yield distinct CSS class names for the report's highlighting.

        Yields:
            `opus-` followed by a base-36 string, two characters long and then
            longer, without end.
        """
        alphabet = string.digits + string.ascii_lowercase
        for length in itertools.count(2):
            for letters in itertools.product(alphabet, repeat=length):
                yield 'opus-' + ''.join(letters)
