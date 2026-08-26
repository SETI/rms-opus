################################################################################
# obs_volume_voyager_common.py
#
# Defines the ObsVolumeVoyagerCommon class, which encapsulates fields in the
# common and obs_mission_voyager tables.
################################################################################

from typing import cast

import opus_support
from opus_import.obs.field_types import FloatField, MultFieldRet, StrField
from opus_import.obs.obs_common_pds3 import ObsCommonPDS3


class ObsVolumeVoyagerCommon(ObsCommonPDS3):
    def _parse_voyager_sclk(self, sclk: str) -> FloatField:
        """Parse a Voyager SCLK, reporting a bad one instead of raising.

        Returns the converted SCLK, or None if it could not be parsed.
        """
        return self._parse_sclk(opus_support.parse_voyager_sclk, sclk, 'Voyager')


    #############################
    ### OVERRIDE FROM ObsBase ###
    #############################

    @property
    def mission_id(self) -> str:
        return 'VG'

    @property
    def inst_host_id(self) -> str:
        inst_host = self._some_index_col('INSTRUMENT_HOST_NAME')
        assert inst_host in ['VOYAGER 1', 'VOYAGER 2']
        return cast(str, 'VG'+inst_host[-1])

    @property
    def primary_filespec(self) -> str | None:
        # Note it's very important that this can be calculated using ONLY
        # the primary index, not the supplemental index!
        # This is because this (and the subsequent creation of opus_id) is used
        # to actually find the matching row in the supplemental index dictionary.
        # Format: "DATA/C13854XX/C1385455_CALIB.LBL"
        filespec = self._index_col('FILE_SPECIFICATION_NAME')
        assert self.bundle is not None
        return cast(str | None, self.bundle + '/' + filespec)


    ################################
    ### OVERRIDE FROM ObsGeneral ###
    ################################

    def _mission_phase_name(self) -> str | None:
        """The mission phase this observation belongs to.

        Returns:
            The phase name as this volume set spells it, or None if the volume set does
            not record one.

        Raises:
            NotImplementedError: Always; each Voyager volume set must override this,
                because the phase is recorded in a different place in each.
        """
        raise NotImplementedError

    def _planet_id(self) -> str:
        mp = self._mission_phase_name()
        assert mp is not None
        pl = mp[:3].upper()
        assert pl in ['JUP', 'SAT', 'URA', 'NEP']
        return pl

    def field_obs_general_planet_id(self) -> MultFieldRet:
        return self._create_mult(self._planet_id())


    ####################################
    ### FIELD METHODS FOR THIS TABLE ###
    ####################################

    def field_obs_mission_voyager_opus_id(self) -> StrField:
        return self.opus_id

    def field_obs_mission_voyager_bundle_id(self) -> StrField:
        return self.bundle

    def field_obs_mission_voyager_ert(self) -> FloatField:
        if not self._col_in_index('EARTH_RECEIVED_TIME'):
            return None
        ert_time = self._index_col('EARTH_RECEIVED_TIME')
        if ert_time.startswith('UNK'):
            return None
        return self._time_from_index(column='EARTH_RECEIVED_TIME')

    def field_obs_mission_voyager_spacecraft_clock_count1(self) -> FloatField:
        sc = self._some_index_or_label_col('SPACECRAFT_CLOCK_START_COUNT')
        if self._col_in_some_index_or_label('SPACECRAFT_CLOCK_PARTITION_NUMBER'):
            partition = self._some_index_or_label_col('SPACECRAFT_CLOCK_PARTITION_NUMBER')
            sc = str(partition) + '/' + sc

        return self._parse_voyager_sclk(sc)

    def field_obs_mission_voyager_spacecraft_clock_count2(self) -> FloatField:
        sc = self._some_index_or_label_col('SPACECRAFT_CLOCK_STOP_COUNT')
        if self._col_in_some_index_or_label('SPACECRAFT_CLOCK_PARTITION_NUMBER'):
            partition = self._some_index_or_label_col('SPACECRAFT_CLOCK_PARTITION_NUMBER')
            sc = str(partition) + '/' + sc
        sc_cvt = self._parse_voyager_sclk(sc)
        if sc_cvt is None:
            return None

        sc1 = self.field_obs_mission_voyager_spacecraft_clock_count1()
        if sc1 is not None and sc_cvt < sc1:
            self._log_nonrepeating_warning(
                    f'spacecraft_clock_count1 ({sc1}) and '+
                    f'spacecraft_clock_count2 ({sc_cvt}) '+
                    'are in the wrong order - setting to count1')
            sc_cvt = sc1

        return sc_cvt
