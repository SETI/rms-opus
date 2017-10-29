"""
    this script will import new volumes to database "opus"
    taking all volumes from database "opus_new_import"

    for new volumes you only need to import

    # data tables
    show tables like 'obs%';

    # tables related to finding files:
    show tables like '%file%';

    # the images table
    opus.images

"""
# Set up the Django Enviroment for running as shell script
import sys
import os
import logging
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

db_new_volumes = 'opus_new_import'
db_opus = 'opus'

cursor = connection.cursor()

# this script could also update ancillary tables, some day maybe it will
rebuild_mults = False  # rebuild all mult tables too, use this when values of
                       # multi-choice fields are going to change, like adding
                       # a new target name.

# add the data tables
all_tables = []
cursor.execute("show tables in {} like 'obs%'".format(db_new_volumes))
obs_exclude = ['obs_surface_geometry_non_unique']
all_tables += [row[0] for row in cursor.fetchall() if row[0] not in obs_exclude]
cursor.close()
cursor = connection.cursor()

# add the files tables
cursor.execute("show tables in {} like '%file%'".format(db_new_volumes))
all_tables += [row[0] for row in cursor.fetchall() if row[0]]
cursor.close()
cursor = connection.cursor()

# add the images tables
all_tables += ['images']

# go!
for tbl in all_tables:
    print 'updating {}'.format(tbl)
    # get all the fields for this table, remove the id field so opus will assign
    cursor.execute('select * from {} limit 1'.format(tbl))
    field_names = [i[0] for i in cursor.description]
    field_names.remove('id')
    cursor.close()
    cursor = connection.cursor()

    field_str = ','.join(field_names)
    q = """
        insert into {}.{} ({}) select {} from {}.{}
        """.format(db_opus, tbl, field_str, field_str, db_new_volumes, tbl)
    try:
        cursor.execute(q)
    except Exception as e:
        print(q)
        print(e)

    cursor.close()
    cursor = connection.cursor()
