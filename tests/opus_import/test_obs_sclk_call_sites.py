"""The three spacecraft-clock call sites that are not the canonical shape.

Twenty of the 23 ``field_obs_mission_<mission>_spacecraft_clock_count*`` methods were
identical modulo the mission name, and `test_obs_sclk` covers the helper they all now
call. Three were not, and each had to be reshaped by hand when the try/except moved into
the helper:

* COVIMS_8xxx count2 computed ``parse_cassini_sclk(sc)+1`` *inside* the try, so the
  ``+1`` had to move after the helper's None check;
* the two PDS4 sites parse ``str(raw).strip()`` but named the unstripped ``raw`` in the
  error message;
* both COCIRS count2 methods reported a badly formatted
  ``SPACECRAFT_CLOCK_START_COUNT`` while reading ``SPACECRAFT_CLOCK_STOP_COUNT``.

The consolidation was verified by a differential probe against the pre-change tree, but
a probe is ephemeral. These tests drive the real field functions so the three reshaped
sites stay pinned.
"""

from typing import Any

import pytest

import opus_support
from opus_import.obs.obs_base import ObsBase
from opus_import.obs.obs_bundle_cassini_iss_fring_mosaics_rsfrench2025 import (
    ObsBundleCassiniISSFRingMosaicsRSFrench2025,
)
from opus_import.obs.obs_volume_cocirs_01xxx import ObsVolumeCOCIRS01xxx
from opus_import.obs.obs_volume_cocirs_56xxx import ObsVolumeCOCIRS56xxx
from opus_import.obs.obs_volume_covims_8xxx import ObsVolumeCOVIMS8xxx

GOOD_SCLK = '1/1294561143.125'
BAD_SCLK = '1/zzz'


def _obs(cls: type, columns: dict[str, Any]) -> tuple[Any, list[str]]:
    """Build an obs object of `cls` whose column reads come from `columns`.

    Returns the object and the list its logging is captured into.
    """
    obs = cls.__new__(cls)
    ObsBase.__init__(obs)
    logged: list[str] = []

    def column(col: str, idx: Any = None) -> Any:
        return columns.get(col)

    obs._index_col = column
    obs._supp_index_col = column
    obs._some_index_or_label_col = column
    obs._col_in_index = lambda col: True
    obs._col_in_some_index_or_label = lambda col: False
    obs._log_nonrepeating_error = lambda msg: logged.append(f'error: {msg}')
    obs._log_nonrepeating_warning = lambda msg: logged.append(f'warning: {msg}')
    return obs, logged


# --- COVIMS_8xxx: the `+1` that moved out of the try -------------------------

def _covims_8xxx(start: str, stop: str) -> tuple[Any, list[str]]:
    return _obs(ObsVolumeCOVIMS8xxx, {'SPACECRAFT_CLOCK_START_COUNT': start,
                                      'SPACECRAFT_CLOCK_STOP_COUNT': stop})


def test_covims_8xxx_count2_still_rounds_up() -> None:
    """count2 is one second past the parsed stop count, as it was inside the try."""
    obs, logged = _covims_8xxx(GOOD_SCLK, '1/1294561200.000')

    assert obs.field_obs_mission_cassini_spacecraft_clock_count2() == (
        opus_support.parse_cassini_sclk('1/1294561200.000') + 1)
    assert logged == []


def test_covims_8xxx_count2_does_not_round_up_a_failed_parse() -> None:
    """An unparseable stop count returns None; the +1 must not run on it."""
    obs, logged = _covims_8xxx(GOOD_SCLK, BAD_SCLK)

    assert obs.field_obs_mission_cassini_spacecraft_clock_count2() is None
    assert len(logged) == 1
    # COVIMS_8xxx rewrites the fractional field only when there already is one, so
    # this reaches the parser unchanged.
    assert logged[0].startswith('error: Unable to parse Cassini SCLK "1/zzz"')


def test_covims_8xxx_count2_falls_back_to_count1_when_out_of_order() -> None:
    """The ordering check still sees the rounded-up value, not the raw parse."""
    obs, _logged = _covims_8xxx('1/1294561200.000', '1/1294561100.000')

    assert obs.field_obs_mission_cassini_spacecraft_clock_count2() == (
        obs.field_obs_mission_cassini_spacecraft_clock_count1())


# --- PDS4: the message names the string that was actually parsed -------------

