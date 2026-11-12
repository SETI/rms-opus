# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class ZZAuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'


class ZZAuthGroupPermissions(models.Model):
    group = models.ForeignKey(ZZAuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('ZZAuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class ZZAuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('ZZDjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class ZZAuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.IntegerField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.IntegerField()
    is_active = models.IntegerField()
    date_joined = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'auth_user'


class ZZAuthUserGroups(models.Model):
    user = models.ForeignKey(ZZAuthUser, models.DO_NOTHING)
    group = models.ForeignKey(ZZAuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class ZZAuthUserUserPermissions(models.Model):
    user = models.ForeignKey(ZZAuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(ZZAuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)


class ZZCart(models.Model):
    session_id = models.CharField(max_length=40, db_collation='ascii_general_ci')
    obs_general = models.ForeignKey(
        'ObsGeneral',
        models.DO_NOTHING,
        related_name='%(class)s_general_id',
        db_column='obs_general_id',
    )
    opus_id = models.CharField(max_length=50, db_collation='ascii_general_ci')
    recycled = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'cart'
        unique_together = (('session_id', 'obs_general'),)


class ZZContexts(models.Model):
    name = models.CharField(unique=True, max_length=50)
    description = models.CharField(max_length=100)
    parent = models.CharField(max_length=25)

    class Meta:
        managed = False
        db_table = 'contexts'


class ZZDefinitions(models.Model):
    term = models.CharField(max_length=255)
    context = models.ForeignKey(ZZContexts, models.DO_NOTHING, db_column='context')
    definition = models.TextField()

    class Meta:
        managed = False
        db_table = 'definitions'
        unique_together = (('term', 'context'),)


class ZZDjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.PositiveSmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey(
        'ZZDjangoContentType', models.DO_NOTHING, blank=True, null=True
    )
    user = models.ForeignKey(ZZAuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class ZZDjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class ZZDjangoMigrations(models.Model):
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class ZZDjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


class ZZDjangoSite(models.Model):
    domain = models.CharField(unique=True, max_length=100)
    name = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'django_site'


class Mult(models.Model):
    pk = models.CompositePrimaryKey('field_id', 'id')
    field_id = models.PositiveSmallIntegerField()
    id = models.PositiveSmallIntegerField()
    value = models.CharField(max_length=100)
    label = models.CharField(max_length=100)
    pin = models.PositiveSmallIntegerField(blank=True, null=True)
    disp_rank = models.PositiveSmallIntegerField()
    display = models.CharField(max_length=1)
    grouping = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'mult'
        unique_together = (('field_id', 'value'),)


class MultField(models.Model):
    field_id = models.PositiveSmallIntegerField(primary_key=True)
    qualified_name = models.CharField(unique=True, max_length=100)
    pinned = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'mult_field'


class MultGroup(models.Model):
    pk = models.CompositePrimaryKey('field_id', 'grouping')
    field_id = models.PositiveSmallIntegerField()
    grouping = models.CharField(max_length=100)
    group_pin = models.PositiveSmallIntegerField(blank=True, null=True)
    group_rank = models.PositiveSmallIntegerField()

    class Meta:
        managed = False
        db_table = 'mult_group'


class ObsFiles(models.Model):
    pk = models.CompositePrimaryKey('obs_general_id', 'file_number')
    obs_general = models.ForeignKey(
        'ObsGeneral',
        models.DO_NOTHING,
        related_name='%(class)s_general_id',
        db_column='obs_general_id',
    )
    file_number = models.PositiveSmallIntegerField()
    opus_id = models.CharField(max_length=50, db_collation='ascii_general_ci')
    instrument_id = models.CharField(max_length=60, db_collation='ascii_general_ci')
    version_number = models.PositiveIntegerField()
    version_name = models.CharField(max_length=16)
    category = models.CharField(max_length=64)
    sort_order = models.CharField(max_length=9)
    short_name = models.CharField(max_length=64)
    full_name = models.CharField(max_length=64)
    default_checked = models.PositiveIntegerField()
    product_order = models.PositiveIntegerField()
    logical_path = models.TextField()
    url = models.TextField()
    checksum = models.CharField(max_length=32)
    size = models.PositiveIntegerField()
    width = models.PositiveIntegerField(blank=True, null=True)
    height = models.PositiveIntegerField(blank=True, null=True)
    pds_version = models.PositiveIntegerField()

    class Meta:
        managed = False
        db_table = 'obs_files'


class ObsGeneral(models.Model):
    id = models.PositiveIntegerField(primary_key=True)
    opus_id = models.CharField(max_length=50, db_collation='ascii_general_ci')
    bundle_id = models.CharField(max_length=75, db_collation='ascii_general_ci')
    instrument_id = models.PositiveSmallIntegerField()
    mission_id = models.PositiveSmallIntegerField()
    inst_host_id = models.PositiveSmallIntegerField()
    planet_id = models.PositiveSmallIntegerField()
    target_name = models.JSONField()
    target_class = models.JSONField()
    time1 = models.FloatField(blank=True, null=True)
    time2 = models.FloatField(blank=True, null=True)
    observation_duration = models.FloatField(blank=True, null=True)
    quantity = models.PositiveSmallIntegerField()
    right_asc1 = models.FloatField(blank=True, null=True)
    right_asc2 = models.FloatField(blank=True, null=True)
    right_asc = models.FloatField(blank=True, null=True)
    d_right_asc = models.FloatField(blank=True, null=True)
    declination1 = models.FloatField(blank=True, null=True)
    declination2 = models.FloatField(blank=True, null=True)
    observation_type = models.PositiveSmallIntegerField()

    class Meta:
        managed = False
        db_table = 'obs_general'


class ObsInstrumentCocirs(models.Model):
    obs_general = models.OneToOneField(
        ObsGeneral,
        models.DO_NOTHING,
        primary_key=True,
        related_name='%(class)s_general_id',
        db_column='obs_general_id',
    )
    detector_id = models.PositiveSmallIntegerField()
    instrument_mode_blinking_flag = models.PositiveSmallIntegerField(blank=True, null=True)
    instrument_mode_even_flag = models.PositiveSmallIntegerField(blank=True, null=True)
    instrument_mode_odd_flag = models.PositiveSmallIntegerField(blank=True, null=True)
    instrument_mode_centers_flag = models.PositiveSmallIntegerField(blank=True, null=True)
    instrument_mode_pairs_flag = models.PositiveSmallIntegerField(blank=True, null=True)
    instrument_mode_all_flag = models.PositiveSmallIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'obs_instrument_cocirs'


class ObsInstrumentCoiss(models.Model):
    obs_general = models.OneToOneField(
        ObsGeneral,
        models.DO_NOTHING,
        primary_key=True,
        related_name='%(class)s_general_id',
        db_column='obs_general_id',
    )
    data_conversion_type = models.PositiveSmallIntegerField()
    compression_type = models.PositiveSmallIntegerField()
    gain_mode_id = models.PositiveSmallIntegerField()
    image_observation_type = models.PositiveSmallIntegerField()
    missing_lines = models.SmallIntegerField(blank=True, null=True)
    shutter_mode_id = models.PositiveSmallIntegerField()
    shutter_state_id = models.PositiveSmallIntegerField()
    image_number = models.IntegerField()
    instrument_mode_id = models.PositiveSmallIntegerField()
    target_desc = models.PositiveSmallIntegerField()
    combined_filter = models.PositiveSmallIntegerField()
    camera = models.PositiveSmallIntegerField()

    class Meta:
        managed = False
        db_table = 'obs_instrument_coiss'


class ObsInstrumentCouvis(models.Model):
    obs_general = models.OneToOneField(
        ObsGeneral,
        models.DO_NOTHING,
        primary_key=True,
        related_name='%(class)s_general_id',
        db_column='obs_general_id',
    )
    observation_type = models.PositiveSmallIntegerField()
    integration_duration = models.FloatField(blank=True, null=True)
    compression_type = models.PositiveSmallIntegerField()
    occultation_port_state = models.PositiveSmallIntegerField()
    slit_state = models.PositiveSmallIntegerField()
    test_pulse_state = models.PositiveSmallIntegerField(blank=True, null=True)
    dwell_time = models.PositiveSmallIntegerField(blank=True, null=True)
    channel = models.PositiveSmallIntegerField()
    band1 = models.IntegerField(blank=True, null=True)
    band2 = models.IntegerField(blank=True, null=True)
    band_bin = models.IntegerField(blank=True, null=True)
    line1 = models.IntegerField(blank=True, null=True)
    line2 = models.IntegerField(blank=True, null=True)
    line_bin = models.IntegerField(blank=True, null=True)
    samples = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'obs_instrument_couvis'


class ObsInstrumentCovims(models.Model):
    obs_general = models.OneToOneField(
        ObsGeneral,
        models.DO_NOTHING,
        primary_key=True,
        related_name='%(class)s_general_id',
        db_column='obs_general_id',
    )
    instrument_mode_id = models.PositiveSmallIntegerField()
    spectral_editing = models.PositiveSmallIntegerField()
    spectral_summing = models.PositiveSmallIntegerField()
    star_tracking = models.PositiveSmallIntegerField()
    swath_width = models.PositiveSmallIntegerField()
    swath_length = models.PositiveSmallIntegerField()
    ir_exposure = models.FloatField(blank=True, null=True)
    ir_sampling_mode_id = models.PositiveSmallIntegerField()
    vis_exposure = models.FloatField(blank=True, null=True)
    vis_sampling_mode_id = models.PositiveSmallIntegerField()
    channel = models.PositiveSmallIntegerField()

    class Meta:
        managed = False
        db_table = 'obs_instrument_covims'


class ObsInstrumentGossi(models.Model):
    obs_general = models.OneToOneField(
        ObsGeneral,
        models.DO_NOTHING,
        primary_key=True,
        related_name='%(class)s_general_id',
        db_column='obs_general_id',
    )
    observation_id = models.CharField(max_length=20, db_collation='ascii_general_ci')
    image_id = models.CharField(max_length=15, db_collation='ascii_general_ci')
    filter_name = models.PositiveSmallIntegerField()
    filter_number = models.PositiveSmallIntegerField()
    gain_mode_id = models.PositiveSmallIntegerField()
    frame_duration = models.PositiveSmallIntegerField()
    obstruction_id = models.PositiveSmallIntegerField()
    compression_type = models.PositiveSmallIntegerField()

    class Meta:
        managed = False
        db_table = 'obs_instrument_gossi'


class ObsInstrumentNhlorri(models.Model):
    obs_general = models.OneToOneField(
        ObsGeneral,
        models.DO_NOTHING,
        primary_key=True,
        related_name='%(class)s_general_id',
        db_column='obs_general_id',
    )
    instrument_compression_type = models.PositiveSmallIntegerField()
    binning_mode = models.PositiveSmallIntegerField()

    class Meta:
        managed = False
        db_table = 'obs_instrument_nhlorri'


class ObsInstrumentNhmvic(models.Model):
    obs_general = models.OneToOneField(
        ObsGeneral,
        models.DO_NOTHING,
        primary_key=True,
        related_name='%(class)s_general_id',
        db_column='obs_general_id',
    )
    instrument_compression_type = models.PositiveSmallIntegerField()

    class Meta:
        managed = False
        db_table = 'obs_instrument_nhmvic'


class ObsInstrumentVgiss(models.Model):
    obs_general = models.OneToOneField(
        ObsGeneral,
        models.DO_NOTHING,
        primary_key=True,
        related_name='%(class)s_general_id',
        db_column='obs_general_id',
    )
    image_id = models.CharField(max_length=10, db_collation='ascii_general_ci')
    scan_mode = models.PositiveSmallIntegerField()
    shutter_mode = models.PositiveSmallIntegerField()
    gain_mode = models.PositiveSmallIntegerField()
    edit_mode = models.PositiveSmallIntegerField()
    filter_name = models.PositiveSmallIntegerField()
    filter_number = models.PositiveSmallIntegerField()
    camera = models.PositiveSmallIntegerField()
    usable_lines = models.SmallIntegerField(blank=True, null=True)
    usable_samples = models.SmallIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'obs_instrument_vgiss'


class ObsMissionCassini(models.Model):
    obs_general = models.OneToOneField(
        ObsGeneral,
        models.DO_NOTHING,
        primary_key=True,
        related_name='%(class)s_general_id',
        db_column='obs_general_id',
    )
    obs_name = models.CharField(max_length=30, db_collation='ascii_general_ci')
    rev_no = models.CharField(max_length=3, blank=True, null=True)
    rev_no_int = models.IntegerField(blank=True, null=True)
    is_prime = models.PositiveSmallIntegerField()
    prime_inst_id = models.PositiveSmallIntegerField()
    spacecraft_clock_count1 = models.FloatField(blank=True, null=True)
    spacecraft_clock_count2 = models.FloatField(blank=True, null=True)
    ert1 = models.FloatField(blank=True, null=True)
    ert2 = models.FloatField(blank=True, null=True)
    cassini_target_code = models.PositiveSmallIntegerField(blank=True, null=True)
    cassini_target_name = models.PositiveSmallIntegerField(blank=True, null=True)
    activity_name = models.CharField(
        max_length=9, db_collation='ascii_general_ci', blank=True, null=True
    )
    mission_phase_name = models.PositiveSmallIntegerField(blank=True, null=True)
    sequence_id = models.CharField(
        max_length=4, db_collation='ascii_general_ci', blank=True, null=True
    )

    class Meta:
        managed = False
        db_table = 'obs_mission_cassini'


class ObsMissionGalileo(models.Model):
    obs_general = models.OneToOneField(
        ObsGeneral,
        models.DO_NOTHING,
        primary_key=True,
        related_name='%(class)s_general_id',
        db_column='obs_general_id',
    )
    orbit_number = models.PositiveSmallIntegerField(blank=True, null=True)
    spacecraft_clock_count1 = models.FloatField()
    spacecraft_clock_count2 = models.FloatField()

    class Meta:
        managed = False
        db_table = 'obs_mission_galileo'


class ObsMissionHubble(models.Model):
    obs_general = models.OneToOneField(
        ObsGeneral,
        models.DO_NOTHING,
        primary_key=True,
        related_name='%(class)s_general_id',
        db_column='obs_general_id',
    )
    stsci_group_id = models.CharField(max_length=9, db_collation='ascii_general_ci')
    hst_proposal_id = models.IntegerField()
    hst_pi_name = models.CharField(max_length=24)
    detector_id = models.PositiveSmallIntegerField()
    publication_date = models.FloatField()
    hst_target_name = models.CharField(max_length=31, db_collation='ascii_general_ci')
    fine_guidance_system_lock_type = models.PositiveSmallIntegerField()
    filter_name = models.PositiveSmallIntegerField()
    filter_type = models.PositiveSmallIntegerField()
    aperture_type = models.PositiveSmallIntegerField()
    proposed_aperture_type = models.PositiveSmallIntegerField(blank=True, null=True)
    exposure_type = models.PositiveSmallIntegerField()
    gain_mode_id = models.PositiveSmallIntegerField()
    instrument_mode_id = models.PositiveSmallIntegerField()
    pc1_flag = models.PositiveSmallIntegerField(blank=True, null=True)
    wf2_flag = models.PositiveSmallIntegerField(blank=True, null=True)
    wf3_flag = models.PositiveSmallIntegerField(blank=True, null=True)
    wf4_flag = models.PositiveSmallIntegerField(blank=True, null=True)
    targeted_detector_id = models.PositiveSmallIntegerField(blank=True, null=True)
    optical_element = models.PositiveSmallIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'obs_mission_hubble'


class ObsMissionNewHorizons(models.Model):
    obs_general = models.OneToOneField(
        ObsGeneral,
        models.DO_NOTHING,
        primary_key=True,
        related_name='%(class)s_general_id',
        db_column='obs_general_id',
    )
    spacecraft_clock_count1 = models.FloatField()
    spacecraft_clock_count2 = models.FloatField()
    mission_phase = models.PositiveSmallIntegerField()

    class Meta:
        managed = False
        db_table = 'obs_mission_new_horizons'


class ObsMissionVoyager(models.Model):
    obs_general = models.OneToOneField(
        ObsGeneral,
        models.DO_NOTHING,
        primary_key=True,
        related_name='%(class)s_general_id',
        db_column='obs_general_id',
    )
    ert = models.FloatField(blank=True, null=True)
    spacecraft_clock_count1 = models.FloatField()
    spacecraft_clock_count2 = models.FloatField()
    mission_phase_name = models.PositiveSmallIntegerField()

    class Meta:
        managed = False
        db_table = 'obs_mission_voyager'


class ObsPds(models.Model):
    obs_general = models.OneToOneField(
        ObsGeneral,
        models.DO_NOTHING,
        primary_key=True,
        related_name='%(class)s_general_id',
        db_column='obs_general_id',
    )
    opus_id = models.CharField(max_length=50, db_collation='ascii_general_ci')
    bundle_id = models.CharField(max_length=75, db_collation='ascii_general_ci')
    data_set_id = models.CharField(
        max_length=40, db_collation='ascii_general_ci', blank=True, null=True
    )
    product_id = models.CharField(
        max_length=50, db_collation='ascii_general_ci', blank=True, null=True
    )
    primary_lid = models.CharField(
        max_length=240, db_collation='ascii_general_ci', blank=True, null=True
    )
    product_creation_time = models.FloatField(blank=True, null=True)
    primary_filespec = models.CharField(max_length=240, db_collation='ascii_general_ci')
    note = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'obs_pds'


class ObsPreview(models.Model):
    obs_general = models.OneToOneField(
        ObsGeneral,
        models.DO_NOTHING,
        primary_key=True,
        related_name='%(class)s_general_id',
        db_column='obs_general_id',
    )
    preview_images = models.JSONField()

    class Meta:
        managed = False
        db_table = 'obs_preview'


class ObsProfile(models.Model):
    obs_general = models.OneToOneField(
        ObsGeneral,
        models.DO_NOTHING,
        primary_key=True,
        related_name='%(class)s_general_id',
        db_column='obs_general_id',
    )
    occ_type = models.PositiveSmallIntegerField(blank=True, null=True)
    occ_dir = models.PositiveSmallIntegerField(blank=True, null=True)
    body_occ_flag = models.PositiveSmallIntegerField(blank=True, null=True)
    temporal_sampling = models.FloatField(blank=True, null=True)
    quality_score = models.PositiveSmallIntegerField(blank=True, null=True)
    optical_depth1 = models.FloatField(blank=True, null=True)
    optical_depth2 = models.FloatField(blank=True, null=True)
    wl_band = models.PositiveSmallIntegerField(blank=True, null=True)
    source = models.PositiveSmallIntegerField(blank=True, null=True)
    host = models.PositiveSmallIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'obs_profile'


class ObsRingGeometry(models.Model):
    obs_general = models.OneToOneField(
        ObsGeneral,
        models.DO_NOTHING,
        primary_key=True,
        related_name='%(class)s_general_id',
        db_column='obs_general_id',
    )
    ring_radius1 = models.FloatField(blank=True, null=True)
    ring_radius2 = models.FloatField(blank=True, null=True)
    resolution1 = models.FloatField(blank=True, null=True)
    resolution2 = models.FloatField(blank=True, null=True)
    projected_radial_resolution1 = models.FloatField(blank=True, null=True)
    projected_radial_resolution2 = models.FloatField(blank=True, null=True)
    range_to_ring_intercept1 = models.FloatField(blank=True, null=True)
    range_to_ring_intercept2 = models.FloatField(blank=True, null=True)
    ring_center_distance1 = models.FloatField(blank=True, null=True)
    ring_center_distance2 = models.FloatField(blank=True, null=True)
    j2000_longitude1 = models.FloatField(blank=True, null=True)
    j2000_longitude2 = models.FloatField(blank=True, null=True)
    j2000_longitude = models.FloatField(blank=True, null=True)
    d_j2000_longitude = models.FloatField(blank=True, null=True)
    ascending_longitude1 = models.FloatField(blank=True, null=True)
    ascending_longitude2 = models.FloatField(blank=True, null=True)
    ascending_longitude = models.FloatField(blank=True, null=True)
    d_ascending_longitude = models.FloatField(blank=True, null=True)
    solar_hour_angle1 = models.FloatField(blank=True, null=True)
    solar_hour_angle2 = models.FloatField(blank=True, null=True)
    solar_hour_angle = models.FloatField(blank=True, null=True)
    d_solar_hour_angle = models.FloatField(blank=True, null=True)
    longitude_wrt_observer1 = models.FloatField(blank=True, null=True)
    longitude_wrt_observer2 = models.FloatField(blank=True, null=True)
    longitude_wrt_observer = models.FloatField(blank=True, null=True)
    d_longitude_wrt_observer = models.FloatField(blank=True, null=True)
    ring_azimuth_wrt_observer1 = models.FloatField(blank=True, null=True)
    ring_azimuth_wrt_observer2 = models.FloatField(blank=True, null=True)
    ring_azimuth_wrt_observer = models.FloatField(blank=True, null=True)
    d_ring_azimuth_wrt_observer = models.FloatField(blank=True, null=True)
    sub_solar_ring_j2000_long1 = models.FloatField(blank=True, null=True)
    sub_solar_ring_j2000_long2 = models.FloatField(blank=True, null=True)
    sub_solar_ring_j2000_long = models.FloatField(blank=True, null=True)
    d_sub_solar_ring_j2000_long = models.FloatField(blank=True, null=True)
    sub_solar_ring_ascending_long1 = models.FloatField(blank=True, null=True)
    sub_solar_ring_ascending_long2 = models.FloatField(blank=True, null=True)
    sub_solar_ring_ascending_long = models.FloatField(blank=True, null=True)
    d_sub_solar_ring_ascending_long = models.FloatField(blank=True, null=True)
    sub_observer_ring_j2000_long1 = models.FloatField(blank=True, null=True)
    sub_observer_ring_j2000_long2 = models.FloatField(blank=True, null=True)
    sub_observer_ring_j2000_long = models.FloatField(blank=True, null=True)
    d_sub_observer_ring_j2000_long = models.FloatField(blank=True, null=True)
    sub_observer_ring_ascending_long1 = models.FloatField(blank=True, null=True)
    sub_observer_ring_ascending_long2 = models.FloatField(blank=True, null=True)
    sub_observer_ring_ascending_long = models.FloatField(blank=True, null=True)
    d_sub_observer_ring_ascending_long = models.FloatField(blank=True, null=True)
    solar_ring_elevation1 = models.FloatField(blank=True, null=True)
    solar_ring_elevation2 = models.FloatField(blank=True, null=True)
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
    ring_center_phase1 = models.FloatField(blank=True, null=True)
    ring_center_phase2 = models.FloatField(blank=True, null=True)
    ring_center_incidence1 = models.FloatField(blank=True, null=True)
    ring_center_incidence2 = models.FloatField(blank=True, null=True)
    ring_center_emission1 = models.FloatField(blank=True, null=True)
    ring_center_emission2 = models.FloatField(blank=True, null=True)
    ring_center_north_based_incidence1 = models.FloatField(blank=True, null=True)
    ring_center_north_based_incidence2 = models.FloatField(blank=True, null=True)
    ring_center_north_based_emission1 = models.FloatField(blank=True, null=True)
    ring_center_north_based_emission2 = models.FloatField(blank=True, null=True)
    solar_ring_opening_angle1 = models.FloatField(blank=True, null=True)
    solar_ring_opening_angle2 = models.FloatField(blank=True, null=True)
    observer_ring_opening_angle1 = models.FloatField(blank=True, null=True)
    observer_ring_opening_angle2 = models.FloatField(blank=True, null=True)
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
    edge_on_ascending_longitude1 = models.FloatField(blank=True, null=True)
    edge_on_ascending_longitude2 = models.FloatField(blank=True, null=True)
    edge_on_ascending_longitude = models.FloatField(blank=True, null=True)
    d_edge_on_ascending_longitude = models.FloatField(blank=True, null=True)
    edge_on_solar_hour_angle1 = models.FloatField(blank=True, null=True)
    edge_on_solar_hour_angle2 = models.FloatField(blank=True, null=True)
    edge_on_solar_hour_angle = models.FloatField(blank=True, null=True)
    d_edge_on_solar_hour_angle = models.FloatField(blank=True, null=True)
    ring_intercept_time1 = models.FloatField(blank=True, null=True)
    ring_intercept_time2 = models.FloatField(blank=True, null=True)
    projected_long_resolution_angle1 = models.FloatField(blank=True, null=True)
    projected_long_resolution_angle2 = models.FloatField(blank=True, null=True)
    projected_long_resolution1 = models.FloatField(blank=True, null=True)
    projected_long_resolution2 = models.FloatField(blank=True, null=True)
    ring_pole_clock_angle = models.FloatField(blank=True, null=True)
    ring_pole_position_angle = models.FloatField(blank=True, null=True)
    ring_diameter_pixels = models.FloatField(blank=True, null=True)
    center_x_coordinate = models.FloatField(blank=True, null=True)
    center_y_coordinate = models.FloatField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'obs_ring_geometry'


class ObsSurfaceGeometry(models.Model):
    obs_general = models.OneToOneField(
        ObsGeneral,
        models.DO_NOTHING,
        primary_key=True,
        related_name='%(class)s_general_id',
        db_column='obs_general_id',
    )
    target_list = models.TextField(db_collation='ascii_general_ci', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'obs_surface_geometry'


class ObsSurfaceGeometryTarget(models.Model):
    pk = models.CompositePrimaryKey('target_name', 'obs_general_id')
    target_name = models.PositiveSmallIntegerField()
    obs_general = models.ForeignKey(
        ObsGeneral,
        models.DO_NOTHING,
        related_name='%(class)s_general_id',
        db_column='obs_general_id',
    )
    planetographic_latitude1 = models.FloatField(blank=True, null=True)
    planetographic_latitude2 = models.FloatField(blank=True, null=True)
    sub_solar_planetographic_latitude1 = models.FloatField(blank=True, null=True)
    sub_solar_planetographic_latitude2 = models.FloatField(blank=True, null=True)
    sub_observer_planetographic_latitude1 = models.FloatField(blank=True, null=True)
    sub_observer_planetographic_latitude2 = models.FloatField(blank=True, null=True)
    planetocentric_latitude1 = models.FloatField(blank=True, null=True)
    planetocentric_latitude2 = models.FloatField(blank=True, null=True)
    sub_solar_planetocentric_latitude1 = models.FloatField(blank=True, null=True)
    sub_solar_planetocentric_latitude2 = models.FloatField(blank=True, null=True)
    sub_observer_planetocentric_latitude1 = models.FloatField(blank=True, null=True)
    sub_observer_planetocentric_latitude2 = models.FloatField(blank=True, null=True)
    iau_west_longitude1 = models.FloatField(blank=True, null=True)
    iau_west_longitude2 = models.FloatField(blank=True, null=True)
    iau_west_longitude = models.FloatField(blank=True, null=True)
    d_iau_west_longitude = models.FloatField(blank=True, null=True)
    sub_solar_iau_west_longitude1 = models.FloatField(blank=True, null=True)
    sub_solar_iau_west_longitude2 = models.FloatField(blank=True, null=True)
    sub_solar_iau_west_longitude = models.FloatField(blank=True, null=True)
    d_sub_solar_iau_west_longitude = models.FloatField(blank=True, null=True)
    sub_observer_iau_west_longitude1 = models.FloatField(blank=True, null=True)
    sub_observer_iau_west_longitude2 = models.FloatField(blank=True, null=True)
    sub_observer_iau_west_longitude = models.FloatField(blank=True, null=True)
    d_sub_observer_iau_west_longitude = models.FloatField(blank=True, null=True)
    observer_west_longitude1 = models.FloatField(blank=True, null=True)
    observer_west_longitude2 = models.FloatField(blank=True, null=True)
    observer_west_longitude = models.FloatField(blank=True, null=True)
    d_observer_west_longitude = models.FloatField(blank=True, null=True)
    iau_east_longitude1 = models.FloatField(blank=True, null=True)
    iau_east_longitude2 = models.FloatField(blank=True, null=True)
    iau_east_longitude = models.FloatField(blank=True, null=True)
    d_iau_east_longitude = models.FloatField(blank=True, null=True)
    sub_solar_iau_east_longitude1 = models.FloatField(blank=True, null=True)
    sub_solar_iau_east_longitude2 = models.FloatField(blank=True, null=True)
    sub_solar_iau_east_longitude = models.FloatField(blank=True, null=True)
    d_sub_solar_iau_east_longitude = models.FloatField(blank=True, null=True)
    sub_observer_iau_east_longitude1 = models.FloatField(blank=True, null=True)
    sub_observer_iau_east_longitude2 = models.FloatField(blank=True, null=True)
    sub_observer_iau_east_longitude = models.FloatField(blank=True, null=True)
    d_sub_observer_iau_east_longitude = models.FloatField(blank=True, null=True)
    observer_east_longitude1 = models.FloatField(blank=True, null=True)
    observer_east_longitude2 = models.FloatField(blank=True, null=True)
    observer_east_longitude = models.FloatField(blank=True, null=True)
    d_observer_east_longitude = models.FloatField(blank=True, null=True)
    range_to_body1 = models.FloatField(blank=True, null=True)
    range_to_body2 = models.FloatField(blank=True, null=True)
    center_distance1 = models.FloatField(blank=True, null=True)
    center_distance2 = models.FloatField(blank=True, null=True)
    finest_resolution1 = models.FloatField(blank=True, null=True)
    finest_resolution2 = models.FloatField(blank=True, null=True)
    coarsest_resolution1 = models.FloatField(blank=True, null=True)
    coarsest_resolution2 = models.FloatField(blank=True, null=True)
    center_resolution1 = models.FloatField(blank=True, null=True)
    center_resolution2 = models.FloatField(blank=True, null=True)
    center_phase_angle1 = models.FloatField(blank=True, null=True)
    center_phase_angle2 = models.FloatField(blank=True, null=True)
    phase1 = models.FloatField(blank=True, null=True)
    phase2 = models.FloatField(blank=True, null=True)
    incidence1 = models.FloatField(blank=True, null=True)
    incidence2 = models.FloatField(blank=True, null=True)
    emission1 = models.FloatField(blank=True, null=True)
    emission2 = models.FloatField(blank=True, null=True)
    solar_hour_angle1 = models.FloatField(blank=True, null=True)
    solar_hour_angle2 = models.FloatField(blank=True, null=True)
    solar_hour_angle = models.FloatField(blank=True, null=True)
    d_solar_hour_angle = models.FloatField(blank=True, null=True)
    north_pole_clock_angle = models.FloatField(blank=True, null=True)
    north_pole_position_angle = models.FloatField(blank=True, null=True)
    limb_clock_angle1 = models.FloatField(blank=True, null=True)
    limb_clock_angle2 = models.FloatField(blank=True, null=True)
    limb_clock_angle = models.FloatField(blank=True, null=True)
    d_limb_clock_angle = models.FloatField(blank=True, null=True)
    limb_altitude1 = models.FloatField(blank=True, null=True)
    limb_altitude2 = models.FloatField(blank=True, null=True)
    diameter_pixels = models.FloatField(blank=True, null=True)
    center_x_coordinate = models.FloatField(blank=True, null=True)
    center_y_coordinate = models.FloatField(blank=True, null=True)
    surface_intercept_time1 = models.FloatField(blank=True, null=True)
    surface_intercept_time2 = models.FloatField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'obs_surface_geometry_target'


class ObsTypeImage(models.Model):
    obs_general = models.OneToOneField(
        ObsGeneral,
        models.DO_NOTHING,
        primary_key=True,
        related_name='%(class)s_general_id',
        db_column='obs_general_id',
    )
    image_type_id = models.PositiveSmallIntegerField(blank=True, null=True)
    duration = models.FloatField(blank=True, null=True)
    levels = models.PositiveIntegerField(blank=True, null=True)
    greater_pixel_size = models.PositiveIntegerField(blank=True, null=True)
    lesser_pixel_size = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'obs_type_image'


class ObsWavelength(models.Model):
    obs_general = models.OneToOneField(
        ObsGeneral,
        models.DO_NOTHING,
        primary_key=True,
        related_name='%(class)s_general_id',
        db_column='obs_general_id',
    )
    wavelength1 = models.FloatField(blank=True, null=True)
    wavelength2 = models.FloatField(blank=True, null=True)
    wave_res1 = models.FloatField(blank=True, null=True)
    wave_res2 = models.FloatField(blank=True, null=True)
    wave_no1 = models.FloatField(blank=True, null=True)
    wave_no2 = models.FloatField(blank=True, null=True)
    wave_no_res1 = models.FloatField(blank=True, null=True)
    wave_no_res2 = models.FloatField(blank=True, null=True)
    spec_flag = models.PositiveSmallIntegerField()
    spec_size = models.PositiveIntegerField(blank=True, null=True)
    polarization_type = models.PositiveSmallIntegerField()

    class Meta:
        managed = False
        db_table = 'obs_wavelength'


class ZZParamInfo(models.Model):
    category_name = models.CharField(max_length=150, blank=True, null=True)
    name = models.CharField(max_length=87, blank=True, null=True)
    form_type = models.CharField(max_length=100, blank=True, null=True)
    display = models.IntegerField()
    display_results = models.IntegerField()
    disp_order = models.IntegerField()
    label = models.CharField(max_length=240, blank=True, null=True)
    label_results = models.CharField(max_length=240, blank=True, null=True)
    slug = models.CharField(max_length=255, blank=True, null=True)
    old_slug = models.CharField(max_length=255, blank=True, null=True)
    referred_slug = models.CharField(max_length=255, blank=True, null=True)
    intro = models.CharField(max_length=1023, blank=True, null=True)
    tooltip = models.CharField(max_length=255, blank=True, null=True)
    dict_context = models.CharField(max_length=255, blank=True, null=True)
    dict_name = models.CharField(max_length=255, blank=True, null=True)
    dict_context_results = models.CharField(max_length=255, blank=True, null=True)
    dict_name_results = models.CharField(max_length=255, blank=True, null=True)
    sub_heading = models.CharField(max_length=150, blank=True, null=True)
    ranges = models.JSONField(blank=True, null=True)
    field_hints1 = models.CharField(max_length=255, blank=True, null=True)
    field_hints2 = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'param_info'


class Partables(models.Model):
    trigger_tab = models.CharField(max_length=200, blank=True, null=True)
    trigger_col = models.CharField(max_length=200, blank=True, null=True)
    trigger_val = models.CharField(max_length=60, blank=True, null=True)
    partable = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'partables'


class TableNames(models.Model):
    table_name = models.CharField(max_length=60)
    label = models.CharField(max_length=60)
    display = models.CharField(max_length=1)
    disp_order = models.IntegerField()
    physical_table = models.CharField(max_length=60, blank=True, null=True)
    target_name = models.PositiveSmallIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'table_names'


class UserSearches(models.Model):
    search_hash = models.BinaryField(unique=True, max_length=32)
    result_count = models.PositiveIntegerField(blank=True, null=True)
    results_built_at = models.DateTimeField(blank=True, null=True)
    last_used_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'user_searches'
