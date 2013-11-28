# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Image'
        db.create_table(u'images', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('ring_obs_id', self.gf('django.db.models.fields.CharField')(max_length=40)),
            ('instrument_id', self.gf('django.db.models.fields.CharField')(max_length=16, blank=True)),
            ('volume_id', self.gf('django.db.models.fields.CharField')(max_length=75, blank=True)),
            ('thumb', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('small', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('med', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('full', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
        ))
        db.send_create_signal(u'results', ['Image'])

        # Adding model 'FileSizes'
        db.create_table(u'file_sizes', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=90)),
            ('size', self.gf('django.db.models.fields.IntegerField')()),
            ('ring_obs_id', self.gf('django.db.models.fields.CharField')(max_length=40, blank=True)),
            ('volume_id', self.gf('django.db.models.fields.CharField')(max_length=75, db_column='VOLUME_ID', blank=True)),
            ('file_type', self.gf('django.db.models.fields.CharField')(max_length=25)),
            ('obs_general_no', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('PRODUCT_TYPE', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('file_name', self.gf('django.db.models.fields.CharField')(max_length=80)),
            ('base_path', self.gf('django.db.models.fields.CharField')(max_length=50)),
        ))
        db.send_create_signal(u'results', ['FileSizes'])

        # Adding model 'Files'
        db.create_table(u'files', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('ring_obs_id', self.gf('django.db.models.fields.CharField')(max_length=40, blank=True)),
            ('file_specification_name', self.gf('django.db.models.fields.CharField')(max_length=180, db_column='FILE_SPECIFICATION_NAME')),
            ('volume_id', self.gf('django.db.models.fields.CharField')(max_length=75, db_column='VOLUME_ID', blank=True)),
            ('product_type', self.gf('django.db.models.fields.CharField')(max_length=90, db_column='PRODUCT_TYPE', blank=True)),
            ('label_type', self.gf('django.db.models.fields.CharField')(max_length=24, db_column='LABEL_TYPE', blank=True)),
            ('object_type', self.gf('django.db.models.fields.CharField')(max_length=9, db_column='OBJECT_TYPE', blank=True)),
            ('file_format_type', self.gf('django.db.models.fields.CharField')(max_length=15, db_column='FILE_FORMAT_TYPE', blank=True)),
            ('interchange_format', self.gf('django.db.models.fields.CharField')(max_length=18, db_column='INTERCHANGE_FORMAT', blank=True)),
            ('instrument_id', self.gf('django.db.models.fields.CharField')(max_length=21, db_column='INSTRUMENT_ID', blank=True)),
            ('note', self.gf('django.db.models.fields.CharField')(max_length=765, blank=True)),
            ('obs_general_no', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('size', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('ascii_ext', self.gf('django.db.models.fields.CharField')(max_length=12, db_column='ASCII_ext', blank=True)),
            ('lsb_ext', self.gf('django.db.models.fields.CharField')(max_length=12, db_column='LSB_ext', blank=True)),
            ('msb_ext', self.gf('django.db.models.fields.CharField')(max_length=12, db_column='MSB_ext', blank=True)),
            ('detached_label_ext', self.gf('django.db.models.fields.CharField')(max_length=12, blank=True)),
            ('extra_files', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('mission', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal(u'results', ['Files'])


    def backwards(self, orm):
        # Deleting model 'Image'
        db.delete_table(u'images')

        # Deleting model 'FileSizes'
        db.delete_table(u'file_sizes')

        # Deleting model 'Files'
        db.delete_table(u'files')


    models = {
        u'results.files': {
            'Meta': {'object_name': 'Files', 'db_table': "u'files'"},
            'ascii_ext': ('django.db.models.fields.CharField', [], {'max_length': '12', 'db_column': "'ASCII_ext'", 'blank': 'True'}),
            'detached_label_ext': ('django.db.models.fields.CharField', [], {'max_length': '12', 'blank': 'True'}),
            'extra_files': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'file_format_type': ('django.db.models.fields.CharField', [], {'max_length': '15', 'db_column': "'FILE_FORMAT_TYPE'", 'blank': 'True'}),
            'file_specification_name': ('django.db.models.fields.CharField', [], {'max_length': '180', 'db_column': "'FILE_SPECIFICATION_NAME'"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instrument_id': ('django.db.models.fields.CharField', [], {'max_length': '21', 'db_column': "'INSTRUMENT_ID'", 'blank': 'True'}),
            'interchange_format': ('django.db.models.fields.CharField', [], {'max_length': '18', 'db_column': "'INTERCHANGE_FORMAT'", 'blank': 'True'}),
            'label_type': ('django.db.models.fields.CharField', [], {'max_length': '24', 'db_column': "'LABEL_TYPE'", 'blank': 'True'}),
            'lsb_ext': ('django.db.models.fields.CharField', [], {'max_length': '12', 'db_column': "'LSB_ext'", 'blank': 'True'}),
            'mission': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'msb_ext': ('django.db.models.fields.CharField', [], {'max_length': '12', 'db_column': "'MSB_ext'", 'blank': 'True'}),
            'note': ('django.db.models.fields.CharField', [], {'max_length': '765', 'blank': 'True'}),
            'object_type': ('django.db.models.fields.CharField', [], {'max_length': '9', 'db_column': "'OBJECT_TYPE'", 'blank': 'True'}),
            'obs_general_no': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'product_type': ('django.db.models.fields.CharField', [], {'max_length': '90', 'db_column': "'PRODUCT_TYPE'", 'blank': 'True'}),
            'ring_obs_id': ('django.db.models.fields.CharField', [], {'max_length': '40', 'blank': 'True'}),
            'size': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'volume_id': ('django.db.models.fields.CharField', [], {'max_length': '75', 'db_column': "'VOLUME_ID'", 'blank': 'True'})
        },
        u'results.filesizes': {
            'Meta': {'object_name': 'FileSizes', 'db_table': "u'file_sizes'"},
            'PRODUCT_TYPE': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'base_path': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'file_name': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            'file_type': ('django.db.models.fields.CharField', [], {'max_length': '25'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '90'}),
            'obs_general_no': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'ring_obs_id': ('django.db.models.fields.CharField', [], {'max_length': '40', 'blank': 'True'}),
            'size': ('django.db.models.fields.IntegerField', [], {}),
            'volume_id': ('django.db.models.fields.CharField', [], {'max_length': '75', 'db_column': "'VOLUME_ID'", 'blank': 'True'})
        },
        u'results.image': {
            'Meta': {'object_name': 'Image', 'db_table': "u'images'"},
            'full': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instrument_id': ('django.db.models.fields.CharField', [], {'max_length': '16', 'blank': 'True'}),
            'med': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'ring_obs_id': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'small': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'thumb': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'volume_id': ('django.db.models.fields.CharField', [], {'max_length': '75', 'blank': 'True'})
        }
    }

    complete_apps = ['results']