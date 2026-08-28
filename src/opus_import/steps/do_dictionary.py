"""Build the ``definitions`` and ``contexts`` tables behind the UI's tooltips.

A definition is a term, the context it belongs to, and its prose. The terms come from
two places: the PDS data dictionary that ships with the package, and the ``definition``
entries in the packaged table schemas, which is where OPUS's own parameters and mult
values are described. A context names where a term came from, and exists so that the
same word can mean different things to different missions.

Neither table is touched by an ordinary import: this step runs only under
``--import-dictionary``, and is the last thing `opus_import.cli` does.
"""

from __future__ import annotations

import csv
import os
from importlib.resources import as_file
from typing import TYPE_CHECKING, Any

import pdsparser

from opus_import import import_util

if TYPE_CHECKING:
    from opus_import.context import ImportContext


def create_import_definitions_table(ctx: ImportContext) -> bool:
    """Fill the import ``definitions`` table from the dictionary and the table schemas.

    The packaged ``pdsdd.full`` contributes one row per dictionary item that has both a
    name and a description, all in the ``PSDD`` context; an item with no description is
    reported as a warning and skipped. Each packaged ``obs*``, ``internal_def*`` and
    ``mult_tooltips*`` schema then contributes a row per ``definition`` and
    ``definition_results`` entry it carries. The mult tooltip files also contribute
    their own rows to ``contexts``, one per file, named after the slug in the file name.

    Parameters:
        ctx: The import run's context, for the open database and the logger.

    Returns:
        True on success. False if the PDS dictionary could not be read, or a schema
        entry has a definition but no term or no context -- each of which is logged as
        an error. Every fault is found before returning, so one run reports all of them,
        and nothing is written to the database when any is found.
    """
    db = ctx.db
    assert db is not None
    logger = ctx.logger

    logger.log('info', 'Creating new import definitions table')
    def_schema = import_util.read_schema_for_table(ctx, 'definitions')
    # definitions.json is packaged with opus_import, so the schema is always found.
    assert def_schema is not None
    # Start from scratch
    db.create_table('import', 'definitions', def_schema, ignore_if_exists=False)

    bad_db = False

    pds_file = import_util.DICTIONARY_DATA_DIR / 'pdsdd.full'
    json_list = import_util.table_schema_files('obs*.json')
    json_list += import_util.table_schema_files('internal_def*.json')
    # Tooltips for mults
    mult_tooltips_json_list = import_util.table_schema_files('mult_tooltips*.json')
    json_list += mult_tooltips_json_list

    rows: list[dict[str, Any]] = []

    logger.log('info', f'Importing {pds_file}')

    context = 'PSDD'
    try:
        with as_file(pds_file) as pds_path:
            label = pdsparser.PdsLabel.from_file(pds_path)
    except OSError as e:
        logger.log('error', f'Failed to read {pds_file}: {e.strerror}')
        bad_db = True
    else:
        # pdsparser.PdsLabel is dict-like (keyed __getitem__) but not iterable,
        # so bare iteration falls back to integer indexing and raises; iterate
        # its keys explicitly.
        for item_name in label.keys():  # noqa: SIM118
            if item_name == 'objects' or label[item_name] is None:
                continue
            term = str(label[item_name]['NAME']).rstrip('\r\n')
            try:
                definition = ' '.join(str(label[item_name]['DESCRIPTION']).split())
            except KeyError:
                logger.log('warning', f'No description for item {item_name}: "{term}"')
                continue
            new_row = {'term': term, 'context': context, 'definition': definition}
            rows.append(new_row)

    for schema_file in json_list:
        file_name = os.path.splitext(schema_file.name)[0]
        logger.log('info', f'Importing {file_name}')
        schema = import_util.read_schema_for_table(ctx, file_name)
        # The file name came from a listing of the packaged schema directory.
        assert schema is not None
        for column in schema:
            for suffix in ('', '_results'):
                if 'definition' + suffix in column:
                    definition = column['definition' + suffix]
                    if column.get('pi_dict_name' + suffix, None) is None:
                        logger.log('error', f'Missing term for "{definition}" in "{file_name}"')
                        bad_db = True
                        continue
                    term = column['pi_dict_name' + suffix]
                    if column.get('pi_dict_context' + suffix, None) is None:
                        logger.log('error', f'Missing context for "{definition}" in "{file_name}"')
                        bad_db = True
                        continue
                    context = column['pi_dict_context' + suffix]

                    new_row = {'term': term, 'context': context, 'definition': definition}
                    rows.append(new_row)

    if bad_db:
        return False

    # create entries in contexts table for mults tooltips
    mult_tp_ctx_rows: list[dict[str, Any]] = []
    for tooltips_file in mult_tooltips_json_list:
        name = tooltips_file.name
        slug = name[name.rindex('_') + 1 : -5]
        new_row = {
            'name': f'MULT_{slug.upper()}',
            'description': f'OPUS {slug.title()}',
            'parent': 'NULL',
        }
        mult_tp_ctx_rows.append(new_row)

    db.insert_rows('import', 'contexts', mult_tp_ctx_rows)
    db.insert_rows('import', 'definitions', rows)

    return True


