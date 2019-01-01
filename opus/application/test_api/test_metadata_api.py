# opus/application/test_api/test_metadata_api.py

import json
import requests
from unittest import TestCase

from django.db import connection
from rest_framework.test import RequestsClient

import settings

import logging
log = logging.getLogger(__name__)

cursor = connection.cursor()

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_COOKIE_NAME = 'opus-test-cookie'
settings.CACHE_BACKEND = 'dummy:///'

# url(r'^api/meta/result_count.(?P<fmt>[json|zip|html|csv]+)$', api_api_meta_result_count),
# url(r'^__api/meta/result_count.(?P<fmt>[json|zip|html|csv]+)$', api_api_meta_result_count),
# url(r'^api/meta/mults/(?P<slug>[-\w]+).(?P<fmt>[json|zip|html|csv]+)$', api_get_mult_counts),
# url(r'^__api/meta/mults/(?P<slug>[-\w]+).(?P<fmt>[json|zip|html|csv]+)$', api_get_mult_counts),
# url(r'^api/meta/range/endpoints/(?P<slug>[-\w]+).(?P<fmt>[json|zip|html|csv]+)$', api_get_range_endpoints),
# url(r'^__api/meta/range/endpoints/(?P<slug>[-\w]+).(?P<fmt>[json|zip|html|csv]+)$', api_get_range_endpoints),
# url(r'^api/fields/(?P<field>\w+).(?P<fmt>[json|zip|html|csv]+)$', api_get_fields),
# url(r'^__api/fields/(?P<field>\w+).(?P<fmt>[json|zip|html|csv]+)$', api_get_fields),
# url(r'^api/fields.(?P<fmt>[json|zip|html|csv]+)$', api_get_fields),
# url(r'^__api/fields.(?P<fmt>[json|zip|html|csv]+)$', api_get_fields),

