# This utility takes a PDS index label file and dumps out the definitions of
# each field in a nice format suitable for use in JSON.
import re
import sys

import pdsparser

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
    assert False

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
