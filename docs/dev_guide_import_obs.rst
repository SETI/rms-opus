.. _dev_guide_import_obs:

The Obs Class Hierarchy
=======================

:mod:`opus_import.obs` is the pipeline's largest structure: the family of classes that
computes a column's value. One instance is created per bundle, and
:func:`~opus_import.steps.do_import_obs.import_run_field_function` calls its
``field_obs_<table>_<column>`` method once per column of each table the bundle fills.
**Everything about the hierarchy exists to decide which class that call lands on.**

This chapter covers the root, the PDS-version split, the nine table modules and the two
assembly classes -- the parts every bundle shares.
:ref:`dev_guide_import_obs_classes` covers the mission and volume-set classes above
them.

.. _dev_guide_import_obs_diagram:

The shape of it
---------------

.. mermaid::

    classDiagram
        class ObsBase {
            <<abstract>>
            #_ctx
            #_metadata
            #_bundle
            +bundle
            +opus_id
            +phase_name
            +phase_names
            +instrument_id()*
            +inst_host_id()*
            +mission_id()*
            +primary_filespec()*
            +primary_filespec_from_index_row()*
            +convert_filespec_from_lbl()
            +surface_geo_target_list()
            +compute_longitude_field()
            +compute_d_longitude_field()
            #_pdsfile_from_filespec()*
            #_index_col()
            #_supp_index_col()
            #_some_index_col()
            #_ring_geo_index_col()
            #_sky_geo_index_col()
            #_surface_geo_index_col()
            #_get_target_info()
            #_create_mult()
        }
        class ObsBasePDS3 {
            <<abstract>>
            PDS3 filespecs and time columns
        }
        class ObsBasePDS4 {
            <<abstract>>
            PDS4 filespecs and time columns
        }
        class ObsGeneral {
            <<abstract>>
            obs_general
        }
        class ObsGeneralPDS3 { obs_general, PDS3 }
        class ObsGeneralPDS4 { obs_general, PDS4 }
        class ObsPds {
            <<abstract>>
            obs_pds
        }
        class ObsPdsPDS3 { obs_pds, PDS3 }
        class ObsPdsPDS4 { obs_pds, PDS4 }
        class ObsProfile {
            <<abstract>>
            obs_profile
        }
        class ObsProfilePDS3 { obs_profile, PDS3 }
        class ObsProfilePDS4 { obs_profile, PDS4 }
        class ObsTypeImage { obs_type_image }
        class ObsWavelength { obs_wavelength }
        class ObsRingGeometry { obs_ring_geometry }
        class ObsSurfaceGeometry { obs_surface_geometry }
        class ObsSurfaceGeometryName { obs_surface_geometry_name }
        class ObsSurfaceGeometryTarget { obs_surface_geometry__TARGET }
        class ObsCommonPDS3 {
            <<abstract>>
            combines the nine PDS3 table modules
        }
        class ObsCommonPDS4 {
            <<abstract>>
            combines the nine PDS4 table modules
        }

        ObsBase <|-- ObsBasePDS3
        ObsBase <|-- ObsBasePDS4
        ObsBase <|-- ObsGeneral
        ObsBase <|-- ObsPds
        ObsBase <|-- ObsProfile
        ObsBase <|-- ObsTypeImage
        ObsBase <|-- ObsWavelength
        ObsBase <|-- ObsRingGeometry
        ObsBase <|-- ObsSurfaceGeometry
        ObsBase <|-- ObsSurfaceGeometryName
        ObsBase <|-- ObsSurfaceGeometryTarget
        ObsGeneral <|-- ObsGeneralPDS3
        ObsBasePDS3 <|-- ObsGeneralPDS3
        ObsGeneral <|-- ObsGeneralPDS4
        ObsBasePDS4 <|-- ObsGeneralPDS4
        ObsPds <|-- ObsPdsPDS3
        ObsBasePDS3 <|-- ObsPdsPDS3
        ObsPds <|-- ObsPdsPDS4
        ObsBasePDS4 <|-- ObsPdsPDS4
        ObsProfile <|-- ObsProfilePDS3
        ObsBasePDS3 <|-- ObsProfilePDS3
        ObsProfile <|-- ObsProfilePDS4
        ObsBasePDS4 <|-- ObsProfilePDS4
        ObsGeneralPDS3 <|-- ObsCommonPDS3
        ObsPdsPDS3 <|-- ObsCommonPDS3
        ObsTypeImage <|-- ObsCommonPDS3
        ObsWavelength <|-- ObsCommonPDS3
        ObsProfilePDS3 <|-- ObsCommonPDS3
        ObsRingGeometry <|-- ObsCommonPDS3
        ObsSurfaceGeometry <|-- ObsCommonPDS3
        ObsSurfaceGeometryName <|-- ObsCommonPDS3
        ObsSurfaceGeometryTarget <|-- ObsCommonPDS3
        ObsGeneralPDS4 <|-- ObsCommonPDS4
        ObsPdsPDS4 <|-- ObsCommonPDS4
        ObsTypeImage <|-- ObsCommonPDS4
        ObsWavelength <|-- ObsCommonPDS4
        ObsProfilePDS4 <|-- ObsCommonPDS4
        ObsRingGeometry <|-- ObsCommonPDS4
        ObsSurfaceGeometry <|-- ObsCommonPDS4
        ObsSurfaceGeometryName <|-- ObsCommonPDS4
        ObsSurfaceGeometryTarget <|-- ObsCommonPDS4

