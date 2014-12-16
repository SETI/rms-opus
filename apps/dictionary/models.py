from django.db import models
from django.db import connection

class Term(models.Model):
    no = models.IntegerField(primary_key=True)
    term = models.CharField(unique=True, max_length=255, blank=True, editable = False)
    term_nice = models.CharField(max_length=255, blank=True)
    display = models.CharField(max_length=3, blank=True, default='Y')
    import_date = models.DateTimeField()
    class Meta:
        db_table = u'terms'
        ordering = ('term',)

    def __unicode__(self):
        return self.term


    def save(self):
        self.term = '_'.join(self.term_nice.split(' '))
        super(Term, self).save()


class Definition(models.Model):
    no = models.IntegerField(primary_key=True)
    term = models.ForeignKey("Term", db_column='term_no')
    definition = models.TextField(db_column='def') # Field renamed because it was a Python reserved word.
    source = models.ForeignKey("Source", db_column='source_no')
    context = models.ForeignKey("Context", db_column='context_no')
    class Meta:
        db_table = u'definitions'

    def __unicode__(self):
        return "definition for " + self.term.term

    def save(self):
        super(Definition, self).save()
        cursor = connection.cursor()
        cursor.execute("replace into contexts_terms select context_id,term_id from definitions");

class Context(models.Model):
    no = models.IntegerField(primary_key=True)
    name = models.CharField(unique=True, max_length=75, blank=True)
    description = models.CharField(unique=True, max_length=255, blank=True)
    parent = models.CharField(max_length=75, blank=True)
    terms = models.ManyToManyField(Term)
    class Meta:
        db_table = u'contexts'

    def __unicode__(self):
        return self.name

class Source(models.Model):
    no = models.IntegerField(primary_key=True)
    name = models.CharField(unique=True, max_length=75, blank=True)
    description = models.CharField(unique=True, max_length=225, blank=True)
    display_order = models.IntegerField(null=True, blank=True)
    class Meta:
        db_table = u'sources'
        ordering = ('display_order',)

    def __unicode__(self):
        return self.name

#---- End of Known Universe -----#

class Alias(models.Model):
    no = models.IntegerField(primary_key=True)
    term_no = models.ForeignKey("Term")
    alias = models.CharField(max_length=180)
    alias_nice = models.CharField(max_length=225)
    note = models.CharField(max_length=225, blank=True)
    context_no = models.ForeignKey("Context")
    class Meta:
        db_table = u'aliases'







class StandardValues(models.Model):
    no = models.IntegerField(primary_key=True)
    term_no = models.ForeignKey("Term")
    standard_value = models.IntegerField(null=True, blank=True)
    context_no = models.ForeignKey("Context")
    class Meta:
        db_table = u'standard_values'


class PSDDExtras(models.Model):
    no = models.IntegerField(primary_key=True)
    term_no = models.ForeignKey("Term")
    status_type = models.CharField(max_length=39, db_column='STATUS_TYPE', blank=True) # Field name made lowercase.
    general_data_type = models.CharField(max_length=150, db_column='GENERAL_DATA_TYPE', blank=True) # Field name made lowercase.
    standard_value_type = models.CharField(max_length=90, db_column='STANDARD_VALUE_TYPE', blank=True) # Field name made lowercase.
    unit_id = models.CharField(max_length=36, db_column='UNIT_ID', blank=True) # Field name made lowercase.
    minimum_length = models.IntegerField(null=True, db_column='MINIMUM_LENGTH', blank=True) # Field name made lowercase.
    maximum_length = models.IntegerField(null=True, db_column='MAXIMUM_LENGTH', blank=True) # Field name made lowercase.
    minimum = models.CharField(max_length=75, db_column='MINIMUM', blank=True) # Field name made lowercase.
    maximum = models.CharField(max_length=75, db_column='MAXIMUM', blank=True) # Field name made lowercase.
    class Meta:
        db_table = u'PSDD_extras'



"""
class RelatedTerms(models.Model):
    no = models.IntegerField(primary_key=True)
    term_no = models.ForeignKey("Term")
    related_term = models.CharField(unique=True, max_length=600, blank=True)\
    context_no = models.ForeignKey("Context")
    class Meta:
        db_table = u'related_terms'

"""


# --------------------- logs ---------------------
class LogAccess(models.Model):
    no = models.IntegerField(primary_key=True)
    datetime = models.DateTimeField()
    term_name = models.CharField(max_length=180, blank=True)
    context_no = models.CharField(max_length=75, blank=True)
    source_no = models.CharField(max_length=75, blank=True)
    referrer = models.CharField(max_length=150, blank=True)
    remote_addr = models.CharField(max_length=150, blank=True)
    remote_host = models.CharField(max_length=150, blank=True)
    class Meta:
        db_table = u'log_access'

class LogErrors(models.Model):
    no = models.IntegerField(primary_key=True)
    datetime = models.DateTimeField()
    log_msg = models.CharField(max_length=255, blank=True)
    term_name = models.CharField(max_length=180, blank=True)
    context_no = models.CharField(max_length=75, blank=True)
    source_no = models.CharField(max_length=75, blank=True)
    referrer = models.CharField(max_length=150, blank=True)
    remote_addr = models.CharField(max_length=150, blank=True)
    remote_host = models.CharField(max_length=150, blank=True)
    class Meta:
        db_table = u'log_errors'


