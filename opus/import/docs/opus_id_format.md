# OPUS ID Format

This document describes the format for OPUS IDs. OPUS IDs are character strings
that unique identify a collection of products in OPUS. A single OPUS ID
corresponds to a single thumbnail for previewing and is the smallest quanta of
data available for searching or displaying of metadata.

OPUS IDs should be short and concise as much as possible without losing
readability and generality. It is expected that OPUS IDs will remain constant
for eternity, thus allowing "permanent links" to OPUS product collections to
remain valid. As such, it is strongly discouraged to change OPUS IDs after they
are deployed for public use.

In general, OPUS IDs follow the format:

`<mission>-<instrument>-<observation_details>`

We first describe the valid `mission` names. Because the `observation_details`
are formatted in a unique way for each instrument, we then describe the
`instrument` and `observation_details` together. Note that a single
`mission`/`instrument` combination may have multiple types of observations, each
with its own `observation_details` format. For example, Cassini UVIS takes both
images and occultations.

## Mission Names

OPUS IDs begin with a prefix that contains the mission name abbreviation. Valid
mission names for space-based observatories are:

| Mission Name    | Abbrev |
|-----------------|--------|
| Cassini Orbiter | co     |
| Galileo Orbiter | go     |
| Voyager         | vg     |
| Hubble          | hst    |
| New Horizons    | nh     |

