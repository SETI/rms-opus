# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'GroupingTargetName'
        db.create_table(u'grouping_target_name', (
            ('id', self.gf('django.db.models.fields.IntegerField')(primary_key=True)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=50, unique=True, null=True, blank=True)),
            ('label', self.gf('django.db.models.fields.CharField')(max_length=50, unique=True, null=True, blank=True)),
            ('disp_order', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('display', self.gf('django.db.models.fields.CharField')(max_length=9)),
            ('default_fade', self.gf('django.db.models.fields.CharField')(max_length=9)),
        ))
        db.send_create_signal(u'metadata', ['GroupingTargetName'])


    def backwards(self, orm):
        # Deleting model 'GroupingTargetName'
        db.delete_table(u'grouping_target_name')


    models = {
        u'metadata.groupingtargetname': {
            'Meta': {'object_name': 'GroupingTargetName', 'db_table': "u'grouping_target_name'"},
            'default_fade': ('django.db.models.fields.CharField', [], {'max_length': '9'}),
            'disp_order': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'display': ('django.db.models.fields.CharField', [], {'max_length': '9'}),
            'id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '50', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '50', 'unique': 'True', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['metadata']