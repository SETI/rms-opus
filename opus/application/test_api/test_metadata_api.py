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

    # disable error logging and trace output before test
    def setUp(self):
        settings.CACHE_KEY_PREFIX = 'opustest:' + settings.OPUS_SCHEMA_NAME
        logging.disable(logging.ERROR)
        if settings.TEST_GO_LIVE:
            self.client = requests.Session()
        else:
            self.client = RequestsClient()

    # enable error logging and trace output after test
    def tearDown(self):
        logging.disable(logging.NOTSET)

    def _get_response(self, url):
        if not settings.TEST_GO_LIVE or settings.TEST_GO_LIVE == "production":
            url = "https://tools.pds-rings.seti.org" + url
        else:
            url = "http://dev.pds-rings.seti.org" + url
        return self.client.get(url)

    def _run_status_equal(self, url, expected, err_string=None):
        print(url)
        response = self._get_response(url)
        self.assertEqual(response.status_code, expected)
        # XXX Fix this once we have a proper 404 page
        # if err_string:
        #     print(response.content)
        #     self.assertEqual(response.content, err_string)

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

    def _run_result_count_equal(self, url, expected, expected_reqno=None):
        print(url)
        response = self._get_response(url)
        self.assertEqual(response.status_code, 200)
        jdata = json.loads(response.content)
        result_count = int(jdata['data'][0]['result_count'])
        print(result_count)
        self.assertEqual(result_count, expected)
        if expected_reqno is not None:
            result_reqno = jdata['data'][0]['reqno']
            print(result_reqno)
            self.assertEqual(result_reqno, expected_reqno)

    def _run_result_count_greater_equal(self, url, expected):
        print(url)
        response = self._get_response(url)
        self.assertEqual(response.status_code, 200)
        jdata = json.loads(response.content)
        result_count = int(jdata['data'][0]['result_count'])
        print(result_count)
        self.assertGreaterEqual(result_count, expected)

    def _run_mults_equal(self, url, expected, mult_name):
        print(url)
        response = self._get_response(url)
        self.assertEqual(response.status_code, 200)
        jdata = json.loads(response.content)
        result_count = int(jdata['mults'][mult_name])
        print(result_count)
        self.assertEqual(result_count, expected)


            #####################################################
            ######### /api/meta/result_count: API TESTS #########
            #####################################################

    # No arguments
    def test__api_meta_result_count_all(self):
        "/api/meta/result_count: no search criteria"
        url = '/opus/__api/meta/result_count.json'
        self._run_result_count_greater_equal(url, 26493) # Assume required volumes

    # Extra args
    def test__api_meta_result_count_with_url_cruft(self):
        "/api/meta/result_count: with extra URL cruft"
        url = '/opus/api/meta/result_count.json?volumeid=COISS_2111&timesec1=2017-03-01T00:00:00&timesec2=2017-03-15T12:00:00&view=search&browse=data&colls_browse=gallery&page=1&gallery_data_viewer=true&limit=100&order=time1&cols=opusid,instrumentid,planet,target,time1,observationduration&widgets=timesec1,COISSshuttermode,volumeid,planet,target&widgets2=&detail='
        self._run_result_count_equal(url, 1321)

    # Mults
    def test__api_meta_result_count_planet(self):
        "/api/meta/result_count: planet=Saturn"
        url = '/opus/__api/meta/result_count.json?planet=Saturn'
        self._run_result_count_greater_equal(url, 15486) # Assume required volumes

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

    # Strings
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

    # Times
    def test__api_meta_result_count_times(self):
        "/api/meta/result_count: time range"
        url = '/opus/__api/meta/result_count.json?planet=Saturn&volumeid=COISS_2111&timesec1=2017-03-01T00:00:00&timesec2=2017-03-15T12:00:00'
        self._run_result_count_equal(url, 1321)

    # 1-column numeric range
    def test__api_meta_result_count_obs_duration(self):
        "/api/meta/result_count: with observation duration"
        url = '/opus/api/meta/result_count.json?volumeid=COISS_2002&observationduration1=.01&observationduration2=.02'
        self._run_result_count_equal(url, 2)

    # 2-column numeric range
    def test__api_meta_result_count_ring_rad_range(self):
        "/api/meta/result_count: with ring radius range, no qtype"
        url = '/opus/api/meta/result_count.json?volumeid=COISS_2111&RINGGEOringradius1=70000&RINGGEOringradius2=80000'
        self._run_result_count_equal(url, 490)

    def test__api_meta_result_count_ring_rad_range_all(self):
        "/api/meta/result_count: with ring radius range, qtype=all"
        url = '/opus/api/meta/result_count.json?volumeid=COISS_2111&RINGGEOringradius1=70000&RINGGEOringradius2=80000&qtype-RINGGEOringradius=all'
        self._run_result_count_equal(url, 217)

    def test__api_meta_result_count_ring_rad_range_only(self):
        "/api/meta/result_count: with ring radius range, qtype=only"
        url = '/opus/api/meta/result_count.json?volumeid=COISS_2111&RINGGEOringradius1=70000&RINGGEOringradius2=80000&qtype-RINGGEOringradius=only'
        self._run_result_count_equal(url, 26)

    # Voyager spacecraft clock count
    def test__api_meta_result_count_voyager_sclk_any(self):
        "/api/meta/result_count: voyager sclk any"
        url = '/opus/api/meta/result_count.json?instrument=Voyager+ISS&insthost=Voyager+2&VOYAGERspacecraftclockcount1=43600:00:775&VOYAGERspacecraftclockcount2=43600:06:780&qtype-VOYAGERspacecraftclockcount=any'
        self._run_result_count_equal(url, 3)

    def test__api_meta_result_count_voyager_sclk_all(self):
        "/api/meta/result_count: voyager sclk all"
        url = '/opus/api/meta/result_count.json?instrument=Voyager+ISS&insthost=Voyager+2&VOYAGERspacecraftclockcount1=43600:00:775&VOYAGERspacecraftclockcount2=43600:06:780&qtype-VOYAGERspacecraftclockcount=all'
        self._run_result_count_equal(url, 0)

    def test__api_meta_result_count_voyager_sclk_only(self):
        "/api/meta/result_count: voyager sclk only"
        url = '/opus/api/meta/result_count.json?instrument=Voyager+ISS&insthost=Voyager+2&VOYAGERspacecraftclockcount1=43600:00:775&VOYAGERspacecraftclockcount2=43600:06:780&qtype-VOYAGERspacecraftclockcount=only'
        self._run_result_count_equal(url, 1)

    # Other return formats
    def test__api_meta_result_count_html(self):
        "/api/meta/result_count: primaryfilespec=1866365558 no qtype"
        url = '/opus/api/meta/result_count.html?primaryfilespec=1866365558'
        expected = b'<body>\n<dl>\n<dt>result_count</dt><dd>2</dd>\n</dl>\n</body>\n'
        self._run_html_equal(url, expected) # BOTSIM

    def test__api_meta_result_count_csv(self):
        "/api/meta/result_count: primaryfilespec=1866365558 no qtype"
        url = '/opus/api/meta/result_count.csv?primaryfilespec=1866365558'
        expected = b'result count,2\n'
        self._run_csv_equal(url, expected) # BOTSIM

    # reqno
    def test__api_meta_result_count_string_no_qtype_reqno(self):
        "/api/meta/result_count: primaryfilespec=1866365558 no qtype"
        url = '/opus/api/meta/result_count.json?primaryfilespec=1866365558&reqno=12345'
        self._run_result_count_equal(url, 2, 12345) # BOTSIM

    def test__api_meta_result_count_html_reqno(self):
        "/api/meta/result_count: primaryfilespec=1866365558 no qtype reqno"
        url = '/opus/api/meta/result_count.html?primaryfilespec=1866365558&reqno=100'
        expected = b'<body>\n<dl>\n<dt>result_count</dt><dd>2</dd>\n</dl>\n</body>\n'
        self._run_html_equal(url, expected) # BOTSIM

    def test__api_meta_result_count_csv_reqno(self):
        "/api/meta/result_count: primaryfilespec=1866365558 no qtype reqno"
        url = '/opus/api/meta/result_count.csv?primaryfilespec=1866365558&reqno=12345'
        expected = b'result count,2\n'
        self._run_csv_equal(url, expected) # BOTSIM

    # Bad queries
    def test__api_meta_result_count_bad_slug(self):
        "/api/meta/result_count: with bad slug"
        url = '/opus/api/meta/result_count.json?volumeid=COISS_2111&RINGGEOringradius1=70000&RINGGEOringradius3=80000&qtype-RINGGEOringradius=only'
        self._run_status_equal(url, 404,
                               settings.HTTP404_SEARCH_PARAMS_INVALID)

    def test__api_meta_result_count_bad_value(self):
        "/api/meta/result_count: with bad value"
        url = '/opus/api/meta/result_count.json?observationduration1=1X2'
        self._run_status_equal(url, 404,
                               settings.HTTP404_SEARCH_PARAMS_INVALID)


            ##############################################
            ######### /api/meta/mults: API TESTS #########
            ##############################################

    # Unrelated constraints
    def test__api_meta_mults_COISS_2111(self):
        "/api/meta/meta/mults: for COISS_2111"
        url = '/opus/api/meta/mults/target.json?volumeid=COISS_2111'
        expected = {"field": "target", "mults": {"Atlas": 2, "Daphnis": 4, "Enceladus": 271, "Epimetheus": 27, "Hyrrokkin": 140, "Iapetus": 127, "Janus": 4, "Methone": 2, "Pallene": 2, "Pan": 56,
                    "Polydeuces": 2, "Prometheus": 4, "Saturn": 1483, "Saturn Rings": 1040, "Sky": 90, "Telesto": 2, "Tethys": 11, "Titan": 384, "Unknown": 16}}
        self._run_json_equal(url, expected)

    def test__api_meta_mults_COISS_2111_saturn(self):
        "/api/meta/meta/mults: for COISS_2111 planet Saturn"
        url = '/opus/api/meta/mults/target.json?volumeid=COISS_2111&planet=Saturn'
        expected = {"field": "target", "mults": {"Atlas": 2, "Daphnis": 4, "Enceladus": 271, "Epimetheus": 27, "Hyrrokkin": 140, "Iapetus": 127, "Janus": 4, "Methone": 2, "Pallene": 2, "Pan": 56,
                    "Polydeuces": 2, "Prometheus": 4, "Saturn": 1483, "Saturn Rings": 1040, "Sky": 90, "Telesto": 2, "Tethys": 11, "Titan": 384, "Unknown": 16}}
        self._run_json_equal(url, expected)

    def test__api_meta_mults_COISS_2111_jupiter(self):
        "/api/meta/meta/mults: for COISS_2111 planet Jupiter"
        url = '/opus/api/meta/mults/target.json?volumeid=COISS_2111&planet=Jupiter'
        expected = {"field": "target", "mults": {}}
        self._run_json_equal(url, expected)

    # Related constraint
    def test__api_meta_mults_COISS_2111_pan(self):
        "/api/meta/meta/mults: for COISS_2111 target Pan"
        url = '/opus/api/meta/mults/target.json?volumeid=COISS_2111&planet=Saturn&target=Pan'
        expected = {"field": "target", "mults": {"Atlas": 2, "Daphnis": 4, "Enceladus": 271, "Epimetheus": 27, "Hyrrokkin": 140, "Iapetus": 127, "Janus": 4, "Methone": 2, "Pallene": 2, "Pan": 56,
                    "Polydeuces": 2, "Prometheus": 4, "Saturn": 1483, "Saturn Rings": 1040, "Sky": 90, "Telesto": 2, "Tethys": 11, "Titan": 384, "Unknown": 16}}
        self._run_json_equal(url, expected)

    def test__api_meta_mults_COISS_2111_dione(self):
        "/api/meta/meta/mults: for COISS_2111 target Dione targetclass"
        url = '/opus/api/meta/mults/target.json?volumeid=COISS_2111&targetclass=Regular+Satellite&target=Dione'
        expected = {"field": "target", "mults": {"Atlas": 2, "Daphnis": 4, "Enceladus": 271, "Epimetheus": 27, "Iapetus": 127, "Janus": 4, "Methone": 2, "Pallene": 2, "Pan": 56, "Polydeuces": 2, "Prometheus": 4, "Telesto": 2, "Tethys": 11, "Titan": 384}}
        self._run_json_equal(url, expected)

    def test__api_meta_mults_COISS_2111_dione_2(self):
        "/api/meta/meta/mults: for COISS_2111 target Dione targetclass 2"
        url = '/opus/api/meta/mults/targetclass.json?volumeid=COISS_2111&targetclass=Regular+Satellite&target=Dione'
        expected = {"field": "targetclass", "mults": {}}
        self._run_json_equal(url, expected)

    def test__api_meta_mults_COISS_2111_daphnis(self):
        "/api/meta/meta/mults: for COISS_2111 target Daphnis targetclass"
        url = '/opus/api/meta/mults/targetclass.json?volumeid=COISS_2111&targetclass=Regular+Satellite&target=Daphnis'
        expected = {"field": "targetclass", "mults": {"Regular Satellite": 4}}
        self._run_json_equal(url, expected)

    # Other return formats
    def test__api_meta_mults_NHPELO_2001_json(self):
        "/api/meta/meta/mults: for NHPELO_2001 target"
        url = '/opus/api/meta/mults/target.json?instrument=New+Horizons+LORRI&volumeid=NHPELO_2001'
        expected = {"field": "target", "mults": {"2002 Ms4": 60, "2010 Jj124": 90, "Arawn": 290, "Calibration": 6, "Charon": 490, "Chiron": 90, "Hd 205905": 10, "Hd 37962": 10, "Hydra": 143, "Ixion": 60,
                    "Kerberos": 10, "Ngc 3532": 45, "Nix": 102, "Pluto": 5265, "Quaoar": 96, "Styx": 6}}
        self._run_json_equal(url, expected)

    def test__api_meta_mults_NHPELO_2001_csv(self):
        "/api/meta/meta/mults: for NHPELO_2001 target csv"
        url = '/opus/api/meta/mults/target.csv?instrument=New+Horizons+LORRI&volumeid=NHPELO_2001'
        expected = b'2002 Ms4,2010 Jj124,Arawn,Calibration,Charon,Chiron,Hd 205905,Hd 37962,Hydra,Ixion,Kerberos,Ngc 3532,Nix,Pluto,Quaoar,Styx\n60,90,290,6,490,90,10,10,143,60,10,45,102,5265,96,6\n'
        self._run_csv_equal(url, expected)

    def test__api_meta_mults_NHPELO_2001_html(self):
        "/api/meta/meta/mults: for NHPELO_2001 target html"
        url = '/opus/api/meta/mults/target.html?instrument=New+Horizons+LORRI&volumeid=NHPELO_2001'
        expected = b'<body>\n<dl>\n<dt>2002 Ms4</dt><dd>60</dd>\n<dt>2010 Jj124</dt><dd>90</dd>\n<dt>Arawn</dt><dd>290</dd>\n<dt>Calibration</dt><dd>6</dd>\n<dt>Charon</dt><dd>490</dd>\n<dt>Chiron</dt><dd>90</dd>\n<dt>Hd 205905</dt><dd>10</dd>\n<dt>Hd 37962</dt><dd>10</dd>\n<dt>Hydra</dt><dd>143</dd>\n<dt>Ixion</dt><dd>60</dd>\n<dt>Kerberos</dt><dd>10</dd>\n<dt>Ngc 3532</dt><dd>45</dd>\n<dt>Nix</dt><dd>102</dd>\n<dt>Pluto</dt><dd>5265</dd>\n<dt>Quaoar</dt><dd>96</dd>\n<dt>Styx</dt><dd>6</dd>\n</dl>\n</body>\n'
        self._run_html_equal(url, expected)

    # reqno
    def test__api_meta_mults_COISS_2111_saturn_reqno(self):
        "/api/meta/meta/mults: for COISS_2111 planet Saturn reqno"
        url = '/opus/api/meta/mults/target.json?volumeid=COISS_2111&planet=Saturn&reqno=98765'
        expected = {"field": "target", "mults": {"Atlas": 2, "Daphnis": 4, "Enceladus": 271, "Epimetheus": 27, "Hyrrokkin": 140, "Iapetus": 127, "Janus": 4, "Methone": 2, "Pallene": 2, "Pan": 56,
                    "Polydeuces": 2, "Prometheus": 4, "Saturn": 1483, "Saturn Rings": 1040, "Sky": 90, "Telesto": 2, "Tethys": 11, "Titan": 384, "Unknown": 16}, "reqno": 98765}
        self._run_json_equal(url, expected)

    # Bad queries
    def test__api_meta_mults_bad_param(self):
        "/api/meta/mults: bad parameter"
        url = '/opus/api/meta/mults/target.json?volumeid=COISS_2111&planetx=Saturn'
        self._run_status_equal(url, 404, settings.HTTP404_SEARCH_PARAMS_INVALID)

    def test__api_meta_mults_bad_slug(self):
        "/api/meta/mults: bad slug"
        url = '/opus/api/meta/mults/targetx.json?volumeid=COISS_2111&planetx=Saturn'
        self._run_status_equal(url, 404, settings.HTTP404_UNKNOWN_SLUG)


            ########################################################
            ######### /api/meta/range/endpoints: API TESTS #########
            ########################################################

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
