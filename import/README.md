Needed before creating the virtual environment:
  sudo apt-get install libmemcached-dev zlib1g-dev memcached-tools
  watch -n1 -d 'memcstat --servers localhost'

sudo apt-get install python-dev libmysqlclient-dev # Debian / Ubuntu


TODO:

- Update table_schema README file

- SLUGs should really search on DB value ("N") not UI pretty string
  ("Narrow Angle Camera") so we can change the pretty versions in the future.

- Finish commenting files other than do_import

- Audit label files and make sure everything is available in database for
  Details page

- Option to regenerate mult tables from production tables

- ring_geometry longitude_WRT_observer[12] should have max 180 instead of 360,
  but the ring_geo files are wrong!

- For every OBS table:
  - Verify display, display_results, disp_order

  select name, display, display_results, disp_order from param_info where category_name='<obs_table>' order by disp_order;

  - Verify key
  - Verify description
  - Verify dictionary context and name
  - Verify slug names

- Add val_min/val_max to UVIS

- Convert GROUP fields to ENUM if they are constant

- Don't create indexes on import tables

- Drop indexes on permanent tables before copying from import, then put
  indexes back later

- Change foreign keys on instruments to point to mission

- Validate JSON
  - val_min and val_max on all int/real fields?
  - Descriptions?
  - Verify dictionary entries present and pi_context equal to table

- ANALYZE TABLES after updating

- There's really no reason to have an ID for mult tables. Why not just key on the value itself?

THE BIG QUESTIONS:

- GENERIC:

  - Do we really want to exclude "None" from being displayed in group selections? ** PUT BACK IN


- OBS_GENERAL:

  - Ring OBS ID (now RMS Obs ID)
    - All products except OPUS use "/" as a separator but that screws up in URLs
    - OPUS uses _ but then we have a disagreement
    - Should we stick with _ or switch to / and munge the URL with % fields?
    - ** STICK WITH _

  - is_image is 0/1 while cassini.is_prime is Y or N. Hubble flags are 0/1.
    Do we want to be consistent? Always have a flag suffix?  *** Yes/No

- COISS:
**** SURFACE GEO IS BROKEN ****

  - When will the Jupiter surface geo tables be readable?

  - When will the surface geo tables include Venus, Earth, etc?

  - Do we include Jupiter rev_no? Should we rename "Saturn Orbit Number"?

  - "VALID_MAXIMUM_maximum_DN_saturation_level",
    - "Indicates the maximum DN saturation level for the signal returned by the
       A/D converter. Valid values are 255 and 4095. See Appendix B tables",
    - Should values > 4095 be kept or marked as NULL?
    ** YES

- COUVIS:
  - H_LEVEL, D_LEVEL
    - Keep?
      ** ASK MARK
  - BAND1, BAND2, BAND_BINNING, LINE1, LINE2, LINE_BINNING
    - Have -1 values - are these valid or NULL? ** ASK MARK
  - Lots of observations are missing supplemental index entries
  - image_type_id
    - Computed backwards?
           if ($this->obs_general__type_id($row) == "CUBE") {
              return 'PUSH';
          }
          return 'CUBE';
  - image_Levels
    - Always 65535?
  - is_image
    - Ever supposed to be set?

  - Is one of these backwards?
    def populate_obs_wavelength_COUVIS_wave_no_res1():
        metadata = kwargs['metadata']
        wl_row = metadata['obs_wavelength_row']
        wave_res1 = wl_row['wave_res1']   <<<=== ???
        wl2 = wl_row['wavelength2']

        return wave_res1 * 100. / (wl2*wl2)

    def populate_obs_wavelength_COUVIS_wave_no_res2():
        metadata = kwargs['metadata']
        wl_row = metadata['obs_wavelength_row']
        wave_res1 = wl_row['wave_res1']  <<<=== ???
        wl1 = wl_row['wavelength1']

        return wave_res1 * 100. / (wl1*wl1)

- SURFACE GEO:
  - incidence[12] is >90 (hacked JSON for now, should be val_max=90)

  - Observer_longitude[12] <0 (hacked JSON for now, should be val_min=0)
  *** SEND EXAMPLES TO MARK

- GALILEO:
  - Volumes overlap, and occasionally duplicate rms_obs_id

  - planet_id:
    - Currently it is NONE if there is no target_name
