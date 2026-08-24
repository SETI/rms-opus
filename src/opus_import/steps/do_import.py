################################################################################
# do_import.py
#
# This is the actual top-level import process.
################################################################################

import os

import pdsfile

from opus_import import impglobals, import_util
from opus_import.steps import (
    do_cart,
    do_django,
    do_import_index,
    do_import_mult,
    do_import_tables,
)

################################################################################
# TOP-LEVEL IMPORT ROUTINES
################################################################################

def import_one_bundle(bundle_id):
    """Read the PDS data and perform all import functions for one bundle.
       The results are left in the import namespace."""
    impglobals.LOGGER.open(f'Importing {bundle_id}',
                           limits={'info': impglobals.ARGUMENTS.log_info_limit,
                                   'debug': impglobals.ARGUMENTS.log_debug_limit})

    # Start fresh
    do_import_mult.reset_bundle_mult_cache()
    impglobals.ANNOUNCED_IMPORT_WARNINGS = []
    impglobals.ANNOUNCED_IMPORT_ERRORS = []
    impglobals.MAX_TABLE_ID_CACHE = {}
    impglobals.CURRENT_BUNDLE_ID = bundle_id
    impglobals.CURRENT_INDEX_ROW_NUMBER = None
    impglobals.CURRENT_PRIMARY_FILESPEC = None

    vol_info = do_import_tables.lookup_vol_info(bundle_id)
    if vol_info is None:
        import_util.log_error(f'No BUNDLE_INFO entry for {bundle_id}!')
        impglobals.LOGGER.close()
        impglobals.CURRENT_BUNDLE_ID = None
        return False
    if vol_info['instrument_class'] is None:
        import_util.log_debug(f'Ignoring import of {bundle_id}')
        impglobals.LOGGER.close()
        impglobals.CURRENT_BUNDLE_ID = None
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
        import_util.log_error(f'BUNDLE_INFO has illegal PDS version for {bundle_id}!')
        return False


    if not bundle_pdsfile.is_bundle:
        import_util.log_error(f'{bundle_id} is not a bundle!')
        impglobals.LOGGER.close()
        impglobals.CURRENT_BUNDLE_ID = None
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
                import_util.log_debug(f'Using index: {bundle_label_path}')
                found_in_this_dir = True
                ret = ret and do_import_index.import_one_index(bundle_id,
                                                               vol_info,
                                                               index_paths,
                                                               bundle_label_path)
        if found_in_this_dir:
            impglobals.LOGGER.close()
            impglobals.CURRENT_BUNDLE_ID = None
            impglobals.CURRENT_INDEX_ROW_NUMBER = None
            impglobals.CURRENT_PRIMARY_FILESPEC = None
            return ret

    import_util.log_error(f'No index label file found: "{bundle_id}" - searched in:')
    for path in index_paths:
        import_util.log_error(f'    {path}')
    impglobals.LOGGER.close()
    impglobals.CURRENT_BUNDLE_ID = None

    return False


################################################################################
# THE MAIN IMPORT LOOP
################################################################################

