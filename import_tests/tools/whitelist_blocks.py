"""One rule for both whitelists: an entry has to sit under a comment.

The warning whitelist and the unexecuted-method whitelist are different files with
different contents and the same discipline -- nothing is admitted without a written
reason -- so the check that enforces it lives in one place.
"""

from __future__ import annotations

from pathlib import Path


def unexplained_entries(path: Path, comment_prefix: str) -> list[str]:
    """Return the whitelist entries no comment justifies.

    An entry is justified by a comment that begins its block: comment lines arm the
    entries that follow them, and a blank line ends the block. That lets one reason cover
    a group of entries that share it, without letting an entry appear where no reason
    was given.

    Parameters:
        path: The whitelist file.
        comment_prefix: What starts a comment line.

    Returns:
        One ``line <n>: <entry>`` per unjustified entry.
    """
    unexplained = []
    justified = False
    for line_number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), start=1):
        stripped = line.strip()
        if len(stripped) == 0:
            justified = False
        elif stripped.startswith(comment_prefix):
            justified = True
        elif not justified:
            unexplained.append(f'line {line_number}: {stripped}')
    return unexplained
