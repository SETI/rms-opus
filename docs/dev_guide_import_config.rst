.. _dev_guide_import_config:

Import Configuration Data
=========================

Three modules and one package answer the question "what exists?": which missions,
spacecraft and instruments OPUS knows, which bundles it can import and how, and which
targets it can name. They are plain module-level constants -- the import reads them and never writes
them -- and adding a mission, an instrument or a bundle means editing them.

This chapter documents every one of them. :ref:`dev_guide_import_extending` is the
recipe that puts them together.

.. _dev_guide_import_config_data:

opus_import.config_data
-----------------------

The names, ids and orderings shared across missions and instruments. Nine constants,
all read-only.

``GROUP_FORM_TYPES``
~~~~~~~~~~~~~~~~~~~~

``['GROUP', 'MULTIGROUP']`` -- the ``param_info`` form types that have a ``mult_``
table. A column whose ``pi_form_type`` names one of these stores a ``mult_`` row id
rather than its value. :func:`opus_import.importdb.get_db` is handed this list, and
:func:`~opus_import.steps.do_import_obs.import_observation_table` tests against it to
decide whether to route a value through
:func:`~opus_import.steps.do_import_mult.update_mult_table`.

``TABLES_TO_POPULATE``
~~~~~~~~~~~~~~~~~~~~~~

The tables OPUS fills for each observation, **in the order it fills them**:

.. code-block:: text

    obs_general
    obs_pds
    obs_mission_<MISSION>
    obs_instrument_<INST>
    obs_type_image
    obs_wavelength
    obs_profile
    obs_files
    obs_ring_geometry
    obs_surface_geometry
    obs_surface_geometry_name
    obs_surface_geometry__<TARGET>

Three of the names carry a placeholder, substituted per bundle by
:func:`~opus_import.steps.do_import_tables.create_tables_for_import`:

.. list-table::
   :header-rows: 1

   * - Placeholder
     - Replaced with
   * - ``<MISSION>``
     - The mission's table suffix, lowercased --
       ``MISSION_ID_TO_MISSION_TABLE_SFX[mission_id]``. ``CO`` gives
       ``obs_mission_cassini``.
   * - ``<INST>``
     - The instrument id, lowercased. ``COISS`` gives ``obs_instrument_coiss``.
   * - ``<TARGET>``
     - The encoded target name, from
       :func:`~opus_import.import_util.table_name_for_sfc_target`. Unlike the other
       two, this is **not** substituted when the tables are created: which targets an
       observation mentions is not known until the index has been read, so the
       ``obs_surface_geometry__<TARGET>`` tables are created during the write-out and
       discovered by listing the database when the copy to the permanent namespace
       happens.

A table whose schema file does not exist is skipped, which is how a bundle ends up
with only the tables its instrument actually has columns in.

Two helper functions build the substituted names:
:func:`opus_import.import_util.table_name_obs_mission` and
:func:`~opus_import.import_util.table_name_obs_instrument`. Both assert that the id
they are given is in the maps below, so a typo fails immediately rather than producing
a table nobody fills.

``VOLSETS_WITH_PREVIEWS``
~~~~~~~~~~~~~~~~~~~~~~~~~

The 21 volume sets that have browse products: the four Cassini ISS and CIRS sets, the
Cassini UVIS and VIMS sets, EBROCC, Galileo, the five Hubble sets, the two New
Horizons sets, and the four Voyager ISS sets. **Nothing reads it.**
:meth:`~opus_import.obs.obs_general.ObsGeneral.field_obs_general_preview_images` decides
whether an observation has previews by asking ``rms-pdsfile`` for a view set, not by
consulting this list.

The mission, host and instrument maps
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Six dictionaries relate an id to everything derived from it. Together they decide which
``obs_mission_*`` and ``obs_instrument_*`` tables exist, what those tables are called,
and how the user interface labels them.

