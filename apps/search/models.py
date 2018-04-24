# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey has `on_delete` set to the desired behavior.
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from __future__ import unicode_literals

from django.db import models


class DjangoMigrations(models.Model):
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


class GroupingTargetName(models.Model):
    value = models.CharField(max_length=100, blank=True, null=True)
    label = models.CharField(max_length=30, blank=True, null=True)
    disp_order = models.IntegerField()
    display = models.CharField(max_length=1)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'grouping_target_name'


class MultObsGeneralDataType(models.Model):
    id = models.IntegerField(primary_key=True)
    value = models.CharField(max_length=100, blank=True, null=True)
    label = models.CharField(max_length=60)
    disp_order = models.IntegerField()
    display = models.CharField(max_length=1)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'mult_obs_general_data_type'


class MultObsGeneralInstHostId(models.Model):
    id = models.IntegerField(primary_key=True)
    value = models.CharField(max_length=100, blank=True, null=True)
    label = models.CharField(max_length=60)
    disp_order = models.IntegerField()
    display = models.CharField(max_length=1)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'mult_obs_general_inst_host_id'


class MultObsGeneralInstrumentId(models.Model):
    id = models.IntegerField(primary_key=True)
    value = models.CharField(max_length=100, blank=True, null=True)
    label = models.CharField(max_length=60)
    disp_order = models.IntegerField()
    display = models.CharField(max_length=1)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'mult_obs_general_instrument_id'


class MultObsGeneralMissionId(models.Model):
    id = models.IntegerField(primary_key=True)
    value = models.CharField(max_length=100, blank=True, null=True)
    label = models.CharField(max_length=60)
    disp_order = models.IntegerField()
    display = models.CharField(max_length=1)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'mult_obs_general_mission_id'


class MultObsGeneralPlanetId(models.Model):
    id = models.IntegerField(primary_key=True)
    value = models.CharField(max_length=100, blank=True, null=True)
    label = models.CharField(max_length=60)
    disp_order = models.IntegerField()
    display = models.CharField(max_length=1)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'mult_obs_general_planet_id'


class MultObsGeneralQuantity(models.Model):
    id = models.IntegerField(primary_key=True)
    value = models.CharField(max_length=100, blank=True, null=True)
    label = models.CharField(max_length=60)
    disp_order = models.IntegerField()
    display = models.CharField(max_length=1)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'mult_obs_general_quantity'


class MultObsGeneralTargetClass(models.Model):
    id = models.IntegerField(primary_key=True)
    value = models.CharField(max_length=100, blank=True, null=True)
    label = models.CharField(max_length=60)
    disp_order = models.IntegerField()
    display = models.CharField(max_length=1)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'mult_obs_general_target_class'


class MultObsGeneralTargetName(models.Model):
    id = models.IntegerField(primary_key=True)
    value = models.CharField(max_length=100, blank=True, null=True)
    label = models.CharField(max_length=30)
    disp_order = models.IntegerField()
    display = models.CharField(max_length=1)
    grouping = models.CharField(max_length=7, blank=True, null=True)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'mult_obs_general_target_name'


class MultObsInstrumentCoissCamera(models.Model):
    id = models.IntegerField(primary_key=True)
    value = models.CharField(max_length=100, blank=True, null=True)
    label = models.CharField(max_length=60)
    disp_order = models.IntegerField()
    display = models.CharField(max_length=1)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'mult_obs_instrument_coiss_camera'


class MultObsInstrumentCoissCombinedFilter(models.Model):
    id = models.IntegerField(primary_key=True)
    value = models.CharField(max_length=100, blank=True, null=True)
    label = models.CharField(max_length=60)
    disp_order = models.IntegerField()
    display = models.CharField(max_length=1)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'mult_obs_instrument_coiss_combined_filter'


class MultObsInstrumentCoissDataConversionType(models.Model):
    id = models.IntegerField(primary_key=True)
    value = models.CharField(max_length=100, blank=True, null=True)
    label = models.CharField(max_length=60)
    disp_order = models.IntegerField()
    display = models.CharField(max_length=1)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'mult_obs_instrument_coiss_data_conversion_type'


class MultObsInstrumentCoissGainModeId(models.Model):
    id = models.IntegerField(primary_key=True)
    value = models.CharField(max_length=100, blank=True, null=True)
    label = models.CharField(max_length=60)
    disp_order = models.IntegerField()
    display = models.CharField(max_length=1)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'mult_obs_instrument_coiss_gain_mode_id'


class MultObsInstrumentCoissImageObservationType(models.Model):
    id = models.IntegerField(primary_key=True)
    value = models.CharField(max_length=100, blank=True, null=True)
    label = models.CharField(max_length=60)
    disp_order = models.IntegerField()
    display = models.CharField(max_length=1)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'mult_obs_instrument_coiss_image_observation_type'


class MultObsInstrumentCoissInstrumentModeId(models.Model):
    id = models.IntegerField(primary_key=True)
    value = models.CharField(max_length=100, blank=True, null=True)
    label = models.CharField(max_length=60)
    disp_order = models.IntegerField()
    display = models.CharField(max_length=1)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'mult_obs_instrument_coiss_instrument_mode_id'


class MultObsInstrumentCoissShutterModeId(models.Model):
    id = models.IntegerField(primary_key=True)
    value = models.CharField(max_length=100, blank=True, null=True)
    label = models.CharField(max_length=60)
    disp_order = models.IntegerField()
    display = models.CharField(max_length=1)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'mult_obs_instrument_coiss_shutter_mode_id'


class MultObsInstrumentCoissShutterStateId(models.Model):
    id = models.IntegerField(primary_key=True)
    value = models.CharField(max_length=100, blank=True, null=True)
    label = models.CharField(max_length=60)
    disp_order = models.IntegerField()
    display = models.CharField(max_length=1)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'mult_obs_instrument_coiss_shutter_state_id'


class MultObsInstrumentCoissTelemetryFormatId(models.Model):
    id = models.IntegerField(primary_key=True)
    value = models.CharField(max_length=100, blank=True, null=True)
    label = models.CharField(max_length=60)
    disp_order = models.IntegerField()
    display = models.CharField(max_length=1)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'mult_obs_instrument_coiss_telemetry_format_id'


class MultObsInstrumentGossiCompressionType(models.Model):
    id = models.IntegerField(primary_key=True)
    value = models.CharField(max_length=100, blank=True, null=True)
    label = models.CharField(max_length=60)
    disp_order = models.IntegerField()
    display = models.CharField(max_length=1)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'mult_obs_instrument_gossi_compression_type'


class MultObsInstrumentGossiFilterName(models.Model):
    id = models.IntegerField(primary_key=True)
    value = models.CharField(max_length=100, blank=True, null=True)
    label = models.CharField(max_length=60)
    disp_order = models.IntegerField()
    display = models.CharField(max_length=1)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'mult_obs_instrument_gossi_filter_name'


class MultObsInstrumentGossiFilterNumber(models.Model):
    id = models.IntegerField(primary_key=True)
    value = models.CharField(max_length=100, blank=True, null=True)
    label = models.CharField(max_length=60)
    disp_order = models.IntegerField()
    display = models.CharField(max_length=1)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'mult_obs_instrument_gossi_filter_number'


class MultObsInstrumentGossiGainModeId(models.Model):
    id = models.IntegerField(primary_key=True)
    value = models.CharField(max_length=100, blank=True, null=True)
    label = models.CharField(max_length=60)
    disp_order = models.IntegerField()
    display = models.CharField(max_length=1)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'mult_obs_instrument_gossi_gain_mode_id'


class MultObsInstrumentGossiObstructionId(models.Model):
    id = models.IntegerField(primary_key=True)
    value = models.CharField(max_length=100, blank=True, null=True)
    label = models.CharField(max_length=60)
    disp_order = models.IntegerField()
    display = models.CharField(max_length=1)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'mult_obs_instrument_gossi_obstruction_id'


class MultObsMissionCassiniCassiniTargetCode(models.Model):
    id = models.IntegerField(primary_key=True)
    value = models.CharField(max_length=100, blank=True, null=True)
    label = models.CharField(max_length=60)
    disp_order = models.IntegerField()
    display = models.CharField(max_length=1)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'mult_obs_mission_cassini_cassini_target_code'


class MultObsMissionCassiniIsPrime(models.Model):
    id = models.IntegerField(primary_key=True)
    value = models.CharField(max_length=100, blank=True, null=True)
    label = models.CharField(max_length=60)
    disp_order = models.IntegerField()
    display = models.CharField(max_length=1)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'mult_obs_mission_cassini_is_prime'


class MultObsMissionCassiniPrimeInstId(models.Model):
    id = models.IntegerField(primary_key=True)
    value = models.CharField(max_length=100, blank=True, null=True)
    label = models.CharField(max_length=60)
    disp_order = models.IntegerField()
    display = models.CharField(max_length=1)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'mult_obs_mission_cassini_prime_inst_id'


class MultObsMissionCassiniRevNo(models.Model):
    id = models.IntegerField(primary_key=True)
    value = models.CharField(max_length=100, blank=True, null=True)
    label = models.CharField(max_length=60)
    disp_order = models.IntegerField()
    display = models.CharField(max_length=1)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'mult_obs_mission_cassini_rev_no'


class MultObsMissionGalileoOrbitNumber(models.Model):
    id = models.IntegerField(primary_key=True)
    value = models.CharField(max_length=100, blank=True, null=True)
    label = models.CharField(max_length=60)
    disp_order = models.IntegerField()
    display = models.CharField(max_length=1)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'mult_obs_mission_galileo_orbit_number'


class MultObsSurfaceGeometryTargetName(models.Model):
    id = models.IntegerField(primary_key=True)
    value = models.CharField(max_length=100, blank=True, null=True)
    label = models.CharField(max_length=30)
    disp_order = models.IntegerField()
    display = models.CharField(max_length=1)
    grouping = models.CharField(max_length=7, blank=True, null=True)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'mult_obs_surface_geometry_target_name'


class MultObsTypeImageImageTypeId(models.Model):
    id = models.IntegerField(primary_key=True)
    value = models.CharField(max_length=100, blank=True, null=True)
    label = models.CharField(max_length=60)
    disp_order = models.IntegerField()
    display = models.CharField(max_length=1)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'mult_obs_type_image_image_type_id'


class MultObsWavelengthPolarizationType(models.Model):
    id = models.IntegerField(primary_key=True)
    value = models.CharField(max_length=100, blank=True, null=True)
    label = models.CharField(max_length=60)
    disp_order = models.IntegerField()
    display = models.CharField(max_length=1)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'mult_obs_wavelength_polarization_type'


class MultObsWavelengthSpecFlag(models.Model):
    id = models.IntegerField(primary_key=True)
    value = models.CharField(max_length=100, blank=True, null=True)
    label = models.CharField(max_length=60)
    disp_order = models.IntegerField()
    display = models.CharField(max_length=1)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'mult_obs_wavelength_spec_flag'


class ObsGeneral(models.Model):
    id = models.IntegerField(primary_key=True)
    rms_obs_id = models.CharField(unique=True, max_length=40)
    volume_id = models.CharField(max_length=11)
    instrument_id = models.CharField(max_length=9)
    mission_id = models.CharField(max_length=3)
    inst_host_id = models.CharField(max_length=3)
    data_type = models.CharField(max_length=7)
    planet_id = models.CharField(max_length=3, blank=True, null=True)
    target_name = models.CharField(max_length=17, blank=True, null=True)
    target_class = models.CharField(max_length=11)
    time1 = models.CharField(max_length=23)
    time2 = models.CharField(max_length=23)
    time_sec1 = models.FloatField()
    time_sec2 = models.FloatField()
    observation_duration = models.FloatField()
    quantity = models.CharField(max_length=25)
    right_asc1 = models.FloatField(blank=True, null=True)
    right_asc2 = models.FloatField(blank=True, null=True)
    right_asc = models.FloatField(blank=True, null=True)
    d_right_asc = models.FloatField(blank=True, null=True)
    declination1 = models.FloatField(blank=True, null=True)
    declination2 = models.FloatField(blank=True, null=True)
    declination = models.FloatField(blank=True, null=True)
    d_declination = models.FloatField(blank=True, null=True)
    note = models.CharField(max_length=255, blank=True, null=True)
    primary_file_spec = models.CharField(max_length=240, blank=True, null=True)
    data_set_id = models.CharField(max_length=40)
    mult_obs_general_instrument = models.ForeignKey(MultObsGeneralInstrumentId, models.DO_NOTHING)
    mult_obs_general_mission = models.ForeignKey(MultObsGeneralMissionId, models.DO_NOTHING)
    mult_obs_general_inst_host = models.ForeignKey(MultObsGeneralInstHostId, models.DO_NOTHING)
    mult_obs_general_data_type = models.ForeignKey(MultObsGeneralDataType, models.DO_NOTHING, db_column='mult_obs_general_data_type')
    mult_obs_general_planet = models.ForeignKey(MultObsGeneralPlanetId, models.DO_NOTHING)
    mult_obs_general_target_name = models.ForeignKey(MultObsGeneralTargetName, models.DO_NOTHING, db_column='mult_obs_general_target_name')
    mult_obs_general_target_class = models.ForeignKey(MultObsGeneralTargetClass, models.DO_NOTHING, db_column='mult_obs_general_target_class')
    mult_obs_general_quantity = models.ForeignKey(MultObsGeneralQuantity, models.DO_NOTHING, db_column='mult_obs_general_quantity')
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'obs_general'


