# The OPUS Database Schema

This document describes the database schema for OPUS 3.x.

OPUS uses MySQL 8.x. MySQL is a relational database based on SQL (Structured Query Language). A relational database is one where data is stored in a collection of *tables*, each of which has pre-defined *columns* with specified data types. The actual data is stored in each table in *rows*, much like in a spreadsheet, and each *row* contains an instance of each *column*. Columns that do not have data available may be marked by storing the special value `NULL`, if the column's properties are set to permit it. The relational part comes when tables cross-reference each other. For example, a column in one table could be used to select rows from another table. Such an operation is called a *join*, and many tables can be joined together. The joining of tables is the fundamental concept of relational databases. To fully understand the OPUS database it is strongly recommended that you become familiar with relational databases and the SQL language before continuing.

OPUS stores metadata in a series of `obs_*` tables. Each `obs_*` table generally corresponds to one of the "Constraints" menus visible in the browser UI. For example, `obs_general` corresponds to "General Constraints" and `obs_wavelength` corresponds to "Wavelength Constraints". This one-to-one correspondence between tables and UI metadata categories is an integral part of the design of OPUS, and if a metadata field is moved to a different "Constraints" category, the table design must also be changed.

Each row in an `obs_*` table represents a single observation represented by a unique OPUS ID, and each column generally represents one user-visible metadata field (although there are additional hidden fields as discussed below).

In addition to metadata, OPUS stores other information that helps it operate in tables. This includes information about checkbox fields, the contents of users' Carts, the dictionary of terms and definitions (including tooltips), information about the metadata fields themselves (this is metadata metadata!), and information about the metadata categories.

## OPUS Metadata

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

## The `obs_*` Tables

### General Overview

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
- `volume_id`: The PDS3 Volume ID of the row
- `instrument_id`: The PDS3 Instrument ID of the row
- `id`: An integer that can be used to quickly index a row in the table
- `timestamp`: A date/time field that records when the row was last updated

With the exception of the `id` field in the `obs_general` table and the `obs_general_id` field in all other `obs_*` tables, these extra fields are not used during OPUS's execution. In fact, the fields `opus_id`, `volume_id`, and `instrument_id` can easily be retrieved simply by joining a table with `obs_general`, which under the concept of "database normalization" is the correct and safest thing to do. Nevertheless, we have this redundant data in each table because it makes the import process easier (e.g., one can readily delete all metadata from a particular instrument without needing to join tables together), and because it helps in manual debugging and/or maintenance.

Here is an example of the schema for the `obs_general` table (note this may change slightly over time without this document being updated, so always refer to the actual database for the current schema):

    mysql> desc obs_general;
    +----------------------+--------------+------+-----+-------------------+
    | Field                | Type         | Null | Key | Default           |
    +----------------------+--------------+------+-----+-------------------+
    | id                   | int unsigned | NO   | PRI | NULL              |
    | opus_id              | char(50)     | NO   | UNI | NULL              |
    | volume_id            | char(11)     | NO   | MUL | NULL              |
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

Most of these fields should be self-evident. Some numeric fields have `1` and `2` versions. These are the minimum and maximum values of the metadata for a "dual column range". `right_asc` has two extra fields (`right_asc` and `d_right_asc`). These are internal fields that are used to help speed up searching on wrap-around longitudes. Also, `obs_general` has a hidden field `preview_images` which stores information about all of the preview images for each observation so that they can be rapidly retrieved when displaying the Gallery View without needing to join tables together.

`obs_pds` is a simple example of a secondary table that depends on `obs_general`:

    mysql> desc obs_pds;
    +-----------------------+--------------+------+-----+-------------------+
    | Field                 | Type         | Null | Key | Default           |
    +-----------------------+--------------+------+-----+-------------------+
    | obs_general_id        | int unsigned | NO   | MUL | NULL              |
    | opus_id               | char(50)     | NO   | MUL | NULL              |
    | volume_id             | char(11)     | NO   | MUL | NULL              |
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

    mysql> desc obs_mission_cassini;
    +-------------------------+--------------+------+-----+-------------------+
    | Field                   | Type         | Null | Key | Default           |
    +-------------------------+--------------+------+-----+-------------------+
    | obs_general_id          | int unsigned | NO   | MUL | NULL              |
    | opus_id                 | char(50)     | NO   | MUL | NULL              |
    | volume_id               | char(11)     | NO   | MUL | NULL              |
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

    mysql> select count(*) from obs_general; select count(*) from obs_mission_cassini;
    +----------+
    | count(*) |
    +----------+
    |    29689 |
    +----------+
    1 row in set (0.00 sec)

    +----------+
    | count(*) |
    +----------+
    |    18081 |
    +----------+
    1 row in set (0.03 sec)

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

### The Encoding of Checkbox IDs and the `mult_obs_*` Tables

"Mult" (aka `GROUP`) fields are multiple choice options selected from a defined set. The list of available options may be hardcoded in the import pipeline or generated dynamically during the import process. Either way, the option associated with a particular observation is stored as an integer in the database. This integer is then used as an index into an associated "mult table" to look up the details of that option. The name of the "mult table" is a combination of the parent `obs_*` table and the field name. For example, for the "Planet Name" (`planet_id`) field in the "General Constraints" category (`obs_general`) the table is called `mult_obs_general_planet_id`, and it has the following schema:

    mysql> desc mult_obs_general_planet_id;
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
    | timestamp        | timestamp     | YES  |     | CURRENT_TIMESTAMP |
    +------------------+---------------+------+-----+-------------------+

The fields are as follows:

- `id`: A unique integer which is used to reference a row in this table. This is the same value that is stored in the `obs_*` table.
- `value`: The actual metadata value which was the source of this option.
- `label`: The string to display in the UI.
- `disp_order`: A string that is used to sort the entries in the mult table so that they are displayed in a meaningful order. These strings do not have to have any intrinsic meaning, just be sortable.
- `display`: An indication of whether the value should be displayed or hidden in the UI. At this time all entries have a value of 'Y'.
- `grouping`: The name of the group this option belongs to. In the UI items in the same group will be collected together under a common, collasible header.
- `group_disp_order`: A string that is used to sort the names of the groups.
` `timestamp`: The date and time the entry was last modified.

For example, here are the entries for the `planet_id` field (timestamp removed for brevity):

    mysql> select * from mult_obs_general_planet_id;
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

    mysql> select * from mult_obs_general_target_name limit 10;
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

### NULL and NOT NULL Columns

Some columns (like `OPUS ID`) must always contain a valid value, while others (like `Right Ascension`) may have values missing for some observations. For safety and database integrity, we prevent columns that must always be valid from having `NULL` values by setting the `NOT NULL` column property. Other columns do not have this property set and allow `NULL` values. The validate step of the import process identifies columns that permit NULLs and yet have no NULL values and issues the suggestion that those columns be modified to be `NOT NULL`.

### The Use of SQL Indexes

SQL indexes are never required, but are useful for performance enhancement. A column that has an index will theoretically be faster to search on and to join with. As such, we try to make every metadata column have an associated index. Unfortunately, MySQL has a limit of 64 indexes for each table, so some tables with a large number of metadata fields (like `obs_ring_geometry`) are unable to have indexes for all columns. In these cases we remove indexes for the columns that are least likely to be used in searches.

### The Surface Geometry Tables


### The Special `obs_file` Table




## The `param_info` Table


## The `table_names` Table


## The `partable` Table


## The `cart` Table



## The `contexts` and `definitions` Tables


## The `user_searches` and `cache_*` Tables