.. list-table::
   :header-rows: 1
   :widths: 42 58

   * - Constant
     - What it maps
   * - ``MISSION_ID_TO_MISSION_TABLE_SFX``
     - Mission id to the suffix of its table. ``CO`` → ``cassini``, ``GB`` →
       ``earth``, ``GO`` → ``galileo``, ``HST`` → ``hubble``, ``NH`` →
       ``new_horizons``, ``VG`` → ``voyager``.
   * - ``MISSION_ID_TO_MISSION_NAME``
     - Mission id to its display name. ``GB`` is ``Ground-based``.
   * - ``INST_HOST_ID_TO_MISSION_ID``
     - Spacecraft id to mission id. The only many-to-one entries are ``VG1`` and
       ``VG2``, which both map to ``VG``.
   * - ``INST_HOST_ID_TO_INST_HOST_NAME``
     - Spacecraft id to display name, which is where ``Voyager 1`` and ``Voyager 2``
       are distinguished.
   * - ``INSTRUMENT_ID_TO_MISSION_ID``
     - Instrument id to mission id, 17 entries. **Membership here is what makes an
       instrument id legal**: :func:`~opus_import.import_util.table_name_obs_instrument`
       asserts it.
   * - ``INSTRUMENT_ID_TO_INSTRUMENT_NAME``
     - Instrument id to display name, 16 entries. Its comment says it holds the keys of
       the map above; it does not hold ``CORSS``, which has no
       ``obs_instrument_corss`` table -- everything Cassini RSS records that OPUS
       searches on is an ``obs_profile`` column. See
       :ref:`dev_guide_import_obs_cassini`.

Two consumers are worth knowing about.
:func:`~opus_import.steps.do_table_names.build_table_names_rows` loops the mission and
instrument maps to generate one ``table_names`` row per mission and instrument table
that exists, and :mod:`~opus_import.steps.do_partables` loops all three id maps to
generate the triggers. **Neither needs a hand-written row for a new mission or
instrument**; :ref:`dev_guide_extending_instrument` says what that means for adding
one.

.. _dev_guide_import_config_bundle_info:

opus_import.config_bundle_info
------------------------------

``BUNDLE_INFO`` is the registry that makes a bundle importable at all. It is a list of
``(regular expression, BundleInfo)`` pairs, read by
:func:`~opus_import.steps.do_import_tables.lookup_vol_info`, which returns the first
entry whose expression matches the **whole** bundle id.

A bundle id matching no entry is one OPUS does not know, and importing it is an error.

:class:`~opus_import.config_bundle_info.BundleInfo` is a :class:`~typing.TypedDict`
with five keys:

.. list-table::
   :header-rows: 1
   :widths: 26 74

   * - Key
     - Meaning
   * - ``pds_version``
     - ``3`` or ``4``. It decides which ``rms-pdsfile`` class is used and which
       PDS-version base the obs class derives from.
   * - ``primary_index``
     - A **tuple** of primary index file names, with ``<BUNDLE>`` standing for the
       bundle id, or None for a bundle OPUS does not import. A tuple because a bundle
       set may have several -- COCIRS_0xxx and COCIRS_1xxx have one index per cube
       geometry, and GO_0xxx has a separate Shoemaker-Levy 9 index. Not every entry
       uses the placeholder: COCIRS_5xxx and COCIRS_6xxx name ``OBSINDEX.LBL``
       outright, and the Cassini ISS F ring mosaics bundle names
       ``global_mosaic_index.tab``.
   * - ``validate_index_rows``
     - True to resolve an observation that has several index rows down to the one whose
       file specification survives a round trip through the OPUS id. See
       :ref:`dev_guide_import_one_index`.
   * - ``temporal_camera``
     - True when one observation can span enough time for a gridless geometry value to
       differ between its start and its end. It is passed onto the metadata and is
       what :meth:`~opus_import.obs.obs_ring_geometry.ObsRingGeometry.validate_ring_geo_fields`
       and
       :meth:`~opus_import.obs.obs_surface_geometry_target.ObsSurfaceGeometryTarget.validate_surface_geo_fields`
       consult before complaining that a minimum and a maximum disagree.
   * - ``instrument_class``
     - The :mod:`opus_import.obs` class that computes this bundle's rows, or None for a
       bundle OPUS knows about and deliberately ignores. **It is None exactly when
       ``primary_index`` is.**

Nothing in ``BUNDLE_INFO`` maps a bundle-id *prefix* to an instrument: the regular
expression selects the class directly.

The registry
~~~~~~~~~~~~

