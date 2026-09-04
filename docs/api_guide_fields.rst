.. _availablefields:

Available Metadata Fields
=========================

Every metadata field OPUS holds, in the order the user interface groups and shows
them. The **Category** is the "Constraints" section a field belongs to, the
**Label** is what a result carries for it, the units under a label are the ones the
field's values may be requested in (see :ref:`Retrieving Metadata
<retrievingmetadata>` and :ref:`Units <units>`), and the **Field ID** is what an API
call names it by.

A separate set of surface geometry fields exists for every target OPUS has geometry
for, and they differ only in that target's name. They are listed once here, with
``<TARGET>`` standing in for the name -- so
``SURFACEGEO<TARGET>_planetographiclatitude1`` is
``SURFACEGEOenceladus_planetographiclatitude1`` for Enceladus. The targets available
for a given search are what :ref:`api/categories.json <categoriesfmt>` returns.

The same information is available through the API itself, in more detail, from
:ref:`api/fields.[fmt] <fieldsfmt>`.

.. include:: api_guide_fields_table.rst
