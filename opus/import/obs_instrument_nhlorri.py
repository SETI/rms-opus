################################################################################
# obs_instrument_nhlorri.py
#
# Defines the ObsInstrumentNHLORRI class, which encapsulates fields in the
# obs_instrument_nhlorri table.
################################################################################

import numpy as np

import opus_support

from obs_mission_new_horizons import ObsMissionNewHorizons


class ObsInstrumentNHLORRI(ObsMissionNewHorizons):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    #############################
    ### OVERRIDE FROM ObsBase ###
    #############################

    @property
    def instrument_id(self):
        return 'NHLORRI'

    @property
    def inst_host_id(self):
        return 'NH'

    @property
    def mission_id(self):
        return 'NH'

    @property
    def primary_filespec(self):
        # Note it's very important that this can be calculated using ONLY
        # the primary index, not the supplemental index!
        # This is because this (and the subsequent creation of opus_id) is used
        # to actually find the matching row in the supplemental index dictionary.
        # Format: "data/20070108_003059/lor_0030598439_0x630_eng.lbl"
        filespec = self._index_col('PATH_NAME') + self._index_col('FILE_NAME')
        return self.volume + '/' + filespec

    def _convert_filespec_from_lbl(self, filespec):
        filespec = filespec.replace('.lbl', '.fit')
        filespec = filespec.replace('.LBL', '.FIT')
        filespec = filespec.replace('_sci', '_eng')
        filespec = filespec.replace('_2001', '_1001')
        return filespec


    ################################
    ### OVERRIDE FROM ObsGeneral ###
    ################################

    def field_obs_general_observation_duration(self):
        return self._supp_index_col('EXPOSURE_DURATION')

    # We occasionally don't bother to generate ring_geo data for NHLORRI, like during
    # cruise, so just use the given RA/DEC from the label if needed. We don't make
    # any effort to figure out the min/max values.
    def field_obs_general_right_asc1(self):
        ra = self._ring_geo_index_col('MINIMUM_RIGHT_ASCENSION')
        if ra is not None:
            return ra
        return self._supp_index_col('RIGHT_ASCENSION')

    def field_obs_general_right_asc2(self):
        ra = self._ring_geo_index_col('MAXIMUM_RIGHT_ASCENSION')
        if ra is not None:
            return ra
        return self._supp_index_col('RIGHT_ASCENSION')

    def field_obs_general_declination1(self):
        dec = self._ring_geo_index_col('MINIMUM_DECLINATION')
        if dec is not None:
            return dec
        return self._supp_index_col('DECLINATION')

    def field_obs_general_declination2(self):
        dec = self._ring_geo_index_col('MAXIMUM_DECLINATION')
        if dec is not None:
            return dec
        return self._supp_index_col('DECLINATION')

    def field_obs_general_ring_obs_id(self):
        image_num = self._index_col('FILE_NAME')[4:14]
        start_time = self._index_col('START_TIME')
        # This is really dumb, but it's what the old OPUS did so we do it for
        # backwards compatability
        if start_time > '2007-09-01':
            pl_str = 'P'
        else:
            pl_str = 'J'
        return f'{pl_str}_IMG_NH_LORRI_{image_num}'

    def field_obs_general_quantity(self):
        return 'REFLECT'

    def field_obs_general_observation_type(self):
        return 'IMG'


    ##################################
    ### OVERRIDE FROM ObsTypeImage ###
    ##################################

    def field_obs_type_image_image_type_id(self):
        return 'FRAM'

    def field_obs_type_image_duration(self):
        return self.field_obs_general_observation_duration()

    def field_obs_type_image_levels(self):
        return 4096

    def field_obs_type_image_greater_pixel_size(self):
        return 1024

    def field_obs_type_image_lesser_pixel_size(self):
        return 1024


    ###################################
    ### OVERRIDE FROM ObsWavelength ###
    ###################################

    def field_obs_wavelength_wavelength1(self):
        return 0.35

    def field_obs_wavelength_wavelength2(self):
        return 0.85

    def field_obs_wavelength_wave_res1(self):
        return 0.5

    def field_obs_wavelength_wave_res2(self):
        return 0.5

    def field_obs_wavelength_wave_no_res1(self):
        wno1 = self.field_obs_wavelength_wave_no1()
        wno2 = self.field_obs_wavelength_wave_no2()
        if wno1 is None or wno2 is None:
            return None
        return wno2 - wno1

    def field_obs_wavelength_wave_no_res2(self):
        return self.field_obs_wavelength_wave_no_res1()


    ####################################
    ### FIELD METHODS FOR THIS TABLE ###
    ####################################

    def field_obs_instrument_nhlorri_opus_id(self):
        return self.opus_id

    def field_obs_instrument_nhlorri_volume_id(self):
        return self.volume

    def field_obs_instrument_nhlorri_instrument_id(self):
        return self.instrument_id

    def field_obs_instrument_nhlorri_instrument_compression_type(self):
        return self._supp_index_col('INSTRUMENT_COMPRESSION_TYPE')

    def field_obs_instrument_nhlorri_binning_mode(self):
        return self._supp_index_col('BINNING_MODE')
