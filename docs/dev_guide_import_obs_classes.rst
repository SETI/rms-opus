.. _dev_guide_import_obs_classes:

The Obs Classes, Mission by Mission
===================================

Above the table modules of :ref:`dev_guide_import_obs` sit two more layers: **one class
per mission**, for what an instrument's archives share, and **one class per volume set
or bundle**, the leaf, which knows how one particular archive spells things. There are
37 of them, and this chapter names every one.

Twelve are shared classes that no ``BUNDLE_INFO`` entry names directly; twenty-five are
leaves, and each is the ``instrument_class`` of exactly one registry entry. A leaf
class's file is named ``obs_volume_*`` for a PDS3 volume set and ``obs_bundle_*`` for a
PDS4 bundle.

.. mermaid::

    classDiagram
        class ObsBase {
            <<abstract>>
        }
        class ObsCommonPDS3 {
            <<abstract>>
            the nine PDS3 table modules
        }
        class ObsCommonPDS4 {
            <<abstract>>
            the nine PDS4 table modules
        }
        class ObsCassiniCommon {
            <<abstract>>
            observation name, mission phase, filters
        }
        class ObsCassiniCommonPDS3 { <<abstract>> }
        class ObsCassiniCommonPDS4 { <<abstract>> }
        class ObsVolumeCassiniOccCommon { <<abstract>> }
        class ObsVolumeUVISVIMSOccCommon { <<abstract>> }
        class ObsBundleOccCommon { <<abstract>> }
        class ObsVolumeGalileoCommon { <<abstract>> }
        class ObsVolumeHubbleCommon { <<abstract>> }
        class ObsVolumeNewHorizonsCommon { <<abstract>> }
        class ObsVolumeVoyagerCommon { <<abstract>> }
        class ObsVolumeVG28xx { <<abstract>> }
        class ObsVolumeVG28xxVGPPSUVS { <<abstract>> }
        class ObsVolumeCOISS12xxx { COISS_1xxx, COISS_2xxx }
        class ObsVolumeCOCIRS01xxx { COCIRS_0xxx, COCIRS_1xxx }
        class ObsVolumeCOCIRS56xxx { COCIRS_5xxx, COCIRS_6xxx }
        class ObsVolumeCOUVIS0xxx { COUVIS_0xxx }
        class ObsVolumeCOVIMS0xxx { COVIMS_0xxx }
        class ObsVolumeCORSS8xxx { CORSS_8001 }
        class ObsVolumeCOUVIS8xxx { COUVIS_8001 }
        class ObsVolumeCOVIMS8xxx { COVIMS_8001 }
        class ObsVolumeGO0xxx { GO_0xxx }
        class ObsVolumeHSTIxxxxx { HSTIx, WFC3 }
        class ObsVolumeHSTJxxxxx { HSTJx, ACS }
        class ObsVolumeHSTNxxxxx { HSTNx, NICMOS }
        class ObsVolumeHSTOxxxxx { HSTOx, STIS }
        class ObsVolumeHSTUxxxxx { HSTUx, WFPC2 }
        class ObsVolumeNHxxLOXxxx { NHxxLO, LORRI }
        class ObsVolumeNHxxMVXxxx { NHxxMV, MVIC }
        class ObsVolumeVGISS5678xxx { VGISS_5xxx..8xxx }
        class ObsVolumeVG2801VGPPS { VG_2801 }
        class ObsVolumeVG2802VGUVS { VG_2802 }
        class ObsVolumeVG2803VGRSS { VG_2803 }
        class ObsVolumeVG2810VGISS { VG_2810 }
        class ObsVolumeEBROCCxxxx { EBROCC_0001 }
        class ObsBundleCassiniISSFRingMosaicsRSFrench2025 { F ring mosaics }
        class ObsBundleCassiniUvisSolarOccBeckerJarmak { UVIS solar occ }
        class ObsBundleUranusOccsEarthbased { uranus_occ_u* }

        ObsBase <|-- ObsCassiniCommon
        ObsCommonPDS3 <|-- ObsCassiniCommonPDS3
        ObsCassiniCommon <|-- ObsCassiniCommonPDS3
        ObsCommonPDS4 <|-- ObsCassiniCommonPDS4
        ObsCassiniCommon <|-- ObsCassiniCommonPDS4
        ObsCassiniCommonPDS3 <|-- ObsVolumeCOISS12xxx
        ObsCassiniCommonPDS3 <|-- ObsVolumeCOCIRS01xxx
        ObsCassiniCommonPDS3 <|-- ObsVolumeCOCIRS56xxx
        ObsCassiniCommonPDS3 <|-- ObsVolumeCOUVIS0xxx
        ObsCassiniCommonPDS3 <|-- ObsVolumeCOVIMS0xxx
        ObsCassiniCommonPDS3 <|-- ObsVolumeCassiniOccCommon
        ObsVolumeCassiniOccCommon <|-- ObsVolumeCORSS8xxx
        ObsVolumeCassiniOccCommon <|-- ObsVolumeUVISVIMSOccCommon
        ObsVolumeUVISVIMSOccCommon <|-- ObsVolumeCOUVIS8xxx
        ObsVolumeUVISVIMSOccCommon <|-- ObsVolumeCOVIMS8xxx
        ObsCassiniCommonPDS4 <|-- ObsBundleCassiniISSFRingMosaicsRSFrench2025
        ObsCommonPDS4 <|-- ObsBundleOccCommon
        ObsBundleOccCommon <|-- ObsBundleCassiniUvisSolarOccBeckerJarmak
        ObsCassiniCommonPDS4 <|-- ObsBundleCassiniUvisSolarOccBeckerJarmak
        ObsBundleOccCommon <|-- ObsBundleUranusOccsEarthbased
        ObsCommonPDS3 <|-- ObsVolumeGalileoCommon
        ObsVolumeGalileoCommon <|-- ObsVolumeGO0xxx
        ObsCommonPDS3 <|-- ObsVolumeHubbleCommon
        ObsVolumeHubbleCommon <|-- ObsVolumeHSTIxxxxx
        ObsVolumeHubbleCommon <|-- ObsVolumeHSTJxxxxx
        ObsVolumeHubbleCommon <|-- ObsVolumeHSTNxxxxx
        ObsVolumeHubbleCommon <|-- ObsVolumeHSTOxxxxx
        ObsVolumeHubbleCommon <|-- ObsVolumeHSTUxxxxx
        ObsCommonPDS3 <|-- ObsVolumeNewHorizonsCommon
        ObsVolumeNewHorizonsCommon <|-- ObsVolumeNHxxLOXxxx
        ObsVolumeNewHorizonsCommon <|-- ObsVolumeNHxxMVXxxx
        ObsCommonPDS3 <|-- ObsVolumeVoyagerCommon
        ObsVolumeVoyagerCommon <|-- ObsVolumeVGISS5678xxx
        ObsVolumeVoyagerCommon <|-- ObsVolumeVG28xx
        ObsVolumeVG28xx <|-- ObsVolumeVG28xxVGPPSUVS
        ObsVolumeVG28xxVGPPSUVS <|-- ObsVolumeVG2801VGPPS
        ObsVolumeVG28xxVGPPSUVS <|-- ObsVolumeVG2802VGUVS
        ObsVolumeVG28xx <|-- ObsVolumeVG2803VGRSS
        ObsVolumeVG28xx <|-- ObsVolumeVG2810VGISS
        ObsCommonPDS3 <|-- ObsVolumeEBROCCxxxx

