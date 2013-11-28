"""
# metadata tests

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
    selections[param_name] = ['Saturn']

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


    def test_resultCount(self):
        response = self.c.get('/opus/result_count/?planet=Saturn')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, '{"result_count": 0}')

        response = self.c.get('/search/result_count/?planet=Jupiter')
        self.assertEqual(response.content, '{"result_count": 2000}')

        response = self.c.get('/search/result_count/?planet=Jupiter&target=SKY')
        self.assertEqual(response.content, '{"result_count": 12}')
        self.teardown()

        response = self.c.get('/search/result_count/?planet=Jupiter&target=IO,PANDORA')
        self.assertEqual(response.content, '{"result_count": 38}')
        self.teardown()

        # some range queries.. single no qtype (defaults any)
        response = self.c.get('/search/result_count/?ringradius1=60000&ringradius2=80000')
        self.assertEqual(response.content, '{"result_count": 187}')
        self.teardown()

        # qtype all
        response = self.c.get('/search/result_count/?ringradius1=60000&ringradius2=80000&qtype-ringradius=all')
        self.assertEqual(response.content, '{"result_count": 187}')
        self.teardown()

        # qtype only
        response = self.c.get('/search/result_count/?ringradius1=60000&ringradius2=80000&qtype-ringradius=only')
        self.assertEqual(response.content, '{"result_count": 0}')
        self.teardown()

        # mult ranges qtype only 1 given as all
        response = self.c.get('/search/result_count/?ringradius1=60000&ringradius2=80000,120000&qtype-ringradius=all')
        self.assertEqual(response.content, '{"result_count": 187}')
        self.teardown()

        # mission and general only
        response = self.c.get('/search/result_count/?planet=Jupiter&cassiniactivityname=catface')
        self.assertEqual(response.content, '{"result_count": 1592}')
        self.teardown()


    def test_getValidMults_planet(self):
        response = self.c.get('opus/mults/ids/?field=planet&planet=Jupiter')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, '{"mults": {"3": 2000}, "field": "planet"}')

    def test_getValidMults_target(self):
        response = self.c.get('/search/mults/ids/?field=target&planet=Jupiter')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, '{"mults": {"6": 11, "60": 5, "10": 54, "18": 8, "20": 81, "25": 38, "28": 1803}, "field": "target"}')
        self.teardown()

    def test_getValidMults_by_labels(self):
        # getting by labels
        response = self.c.get('/search/mults/labels/?field=target&planet=Jupiter')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, '{"mults": {"EUROPA": 8, "AMALTHEA": 11, "GANYMEDE": 81, "CALLISTO": 54, "JUPITER": 1803, "IO": 38, "THEBE": 5}, "field": "target"}')

