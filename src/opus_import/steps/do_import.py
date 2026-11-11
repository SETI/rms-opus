"""The observation import: read the PDS holdings and write the observation tables.

This is the step behind ``--import``, and behind ``--join``, which imports bundles from
the bundle registry's queue so that several import processes, on one computer or
several, can import into one schema at once (`import_from_queue`). It also owns the
options that are not steps of their own, because each has to happen at a particular
point in this sequence: ``--scorched-earth``, which drops every table the import creates
before anything else runs; ``--delete-bundles``, which deletes the named bundles before
any is imported; ``--requeue``, which returns bundles to the queue; and
``--register-bundles``, which registers bundles without importing them.

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

On both paths every bundle is registered in the bundle registry
(`opus_import.steps.do_register`) before the first one starts, which fixes the range its
observation ids come from, and then deleted from the observation tables and loaded
again, so a rerun is clean. A bundle that logs an error is
recorded ``failed``, and finalization and the version step refuse to run until it is
imported again or deleted; ``--ignore-errors`` records it ``done`` instead.

The per-bundle work is split across four modules that are not steps of their own:
`opus_import.steps.do_import_tables` prepares the tables,
`opus_import.steps.do_import_index` walks one index file,
`opus_import.steps.do_import_obs` computes one row, and
`opus_import.steps.do_import_mult` maintains the enumerated-value tables.
"""

from __future__ import annotations

import contextlib
import time
import traceback
from typing import TYPE_CHECKING

