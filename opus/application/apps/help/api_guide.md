# OPUS API Guide

This guide describes the public API for the Outer Planets Unified Search (OPUS) tool of the PDS Ring-Moon Systems Node. It was produced on %DATE% and covers OPUS version %VERSION%.

# Basic Concepts: Metadata Fields, Retrieving, and Searching

The OPUS database contains a set of _observations_. Each observation is identified by a unique _OPUS ID_, which is a short series of characters identifying the mission, instrument, and observation number. The exact format of the OPUS ID varies by mission and instrument (examples: Cassini ISS: `co-iss-w1294561143`, HST WFPC2: `hst-05392-wfpc2-u2930301`). OPUS IDs can also be used to represent derived or composite products. Each observation is associated with metadata in one or more categories (e.g. "General" or "Ring Geometry"), each of which contains a series of metadata fields. Each metadata field is identified by a _slug_, which is a human-readable abbreviation. The list of available categories, metadata fields, and associated information is available [[XXXhere]] or through an API call described [[XXXhere]].

## Field Types

There are 3 basic types of fields: _multiple-choice_, _string_, and _range_.

* **Multiple-choice** fields contain a single value chosen from a set of valid values. For example, the `Mission` field may contain values such as `Cassini`, `Voyager`, or `Hubble`.
* **String** fields contain a single string of arbitrary characters. The formatting is specific to the individual field (e.g. a PDS3 volume ID might look like "COISS_2001" while a Dataset ID might look like "CO-E/V/J-ISSNA/ISSWA-2-EDR-V1.0").
* **Range** fields contain either a single value or a pair of values (minimum and maximum). Depending on the field, values may be integers, floating point values, date/time strings, or specially-formatted values such as spacecraft clock count. A single-value field is used for cases where there is only a single value for each observation, such as observation duration (there is only a single duration of time for each observation). Fields with both a minimum and maximum are used when a range of values is appropriate. Examples include observation time (where minimum is the starting time and maximum is the ending time) or right ascension (where minimum and maximum represent the range of right ascension values covered by an observation).

## Retrieving Metadata

Many API calls allow you to choose which metadata fields are returned by specifying the parameter `cols=`. In this case, a comma-separate list of slugs must be provided. For example:

    cols=opusid,instrument,planet,target,time1,time2

If a metadata field is a _single-value range_, then that slug must be provided without a numeric suffix (e.g. `observationduration`). However, if a metadata field contains both a minimum and maximum value in the database (e.g. `rightasc` for Right Ascension), then a `1` suffix indicates the minimum and a `2` suffix indicates the maximum. For example:

    cols=observationduration,rightasc1,rightasc2

However, it would be illegal to say `cols=observationduration1` or `cols=rightasc`.

See the section on [[XXX Field Types]] Field Types below for more information.

### Sorting

XXX

## Performing Searches

Many API calls allow you to select which observations you want to return by specifying a set of search constraints. If no constraints are specified, all observations in the database are returned. A search constraint consists of a slug and a desired value. For example:

    volumeid=COISS_2001

When searching on a multiple-choice field, multiple search values can be specified separated by commas. In this case, fields matching any of the values are returned:

    planet=Saturn,Uranus,Neptune

Multiple-choice values are case-insensitive.

Multiple search constraints are specified by joining them with a `&`. When search constraints are specified for different metadata fields, they are "AND"ed together:

    volumeid=COISS_2001&planet=Saturn,Uranus,Neptune

will return any observation with Volume ID `COISS_2001` **and** a Planet value of `Saturn`, `Uranus`, or `Neptune`.

All numeric ranges may be searched by specifying a minimum value (`1` suffix), maximum value (`2` suffix), or both. These suffixes should not be confused with the suffixes used to return metadata. In the case of searches, any range field, whether single-value or not, can have a minimum and maximum search value:

    `observationduration1=10&observationduration2=20`

### Query Types

