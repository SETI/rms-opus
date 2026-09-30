"""What every Cassini instrument's PDS3 volumes share.

Two things the PDS4 bundles do not need: reconciling ``TARGET_NAME`` with the target
description, which is what a sky or calibration pointing records the real target in, and
correcting a spacecraft clock count into the form the parser accepts, which the
instruments spell differently from one another.
"""

from typing import cast

from opus_import import config_targets
from opus_import.obs.field_types import IntField, MultFieldRet, StrField, as_int
from opus_import.obs.obs_cassini_common import ObsCassiniCommon
from opus_import.obs.obs_common_pds3 import ObsCommonPDS3


class ObsCassiniCommonPDS3(ObsCommonPDS3, ObsCassiniCommon):
    """What every Cassini instrument's PDS3 volumes share.

    Its ``field_obs_*`` methods each fill the schema column their name ends in,
    declaring the type `opus_import.obs.field_types` gives that column.
    """

    ################################################################################
    # HELPER FUNCTIONS USED BY CASSINI INSTRUMENTS
    ################################################################################
    def _cassini_intended_target_name(self) -> tuple[str | None, str | None]:
        """Return the target this observation was aimed at, correcting the label where
        needed.

        ``TARGET_NAME`` records what the spacecraft was pointed at, which is not always
        what
        the observation is of: a sky or calibration pointing carries a target description
        that names the real one, and several volumes spell a target in a way this pipeline
        maps.

        Returns:
            The corrected target name and the name shown for it, or ``(None, None)`` if
            the
            name is one this pipeline does not describe. Under ``--import-ignore-errors``
            the name becomes the string ``'None'`` so that the observation still imports.
        """
        target_name = self._index_col('TARGET_NAME').upper()
        # Note this mapping takes care of the "ATLAS:" case from COUVIS_0053
        if target_name in config_targets.TARGET_NAME_MAPPING:
            target_name = config_targets.TARGET_NAME_MAPPING[target_name]

        target_desc = None
        assert self._metadata is not None
        if 'TARGET_DESC' in self._metadata['index_row']:
            # Only for COISS
            target_desc = self._index_col('TARGET_DESC').upper()
            coiss_target_desc_mapping = self._coiss_target_desc_mapping()
            if target_desc in coiss_target_desc_mapping:
                target_desc = coiss_target_desc_mapping[target_desc]
            if target_desc in config_targets.TARGET_NAME_MAPPING:
                target_desc = config_targets.TARGET_NAME_MAPPING[target_desc]

        target_code = None
        obs_name = self._some_index_col('OBSERVATION_ID')
        if self._cassini_valid_obs_name(obs_name):
            obs_parts = obs_name.split('_')
            target_code = obs_parts[1][-2:]

        # 1: TARGET_NAME of SATURN or SKY and TARGET_CODE is one of the rings
        if (target_name == 'SATURN' or target_name == 'SKY') and target_code in (
            'RA',
            'RB',
            'RC',
            'RD',
            'RE',
            'RF',
            'RG',
            'RI',
        ):
            return ('S RINGS', 'Saturn Rings')

        # 2: TARGET_NAME of SATURN or SKY and TARGET_DESC contains "RING"
        # (leave TARGET_CODE of "Star" alone)
        if (
            (target_name == 'SATURN' or target_name == 'SKY')
            and target_desc is not None
            and target_desc.find('RING') != -1
            and target_code != 'ST'
        ):
            return ('S RINGS', 'Saturn Rings')

        # 3: TARGET_NAME of SKY and TARGET_CODE of Skeleton, let TARGET_DESC
        # override TARGET_NAME
        if (
            target_name == 'SKY'
            and target_code == 'SK'
            and target_desc is not None
            and target_desc in config_targets.TARGET_NAME_INFO
        ):
            target_name_info = config_targets.TARGET_NAME_INFO[target_desc]
            return target_desc, target_name_info[2]

        if target_name not in config_targets.TARGET_NAME_INFO:
            self._log_unknown_target_name(target_name)
            if self._ignore_errors:
                return 'None', None
            return None, None
        target_info = config_targets.TARGET_NAME_INFO[target_name]
        return target_name, target_info[2]

    def _fix_cassini_sclk(self, count: str | None) -> str | None:
        """Correct a Cassini spacecraft clock count into the form the parser accepts.

        The instruments do not agree on how they write one: CIRS omits the fractional
        part,
        VIMS writes a partition where there is none, and some volumes pad differently.

        Parameters:
            count: The count as the label spells it.

        Returns:
            The corrected count, or None if there was none to correct.
        """
        if count is None:
            return None

        ### CIRS
        if count.find('.') == -1:
            count += '.000'

        ### VIMS
        # See rms-opus issue #444
        if count.endswith('.971'):
            count = count.replace('.971', '.000')
        if count.endswith('.973'):
            count = count.replace('.973', '.000')

        ### UVIS
        # See rms-opus issue #443
        if count.endswith('.324'):
            count = count.replace('.324', '.000')

        return count

    ##############################################################
    ### OVERRIDE FOR obs_mission_cassini FROM ObsCassiniCommon ###
    ##############################################################
    def field_obs_mission_cassini_obs_name(self) -> StrField:
        return cast(StrField, self._some_index_col('OBSERVATION_ID'))

    #######################################################################
    ### OVERRIDE METHODS FOR obs_instrument_coiss FROM ObsCassiniCommon ###
    #######################################################################

    def field_obs_instrument_coiss_opus_id(self) -> StrField:
        return self.opus_id

    def field_obs_instrument_coiss_bundle_id(self) -> StrField:
        return self.bundle

    def field_obs_instrument_coiss_data_conversion_type(self) -> MultFieldRet:
        return self._create_mult(self._index_col('DATA_CONVERSION_TYPE'))

    def field_obs_instrument_coiss_compression_type(self) -> MultFieldRet:
        return self._create_mult(self._index_col('INST_CMPRS_TYPE'))

    def field_obs_instrument_coiss_gain_mode_id(self) -> MultFieldRet:
        return self._create_mult(self._index_col('GAIN_MODE_ID'))

    def field_obs_instrument_coiss_image_observation_type(self) -> MultFieldRet:
        obs_type = self._index_col('IMAGE_OBSERVATION_TYPE')

        # Sometimes they have both SCIENCE,OPNAV and OPNAV,SCIENCE so normalize
        # the order
        ret_list = []
        if obs_type.find('SCIENCE') != -1:
            ret_list.append('SCIENCE')
        if obs_type.find('OPNAV') != -1:
            ret_list.append('OPNAV')
        if obs_type.find('CALIBRATION') != -1:
            ret_list.append('CALIBRATION')
        if obs_type.find('ENGINEERING') != -1:
            ret_list.append('ENGINEERING')
        if obs_type.find('SUPPORT') != -1:
            ret_list.append('SUPPORT')
        if obs_type.find('UNK') != -1:
            ret_list.append('UNKNOWN')

        ret = '/'.join(ret_list)

        # If the result isn't the same length as what we started with, we must've
        # encountered a new type we didn't know about
        if len(ret) != len(obs_type.replace('UNK', 'UNKNOWN')):
            self._log_nonrepeating_error(
                f'Unknown format for COISS image_observation_type: "{obs_type}"'
            )
            return self._create_mult(None)

        return self._create_mult(ret)

    def field_obs_instrument_coiss_missing_lines(self) -> IntField:
        return as_int(self._index_col('MISSING_LINES'))

    def field_obs_instrument_coiss_shutter_mode_id(self) -> MultFieldRet:
        return self._create_mult(self._index_col('SHUTTER_MODE_ID'))

    def field_obs_instrument_coiss_shutter_state_id(self) -> MultFieldRet:
        return self._create_mult(self._index_col('SHUTTER_STATE_ID'))

    def field_obs_instrument_coiss_image_number(self) -> IntField:
        # The index declares this CHARACTER, and the column is int4: the digits are the
        # seconds part of the spacecraft clock.
        image_number = self._index_col('IMAGE_NUMBER')
        return None if image_number is None else int(image_number)

    def field_obs_instrument_coiss_instrument_mode_id(self) -> MultFieldRet:
        return self._create_mult(self._index_col('INSTRUMENT_MODE_ID'))

    def field_obs_instrument_coiss_target_desc(self) -> MultFieldRet:
        target_desc = self._index_col('TARGET_DESC').upper()
        coiss_target_desc_mapping = self._coiss_target_desc_mapping()
        if target_desc in coiss_target_desc_mapping:
            target_desc = coiss_target_desc_mapping[target_desc]
        return self._create_mult(target_desc)

    def field_obs_instrument_coiss_combined_filter(self) -> MultFieldRet:
        new_filter = self._combined_filter()
        return self._create_mult_keep_case(new_filter)

    def field_obs_instrument_coiss_camera(self) -> MultFieldRet:
        camera = self._index_col('INSTRUMENT_ID')[3]
        assert camera in ('N', 'W')
        return self._create_mult(camera)
