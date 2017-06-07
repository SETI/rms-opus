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
# from django.test import TestCase  removed because it deletes test table data after every test
from unittest import TestCase
from django.test.client import Client
from django.test import RequestFactory

from search.views import *
from results.views import *
from django.http import QueryDict
from django.db.models import Count

cursor = connection.cursor()

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_COOKIE_NAME = 'opus-test-cookie'
settings.CACHE_BACKEND = 'dummy:///'

class ParamInfoTests(TestCase):

    # setup
    param_name = 'obs_general.planet_id'
    selections = {}
    selections[param_name] = ['Jupiter']

    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()

    def test__surface_geo_results_label_not_null(self):
        count = ParamInfo.objects.filter(category_name__contains="surface_geo", label_results='').count()
        print "you may need to \n update param_info set label_results = label where category_name like '%surface_geo%';"
        self.assertEqual(0, count)

    def test__surface_geo_all_exist(self):
        count_param_info = ParamInfo.objects.filter(category_name__contains="surface_geometry__").values('category_name').distinct().count()
        count_surface_geo = ObsSurfaceGeometry.objects.all().values('target_name').distinct().count()
        self.assertGreaterEqual(count_param_info, count_surface_geo)

    def test__primary_file_spec_has_form_type(self):
        form_type = ParamInfo.objects.get(name='primary_file_spec').form_type
        self.assertEqual(form_type, 'STRING')

    def test__param_name_for_target_slug(self):
        # this will catch when we forget to futz with target fields in param_info table
        param_name = ParamInfo.objects.get(slug='target').param_name()
        self.assertTrue(param_name, 'obs_general.planet_id')

    def test__all_has_slugs(self):
        # check all fields have slugs
        all_params = ParamInfo.objects.all()
        for param in all_params:
            self.assertGreater(len(param.slug), 0)

    def test_obs_general_time_fields_have_correct_form_type(self):
        count = len(ParamInfo.objects.filter(form_type='TIME', category_name='obs_general'))
        self.assertEqual(count, 2)
