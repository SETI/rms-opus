################################################################################
# do_partables.py
#
# Generate and maintain the partables table.
################################################################################

import config_data
from do_import import mult_table_lookup_id
import impglobals
import import_util


def _lookup_table_column(table_schema, column_name):
    for table_column in table_schema:
        if table_column.get('field_name', None) == column_name:
            return table_column
    return None

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

    obs_general_schema = import_util.read_schema_for_table('obs_general')

    rows = []

    mission_id_column = _lookup_table_column(obs_general_schema, 'mission_id')
    for mission_id in sorted(config_data.MISSION_ID_TO_MISSION_TABLE_SFX.keys()):
        mission_id_val = mult_table_lookup_id('obs_general', 'mission_id',
                                              mission_id_column, mission_id)
        entry = {
            'trigger_tab': 'obs_general',
            'trigger_col': 'mission_id',
            'trigger_val': str(mission_id_val),
            'partable':    import_util.table_name_obs_mission(mission_id)
        }
        rows.append(entry)

    instrument_id_column = _lookup_table_column(obs_general_schema, 'instrument_id')
    for instrument_id in sorted(config_data.INSTRUMENT_ID_TO_MISSION_ID.keys()):
        instrument_id_val = mult_table_lookup_id('obs_general', 'instrument_id',
                                                 instrument_id_column, instrument_id)
        partable = import_util.table_name_obs_instrument(instrument_id)
        if instrument_id[:3] == 'HST':
            # This is a hack because we don't actually have HST instrument
            # tables, but instead put everything in the mission tables
            partable = 'obs_mission_hubble'
        entry = {
            'trigger_tab': 'obs_general',
            'trigger_col': 'instrument_id',
            'trigger_val': str(instrument_id_val),
            'partable':    partable
        }
        rows.append(entry)

    inst_host_id_column = _lookup_table_column(obs_general_schema, 'inst_host_id')
    for inst_host_id in sorted(config_data.INST_HOST_ID_TO_MISSION_ID.keys()):
        inst_host_id_val = mult_table_lookup_id('obs_general', 'inst_host_id',
                                                inst_host_id_column, inst_host_id)
        entry = {
            'trigger_tab': 'obs_general',
            'trigger_col': 'inst_host_id',
            'trigger_val': str(inst_host_id_val),
            'partable':    ('obs_mission_'+
                            config_data.MISSION_ID_TO_MISSION_TABLE_SFX[
                                config_data.INST_HOST_ID_TO_MISSION_ID[
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
        target_name = import_util.decode_target_name(target_name).upper()
        # For surface_geometry targets, we don't find the mult id for the target name
        # but instead put the target name string directly in the partable. This is
        # because get_triggered_tables compares the user search string against the
        # partable trigger_val directly instead of doing a database search like it does
        # for other types of triggered tables.
        entry = {
            'trigger_tab': 'obs_surface_geometry_name',
            'trigger_col': 'target_name',
            'trigger_val': target_name,
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
