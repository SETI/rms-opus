import collections
import textwrap
from collections.abc import Sequence
from typing import Any, ClassVar, TextIO, cast

from opus_log_analyzer.abstract_configuration import AbstractConfiguration
from opus_log_analyzer.ip_to_host_converter import IpToHostConverter
from opus_log_analyzer.log_entry import LogEntry
from opus_log_analyzer.log_parser import HostInfo, Session
from opus_log_analyzer.opus import slug
from opus_log_analyzer.opus.html_generator import HtmlGenerator
from opus_log_analyzer.opus.query_handler import MetadataSlugInfo, QueryHandler
from opus_log_analyzer.opus.session_info import SessionInfo


class Configuration(AbstractConfiguration):
    """
    A generator class for creating a SessionInfo.
    """
    _slug_map: slug.ToInfoMap
    _default_column_slug_info: MetadataSlugInfo
    _api_host_url: str
    _debug_show_all: bool
    _elide_session_info: bool
    _ip_to_host_converter: IpToHostConverter
    _sessions_relative_directory: str | None
    _manifests: Sequence[str]

    _sessionless_downloads: list[tuple[str, LogEntry]]

    DEFAULT_COLUMN_INFO: ClassVar[list[str]] = ['opusid', 'instrument', 'planet', 'target',
                                                'time1', 'observationduration']

    def __init__(self, *, api_host_url: str, debug_show_all: bool, no_sessions: bool,
                 ip_to_host_converter: IpToHostConverter,
                 sessions_relative_directory: str | None,
                 manifests: Sequence[str],
                 **_: Any):
        self._slug_map = slug.ToInfoMap(api_host_url)
        self._default_column_slug_info = QueryHandler.get_metadata_slug_info(self.DEFAULT_COLUMN_INFO, self._slug_map)
        self._api_host_url = api_host_url
        self._debug_show_all = debug_show_all
        self._elide_session_info = no_sessions
        self._ip_to_host_converter = ip_to_host_converter
        self._sessions_relative_directory = sessions_relative_directory
        self._sessionless_downloads = []
        self._manifests = manifests

    def create_session_info(self, uses_html: bool = False) -> 'SessionInfo':
        """Create a new SessionInfo"""
        return SessionInfo(self._slug_map, self._default_column_slug_info, self._debug_show_all, uses_html,
                           self._sessionless_downloads)

    def create_batch_html_generator(self, host_infos_by_ip: list[HostInfo]) -> HtmlGenerator:
        return HtmlGenerator(self, host_infos_by_ip)

    @property
    def api_host_url(self) -> str:
        return self._api_host_url

    @property
    def elide_session_info(self) -> bool:
        return self._elide_session_info

    @property
    def sessions_relative_directory(self) -> str | None:
        return self._sessions_relative_directory

    @property
    def sessionless_downloads(self) -> list[tuple[str, LogEntry]]:
        return self._sessionless_downloads

    @property
    def manifests(self) -> Sequence[str]:
        return self._manifests

    def show_summary(self, sessions: list[Session], output: TextIO) -> None:
        all_info: dict[str, dict[str, bool]] = collections.defaultdict(dict)
        for session in sessions:
            session_info = cast(SessionInfo, session.session_info)
            search_slug_info, column_slug_info, _ = session_info.get_slug_info()
            for info_type, slug_and_flags in (("search", search_slug_info), ("column", column_slug_info)):
                for slug_name, is_obsolete in slug_and_flags:
                    all_info[info_type][slug_name] = is_obsolete

        def show_info(info_type: str) -> None:
            result = ', '.join(
                # Use ~ as a non-breaking space for textwrap.  We replace it with a space, below
                (slug + '~[OBSOLETE]') if all_info[slug] else slug
                for slug in sorted(all_info[info_type], key=str.lower))
            wrapped = textwrap.fill(result, 100,
                                    initial_indent=f'{info_type.title()} slugs: ', subsequent_indent='    ')
            print(wrapped.replace('~', ' '), file=output)

        show_info('search')
        print('', file=output)
        show_info('column')
