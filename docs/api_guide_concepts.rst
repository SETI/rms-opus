.. This file is the API guide itself; nothing generates it.

.. _basicconcepts:

Basic Concepts: Metadata Fields, Retrieving, and Searching
==========================================================

.. contents::
   :local:
   :depth: 2

.. _apiformat:

API Format
----------

The OPUS API is accessed by encoding requests in individual URLs passed to the OPUS server (normally  ``https://opus.pds-rings.seti.org``). Each request is independent and no state is saved between requests. A URL consists of the prefix components ``/opus/api/`` followed by the API entry point desired. The entry point name is suffixed by the desired format of the returned data (see :ref:`Return Formats <returnformats>`). API calls may take parameters provided after a single ``?``. Each parameter is of the form ``<name>=<value>``. If there is more than one parameter, they are separated by ``&``. Parameters may be encoded using the standard octet encoding detailed in `RFC3986 <https://tools.ietf.org/html/rfc3986>`__, although only ``&``, ``=``, and ``+`` are required to be encoded as octets if used as a parameter's value. Spaces in search values may also be encoded as ``+``.

Examples:

* API call with no parameters:

  `<https://opus.pds-rings.seti.org/opus/api/meta/result_count.json>`__

* API call with one parameter:

  `<https://opus.pds-rings.seti.org/opus/api/meta/result_count.json?bundleid=COISS_2001>`__

* API call with two parameters:

  `<https://opus.pds-rings.seti.org/opus/api/meta/result_count.json?time1=2009-01-01&time2=2010-01-01>`__

.. _opusdatabase:

The OPUS Database
-----------------

The OPUS database contains a set of *observations*. Each observation is identified by a unique *OPUS ID*, which is a short series of characters identifying the mission, instrument, and observation number; the exact format of the OPUS ID varies by mission and instrument (e.g. Cassini ISS: ``co-iss-w1294561143``, HST WFPC2: ``hst-05392-wfpc2-u2930301t``). OPUS IDs can also be used to represent derived or composite products. Each observation is associated with metadata in one or more categories (e.g. "General" or "Ring Geometry"), each of which contains a series of metadata fields. Each metadata field is identified by a *fieldid*, which is a human-readable abbreviation. The list of available categories, metadata fields, and associated information is available :ref:`here <availablefields>` or through the API calls :ref:`api/categories.json <categoriesfmt>`, :ref:`api/categories/[opusid].json <categoriesopusidfmt>`, :ref:`api/fields.[fmt] <fieldsfmt>`, and :ref:`api/fields/[field].[fmt] <fieldsfmt>`.

There are three basic types of fields stored in the database: *multiple-choice*, *string*, and *range*.

* **Multiple-choice** fields contain a single value chosen from a set of valid values. For example, the ``Mission`` field may contain values such as ``Cassini``, ``Voyager``, or ``Hubble``.
* **String** fields contain a single string of arbitrary characters. The formatting is specific to the individual field (e.g. PDS3 volume ID: "COISS_2001", Dataset ID: "CO-E/V/J-ISSNA/ISSWA-2-EDR-V1.0").
* **Range** fields contain either a single value or a pair of values (minimum and maximum). Depending on the field, values may be integers, floating point values, date/time strings, or specially-formatted values such as spacecraft clock count. A single-value field is used for cases where there is only a single value for each observation, such as observation duration (there is only a single duration of time for each observation). Fields with both a minimum and maximum are used when a range of values is appropriate. Examples include observation time (where minimum is the starting time and maximum is the ending time) or right ascension (where minimum and maximum represent the range of right ascension values covered by an observation).

.. _retrievingmetadata:

Retrieving Metadata
-------------------

Some API calls allow you to choose which metadata fields are returned by specifying the parameter ``cols=<fieldid_list>``, where ``<fieldid_list>`` is a comma-separated list of ``fieldid``. For example:

::

    cols=opusid,instrument,planet,target,time1,time2

When a ``cols`` parameter is supported but none is provided, the default columns are used: ``opusid,instrument,planet,target,time1,observationduration``.

If a metadata field is a *single-value range*, then that ``fieldid`` **must** be provided without a numeric suffix (e.g. ``observationduration``). However, if a metadata field contains both a minimum and maximum value in the database (e.g. ``rightasc`` for Right Ascension), then a ``1`` suffix indicating the minimum a ``2`` suffix indicating the maximum must be provided. For example:

::

    cols=observationduration,rightasc1,rightasc2

However, it would be illegal to say ``cols=observationduration1`` or ``cols=rightasc``.

For some numeric fields, the units for the returned values may be specified after a ``:``. For example:

::

    cols=opusid,time1:ydhms,time2:ydhms,observationduration:milliseconds

If no units are specified, the default units are used. A metadata field may be specified more than once with different units if desired:

::

    cols=time1,time1:ydhms,time1:jd,time1:et

See the section on :ref:`Available Metadata Fields <availablefields>` below for more information, including a list of available units for each field.

.. _performingsearches:

Performing Searches
-------------------

Many API calls allow you to select which observations you want to return by specifying a set of search constraints. If no constraints are specified, all observations in the database are returned. A search constraint consists of a ``searchid`` and a desired value. For example:

::

    bundleid=COISS_2001

When searching on a multiple-choice field, additional search values can be specified separated by commas. In this case, observations matching any of the values are returned:

::

    planet=Saturn,Uranus,Neptune

Multiple-choice values are case-insensitive.

More than one search constraint can be specified by joining them with ``&``. When search constraints are specified for different metadata fields, they are "AND"ed together. For example:

::

    bundleid=COISS_2001&planet=Saturn,Uranus,Neptune

will return any observation with Volume ID ``COISS_2001`` **and** a Planet value of ``Saturn``, ``Uranus``, or ``Neptune``.

All numeric ranges may be searched by specifying a minimum value (``1`` suffix), maximum value (``2`` suffix), or both. These suffixes should not be confused with the suffixes used to return metadata. In the case of searches, any range field, whether single-value or not, can have a minimum and maximum search value:

::

    observationduration1=10&observationduration2=20

Fields containing longitudes are treated specially and the minimum search value may be greater than the maximum, in which case the search "wraps around" 360 degrees. For example, it is reasonable to search on a longitude range of 350 to 10 degrees. This will give the opposite results of searching on 10 to 350 degrees.

.. _querytypes:

Query Types
~~~~~~~~~~~

When performing a search, all string and some range fields may have an additional "query type" (*qtype*) that describes how the search should be performed. The query type is specified by including ``qtype-<searchid>=value`` as a search parameter. Note that the ``searchid`` is always specified without a (``1`` or ``2``) suffix, even if the search requires suffixes for minimum and maximum vales. This is because the qtype applies to the entire search field, not to the minimum or maximum values separately. The details of the qtypes associated with each field type are given below.

String Fields
^^^^^^^^^^^^^

Strings can be searched using the following query types:

* **contains**: the search string occurs anywhere within the metadata string. This is the default if no qtype is given.
* **begins**: the search string occurs at the beginning of the metadata string.
* **ends**: the search string occurs at the end of the metadata string.
* **matches**: the search string is exactly equal to the metadata string.
* **excludes**: the search string does *not* appear anywhere in the metadata string.
* **regex**: the metadata string matches the given `regular expression <http://userguide.icu-project.org/strings/regexp>`__.

Range Fields
^^^^^^^^^^^^

Range fields can be searched using the following query types:

* **any**: The observation range overlaps at least some with the search range. In other words, either the observation maximum is greater than the search minimum, or the observation minimum is less than the search maximum. This option is used to request the widest possible set of observations that contain at least some of the range you are searching for. This is the default if no qtype is given.
* **all**: The observation range is a strict superset of the search range. In other words, the observation minimum is less than the search minimum, and the observation maximum is greater than the search maximum. This option is used to ensure that an entire feature you are looking for (such as a crater) is visible in the observation.
* **only**: The observation range is a strict subset of the search range. In other words, the observation minimum is greater than the search minimum, and the observation maximum is less than the search maximum. This option is used to tighly constrain your search to the smallest possible set of results.

.. _units:

Units
~~~~~

When performing a search, some range fields have an additional *unit* that describes what units the search values are in. If no unit is specified, the default for that field is used. The unit is specified by including ``unit-<searchid>=value`` as a search parameter. Note that the ``searchid`` is always specified without a suffix, even if the search requires suffixes for minimum and maximum vales.

.. _clauses:

Multiple Clauses
~~~~~~~~~~~~~~~~

Multiple string and range constraints can be specified for the same field. In this case, the multiple constraints are "OR"ed together. To distinguish between the constraints, the ``searchid``\ s are suffixed with ``_N`` where ``N`` is any positive integer. For example:

::

    observationduration1_1=10&observationduration2_1=20&observationduration1_2=30&observationduration2_2=40

would search for Observation Duration between 10 and 20 seconds (inclusive) *or* between 30 and 40 seconds (inclusive). Each clause can have its own ``qtype`` and ``unit``, if applicable.

.. _sorting:

Sorting
~~~~~~~

By default, the results of a search are sorted first by Observation Start Time (``time1``) and then by OPUS ID (``opusid``). This order can be changed by specifying ``order=<fieldid_list>``, where ``<fieldid_list>`` contains one or more ``fieldid``\ s (as would be used when retrieving metadata) separated by commas. If multiple ``fieldid``\ s are given, the sorting proceeds by the first ``fieldid``, and then if the values are identical by the second ``fieldid``, etc. Sorting is normally done in ascending order, but may be changed to descending for a particular field by prepending the ``fieldid`` with a minus sign (``-``).

Note that if ``opusid`` does not appear in the sort order list, it will automatically be added at the end. Since all OPUS IDs are unique, this guarantees the resulting order is deterministic.

.. _basicconceptexamples:

Examples
~~~~~~~~

* To search for Data Set IDs that contain "ISS" anywhere (the qtype is optional):

::

    datasetid=ISS&qtype-datasetid=contains

* To search for Data Set IDs that start with "CO-E":

::

    datasetid=CO-E&qtype-datasetid=begins

* To search for Volume IDs "COISS_2001" or "COISS_2002":

::

    bundleid_1=COISS_2001&qtype-bundleid_1=matches&bundleid_2=COISS_2002&qtype-bundleid_2=matches

* To search for ring radii between 110,000 and 130,000 km using the "any" qtype (the qtype is optional):

::

    RINGGEOringradius1=110000&RINGGEOringradius2=130000

    RINGGEOringradius1=110000&RINGGEOringradius2=130000&qtype-RINGGEOringradius=any

* To search for ring radii between 1.3 and 1.7 Saturn radii using the "only" qtype:

::

    RINGGEOringradius1=1.3&RINGGEOringradius2=1.7&unit-RINGGEOringradius=saturnradii&qtype-RINGGEOringradius=only

* To search for all Hubble images taken of Jupiter or Saturn in 1994 or 2001 with a spectral bandpass limited to 400-700 nm:

::

    mission=Hubble&observationtype=Image&planet=Jupiter,Saturn&time1_1=1994-01-01T00:00:00.000&time2_1=1994-12-31T23:59:59.999&qtype-time_1=any&time1_2=2001-01-01T00:00:00.000&time2_2=2002-12-31T23:59:59.999&qtype-time_2=any&wavelength1=400&wavelength2=700&qtype-wavelength=only&unit-wavelength=nm

* To search for all Cassini ISS images sorted by filter name then in reverse order by observation duration, and finally by OPUS ID:

::

    instrument=Cassini+ISS&order=COISSfilter,-observationduration,opusid