from opus_import import (
    bundle_registry,
    import_processes,
    import_util,
    primary_index,
    schema_version,
)
from opus_import.import_fault import import_fault_argument
from opus_import.steps import do_import_index, do_import_tables, do_recover, do_register
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

    The bundle's primary index files are found by `opus_import.primary_index.locate`,
    and each is imported in name order. The bundle's observations take ids from its
    registered range (`opus_import.bundle_registry.BundleIds`).

    Parameters:
        ctx: The import run's context, which is reset to this bundle here.
        bundle_id: The bundle to import, registered unless OPUS deliberately ignores it.

    Returns:
        True if the bundle imported, and also if OPUS deliberately ignores it -- an
        entry with no instrument class is one OPUS knows about and does not import.
        False if the bundle is unknown, is not a bundle, has an unsupported PDS version,
        no index file was found, an index failed to import, or the bundle needs more
        ids than its range holds.
    """
    ctx.logger.open(
        f'Importing {bundle_id}',
        limits={'info': ctx.args.log_info_limit, 'debug': ctx.args.log_debug_limit},
    )

    # Start fresh
    ctx.mult_table_cache = {}
    ctx.current_bundle_id = bundle_id
    ctx.current_index_row_number = None
    ctx.current_primary_filespec = None
    try:
        return _import_bundle_indexes(ctx, bundle_id)
    finally:
        ctx.logger.close()
        ctx.bundle_ids = None
        ctx.load_guard = None
        ctx.current_bundle_id = None
        ctx.current_index_row_number = None
        ctx.current_primary_filespec = None


def _import_bundle_indexes(ctx: ImportContext, bundle_id: str) -> bool:
    """Find a bundle's primary index files and import each; `import_one_bundle`'s body.

    Parameters:
        ctx: The import run's context, reset to this bundle.
        bundle_id: The bundle.

    Returns:
        What `import_one_bundle` returns.
    """
    if not do_import_tables.opus_imports_bundle(bundle_id):
        import_util.log_debug(ctx, f'Ignoring import of {bundle_id}')
        return True
    vol_info = do_import_tables.lookup_vol_info(bundle_id)
    if vol_info is None:
        import_util.log_error(ctx, f'No BUNDLE_INFO entry for {bundle_id}!')
        return False
    if import_fault_argument(LOG_ERROR_FAULT_SITE) == bundle_id:
        import_util.log_error(ctx, f'{LOG_ERROR_FAULT_SITE} fault injected into {bundle_id}')

    ctx.bundle_ids = bundle_registry.bundle_ids(ctx, bundle_id)
    if ctx.bundle_ids is None:
        import_util.log_error(ctx, f'{bundle_id} is not in the bundle registry')
        return False
    ctx.load_guard = import_processes.BundleGuard(ctx.bundle_ids, ctx.importer)

    try:
        found = primary_index.locate(bundle_id, vol_info)
    except primary_index.PrimaryIndexError as e:
        import_util.log_error(ctx, str(e))
        return False
    if not found.files:
        import_util.log_error(ctx, f'No index label file found: "{bundle_id}" - searched in:')
        for path in found.searched:
            import_util.log_error(ctx, f'    {path}')
        return False

    for bundle_label_path in found.files:
        import_util.log_debug(ctx, f'Using index: {bundle_label_path}')
        try:
            imported = do_import_index.import_one_index(
                ctx, bundle_id, vol_info, found.searched, bundle_label_path
            )
        except bundle_registry.BundleIdRangeError as e:
            import_util.log_error(ctx, str(e))
            return False
        if not imported:
            # The later indexes are not imported: the bundle has failed.
            return False
    return True


################################################################################
# THE MAIN IMPORT LOOP
################################################################################


def do_import_steps(ctx: ImportContext) -> bool:
    """Run the import work the command line asked for, in the one order that is safe.

    ``--scorched-earth`` drops every table the import creates first; ``--delete-bundles``
    then deletes the named bundles and their registry rows, setting a ``ready`` schema of
    this release's version to ``appending`` first, since the deletion unfinishes it as an
    append does; ``--requeue`` returns named ``failed`` or ``importing`` bundles to
    ``pending`` after deleting their rows (`requeue_bundles`).

    An invocation that registers or imports bundles chooses its path from the schema's
    state (`choose_import_path`), unless `opus_import.cli` chose it already.
    ``--register-bundles`` registers the named bundles in their order
    (`opus_import.steps.do_register`) and imports nothing: on the append path it also
    returns the named bundles already registered to ``pending`` and sets the schema
    ``appending``; on a fresh import it leaves registered bundles as they are.
    ``--import`` registers its bundles before the first one starts, returning those
    already registered to ``pending``: on the append path every bundle an earlier append
    left ``pending`` or ``failed`` and not named, in registration order, followed by the
    ones named in their order; on a fresh import the ones named. A bundle OPUS
    deliberately skips is never registered, and an append that registers none leaves the
    schema's state alone. ``--join`` imports bundles from the registry's queue instead
    (`import_from_queue`).

    Each bundle ``--import`` imports is marked ``importing``, deleted from the
    observation tables with foreign keys checked, so ``cart``'s cascade removes the cart
    rows that name it, and loaded with them unchecked, which validation's orphan count
    stands in for. It ends ``done``, or ``failed`` when its import failed or logged an
    error, unless ``--ignore-errors``, which records it ``done`` regardless. A bundle
    whose import failed stops the loop and leaves the bundles after it ``pending``,
    again unless ``--ignore-errors``.

    Each phase that runs is timed into `ImportContext.step_timings` under its own name,
    the bundle import also per bundle as ``delete_bundle:<bundle>`` and
    ``import_bundle:<bundle>``. The names are the arguments of the ``ctx.timed`` calls
    below; ``grep -n "ctx.timed(" src/opus_import`` lists every one.

    Parameters:
        ctx: The import run's context, whose per-run caches are reset here.

    Returns:
        True if everything asked for succeeded. False if a step was refused, a
        registration was refused, or a bundle failed or logged an error and errors are
        not being ignored, which is logged.
    """
    ctx.import_has_bad_data = False
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

    if ctx.args.requeue and not requeue_bundles(ctx, named_bundles):
        return False

    if not (ctx.args.register_bundles or ctx.args.do_import or ctx.args.join):
        return True
    if ctx.import_path is None and not choose_import_path(ctx):
        return False

    if ctx.args.register_bundles:
        appending = ctx.import_path == IMPORT_PATH_APPEND
        registered = _register(ctx, named_bundles, make_pending=appending)
        if registered is None:
            return False
        if appending and registered:
            _mark_appending(ctx)
        return True

    if ctx.args.join:
        return import_from_queue(ctx, set(named_bundles) if ctx.args.bundles else None)

    bundle_id_list = _bundles_to_import(ctx, named_bundles)
    registered = _register(ctx, bundle_id_list, make_pending=True)
    if registered is None:
        return False
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


def _register(ctx: ImportContext, bundle_ids: list[str], *, make_pending: bool) -> list[str] | None:
    """Register bundles, logging a refusal.

    Parameters:
        ctx: The import run's context.
        bundle_ids: The bundles, in import order.
        make_pending: Whether a bundle already registered goes back to ``pending``.

    Returns:
        The bundles registered (`opus_import.steps.do_register.register_bundles`), or
        None when registration was refused, which is logged as fatal.
    """
    try:
        with ctx.timed('register_bundles'):
            return do_register.register_bundles(ctx, bundle_ids, make_pending=make_pending)
    except bundle_registry.RegistrationError as e:
        ctx.logger.log('fatal', str(e))
        ctx.import_has_bad_data = True
        return None


#: The `opus_import.import_fault` site after a queue importer's claim commits. Its
#: argument is a number of seconds the importer sleeps there before importing.
HOLD_AFTER_CLAIM_FAULT_SITE = 'hold_after_claim'

#: How the log line naming a claimed bundle starts.
CLAIMED_PREFIX = 'Claimed bundle '

#: The log line a queue importer writes when no bundle is left for it.
QUEUE_EMPTY_LINE = 'No pending bundle is left to claim; this importer exits'

#: How the log line naming a queue importer's ``import_process`` row starts.
IMPORTER_PREFIX = 'Importer '


def import_from_queue(ctx: ImportContext, among: set[str] | None) -> bool:
    """Import bundles from the registry's queue until none is left: one importer's run.

    The importer first records itself in ``import_process`` and takes its lock, on a
    connection of its own (`opus_import.import_processes.start_importer`). It then
    claims the largest ``pending`` bundle no other process holds
    (`opus_import.bundle_registry.claim_bundle`), deletes its rows and imports it, marks
    it ``done``, and claims the next, until no bundle is ``pending``. It never erases or
    finalizes anything. A bundle whose import raises or logs an error is marked
    ``failed`` and its rows are deleted; the importer moves on to the next, and does not
    claim the failed bundle again.

    Every chunk it commits, every claim and every move to ``done`` is committed only
    while it holds its lock and the registry still names it as holding the bundle. When
    either is lost, it aborts its bundle (`abort_bundle`) and stops. After one interrupt
    it finishes its bundle and claims nothing new; a second aborts its bundle and stops.
    Whichever way it ends, it records itself ``exited`` and frees its lock.

    Parameters:
        ctx: The import run's context, with its path chosen.
        among: The only bundles the importer claims, or None for any.

    Returns:
        True when the queue was emptied and every bundle the importer imported is
        ``done``; False when one failed, the importer lost its lock or its bundle, or it
        was interrupted, which is logged as fatal.
    """
    db = ctx.db
    assert db is not None
    import_processes.create_process_table(db)
    lock_db = db.open_sibling_connection()
    importer = import_processes.start_importer(lock_db, ctx.log_path or '')
    ctx.importer = importer
    import_util.log_info(
        ctx, f'{IMPORTER_PREFIX}{importer.process_id}, holding the lock "{importer.name}"'
    )
    failures: list[str] = []
    try:
        with ctx.timed('import'):
            while True:
                if ctx.interrupts:
                    ctx.logger.log(
                        'fatal', 'Interrupted: this importer claims nothing more and exits'
                    )
                    return False
                if not importer.held():
                    raise import_processes.LostImporterError(
                        import_processes.lost_lock_message(importer)
                    )
                bundle_id = bundle_registry.claim_bundle(ctx, among, importer)
                if bundle_id is None:
                    import_util.log_info(ctx, QUEUE_EMPTY_LINE)
                    break
                import_util.log_info(ctx, f'{CLAIMED_PREFIX}{bundle_id}')
                if not _import_claimed_bundle(ctx, bundle_id, importer):
                    failures.append(bundle_id)
    except import_processes.LostImporterError as e:
        ctx.logger.log('fatal', str(e))
        return False
    except KeyboardInterrupt:
        ctx.logger.log('fatal', 'Interrupted twice: this importer aborted its bundle and exits')
        return False
    finally:
        ctx.importer = None
        importer.exit()
    if failures:
        ctx.logger.log(
            'fatal', f'This importer failed to import, and deleted: {", ".join(failures)}'
        )
        return False
    return True


def _import_claimed_bundle(
    ctx: ImportContext, bundle_id: str, importer: import_processes.ImporterLock
) -> bool:
    """Delete, import and mark one claimed bundle; delete it again if its import fails.

    Parameters:
        ctx: The import run's context.
        bundle_id: The bundle, ``importing`` under the importer.
        importer: The importer.

    Returns:
        True when the bundle ends ``done``; False when it ends ``failed``.

    Raises:
        opus_import.import_processes.LostImporterError: If the importer lost its lock or
            its bundle, after the bundle was aborted.
        KeyboardInterrupt: On a second interrupt, after the bundle was aborted.
    """
    db = ctx.db
    assert db is not None
    registered = bundle_registry.bundle_range(ctx, bundle_id)
    assert registered is not None
    number = registered.bundle_number
    ctx.bundle_has_errors = False
    imported = False
    try:
        hold = import_fault_argument(HOLD_AFTER_CLAIM_FAULT_SITE)
        if hold is not None:
            time.sleep(float(hold))
        with ctx.timed(f'delete_bundle:{bundle_id}'):
            if not do_recover.release_bundle(ctx, bundle_id, number, importer.process_id, None):
                raise import_processes.LostImporterError(
                    import_processes.lost_lock_message(importer)
                )
        with ctx.timed(f'import_bundle:{bundle_id}'), db.foreign_keys_unchecked():
            imported = import_one_bundle(ctx, bundle_id)
        if imported and not ctx.bundle_has_errors:
            bundle_registry.finish_claimed_bundle(ctx, number, importer)
            return True
    except (import_processes.LostImporterError, KeyboardInterrupt):
        abort_bundle(ctx, bundle_id, number, importer)
        raise
    except Exception:
        import_util.log_error(
            ctx, f'Import of bundle {bundle_id} raised:\n{traceback.format_exc()}'
        )
    ctx.mark_bad_data()
    if not do_recover.release_bundle(
        ctx, bundle_id, number, importer.process_id, bundle_registry.BUNDLE_FAILED
    ):
        raise import_processes.LostImporterError(import_processes.lost_lock_message(importer))
    return False


def abort_bundle(
    ctx: ImportContext, bundle_id: str, number: int, importer: import_processes.ImporterLock
) -> None:
    """Delete an importer's bundle's rows and return it to the queue, if it still holds it.

    The import connection may be part way through a statement when an interrupt arrives,
    so it is closed, which rolls back whatever it held, and a fresh one does the deletes.
    A bundle a recovery has already returned, or another importer holds, is left alone
    (`opus_import.steps.do_recover.release_bundle`).

    Parameters:
        ctx: The import run's context, whose connection is replaced.
        bundle_id: The bundle.
        number: Its number.
        importer: The importer.
    """
    old = ctx.db
    assert old is not None
    with contextlib.suppress(Exception):
        old.close()
    fresh = old.open_sibling_connection()
    fresh.logger = old.logger
    ctx.db = fresh
    if do_recover.release_bundle(
        ctx, bundle_id, number, importer.process_id, bundle_registry.BUNDLE_PENDING
    ):
        import_util.log_info(
            ctx, f'Aborted {bundle_id}: deleted its rows and returned it to the queue'
        )
    else:
        import_util.log_info(ctx, f'Aborted {bundle_id}: it had already left this importer')


def requeue_bundles(ctx: ImportContext, bundle_ids: list[str]) -> bool:
    """Return ``failed`` or ``importing`` bundles to ``pending``, after deleting their rows.

    Naming an ``importing`` bundle is the operator's statement that the process that
    claimed it is no longer running; one whose importer still holds its lock is refused.

    Parameters:
        ctx: The import run's context, for the open database and the log.
        bundle_ids: The bundles to return.

    Returns:
        True when every named bundle was returned. False, changing nothing, when a named
        bundle is not registered or is neither ``failed`` nor ``importing``, which is
        logged as fatal naming each such bundle.
    """
    states = dict(bundle_registry.registered_bundles(ctx))
    returnable = (bundle_registry.BUNDLE_FAILED, bundle_registry.BUNDLE_IMPORTING)
    refused = [
        f'{bundle_id} ({states.get(bundle_id, "not registered")})'
        for bundle_id in bundle_ids
        if states.get(bundle_id) not in returnable
    ]
    refused += [
        f'{bundle_id} (importing under importer {process_id}, which holds its lock)'
        for bundle_id, process_id in _alive_holders(ctx, bundle_ids)
    ]
    if refused or not bundle_ids:
        ctx.logger.log(
            'fatal',
            '--requeue returns only failed or importing bundles to the queue, and changes '
            f'nothing otherwise: {", ".join(refused) or "no bundle was named"}',
        )
        ctx.import_has_bad_data = True
        return False
    for bundle_id in bundle_ids:
        do_import_tables.delete_bundle_from_obs_tables(ctx, bundle_id)
        bundle_registry.set_bundle_state(ctx, bundle_id, bundle_registry.BUNDLE_PENDING)
        import_util.log_info(ctx, f'Returned {bundle_id} to the queue')
    return True


def _alive_holders(ctx: ImportContext, bundle_ids: list[str]) -> list[tuple[str, int]]:
    """Return the named ``importing`` bundles whose importer holds its lock.

    Parameters:
        ctx: The import run's context, for the open database.
        bundle_ids: The bundles.

    Returns:
        Each such bundle with its importer's ``process_id``, in the order named.
    """
    db = ctx.db
    assert db is not None
    alive = []
    for status in import_processes.read_snapshot(db).bundles:
        if (
            status.bundle_id in bundle_ids
            and status.state == bundle_registry.BUNDLE_IMPORTING
            and status.process_id is not None
            and db.named_lock_holder(
                import_processes.importer_lock_name(db.db_schema, status.process_id)
            )
            is not None
        ):
            alive.append((status.bundle_id, status.process_id))
    return sorted(alive, key=lambda found: bundle_ids.index(found[0]))


def _bundles_to_import(ctx: ImportContext, named_bundles: list[str]) -> list[str]:
    """Return the bundles an invocation imports, in order.

    Parameters:
        ctx: The import run's context, for the open database and the chosen path.
        named_bundles: The bundles the command line's descriptors expand to.

    Returns:
        On the append path, every bundle the registry holds that is ``pending`` or
        ``failed`` and is not named, in registration order, then the named bundles in
        the order named; on a fresh import, the named bundles. A bundle left
        ``importing`` is not resumed: ``--requeue`` returns it, once the process holding
        it is known to have stopped.
    """
    if ctx.import_path != IMPORT_PATH_APPEND:
        return named_bundles
    resumable = (bundle_registry.BUNDLE_PENDING, bundle_registry.BUNDLE_FAILED)
    resumed = [
        bundle for bundle, state in bundle_registry.unfinished_bundles(ctx) if state in resumable
    ]
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
