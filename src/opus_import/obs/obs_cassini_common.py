"""What every Cassini instrument shares: the observation name, and what is derived from
it.

A Cassini observation name encodes the prime instrument, the orbit number, the target
code and the activity, none of which is a column of its own, so most of this module is
about parsing it and reporting one that cannot be parsed. The mission phase is derived
from the observation's time rather than read from the label, because the labels do not
agree on how a phase is spelled.
"""

import re
from collections.abc import Callable
from typing import TYPE_CHECKING, TypeGuard, cast

import opus_support
from opus_import.import_util import cached_tai_from_iso
from opus_import.obs.field_types import FloatField, IntField, MultFieldRet, StrField
from opus_import.obs.obs_base import ObsBase

# TODO: This is probably PDS3-only, move it to the PDS3 specific class in the future.
# These codes show up as the last two characters of the second part of an observation name.
_CASSINI_TARGET_CODE_MAPPING = {
    'AG': 'AG (Aegaeon)',
    'AN': 'AN (Anthe)',
    'AT': 'AT (Atlas)',
    'CA': 'CA (Callisto)',
    'CO': 'CO (Co-rotation)',
    'CP': 'CP (Calypso)',
    'DA': 'DA (Daphnis)',
    'DI': 'DI (Dione)',
    'DN': 'DN (Downstream of the wake)',
    'DR': 'DR (Dust RAM direction)',
    'EA': 'EA (Earth)',
    'EN': 'EN (Enceladus)',
    'EP': 'EP (Epimetheus)',
    'EU': 'EU (Europa)',
    'FO': 'FO (Fomalhaut)',
    'FT': 'FT (Flux tube)',
    'GA': 'GA (Ganymede)',
    'HE': 'HE (Helene)',
    'HI': 'HI (Himalia)',
    'HY': 'HY (Hyperion)',
    'IA': 'IA (Iapetus)',
    'IC': 'IC (Instrument calibration)',
    'IO': 'IO (Io)',
    'JA': 'JA (Janus)',
    'JU': 'JU (Jupiter)',
    'ME': 'ME (Methone)',
    'MI': 'MI (Mimas)',
    'NA': 'Not Applicable',
    'OT': 'OT (Other)',
    'PA': 'PA (Pandora)',
    'PH': 'PH (Phoebe)',
    'PL': 'PL (Pallene)',
    'PM': 'PM (Prometheus)',
    'PN': 'PN (Pan)',
    'PO': 'PO (Polydeuces)',
    'PR': 'PR (Plasma RAM direction)',
    'RA': 'RA (Ring A)',
    'RB': 'RB (Ring B)',
    'RC': 'RC (Ring C)',
    'RD': 'RD (Ring D)',
    'RE': 'RE (Ring E)',
    'RF': 'RF (Ring F)',
    'RG': 'RG (Ring G)',
    'RH': 'RH (Rhea)',
    'RI': 'RI (Rings - general)',
    'SA': 'SA (Saturn)',
    'SC': 'SC (Spacecraft activity)',
    'SK': 'SK (Skeleton request)',
    'SR': 'SR (Spacecraft RAM direction)',
    'ST': 'ST (Star)',
    'SU': 'SU (Sun)',
    'SW': 'SW (Solar wind)',
    'TE': 'TE (Tethys)',
    'TI': 'TI (Titan)',
    'TL': 'TL (Telesto)',
    'TO': 'TO (Io torus)',
    'UP': 'UP (Upstream of the wake)'
}

# These mappings are for the TARGET_DESC field to clean them up
_COISS_TARGET_DESC_MAPPING = {
    'DIONE, RHEA, MIMAS(?), RINGS': 'ICY SATELLITES',
    'GENERIC-SATELLITE': 'ICY SATELLITES',
    'SATELLITE SEARCH': 'ICY SATELLITES',
    'TETHYS, RHEA, RINGS': 'ICY SATELLITES',
    'ENCELADUS, RINGS': 'ENCELADUS',
    'IAPETUS FP1': 'IAPETUS',
    'METHON': 'METHONE',
    'ROCK': 'ROCKS',
    'STAR -- CW LEO': 'STAR',
    'STAR -- ETA CAR': 'STAR',
    '--': 'UNKNOWN',
    'UNK': 'UNKNOWN',
    'F RING': 'SATURN-FRING'
}

