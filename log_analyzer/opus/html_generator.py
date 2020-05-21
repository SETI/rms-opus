import collections
import datetime
import itertools
import math
import statistics
from enum import Flag
from ipaddress import IPv4Address
from operator import methodcaller, itemgetter, attrgetter
from typing import List, Dict, TextIO, Tuple, Sequence, Optional, Any, Callable, Iterable, cast,  TypeVar

from abstract_configuration import AbstractBatchHtmlGenerator
from jinga_environment import JINJA_ENVIRONMENT
from log_entry import LogEntry
from log_parser import HostInfo, Session
from . import slug
from .configuration_flags import IconFlags, InfoFlags

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .configuration import Configuration
    from .session_info import SessionInfo

T = TypeVar('T')


class HtmlGenerator(AbstractBatchHtmlGenerator):
    _configuration: 'Configuration'
    _host_infos_by_ip:  List[HostInfo]
    _sessions: List[Session]
    _ip_to_host_name: Dict[IPv4Address, str]
    _flag_name_to_flag: Dict[str, IconFlags]

    def __init__(self, configuration: 'Configuration', host_infos_by_ip: List[HostInfo]):
        self._configuration = configuration
        self._host_infos_by_ip = host_infos_by_ip
        self._sessions = [session for host_info in host_infos_by_ip for session in host_info.sessions]
        self._ip_to_host_name = {host_info.ip: host_info.name for host_info in host_infos_by_ip if host_info.name}
        self._flag_name_to_flag = {x.name: x for x in IconFlags}

    def generate_output(self, output: TextIO) -> None:
        template = JINJA_ENVIRONMENT.get_template('log_analysis.html')
        output_generator = template.generate(context=self, host_infos_by_ip=self._host_infos_by_ip)
        lines = (line.strip()
                 for chunks in output_generator
                 for line in chunks.split('\n') if line)
        for line in lines:
            output.write(line)
            output.write("\n")

    #
    #  All public methods beyond this point are callbacks made by the Jinga2 template.
    #

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
    def session_count(self) -> int:
        """Returns the number of sessions"""
        return len(self._sessions)

    def flag_name_to_flag(self, name: str) -> IconFlags:
        """Convert a flag name into the actual icon flag with that name """
        return self._flag_name_to_flag[name]

    def get_host_infos_by_date(self) -> List[Tuple[datetime.date, List[Session]]]:
        host_infos_by_time = sorted(self._sessions, key=lambda session: session.start_time(), reverse=True)
        host_infos_by_date = [(date, list(values))
                              for date, values in itertools.groupby(host_infos_by_time,
                                                                    lambda host_info: host_info.start_time().date())]
        return host_infos_by_date

    def generate_ordered_search(self) -> Sequence[Tuple[str, int, List[List[Session]]]]:
        return self.__collect_sessions_by_info(lambda si: si.get_search_names())

    def generate_ordered_metadata(self) -> Sequence[Tuple[str, int, List[List[Session]]]]:
        return self.__collect_sessions_by_info(lambda si: si.get_metadata_names())

    def generate_ordered_info_flags(self) -> Sequence[Tuple[Flag, int, List[List[Session]]]]:
        return self.__collect_sessions_by_info(lambda si: si.get_info_flags().as_list(), InfoFlags)

    def generate_ordered_sort_lists(self) -> Sequence[Tuple[Tuple[str], int, List[List[Session]]]]:
        return self.__collect_sessions_by_info(methodcaller("get_sort_list_names"))

    def generate_ordered_help_files(self) -> Sequence[Tuple[str, int, List[List[Session]]]]:
        return self.__collect_sessions_by_info(methodcaller("get_help_files"))

    def generate_ordered_product_types(self) -> Sequence[Tuple[str, int, List[List[Session]]]]:
        return self.__collect_sessions_by_info(methodcaller("get_product_types"))

    def generate_ordered_unmatched_widgets(self) -> Sequence[Tuple[slug.Family, int, List[List[Session]]]]:
        temp = self.__collect_sessions_by_info(methodcaller("get_unmatched_widgets"))
        return temp

    def get_product_types_count(self) -> int:
        return sum(self.__to_session_info(session).get_product_types_count() for session in self._sessions)

    def generate_ordered_download_files(self) -> \
            Sequence[Tuple[str, int, List[Tuple[Optional[Session], Optional[LogEntry], int]]]]:
        info_dict: Dict[str, List[Tuple[Optional[Session], Optional[LogEntry], int]]] = collections.defaultdict(list)
        for session in self._sessions:
            session_info = self.__to_session_info(session)
            for filename, size in session_info.get_downloads():
                info_dict[filename].append((session, None, size))
        for filename, entry in self._configuration.sessionless_downloads:
            info_dict[filename].append((None, entry, entry.size or 0))

        result: List[Tuple[str, int, List[Tuple[Optional[Session], Optional[LogEntry], int]]]] = []
        for filename, sessions_and_sizes in info_dict.items():
            sessions_and_sizes.sort(key=itemgetter(2), reverse=True)
            total_size = sum(size for _, _, size in sessions_and_sizes)
            result.append((filename, total_size, sessions_and_sizes))
        result.sort(key=itemgetter(1), reverse=True)
        return result

    def get_download_statistics(self) -> Dict[str, Any]:
        data = [size for _, size, _ in self.generate_ordered_download_files()]
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

    def __collect_sessions_by_info(self,
                                   func: Callable[['SessionInfo'], Iterable[T]],
                                   fixed: Optional[Iterable[T]] = None) -> List[Tuple[T, int, List[List[Session]]]]:
        info_dict: Dict[T, List[Session]] = collections.defaultdict(list)
        for session in self._sessions:
            session_info = self.__to_session_info(session)
            for item in func(session_info):
                info_dict[item].append(session)
        if fixed:
            result = [(item, len(info_dict[item]), self.__group_sessions_by_host_id(info_dict[item]))
                      for item in fixed]
        else:
            result = [(item, len(sessions), self.__group_sessions_by_host_id(sessions))
                      for item, sessions in info_dict.items()]
            # Sort the outer list secondarily by whatever item we're looking at, and primarily by the count of that item
            result.sort(key=itemgetter(0))
            result.sort(key=itemgetter(1), reverse=True)
        return result

    def __group_sessions_by_host_id(self, sessions: List[Session]) -> List[List[Session]]:
        sessions.sort(key=lambda session: session.start_time())
        sessions.sort(key=lambda session: session.host_ip)
        grouped_sessions = [list(sessions) for _, sessions in itertools.groupby(sessions, attrgetter("host_ip"))]

        # At this point, groups are sorted by host_ip, and within each group, they are sorted by start time
        # But we want the groups sorted by length, and within length, we want them in our standard sort order
        def group_session_sorter(sessions: List[Session]) -> Tuple[int, Any]:
            host_ip = sessions[0].host_ip
            name = self._ip_to_host_name.get(host_ip)
            return -len(sessions), self.__sort_key_from_ip_and_name(host_ip, name)

        grouped_sessions.sort(key=group_session_sorter)
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
