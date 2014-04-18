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

class UITests(TestCase):

    # setup
    c = Client()
    param_name = 'obs_general.planet_id'
    selections = {}
    selections[param_name] = ['Jupiter']

    def teardown(self):
        cursor = connection.cursor()
        cursor.execute("delete from user_searches")
        cursor.execute("ALTER TABLE user_searches AUTO_INCREMENT = 1")
        cursor.execute("show tables like %s " , ["cache%"])
        print "running teardown"
        for row in cursor:
            q = 'drop table ' + row[0]
            print q
            cursor.execute(q)

    def test__mainSite(self):
        response = self.c.get('/opus/')
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.content), 104098)

    #
    def test__getDataTable(self):
        response = self.c.get('/opus/table_headers.html')
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.content), 2000)
        self.assertEqual(str(response.content).strip().find('<table class = "data_table">'), 0 )

    def test__getWidget_planet_json(self):
        response = self.c.get('/opus/forms/widget/planet.html')
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.content), 2000)
        self.assertEqual(str(response.content).strip().find('<div class = "widget_draghandle">'), 0 )

    def test__getWidget_target_json(self):
        response = self.c.get('/opus/forms/widget/target.html')
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.content), 2000)
        self.assertEqual(str(response.content).strip().find('<div class = "widget_draghandle">'), 0 )

    """
    def test__getMenu(self):
        self.assertEqual(True, False)

    def test__getQuickPage(self):
        self.assertEqual(True, False)

    """

    def test__getDetailPage(self):
        response = self.c.get('/opus/api/detailpage/S_IMG_CO_ISS_1686170088_N.json')
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.content), 2000)


    """
    def test__getColumnLabels(self):
        self.assertEqual(True, False)


    def test__getDetailQuick(self):
        self.assertEqual(True, False)

    def test__getDetailQuick(self):
        self.assertEqual(True, False)

    def test__getColumnChooser(self):
        self.assertEqual(True, False)

    """



