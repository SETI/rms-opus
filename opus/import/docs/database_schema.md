This document describes the database schema for OPUS 3.x.

OPUS uses MySQL 8.x. MySQL is a relational database based on SQL (Structured Query Language). A relational database is one where data is stored in a collection of *tables*, each of which has pre-defined *columns* with specified data types. The actual data is stored in each table in *rows*, much like in a spreadsheet, and each *row* contains an instance of each *column*. Columns that do not have data available may be marked by storing the special value `NULL`, if the column's properties are set to permit it. The relational part comes when tables cross-reference each other. For example, a column in one table could be used to select rows from another table. Such an operation is called a *join*, and many tables can be joined together. The joining of tables is the fundamental concept of relational databases. To fully understand the OPUS database it is strongly recommended that you become familiar with relational databases and the SQL language before continuing.

OPUS stores metadata in a series of `obs_*` tables. Each `obs_*` table generally corresponds to one of the "Constraints" menus visible in the browser UI. For example, `obs_general` corresponds to "General Constraints" and `obs_wavelength` corresponds to "Wavelength Constraints". This one-to-one correspondence between tables and UI metadata categories is an integral part of the design of OPUS, and if a metadata field is moved to a different "Constraints" category, the table design must also be changed.

Each row in an `obs_*` table represents a single observation represented by a unique OPUS ID, and each column generally represents one user-visible metadata field (although there are additional hidden fields as discussed below).

In addition to metadata, OPUS stores other information that helps it operate in tables. This includes information about checkbox fields, the contents of users' Carts, the dictionary of terms and definitions (including tooltips), information about the metadata fields themselves (this is metadata metadata!), and information about the metadata categories.

#
# OPUS Metadata

It's important to understand that OPUS has its own concept of metadata types independent of the SQL data types. For example, an integer in the database could represent a numeric value (like the pixel size of an image) or an index into a "mult table" (like the selection of a particular mission from the available options) or a reference to an entry in another table or just a unique ID in the current table. As such, there needs to be a place to store "metadata about the metadata", and this is the separate `param_info` table, which will be discussed later. We will use the term "field type" when discussing OPUS's concept of metadata types, and "SQL data type" when discussing the attributes of a SQL column.

OPUS understands the following high-level field types:

- `STRING`: A single arbitrary string. It is represented in the database with a SQL `charNNN` data type (a string with a maximum length). When searching, the string can be matched exactly or by various types of pattern matching (e.g. `begins`, `ends`, `contains`, `excludes`, or `regex`). When displaying metadata, the string is simply shown as-is. Examples:
    - `Volume ID` = `"HSTU0_5392"`
    - `Primary File Spec` = `"HSTU0_5392/DATA/VISIT_03/U2930301T.LBL"`
    - `PI Name` = `"Spencer, John R."`
- `GROUP`: A selection in a list of possible options. `GROUP` is also referred to as a "mult", meaning multiple choice. In the database, a `GROUP` is stored as a single integer (using the SQL `int unsigned` data type), which is an index into another special "mult table", which will be described below. When searching, the user can select one or more checkboxes from the group. Any observation that matches one of the selected checkboxes will be given as a result. When displaying metadata, the integer is converted to a string by referencing the "mult table" and the string is shown. Examples:
    - `Mission` = `Galileo` (stored in the database as the value `1`)
    - `Saturn Orbit Number (By Checkbox)` = `044` (stored in the database as the value `23`)
    - `Body Occultation Flag` = `N/A` (stored in the database as the value `0`)
- `MULTIGROUP`: Multiple selections in a list of possible options. This is similar to a `GROUP`, except that instead of having a single option selected represented as an integer, the database contains a JSON list (using the SQL `JSON` data type) containing, potentially, multiple integers. This type is used when a single observation can apply to more than one entry in the group, such as `Intended Target Name` (where one observation can be intended for multiple targets in PDS4) or `Nominal Target Class` (where multiple intended targets results in multiple target classes). Searching by the user is performed the same way as with a `GROUP`, except that the matching is done against any of the entries in the list, not just a single integer. If any of the entries match, the observation is returned as a search result. When displaying metadata, each entry in the list is converted to a string by referencing the "mult table" and then they are joined together by commas. The functionality provided by `MULTIGROUP` is a strict superset of `GROUP` and technically we could remove the `GROUP` type entirely. However, the performance of searching and retrieving the values from a `MULTIGROUP` is roughly 30% slower than a `GROUP` due to the need to handle the arbitrary length list of values, and thus we keep both types around for performance. Examples:
    - `Intended Target Name` = `Jupiter,Amalthea`
    - `Nominal Target Class` = `Planet,Regular Satellite`
