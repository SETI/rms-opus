"""The ``obs_general`` columns: what every observation has: its ids, its target, its
times,
and its sky position.

One module per OPUS table, mixed into every obs class that fills the table. A column
whose value depends on the PDS version or on the instrument is left to a subclass, which
is why most of the methods here can be overridden and a few raise `NotImplementedError`
outright.
"""

from opus_import.obs.field_types import FloatField, MultField, MultFieldRet, StrField
from opus_import.obs.obs_base import ObsBase


class ObsGeneral(ObsBase):
    """The ``obs_general`` columns, which every observation has.

    Its ``field_obs_*`` methods each fill the schema column their name ends in,
    declaring the type `opus_import.obs.field_types` gives that column.
    """

    ####################################
    ### FIELD METHODS FOR THIS TABLE ###
    ####################################

    ### Don't override these ###

    def field_obs_general_opus_id(self) -> StrField:
        return self.opus_id

    def field_obs_general_bundle_id(self) -> StrField:
        return self.bundle

    def field_obs_general_instrument_id(self) -> MultFieldRet:
        return self._create_mult(self.instrument_id)

    def field_obs_general_inst_host_id(self) -> MultFieldRet:
        return self._create_mult(self.inst_host_id)

    def field_obs_general_mission_id(self) -> MultFieldRet:
        return self._create_mult(self.mission_id)

    def field_obs_general_target_class(self) -> list[MultField]:
        # target_class supports multiple target names
        target_names = self._target_name()
        ret_list = []
        used_classes = set()
        for target_name, _ in target_names:
            if target_name is None:
                ret_list.append(self._create_mult(None))
            else:
                target_name, target_info = self._get_target_info(target_name)
                if target_info is None:
                    ret_list.append(self._create_mult(None))
                else:
                    if target_info[1] not in used_classes:
                        ret_list.append(self._create_mult(target_info[1]))
                        used_classes.add(target_info[1])
        return ret_list

    ################################
    ### ! Might override these ! ###
    ################################

    def _target_name(self) -> list[tuple[str | None, str | None]]:
        """Return every target this observation is of.

        Returns:
            One ``(name, shown name)`` pair per target, which is what lets an observation
            carry several. Most instruments return exactly one.

        Raises:
            NotImplementedError: Always; a PDS-version or instrument class must override
                this, since no two of them record the target the same way.
        """
        raise NotImplementedError

    def field_obs_general_target_name(self) -> list[MultField]:
        ret = []
        for target_name, target_disp_name in self._target_name():
            if target_name is None:
                ret.append(self._create_mult(None))
            else:
                group_info = self._get_planet_group_info(target_name)
                ret.append(
                    self._create_mult(
                        col_val=target_name,
                        disp_name=target_disp_name,
                        grouping=group_info['label'],
                        group_pin=group_info['disp_order'],
                    )
                )
        return ret

    def field_obs_general_time1(self) -> FloatField:
        return self._time_from_some_index()

    def field_obs_general_time2(self) -> FloatField:
        return self._time2_from_some_index(self.field_obs_general_time1())

    def field_obs_general_observation_duration(self) -> FloatField:
        # This is the default behavior, but will be overridden for some
        # instruments
        time1 = self.field_obs_general_time1()
        time2 = self.field_obs_general_time2()
        assert time1 is not None
        assert time2 is not None
        return max(time2 - time1, 0)

    def field_obs_general_right_asc1(self) -> FloatField:
        return None

    def field_obs_general_right_asc2(self) -> FloatField:
        return None

    def field_obs_general_declination1(self) -> FloatField:
        return None

    def field_obs_general_declination2(self) -> FloatField:
        return None

    ###################################
    ### !!! Must override these !!! ###
    ###################################

    def field_obs_general_planet_id(self) -> MultFieldRet:
        raise NotImplementedError

    def field_obs_general_quantity(self) -> MultFieldRet:
        raise NotImplementedError

    def field_obs_general_observation_type(self) -> MultFieldRet:
        raise NotImplementedError
