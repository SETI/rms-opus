.. _dev_guide_import_extending:

Extending the Import Pipeline
=============================

Five things get added to the import pipeline often enough to have a recipe: a metadata
column, a bundle, an instrument or a mission, a unit, and a database brand. The web
application's extension points are in :ref:`dev_guide_webapp_extending`, and a
log-analyzer configuration for a different site is in :ref:`dev_guide_log_analyzer`.

**Every one of these ends the same way: run an import and read the error log.** Nothing
else exercises the code that reads a PDS label. :ref:`dev_guide_import_running` says how,
and :ref:`dev_guide_import_fixture` is what covers the pipeline without holdings.

.. _dev_guide_extending_column:

Adding a metadata column
------------------------

1. **Add the column to the table's schema** in
   ``src/opus_import/table_schemas/<table>.json``, at the position it should occupy.
   :ref:`dev_guide_table_schemas` describes every key. At a minimum it needs
   ``field_name``, ``field_type`` and ``data_source``; to be searchable it also needs
   the ``pi_*`` keys, and ``pi_category_name`` is the one whose presence makes it a
   field at all.
2. **Write the field method** on whichever class in the obs hierarchy knows the answer
   -- the table module if every mission computes it the same way, a mission module if a
   mission differs, a bundle module if only one archive does.
   :ref:`dev_guide_import_obs_mro` is what decides which of those actually answers the
   call. The method is named ``field_obs_<table>_<column>``, where ``<table>`` is the
   schema file's name without the ``obs_`` and ``<column>`` is ``field_name``;
   :func:`~opus_import.steps.do_import_obs.field_function_name` is the rule, and a name
   it cannot produce is a method that is never called.
3. **Give it the return type its column implies.** The aliases are in
   :mod:`opus_import.obs.field_types`, and
   ``tests/opus_import/test_obs_field_annotations.py`` is what checks that every
   method's annotation matches its schema column. **That test is the authority on what a
   method has to return**, not any list written down here. Remember that the *form type*
   decides, not the storage type: a flag column returns a
   :class:`~opus_import.obs.field_types.MultField`, not a bool.
4. **Add a definition** if the field is user-visible: ``pi_dict_context`` and
   ``pi_dict_name`` name the data-dictionary term whose text becomes the tooltip, and
   ``definition`` carries the text itself. See :ref:`dev_guide_dictionary`.
5. **Import a bundle and look at the error log.** A column with no ``param_info`` row is
   invisible; a column whose field method returns the wrong shape is reported by
   ``--validate-perm`` through the error log rather than through an exit status.

.. code-block:: python

    # In the class that knows the answer -- a table module, a mission module, or a
    # bundle module. The return type is decided by the schema column, and checked by
    # tests/opus_import/test_obs_field_annotations.py.
    def field_obs_instrument_coiss_my_new_column(self) -> StrField:
        return self._some_index_col('MY_NEW_LABEL_KEYWORD')

.. _dev_guide_extending_bundle:

Adding a bundle
---------------

A bundle whose instrument OPUS already imports needs a leaf class and a registry entry
saying which one to use.

1. **Add an entry to** ``BUNDLE_INFO`` **in**
   :mod:`opus_import.config_bundle_info`. :ref:`dev_guide_import_config_bundle_info`
   describes all five keys. Put it where its regular expression will not be shadowed by
   an earlier, broader one: :func:`~opus_import.steps.do_import_tables.lookup_vol_info`
   takes the **first** match.
2. **Add the leaf class**, in ``src/opus_import/obs/obs_volume_<name>.py`` for a PDS3
   volume set or ``obs_bundle_<name>.py`` for a PDS4 bundle set, deriving from its
   mission's class -- or from an assembly class if the mission has none, as
   :class:`~opus_import.obs.obs_volume_ebrocc_xxxx.ObsVolumeEBROCCxxxx` does. Read
   :ref:`dev_guide_import_obs_mro` first.
3. **Override only what differs.** Everything the mission and the table modules already
   answer correctly should be left alone. :ref:`dev_guide_import_obs_classes` is a
   catalogue of what each existing leaf found it had to override, which is the quickest
   guide to what a new one is likely to need.
4. **Run the import.**

