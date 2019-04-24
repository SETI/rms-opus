import abc
import re
from enum import Flag
from typing import List, Dict, Optional, Match, Tuple, Pattern, Callable, Any

from markupsafe import Markup

from log_entry import LogEntry

SESSION_INFO = Tuple[List[str], Optional[str]]


class AbstractConfiguration(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def create_session_info(self, uses_html: bool = False) -> 'AbstractSessionInfo':
        raise Exception()

    @abc.abstractmethod
    def get_session_flag_list(self) -> List[Flag]:
        raise Exception()


class AbstractSessionInfo(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def parse_log_entry(self, entry: LogEntry) -> SESSION_INFO:
        raise Exception()

    @abc.abstractmethod
    def get_session_flags(self) -> Flag:
        raise Exception()

    @staticmethod
    def quote_and_join_list(string_list: List[str]) -> str:
        return ', '.join(f'"{string}"' for string in string_list)

    @staticmethod
    def safe_format(format_string: str, *args: Any) -> str:
        return Markup(format_string).format(*args)


class ForPattern:
    """
    A Decorator used by SessionInfo.
    A method is decorated with the regex of the URLs that it knows how to parse.
    """

    METHOD = Callable[[Any, Dict[str, str], Match[str]], SESSION_INFO]

    PATTERNS: List[Tuple[Pattern[str], METHOD]] = []

    def __init__(self, pattern: str):
        self.pattern = re.compile(pattern + '$')

    def __call__(self, fn: METHOD, *args: Any, **kwargs: Any) -> METHOD:
        # We leave the function unchanged, but we add the regular expression and the function to our list of
        # regexp/function pairs
        ForPattern.PATTERNS.append((self.pattern, fn))
        return fn
