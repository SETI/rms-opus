"""The obs class for COISS_1xxx and COISS_2xxx.

Cassini ISS images of Jupiter and of Saturn.
"""

from typing import cast

from opus_import.obs.field_types import FloatField, IntField, MultFieldRet, StrField
from opus_import.obs.obs_cassini_common_pds3 import ObsCassiniCommonPDS3
from opus_import.obs.obs_type_image import TWELVE_BIT_IMAGE_LEVELS

# The ISS CCDs are 1024x1024, and the on-chip summation modes read them out at half
# and quarter resolution in each direction. Images are always square, so this is both
# the greater and the lesser pixel size.
_INSTRUMENT_MODE_PIXEL_SIZE = {
    'FULL': 1024,
    'SUM2': 512,
    'SUM4': 256,
}


class ObsVolumeCOISS12xxx(ObsCassiniCommonPDS3):
    """The Cassini ISS images of COISS_1xxx and COISS_2xxx.

    Its ``field_obs_*`` methods each fill the schema column their name ends in,
    declaring the type `opus_import.obs.field_types` gives that column.
    """

    #############################
    ### OVERRIDE FROM ObsBase ###
    #############################


    @property
    def instrument_id(self) -> str | None:
        """The OPUS instrument id, ``COISS``."""
        return 'COISS'

    def convert_filespec_from_lbl(self, filespec: str) -> str:
        """Convert a ``.LBL`` file specification to the ``.IMG`` data file.

        Parameters:
            filespec: The path, relative to the holdings root.

        Returns:
            The same path with ``.LBL`` replaced by ``.IMG``, which is the file
            this bundle's observations are identified by.
        """
        return filespec.replace('.LBL', '.IMG')


    ################################
    ### OVERRIDE FROM ObsGeneral ###
    ################################

    def field_obs_general_observation_duration(self) -> FloatField:
        return cast(FloatField, self._index_col('EXPOSURE_DURATION') / 1000)

    # We occasionally don't bother to generate ring_geo data for COISS, like during
    # cruise, so just use the given RA/DEC from the index if needed. We don't make
    # any effort to figure out the min/max values.
    def field_obs_general_right_asc1(self) -> FloatField:
        ra = self._ring_geo_index_col('MINIMUM_RIGHT_ASCENSION')
        if ra is not None:
            return ra
        return cast(FloatField, self._index_col('RIGHT_ASCENSION'))

    def field_obs_general_right_asc2(self) -> FloatField:
        ra = self._ring_geo_index_col('MAXIMUM_RIGHT_ASCENSION')
        if ra is not None:
            return ra
        return cast(FloatField, self._index_col('RIGHT_ASCENSION'))

    def field_obs_general_declination1(self) -> FloatField:
        dec = self._ring_geo_index_col('MINIMUM_DECLINATION')
        if dec is not None:
            return dec
        return cast(FloatField, self._index_col('DECLINATION'))

    def field_obs_general_declination2(self) -> FloatField:
        dec = self._ring_geo_index_col('MAXIMUM_DECLINATION')
        if dec is not None:
            return dec
        return cast(FloatField, self._index_col('DECLINATION'))

    def field_obs_general_ring_obs_id(self) -> StrField:
        camera = self._index_col('INSTRUMENT_ID')[3]
        assert camera in ('N', 'W')
        filename = self._index_col('FILE_NAME')
        image_num = filename[1:11]
        planet = self._cassini_planet_id()
        if planet is None:
            pl_str = ''
        else:
            pl_str = planet[0]
        return f'{pl_str}_IMG_CO_ISS_{image_num}_{camera}'

    def field_obs_general_planet_id(self) -> MultFieldRet:
        return self._create_mult(self._cassini_planet_id())

    def _target_name(self) -> list[tuple[str | None, str | None]]:
        """The target this observation was aimed at.

        Returns:
            The intended target, as a one-element list.
        """
        return [self._cassini_intended_target_name()]

    def field_obs_general_quantity(self) -> MultFieldRet:
        filter1, filter2 = self._index_col('FILTER_NAME')
        if filter1.startswith('UV') or filter2.startswith('UV'):
            return self._create_mult('EMISSION')
        return self._create_mult('REFLECT')

    def field_obs_general_observation_type(self) -> MultFieldRet:
        return self._create_mult('IMG') # Image


    ############################
    ### OVERRIDE FROM ObsPds ###
    ############################

    def field_obs_pds_note(self) -> StrField:
        return cast(StrField, self._index_col('DESCRIPTION'))


    ##################################
    ### OVERRIDE FROM ObsTypeImage ###
    ##################################

    def field_obs_type_image_image_type_id(self) -> MultFieldRet:
        return self._create_mult('FRAM')

    def field_obs_type_image_duration(self) -> FloatField:
        return self.field_obs_general_observation_duration()

    def field_obs_type_image_levels(self) -> IntField:
        return TWELVE_BIT_IMAGE_LEVELS

    def field_obs_type_image_greater_pixel_size(self) -> IntField:
        # For COISS, this is both greater and lesser pixel size
        inst_mode = self._index_col('INSTRUMENT_MODE_ID')
        if inst_mode not in _INSTRUMENT_MODE_PIXEL_SIZE:
            self._log_nonrepeating_error(f'Unknown INSTRUMENT_MODE_ID "{inst_mode}"')
            return None
        return _INSTRUMENT_MODE_PIXEL_SIZE[inst_mode]

    def field_obs_type_image_lesser_pixel_size(self) -> IntField:
        return self.field_obs_type_image_greater_pixel_size()


    ###################################
    ### OVERRIDE FROM ObsWavelength ###
    ###################################

    def field_obs_wavelength_wavelength1(self) -> FloatField:
        camera = self._index_col('INSTRUMENT_ID')[3]
        filter1, filter2 = self._index_col('FILTER_NAME')
        central_wl, fwhm, _effective_wl = self._coiss_wavelength_helper(camera, filter1, filter2)
        if central_wl is None or fwhm is None:
            return None
        return (central_wl - fwhm/2) / 1000 # microns

    def field_obs_wavelength_wavelength2(self) -> FloatField:
        camera = self._index_col('INSTRUMENT_ID')[3]
        filter1, filter2 = self._index_col('FILTER_NAME')
        central_wl, fwhm, _effective_wl = self._coiss_wavelength_helper(camera, filter1, filter2)
        if central_wl is None or fwhm is None:
            return None
        return (central_wl + fwhm/2) / 1000 # microns

    def field_obs_wavelength_wave_res1(self) -> FloatField:
        return self._wave_res_from_full_bandwidth()

    def field_obs_wavelength_wave_res2(self) -> FloatField:
        return self.field_obs_wavelength_wave_res1()

    def field_obs_wavelength_wave_no_res1(self) -> FloatField:
        return self._wave_no_res_from_full_bandwidth()

    def field_obs_wavelength_wave_no_res2(self) -> FloatField:
        return self.field_obs_wavelength_wave_no_res1()

    def field_obs_wavelength_polarization_type(self) -> MultFieldRet:
        the_filter = self._combined_filter()
        if the_filter.find('P') != -1:
            return self._create_mult('LINEAR')
        return self._create_mult('NONE')


    ##########################################
    ### OVERRIDE FROM ObsCassiniCommonPDS3 ###
    ##########################################

    def field_obs_mission_cassini_spacecraft_clock_count1(self) -> FloatField:
        partition = self._index_col('SPACECRAFT_CLOCK_CNT_PARTITION')
        count = self._index_col('SPACECRAFT_CLOCK_START_COUNT')
        sc = self._fix_cassini_sclk(str(partition) + '/' + str(count))
        assert sc is not None  # _fix_cassini_sclk returns None only for a None argument
        return self._parse_cassini_sclk(sc)

    def field_obs_mission_cassini_spacecraft_clock_count2(self) -> FloatField:
        partition = self._index_col('SPACECRAFT_CLOCK_CNT_PARTITION')
        count = self._index_col('SPACECRAFT_CLOCK_STOP_COUNT')
        sc = self._fix_cassini_sclk(str(partition) + '/' + str(count))
        assert sc is not None  # _fix_cassini_sclk returns None only for a None argument
        sc_cvt = self._parse_cassini_sclk(sc)
        if sc_cvt is None:
            return None

        sc1 = self.field_obs_mission_cassini_spacecraft_clock_count1()
        if sc1 is not None and sc_cvt < sc1:
            self._log_nonrepeating_warning(
                f'spacecraft_clock_count1 ({sc1}) and spacecraft_clock_count2 '+
                f'({sc_cvt}) are in the wrong order - setting to count1')
            sc_cvt = sc1
        else:
            image_number = self._index_col('IMAGE_NUMBER')
            sc2_int = int(sc_cvt)
            if int(image_number) != sc2_int:
                self._log_nonrepeating_warning(
                     f'spacecraft_clock_count2 ({sc_cvt}) and COISS IMAGE_NUMBER '+
                     f'({image_number}) don\'t match')

        return sc_cvt

    def field_obs_mission_cassini_ert1(self) -> FloatField:
        return self._time_from_index(column='EARTH_RECEIVED_START_TIME')

    def field_obs_mission_cassini_ert2(self) -> FloatField:
        return self._time2_from_index(self.field_obs_mission_cassini_ert1(),
                                      column='EARTH_RECEIVED_STOP_TIME')

    def field_obs_mission_cassini_mission_phase_name(self) -> MultFieldRet:
        mp = self._cassini_normalize_mission_phase_name()
        return self._create_mult(mp)

    def field_obs_mission_cassini_sequence_id(self) -> StrField:
        return cast(StrField, self._index_col('SEQUENCE_ID'))
