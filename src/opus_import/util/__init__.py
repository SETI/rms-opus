"""Standalone authoring tools that are not part of the import pipeline itself.

These modules are run by hand while adding an instrument or mission:
`dump_pds_definitions` helps write the packaged ``table_schemas`` JSON schemas, and
`retrieve_ra_dec` prints the star coordinate table that
`opus_import.config_targets.star_ra_dec` holds. Neither is imported by the pipeline.

Each does its work in a ``main()`` guarded by ``if __name__ == '__main__':``, so
importing one -- as Sphinx autodoc and any package-wide sweep does -- runs nothing. Run
them as ``python -m opus_import.util.dump_pds_definitions <label>`` and
``python -m opus_import.util.retrieve_ra_dec``. `retrieve_ra_dec` issues one live HTTP
request to SIMBAD per star in its table; that is why keeping it out of a bare import
matters.
"""
