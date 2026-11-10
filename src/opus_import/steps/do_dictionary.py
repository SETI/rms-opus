"""Build the ``definitions`` and ``contexts`` tables behind the UI's tooltips.

A definition is a term, the context it belongs to, and its prose. The terms come from the
``definition`` entries in the packaged table schemas, which is where OPUS's own
parameters and mult values are described. A context names where a term came from, and
exists so that the same word can mean different things to different missions.

Neither table is touched by an ordinary import: this step runs only under
``--import-dictionary``. The two tables are built beside the live ones and swapped in
together (`opus_import.table_swap`), so a reader never finds the dictionary missing or
partly filled, and ``definitions``' foreign key onto ``contexts`` follows the swap.
"""

from __future__ import annotations

import csv
import os
from typing import TYPE_CHECKING, Any

from opus_import import import_util, table_swap

if TYPE_CHECKING:
    from opus_import.context import ImportContext


def fill_definitions(ctx: ImportContext, definitions_table: str, contexts_table: str) -> bool:
    """Fill an empty ``definitions`` table from the table schemas.

    Each packaged ``obs*``, ``internal_def*`` and ``mult_tooltips*`` schema contributes a
    row per ``definition`` and ``definition_results`` entry it carries, filed under the
    ``pi_dict_context`` beside it. The mult tooltip files also contribute their own rows
    to ``contexts``, one per file, named after the slug in the file name.

    The schemas are the whole source. Every tooltip the application asks for is looked up
    under a context one of them names, or under ``OPUS_PRODUCT_TYPE``, and those are the
    contexts filled here.

    Parameters:
        ctx: The import run's context, for the open database and the logger.
        definitions_table: The table to fill, already created from
            ``definitions``' schema with its foreign key onto ``contexts_table``.
        contexts_table: The ``contexts`` table being built beside it, which gains the
            mult tooltip contexts.

    Returns:
        True on success. False if a schema entry has a definition but no term or no
        context -- each of which is logged as an error. Every fault is found before
        returning, so one run reports all of them, and nothing is written to the database
        when any is found.
    """
    db = ctx.db
    assert db is not None
    logger = ctx.logger

    logger.log('info', f'Filling {definitions_table}')

    bad_db = False

    json_list = import_util.table_schema_files('obs*.json')
    json_list += import_util.table_schema_files('internal_def*.json')
    # Tooltips for mults
    mult_tooltips_json_list = import_util.table_schema_files('mult_tooltips*.json')
    json_list += mult_tooltips_json_list

    rows: list[dict[str, Any]] = []

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

    db.insert_rows(contexts_table, mult_tp_ctx_rows)
    db.insert_rows(definitions_table, rows)

    return True


def fill_contexts(ctx: ImportContext, new_table: str) -> bool:
    """Fill an empty ``contexts`` table from the packaged ``contexts.csv``.

    Each line of the file is a context's name, its description and the name of its
    parent context.

    Parameters:
        ctx: The import run's context, for the open database and the logger.
        new_table: The table to fill, already created from ``contexts``'
            schema.

    Returns:
        True on success. False if the file could not be read or any line does not have
        exactly three fields, either of which is logged as an error. A bad line stops
        the read, so nothing is written.
    """
    db = ctx.db
    assert db is not None
    logger = ctx.logger

    logger.log('info', f'Filling {new_table}')

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

    db.insert_rows(new_table, rows)

    return True


def do_dictionary(ctx: ImportContext) -> bool:
    """Rebuild the dictionary tables, driven by ``--import-dictionary``.

    A failed build leaves the live tables as the previous run wrote them.

    Parameters:
        ctx: The import run's context, for the open database and the logger.

    Returns:
        True if both tables were rebuilt, False if a build failed, having logged why.
    """
    contexts_table = table_swap.swap_new_name('contexts')
    definitions_table = table_swap.swap_new_name('definitions')
    return table_swap.rebuild_tables_by_swap(
        ctx,
        ['contexts', 'definitions'],
        lambda: (
            fill_contexts(ctx, contexts_table)
            and fill_definitions(ctx, definitions_table, contexts_table)
        ),
    )