When performing a search, all string and some range fields may have an additional "query type" (_qtype_) that describes how the search should be performed. The query type is specified by including `qtype-<slug>=value` as a search parameter. Note that the slug is always specified without a suffix, even if the search requires suffixes for minimum and maximum vales. The details of the qtypes associated with each field type are given below.

#### String Fields

Strings can be searched using the following query types:

* **contains**: the search string occurs anywhere within the metadata string. This is the default if not qtype is given.
* **begins**: the search string occurs at the beginning of the metadata string.
* **ends**: the search string occurs at the end of the metadata string.
* **matches**: the search string is exactly equal to the metadata string.
* **excludes**: the search string does _not_ appear anywhere in the metadata string.

#### Range Fields

Range fields can be searched using the following query types:

* **any**: The observation range overlaps at least some with the search range. In other words, either the observation maximum is greater than the search minimum, or the observation minimum is less than the search maximum. This option is used to request the widest possible set of observations that contain at least some of the range you are searching for. This is the default if no qtype is given.
* **all**: The observation range is a strict superset of the search range. In other words, the observation minimum is less than the search minimum, and the observation maximum is greater than the search maximum. This option is used to ensure that an entire feature you are looking for (such as a crater) is visible in the observation.
* **only**: The observation range is a strict subset of the search range. In other words, the observation minimum is greater than the search minimum, and the observation maximum is less than the search maximum. This option is used to tighly constrain your search to the smallest possible set of results.

### Units

When performing a search, some range fields may have an additional _unit_ that describes what units the search values are in. If no unit is specified, the default for that field is used. The unit is specified by including `unit-<slug>=value` as a search parameter. Note that the slug is always specified without a suffix, even if the search requires suffixes for minimum and maximum vales.

### Multiple Clauses

Multiple string and range constraints can be specified for the same field. In this case, the multiple constraints are "OR"ed together. To distinguish between the constraints, the slugs are suffixed with `_N` where `N` is any positive integer. For example:

    observationduration1_1=10&observationduration2_1=20&
    observationduration1_2=30&observationduration2_2=40

### Examples

* To search for Data Set IDs that contain "ISS" anywhere:

    `datasetid=ISS&qtype=contains` or `datasetid=ISS`

* To search for Data Set IDs that start with "CO-E":

    `datasetid=CO-E&qtype=begins`

* To search for Volume IDs "COISS_2001" or "COISS_2002":

    `volumeid_1=COISS_2001&qtype-volumeid_01=matches&`
    `volumeid_2=COISS_2002&qtype-volumeid_02=matches`

* To search for ring radii between 110,000 and 130,000 km using the "any" qtype:

    `RINGGEOringradius1=110000&RINGGEOringradius2=130000` or
    `RINGGEOringradius1=110000&RINGGEOringradius2=130000&qtype-RINGGEOringradius=any`

* To search for ring radii between 1.3 and 1.7 Saturn radii using the "only" qtype:

    `RINGGEOringradius1=1.3&RINGGEOringradius2=1.7&unit-RINGGEOringradius=saturnradii&qtype-RINGGEOringradius=only`

* To search for all Hubble images taken of Jupiter or Saturn in 1994 or 2001 with a spectral bandpass limited to 400-700 nm:

    `mission=Hubble&observationtype=Image&planet=Jupiter,Saturn&time1_1=1994-01-01T00:00:00.000&time2_1=1994-12-31T23:59:59.999&qtype-time_1=any&time1_2=2001-01-01T00:00:00.000&time2_2=2002-12-31T23:59:59.999&qtype-time_2=any&wavelength1=400&wavelength2=700&qtype-wavelength=only&unit-wavelength=nm`

# API Calls

## Return Formats

* json
* csv
* html
* zip

## Getting Data

### api/data.[fmt]

Get data for observations based on search criteria, columns, and sort order. Data is returned by "page" in the same sense that OPUS's "Browse Results" display is paginated.