.. code-block:: python

    """The obs class for MYVOL_xxxx.

    One sentence saying what instrument and what mission this volume set holds.
    """

    from __future__ import annotations

    from opus_import.obs.field_types import FloatField, MultFieldRet, StrField
    from opus_import.obs.obs_volume_mymission_common import ObsVolumeMyMissionCommon


    class ObsVolumeMYVOLxxxx(ObsVolumeMyMissionCommon):
        """The observations of MYVOL_xxxx.

        Its ``field_obs_*`` methods each fill the schema column their name ends in.
        """

        # --- The contract ObsBase declares --------------------------------------
        @property
        def instrument_id(self) -> str | None:
            return 'MYINST'

        @property
        def inst_host_id(self) -> str:
            return 'MY'

        @property
        def mission_id(self) -> str:
            return 'MY'

        @property
        def primary_filespec(self) -> str | None:
            # This must be computable from the PRIMARY index alone, never from a
            # supplemental one: it is what finds the matching supplemental row, and
            # it is what the OPUS ID is derived from.
            return self._index_col('FILE_SPECIFICATION_NAME')

        # --- What ObsGeneral requires -------------------------------------------
        def field_obs_general_planet_id(self) -> MultFieldRet: ...

        def field_obs_general_quantity(self) -> MultFieldRet: ...

        def field_obs_general_observation_type(self) -> MultFieldRet: ...

        # --- Then one method per column of every other table this bundle fills
        #     that the mission and table modules do not already answer correctly.
        def field_obs_wavelength_wavelength1(self) -> FloatField: ...

        def field_obs_pds_product_id(self) -> StrField: ...

The skeleton is a **starting point, not a specification**. What a class actually has to
supply is decided by the schemas of the tables its bundles fill, and
``tests/opus_import/test_obs_field_annotations.py`` is what says whether the set is
complete and what each method must return.

.. _dev_guide_extending_instrument:

Adding an instrument or a mission
---------------------------------

This is the bundle recipe plus the configuration data that says the instrument exists.

1. **Edit** :mod:`opus_import.config_data`. Add the mission to
   ``MISSION_ID_TO_MISSION_NAME`` and ``MISSION_ID_TO_MISSION_TABLE_SFX``, its
   spacecraft to ``INST_HOST_ID_TO_MISSION_ID`` and ``INST_HOST_ID_TO_INST_HOST_NAME``,
   and the instrument to ``INSTRUMENT_ID_TO_MISSION_ID`` and
   ``INSTRUMENT_ID_TO_INSTRUMENT_NAME``. If the new tables are of a kind
   ``TABLES_TO_POPULATE`` does not already cover, add them there too -- but an ordinary
   new mission or instrument needs no change to that list, because its mission,
   instrument and surface-geometry entries carry placeholders that are substituted per
   bundle.
2. **Add the table schemas** the new mission and instrument tables need -- one JSON file
   per table, named after the table. A table with no schema file is silently skipped, so
   a missing file looks like a table nobody fills rather than an error.
3. **Usually nothing to do in** :mod:`opus_import.steps.do_table_names` **or**
   :mod:`opus_import.steps.do_partables`. Both generate their rows by looping the maps
   you edited in step 1, so adding one by hand would give the table a **second** row and
   a second display position. A row has to be written in
   :func:`~opus_import.steps.do_table_names.build_table_names_rows` only for a table of a
   *new kind* -- neither a mission nor an instrument table, as ``obs_wavelength`` is --
   because those are written out individually. A table of a new kind with no row has no
   "Constraints" section and its fields are invisible.
4. **Add any target names the instrument uses.** A ``TARGET_NAME`` that
   ``TARGET_NAME_INFO`` does not describe is an error per observation. Add the target
   there, or -- if it is a spelling of a body OPUS already knows -- add the fold to
   ``TARGET_NAME_MAPPING``. Adding a new *target class* means adding it to the ``enum``
   field and the ``mult_options`` of ``obs_general.json`` as well, or the import rejects
   the value it stores.
5. **Add any label parsing** the instrument needs to :mod:`opus_import.instruments` --
   and remember that only ``PDSTABLE_REPLACEMENTS`` is consulted; an entry added to
   ``PDSTABLE_PREPROCESS`` has to be switched on as well as written.
