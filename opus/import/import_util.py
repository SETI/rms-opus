################################################################################
# import_util.py
#
# General utilities used by the import process.
################################################################################

import csv
from functools import lru_cache
import json
import numpy as np
import os
import re
import sys
import traceback

import julian
import pdsfile
import pdslogger
import pdsparser
import pdstable

import opus_secrets

import config_data
import config_targets
import impglobals
import instruments


################################################################################
# GENERAL UTILITIES
################################################################################

# This is necessary because NHK2LO needs to come after NHKELO. See issue #1392.
# We go ahead and arrange the other volumes in chronological order as well.
# Also this allows us to only import the 1xxx volumes. The 2xxx volumes are
# calibrated data that show up as a download product and are not really separate
# volumes.
_NHXXLO_BUNDLES = [
    'NHLALO_1001',
    'NHJULO_1001',
    'NHPCLO_1001',
    'NHPELO_1001',
    'NHKCLO_1001',
    'NHKELO_1001',
    'NHK2LO_1001',
]

# Might as well do the same for NHxxMV.
_NHXXMV_BUNDLES = [
    'NHLAMV_1001',
    'NHJUMV_1001',
    'NHPCMV_1001',
    'NHPEMV_1001',
    'NHKCMV_1001',
    'NHKEMV_1001',
]

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
                    bundle_descs.extend(_NHXXLO_BUNDLES)
                    bundle_descs.extend(_NHXXMV_BUNDLES)
                    bundle_descs.append('EBROCC_xxxx')
                    bundle_descs.append('CORSS_8xxx')
                    bundle_descs.append('COUVIS_8xxx')
                    bundle_descs.append('COVIMS_8xxx')
                    bundle_descs.append('VG_28xx')
                    bundle_descs.append('uranus_occs_earthbased')
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
                    bundle_descs.extend(_NHXXLO_BUNDLES)
                    bundle_descs.extend(_NHXXMV_BUNDLES)
                elif desc.upper() == 'NHLORRI':
                    bundle_descs.extend(_NHXXLO_BUNDLES)
                elif desc.upper() == 'NHMVIC':
                    bundle_descs.extend(_NHXXMV_BUNDLES)
                elif desc.upper() == 'EBROCC':
                    bundle_descs.append('EBROCC_xxxx')
                else:
                    bundle_descs.append(desc)
        # First make sure everything is valid
        any_invalid = False
        for bundle_desc in bundle_descs:
            if bundle_desc in exclude_list:
                continue
            good_bundle = False
            # Try it as PDS3 and then PDS4
            try:
                bundle_pdsfile = pdsfile.pds3file.Pds3File.from_path(bundle_desc)
                good_bundle = True
            except (KeyError, ValueError):
                tb_pds3 = traceback.format_exc()
                try:
                    bundle_pdsfile = pdsfile.pds4file.Pds4File.from_path(bundle_desc)
                    good_bundle = True
                except (KeyError, ValueError):
                    any_invalid = True
                    msg = f'Bad bundle descriptor {bundle_desc}'
                    if not impglobals.ARGUMENTS.log_suppress_traceback:
                        msg += ':\n\n'
                        msg += ('*' * 80) + '\nPDS3:\n\n'
                        msg += tb_pds3
                        msg += '\n' + ('*' * 80) + '\nPDS4:\n\n'
                        msg += traceback.format_exc()
                    impglobals.LOGGER.log('fatal', msg)
            if good_bundle:
                if (not bundle_pdsfile.is_bundle_dir and
                    not bundle_pdsfile.is_bundleset_dir):
                    any_invalid = True
                    impglobals.LOGGER.log('fatal',
                        f'Bundle descriptor not a bundle or bundleset: {bundle_desc}')
                if not bundle_pdsfile.exists:
                    any_invalid = True
                    impglobals.LOGGER.log('fatal',
                        f'Bundle descriptor not found: {bundle_desc}')

        if any_invalid:
            sys.exit(-1)

        # Expand the bundlesets
        new_bundledescs = []
        for bundle_desc in bundle_descs:
            try:
                bundle_pdsfile = pdsfile.pds3file.Pds3File.from_path(bundle_desc)
            except (KeyError, ValueError):
                bundle_pdsfile = pdsfile.pds4file.Pds4File.from_path(bundle_desc)
            if bundle_pdsfile.is_bundleset_dir:
                childnames = bundle_pdsfile.childnames
                # Make sure 2001 is imported first and then 1001 second for each
                # New Horizon bundle. That way, the primary filespec will be
                # raw in OPUS (same as pdsfile).
                if bundle_pdsfile.bundleset.startswith("NH"):
                    childnames.reverse()
                new_bundledescs += childnames
            else:
                new_bundledescs.append(bundle_desc)

        # Now actually return the bundle_ids
        for bundle_id in new_bundledescs:
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

