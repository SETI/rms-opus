.. _dev_guide:

Developer Guide
===============

This guide is for people who modify, extend, build, test, release or deploy OPUS. It
assumes a developer who knows the PDS holdings format and nothing about OPUS, and it
explains how the code is organized and how the pieces cooperate; the
:ref:`Public Web API guide <api_guide>` is the manual for people who only want to
query an OPUS server.

Three chapters carry the bulk of it, and they are in the order a value moves: the
database is what the import writes and what the web application reads, so
:ref:`dev_guide_database` comes before :ref:`dev_guide_import`, which comes before
:ref:`dev_guide_webapp`. Each of the three opens on a page naming what is under it, and
holds the rest of its subject as pages beneath.

.. toctree::
   :maxdepth: 2

   dev_guide_introduction
   dev_guide_layout
   dev_guide_environment
   dev_guide_architecture
   dev_guide_database
   dev_guide_import
   dev_guide_webapp
   dev_guide_config
   dev_guide_conversions
   dev_guide_testing
   dev_guide_log_analyzer
   dev_guide_server
   dev_guide_conventions
   dev_guide_contributing
   api_reference