Ground-based telescopes use an abbreviation of the site name and the telescope size, as long as there is no ambiguity. Possible telescopes are taken from the [PDS4 master list](https://pds.nasa.gov/data/pds4/context-pds4/telescope/).

| PDS4 Telescope Name                   | OPUS ID Abbrev |
|---------------------------------------|----------------|
| `amos.aeos`                           | `amosaeos` |
| `amos.geodss`                         | `amosgeodss` |
| `amos.msss1m2`                        | `amos1m2` |
| `apache_point.arc3m5`                 | `ap3m5` |
| `apache_point.sdss2m5`                | `ap2m5` |
| `arecibo.305m`                        | `arecibo305m` |
| `asiago.copernico1m82`                | `asi1m82` |
| `bopps.sto`                           | `bopps` |
| `caha-calar_alto.1m23`                | `caha1m23` |
| `canberra.dss33_34m`                  | `dss33_34m` |
| `canberra.dss34_34m`                  | `dss34_34m` |
| `canberra.dss35_34m`                  | `dss35_34m` |
| `canberra.dss36_34m`                  | `dss36_34m` |
| `canberra.dss42_26m`                  | `dss42_26m` |
| `canberra.dss42_34m`                  | `dss42_34m` |
| `canberra.dss43_64m`                  | `dss43_64m` |
| `canberra.dss43_70m`                  | `dss43_70m` |
| `canberra.dss45_34m`                  | `dss45_34m` |
| `canberra.dss46_26m`                  | `dss46_26m` |
| `carbuncle_hill.0m35`                 | `car0m35` |
| `chuguev.azt8_0m70`                   | `chu0m7` |
| `chuguevskaya.0m7`                    | `chu0m7` |
| `ctio-cerro_tololo.2mass_1m3`         | `ctio1m3` |
| `ctio-cerro_tololo.smarts_1m0`        | `ctio1m0` |
| `ctio-cerro_tololo.smarts_1m50`       | `ctio1m50` |
| `ctio-cerro_tololo.soar_4m1`          | `ctio4m1` |
| `ctio-cerro_tololo.victorblanco_4m0`  | `ctio4m0` |
| `dushanbe.rcc`                        | `dusrcc` |
| `el_leoncito.js2m15`                  | `elleon2m15` |
| `ensenada.1m5`                        | `ens1m5` |
| `ensenada.2m12`                       | `ens2m12` |
| `eso-chajnantor.alma`                 | `esochaalma` |
| `eso-la_silla.1m04`                   | `esosil1m04` |
| `eso-la_silla.1m52`                   | `esosil1m52` |
| `eso-la_silla.2m2`                    | `esosil2m2` |
| `eso-la_silla.3m6`                    | `esosil3m6` |
| `eso-la_silla.ntt`                    | `esosilntt` |
| `eso-paranal.vlt_antu_8m2_ut1`        | `esopar8m2ut1` |
| `eso-paranal.vlt_kueyen_8m2_ut2`      | `esopar8m2ut2` |
| `eso-paranal.vlt_melipal_8m2_ut3`     | `esopar8m2ut3` |
| `eso-paranal.vlt_yepun_8m2_ut4`       | `esopar8m2ut4` |
| `flwo.2mass1m3`                       | `flwo1m3` |
| `fremonte_peak.fpo0m32`               | `fre0m32` |
| `gbo.gbt_100m`                        | `gbo100m` |
| `gemini-south.8m1`                    | `gems8m1` |
| `gemini_north-maunakea.8m1`           | `gemn8m1` |
| `goldstone.dss11_26m`                 | `dss11_26m` |
| `goldstone.dss12_26m`                 | `dss12_26m` |
| `goldstone.dss12_34m`                 | `dss12_34m` |
| `goldstone.dss13_26m`                 | `dss13_26m` |
| `goldstone.dss13_34m`                 | `dss13_34m` |
| `goldstone.dss14_64m`                 | `dss14_64m` |
| `goldstone.dss14_70m`                 | `dss14_70m` |
| `goldstone.dss15_34m`                 | `dss15_34m` |
| `goldstone.dss16_26m`                 | `dss16_26m` |
| `goldstone.dss23_34m`                 | `dss23_34m` |
| `goldstone.dss24_34m`                 | `dss24_34m` |
| `goldstone.dss25_34m`                 | `dss25_34m` |
| `goldstone.dss26_34m`                 | `dss26_34m` |
| `goldstone.dss27_34m`                 | `dss27_34m` |
| `goldstone.dss28_34m`                 | `dss28_34m` |
| `goodricke-pigott.orion_astroview`    | `goodorion` |
| `haute-provence.1m20`                 | `hp1m20` |
| `hunters_hill.sct0m36`                | `hh0m36` |
| `irtf-maunakea.3m2`                   | `irtf3m2` |
| `jac.ukirt3m8`                        | `jac3m8` |
| `keck.10m_keck1`                      | `keck1_10m` |
| `keck.10m_keck2`                      | `keck2_10m` |
| `kpno-mcmath-pierce-solar.main_1m61`  | `kpno1m61` |
| `kpno.boller1m3`                      | `kpno1m3` |
| `kpno.corning2m13`                    | `kpno2m13` |
| `kpno.mayall4m`                       | `kpnp4m` |
| `kuiper-airborne.0m91`                | `kao0m91` |
| `las_campanas.ireneedupont_2m5`       | `lascam2m5` |
| `las_campanas.magellan_baade_6m5`     | `lascam6m5` |
| `las_campanas.magellan_clay_6m5`      | `lascam6m5` |
| `las_campanas.swope_1m0`              | `lascam1m0` |
| `las_cumbres.0m4_telescopes`          | `lascum0m4` |
| `las_cumbres.1m0_telescopes`          | `lascum1m0` |
| `las_cumbres.2m0_telescopes`          | `lascum2m0` |
| `leura.0m25`                          | `leu0m25` |
| `lick.shane3m05`                      | `lick3m05` |
| `lowell.21in0`                        | `low21in` |
| `lowell.discovery_4m3`                | `llow4m3` |
| `lowell.hall_ritchey-chretien_1_1m07` | `low1m07` |
| `lowell.loneos_0m60`                  | `low0m60` |
| `lowell.nuro_0m79`                    | `low0m79` |
| `lowell.perkins_warner1m83`           | `low1m83` |
| `madrid.dss53_34m`                    | `dss53_34m` |
| `madrid.dss54_34m`                    | `dss54_34m` |
| `madrid.dss55_34m`                    | `dss55_34m` |
| `madrid.dss56_34m`                    | `dss56_34m` |
| `madrid.dss61_26m`                    | `dss61_26m` |
| `madrid.dss61_34m`                    | `dss61_34m` |
| `madrid.dss63_64m`                    | `dss63_64m` |
| `madrid.dss63_70m`                    | `dss63_70m` |
| `madrid.dss65_34m-post2005`           | `dss65_34m` |
| `madrid.dss65_34m`                    | `dss65_34m` |
| `madrid.dss66_26m`                    | `dss66_26m` |
| `magdalena_ridge.mro2m4`              | `mag2m4` |
| `maunakea.0m61`                       | `mk0m61` |
| `maunakea.2m24`                       | `mk2m24` |
| `maunakea.ukirt_3m8`                  | `mk3m8` |
| `mcdonald.0m91`                       | `mcd0m91` |
| `mcdonald.harlanjsmith_2m7`           | `mcd2m7` |
| `mcdonald.struve2m1`                  | `mcd2m1` |
| `mdm.hiltner2m4`                      | `mdm2m4` |
| `mdm.tinsley1m3`                      | `mdm1m3` |
| `mmt.single_mirror6m5`                | `mmt6m5` |
| `modra.0m6`                           | `mod0m6` |
| `mount_bigelow.0m7`                   | `mtbig0m7` |
| `mount_bigelow.1m54`                  | `mtbig1m54` |
| `mount_canopus.1m0`                   | `mtcan1m0` |
| `mount_lemmon.1m02`                   | `mtlem1m02` |
| `mount_lemmon.1m54`                   | `mtlem1m54` |
| `mount_stromlo.1m9`                   | `mtstr1m9` |
| `mount_stromlo.eos`                   | `mtstreos` |
| `naoj-hawaii.subaru_8m2`              | `naoj8m2` |
| `nofs.usno1m55`                       | `nofs1m55` |
| `ondrejov.0m65`                       | `ond0m65` |
| `orm.galileo_zeiss3m5`                | `orm3m5` |
| `orm.gtc10m4`                         | `orm10m4` |
| `orm.int2m54`                         | `orm2m54` |
| `palmer_divide.0m5`                   | `palm0m5` |
| `palmer_divide.old10inch`             | `palm10in` |
| `palomar.1m52`                        | `pal1m52` |
| `palomar.hale_5m08`                   | `pal5m08` |
| `palomar.oschin_schmidt_1m2`          | `pal1m2` |
| `partizanskoye.1m25_azt11`            | `par1m25` |
| `paul_wild.dss47_2008`                | `dss47` |
| `pic_du_midi.1m06`                    | `pic1m06` |
| `pic_du_midi.bernardlyot_2m0`         | `pic2m0` |
| `saao.radcliffe_1m88`                 | `saao1m88` |
| `siding_spring.aat_3m9`               | `sso3m9` |
| `siding_spring.anu_2m3`               | `sso2m3` |
| `siding_spring.uppsala0m5`            | `sso0m5` |
| `simeis.grubb1m`                      | `simgrub` |
| `smt.heinrich_hertz10m`               | `smt10m` |
| `star_castle.black_springs0m8`        | `sc0m8` |
| `steward-kittpeak.bok2m3`             | `skp2m3` |
| `steward-kittpeak.spacewatch_0m9`     | `skp0m9` |
| `steward-kittpeak.spacewatch_1m8`     | `skp1m8` |
| `stockport.jubilee`                   | `stojub` |
| `table_mountain.astro_mechanics0m61`  | `tm0m61` |
| `teide.carlossanchez_1m55`            | `tei1m55` |
| `u_alabama.fecker0m25`                | `ual0m25` |
| `uwo_meteor_radar.cmor`               | `uwocmor` |
| `valle_d'aosta.oavda`                 | `vdaoavda` |

The `EBROCC_0001` volume refers to telescopes that are not available in the
above list. We map them, and the other telescopes in that volume, as follows.

| EBROCC Telescope Name | OPUS ID Abbrev |
|-----------------------|----------------|
| ESO 1-meter           | `esosil1m04` (missing, is this the same telescope?) |
| ESO 2.2-meter         | `esosil2m2` |
| NASA IRTF             | `irtf` |
| Lick 1-meter          | `lick1m0` (missing) |
| McDonald 2.7-meter    | `mcd2m7` |
| Palomar 200-inch Cass | `pal5m08` |


## Instrument Names and Observation Details (non-Occultation)

Each mission may have observations from one or more instruments. Each instrument
has its own way of recording observations, and so are treated separately here.
The following table shows the format for non-occultation observations.

| Instrument                 | Instrument and Details        | Example |
|----------------------------|-------------------------------|---------|
| Cassini CIRS (time series) | `cirs-<imgnum>-<detector>`    | `co-cirs-0401130240-fp1` |
| Cassini CIRS (cube)        | `cirs-cube-<filename>`        | `co-cirs-cube-c43sa_apprmov002___is____699_f4_400p` |
| Cassini ISS                | `iss-<camera><imgnum>`        | `co-iss-w1294561143` |
| Cassini UVIS               | `uvis-<filename>`             | `co-uvis-euv2004_266_04_11` |
| Cassini VIMS               | `vims-v<sclk>_[ir\|vis]`      | `co-vims-v1855634879_ir` |
| Galileo SSI                | `ssi-c<sclk>`                 | `go-ssi-c0003061100` |
| Voyager ISS                | `iss-<1\|2>-<planet>-c<sclk>` | `vg-iss-1-s-c2783018` |
| Hubble ACS                 | `<propid>-acs-<filename>`     | `hst-09391-acs-j8fb01rqq` |
| Hubble NICMOS              | `<propid>-nicmos-<filename>`  | `hst-07319-nicmos-n41s01010` |
| Hubble STIS                | `<propid>-stis-<filename>`    | `hst-07308-stis-o43ba1bpq` |
| Hubble WFC3                | `<propid>-wfc3-<filename>`    | `hst-12003-wfc3-ibcz21dpq` |
| Hubble WFPC2               | `<propid>-wfpc2-<filename>`   | `hst-05392-wfpc2-u2930301t` |
| New Horizons LORRI         | `lorri-lor_<imgnum>`          | `nh-lorri-lor_0003103486` |
| New Horizons MVIC          | `mvic-<filename>`             | `nh-mvic-mc1_0013194802` |

A few comments on the above:

- In many cases, the PDS3 product filename was used for the OPUS ID because it
  made mapping between OPUS ID and filename easy in PdsFile. This may eventually
  cause problems when those datasets are converted to PDS4 and those filenames
  change. We will have to make a determination at that point whether to continue
  using the old PDS3-based OPUS IDs or take the hit (and break perma-links) and
  reformat the OPUS IDs to match the PDS4 filenames.
- In retrospect, we should've placed the camera after the image number for
  Cassini ISS to make sorting more meaningful.
- Cassini VIMS is unusual in that each product actually contains the data for
  two separate observations - visual and IR. We create two OPUS IDs for the same
  set of products and simply provide different metadata in the database for
  each.
- Our reformatted Voyager ISS volumes (5xxx thru 8xxx) are sorted by planet, and
  thus our OPUS IDs include the name of the planet as well. Given that Voyager 1
  and 2 are jointly considered to be a single mission, the mission abbreviation
  is `vg` for both and the particular number is included after the instrument
  name.
- For HST, we place the proposal ID before the instrument name to make sorting
  more meaningful.

## Instrument Names and Observation Details (Occultation)

Occultations come in two flavors: ring and atmosphere. Each has its own general OPUS ID format.

### Occultations

OPUS IDs for ring occultations follow the format:

`<mission>-<instrument>-occ-<year>-<doy>-<source>-[<ringname>-]<direction>`

OPUS IDs for atmosphere occultations follow the format:

`<mission>-<instrument>-occ-<year>-<doy>-<source>-atmos-<direction>`

- `<instrument>` is the instrument on the spacecraft, or the detector of a ground-based telescope, if known. See below for details.
- `<year>` is the four-digit year.
- `<doy>` is the three-digit day-of-year (with leading zeroes if necessary).
- `<source>` is an abbreviation for the name of the signal source.
  - For stars, the star name is `<3-letter-greek-prefix><3-letter-constellation>` such as `betper` for beta Perseus (Algol). Other abbreviations can be used depending on the star. For example `rleo` is used for the variable star R Leonis. Stars that only have a catalog identifier can be abbreviated in any way deemed reasonable. For the PDS4 Uranus ground-based occultation bundles, that stars are identified using the short names defined in those bundles (e.g. `u5`).
  - For spacecraft sources, `<source>` can be defined as neccessary for that source.
    - For the Cassini RSS occultations, `<source>` is defined as `rev<orbitnum>c-<band>`, such as `rev089c-k34`.
    - For the Voyager RSS occultatoins, `<source>` is defined as `<band>`, such as `s63`.
- Ring only: `<ringname>` is the optional name of the ring covered by the occultation. If no ring name is specified, then more than one ring is covered.
  - For Uranus: `alpha`, `beta`, `delta`, `epsilon`, `eta`, `gamma`, `lambda`, `four`, `five`, `six`, or `ringpl` for the entire ring plane.
- `<direction>` is the direction of the occultation: `i` for ingress, `e` for `egress`, or `b` for both.

For ground-based telescopes, the particular detector is often not specified or
well-defined. For example, for the PDS4 Uranus occultations, all telescopes are
marked as using a "Generic InSb High Speed Photometer". We simply have to do the best we can to figure out an instrument name and provide an appropriate abbreviation for the OPUS ID, or use a generic instrument abbreviation like `insb` when that is not possible.

Example OPUS IDs for various instruments:

| Instrument      | OPUS ID |
|-----------------|---------|
| Cassini RSS     | `co-rss-occ-2008-027-rev057c-s43-i` |
| Cassini UVIS    | `co-uvis-occ-2008-026-gamlup-i` |
| Cassini VIMS    | `co-vims-occ-2007-163-alpori-i` |
| Voyager RSS     | `vg-rss-1-s-occ-1980-318-s63-e` |
| Voyager UVS     | `vg-uvs-1-s-occ-1980-317-iother-e` |
| Voyager UVS     | `vg-uvs-2-u-occ-1986-024-sigsgr-epsilon-i` |
| Voyager UVS     | `vg-uvs-2-u-occ-1986-024-sigsgr-ringpl-i` |
| Voyager PPS     | `vg-pps-2-s-occ-1981-238-delsco-e` |
| Voyager PPS     | `vg-pps-2-u-occ-1986-024-betper-four-i` |
| Lick CCD Camera | `lick1m-ccdc-occ-1989-184-28sgr-i` |
| Palomar 5.08m   | `pal5m08-insb-occ-2002-210-u0201-alpha-i` |
| Palomar 5.08m   | `pal5m08-insb-occ-2002-210-u0201-atmos-i` |