# These date ranges are used to deduce the MISSION_PHASE_NAME for all Cassini
# data, regardless of whether it is specified in their metadata. This is because
# different instruments specify the mission phases in ways that diverge from
# each other and often are inconsistent with the official definition. Moreover,
# the official definition is multi-valued for many dates. This list is
# single-valued for every observation date but fully consistent with the
# official definition found in the MISSION.CAT file.
_CASSINI_PHASE_NAME_MAPPING = (
    # Short encounters that interrupt longer ones; these take priority so
    # are listed first
    ('Venus 1 Encounter',         cached_tai_from_iso('1998-116T00:00:00.000'),
                                  cached_tai_from_iso('1998-117T00:00:00.000')),
    ('Venus 2 Encounter',         cached_tai_from_iso('1999-175T00:00:00.000'),
                                  cached_tai_from_iso('1999-176T00:00:00.000')),
    ('Earth Encounter',           cached_tai_from_iso('1999-230T00:00:00.000'),
                                  cached_tai_from_iso('1999-231T00:00:00.000')),
    ('Jupiter Encounter',         cached_tai_from_iso('2000-365T00:00:00.000'),
                                  cached_tai_from_iso('2000-366T00:00:00.000')),
    ('Phoebe Encounter',          cached_tai_from_iso('2004-163T00:00:00.000'),
                                  cached_tai_from_iso('2004-164T00:00:00.000')),
    ('Saturn Orbit Insertion',    cached_tai_from_iso('2004-183T00:00:00.000'),
                                  cached_tai_from_iso('2004-184T00:00:00.000')),
    ('Titan A Encounter',         cached_tai_from_iso('2004-300T00:00:00.000'),
                                  cached_tai_from_iso('2004-301T00:00:00.000')),
    ('Titan B Encounter',         cached_tai_from_iso('2004-348T00:00:00.000'),
                                  cached_tai_from_iso('2004-349T00:00:00.000')),
    # Full length encounters that completely cover the mission timeline
    ('Interplanetary Cruise',     cached_tai_from_iso('1997-001T00:00:00.000'),
                                  cached_tai_from_iso('1999-312T00:00:00.000')),
    ('Outer Cruise',              cached_tai_from_iso('1999-312T00:00:00.000'),
                                  cached_tai_from_iso('2002-189T00:00:00.000')),
    ('Science Cruise',            cached_tai_from_iso('2002-189T00:00:00.000'),
                                  cached_tai_from_iso('2004-012T00:00:00.000')),
    ('Approach Science',          cached_tai_from_iso('2004-012T00:00:00.000'),
                                  cached_tai_from_iso('2004-163T00:00:00.000')),
    ('Tour Pre-Huygens',          cached_tai_from_iso('2004-163T00:00:00.000'),
                                  cached_tai_from_iso('2004-359T00:00:00.000')),
    ('Huygens Probe Separation',  cached_tai_from_iso('2004-359T00:00:00.000'),
                                  cached_tai_from_iso('2004-360T00:00:00.000')),
    ('Huygens Descent',           cached_tai_from_iso('2004-360T00:00:00.000'),
                                  cached_tai_from_iso('2005-014T00:00:00.000')),
    ('Titan C Huygens',           cached_tai_from_iso('2005-014T00:00:00.000'),
                                  cached_tai_from_iso('2005-015T00:00:00.000')),
    ('Tour (Prime Mission)',      cached_tai_from_iso('2005-015T00:00:00.000'),
                                  cached_tai_from_iso('2008-183T00:00:00.000')),
    ('Equinox Mission (XM)',      cached_tai_from_iso('2008-183T00:00:00.000'),
                                  cached_tai_from_iso('2010-273T00:00:00.000')),
    ('Solstice Mission (XXM)',    cached_tai_from_iso('2010-273T00:00:00.000'),
                                  cached_tai_from_iso('2020-001T00:00:00.000')),
)

