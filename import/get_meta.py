#---------------------------------------------------------------
#
#   this is just a way to get a CSV of the pertinent fields 
#   in a volumes meta table for parsing dat files
#
#---------------------------------------------------------------
# Set up the Django Enviroment for running as shell script    
import sys
from django.db import connection
cursor = connection.cursor()
cursor.execute('select name,start_byte,bytes,type from volumes.coiss_meta where start_byte is not null order by start_byte');
rows = cursor.fetchall()
for r in rows:    
    new = [str(f) for f in r] 
    print ','.join(new)     
    