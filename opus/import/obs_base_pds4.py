################################################################################
# obs_base_pds4.py
#
# Defines the ObsBasePDS4 class, which augments the ObsBase class with methods
# that are PDS4-specific.
################################################################################

import pdsfile

from obs_base import ObsBase


class ObsBasePDS4(ObsBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    #############################
    ### Public access methods ###
    #############################

    def primary_filespec_from_index_row(self, row,
                                        convert_lbl=False,
                                        add_phase_from_inst=False):
        return row['filepath']


    ###############################
    ### Internal access methods ###
    ###############################

    def _pdsfile_from_filespec(self, filespec):
        return pdsfile.pds4file.Pds4File.from_filespec(filespec, fix_case=True)


    # Helpers for time fields

    def _time_from_index(self, column='pds:start_date_time'):
        return self._time_helper('index_row', column)

    def _time2_from_index(self, start_time_sec, column='pds:stop_date_time'):
        return self._time2_helper('index_row', start_time_sec, column)

    def _time_from_some_index(self, column='pds:start_date_time'):
        return self._time_from_index(column=column)

    def _time2_from_some_index(self, time1, column='pds:stop_date_time'):
        return self._time2_helper('index_row', time1, column=column)
