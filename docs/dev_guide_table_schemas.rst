.. _dev_guide_table_schemas:

Table Schemas
=============

``src/opus_import/table_schemas/`` holds one JSON file per OPUS table, named after the
table. A file is a list of objects in the order the columns appear in the table --
mostly one per column, plus the occasional entry that deliberately defines no column:
a ``constraint``, a table-level key, or a ``pi_referred_slug`` link to a
field defined in another table. This is the single description of the database: the
import pipeline creates every table from it, computes its schema-driven values from it, validates the result
against it, and derives from it what the web application's search form contains.
``obs_files`` is the exception to the second of those -- its rows are built from
literals rather than computed from the schema; see `Filling the column`_ below.

The schemas ship inside the wheel and are read through :mod:`importlib.resources`, so
an installed OPUS finds them without a checkout.

Two files are not tables:

``param_info_ranges.json``
    The named range sets a column's ``pi_ranges`` refers to.

``internal_def_product_types.json``
    A dictionary source rather than a table. Its entries carry only ``definition``,
    ``pi_dict_name`` and ``pi_dict_context`` -- no ``field_name``, no ``field_type``
    -- and :mod:`opus_import.steps.do_dictionary` reads them to fill the
    ``definitions`` table.

Each ``mult_list`` column has a junction table, ``<table>_<column>``, with a schema file
of its own: ``obs_general_target_name.json`` and ``obs_general_target_class.json``. Its
columns are ``mult_id``, one id of the list, and ``obs_general_id``; its primary key is
``(mult_id, obs_general_id)``; it declares a table-level ``key`` on ``obs_general_id`` and
a table-level ``foreign_key`` onto ``obs_general``. The import creates it after the
table holding the column and fills it from that table's rows, so it has no
``data_source`` (:ref:`dev_guide_database_schema_junction_tables`).
``tests/opus_import/test_table_schemas.py`` requires every ``mult_list`` column to have
such a file, and every file holding ``mult_id`` to be one.

``obs_surface_geometry_target.json`` is the schema of ``obs_surface_geometry_target``
and also a *template* of the surface geometry categories: each body's category,
``obs_surface_geometry__<target>``, reads it with ``<TARGET>`` in its ``pi_*`` values
replaced by the body's encoded name and ``<SLUGTARGET>`` by its slug name. The
``target_name`` column's ``pi_*`` values describe the selector category,
``obs_surface_geometry_name``, and carry no placeholder.

Reading a schema is :func:`opus_import.import_util.read_schema_for_table`, which reads a
body's category as the filled-in template, and it is the only place that substitution
happens. Which entries describe a category's fields is
:func:`opus_import.surface_geometry.category_columns`: those whose ``pi_category_name``
is the category.

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
        grep -rqE "['\"]$key['\"]" src --include='*.py' \
            || echo "no literal reader: $key"
    done

