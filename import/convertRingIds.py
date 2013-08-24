# Set up the Django Enviroment for running as shell script
import sys
sys.path.append('/users/lballard/projects/')
sys.path.append('/users/lballard/projects/opus/')
from opus import settings  
from django.core.management import setup_environ 
setup_environ(settings)   

from django.db import connection
cursor = connection.cursor()                  
opus1 = 'Observations' 
opus2 = 'opus'       


print "updating observations"
q = "select opus2.id,opus2.ring_obs_id from " + opus2 + ".observations as opus2," + opus1 + ".obs_general as opus1 "
q += " where opus1.ring_obs_id = opus2.ring_obs_id "
cursor.execute(q)
rows = cursor.fetchall()       
for row in rows:
	id = row[0]
	ring_obs_id = row[1]
	new_id = '_'.join(ring_obs_id.split('/'))   
	new_id = ''.join(new_id.split('.'))   
	print 'Observations: ' + new_id
	q = "update " + opus2 + ".Observations set ring_obs_id = '" + new_id + "' where id = " + str(id)
	cursor.execute(q)

print "updating images"
q = "select opus2.id,opus2.ring_obs_id from " + opus2 + ".images as opus2," + opus1 + ".images as opus1 "
q += " where opus1.ring_obs_id = opus2.ring_obs_id "
cursor.execute(q)
rows = cursor.fetchall()       
for row in rows:
	id = row[0]
	ring_obs_id = row[1]
	new_id = '_'.join(ring_obs_id.split('/'))   
	new_id = ''.join(new_id.split('.'))   
	print 'Images: ' + new_id
	q = "update " + opus2 + ".images set ring_obs_id = '" + new_id + "' where id = " + str(id)
	cursor.execute(q)



print "updating files"
q = "select opus2.id,opus2.ring_obs_id from " + opus2 + ".files as opus2," + opus1 + ".files as opus1 "
q += " where opus1.ring_obs_id = opus2.ring_obs_id "
cursor.execute(q)
rows = cursor.fetchall()       
for row in rows:
	id = row[0]
	ring_obs_id = row[1]
	new_id = '_'.join(ring_obs_id.split('/'))   
	new_id = ''.join(new_id.split('.'))   
	print 'Files: ' + new_id
	q = "update " + opus2 + ".files set ring_obs_id = '" + new_id + "' where id = " + str(id)
	cursor.execute(q)

