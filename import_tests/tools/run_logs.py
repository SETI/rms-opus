"""Read a pipeline run's logs, and decide which warnings were expected.

The import's real gate is its log, not its exit status: several steps report failure
through the log and still exit zero. So the suite reads the logs, and it holds every
warning to a checked-in whitelist whose entries each carry a comment saying why the
warning is benign.

The whitelist is matched against the message alone, with pdslogger's timestamp, logger
name, nesting depth and level stripped off, so a pattern describes content rather than
the clock.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

#: How pdslogger starts every log record: an ISO timestamp, the logger's name, a run of
#: dashes standing for the nesting depth, and the level. Everything after that is the
#: message, which can then run over several lines.
_RECORD_START_RE = re.compile(
    r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+ \| [^|]+\|-*\| [A-Z]+ \| (?P<message>.*)$'
)

#: A whitelist line that starts with this is a comment. Every entry carries one above it
#: saying why the warning it admits is benign.
COMMENT_PREFIX = '#'


@dataclass(frozen=True)
class WhitelistEntry:
    """One admitted warning.

    Attributes:
        pattern: The regular expression, matched against a whole message.
        line_number: Where it sits in the file, for a failure message that can be acted
            on.
    """

    pattern: re.Pattern[str]
    line_number: int


def read_messages(log_path: Path) -> list[str]:
    """Return the messages a log file holds, with pdslogger's own prefix removed.

    A message that runs over several lines -- a traceback, most often -- is returned as
    one string with its newlines intact.

    Parameters:
        log_path: The log file. A file that does not exist holds no messages.

    Returns:
        One string per record, in the order they were logged.
    """
    if not log_path.is_file():
        return []
    messages: list[str] = []
    for line in log_path.read_text(encoding='utf-8', errors='replace').splitlines():
        match = _RECORD_START_RE.match(line)
        if match is None:
            if len(messages) > 0:
                messages[-1] += '\n' + line
            continue
        messages.append(match.group('message').strip())
    return messages


def read_whitelist(path: Path) -> list[WhitelistEntry]:
    """Read the warning whitelist.

    Parameters:
        path: The whitelist file.

    Returns:
        One entry per non-comment, non-blank line, in file order.

    Raises:
        re.error: If a line is not a valid regular expression.
    """
    entries = []
    for line_number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), start=1):
        stripped = line.strip()
        if len(stripped) == 0 or stripped.startswith(COMMENT_PREFIX):
            continue
        entries.append(
            WhitelistEntry(pattern=re.compile(stripped, re.DOTALL), line_number=line_number)
        )
    return entries


def classify(
    messages: list[str], entries: list[WhitelistEntry]
) -> tuple[list[str], list[WhitelistEntry]]:
    """Match a run's warnings against the whitelist, both ways.

    Parameters:
        messages: The warnings the run logged.
        entries: The whitelist.

    Returns:
        The messages no entry admits, and the entries no message needed. A stale entry
        is itself a defect: the file's whole value is that each line was justified
        against a warning someone actually saw.
    """
    unmatched_messages = []
    used = set()
    for message in messages:
        matched = False
        for index, entry in enumerate(entries):
            if entry.pattern.fullmatch(message):
                used.add(index)
                matched = True
        if not matched:
            unmatched_messages.append(message)
    unused = [entry for index, entry in enumerate(entries) if index not in used]
    return unmatched_messages, unused


def distinct(messages: list[str]) -> list[str]:
    """Return the distinct messages in a list, in first-seen order.

    Parameters:
        messages: The messages.

    Returns:
        Each distinct message once, which is what a failure report should show rather
        than the same warning a thousand times.
    """
    seen: set[str] = set()
    ordered = []
    for message in messages:
        if message not in seen:
            seen.add(message)
            ordered.append(message)
    return ordered
