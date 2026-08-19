"""The OPUS import pipeline: it populates the OPUS database from PDS3/PDS4 holdings.

The pipeline is a program, not a library: it is run as ``python -m opus_import`` (see
`opus_import.cli` for the command-line surface) and is internal to the ``rms-opus``
distribution, with no API stability guarantees for outside users.

This module deliberately imports nothing. The pipeline's modules import each other by
absolute path (``from opus_import import import_util``), and an empty package root keeps
that graph free of import cycles.
"""
