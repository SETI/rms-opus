.. _dev_guide_config:

The Configuration File
======================

One TOML file describes an OPUS installation, and :mod:`opus_config` is the package that
reads it. Everything a deployment can vary is in that file -- the database, the holdings
roots, the directories written to, the Django settings, the import pipeline's log files
-- so that no OPUS process reads a second source of truth and no setting is passed from
one program to another.

The file is found through the ``OPUS_CONFIG`` environment variable, and there is **no
default location**. An unset variable, a missing file, or an invalid one is an error at
startup naming what is wrong, rather than a surprise at the first request or halfway
through an import. That is deliberate: a machine hosting several installations gives each
one its own file, and a process that guessed would quietly serve or overwrite a
neighbor's database.

:func:`opus_config.config.get_config` is the entry point, and it caches -- the file is
read once per process, so every part of a process sees one configuration. A test that
loads a different configuration has to clear that cache, which ``tests/conftest.py`` does
around every test. :func:`opus_config.config.load_config` reads a file named directly and
does not cache, which is what a test or a tool that has a path in hand uses.

The four tables mirror the file: ``database``, ``paths``, ``django`` and ``import``, each
read into a frozen dataclass. Validation is explicit rather than best-effort -- an unknown
key, a missing required key, a value of the wrong type, and a value outside the set a key
allows are each reported with the table and the key at fault. ``opus.toml.template`` in
the repository root documents every key and is the file to copy when configuring an
installation; :ref:`dev_guide_installation_configuring` walks through filling it in.

:mod:`opus_config` also hosts ``_version.py``, which setuptools-scm writes at build time.
Every other package asks :func:`importlib.metadata.version` for the distribution's version
rather than carrying one.

:ref:`dev_guide_opus_support` is the other package that sits under both programs.

API reference
-------------

:doc:`api_opus_config`
