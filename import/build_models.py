"""
    This script reads the opus1 database and builds the opus2 django models

    todo:
        the surface geo tables are all the same schema, a more readable
        models.py would be to have one abstract surface_geo class and then
        all the little geo tables extend that
        https://docs.djangoproject.com/en/dev/topics/db/models/#abstract-base-classes


"""
# Set up the Django Enviroment for running as shell script
import sys
sys.path.append('/home/django/djcode/opus/')  #srvr
# from opus import settings
from django.conf import settings
from settings import CACHES, DATABASES
settings.configure(CACHES=CACHES, DATABASES=DATABASES) # include any other settings you might need

# script imports
from django.db import transaction, connection
from django.core.management import  call_command
from collections import OrderedDict
from settings import DATABASES, MULT_FIELDS

opus1 = 'Observations' # from here
opus2 = 'opus_small'   # to here

#----  shell argvs --------#
import sys

if len(sys.argv) < 2:
    print """

    Welcome to the OPUS 2 importer! This script builds OPUS 2 django models by inspecting opus 1

    This script prints statements to stdout

    1st arg is a list of volumes, with no spaces

    Like so:

    python build_models.py COISS_2060,NHJULO_1001,COCIRS_5403 > models.py

    make sure there are no spaces in your volume list!

    this script assumes we are connecting an old database named Observations
    to a new one named opus. these db names can be changed at the top of the script.

    expired: see the wiki for how to use this! http://localhost/wikka/wikka.php?wakka=DjangoPortNotes

    """
    sys.exit()



# can choose to only import a few volumes
volumes = sys.argv[1].split(',')

if volumes == ['all']:
    volumes = []  # nothing to add to the query

volumes_str = '"' + ('","').join(volumes) + '"'


# ------------ some initial defining of things ------------#

# hello mysql
cursor = connection.cursor()
cursor.execute("SET SQL_MODE = 'STRICT_ALL_TABLES'")
cursor.execute("SET foreign_key_checks = 0")

field_choices = {} # we will build a bunch of tuples that hold choices for the mult fields
mult_models = [] # mult table model holder

# field_type from Observations.forms corresponds to a Django Model field type
field_types = {
    'TIME'   : '',           # time vs str time fields?
    'GROUP'  : 'CharField',
    'RANGE'  : 'FloatField', # floats?
    'STRING' : 'CharField',
    'TARGETS': 'CharField'
}

# almost all mult tables are the same model, like so:
mult_model_core = """
    value = models.CharField(unique=True, max_length=50, blank=True, null = True)
    label = models.CharField(unique=True, max_length=50, blank=True, null = True)
    disp_order = models.IntegerField(null=True, blank=True)
    display = models.CharField(max_length=9)
    default_fade = models.CharField(max_length=9)

    def __unicode__(self):
        return self.label

    """

# exclude these field_names with these table_names found in Observations.forms
exclude = ['%movies%',"%mvf_c%",'file_sizes']



# ------------ first, copy all the Obs_ tables from Observations to opus ------------#

obs_exclude = ['obs_rg_COISS_2075', 'obs_surface_geometry_raw'] # obs-like tables to exclude
cursor.execute("use %s" % opus1)
q = "show tables like '%s'" % ('obs%')
cursor.execute(q)
obs_tables = [row[0] for row in cursor.fetchall() if row[0] not in obs_exclude]


# ------------ build model definition strings for the data tables ------------#
# for each shard start building the model definition string with the model class declaration
for tbl in obs_tables:
    model_name = ''.join(tbl.title().split('_'))
    vars()[tbl + '_model'] = "class Obs" + model_name + "(models.Model): \n"


# ------------ build model defs  ------------#

# get all the fields in the database from the old opus database Observations.forms
where_clause = " where (display = 'Y' or display_results = 'Y') "
where_clause += ' '.join(["and table_name not like %s" for t in exclude])
where_clause += " order by table_name,name "
cursor.execute("select search_form,name,type,length,form_type from " + opus1 + ".forms " + where_clause, exclude)
param_info_rows = cursor.fetchall()