class ObsInstrumentCoiss(models.Model):
    obs_general = models.ForeignKey(ObsGeneral, models.DO_NOTHING)
    rms_obs_id = models.ForeignKey(ObsGeneral, models.DO_NOTHING, related_name='%(class)s_rms_obs_id')
    volume_id = models.CharField(max_length=11)
    antiblooming_state_flag = models.CharField(max_length=3)
    bias_strip_mean = models.FloatField(blank=True, null=True)
    calibration_lamp_state_flag = models.CharField(max_length=3, blank=True, null=True)
    command_sequence_number = models.SmallIntegerField(blank=True, null=True)
    dark_strip_mean = models.FloatField(blank=True, null=True)
    data_conversion_type = models.CharField(max_length=5, blank=True, null=True)
    delayed_readout_flag = models.CharField(max_length=3)
    detector_temperature = models.FloatField(blank=True, null=True)
    electronics_bias = models.SmallIntegerField(blank=True, null=True)
    expected_packets = models.SmallIntegerField(blank=True, null=True)
    filter_name = models.CharField(max_length=13, blank=True, null=True)
    filter_temperature = models.FloatField(blank=True, null=True)
    flight_software_version_id = models.CharField(max_length=4, blank=True, null=True)
    gain_mode_id = models.CharField(max_length=20, blank=True, null=True)
    image_observation_type = models.CharField(max_length=48, blank=True, null=True)
    instrument_data_rate = models.FloatField(blank=True, null=True)
    inst_cmprs_rate_expected_average = models.FloatField(blank=True, null=True)
    inst_cmprs_rate_actual_average = models.FloatField(blank=True, null=True)
    light_flood_state_flag = models.CharField(max_length=3)
    method_desc = models.CharField(max_length=75, blank=True, null=True)
    missing_lines = models.SmallIntegerField(blank=True, null=True)
    missing_packet_flag = models.CharField(max_length=3, blank=True, null=True)
    optics_temperature_front = models.FloatField(blank=True, null=True)
    optics_temperature_rear = models.FloatField(blank=True, null=True)
    order_number = models.SmallIntegerField(blank=True, null=True)
    parallel_clock_voltage_index = models.SmallIntegerField(blank=True, null=True)
    prepare_cycle_index = models.IntegerField(blank=True, null=True)
    product_version_type = models.CharField(max_length=11, blank=True, null=True)
    readout_cycle_index = models.IntegerField(blank=True, null=True)
    received_packets = models.SmallIntegerField(blank=True, null=True)
    sensor_head_elec_temperature = models.FloatField(blank=True, null=True)
    sequence_number = models.SmallIntegerField(blank=True, null=True)
    sequence_title = models.CharField(max_length=60, blank=True, null=True)
    shutter_mode_id = models.CharField(max_length=7, blank=True, null=True)
    shutter_state_id = models.CharField(max_length=8, blank=True, null=True)
    software_version_id = models.CharField(max_length=20, blank=True, null=True)
    telemetry_format_id = models.CharField(max_length=16, blank=True, null=True)
    valid_maximum_minimum_full_well_saturation_level = models.SmallIntegerField(blank=True, null=True)
    valid_maximum_maximum_dn_saturation_level = models.SmallIntegerField(blank=True, null=True)
    product_type = models.CharField(max_length=4, blank=True, null=True)
    standard_data_product_id = models.CharField(max_length=7, blank=True, null=True)
    image_number = models.IntegerField()
    instrument_mode_id = models.CharField(max_length=4)
    target_desc = models.CharField(max_length=75)
    image_mid_time = models.CharField(max_length=22)
    image_time = models.CharField(max_length=22)
    product_creation_time = models.CharField(max_length=22)
    product_id = models.CharField(max_length=18)
    sequence_id = models.CharField(max_length=4)
    combined_filter = models.CharField(max_length=30)
    camera = models.CharField(max_length=1)
    mult_obs_instrument_coiss_data_conversion_type = models.ForeignKey(MultObsInstrumentCoissDataConversionType, models.DO_NOTHING, db_column='mult_obs_instrument_coiss_data_conversion_type')
    mult_obs_instrument_coiss_gain_mode = models.ForeignKey(MultObsInstrumentCoissGainModeId, models.DO_NOTHING)
    mult_obs_instrument_coiss_image_observation_type = models.ForeignKey(MultObsInstrumentCoissImageObservationType, models.DO_NOTHING, db_column='mult_obs_instrument_coiss_image_observation_type')
    mult_obs_instrument_coiss_shutter_mode = models.ForeignKey(MultObsInstrumentCoissShutterModeId, models.DO_NOTHING)
    mult_obs_instrument_coiss_shutter_state = models.ForeignKey(MultObsInstrumentCoissShutterStateId, models.DO_NOTHING)
    mult_obs_instrument_coiss_telemetry_format = models.ForeignKey(MultObsInstrumentCoissTelemetryFormatId, models.DO_NOTHING)
    mult_obs_instrument_coiss_instrument_mode = models.ForeignKey(MultObsInstrumentCoissInstrumentModeId, models.DO_NOTHING)
    mult_obs_instrument_coiss_combined_filter = models.ForeignKey(MultObsInstrumentCoissCombinedFilter, models.DO_NOTHING, db_column='mult_obs_instrument_coiss_combined_filter')
    mult_obs_instrument_coiss_camera = models.ForeignKey(MultObsInstrumentCoissCamera, models.DO_NOTHING, db_column='mult_obs_instrument_coiss_camera')
    id = models.IntegerField(primary_key=True)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'obs_instrument_coiss'


class ObsInstrumentGossi(models.Model):
    obs_general = models.ForeignKey(ObsGeneral, models.DO_NOTHING)
    rms_obs_id = models.ForeignKey(ObsGeneral, models.DO_NOTHING, related_name='%(class)s_rms_obs_id')
    volume_id = models.CharField(max_length=11)
    image_id = models.CharField(max_length=7)
    filter_name = models.CharField(max_length=7)
    filter_number = models.IntegerField()
    gain_mode_id = models.CharField(max_length=4)
    frame_duration = models.FloatField()
    obstruction_id = models.CharField(max_length=17)
    compression_type = models.CharField(max_length=27)
    encoding_min_compression_ratio = models.FloatField()
    encoding_max_compression_ratio = models.FloatField()
    encoding_compression_ratio = models.FloatField()
    processing_history_text = models.CharField(max_length=75)
    mult_obs_instrument_gossi_filter_name = models.ForeignKey(MultObsInstrumentGossiFilterName, models.DO_NOTHING, db_column='mult_obs_instrument_gossi_filter_name')
    mult_obs_instrument_gossi_filter_number = models.ForeignKey(MultObsInstrumentGossiFilterNumber, models.DO_NOTHING, db_column='mult_obs_instrument_gossi_filter_number')
    mult_obs_instrument_gossi_gain_mode = models.ForeignKey(MultObsInstrumentGossiGainModeId, models.DO_NOTHING)
    mult_obs_instrument_gossi_obstruction = models.ForeignKey(MultObsInstrumentGossiObstructionId, models.DO_NOTHING)
    mult_obs_instrument_gossi_compression_type = models.ForeignKey(MultObsInstrumentGossiCompressionType, models.DO_NOTHING, db_column='mult_obs_instrument_gossi_compression_type')
    id = models.IntegerField(primary_key=True)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'obs_instrument_gossi'


class ObsMissionCassini(models.Model):
    obs_general = models.ForeignKey(ObsGeneral, models.DO_NOTHING)
    rms_obs_id = models.ForeignKey(ObsGeneral, models.DO_NOTHING, related_name='%(class)s_rms_obs_id')
    volume_id = models.CharField(max_length=11)
    instrument_id = models.CharField(max_length=9)
    obs_name = models.CharField(max_length=30)
    rev_no = models.CharField(max_length=3, blank=True, null=True)
    is_prime = models.CharField(max_length=3)
    prime_inst_id = models.CharField(max_length=6, blank=True, null=True)
    spacecraft_clock_count1 = models.FloatField(blank=True, null=True)
    spacecraft_clock_count2 = models.FloatField(blank=True, null=True)
    ert1 = models.CharField(max_length=23, blank=True, null=True)
    ert2 = models.CharField(max_length=23, blank=True, null=True)
    ert_sec1 = models.FloatField(blank=True, null=True)
    ert_sec2 = models.FloatField(blank=True, null=True)
    cassini_target_code = models.CharField(max_length=50, blank=True, null=True)
    activity_name = models.CharField(max_length=9, blank=True, null=True)
    mission_phase_name = models.CharField(max_length=32)
    mult_obs_mission_cassini_rev_no = models.ForeignKey(MultObsMissionCassiniRevNo, models.DO_NOTHING, db_column='mult_obs_mission_cassini_rev_no')
    mult_obs_mission_cassini_is_prime = models.ForeignKey(MultObsMissionCassiniIsPrime, models.DO_NOTHING, db_column='mult_obs_mission_cassini_is_prime')
    mult_obs_mission_cassini_prime_inst = models.ForeignKey(MultObsMissionCassiniPrimeInstId, models.DO_NOTHING)
    mult_obs_mission_cassini_cassini_target_code = models.ForeignKey(MultObsMissionCassiniCassiniTargetCode, models.DO_NOTHING, db_column='mult_obs_mission_cassini_cassini_target_code')
    id = models.IntegerField(primary_key=True)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'obs_mission_cassini'


class ObsMissionGalileo(models.Model):
    obs_general = models.ForeignKey(ObsGeneral, models.DO_NOTHING)
    rms_obs_id = models.ForeignKey(ObsGeneral, models.DO_NOTHING, related_name='%(class)s_rms_obs_id')
    volume_id = models.CharField(max_length=11)
    instrument_id = models.CharField(max_length=9)
    observation_id = models.CharField(max_length=20)
    orbit_number = models.IntegerField()
    spacecraft_clock_count1 = models.FloatField()
    spacecraft_clock_count2 = models.FloatField()
    mult_obs_mission_galileo_orbit_number = models.ForeignKey(MultObsMissionGalileoOrbitNumber, models.DO_NOTHING, db_column='mult_obs_mission_galileo_orbit_number')
    id = models.IntegerField(primary_key=True)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'obs_mission_galileo'


class ObsRingGeometry(models.Model):
    obs_general = models.ForeignKey(ObsGeneral, models.DO_NOTHING)
    rms_obs_id = models.ForeignKey(ObsGeneral, models.DO_NOTHING, related_name='%(class)s_rms_obs_id')
    volume_id = models.CharField(max_length=11)
    instrument_id = models.CharField(max_length=9)
    ring_radius1 = models.FloatField(blank=True, null=True)
    ring_radius2 = models.FloatField(blank=True, null=True)
    resolution1 = models.FloatField(blank=True, null=True)
    resolution2 = models.FloatField(blank=True, null=True)
    projected_radial_resolution1 = models.FloatField(blank=True, null=True)
    projected_radial_resolution2 = models.FloatField(blank=True, null=True)
    range_to_ring_intercept1 = models.FloatField(blank=True, null=True)
    range_to_ring_intercept2 = models.FloatField(blank=True, null=True)
    ring_center_distance = models.FloatField(blank=True, null=True)
    j2000_longitude1 = models.FloatField(blank=True, null=True)
    j2000_longitude2 = models.FloatField(blank=True, null=True)
    j2000_longitude = models.FloatField(blank=True, null=True)
    d_j2000_longitude = models.FloatField(blank=True, null=True)
    solar_hour_angle1 = models.FloatField(blank=True, null=True)
    solar_hour_angle2 = models.FloatField(blank=True, null=True)
    solar_hour_angle = models.FloatField(blank=True, null=True)
    d_solar_hour_angle = models.FloatField(blank=True, null=True)
    longitude_wrt_observer1 = models.FloatField(blank=True, null=True)
    longitude_wrt_observer2 = models.FloatField(blank=True, null=True)
    ring_azimuth_wrt_observer1 = models.FloatField(blank=True, null=True)
    ring_azimuth_wrt_observer2 = models.FloatField(blank=True, null=True)
    sub_solar_ring_long = models.FloatField(blank=True, null=True)
    sub_observer_ring_long = models.FloatField(blank=True, null=True)
    solar_ring_elev1 = models.FloatField(blank=True, null=True)
    solar_ring_elev2 = models.FloatField(blank=True, null=True)
    observer_ring_elevation1 = models.FloatField(blank=True, null=True)
    observer_ring_elevation2 = models.FloatField(blank=True, null=True)
    phase1 = models.FloatField(blank=True, null=True)
    phase2 = models.FloatField(blank=True, null=True)
    incidence1 = models.FloatField(blank=True, null=True)
    incidence2 = models.FloatField(blank=True, null=True)
    emission1 = models.FloatField(blank=True, null=True)
    emission2 = models.FloatField(blank=True, null=True)
    north_based_incidence1 = models.FloatField(blank=True, null=True)
    north_based_incidence2 = models.FloatField(blank=True, null=True)
    north_based_emission1 = models.FloatField(blank=True, null=True)
    north_based_emission2 = models.FloatField(blank=True, null=True)
    ring_center_phase = models.FloatField(blank=True, null=True)
    ring_center_incidence = models.FloatField(blank=True, null=True)
    ring_center_emission = models.FloatField(blank=True, null=True)
    ring_center_north_based_incidence = models.FloatField(blank=True, null=True)
    ring_center_north_based_emission = models.FloatField(blank=True, null=True)
    solar_ring_opening_angle = models.FloatField(blank=True, null=True)
    observer_ring_opening_angle = models.FloatField(blank=True, null=True)
    edge_on_radius1 = models.FloatField(blank=True, null=True)
    edge_on_radius2 = models.FloatField(blank=True, null=True)
    edge_on_altitude1 = models.FloatField(blank=True, null=True)
    edge_on_altitude2 = models.FloatField(blank=True, null=True)
    edge_on_radial_resolution1 = models.FloatField(blank=True, null=True)
    edge_on_radial_resolution2 = models.FloatField(blank=True, null=True)
    range_to_edge_on_point1 = models.FloatField(blank=True, null=True)
    range_to_edge_on_point2 = models.FloatField(blank=True, null=True)
    edge_on_j2000_longitude1 = models.FloatField(blank=True, null=True)
    edge_on_j2000_longitude2 = models.FloatField(blank=True, null=True)
    edge_on_j2000_longitude = models.FloatField(blank=True, null=True)
    d_edge_on_j2000_longitude = models.FloatField(blank=True, null=True)
    edge_on_solar_hour_angle1 = models.FloatField(blank=True, null=True)
    edge_on_solar_hour_angle2 = models.FloatField(blank=True, null=True)
    edge_on_solar_hour_angle = models.FloatField(blank=True, null=True)
    d_edge_on_solar_hour_angle = models.FloatField(blank=True, null=True)
    id = models.IntegerField(primary_key=True)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'obs_ring_geometry'


