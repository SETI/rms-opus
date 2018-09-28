################################################################################
# populate_obs_general.py
#
# Routines to populate fields in the obs_general table.
################################################################################

import json

import julian
import pdsfile

from config_data import *
import impglobals
import import_util
import opus_secrets

# Ordering:
#   target_name must come before target_class
#   time_sec1 must come before time_sec2
#   time_sec1/2 must come before planet_id
#   planet_id must come before opus_id
#   opus_id must come before right_asc[12] and declination[12]
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
    # This target_name might have "S RINGS" in it; slightly different from the
    # PDS "TARGET_NAME"
    target_name = obs_general_row['target_name'].upper()
    if target_name in TARGET_NAME_MAPPING:
        target_name = TARGET_NAME_MAPPING[target_name]
    if target_name not in TARGET_NAME_INFO:
        import_util.announce_unknown_target_name(target_name)
        if impglobals.ARGUMENTS.import_ignore_errors:
            return 'OTHER'
        return None
    _, target_class = TARGET_NAME_INFO[target_name]
    return target_class

def populate_obs_general_time_sec1(**kwargs):
    metadata = kwargs['metadata']
    general_row = metadata['obs_general_row']
    time1 = general_row['time1']

    if time1 is None:
        return None

    try:
        time1_sec = julian.tai_from_iso(time1)
    except Exception as e:
        import_util.log_nonrepeating_error(
            f'Bad start time format "{time1}": {e}')
        return None

    return time1_sec

def populate_obs_general_time_sec2(**kwargs):
    metadata = kwargs['metadata']
    general_row = metadata['obs_general_row']
    time2 = general_row['time2']

    if time2 is None:
        return None

    try:
        time2_sec = julian.tai_from_iso(time2)
    except Exception as e:
        import_util.log_nonrepeating_error(
            f'Bad stop time format "{time2}": {e}')
        return None

    time1_sec = general_row['time_sec1']

    if time1_sec is not None and time2_sec < time1_sec:
        time1 = general_row['time1']
        import_util.log_warning(f'time1 ({time1}) and time2 ({time2}) are '+
                                f'in the wrong order - setting to time1')
        time2_sec = time1_sec

    return time2_sec

def _iter_flatten(iterable):
  it = iter(iterable)
  for e in it:
    if isinstance(e, (list, tuple)):
      for f in _iter_flatten(e):
        yield f
    else:
      yield e

def _pdsfile_iter_flatten(iterable):
    "Flatten list and remove duplicate PdsFile objects"
    pdsfiles = _iter_flatten(iterable)
    abspaths = []
    ret = []
    for pdsfile in pdsfiles:
        if pdsfile.abspath not in abspaths:
            abspaths.append(pdsfile.abspath)
            ret.append(pdsfile)
    return ret

def populate_obs_general_preview_images(**kwargs):
    metadata = kwargs['metadata']
    general_row = metadata['obs_general_row']
    file_spec = general_row['primary_file_spec']
    pdsf = pdsfile.PdsFile.from_filespec(file_spec)
    products = pdsf.opus_products()

    browse_data = {}

    for product_type in products.keys():
        if not isinstance(product_type, tuple):
            import_util.log_nonrepeating_error('Non-tuple product type')
            continue
        product_class = product_type[0]
        if product_class != 'browse' and product_class != 'diagram':
            continue
        browse_type = product_type[2]
        list_of_sublists = products[product_type]
        flat_list = _pdsfile_iter_flatten(list_of_sublists)
        if len(flat_list) > 1:
            # This can happen for CIRS, which has multiple browse
            # products. Take that one that starts with IMG if possible.
            for product in flat_list:
                filename = product.url.split('/')[-1]
                if filename.startswith('IMG'):
                    break
            else:
                product = flat_list[0]
        else:
            product = flat_list[0]
        data = {}
        data['url'] = product.url
        data['alt_text'] = product.alt
        data['size_bytes'] = product.size_bytes
        data['width'] = product.width
        data['height'] = product.height
        browse_data[browse_type.replace('-','_')] = data

    if len(browse_data) != 4:
        import_util.log_nonrepeating_warning(
            f'Some browse/diagram images missing for "{file_spec}" - found '
            +f'{len(browse_data)}')
    ret = json.dumps(browse_data)
    return ret
