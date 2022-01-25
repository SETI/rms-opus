################################################################################
# obs_instrument_gossi.py
#
# Defines the ObsInstrumentGOSSI class, which encapsulates fields in the
# obs_instrument_gossi table.
################################################################################

from functools import cached_property
import json
import os

import numpy as np

import pdsfile

import impglobals
import import_util
import opus_support

from obs_mission_galileo import ObsMissionGalileo


# GOSSI is 10.16 microRad / pixel and 800x800
_GOSSI_FOV_RAD = 10.16e-6 * 800
_GOSSI_FOV_RAD_DIAG = _GOSSI_FOV_RAD * np.sqrt(2)

# Data from:
#   Title: The Galileo Solid-State Imaging experiment
#   Authors: Belton, M. J. S., Klaasen, K. P., Clary, M. C., Anderson, J. L.,
#            Anger, C. D., Carr, M. H., ,
#   Journal: Space Science Reviews (ISSN 0038-6308), vol. 60, no. 1-4, May 1992,
#            p. 413-455.
#   Bibliographic Code: 1992SSRv...60..413B
# WL MIN/MAX are taken by eye-balling Fig. 3 of the above paper
# Note that min/max are the FULL bandwidth, not just the FWHM
# (WL MIN, WL MAX, EFFECTIVE WL)
_GOSSI_FILTER_WAVELENGTHS = {
    'CLEAR':   (360, 1050, 611),
    'VIOLET':  (360, 440, 404),
    'GREEN':   (510, 610, 559),
    'RED':     (620, 730, 671),
    'IR-7270': (725, 750, 734),
    'IR-7560': (750, 790, 756),
    'IR-8890': (870, 900, 887),
    'IR-9680': (940, 1050, 986),
}