class ObsSurfaceGeometry(models.Model):
    obs_general = models.ForeignKey(ObsGeneral, models.DO_NOTHING)
    rms_obs_id = models.ForeignKey(ObsGeneral, models.DO_NOTHING, related_name='%(class)s_rms_obs_id')
    volume_id = models.CharField(max_length=11)
    instrument_id = models.CharField(max_length=9)
    target_name = models.CharField(max_length=75)
    mult_obs_surface_geometry_target_name = models.ForeignKey(MultObsSurfaceGeometryTargetName, models.DO_NOTHING, db_column='mult_obs_surface_geometry_target_name')
    id = models.IntegerField(primary_key=True)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'obs_surface_geometry'


class ObsSurfaceGeometryAegaeon(models.Model):
    obs_general = models.ForeignKey(ObsGeneral, models.DO_NOTHING)
    rms_obs_id = models.ForeignKey(ObsGeneral, models.DO_NOTHING, related_name='%(class)s_rms_obs_id')
    volume_id = models.CharField(max_length=11)
    instrument_id = models.CharField(max_length=9)
    planetocentric_latitude1 = models.FloatField(blank=True, null=True)
    planetocentric_latitude2 = models.FloatField(blank=True, null=True)
    planetographic_latitude1 = models.FloatField(blank=True, null=True)
    planetographic_latitude2 = models.FloatField(blank=True, null=True)
    iau_west_longitude1 = models.FloatField(blank=True, null=True)
    iau_west_longitude2 = models.FloatField(blank=True, null=True)
    iau_west_longitude = models.FloatField(blank=True, null=True)
    d_iau_west_longitude = models.FloatField(blank=True, null=True)
    solar_hour_angle1 = models.FloatField(blank=True, null=True)
    solar_hour_angle2 = models.FloatField(blank=True, null=True)
    solar_hour_angle = models.FloatField(blank=True, null=True)
    d_solar_hour_angle = models.FloatField(blank=True, null=True)
    observer_longitude1 = models.FloatField(blank=True, null=True)
    observer_longitude2 = models.FloatField(blank=True, null=True)
    observer_longitude = models.FloatField(blank=True, null=True)
    d_observer_longitude = models.FloatField(blank=True, null=True)
    finest_resolution1 = models.FloatField(blank=True, null=True)
    finest_resolution2 = models.FloatField(blank=True, null=True)
    coarsest_resolution1 = models.FloatField(blank=True, null=True)
    coarsest_resolution2 = models.FloatField(blank=True, null=True)
    range_to_body1 = models.FloatField(blank=True, null=True)
    range_to_body2 = models.FloatField(blank=True, null=True)
    phase1 = models.FloatField(blank=True, null=True)
    phase2 = models.FloatField(blank=True, null=True)
    incidence1 = models.FloatField(blank=True, null=True)
    incidence2 = models.FloatField(blank=True, null=True)
    emission1 = models.FloatField(blank=True, null=True)
    emission2 = models.FloatField(blank=True, null=True)
    sub_solar_planetocentric_latitude = models.FloatField(blank=True, null=True)
    sub_solar_planetographic_latitude = models.FloatField(blank=True, null=True)
    sub_observer_planetocentric_latitude = models.FloatField(blank=True, null=True)
    sub_observer_planetographic_latitude = models.FloatField(blank=True, null=True)
    sub_solar_iau_longitude = models.FloatField(blank=True, null=True)
    sub_observer_iau_longitude = models.FloatField(blank=True, null=True)
    center_resolution = models.FloatField(blank=True, null=True)
    center_distance = models.FloatField(blank=True, null=True)
    center_phase_angle = models.FloatField(blank=True, null=True)
    id = models.IntegerField(primary_key=True)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'obs_surface_geometry__aegaeon'


class ObsSurfaceGeometryAnthe(models.Model):
    obs_general = models.ForeignKey(ObsGeneral, models.DO_NOTHING)
    rms_obs_id = models.ForeignKey(ObsGeneral, models.DO_NOTHING, related_name='%(class)s_rms_obs_id')
    volume_id = models.CharField(max_length=11)
    instrument_id = models.CharField(max_length=9)
    planetocentric_latitude1 = models.FloatField(blank=True, null=True)
    planetocentric_latitude2 = models.FloatField(blank=True, null=True)
    planetographic_latitude1 = models.FloatField(blank=True, null=True)
    planetographic_latitude2 = models.FloatField(blank=True, null=True)
    iau_west_longitude1 = models.FloatField(blank=True, null=True)
    iau_west_longitude2 = models.FloatField(blank=True, null=True)
    iau_west_longitude = models.FloatField(blank=True, null=True)
    d_iau_west_longitude = models.FloatField(blank=True, null=True)
    solar_hour_angle1 = models.FloatField(blank=True, null=True)
    solar_hour_angle2 = models.FloatField(blank=True, null=True)
    solar_hour_angle = models.FloatField(blank=True, null=True)
    d_solar_hour_angle = models.FloatField(blank=True, null=True)
    observer_longitude1 = models.FloatField(blank=True, null=True)
    observer_longitude2 = models.FloatField(blank=True, null=True)
    observer_longitude = models.FloatField(blank=True, null=True)
    d_observer_longitude = models.FloatField(blank=True, null=True)
    finest_resolution1 = models.FloatField(blank=True, null=True)
    finest_resolution2 = models.FloatField(blank=True, null=True)
    coarsest_resolution1 = models.FloatField(blank=True, null=True)
    coarsest_resolution2 = models.FloatField(blank=True, null=True)
    range_to_body1 = models.FloatField(blank=True, null=True)
    range_to_body2 = models.FloatField(blank=True, null=True)
    phase1 = models.FloatField(blank=True, null=True)
    phase2 = models.FloatField(blank=True, null=True)
    incidence1 = models.FloatField(blank=True, null=True)
    incidence2 = models.FloatField(blank=True, null=True)
    emission1 = models.FloatField(blank=True, null=True)
    emission2 = models.FloatField(blank=True, null=True)
    sub_solar_planetocentric_latitude = models.FloatField(blank=True, null=True)
    sub_solar_planetographic_latitude = models.FloatField(blank=True, null=True)
    sub_observer_planetocentric_latitude = models.FloatField(blank=True, null=True)
    sub_observer_planetographic_latitude = models.FloatField(blank=True, null=True)
    sub_solar_iau_longitude = models.FloatField(blank=True, null=True)
    sub_observer_iau_longitude = models.FloatField(blank=True, null=True)
    center_resolution = models.FloatField(blank=True, null=True)
    center_distance = models.FloatField(blank=True, null=True)
    center_phase_angle = models.FloatField(blank=True, null=True)
    id = models.IntegerField(primary_key=True)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'obs_surface_geometry__anthe'


class ObsSurfaceGeometryAtlas(models.Model):
    obs_general = models.ForeignKey(ObsGeneral, models.DO_NOTHING)
    rms_obs_id = models.ForeignKey(ObsGeneral, models.DO_NOTHING, related_name='%(class)s_rms_obs_id')
    volume_id = models.CharField(max_length=11)
    instrument_id = models.CharField(max_length=9)
    planetocentric_latitude1 = models.FloatField(blank=True, null=True)
    planetocentric_latitude2 = models.FloatField(blank=True, null=True)
    planetographic_latitude1 = models.FloatField(blank=True, null=True)
    planetographic_latitude2 = models.FloatField(blank=True, null=True)
    iau_west_longitude1 = models.FloatField(blank=True, null=True)
    iau_west_longitude2 = models.FloatField(blank=True, null=True)
    iau_west_longitude = models.FloatField(blank=True, null=True)
    d_iau_west_longitude = models.FloatField(blank=True, null=True)
    solar_hour_angle1 = models.FloatField(blank=True, null=True)
    solar_hour_angle2 = models.FloatField(blank=True, null=True)
    solar_hour_angle = models.FloatField(blank=True, null=True)
    d_solar_hour_angle = models.FloatField(blank=True, null=True)
    observer_longitude1 = models.FloatField(blank=True, null=True)
    observer_longitude2 = models.FloatField(blank=True, null=True)
    observer_longitude = models.FloatField(blank=True, null=True)
    d_observer_longitude = models.FloatField(blank=True, null=True)
    finest_resolution1 = models.FloatField(blank=True, null=True)
    finest_resolution2 = models.FloatField(blank=True, null=True)
    coarsest_resolution1 = models.FloatField(blank=True, null=True)
    coarsest_resolution2 = models.FloatField(blank=True, null=True)
    range_to_body1 = models.FloatField(blank=True, null=True)
    range_to_body2 = models.FloatField(blank=True, null=True)
    phase1 = models.FloatField(blank=True, null=True)
    phase2 = models.FloatField(blank=True, null=True)
    incidence1 = models.FloatField(blank=True, null=True)
    incidence2 = models.FloatField(blank=True, null=True)
    emission1 = models.FloatField(blank=True, null=True)
    emission2 = models.FloatField(blank=True, null=True)
    sub_solar_planetocentric_latitude = models.FloatField(blank=True, null=True)
    sub_solar_planetographic_latitude = models.FloatField(blank=True, null=True)
    sub_observer_planetocentric_latitude = models.FloatField(blank=True, null=True)
    sub_observer_planetographic_latitude = models.FloatField(blank=True, null=True)
    sub_solar_iau_longitude = models.FloatField(blank=True, null=True)
    sub_observer_iau_longitude = models.FloatField(blank=True, null=True)
    center_resolution = models.FloatField(blank=True, null=True)
    center_distance = models.FloatField(blank=True, null=True)
    center_phase_angle = models.FloatField(blank=True, null=True)
    id = models.IntegerField(primary_key=True)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'obs_surface_geometry__atlas'


class ObsSurfaceGeometryCalypso(models.Model):
    obs_general = models.ForeignKey(ObsGeneral, models.DO_NOTHING)
    rms_obs_id = models.ForeignKey(ObsGeneral, models.DO_NOTHING, related_name='%(class)s_rms_obs_id')
    volume_id = models.CharField(max_length=11)
    instrument_id = models.CharField(max_length=9)
    planetocentric_latitude1 = models.FloatField(blank=True, null=True)
    planetocentric_latitude2 = models.FloatField(blank=True, null=True)
    planetographic_latitude1 = models.FloatField(blank=True, null=True)
    planetographic_latitude2 = models.FloatField(blank=True, null=True)
    iau_west_longitude1 = models.FloatField(blank=True, null=True)
    iau_west_longitude2 = models.FloatField(blank=True, null=True)
    iau_west_longitude = models.FloatField(blank=True, null=True)
    d_iau_west_longitude = models.FloatField(blank=True, null=True)
    solar_hour_angle1 = models.FloatField(blank=True, null=True)
    solar_hour_angle2 = models.FloatField(blank=True, null=True)
    solar_hour_angle = models.FloatField(blank=True, null=True)
    d_solar_hour_angle = models.FloatField(blank=True, null=True)
    observer_longitude1 = models.FloatField(blank=True, null=True)
    observer_longitude2 = models.FloatField(blank=True, null=True)
    observer_longitude = models.FloatField(blank=True, null=True)
    d_observer_longitude = models.FloatField(blank=True, null=True)
    finest_resolution1 = models.FloatField(blank=True, null=True)
    finest_resolution2 = models.FloatField(blank=True, null=True)
    coarsest_resolution1 = models.FloatField(blank=True, null=True)
    coarsest_resolution2 = models.FloatField(blank=True, null=True)
    range_to_body1 = models.FloatField(blank=True, null=True)
    range_to_body2 = models.FloatField(blank=True, null=True)
    phase1 = models.FloatField(blank=True, null=True)
    phase2 = models.FloatField(blank=True, null=True)
    incidence1 = models.FloatField(blank=True, null=True)
    incidence2 = models.FloatField(blank=True, null=True)
    emission1 = models.FloatField(blank=True, null=True)
    emission2 = models.FloatField(blank=True, null=True)
    sub_solar_planetocentric_latitude = models.FloatField(blank=True, null=True)
    sub_solar_planetographic_latitude = models.FloatField(blank=True, null=True)
    sub_observer_planetocentric_latitude = models.FloatField(blank=True, null=True)
    sub_observer_planetographic_latitude = models.FloatField(blank=True, null=True)
    sub_solar_iau_longitude = models.FloatField(blank=True, null=True)
    sub_observer_iau_longitude = models.FloatField(blank=True, null=True)
    center_resolution = models.FloatField(blank=True, null=True)
    center_distance = models.FloatField(blank=True, null=True)
    center_phase_angle = models.FloatField(blank=True, null=True)
    id = models.IntegerField(primary_key=True)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'obs_surface_geometry__calypso'