Three naming traps, worth knowing before you go looking for a file:

* Two class names **drop or reorder** what their module names carry:
  :class:`~opus_import.obs.obs_volume_couvis_covims_occ_common.ObsVolumeUVISVIMSOccCommon`,
  and
  :class:`~opus_import.obs.obs_bundle_cassini_uvis_solarocc_beckerjarmak2023.ObsBundleCassiniUvisSolarOccBeckerJarmak`,
  which drops the year its module carries. Several VG_28xx classes *add* an instrument
  suffix their modules lack, which is the next trap rather than this one.
* ``obs_volume_vg28xx.py`` holds
  :class:`~opus_import.obs.obs_volume_vg28xx.ObsVolumeVG28xx`, but the VG_2801 and
  VG_2802 classes and their shared parent
  :class:`~opus_import.obs.obs_volume_vg2801_vg2802.ObsVolumeVG28xxVGPPSUVS` live in
  ``obs_volume_vg2801_vg2802.py``. That is the only file defining more than one class.
* A leaf named ``xxxx`` does not always cover a whole set:
  :class:`~opus_import.obs.obs_volume_ebrocc_xxxx.ObsVolumeEBROCCxxxx` matches only
  ``EBROCC_0001``, and the three ``8xxx`` Cassini occultation classes match only their
  single ``8001`` volume.

.. _dev_guide_import_obs_cassini:

Cassini
-------

Fifteen classes -- more than any other mission, because Cassini contributes four
imaging and spectroscopy instruments plus three ring-occultation volume sets and two
PDS4 bundles. Five of them are shared and ten are leaves.

Shared: ObsCassiniCommon
~~~~~~~~~~~~~~~~~~~~~~~~

