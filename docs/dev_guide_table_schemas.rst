.. _dev_guide_table_schemas:

Table Schemas
=============

``src/opus_import/table_schemas/`` holds one JSON file per OPUS table, named after the
table. A file is a list of objects, one per column, in the order the columns appear in
the table. This is the single description of the database: the import pipeline creates
every table from it, computes every value from it, validates the result against it, and
derives from it what the web application's search form contains.

The schemas ship inside the wheel and are read through :mod:`importlib.resources`, so
an installed OPUS finds them without a checkout.

Four files are not tables, and reading any of them as a column list will not work:

``param_info_ranges.json``
    The named range sets a column's ``pi_ranges`` refers to.

``mult_template.json``
    The shape every ``mult_`` table is created with.

``obs_surface_geometry_target.json``
    A *template*: one surface-geometry table is created from it per target, with
    ``<TARGET>`` replaced by the target's encoded name and ``<SLUGTARGET>`` by its
    slug name.

``internal_def_product_types.json``
    A dictionary source rather than a table. Its entries carry only ``definition``,
    ``pi_dict_name`` and ``pi_dict_context`` -- no ``field_name``, no ``field_type``
    -- and :mod:`opus_import.steps.do_dictionary` reads them alongside the PDS data
    dictionary. It is the only file in the directory that names no columns.

Reading a schema is :func:`opus_import.import_util.read_schema_for_table`, and it is
the only place that substitution happens.

Column keys
-----------

Every key below is read by something. **Do not take that on trust and do not take a
list of the modules that read them on trust either** -- an enumeration of code sites is
wrong the moment somebody edits the code. Run this from the repository root instead: it
collects the keys the schemas actually use and prints the ones no Python file mentions.

.. code-block:: bash

    python - <<'EOF' |
    import json
    from pathlib import Path

    keys = set()
    for path in sorted(Path('src/opus_import/table_schemas').glob('*.json')):
        data = json.loads(path.read_text())
        if isinstance(data, list):
            keys.update(key for entry in data for key in entry)
    print('\n'.join(sorted(keys)))
    EOF
    while read -r key; do
        grep -rqF "'$key'" src --include='*.py' || echo "no literal reader: $key"
    done

It greps for the key as a literal, so it has one blind spot worth knowing before you
read its output: a key assembled at the point of use does not appear as a literal
anywhere. ``definition_results`` is the only one today --
:mod:`opus_import.steps.do_dictionary` reads it as ``column['definition'+suffix]`` --
so the recipe reports it and it is nonetheless read. Everything else the recipe reports
really is unread; see `Keys nothing reads`_ below.

Defining the column
~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1

   * - Key
     - Meaning
   * - ``field_name``
     - The column's name in SQL. Required.
   * - ``field_type``
     - The OPUS type, which decides the SQL type. Required; the values are in the
       table below.
   * - ``field_enum_options``
     - Required when ``field_type`` is ``enum``: the comma-separated, quoted list of
       values, rendered straight into ``enum(...)``.
   * - ``field_notnull``
     - True to declare the column ``NOT NULL``.
   * - ``field_default``
     - The column's default. ``null``, or the string ``"NULL"``, means SQL ``NULL``. A
       value that is neither ``NULL``, ``CURRENT_TIMESTAMP`` nor all digits is quoted.
       A ``NOT NULL`` column whose default would be ``NULL`` gets no ``DEFAULT``
       clause at all.
   * - ``field_autoincrement``
     - True to add ``AUTO_INCREMENT``.
   * - ``field_key``
     - ``"primary"``, ``"unique"``, ``"foreign"``, or any other true value for an
       ordinary index. ``"foreign"`` requires ``field_key_foreign``.
   * - ``field_key_foreign``
     - ``[table, column]``, the target of a foreign key. The constraint is created
       ``ON DELETE RESTRICT ON UPDATE CASCADE``, and the referenced table is resolved
       in the same namespace as the table being created.
   * - ``constraint``
     - Raw SQL inserted into the ``CREATE TABLE`` in place of a column definition. An
       entry carrying it defines no column.
   * - ``comments``
     - A note for whoever reads the schema. Nothing consumes it.

