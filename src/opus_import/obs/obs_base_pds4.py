################################################################################
# obs_base_pds4.py
#
# Defines the ObsBasePDS4 class, which augments the ObsBase class with methods
# that are PDS4-specific.
################################################################################

from typing import Any, cast

import pdsfile

from opus_import.import_util import IndexRow
from opus_import.obs.field_types import FloatField
from opus_import.obs.obs_base import ObsBase


class ObsBasePDS4(ObsBase):
    #############################
    ### Public access methods ###
    #############################

    def primary_filespec_from_index_row(self, row: IndexRow,
                                        convert_lbl: bool = False,
                                        add_phase_from_row: bool = False,
                                        add_phase_from_inst: bool = False
                                        ) -> str | None:
        return cast(str | None, row['filepath'])


    ###############################
    ### Internal access methods ###
    ###############################

    def _pdsfile_from_filespec(self, filespec: str) -> Any:
        return pdsfile.pds4file.Pds4File.from_filespec(filespec, fix_case=True)


    # Helpers for time fields

    def _time_from_index(self,
                         column: str = 'pds:start_date_time') -> FloatField:
        return self._time_helper('index_row', column)

    def _time2_from_index(self, start_time_sec: FloatField,
                          column: str = 'pds:stop_date_time') -> FloatField:
        return self._time2_helper('index_row', start_time_sec, column)

    def _time_from_some_index(self,
                              column: str = 'pds:start_date_time') -> FloatField:
        return self._time_from_index(column=column)

    def _time2_from_some_index(self, time1: FloatField,
                               column: str = 'pds:stop_date_time') -> FloatField:
        return self._time2_helper('index_row', time1, column=column)
