from functools import cached_property

import pdsfile

from config_data import (TARGET_NAME_INFO,
                         TARGET_NAME_MAPPING)


class ObsBase(object):
    def __init__(self, volume_id=None, volset=None, mission_abbrev=None,
                       instrument_name=None, inst_host_id=None,
                       index_row=None):
        self._volume_id = volume_id
        self._volset = volset
        self._mission_abbrev = mission_abbrev
        self._instrument_name = instrument_name
        self._inst_host_id = inst_host_id
        self._index_row = index_row

    @cached_property
    def opus_id(self):
        file_spec = self.field_primary_file_spec
        pdsf = ObsBase.pdsfile_from_filespec(file_spec)
        opus_id = pdsf.opus_id
        if not opus_id:
            import_util.log_nonrepeating_error(
                f'Unable to create OPUS_ID for FILE_SPEC "{file_spec}"')
            return file_spec.split('/')[-1]
        return opus_id

    @property
    def field_opus_id(self):
        return self.opus_id

    @property
    def field_volume_id(self):
        return self._volume_id

    @property
    def field_instrument_id(self):
        return self._instrument_name

    @property
    def field_mission_id(self):
        return self._mission_abbrev

    @property
    def field_inst_host_id(self):
        return self._inst_host_id

    @property
    def field_primary_file_spec(self):
        # This is here instead of ObsGeneral because the field exists in both
        # the obs_general and obs_pds tables.
        assert NotImplementedError

    @staticmethod
    def get_target_info(target_name):
        if target_name is None:
            return None
        if target_name in TARGET_NAME_MAPPING:
            target_name = TARGET_NAME_MAPPING[target_name]
        if target_name not in TARGET_NAME_INFO:
            import_util.announce_unknown_target_name(target_name)
            if impglobals.ARGUMENTS.import_ignore_errors:
                return 'OTHER'
            return None
        return TARGET_NAME_INFO[target_name]

    @staticmethod
    def pdsfile_from_filespec(filespec):
        # The PDS3 filespec is often the .LBL file, but from_filespec doesn't
        # handle .LBL files because ViewMaster needs to distinguish between
        # .LBL and whatever the data file extension is. So we do the conversion
        # here.
        if filespec.startswith('NH'):
            filespec = filespec.replace('.lbl', '.fit')
            filespec = filespec.replace('.LBL', '.FIT')
        elif filespec.startswith('COUVIS_0'):
            filespec = filespec.replace('.LBL', '.DAT')
        elif (filespec.startswith('VGISS_5') or
              filespec.startswith('VGISS_6') or
              filespec.startswith('VGISS_7') or
              filespec.startswith('VGISS_8')):
            filespec = filespec.replace('.LBL', '.IMG')
        elif filespec.startswith('CORSS_8'):
            filespec = filespec.replace('.LBL', '.TAB')
        elif filespec.startswith('COUVIS_8'):
            filespec = filespec.replace('.LBL', '.TAB')
        elif filespec.startswith('COVIMS_8'):
            filespec = filespec.replace('.LBL', '.TAB')
        elif filespec.startswith('EBROCC'):
            filespec = filespec.replace('.LBL', '.TAB')

        return pdsfile.PdsFile.from_filespec(filespec, fix_case=True)

    def populate_helper_longitude_field(**kwargs):
        metadata = kwargs['metadata']
        field_name = metadata['field_name']
        table_name = metadata['table_name']
        row = metadata[table_name+'_row']

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

    def populate_helper_d_longitude_field(**kwargs):
        metadata = kwargs['metadata']
        field_name = metadata['field_name']
        table_name = metadata['table_name']
        row = metadata[table_name+'_row']

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