The diagram shows every class in this chapter and every direct base of each. The
mission and volume-set classes hang off
:class:`~opus_import.obs.obs_common_pds3.ObsCommonPDS3` and
:class:`~opus_import.obs.obs_common_pds4.ObsCommonPDS4` and are drawn in
:ref:`dev_guide_import_obs_classes`.

"Abstract" here means *a class with a member that raises*
:exc:`NotImplementedError`. Nothing in :mod:`opus_import.obs` inherits from
:class:`abc.ABC` or uses :func:`abc.abstractmethod`; the stubs raise instead, which is
what lets a table module supply a default for a question most instruments answer the
same way while still failing loudly for one that has to answer it itself.

**The diagram marks a class abstract where it *introduces* such a member**, not where it
merely inherits one. By the second reading almost every class above is abstract, because
:class:`~opus_import.obs.obs_base.ObsBase`'s eight raising members are inherited all the
way down: none of these classes can be instantiated and asked for a row.
:class:`~opus_import.obs.obs_general_pds4.ObsGeneralPDS4` is the clearest case -- it
introduces nothing at all, and exists only to put the PDS4 base into a class's ancestry.
The first class in any of these chains that can actually compute a row is a leaf.

The five kinds of module
------------------------

**The root.** :mod:`opus_import.obs.obs_base` owns the per-observation metadata, the
helpers that read a value out of a PDS index, and the mult builder.

**The PDS-version split.** :mod:`opus_import.obs.obs_base_pds3` and
:mod:`opus_import.obs.obs_base_pds4` answer the questions a PDS version decides: where a
file specification comes from, and what the time columns are called.

**One module per OPUS table.** Nine of them, three with a ``_pds3``/``_pds4`` variant of
their own.

**Two assembly classes.** :class:`~opus_import.obs.obs_common_pds3.ObsCommonPDS3` and
:class:`~opus_import.obs.obs_common_pds4.ObsCommonPDS4` combine all nine table modules
so that a mission class names one base instead of nine. Neither introduces behavior of
its own; each exists so that the order the nine are combined in is written down once.

**One module per mission, and one per bundle or volume set.** These are
:ref:`dev_guide_import_obs_classes`.

Import a class from its own module (``from opus_import.obs.obs_base import ObsBase``).
The package deliberately re-exports nothing, because importing every leaf class in the
package's ``__init__`` would import every mission's parsing code no matter which bundle
is running.

.. _dev_guide_import_obs_mro:

How a method is chosen
----------------------

The method resolution order that falls out of this is not obvious, and getting it wrong
is the usual way a new class misbehaves. A leaf class's order runs: the leaf, then the
mission's PDS-version half, then the assembly class, then the table modules in the order
that class lists them, and finally the mission's PDS-version-independent half and the
root.

Reading a Cassini ISS volume's order off the tree gives:

.. code-block:: text

    ObsVolumeCOISS12xxx     the volume set
    ObsCassiniCommonPDS3    the mission, PDS3 half
    ObsCommonPDS3           the assembly class
    ObsGeneralPDS3, ObsGeneral, ObsPdsPDS3, ObsPds, ObsTypeImage, ObsWavelength,
    ObsProfilePDS3, ObsProfile      one per table, in the order ObsCommonPDS3 lists them
    ObsBasePDS3             the PDS3 base, released here by the last table module
                            above that derives from it
    ObsRingGeometry, ObsSurfaceGeometry, ObsSurfaceGeometryName,
    ObsSurfaceGeometryTarget        the remaining table modules
    ObsCassiniCommon        the mission's PDS-version-independent half
    ObsBase                 the root

So a bundle module overrides everything, and a mission's PDS-version half overrides the
table modules. Two consequences surprise people:

