################################################################################
# impglobals.py
#
# General utilities used by the import process.
################################################################################

from functools import lru_cache
import json
import numpy as np
import os
import re
import sys
import traceback

import julian
import pdsfile
import pdsparser
import pdstable

from opus_secrets import *
from config_data import *
from config_targets import *
import impglobals
import instruments


################################################################################
# GENERAL UTILITIES
################################################################################

def yield_import_bundle_ids(arguments):
    bundle_descs = []
    exclude_list = []
    if arguments.exclude_bundles:
        exclude_list = arguments.exclude_bundles.split(',')
    if arguments.bundles:
        for bundles in arguments.bundles:
            orig_bundle_descs = bundles.split(',')
            for desc in orig_bundle_descs:
                if desc.upper() == 'ALL':
                    bundle_descs.append('COISS_1xxx')
                    bundle_descs.append('COISS_2xxx')
                    bundle_descs.append('COCIRS_0xxx')
                    bundle_descs.append('COCIRS_1xxx')
                    bundle_descs.append('COCIRS_5xxx')
                    bundle_descs.append('COCIRS_6xxx')
                    bundle_descs.append('COUVIS_0xxx')
                    bundle_descs.append('COVIMS_0xxx')
                    bundle_descs.append('VGISS_5xxx')
                    bundle_descs.append('VGISS_6xxx')
                    bundle_descs.append('VGISS_7xxx')
                    bundle_descs.append('VGISS_8xxx')
                    bundle_descs.append('GO_0xxx')
                    bundle_descs.append('HSTIx_xxxx')
                    bundle_descs.append('HSTJx_xxxx')
                    bundle_descs.append('HSTNx_xxxx')
                    bundle_descs.append('HSTOx_xxxx')
                    bundle_descs.append('HSTUx_xxxx')
                    bundle_descs.append('NHxxLO_xxxx')
                    bundle_descs.append('NHxxMV_xxxx')
                    bundle_descs.append('EBROCC_xxxx')
                    bundle_descs.append('CORSS_8xxx')
                    bundle_descs.append('COUVIS_8xxx')
                    bundle_descs.append('COVIMS_8xxx')
                    bundle_descs.append('VG_28xx')
                elif desc.upper() == 'CASSINI':
                    bundle_descs.append('COISS_1xxx')
                    bundle_descs.append('COISS_2xxx')
                    bundle_descs.append('COCIRS_0xxx')
                    bundle_descs.append('COCIRS_1xxx')
                    bundle_descs.append('COCIRS_5xxx')
                    bundle_descs.append('COCIRS_6xxx')
                    bundle_descs.append('COUVIS_0xxx')
                    bundle_descs.append('COVIMS_0xxx')
                    bundle_descs.append('CORSS_8xxx')
                    bundle_descs.append('COUVIS_8xxx')
                    bundle_descs.append('COVIMS_8xxx')
                elif desc.upper() == 'COISS':
                    bundle_descs.append('COISS_1xxx')
                    bundle_descs.append('COISS_2xxx')
                elif desc.upper() == 'COCIRS':
                    bundle_descs.append('COCIRS_0xxx')
                    bundle_descs.append('COCIRS_1xxx')
                    bundle_descs.append('COCIRS_5xxx')
                    bundle_descs.append('COCIRS_6xxx')
                elif desc.upper() == 'COUVIS':
                    bundle_descs.append('COUVIS_0xxx')
                    bundle_descs.append('COUVIS_8xxx')
                elif desc.upper() == 'COVIMS':
                    bundle_descs.append('COVIMS_0xxx')
                    bundle_descs.append('COVIMS_8xxx')
                elif desc.upper() == 'CORSS':
                    bundle_descs.append('CORSS_8xxx')
                elif desc.upper() == 'VOYAGER':
                    bundle_descs.append('VGISS_5xxx')
                    bundle_descs.append('VGISS_6xxx')
                    bundle_descs.append('VGISS_7xxx')
                    bundle_descs.append('VGISS_8xxx')
                    bundle_descs.append('VG_28xx')
                elif desc.upper() == 'VGISS':
                    bundle_descs.append('VGISS_5xxx')
                    bundle_descs.append('VGISS_6xxx')
                    bundle_descs.append('VGISS_7xxx')
                    bundle_descs.append('VGISS_8xxx')
                    bundle_descs.append('VG_2810')
                elif desc.upper() == 'VGPPS':
                    bundle_descs.append('VG_2801')
                elif desc.upper() == 'VGUVS':
                    bundle_descs.append('VG_2802')
                elif desc.upper() == 'VGRSS':
                    bundle_descs.append('VG_2803')
                elif desc.upper() == 'GALILEO' or desc.upper() == 'GOSSI':
                    bundle_descs.append('GO_0xxx')
                elif desc.upper() == 'HST' or desc.upper() == 'HUBBLE':
                    bundle_descs.append('HSTIx_xxxx')
                    bundle_descs.append('HSTJx_xxxx')
                    bundle_descs.append('HSTNx_xxxx')
                    bundle_descs.append('HSTOx_xxxx')
                    bundle_descs.append('HSTUx_xxxx')
                elif desc.upper() == 'NH' or desc.upper() == 'NEWHORIZONS':
                    bundle_descs.append('NHxxLO_xxxx')
                    bundle_descs.append('NHxxMV_xxxx')
                elif desc.upper() == 'NHLORRI':
                    bundle_descs.append('NHxxLO_xxxx')
                elif desc.upper() == 'NHMVIC':
                    bundle_descs.append('NHxxMV_xxxx')
                elif desc.upper() == 'EBROCC':
                    bundle_descs.append('EBROCC_xxxx')
                else:
                    bundle_descs.append(desc)
        # First make sure everything is valid
        any_invalid = False
        for bundle_desc in bundle_descs:
            if bundle_desc in exclude_list:
                continue
            try:
                bundle_pdsfile = pdsfile.PdsFile.from_path(bundle_desc)
            except (KeyError, ValueError):
                any_invalid = True
                impglobals.LOGGER.log('fatal',
                           f'Bad bundle descriptor {bundle_desc}')
            else:
                if (not bundle_pdsfile.is_volume_dir and
                    not bundle_pdsfile.is_volset_dir):
                    any_invalid = True
                    impglobals.LOGGER.log('fatal',
                     f'Volume descriptor not a bundle or volset: {bundle_desc}')
                if not bundle_pdsfile.exists:
                    any_invalid = True
                    impglobals.LOGGER.log('fatal',
                               f'Volume descriptor not found: {bundle_desc}')
        if any_invalid:
            sys.exit(-1)
        # Expand the volsets
        new_voldescs = []
        for bundle_desc in bundle_descs:
            bundle_pdsfile = pdsfile.PdsFile.from_path(bundle_desc)
            if bundle_pdsfile.is_volset_dir:
                childnames = bundle_pdsfile.childnames
                # Make sure 2001 is imported first and then 1001 second for each
                # New Horizon bundle. That way, the primary filespec will be
                # raw in OPUS (same as pdsfile).
                if bundle_pdsfile.volset.startswith("NH"):
                    childnames.reverse()
                new_voldescs += childnames
            else:
                new_voldescs.append(bundle_desc)
        # Now actually return the bundle_ids
        for bundle_id in new_voldescs:
            if bundle_id in exclude_list:
                impglobals.LOGGER.log('info',
                           f'Excluding bundle: {bundle_id}')
                continue
            if bundle_id.find('.') != -1:
                continue # Sometimes a bad tar file gets stuck in the dir
            yield bundle_id

