################################################################################
# populate_obs_general.py
#
# Routines to populate fields in the obs_general table.
################################################################################

import julian

from config_data import *
import impglobals
import import_util

# Ordering:
#   target_name must come before target_class
#   time_sec1 must come before time_sec2
#   time_sec1/2 must come before planet_id
#   planet_id must come before rms_obs_id
#   rms_obs_id must come before right_asc[12] and declination[12]
#   right_asc[12] and declination[12] must come before right_asc/d_right_asc
#       and declination/d_declination

################################################################################
# HELPER FUNCTIONS THAT CAN BE USED BY ANY OBS TABLE.
# THEY'RE JUST HERE FOR CONVENIENCE.
################################################################################

def populate_helper_longitude_field(**kwargs):
    metadata = kwargs['metadata']
    field_name = metadata['field_name']
    table_name = metadata['table_name']
    row = metadata[table_name+'_row']

    assert not field_name.startswith('d_'), (table_name, field_name)

    long1 = row[field_name+'1']
    long2 = row[field_name+'2']

    if long1 is None or long2 is None:
        return None

    if long2 >= long1:
        the_long = (long1 + long2)/2.
    else:
        the_long = (long1 + long2 + 360.)/2.

    if the_long >= 360:
        the_long -= 360.
    if the_long < 0:
        the_long += 360.

    return the_long

def populate_helper_d_longitude_field(**kwargs):
    metadata = kwargs['metadata']
    field_name = metadata['field_name']
    table_name = metadata['table_name']
    row = metadata[table_name+'_row']

    assert field_name.startswith('d_'), (table_name, field_name)

    field_name = field_name[2:] # Get rid of d_

    long1 = row[field_name+'1']
    long2 = row[field_name+'2']

    if long1 is None or long2 is None:
        return None

    if long2 >= long1:
        the_long = (long1 + long2)/2.
    else:
        the_long = (long1 + long2 + 360.)/2.

    return the_long - long1


################################################################################
# THESE ARE SPECIFIC TO OBS_GENERAL
################################################################################

def populate_obs_general_id(**kwargs):
    next_id = impglobals.NEXT_OBS_GENERAL_ID
    impglobals.NEXT_OBS_GENERAL_ID += 1
    return next_id

def populate_obs_general_instrument_id(**kwargs):
    volume_id = kwargs['volume_id']
    volume_id_prefix = volume_id[:volume_id.find('_')]
    instrument_name = VOLUME_ID_PREFIX_TO_INSTRUMENT_NAME[volume_id_prefix]
    return instrument_name

def populate_obs_general_volume_id(**kwargs):
    volume_id = kwargs['volume_id']
    return volume_id

def populate_obs_general_mission_id(**kwargs):
    mission_id = kwargs['mission_abbrev']
    return mission_id

def populate_obs_general_target_class(**kwargs):
    metadata = kwargs['metadata']
    obs_general_row = metadata['obs_general_row']
    index_row_num = metadata['index_row_num']
    # This target_name might have "S RINGS" in it; slightly different from the
    # PDS "TARGET_NAME"
    target_name = obs_general_row['target_name'].upper()
    if target_name in TARGET_NAME_MAPPING:
        target_name = TARGET_NAME_MAPPING[target_name]
    if target_name not in TARGET_NAME_INFO:
        import_util.announce_unknown_target_name(target_name, index_row_num)
        return None
    _, target_class = TARGET_NAME_INFO[target_name]
    return target_class