* **The PDS-version base lands in the middle of the table modules**, not after them.
  Some of them derive from it, and Python places it as soon as the last of those has
  been placed. A default defined in :mod:`opus_import.obs.obs_base_pds3` is therefore
  overridden by every table module the assembly class lists up to and including the last
  one deriving from it -- which is *not* the same set as the ones that derive from it --
  and overrides every table module listed after that.
* **A mission's PDS-version-independent half sits below every table module**, so a
  default it defines is overridden by any table module that defines the same name.

Read the split off the tree rather than off a list: the assembly class's base order is
what decides it, and :mod:`opus_import.obs` is the authoritative statement.

.. _dev_guide_import_obs_base:

The root: ObsBase
-----------------

:class:`opus_import.obs.obs_base.ObsBase`

One instance is created per bundle, not per observation.
:func:`~opus_import.steps.do_import_index.import_one_index` mutates the metadata
dictionary in place for each row it reads, so **no method may cache anything derived
from it**. :attr:`~opus_import.obs.obs_base.ObsBase.opus_id` shows what caching is
allowed to look like: it re-derives whenever the file specification it was computed from
changes.

Construction and attributes
~~~~~~~~~~~~~~~~~~~~~~~~~~~

``ObsBase(ctx, bundle=None, metadata=None)``. Four instance attributes plus two cache
slots:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Attribute
     - Meaning
   * - ``_ctx``
     - The run's :class:`~opus_import.context.ImportContext`. **An obs class uses it
       only to log and to read the run's arguments; it never reaches the database
       through it**, which is what lets
       :func:`~opus_import.steps.do_import_obs.import_run_field_function` treat a field
       method's exception as a bad field rather than an aborted import.
   * - ``_bundle``
     - The PDS3 volume or PDS4 bundle being imported, exposed as
       :attr:`~opus_import.obs.obs_base.ObsBase.bundle`.
   * - ``_metadata``
     - Everything the import has assembled for the current observation. **It is the same
       dictionary object for the whole index file, mutated in place.** It is None while
       the tables are being created, before any observation has been read.
   * - ``_ignore_errors``
     - ``--import-ignore-errors``, read off the run's arguments at construction rather
       than taken as a parameter, so that every construction site reaches the branches
       that consult it. Read eagerly, so a context built without real parsed arguments
       fails at construction rather than only on a rare error path.
   * - ``_opus_id_last_filespec``, ``_opus_id_cached``
     - The one permitted cache: the last file specification the OPUS ID was derived
       from, and the id.

The metadata dictionary
~~~~~~~~~~~~~~~~~~~~~~~

A subclass reads it through the ``_*_col`` helpers rather than reaching into it, because
those apply the ``pdstable`` mask that marks a value as missing. The keys
:func:`~opus_import.steps.do_import_index.import_one_index` fills, and which an obs
class may read:

.. list-table::
   :header-rows: 1
   :widths: 34 66

   * - Key
     - Contents
   * - ``index``, ``index_label``
     - Every row of the primary index, and the index's own label.
   * - ``index_row``, ``index_row_num``
     - The row being imported, and its 1-based number.
   * - ``supp_index``, ``supp_index_row``, ``supp_index_label``
     - The supplemental index keyed by file specification, this observation's row (or
       None), and the file's label.
   * - ``ring_geo``, ``ring_geo_row``, ``ring_geo_label``
     - The ring geometry summary, likewise. ``sky_geo`` and ``inventory`` follow the
       same pattern.
   * - ``surface_geo``, ``surface_geo_row``, ``surface_geo_target_name``
     - The surface geometry summaries keyed by file specification and then by target;
       the row for the target currently being computed, and that target's name.
   * - ``inventory_list``, ``used_surface_geo_targets``
     - The target list from the inventory file, and the targets surface geometry rows
       were actually found for.
   * - ``phase_name``, ``temporal_camera``
     - The phase currently being computed, and the bundle's ``temporal_camera`` flag.
   * - ``table_name``, ``field_name``
     - The table and column currently being computed, set by
       :func:`~opus_import.steps.do_import_obs.import_observation_table`.
   * - ``<table_name>_row``
     - Each row computed so far for this observation, which is how a later table's field
       methods read what an earlier one produced.

The abstract contract
~~~~~~~~~~~~~~~~~~~~~

Eight members raise :exc:`NotImplementedError`. Every one is answered somewhere between
here and the leaf class.

