"""The log analyzer's configuration for OPUS.

`Configuration` is the class `--configuration` names by default.  It reads the OPUS
field definitions, holds the settings the OPUS-specific code needs for a run, and
builds the per-session parser and the HTML generator the analyzer asks it for.
"""
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
        """Read the OPUS field definitions and keep the settings for one run.

        Parameters:
            api_host_url: Base URL of the OPUS server.  Its field definitions are
                read here, and the report's links to the site are built on it.
            debug_show_all: The hidden `--xxshowall` debugging setting, handed to
                each session this creates.
            no_sessions: Whether to leave the detailed per-session information out
                of the report.
            ip_to_host_converter: The converter from host address to host name.  It
                is stored, but nothing in this class reads it.
            sessions_relative_directory: Directory the per-session pages are written
                into, taken relative to the report, or None to keep every session in
                the report itself.
            manifests: Paths of the download manifests to summarize.
            **_: The rest of the parsed arguments, ignored.  The caller passes the
                whole argument namespace.
        """
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
        """Create the generator that renders a batch run.

        Parameters:
            host_infos_by_ip: The run's sessions, grouped by host.

        Returns:
            An `HtmlGenerator` that reads its settings from this configuration.
        """
        return HtmlGenerator(self, host_infos_by_ip)

    @property
    def api_host_url(self) -> str:
        """Base URL of the OPUS server; the links to the site are built on it."""
        return self._api_host_url

    @property
    def elide_session_info(self) -> bool:
        """Whether the report leaves out the detailed per-session information."""
        return self._elide_session_info

    @property
    def sessions_relative_directory(self) -> str | None:
        """Directory for the per-session pages, relative to the report, or None."""
        return self._sessions_relative_directory

    @property
    def sessionless_downloads(self) -> list[tuple[str, LogEntry]]:
        """The `/downloads/` requests seen, as file name and log entry.

        The list is shared with every session this configuration creates, and grows
        as they parse their entries.
        """
        return self._sessionless_downloads

    @property
    def manifests(self) -> Sequence[str]:
        """Paths of the download manifests to summarize."""
        return self._manifests

    def show_summary(self, sessions: list[Session], output: TextIO) -> None:
        """Implement the `--summary` operation for OPUS.

        Gathers the search slugs and the column slugs the sessions used and prints
        them: the search slugs, a blank line, then the column slugs.

        The gathering step unpacks three values from the two that `get_slug_info`
        returns, so nothing is printed for a run that has any session at all.
        Log-analyzer behavior is out of scope for this modernization (plan rev
        7.14), so this is recorded rather than fixed; issue #1451 records that
        `--summary` already fails before reaching this method.

        Parameters:
            sessions: The sessions to summarize.
            output: The stream to write to.

        Raises:
            ValueError: `sessions` is not empty, as described above.
        """
        all_info: dict[str, dict[str, bool]] = collections.defaultdict(dict)
        for session in sessions:
            session_info = cast(SessionInfo, session.session_info)
            # get_slug_info returns a pair, and this unpacks three: the
            # ValueError that raises is issue #1465, and it is what makes
            # --summary unusable once the earlier #1451 crash is fixed. The
            # declared type is honest, so the checker reports it here; the marker
            # keeps the tree green without hiding the fault, and mypy's
            # warn_unused_ignores will flag it the moment #1465 is fixed.
            search_slug_info, column_slug_info, _ = session_info.get_slug_info()  # type: ignore[misc]
            for info_type, slug_and_flags in (("search", search_slug_info), ("column", column_slug_info)):
                for slug_name, is_obsolete in slug_and_flags:
                    all_info[info_type][slug_name] = is_obsolete

        def show_info(info_type: str) -> None:
            """Print the slugs of one kind.

            The names are sorted case-insensitively, joined with commas, and wrapped
            to 100 columns with continuation lines indented four spaces.  The output
            opens with `info_type` capitalized, as in `Search slugs: `, unless there
            are no names, in which case it is a blank line.

            Parameters:
                info_type: Which kind of slug to print, `search` or `column`.
            """
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
