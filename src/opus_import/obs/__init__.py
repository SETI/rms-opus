"""The ``obs_*`` class hierarchy that computes one database row per observation.

`opus_import.steps.do_import_index` instantiates the leaf class
`opus_import.config_bundle_info` names for the bundle it is importing, and
`opus_import.steps.do_import_obs.import_run_field_function` then calls that instance's
``field_obs_<table>_<column>`` method once per column of each table the bundle fills.
Everything else here exists to decide which method that call lands on.

Import the classes from their own modules (``from opus_import.obs.obs_base import
ObsBase``); this module deliberately re-exports nothing, because importing every leaf
class here would import every mission's parsing code no matter which bundle is running.

Five kinds of module
--------------------

* **The root**, `opus_import.obs.obs_base`, which holds the metadata, the helpers that
  read a value out of a PDS index, and `opus_import.obs.obs_base.ObsBase._create_mult`.
* **The PDS-version split**, `opus_import.obs.obs_base_pds3` and
  `opus_import.obs.obs_base_pds4`, which answer the questions only a PDS version can:
  where a file specification comes from, and what the time columns are called.
* **One module per OPUS table** -- general, pds, profile, wavelength, type_image, ring
  geometry, and the three surface geometry modules -- each holding that table's field
  methods, some of them with a ``_pds3``/``_pds4`` variant of its own. Two assembly
  classes, `opus_import.obs.obs_common_pds3.ObsCommonPDS3` and
  `opus_import.obs.obs_common_pds4.ObsCommonPDS4`, combine all of them so that a mission
  class names one base instead of nine.
* **One module per mission** -- Cassini, Galileo, Hubble, New Horizons, Voyager -- for
  what an instrument's volumes share: a spacecraft clock format, an observation-name
  grammar, a mission phase.
* **One module per bundle or volume set**, the leaf, which knows how that particular
  archive spells things.

How a method is chosen
----------------------

A leaf class's method resolution order runs leaf, then the mission's PDS-version half,
then the assembly class, then the table modules in the order that class lists them, and
finally the mission's PDS-version-independent half and the root. So a bundle module
overrides everything, and a mission's PDS-version half overrides the table modules --
but its PDS-version-independent half does not, because that one sits *below* them.
Reading a Cassini ISS volume's order out of the tree gives:

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

Two consequences are worth knowing before adding a class. The PDS-version base lands in
the *middle* of the table modules rather than after them: some of them derive from it,
and it is placed as soon as the last of those has been. So a default defined in
`opus_import.obs.obs_base_pds3` is overridden by every table module the assembly class
lists up to and including the last one deriving from it -- which is not the same set as
the ones that derive from it -- and overrides every table module listed after that. Read
the split off the tree rather than from a list here; the assembly class's base order is
what decides it. And a mission's PDS-version-independent half sits below every table
module, so a default it defines is overridden by any table module that defines the same
name.

Adding a bundle
---------------

A new bundle needs a leaf class deriving from its mission's class (or from an assembly
class where the mission has none), an entry in `opus_import.config_bundle_info`, and a
field method for every column of every table the bundle fills that it does not inherit.
``tests/opus_import/test_obs_field_annotations.py`` is what says whether the last of
those is complete, and what each method's declared return type has to be.
"""