Twenty-nine entries: twenty-five PDS3 and four PDS4, of which four have no
``instrument_class`` and are the bundles OPUS deliberately ignores.

.. list-table::
   :header-rows: 1
   :widths: 30 8 30 16 16

   * - Bundle id pattern
     - PDS
     - Obs class
     - Validate rows
     - Temporal
   * - ``COCIRS_0[0123]\d\d|COCIRS_0401``
     - 3
     - *(ignored: early cruise volumes with no metadata)*
     - no
     - yes
   * - ``COCIRS_040[2-9]|COCIRS_041\d|COCIRS_0[5-9]\d\d|COCIRS_1\d\d\d``
     - 3
     - :class:`~opus_import.obs.obs_volume_cocirs_01xxx.ObsVolumeCOCIRS01xxx`
     - no
     - yes
   * - ``COCIRS_[56]\d\d\d``
     - 3
     - :class:`~opus_import.obs.obs_volume_cocirs_56xxx.ObsVolumeCOCIRS56xxx`
     - no
     - yes
   * - ``COISS_[12]\d\d\d``
     - 3
     - :class:`~opus_import.obs.obs_volume_coiss_12xxx.ObsVolumeCOISS12xxx`
     - no
     - no
   * - ``CORSS_8001``
     - 3
     - :class:`~opus_import.obs.obs_volume_corss_8xxx.ObsVolumeCORSS8xxx`
     - yes
     - yes
   * - ``COUVIS_0\d\d\d``
     - 3
     - :class:`~opus_import.obs.obs_volume_couvis_0xxx.ObsVolumeCOUVIS0xxx`
     - no
     - yes
   * - ``COUVIS_8001``
     - 3
     - :class:`~opus_import.obs.obs_volume_couvis_8xxx.ObsVolumeCOUVIS8xxx`
     - yes
     - yes
   * - ``COVIMS_0\d\d\d``
     - 3
     - :class:`~opus_import.obs.obs_volume_covims_0xxx.ObsVolumeCOVIMS0xxx`
     - no
     - yes
   * - ``COVIMS_8001``
     - 3
     - :class:`~opus_import.obs.obs_volume_covims_8xxx.ObsVolumeCOVIMS8xxx`
     - yes
     - yes
   * - ``EBROCC_0001``
     - 3
     - :class:`~opus_import.obs.obs_volume_ebrocc_xxxx.ObsVolumeEBROCCxxxx`
     - yes
     - yes
   * - ``GO_0001``
     - 3
     - *(ignored)*
     - no
     - no
   * - ``GO_000[2-9]|GO_001\d|GO_002\d``
     - 3
     - :class:`~opus_import.obs.obs_volume_go_0xxx.ObsVolumeGO0xxx`
     - yes
     - no
   * - ``HSTI\d_\d\d\d\d``
     - 3
     - :class:`~opus_import.obs.obs_volume_hstix_xxxx.ObsVolumeHSTIxxxxx`
     - no
     - no
   * - ``HSTJ\d_\d\d\d\d``
     - 3
     - :class:`~opus_import.obs.obs_volume_hstjx_xxxx.ObsVolumeHSTJxxxxx`
     - no
     - no
   * - ``HSTN\d_\d\d\d\d``
     - 3
     - :class:`~opus_import.obs.obs_volume_hstnx_xxxx.ObsVolumeHSTNxxxxx`
     - no
     - no
   * - ``HSTO\d_\d\d\d\d``
     - 3
     - :class:`~opus_import.obs.obs_volume_hstox_xxxx.ObsVolumeHSTOxxxxx`
     - no
     - no
   * - ``HSTU\d_\d\d\d\d``
     - 3
     - :class:`~opus_import.obs.obs_volume_hstux_xxxx.ObsVolumeHSTUxxxxx`
     - no
     - no
   * - ``NH..LO_1001``
     - 3
     - :class:`~opus_import.obs.obs_volume_nhxxlo_xxxx.ObsVolumeNHxxLOXxxx`
     - yes
     - no
   * - ``NH..MV_1001``
     - 3
     - :class:`~opus_import.obs.obs_volume_nhxxmv_xxxx.ObsVolumeNHxxMVXxxx`
     - yes
     - yes
   * - ``NH...._2\d\d\d``
     - 3
     - *(ignored: only the 1001 volumes are imported)*
     - no
     - no
   * - ``VGISS_[5678]\d\d\d``
     - 3
     - :class:`~opus_import.obs.obs_volume_vgiss_5678xxx.ObsVolumeVGISS5678xxx`
     - no
     - no
   * - ``VG_2801``
     - 3
     - :class:`~opus_import.obs.obs_volume_vg2801_vg2802.ObsVolumeVG2801VGPPS`
     - yes
     - yes
   * - ``VG_2802``
     - 3
     - :class:`~opus_import.obs.obs_volume_vg2801_vg2802.ObsVolumeVG2802VGUVS`
     - yes
     - yes
   * - ``VG_2803``
     - 3
     - :class:`~opus_import.obs.obs_volume_vg2803.ObsVolumeVG2803VGRSS`
     - yes
     - yes
   * - ``VG_2810``
     - 3
     - :class:`~opus_import.obs.obs_volume_vg2810.ObsVolumeVG2810VGISS`
     - yes
     - yes
   * - ``cassini_iss_fring_mosaics_rsfrench2025``
     - 4
     - :class:`~opus_import.obs.obs_bundle_cassini_iss_fring_mosaics_rsfrench2025.ObsBundleCassiniISSFRingMosaicsRSFrench2025`
     - no
     - yes
   * - ``cassini_uvis_solarocc_beckerjarmak2023``
     - 4
     - :class:`~opus_import.obs.obs_bundle_cassini_uvis_solarocc_beckerjarmak2023.ObsBundleCassiniUvisSolarOccBeckerJarmak`
     - no
     - yes
   * - ``uranus_occ_u.*``
     - 4
     - :class:`~opus_import.obs.obs_bundle_uranus_occs_earthbased.ObsBundleUranusOccsEarthbased`
     - yes
     - yes
   * - ``checksums_uranus_occs_earthbased|uranus_occ_support|superseded``
     - 4
     - *(ignored: part of the Uranus occultation bundle set, not observations)*
     - no
     - yes

