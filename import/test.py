# Set up the Django Enviroment for running as shell script
import sys
sys.path.append('/users/lballard/projects/')
sys.path.append('/users/lballard/projects/opus/')
from opus import settings  
from django.core.management import setup_environ 
setup_environ(settings)                


def say_hello():
    print 'hello'
    
say_hello();
