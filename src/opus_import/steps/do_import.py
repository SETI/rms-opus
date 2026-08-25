"""The observation import: read the PDS holdings and fill the import tables.

This is the step behind ``--import`` and the several options that imply it. It also owns
the work for three options that are not steps of their own -- dropping the permanent
tables under ``--drop-permanent-tables``, deleting bundles from the import tables under
``--delete-import-bundles``, and analyzing the permanent tables under
``--analyze-permanent-tables`` -- because each of them has to happen at a particular
point in this sequence.

Everything is written to the import namespace first and copied over the permanent tables
only once the whole run has succeeded, so a failed import cannot leave the web
application serving half a bundle. An error anywhere aborts before that copy, unless
``--import-ignore-errors`` says otherwise.

The per-bundle work is split across four modules that are not steps of their own:
`opus_import.steps.do_import_tables` prepares the tables,
`opus_import.steps.do_import_index` walks one index file,
`opus_import.steps.do_import_obs` computes one row, and
`opus_import.steps.do_import_mult` maintains the enumerated-value tables.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import pdsfile

from opus_import import import_util
from opus_import.steps import (
    do_cart,
    do_django,
    do_import_index,
    do_import_mult,
    do_import_tables,
)

if TYPE_CHECKING:
    from opus_import.context import ImportContext

################################################################################
# TOP-LEVEL IMPORT ROUTINES
################################################################################

def import_one_bundle(ctx: ImportContext, bundle_id: str) -> bool:
    """Import one bundle into the import namespace.

    The bundle's primary index files are found by looking through its metadata
    directories, and for PDS3 its own ``index`` directory as well, for the file names
    `opus_import.config_bundle_info` says to expect. Every index found in the first
    directory that has one is imported; later directories are not searched, so a bundle
    whose indexes are split across directories imports only the first group.

    Parameters:
        ctx: The import run's context, which is reset to this bundle here.
        bundle_id: The bundle to import.

    Returns:
        True if the bundle imported, and also if OPUS deliberately ignores it -- an
        entry with no instrument class is one OPUS knows about and does not import.
        False if the bundle is unknown, is not a bundle, has an unsupported PDS version,
        no index file was found, or an index failed to import.
    """
    ctx.logger.open(f'Importing {bundle_id}',
                    limits={'info': ctx.args.log_info_limit,
                            'debug': ctx.args.log_debug_limit})

    # Start fresh
    ctx.mult_table_cache = {}
    ctx.modified_mult_tables = set()
    ctx.max_table_id_cache = {}
    ctx.current_bundle_id = bundle_id
    ctx.current_index_row_number = None
    ctx.current_primary_filespec = None

    vol_info = do_import_tables.lookup_vol_info(bundle_id)
    if vol_info is None:
        import_util.log_error(ctx, f'No BUNDLE_INFO entry for {bundle_id}!')
        ctx.logger.close()
        ctx.current_bundle_id = None
        return False
    if vol_info['instrument_class'] is None:
        import_util.log_debug(ctx, f'Ignoring import of {bundle_id}')
        ctx.logger.close()
        ctx.current_bundle_id = None
        return True

    if vol_info['pds_version'] == 3:
        bundle_pdsfile = pdsfile.pds3file.Pds3File.from_path(bundle_id)
    elif vol_info['pds_version'] == 4:
        # This works fine for Uranus Occs Earthbased, where bundleset and bundle have
        # different names
        bundle_pdsfile = pdsfile.pds4file.Pds4File.from_path(bundle_id)
        if not bundle_pdsfile.is_bundle:
            # Handle the case where the bundleset and bundle have the same name, in
            # which case PdsFile prefers the bundleset, but we want to prefer the bundle
            bundle_pdsfile = pdsfile.pds4file.Pds4File.from_path(f'bundles/{bundle_id}/{bundle_id}')
    else:
        import_util.log_error(ctx, f'BUNDLE_INFO has illegal PDS version for {bundle_id}!')
        return False


    if not bundle_pdsfile.is_bundle:
        import_util.log_error(ctx, f'{bundle_id} is not a bundle!')
        ctx.logger.close()
        ctx.current_bundle_id = None
        return False


    ##################################
    ### FIND PRIMARY INDEX FILE(s) ###
    ##################################

    primary_index_names = [
        x.replace('<BUNDLE>', bundle_id) for x in vol_info['primary_index']]

    # These are the metadata directories
    index_paths = bundle_pdsfile.associated_abspaths('metadata', must_exist=True)

    if vol_info['pds_version'] == 3:
        # These are the plain <volume>/index directories for PDS3 volumes that
        # don't have a separate metadata directory
        index_paths.append(import_util.safe_join(bundle_pdsfile.abspath, 'INDEX'))
        index_paths.append(import_util.safe_join(bundle_pdsfile.abspath, 'index'))
    found_in_this_dir = False

    for path in index_paths:
        if not os.path.exists(path):
            continue
        basenames = os.listdir(path)
        ret = True
        for basename in basenames:
            if basename in primary_index_names:
                bundle_label_path = import_util.safe_join(path, basename)
                import_util.log_debug(ctx, f'Using index: {bundle_label_path}')
                found_in_this_dir = True
                ret = ret and do_import_index.import_one_index(ctx, bundle_id,
                                                               vol_info,
                                                               index_paths,
                                                               bundle_label_path)
        if found_in_this_dir:
            ctx.logger.close()
            ctx.current_bundle_id = None
            ctx.current_index_row_number = None
            ctx.current_primary_filespec = None
            return ret

    import_util.log_error(ctx, f'No index label file found: "{bundle_id}" - searched in:')
    for path in index_paths:
        import_util.log_error(ctx, f'    {path}')
    ctx.logger.close()
    ctx.current_bundle_id = None

    return False


################################################################################
# THE MAIN IMPORT LOOP
################################################################################

def do_import_steps(ctx: ImportContext) -> bool:
    """Run the import work the command line asked for, in the one order that is safe.

    The order is fixed by the foreign keys and by what each step needs to already exist:
    the old import tables are dropped, then the permanent tables if ``--scorched-earth``
    confirms it, then the bundles are imported, then the permanent tables get the
    bundles the import produced -- deleted first, then created, then copied -- and
    finally the import tables are dropped and the permanent ones analyzed.

    The copy to the permanent tables is skipped when the import logged any error, so a
    run that produced bad data leaves the web application on the previous import.
    ``--import-ignore-errors`` overrides that, and also keeps the run going past a
    bundle that failed.

    Parameters:
        ctx: The import run's context, whose per-run caches are reset here.

    Returns:
        True if everything asked for succeeded. False if a bundle failed and errors are
        not being ignored, which is logged.
    """
    ctx.import_has_bad_data = False
    ctx.max_table_id_cache = {}
    ctx.created_import_mult_tables = set()

    bundle_id_list = []
    for bundle_id in import_util.yield_import_bundle_ids(ctx):
        bundle_id_list.append(bundle_id)

    # Delete the old import tables if
    #   --drop-old-import-tables but not
    #   --leave-old-import-tables
    # is given.
    old_imp_tables_dropped = False
    if (ctx.args.drop_old_import_tables and
        not ctx.args.leave_old_import_tables):
        import_util.log_info(ctx, 'Deleting all old import tables')
        do_import_tables.delete_all_obs_mult_tables(ctx, 'import')
        old_imp_tables_dropped = True

    # If --drop-permanent-tables AND --scorched-earth is given, delete
    # the permanent tables entirely. We have to do this before starting the
    # real import so that there are no vestigial mult tables and the ids
    # can be reset to 0.
    old_perm_tables_dropped = False
    if (ctx.args.drop_permanent_tables and
        ctx.args.scorched_earth):
        import_util.log_warning(ctx, '** DELETING ALL PERMANENT TABLES **')
        do_import_tables.delete_all_obs_mult_tables(ctx, 'perm')
        old_perm_tables_dropped = True

        # This must be done after the permanent tables were deleted, since
        # that process also deleted these tables. In this case, we didn't do
        # this step earlier.
        if (ctx.args.drop_cache_tables or
            ctx.args.create_cart):
            ctx.logger.open(
                'Cleaning up OPUS/Django tables',
                limits={'info': ctx.args.log_info_limit,
                        'debug': ctx.args.log_debug_limit})

            if ctx.args.create_cart:
                do_cart.create_cart(ctx)
            if ctx.args.drop_cache_tables:
                do_django.drop_cache_tables(ctx)

            ctx.logger.close()

    # If --import is given, first delete the bundles from the import tables,
    # then do the new import
    if (ctx.args.do_import or
        ctx.args.delete_import_bundles) and not old_imp_tables_dropped:
        import_util.log_warning(ctx, 'Importing on top of previous import tables!')
        for bundle_id in import_util.yield_import_bundle_ids(ctx):
            do_import_tables.delete_bundle_from_obs_tables(ctx, bundle_id, 'import')

    if ctx.args.do_import:
        for bundle_id in bundle_id_list:
            if not import_one_bundle(ctx, bundle_id):
                ctx.logger.log('fatal',
                               f'Import of bundle {bundle_id} failed - Aborting')
                ctx.import_has_bad_data = True
                if not ctx.args.import_ignore_errors:
                    break

        if (ctx.import_has_bad_data and
            not ctx.args.import_ignore_errors):
            ctx.logger.log('fatal',
                           'ERRORs found during import - aborting early')
            return False

    # If --copy-import-to-permanent-tables or --delete-permanent-import-bundles
    # are given, delete all bundles that exist in the import tables from the
    # permanent tables.
    db = ctx.db
    assert db is not None
    import_bundle_ids = []
    if ((ctx.args.copy_import_to_permanent_tables or
         ctx.args.delete_permanent_import_bundles) and
        db.table_exists('import', 'obs_general')):
        imp_obs_general_table_name = (
            db.convert_raw_to_namespace('import', 'obs_general'))
        q = db.quote_identifier
        import_bundle_ids = [x[0] for x in
                      db.general_select(
    f'DISTINCT {q("bundle_id")} FROM {q(imp_obs_general_table_name)} ORDER BY {q("bundle_id")}')
                     ]
        if not old_perm_tables_dropped:
            # Don't bother if there's nothing there!
            if not ctx.args.create_cart:
                import_util.log_warning(
                        ctx,
                        'Deleting bundles from perm tables but cart table not wiped')
            for bundle_id in import_bundle_ids:
                do_import_tables.delete_bundle_from_obs_tables(ctx, bundle_id, 'perm')

    # If --delete-permanent-bundles is given, delete the given set of bundles
    # from the permanent tables.
    if ctx.args.delete_permanent_bundles:
        for bundle_id in bundle_id_list:
            do_import_tables.delete_bundle_from_obs_tables(ctx, bundle_id, 'perm')

    # If --copy-import-to-permanent-tables is given, create obs and mult tables
    # as necessary, then copy the import tables to the permanent tables.
    if ctx.args.copy_import_to_permanent_tables:
        for bundle_id in import_bundle_ids:
            do_import_tables.create_tables_for_import(ctx, bundle_id, 'perm')

        import_util.log_info(ctx, 'Deleting duplicate opus_ids')
        do_import_tables.delete_duplicate_opus_id_from_perm_tables(ctx)

        import_util.log_info(ctx, 'Copying import mult tables to permanent')
        do_import_mult.copy_mult_from_import_to_permanent(ctx)

        for bundle_id in import_bundle_ids:
            do_import_tables.copy_bundle_from_import_to_permanent(ctx, bundle_id)

    # If --drop-new-import-tables is given, delete the new import tables
    if ctx.args.drop_new_import_tables:
        import_util.log_info(ctx, 'Deleting all new import tables')
        do_import_tables.delete_all_obs_mult_tables(ctx, 'import')

    # If --analyze-permanent-tables is given, analyze the permanent tables
    if ctx.args.analyze_permanent_tables:
        import_util.log_info(ctx, 'Analyzing all permanent tables')
        do_import_tables.analyze_all_tables(ctx, 'perm')

    return True