- `RANGE`: Either a single integer or floating point value (a "single column range", if the observation only has a single relevant value) or a pair of integers or floating point values (a "dual-column range" if the observation has a range of values represented by minimum and maximum). The value(s) are stored in the database using the appropriate SQL data type, such as `tinyint`, `smallint`, `mediumint`, `int`, `bigint`, `float`, or `double`. In either case the UI provides the user with a pair of minimum/maximum search boxes.
    - For searching:
        - For a single value, when a search is performed, the database is queried for the simple inequality:
            - If only the minimum value is being searched on: `usermin <= dbvalue`
            - If only the maximum value is being searched on: `dbvalue <= usermax`
            - If both are being searched on: `usermin <= dbvalue <= usermax`
        - For a pair of values, searching is more complicated because you are comparing two overlapping ranges. There are three types of comparisons available:
            - `all`, meaning the observation's range covers all of the user's specified range (and maybe more): `dbmin <= usermin AND dbmax >= usermax`
            - `only`, meaning the observation's range is strictly inside of the user's specified range: `dbmin >= usermin AND dbmax <= usermax`
            - `any`, mean the two ranges overlap at least a little: `dbmin <= usermax AND dbmax >= usermin`
        - For more details about how `RANGE` queries are performed, see the function `get_range_query` in `apps/search/views.py`
    - For displaying metadata:
        - A "single column range" has just a single value, and is displayed as such. Examples:
            - `Greater Size in Pixels` = `512`
            - `Spectrum Size` = `38946`
        - A "dual column range" has two values, and is displayed as two separate pieces of metadata. Examples:
            - `Wavelength (Min)` = `0.1244`, `Wavelength (Max)` = `0.13`
            - `Observed Ring Radius (Min)` = `76782.765`, `Observed Ring Radius (Max)` = `110916.014`
- `LONG`: A longitude behaves similarly to a "dual column range", except that longitudes can wrap around at 0 and 360 degrees. This means that the "minimum" and "maximum" fields can actually be reversed: A range of 60-to-300 degrees is different from a range of 300-to-60 degrees. Displaying metadata is the same as any other `RANGE` field, but searching must take the potential wrap into account. To aid in the searching, the database includes two additional fields for each `LONG` field, one which contains the midpoint between the minimum and maximum and the other which includes the span of the range. The math for searching is too long to include here. See the function `get_longitude_query` in `apps/search/views.py` for details. Examples:
    - `Observed J2000 Longitude (Min)` = `350.444`, `Observed J2000 Longitude (Max)` = `128.054`

Many numerical fields can be interpreted in different units. In these cases, there is a default unit that is stored in the database (for example, `km`) and the values are converted to/from this default unit as needed. This is also the case for fields that are numerical in nature but whose printed representation is something more complicated, like date/time strings (store as Ephemeris Time) or the various Spacecraft Clock Counts (stored in an internal floating point representation).

#
# The `obs_*` Tables

## General Overview

Each "Constraints" section corresponds to one `obs_*` table. Each `obs_*` table has columns representing a series of metadata fields. Each row of a table represents a single observation identified by a unique OPUS ID.

A row for an OPUS ID does not need to be present in each table, and in fact never is. For example, a Cassini ISS observation will not have a row in the New Horizons LORRI table. However, the `obs_general` table, representing the "General Constraints", is guaranteed to have a row for every OPUS ID and as a result is considered the master table. The "PDS Constraints" table `obs_pds`, "Image Constraints" table `obs_type_image`, and "Wavelength Constraints" table `obs_wavelength` also have a row for every observation. Other tables have rows only for the observations that are relevant:

- "Occultation/Reflectance Profiles Constraints" (`obs_profile`) has rows only for observations that are occultations or reflectance profiles.
- The various Mission Constraints (e.g. "Cassini Mission Constraints", `obs_mission_cassini`) have rows only for observations that were part of that mission.
- The various Instrument Constraints (e.g. "Cassini ISS Constraints", `obs_instrument_coiss`) have rows only for observations that were taken by that instrument.
- "Ring Geometry Constraints" (`obs_ring_geometry`) has rows only for observations for which some amount of ring geometry metadata exists.
- The top-level "Surface Geometry Constraints" (`obs_surface_geometry`) and body-specific Surface Geometry Constraints (e.g. "Saturn Surface Geometry Constraints", `obs_surface_geometry__saturn`) have rows only for observations for which some amount of surface geometry metadata exists for the observation (top-level) or specific body (body-specific).

In addition to the fields corresponding to the metadata available in the UI, each `obs_*` table also has several columns for internal use:

- `obs_general_id`: An integer corresponding to the `id` field in the `obs_general` table. This field is used to join multiple tables together so that a single joined row has all of the metadata from all of the relevant tables. This field does not exist in the `obs_general` table itself.
- `opus_id`: The OPUS ID of the row
- `bundle_id`: The PDS3 Volume ID of the row
- `instrument_id`: The PDS3 Instrument ID of the row
- `id`: An integer that can be used to quickly index a row in the table
- `timestamp`: A date/time field that records when the row was last updated

With the exception of the `id` field in the `obs_general` table and the `obs_general_id` field in all other `obs_*` tables, these extra fields are not used during OPUS's execution. In fact, the fields `opus_id`, `bundle_id`, and `instrument_id` can easily be retrieved simply by joining a table with `obs_general`, which under the concept of "database normalization" is the correct and safest thing to do. Nevertheless, we have this redundant data in each table because it makes the import process easier (e.g., one can readily delete all metadata from a particular instrument without needing to join tables together), and because it helps in manual debugging and/or maintenance.

