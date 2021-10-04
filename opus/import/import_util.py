################################################################################
# impglobals.py
#
# General utilities used by the import process.
################################################################################

import json
import os
import re
import sys
import traceback

import pdsfile
import pdsparser
import pdstable

from opus_secrets import *
from config_data import *
import impglobals
import instruments

################################################################################
# GENERAL UTILITIES
################################################################################

def yield_import_volume_ids(arguments):
    volume_descs = []
    exclude_list = []
    if arguments.exclude_volumes:
        exclude_list = arguments.exclude_volumes.split(',')
    if arguments.volumes:
        for volumes in arguments.volumes:
            orig_volume_descs = volumes.split(',')
            for desc in orig_volume_descs:
                if desc.upper() == 'ALL':
                    volume_descs.append('COISS_1xxx')
                    volume_descs.append('COISS_2xxx')
                    volume_descs.append('COCIRS_5xxx')
                    volume_descs.append('COCIRS_6xxx')
                    volume_descs.append('COUVIS_0xxx')
                    volume_descs.append('COVIMS_0xxx')
                    volume_descs.append('VGISS_5xxx')
                    volume_descs.append('VGISS_6xxx')
                    volume_descs.append('VGISS_7xxx')
                    volume_descs.append('VGISS_8xxx')
                    volume_descs.append('GO_0xxx')
                    volume_descs.append('HSTIx_xxxx')
                    volume_descs.append('HSTJx_xxxx')
                    volume_descs.append('HSTNx_xxxx')
                    volume_descs.append('HSTOx_xxxx')
                    volume_descs.append('HSTUx_xxxx')
                    volume_descs.append('NHxxLO_xxxx')
                    volume_descs.append('NHxxMV_xxxx')
                    volume_descs.append('EBROCC_xxxx')
                    volume_descs.append('CORSS_8xxx')
                    volume_descs.append('COUVIS_8xxx')
                    volume_descs.append('COVIMS_8xxx')
                    volume_descs.append('VG_28xx')
                elif desc.upper() == 'ALLBUTNH':
                    # This is useful because NH has duplicate opus_id that require
                    # checking while the others don't.
                    volume_descs.append('COISS_1xxx')
                    volume_descs.append('COISS_2xxx')
                    volume_descs.append('COCIRS_5xxx')
                    volume_descs.append('COCIRS_6xxx')
                    volume_descs.append('COUVIS_0xxx')
                    volume_descs.append('COVIMS_0xxx')
                    volume_descs.append('VGISS_5xxx')
                    volume_descs.append('VGISS_6xxx')
                    volume_descs.append('VGISS_7xxx')
                    volume_descs.append('VGISS_8xxx')
                    volume_descs.append('GO_0xxx')
                    volume_descs.append('HSTIx_xxxx')
                    volume_descs.append('HSTJx_xxxx')
                    volume_descs.append('HSTNx_xxxx')
                    volume_descs.append('HSTOx_xxxx')
                    volume_descs.append('HSTUx_xxxx')
                    volume_descs.append('EBROCC_xxxx')
                    volume_descs.append('CORSS_8xxx')
                    volume_descs.append('COUVIS_8xxx')
                    volume_descs.append('COVIMS_8xxx')
                    volume_descs.append('VG_28xx')
                elif desc.upper() == 'CASSINI':
                    volume_descs.append('COISS_1xxx')
                    volume_descs.append('COISS_2xxx')
                    volume_descs.append('COCIRS_5xxx')
                    volume_descs.append('COCIRS_6xxx')
                    volume_descs.append('COUVIS_0xxx')
                    volume_descs.append('COVIMS_0xxx')
                    volume_descs.append('CORSS_8xxx')
                    volume_descs.append('COUVIS_8xxx')
                    volume_descs.append('COVIMS_8xxx')
                elif desc.upper() == 'COISS':
                    volume_descs.append('COISS_1xxx')
                    volume_descs.append('COISS_2xxx')
                elif desc.upper() == 'COCIRS':
                    volume_descs.append('COCIRS_5xxx')
                    volume_descs.append('COCIRS_6xxx')
                elif desc.upper() == 'COUVIS':
                    volume_descs.append('COUVIS_0xxx')
                    volume_descs.append('COUVIS_8xxx')
                elif desc.upper() == 'COVIMS':
                    volume_descs.append('COVIMS_0xxx')
                    volume_descs.append('COVIMS_8xxx')
                elif desc.upper() == 'CORSS':
                    volume_descs.append('CORSS_8xxx')
                elif desc.upper() == 'VOYAGER':
                    volume_descs.append('VGISS_5xxx')
                    volume_descs.append('VGISS_6xxx')
                    volume_descs.append('VGISS_7xxx')
                    volume_descs.append('VGISS_8xxx')
                    volume_descs.append('VG_28xx')
                elif desc.upper() == 'VGISS':
                    volume_descs.append('VGISS_5xxx')
                    volume_descs.append('VGISS_6xxx')
                    volume_descs.append('VGISS_7xxx')
                    volume_descs.append('VGISS_8xxx')
                    volume_descs.append('VG_2810')
                elif desc.upper() == 'VGPPS':
                    volume_descs.append('VG_2801')
                elif desc.upper() == 'VGUVS':
                    volume_descs.append('VG_2802')
                elif desc.upper() == 'VGRSS':
                    volume_descs.append('VG_2803')
                elif desc.upper() == 'GALILEO' or desc.upper() == 'GOSSI':
                    volume_descs.append('GO_0xxx')
                elif desc.upper() == 'HST' or desc.upper() == 'HUBBLE':
                    volume_descs.append('HSTIx_xxxx')
                    volume_descs.append('HSTJx_xxxx')
                    volume_descs.append('HSTNx_xxxx')
                    volume_descs.append('HSTOx_xxxx')
                    volume_descs.append('HSTUx_xxxx')
                elif desc.upper() == 'NH' or desc.upper() == 'NEWHORIZONS':
                    volume_descs.append('NHxxLO_xxxx')
                    volume_descs.append('NHxxMV_xxxx')
                elif desc.upper() == 'NHLORRI':
                    volume_descs.append('NHxxLO_xxxx')
                elif desc.upper() == 'NHMVIC':
                    volume_descs.append('NHxxMV_xxxx')
                elif desc.upper() == 'EBROCC':
                    volume_descs.append('EBROCC_xxxx')
                else:
                    volume_descs.append(desc)
        # First make sure everything is valid
        any_invalid = False
        for volume_desc in volume_descs:
            if volume_desc in exclude_list:
                continue
            try:
                volume_pdsfile = pdsfile.PdsFile.from_path(volume_desc)
            except (KeyError, ValueError):
                any_invalid = True
                impglobals.LOGGER.log('fatal',
                           f'Bad volume descriptor {volume_desc}')
            else:
                if (not volume_pdsfile.is_volume_dir and
                    not volume_pdsfile.is_volset_dir):
                    any_invalid = True
                    impglobals.LOGGER.log('fatal',
                     f'Volume descriptor not a volume or volset: {volume_desc}')
                if not volume_pdsfile.exists:
                    any_invalid = True
                    impglobals.LOGGER.log('fatal',
                               f'Volume descriptor not found: {volume_desc}')
        if any_invalid:
            sys.exit(-1)
        # Expand the volsets
        new_voldescs = []
        for volume_desc in volume_descs:
            volume_pdsfile = pdsfile.PdsFile.from_path(volume_desc)
            if volume_pdsfile.is_volset_dir:
                childnames = volume_pdsfile.childnames
                # Make sure 2001 is imported first and then 1001 second for each
                # New Horizon volume. That way, the primary filespec will be
                # raw in OPUS (same as pdsfile).
                if volume_pdsfile.volset.startswith("NH"):
                    childnames.reverse()
                new_voldescs += childnames
            else:
                new_voldescs.append(volume_desc)
        # Now actually return the volume_ids
        for volume_id in new_voldescs:
            if volume_id in exclude_list:
                impglobals.LOGGER.log('info',
                           f'Excluding volume: {volume_id}')
                continue
            if volume_id.find('.') != -1:
                continue # Sometimes a bad tar file gets stuck in the dir
            yield volume_id