6. **Add the mission class**, naming its file the way the existing mission modules are
   named -- read those off ``src/opus_import/obs/`` rather than from here, because they
   do not all follow one spelling and not every entry in the mission map has a module at
   all. Add its ``_pds3``/``_pds4`` halves if the mission has both, then the leaf classes
   for its bundles as above.
7. **Regenerate the Django models**: ``scripts/models/create_opus_models.sh`` rewrites
   ``src/opus_app/apps/search/models.py`` from a populated database. New tables do not
   exist to the web application until it has been run, and the script refuses to run
   while any ``cache_*`` table is present. See :ref:`dev_guide_webapp_search`.

.. _dev_guide_extending_target:

Adding a surface geometry target
--------------------------------

There is nothing to do. The ``obs_surface_geometry__<TARGET>`` tables are created from
one template as the targets are discovered, their ``table_names`` rows and their
``partables`` triggers are generated from the tables that exist, and their search
parameters are named by the slug form of the target name.
:ref:`dev_guide_import_obs_target_template` describes the mechanism.

The one thing that is **not** automatic: adding the target to ``TARGET_NAME_INFO`` if it
is not already there, since an unknown name never reaches the surface geometry code at
all.

.. _dev_guide_extending_unit:

Adding a unit
-------------

Units live in :mod:`opus_support.units`, in ``UNIT_FORMAT_DB``: a unit id maps to its
units, each unit's conversion factor to the id's default unit, and the functions that
parse and format a value in it.

1. **Add the unit** to the unit id's ``conversions``, in the order it should be offered
   to the user. **Order does not decide the default**: each unit id carries an explicit
   ``'default'`` key naming the unit its values are stored in, and
   :func:`opus_support.units.get_default_unit` returns that. The two happen to agree for
   every unit id today, which is exactly why inserting a new unit at the front will not
   change the default and will not look like it failed.
2. **Add tests.** :mod:`opus_support` carries a standing demand for 100% coverage, and a
   unit needs its parse and its format tested in both directions, including the values
   it rejects.
3. **Reference it from a schema** by putting the unit id after the ``:`` in a column's
   ``pi_form_type``. :mod:`opus_import.steps.do_param_info` validates that the id
   exists, so a typo fails the import rather than reaching a user.

A field's available units are what the :ref:`API guide's field table <availablefields>`
lists, and that table is generated from the schemas, so a new unit appears there as soon
as a column names it. The web application reads the same functions -- see
:ref:`dev_guide_webapp_search` for where units are parsed out of a query string.

.. _dev_guide_extending_brand:

Adding a database brand
-----------------------

The pipeline's database layer is written against an abstraction with room for a second
brand, and :mod:`opus_import.importdb.postgresql` is the stub kept so that adding one is
a matter of filling it in.

1. **Implement the sixteen abstract members** of
   :class:`~opus_import.importdb.super.ImportDBSuper`, listed in
   :ref:`dev_guide_import_db_importdb`. Two of their contracts are not optional:
   ``table_names`` must return its names **sorted**, or two imports of identical
   holdings will disagree about every row id; and every identifier must be validated
   before it is quoted, because quoting alone does not escape the quote character.
2. **Add the branch** to :func:`opus_import.importdb.get_db`.
3. **Add the engine** to the ``_db_engines`` map in :mod:`opus_app.settings`, so that
   the web application follows the same configured brand. The placeholder is already
   there.
4. **Check the schema translation.** ``create_table`` and ``table_info`` are a matched
   pair: the first turns a schema's ``field_type`` into the brand's SQL type and the
   second turns it back. :ref:`dev_guide_table_schemas` lists the types a schema may
   name, and an unrecognized one must raise rather than be guessed at.

Nothing else in the pipeline names a brand, so there is no third place to change.

Where to go next
----------------

:ref:`dev_guide_table_schemas`
    Every key a schema column may carry.

:ref:`dev_guide_import_obs`
    The contracts a new obs class has to meet.

:ref:`dev_guide_import_fixture`
    How to cover a new bundle type without holdings -- and why a newly registered type
    fails the suite until you do.

API reference
-------------

:doc:`api_opus_import`, :doc:`api_opus_support`
