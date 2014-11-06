# Set up the Django Enviroment for running as shell script
import sys
sys.path.append('/home/django/djcode/opus')  #srvr
# sys.path.append('/users/lballard/projects/opus/')
# from opus import settings
from django.conf import settings
from settings import CACHES, DATABASES  # DATABASES creds only
settings.configure(CACHES=CACHES, DATABASES=DATABASES) # include any other settings you might need

# script imports
from os import system
from django.db import transaction, connection
from django.core.management import  call_command
from django.db.models import get_model
from django.db.utils import DatabaseError
from django.utils.datastructures import SortedDict
from settings import DATABASES, MULT_FIELDS  # DATABASES creds only

opus1 = 'Observations2' # from here
opus2 = 'opus'   # to here


#----  shell argvs --------#
import sys

if len(sys.argv) < 2:
    print """

    Welcome to the OPUS 2 importer! This script transfers data from OPUS1 to OPUS2.

    1st arg is a list of volumes, with no spaces

    Like so:

    python build_db.py COCIRS_5909,COISS_2068,COISS_2069,COVIMS_0040,VGISS_8207

    make sure there are no spaces in your volume list!

    you can also do all volumes:

    python build_db.py all

    this script assumes we are connecting an old database named Observations
    to a new one named opus. These names can be changed at the top of the script

    expired: see the wiki for how to use this! http://localhost/wikka/wikka.php?wakka=DjangoPortNotes

    """
    sys.exit()


volumes = sys.argv[1].split(',')
volumes.sort()

volumes_str = '"' + ('","').join(volumes) + '"'
if volumes == ['all']:
    volumes = []  # nothing to add to the query
    volumes_str = ''



# ------------ some initial defining of things ------------#

# hello mysql

cursor = connection.cursor()
# cursor.execute("SET SQL_MODE = 'STRICT_ALL_TABLES'")
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


# ------------ we will copy all the Obs_ tables from Observations to opus ------------#
obs_exclude = ['obs_rg_COISS_2075', 'obs_surface_geometry_raw'] # obs-like tables to exclude
cursor.execute("use %s" % opus1)
cursor.execute("show tables like %s", 'obs%')
obs_tables = [row[0] for row in cursor.fetchall() if row[0] not in obs_exclude]


# ------------------------ begin the beguine -----------------------------------#
# loop thru all obs tables in the old opus database
# and copy these tables to the new opus database
for tbl in obs_tables:

    # create the new table
    q_create = "create table %s.%s like %s.%s"
    q_params = [opus2, tbl, opus1, tbl]
    q = q_create % tuple(q_params)  # using % instead of comma here because we are substituting a table name and don't want Django to be adding quotes
    print q
    try:
        cursor.execute(q)
    except DatabaseError, e:
        print e
        print """
                failed to create first table, does it already exist?

                You may need to:

                    drop database %s;
                    create database %s;
                """ % (opus2, opus2)
        sys.exit()


    # copy the data over from the old table to the new
    q_insert = "insert into %s.%s select %s.* from %s.%s"
    q_params = [opus2, tbl, tbl, opus1, tbl]

    # some tables don't have the volume_id field, so we will join all tables with obs_general to get the volume_id
    if tbl != 'obs_general':
        q_insert = q_insert + " join obs_general on %s.obs_general_no = obs_general.obs_general_no"
        q_params.append(tbl)
    if volumes:
        q_insert = q_insert + " where obs_general.volume_id in (%s)"
        q_params.append(volumes_str)

    print q_insert % tuple(q_params)
    cursor.execute(q_insert % tuple(q_params))

    # handle the changing of the primary key and field from 'obs_general_no' to 'obs_general_id' for Django happyness

    # the obs_general table is the main holder of the PK to all other tables
    # it's called obs_general_no in opus1, so here we change it to
    # "id" for the obs_general_table and "obs_general_id" for all other tables

    # some constants for this table, the field name and the primary key declaration for the query
    field_name = 'obs_general_id'
    if tbl == 'obs_general':
        field_name = 'id'
    if tbl in ['obs_movies'] and tbl.find('obs_surface') > -1:
        field_name = 'id'

    # obs_general_no is the PK or Foreign Key for all tables, change its name to field_name
    alter_query = "alter table %s.%s change obs_general_no %s mediumint(8) unsigned not null" % (opus2, tbl, field_name)
    if tbl == 'obs_general':
        alter_query = "alter table %s.%s change obs_general_no %s mediumint(8) unsigned not null auto_increment " % (opus2, tbl, field_name)
    try:
        print alter_query
        cursor.execute(alter_query)
    except Warning:
        pass  # it's ok, the query executed it's just that I upgraded mysql

    # opus1 uses obs_general_no as PK in all tables, but django would prefer to use its own id field
    """
    # removed, just handle the exception in the execute statement below
    unique = False
    if tbl not in ['obs_movies'] and tbl.find('obs_surface') == -1:
        unique = True
    """
    try:
        cursor.execute("drop index `PRIMARY` on %s.%s" % (opus2, tbl))  # drop the primary index so we can change this field
    except DatabaseError:
        pass  # some tables don't have this index

    # now add a primary key 'id' to all tables (except obs_general, and multi tables) for django to use
    # this was removed, was it important? -->
    #    if tbl not in ['obs_movies'] and tbl.find('obs_surface') == -1:
    #        # something..
    if tbl != 'obs_general':
        alter_query = "alter table %s.%s add column id mediumint(8) unsigned not null auto_increment primary key" % (opus2, tbl)
        print alter_query
        cursor.execute(alter_query)

    # and add the key for obs_general_no field
    if tbl != 'obs_general':
        if tbl not in ['obs_movies'] and tbl.find('obs_surface') == -1:
            alter_query = "alter table %s.%s add unique key (obs_general_id)" % (opus2, tbl)
            print alter_query
            cursor.execute(alter_query)