.. list-table::
   :header-rows: 1
   :widths: 34 20 46

   * - Member
     - Supplied by
     - Must return
   * - :attr:`~opus_import.obs.obs_base.ObsBase.instrument_id`
     - an instrument class
     - The OPUS instrument id, such as ``'COISS'``, or None for a bundle whose
       instrument is not known until an observation has been read -- which is what
       decides that no ``obs_instrument_*`` table is created for it.
   * - :attr:`~opus_import.obs.obs_base.ObsBase.inst_host_id`
     - an instrument class
     - The spacecraft id, such as ``'CO'``.
   * - :attr:`~opus_import.obs.obs_base.ObsBase.mission_id`
     - an instrument class
     - The mission id, which selects the ``obs_mission_*`` table.
   * - :attr:`~opus_import.obs.obs_base.ObsBase.primary_filespec`
     - an instrument class
     - The path, relative to the holdings root, of this observation's data file, or None
       for an index row naming no data file.
   * - :meth:`~opus_import.obs.obs_base.ObsBase.primary_filespec_from_index_row`
     - a PDS-version base
     - The same, built from a row of *any* of the bundle's index files, which is how a
       supplemental or geometry row is matched to its primary one.
   * - ``_pdsfile_from_filespec``
     - a PDS-version base
     - The ``rms-pdsfile`` object for a file specification.
   * - ``_time_from_some_index``, ``_time2_from_some_index``
     - a PDS-version base
     - The start and stop times in seconds TAI, or None.

Three more members are declared here with a working default and are meant to be
overridden where a bundle differs:

* :attr:`~opus_import.obs.obs_base.ObsBase.phase_names` returns ``['']`` -- one
  observation per index row. An instrument whose row describes several observations
  overrides it with one name per observation, and every field method is then called once
  per name.
* :meth:`~opus_import.obs.obs_base.ObsBase.surface_geo_target_list` returns None,
  meaning the surface geometry comes from separate summary files. An instrument that
  carries it inline overrides it with the target names.
* :meth:`~opus_import.obs.obs_base.ObsBase.convert_filespec_from_lbl` returns its
  argument unchanged. An instrument whose primary file specification names a ``.LBL``
  file overrides it, because the data file's extension is instrument-specific.

Reading the indexes
~~~~~~~~~~~~~~~~~~~

Every ``_*_col`` helper returns **whatever the PDS parser produced** -- a string, a
number, or None -- because a PDS index is untyped as far as this code is concerned. It
is the field method calling it that declares, from its schema column, what the value is
supposed to be.

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Helper
     - Reads
   * - ``_index_col(col, idx=None)``
     - The primary index row.
   * - ``_index_label_col(col, idx=None)``
     - A keyword of the primary index's own label, which describes the whole file and is
       therefore the same for every observation in it.
   * - ``_has_supp_index()``, ``_supp_index_col(col, idx=None)``
     - The supplemental index row.
   * - ``_col_in_index(col)``, ``_col_in_some_index(col)``, ``_col_in_some_index_or_label(col)``
     - Which index carries a column. **The supplemental index wins** when both do, which
       is what decides the value for COCIRS_0xxx and COCIRS_1xxx. The label form tries
       the supplemental row, the primary row, the supplemental label and the primary
       label, in that order.
   * - ``_some_index_col(col, idx=None)``, ``_some_index_or_label_col(col, idx=None)``
     - Whichever of those carries it, logging an error if none does.
   * - ``_ring_geo_index_col(col, col2=None, col3=None, idx=None, missing_ok=False)``
     - The ring geometry summary row. Unlike the others this one declares a float,
       because every column of a geometry summary file is one. The ``col2``/``col3``
       fallbacks support both the older geometry files, where a gridless quantity has
       one column, and the newer ones, where it has a minimum and a maximum. Returns
       None quietly when the bundle has no ring geometry or the observation has no row.
   * - ``_surface_geo_index_col(...)``
     - The same, against the surface geometry row for the current target.
   * - ``_sky_geo_index_col(col, idx=None)``
     - The sky geometry row. No fallback spellings and no error logging.

Building a mult value
~~~~~~~~~~~~~~~~~~~~~

A group column stores an index into a ``mult_`` table rather than the value itself, and
that table also carries how the web application presents the value.
``_create_mult(col_val, disp_name=None, disp='Y', disp_order=None, grouping=None,
group_disp_order=None, tooltip=None, aliases=None)`` builds the dictionary a group
column's field method must return. Everything but ``col_val`` is presentation, and every
one of those may be left out --
:func:`~opus_import.steps.do_import_mult.update_mult_table` derives a label and a sort
order from the value when none is given.

