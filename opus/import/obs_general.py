################################################################################
# obs_general.py
#
# Defines the ObsGeneral class, which encapsulates fields in the
# obs_general table.
################################################################################

import json
import os

import impglobals # XXX

from obs_base import ObsBase


class ObsGeneral(ObsBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    ####################################
    ### FIELD METHODS FOR THIS TABLE ###
    ####################################

    ### Don't override these ###

    def field_obs_general_opus_id(self):
        return self.opus_id

    def field_obs_general_volume_id(self):
        return self.volume

    def field_obs_general_instrument_id(self):
        return self.instrument_id

    def field_obs_general_inst_host_id(self):
        return self.inst_host_id

    def field_obs_general_mission_id(self):
        return self.mission_id

    def field_obs_general_target_class(self):
        target_name = self.field_obs_general_target_name()[0]
        target_name, target_info = self._get_target_info(target_name)
        if target_info is None:
            return None
        return target_info[1]

    def field_obs_general_primary_filespec(self):
        return self.primary_filespec

    def field_obs_general_preview_images(self):
        ### XXX Review this
        pdsf = self._pdsfile_from_filespec(self.primary_filespec)

        try:
            viewset = pdsf.viewset
        except ValueError as e:
            self._log_nonrepeating_warning(
                f'ViewSet threw ValueError for "{filespec}": {e}')
            viewset = None

        if viewset:
            browse_data = viewset.to_dict()
            if not impglobals.ARGUMENTS.import_ignore_missing_images:
                if not viewset.thumbnail:
                    self._log_nonrepeating_warning(
                        f'Missing thumbnail browse/diagram image for "{filespec}"')
                if not viewset.small:
                    self._log_nonrepeating_warning(
                        f'Missing small browse/diagram image for "{filespec}"')
                if not viewset.medium:
                    self._log_nonrepeating_warning(
                        f'Missing medium browse/diagram image for "{filespec}"')
                if not viewset.full_size:
                    self._log_nonrepeating_warning(
                        f'Missing full_size browse/diagram image for "{filespec}"')
        else:
            if impglobals.ARGUMENTS.import_fake_images:
                # impglobals.LOGGER.log('debug',
                #                 f'Faking browse/diagram images for "{filespec}"')
                base_path = os.path.splitext(pdsf.logical_path)[0]
                if base_path.find('CIRS') != -1:
                    base_path = base_path.replace('volumes', 'diagrams')
                    base_path = base_path.replace('DATA/APODSPEC/SPEC',
                                                  'BROWSE/TARGETS/IMG')
                else:
                    base_path = base_path.replace('volumes', 'previews')
                base_path = 'holdings/'+base_path
                ext = 'jpg'
                if (base_path.find('VIMS') != -1 or  # XXX
                    base_path.find('UVIS') != -1):
                    ext = 'png'
                browse_data = {'viewables':
                    [{'url': base_path+'_thumb.'+ext,
                      'bytes': 500, 'width': 100, 'height': 100},
                     {'url': base_path+'_small.'+ext,
                      'bytes': 1000, 'width': 256, 'height': 256},
                     {'url': base_path+'_med.'+ext,
                      'bytes': 2000, 'width': 512, 'height': 512},
                     {'url': base_path+'_full.'+ext, 'name': 'full',
                      'bytes': 4000, 'width': 1024, 'height': 1024}
                     ]
                }
            else:
                browse_data = {'viewables': []}
                # # XXX
                # if (volset in VOLSETS_WITH_PREVIEWS and
                #     not impglobals.ARGUMENTS.import_ignore_missing_images):
                self._log_nonrepeating_warning(
                    f'Missing all browse/diagram images for "{self.primary_filespec}"')

        ret = json.dumps(browse_data)
        return ret


    ################################
    ### ! Might override these ! ###
    ################################

    def field_obs_general_target_name(self):
        target_name = self._some_index_or_label_col('TARGET_NAME')
        target_name, target_info = self._get_target_info(target_name)
        if target_info is None:
            return None
        return target_name, target_info[2]

    def field_obs_general_time1(self):
        return self._time1_from_some_index()

    def field_obs_general_time2(self):
        return self._time2_from_some_index()

    def field_obs_general_observation_duration(self):
        # This is the default behavior, but will be overriden for some
        # instruments
        return max(self.field_obs_general_time2() - self.field_obs_general_time1(), 0)

    def field_obs_general_right_asc1(self):
        return None

    def field_obs_general_right_asc2(self):
        return None

    def field_obs_general_declination1(self):
        return None

    def field_obs_general_declination2(self):
        return None

    def field_obs_general_ring_obs_id(self):
        return None


    ###################################
    ### !!! Must override these !!! ###
    ###################################

    def field_obs_general_planet_id(self):
        raise NotImplementedError

    def field_obs_general_quantity(self):
        raise NotImplementedError

    def field_obs_general_observation_type(self):
        raise NotImplementedError