:class:`opus_import.obs.obs_cassini_common.ObsCassiniCommon`

What every Cassini instrument shares, and the largest of the mission classes. It is
where four pieces of Cassini knowledge live:

* **The observation name grammar.** A Cassini observation name is
  ``<PRIME>_<REVNO><TARGETCODE>_<ACTIVITYNAME><ACTIVITYNUMBER>_<INST>``, with a
  three-part VIMS variant. Parsing it gives the revolution number, the prime instrument,
  the target code and the activity name, each of which becomes an
  ``obs_mission_cassini`` column. A 57-entry table maps the two-letter target codes onto
  display names.
* **The mission phase, derived from the time rather than read from the label**, because
  the labels do not agree on how a phase is spelled or on when one ends. A table of
  nineteen phase/interval triples is walked, short encounters first so that they win.
* **The planet, and which side of the rings is lit.** Both are decided against fixed
  instants -- the planet by comparing the observation's **stop** time against Jupiter and
  Saturn arrival, and the lit ring face by comparing its **start** time against Saturn's
  2009 equinox.
* **The Cassini ISS filter table** -- 107 ``(camera, filter1, filter2)`` entries giving
  a central wavelength, a full width at half maximum and an effective wavelength in
  nanometers, from the ISS Data User's Guide and the CISSCAL calibration tables --
  together with the helper that falls back to CLEAR for an unknown polarizer combination
  and the one that joins two filter wheels into a combined name with the polarizer
  second.

It also declares the whole ``obs_instrument_coiss`` column set as None-returning stubs,
so that each PDS-version half can fill them from its own label vocabulary.

Shared: ObsCassiniCommonPDS3
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:class:`opus_import.obs.obs_cassini_common_pds3.ObsCassiniCommonPDS3`

What every Cassini instrument's PDS3 volumes share. Two things distinguish it:

* **Reconciling the target.** ``TARGET_NAME``, ``TARGET_DESC`` and the observation
  name's target code do not always agree, and three numbered rules plus a fallthrough
  decide between them -- chiefly that a SATURN or SKY target with a ring target code, or
  with a description mentioning rings, is really ``S RINGS``.
* **Repairing spacecraft clock counts.** Three per-instrument fixes: CIRS omits the
  fractional part, and VIMS and UVIS write fractional parts that are not clock ticks.
  The latter two cite the filed issue they answer.

It fills the ``obs_instrument_coiss`` columns from the PDS3 label keywords, normalizing
the order of the observation-type words and reporting a change in length as an error.

Shared: ObsCassiniCommonPDS4
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:class:`opus_import.obs.obs_cassini_common_pds4.ObsCassiniCommonPDS4`

The same for PDS4, reading the ``cassini:`` namespace instead of PDS3 keywords. Unlike
the PDS3 half it implements the two spacecraft clock columns itself, including the
out-of-order correction, and those two strip the label value's surrounding whitespace
before parsing it.

Leaf: ObsVolumeCOISS12xxx
~~~~~~~~~~~~~~~~~~~~~~~~~

:class:`opus_import.obs.obs_volume_coiss_12xxx.ObsVolumeCOISS12xxx`

**COISS_1xxx and COISS_2xxx** -- Cassini ISS images of Jupiter and of Saturn.

* Pixel size comes from a three-entry table keyed on the instrument mode (``FULL``,
  ``SUM2``, ``SUM4``).
* Wavelengths are the central wavelength plus or minus half the full width, from the
  mission class's filter table.
* Exposure duration is converted from milliseconds.
* Right ascension and declination fall back from the ring geometry summary to the
  primary index, for cruise data that has no ring geometry.
* The spacecraft clock is assembled from a partition and a count and cross-checked
  against ``IMAGE_NUMBER``, warning on a mismatch.
* A combined filter containing ``P`` makes the polarization type linear; a filter
  beginning ``UV`` makes the quantity emission.
* ``.LBL`` converts to ``.IMG``.

Leaf: ObsVolumeCOCIRS01xxx
~~~~~~~~~~~~~~~~~~~~~~~~~~

:class:`opus_import.obs.obs_volume_cocirs_01xxx.ObsVolumeCOCIRS01xxx`

**COCIRS_0402 to 0419, COCIRS_0500 onward, and COCIRS_1xxx** -- Cassini CIRS cubes.
(The registry's pattern leaves COCIRS_0420 to 0499 matching nothing at all, so a volume
in that range would be reported as one OPUS does not know.) The most unusual leaf in the
set:

* **Three primary index files**, one per cube geometry (equirectangular, point, ring).
* **The map projection is read from the last letter of ``PRODUCT_ID``**, and it switches
  nearly every geometry method between the ring-geometry and the surface-geometry column
  families.
* **The surface geometry is inline**, in the index rather than in per-target summary
  files, so this class overrides
  :meth:`~opus_import.obs.obs_base.ObsBase.surface_geo_target_list`.
* Several geometry values come from ``CSS:``-prefixed columns, including a ring
  longitude measured east from the ascending node and a local time converted to a solar
  hour angle.
* Wavelengths are converted from wavenumbers in the supplemental index.
* ``.LBL`` converts to ``.tar.gz``.

The earlier COCIRS_0xxx volumes -- 0000 to 0399 and 0401 -- are registered with no obs
class at all: they are cruise volumes with no metadata.

Leaf: ObsVolumeCOCIRS56xxx
~~~~~~~~~~~~~~~~~~~~~~~~~~

:class:`opus_import.obs.obs_volume_cocirs_56xxx.ObsVolumeCOCIRS56xxx`

**COCIRS_5xxx and COCIRS_6xxx** -- Cassini CIRS spectra. Its primary index is
``OBSINDEX.LBL``, one of the two registry entries that name a fixed file rather than one
derived from the bundle id -- the other being the Cassini ISS F ring mosaics bundle.

* The primary file specification comes from ``SPECTRUM_FILE_SPECIFICATION`` rather than
  from the index's own file column, and may be None.
* The observation type is a spectral time series rather than a cube.
* Wavenumbers are read directly from the primary index.
* A badly formatted spacecraft clock is a **warning** here rather than an error -- the
  one place that overrides the log function ``_parse_sclk`` uses.
* It fills the six CIRS instrument-mode flag columns that COCIRS_0xxx and COCIRS_1xxx
  leave None.

Leaf: ObsVolumeCOUVIS0xxx
~~~~~~~~~~~~~~~~~~~~~~~~~

:class:`opus_import.obs.obs_volume_couvis_0xxx.ObsVolumeCOUVIS0xxx`

**COUVIS_0xxx** -- Cassini UVIS. One volume set holding four instruments: two
spectrographs (EUV and FUV), a high-speed photometer (HSP) and a hydrogen-deuterium
absorption cell (HDAC), **distinguished by the file name** rather than by a label
keyword. The channel decides the observation type, the wavelength range, the spectral
size and whether the observation counts as an image at all.

* HSP integration durations are in milliseconds while the others are in seconds.
* The HSP stop times in the archive are wrong, so ``time2`` is recomputed as the start
  plus the number of samples times the integration duration.
* There is no stop-count clock column, so the second one is derived from the first plus
  the duration.
* The primary file specification is the ``FILE_NAME`` column, already volume-relative.
* ``.LBL`` converts to ``.DAT``.

Leaf: ObsVolumeCOVIMS0xxx
~~~~~~~~~~~~~~~~~~~~~~~~~

:class:`opus_import.obs.obs_volume_covims_0xxx.ObsVolumeCOVIMS0xxx`

**COVIMS_0xxx** -- Cassini VIMS cubes. This is the class that makes *phases* exist: one
index row describes both an infrared and a visible observation, so it overrides
:attr:`~opus_import.obs.obs_base.ObsBase.phase_names` to return one or both, and
overrides :attr:`~opus_import.obs.obs_base.ObsBase.opus_id` to append ``_ir`` or
``_vis``.

Each channel carries its own fixed wavelength range, resolution, spectral size and image
type. An occultation instrument mode switches the quantity to optical depth and the type
to a time series. The spacecraft clock is given the partition VIMS omits. The file
specification is built from separate path and file columns, and ``.lbl`` converts to
``.qub`` in lower case.

Shared: ObsVolumeCassiniOccCommon
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:class:`opus_import.obs.obs_volume_cassini_occ_common.ObsVolumeCassiniOccCommon`

What the three Cassini ring-occultation volumes share. The target is hardcoded to
``S RINGS`` -- that is what a ring occultation is of, by construction -- the planet is
Saturn, the quantity is optical depth and the type is occultation. The occultation
direction is read out of the **file name** (``_I_`` or ``_E_``), because these are
always split into separate ingress and egress files. Ring geometry comes from the
primary index's radius, resolution, longitude and azimuth columns, the phase angle is
pinned at 180 degrees, and the two optical depth columns come from the supplemental
index. ``.LBL`` converts to ``.TAB``.

Shared: ObsVolumeUVISVIMSOccCommon
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:class:`opus_import.obs.obs_volume_couvis_covims_occ_common.ObsVolumeUVISVIMSOccCommon`

