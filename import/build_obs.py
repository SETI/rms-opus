#!/usr/bin/env python
####################################################################################################
#
#   Has 2 uses:
#
#   prints all search and param_info models by reading OPUS 1 database (named Observations)
#
#   unicorns be found here
#
#   - or -
#
#   prints all sql needed to get the data from OPUS 1 (Observations db) to OPUS 2 (opus db)
#
#   used to create models.py or import.sql
#
#
#   prints to stdout
#
#
#####################################################################################################

opus1 = 'Observations' # from here
opus2 = 'opus'         # to here

#----  shell argvs --------#
import sys

if len(sys.argv) < 2:
    print """

    Welcome to the OPUS 2 importer! This script transfers data from OPUS1 to OPUS2.

    This script prints statements to stdout

    1st arg is what want to make: either 'models' or 'sql'
    2nd arumnet is a list of volumes, with no spaces

    Like so:

    python build_obs.py models COISS_2060,NHJULO_1001,COCIRS_5403 > models.py

    make sure there are no spaces in your volume list!

    this script assumes we are connecting an old database named Observations
    to a new one named opus

    see the wiki for how to use this! http://localhost/wikka/wikka.php?wakka=DjangoPortNotes

    """
    sys.exit()

to_print = sys.argv[1]

# can choose to only import a few volumes
try:
    volumes = sys.argv[2].split(',')
except:
    print "please specify volume list or 'all' as 2nd arg"
    sys.exit()

# params_cats_file = '/users/lballard/projects/opus/import/params_cats.json'

# Set up the Django Enviroment for running as shell script
import sys
sys.path.append('/users/lballard/projects/')
sys.path.append('/users/lballard/projects/opus/')
sys.path.append('/home/lballard/')
sys.path.append('/home/lballard/opus/')
from opus import settings
from django.core.management import setup_environ
setup_environ(settings)

# script imports
from django.db import connection
from django.core.management import call_command
from django.db.models import get_model
import settings

# hello mysql
cursor = connection.cursor()



#------------------------ a few data transformations ----------------------------------------#

# abbreviations for all data tables in OPUS 1:
abbrevs = {
    'obs_instrument_COCIRS':'COCIRS',
    'obs_instrument_COISS':'COISS',
    'obs_instrument_COVIMS':'COVIMS',
    'obs_instrument_COVIMS':'COUVIS',
    'obs_instrument_GOSSI':'GOSSI',
    'obs_instrument_NHJULO':'NHJULO',
    'obs_instrument_VGISS':'VGISS',
    'obs_mission_cassini':'CO',
    'obs_mission_galileo':'GO',
    'obs_mission_voyager':'VG',
    'obs_mission_new_horizons':'NH',
}

mission_abbrevs = ['CO','GO','VG','NH']

# we are building a model called Observation as well as a number of models for sharding
# key of this data struct = name of shard table ('Obs_' prefix will be added)
# 'previxes' are a list of abbrevs, tables associated with abbrevs are what gets imported into the shard
# 'clause' is the query constraint for that shard table
shards = {
    'CO':{         # Cassini Mission
        'prefixes':['CO','COISS','COCIRS','COVIMS'],
        'clause':"mission_id = 'CO'",
        'mission':'CO'
        },
    'CO_COISS': {   # Cassini ISS
        'prefixes':['CO','COISS'],
        'clause':"mission_id = 'CO' and instrument_id = 'COISS'",
        'mission':'CO'
        },
    'CO_COVIMS': {   # Cassini Vims
        'prefixes':['CO','COVIMS'],
        'clause':"mission_id = 'CO' and instrument_id = 'COVIMS'",
        'mission':'CO'
        },
    'CO_COCIRS': {   # Cassini CIRS
        'prefixes':['CO','COCIRS'],
        'clause':"mission_id = 'CO' and instrument_id = 'COCIRS'",
        'mission':'CO'
        },
    'VG': {         # Voyager Mission
        'prefixes':['VG','VGISS'],
        'clause':"mission_id = 'VG'",
        'mission':'VG'
        },
    'VG_VGISS': {    # Voyager ISS
        'prefixes':['VG','VGISS'],
        'clause':"mission_id = 'VG' and instrument_id = 'VGISS'",
        'mission':'VG'
        },
    'GO': {          # Galileo Mission
        'prefixes':['GO'],
        'clause':"mission_id = 'GO'",
        'mission':'GO'
        },
    'GO_GOSSI': {    # Galileo SSI
        'prefixes':['GO','GOSSI'],
        'clause':"mission_id = 'CO' and instrument_id = 'GOSSI'",
        'mission':'GO'
        },
    'NH': {     # New Horizons Mission
        'prefixes':['NH'],
        'clause':"mission_id = 'NH'" ,
        'mission':'NH'
        },
    'NH_NHJULO':{ # New Horizons JULO
        'prefixes':['NH','NHJULO'],
        'clause':"mission_id = 'NH' and instrument_id = 'NHJULO'" ,
        'mission':'NH'
        }
}

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
exclude = ('%movies%',"%mvf_c%",'file_sizes','obs_surface_geometry__%')




