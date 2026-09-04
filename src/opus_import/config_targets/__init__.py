"""Information about every target OPUS supports, split one table per module.

The four tables are re-exported here, so a consumer reads them as
``config_targets.TARGET_NAME_INFO`` and never needs to know which module holds
which table.
"""

from opus_import.config_targets.planet_group_mapping import PLANET_GROUP_MAPPING
from opus_import.config_targets.star_ra_dec import STAR_RA_DEC
from opus_import.config_targets.target_name_info import TARGET_NAME_INFO
from opus_import.config_targets.target_name_mapping import TARGET_NAME_MAPPING

__all__ = [
    'PLANET_GROUP_MAPPING',
    'STAR_RA_DEC',
    'TARGET_NAME_INFO',
    'TARGET_NAME_MAPPING',
]
