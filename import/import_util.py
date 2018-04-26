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
import pdslogger
import pdsparser
import pdstable

from secrets import *
from config_data import *
import impglobals
import instruments

################################################################################
# GENERAL UTILITIES
################################################################################

def yield_import_volume_ids(arguments):
    if arguments.volumes:
        volume_descs = arguments.volumes.split(',')
        # First make sure everything is valid
        any_invalid = False
        for volume_desc in volume_descs:
            try:
                volume_pdsfile = pdsfile.PdsFile.from_path(volume_desc)
            except (KeyError, ValueError):
                any_invalid = True
                impglobals.LOGGER.log('fatal',
                           f'Bad volume descriptor {volume_desc}')
            else:
                if (not volume_pdsfile.is_volume_dir() and
                    not volume_pdsfile.is_volset_dir()):
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
            if volume_pdsfile.is_volset_dir():
                new_voldescs += volume_pdsfile.childnames
            else:
                new_voldescs.append(volume_desc)
        new_voldescs.sort()
        # Now actually return the volume_ids
        for volume_id in new_voldescs:
            yield volume_id

def log_accumulated_warnings(title):
    if len(impglobals.PYTHON_WARNING_LIST) > 0:
        impglobals.LOGGER.log('error',
                   f'Warnings found during {title}:')
        for w in impglobals.PYTHON_WARNING_LIST:
            impglobals.LOGGER.log('error', '  '+w)
        impglobals.PYTHON_WARNING_LIST = []
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
    print(replacements)
    try:
        if preprocess_label_func is None:
            table = pdstable.PdsTable(filename, replacements=replacements,
                                      table_callback=
                                            preprocess_table_func)
        else:
            lines = pdsparser.PdsLabel.load_file(filename)
            lines = preprocess_label_func(lines)
            table = pdstable.PdsTable(filename, label_contents=lines,
                                      replacements=replacements,
                                      table_callback=
                                            preprocess_table_func)

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

    return table.dicts_by_row(), table.info.label.as_dict()

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

def read_schema_for_table(table_name, replace=None):
    table_name = table_name.replace(IMPORT_TABLE_TEMP_PREFIX, '').lower()
    if table_name.startswith('obs_surface_geometry__'):
        assert replace is None
        target_name = table_name.replace('obs_surface_geometry__', '')
        table_name = 'obs_surface_geometry_target'
        replace = ('<TARGET>', target_name)
    with open(os.path.join('table_schemas', table_name+'.json'), 'r') as fp:
        try:
            if replace is None:
                return json.load(fp)
            contents = fp.read()
            contents = contents.replace(replace[0], replace[1])
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

def announce_nonrepeating_error(msg, index_row_num=None):
    if index_row_num is not None:
        msg += f' [line {index_row_num}]'
    short_msg = msg
    if msg.find(' [line') != -1:
        short_msg = short_msg[:msg.find(' [line')]
    if short_msg not in impglobals.ANNOUNCED_IMPORT_ERRORS:
        impglobals.ANNOUNCED_IMPORT_ERRORS.append(short_msg)
        impglobals.LOGGER.log('error', msg)
        impglobals.IMPORT_HAS_BAD_DATA = True

def announce_nonrepeating_warning(msg, index_row_num=None):
    if index_row_num is not None:
        msg += f' [line {index_row_num}]'
    short_msg = msg
    if msg.find(' [line') != -1:
        short_msg = short_msg[:msg.find(' [line')]
    if short_msg not in impglobals.ANNOUNCED_IMPORT_WARNINGS:
        impglobals.ANNOUNCED_IMPORT_WARNINGS.append(short_msg)
        impglobals.LOGGER.log('warning', msg)

def announce_unknown_target_name(target_name, index_row_num=None):
    msg = f'Unknown TARGET_NAME "{target_name}" - edit data_config.py'
    if index_row_num is not None:
        msg += f' [line {index_row_num}]'
    announce_nonrepeating_error(msg)

def announce_no_data_source_for_column(table_name, column_name):
    announce_nonrepeating_error(msg)
