"""Standalone authoring tools that are not part of the import pipeline itself.

These modules are run by hand while adding an instrument or mission; they help write the
``table_schemas`` JSON files and are never imported by the pipeline. Note that each does
its work at import time rather than in a ``main()``, so importing one runs it.
"""
