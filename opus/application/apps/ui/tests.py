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

from search.views import *
from results.views import *
from django.http import QueryDict

cursor = connection.cursor()

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_COOKIE_NAME = 'opus-test-cookie'
settings.CACHE_BACKEND = 'dummy:///'


class UITests(TestCase):

    # setup
    c = Client()
    param_name = 'obs_general.planet_id'
    selections = {}
    selections[param_name] = ['Jupiter']

    def test__getDataTable(self):
        response = self.c.get('/opus/__table_headers.html')
        print response.content
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.content), 1400)
        self.assertEqual(str(response.content).strip().find('<table class = "data_table'), 0 )

    def test__getWidget_planet_json(self):
        response = self.c.get('/opus/__forms/widget/planet.html')
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.content), 2000)
        self.assertEqual(str(response.content).strip().find('<div class="row'), 0 )

    def test__getWidget_target_json(self):
        response = self.c.get('/opus/__forms/widget/target.html')
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.content), 2000)
        self.assertEqual(str(response.content).strip().find('<div class="row'), 0 )

    def test__pluto_has_grouping_in_general_target_name(self):
        fields = [f.value for f in MultObsGeneralTargetName.objects.filter(grouping='OTHER')]
        print """
            if this fails you need to:

                update mult_obs_general_target_name set planet_group = 'PLU' where value = 'PLUTO';
                update mult_obs_surface_geometry_target_name set grouping = 'PLU' where value = 'PLUTO';

            """
        self.assertNotIn('PLUTO', fields)

    def test__pluto_has_grouping_in_surface_target_name(self):
        fields = [f.value for f in MultObsSurfaceGeometryTargetName.objects.filter(grouping='OTHER')]
        print """
            if this fails you need to:

                update mult_obs_general_target_name set planet_group = 'PLU' where value = 'PLUTO';
                update mult_obs_surface_geometry_target_name set grouping = 'PLU' where value = 'PLUTO';

            """
        self.assertNotIn('PLUTO', fields)

    """
    def test__getMenu(self):
        self.assertEqual(True, False)

    def test__getQuickPage(self):
        self.assertEqual(True, False)

    """

    def test__getDetailPage(self):
        response = self.c.get('/opus/api/detail/S_IMG_CO_ISS_1686170088_N.json')
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.content), 2000)


    """

    def test__getDetailQuick(self):
        self.assertEqual(True, False)

    def test__getDetailQuick(self):
        self.assertEqual(True, False)

    def test__getColumnChooser(self):
        self.assertEqual(True, False)

    """
