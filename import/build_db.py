"""
    This script populates a database named opus_new_import
    that is a smaller version of the opus database that contains
    only the volumes passed at the command line, like so:

        sudo python build_db.py COISS_2069,COISS_2070,COISS_2071

    NOTE: some tables are copied from opus_hack, and others are built
    from a dump file on disk. See below! 

    It was once used to create the entire opus database and to create
    smaller versions (ie opus_small) for laptop development
    and can still be used that way, but now it's still part of the
    deploy pipeline but is only used to build the small database version
    (you can no longer pass "all" volumes at the command line)

"""

# Set up the Django Enviroment for running as shell script
import sys
import os
import django
from django.conf import settings
# sys.path.append('/Users/lballard/projects/opus/')
sys.path.append('/home/django/djcode/')  #srvr
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "opus.settings")
# from opus import settings
# settings.configure(CACHES=settings.CACHES, DATABASES=settings.DATABASES) # include any other settings you might need
django.setup()

# script imports
from os import system
from django.db import transaction, connection, reset_queries
from django.core.management import  call_command
from django.db.utils import DatabaseError
from settings import MULT_FIELDS  # DATABASES creds only
from secrets import DB_ADMIN, DB_ADMIN_PASS

# forget about it
# from settings_local import opus1, opus_to_deploy  # names of the databases

opus1 = 'Observations'
opus_to_deploy = 'opus_new_import'  # the name of the database we'll create

#----  shell argvs --------#
import sys

if len(sys.argv) < 2:
    print """

    use this to only build the new volumes, opus_small becomes opus_new_import
    use another script to update the local clone of production database, test
    apply it to production using same script

    Welcome to the OPUS 2 importer! This script transfers data from OPUS1 to opus_to_deploy.

    1st arg is a list of volumes, with no spaces

    Like so:

    python build_db.py COCIRS_5909,COISS_1007,COISS_2068,COISS_2069,COVIMS_0040,VGISS_8207

    this will build all volumes and no others. used for making smaller test/laptop version
    haven't tested it in a while.

    make sure there are no spaces in your volume list!

    you can also do all volumes:

    python build_db.py all

    this is what is usually done during a deploy to production, but it's long!
    it rebuilds the entire database, even if you're only importing a few new volumes

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
obs_exclude = ['obs_rg_COISS_2075', 'obs_surface_geometry_raw','obs_surface_geometry_non_unique'] # obs-like tables to exclude
cursor.execute("use %s" % opus1)
q = "show tables like '%s'" % 'obs%'
cursor.execute(q)
obs_tables = [row[0] for row in cursor.fetchall() if row[0] not in obs_exclude]

print "begin"

# ------------------------ begin the beguine -----------------------------------#
# ------------ copy over the 'forms' table into the new 'param_info' table  ------------#

# build the little user_collections template table
print "building user_collections_template from user_collections_template.sql "
system("mysql %s < import/user_collections_template.sql -u%s -p%s" % (opus_to_deploy, DB_ADMIN, DB_ADMIN_PASS))

# build the  param_info table in the new db - the table  lives in a dump file in the repo
print "building param_info from param_info_table.sql "
system("mysql %s < import/param_info_table.sql -u%s -p%s" % (opus_to_deploy, DB_ADMIN, DB_ADMIN_PASS))


# only need this part if regenerating param_info_table from Observations dabase
# also just don't
# see also update_forms_with_opu2_param_info.sql
"""
q = "replace into %s.param_info select * from %s.forms where (display = 'Y' or display_results = 'Y')" % (opus_to_deploy, opus1)
for x in exclude:
    q = q + " and table_name not like %s "
