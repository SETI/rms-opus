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

  - PRODUCT_CREATION_TIME (Steal from COISS)

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

COUVIS:

  - wave_res and waveno_res for HSP and HDAC?

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

HUBBLE:

  - Publication date needs to be searchable as a date/time

IMPORT PROBLEMS WITH LABELS: (as of 5/2/18)

COISS

  As I mentioned earlier, "inst_cmprs_rate" has the misfortune of needing TWO different illegal values: 1.e32, which is currently in the LBL file, and -999, which isn't. Can you support two?

  "optics_temperature" occasionally has a value of 26193824841.0, which must be illegal.

  COISS_1008 and 1009 don't have ring or surface geometry files. I assume this is intentional.

COUVIS:



NH:

  - What is target M7?

  General/PDS Constraints (all search & display):
  - VOLUME_ID
  - INSTRUMENT_ID
  - FILE_SPECIFICATION_NAME
  - DATA_SET_ID
  - PRODUCT_ID
  - TARGET_NAME
  - MISSION_PHASE_NAME
  - PRODUCT_CREATION_TIME
  - START_TIME
  - STOP_TIME
  - OBSERVATION_DESC (goes in NOTE)
    - Should this go into some NH-specific "Observation Name" instead and make NOTE "NULL"?

  Image Constraints (all search & display):
  - EXPOSURE_DURATION

  NHLORRI:
  - Measurement Quantity: REFLECT
  - Spatial Sampling: 2D
  - Wavelength Sampling: N
  - Time Sampling: N
  - Image Type: Frame
  - Image # Levels: 4096
  - Image size: 1024x1024
  NHMVIC:
  - Measurement Quantity: REFLECT
  - Spatial Sampling: 2D
  - Wavelength Sampling: N
  - Time Sampling: N
  - Image Type: Pushbroom
  - Image # Levels: 4096
  - Image size: 5024 x 128

  Wavelength Constraints (all search & display):
  NHLORRI:
  - Wavelength: 0.35 to 0.85
  - Wavelength Resolution: 0.5
  - Wave Number: 10000 / wavelength
  - Wave Number Resolution: WN2 - WN1
  - Spectral information flag: N
  - Spectrum size: N/A
  - Polarization: None
  NHMVIC:
  - Wavelength: 0.4 to 0.975
  - Wavelength Resolution: 0.575
  - Wave Number: 10000 / wavelength
  - Wave Number Resolution: WN2 - WN1
  - Spectral information flag: N
  - Spectrum size: N/A
  - Polarization: None

  Mission New Horizons (all search & display):
  - MISSION_PHASE_NAME
  - SPACECRAFT_CLOCK_PARTITION_NUMBER / SPACECRAFT_CLOCK_START_COUNT
  - SPACECRAFT_CLOCK_PARTITION_NUMBER / SPACECRAFT_CLOCK_STOP_COUNT
    - Format is: "0030598438:48850" - do I leave this as a string or convert it to something?
    - Right now I'm making it "1/0030598438:48850" as a string
  - TELEMETRY_APPLICATION_ID

  - Display only:
    - SEQUENCE ID

  NHLORRI (all search & display):
  - BINNING_MODE
  - INSTRUMENT_COMPRESSION_TYPE (should this be moved to Mission NH?)

  NHMVIC (all search & display):
  - INSTRUMENT_COMPRESSION_TYPE (should this be moved to Mission NH?)

  - Skip entirely (we have ring and moon geometry for NH):
    - REDUCTION_LEVEL
    - PRODUCT_TYPE (EDR vs RDR)
    - APPROX_TARGET_LINE
    - APPROX_TARGET_SAMPLE
    - PHASE_ANGLE
    - SOLAR_ELONGATION
    - SUB_SOLAR_LATITUDE
    - SUB_SOLAR_LONGITUDE
    - SUB_SPACECRAFT_LATITUDE
    - SUB_SPACECRAFT_LONGITUDE
    - RIGHT_ASCENSION
    - DECLINATION
    - CELESTIAL_NORTH_CLOCK_ANGLE
    - BODY_POLE_CLOCK_ANGLE
    - SC_TARGET_POSITION_VECTOR_X
    - SC_TARGET_POSITION_VECTOR_Y
    - SC_TARGET_POSITION_VECTOR_Z
    - SC_TARGET_VELOCITY_VECTOR_X
    - SC_TARGET_VELOCITY_VECTOR_Y
    - SC_TARGET_VELOCITY_VECTOR_Z
    - TARGET_CENTER_DISTANCE
    - TARGET_SUN_POSITION_VECTOR_X
    - TARGET_SUN_POSITION_VECTOR_Y
    - TARGET_SUN_POSITION_VECTOR_Z
    - TARGET_SUN_VELOCITY_VECTOR_X
    - TARGET_SUN_VELOCITY_VECTOR_Y
    - TARGET_SUN_VELOCITY_VECTOR_Z
    - SOLAR_DISTANCE
    - SC_SUN_POSITION_VECTOR_X
    - SC_SUN_POSITION_VECTOR_Y
    - SC_SUN_POSITION_VECTOR_Z
    - SC_SUN_VELOCITY_VECTOR_X
    - SC_SUN_VELOCITY_VECTOR_Y
    - SC_SUN_VELOCITY_VECTOR_Z
    - SPACECRAFT_SOLAR_DISTANCE
    - SC_EARTH_POSITION_VECTOR_X
    - SC_EARTH_POSITION_VECTOR_Y
    - SC_EARTH_POSITION_VECTOR_Z
    - SC_EARTH_VELOCITY_VECTOR_X
    - SC_EARTH_VELOCITY_VECTOR_Y
    - SC_EARTH_VELOCITY_VECTOR_Z
    - SC_GEOCENTRIC_DISTANCE
    - QUATERNIAN_1
    - QUATERNIAN_2
    - QUATERNIAN_3
    - QUATERNIAN_4
