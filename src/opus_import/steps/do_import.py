"""The observation import: read the PDS holdings and write the observation tables.

This is the step behind ``--import``. It also owns two options that are not steps of
their own, because each has to happen at a particular point in this sequence:
``--scorched-earth``, which drops every table the import creates before anything else
runs, and ``--delete-bundles``, which deletes the named bundles before any is imported.

Which way an invocation that imports bundles writes depends on the target schema's state,
which `choose_import_path` reads before the first bundle:

- **A schema with no** ``schema_version`` **row and none of the secondary keys
  finalization adds** is imported fresh: the observation and mult tables are created with
  only the keys a load needs (`opus_import.table_keys`), and finalization's
  ``--create-indexes`` adds the rest once. A failed fresh import leaves a schema with no
  version row, which the web application refuses to serve and both deploy scripts refuse
  to promote.
- **A schema with this release's version row** is appended to, its keys in place. The
  append first sets the row's state to ``appending``, which the web application and both
  deploy scripts refuse until ``--write-schema-version`` changes it back to ``ready``, and
  resumes every bundle an earlier append left unfinished. It never finalizes the schema
  itself: ``--finalize`` does, as after a fresh import.
- **A schema with another release's version row** is refused, and so is **one with no
  version row but with those keys**, whose finalization was interrupted, in favor of
  ``--finalize``.

On both paths every bundle is recorded in the bundle registry
(`opus_import.bundle_registry`) before the first one starts, and then deleted from the
observation tables and loaded again, so a rerun is clean. A bundle that logs an error is
recorded ``failed``, and finalization and the version step refuse to run until it is
imported again or deleted; ``--ignore-errors`` records it ``done`` instead.

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

from opus_import import bundle_registry, import_util, schema_version
from opus_import.import_fault import import_fault_argument
from opus_import.steps import do_import_index, do_import_tables
from opus_import.table_keys import KEY_FILTERED_TABLE_PREFIXES, add_secondary_indexes

if TYPE_CHECKING:
    from opus_import.context import ImportContext

#: The path a fresh import takes, into a schema with no version row.
IMPORT_PATH_FRESH = 'fresh import'

#: The path an import into a finalized schema takes.
IMPORT_PATH_APPEND = 'append'

#: How the log line naming the path starts.
IMPORT_PATH_PREFIX = 'Import path: '

#: The `opus_import.import_fault` site inside a bundle's import. Its argument is a
#: bundle; importing that bundle logs one error there and carries on.
LOG_ERROR_FAULT_SITE = 'log_error'


def finalization_keys_present(ctx: ImportContext) -> list[str]:
    """Return the secondary keys finalization adds that the tables already have.

    Parameters:
        ctx: The import run's context, for the open database.

    Returns:
        Each such key as ``table: key``, in table order; none on a schema imported fresh
        and not yet finalized.
    """
    db = ctx.db
    assert db is not None
    existing = db.read_table_keys()
    present: list[str] = []
    for table_name in sorted(db.table_names(prefix=list(KEY_FILTERED_TABLE_PREFIXES))):
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
    fresh. A schema whose one row holds this release's version is appended to, whether
    the row is ``ready`` or an earlier append left it ``appending``. Anything else is
    refused: a row of another version, or several rows, since a schema is re-imported
    under the release that will serve it; and no row but such keys, a finalization that
    was interrupted, since loading into tables that carry every index is what a fresh
    import exists to avoid and ``--finalize`` completes it. The choice is logged on one
    line naming the path, the schema and its version, and kept in
    `ImportContext.import_path`.

    Parameters:
        ctx: The import run's context, for the open database, the arguments and the
            logger.

    Returns:
        True if the import may go ahead, False if it is refused, which is logged.
    """
    db = ctx.db
    assert db is not None
    rows = []
    if db.table_exists(schema_version.SCHEMA_VERSION_TABLE):
        rows = list(db.read_rows(schema_version.SCHEMA_VERSION_TABLE, ['version', 'state']))
    if rows:
        versions = ', '.join(f'version {version}, {state}' for version, state in rows)
        problem = None
        if len(rows) > 1:
            problem = f'has {len(rows)} {schema_version.SCHEMA_VERSION_TABLE} rows ({versions})'
        elif rows[0][0] != schema_version.SCHEMA_VERSION:
            problem = (
                f'is version {rows[0][0]} and this release is version '
                f'{schema_version.SCHEMA_VERSION}'
            )
        elif rows[0][1] not in (
            schema_version.SCHEMA_STATE_READY,
            schema_version.SCHEMA_STATE_APPENDING,
        ):
            problem = f'has the state {rows[0][1]!r}'
        if problem is not None:
            ctx.logger.log(
                'fatal',
                f'"{db.db_schema}" {problem}, so nothing is imported into it: a schema is '
                're-imported under the release that will serve it, starting with '
                '"opus_import --scorched-earth --yes"',
            )
            ctx.import_has_bad_data = True
            return False
        ctx.import_path = IMPORT_PATH_APPEND
        import_util.log_info(
            ctx, f'{IMPORT_PATH_PREFIX}{IMPORT_PATH_APPEND}, into "{db.db_schema}" ({versions})'
        )
        return True
    present = finalization_keys_present(ctx)
    if present:
        ctx.logger.log(
            'fatal',
            f'"{db.db_schema}" has no {schema_version.SCHEMA_VERSION_TABLE} row but has '
            f'{len(present)} of the keys finalization adds (the first: {present[0]}), so its '
            'finalization was interrupted: "opus_import --finalize" completes it, and '
            '"--scorched-earth --yes" starts over',
        )
        ctx.import_has_bad_data = True
        return False
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
    """Import one bundle into the observation tables.

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

    if not do_import_tables.opus_imports_bundle(bundle_id):
        import_util.log_debug(ctx, f'Ignoring import of {bundle_id}')
        ctx.logger.close()
        ctx.current_bundle_id = None
        return True
    vol_info = do_import_tables.lookup_vol_info(bundle_id)
    if vol_info is None:
        import_util.log_error(ctx, f'No BUNDLE_INFO entry for {bundle_id}!')
        ctx.logger.close()
        ctx.current_bundle_id = None
        return False
    if import_fault_argument(LOG_ERROR_FAULT_SITE) == bundle_id:
        import_util.log_error(ctx, f'{LOG_ERROR_FAULT_SITE} fault injected into {bundle_id}')

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

    ``--scorched-earth`` drops every table the import creates first; ``--delete-bundles``
    then deletes the named bundles and their registry rows, setting a ``ready`` schema of
    this release's version to ``appending`` first, since the deletion unfinishes it as an
    append does. An invocation that imports
    bundles chooses its path from the schema's state (`choose_import_path`), unless
    `opus_import.cli` chose it already, and records its bundles in the registry before
    the first one starts: on the append path every bundle an earlier append left
    unfinished and not named, in bundle order, followed by the ones named in their order;
    on a fresh import the ones named. A bundle OPUS deliberately skips is never recorded,
    and an append that records none leaves the schema's state alone.

    Each bundle is then marked ``importing``, deleted from the observation tables with
    foreign keys checked, so ``cart``'s cascade removes the cart rows that name it, and
    loaded with them unchecked, which validation's orphan count stands in for. It ends
    ``done``, or ``failed`` when its import failed or logged an error, unless
    ``--ignore-errors``, which records it ``done`` regardless. A bundle whose import
    failed stops the loop and leaves the bundles after it ``pending``, again unless
    ``--ignore-errors``.

    Each phase that runs is timed into `ImportContext.step_timings` under its own name,
    the bundle import also per bundle as ``delete_bundle:<bundle>`` and
    ``import_bundle:<bundle>``. The names are the arguments of the ``ctx.timed`` calls
    below; ``grep -n "ctx.timed(" src/opus_import`` lists every one.

    Parameters:
        ctx: The import run's context, whose per-run caches are reset here.

    Returns:
        True if everything asked for succeeded. False if the import was refused, or a
        bundle failed or logged an error and errors are not being ignored, which is
        logged.
    """
    ctx.import_has_bad_data = False
    ctx.max_table_id_cache = {}
    db = ctx.db
    assert db is not None

    named_bundles = list(import_util.yield_import_bundle_ids(ctx))

    # Before anything else, so that there are no vestigial mult rows and the ids start
    # again.
    if ctx.args.scorched_earth:
        import_util.log_warning(ctx, f'** DELETING EVERY OPUS TABLE IN SCHEMA {db.db_schema} **')
        with ctx.timed('scorched_earth'):
            do_import_tables.delete_all_opus_tables(ctx)
        ctx.mult_fields = None

    if ctx.args.delete_bundles:
        if named_bundles and _schema_is_ready(ctx):
            _mark_appending(ctx)
        with ctx.timed('delete_bundles'):
            for bundle_id in named_bundles:
                do_import_tables.delete_bundle_from_obs_tables(ctx, bundle_id)
            bundle_registry.unregister_bundles(ctx, named_bundles)

    if not ctx.args.do_import:
        return True
    if ctx.import_path is None and not choose_import_path(ctx):
        return False

    bundle_id_list = _bundles_to_import(ctx, named_bundles)
    registered = [b for b in bundle_id_list if do_import_tables.opus_imports_bundle(b)]
    bundle_registry.create_registry(ctx)
    bundle_registry.register_bundles(ctx, registered)
    # An append that has nothing to import leaves a finished schema as it is.
    if ctx.import_path == IMPORT_PATH_APPEND and registered:
        _mark_appending(ctx)

    with ctx.timed('import'):
        for bundle_id in bundle_id_list:
            is_registered = bundle_id in registered
            if is_registered:
                bundle_registry.set_bundle_state(ctx, bundle_id, bundle_registry.BUNDLE_IMPORTING)
            ctx.bundle_has_errors = False
            with ctx.timed(f'delete_bundle:{bundle_id}'):
                do_import_tables.delete_bundle_from_obs_tables(ctx, bundle_id)
            with ctx.timed(f'import_bundle:{bundle_id}'), db.foreign_keys_unchecked():
                imported = import_one_bundle(ctx, bundle_id)
            if not imported:
                ctx.logger.log('fatal', f'Import of bundle {bundle_id} failed - Aborting')
                ctx.mark_bad_data()
            if is_registered:
                failed = ctx.bundle_has_errors and not ctx.args.ignore_errors
                bundle_registry.set_bundle_state(
                    ctx,
                    bundle_id,
                    bundle_registry.BUNDLE_FAILED if failed else bundle_registry.BUNDLE_DONE,
                )
            if not imported and not ctx.args.ignore_errors:
                break

    if ctx.import_has_bad_data and not ctx.args.ignore_errors:
        ctx.logger.log('fatal', 'ERRORs found during import - aborting early')
        return False
    return True


