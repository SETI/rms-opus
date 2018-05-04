Needed before creating the virtual environment:
  sudo apt-get install libmemcached-dev zlib1g-dev memcached-tools
  watch -n1 -d 'memcstat --servers localhost'

sudo apt-get install python-dev libmysqlclient-dev # Debian / Ubuntu


TODO:

- Routine to validate JSON files
  - param_info display order
  - Definitions present when needed
  - val_min/max on int and real types

- Instrument-specific definitions of effective wavelength and min/max wavelength
   - Also START_TIME and STOP_TIME

- Clean up mults
  - data_type
  - Cassini rev_no (sort 00A/B/C properly)
  - Cassini primary instrument (put Other last)
  - COUVIS observation type has ""
  - COVIMS VIS sampling mode "Unk"
  - Cassini Image Observation Type has some "" entries

  Cassini image number should be written out in decimal not exp notation

- Update table_schema README file

- SLUGs should really search on DB value ("N") not UI pretty string
  ("Narrow Angle Camera") so we can change the pretty versions in the future.

- Finish commenting files other than do_import

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

- OBS_GENERAL:

  - PRODUCT_CREATION_TIME
  
- COISS:
  - When will the surface geo tables include Venus, Earth, etc?

- COUVIS:
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

  - Right Asc and Declination from index.lbl when ring_geo not available
    Set both min and max to same value?

  - Spacecraft STOP clock count is always unknown - set to same as START?

- SURFACE GEO:
  - incidence[12] is >90 (hacked JSON for now, should be val_max=90)

  - Observer_longitude[12] <0 (hacked JSON for now, should be val_min=0)
  *** SEND EXAMPLES TO MARK

- GALILEO:
  - Volumes overlap, and occasionally duplicate rms_obs_id

  - planet_id:
    - Currently it is NONE if there is no target_name

COVIMS:

  - target_name uses RA,RB etc?

  - wave_no_res?
      $wave_res2 = $this->obs_wavelength__wave_res2($obs);
      $wavelength2 = $this->obs_wavelength__wavelength2($obs);
      $wave_no_res = 100 * $wave_res2/($wavelength2*$wavelength2);
      return $wave_no_res;

  - is_image is always FALSE!

  - image_type_id:
      if phase_name == 'IR' and inst_mod == 'IMAGE':
          return 'RAST'
      if phase_name == "VIS":
          return 'PUSH'
      return 'FIX'

  - Levels? 4096

  - def populate_obs_general_COVIMS_data_type():
      metadata = kwargs['metadata']
      index_row = metadata['index_row']
      inst_mod = index_row['INSTRUMENT_MODE_ID']

      if inst_mod == 'IMAGE':
          return ('IMG', 'Image')
      if inst_mod == 'LINE':
          return ('LINE', 'Line')
      if inst_mod == 'POINT' or inst_mod == 'OCCULTATION':
          return ('POINT', 'Point')

      index_row_num = metadata['index_row_num']
      import_util.announce_nonrepeating_error(
          f'Unknown INSTRUMENT_MODE_ID "{inst_mod}"', index_row_num)
      return ('IMG', 'Image') # XXX

  - RA/DEC without ring_geo?

  - OBS ID "VIMS_015SA_1X6MOVIEA003" - Valid?

  - No MISSION_PHASE_NAME



IMPORT PROBLEMS WITH LABELS: (as of 5/2/18)

COISS

- Times are sometimes in the wrong order. Our index files differ
  from those at JPL:

  (From COISS_1001)
  ERROR | time_sec1 (1999-009T08:21:37.692) and time_sec2 (1999-009T08:20:15.568) are in the wrong order [line 7]

- COISS_xxxx_ring_summary.tab has values from 0 to 360 for
  MINIMUM_LONGITUDE_WRT_OBSERVER and MAXIMUM_LONGITUDE_WRT_OBSERVER
  even though the label file says valid values at -180 to 180.
  This is true for all volumes, both 1xxx and 2xxx.

  (From COISS_1001)
  ERROR | Column "longitude_wrt_observer2" in table "obs_ring_geometry" has maximum value 180 but 360.0 is too large [line 1281]

- COISS_1001_moon_summary.tab has the wrong field size for TARGET_NAME

  (From COISS_1001)
  ERROR | Unknown TARGET_NAME "ADRASTEA"," - edit config_data.py [line 1281]

- MISSING_LINES needs to have NULL_CONSTANT   = -2147483648
  This has already been done in 1001-1009, but appears to be missing
  from all 2xxx volumes.

  However, there are some volumes that use 2147483647 instead.

- FILTER_TEMPERATURE needs to have NULL_CONSTANT = -999
  All Volumes

- SENSOR_HEAD_ELEC_TEMPERATURE needs to have NULL_CONSTANT = -999
  All Volumes

- DETECTOR_TEMPERATURE needs to have NULL_CONSTANT = -999
  All Volumes

- INSTRUMENT_DATA_RATE needs to have NULL_CONSTANT = -999
  All Volumes

- OPTICS_TEMPERATURE currently says (in 1xxx):
    NOT_APPLICABLE_CONSTANT = 1.e32
  and in 2xxx:
    NULL_CONSTANT = -999
  The 2xxx version is correct.
  There are several two cases that have values of 26193824841

- INST_CMPRS_RATE needs to have NULL_CONSTANT = 1e32
  All Volumes
  ALSO needs to have -999 too

COUVIS:
