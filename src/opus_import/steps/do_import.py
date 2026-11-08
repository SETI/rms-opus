"""The observation import: read the PDS holdings and write the observation tables.

This is the step behind ``--import`` and the several options that imply it. It also owns
the work for two options that are not steps of their own -- dropping the permanent tables
under ``--drop-permanent-tables`` and deleting bundles from the import tables under
``--delete-import-bundles`` -- because each of them has to happen at a particular point
in this sequence.

Which way an invocation that imports bundles writes depends on the target schema's state,
which `choose_import_path` reads before the first bundle:

- **A schema with no** ``schema_version`` **row and none of the secondary keys
  finalization adds** is imported fresh: each bundle's rows are written straight to the
  permanent observation and mult tables, which are created with only the keys a load
  needs (`opus_import.table_keys`), and finalization's ``--create-indexes`` adds the
  rest once. A failed fresh import leaves a schema with no version row, which the web
  application refuses to serve and both deploy scripts refuse to promote.
- **A schema with a version row** is imported into through the import namespace:
  everything is written to the import tables first and copied over the permanent tables
  only once the whole run has succeeded, so a failed import cannot leave the web
  application serving half a bundle.
- **A schema with no version row but with those keys** is one whose finalization was
  interrupted, and an import into it is refused in favor of ``--finalize``.

An error anywhere aborts the run, unless ``--import-ignore-errors`` says otherwise.

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

from opus_import import import_util, schema_version
from opus_import.steps import (
    do_cart,
    do_django,
    do_import_index,
    do_import_mult,
    do_import_tables,
)
from opus_import.table_keys import KEY_FILTERED_TABLE_PREFIXES, add_secondary_indexes

if TYPE_CHECKING:
    from opus_import.context import ImportContext

#: The path a fresh import takes, straight into the permanent tables.
IMPORT_PATH_FRESH = 'fresh import'

#: The path an import into a schema with a version row takes, through the import tables.
IMPORT_PATH_NAMESPACE = 'import tables'

#: How the log line naming the path starts.
IMPORT_PATH_PREFIX = 'Import path: '


def finalization_keys_present(ctx: ImportContext) -> list[str]:
    """Return the secondary keys finalization adds that the permanent tables already have.

    Parameters:
        ctx: The import run's context, for the open database.

    Returns:
        Each such key as ``table: key``, in table order; none on a schema imported fresh
        and not yet finalized.
    """
    db = ctx.db
    assert db is not None
    existing = db.read_table_keys('perm')
    present: list[str] = []
    for table_name in sorted(db.table_names('perm', prefix=list(KEY_FILTERED_TABLE_PREFIXES))):
        schema = import_util.read_schema_for_existing_table(ctx, table_name)
        if schema is None:
            continue
        have = existing.get(table_name, [])
        present += [
            f'{table_name}: {key.describe()}'
            for key in add_secondary_indexes(table_name, schema)
            if key in have
        ]
    return present


def choose_import_path(ctx: ImportContext) -> bool:
    """Choose the path an invocation that imports bundles takes, from the target schema.

    A schema with no ``schema_version`` row and none of the secondary keys finalization
    adds -- an empty schema, or one a fresh import is part way through -- is imported
    fresh, which sets `ImportDBSuper.direct`. A schema with a version row is imported
    through the import tables. One with no version row but such keys had its
    finalization interrupted, and the import is refused, since loading into tables that
    carry every index is the slow path a fresh import exists to avoid and its bundles
    would then miss the finalization already done; ``--finalize`` completes it. The
    choice is logged on one line naming the path, the schema and its version, and kept
    in `ImportContext.import_path`.

    Parameters:
        ctx: The import run's context, for the open database, the arguments and the
            logger.

    Returns:
        True if the import may go ahead, False if it is refused, which is logged.
    """
    db = ctx.db
    assert db is not None
    rows = []
    if db.table_exists('perm', schema_version.SCHEMA_VERSION_TABLE):
        rows = list(db.read_rows('perm', schema_version.SCHEMA_VERSION_TABLE, ['version', 'state']))
    if rows:
        versions = ', '.join(f'version {version}, {state}' for version, state in rows)
        ctx.import_path = IMPORT_PATH_NAMESPACE
        import_util.log_info(
            ctx, f'{IMPORT_PATH_PREFIX}{IMPORT_PATH_NAMESPACE}, into "{db.db_schema}" ({versions})'
        )
        return True
    present = finalization_keys_present(ctx)
    if present:
        ctx.logger.log(
            'fatal',
            f'"{db.db_schema}" has no {schema_version.SCHEMA_VERSION_TABLE} row but has '
            f'{len(present)} of the keys finalization adds (the first: {present[0]}), so its '
            'finalization was interrupted: "opus_import --finalize" completes it, and '
            '"--drop-permanent-tables --scorched-earth" starts over',
        )
        ctx.import_has_bad_data = True
        return False
    db.direct = True
    ctx.import_path = IMPORT_PATH_FRESH
    import_util.log_info(
        ctx,
        f'{IMPORT_PATH_PREFIX}{IMPORT_PATH_FRESH}, into "{db.db_schema}" '
        f'(no {schema_version.SCHEMA_VERSION_TABLE} row)',
    )
    return True


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
    ctx.logger.open(
        f'Importing {bundle_id}',
        limits={'info': ctx.args.log_info_limit, 'debug': ctx.args.log_debug_limit},
    )

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

    # An entry has a primary index exactly when it has an instrument class, and the
    # bundles with neither returned above.
    primary_index = vol_info['primary_index']
    assert primary_index is not None
    primary_index_names = [x.replace('<BUNDLE>', bundle_id) for x in primary_index]

    # These are the metadata directories
    index_paths = bundle_pdsfile.associated_abspaths('metadata', must_exist=True)

    if vol_info['pds_version'] == 3:
        # These are the plain <volume>/index directories for PDS3 volumes that
        # don't have a separate metadata directory
        bundle_abspath = bundle_pdsfile.abspath
        # A pdsfile below a merged or category-level directory has no absolute path, and
        # neither is a bundle -- which the check above has already required this to be.
        assert bundle_abspath is not None
        index_paths.append(import_util.safe_join(bundle_abspath, 'INDEX'))
        index_paths.append(import_util.safe_join(bundle_abspath, 'index'))
    found_in_this_dir = False

    for path in index_paths:
        if not os.path.exists(path):
            continue
        # Sorted, because a bundle can have several primary indexes -- COCIRS_1xxx has
        # one per cube geometry -- and row ids are handed out in the order rows are
        # inserted. Taking them in `os.listdir` order makes every id in the database
        # depend on how one filesystem happened to enumerate one directory, so two
        # imports of identical holdings on two machines disagree about every id.
        basenames = sorted(os.listdir(path))
        ret = True
        for basename in basenames:
            if basename in primary_index_names:
                bundle_label_path = import_util.safe_join(path, basename)
                import_util.log_debug(ctx, f'Using index: {bundle_label_path}')
                found_in_this_dir = True
                ret = ret and do_import_index.import_one_index(
                    ctx, bundle_id, vol_info, index_paths, bundle_label_path
                )
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

    The permanent tables are dropped first if ``--scorched-earth`` confirms it. An
    invocation that imports bundles then chooses its path from the schema's state
    (`choose_import_path`), unless `opus_import.cli` chose it already.

    On the fresh-import path each bundle is deleted from the permanent tables and
    imported straight into them, so a rerun of a bundle is clean; nothing is staged,
    copied or dropped, and each step of the import-tables path that is skipped says so
    at debug level. On the import-tables path the old import tables are dropped, the
    bundles are imported into them, then the permanent tables get the bundles the import
    produced -- deleted first, then created, then copied -- and finally the import tables
    are dropped.

    The copy to the permanent tables is skipped when the import logged any error, so a
    run that produced bad data leaves the web application on the previous import.
    ``--import-ignore-errors`` overrides that, and also keeps the run going past a
    bundle that failed.

    Each phase that runs is timed into `ImportContext.step_timings` under its own name,
    the bundle import and the copy also per bundle as ``import_bundle:<bundle>`` and
    ``copy_bundle:<bundle>``. The names are the arguments of the ``ctx.timed`` calls
    below; ``grep -n "ctx.timed(" src/opus_import`` lists every one.

    Parameters:
        ctx: The import run's context, whose per-run caches are reset here.

    Returns:
        True if everything asked for succeeded. False if the import was refused, or a
        bundle failed and errors are not being ignored, which is logged.
    """
    ctx.import_has_bad_data = False
    ctx.max_table_id_cache = {}
    ctx.created_import_mult_tables = set()

    bundle_id_list = []
    for bundle_id in import_util.yield_import_bundle_ids(ctx):
        bundle_id_list.append(bundle_id)

    # If --drop-permanent-tables AND --scorched-earth is given, delete
    # the permanent tables entirely. We have to do this before starting the
    # real import so that there are no vestigial mult tables and the ids
    # can be reset to 0.
    old_perm_tables_dropped = False
    if ctx.args.drop_permanent_tables and ctx.args.scorched_earth:
        import_util.log_warning(ctx, '** DELETING ALL PERMANENT TABLES **')
        with ctx.timed('drop_permanent_tables'):
            do_import_tables.delete_all_obs_mult_tables(ctx, 'perm')
        old_perm_tables_dropped = True

        # This must be done after the permanent tables were deleted, since
        # that process also deleted these tables. In this case, we didn't do
        # this step earlier.
        if ctx.args.drop_cache_tables or ctx.args.create_cart:
            ctx.logger.open(
                'Cleaning up OPUS/Django tables',
                limits={'info': ctx.args.log_info_limit, 'debug': ctx.args.log_debug_limit},
            )

            if ctx.args.create_cart:
                with ctx.timed('create_cart'):
                    do_cart.create_cart(ctx)
            if ctx.args.drop_cache_tables:
                with ctx.timed('drop_cache_tables'):
                    do_django.drop_cache_tables(ctx)

            ctx.logger.close()

    if ctx.args.do_import and ctx.import_path is None and not choose_import_path(ctx):
        return False
    fresh = ctx.import_path == IMPORT_PATH_FRESH

    # Delete the old import tables if
    #   --drop-old-import-tables but not
    #   --leave-old-import-tables
    # is given.
    old_imp_tables_dropped = False
    if ctx.args.drop_old_import_tables and not ctx.args.leave_old_import_tables:
        if fresh:
            import_util.log_debug(ctx, 'Fresh import: no old import tables to drop')
        else:
            import_util.log_info(ctx, 'Deleting all old import tables')
            with ctx.timed('drop_old_import_tables'):
                do_import_tables.delete_all_obs_mult_tables(ctx, 'import')
        old_imp_tables_dropped = True

    # If --import is given, first delete the bundles from the import tables,
    # then do the new import
    if (ctx.args.do_import or ctx.args.delete_import_bundles) and not old_imp_tables_dropped:
        if fresh:
            import_util.log_debug(
                ctx, 'Fresh import: each bundle is deleted from the permanent tables instead'
            )
        else:
            import_util.log_warning(ctx, 'Importing on top of previous import tables!')
            with ctx.timed('delete_import_bundles'):
                for bundle_id in import_util.yield_import_bundle_ids(ctx):
                    do_import_tables.delete_bundle_from_obs_tables(ctx, bundle_id, 'import')

    if ctx.args.do_import:
        with ctx.timed('import'):
            for bundle_id in bundle_id_list:
                if fresh:
                    with ctx.timed(f'delete_bundle:{bundle_id}'):
                        do_import_tables.delete_bundle_from_obs_tables(ctx, bundle_id, 'perm')
                with ctx.timed(f'import_bundle:{bundle_id}'):
                    imported = import_one_bundle(ctx, bundle_id)
                if not imported:
                    ctx.logger.log('fatal', f'Import of bundle {bundle_id} failed - Aborting')
                    ctx.import_has_bad_data = True
                    if not ctx.args.import_ignore_errors:
                        break

        if ctx.import_has_bad_data and not ctx.args.import_ignore_errors:
            ctx.logger.log('fatal', 'ERRORs found during import - aborting early')
            return False

    if fresh:
        if (
            ctx.args.copy_import_to_permanent_tables
            or ctx.args.delete_permanent_import_bundles
            or ctx.args.drop_new_import_tables
        ):
            import_util.log_debug(
                ctx, 'Fresh import: the bundles are already in the permanent tables'
            )
    else:
        _copy_import_tables_to_permanent(ctx, old_perm_tables_dropped)

    # If --delete-permanent-bundles is given, delete the given set of bundles
    # from the permanent tables.
    if ctx.args.delete_permanent_bundles:
        with ctx.timed('delete_permanent_bundles'):
            for bundle_id in bundle_id_list:
                do_import_tables.delete_bundle_from_obs_tables(ctx, bundle_id, 'perm')

    return True