# done looping through obs tables

# ------------ Now update all the rings_obs_ids in all the created tables ------------#
# opus2 has a different style of ring_obs_ids than opus1 - underscores replace slashes

# first add the column to obs_general to preserve an association with the old opus ring_obs_id
cursor.execute("alter table %s.obs_general add column opus1_ring_obs_id char(40);" % opus2)
cursor.execute("update %s.obs_general set opus1_ring_obs_id = ring_obs_id" % opus2)

# and do the ring_obs_id converting
for tbl in obs_tables:
    print tbl
    cursor.execute("select ring_obs_id from %s.%s" % (opus2, tbl))
    all_rows = cursor.fetchall()
    for row in all_rows:
        ring_obs_id = row[0]
        new_ring_obs_id = '_'.join(ring_obs_id.strip().split('/'))
        new_ring_obs_id = ''.join(new_ring_obs_id.split('.'))
        q_up = "update %s.%s set ring_obs_id = '%s' where ring_obs_id = '%s'" % (opus2, tbl, new_ring_obs_id, ring_obs_id)
        print q_up
        cursor.execute(q_up)

# flush commit all of the above
transaction.commit_unless_managed()



# ------------- handle mult tables -------------#

# first get the names of all the tables we'll be copying
cursor.execute("use %s" % opus1)
cursor.execute("show tables like %s", 'mult%')
mult_tables = [row[0] for row in cursor.fetchall() if row[0]]

# now copy all these tables to the new opus database
for tbl in mult_tables:

    # create the mult table
    q_create = "create table %s.%s like %s.%s"
    q_params = [opus2, tbl, opus1, tbl]
    cursor.execute(q_create % tuple(q_params))  # using % over comma here because we are substituting a table name and don't want Django to be adding quotes

    # handle the changing of the key and field from 'no' to 'id' for Django happyness

    try:
        cursor.execute("alter table %s.%s add unique index(no)" % (opus2, tbl))  # placeholder index, with auto_increment won't let you drop primary, must have some unique key
    except Warning:
        pass  # upgrade probs, query executed ok

    cursor.execute("drop index `PRIMARY` on %s.%s" % (opus2, tbl))  # drop the primary index so we can cange this field

    try:
        cursor.execute("alter table %s.%s change no id int(3) unsigned not null auto_increment primary key;" % (opus2, tbl))  # change the field, adding the primary key
    except Warning:
        pass  # upgrade probs, query executed ok

    cursor.execute("drop index no on %s.%s" % (opus2, tbl))  # drop the placeholder index

    # copy over the data from old mult table to new
    q_insert = "insert into %s.%s select %s.* from %s.%s"
    q_params = [opus2, tbl, tbl, opus1, tbl]
    cursor.execute(q_insert % tuple(q_params))



cursor.execute("create view %s.grouping_target_name as select * from %s.mult_obs_general_planet_id" % (opus2, opus2))


# ------------ copy over the 'forms' table into the new 'param_info' table  ------------#

# first, fetch the tables:
# system("mysql %s < import/backup_util_tables.sql -u%s -p%s" % (opus2, DATABASES['default']['USER'], DATABASES['default']['PASSWORD'])))

