"""
# results tests

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

from search.views import *
from results.views import *
from django.http import QueryDict

cursor = connection.cursor()

class metadataTests(TestCase):

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


    def test__getImages(self):
        response = self.c.get('/search/results/images/?planet=Jupiter')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.content), 42292)

