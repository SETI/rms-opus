"""The shared spacecraft-clock helpers on the mission common classes.

Twenty-three ``field_obs_mission_<mission>_spacecraft_clock_count*`` methods used to
carry their own copy of the same try/except: parse, and on any exception log
``Unable to parse <Mission> SCLK "<sclk>": <exc>`` and return None. They now call a
``_parse_<mission>_sclk`` helper on their mission common class, which routes through
`ObsBase._parse_sclk`.

These tests pin what the field functions depend on: the converted value, the exact
message text (it is user-visible in the import log and no golden fixture captures it),
and that the two COCIRS_56xxx sites can still report at warning level.
"""

from typing import Any

import pytest

import opus_support
from opus_import.obs.obs_cassini_common import ObsCassiniCommon
from opus_import.obs.obs_volume_galileo_common import ObsVolumeGalileoCommon
from opus_import.obs.obs_volume_new_horizons_common import ObsVolumeNewHorizonsCommon
from opus_import.obs.obs_volume_voyager_common import ObsVolumeVoyagerCommon

from .conftest import make_context

#: (mission common class, helper name, opus_support parser, display name, a valid SCLK)
MISSIONS = [
    (ObsCassiniCommon, '_parse_cassini_sclk', opus_support.parse_cassini_sclk,
     'Cassini', '1/1294561143.125'),
    (ObsVolumeVoyagerCommon, '_parse_voyager_sclk', opus_support.parse_voyager_sclk,
     'Voyager', '3/20997.32'),
    (ObsVolumeGalileoCommon, '_parse_galileo_sclk', opus_support.parse_galileo_sclk,
     'Galileo', '03464059.00'),
    (ObsVolumeNewHorizonsCommon, '_parse_new_horizons_sclk',
     opus_support.parse_new_horizons_sclk, 'New Horizons', '1/0034948318:00000'),
]

MISSION_IDS = [mission[3] for mission in MISSIONS]

#: No mission's parser accepts this, so every helper takes its failure path.
BAD_SCLK = 'not a spacecraft clock'


def _recording_obs(cls: type, monkeypatch: pytest.MonkeyPatch) -> tuple[Any, list[str]]:
    """Build an obs object whose error and warning logging is captured, not emitted."""
    obs = cls(make_context())
    logged: list[str] = []
    monkeypatch.setattr(obs, '_log_nonrepeating_error',
                        lambda msg: logged.append(f'error: {msg}'))
    monkeypatch.setattr(obs, '_log_nonrepeating_warning',
                        lambda msg: logged.append(f'warning: {msg}'))
    return obs, logged


@pytest.mark.parametrize(('cls', 'helper_name', 'parse_func', 'mission', 'good_sclk'),
                         MISSIONS, ids=MISSION_IDS)
def test_a_good_sclk_converts_exactly_as_the_parser_does(
        cls: type, helper_name: str, parse_func: Any, mission: str, good_sclk: str,
        monkeypatch: pytest.MonkeyPatch) -> None:
    """The helper adds error handling and nothing else to the opus_support parser."""
    obs, logged = _recording_obs(cls, monkeypatch)

    assert getattr(obs, helper_name)(good_sclk) == parse_func(good_sclk)
    assert logged == []


@pytest.mark.parametrize(('cls', 'helper_name', 'parse_func', 'mission', 'good_sclk'),
                         MISSIONS, ids=MISSION_IDS)
def test_a_bad_sclk_is_reported_and_returns_none(
        cls: type, helper_name: str, parse_func: Any, mission: str, good_sclk: str,
        monkeypatch: pytest.MonkeyPatch) -> None:
    """A bad SCLK is one nonrepeating error naming the mission, the value and the cause.

    The wrapper's whole format string is asserted, because it is the text the import log
    shows an operator and it is what the 23 hand-written copies produced before this
    helper existed. The reason for the failure is taken from the parser rather than
    hard-coded, since that half is opus_support's message, not this helper's.
    """
    obs, logged = _recording_obs(cls, monkeypatch)

    with pytest.raises(Exception) as excinfo:
        parse_func(BAD_SCLK)
    reason = str(excinfo.value)
    assert reason, 'the parser rejected the input with an empty message'
    expected = f'Unable to parse {mission} SCLK "{BAD_SCLK}": {reason}'

    assert getattr(obs, helper_name)(BAD_SCLK) is None
    assert logged == [f'error: {expected}']


def test_the_cassini_message_is_exactly_this_text(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """One literal spelling of the message, so the format string cannot drift silently."""
    obs, logged = _recording_obs(ObsCassiniCommon, monkeypatch)

    assert obs._parse_cassini_sclk('1/zzz') is None

    assert logged == ['error: Unable to parse Cassini SCLK "1/zzz": '
                      'Cassini clock fields must be integers: zzz']


def test_cassini_can_report_a_bad_sclk_as_a_warning(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """COCIRS_56xxx reports at warning level; the helper's log_func is how it still can."""
    obs, logged = _recording_obs(ObsCassiniCommon, monkeypatch)

    assert obs._parse_cassini_sclk(BAD_SCLK, obs._log_nonrepeating_warning) is None

    assert len(logged) == 1
    assert logged[0].startswith(f'warning: Unable to parse Cassini SCLK "{BAD_SCLK}": ')


def test_the_default_log_level_is_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Passing no log_func reports at error level, as 21 of the 23 sites do."""
    obs, logged = _recording_obs(ObsCassiniCommon, monkeypatch)

    assert obs._parse_cassini_sclk(BAD_SCLK) is None

    assert len(logged) == 1
    assert logged[0].startswith('error: ')