Here is an example of the schema for the `obs_general` table (note this may change slightly over time without this document being updated, so always refer to the actual database for the current schema):

    mysql> DESC obs_general;
    +----------------------+--------------+------+-----+-------------------+
    | Field                | Type         | Null | Key | Default           |
    +----------------------+--------------+------+-----+-------------------+
    | id                   | int unsigned | NO   | PRI | NULL              |
    | opus_id              | char(50)     | NO   | UNI | NULL              |
    | bundle_id            | char(11)     | NO   | MUL | NULL              |
    | instrument_id        | int unsigned | NO   | MUL | NULL              |
    | mission_id           | int unsigned | NO   | MUL | NULL              |
    | inst_host_id         | int unsigned | NO   | MUL | NULL              |
    | planet_id            | int unsigned | NO   | MUL | NULL              |
    | target_name          | json         | NO   |     | NULL              |
    | target_class         | json         | NO   |     | NULL              |
    | time1                | double       | YES  | MUL | NULL              |
    | time2                | double       | YES  | MUL | NULL              |
    | observation_duration | double       | YES  | MUL | NULL              |
    | quantity             | int unsigned | NO   | MUL | NULL              |
    | right_asc1           | double       | YES  | MUL | NULL              |
    | right_asc2           | double       | YES  | MUL | NULL              |
    | right_asc            | double       | YES  | MUL | NULL              |
    | d_right_asc          | double       | YES  | MUL | NULL              |
    | declination1         | double       | YES  | MUL | NULL              |
    | declination2         | double       | YES  | MUL | NULL              |
    | observation_type     | int unsigned | NO   |     | NULL              |
    | ring_obs_id          | char(40)     | YES  | MUL | NULL              |
    | primary_filespec     | char(240)    | NO   | MUL | NULL              |
    | preview_images       | json         | NO   |     | NULL              |
    | timestamp            | timestamp    | NO   |     | CURRENT_TIMESTAMP |
    +----------------------+--------------+------+-----+-------------------+

Most of these fields should be self-evident. Some numeric fields have `1` and `2` versions. These are the minimum and maximum values of the metadata for a "dual column range". `right_asc` has two extra fields (`right_asc` and `d_right_asc`). These are internal fields that are used to help speed up searching on wrap-around longitudes. Also, `obs_general` has a hidden field `preview_images` which stores information (in the form of a JSON encoded PdsViewSet) about all of the preview images for each observation so that they can be rapidly retrieved when displaying the Gallery View without needing to join tables together.

`obs_pds` is a simple example of a secondary table that depends on `obs_general`:

    mysql> DESC obs_pds;
    +-----------------------+--------------+------+-----+-------------------+
    | Field                 | Type         | Null | Key | Default           |
    +-----------------------+--------------+------+-----+-------------------+
    | obs_general_id        | int unsigned | NO   | MUL | NULL              |
    | opus_id               | char(50)     | NO   | MUL | NULL              |
    | bundle_id             | char(11)     | NO   | MUL | NULL              |
    | instrument_id         | char(12)     | NO   | MUL | NULL              |
    | data_set_id           | char(40)     | NO   | MUL | NULL              |
    | product_id            | char(50)     | NO   | MUL | NULL              |
    | product_creation_time | double       | YES  | MUL | NULL              |
    | primary_filespec      | char(240)    | NO   | MUL | NULL              |
    | note                  | char(255)    | YES  | MUL | NULL              |
    | id                    | int unsigned | NO   | PRI | NULL              |
    | timestamp             | timestamp    | NO   |     | CURRENT_TIMESTAMP |
    +-----------------------+--------------+------+-----+-------------------+

Here is an example of a mission table:

    mysql> DESC obs_mission_cassini;
    +-------------------------+--------------+------+-----+-------------------+
    | Field                   | Type         | Null | Key | Default           |
    +-------------------------+--------------+------+-----+-------------------+
    | obs_general_id          | int unsigned | NO   | MUL | NULL              |
    | opus_id                 | char(50)     | NO   | MUL | NULL              |
    | bundle_id               | char(11)     | NO   | MUL | NULL              |
    | instrument_id           | char(12)     | NO   | MUL | NULL              |
    | obs_name                | char(30)     | NO   | MUL | NULL              |
    | rev_no                  | char(3)      | YES  | MUL | NULL              |
    | rev_no_int              | int          | YES  | MUL | NULL              |
    | is_prime                | int unsigned | NO   |     | NULL              |
    | prime_inst_id           | int unsigned | NO   | MUL | NULL              |
    | spacecraft_clock_count1 | double       | YES  | MUL | NULL              |
    | spacecraft_clock_count2 | double       | YES  | MUL | NULL              |
    | ert1                    | double       | YES  | MUL | NULL              |
    | ert2                    | double       | YES  | MUL | NULL              |
    | cassini_target_code     | int unsigned | YES  | MUL | NULL              |
    | cassini_target_name     | int unsigned | YES  | MUL | NULL              |
    | activity_name           | char(9)      | YES  | MUL | NULL              |
    | mission_phase_name      | int unsigned | YES  | MUL | NULL              |
    | sequence_id             | char(4)      | YES  |     | NULL              |
    | id                      | int unsigned | NO   | PRI | NULL              |
    | timestamp               | timestamp    | NO   |     | CURRENT_TIMESTAMP |
    +-------------------------+--------------+------+-----+-------------------+

