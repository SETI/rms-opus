from __future__ import annotations

import collections
import datetime
import itertools
import math
import re
import statistics
import string
from ipaddress import IPv4Address
from operator import itemgetter, attrgetter
from os.path import dirname
from pathlib import Path

from typing import List, Dict, TextIO, Tuple, Sequence, Optional, Any, Callable, NamedTuple
from typing import Iterable, cast, TypeVar, Mapping, Set, Iterator
from typing import TYPE_CHECKING

from abstract_configuration import AbstractBatchHtmlGenerator
from jinga_environment import JINJA_ENVIRONMENT
from log_entry import LogEntry
from log_parser import HostInfo, Session, Entry
from manifest import ManifestStatus
from .configuration_flags import IconFlags, Action

if TYPE_CHECKING:
    from .configuration import Configuration
    from .session_info import SessionInfo, LogMarker

T = TypeVar('T')

HtmlStatisticsOutput = Tuple[List[Tuple[T, int, List[List[Session]]]], Mapping[T, str]]


class HtmlGenerator(AbstractBatchHtmlGenerator):
    _configuration: Configuration
    _host_infos_by_ip: List[HostInfo]
    _sessions: List[Session]
    _ip_to_host_name: Dict[IPv4Address, str]
    _flag_name_to_flag: Dict[str, IconFlags]
    _sessions_relative_directory: Optional[str]

    _log_entry_to_classes: Dict[Tuple[Session, LogMarker], Set[str]]

    _class_name_generator: Iterator[str]

    def __init__(self, configuration: Configuration, host_infos_by_ip: List[HostInfo]):
        self._configuration = configuration
        self._host_infos_by_ip = host_infos_by_ip
        self._sessions = [session for host_info in host_infos_by_ip for session in host_info.sessions]
        self._ip_to_host_name = {host_info.ip: host_info.name for host_info in host_infos_by_ip if host_info.name}
        self._flag_name_to_flag = {x.name: x for x in IconFlags}
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
        template = JINJA_ENVIRONMENT.get_template('log_analysis.html')
        output_generator: Iterable[str] = template.generate(context=self, host_infos_by_ip=self._host_infos_by_ip)

        def get_lines():
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
                    current_output = file_output = open(file_name, "w")
                    continue
                else:
                    line = match.group(2)
            elif line.startswith(">>>>"):
                match = re.match(r"[>]+ ([\w\d]+) (.*)", line)
                assert match
                if directory:
                    assert current_output == file_output and file_output and not file_output.closed
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
    def sessions_relative_directory(self) -> Optional[str]:
        return self._sessions_relative_directory

    @property
    def api_host_url(self) -> str:
        """Returns the api_host_url, indicating the base url to use for showing results"""
        return self._configuration.api_host_url

    @property
    def ip_to_host_name(self) -> Dict[IPv4Address, str]:
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

    def log_entry_to_classes(self, session: Session, log_entry: Entry, line_number: int) -> Sequence[str]:
        # They don't need to be sorted, but it looks nicer.
        log_entries = self._log_entry_to_classes[session, log_entry.id]
        line_entries = self._log_entry_to_classes[session, (log_entry.id, line_number)]
        return sorted(log_entries.union(line_entries))

    def flag_name_to_flag(self, name: str) -> IconFlags:
        """Convert a flag name into the actual icon flag with that name """
        return self._flag_name_to_flag[name]

    def get_host_infos_by_date(self) -> List[Tuple[datetime.date, List[Session]]]:
        host_infos_by_time = sorted(self._sessions, key=lambda session: session.start_time(), reverse=True)
        date_iterator = itertools.groupby(host_infos_by_time, lambda host_info: host_info.start_time().date())
        return [(date, list(values)) for date, values in date_iterator]

    def generate_ordered_search(self) -> HtmlStatisticsOutput[str]:
        return self.__collect_sessions_by_info(lambda si: si.get_search_names_usage().items())

    def generate_ordered_metadata(self) -> HtmlStatisticsOutput[str]:
        return self.__collect_sessions_by_info(lambda si: si.get_metadata_names_usage())

    def generate_ordered_info_flags(self) -> HtmlStatisticsOutput[Action]:
        def get_info_flags(si: SessionInfo) -> Iterable[Tuple[Action, Set[LogMarker]]]:
            info_flags = si.get_info_flags_usage()
            yield from info_flags.items()
            if Action.PERFORMED_SEARCH not in info_flags:
                yield Action.DID_NOT_PERFORM_SEARCH, set()

        return self.__collect_sessions_by_info(get_info_flags, cast(Iterable[Action], Action))

    def generate_ordered_sort_lists(self) -> HtmlStatisticsOutput[Tuple[str, ...]]:
        return self.__collect_sessions_by_info(lambda si: si.get_sort_list_names_usage())

    def generate_ordered_help_files(self) -> HtmlStatisticsOutput[str]:
        return self.__collect_sessions_by_info(lambda si: si.get_help_files_usage().items())

    def generate_ordered_product_types(self) -> HtmlStatisticsOutput[str]:
        # Counts work a little bit different for product types.  So if there are n different log entries for
        # a specific product type, we want that session to appear n times.
        def get_info(si: SessionInfo) -> Iterator[Tuple[str, Set[LogMarker]]]:
            return ((name, ids)
                    for name, ids in si.get_product_types_usage().items()
                    for _ in range(len(ids)))

        return self.__collect_sessions_by_info(get_info)

    def generate_ordered_unmatched_widgets(self) -> HtmlStatisticsOutput[str]:
        return self.__collect_sessions_by_info(lambda si: si.get_unmatched_widgets_usage())

    def get_product_types_count(self) -> int:
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
            return self.log_entry.host_ip

        def start_time(self) -> datetime.datetime:
            return self.log_entry.time

    def generate_ordered_download_files(self) -> Tuple[List[Tuple[str, int, List[Tuple[Session, int]]]],
                                                       Dict[str, str]]:
        value_to_sessions: Dict[str, List[Session]] = collections.defaultdict(list)
        sizing_dict: Dict[Tuple[str, Session], int] = collections.defaultdict(int)
        value_to_class: Dict[str, str] = collections.defaultdict(lambda: next(self._class_name_generator))

        for session in self._sessions:
            session_info = self.__to_session_info(session)

            for filename, ([size], log_ids) in session_info.get_sessioned_downloads_usage().items():
                value_to_sessions[filename].append(session)
                sizing_dict[filename, session] += size
                for log_id in log_ids:
                    class_for_file = value_to_class[filename]
                    self._log_entry_to_classes[session, log_id].add(class_for_file)

        host_ip_to_fake_session: Dict[Tuple[IPv4Address, str], Session] = {}
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

        def get_sessions_for_filename(filename: str) -> Tuple[str, int, List[Tuple[Session, int]]]:
            sessions = value_to_sessions[filename]
            sessions_and_sizes = [(session, sizing_dict[filename, session]) for session in sessions]
            total_size = sum(size for _, size in sessions_and_sizes)
            sessions_and_sizes.sort(key=lambda ss: ss[0].start_time())
            return filename, total_size, sessions_and_sizes
        
        result = [get_sessions_for_filename(filename) for filename in value_to_sessions.keys()]
        return result, value_to_class

    def get_session_statistics(self) -> Dict[str, Any]:
        data = [session.total_time for session in self._sessions]
        mean = statistics.mean(x.total_seconds() for x in data)
        median = statistics.median(x.total_seconds() for x in data)
        return dict(data=data,
                    count=len(data),
                    sum=sum(data, datetime.timedelta(0)),
                    mean=datetime.timedelta(seconds=round(mean)),
                    median=datetime.timedelta(seconds=round(median)))

    def get_logged_download_statistics(self) -> Dict[str, Any]:
        sizing_dict: Dict[Tuple[str, IPv4Address], int] = collections.defaultdict(int)

        for session in self._sessions:
            session_info = self.__to_session_info(session)
            for filename, ([size], log_ids) in session_info.get_sessioned_downloads_usage().items():
                sizing_dict[filename, session.host_ip] += size

        for filename, entry in self._configuration.sessionless_downloads:
            sizing_dict[filename, entry.host_ip] += (entry.size or 0)

        data = list(sizing_dict.values())
        return self.__create_statistics(data)

    def get_manifest_download_statistics(self) -> Dict[str, Any]:
        result = ManifestStatus.get_statistics(self._configuration.manifests)
        result['statistics'] = self.__create_statistics(result['data'])
        return result

    @staticmethod
    def __create_statistics(data:Sequence[int]) -> Dict[str, Any]:
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

        result = dict(data=data, count=len(data), sum=sum(data), zeros = data.count(0),
                      mean=mean, gmean=gmean, median=median)
        return result

    @staticmethod
    def run_length_encode(values: Sequence[T]) -> List[Tuple[T, int]]:
        """Given a list with consecutive duplicate elements, converts it into a run-list encoded list"""
        temp = [(value, len(list(iterable))) for value, iterable in itertools.groupby(values)]
        return temp

    def debug(self, arg: Any) -> None:
        """Useful for debugging.  The Jinga template can print out information."""
        print(arg)

    def __collect_sessions_by_info(self, func: Callable[[SessionInfo], Iterable[Tuple[T, Iterable[LogMarker]]]],
                                   fixed: Optional[Iterable[T]] = None) -> HtmlStatisticsOutput[T]:
        value_to_sessions: Dict[T, List[Session]] = collections.defaultdict(list)
        value_to_class: Dict[T, str] = collections.defaultdict(lambda: next(self._class_name_generator))
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

    def __group_sessions_by_host_id(self, sessions: List[Session]) -> List[List[Session]]:
        sessions.sort(key=lambda session: session.start_time())
        sessions.sort(key=lambda session: session.host_ip)
        grouped_sessions = [list(sessions) for _, sessions in itertools.groupby(sessions, attrgetter('host_ip'))]

        # At this point, groups are sorted by host_ip, and within each group, they are sorted by start time
        # But we want the groups sorted by length, and within length, we want them in our standard sort order
        def group_session_sort_key(sessions: List[Session]) -> Tuple[int, Any]:
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
    def __sort_key_from_ip_and_name(ip: IPv4Address, name: Optional[str]) -> Any:
        if name:
            return 1, tuple(reversed(name.lower().split('.')))
        else:
            return 2, ip

    def __generate_class_names(self) -> Iterator[str]:
        alphabet = string.digits + string.ascii_lowercase
        for length in itertools.count(2):
            for letters in itertools.product(alphabet, repeat=length):
                yield 'opus-' + ''.join(letters)
