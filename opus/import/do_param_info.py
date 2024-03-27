################################################################################
# do_param_info.py
#
# Generate and maintain the param_info table.
################################################################################

import json

import opus_support

import impglobals
import import_util


def create_import_param_info_table():
    db = impglobals.DATABASE
    logger = impglobals.LOGGER

    logger.log('info', 'Creating new import param_info table')
    pi_schema = import_util.read_schema_for_table('param_info')
    # Start from scratch
    db.drop_table('import', 'param_info')
    db.create_table('import', 'param_info', pi_schema, ignore_if_exists=False)

    # We use the permanent tables to determine what goes into param_info
    table_names = db.table_names('perm', prefix='obs_')

    # read json file for ranges info
    ranges_filename = import_util.safe_join('table_schemas', 'param_info_ranges.json')
    with open(ranges_filename, 'r') as fp:
        try:
            # read contents (str) and convert it to a json object (dict)
            contents = fp.read()
            ranges_json = json.loads(contents)
        except json.decoder.JSONDecodeError:
            logger.log('debug', f'Was reading ranges json file "{ranges_filename}"')
            raise
        except:
            raise

    rows = []
    for table_name in table_names:
        table_schema = import_util.read_schema_for_table(table_name)
        if table_schema is None:
            logger.log('error',
                       f'Unable to read table schema for "{table_name}"')
            return False
        for column in table_schema:
            category_name = column.get('pi_category_name', None)
            if category_name is None:
                continue
            field_name = column.get('field_name', None)
            form_type_str = column.get('pi_form_type', None)
            (form_type, form_type_format,
             form_type_unit_id) = opus_support.parse_form_type(form_type_str)
            if form_type_unit_id and not opus_support.is_valid_unit_id(form_type_unit_id):
                logger.log('error',
                           f'"{form_type_unit_id}" '
                           +f'in "{category_name}/{field_name}" is not '
                           +'a valid unit')
                return False
            # if pi_ranges exists in .json, get the corresponding ranges info
            # from dict and convert it to str before storing to database
            ranges = column.get('pi_ranges', None)
            if ranges:
                if ranges in ranges_json:
                    ranges = ranges_json[ranges]
                    ranges = json.dumps(ranges)
                else:
                    logger.log('error',
                               f'pi_ranges: "{ranges}" is not in "{ranges_filename}"')
                    return False

            new_row = {
                'category_name': category_name,
                'dict_context': column.get('pi_dict_context', None),
                'dict_name': column.get('pi_dict_name', None),
                'dict_context_results': column.get('pi_dict_context_results',
                                                   None),
                'dict_name_results': column.get('pi_dict_name_results',
                                                None),
                'disp_order': column['pi_disp_order'],
                'display': column['pi_display'],
                'display_results': column['pi_display_results'],
                'referred_slug': column.get('pi_referred_slug', None),
                'form_type': column.get('pi_form_type', None),
                'intro': column.get('pi_intro', None),
                'label': column.get('pi_label', None),
                'label_results': column.get('pi_label_results', None),
                'name': column.get('field_name', None),
                'slug': column.get('pi_slug', None),
                'old_slug': column.get('pi_old_slug', None),
                'sub_heading': column.get('pi_sub_heading', None),
                'tooltip': column.get('pi_tooltip', None),
                'ranges': ranges,
                'field_hints1': column.get('pi_field_hints1', None),
                'field_hints2': column.get('pi_field_hints2', None),
            }
            rows.append(new_row)
    db.insert_rows('import', 'param_info', rows)

    return True

def copy_param_info_from_import_to_permanent():
    db = impglobals.DATABASE
    logger = impglobals.LOGGER

    logger.log('info', 'Copying param_info table from import to permanent')
    # Start from scratch
    pi_schema = import_util.read_schema_for_table('param_info')
    db.drop_table('perm', 'param_info')
    db.create_table('perm', 'param_info', pi_schema, ignore_if_exists=False)

    db.copy_rows_between_namespaces('import', 'perm', 'param_info')


def do_param_info():
    if create_import_param_info_table():
        copy_param_info_from_import_to_permanent()
    impglobals.DATABASE.drop_table('import', 'param_info')
