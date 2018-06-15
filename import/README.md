Needed before creating the virtual environment:
  sudo apt-get install libmemcached-dev zlib1g-dev memcached-tools
  watch -n1 -d 'memcstat --servers localhost'

sudo apt-get install python-dev libmysqlclient-dev # Debian / Ubuntu


TODO:

- Collapse user_collections

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




*** FILES ***

| file_sizes                                               |
+----------------+-----------------------+------+-----+---------+----------------+
| Field          | Type                  | Null | Key | Default | Extra          |
+----------------+-----------------------+------+-----+---------+----------------+
| name           | char(90)              | NO   | MUL | NULL    |                |
| size           | int(11) unsigned      | NO   |     | 0       |                |
| ring_obs_id    | char(40)              | YES  | MUL | NULL    |                |
| volume_id      | char(20)              | YES  |     | NULL    |                |
| file_type      | char(25)              | YES  |     | NULL    |                |
| obs_general_no | mediumint(8) unsigned | NO   | MUL | NULL    |                |
| PRODUCT_TYPE   | char(30)              | YES  |     | NULL    |                |
| file_name      | char(80)              | YES  | MUL | NULL    |                |
| base_path      | char(50)              | YES  |     | NULL    |                |
| id             | int(9)                | NO   | PRI | NULL    | auto_increment |
+----------------+-----------------------+------+-----+---------+----------------+
---------------------------+----+
| name                                                             
| size
| ring_obs_id                   
| volume_id   
| file_type - ALWAYS NULL
| obs_general_no
| PRODUCT_TYPE            
| file_name         
| base_path                             
| id
| COVIMS_0040/data/2009339T163148_2009341T041919/v1638723713_1.LBL
| 6193
| S_CUBE_CO_VIMS_1638723713_VIS
| COVIMS_0040
| NULL      
|        5495244
| RAW_SPECTRAL_IMAGE_CUBE
| v1638723713_1.LBL
| /volumes/pdsdata/volumes/COVIMS_0xxx/
|  1
|
| COISS_2068/data/1680805782_1681997642/N1680805782_1.IMG | 2127944 | S_IMG_CO_ISS_1680805782_N | COISS_2068 | NULL      |        4762709 | RAW_IMAGE    | N1680805782_1.IMG | /volumes/pdsdata/volumes/COISS_2xxx/ | 33832 |
| COISS_2068/LABEL/TLMTAB.FMT                             |   19562 | S_IMG_CO_ISS_1680805782_N | COISS_2068 | NULL      |        4762709 | CALIBRATED   | TLMTAB.FMT        | /volumes/pdsdata/volumes/COISS_2xxx/ | 33833 |
PRODUCT_TYPE:
| RAW_SPECTRAL_IMAGE_CUBE        |
| CALIBRATED_SPECTRUM            |
| CALIBRATED_SPECTRUM_PREFIX     |
| TARGET_TABLE                   |
| FOOTPRINT_GEOMETRY             |
| SYSTEM_GEOMETRY                |
| RING_FOOTPRINT_GEOMETRY        |
| CALIBRATED_IMAGE               |
| CLEANED_IMAGE                  |
| TIEPOINT_TABLE                 |
| GEOMETRICALLY_CORRECTED_IMAGE  |
| DECOMPRESSED_RAW_IMAGE         |
| RESEAU_TABLE                   |
| RAW_IMAGE                      |
| CALIBRATED                     |
| LOSSY_RAW_IMAGE                |
| LOSSY_CALIBRATED_IMAGE         |
| DUPLICATE_RAW_IMAGE            |
| DUPLICATE_LOSSY_RAW_IMAGE      |
| DUPLICATE_CALIBRATED_IMAGE     |
| DUPLICATE_LOSSY_CALIBRATED_IMA |
+--------------------------------+


============================================================================================