def log_accumulated_warnings(title):
    if len(impglobals.PYTHON_WARNING_LIST) > 0:
        impglobals.LOGGER.log('error',
                   f'Warnings found during {title}:')
        for w in impglobals.PYTHON_WARNING_LIST:
            impglobals.LOGGER.log('error', '  '+w)
        impglobals.PYTHON_WARNING_LIST = []
        impglobals.IMPORT_HAS_BAD_DATA = True
        return True
    return False

def safe_pdstable_read(filename):
    preprocess_label_func = None
    preprocess_table_func = None
    # for (set_search, set_preprocess_label,
    #      set_preprocess_table) in instruments.PDSTABLE_PREPROCESS:
    #     if re.fullmatch(set_search, filename.upper()):
    #         preprocess_label_func = set_preprocess_label
    #         preprocess_table_func = set_preprocess_table

    replacements = {}
    for set_search, set_replacements in instruments.PDSTABLE_REPLACEMENTS:
        if re.fullmatch(set_search, filename.upper()):
            replacements = set_replacements
            break
    try:
        if preprocess_label_func is None:
            table = pdstable.PdsTable(filename, replacements=replacements,
                                      table_callback=preprocess_table_func)
        else:
            lines = pdsparser.PdsLabel.load_file(filename)
            lines = preprocess_label_func(lines)
            table = pdstable.PdsTable(filename, label_contents=lines,
                                      replacements=replacements,
                                      table_callback=preprocess_table_func)

    except KeyboardInterrupt:
        raise
    except:
        msg = f'Exception during reading of "{filename}"'
        if not impglobals.ARGUMENTS.log_suppress_traceback:
            msg += ':\n' + traceback.format_exc()
        impglobals.LOGGER.log('error', msg)
        return None, None

    if log_accumulated_warnings(f'table import of {filename}'):
        return None, None

    rows = table.dicts_by_row()
    label = table.info.label.as_dict()

    return rows, label