What the UVIS and VIMS ring-occultation volumes share, and what distinguishes them from
the radio one: these are **stellar** occultations. The source is a star, so right
ascension and declination come from
``STAR_RA_DEC`` (:mod:`opus_import.config_targets.star_ra_dec`); times come from the
supplemental index; and the whole family of ring elevation, incidence and emission
columns is derived arithmetically from the single ``OBSERVED_RING_ELEVATION`` column.

Leaf: ObsVolumeCORSS8xxx
~~~~~~~~~~~~~~~~~~~~~~~~

:class:`opus_import.obs.obs_volume_corss_8xxx.ObsVolumeCORSS8xxx`

**CORSS_8001** -- Cassini radio science ring occultations. A **radio** occultation, so
the source is the spacecraft's own signal and the host is a Deep Space Network station:
a ten-entry table maps a DSN station number onto its PDS4 instrument id. The start time
is the spacecraft event time but the stop time is the Earth-received time; the
wavelength is converted from centimeters; and the ``K`` band is renamed ``KA``.

There is **no** ``obs_instrument_corss`` **table**: everything Cassini RSS records that
OPUS searches on is an ``obs_profile`` column, which is why ``CORSS`` appears in
``INSTRUMENT_ID_TO_MISSION_ID`` and not in ``INSTRUMENT_ID_TO_INSTRUMENT_NAME``.

Leaf: ObsVolumeCOUVIS8xxx
~~~~~~~~~~~~~~~~~~~~~~~~~

:class:`opus_import.obs.obs_volume_couvis_8xxx.ObsVolumeCOUVIS8xxx`

**COUVIS_8001** -- Cassini UVIS stellar ring occultations. Wavelengths converted from
nanometers, temporal sampling from the supplemental integration duration in
milliseconds, the wavelength band fixed at UV, the channel fixed at HSP, and every
COUVIS band, line and sample column None.

Leaf: ObsVolumeCOVIMS8xxx
~~~~~~~~~~~~~~~~~~~~~~~~~

:class:`opus_import.obs.obs_volume_covims_8xxx.ObsVolumeCOVIMS8xxx`

**COVIMS_8001** -- Cassini VIMS stellar ring occultations. Temporal sampling from the
infrared exposure; the wavelength band fixed at IR; and a spacecraft clock quirk of its
own, since this volume's clock fractions are in units where the fractional part can
exceed 255, so they are truncated. Every ``obs_instrument_covims`` column comes from the
supplemental index rather than the primary one; the three visible-channel columns are
constants, because this volume has no visible channel.

Leaf: ObsBundleCassiniISSFRingMosaicsRSFrench2025
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:class:`opus_import.obs.obs_bundle_cassini_iss_fring_mosaics_rsfrench2025.ObsBundleCassiniISSFRingMosaicsRSFrench2025`

**cassini_iss_fring_mosaics_rsfrench2025** -- PDS4 mosaics of Saturn's F ring built from
Cassini ISS images. A derived product rather than a raw observation, and it shows:

* The observation type is a mosaic, with fixed pixel dimensions and no intensity levels.
* Longitudinal resolutions are converted from degrees to a linear distance using the F
  ring's circumference.
* A ten-code note vocabulary is decoded from a semicolon-separated ``notes`` column into
  prose, and an unknown code is an error.
* The camera is the last character of the minimum image name.
* It overrides
  :meth:`~opus_import.obs.obs_base.ObsBase.primary_filespec_from_index_row` to use the
  index's own ``file_spec`` column.

Leaf: ObsBundleCassiniUvisSolarOccBeckerJarmak
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:class:`opus_import.obs.obs_bundle_cassini_uvis_solarocc_beckerjarmak2023.ObsBundleCassiniUvisSolarOccBeckerJarmak`

**cassini_uvis_solarocc_beckerjarmak2023** -- Cassini UVIS **solar** occultations of
Saturn's rings, in PDS4. One of three classes with two bases, combining the PDS4
occultation machinery with the Cassini mission knowledge.

The occultation type is solar and the source is the Sun. Right ascension and declination
are deliberately left None, because the Sun is an extended source that moves relative to
the spacecraft. Incidence and emission are flipped by 180 degrees for observations before
Saturn's equinox. Several UVIS instrument columns are pinned, because every observation
in the bundle uses the same configuration.

Galileo
-------

Shared: ObsVolumeGalileoCommon
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:class:`opus_import.obs.obs_volume_galileo_common.ObsVolumeGalileoCommon`

The smallest mission class: the Galileo spacecraft clock parser and the two
``obs_mission_galileo`` id columns. Everything else -- the orbit number and the two clock
counts -- raises.