# Wavelength information for combinations of filters
# This data is from the ISS Data User's Guide Table A.2
# When missing from there it is from the CISSCAL files na_effwl.tab
# and wa_effwl.tab
# (Camera, Filter1, Filter2): (Central wavelength, FWHM, Effective wavelength)
# Values are in nm and must be converted to microns!
_COISS_FILTER_WAVELENGTHS = {
    ('N', 'CL1', 'CL2'):   (610.675, 340.056, 651.057),
    ('N', 'CL1', 'GRN'):   (568.134, 113.019, 569.236),
    ('N', 'CL1', 'UV3'):   (338.284, 68.0616, 343.136),
    ('N', 'CL1', 'BL2'):   (439.923, 29.4692, 440.980),
    ('N', 'CL1', 'MT2'):   (727.421, 4.11240, 727.415),
    ('N', 'CL1', 'CB2'):   (750.505, 10.0129, 750.495),
    ('N', 'CL1', 'MT3'):   (889.194, 10.4720, 889.196),
    ('N', 'CL1', 'CB3'):   (937.964, 9.54761, 937.928),
    ('N', 'CL1', 'MT1'):   (618.945, 3.68940, 618.949),
    ('N', 'CL1', 'CB1'):   (619.381, 9.99526, 619.292),
    ('N', 'CL1', 'CB1A'):  (602.908, 9.99526, 602.917),
    ('N', 'CL1', 'CB1B'):  (634.531, 11.9658, 634.526),
    ('N', 'CL1', 'IR3'):   (929.763, 66.9995, 928.304),
    ('N', 'CL1', 'IR1'):   (751.894, 152.929, 750.048),
    ('N', 'RED', 'CL2'):   (650.086, 149.998, 648.879),
    ('N', 'RED', 'GRN'):   (601.032, 51.9801, 600.959),
    ('N', 'RED', 'MT2'):   (726.633, 2.33906, 726.624),
    ('N', 'RED', 'CB2'):   (744.255, 4.22393, 743.912),
    ('N', 'RED', 'MT1'):   (618.911, 3.69858, 618.922),
    ('N', 'RED', 'CB1'):   (619.568, 9.07488, 619.481),
    ('N', 'RED', 'IR3'):   (695.435, 2.04887, 695.040),
    ('N', 'RED', 'IR1'):   (701.900, 44.9603, 701.692),
    ('N', 'BL1', 'CL2'):   (450.851, 102.996, 455.471),
    ('N', 'BL1', 'GRN'):   (497.445, 5.00811, 497.435),
    ('N', 'BL1', 'UV3'):   (386.571, 14.0295, 389.220),
    ('N', 'BL1', 'BL2'):   (440.035, 29.6733, 441.077),
    ('N', 'UV2', 'CL2'):   (297.880, 59.9535, 306.477),
    ('N', 'UV2', 'UV3'):   (315.623, 28.9282, 317.609),
    ('N', 'UV1', 'CL2'):   (258.098, 37.9542, 266.321),
    ('N', 'UV1', 'UV3'):   (350.697, 9.07263, 353.878),
    ('N', 'IRPO', 'MT2'):  (727.434, 4.11241, 727.424),
    ('N', 'IRPO', 'CB2'):  (750.512, 10.0158, 750.501),
    ('N', 'IRPO', 'MT3'):  (889.211, 10.4738, 889.208),
    ('N', 'IRPO', 'CB3'):  (938.001, 9.54946, 937.961),
    ('N', 'IRPO', 'MT1'):  (618.970, 3.69682, 618.967),
    ('N', 'IRPO', 'IR3'):  (930.047, 67.9802, 928.583),
    ('N', 'IRPO', 'IR1'):  (752.822, 153.994, 750.967),
    ('N', 'P120', 'GRN'):  (568.532, 112.946, 569.630),
    ('N', 'P120', 'UV3'):  (341.101, 66.0391, 345.492),
    ('N', 'P120', 'BL2'):  (440.022, 29.4620, 441.079),
    ('N', 'P120', 'MT2'):  (727.430, 4.11216, 727.421),
    ('N', 'P120', 'CB2'):  (750.535, 10.0307, 750.524),
    ('N', 'P120', 'MT1'):  (618.908, 3.69299, 618.920),
    ('N', 'P120', 'CB1'):  (619.961, 9.99561, 619.872),
    ('N', 'P60', 'GRN'):   (568.532, 112.946, 569.630),
    ('N', 'P60', 'UV3'):   (341.101, 66.0391, 345.492),
    ('N', 'P60', 'BL2'):   (440.022, 29.4620, 441.079),
    ('N', 'P60', 'MT2'):   (727.430, 4.11216, 727.421),
    ('N', 'P60', 'CB2'):   (750.535, 10.0307, 750.524),
    ('N', 'P60', 'MT1'):   (618.908, 3.69299, 618.920),
    ('N', 'P60', 'CB1'):   (619.961, 9.99561, 619.872),
    ('N', 'P0', 'GRN'):    (568.532, 112.946, 569.630),
    ('N', 'P0', 'UV3'):    (341.101, 66.0391, 345.492),
    ('N', 'P0', 'BL2'):    (440.022, 29.4620, 441.079),
    ('N', 'P0', 'MT2'):    (727.430, 4.11216, 727.421),
    ('N', 'P0', 'CB2'):    (750.535, 10.0307, 750.524),
    ('N', 'P0', 'MT1'):    (618.908, 3.69299, 618.920),
    ('N', 'P0', 'CB1'):    (619.961, 9.99561, 619.872),
    ('N', 'HAL', 'CL2'):   (655.663, 9.26470, 655.621),
    ('N', 'HAL', 'GRN'):   (648.028, 5.58862, 647.808),
    ('N', 'HAL', 'CB1'):   (650.567, 2.73589, 650.466),
    ('N', 'HAL', 'IR1'):   (663.476, 5.25757, 663.431),
    ('N', 'IR4', 'CL2'):   (1002.40, 35.9966, 1001.91),
    ('N', 'IR4', 'IR3'):   (996.723, 36.0700, 996.460),
    ('N', 'IR2', 'CL2'):   (861.962, 97.0431, 861.066),
    ('N', 'IR2', 'MT3'):   (889.176, 10.4655, 889.176),
    ('N', 'IR2', 'CB3'):   (933.657, 3.71709, 933.593),
    ('N', 'IR2', 'IR3'):   (901.843, 44.0356, 901.630),
    ('N', 'IR2', 'IR1'):   (827.438, 28.0430, 827.331),
    ('W', 'CL1', 'CL2'):   (634.928, 285.999, 633.817),
    ('W', 'CL1', 'RED'):   (648.422, 150.025, 647.239),
    ('W', 'CL1', 'GRN'):   (567.126, 123.999, 568.214),
    ('W', 'CL1', 'BL1'):   (460.418, 62.2554, 462.865),
    ('W', 'CL1', 'VIO'):   (419.684, 18.1825, 419.822),
    ('W', 'CL1', 'HAL'):   (656.401, 9.96150, 656.386),
    ('W', 'CL1', 'IR1'):   (741.456, 99.9735, 739.826),
    ('W', 'IR3', 'CL2'):   (917.841, 45.3074, 916.727),
    ('W', 'IR3', 'RED'):   (690.604, 3.04414, 689.959),
    ('W', 'IR3', 'IRP90'): (917.883, 45.3223, 916.770),
    ('W', 'IR3', 'IRP0'):  (917.883, 45.3223, 916.770),
    ('W', 'IR3', 'IR1'):   (790.007, 3.02556, 783.722),
    ('W', 'IR4', 'CL2'):   (1002.36, 25.5330, 1001.88),
    ('W', 'IR4', 'IRP90'): (1002.44, 25.5299, 1001.98),
    ('W', 'IR4', 'IRP0'):  (1002.44, 25.5299, 1001.98),
    ('W', 'IR5', 'CL2'):   (1034.49, 19.4577, 1033.87),
    ('W', 'IR5', 'IRP90'): (1035.20, 19.4591, 1034.85),
    ('W', 'IR5', 'IRP0'):  (1035.20, 19.4591, 1034.85),
    ('W', 'CB3', 'CL2'):   (938.532, 9.95298, 938.445),
    ('W', 'CB3', 'IRP90'): (938.668, 9.95308, 938.611),
    ('W', 'CB3', 'IRP0'):  (938.668, 9.95308, 938.611),
    ('W', 'MT3', 'CL2'):   (890.340, 10.0116, 890.332),
    ('W', 'MT3', 'IRP90'): (890.368, 10.0118, 890.364),
    ('W', 'MT3', 'IRP0'):  (890.368, 10.0118, 890.364),
    ('W', 'CB2', 'CL2'):   (752.364, 10.0044, 752.354),
    ('W', 'CB2', 'RED'):   (747.602, 4.07656, 747.317),
    ('W', 'CB2', 'IRP90'): (752.373, 10.0049, 752.363),
    ('W', 'CB2', 'IRP0'):  (752.373, 10.0049, 752.363),
    ('W', 'CB2', 'IR1'):   (752.324, 10.0026, 752.314),
    ('W', 'MT2', 'CL2'):   (728.452, 4.00903, 728.418),
    ('W', 'MT2', 'RED'):   (727.517, 2.05059, 727.507),
    ('W', 'MT2', 'IRP90'): (728.470, 4.00906, 728.435),
    ('W', 'MT2', 'IRP0'):  (728.470, 4.00906, 728.435),
    ('W', 'MT2', 'IR1'):   (728.293, 4.00906, 728.284),
    ('W', 'IR2', 'CL2'):   (853.258, 54.8544, 852.448),
    ('W', 'IR2', 'IRP90'): (853.320, 54.8765, 852.510),
    ('W', 'IR2', 'IRP0'):  (853.320, 54.8765, 852.510),
    ('W', 'IR2', 'IR1'):   (826.348, 26.0795, 826.255),
}
# The following filter combinations are found in the data (through COISS_2111)
# but aren't in the above table.
# If one of the filters is a polarizer, we substitute it with CLEAR and see if
# that works. Note that this isn't really a great choice - IRP especially has
# a fairly narrow pass band. If this doesn't work or neither of the filters is
# a polarizer, we just set the result to NULL. These combinations are often
# silly anyway. Who wants IR2+UV3?
# N/HAL/UV3
# N/IR2/UV3
# N/IR4/UV3
# N/IRP0/CB1
# N/IRP0/CB2
# N/IRP0/CB3
# N/IRP0/CL2
# N/IRP0/GRN
# N/IRP0/IR1
# N/IRP0/IR3
# N/IRP0/MT1
# N/IRP0/MT2
# N/IRP0/MT3
# N/P0/CL2
# N/P0/IR1
# N/P0/IR3
# N/P120/CL2
# N/P120/IR1
# N/P60/CL2
# N/P60/IR1
# N/RED/UV3
# N/UV1/BL2
# N/UV1/CB1
# N/UV1/CB2
# N/UV1/GRN
# N/UV1/IR1
# N/UV1/IR3
# N/UV2/BL2
# N/UV2/CB1
# N/UV2/CB2
# N/UV2/GRN
# N/UV2/IR1
# N/UV2/IR3
# N/UV2/MT1
# W/CB3/HAL
# W/CB3/VIO
# W/CL1/IRP0
# W/CL1/IRP90
# W/IR3/BL1
# W/MT3/BL1

