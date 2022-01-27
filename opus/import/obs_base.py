################################################################################
# obs_base.py
#
# Defines the ObsBase class, which is the base class for all Obs* classes.
# It contains information on the observation and basic utility methods.
################################################################################

import julian
import pdsfile

from config_data import (TARGET_NAME_INFO,
                         TARGET_NAME_MAPPING)
from import_util import (log_nonrepeating_error,
                         log_nonrepeating_warning,
                         log_unknown_target_name,
                         safe_column)


class ObsBase(object):
    def __init__(self, volume=None, volset=None, mission_id=None,
                       instrument_id=None,
                       metadata=None,
                       ignore_errors=False):
        """Initialize an ObsBase object.

        volume          The PDS3 volume ("COISS_2116")
        volset          The PDS3 volset ("COISS_2xxx")
        mission_id      The mission abbreviation ("CO")
        instrument_id   The instrument abbreviation ("COISS")
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
        self._volset         = volset
        self._mission_id     = mission_id
        self._instrument_id  = instrument_id
        self._metadata       = metadata
        self._ignore_errors  = ignore_errors

    def __str__(self):
        s  = 'class '+type(self).__name__+'\n'
        s += '  volume = '+str(self._volume)+'\n'
        s += '  volset = '+str(self._volset)+'\n'
        s += '  mission_id = '+str(self._mission_id)+'\n'
        s += '  ignore_errors = '+str(self._ignore_errors)+'\n'
        return s


    #############################
    ### Public access methods ###
    #############################

    @property
    def volume(self):
        return self._volume

    @property
    def volset(self):
        return self._volset

    @property
    def mission_id(self):
        return self._mission_id

    @property
    def instrument_id(self):
        return self._instrument_id

    @property
    def inst_host_id(self):
        # This will be overriden by instrument subclasses
        raise NotImplementedError


    ### Compute the OPUS ID ###

    @property
    def primary_filespec(self):
        raise NotImplementedError

    @property
    def opus_id(self):
        filespec = self.primary_filespec
        pdsf = self._pdsfile_from_filespec(filespec)
        opus_id = pdsf.opus_id
        if not opus_id:
            self._log_nonrepeating_error('Unable to create OPUS_ID')
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

    def _ring_geo_index_col(self, col, idx=None):
        # ring_geo is an optional index file so we allow it to be missing
        if 'ring_geo_row' not in self._metadata:
            return None
        return safe_column(self._metadata['ring_geo_row'], col, idx=idx)

    def _surface_geo_index_col(self, col, idx=None):
        # surface_geo is an optional index file so we allow it to be missing
        if 'surface_geo_row' not in self._metadata:
            return None
        return safe_column(self._metadata['surface_geo_row'], col, idx=idx)


    ### Error logging ###

    def _log_unknown_target_name(self, target_name):
        log_unknown_target_name(target_name)

    def _log_nonrepeating_warning(self, *args, **kwargs):
        log_nonrepeating_warning(*args, **kwargs)

    def _log_nonrepeating_error(self, *args, **kwargs):
        log_nonrepeating_error(*args, **kwargs)


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
        return TARGET_NAME_INFO[target_name]

    def _convert_filespec_from_lbl(self, filespec):
        # If necessary, convert a primary filespec from a .LBL file to some other
        # extension. The extension is instrument-specific, so this function will
        # be subclassed as necessary.
        # XXX
        return filespec
        # if filespec.startswith('NH'):
        #     filespec = filespec.replace('.lbl', '.fit')
        #     filespec = filespec.replace('.LBL', '.FIT')
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
        # elif filespec.startswith('EBROCC'):
        #     filespec = filespec.replace('.LBL', '.TAB')

    def _pdsfile_from_filespec(self, filespec):
        # Create a PdsFile object from a primary filespec.
        # The PDS3 filespec is often the .LBL file, but from_filespec doesn't
        # handle .LBL files because ViewMaster needs to distinguish between
        # .LBL and whatever the data file extension is. So we do the conversion
        # here.
        filespec = self._convert_filespec_from_lbl(filespec)
        return pdsfile.PdsFile.from_filespec(filespec, fix_case=True)

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
