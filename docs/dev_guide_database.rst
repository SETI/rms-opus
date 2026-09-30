.. _dev_guide_database:

The OPUS Database
=================

The database is the middle of OPUS. The import pipeline writes it, the web application
reads it, and neither one knows anything about the other: they share this schema, and
their only other common ground is :mod:`opus_config` and :mod:`opus_support`. That makes
it the thing to understand first, which is why it comes before both of them here.

It is one MySQL schema. Observation metadata lives in the ``obs_*`` tables, one row per
observation and one table per group of fields the user interface offers as a "Constraints"
menu; the enumerated values those rows point at live in ``mult_*`` tables; and a handful
of auxiliary tables describe the fields themselves, hold the data dictionary, and carry
what a user's session produces. No OPUS table is created by a Django migration: the
import pipeline creates every one of them from a checked-in JSON description, and the
only tables in the schema that a migration does create are Django's own contrib tables.

.. toctree::
   :maxdepth: 1

   dev_guide_database_schema
   dev_guide_table_schemas
   dev_guide_opus_id
   dev_guide_dictionary

:ref:`dev_guide_database_schema` is the table-by-table reference.
:ref:`dev_guide_table_schemas` is the JSON every one of those tables is created from --
the single description that the import, the validation and the web application's search
form all read. :ref:`dev_guide_opus_id` is the identifier each observation hangs off, and
:ref:`dev_guide_dictionary` is where the tooltip text in ``contexts`` and ``definitions``
comes from.
