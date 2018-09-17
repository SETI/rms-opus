# metadata/test.py

import json
from unittest import TestCase

from django.db import connection
from django.test.client import Client

from metadata.views import *

import logging
log = logging.getLogger(__name__)

cursor = connection.cursor()

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_COOKIE_NAME = 'opus-test-cookie'
settings.CACHE_BACKEND = 'dummy:///'

# url(r'^api/meta/result_count.(?P<fmt>[json|zip|html|csv]+)$', api_get_result_count),
# url(r'^__api/meta/result_count.(?P<fmt>[json|zip|html|csv]+)$', api_get_result_count),
# url(r'^api/meta/mults/(?P<slug>[-\w]+).(?P<fmt>[json|zip|html|csv]+)$', api_get_mult_counts),
# url(r'^__api/meta/mults/(?P<slug>[-\w]+).(?P<fmt>[json|zip|html|csv]+)$', api_get_mult_counts),
# url(r'^api/meta/range/endpoints/(?P<slug>[-\w]+).(?P<fmt>[json|zip|html|csv]+)$', api_get_range_endpoints),
# url(r'^__api/meta/range/endpoints/(?P<slug>[-\w]+).(?P<fmt>[json|zip|html|csv]+)$', api_get_range_endpoints),
# url(r'^api/fields/(?P<field>\w+).(?P<fmt>[json|zip|html|csv]+)$', api_get_fields),
# url(r'^__api/fields/(?P<field>\w+).(?P<fmt>[json|zip|html|csv]+)$', api_get_fields),
# url(r'^api/fields.(?P<fmt>[json|zip|html|csv]+)$', api_get_fields),
# url(r'^__api/fields.(?P<fmt>[json|zip|html|csv]+)$', api_get_fields),

