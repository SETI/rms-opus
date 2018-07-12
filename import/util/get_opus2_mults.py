# This utility finds all of the existing mult_ tables and sends to stdout a new
# file containing the prototype definitions for the mult tables, which then
# needs to be hand-edited.
#
# This program should only be used for initial setup of the new import pipeline.
# Once all tables are transferred over this program is deprecated.

import json
import re
import sys

import MySQLdb

import pdsparser

from secrets import *

if len(sys.argv) != 2:
    print('Usage:', file=sys.stderr)
    print('  python get_opus2_mults.py <database>',
          file=sys.stderr)
    sys.exit(-1)

db_name = sys.argv[1]

res = []

conn = MySQLdb.connect(user=DB_USER, passwd=DB_PASSWORD,
                       db=db_name)

cur = conn.cursor()
cur.execute("SHOW TABLES LIKE 'mult_%'")
table_names = cur.fetchall()

print('PREPROGRAMMED_MULT_TABLE_CONTENTS = {')
for table_name in table_names:
    table_name = table_name[0]
    if table_name == 'mult_tracker':
        continue
    cur.execute('SELECT value, label, disp_order, display FROM '+table_name)
    rows = list(cur.fetchall())
    rows.sort(key=lambda x: 0 if x[2] is None else x[2] )
    new_rows = []
    always_same = True
    for row in rows:
        value, label, disp_order, display = row
        if value != label:
            always_same = False
        if value is None:
            value = 'None'
        else:
            value = "'"+value+"'"
        if label is None:
            label = 'None'
        else:
            label = "'"+label+"'"
        if disp_order is None:
            disp_order = 'None'
        else:
            disp_order = str(disp_order*10)
        if display is None:
            display = 'None'
        else:
            display = "'"+display+"'"
        new_rows.append((value, label, disp_order, display))
    if not always_same:
        print(f"    '{table_name}': [")
        max_value = max([len(x[0]) for x in new_rows])
        max_label = max([len(x[1]) for x in new_rows])
        max_disp_order = max([len(x[2]) for x in new_rows])
        for row_num, row in enumerate(new_rows):
            value, label, disp_order, display = row
            fmt = ("        ({row_num:4d}, {value:>"+str(max_value)+"s}, "+
                   "{label:>"+str(max_label)+"s}, {disp_order:>4s}, {display}),")
            print(fmt.format(row_num=row_num, value=value, label=label,
                              disp_order=disp_order, display=display))
        print('    ],')
print( '}')
