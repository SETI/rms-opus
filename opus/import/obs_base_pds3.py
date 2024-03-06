################################################################################
# obs_base_pds3.py
#
# Defines the ObsBasePDS3 class, which augments the ObsBase class with methods
# that are PDS3-specific.
################################################################################

import pdsfile

from obs_base import ObsBase


class ObsBasePDS3(ObsBase):
    def __init__(self, **kwargs):
        super().__init__(*args, **kwargs)


    #############################
    ### Public access methods ###
    #############################

    # Warning: This doesn't work for COCIRS. That's OK for now because there is
    # no supplemental metadata for those volumes.
    def primary_filespec_from_index_row(self, row, convert_lbl=False,
                                        add_phase_from_row=False,
                                        add_phase_from_inst=False):
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


    ###############################
    ### Internal access methods ###
    ###############################

    def _pdsfile_from_filespec(self, filespec):
        # Create a PdsFile object from a primary filespec.
        # The PDS3 filespec is often the .LBL file, but from_filespec doesn't
        # handle .LBL files because ViewMaster needs to distinguish between
        # .LBL and whatever the data file extension is. So we do the conversion
        # here.
        filespec = self.convert_filespec_from_lbl(filespec)
        return pdsfile.pds3file.Pds3File.from_filespec(filespec, fix_case=True)


    # Helpers for time fields

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