cursor.execute(q, exclude)
q = "replace into %s.param_info select * from %s.forms where table_name = 'obs_general' and name in ('time1','time2')" % (opus_to_deploy, opus1)
cursor.execute(q)
"""

# some fiddly updates to the param_info_table #why!
cursor.execute("update %s.param_info as params, %s.forms as forms set params.display = true where forms.display = 'Y' and params.id = forms.no" % (opus_to_deploy, opus1))
cursor.execute("update %s.param_info as params, %s.forms as forms set params.display_results = true where forms.display_results = 'Y' and params.id = forms.no" % (opus_to_deploy, opus1))
cursor.execute("update " + opus_to_deploy + ".param_info set form_type = 'RANGE' where form_type = 'None' and name like %s or name like %s" , ('%1', '%2'))
cursor.execute("update %s.param_info set slug = 'target' where name = 'target_name' and category_name = 'obs_general'" % opus_to_deploy)
cursor.execute("update %s.param_info set display = NULL where display = 'N'" % opus_to_deploy)
cursor.execute("update %s.param_info set slug = 'planet' where name = 'planet_id'" % opus_to_deploy)
cursor.execute("update %s.param_info set slug = 'surfacetarget' where slug = 'target' and category_name = 'obs_surface_geometry'" % opus_to_deploy)
cursor.execute("update %s.param_info set form_type = 'TIME' where slug = 'timesec2'" % opus_to_deploy)
q = "delete from %s.param_info where slug = 'target'  and category_name like '%s'" % (opus_to_deploy, 'obs_surface%')
cursor.execute(q)
cursor.execute("update %s.param_info set display = 1 where name = 'primary_file_spec'" % opus_to_deploy)
# update param_info set display_results = 1 where slug = 'time1' or slug = 'time2';
cursor.execute("update %s.param_info set display_results = 1 where slug = 'time1' or slug = 'time2'" % opus_to_deploy)
# update param_info set display_results = 1 where slug = 'timesec1' or slug = 'timesec2';
cursor.execute("update %s.param_info set display_results = 1 where slug = 'timesec1' or slug = 'timesec2';" % opus_to_deploy)
cursor.execute("update %s.param_info set form_type = 'STRING' where name = 'primary_file_spec'" % opus_to_deploy)
cursor.execute("update %s.param_info set label = label_results, form_type = NULL where category_name = 'obs_general' and name in ('time1','time2');" % opus_to_deploy)
cursor.execute("update %s.param_info set category_name = 'obs_general' where name = 'volume_id' " % opus_to_deploy)



# loop thru all obs tables in the old opus database
# and copy these tables to the new opus database
print "obs table loop"
for tbl in obs_tables:

    # create the new table
    q_create = "create table %s.%s like %s.%s"
    q_params = [opus_to_deploy, tbl, opus1, tbl]
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
                """ % (opus_to_deploy, opus_to_deploy)
        sys.exit()


    # copy the data over from the old table to the new
    q_insert = "insert into %s.%s select %s.* from %s.%s"
    q_params = [opus_to_deploy, tbl, tbl, opus1, tbl]

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
    alter_query = "alter table %s.%s change obs_general_no %s mediumint(8) unsigned not null" % (opus_to_deploy, tbl, field_name)
    if tbl == 'obs_general':
        alter_query = "alter table %s.%s change obs_general_no %s mediumint(8) unsigned not null auto_increment " % (opus_to_deploy, tbl, field_name)
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
        cursor.execute("drop index `PRIMARY` on %s.%s" % (opus_to_deploy, tbl))  # drop the primary index so we can change this field
    except DatabaseError:
        pass  # some tables don't have this index

    # now add a primary key 'id' to all tables (except obs_general, and multi tables) for django to use
    # this was removed, was it important? -->
    #    if tbl not in ['obs_movies'] and tbl.find('obs_surface') == -1:
    #        # something..
    if tbl != 'obs_general':
        alter_query = "alter table %s.%s add column id mediumint(8) unsigned not null auto_increment primary key" % (opus_to_deploy, tbl)
        print alter_query
        cursor.execute(alter_query)

    # and add the key for obs_general_no field
    if tbl != 'obs_general':
        if tbl not in ['obs_movies'] and tbl.find('obs_surface') == -1:
            alter_query = "alter table %s.%s add unique key (obs_general_id)" % (opus_to_deploy, tbl)
            print alter_query
            cursor.execute(alter_query)

# done looping through obs tables

# ------------ Now update all the rings_obs_ids in all the created tables ------------#
# opus_to_deploy has a different style of ring_obs_ids than opus1 - underscores replace slashes

