# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey has `on_delete` set to the desired behavior.
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from __future__ import unicode_literals

from django.db.models import F, Func, Value
from django.db import models
from django.contrib import admin


class Contexts(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(unique=True, max_length=25)
    description = models.CharField(max_length=100)
    parent = models.CharField(max_length=25)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'contexts'


class Definitions(models.Model):
    id = models.IntegerField(primary_key=True)
    term = models.CharField(max_length=255)
    context = models.ForeignKey(Contexts, models.DO_NOTHING, related_name='%(class)s_name', db_column='context', to_field='name')
    definition = models.TextField()
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'definitions'
        unique_together = (('term', 'context'),)