# first, build the empty param_info table in the new db - the table schema lives in a dump file in the repo
print "building param_info from param_info_table.sql "
system("mysql %s < param_info_table.sql -u%s -p%s" % (opus2, DATABASES['default']['USER'], DATABASES['default']['PASSWORD']))

# and import the data
q = "insert into %s.param_info select * from %s.forms where (display = 'Y' or display_results = 'Y')" % (opus2, opus1)
for x in exclude:
    q = q + " and table_name not like %s "
cursor.execute(q, exclude)
q = "insert into %s.param_info select * from %s.forms where table_name = 'obs_general' and name in ('time1','time2')" % (opus2, opus1)
cursor.execute(q)

# some fiddly updates to the param_info_table
cursor.execute("update %s.param_info as params, %s.forms as forms set params.display = true where forms.display = 'Y' and params.id = forms.no" % (opus2, opus1))
cursor.execute("update %s.param_info as params, %s.forms as forms set params.display_results = true where forms.display_results = 'Y' and params.id = forms.no" % (opus2, opus1))
cursor.execute("update " + opus2 + ".param_info set form_type = 'RANGE' where form_type = 'None' and name like %s or name like %s" , ('%1', '%2'))
cursor.execute("update %s.param_info set slug = 'target' where name = 'target_name'" % opus2)
cursor.execute("update %s.param_info set display = NULL where display = 'N'" % opus2)
cursor.execute("update %s.param_info set slug = 'planet' where name = 'planet_id'" % opus2)
cursor.execute("update %s.param_info set slug = 'surfacetarget' where slug = 'target' and category_name = 'obs_surface_geometry'" % opus2)
cursor.execute("update %s.param_info set form_type = 'TIME' where slug = 'timesec2'" % opus2)
q = "delete from %s.param_info where slug = 'target'" % opus2
cursor.execute(q + " and category_name like %s" , 'obs_surface%')
cursor.execute("update %s.param_info set display = 1 where name = 'primary_file_spec'" % opus2)
# update param_info set display_results = 1 where slug = 'time1' or slug = 'time2';
cursor.execute("update %s.param_info set display_results = 1 where slug = 'time1' or slug = 'time2'" % opus2)
# update param_info set display_results = 1 where slug = 'timesec1' or slug = 'timesec2';
cursor.execute("update %s.param_info set display_results = 1 where slug = 'timesec1' or slug = 'timesec2';" % opus2)
cursor.execute("update %s.param_info set form_type = 'STRING' where name = 'primary_file_spec'" % opus2)


# ----------- creating the grouping, category, and guide tables --------------#
queries = """
create table %s.groups like opus_hack.groups;
create table %s.categories like opus_hack.categories;
insert into %s.groups select * from opus_hack.groups;
insert into %s.categories select * from opus_hack.categories;

create table %s.guide_example like opus_hack.guide_example;
create table %s.guide_group like opus_hack.guide_group;
create table %s.guide_keyvalue like opus_hack.guide_keyvalue;
create table %s.guide_resource like opus_hack.guide_resource;
create table %s.user_searches like opus_hack.user_searches;
insert into %s.guide_example select * from opus_hack.guide_example;
insert into %s.guide_group select * from opus_hack.guide_group;
insert into %s.guide_keyvalue select * from opus_hack.guide_keyvalue;
insert into %s.guide_resource select * from opus_hack.guide_resource;

create table %s.partables like opus_hack.partables;
insert into %s.partables select * from opus_hack.partables;

create table %s.django_admin_log like opus_hack.django_admin_log;
create table %s.django_content_type like opus_hack.django_content_type;
create table %s.django_session like opus_hack.django_session;
create table %s.django_site     like opus_hack.django_site    ;

insert into %s.django_admin_log select * from opus_hack.django_admin_log;
insert into %s.django_content_type select * from opus_hack.django_content_type;
insert into %s.django_session select * from opus_hack.django_session;
insert into %s.django_site select * from opus_hack.django_site;

"""

for q in queries.strip().split(';'):
    if not q.strip(): continue  # skip blank lines
    print q % opus2
    cursor.execute(q % opus2)

print "OK"

# ----------- restore the files table -------------#
cursor.execute("create table %s.files like %s.files" % (opus2, opus1))
q = "insert into %s.files select * from %s.files " % (opus2, opus1)
if volumes:
    q += "where %s.files.volume_id in (%s)" % (opus1, volumes_str)
