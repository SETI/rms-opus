.. _dev_guide_extending:

Extending OPUS
==============

Four things get added often enough to have a recipe: a metadata column, a bundle, an
instrument or mission, and a unit. A fifth -- a log-analyzer configuration for a
different site -- is covered in :ref:`dev_guide_log_analyzer`.

Every one of them ends the same way: run an import against real holdings and check the
error log. Nothing else exercises the code that reads a PDS label.

Adding a metadata column
------------------------

1. **Add the column to the table's schema** in
   ``src/opus_import/table_schemas/<table>.json``, at the position it should occupy.
   :ref:`dev_guide_table_schemas` describes every key. At a minimum it needs
   ``field_name``, ``field_type`` and ``data_source``; to be searchable it also needs
   the ``pi_*`` keys, and ``pi_category_name`` is the one whose presence makes it a
   field at all.
2. **Write the field method** on whichever class in the obs hierarchy knows the
   answer -- the table module if every mission computes it the same way, a mission
   module if a mission differs, a bundle module if only one archive does. It is named
   ``field_obs_<table>_<column>``, where ``<table>`` is the schema file's name without
   ``obs_`` and ``<column>`` is ``field_name``.
3. **Give it the return type its column implies.** The aliases are in
   :mod:`opus_import.obs.field_types`, and
   ``tests/opus_import/test_obs_field_annotations.py`` is what checks that every
   method's annotation matches its schema column. That test is the authority on what
   a method has to return, not any list written down here.
4. **Add a definition** if the field is user-visible: ``pi_dict_context`` and
   ``pi_dict_name`` name the data-dictionary term whose text becomes the tooltip, and
   ``definition`` carries the text itself.
5. **Import a bundle and look at the error log.** A column with no ``param_info`` row
   is invisible; a column whose field method returns the wrong shape is reported by
   ``--validate-perm`` through the error log rather than through an exit status.

Adding a bundle
---------------

A bundle whose instrument OPUS already imports needs a leaf class and an entry saying
which one to use:

1. **Add an entry to** ``BUNDLE_INFO`` **in**
   :mod:`opus_import.config_bundle_info`. Each entry pairs a regular expression
   matching the bundle id with the details of importing it: the obs class that
   computes its rows, the PDS version, the primary index file, and the flags saying
   whether index rows need validating and whether the observation spans time. A
   bundle id that matches no entry is one OPUS does not know; an entry whose
   ``instrument_class`` is None names one OPUS knows and deliberately ignores.
2. **Add the leaf class**, in ``src/opus_import/obs/obs_volume_<name>.py`` for a PDS3
   volume set or ``obs_bundle_<name>.py`` for a PDS4 bundle set, deriving from its
   mission's class -- or from an assembly class if the mission has none. Read
   :mod:`opus_import.obs` first: the method resolution order decides which of the
   classes above the leaf actually answers a call, and it is not the order the class
   list suggests.
3. **Override only what differs.** Everything the mission and the table modules
   already answer correctly should be left alone.
4. **Run the import.**

Adding an instrument or a mission
---------------------------------

This is the bundle recipe plus the configuration data that says the instrument exists:

1. **Edit** :mod:`opus_import.config_data`: add the mission to
   ``MISSION_ID_TO_MISSION_NAME`` and ``MISSION_ID_TO_MISSION_TABLE_SFX``, its
   spacecraft to ``INST_HOST_ID_TO_MISSION_ID`` and
   ``INST_HOST_ID_TO_INST_HOST_NAME``, and the instrument to
   ``INSTRUMENT_ID_TO_MISSION_ID`` and ``INSTRUMENT_ID_TO_INSTRUMENT_NAME``. If the
   new tables are of a kind ``TABLES_TO_POPULATE`` does not already cover, add them
   there too; the mission, instrument and surface-geometry entries in that list carry
   placeholders that are substituted per bundle, so an ordinary new mission or
   instrument needs no change to it.
2. **Add the table schemas** the new mission and instrument tables need -- one JSON
   file per table, named after the table.
3. **Usually nothing to do in** :mod:`opus_import.steps.do_table_names`.
   ``build_table_names_rows`` already loops the mission and instrument maps you edited
   in step 1 and emits a row for every one of those tables that exists, so adding one
   by hand would give the table a **second** row and a second display position. A row
   has to be written there only for a table of a *new kind* -- neither a mission nor an
   instrument table, as ``obs_wavelength`` is -- because those are written out
   individually. A table of a new kind with no row has no "Constraints" section and
   its fields are invisible.
