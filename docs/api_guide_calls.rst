.. _apicalls:

API Calls
=========

.. contents::
   :local:
   :depth: 2

.. _returnformats:

Return Formats
--------------

All API calls take a suffix ``.[fmt]`` specifying the format in which to return data. Possible values are:

* **json**: Return all data in a JSON structure. This is most useful for programs wanting to process the returned data directly. Note that some JSON returns may contain data that is not detailed in this document. This data is usually provided for backwards compatibility with legacy applications and should **not** be relied on for new development.
* **csv**: Return all data in a comma-separated value (CSV) file, suitable for import into a spreadsheet program.
* **html**: Return all data as an HTML document. This is most useful when viewing directly in a browser. Note that the returned HTML has minimal formatting and does not include any header or ``body`` tags.
* **zip**: Return all data as a ZIP file.

Not all API calls provide results in all formats. The formats supported are listed with each call.


.. _errorresponses:

Error Responses
---------------

When a request cannot be answered, OPUS returns an HTML page describing what went wrong together with one of these HTTP status codes:

* **400 Bad Request**: Something the request itself supplied was wrong - an unknown metadata field, a value that could not be parsed, an unsupported unit or query type, or a required parameter that was missing. The returned page names the field or value at fault. The same request will always fail the same way; it has to be corrected.
* **404 Not Found**: Usually the URL named something that does not exist - an entry point OPUS does not provide, or an OPUS ID (or legacy RING OBS ID) in the URL path that matches no observation. A few server-side failures also answer 404 rather than 500, for historical reasons.
* **500 Internal Server Error**: OPUS failed while answering a request that was otherwise valid. Retrying may succeed; a failure that persists is worth reporting.

Requests that supply a bad field, value, unit, or query type answer with 400 rather than the 404 that earlier versions of OPUS returned for every kind of error. Client code that treats 404 as "my request was wrong" should be updated to look at 400 for that.


.. _gettingmetadata:

Getting Metadata
----------------

.. _datafmt:

``api/data.[fmt]`` - Return Metadata from a Search
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Get data for observations based on search criteria, sort order, and requested metadata fields. Data is returned in chunks (called "pages" in the returned JSON) to limit return size. The starting observation number and the number of observations desired can be specified.

Supported return formats: ``json``, ``html``, ``csv``

Parameters
^^^^^^^^^^

.. list-table::
   :header-rows: 1

   * - Parameter
     - Description
     - Default
   * - ``<searchid>=<value>``
     - Search parameters (including sort order)
     - All observations in database
   * - ``cols=<fieldid_list>``
     - Metadata fields to return
     - :ref:`Default columns <retrievingmetadata>`
   * - ``startobs=<N>``
     - The (1-based) observation number to start with
     - 1
   * - ``limit=<N>``
     - The maximum number of observations to return
     - 100

JSON Return Format
^^^^^^^^^^^^^^^^^^

The return value is a JSON object containing these fields:

.. list-table::
   :header-rows: 1

   * - Field Name
     - Description
   * - ``start_obs``
     - Requested starting observation
   * - ``limit``
     - Requested limit
   * - ``count``
     - Number of observations actually returned
   * - ``available``
     - Total number of observations available from this search
   * - ``order``
     - Sort order used
   * - ``labels``
     - Requested metadata field names (fully qualified) in the order requested with ``cols``
   * - ``page``
     - The observation data

``page`` is a list with one entry per returned observation. Each entry is itself a list, with one entry per requested metadata field, in the same order as was requested with ``cols``.

Example:

* Retrieve data in JSON format for the first three Cassini ISS images that contain Enceladus' south pole (latitude 70 degrees or greater) and have a phase angle at Enceladus of 160 degrees or greater.

  `<https://opus.pds-rings.seti.org/opus/api/data.json?instrument=Cassini+ISS&SURFACEGEOenceladus_planetographiclatitude1=70&SURFACEGEOenceladus_centerphaseangle1=160&order=time1&cols=opusid,target,time1,SURFACEGEOenceladus_centerphaseangle&startobs=5&limit=3>`__

  Return value:

::

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

CSV Return Format
^^^^^^^^^^^^^^^^^

The return value is a series of text lines. The first line contains the names of the requested metadata fields. After that is one line per observation containing the requested metadata.

Example:

* Retrieve data in CSV format for the first three Cassini ISS images that contain Enceladus' south pole (latitude 70 degrees or greater) and have a phase angle at Enceladus of 160 degrees or greater.

  `<https://opus.pds-rings.seti.org/opus/api/data.csv?instrument=Cassini+ISS&SURFACEGEOenceladus_planetographiclatitude1=70&SURFACEGEOenceladus_centerphaseangle1=160&order=time1&cols=opusid,target,time1,SURFACEGEOenceladus_centerphaseangle&startobs=5&limit=3>`__

  Return value:

::

    OPUS ID,Intended Target Name,Observation Start Time,Phase Angle at Body Center [Enceladus] (degrees)
    co-iss-n1635813867,Enceladus,2009-11-02T00:01:22.626,161.414
    co-iss-n1635814065,Enceladus,2009-11-02T00:03:38.237,161.519
    co-iss-n1635814245,Enceladus,2009-11-02T00:07:43.051,161.657

HTML Return Format
^^^^^^^^^^^^^^^^^^

The return value is an HTML table. The table header contains the names of the requested metadata fields. The table rows contain the requested metadata.

Example:

* Retrieve data in HTML format for the first three Cassini ISS images that contain Enceladus' south pole (latitude 70 degrees or greater) and have a phase angle at Enceladus of 160 degrees or greater.

  `<https://opus.pds-rings.seti.org/opus/api/data.html?instrument=Cassini+ISS&SURFACEGEOenceladus_planetographiclatitude1=70&SURFACEGEOenceladus_centerphaseangle1=160&order=time1&cols=opusid,target,time1,SURFACEGEOenceladus_centerphaseangle&startobs=5&limit=3>`__

  Return value:

::

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

.. _metadatafmt:

``api/metadata/[opusid].[fmt]`` - Return Metadata for an OPUSID
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Get all available, or particular, metadata for a single observation.

Supported return formats: ``json``, ``html``, ``csv``

Parameters
^^^^^^^^^^

.. list-table::
   :header-rows: 1

   * - Parameter
     - Description
     - Default
   * - ``cols=<field list>``
     - Metadata fields to return
     - All columns
   * - ``cats=<categories>``
     - If supplied, only returns data for these categories; if ``cols`` is supplied, ``cats`` is ignored
     - All categories

``categories`` is a list of category names separated by commas. Category names can either be full names ending in "Constraints" (e.g. ``PDS Constraints`` or ``Cassini ISS Constraints``) or abbreviated names representing internal database tables (``obs_pds``, ``obs_mission_cassini``, or ``obs_instrument_coiss``). Full category names must replace spaces with ``+`` or another appropriate encoding. The list of categories available for an ``opusid`` can be retrieved with :ref:`api/categories/[opusid].json <categoriesopusidfmt>`.

JSON Return Format
^^^^^^^^^^^^^^^^^^

If the ``cols`` parameter is supplied, the return value is a JSON object containing a list of objects each with a single name/value pair ``{<fieldid>: <value>}``. If the ``cols`` parameter is not supplied, the return value is a JSON object containing name/value pairs ``{<category>: <data>}`` where ``data`` is a list of objects each with a single name/value pair ``{<fieldid>: <value>}``.

Examples:

* Retrieve all metadata for a single Cassini ISS Saturn observation in JSON format:

  `<https://opus.pds-rings.seti.org/opus/api/metadata/co-iss-w1866600688.json>`__

  Return value:

::

    {
      "General Constraints": {
        "planet": "Saturn",
        "target": "Saturn",
        [...]
      },
      "PDS Constraints": {
        "bundleid": "COISS_2111",
        "datasetid": "CO-S-ISSNA/ISSWA-2-EDR-V1.0",
        [...]
      },
      [...]
    }

* Retrieve start and stop time only for a single Cassini ISS Saturn observation in JSON format:

  `<https://opus.pds-rings.seti.org/opus/api/metadata/co-iss-w1866600688.json?cols=time1,time2>`__

  Return value:

::

    [
      {
        "time1": "2017-02-24T03:03:29.866"
      },
      {
        "time2": "2017-02-24T03:03:33.666"
      }
    ]

* Retrieve PDS and Images Constraints only for a single Cassini ISS Saturn Observation in JSON format:

  `<https://opus.pds-rings.seti.org/opus/api/metadata/co-iss-w1866600688.json?cats=PDS+Constraints,Image+Constraints>`__

  Return value:

