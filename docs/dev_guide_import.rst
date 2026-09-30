.. _dev_guide_import:

The Import Pipeline
===================

:mod:`opus_import` is the program that turns the PDS holdings into the OPUS database. It
reads the index tables of PDS3 volumes and PDS4 bundles -- never a data file -- computes
one row per observation for every ``obs_`` table, and writes the auxiliary tables the web
application needs to describe what it has written. Every table
:ref:`dev_guide_database` describes is created and filled here.

It is a program rather than a library: nothing outside the distribution imports it, and
it is run as ``opus_import``, or equivalently as ``python -m opus_import``.

This chapter is the whole of it. :ref:`dev_guide_import_overview` is the theory of
operation and the page to read first; the rest are the command-line surface, the
configuration data that says which bundles exist and what each one is, the steps a run
executes in order, the class hierarchy that computes the values, the database layer
underneath, the fixture that tests the pipeline end to end without any holdings, and what
to do to teach it a bundle set it does not know.

.. toctree::
   :maxdepth: 1

   dev_guide_import_overview
   dev_guide_import_running
   dev_guide_import_config
   dev_guide_import_steps
   dev_guide_import_obs
   dev_guide_import_obs_classes
   dev_guide_import_db
   dev_guide_import_fixture
   dev_guide_import_extending