It greps for the key as a literal in either quote style, so it has one blind spot worth
knowing before you read its output: a key assembled at the point of use does not appear
as a literal anywhere. ``definition_results`` is the only one today --
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
   * - ``field_charset``
     - ``"ascii"`` on a ``varcharNNN`` or ``text`` column to store it as ``CHARACTER SET
       ascii COLLATE ascii_general_ci``, which compares without case; any other value,
       or the key on another type, is refused. A column without it takes the schema's
       ``utf8mb4``. A value with a character outside ASCII fails the load that writes
       it, and one holding DEL is an error and is stored without it.
       :ref:`dev_guide_database_schema` says which columns carry it.
   * - ``field_notnull``
     - True to declare the column ``NOT NULL``.
   * - ``field_default``
     - The column's default. ``null``, or the string ``"NULL"``, means SQL ``NULL``. A
       value that is neither ``NULL`` nor all digits, a leading minus sign aside, is
       quoted.
       A ``NOT NULL`` column whose default would be ``NULL`` gets no ``DEFAULT``
       clause at all.
   * - ``field_autoincrement``
     - True to add ``AUTO_INCREMENT``.
   * - ``field_key``
     - ``"primary"``, ``"unique"``, ``"foreign"``, or ``true`` for an ordinary index;
       any other value is refused. ``"foreign"`` requires ``field_key_foreign``. A
       table whose name begins ``obs_`` or ``mult_`` is created with only its primary
       key, its unique keys and the keys the per-bundle delete reads -- ``obs_general``'s
       key on ``bundle_id``, and in any other observation table a plain key on
       ``obs_general_id`` alone -- on either write path, and finalization adds the
       others
       (:ref:`dev_guide_import_db_keys`); the finished table carries every key
       declared.
   * - ``field_key_foreign``
     - ``[table, column]``, the target of a foreign key. The constraint is created
       ``ON DELETE RESTRICT ON UPDATE CASCADE``; a foreign key that says what deleting
       the referenced row does is a table-level ``foreign_key`` entry instead. An
       observation table's one foreign key is ``obs_general_id`` onto
       ``obs_general.id``, and every observation table declares it as a table-level
       ``foreign_key`` entry.

       A key on ``opus_id`` is always a plain key, never a unique one, because two
       bundles can produce the same OPUS ID, and both copies are loaded before
       finalization keeps one.
   * - ``constraint``
     - Raw SQL inserted into the ``CREATE TABLE`` in place of a column definition. An
       entry carrying it defines no column.
   * - ``foreign_key``
     - A table-level foreign key, in an entry of its own that defines no column:
       ``{"foreign_key": {"columns": [...], "references": ["<table>", "<column>", ...],
       "on_delete": "cascade"}}``. ``references`` names the referenced table and then
       one column for each of ``columns``. ``on_delete`` is ``"cascade"`` or
       ``"restrict"``, and ``"restrict"`` when it is absent; the key is created
       ``ON DELETE CASCADE`` or ``ON DELETE RESTRICT``, each with ``ON UPDATE CASCADE``,
       and :func:`~opus_import.table_keys.declared_keys` reads it as a
       :class:`~opus_import.table_keys.TableKey` beside the column-level keys, so
       finalization compares it with the server's keys by what it does on delete as
       well. ``cart`` declares its key onto ``obs_general`` this way, with
       ``"cascade"``, so deleting a bundle's observations deletes the cart rows that
       name them rather than being refused.
   * - ``primary_key``
     - A table-level primary key, in an entry of its own that defines no column:
       ``{"primary_key": ["<column>", ...]}``, listing its columns in order. It is how
       a key over several columns is declared, which ``field_key`` cannot express, and
       :func:`~opus_import.table_keys.declared_keys` reads it as a
       :class:`~opus_import.table_keys.TableKey` beside the column-level keys.
       ``search_results`` declares its primary key ``(search_id, sort_order)`` this way,
       and ``obs_surface_geometry_target`` its primary key
       ``(target_name, obs_general_id)``.
   * - ``unique``
     - A table-level unique key over listed columns, in the same form:
       ``{"unique": ["<column>", ...]}``. ``search_results`` declares its unique key
       ``(search_id, obs_general_id)`` this way.
   * - ``key``
     - A table-level plain key over listed columns, in the same form:
       ``{"key": ["<column>", ...]}``. It is created and added like a column's plain
       key: a table whose name begins ``obs_`` or ``mult_`` gains it at finalization.
       ``obs_files`` declares its key ``(opus_id, short_name, version_name)`` this way,
       ``obs_general`` its keys ``(time1, opus_id)``, ``(right_asc, d_right_asc)`` and
       ``(declination1, declination2)``, ``obs_ring_geometry`` a key over each
       longitude column and its ``d_`` partner, ``obs_surface_geometry_target`` a
       key on ``obs_general_id`` and keys that start with ``target_name``, and each
       junction table of a ``mult_list`` column a key on ``obs_general_id``.
       A ``primary_key``, ``unique``, ``key`` or ``fulltext`` entry whose value is not a
       non-empty list of column names is refused.
   * - ``fulltext``
     - A ``FULLTEXT`` index on one column, in the same form:
       ``{"fulltext": ["<column>"]}``. It is built with MySQL's ngram parser, which
       indexes every run of two characters inside a word, and it is how the search
       form's completions find text in the middle of a value
       (:ref:`dev_guide_webapp_search`). The column keeps any B-tree key it declares
       beside it. Finalization adds it, before the table's other keys and in a statement
       of its own (:ref:`dev_guide_import_steps_create_indexes`). The entries are on
       exactly the columns the completions read whose declared width is at most
       :data:`~opus_import.table_keys.FULLTEXT_MAX_WIDTH` characters: each ``STRING``
       field with a slug, read from the column its search reads, which for the OPUS ID
       is ``obs_general.opus_id``. A wider column, a file specification or a note, has
       none, since an index holding nearly every run of two characters of every value
       would outweigh the table. ``tests/opus_app/test_string_choice_fulltext.py``
       derives that set and compares it with the entries.
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
   * - ``varcharNNN``
     - ``varchar(NNN)``
     - The most characters a value may have is part of the type name. The import
       truncates a longer value and logs an error.
   * - ``text``
     - ``text``
     -
   * - ``enum``
     - ``enum(...)``
     - Needs ``field_enum_options``.
   * - ``mult_idx``
     - ``smallint unsigned``
     - The id of a ``mult`` row of this column's mult field; in a junction table, of the
       ``mult_list`` column's field.
   * - ``mult_list``
     - ``JSON``
     - A list of ids of ``mult`` rows of this column's mult field, for a column an
       observation can have several values of. The column has a junction table.
   * - ``json``
     - ``JSON``
     - Arbitrary JSON that is not a list of mult ids.
   * - ``flag_yesno`` ``flag_onoff``
     - ``smallint unsigned``
     - Stored exactly like ``mult_idx``: the "Yes"/"No"/"N/A" and "On"/"Off"/"N/A"
       values are ``mult`` rows like any other enumerated value.
   * - ``datetime``
     - ``datetime``
     -
   * - ``binary32``
     - ``binary(32)``
     - A SHA-256 digest, stored as its bytes.

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
dispatch above: it writes each row's values directly, and numbers an observation's rows
in ``file_number``, from 1, in the order it writes them. Its schema's list-valued
``data_source`` entries are therefore **dead data** -- nothing reads them. The ``TAB:`` values among them are the only ones left in
the repository, and a ``TAB:`` written into any other schema would be reported as an
unknown data source: they are a survival of a vocabulary the pipeline does not
dispatch on.

