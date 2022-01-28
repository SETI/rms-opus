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


    ################################
    ### OVERRIDE FROM ObsGeneral ###
    ################################

    @property
    def inst_host_id(self):
        return 'NH'

    @property
    def field_obs_general_ring_obs_id(self):
        image_num = self._index_col('FILE_NAME')[4:14]
        start_time = self._index_col('START_TIME')
        # This is really dumb, but it's what the old OPUS did so we do it for
        # backwards compatability
        if start_time > '2007-09-01':
            pl_str = 'P'
        else:
            pl_str = 'J'
        return pl_str + '_IMG_NH_LORRI_' + image_num


    @property
    def field_obs_general_target_name(self):
        target_name = self._supp_index_col('TARGET_NAME')
        target_info = self._get_target_info(target_name)
        if target_info is None:
            return None
        return target_name, target_info[2]

    # We actually have no idea what IMAGE_TIME represents - start, mid, stop?
    # We assume it means stop time like it does for Voyager, and because Mark
    # has done some ring analysis with this assumption and it seemed to work OK.
    # So we compute start time by taking IMAGE_TIME and subtracting exposure.
    # If we don't have exposure, we just set them equal so we can still search
    # cleanly.
    @property
    def field_obs_general_time1(self):
        return self._time1_from_index()

    @property
    def field_obs_general_time2(self):
        return self._time2_from_index(self.field_obs_general_time1)

    @property
    def field_obs_general_observation_duration(self):
        return self._supp_index_col('EXPOSURE_DURATION')

    @property
    def field_obs_general_quantity(self):
        return 'REFLECT'

    # We occasionally don't bother to generate ring_geo data for NHLORRI, like during
    # cruise, so just use the given RA/DEC from the label if needed. We don't make
    # any effort to figure out the min/max values.
    @property
    def field_obs_general_right_asc1(self):
        ra = self._ring_geo_index_col('MINIMUM_RIGHT_ASCENSION')
        if ra is not None:
            return ra
        return self._supp_index_col('RIGHT_ASCENSION')

    @property
    def field_obs_general_right_asc2(self):
        ra = self._ring_geo_index_col('MAXIMUM_RIGHT_ASCENSION')
        if ra is not None:
            return ra
        return self._supp_index_col('RIGHT_ASCENSION')

    @property
    def field_obs_general_declination1(self):
        dec = self._ring_geo_index_col('MINIMUM_DECLINATION')
        if dec is not None:
            return dec
        return self._supp_index_col('DECLINATION')

    @property
    def field_obs_general_declination2(self):
        dec = self._ring_geo_index_col('MAXIMUM_DECLINATION')
        if dec is not None:
            return dec
        return self._supp_index_col('DECLINATION')

    @property
    def field_obs_general_observation_type(self):
        return 'IMG'


    ############################
    ### OVERRIDE FROM ObsPds ###
    ############################

    @property
    def primary_filespec(self):
        # Format: "data/20070108_003059/lor_0030598439_0x630_eng.lbl"
        filespec = self._index_col('PATH_NAME') + self._index_col('FILE_NAME')
        return self.volume + '/' + filespec



    ##################################
    ### OVERRIDE FROM ObsTypeImage ###
    ##################################

    @property
    def field_obs_type_image_image_type_id(self):
        return 'FRAM'

    @property
    def field_obs_type_image_duration(self):
        return self.field_obs_general_observation_duration

    @property
    def field_obs_type_image_levels(self):
        return 4096

    @property
    def field_obs_type_image_greater_pixel_size(self):
        return 1024

    @property
    def field_obs_type_image_lesser_pixel_size(self):
        return 1024


    ###################################
    ### OVERRIDE FROM ObsWavelength ###
    ###################################

    @property
    def field_obs_wavelength_wavelength1(self):
        return 0.35

    @property
    def field_obs_wavelength_wavelength2(self):
        return 0.85

    @property
    def field_obs_wavelength_wave_res1(self):
        return 0.5

    @property
    def field_obs_wavelength_wave_res2(self):
        return 0.5

    @property
    def field_obs_wavelength_wave_no1(self):
        return 10000 / self.field_obs_wavelength_wavelength2 # cm^-1

    @property
    def field_obs_wavelength_wave_no2(self):
        return 10000 / self.field_obs_wavelength_wavelength1 # cm^-1

    @property
    def field_obs_wavelength_wave_no_res1(self):
        wno1 = self.field_obs_wavelength_wave_no1
        wno2 = self.field_obs_wavelength_wave_no2
        if wno1 is None or wno2 is None:
            return None
        return wno2 - wno1

    @property
    def field_obs_wavelength_wave_no_res2(self):
        return self.field_obs_wavelength_wave_no_res1

    @property
    def field_obs_wavelength_spec_flag(self):
        return 'N'

    @property
    def field_obs_wavelength_spec_size(self):
        return None

    @property
    def field_obs_wavelength_polarization_type(self):
        return 'NONE'


    ####################################
    ### FIELD METHODS FOR THIS TABLE ###
    ####################################

    @property
    def field_obs_instrument_nhlorri_opus_id(self):
        return self.opus_id

    @property
    def field_obs_instrument_nhlorri_volume_id(self):
        return self.volume

    @property
    def field_obs_instrument_nhlorri_instrument_id(self):
        return self.instrument_id

    @property
    def field_obs_instrument_nhlorri_instrument_compression_type(self):
        return self._supp_index_col('INSTRUMENT_COMPRESSION_TYPE')

    @property
    def field_obs_instrument_nhlorri_binning_mode(self):
        return self._supp_index_col('BINNING_MODE')
