# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'UserCollectionsTemplate'
        db.create_table(u'user_collections_usercollectionstemplate', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('ring_obs_id', self.gf('django.db.models.fields.CharField')(max_length=40)),
            ('collection_meta', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['user_collections.UserCollectionsMeta'])),
        ))
        db.send_create_signal(u'user_collections', ['UserCollectionsTemplate'])

        # Adding model 'UserCollectionsMeta'
        db.create_table(u'user_collections_usercollectionsmeta', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('session_id', self.gf('django.db.models.fields.CharField')(max_length=32, null=True, blank=True)),
            ('permalink', self.gf('django.db.models.fields.CharField')(max_length=23, null=True, blank=True)),
            ('product_types', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('extra_products', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'user_collections', ['UserCollectionsMeta'])


    def backwards(self, orm):
        # Deleting model 'UserCollectionsTemplate'
        db.delete_table(u'user_collections_usercollectionstemplate')

        # Deleting model 'UserCollectionsMeta'
        db.delete_table(u'user_collections_usercollectionsmeta')


    models = {
        u'user_collections.usercollectionsmeta': {
            'Meta': {'object_name': 'UserCollectionsMeta'},
            'extra_products': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'permalink': ('django.db.models.fields.CharField', [], {'max_length': '23', 'null': 'True', 'blank': 'True'}),
            'product_types': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'session_id': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'})
        },
        u'user_collections.usercollectionstemplate': {
            'Meta': {'object_name': 'UserCollectionsTemplate'},
            'collection_meta': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['user_collections.UserCollectionsMeta']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ring_obs_id': ('django.db.models.fields.CharField', [], {'max_length': '40'})
        }
    }

    complete_apps = ['user_collections']