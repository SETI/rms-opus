"""The obs class for COUVIS_0xxx.

Cassini UVIS observations. One volume set holds four instruments -- two spectrographs, a
photometer and a hydrogen-deuterium cell -- distinguished by the file name, and only a
spectrograph with a spatially resolved window produces an image at all.
"""

import os
from typing import cast

from opus_import.obs.field_types import FloatField, IntField, MultFieldRet, StrField, as_int
from opus_import.obs.obs_cassini_common_pds3 import ObsCassiniCommonPDS3
from opus_import.obs.obs_type_image import SIXTEEN_BIT_IMAGE_LEVELS


class ObsVolumeCOUVIS0xxx(ObsCassiniCommonPDS3):
    #############################
    ### OVERRIDE FROM ObsBase ###
    #############################

    """The Cassini UVIS observations of COUVIS_0xxx.

    Its ``field_obs_*`` methods each fill the schema column their name ends in,
    declaring the type `opus_import.obs.field_types` gives that column.
    """

    @property
    def instrument_id(self) -> str | None:
        """The OPUS instrument id, ``COUVIS``."""
        return 'COUVIS'

    @property
    def primary_filespec(self) -> str | None:
        """The path of this observation's data file.

        Computed from the primary index alone, for the reason
        `opus_import.obs.obs_cassini_common.ObsCassiniCommon.primary_filespec` gives.

        Returns:
            The path, which these volumes already record relative to the volume root.
        """
        # Note it's very important that this can be calculated using ONLY
        # the primary index, not the supplemental index!
        # This is because this (and the subsequent creation of opus_id) is used
        # to actually find the matching row in the supplemental index dictionary.
        filespec = self._index_col('FILE_NAME')
        return cast(str | None, filespec.lstrip('/'))

    def convert_filespec_from_lbl(self, filespec: str) -> str:
        """Convert a ``.LBL`` file specification to the ``.DAT`` data file.

        Parameters:
            filespec: The path, relative to the holdings root.

        Returns:
            The same path with ``.LBL`` replaced by ``.DAT``, which is the file
            this bundle's observations are identified by.
        """
        return filespec.replace('.LBL', '.DAT')

    def _channel_time_helper(self) -> tuple[str, str]:
        """Split the file name into the UVIS channel and the observation's time stamp.

        Returns:
            The channel -- ``'EUV'``, ``'FUV'``, ``'HSP'`` or ``'HDAC'`` -- and the time
            stamp that follows it in the name.
        """
        file_name = self._index_col('FILE_NAME')
        last_part = os.path.basename(file_name)
        last_part = last_part.replace('.LBL', '')

        if last_part.startswith('HDAC'):
            channel = 'HDAC'
            image_time = last_part[4:]
        else:
            channel = last_part[:3]
            image_time = last_part[3:]

        return channel, image_time

    def _is_image(self) -> bool:
        """Whether this observation is a spectral image rather than a spectrum or a time series.

        Returns:
            True for a spatially resolved EUV or FUV observation. The photometers produce no
            image at all, an occultation slit produces a time series, and a single-pixel
            window produces a spectrum.
        """
        channel, _image_time = self._channel_time_helper()
        slit_state = self._index_col('SLIT_STATE')

        if channel == 'HSP' or channel == 'HDAC':
            return False
        assert channel == 'EUV' or channel == 'FUV'
        if slit_state == 'OCCULTATION':
            return False

        if not self._has_supp_index():
            self._log_nonrepeating_error(
                '_is_image has channel EUV or FUV but no DATA_OBJECT_TYPE available')
            return False

        object_type = self._supp_index_col('DATA_OBJECT_TYPE')
        return cast(bool, object_type != 'SPECTRUM')

    def _integration_duration_helper(self) -> FloatField:
        """Return the integration duration in seconds.

        Returns:
            The duration, or None if the index does not carry one. The photometer records it
            in milliseconds and every other channel in seconds, which is what this converts.
        """
        dur = self._index_col('INTEGRATION_DURATION')
        if dur is None:
            return None
        channel, _image_time = self._channel_time_helper()
        if channel == 'HSP':
            # HSP integration_duration is in milliseconds!
            return cast(FloatField, dur/1000)
        # EUV and FUV are in seconds! What were they thinking?
        return cast(FloatField, dur)


    ################################
    ### OVERRIDE FROM ObsGeneral ###
    ################################

    def _target_name(self) -> list[tuple[str | None, str | None]]:
        """The target this observation was aimed at.

        Returns:
            The intended target, as a one-element list.
        """
        return [self._cassini_intended_target_name()]

    def field_obs_general_time2(self) -> FloatField:
        channel, _image_time = self._channel_time_helper()
        start_time_sec = self.field_obs_general_time1()
        if channel != 'HSP':
            return self._time2_from_index(start_time_sec)

        # The HSP stop times are wrong by a factor of the integration duration.
        # So we use the normal start time but then compute the stop time by taking
        # the start time and adding the number of samples * integration duration.
        samples = self._supp_index_col('LINE_SAMPLES')
        integration_duration = self._integration_duration_helper()

        if samples is None or integration_duration is None:
            return None

        return cast(FloatField, start_time_sec + samples*integration_duration)

    # We occasionally don't bother to generate ring_geo data for COUVIS, like during
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
        ra = self._ring_geo_index_col('MINIMUM_DECLINATION')
        if ra is not None:
            return ra
        return cast(FloatField, self._index_col('DECLINATION'))

    def field_obs_general_declination2(self) -> FloatField:
        ra = self._ring_geo_index_col('MAXIMUM_DECLINATION')
        if ra is not None:
            return ra
        return cast(FloatField, self._index_col('DECLINATION'))

    def field_obs_general_ring_obs_id(self) -> StrField:
        filename = self._index_col('FILE_NAME').split('/')[-1]
        if filename.startswith('HDAC'):
            image_camera = filename[:4]
            image_time = filename[4:18]
        else:
            image_camera = filename[:3]
            image_time = filename[3:17]
        image_time_str = (image_time[:4] + '-' + image_time[5:8] + 'T' +
                          image_time[9:11] + '-' + image_time[12:14])
        planet = self._cassini_planet_id()
        if planet == 'OTH':
            pl_str = ''
        else:
            pl_str = planet[0]

        return f'{pl_str}_CO_UVIS_{image_time_str}_{image_camera}'

    def field_obs_general_planet_id(self) -> MultFieldRet:
        return self._create_mult(self._cassini_planet_id())

    def field_obs_general_quantity(self) -> MultFieldRet:
        if not self._has_supp_index():
            return self._create_mult(None)
        description = self._supp_index_col('DESCRIPTION').upper()
        if (description.find('OCCULTATION') != -1 and
            description.find('CALIBRATION') == -1):
            return self._create_mult('OPDEPTH')
        return self._create_mult('EMISSION')

    def field_obs_general_observation_type(self) -> MultFieldRet:
        channel, _image_time = self._channel_time_helper()
        if channel == 'HSP' or channel == 'HDAC':
            return self._create_mult('TS') # Time Series
        assert channel == 'EUV' or channel == 'FUV'
        return self._create_mult('SCU') # Spectral Cube


    ############################
    ### OVERRIDE FROM ObsPds ###
    ############################

    def field_obs_pds_note(self) -> StrField:
        if not self._has_supp_index():
            return None
        description = self._supp_index_col('DESCRIPTION')
        description = description.replace('The purpose of this observation is ', '')
        return cast(StrField, description)


    ##################################
    ### OVERRIDE FROM ObsTypeImage ###
    ##################################

    def field_obs_type_image_image_type_id(self) -> MultFieldRet:
        if self._is_image():
            return self._create_mult('PUSH')
        return self._create_mult(None)

    def field_obs_type_image_duration(self) -> FloatField:
        if not self._is_image():
            return None
        return self._integration_duration_helper()

    def field_obs_type_image_levels(self) -> IntField:
        if not self._is_image():
            return None
        return SIXTEEN_BIT_IMAGE_LEVELS

    def _pixel_size_helper(self) -> tuple[IntField, IntField]:
        """Return the two dimensions of the imaging window, in pixels.

        Returns:
            The smaller and the larger dimension, or ``(None, None)`` where the observation
            is not an image, carries no supplemental index row, or is missing one of the
            window columns. A dimension that comes out negative is returned as None rather
            than as a nonsense count.
        """
        if not self._is_image():
            return None, None

        if not self._has_supp_index():
            return None, None
        line1 = self._supp_index_col('WINDOW_MINIMUM_LINE_NUMBER')
        line2 = self._supp_index_col('WINDOW_MAXIMUM_LINE_NUMBER')
        line_bin = self._supp_index_col('LINE_BINNING_FACTOR')
        samples = self._supp_index_col('LINE_SAMPLES')
        if line1 is None or line2 is None or line_bin is None or samples is None:
            return None, None
        min_val = min(samples, (line2-line1+1)//line_bin)
        max_val = max(samples, (line2-line1+1)//line_bin)
        min_ret: IntField = None if min_val < 0 else min_val
        max_ret: IntField = None if max_val < 0 else max_val

        return min_ret, max_ret

    def field_obs_type_image_greater_pixel_size(self) -> IntField:
        return self._pixel_size_helper()[1]

    def field_obs_type_image_lesser_pixel_size(self) -> IntField:
        return self._pixel_size_helper()[0]


    ###################################
    ### OVERRIDE FROM ObsWavelength ###
    ###################################

    def field_obs_wavelength_wavelength1(self) -> FloatField:
        channel, _image_time = self._channel_time_helper()
        if channel == 'HSP':
            return 0.11
        if channel == 'HDAC':
            return 0.115

        if not self._has_supp_index():
            return None
        band1 = self._supp_index_col('MINIMUM_BAND_NUMBER')
        if band1 is None:
            return None

        if channel == 'EUV':
            return cast(FloatField, 0.0558 + band1 * 0.0000607422)
        if channel == 'FUV':
            return cast(FloatField, 0.11 + band1 * 0.000078125)

        self._log_nonrepeating_error(f'wavelength1 has unknown channel type {channel}')
        return None

    def field_obs_wavelength_wavelength2(self) -> FloatField:
        channel, _image_time = self._channel_time_helper()
        if channel == 'HSP':
            return 0.19
        if channel == 'HDAC':
            return 0.180

        if not self._has_supp_index():
            return None
        band2 = self._supp_index_col('MAXIMUM_BAND_NUMBER')
        if band2 is None:
            return None

        if channel == 'EUV':
            return cast(FloatField, 0.0558 + (band2+1) * 0.0000607422)
        if channel == 'FUV':
            return cast(FloatField, 0.11 + (band2+1) * 0.000078125)

        self._log_nonrepeating_error(f'wavelength2 has unknown channel type {channel}')
        return None

    def field_obs_wavelength_wave_res1(self) -> FloatField:
        if not self._has_supp_index():
            return None
        channel, _image_time = self._channel_time_helper()
        band_bin = self._supp_index_col('BAND_BINNING_FACTOR')

        if channel == 'EUV':
            return cast(FloatField, band_bin * 0.0000607422)
        if channel == 'FUV':
            return cast(FloatField, band_bin * 0.000078125)

        wl1 = self.field_obs_wavelength_wavelength1()
        wl2 = self.field_obs_wavelength_wavelength2()
        if wl1 is None or wl2 is None:
            return None
        return wl2 - wl1

    def field_obs_wavelength_wave_res2(self) -> FloatField:
        return self.field_obs_wavelength_wave_res1()

    def field_obs_wavelength_wave_no_res1(self) -> FloatField:
        channel, _image_time = self._channel_time_helper()
        if channel == 'HSP' or channel == 'HDAC':
            return self._wave_no_res_from_full_bandwidth()
        return self._wave_no_res1_from_wave_res()

    def field_obs_wavelength_wave_no_res2(self) -> FloatField:
        channel, _image_time = self._channel_time_helper()
        if channel == 'HSP' or channel == 'HDAC':
            return self._wave_no_res_from_full_bandwidth()
        return self._wave_no_res2_from_wave_res()

    def field_obs_wavelength_spec_flag(self) -> MultFieldRet:
        spec_size = self.field_obs_wavelength_spec_size()
        if spec_size is None or spec_size < 1:
            return self._create_mult('N')
        return self._create_mult('Y')

    def field_obs_wavelength_spec_size(self) -> IntField:
        channel, _image_time = self._channel_time_helper()

        if channel == 'HSP' or channel == 'HDAC':
            return None

        if not self._has_supp_index():
            return None
        band1 = self._supp_index_col('MINIMUM_BAND_NUMBER')
        band2 = self._supp_index_col('MAXIMUM_BAND_NUMBER')
        band_bin = self._supp_index_col('BAND_BINNING_FACTOR')
        if band1 is None or band2 is None or band_bin is None:
            return None

        return as_int((band2 - band1 + 1) // band_bin)


    ##########################################
    ### OVERRIDE FROM ObsCassiniCommonPDS3 ###
    ##########################################

    def field_obs_mission_cassini_spacecraft_clock_count1(self) -> FloatField:
        sc = self._index_col('SPACECRAFT_CLOCK_START_COUNT')
        sc = self._fix_cassini_sclk(sc)
        if sc is None or not sc.startswith('1/'):
            self._log_nonrepeating_error(
                f'Badly formatted SPACECRAFT_CLOCK_START_COUNT "{sc}"')
            return None
        return self._parse_cassini_sclk(sc)

    # There is no SPACECRAFT_CLOCK_STOP_COUNT for COUVIS so we have to compute it.
    # This works because Cassini SCLK is in units of seconds.
    def field_obs_mission_cassini_spacecraft_clock_count2(self) -> FloatField:
        sc_cvt = self.field_obs_mission_cassini_spacecraft_clock_count1()
        time1 = self.field_obs_general_time1()
        time2 = self.field_obs_general_time2()
        assert sc_cvt is not None
        assert time1 is not None
        assert time2 is not None
        return sc_cvt + time2-time1

    def field_obs_mission_cassini_mission_phase_name(self) -> MultFieldRet:
        return self._create_mult(self._cassini_normalize_mission_phase_name())


    ###############################################
    ### FIELD METHODS FOR obs_instrument_couvis ###
    ###############################################

    def field_obs_instrument_couvis_opus_id(self) -> StrField:
        return self.opus_id

    def field_obs_instrument_couvis_bundle_id(self) -> StrField:
        return self.bundle

    def field_obs_instrument_couvis_observation_type(self) -> MultFieldRet:
        obstype = self._index_col('OBSERVATION_TYPE')
        if obstype == '' or obstype == 'NULL':
            obstype = 'NONE'
        return self._create_mult(obstype.upper())

    def field_obs_instrument_couvis_integration_duration(self) -> FloatField:
        return self._integration_duration_helper()

    def field_obs_instrument_couvis_compression_type(self) -> MultFieldRet:
        return self._create_mult(self._index_col('COMPRESSION_TYPE'))

    def field_obs_instrument_couvis_occultation_port_state(self) -> MultFieldRet:
        occ_state = self._index_col('OCCULTATION_PORT_STATE')
        if occ_state == 'NULL':
            occ_state = 'N/A'
        return self._create_mult(occ_state.upper())

    def field_obs_instrument_couvis_slit_state(self) -> MultFieldRet:
        return self._create_mult(self._index_col('SLIT_STATE'))

    def field_obs_instrument_couvis_test_pulse_state(self) -> MultFieldRet:
        return self._create_mult(self._index_col('TEST_PULSE_STATE'))

    def field_obs_instrument_couvis_dwell_time(self) -> MultFieldRet:
        return self._create_mult(self._index_col('DWELL_TIME'))

    def field_obs_instrument_couvis_channel(self) -> MultFieldRet:
        channel, _image_time = self._channel_time_helper()
        return self._create_mult_keep_case(channel)

    def field_obs_instrument_couvis_band1(self) -> IntField:
        return as_int(self._supp_index_col('MINIMUM_BAND_NUMBER'))

    def field_obs_instrument_couvis_band2(self) -> IntField:
        return as_int(self._supp_index_col('MAXIMUM_BAND_NUMBER'))

    def field_obs_instrument_couvis_band_bin(self) -> IntField:
        return as_int(self._supp_index_col('BAND_BINNING_FACTOR'))

    def field_obs_instrument_couvis_line1(self) -> IntField:
        return as_int(self._supp_index_col('WINDOW_MINIMUM_LINE_NUMBER'))

    def field_obs_instrument_couvis_line2(self) -> IntField:
        return as_int(self._supp_index_col('WINDOW_MAXIMUM_LINE_NUMBER'))

    def field_obs_instrument_couvis_line_bin(self) -> IntField:
        return as_int(self._supp_index_col('LINE_BINNING_FACTOR'))

    def field_obs_instrument_couvis_samples(self) -> IntField:
        return as_int(self._supp_index_col('LINE_SAMPLES'))