Note that there will be a different number of rows in the `obs_general` table and many of the other tables:

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

    mysql> SELECT obs_general.planet_id, obs_mission_cassini.obs_name FROM obs_general
               JOIN obs_mission_cassini ON obs_mission_cassini.obs_general_id=obs_general.id
               WHERE obs_general.opus_id='co-iss-n1460960653';
    +-----------+-----------------------------+
    | planet_id | obs_name                    |
    +-----------+-----------------------------+
    |         4 | ISS_C44SA_APPRMOVU002_PRIME |
    +-----------+-----------------------------+

Generally speaking, you can think of the OPUS schema as having only one `obs` table and one row per OPUS ID with a huge number of columns encoding all of the possible metadata that could be needed. However, this would be inefficient to store (e.g. why store New Horizons metadata for a Cassini mission? You would just have to fill the columns wth NULLs), so instead we break the information across multiple tables and only populate the rows in the tables as necessary, allowing MySQL's efficient JOIN functionality to combine everything together when needed.

## The Encoding of Checkbox IDs and the `mult_obs_*` Tables

"Mult" (aka `GROUP`) fields are multiple choice options selected from a defined set. The list of available options may be hardcoded in the import pipeline or generated dynamically during the import process. Either way, the option associated with a particular observation is stored as an integer in the database. This integer is then used as an index into an associated "mult table" to look up the details of that option. The name of the "mult table" is a combination of the parent `obs_*` table and the field name. For example, for the "Planet Name" (`planet_id`) field in the "General Constraints" category (`obs_general`) the table is called `mult_obs_general_planet_id`, and it has the following schema:

    mysql> DESC mult_obs_general_planet_id;
    +------------------+---------------+------+-----+-------------------+
    | Field            | Type          | Null | Key | Default           |
    +------------------+---------------+------+-----+-------------------+
    | id               | int unsigned  | NO   | PRI | NULL              |
    | value            | char(100)     | YES  |     | NULL              |
    | label            | char(100)     | NO   |     | NULL              |
    | disp_order       | char(100)     | NO   |     | NULL              |
    | display          | enum('Y','N') | NO   |     | Y                 |
    | grouping         | char(100)     | YES  |     | NULL              |
    | group_disp_order | char(100)     | YES  |     | NULL              |
    | aliases          | json          | YES  |     | NULL              |
    | timestamp        | timestamp     | YES  |     | CURRENT_TIMESTAMP |
    +------------------+---------------+------+-----+-------------------+

The fields are:

- `id`: A unique integer which is used to reference a row in this table. This is the same value that is stored in the `obs_*` table.
- `value`: The actual metadata value which was the source of this option.
- `label`: The string to display in the UI.
- `disp_order`: A string that is used to sort the entries in the mult table so that they are displayed in a meaningful order. These strings do not have to have any intrinsic meaning, just be sortable.
- `display`: An indication of whether the value should be displayed or hidden in the UI. At this time all entries have a value of 'Y'.
- `grouping`: The name of the group this option belongs to. In the UI items in the same group will be collected together under a common, collasible header.
- `group_disp_order`: A string that is used to sort the names of the groups.
- `aliases`: A JSON-encoded list of strings representing alias names for this value, for example historical names for a target.
- `timestamp`: The date and time the entry was last modified.

For example, here are the entries for the `planet_id` field (timestamp removed for brevity):

    mysql> SELECT * FROM mult_obs_general_planet_id;
    +----+-------+---------+------------+---------+----------+------------------+
    | id | value | label   | disp_order | display | grouping | group_disp_order |
    +----+-------+---------+------------+---------+----------+------------------+
    |  0 | VEN   | Venus   | 010        | Y       | NULL     | NULL             |
    |  1 | EAR   | Earth   | 020        | Y       | NULL     | NULL             |
    |  2 | MAR   | Mars    | 030        | Y       | NULL     | NULL             |
    |  3 | JUP   | Jupiter | 040        | Y       | NULL     | NULL             |
    |  4 | SAT   | Saturn  | 050        | Y       | NULL     | NULL             |
    |  5 | URA   | Uranus  | 060        | Y       | NULL     | NULL             |
    |  6 | NEP   | Neptune | 070        | Y       | NULL     | NULL             |
    |  7 | PLU   | Pluto   | 080        | Y       | NULL     | NULL             |
    |  8 | OTH   | Other   | 090        | Y       | NULL     | NULL             |
    +----+-------+---------+------------+---------+----------+------------------+

Notice in this case that the `disp_order` field is simply a three-digit string that specifies the planets from inner to outer in the solar system, and there is no grouping.

