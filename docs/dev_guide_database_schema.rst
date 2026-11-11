.. _dev_guide_database_schema:

The Database Schema
===================

This page describes the database schema for OPUS 3.x: every table, and what each of its
columns means.

OPUS uses MySQL 8.0.19 or later. MySQL is a relational database based on SQL (Structured Query Language). A relational database is one where data is stored in a collection of *tables*, each of which has pre-defined *columns* with specified data types. The actual data is stored in each table in *rows*, much like in a spreadsheet, and each *row* contains an instance of each *column*. Columns that do not have data available may be marked by storing the special value ``NULL``, if the column's properties are set to permit it. The relational part comes when tables cross-reference each other. For example, a column in one table could be used to select rows from another table. Such an operation is called a *join*, and many tables can be joined together. The joining of tables is the fundamental concept of relational databases. To fully understand the OPUS database it is strongly recommended that you become familiar with relational databases and the SQL language before continuing.

OPUS stores metadata in a series of ``obs_*`` tables. Each ``obs_*`` table generally corresponds to one of the "Constraints" menus visible in the browser UI. For example, ``obs_general`` corresponds to "General Constraints" and ``obs_wavelength`` corresponds to "Wavelength Constraints". This one-to-one correspondence between tables and UI metadata categories is an integral part of the design of OPUS, and if a metadata field is moved to a different "Constraints" category, the table design must also be changed.

Each row in an ``obs_*`` table represents a single observation represented by a unique OPUS ID, and each column generally represents one user-visible metadata field (although there are additional hidden fields as discussed below).

In addition to metadata, OPUS stores other information that helps it operate in tables. This includes information about checkbox fields, the contents of users' Carts, the dictionary of terms and definitions (including tooltips), information about the metadata fields themselves (this is metadata metadata!), and information about the metadata categories.

OPUS Metadata
-------------

It's important to understand that OPUS has its own concept of metadata types independent of the SQL data types. For example, an integer in the database could represent a numeric value (like the pixel size of an image) or the id of a row of the ``mult`` table (like the selection of a particular mission from the available options) or a reference to an entry in another table or just a unique ID in the current table. As such, there needs to be a place to store "metadata about the metadata", and this is the separate ``param_info`` table, which will be discussed later. We will use the term "field type" when discussing OPUS's concept of metadata types, and "SQL data type" when discussing the attributes of a SQL column.

OPUS understands the following high-level field types:

* ``STRING``: A single arbitrary string. It is represented in the database with a SQL ``charNNN`` data type (a string with a maximum length). When searching, the string can be matched exactly or by various types of pattern matching (e.g. ``begins``, ``ends``, ``contains``, ``excludes``, or ``regex``). When displaying metadata, the string is simply shown as-is. Examples:

  * ``Volume ID`` = ``"HSTU0_5392"``
  * ``Primary File Spec`` = ``"HSTU0_5392/DATA/VISIT_03/U2930301T.LBL"``
  * ``PI Name`` = ``"Spencer, John R."``
* ``GROUP``: A selection in a list of possible options. ``GROUP`` is also referred to as a "mult", meaning multiple choice. In the database, a ``GROUP`` is stored as a single integer (using the SQL ``smallint unsigned`` data type), which is the id of a row of the special ``mult`` table, which will be described below. When searching, the user can select one or more checkboxes from the group. Any observation that matches one of the selected checkboxes will be given as a result. When displaying metadata, the integer is converted to a string by looking up its ``mult`` row and the row's label is shown. Examples:

  * ``Mission`` = ``Galileo`` (stored in the database as the value ``1``)
  * ``Saturn Orbit Number (By Checkbox)`` = ``044`` (stored in the database as the value ``23``)
  * ``Body Occultation Flag`` = ``N/A`` (stored in the database as the value ``0``)
* ``MULTIGROUP``: Multiple selections in a list of possible options. This is similar to a ``GROUP``, except that instead of having a single option selected represented as an integer, the database contains a JSON list (using the SQL ``JSON`` data type) containing, potentially, multiple integers. This type is used when a single observation can apply to more than one entry in the group, such as ``Intended Target Name`` (where one observation can be intended for multiple targets in PDS4) or ``Nominal Target Class`` (where multiple intended targets results in multiple target classes). Searching by the user is performed the same way as with a ``GROUP``, except that the matching is done against any of the entries in the list, not just a single integer. If any of the entries match, the observation is returned as a search result. When displaying metadata, each entry in the list is converted to a string by looking up its ``mult`` row and then they are joined together by commas. The functionality provided by ``MULTIGROUP`` is a strict superset of ``GROUP`` and technically we could remove the ``GROUP`` type entirely. However, the performance of searching and retrieving the values from a ``MULTIGROUP`` is roughly 30% slower than a ``GROUP`` due to the need to handle the arbitrary length list of values, and thus we keep both types around for performance. Examples:

  * ``Intended Target Name`` = ``Jupiter,Amalthea``
  * ``Nominal Target Class`` = ``Planet,Regular Satellite``
* ``RANGE``: Either a single integer or floating point value (a "single column range", if the observation only has a single relevant value) or a pair of integers or floating point values (a "dual-column range" if the observation has a range of values represented by minimum and maximum). The value(s) are stored in the database using the appropriate SQL data type, such as ``tinyint``, ``smallint``, ``mediumint``, ``int``, ``bigint``, ``float``, or ``double``. In either case the UI provides the user with a pair of minimum/maximum search boxes.

  * For searching:

    * For a single value, when a search is performed, the database is queried for the simple inequality:

      * If only the minimum value is being searched on: ``usermin <= dbvalue``
      * If only the maximum value is being searched on: ``dbvalue <= usermax``
      * If both are being searched on: ``usermin <= dbvalue <= usermax``
    * For a pair of values, searching is more complicated because you are comparing two overlapping ranges. There are three types of comparisons available:

      * ``all``, meaning the observation's range covers all of the user's specified range (and maybe more): ``dbmin <= usermin AND dbmax >= usermax``
      * ``only``, meaning the observation's range is strictly inside of the user's specified range: ``dbmin >= usermin AND dbmax <= usermax``
      * ``any``, mean the two ranges overlap at least a little: ``dbmin <= usermax AND dbmax >= usermin``
    * For more details about how ``RANGE`` queries are performed, see the function ``get_range_query`` in ``apps/search/views.py``
  * For displaying metadata:

    * A "single column range" has just a single value, and is displayed as such. Examples:

      * ``Greater Size in Pixels`` = ``512``
      * ``Spectrum Size`` = ``38946``
    * A "dual column range" has two values, and is displayed as two separate pieces of metadata. Examples:

      * ``Wavelength (Min)`` = ``0.1244``, ``Wavelength (Max)`` = ``0.13``
      * ``Observed Ring Radius (Min)`` = ``76782.765``, ``Observed Ring Radius (Max)`` = ``110916.014``
* ``LONG``: A longitude behaves similarly to a "dual column range", except that longitudes can wrap around at 0 and 360 degrees. This means that the "minimum" and "maximum" fields can actually be reversed: A range of 60-to-300 degrees is different from a range of 300-to-60 degrees. Displaying metadata is the same as any other ``RANGE`` field, but searching must take the potential wrap into account. To aid in the searching, the database includes two additional fields for each ``LONG`` field, one which contains the midpoint between the minimum and maximum and the other which includes the span of the range. The math for searching is too long to include here. See the function ``get_longitude_query`` in ``apps/search/views.py`` for details. Examples:

  * ``Observed J2000 Longitude (Min)`` = ``350.444``, ``Observed J2000 Longitude (Max)`` = ``128.054``

