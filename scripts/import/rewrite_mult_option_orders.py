"""Rewrite the order elements of the packaged ``mult_options`` lists as integers.

A ``mult_options`` entry is ``[id, value, label, pin, display, grouping, group_pin]``,
and the import reads its ``pin`` and ``group_pin`` as integers, rejecting a string. This
rewrites every ``pin`` and ``group_pin`` written as a string of digits, such as
``"010"``, as the integer it spells, ``10``, in every packaged ``obs_*.json`` schema, and
the group ``disp_order`` strings of
``opus_import/config_targets/planet_group_mapping.py`` likewise. Each file keeps its
layout: a rewritten element is padded on the left to the width the string took, so the
columns of a list stay aligned.

Run it from the repository root: ``python scripts/import/rewrite_mult_option_orders.py``.
A file with nothing to rewrite is left untouched, so a second run changes nothing.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

#: The packaged table schemas.
SCHEMA_DIR = Path('src/opus_import/table_schemas')

#: The module holding the planet groups' order.
PLANET_GROUP_MAPPING = Path('src/opus_import/config_targets/planet_group_mapping.py')

#: One ``mult_options`` entry on a line of its own, with its trailing comma if any.
_ENTRY_LINE = re.compile(r'^(?P<indent>\s*)\[(?P<body>.*)\](?P<tail>,?)\s*$')

#: One element of an entry: a JSON string, ``null`` or a number, with its spacing.
_ELEMENT = re.compile(r'\s*(?:"(?:[^"\\]|\\.)*"|null|-?\d+)\s*')

#: The positions of ``pin`` and ``group_pin`` in an entry.
_ORDER_POSITIONS = (3, 6)

#: The number of elements an entry has.
_ENTRY_LENGTH = 7

#: A planet group's order, as the mapping wrote it.
_GROUP_ORDER = re.compile(r"'disp_order': '(\d+)'")


def _rewrite_element(element: str) -> str:
    """Return one element with a quoted string of digits written as an integer.

    Parameters:
        element: The element's text, with the spacing around it.

    Returns:
        The element unchanged unless it is a quoted string of digits; then the integer,
        padded on the left so the element keeps its width.
    """
    stripped = element.strip()
    if not re.fullmatch(r'"\d+"', stripped):
        return element
    number = str(int(stripped[1:-1]))
    leading = element[: len(element) - len(element.lstrip())]
    trailing = element[len(element.rstrip()) :]
    return leading + number.rjust(len(stripped)) + trailing


def rewrite_entry_line(line: str) -> str:
    """Return a schema line with its entry's ``pin`` and ``group_pin`` as integers.

    Parameters:
        line: One line of a schema file.

    Returns:
        The line unchanged unless it is a whole ``mult_options`` entry; then the entry
        with each order element that is a quoted string of digits rewritten.
    """
    match = _ENTRY_LINE.match(line)
    if match is None:
        return line
    body = match['body']
    elements: list[str] = []
    position = 0
    while position < len(body):
        element = _ELEMENT.match(body, position)
        if element is None:
            return line
        elements.append(element.group())
        position = element.end()
        if position < len(body):
            if body[position] != ',':
                return line
            position += 1
    if len(elements) != _ENTRY_LENGTH:
        return line
    json.loads('[' + body + ']')
    for index in _ORDER_POSITIONS:
        elements[index] = _rewrite_element(elements[index])
    return f'{match["indent"]}[{",".join(elements)}]{match["tail"]}\n'


def rewrite_schema(path: Path) -> bool:
    """Rewrite one schema file's ``mult_options`` entries in place.

    Parameters:
        path: The schema file.

    Returns:
        True if the file changed.
    """
    text = path.read_text(encoding='utf-8')
    lines = text.splitlines(keepends=True)
    rewritten = ''.join(rewrite_entry_line(line) for line in lines)
    if rewritten == text:
        return False
    path.write_text(rewritten, encoding='utf-8')
    return True


def rewrite_planet_groups(path: Path) -> bool:
    """Rewrite the planet groups' ``disp_order`` strings as integers, in place.

    Parameters:
        path: ``planet_group_mapping.py``.

    Returns:
        True if the file changed.
    """
    text = path.read_text(encoding='utf-8')
    rewritten = _GROUP_ORDER.sub(lambda m: f"'disp_order': {int(m[1])}", text)
    if rewritten == text:
        return False
    path.write_text(rewritten, encoding='utf-8')
    return True


def main() -> int:
    """Rewrite every packaged schema and the planet groups, naming each file changed.

    Returns:
        The exit status, 0.
    """
    changed = [path for path in sorted(SCHEMA_DIR.glob('obs_*.json')) if rewrite_schema(path)]
    if rewrite_planet_groups(PLANET_GROUP_MAPPING):
        changed.append(PLANET_GROUP_MAPPING)
    for path in changed:
        sys.stdout.write(f'{path}\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())