cursor.execute(q)
cursor.execute("alter table %s.files change column no id int(7) not null" % (opus2))
# and take care of the ring_obs_id transform
cursor.execute("update %s.files t,%s.obs_general o set t.ring_obs_id = o.ring_obs_id where t.ring_obs_id = o.opus1_ring_obs_id" % (opus2, opus2))

cursor.execute("alter table %s.files add column mission_id char(2) not null" % (opus2))
cursor.execute("select distinct instrument_id from %s.files" % opus2)
all_inst_ids = [row[0] for row in cursor.fetchall() if row[0]]
for instrument_id in all_inst_ids:
    mission_id = 'NH' if instrument_id.strip() == 'LORRI' else instrument_id[0:2]
    cursor.execute("update %s.files set mission_id = '%s' where instrument_id = '%s'" % (opus2, mission_id, instrument_id))



# ----------- restore table_names  -------------#
cursor.execute("create table %s.table_names like %s.table_names" % (opus2, opus1))
cursor.execute("insert into %s.table_names select * from %s.table_names" % (opus2, opus1))
cursor.execute("alter table %s.table_names change column no id int(9) not null auto_increment" % (opus2))
cursor.execute("alter table %s.table_names change column rings display char(1) default 'Y'" % (opus2))
cursor.execute("alter table %s.table_names change column div_title label char(60)" % (opus2))
cursor.execute("alter table %s.table_names add column mission_id char(2)" % opus2)
cursor.execute("update %s.table_names set mission_id = 'CO' where table_name = 'obs_mission_cassini'" % opus2)
cursor.execute("update %s.table_names set mission_id = 'GO' where table_name = 'obs_mission_galileo'" % opus2)
cursor.execute("update %s.table_names set mission_id = 'NH' where table_name = 'obs_mission_new_horizons'" % opus2)
cursor.execute("update %s.table_names set mission_id = 'VG' where table_name = 'obs_mission_voyager'" % opus2)

# ----------- restore file_sizes  -------------#
cursor.execute("create table %s.file_sizes like %s.file_sizes" % (opus2, opus1))
q = "replace into %s.file_sizes select * from %s.file_sizes " % (opus2, opus1)
if volumes_str:
    q = q + " where %s.file_sizes.volume_id IN (%s)" % (opus1, volumes_str)
cursor.execute(q)
cursor.execute("alter table %s.file_sizes add column id int(9) not null auto_increment primary key" % (opus2))
cursor.execute("update %s.file_sizes t,%s.obs_general o set t.ring_obs_id = o.ring_obs_id where t.ring_obs_id = o.opus1_ring_obs_id" % (opus2, opus2))

# ----------- restore files_not_found -------------#
q = "create table %s.files_not_found select * from %s.files_not_found" % (opus2, opus1)
if volumes_str:
    q = q + " where %s.files_not_found.volume_id IN (%s)" % (opus1, volumes_str)
cursor.execute(q)
cursor.execute("alter table %s.files_not_found add column id int(8) not null auto_increment primary key" % (opus2))
cursor.execute("alter table %s.files_not_found add unique key (name)" % (opus2))
cursor.execute("alter table %s.files_not_found add key (ring_obs_id)" % (opus2))
cursor.execute("update %s.files_not_found t,%s.obs_general o set t.ring_obs_id = o.ring_obs_id where t.ring_obs_id = o.opus1_ring_obs_id" % (opus2, opus2))


# ----------- restore images -------------#
# first make sure that old db has volume_id in images table
cursor.execute("update %s.images as i, %s.obs_general as g set i.volume_id = g.volume_id where i.ring_obs_id = g.ring_obs_id" % (opus1, opus1))
q = "create table %s.images select * from %s.images" % (opus2, opus1)
if volumes:
    q = q + " where %s.images.volume_id in (%s)" % (opus1, volumes_str)
cursor.execute(q)
cursor.execute("alter table %s.images add column id bigint not null auto_increment primary key" % (opus2))
cursor.execute("alter table %s.images add unique key (ring_obs_id)" % (opus2))
cursor.execute("alter table %s.images add key (ring_obs_id)" % (opus2))
cursor.execute("update %s.images t,%s.obs_general o set t.ring_obs_id = o.ring_obs_id where t.ring_obs_id = o.opus1_ring_obs_id" % (opus2, opus2))



# ------------ cleanup ------------ #
transaction.commit_unless_managed()  # flushes any waiting queries
cursor.execute("SET foreign_key_checks = 1")

print("build of %s 2 database is complete. Bye!" % opus2);
