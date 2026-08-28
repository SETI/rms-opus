"""What a PDS3 volume's obs classes share: index paths and PDS3 time columns.

`opus_import.obs.obs_base.ObsBase` leaves the PDS-version questions unanswered; this
answers them for PDS3. The file specification is the interesting one, because a PDS3
volume's several index files do not spell it the same way.
"""

from typing import cast

import pdsfile

from opus_import.import_util import IndexRow
from opus_import.obs.field_types import FloatField
from opus_import.obs.obs_base import ObsBase


class ObsBasePDS3(ObsBase):
    """What every obs class for a PDS3 volume shares."""

    #############################
    ### Public access methods ###
    #############################


    # Warning: This doesn't work for COCIRS. That's OK for now because there is
    # no supplemental metadata for those volumes.
    def primary_filespec_from_index_row(self, row: IndexRow,
                                        convert_lbl: bool = False,
                                        add_phase_from_row: bool = False,
                                        add_phase_from_inst: bool = False
                                        ) -> str | None:
        """Build a file specification from a row of any of this volume's PDS3 index files.

        Deliberately generic rather than overridden per instrument: within one volume the
        primary, supplemental and geometry indexes spell a file specification differently,
        so the accessors are tried in turn -- ``FILE_SPECIFICATION_NAME`` first, then
        ``PATH_NAME`` joined to ``FILE_NAME``.

        Parameters:
            row: The index row to read.
            convert_lbl: True to run the result through
                `ObsBase.convert_filespec_from_lbl`.
            add_phase_from_row: True to append the phase this row's ``OPUS_ID`` names,
                which is what tells COVIMS's two geometry rows per observation apart.
            add_phase_from_inst: True to append this instance's own phase instead.

        Returns:
            The volume-prefixed path, or None if the row names a different volume, which
            is logged as an error. A row carrying none of the file-specification columns
            yields the volume prefix alone rather than None: the fallback joins
            ``PATH_NAME`` and ``FILE_NAME``, both of which default to empty.
        """
        # Given a row from an index file, return the primary_filespec.
        # This routine is as generic as possible, because within a single volume
        # the formats of the primary index, supplemental index, and geo index files
        # can be different, so it's not worth overriding this function for each
        # instrument.
        # This is just a sanity check. Not all indexes include the bundle/volume ID, so
        # we don't rely on getting it from there.
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
        assert self.bundle is not None
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
        return cast(str | None, ret)


    ###############################
    ### Internal access methods ###
    ###############################

    def _pdsfile_from_filespec(self, filespec: str) -> pdsfile.PdsFile:
        """Return the ``Pds3File`` for a file specification.

        Parameters:
            filespec: The path, relative to the holdings root.

        Returns:
            The ``pdsfile`` object, typed as the ``PdsFile`` base ``Pds3File`` derives
            from. A PDS3 primary file specification often names the ``.LBL`` file, which
            ``from_filespec`` does not accept, so it is converted to the data file first.
        """
        # Create a PdsFile object from a primary filespec.
        # The PDS3 filespec is often the .LBL file, but from_filespec doesn't
        # handle .LBL files because ViewMaster needs to distinguish between
        # .LBL and whatever the data file extension is. So we do the conversion
        # here.
        filespec = self.convert_filespec_from_lbl(filespec)
        return pdsfile.pds3file.Pds3File.from_filespec(filespec, fix_case=True)


    # Helpers for time fields

    def _time_from_index(self, column: str = 'START_TIME') -> FloatField:
        """Read the observation's start time from the primary index row.

        Parameters:
            column: The column holding it, ``START_TIME`` by default.

        Returns:
            The time in seconds TAI, or None if the column is missing or unparsable.
        """
        return self._time_helper('index_row', column)

    def _time_from_supp_index(self, column: str = 'START_TIME') -> FloatField:
        """Read the observation's start time from the supplemental index row.

        Parameters:
            column: The column holding it, ``START_TIME`` by default.

        Returns:
            The time in seconds TAI, or None if the column is missing or unparsable.
        """
        return self._time_helper('supp_index_row', column)

    def _time2_from_index(self, start_time_sec: FloatField,
                          column: str = 'STOP_TIME') -> FloatField:
        """Read the observation's stop time from the primary index row.

        Parameters:
            start_time_sec: The start time, so a stop time that precedes it is caught.
            column: The column holding it, ``STOP_TIME`` by default.

        Returns:
            The time in seconds TAI, or None if the column is missing or unparsable.
        """
        return self._time2_helper('index_row', start_time_sec, column)

    def _time2_from_supp_index(self, start_time_sec: FloatField,
                               column: str = 'STOP_TIME') -> FloatField:
        """Read the observation's stop time from the supplemental index row.

        Parameters:
            start_time_sec: The start time, so a stop time that precedes it is caught.
            column: The column holding it, ``STOP_TIME`` by default.

        Returns:
            The time in seconds TAI, or None if the column is missing or unparsable.
        """
        return self._time2_helper('supp_index_row', start_time_sec, column)

    def _time_from_some_index(self, column: str = 'START_TIME') -> FloatField:
        """Read the observation's start time from whichever index row carries the column.

        Parameters:
            column: The column holding it, ``START_TIME`` by default.

        Returns:
            The time in seconds TAI, or None if the column is missing or unparsable.
        """
        index = self._col_in_some_index(column)
        if index is None:
            self._log_nonrepeating_error(
                f'Column "{column}" not found in supp_index or index')
            return None
        return self._time_helper(index, column=column)

    def _time2_from_some_index(self, time1: FloatField,
                               column: str = 'STOP_TIME') -> FloatField:
        """Read the observation's stop time from whichever index row carries the column.

        Parameters:
            time1: The start time, so a stop time that precedes it is caught.
            column: The column holding it, ``STOP_TIME`` by default.

        Returns:
            The time in seconds TAI, or None if the column is missing or unparsable.
        """
        index = self._col_in_some_index_or_label(column)
        if index is None:
            self._log_nonrepeating_error(
                f'Column "{column}" not found in supp_index or index')
            return None
        return self._time2_helper(index, time1, column=column)
