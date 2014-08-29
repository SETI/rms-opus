# Set up the Django Enviroment for running as shell script
import sys
# sys.path.append('/home/django/djcode/opus')  #srvr
sys.path.append('/users/lballard/projects/opus/')
# from opus import settings
from django.conf import settings
from settings import CACHES, DATABASES
settings.configure(CACHES=CACHES, DATABASES=DATABASES) # include any other settings you might need

# app imports
from results.models import *


# do only certain volumes
volumes = []

if len(volumes):
    images = Image.objects.filter(volume_id__in=volumes)
else:
    images =  Image.objects.all()

for i in images:
