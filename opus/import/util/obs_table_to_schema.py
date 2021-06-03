# This utility takes a table name and retrieves its schema from a MySQL
# database in OLD OPUS2 FORMAT. It combines this information with that from
# param_info in OLD OPUS2 FORMAT to generate the JSON description of the table
# for the obs_tables directory.
#
# This program should only be used for initial setup of the new import pipeline.
# Once all tables are transferred over this program is deprecated.
#
# Usage:
#  python mysql_obs_table_to_schema.py
#        <database> <table> <label_file>
#
# It's mainly designed to work with OBS_XXX tables, but can be used with things
# like param_info as well. In this case, use this command line:
#
# Usage:
#  python mysql_obs_table_to_schema.py
#        <database> <table>

##### Known unused columns in the OPUS2 database #####
# obs_general:
    # No param_info for column class_id - ignoring column
    # No param_info for column ring_hour1 - ignoring column
    # No param_info for column ring_hour2 - ignoring column
    # No param_info for column ring_hour_wrap - ignoring column
    # No param_info for column target_intercept_time1 - ignoring column
    # No param_info for column target_intercept_time2 - ignoring column
    # No param_info for column opus1_ring_obs_id - ignoring column

# obs_mission_voyager:
    # No param_info for column clock_count_num - ignoring column

# obs_instrument_COCIRS:
    # No param_info for column instrument_mode_list - ignoring column

# obs_instrument_COISS:
    # No param_info for column instrument_flag_list - ignoring column

# obs_ring_geometry:
    # No param_info for column file_name - ignoring column

# obs_surface_geometry_XXX:
    # No param_info for column file_name - ignoring column
    # No param_info for column target_name - ignoring column

# obs_type_image:
    # No param_info for column numeric_id - ignoring column

import json
import os
import re
import sys

import MySQLdb

import pdsparser

from secrets import *

if not 3 <= len(sys.argv) <= 4:
    print('Usage:', file=sys.stderr)
    print('  python obs_table_to_schema.py <database> <table> [<label_file>]',
          file=sys.stderr)
    sys.exit(-1)

db_name = sys.argv[1]
table_name = sys.argv[2]
label_file = None
if len(sys.argv) == 4:
    label_path = sys.argv[3]
    _, label_file = os.path.split(label_path)
    label_file = label_file.lower().replace('.lbl','')

print('** Processing '+table_name)

if label_file:
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

res = []

conn = MySQLdb.connect(user=DB_USER, passwd=DB_PASSWORD,
                       db=db_name)

cur = conn.cursor()
cmd = f'DESC {table_name}'
cur.execute(cmd)
desc_rows = cur.fetchall()

schema = []

django_id = {
    '@field_name': 'id',
    '@field_type': 'uint4',
    '@field_x_autoincrement': True,
    '@field_x_notnull': True,
    '@field_x_key': 'unique',
}

if table_name == 'obs_general' or not table_name.startswith('obs_'):
    # If this is obs_general or a non-obs table, put the Django id first
    # because it's important and prettier this way.
    schema.append(django_id)
elif table_name.startswith('obs_'):
    # For everything except obs_general, add a link back to the obs_general id
    schema.append({
        '@field_name': 'obs_general_id',
        '@field_type': 'uint4',
        '@field_x_notnull': True,
        '@field_x_key': 'foreign',
        '@field_x_key_foreign': ('obs_general', 'id'),
        'data_source': ['TAB:obs_general', 'id']
    })

if table_name.startswith('obs_'):
    if table_name == 'obs_general':
        schema.append({
            '@field_name': 'opus_id',
            '@field_type': 'char40',
            '@field_x_notnull': True,
            '@field_x_key': 'foreign',
            '@field_x_key_foreign': ('obs_general', 'opus_id'),
        })
    else:
        schema.append({
            '@field_name': 'opus_id',
            '@field_type': 'char40',
            '@field_x_notnull': True,
            '@field_x_key': 'foreign',
            '@field_x_key_foreign': ('obs_general', 'opus_id'),
            'data_source': ['TAB:obs_general', 'opus_id'],
        })

