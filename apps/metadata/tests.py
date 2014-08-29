"""
# metadata tests

"""
import json
from django.test import TestCase
from django.test.client import Client
from django.db import connection

from metadata.views import *

cursor = connection.cursor()

class metadataTests(TestCase):

    c = Client()
    param_name = 'obs_general.planet_id'
    selections = {}
    selections[param_name] = ['Saturn']

    def test__getRangeEndpoints_times(self):
        url = '/opus/api/meta/range/endpoints/timesec1.json?planet=Saturn&view=search&browse=gallery&colls_browse=gallery&page=1&limit=100&order=&cols=ringobsid,planet,target,phase1&widgets=planet,target,timesec1&widgets2=&detail=&reqno=1'
        print url
        response = self.c.get(url)
        print 'got:'
        print response.content
        expected = '{"max": "2011-269T19:59:13.124", "nulls": 0, "min": "2009-09-01T00:00:01"}'
        print 'expected:'
        print expected
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, expected)

    def test_getResultCount(self):
        response = self.c.get('/opus/api/meta/result_count.json?planet=Saturn')
        print response.content
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, '{"data": [{"result_count": 11373}]}')

    def test_getResultCount_times(self):
        response = self.c.get('/opus/api/meta/result_count.json?planet=Saturn&timesec1=2009-12-23&timesec2=2009-12-28')
        print response.content
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, '{"data": [{"result_count": 882}]}')

    def test_resultcount_with_url_cruft(self):
        url = '/opus/api/meta/result_count.json?planet=Saturn&view=search&page=1&colls_page=1&limit=100&widgets=planet,target&widgets2=&browse=gallery&colls_browse=gallery&detail=&order=&cols=&reqno=1'
        print url
        response = self.c.get(url)
        print response.content
        self.assertEqual(response.status_code, 200)

        jdata = json.loads(response.content)
        result_count = int(jdata['data'][0]['result_count'])
        print result_count
        self.assertGreater(result_count, 11000)


    def test_result_count_target_PAN(self):
        response = self.c.get('/opus/api/meta/result_count.json?planet=Saturn&target=PANDORA')
        jdata = json.loads(response.content)
        result_count = int(jdata['data'][0]['result_count'])
        print result_count
        self.assertGreater(result_count, 20)

    def test_result_count_target_SKY(self):
        response = self.c.get('/opus/api/meta/result_count.json?planet=Saturn&target=SKY')
        print response.content
        jdata = json.loads(response.content)
        result_count = int(jdata['data'][0]['result_count'])
        print result_count
        self.assertGreater(result_count, 1500)

    def test_result_count_multi_target(self):
        response = self.c.get('/opus/api/meta/result_count.json?planet=Saturn&target=IO,PANDORA')
        print response.content
        jdata = json.loads(response.content)
        result_count = int(jdata['data'][0]['result_count'])
        print result_count
        self.assertGreater(result_count, 22)

    def test_result_count_ring_rad_range(self):
        # some range queries.. single no qtype (defaults any)
        response = self.c.get('/opus/api/meta/result_count.json?ringradius1=60000&ringradius2=80000')
        print response.content
        jdata = json.loads(response.content)
        result_count = int(jdata['data'][0]['result_count'])
        print result_count
        self.assertGreater(result_count, 1400)

    def test_result_count_ring_rad_range_qtype_all(self):
        response = self.c.get('/opus/api/meta/result_count.json?ringradius1=60000&ringradius2=80000&qtype-ringradius=all')
        print response.content
        jdata = json.loads(response.content)
        result_count = int(jdata['data'][0]['result_count'])
        print result_count
        self.assertGreater(result_count, 1100)

    def test_result_count_ring_rad_range_qtype_only(self):
        # qtype only
        response = self.c.get('/opus/api/meta/result_count.json?ringradius1=60000&ringradius2=80000&qtype-ringradius=only')
        jdata = json.loads(response.content)
        result_count = int(jdata['data'][0]['result_count'])
        print result_count
        self.assertEqual(result_count, 0)

    def test_result_count_multi_range_single_qtype(self):
        # mult ranges qtype only 1 given as all
        response = self.c.get('/opus/api/meta/result_count.json?ringradius1=60000&ringradius2=80000,120000&qtype-ringradius=all')
        jdata = json.loads(response.content)
        result_count = int(jdata['data'][0]['result_count'])
        print result_count
        self.assertGreater(result_count, 7900)

    def test_result_count_mission_general_only(self):
        # mission and general only
        response = self.c.get('/opus/api/meta/result_count.json?planet=Neptune&missionid=VG')
        jdata = json.loads(response.content)
        result_count = int(jdata['data'][0]['result_count'])
        print result_count
        self.assertGreater(result_count, 1300)

    def test_result_count_empty_result_set(self):
        # mission and general only
        response = self.c.get('/opus/api/meta/result_count.json?planet=Saturn&missionid=VGISS')
        jdata = json.loads(response.content)
        result_count = int(jdata['data'][0]['result_count'])
        print result_count
        self.assertEqual(result_count, 0)


    def test_getValidMults_planet_SAT_for_target(self):
        response = self.c.get('/opus/api/meta/mults/target.json?planet=Saturn')
        print response.content
        self.assertEqual(response.status_code, 200)
        jdata = json.loads(response.content)
        result_count = int(jdata['mults']['PAALIAQ'])
        print result_count
        self.assertGreater(result_count, 450)


    def test_getValidMults_planet_sat_for_planet(self):
        response = self.c.get('/opus/api/meta/mults/planet.json?planet=Saturn')
        print response.content
        self.assertEqual(response.status_code, 200)

        jdata = json.loads(response.content)
        result_count = int(jdata['mults']['Saturn'])
        print result_count
        self.assertGreater(result_count, 11370)

        """

    def test_getValidMults_by_labels(self):
        # getting by labels
        response = self.c.get('/opus/api/meta/mults/labels/?field=target&planet=Saturn')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, '{"mults": {"EUROPA": 8, "AMALTHEA": 11, "GANYMEDE": 81, "CALLISTO": 54, "Saturn": 1803, "IO": 38, "THEBE": 5}, "field": "target"}')
        """