Many numerical fields can be interpreted in different units. In these cases, there is a default unit that is stored in the database (for example, ``km``) and the values are converted to/from this default unit as needed. This is also the case for fields that are numerical in nature but whose printed representation is something more complicated, like date/time strings (store as Ephemeris Time) or the various Spacecraft Clock Counts (stored in an internal floating point representation).

The ``obs_*`` Tables
--------------------

General Overview
~~~~~~~~~~~~~~~~

Each "Constraints" section corresponds to one ``obs_*`` table. Each ``obs_*`` table has columns representing a series of metadata fields. Each row of a table represents a single observation identified by a unique OPUS ID.

A row for an OPUS ID does not need to be present in each table, and in fact never is. For example, a Cassini ISS observation will not have a row in the New Horizons LORRI table. However, the ``obs_general`` table, representing the "General Constraints", is guaranteed to have a row for every OPUS ID and as a result is considered the master table. The "PDS Constraints" table ``obs_pds``, "Image Constraints" table ``obs_type_image``, and "Wavelength Constraints" table ``obs_wavelength`` also have a row for every observation. Other tables have rows only for the observations that are relevant:

* "Occultation/Reflectance Profiles Constraints" (``obs_profile``) has rows only for observations that are occultations or reflectance profiles.
* The various Mission Constraints (e.g. "Cassini Mission Constraints", ``obs_mission_cassini``) have rows only for observations that were part of that mission.
* The various Instrument Constraints (e.g. "Cassini ISS Constraints", ``obs_instrument_coiss``) have rows only for observations that were taken by that instrument.
* "Ring Geometry Constraints" (``obs_ring_geometry``) has rows only for observations for which some amount of ring geometry metadata exists.
* The top-level "Surface Geometry Constraints" (``obs_surface_geometry``) and body-specific Surface Geometry Constraints (e.g. "Saturn Surface Geometry Constraints", ``obs_surface_geometry__saturn``) have rows only for observations for which some amount of surface geometry metadata exists for the observation (top-level) or specific body (body-specific). The body-specific categories are not tables of their own: each is one body's rows of ``obs_surface_geometry_target`` (`The Surface Geometry Tables`_).

In addition to the fields corresponding to the metadata available in the UI, each ``obs_*`` table also has columns for internal use:

* ``obs_general_id``: The ``id`` of the observation's row in ``obs_general``, and a foreign key onto it. Joining tables on it puts all of an observation's metadata into one row. Most ``obs_*`` tables have at most one row per observation, so ``obs_general_id`` is their primary key. The exceptions are ``obs_files`` (`The Special obs_files Table`_) and ``obs_surface_geometry_target`` (`The Surface Geometry Tables`_), which can have several rows per observation. ``obs_general`` itself has no ``obs_general_id``.
* ``timestamp``: A date/time field that records when the row was last updated

The columns that identify an observation are stored once, in ``obs_general``: its ``id``, its ``opus_id``, its ``bundle_id`` (the PDS3 volume or PDS4 bundle it came from) and its ``instrument_id``. Another table that needs one of them joins ``obs_general`` on ``obs_general_id``. Storing each value in one place means the copies can never disagree.

``obs_pds`` is the exception: it also has ``opus_id`` and ``bundle_id``, because they are search fields of their own, "OPUS ID" and "Bundle/Volume ID" in the "PDS Constraints" category. Each has a plain key and no foreign key. The import writes the same values into ``obs_pds`` as into ``obs_general``, and its validation step reports any ``obs_pds`` row whose ``bundle_id`` differs from its ``obs_general`` row's.

Here is an example of the schema for the ``obs_general`` table (note this may change slightly over time without this document being updated, so always refer to the actual database for the current schema):

::

    mysql> DESC obs_general;
    +----------------------+-------------------+------+-----+-------------------+
    | Field                | Type              | Null | Key | Default           |
    +----------------------+-------------------+------+-----+-------------------+
    | id                   | int unsigned      | NO   | PRI | NULL              |
    | opus_id              | char(50)          | NO   | MUL | NULL              |
    | bundle_id            | char(75)          | NO   | MUL | NULL              |
    | instrument_id        | smallint unsigned | NO   | MUL | NULL              |
    | mission_id           | smallint unsigned | NO   | MUL | NULL              |
    | inst_host_id         | smallint unsigned | NO   | MUL | NULL              |
    | planet_id            | smallint unsigned | NO   | MUL | NULL              |
    | target_name          | json              | NO   |     | NULL              |
    | target_class         | json              | NO   |     | NULL              |
    | time1                | double            | YES  | MUL | NULL              |
    | time2                | double            | YES  | MUL | NULL              |
    | observation_duration | double            | YES  | MUL | NULL              |
    | quantity             | smallint unsigned | NO   | MUL | NULL              |
    | right_asc1           | double            | YES  | MUL | NULL              |
    | right_asc2           | double            | YES  | MUL | NULL              |
    | right_asc            | double            | YES  | MUL | NULL              |
    | d_right_asc          | double            | YES  |     | NULL              |
    | declination1         | double            | YES  | MUL | NULL              |
    | declination2         | double            | YES  | MUL | NULL              |
    | observation_type     | smallint unsigned | NO   |     | NULL              |
    | preview_images       | json              | NO   |     | NULL              |
    | timestamp            | timestamp         | NO   |     | CURRENT_TIMESTAMP |
    +----------------------+-------------------+------+-----+-------------------+

Besides the keys shown, ``obs_general`` has three keys over two columns each:
``(time1, opus_id)``, which serves the default sort, ``(right_asc, d_right_asc)`` and
``(declination1, declination2)``. ``DESC`` marks only a key's first column, which is why
``d_right_asc`` shows no key. Most columns of the other observation tables have no key of
their own; :ref:`dev_guide_table_schemas` says which columns get one.

``opus_id`` carries a plain key rather than a unique one. Two bundles can produce the same OPUS ID, and an import loads both copies side by side; the import's finalization then keeps the copy with the highest ``id``, which is the copy from the bundle registered later (:ref:`dev_guide_database_schema_import_bundle`), and deletes the others, so a finished database has one row per OPUS ID.

Most of these fields should be self-evident. Some numeric fields have ``1`` and ``2`` versions. These are the minimum and maximum values of the metadata for a "dual column range". ``right_asc`` has two extra fields (``right_asc`` and ``d_right_asc``). These are internal fields that are used to help speed up searching on wrap-around longitudes. Also, ``obs_general`` has a hidden field ``preview_images`` which stores information (in the form of a JSON encoded PdsViewSet) about all of the preview images for each observation so that they can be rapidly retrieved when displaying the Gallery View without needing to join tables together.

``obs_pds`` is a simple example of a secondary table that depends on ``obs_general``:

::

    mysql> DESC obs_pds;
    +-----------------------+--------------+------+-----+-------------------+
    | Field                 | Type         | Null | Key | Default           |
    +-----------------------+--------------+------+-----+-------------------+
    | obs_general_id        | int unsigned | NO   | PRI | NULL              |
    | opus_id               | char(50)     | NO   | MUL | NULL              |
    | bundle_id             | char(75)     | NO   | MUL | NULL              |
    | data_set_id           | char(40)     | YES  | MUL | NULL              |
    | product_id            | char(50)     | YES  | MUL | NULL              |
    | primary_lid           | char(240)    | YES  | MUL | NULL              |
    | product_creation_time | double       | YES  | MUL | NULL              |
    | primary_filespec      | char(240)    | NO   | MUL | NULL              |
    | note                  | char(255)    | YES  | MUL | NULL              |
    | timestamp             | timestamp    | NO   |     | CURRENT_TIMESTAMP |
    +-----------------------+--------------+------+-----+-------------------+