# now build our list of field definitions
all_field_defs = OrderedDict() # field definitions for django models
last_table_name = ""
for row in param_info_rows:

    choices = []            # we will fill in CHOICES for django model fields, may not need these in pk columns
    fkey_field_def = ''     # for the sql queries

    table_name  = row[0]
    field_name  = row[1]
    field_type  = row[2]
    length      = row[3]
    form_type   = row[4]

    if table_name != last_table_name and table_name != 'obs_general':
        # this is beginning a new table, add the foreign key to the obs_general model
        main_fk_def = '    obs_general = models.ForeignKey(ObsGeneral, db_column="obs_general_id", null=True, blank=True)'
        all_field_defs.setdefault(table_name, []).append(main_fk_def)

    last_table_name = table_name

    # if this is a mult field, construct choices and mult field declaration
    if form_type in MULT_FIELDS:
        mult_table = 'mult_' + table_name + '_' + field_name         # name of mult table
        cursor.execute("select id,value from " + opus2 + "." + mult_table + " where display = 'Y' order by disp_order")
        choice_rows = cursor.fetchall()
        for choice_row in choice_rows:
            choices += [(choice_row[0],choice_row[1])]
        choices = tuple(choices)
        field_choices[table_name.upper() + "_" + field_name.upper() + "_CHOICES"] = choices
        mult_model_name = ''.join(mult_table.title().split('_'))
        mult_model = "class " + mult_model_name + "(models.Model):" + mult_model_core
        mult_model += "class Meta:\n"
        mult_model += "        db_table = u'" + mult_table + "'\n"

        if (mult_table in ['mult_obs_surface_geometry_target_name','mult_obs_general_target_name']) or \
            ('FILTER' in mult_table and 'FILTER_NUMBER' not in mult_table):  # order FILTER fields by label
            # some mult tables are always ordered alphabetically
            mult_model += "        ordering = ['label']\n"
        else:
            # others follow disp_order field in db table
            mult_model += "        ordering = ['disp_order']\n"

        mult_models += [mult_model]
        fkey_field_def = "    " + mult_table + ' = models.ForeignKey(' + mult_model_name + ', db_column="' + mult_table + '", db_index=False, null=True, blank=True)'

    # create the django model def
    try:
        mysql_type = field_types[form_type]
    except:
        if field_type == 'string':
            mysql_type = field_types['STRING']
        if field_type == 'real':
            mysql_type = field_types['RANGE']

    if mysql_type == 'CharField':
        model_def = 'models.CharField(max_length=' + str(length) + ', blank=True, null=True'
        if choices:
            model_def += ', choices = ' + table_name.upper() + "_" + field_name.upper() + "_CHOICES"
        model_def += ')'
    if mysql_type == 'FloatField':
        # model_def =  'models.FloatField(db_index=True, null=True, blank=True)'
        model_def =  'models.FloatField(null=True, blank=True)'

    # now we have a django model field definition
    field_def = "    " + field_name + ' = ' + model_def

    all_field_defs.setdefault(table_name, []).append(field_def)
    if fkey_field_def:
        all_field_defs.setdefault(table_name, []).append(fkey_field_def)



# ------------ cleanup ------------ #
# transaction.commit_unless_managed()  # flushes any waiting queries
cursor.execute("SET foreign_key_checks = 1")


models_dot_py =  """
# Don't add stuff here, this is a generated file.
#
# This file was generated for volumes %s
#
# generated by import/build_obs.py
# for custom models use models_custom.py
# TODO: break these intro static models out into own file

from django.db import models

class Partable(models.Model):
    trigger_tab = models.CharField(max_length=200)
    trigger_col = models.CharField(max_length=200)
    trigger_val = models.CharField(max_length=60)
    partable = models.CharField(max_length=200)
    display = models.CharField(max_length=1)
    disp_order = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = u'partables'
        unique_together = ('trigger_col', 'trigger_val','trigger_tab')
        ordering = ['disp_order']


class UserSearches(models.Model):
    # the table that describes a search that was issued by a user during a session
    selections_json = models.TextField()
    selections_hash = models.CharField(max_length=32)
    string_selects = models.TextField(null=True, blank=True)
    string_selects_hash = models.CharField(max_length=32,null=True, blank=True)
    units = models.TextField(null=True, blank=True)
    units_hash = models.CharField(max_length=32,null=True, blank=True)
    qtypes = models.TextField(null=True, blank=True)
    qtypes_hash = models.CharField(max_length=32,null=True, blank=True)
    timestamp = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = u'user_searches'
        unique_together = ('selections_hash', 'string_selects_hash','units_hash','qtypes_hash')

class TableName(models.Model):
    table_name = models.CharField(max_length=60)
    label = models.CharField(max_length=60)
    display = models.CharField(max_length=1)
    disp_order = models.IntegerField(null=True, blank=True)
    mission_id = models.CharField(max_length=2)
    alert = models.TextField()

    class Meta:
        db_table = u'table_names'
        ordering = ['disp_order']

""".format(volumes_str)

models_dot_py += "\n\n".join(mult_models)
models_dot_py += "\n"
models_dot_py += "\n"


# print all the mult field choices
models_dot_py += "# choices for all the mult fields in all data tables \n"
for choice_name,choices in field_choices.items():
    models_dot_py += choice_name + ' = ' + str(choices) + "\n"

models_dot_py += "\n"

# print all data classes
models_dot_py += "# Data Models: \n"
for table in all_field_defs:
    model_name = ''.join(table.title().split('_'))
    models_dot_py +=  "class %s(models.Model): \n" % model_name
    for field_def in all_field_defs[table]:
        models_dot_py += "%s \n" % field_def
    models_dot_py += "    ring_obs_id = models.CharField(max_length=40, blank=True, null=True) \n"

    meta_stmt = """
    class Meta:
        db_table = '{0}'

    def __unicode__(self):
        return self.ring_obs_id

    """.format(table)
    models_dot_py += meta_stmt
    models_dot_py += "\n"  # returns carriage to front of line


print models_dot_py