class ObsSurfaceGeometryDaphnis(models.Model):
    obs_general = models.ForeignKey(ObsGeneral, models.DO_NOTHING)
    rms_obs_id = models.ForeignKey(ObsGeneral, models.DO_NOTHING, related_name='%(class)s_rms_obs_id')
    volume_id = models.CharField(max_length=11)
    instrument_id = models.CharField(max_length=9)
    planetocentric_latitude1 = models.FloatField(blank=True, null=True)
    planetocentric_latitude2 = models.FloatField(blank=True, null=True)
    planetographic_latitude1 = models.FloatField(blank=True, null=True)
    planetographic_latitude2 = models.FloatField(blank=True, null=True)
    iau_west_longitude1 = models.FloatField(blank=True, null=True)
    iau_west_longitude2 = models.FloatField(blank=True, null=True)
    iau_west_longitude = models.FloatField(blank=True, null=True)
    d_iau_west_longitude = models.FloatField(blank=True, null=True)
    solar_hour_angle1 = models.FloatField(blank=True, null=True)
    solar_hour_angle2 = models.FloatField(blank=True, null=True)
    solar_hour_angle = models.FloatField(blank=True, null=True)
    d_solar_hour_angle = models.FloatField(blank=True, null=True)
    observer_longitude1 = models.FloatField(blank=True, null=True)
    observer_longitude2 = models.FloatField(blank=True, null=True)
    observer_longitude = models.FloatField(blank=True, null=True)
    d_observer_longitude = models.FloatField(blank=True, null=True)
    finest_resolution1 = models.FloatField(blank=True, null=True)
    finest_resolution2 = models.FloatField(blank=True, null=True)
    coarsest_resolution1 = models.FloatField(blank=True, null=True)
    coarsest_resolution2 = models.FloatField(blank=True, null=True)
    range_to_body1 = models.FloatField(blank=True, null=True)
    range_to_body2 = models.FloatField(blank=True, null=True)
    phase1 = models.FloatField(blank=True, null=True)
    phase2 = models.FloatField(blank=True, null=True)
    incidence1 = models.FloatField(blank=True, null=True)
    incidence2 = models.FloatField(blank=True, null=True)
    emission1 = models.FloatField(blank=True, null=True)
    emission2 = models.FloatField(blank=True, null=True)
    sub_solar_planetocentric_latitude = models.FloatField(blank=True, null=True)
    sub_solar_planetographic_latitude = models.FloatField(blank=True, null=True)
    sub_observer_planetocentric_latitude = models.FloatField(blank=True, null=True)
    sub_observer_planetographic_latitude = models.FloatField(blank=True, null=True)
    sub_solar_iau_longitude = models.FloatField(blank=True, null=True)
    sub_observer_iau_longitude = models.FloatField(blank=True, null=True)
    center_resolution = models.FloatField(blank=True, null=True)
    center_distance = models.FloatField(blank=True, null=True)
    center_phase_angle = models.FloatField(blank=True, null=True)
    id = models.IntegerField(primary_key=True)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'obs_surface_geometry__daphnis'


class ObsSurfaceGeometryDione(models.Model):
    obs_general = models.ForeignKey(ObsGeneral, models.DO_NOTHING)
    rms_obs_id = models.ForeignKey(ObsGeneral, models.DO_NOTHING, related_name='%(class)s_rms_obs_id')
    volume_id = models.CharField(max_length=11)
    instrument_id = models.CharField(max_length=9)
    planetocentric_latitude1 = models.FloatField(blank=True, null=True)
    planetocentric_latitude2 = models.FloatField(blank=True, null=True)
    planetographic_latitude1 = models.FloatField(blank=True, null=True)
    planetographic_latitude2 = models.FloatField(blank=True, null=True)
    iau_west_longitude1 = models.FloatField(blank=True, null=True)
    iau_west_longitude2 = models.FloatField(blank=True, null=True)
    iau_west_longitude = models.FloatField(blank=True, null=True)
    d_iau_west_longitude = models.FloatField(blank=True, null=True)
    solar_hour_angle1 = models.FloatField(blank=True, null=True)
    solar_hour_angle2 = models.FloatField(blank=True, null=True)
    solar_hour_angle = models.FloatField(blank=True, null=True)
    d_solar_hour_angle = models.FloatField(blank=True, null=True)
    observer_longitude1 = models.FloatField(blank=True, null=True)
    observer_longitude2 = models.FloatField(blank=True, null=True)
    observer_longitude = models.FloatField(blank=True, null=True)
    d_observer_longitude = models.FloatField(blank=True, null=True)
    finest_resolution1 = models.FloatField(blank=True, null=True)
    finest_resolution2 = models.FloatField(blank=True, null=True)
    coarsest_resolution1 = models.FloatField(blank=True, null=True)
    coarsest_resolution2 = models.FloatField(blank=True, null=True)
    range_to_body1 = models.FloatField(blank=True, null=True)
    range_to_body2 = models.FloatField(blank=True, null=True)
    phase1 = models.FloatField(blank=True, null=True)
    phase2 = models.FloatField(blank=True, null=True)
    incidence1 = models.FloatField(blank=True, null=True)
    incidence2 = models.FloatField(blank=True, null=True)
    emission1 = models.FloatField(blank=True, null=True)
    emission2 = models.FloatField(blank=True, null=True)
    sub_solar_planetocentric_latitude = models.FloatField(blank=True, null=True)
    sub_solar_planetographic_latitude = models.FloatField(blank=True, null=True)
    sub_observer_planetocentric_latitude = models.FloatField(blank=True, null=True)
    sub_observer_planetographic_latitude = models.FloatField(blank=True, null=True)
    sub_solar_iau_longitude = models.FloatField(blank=True, null=True)
    sub_observer_iau_longitude = models.FloatField(blank=True, null=True)
    center_resolution = models.FloatField(blank=True, null=True)
    center_distance = models.FloatField(blank=True, null=True)
    center_phase_angle = models.FloatField(blank=True, null=True)
    id = models.IntegerField(primary_key=True)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'obs_surface_geometry__dione'


class ObsSurfaceGeometryEnceladus(models.Model):
    obs_general = models.ForeignKey(ObsGeneral, models.DO_NOTHING)
    rms_obs_id = models.ForeignKey(ObsGeneral, models.DO_NOTHING, related_name='%(class)s_rms_obs_id')
    volume_id = models.CharField(max_length=11)
    instrument_id = models.CharField(max_length=9)
    planetocentric_latitude1 = models.FloatField(blank=True, null=True)
    planetocentric_latitude2 = models.FloatField(blank=True, null=True)
    planetographic_latitude1 = models.FloatField(blank=True, null=True)
    planetographic_latitude2 = models.FloatField(blank=True, null=True)
    iau_west_longitude1 = models.FloatField(blank=True, null=True)
    iau_west_longitude2 = models.FloatField(blank=True, null=True)
    iau_west_longitude = models.FloatField(blank=True, null=True)
    d_iau_west_longitude = models.FloatField(blank=True, null=True)
    solar_hour_angle1 = models.FloatField(blank=True, null=True)
    solar_hour_angle2 = models.FloatField(blank=True, null=True)
    solar_hour_angle = models.FloatField(blank=True, null=True)
    d_solar_hour_angle = models.FloatField(blank=True, null=True)
    observer_longitude1 = models.FloatField(blank=True, null=True)
    observer_longitude2 = models.FloatField(blank=True, null=True)
    observer_longitude = models.FloatField(blank=True, null=True)
    d_observer_longitude = models.FloatField(blank=True, null=True)
    finest_resolution1 = models.FloatField(blank=True, null=True)
    finest_resolution2 = models.FloatField(blank=True, null=True)
    coarsest_resolution1 = models.FloatField(blank=True, null=True)
    coarsest_resolution2 = models.FloatField(blank=True, null=True)
    range_to_body1 = models.FloatField(blank=True, null=True)
    range_to_body2 = models.FloatField(blank=True, null=True)
    phase1 = models.FloatField(blank=True, null=True)
    phase2 = models.FloatField(blank=True, null=True)
    incidence1 = models.FloatField(blank=True, null=True)
    incidence2 = models.FloatField(blank=True, null=True)
    emission1 = models.FloatField(blank=True, null=True)
    emission2 = models.FloatField(blank=True, null=True)
    sub_solar_planetocentric_latitude = models.FloatField(blank=True, null=True)
    sub_solar_planetographic_latitude = models.FloatField(blank=True, null=True)
    sub_observer_planetocentric_latitude = models.FloatField(blank=True, null=True)
    sub_observer_planetographic_latitude = models.FloatField(blank=True, null=True)
    sub_solar_iau_longitude = models.FloatField(blank=True, null=True)
    sub_observer_iau_longitude = models.FloatField(blank=True, null=True)
    center_resolution = models.FloatField(blank=True, null=True)
    center_distance = models.FloatField(blank=True, null=True)
    center_phase_angle = models.FloatField(blank=True, null=True)
    id = models.IntegerField(primary_key=True)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'obs_surface_geometry__enceladus'


class ObsSurfaceGeometryEpimetheus(models.Model):
    obs_general = models.ForeignKey(ObsGeneral, models.DO_NOTHING)
    rms_obs_id = models.ForeignKey(ObsGeneral, models.DO_NOTHING, related_name='%(class)s_rms_obs_id')
    volume_id = models.CharField(max_length=11)
    instrument_id = models.CharField(max_length=9)
    planetocentric_latitude1 = models.FloatField(blank=True, null=True)
    planetocentric_latitude2 = models.FloatField(blank=True, null=True)
    planetographic_latitude1 = models.FloatField(blank=True, null=True)
    planetographic_latitude2 = models.FloatField(blank=True, null=True)
    iau_west_longitude1 = models.FloatField(blank=True, null=True)
    iau_west_longitude2 = models.FloatField(blank=True, null=True)
    iau_west_longitude = models.FloatField(blank=True, null=True)
    d_iau_west_longitude = models.FloatField(blank=True, null=True)
    solar_hour_angle1 = models.FloatField(blank=True, null=True)
    solar_hour_angle2 = models.FloatField(blank=True, null=True)
    solar_hour_angle = models.FloatField(blank=True, null=True)
    d_solar_hour_angle = models.FloatField(blank=True, null=True)
    observer_longitude1 = models.FloatField(blank=True, null=True)
    observer_longitude2 = models.FloatField(blank=True, null=True)
    observer_longitude = models.FloatField(blank=True, null=True)
    d_observer_longitude = models.FloatField(blank=True, null=True)
    finest_resolution1 = models.FloatField(blank=True, null=True)
    finest_resolution2 = models.FloatField(blank=True, null=True)
    coarsest_resolution1 = models.FloatField(blank=True, null=True)
    coarsest_resolution2 = models.FloatField(blank=True, null=True)
    range_to_body1 = models.FloatField(blank=True, null=True)
    range_to_body2 = models.FloatField(blank=True, null=True)
    phase1 = models.FloatField(blank=True, null=True)
    phase2 = models.FloatField(blank=True, null=True)
    incidence1 = models.FloatField(blank=True, null=True)
    incidence2 = models.FloatField(blank=True, null=True)
    emission1 = models.FloatField(blank=True, null=True)
    emission2 = models.FloatField(blank=True, null=True)
    sub_solar_planetocentric_latitude = models.FloatField(blank=True, null=True)
    sub_solar_planetographic_latitude = models.FloatField(blank=True, null=True)
    sub_observer_planetocentric_latitude = models.FloatField(blank=True, null=True)
    sub_observer_planetographic_latitude = models.FloatField(blank=True, null=True)
    sub_solar_iau_longitude = models.FloatField(blank=True, null=True)
    sub_observer_iau_longitude = models.FloatField(blank=True, null=True)
    center_resolution = models.FloatField(blank=True, null=True)
    center_distance = models.FloatField(blank=True, null=True)
    center_phase_angle = models.FloatField(blank=True, null=True)
    id = models.IntegerField(primary_key=True)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'obs_surface_geometry__epimetheus'


class ObsSurfaceGeometryHelene(models.Model):
    obs_general = models.ForeignKey(ObsGeneral, models.DO_NOTHING)
    rms_obs_id = models.ForeignKey(ObsGeneral, models.DO_NOTHING, related_name='%(class)s_rms_obs_id')
    volume_id = models.CharField(max_length=11)
    instrument_id = models.CharField(max_length=9)
    planetocentric_latitude1 = models.FloatField(blank=True, null=True)
    planetocentric_latitude2 = models.FloatField(blank=True, null=True)
    planetographic_latitude1 = models.FloatField(blank=True, null=True)
    planetographic_latitude2 = models.FloatField(blank=True, null=True)
    iau_west_longitude1 = models.FloatField(blank=True, null=True)
    iau_west_longitude2 = models.FloatField(blank=True, null=True)
    iau_west_longitude = models.FloatField(blank=True, null=True)
    d_iau_west_longitude = models.FloatField(blank=True, null=True)
    solar_hour_angle1 = models.FloatField(blank=True, null=True)
    solar_hour_angle2 = models.FloatField(blank=True, null=True)
    solar_hour_angle = models.FloatField(blank=True, null=True)
    d_solar_hour_angle = models.FloatField(blank=True, null=True)
    observer_longitude1 = models.FloatField(blank=True, null=True)
    observer_longitude2 = models.FloatField(blank=True, null=True)
    observer_longitude = models.FloatField(blank=True, null=True)
    d_observer_longitude = models.FloatField(blank=True, null=True)
    finest_resolution1 = models.FloatField(blank=True, null=True)
    finest_resolution2 = models.FloatField(blank=True, null=True)
    coarsest_resolution1 = models.FloatField(blank=True, null=True)
    coarsest_resolution2 = models.FloatField(blank=True, null=True)
    range_to_body1 = models.FloatField(blank=True, null=True)
    range_to_body2 = models.FloatField(blank=True, null=True)
    phase1 = models.FloatField(blank=True, null=True)
    phase2 = models.FloatField(blank=True, null=True)
    incidence1 = models.FloatField(blank=True, null=True)
    incidence2 = models.FloatField(blank=True, null=True)
    emission1 = models.FloatField(blank=True, null=True)
    emission2 = models.FloatField(blank=True, null=True)
    sub_solar_planetocentric_latitude = models.FloatField(blank=True, null=True)
    sub_solar_planetographic_latitude = models.FloatField(blank=True, null=True)
    sub_observer_planetocentric_latitude = models.FloatField(blank=True, null=True)
    sub_observer_planetographic_latitude = models.FloatField(blank=True, null=True)
    sub_solar_iau_longitude = models.FloatField(blank=True, null=True)
    sub_observer_iau_longitude = models.FloatField(blank=True, null=True)
    center_resolution = models.FloatField(blank=True, null=True)
    center_distance = models.FloatField(blank=True, null=True)
    center_phase_angle = models.FloatField(blank=True, null=True)
    id = models.IntegerField(primary_key=True)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'obs_surface_geometry__helene'


