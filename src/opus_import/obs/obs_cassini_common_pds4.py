################################################################################
# obs_cassini_common_pds4.py
#
# Defines the ObsCassiniCommonPDS4 class, which augments ObsCassiniCommon with
# methods that are PDS4-specific.
# Currently, none of the Cassini PDS4 migrations have been imported into OPUS
# yet (and so this PDS4 class simply inherits from the shared Cassini Common,
# using the attributes deduced from the OBSERVATION_ID).
################################################################################

from typing import cast

from opus_import.obs.field_types import FloatField, IntField, MultFieldRet, StrField
from opus_import.obs.obs_cassini_common import ObsCassiniCommon
from opus_import.obs.obs_common_pds4 import ObsCommonPDS4


class ObsCassiniCommonPDS4(ObsCommonPDS4, ObsCassiniCommon):
    ##############################################################
    ### OVERRIDE FOR obs_mission_cassini FROM ObsCassiniCommon ###
    ##############################################################

    def field_obs_mission_cassini_obs_name(self) -> StrField:
        # Strip leading/trailing whitespace from the label value
        val = self._some_index_col('cassini:observation_id')
        return cast(StrField, val)

    def field_obs_mission_cassini_spacecraft_clock_count1(self) -> FloatField:
        raw = self._index_col('cassini:spacecraft_clock_start_count')
        if raw is None:
            return None
        return self._parse_cassini_sclk(str(raw).strip())

    def field_obs_mission_cassini_spacecraft_clock_count2(self) -> FloatField:
        raw = self._index_col('cassini:spacecraft_clock_stop_count')
        if raw is None:
            return None
        sc_cvt = self._parse_cassini_sclk(str(raw).strip())
        if sc_cvt is None:
            return None
        sc1 = self.field_obs_mission_cassini_spacecraft_clock_count1()
        if sc1 is not None and sc_cvt < sc1:
            self._log_nonrepeating_warning(
                'spacecraft_clock_count1 and spacecraft_clock_count2 are in the '
                'wrong order - setting count2 to count1')
            return sc1
        return sc_cvt


    #######################################################################
    ### OVERRIDE METHODS FOR obs_instrument_coiss FROM ObsCassiniCommon ###
    #######################################################################

    def field_obs_instrument_coiss_opus_id(self) -> StrField:
        return self.opus_id

    def field_obs_instrument_coiss_bundle_id(self) -> StrField:
        return self.bundle

    def field_obs_instrument_coiss_data_conversion_type(self) -> MultFieldRet:
        return self._create_mult(self._index_col('cassini:data_conversion_type'))

    def field_obs_instrument_coiss_compression_type(self) -> MultFieldRet:
        return self._create_mult(self._index_col('cassini:inst_cmprs_type'))

    def field_obs_instrument_coiss_gain_mode_id(self) -> MultFieldRet:
        return self._create_mult(self._index_col('cassini:gain_mode_id'))

    def field_obs_instrument_coiss_image_observation_type(self) -> MultFieldRet:
        return self._create_mult(self._index_col('cassini:image_observation_type'))

    def field_obs_instrument_coiss_missing_lines(self) -> IntField:
        return cast(IntField, self._index_col('cassini:missing_lines'))

    def field_obs_instrument_coiss_shutter_mode_id(self) -> MultFieldRet:
        return self._create_mult(self._index_col('cassini:shutter_mode_id'))

    def field_obs_instrument_coiss_shutter_state_id(self) -> MultFieldRet:
        return self._create_mult(self._index_col('cassini:shutter_state_id'))

    def field_obs_instrument_coiss_image_number(self) -> IntField:
        image_number = self._index_col('cassini:image_number')
        return None if image_number is None else int(image_number)

    def field_obs_instrument_coiss_instrument_mode_id(self) -> MultFieldRet:
        return self._create_mult(self._index_col('cassini:instrument_mode_id'))

    def field_obs_instrument_coiss_target_desc(self) -> MultFieldRet:
        target_desc = self._index_col('cassini:pds3_target_desc')
        if target_desc is not None:
            target_desc = target_desc.upper()
            coiss_target_desc_mapping = self._coiss_target_desc_mapping()
            if target_desc in coiss_target_desc_mapping:
                target_desc = coiss_target_desc_mapping[target_desc]
        return self._create_mult(target_desc)

    def field_obs_instrument_coiss_combined_filter(self) -> MultFieldRet:
        camera_mult = self.field_obs_instrument_coiss_camera()
        # A GROUP column's method returns one value, and _combined_filter keys its
        # wavelength table on the camera letter rather than on the mult dictionary.
        assert isinstance(camera_mult, dict)
        camera = camera_mult['col_val']
        if not isinstance(camera, str):
            return self._create_mult_keep_case(None)

        filter1 = self._index_col('cassini:filter_name_1')
        filter2 = self._index_col('cassini:filter_name_2')
        new_filter = self._combined_filter(camera, filter1, filter2)
        return self._create_mult_keep_case(new_filter)
