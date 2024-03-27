################################################################################
# do_table_names.py
#
# Generate and maintain the table_names table.
################################################################################

import config_data
import impglobals
import import_util


def create_import_table_names_table():
    db = impglobals.DATABASE
    logger = impglobals.LOGGER

    logger.log('info', 'Creating new import table_names table')
    table_names_schema = import_util.read_schema_for_table('table_names')
    # Start from scratch
    db.drop_table('import', 'table_names')
    db.create_table('import', 'table_names', table_names_schema,
                    ignore_if_exists=False)

    # We use the entries in data_config to determine what
    # goes into table_names. The order we do things here matters because we're
    # creating disp_order as we go. This will determine the order of how things
    # are displayed on the Details tab.

    rows = []
    disp_order = 0

    # obs_general first
    entry = {
        'table_name': 'obs_general',
        'label':      'General Constraints',
        'display':    'Y',
        'disp_order': disp_order
    }
    disp_order += 1
    rows.append(entry)

    # Then various random tables
    if impglobals.DATABASE.table_exists('perm', 'obs_pds'):
        entry = {
            'table_name': 'obs_pds',
            'label':      'PDS Constraints',
            'display':    'Y',
            'disp_order': disp_order
        }
        disp_order += 1
        rows.append(entry)

    if impglobals.DATABASE.table_exists('perm', 'obs_type_image'):
        entry = {
            'table_name': 'obs_type_image',
            'label':      'Image Constraints',
            'display':    'Y',
            'disp_order': disp_order
        }
        disp_order += 1
        rows.append(entry)

    if impglobals.DATABASE.table_exists('perm', 'obs_wavelength'):
        entry = {
            'table_name': 'obs_wavelength',
            'label':      'Wavelength Constraints',
            'display':    'Y',
            'disp_order': disp_order
        }
        disp_order += 1
        rows.append(entry)

    if impglobals.DATABASE.table_exists('perm', 'obs_profile'):
        entry = {
            'table_name': 'obs_profile',
            'label':      'Occultation/Reflectance Profiles Constraints',
            'display':    'Y',
            'disp_order': disp_order
        }
        disp_order += 1
        rows.append(entry)

    if impglobals.DATABASE.table_exists('perm', 'obs_surface_geometry_name'):
        entry = {
            'table_name': 'obs_surface_geometry_name',
            'label':      'Surface Geometry Constraints',
            'display':    'Y',
            'disp_order': disp_order
        }
        disp_order += 1
        rows.append(entry)

    if impglobals.DATABASE.table_exists('perm', 'obs_surface_geometry'):
        entry = {
            'table_name': 'obs_surface_geometry',
            'label':      'Surface Geometry Constraints',
            'display':    'Y',
            'disp_order': disp_order
        }
        disp_order += 1
        rows.append(entry)

    surface_geo_table_names = impglobals.DATABASE.table_names(
                                            'perm',
                                            prefix='obs_surface_geometry__')
    for table_name in sorted(surface_geo_table_names):
        target_name = table_name.replace('obs_surface_geometry__', '')
        target_name = import_util.decode_target_name(target_name).title()
        entry = {
            'table_name': table_name,
            'label':      target_name + ' Surface Geometry Constraints',
            'display':    'Y',
            'disp_order': disp_order
        }
        disp_order += 1
        rows.append(entry)

    if impglobals.DATABASE.table_exists('perm', 'obs_ring_geometry'):
        entry = {
            'table_name': 'obs_ring_geometry',
            'label':      'Ring Geometry Constraints',
            'display':    'Y',
            'disp_order': disp_order
        }
        disp_order += 1
        rows.append(entry)

    # Then missions
    for mission_id in sorted(
        config_data.MISSION_ID_TO_MISSION_TABLE_SFX.keys()):
        table_name = 'obs_mission_'+config_data.MISSION_ID_TO_MISSION_TABLE_SFX[
                                                            mission_id]
        if impglobals.DATABASE.table_exists('perm', table_name):
            entry = {
                'table_name': table_name,
                'label':      (config_data.MISSION_ID_TO_MISSION_NAME[mission_id] +
                               ' Mission Constraints'),
                'display':    'Y',
                'disp_order': disp_order
            }
            disp_order += 1
            rows.append(entry)

    # Then instruments
    for instrument_id in sorted(config_data.INSTRUMENT_ID_TO_MISSION_ID.keys()):
        display = 'Y'
        if instrument_id[:3] == 'HST':
            # This is a hack because we don't actually have HST instrument
            # tables, but instead put everything in the mission tables
            display = 'N'
        table_name = 'obs_instrument_'+instrument_id.lower()
        if impglobals.DATABASE.table_exists('perm', table_name):
            entry = {
                'table_name': table_name,
                'label':      (config_data.INSTRUMENT_ID_TO_INSTRUMENT_NAME[
                                                                        instrument_id]+
                               ' Constraints'),
                'display':    display,
                'disp_order': disp_order
            }
            disp_order += 1
            rows.append(entry)

    db.insert_rows('import', 'table_names', rows)

def copy_table_names_from_import_to_permanent():
    db = impglobals.DATABASE
    logger = impglobals.LOGGER

    logger.log('info', 'Copying table_names table from import to permanent')
    # Start from scratch
    table_names_schema = import_util.read_schema_for_table('table_names')
    db.drop_table('perm', 'table_names')
    db.create_table('perm', 'table_names', table_names_schema,
                    ignore_if_exists=False)

    db.copy_rows_between_namespaces('import', 'perm', 'table_names')


def do_table_names():
    create_import_table_names_table()
    copy_table_names_from_import_to_permanent()
    impglobals.DATABASE.drop_table('import', 'table_names')
