# Set up the Django Enviroment for running as shell script
import sys
sys.path.append('/users/lballard/projects/')
sys.path.append('/users/lballard/projects/opus/')
from opus import settings  
from django.core.management import setup_environ 
setup_environ(settings)
                            
# app imports
from results.models import *


# do only certain volumes
volumes = []

if len(volumes):
    images = Image.objects.filter(volume_id__in=volumes)
else:
    images =  Image.objects.all()
    
for i in images:
    