Validating the value
~~~~~~~~~~~~~~~~~~~~

**All four of these keys are honored only on a numeric column** -- one whose
``field_type`` starts with ``int``, ``uint`` or ``real``. Every one of them is read
inside that single branch of
:func:`opus_import.steps.do_import_obs.import_observation_table`, so putting
``val_max`` on a ``varcharNNN`` or a ``mult_idx`` column silently enforces nothing.
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

A ``GROUP`` or ``MULTIGROUP`` column's values are rows of the ``mult`` table, under the
column's mult field (:ref:`dev_guide_database_schema_mult`). Normally the import
discovers them from the data. Three keys of a column change that:

``mult_options``
    Pins the field's values. Each entry is one ``mult`` row, a list of seven values
    ``[id, value, label, pin, display, grouping, group_pin]``, read by
    :func:`opus_import.import_util.read_mult_option` into
    :class:`~opus_import.import_util.MultOption`, which names the positions so that a
    reader does not have to count them. ``pin`` is an integer, and ``group_pin`` an
    integer or ``null``; a string of digits is refused. The ids are the ones the
    observation rows hold, and a value the import meets that is not in the list is an
    error. The field's ``pinned`` is 1, and finalization never deletes a row its list
    gives. An entry's id and value are what the observations hold and mean, so once
    stored they do not change: an edit to an entry changes its label, pin, display or
    grouping, and an entry that gives a stored id another value, or a stored value
    another id, is an error. No entry may give the id 65535, which a pinned field's
    absent value takes when its list has none.

``mult_overrides``
    Sets the presentation of values the import discovers, on a column that has no
    ``mult_options``. It is a list of objects, each with a required ``value``, which
    names the stored value, and any of ``label``, ``display`` (``"Y"`` or ``"N"``),
    ``grouping`` and ``pin`` (an integer), each of which sets that column of the row.
    Finalization and ``--update-mult-info`` apply them over the stored rows
    (:ref:`dev_guide_import_steps_do_finalize_mult`); an override that names a value the
    field does not hold is logged as a warning and skipped. A column entry renaming one
    value carries, among its other keys:

    .. code-block:: json

        {
            "mult_overrides": [
                {"value": "SOME_VALUE", "label": "Some Value"}
            ]
        }

``mult_field``
    Names the column's mult field outright, so that several columns can share one, or a
    column can hold the field another name gives it. A column without it has the field
    ``<table>.<column>``. ``obs_surface_geometry_target.target_name`` holds the field
    ``obs_surface_geometry_name.target_name``, the surface geometry selector's, which
    the web application reads it by.

:mod:`opus_import.steps.do_update_mult_info` writes the ``mult_options`` and the
``mult_overrides`` over the stored rows of a database that is already imported, and the
code-only deploy runs it, which is how a value is renamed without a re-import
(:ref:`user_guide_deployment_rename_mult_value`).

Keys nothing reads
------------------

The recipe above is the authority; this is what it reports today, with what each one
is.

``comment``, ``comments``
    Notes to whoever reads the schema. Nothing consumes them, and that is what they
    are for.

``definition_results``
    Reported by the recipe and nonetheless read, for the reason given above.

