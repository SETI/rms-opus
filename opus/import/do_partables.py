################################################################################
# do_partables.py
#
# Generate and maintain the partables table.
################################################################################

from config_data import *
import impglobals
import import_util


def create_import_partables_table():
    db = impglobals.DATABASE
    logger = impglobals.LOGGER

    logger.log('info', 'Creating new import partables table')
    partables_schema = import_util.read_schema_for_table('partables')
    # Start from scratch
    db.drop_table('import', 'partables')
    db.create_table('import', 'partables', partables_schema,
                    ignore_if_exists=False)

    # We use the entries in data_config to determine the first part of what
    # goes into partables.

    # For obs_general, we care about mission_id, inst_host_id, instrument_id,
    # and type_id.

    rows = []

    for mission_id in sorted(MISSION_ID_TO_MISSION_TABLE_SFX.keys()):
        entry = {
            'trigger_tab': 'obs_general',
            'trigger_col': 'mission_id',
            'trigger_val': mission_id,
            'partable':    ('obs_mission_'+
                            MISSION_ID_TO_MISSION_TABLE_SFX[mission_id])
        }
        rows.append(entry)

    for instrument_id in sorted(INSTRUMENT_ID_TO_MISSION_ID.keys()):
        partable = 'obs_instrument_'+instrument_id.lower()
        if instrument_id[:3] == 'HST':
            # This is a hack because we don't actually have HST instrument
            # tables, but instead put everything in the mission tables
            partable = 'obs_mission_hubble'
        entry = {
            'trigger_tab': 'obs_general',
            'trigger_col': 'instrument_id',
            'trigger_val': instrument_id,
            'partable':    partable
        }
        rows.append(entry)

    for inst_host_id in sorted(INST_HOST_ID_TO_MISSION_ID.keys()):
        entry = {
            'trigger_tab': 'obs_general',
            'trigger_col': 'inst_host_id',
            'trigger_val': inst_host_id,
            'partable':    ('obs_mission_'+
                            MISSION_ID_TO_MISSION_TABLE_SFX[
                                INST_HOST_ID_TO_MISSION_ID[
                                    inst_host_id]])
        }
        rows.append(entry)

    # We don't need this anymore because Image Constraints are now permanently
    # displayed
    # entry = {
    #     'trigger_tab': 'obs_general',
    #     'trigger_col': 'data_type',
    #     'trigger_val': 'IMG',
    #     'partable':    'obs_type_image'
    # }
    # rows.append(entry)

    surface_geo_table_names = impglobals.DATABASE.table_names(
                                            'perm',
                                            prefix='obs_surface_geometry__')
    for table_name in sorted(surface_geo_table_names):
        target_name = table_name.replace('obs_surface_geometry__', '')
        entry = {
            'trigger_tab': 'obs_surface_geometry_name',
            'trigger_col': 'target_name',
            'trigger_val': import_util.decode_target_name(target_name).upper(),
            'partable':    table_name
        }
        rows.append(entry)

    db.insert_rows('import', 'partables', rows)

def copy_partables_from_import_to_permanent():
    db = impglobals.DATABASE
    logger = impglobals.LOGGER

    logger.log('info', 'Copying partables table from import to permanent')
    # Start from scratch
    partables_schema = import_util.read_schema_for_table('partables')
    db.drop_table('perm', 'partables')
    db.create_table('perm', 'partables', partables_schema, ignore_if_exists=False)

    db.copy_rows_between_namespaces('import', 'perm', 'partables')


def do_partables():
    create_import_partables_table()
    copy_partables_from_import_to_permanent()
    impglobals.DATABASE.drop_table('import', 'partables')