Here are the first 10 entries for the `target_name` field (timestamp removed for brevity):

    mysql> SELECT * FROM mult_obs_general_target_name LIMIT 10;
    +----+-----------+--------------+--------------+---------+----------+------------------+
    | id | value     | label        | disp_order   | display | grouping | group_disp_order |
    +----+-----------+--------------+--------------+---------+----------+------------------+
    |  0 | S RINGS   | Saturn Rings | Saturn Rings | Y       | Saturn   | 060              |
    |  1 | SATURN    | Saturn       | Saturn       | Y       | Saturn   | 060              |
    |  2 | TITAN     | Titan        | Titan        | Y       | Saturn   | 060              |
    |  3 | ENCELADUS | Enceladus    | Enceladus    | Y       | Saturn   | 060              |
    |  4 | PHOEBE    | Phoebe       | Phoebe       | Y       | Saturn   | 060              |
    |  5 | HYPERION  | Hyperion     | Hyperion     | Y       | Saturn   | 060              |
    |  6 | PANDORA   | Pandora      | Pandora      | Y       | Saturn   | 060              |
    |  7 | DIONE     | Dione        | Dione        | Y       | Saturn   | 060              |
    |  8 | ATLAS     | Atlas        | Atlas        | Y       | Saturn   | 060              |
    |  9 | RHEA      | Rhea         | Rhea         | Y       | Saturn   | 060              |
    +----+-----------+--------------+--------------+---------+----------+------------------+

Notice in this case that the `disp_order` field is simply the name of the target, resulting in the targets being listed in alphabetical order. The grouping is done by planet, and the groups are sorted from inner to outer.

As discussed earlier, the value stored in the main `obs_*` table corresponds to the `id` index:

    mysql> SELECT obs_general.planet_id, mult_obs_general_planet_id.label FROM obs_general
               JOIN mult_obs_general_planet_id ON obs_general.planet_id=mult_obs_general_planet_id.id
               WHERE obs_general.opus_id='co-iss-n1460960653';
    +-----------+--------+
    | planet_id | label  |
    +-----------+--------+
    |         4 | Saturn |
    +-----------+--------+

Fields like `Intended Target Name` that support multiple simultaneous options are stored as JSON lists, and more complicated SQL queries are requried to extract the contents of those lists and match them with the mult tables:

    mysql> SELECT obs_general.target_name, obs_general.target_class FROM obs_general WHERE obs_general.opus_id='co-iss-n1460960653';
    +-------------+--------------+
    | target_name | target_class |
    +-------------+--------------+
    | [0]         | [3]          |
    +-------------+--------------+

To better understand how this is used, search for SQL commands containing `JSON_` in the `views.py` files under `apps`.

## NULL and NOT NULL Columns

Some columns (like `OPUS ID`) must always contain a valid value, while others (like `Right Ascension`) may have values missing for some observations. For safety and database integrity, we prevent columns that must always be valid from having `NULL` values by setting the `NOT NULL` column property. Other columns do not have this property set and allow `NULL` values. The validate step of the import process identifies columns that permit NULLs and yet have no NULL values and issues the suggestion that those columns be modified to be `NOT NULL`.

## The Use of SQL Indexes

SQL indexes are never required, but are useful for performance enhancement. A column that has an index will theoretically be faster to search on and to join with. As such, we try to make every metadata column have an associated index. Unfortunately, MySQL has a limit of 64 indexes for each table, so some tables with a large number of metadata fields (like `obs_ring_geometry`) are unable to have indexes for all columns. In these cases we remove indexes for the columns that are least likely to be used in searches.

## The Surface Geometry Tables

There are two types of surface geometry tables. The first, called simply `obs_surface_geometry`, contains the fields shown under "Surface Geometry Constraints" *other than* `Surface Geometry Target Selector`, which is a magic field. At the time of this writing, the only other field is `Multiple Target List`. Thus its schema is:

    mysql> DESC obs_surface_geometry;
    +----------------+--------------+------+-----+-------------------+
    | Field          | Type         | Null | Key | Default           |
    +----------------+--------------+------+-----+-------------------+
    | obs_general_id | int unsigned | NO   | MUL | NULL              |
    | opus_id        | char(50)     | NO   | MUL | NULL              |
    | bundle_id      | char(11)     | NO   | MUL | NULL              |
    | instrument_id  | char(12)     | NO   | MUL | NULL              |
    | target_list    | text         | YES  |     | NULL              |
    | id             | int unsigned | NO   | PRI | NULL              |
    | timestamp      | timestamp    | NO   |     | CURRENT_TIMESTAMP |
    +----------------+--------------+------+-----+-------------------+

There is also a series of tables, one per body, containing the surface geometry information for that body for each OPUS ID for which geometry information is available. These tables are named `obs_surface_geometry__<body>`. Normally at most only a few such tables will contain rows for a given OPUS ID, since only a small number bodies are in the field of view:

    mysql> SELECT COUNT(*) FROM obs_surface_geometry__enceladus WHERE opus_id='co-iss-n1460961193';
    +----------+
    | COUNT(*) |
    +----------+
    |        1 |
    +----------+

    mysql> SELECT COUNT(*) FROM obs_surface_geometry__titan WHERE opus_id='co-iss-n1460961193';
    +----------+
    | COUNT(*) |
    +----------+
    |        0 |
    +----------+