Here is an example of a mission table:

::

    mysql> DESC obs_mission_cassini;
    +-------------------------+-------------------+------+-----+-------------------+
    | Field                   | Type              | Null | Key | Default           |
    +-------------------------+-------------------+------+-----+-------------------+
    | obs_general_id          | int unsigned      | NO   | PRI | NULL              |
    | obs_name                | char(30)          | NO   | MUL | NULL              |
    | rev_no                  | char(3)           | YES  |     | NULL              |
    | rev_no_int              | int               | YES  |     | NULL              |
    | is_prime                | smallint unsigned | NO   |     | NULL              |
    | prime_inst_id           | smallint unsigned | NO   |     | NULL              |
    | spacecraft_clock_count1 | double            | YES  | MUL | NULL              |
    | spacecraft_clock_count2 | double            | YES  | MUL | NULL              |
    | ert1                    | double            | YES  | MUL | NULL              |
    | ert2                    | double            | YES  | MUL | NULL              |
    | cassini_target_code     | smallint unsigned | YES  |     | NULL              |
    | cassini_target_name     | smallint unsigned | YES  | MUL | NULL              |
    | activity_name           | char(9)           | YES  | MUL | NULL              |
    | mission_phase_name      | smallint unsigned | YES  |     | NULL              |
    | sequence_id             | char(4)           | YES  |     | NULL              |
    | timestamp               | timestamp         | NO   |     | CURRENT_TIMESTAMP |
    +-------------------------+-------------------+------+-----+-------------------+

Note that there will be a different number of rows in the ``obs_general`` table and many of the other tables:

::

    mysql> SELECT COUNT(*) FROM obs_general; SELECT COUNT(*) FROM obs_mission_cassini;
    +----------+
    | COUNT(*) |
    +----------+
    |    29689 |
    +----------+

    +----------+
    | COUNT(*) |
    +----------+
    |    18081 |
    +----------+

Tables can be joined together to retrieve all of the metadata for one or more observations:

::

    mysql> SELECT obs_general.planet_id, obs_mission_cassini.obs_name FROM obs_general
               JOIN obs_mission_cassini ON obs_mission_cassini.obs_general_id=obs_general.id
               WHERE obs_general.opus_id='co-iss-n1460960653';
    +-----------+-----------------------------+
    | planet_id | obs_name                    |
    +-----------+-----------------------------+
    |         4 | ISS_C44SA_APPRMOVU002_PRIME |
    +-----------+-----------------------------+

Generally speaking, you can think of the OPUS schema as having only one ``obs`` table and one row per OPUS ID with a huge number of columns encoding all of the possible metadata that could be needed. However, this would be inefficient to store (e.g. why store New Horizons metadata for a Cassini mission? You would just have to fill the columns wth NULLs), so instead we break the information across multiple tables and only populate the rows in the tables as necessary, allowing MySQL's efficient JOIN functionality to combine everything together when needed.

.. _dev_guide_database_schema_mult:

The Encoding of Checkbox IDs and the ``mult`` Tables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"Mult" (aka ``GROUP``) fields are multiple choice options selected from a defined set.
The set of options may be listed in the column's table schema (its ``mult_options``) or
found during the import. Either way, an observation's column stores an integer, the
option's id. Three tables describe the options:

* ``mult_field`` names each **mult field**: the set of values one column can hold.
* ``mult`` holds the values of every field, one row per value.
* ``mult_group`` holds the groups of every field.

Every column whose form type is ``GROUP`` or ``MULTIGROUP`` has a mult field. The
field's qualified name is ``<table>.<column>``, such as ``obs_general.planet_id``. A
``mult_field`` key in the column's schema names the field instead, so that several
columns can share one (:ref:`dev_guide_table_schemas`).

The ``mult_field`` table has these columns:

* ``field_id`` (``smallint unsigned``, the primary key): The field's number. Every
  ``mult`` and ``mult_group`` row of the field carries it.
* ``qualified_name`` (``varchar(100)``, a unique key): The field's qualified name.
* ``pinned`` (``tinyint``): 1 when the column's schema lists the field's values in
  ``mult_options``, 0 otherwise.
* ``last_id`` (``int``, default -1): The highest id handed out in the field, or -1
  before the first. A value new to the field takes the next one, so a field's first
  value is 0. It only goes up: an id whose row finalization deletes is never handed out
  again. With several processes importing at once, an id taken for a value another
  process stored first is left unused, so a field's ids may have gaps; the id-width
  check counts ``last_id``, not the rows.

Bundle registration numbers the fields once in each database. The first registration
gives every mult field of the packaged ``obs_*.json`` schemas an id, 1, 2, 3, ..., in
order of qualified name. A field that a later release adds takes the next id after the highest one in
``mult_field``. A field's id never changes.

The ``mult`` table has these columns:

* ``field_id`` (``smallint unsigned``): The field the value belongs to.
* ``id`` (``smallint unsigned``): What an observation's column holds for this value. Ids
  are numbered within a field: a field's ids start at 0, and a value the import finds
  takes the next id of the field's ``last_id`` counter. A pinned field's ids are the ones
  its ``mult_options`` gives, written by bundle registration; if its list has no absent
  value and an observation needs one, the import adds it under 65535, an id no list may
  give. A stored row keeps its id and its value, so no observation row has to be
  rewritten when a value is renamed. Finalization deletes the values no observation
  holds, and their ids are not handed out again.
* ``value`` (``varchar(100)``): The value as the import read it. The absent value is
  stored as the empty string, never ``NULL``.
* ``label`` (``varchar(100)``): The string to display in the UI.
* ``pin`` (``smallint unsigned``, may be ``NULL``): The value's configured position, or
  ``NULL`` to place the value by what it holds.
* ``disp_rank`` (``smallint unsigned``): The value's position among its field's values,
  counting from 1. Finalization computes it.
* ``display`` (``enum('Y','N')``): ``Y`` to offer the value in the search form, ``N``
  to hide it.
* ``grouping`` (``varchar(100)``, may be ``NULL``): The name of the group the value
  belongs to, or ``NULL`` for none. In the UI, values in the same group are collected
  together under a common, collapsible header.

The primary key is ``(field_id, id)``, and ``(field_id, value)`` is a unique key. The
unique key compares values with the server's collation, which ignores case and accents,
so two values that differ only in case are one value. The largest id a column can hold is
65535; an import that would need a larger id stops with an error naming the field.

The ``mult_group`` table has these columns:

* ``field_id`` (``smallint unsigned``): The field the group belongs to.
* ``grouping`` (``varchar(100)``): The group's name, which the field's ``mult`` rows
  name in their ``grouping``.
* ``group_pin`` (``smallint unsigned``, may be ``NULL``): The group's configured
  position, or ``NULL`` to place the group by name.
* ``group_rank`` (``smallint unsigned``): The group's position among its field's groups,
  counting from 1. Finalization computes it.

The primary key is ``(field_id, grouping)``.

The order of a field's values and groups never depends on the order the import met them.
Finalization ranks every field (:ref:`dev_guide_import_steps_do_finalize_mult`): the
pinned values come first, in order of their pin; then the ordinary values, by number
when every one of them is a number and by label otherwise; then ``Yes`` and ``On``; then
``No`` and ``Off``; and last the absent-value labels ``None``, ``N/A`` and ``NULL``.
:mod:`opus_import.mult_rank` gives the full rules. The pinned groups come first, in order
of their pin, and the others follow by name.