def do_import_steps():
    "Do all of the steps requested by the user for an import."
    impglobals.IMPORT_HAS_BAD_DATA = False
    impglobals.MAX_TABLE_ID_CACHE = {}
    do_import_mult.reset_created_import_mult_tables()

    bundle_id_list = []
    for bundle_id in import_util.yield_import_bundle_ids(impglobals.ARGUMENTS):
        bundle_id_list.append(bundle_id)

    # Delete the old import tables if
    #   --drop-old-import-tables but not
    #   --leave-old-import-tables
    # is given.
    old_imp_tables_dropped = False
    if (impglobals.ARGUMENTS.drop_old_import_tables and
        not impglobals.ARGUMENTS.leave_old_import_tables):
        import_util.log_info('Deleting all old import tables')
        do_import_tables.delete_all_obs_mult_tables('import')
        old_imp_tables_dropped = True

    # If --drop-permanent-tables AND --scorched-earth is given, delete
    # the permanent tables entirely. We have to do this before starting the
    # real import so that there are no vestigial mult tables and the ids
    # can be reset to 0.
    old_perm_tables_dropped = False
    if (impglobals.ARGUMENTS.drop_permanent_tables and
        impglobals.ARGUMENTS.scorched_earth):
        import_util.log_warning('** DELETING ALL PERMANENT TABLES **')
        do_import_tables.delete_all_obs_mult_tables('perm')
        old_perm_tables_dropped = True

        # This must be done after the permanent tables were deleted, since
        # that process also deleted these tables. In this case, we didn't do
        # this step earlier.
        if (impglobals.ARGUMENTS.drop_cache_tables or
            impglobals.ARGUMENTS.create_cart):
            impglobals.LOGGER.open(
                'Cleaning up OPUS/Django tables',
                limits={'info': impglobals.ARGUMENTS.log_info_limit,
                        'debug': impglobals.ARGUMENTS.log_debug_limit})

            if impglobals.ARGUMENTS.create_cart:
                do_cart.create_cart()
            if impglobals.ARGUMENTS.drop_cache_tables:
                do_django.drop_cache_tables()

            impglobals.LOGGER.close()

    # If --import is given, first delete the bundles from the import tables,
    # then do the new import
    if (impglobals.ARGUMENTS.do_import or
        impglobals.ARGUMENTS.delete_import_bundles) and not old_imp_tables_dropped:
        import_util.log_warning('Importing on top of previous import tables!')
        for bundle_id in import_util.yield_import_bundle_ids(
                                                impglobals.ARGUMENTS):
            do_import_tables.delete_bundle_from_obs_tables(bundle_id, 'import')

    if impglobals.ARGUMENTS.do_import:
        for bundle_id in bundle_id_list:
            if not import_one_bundle(bundle_id):
                impglobals.LOGGER.log('fatal',
                        f'Import of bundle {bundle_id} failed - Aborting')
                impglobals.IMPORT_HAS_BAD_DATA = True
                if not impglobals.ARGUMENTS.import_ignore_errors:
                    break

        if (impglobals.IMPORT_HAS_BAD_DATA and
            not impglobals.ARGUMENTS.import_ignore_errors):
            impglobals.LOGGER.log('fatal',
                                  'ERRORs found during import - aborting early')
            return False

    # If --copy-import-to-permanent-tables or --delete-permanent-import-bundles
    # are given, delete all bundles that exist in the import tables from the
    # permanent tables.
    import_bundle_ids = []
    if ((impglobals.ARGUMENTS.copy_import_to_permanent_tables or
         impglobals.ARGUMENTS.delete_permanent_import_bundles) and
        impglobals.DATABASE.table_exists('import', 'obs_general')):
        imp_obs_general_table_name = (
            impglobals.DATABASE.convert_raw_to_namespace('import',
                                                         'obs_general'))
        q = impglobals.DATABASE.quote_identifier
        import_bundle_ids = [x[0] for x in
                      impglobals.DATABASE.general_select(
    f'DISTINCT {q("bundle_id")} FROM {q(imp_obs_general_table_name)} ORDER BY {q("bundle_id")}')
                     ]
        if not old_perm_tables_dropped:
            # Don't bother if there's nothing there!
            if not impglobals.ARGUMENTS.create_cart:
                import_util.log_warning(
                        'Deleting bundles from perm tables but cart table not wiped')
            for bundle_id in import_bundle_ids:
                do_import_tables.delete_bundle_from_obs_tables(bundle_id, 'perm')

    # If --delete-permanent-bundles is given, delete the given set of bundles
    # from the permanent tables.
    if impglobals.ARGUMENTS.delete_permanent_bundles:
        for bundle_id in bundle_id_list:
            do_import_tables.delete_bundle_from_obs_tables(bundle_id, 'perm')

    # If --copy-import-to-permanent-tables is given, create obs and mult tables
    # as necessary, then copy the import tables to the permanent tables.
    if impglobals.ARGUMENTS.copy_import_to_permanent_tables:
        for bundle_id in import_bundle_ids:
            do_import_tables.create_tables_for_import(bundle_id, 'perm')

        import_util.log_info('Deleting duplicate opus_ids')
        do_import_tables.delete_duplicate_opus_id_from_perm_tables()

        import_util.log_info('Copying import mult tables to permanent')
        do_import_mult.copy_mult_from_import_to_permanent()

        for bundle_id in import_bundle_ids:
            do_import_tables.copy_bundle_from_import_to_permanent(bundle_id)

    # If --drop-new-import-tables is given, delete the new import tables
    if impglobals.ARGUMENTS.drop_new_import_tables:
        import_util.log_info('Deleting all new import tables')
        do_import_tables.delete_all_obs_mult_tables('import')

    # If --analyze-permanent-tables is given, analyze the permanent tables
    if impglobals.ARGUMENTS.analyze_permanent_tables:
        import_util.log_info('Analyzing all permanent tables')
        do_import_tables.analyze_all_tables('perm')

    return True