def _fring_mosaics(start: Any, stop: Any) -> tuple[Any, list[str]]:
    return _obs(ObsBundleCassiniISSFRingMosaicsRSFrench2025,
                {'cassini:spacecraft_clock_start_count': start,
                 'cassini:spacecraft_clock_stop_count': stop})


def test_pds4_sclk_is_parsed_with_surrounding_whitespace_stripped() -> None:
    """A padded column value parses, exactly as it did before the consolidation."""
    obs, logged = _fring_mosaics(f'  {GOOD_SCLK}  ', f'  {GOOD_SCLK}  ')

    assert obs.field_obs_mission_cassini_spacecraft_clock_count1() == (
        opus_support.parse_cassini_sclk(GOOD_SCLK))
    assert logged == []


def test_pds4_bad_sclk_message_names_the_stripped_value() -> None:
    """The message quotes what was parsed, not the padded column value.

    This is the single deliberate message change of the SCLK consolidation: the site
    used to interpolate the raw column value while parsing ``str(raw).strip()``.
    """
    obs, logged = _fring_mosaics(f'  {BAD_SCLK}  ', None)

    assert obs.field_obs_mission_cassini_spacecraft_clock_count1() is None
    assert len(logged) == 1
    assert f'SCLK "{BAD_SCLK}"' in logged[0]


def test_pds4_missing_sclk_column_is_none_without_logging() -> None:
    """An absent column is not an error; it returns None before any parse."""
    obs, logged = _fring_mosaics(None, None)

    assert obs.field_obs_mission_cassini_spacecraft_clock_count1() is None
    assert logged == []


# --- COCIRS: the count2 guard names the column it actually read --------------

@pytest.mark.parametrize('cls', [ObsVolumeCOCIRS01xxx, ObsVolumeCOCIRS56xxx],
                         ids=['COCIRS_01xxx', 'COCIRS_56xxx'])
def test_cocirs_count2_guard_names_the_stop_count(cls: type) -> None:
    """A badly formatted stop count is reported as STOP, not START.

    Both count2 methods read SPACECRAFT_CLOCK_STOP_COUNT and reported
    SPACECRAFT_CLOCK_START_COUNT, which sent an operator to the wrong column.
    """
    obs, logged = _obs(cls, {'SPACECRAFT_CLOCK_START_COUNT': GOOD_SCLK,
                             'SPACECRAFT_CLOCK_STOP_COUNT': 'nonsense'})

    assert obs.field_obs_mission_cassini_spacecraft_clock_count2() is None
    assert len(logged) == 1
    # _fix_cassini_sclk supplies the missing fractional field before the guard runs.
    assert 'Badly formatted SPACECRAFT_CLOCK_STOP_COUNT "nonsense.000"' in logged[0]


@pytest.mark.parametrize('cls', [ObsVolumeCOCIRS01xxx, ObsVolumeCOCIRS56xxx],
                         ids=['COCIRS_01xxx', 'COCIRS_56xxx'])
def test_cocirs_count1_guard_still_names_the_start_count(cls: type) -> None:
    """The count1 guard was already right and must stay that way."""
    obs, logged = _obs(cls, {'SPACECRAFT_CLOCK_START_COUNT': 'nonsense'})

    assert obs.field_obs_mission_cassini_spacecraft_clock_count1() is None
    assert len(logged) == 1
    assert 'Badly formatted SPACECRAFT_CLOCK_START_COUNT "nonsense.000"' in logged[0]


def test_cocirs_56xxx_reports_an_unparseable_sclk_as_a_warning() -> None:
    """COCIRS_56xxx is the one file that logs a bad SCLK below error level."""
    obs, logged = _obs(ObsVolumeCOCIRS56xxx,
                       {'SPACECRAFT_CLOCK_START_COUNT': BAD_SCLK})

    assert obs.field_obs_mission_cassini_spacecraft_clock_count1() is None
    assert len(logged) == 1
    assert logged[0].startswith('warning: Unable to parse Cassini SCLK "1/zzz.000"')


def test_cocirs_01xxx_reports_an_unparseable_sclk_as_an_error() -> None:
    """Its sibling volume logs the same failure at error level."""
    obs, logged = _obs(ObsVolumeCOCIRS01xxx,
                       {'SPACECRAFT_CLOCK_START_COUNT': BAD_SCLK})

    assert obs.field_obs_mission_cassini_spacecraft_clock_count1() is None
    assert len(logged) == 1
    assert logged[0].startswith('error: Unable to parse Cassini SCLK "1/zzz.000"')
