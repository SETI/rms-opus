from django.db import models
from paraminfo.models import *

class Image(models.Model):
    opus_id = models.CharField(max_length=40)
    instrument_id = models.CharField(max_length=16, blank=True)
    volume_id = models.CharField(max_length=75, blank=True) # Field name made lo$
    thumb = models.CharField(max_length=255, blank=True)
    small = models.CharField(max_length=255, blank=True)
    med = models.CharField(max_length=255, blank=True)
    full = models.CharField(max_length=255, blank=True)
    size_thumb = models.IntegerField()
    size_small = models.IntegerField()
    size_med = models.IntegerField()
    size_full = models.IntegerField()
    # opus1_opus_id = models.CharField(max_length=40)

    class Meta:
        db_table = u'images'

    def __unicode__(self):
        return self.opus_id

class FileSizes(models.Model):
    name = models.CharField(max_length=90)
    size = models.IntegerField()
    opus_id = models.CharField(max_length=40, blank=True)
    volume_id = models.CharField(max_length=75, db_column='VOLUME_ID', blank=True) # Field name made lo$
    file_type = models.CharField(max_length=25)
    obs_general_no = models.IntegerField(null=True,blank=True)
    PRODUCT_TYPE = models.CharField(max_length=30)
    file_name = models.CharField(max_length=80)
    base_path = models.CharField(max_length=50)

    class Meta:
        db_table = u'file_sizes'


    def __unicode__(self):
        return self.name

class Files(models.Model):
    opus_id = models.CharField(max_length=40, blank=True)
    file_specification_name = models.CharField(max_length=180, db_column='FILE_SPECIFICATION_NAME') # F$
    volume_id = models.CharField(max_length=75, db_column='VOLUME_ID', blank=True) # Field name made lo$
    product_type = models.CharField(max_length=90, db_column='PRODUCT_TYPE', blank=True) # Field name m$
    label_type = models.CharField(max_length=24, db_column='LABEL_TYPE', blank=True) # Field name made $
    object_type = models.CharField(max_length=9, db_column='OBJECT_TYPE', blank=True) # Field name made$
    file_format_type = models.CharField(max_length=15, db_column='FILE_FORMAT_TYPE', blank=True) # Fiel$
    interchange_format = models.CharField(max_length=18, db_column='INTERCHANGE_FORMAT', blank=True) # $
    instrument_id = models.CharField(max_length=21, db_column='INSTRUMENT_ID', blank=True) # Field name$
    note = models.CharField(max_length=765, blank=True)
    obs_general_no = models.IntegerField(null=True, blank=True)
    size = models.IntegerField(null=True, blank=True)
    ascii_ext = models.CharField(max_length=12, db_column='ASCII_ext', blank=True) # Field name made lo$
    lsb_ext = models.CharField(max_length=12, db_column='LSB_ext', blank=True) # Field name made lowerc$
    msb_ext = models.CharField(max_length=12, db_column='MSB_ext', blank=True) # Field name made lowerc$
    detached_label_ext = models.CharField(max_length=12, blank=True)
    extra_files = models.TextField(blank=True)
    base_path = models.CharField(max_length=60)
    mission_id = models.TextField(blank=True)

    class Meta:
        db_table = u'files'

    def __unicode__(self):
        return self.opus_id
