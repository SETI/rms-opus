"""
# metadata tests

"""
from django.test import TestCase
from django.test.client import Client
from django.db import connection

from metadata.views import *

"""
from search.views import *
from results.views import *
"""

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


    def test_obs_general_time_fields_have_correct_form_type(self):
        print 'hello'
        q = "select count(*) from param_info where form_type = 'TIME' and category_name = 'obs_general'"
        print q
        cursor.execute(q)
        print 'ok'
        c = cursor.numrows(q)
        print c
        print 'that was c'
        self.assertEqual(c, 2)

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
        response = self.c.get('/opus/api/meta/result_count.json?planet=Saturn&view=search&page=1&colls_page=1&limit=100&widgets=planet,target&widgets2=&browse=gallery&colls_browse=gallery&detail=&order=&cols=&reqno=1')
        print response.content
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, '{"data": [{"result_count": 11373}]}')


    def test_result_count_target_PAN(self):
        response = self.c.get('/opus/api/meta/result_count.json?planet=Saturn&target=PANDORA')
        print response.content
        self.assertEqual(response.content, '{"data": [{"result_count": 23}]}')

    def test_result_count_target_SKY(self):
        response = self.c.get('/opus/api/meta/result_count.json?planet=Saturn&target=SKY')
        print response.content
        self.assertEqual(response.content, '{"data": [{"result_count": 1635}]}')
        self.teardown()

    def test_result_count_multi_target(self):
        response = self.c.get('/opus/api/meta/result_count.json?planet=Saturn&target=IO,PANDORA')
        print response.content
        self.assertEqual(response.content, '{"data": [{"result_count": 23}]}')
        self.teardown()

    def test_result_count_ring_rad_range(self):
        # some range queries.. single no qtype (defaults any)
        response = self.c.get('/opus/api/meta/result_count.json?ringradius1=60000&ringradius2=80000')
        print response.content
        self.assertEqual(response.content, '{"data": [{"result_count": 1422}]}')
        self.teardown()

    def test_result_count_ring_rad_range_qtype_all(self):
        response = self.c.get('/opus/api/meta/result_count.json?ringradius1=60000&ringradius2=80000&qtype-ringradius=all')
        print response.content
        self.assertEqual(response.content, '{"data": [{"result_count": 1138}]}')
        self.teardown()

    def test_result_count_ring_rad_range_qtype_only(self):
        # qtype only
        response = self.c.get('/opus/api/meta/result_count.json?ringradius1=60000&ringradius2=80000&qtype-ringradius=only')
        print response.content
        self.assertEqual(response.content, '{"data": [{"result_count": 0}]}')
        self.teardown()

    def test_result_count_multi_range_single_qtype(self):
        # mult ranges qtype only 1 given as all
        response = self.c.get('/opus/api/meta/result_count.json?ringradius1=60000&ringradius2=80000,120000&qtype-ringradius=all')
        print response.content
        self.assertEqual(response.content, '{"data": [{"result_count": 7904}]}')
        self.teardown()

    def test_result_count_mission_general_only(self):
        # mission and general only
        response = self.c.get('/opus/api/meta/result_count.json?planet=Neptune&missionid=VG')
        print response.content
        self.assertEqual(response.content, '{"data": [{"result_count": 1360}]}')
        self.teardown()

    def test_result_count_empty_result_set(self):
        # mission and general only
        response = self.c.get('/opus/api/meta/result_count.json?planet=Saturn&missionid=VGISS')
        print response.content
        self.assertEqual(response.content, '{"data": [{"result_count": 0}]}')
        self.teardown()


    def test_getValidMults_planet_SAT_for_target(self):
        response = self.c.get('/opus/api/meta/mults/target.json?planet=Saturn')
        print response.content
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, '{"mults": {"UNKNOWN": 196, "PAALIAQ": 465, "SKY": 1635, "METHONE": 20, "JANUS": 29, "EPIMETHEUS": 23, "ATLAS": 28, "SATURN": 3083, "SUTTUNGR": 125, "DIONE": 180, "TITAN": 2269, "SUN": 48, "HYPERION": 232, "CALYPSO": 25, "PALLENE": 40, "TETHYS": 74, "S RINGS": 786, "POLYDEUCES": 35, "PANDORA": 23, "S12_2004": 145, "ENCELADUS": 406, "TELESTO": 24, "PROMETHEUS": 107, "ANTHE": 22, "RHEA": 81, "TARQEQ": 97, "IAPETUS": 1022, "HELENE": 153}, "field": "target"}')

    def test_getValidMults_planet_sat_for_planet(self):
        response = self.c.get('/opus/api/meta/mults/planet.json?planet=Saturn')
        print response.content
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, '{"mults": {"Saturn": 11373, "Neptune": 1360}, "field": "planet"}')
        self.teardown()


        """

    def test_getValidMults_by_labels(self):
        # getting by labels
        response = self.c.get('/opus/api/meta/mults/labels/?field=target&planet=Saturn')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, '{"mults": {"EUROPA": 8, "AMALTHEA": 11, "GANYMEDE": 81, "CALLISTO": 54, "Saturn": 1803, "IO": 38, "THEBE": 5}, "field": "target"}')
        """
