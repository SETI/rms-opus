# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey has `on_delete` set to the desired behavior.
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from __future__ import unicode_literals

from django.db import models


class Alias(models.Model):
    no = models.AutoField(primary_key=True)
    term_no = models.ForeignKey("Term")
    alias = models.CharField(max_length=180)
    alias_nice = models.CharField(max_length=225)
    note = models.CharField(max_length=225, blank=True)
    context_no = models.ForeignKey("Context")

    class Meta:
        managed = False
        db_table = 'aliases'
        app_label = 'dictionary'


class Context(models.Model):
    no = models.AutoField(primary_key=True)
    name = models.CharField(unique=True, max_length=75, blank=True)
    description = models.CharField(unique=True, max_length=255, blank=True)
    parent = models.CharField(max_length=75, blank=True)

    class Meta:
        managed = False
        db_table = u'contexts'
        app_label = 'dictionary'

    def __unicode__(self):
        return self.name


class ContextsTerms(models.Model):
    context_no = models.IntegerField(blank=True, null=True)
    term_no = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'contexts_terms'
        app_label = 'dictionary'
        unique_together = (('context_no', 'term_no'),)


class Definition(models.Model):
    no = models.IntegerField(primary_key=True)
    term = models.ForeignKey("Term", db_column='term_no')
    definition = models.TextField(db_column='def') # Field renamed because it was a Python reserved word.
    source = models.ForeignKey("Source", db_column='source_no')
    context = models.ForeignKey("Context", db_column='context_no')

    class Meta:
        db_table = u'definitions'
        app_label = 'dictionary'

    def __unicode__(self):
        return "definition for " + self.term.term

class LogAccess(models.Model):
    no = models.AutoField(primary_key=True)
    datetime = models.DateTimeField()
    term_name = models.CharField(max_length=60, blank=True, null=True)
    context_no = models.CharField(max_length=25, blank=True, null=True)
    source_no = models.CharField(max_length=25, blank=True, null=True)
    referrer = models.CharField(max_length=50, blank=True, null=True)
    remote_addr = models.CharField(max_length=50, blank=True, null=True)
    remote_host = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'log_access'
        app_label = 'dictionary'

class LogErrors(models.Model):
    no = models.AutoField(primary_key=True)
    datetime = models.DateTimeField()
    log_msg = models.CharField(max_length=255, blank=True, null=True)
    term_name = models.CharField(max_length=60, blank=True, null=True)
    context_no = models.CharField(max_length=25, blank=True, null=True)
    source_no = models.CharField(max_length=25, blank=True, null=True)
    referrer = models.CharField(max_length=50, blank=True, null=True)
    remote_addr = models.CharField(max_length=50, blank=True, null=True)
    remote_host = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'log_errors'


class PsddExtras(models.Model):
    no = models.AutoField(primary_key=True)
    term_no = models.IntegerField()
    status_type = models.CharField(db_column='STATUS_TYPE', max_length=13, blank=True, null=True)  # Field name made lowercase.
    general_data_type = models.CharField(db_column='GENERAL_DATA_TYPE', max_length=50, blank=True, null=True)  # Field name made lowercase.
    standard_value_type = models.CharField(db_column='STANDARD_VALUE_TYPE', max_length=30, blank=True, null=True)  # Field name made lowercase.
    unit_id = models.CharField(db_column='UNIT_ID', max_length=12, blank=True, null=True)  # Field name made lowercase.
    minimum_length = models.IntegerField(db_column='MINIMUM_LENGTH', blank=True, null=True)  # Field name made lowercase.
    maximum_length = models.IntegerField(db_column='MAXIMUM_LENGTH', blank=True, null=True)  # Field name made lowercase.
    minimum = models.CharField(db_column='MINIMUM', max_length=25, blank=True, null=True)  # Field name made lowercase.
    maximum = models.CharField(db_column='MAXIMUM', max_length=25, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'psdd_extras'
        app_label = 'dictionary'


class RelatedTerms(models.Model):
    no = models.AutoField(primary_key=True)
    term_no = models.IntegerField(blank=True, null=True)
    related_term = models.IntegerField(blank=True, null=True)
    context_no = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'related_terms'
        unique_together = (('term_no', 'related_term', 'context_no'),)
        app_label = 'dictionary'

class Source(models.Model):
    no = models.AutoField(primary_key=True)
    name = models.CharField(unique=True, max_length=25, blank=True, null=True)
    description = models.CharField(unique=True, max_length=75, blank=True, null=True)
    display_order = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'sources'
        app_label = 'dictionary'


class StandardValues(models.Model):
    term_no = models.IntegerField(blank=True, null=True)
    standard_value = models.IntegerField(blank=True, null=True)
    context_no = models.IntegerField(blank=True, null=True)
    no = models.AutoField(primary_key=True)

    class Meta:
        managed = False
        db_table = 'standard_values'
        app_label = 'dictionary'


class Term(models.Model):
    no = models.AutoField(primary_key=True)
    term = models.CharField(unique=True, max_length=200, blank=True, null=True)
    term_nice = models.CharField(max_length=110, blank=True, null=True)
    display = models.CharField(max_length=1, blank=True, null=True)
    import_date = models.DateTimeField()

    class Meta:
        db_table = 'terms'
        ordering = ('term',)
        app_label = 'dictionary'

    def __unicode__(self):
        return self.term


    def save(self):
        self.term = '_'.join(self.term_nice.split(' '))
        super(Term, self).save()