The ``data_source`` entries in ``obs_files.json`` are unread too, for a different
reason: the key is read everywhere else, so no key-level check can see it. See
`Filling the column`_.

.. _dev_guide_table_schemas_checks:

Checking the schemas
--------------------

``tests/opus_import/test_table_schemas.py``, in the database-free unit suite, reads every
packaged schema whole and checks what the import and the web application assume of it,
so a mistake fails the suite rather than an import, or a tooltip nobody sees. An entry is
one of four kinds, told apart by its keys -- a column (``field_name``), a link
(``pi_referred_slug``), a definition with no column (``definition`` and no
``field_name``), or a table-level entry, which is one of ``{"constraint": "..."}``,
``{"foreign_key": {...}}``, ``{"primary_key": [...]}``, ``{"unique": [...]}``,
``{"key": [...]}`` and ``{"fulltext": [...]}`` -- and the checks are:

* **No object names a key twice.** JSON allows it and Python's reader keeps the last
  value without a word, so a key written twice is a value silently ignored. The files
  are read with a loader that refuses it.
* Each entry carries exactly the keys of its kind: a column only the keys above, at
  least ``field_name`` and ``field_type``; a link and a definition exactly theirs; a
  table-level entry its one key. A ``constraint`` is text, and a ``foreign_key`` has
  ``columns`` and ``references``, optionally ``on_delete`` and nothing else, with a
  non-empty list of column names, a table and one column for each of them, and an
  ``on_delete`` of ``"cascade"`` or ``"restrict"``; a ``primary_key``, ``unique``,
  ``key`` or ``fulltext`` entry is a non-empty list of column names. A ``fulltext``
  entry is in an observation table's schema and names one of its columns, a ``varchar``
  of at most :data:`~opus_import.table_keys.FULLTEXT_MAX_WIDTH` characters.
* Every ``field_type`` is one ``create_table`` renders. The renderer and the test read
  the same constants, ``MYSQL_FIELD_TYPE_SQL`` and ``MYSQL_WIDTH_FIELD_TYPE`` in
  :mod:`opus_import.importdb.mysql`, so the two cannot disagree. An ``enum`` column, and
  only one, carries ``field_enum_options``.
* Every ``field_key`` is one ``create_table`` renders, and a foreign key, and only a
  foreign key, names its table and column. The flags are booleans.
* A column with a ``param_info`` row carries the keys that step reads without a default;
  its ``pi_form_type`` names a unit :mod:`opus_support` knows, and its ``pi_ranges`` an
  entry of ``param_info_ranges.json``.
* Every ``mult_options`` row has the seven values of
  :class:`~opus_import.import_util.MultOption`, typed as it says, with distinct ids. Each
  id fits ``mult.id`` below 65535, and each pin and group pin is an integer, never a
  string.
* Every ``mult_overrides`` entry is an object with a ``value`` and only the members
  ``label``, ``display``, ``grouping`` and ``pin``, on a column that holds mult ids and
  has no ``mult_options``.
* Every ``mult_field`` key is a string, on a column that holds mult ids.
* Every definition has a term and a context, no two share both, every context is one
  ``contexts.csv`` defines, and every ``pi_dict_name`` and ``pi_dict_context`` pair a
  column names, for the search form or the results, resolves to a definition the
  dictionary step creates.

A schema change that breaks one of these fails here first. A new key or a new
table-level entry is added to the test in the same change that adds it to a schema.

Choosing a column's keys
------------------------

An index speeds up the searches that read it, but it costs disk space, buffer-pool
memory and import time, so an observation column carries a single-column key
(``"field_key": true``) only when one of these holds:

* searches or results pages filter or sort by the column often, as production's index
  statistics show;
* the import, finalization or a management command reads rows by it;
* a foreign key needs it;
* it is an autocomplete column, a searchable field with the ``STRING`` form type, whose
  prefix match reads the key (a narrow one has a ``fulltext`` entry beside it, for text
  in the middle of a value);
* it is one half of a ``1``/``2`` range pair, and the other half has a key.

Not every column that meets one of these has a key: production's statistics decide, and
a few keys are kept by choice. Columns that are filtered or sorted together get a
table-level ``key`` entry instead. The default sort, ``time1`` then ``opus_id``, has the
key ``(time1, opus_id)``, which holds the observations in that order. A column that leads
such a key needs no key of its own, because the longer key serves every read the shorter
one would.

Adding a column
---------------

See :ref:`dev_guide_extending_column`.

API reference
-------------

:doc:`api_opus_import`
