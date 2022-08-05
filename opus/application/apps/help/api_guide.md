This guide describes the public API for the Outer Planets Unified Search (OPUS) tool of the PDS Ring-Moon Systems Node. It was produced on %DATE% and covers OPUS version %VERSION%.

<h1 class="op-help-api-guide-no-count">Table of Contents</h1>

%ADDCLASS%op-help-api-guide-toc%ENDADDCLASS%

* [Basic Concepts: Metadata Fields, Retrieving, and Searching](#basicconcepts)
    * [API Format](#apiformat)
    * [The OPUS Database](#opusdatabase)
    * [Retrieving Metadata](#retrievingmetadata)
    * [Performing Searches](#performingsearches)
      * [Query Types](#querytypes)
      * [Units](#units)
      * [Multiple Clauses](#clauses)
      * [Sorting](#sorting)
      * [Examples](#basicconceptexamples)
* [API Calls](#apicalls)
    * [Return Formats](#returnformats)
    * [Getting Metadata](#gettingmetadata)
      * [`api/data.[fmt]` - Return Metadata from a Search](#datafmt)
      * [`api/metadata_v2/[opusid].[fmt]` - Return Metadata for an OPUS ID](#metadatav2fmt)
    * [Getting Data](#gettingdata)
      * [`api/download/[opusid].zip` - Download Files for an O  PUS ID](#downloadopusidzip)
      * [`api/files.json` - Return URLs of Files from a Search](#filesjson)
      * [`api/files/[opusid].json` - Return URLs of Files for an OPUS ID](#filesopusidjson)
      * [`api/images.[fmt]` - Return URLs of All Images from a Search](#imagesfmt)
      * [`api/images/[size].[fmt]` - Return URLs of Images of a Specific Size from a Search](#imagesfmt)
      * [`api/image/[size]/[opusid].[fmt]` - Return URLs of Images of a Specific Size for an OPUS ID](#imagesfmt)
    * [Getting Information About Search Results](#infosearchresults)
      * [`api/meta/result_count.[fmt]` - Result Count for a Search](#resultcountfmt)
      * [`api/meta/mults/[field].[fmt]` - Return Possible Values for a Multiple-Choice Field](#multsfmt)
      * [`api/meta/range/endpoints/[field].[fmt]` - Return Range Endpoints for a Numeric Field](#endpointsfmt)
      * [`api/categories.json` - Return Categories from a Search](#categoriesfmt)
      * [`api/categories/[opusid].json` - Return Categories for an OPUS ID](#categoriesopusidfmt)
      * [`api/product_types.json` - Return Product Types from a Search](#producttypesfmt)
      * [`api/product_types/[opusid].json` - Return Product Types for an OPUS ID](#producttypesopusidfmt)
      * [`api/fields.[fmt]` - Return Information About All Metadata Fields](#fieldsfmt)
      * [`api/fields/[field].[fmt]` - Return Information About a Metadata Field](#fieldsfieldfmt)
* [Available Metadata Fields](#availablefields)


%ENDCLASS%

--------------------------------------------------------------------------------

<h1 id="basicconcepts">Basic Concepts: Metadata Fields, Retrieving, and Searching</h1>

<h2 id="apiformat">API Format</h2>

The OPUS API is accessed by encoding requests in individual URLs passed to the OPUS server (normally  `https://opus.pds-rings.seti.org`). Each request is independent and no state is saved between requests. A URL consists of the prefix components `/opus/api/` followed by the API entry point desired. The entry point name is suffixed by the desired format of the returned data (see [Return Formats](#returnformats)). API calls may take parameters provided after a single `?`. Each parameter is of the form `<name>=<value>`. If there is more than one parameter, they are separated by `&`. Parameters may be encoded using the standard octet encoding detailed in [RFC3986](https://tools.ietf.org/html/rfc3986), although only `&`, `=`, and `+` are required to be encoded as octets if used as a parameter's value. Spaces in search values may also be encoded as `+`.

Examples:

* API call with no parameters:

    %EXTLINK%%HOST%/opus/api/meta/result_count.json%ENDEXTLINK%

* API call with one parameter:

    %EXTLINK%%HOST%/opus/api/meta/result_count.json?volumeid=COISS_2001%ENDEXTLINK%

* API call with two parameters:

    %EXTLINK%%HOST%/opus/api/meta/result_count.json?time1=2009-01-01&time2=2010-01-01%ENDEXTLINK%

<h2 id="opusdatabase">The OPUS Database</h2>

The OPUS database contains a set of _observations_. Each observation is identified by a unique _OPUS ID_, which is a short series of characters identifying the mission, instrument, and observation number; the exact format of the OPUS ID varies by mission and instrument (e.g. Cassini ISS: `co-iss-w1294561143`, HST WFPC2: `hst-05392-wfpc2-u2930301t`). OPUS IDs can also be used to represent derived or composite products. Each observation is associated with metadata in one or more categories (e.g. "General" or "Ring Geometry"), each of which contains a series of metadata fields. Each metadata field is identified by a *fieldid*, which is a human-readable abbreviation. The list of available categories, metadata fields, and associated information is available [here](#availablefields) or through the API calls [`api/categories.json`](#categoriesfmt), [`api/categories/[opusid].json`](#categoriesopusidfmt), [`api/fields.[fmt]`](#fieldsfmt), and [`api/fields/[field].[fmt]`](#fieldsfmt).

There are three basic types of fields stored in the database: _multiple-choice_, _string_, and _range_.

* **Multiple-choice** fields contain a single value chosen from a set of valid values. For example, the `Mission` field may contain values such as `Cassini`, `Voyager`, or `Hubble`.
* **String** fields contain a single string of arbitrary characters. The formatting is specific to the individual field (e.g. PDS3 volume ID: "COISS_2001", Dataset ID: "CO-E/V/J-ISSNA/ISSWA-2-EDR-V1.0").
* **Range** fields contain either a single value or a pair of values (minimum and maximum). Depending on the field, values may be integers, floating point values, date/time strings, or specially-formatted values such as spacecraft clock count. A single-value field is used for cases where there is only a single value for each observation, such as observation duration (there is only a single duration of time for each observation). Fields with both a minimum and maximum are used when a range of values is appropriate. Examples include observation time (where minimum is the starting time and maximum is the ending time) or right ascension (where minimum and maximum represent the range of right ascension values covered by an observation).

<h2 id="retrievingmetadata">Retrieving Metadata</h2>

Many API calls allow you to choose which metadata fields are returned by specifying the parameter `cols=<fieldid_list>`, where `<fieldid_list>` is a comma-separated list of `fieldid`. For example:

%CODE%
cols=opusid,instrument,planet,target,time1,time2
%ENDCODE%

When a `cols` parameter is supported but none is provided, the default columns are used: `opusid,instrument,planet,target,time1,observationduration`.

If a metadata field is a _single-value range_, then that `fieldid` **must** be provided without a numeric suffix (e.g. `observationduration`). However, if a metadata field contains both a minimum and maximum value in the database (e.g. `rightasc` for Right Ascension), then a `1` suffix indicating the minimum a `2` suffix indicating the maximum must be provided. For example:

%CODE%
cols=observationduration,rightasc1,rightasc2
%ENDCODE%

However, it would be illegal to say `cols=observationduration1` or `cols=rightasc`.

See the section on [Available Metadata Fields](#availablefields) below for more information.

<h2 id="performingsearches">Performing Searches</h2>

Many API calls allow you to select which observations you want to return by specifying a set of search constraints. If no constraints are specified, all observations in the database are returned. A search constraint consists of a `searchid` and a desired value. For example:

%CODE%
volumeid=COISS_2001
%ENDCODE%

When searching on a multiple-choice field, additional search values can be specified separated by commas. In this case, observations matching any of the values are returned:

%CODE%
planet=Saturn,Uranus,Neptune
%ENDCODE%

Multiple-choice values are case-insensitive.

More than one search constraint can be specified by joining them with `&`. When search constraints are specified for different metadata fields, they are "AND"ed together. For example:

%CODE%
volumeid=COISS_2001&planet=Saturn,Uranus,Neptune
%ENDCODE%

will return any observation with Volume ID `COISS_2001` **and** a Planet value of `Saturn`, `Uranus`, or `Neptune`.

All numeric ranges may be searched by specifying a minimum value (`1` suffix), maximum value (`2` suffix), or both. These suffixes should not be confused with the suffixes used to return metadata. In the case of searches, any range field, whether single-value or not, can have a minimum and maximum search value:

%CODE%
observationduration1=10&observationduration2=20
%ENDCODE%

Fields containing longitudes are treated specially and the minimum search value may be greater than the maximum, in which case the search "wraps around" 360 degrees. For example, it is reasonable to search on a longitude range of 350 to 10 degrees. This will give the opposite results of searching on 10 to 350 degrees.

<h3 id="querytypes">Query Types</h3>

When performing a search, all string and some range fields may have an additional "query type" (_qtype_) that describes how the search should be performed. The query type is specified by including `qtype-<searchid>=value` as a search parameter. Note that the `searchid` is always specified without a (`1` or `2`) suffix, even if the search requires suffixes for minimum and maximum vales. This is because the qtype applies to the entire search field, not to the minimum or maximum values separately. The details of the qtypes associated with each field type are given below.

#### String Fields

Strings can be searched using the following query types:

* **contains**: the search string occurs anywhere within the metadata string. This is the default if no qtype is given.
* **begins**: the search string occurs at the beginning of the metadata string.
* **ends**: the search string occurs at the end of the metadata string.
* **matches**: the search string is exactly equal to the metadata string.
* **excludes**: the search string does _not_ appear anywhere in the metadata string.
* **regex**: the metadata string matches the given [regular expression](http://userguide.icu-project.org/strings/regexp).

#### Range Fields

Range fields can be searched using the following query types:

* **any**: The observation range overlaps at least some with the search range. In other words, either the observation maximum is greater than the search minimum, or the observation minimum is less than the search maximum. This option is used to request the widest possible set of observations that contain at least some of the range you are searching for. This is the default if no qtype is given.
* **all**: The observation range is a strict superset of the search range. In other words, the observation minimum is less than the search minimum, and the observation maximum is greater than the search maximum. This option is used to ensure that an entire feature you are looking for (such as a crater) is visible in the observation.
* **only**: The observation range is a strict subset of the search range. In other words, the observation minimum is greater than the search minimum, and the observation maximum is less than the search maximum. This option is used to tighly constrain your search to the smallest possible set of results.

<h3 id="units">Units</h3>

When performing a search, some range fields have an additional _unit_ that describes what units the search values are in. If no unit is specified, the default for that field is used. The unit is specified by including `unit-<searchid>=value` as a search parameter. Note that the `searchid` is always specified without a suffix, even if the search requires suffixes for minimum and maximum vales.

<h3 id="clauses">Multiple Clauses</h3>

Multiple string and range constraints can be specified for the same field. In this case, the multiple constraints are "OR"ed together. To distinguish between the constraints, the `searchid`s are suffixed with `_N` where `N` is any positive integer. For example:

%CODE%
observationduration1_1=10&observationduration2_1=20&observationduration1_2=30&observationduration2_2=40
%ENDCODE%

would search for Observation Duration between 10 and 20 seconds (inclusive) *or* between 30 and 40 seconds (inclusive). Each clause can have its own `qtype` and `unit`, if applicable.

<h3 id="sorting">Sorting</h3>

By default, the results of a search are sorted first by Observation Start Time (`time1`) and then by OPUS ID (`opusid`). This order can be changed by specifying `order=<fieldid_list>`, where `<fieldid_list>` contains one or more `fieldid`s (as would be used when retrieving metadata) separated by commas. If multiple `fieldid`s are given, the sorting proceeds by the first `fieldid`, and then if the values are identical by the second `fieldid`, etc. Sorting is normally done in ascending order, but may be changed to descending for a particular field by prepending the `fieldid` with a minus sign (`-`).

Note that if `opusid` does not appear in the sort order list, it will automatically be added at the end. Since all OPUS IDs are unique, this guarantees the resulting order is deterministic.

<h3 id="basicconceptexamples">Examples</h3>

* To search for Data Set IDs that contain "ISS" anywhere (the qtype is optional):

%CODE%
datasetid=ISS&qtype-datasetid=contains
%ENDCODE%

* To search for Data Set IDs that start with "CO-E":

%CODE%
datasetid=CO-E&qtype-datasetid=begins
%ENDCODE%

* To search for Volume IDs "COISS_2001" or "COISS_2002":

%CODE%
volumeid_1=COISS_2001&qtype-volumeid_1=matches&volumeid_2=COISS_2002&qtype-volumeid_2=matches
%ENDCODE%

* To search for ring radii between 110,000 and 130,000 km using the "any" qtype (the qtype is optional):

%CODE%
RINGGEOringradius1=110000&RINGGEOringradius2=130000

RINGGEOringradius1=110000&RINGGEOringradius2=130000&qtype-RINGGEOringradius=any
%ENDCODE%

* To search for ring radii between 1.3 and 1.7 Saturn radii using the "only" qtype:

%CODE%
RINGGEOringradius1=1.3&RINGGEOringradius2=1.7&unit-RINGGEOringradius=saturnradii&qtype-RINGGEOringradius=only
%ENDCODE%

* To search for all Hubble images taken of Jupiter or Saturn in 1994 or 2001 with a spectral bandpass limited to 400-700 nm:

%CODE%
mission=Hubble&observationtype=Image&planet=Jupiter,Saturn&time1_1=1994-01-01T00:00:00.000&time2_1=1994-12-31T23:59:59.999&qtype-time_1=any&time1_2=2001-01-01T00:00:00.000&time2_2=2002-12-31T23:59:59.999&qtype-time_2=any&wavelength1=400&wavelength2=700&qtype-wavelength=only&unit-wavelength=nm
%ENDCODE%

* To search for all Cassini ISS images sorted by filter name then in reverse order by observation duration, and finally by OPUS ID:

%CODE%
instrument=Cassini+ISS&order=COISSfilter,-observationduration,opusid
%ENDCODE%

--------------------------------------------------------------------------------

<h1 id="apicalls">API Calls</h1>

<h2 id="returnformats">Return Formats</h2>

All API calls take a suffix `.[fmt]` specifying the format in which to return data. Possible values are:

* **json**: Return all data in a JSON structure. This is most useful for programs wanting to process the returned data directly. Note that some JSON returns may contain data that is not detailed in this document. This data is usually provided for backwards compatibility with legacy applications and should **not** be relied on for new development.
* **csv**: Return all data in a comma-separated value (CSV) file, suitable for import into a spreadsheet program.
* **html**: Return all data as an HTML document. This is most useful when viewing directly in a browser. Note that the returned HTML has minimal formatting and does not include any header or `body` tags.
* **zip**: Return all data as a ZIP file.

Not all API calls provide results in all formats. The formats supported are listed with each call.

---

<h2 id="gettingmetadata">Getting Metadata</h2>





<h3 id="datafmt"><code>api/data.[fmt]</code> - Return Metadata from a Search</h3>

Get data for observations based on search criteria, sort order, and requested metadata fields. Data is returned in chunks (called "pages" in the returned JSON) to limit return size. The starting observation number and the number of observations desired can be specified.

Supported return formats: `json`, `html`, `csv`

#### Parameters

| Parameter | Description | Default |
|---|---|---|
| `<searchid>=<value>` | Search parameters (including sort order) | All observations in database |
| `cols=<fieldid_list>` | Metadata fields to return | [Default columns](#retrievingmetadata) |
| `startobs=<N>` | The (1-based) observation number to start with | 1 |
| `limit=<N>` | The maximum number of observations to return | 100 |

#### JSON Return Format

The return value is a JSON object containing these fields:

| Field Name | Description |
|---|---|
| `start_obs` | Requested starting observation |
| `limit` | Requested limit |
| `count` | Number of observations actually returned |
| `available` | Total number of observations available from this search |
| `order` | Sort order used |
| `labels` | Requested metadata field names (fully qualified) in the order requested with `cols` |
| `page` | The observation data |

`page` is a list with one entry per returned observation. Each entry is itself a list, with one entry per requested metadata field, in the same order as was requested with `cols`.

Example:

* Retrieve data in JSON format for the first three Cassini ISS images that contain Enceladus' south pole (latitude 70 degrees or greater) and have a phase angle at Enceladus of 160 degrees or greater.

    %EXTLINK%%HOST%/opus/api/data.json?instrument=Cassini+ISS&SURFACEGEOenceladus_planetographiclatitude1=70&SURFACEGEOenceladus_centerphaseangle1=160&order=time1&cols=opusid,target,time1,SURFACEGEOenceladus_centerphaseangle&startobs=5&limit=3%ENDEXTLINK%

    Return value:

%CODE%
{
  "start_obs": 5
  "limit": 3,
  "count": 3,
  "available": 81,
  "order": "time1,opusid",
  "labels": [
    "OPUS ID",
    "Intended Target Name",
    "Observation Start Time",
    "Phase Angle at Body Center [Enceladus] (degrees)"
  ],
  "page": [
    [
      "co-iss-n1635813867",
      "Enceladus",
      "2009-11-02T00:01:22.626",
      "161.414"
    ],
    [
      "co-iss-n1635814065",
      "Enceladus",
      "2009-11-02T00:03:38.237",
      "161.519"
    ],
    [
      "co-iss-n1635814245",
      "Enceladus",
      "2009-11-02T00:07:43.051",
      "161.657"
    ]
  ]
}
%ENDCODE%

#### CSV Return Format

The return value is a series of text lines. The first line contains the names of the requested metadata fields. After that is one line per observation containing the requested metadata.

Example:

* Retrieve data in CSV format for the first three Cassini ISS images that contain Enceladus' south pole (latitude 70 degrees or greater) and have a phase angle at Enceladus of 160 degrees or greater.

    %EXTLINK%%HOST%/opus/api/data.csv?instrument=Cassini+ISS&SURFACEGEOenceladus_planetographiclatitude1=70&SURFACEGEOenceladus_centerphaseangle1=160&order=time1&cols=opusid,target,time1,SURFACEGEOenceladus_centerphaseangle&startobs=5&limit=3%ENDEXTLINK%

    Return value:

%CODE%
OPUS ID,Intended Target Name,Observation Start Time,Phase Angle at Body Center [Enceladus] (degrees)
co-iss-n1635813867,Enceladus,2009-11-02T00:01:22.626,161.414
co-iss-n1635814065,Enceladus,2009-11-02T00:03:38.237,161.519
co-iss-n1635814245,Enceladus,2009-11-02T00:07:43.051,161.657
%ENDCODE%

#### HTML Return Format

The return value is an HTML table. The table header contains the names of the requested metadata fields. The table rows contain the requested metadata.

Example:

* Retrieve data in HTML format for the first three Cassini ISS images that contain Enceladus' south pole (latitude 70 degrees or greater) and have a phase angle at Enceladus of 160 degrees or greater.

    %EXTLINK%%HOST%/opus/api/data.html?instrument=Cassini+ISS&SURFACEGEOenceladus_planetographiclatitude1=70&SURFACEGEOenceladus_centerphaseangle1=160&order=time1&cols=opusid,target,time1,SURFACEGEOenceladus_centerphaseangle&startobs=5&limit=3%ENDEXTLINK%

    Return value:

%ADDCLASS%op-api-guide-code-block%ENDADDCLASS%

    <table>
    <tr>
    <th>OPUS ID</th>
    <th>Intended Target Name</th>
    <th>Observation Start Time</th>
    <th>Phase Angle at Body Center [Enceladus] (degrees)</th>
    </tr>
    <tr>
    <td>co-iss-n1635813867</td>
    <td>Enceladus</td>
    <td>2009-11-02T00:01:22.626</td>
    <td>161.414</td>
    </tr>
    <tr>
    <td>co-iss-n1635814065</td>
    <td>Enceladus</td>
    <td>2009-11-02T00:03:38.237</td>
    <td>161.519</td>
    </tr>
    <tr>
    <td>co-iss-n1635814245</td>
    <td>Enceladus</td>
    <td>2009-11-02T00:07:43.051</td>
    <td>161.657</td>
    </tr>
    </table>
%ENDCLASS%




<h3 id="metadatav2fmt"><code>api/metadata_v2/[opusid].[fmt]</code> - Return Metadata for an OPUSID</h3>

Get all available, or particular, metadata for a single observation.

Supported return formats: `json`, `html`, `csv`

#### Parameters

| Parameter | Description | Default |
|---|---|---|
| `cols=<field list>` | Metadata fields to return | All columns |
| `cats=<categories>` | If supplied, only returns data for these categories; if `cols` is supplied, `cats` is ignored | All categories |

`categories` is a list of category names separated by commas. Category names can either be full names ending in "Constraints" (e.g. `PDS Constraints` or `Cassini ISS Constraints`) or abbreviated names representing internal database tables (`obs_pds`, `obs_mission_cassini`, or `obs_instrument_coiss`). Full category names must replace spaces with `+` or another appropriate encoding. The list of categories available for an `opusid` can be retrieved with [`api/categories/[opusid].json`](#categoriesopusidfmt).

#### JSON Return Format

If the `cols` parameter is supplied, the return value is a JSON object containing a list of objects each with a single name/value pair `{<fieldid>: <value>}`. If the `cols` parameter is not supplied, the return value is a JSON object containing name/value pairs `{<category>: <data>}` where `data` is a list of objects each with a single name/value pair `{<fieldid>: <value>}`.

Examples:

* Retrieve all metadata for a single Cassini ISS Saturn observation in JSON format:

    %EXTLINK%%HOST%/opus/api/metadata_v2/co-iss-w1866600688.json%ENDEXTLINK%

    Return value:

%CODE%
{
  "General Constraints": {
    "planet": "Saturn",
    "target": "Saturn",
    [...]
  },
  "PDS Constraints": {
    "volumeid": "COISS_2111",
    "datasetid": "CO-S-ISSNA/ISSWA-2-EDR-V1.0",
    [...]
  },
  [...]
}
%ENDCODE%

* Retrieve start and stop time only for a single Cassini ISS Saturn observation in JSON format:

    %EXTLINK%%HOST%/opus/api/metadata_v2/co-iss-w1866600688.json?cols=time1,time2%ENDEXTLINK%

    Return value:

%CODE%
[
  {
    "time1": "2017-02-24T03:03:29.866"
  },
  {
    "time2": "2017-02-24T03:03:33.666"
  }
]
%ENDCODE%

* Retrieve PDS and Images Constraints only for a single Cassini ISS Saturn Observation in JSON format:

    %EXTLINK%%HOST%/opus/api/metadata_v2/co-iss-w1866600688.json?cats=PDS+Constraints,Image+Constraints%ENDEXTLINK%

    Return value:

%CODE%
{
  "PDS Constraints": {
    "volumeid": "COISS_2111",
    "datasetid": "CO-S-ISSNA/ISSWA-2-EDR-V1.0",
    "productid": "1_W1866600688.122",
    "productcreationtime": "2017-02-25T09:50:35.000",
    "primaryfilespec": "COISS_2111/data/1866491385_1866605022/W1866600688_1.IMG",
    "opusid": "co-iss-w1866600688",
    "note": "N/A"
  },
  "Image Constraints": {
    "duration": "3.8000",
    "greaterpixelsize": "1024",
    "lesserpixelsize": "1024",
    "levels": "4096",
    "imagetype": "Frame"
  }
}
%ENDCODE%

#### CSV Return Format

The return value is a series of text lines. If `cols` is supplied, the return value is a line containing the list of field names followed by a line containing the list of metadata for those fields. If `cols` is not supplied, the return contains, for each category, three lines: the name of the category, the list of field names in that category, and the metadata for those fields.

* Retrieve all metadata for a single Cassini ISS Saturn observation in CSV format:

    %EXTLINK%%HOST%/opus/api/metadata_v2/co-iss-w1866600688.csv%ENDEXTLINK%

    Return value:

%CODE%
General Constraints
Planet,Intended Target Name,Nominal Target Class,Mission, [...]
Saturn,Saturn,Planet,Cassini, [...]
PDS Constraints
Volume ID,Data Set ID,Product ID,Product Creation Time, [...]
COISS_2111,CO-S-ISSNA/ISSWA-2-EDR-V1.0,1_W1866600688.122,2017-02-25T09:50:35.000, [...]
Image Constraints
Exposure Duration (secs),Greater Size in Pixels,Lesser Size in Pixels, [...]
3.8000,1024,1024, [...]
[...]
%ENDCODE%

* Retrieve start and stop time only for a single Cassini ISS Saturn observation in CSV format:

    %EXTLINK%%HOST%/opus/api/metadata_v2/co-iss-w1866600688.csv?cols=time1,time2%ENDEXTLINK%

    Return value:

%CODE%
Observation Start Time,Observation Stop Time
2017-02-24T03:03:29.866,2017-02-24T03:03:33.666
%ENDCODE%

* Retrieve PDS and Image Constraints only for a single Cassini ISS Saturn Observation in CSV format:

    %EXTLINK%%HOST%/opus/api/metadata_v2/co-iss-w1866600688.csv?cats=PDS+Constraints,Image+Constraints%ENDEXTLINK%

    Return value:

%CODE%
PDS Constraints
Volume ID,Data Set ID,Product ID,Product Creation Time, [...]
COISS_2111,CO-S-ISSNA/ISSWA-2-EDR-V1.0,1_W1866600688.122,2017-02-25T09:50:35.000, [...]
Image Constraints
Exposure Duration (secs),Greater Size in Pixels,Lesser Size in Pixels, [...]
3.8000,1024,1024, [...]
%ENDCODE%

#### HTML Return Format

If the `cols` parameter is supplied, the return value is an HTML description list containing name/value pairs where the name is the fully-qualified name of the metadata field. If the `cols` parameter is not supplied, the return value is an HTML description list containing name/value pairs organized by category name.

Examples:

* Retrieve all metadata for a single Cassini ISS Saturn observation in HTML format:

    %EXTLINK%%HOST%/opus/api/metadata_v2/co-iss-w1866600688.html%ENDEXTLINK%

    Return value:

%ADDCLASS%op-api-guide-code-block%ENDADDCLASS%

    <dl>
    <dt>General Constraints</dt>
    <dl>
    <dt>Planet</dt><dd>Saturn</dd>
    <dt>Intended Target Name</dt><dd>Saturn</dd>
    [...]
    </dl>
    <dt>PDS Constraints</dt>
    <dl>
    <dt>Volume ID</dt><dd>COISS_2111</dd>
    <dt>Data Set ID</dt><dd>CO-S-ISSNA/ISSWA-2-EDR-V1.0</dd>
    [...]
    </dl>
    [...]
    </dl>
%ENDCLASS%

* Retrieve start and stop time only for a single Cassini ISS Saturn observation in HTML format:

    %EXTLINK%%HOST%/opus/api/metadata_v2/co-iss-w1866600688.html?cols=time1,time2%ENDEXTLINK%

    Return value:

%ADDCLASS%op-api-guide-code-block%ENDADDCLASS%

    <dl>
    <dt>Observation Start Time</dt><dd>2017-02-24T03:03:29.866</dd>
    <dt>Observation Stop Time</dt><dd>2017-02-24T03:03:33.666</dd>
    </dl>
%ENDCLASS%

* Retrieve PDS and Image Constraints only for a single Cassini ISS Saturn Observation in HTML format:

    %EXTLINK%%HOST%/opus/api/metadata_v2/co-iss-w1866600688.html?cats=PDS+Constraints,Image+Constraints%ENDEXTLINK%

    Return value:

%ADDCLASS%op-api-guide-code-block%ENDADDCLASS%

    <dl>
    <dt>PDS Constraints</dt>
    <dl>
    <dt>Volume ID</dt><dd>COISS_2111</dd>
    <dt>Data Set ID</dt><dd>CO-S-ISSNA/ISSWA-2-EDR-V1.0</dd>
    <dt>Product ID</dt><dd>1_W1866600688.122</dd>
    <dt>Product Creation Time</dt><dd>2017-02-25T09:50:35.000</dd>
    <dt>Primary File Spec</dt><dd>COISS_2111/data/1866491385_1866605022/W1866600688_1.IMG</dd>
    <dt>OPUS ID</dt><dd>co-iss-w1866600688</dd>
    <dt>Note</dt><dd>N/A</dd>
    </dl>
    <dt>Image Constraints</dt>
    <dl>
    <dt>Exposure Duration (secs)</dt><dd>3.8000</dd>
    <dt>Greater Size in Pixels</dt><dd>1024</dd>
    <dt>Lesser Size in Pixels</dt><dd>1024</dd>
    <dt>Intensity Levels</dt><dd>4096</dd>
    <dt>Image Type</dt><dd>Frame</dd>
    </dl>
    </dl>
%ENDCLASS%





<h2 id="gettingdata">Getting Data</h2>

<h3 id="downloadopusidzip"><code>api/download/[opusid].zip</code> - Download Files for an OPUS ID</h3>

Download a ZIP file containing all (or some) of the products related to opusid.

Supported return formats: `zip`.

#### Parameters

| Parameter | Description | Default |
|---|---|---|
| `urlonly=<N>` | If `urlonly=1` is specified, only include the `urls.txt` file and omit all data files | Include all data files |
| `types=<types>` | List of product types to return | All product types  |

The `types` parameter is a list of download product types. Available types can be retrieved with the [`api/product_types.json`](#producttypesfmt) or [`api/product_types/[opusid].json`](#producttypesopusidfmt) API calls. The `@` modifier can be used to specify the version for a product type. If the version is not specified for a product type, the "Current" version will be returned.

#### Examples

* Download both current and version 2.0 calibrated image files for a Cassini ISS observation:

    %EXTLINK%%HOST%/opus/api/download/co-iss-n1460973661.zip?types=coiss_calib@current,coiss_calib@v2.0%ENDEXTLINK%

    Return value is a zip archive containing the files:

%CODE%
calibrated/COISS_2xxx/COISS_2002/data/1460960653_1461048959/N1460973661_1_CALIB.IMG
calibrated/COISS_2xxx/COISS_2002/data/1460960653_1461048959/N1460973661_1_CALIB.LBL
calibrated/COISS_2xxx/COISS_2002/data/1462783195_1462915477/N1462840881_1_CALIB.IMG
calibrated/COISS_2xxx/COISS_2002/data/1462783195_1462915477/N1462840881_1_CALIB.LBL
calibrated/COISS_2xxx_v1/COISS_2002/data/1460960653_1461048959/N1460973661_1_CALIB.IMG
calibrated/COISS_2xxx_v1/COISS_2002/data/1460960653_1461048959/N1460973661_1_CALIB.LBL
calibrated/COISS_2xxx_v1/COISS_2002/data/1462783195_1462915477/N1462840881_1_CALIB.IMG
calibrated/COISS_2xxx_v1/COISS_2002/data/1462783195_1462915477/N1462840881_1_CALIB.LBL
calibrated/COISS_2xxx_v2/COISS_2002/data/1460960653_1461048959/N1460973661_1_CALIB.IMG
C4360022_GEOMED.LBL
C4360022_med.jpg
C4360022_RAW.IMG
C4360022_RAW.LBL
C4360022_RESLOC.DAT
C4360022_RESLOC.LBL
C4360022_RESLOC.TAB
C4360022_small.jpg
C4360022_thumb.jpg
data.csv
manifest.csv
urls.txt
VGISS_6210_inventory.lbl
VGISS_6210_inventory.csv
VGISS_6210_moon_summary.lbl
VGISS_6210_moon_summary.tab
VGISS_6210_ring_summary.lbl
VGISS_6210_ring_summary.tab
VGISS_6210_saturn_summary.lbl
VGISS_6210_saturn_summary.tab
%ENDCODE%

* Download all product types (including all data files) for a Voyager ISS observation:

    %EXTLINK%%HOST%/opus/api/download/vg-iss-2-s-c4360022.zip%ENDEXTLINK%

    Return value is a zip archive containing the files:

%CODE%
C4360022_CALIB.IMG
C4360022_CALIB.LBL
C4360022_CLEANED.IMG
C4360022_CLEANED.LBL
C4360022_full.jpg
C4360022_GEOMA.DAT
C4360022_GEOMA.LBL
C4360022_GEOMA.TAB
C4360022_GEOMED.IMG
C4360022_GEOMED.LBL
C4360022_med.jpg
C4360022_RAW.IMG
C4360022_RAW.LBL
C4360022_RESLOC.DAT
C4360022_RESLOC.LBL
C4360022_RESLOC.TAB
C4360022_small.jpg
C4360022_thumb.jpg
data.csv
manifest.csv
urls.txt
VGISS_6210_inventory.lbl
VGISS_6210_inventory.csv
VGISS_6210_moon_summary.lbl
VGISS_6210_moon_summary.tab
VGISS_6210_ring_summary.lbl
VGISS_6210_ring_summary.tab
VGISS_6210_saturn_summary.lbl
VGISS_6210_saturn_summary.tab
%ENDCODE%

* Download all product types (with no data files) for a Voyager ISS observation:

    %EXTLINK%%HOST%/opus/api/download/vg-iss-2-s-c4360022.zip?urlonly=1%ENDEXTLINK%

    Return value is a zip archive containing the files:

%CODE%
data.csv
manifest.csv
urls.txt
%ENDCODE%

* Download only raw image files for a Galileo SSI observation.

    %EXTLINK%%HOST%/opus/api/download/go-ssi-c0349632000.zip?types=gossi_raw%ENDEXTLINK%

    Return value is a zip archive containing the files:

%CODE%
C0349632000R.IMG
C0349632000R.LBL
data.csv
manifest.csv
RLINEPRX.FMT
RTLMTAB.FMT
urls.txt
%ENDCODE%





<h3 id="filesjson"><code>api/files.json</code> - Return URLs of Files from a Search</h3>

Get a list of all (or some) product files for the search results.

Supported return formats: `json`.

#### Parameters

| Parameter | Description | Default |
|---|---|---|
| `<searchid>=<value>` | Search parameters (including sort order) | All observations in database |
| `startobs=<N>` | The (1-based) observation number to start with | 1 |
| `limit=<N>` | The maximum number of observations to return | 100 |
| `types=<types>` | List of product types to return | All product types |

The `types` parameter is a list of download product types. Available types can be retrieved with the [`api/product_types.json`](#producttypesfmt) or [`api/product_types/[opusid].json`](#producttypesopusidfmt) API calls. The `@` modifier can be used to specify the version for a product type. If the version is not specified for a product type, the "Current" version will be returned.

#### JSON Return Format

The return value is a JSON object containing these fields:

| Field Name | Description |
|---|---|
| `start_obs` | Requested starting observation |
| `limit` | Requested limit |
| `count` | Number of observations actually returned |
| `available` | Total number of observations available from this search |
| `order` | Sort order |
| `data` | The file information for the current version |
| `versions` | The file information for all versions (including the current one) |

`data` and `versions` are both objects indexed by opusid. `versions` is further indexed by version number. Both are then indexed by product type, which gives a list of URLs of associated files.

Example (see [`api/files/[opusid].json`](#fileopusidjson) for more):

* Retrieve all files associated with images of Pan in volume COISS_2111 in JSON format.

    %EXTLINK%%HOST%/opus/api/files.json?volumeid=COISS_2111&target=pan%ENDEXTLINK%

    Return value:

%CODE%
{
  "start_obs": 1,
  "limit": 100,
  "count": 56,
  "available": 56,
  "order": "time1,opusid",
  "data": {
    "co-iss-n1867599811": {
      "coiss_raw": [
        "https://opus.pds-rings.seti.org/holdings/volumes/COISS_2xxx/COISS_2111/data/1867558636_1867602962/N1867599811_1.IMG",
        "https://opus.pds-rings.seti.org/holdings/volumes/COISS_2xxx/COISS_2111/data/1867558636_1867602962/N1867599811_1.LBL",
        "https://opus.pds-rings.seti.org/holdings/volumes/COISS_2xxx/COISS_2111/label/prefix3.fmt",
        "https://opus.pds-rings.seti.org/holdings/volumes/COISS_2xxx/COISS_2111/label/tlmtab.fmt"
      ],
      "coiss_calib": [
        "https://opus.pds-rings.seti.org/holdings/calibrated/COISS_2xxx/COISS_2111/data/1867558636_1867602962/N1867599811_1_CALIB.IMG",
        "https://opus.pds-rings.seti.org/holdings/calibrated/COISS_2xxx/COISS_2111/data/1867558636_1867602962/N1867599811_1_CALIB.LBL"
      ],
      "coiss_thumb": [
        "https://opus.pds-rings.seti.org/holdings/volumes/COISS_2xxx/COISS_2111/extras/thumbnail/1867558636_1867602962/N1867599811_1.IMG.jpeg_small"
      ],
      [...]
    },
    "co-iss-n1867600166": {
      "coiss_raw": [
        "https://opus.pds-rings.seti.org/holdings/volumes/COISS_2xxx/COISS_2111/data/1867558636_1867602962/N1867600166_1.IMG",
        "https://opus.pds-rings.seti.org/holdings/volumes/COISS_2xxx/COISS_2111/data/1867558636_1867602962/N1867600166_1.LBL",
        "https://opus.pds-rings.seti.org/holdings/volumes/COISS_2xxx/COISS_2111/label/prefix3.fmt",
        "https://opus.pds-rings.seti.org/holdings/volumes/COISS_2xxx/COISS_2111/label/tlmtab.fmt"
      ],
      [...]
  },
  [...]
}
%ENDCODE%





<h3 id="filesopusidjson"><code>api/files/[opusid].json</code> - Return URLs of Files for an OPUS ID</h3>

Get the URLs of all (or some) product files available for a single observation.

Supported return formats: `json`.

#### Parameters

| Parameter | Description | Default |
|---|---|---|
| `types=<types>` | List of product types to return | All product types |

The `types` parameter is a list of download product types. Available types can be retrieved with the [`api/product_types.json`](#producttypesfmt) or [`api/product_types/[opusid].json`](#producttypesopusidfmt) API calls. The `@` modifier can be used to specify the version for a product type. If the version is not specified for a product type, the "Current" version will be returned.

#### JSON Return Format

The return value is a JSON object containing these fields:

| Field Name | Description |
|---|---|
| `data` | The file information for the current version |
| `versions` | The file information for all versions (including the current one) |

`data` and `versions` are both objects indexed by opusid. `versions` is further indexed by version number. Both are then indexed by product type, which gives a list of URLs of associated files.

Examples:

* Retrieve all files associated with a Voyager ISS observation in JSON format.

    %EXTLINK%%HOST%/opus/api/files/vg-iss-2-s-c4360022.json%ENDEXTLINK%

    Return value:

%CODE%
{
  "data": {
    "vg-iss-2-s-c4360022": {
      "vgiss_raw": [
        "https://opus.pds-rings.seti.org/holdings/volumes/VGISS_6xxx/VGISS_6210/DATA/C43600XX/C4360022_RAW.IMG",
        "https://opus.pds-rings.seti.org/holdings/volumes/VGISS_6xxx/VGISS_6210/DATA/C43600XX/C4360022_RAW.LBL"
      ],
      "vgiss_cleaned": [
        "https://opus.pds-rings.seti.org/holdings/volumes/VGISS_6xxx/VGISS_6210/DATA/C43600XX/C4360022_CLEANED.IMG",
        "https://opus.pds-rings.seti.org/holdings/volumes/VGISS_6xxx/VGISS_6210/DATA/C43600XX/C4360022_CLEANED.LBL"
      ],
      "vgiss_calib": [
        "https://opus.pds-rings.seti.org/holdings/volumes/VGISS_6xxx/VGISS_6210/DATA/C43600XX/C4360022_CALIB.IMG",
        "https://opus.pds-rings.seti.org/holdings/volumes/VGISS_6xxx/VGISS_6210/DATA/C43600XX/C4360022_CALIB.LBL"
      ],
      [...]
    }
  },
  "versions": {
    "vg-iss-2-s-c4360022": {
      "Current": {
        "vgiss_raw": [
          "https://opus.pds-rings.seti.org/holdings/volumes/VGISS_6xxx/VGISS_6210/DATA/C43600XX/C4360022_RAW.IMG",
          "https://opus.pds-rings.seti.org/holdings/volumes/VGISS_6xxx/VGISS_6210/DATA/C43600XX/C4360022_RAW.LBL"
        ],
        "vgiss_cleaned": [
          "https://opus.pds-rings.seti.org/holdings/volumes/VGISS_6xxx/VGISS_6210/DATA/C43600XX/C4360022_CLEANED.IMG",
          "https://opus.pds-rings.seti.org/holdings/volumes/VGISS_6xxx/VGISS_6210/DATA/C43600XX/C4360022_CLEANED.LBL"
        ],
        "vgiss_calib": [
          "https://opus.pds-rings.seti.org/holdings/volumes/VGISS_6xxx/VGISS_6210/DATA/C43600XX/C4360022_CALIB.IMG",
          "https://opus.pds-rings.seti.org/holdings/volumes/VGISS_6xxx/VGISS_6210/DATA/C43600XX/C4360022_CALIB.LBL"
        ],
        [...]
      }
    }
  }
}    
%ENDCODE%

* Retrieve raw images ("Current" version) only for a Galileo SSI observation in JSON format.

    %EXTLINK%%HOST%/opus/api/files/go-ssi-c0349632000.json?types=gossi_raw%ENDEXTLINK%

    Return value:

%CODE%
{
  "data": {
    "go-ssi-c0349632000": {
      "gossi_raw": [
        "https://opus.pds-rings.seti.org/holdings/volumes/GO_0xxx/GO_0017/G1/GANYMEDE/C0349632000R.IMG",
        "https://opus.pds-rings.seti.org/holdings/volumes/GO_0xxx/GO_0017/G1/GANYMEDE/C0349632000R.LBL",
        "https://opus.pds-rings.seti.org/holdings/volumes/GO_0xxx/GO_0017/LABEL/RLINEPRX.FMT",
        "https://opus.pds-rings.seti.org/holdings/volumes/GO_0xxx/GO_0017/LABEL/RTLMTAB.FMT"
      ]
    }
  },
  "versions": {
    "go-ssi-c0349632000": {
      "Current": {
        "gossi_raw": [
          "https://opus.pds-rings.seti.org/holdings/volumes/GO_0xxx/GO_0017/G1/GANYMEDE/C0349632000R.IMG",
          "https://opus.pds-rings.seti.org/holdings/volumes/GO_0xxx/GO_0017/G1/GANYMEDE/C0349632000R.LBL",
          "https://opus.pds-rings.seti.org/holdings/volumes/GO_0xxx/GO_0017/LABEL/RLINEPRX.FMT",
          "https://opus.pds-rings.seti.org/holdings/volumes/GO_0xxx/GO_0017/LABEL/RTLMTAB.FMT"
        ]
      }
    }
  }
}
%ENDCODE%

* Retrieve raw images ("Current" version) and calibrated images (version 1.0) for a Cassini ISS observation in JSON format.

    %EXTLINK%%HOST%/opus/api/files/co-iss-n1460973661.json?types=coiss_raw,coiss_calib@v1%ENDEXTLINK%

    Return value:

%CODE%
{
  "data": {
    "co-iss-n1460973661": {
      "coiss_raw": [
        "https://opus.pds-rings.seti.org/holdings/volumes/COISS_2xxx/COISS_2002/data/1460960653_1461048959/N1460973661_1.IMG",
        "https://opus.pds-rings.seti.org/holdings/volumes/COISS_2xxx/COISS_2002/data/1460960653_1461048959/N1460973661_1.LBL",
        "https://opus.pds-rings.seti.org/holdings/volumes/COISS_2xxx/COISS_2002/label/prefix2.fmt",
        "https://opus.pds-rings.seti.org/holdings/volumes/COISS_2xxx/COISS_2002/label/tlmtab.fmt"
      ]
    }
  },
  "versions": {
    "co-iss-n1460973661": {
      "1": {
        "coiss_calib": [
          "https://opus.pds-rings.seti.org/holdings/calibrated/COISS_2xxx_v1/COISS_2002/data/1460960653_1461048959/N1460973661_1_CALIB.IMG",
          "https://opus.pds-rings.seti.org/holdings/calibrated/COISS_2xxx_v1/COISS_2002/data/1460960653_1461048959/N1460973661_1_CALIB.LBL"
        ]
      },
      "Current": {
        "coiss_raw": [
          "https://opus.pds-rings.seti.org/holdings/volumes/COISS_2xxx/COISS_2002/data/1460960653_1461048959/N1460973661_1.IMG",
          "https://opus.pds-rings.seti.org/holdings/volumes/COISS_2xxx/COISS_2002/data/1460960653_1461048959/N1460973661_1.LBL",
          "https://opus.pds-rings.seti.org/holdings/volumes/COISS_2xxx/COISS_2002/label/prefix2.fmt",
          "https://opus.pds-rings.seti.org/holdings/volumes/COISS_2xxx/COISS_2002/label/tlmtab.fmt"
        ]
      }
    }
  }
}
%ENDCODE%

* Retrieve drizzle images from an HST WFC3 observation with multiple versions in JSON format.

    %EXTLINK%%HOST%/opus/api/files/hst-11559-wfc3-ib4v19rp.json%ENDEXTLINK%

    Return value:

%CODE%
{
  "data": {
    "hst-11559-wfc3-ib4v19rp": {
      "hst_calib": [
        "https://opus.pds-rings.seti.org/holdings/volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_19/IB4V19RPQ_FLT.JPG",
        "https://opus.pds-rings.seti.org/holdings/volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_19/IB4V19RPQ.LBL"
      ],
      "hst_drizzled": [
        "https://opus.pds-rings.seti.org/holdings/volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_19/IB4V19RPQ_DRZ.JPG",
        "https://opus.pds-rings.seti.org/holdings/volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_19/IB4V19RPQ.LBL"
      ]
    }
  },
  "versions": {
    "hst-11559-wfc3-ib4v19rp": {
      "Current": {
        "hst_calib": [
          "https://opus.pds-rings.seti.org/holdings/volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_19/IB4V19RPQ_FLT.JPG",
          "https://opus.pds-rings.seti.org/holdings/volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_19/IB4V19RPQ.LBL"
        ],
        "hst_drizzled": [
          "https://opus.pds-rings.seti.org/holdings/volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_19/IB4V19RPQ_DRZ.JPG",
          "https://opus.pds-rings.seti.org/holdings/volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_19/IB4V19RPQ.LBL"
        ]
      },
      "1.1": {
        "hst_calib": [
          "https://opus.pds-rings.seti.org/holdings/volumes/HSTIx_xxxx_v1.1/HSTI1_1559/DATA/VISIT_19/IB4V19RPQ_FLT.JPG",
          "https://opus.pds-rings.seti.org/holdings/volumes/HSTIx_xxxx_v1.1/HSTI1_1559/DATA/VISIT_19/IB4V19RPQ.LBL"
        ],
        "hst_drizzled": [
          "https://opus.pds-rings.seti.org/holdings/volumes/HSTIx_xxxx_v1.1/HSTI1_1559/DATA/VISIT_19/IB4V19RPQ_DRZ.JPG",
          "https://opus.pds-rings.seti.org/holdings/volumes/HSTIx_xxxx_v1.1/HSTI1_1559/DATA/VISIT_19/IB4V19RPQ.LBL"
        ]
      },
      "1.0": {
        "hst_calib": [
          "https://opus.pds-rings.seti.org/holdings/volumes/HSTIx_xxxx_v1.0/HSTI1_1559/DATA/VISIT_19/IB4V19RPQ_FLT.JPG",
          "https://opus.pds-rings.seti.org/holdings/volumes/HSTIx_xxxx_v1.0/HSTI1_1559/DATA/VISIT_19/IB4V19RPQ.LBL"
        ],
        "hst_drizzled": [
          "https://opus.pds-rings.seti.org/holdings/volumes/HSTIx_xxxx_v1.0/HSTI1_1559/DATA/VISIT_19/IB4V19RPQ_DRZ.JPG",
          "https://opus.pds-rings.seti.org/holdings/volumes/HSTIx_xxxx_v1.0/HSTI1_1559/DATA/VISIT_19/IB4V19RPQ.LBL"
        ]
      }
    }
  }
}
%ENDCODE%





<h3 id="imagesfmt"><code>api/images.[fmt]</code> - Return URLs of All Images from a Search</h3>
<h3><code>api/images/[size].[fmt]</code> - Return URLs of Images of a Specific Size from a Search</h3>
<h3><code>api/image/[size]/[opusid].[fmt]</code> - Return URLs of Images of a Specific Size for an OPUS ID</h3>

Get the URLs of images of all sizes (or a given size) based on search criteria and sort order. Image URLs are returned in chunks to limit return size. The starting observation number and the number of observations desired can be specified. An image of a specific size may also be returned for a single OPUS ID.

If specified, `[size]` must be one of `full`, `med`, `small`, or `thumb`.

Supported return formats: `json`, `csv`. `html` is also supported when a specified size is requested.

#### Parameters

| Parameter | Description | Default |
|---|---|---|
| `<searchid>=<value>` | Search parameters (including sort order) | All observations in database |
| `startobs=<N>` | The (1-based) observation number to start with | 1 |
| `limit=<N>` | The maximum number of observations to return | 100 |

#### JSON Return Format

The return value is a JSON object containing this field:

| Field Name | Description |
|---|---|
| `data` | The images data with one entry per returned observation |

When a search was requested, the JSON object also includes these fields:

| Field Name | Description |
|---|---|
| `start_obs` | Requested starting observation |
| `limit` | Requested limit |
| `count` | Number of observations actually returned |
| `available` | Total number of observations available from this search |
| `order` | Sort order |
| `labels` | Requested metadata field names (fully qualified) |

When all sizes are requested, `data` is an object containing a series of entries, each with these fields:

| Field Name | Description |
|---|---|
| `opusid` | OPUS ID of the observation |
| `<size>_alt_text` | Alternate text (image filename) |
| `<size>_size_bytes` | Size of the image file in bytes |
| `<size>_width` | Width of the image in pixels |
| `<size>_height` | Height of the image in pixels |
| `<size>_url` | Full URL path to the image |

When one size is requested, `data` an object containing a single entry with these fields:

| Field Name | Description |
|---|---|
| `opusid` | OPUS ID of the observation |
| `alt_text` | Alternate text (image filename) |
| `size_bytes` | Size of the image file in bytes |
| `width` | Width of the image in pixels |
| `height` | Height of the image in pixels |
| `url` | Full URL path to the image |

Examples:

* Retrieve information in JSON format about all sizes of images for observations 10-11 from Cassini ISS volume COISS_2002.

    %EXTLINK%%HOST%/opus/api/images.json?volumeid=COISS_2002&startobs=10&limit=2%ENDEXTLINK%

    Return value:

%CODE%
{
  "start_obs": 10,
  "limit": 2,
  "count": 2,
  "available": 3296,
  "order": "time1,opusid"
  "data": [
    {
      "opusid": "co-iss-n1460962327",
      "thumb_url": "https://opus.pds-rings.seti.org/holdings/previews/COISS_2xxx/COISS_2002/data/1460960653_1461048959/N1460962327_1_thumb.jpg",
      "thumb_alt_text": "N1460962327_1_thumb.jpg",
      "thumb_size_bytes": 864,
      "thumb_width": 100,
      "thumb_height": 100,
      "small_url": "https://opus.pds-rings.seti.org/holdings/previews/COISS_2xxx/COISS_2002/data/1460960653_1461048959/N1460962327_1_small.jpg",
      "small_alt_text": "N1460962327_1_small.jpg",
      "small_size_bytes": 1729,
      "small_width": 256,
      "small_height": 256,
      [...]
    },
    [...]
  ]
}
%ENDCODE%

* Retrieve information in JSON format about medium-size images for observations 10-11 from Cassini ISS volume COISS_2002.

    %EXTLINK%%HOST%/opus/api/images/med.json?volumeid=COISS_2002&startobs=10&limit=2%ENDEXTLINK%

    Return value:

%CODE%
{
  "start_obs": 10,
  "limit": 2,
  "count": 2,
  "available": 3296,
  "order": "time1,opusid",
  "data": [
    {
      "opusid": "co-iss-n1460962327",
      "alt_text": "N1460962327_1_med.jpg",
      "size_bytes": 4971,
      "width": 512,
      "height": 512,
      "url": "https://opus.pds-rings.seti.org/holdings/previews/COISS_2xxx/COISS_2002/data/1460960653_1461048959/N1460962327_1_med.jpg"
    },
    {
      "opusid": "co-iss-n1460962415",
      "alt_text": "N1460962415_1_med.jpg",
      "size_bytes": 4991,
      "width": 512,
      "height": 512,
      "url": "https://opus.pds-rings.seti.org/holdings/previews/COISS_2xxx/COISS_2002/data/1460960653_1461048959/N1460962415_1_med.jpg"
    }
  ]
}
%ENDCODE%

* Retrieve information in JSON format about the full-size image for OPUS ID vg-iss-2-s-c4360022.

    %EXTLINK%%HOST%/opus/api/image/full/vg-iss-2-s-c4360022.json%ENDEXTLINK%

    Return value:

%CODE%
{
  "data": [
    {
      "opusid": "vg-iss-2-s-c4360022",
      "alt_text": "C4360022_full.jpg",
      "size_bytes": 24607,
      "width": 800,
      "height": 800,
      "url": "https://opus.pds-rings.seti.org/holdings/previews/VGISS_6xxx/VGISS_6210/DATA/C43600XX/C4360022_full.jpg"
    }
  ]
}
%ENDCODE%

#### CSV Return Format

The return value is a series of text lines. The first returned line contains the column headers. After that is one line per observation containing the information about each image.

Example:

* Retrieve information in CSV format about all sizes of images for observations 10-11 from Cassini ISS volume COISS_2002.

    %EXTLINK%%HOST%/opus/api/images.csv?volumeid=COISS_2002&startobs=10&limit=2%ENDEXTLINK%

    Return value:

%CODE%
OPUS ID,Thumb URL,Small URL,Med URL,Full URL
co-iss-n1460962327,https://opus.pds-rings.seti.org/holdings/previews/COISS_2xxx/COISS_2002/data/1460960653_1461048959/N1460962327_1_full.png
co-iss-n1460962415,https://opus.pds-rings.seti.org/holdings/previews/COISS_2xxx/COISS_2002/data/1460960653_1461048959/N1460962415_1_full.png
%ENDCODE%

* Retrieve information in CSV format about medium-size images for observations 10-11 from Cassini ISS volume COISS_2002.

    %EXTLINK%%HOST%/opus/api/images/med.csv?volumeid=COISS_2002&startobs=10&limit=2%ENDEXTLINK%

    Return value:

%CODE%
OPUS ID,URL
co-iss-n1460962327,https://opus.pds-rings.seti.org/holdings/previews/COISS_2xxx/COISS_2002/data/1460960653_1461048959/N1460962327_1_med.jpg
co-iss-n1460962415,https://opus.pds-rings.seti.org/holdings/previews/COISS_2xxx/COISS_2002/data/1460960653_1461048959/N1460962415_1_med.jpg
%ENDCODE%

* Retrieve information in CSV format about the full-size image for OPUS ID vg-iss-2-s-c4360022.

    %EXTLINK%%HOST%/opus/api/image/full/vg-iss-2-s-c4360022.csv%ENDEXTLINK%

    Return value:

%CODE%
OPUS ID,URL
vg-iss-2-s-c4360022,https://opus.pds-rings.seti.org/holdings/previews/VGISS_6xxx/VGISS_6210/DATA/C43600XX/C4360022_full.jpg
%ENDCODE%

#### HTML Return Format

The return is an HTML list containing the URLs of the requested images.

Example:

* Retrieve information in HTML format about medium-size images for observations 10-11 from Cassini ISS volume COISS_2002.

    %EXTLINK%%HOST%/opus/api/images/med.html?volumeid=COISS_2002&startobs=10&limit=2%ENDEXTLINK%

    Return value:

%ADDCLASS%op-api-guide-code-block%ENDADDCLASS%

    <ul>
    <li>
    <img id="med__co-iss-n1460962327" src="https://opus.pds-rings.seti.org/holdings/previews/COISS_2xxx/COISS_2002/data/1460960653_1461048959/N1460962327_1_med.jpg">
    </li>
    <li>
    <img id="med__co-iss-n1460962415" src="https://opus.pds-rings.seti.org/holdings/previews/COISS_2xxx/COISS_2002/data/1460960653_1461048959/N1460962415_1_med.jpg">
    </li>
    </ul>
%ENDCLASS%

* Retrieve information in HTML format about the full-size image for OPUS ID vg-iss-2-s-c4360022.

    %EXTLINK%%HOST%/opus/api/image/full/vg-iss-2-s-c4360022.html%ENDEXTLINK%

    Return value:

%ADDCLASS%op-api-guide-code-block%ENDADDCLASS%

    <ul>
    <li>
    <img id="full__vg-iss-2-s-c4360022" src="https://opus.pds-rings.seti.org/holdings/previews/VGISS_6xxx/VGISS_6210/DATA/C43600XX/C4360022_full.jpg">
    </li>
    </ul>
%ENDCLASS%





<h2 id="infosearchresults">Getting Information About Search Results</h2>

<h3 id="resultcountfmt"><code>api/meta/result_count.[fmt]</code> - Result Count for a Search</h3>

Get the result count for a search.

Supported return formats: `json`, `html`, `csv`

#### Parameters

| Parameter | Description | Default |
|---|---|---|
| `<searchid>=<value>` | Search parameters (including sort order) | All observations in database |

Specifying a sort order will not change the number of results, but will be used to cache the actual results in order so that future attempts to perform the search will be faster. Thus if you are planning to perform the search again to retrieve metadata, it is recommended to specify a sort order (if not using the default order) when calling `api/meta/result_count.[fmt]` as well.

#### JSON Return Format

The return value is a JSON object containing these fields:

| Field Name | Description |
|---|---|
| `data` | An object containing a single `result_count` field |

Example:

* Retrieve the number of observations with Pan as the target in JSON format.

    %EXTLINK%%HOST%/opus/api/meta/result_count.json?target=Pan%ENDEXTLINK%

    Return value:

%CODE%
{
  "data": [
    {
      "result_count": 1636
    }
  ]
}
%ENDCODE%

#### CSV Return Format

The return value is a single text line with the label "result count" followed by the number of results.

* Retrieve the number of observations with Pan as the target in CSV format.

    %EXTLINK%%HOST%/opus/api/meta/result_count.csv?target=Pan%ENDEXTLINK%

    Return value:

%CODE%
result count,1636
%ENDCODE%

#### HTML Return Format

The return value is an HTML description list containing a single item specifying the label `result_count` and the number of results.

* Retrieve the number of observations with Pan as the target in HTML format.

    %EXTLINK%%HOST%/opus/api/meta/result_count.csv?target=Pan%ENDEXTLINK%

    Return value:

%ADDCLASS%op-api-guide-code-block%ENDADDCLASS%

    <dl>
    <dt>result_count</dt><dd>1636</dd>
    </dl>
%ENDCLASS%





<h3 id="multsfmt"><code>api/meta/mults/[field].[fmt]</code> - Return Possible Values for a Multiple-Choice Field</h3>

Returns all possible values for a multiple-choice field and the result count for each value if that value were added to the search constraints.

Supported return formats: `json`, `html`, `csv`

#### Parameters

| Parameter | Description | Default |
|---|---|---|
| `<searchid>=<value>` | Search parameters (including sort order) | All observations in database |

Specifying a sort order will not change the results, but will be used to cache the actual results in order so that future attempts to perform the search will be faster. Thus if you are planning to perform the search again to retrieve metadata, it is recommended to specify a sort order (if not using the default order) when calling `api/meta/mults/[field].[fmt]` as well.

#### JSON Return Format

The return value is a JSON object containing these fields:

| Field Name | Description |
|---|---|
| `field_id` | The `fieldid` requested |
| `mults` | A JSON object containing the result counts for each choice |

Example:

* Retrieve the number of results broken down by `planet` for Hubble observations in JSON format.

    %EXTLINK%%HOST%/opus/api/meta/mults/planet.json?mission=Hubble%ENDEXTLINK%

    Return value:

%CODE%
{
  "field_id": "planet",
  "mults": {
    "Earth": 10,
    "Mars": 354,
    "Jupiter": 7956,
    "Saturn": 4885,
    "Uranus": 3395,
    "Neptune": 1800,
    "Pluto": 2051,
    "Other": 892
  }
}
%ENDCODE%

#### CSV Return Format

The return value is two text lines. The first is a list of choices. The second is a list of result counts broken down by choice.

* Retrieve the number of results broken down by `planet` for Hubble observations in CSV format.

    %EXTLINK%%HOST%/opus/api/meta/mults/planet.csv?mission=Hubble%ENDEXTLINK%

    Return value:

%CODE%
Earth,Mars,Jupiter,Saturn,Uranus,Neptune,Pluto,Other
10,354,7956,4885,3395,1800,2051,892
%ENDCODE%

#### HTML Return Format

The return value is an HTML description list containing the choices and the result counts broken down by choice.

Example:

* Retrieve the number of results in HTML format broken down by `planet` for Hubble observations.

    %EXTLINK%%HOST%/opus/api/meta/mults/planet.csv?mission=Hubble%ENDEXTLINK%

    Return value:

%ADDCLASS%op-api-guide-code-block%ENDADDCLASS%

    <dl>
    <dt>Earth</dt><dd>10</dd>
    <dt>Mars</dt><dd>354</dd>
    <dt>Jupiter</dt><dd>7956</dd>
    <dt>Saturn</dt><dd>4885</dd>
    <dt>Uranus</dt><dd>3395</dd>
    <dt>Neptune</dt><dd>1800</dd>
    <dt>Pluto</dt><dd>2051</dd>
    <dt>Other</dt><dd>892</dd>
    </dl>
%ENDCLASS%





<h3 id="endpointsfmt"><code>api/meta/range/endpoints/[field].[fmt]</code> - Return Range Endpoints for a Numeric Field</h3>

Return range endpoints for a numeric field, given a search.

Supported return formats: `json`, `html`, `csv`

#### Parameters

| Parameter | Description | Default |
|---|---|---|
| `<searchid>=<value>` | Search parameters (including sort order) | All observations in database |
| `units=<unit>` | The units to use for the returned values | The default unit for the field |

Specifying a sort order will not change the results, but will be used to cache the actual results in order so that future attempts to perform the search will be faster. Thus if you are planning to perform the search again to retrieve metadata, it is recommended to specify a sort order (if not using the default order) when calling `api/meta/range/endpoints/[field].[fmt]` as well.

#### JSON Return Format

The return value is a JSON object containing these fields:

| Field Name | Description |
|---|---|
| `min` | The minimum value for the field |
| `max` | The maximum value for the field |
| `nulls` | The number of null values for the field |
| `units` | The units of the returned `min` and `max` fields |

Examples:

* Retrieve the range endpoints in the default units (km) for Observed Ring Radius for all Saturn observations in JSON format.

    %EXTLINK%%HOST%/opus/api/meta/range/endpoints/RINGGEOringradius1.json?target=Saturn%ENDEXTLINK%

    Return value:

%CODE%
{
  "min": "334.161",
  "max": "12873823.895",
  "nulls": 125566,
  "units": "km"
}
%ENDCODE%

* Retrieve the range endpoints in units of Saturn radii for Observed Ring Radius for all Saturn observations in JSON format.

    %EXTLINK%%HOST%/opus/api/meta/range/endpoints/RINGGEOringradius1.json?target=Saturn&units=saturnradii%ENDEXTLINK%

    Return value:

%CODE%
{
  "min": "0.00553888613",
  "max": "213.39008610973",
  "nulls": 125566,
  "units": "saturnradii"
}
%ENDCODE%

#### CSV Return Format

The return value is a series of text lines. The first line contains the column labels `min,max,nulls,units`. The second line contains the associated values.

Examples:

* Retrieve the range endpoints in the default units (km) for Observed Ring Radius for all Saturn observations in CSV format.

    %EXTLINK%%HOST%/opus/api/meta/range/endpoints/RINGGEOringradius1.csv?target=Saturn%ENDEXTLINK%

    Return value:

%CODE%
min,max,nulls,units
334.161,12873823.895,125566,km
%ENDCODE%

* Retrieve the range endpoints in units of Saturn radii for Observed Ring Radius for all Saturn observations in CSV format.

    %EXTLINK%%HOST%/opus/api/meta/range/endpoints/RINGGEOringradius1.json?target=Saturn&units=saturnradii%ENDEXTLINK%

    Return value:

%CODE%
min,max,nulls,units
0.00553888613,213.39008610973,125566,saturnradii
%ENDCODE%

#### HTML Return Format

The return value is an HTML description list containing name/value pairs where the name is the label and the value is the associated value.

Examples:

* Retrieve the range endpoints in the default units (km) for Observed Ring Radius for all Saturn observations in HTML format.

    %EXTLINK%%HOST%/opus/api/meta/range/endpoints/RINGGEOringradius1.html?target=Saturn%ENDEXTLINK%

    Return value:

%ADDCLASS%op-api-guide-code-block%ENDADDCLASS%

    <dl>
    <dt>min</dt><dd>334.161</dd>
    <dt>max</dt><dd>12873823.895</dd>
    <dt>nulls</dt><dd>125566</dd>
    <dt>units</dt><dd>km</dd>
    </dl>
%ENDCLASS%

* Retrieve the range endpoints in units of Saturn radii for Observed Ring Radius for all Saturn observations in HTML format.

    %EXTLINK%%HOST%/opus/api/meta/range/endpoints/RINGGEOringradius1.html?target=Saturn&units=saturnradii%ENDEXTLINK%

    Return value:

%ADDCLASS%op-api-guide-code-block%ENDADDCLASS%

    <dl>
    <dt>min</dt><dd>0.00553888613</dd>
    <dt>max</dt><dd>213.39008610973</dd>
    <dt>nulls</dt><dd>125566</dd>
    <dt>units</dt><dd>saturnradii</dd>
    </dl>
%ENDCLASS%





<h3 id="categoriesfmt"><code>api/categories.json</code> - Return Categories from a Search</h3>

Return all category names common to the results of a particular search.

Supported return formats: `json`

#### Parameters

| Parameter | Description | Default |
|---|---|---|
| `<searchid>=<value>` | Search parameters (including sort order) | All observations in database |

Specifying a sort order will not change the results, but will be used to cache the actual results in order so that future attempts to perform the search will be faster. Thus if you are planning to perform the search again to retrieve metadata, it is recommended to specify a sort order (if not using the default order) when calling `api/categories.json` as well.

#### JSON Return Format

The return value is a JSON list of objects each containing information about one category that contains data for all of the observations resulting from the given search. Each category is described by:

| Field Name | Description |
|---|---|
| `table_name` | The internal database table table (e.g. `obs_general`) |
| `label` | The pretty label as displayed to the user (e.g. `General Constraints`) |

Example:

* Retrieve the categories for all observations that have surface geometry information about Methone in JSON format.

    %EXTLINK%%HOST%/opus/api/categories.json?surfacegeometrytargetname=Methone%ENDEXTLINK%

    Return value:

%CODE%
[
  {
    "table_name": "obs_general",
    "label": "General Constraints"
  },
  {
    "table_name": "obs_pds",
    "label": "PDS Constraints"
  },
  {
    "table_name": "obs_type_image",
    "label": "Image Constraints"
  },
  {
    "table_name": "obs_wavelength",
    "label": "Wavelength Constraints"
  },
  {
    "table_name": "obs_profile",
    "label": "Occultation/Reflectance Profiles Constraints"
  },
  {
    "table_name": "obs_surface_geometry__methone",
    "label": "Methone Surface Geometry Constraints"
  },
  {
    "table_name": "obs_ring_geometry",
    "label": "Ring Geometry Constraints"
  }
]
%ENDCODE%





<h3 id="categoriesopusidfmt"><code>api/categories/[opusid].json</code> - Return Categories for an OPUS ID</h3>

Return a list of all categories an OPUS ID exists in.

Supported return formats: `json`

#### Parameters

There are no parameters.

#### JSON Return Format

The return value is a JSON list of objects each containing information about one category that contains data for the given OPUS ID. Each category is described by:

| Field Name | Description |
|---|---|
| `table_name` | The internal database table table (e.g. `obs_general`) |
| `label` | The pretty label as displayed to the user (e.g. `General Constraints`) |

Example:

* Retrieve the categories for a Cassini ISS observation in JSON format.

    %EXTLINK%%HOST%/opus/api/categories/co-iss-w1866600688.json%ENDEXTLINK%

    Return value:

%CODE%
[
  {
    "table_name": "obs_general",
    "label": "General Constraints"
  },
  {
    "table_name": "obs_pds",
    "label": "PDS Constraints"
  },
  {
    "table_name": "obs_type_image",
    "label": "Image Constraints"
  },
  {
    "table_name": "obs_wavelength",
    "label": "Wavelength Constraints"
  },
  {
    "table_name": "obs_profile",
    "label": "Occultation/Reflectance Profiles Constraints"
  },
  {
    "table_name": "obs_surface_geometry__daphnis",
    "label": "Daphnis Surface Geometry Constraints"
  },
  {
    "table_name": "obs_surface_geometry__epimetheus",
    "label": "Epimetheus Surface Geometry Constraints"
  },
  {
    "table_name": "obs_surface_geometry__saturn",
    "label": "Saturn Surface Geometry Constraints"
  },
  {
    "table_name": "obs_ring_geometry",
    "label": "Ring Geometry Constraints"
  },
  {
    "table_name": "obs_mission_cassini",
    "label": "Cassini Mission Constraints"
  },
  {
    "table_name": "obs_instrument_coiss",
    "label": "Cassini ISS Constraints"
  }
]
%ENDCODE%





<h3 id="producttypesfmt"><code>api/product_types.json</code> - Return Product Types from a Search</h3>

Return all download product types and associated product versions available from the results of a particular search.

Supported return formats: `json`

#### Parameters

| Parameter | Description | Default |
|---|---|---|
| `<searchid>=<value>` | Search parameters (including sort order) | All observations in database |

Specifying a sort order will not change the results, but will be used to cache the actual results in order so that future attempts to perform the search will be faster. Thus if you are planning to perform the search again to retrieve metadata, it is recommended to specify a sort order (if not using the default order) when calling `api/product_types.json` as well.

#### JSON Return Format

The return value is a JSON list of objects each containing information about one product type and version that is available for at least one observation returned by the given search. Each product type and version is described by:

| Field Name | Description |
|---|---|
| `category` | The category of the product type (e.g. `Cassini ISS`)|
| `product_type` | The abbreviated name of the product type (e.g. `coiss_raw`)|
| `description` | A brief description of the product type (e.g. `Raw Image`)|
| `version_number` | A numerical representation of the version number suitable for sorting (999999 means Current)|
| `version_name` | A string representation of the version number |

Example:

* Retrieve the product types and versions for all observations that have surface geometry information about Methone in JSON format.

    %EXTLINK%%HOST%/opus/api/product_types.json?surfacegeometrytargetname=Methone%ENDEXTLINK%

    Return value:

%CODE%
[
  {
    "category": "Cassini ISS",
    "product_type": "coiss_raw",
    "description": "Raw Image",
    "version_number": 999999,
    "version_name": "Current"
  },
  {
    "category": "Cassini ISS",
    "product_type": "coiss_calib",
    "description": "Calibrated Image",
    "version_number": 999999,
    "version_name": "Current"
  },
  {
    "category": "Cassini ISS",
    "product_type": "coiss_calib",
    "description": "Calibrated Image",
    "version_number": 10000,
    "version_name": "1.0"
  },
  [...]
]
%ENDCODE%





<h3 id="producttypesopusidfmt"><code>api/product_types/[opusid].json</code> - Return Product Types for an OPUS ID</h3>

Return a list of all download product types and associated product versions available for an OPUS ID.

Supported return formats: `json`

#### Parameters

There are no parameters.

#### JSON Return Format

The return value is a JSON list of objects each containing information about one product type and version that is available for the given OPUS ID. Each product type is described by:

| Field Name | Description |
|---|---|
| `category` | The category of the product type (e.g. `Cassini ISS`)|
| `product_type` | The abbreviated name of the product type (e.g. `coiss_raw`)|
| `description` | A brief description of the product type (e.g. `Raw Image`)|
| `version_number` | A numerical representation of the version number suitable for sorting (999999 means Current)|
| `version_name` | A string representation of the version number |

Example:

* Retrieve the product types and versions for a Cassini ISS observation in JSON format.

    %EXTLINK%%HOST%/opus/api/product_types/co-iss-w1866600688.json%ENDEXTLINK%

    Return value:

%CODE%
[
  {
    "category": "Cassini ISS",
    "product_type": "coiss_raw",
    "description": "Raw Image",
    "version_number": 999999,
    "version_name": "Current"
  },
  {
    "category": "Cassini ISS",
    "product_type": "coiss_calib",
    "description": "Calibrated Image",
    "version_number": 999999,
    "version_name": "Current"
  },
  {
    "category": "Cassini ISS",
    "product_type": "coiss_thumb",
    "description": "Extra Preview (thumbnail)",
    "version_number": 999999,
    "version_name": "Current"
  },
  [...]
]
%ENDCODE%





<h3 id="fieldsfmt"><code>api/fields.[fmt]</code> - Return Information About All Metadata Fields</h3>

Return information about all metadata fields.

Supported return formats: `json`, `csv`

#### Parameters

| Parameter | Description | Default |
|---|---|---|
| `collapse=<N>` | If `collapse=1` is given, collapse all surface geometry entries into single generic-target entries |

#### JSON Return Format

The return value is a JSON object containing this field:

| Field Name | Description |
|---|---|
| `data` | An object containing information about all fields |

`data` is an object indexed by `fieldid` containing:

| Field Name | Description |
|---|---|
| `field_id` | The `fieldid` |
| `category` | The full name of the category to which the field belongs |
| `type` | The data type of the field |
| `search_label` | The field name as shown on the Search tab (without Min/Max qualifiers) |
| `full_search_label` | The field name without Min/Max qualifiers but with the category name |
| `label` | The field name as shown when displaying results (with Min/Max qualifiers as appropriate) |
| `full_label` | The field name with Min/Max qualifiers (as appropriate) but with the category name |
| `available_units` | The units that can be used for searching with this field |
| `default_units` | The default units when none is specified |
| `linked` | `true` if this field is not native to this category but has been linked from its normal location |

`type` can be one of: `multiple`, `string`, `range_integer`, `range_float`,
`range_longitude`, `range_time`, or `range_special`.

Examples:

* Retrieve information about all fields in JSON format.

    %EXTLINK%%HOST%/opus/api/fields.json%ENDEXTLINK%

    Return value:

%CODE%
{
  "data": {
    "General Constraints": {
      "planet": {
        "field_id": "planet",
        "category": "General Constraints",
        "type": "multiple",
        "label": "Planet",
        "search_label": "Planet",
        "full_label": "Planet",
        "full_search_label": "Planet [General]",
        "default_units": null,
        "available_units": null,
        "old_slug": null,
        "slug": "planet",
        "linked": false
      },
      [...]
      "rightasc1": {
        "field_id": "rightasc1",
        "category": "General Constraints",
        "type": "range_longitude",
        "label": "Right Ascension (Min)",
        "search_label": "Right Ascension",
        "full_label": "Right Ascension (Min)",
        "full_search_label": "Right Ascension [General]",
        "default_units": "degrees",
        "available_units": [
          "degrees",
          "hourangle",
          "radians"
        ],
        "old_slug": null,
        "slug": "rightasc1",
        "linked": false
      },
      "rightasc2": {
        "field_id": "rightasc2",
        "category": "General Constraints",
        [...]
      },
      [...]
    },
    [...]
    "Umbriel Surface Geometry Constraints": {
      "SURFACEGEOumbriel_planetographiclatitude1": {
        "field_id": "SURFACEGEOumbriel_planetographiclatitude1",
        "category": "Umbriel Surface Geometry Constraints",
        "type": "range_float",
        "label": "Observed Planetographic Latitude (Min)",
        "search_label": "Observed Planetographic Latitude",
        "full_label": "Observed Planetographic Latitude (Min) [Umbriel]",
        "full_search_label": "Observed Planetographic Latitude [Umbriel]",
        "default_units": "degrees",
        "available_units": [
          "degrees",
          "hourangle",
          "radians"
        ],
        "old_slug": "SURFACEGEOumbrielplanetographiclatitude1",
        "slug": "SURFACEGEOumbriel_planetographiclatitude1",
        "linked": false
      },
      "SURFACEGEOumbriel_planetographiclatitude2": {
        "field_id": "SURFACEGEOumbriel_planetographiclatitude2",
        [...]
      },
      [...]
    },
    [...]
  }
}
%ENDCODE%

* Retrieve information about all fields in JSON format.

    %EXTLINK%%HOST%/opus/api/fields.json?collapse=1%ENDEXTLINK%

    Return value:

%CODE%
{
  "data": {
    [...]
    "&lt;TARGET&gt; Surface Geometry Constraints": {
      "SURFACEGEO&lt;TARGET&gt;_planetographiclatitude1": {
        "field_id": "SURFACEGEO&lt;TARGET&gt;_planetographiclatitude1",
        "category": "&lt;TARGET&gt; Surface Geometry Constraints",
        "type": "range_float",
        "label": "Observed Planetographic Latitude (Min)",
        "search_label": "Observed Planetographic Latitude",
        "full_label": "Observed Planetographic Latitude (Min) [Saturn]",
        "full_search_label": "Observed Planetographic Latitude [Saturn]",
        "default_units": "degrees",
        "available_units": [
          "degrees",
          "hourangle",
          "radians"
        ],
        "old_slug": "SURFACEGEO&lt;TARGET&gt;planetographiclatitude1",
        "slug": "SURFACEGEO&lt;TARGET&gt;_planetographiclatitude1",
        "linked": false
      },
      "SURFACEGEO&lt;TARGET&gt;_planetographiclatitude2": {
        "field_id": "SURFACEGEO&lt;TARGET&gt;_planetographiclatitude2",
        "category": "&lt;TARGET&gt; Surface Geometry Constraints",
        "type": "range_float",
        "label": "Observed Planetographic Latitude (Max)",
        "search_label": "Observed Planetographic Latitude",
        "full_label": "Observed Planetographic Latitude (Max) [Saturn]",
        "full_search_label": "Observed Planetographic Latitude [Saturn]",
        "default_units": "degrees",
        "available_units": [
          "degrees",
          "hourangle",
          "radians"
        ],
        "old_slug": "SURFACEGEO&lt;TARGET&gt;planetographiclatitude2",
        "slug": "SURFACEGEO&lt;TARGET&gt;_planetographiclatitude2",
        "linked": false
      },
      [...]
    },
    [...]
  }
}
%ENDCODE%

#### CSV Return Format

The return value is a series of text lines. The first line contains the column headers. After that is one line per metadata field containing the field information.

Example:

* Retrieve information about all fields in CSV format.

    %EXTLINK%%HOST%/opus/api/fields.csv%ENDEXTLINK%

    Return value:

%CODE%
Field ID,Category,Type,Search Label,Results Label,Full Search Label,Full Results Label,Default Units,Available Units,Old Field ID,Linked
planet,General Constraints,multiple,Planet,Planet,Planet [General],Planet,,,,0
target,General Constraints,multiple,Intended Target Name,Intended Target Name,Intended Target Name [General],Intended Target Name,,,,0
[...]
rightasc1,General Constraints,range_longitude,Right Ascension,Right Ascension (Min),Right Ascension [General],Right Ascension (Min),degrees,"['degrees', 'hourangle', 'radians']",,0
rightasc2,General Constraints,range_longitude,Right Ascension,Right Ascension (Max),Right Ascension [General],Right Ascension (Max),degrees,"['degrees', 'hourangle', 'radians']",,0
declination1,General Constraints,range_float,Declination,Declination (Min),Declination [General],Declination (Min),degrees,"['degrees', 'hourangle', 'radians']",,0
declination2,General Constraints,range_float,Declination,Declination (Max),Declination [General],Declination (Max),degrees,"['degrees', 'hourangle', 'radians']",,0
[...]
%ENDCODE%





<h3 id="fieldsfieldfmt"><code>api/fields/[field].[fmt]</code> - Return Information About a Metadata Field</h3>

Return information about a particular metadata field.

Supported return formats: `json`, `csv`

#### Parameters

There are no parameters.

#### JSON Return Format

The return value is a JSON object containing this field:

| Field Name | Description |
|---|---|
| `data` | An object containing information about the requested field |

`data` is an object indexed by `fieldid` containing:

| Field Name | Description |
|---|---|
| `field_id` | The `fieldid` |
| `category` | The full name of the category to which the field belongs |
| `search_label` | The field name as shown on the Search tab (without Min/Max qualifiers) |
| `full_search_label` | The field name without Min/Max qualifiers but with the category name |
| `label` | The field name as shown when displaying results (with Min/Max qualifiers as appropriate) |
| `full_label` | The field name with Min/Max qualifiers (as appropriate) but with the category name |
| `available_units` | The units that can be used for searching with this field |
| `default_units` | The default units when none is specified |
| `linked` | Always `false` because this API call returns information about the field's native category |

Examples:

* Retrieve information about the `planet` field in JSON format.

    %EXTLINK%%HOST%/opus/api/fields/planet.json%ENDEXTLINK%

    Return value:

%CODE%
{
  "data": {
    "General Constraints": {
      "planet": {
        "field_id": "planet",
        "category": "General Constraints",
        "type": "multiple",
        "label": "Planet",
        "search_label": "Planet",
        "full_label": "Planet",
        "full_search_label": "Planet [General]",
        "default_units": null,
        "available_units": null,
        "old_slug": null,
        "slug": "planet",
        "linked": false
      }
    }
  }
}
%ENDCODE%

* Retrieve information about the `SURFACEGEOrhea_centerphaseangle` field in JSON format.

    %EXTLINK%%HOST%/opus/api/fields/SURFACEGEOrhea_centerphaseangle.json%ENDEXTLINK%

    Return value:

%CODE%
{
  "data": {
    "Rhea Surface Geometry Constraints": {
      "SURFACEGEOrhea_centerphaseangle": {
        "field_id": "SURFACEGEOrhea_centerphaseangle",
        "category": "Rhea Surface Geometry Constraints",
        "type": "range_float",
        "label": "Phase Angle at Body Center",
        "search_label": "Phase Angle at Body Center",
        "full_label": "Phase Angle at Body Center [Rhea]",
        "full_search_label": "Phase Angle at Body Center [Rhea]",
        "default_units": "degrees",
        "available_units": [
          "degrees",
          "hourangle",
          "radians"
        ],
        "old_slug": "SURFACEGEOrheacenterphaseangle",
        "slug": "SURFACEGEOrhea_centerphaseangle",
        "linked": false
      }
    }
  }
}
%ENDCODE%

#### CSV Return Format

The return value is a series of text lines. The first line contains the column headers. After that is one line per metadata field containing the field information.

Example:

* Retrieve information about the `planet` field in CSV format.

    %EXTLINK%%HOST%/opus/api/fields/planet.csv%ENDEXTLINK%

    Return value:

%CODE%
Field ID,Category,Type,Search Label,Results Label,Full Search Label,Full Results Label,Default Units,Available Units,Old Field ID,Linked
planet,General Constraints,multiple,Planet,Planet,Planet [General],Planet,,,,0
%ENDCODE%

--------------------------------------------------------------------------------
