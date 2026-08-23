################################################################################
# do_import_index.py
#
# Import all of the observations described by a single primary index file. These
# are the per-index internals of do_import, not a step of their own.
################################################################################

import csv

import pdsfile

from opus_import import impglobals, import_util
from opus_import.steps import do_import_mult, do_import_obs, do_import_tables


def import_one_index(bundle_id, vol_info, index_paths, bundle_label_path):
    """Import the observations given a single primary index file."""
    instrument_class = vol_info['instrument_class']
    pds_version = vol_info['pds_version']

    obs_rows, obs_label_dict = import_util.safe_pdstable_read(bundle_label_path,
                                                              pds_version)
    if not obs_rows:
        import_util.log_error(f'Read failed: "{bundle_label_path}"')
        return False

    import_util.log_info(f'OBSERVATIONS: {len(obs_rows)} in {bundle_label_path}')

    metadata = {'phase_name': None,
                'temporal_camera': vol_info['temporal_camera']}

    # Instantiate the appropriate class that knows how to import this instrument
    instrument_obj = instrument_class(
        bundle=bundle_id,
        metadata=metadata
    )

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
        opus_ids = {}
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
            if len(row_nos) == 1: # Only one row means not ambiguous
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
                    impglobals.CURRENT_INDEX_ROW_NUMBER = row_no+1
                    import_util.log_nonrepeating_warning(
                        f'Unable to convert OPUS ID "{opus_id}" to filespec')
            if deriv_filespec is not None:
                for row_no in row_nos:
                    orig_filespec = instrument_obj.primary_filespec_from_index_row(
                                            obs_rows[row_no], convert_lbl=True)
                    orig_filespec = instrument_obj.convert_filespec_from_lbl(
                                                                        orig_filespec)
                    if orig_filespec in deriv_filespec:
                        # Found it!
                        if good_row is not None:
                            import_util.log_nonrepeating_error(
                                f'Found multiple rows that map from the same opus_id '
                                f'{opus_id}: {good_row} and {row_no}')
                        good_row = row_no
            if good_row is None:
                impglobals.CURRENT_INDEX_ROW_NUMBER = row_nos[0]+1
                # This isn't always an error because sometimes we actually do have
                # an opud_id that can't be properly reverse-mapped, like
                # vg-pps-2-u-occ-1986-024-betper-lambda-i
                import_util.log_nonrepeating_warning(
                    f'No row found that reverse matches opus_id {opus_id}')
            else:
                valid_rows[good_row] = True
                import_util.log_info('Resolving OPUS ID ambiguity:')
                for row_no in row_nos:
                    orig_filespec = instrument_obj.primary_filespec_from_index_row(
                                                    obs_rows[row_no], convert_lbl=True)
                    sfx = ' (chosen)' if row_no == good_row else ''
                    import_util.log_info('  '+orig_filespec+sfx)

        old_obs_rows = obs_rows
        obs_rows = []
        for row_no, row in enumerate(old_obs_rows):
            if valid_rows[row_no]:
                obs_rows.append(row)
            else:
                impglobals.CURRENT_INDEX_ROW_NUMBER = row_no+1
                import_util.log_info('Dropping index row '+
                                     instrument_obj.primary_filespec_from_index_row(row))

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
                if (not basename_upper.endswith('SUMMARY.LBL') and
                    not basename_upper.endswith('SUPPLEMENTAL_INDEX.LBL') and
                    not basename_upper.endswith('INVENTORY.LBL')):
                    continue
                assoc_label_path = import_util.safe_join(index_path, basename)
                if basename_upper.endswith('INVENTORY.LBL'):
                    # The inventory files are in CSV format, but the pdstable
                    # module can't read non-fixed-length records so we fake it up
                    # ourselves here.
                    # The old format had as many extra columns as there were targets.
                    # The new format has a single column with the targets separated
                    # by commas.
                    table_filename = (assoc_label_path.replace('.LBL', '.CSV')
                                      .replace('.lbl', '.csv'))
                    assoc_rows = []
                    assoc_label_dict = {} # Not used
                    with open(table_filename) as table_file:
                        csvreader = csv.reader(table_file)
                        for row in csvreader:
                            if len(row) > 2 and row[2].count('-') > 1:
                                # Old format with OPUS ID column
                                (csv_bundle, csv_filespec, csv_ringobsid,
                                 *csv_targets) = row
                            else:
                                # New format without OPUS ID column
                                csv_ringobsid = None
                                (csv_bundle, csv_filespec, *csv_targets) = row
                            if len(csv_targets) == 1:
                                csv_targets = csv_targets[0].split(',')  # New format
                            row_dict = {'BUNDLE_ID': csv_bundle.strip(),
                                        'FILE_SPECIFICATION_NAME': csv_filespec.strip(),
                                        'TARGET_LIST': csv_targets}
                            if csv_ringobsid:
                                row_dict['OPUS_ID'] = csv_ringobsid.strip()

                            assoc_rows.append(row_dict)
                else:
                    (assoc_rows,
                     assoc_label_dict) = import_util.safe_pdstable_read(assoc_label_path,
                                                                        pds_version)

                if assoc_rows is None:
                    # No need to report an error here because safe_pdstable_read
                    # will have already done so
                    return False

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
                        f'{assoc_type.upper()}: {len(assoc_rows)} in {assoc_label_path}')
                assoc_dict = metadata.get(assoc_type, {})
                if assoc_type in ('ring_geo', 'surface_geo', 'sky_geo', 'inventory'):
                    for row in assoc_rows:
                        # We use add_phase_from_row=True here because in COVIMS_0xxx
                        # there are both _IR and _VIS versions of each geo row and we
                        # need a way to distinguish between them. It does nothing
                        # for other cases.
                        key = instrument_obj.primary_filespec_from_index_row(
                                                                row, convert_lbl=True,
                                                                add_phase_from_row=True)
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
                                    f'{assoc_label_path} is missing TARGET_NAME or BODY_NAME field')
                                break
                            if key not in assoc_dict:
                                assoc_dict[key] = {}
                            assoc_dict[key][key2] = row

                else:
                    assert assoc_type == 'supp_index'
                    for row in assoc_rows:
                        key = instrument_obj.primary_filespec_from_index_row(
                                                                row, convert_lbl=True)
                        if key is not None:
                            # Error will already be logged if key is None
                            key = key.upper()
                            assoc_dict[key] = row

                # We need to be able to look things up in both the main tab file and
                # also the associate label, because different instruments store
                # useful data in both places.
                metadata[assoc_type] = assoc_dict
                metadata[assoc_type+'_label'] = assoc_label_dict

    table_schemas, table_names_in_order = do_import_tables.create_tables_for_import(bundle_id,
                                                                                    'import')

    # It's time to actually compute the values that will go in the database!
    # Start with the obs_general table, because other tables reference
    # it with foreign keys. Then do general, mission, and instrument in that
    # order. Later come things like type_id, wavelength, and ring_geo. Finally
    # take care of surface geometry, which has to be done once for each target
    # in the image, so is handled separately.
    table_rows = {}
    for table_name in table_names_in_order:
        table_rows[table_name] = []

    # Also look for duplicates in the existing import tables
    if impglobals.ARGUMENTS.import_check_duplicate_id:
        used_opus_id_prev_vol = do_import_tables.read_existing_import_opus_id()
    else:
        used_opus_id_prev_vol = set()

    used_targets = set()

    ##############################################
    ### MASTER LOOP - IMPORT ONE ROW AT A TIME ###
    ##############################################

    for index_row_num, index_row in enumerate(obs_rows):
        metadata['index_row'] = index_row
        metadata['index_row_num'] = index_row_num+1
        metadata['phase_name'] = None
        obs_general_row = None
        obs_pds_row = None
        impglobals.CURRENT_INDEX_ROW_NUMBER = index_row_num+1

        # Sometimes the primary_filespec is taken from the supplemental index, which we
        # don't have yet, so we can't look it up until later.
        impglobals.CURRENT_PRIMARY_FILESPEC = None

        # For supplemental_index and logging
        # Note we don't use primary_filespec_from_index_row here because that doesn't
        # currently work with CIRS, which makes the logging not give full
        # row information.
        primary_filespec = instrument_obj.primary_filespec
        primary_filespec = instrument_obj.convert_filespec_from_lbl(primary_filespec)
        impglobals.CURRENT_PRIMARY_FILESPEC = primary_filespec
        primary_filespec = primary_filespec.upper()
        if 'supp_index' in metadata:
            supp_index = metadata['supp_index']
            if primary_filespec in supp_index:
                metadata['supp_index_row'] = supp_index[primary_filespec]
            else:
                import_util.log_nonrepeating_warning(
                    f'FILESPEC "{primary_filespec}" is missing supplemental data')
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
                                                            index_row, convert_lbl=True,
                                                            add_phase_from_inst=True)
            primary_filespec_phase = primary_filespec_phase.upper()
            if 'ring_geo' in metadata:
                ring_geo = metadata['ring_geo'].get(primary_filespec_phase, None)
                metadata['ring_geo_row'] = ring_geo
                if (ring_geo is None and
                    impglobals.ARGUMENTS.import_report_missing_ring_geo):
                    import_util.log_warning(
                        f'RING GEO metadata missing for "{primary_filespec_phase}"')
            if 'sky_geo' in metadata:
                sky_geo = metadata['sky_geo'].get(primary_filespec_phase, None)
                metadata['sky_geo_row'] = sky_geo
                if (sky_geo is None and
                    impglobals.ARGUMENTS.import_report_missing_sky_geo):
                    import_util.log_warning(
                        f'SKY GEO metadata missing for "{primary_filespec_phase}"')
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
                row = do_import_obs.import_observation_table(instrument_obj,
                                                             table_name,
                                                             table_schemas[table_name],
                                                             metadata)
                if table_name == 'obs_pds':
                    obs_pds_row = row
                if table_name == 'obs_general':
                    obs_general_row = row
                    opus_id = row['opus_id']
                    if opus_id in used_opus_id_prev_vol:
                        # Some of the GO_xxxx and COUVIS_xxxx bundles have
                        # duplicate observations across bundles. In these cases
                        # we have to use the NEW one and delete the old one
                        # from the database itself. Note this will only be
                        # triggered if we have already loaded the previous
                        # bundle into the import tables but not clear them out.
                        # In the case where we copied them to the perm tables
                        # and cleared them out, a future check during the copy
                        # process will catch the duplicates.
                        do_import_tables.delete_opus_id_from_obs_tables(opus_id, 'import')
                table_rows[table_name].append(row)
                metadata[table_name+'_row'] = row

            assert obs_general_row is not None

            # Handle obs_surface_geometry_name and
            # obs_surface_geometry__<TARGET>

            target_dict = {}
            if 'surface_geo' in metadata:
                surface_geo_dict = metadata['surface_geo']
                for table_name in table_names_in_order:
                    if not table_name.startswith('obs_surface_geometry_'):
                        # Deal with obs_surface_geometry_name and
                        # obs_surface_geometry__<TARGET> only
                        continue
                    # Here we are handling both obs_surface_geometry_name and
                    # obs_surface_geometry as well as all of the
                    # obs_surface_geometry__<TARGET> tables

                    # Retrieve the opus_id from obs_general to find the
                    # surface_geo
                    target_dict = surface_geo_dict.get(primary_filespec_phase, {})
                    for target_name in sorted(target_dict.keys()):
                        used_targets.add(target_name)
                        # Note the following only affects
                        # obs_surface_geometry__<T> not the generalized
                        # obs_surface_geometry. This is fine because we want the
                        # generalized obs_surface_geometry to include all the
                        # targets.
                        new_target_name = import_util.table_name_for_sfc_target(
                                                                target_name)
                        new_table_name = table_name.replace('<TARGET>',
                                                            new_target_name)
                        metadata['surface_geo_row'] = target_dict[
                                                                target_name]
                        metadata['surface_geo_target_name'] = target_name

                        row = do_import_obs.import_observation_table(instrument_obj,
                                                                     new_table_name,
                                                                     table_schemas[table_name],
                                                                     metadata)
                        if new_table_name not in table_rows:
                            table_rows[new_table_name] = []
                            import_util.log_debug(
                              f'Creating surface geo table for new target {target_name}')
                        table_rows[new_table_name].append(row)

            if instrument_obj.surface_geo_target_list():
                # The are some cases (like COCIRS_[01]xxx) where the index files
                # contain the surface geo information instead of a separate
                # summary file. In these cases we ask the instrument for the list of
                # targets and process them directly.
                for table_name in table_names_in_order:
                    if not table_name.startswith('obs_surface_geometry_'):
                        # Deal with obs_surface_geometry_name and
                        # obs_surface_geometry__<TARGET> only
                        continue
                    # Here we are handling both obs_surface_geometry_name and
                    # obs_surface_geometry as well as all of the
                    # obs_surface_geometry__<TARGET> tables

                    for target_name in instrument_obj.surface_geo_target_list():
                        used_targets.add(target_name)
                        # Note the following only affects
                        # obs_surface_geometry__<T> not the generalized
                        # obs_surface_geometry. This is fine because we want the
                        # generalized obs_surface_geometry to include all the
                        # targets.
                        new_target_name = import_util.table_name_for_sfc_target(
                                                                target_name)
                        new_table_name = table_name.replace('<TARGET>',
                                                            new_target_name)
                        metadata['surface_geo_row'] = None
                        metadata['surface_geo_target_name'] = target_name

                        row = do_import_obs.import_observation_table(instrument_obj,
                                                                     new_table_name,
                                                                     table_schemas[table_name],
                                                                     metadata)
                        if new_table_name not in table_rows:
                            table_rows[new_table_name] = []
                            import_util.log_debug(
                              f'Creating surface geo table for new target {target_name}')
                        table_rows[new_table_name].append(row)


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

                row = do_import_obs.import_observation_table(instrument_obj,
                                                             table_name,
                                                             table_schemas[table_name],
                                                             metadata)
                if table_name not in table_rows:
                    table_rows[new_table_name] = []
                table_rows[table_name].append(row)

            # Handle obs_files

            if 'obs_files' not in table_rows:
                table_rows['obs_files'] = []
            for table_name in table_names_in_order:
                if table_name != 'obs_files':
                    # Deal with obs_files only
                    continue
                rows = get_opus_products_rows_for_filespec(
                                vol_info['pds_version'],
                                obs_pds_row['primary_filespec'],
                                obs_general_row['id'],
                                obs_general_row['opus_id'],
                                obs_general_row['bundle_id'],
                                obs_general_row['instrument_id'])
                table_rows[table_name].extend(rows)


    #################################################################
    ### DONE COMPUTING ROW CONTENTS - CREATE MULTS AND DUMP TO DB ###
    #################################################################

    impglobals.CURRENT_INDEX_ROW_NUMBER = None
    impglobals.CURRENT_PRIMARY_FILESPEC = None

    # Now that we have all the values, we have to dump out the mult tables
    # because they are referenced as foreign keys
    do_import_mult.dump_import_mult_tables()

    # Now dump out the obs tables, in order, because at least obs_general
    # is referenced by foreign keys.
    for table_name in table_names_in_order:
        if table_name.find('<TARGET>') == -1:
            imp_name = impglobals.DATABASE.convert_raw_to_namespace('import', table_name)
            import_util.log_debug(f'Inserting into obs table "{imp_name}"')
            impglobals.DATABASE.insert_rows('import', table_name, table_rows[table_name])
        else:
            for target_name in sorted(used_targets):
                new_table_name = table_name.replace(
                            '<TARGET>',
                            import_util.table_name_for_sfc_target(target_name))
                imp_name = impglobals.DATABASE.convert_raw_to_namespace('import',
                                                                        new_table_name)
                import_util.log_debug(f'Inserting into obs table "{imp_name}"')
                surface_geo_schema = import_util.read_schema_for_table(
                                            'obs_surface_geometry_target',
                                            replace=[
                    ('<TARGET>', import_util.table_name_for_sfc_target(target_name)),
                    ('<SLUGTARGET>', import_util.slug_name_for_sfc_target(target_name))])
                # We can finally get around to creating the
                # obs_surface_geometry_<T> tables now that we know what targets
                # we have
                impglobals.DATABASE.create_table('import', new_table_name,
                                                 surface_geo_schema)
                impglobals.DATABASE.insert_rows('import', new_table_name,
                                                table_rows[new_table_name])

    return True # SUCCESS!


