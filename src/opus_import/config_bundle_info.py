"""How to import each kind of bundle, keyed by a pattern matching the bundle id.

`BUNDLE_INFO` is what makes a bundle importable at all: an id that matches no entry is
one OPUS does not know, and an entry whose ``instrument_class`` is None names a bundle
OPUS knows and deliberately ignores. `opus_import.steps.do_import_tables.lookup_vol_info`
is how the pipeline reads it.
"""

from typing import Literal, TypedDict

# flake8: noqa

from opus_import.obs.obs_base import ObsBase
from opus_import.obs.obs_volume_cocirs_56xxx import ObsVolumeCOCIRS56xxx
from opus_import.obs.obs_volume_cocirs_01xxx import ObsVolumeCOCIRS01xxx
from opus_import.obs.obs_volume_coiss_12xxx import ObsVolumeCOISS12xxx
from opus_import.obs.obs_volume_corss_8xxx import ObsVolumeCORSS8xxx
from opus_import.obs.obs_volume_couvis_0xxx import ObsVolumeCOUVIS0xxx
from opus_import.obs.obs_volume_couvis_8xxx import ObsVolumeCOUVIS8xxx
from opus_import.obs.obs_volume_covims_0xxx import ObsVolumeCOVIMS0xxx
from opus_import.obs.obs_volume_covims_8xxx import ObsVolumeCOVIMS8xxx
from opus_import.obs.obs_volume_ebrocc_xxxx import ObsVolumeEBROCCxxxx
from opus_import.obs.obs_volume_go_0xxx import ObsVolumeGO0xxx
from opus_import.obs.obs_volume_hstjx_xxxx import ObsVolumeHSTJxxxxx
from opus_import.obs.obs_volume_hstnx_xxxx import ObsVolumeHSTNxxxxx
from opus_import.obs.obs_volume_hstox_xxxx import ObsVolumeHSTOxxxxx
from opus_import.obs.obs_volume_hstix_xxxx import ObsVolumeHSTIxxxxx
from opus_import.obs.obs_volume_hstux_xxxx import ObsVolumeHSTUxxxxx
from opus_import.obs.obs_volume_nhxxlo_xxxx import ObsVolumeNHxxLOXxxx
from opus_import.obs.obs_volume_nhxxmv_xxxx import ObsVolumeNHxxMVXxxx
from opus_import.obs.obs_volume_vgiss_5678xxx import ObsVolumeVGISS5678xxx
from opus_import.obs.obs_volume_vg2801_vg2802 import ObsVolumeVG2801VGPPS, ObsVolumeVG2802VGUVS
from opus_import.obs.obs_volume_vg2803 import ObsVolumeVG2803VGRSS
from opus_import.obs.obs_volume_vg2810 import ObsVolumeVG2810VGISS

from opus_import.obs.obs_bundle_uranus_occs_earthbased import ObsBundleUranusOccsEarthbased
from opus_import.obs.obs_bundle_cassini_uvis_solarocc_beckerjarmak2023 import (
    ObsBundleCassiniUvisSolarOccBeckerJarmak,
)
from opus_import.obs.obs_bundle_cassini_iss_fring_mosaics_rsfrench2025 import (
    ObsBundleCassiniISSFRingMosaicsRSFrench2025,
)

# The BUNDLE_INFO structure is used to determine the details of importing
# each distinct type of bundle/volume.
# - The first element of each tuple is a regular expression to match the bundle_id.
# - The second element of each tuple is a dictionary with these keys:
#   - pds_version: 3 for PDS3, 4 for PDS4.
#   - primary_index: The name of the primary index file. <BUNDLE> will be
#       substituted with the current bundle/volume ID. This is used to distinguish
#       between plain index files and other special index files like
#       raw_image_index for VGISS.
#   - validate_index_rows: True if we should check the filespec for each row in
#       the primary index to see if filespec -> opus_id -> filespec is
#       idempotent. If it's not, we ignore this row. This is used to handle
#       index files that include multiple versions of each opus_id or information
#       on other support files. Basically this guarantees that only a single row
#       will be used for each opus_id.
#   - temporal_camera: True if the observation can span multiple time steps. This
#       is used to determine whether the gridless ring and surface geo fields
#       should have identical min/max, or whether it's OK for them to be different.
#       When True, we assume that the observation happens over such a long time
#       period that things like ring center distance can vary.
#   - instrument_class: The Python class, imported above, that will handle the
#       import.


