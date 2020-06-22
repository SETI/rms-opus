import abc
import re
from enum import Flag
from typing import List, Dict, Optional, Match, Tuple, Pattern, Callable, Any, TextIO, NewType

from markupsafe import Markup

from log_entry import LogEntry

SESSION_INFO = Tuple[List[str], Optional[str]]
LogId = NewType('LogId', int)


class AbstractConfiguration(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def create_session_info(self, uses_html: bool = False) -> 'AbstractSessionInfo':
        """
        Creates a new user session for parsing log entries.
        """
        raise Exception()

    @abc.abstractmethod
    def create_batch_html_generator(self, host_infos_by_ip: List[Any]) -> 'AbstractBatchHtmlGenerator':
        """
        Creates a blackbox capable of giving the Jinja template whatever information it needs
        """
        raise Exception()

    @abc.abstractmethod
    def show_summary(self, sessions: List[Any], output: TextIO) -> None:
        """Implements the --summary operation, whatever that happens to mean for this configuration"""
        raise Exception()


class AbstractSessionInfo(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def parse_log_entry(self, entry: LogEntry, log_id: LogId) -> SESSION_INFO:
        raise Exception()

    @abc.abstractmethod
    def get_icon_flags(self) -> Flag:
        raise Exception()

    @staticmethod
    def quote_and_join_list(string_list: List[str]) -> str:
        return ', '.join(f'"{string}"' for string in string_list)

    @staticmethod
    def safe_format(format_string: str, *args: Any) -> str:
        return Markup(format_string).format(*args)


class AbstractBatchHtmlGenerator(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def generate_output(self, output: TextIO) -> None: ...


class PatternRegistry:
    """
    A Decorator used by SessionInfo.
    A method is decorated with the regex of the URLs that it knows how to parse.
    """

    METHOD = Callable[[Any, LogEntry, Dict[str, str], Match[str]], SESSION_INFO]

    patterns: List[Tuple[Pattern[str], METHOD]]

    def __init__(self) -> None:
        self.patterns = []

    def register(self, pattern: str) -> Callable[[METHOD], METHOD]:
        def decorator_for_pattern(method: PatternRegistry.METHOD) -> PatternRegistry.METHOD:
            self.patterns.append((re.compile(pattern), method))
            return method
        return decorator_for_pattern

    def find_matching_pattern(self, path: str) -> Optional[Tuple[METHOD, Match[str]]]:
        for (pattern, method) in self.patterns:
            match = re.match(pattern, path)
            if match:
                return method, match
        return None