| files   
+-------------------------+-------------------------------+------+-----+---------+-------+
| Field                   | Type                          | Null | Key | Default | Extra |
+-------------------------+-------------------------------+------+-----+---------+-------+
| id                      | int(7)                        | NO   | PRI | NULL    |       |
| ring_obs_id             | char(40)                      | YES  | MUL | NULL    |       |
| FILE_SPECIFICATION_NAME | varchar(60)                   | NO   | MUL |         |       |
| VOLUME_ID               | varchar(25)                   | YES  | MUL | NULL    |       |
| PRODUCT_TYPE            | char(50)                      | YES  | MUL | NULL    |       |
| LABEL_TYPE              | enum('DETACHED','ATTACHED')   | YES  |     | NULL    |       |
| OBJECT_TYPE             | enum('IMG','TBL','QUB','DOC') | YES  |     | NULL    |       |
| FILE_FORMAT_TYPE        | char(5)                       | YES  |     | NULL    |       |
| INTERCHANGE_FORMAT      | enum('BINARY','ASCII','BOTH') | YES  |     | NULL    |       |
| instrument_id           | char(9)                       | YES  | MUL | NULL    |       |
| note                    | varchar(255)                  | YES  |     | NULL    |       |
| obs_general_no          | mediumint(6) unsigned         | YES  | MUL | NULL    |       |
| size                    | int(9)                        | YES  |     | NULL    |       |
| ASCII_ext               | varchar(4)                    | YES  |     | NULL    |       |
| LSB_ext                 | varchar(4)                    | YES  |     | NULL    |       |
| MSB_ext                 | varchar(4)                    | YES  |     | NULL    |       |
| detached_label_ext      | varchar(4)                    | YES  |     | NULL    |       |
| extra_files             | text                          | YES  |     | NULL    |       |
| base_path               | char(100)                     | YES  |     | NULL    |       |
| mission_id              | char(2)                       | NO   |     | NULL    |       |
+-------------------------+-------------------------------+------+-----+---------+-------+
| 36067710
| J_IMG_CO_ISS_1351738505_N
| data/1351738505_1351858128/N1351738505_2.IMG       
| COISS_1002
| RAW_IMAGE    
| DETACHED   
| IMG         
| VICAR            
| BINARY             
| COISS         
| NULL
| 3139043
| NULL
| NULL      
| IMG     
| IMG     
| LBL                
| NULL        
| /volumes/pdsdata/volumes/COISS_1xxx/
| CO         
|
| 36505154 | J_IMG_CO_ISS_1351738505_N | data/1351738505_1351858128/N1351738505_2_CALIB.IMG | COISS_1002 | CALIBRATED   | DETACHED   | IMG         | VICAR            | BINARY             | COISS         | NULL |        3139043 | NULL | NULL      | IMG     | IMG     | LBL                | NULL        | /volumes/pdsdata/derived/COISS_1xxx/ | CO   



                                                 |
| files_not_found  
+-------------+-----------+------+-----+---------+----------------+
| Field       | Type      | Null | Key | Default | Extra          |
+-------------+-----------+------+-----+---------+----------------+
| name        | char(150) | NO   | UNI |         |                |
| ring_obs_id | char(100) | YES  | MUL | NULL    |                |
| volume_id   | char(20)  | YES  |     | NULL    |                |
| id          | int(8)    | NO   | PRI | NULL    | auto_increment |
+-------------+-----------+------+-----+---------+----------------+
| COISS_2068/data/1680805782_1681997642/N1680805782_1_CALIB.LBL | S_IMG_CO_ISS_1680805782_N | COISS_2068 | 1647 |
| COISS_2068/data/1680805782_1681997642/N1680805782_1_CALIB.IMG | S_IMG_CO_ISS_1680805782_N | COISS_2068 | 1648 |



| images   
+---------------+------------------+------+-----+---------+----------------+
| Field         | Type             | Null | Key | Default | Extra          |
+---------------+------------------+------+-----+---------+----------------+
| ring_obs_id   | char(40)         | NO   | UNI |         |                |
| thumb         | char(255)        | YES  |     | NULL    |                |
| instrument_id | char(9)          | YES  |     | NULL    |                |
| small         | char(255)        | YES  |     | NULL    |                |
| med           | char(255)        | YES  |     | NULL    |                |
| full          | char(255)        | YES  |     | NULL    |                |
| volume_id     | varchar(30)      | YES  |     | NULL    |                |
| size_thumb    | int(11) unsigned | YES  |     | NULL    |                |
| size_small    | int(11) unsigned | YES  |     | NULL    |                |
| size_med      | int(11) unsigned | YES  |     | NULL    |                |
| size_full     | int(11) unsigned | YES  |     | NULL    |                |
| id            | bigint(20)       | NO   | PRI | NULL    | auto_increment |
+---------------+------------------+------+-----+---------+----------------+
| ring_obs_id   | J_IMG_GO_SSI_0527275700       
| thumb         | GO_0022/I25/EUROPA/C052727/5700R_thumb.jpg                         
| instrument_id | GOSSI         
| small         | GO_0022/I25/EUROPA/C052727/5700R_small.jpg                           
| med           | GO_0022/I25/EUROPA/C052727/5700R_med.jpg                         
| full          | GO_0022/I25/EUROPA/C052727/5700R_full.jpg                          
| volume_id     | GO_0022  
| size_thumb    |       6106
| size_small    |      11047
| size_med      |    47683
| size_full     |    168728
| id            |  1
|