Leaf: ObsVolumeGO0xxx
~~~~~~~~~~~~~~~~~~~~~

:class:`opus_import.obs.obs_volume_go_0xxx.ObsVolumeGO0xxx`

**GO_0002 through GO_0029** -- Galileo SSI images. (``GO_0001`` is registered and
deliberately ignored.)

* **The index gives one pointing rather than a range**, so the right-ascension range is
  the camera's own field of view about it, widened by the diagonal half-width and
  corrected for the declination.
* An eight-filter wavelength table, with bandwidths read off a published figure.
* **Shoemaker-Levy 9.** GO_0016's SL9 observations share a file specification, so a
  second primary index supplies their per-observation minimum and maximum image times
  and ids; the time columns try those first and fall back to the supplemental index, and
  the image id becomes a range.
* Pixel size comes from the supplemental cut-out window, defaulting to 800.
* Eight-bit intensity levels.

Hubble
------

Shared: ObsVolumeHubbleCommon
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:class:`opus_import.obs.obs_volume_hubble_common.ObsVolumeHubbleCommon`

What every HST instrument shares: splitting the ``+``-joined filter name into its two
wheels (more than two is an error), classifying an observation as an image or a
spectrum, deciding the planet from ``PLANET_NAME``, and calling the quantity *emission*
when at least three quarters of the passband is below 350 nm and its high end is below
400 nm. It swaps a reversed wavelength pair with a warning, and it fills the whole
``obs_mission_hubble`` column family -- proposal id, principal investigator, detector,
publication date, target name, guidance lock type, filter and aperture -- with the
detector prefixed by the instrument, and the filter and aperture both prefixed and
grouped by it.

Two members raise: the observation type, and the filter type.

**There are no HST instrument tables.** Every Hubble column lives in the mission table,
which is why the trigger and category rows for an ``HST``-prefixed instrument point at
``obs_mission_hubble`` and are not displayed separately.

The five leaves
~~~~~~~~~~~~~~~

All five derive directly from the shared class and differ chiefly in how they decide
"spectroscopic" and how they classify a filter.

.. list-table::
   :header-rows: 1
   :widths: 26 14 12 48

   * - Class
     - Volumes
     - Instrument
     - What distinguishes it
   * - :class:`~opus_import.obs.obs_volume_hstix_xxxx.ObsVolumeHSTIxxxxx`
     - ``HSTIx_xxxx``
     - WFC3
     - Spectroscopic when the filter is a grism. WFC3 has **one** filter wheel, so a
       second filter is an error. Spectral size is computed from published resolving
       powers per grism and clamped to the larger image dimension; an unrecognized grism
       raises.
   * - :class:`~opus_import.obs.obs_volume_hstjx_xxxx.ObsVolumeHSTJxxxxx`
     - ``HSTJx_xxxx``
     - ACS
     - Spectroscopic for a grism **or** a prism. Filter types come from explicit
       published lists. A ``POL`` filter in the second wheel makes the polarization
       linear. One grism warns that its resolving power depends on the channel and the
       order, and computes a spectral size from an assumed one anyway.
   * - :class:`~opus_import.obs.obs_volume_hstnx_xxxx.ObsVolumeHSTNxxxxx`
     - ``HSTNx_xxxx``
     - NICMOS
     - Spectroscopic when the filter is a grism. Polarizer suffixes map onto wide and
       medium; the blank position is opaque. Spectral size is the larger image
       dimension, deliberately generous because the dispersion direction is unknown.
   * - :class:`~opus_import.obs.obs_volume_hstox_xxxx.ObsVolumeHSTOxxxxx`
     - ``HSTOx_xxxx``
     - STIS
     - **The only one that reads the distinction directly**, from
       ``OBSERVATION_TYPE``. Also the only one that overrides the shared wavelength
       resolutions, and the only one filling the proposed aperture type and the optical
       element.
   * - :class:`~opus_import.obs.obs_volume_hstux_xxxx.ObsVolumeHSTUxxxxx`
     - ``HSTUx_xxxx``
     - WFPC2
     - **Never spectroscopic.** Twelve-bit levels, where the other four are sixteen. The
       only one that combines both filter wheels when classifying, taking the type of
       the narrower bandpass; and the only one filling the four chip flags and the
       targeted detector.

New Horizons
------------

Shared: ObsVolumeNewHorizonsCommon
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:class:`opus_import.obs.obs_volume_new_horizons_common.ObsVolumeNewHorizonsCommon`

The New Horizons spacecraft clock format, the two clock counts assembled from the
supplemental partition and count columns with an out-of-order warning, a seven-entry
mission-phase name table (which carries both spellings of one phase), the planet derived
from that phase, and the note column.

New Horizons is the one mission whose bundleset expansion is reordered.
:func:`~opus_import.import_util.yield_import_bundle_ids` reverses a New Horizons
bundleset's whole listing, so that a bundleset's calibrated ``2xxx`` bundle is yielded
before its raw ``1001`` one and the raw bundle is left holding the primary file
specification ``rms-pdsfile`` reports.

Two things follow. The reversal applies to the **whole** listing, not to each pair, so it
also reverses the relative order of the ``_1001`` bundles inside a bundleset -- and row
ids depend on that order. And it fires only when a bundleset is expanded: every ``NH``
shorthand instead names an explicit, hand-ordered list of ``_1001`` bundles, because that
order matters for its own reason, which the source records against a filed issue.

Leaf: ObsVolumeNHxxLOXxxx
~~~~~~~~~~~~~~~~~~~~~~~~~

:class:`opus_import.obs.obs_volume_nhxxlo_xxxx.ObsVolumeNHxxLOXxxx`

**NHxxLO_1001** -- New Horizons LORRI. OPUS identifies an observation by its engineering
FITS file, so the file-specification conversion makes four substitutions at once:
``.lbl``/``.LBL`` to ``.fit``/``.FIT``, ``_sci`` to ``_eng``, and ``_2001`` to
``_1001``. Fixed 1024 by 1024 frames, twelve-bit levels, a fixed wavelength range, and a
compression type and a binning mode.

Leaf: ObsVolumeNHxxMVXxxx
~~~~~~~~~~~~~~~~~~~~~~~~~

:class:`opus_import.obs.obs_volume_nhxxmv_xxxx.ObsVolumeNHxxMVXxxx`

**NHxxMV_1001** -- New Horizons MVIC, identified the same way. Push-broom rather than
framing, so the image type differs and the frame is 5024 by 128; a different wavelength
range; the camera comes from the file name; and there is no binning mode. It is
registered with ``temporal_camera`` set, where LORRI is not.

Voyager
-------

Shared: ObsVolumeVoyagerCommon
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:class:`opus_import.obs.obs_volume_voyager_common.ObsVolumeVoyagerCommon`

The one mission where **the spacecraft is read per observation rather than fixed per
volume**: the instrument host id is derived from the last character of
``INSTRUMENT_HOST_NAME``, asserted to be Voyager 1 or Voyager 2. It supplies the Voyager
clock parser, the two clock counts with an optional partition prefix, the Earth-received
time, and the planet derived from the first three letters of the mission phase. The
mission phase itself raises, because it is recorded in a different place in each volume
set.

Leaf: ObsVolumeVGISS5678xxx
~~~~~~~~~~~~~~~~~~~~~~~~~~~

:class:`opus_import.obs.obs_volume_vgiss_5678xxx.ObsVolumeVGISS5678xxx`

**VGISS_5xxx through VGISS_8xxx** -- Voyager ISS images of the four outer planets. The
only Voyager volume set whose primary index is not the plain one: it uses
``<BUNDLE>_raw_image_index.lbl``.

A nine-filter wavelength table including the two methane filters; the mission phase read
from the index column; usable line and sample counts computed from the supplemental
window columns and also exposed as their own columns; a negative exposure duration
returned as None (one observation in the archive has one); the UV filter making the
quantity emission; and ``.LBL`` converting to ``.IMG``.

Shared: ObsVolumeVG28xx
~~~~~~~~~~~~~~~~~~~~~~~

:class:`opus_import.obs.obs_volume_vg28xx.ObsVolumeVG28xx`

What every Voyager ring-profile volume shares. These four volumes hold **radial ring
profiles reconstructed from the observations**, not the original observations, and it
shows in every column: wavelengths, radial resolutions, ring radii and ring-intercept
times all come from the supplemental index, and the mission phase is derived from the
target name because the volumes record no phase of their own.

It also exports the list of instants at which Voyager crossed each ring plane, which the
subclasses use to check which side of the rings they were on.

Shared: ObsVolumeVG28xxVGPPSUVS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:class:`opus_import.obs.obs_volume_vg2801_vg2802.ObsVolumeVG28xxVGPPSUVS`

What VG_2801 and VG_2802 share. These carry no geometry summary, so **which face of the
rings the signal source was on is decided from the star and the planet** and then
checked against the observation's start time, logging a disagreement.

There are **two** such conventions, and the class supplies both: one for the elevation
columns and one for the north-based and opening-angle columns. The reason is Uranus --
its pole is tipped past the ecliptic, so an observation of its rings is north-facing by
the ring plane's own reckoning and south-facing by the convention the other columns use.