def safe_column(row, column_name, idx=None):
    "Read a value from a pdstable column accounting for the mask."

    if column_name+'_mask' not in row:
        if idx is None:
            return row[column_name]
        return row[column_name][idx]

    if idx is None:
        if row[column_name+'_mask']:
            return None
        return row[column_name]

    if row[column_name+'_mask'][idx]:
        return None
    return row[column_name][idx]

################################################################################
# TABLE MANIPULATION
################################################################################

def table_name_obs_mission(mission_name):
    assert mission_name in MISSION_ABBREV_TO_MISSION_TABLE_SFX
    return ('obs_mission_'+
            MISSION_ABBREV_TO_MISSION_TABLE_SFX[mission_name].lower())

def table_name_obs_instrument(inst_name):
    assert inst_name in INSTRUMENT_ABBREV_TO_MISSION_ABBREV
    return 'obs_instrument_'+inst_name.lower()

def table_name_mult(table_name, field_name):
    return 'mult_'+table_name.lower()+'_'+field_name.lower()

def table_name_param_info(namespace):
    return impglobals.DATABASES.convert_raw_to_namespace(namespace,
                                                         'param_info')

def table_name_partables(namespace):
    return impglobals.DATABASES.convert_raw_to_namespace(namespace, 'partables')

def encode_target_name(target_name):
    target_name = target_name.lower()
    target_name = target_name.replace('/', '___')
    target_name = target_name.replace(' ', '____')
    return target_name

def decode_target_name(target_name):
    target_name = target_name.replace('____', ' ')
    target_name = target_name.replace('___', '/')
    return target_name