mult_fields = []

for table_column in desc_rows:
    (field_name, field_type, field_null, field_key,
     field_default, field_extra) = table_column

    if field_name in ('id', 'time_stamp', 'obs_general_id',
                      'ring_obs_id', 'opus_id'):
        # Already handled
        continue

    if field_name.startswith('mult_'):
        # All mult_ fields are dealth with separately
        continue

    row = {}

    ### Basic information about this column ###

    row['@field_name'] = field_name

    if (field_type.startswith('int') or
        field_type.startswith('tinyint') or
        field_type.startswith('smallint') or
        field_type.startswith('mediumint') or
        field_type.startswith('bigint')):
        row['@field_type'] = 'int4'
        if field_type.endswith('unsigned'):
            row['@field_type'] = 'uint4'
    elif field_type.startswith('float'):
        row['@field_type'] = 'real4'
    elif field_type.startswith('double'):
        row['@field_type'] = 'real8'
    elif field_type.startswith('char'):
        row['@field_type'] = field_type.lower().replace('(','').replace(')','')
    elif field_type.startswith('varchar'):
        row['@field_type'] = field_type.lower().replace('(','').replace(')','')
    elif field_type == 'text' or field_type == 'longtext':
        row['@field_type'] = 'text'
    elif field_type.startswith('datetime'):
        row['@field_type'] = 'datetime'
    elif field_type.startswith('enum'):
        row['@field_type'] = 'enum'
        enum_str = field_type[field_type.index('(')+1:
                             field_type.index(')')]
        row['@field_x_enum_options'] = enum_str
    else:
        print(f'Bad type {field_type}')
        assert False

    if ((field_key == 'UNI' or field_key == 'PRI') and
        table_name.startswith('obs_')):
        print(f'Bad key type {field_name}: {field_key}')
        assert False
    if field_key == 'MUL':
        row['@field_x_key'] = True

    assert field_extra == ''

    if field_null == 'NO':
        row['@field_x_notnull'] = True

    row['@field_x_default'] = field_default

    ### Cross reference with param_info ###
    # This is only done for obs_ tables

    if table_name.startswith('obs_'):
        cmd = f"""
        SELECT * FROM param_info WHERE
            category_name='{table_name}' AND
            (name='{field_name}' OR
            name='{field_name}1')
        """
        cur.execute(cmd)
        pi_rows = cur.fetchall()
        if len(pi_rows) != 1:
            if (not field_name.startswith('d_') and
                field_name != field_name.upper()):
                print(
            f'WARNING: No param_info for column {field_name} - REMOVING COLUMN',
                      file=sys.stderr)
                continue
            else:
                print(
            f'WARNING: No param_info for column {field_name} - column OK',
                      file=sys.stderr)
        else:
            (pi_id,                         # Django unique id
             pi_category_id,                # NOT USED
             pi_name,                       # obs_XXX column name
             pi_type,                       # NOT USED ('real', 'int', 'string')
             pi_length,                     # NOT USED
             pi_slug,                       # URL slug
             pi_post_length,                # NOT USED
             pi_form_type,                  # 'TIME', 'GROUP', 'RANGE', 'STRING',
                                            # 'NULL', 'TARGETS'
             pi_display,                    # Display in search form?
             pi_rank,                       # NOT USED
             pi_disp_order,                 # Order to display
             pi_label,                      # Label on search form
             pi_intro,                      # String to display above search term in
                                            # the left menu
             pi_category_name,              # obs_XXX table name
             pi_display_results,            # Display on metadata page?
             pi_units,                      # Units
             pi_tooltip,                    # String to display above the search
                                            # term in the form
             pi_dict_context,               # Dictionary context
             pi_dict_name,                  # Dictionary term name
             pi_checkbox_group_col_count,   # NOT USED
             pi_special_query,              # NULL, 'long'
             pi_label_results,              # Label on metadata page
             pi_onclick,                    # NOT USED
             pi_dict_more_info_context,     # Dictionary more_info context
             pi_dict_more_info_name,        # Dictionary more_info term name
             pi_search_form,                # NOT USED
                                            # (actually used, but always the same as
                                            #  category_name)
             pi_mission,                    # NOT USED
             pi_instrument,                 # NOT USED
             pi_sub_heading                 # Sub-heading on search form
             ) = pi_rows[0]

            # This is the wrap-around longitude version of the 1/2 fields
            # that we already dealt with, so don't make a param_info entry for
            # this one.

            assert (pi_name == field_name or
                    (pi_name[:-1] == field_name and
                     pi_name[-1] == '1'))

            if pi_name == field_name:
                # Add param_info fields
                row['pi_category_name'] = pi_category_name
                if pi_special_query == 'long':
                    row['pi_form_type'] = 'LONG'
                else:
                    row['pi_form_type'] = pi_form_type
                row['pi_units'] = pi_units
                row['pi_display'] = int(pi_display)
                row['pi_display_results'] = pi_display_results
                row['pi_disp_order'] = pi_disp_order
                row['pi_sub_heading'] = pi_sub_heading
                row['pi_label'] = pi_label
                row['pi_label_results'] = pi_label_results
                row['pi_intro'] = pi_intro
                row['pi_tooltip'] = pi_tooltip
                row['pi_slug'] = pi_slug
                row['pi_dict_context'] = pi_dict_context
                row['pi_dict_name'] = pi_dict_name

                if pi_form_type == 'GROUP':
                    mult_fields.append(field_name)

    ### Cross-reference with PDS label ###
    # This is only done if a PDS label was provided

    if label_file is not None:
        if field_name not in index_dict:
            if field_name == field_name.upper():
                print(f'Column {field_name} not found in PDS label')
        else:
            index_entry = index_dict[field_name.upper()]
            index_name = index_entry['NAME']
            index_type = index_entry['DATA_TYPE']
            index_type_size = index_entry['BYTES']
            index_description = index_entry['DESCRIPTION']

            index_description = re.sub(r'\s+', ' ', index_description)

            val_min = None
            val_max = None
            if index_type == 'INTEGER' or index_type == 'ASCII_REAL':
                val_min = -1e38
                val_max = 1e38

            if index_type == 'ASCII_REAL' and index_type_size < 23:
                if not row['@field_type'].startswith('real'):
                    print(f'WARNING: {field_name} {field_type} not (PDS) real')
            elif index_type == 'INTEGER' and index_type_size < 23:
                if row['@field_type'].find('int') == -1:
                    print(f'WARNING: {field_name} {field_type} not (PDS) int')
            elif index_type == 'CHARACTER':
                if row['@field_type'] != 'char'+str(index_type_size):
                    print(f'WARNING: {field_name} {field_type} not (PDS) '+
                          'char'+str(index_type_size))

            row['data_source'] = (label_file, index_name)
            if val_min is not None:
                row['val_min'] = val_min
            if val_max is not None:
                row['val_max'] = val_max
            row['description'] = index_description

    schema.append(row)

# Now add all the mult_fields
for mult_field in mult_fields:
    mult = {
        '@field_name': 'mult_'+table_name+'_'+mult_field,
        '@field_type': 'uint4',
        '@field_x_key': 'foreign',
        '@field_x_key_foreign': [
            'mult_'+table_name+'_'+mult_field,
            'id'
        ],
        '@field_x_notnull': True
    }
    schema.append(mult)

# Add more fields at the end - these are placed late because they aren't needed
# very often in manual manipulation and it's prettier this way.

if table_name != 'obs_general':
    # Add the Django ID - integer, auto-increment
    schema.append(django_id)

# Add a timestamp field
# This will be created as:
#   DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
schema.append({
    '@field_name': 'timestamp',
    '@field_type': 'timestamp',
})

with open('../table_schemas/'+table_name+'_proto.json', 'w') as fp:
    json.dump(schema, fp, sort_keys=True, indent=4,
                          separators=(',',': '))
