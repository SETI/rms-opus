# opus/application/search/test_db_integrity.py

from unittest import TestCase

from django.apps import apps
from django.db import connection
from django.db.models import Count
from django.http import QueryDict

from search.views import *
from tools.db_utils import MYSQL_TABLE_NOT_EXISTS

class DBIntegrityTest(TestCase):

    # Clean up the user_searches and cache tables before and after running
    # the tests so that the results from set_user_search_number and
    # get_user_query_table are predictable.

    def setUp(self):
        print('Running setup')
        cursor = connection.cursor()
        cursor.execute('DELETE FROM user_searches')
        cursor.execute("ALTER TABLE user_searches AUTO_INCREMENT = 1")
        cursor.execute("SHOW TABLES LIKE %s" , ["cache_%"])
        for row in cursor:
            q = 'DROP TABLE ' + row[0]
            print(q)
            cursor.execute(q)

    def teardown(self):
        assert False
        print('Running teardown')
        cursor = connection.cursor()
        cursor.execute('DELETE FROM user_searches')
        cursor.execute("ALTER TABLE user_searches AUTO_INCREMENT = 1")
        cursor.execute("SHOW TABLES LIKE %s" , ["cache_%"])
        for row in cursor:
            q = 'DROP TABLE ' + row[0]
            print(q)
            cursor.execute(q)


    # TODO: put tests here
    # def test__obs_surface_geometry_titan_sentinel_value(self):
    #     """
    #     """
    #     obs_surface_geometry_titan = ObsSurfaceGeometryTitan.objects.values()
    #     print(obs_surface_geometry_titan)