# first add the column to obs_general to preserve an association with the old opus ring_obs_id
cursor.execute("alter table %s.obs_general add column opus1_ring_obs_id char(40);" % opus_to_deploy)
cursor.execute("update %s.obs_general set opus1_ring_obs_id = ring_obs_id" % opus_to_deploy)

# and do the ring_obs_id converting
for tbl in obs_tables:
    print tbl
    cursor.execute("select ring_obs_id from %s.%s" % (opus_to_deploy, tbl))
    all_rows = cursor.fetchall()
    for row in all_rows:
        ring_obs_id = row[0]
        new_ring_obs_id = '_'.join(ring_obs_id.strip().split('/'))
        new_ring_obs_id = ''.join(new_ring_obs_id.split('.'))
        q_up = "update %s.%s set ring_obs_id = '%s' where ring_obs_id = '%s'" % (opus_to_deploy, tbl, new_ring_obs_id, ring_obs_id)
        print q_up
        cursor.execute(q_up)

# flush commit all of the above
# why was I doing this and now it breaks do we really need..
reset_queries()



# ------------- handle mult tables -------------#

# first get the names of all the tables we'll be copying
cursor.execute("use %s" % opus1)
q = "show tables like '%s'" % 'mult%'
cursor.execute(q)
mult_tables = [row[0] for row in cursor.fetchall() if row[0]]

# now copy all these tables to the new opus database
for tbl in mult_tables:

    # create the mult table
    q_create = "create table %s.%s like %s.%s"
    q_params = [opus_to_deploy, tbl, opus1, tbl]
    cursor.execute(q_create % tuple(q_params))  # using % over comma here because we are substituting a table name and don't want Django to be adding quotes

    # handle the changing of the key and field from 'no' to 'id' for Django happyness

    try:
        cursor.execute("alter table %s.%s add unique index(no)" % (opus_to_deploy, tbl))  # placeholder index, with auto_increment won't let you drop primary, must have some unique key
    except Warning:
        pass  # upgrade probs, query executed ok

    cursor.execute("drop index `PRIMARY` on %s.%s" % (opus_to_deploy, tbl))  # drop the primary index so we can cange this field

    try:
        cursor.execute("alter table %s.%s change no id int(3) unsigned not null auto_increment primary key;" % (opus_to_deploy, tbl))  # change the field, adding the primary key
    except Warning:
        pass  # upgrade probs, query executed ok

    cursor.execute("drop index no on %s.%s" % (opus_to_deploy, tbl))  # drop the placeholder index

    # copy over the data from old mult table to new
    q_insert = "insert into %s.%s select %s.* from %s.%s"
    q_params = [opus_to_deploy, tbl, tbl, opus1, tbl]  # tbl is the mult table
    cursor.execute(q_insert % tuple(q_params))

cursor.execute("create view %s.grouping_target_name as select * from %s.mult_obs_general_planet_id" % (opus_to_deploy, opus_to_deploy))



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
    print q % opus_to_deploy
    cursor.execute(q % opus_to_deploy)

print "OK"

# ----------- restore the files table -------------#
cursor.execute("create table %s.files like %s.files" % (opus_to_deploy, opus1))
q = "insert into %s.files select * from %s.files " % (opus_to_deploy, opus1)
if volumes:
    q += "where %s.files.volume_id in (%s)" % (opus1, volumes_str)
cursor.execute(q)
cursor.execute("alter table %s.files change column no id int(7) not null" % (opus_to_deploy))
# and take care of the ring_obs_id transform
cursor.execute("update %s.files t,%s.obs_general o set t.ring_obs_id = o.ring_obs_id where t.ring_obs_id = o.opus1_ring_obs_id" % (opus_to_deploy, opus_to_deploy))

cursor.execute("alter table %s.files add column mission_id char(2) not null" % (opus_to_deploy))
cursor.execute("select distinct instrument_id from %s.files" % opus_to_deploy)
all_inst_ids = [row[0] for row in cursor.fetchall() if row[0]]
for instrument_id in all_inst_ids:
    mission_id = 'NH' if instrument_id.strip() == 'LORRI' else instrument_id[0:2]
    cursor.execute("update %s.files set mission_id = '%s' where instrument_id = '%s'" % (opus_to_deploy, mission_id, instrument_id))