class ObsSurfaceGeometryHyperion(models.Model):
    obs_general = models.ForeignKey(ObsGeneral, models.DO_NOTHING)
    rms_obs_id = models.ForeignKey(ObsGeneral, models.DO_NOTHING, related_name='%(class)s_rms_obs_id')
    volume_id = models.CharField(max_length=11)
    instrument_id = models.CharField(max_length=9)
    planetocentric_latitude1 = models.FloatField(blank=True, null=True)
    planetocentric_latitude2 = models.FloatField(blank=True, null=True)
    planetographic_latitude1 = models.FloatField(blank=True, null=True)
    planetographic_latitude2 = models.FloatField(blank=True, null=True)
    iau_west_longitude1 = models.FloatField(blank=True, null=True)
    iau_west_longitude2 = models.FloatField(blank=True, null=True)
    iau_west_longitude = models.FloatField(blank=True, null=True)
    d_iau_west_longitude = models.FloatField(blank=True, null=True)
    solar_hour_angle1 = models.FloatField(blank=True, null=True)
    solar_hour_angle2 = models.FloatField(blank=True, null=True)
    solar_hour_angle = models.FloatField(blank=True, null=True)
    d_solar_hour_angle = models.FloatField(blank=True, null=True)
    observer_longitude1 = models.FloatField(blank=True, null=True)
    observer_longitude2 = models.FloatField(blank=True, null=True)
    observer_longitude = models.FloatField(blank=True, null=True)
    d_observer_longitude = models.FloatField(blank=True, null=True)
    finest_resolution1 = models.FloatField(blank=True, null=True)
    finest_resolution2 = models.FloatField(blank=True, null=True)
    coarsest_resolution1 = models.FloatField(blank=True, null=True)
    coarsest_resolution2 = models.FloatField(blank=True, null=True)
    range_to_body1 = models.FloatField(blank=True, null=True)
    range_to_body2 = models.FloatField(blank=True, null=True)
    phase1 = models.FloatField(blank=True, null=True)
    phase2 = models.FloatField(blank=True, null=True)
    incidence1 = models.FloatField(blank=True, null=True)
    incidence2 = models.FloatField(blank=True, null=True)
    emission1 = models.FloatField(blank=True, null=True)
    emission2 = models.FloatField(blank=True, null=True)
    sub_solar_planetocentric_latitude = models.FloatField(blank=True, null=True)
    sub_solar_planetographic_latitude = models.FloatField(blank=True, null=True)
    sub_observer_planetocentric_latitude = models.FloatField(blank=True, null=True)
    sub_observer_planetographic_latitude = models.FloatField(blank=True, null=True)
    sub_solar_iau_longitude = models.FloatField(blank=True, null=True)
    sub_observer_iau_longitude = models.FloatField(blank=True, null=True)
    center_resolution = models.FloatField(blank=True, null=True)
    center_distance = models.FloatField(blank=True, null=True)
    center_phase_angle = models.FloatField(blank=True, null=True)
    id = models.IntegerField(primary_key=True)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'obs_surface_geometry__hyperion'


class ObsSurfaceGeometryHyrokkin(models.Model):
    obs_general = models.ForeignKey(ObsGeneral, models.DO_NOTHING)
    rms_obs_id = models.ForeignKey(ObsGeneral, models.DO_NOTHING, related_name='%(class)s_rms_obs_id')
    volume_id = models.CharField(max_length=11)
    instrument_id = models.CharField(max_length=9)
    planetocentric_latitude1 = models.FloatField(blank=True, null=True)
    planetocentric_latitude2 = models.FloatField(blank=True, null=True)
    planetographic_latitude1 = models.FloatField(blank=True, null=True)
    planetographic_latitude2 = models.FloatField(blank=True, null=True)
    iau_west_longitude1 = models.FloatField(blank=True, null=True)
    iau_west_longitude2 = models.FloatField(blank=True, null=True)
    iau_west_longitude = models.FloatField(blank=True, null=True)
    d_iau_west_longitude = models.FloatField(blank=True, null=True)
    solar_hour_angle1 = models.FloatField(blank=True, null=True)
    solar_hour_angle2 = models.FloatField(blank=True, null=True)
    solar_hour_angle = models.FloatField(blank=True, null=True)
    d_solar_hour_angle = models.FloatField(blank=True, null=True)
    observer_longitude1 = models.FloatField(blank=True, null=True)
    observer_longitude2 = models.FloatField(blank=True, null=True)
    observer_longitude = models.FloatField(blank=True, null=True)
    d_observer_longitude = models.FloatField(blank=True, null=True)
    finest_resolution1 = models.FloatField(blank=True, null=True)
    finest_resolution2 = models.FloatField(blank=True, null=True)
    coarsest_resolution1 = models.FloatField(blank=True, null=True)
    coarsest_resolution2 = models.FloatField(blank=True, null=True)
    range_to_body1 = models.FloatField(blank=True, null=True)
    range_to_body2 = models.FloatField(blank=True, null=True)
    phase1 = models.FloatField(blank=True, null=True)
    phase2 = models.FloatField(blank=True, null=True)
    incidence1 = models.FloatField(blank=True, null=True)
    incidence2 = models.FloatField(blank=True, null=True)
    emission1 = models.FloatField(blank=True, null=True)
    emission2 = models.FloatField(blank=True, null=True)
    sub_solar_planetocentric_latitude = models.FloatField(blank=True, null=True)
    sub_solar_planetographic_latitude = models.FloatField(blank=True, null=True)
    sub_observer_planetocentric_latitude = models.FloatField(blank=True, null=True)
    sub_observer_planetographic_latitude = models.FloatField(blank=True, null=True)
    sub_solar_iau_longitude = models.FloatField(blank=True, null=True)
    sub_observer_iau_longitude = models.FloatField(blank=True, null=True)
    center_resolution = models.FloatField(blank=True, null=True)
    center_distance = models.FloatField(blank=True, null=True)
    center_phase_angle = models.FloatField(blank=True, null=True)
    id = models.IntegerField(primary_key=True)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'obs_surface_geometry__hyrokkin'


class ObsSurfaceGeometryIapetus(models.Model):
    obs_general = models.ForeignKey(ObsGeneral, models.DO_NOTHING)
    rms_obs_id = models.ForeignKey(ObsGeneral, models.DO_NOTHING, related_name='%(class)s_rms_obs_id')
    volume_id = models.CharField(max_length=11)
    instrument_id = models.CharField(max_length=9)
    planetocentric_latitude1 = models.FloatField(blank=True, null=True)
    planetocentric_latitude2 = models.FloatField(blank=True, null=True)
    planetographic_latitude1 = models.FloatField(blank=True, null=True)
    planetographic_latitude2 = models.FloatField(blank=True, null=True)
    iau_west_longitude1 = models.FloatField(blank=True, null=True)
    iau_west_longitude2 = models.FloatField(blank=True, null=True)
    iau_west_longitude = models.FloatField(blank=True, null=True)
    d_iau_west_longitude = models.FloatField(blank=True, null=True)
    solar_hour_angle1 = models.FloatField(blank=True, null=True)
    solar_hour_angle2 = models.FloatField(blank=True, null=True)
    solar_hour_angle = models.FloatField(blank=True, null=True)
    d_solar_hour_angle = models.FloatField(blank=True, null=True)
    observer_longitude1 = models.FloatField(blank=True, null=True)
    observer_longitude2 = models.FloatField(blank=True, null=True)
    observer_longitude = models.FloatField(blank=True, null=True)
    d_observer_longitude = models.FloatField(blank=True, null=True)
    finest_resolution1 = models.FloatField(blank=True, null=True)
    finest_resolution2 = models.FloatField(blank=True, null=True)
    coarsest_resolution1 = models.FloatField(blank=True, null=True)
    coarsest_resolution2 = models.FloatField(blank=True, null=True)
    range_to_body1 = models.FloatField(blank=True, null=True)
    range_to_body2 = models.FloatField(blank=True, null=True)
    phase1 = models.FloatField(blank=True, null=True)
    phase2 = models.FloatField(blank=True, null=True)
    incidence1 = models.FloatField(blank=True, null=True)
    incidence2 = models.FloatField(blank=True, null=True)
    emission1 = models.FloatField(blank=True, null=True)
    emission2 = models.FloatField(blank=True, null=True)
    sub_solar_planetocentric_latitude = models.FloatField(blank=True, null=True)
    sub_solar_planetographic_latitude = models.FloatField(blank=True, null=True)
    sub_observer_planetocentric_latitude = models.FloatField(blank=True, null=True)
    sub_observer_planetographic_latitude = models.FloatField(blank=True, null=True)
    sub_solar_iau_longitude = models.FloatField(blank=True, null=True)
    sub_observer_iau_longitude = models.FloatField(blank=True, null=True)
    center_resolution = models.FloatField(blank=True, null=True)
    center_distance = models.FloatField(blank=True, null=True)
    center_phase_angle = models.FloatField(blank=True, null=True)
    id = models.IntegerField(primary_key=True)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'obs_surface_geometry__iapetus'


class ObsSurfaceGeometryJanus(models.Model):
    obs_general = models.ForeignKey(ObsGeneral, models.DO_NOTHING)
    rms_obs_id = models.ForeignKey(ObsGeneral, models.DO_NOTHING, related_name='%(class)s_rms_obs_id')
    volume_id = models.CharField(max_length=11)
    instrument_id = models.CharField(max_length=9)
    planetocentric_latitude1 = models.FloatField(blank=True, null=True)
    planetocentric_latitude2 = models.FloatField(blank=True, null=True)
    planetographic_latitude1 = models.FloatField(blank=True, null=True)
    planetographic_latitude2 = models.FloatField(blank=True, null=True)
    iau_west_longitude1 = models.FloatField(blank=True, null=True)
    iau_west_longitude2 = models.FloatField(blank=True, null=True)
    iau_west_longitude = models.FloatField(blank=True, null=True)
    d_iau_west_longitude = models.FloatField(blank=True, null=True)
    solar_hour_angle1 = models.FloatField(blank=True, null=True)
    solar_hour_angle2 = models.FloatField(blank=True, null=True)
    solar_hour_angle = models.FloatField(blank=True, null=True)
    d_solar_hour_angle = models.FloatField(blank=True, null=True)
    observer_longitude1 = models.FloatField(blank=True, null=True)
    observer_longitude2 = models.FloatField(blank=True, null=True)
    observer_longitude = models.FloatField(blank=True, null=True)
    d_observer_longitude = models.FloatField(blank=True, null=True)
    finest_resolution1 = models.FloatField(blank=True, null=True)
    finest_resolution2 = models.FloatField(blank=True, null=True)
    coarsest_resolution1 = models.FloatField(blank=True, null=True)
    coarsest_resolution2 = models.FloatField(blank=True, null=True)
    range_to_body1 = models.FloatField(blank=True, null=True)
    range_to_body2 = models.FloatField(blank=True, null=True)
    phase1 = models.FloatField(blank=True, null=True)
    phase2 = models.FloatField(blank=True, null=True)
    incidence1 = models.FloatField(blank=True, null=True)
    incidence2 = models.FloatField(blank=True, null=True)
    emission1 = models.FloatField(blank=True, null=True)
    emission2 = models.FloatField(blank=True, null=True)
    sub_solar_planetocentric_latitude = models.FloatField(blank=True, null=True)
    sub_solar_planetographic_latitude = models.FloatField(blank=True, null=True)
    sub_observer_planetocentric_latitude = models.FloatField(blank=True, null=True)
    sub_observer_planetographic_latitude = models.FloatField(blank=True, null=True)
    sub_solar_iau_longitude = models.FloatField(blank=True, null=True)
    sub_observer_iau_longitude = models.FloatField(blank=True, null=True)
    center_resolution = models.FloatField(blank=True, null=True)
    center_distance = models.FloatField(blank=True, null=True)
    center_phase_angle = models.FloatField(blank=True, null=True)
    id = models.IntegerField(primary_key=True)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'obs_surface_geometry__janus'


class ObsSurfaceGeometryMethone(models.Model):
    obs_general = models.ForeignKey(ObsGeneral, models.DO_NOTHING)
    rms_obs_id = models.ForeignKey(ObsGeneral, models.DO_NOTHING, related_name='%(class)s_rms_obs_id')
    volume_id = models.CharField(max_length=11)
    instrument_id = models.CharField(max_length=9)
    planetocentric_latitude1 = models.FloatField(blank=True, null=True)
    planetocentric_latitude2 = models.FloatField(blank=True, null=True)
    planetographic_latitude1 = models.FloatField(blank=True, null=True)
    planetographic_latitude2 = models.FloatField(blank=True, null=True)
    iau_west_longitude1 = models.FloatField(blank=True, null=True)
    iau_west_longitude2 = models.FloatField(blank=True, null=True)
    iau_west_longitude = models.FloatField(blank=True, null=True)
    d_iau_west_longitude = models.FloatField(blank=True, null=True)
    solar_hour_angle1 = models.FloatField(blank=True, null=True)
    solar_hour_angle2 = models.FloatField(blank=True, null=True)
    solar_hour_angle = models.FloatField(blank=True, null=True)
    d_solar_hour_angle = models.FloatField(blank=True, null=True)
    observer_longitude1 = models.FloatField(blank=True, null=True)
    observer_longitude2 = models.FloatField(blank=True, null=True)
    observer_longitude = models.FloatField(blank=True, null=True)
    d_observer_longitude = models.FloatField(blank=True, null=True)
    finest_resolution1 = models.FloatField(blank=True, null=True)
    finest_resolution2 = models.FloatField(blank=True, null=True)
    coarsest_resolution1 = models.FloatField(blank=True, null=True)
    coarsest_resolution2 = models.FloatField(blank=True, null=True)
    range_to_body1 = models.FloatField(blank=True, null=True)
    range_to_body2 = models.FloatField(blank=True, null=True)
    phase1 = models.FloatField(blank=True, null=True)
    phase2 = models.FloatField(blank=True, null=True)
    incidence1 = models.FloatField(blank=True, null=True)
    incidence2 = models.FloatField(blank=True, null=True)
    emission1 = models.FloatField(blank=True, null=True)
    emission2 = models.FloatField(blank=True, null=True)
    sub_solar_planetocentric_latitude = models.FloatField(blank=True, null=True)
    sub_solar_planetographic_latitude = models.FloatField(blank=True, null=True)
    sub_observer_planetocentric_latitude = models.FloatField(blank=True, null=True)
    sub_observer_planetographic_latitude = models.FloatField(blank=True, null=True)
    sub_solar_iau_longitude = models.FloatField(blank=True, null=True)
    sub_observer_iau_longitude = models.FloatField(blank=True, null=True)
    center_resolution = models.FloatField(blank=True, null=True)
    center_distance = models.FloatField(blank=True, null=True)
    center_phase_angle = models.FloatField(blank=True, null=True)
    id = models.IntegerField(primary_key=True)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'obs_surface_geometry__methone'


