"""The ``obs_*`` class hierarchy that computes one database row per observation.

Each module defines one class in the hierarchy: `opus_import.obs.obs_base` at the root,
then the PDS3/PDS4 splits, the per-table mixins (general, pds, ring geometry, ...), the
per-mission classes, and finally one class per bundle (volume). `do_import` instantiates
the leaf class chosen by `opus_import.config_bundle_info` and calls its
``field_obs_<table>_<column>`` methods.

Import the classes from their own modules (``from opus_import.obs.obs_base import
ObsBase``); this module deliberately re-exports nothing, because importing every leaf
class here would import every mission's parsing code no matter which bundle is running.
"""