class ObsInstrumentGOSSI(ObsMissionGalileo):
    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)


    ################################
    ### OVERRIDE FROM ObsGeneral ###
    ################################

    @property
    def field_ring_obs_id(self):
        image_num = self._index_row['SPACECRAFT_CLOCK_START_COUNT'].replace('.', '')
        return pl_str + 'J_IMG_GO_SSI_' + image_num

    @property
    def field_planet_id(self):
        # WARNING: This will need to be changed if we ever get additional volumes
        # for Galileo. Right now we set everything to Jupiter rather than basing
        # it on the target name because we only have volumes for the time Galileo
        # was in Jupiter orbit (GO_0017 to GO_0023).
        # XXX Update for new GOSSI volume list
        return 'JUP'

    @cached_property
    def field_target_name(self):
        # XXX COLLAPSE TO SUBFUNCTION
        target_name = self._index_row['TARGET_NAME']
        if target_name in TARGET_NAME_MAPPING:
            target_name = TARGET_NAME_MAPPING[target_name]
        if target_name is None:
            return None
        if target_name not in TARGET_NAME_INFO:
            import_util.announce_unknown_target_name(target_name)
            return None
        target_name_info = TARGET_NAME_INFO[target_name]
        return target_name, target_name_info[2]

    # We actually have no idea what IMAGE_TIME represents - start, mid, stop?
    # We assume it means stop time like it does for Voyager, and because Mark
    # has done some ring analysis with this assumption and it seemed to work OK.
    # So we compute start time by taking IMAGE_TIME and subtracting exposure.
    # If we don't have exposure, we just set them equal so we can still search
    # cleanly.
    @property
    def field_time1(self):
        exposure = self._index_row['EXPOSURE_DURATION']
        return self.field_time2 - exposure/1000

    @property
    def field_time2(self):
        stop_time = self._index_row['IMAGE_TIME']

        try:
            stop_time_sec = julian.tai_from_iso(stop_time)
        except Exception as e:
            import_util.log_nonrepeating_error(
                f'Bad image time format "{stop_time}": {e}')
            return None

        return stop_time_sec

    @property
    def field_observation_duration(self):
        exposure = import_util.safe_column(self._index_row, 'EXPOSURE_DURATION')
        if exposure is None:
            return None
        return exposure / 1000

    @property
    def field_quantity(self):
        return 'REFLECT'

    # We only have the center point for RA,DEC so derive the edges by using the
    # FOV
    def _gossi_ra_helper(self):
        ra = import_util.safe_column(self._index_row, 'RIGHT_ASCENSION')
        dec = import_util.safe_column(self._index_row, 'DECLINATION')
        if ra is None or dec is None:
            return None, None
        delta = np.rad2deg(self._GOSSI_FOV_RAD_DIAG/2 / np.cos(np.deg2rad(dec)))
        ra1 = (ra-delta) % 360
        ra2 = (ra+delta) % 360
        if ra2 < ra1:
            ra1, ra2 = ra2, ra1
        return ra1, ra2

    @property
    def field_right_asc1(self):
        return self._gossi_ra_helper()[0]

    @property
    def field_right_asc2(self):
        return self._gossi_ra_helper()[1]

    @property
    def field_declination1(self):
        dec = import_util.safe_column(self._index_row, 'DECLINATION')
        if dec is None:
            return None
        return dec - np.rad2deg(_GOSSI_FOV_RAD_DIAG/2)

    @property
    def field_declination2(self):
        dec = import_util.safe_column(self._index_row, 'DECLINATION')
        if dec is None:
            return None
        return dec + np.rad2deg(_GOSSI_FOV_RAD_DIAG/2)

    @property
    def field_observation_type(self):
        return 'IMG' # Image


    ############################
    ### OVERRIDE FROM ObsPds ###
    ############################

    @cached_property
    def field_primary_file_spec(self):
        # Format: GO_0017/J0/OPNAV/C0347569700R.IMG
        return self._index_row['FILE_SPECIFICATION_NAME']

    @property
    def field_data_set_id(self):
        return self.data_set_id_from_index

    @property
    def field_product_id(self):
        s = self._index_row['FILE_SPECIFICATION_NAME']

        # The file_spec looks like GO_0017:[J0.OPNAV.C034640]5900R.IMG
        # We want to extract C0346405900R
        idx = file_spec.find('.')
        s = s[idx+1:]
        idx = file_spec.find('.')
        s = s[idx+1:].replace(']', '').replace('.IMG', '')

        return s


    ##################################
    ### OVERRIDE FROM ObsTypeImage ###
    ##################################

    @property
    def field_image_type_id(self):
        return 'FRAM'

    @property
    def field_duration(self):
        return self.field_observation_duration # from ObsGeneral

    @property
    def field_levels(self):
        return 256

    @property
    def field_greater_pixel_size(self):
        return 800

    @property
    def field_lesser_pixel_size(self):
        return 800


    ###################################
    ### OVERRIDE FROM ObsWavelength ###
    ###################################

    def _gossi_wavelength_helper(self):
        filter_name = self._index_row['FILTER_NAME']

        if filter_name not in self._GOSSI_FILTER_WAVELENGTHS:
            import_util.log_nonrepeating_error(
                f'Unknown GOSSI filter name "{filter_name}"')
            return 0

        return _GOSSI_FILTER_WAVELENGTHS[filter_name]

    @cached_property
    def field_wavelength1(self):
        return self._gossi_wavelength_helper()[0] / 1000 # microns

    @cached_property
    def field_wavelength2(self):
        return self._gossi_wavelength_helper()[1] / 1000 # microns

    @property
    def field_waveres1(self):
        wl1 = self.field_wavelength1
        wl2 = self.field_wavelength2
        if wl1 is None or wl2 is None:
            return None
        return wl2 - wl1

    @property
    def field_waveres2(self):
        return self.field_waveres1

    @property
    def field_wave_no1(self):
        return 10000 / self.field_wavelength2 # cm^-1

    @property
    def field_wave_no2(self):
        return 10000 / self.field_wavelength1 # cm^-1

    @cached_property
    def field_wave_no_res1(self):
        wno1 = self.field_wave_no1
        wno2 = self.field_wave_no2
        if wno1 is None or wno2 is None:
            return None
        return wno2 - wno1

    @property
    def field_wave_no_res2(self):
        return self.field_wave_no_res1

    @property
    def field_spec_flag(self):
        return 'N'

    @property
    def field_spec_size(self):
        return None

    @property
    def field_polarization_type(self):
        return 'NONE'


    #######################################
    ### OVERRIDE FROM ObsMissionGalileo ###
    #######################################

    @property
    def field_orbit_number(self):
        return str(self._index_row['ORBIT_NUMBER'])


    ####################################
    ### FIELD METHODS FOR THIS TABLE ###
    ####################################

    @property
    def field_observation_id(self):
        return self._index_row['OBSERVATION_ID']

    @property
    def field_image_id(self):
        return self._index_row['IMAGE_ID']

    @property
    def field_filter_name(self):
        return self._index_row['FILTER_NAME']

    @property
    def field_filter_number(self):
        return self._index_row['FILTER_NUMBER']

    @property
    def field_gain_mode_id(self):
        return self._index_row['GAIN_MODE_ID']

    @property
    def field_frame_duration(self):
        return self._index_row['FRAME_DURATION']

    @property
    def field_obstruction_id(self):
        return self._index_row['OBSTRUCTION_ID']

    @property
    def field_compression_type(self):
        return self._index_row['COMPRESSION_TYPE']
