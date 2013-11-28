# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Group'
        db.create_table(u'groups', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=150, blank=True)),
            ('display', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('disp_order', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('alert', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'paraminfo', ['Group'])

        # Adding model 'Category'
        db.create_table(u'categories', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=150, blank=True)),
            ('label', self.gf('django.db.models.fields.CharField')(max_length=108, blank=True)),
            ('display', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('disp_order', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('alert', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['paraminfo.Group'], null=True, blank=True)),
        ))
        db.send_create_signal(u'paraminfo', ['Category'])

        # Adding model 'ParamInfo'
        db.create_table(u'param_info', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('category', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['paraminfo.Category'], null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=87)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=18, blank=True)),
            ('length', self.gf('django.db.models.fields.IntegerField')()),
            ('slug', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('post_length', self.gf('django.db.models.fields.IntegerField')()),
            ('form_type', self.gf('django.db.models.fields.CharField')(max_length=21, null=True, blank=True)),
            ('display', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('rank', self.gf('django.db.models.fields.CharField')(max_length=48, null=True, blank=True)),
            ('disp_order', self.gf('django.db.models.fields.IntegerField')()),
            ('label', self.gf('django.db.models.fields.CharField')(max_length=240, null=True, blank=True)),
            ('intro', self.gf('django.db.models.fields.CharField')(max_length=150, null=True, blank=True)),
            ('category_name', self.gf('django.db.models.fields.CharField')(max_length=150, blank=True)),
            ('display_results', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('units', self.gf('django.db.models.fields.CharField')(max_length=75, null=True, blank=True)),
            ('tooltip', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('dict_context', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('dict_name', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('checkbox_group_col_count', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('special_query', self.gf('django.db.models.fields.CharField')(max_length=15, null=True, blank=True)),
            ('label_results', self.gf('django.db.models.fields.CharField')(max_length=240, null=True, blank=True)),
            ('onclick', self.gf('django.db.models.fields.CharField')(max_length=75, null=True, blank=True)),
            ('dict_more_info_context', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('dict_more_info_name', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('search_form', self.gf('django.db.models.fields.CharField')(max_length=63, null=True, blank=True)),
            ('mission', self.gf('django.db.models.fields.CharField')(max_length=15, null=True, blank=True)),
            ('instrument', self.gf('django.db.models.fields.CharField')(max_length=15, null=True, blank=True)),
            ('sub_heading', self.gf('django.db.models.fields.CharField')(max_length=150, null=True, blank=True)),
        ))
        db.send_create_signal(u'paraminfo', ['ParamInfo'])


    def backwards(self, orm):
        # Deleting model 'Group'
        db.delete_table(u'groups')

        # Deleting model 'Category'
        db.delete_table(u'categories')

        # Deleting model 'ParamInfo'
        db.delete_table(u'param_info')


    models = {
        u'paraminfo.category': {
            'Meta': {'ordering': "('disp_order',)", 'object_name': 'Category', 'db_table': "u'categories'"},
            'alert': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'disp_order': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'display': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['paraminfo.Group']", 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '108', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '150', 'blank': 'True'})
        },
        u'paraminfo.group': {
            'Meta': {'ordering': "('disp_order',)", 'object_name': 'Group', 'db_table': "u'groups'"},
            'alert': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'disp_order': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'display': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '150', 'blank': 'True'})
        },
        u'paraminfo.paraminfo': {
            'Meta': {'ordering': "('disp_order',)", 'object_name': 'ParamInfo', 'db_table': "u'param_info'"},
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['paraminfo.Category']", 'null': 'True', 'blank': 'True'}),
            'category_name': ('django.db.models.fields.CharField', [], {'max_length': '150', 'blank': 'True'}),
            'checkbox_group_col_count': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'dict_context': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'dict_more_info_context': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'dict_more_info_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'dict_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'disp_order': ('django.db.models.fields.IntegerField', [], {}),
            'display': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'display_results': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'form_type': ('django.db.models.fields.CharField', [], {'max_length': '21', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instrument': ('django.db.models.fields.CharField', [], {'max_length': '15', 'null': 'True', 'blank': 'True'}),
            'intro': ('django.db.models.fields.CharField', [], {'max_length': '150', 'null': 'True', 'blank': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '240', 'null': 'True', 'blank': 'True'}),
            'label_results': ('django.db.models.fields.CharField', [], {'max_length': '240', 'null': 'True', 'blank': 'True'}),
            'length': ('django.db.models.fields.IntegerField', [], {}),
            'mission': ('django.db.models.fields.CharField', [], {'max_length': '15', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '87'}),
            'onclick': ('django.db.models.fields.CharField', [], {'max_length': '75', 'null': 'True', 'blank': 'True'}),
            'post_length': ('django.db.models.fields.IntegerField', [], {}),
            'rank': ('django.db.models.fields.CharField', [], {'max_length': '48', 'null': 'True', 'blank': 'True'}),
            'search_form': ('django.db.models.fields.CharField', [], {'max_length': '63', 'null': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'special_query': ('django.db.models.fields.CharField', [], {'max_length': '15', 'null': 'True', 'blank': 'True'}),
            'sub_heading': ('django.db.models.fields.CharField', [], {'max_length': '150', 'null': 'True', 'blank': 'True'}),
            'tooltip': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '18', 'blank': 'True'}),
            'units': ('django.db.models.fields.CharField', [], {'max_length': '75', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['paraminfo']