This statement lists the values of the "Planet Name" (``planet_id``) field in the
"General Constraints" category (``obs_general``) in the order the UI shows them:

::

    mysql> SELECT mult.id, mult.value, mult.label FROM mult
               JOIN mult_field ON mult_field.field_id=mult.field_id
               WHERE mult_field.qualified_name='obs_general.planet_id'
               ORDER BY mult.disp_rank;

The value stored in the main ``obs_*`` table is the ``id`` of a ``mult`` row of the
column's field, so reading an observation's label joins ``mult`` on both ``field_id``
and ``id``:

::

    mysql> SELECT obs_general.planet_id, mult.label FROM obs_general
               JOIN mult_field ON mult_field.qualified_name='obs_general.planet_id'
               JOIN mult ON mult.field_id=mult_field.field_id
                         AND mult.id=obs_general.planet_id
               WHERE obs_general.opus_id='co-iss-n1460960653';

The web application joins ``mult`` the same way, once for each mult column a statement
reads, each time under an alias of its own and with the field's id as a parameter
(:func:`opus_app.apps.tools.sql_builder.mult_join`).

Fields like ``Intended Target Name`` that support multiple simultaneous options are stored as JSON lists, and more complicated SQL queries are required to extract the contents of those lists and match them with the ``mult`` rows:

::

    mysql> SELECT obs_general.target_name, obs_general.target_class FROM obs_general WHERE obs_general.opus_id='co-iss-n1460960653';
    +-------------+--------------+
    | target_name | target_class |
    +-------------+--------------+
    | [0]         | [3]          |
    +-------------+--------------+

To better understand how this is used, search for SQL commands containing ``JSON_`` in the ``views.py`` files under ``apps``.

NULL and NOT NULL Columns
~~~~~~~~~~~~~~~~~~~~~~~~~

Some columns (like ``OPUS ID``) must always contain a valid value, while others (like ``Right Ascension``) may have values missing for some observations. For safety and database integrity, we prevent columns that must always be valid from having ``NULL`` values by setting the ``NOT NULL`` column property. Other columns do not have this property set and allow ``NULL`` values. The validate step of the import process identifies columns that permit NULLs and yet have no NULL values and issues the suggestion that those columns be modified to be ``NOT NULL``.

The Use of SQL Indexes
~~~~~~~~~~~~~~~~~~~~~~

SQL indexes are never required, but are useful for performance enhancement. A column that has an index will theoretically be faster to search on and to join with. As such, we try to make every metadata column have an associated index. Unfortunately, MySQL has a limit of 64 indexes for each table, so some tables with a large number of metadata fields (like ``obs_ring_geometry``) are unable to have indexes for all columns. In these cases we remove indexes for the columns that are least likely to be used in searches.

The Surface Geometry Tables
~~~~~~~~~~~~~~~~~~~~~~~~~~~

There are two types of surface geometry tables. The first, called simply ``obs_surface_geometry``, contains the fields shown under "Surface Geometry Constraints" *other than* ``Surface Geometry Target Selector``, which is a magic field. At the time of this writing, the only other field is ``Multiple Target List``. Thus its schema is:

::

    mysql> DESC obs_surface_geometry;
    +----------------+--------------+------+-----+-------------------+
    | Field          | Type         | Null | Key | Default           |
    +----------------+--------------+------+-----+-------------------+
    | obs_general_id | int unsigned | NO   | PRI | NULL              |
    | target_list    | text         | YES  |     | NULL              |
    | timestamp      | timestamp    | NO   |     | CURRENT_TIMESTAMP |
    +----------------+--------------+------+-----+-------------------+

The second, ``obs_surface_geometry_target``, holds every body's surface geometry: one row per observation and body for which geometry information is available. Normally only a few bodies have a row for a given OPUS ID, since only a small number of bodies are in the field of view. Its columns are:

* ``target_name``: The body, as the id of its value in the mult field of the ``Surface Geometry Target Selector`` (``obs_surface_geometry_name.target_name``, `The Encoding of Checkbox IDs and the mult Tables`_). The column's schema entry names that field with its ``mult_field`` key, since the column's own qualified name would name another one.
* ``obs_general_id``: The observation, a foreign key onto ``obs_general.id``.
* The geometry columns, one set for every body.

The primary key is ``(target_name, obs_general_id)``, so one body's rows are next to each other in the table. A plain key on ``obs_general_id`` serves the foreign key, the lookups of one observation's bodies, and the deletion of a bundle's rows. Every other key starts with ``target_name``: a pair of displayed range columns that both carry a key in the template is one key over the body and both columns, and every other keyed column has a key over the body and the column. The keys are listed in the schema file, ``obs_surface_geometry_target.json``.

The web application presents the table as one category per body, named ``obs_surface_geometry__<body>``, and one more category, ``obs_surface_geometry_name``, whose one field is the ``Surface Geometry Target Selector``. A category is data, not a table: ``table_names`` names the table and the body each category reads (`The table_names Table`_), and ``param_info`` and ``partables`` carry the category's rows. A statement reads a body's category as the table under the category's name, keeping to the body's rows:

::

    mysql> SELECT COUNT(*) FROM obs_general
               JOIN obs_surface_geometry_target AS obs_surface_geometry__enceladus
               ON obs_surface_geometry__enceladus.obs_general_id = obs_general.id
               AND obs_surface_geometry__enceladus.target_name =
                   (SELECT target_name FROM table_names
                    WHERE table_name = 'obs_surface_geometry__enceladus')
               WHERE obs_general.opus_id = 'co-iss-n1460961193';
    +----------+
    | COUNT(*) |
    +----------+
    |        1 |
    +----------+

The bodies are the values the table holds, so a body's category exists exactly when some observation has geometry for it. An import that brings a body the database has not held writes the body's mult value and its geometry rows, and its finalization writes the body's ``table_names``, ``param_info`` and ``partables`` rows: no table is created and no code changes.

To remove a bundle, the import deletes the table's rows by joining ``obs_general`` on ``obs_general_id``, as for every other ``obs_*`` table.

The Special ``obs_files`` Table
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The list of product files for any OPUS ID can be exceedingly long, and each file also needs to have associated metadata such as file size, version number, URL, and whether it is marked as checked in the Cart by default. ``obs_files`` holds one row per downloadable file, so an observation has as many rows as it has files. That is why it is a table of its own, rather than columns of ``obs_general``.

* ``obs_general_id`` is a foreign key onto ``obs_general.id``.
* ``file_number`` numbers an observation's files 1, 2, 3, ..., in the order the import writes them. The web application's file list sorts by it last, so the files of one product type and version keep that order.
* The primary key is ``(obs_general_id, file_number)``.
* ``opus_id`` is copied from ``obs_general``, because the web application looks files up by OPUS ID. The one other key, over ``(opus_id, short_name, version_name)``, serves those lookups.

``obs_files`` is joined with ``obs_general`` only to compute details of the Cart and to list the available products on the Detail tab. Its schema is:

::

    mysql> DESC obs_files;
    +-----------------+-------------------+------+-----+-------------------+
    | Field           | Type              | Null | Key | Default           |
    +-----------------+-------------------+------+-----+-------------------+
    | obs_general_id  | int unsigned      | NO   | PRI | NULL              |
    | file_number     | smallint unsigned | NO   | PRI | NULL              |
    | opus_id         | char(50)          | NO   | MUL | NULL              |
    | instrument_id   | char(60)          | NO   |     | NULL              |
    | version_number  | int unsigned      | NO   |     | NULL              |
    | version_name    | char(16)          | NO   |     | NULL              |
    | category        | char(64)          | NO   |     | NULL              |
    | sort_order      | char(9)           | NO   |     | NULL              |
    | short_name      | char(64)          | NO   |     | NULL              |
    | full_name       | char(64)          | NO   |     | NULL              |
    | default_checked | int unsigned      | NO   |     | NULL              |
    | product_order   | int unsigned      | NO   |     | NULL              |
    | logical_path    | text              | NO   |     | NULL              |
    | url             | text              | NO   |     | NULL              |
    | checksum        | char(32)          | NO   |     | NULL              |
    | size            | int unsigned      | NO   |     | NULL              |
    | width           | int unsigned      | YES  |     | NULL              |
    | height          | int unsigned      | YES  |     | NULL              |
    | pds_version     | int unsigned      | NO   |     | NULL              |
    | timestamp       | timestamp         | NO   |     | CURRENT_TIMESTAMP |
    +-----------------+-------------------+------+-----+-------------------+

And as predicted a single OPUS ID is likely to appear more than once:

::

    mysql> SELECT COUNT(*) FROM obs_files WHERE opus_id='co-iss-n1460961193';
    +----------+
    | COUNT(*) |
    +----------+
    |       27 |
    +----------+

    mysql> SELECT short_name, logical_path, size, width, height
                FROM obs_files WHERE opus_id='co-iss-n1460961193' LIMIT 10;
    +--------------+--------------...---------------...-------------------------+---------+-------+--------+
    | short_name   | logical_path ...               ...                         | size    | width | height |
    +--------------+--------------...---------------...-------------------------+---------+-------+--------+
    | coiss_raw    | volumes/COISS...1460960653_1461...G                        | 1077344 |  NULL |   NULL |
    | coiss_raw    | volumes/COISS...1460960653_1461...L                        |    3656 |  NULL |   NULL |
    | coiss_raw    | volumes/COISS.../prefix2.fmt   ...                         |    4753 |  NULL |   NULL |
    | coiss_raw    | volumes/COISS.../tlmtab.fmt    ...                         |   18676 |  NULL |   NULL |
    | coiss_thumb  | volumes/COISS...s/thumbnail/146...0961193_1.IMG.jpeg_small |     560 |    50 |     50 |
    | coiss_medium | volumes/COISS...s/browse/146096...1193_1.IMG.jpeg          |    2894 |   256 |    256 |
    | coiss_full   | volumes/COISS...s/full/14609606...93_1.IMG.png             |  237420 |  1024 |   1024 |
    | coiss_calib  | calibrated/CO...ta/1460960653_1..._CALIB.IMG               | 4202496 |  NULL |   NULL |
    | coiss_calib  | calibrated/CO...ta/1460960653_1..._CALIB.LBL               |    3793 |  NULL |   NULL |
    | coiss_calib  | calibrated/CO.../data/146096065...3_1_CALIB.IMG            | 4202496 |  NULL |   NULL |
    +--------------+--------------...---------------...-------------------------+---------+-------+--------+

The ``param_info`` Table
------------------------

In order for OPUS to properly handle search and metadata display, it needs detailed information about each metadata field. This information is encoded in the ``param_info`` table, which has one row for each displayable metadata field:

::

    mysql> DESC param_info;
    +----------------------+---------------+------+-----+-------------------+
    | Field                | Type          | Null | Key | Default           |
    +----------------------+---------------+------+-----+-------------------+
    | category_name        | varchar(150)  | YES  | MUL | NULL              |
    | name                 | varchar(87)   | YES  | MUL | NULL              |
    | form_type            | varchar(100)  | YES  |     | NULL              |
    | display              | tinyint       | NO   |     | NULL              |
    | display_results      | tinyint       | NO   |     | NULL              |
    | disp_order           | int           | NO   |     | NULL              |
    | label                | varchar(240)  | YES  |     | NULL              |
    | label_results        | varchar(240)  | YES  |     | NULL              |
    | slug                 | varchar(255)  | YES  |     | NULL              |
    | old_slug             | varchar(255)  | YES  |     | NULL              |
    | referred_slug        | varchar(255)  | YES  |     | NULL              |
    | intro                | varchar(1023) | YES  |     | NULL              |
    | tooltip              | varchar(255)  | YES  |     | NULL              |
    | dict_context         | varchar(255)  | YES  |     | NULL              |
    | dict_name            | varchar(255)  | YES  |     | NULL              |
    | dict_context_results | varchar(255)  | YES  |     | NULL              |
    | dict_name_results    | varchar(255)  | YES  |     | NULL              |
    | sub_heading          | varchar(150)  | YES  |     | NULL              |
    | ranges               | json          | YES  |     | NULL              |
    | field_hints1         | varchar(255)  | YES  |     | NULL              |
    | field_hints2         | varchar(255)  | YES  |     | NULL              |
    | id                   | int unsigned  | NO   | PRI | NULL              |
    | timestamp            | timestamp     | YES  |     | CURRENT_TIMESTAMP |
    +----------------------+---------------+------+-----+-------------------+

The fields are:

* ``category_name``: The name of the category containing the metadata field: an ``obs_*`` table, or a surface geometry category (`The Surface Geometry Tables`_), whose fields are the template's with the body's name in their labels and slugs.
* ``name``: The name of the field's column in the category's table.
* ``form_type``: Information about the field so that OPUS knows how to present it for searching and metadata display. The format is ``TYPE[precision][:units]``. The available ``TYPE``\ s are described in the section "Opus Metadata" above.

  * For numeric fields (``RANGE`` and ``LONG``), ``precision`` defines the precision of the value using ``%`` notation:

    * ``%d`` means a decimal value (no fractional part)
    * ``%.nf`` means a floating point value with ``n`` digits to the right of the decimal point.
  * When specified, ``units`` is a descriptor of the encoding of the value, including what the default units are, what other units are available, and how to convert the value between units. The list of available units is given in the ``src/opus_support/units.py`` module. For example, ``form_type="RANGE%.4f:duration"`` means to use the ``duration`` type of units, which has a default unit of ``seconds`` and support for ``microseconds``, ``milliseconds``, ``minutes``, ``hours``, and ``days``. The values are displayed numerically and the precision of the default ``%.3f`` is adjusted based on the factor needed to convert from unit to unit. Another example is ``form_type="RANGE:range_cassini_sclk"``. In this case, the "units" are really a way of indicating the conversion to and from the Cassini Spacecraft Clock Count, which has the format ``dddddddddd.sss`` where ``sss`` can be between 0 and 255 inclusive. There is no need to specify a precision because it is already implied by ``range_cassini_sclk``. Likewise there are no units available other than the default units, since there is no other way to display this metadata.