The ``field_type`` values, and the SQL each produces, are decided by
:meth:`opus_import.importdb.mysql.ImportDBMySQL.create_table`; a value it does not
recognize raises :exc:`NotImplementedError` rather than being guessed at.

.. list-table::
   :header-rows: 1

   * - ``field_type``
     - MySQL type
     - Notes
   * - ``int1`` ``int2`` ``int3`` ``int4`` ``int8``
     - ``tinyint`` ``smallint`` ``mediumint`` ``int`` ``bigint``
     -
   * - ``uint1`` ``uint2`` ``uint3`` ``uint4`` ``uint8``
     - the same, ``unsigned``
     -
   * - ``real4`` ``real8``
     - ``float`` ``double``
     -
   * - ``charNNN`` ``varcharNNN``
     - ``char(NNN)`` ``varchar(NNN)``
     - The length is part of the type name.
   * - ``text``
     - ``text``
     -
   * - ``enum``
     - ``enum(...)``
     - Needs ``field_enum_options``.
   * - ``mult_idx``
     - ``int unsigned``
     - A row id in this column's ``mult_`` table.
   * - ``mult_list``
     - ``JSON``
     - A list of ``mult_`` row ids, for a column an observation can have several
       values of.
   * - ``json``
     - ``JSON``
     - Arbitrary JSON that is not a list of mult ids.
   * - ``flag_yesno`` ``flag_onoff``
     - ``int unsigned``
     - Stored exactly like ``mult_idx``: the "Yes"/"No"/"N/A" and "On"/"Off"/"N/A"
       values live in a ``mult_`` table like any other enumerated value.
   * - ``timestamp``
     - ``timestamp``
     - Always given ``DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP``,
       whatever the schema says.
   * - ``datetime``
     - ``datetime``
     -

Filling the column
~~~~~~~~~~~~~~~~~~

``data_source`` says where an ``obs_`` column's value comes from.
:func:`opus_import.steps.do_import_obs.import_observation_table` dispatches on it, and
a value it does not recognize is logged as a schema fault.

.. list-table::
   :header-rows: 1

   * - ``data_source``
     - The value is
   * - ``COMPUTE``
     - Whatever this observation's ``field_obs_<table>_<column>`` method returns. This
       is the case for almost every column.
   * - ``OBS_GENERAL_ID``
     - The ``id`` of this observation's ``obs_general`` row, which is how every other
       table hangs off it.
   * - ``MAX_ID``
     - One more than the largest id used in this table so far.
   * - ``LONGITUDE_FIELD``
     - The midpoint of a longitude range, from
       :meth:`~opus_import.obs.obs_base.ObsBase.compute_longitude_field`.
   * - ``D_LONGITUDE_FIELD``
     - The half-span of a longitude range, from
       :meth:`~opus_import.obs.obs_base.ObsBase.compute_d_longitude_field`.

Two more keys change what is computed rather than where it comes from.
``put_mults_here`` marks a column that holds another column's mult id, which the row
builder skips; ``pi_referred_slug`` marks an entry that links to a field defined in
another table rather than defining a column of this one, so no SQL column is created
for it and no value is computed.

``obs_files`` is filled by :mod:`opus_import.steps.do_import_index` rather than by the
dispatch above: it builds each row from a literal, and takes the row id by calling
:func:`opus_import.import_util.find_max_table_id` directly rather than through
``MAX_ID``. Its schema's five list-valued ``data_source`` entries -- the only
``TAB:`` values left in the repository -- are therefore **dead data**: nothing reads
them, and a ``TAB:`` written into any schema would be reported as an unknown data
source. They are a survival of a vocabulary the pipeline no longer dispatches on.

Validating the value
~~~~~~~~~~~~~~~~~~~~

**All four of these keys are honoured only on a numeric column** -- one whose
``field_type`` starts with ``int``, ``uint`` or ``real``. Every one of them is read
inside that single branch of
:func:`opus_import.steps.do_import_obs.import_observation_table`, so putting
``val_max`` on a ``charNNN`` or a ``mult_idx`` column silently enforces nothing.
Several shipping columns already do exactly that.

