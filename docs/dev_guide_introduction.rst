.. _dev_guide_introduction:

Introduction
============

OPUS is the Outer Planets Unified Search tool of the Ring-Moon Systems Node of NASA's
Planetary Data System. It lets a scientist search the Node's holdings by observation
metadata -- when an observation was taken, what it was pointed at, what geometry it
covers -- and then retrieve the data files that match.

Who this guide is for
---------------------

This guide is the manual for working *on* OPUS. It assumes a competent Python
developer who is new to this codebase, and it favors architecture and contracts over
restating what the code already says. Where a module's own docstring is the
authoritative description of something, this guide points at it rather than copying
it, because a copy goes stale and a cross-reference does not.

Two other documents sit beside it. The :ref:`Public Web API guide <api_guide>`
documents the HTTP interface an OPUS server offers, and is written for people using
OPUS rather than developing it. ``CONTRIBUTING.md`` in the repository root, reproduced
under :ref:`dev_guide_contributing`, describes how to propose a change.

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
    of the database the import pipeline wrote. It runs under a WSGI server.

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

Runtime and dependencies
------------------------

OPUS needs **Python 3.12 or later** and **MySQL 8**. The database backend is written
against an abstraction (:mod:`opus_import.importdb`) that keeps room for another
brand, but MySQL is the only brand implemented.

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
