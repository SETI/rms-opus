"""General routines shared by the OPUS import pipeline and the OPUS Django backend.

Because both code bases need them, these routines can live in neither one; they are
generally related to the conversion of values to and from various text formats.

This package is internal to the ``rms-opus`` distribution and carries no API stability
guarantees for outside users. Its whole public surface is re-exported here, so both sides
import from ``opus_support`` directly (``from opus_support import parse_form_type``) and
never from the individual modules.

NOTE: THIS PACKAGE HAS 100% TEST COVERAGE AND ANY FUTURE MODIFICATIONS MUST
      MAINTAIN THIS LEVEL OF COVERAGE.
"""

from opus_support.angles import (
    format_dms_hms,
    parse_dms,
    parse_dms_hms,
    parse_hms,
    parse_hms_dms,
)
from opus_support.orbits import (
    CASSINI_ORBIT_NAME,
    CASSINI_ORBIT_NUMBER,
    format_cassini_orbit,
    parse_cassini_orbit,
)
from opus_support.sclk import (
    VOYAGER_PLANET_NAMES,
    VOYAGER_PLANET_PARTITIONS,
    format_cassini_sclk,
    format_galileo_sclk,
    format_new_horizons_sclk,
    format_voyager_sclk,
    parse_cassini_sclk,
    parse_galileo_sclk,
    parse_new_horizons_sclk,
    parse_voyager_sclk,
)
from opus_support.time_parsing import (
    MAX_TIME,
    MIN_TIME,
    format_time_et,
    format_time_jd,
    format_time_jed,
    format_time_mjd,
    format_time_mjed,
    format_time_ydoy,
    format_time_ymd,
    parse_time,
)
from opus_support.units import (
    DEG_RAD,
    UNIT_FORMAT_DB,
    adjust_format_string_for_units,
    convert_from_default_unit,
    convert_to_default_unit,
    display_result_unit,
    display_search_unit,
    display_unit_ever,
    format_unit_value,
    get_default_unit,
    get_disp_default_and_avail_units,
    get_single_format_function,
    get_single_parse_function,
    get_unit_display_name,
    get_unit_display_names,
    get_valid_units,
    is_valid_unit,
    is_valid_unit_id,
    parse_form_type,
    parse_unit_value,
)

__all__ = [
    'CASSINI_ORBIT_NAME',
    'CASSINI_ORBIT_NUMBER',
    'DEG_RAD',
    'MAX_TIME',
    'MIN_TIME',
    'UNIT_FORMAT_DB',
    'VOYAGER_PLANET_NAMES',
    'VOYAGER_PLANET_PARTITIONS',
    'adjust_format_string_for_units',
    'convert_from_default_unit',
    'convert_to_default_unit',
    'display_result_unit',
    'display_search_unit',
    'display_unit_ever',
    'format_cassini_orbit',
    'format_cassini_sclk',
    'format_dms_hms',
    'format_galileo_sclk',
    'format_new_horizons_sclk',
    'format_time_et',
    'format_time_jd',
    'format_time_jed',
    'format_time_mjd',
    'format_time_mjed',
    'format_time_ydoy',
    'format_time_ymd',
    'format_unit_value',
    'format_voyager_sclk',
    'get_default_unit',
    'get_disp_default_and_avail_units',
    'get_single_format_function',
    'get_single_parse_function',
    'get_unit_display_name',
    'get_unit_display_names',
    'get_valid_units',
    'is_valid_unit',
    'is_valid_unit_id',
    'parse_cassini_orbit',
    'parse_cassini_sclk',
    'parse_dms',
    'parse_dms_hms',
    'parse_form_type',
    'parse_galileo_sclk',
    'parse_hms',
    'parse_hms_dms',
    'parse_new_horizons_sclk',
    'parse_time',
    'parse_unit_value',
    'parse_voyager_sclk',
]