``_create_mult_keep_case`` is the variant that passes the value through as the label
rather than letting the derivation title-case it, which is what a value whose
capitalization carries meaning -- a filter name, an observation name -- needs.

Other helpers
~~~~~~~~~~~~~

``_get_target_info(target_name)``
    Upper-cases the name, folds it through
    ``TARGET_NAME_MAPPING`` (:mod:`opus_import.config_targets.target_name_mapping`), and
    looks it up in
    ``TARGET_NAME_INFO`` (:mod:`opus_import.config_targets.target_name_info`). An unknown
    name is reported through
    :meth:`~opus_import.context.ImportLog.unknown_target_name` and returns
    ``(None, None)`` -- or ``OTHER`` under ``--import-ignore-errors``, so the
    observation still imports.

``_get_planet_group_info(target_name)``
    The search form's group label and sort key for a target's planet.

``_time_helper(index, column, missing_index_ok=False)`` and ``_time2_helper(...)``
    Read an ISO time out of one of the indexes and convert it to seconds TAI, logging an
    unparsable one. The stop-time form additionally holds the stop time at or after the
    start time, logging a warning and substituting the start time when the pair is
    reversed -- because otherwise the range is unsearchable.

``_parse_sclk(parse_func, sclk, mission_name, log_func=None)``
    Parse a spacecraft clock count, reporting a bad one instead of raising. Every
    mission needs the same error handling, so each mission class wraps this in a
    ``_parse_<mission>_sclk`` helper and its field methods call that.

``compute_longitude_field()`` and ``compute_d_longitude_field()``
    The values a ``LONGITUDE_FIELD`` and a ``D_LONGITUDE_FIELD`` data source ask for:
    the center of the range, normalized to ``[0, 360)``, and half its span. Storing the
    center and the span rather than the endpoints is what lets a search wrap around
    zero.

``_log_warning``, ``_log_nonrepeating_warning``, ``_log_nonrepeating_error``, ``_log_unknown_target_name``
    The logging surface an obs class has. The non-repeating forms log a given message
    once per run, which is what keeps a fault shared by every row of an index out of the
    log a hundred thousand times.

.. _dev_guide_import_obs_field_types:

What a field method returns
---------------------------

:mod:`opus_import.obs.field_types` declares the types a
``field_obs_<table>_<column>`` method may return. **The column's schema decides which
one**, and ``tests/opus_import/test_obs_field_annotations.py`` is what checks that every
method's annotation matches its column. That test is the authority; the rule it applies
is written once, inside it, and deliberately not restated here.

.. list-table::
   :header-rows: 1
   :widths: 24 76

   * - Alias
     - Covers
   * - :data:`~opus_import.obs.field_types.StrField`
     - ``char*``, ``varchar*`` and ``text`` columns, and the one ``json`` column
       (``obs_general.preview_images``, whose method returns the output of
       :func:`json.dumps`).
   * - :data:`~opus_import.obs.field_types.FloatField`
     - ``real4`` and ``real8`` columns.
   * - :data:`~opus_import.obs.field_types.IntField`
     - ``int*`` and ``uint*`` columns.
   * - :class:`~opus_import.obs.field_types.MultField`
     - One value of a ``GROUP`` column, as the eight-key dictionary
       ``_create_mult`` builds.
   * - :data:`~opus_import.obs.field_types.MultFieldRet`
     - What a ``GROUP`` column's method returns: a
       :class:`~opus_import.obs.field_types.MultField` or a list of them. A
       ``MULTIGROUP`` column is annotated ``list[MultField]`` instead.

Two rules are worth stating explicitly, because both are easy to get wrong:

* **The form type decides, not the storage type.** A ``flag_yesno`` or ``flag_onoff``
  column is stored as ``int unsigned`` exactly like a ``mult_idx`` one, because it *is*
  an index into a ``mult_`` table, so its method returns a
  :class:`~opus_import.obs.field_types.MultField`. So does the one ``char3`` column that
  carries a ``GROUP`` form type. Returning a bare value from a group column makes
  :func:`~opus_import.steps.do_import_obs.import_observation_table` log ``bad data type
  returned for mult`` and **discard the whole observation**.
* **A PDS index does not hand out builtin integers.** ``pdstable`` parses an integer
  column with NumPy, so what reaches a field method is a ``numpy.int64``, which is not
  an :class:`int`. :func:`~opus_import.obs.field_types.as_int` is what converts one, and
  raises if the conversion is not exact. ``numpy.float64`` *does* subclass
  :class:`float` and ``numpy.str_`` *does* subclass :class:`str`, so
  :data:`~opus_import.obs.field_types.FloatField` and
  :data:`~opus_import.obs.field_types.StrField` need no equivalent.