def get_opus_products_rows_for_filespec(pds_version, filespec, obs_general_id,
                                        opus_id, bundle_id, instrument_id):
    rows = []

    try:
        if pds_version == 3:
            pdsf = pdsfile.pds3file.Pds3File.from_filespec(filespec, fix_case=True)
        else:
            pdsf = pdsfile.pds4file.Pds4File.from_filespec(filespec, fix_case=True)
    except ValueError:
        import_util.log_nonrepeating_error(f'Failed to convert filespec "{filespec}"')
        return

    products = pdsf.opus_products()
    if '' in products:
        file_list_str = '  '.join([x.abspath for x in products[''][0]])
        if impglobals.ARGUMENTS.import_report_empty_products:
            import_util.log_nonrepeating_warning(
                f'Empty opus_product key for files: {file_list_str}')
        del products['']
    # Keep a running list of all products by type, sorted by version
    for product_type in products:
        (category, sort_order_num, short_name,
         full_name, default_checked) = product_type

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
        current_rows = []
        for sublist in list_of_sublists:
            if (not impglobals.ARGUMENTS.import_dont_use_row_files and
                skip_current_product_type):
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
                if (not impglobals.ARGUMENTS.import_dont_use_row_files and
                    file.is_index and pds_version == 3):
                    basename = filespec.split('/')[-1]
                    selection = basename.split('.')[0]
                    try:
                        file.find_selected_row_key(selection, '=',
                                                   exact_match=True)
                    except KeyError:
                        # can't find the row, we skip this product_type
                        skip_current_product_type = True
                        break
                    except OSError as e:
                        # selection is partially matched, we skip this
                        # product_type
                        import_util.log_warning(
                            f'{e} - {selection} is partially matched and ' +
                            'does not exist in the table.')
                        skip_current_product_type = True
                        break
                elif ('_summary.tab' in logical_path or
                      '_index.tab' in logical_path or
                      '_hstfiles.tab' in logical_path):
                    # if an index file has no files in shelves/index
                    import_util.log_nonrepeating_warning(
                        f'Volume "{bundle_id}" is missing row files under '+
                        f'shelves/index for {logical_path}')

                # If the pdsfile is expecting the shelf file, check if corresponding
                # shelves/info files exist, if not, we skip the file.
                # For cross pds4 products, don't skip the import if the shelves file
                # doesn't exist.
                if (pds_version == 3 and file.shelf_exists_if_expected() is False
                        and not isinstance(file, pdsfile.pds4file.Pds4File)):
                    # TODOPDS4 ^^^
                    import_util.log_nonrepeating_warning(
                        'Missing corresponding ' +
                        f'shelves/info for {file.abspath}')
                    continue

                # The following info are obtained from _info (from shelves/info)
                url = file.url.strip('/')
                checksum = file.checksum
                size = file.size_bytes
                width = file.width or None
                height = file.height or None

                if 'obs_files' not in impglobals.MAX_TABLE_ID_CACHE:
                    impglobals.MAX_TABLE_ID_CACHE['obs_files'] = (
                        import_util.find_max_table_id('obs_files'))
                impglobals.MAX_TABLE_ID_CACHE['obs_files'] = (
                    impglobals.MAX_TABLE_ID_CACHE['obs_files']+1)
                table_id = impglobals.MAX_TABLE_ID_CACHE['obs_files']

                row = {'id': table_id,
                       'obs_general_id': obs_general_id,
                       'opus_id': opus_id,
                       'bundle_id': bundle_id,
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
                        f'File has zero size: {opus_id} {logical_path}')

            if skip_current_product_type:
                current_rows = []

        rows += current_rows

    return rows

def remove_opus_id_from_tables(table_rows, opus_id):
    for table_name in table_rows:
        rows = table_rows[table_name]
        i = 0
        while i < len(rows):
            if ('opus_id' in rows[i] and
                rows[i]['opus_id'] == opus_id):
                import_util.log_debug(f'Removing "{opus_id}" from unwritten table '
                                      f'"{table_name}"')
                del rows[i]
                continue # There might be more than one in obs_surface_geometry
            i += 1