#------------------------ defs ----------------------------------------

# takes field_name from OPUS1 returns a unique field name for OPUS2
# table name is table_name field of forms table in opus1
# field_names is the set of already created field_names (huh?)
# abbrevs provides accronym tags denoting mission and instrument to be appended onto field_name
def getFieldName(field_name,table_name,field_names,abbrevs):
    """
    guarantees unique field name with respect to field_names
    if this causes too much recursion see the exception below
    """
    abbrev = ''
    if table_name in abbrevs:
        abbrev = abbrevs[table_name]
        field_name = abbrev + '_' + field_name

    field_name = field_name[0:63]  # max length of myisam column names is 64 chars

    if field_name in field_names:
          # use this instead if this causes too much recusion then there is a problem.
          # it means that this field has no abbreviation and also is same name as another field
          # #### this shouldn't happen ####
          # and inspect the elements returned
          # field_name = 'wtf_'+name
          if abbrev:
              field_name = abbrev + '_' + field_name
          if table_name == 'obs_surface_geometry':
              field_name = 'surface_' + field_name
          return getFieldName(field_name,table_name,field_names,abbrevs)
    else:
       return field_name

def getSlug(field_name,table_name,abbrevs):
    if table_name in abbrevs:
        field_split = field_name.split('_')
        return ''.join(field_split[0:1]) + '-' + ''.join(field_split[1:len(field_split)]).lower()
    else:
        return ''.join(field_name.split('_')).lower()




#------------------------body----------------------------------------#

field_names     = [] # we need unique field names so keeping track with this
field_choices   = {} # we will build a bunch of tuples that hold choices for the mult fields
data_queries    = {} # queries that move the data to the new model
mult_models     = [] # mult table model holder
mult_queries    = [] # queries that update the mult tables
mult_field_data = [] # queries that transfer data from opus1 mult fields to opus2 mult fields

# start the model definition strings
# first start the string that holds the main Observations model with the Observations class declaration:
Obs_model = "class Observations(models.Model): \n"

# then the shard madels
# for each shard start building the model definition string with the model class declaration
for shard in shards:
    model_name = ''.join(shard.title().split('_'))
    vars()['Obs' + shard + '_model'] = "class Obs" + model_name + "(models.Model): \n" + '    """ ** All other models that begin with "Obs" are shards of this table ** """ ' + "\n"


# get all the fields in the database from the old opus database Observations.forms
where_clause = " where (display = 'Y' or display_results = 'Y') "
where_clause += ' '.join(["and table_name not like %s" for t in exclude])
where_clause += " order by table_name,name "
# cursor.execute("select table_name,name,type,length,form_type from " + opus1 + ".forms " + where_clause, exclude)
cursor.execute("select search_form,name,type,length,form_type from " + opus1 + ".forms " + where_clause, exclude)
rows = cursor.fetchall()