class ApiMetadataTests(TestCase):
    GO_LIVE = False
    LIVE_TARGET = "production"

    # disable error logging and trace output before test
    def setUp(self):
        logging.disable(logging.ERROR)

    # enable error logging and trace output after test
    def tearDown(self):
        logging.disable(logging.NOTSET)

    def _get_response(self, url):
        if self.GO_LIVE:
            client = requests.Session()
        else:
            client = RequestsClient()
        if self.LIVE_TARGET == "production":
            url = "https://tools.pds-rings.seti.org" + url
        else:
            url = "http://dev.pds-rings.seti.org" + url
        return client.get(url)

    def _run_status_equal(self, url, expected):
        print(url)
        response = self._get_response(url)
        self.assertEqual(response.status_code, expected)

    def _run_json_equal(self, url, expected):
        print(url)
        response = self._get_response(url)
        self.assertEqual(response.status_code, 200)
        jdata = json.loads(response.content)
        print('Got:')
        print(str(jdata))
        print('Expected:')
        print(str(expected))
        self.assertEqual(expected, jdata)

    def _run_html_equal(self, url, expected):
        print(url)
        response = self._get_response(url)
        self.assertEqual(response.status_code, 200)
        print('Got:')
        print(str(response.content))
        print('Expected:')
        print(str(expected))
        self.assertEqual(expected, response.content)

    def _run_csv_equal(self, url, expected):
        print(url)
        response = self._get_response(url)
        self.assertEqual(response.status_code, 200)
        print('Got:')
        print(str(response.content))
        print('Expected:')
        print(str(expected))
        self.assertEqual(expected, response.content)

    def _run_result_count_equal(self, url, expected):
        print(url)
        response = self._get_response(url)
        self.assertEqual(response.status_code, 200)
        jdata = json.loads(response.content)
        result_count = int(jdata['data'][0]['result_count'])
        print(result_count)
        self.assertEqual(result_count, expected)

    def _run_result_count_greater(self, url, expected):
        print(url)
        response = self._get_response(url)
        self.assertEqual(response.status_code, 200)
        jdata = json.loads(response.content)
        result_count = int(jdata['data'][0]['result_count'])
        print(result_count)
        self.assertGreater(result_count, expected)

    def _run_mults_equal(self, url, expected, mult_name):
        print(url)
        response = self._get_response(url)
        self.assertEqual(response.status_code, 200)
        jdata = json.loads(response.content)
        result_count = int(jdata['mults'][mult_name])
        print(result_count)
        self.assertEqual(result_count, expected)


            ####################################################
            ######### /api/meta/result_count: API TESTS #########
            ####################################################

    def test__api_meta_result_count_all(self):
        "/api/meta/result_count: no search criteria"
        url = '/opus/__api/meta/result_count.json'
        self._run_result_count_greater(url, 1486) # Assume COISS_2111 at a minimum

    def test__api_meta_result_count_planet(self):
        "/api/meta/result_count: planet=Saturn"
        url = '/opus/__api/meta/result_count.json?planet=Saturn'
        self._run_result_count_greater(url, 1486) # Assume COISS_2111 at a minimum

    def test__api_meta_result_count_string_no_qtype(self):
        "/api/meta/result_count: primaryfilespec=1866365558 no qtype"
        url = '/opus/api/meta/result_count.json?primaryfilespec=1866365558'
        self._run_result_count_equal(url, 2) # BOTSIM

    def test__api_meta_result_count_string_contains(self):
        "/api/meta/result_count: primaryfilespec=1866365558 qtype=contains"
        url = '/opus/__api/meta/result_count.json?primaryfilespec=1866365558&qtype-primaryfilespec=contains'
        self._run_result_count_equal(url, 2) # BOTSIM

    def test__api_meta_result_count_string_begins(self):
        "/api/meta/result_count: primaryfilespec=1866365558 qtype=begins"
        url = '/opus/api/meta/result_count.json?primaryfilespec=1866365558&qtype-primaryfilespec=begins'
        self._run_result_count_equal(url, 0)

    def test__api_meta_result_count_string_ends(self):
        "/api/meta/result_count: primaryfilespec=1866365558_1.IMG qtype=ends"
        url = '/opus/api/meta/result_count.json?primaryfilespec=1866365558_1.IMG&qtype-primaryfilespec=ends'
        self._run_result_count_equal(url, 2)

    def test__api_meta_result_count_times(self):
        "/api/meta/result_count: time range"
        url = '/opus/__api/meta/result_count.json?planet=Saturn&volumeid=COISS_2111&timesec1=2017-03-01T00:00:00&timesec2=2017-03-15T12:00:00'
        self._run_result_count_equal(url, 1321)

    def test__api_meta_result_count_with_url_cruft(self):
        "/api/meta/result_count: with extra URL cruft"
        url = '/opus/api/meta/result_count.json?volumeid=COISS_2111&timesec1=2017-03-01T00:00:00&timesec2=2017-03-15T12:00:00&view=search&browse=data&colls_browse=gallery&page=1&gallery_data_viewer=true&limit=100&order=time1&cols=opusid,instrumentid,planet,target,time1,observationduration&widgets=timesec1,COISSshuttermode,volumeid,planet,target&widgets2=&detail='
        self._run_result_count_equal(url, 1321)

    def  test__api_meta_result_count_target_pan(self):
        "/api/meta/result_count: with target=Pan"
        url = '/opus/api/meta/result_count.json?volumeid=COISS_2111&target=PAN'
        self._run_result_count_equal(url, 56)

    def  test__api_meta_result_count_target_s_rings(self):
        "/api/meta/result_count: with target=S Rings"
        url = '/opus/api/meta/result_count.json?planet=Saturn&volumeid=COISS_2111&target=S+Rings'
        self._run_result_count_equal(url, 1040)

    def  test__api_meta_result_count_multi_target(self):
        "/api/meta/result_count: with target=Iapetus,Methone"
        url = '/opus/api/meta/result_count.json?planet=Saturn&volumeid=COISS_2111&target=Iapetus,Methone'
        self._run_result_count_equal(url, 129)

    def  test__api_meta_result_count_ring_rad_range(self):
        "/api/meta/result_count: with ring radius range, no qtype"
        url = '/opus/api/meta/result_count.json?volumeid=COISS_2111&RINGGEOringradius1=70000&RINGGEOringradius2=80000'
        self._run_result_count_equal(url, 490)

    def  test__api_meta_result_count_ring_rad_range_all(self):
        "/api/meta/result_count: with ring radius range, qtype=all"
        url = '/opus/api/meta/result_count.json?volumeid=COISS_2111&RINGGEOringradius1=70000&RINGGEOringradius2=80000&qtype-RINGGEOringradius=all'
        self._run_result_count_equal(url, 217)

    def  test__api_meta_result_count_ring_rad_range_only(self):
        "/api/meta/result_count: with ring radius range, qtype=only"
        url = '/opus/api/meta/result_count.json?volumeid=COISS_2111&RINGGEOringradius1=70000&RINGGEOringradius2=80000&qtype-RINGGEOringradius=only'
        self._run_result_count_equal(url, 26)

    def  test__api_meta_result_count_bad_slug(self):
        "/api/meta/result_count: with bad slug"
        url = '/opus/api/meta/result_count.json?volumeid=COISS_2111&RINGGEOringradius1=70000&RINGGEOringradius3=80000&qtype-RINGGEOringradius=only'
        self._run_status_equal(url, 404)

    def  test__api_meta_result_count_bad_value(self):
        "/api/meta/result_count: with bad value"
        url = '/opus/api/meta/result_count.json?observationduration1=1X2'
        self._run_status_equal(url, 404)

    def test__api_meta_result_count_html(self):
        "/api/meta/result_count: primaryfilespec=1866365558 no qtype"
        url = '/opus/api/meta/result_count.html?primaryfilespec=1866365558'
        expected = b'<body>\n\t<dl>\n\t\t\n\t    <dt>result_count</dt><dd>2</dd>\n\t\t\n\t</dl>\n</body>\n'
        self._run_html_equal(url, expected) # BOTSIM

    def test__api_meta_result_count_csv(self):
        "/api/meta/result_count: primaryfilespec=1866365558 no qtype"
        url = '/opus/api/meta/result_count.csv?primaryfilespec=1866365558'
        expected = b'result count,2\r\n'
        self._run_csv_equal(url, expected) # BOTSIM


            #######################################################
            ######### /api/meta/range/endpoints: API TESTS #########
            #######################################################

    ##################################
    ### General / OBSERVATION TIME ###
    ##################################

    def test__api_meta_range_endpoints_times_COISS(self):
        "/api/meta/range/endpoints: times COISS"
        url = '/opus/__api/meta/range/endpoints/timesec1.json?volumeid=COISS_2111'
        expected = {"max": "2017-03-31T13:05:35.059", "nulls": 0, "min": "2017-02-17T23:59:39.059"}
        self._run_json_equal(url, expected)

    def test__api_meta_range_endpoints_times_COUVIS(self):
        "/api/meta/range/endpoints: times COUVIS"
        url = '/opus/__api/meta/range/endpoints/timesec1.json?volumeid=COUVIS_0002'
        expected = {"max": "2001-04-01T00:07:19.842", "nulls": 0, "min": "2001-01-01T02:12:02.721"}
        self._run_json_equal(url, expected)

    def test__api_meta_range_endpoints_times_COVIMS(self):
        "/api/meta/range/endpoints: times COVIMS"
        url = '/opus/__api/meta/range/endpoints/timesec1.json?volumeid=COVIMS_0006'
        expected = {"max": "2005-04-01T00:06:46.867", "nulls": 0, "min": "2005-01-15T17:55:38.899"}
        self._run_json_equal(url, expected)

    def test__api_meta_range_endpoints_times_GOSSI(self):
        "/api/meta/range/endpoints: times GOSSI"
        url = '/opus/__api/meta/range/endpoints/timesec1.json?volumeid=GO_0017'
        expected = {"max": "1996-12-14T17:30:37.354", "nulls": 0, "min": "1996-06-03T17:05:38.002"}
        self._run_json_equal(url, expected)

    def test__api_meta_range_endpoints_times_VGISS(self):
        "/api/meta/range/endpoints: times VGISS"
        url = '/opus/__api/meta/range/endpoints/timesec1.json?volumeid=VGISS_6210'
        expected = {"max": "1981-08-15T22:17:36.000", "nulls": 0, "min": "1981-08-12T14:55:10.080"}
        self._run_json_equal(url, expected)

    def test__api_meta_range_endpoints_times_HSTI(self):
        "/api/meta/range/endpoints: times HSTI"
        url = '/opus/__api/meta/range/endpoints/timesec1.json?volumeid=HSTI1_2003'
        expected = {"max": "2009-08-08T23:13:10.000", "nulls": 0, "min": "2009-07-23T18:12:25.000"}
        self._run_json_equal(url, expected)

    ######################################
    ### General / OBSERVATION DURATION ###
    ######################################

    def test__api_meta_range_endpoints_observation_duration_VGISS(self):
        "/api/meta/range/endpoints: observation duration VGISS"
        url = '/opus/__api/meta/range/endpoints/observationduration1.json?volumeid=VGISS_6210'
        expected = {'min': '0.2400', 'max': '15.3600', 'nulls': 0}
        self._run_json_equal(url, expected)

    #################################
    ### General / RIGHT ASCENSION ###
    #################################

    #############################
    ### General / DECLINATION ###
    #############################


    ##########################
    ### Image / PIXEL SIZE ###
    ##########################

    def test__api_meta_range_endpoints_COISS_greaterpixelsize1(self):
        "/api/meta/range/endpoints: greaterpixelsize1 COISS"
        url = '/opus/__api/meta/range/endpoints/greaterpixelsize1.json?instrument=Cassini+ISS'
        expected = {'max': '1024', 'min': '256', 'nulls': 0}
        self._run_json_equal(url, expected)

    def test__api_meta_range_endpoints_COISS_greaterpixelsize2(self):
        "/api/meta/range/endpoints: greaterpixelsize2 COISS"
        url = '/opus/api/meta/range/endpoints/greaterpixelsize2.json?instrument=Cassini+ISS'
        expected = {'min': '256', 'max': '1024', 'nulls': 0}
        self._run_json_equal(url, expected)

    def test__api_meta_range_endpoints_COISS_lesserpixelsize1(self):
        "/api/meta/range/endpoints: lesserpixelsize1 COISS"
        url = '/opus/api/meta/range/endpoints/lesserpixelsize1.json?instrument=Cassini+ISS'
        expected = {'min': '256', 'max': '1024', 'nulls': 0}
        self._run_json_equal(url, expected)

    def test__api_meta_range_endpoints_COISS_lesserpixelsize2(self):
        "/api/meta/range/endpoints: lesserpixelsize2 COISS"
        url = '/opus/__api/meta/range/endpoints/lesserpixelsize2.json?instrument=Cassini+ISS'
        expected = {'min': '256', 'max': '1024', 'nulls': 0}
        self._run_json_equal(url, expected)

    def test__api_meta_range_endpoints_GOSSI_greaterpixelsize1(self):
        "/api/meta/range/endpoints: greaterpixelsize1 GOSSI"
        url = '/opus/__api/meta/range/endpoints/greaterpixelsize1.json?instrument=Galileo+SSI'
        expected = {'min': '800', 'max': '800', 'nulls': 0}
        self._run_json_equal(url, expected)

    def test__api_meta_range_endpoints_GOSSI_lesserpixelsize1(self):
        "/api/meta/range/endpoints: greaterpixelsize1 GOSSI"
        url = '/opus/__api/meta/range/endpoints/lesserpixelsize1.json?instrument=Galileo+SSI'
        expected = {'min': '800', 'max': '800', 'nulls': 0}
        self._run_json_equal(url, expected)

    # We don't do greater/lesserpixelsize for VGISS because it can change in
    # different volumes.

    ################################
    ### Image / INTENSITY LEVELS ###
    ################################

    def test__api_meta_range_endpoints_COISS_levels1(self):
        "/api/meta/range/endpoints: levels1 COISS"
        url = '/opus/__api/meta/range/endpoints/levels1.json?instrument=Cassini+ISS'
        expected = {'min': '4096', 'max': '4096', 'nulls': 0}
        self._run_json_equal(url, expected)

    def test__api_meta_range_endpoints_COVIMS_levels1(self):
        "/api/meta/range/endpoints: levels1 COVIMS"
        url = '/opus/__api/meta/range/endpoints/levels1.json?instrument=Cassini+VIMS'
        expected = {'min': '4096', 'max': '4096', 'nulls': 0}
        self._run_json_equal(url, expected)

    def test__api_meta_range_endpoints_GOSSI_levels1(self):
        "/api/meta/range/endpoints: levels1 GOSSI"
        url = '/opus/__api/meta/range/endpoints/levels1.json?instrument=Galileo+SSI'
        expected = {'min': '256', 'max': '256', 'nulls': 0}
        self._run_json_equal(url, expected)

    def test__api_meta_range_endpoints_VGISS_levels1(self):
        "/api/meta/range/endpoints: levels1 VGISS"
        url = '/opus/__api/meta/range/endpoints/levels1.json?instrument=Voyager+ISS'
        expected = {'min': '256', 'max': '256', 'nulls': 0}
        self._run_json_equal(url, expected)

    ########################
    ### Error Conditions ###
    ########################

    def test__api_meta_range_endpoints_bad_slug(self):
        "/api/meta/range/endpoints: bad slug name"
        url = '/opus/__api/meta/range/endpoints/badslug.json?instrument=Cassini+ISS'
        self._run_status_equal(url, 404)


            ##############################################
            ######### /api/meta/mults UNIT TESTS #########
            ##############################################

    def test__api_meta_mults_COISS_2111(self):
        "/api/meta/meta/mults: for COISS_2111"
        url = '/opus/api/meta/mults/target.json?volumeid=COISS_2111&planet=Saturn'
        self._run_mults_equal(url, 2, 'Polydeuces')

    def test__api_meta_mults_bad_param(self):
        "/api/meta/mults: bad parameter"
        url = '/opus/api/meta/mults/target.json?volumeid=COISS_2111&planetx=Saturn'
        self._run_status_equal(url, 404)
