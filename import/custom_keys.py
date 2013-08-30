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
from paraminfo.models import *

cursor = connection.cursor()

database = 'opus'

q = "desc %s.observations" % database

cursor.execute(q)
rows = cursor.fetchall()
for row in rows:
    index_tables = []  # tables in which this param will be indexed
    if row[0].find('mult_') == 0:
        field = row[0]
        param_name = field[5:-3]
        print param_name

        param_info = ParamInfo.objects.get(name=param_name)
        if len(param_info.mission):
            # this will be indexed in a mission table
            index_tables.append('obs_' + param_info.mission.strip())

            if len(param_info.instrument):
                # this will be indexed in a instrument table
                index_tables.append('obs_' + param_info.mission.strip() + '_' + param_info.instrument.strip())
        else:
            index_tables.append('observations')

        print 'tables: ' + ', '.join(index_tables)
        for table in index_tables:
            q = "alter table %s add index (%s)" % (table, field)
            cursor.execute(q)
            print q