class ObsSurfaceGeometryMimas(models.Model):
    obs_general = models.ForeignKey(ObsGeneral, models.DO_NOTHING)
    rms_obs_id = models.ForeignKey(ObsGeneral, models.DO_NOTHING, related_name='%(class)s_rms_obs_id')
    volume_id = models.CharField(max_length=11)
    instrument_id = models.CharField(max_length=9)
    planetocentric_latitude1 = models.FloatField(blank=True, null=True)
    planetocentric_latitude2 = models.FloatField(blank=True, null=True)
    planetographic_latitude1 = models.FloatField(blank=True, null=True)
    planetographic_latitude2 = models.FloatField(blank=True, null=True)
    iau_west_longitude1 = models.FloatField(blank=True, null=True)
    iau_west_longitude2 = models.FloatField(blank=True, null=True)
    iau_west_longitude = models.FloatField(blank=True, null=True)
    d_iau_west_longitude = models.FloatField(blank=True, null=True)
    solar_hour_angle1 = models.FloatField(blank=True, null=True)
    solar_hour_angle2 = models.FloatField(blank=True, null=True)
    solar_hour_angle = models.FloatField(blank=True, null=True)
    d_solar_hour_angle = models.FloatField(blank=True, null=True)
    observer_longitude1 = models.FloatField(blank=True, null=True)
    observer_longitude2 = models.FloatField(blank=True, null=True)
    observer_longitude = models.FloatField(blank=True, null=True)
    d_observer_longitude = models.FloatField(blank=True, null=True)
    finest_resolution1 = models.FloatField(blank=True, null=True)
    finest_resolution2 = models.FloatField(blank=True, null=True)
    coarsest_resolution1 = models.FloatField(blank=True, null=True)
    coarsest_resolution2 = models.FloatField(blank=True, null=True)
    range_to_body1 = models.FloatField(blank=True, null=True)
    range_to_body2 = models.FloatField(blank=True, null=True)
    phase1 = models.FloatField(blank=True, null=True)
    phase2 = models.FloatField(blank=True, null=True)
    incidence1 = models.FloatField(blank=True, null=True)
    incidence2 = models.FloatField(blank=True, null=True)
    emission1 = models.FloatField(blank=True, null=True)
    emission2 = models.FloatField(blank=True, null=True)
    sub_solar_planetocentric_latitude = models.FloatField(blank=True, null=True)
    sub_solar_planetographic_latitude = models.FloatField(blank=True, null=True)
    sub_observer_planetocentric_latitude = models.FloatField(blank=True, null=True)
    sub_observer_planetographic_latitude = models.FloatField(blank=True, null=True)
    sub_solar_iau_longitude = models.FloatField(blank=True, null=True)
    sub_observer_iau_longitude = models.FloatField(blank=True, null=True)
    center_resolution = models.FloatField(blank=True, null=True)
    center_distance = models.FloatField(blank=True, null=True)
    center_phase_angle = models.FloatField(blank=True, null=True)
    id = models.IntegerField(primary_key=True)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'obs_surface_geometry__mimas'


class ObsSurfaceGeometryPallene(models.Model):
    obs_general = models.ForeignKey(ObsGeneral, models.DO_NOTHING)
    rms_obs_id = models.ForeignKey(ObsGeneral, models.DO_NOTHING, related_name='%(class)s_rms_obs_id')
    volume_id = models.CharField(max_length=11)
    instrument_id = models.CharField(max_length=9)
    planetocentric_latitude1 = models.FloatField(blank=True, null=True)
    planetocentric_latitude2 = models.FloatField(blank=True, null=True)
    planetographic_latitude1 = models.FloatField(blank=True, null=True)
    planetographic_latitude2 = models.FloatField(blank=True, null=True)
    iau_west_longitude1 = models.FloatField(blank=True, null=True)
    iau_west_longitude2 = models.FloatField(blank=True, null=True)
    iau_west_longitude = models.FloatField(blank=True, null=True)
    d_iau_west_longitude = models.FloatField(blank=True, null=True)
    solar_hour_angle1 = models.FloatField(blank=True, null=True)
    solar_hour_angle2 = models.FloatField(blank=True, null=True)
    solar_hour_angle = models.FloatField(blank=True, null=True)
    d_solar_hour_angle = models.FloatField(blank=True, null=True)
    observer_longitude1 = models.FloatField(blank=True, null=True)
    observer_longitude2 = models.FloatField(blank=True, null=True)
    observer_longitude = models.FloatField(blank=True, null=True)
    d_observer_longitude = models.FloatField(blank=True, null=True)
    finest_resolution1 = models.FloatField(blank=True, null=True)
    finest_resolution2 = models.FloatField(blank=True, null=True)
    coarsest_resolution1 = models.FloatField(blank=True, null=True)
    coarsest_resolution2 = models.FloatField(blank=True, null=True)
    range_to_body1 = models.FloatField(blank=True, null=True)
    range_to_body2 = models.FloatField(blank=True, null=True)
    phase1 = models.FloatField(blank=True, null=True)
    phase2 = models.FloatField(blank=True, null=True)
    incidence1 = models.FloatField(blank=True, null=True)
    incidence2 = models.FloatField(blank=True, null=True)
    emission1 = models.FloatField(blank=True, null=True)
    emission2 = models.FloatField(blank=True, null=True)
    sub_solar_planetocentric_latitude = models.FloatField(blank=True, null=True)
    sub_solar_planetographic_latitude = models.FloatField(blank=True, null=True)
    sub_observer_planetocentric_latitude = models.FloatField(blank=True, null=True)
    sub_observer_planetographic_latitude = models.FloatField(blank=True, null=True)
    sub_solar_iau_longitude = models.FloatField(blank=True, null=True)
    sub_observer_iau_longitude = models.FloatField(blank=True, null=True)
    center_resolution = models.FloatField(blank=True, null=True)
    center_distance = models.FloatField(blank=True, null=True)
    center_phase_angle = models.FloatField(blank=True, null=True)
    id = models.IntegerField(primary_key=True)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'obs_surface_geometry__pallene'


class ObsSurfaceGeometryPan(models.Model):
    obs_general = models.ForeignKey(ObsGeneral, models.DO_NOTHING)
    rms_obs_id = models.ForeignKey(ObsGeneral, models.DO_NOTHING, related_name='%(class)s_rms_obs_id')
    volume_id = models.CharField(max_length=11)
    instrument_id = models.CharField(max_length=9)
    planetocentric_latitude1 = models.FloatField(blank=True, null=True)
    planetocentric_latitude2 = models.FloatField(blank=True, null=True)
    planetographic_latitude1 = models.FloatField(blank=True, null=True)
    planetographic_latitude2 = models.FloatField(blank=True, null=True)
    iau_west_longitude1 = models.FloatField(blank=True, null=True)
    iau_west_longitude2 = models.FloatField(blank=True, null=True)
    iau_west_longitude = models.FloatField(blank=True, null=True)
    d_iau_west_longitude = models.FloatField(blank=True, null=True)
    solar_hour_angle1 = models.FloatField(blank=True, null=True)
    solar_hour_angle2 = models.FloatField(blank=True, null=True)
    solar_hour_angle = models.FloatField(blank=True, null=True)
    d_solar_hour_angle = models.FloatField(blank=True, null=True)
    observer_longitude1 = models.FloatField(blank=True, null=True)
    observer_longitude2 = models.FloatField(blank=True, null=True)
    observer_longitude = models.FloatField(blank=True, null=True)
    d_observer_longitude = models.FloatField(blank=True, null=True)
    finest_resolution1 = models.FloatField(blank=True, null=True)
    finest_resolution2 = models.FloatField(blank=True, null=True)
    coarsest_resolution1 = models.FloatField(blank=True, null=True)
    coarsest_resolution2 = models.FloatField(blank=True, null=True)
    range_to_body1 = models.FloatField(blank=True, null=True)
    range_to_body2 = models.FloatField(blank=True, null=True)
    phase1 = models.FloatField(blank=True, null=True)
    phase2 = models.FloatField(blank=True, null=True)
    incidence1 = models.FloatField(blank=True, null=True)
    incidence2 = models.FloatField(blank=True, null=True)
    emission1 = models.FloatField(blank=True, null=True)
    emission2 = models.FloatField(blank=True, null=True)
    sub_solar_planetocentric_latitude = models.FloatField(blank=True, null=True)
    sub_solar_planetographic_latitude = models.FloatField(blank=True, null=True)
    sub_observer_planetocentric_latitude = models.FloatField(blank=True, null=True)
    sub_observer_planetographic_latitude = models.FloatField(blank=True, null=True)
    sub_solar_iau_longitude = models.FloatField(blank=True, null=True)
    sub_observer_iau_longitude = models.FloatField(blank=True, null=True)
    center_resolution = models.FloatField(blank=True, null=True)
    center_distance = models.FloatField(blank=True, null=True)
    center_phase_angle = models.FloatField(blank=True, null=True)
    id = models.IntegerField(primary_key=True)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'obs_surface_geometry__pan'


class ObsSurfaceGeometryPandora(models.Model):
    obs_general = models.ForeignKey(ObsGeneral, models.DO_NOTHING)
    rms_obs_id = models.ForeignKey(ObsGeneral, models.DO_NOTHING, related_name='%(class)s_rms_obs_id')
    volume_id = models.CharField(max_length=11)
    instrument_id = models.CharField(max_length=9)
    planetocentric_latitude1 = models.FloatField(blank=True, null=True)
    planetocentric_latitude2 = models.FloatField(blank=True, null=True)
    planetographic_latitude1 = models.FloatField(blank=True, null=True)
    planetographic_latitude2 = models.FloatField(blank=True, null=True)
    iau_west_longitude1 = models.FloatField(blank=True, null=True)
    iau_west_longitude2 = models.FloatField(blank=True, null=True)
    iau_west_longitude = models.FloatField(blank=True, null=True)
    d_iau_west_longitude = models.FloatField(blank=True, null=True)
    solar_hour_angle1 = models.FloatField(blank=True, null=True)
    solar_hour_angle2 = models.FloatField(blank=True, null=True)
    solar_hour_angle = models.FloatField(blank=True, null=True)
    d_solar_hour_angle = models.FloatField(blank=True, null=True)
    observer_longitude1 = models.FloatField(blank=True, null=True)
    observer_longitude2 = models.FloatField(blank=True, null=True)
    observer_longitude = models.FloatField(blank=True, null=True)
    d_observer_longitude = models.FloatField(blank=True, null=True)
    finest_resolution1 = models.FloatField(blank=True, null=True)
    finest_resolution2 = models.FloatField(blank=True, null=True)
    coarsest_resolution1 = models.FloatField(blank=True, null=True)
    coarsest_resolution2 = models.FloatField(blank=True, null=True)
    range_to_body1 = models.FloatField(blank=True, null=True)
    range_to_body2 = models.FloatField(blank=True, null=True)
    phase1 = models.FloatField(blank=True, null=True)
    phase2 = models.FloatField(blank=True, null=True)
    incidence1 = models.FloatField(blank=True, null=True)
    incidence2 = models.FloatField(blank=True, null=True)
    emission1 = models.FloatField(blank=True, null=True)
    emission2 = models.FloatField(blank=True, null=True)
    sub_solar_planetocentric_latitude = models.FloatField(blank=True, null=True)
    sub_solar_planetographic_latitude = models.FloatField(blank=True, null=True)
    sub_observer_planetocentric_latitude = models.FloatField(blank=True, null=True)
    sub_observer_planetographic_latitude = models.FloatField(blank=True, null=True)
    sub_solar_iau_longitude = models.FloatField(blank=True, null=True)
    sub_observer_iau_longitude = models.FloatField(blank=True, null=True)
    center_resolution = models.FloatField(blank=True, null=True)
    center_distance = models.FloatField(blank=True, null=True)
    center_phase_angle = models.FloatField(blank=True, null=True)
    id = models.IntegerField(primary_key=True)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'obs_surface_geometry__pandora'


