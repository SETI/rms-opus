################################################################################
# obs_volume_nhxxmv_xxxx.py
#
# Defines the ObsVolumeNHxxMVXxxx class, which encapsulates fields in the
# common, obs_mission_new_horizons, and obs_instrument_nhmvic tables for
# NHxxMV_xxxx.
################################################################################

from typing import cast

from opus_import.obs.field_types import FloatField, IntField, MultFieldRet, StrField
from opus_import.obs.obs_type_image import TWELVE_BIT_IMAGE_LEVELS
from opus_import.obs.obs_volume_new_horizons_common import ObsVolumeNewHorizonsCommon


class ObsVolumeNHxxMVXxxx(ObsVolumeNewHorizonsCommon):
    #############################
    ### OVERRIDE FROM ObsBase ###
    #############################

    @property
    def instrument_id(self) -> str | None:
        return 'NHMVIC'

    @property
    def inst_host_id(self) -> str:
        return 'NH'

    @property
    def mission_id(self) -> str:
        return 'NH'

    @property
    def primary_filespec(self) -> str | None:
        # Note it's very important that this can be calculated using ONLY
        # the primary index, not the supplemental index!
        # This is because this (and the subsequent creation of opus_id) is used
        # to actually find the matching row in the supplemental index dictionary.
        # Format: "data/20070108_003059/lor_0030598439_0x630_eng.lbl"
        filespec = self._index_col('FILE_SPECIFICATION_NAME')
        assert self.bundle is not None
        return cast(str | None, self.bundle + '/' + filespec)

    def convert_filespec_from_lbl(self, filespec: str) -> str:
        filespec = filespec.replace('.lbl', '.fit')
        filespec = filespec.replace('.LBL', '.FIT')
        filespec = filespec.replace('_sci', '_eng')
        filespec = filespec.replace('_2001', '_1001')
        return filespec


    ################################
    ### OVERRIDE FROM ObsGeneral ###
    ################################

    def field_obs_general_observation_duration(self) -> FloatField:
        return cast(FloatField, self._supp_index_col('EXPOSURE_DURATION'))

    # We occasionally don't bother to generate ring_geo data for NHMVIC, like during
    # cruise, so just use the given RA/DEC from the label if needed. We don't make
    # any effort to figure out the min/max values.
    def field_obs_general_right_asc1(self) -> FloatField:
        ra = self._ring_geo_index_col('MINIMUM_RIGHT_ASCENSION')
        if ra is not None:
            return ra
        return cast(FloatField, self._supp_index_col('RIGHT_ASCENSION'))

    def field_obs_general_right_asc2(self) -> FloatField:
        ra = self._ring_geo_index_col('MAXIMUM_RIGHT_ASCENSION')
        if ra is not None:
            return ra
        return cast(FloatField, self._supp_index_col('RIGHT_ASCENSION'))

    def field_obs_general_declination1(self) -> FloatField:
        dec = self._ring_geo_index_col('MINIMUM_DECLINATION')
        if dec is not None:
            return dec
        return cast(FloatField, self._supp_index_col('DECLINATION'))

    def field_obs_general_declination2(self) -> FloatField:
        dec = self._ring_geo_index_col('MAXIMUM_DECLINATION')
        if dec is not None:
            return dec
        return cast(FloatField, self._supp_index_col('DECLINATION'))

    def field_obs_general_ring_obs_id(self) -> StrField:
        filename = self._index_col('FILE_SPECIFICATION_NAME').split('/')[-1]
        image_num = filename[4:14]
        camera = filename[:3].upper()
        start_time = self._index_col('START_TIME')
        # This is really dumb, but it's what the old OPUS did so we do it for
        # backwards compatability
        if start_time > '2007-09-01':
            pl_str = 'P'
        else:
            pl_str = 'J'
        return f'{pl_str}_IMG_NH_MVIC_{image_num}_{camera}'

    def field_obs_general_quantity(self) -> MultFieldRet:
        return self._create_mult('REFLECT')

    def field_obs_general_observation_type(self) -> MultFieldRet:
        return self._create_mult('IMG')


    ##################################
    ### OVERRIDE FROM ObsTypeImage ###
    ##################################

    def field_obs_type_image_image_type_id(self) -> MultFieldRet:
        return self._create_mult('PUSH')

    def field_obs_type_image_duration(self) -> FloatField:
        return self.field_obs_general_observation_duration()

    def field_obs_type_image_levels(self) -> IntField:
        return TWELVE_BIT_IMAGE_LEVELS

    def field_obs_type_image_greater_pixel_size(self) -> IntField:
        return 5024

    def field_obs_type_image_lesser_pixel_size(self) -> IntField:
        return 128


    ###################################
    ### OVERRIDE FROM ObsWavelength ###
    ###################################

    def field_obs_wavelength_wavelength1(self) -> FloatField:
        return 0.4

    def field_obs_wavelength_wavelength2(self) -> FloatField:
        return 0.975

    def field_obs_wavelength_wave_res1(self) -> FloatField:
        return 0.575

    def field_obs_wavelength_wave_res2(self) -> FloatField:
        return 0.575

    def field_obs_wavelength_wave_no_res1(self) -> FloatField:
        wno1 = self.field_obs_wavelength_wave_no1()
        wno2 = self.field_obs_wavelength_wave_no2()
        if wno1 is None or wno2 is None:
            return None
        return wno2 - wno1

    def field_obs_wavelength_wave_no_res2(self) -> FloatField:
        return self.field_obs_wavelength_wave_no_res1()


    ###############################################
    ### FIELD METHODS FOR obs_instrument_nhmvic ###
    ###############################################

    def field_obs_instrument_nhmvic_opus_id(self) -> StrField:
        return self.opus_id

    def field_obs_instrument_nhmvic_bundle_id(self) -> StrField:
        return self.bundle

    def field_obs_instrument_nhmvic_instrument_compression_type(self) -> MultFieldRet:
        compression_type = self._supp_index_col('INSTRUMENT_COMPRESSION_TYPE')
        return self._create_mult(compression_type)