.. list-table::
   :header-rows: 1

   * - Key
     - Meaning
   * - ``val_min`` ``val_max``
     - The permitted range. A value outside it is stored as ``NULL`` and reported as
       an error.
   * - ``val_sentinel``
     - A value, or list of values, standing for "no data" that the PDS label should
       already have masked. A match is stored as ``NULL`` **and reported as an
       error**, because reaching this check means the label did not mark the value
       missing.
   * - ``val_set_invalid_to_null``
     - True to log an out-of-range value at debug level instead of as an error. The
       value is stored as ``NULL`` either way.

Describing the field to the user interface
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A column carrying ``pi_category_name`` becomes a row of ``param_info``, and that row
is what makes the field visible in the search form and beside a result.
:mod:`opus_import.steps.do_param_info` copies the keys across.

.. list-table::
   :header-rows: 1

   * - Key
     - Meaning
   * - ``pi_category_name``
     - The table this field belongs to, which is also its "Constraints" category. Its
       presence is what makes the column a searchable or displayable field.
   * - ``pi_slug`` ``pi_old_slug``
     - The field id an API call names the field by, and a previous spelling that still
       resolves. A slug beginning with ``**`` is internal and is not offered to users.
   * - ``pi_label`` ``pi_label_results``
     - What the field is called on the Search tab, and beside a result.
   * - ``pi_form_type``
     - ``TYPE[%format][:unit]`` -- the OPUS field type (``STRING``, ``GROUP``,
       ``MULTIGROUP``, ``RANGE``, ``LONG``), the numeric format values are printed
       in, and the unit system they are in.
       :func:`opus_support.units.parse_form_type` splits it, and
       :func:`opus_support.units.is_valid_unit_id` is what rejects an unknown unit at
       import time.
   * - ``pi_display`` ``pi_display_results``
     - Whether the field is offered on the Search tab, and shown beside a result.
   * - ``pi_disp_order`` ``pi_sub_heading``
     - Where the field sits within its category.
   * - ``pi_intro`` ``pi_tooltip``
     - Extra text shown around the field's search widget.
   * - ``pi_dict_context`` ``pi_dict_name``
     - The data-dictionary context and term whose definition is this field's tooltip.
       ``pi_dict_context_results`` and ``pi_dict_name_results`` are the same for the
       results label.
   * - ``pi_ranges``
     - Names an entry in ``param_info_ranges.json``, the preset ranges the search
       widget offers. A name that is not in that file fails the import.
   * - ``pi_referred_slug``
     - This entry is a link to a field defined elsewhere; the slug names it.
   * - ``pi_field_hints1`` ``pi_field_hints2``
     - Hint text for the two ends of a range widget.

``definition`` and ``definition_results`` hold the text
:mod:`opus_import.steps.do_dictionary` loads into the ``definitions`` table for this
field's dictionary terms.

Enumerated values
~~~~~~~~~~~~~~~~~

A ``GROUP`` or ``MULTIGROUP`` column's values live in a ``mult_`` table. Normally the
import discovers them from the data. A column that instead carries ``mult_options``
pins them: each entry is one row of that table, read into
:class:`opus_import.import_util.MultOption`, which names the positions so that a
reader does not have to count them. :mod:`opus_import.steps.do_update_mult_info` is
what writes the pinned display details back over the table after an import.

Keys nothing reads
------------------

The recipe above is the authority; this is what it reports today, with what each one
is.

``comment``, ``comments``
    Notes to whoever reads the schema. Nothing consumes them, and that is what they
    are for.

``data_source_order``, ``pi_units``
    Read by no code at all. They are left where they are rather than removed, because
    deleting a key from a schema is a change to the definition of the database rather
    than documentation work. Do not add either to a new column.

``field_defalut``
    A misspelling of ``field_default``, on one column. It changes nothing today,
    because a missing ``field_default`` already means SQL ``NULL`` and that column's
    value is ``null`` -- but a non-null default written under this spelling would be
    ignored without complaint.

``definition_results``
    Reported by the recipe and nonetheless read, for the reason given above.

The ``data_source`` entries in ``obs_files.json`` are unread too, for a different
reason: the key is read everywhere else, so no key-level check can see it. See
`Filling the column`_.

Adding a column
---------------

See :ref:`dev_guide_extending`.
