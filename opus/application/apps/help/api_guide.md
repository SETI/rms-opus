<h1 class="op-help-api-guide-no-count">OPUS API Guide</h1>

This guide describes the public API for the Outer Planets Unified Search (OPUS) tool of the PDS Ring-Moon Systems Node. It was produced on %DATE% and covers OPUS version %VERSION%.

Table of Contents:

%ADDCLASS%op-help-api-guide-toc%ENDADDCLASS%

* [Basic Concepts](#basicconcepts)
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
    * [Getting Data](#gettingdata)
        * [`api/data.[fmt]` - Return Metadata from a Search](#datafmt)
        * [`api/metadata_v2/[opusid].[fmt]` - Return Metadata for an OPUSID](#metadatav2fmt)
        * [`api/images.[fmt]` - Return Images from a Search](#imagesfmt)
        * [`api/images/[size].[fmt]` - Return Images of a Specific Size from a Search](#imagesfmt)
        * [`api/image/[size]/[opusid].[fmt]` - Return Images of a Specific Size for an OPUS ID](#imagesfmt)
        * [`api/files.json` - Return Files from a Search](#filesjson)
        * [`api/files/[opusid].json` - Return Files for an OPUS ID](#filesopusidjson)
* [Available Metadata Fields](#availablefields)

%ENDCLASS%

--------------------------------------------------------------------------------

<h1 id="basicconcepts">Basic Concepts: Metadata Fields, Retrieving, and Searching</h1>

<h2 id="apiformat">API Format</h2>

The OPUS API consists of requests encoded in a single URL passed to the OPUS server (normally `https://tools.pds-rings.seti.org`). Each request is independent and no state is saved between requests. A URL consists of the prefix components `/opus/api/` followed by the API entry point desired. The entry point name is suffixed by the desired format of the returned data (see [Return Formats](#returnformats)). API calls may take parameters provided after a single `?`. Each parameter is of the form `<name>=<value>`. If there is more than one parameter, they are separated by `&`. Parameters may be encoded using the standard octet encoding detailed in [RFC3986](https://tools.ietf.org/html/rfc3986), although only `&` and `=` are required to be encoded if used as a parameter's value.

Examples:

* API call with no parameters:

    %EXTLINK%%HOST%/opus/api/meta/result_count.json%ENDEXTLINK%

* API call with one parameter:

    %EXTLINK%%HOST%/opus/api/meta/result_count.json?volumeid=COISS_2001%ENDEXTLINK%

* API call with two parameters:

    %EXTLINK%%HOST%/opus/api/meta/result_count.json?time1=2009-01-01&time2=2010-01-01%ENDEXTLINK%

<h2 id="opusdatabase">The OPUS Database</h2>

The OPUS database contains a set of _observations_. Each observation is identified by a unique _OPUS ID_, which is a short series of characters identifying the mission, instrument, and observation number; the exact format of the OPUS ID varies by mission and instrument (examples: Cassini ISS: `co-iss-w1294561143`, HST WFPC2: `hst-05392-wfpc2-u2930301`). OPUS IDs can also be used to represent derived or composite products. Each observation is associated with metadata in one or more categories (e.g. "General" or "Ring Geometry"), each of which contains a series of metadata fields. Each metadata field is identified by a _slug_, which is a human-readable abbreviation. The list of available categories, metadata fields, and associated information is available [here](#availablefields) or through an API call described [[XXXhere]].

There are 3 basic types of fields stored in the database: _multiple-choice_, _string_, and _range_.

* **Multiple-choice** fields contain a single value chosen from a set of valid values. For example, the `Mission` field may contain values such as `Cassini`, `Voyager`, or `Hubble`.
* **String** fields contain a single string of arbitrary characters. The formatting is specific to the individual field (e.g. a PDS3 volume ID might look like "COISS_2001" while a Dataset ID might look like "CO-E/V/J-ISSNA/ISSWA-2-EDR-V1.0").
* **Range** fields contain either a single value or a pair of values (minimum and maximum). Depending on the field, values may be integers, floating point values, date/time strings, or specially-formatted values such as spacecraft clock count. A single-value field is used for cases where there is only a single value for each observation, such as observation duration (there is only a single duration of time for each observation). Fields with both a minimum and maximum are used when a range of values is appropriate. Examples include observation time (where minimum is the starting time and maximum is the ending time) or right ascension (where minimum and maximum represent the range of right ascension values covered by an observation).

<h2 id="retrievingmetadata">Retrieving Metadata</h2>

Many API calls allow you to choose which metadata fields are returned by specifying the parameter `cols=<fields>`, where `<fields>` is a comma-separated list of slugs. For example:

        cols=opusid,instrument,planet,target,time1,time2

When a `cols` parameter is supported but none is provided, the default columns are used: `opusid,instrument,planet,target,time1,observationduration`.

If a metadata field is a _single-value range_, then that slug **must** be provided without a numeric suffix (e.g. `observationduration`). However, if a metadata field contains both a minimum and maximum value in the database (e.g. `rightasc` for Right Ascension), then a `1` suffix indicates the minimum and a `2` suffix indicates the maximum. For example:

        cols=observationduration,rightasc1,rightasc2

However, it would be illegal to say `cols=observationduration1` or `cols=rightasc`.

See the section on [Available Metadata Fields](#availablefields) below for more information.

<h2 id="performingsearches">Performing Searches</h2>

Many API calls allow you to select which observations you want to return by specifying a set of search constraints. If no constraints are specified, all observations in the database are returned. A search constraint consists of a slug and a desired value. For example:

        volumeid=COISS_2001

When searching on a multiple-choice field, multiple search values can be specified separated by commas. In this case, fields matching any of the values are returned:

        planet=Saturn,Uranus,Neptune

Multiple-choice values are case-insensitive.

Multiple search constraints are specified by joining them with `&`. When search constraints are specified for different metadata fields, they are "AND"ed together. For example:

        volumeid=COISS_2001&planet=Saturn,Uranus,Neptune

will return any observation with Volume ID `COISS_2001` **and** a Planet value of `Saturn`, `Uranus`, or `Neptune`.

All numeric ranges may be searched by specifying a minimum value (`1` suffix), maximum value (`2` suffix), or both. These suffixes should not be confused with the suffixes used to return metadata. In the case of searches, any range field, whether single-value or not, can have a minimum and maximum search value:

        observationduration1=10&observationduration2=20

<h3 id="querytypes">Query Types</h3>

When performing a search, all string and some range fields may have an additional "query type" (_qtype_) that describes how the search should be performed. The query type is specified by including `qtype-<slug>=value` as a search parameter. Note that the slug is always specified without a (`1` or `2`) suffix, even if the search requires suffixes for minimum and maximum vales. This is because the qtype applies to the entire search field, not to the minimum or maximum values separately. The details of the qtypes associated with each field type are given below.

#### String Fields

Strings can be searched using the following query types:

* **contains**: the search string occurs anywhere within the metadata string. This is the default if no qtype is given.
* **begins**: the search string occurs at the beginning of the metadata string.
* **ends**: the search string occurs at the end of the metadata string.
* **matches**: the search string is exactly equal to the metadata string.
* **excludes**: the search string does _not_ appear anywhere in the metadata string.

#### Range Fields

Range fields can be searched using the following query types:

* **any**: The observation range overlaps at least some with the search range. In other words, either the observation maximum is greater than the search minimum, or the observation minimum is less than the search maximum. This option is used to request the widest possible set of observations that contain at least some of the range you are searching for. This is the default if no qtype is given.
* **all**: The observation range is a strict superset of the search range. In other words, the observation minimum is less than the search minimum, and the observation maximum is greater than the search maximum. This option is used to ensure that an entire feature you are looking for (such as a crater) is visible in the observation.
* **only**: The observation range is a strict subset of the search range. In other words, the observation minimum is greater than the search minimum, and the observation maximum is less than the search maximum. This option is used to tighly constrain your search to the smallest possible set of results.

<h3 id="units">Units</h3>

When performing a search, some range fields have an additional _unit_ that describes what units the search values are in. If no unit is specified, the default for that field is used. The unit is specified by including `unit-<slug>=value` as a search parameter. Note that the slug is always specified without a suffix, even if the search requires suffixes for minimum and maximum vales.

<h3 id="clauses">Multiple Clauses</h3>

Multiple string and range constraints can be specified for the same field. In this case, the multiple constraints are "OR"ed together. To distinguish between the constraints, the slugs are suffixed with `_N` where `N` is any positive integer. For example:

        observationduration1_1=10&observationduration2_1=20&observationduration1_2=30&observationduration2_2=40

would search for Observation Duration between 10 and 20 seconds (inclusive) *or* between 30 and 40 seconds (inclusive).

<h3 id="sorting">Sorting</h3>

By default, the results of a search are sorted first by Observation Start Time (`time1`) and then by OPUS ID (`opusid`). This order can be changed by specifying `order=<fields>`, where `<fields>` contains one or more slugs (as would be used when retrieving metadata) separated by commas. If multiple slugs are given, the sorting proceeds by the first slug, and then if the values are identical by the second slug, etc. Sorting is normally done in ascending order, but may be changed to descending for a particular field by prepending the metadata field slug with a minus sign (`-`).

Note that if `opusid` does not appear in the sort order list, it will automatically be added at the end. Since all OPUS IDs are unique, this guarantees the resulting order is deterministic.

<h3 id="basicconceptexamples">Examples</h3>

* To search for Data Set IDs that contain "ISS" anywhere (the qtype is optional):

        datasetid=ISS&qtype=contains  

* To search for Data Set IDs that start with "CO-E":

        datasetid=CO-E&qtype=begins

* To search for Volume IDs "COISS_2001" or "COISS_2002":

        volumeid_1=COISS_2001&qtype-volumeid_01=matches&volumeid_2=COISS_2002&qtype-volumeid_02=matches

* To search for ring radii between 110,000 and 130,000 km using the "any" qtype (the qtype is optional):

        RINGGEOringradius1=110000&RINGGEOringradius2=130000

        RINGGEOringradius1=110000&RINGGEOringradius2=130000&qtype-RINGGEOringradius=any

* To search for ring radii between 1.3 and 1.7 Saturn radii using the "only" qtype:

        RINGGEOringradius1=1.3&RINGGEOringradius2=1.7&unit-RINGGEOringradius=saturnradii&qtype-RINGGEOringradius=only

* To search for all Hubble images taken of Jupiter or Saturn in 1994 or 2001 with a spectral bandpass limited to 400-700 nm:

        mission=Hubble&observationtype=Image&planet=Jupiter,Saturn&time1_1=1994-01-01T00:00:00.000&time2_1=1994-12-31T23:59:59.999&qtype-time_1=any&time1_2=2001-01-01T00:00:00.000&time2_2=2002-12-31T23:59:59.999&qtype-time_2=any&wavelength1=400&wavelength2=700&qtype-wavelength=only&unit-wavelength=nm

* To search for all Cassini ISS images sorted by filter name then in reverse order by observation duration, and finally by OPUS ID:

        instrument=Cassini+ISS&order=COISSfilter,-observationduration,opusid

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

<h2 id="gettingdata">Getting Data</h2>





<h3 id="datafmt"><code>api/data.[fmt]</code> - Return Metadata from a Search</h3>

Get data for observations based on search criteria, sort order, and requested metadata fields. Data is returned in chunks (called "pages" in the returned JSON) to limit return size. The starting observation number and the number of observations desired can be specified.

Supported return formats: `json`, `html`, `csv`

#### Parameters

| Parameter | Description |
|---|---|
| `<slug>=<value>` | Search parameters (including sort order) |
| `cols=<field list>` | Metadata fields to return |
| `startobs=<N>` | The (1-based) observation number to start with; defaults to 1 |
| `limit=<N>` | The maximum number of observations to return; defaults to 100 |

#### JSON Return

| Field Name | Description |
|---|---|
| `start_obs` | Requested starting observation |
| `limit` | Requested limit |
| `count` | Number of observations actually returned |
| `available` | Total number of observations available from this search |
| `order` | Sort order |
| `labels` | Requested metadata field names (fully qualified) in the order requested with `cols` |
| `page` | The observation data |

`page` is a list with one entry per returned observation. Each entry is itself a list, with one entry per requested metadata field, in the same order as was requested with `cols`.

Example:

* Retrieve data in JSON format for the first 3 Cassini ISS images that contain Enceladus' south pole (latitude 70 degrees or greater) and have a phase angle at Enceladus of 160 degrees or greater.

    %EXTLINK%%HOST%/opus/api/data.json?instrument=Cassini+ISS&SURFACEGEOenceladusplanetographiclatitude1=70&SURFACEGEOenceladuscenterphaseangle1=160&order=time1&cols=opusid,target,time1,SURFACEGEOenceladuscenterphaseangle&startobs=5&limit=3%ENDEXTLINK%

    Returns:

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

#### CSV Return

The first returned line contains the names of the requested metadata fields; after that is one row per observation containing the requested metadata.

Example:

* Retrieve data in CSV format for the first 3 Cassini ISS images that contain Enceladus' south pole (latitude 70 degrees or greater) and have a phase angle at Enceladus of 160 degrees or greater.

    %EXTLINK%%HOST%/opus/api/data.csv?instrument=Cassini+ISS&SURFACEGEOenceladusplanetographiclatitude1=70&SURFACEGEOenceladuscenterphaseangle1=160&order=time1&cols=opusid,target,time1,SURFACEGEOenceladuscenterphaseangle&startobs=5&limit=3%ENDEXTLINK%

    Returns:

        OPUS ID,Intended Target Name,Observation Start Time,Phase Angle at Body Center [Enceladus] (degrees)
        co-iss-n1635813867,Enceladus,2009-11-02T00:01:22.626,161.414
        co-iss-n1635814065,Enceladus,2009-11-02T00:03:38.237,161.519
        co-iss-n1635814245,Enceladus,2009-11-02T00:07:43.051,161.657

#### HTML Return

The return is a table. The table header contains the names of the requested metadata fields. The table rows contain the requested metadata.

Example:

* Retrieve data in HTML format for the first 3 Cassini ISS images that contain Enceladus' south pole (latitude 70 degrees or greater) and have a phase angle at Enceladus of 160 degrees or greater.

    %EXTLINK%%HOST%/opus/api/data.html?instrument=Cassini+ISS&SURFACEGEOenceladusplanetographiclatitude1=70&SURFACEGEOenceladuscenterphaseangle1=160&order=time1&cols=opusid,target,time1,SURFACEGEOenceladuscenterphaseangle&startobs=5&limit=3%ENDEXTLINK%

    Returns:

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





<h3 id="metadatav2fmt"><code>api/metadata_v2/[opusid].[fmt]</code> - Return Metadata for an OPUSID</h3>

Get all available, or particular, metadata for a single observation.

Supported return formats: `json`, `html`, `csv`

#### Parameters:

| Parameter | Description |
|---|---|
| `cols=<field list>` | Metadata fields to return |
| `cats=<category names>` | If supplied, only returns data for these categories; if `cols` is supplied, `cats` is ignored |

#### JSON Return

If `cols` is supplied, the return is a list of objects each with a single name/value pair `{slug: value}`. If `cols` is not supplied, the return is an object containing name/value pairs `{category: data}` where `data` is a list of objects each with a single name/value pair `{slug: value}`.

Examples:

* Retrieve all metadata for a single Cassini ISS Saturn observation in JSON format:

    %EXTLINK%%HOST%/opus/api/metadata_v2/co-iss-w1866600688.json%ENDEXTLINK%

    Returns:

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

* Retrieve start and stop time only for a single Cassini ISS Saturn observation in JSON format:

    %EXTLINK%%HOST%/opus/api/metadata_v2/co-iss-w1866600688.json?cols=time1,time2%ENDEXTLINK%

    Returns:

        [
          {
            "time1": "2017-02-24T03:03:29.866"
          },
          {
            "time2": "2017-02-24T03:03:33.666"
          }
        ]

* Retrieve PDS and Images Constraints only for a single Cassini ISS Saturn Observation in JSON format:

    %EXTLINK%%HOST%/opus/api/metadata_v2/co-iss-w1866600688.json?cats=PDS+Constraints,Image+Constraints%ENDEXTLINK%

    Returns:

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

#### CSV Return

If `cols` is supplied, the return is a line containing the list of field names followed by a line containing the list of metadata for those fields. If `cols` is not supplied, the return contains, for each category, three lines: the name of the category, the list of field names in that category, and the metadata for those fields.

* Retrieve all metadata for a single Cassini ISS Saturn observation in CSV format:

    %EXTLINK%%HOST%/opus/api/metadata_v2/co-iss-w1866600688.csv%ENDEXTLINK%

    Returns:

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

* Retrieve start and stop time only for a single Cassini ISS Saturn observation in CSV format:

    %EXTLINK%%HOST%/opus/api/metadata_v2/co-iss-w1866600688.csv?cols=time1,time2%ENDEXTLINK%

    Returns:

        Observation Start Time,Observation Stop Time
        2017-02-24T03:03:29.866,2017-02-24T03:03:33.666

* Retrieve PDS and Image Constraints only for a single Cassini ISS Saturn Observation in HTML format:

    %EXTLINK%%HOST%/opus/api/metadata_v2/co-iss-w1866600688.csv?cats=PDS+Constraints,Image+Constraints%ENDEXTLINK%

    Returns:

        PDS Constraints
        Volume ID,Data Set ID,Product ID,Product Creation Time, [...]
        COISS_2111,CO-S-ISSNA/ISSWA-2-EDR-V1.0,1_W1866600688.122,2017-02-25T09:50:35.000, [...]
        Image Constraints
        Exposure Duration (secs),Greater Size in Pixels,Lesser Size in Pixels, [...]
        3.8000,1024,1024, [...]

#### HTML Return        

If `cols` is supplied, the return is a description list containing name/value pairs where the name is the "pretty" name of the metadata field. If `cols` is not supplied, the return is a description list containing name/value pairs organized by category name.

Examples:

* Retrieve all metadata for a single Cassini ISS Saturn observation in HTML format:

    %EXTLINK%%HOST%/opus/api/metadata_v2/co-iss-w1866600688.html%ENDEXTLINK%

    Returns:

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

* Retrieve start and stop time only for a single Cassini ISS Saturn observation in HTML format:

    %EXTLINK%%HOST%/opus/api/metadata_v2/co-iss-w1866600688.html?cols=time1,time2%ENDEXTLINK%

    Returns:

        <dl>
        <dt>Observation Start Time</dt><dd>2017-02-24T03:03:29.866</dd>
        <dt>Observation Stop Time</dt><dd>2017-02-24T03:03:33.666</dd>
        </dl>

* Retrieve PDS and Image Constraints only for a single Cassini ISS Saturn Observation in HTML format:

    %EXTLINK%%HOST%/opus/api/metadata_v2/co-iss-w1866600688.html?cats=PDS+Constraints,Image+Constraints%ENDEXTLINK%

    Returns:

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





<h3 id="imagesfmt"><code>api/images.[fmt]</code> - Return Images from a Search</h3>
<h3><code>api/images/[size].[fmt]</code> - Return Images from a Search</h3>
<h3><code>api/image/[size]/[opusid].[fmt]</code> - Return Images of a Specific Size for an OPUS ID</h3>

Get the URLs of images of all sizes (or a given size) based on search criteria and sort order. Image URLs are returned in chunks to limit return size. The starting observation number and the number of observations desired can be specified. An image of a specific size may also be returned for a single OPUS ID.

If specified, `[size]` must be one of `full`, `med`, `small`, or `thumb`.

Supported return formats: `json`, `csv`. `html` is also supported when a specified size is requested.

#### Parameters:

| Parameter | Description |
|---|---|
| `<slug>=<value>` | Search parameters (including sort order) |
| `startobs=<N>` | The (1-based) observation number to start with; defaults to 1 |
| `limit=<N>` | The maximum number of observations to return; defaults to 100 |

#### JSON Return

When a search was requested, the return includes:

| Field Name | Description |
|---|---|
| `start_obs` | Requested starting observation |
| `limit` | Requested limit |
| `count` | Number of observations actually returned |
| `available` | Total number of observations available from this search |
| `order` | Sort order |
| `labels` | Requested metadata field names (fully qualified) |
| `data` | The images data with one entry per returned observation |

When all sizes are requested, each entry is an object containing:

| Field Name | Description |
|---|---|
| `opus_id` | OPUS ID of the observation |
| `<size>_alt_text` | Alternate text (image filename) |
| `<size>_size_bytes` | Size of the image file in bytes |
| `<size>_width` | Width of the image in pixels |
| `<size>_height` | Height of the image in pixels |
| `<size>_url` | Relative path to the image |

When one size is requested, each entry is an object containing:

| Field Name | Description |
|---|---|
| `opus_id` | OPUS ID of the observation |
| `alt_text` | Alternate text (image filename) |
| `size_bytes` | Size of the image file in bytes |
| `width` | Width of the image in pixels |
| `height` | Height of the image in pixels |
| `url` | Relative path to the image |

Example:

* Retrieve all sizes of images in JSON format for observations 10-11 from Cassini ISS volume COISS_2002.

    %EXTLINK%%HOST%/opus/api/images.json?volumeid=COISS_2002&startobs=10&limit=2%ENDEXTLINK%

    Returns:

        {
          "start_obs": 10,
          "limit": 2,
          "count": 2,
          "available": 3296,
          "order": "time1,opusid"
          "data": [
            {
              "opus_id": "co-iss-n1460962327",
              "thumb_url": "https://pds-rings.seti.org/holdings/previews/COISS_2xxx/COISS_2002/data/1460960653_1461048959/N1460962327_1_thumb.jpg",
              "thumb_alt_text": "N1460962327_1_thumb.jpg",
              "thumb_size_bytes": 864,
              "thumb_width": 100,
              "thumb_height": 100,
              "small_url": "https://pds-rings.seti.org/holdings/previews/COISS_2xxx/COISS_2002/data/1460960653_1461048959/N1460962327_1_small.jpg",
              "small_alt_text": "N1460962327_1_small.jpg",
              "small_size_bytes": 1729,
              "small_width": 256,
              "small_height": 256,
              [...]
            },
            [...]
          ]
        }

* Retrieve medium-size images in JSON format for observations 10-11 from Cassini ISS volume COISS_2002.

    %EXTLINK%%HOST%/opus/api/images/med.json?volumeid=COISS_2002&startobs=10&limit=2%ENDEXTLINK%

    Returns:

        {
          "start_obs": 10,
          "limit": 2,
          "count": 2,
          "available": 3296,
          "order": "time1,opusid",
          "data": [
            {
              "opus_id": "co-iss-n1460962327",
              "alt_text": "N1460962327_1_med.jpg",
              "size_bytes": 4971,
              "width": 512,
              "height": 512,
              "url": "https://pds-rings.seti.org/holdings/previews/COISS_2xxx/COISS_2002/data/1460960653_1461048959/N1460962327_1_med.jpg"
            },
            {
              "opus_id": "co-iss-n1460962415",
              "alt_text": "N1460962415_1_med.jpg",
              "size_bytes": 4991,
              "width": 512,
              "height": 512,
              "url": "https://pds-rings.seti.org/holdings/previews/COISS_2xxx/COISS_2002/data/1460960653_1461048959/N1460962415_1_med.jpg"
            }
          ]
        }

* Retrieve the medium-size image in JSON format for OPUS ID vg-iss-2-s-c4360022.

    %EXTLINK%%HOST%/opus/api/image/full/vg-iss-2-s-c4360022.json%ENDEXTLINK%

    Returns:

        {
          "data": [
            {
              "opus_id": "vg-iss-2-s-c4360022",
              "alt_text": "C4360022_full.jpg",
              "size_bytes": 24607,
              "width": 800,
              "height": 800,
              "url": "https://pds-rings.seti.org/holdings/previews/VGISS_6xxx/VGISS_6210/DATA/C43600XX/C4360022_full.jpg"
            }
          ]
        }


#### CSV Return

The first returned line contains the column headers; after that is one row per observation containing the information about each image.

Example:

* Retrieve all sizes of images in CSV format for observations 10-11 from Cassini ISS volume COISS_2002.

    %EXTLINK%%HOST%/opus/api/images.csv?volumeid=COISS_2002&startobs=10&limit=2%ENDEXTLINK%

    Returns:

        OPUS ID,Thumb URL,Small URL,Med URL,Full URL
        co-iss-n1460962327,https://pds-rings.seti.org/holdings/previews/COISS_2xxx/COISS_2002/data/1460960653_1461048959/N1460962327_1_full.png
        co-iss-n1460962415,https://pds-rings.seti.org/holdings/previews/COISS_2xxx/COISS_2002/data/1460960653_1461048959/N1460962415_1_full.png

* Retrieve medium-size images in CSV format for observations 10-11 from Cassini ISS volume COISS_2002.

    %EXTLINK%%HOST%/opus/api/images/med.csv?volumeid=COISS_2002&startobs=10&limit=2%ENDEXTLINK%

    Returns:

        OPUS ID,URL
        co-iss-n1460962327,https://pds-rings.seti.org/holdings/previews/COISS_2xxx/COISS_2002/data/1460960653_1461048959/N1460962327_1_med.jpg
        co-iss-n1460962415,https://pds-rings.seti.org/holdings/previews/COISS_2xxx/COISS_2002/data/1460960653_1461048959/N1460962415_1_med.jpg

* Retrieve the medium-size image in CSV format for OPUS ID vg-iss-2-s-c4360022.

    %EXTLINK%%HOST%/opus/api/image/full/vg-iss-2-s-c4360022.csv%ENDEXTLINK%

    Returns:

        OPUS ID,URL
        vg-iss-2-s-c4360022,https://pds-rings.seti.org/holdings/previews/VGISS_6xxx/VGISS_6210/DATA/C43600XX/C4360022_full.jpg

#### HTML Return

The return is a list containing the requested images.

Example:

* Retrieve medium-size images in HTML format for observations 10-11 from Cassini ISS volume COISS_2002.

    %EXTLINK%%HOST%/opus/api/images/med.html?volumeid=COISS_2002&startobs=10&limit=2%ENDEXTLINK%

    Returns:

        <ul>
        <li>
        <img id="med__co-iss-n1460962327" src="https://pds-rings.seti.org/holdings/previews/COISS_2xxx/COISS_2002/data/1460960653_1461048959/N1460962327_1_med.jpg">
        </li>
        <li>
        <img id="med__co-iss-n1460962415" src="https://pds-rings.seti.org/holdings/previews/COISS_2xxx/COISS_2002/data/1460960653_1461048959/N1460962415_1_med.jpg">
        </li>
        </ul>

* Retrieve the medium-size image in HTML format for OPUS ID vg-iss-2-s-c4360022.

    %EXTLINK%%HOST%/opus/api/image/full/vg-iss-2-s-c4360022.html%ENDEXTLINK%

    Returns:

        <ul>
        <li>
        <img id="full__vg-iss-2-s-c4360022" src="https://pds-rings.seti.org/holdings/previews/VGISS_6xxx/VGISS_6210/DATA/C43600XX/C4360022_full.jpg">
        </li>
        </ul>





<h3 id="filesjson"><code>api/files.json</code> - Return Files from a Search</h3>

Get a list of all (or some) files for the search results.

Supported return formats: `json`.

#### Parameters

| Parameter | Description |
|---|---|
| `<slug>=<value>` | Search parameters (including sort order) |
| `cols=<field list>` | Metadata fields to return |
| `startobs=<N>` | The (1-based) observation number to start with; defaults to 1 |
| `limit=<N>` | The maximum number of observations to return; defaults to 100 |
| `types=<types>` | List of product types; if not supplied, all are returned |

#### JSON Return

| Field Name | Description |
|---|---|
| `start_obs` | Requested starting observation |
| `limit` | Requested limit |
| `count` | Number of observations actually returned |
| `available` | Total number of observations available from this search |
| `order` | Sort order |
| `data` | The file information for the current version |
| `versions` | The file information for all versions (including the current one) |

`data` and `versions` are both objects indexed by opusid. `versions` is further indexed by version number. Both are then indexed by product type, which gives a list of URLs to associated files.

Examples:

* Retrieve all files associated with images of Pan in volume COISS_2111.

    %EXTLINK%%HOST%/opus/api/files.json?volumeid=COISS_2111&target=pan%ENDEXTLINK%

    Returns:

        {
          "start_obs": 1,
          "limit": 100,
          "count": 56,
          "available": 56,
          "order": "time1,opusid",
          "data": {
            "co-iss-n1867599811": {
              "coiss-raw": [
                "https://pds-rings.seti.org/holdings/volumes/COISS_2xxx/COISS_2111/data/1867558636_1867602962/N1867599811_1.IMG",
                "https://pds-rings.seti.org/holdings/volumes/COISS_2xxx/COISS_2111/data/1867558636_1867602962/N1867599811_1.LBL",
                "https://pds-rings.seti.org/holdings/volumes/COISS_2xxx/COISS_2111/label/prefix3.fmt",
                "https://pds-rings.seti.org/holdings/volumes/COISS_2xxx/COISS_2111/label/tlmtab.fmt"
              ],
              "coiss-calib": [
                "https://pds-rings.seti.org/holdings/calibrated/COISS_2xxx/COISS_2111/data/1867558636_1867602962/N1867599811_1_CALIB.IMG",
                "https://pds-rings.seti.org/holdings/calibrated/COISS_2xxx/COISS_2111/data/1867558636_1867602962/N1867599811_1_CALIB.LBL"
              ],
              "coiss-thumb": [
                "https://pds-rings.seti.org/holdings/volumes/COISS_2xxx/COISS_2111/extras/thumbnail/1867558636_1867602962/N1867599811_1.IMG.jpeg_small"
              ],
              [...]
            },
            "co-iss-n1867600166": {
              "coiss-raw": [
                "https://pds-rings.seti.org/holdings/volumes/COISS_2xxx/COISS_2111/data/1867558636_1867602962/N1867600166_1.IMG",
                "https://pds-rings.seti.org/holdings/volumes/COISS_2xxx/COISS_2111/data/1867558636_1867602962/N1867600166_1.LBL",
                "https://pds-rings.seti.org/holdings/volumes/COISS_2xxx/COISS_2111/label/prefix3.fmt",
                "https://pds-rings.seti.org/holdings/volumes/COISS_2xxx/COISS_2111/label/tlmtab.fmt"
              ],
              [...]
          },
          [...]
        }




<h3 id="filesopusidjson"><code>api/files/[opusid].json</code> - Return Files for an OPUS ID</h3>

Get the URLs of all (or some) files available for a single observation.

Supported return formats: `json`.

Parameters:

| Parameter | Description |
|---|---|
| `types=<types>` | List of product types; if not supplied, all are returned |

#### JSON Return

| Field Name | Description |
|---|---|
| `data` | The file information for the current version |
| `versions` | The file information for all versions (including the current one) |

`data` and `versions` are both objects indexed by opusid. `versions` is further indexed by version number. Both are then indexed by product type, which gives a list of URLs to associated files.

Examples:

* Retrieve all files associated with a Voyager ISS observation

    %EXTLINK%%HOST%/opus/api/files/vg-iss-2-s-c4360022.json%ENDEXTLINK%

    Returns:

        {
          "data": {
            "vg-iss-2-s-c4360022": {
              "vgiss-raw": [
                "https://pds-rings.seti.org/holdings/volumes/VGISS_6xxx/VGISS_6210/DATA/C43600XX/C4360022_RAW.IMG",
                "https://pds-rings.seti.org/holdings/volumes/VGISS_6xxx/VGISS_6210/DATA/C43600XX/C4360022_RAW.LBL"
              ],
              "vgiss-cleaned": [
                "https://pds-rings.seti.org/holdings/volumes/VGISS_6xxx/VGISS_6210/DATA/C43600XX/C4360022_CLEANED.IMG",
                "https://pds-rings.seti.org/holdings/volumes/VGISS_6xxx/VGISS_6210/DATA/C43600XX/C4360022_CLEANED.LBL"
              ],
              "vgiss-calib": [
                "https://pds-rings.seti.org/holdings/volumes/VGISS_6xxx/VGISS_6210/DATA/C43600XX/C4360022_CALIB.IMG",
                "https://pds-rings.seti.org/holdings/volumes/VGISS_6xxx/VGISS_6210/DATA/C43600XX/C4360022_CALIB.LBL"
              ],
              [...]
            }
          },
          "versions": {
            "vg-iss-2-s-c4360022": {
              "Current": {
                "vgiss-raw": [
                  "https://pds-rings.seti.org/holdings/volumes/VGISS_6xxx/VGISS_6210/DATA/C43600XX/C4360022_RAW.IMG",
                  "https://pds-rings.seti.org/holdings/volumes/VGISS_6xxx/VGISS_6210/DATA/C43600XX/C4360022_RAW.LBL"
                ],
                "vgiss-cleaned": [
                  "https://pds-rings.seti.org/holdings/volumes/VGISS_6xxx/VGISS_6210/DATA/C43600XX/C4360022_CLEANED.IMG",
                  "https://pds-rings.seti.org/holdings/volumes/VGISS_6xxx/VGISS_6210/DATA/C43600XX/C4360022_CLEANED.LBL"
                ],
                "vgiss-calib": [
                  "https://pds-rings.seti.org/holdings/volumes/VGISS_6xxx/VGISS_6210/DATA/C43600XX/C4360022_CALIB.IMG",
                  "https://pds-rings.seti.org/holdings/volumes/VGISS_6xxx/VGISS_6210/DATA/C43600XX/C4360022_CALIB.LBL"
                ],
                [...]
              }
            }
          }
        }    

* Retrieve raw images only for a Galileo SSI observation.

    %EXTLINK%%HOST%/opus/api/files/go-ssi-c0349632000.json?types=gossi-raw

    Returns:

        {
          "data": {
            "go-ssi-c0349632000": {
              "gossi-raw": [
                "https://pds-rings.seti.org/holdings/volumes/GO_0xxx/GO_0017/G1/GANYMEDE/C0349632000R.IMG",
                "https://pds-rings.seti.org/holdings/volumes/GO_0xxx/GO_0017/G1/GANYMEDE/C0349632000R.LBL",
                "https://pds-rings.seti.org/holdings/volumes/GO_0xxx/GO_0017/LABEL/RLINEPRX.FMT",
                "https://pds-rings.seti.org/holdings/volumes/GO_0xxx/GO_0017/LABEL/RTLMTAB.FMT"
              ]
            }
          },
          "versions": {
            "go-ssi-c0349632000": {
              "1": {
                "gossi-raw": [
                  "https://pds-rings.seti.org/holdings/volumes/GO_0xxx_v1/GO_0017/G1/GANYMEDE/C034963/2000R.IMG",
                  "https://pds-rings.seti.org/holdings/volumes/GO_0xxx_v1/GO_0017/G1/GANYMEDE/C034963/2000R.LBL",
                  "https://pds-rings.seti.org/holdings/volumes/GO_0xxx_v1/GO_0017/LABEL/RLINEPRX.FMT",
                  "https://pds-rings.seti.org/holdings/volumes/GO_0xxx_v1/GO_0017/LABEL/RTLMTAB.FMT"
                ]
              },
              "Current": {
                "gossi-raw": [
                  "https://pds-rings.seti.org/holdings/volumes/GO_0xxx/GO_0017/G1/GANYMEDE/C0349632000R.IMG",
                  "https://pds-rings.seti.org/holdings/volumes/GO_0xxx/GO_0017/G1/GANYMEDE/C0349632000R.LBL",
                  "https://pds-rings.seti.org/holdings/volumes/GO_0xxx/GO_0017/LABEL/RLINEPRX.FMT",
                  "https://pds-rings.seti.org/holdings/volumes/GO_0xxx/GO_0017/LABEL/RTLMTAB.FMT"
                ]
              }
            }
          }
        }

* Retrieve drizzle images from an HST WFC3 observation with multiple versions.

    %EXTLINK%%HOST%/opus/api/files/hst-11559-wfc3-ib4v19rp.json%ENDEXTLINK%

    Returns:

        {
          "data": {
            "hst-11559-wfc3-ib4v19rp": {
              "hst-calib": [
                "https://pds-rings.seti.org/holdings/volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_19/IB4V19RPQ_FLT.JPG",
                "https://pds-rings.seti.org/holdings/volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_19/IB4V19RPQ.LBL"
              ],
              "hst-drizzled": [
                "https://pds-rings.seti.org/holdings/volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_19/IB4V19RPQ_DRZ.JPG",
                "https://pds-rings.seti.org/holdings/volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_19/IB4V19RPQ.LBL"
              ]
            }
          },
          "versions": {
            "hst-11559-wfc3-ib4v19rp": {
              "Current": {
                "hst-calib": [
                  "https://pds-rings.seti.org/holdings/volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_19/IB4V19RPQ_FLT.JPG",
                  "https://pds-rings.seti.org/holdings/volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_19/IB4V19RPQ.LBL"
                ],
                "hst-drizzled": [
                  "https://pds-rings.seti.org/holdings/volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_19/IB4V19RPQ_DRZ.JPG",
                  "https://pds-rings.seti.org/holdings/volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_19/IB4V19RPQ.LBL"
                ]
              },
              "1.1": {
                "hst-calib": [
                  "https://pds-rings.seti.org/holdings/volumes/HSTIx_xxxx_v1.1/HSTI1_1559/DATA/VISIT_19/IB4V19RPQ_FLT.JPG",
                  "https://pds-rings.seti.org/holdings/volumes/HSTIx_xxxx_v1.1/HSTI1_1559/DATA/VISIT_19/IB4V19RPQ.LBL"
                ],
                "hst-drizzled": [
                  "https://pds-rings.seti.org/holdings/volumes/HSTIx_xxxx_v1.1/HSTI1_1559/DATA/VISIT_19/IB4V19RPQ_DRZ.JPG",
                  "https://pds-rings.seti.org/holdings/volumes/HSTIx_xxxx_v1.1/HSTI1_1559/DATA/VISIT_19/IB4V19RPQ.LBL"
                ]
              },
              "1.0": {
                "hst-calib": [
                  "https://pds-rings.seti.org/holdings/volumes/HSTIx_xxxx_v1.0/HSTI1_1559/DATA/VISIT_19/IB4V19RPQ_FLT.JPG",
                  "https://pds-rings.seti.org/holdings/volumes/HSTIx_xxxx_v1.0/HSTI1_1559/DATA/VISIT_19/IB4V19RPQ.LBL"
                ],
                "hst-drizzled": [
                  "https://pds-rings.seti.org/holdings/volumes/HSTIx_xxxx_v1.0/HSTI1_1559/DATA/VISIT_19/IB4V19RPQ_DRZ.JPG",
                  "https://pds-rings.seti.org/holdings/volumes/HSTIx_xxxx_v1.0/HSTI1_1559/DATA/VISIT_19/IB4V19RPQ.LBL"
                ]
              }
            }
          }
        }

### api/download/[opusid].zip

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

### api/categories/[opusid].json

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

--------------------------------------------------------------------------------
