"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.

*************** PLEASE NOTE ***************

be sure and delete all from user_searches before you build the 'search' fixture
otherwise your cache_x table names will never match
reset the auto_increment too.. DO THIS:

delete from user_searches;
ALTER TABLE user_searches AUTO_INCREMENT = 1;
analyze table user_searches;

*****************************
"""
import sys
# sys.path.append('/home/lballard/opus/')  #srvr
sys.path.append('/users/lballard/projects/opus/')
# from opus import settings
import settings
from django.core.management import setup_environ
setup_environ(settings)

from django.test import TestCase
from django.test.client import Client
from django.db.models import get_model

from search.views import *
from results.views import *
from django.http import QueryDict

cursor = connection.cursor()

class ParamInfoTests(TestCase):

    # setup
    c = Client()
    param_name = 'obs_general.planet_id'
    selections = {}
    selections[param_name] = ['Jupiter']

    def test__param_name_for_target_slug(self):
        # this will catch when we forget to futz with target fields in param_info table
        param_name = ParamInfo.objects.get(slug='target').param_name()
        self.assertTrue(param_name, 'obs_general.planet_id')

    def test__all_has_slugs(self):
        # check all fields have slugs
        all_params = ParamInfo.objects.all()
        for param in all_params:
            self.assertGreater(len(param.slug), 0)