def log_accumulated_warnings(title):
    if len(impglobals.PYTHON_WARNING_LIST) > 0:
        log_error(f'Warnings found during {title}:')
        for w in impglobals.PYTHON_WARNING_LIST:
            log_error('  '+w)
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
        log_error(msg)
        return None, None

    if log_accumulated_warnings(f'table import of {filename}'):
        return None, None

    rows = table.dicts_by_row()
    label = table.info.label.as_dict()

    return rows, label

def safe_column(row, column_name, idx=None):
    "Read a value from a pdstable column accounting for the mask."

    if column_name not in row:
        return None

    if column_name+'_mask' not in row:
        if idx is None:
            return row[column_name]
        return row[column_name][idx]

    if idx is None:
        if np.any(row[column_name+'_mask']):
            return None
        return row[column_name]

    if row[column_name+'_mask'][idx]:
        return None
    return row[column_name][idx]


################################################################################
# TABLE MANIPULATION
################################################################################

def table_name_obs_mission(mission_name):
    assert mission_name in MISSION_ID_TO_MISSION_TABLE_SFX
    return ('obs_mission_'+
            MISSION_ID_TO_MISSION_TABLE_SFX[mission_name].lower())

def table_name_obs_instrument(inst_name):
    assert inst_name in INSTRUMENT_ID_TO_MISSION_ID
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
    schema_filename = safe_join('table_schemas', table_name+'.json')
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
            log_debug(f'Was reading table "{table_name}"')
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
    if impglobals.CURRENT_BUNDLE_ID is not None:
        ret = impglobals.CURRENT_BUNDLE_ID
        if impglobals.CURRENT_INDEX_ROW_NUMBER is not None:
            ret += ' index row '+str(impglobals.CURRENT_INDEX_ROW_NUMBER)
        if impglobals.CURRENT_PRIMARY_FILESPEC is not None:
            ret += f' "{impglobals.CURRENT_PRIMARY_FILESPEC}"'
    if ret != '':
        ret = '[' + ret + '] '
    return ret

def log_error(msg, *args):
    impglobals.LOGGER.log('error', _format_vol_line()+msg, *args)
    impglobals.IMPORT_HAS_BAD_DATA = True

def log_warning(msg, *args):
    impglobals.LOGGER.log('warning', _format_vol_line()+msg, *args)

def log_info(msg, *args):
    impglobals.LOGGER.log('info', _format_vol_line()+msg, *args)

def log_debug(msg, *args):
    impglobals.LOGGER.log('debug', _format_vol_line()+msg, *args)

def log_nonrepeating_error(msg):
    if msg not in impglobals.LOGGED_IMPORT_ERRORS:
        impglobals.LOGGED_IMPORT_ERRORS.append(msg)
        log_error(msg)
        impglobals.IMPORT_HAS_BAD_DATA = True

def log_nonrepeating_warning(msg):
    if msg not in impglobals.LOGGED_IMPORT_WARNINGS:
        impglobals.LOGGED_IMPORT_WARNINGS.append(msg)
        log_warning(msg)

def log_unknown_target_name(target_name):
    msg = f'Unknown TARGET_NAME "{target_name}" - edit config_targets.py'
    log_nonrepeating_error(msg)


################################################################################
# MISC UTILITIES
################################################################################

@lru_cache(maxsize=64)
def cached_tai_from_iso(s):
    return julian.tai_from_iso(s)

def safe_join(*paths)
    return os.path.join(*paths).replace('\\', '/')
