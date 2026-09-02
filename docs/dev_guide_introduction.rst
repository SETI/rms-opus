.. _dev_guide_introduction:

Introduction
============

OPUS is the Outer Planets Unified Search tool of the Ring-Moon Systems Node of NASA's
Planetary Data System. It lets a scientist search the Node's holdings by observation
metadata -- when an observation was taken, what it was pointed at, what geometry it
covers -- and then retrieve the data files that match.

Who this guide is for
---------------------

This guide is the manual for working *on* OPUS. It assumes:

* a competent Python developer, who is **new to this codebase**;
* **no prior knowledge of OPUS** -- every term OPUS coins is defined here on first use;
* **familiarity with the PDS holdings format** -- PDS3 volumes and PDS4 bundles, labels,
  index tables, and the shape of an archive directory tree. This guide does not re-teach
  those. It does say precisely which parts of a holdings tree OPUS reads and what it does
  with each of them, because that is an OPUS decision rather than a PDS one.

It favors architecture and contracts over restating what the code already says. Where a
module's own docstring is the authoritative description of something, this guide points
at it rather than copying it, because a copy goes stale and a cross-reference does not.

Two other documents sit beside it. The :ref:`Public Web API guide <api_guide>`
documents the HTTP interface an OPUS server offers, and is written for people using
OPUS rather than developing it. ``CONTRIBUTING.md`` in the repository root, reproduced
under :ref:`dev_guide_contributing`, describes how to propose a change.

.. _dev_guide_reading_order:

How to read it
--------------

The chapters are in reading order, and the order is deliberate:

* **Orientation** -- this chapter, :ref:`dev_guide_layout` and
  :ref:`dev_guide_environment` get a checkout working and say where everything is.
* **The whole system at once** -- :ref:`dev_guide_architecture` is the one-page map of
  the two programs and the database between them. Read it before either subsystem.
* **The import pipeline** -- :ref:`dev_guide_import` and the pages under it, covering
  how holdings become tables, how to run a run, what each module does, how it is tested
  without holdings, and how to add to it.
* **The database** -- :ref:`dev_guide_database` and the pages under it describe the
  thing the two programs share: the schema itself, the JSON every table is created from,
  the OPUS ID, and the data dictionary.
* **The web application** -- :ref:`dev_guide_webapp` and the pages under it, from how a
  request is served to how to add an app.
* **The two shared packages** -- :ref:`dev_guide_config` is the file every OPUS process
  is configured by, and :ref:`dev_guide_opus_support` is what the two programs convert
  values with so that they agree.
* **Testing it, and the third program** -- :ref:`dev_guide_testing` covers the three
  suites and what each one needs, and :ref:`dev_guide_log_analyzer` the log analyzer.
* **Running a server** -- :ref:`dev_guide_server` and the pages under it: installing
  one, fronting it with a web server, and operating it.
* **Working on it** -- :ref:`dev_guide_conventions` and
  :ref:`dev_guide_contributing`, then the generated :doc:`api_reference`.

What the distribution contains
------------------------------

``rms-opus`` is one Python distribution holding three programs -- two of which share a
database -- and two supporting packages:

:mod:`opus_import`
    The import pipeline. It reads PDS3 volumes and PDS4 bundles out of the Node's
    holdings, computes one row of metadata per observation, and writes the OPUS
    database. It runs as ``opus_import``, or equivalently ``python -m opus_import``.

:mod:`opus_app`
    The Django project. It serves the OPUS user interface and the public web API out
    of the database the import pipeline wrote. It runs under a WSGI server, and its
    management commands are run with ``opus_manage``, which is Django's own command
    line with the settings module already named.

:mod:`opus_config`
    The configuration loader. It reads the one TOML file an installation is
    configured by and hands it to the other packages as frozen dataclasses.

:mod:`opus_support`
    Conversions both programs need and neither owns: units, times, spacecraft clock
    counts, angles and orbit numbers. It is internal to this distribution.

