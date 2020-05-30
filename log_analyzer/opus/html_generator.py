import collections
import datetime
import itertools
import math
import re
import statistics
from ipaddress import IPv4Address
from operator import itemgetter, attrgetter
from os.path import dirname
from pathlib import Path

from typing import List, Dict, TextIO, Tuple, Sequence, Optional, Any, Callable, NamedTuple
from typing import Iterable, cast, TypeVar, Mapping, Set, Iterator
from typing import TYPE_CHECKING

from abstract_configuration import AbstractBatchHtmlGenerator, LogId
from jinga_environment import JINJA_ENVIRONMENT
from log_entry import LogEntry
from log_parser import HostInfo, Session
from . import slug
from .configuration_flags import IconFlags, InfoFlags

if TYPE_CHECKING:
    from .configuration import Configuration
    from .session_info import SessionInfo

T = TypeVar('T')

HtmlStatisticsOutput = Tuple[List[Tuple[T, int, List[List[Session]]]], Mapping[Tuple[T, Session], Set['LogId']]]


class HtmlGenerator(AbstractBatchHtmlGenerator):
    _configuration: 'Configuration'
    _host_infos_by_ip: List[HostInfo]
    _sessions: List[Session]
    _ip_to_host_name: Dict[IPv4Address, str]
    _flag_name_to_flag: Dict[str, IconFlags]
    _sessions_relative_directory: Optional[str]

    def __init__(self, configuration: 'Configuration', host_infos_by_ip: List[HostInfo]):
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

    def generate_output(self, output: TextIO) -> None:
        template = JINJA_ENVIRONMENT.get_template('log_analysis.html')
        output_generator: Iterable[str] = template.generate(context=self, host_infos_by_ip=self._host_infos_by_ip)
        lines = (line.strip()
                 for chunks in output_generator
                 for line in chunks.split('\n') if line)
        directory = (f'{dirname(output.name)}/{self._sessions_relative_directory}'
                     if self._sessions_relative_directory else None)
        current_output = output
        file_output = None
        for line in lines:
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

    def generate_ordered_info_flags(self) -> HtmlStatisticsOutput[InfoFlags]:
        def get_info_flags(si: 'SessionInfo') -> Iterable[Tuple[InfoFlags, Set['LogId']]]:
            info_flags = si.get_info_flags_usage()
            yield from info_flags.items()
            if InfoFlags.PERFORMED_SEARCH not in info_flags:
                yield InfoFlags.DID_NOT_PERFORM_SEARCH, set()

        return self.__collect_sessions_by_info(get_info_flags, cast(Iterable[InfoFlags], InfoFlags))

    def generate_ordered_sort_lists(self) -> HtmlStatisticsOutput[Tuple[str, ...]]:
        return self.__collect_sessions_by_info(lambda si: si.get_sort_list_names_usage())

    def generate_ordered_help_files(self) -> HtmlStatisticsOutput[str]:
        return self.__collect_sessions_by_info(lambda si: si.get_help_files_usage().items())

    def generate_ordered_product_types(self) -> HtmlStatisticsOutput[str]:
        # Counts work a little bit different for product types.  So if there are n different log entries for
        # a specific product type, we want that session to appear n times.
        def get_info(si: 'SessionInfo') -> Iterator[Tuple[str, Set['LogId']]]:
            return ((name, ids)
                    for name, ids in si.get_product_types_usage().items()
                    for _ in range(len(ids)))

        return self.__collect_sessions_by_info(get_info)

    def generate_ordered_unmatched_widgets(self) -> HtmlStatisticsOutput[slug.Family]:
        return self.__collect_sessions_by_info(lambda si: si.get_unmatched_widgets_usage())

    def get_product_types_count(self) -> int:
        return sum(self.__to_session_info(session).get_product_types_usage_count() for session in self._sessions)

    class FakeSession(NamedTuple):
        log_entry: LogEntry
        id: str = ''

        @property
        def host_ip(self) -> IPv4Address:
            return self.log_entry.host_ip

        def start_time(self) -> datetime.datetime:
            return self.log_entry.time

    def generate_ordered_download_files(self) -> Tuple[List[Tuple[str, int, List[Tuple[Session, int]]]], Dict[Tuple[str, Session], Set['LogId']]]:
        info_dict: Dict[str, List[Session]] = collections.defaultdict(list)
        mapping_dict: Dict[Tuple[str, Session], Set['LogId']] = collections.defaultdict(set)
        sizing_dict: Dict[Any, int] = collections.defaultdict(int)

        for session in self._sessions:
            session_info = self.__to_session_info(session)

            for filename, ([size], ids) in session_info.get_sessioned_downloads_usage().items():
                info_dict[filename].append(session)
                mapping_dict[filename, session].update(ids)
                sizing_dict[filename, session] += size

        for filename, entry in self._configuration.sessionless_downloads:
            session = cast(Session, HtmlGenerator.FakeSession(entry))
            info_dict[filename].append(session)
            sizing_dict[filename, session] += (entry.size or 0)

        def get_sessions_for_filename(filename: str) -> Tuple[str, int, List[Tuple[Session, int]]]:
            sessions = info_dict[filename]
            sessions_and_sizes = [(session, sizing_dict[filename, session]) for session in sessions]
            total_size = sum(size for _, size in sessions_and_sizes)
            sessions_and_sizes.sort(key=lambda ss: ss[0].start_time())
            return filename, total_size, sessions_and_sizes
        
        result: List[Tuple[str, int, List[Tuple[Session, int]]]] = [get_sessions_for_filename(filename) for filename in info_dict.keys()]
        return result, mapping_dict

    def get_download_statistics(self) -> Dict[str, Any]:
        result, _ = self.generate_ordered_download_files()
        data = [size for _, size, _ in result]
        mean = int(statistics.mean(data))
        gmean = int(math.exp(statistics.mean(map(math.log, data))))
        median = int(statistics.median(data))
        return dict(data=data, count=len(data), sum=sum(data), mean=mean, gmean=gmean, median=median)

    def get_session_statistics(self) -> Dict[str, Any]:
        data = [session.total_time for session in self._sessions]
        mean = statistics.mean(x.total_seconds() for x in data)
        median = statistics.median(x.total_seconds() for x in data)
        return dict(data=data,
                    count=len(data),
                    sum=sum(data, datetime.timedelta(0)),
                    mean=datetime.timedelta(seconds=round(mean)),
                    median=datetime.timedelta(seconds=round(median)))

    @staticmethod
    def run_length_encode(values: Sequence[T]) -> List[Tuple[T, int]]:
        """Given a list with consecutive duplicate elements, converts it into a run-list encoded list"""
        temp = [(value, len(list(iterable))) for value, iterable in itertools.groupby(values)]
        return temp

    def debug(self, arg: Any) -> None:
        """Useful for debugging.  The Jinga template can print out information."""
        print(arg)

    def __collect_sessions_by_info(self, func: Callable[['SessionInfo'], Iterable[Tuple[T, Iterable['LogId']]]],
                                   fixed: Optional[Iterable[T]] = None) -> HtmlStatisticsOutput[T]:
        info_dict: Dict[T, List[Session]] = collections.defaultdict(list)
        mapping_dict: Dict[Tuple[T, Session], Set['LogId']] = collections.defaultdict(set)
        for session in self._sessions:
            session_info = self.__to_session_info(session)
            for item, ids in func(session_info):
                info_dict[item].append(session)
                mapping_dict[item, session].update(ids)

        if fixed:
            result = [(item, len(info_dict[item]), self.__group_sessions_by_host_id(info_dict[item]))
                      for item in fixed]
        else:
            result = [(item, len(sessions), self.__group_sessions_by_host_id(sessions))
                      for item, sessions in info_dict.items()]
            # Sort the outer list secondarily by whatever item we're looking at, and primarily by the count of that item
            result.sort(key=itemgetter(0))
            result.sort(key=itemgetter(1), reverse=True)
        return result, mapping_dict

    def __group_sessions_by_host_id(self, sessions: List[Session]) -> List[List[Session]]:
        sessions.sort(key=lambda session: session.start_time())
        sessions.sort(key=lambda session: session.host_ip)
        grouped_sessions = [list(sessions) for _, sessions in itertools.groupby(sessions, attrgetter("host_ip"))]

        # At this point, groups are sorted by host_ip, and within each group, they are sorted by start time
        # But we want the groups sorted by length, and within length, we want them in our standard sort order
        def group_session_sort_key(sessions: List[Session]) -> Tuple[int, Any]:
            host_ip = sessions[0].host_ip
            name = self._ip_to_host_name.get(host_ip)
            return -len(sessions), self.__sort_key_from_ip_and_name(host_ip, name)

        grouped_sessions.sort(key=group_session_sort_key)
        return grouped_sessions

    @staticmethod
    def __to_session_info(session: Session) -> 'SessionInfo':
        """Helper function that casts session.session_info from AbstractSession to SessionInfo"""
        return cast('SessionInfo', session.session_info)

    @staticmethod
    def __sort_key_from_ip_and_name(ip: IPv4Address, name: Optional[str]) -> Any:
        if name:
            return 1, tuple(reversed(name.lower().split('.')))
        else:
            return 2, ip