Two keys of :class:`~opus_import.obs.field_types.MultField` are inert: nothing reads
``tooltip`` -- a ``mult_`` table has no such column -- and no obs class passes either
``tooltip`` or ``aliases``, so both are None in every row the pipeline writes.

.. _dev_guide_import_obs_version_bases:

The PDS-version bases
---------------------

:class:`~opus_import.obs.obs_base_pds3.ObsBasePDS3`
    Builds a file specification out of a PDS3 index row: it checks ``VOLUME_ID`` -- or
    ``VOLUME_NAME``, for an index that has no ``VOLUME_ID`` -- against the bundle being
    imported, takes ``FILE_SPECIFICATION_NAME`` if it is there, and otherwise joins
    ``PATH_NAME`` and ``FILE_NAME``. It prepends the bundle id unless the row
    already carries it, which GOSSI and COUVIS_0xxx do. It supplies
    ``_time_from_index``, ``_time_from_supp_index``, ``_time2_from_index`` and
    ``_time2_from_supp_index`` defaulting to ``START_TIME`` and ``STOP_TIME``, and
    resolves ``_time_from_some_index`` across both indexes.

    The ``add_phase_from_row`` and ``add_phase_from_inst`` flags append ``_ir`` or
    ``_vis``, which is what distinguishes the two rows COVIMS geometry indexes carry per
    observation.

:class:`~opus_import.obs.obs_base_pds4.ObsBasePDS4`
    Much simpler: a PDS4 index row carries its own ``filepath`` column, so the file
    specification is that value and the three remaining arguments are ignored. The time columns
    default to ``pds:start_date_time`` and ``pds:stop_date_time``, and there is **no
    supplemental-index form** of either, because the PDS4 bundles OPUS imports have
    none.

.. _dev_guide_import_obs_table_modules:

The table modules
-----------------

Nine modules, one per OPUS table. Each holds that table's ``field_obs_*`` methods, and
each method fills the schema column its name ends in. Per the project's coding
conventions, a ``field_obs_*`` method carries no individual docstring -- each class says
so once in its own -- because the authoritative statement of what one returns is its
schema column plus the test that checks the correspondence. Two methods of
:class:`~opus_import.obs.obs_volume_covims_0xxx.ObsVolumeCOVIMS0xxx` are the exception,
and say something the schema cannot.

ObsGeneral -- ``obs_general``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:class:`opus_import.obs.obs_general.ObsGeneral`

What every observation has: its ids, its target, its times, and its sky position. This
is the master table, and every other table's rows hang off it.

The methods fall into three groups:

* **Do not override** -- ``opus_id``, ``bundle_id``, ``instrument_id``,
  ``inst_host_id``, ``mission_id``, ``target_class``, ``primary_filespec`` and
  ``preview_images``. These are derived from the contract members above.
  ``preview_images`` is the interesting one: it asks ``rms-pdsfile`` for a view set and
  renders it to JSON, and it honors ``--import-ignore-missing-images`` and
  ``--import-fake-images``. Its handling of a miss is load-bearing, because a miss comes
  back two different ways: ``rms-pdsfile`` answers a file that does not exist, and a
  directory whose candidate children all decline, with None -- while everything else that
  fails gets an *empty* view set, which is falsy, is not None, and whose ``thumbnail``
  raises. The test therefore has to reject both.
* **Might override** -- ``target_name``, ``time1``, ``time2``,
  ``observation_duration``, the four right-ascension and declination columns, and
  ``ring_obs_id``. The four sky columns and ``ring_obs_id`` default to None;
  ``observation_duration`` is ``max(time2 - time1, 0)``.
* **Must override** -- ``planet_id``, ``quantity`` and ``observation_type``, each of
  which raises. ``_target_name`` belongs with them: it returns one ``(name, shown name)``
  pair per target and raises too, since no two archives record the target the same way,
  even though the source files it under the might-override banner.

:class:`~opus_import.obs.obs_general_pds3.ObsGeneralPDS3` supplies ``_target_name`` from
``TARGET_NAME`` in whichever index or label carries it.
:class:`~opus_import.obs.obs_general_pds4.ObsGeneralPDS4` supplies **nothing**: the
pairing exists to put the PDS4 base into the class's ancestry, and a PDS4 bundle class
has to answer ``_target_name`` itself.

ObsPds -- ``obs_pds``
~~~~~~~~~~~~~~~~~~~~~

:class:`opus_import.obs.obs_pds.ObsPds`