Read the registry out of the module rather than out of this table when the two
disagree: the module is the specification. The mini-holdings fixture holds one bundle
per importable entry, minus the entries its own ``exclusions.tsv`` excuses by name, so a
newly registered type cannot go untested (see :ref:`dev_guide_import_fixture`).

.. _dev_guide_import_config_targets:

opus_import.config_targets
--------------------------

Four tables describing every target OPUS can name, in one module each and re-exported
from the package, so a consumer writes ``config_targets.TARGET_NAME_INFO`` without
knowing which module it lives in.

``TARGET_NAME_INFO`` (:mod:`opus_import.config_targets.target_name_info`)
    The master table: 445 entries mapping a canonical, upper-case target name to a
    three-element tuple.

    .. list-table::
       :header-rows: 1

       * - Element
         - Meaning
       * - 0
         - The planet the target is associated with: one of the keys of
           ``PLANET_GROUP_MAPPING``, or None for a target that belongs to no planet,
           which is what most entries are. ``MER`` is a legal value that no entry uses.
       * - 1
         - The target class: ``PLANET``, ``REG_SAT``, ``IRR_SAT``, ``RING``, ``SKY``,
           ``CALIBRATION`` or ``OTHER``. This is stored in ``obs_general.target_class``.
       * - 2
         - The name shown to the user.

    Two examples: ``'ENCELADUS': ('SAT', 'REG_SAT', 'Enceladus')`` and
    ``'ALF_LYR': (None, 'OTHER', 'Alp Lyr (Vega)')``.

    **A target class added here has to be added to the ``enum`` field and the
    ``mult_options`` of ``obs_general.json`` as well**, or the import rejects the value
    it stores. The module's own docstring says so, and it is the easiest thing to
    forget.

    A ``TARGET_NAME`` this table does not describe is reported through
    :meth:`~opus_import.context.ImportLog.unknown_target_name`, and the observation
    imports without a target -- unless ``--import-ignore-errors`` is given, under which
    it becomes ``OTHER``.

