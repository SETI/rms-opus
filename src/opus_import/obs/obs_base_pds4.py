"""What a PDS4 bundle's obs classes share: index paths and PDS4 time columns.

The PDS4 counterpart of `opus_import.obs.obs_base_pds3`, and a much shorter one: a PDS4
index names its file the same way in every table, and its time columns are named by the
PDS4 dictionary rather than per instrument.
"""

from typing import cast

import pdsfile

from opus_import.import_util import IndexRow
from opus_import.obs.field_types import FloatField
from opus_import.obs.obs_base import ObsBase


class ObsBasePDS4(ObsBase):
    """What every obs class for a PDS4 bundle shares."""

    #############################
    ### Public access methods ###
    #############################

    def primary_filespec_from_index_row(
        self,
        row: IndexRow,
        convert_lbl: bool = False,
        add_phase_from_row: bool = False,
        add_phase_from_inst: bool = False,
    ) -> str | None:
        """Return the file specification a PDS4 index row carries.

        A PDS4 index names the file the same way in every one of its tables, so unlike the
        PDS3 version this needs no reconciling and ignores every option.

        Parameters:
            row: The index row to read.
            convert_lbl: Ignored; a PDS4 file specification already names the data file.
            add_phase_from_row: Ignored; no PDS4 bundle splits an index row into phases.
            add_phase_from_inst: Ignored, for the same reason.

        Returns:
            The path the row's ``filepath`` column holds.
        """
        return cast(str | None, row['filepath'])

    ###############################
    ### Internal access methods ###
    ###############################

    def _pdsfile_from_filespec(self, filespec: str) -> pdsfile.PdsFile:
        """Return the ``Pds4File`` for a file specification.

        Parameters:
            filespec: The path, relative to the holdings root.

        Returns:
            The ``pdsfile`` object, typed as the ``PdsFile`` base ``Pds4File`` derives
            from.
        """
        return pdsfile.pds4file.Pds4File.from_filespec(filespec, fix_case=True)

    # Helpers for time fields

    def _time_from_index(self, column: str = 'pds:start_date_time') -> FloatField:
        """Read the observation's start time from the primary index row.

        Parameters:
            column: The column holding it, ``pds:start_date_time`` by default.

        Returns:
            The time in seconds TAI, or None if the column is missing or unparsable.
        """
        return self._time_helper('index_row', column)

    def _time2_from_index(
        self, start_time_sec: FloatField, column: str = 'pds:stop_date_time'
    ) -> FloatField:
        """Read the observation's stop time from the primary index row.

        Parameters:
            start_time_sec: The start time, so a stop time that precedes it is caught.
            column: The column holding it, ``pds:stop_date_time`` by default.

        Returns:
            The time in seconds TAI, or None if the column is missing or unparsable.
        """
        return self._time2_helper('index_row', start_time_sec, column)

    def _time_from_some_index(self, column: str = 'pds:start_date_time') -> FloatField:
        """Read the observation's start time from whichever index row carries the column.

        Parameters:
            column: The column holding it, ``pds:start_date_time`` by default.

        Returns:
            The time in seconds TAI, or None if the column is missing or unparsable.
        """
        return self._time_from_index(column=column)

    def _time2_from_some_index(
        self, time1: FloatField, column: str = 'pds:stop_date_time'
    ) -> FloatField:
        """Read the observation's stop time from whichever index row carries the column.

        Parameters:
            time1: The start time, so a stop time that precedes it is caught.
            column: The column holding it, ``pds:stop_date_time`` by default.

        Returns:
            The time in seconds TAI, or None if the column is missing or unparsable.
        """
        return self._time2_helper('index_row', time1, column=column)