Other than the odd naming, these surface geometry tables behave exactly the same as any other `obs_*` table.

## The Special `obs_file` Table

The list of product files for any OPUS ID can be exceedingly long, and each file also needs to have associated metadata such as file size, version number, URL, and whether it is marked as checked in the Cart by default. All of this information could be encoded in a single enormous JSON structure in the `obs_general` table, but for efficiency and historical reasons we break this information out into its own table, `obs_file`. The `obs_file` table has a similar structure to other `obs_*` tables, but is unique in that it has a one-to-many relationship with OPUS IDs. In other words, with one row per downloadable file product, a single OPUS ID will likely have more than one row in this table. The `obs_file` table is only joined with `obs_general` when computing details of the Cart or displaying the list of available products on the Detail tab. Its schema is:

    mysql> DESC obs_files;
    +-----------------+--------------+------+-----+-------------------+
    | Field           | Type         | Null | Key | Default           |
    +-----------------+--------------+------+-----+-------------------+
    | obs_general_id  | int unsigned | NO   | MUL | NULL              |
    | opus_id         | char(50)     | NO   | MUL | NULL              |
    | bundle_id       | char(11)     | NO   | MUL | NULL              |
    | instrument_id   | char(12)     | NO   | MUL | NULL              |
    | version_number  | int unsigned | NO   | MUL | NULL              |
    | version_name    | char(16)     | NO   | MUL | NULL              |
    | category        | char(32)     | NO   | MUL | NULL              |
    | sort_order      | char(9)      | NO   | MUL | NULL              |
    | short_name      | char(32)     | NO   | MUL | NULL              |
    | full_name       | char(64)     | NO   | MUL | NULL              |
    | default_checked | int unsigned | NO   |     | NULL              |
    | product_order   | int unsigned | NO   |     | NULL              |
    | logical_path    | text         | NO   |     | NULL              |
    | url             | text         | NO   |     | NULL              |
    | checksum        | char(32)     | NO   |     | NULL              |
    | size            | int unsigned | NO   |     | NULL              |
    | width           | int unsigned | YES  |     | NULL              |
    | height          | int unsigned | YES  |     | NULL              |
    | pds_version     | int unsigned | NO   |     | NULL              |
    | id              | int unsigned | NO   | PRI | NULL              |
    | timestamp       | timestamp    | NO   |     | CURRENT_TIMESTAMP |
    +-----------------+--------------+------+-----+-------------------+

And as predicted a single OPUS ID is likely to appear more than once:

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

#
# The `param_info` Table

In order for OPUS to properly handle search and metadata display, it needs detailed information about each metadata field. This information is encoded in the `param_info` table, which has one row for each displayable metadata field:

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

- `category_name`: The name of the `obs_*` table containing the metadata field.
- `name`: The name of the field in the above-referenced table.
- `form_type`: Information about the field so that OPUS knows how to present it for searching and metadata display. The format is `TYPE[precision][:units]`. The available `TYPE`s are described in the section "Opus Metadata" above.
  - For numeric fields (`RANGE` and `LONG`), `precision` defines the precision of the value using `%` notation:
    - `%d` means a decimal value (no fractional part)
    - `%.nf` means a floating point value with `n` digits to the right of the decimal point.
  - When specified, `units` is a descriptor of the encoding of the value, including what the default units are, what other units are available, and how to convert the value between units. The list of available units is given in the top-level file `lib/opus_support.py`. For example, `form_type="RANGE%.4f:duration"` means to use the `duration` type of units, which has a default unit of `seconds` and support for `microseconds`, `milliseconds`, `minutes`, `hours`, and `days`. The values are displayed numerically and the precision of the default `%.3f` is adjusted based on the factor needed to convert from unit to unit. Another example is `form_type="RANGE:range_cassini_sclk"`. In this case, the "units" are really a way of indicating the conversion to and from the Cassini Spacecraft Clock Count, which has the format `dddddddddd.sss` where `sss` can be between 0 and 255 inclusive. There is no need to specify a precision because it is already implied by `range_cassini_sclk`. Likewise there are no units available other than the default units, since there is no other way to display this metadata.
- `display`: A boolean value indicating whether this metadata is available for searching in the UI. The primary reason to hide a metadata value from searching is because a min/max pair of `XXX1` and `XXX2` really only represents a single UI search widget. By convention we mark the `1` field as displayed and the `2` field hidden.
- `display_results`: A boolean value indicating whether this metadata is available for viewing. This is set to `False` only in rare occasions, such as the hidden `preview_images` field which is only for internal use.
- `disp_order`: An integer indicating how the metadata fields within a given category should be sorted for display. Smaller values will appear higher in the list.
- `label`: The English name of the metadata field as displayed in the title of a search widget, such as `Right Ascension`.
- `label_results`: The English name of the metadata field as displayed as a result, such as `Right Ascension (Min)` or `Right Ascension (Max)`.
- `slug`: The abbreviation for the field used in the main URL, such as `rightasc1` or `VOYAGERmissionphasename`.
- `old_slug`: An old abbreviation for the field from a previous version of OPUS. This is supported for backwards compatibility but is not used when creating any new URLs.
- `referred_slug`: Some fields (such as `Ring Radius`) appear under multiple categories (`Ring Geometry Constraints` and `Occultation/Reflectance Profiles Constraints`). Only one of these is the "real" field and the other simply refers to the real field. In the latter case, the `referred_slug` field gives the `slug` of the "real" field, and the `slug` field is `NULL`.
- `intro`: The extended text that appears at the top of a search widget explaining any special circumstances; `NULL` if none is provided. For example, for `Product Creation Time`:

        The Product Creation Time is the time when the actual final data product was created for inclusion in the PDS archive, not the time of the original observation. In most cases, you will want to use the Observation Time under General Constraints instead.

