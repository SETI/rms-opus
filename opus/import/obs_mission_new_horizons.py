################################################################################
# obs_mission_new_horizons.py
#
# Defines the ObsMissionNewHorizons class, which encapsulates fields in the
# common and obs_mission_new_horizons tables.
################################################################################

import opus_support

from obs_common import ObsCommon


_MISSION_PHASE_NAMES = {
    'JUPITER ENCOUNTER':              'Jupiter Encounter',
    'PLUTO CRUISE':                   'Pluto Cruise',
    'PLUTO ENCOUNTER':                'Pluto Encounter',
    'POST-LAUNCH CHECKOUT':           'Post-Launch Checkout',
    'CRUISE TO FIRST KBO EN':         'Cruise to First KBO Encounter',
    'CRUISE TO FIRST KBO ENCOUNTER':  'Cruise to First KBO Encounter',
    'KEM1 ENCOUNTER':                 'KEM1 Encounter',
}

class ObsMissionNewHorizons(ObsCommon):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    ################################
    ### OVERRIDE FROM ObsGeneral ###
    ################################

    def field_obs_general_planet_id(self):
        # Values are:
        #   Jupiter Encounter
        #   Pluto Cruise
        #   Pluto Encounter
        #   Post-Launch Checkout
        mp = self._supp_index_col('MISSION_PHASE_NAME').upper()
        if mp == 'JUPITER ENCOUNTER':
            return 'JUP'
        if mp in ('PLUTO CRUISE', 'PLUTO ENCOUNTER'):
            return 'PLU'
        if mp in ('POST-LAUNCH CHECKOUT',
                  'CRUISE TO FIRST KBO EN',
                  'CRUISE TO FIRST KBO ENCOUNTER',
                  'KEM1 ENCOUNTER'):
            return 'OTH'

        self._log_nonrepeating_error(f'Unknown MISSION_PHASE_NAME "{mp}"')
        return 'OTH'


    ############################
    ### OVERRIDE FROM ObsPds ###
    ############################

    def field_obs_pds_note(self):
        note = self._supp_index_col('OBSERVATION_DESC')
        if note == 'NULL':
            return None
        return note


    ####################################
    ### FIELD METHODS FOR THIS TABLE ###
    ####################################

    def field_obs_mission_new_horizons_opus_id(self):
        return self.opus_id

    def field_obs_mission_new_horizons_volume_id(self):
        return self.volume

    def field_obs_mission_new_horizons_instrument_id(self):
        return self.instrument_id

    def field_obs_mission_new_horizons_spacecraft_clock_count1(self):
        partition = self._supp_index_col('SPACECRAFT_CLOCK_COUNT_PARTITION')
        start_time = self._supp_index_col('SPACECRAFT_CLOCK_START_COUNT')

        sc = str(partition) + '/' + start_time

        try:
            sc_cvt = opus_support.parse_new_horizons_sclk(sc)
        except Exception as e:
            self._log_nonrepeating_error(
                f'Unable to parse New Horizons SCLK "{sc}": {e}')
            return None

        return sc_cvt

    def field_obs_mission_new_horizons_spacecraft_clock_count2(self):
        partition = self._supp_index_col('SPACECRAFT_CLOCK_COUNT_PARTITION')
        stop_time = self._supp_index_col('SPACECRAFT_CLOCK_STOP_COUNT')

        sc = str(partition) + '/' + stop_time

        try:
            sc_cvt = opus_support.parse_new_horizons_sclk(sc)
        except Exception as e:
            self._log_nonrepeating_error(
                f'Unable to parse New Horizons SCLK "{sc}": {e}')
            return None

        sc1 = self.field_obs_mission_new_horizons_spacecraft_clock_count1()
        if sc1 is not None and sc_cvt < sc1:
            self._log_nonrepeating_warning(
                f'spacecraft_clock_count1 ({sc1}) and spacecraft_clock_count2 ({sc_cvt}) '
                +'are in the wrong order - setting to count1')
            sc_cvt = sc1

        return sc_cvt

    def field_obs_mission_new_horizons_mission_phase(self):
        mp = self._supp_index_col('MISSION_PHASE_NAME')
        good_mp = _MISSION_PHASE_NAMES[mp]
        return good_mp.upper(), good_mp
