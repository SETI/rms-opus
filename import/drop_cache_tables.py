"""
    drops all tables like 'cache%' in database 'opus'
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

cursor = connection.cursor()

# forget about it
# from settings_local import opus1, opus_to_deploy  # names of the databases

database = 'opus'

# drop cache tables
cursor.execute("show tables in {} like 'cache%'".format(database))
all_cache_tables = [row[0] for row in cursor.fetchall() if row[0]]

for cache_table in all_cache_tables:
    q_up = "drop table {}.{}".format(database, cache_table)
    cursor.execute(q_up)
    print q_up

print "Done!"
