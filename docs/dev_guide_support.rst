.. _dev_guide_support:

Configuration and Shared Conversions
====================================

Two small packages sit under both programs. Neither imports the other, and neither
imports :mod:`opus_import` or :mod:`opus_app` -- that is what lets both programs depend
on them without depending on each other.

opus_config
-----------

:mod:`opus_config` reads the installation's TOML file and hands it back as frozen
dataclasses. It has **no default location for the file**: ``OPUS_CONFIG`` must name
it, and an unset variable, a missing file or an invalid one is an error at startup
rather than a surprise later.

:func:`opus_config.config.get_config` is the entry point, and it caches: the file is read
once per process. A test that loads a different configuration has to clear that cache,
which ``tests/conftest.py`` does around every test.

The four sections mirror the file: ``database``, ``paths``, ``django`` and
``import``. Validation is explicit rather than best-effort -- an unknown key, a
missing required key, or a value of the wrong type is reported with the table and key
at fault. ``opus.toml.template`` in the repository root documents every key and is the
file to copy when configuring an installation.

:mod:`opus_config` also hosts ``_version.py``, which setuptools-scm writes at build
time. Every other package asks
:func:`importlib.metadata.version` for the distribution's version instead of carrying
one.

opus_support
------------

:mod:`opus_support` holds the conversions the import pipeline and the web application
both need. The import pipeline uses them to normalize what it reads out of a PDS
label; the web application uses them to parse what a user typed and to format what it
returns. Both have to agree exactly, which is why they are one package rather than two
copies.

It is **internal**: it carries no API guarantees for anything outside this
distribution, even though its import name has no ``opus_app``-style prefix. Its whole
public surface is re-exported from the package root, and both programs import from
there (``from opus_support import parse_form_type``) rather than from the module a
name happens to be defined in. The modules below are where to look for an
implementation, not what to import.

:mod:`opus_support.units`
    The unit systems. ``UNIT_FORMAT_DB`` maps a unit id to its units, their conversion
    factors, and the functions that parse and format a value in each. It is what
    :func:`~opus_support.units.parse_form_type`,
    :func:`~opus_support.units.get_valid_units` and
    :func:`~opus_support.units.get_default_unit` read, and therefore what decides which
    units an API call may ask a field's values in.

:mod:`opus_support.time_parsing`
    Times, in every spelling OPUS accepts -- ``ymdhms``, ``ydhms``, Julian and
    modified Julian dates, ephemeris time -- built on ``rms-julian``.

:mod:`opus_support.sclk`
    Spacecraft clock counts, whose format differs per mission and per instrument.

:mod:`opus_support.angles`
    Degrees, radians, and the sexagesimal spellings a right ascension or declination
    is written in.

:mod:`opus_support.orbits`
    The Cassini orbit ("rev") numbering, whose first few orbits are named rather than
    numbered.

The package's header carries a standing demand for **100% test coverage**, and
``tests/opus_support/`` is where it is met. A new unit system, clock format or angle
spelling comes with tests for its parse and its format, in both directions, including
the values it rejects.

API reference
-------------

:doc:`api_opus_config`, :doc:`api_opus_support`