class ObsSurfaceGeometryPhoebe(models.Model):
    obs_general = models.ForeignKey(ObsGeneral, models.DO_NOTHING)
    rms_obs_id = models.ForeignKey(ObsGeneral, models.DO_NOTHING, related_name='%(class)s_rms_obs_id')
    volume_id = models.CharField(max_length=11)
    instrument_id = models.CharField(max_length=9)
    planetocentric_latitude1 = models.FloatField(blank=True, null=True)
    planetocentric_latitude2 = models.FloatField(blank=True, null=True)
    planetographic_latitude1 = models.FloatField(blank=True, null=True)
    planetographic_latitude2 = models.FloatField(blank=True, null=True)
    iau_west_longitude1 = models.FloatField(blank=True, null=True)
    iau_west_longitude2 = models.FloatField(blank=True, null=True)
    iau_west_longitude = models.FloatField(blank=True, null=True)
    d_iau_west_longitude = models.FloatField(blank=True, null=True)
    solar_hour_angle1 = models.FloatField(blank=True, null=True)
    solar_hour_angle2 = models.FloatField(blank=True, null=True)
    solar_hour_angle = models.FloatField(blank=True, null=True)
    d_solar_hour_angle = models.FloatField(blank=True, null=True)
    observer_longitude1 = models.FloatField(blank=True, null=True)
    observer_longitude2 = models.FloatField(blank=True, null=True)
    observer_longitude = models.FloatField(blank=True, null=True)
    d_observer_longitude = models.FloatField(blank=True, null=True)
    finest_resolution1 = models.FloatField(blank=True, null=True)
    finest_resolution2 = models.FloatField(blank=True, null=True)
    coarsest_resolution1 = models.FloatField(blank=True, null=True)
    coarsest_resolution2 = models.FloatField(blank=True, null=True)
    range_to_body1 = models.FloatField(blank=True, null=True)
    range_to_body2 = models.FloatField(blank=True, null=True)
    phase1 = models.FloatField(blank=True, null=True)
    phase2 = models.FloatField(blank=True, null=True)
    incidence1 = models.FloatField(blank=True, null=True)
    incidence2 = models.FloatField(blank=True, null=True)
    emission1 = models.FloatField(blank=True, null=True)
    emission2 = models.FloatField(blank=True, null=True)
    sub_solar_planetocentric_latitude = models.FloatField(blank=True, null=True)
    sub_solar_planetographic_latitude = models.FloatField(blank=True, null=True)
    sub_observer_planetocentric_latitude = models.FloatField(blank=True, null=True)
    sub_observer_planetographic_latitude = models.FloatField(blank=True, null=True)
    sub_solar_iau_longitude = models.FloatField(blank=True, null=True)
    sub_observer_iau_longitude = models.FloatField(blank=True, null=True)
    center_resolution = models.FloatField(blank=True, null=True)
    center_distance = models.FloatField(blank=True, null=True)
    center_phase_angle = models.FloatField(blank=True, null=True)
    id = models.IntegerField(primary_key=True)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'obs_surface_geometry__phoebe'


class ObsSurfaceGeometryPolydeuces(models.Model):
    obs_general = models.ForeignKey(ObsGeneral, models.DO_NOTHING)
    rms_obs_id = models.ForeignKey(ObsGeneral, models.DO_NOTHING, related_name='%(class)s_rms_obs_id')
    volume_id = models.CharField(max_length=11)
    instrument_id = models.CharField(max_length=9)
    planetocentric_latitude1 = models.FloatField(blank=True, null=True)
    planetocentric_latitude2 = models.FloatField(blank=True, null=True)
    planetographic_latitude1 = models.FloatField(blank=True, null=True)
    planetographic_latitude2 = models.FloatField(blank=True, null=True)
    iau_west_longitude1 = models.FloatField(blank=True, null=True)
    iau_west_longitude2 = models.FloatField(blank=True, null=True)
    iau_west_longitude = models.FloatField(blank=True, null=True)
    d_iau_west_longitude = models.FloatField(blank=True, null=True)
    solar_hour_angle1 = models.FloatField(blank=True, null=True)
    solar_hour_angle2 = models.FloatField(blank=True, null=True)
    solar_hour_angle = models.FloatField(blank=True, null=True)
    d_solar_hour_angle = models.FloatField(blank=True, null=True)
    observer_longitude1 = models.FloatField(blank=True, null=True)
    observer_longitude2 = models.FloatField(blank=True, null=True)
    observer_longitude = models.FloatField(blank=True, null=True)
    d_observer_longitude = models.FloatField(blank=True, null=True)
    finest_resolution1 = models.FloatField(blank=True, null=True)
    finest_resolution2 = models.FloatField(blank=True, null=True)
    coarsest_resolution1 = models.FloatField(blank=True, null=True)
    coarsest_resolution2 = models.FloatField(blank=True, null=True)
    range_to_body1 = models.FloatField(blank=True, null=True)
    range_to_body2 = models.FloatField(blank=True, null=True)
    phase1 = models.FloatField(blank=True, null=True)
    phase2 = models.FloatField(blank=True, null=True)
    incidence1 = models.FloatField(blank=True, null=True)
    incidence2 = models.FloatField(blank=True, null=True)
    emission1 = models.FloatField(blank=True, null=True)
    emission2 = models.FloatField(blank=True, null=True)
    sub_solar_planetocentric_latitude = models.FloatField(blank=True, null=True)
    sub_solar_planetographic_latitude = models.FloatField(blank=True, null=True)
    sub_observer_planetocentric_latitude = models.FloatField(blank=True, null=True)
    sub_observer_planetographic_latitude = models.FloatField(blank=True, null=True)
    sub_solar_iau_longitude = models.FloatField(blank=True, null=True)
    sub_observer_iau_longitude = models.FloatField(blank=True, null=True)
    center_resolution = models.FloatField(blank=True, null=True)
    center_distance = models.FloatField(blank=True, null=True)
    center_phase_angle = models.FloatField(blank=True, null=True)
    id = models.IntegerField(primary_key=True)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'obs_surface_geometry__polydeuces'


class ObsSurfaceGeometryPrometheus(models.Model):
    obs_general = models.ForeignKey(ObsGeneral, models.DO_NOTHING)
    rms_obs_id = models.ForeignKey(ObsGeneral, models.DO_NOTHING, related_name='%(class)s_rms_obs_id')
    volume_id = models.CharField(max_length=11)
    instrument_id = models.CharField(max_length=9)
    planetocentric_latitude1 = models.FloatField(blank=True, null=True)
    planetocentric_latitude2 = models.FloatField(blank=True, null=True)
    planetographic_latitude1 = models.FloatField(blank=True, null=True)
    planetographic_latitude2 = models.FloatField(blank=True, null=True)
    iau_west_longitude1 = models.FloatField(blank=True, null=True)
    iau_west_longitude2 = models.FloatField(blank=True, null=True)
    iau_west_longitude = models.FloatField(blank=True, null=True)
    d_iau_west_longitude = models.FloatField(blank=True, null=True)
    solar_hour_angle1 = models.FloatField(blank=True, null=True)
    solar_hour_angle2 = models.FloatField(blank=True, null=True)
    solar_hour_angle = models.FloatField(blank=True, null=True)
    d_solar_hour_angle = models.FloatField(blank=True, null=True)
    observer_longitude1 = models.FloatField(blank=True, null=True)
    observer_longitude2 = models.FloatField(blank=True, null=True)
    observer_longitude = models.FloatField(blank=True, null=True)
    d_observer_longitude = models.FloatField(blank=True, null=True)
    finest_resolution1 = models.FloatField(blank=True, null=True)
    finest_resolution2 = models.FloatField(blank=True, null=True)
    coarsest_resolution1 = models.FloatField(blank=True, null=True)
    coarsest_resolution2 = models.FloatField(blank=True, null=True)
    range_to_body1 = models.FloatField(blank=True, null=True)
    range_to_body2 = models.FloatField(blank=True, null=True)
    phase1 = models.FloatField(blank=True, null=True)
    phase2 = models.FloatField(blank=True, null=True)
    incidence1 = models.FloatField(blank=True, null=True)
    incidence2 = models.FloatField(blank=True, null=True)
    emission1 = models.FloatField(blank=True, null=True)
    emission2 = models.FloatField(blank=True, null=True)
    sub_solar_planetocentric_latitude = models.FloatField(blank=True, null=True)
    sub_solar_planetographic_latitude = models.FloatField(blank=True, null=True)
    sub_observer_planetocentric_latitude = models.FloatField(blank=True, null=True)
    sub_observer_planetographic_latitude = models.FloatField(blank=True, null=True)
    sub_solar_iau_longitude = models.FloatField(blank=True, null=True)
    sub_observer_iau_longitude = models.FloatField(blank=True, null=True)
    center_resolution = models.FloatField(blank=True, null=True)
    center_distance = models.FloatField(blank=True, null=True)
    center_phase_angle = models.FloatField(blank=True, null=True)
    id = models.IntegerField(primary_key=True)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'obs_surface_geometry__prometheus'


class ObsSurfaceGeometryRhea(models.Model):
    obs_general = models.ForeignKey(ObsGeneral, models.DO_NOTHING)
    rms_obs_id = models.ForeignKey(ObsGeneral, models.DO_NOTHING, related_name='%(class)s_rms_obs_id')
    volume_id = models.CharField(max_length=11)
    instrument_id = models.CharField(max_length=9)
    planetocentric_latitude1 = models.FloatField(blank=True, null=True)
    planetocentric_latitude2 = models.FloatField(blank=True, null=True)
    planetographic_latitude1 = models.FloatField(blank=True, null=True)
    planetographic_latitude2 = models.FloatField(blank=True, null=True)
    iau_west_longitude1 = models.FloatField(blank=True, null=True)
    iau_west_longitude2 = models.FloatField(blank=True, null=True)
    iau_west_longitude = models.FloatField(blank=True, null=True)
    d_iau_west_longitude = models.FloatField(blank=True, null=True)
    solar_hour_angle1 = models.FloatField(blank=True, null=True)
    solar_hour_angle2 = models.FloatField(blank=True, null=True)
    solar_hour_angle = models.FloatField(blank=True, null=True)
    d_solar_hour_angle = models.FloatField(blank=True, null=True)
    observer_longitude1 = models.FloatField(blank=True, null=True)
    observer_longitude2 = models.FloatField(blank=True, null=True)
    observer_longitude = models.FloatField(blank=True, null=True)
    d_observer_longitude = models.FloatField(blank=True, null=True)
    finest_resolution1 = models.FloatField(blank=True, null=True)
    finest_resolution2 = models.FloatField(blank=True, null=True)
    coarsest_resolution1 = models.FloatField(blank=True, null=True)
    coarsest_resolution2 = models.FloatField(blank=True, null=True)
    range_to_body1 = models.FloatField(blank=True, null=True)
    range_to_body2 = models.FloatField(blank=True, null=True)
    phase1 = models.FloatField(blank=True, null=True)
    phase2 = models.FloatField(blank=True, null=True)
    incidence1 = models.FloatField(blank=True, null=True)
    incidence2 = models.FloatField(blank=True, null=True)
    emission1 = models.FloatField(blank=True, null=True)
    emission2 = models.FloatField(blank=True, null=True)
    sub_solar_planetocentric_latitude = models.FloatField(blank=True, null=True)
    sub_solar_planetographic_latitude = models.FloatField(blank=True, null=True)
    sub_observer_planetocentric_latitude = models.FloatField(blank=True, null=True)
    sub_observer_planetographic_latitude = models.FloatField(blank=True, null=True)
    sub_solar_iau_longitude = models.FloatField(blank=True, null=True)
    sub_observer_iau_longitude = models.FloatField(blank=True, null=True)
    center_resolution = models.FloatField(blank=True, null=True)
    center_distance = models.FloatField(blank=True, null=True)
    center_phase_angle = models.FloatField(blank=True, null=True)
    id = models.IntegerField(primary_key=True)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'obs_surface_geometry__rhea'


class ObsSurfaceGeometrySaturn(models.Model):
    obs_general = models.ForeignKey(ObsGeneral, models.DO_NOTHING)
    rms_obs_id = models.ForeignKey(ObsGeneral, models.DO_NOTHING, related_name='%(class)s_rms_obs_id')
    volume_id = models.CharField(max_length=11)
    instrument_id = models.CharField(max_length=9)
    planetocentric_latitude1 = models.FloatField(blank=True, null=True)
    planetocentric_latitude2 = models.FloatField(blank=True, null=True)
    planetographic_latitude1 = models.FloatField(blank=True, null=True)
    planetographic_latitude2 = models.FloatField(blank=True, null=True)
    iau_west_longitude1 = models.FloatField(blank=True, null=True)
    iau_west_longitude2 = models.FloatField(blank=True, null=True)
    iau_west_longitude = models.FloatField(blank=True, null=True)
    d_iau_west_longitude = models.FloatField(blank=True, null=True)
    solar_hour_angle1 = models.FloatField(blank=True, null=True)
    solar_hour_angle2 = models.FloatField(blank=True, null=True)
    solar_hour_angle = models.FloatField(blank=True, null=True)
    d_solar_hour_angle = models.FloatField(blank=True, null=True)
    observer_longitude1 = models.FloatField(blank=True, null=True)
    observer_longitude2 = models.FloatField(blank=True, null=True)
    observer_longitude = models.FloatField(blank=True, null=True)
    d_observer_longitude = models.FloatField(blank=True, null=True)
    finest_resolution1 = models.FloatField(blank=True, null=True)
    finest_resolution2 = models.FloatField(blank=True, null=True)
    coarsest_resolution1 = models.FloatField(blank=True, null=True)
    coarsest_resolution2 = models.FloatField(blank=True, null=True)
    range_to_body1 = models.FloatField(blank=True, null=True)
    range_to_body2 = models.FloatField(blank=True, null=True)
    phase1 = models.FloatField(blank=True, null=True)
    phase2 = models.FloatField(blank=True, null=True)
    incidence1 = models.FloatField(blank=True, null=True)
    incidence2 = models.FloatField(blank=True, null=True)
    emission1 = models.FloatField(blank=True, null=True)
    emission2 = models.FloatField(blank=True, null=True)
    sub_solar_planetocentric_latitude = models.FloatField(blank=True, null=True)
    sub_solar_planetographic_latitude = models.FloatField(blank=True, null=True)
    sub_observer_planetocentric_latitude = models.FloatField(blank=True, null=True)
    sub_observer_planetographic_latitude = models.FloatField(blank=True, null=True)
    sub_solar_iau_longitude = models.FloatField(blank=True, null=True)
    sub_observer_iau_longitude = models.FloatField(blank=True, null=True)
    center_resolution = models.FloatField(blank=True, null=True)
    center_distance = models.FloatField(blank=True, null=True)
    center_phase_angle = models.FloatField(blank=True, null=True)
    id = models.IntegerField(primary_key=True)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'obs_surface_geometry__saturn'