# loop thru all fields in the old opus database
for row in rows:

    choices = []            # we will fill in CHOICES for django model fields, may not need these in pk columns
    fkey_field_def = ''     # for the sql queries

    table_name  = row[0]
    field_name  = row[1]
    field_type  = row[2]
    length      = row[3]
    form_type   = row[4]

    abbrev = ''
    if table_name in abbrevs:
        abbrev = abbrevs[table_name]

    new_field_name = getFieldName(field_name,table_name,field_names,abbrevs)
    field_names += [new_field_name]

    # now we have enough info for moving data from one database to the other
    try:    data_queries[table_name] += [{'obs':field_name, 'opus':new_field_name, 'form_type':form_type}]
    except: data_queries[table_name]  = [{'obs':field_name, 'opus':new_field_name, 'form_type':form_type}]

    # if this is a mult field construct choices and mult model declaration
    if form_type in settings.MULT_FIELDS:
        mult_table = 'mult_' + table_name + '_' + field_name         # name of mult table in opus1
        cursor.execute("select no,label from " + opus1 + "." + mult_table + " where display = 'Y'")
        choice_rows = cursor.fetchall()
        for choice_row in choice_rows:
            choices += [(choice_row[0],choice_row[1])]
        choices = tuple(choices)
        field_choices[new_field_name + "_CHOICES"] = choices
        mult_model_name = "Mult" + ''.join(new_field_name.title().split('_'))
        mult_model = "class " + mult_model_name + "(models.Model):" + mult_model_core
        mult_model += "class Meta:\n"
        mult_model += "        db_table = u'mult_" + new_field_name + "'\n"
        mult_models += [mult_model]
        fkey_field_def = "    mult_" + new_field_name + '=models.ForeignKey("' + mult_model_name + '", db_index=False, null=True, blank=True) \n'
        mult_queries += ["insert into opus.mult_" + new_field_name + " (id,value,label,disp_order,display,default_fade) select * from " + opus1 + "." + mult_table]
        mult_field_data += ["update opus.observations, opus.mult_" + new_field_name + \
                           " set opus.observations.mult_" + new_field_name + "_id = opus.mult_" + new_field_name + ".id" + \
                           " where opus.observations." + new_field_name + " = opus.mult_" + new_field_name + ".value;"]

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
            model_def += ', choices = ' + new_field_name + '_CHOICES';
        model_def += ')'
    if mysql_type == 'FloatField':
        # model_def =  'models.FloatField(db_index=True, null=True, blank=True)'
        model_def =  'models.FloatField(null=True, blank=True)'


    # now we have a django model field definition
    field_def = "    " + field_names[len(field_names)-1] + ' = ' + model_def + "\n"

    # now add the field definitions to the models
    Obs_model += field_def + fkey_field_def

    # loop through all the shard tables
    for shard,shard_abbrevs in shards.items():
        # we only want to add the field def to this shard model if it is a global field (no abbrev)
        # or if the abbrevs match those defined in shards
        if not abbrev or abbrev in shard_abbrevs['prefixes']:
           vars()['Obs' + shard + '_model'] += field_def + fkey_field_def

# now for the param_info model data transfers
fields = []
cursor.execute("desc " + opus1 + ".forms")
param_info_sql = []
rows = cursor.fetchall()
for row in rows:
    field = row[0]
    fields += [field]

param_info_sql += ["delete from opus.param_info"]
hacked_exclude = ("'" + "','".join(exclude) + "'").split(',')
param_info_sql += ["insert into opus.param_info select " + ','.join(fields) + " from " + opus1 + ".forms " + where_clause % tuple(hacked_exclude)]

# update the display prefs for each field in the new param_info table
fields = []
cursor.execute("desc " + opus1 + ".table_names")
rows = cursor.fetchall()
for row in rows:
    field = row[0]
    fields += [field]
param_info_sql += ["update opus.param_info as params," + opus1 + ".forms as forms set params.display = true where forms.display = 'Y' and params.id = forms.no"]
param_info_sql += ["update opus.param_info as params," + opus1 + ".forms as forms set params.display_results = true where forms.display_results = 'Y' and params.id = forms.no"]
# param_info_sql += ["update param_info set name = concat('mov_', name) where category_name = 'obs_movies'"]





