"""The interface between the log analyzer and the site whose logs it reads.

The analyzer itself knows about hosts, sessions and timeouts, and nothing about any
particular site.  Everything site-specific reaches it through a configuration: the
class named `Configuration` in the module given to `--configuration`, which supplies
the per-session parser, the HTML generator and the summary report that `LogParser`
drives.  `opus_log_analyzer.opus.configuration` is the configuration shipped for OPUS.
"""
import abc
import re
from collections.abc import Callable
from enum import Flag
from re import Match, Pattern
from typing import Any, NewType, TextIO

from markupsafe import Markup

from opus_log_analyzer.log_entry import LogEntry

SESSION_INFO = tuple[list[str], str | None]
LogId = NewType('LogId', int)


class AbstractConfiguration(metaclass=abc.ABCMeta):
    """What the analyzer asks of a configuration.

    The analyzer constructs the configuration once per run, handing it the parsed
    command-line arguments as keyword arguments.
    """

    @abc.abstractmethod
    def create_session_info(self, uses_html: bool = False) -> 'AbstractSessionInfo':
        """
        Creates a new user session for parsing log entries.
        """
        raise Exception()

    @abc.abstractmethod
    def create_batch_html_generator(self, host_infos_by_ip: list[Any]) -> 'AbstractBatchHtmlGenerator':
        """
        Creates a blackbox capable of giving the Jinja template whatever information it needs
        """
        raise Exception()

    @abc.abstractmethod
    def show_summary(self, sessions: list[Any], output: TextIO) -> None:
        """Implements the --summary operation, whatever that happens to mean for this configuration"""
        raise Exception()


class AbstractSessionInfo(metaclass=abc.ABCMeta):
    """Parses the log entries of one session and remembers what it has seen.

    The analyzer creates one of these per session through
    `AbstractConfiguration.create_session_info`, then hands it that session's
    entries in the order they were logged.
    """

    @abc.abstractmethod
    def parse_log_entry(self, entry: LogEntry, log_id: LogId) -> SESSION_INFO:
        """Work out what one log entry did, in the light of the ones before it.

        Parameters:
            entry: The entry to interpret.
            log_id: Identifies the entry within its session, so that what the entry
                is found to have done can be recorded against it.

        Returns:
            The lines of text describing what the entry did, and a site-relative URL
            showing roughly what the user was looking at, or None where there is
            none.  An empty list of lines means the entry says nothing worth
            reporting: the analyzer leaves such an entry out, and one at the start of
            a session does not begin a session.
        """
        raise Exception()

    @abc.abstractmethod
    def get_icon_flags(self) -> Flag:
        """Return the flags summarizing what this session did.

        A session whose flags come back empty is left out of the batch output, on the
        grounds that it did nothing.
        """
        raise Exception()

    @staticmethod
    def quote_and_join_list(string_list: list[str]) -> str:
        """Join the strings into a comma-separated list, each item double-quoted."""
        return ', '.join(f'"{string}"' for string in string_list)

    @staticmethod
    def safe_format(format_string: str, *args: Any) -> str:
        """Substitute values into an HTML format string, escaping them as it goes.

        Parameters:
            format_string: HTML containing `str.format` fields.  It is taken as
                markup and is not escaped.
            *args: The values to substitute.  Each is HTML-escaped unless it is
                already markup.

        Returns:
            The formatted HTML, as a `Markup` string.
        """
        # Markup() marks the format string as trusted and Markup.format then
        # escapes each argument as it substitutes it. That split is the contract
        # this method exists for: the template is the caller's own and carries no
        # data, while the arguments are what can carry log content, and those are
        # escaped. A caller that built its template out of log text would defeat
        # it, which is why the parameter is documented as taken-as-markup.
        return Markup(format_string).format(*args)  # nosec B704


class AbstractBatchHtmlGenerator(metaclass=abc.ABCMeta):
    """Renders a whole batch run, with all of its hosts and sessions, as HTML."""

    @abc.abstractmethod
    def generate_output(self, output: TextIO) -> None:
        """Write the report.

        Parameters:
            output: The stream to write to.
        """
        ...


class PatternRegistry:
    """
    A Decorator used by SessionInfo.
    A method is decorated with the regex of the URLs that it knows how to parse.
    """

    METHOD = Callable[[Any, LogEntry, dict[str, str], Match[str]], SESSION_INFO]

    patterns: list[tuple[Pattern[str], METHOD]]

    def __init__(self) -> None:
        """Start with no patterns registered."""
        self.patterns = []

    def register(self, pattern: str) -> Callable[[METHOD], METHOD]:
        """Build a decorator that registers a method under a URL pattern.

        Parameters:
            pattern: A regular expression, matched against a path from its start.

        Returns:
            A decorator that adds the method it is given to this registry and hands
            it back unchanged, so several patterns can be stacked on one method.
        """
        def decorator_for_pattern(method: PatternRegistry.METHOD) -> PatternRegistry.METHOD:
            """Add the method to the registry under this pattern and return it."""
            self.patterns.append((re.compile(pattern), method))
            return method
        return decorator_for_pattern

    def find_matching_pattern(self, path: str) -> tuple[METHOD, Match[str]] | None:
        """Find the method registered for a path.

        Parameters:
            path: The path to match.

        Returns:
            The first method whose pattern matches, in the order the patterns were
            registered, together with the match, or None if no pattern matches.
        """
        for (pattern, method) in self.patterns:
            match = re.match(pattern, path)
            if match:
                return method, match
        return None