What the PDS archive says about the product: its data set, its product id, and when it
was made. ``opus_id``, ``bundle_id``, ``instrument_id`` and ``primary_filespec`` are
derived; ``data_set_id``, ``product_id``, ``product_creation_time`` and ``primary_lid``
raise; ``note`` defaults to None.

The two variants split on identity: a PDS3 product has a data set id and a product id
and no logical identifier, so :class:`~opus_import.obs.obs_pds_pds3.ObsPdsPDS3` fills
the first two from ``DATA_SET_ID`` and ``PRODUCT_ID`` and leaves ``primary_lid`` None. A
PDS4 product is the other way round, so
:class:`~opus_import.obs.obs_pds_pds4.ObsPdsPDS4` fills ``primary_lid`` from
``pds:logical_identifier`` and leaves the other two None. Both are stored so that a
search can use either.

ObsTypeImage -- ``obs_type_image``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:class:`opus_import.obs.obs_type_image.ObsTypeImage`

An image's dimensions and its intensity levels. Everything but the three derived id
columns defaults to None or to a null mult, because an observation that is not an image
fills none of it. Three module constants give the number of distinct intensity levels a
detector of a given bit depth records: ``EIGHT_BIT_IMAGE_LEVELS``,
``TWELVE_BIT_IMAGE_LEVELS`` and ``SIXTEEN_BIT_IMAGE_LEVELS``.

``duration`` deliberately does **not** default to the observation's duration: it is None
unless the observation is an image at all.

ObsWavelength -- ``obs_wavelength``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:class:`opus_import.obs.obs_wavelength.ObsWavelength`

The observation's spectral coverage and resolution, in both wavelength and wavenumber.
**Units are the thing to get right here.** Wavelengths are stored in microns and
wavenumbers in cm\ :sup:`-1`, and the module constant ``MICRONS_PER_CM`` (10000.0) is
the conversion: ``wavelength = MICRONS_PER_CM / wavenumber``, and a resolution converts
as ``MICRONS_PER_CM * resolution / wavelength**2`` -- the square of the wavelength the
resolution applies at, which is what the two conversion helpers divide by. The wavenumber
columns default to
the converted wavelengths, and four helpers derive a resolution from a full bandwidth or
from the other system's resolution, so a subclass usually supplies only the two
wavelength endpoints.

ObsProfile -- ``obs_profile``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:class:`opus_import.obs.obs_profile.ObsProfile`

What an occultation profile records: its direction, its source, and its optical depth.
Ten of its methods raise here, and both PDS-version variants
(:class:`~opus_import.obs.obs_profile_pds3.ObsProfilePDS3` and
:class:`~opus_import.obs.obs_profile_pds4.ObsProfilePDS4`) concretize all ten with
empty defaults -- because the table has a row for *every* observation, so a bundle that
is not an occultation must not be required to answer.

Two helpers serve the occultation classes: ``_star_name_helper`` reads a star name out
of an index and resolves it, and ``_prof_ra_dec_helper`` returns the four right-ascension
and declination columns from
``STAR_RA_DEC`` (:mod:`opus_import.config_targets.star_ra_dec`), widened by the class
constant ``_STAR_RA_DEC_SLOP`` -- which is 0.0, a decision recorded in the source, so
stars are fixed points.

ObsRingGeometry -- ``obs_ring_geometry``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:class:`opus_import.obs.obs_ring_geometry.ObsRingGeometry`

Where the observation fell on a ring plane, and at what angles. It is the largest table
module: 84 field methods, none abstract, almost all of them reading a column of the ring
geometry summary through ``_ring_geo_index_col``. They are grouped by radius and
longitude, distance and resolution, observed lighting geometry, ring-center lighting
geometry, edge-on viewing geometry, pole, image geometry and timing.

Two things in it are not a plain read:

* **Ascending-node longitudes.** A module constant gives each planet's ring-plane
  ascending node in degrees from the J2000 prime meridian, and
  ``_j2000_to_ascending`` / ``_ascending_to_j2000`` convert between the two systems.
  Eight columns try the summary file's own ``..._WRT_NODE`` column first and fall back
  to the
  conversion, with a special case that keeps a 0--360 range as 0--360, because nothing
  else would make sense.
* :meth:`~opus_import.obs.obs_ring_geometry.ObsRingGeometry.validate_ring_geo_fields`
  reports a **gridless** value whose minimum and maximum disagree -- twelve column stems
  covering ring-center distance, the sub-solar and sub-observer longitudes, the
  ring-center angles and the two opening angles. It returns immediately when the
  bundle's ``temporal_camera`` flag is set, because such an observation legitimately
  spans enough time for those to vary, and it exempts a 0/360 pair on a longitude
  column. :func:`~opus_import.steps.do_import_obs.import_observation_table` calls it
  unless ``--import-ignore-geo-mismatch``.