Supported return formats: json,html,csv

Parameters:

* search params (If not supplied, all results are returned)
* column params (If not supplied, default columns are used)
* order=column_slug,... (Column(s) to sort on; if not supplied, default sort order is used)
* limit=N (The maximum number of observations to return; defaults to 100; can be more than 100)
* startobs=N (The observation number to start with; one-based) OR...
* page=N (The 100-observation page number to start with; defaults to 1)

JSON return:

    {'page_no': given page number OR 'start_obs': given starting observation, 'limit': given limit, 'count': number of observations returned, 'order': sort order, 'labels': selected column headers, 'page': data}

    Data is a list of lists in the requested sort order with one list entry per column."

examples:
-
Target Enceladus plumes taken with COISS in JSON
url: <HOST>/opus/api/data.json?instrument=Cassini+ISS&SURFACEGEOenceladusplanetographiclatitude1=70&SURFACEGEOenceladuscenterphaseangle1=160&order=time1&cols=opusid,target,time1,SURFACEGEOenceladuscenterphaseangle

### api/metadata_v2/[opus_id].[fmt]

Get all available, or particular, metadata for a single observation. opus_id: valid opus_id (or old ring_obs_id)

Supported return formats: json,html,csv

Parameters:

* cols=<column names> (If supplied, only returns data for these columns; cats is ignored)
* cats=<category names> (If supplied, only returns data for these categories)
JSON return: "If cols is supplied, a list of pairs {slug: value}. Otherwise a list of pairs {category: data} where data is a list of pairs {slug: value}."
examples:
-
Single Cassini ISS Saturn Observation (JSON, all metadata)
url: <HOST>/opus/api/metadata_v2/co-iss-w1866600688.json
-
Single Cassini ISS Saturn Observation (JSON, start and stop time only)
url: <HOST>/opus/api/metadata_v2/co-iss-w1866600688.json?cols=time1,time2
-
Single Cassini ISS Saturn Observation (JSON, PDS and Images constraints only)
url: <HOST>/opus/api/metadata_v2/co-iss-w1866600688.json?cats=PDS+Constraints,Image+Constraints
-
Single Cassini ISS Saturn Observation (HTML, all metadata)
url: <HOST>/opus/api/metadata_v2/co-iss-w1866600688.html
-
Single Cassini ISS Saturn Observation (HTML, start and stop time only)
url: <HOST>/opus/api/metadata_v2/co-iss-w1866600688.html?cols=time1,time2
-
Single Cassini ISS Saturn Observation (HTML, PDS and Images constraints only)
url: <HOST>/opus/api/metadata_v2/co-iss-w1866600688.html?cats=PDS+Constraints,Image+Constraints
-
Single Cassini ISS Saturn Observation (CSV, all metadata)
url: <HOST>/opus/api/metadata_v2/co-iss-w1866600688.csv
-
Single Cassini ISS Saturn Observation (CSV, start and stop time only)
url: <HOST>/opus/api/metadata_v2/co-iss-w1866600688.csv?cols=time1,time2
-
Single Cassini ISS Saturn Observation (CSV, PDS and Images constraints only)
url: <HOST>/opus/api/metadata_v2/co-iss-w1866600688.csv?cats=PDS+Constraints,Image+Constraints

### api/images/[size].[fmt]

Get image results of a given size for a search.
size: thumb,small,med,full

Supported return formats: json,html,csv,zip

Parameters:

* search params (If not supplied, all results are returned)
* order=column_slug,... (Column(s) to sort on; if not supplied, default sort order is used)
* limit=N (The maximum number of observations to return; defaults to 100)
* startobs=N (The observation number to start with; one-based) OR...
* page=N (The 100-observation page number to start with; defaults to 1)
examples:
-
planet = Jupiter, medium images, in JSON
url: <HOST>/opus/api/images/med.json?planet=Jupiter

