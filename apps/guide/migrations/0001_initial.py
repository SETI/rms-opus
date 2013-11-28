# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Resource'
        db.create_table(u'guide_resource', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=70)),
            ('desc', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('display', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('disp_order', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['guide.Group'])),
        ))
        db.send_create_signal(u'guide', ['Resource'])

        # Adding model 'Group'
        db.create_table(u'guide_group', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=150, blank=True)),
            ('desc', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('disp_order', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'guide', ['Group'])

        # Adding model 'KeyValue'
        db.create_table(u'guide_keyvalue', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('key', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('disp_order', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('display', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('resource', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['guide.Resource'])),
        ))
        db.send_create_signal(u'guide', ['KeyValue'])

        # Adding model 'Example'
        db.create_table(u'guide_example', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('intro', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('link', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('display', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('disp_order', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('resource', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['guide.Resource'])),
        ))
        db.send_create_signal(u'guide', ['Example'])


    def backwards(self, orm):
        # Deleting model 'Resource'
        db.delete_table(u'guide_resource')

        # Deleting model 'Group'
        db.delete_table(u'guide_group')

        # Deleting model 'KeyValue'
        db.delete_table(u'guide_keyvalue')

        # Deleting model 'Example'
        db.delete_table(u'guide_example')


    models = {
        u'guide.example': {
            'Meta': {'ordering': "['disp_order']", 'object_name': 'Example'},
            'disp_order': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'display': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'intro': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'link': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'resource': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['guide.Resource']"})
        },
        u'guide.group': {
            'Meta': {'ordering': "['disp_order']", 'object_name': 'Group'},
            'desc': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'disp_order': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '150', 'blank': 'True'})
        },
        u'guide.keyvalue': {
            'Meta': {'ordering': "['disp_order']", 'object_name': 'KeyValue'},
            'disp_order': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'display': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'resource': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['guide.Resource']"}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'guide.resource': {
            'Meta': {'ordering': "['disp_order']", 'object_name': 'Resource'},
            'desc': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'disp_order': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'display': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['guide.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '70'})
        }
    }

    complete_apps = ['guide']