* ``display``: A boolean value indicating whether this metadata is available for searching in the UI. The primary reason to hide a metadata value from searching is because a min/max pair of ``XXX1`` and ``XXX2`` really only represents a single UI search widget. By convention we mark the ``1`` field as displayed and the ``2`` field hidden.
* ``display_results``: A boolean value indicating whether this metadata is available for viewing. This is set to ``False`` only in rare occasions, such as the hidden ``preview_images`` field which is only for internal use.
* ``disp_order``: An integer indicating how the metadata fields within a given category should be sorted for display. Smaller values will appear higher in the list.
* ``label``: The English name of the metadata field as displayed in the title of a search widget, such as ``Right Ascension``.
* ``label_results``: The English name of the metadata field as displayed as a result, such as ``Right Ascension (Min)`` or ``Right Ascension (Max)``.
* ``slug``: The abbreviation for the field used in the main URL, such as ``rightasc1`` or ``VOYAGERmissionphasename``.
* ``old_slug``: An old abbreviation for the field from a previous version of OPUS. This is supported for backwards compatibility but is not used when creating any new URLs.
* ``referred_slug``: Some fields (such as ``Ring Radius``) appear under multiple categories (``Ring Geometry Constraints`` and ``Occultation/Reflectance Profiles Constraints``). Only one of these is the "real" field and the other simply refers to the real field. In the latter case, the ``referred_slug`` field gives the ``slug`` of the "real" field, and the ``slug`` field is ``NULL``.
* ``intro``: The extended text that appears at the top of a search widget explaining any special circumstances; ``NULL`` if none is provided. For example, for ``Product Creation Time``:

  The Product Creation Time is the time when the actual final data product was created for inclusion in the PDS archive, not the time of the original observation. In most cases, you will want to use the Observation Time under General Constraints instead.

* ``tooltip``: This field is not used.
* ``dict_context`` and ``dict_name``: The "context" and "name" used to look up the tooltip for this field in the dictionary when used in a search widget. A ``XXX2`` field will have ``NULL`` for these columns. For example, for ``right_asc1`` we have ``dict_context="OPUS_GENERAL"`` and ``dict_name="RIGHT_ASCENSION"`` while for ``right_asc2`` both fields are ``NULL.``
* ``dict_context_results`` and ``dict_name_results``: The "context" and "name" used to look up the tooltip for this field in the dictionary when used to display metadata. For example, for ``right_asc1`` we have ``dict_context_results="OPUS_GENERAL"`` and ``dict_name_results="RIGHT_ASCENSION_MIN"`` while for ``right_asc2`` we have ``dict_context_results="OPUS_GENERAL"`` and ``dict_name_results="RIGHT_ASCENSION_MAX"``.
* ``sub_heading``: The sub-category to use when the category is further divided. For example, in the ``Ring Geometry Constraints`` category each field is under a sub-heading such as ``Radius & Longitude`` or ``Edge-On Viewing Geometry``.
* ``ranges``: A JSON field giving details of pre-programmed ranges that can be selected during searching, if any. For example, the ``Wavelength`` field has a number of pre-programmed options such as "Red" or "Violet".
* ``field_hints1`` and ``field_hints2``: When ``ranges`` is specified, the grey text to display in the search widget to give a hint as to what can be typed. For example, for the ``Wavelength`` field this is "Wavelength or Color".
* ``id``: A unique ID.
* ``timestamp``: The date and time this row was last modified.

The ``table_names`` Table
-------------------------

The ``table_names`` table contains the mapping between the ``obs_*`` SQL table name and the English used to describe the category in the UI:

::

    mysql> DESC table_names;
    +----------------+-------------------+------+-----+-------------------+
    | Field          | Type              | Null | Key | Default           |
    +----------------+-------------------+------+-----+-------------------+
    | table_name     | char(60)          | NO   | MUL | NULL              |
    | label          | char(60)          | NO   |     | NULL              |
    | display        | char(1)           | NO   |     | Y                 |
    | disp_order     | int               | NO   |     | NULL              |
    | physical_table | varchar(60)       | YES  |     | NULL              |
    | target_name    | smallint unsigned | YES  |     | NULL              |
    | id             | int unsigned      | NO   | PRI | NULL              |
    | timestamp      | timestamp         | YES  |     | CURRENT_TIMESTAMP |
    +----------------+-------------------+------+-----+-------------------+

The fields are:

* ``table_name``: The name of the category: an SQL ``obs_*`` table, or a surface geometry category (`The Surface Geometry Tables`_).
* ``label``: The English label, such as ``Occultation/Reflectance Profiles Constraints``.
* ``display``: A flag ``Y`` or ``N`` indicating whether to display this table. Currently this is always ``Y``.
* ``disp_order``: An integer indicating how the table should be sorted when displaying them.
* ``physical_table``: The table a category's rows are in when the category is not a table of its own, ``obs_surface_geometry_target`` for every surface geometry category; ``NULL`` for a table.
* ``target_name``: For a surface geometry body's category, the body's id in the selector's mult field, which the rows of the category hold in ``obs_surface_geometry_target.target_name``; ``NULL`` for every other category, the selector ``obs_surface_geometry_name`` among them, which reads every row of the table.
* ``id``: A unique ID.
* ``timestamp``: The date and time this row was last modified.

The ``partables`` Table
-----------------------

The ``partables`` table is used to instruct OPUS on how to figure out when a particular search category should be displayed. In general a category is displayed when all of the current search results have a particular property, e.g. the ``Cassini Mission Constraints`` table is displayed when all of the search results have the ``Mission`` field equal to ``Cassini``.

::

    mysql> DESC partables;
    +-------------+--------------+------+-----+-------------------+
    | Field       | Type         | Null | Key | Default           |
    +-------------+--------------+------+-----+-------------------+
    | trigger_tab | char(200)    | YES  | MUL | NULL              |
    | trigger_col | char(200)    | YES  |     | NULL              |
    | trigger_val | char(60)     | YES  |     | NULL              |
    | partable    | char(200)    | YES  |     | NULL              |
    | id          | int unsigned | NO   | PRI | NULL              |
    | timestamp   | timestamp    | YES  |     | CURRENT_TIMESTAMP |
    +-------------+--------------+------+-----+-------------------+

* ``trigger_tab``: The table to look at for a particular value.
* ``trigger_col``: The column in that table to look at for a particular value.
* ``trigger_val``: The value to look for.
* ``partable``: When that value is found in that column in that table for all search results, trigger the display of this table.
* ``id``: A unique ID.
* ``timestamp``: The date and time this row was last modified.

For example:

::

    mysql> SELECT trigger_tab, trigger_col, trigger_val, partable FROM partables
               WHERE partable='obs_mission_cassini' OR partable='obs_instrument_nhlorri';
    +-------------+---------------+-------------+------------------------+
    | trigger_tab | trigger_col   | trigger_val | partable               |
    +-------------+---------------+-------------+------------------------+
    | obs_general | mission_id    | 0           | obs_mission_cassini    |
    | obs_general | instrument_id | 15          | obs_instrument_nhlorri |
    | obs_general | inst_host_id  | 0           | obs_mission_cassini    |
    +-------------+---------------+-------------+------------------------+

The ``obs_mission_cassini`` table will be displayed whenever all of the search results have a ``mission_id`` of Cassini (the mult value ``0`` for that column) or a ``inst_host_id`` of Cassini (the mult value ``0`` for that column), while the ``obs_instrument_nhlorri`` table will be displayed whenever all of the search results have an ``instrument_id`` of ``NHLORRI`` (the mult value ``15`` for that column).

The ``cart`` Table
------------------

The ``cart`` table records the current Cart contents for all users. As long as the Django session is not changed and the database is not reinitialized, users have a cart that persists across browser sessions. Each row in the table represents one OPUS ID stored in the cart for a particular user. Thus the cart for one user is spread across as many rows as necessary.

::

    mysql> DESC cart;
    +----------------+--------------+------+-----+-------------------+
    | Field          | Type         | Null | Key | Default           |
    +----------------+--------------+------+-----+-------------------+
    | session_id     | char(80)     | NO   | MUL | NULL              |
    | obs_general_id | int unsigned | NO   | MUL | NULL              |
    | opus_id        | char(50)     | NO   | MUL | NULL              |
    | recycled       | tinyint      | NO   |     | NULL              |
    | id             | int unsigned | NO   | PRI | NULL              |
    | timestamp      | timestamp    | YES  |     | CURRENT_TIMESTAMP |
    +----------------+--------------+------+-----+-------------------+