def create_import_contexts_table(ctx: ImportContext) -> bool:
    """Fill the import ``contexts`` table from the packaged ``contexts.csv``.

    Each line of the file is a context's name, its description and the name of its
    parent context.

    Parameters:
        ctx: The import run's context, for the open database and the logger.

    Returns:
        True on success. False if the file could not be read or any line does not have
        exactly three fields, either of which is logged as an error. A bad line stops
        the read, so nothing is written.
    """
    db = ctx.db
    assert db is not None
    logger = ctx.logger

    logger.log('info', 'Creating new import contexts table')
    contexts_schema = import_util.read_schema_for_table(ctx, 'contexts')
    # contexts.json is packaged with opus_import, so the schema is always found.
    assert contexts_schema is not None
    # Start from scratch
    db.create_table('import', 'contexts', contexts_schema, ignore_if_exists=False)

    contexts_file = import_util.DICTIONARY_DATA_DIR / 'contexts.csv'
    rows: list[dict[str, Any]] = []
    try:
        with contexts_file.open(encoding='utf-8') as csvfile:
            filereader = csv.reader(csvfile)
            for row in filereader:
                if len(row) != 3:
                    logger.log('error', f'Bad row in "{contexts_file}": {row}')
                    return False
                name, description, parent = row
                new_row = {'name': name, 'description': description, 'parent': parent}
                rows.append(new_row)
    except OSError as e:
        logger.log('error', f'Failed to read {contexts_file}: {e.strerror}')
        return False

    db.insert_rows('import', 'contexts', rows)

    return True


def copy_dictionary_from_import_to_permanent(ctx: ImportContext) -> None:
    """Replace the permanent dictionary tables with the import ones.

    ``definitions`` has a foreign key onto ``contexts``, so it is dropped first and
    created last.

    Parameters:
        ctx: The import run's context, for the open database and the logger.
    """
    db = ctx.db
    assert db is not None
    logger = ctx.logger

    logger.log('info', 'Copying contexts table from import to permanent')
    # Start from scratch
    contexts_schema = import_util.read_schema_for_table(ctx, 'contexts')
    # contexts.json is packaged with opus_import, so the schema is always found.
    assert contexts_schema is not None
    db.drop_table('perm', 'definitions')
    db.drop_table('perm', 'contexts')
    db.create_table('perm', 'contexts', contexts_schema, ignore_if_exists=False)

    db.copy_rows_between_namespaces('import', 'perm', 'contexts')

    logger.log('info', 'Copying definitions table from import to permanent')
    # Start from scratch
    def_schema = import_util.read_schema_for_table(ctx, 'definitions')
    # definitions.json is packaged with opus_import, so the schema is always found.
    assert def_schema is not None
    db.create_table('perm', 'definitions', def_schema, ignore_if_exists=False)

    db.copy_rows_between_namespaces('import', 'perm', 'definitions')


def do_dictionary(ctx: ImportContext) -> None:
    """Rebuild the permanent dictionary tables, driven by ``--import-dictionary``.

    The import tables are dropped both before and after, so a failed build leaves
    nothing behind and the permanent tables keep what the previous run wrote.

    Parameters:
        ctx: The import run's context, for the open database and the logger.
    """
    db = ctx.db
    assert db is not None
    # Contexts has to come first because of a foreign key
    db.drop_table('import', 'definitions')
    db.drop_table('import', 'contexts')
    if create_import_contexts_table(ctx) and create_import_definitions_table(ctx):
        copy_dictionary_from_import_to_permanent(ctx)
    db.drop_table('import', 'definitions')
    db.drop_table('import', 'contexts')
