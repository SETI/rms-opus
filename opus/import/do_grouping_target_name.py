################################################################################
# do_grouping_target_name.py
#
# Generate and maintain the grouping_target_name table.
#
# This is a really lame, constant table that gives an ordering to the planets
# for the Intended Target widget.
################################################################################

import os

from config_data import *
import impglobals
import import_util


def create_import_grouping_target_name_table():
    db = impglobals.DATABASE
    logger = impglobals.LOGGER

    logger.log('info',
                          'Creating new import grouping_target_name table')
    grouping_target_name_schema = import_util.read_schema_for_table(
                                                        'grouping_target_name')
    # Start from scratch
    db.drop_table('import', 'grouping_target_name')
    db.create_table('import', 'grouping_target_name',
                    grouping_target_name_schema,
                    ignore_if_exists=False)

    rows = []
    disp_order = 0

    for abbrev, planet in [('VEN', 'Venus'),
                           ('EAR', 'Earth'),
                           ('MAR', 'Mars'),
                           ('JUP', 'Jupiter'),
                           ('SAT', 'Saturn'),
                           ('URA', 'Uranus'),
                           ('NEP', 'Neptune'),
                           ('PLU', 'Pluto'),
                           ('OTHER', 'Other'),
                           (None,  'NULL')]:
        entry = {
            'value': abbrev,
            'label': planet,
            'display': 'Y',
            'disp_order': disp_order
        }
        disp_order += 1
        rows.append(entry)

    db.insert_rows('import', 'grouping_target_name', rows)

def copy_grouping_target_name_from_import_to_permanent():
    db = impglobals.DATABASE
    logger = impglobals.LOGGER

    logger.log('info',
               'Copying grouping_target_name table from import to permanent')
    # Start from scratch
    grouping_target_name_schema = import_util.read_schema_for_table('grouping_target_name')
    db.drop_table('perm', 'grouping_target_name')
    db.create_table('perm', 'grouping_target_name', grouping_target_name_schema,
                    ignore_if_exists=False)

    db.copy_rows_between_namespaces('import', 'perm', 'grouping_target_name')


def do_grouping_target_name():
    create_import_grouping_target_name_table()
    copy_grouping_target_name_from_import_to_permanent()
    impglobals.DATABASE.drop_table('import', 'grouping_target_name')
