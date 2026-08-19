################################################################################
# obs_cassini_common_pds4.py
#
# Defines the ObsCassiniCommonPDS4 class, which augments ObsCassiniCommon with
# methods that are PDS4-specific.
# Currently, none of the Cassini PDS4 migrations have been imported into OPUS
# yet (and so this PDS4 class simply inherits from the shared Cassini Common,
# using the attributes deduced from the OBSERVATION_ID).
################################################################################

from obs_cassini_common import ObsCassiniCommon
from obs_common_pds4 import ObsCommonPDS4

import opus_support


class ObsCassiniCommonPDS4(ObsCommonPDS4, ObsCassiniCommon):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    ##############################################################
    ### OVERRIDE FOR obs_mission_cassini FROM ObsCassiniCommon ###
    ##############################################################

    def field_obs_mission_cassini_obs_name(self):
        # Strip leading/trailing whitespace from the label value
        val = self._some_index_col('cassini:observation_id')
        return val

    def field_obs_mission_cassini_spacecraft_clock_count1(self):
        raw = self._index_col('cassini:spacecraft_clock_start_count')
        if raw is None:
            return None
        try:
            return opus_support.parse_cassini_sclk(str(raw).strip())
        except Exception as e:
            self._log_nonrepeating_error(
                f'Unable to parse Cassini SCLK "{raw}": {e}')
            return None

    def field_obs_mission_cassini_spacecraft_clock_count2(self):
        raw = self._index_col('cassini:spacecraft_clock_stop_count')
        if raw is None:
            return None
        try:
            sc_cvt = opus_support.parse_cassini_sclk(str(raw).strip())
        except Exception as e:
            self._log_nonrepeating_error(
                f'Unable to parse Cassini SCLK "{raw}": {e}')
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

    def field_obs_instrument_coiss_opus_id(self):
        return self.opus_id

    def field_obs_instrument_coiss_bundle_id(self):
        return self.bundle

    def field_obs_instrument_coiss_instrument_id(self):
        return self.instrument_id

    def field_obs_instrument_coiss_data_conversion_type(self):
        return self._create_mult(self._index_col('cassini:data_conversion_type'))

    def field_obs_instrument_coiss_compression_type(self):
        return self._create_mult(self._index_col('cassini:inst_cmprs_type'))

    def field_obs_instrument_coiss_gain_mode_id(self):
        return self._create_mult(self._index_col('cassini:gain_mode_id'))

    def field_obs_instrument_coiss_image_observation_type(self):
        return self._create_mult(self._index_col('cassini:image_observation_type'))

    def field_obs_instrument_coiss_missing_lines(self):
        return self._index_col('cassini:missing_lines')

    def field_obs_instrument_coiss_shutter_mode_id(self):
        return self._create_mult(self._index_col('cassini:shutter_mode_id'))

    def field_obs_instrument_coiss_shutter_state_id(self):
        return self._create_mult(self._index_col('cassini:shutter_state_id'))

    def field_obs_instrument_coiss_image_number(self):
        return self._index_col('cassini:image_number')

    def field_obs_instrument_coiss_instrument_mode_id(self):
        return self._create_mult(self._index_col('cassini:instrument_mode_id'))

    def field_obs_instrument_coiss_target_desc(self):
        target_desc = self._index_col('cassini:pds3_target_desc')
        if target_desc is not None:
            target_desc = target_desc.upper()
            coiss_target_desc_mapping = self._coiss_target_desc_mapping()
            if target_desc in coiss_target_desc_mapping:
                target_desc = coiss_target_desc_mapping[target_desc]
        return self._create_mult(target_desc)

    def field_obs_instrument_coiss_combined_filter(self):
        camera = self.field_obs_instrument_coiss_camera()
        if camera is None:
            return self._create_mult_keep_case(None)

        filter1 = self._index_col('cassini:filter_name_1')
        filter2 = self._index_col('cassini:filter_name_2')
        new_filter = self._combined_filter(camera, filter1, filter2)
        return self._create_mult_keep_case(new_filter)
