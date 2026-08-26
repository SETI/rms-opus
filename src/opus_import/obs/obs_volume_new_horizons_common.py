################################################################################
# obs_volume_new_horizons_common.py
#
# Defines the ObsVolumeNewHorizonsCommon class, which encapsulates fields in the
# common and obs_mission_new_horizons tables.
################################################################################

from typing import cast

import opus_support
from opus_import.obs.field_types import FloatField, MultFieldRet, StrField
from opus_import.obs.obs_common_pds3 import ObsCommonPDS3

_MISSION_PHASE_NAMES = {
    'JUPITER ENCOUNTER':              'Jupiter Encounter',
    'PLUTO CRUISE':                   'Pluto Cruise',
    'PLUTO ENCOUNTER':                'Pluto Encounter',
    'POST-LAUNCH CHECKOUT':           'Post-Launch Checkout',
    'CRUISE TO FIRST KBO EN':         'Cruise to First KBO Encounter',
    'CRUISE TO FIRST KBO ENCOUNTER':  'Cruise to First KBO Encounter',
    'KEM1 ENCOUNTER':                 'KEM1 Encounter',
}

class ObsVolumeNewHorizonsCommon(ObsCommonPDS3):
    def _parse_new_horizons_sclk(self, sclk: str) -> FloatField:
        """Parse a New Horizons SCLK, reporting a bad one instead of raising.

        Returns the converted SCLK, or None if it could not be parsed.
        """
        return self._parse_sclk(opus_support.parse_new_horizons_sclk, sclk,
                                'New Horizons')


    ################################
    ### OVERRIDE FROM ObsGeneral ###
    ################################

    def field_obs_general_planet_id(self) -> MultFieldRet:
        # Values are:
        #   Jupiter Encounter
        #   Pluto Cruise
        #   Pluto Encounter
        #   Post-Launch Checkout
        mp = self._supp_index_col('MISSION_PHASE_NAME').upper()
        if mp == 'JUPITER ENCOUNTER':
            return self._create_mult('JUP')
        if mp in ('PLUTO CRUISE', 'PLUTO ENCOUNTER'):
            return self._create_mult('PLU')
        if mp in ('POST-LAUNCH CHECKOUT',
                  'CRUISE TO FIRST KBO EN',
                  'CRUISE TO FIRST KBO ENCOUNTER',
                  'KEM1 ENCOUNTER'):
            return self._create_mult('OTH')

        self._log_nonrepeating_error(f'Unknown MISSION_PHASE_NAME "{mp}"')
        return self._create_mult('OTH')


    ############################
    ### OVERRIDE FROM ObsPds ###
    ############################

    def field_obs_pds_note(self) -> StrField:
        note = self._supp_index_col('OBSERVATION_DESC')
        if note == 'NULL':
            return None
        return cast(StrField, note)


    ####################################
    ### FIELD METHODS FOR THIS TABLE ###
    ####################################

    def field_obs_mission_new_horizons_opus_id(self) -> StrField:
        return self.opus_id

    def field_obs_mission_new_horizons_bundle_id(self) -> StrField:
        return self.bundle

    def field_obs_mission_new_horizons_instrument_id(self) -> StrField:
        return self.instrument_id

    def field_obs_mission_new_horizons_spacecraft_clock_count1(self) -> FloatField:
        partition = self._supp_index_col('SPACECRAFT_CLOCK_COUNT_PARTITION')
        start_time = self._supp_index_col('SPACECRAFT_CLOCK_START_COUNT')

        sc = str(partition) + '/' + start_time

        return self._parse_new_horizons_sclk(sc)

    def field_obs_mission_new_horizons_spacecraft_clock_count2(self) -> FloatField:
        partition = self._supp_index_col('SPACECRAFT_CLOCK_COUNT_PARTITION')
        stop_time = self._supp_index_col('SPACECRAFT_CLOCK_STOP_COUNT')

        sc = str(partition) + '/' + stop_time

        sc_cvt = self._parse_new_horizons_sclk(sc)
        if sc_cvt is None:
            return None

        sc1 = self.field_obs_mission_new_horizons_spacecraft_clock_count1()
        if sc1 is not None and sc_cvt < sc1:
            self._log_nonrepeating_warning(
                f'spacecraft_clock_count1 ({sc1}) and spacecraft_clock_count2 ({sc_cvt}) '
                +'are in the wrong order - setting to count1')
            sc_cvt = sc1

        return sc_cvt

    def field_obs_mission_new_horizons_mission_phase(self) -> MultFieldRet:
        mp = self._supp_index_col('MISSION_PHASE_NAME')
        good_mp = _MISSION_PHASE_NAMES[mp]
        return self._create_mult(col_val=good_mp.upper(), disp_name=good_mp)