def _copy_import_tables_to_permanent(ctx: ImportContext, old_perm_tables_dropped: bool) -> None:
    """Copy the bundles the import tables hold over the permanent tables, as asked.

    Under ``--copy-import-to-permanent-tables`` or ``--delete-permanent-import-bundles``
    every bundle the import ``obs_general`` holds is deleted from the permanent tables;
    the copy then creates the permanent tables it needs, deletes the permanent copy of
    every observation the import also produced, and copies the mult tables and each
    bundle. ``--drop-new-import-tables`` then drops the import tables.

    Parameters:
        ctx: The import run's context, for the arguments, the open database and the
            logger.
        old_perm_tables_dropped: True when this invocation dropped the permanent tables,
            so there is nothing in them to delete.
    """
    # If --copy-import-to-permanent-tables or --delete-permanent-import-bundles
    # are given, delete all bundles that exist in the import tables from the
    # permanent tables.
    db = ctx.db
    assert db is not None
    import_bundle_ids = []
    if (
        ctx.args.copy_import_to_permanent_tables or ctx.args.delete_permanent_import_bundles
    ) and db.table_exists('import', 'obs_general'):
        imp_obs_general_table_name = db.convert_raw_to_namespace('import', 'obs_general')
        q = db.quote_identifier
        import_bundle_ids = [
            x[0]
            for x in db.general_select(
                f'DISTINCT {q("bundle_id")} FROM {q(imp_obs_general_table_name)} ORDER BY {q("bundle_id")}'
            )
        ]
        if not old_perm_tables_dropped:
            # Don't bother if there's nothing there!
            if not ctx.args.create_cart:
                import_util.log_warning(
                    ctx, 'Deleting bundles from perm tables but cart table not wiped'
                )
            with ctx.timed('delete_permanent_import_bundles'):
                for bundle_id in import_bundle_ids:
                    do_import_tables.delete_bundle_from_obs_tables(ctx, bundle_id, 'perm')

    # If --copy-import-to-permanent-tables is given, create obs and mult tables
    # as necessary, then copy the import tables to the permanent tables.
    if ctx.args.copy_import_to_permanent_tables:
        with ctx.timed('create_permanent_tables'):
            for bundle_id in import_bundle_ids:
                do_import_tables.create_tables_for_import(ctx, bundle_id, 'perm')

        import_util.log_info(ctx, 'Deleting duplicate opus_ids')
        with ctx.timed('delete_duplicate_opus_ids'):
            do_import_tables.delete_duplicate_opus_id_from_perm_tables(ctx)

        import_util.log_info(ctx, 'Copying import mult tables to permanent')
        with ctx.timed('copy_mult_tables'):
            do_import_mult.copy_mult_from_import_to_permanent(ctx)

        with ctx.timed('copy_to_permanent'):
            for bundle_id in import_bundle_ids:
                with ctx.timed(f'copy_bundle:{bundle_id}'):
                    do_import_tables.copy_bundle_from_import_to_permanent(ctx, bundle_id)

    # If --drop-new-import-tables is given, delete the new import tables
    if ctx.args.drop_new_import_tables:
        import_util.log_info(ctx, 'Deleting all new import tables')
        with ctx.timed('drop_new_import_tables'):
            do_import_tables.delete_all_obs_mult_tables(ctx, 'import')
