"""Standalone authoring tools that are not part of the import pipeline itself.

These modules are run by hand while adding an instrument or mission: `dump_pds_definitions`
helps write the packaged ``table_schemas`` JSON schemas, and `retrieve_ra_dec` prints the
star coordinate table that `opus_import.config_targets` holds. Neither is imported by the
pipeline, and each does its work at import time rather than in a ``main()``, so importing
one runs it.
"""