class ObsSurfaceGeometryTelesto(models.Model):
    obs_general = models.ForeignKey(ObsGeneral, models.DO_NOTHING)
    rms_obs_id = models.ForeignKey(ObsGeneral, models.DO_NOTHING, related_name='%(class)s_rms_obs_id')
    volume_id = models.CharField(max_length=11)
    instrument_id = models.CharField(max_length=9)
    planetocentric_latitude1 = models.FloatField(blank=True, null=True)
    planetocentric_latitude2 = models.FloatField(blank=True, null=True)
    planetographic_latitude1 = models.FloatField(blank=True, null=True)
    planetographic_latitude2 = models.FloatField(blank=True, null=True)
    iau_west_longitude1 = models.FloatField(blank=True, null=True)
    iau_west_longitude2 = models.FloatField(blank=True, null=True)
    iau_west_longitude = models.FloatField(blank=True, null=True)
    d_iau_west_longitude = models.FloatField(blank=True, null=True)
    solar_hour_angle1 = models.FloatField(blank=True, null=True)
    solar_hour_angle2 = models.FloatField(blank=True, null=True)
    solar_hour_angle = models.FloatField(blank=True, null=True)
    d_solar_hour_angle = models.FloatField(blank=True, null=True)
    observer_longitude1 = models.FloatField(blank=True, null=True)
    observer_longitude2 = models.FloatField(blank=True, null=True)
    observer_longitude = models.FloatField(blank=True, null=True)
    d_observer_longitude = models.FloatField(blank=True, null=True)
    finest_resolution1 = models.FloatField(blank=True, null=True)
    finest_resolution2 = models.FloatField(blank=True, null=True)
    coarsest_resolution1 = models.FloatField(blank=True, null=True)
    coarsest_resolution2 = models.FloatField(blank=True, null=True)
    range_to_body1 = models.FloatField(blank=True, null=True)
    range_to_body2 = models.FloatField(blank=True, null=True)
    phase1 = models.FloatField(blank=True, null=True)
    phase2 = models.FloatField(blank=True, null=True)
    incidence1 = models.FloatField(blank=True, null=True)
    incidence2 = models.FloatField(blank=True, null=True)
    emission1 = models.FloatField(blank=True, null=True)
    emission2 = models.FloatField(blank=True, null=True)
    sub_solar_planetocentric_latitude = models.FloatField(blank=True, null=True)
    sub_solar_planetographic_latitude = models.FloatField(blank=True, null=True)
    sub_observer_planetocentric_latitude = models.FloatField(blank=True, null=True)
    sub_observer_planetographic_latitude = models.FloatField(blank=True, null=True)
    sub_solar_iau_longitude = models.FloatField(blank=True, null=True)
    sub_observer_iau_longitude = models.FloatField(blank=True, null=True)
    center_resolution = models.FloatField(blank=True, null=True)
    center_distance = models.FloatField(blank=True, null=True)
    center_phase_angle = models.FloatField(blank=True, null=True)
    id = models.IntegerField(primary_key=True)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'obs_surface_geometry__telesto'


class ObsSurfaceGeometryTethys(models.Model):
    obs_general = models.ForeignKey(ObsGeneral, models.DO_NOTHING)
    rms_obs_id = models.ForeignKey(ObsGeneral, models.DO_NOTHING, related_name='%(class)s_rms_obs_id')
    volume_id = models.CharField(max_length=11)
    instrument_id = models.CharField(max_length=9)
    planetocentric_latitude1 = models.FloatField(blank=True, null=True)
    planetocentric_latitude2 = models.FloatField(blank=True, null=True)
    planetographic_latitude1 = models.FloatField(blank=True, null=True)
    planetographic_latitude2 = models.FloatField(blank=True, null=True)
    iau_west_longitude1 = models.FloatField(blank=True, null=True)
    iau_west_longitude2 = models.FloatField(blank=True, null=True)
    iau_west_longitude = models.FloatField(blank=True, null=True)
    d_iau_west_longitude = models.FloatField(blank=True, null=True)
    solar_hour_angle1 = models.FloatField(blank=True, null=True)
    solar_hour_angle2 = models.FloatField(blank=True, null=True)
    solar_hour_angle = models.FloatField(blank=True, null=True)
    d_solar_hour_angle = models.FloatField(blank=True, null=True)
    observer_longitude1 = models.FloatField(blank=True, null=True)
    observer_longitude2 = models.FloatField(blank=True, null=True)
    observer_longitude = models.FloatField(blank=True, null=True)
    d_observer_longitude = models.FloatField(blank=True, null=True)
    finest_resolution1 = models.FloatField(blank=True, null=True)
    finest_resolution2 = models.FloatField(blank=True, null=True)
    coarsest_resolution1 = models.FloatField(blank=True, null=True)
    coarsest_resolution2 = models.FloatField(blank=True, null=True)
    range_to_body1 = models.FloatField(blank=True, null=True)
    range_to_body2 = models.FloatField(blank=True, null=True)
    phase1 = models.FloatField(blank=True, null=True)
    phase2 = models.FloatField(blank=True, null=True)
    incidence1 = models.FloatField(blank=True, null=True)
    incidence2 = models.FloatField(blank=True, null=True)
    emission1 = models.FloatField(blank=True, null=True)
    emission2 = models.FloatField(blank=True, null=True)
    sub_solar_planetocentric_latitude = models.FloatField(blank=True, null=True)
    sub_solar_planetographic_latitude = models.FloatField(blank=True, null=True)
    sub_observer_planetocentric_latitude = models.FloatField(blank=True, null=True)
    sub_observer_planetographic_latitude = models.FloatField(blank=True, null=True)
    sub_solar_iau_longitude = models.FloatField(blank=True, null=True)
    sub_observer_iau_longitude = models.FloatField(blank=True, null=True)
    center_resolution = models.FloatField(blank=True, null=True)
    center_distance = models.FloatField(blank=True, null=True)
    center_phase_angle = models.FloatField(blank=True, null=True)
    id = models.IntegerField(primary_key=True)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'obs_surface_geometry__tethys'


class ObsSurfaceGeometryTitan(models.Model):
    obs_general = models.ForeignKey(ObsGeneral, models.DO_NOTHING)
    rms_obs_id = models.ForeignKey(ObsGeneral, models.DO_NOTHING, related_name='%(class)s_rms_obs_id')
    volume_id = models.CharField(max_length=11)
    instrument_id = models.CharField(max_length=9)
    planetocentric_latitude1 = models.FloatField(blank=True, null=True)
    planetocentric_latitude2 = models.FloatField(blank=True, null=True)
    planetographic_latitude1 = models.FloatField(blank=True, null=True)
    planetographic_latitude2 = models.FloatField(blank=True, null=True)
    iau_west_longitude1 = models.FloatField(blank=True, null=True)
    iau_west_longitude2 = models.FloatField(blank=True, null=True)
    iau_west_longitude = models.FloatField(blank=True, null=True)
    d_iau_west_longitude = models.FloatField(blank=True, null=True)
    solar_hour_angle1 = models.FloatField(blank=True, null=True)
    solar_hour_angle2 = models.FloatField(blank=True, null=True)
    solar_hour_angle = models.FloatField(blank=True, null=True)
    d_solar_hour_angle = models.FloatField(blank=True, null=True)
    observer_longitude1 = models.FloatField(blank=True, null=True)
    observer_longitude2 = models.FloatField(blank=True, null=True)
    observer_longitude = models.FloatField(blank=True, null=True)
    d_observer_longitude = models.FloatField(blank=True, null=True)
    finest_resolution1 = models.FloatField(blank=True, null=True)
    finest_resolution2 = models.FloatField(blank=True, null=True)
    coarsest_resolution1 = models.FloatField(blank=True, null=True)
    coarsest_resolution2 = models.FloatField(blank=True, null=True)
    range_to_body1 = models.FloatField(blank=True, null=True)
    range_to_body2 = models.FloatField(blank=True, null=True)
    phase1 = models.FloatField(blank=True, null=True)
    phase2 = models.FloatField(blank=True, null=True)
    incidence1 = models.FloatField(blank=True, null=True)
    incidence2 = models.FloatField(blank=True, null=True)
    emission1 = models.FloatField(blank=True, null=True)
    emission2 = models.FloatField(blank=True, null=True)
    sub_solar_planetocentric_latitude = models.FloatField(blank=True, null=True)
    sub_solar_planetographic_latitude = models.FloatField(blank=True, null=True)
    sub_observer_planetocentric_latitude = models.FloatField(blank=True, null=True)
    sub_observer_planetographic_latitude = models.FloatField(blank=True, null=True)
    sub_solar_iau_longitude = models.FloatField(blank=True, null=True)
    sub_observer_iau_longitude = models.FloatField(blank=True, null=True)
    center_resolution = models.FloatField(blank=True, null=True)
    center_distance = models.FloatField(blank=True, null=True)
    center_phase_angle = models.FloatField(blank=True, null=True)
    id = models.IntegerField(primary_key=True)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'obs_surface_geometry__titan'


class ObsTypeImage(models.Model):
    obs_general = models.ForeignKey(ObsGeneral, models.DO_NOTHING)
    rms_obs_id = models.ForeignKey(ObsGeneral, models.DO_NOTHING, related_name='%(class)s_rms_obs_id')
    volume_id = models.CharField(max_length=11)
    instrument_id = models.CharField(max_length=9)
    image_type_id = models.CharField(max_length=4)
    duration = models.FloatField(blank=True, null=True)
    levels = models.IntegerField(blank=True, null=True)
    greater_pixel_size = models.IntegerField(blank=True, null=True)
    lesser_pixel_size = models.IntegerField(blank=True, null=True)
    mult_obs_type_image_image_type = models.ForeignKey(MultObsTypeImageImageTypeId, models.DO_NOTHING)
    id = models.IntegerField(primary_key=True)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'obs_type_image'


class ObsWavelength(models.Model):
    obs_general = models.ForeignKey(ObsGeneral, models.DO_NOTHING)
    rms_obs_id = models.ForeignKey(ObsGeneral, models.DO_NOTHING, related_name='%(class)s_rms_obs_id')
    volume_id = models.CharField(max_length=11)
    instrument_id = models.CharField(max_length=9)
    effective_wavelength = models.FloatField(blank=True, null=True)
    wavelength1 = models.FloatField(blank=True, null=True)
    wavelength2 = models.FloatField(blank=True, null=True)
    wave_res1 = models.FloatField(blank=True, null=True)
    wave_res2 = models.FloatField(blank=True, null=True)
    wave_no1 = models.FloatField(blank=True, null=True)
    wave_no2 = models.FloatField(blank=True, null=True)
    wave_no_res1 = models.FloatField(blank=True, null=True)
    wave_no_res2 = models.FloatField(blank=True, null=True)
    spec_flag = models.CharField(max_length=3)
    spec_size = models.IntegerField(blank=True, null=True)
    polarization_type = models.CharField(max_length=8)
    mult_obs_wavelength_spec_flag = models.ForeignKey(MultObsWavelengthSpecFlag, models.DO_NOTHING, db_column='mult_obs_wavelength_spec_flag')
    mult_obs_wavelength_polarization_type = models.ForeignKey(MultObsWavelengthPolarizationType, models.DO_NOTHING, db_column='mult_obs_wavelength_polarization_type')
    id = models.IntegerField(primary_key=True)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'obs_wavelength'


class ParamInfo(models.Model):
    category_name = models.CharField(max_length=150)
    name = models.CharField(max_length=87)
    form_type = models.CharField(max_length=21, blank=True, null=True)
    display = models.CharField(max_length=1)
    display_results = models.IntegerField()
    disp_order = models.IntegerField()
    label = models.CharField(max_length=240, blank=True, null=True)
    label_results = models.CharField(max_length=240, blank=True, null=True)
    slug = models.CharField(max_length=255, blank=True, null=True)
    units = models.CharField(max_length=75, blank=True, null=True)
    intro = models.CharField(max_length=150, blank=True, null=True)
    tooltip = models.CharField(max_length=255, blank=True, null=True)
    dict_context = models.CharField(max_length=255, blank=True, null=True)
    dict_name = models.CharField(max_length=255, blank=True, null=True)
    special_query = models.CharField(max_length=15, blank=True, null=True)
    sub_heading = models.CharField(max_length=150, blank=True, null=True)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'param_info'


class Partables(models.Model):
    trigger_tab = models.CharField(max_length=200, blank=True, null=True)
    trigger_col = models.CharField(max_length=200, blank=True, null=True)
    trigger_val = models.CharField(max_length=60, blank=True, null=True)
    partable = models.CharField(max_length=200, blank=True, null=True)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'partables'


class TableNames(models.Model):
    table_name = models.CharField(max_length=60)
    label = models.CharField(max_length=60)
    display = models.CharField(max_length=1)
    disp_order = models.IntegerField()
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'table_names'


class UserCollectionsTemplate(models.Model):
    ring_obs_id = models.CharField(unique=True, max_length=40, blank=True, null=True)
    collection_meta = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'user_collections_template'


class UserSearches(models.Model):
    selections_json = models.TextField()
    selections_hash = models.CharField(max_length=32)
    string_selects = models.TextField(blank=True, null=True)
    string_selects_hash = models.CharField(max_length=32, blank=True, null=True)
    units = models.TextField(blank=True, null=True)
    units_hash = models.CharField(max_length=32, blank=True, null=True)
    qtypes = models.TextField(blank=True, null=True)
    qtypes_hash = models.CharField(max_length=32, blank=True, null=True)
    timestamp = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'user_searches'