:mod:`opus_log_analyzer`
    A separate program that turns a server's Apache access logs into reports on how
    OPUS is being used. It runs as ``opus_log_analyzer``, or equivalently
    ``python -m opus_log_analyzer``; its error-log companion is ``opus_error_analyzer``.

.. _dev_guide_holdings_opus_consumes:

What OPUS reads out of the holdings
-----------------------------------

The import is **index-driven**, and this is the single most important fact about it. A
run never walks an archive looking for data products and never opens one. Everything it
computes comes from the index tables an archive ships, and everything it records about a
*file* -- size, checksum, image dimensions -- comes from an ``rms-pdsfile`` shelf rather
than from the filesystem.

Concretely, for one PDS3 volume or PDS4 bundle:

**The primary index.** One row per observation, or per group of observations where an
instrument records several phases in one row. :mod:`opus_import.config_bundle_info` names
the file to look for, and :mod:`opus_import.steps.do_import` searches the bundle's
``metadata`` directories -- and, for PDS3, the volume's own ``INDEX``/``index`` directory
-- for it. This is the spine of the import: every observation OPUS holds for that bundle
comes from a row of this file.

**The index's own label.** Read alongside the rows, because some instruments record
per-file information as label keywords rather than as table columns.

**The associated metadata files beside it.** These are *discovered*, not configured:
:func:`~opus_import.steps.do_import_index.import_one_index` lists the same directories
and takes every file whose name starts with the bundle id and ends with
``SUMMARY.LBL``, ``SUPPLEMENTAL_INDEX.LBL`` or ``INVENTORY.LBL``, ignoring any name
containing ``999`` because those are the cumulative files. Each kind is joined to the
primary index on the primary file specification:

.. list-table::
   :header-rows: 1

   * - File
     - What it contributes
   * - ``<bundle>_supplemental_index.lbl``
     - Extra columns for the same observations -- at most one row each.
   * - ``<bundle>_ring_summary.lbl``
     - Ring geometry, at most one row per observation. Fills ``obs_ring_geometry``.
   * - ``<bundle>_sky_summary.lbl``
     - Sky (right ascension and declination) geometry, at most one row per observation.
   * - ``<bundle>_<body>_summary.lbl``
     - Surface geometry, **one row per target per observation**, so these are collected
       into a per-observation dictionary keyed by target name. Fills the
       ``obs_surface_geometry__<TARGET>`` tables.
   * - ``<bundle>_inventory.lbl``
     - The list of targets each observation covers. It is CSV rather than a fixed-width
       PDS table, so it is parsed with :mod:`csv` rather than with ``pdstable``.

**The shelves.** ``rms-pdsfile`` answers which files an observation has
(``opus_products()``), and its info shelves supply each file's size, checksum and, for
an image, its width and height. Those values fill ``obs_files``.

Nothing else in the tree is read. There are no data files in the picture at all, which
is exactly why the whole pipeline can be tested against a few megabytes of checked-in
metadata; see :ref:`dev_guide_import_fixture`.

.. _dev_guide_glossary:

OPUS vocabulary
---------------

OPUS coins a small number of terms and reuses a few PDS ones with a narrower meaning.
Every one of them appears throughout this guide.

Bundle
    OPUS's word for **the unit an import run is asked for**: a PDS4 bundle *or* a PDS3
    volume. The command line, :mod:`opus_import.config_bundle_info` and the
    ``bundle_id`` column all use it in that widened sense, so ``COISS_2002`` -- a PDS3
    volume -- is a "bundle" here. Where a passage means specifically one or the other,
    it says PDS3 volume or PDS4 bundle.

Observation
    One row of a bundle's primary index, expanded by *phase* (below) if the instrument
    produces more than one observation per row. It is the unit everything else in OPUS
    is counted in: one observation has one row in ``obs_general``, one OPUS ID, and one
    entry in a result set.

Phase
    An extra dimension some instruments add to an index row. Cassini VIMS records an
    infrared and a visible observation in one row, so its obs class returns two phase
    names and every field method is called once per phase. Most instruments have a
    single, empty, phase name. See
    :attr:`~opus_import.obs.obs_base.ObsBase.phase_names`.