class ObsCassiniCommon(ObsBase):
    """What every Cassini instrument shares.

    Its ``field_obs_*`` methods each fill the schema column their name ends in,
    declaring the type `opus_import.obs.field_types` gives that column.
    """

    if TYPE_CHECKING:
        # Supplied by ObsGeneral, which every class combining this one also inherits.
        def field_obs_general_time1(self) -> FloatField: ...
        def field_obs_general_time2(self) -> FloatField: ...


    ################################################################################
    # HELPER FUNCTIONS USED BY CASSINI INSTRUMENTS
    ################################################################################

    # Equinox: 2009-08-11T01:40:08.914
    # After this time, north side of the ring is lit.
    # Before this time, south side of the ring is lit.
    def _is_ring_north_side_lit(self) -> bool | None:
        """Whether the Sun was on the north face of Saturn's rings.

        Returns:
            True after Saturn's 2009 equinox and False before it, or None if the
            observation has no start time. Which face is lit is what turns an angle
            measured
            from the lit face into a north-based one.
        """
        start_time = self.field_obs_general_time1()
        if start_time is None:
            return None
        equinox_time = cached_tai_from_iso('2009-08-11T01:40:08.914')
        return cast(bool | None, start_time > equinox_time)

    def _coiss_target_desc_mapping(self) -> dict[str, str]:
        """Return the corrections applied to COISS ``TARGET_DESC`` values.

        Returns:
            The mapping, which a subclass overrides where its own volumes spell a target
            differently.
        """
        return _COISS_TARGET_DESC_MAPPING

    def _parse_cassini_sclk(self, sclk: str,
                            log_func: Callable[[str], None] | None = None
                            ) -> FloatField:
        """Parse a Cassini SCLK, reporting a bad one instead of raising.

        log_func defaults to `_log_nonrepeating_error`. COCIRS_56xxx passes
        `_log_nonrepeating_warning` instead: an unparseable SCLK there has always
        been a warning rather than an error.

        Returns the converted SCLK, or None if it could not be parsed.
        """
        return self._parse_sclk(opus_support.parse_cassini_sclk, sclk, 'Cassini',
                                log_func)

    def _cassini_valid_obs_name(self, obs_name: str | None) -> TypeGuard[str]:
        r"""Check a Cassini observation name to see if it is parsable. Such a
        name will have four parts separated by _:

        <PRIME> _ <REVNO> <TARGETCODE> _ <ACTIVITYNAME> <ACTIVITYNUMBER> _ <INST>

        or, in the case of VIMS (sometimes):

        <PRIME> _ <REVNO> <TARGETCODE> _ <ACTIVITYNAME> <ACTIVITYNUMBER>

        <PRIME> can be: ([A-Z]{2,5}|22NAV)
            - '18ISS', '22NAV', 'CIRS', 'IOSIC', 'IOSIU', 'IOSIV', 'ISS',
              'NAV', 'UVIS', 'VIMS'
            - If <INST> is 'PRIME' or 'PIE' then <PRIME> can only be one of:
              '22NAV', 'CIRS', 'ISS', 'NAV', 'UVIS', 'VIMS'

        <REVNO> can be: ([0-2]\d\d|00[A-C]|C\d\d)
            - 000 to 299
            - 00A to 00C
            - C00 to C99

        <TARGETCODE> can be: [A-Z]{2}
            - See _CASSINI_TARGET_CODE_MAPPING

        <ACTIVITYNAME> can be: [0-9A-Z]+
            - Everything except the final three digits

        <ACTIVITYNUMBER> can be: \d\d\d
            - Last final three digits

        <INST> can be one of: [A-Z]{2,7}
            - 'PRIME', 'PIE' (prime inst is in <PRIME>)
            - 'CAPS', 'CDA', 'CIRS', 'INMS', 'ISS', 'MAG', 'MIMI', 'NAV', 'RADAR',
              'RPWS', 'RSS', 'SI', 'UVIS', 'VIMS'
            - Even though these aren't instruments, it can also be:
              'AACS' (reaction wheel assembly),
              'ENGR' (engineering),
              'IOPS',
              'MP' (mission planning),
              'RIDER', 'SP', 'TRIGGER'

        If <INST> is missing but everything else is OK, we assume it's PRIME
        """

        if obs_name is None:
            return False

        ret = re.fullmatch(
    r'([A-Z]{2,5}|22NAV)_([0-2]\d\d|00[A-C]|C\d\d)[A-Z]{2}_[0-9A-Z]+\d\d\d_[A-Z]{2,7}',
            obs_name)
        if ret:
            return True

        # Try without _INST
        ret = re.fullmatch(
    r'([A-Z]{2,5}|22NAV)_([0-2]\d\d|00[A-C]|C\d\d)[A-Z]{2}_[0-9A-Z]+\d\d\d',
            obs_name)
        return bool(ret)

    # Break points for each planet
    _JUPITER_TAI = cached_tai_from_iso('2000-262T00:32:38.930')
    _SATURN_TAI = cached_tai_from_iso('2003-138T02:16:18.383')

    def _cassini_planet_id(self) -> str:
        """Find the planet associated with an observation. This is based on the
        mission phase (as encoded in the observation time so it works with all
        instruments)."""
        time_sec2 = self.field_obs_general_time2()
        if time_sec2 is None or time_sec2 < self._JUPITER_TAI:
            return 'OTH'
        if time_sec2 < self._SATURN_TAI:
            return 'JUP'
        return 'SAT'

    def _cassini_normalize_mission_phase_name(self) -> str | None:
        """Return the mission phase this observation falls in, by its start time.

        The phase is derived from the time rather than read from the label, because the
        labels do not agree on how a phase is spelled or on when one ends.

        Returns:
            The phase name in upper case, or None for a time in no phase's range.
        """
        time1 = self.field_obs_general_time1()
        assert time1 is not None
        for phase, start_time_sec, stop_time_sec in _CASSINI_PHASE_NAME_MAPPING:
            if start_time_sec <= time1 < stop_time_sec:
                return phase.upper()
        return None

    #################################################################
    ### HELPER FUNCTIONS USED BY METHODS FOR obs_instrument_coiss ###
    #################################################################
    # See additional notes under _COISS_FILTER_WAVELENGTHS
    def _coiss_wavelength_helper(self, camera: str | None, filter1: str | None,
                                 filter2: str | None
                                 ) -> tuple[FloatField, FloatField, FloatField]:
        """Look up a COISS filter combination's wavelengths.

        Parameters:
            camera: ``'N'`` or ``'W'``.
            filter1: The first filter wheel's position.
            filter2: The second filter wheel's position.

        Returns:
            The central wavelength, the full width at half maximum, and the effective
            wavelength, in nanometres, or ``(None, None, None)`` for a combination this
            pipeline does not describe, which is logged as an error. A polarized
            combination that is not listed falls back to the unpolarized one and is logged
            as a warning instead.
        """
        key = (camera, filter1, filter2)
        if key in _COISS_FILTER_WAVELENGTHS:
            return _COISS_FILTER_WAVELENGTHS[key]

        # If we don't have the exact key combination, try to set polarization equal
        # to CLEAR for lack of anything better to do.
        nfilter1 = filter1 if filter1 and 'P' not in filter1 else 'CL1'
        nfilter2 = filter2 if filter2 and 'P' not in filter2 else 'CL2'
        key2 = (camera, nfilter1, nfilter2)
        if key2 in _COISS_FILTER_WAVELENGTHS:
            self._log_nonrepeating_warning(
                'Using CLEAR instead of polarized filter for unknown COISS '+
                f'filter combination {key[0]}/{key[1]}/{key[2]}')
            return _COISS_FILTER_WAVELENGTHS[key2]

        self._log_nonrepeating_warning('Ignoring unknown COISS filter combination '+
                                      f'{key[0]}/{key[1]}/{key[2]}')
        return None, None, None

    def _combined_filter(self, camera: str | None = None,
                         filter1: str | None = None,
                         filter2: str | None = None) -> str:
        """Return the single filter name OPUS shows for a two-wheel filter combination.

        Parameters:
            camera: ``'N'`` or ``'W'``, or None to read it from the index.
            filter1: The first filter wheel's position, or None to read the pair from the
                index.
            filter2: The second filter wheel's position, or None for the same reason.

        Returns:
            The name: ``'CLEAR'`` when both wheels are clear, the one filter's name when
            only one is, and otherwise the two joined by ``+`` -- in wavelength order, or
            in
            name order where the wavelengths are equal or unknown, with a polarizer always
            placed second.
        """
        if camera is None:
            camera = self._index_col('INSTRUMENT_ID')[3]

        if filter1 is None or filter2 is None:
            filter1, filter2 = self._index_col('FILTER_NAME')

        _central_wl1, _fwhm1, wl1 = self._coiss_wavelength_helper(camera, filter1, 'CL2')
        _central_wl2, _fwhm2, wl2 = self._coiss_wavelength_helper(camera, 'CL1', filter2)

        new_filter = None

        if filter1 == 'CL1' and filter2 == 'CL2':
            new_filter = 'CLEAR'
        elif filter1 == 'CL1':
            new_filter = filter2
        elif filter2 == 'CL2':
            new_filter = filter1
        else:
            if filter1 and 'P' in filter1:
                new_filter = filter2 + '+' + filter1
            elif filter2 and 'P' in filter2:
                new_filter = filter1 + '+' + filter2
            else:
                same_or_unknown_wl = (wl1 is None or wl2 is None or wl1 == wl2)
                if ((same_or_unknown_wl and filter1 > filter2) or
                    (not same_or_unknown_wl and wl1 is not None and wl2 is not None
                     and wl1 > wl2)):
                    # Place filters in wavelength order
                    # If wavelengths are the same, make it name order
                    filter1, filter2 = filter2, filter1
                new_filter = filter1 + '+' + filter2

        return new_filter

    #############################
    ### OVERRIDE FROM ObsBase ###
    #############################

    @property
    def inst_host_id(self) -> str:
        """The OPUS instrument host id, ``CO``."""
        return 'CO'

    @property
    def mission_id(self) -> str:
        """The OPUS mission id, ``CO``."""
        return 'CO'

    @property
    def primary_filespec(self) -> str | None:
        """The path of this observation's data file.

        Computed from the primary index alone, deliberately: it is what the OPUS id is
        derived from, and the OPUS id is in turn what finds this observation's row in the
        supplemental index.

        Returns:
            The volume-prefixed path.
        """
        # Note it's very important that this can be calculated using ONLY
        # the primary index, not the supplemental index!
        # This is because this (and the subsequent creation of opus_id) is used
        # to actually find the matching row in the supplemental index dictionary.
        # Format: "data/1294561143_1295221348/W1294561143_1.IMG"
        filespec = self._index_col('FILE_SPECIFICATION_NAME')
        assert self.bundle is not None
        return cast(str | None, self.bundle + '/' + filespec)


    #############################################
    ### FIELD METHODS FOR obs_mission_cassini ###
    #############################################

    def field_obs_mission_cassini_opus_id(self) -> StrField:
        return self.opus_id

    def field_obs_mission_cassini_bundle_id(self) -> StrField:
        return self.bundle

    def field_obs_mission_cassini_instrument_id(self) -> StrField:
        return self.instrument_id

    # Override this in obs_cassini_common_pds3/4
    def field_obs_mission_cassini_obs_name(self) -> StrField:
        return None

    def _rev_no(self) -> str | None:
        """Return the Saturn orbit number this observation was taken during.

        Returns:
            The three characters of the observation name that hold it, or None if the
            observation name is unparsable or names a cruise-phase orbit, which OPUS does
            not number.
        """
        obs_name = self.field_obs_mission_cassini_obs_name()
        if not self._cassini_valid_obs_name(obs_name):
            return None
        obs_parts = obs_name.split('_')
        rev_no = obs_parts[1][:3]
        if rev_no[0] == 'C':
            return None
        return rev_no

    def field_obs_mission_cassini_rev_no(self) -> MultFieldRet:
        return self._create_mult_keep_case(self._rev_no())

    def field_obs_mission_cassini_rev_no_int(self) -> IntField:
        rev_no = self._rev_no()
        if rev_no is None:
            return None
        try:
            rev_no_cvt = opus_support.parse_cassini_orbit(rev_no)
        except Exception as e:
            self._log_nonrepeating_error(
                f'Unable to parse Cassini orbit "{rev_no}": {e}')
            return None
        return rev_no_cvt

    def field_obs_mission_cassini_is_prime(self) -> MultFieldRet:
        prime_inst = self._prime_inst_id()
        inst_id = self.instrument_id

        # Change COISS to ISS, etc.
        assert inst_id is not None
        inst_id = inst_id.replace('CO', '')
        if prime_inst == inst_id:
            return self._create_mult('Yes')
        return self._create_mult('No')

    def _prime_inst_id(self) -> str:
        """Return which instrument the observation was primarily taken for.

        A Cassini observation is often recorded by one instrument while another is the
        reason it was taken, and the observation name records both.

        Returns:
            The OPUS instrument id of the prime instrument, or ``'UNK'`` where the
            observation name is missing or unparsable.
        """
        obs_name = self.field_obs_mission_cassini_obs_name()
        if obs_name is None:
            return 'UNK'

        if not self._cassini_valid_obs_name(obs_name):
            return 'UNK'

        obs_parts = obs_name.split('_')
        first = obs_parts[0]
        if len(obs_parts) == 3:
            # This happens for some VIMS observations
            last = 'PRIME'
        else:
            last = obs_parts[-1]

        # If the last part is PRIME, the prime_inst is the first part. Otherwise
        # it's the last part.
        # From Matt Tiscareno:
        # PIE is equivalent to PRIME. These were "pre-integrated elements" that
        # were considered to be tall tent poles in the process of portioning out
        # observation time.
        if last == 'PRIME' or last == 'PIE':
            if first == 'NAV' or first == '22NAV':
                prime_inst_id = 'ISS'
            else:
                prime_inst_id = first
        else:
            if last == 'NAV' or last == 'SI':
                prime_inst_id = 'ISS'
            else:
                prime_inst_id = last

        if prime_inst_id not in ('CIRS', 'ISS', 'RSS', 'UVIS', 'VIMS'):
            prime_inst_id = 'OTHER'

        return prime_inst_id

    def field_obs_mission_cassini_prime_inst_id(self) -> MultFieldRet:
        return self._create_mult(self._prime_inst_id())

    def field_obs_mission_cassini_spacecraft_clock_count1(self) -> FloatField:
        return None

    def field_obs_mission_cassini_spacecraft_clock_count2(self) -> FloatField:
        return None

    def field_obs_mission_cassini_ert1(self) -> FloatField:
        return None

    def field_obs_mission_cassini_ert2(self) -> FloatField:
        return None

    def field_obs_mission_cassini_cassini_target_code(self) -> MultFieldRet:
        obs_name = self.field_obs_mission_cassini_obs_name()
        if obs_name is None:
            return self._create_mult(None)
        if not self._cassini_valid_obs_name(obs_name):
            return self._create_mult(None)
        obs_parts = obs_name.split('_')
        target_code = obs_parts[1][-2:]
        if target_code in _CASSINI_TARGET_CODE_MAPPING:
            return self._create_mult(col_val=target_code,
                                     disp_name=_CASSINI_TARGET_CODE_MAPPING[target_code])

        return self._create_mult(None)

    def field_obs_mission_cassini_cassini_target_name(self) -> MultFieldRet:
        assert self._metadata is not None
        if 'TARGET_NAME' not in self._metadata['index_row']: # RSS
            return self._create_mult(None)
        target_name = self._index_col('TARGET_NAME').title()
        target_name = target_name.replace(':', '') # Bug in COUVIS_0053 index
        if target_name == 'N/A':
            return self._create_mult(None)
        return self._create_mult_keep_case(target_name)

    def field_obs_mission_cassini_activity_name(self) -> StrField:
        obs_name = self.field_obs_mission_cassini_obs_name()
        if not self._cassini_valid_obs_name(obs_name):
            return None
        obs_parts = obs_name.split('_')
        return obs_parts[2][:-3]

    def field_obs_mission_cassini_mission_phase_name(self) -> MultFieldRet:
        raise NotImplementedError

    def field_obs_mission_cassini_sequence_id(self) -> StrField:
        return None

    ##############################################
    ### FIELD METHODS FOR obs_instrument_coiss ###
    ##############################################

    def field_obs_instrument_coiss_opus_id(self) -> StrField:
        return None

    def field_obs_instrument_coiss_bundle_id(self) -> StrField:
        return None

    def field_obs_instrument_coiss_data_conversion_type(self) -> MultFieldRet:
        return self._create_mult(None)

    def field_obs_instrument_coiss_compression_type(self) -> MultFieldRet:
        return self._create_mult(None)

    def field_obs_instrument_coiss_gain_mode_id(self) -> MultFieldRet:
        return self._create_mult(None)

    def field_obs_instrument_coiss_image_observation_type(self) -> MultFieldRet:
        return self._create_mult(None)

    def field_obs_instrument_coiss_missing_lines(self) -> IntField:
        return None

    def field_obs_instrument_coiss_shutter_mode_id(self) -> MultFieldRet:
        return self._create_mult(None)

    def field_obs_instrument_coiss_shutter_state_id(self) -> MultFieldRet:
        return self._create_mult(None)

    def field_obs_instrument_coiss_image_number(self) -> IntField:
        return None

    def field_obs_instrument_coiss_instrument_mode_id(self) -> MultFieldRet:
        return self._create_mult(None)

    def field_obs_instrument_coiss_target_desc(self) -> MultFieldRet:
        return self._create_mult(None)

    def field_obs_instrument_coiss_combined_filter(self) -> MultFieldRet:
        return self._create_mult(None)

    def field_obs_instrument_coiss_camera(self) -> MultFieldRet:
        return self._create_mult(None)
