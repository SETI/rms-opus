import sys
import datetime
sys.path.insert(0, '/home/django/djcode/opus/')
import settings
# this will set the last_modified header to now
dt_file = settings.PROJECT_ROOT + '/apps/tools/deploy_datetime.py'
f1 = open(dt_file, 'w+')
f1.write("deploy_dt = '%s'" % str(datetime.datetime.now()))
f1.close()