The three surface geometry modules
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Surface geometry is three tables, because it answers three different questions.

:class:`~opus_import.obs.obs_surface_geometry.ObsSurfaceGeometry` -- ``obs_surface_geometry``
    **Which bodies the observation covered**, as one comma-separated list of display
    names built from the inventory file's target list. A single unknown target name
    makes the whole column None. Under ``--import-report-inventory-mismatch`` it also
    builds the same list from the targets surface geometry rows were actually found for
    and warns when they differ -- retrying first with the central planets removed, since
    it is fine for the surface geometry to carry the central planet when the inventory
    does not.

:class:`~opus_import.obs.obs_surface_geometry_name.ObsSurfaceGeometryName` -- ``obs_surface_geometry_name``
    **The one body a per-target geometry row belongs to.** It has one field method of
    substance, which reads ``surface_geo_target_name`` off the metadata, resolves it, and
    builds a mult carrying the target's display name and its planet group. This is the
    many-to-one mapping of rows to OPUS IDs.

:class:`~opus_import.obs.obs_surface_geometry_target.ObsSurfaceGeometryTarget` -- ``obs_surface_geometry__<TARGET>``
    **Where the observation fell on one body's surface**: 62 field methods reading the
    surface geometry summary row for the current target, grouped by planetographic and
    planetocentric latitude, west longitude, distance and resolution, lighting geometry,
    pole and limb, image geometry and timing. The eight **east longitude** columns are
    computed rather than read, and are marked do-not-override: six are
    ``(360 - west) % 360``, with a special case keeping a 360 as 360, and the two
    observer columns are the plain negation instead.
    :meth:`~opus_import.obs.obs_surface_geometry_target.ObsSurfaceGeometryTarget.validate_surface_geo_fields`
    is the surface counterpart of the ring validator, over nine gridless stems.

.. _dev_guide_import_obs_target_template:

One class, many tables
~~~~~~~~~~~~~~~~~~~~~~

There is exactly one :class:`~opus_import.obs.obs_surface_geometry_target.ObsSurfaceGeometryTarget` class
and one template schema, and the
``<TARGET>`` placeholder is substituted at three separate points. This is the mechanism
to understand before touching surface geometry:

1. **The table list carries the placeholder.** ``TABLES_TO_POPULATE`` ends with
   ``obs_surface_geometry__<TARGET>``.
2. **The schema reader expands it.**
   :func:`~opus_import.import_util.read_schema_for_table` recognizes a name starting
   ``obs_surface_geometry__``, redirects to ``obs_surface_geometry_target.json``, and
   substitutes ``<TARGET>`` with
   :func:`~opus_import.import_util.table_name_for_sfc_target` and ``<SLUGTARGET>`` with
   :func:`~opus_import.import_util.slug_name_for_sfc_target`. The substitution is plain
   text, applied to the file's contents before it is parsed.
3. **The field-method lookup collapses back to the template name.**
   :func:`~opus_import.steps.do_import_obs.field_function_name` maps every
   ``obs_surface_geometry__<TARGET>`` table onto
   ``obs_surface_geometry_target``, which is why the methods are named
   ``field_obs_surface_geometry_target_*`` while the tables are not.

The driver loops the targets, replaces the token in the table name, and rewrites two
metadata keys per iteration -- and hands
:func:`~opus_import.steps.do_import_obs.import_observation_table` the **unsubstituted**
template schema with the **substituted** table name.
:func:`~opus_import.import_util.slug_name_for_sfc_target` carries a warning worth
repeating: changing it means changing ``getSurfacegeoTargetSlug`` in the front end's
``utils.js`` too.

The assembly classes
--------------------

:class:`~opus_import.obs.obs_common_pds3.ObsCommonPDS3` and
:class:`~opus_import.obs.obs_common_pds4.ObsCommonPDS4` each list the same nine table
modules in the same order -- general, pds, type image, wavelength, profile, ring
geometry, surface geometry, surface geometry name, surface geometry target -- differing
only in the three PDS-version variants. That order is what decides which module wins
when two define the same method, and it is the only reason these classes exist.

Where to go next
----------------

:ref:`dev_guide_import_obs_classes` walks the mission and volume-set classes.
:ref:`dev_guide_import_extending` is the recipe for adding one.

API reference
-------------

:doc:`api_opus_import`