The fields are:

* ``session_id``: The Django session ID.
* ``obs_general_id``: The ``obs_general`` unique ID of the observation in the cart. It is a foreign key that cascades on delete, so deleting an observation -- when its bundle is imported again, deleted with ``--delete-bundles``, or settled by finalization's duplicate step -- deletes the cart rows that hold it.
* ``opus_id``: The OPUS ID of the observation in the cart (which could also be found by joining the ``obs_general_id`` with the ``obs_general`` table).
* ``recycled``: A boolean flag saying whether or not this observation is in the recycle bin.
* ``id``: A unique ID.
* ``timestamp``: The date and time this row was last modified.

The ``user_searches`` and ``search_results`` Tables
---------------------------------------------------

OPUS stores every search a user makes, so that a later request for the same search reads
the stored results instead of running the search again:

* ``user_searches`` has one row for each distinct search. The row's ``id`` is the
  search's number.
* ``search_results`` holds each search's results: the observations it matched, in sort
  order.

When a request makes a search, OPUS looks for it in ``user_searches``. If the search is
not there, OPUS adds a row for it. If the search's results are not stored yet, the request
writes them into ``search_results``; every later request for the search reads them.

The import creates both tables from their schema files, and empties them when it resets
the search tables (``opus_import --reset-search-tables``). Between imports,
``opus_manage prune`` removes the searches that have gone longest without use
(:ref:`user_guide_deployment_prune`).

::

    mysql> DESC user_searches;
    +------------------+--------------+------+-----+---------+
    | Field            | Type         | Null | Key | Default |
    +------------------+--------------+------+-----+---------+
    | id               | int unsigned | NO   | PRI | NULL    |
    | search_hash      | binary(32)   | NO   | UNI | NULL    |
    | result_count     | int unsigned | YES  |     | NULL    |
    | results_built_at | datetime     | YES  |     | NULL    |
    | last_used_at     | datetime     | NO   |     | NULL    |
    +------------------+--------------+------+-----+---------+

    mysql> DESC search_results;
    +----------------+--------------+------+-----+---------+
    | Field          | Type         | Null | Key | Default |
    +----------------+--------------+------+-----+---------+
    | search_id      | int unsigned | NO   | PRI | NULL    |
    | sort_order     | int unsigned | NO   | PRI | NULL    |
    | obs_general_id | int unsigned | NO   |     | NULL    |
    +----------------+--------------+------+-----+---------+

The fields of ``user_searches`` are:

* ``id``: The search's number. The search's rows in ``search_results`` carry it.
* ``search_hash``: What identifies the search: the SHA-256 hash, stored as 32 bytes, of
  a JSON list of the search's selections, qtypes, units and sort order; each of the last
  three is ``null`` when the search has none. It is a unique key, so two searches are the
  same search only if all four match.
* ``result_count``: How many results the search has. ``NULL`` until its results are
  stored.
* ``results_built_at``: When the search's results were stored. ``NULL`` until they are;
  this is how OPUS tells whether a search's results exist yet.
* ``last_used_at``: When the search was added or last used, updated at most once a day.
  ``opus_manage prune`` removes the searches with the oldest ``last_used_at`` first.

Both times are in UTC.

Each row of ``search_results`` is one observation in one search's results. Its fields are:

* ``search_id``: The search's number, its ``user_searches`` ``id``.
* ``sort_order``: The observation's position in the search's sorted order: 1, 2, 3, ...
  with no gaps.
* ``obs_general_id``: The observation's ``obs_general`` ``id``.

It has two keys:

* The primary key, ``(search_id, sort_order)``, keeps each search's results together and
  in order, so a page of results is one range of the key.
* The unique key, ``(search_id, obs_general_id)``, finds an observation in one search's
  results. The queries that join the ``obs_*`` tables to a search's results use it.

Neither table has a foreign key. The code that removes a search removes its rows of
``search_results`` too.

A search's results are written by one ``INSERT INTO search_results ... SELECT``
statement, which runs the search and numbers its rows in sort order with
``ROW_NUMBER()``. The same transaction locks the search's ``user_searches`` row
(``SELECT ... FOR UPDATE``) and fills in ``result_count``, ``results_built_at`` and
``last_used_at``. Two requests that make the same new search at once therefore cannot
both write its results: the second waits for the lock, then finds the results stored.
:ref:`dev_guide_webapp_search_flow` describes this step by step.

The ``contexts`` and ``definitions`` Tables
-------------------------------------------

OPUS supports a flexible database-based dictionary. It is used to supply tooltips for OPUS metadata fields. Each entry in the dictionary consists of a field name (e.g. ``PLANET_NAME``) and a context (e.g. ``OPUS_GENERAL_SEARCH``). It is possible for a field name to appear under multiple contexts. For example, a field such as ``EXPOSURE_TIME`` might mean something different in the ``COISS`` and ``COCIRS`` contexts. There are two database tables that support the dictionary.

The ``contexts`` table has the following schema:

::

    mysql> DESC contexts;
    +-------------+--------------+------+-----+-------------------+
    | Field       | Type         | Null | Key | Default           |
    +-------------+--------------+------+-----+-------------------+
    | name        | char(50)     | NO   | UNI | NULL              |
    | description | char(100)    | NO   |     | NULL              |
    | parent      | char(25)     | NO   |     | NULL              |
    | timestamp   | timestamp    | YES  |     | CURRENT_TIMESTAMP |
    | id          | int unsigned | NO   | PRI | NULL              |
    +-------------+--------------+------+-----+-------------------+

Contexts are arranged in a tree, such that each context has a single parent. In the eventual website interface, a term will be displayed in multiple contexts if appropriate. The top-level context is the NASA PDS Planetary Science Data Dictionary, ``PSDD``. Under this are the top-level OPUS Constraints categories: ``OPUS_GENERAL``, ``OPUS_PDS``, ``OPUS_TYPE_IMAGE``, ``OPUS_WAVELENGTH``, etc., as well as the missions like ``CASSINI``. Under each mission are the instruments: ``CASSINI`` has ``COCIRS``, ``COISS``, ``COUVIS``, etc.

The fields are:

* ``name``: The internal name of the context (e.g. ``CASSINI``).
* ``description``: The pretty English name of the context (e.g. ``Cassini Mission``).
* ``parent``: The internal name of the parent context.
* ``timestamp``: The date and time this row was last modified.
* ``id``: A unique ID.

The ``definitions`` table has the following schema:

::

    mysql> DESC definitions;
    +------------+--------------+------+-----+-------------------+
    | Field      | Type         | Null | Key | Default           |
    +------------+--------------+------+-----+-------------------+
    | term       | char(255)    | NO   | MUL | NULL              |
    | context    | char(50)     | NO   | MUL | NULL              |
    | definition | text         | NO   |     | NULL              |
    | timestamp  | timestamp    | YES  |     | CURRENT_TIMESTAMP |
    | id         | int unsigned | NO   | PRI | NULL              |
    +------------+--------------+------+-----+-------------------+

The fields are:

* ``term``: The internal name of the term (e.g. ``PLANET_NAME``).
* ``context``: The associated internal name of the context.
* ``definition``: The full free-form text definition.
* ``timestamp``: The date and time this row was last modified.
* ``id``: A unique ID.

