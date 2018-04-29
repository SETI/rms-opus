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


class Context(models.Model):
    name = models.CharField(primary_key=True, unique=True, max_length=75, blank=True)
    description = models.CharField(unique=True, max_length=255, blank=True)
    parent = models.CharField(max_length=75, blank=True)

    class Meta:
        managed = False
        db_table = u'contexts'
        app_label = 'dictionary'

    def __unicode__(self):
        return self.name


class Definition(models.Model):
    term = models.CharField(primary_key=True, max_length=255)
    context = models.ForeignKey("Context", on_delete=models.CASCADE, db_column='context')
    definition = models.TextField(db_column='def', help_text="Term definition")  # Field renamed because it was a Python reserved word.
    expanded = models.TextField(blank=True, null=True, help_text="Expanded definition")
    image_url = models.CharField(db_column='image_URL', max_length=255, blank=True, null=True, help_text='Image URL for the expanded definition')  # Field name made lowercase.
    more_info_url = models.CharField(db_column='more_info_URL', max_length=255, blank=True, null=True, help_text='More info URL <full definition, url to a picture or pdf>')  # Field name made lowercase.
    more_info_label = models.CharField(db_column='more_info_label', max_length=150, blank=True, null=True, help_text='Label for the more info URL page')  # Field name made lowercase.
    modified = models.IntegerField(default=0)
    import_date = models.DateField(blank=True, null=True)

    class Meta:
        managed = False
        ordering = ["term", "context"]
        db_table = u'definitions'
        app_label = 'dictionary'
        unique_together = (('term', 'context'),)

    def __str__(self):
        return self.term

    def get_absolute_url(self):
        """
        Returns the url to access a detail record for this definition.
        """
        return reverse('definition-detail', args=[str(self.id)])

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