- `tooltip`: This field is not used.
- `dict_context` and `dict_name`: The "context" and "name" used to look up the tooltip for this field in the dictionary when used in a search widget. A `XXX2` field will have `NULL` for these columns. For example, for `right_asc1` we have `dict_context="OPUS_GENERAL"` and `dict_name="RIGHT_ASCENSION"` while for `right_asc2` both fields are `NULL.`
- `dict_context_results` and `dict_name_results`: The "context" and "name" used to look up the tooltip for this field in the dictionary when used to display metadata. For example, for `right_asc1` we have `dict_context="OPUS_GENERAL"` and `dict_name="RIGHT_ASCENSION_MIN"` while for `right_asc2` we have `dict_context="OPUS_GENERAL"` and `dict_name="RIGHT_ASCENSION_MAX"`.
- `sub_heading`: The sub-category to use when the category is further divided. For example, in the `Ring Geometry Constraints` category each field is under a sub-heading such as `Radius & Longitude` or `Edge-On Viewing Geometry`.
- `ranges`: A JSON field giving details of pre-programmed ranges that can be selected during searching, if any. For example, the `Wavelength` field has a number of pre-programmed options such as "Red" or "Violet".
- `field_hints1` and `field_hints2`: When `ranges` is specified, the grey text to display in the search widget to give a hint as to what can be typed. For example, for the `Wavelength` field this is "Wavelength or Color".
- `id`: A unique ID.
- `timestamp`: The date and time this row was last modified.

#
# The `table_names` Table

The `table_names` table contains the mapping between the `obs_*` SQL table name and the English used to describe the category in the UI:

    mysql> DESC table_names;
    +------------+--------------+------+-----+-------------------+
    | Field      | Type         | Null | Key | Default           |
    +------------+--------------+------+-----+-------------------+
    | table_name | char(60)     | NO   | MUL | NULL              |
    | label      | char(60)     | NO   |     | NULL              |
    | display    | char(1)      | NO   |     | Y                 |
    | disp_order | int          | NO   |     | NULL              |
    | id         | int unsigned | NO   | PRI | NULL              |
    | timestamp  | timestamp    | YES  |     | CURRENT_TIMESTAMP |
    +------------+--------------+------+-----+-------------------+

The fields are:

- `table_name`: The name of the SQL `obs_*` table.
- `label`: The English label, such as `Occultation/Reflectance Profiles Constraints`.
- `display`: A flag `Y` or `N` indicating whether to display this table. Currently this is always `Y`.
- `disp_order`: An integer indicating how the table should be sorted when displaying them.
- `id`: A unique ID.
- `timestamp`: The date and time this row was last modified.

#
# The `partables` Table

The `partables` table is used to instruct OPUS on how to figure out when a particular search category should be displayed. In general a category is displayed when all of the current search results have a particular property, e.g. the `Cassini Mission Constraints` table is displayed when all of the search results have the `Mission` field equal to `Cassini`.

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

- `trigger_tab`: The table to look at for a particular value.
- `trigger_col`: The column in that table to look at for a particular value.
- `trigger_val`: The value to look for.
- `partable`: When that value is found in that column in that table for all search results, trigger the display of this table.
- `id`: A unique ID.
- `timestamp`: The date and time this row was last modified.

For example:

    mysql> SELECT trigger_tab, trigger_col, trigger_val, partable FROM partables
               WHERE partable='obs_mission_cassini' OR partable='obs_instrument_nhlorri';
    +-------------+---------------+-------------+------------------------+
    | trigger_tab | trigger_col   | trigger_val | partable               |
    +-------------+---------------+-------------+------------------------+
    | obs_general | mission_id    | 0           | obs_mission_cassini    |
    | obs_general | instrument_id | 15          | obs_instrument_nhlorri |
    | obs_general | inst_host_id  | 0           | obs_mission_cassini    |
    +-------------+---------------+-------------+------------------------+

The `obs_mission_cassini` table will be displayed whenever all of the search results have a `mission_id` of Cassini (the mult value `0` for that column) or a `inst_host_id` of Cassini (the mult value `0` for that column), while the `obs_instrument_nhlorri` table will be displayed whenever all of the search results have an `instrument_id` of `NHLORRI` (the mult value `15` for that column).

#
# The `cart` Table