def _bundles_to_import(ctx: ImportContext, named_bundles: list[str]) -> list[str]:
    """Return the bundles an invocation imports, in order.

    Parameters:
        ctx: The import run's context, for the open database and the chosen path.
        named_bundles: The bundles the command line's descriptors expand to.

    Returns:
        On the append path, every bundle the registry holds that is not ``done`` and is
        not named, in bundle order, then the named bundles in the order named; on a
        fresh import, the named bundles. The named order is kept because it decides
        which copy of a shared OPUS ID finalization keeps: the one imported last.
    """
    if ctx.import_path != IMPORT_PATH_APPEND:
        return named_bundles
    resumed = [bundle for bundle, _ in bundle_registry.unfinished_bundles(ctx)]
    if resumed:
        import_util.log_info(
            ctx, f'Resuming the unfinished bundles of an earlier append: {", ".join(resumed)}'
        )
    return [*(bundle for bundle in resumed if bundle not in named_bundles), *named_bundles]


def _schema_is_ready(ctx: ImportContext) -> bool:
    """Return whether the schema's one version row is this release's version, ``ready``.

    Parameters:
        ctx: The import run's context, for the open database.
    """
    db = ctx.db
    assert db is not None
    if not db.table_exists(schema_version.SCHEMA_VERSION_TABLE):
        return False
    rows = list(db.read_rows(schema_version.SCHEMA_VERSION_TABLE, ['version', 'state']))
    return rows == [(schema_version.SCHEMA_VERSION, schema_version.SCHEMA_STATE_READY)]


def _mark_appending(ctx: ImportContext) -> None:
    """Set the schema's version row to ``appending``, if it is not already.

    Parameters:
        ctx: The import run's context, for the open database and the logger.
    """
    db = ctx.db
    assert db is not None
    db.update_row(
        schema_version.SCHEMA_VERSION_TABLE,
        {'state': schema_version.SCHEMA_STATE_APPENDING},
        f'{db.quote_identifier("version")}=%s',
        [schema_version.SCHEMA_VERSION],
    )
    import_util.log_info(
        ctx,
        f'Schema version {schema_version.SCHEMA_VERSION} is '
        f'{schema_version.SCHEMA_STATE_APPENDING} until --write-schema-version',
    )