#----------------------------------- print sql quries -----------------------------------#
if to_print == 'sql':

    print "SET SQL_MODE = 'STRICT_ALL_TABLES'; \n"
    print "SET foreign_key_checks = 0; \n"

    # param_info queries
    print "#\n# param_info queries"
    for q in param_info_sql:
       print str(q) + ';'

    print "# update field_names in param_info table"
    for table_name in data_queries:
        for field_info in data_queries[table_name]:
            obs_field  = field_info['obs']
            opus_field = field_info['opus']
            form_type = field_info['form_type']
            mission = ''
            inst = ''
            if table_name in abbrevs:
                abbrev = abbrevs[table_name]
                if abbrev in mission_abbrevs:
                    mission = abbrev
                else:
                    inst = abbrev
                    for shard in shards: # finding the mission, we know the inst
                        if inst in shards[shard]['prefixes']:
                    	    mission = shards[shard]['mission']

            slug = getSlug(opus_field,table_name,abbrevs)
            print "update " + opus2 + ".param_info set name = '" + opus_field + "', "
            print "form_type = '" + str(form_type) + "', "
            print "mission = '" + str(mission) + "', "
            print "instrument = '" + str(inst) + "', "
            print "slug = '" + slug + "' "
            print " where name = '" + obs_field + "' and category_name = '" + table_name + "';"


    print "#\n# moving data from opus1 fields to opus2 fields in Observations"
    # first add a primary key to ring_obs_id fields
    print "alter table " + opus2 + ".observations add unique key (ring_obs_id);"

    from search.models import *

    sql = []

    for table_name in data_queries:
       equiv_list = []
       obs_field_list = []
       for field_info in data_queries[table_name]:
           obs_field  = field_info['obs']
           opus_field = field_info['opus']
           obs_field_list += [obs_field]
           equiv_list += ["opus.observations."  + opus_field + " = " + opus1 + "." + table_name + "." + obs_field]
       if table_name == "obs_general":
           clause = "insert into opus.observations (" + ','.join(obs_field_list) + ") select " + ','.join(obs_field_list) + " from " + opus1 + "." + table_name
           if len(volumes):
               clause += " \n where " + opus1 + ".obs_general.volume_id in ('" + "','".join(volumes) + "')"
       else:
           clause = "update opus.observations," + opus1 + "." + table_name + " set " + ','.join(equiv_list) + \
                    "\n where opus.observations.ring_obs_id = " + opus1 + "." + table_name + ".ring_obs_id"
           if len(volumes):
               clause += " \n and " + opus2 + ".observations.volume_id in ('" + "','".join(volumes) + "')"
       sql += [clause + ';']
    print ";\n".join(sorted(sql))

    # fix all the ring obs ids
    print "\n"
    print "# converting ring_obs_ids in Observations from slashes to underscores + removing dots"
    print "# also adding field for opus1_ring_obs_id "
    print "alter table observations add column opus1_ring_obs_id char(40);"
    table = "observations"
    q = "select ring_obs_id from " + opus1 + '.obs_general '
    if len(volumes):
        q += " where " + "volume_id in ('" + "','".join(volumes) + "')"
    cursor.execute(q)
    rows = cursor.fetchall()
    for row in rows:
    	ring_obs_id = row[0]
    	new_id = '_'.join(ring_obs_id.split('/'))
    	new_id = ''.join(new_id.split('.'))
    	q = "update " + opus2 + '.' + table + " set ring_obs_id = '" + new_id + "', opus1_ring_obs_id = '" + ring_obs_id + "' where ring_obs_id = '" + ring_obs_id + "';"
    	print q


    # mult table data
    print "#\n# loading up the mult_table data"
    print "alter table "+ opus2 + ".mult_target_name add column grouping char(7);"
    for q in mult_queries:
        if q.find("insert into "+ opus2 + ".mult_target_name") > -1:
           print "insert into "+ opus2 + ".mult_target_name (id,value,label,disp_order,display,default_fade,grouping) select * from " + opus1 + ".mult_obs_general_target_name;"
        else: print q + ';'

    print "#\n# updating the mult fields in the data tables"
    for q in mult_field_data:
       print q

    print "#\n# building the shard tables"
    for shard,shard_info in shards.items():
       table_name = 'obs_' + shard
       clause = shard_info['clause']
       model_name = 'Obs' + shard.title().replace('_','')
       # shard_model = get_model('search',model_name)
       shard_fields = [f.name for f in get_model('search',model_name)._meta.fields]
       for index, field in enumerate(shard_fields):
           if field.startswith('mult_'):
               shard_fields[index] = field + "_id" # django adds the "_id" suffix to FKey fields
       shard_fields = ','.join(shard_fields)

       # REMOVING THIS
       print "drop table if exists " + opus2 + '.' + table_name + ";"
       q = "create table " + opus2 + '.' + table_name + " like " + opus2 + ".observations;"
       print q
       q = "insert into " + opus2 + "." + table_name + " (" + shard_fields + ") select " + shard_fields + " from " + opus2 + ".observations where " + clause + ';'
       # DO NOT USE VIEWS views do not retain the keys of the original table
       # q = "create or replace view " + opus2 + "." + table_name + "(" + shard_fields + ") as select * from " + opus2 + ".Observations where " + clause + ';'
       print q

    # restore the param_info,categories,groups, and images tables
    print """

# restore some old tables
use opus;
SET foreign_key_checks = 0;

# some fiddly fixy things
update param_info set form_type = 'RANGE' where form_type = 'None' and name like '%1' or name like '%2';
update param_info set slug = 'target' where name = 'target_name';
update param_info set display = NULL where display = 'N';
update param_info set slug = 'planet' where name = 'planet_id';

# first make sure we have all the volume_ids filled out, somehow this didn't..
update opus.observations o, Observations.obs_general g set o.volume_id = g.volume_id where o.opus1_ring_obs_id = g.ring_obs_id;


drop table if exists all_volumes_temp;
create table all_volumes_temp select distinct volume_id from observations;

drop table if exists opus.groups;
drop table if exists opus.categories;

# grouped widgets
drop table if exists opus.grouping_target_name;
create view grouping_target_name as select * from mult_planet_id;

create table opus.groups like opus_hack.groups;
create table opus.categories like opus_hack.categories;

insert into opus.groups select * from opus_hack.groups;
insert into opus.categories select * from opus_hack.categories;

update param_info n, opus_hack.param_info o set n.category_id = o.category_id, n.category_name = o.category_name where n.name = o.name;

drop table if exists opus.guide_example;
drop table if exists opus.guide_group;
drop table if exists opus.guide_keyvalue;
drop table if exists opus.guide_resource;
create table opus.guide_example like opus_hack.guide_example;
create table opus.guide_group like opus_hack.guide_group;
create table opus.guide_keyvalue like opus_hack.guide_keyvalue;
create table opus.guide_resource like opus_hack.guide_resource;
insert into opus.guide_example select * from opus_hack.guide_example;
insert into opus.guide_group select * from opus_hack.guide_group;
insert into opus.guide_keyvalue select * from opus_hack.guide_keyvalue;
insert into opus.guide_resource select * from opus_hack.guide_resource;

# restore the files table
drop table if exists opus.files;
create table opus.files select * from Observations.files where volume_id in (select * from all_volumes_temp);
alter table files change column no id int(7) not null;
update opus.files,opus.observations set files.ring_obs_id = observations.ring_obs_id where files.ring_obs_id = observations.opus1_ring_obs_id;
alter table files add column mission char(15);
update files set mission = 'CO' where instrument_id like 'CO%';
update files set mission = 'GO' where instrument_id = 'GOSSI';
update files set mission = 'NH' where instrument_id = 'LORRI';
update files set mission = 'VG' where instrument_id = 'VGISS';

# restore file_sizes
drop table if exists opus.file_sizes;
create table opus.file_sizes select * from Observations.file_sizes where volume_id in (select * from all_volumes_temp);
alter table file_sizes add key (ring_obs_id);
update opus.file_sizes,opus.observations set file_sizes.ring_obs_id = observations.ring_obs_id where file_sizes.ring_obs_id = observations.opus1_ring_obs_id;
alter table file_sizes add key (name);
alter table file_sizes add column id int(7) not null auto_increment primary key;

# restore files_not_found
drop table if exists opus.files_not_found;
create table opus.files_not_found select * from Observations.files_not_found where volume_id in (select * from all_volumes_temp);
alter table files_not_found add key (ring_obs_id);
update opus.files_not_found f,opus.observations o set f.ring_obs_id = o.ring_obs_id where f.ring_obs_id = o.opus1_ring_obs_id;
alter table files_not_found add column id int(7) not null auto_increment primary key;
alter table files_not_found add key (name);



# restore the images table
# first make sure the observation.images table is up to date:
update Observations.images as i, Observations.obs_general as g set i.volume_id = g.volume_id where i.ring_obs_id = g.ring_obs_id;
drop table if exists opus.images;
create table opus.images select * from Observations.images  where volume_id in (select * from all_volumes_temp);
alter table images add key (volume_id);
alter table images add key (instrument_id);
alter table images add key (volume_id);
alter table images add column id bigint not null auto_increment primary key;
alter table images add unique key (ring_obs_id);
update images as i,observations as o set i.volume_id = o.volume_id where i.ring_obs_id= o.ring_obs_id;
update opus.images,opus.observations set images.ring_obs_id = observations.ring_obs_id where images.ring_obs_id = observations.opus1_ring_obs_id;


# somehow this didn't happen
update observations as a, obs_CO       as b set b.primary_file_spec = a.primary_file_spec where b.ring_obs_id = a.ring_obs_id;
update observations as a, obs_CO_COCIRS as b set b.primary_file_spec = a.primary_file_spec where b.ring_obs_id = a.ring_obs_id;
update observations as a, obs_CO_COISS as b set b.primary_file_spec = a.primary_file_spec where b.ring_obs_id = a.ring_obs_id;
update observations as a, obs_CO_COVIMS as b set b.primary_file_spec = a.primary_file_spec where b.ring_obs_id = a.ring_obs_id;
update observations as a, obs_GO       as b set b.primary_file_spec = a.primary_file_spec where b.ring_obs_id = a.ring_obs_id;
update observations as a, obs_GO_GOSSI as b set b.primary_file_spec = a.primary_file_spec where b.ring_obs_id = a.ring_obs_id;
update observations as a, obs_NH       as b set b.primary_file_spec = a.primary_file_spec where b.ring_obs_id = a.ring_obs_id;
update observations as a, obs_NH_NHJULO  as b set b.primary_file_spec = a.primary_file_spec where b.ring_obs_id = a.ring_obs_id;
update observations as a, obs_VG       as b set b.primary_file_spec = a.primary_file_spec where b.ring_obs_id = a.ring_obs_id;
update observations as a, obs_VG_VGISS as b set b.primary_file_spec = a.primary_file_spec where b.ring_obs_id = a.ring_obs_id;




#cleanup
SET foreign_key_checks = 1;

DELIMITER //
CREATE PROCEDURE `vols` (IN my_table VARCHAR(200))
BEGIN
    SET @sql = CONCAT('SELECT volume_id,count(*) FROM ',my_table,' group by volume_id order by volume_id');
    PREPARE s1 from @sql;
    EXECUTE s1;
END //
DELIMITER ;


select ('BYE !!!!!');

"""






#----------------------------------- print django models -----------------------------------#
# this Observations Model's extra manager
Obs_model += """

    test_objects = ObservationsManager()
    objects = models.Manager()

    class Meta:
        db_table = u'observations'

    def __unicode__(self):
        return self.ring_obs_id

"""

if to_print == 'models':

    print """
# Don't add stuff here, this is a generated file.
# generated by import/build_obs.py
# for custom models use models_custom.py

from django.db import models

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

class ObservationsManager(models.Manager):
    # this is used by unit tests to make a smaller set
    def get_query_set(self):
        return super(ObservationsManager, self).get_query_set().order_by('ring_obs_id')

    """
    # print all the mult field choices
    print "# choices for all the mult fields in all data tables"
    for choice_name,choices in field_choices.items():
        print choice_name + ' = ' + str(choices) + "\n"

    print "# Main Data Model table Observations"
    print Obs_model

    print "\n#Shard Models"
    for shard in shards:
        print vars()['Obs' + shard + '_model']
        print "    class Meta:"
        print "        db_table = u'obs_" + shard + "'\n"

    print "\n#Mult table fkey models"
    for mult_model in mult_models:
        print mult_model + "\n"