### api/images.[fmt]

Get image results of all sizes for a search.

Supported return formats: json,html,csv,zip

Parameters:

* search params (If not supplied, all results are returned)
* order=column_slug,... (Column(s) to sort on; if not supplied, default sort order is used)
* limit=N (The maximum number of observations to return; defaults to 100)
* startobs=N (The observation number to start with; one-based) OR...
* page=N (The 100-observation page number to start with; defaults to 1)
JSON return:

    `"{'page_no': given page number OR 'start_obs': given starting observation, 'limit': given limit, 'count': number of observations returned, 'order': sort order, 'data': List of: {'opus_id': opus_id, '<size>_url': full URL, '<size>_alt_text': alt text, '<size>_size_bytes': image size in bytes, '<size>_width': image width in pixels, '<size>_height': image height in pixels}"`

examples:
-
planet = Saturn, sorted reverse by Saturn phase angle, in JSON
url: <HOST>/opus/api/images.json?planet=Saturn&order=-SURFACEGEOsaturncenterphaseangle

### api/image/[size]/[opus_id].[fmt]

Get an image of the given size for a single observation.
size: thumb,small,med,full

Supported return formats: json,html,csv,zip
opus_id: valid opus_id (or old ring_obs_id)
JSON return: "{'path': root path of the preview directory (deprecated), 'data': ingle-element list: {'opus_id': opus_id, '<size>_url': full URL, '<size>_alt_text': alt text, '<size>_size_bytes': image size in bytes, '<size>_width': image width in pixels, '<size>_height': image height in pixels, 'path': oot path of preview directory (deprecated), 'img': path to image relative to root path (deprecated), 'url': full URL (deprecated)}"
examples:
-
Saturn observation, full size, in JSON
url: <HOST>/opus/api/image/full/vg-iss-2-s-c4360022.json

### api/files/[opus_id].json

Get a list of all files for a single observation.
opus_id: valid opus_id (if you provide an old ring_obs_id, you will get the appropriate opus_id back)

Parameters:

* types=<types> (List of product types; if not supplied, all are returned)
* loc_type=<loc> (Format of returned path, 'url' or 'path'; defaults to 'url')
JSON return: "{'data': dictionary of opus_id, then indexed by product type for current version, 'versions': dictionary of version, then opus_id, then product_type}"
examples:
-
A Voyager ISS observation
url: <HOST>/opus/api/files/vg-iss-2-s-c4360022.json
-
A Galileo SSI observation, Raw data only
url: <HOST>/opus/api/files/go-ssi-c0349632000.json?types=gossi-raw
-
An HST WFC3 observation with multiple versions
url: <HOST>/opus/api/files/hst-11559-wfc3-ib4v19rp.json

### api/files.json

Get a list of all files for the search results.

Parameters:

* search params (If not supplied, all results are returned)
* order=column_slug,... (Column(s) to sort on; if not supplied, default sort order is used)
* limit=N (The maximum number of observations to return; defaults to 100)
* startobs=N (The observation number to start with; one-based) OR...
* page=N (The 100-observation page number to start with; defaults to 1)
* types=<types> (List of product types; if not supplied, all are returned)
* loc_type=<loc> (Format of returned path, 'url' or 'path'; defaults to 'url')
JSON return: "{'page_no': given page number OR 'start_obs': given starting observation, 'limit': given limit, 'count': number of observations returned, 'order': sort order, 'data': dictionary of opus_id, then indexed by product type for current version, 'versions': dictionary of version, then opus_id, then product_type}"
examples:
-
Target Pan
url: <HOST>/opus/api/files.json?&target=pan

### api/download/[opus_id].zip

Download a ZIP file containing all the products related to opus_id

Parameters:

