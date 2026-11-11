"""Import every observation a single primary index file describes.

A bundle's primary index has one row per observation, and the metadata directory beside
it holds further index files -- ring, sky and surface geometry summaries, an inventory of
the targets in each observation, and a supplemental index -- that carry more columns for
the same observations. They are cross-referenced by primary filespec, so the first half
of this module reads them all and builds one metadata dictionary per observation out of
them.

The second half is the master loop: for each index row, and for each phase of it (Cassini
VIMS produces both a visible and an infrared observation from one row), every table gets
a row computed by `opus_import.steps.do_import_obs`. The surface geometry rows, one per
body the observation has geometry for, are computed after the other tables' rows, and
``obs_surface_geometry``'s row, which lists the bodies, after them; ``obs_files`` is
deferred past even that, because it needs the ``obs_general`` and ``obs_pds`` rows and
contributes many rows per observation rather than one.

Nothing is written to the database until every row has been computed. The new ``mult``
rows go out first, because an ``obs_`` row stores the id a value was given in its mult
field and that row has to exist to be looked up -- by convention rather than by a database
constraint, since a ``mult_idx`` column carries no foreign key.

These are the per-index internals of `opus_import.steps.do_import`, not a step of their
own.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal

import pdsfile

from opus_import import bundle_registry, import_util, surface_geometry, table_keys
from opus_import.obs.obs_surface_geometry_target import ObsSurfaceGeometryTarget
from opus_import.steps import do_import_obs, do_import_pool, do_import_tables

if TYPE_CHECKING:
    from collections.abc import Sequence

    from opus_import.config_bundle_info import BundleInfo
    from opus_import.context import ImportContext
    from opus_import.import_util import IndexRow, TableSchema
    from opus_import.obs.obs_base import ObsBase


def import_one_index(
    ctx: ImportContext,
    bundle_id: str,
    vol_info: BundleInfo,
    index_paths: Sequence[str],
    bundle_label_path: str,
) -> bool:
    """Import every observation described by one primary index file.

    The associated metadata files found beside the index contribute their columns to
    each observation, keyed by primary filespec. A surface geometry summary has one row
    per target per observation, so its rows are collected per target; the others have at
    most one row per observation.

    A bundle whose `BundleInfo` sets ``validate_index_rows`` has its rows resolved when
    an observation has more than one: the one whose filespec round-trips through the
    OPUS id is kept and the others are dropped with a log message. Without that flag
    every row is imported as it stands. Where an index row produces more than one
    observation, the row is processed once per phase.

    Parameters:
        ctx: The import run's context.
        bundle_id: The bundle being imported.
        vol_info: What `opus_import.config_bundle_info` says about this bundle.
        index_paths: The directories to look for associated metadata files in.
        bundle_label_path: The primary index file.

    Returns:
        True if the index imported. False if the primary index could not be read, or an
        associated metadata file could not be, both of which are logged.
    """
    instrument_class = vol_info['instrument_class']
    # `import_one_bundle` returns before calling this for a bundle OPUS ignores, which
    # is the only kind with no instrument class.
    assert instrument_class is not None
    pds_version = vol_info['pds_version']

    obs_rows, obs_label_dict = import_util.safe_pdstable_read(ctx, bundle_label_path, pds_version)
    if not obs_rows:
        import_util.log_error(ctx, f'Read failed: "{bundle_label_path}"')
        return False

    import_util.log_info(ctx, f'OBSERVATIONS: {len(obs_rows)} in {bundle_label_path}')

    metadata: dict[str, Any] = {'phase_name': None, 'temporal_camera': vol_info['temporal_camera']}

    # Instantiate the appropriate class that knows how to import this instrument
    instrument_obj = instrument_class(ctx, bundle=bundle_id, metadata=metadata)

    # We need to validate index rows for bundles where there can be more than one
    # row in the index file for a single opus_id. We first compute the opus_id for
    # each row (which is a fast operation), looking for duplicates. When we find
    # duplicates, we collect them into a dictionary. Then we go through the duplicates,
    # if any, and do the reverse mapping opus_id -> filespec, seeing if the result
    # is the same. If it is, that's the row we want to use.
    # We do this complicated process because from_opus_id is a slow operation so we
    # don't want to do it unless absolutely necessary.
    valid_rows = None
    if vol_info['validate_index_rows']:
        opus_ids: dict[str, list[int]] = {}
        valid_rows = [True] * len(obs_rows)
        for row_no, row in enumerate(obs_rows):
            opus_id = instrument_obj.opus_id_from_index_row(row)
            if opus_id is None:
                # Error already reported
                valid_rows[row_no] = False
                continue
            if opus_id not in opus_ids:
                opus_ids[opus_id] = []
            opus_ids[opus_id].append(row_no)
        for opus_id, row_nos in opus_ids.items():
            if len(row_nos) == 1:  # Only one row means not ambiguous
                continue
            # Mark them all invalid to start
            for row_no in row_nos:
                valid_rows[row_no] = False
            good_row = None
            deriv_filespec = None
            try:
                deriv_filespec = pdsfile.pds3file.Pds3File.from_opus_id(opus_id).abspath
            except ValueError:
                try:
                    deriv_filespec = pdsfile.pds4file.Pds4File.from_opus_id(opus_id).abspath
                except ValueError:
                    ctx.current_index_row_number = row_no + 1
                    import_util.log_nonrepeating_warning(
                        ctx, f'Unable to convert OPUS ID "{opus_id}" to filespec'
                    )
            if deriv_filespec is not None:
                for row_no in row_nos:
                    orig_filespec = instrument_obj.primary_filespec_from_index_row(
                        obs_rows[row_no], convert_lbl=True
                    )
                    if orig_filespec is None:
                        # A row that names no file cannot be the one this OPUS ID came
                        # from.
                        continue
                    orig_filespec = instrument_obj.convert_filespec_from_lbl(orig_filespec)
                    if orig_filespec in deriv_filespec:
                        # Found it!
                        if good_row is not None:
                            import_util.log_nonrepeating_error(
                                ctx,
                                f'Found multiple rows that map from the same opus_id '
                                f'{opus_id}: {good_row} and {row_no}',
                            )
                        good_row = row_no
            if good_row is None:
                ctx.current_index_row_number = row_nos[0] + 1
                # This isn't always an error because sometimes we actually do have
                # an opud_id that can't be properly reverse-mapped, like
                # vg-pps-2-u-occ-1986-024-betper-lambda-i
                import_util.log_nonrepeating_warning(
                    ctx, f'No row found that reverse matches opus_id {opus_id}'
                )
            else:
                valid_rows[good_row] = True
                import_util.log_info(ctx, 'Resolving OPUS ID ambiguity:')
                for row_no in row_nos:
                    orig_filespec = instrument_obj.primary_filespec_from_index_row(
                        obs_rows[row_no], convert_lbl=True
                    )
                    sfx = ' (chosen)' if row_no == good_row else ''
                    import_util.log_info(ctx, '  ' + str(orig_filespec) + sfx)

        old_obs_rows = obs_rows
        obs_rows = []
        for row_no, row in enumerate(old_obs_rows):
            if valid_rows[row_no]:
                obs_rows.append(row)
            else:
                ctx.current_index_row_number = row_no + 1
                import_util.log_info(
                    ctx,
                    'Dropping index row '
                    + str(instrument_obj.primary_filespec_from_index_row(row)),
                )

    metadata['index'] = obs_rows
    metadata['index_label'] = obs_label_dict

    ######################################
    ### FIND ASSOCIATED METADATA FILES ###
    ######################################

    # Look for all the "associated" metadata files and read them in
    # Metadata filenames include:
    #   <vol>_ring_summary.lbl
    #   <vol>_moon_summary.lbl
    #   <vol>_<planet>_summary.lbl
    #   <vol>_body_summary.lbl
    #   <vol>_sky_summary.lbl
    #   <vol>_supplemental_index.lbl
    # All of these files are cross-indexed with the primary index file based on
    # the primary filespec.

    if index_paths:
        for index_path in index_paths:
            if vol_info['pds_version'] == 3:
                assoc_pdsfile = pdsfile.pds3file.Pds3File.from_abspath(index_path)
            else:
                assoc_pdsfile = pdsfile.pds4file.Pds4File.from_abspath(index_path)
            try:
                basenames = assoc_pdsfile.childnames
            except KeyError:
                continue
            for basename in basenames:
                if basename.find('999') != -1:
                    # These are cumulative geo files
                    continue
                if not basename.startswith(bundle_id):
                    continue
                basename_upper = basename.upper()
                if (
                    not basename_upper.endswith('SUMMARY.LBL')
                    and not basename_upper.endswith('SUPPLEMENTAL_INDEX.LBL')
                    and not basename_upper.endswith('INVENTORY.LBL')
                ):
                    continue
                assoc_label_path = import_util.safe_join(index_path, basename)
                assoc_rows: list[dict[str, Any]] | None
                assoc_label_dict: dict[str, Any] | None
                if basename_upper.endswith('INVENTORY.LBL'):
                    # The inventory files are in CSV format, but the pdstable
                    # module can't read non-fixed-length records so we fake it up
                    # ourselves here.
                    # The old format had as many extra columns as there were targets.
                    # The new format has a single column with the targets separated
                    # by commas.
                    table_filename = assoc_label_path.replace('.LBL', '.CSV').replace(
                        '.lbl', '.csv'
                    )
                    assoc_rows = []
                    assoc_label_dict = {}  # Not used
                    with open(table_filename) as table_file:
                        csvreader = csv.reader(table_file)
                        for csv_row in csvreader:
                            if len(csv_row) > 2 and csv_row[2].count('-') > 1:
                                # Old format with OPUS ID column
                                (csv_bundle, csv_filespec, csv_opus_id, *csv_targets) = csv_row
                            else:
                                # New format without OPUS ID column
                                csv_opus_id = None
                                (csv_bundle, csv_filespec, *csv_targets) = csv_row
                            if len(csv_targets) == 1:
                                csv_targets = csv_targets[0].split(',')  # New format
                            row_dict = {
                                'BUNDLE_ID': csv_bundle.strip(),
                                'FILE_SPECIFICATION_NAME': csv_filespec.strip(),
                                'TARGET_LIST': csv_targets,
                            }
                            if csv_opus_id:
                                row_dict['OPUS_ID'] = csv_opus_id.strip()

                            assoc_rows.append(row_dict)
                else:
                    (assoc_rows, assoc_label_dict) = import_util.safe_pdstable_read(
                        ctx, assoc_label_path, pds_version
                    )

                if assoc_rows is None:
                    # No need to report an error here because safe_pdstable_read
                    # will have already done so
                    return False

                if len(assoc_rows) == 0:
                    # An empty associated index reads as a successful read of a file
                    # with no rows -- the same result the PDS3 path gives -- so say so
                    # at error level rather than importing the whole bundle short of
                    # this metadata in silence.
                    import_util.log_error(
                        ctx,
                        f'No rows in associated index "{assoc_label_path}" - every '
                        'observation in this bundle will import without its metadata',
                    )

                if 'RING_SUMMARY' in basename_upper:
                    assoc_type = 'ring_geo'
                elif 'SKY_SUMMARY' in basename_upper:
                    assoc_type = 'sky_geo'
                elif 'SUPPLEMENTAL_INDEX' in basename_upper:
                    assoc_type = 'supp_index'
                elif 'INVENTORY' in basename_upper:
                    assoc_type = 'inventory'
                else:
                    assoc_type = 'surface_geo'

                # Now that we have the data from the associated file, we need to go
                # through and cross-reference it with the primary index based on the
                # primary filespec.
                import_util.log_info(
                    ctx, f'{assoc_type.upper()}: {len(assoc_rows)} in {assoc_label_path}'
                )
                assoc_dict = metadata.get(assoc_type, {})
                if assoc_type in ('ring_geo', 'surface_geo', 'sky_geo', 'inventory'):
                    for row in assoc_rows:
                        # We use add_phase_from_row=True here because in COVIMS_0xxx
                        # there are both _IR and _VIS versions of each geo row and we
                        # need a way to distinguish between them. It does nothing
                        # for other cases.
                        key = instrument_obj.primary_filespec_from_index_row(
                            row, convert_lbl=True, add_phase_from_row=True
                        )
                        if key is None:
                            # Error will already be logged
                            continue
                        key = key.upper()

                        if assoc_type in ('ring_geo', 'sky_geo', 'inventory'):
                            # RING_GEO, SKY_GEO, and INVENTORY are easy - there is at most
                            # a single entry per observation, so we just create
                            # a dictionary keyed by opus_id.
                            assoc_dict[key] = row

                        elif assoc_type == 'surface_geo':
                            # SURFACE_GEO is more complicated, because there can
                            # be more than one entry per observation, since
                            # there is one for each target. We create a
                            # dictionary keyed by opus_id containing a
                            # dictionary keyed by target name so we can collect
                            # all the target entries in one place.
                            key2 = row.get('TARGET_NAME', row.get('BODY_NAME', None))
                            if key2 is None:
                                import_util.log_nonrepeating_error(
                                    ctx,
                                    f'{assoc_label_path} is missing TARGET_NAME or BODY_NAME field',
                                )
                                break
                            if key not in assoc_dict:
                                assoc_dict[key] = {}
                            assoc_dict[key][key2] = row

                else:
                    assert assoc_type == 'supp_index'
                    for row in assoc_rows:
                        key = instrument_obj.primary_filespec_from_index_row(row, convert_lbl=True)
                        if key is not None:
                            # Error will already be logged if key is None
                            key = key.upper()
                            assoc_dict[key] = row

                # We need to be able to look things up in both the main tab file and
                # also the associate label, because different instruments store
                # useful data in both places.
                metadata[assoc_type] = assoc_dict
                metadata[assoc_type + '_label'] = assoc_label_dict

    table_schemas, table_names_in_order = do_import_tables.create_tables_for_import(ctx, bundle_id)

    state = IndexState(
        instrument_obj=instrument_obj,
        metadata=metadata,
        base_metadata=dict(metadata),
        table_schemas=table_schemas,
        table_names_in_order=table_names_in_order,
        pds_version=pds_version,
        obs_rows=obs_rows,
    )
    sink = TableRowSink(ctx, table_names_in_order)

    # Two bundles can produce the same OPUS ID; finalization's duplicate step keeps the
    # copy from the bundle registered later.
    if not do_import_pool.compute_index(ctx, state, import_index_row, sink.add, bundle_label_path):
        # A failed index leaves none of its rows; the mult values it added stay, and
        # finalization deletes those no observation holds.
        sink.discard()
        return False

    ctx.current_index_row_number = None
    ctx.current_primary_filespec = None

    sink.finish()

    return True  # SUCCESS!


@dataclass
class IndexState:
    """What every row of one index is computed from.

    Attributes:
        instrument_obj: The obs class instance for the bundle, whose field functions
            compute the columns. It holds `metadata` itself.
        metadata: The dictionary the field functions read, which each row starts afresh
            from `base_metadata` and adds to.
        base_metadata: `metadata` as it stands before the first row: the index, its
            label, and the associated metadata files.
        table_schemas: Each table's column definitions.
        table_names_in_order: The tables, in the order their rows are computed.
        pds_version: 3 or 4.
        obs_rows: The index rows to import.
    """

    instrument_obj: ObsBase
    metadata: dict[str, Any]
    base_metadata: dict[str, Any]
    table_schemas: dict[str, TableSchema]
    table_names_in_order: list[str]
    pds_version: Literal[3, 4]
    obs_rows: list[IndexRow]


def _observation_id_column(table_name: str) -> str:
    """Return the column a failed index's rows of a table are taken back by.

    Parameters:
        table_name: An observation table.

    Returns:
        ``id`` for ``obs_general``, which numbers its own rows, and ``obs_general_id``
        for every other table, which a key of the table leads.
    """
    return 'id' if table_keys.is_bundle_keyed_table(table_name) else 'obs_general_id'


@dataclass
class TableRowSink:
    """Collects an index's rows per table and loads each table a transaction at a time.

    A table's rows are loaded as soon as `transaction_rows` of them are waiting, so the
    import holds at most that many rows of a table at once rather than a whole index's.
    A surface geometry row arrives under its body's category and waits with the surface
    geometry table's rows (`opus_import.surface_geometry.physical_table`). An index that
    fails partway takes back what was loaded (`discard`), so a failed index leaves no
    rows, as it would if its rows were loaded only at the end.

    Attributes:
        ctx: The import run's context, for the open database and the logger.
        table_names_in_order: The tables, in the order `finish` loads what is left of
            them.
        rows: The rows waiting to be loaded, per table.
        first_loaded: The observation id of the first row loaded into each table, in the
            order the tables were first loaded.
    """

    ctx: ImportContext
    table_names_in_order: list[str]
    rows: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    first_loaded: dict[str, int] = field(default_factory=dict)

    def add(self, table_name: str, row: dict[str, Any]) -> None:
        """Take one computed row, loading its table's rows once a transaction's worth wait.

        Parameters:
            table_name: The table the row goes into, or the surface geometry category it
                was computed under.
            row: The row, with every value final.
        """
        table_name = surface_geometry.physical_table(table_name)
        waiting = self.rows.setdefault(table_name, [])
        waiting.append(row)
        db = self.ctx.db
        assert db is not None
        if len(waiting) >= db.transaction_rows:
            self._load(table_name)

    def finish(self) -> None:
        """Load every row still waiting, table by table in order."""
        for table_name in self.table_names_in_order:
            self._load(table_name)

    def discard(self) -> None:
        """Delete every row this sink loaded, and drop the rows still waiting.

        Ids are handed out in ascending order from the bundle's own range, which no other
        process writes, so this index's rows are those from the first it loaded to the
        end of the range: by ``id`` in ``obs_general``, and by ``obs_general_id``, the
        observation's id, in every other table. The tables are emptied of them in the
        reverse of the order they were first loaded, except that ``obs_general`` always
        goes last, after every table whose rows refer to it: a table with many rows per
        observation, such as ``obs_files``, can fill a transaction and load before
        ``obs_general`` does.
        """
        db = self.ctx.db
        assert db is not None
        assert self.ctx.bundle_ids is not None
        end = self.ctx.bundle_ids.range.end
        in_order = [name for name in reversed(self.first_loaded) if name != 'obs_general']
        if 'obs_general' in self.first_loaded:
            in_order.append('obs_general')
        for table_name in in_order:
            first_id = self.first_loaded[table_name]
            column = db.quote_identifier(_observation_id_column(table_name))
            db.delete_rows(table_name, f'{column} >= %s AND {column} < %s', [first_id, end])
        self.first_loaded.clear()
        self.rows.clear()

    def _load(self, table_name: str) -> None:
        """Load one table's waiting rows, and record the bundle's progress after ``obs_general``.

        Parameters:
            table_name: The table.
        """
        db = self.ctx.db
        assert db is not None
        import_util.log_debug(self.ctx, f'Inserting into obs table "{table_name}"')
        waiting = self.rows.get(table_name, [])
        if waiting:
            self.first_loaded.setdefault(table_name, waiting[0][_observation_id_column(table_name)])
        db.bulk_load_rows(table_name, waiting)
        self.rows[table_name] = []
        bundle_ids = self.ctx.bundle_ids
        if waiting and table_name == 'obs_general' and bundle_ids is not None:
            bundle_ids.rows_done += len(waiting)
            bundle_registry.record_rows_done(
                self.ctx, bundle_ids.range.bundle_number, bundle_ids.rows_done
            )


def import_index_row(
    ctx: ImportContext, state: IndexState, index_row_num: int, emit: do_import_pool.RowEmitter
) -> None:
    """Compute every table's rows for one index row, handing each to `emit` in order.

    The row starts from the index's metadata as it stood before the first row, so what
    it computes depends on the row alone, not on the rows computed before it. Where an
    index row produces more than one observation (Cassini VIMS's visible and infrared
    phases), each phase is computed in turn.

    Parameters:
        ctx: The import run's context.
        state: What every row of the index is computed from.
        index_row_num: The row's position in `IndexState.obs_rows`, from zero.
        emit: Where each computed row goes, in the order the rows are computed.
    """
    instrument_obj = state.instrument_obj
    metadata = state.metadata
    table_schemas = state.table_schemas
    table_names_in_order = state.table_names_in_order
    index_row = state.obs_rows[index_row_num]

    metadata.clear()
    metadata.update(state.base_metadata)
    metadata['index_row'] = index_row
    metadata['index_row_num'] = index_row_num + 1
    metadata['phase_name'] = None
    obs_general_row = None
    obs_pds_row = None
    ctx.current_index_row_number = index_row_num + 1

    # Sometimes the primary_filespec is taken from the supplemental index, which we
    # don't have yet, so we can't look it up until later.
    ctx.current_primary_filespec = None

    # For supplemental_index and logging
    # Note we don't use primary_filespec_from_index_row here because that doesn't
    # currently work with CIRS, which makes the logging not give full
    # row information.
    primary_filespec = instrument_obj.primary_filespec
    # Every observation reaching this point came from an index row that named a
    # file; an obs class returns None only for a row that did not.
    assert primary_filespec is not None
    primary_filespec = instrument_obj.convert_filespec_from_lbl(primary_filespec)
    ctx.current_primary_filespec = primary_filespec
    primary_filespec = primary_filespec.upper()
    if 'supp_index' in metadata:
        supp_index = metadata['supp_index']
        if primary_filespec in supp_index:
            metadata['supp_index_row'] = supp_index[primary_filespec]
        else:
            import_util.log_nonrepeating_warning(
                ctx, f'FILESPEC "{primary_filespec}" is missing supplemental data'
            )
            metadata['supp_index_row'] = None

    # Sometimes a single row in the index turns into multiple opus_id
    # in the database. This happens with COVIMS because each observation
    # might include both VIS and IR entries. Build up a list of such entries
    # here and then process the row as many times as necessary.
    phase_names = instrument_obj.phase_names
    for phase_name in phase_names:
        metadata['phase_name'] = phase_name

        # For the geo indexes - we have to add in the phase because COVIMS_0xxx has
        # separate rows for IR and VIS
        primary_filespec_phase = instrument_obj.primary_filespec_from_index_row(
            index_row, convert_lbl=True, add_phase_from_inst=True
        )
        assert primary_filespec_phase is not None
        primary_filespec_phase = primary_filespec_phase.upper()
        if 'ring_geo' in metadata:
            ring_geo = metadata['ring_geo'].get(primary_filespec_phase, None)
            metadata['ring_geo_row'] = ring_geo
            if ring_geo is None and ctx.args.report_missing_ring_geo:
                import_util.log_warning(
                    ctx, f'RING GEO metadata missing for "{primary_filespec_phase}"'
                )
        if 'sky_geo' in metadata:
            sky_geo = metadata['sky_geo'].get(primary_filespec_phase, None)
            metadata['sky_geo_row'] = sky_geo
            if sky_geo is None and ctx.args.report_missing_sky_geo:
                import_util.log_warning(
                    ctx, f'SKY GEO metadata missing for "{primary_filespec_phase}"'
                )
        if 'surface_geo' in metadata:
            body_geo = metadata['surface_geo'].get(primary_filespec_phase)
            metadata['surface_geo_row'] = body_geo

        # Handle everything except surface_geo

        for table_name in table_names_in_order:
            if table_name.startswith('obs_surface_geometry'):
                # Deal with surface geometry a little later
                continue
            if table_name == 'obs_files':
                # obs_files is done separately below because it has multiple
                # rows per observation
                continue
            if table_name not in table_schemas:
                # Table not relevant for this product
                continue
            obs_row = do_import_obs.import_observation_table(
                ctx, instrument_obj, table_name, table_schemas[table_name], metadata
            )
            # A missing row means a mult column returned something that is not a
            # mult specification, which has already been reported. No table can be
            # filled from one, so every call site below narrows it the same way.
            assert obs_row is not None
            if table_name == 'obs_pds':
                obs_pds_row = obs_row
            if table_name == 'obs_general':
                obs_general_row = obs_row
            emit(table_name, obs_row)
            metadata[table_name + '_row'] = obs_row

        assert obs_general_row is not None

        # Every body the observation has surface geometry for: the summary file's, in
        # sorted order, then the ones an index holding the geometry itself lists.
        target_dict: dict[str, Any] = {}
        if 'surface_geo' in metadata:
            target_dict = metadata['surface_geo'].get(primary_filespec_phase, {})
        bodies: list[tuple[str, Any]] = [(name, target_dict[name]) for name in sorted(target_dict)]
        bodies += [(name, None) for name in instrument_obj.surface_geo_target_list() or ()]
        if bodies and surface_geometry.SURFACE_GEOMETRY_TABLE in table_schemas:
            _emit_surface_geometry_rows(
                ctx,
                state,
                table_schemas[surface_geometry.SURFACE_GEOMETRY_TABLE],
                obs_general_row['opus_id'],
                bodies,
                emit,
            )

        # Handle obs_surface_geometry
        # We have to do this later than the other obs_ tables because only
        # now do we know what all the available targets are

        surface_target_list = None
        if 'inventory' in metadata:
            inventory = metadata['inventory']
            if primary_filespec_phase in inventory:
                surface_target_list = inventory[primary_filespec_phase]['TARGET_LIST']
        metadata['inventory_list'] = surface_target_list
        metadata['used_surface_geo_targets'] = list(target_dict.keys())

        for table_name in table_names_in_order:
            if table_name != 'obs_surface_geometry':
                # Deal with obs_surface_geometry only
                continue
            # This is used to populate the surface geo target_list
            # field

            obs_row = do_import_obs.import_observation_table(
                ctx, instrument_obj, table_name, table_schemas[table_name], metadata
            )
            assert obs_row is not None
            emit(table_name, obs_row)

        # Handle obs_files

        for table_name in table_names_in_order:
            if table_name != 'obs_files':
                # Deal with obs_files only
                continue
            assert obs_pds_row is not None
            rows = get_opus_products_rows_for_filespec(
                ctx,
                state.pds_version,
                obs_pds_row['primary_filespec'],
                obs_general_row['id'],
                obs_general_row['opus_id'],
                obs_general_row['bundle_id'],
                obs_general_row['instrument_id'],
            )
            for row in rows:
                emit(table_name, row)


def _emit_surface_geometry_rows(
    ctx: ImportContext,
    state: IndexState,
    schema: TableSchema,
    opus_id: str,
    bodies: Sequence[tuple[str, Any]],
    emit: do_import_pool.RowEmitter,
) -> None:
    """Compute one observation's surface geometry row for each body it has geometry for.

    Each row is computed under the body's category, ``obs_surface_geometry__<target>``,
    which the field functions and the geometry checks are told, and goes to the one
    surface geometry table when it is loaded. The body is the target the raw name
    resolves to (`opus_import.obs.obs_surface_geometry_target.ObsSurfaceGeometryTarget.
    surface_geo_target`). A body that resolves to no target gets no row, its name having
    been reported as unknown. Two raw names that resolve to the same target, such as two
    spellings of one body, get one row, the first in `bodies`, and a warning naming the
    observation and both names.

    Parameters:
        ctx: The import run's context, for the logger.
        state: What every row of the index is computed from.
        schema: The surface geometry table's schema.
        opus_id: The observation's OPUS id, for the warning.
        bodies: Each body's raw name and its summary-file row, or None for a body whose
            geometry the index row itself holds, in the order the rows are computed.
        emit: Where each computed row goes.
    """
    instrument_obj = state.instrument_obj
    # Every obs class mixes in the module that fills the surface geometry table.
    assert isinstance(instrument_obj, ObsSurfaceGeometryTarget)
    metadata = state.metadata
    first_names: dict[str, str] = {}
    for raw_name, geo_row in bodies:
        metadata['surface_geo_row'] = geo_row
        metadata['surface_geo_target_name'] = raw_name
        target = instrument_obj.surface_geo_target(raw_name)
        if target is None:
            continue
        if target in first_names:
            import_util.log_nonrepeating_warning(
                ctx,
                f'Observation "{opus_id}" has surface geometry for "{first_names[target]}" '
                f'and "{raw_name}", which are both {target}; only "{first_names[target]}" '
                'is imported',
            )
            continue
        first_names[target] = raw_name
        category = surface_geometry.target_category(import_util.table_name_for_sfc_target(target))
        obs_row = do_import_obs.import_observation_table(
            ctx, instrument_obj, category, schema, metadata
        )
        assert obs_row is not None
        emit(category, obs_row)


def get_opus_products_rows_for_filespec(
    ctx: ImportContext,
    pds_version: Literal[3, 4],
    filespec: str,
    obs_general_id: int,
    opus_id: str,
    bundle_id: str,
    instrument_id: str,
) -> list[dict[str, Any]]:
    """Return the ``obs_files`` rows listing every file one observation has.

    Each row is one file of one product type at one version: where it lives, how big it
    is, its checksum, and the ordering the results page shows the product types in. A
    file that is not the current version is never checked by default. A row's
    ``file_number`` is its position in the list, from 1, which with the observation's id
    is the table's primary key and keeps the observation's files in this order.

    Two kinds of file are left out. A shared index or summary file that does not list
    this observation contributes nothing, since it holds no data for it; that check runs
    only for PDS3 and only without ``--no-row-files``, so otherwise every
    index file is listed. A PDS3 file whose shelf metadata is missing is left out too,
    with a warning, because its size and checksum are unknown.

    Parameters:
        ctx: The import run's context, for the arguments, the id caches and the logger.
        pds_version: 3 or 4.
        filespec: The observation's primary filespec.
        obs_general_id: The observation's ``obs_general`` row id.
        opus_id: The observation's OPUS id.
        bundle_id: The bundle being imported, for a warning's message.
        instrument_id: The OPUS instrument id.

    Returns:
        One row per file, or no rows at all if the filespec does not name a PDS file,
        which is logged as an error and leaves the index import running.
    """
    rows: list[dict[str, Any]] = []

    try:
        if pds_version == 3:
            pdsf = pdsfile.pds3file.Pds3File.from_filespec(filespec, fix_case=True)
        else:
            pdsf = pdsfile.pds4file.Pds4File.from_filespec(filespec, fix_case=True)
    except ValueError:
        import_util.log_nonrepeating_error(ctx, f'Failed to convert filespec "{filespec}"')
        # The caller extends its row list with the result, so a failed conversion
        # has to yield an empty list rather than None. The error is logged and the
        # index import continues, which is what the caller expects.
        return rows

    products = pdsf.opus_products()
    if '' in products:
        # A product that is not local has no absolute path; it cannot be named in the
        # message, and there is nothing to say about it beyond the ones that can.
        file_list_str = '  '.join([x.abspath for x in products[''][0] if x.abspath is not None])
        if ctx.args.report_empty_products:
            import_util.log_nonrepeating_warning(
                ctx, f'Empty opus_product key for files: {file_list_str}'
            )
        del products['']
    # Keep a running list of all products by type, sorted by version
    for product_type in products:
        (category, sort_order_num, short_name, full_name, default_checked) = product_type

        if category == 'standard':
            pref = 'ZZZZZ1'
        elif category == 'metadata':
            pref = 'ZZZZZ2'
        elif category == 'browse':
            pref = 'ZZZZZ3'
        elif category == 'diagram':
            pref = 'ZZZZZ4'
        else:
            pref_list = category.split(' ')
            pref = pref_list[0][:3]
            if len(pref_list) == 1:
                pref += pref_list[0][-3:]
            else:
                pref += pref_list[-1][:3]
            pref = pref.upper()
        sort_order = pref + f'{sort_order_num:03d}'
        list_of_sublists = products[product_type]

        skip_current_product_type = False

        # rows for current product type
        # Since the opus products output is sorted in alphebatical order, for the opus
        # type of index files, we will visit label file first before visiting the index
        # file. In the case like this, we don't want to include the lable file in the row
        # when the current index product type is skip.
        current_rows: list[dict[str, Any]] = []
        for sublist in list_of_sublists:
            if not ctx.args.no_row_files and skip_current_product_type:
                current_rows = []
                break
            for file_num, file in enumerate(sublist):
                version_number = sublist[0].version_rank
                version_name = sublist[0].version_id
                if version_name == '':
                    version_name = 'Current'
                # Make sure versions other than "Current" are not checked by default
                if version_name != 'Current':
                    default_checked = False
                logical_path = file.logical_path

                # For an index file, we check to see if this observation is
                # present. If not, we don't include the index file in the
                # results.
                # TODO: for PDS4, find_selected_row_key will raise an OSError complaining
                # about missing pickle files in _indexshelf-metadata, so for now we will
                # assume the selection is always in the index file and create a row for
                # it in db. Will fix this when pickle files in indexshelf is ready.
                if not ctx.args.no_row_files and file.is_index and pds_version == 3:
                    basename = filespec.split('/')[-1]
                    selection = basename.split('.')[0]
                    try:
                        file.find_selected_row_key(selection, '=', exact_match=True)
                    except KeyError:
                        # can't find the row, we skip this product_type
                        skip_current_product_type = True
                        break
                    except OSError as e:
                        # selection is partially matched, we skip this
                        # product_type
                        import_util.log_warning(
                            ctx,
                            f'{e} - {selection} is partially matched and '
                            + 'does not exist in the table.',
                        )
                        skip_current_product_type = True
                        break
                elif (
                    '_summary.tab' in logical_path
                    or '_index.tab' in logical_path
                    or '_hstfiles.tab' in logical_path
                ):
                    # if an index file has no files in shelves/index
                    import_util.log_nonrepeating_warning(
                        ctx,
                        f'Volume "{bundle_id}" is missing row files under '
                        + f'shelves/index for {logical_path}',
                    )

                # If the pdsfile is expecting the shelf file, check if corresponding
                # shelves/info files exist, if not, we skip the file.
                # For cross pds4 products, don't skip the import if the shelves file
                # doesn't exist.
                if (
                    pds_version == 3
                    and file.shelf_exists_if_expected() is False
                    and not isinstance(file, pdsfile.pds4file.Pds4File)
                ):
                    # TODOPDS4 ^^^
                    import_util.log_nonrepeating_warning(
                        ctx, 'Missing corresponding ' + f'shelves/info for {file.abspath}'
                    )
                    continue

                # The following info are obtained from _info (from shelves/info)
                url = file.url.strip('/')
                checksum = file.checksum
                size = file.size_bytes
                width = file.width or None
                height = file.height or None

                row = {
                    'obs_general_id': obs_general_id,
                    'opus_id': opus_id,
                    'instrument_id': instrument_id,
                    'version_number': version_number,
                    'version_name': version_name,
                    'category': category,
                    'sort_order': sort_order,
                    'product_order': file_num,
                    'short_name': short_name,
                    'full_name': full_name,
                    'logical_path': logical_path,
                    'url': url,
                    'checksum': checksum,
                    'size': size,
                    'width': width,
                    'height': height,
                    'pds_version': pds_version,
                    'default_checked': default_checked,
                }
                current_rows.append(row)
                if size == 0:
                    import_util.log_nonrepeating_warning(
                        ctx, f'File has zero size: {opus_id} {logical_path}'
                    )

            if skip_current_product_type:
                current_rows = []

        rows += current_rows

    for file_number, row in enumerate(rows, 1):
        row['file_number'] = file_number
    return rows
