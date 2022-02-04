################################################################################
# obs_base.py
#
# Defines the ObsBase class, which is the base class for all Obs* classes.
# It contains information on the observation and basic utility methods.
################################################################################

import julian
import pdsfile

from config_targets import (TARGET_NAME_INFO,
                            TARGET_NAME_MAPPING)
from import_util import (log_nonrepeating_error,
                         log_nonrepeating_warning,
                         log_unknown_target_name,
                         safe_column)


class ObsBase(object):
    def __init__(self, volume=None, metadata=None, ignore_errors=False):
        """Initialize an ObsBase object.

        volume          The PDS3 volume ("COISS_2116")
        metadata        The collection of metadata available for this observation.
                        This includes rows from the various index as well as additional
                        information. Note that the metadata structure is updated
                        for each observation even though only a single ObsBase instance
                        is created for each volume. Thus methods have to assume that
                        the metadata has changed between calls and they can't cache
                        results.
        ignore_errors   True if the user argument --import-ignore-errors was
                        given. This bypasses certain errors (like unknown
                        target name) and fakes data so that the import can
                        complete, even though the answer will be wrong.
        """
        self._volume         = volume
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
        # Note it's very important that this can be calculated using ONLY
        # the primary index, not the supplemental index!
        # This is because this (and the subsequent creation of opus_id) is used
        # to actually find the matching row in the supplemental index dictionary.
        raise NotImplementedError


    #############################
    ### Public access methods ###
    #############################

    def __str__(self):
        s  = 'class '+type(self).__name__+'\n'
        s += '  volume = '+str(self._volume)+'\n'
        s += '  ignore_errors = '+str(self._ignore_errors)+'\n'
        return s

    @property
    def volume(self):
        return self._volume

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
            self._log_nonrepeating_error('Unable to create OPUS_ID')
            opus_id = filespec.split('/')[-1]
        self._opus_id_last_filespec = filespec
        self._opus_id_cached = opus_id
        return opus_id

    def opus_id_from_supp_index_row(self, supp_row):
        # This is a helper function used to take a row from the supplemental_index
        # and convert it to an opus_id so that the supplemental_index and other
        # index/geo/inventory files can be cross-referenced. We do this here
        # because the supplemental index files are inconsistent in their formatting.
        volume_id = supp_row.get('VOLUME_ID', None)
        if volume_id is None:
            self._log_nonrepeating_error('Supplemental index missing VOLUME_ID field')
            return None
        filespec = supp_row.get('FILE_SPECIFICATION_NAME')
        if filespec is None:
            self._log_nonrepeating_error('Supplemental index missing FILESPEC field')
            return None
        full_filespec = volume_id + '/' + filespec
        pdsf = self._pdsfile_from_filespec(full_filespec)
        opus_id = pdsf.opus_id
        if not opus_id:
            self._log_nonrepeating_error(
                        'Unable to create OPUS_ID from supplemental index')
            return filespec.split('/')[-1]
        return opus_id


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
        # return None.
        for index in ['supp_index_row', 'index_row']:
            if index in self._metadata and col in self._metadata[index]:
                return index
        return None

    def _col_in_some_index_or_label(self, col):
        # Figure out if col is in the supplemental index or normal index
        # or one of the associated label files and return the index name
        # as appropriate. If not found anywhere, return None.
        for index in ['supp_index_row', 'index_row', 'supp_index_label', 'index_label']:
            if index in self._metadata and col in self._metadata[index]:
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
            return None
        if target_name in TARGET_NAME_MAPPING:
            target_name = TARGET_NAME_MAPPING[target_name]
        if target_name not in TARGET_NAME_INFO:
            self._log_unknown_target_name(target_name)
            if self.ignore_errors:
                return 'OTHER'
            return None
        return target_name, TARGET_NAME_INFO[target_name]

    def _convert_filespec_from_lbl(self, filespec):
        # If necessary, convert a primary filespec from a .LBL file to some other
        # extension. The extension is instrument-specific, so this function will
        # be subclassed as necessary.
        # XXX
        return filespec

        # elif filespec.startswith('COUVIS_0'):
        #     filespec = filespec.replace('.LBL', '.DAT')
        # elif (filespec.startswith('VGISS_5') or
        #       filespec.startswith('VGISS_6') or
        #       filespec.startswith('VGISS_7') or
        #       filespec.startswith('VGISS_8')):
        #     filespec = filespec.replace('.LBL', '.IMG')
        # elif filespec.startswith('CORSS_8'):
        #     filespec = filespec.replace('.LBL', '.TAB')
        # elif filespec.startswith('COUVIS_8'):
        #     filespec = filespec.replace('.LBL', '.TAB')
        # elif filespec.startswith('COVIMS_8'):
        #     filespec = filespec.replace('.LBL', '.TAB')


    def _pdsfile_from_filespec(self, filespec):
        # Create a PdsFile object from a primary filespec.
        # The PDS3 filespec is often the .LBL file, but from_filespec doesn't
        # handle .LBL files because ViewMaster needs to distinguish between
        # .LBL and whatever the data file extension is. So we do the conversion
        # here.
        filespec = self._convert_filespec_from_lbl(filespec)
        return pdsfile.PdsFile.from_filespec(filespec, fix_case=True)


    # Helpers for field_obs_general_time[12]

    def _time1_helper(self, index, column):
        # Read and convert the starting time, which can exist in various indexes or
        # columns.
        start_time = safe_column(self._metadata[index], column)

        if start_time is None:
            return None

        try:
            start_time_sec = julian.tai_from_iso(start_time)
        except Exception as e:
            self._log_nonrepeating_error(f'Bad start time format "{start_time}": {e}')
            return None

        return start_time_sec

    def _time2_helper(self, index, start_time_sec, column):
        # Read and convert the ending time, which can exist in various indexes or
        # columns. Compare it to the starting time to make sure they're in the proper
        # order.
        index_row = self._metadata[index]
        stop_time = safe_column(index_row, column)

        if stop_time is None:
            return None

        try:
            stop_time_sec = julian.tai_from_iso(stop_time)
        except Exception as e:
            self._log_nonrepeating_error(f'Bad stop time format "{stop_time}": {e}')
            return None

        if start_time_sec is not None and stop_time_sec < start_time_sec:
            start_time = safe_column(index_row, column1)
            self._log_warning(f'{column} ({start_time}) and ({stop_time}) '
                              'are in the wrong order - setting to start time')
            stop_time_sec = start_time_sec

        return stop_time_sec

    def _time1_from_index(self, column='START_TIME'):
        return self._time1_helper('index_row', column)

    def _time1_from_supp_index(self, column='START_TIME'):
        return self._time1_helper('supp_index_row', column)

    def _time2_from_index(self, start_time_sec, column='STOP_TIME'):
        return self._time2_helper('index_row', start_time_sec, column)

    def _time2_from_supp_index(self, start_time_sec, column='STOP_TIME'):
        return self._time2_helper('supp_index_row', start_time_sec, column)

    def _time1_from_some_index(self):
        index = self._col_in_some_index_or_label('START_TIME')
        if index is None:
            self._log_nonrepeating_error(
                f'Column "START_TIME" not found in supp_index or index')
            return None
        return self._time1_helper(index, 'START_TIME')

    def _time2_from_some_index(self):
        index = self._col_in_some_index_or_label('STOP_TIME')
        if index is None:
            self._log_nonrepeating_error(
                f'Column "STOP_TIME" not found in supp_index or index')
            return None
        return self._time2_helper(index, self.field_obs_general_time1(), 'STOP_TIME')


    # Helpers for field_obs_pds_product_creation_time

    def _product_creation_time_helper(self, index):
        index_row = self._metadata[index]
        pct = index_row['PRODUCT_CREATION_TIME']

        try:
            pct_sec = julian.tai_from_iso(pct)
        except Exception as e:
            import_util.log_nonrepeating_error(
                f'Bad product creation time format "{pct}": {e}')
            return None

        return pct_sec

    def _product_creation_time_from_index(self):
        return self._product_creation_time_helper('index_row')

    def _product_creation_time_from_supp_index(self):
        return self._product_creation_time_helper('supp_index_row')

    def _product_creation_time_from_some_index(self):
        index = self._col_in_some_index_or_label('PRODUCT_CREATION_TIME')
        if index is None:
            self._log_nonrepeating_error(
                f'Column "PRODUCT_CREATION_TIME" not found in supp_index or index')
            return None
        return self._product_creation_time_helper(index)


    ### Error logging ###

    def _log_unknown_target_name(self, target_name):
        log_unknown_target_name(target_name)

    def _log_nonrepeating_warning(self, *args, **kwargs):
        log_nonrepeating_warning(*args, **kwargs)

    def _log_nonrepeating_error(self, *args, **kwargs):
        log_nonrepeating_error(*args, **kwargs)