.. _dev_guide_database_schema_version:

The ``schema_version`` Table
----------------------------

The ``schema_version`` table records which generation of the table schemas imported the database, and whether the import is finished. It holds one row.

::

    mysql> DESC schema_version;
    +---------+---------------------------+------+-----+---------+
    | Field   | Type                      | Null | Key | Default |
    +---------+---------------------------+------+-----+---------+
    | version | int unsigned              | NO   | PRI | NULL    |
    | state   | enum('ready','appending') | NO   |     | NULL    |
    +---------+---------------------------+------+-----+---------+

The fields are:

* ``version``: The :data:`~opus_import.schema_version.SCHEMA_VERSION` of the release whose import created the tables. A release that changes a table schema in a way an existing database does not have raises it, and is deployed with a fresh import.
* ``state``: ``ready`` once the database is finished; ``appending`` while an append to it is writing.

The import's last step, ``--write-schema-version`` (:ref:`dev_guide_import_steps_do_schema_version`), creates the table and writes the row. It is the only writer of ``ready``, it never changes a ``version`` the row already holds, and it refuses to write ``ready`` while any bundle in ``import_bundle`` is not ``done``. An append, and ``--delete-bundles`` on a finished database, set ``state`` to ``appending`` before the first write (:ref:`dev_guide_import_write_paths`). ``--scorched-earth`` drops the table before any other.

Two things read it, and both require the release's own version in the ``ready`` state:

* the web application, as it loads (:mod:`opus_app.schema_guard`, called from :mod:`opus_app.wsgi`). Any other row, or none, makes every request answer 503 with a message naming the remedy, and each refused request checks again, so a worker serves the database as soon as it is finished, without a reload. Once the check passes the worker does not make it again, so a worker already serving a database goes on serving it if the row later changes: an append or a deletion is made only to a database nothing is serving. The check is in the WSGI entry point and not in the settings, so management commands, ``inspectdb`` among them, work against any database;
* both deploy scripts, before they write anything (:ref:`user_guide_deployment_schema_version`).

.. _dev_guide_database_schema_import_bundle:

The ``import_bundle`` Table
---------------------------

The ``import_bundle`` table is the bundle registry: the import's record of each bundle registered for import, the range its observation ids come from, and how far it got (:ref:`dev_guide_import_steps_registry`). Its states are also the work queue several import processes draw from. The web application never reads it.

::

    mysql> DESC import_bundle;
    +---------------+---------------------------------------------+------+-----+---------+----------------+
    | Field         | Type                                        | Null | Key | Default | Extra          |
    +---------------+---------------------------------------------+------+-----+---------+----------------+
    | bundle_number | smallint unsigned                           | NO   | PRI | NULL    | auto_increment |
    | bundle_id     | varchar(75)                                 | NO   | UNI | NULL    |                |
    | size_estimate | bigint unsigned                             | NO   |     | NULL    |                |
    | first_id      | int unsigned                                | NO   |     | NULL    |                |
    | id_capacity   | int unsigned                                | NO   |     | NULL    |                |
    | state         | enum('pending','importing','done','failed') | NO   | MUL | pending |                |
    | started_at    | datetime                                    | YES  |     | NULL    |                |
    | finished_at   | datetime                                    | YES  |     | NULL    |                |
    | process_id    | int unsigned                                | YES  |     | NULL    |                |
    | rows_done     | bigint unsigned                             | NO   |     | 0       |                |
    | losses        | tinyint unsigned                            | NO   |     | 0       |                |
    +---------------+---------------------------------------------+------+-----+---------+----------------+

The fields are:

* ``bundle_number``: The bundle's place in registration order, which is the import order. A bundle keeps its number when it is imported again.
* ``bundle_id``: The bundle, such as ``COISS_2002``. A bundle OPUS deliberately skips is never registered.
* ``size_estimate``: The rows the bundle's primary index labels declared when it was registered.
* ``first_id``: The ``obs_general.id`` of the bundle's first observation. A bundle's range starts where the range of the bundle registered before it ends, so the ranges ascend in ``bundle_number`` order and the copy of a shared OPUS ID that finalization keeps, the one with the highest ``id``, is the one from the bundle registered later.
* ``id_capacity``: How many ids, from ``first_id``, the bundle's observations may take: a hundred for each row of ``size_estimate``. A bundle that needs more fails its import, naming its capacity.
* ``state``: ``pending`` once the bundle is registered and before an import takes it; ``importing`` while the bundle is deleted and loaded; ``done`` once it is imported without logging an error, or under ``--ignore-errors``; ``failed`` when its import failed or logged an error.
* ``started_at`` and ``finished_at``: When the bundle's latest import began and ended, in UTC; ``NULL`` before the first, and ``finished_at`` while one is running.
* ``process_id``: The ``import_process`` row of the importer that claimed the bundle, set with ``importing``, and kept on a ``failed`` bundle so its importer's log can be found; ``NULL`` for a bundle imported by a plain ``opus_import``, and once the bundle returns to ``pending``.
* ``rows_done``: The ``obs_general`` rows the bundle's latest import has committed, advanced in each chunk's transaction.
* ``losses``: How many importers died holding the bundle. Its second loss marks it ``failed``.

The key on ``(state, size_estimate, bundle_number)`` is what a claim reads: scanned from its highest entry, it gives the largest ``pending`` bundle in one index entry, so a claim locks only the row it takes.

Every invocation that registers or imports bundles creates the table when the schema lacks it, on a fresh import and an append alike, and registers its bundles before the first one starts. ``--finalize`` refuses to run, and ``--write-schema-version`` refuses to write ``ready``, while any row is not ``done``. ``--delete-bundles`` deletes a bundle's row with its observations, and ``--scorched-earth`` drops the table.

.. _dev_guide_database_schema_import_process:

The ``import_process`` Table
----------------------------

The ``import_process`` table records every importer, an ``opus_import --join`` process drawing bundles from the queue (:ref:`dev_guide_import_full_run`). Only the import reads it; the web application never does, and ``SCHEMA_VERSION`` does not cover it, since an importer creates it when the schema lacks it.

::

    mysql> DESC import_process;
    +-------------+---------------------------------+------+-----+---------+----------------+
    | Field       | Type                            | Null | Key | Default | Extra          |
    +-------------+---------------------------------+------+-----+---------+----------------+
    | process_id  | int unsigned                    | NO   | PRI | NULL    | auto_increment |
    | host        | varchar(255)                    | NO   |     | NULL    |                |
    | pid         | int unsigned                    | NO   |     | NULL    |                |
    | log_path    | varchar(1024)                   | NO   |     | NULL    |                |
    | started_at  | datetime                        | NO   |     | NULL    |                |
    | progress_at | datetime                        | NO   |     | NULL    |                |
    | state       | enum('running','exited','lost') | NO   |     | NULL    |                |
    +-------------+---------------------------------+------+-----+---------+----------------+

The fields are:

* ``process_id``: The importer, as ``import_bundle.process_id`` names it.
* ``host`` and ``pid``: The computer the importer runs on, and its process id there.
* ``log_path``: The importer's information log, on its computer.
* ``started_at`` and ``progress_at``: When the importer started, and when it last committed a chunk of rows, in UTC.
* ``state``: ``running`` from its start; ``exited`` once it has exited; ``lost`` once a coordinator found its lock free while the row was ``running``.

Whether an importer is alive is not in the table: it is whether the server-wide named lock :func:`opus_import.import_processes.importer_lock_name` names is held, which the server frees when the importer's lock connection closes. ``--scorched-earth`` drops the table.