``TARGET_NAME_MAPPING`` (:mod:`opus_import.config_targets.target_name_mapping`)
    269 entries folding an instrument's own spelling onto a canonical name, so that
    observations of one body are searchable under one name whichever mission took them.
    It is applied first, before the lookup above:
    ``_get_target_info`` upper-cases the label's
    value, maps it through this table, and only then looks it up. The entries are
    grouped by the archive that needs them -- COCIRS, COISS, COUVIS, HST, GOSSI, New
    Horizons, a miscellaneous group, and a large block of star names. ``'VEGA'`` maps to
    ``'ALF_LYR'``; ``'S_RINGS'`` maps to ``'S RINGS'``; ``'2003UB313'`` maps to
    ``'ERIS'``.

``PLANET_GROUP_MAPPING`` (:mod:`opus_import.config_targets.planet_group_mapping`)
    Eleven entries mapping a planet id -- plus ``OTHER`` and None -- to the label and
    sort key the search form groups targets under.
    ``_get_planet_group_info`` reads it, and a
    target with no planet, or one the tables do not describe, is grouped under
    ``OTHER``.

``STAR_RA_DEC`` (:mod:`opus_import.config_targets.star_ra_dec`)
    190 entries mapping a star name to its ``(right ascension, declination)`` in
    degrees, J2000. It is checked in rather than fetched, so an import needs no network
    access. ``_prof_ra_dec_helper`` reads
    it to give an occultation's source star a position.

    :mod:`opus_import.util.retrieve_ra_dec` prints entries in this format; see
    :ref:`dev_guide_import_running` for the one rule about using its output.

.. _dev_guide_import_config_instruments:

opus_import.instruments
-----------------------

Two per-instrument hook tables, both keyed by a regular expression matched against a
label's file name, and **both empty**: every label OPUS imports is readable as it
stands. They are the place a per-instrument workaround goes when one is not, which is
why they survive with no entries.

:data:`~opus_import.instruments.PDSTABLE_REPLACEMENTS`
    File-name pattern and the value replacements to hand ``pdstable``. This is the one
    of the two that is actually consulted, by
    :func:`~opus_import.import_util.safe_pdstable_read_pds3`.

:data:`~opus_import.instruments.PDSTABLE_PREPROCESS`
    File-name pattern, a label-text preprocessor and a table callback. The loop that
    would read it is commented out, so **an entry added here has to be switched on as
    well as written.**

.. _dev_guide_import_config_file:

The configuration file
----------------------

Everything above is checked-in Python, the same on every installation. The other half of
"what exists" is the installation's TOML file, which says where the holdings are and
which database to write.

:mod:`opus_config` is the loader, and it is deliberately strict.
:func:`~opus_config.config.get_config` is the entry point; it reads the file
:func:`~opus_config.config.config_path` resolves from ``OPUS_CONFIG`` and **caches the
result for the life of the process**, so a test that loads a different configuration has
to clear that cache. The file becomes a tree of frozen dataclasses: an
:class:`~opus_config.config.OpusConfig` holding one per TOML table --
:class:`~opus_config.config.DatabaseConfig`, :class:`~opus_config.config.PathsConfig`,
:class:`~opus_config.config.DjangoConfig` and :class:`~opus_config.config.ImportConfig`,
the last spelled ``import_`` because ``import`` is a keyword. Nothing downstream can
mutate a setting, and every key is read through a typed accessor rather than by indexing
a dictionary.

Three properties are worth relying on:

* **An unknown key is an error**, not something ignored. So is a missing required key,
  and so is a value of the wrong type; each is reported as
  :exc:`~opus_config.config.ConfigError` naming the table and the key at fault.
* **A key with a default is optional and a key without one is required**, and the
  distinction is in the accessor call rather than in a separate list.
  :ref:`dev_guide_installation` tabulates every key and which it is.
* **The brand is validated against** :data:`~opus_config.config.DATABASE_BRANDS`, so a
  consumer receives a value already known to be one of the two.
  :mod:`opus_app.settings` dispatches on it blind, through a two-entry map;
  :func:`opus_import.importdb.get_db` re-checks anyway and raises for anything it does
  not implement.

:ref:`dev_guide_support` describes the package alongside :mod:`opus_support`, and
:ref:`dev_guide_installation` describes writing a file.

API reference
-------------

:doc:`api_opus_import`
