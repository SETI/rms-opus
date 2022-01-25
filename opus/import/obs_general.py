################################################################################
# obs_general.py
#
# Defines the ObsGeneral class, which encapsulates fields in the
# obs_general table.
################################################################################

from functools import cached_property
import json
import os

import pdsfile

import impglobals
import import_util

from obs_base import ObsBase


class ObsGeneral(ObsBase):
    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)


    ####################################
    ### FIELD METHODS FOR THIS TABLE ###
    ####################################

    @property
    def field_planet_id(self):
        raise NotImplementedError

    @cached_property
    def field_target_name(self):
        raise NotImplementedError

    @property
    def field_time1(self):
        raise NotImplementedError

    @property
    def field_time2(self):
        raise NotImplementedError

    @property
    def field_observation_duration(self):
        # This is the default behavior, but will be overriden for some
        # instruments
        return self.field_time2 - self.field_time1

    @property
    def field_quantity(self):
        raise NotImplementedError

    @property
    def field_right_asc1(self):
        raise None

    @property
    def field_right_asc2(self):
        raise None

    @property
    def field_declination1(self):
        raise None

    @property
    def field_declination2(self):
        raise None

    @property
    def field_observation_type(self):
        raise NotImplementedError

    @property
    def field_ring_obs_id(self):
        raise None

    @property
    def field_target_class(self):
        target_name = self.field_target_name
        target_info = self.get_target_info(target_name)
        if target_info is None:
            return None
        return target_info[1]

    @property
    def field_preview_images(self):
        ### XXX Review this
        pdsf = self.pdsfile_from_filespec(self.field_primary_file_spec)

        try:
            viewset = pdsf.viewset
        except ValueError as e:
            import_util.log_nonrepeating_warning(
                f'ViewSet threw ValueError for "{file_spec}": {e}')
            viewset = None

        if viewset:
            browse_data = viewset.to_dict()
            if not impglobals.ARGUMENTS.import_ignore_missing_images:
                if not viewset.thumbnail:
                    import_util.log_nonrepeating_warning(
                        f'Missing thumbnail browse/diagram image for "{file_spec}"')
                if not viewset.small:
                    import_util.log_nonrepeating_warning(
                        f'Missing small browse/diagram image for "{file_spec}"')
                if not viewset.medium:
                    import_util.log_nonrepeating_warning(
                        f'Missing medium browse/diagram image for "{file_spec}"')
                if not viewset.full_size:
                    import_util.log_nonrepeating_warning(
                        f'Missing full_size browse/diagram image for "{file_spec}"')
        else:
            if impglobals.ARGUMENTS.import_fake_images:
                # impglobals.LOGGER.log('debug',
                #                 f'Faking browse/diagram images for "{file_spec}"')
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
                if (volset in VOLSETS_WITH_PREVIEWS and
                    not impglobals.ARGUMENTS.import_ignore_missing_images):
                    import_util.log_nonrepeating_warning(
                        f'Missing all browse/diagram images for "{file_spec}"')

        ret = json.dumps(browse_data)
        return ret
