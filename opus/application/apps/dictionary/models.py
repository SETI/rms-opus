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
    subterm = models.CharField(db_column='subterm', max_length=255, blank=True, null=True, help_text='Text for the subterm hover text')
    modified = models.IntegerField(default=0)
    import_date = models.DateField(blank=True, null=True)

    class Meta:
        managed = False
        ordering = ["term", "context"]
        db_table = u'definitions'
        app_label = 'dictionary'
        unique_together = (('term', 'context', 'subterm'),)

    def __str__(self):
        return self.term

    def get_absolute_url(self):
        """
        Returns the url to access a detail record for this definition.
        """
        return reverse('definition-detail', args=[str(self.id)])