* urlonly=N (Optional; if urlonly=1, only include the urls.txt file and omit all data files from the resulting zip)
* types=<types> (List of product types; if not supplied, all are returned)
examples:
-
A Voyager ISS observation
url: <HOST>/opus/api/download/vg-iss-2-s-c4360022.zip
-
A Voyager ISS observation, URLs only
url: <HOST>/opus/api/download/vg-iss-2-s-c4360022.zip?urlonly=1

### Getting Information about Data
endpoints:

### api/meta/result_count.[fmt]

Get the result count for a search

Supported return formats: json,html,csv

Parameters:

* search params (If not supplied, all results are returned)
examples:
-
Target Pan in JSON
url: <HOST>/opus/api/meta/result_count.json?target=Pan
-
Target Pan in HTML
url: <HOST>/opus/api/meta/result_count.html?target=Pan
-
Target Pan in CSV
url: <HOST>/opus/api/meta/result_count.csv?target=Pan

### api/meta/mults/[param].[fmt]

Returns all possible values for a given multiple choice field, given a search, and the result count for each value.
param: param name
fmt : json,html,csv

Parameters:

* search params (If not supplied, the result is not constrained)
examples:
-
Get all possible targets and counts for each when planet=Saturn in JSON
url: <HOST>/opus/api/meta/mults/target.json?planet=Saturn
-
Get all possible targets and counts for each when planet=Saturn in HTML
url: <HOST>/opus/api/meta/mults/target.html?planet=Saturn
-
Get all possible targets and counts for each when planet=Saturn in CSV
url: <HOST>/opus/api/meta/mults/target.csv?planet=Saturn

### api/meta/range/endpoints/[param].[fmt]

Get range endpoints for a field, given a search
param: param name

Supported return formats: json,html,csv

Parameters:

* search params (If not supplied, the result is not constrained)
examples:
-
Get ring radius endpoints for target Saturn in JSON
url: <HOST>/opus/api/meta/range/endpoints/RINGGEOringradius1.json?target=Saturn
-
Get ring radius endpoints for target Saturn in HTML
url: <HOST>/opus/api/meta/range/endpoints/RINGGEOringradius1.html?target=Saturn
-
Get ring radius endpoints for target Saturn in CSV
url: <HOST>/opus/api/meta/range/endpoints/RINGGEOringradius1.csv?target=Saturn

### api/categories/[opus_id].json

Return a list of all table names this opus_id exists in.
opus_id: valid opus_id
JSON return: "List of {'table_name': internal name, 'label': user-visible name}"
examples:
-
Category names for a Cassini ISS observation
url: <HOST>/opus/api/categories/co-iss-w1866600688.json

### api/categories.json

List all category names triggered by a particular search.

Parameters:

* search params (If not supplied, the result is not constrained)
JSON return: "List of {'table_name': internal name, 'label': user-visible name}"
examples:
-
Category names in JSON for a search for Methone
url: <HOST>/opus/api/categories.json?surfacegeometrytargetname=Methone

### api/fields/[field].[fmt]

Get information about a particular field
field: field slug

Supported return formats: json,csv
JSON response: "{'data': {slug: {'category': Pretty category name, 'label': Pretty field name, 'slug': slug, 'old_slug': previous slug (deprecated)}}}"
examples:
-
Get information about the "planet" field
url: <HOST>/opus/api/fields/planet.json
-
Get information about the "Rhea body center phase angle" field
url: <HOST>/opus/api/fields/SURFACEGEOrheacenterphaseangle.json

### api/fields.[fmt]

Get information about all fields

Supported return formats: json,csv

Parameters:

* collapse=1 (collapse all surface geo entries into single generic-target entries)
JSON response: "{'data': {slug: {'category': Pretty category name, 'label': Pretty field name, 'slug': slug, 'old_slug': previous slug (deprecated)}}}"
examples:
-
Get information about all fields
url: <HOST>/opus/api/fields.json
-
Get information about all fields but collapse surface geo fields
url: <HOST>/opus/api/fields.json?collapse=1