class metadataTests(TestCase):

    c = Client()


    def test__get_range_endpoints_times(self):
        "Range endpoints times."
        response = self.c.get('/opus/__api/meta/range/endpoints/timesec1.json?volumeid=COISS_2111')
        self.assertEqual(response.status_code, 200)
        jdata = json.loads(response.content)
        expected = {"max": "2017-03-31T13:05:35.059", "nulls": 0, "min": "2017-02-17T23:59:39.059"}
        print('got:')
        print(str(jdata))
        print('expected:')
        print(str(expected))
        self.assertEqual(expected, jdata)

    def test__get_range_endpoints_COISS_greaterpixelsize1(self):
        "Range endpoints greaterpixelsize1."
        response = self.c.get('/opus/__api/meta/range/endpoints/greaterpixelsize1.json?instrumentid=Cassini+ISS')
        self.assertEqual(response.status_code, 200)
        jdata = json.loads(response.content)
        expected = {"max": 1024.0, "nulls": 0, "min": 256.0}
        print('got:')
        print(str(jdata))
        print('expected:')
        print(str(expected))
        self.assertEqual(expected, jdata)

    def test__get_range_endpoints_COISS_greaterpixelsize2(self):
        "Range endpoints greaterpixelsize1."
        response = self.c.get('/opus/api/meta/range/endpoints/greaterpixelsize2.json?instrumentid=Cassini+ISS')
        self.assertEqual(response.status_code, 200)
        jdata = json.loads(response.content)
        expected = {"max": 1024.0, "nulls": 0, "min": 256.0}
        print('got:')
        print(str(jdata))
        print('expected:')
        print(str(expected))
        self.assertEqual(expected, jdata)

    def test__get_range_endpoints_COISS_lesserpixelsize1(self):
        "Range endpoints lesserpixelsize1."
        response = self.c.get('/opus/api/meta/range/endpoints/lesserpixelsize1.json?instrumentid=Cassini+ISS')
        self.assertEqual(response.status_code, 200)
        jdata = json.loads(response.content)
        expected = {"max": 1024.0, "nulls": 0, "min": 256.0}
        print('got:')
        print(str(jdata))
        print('expected:')
        print(str(expected))
        self.assertEqual(expected, jdata)

    def test__get_range_endpoints_COISS_lesserpixelsize2(self):
        "Range endpoints lesserpixelsize1."
        response = self.c.get('/opus/__api/meta/range/endpoints/lesserpixelsize2.json?instrumentid=Cassini+ISS')
        self.assertEqual(response.status_code, 200)
        jdata = json.loads(response.content)
        expected = {"max": 1024.0, "nulls": 0, "min": 256.0}
        print('got:')
        print(str(jdata))
        print('expected:')
        print(str(expected))
        self.assertEqual(expected, jdata)

    def test_get_result_count_planet(self):
        "Result count planet=Saturn."
        response = self.c.get('/opus/__api/meta/result_count.json?planet=Saturn')
        self.assertEqual(response.status_code, 200)
        jdata = json.loads(response.content)
        result_count = int(jdata['data'][0]['result_count'])
        print(result_count)
        self.assertGreater(result_count, 1486) # Assume COISS_2111 at a minimum

    def test_get_result_count_string_no_qtype(self):
        "Result count primaryfilespec=1866365558 no qtype."
        response = self.c.get('/opus/api/meta/result_count.json?primaryfilespec=1866365558')
        self.assertEqual(response.status_code, 200)
        jdata = json.loads(response.content)
        result_count = int(jdata['data'][0]['result_count'])
        print(result_count)
        self.assertEqual(result_count, 2) # BOTSIM

    def test_get_result_count_string_contains(self):
        "Result count primaryfilespec=1866365558 qtype=contains."
        response = self.c.get('/opus/__api/meta/result_count.json?primaryfilespec=1866365558&qtype-primaryfilespec=contains')
        self.assertEqual(response.status_code, 200)
        jdata = json.loads(response.content)
        result_count = int(jdata['data'][0]['result_count'])
        print(result_count)
        self.assertEqual(result_count, 2) # BOTSIM

    def test_get_result_count_string_begins(self):
        "Result count primaryfilespec=1866365558 qtype=begins."
        response = self.c.get('/opus/api/meta/result_count.json?primaryfilespec=1866365558&qtype-primaryfilespec=begins')
        self.assertEqual(response.status_code, 200)
        jdata = json.loads(response.content)
        result_count = int(jdata['data'][0]['result_count'])
        print(result_count)
        self.assertEqual(result_count, 0)

    def test_get_result_count_times(self):
        "Result count time range."
        response = self.c.get('/opus/__api/meta/result_count.json?planet=Saturn&volumeid=COISS_2111&timesec1=2017-03-01T00:00:00&timesec2=2017-03-15T12:00:00')
        print(response.content)
        self.assertEqual(response.status_code, 200)
        jdata = json.loads(response.content)
        result_count = int(jdata['data'][0]['result_count'])
        print(result_count)
        self.assertEqual(result_count, 1321)

    def test__get_result_count_with_url_cruft(self):
        "Result count with extra URL cruft."
        url = '/opus/api/meta/result_count.json?volumeid=COISS_2111&timesec1=2017-03-01T00:00:00&timesec2=2017-03-15T12:00:00&view=search&browse=data&colls_browse=gallery&page=1&gallery_data_viewer=true&limit=100&order=time1&cols=opusid,instrumentid,planet,target,time1,observationduration&widgets=timesec1,COISSshuttermode,volumeid,planet,target&widgets2=&detail='
        print(url)
        response = self.c.get(url)
        print(response.content)
        self.assertEqual(response.status_code, 200)
        jdata = json.loads(response.content)
        result_count = int(jdata['data'][0]['result_count'])
        print(result_count)
        self.assertEqual(result_count, 1321)

    def test_result_count_target_pan(self):
        "Result count with target=Pan."
        url = '/opus/api/meta/result_count.json?volumeid=COISS_2111&target=PAN'
        print(url)
        response = self.c.get(url)
        print(response.content)
        self.assertEqual(response.status_code, 200)
        jdata = json.loads(response.content)
        result_count = int(jdata['data'][0]['result_count'])
        print(result_count)
        self.assertEqual(result_count, 56)

    def test_result_count_target_s_rings(self):
        "Result count with target=S Rings."
        url = '/opus/api/meta/result_count.json?planet=Saturn&volumeid=COISS_2111&target=S+Rings'
        print(url)
        response = self.c.get(url)
        print(response.content)
        self.assertEqual(response.status_code, 200)
        jdata = json.loads(response.content)
        result_count = int(jdata['data'][0]['result_count'])
        print(result_count)
        self.assertEqual(result_count, 1036)

    def test_result_count_multi_target(self):
        "Result count with target=Iapetus,Methone."
        url = '/opus/api/meta/result_count.json?planet=Saturn&volumeid=COISS_2111&target=Iapetus,Methone'
        print(url)
        response = self.c.get(url)
        print(response.content)
        self.assertEqual(response.status_code, 200)
        jdata = json.loads(response.content)
        result_count = int(jdata['data'][0]['result_count'])
        print(result_count)
        self.assertEqual(result_count, 129)

    def test_result_count_ring_rad_range(self):
        "Result count with ring radius range, no qtype."
        # some range queries.. single no qtype (defaults any)
        response = self.c.get('/opus/api/meta/result_count.json?volumeid=COISS_2111&RINGGEOringradius1=70000&RINGGEOringradius2=80000')
        print(response.content)
        self.assertEqual(response.status_code, 200)
        jdata = json.loads(response.content)
        result_count = int(jdata['data'][0]['result_count'])
        print(result_count)
        self.assertEqual(result_count, 490)

    def test_result_count_ring_rad_range_all(self):
        "Result count with ring radius range, qtype=all."
        # some range queries.. single no qtype (defaults any)
        response = self.c.get('/opus/api/meta/result_count.json?volumeid=COISS_2111&RINGGEOringradius1=70000&RINGGEOringradius2=80000&qtype-RINGGEOringradius=all')
        print(response.content)
        self.assertEqual(response.status_code, 200)
        jdata = json.loads(response.content)
        result_count = int(jdata['data'][0]['result_count'])
        print(result_count)
        self.assertEqual(result_count, 217)

    def test_result_count_ring_rad_range_only(self):
        "Result count with ring radius range, qtype=only."
        # some range queries.. single no qtype (defaults any)
        response = self.c.get('/opus/api/meta/result_count.json?volumeid=COISS_2111&RINGGEOringradius1=70000&RINGGEOringradius2=80000&qtype-RINGGEOringradius=only')
        print(response.content)
        self.assertEqual(response.status_code, 200)
        jdata = json.loads(response.content)
        result_count = int(jdata['data'][0]['result_count'])
        print(result_count)
        self.assertEqual(result_count, 26)

    def test_result_count_bad_param(self):
        "Result count with bad parameter."
        # some range queries.. single no qtype (defaults any)
        response = self.c.get('/opus/api/meta/result_count.json?volumeid=COISS_2111&RINGGEOringradius1=70000&RINGGEOringradius3=80000&qtype-RINGGEOringradius=only')
        print(response.content)
        self.assertEqual(response.status_code, 404)

    def test_get_valid_mults_COISS_2111(self):
        "Mults for COISS_2111."
        response = self.c.get('/opus/api/meta/mults/target.json?volumeid=COISS_2111&planet=Saturn')
        print(response.content)
        self.assertEqual(response.status_code, 200)
        jdata = json.loads(response.content)
        result_count = int(jdata['mults']['Polydeuces'])
        print(result_count)
        self.assertEqual(result_count, 2)

    def test_get_valid_mults_bad_param(self):
        "Mults with bad parameter."
        response = self.c.get('/opus/api/meta/mults/target.json?volumeid=COISS_2111&planetx=Saturn')
        print(response.content)
        self.assertEqual(response.status_code, 404)
