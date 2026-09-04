"""Print a PDS index label's field definitions in the form a table schema wants.

Run as ``python -m opus_import.util.dump_pds_definitions <label>`` while adding an
instrument: the output is the ``"definition"`` entries for the packaged
``table_schemas`` JSON, with each label's prose reflowed onto one line.
"""

from __future__ import annotations

import re
import sys

import pdsparser


def main() -> None:
    """Dump the field definitions of the PDS index label named by the argument.

    Raises:
        ValueError: If the label holds no table object under a name this recognizes.
    """
    label_path = sys.argv[1]

    label = pdsparser.PdsLabel.from_file(label_path).as_dict()
    if 'INDEX_TABLE' in label:
        index_dict = label['INDEX_TABLE']
    elif 'IMAGE_INDEX_TABLE' in label:
        index_dict = label['IMAGE_INDEX_TABLE']
    elif 'TABLE' in label:
        index_dict = label['TABLE']
    elif 'MOON_GEOMETRY_TABLE' in label:
        index_dict = label['MOON_GEOMETRY_TABLE']
    elif 'RING_GEOMETRY_TABLE' in label:
        index_dict = label['RING_GEOMETRY_TABLE']
    else:
        raise ValueError(f'No recognized table key found in label "{label_path}"')

    for field_name in sorted(index_dict.keys()):
        index_entry = index_dict[field_name.upper()]
        if not isinstance(index_entry, dict):
            continue
        index_description = index_entry['DESCRIPTION']

        index_description = re.sub(' +', ' ', index_description)
        index_description = re.sub('\n +', '\n', index_description)
        index_description = re.sub(' +\n', '\n', index_description)
        index_description, _ = re.subn(r'(\S)\n(\S)', '\\1 \\2', index_description)
        index_description = index_description.replace('\n\n', '\\n')
        print(field_name)
        print(f'    "definition": "{index_description}",')


if __name__ == '__main__':
    main()