::

    {
      "PDS Constraints": {
        "bundleid": "COISS_2111",
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

CSV Return Format
^^^^^^^^^^^^^^^^^

The return value is a series of text lines. If ``cols`` is supplied, the return value is a line containing the list of field names followed by a line containing the list of metadata for those fields. If ``cols`` is not supplied, the return contains, for each category, three lines: the name of the category, the list of field names in that category, and the metadata for those fields.

* Retrieve all metadata for a single Cassini ISS Saturn observation in CSV format:

  `<https://opus.pds-rings.seti.org/opus/api/metadata/co-iss-w1866600688.csv>`__

  Return value:

::

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

  `<https://opus.pds-rings.seti.org/opus/api/metadata/co-iss-w1866600688.csv?cols=time1,time2>`__

  Return value:

::

    Observation Start Time,Observation Stop Time
    2017-02-24T03:03:29.866,2017-02-24T03:03:33.666

* Retrieve PDS and Image Constraints only for a single Cassini ISS Saturn Observation in CSV format:

  `<https://opus.pds-rings.seti.org/opus/api/metadata/co-iss-w1866600688.csv?cats=PDS+Constraints,Image+Constraints>`__

  Return value:

::

    PDS Constraints
    Volume ID,Data Set ID,Product ID,Product Creation Time, [...]
    COISS_2111,CO-S-ISSNA/ISSWA-2-EDR-V1.0,1_W1866600688.122,2017-02-25T09:50:35.000, [...]
    Image Constraints
    Exposure Duration (secs),Greater Size in Pixels,Lesser Size in Pixels, [...]
    3.8000,1024,1024, [...]

HTML Return Format
^^^^^^^^^^^^^^^^^^

If the ``cols`` parameter is supplied, the return value is an HTML description list containing name/value pairs where the name is the fully-qualified name of the metadata field. If the ``cols`` parameter is not supplied, the return value is an HTML description list containing name/value pairs organized by category name.

Examples:

* Retrieve all metadata for a single Cassini ISS Saturn observation in HTML format:

  `<https://opus.pds-rings.seti.org/opus/api/metadata/co-iss-w1866600688.html>`__

  Return value:

::

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

  `<https://opus.pds-rings.seti.org/opus/api/metadata/co-iss-w1866600688.html?cols=time1,time2>`__

  Return value:

::

    <dl>
    <dt>Observation Start Time</dt><dd>2017-02-24T03:03:29.866</dd>
    <dt>Observation Stop Time</dt><dd>2017-02-24T03:03:33.666</dd>
    </dl>

* Retrieve PDS and Image Constraints only for a single Cassini ISS Saturn Observation in HTML format:

  `<https://opus.pds-rings.seti.org/opus/api/metadata/co-iss-w1866600688.html?cats=PDS+Constraints,Image+Constraints>`__

  Return value:

::

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

.. _gettingdata:

Getting Data
------------

.. _downloadopusidzip:

``api/download/[opusid].zip`` - Download Files for an OPUS ID
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Download a ZIP file containing all (or some) of the products related to opusid.

Supported return formats: ``zip``.

Parameters
^^^^^^^^^^

.. list-table::
   :header-rows: 1

   * - Parameter
     - Description
     - Default
   * - ``urlonly=<N>``
     - If ``urlonly=1`` is specified, only include the ``urls.txt`` file and omit all data files
     - Include all data files
   * - ``types=<types>``
     - List of product types to return
     - All product types

The ``types`` parameter is a list of download product types. Available types can be retrieved with the :ref:`api/product_types.json <producttypesfmt>` or :ref:`api/product_types/[opusid].json <producttypesopusidfmt>` API calls. The ``@`` modifier can be used to specify the version for a product type. If the version is not specified for a product type, the "Current" version will be returned.

Examples
^^^^^^^^

* Download both current and version 2 calibrated image files for a Cassini ISS observation:

  `<https://opus.pds-rings.seti.org/opus/api/download/co-iss-n1460973661.zip?types=coiss_calib@current,coiss_calib@2>`__

  Return value is a zip archive containing the files:

::

    calibrated/COISS_2xxx/COISS_2002/data/1460960653_1461048959/N1460973661_1_CALIB.IMG
    calibrated/COISS_2xxx/COISS_2002/data/1460960653_1461048959/N1460973661_1_CALIB.LBL
    calibrated/COISS_2xxx_v2/COISS_2002/data/1460960653_1461048959/N1460973661_1_CALIB.IMG
    calibrated/COISS_2xxx_v2/COISS_2002/data/1460960653_1461048959/N1460973661_1_CALIB.LBL
    data.csv
    manifest.csv
    urls.txt

* Download all product types (including all data files) for a Voyager ISS observation:

  `<https://opus.pds-rings.seti.org/opus/api/download/vg-iss-2-s-c4360022.zip>`__

  Return value is a zip archive containing the files:

::

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

* Download all product types (with no data files) for a Voyager ISS observation:

  `<https://opus.pds-rings.seti.org/opus/api/download/vg-iss-2-s-c4360022.zip?urlonly=1>`__

  Return value is a zip archive containing the files:

::

    data.csv
    manifest.csv
    urls.txt

* Download only raw image files for a Galileo SSI observation.

  `<https://opus.pds-rings.seti.org/opus/api/download/go-ssi-c0349632000.zip?types=gossi_raw>`__

  Return value is a zip archive containing the files:

::

    C0349632000R.IMG
    C0349632000R.LBL
    data.csv
    manifest.csv
    RLINEPRX.FMT
    RTLMTAB.FMT
    urls.txt

.. _filesjson:

``api/files.json`` - Return URLs of Files from a Search
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Get a list of all (or some) product files for the search results.

Supported return formats: ``json``.

Parameters
^^^^^^^^^^

.. list-table::
   :header-rows: 1

   * - Parameter
     - Description
     - Default
   * - ``<searchid>=<value>``
     - Search parameters (including sort order)
     - All observations in database
   * - ``startobs=<N>``
     - The (1-based) observation number to start with
     - 1
   * - ``limit=<N>``
     - The maximum number of observations to return
     - 100
   * - ``types=<types>``
     - List of product types to return
     - All product types

The ``types`` parameter is a list of download product types. Available types can be retrieved with the :ref:`api/product_types.json <producttypesfmt>` or :ref:`api/product_types/[opusid].json <producttypesopusidfmt>` API calls. The ``@`` modifier can be used to specify the version for a product type. If the version is not specified for a product type, the "Current" version will be returned.

JSON Return Format
^^^^^^^^^^^^^^^^^^

The return value is a JSON object containing these fields:

.. list-table::
   :header-rows: 1

   * - Field Name
     - Description
   * - ``start_obs``
     - Requested starting observation
   * - ``limit``
     - Requested limit
   * - ``count``
     - Number of observations actually returned
   * - ``available``
     - Total number of observations available from this search
   * - ``order``
     - Sort order
   * - ``data``
     - The file information for the current version
   * - ``versions``
     - The file information for all versions (including the current one)

``data`` and ``versions`` are both objects indexed by opusid. ``versions`` is further indexed by version number. Both are then indexed by product type, which gives a list of URLs of associated files.

Example (see :ref:`api/files/[opusid].json <filesopusidjson>` for more):

* Retrieve all files associated with images of Pan in volume COISS_2111 in JSON format.

  `<https://opus.pds-rings.seti.org/opus/api/files.json?bundleid=COISS_2111&target=pan>`__

  Return value:

::

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

.. _filesopusidjson:

``api/files/[opusid].json`` - Return URLs of Files for an OPUS ID
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Get the URLs of all (or some) product files available for a single observation.

Supported return formats: ``json``.

Parameters
^^^^^^^^^^

.. list-table::
   :header-rows: 1

   * - Parameter
     - Description
     - Default
   * - ``types=<types>``
     - List of product types to return
     - All product types

The ``types`` parameter is a list of download product types. Available types can be retrieved with the :ref:`api/product_types.json <producttypesfmt>` or :ref:`api/product_types/[opusid].json <producttypesopusidfmt>` API calls. The ``@`` modifier can be used to specify the version for a product type. If the version is not specified for a product type, the "Current" version will be returned.

JSON Return Format
^^^^^^^^^^^^^^^^^^

The return value is a JSON object containing these fields:

.. list-table::
   :header-rows: 1

   * - Field Name
     - Description
   * - ``data``
     - The file information for the current version
   * - ``versions``
     - The file information for all versions (including the current one)

``data`` and ``versions`` are both objects indexed by opusid. ``versions`` is further indexed by version number. Both are then indexed by product type, which gives a list of URLs of associated files.

Examples:

* Retrieve all files associated with a Voyager ISS observation in JSON format.

  `<https://opus.pds-rings.seti.org/opus/api/files/vg-iss-2-s-c4360022.json>`__

  Return value:

::

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

* Retrieve raw images ("Current" version) only for a Galileo SSI observation in JSON format.

  `<https://opus.pds-rings.seti.org/opus/api/files/go-ssi-c0349632000.json?types=gossi_raw>`__

  Return value:

::

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

* Retrieve raw images ("Current" version) and calibrated images (version 1) for a Cassini ISS observation in JSON format.

  `<https://opus.pds-rings.seti.org/opus/api/files/co-iss-n1460973661.json?types=coiss_raw,coiss_calib@1>`__

  Return value:

::

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

* Retrieve all versions of calibrated images for a Cassini ISS observation in JSON format.

  `<https://opus.pds-rings.seti.org/opus/api/files/co-iss-n1460973661.json?types=coiss_calib@all>`__

  Return value:

::

    {
      "data": {
        "co-iss-n1460973661": {
          "coiss_calib": [
            "https://opus.pds-rings.seti.org/holdings/calibrated/COISS_2xxx/COISS_2002/data/1460960653_1461048959/N1460973661_1_CALIB.IMG",
            "https://opus.pds-rings.seti.org/holdings/calibrated/COISS_2xxx/COISS_2002/data/1460960653_1461048959/N1460973661_1_CALIB.LBL"
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
          "2": {
            "coiss_calib": [
              "https://opus.pds-rings.seti.org/holdings/calibrated/COISS_2xxx_v2/COISS_2002/data/1460960653_1461048959/N1460973661_1_CALIB.IMG",
              "https://opus.pds-rings.seti.org/holdings/calibrated/COISS_2xxx_v2/COISS_2002/data/1460960653_1461048959/N1460973661_1_CALIB.LBL"
            ]
          },
          "Current": {
            "coiss_calib": [
              "https://opus.pds-rings.seti.org/holdings/calibrated/COISS_2xxx/COISS_2002/data/1460960653_1461048959/N1460973661_1_CALIB.IMG",
              "https://opus.pds-rings.seti.org/holdings/calibrated/COISS_2xxx/COISS_2002/data/1460960653_1461048959/N1460973661_1_CALIB.LBL"
            ]
          }
        }
      }
    }

* Retrieve drizzle images from an HST WFC3 observation with multiple versions in JSON format.

  `<https://opus.pds-rings.seti.org/opus/api/files/hst-11559-wfc3-ib4v19rp.json>`__

  Return value:

::

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

.. _imagesfmt:

``api/images.[fmt]`` - Return URLs of All Images from a Search
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``api/images/[size].[fmt]`` - Return URLs of Images of a Specific Size from a Search
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``api/image/[size]/[opusid].[fmt]`` - Return URLs of Images of a Specific Size for an OPUS ID
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Get the URLs of images of all sizes (or a given size) based on search criteria and sort order. Image URLs are returned in chunks to limit return size. The starting observation number and the number of observations desired can be specified. An image of a specific size may also be returned for a single OPUS ID.

If specified, ``[size]`` must be one of ``full``, ``med``, ``small``, or ``thumb``.

Supported return formats: ``json``, ``csv``. ``html`` is also supported when a specified size is requested.

Parameters
^^^^^^^^^^

.. list-table::
   :header-rows: 1

   * - Parameter
     - Description
     - Default
   * - ``<searchid>=<value>``
     - Search parameters (including sort order)
     - All observations in database
   * - ``startobs=<N>``
     - The (1-based) observation number to start with
     - 1
   * - ``limit=<N>``
     - The maximum number of observations to return
     - 100

JSON Return Format
^^^^^^^^^^^^^^^^^^

The return value is a JSON object containing this field:

.. list-table::
   :header-rows: 1

   * - Field Name
     - Description
   * - ``data``
     - The images data with one entry per returned observation

When a search was requested, the JSON object also includes these fields:

.. list-table::
   :header-rows: 1

   * - Field Name
     - Description
   * - ``start_obs``
     - Requested starting observation
   * - ``limit``
     - Requested limit
   * - ``count``
     - Number of observations actually returned
   * - ``available``
     - Total number of observations available from this search
   * - ``order``
     - Sort order
   * - ``labels``
     - Requested metadata field names (fully qualified)

When all sizes are requested, ``data`` is an object containing a series of entries, each with these fields:

.. list-table::
   :header-rows: 1

   * - Field Name
     - Description
   * - ``opusid``
     - OPUS ID of the observation
   * - ``<size>_alt_text``
     - Alternate text (image filename)
   * - ``<size>_size_bytes``
     - Size of the image file in bytes
   * - ``<size>_width``
     - Width of the image in pixels
   * - ``<size>_height``
     - Height of the image in pixels
   * - ``<size>_url``
     - Full URL path to the image

When one size is requested, ``data`` an object containing a single entry with these fields:

.. list-table::
   :header-rows: 1

   * - Field Name
     - Description
   * - ``opusid``
     - OPUS ID of the observation
   * - ``alt_text``
     - Alternate text (image filename)
   * - ``size_bytes``
     - Size of the image file in bytes
   * - ``width``
     - Width of the image in pixels
   * - ``height``
     - Height of the image in pixels
   * - ``url``
     - Full URL path to the image

Examples:

* Retrieve information in JSON format about all sizes of images for observations 10-11 from Cassini ISS volume COISS_2002.

  `<https://opus.pds-rings.seti.org/opus/api/images.json?bundleid=COISS_2002&startobs=10&limit=2>`__

  Return value:

::

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

* Retrieve information in JSON format about medium-size images for observations 10-11 from Cassini ISS volume COISS_2002.

  `<https://opus.pds-rings.seti.org/opus/api/images/med.json?bundleid=COISS_2002&startobs=10&limit=2>`__

  Return value:

::

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

* Retrieve information in JSON format about the full-size image for OPUS ID vg-iss-2-s-c4360022.

  `<https://opus.pds-rings.seti.org/opus/api/image/full/vg-iss-2-s-c4360022.json>`__

  Return value:

::

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

CSV Return Format
^^^^^^^^^^^^^^^^^

The return value is a series of text lines. The first returned line contains the column headers. After that is one line per observation containing the information about each image.

Example:

* Retrieve information in CSV format about all sizes of images for observations 10-11 from Cassini ISS volume COISS_2002.

  `<https://opus.pds-rings.seti.org/opus/api/images.csv?bundleid=COISS_2002&startobs=10&limit=2>`__

  Return value:

::

    OPUS ID,Thumb URL,Small URL,Med URL,Full URL
    co-iss-n1460962327,https://opus.pds-rings.seti.org/holdings/previews/COISS_2xxx/COISS_2002/data/1460960653_1461048959/N1460962327_1_full.png
    co-iss-n1460962415,https://opus.pds-rings.seti.org/holdings/previews/COISS_2xxx/COISS_2002/data/1460960653_1461048959/N1460962415_1_full.png

* Retrieve information in CSV format about medium-size images for observations 10-11 from Cassini ISS volume COISS_2002.

  `<https://opus.pds-rings.seti.org/opus/api/images/med.csv?bundleid=COISS_2002&startobs=10&limit=2>`__

  Return value:

::

    OPUS ID,URL
    co-iss-n1460962327,https://opus.pds-rings.seti.org/holdings/previews/COISS_2xxx/COISS_2002/data/1460960653_1461048959/N1460962327_1_med.jpg
    co-iss-n1460962415,https://opus.pds-rings.seti.org/holdings/previews/COISS_2xxx/COISS_2002/data/1460960653_1461048959/N1460962415_1_med.jpg

* Retrieve information in CSV format about the full-size image for OPUS ID vg-iss-2-s-c4360022.

  `<https://opus.pds-rings.seti.org/opus/api/image/full/vg-iss-2-s-c4360022.csv>`__

  Return value:

::

    OPUS ID,URL
    vg-iss-2-s-c4360022,https://opus.pds-rings.seti.org/holdings/previews/VGISS_6xxx/VGISS_6210/DATA/C43600XX/C4360022_full.jpg

HTML Return Format
^^^^^^^^^^^^^^^^^^

The return is an HTML list containing the URLs of the requested images.

Example:

* Retrieve information in HTML format about medium-size images for observations 10-11 from Cassini ISS volume COISS_2002.

  `<https://opus.pds-rings.seti.org/opus/api/images/med.html?bundleid=COISS_2002&startobs=10&limit=2>`__

  Return value:

::

    <ul>
    <li>
    <img id="med__co-iss-n1460962327" src="https://opus.pds-rings.seti.org/holdings/previews/COISS_2xxx/COISS_2002/data/1460960653_1461048959/N1460962327_1_med.jpg">
    </li>
    <li>
    <img id="med__co-iss-n1460962415" src="https://opus.pds-rings.seti.org/holdings/previews/COISS_2xxx/COISS_2002/data/1460960653_1461048959/N1460962415_1_med.jpg">
    </li>
    </ul>

* Retrieve information in HTML format about the full-size image for OPUS ID vg-iss-2-s-c4360022.

  `<https://opus.pds-rings.seti.org/opus/api/image/full/vg-iss-2-s-c4360022.html>`__

  Return value:

::

    <ul>
    <li>
    <img id="full__vg-iss-2-s-c4360022" src="https://opus.pds-rings.seti.org/holdings/previews/VGISS_6xxx/VGISS_6210/DATA/C43600XX/C4360022_full.jpg">
    </li>
    </ul>

.. _infosearchresults:

Getting Information About Search Results
----------------------------------------

.. _resultcountfmt:

``api/meta/result_count.[fmt]`` - Result Count for a Search
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Get the result count for a search.

Supported return formats: ``json``, ``html``, ``csv``

Parameters
^^^^^^^^^^

.. list-table::
   :header-rows: 1

   * - Parameter
     - Description
     - Default
   * - ``<searchid>=<value>``
     - Search parameters (including sort order)
     - All observations in database

Specifying a sort order will not change the number of results, but will be used to cache the actual results in order so that future attempts to perform the search will be faster. Thus if you are planning to perform the search again to retrieve metadata, it is recommended to specify a sort order (if not using the default order) when calling ``api/meta/result_count.[fmt]`` as well.

JSON Return Format
^^^^^^^^^^^^^^^^^^

The return value is a JSON object containing these fields:

.. list-table::
   :header-rows: 1

   * - Field Name
     - Description
   * - ``data``
     - An object containing a single ``result_count`` field

Example:

* Retrieve the number of observations with Pan as the target in JSON format.

  `<https://opus.pds-rings.seti.org/opus/api/meta/result_count.json?target=Pan>`__

  Return value:

::

    {
      "data": [
        {
          "result_count": 1636
        }
      ]
    }

CSV Return Format
^^^^^^^^^^^^^^^^^

The return value is a single text line with the label "result count" followed by the number of results.

* Retrieve the number of observations with Pan as the target in CSV format.

  `<https://opus.pds-rings.seti.org/opus/api/meta/result_count.csv?target=Pan>`__

  Return value:

::

    result count,1636

HTML Return Format
^^^^^^^^^^^^^^^^^^

The return value is an HTML description list containing a single item specifying the label ``result_count`` and the number of results.

* Retrieve the number of observations with Pan as the target in HTML format.

  `<https://opus.pds-rings.seti.org/opus/api/meta/result_count.csv?target=Pan>`__

  Return value:

::

    <dl>
    <dt>result_count</dt><dd>1636</dd>
    </dl>

.. _multsfmt:

``api/meta/mults/[field].[fmt]`` - Return Possible Values for a Multiple-Choice Field
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Returns all possible values for a multiple-choice field and the result count for each value if that value were added to the search constraints.

Supported return formats: ``json``, ``html``, ``csv``

Parameters
^^^^^^^^^^

.. list-table::
   :header-rows: 1

   * - Parameter
     - Description
     - Default
   * - ``<searchid>=<value>``
     - Search parameters (including sort order)
     - All observations in database

Specifying a sort order will not change the results, but will be used to cache the actual results in order so that future attempts to perform the search will be faster. Thus if you are planning to perform the search again to retrieve metadata, it is recommended to specify a sort order (if not using the default order) when calling ``api/meta/mults/[field].[fmt]`` as well.

JSON Return Format
^^^^^^^^^^^^^^^^^^

The return value is a JSON object containing these fields:

.. list-table::
   :header-rows: 1

   * - Field Name
     - Description
   * - ``field_id``
     - The ``fieldid`` requested
   * - ``mults``
     - A JSON object containing the result counts for each choice

Example:

* Retrieve the number of results broken down by ``planet`` for Hubble observations in JSON format.

  `<https://opus.pds-rings.seti.org/opus/api/meta/mults/planet.json?mission=Hubble>`__

  Return value:

::

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

CSV Return Format
^^^^^^^^^^^^^^^^^

The return value is two text lines. The first is a list of choices. The second is a list of result counts broken down by choice.

* Retrieve the number of results broken down by ``planet`` for Hubble observations in CSV format.

  `<https://opus.pds-rings.seti.org/opus/api/meta/mults/planet.csv?mission=Hubble>`__

  Return value:

::

    Earth,Mars,Jupiter,Saturn,Uranus,Neptune,Pluto,Other
    10,354,7956,4885,3395,1800,2051,892

HTML Return Format
^^^^^^^^^^^^^^^^^^

The return value is an HTML description list containing the choices and the result counts broken down by choice.

Example:

* Retrieve the number of results in HTML format broken down by ``planet`` for Hubble observations.

  `<https://opus.pds-rings.seti.org/opus/api/meta/mults/planet.csv?mission=Hubble>`__

  Return value:

::

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

.. _endpointsfmt:

``api/meta/range/endpoints/[field].[fmt]`` - Return Range Endpoints for a Numeric Field
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Return range endpoints for a numeric field, given a search.

Supported return formats: ``json``, ``html``, ``csv``

Parameters
^^^^^^^^^^

.. list-table::
   :header-rows: 1

   * - Parameter
     - Description
     - Default
   * - ``<searchid>=<value>``
     - Search parameters (including sort order)
     - All observations in database
   * - ``units=<unit>``
     - The units to use for the returned values
     - The default unit for the field

Specifying a sort order will not change the results, but will be used to cache the actual results in order so that future attempts to perform the search will be faster. Thus if you are planning to perform the search again to retrieve metadata, it is recommended to specify a sort order (if not using the default order) when calling ``api/meta/range/endpoints/[field].[fmt]`` as well.

JSON Return Format
^^^^^^^^^^^^^^^^^^

The return value is a JSON object containing these fields:

.. list-table::
   :header-rows: 1

   * - Field Name
     - Description
   * - ``min``
     - The minimum value for the field
   * - ``max``
     - The maximum value for the field
   * - ``nulls``
     - The number of null values for the field
   * - ``units``
     - The units of the returned ``min`` and ``max`` fields

Examples:

* Retrieve the range endpoints in the default units (km) for Observed Ring Radius for all Saturn observations in JSON format.

  `<https://opus.pds-rings.seti.org/opus/api/meta/range/endpoints/RINGGEOringradius1.json?target=Saturn>`__

  Return value:

::

    {
      "min": "334.161",
      "max": "12873823.895",
      "nulls": 125566,
      "units": "km"
    }

* Retrieve the range endpoints in units of Saturn radii for Observed Ring Radius for all Saturn observations in JSON format.

  `<https://opus.pds-rings.seti.org/opus/api/meta/range/endpoints/RINGGEOringradius1.json?target=Saturn&units=saturnradii>`__

  Return value:

::

    {
      "min": "0.00553888613",
      "max": "213.39008610973",
      "nulls": 125566,
      "units": "saturnradii"
    }

CSV Return Format
^^^^^^^^^^^^^^^^^

The return value is a series of text lines. The first line contains the column labels ``min,max,nulls,units``. The second line contains the associated values.

Examples:

* Retrieve the range endpoints in the default units (km) for Observed Ring Radius for all Saturn observations in CSV format.

  `<https://opus.pds-rings.seti.org/opus/api/meta/range/endpoints/RINGGEOringradius1.csv?target=Saturn>`__

  Return value:

::

    min,max,nulls,units
    334.161,12873823.895,125566,km

* Retrieve the range endpoints in units of Saturn radii for Observed Ring Radius for all Saturn observations in CSV format.

  `<https://opus.pds-rings.seti.org/opus/api/meta/range/endpoints/RINGGEOringradius1.json?target=Saturn&units=saturnradii>`__

  Return value:

::

    min,max,nulls,units
    0.00553888613,213.39008610973,125566,saturnradii

HTML Return Format
^^^^^^^^^^^^^^^^^^

The return value is an HTML description list containing name/value pairs where the name is the label and the value is the associated value.

Examples:

* Retrieve the range endpoints in the default units (km) for Observed Ring Radius for all Saturn observations in HTML format.

  `<https://opus.pds-rings.seti.org/opus/api/meta/range/endpoints/RINGGEOringradius1.html?target=Saturn>`__

  Return value:

::

    <dl>
    <dt>min</dt><dd>334.161</dd>
    <dt>max</dt><dd>12873823.895</dd>
    <dt>nulls</dt><dd>125566</dd>
    <dt>units</dt><dd>km</dd>
    </dl>

* Retrieve the range endpoints in units of Saturn radii for Observed Ring Radius for all Saturn observations in HTML format.

  `<https://opus.pds-rings.seti.org/opus/api/meta/range/endpoints/RINGGEOringradius1.html?target=Saturn&units=saturnradii>`__

  Return value:

::

    <dl>
    <dt>min</dt><dd>0.00553888613</dd>
    <dt>max</dt><dd>213.39008610973</dd>
    <dt>nulls</dt><dd>125566</dd>
    <dt>units</dt><dd>saturnradii</dd>
    </dl>

.. _categoriesfmt:

``api/categories.json`` - Return Categories from a Search
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Return all category names common to the results of a particular search.

Supported return formats: ``json``

Parameters
^^^^^^^^^^

.. list-table::
   :header-rows: 1

   * - Parameter
     - Description
     - Default
   * - ``<searchid>=<value>``
     - Search parameters (including sort order)
     - All observations in database

Specifying a sort order will not change the results, but will be used to cache the actual results in order so that future attempts to perform the search will be faster. Thus if you are planning to perform the search again to retrieve metadata, it is recommended to specify a sort order (if not using the default order) when calling ``api/categories.json`` as well.

JSON Return Format
^^^^^^^^^^^^^^^^^^

The return value is a JSON list of objects each containing information about one category that contains data for all of the observations resulting from the given search. Each category is described by:

.. list-table::
   :header-rows: 1

   * - Field Name
     - Description
   * - ``table_name``
     - The internal database table table (e.g. ``obs_general``)
   * - ``label``
     - The pretty label as displayed to the user (e.g. ``General Constraints``)

Example:

* Retrieve the categories for all observations that have surface geometry information about Methone in JSON format.

  `<https://opus.pds-rings.seti.org/opus/api/categories.json?surfacegeometrytargetname=Methone>`__

  Return value:

::

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

.. _categoriesopusidfmt:

``api/categories/[opusid].json`` - Return Categories for an OPUS ID
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Return a list of all categories an OPUS ID exists in.

Supported return formats: ``json``

Parameters
^^^^^^^^^^

There are no parameters.

JSON Return Format
^^^^^^^^^^^^^^^^^^

The return value is a JSON list of objects each containing information about one category that contains data for the given OPUS ID. Each category is described by:

.. list-table::
   :header-rows: 1

   * - Field Name
     - Description
   * - ``table_name``
     - The internal database table table (e.g. ``obs_general``)
   * - ``label``
     - The pretty label as displayed to the user (e.g. ``General Constraints``)

Example:

* Retrieve the categories for a Cassini ISS observation in JSON format.

  `<https://opus.pds-rings.seti.org/opus/api/categories/co-iss-w1866600688.json>`__

  Return value:

::

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

.. _producttypesfmt:

``api/product_types.json`` - Return Product Types from a Search
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Return all download product types and associated product versions available from the results of a particular search.

Supported return formats: ``json``

Parameters
^^^^^^^^^^

.. list-table::
   :header-rows: 1

   * - Parameter
     - Description
     - Default
   * - ``<searchid>=<value>``
     - Search parameters (including sort order)
     - All observations in database

Specifying a sort order will not change the results, but will be used to cache the actual results in order so that future attempts to perform the search will be faster. Thus if you are planning to perform the search again to retrieve metadata, it is recommended to specify a sort order (if not using the default order) when calling ``api/product_types.json`` as well.

JSON Return Format
^^^^^^^^^^^^^^^^^^

The return value is a JSON list of objects each containing information about one product type and version that is available for at least one observation returned by the given search. Each product type and version is described by:

.. list-table::
   :header-rows: 1

   * - Field Name
     - Description
   * - ``category``
     - The category of the product type (e.g. ``Cassini ISS``)
   * - ``product_type``
     - The abbreviated name of the product type (e.g. ``coiss_raw``)
   * - ``description``
     - A brief description of the product type (e.g. ``Raw Image``)
   * - ``version_number``
     - A numerical representation of the version number suitable for sorting (999999 means Current)
   * - ``version_name``
     - A string representation of the version number

Example:

* Retrieve the product types and versions for all observations that have surface geometry information about Methone in JSON format.

  `<https://opus.pds-rings.seti.org/opus/api/product_types.json?surfacegeometrytargetname=Methone>`__

  Return value:

::

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

.. _producttypesopusidfmt:

``api/product_types/[opusid].json`` - Return Product Types for an OPUS ID
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Return a list of all download product types and associated product versions available for an OPUS ID.

Supported return formats: ``json``

Parameters
^^^^^^^^^^

There are no parameters.

JSON Return Format
^^^^^^^^^^^^^^^^^^

The return value is a JSON list of objects each containing information about one product type and version that is available for the given OPUS ID. Each product type is described by:

.. list-table::
   :header-rows: 1

   * - Field Name
     - Description
   * - ``category``
     - The category of the product type (e.g. ``Cassini ISS``)
   * - ``product_type``
     - The abbreviated name of the product type (e.g. ``coiss_raw``)
   * - ``description``
     - A brief description of the product type (e.g. ``Raw Image``)
   * - ``version_number``
     - A numerical representation of the version number suitable for sorting (999999 means Current)
   * - ``version_name``
     - A string representation of the version number

Example:

* Retrieve the product types and versions for a Cassini ISS observation in JSON format.

  `<https://opus.pds-rings.seti.org/opus/api/product_types/co-iss-w1866600688.json>`__

  Return value:

::

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

.. _fieldsfmt:

``api/fields.[fmt]`` - Return Information About All Metadata Fields
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Return information about all metadata fields.

Supported return formats: ``json``, ``csv``

Parameters
^^^^^^^^^^

.. list-table::
   :header-rows: 1

   * - Parameter
     - Description
     - Default
   * - ``collapse=<N>``
     - If ``collapse=1`` is given, collapse all surface geometry entries into single generic-target entries
     - 0

JSON Return Format
^^^^^^^^^^^^^^^^^^

The return value is a JSON object containing this field:

.. list-table::
   :header-rows: 1

   * - Field Name
     - Description
   * - ``data``
     - An object containing information about all fields

``data`` is an object indexed by ``fieldid`` containing:

.. list-table::
   :header-rows: 1

   * - Field Name
     - Description
   * - ``field_id``
     - The ``fieldid``
   * - ``category``
     - The full name of the category to which the field belongs
   * - ``type``
     - The data type of the field
   * - ``search_label``
     - The field name as shown on the Search tab (without Min/Max qualifiers)
   * - ``full_search_label``
     - The field name without Min/Max qualifiers but with the category name
   * - ``label``
     - The field name as shown when displaying results (with Min/Max qualifiers as appropriate)
   * - ``full_label``
     - The field name with Min/Max qualifiers (as appropriate) but with the category name
   * - ``available_units``
     - The units that can be used for searching with this field
   * - ``default_units``
     - The default units when none is specified
   * - ``linked``
     - ``true`` if this field is not native to this category but has been linked from its normal location

``type`` can be one of: ``multiple``, ``string``, ``range_integer``, ``range_float``,
``range_longitude``, ``range_time``, or ``range_special``.

Examples:

* Retrieve information about all fields in JSON format.

  `<https://opus.pds-rings.seti.org/opus/api/fields.json>`__

  Return value:

::

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

* Retrieve information about all fields in JSON format.

  `<https://opus.pds-rings.seti.org/opus/api/fields.json?collapse=1>`__

  Return value:

::

    {
      "data": {
        [...]
        "<TARGET> Surface Geometry Constraints": {
          "SURFACEGEO<TARGET>_planetographiclatitude1": {
            "field_id": "SURFACEGEO<TARGET>_planetographiclatitude1",
            "category": "<TARGET> Surface Geometry Constraints",
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
            "old_slug": "SURFACEGEO<TARGET>planetographiclatitude1",
            "slug": "SURFACEGEO<TARGET>_planetographiclatitude1",
            "linked": false
          },
          "SURFACEGEO<TARGET>_planetographiclatitude2": {
            "field_id": "SURFACEGEO<TARGET>_planetographiclatitude2",
            "category": "<TARGET> Surface Geometry Constraints",
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
            "old_slug": "SURFACEGEO<TARGET>planetographiclatitude2",
            "slug": "SURFACEGEO<TARGET>_planetographiclatitude2",
            "linked": false
          },
          [...]
        },
        [...]
      }
    }

CSV Return Format
^^^^^^^^^^^^^^^^^

The return value is a series of text lines. The first line contains the column headers. After that is one line per metadata field containing the field information.

Example:

* Retrieve information about all fields in CSV format.

  `<https://opus.pds-rings.seti.org/opus/api/fields.csv>`__

  Return value:

::

    Field ID,Category,Type,Search Label,Results Label,Full Search Label,Full Results Label,Default Units,Available Units,Old Field ID,Linked
    planet,General Constraints,multiple,Planet,Planet,Planet [General],Planet,,,,0
    target,General Constraints,multiple,Intended Target Name,Intended Target Name,Intended Target Name [General],Intended Target Name,,,,0
    [...]
    rightasc1,General Constraints,range_longitude,Right Ascension,Right Ascension (Min),Right Ascension [General],Right Ascension (Min),degrees,"['degrees', 'hourangle', 'radians']",,0
    rightasc2,General Constraints,range_longitude,Right Ascension,Right Ascension (Max),Right Ascension [General],Right Ascension (Max),degrees,"['degrees', 'hourangle', 'radians']",,0
    declination1,General Constraints,range_float,Declination,Declination (Min),Declination [General],Declination (Min),degrees,"['degrees', 'hourangle', 'radians']",,0
    declination2,General Constraints,range_float,Declination,Declination (Max),Declination [General],Declination (Max),degrees,"['degrees', 'hourangle', 'radians']",,0
    [...]

.. _fieldsfieldfmt:

``api/fields/[field].[fmt]`` - Return Information About a Metadata Field
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Return information about a particular metadata field.

Supported return formats: ``json``, ``csv``

Parameters
^^^^^^^^^^

There are no parameters.

JSON Return Format
^^^^^^^^^^^^^^^^^^

The return value is a JSON object containing this field:

.. list-table::
   :header-rows: 1

   * - Field Name
     - Description
   * - ``data``
     - An object containing information about the requested field

``data`` is an object indexed by ``fieldid`` containing:

.. list-table::
   :header-rows: 1

   * - Field Name
     - Description
   * - ``field_id``
     - The ``fieldid``
   * - ``category``
     - The full name of the category to which the field belongs
   * - ``search_label``
     - The field name as shown on the Search tab (without Min/Max qualifiers)
   * - ``full_search_label``
     - The field name without Min/Max qualifiers but with the category name
   * - ``label``
     - The field name as shown when displaying results (with Min/Max qualifiers as appropriate)
   * - ``full_label``
     - The field name with Min/Max qualifiers (as appropriate) but with the category name
   * - ``available_units``
     - The units that can be used for searching with this field
   * - ``default_units``
     - The default units when none is specified
   * - ``linked``
     - Always ``false`` because this API call returns information about the field's native category

Examples:

* Retrieve information about the ``planet`` field in JSON format.

  `<https://opus.pds-rings.seti.org/opus/api/fields/planet.json>`__

  Return value:

::

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

* Retrieve information about the ``SURFACEGEOrhea_centerphaseangle1`` field in JSON format.

  `<https://opus.pds-rings.seti.org/opus/api/fields/SURFACEGEOrhea_centerphaseangle1.json>`__

  Return value:

::

    {
      "data": {
        "Rhea Surface Geometry Constraints": {
          "SURFACEGEOrhea_centerphaseangle1": {
            "field_id": "SURFACEGEOrhea_centerphaseangle1",
            "category": "Rhea Surface Geometry Constraints",
            "type": "range_float",
            "label": "Phase Angle at Body Center (Min)",
            "search_label": "Phase Angle at Body Center",
            "full_label": "Phase Angle at Body Center (Min) [Rhea]",
            "full_search_label": "Phase Angle at Body Center [Rhea]",
            "default_units": "degrees",
            "available_units": [
              "degrees",
              "hourangle",
              "radians"
            ],
            "old_slug": "SURFACEGEOrhea_centerphaseangle",
            "slug": "SURFACEGEOrhea_centerphaseangle1",
            "linked": false
          }
        }
      }
    }

CSV Return Format
^^^^^^^^^^^^^^^^^

The return value is a series of text lines. The first line contains the column headers. After that is one line per metadata field containing the field information.

Example:

* Retrieve information about the ``planet`` field in CSV format.

  `<https://opus.pds-rings.seti.org/opus/api/fields/planet.csv>`__

  Return value:

::

    Field ID,Category,Type,Search Label,Results Label,Full Search Label,Full Results Label,Default Units,Available Units,Old Field ID,Linked
    planet,General Constraints,multiple,Planet,Planet,Planet [General],Planet,,,,0
