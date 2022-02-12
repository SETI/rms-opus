################################################################################
# obs_instrument_gossi.py
#
# Defines the ObsInstrumentGOSSI class, which encapsulates fields in the
# obs_instrument_gossi table.
################################################################################

import numpy as np

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
    'VIOLET':  (360,  440, 404),
    'GREEN':   (510,  610, 559),
    'RED':     (620,  730, 671),
    'IR-7270': (725,  750, 734),
    'IR-7560': (750,  790, 756),
    'IR-8890': (870,  900, 887),
    'IR-9680': (940, 1050, 986),
}


class ObsInstrumentGOSSI(ObsMissionGalileo):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    #############################
    ### OVERRIDE FROM ObsBase ###
    #############################

    @property
    def instrument_id(self):
        return 'GOSSI'

    @property
    def inst_host_id(self):
        return 'GO'

    @property
    def mission_id(self):
        return 'GO'

    @property
    def primary_filespec(self):
        # Note it's very important that this can be calculated using ONLY
        # the primary index, not the supplemental index!
        # This is because this (and the subsequent creation of opus_id) is used
        # to actually find the matching row in the supplemental index dictionary.
        # Format: GO_0017/J0/OPNAV/C0347569700R.IMG
        return self._index_col('FILE_SPECIFICATION_NAME')


    ################################
    ### OVERRIDE FROM ObsGeneral ###
    ################################

    def field_obs_general_observation_duration(self):
        exposure = self._index_col('EXPOSURE_DURATION')
        if exposure is None:
            # Error will be reported under field_obs_general_time1
            return None
        return exposure / 1000


    # We only have the center point for RA,DEC so derive the edges by using the
    # FOV
    def _gossi_ra_helper(self):
        ra = self._index_col('RIGHT_ASCENSION')
        dec = self._index_col('DECLINATION')
        if ra is None or dec is None:
            return None, None
        delta = np.rad2deg(_GOSSI_FOV_RAD_DIAG/2 / np.cos(np.deg2rad(dec)))
        ra1 = (ra-delta) % 360
        ra2 = (ra+delta) % 360
        if ra2 < ra1:
            ra1, ra2 = ra2, ra1
        return ra1, ra2

    def field_obs_general_right_asc1(self):
        return self._gossi_ra_helper()[0]

    def field_obs_general_right_asc2(self):
        return self._gossi_ra_helper()[1]

    def field_obs_general_declination1(self):
        dec = self._index_col('DECLINATION')
        if dec is None:
            return None
        return dec - np.rad2deg(_GOSSI_FOV_RAD_DIAG/2)

    def field_obs_general_declination2(self):
        dec = self._index_col('DECLINATION')
        if dec is None:
            return None
        return dec + np.rad2deg(_GOSSI_FOV_RAD_DIAG/2)

    def field_obs_general_ring_obs_id(self):
        image_num = self._index_col('SPACECRAFT_CLOCK_START_COUNT').replace('.', '')
        return 'J_IMG_GO_SSI_' + image_num

    def field_obs_general_planet_id(self):
        # WARNING: This will need to be changed if we ever get additional volumes
        # for Galileo. Right now we set everything to Jupiter rather than basing
        # it on the target name because we only have volumes for the time Galileo
        # was in Jupiter orbit (GO_0017 to GO_0023).
        # XXX Update for new GOSSI volume list
        return 'JUP'

    # We actually have no idea what IMAGE_TIME represents - start, mid, stop?
    # We assume it means stop time like it does for Voyager, and because Mark
    # has done some ring analysis with this assumption and it seemed to work OK.
    # So we compute start time by taking IMAGE_TIME and subtracting exposure.
    # If we don't have exposure, we just set them equal so we can still search
    # cleanly.
    def field_obs_general_time1(self):
        exposure = self._index_col('EXPOSURE_DURATION')
        if exposure is None:
            self._log_nonrepeating_warning(
                f'Null exposure time for {self.opus_id}')
            exposure = 0
        return self.field_obs_general_time2() - exposure/1000

    def field_obs_general_time2(self):
        return self._time2_from_index(None, column='IMAGE_TIME')

    def field_obs_general_quantity(self):
        return 'REFLECT'

    def field_obs_general_observation_type(self):
        return 'IMG'


    ############################
    ### OVERRIDE FROM ObsPds ###
    ############################

    def field_obs_pds_product_id(self):
        s = self._index_col('FILE_SPECIFICATION_NAME')

        # The filespec looks like GO_0017:[J0.OPNAV.C034640]5900R.IMG
        # We want to extract C0346405900R
        idx = s.find('.')
        s = s[idx+1:]
        idx = s.find('.')
        s = s[idx+1:].replace(']', '').replace('.IMG', '')

        return s

    def field_obs_pds_product_creation_time(self):
        return None


    ##################################
    ### OVERRIDE FROM ObsTypeImage ###
    ##################################

    def field_obs_type_image_image_type_id(self):
        return 'FRAM'

    def field_obs_type_image_duration(self):
        return self.field_obs_general_observation_duration()

    def field_obs_type_image_levels(self):
        return 256

    def field_obs_type_image_greater_pixel_size(self):
        return 800

    def field_obs_type_image_lesser_pixel_size(self):
        return 800


    ###################################
    ### OVERRIDE FROM ObsWavelength ###
    ###################################

    def _gossi_wavelength_helper(self):
        filter_name = self._index_col('FILTER_NAME')

        if filter_name not in _GOSSI_FILTER_WAVELENGTHS:
            self._log_nonrepeating_error(f'Unknown GOSSI filter name "{filter_name}"')
            return 0

        return _GOSSI_FILTER_WAVELENGTHS[filter_name]

    def field_obs_wavelength_wavelength1(self):
        return self._gossi_wavelength_helper()[0] / 1000 # microns

    def field_obs_wavelength_wavelength2(self):
        return self._gossi_wavelength_helper()[1] / 1000 # microns

    def field_obs_wavelength_wave_res1(self):
        return self._wave_res_from_full_bandwidth()

    def field_obs_wavelength_wave_res2(self):
        return self.field_obs_wavelength_wave_res1()

    def field_obs_wavelength_wave_no_res1(self):
        return self._wave_no_res_from_full_bandwidth()

    def field_obs_wavelength_wave_no_res2(self):
        return self.field_obs_wavelength_wave_no_res1()


    #######################################
    ### OVERRIDE FROM ObsMissionGalileo ###
    #######################################

    def field_obs_mission_galileo_orbit_number(self):
        return str(self._index_col('ORBIT_NUMBER'))

    def field_obs_mission_galileo_spacecraft_clock_count1(self):
        sc = self._index_col('SPACECRAFT_CLOCK_START_COUNT')
        try:
            sc_cvt = opus_support.parse_galileo_sclk(sc)
        except Exception as e:
            self._log_nonrepeating_error(f'Unable to parse Galileo SCLK "{sc}": {e}')
            return None
        return sc_cvt

    def field_obs_mission_galileo_spacecraft_clock_count2(self):
        # There is no SPACECRAFT_CLOCK_STOP_COUNT for Galileo
        return self.field_obs_mission_galileo_spacecraft_clock_count1()


    ####################################
    ### FIELD METHODS FOR THIS TABLE ###
    ####################################

    def field_obs_instrument_gossi_opus_id(self):
        return self.opus_id

    def field_obs_instrument_gossi_volume_id(self):
        return self.volume

    def field_obs_instrument_gossi_instrument_id(self):
        return self.instrument_id

    def field_obs_instrument_gossi_observation_id(self):
        return self._index_col('OBSERVATION_ID')

    def field_obs_instrument_gossi_image_id(self):
        return self._index_col('IMAGE_ID')

    def field_obs_instrument_gossi_filter_name(self):
        return self._index_col('FILTER_NAME')

    def field_obs_instrument_gossi_filter_number(self):
        return self._index_col('FILTER_NUMBER')

    def field_obs_instrument_gossi_gain_mode_id(self):
        return self._index_col('GAIN_MODE_ID')

    def field_obs_instrument_gossi_frame_duration(self):
        return self._index_col('FRAME_DURATION')

    def field_obs_instrument_gossi_obstruction_id(self):
        return self._index_col('OBSTRUCTION_ID')

    def field_obs_instrument_gossi_compression_type(self):
        return self._index_col('COMPRESSION_TYPE')