4. **Add any label parsing** the instrument needs to
   :mod:`opus_import.instruments`.
5. **Add the mission class**, naming its file the way the existing mission modules
   are named -- read those off ``opus_import/obs/`` rather than from here, because
   they do not all follow one spelling and not every entry in the mission map has a
   module at all. Add its ``_pds3``/``_pds4`` halves if the mission has both, then the
   leaf classes for its bundles as above.
6. **Regenerate the Django models**: ``scripts/models/create_opus_models.sh`` rewrites
   ``src/opus_app/apps/search/models.py`` from a populated database. New tables do not
   exist to the web application until it has been run.

A class skeleton
~~~~~~~~~~~~~~~~

The skeleton below is a **starting point, not a specification**: it lists the
overrides an instrument class usually supplies, grouped by the class each comes from.
What a class actually has to supply is decided by the schemas of the tables its
bundles fill, and ``tests/opus_import/test_obs_field_annotations.py`` is what says
whether the set is complete and what each method must return.

.. code-block:: python

    # INST and MISSION are placeholders, carried over from the template this
    # skeleton replaced. A real class is named for its bundle or volume set -- see
    # the file names in opus_import/obs/ -- rather than for the instrument alone.
    class ObsInstrumentINST(ObsMissionMISSION):
        """One-line description of the instrument this class imports."""

        # --- Mandatory, from ObsBase ------------------------------------------
        @property
        def instrument_id(self) -> str | None: ...

        @property
        def inst_host_id(self) -> str: ...

        @property
        def mission_id(self) -> str: ...

        @property
        def primary_filespec(self) -> str | None:
            # This must be computable from the PRIMARY index alone, never from a
            # supplemental one: it is what finds the matching supplemental row, and
            # it is what the OPUS ID is derived from.
            ...

        # --- Mandatory, from ObsGeneral ---------------------------------------
        def field_obs_general_planet_id(self) -> MultFieldRet: ...
        def field_obs_general_quantity(self) -> MultFieldRet: ...
        def field_obs_general_observation_type(self) -> MultFieldRet: ...

        # --- Optional, from ObsGeneral: override where the mission's answer is
        #     wrong for this instrument -----------------------------------------
        def field_obs_general_target_name(self) -> MultFieldRet: ...
        def field_obs_general_time1(self) -> FloatField: ...
        def field_obs_general_time2(self) -> FloatField: ...
        def field_obs_general_observation_duration(self) -> FloatField: ...
        def field_obs_general_right_asc1(self) -> FloatField: ...
        def field_obs_general_right_asc2(self) -> FloatField: ...
        def field_obs_general_declination1(self) -> FloatField: ...
        def field_obs_general_declination2(self) -> FloatField: ...

        # --- Then one method per column of every other table the bundle fills:
        #     obs_pds, obs_type_image, obs_wavelength, obs_profile, the geometry
        #     tables, the mission table, and this instrument's own table. -------

Adding a unit
-------------

Units live in :mod:`opus_support.units`, in ``UNIT_FORMAT_DB``: a unit id maps to its
units, each unit's conversion factor to the id's default unit, and the functions that
parse and format a value in it.

1. **Add the unit** to the unit id's ``conversions``, in the order it should be
   offered to the user. **Order does not decide the default**: each unit id carries an
   explicit ``'default'`` key naming the unit its values are stored in, and
   :func:`opus_support.units.get_default_unit` returns that. The two happen to agree
   for every unit id today, which is exactly why inserting a new unit at the front
   will not change the default and will not look like it failed.
2. **Add tests.** :mod:`opus_support` carries a standing demand for 100% coverage, and
   a unit needs its parse and its format tested in both directions, including the
   values it rejects.
3. **Reference it from a schema** by putting the unit id after the ``:`` in a column's
   ``pi_form_type``. The import validates that the id exists, so a typo fails the
   import rather than reaching a user.

A field's available units are what the :ref:`API guide's field table
<availablefields>` lists, and that table is generated from the schemas, so a new unit
appears there as soon as a column names it.