def table_name_for_sfc_target(target_name):
    if target_name.upper() in TARGET_NAME_MAPPING:
        target_name = TARGET_NAME_MAPPING[target_name.upper()]
    return encode_target_name(target_name)

# NOTE: whenever we change this function, we will have to change
# getSurfacegeoTargetSlug in JS code (in utils.js) as well.
def slug_name_for_sfc_target(target_name):
    if target_name.upper() in TARGET_NAME_MAPPING:
        target_name = TARGET_NAME_MAPPING[target_name.upper()]
    target_name = target_name.lower()
    target_name = target_name.replace('_', '').replace('/', '').replace(' ', '')
    return target_name

def read_schema_for_table(table_name, replace=[]):
    table_name = table_name.replace(IMPORT_TABLE_TEMP_PREFIX, '').lower()
    if table_name.startswith('obs_surface_geometry__'):
        assert replace == []
        target_name = table_name.replace('obs_surface_geometry__', '')
        table_name = 'obs_surface_geometry_target'
        replace=[('<TARGET>', table_name_for_sfc_target(target_name)),
                 ('<SLUGTARGET>', slug_name_for_sfc_target(target_name))]
    schema_filename = os.path.join('table_schemas', table_name+'.json')
    if not os.path.exists(schema_filename):
        return None
    with open(schema_filename, 'r') as fp:
        try:
            if replace is None:
                return json.load(fp)
            contents = fp.read()
            for r in replace:
                contents = contents.replace(r[0], r[1])
            return json.loads(contents)
        except json.decoder.JSONDecodeError:
            impglobals.LOGGER.log('debug', f'Was reading table "{table_name}"')
            raise
        except:
            raise

def find_max_table_id(table_name):
    max1 = -1
    max2 = -1
    if impglobals.DATABASE.table_exists('import', table_name):
        max1 = impglobals.DATABASE.find_column_max('import',
                                                   table_name, 'id')
    if impglobals.DATABASE.table_exists('perm', table_name):
        max2 = impglobals.DATABASE.find_column_max('perm',
                                                   table_name, 'id')
    if max1 is None and max2 is None:
        return -1
    if max1 is None:
        return max2
    if max2 is None:
        return max1
    return max(max1, max2)


################################################################################
# ANNOUNCE ERRORS BUT LET IMPORT CONTINUE
################################################################################

def _format_vol_line():
    ret = ''
    if impglobals.CURRENT_VOLUME_ID is not None:
        ret = impglobals.CURRENT_VOLUME_ID
        if impglobals.CURRENT_INDEX_ROW_NUMBER is not None:
            ret += ' index row '+str(impglobals.CURRENT_INDEX_ROW_NUMBER)
    if ret != '':
        ret = '[' + ret + '] '
    return ret

def log_error(msg, *args):
    impglobals.LOGGER.log('error', _format_vol_line()+msg, *args)
    impglobals.IMPORT_HAS_BAD_DATA = True

def log_warning(msg, *args):
    impglobals.LOGGER.log('warning', _format_vol_line()+msg, *args)

def log_debug(msg, *args):
    impglobals.LOGGER.log('debug', _format_vol_line()+msg, *args)

def log_nonrepeating_error(msg):
    if msg not in impglobals.LOGGED_IMPORT_ERRORS:
        impglobals.LOGGED_IMPORT_ERRORS.append(msg)
        impglobals.LOGGER.log('error', _format_vol_line()+msg)
        impglobals.IMPORT_HAS_BAD_DATA = True

def log_nonrepeating_warning(msg):
    if msg not in impglobals.LOGGED_IMPORT_WARNINGS:
        impglobals.LOGGED_IMPORT_WARNINGS.append(msg)
        impglobals.LOGGER.log('warning', _format_vol_line()+msg)

def announce_unknown_target_name(target_name):
    msg = f'Unknown TARGET_NAME "{target_name}" - edit config_data.py'
    log_nonrepeating_error(msg)