class BundleInfo(TypedDict):
    """What the import needs to know about one kind of bundle.

    Attributes:
        pds_version: 3 or 4.
        primary_index: The primary index file names, with ``<BUNDLE>`` standing for the
            bundle id, or None for a bundle OPUS does not import.
        validate_index_rows: True to resolve an observation that has several index
            rows down to the one whose filespec survives a round trip through the OPUS
            id. An observation with a single row is kept without that check. Bundles
            whose index carries several rows per observation need this.
        temporal_camera: True if one observation can span enough time for a gridless
            geometry value to differ between its start and its end, which is what
            decides whether such a pair is allowed to disagree.
        instrument_class: The `opus_import.obs` class that imports this bundle, or None
            for a bundle OPUS knows about and deliberately ignores. It is None exactly
            when ``primary_index`` is.
    """

    pds_version: Literal[3, 4]
    primary_index: tuple[str, ...] | None
    validate_index_rows: bool
    temporal_camera: bool
    instrument_class: type[ObsBase] | None


BUNDLE_INFO: list[tuple[str, BundleInfo]] = [
    ####################
    ### PDS3 VOLUMES ###
    ####################
    (
        r'COCIRS_0[0123]\d\d|COCIRS_0401',  # We ignore these volumes from early
        {
            'pds_version': 3,
            'primary_index': None,  # in the cruise without metadata
            'validate_index_rows': False,
            'temporal_camera': True,
            'instrument_class': None,
        },
    ),
    (
        r'COCIRS_040[2-9]|COCIRS_041\d|COCIRS_0[5-9]\d\d|COCIRS_1\d\d\d',  # COCIRS_0402->
        {
            'pds_version': 3,
            'primary_index': (
                '<BUNDLE>_cube_equi_index.lbl',
                '<BUNDLE>_cube_point_index.lbl',
                '<BUNDLE>_cube_ring_index.lbl',
            ),
            'validate_index_rows': False,
            'temporal_camera': True,
            'instrument_class': ObsVolumeCOCIRS01xxx,
        },
    ),
    (
        r'COCIRS_[56]\d\d\d',
        {
            'pds_version': 3,
            'primary_index': ('OBSINDEX.LBL',),
            'validate_index_rows': False,
            'temporal_camera': True,
            'instrument_class': ObsVolumeCOCIRS56xxx,
        },
    ),
    (
        r'COISS_[12]\d\d\d',
        {
            'pds_version': 3,
            'primary_index': ('<BUNDLE>_index.lbl',),
            'validate_index_rows': False,
            'temporal_camera': False,
            'instrument_class': ObsVolumeCOISS12xxx,
        },
    ),
    (
        r'CORSS_8001',
        {
            'pds_version': 3,
            'primary_index': ('<BUNDLE>_index.lbl',),
            'validate_index_rows': True,
            'temporal_camera': True,
            'instrument_class': ObsVolumeCORSS8xxx,
        },
    ),
    (
        r'COUVIS_0\d\d\d',
        {
            'pds_version': 3,
            'primary_index': ('<BUNDLE>_index.lbl',),
            'validate_index_rows': False,
            'temporal_camera': True,
            'instrument_class': ObsVolumeCOUVIS0xxx,
        },
    ),
    (
        r'COUVIS_8001',
        {
            'pds_version': 3,
            'primary_index': ('<BUNDLE>_index.lbl',),
            'validate_index_rows': True,
            'temporal_camera': True,
            'instrument_class': ObsVolumeCOUVIS8xxx,
        },
    ),
    (
        r'COVIMS_0\d\d\d',
        {
            'pds_version': 3,
            'primary_index': ('<BUNDLE>_index.lbl',),
            'validate_index_rows': False,
            'temporal_camera': True,
            'instrument_class': ObsVolumeCOVIMS0xxx,
        },
    ),
    (
        r'COVIMS_8001',
        {
            'pds_version': 3,
            'primary_index': ('<BUNDLE>_index.lbl',),
            'validate_index_rows': True,
            'temporal_camera': True,
            'instrument_class': ObsVolumeCOVIMS8xxx,
        },
    ),
    (
        r'EBROCC_0001',
        {
            'pds_version': 3,
            'primary_index': ('<BUNDLE>_index.lbl',),
            'validate_index_rows': True,
            'temporal_camera': True,
            'instrument_class': ObsVolumeEBROCCxxxx,
        },
    ),
    (
        r'GO_0001',
        {
            'pds_version': 3,
            'primary_index': None,
            'validate_index_rows': False,
            'temporal_camera': False,
            'instrument_class': None,
        },
    ),
    (
        r'GO_000[2-9]|GO_001\d|GO_002\d',
        {
            'pds_version': 3,
            'primary_index': ('<BUNDLE>_index.lbl', '<BUNDLE>_sl9_index.lbl'),
            'validate_index_rows': True,
            'temporal_camera': False,
            'instrument_class': ObsVolumeGO0xxx,
        },
    ),
    (
        r'HSTI\d_\d\d\d\d',
        {
            'pds_version': 3,
            'primary_index': ('<BUNDLE>_index.lbl',),
            'validate_index_rows': False,
            'temporal_camera': False,
            'instrument_class': ObsVolumeHSTIxxxxx,
        },
    ),
    (
        r'HSTJ\d_\d\d\d\d',
        {
            'pds_version': 3,
            'primary_index': ('<BUNDLE>_index.lbl',),
            'validate_index_rows': False,
            'temporal_camera': False,
            'instrument_class': ObsVolumeHSTJxxxxx,
        },
    ),
    (
        r'HSTN\d_\d\d\d\d',
        {
            'pds_version': 3,
            'primary_index': ('<BUNDLE>_index.lbl',),
            'validate_index_rows': False,
            'temporal_camera': False,
            'instrument_class': ObsVolumeHSTNxxxxx,
        },
    ),
    (
        r'HSTO\d_\d\d\d\d',
        {
            'pds_version': 3,
            'primary_index': ('<BUNDLE>_index.lbl',),
            'validate_index_rows': False,
            'temporal_camera': False,
            'instrument_class': ObsVolumeHSTOxxxxx,
        },
    ),
    (
        r'HSTU\d_\d\d\d\d',
        {
            'pds_version': 3,
            'primary_index': ('<BUNDLE>_index.lbl',),
            'validate_index_rows': False,
            'temporal_camera': False,
            'instrument_class': ObsVolumeHSTUxxxxx,
        },
    ),
    (
        r'NH..LO_1001',
        {
            'pds_version': 3,
            'primary_index': ('<BUNDLE>_index.lbl',),
            'validate_index_rows': True,
            'temporal_camera': False,
            'instrument_class': ObsVolumeNHxxLOXxxx,
        },
    ),
    (
        r'NH..MV_1001',
        {
            'pds_version': 3,
            'primary_index': ('<BUNDLE>_index.lbl',),
            'validate_index_rows': True,
            'temporal_camera': True,
            'instrument_class': ObsVolumeNHxxMVXxxx,
        },
    ),
    (
        r'NH...._2\d\d\d',  # Ignore these volumes - we only import 1001
        {
            'pds_version': 3,
            'primary_index': None,
            'validate_index_rows': False,
            'temporal_camera': False,
            'instrument_class': None,
        },
    ),
    (
        r'VGISS_[5678]\d\d\d',
        {
            'pds_version': 3,
            'primary_index': ('<BUNDLE>_raw_image_index.lbl',),
            'validate_index_rows': False,
            'temporal_camera': False,
            'instrument_class': ObsVolumeVGISS5678xxx,
        },
    ),
    (
        r'VG_2801',
        {
            'pds_version': 3,
            'primary_index': ('<BUNDLE>_index.lbl',),
            'validate_index_rows': True,
            'temporal_camera': True,
            'instrument_class': ObsVolumeVG2801VGPPS,
        },
    ),
    (
        r'VG_2802',
        {
            'pds_version': 3,
            'primary_index': ('<BUNDLE>_index.lbl',),
            'validate_index_rows': True,
            'temporal_camera': True,
            'instrument_class': ObsVolumeVG2802VGUVS,
        },
    ),
    (
        r'VG_2803',
        {
            'pds_version': 3,
            'primary_index': ('<BUNDLE>_index.lbl',),
            'validate_index_rows': True,
            'temporal_camera': True,
            'instrument_class': ObsVolumeVG2803VGRSS,
        },
    ),
    (
        r'VG_2810',
        {
            'pds_version': 3,
            'primary_index': ('<BUNDLE>_index.lbl',),
            'validate_index_rows': True,
            'temporal_camera': True,
            'instrument_class': ObsVolumeVG2810VGISS,
        },
    ),
    ####################
    ### PDS4 BUNDLES ###
    ####################
    (
        r'cassini_iss_fring_mosaics_rsfrench2025',
        {
            'pds_version': 4,
            'primary_index': ('global_mosaic_index.tab',),
            'validate_index_rows': False,
            'temporal_camera': True,
            'instrument_class': ObsBundleCassiniISSFRingMosaicsRSFrench2025,
        },
    ),
    (
        r'cassini_uvis_solarocc_beckerjarmak2023',
        {
            'pds_version': 4,
            'primary_index': ('<BUNDLE>_index.csv',),
            'validate_index_rows': False,
            'temporal_camera': True,
            'instrument_class': ObsBundleCassiniUvisSolarOccBeckerJarmak,
        },
    ),
    (
        r'uranus_occ_u.*',
        {
            'pds_version': 4,
            'primary_index': (
                '<BUNDLE>_rings_index.csv',
                '<BUNDLE>_global_index.csv',
                '<BUNDLE>_atmosphere_index.csv',
            ),
            'validate_index_rows': True,
            'temporal_camera': True,
            'instrument_class': ObsBundleUranusOccsEarthbased,
        },
    ),
    # These bundles are part of uranus_occs_earthbased but should not be imported
    (
        r'checksums_uranus_occs_earthbased|uranus_occ_support|superseded',
        {
            'pds_version': 4,
            'primary_index': None,
            'validate_index_rows': False,
            'temporal_camera': True,
            'instrument_class': None,
        },
    ),
]
