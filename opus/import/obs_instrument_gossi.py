################################################################################
# obs_instrument_gossi.py
#
# Defines the ObsInstrumentGOSSI class, which encapsulates fields in the
# common, obs_mission_galileo, and obs_instrument_gossi tables for GO_0xxx.
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


# GO_0016 has a bunch of SL9 observations that have the same primary filespec.
# This causes problems because they map to the same opus id. We have fixed this
# by creating a separate go_0016_sl9_index.tab file that summaries these by group,
# replacing single scalar fields like IMAGE_TIME and SPACECRAFT_CLOCK_START_COUNT
# with MINIMUM_* and MAXIMUM_* versions. We ignore the SL9 files in the main
# index by returning a NULL opus id, and then handle them from the sl9_index by
# looking to see where there is a <field> or MINIMUM/MAXIMUM_<field> in the index.
# What a mess for only 13 observations...

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
        return self.volume + '/' + self._index_col('FILE_SPECIFICATION_NAME')

    def opus_id_from_index_row(self, row):
        # SL9 entries from the main index are ignored because those are in the
        # sl9_index file.
        if 'SPACECRAFT_CLOCK_START_COUNT' in row:
            # We're looking at the main index
            if 'SL9' in row['FILE_SPECIFICATION_NAME']:
                return None
        return super().opus_id_from_index_row(row)


    ################################
    ### OVERRIDE FROM ObsGeneral ###
    ################################

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
        if self._index_col('ORBIT_NUMBER') is None:
            return None
        if not self._col_in_index('SPACECRAFT_CLOCK_START_COUNT'):
            return None # SL9 - they didn't exist before anyway
        image_num = self._index_col('SPACECRAFT_CLOCK_START_COUNT').replace('.', '')
        return 'J_IMG_GO_SSI_' + image_num

    def field_obs_general_planet_id(self):
        if self._index_col('ORBIT_NUMBER') is None:
            return self._create_mult('OTH')
        return self._create_mult('JUP')

    # We actually have no idea what IMAGE_TIME represents - start, mid, stop?
    # We assume it means stop time like it does for Voyager, and because Mark
    # has done some ring analysis with this assumption and it seemed to work OK.
    # So we compute start time by taking IMAGE_TIME and subtracting exposure.
    # If we don't have exposure, we just set them equal so we can still search
    # cleanly.
    # For SL9, we have a min/max for IMAGE_TIME, but play the same game.
    def field_obs_general_time1(self):
        if self._col_in_index('IMAGE_TIME'):
            time2 = self.field_obs_general_time2()
        else:
            time2 = self._time_from_index(column='MINIMUM_IMAGE_TIME')
        if time2 is None:
            return None
        exposure = self._index_col('EXPOSURE_DURATION')
        if exposure is None:
            self._log_nonrepeating_warning(f'Null exposure time for {self.opus_id}')
            exposure = 0
        return time2 - exposure/1000

    def field_obs_general_time2(self):
        if self._col_in_index('IMAGE_TIME'):
            if self._index_col('IMAGE_TIME') == 'UNK':
                return None
            return self._time2_from_index(None, column='IMAGE_TIME')
        return self._time2_from_index(None, column='MAXIMUM_IMAGE_TIME')

    def field_obs_general_observation_duration(self):
        time1 = self.field_obs_general_time1()
        time2 = self.field_obs_general_time2()
        if time1 is None or time2 is None:
            exposure = self._index_col('EXPOSURE_DURATION')
            if exposure is None:
                return None
            return exposure/1000
        return max(time2 - time1, 0)

    def field_obs_general_quantity(self):
        return self._create_mult('REFLECT')

    def field_obs_general_observation_type(self):
        return self._create_mult('IMG')


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
        return self._create_mult('FRAM')

    def field_obs_type_image_duration(self):
        exposure = self._index_col('EXPOSURE_DURATION')
        if exposure is None:
            return self.field_obs_general_observation_duration()
        return exposure/1000

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
        orbit = self._index_col('ORBIT_NUMBER')
        if orbit is None:
            return None
        return str(orbit)

    def field_obs_mission_galileo_spacecraft_clock_count1(self):
        if self._col_in_index('SPACECRAFT_CLOCK_START_COUNT'):
            sc = self._index_col('SPACECRAFT_CLOCK_START_COUNT')
        else:
            sc = self._index_col('MINIMUM_SPACECRAFT_CLOCK_START_COUNT')
        try:
            sc_cvt = opus_support.parse_galileo_sclk(sc)
        except Exception as e:
            self._log_nonrepeating_error(f'Unable to parse Galileo SCLK "{sc}": {e}')
            return None
        return sc_cvt

    def field_obs_mission_galileo_spacecraft_clock_count2(self):
        if self._col_in_index('SPACECRAFT_CLOCK_START_COUNT'):
            # There is no SPACECRAFT_CLOCK_STOP_COUNT for Galileo
            return self.field_obs_mission_galileo_spacecraft_clock_count1()
        # This is the maximum start count, which is the best we can do
        sc = self._index_col('MAXIMUM_SPACECRAFT_CLOCK_START_COUNT') # SL9
        try:
            sc_cvt = opus_support.parse_galileo_sclk(sc)
        except Exception as e:
            self._log_nonrepeating_error(f'Unable to parse Galileo SCLK "{sc}": {e}')
            return None
        return sc_cvt


    ##############################################
    ### FIELD METHODS FOR obs_instrument_gossi ###
    ##############################################

    def field_obs_instrument_gossi_opus_id(self):
        return self.opus_id

    def field_obs_instrument_gossi_volume_id(self):
        return self.volume

    def field_obs_instrument_gossi_instrument_id(self):
        return self.instrument_id

    def field_obs_instrument_gossi_observation_id(self):
        return self._index_col('OBSERVATION_ID')

    def field_obs_instrument_gossi_image_id(self):
        if self._col_in_index('IMAGE_ID'):
            return self._index_col('IMAGE_ID')
        min_id = self._index_col('MINIMUM_IMAGE_ID')
        max_id = self._index_col('MAXIMUM_IMAGE_ID')
        # For SL9, give the range MIN-MAX as a string
        return f'{min_id}-{max_id}'

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