Incidence angles are computed from the emission angles and cross-checked against the
label's own incidence, erroring when they differ by more than a small tolerance.

Leaves: ObsVolumeVG2801VGPPS and ObsVolumeVG2802VGUVS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:class:`opus_import.obs.obs_volume_vg2801_vg2802.ObsVolumeVG2801VGPPS`, :class:`opus_import.obs.obs_volume_vg2801_vg2802.ObsVolumeVG2802VGUVS`

**VG_2801** and **VG_2802** -- Voyager PPS and UVS radial ring profiles. Each supplies
exactly one thing: its instrument id. Everything else is the shared class above. They
are the two smallest leaves in the hierarchy, and they are the reason that class exists.

Leaf: ObsVolumeVG2803VGRSS
~~~~~~~~~~~~~~~~~~~~~~~~~~

:class:`opus_import.obs.obs_volume_vg2803.ObsVolumeVG2803VGRSS`

**VG_2803** -- Voyager radio science radial ring profiles. A radio rather than a stellar
occultation, with its own two-entry DSN station table keyed off the receiver host name.
Its Uranus special case is much narrower than VG_2801's: it flips only the *solar* ring
elevation. North-based incidence is taken straight from the emission angle, because the
south side is lit.

Leaf: ObsVolumeVG2810VGISS
~~~~~~~~~~~~~~~~~~~~~~~~~~

:class:`opus_import.obs.obs_volume_vg2810.ObsVolumeVG2810VGISS`

**VG_2810** -- Voyager ISS radial ring profiles, reconstructed from the images. The only
VG_28xx leaf that is **reflectance rather than occultation**: the quantity, the
observation type and the profile type all say so, and there is no source. The Sun lit the
north side while Voyager observed from the south, so the north-based angles equal the
plain ones. It is also the only one with real phase-angle columns, and it fills the
``obs_instrument_vgiss`` table with placeholder values.

Ground-based
------------

Leaf: ObsVolumeEBROCCxxxx
~~~~~~~~~~~~~~~~~~~~~~~~~

:class:`opus_import.obs.obs_volume_ebrocc_xxxx.ObsVolumeEBROCCxxxx`

**EBROCC_0001** -- ground-based stellar occultations of Saturn's rings from 1989. It
derives straight from :class:`~opus_import.obs.obs_common_pds3.ObsCommonPDS3`; there is
no ground-based mission class.

**Six telescopes contributed**, so the instrument is per observation rather than per
volume: a six-entry table maps the host and instrument ids onto a PDS4 instrument id.
The whole event's geometry is fixed and recorded in the source, because every
observation was of one star on one date. Right ascension, declination and the source
name come from the **index label** rather than from a row, which no other class does.

Shared: ObsBundleOccCommon
~~~~~~~~~~~~~~~~~~~~~~~~~~

:class:`opus_import.obs.obs_bundle_occ_common.ObsBundleOccCommon`

What every PDS4 occultation bundle shares. The primary file specification is the index
row's ``filepath`` column, already relative to the holdings root -- no bundle prefix,
unlike every PDS3 class. Wavelengths are converted from nanometers, and the whole ring
geometry family is derived from the ``rings:`` namespace and from the single light-source
incidence angle. Ring intercept times are taken as barycentric dynamical time with no
conversion.

Leaf: ObsBundleUranusOccsEarthbased
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:class:`opus_import.obs.obs_bundle_uranus_occs_earthbased.ObsBundleUranusOccsEarthbased`

**uranus_occ_u\*** -- Earth-based stellar occultations of Uranus and its rings, in PDS4.
Three primary index files per bundle: rings, global and atmosphere.

* **The index files are not archived with the bundle.** The module's own docstring
  carries the shell recipe that generates them; read it before trying to import one of
  these bundles for the first time.
* A 22-entry table maps a fragment of the PDS4 logical identifier onto a PDS4 instrument
  id, covering many ground telescopes plus one Hubble observation. The instrument, host
  and mission ids are therefore all **per observation**.
* Whether the observation is atmospheric is decided from the logical identifier, and it
  switches the target between Uranus and the rings.
* Earth saw Uranus's south pole for the whole data set, so the star lit the north side
  of the rings and the north-based angles equal the plain ones.
* Many ring-specific columns are absent from the atmosphere labels and come out None.

The bundle set also contains checksum, support and superseded bundles, which are
registered as deliberately ignored.

Where to go next
----------------

:ref:`dev_guide_import_extending` is the recipe for adding a class to any of these
families.

API reference
-------------

:doc:`api_opus_import`
