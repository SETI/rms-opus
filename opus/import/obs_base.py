################################################################################
# obs_base.py
#
# Defines the ObsBase class, which is the base class for all Obs* classes.
# It contains information on the observation and basic utility methods.
################################################################################

import json
import pdsfile

from config_targets import (TARGET_NAME_INFO,
                            TARGET_NAME_MAPPING,
                            PLANET_GROUP_MAPPING)
from import_util import (cached_tai_from_iso,
                         log_nonrepeating_error,
                         log_warning,
                         log_nonrepeating_warning,
                         log_unknown_target_name,
                         safe_column)


class ObsBase(object):
    def __init__(self, bundle=None, metadata=None, ignore_errors=False):
        """Initialize an ObsBase object.

        bundle          The PDS3 volume ("COISS_2116") or PDS4 bundle.
        metadata        The collection of metadata available for this observation.
                        This includes rows from the various index as well as additional
                        information. Note that the metadata structure is updated
                        for each observation even though only a single ObsBase instance
                        is created for each bundle/volume. Thus methods have to assume
                        that the metadata has changed between calls and they can't cache
                        results.
        ignore_errors   True if the user argument --import-ignore-errors was
                        given. This bypasses certain errors (like unknown
                        target name) and fakes data so that the import can
                        complete, even though the answer will be wrong.
        """
        self._bundle         = bundle
        self._metadata       = metadata
        self._ignore_errors  = ignore_errors

        self._opus_id_last_filespec = None # For caching opus_id
        self._opus_id_cached        = None


    ###################################
    ### !!! Must override these !!! ###
    ###################################

    @property
    def instrument_id(self):
        raise NotImplementedError

    @property
    def inst_host_id(self):
        raise NotImplementedError

    @property
    def mission_id(self):
        raise NotImplementedError

    @property
    def primary_filespec(self):
        raise NotImplementedError


    #############################
    ### Public access methods ###
    #############################

    def __str__(self):
        s  = 'class '+type(self).__name__+'\n'
        s += '  bundle = '+str(self._bundle)+'\n'
        s += '  ignore_errors = '+str(self._ignore_errors)+'\n'
        return s

    @property
    def bundle(self):
        return self._bundle

    @property
    def phase_name(self):
        return self._metadata['phase_name']

    @property
    def opus_id(self):
        filespec = self.primary_filespec
        if filespec == self._opus_id_last_filespec:
            # Creating the OPUS ID can be expensive so we cache it here because
            # it is used for every obs_ table.
            return self._opus_id_cached
        pdsf = self._pdsfile_from_filespec(filespec)
        opus_id = pdsf.opus_id
        if not opus_id:
            self._log_nonrepeating_error(
                        f'Unable to create OPUS_ID using filespec {filespec}')
            return None
        self._opus_id_last_filespec = filespec
        self._opus_id_cached = opus_id
        return opus_id

    # Warning: This doesn't work for COCIRS. That's OK for now because there is
    # no supplemental metadata for those volumes.
    def primary_filespec_from_index_row(self, row, convert_lbl=False,
                                        add_phase_from_row=False,
                                        add_phase_from_inst=False):
        # Given a row from an index file, return the primary_filespec.
        # This routine is as generic as possible, because within a single bundle/volume
        # the formats of the primary index, supplemental index, and geo index files
        # can be different, so it's not worth overriding this function for each
        # instrument.
        # This is just a sanity check. Not all indexes include the bundle/volume ID, so
        # we don't rely on getting it from there.
        bundle_id = row.get('BUNDLE_ID', None)
        if bundle_id is None:
            bundle_id = row.get('VOLUME_ID', None)
        if bundle_id is None:
            bundle_id = row.get('VOLUME_NAME', None) # VG_[5678]xxx
        if bundle_id is not None and bundle_id.rstrip('/') != self.bundle:
            self._log_nonrepeating_error('Volume ID in index file inconsistent')
            return None

        filespec = row.get('FILE_SPECIFICATION_NAME', None)
        if filespec is None:
            path_name = row.get('PATH_NAME', '').strip('/') # NH
            filename = row.get('FILE_NAME', '').strip('/') # NH and COUVIS_0xxx
            if path_name != '':
                path_name = path_name + '/'
            filespec = path_name + filename
        if filespec is None:
            self._log_nonrepeating_error('Index missing FILESPEC field(s)')
            return None

        # In the case of GOSSI and COUVIS, the volume name is already prepended
        # to the filespec
        ret = filespec.strip('/')
        if not ret.startswith(self.bundle+'/'):
            ret = self.bundle + '/' + filespec.lstrip('/')
        if convert_lbl:
            ret = self.convert_filespec_from_lbl(ret)

        # This is a really horrid hack required because COVIMS_0xxx has two entries
        # per index row in the geo indexes (IR and VIS), but only one entry in the
        # supplemental index. The only way to know which row is which is to look at
        # the OPUS_ID field in the geo index.
        if add_phase_from_row:
            opus_id = row.get('OPUS_ID', None)
            if opus_id is not None:
                components = opus_id.split('_')
                sfx = components[-1]
                if sfx in ('ir', 'vis'):
                    ret += '_'+sfx

        # Likewise, we have to do the same thing when looking up the row, but in
        # this case we have to get the phase name from this instance.
        if add_phase_from_inst and self.phase_name:
            ret += '_'+self.phase_name.lower()
        return ret

    def opus_id_from_index_row(self, row):
        # This is a helper function used to take a row from the supplemental_index
        # and convert it to an opus_id so that the supplemental_index and other
        # index/geo/inventory files can be cross-referenced. We do this here
        # because the supplemental index files are inconsistent in their formatting.
        full_filespec = self.primary_filespec_from_index_row(row)
        try:
            pdsf = self._pdsfile_from_filespec(full_filespec)
        except KeyError:
            self._log_nonrepeating_warning(
                    'Unable to create OPUS_ID from index '+
                    f'using filespec {full_filespec} - internal PdsFile crash')
            return None
        opus_id = pdsf.opus_id
        if not opus_id:
            self._log_nonrepeating_warning(
                    f'Unable to create OPUS_ID from index using filespec {full_filespec}')
            return None
        return opus_id

    def convert_filespec_from_lbl(self, filespec):
        # If necessary, convert a primary filespec from a .LBL file to some other
        # extension. The extension is instrument-specific, so this function will
        # be subclassed as necessary.
        return filespec

    @property
    def phase_names(self):
        # Return a list of names of phases that each row in the index file should go
        # through. Normally this is just a single empty string, but in cases like
        # COVIMS, each index row actually represents two observations - IR and VIS -
        # which would count as two phases. Instruments can override this list as
        # necessary.
        return ['']

    def surface_geo_target_list(self):
        # If the surface_geo info exists somewhere other than in separate summary
        # files, we can give a list of targets this observation supports here.
        # This instrument's surface geo field methods will then be called on
        # each target.
        return None


    ### Helpers for other data_sources ###

    def compute_longitude_field(self):
        # Fill in the value for a LONGITUDE_FIELD data_source. This is the center
        # of a longitude range to enable wrap-around searching.
        field_name = self._metadata['field_name']
        table_name = self._metadata['table_name']
        row = self._metadata[table_name+'_row']

        assert not field_name.startswith('d_'), (table_name, field_name)

        long1 = row[field_name+'1']
        long2 = row[field_name+'2']

        if long1 is None or long2 is None:
            return None

        if long2 >= long1:
            the_long = (long1 + long2)/2.
        else:
            the_long = (long1 + long2 + 360.)/2.

        if the_long >= 360:
            the_long -= 360.
        if the_long < 0:
            the_long += 360.

        return the_long

    def compute_d_longitude_field(self):
        # Fill in the value for a D_LONGITUDE_FIELD data_source. This is the span
        # of a longitude range to enable wrap-around searching.
        field_name = self._metadata['field_name']
        table_name = self._metadata['table_name']
        row = self._metadata[table_name+'_row']

        assert field_name.startswith('d_'), (table_name, field_name)

        field_name = field_name[2:] # Get rid of d_

        long1 = row[field_name+'1']
        long2 = row[field_name+'2']

        if long1 is None or long2 is None:
            return None

        if long2 >= long1:
            the_long = (long1 + long2)/2.
        else:
            the_long = (long1 + long2 + 360.)/2.

        return the_long - long1


    ###############################
    ### Internal access methods ###
    ###############################

    def _index_col(self, col, idx=None):
        return safe_column(self._metadata['index_row'], col, idx=idx)

    def _has_supp_index(self):
        return 'supp_index_row' in self._metadata

    def _supp_index_col(self, col, idx=None):
        return safe_column(self._metadata['supp_index_row'], col, idx=idx)

    def _index_label_col(self, col, idx=None):
        return safe_column(self._metadata['index_label'], col, idx=idx)

    def _supp_index_label_col(self, col, idx=None):
        return safe_column(self._metadata['supp_index_label'], col, idx=idx)

    def _ring_geo_index_col(self, col, idx=None):
        # ring_geo is an optional index file so we allow it to be missing
        if ('ring_geo_row' not in self._metadata or
            self._metadata['ring_geo_row'] is None):
            return None
        return safe_column(self._metadata['ring_geo_row'], col, idx=idx)

    def _surface_geo_index_col(self, col, idx=None):
        # surface_geo is an optional index file so we allow it to be missing
        if ('surface_geo_row' not in self._metadata or
            self._metadata['surface_geo_row'] is None):
            return None
        return safe_column(self._metadata['surface_geo_row'], col, idx=idx)

    def _col_in_index(self, col):
        return col in self._metadata['index_row']

    def _col_in_supp_index(self, col):
        return col in self._metadata['supp_index_row']

    def _col_in_some_index(self, col):
        # Figure out if col is in the supplemental index or normal index
        # and return the index name as appropriate. If not found anywhere,
        # return None. Very important: We prioritize the supplemental index
        # if the field exists in both. This makes a difference for
        # COCIRS_[01]xxx.
        for index in ['supp_index_row', 'index_row']:
            if index in self._metadata and col in self._metadata[index]:
                return index
        return None

    def _col_in_some_index_or_label(self, col):
        # Figure out if col is in the supplemental index or normal index
        # or one of the associated label files and return the index name
        # as appropriate. If not found anywhere, return None.
        for index in ['supp_index_row', 'index_row', 'supp_index_label', 'index_label']:
            if (index in self._metadata and
                self._metadata[index] is not None and
                col in self._metadata[index]):
                return index
        return None

    def _some_index_col(self, col, idx=None):
        index = self._col_in_some_index(col)
        if index is None:
            self._log_nonrepeating_error(
                f'Column "{col}" not found in supp_index or index')
            return None
        return safe_column(self._metadata[index], col, idx=idx)

    def _some_index_or_label_col(self, col, idx=None):
        index = self._col_in_some_index_or_label(col)
        if index is None:
            self._log_nonrepeating_error(
                f'Column "{col}" not found in supp_index or index or their labels')
            return None
        return safe_column(self._metadata[index], col, idx=idx)


    ### Utility functions useful for subclasses ###

    def _get_target_info(self, target_name):
        # Given a target_name, map the name as necessary and return the
        # target_class tuple (planet_id, target_class, pretty name).
        # Example: ('JUP', 'IRR_SAT', 'Callirrhoe')
        if target_name is None:
            return None, None
        target_name = target_name.upper()
        if target_name in TARGET_NAME_MAPPING:
            target_name = TARGET_NAME_MAPPING[target_name]
        if target_name not in TARGET_NAME_INFO:
            self._log_unknown_target_name(target_name)
            if self._ignore_errors:
                return 'OTHER'
            return None, None
        return target_name, TARGET_NAME_INFO[target_name]

    def _get_planet_group_info(self, target_name):
        # Return the planet group info for a passed in target_name
        if target_name not in TARGET_NAME_INFO:
            planet_id = 'OTHER'
        else:
            planet_id = TARGET_NAME_INFO[target_name][0]
            if planet_id is None:
                planet_id = 'OTHER'
        return PLANET_GROUP_MAPPING[planet_id]

    def _create_mult(self, col_val, disp_name=None, disp='Y', disp_order=None,
                     grouping=None, group_disp_order=None, tooltip=None, aliases=None):
        data_dict = {}
        data_dict['col_val'] = col_val
        data_dict['disp'] = disp
        data_dict['disp_name'] = disp_name
        data_dict['disp_order'] = disp_order
        data_dict['grouping'] = grouping
        data_dict['group_disp_order'] = group_disp_order
        data_dict['tooltip'] = tooltip
        data_dict['aliases'] = json.dumps(aliases) if aliases else None
        # For testing purpose: uncomment the following code to hide the Dark field
        # under "Other" in target widget and also store aliases for the field.
        # if col_val == 'DARK':
        #     data_dict['disp'] = 'N'
        #     aliases_list = ['dark_1', 'dark_2', 'dark_3']
        #     data_dict['aliases'] = json.dumps(aliases_list)
        return data_dict

    def _create_mult_keep_case(self, col_val, disp='Y', disp_order=None, grouping=None,
                               group_disp_order=None, tooltip=None, aliases=None):
        return self._create_mult(col_val=col_val, disp_name=col_val, disp=disp,
                                 disp_order=disp_order, grouping=grouping,
                                 group_disp_order=group_disp_order,
                                 tooltip=tooltip, aliases=aliases)

    def _pdsfile_from_filespec(self, filespec):
        # Create a PdsFile object from a primary filespec.
        # The PDS3 filespec is often the .LBL file, but from_filespec doesn't
        # handle .LBL files because ViewMaster needs to distinguish between
        # .LBL and whatever the data file extension is. So we do the conversion
        # here.
        filespec = self.convert_filespec_from_lbl(filespec)
        return pdsfile.PdsFile.from_filespec(filespec, fix_case=True)


    # Helpers for time fields

    def _time_helper(self, index, column):
        # Read and convert a time, which can exist in various indexes or
        # columns.
        the_time = safe_column(self._metadata[index], column)
        if the_time is None:
            return None

        try:
            time_sec = cached_tai_from_iso(the_time)
        except Exception as e:
            self._log_nonrepeating_error(f'Bad {column} format "{the_time}": {e}')
            return None

        return time_sec

    def _time2_helper(self, index, start_time_sec, column):
        # Read and convert the ending time, which can exist in various indexes or
        # columns. Compare it to the starting time to make sure they're in the proper
        # order.
        index_row = self._metadata[index]
        stop_time = safe_column(index_row, column)
        if stop_time is None:
            return None

        try:
            stop_time_sec = cached_tai_from_iso(stop_time)
        except Exception as e:
            self._log_nonrepeating_error(f'Bad {column} format "{stop_time}": {e}')
            return None

        if start_time_sec is not None and stop_time_sec < start_time_sec:
            self._log_nonrepeating_warning(
                        f'{column} start and end ({stop_time}) '+
                        'are in the wrong order - setting to start time')
            stop_time_sec = start_time_sec

        return stop_time_sec

    def _time_from_index(self, column='START_TIME'):
        return self._time_helper('index_row', column)

    def _time_from_supp_index(self, column='START_TIME'):
        return self._time_helper('supp_index_row', column)

    def _time2_from_index(self, start_time_sec, column='STOP_TIME'):
        return self._time2_helper('index_row', start_time_sec, column)

    def _time2_from_supp_index(self, start_time_sec, column='STOP_TIME'):
        return self._time2_helper('supp_index_row', start_time_sec, column)

    def _time_from_some_index(self, column='START_TIME'):
        index = self._col_in_some_index(column)
        if index is None:
            self._log_nonrepeating_error(
                f'Column "{column}" not found in supp_index or index')
            return None
        return self._time_helper(index, column=column)

    def _time2_from_some_index(self, time1, column='STOP_TIME'):
        index = self._col_in_some_index_or_label(column)
        if index is None:
            self._log_nonrepeating_error(
                f'Column "{column}" not found in supp_index or index')
            return None
        return self._time2_helper(index, time1, column=column)


    ### Error logging ###

    def _log_unknown_target_name(self, target_name):
        log_unknown_target_name(target_name)

    def _log_warning(self, *args, **kwargs):
        log_warning(*args, **kwargs)

    def _log_nonrepeating_warning(self, *args, **kwargs):
        log_nonrepeating_warning(*args, **kwargs)

    def _log_nonrepeating_error(self, *args, **kwargs):
        log_nonrepeating_error(*args, **kwargs)