OPUS ID
    The stable, human-readable identifier of one observation, such as
    ``co-iss-n1635813867``. It is derived by ``rms-pdsfile`` from the observation's
    primary file specification, is unique across the whole database, and is what the
    public API and the cart identify observations by. :ref:`dev_guide_opus_id`
    describes the format mission by mission.

Primary file specification
    The path, relative to the holdings root, of an observation's primary data file. It
    is what the OPUS ID is derived from and what every other index file is
    cross-referenced on, so it must be computable from the **primary** index alone. See
    :attr:`~opus_import.obs.obs_base.ObsBase.primary_filespec`.

Obs class
    A class in the :mod:`opus_import.obs` hierarchy. One instance is created per bundle,
    and its ``field_obs_<table>_<column>`` methods compute the columns of that bundle's
    rows. :ref:`dev_guide_import_obs` describes the hierarchy.

Field method
    A method named ``field_obs_<table>_<column>`` on an obs class. The import calls it
    once per column per observation; whatever it returns, after validation, is what goes
    in the database.

Table schema
    The JSON file under ``src/opus_import/table_schemas/`` that defines one OPUS table:
    its columns, their SQL types, where each value comes from, and how the search form
    presents it. It is the single description of the database.
    :ref:`dev_guide_table_schemas` documents every key.

``obs_`` table
    A table holding observation metadata, one row per observation.
    ``obs_general`` is the master: every observation has a row there and every other
    table's rows hang off it. An ``obs_`` table corresponds one-for-one to a
    "Constraints" category in the user interface.

``mult_`` table
    The table of permitted values for one enumerated column. An ``obs_`` column whose
    value comes from a fixed set stores an integer row id into its ``mult_`` table
    rather than the value itself, which is what makes the checkbox searches fast.
    "Mult" is short for *multiple choice*.

Slug
    The short field id an API call names a field by -- ``time1``, ``RINGGEOringradius1``
    -- as distinct from the SQL column name. The mapping lives in ``param_info``.

Import namespace, permanent namespace
    Every table OPUS imports exists twice: once under a configured prefix (the *import*
    namespace) and once without it (the *permanent* namespace, which the web application
    reads). A run writes the import tables and copies them over the permanent ones only
    once the whole run has succeeded.

Cache table
    A table named ``cache_NNN`` holding the ids of the observations one search matched,
    in sort order. The web application builds it once per distinct search and joins
    every later query against it.

Trigger
    A value a user can search for that makes a further table of search parameters
    relevant -- choosing the Cassini mission reveals the Cassini mission table. The
    ``partables`` table records them.

Runtime and dependencies
------------------------

OPUS needs **Python 3.12 or later** and **MySQL 8.0.19 or later**. The database
backend is written against an abstraction (:mod:`opus_import.importdb`) that keeps
room for another brand, but MySQL is the only brand implemented.

The dependencies worth knowing about before reading any code:

* **Django 5.2** -- the web application. OPUS uses Django's ORM only for reading;
  every OPUS table is created by the import pipeline rather than by a migration, and
  the heavier queries are assembled by :mod:`opus_app.apps.tools.sql_builder` instead.
* **rms-pdsfile**, **rms-pdstable**, **rms-pdsparser** -- the Node's own libraries for
  finding files in the holdings and for reading PDS3 labels and index tables.
* **rms-julian** -- time conversions, which :mod:`opus_support.time_parsing` builds on.
* **mysqlclient** -- the MySQL driver. It has no Linux wheel, so installing OPUS
  compiles it and needs the MySQL client development headers.
* **pdfkit** and **qrcode** -- used by the help pages to offer a PDF and a citation QR
  code. ``pdfkit`` shells out to ``wkhtmltopdf``, which is why PDF generation is
  skipped on platforms that do not have it.

The JavaScript and CSS front end is served as static assets with no build step. There
is no bundler; introducing one is tracked separately as issue
`#1436 <https://github.com/SETI/rms-opus/issues/1436>`__.
