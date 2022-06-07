################################################################################
# do_dictionary.py
#
# Generate and maintain the dictionary (definitions and contexts tables)
################################################################################

import csv
import glob
import os

import pdsparser

import impglobals
import import_util
import opus_secrets

def create_import_definitions_table():
    db = impglobals.DATABASE
    logger = impglobals.LOGGER

    logger.log('info', 'Creating new import definitions table')
    def_schema = import_util.read_schema_for_table('definitions')
    # Start from scratch
    db.create_table('import', 'definitions', def_schema, ignore_if_exists=False)

    bad_db = False

    pds_file = opus_secrets.DICTIONARY_PDSDD_FILE
    json_schema_path = opus_secrets.DICTIONARY_JSON_SCHEMA_PATH + '/obs*.json'
    json_list = glob.glob(json_schema_path)
    json_def_path = (opus_secrets.DICTIONARY_JSON_SCHEMA_PATH +
                     '/internal_def*.json')
    json_list += glob.glob(json_def_path)
    # Tooltips for mult 
    json_tooltips_def_path = (opus_secrets.DICTIONARY_JSON_SCHEMA_PATH +
                     '/mult_tooltips.json')
    json_list += glob.glob(json_tooltips_def_path)
    rows = []

    logger.log('info', f'Importing {pds_file}')

    context = 'PSDD'
    try:
        label = pdsparser.PdsLabel.from_file(pds_file)
    except IOError as e:
        logger.log('error', f'Failed to read {pds_file}: {e.strerror}')
        bad_db = True
    else:
        for item in range(len(label)):
            term = str(label[item]['NAME']).rstrip('\r\n')
            try:
                definition = ' '.join(str(label[item]['DESCRIPTION']).split())
            except KeyError:
                logger.log('warning',
                           f'No description for item {item}: "{term}"')
                continue
            new_row = {
                'term': term,
                'context': context,
                'definition': definition
            }
            rows.append(new_row)

    for file_path in json_list:
        file_name = os.path.basename(file_path)
        file_name = os.path.splitext(file_name)[0]
        logger.log('info', f'Importing {file_name}')
        schema = import_util.read_schema_for_table(file_name)
        for column in schema:
            for suffix in ('', '_results'):
                if 'definition'+suffix in column:
                    definition = column['definition'+suffix]
                    if column.get('pi_dict_name'+suffix, None) is None:
                        logger.log('error',
                           f'Missing term for "{definition}" in "{file_name}"')
                        bad_db = True
                        continue
                    term = column['pi_dict_name'+suffix]
                    if column.get('pi_dict_context'+suffix, None) is None:
                        logger.log('error',
                         f'Missing context for "{definition}" in "{file_name}"')
                        bad_db = True
                        continue
                    context = column['pi_dict_context'+suffix]

                    new_row = {
                        'term': term,
                        'context': context,
                        'definition': definition
                    }
                    rows.append(new_row)

    if bad_db:
        return False

    db.insert_rows('import', 'definitions', rows)

    return True

def create_import_contexts_table():
    db = impglobals.DATABASE
    logger = impglobals.LOGGER

    logger.log('info', 'Creating new import contexts table')
    ctx_schema = import_util.read_schema_for_table('contexts')
    # Start from scratch
    db.create_table('import', 'contexts', ctx_schema, ignore_if_exists=False)

    ctx_file = opus_secrets.DICTIONARY_CONTEXTS_FILE
    rows = []
    try:
        with open(ctx_file, 'r') as csvfile:
            filereader = csv.reader(csvfile)
            for row in filereader:
                if len(row) != 3:
                    logger.log('error', 'Bad row in "{ctxfile}": {row}')
                    return False
                name, description, parent = row
                new_row = {
                    'name': name,
                    'description': description,
                    'parent': parent
                }
                rows.append(new_row)
    except IOError as e:
        logger.log('error', f'Failed to read {ctx_file}: {e.strerror}')
        return False

    db.insert_rows('import', 'contexts', rows)

    return True


def copy_dictionary_from_import_to_permanent():
    db = impglobals.DATABASE
    logger = impglobals.LOGGER

    logger.log('info', 'Copying contexts table from import to permanent')
    # Start from scratch
    ctx_schema = import_util.read_schema_for_table('contexts')
    db.drop_table('perm', 'definitions')
    db.drop_table('perm', 'contexts')
    db.create_table('perm', 'contexts', ctx_schema, ignore_if_exists=False)

    db.copy_rows_between_namespaces('import', 'perm', 'contexts')

    logger.log('info', 'Copying definitions table from import to permanent')
    # Start from scratch
    def_schema = import_util.read_schema_for_table('definitions')
    db.create_table('perm', 'definitions', def_schema, ignore_if_exists=False)

    db.copy_rows_between_namespaces('import', 'perm', 'definitions')

def do_dictionary():
    # Contexts has to come first because of a foreign key
    impglobals.DATABASE.drop_table('import', 'definitions')
    impglobals.DATABASE.drop_table('import', 'contexts')
    if (create_import_contexts_table() and
        create_import_definitions_table()):
        copy_dictionary_from_import_to_permanent()
    impglobals.DATABASE.drop_table('import', 'definitions')
    impglobals.DATABASE.drop_table('import', 'contexts')