def safe_pdstable_read(filename, pds_version):
    if pds_version == 3:
        return safe_pdstable_read_pds3(filename)

    # TODOPDS4 For now, PDS4 index files do not have labels. They are just
    # CSV files. So we read the CSV file and determine the column names from
    # the single header line. We then infer the datatypes from the column data.
    # Eventually we will want to change this to use an official PDS4 label/table
    # reader module.

    with open(filename) as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)

    if len(rows) == 0:
        return rows

    # Infer data types from the data in each column
    for col_name in rows[0].keys():
        col_data = [row[col_name] for row in rows]
        # First check if they are all integers
        try:
            _ = [int(x) for x in col_data]
        except ValueError: # Something parsed badly
            # Now check if they are all floats
            try:
                _ = [float(x) for x in col_data]
            except ValueError: # Something parsed badly
                # Not ints or floats, just leave them as strings
                pass
            else: # All floats
                for row in rows:
                    row[col_name] = float(row[col_name])

        else: # All integers
            for row in rows:
                row[col_name] = int(row[col_name])

    return rows, None  # TODOPDS4 There is no label for now

def safe_pdstable_read_pds3(filename):
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
    assert mission_name in config_data.MISSION_ID_TO_MISSION_TABLE_SFX
    return ('obs_mission_'+
            config_data.MISSION_ID_TO_MISSION_TABLE_SFX[mission_name].lower())

def table_name_obs_instrument(inst_name):
    assert inst_name in config_data.INSTRUMENT_ID_TO_MISSION_ID
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
    if target_name.upper() in config_targets.TARGET_NAME_MAPPING:
        target_name = config_targets.TARGET_NAME_MAPPING[target_name.upper()]
    return encode_target_name(target_name)

# NOTE: whenever we change this function, we will have to change
# getSurfacegeoTargetSlug in JS code (in utils.js) as well.
def slug_name_for_sfc_target(target_name):
    if target_name.upper() in config_targets.TARGET_NAME_MAPPING:
        target_name = config_targets.TARGET_NAME_MAPPING[target_name.upper()]
    target_name = target_name.lower()
    target_name = target_name.replace('_', '').replace('/', '').replace(' ', '')
    return target_name

def read_schema_for_table(table_name, replace=[]):
    table_name = table_name.replace(opus_secrets.IMPORT_TABLE_TEMP_PREFIX, '').lower()
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

class NoDupLogger(pdslogger.PdsLogger):
    """Wrapper around PdsLogger that only logs each message one time.

    This is used for logging of PdsFile warnings that we don't want to see
    over and over."""

    _LOGGED_DEBUG = []
    _LOGGED_WARN = []
    _LOGGED_ERROR = []
    _LOGGED_FATAL = []

    def __init__(self, logger):
        self._logger = logger

    def debug(self, msg, *args, **kwargs):
        key = (msg, args, kwargs)
        if key in self._LOGGED_DEBUG:
            return
        self._LOGGED_DEBUG.append(key)
        self._logger.debug(msg, *args, **kwargs)

    def warn(self, msg, *args, **kwargs):
        key = (msg, args, kwargs)
        if key in self._LOGGED_WARN:
            return
        self._LOGGED_WARN.append(key)
        self._logger.warn(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        key = (msg, args, kwargs)
        if key in self._LOGGED_ERROR:
            return
        self._LOGGED_ERROR.append(key)
        self._logger.error(msg, *args, **kwargs)

    def fatal(self, msg, *args, **kwargs):
        key = (msg, args, kwargs)
        if key in self._LOGGED_FATAL:
            return
        self._LOGGED_FATAL.append(key)
        self._logger.fatal(msg, *args, **kwargs)


def _format_bundle_line():
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
    impglobals.LOGGER.log('error', _format_bundle_line()+msg, *args)
    impglobals.IMPORT_HAS_BAD_DATA = True

def log_warning(msg, *args):
    impglobals.LOGGER.log('warning', _format_bundle_line()+msg, *args)

def log_info(msg, *args):
    impglobals.LOGGER.log('info', _format_bundle_line()+msg, *args)

def log_debug(msg, *args):
    impglobals.LOGGER.log('debug', _format_bundle_line()+msg, *args)

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

def safe_join(*paths):
    return os.path.join(*paths).replace('\\', '/')