The `cart` table records the current Cart contents for all users. As long as the Django session is not changed and the database is not reinitialized, users have a cart that persists across browser sessions. Each row in the table represents one OPUS ID stored in the cart for a particular user. Thus the cart for one user is spread across as many rows as necessary.

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

- `session_id`: The Django session ID.
- `obs_general_id`: The `obs_general` unique ID of the observation in the cart.
- `opus_id`: The OPUS ID of the observation in the cart (which could also be found by joining the `obs_general_id` with the `obs_general` table).
- `recycled`: A boolean flag saying whether or not this observation is in the recycle bin.
- `id`: A unique ID.
- `timestamp`: The date and time this row was last modified.

#
# The `user_searches` and `cache_*` Tables

When a search query comes in, OPUS first looks in the `user_searches` table to see if the exact same search has already been performed; if so the results are already cached in one of the `cache_*` tables. If not, the details of the search are stored in `user_searches` and a new `cache_*` table is created with the results.

    mysql> DESC user_searches;
    +-----------------+--------------+------+-----+-------------------+
    | Field           | Type         | Null | Key | Default           |
    +-----------------+--------------+------+-----+-------------------+
    | id              | int unsigned | NO   | PRI | NULL              |
    | selections_json | text         | NO   |     | NULL              |
    | selections_hash | varchar(32)  | NO   | MUL | NULL              |
    | qtypes_json     | text         | YES  |     | NULL              |
    | qtypes_hash     | varchar(32)  | YES  |     | NULL              |
    | units_json      | text         | YES  |     | NULL              |
    | units_hash      | varchar(32)  | YES  |     | NULL              |
    | order_json      | text         | YES  |     | NULL              |
    | order_hash      | varchar(32)  | YES  |     | NULL              |
    | timestamp       | timestamp    | YES  |     | CURRENT_TIMESTAMP |
    +-----------------+--------------+------+-----+-------------------+

    mysql> DESC cache_1;
    +------------+--------------+------+-----+---------+
    | Field      | Type         | Null | Key | Default |
    +------------+--------------+------+-----+---------+
    | sort_order | int          | NO   | PRI | NULL    |
    | id         | int unsigned | YES  | UNI | NULL    |
    +------------+--------------+------+-----+---------+

The fields of `user_searches` are:

- `selections_json` and `selections_hash`: A JSON structure containing internal details of the search query, and an MD5 hash of the structure for ease of searching.
- `qtypes_json` and `qtypes_hash`: A JSON structure containing internal details of the qtypes used in the search query, and an MD5 hash of the structure for ease of searching.
- `units_json` and `units_hash`: A JSON structure containing internal details of the units used in the search query, and an MD5 hash of the structure for ease of searching.
- `order_json` and `order_hash`: A JSON structure containing internal details of the sort order used in the search query, and an MD5 hash of the structure for ease of searching.
- `id`: A unique ID. This unique ID is also used to identify the particular associated `cache_N` table.
- `timestamp`: The date and time this row was last modified.

Only if all four fields `selections`, `qtypes`, `units`, and `order` match is a search considered to have been previously performed.

The `cache_*` tables each contain all of the results from one search. Each row represents one OPUS ID in the search results. The fields of `cache_*` are:

- `id`: The `obs_general` ID of the result.
- `sort_order`: An integer indicating how the result appears in the sorted order. It is necessary because the `CREATE TABLE` operation in `get_search_results_chunk` does not preserve the ordering of the original table.

#
# The `contexts` and `definitions` Tables

OPUS supports a flexible database-based dictionary. Eventually this dictionary will be available through a website interface as a searchable glossary, but in the meantime it is used to supply tooltips for OPUS metadata fields. Each entry in the dictionary consists of a field name (e.g. `PLANET_NAME`) and a context (e.g. `OPUS_GENERAL_SEARCH`). It is possible for a field name to appear under multiple contexts. For example, a field such as `EXPOSURE_TIME` might mean something different in the `COISS` and `COCIRS` contexts. There are two database tables that support the dictionary.

The `contexts` table has the following schema:

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

Contexts are arranged in a tree, such that each context has a single parent. In the eventual website interface, a term will be displayed in multiple contexts if appropriate. The top-level context is the NASA PDS Planetary Science Data Dictionary, `PSDD`. Under this are the top-level OPUS Constraints categories: `OPUS_GENERAL`, `OPUS_PDS`, `OPUS_TYPE_IMAGE`, `OPUS_WAVELENGTH`, etc., as well as the missions like `CASSINI`. Under each mission are the instruments: `CASSINI` has `COCIRS`, `COISS`, `COUVIS`, etc.

The fields are:

- `name`: The internal name of the context (e.g. `CASSINI`).
- `description`: The pretty English name of the context (e.g. `Cassini Mission`).
- `parent`: The internal name of the parent context.
- `timestamp`: The date and time this row was last modified.
- `id`: A unique ID.

The `definitions` table has the following schema:

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

- `term`: The internal name of the term (e.g. `PLANET_NAME`).
- `context`: The associated internal name of the context.
- `definition`: The full free-form text definition.
- `timestamp`: The date and time this row was last modified.
- `id`: A unique ID.