# ----------- restore table_names  -------------#
cursor.execute("create table %s.table_names like %s.table_names" % (opus_to_deploy, opus1))
cursor.execute("insert into %s.table_names select * from %s.table_names" % (opus_to_deploy, opus1))
cursor.execute("alter table %s.table_names change column no id int(9) not null auto_increment" % (opus_to_deploy))
cursor.execute("alter table %s.table_names change column rings display char(1) default 'Y'" % (opus_to_deploy))
cursor.execute("alter table %s.table_names change column div_title label char(60)" % (opus_to_deploy))
cursor.execute("alter table %s.table_names add column mission_id char(2)" % opus_to_deploy)
cursor.execute("update %s.table_names set mission_id = 'CO' where table_name = 'obs_mission_cassini'" % opus_to_deploy)
cursor.execute("update %s.table_names set mission_id = 'GO' where table_name = 'obs_mission_galileo'" % opus_to_deploy)
cursor.execute("update %s.table_names set mission_id = 'NH' where table_name = 'obs_mission_new_horizons'" % opus_to_deploy)
cursor.execute("update %s.table_names set mission_id = 'VG' where table_name = 'obs_mission_voyager'" % opus_to_deploy)

# ----------- restore file_sizes  -------------#
cursor.execute("create table %s.file_sizes like %s.file_sizes" % (opus_to_deploy, opus1))
q = "replace into %s.file_sizes select * from %s.file_sizes " % (opus_to_deploy, opus1)
if volumes_str:
    q = q + " where %s.file_sizes.volume_id IN (%s)" % (opus1, volumes_str)
cursor.execute(q)
cursor.execute("alter table %s.file_sizes add column id int(9) not null auto_increment primary key" % (opus_to_deploy))
cursor.execute("update %s.file_sizes t,%s.obs_general o set t.ring_obs_id = o.ring_obs_id where t.ring_obs_id = o.opus1_ring_obs_id" % (opus_to_deploy, opus_to_deploy))

# ----------- restore files_not_found -------------#
q = "create table %s.files_not_found select * from %s.files_not_found" % (opus_to_deploy, opus1)
if volumes_str:
    q = q + " where %s.files_not_found.volume_id IN (%s)" % (opus1, volumes_str)
cursor.execute(q)
cursor.execute("alter table %s.files_not_found add column id int(8) not null auto_increment primary key" % (opus_to_deploy))
cursor.execute("alter table %s.files_not_found add unique key (name)" % (opus_to_deploy))
cursor.execute("alter table %s.files_not_found add key (ring_obs_id)" % (opus_to_deploy))
cursor.execute("update %s.files_not_found t,%s.obs_general o set t.ring_obs_id = o.ring_obs_id where t.ring_obs_id = o.opus1_ring_obs_id" % (opus_to_deploy, opus_to_deploy))


# ----------- restore images -------------#
# first make sure that old db has volume_id in images table
cursor.execute("update %s.images as i, %s.obs_general as g set i.volume_id = g.volume_id where i.ring_obs_id = g.ring_obs_id" % (opus1, opus1))
q = "create table %s.images select * from %s.images" % (opus_to_deploy, opus1)
if volumes:
    q = q + " where %s.images.volume_id in (%s)" % (opus1, volumes_str)
cursor.execute(q)
cursor.execute("alter table %s.images add column id bigint not null auto_increment primary key" % (opus_to_deploy))
cursor.execute("alter table %s.images add unique key (ring_obs_id)" % (opus_to_deploy))
cursor.execute("alter table %s.images add key (ring_obs_id)" % (opus_to_deploy))
cursor.execute("update %s.images t,%s.obs_general o set t.ring_obs_id = o.ring_obs_id where t.ring_obs_id = o.opus1_ring_obs_id" % (opus_to_deploy, opus_to_deploy))


# ----------- restore colls_test_key -------------#
cursor.execute("create table %s.colls_test_key like opus_hack.colls_test_key;" % (opus_to_deploy))


# ------------ cleanup ------------ #
reset_queries() # flushes any waiting queries
cursor.execute("SET foreign_key_checks = 1")

print("build of %s 2 database is complete. Bye!" % opus_to_deploy);
