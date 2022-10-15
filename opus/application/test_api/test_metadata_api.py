# opus/application/test_api/test_metadata_api.py

import json
import logging
import requests
from unittest import TestCase

from django.core.cache import cache
from rest_framework.test import RequestsClient

from tools.app_utils import (HTTP404_BAD_COLLAPSE,
                             HTTP404_BAD_OR_MISSING_REQNO,
                             HTTP404_SEARCH_PARAMS_INVALID,
                             HTTP404_UNKNOWN_UNITS,
                             HTTP404_UNKNOWN_SLUG)

from .api_test_helper import ApiTestHelper

import settings

class ApiMetadataTests(TestCase, ApiTestHelper):

    def setUp(self):
        self.maxDiff = None
        settings.OPUS_FAKE_API_DELAYS = 0
        settings.OPUS_FAKE_SERVER_ERROR404_PROBABILITY = 0
        settings.OPUS_FAKE_SERVER_ERROR500_PROBABILITY = 0
        settings.CACHE_KEY_PREFIX = 'opustest:' + settings.DB_SCHEMA_NAME
        logging.disable(logging.ERROR)
        if settings.TEST_GO_LIVE: # pragma: no cover
            self.client = requests.Session()
        else:
            self.client = RequestsClient()
        cache.clear()

    def tearDown(self):
        logging.disable(logging.NOTSET)

    def _run_result_count_equal(self, url, expected, expected_reqno=None):
        print(url)
        response = self._get_response(url)
        self.assertEqual(response.status_code, 200)
        jdata = json.loads(response.content)
        result_count = int(jdata['data'][0]['result_count'])
        print(result_count)
        self.assertEqual(result_count, expected)
        if expected_reqno is None:
            self.assertFalse('reqno' in jdata)
        else:
            result_reqno = jdata['data'][0]['reqno']
            print(result_reqno)
            self.assertEqual(result_reqno, expected_reqno)

    def _run_result_count_greater_equal(self, url, expected,
                                        expected_reqno=None):
        print(url)
        response = self._get_response(url)
        self.assertEqual(response.status_code, 200)
        jdata = json.loads(response.content)
        result_count = int(jdata['data'][0]['result_count'])
        print(result_count)
        self.assertGreaterEqual(result_count, expected)
        if expected_reqno is None:
            self.assertFalse('reqno' in jdata)
        else:
            result_reqno = jdata['data'][0]['reqno']
            print(result_reqno)
            self.assertEqual(result_reqno, expected_reqno)


            #####################################################
            ######### /api/meta/result_count: API TESTS #########
            #####################################################

    # Caching test (only visible through code coverage)
    def test__api_meta_result_count_cache(self):
        "[test_metadata_api.py] /api/meta/result_count: cache"
        url = '/api/meta/result_count.json?volumeid=COISS_2111&target=PAN&reqno=1'
        self._run_result_count_equal(url, 56)
        url = '/api/meta/result_count.json?volumeid=COISS_2111&target=PAN&reqno=2'
        self._run_result_count_equal(url, 56)
        url = '/api/meta/result_count.json?volumeid=COISS_2111&target=PAN&reqno=3'
        self._run_result_count_equal(url, 56)
        url = '/api/meta/result_count.json?volumeid=COISS_2111&target=PAN&reqno=1'
        self._run_result_count_equal(url, 56)
        url = '/api/meta/result_count.json?volumeid=COISS_2111&target=PAN&reqno=2'
        self._run_result_count_equal(url, 56)
        url = '/api/meta/result_count.json?volumeid=COISS_2111&target=PAN&reqno=3'
        self._run_result_count_equal(url, 56)

    # No arguments
    def test__api_meta_result_count_all(self):
        "[test_metadata_api.py] /api/meta/result_count: no search criteria"
        url = '/api/meta/result_count.json'
        self._run_result_count_greater_equal(url, 26493) # Assume required volumes

    def test__api_meta_result_count_all_internal(self):
        "[test_metadata_api.py] /api/meta/result_count: no search criteria internal"
        url = '/__api/meta/result_count.json?reqno=1'
        self._run_result_count_greater_equal(url, 26493, 1) # Assume required volumes

    # Extra args
    def test__api_meta_result_count_with_url_cruft(self):
        "[test_metadata_api.py] /api/meta/result_count: with extra URL cruft"
        url = '/api/meta/result_count.json?volumeid=COISS_2111&timesec1=2017-03-01T00:00:00&timesec2=2017-03-15T12:00:00&view=search&browse=data&colls_browse=gallery&page=1&gallery_data_viewer=true&limit=100&order=time1&cols=opusid,instrumentid,planet,target,time1,observationduration&widgets=timesec1,COISSshuttermode,volumeid,planet,target&widgets2=&detail='
        self._run_result_count_equal(url, 1321)

    # Mults
    def test__api_meta_result_count_planet(self):
        "[test_metadata_api.py] /api/meta/result_count: planet=Saturn"
        url = '/api/meta/result_count.json?planet=Saturn'
        self._run_result_count_greater_equal(url, 15486) # Assume required volumes

    def  test__api_meta_result_count_target_pan(self):
        "[test_metadata_api.py] /api/meta/result_count: with target=Pan"
        url = '/api/meta/result_count.json?volumeid=COISS_2111&target=PAN'
        self._run_result_count_equal(url, 56)

    def  test__api_meta_result_count_target_s_rings(self):
        "[test_metadata_api.py] /api/meta/result_count: with target=S Rings"
        url = '/api/meta/result_count.json?planet=Saturn&volumeid=COISS_2111&target=S+Rings'
        self._run_result_count_equal(url, 1040)

    def  test__api_meta_result_count_multi_target(self):
        "[test_metadata_api.py] /api/meta/result_count: with target=Iapetus,Methone"
        url = '/api/meta/result_count.json?planet=Saturn&volumeid=COISS_2111&target=Iapetus,Methone'
        self._run_result_count_equal(url, 129)

    # Strings
    def test__api_meta_result_count_string_no_qtype(self):
        "[test_metadata_api.py] /api/meta/result_count: primaryfilespec=1866365558 no qtype"
        url = '/api/meta/result_count.json?primaryfilespec=1866365558'
        self._run_result_count_equal(url, 2) # BOTSIM

    def test__api_meta_result_count_string_contains(self):
        "[test_metadata_api.py] /api/meta/result_count: primaryfilespec=1866365558 qtype=contains"
        url = '/api/meta/result_count.json?primaryfilespec=1866365558&qtype-primaryfilespec=contains'
        self._run_result_count_equal(url, 2) # BOTSIM

    def test__api_meta_result_count_string_begins(self):
        "[test_metadata_api.py] /api/meta/result_count: primaryfilespec=1866365558 qtype=begins"
        url = '/api/meta/result_count.json?primaryfilespec=1866365558&qtype-primaryfilespec=begins'
        self._run_result_count_equal(url, 0)

    def test__api_meta_result_count_string_ends(self):
        "[test_metadata_api.py] /api/meta/result_count: primaryfilespec=1866365558_1.IMG qtype=ends"
        url = '/api/meta/result_count.json?primaryfilespec=1866365558_1.IMG&qtype-primaryfilespec=ends'
        self._run_result_count_equal(url, 2)

    # Times
    def test__api_meta_result_count_times(self):
        "[test_metadata_api.py] /api/meta/result_count: time range"
        url = '/api/meta/result_count.json?planet=Saturn&volumeid=COISS_2111&timesec1=2017-03-01T00:00:00&timesec2=2017-03-15T12:00:00'
        self._run_result_count_equal(url, 1321)

    # 1-column numeric range
    def test__api_meta_result_count_obs_duration(self):
        "[test_metadata_api.py] /api/meta/result_count: with observation duration"
        url = '/api/meta/result_count.json?volumeid=COISS_2002&observationduration1=.01&observationduration2=.02'
        self._run_result_count_equal(url, 2)

    # 2-column numeric range
    def test__api_meta_result_count_ring_rad_range(self):
        "[test_metadata_api.py] /api/meta/result_count: with ring radius range, no qtype"
        url = '/api/meta/result_count.json?volumeid=COISS_2111&RINGGEOringradius1=70000&RINGGEOringradius2=80000'
        self._run_result_count_equal(url, 490)

    def test__api_meta_result_count_ring_rad_range_all(self):
        "[test_metadata_api.py] /api/meta/result_count: with ring radius range, qtype=all"
        url = '/api/meta/result_count.json?volumeid=COISS_2111&RINGGEOringradius1=70000&RINGGEOringradius2=80000&qtype-RINGGEOringradius=all'
        self._run_result_count_equal(url, 217)

    def test__api_meta_result_count_ring_rad_range_only(self):
        "[test_metadata_api.py] /api/meta/result_count: with ring radius range, qtype=only"
        url = '/api/meta/result_count.json?volumeid=COISS_2111&RINGGEOringradius1=70000&RINGGEOringradius2=80000&qtype-RINGGEOringradius=only'
        self._run_result_count_equal(url, 26)

    # Voyager spacecraft clock count
    def test__api_meta_result_count_voyager_sclk_any(self):
        "[test_metadata_api.py] /api/meta/result_count: voyager sclk any"
        url = '/api/meta/result_count.json?instrument=Voyager+ISS&insthost=Voyager+2&VOYAGERspacecraftclockcount1=43600:00:775&VOYAGERspacecraftclockcount2=43600:06:780&qtype-VOYAGERspacecraftclockcount=any'
        self._run_result_count_equal(url, 3)

    def test__api_meta_result_count_voyager_sclk_all(self):
        "[test_metadata_api.py] /api/meta/result_count: voyager sclk all"
        url = '/api/meta/result_count.json?instrument=Voyager+ISS&insthost=Voyager+2&VOYAGERspacecraftclockcount1=43600:00:775&VOYAGERspacecraftclockcount2=43600:06:780&qtype-VOYAGERspacecraftclockcount=all'
        self._run_result_count_equal(url, 0)

    def test__api_meta_result_count_voyager_sclk_only(self):
        "[test_metadata_api.py] /api/meta/result_count: voyager sclk only"
        url = '/api/meta/result_count.json?instrument=Voyager+ISS&insthost=Voyager+2&VOYAGERspacecraftclockcount1=43600:00:775&VOYAGERspacecraftclockcount2=43600:06:780&qtype-VOYAGERspacecraftclockcount=only'
        self._run_result_count_equal(url, 1)

    # Other return formats
    def test__api_meta_result_count_html(self):
        "[test_metadata_api.py] /api/meta/result_count: primaryfilespec=1866365558 no qtype html"
        url = '/api/meta/result_count.html?primaryfilespec=1866365558'
        expected = b'<dl>\n<dt>result_count</dt><dd>2</dd>\n</dl>\n'
        self._run_html_equal(url, expected) # BOTSIM

    def test__api_meta_result_count_csv(self):
        "[test_metadata_api.py] /api/meta/result_count: primaryfilespec=1866365558 no qtype csv"
        url = '/api/meta/result_count.csv?primaryfilespec=1866365558'
        expected = b'result count,2\n'
        self._run_csv_equal(url, expected) # BOTSIM

    def test__api_meta_result_count_html_internal(self):
        "[test_metadata_api.py] /api/meta/result_count: primaryfilespec=1866365558 no qtype html internal"
        url = '/__api/meta/result_count.html?primaryfilespec=1866365558'
        expected = b'<dl>\n<dt>result_count</dt><dd>2</dd>\n</dl>\n'
        self._run_status_equal(url, 404)

    def test__api_meta_result_count_csv_internal(self):
        "[test_metadata_api.py] /api/meta/result_count: primaryfilespec=1866365558 no qtype csv internal"
        url = '/__api/meta/result_count.csv?primaryfilespec=1866365558'
        expected = b'result count,2\n'
        self._run_status_equal(url, 404)

    # reqno
    def test__api_meta_result_count_string_no_qtype_reqno(self):
        "[test_metadata_api.py] /api/meta/result_count: primaryfilespec=1866365558 no qtype reqno"
        url = '/api/meta/result_count.json?primaryfilespec=1866365558&reqno=12345'
        self._run_result_count_equal(url, 2) # BOTSIM

    def test__api_meta_result_count_string_no_qtype_reqno_internal(self):
        "[test_metadata_api.py] /api/meta/result_count: primaryfilespec=1866365558 no qtype reqno internal"
        url = '/__api/meta/result_count.json?primaryfilespec=1866365558&reqno=12345'
        self._run_result_count_equal(url, 2, 12345) # BOTSIM

    def test__api_meta_result_count_string_no_qtype_reqno_bad_internal(self):
        "[test_metadata_api.py] /api/meta/result_count: primaryfilespec=1866365558 no qtype reqno bad internal"
        url = '/__api/meta/result_count.json?primaryfilespec=1866365558&reqno=NaN'
        self._run_status_equal(url, 404,
               HTTP404_BAD_OR_MISSING_REQNO('/__api/meta/result_count.json'))

    def test__api_meta_result_count_string_no_qtype_reqno_bad_internal_2(self):
        "[test_metadata_api.py] /api/meta/result_count: primaryfilespec=1866365558 no qtype reqno bad internal 2"
        url = '/__api/meta/result_count.json?primaryfilespec=1866365558&reqno=-1'
        self._run_status_equal(url, 404,
               HTTP404_BAD_OR_MISSING_REQNO('/__api/meta/result_count.json'))

    def test__api_meta_result_count_html_reqno(self):
        "[test_metadata_api.py] /api/meta/result_count: primaryfilespec=1866365558 no qtype reqno html"
        url = '/api/meta/result_count.html?primaryfilespec=1866365558&reqno=100'
        expected = b'<dl>\n<dt>result_count</dt><dd>2</dd>\n</dl>\n'
        self._run_html_equal(url, expected) # BOTSIM

    def test__api_meta_result_count_csv_reqno(self):
        "[test_metadata_api.py] /api/meta/result_count: primaryfilespec=1866365558 no qtype reqno csv"
        url = '/api/meta/result_count.csv?primaryfilespec=1866365558&reqno=NaN'
        expected = b'result count,2\n'
        self._run_csv_equal(url, expected) # BOTSIM

    # Bad queries
    def test__api_meta_result_count_bad_slug(self):
        "[test_metadata_api.py] /api/meta/result_count: with bad slug"
        url = '/api/meta/result_count.json?volumeid=COISS_2111&RINGGEOringradius1=70000&RINGGEOringradius3=80000&qtype-RINGGEOringradius=only'
        self._run_status_equal(url, 404,
                HTTP404_SEARCH_PARAMS_INVALID('/api/meta/result_count.json'))

    def test__api_meta_result_count_bad_value(self):
        "[test_metadata_api.py] /api/meta/result_count: with bad value"
        url = '/api/meta/result_count.json?observationduration=1X2'
        self._run_status_equal(url, 404,
                HTTP404_SEARCH_PARAMS_INVALID('/api/meta/result_count.json'))


            ##############################################
            ######### /api/meta/mults: API TESTS #########
            ##############################################

    # Caching (only visible through code coverage)
    def test__api_meta_mults_cache(self):
        "[test_metadata_api.py] /api/meta/meta/mults: cache"
        url = '/__api/meta/mults/target.json?volumeid=COISS_2111&reqno=1'
        expected = {"field_id": "target", "mults": {"Atlas": 2, "Daphnis": 4, "Enceladus": 271, "Epimetheus": 27, "Hyrrokkin": 140, "Iapetus": 127, "Janus": 4, "Methone": 2, "Pallene": 2, "Pan": 56,
                    "Polydeuces": 2, "Prometheus": 4, "Saturn": 1483, "Saturn Rings": 1040, "Sky": 90, "Telesto": 2, "Tethys": 11, "Titan": 384, "Unknown": 16}, "reqno": 1}
        self._run_json_equal(url, expected)
        url = '/__api/meta/mults/target.json?volumeid=COISS_2111&reqno=2'
        expected = {"field_id": "target", "mults": {"Atlas": 2, "Daphnis": 4, "Enceladus": 271, "Epimetheus": 27, "Hyrrokkin": 140, "Iapetus": 127, "Janus": 4, "Methone": 2, "Pallene": 2, "Pan": 56,
                    "Polydeuces": 2, "Prometheus": 4, "Saturn": 1483, "Saturn Rings": 1040, "Sky": 90, "Telesto": 2, "Tethys": 11, "Titan": 384, "Unknown": 16}, "reqno": 2}
        self._run_json_equal(url, expected)
        url = '/__api/meta/mults/target.json?volumeid=COISS_2111&reqno=3'
        expected = {"field_id": "target", "mults": {"Atlas": 2, "Daphnis": 4, "Enceladus": 271, "Epimetheus": 27, "Hyrrokkin": 140, "Iapetus": 127, "Janus": 4, "Methone": 2, "Pallene": 2, "Pan": 56,
                    "Polydeuces": 2, "Prometheus": 4, "Saturn": 1483, "Saturn Rings": 1040, "Sky": 90, "Telesto": 2, "Tethys": 11, "Titan": 384, "Unknown": 16}, "reqno": 3}
        self._run_json_equal(url, expected)
        url = '/__api/meta/mults/target.json?volumeid=COISS_2111&reqno=1'
        expected = {"field_id": "target", "mults": {"Atlas": 2, "Daphnis": 4, "Enceladus": 271, "Epimetheus": 27, "Hyrrokkin": 140, "Iapetus": 127, "Janus": 4, "Methone": 2, "Pallene": 2, "Pan": 56,
                    "Polydeuces": 2, "Prometheus": 4, "Saturn": 1483, "Saturn Rings": 1040, "Sky": 90, "Telesto": 2, "Tethys": 11, "Titan": 384, "Unknown": 16}, "reqno": 1}
        self._run_json_equal(url, expected)
        url = '/__api/meta/mults/target.json?volumeid=COISS_2111&reqno=2'
        expected = {"field_id": "target", "mults": {"Atlas": 2, "Daphnis": 4, "Enceladus": 271, "Epimetheus": 27, "Hyrrokkin": 140, "Iapetus": 127, "Janus": 4, "Methone": 2, "Pallene": 2, "Pan": 56,
                    "Polydeuces": 2, "Prometheus": 4, "Saturn": 1483, "Saturn Rings": 1040, "Sky": 90, "Telesto": 2, "Tethys": 11, "Titan": 384, "Unknown": 16}, "reqno": 2}
        self._run_json_equal(url, expected)
        url = '/__api/meta/mults/target.json?volumeid=COISS_2111&reqno=3'
        expected = {"field_id": "target", "mults": {"Atlas": 2, "Daphnis": 4, "Enceladus": 271, "Epimetheus": 27, "Hyrrokkin": 140, "Iapetus": 127, "Janus": 4, "Methone": 2, "Pallene": 2, "Pan": 56,
                    "Polydeuces": 2, "Prometheus": 4, "Saturn": 1483, "Saturn Rings": 1040, "Sky": 90, "Telesto": 2, "Tethys": 11, "Titan": 384, "Unknown": 16}, "reqno": 3}
        self._run_json_equal(url, expected)

    # Unrelated constraints
    def test__api_meta_mults_COISS_2111(self):
        "[test_metadata_api.py] /api/meta/meta/mults: for COISS_2111"
        url = '/api/meta/mults/target.json?volumeid=COISS_2111'
        expected = {"field_id": "target", "mults": {"Atlas": 2, "Daphnis": 4, "Enceladus": 271, "Epimetheus": 27, "Hyrrokkin": 140, "Iapetus": 127, "Janus": 4, "Methone": 2, "Pallene": 2, "Pan": 56,
                    "Polydeuces": 2, "Prometheus": 4, "Saturn": 1483, "Saturn Rings": 1040, "Sky": 90, "Telesto": 2, "Tethys": 11, "Titan": 384, "Unknown": 16}}
        self._run_json_equal(url, expected)

    def test__api_meta_mults_COISS_2111_internal(self):
        "[test_metadata_api.py] /api/meta/meta/mults: for COISS_2111 internal"
        url = '/__api/meta/mults/target.json?volumeid=COISS_2111&reqno=1'
        expected = {"field_id": "target", "mults": {"Atlas": 2, "Daphnis": 4, "Enceladus": 271, "Epimetheus": 27, "Hyrrokkin": 140, "Iapetus": 127, "Janus": 4, "Methone": 2, "Pallene": 2, "Pan": 56,
                    "Polydeuces": 2, "Prometheus": 4, "Saturn": 1483, "Saturn Rings": 1040, "Sky": 90, "Telesto": 2, "Tethys": 11, "Titan": 384, "Unknown": 16}, "reqno": 1}
        self._run_json_equal(url, expected)

    def test__api_meta_mults_COISS_2111_saturn(self):
        "[test_metadata_api.py] /api/meta/meta/mults: for COISS_2111 planet Saturn"
        url = '/api/meta/mults/target.json?volumeid=COISS_2111&planet=Saturn'
        expected = {"field_id": "target", "mults": {"Atlas": 2, "Daphnis": 4, "Enceladus": 271, "Epimetheus": 27, "Hyrrokkin": 140, "Iapetus": 127, "Janus": 4, "Methone": 2, "Pallene": 2, "Pan": 56,
                    "Polydeuces": 2, "Prometheus": 4, "Saturn": 1483, "Saturn Rings": 1040, "Sky": 90, "Telesto": 2, "Tethys": 11, "Titan": 384, "Unknown": 16}}
        self._run_json_equal(url, expected)

    def test__api_meta_mults_COISS_2111_jupiter(self):
        "[test_metadata_api.py] /api/meta/meta/mults: for COISS_2111 planet Jupiter"
        url = '/api/meta/mults/target.json?volumeid=COISS_2111&planet=Jupiter'
        expected = {"field_id": "target", "mults": {}}
        self._run_json_equal(url, expected)

    # Related constraint
    def test__api_meta_mults_COISS_2111_pan(self):
        "[test_metadata_api.py] /api/meta/meta/mults: for COISS_2111 target Pan"
        url = '/api/meta/mults/target.json?volumeid=COISS_2111&planet=Saturn&target=Pan'
        expected = {"field_id": "target", "mults": {"Atlas": 2, "Daphnis": 4, "Enceladus": 271, "Epimetheus": 27, "Hyrrokkin": 140, "Iapetus": 127, "Janus": 4, "Methone": 2, "Pallene": 2, "Pan": 56,
                    "Polydeuces": 2, "Prometheus": 4, "Saturn": 1483, "Saturn Rings": 1040, "Sky": 90, "Telesto": 2, "Tethys": 11, "Titan": 384, "Unknown": 16}}
        self._run_json_equal(url, expected)

    def test__api_meta_mults_COISS_2111_dione(self):
        "[test_metadata_api.py] /api/meta/meta/mults: for COISS_2111 target Dione targetclass"
        url = '/api/meta/mults/target.json?volumeid=COISS_2111&targetclass=Regular+Satellite&target=Dione'
        expected = {"field_id": "target", "mults": {"Atlas": 2, "Daphnis": 4, "Enceladus": 271, "Epimetheus": 27, "Iapetus": 127, "Janus": 4, "Methone": 2, "Pallene": 2, "Pan": 56, "Polydeuces": 2, "Prometheus": 4, "Telesto": 2, "Tethys": 11, "Titan": 384}}
        self._run_json_equal(url, expected)

    def test__api_meta_mults_COISS_2111_dione_2(self):
        "[test_metadata_api.py] /api/meta/meta/mults: for COISS_2111 target Dione targetclass 2"
        url = '/api/meta/mults/targetclass.json?volumeid=COISS_2111&targetclass=Regular+Satellite&target=Dione'
        expected = {"field_id": "targetclass", "mults": {}}
        self._run_json_equal(url, expected)

    def test__api_meta_mults_COISS_2111_daphnis(self):
        "[test_metadata_api.py] /api/meta/meta/mults: for COISS_2111 target Daphnis targetclass"
        url = '/api/meta/mults/targetclass.json?volumeid=COISS_2111&targetclass=Regular+Satellite&target=Daphnis'
        expected = {"field_id": "targetclass", "mults": {"Regular Satellite": 4}}
        self._run_json_equal(url, expected)

    def test__api_meta_mults_COISS_2111_imagetype(self):
        "[test_metadata_api.py] /api/meta/meta/mults: for COISS_2111 imagetype"
        # This joins in a non-obs_general table
        url = '/api/meta/mults/imagetype.json?volumeid=COISS_2111'
        expected = {"field_id": "imagetype", "mults": {"Frame": 3667}}
        self._run_json_equal(url, expected)

    # Other return formats
    def test__api_meta_mults_NHPELO_1001_json(self):
        "[test_metadata_api.py] /api/meta/meta/mults: for NHPELO_1001 target"
        url = '/api/meta/mults/target.json?instrument=New+Horizons+LORRI&volumeid=NHPELO_1001'
        expected = {"field_id": "target", "mults": {"2002 MS4": 60, "2010 JJ124": 90, "Arawn": 290, "Calibration": 6, "Charon": 490, "Chiron": 90, "HD 205905": 10, "HD 37962": 10, "Hydra": 143, "Ixion": 60,
                    "Kerberos": 10, "NGC 3532": 45, "Nix": 102, "Pluto": 5265, "Quaoar": 96, "Styx": 6}}
        self._run_json_equal(url, expected)

    def test__api_meta_mults_NHPELO_1001_csv(self):
        "[test_metadata_api.py] /api/meta/meta/mults: for NHPELO_1001 target csv"
        url = '/api/meta/mults/target.csv?instrument=New+Horizons+LORRI&volumeid=NHPELO_1001'
        expected = b'2002 MS4,2010 JJ124,Arawn,Calibration,Charon,Chiron,HD 205905,HD 37962,Hydra,Ixion,Kerberos,NGC 3532,Nix,Pluto,Quaoar,Styx\n60,90,290,6,490,90,10,10,143,60,10,45,102,5265,96,6\n'
        self._run_csv_equal(url, expected)

    def test__api_meta_mults_NHPELO_1001_html(self):
        "[test_metadata_api.py] /api/meta/meta/mults: for NHPELO_1001 target html"
        url = '/api/meta/mults/target.html?instrument=New+Horizons+LORRI&volumeid=NHPELO_1001'
        expected = b'<dl>\n<dt>2002 MS4</dt><dd>60</dd>\n<dt>2010 JJ124</dt><dd>90</dd>\n<dt>Arawn</dt><dd>290</dd>\n<dt>Calibration</dt><dd>6</dd>\n<dt>Charon</dt><dd>490</dd>\n<dt>Chiron</dt><dd>90</dd>\n<dt>HD 205905</dt><dd>10</dd>\n<dt>HD 37962</dt><dd>10</dd>\n<dt>Hydra</dt><dd>143</dd>\n<dt>Ixion</dt><dd>60</dd>\n<dt>Kerberos</dt><dd>10</dd>\n<dt>NGC 3532</dt><dd>45</dd>\n<dt>Nix</dt><dd>102</dd>\n<dt>Pluto</dt><dd>5265</dd>\n<dt>Quaoar</dt><dd>96</dd>\n<dt>Styx</dt><dd>6</dd>\n</dl>\n'
        self._run_html_equal(url, expected)

    def test__api_meta_mults_NHPELO_1001_csv_internal(self):
        "[test_metadata_api.py] /api/meta/meta/mults: for NHPELO_1001 target csv internal"
        url = '/__api/meta/mults/target.csv?instrument=New+Horizons+LORRI&volumeid=NHPELO_1001'
        self._run_status_equal(url, 404)

    def test__api_meta_mults_NHPELO_1001_html_internal(self):
        "[test_metadata_api.py] /api/meta/meta/mults: for NHPELO_1001 target html internal"
        url = '/__api/meta/mults/target.html?instrument=New+Horizons+LORRI&volumeid=NHPELO_1001'
        self._run_status_equal(url, 404)

    # reqno
    def test__api_meta_mults_COISS_2111_saturn_reqno(self):
        "[test_metadata_api.py] /api/meta/meta/mults: for COISS_2111 planet Saturn reqno"
        url = '/api/meta/mults/target.json?volumeid=COISS_2111&planet=Saturn&reqno=98765'
        expected = {"field_id": "target", "mults": {"Atlas": 2, "Daphnis": 4, "Enceladus": 271, "Epimetheus": 27, "Hyrrokkin": 140, "Iapetus": 127, "Janus": 4, "Methone": 2, "Pallene": 2, "Pan": 56,
                    "Polydeuces": 2, "Prometheus": 4, "Saturn": 1483, "Saturn Rings": 1040, "Sky": 90, "Telesto": 2, "Tethys": 11, "Titan": 384, "Unknown": 16}}
        self._run_json_equal(url, expected)

    def test__api_meta_mults_COISS_2111_saturn_reqno_internal(self):
        "[test_metadata_api.py] /api/meta/meta/mults: for COISS_2111 planet Saturn reqno internal"
        url = '/__api/meta/mults/target.json?volumeid=COISS_2111&planet=Saturn&reqno=98765'
        expected = {"field_id": "target", "mults": {"Atlas": 2, "Daphnis": 4, "Enceladus": 271, "Epimetheus": 27, "Hyrrokkin": 140, "Iapetus": 127, "Janus": 4, "Methone": 2, "Pallene": 2, "Pan": 56,
                    "Polydeuces": 2, "Prometheus": 4, "Saturn": 1483, "Saturn Rings": 1040, "Sky": 90, "Telesto": 2, "Tethys": 11, "Titan": 384, "Unknown": 16}, "reqno": 98765}
        self._run_json_equal(url, expected)

    def test__api_meta_mults_COISS_2111_saturn_reqno_bad_internal(self):
        "[test_metadata_api.py] /api/meta/meta/mults: for COISS_2111 planet Saturn reqno bad internal"
        url = '/__api/meta/mults/target.json?volumeid=COISS_2111&planet=Saturn&reqno=NaN'
        self._run_status_equal(url, 404,
                HTTP404_BAD_OR_MISSING_REQNO('/__api/meta/mults/target.json'))

    def test__api_meta_mults_COISS_2111_saturn_reqno_bad_internal_2(self):
        "[test_metadata_api.py] /api/meta/meta/mults: for COISS_2111 planet Saturn reqno bad internal 2"
        url = '/__api/meta/mults/target.json?volumeid=COISS_2111&planet=Saturn&reqno=-101010'
        self._run_status_equal(url, 404,
                HTTP404_BAD_OR_MISSING_REQNO('/__api/meta/mults/target.json'))

    def test__api_meta_mults_NHPELO_1001_csv_reqno(self):
        "[test_metadata_api.py] /api/meta/meta/mults: for NHPELO_1001 target reqno csv"
        url = '/api/meta/mults/target.csv?instrument=New+Horizons+LORRI&volumeid=NHPELO_1001&reqno=NaN'
        expected = b'2002 MS4,2010 JJ124,Arawn,Calibration,Charon,Chiron,HD 205905,HD 37962,Hydra,Ixion,Kerberos,NGC 3532,Nix,Pluto,Quaoar,Styx\n60,90,290,6,490,90,10,10,143,60,10,45,102,5265,96,6\n'
        self._run_csv_equal(url, expected)

    def test__api_meta_mults_NHPELO_1001_html_reqno(self):
        "[test_metadata_api.py] /api/meta/meta/mults: for NHPELO_1001 target reqno html"
        url = '/api/meta/mults/target.html?instrument=New+Horizons+LORRI&volumeid=NHPELO_1001&reqno=5'
        expected = b'<dl>\n<dt>2002 MS4</dt><dd>60</dd>\n<dt>2010 JJ124</dt><dd>90</dd>\n<dt>Arawn</dt><dd>290</dd>\n<dt>Calibration</dt><dd>6</dd>\n<dt>Charon</dt><dd>490</dd>\n<dt>Chiron</dt><dd>90</dd>\n<dt>HD 205905</dt><dd>10</dd>\n<dt>HD 37962</dt><dd>10</dd>\n<dt>Hydra</dt><dd>143</dd>\n<dt>Ixion</dt><dd>60</dd>\n<dt>Kerberos</dt><dd>10</dd>\n<dt>NGC 3532</dt><dd>45</dd>\n<dt>Nix</dt><dd>102</dd>\n<dt>Pluto</dt><dd>5265</dd>\n<dt>Quaoar</dt><dd>96</dd>\n<dt>Styx</dt><dd>6</dd>\n</dl>\n'
        self._run_html_equal(url, expected)

    # Bad queries
    def test__api_meta_mults_bad_param(self):
        "[test_metadata_api.py] /api/meta/mults: bad parameter"
        url = '/api/meta/mults/target.json?volumeid=COISS_2111&planetx=Saturn'
        self._run_status_equal(url, 404,
                HTTP404_SEARCH_PARAMS_INVALID('/api/meta/mults/target.json'))

    def test__api_meta_mults_bad_slug(self):
        "[test_metadata_api.py] /api/meta/mults: bad slug"
        url = '/api/meta/mults/targetx.json?volumeid=COISS_2111&planet=Saturn'
        self._run_status_equal(url, 404,
                HTTP404_UNKNOWN_SLUG('targetx', '/api/meta/mults/targetx.json'))


            ########################################################
            ######### /api/meta/range/endpoints: API TESTS #########
            ########################################################

    # Caching (only visible through code coverage)
    def test__api_meta_range_endpoints_cache(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: cache"
        url = '/__api/meta/range/endpoints/timesec1.json?volumeid=COISS_2111&reqno=1'
        expected = {"max": "2017-03-31T13:05:35.059", "nulls": 0, "min": "2017-02-17T23:59:39.059", "reqno": 1, "units": "ymdhms"}
        self._run_json_equal(url, expected)
        url = '/__api/meta/range/endpoints/timesec1.json?volumeid=COISS_2111&reqno=2'
        expected = {"max": "2017-03-31T13:05:35.059", "nulls": 0, "min": "2017-02-17T23:59:39.059", "reqno": 2, "units": "ymdhms"}
        self._run_json_equal(url, expected)
        url = '/__api/meta/range/endpoints/timesec1.json?volumeid=COISS_2111&reqno=3'
        expected = {"max": "2017-03-31T13:05:35.059", "nulls": 0, "min": "2017-02-17T23:59:39.059", "reqno": 3, "units": "ymdhms"}
        self._run_json_equal(url, expected)
        url = '/__api/meta/range/endpoints/timesec1.json?volumeid=COISS_2111&reqno=1'
        expected = {"max": "2017-03-31T13:05:35.059", "nulls": 0, "min": "2017-02-17T23:59:39.059", "reqno": 1, "units": "ymdhms"}
        self._run_json_equal(url, expected)
        url = '/__api/meta/range/endpoints/timesec1.json?volumeid=COISS_2111&reqno=2'
        expected = {"max": "2017-03-31T13:05:35.059", "nulls": 0, "min": "2017-02-17T23:59:39.059", "reqno": 2, "units": "ymdhms"}
        self._run_json_equal(url, expected)
        url = '/__api/meta/range/endpoints/timesec1.json?volumeid=COISS_2111&reqno=3'
        expected = {"max": "2017-03-31T13:05:35.059", "nulls": 0, "min": "2017-02-17T23:59:39.059", "reqno": 3, "units": "ymdhms"}
        self._run_json_equal(url, expected)

    # General / Observation Time (string return)
    def test__api_meta_range_endpoints_times_COISS(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: times COISS"
        url = '/api/meta/range/endpoints/timesec1.json?volumeid=COISS_2111'
        expected = {"max": "2017-03-31T13:05:35.059", "nulls": 0, "min": "2017-02-17T23:59:39.059", "units": "ymdhms"}
        self._run_json_equal(url, expected)

    def test__api_meta_range_endpoints_times_COISS_internal(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: times COISS internal"
        url = '/__api/meta/range/endpoints/timesec1.json?volumeid=COISS_2111&reqno=1'
        expected = {"max": "2017-03-31T13:05:35.059", "nulls": 0, "min": "2017-02-17T23:59:39.059", "reqno": 1, "units": "ymdhms"}
        self._run_json_equal(url, expected)

    def test__api_meta_range_endpoints_times_COUVIS(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: times COUVIS"
        url = '/api/meta/range/endpoints/timesec1.json?volumeid=COUVIS_0002'
        expected = {"max": "2001-04-01T00:07:19.842", "nulls": 0, "min": "2001-01-01T02:12:02.721", "units": "ymdhms"}
        self._run_json_equal(url, expected)

    def test__api_meta_range_endpoints_times_COVIMS(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: times COVIMS"
        url = '/api/meta/range/endpoints/timesec1.json?volumeid=COVIMS_0006'
        expected = {"max": "2005-04-01T00:06:46.867", "nulls": 0, "min": "2005-01-15T17:55:38.899", "units": "ymdhms"}
        self._run_json_equal(url, expected)

    def test__api_meta_range_endpoints_times_GOSSI(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: times GOSSI"
        url = '/api/meta/range/endpoints/timesec1.json?volumeid=GO_0017'
        expected = {"max": "1996-12-14T17:30:37.354", "nulls": 0, "min": "1996-06-03T17:05:38.002", "units": "ymdhms"}
        self._run_json_equal(url, expected)

    def test__api_meta_range_endpoints_times_VGISS(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: times VGISS"
        url = '/api/meta/range/endpoints/timesec1.json?volumeid=VGISS_6210'
        expected = {"max": "1981-08-15T22:17:36.000", "nulls": 0, "min": "1981-08-12T14:55:10.080", "units": "ymdhms"}
        self._run_json_equal(url, expected)

    def test__api_meta_range_endpoints_times_HSTI(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: times HSTI"
        url = '/api/meta/range/endpoints/timesec1.json?volumeid=HSTI1_1559'
        expected = {"min": "2009-09-18T13:13:10.000", "max": "2009-09-23T01:05:12.000", "nulls": 0, "units": "ymdhms"}
        self._run_json_equal(url, expected)

    def test__api_meta_range_endpoints_times_HSTI_html(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: times HSTI html"
        url = '/api/meta/range/endpoints/timesec1.html?volumeid=HSTI1_1559'
        expected = b'<dl>\n<dt>min</dt><dd>2009-09-18T13:13:10.000</dd>\n<dt>max</dt><dd>2009-09-23T01:05:12.000</dd>\n<dt>nulls</dt><dd>0</dd>\n<dt>units</dt><dd>ymdhms</dd>\n</dl>\n'
        self._run_html_equal(url, expected)

    def test__api_meta_range_endpoints_times_HSTI_csv(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: times HSTI csv"
        url = '/api/meta/range/endpoints/timesec1.csv?volumeid=HSTI1_1559'
        expected = b'min,max,nulls,units\n2009-09-18T13:13:10.000,2009-09-23T01:05:12.000,0,ymdhms\n'
        self._run_csv_equal(url, expected)

    # General / Observation Duration (floating point return)
    def test__api_meta_range_endpoints_observation_duration_VGISS(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: observation duration VGISS"
        url = '/api/meta/range/endpoints/observationduration.json?volumeid=VGISS_6210'
        expected = {'min': '0.24', 'max': '15.36', 'nulls': 0, "units": "seconds"}
        self._run_json_equal(url, expected)

    def test__api_meta_range_endpoints_observation_duration_VGISS_milliseconds(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: observation duration VGISS milliseconds"
        url = '/api/meta/range/endpoints/observationduration.json?volumeid=VGISS_6210&units=milliseconds'
        expected = {'min': '240', 'max': '15360', 'nulls': 0, "units": "milliseconds"}
        self._run_json_equal(url, expected)

    def test__api_meta_range_endpoints_observation_duration_VGISS_seconds(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: observation duration VGISS seconds"
        url = '/api/meta/range/endpoints/observationduration.json?volumeid=VGISS_6210&units=seconds'
        expected = {'min': '0.24', 'max': '15.36', 'nulls': 0, "units": "seconds"}
        self._run_json_equal(url, expected)

    def test__api_meta_range_endpoints_observation_duration_VGISS_minutes(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: observation duration VGISS minutes"
        url = '/api/meta/range/endpoints/observationduration.json?volumeid=VGISS_6210&units=minutes'
        expected = {"min": "0.004", "max": "0.256", "nulls": 0, "units": "minutes"}
        self._run_json_equal(url, expected)

    def test__api_meta_range_endpoints_observation_duration_VGISS_hours(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: observation duration VGISS hours"
        url = '/api/meta/range/endpoints/observationduration.json?volumeid=VGISS_6210&units=hours'
        expected = {"min": "0.00006667", "max": "0.00426667", "nulls": 0, "units": "hours"}
        self._run_json_equal(url, expected)

    def test__api_meta_range_endpoints_observation_duration_VGISS_days(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: observation duration VGISS days"
        url = '/api/meta/range/endpoints/observationduration.json?volumeid=VGISS_6210&units=days'
        expected = {"min": "0.000002778", "max": "0.000177778", "nulls": 0, "units": "days"}
        self._run_json_equal(url, expected)

    def test__api_meta_range_endpoints_observation_duration_VGISS_degrees(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: observation duration VGISS degrees"
        url = '/api/meta/range/endpoints/observationduration.json?volumeid=VGISS_6210&units=degrees'
        self._run_status_equal(url, 404,
                HTTP404_UNKNOWN_UNITS('degrees', 'observationduration',
                        '/api/meta/range/endpoints/observationduration.json'))

    # General / Right Ascension (floating point return with nulls)
    def test__api_meta_range_endpoints_right_ascension_HST(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: right ascension HSTJ"
        url = '/api/meta/range/endpoints/rightasc.json?volumeid=HSTJ0_9975'
        expected = {"min": None, "max": None, "nulls": 75, "units": "degrees"}
        self._run_json_equal(url, expected)

    def test__api_meta_range_endpoints_right_ascension_HST_html(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: right ascension HSTJ html"
        url = '/api/meta/range/endpoints/rightasc.html?volumeid=HSTJ0_9975'
        expected = b'<dl>\n<dt>min</dt><dd>None</dd>\n<dt>max</dt><dd>None</dd>\n<dt>nulls</dt><dd>75</dd>\n<dt>units</dt><dd>degrees</dd>\n</dl>\n'
        self._run_html_equal(url, expected)

    def test__api_meta_range_endpoints_right_ascension_HST_csv(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: right ascension HSTJ csv"
        url = '/api/meta/range/endpoints/rightasc.csv?volumeid=HSTJ0_9975'
        expected = b'min,max,nulls,units\n,,75,degrees\n'
        self._run_csv_equal(url, expected)

    def test__api_meta_range_endpoints_right_ascension_VGISS(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: right ascension VGISS"
        url = '/api/meta/range/endpoints/rightasc.json?volumeid=VGISS_6210'
        expected = {"min": "192.007002", "max": "242.282082", "nulls": 0, "units": "degrees"}
        self._run_json_equal(url, expected)

    def test__api_meta_range_endpoints_right_ascension_VGISS_degrees(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: right ascension VGISS degrees"
        url = '/api/meta/range/endpoints/rightasc.json?volumeid=VGISS_6210&units=degrees'
        expected = {"min": "192.007002", "max": "242.282082", "nulls": 0, "units": "degrees"}
        self._run_json_equal(url, expected)

    def test__api_meta_range_endpoints_right_ascension_VGISS_dms(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: right ascension VGISS dms"
        url = '/api/meta/range/endpoints/rightasc.json?volumeid=VGISS_6210&units=dms'
        expected = {"min": "192d 00m 25.207s", "max": "242d 16m 55.495s", "nulls": 0, "units": "dms"}
        self._run_json_equal(url, expected)

    def test__api_meta_range_endpoints_right_ascension_VGISS_hours(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: right ascension VGISS hours"
        url = '/api/meta/range/endpoints/rightasc.json?volumeid=VGISS_6210&units=hours'
        expected = {"min": "12.8004668", "max": "16.1521388", "nulls": 0, "units": "hours"}
        self._run_json_equal(url, expected)

    def test__api_meta_range_endpoints_right_ascension_VGISS_hms(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: right ascension VGISS hms"
        url = '/api/meta/range/endpoints/rightasc.json?volumeid=VGISS_6210&units=hms'
        expected = {"min": "12h 48m 01.6805s", "max": "16h 09m 07.6997s", "nulls": 0, "units": "hms"}
        self._run_json_equal(url, expected)

    def test__api_meta_range_endpoints_right_ascension_VGISS_radians(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: right ascension VGISS radians"
        url = '/api/meta/range/endpoints/rightasc.json?volumeid=VGISS_6210&units=radians'
        expected = {"min": "3.35115437", "max": "4.22862005", "nulls": 0, "units": "radians"}
        self._run_json_equal(url, expected)

    # Image / Pixel Size (integer return)
    def test__api_meta_range_endpoints_greaterpixelsize_COISS(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: greaterpixelsize COISS"
        url = '/api/meta/range/endpoints/greaterpixelsize.json?instrument=Cassini+ISS'
        expected = {'max': '1024', 'min': '256', 'nulls': 0, "units": None}
        self._run_json_equal(url, expected)

    def test__api_meta_range_endpoints_lesserpixelsize_COISS(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: lesserpixelsize COISS"
        url = '/api/meta/range/endpoints/lesserpixelsize.json?instrument=Cassini+ISS'
        expected = {'min': '256', 'max': '1024', 'nulls': 0, "units": None}
        self._run_json_equal(url, expected)

    def test__api_meta_range_endpoints_greaterpixelsize_GOSSI(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: greaterpixelsize GOSSI"
        url = '/api/meta/range/endpoints/greaterpixelsize.json?instrument=Galileo+SSI'
        expected = {'min': '800', 'max': '800', 'nulls': 0, "units": None}
        self._run_json_equal(url, expected)

    def test__api_meta_range_endpoints_lesserpixelsize_GOSSI(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: lesserpixelsize GOSSI"
        url = '/api/meta/range/endpoints/lesserpixelsize.json?instrument=Galileo+SSI'
        expected = {'min': '800', 'max': '800', 'nulls': 0, "units": None}
        self._run_json_equal(url, expected)

    def test__api_meta_range_endpoints_lesserpixelsize_html_GOSSI(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: lesserpixelsize GOSSI html"
        url = '/api/meta/range/endpoints/lesserpixelsize.html?instrument=Galileo+SSI'
        expected = b'<dl>\n<dt>min</dt><dd>800</dd>\n<dt>max</dt><dd>800</dd>\n<dt>nulls</dt><dd>0</dd>\n<dt>units</dt><dd>None</dd>\n</dl>\n'
        self._run_html_equal(url, expected)

    def test__api_meta_range_endpoints_lesserpixelsize_csv_GOSSI(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: lesserpixelsize GOSSI csv"
        url = '/api/meta/range/endpoints/lesserpixelsize.csv?instrument=Galileo+SSI'
        expected = b'min,max,nulls,units\n800,800,0,\n'
        self._run_csv_equal(url, expected)

    # We don't do greater/lesserpixelsize for VGISS because it can change in
    # different volumes.

    # Image / Intensity Levels (integer return)
    def test__api_meta_range_endpoints_levels1_COISS(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: levels1 COISS"
        url = '/api/meta/range/endpoints/levels.json?instrument=Cassini+ISS'
        expected = {'min': '4096', 'max': '4096', 'nulls': 0, "units": None}
        self._run_json_equal(url, expected)

    def test__api_meta_range_endpoints_levels1_COVIMS(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: levels1 COVIMS"
        url = '/api/meta/range/endpoints/levels.json?instrument=Cassini+VIMS&observationtype=Spectral+Cube,Time+Series&imagetype=Raster+Scan'
        expected = {'min': '4096', 'max': '4096', 'nulls': 0, "units": None}
        self._run_json_equal(url, expected)

    def test__api_meta_range_endpoints_levels1_GOSSI(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: levels1 GOSSI"
        url = '/api/meta/range/endpoints/levels.json?instrument=Galileo+SSI'
        expected = {'min': '256', 'max': '256', 'nulls': 0, "units": None}
        self._run_json_equal(url, expected)

    def test__api_meta_range_endpoints_levels1_VGISS(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: levels1 VGISS"
        url = '/api/meta/range/endpoints/levels.json?instrument=Voyager+ISS'
        expected = {'min': '256', 'max': '256', 'nulls': 0, "units": None}
        self._run_json_equal(url, expected)

    def test__api_meta_range_endpoints_levels_constrained_VGISS(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: levels1 VGISS constrained"
        url = '/api/meta/range/endpoints/levels.json?instrument=Voyager+ISS&levels1=5&levels2=10'
        expected = {'min': '256', 'max': '256', 'nulls': 0, "units": None}
        self._run_json_equal(url, expected)

    # reqno
    def test__api_meta_range_endpoints_lesserpixelsize_GOSSI_reqno(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: greaterpixelsize GOSSI reqno"
        url = '/api/meta/range/endpoints/lesserpixelsize.json?instrument=Galileo+SSI&reqno=12345'
        expected = {'min': '800', 'max': '800', 'nulls': 0, "units": None}
        self._run_json_equal(url, expected)

    def test__api_meta_range_endpoints_lesserpixelsize_GOSSI_reqno_internal(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: greaterpixelsize GOSSI reqno internal"
        url = '/__api/meta/range/endpoints/lesserpixelsize.json?instrument=Galileo+SSI&reqno=12345'
        expected = {'min': '800', 'max': '800', 'nulls': 0, 'reqno': 12345, "units": None}
        self._run_json_equal(url, expected)

    def test__api_meta_range_endpoints_lesserpixelsize_GOSSI_reqno_bad_internal(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: greaterpixelsize GOSSI reqno bad internal"
        url = '/__api/meta/range/endpoints/lesserpixelsize.json?instrument=Galileo+SSI&reqno=NaN'
        self._run_status_equal(url, 404,
                    HTTP404_BAD_OR_MISSING_REQNO(
                            '/__api/meta/range/endpoints/lesserpixelsize.json'))

    def test__api_meta_range_endpoints_lesserpixelsize_GOSSI_reqno_bad_internal_2(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: greaterpixelsize GOSSI reqno bad internal 2"
        url = '/__api/meta/range/endpoints/lesserpixelsize.json?instrument=Galileo+SSI&reqno=-101010'
        self._run_status_equal(url, 404,
                    HTTP404_BAD_OR_MISSING_REQNO(
                            '/__api/meta/range/endpoints/lesserpixelsize.json'))

    def test__api_meta_range_endpoints_lesserpixelsize_GOSSI_html_reqno(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: greaterpixelsize GOSSI html reqno"
        url = '/api/meta/range/endpoints/lesserpixelsize.html?instrument=Galileo+SSI&reqno=1e38'
        expected = b'<dl>\n<dt>min</dt><dd>800</dd>\n<dt>max</dt><dd>800</dd>\n<dt>nulls</dt><dd>0</dd>\n<dt>units</dt><dd>None</dd>\n</dl>\n'
        self._run_html_equal(url, expected)

    def test__api_meta_range_endpoints_lesserpixelsize_GOSSI_csv_reqno(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: greaterpixelsize GOSSI csv reqno"
        url = '/api/meta/range/endpoints/lesserpixelsize.csv?instrument=Galileo+SSI&reqno=12345'
        expected = b'min,max,nulls,units\n800,800,0,\n'
        self._run_csv_equal(url, expected)

    # Ring Geo / Ring Radius (floating point return)
    def test__api_meta_range_endpoints_ring_radius_VGISS_km(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: ring radius VGISS km"
        url = '/api/meta/range/endpoints/RINGGEOringradius.json?volumeid=VGISS_6210&units=km'
        expected = {"min": "60268.051", "max": "3047750.647", "nulls": 10, "units": "km"}
        self._run_json_equal(url, expected)

    def test__api_meta_range_endpoints_ring_radius_VGISS_rj(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: ring radius VGISS RJ"
        url = '/api/meta/range/endpoints/RINGGEOringradius.json?volumeid=VGISS_6210&units=jupiterradii'
        expected = {"min": "0.84300412634", "max": "42.6306530381", "nulls": 10, "units": "jupiterradii"}
        self._run_json_equal(url, expected)

    def test__api_meta_range_endpoints_ring_radius_VGISS_rs(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: ring radius VGISS RS"
        url = '/api/meta/range/endpoints/RINGGEOringradius.json?volumeid=VGISS_6210&units=saturnradii'
        expected = {"min": "0.99897316426", "max": "50.51799514338", "nulls": 10, "units": "saturnradii"}
        self._run_json_equal(url, expected)

    def test__api_meta_range_endpoints_ring_radius_VGISS_ru(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: ring radius VGISS RU"
        url = '/api/meta/range/endpoints/RINGGEOringradius.json?volumeid=VGISS_6210&units=uranusradii'
        expected = {"min": "2.35799722211", "max": "119.24373594429", "nulls": 10, "units": "uranusradii"}
        self._run_json_equal(url, expected)

    def test__api_meta_range_endpoints_ring_radius_VGISS_rn(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: ring radius VGISS RN"
        url = '/api/meta/range/endpoints/RINGGEOringradius.json?volumeid=VGISS_6210&units=neptuneradii'
        expected = {"min": "2.38921906838", "max": "120.82262227948", "nulls": 10, "units": "neptuneradii"}
        self._run_json_equal(url, expected)

    # Bad queries
    def test__api_meta_range_endpoints_bad_search(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: bad search"
        url = '/__api/meta/range/endpoints/lesserpixelsize.json?observationduration=1x2'
        self._run_status_equal(url, 404,
                    HTTP404_SEARCH_PARAMS_INVALID(
                            '/__api/meta/range/endpoints/lesserpixelsize.json'))

    def test__api_meta_range_endpoints_bad_slug(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: bad slug name"
        url = '/__api/meta/range/endpoints/badslug.json?instrument=Cassini+ISS'
        self._run_status_equal(url, 404,
                    HTTP404_UNKNOWN_SLUG('badslug',
                                '/__api/meta/range/endpoints/badslug.json'))


            ##########################################
            ######### /api/fields: API TESTS #########
            ##########################################

    # Test caching (only visible with code coverage)
    def test__api_fields_time1_cache(self):
        "[test_metadata_api.py] /api/fields: time1 json cache"
        url = '/api/fields/time1.json'
        expected = {"data": {"General Constraints": {"time1": {"label": "Observation Start Time", "search_label": "Observation Time", "full_label": "Observation Start Time", "full_search_label": "Observation Time [General]", "category": "General Constraints", "slug": "time1", "field_id": "time1", "old_slug": "timesec1", 'linked': False, "default_units": "ymdhms", "available_units": ['ymdhms', 'ydhms', 'jd', 'jed', 'mjd', 'mjed', 'et'], "type": "range_time"}}}}
        self._run_json_equal(url, expected)
        url = '/api/fields/time1.json'
        expected = {"data": {"General Constraints": {"time1": {"label": "Observation Start Time", "search_label": "Observation Time", "full_label": "Observation Start Time", "full_search_label": "Observation Time [General]", "category": "General Constraints", "slug": "time1", "field_id": "time1", "old_slug": "timesec1", 'linked': False, "default_units": "ymdhms", "available_units": ['ymdhms', 'ydhms', 'jd', 'jed', 'mjd', 'mjed', 'et'], "type": "range_time"}}}}
        self._run_json_equal(url, expected)
        url = '/api/fields/time1.json'
        expected = {"data": {"General Constraints": {"time1": {"label": "Observation Start Time", "search_label": "Observation Time", "full_label": "Observation Start Time", "full_search_label": "Observation Time [General]", "category": "General Constraints", "slug": "time1", "field_id": "time1", "old_slug": "timesec1", 'linked': False, "default_units": "ymdhms", "available_units": ['ymdhms', 'ydhms', 'jd', 'jed', 'mjd', 'mjed', 'et'], "type": "range_time"}}}}
        self._run_json_equal(url, expected)
        url = '/api/fields/time1.json'
        expected = {"data": {"General Constraints": {"time1": {"label": "Observation Start Time", "search_label": "Observation Time", "full_label": "Observation Start Time", "full_search_label": "Observation Time [General]", "category": "General Constraints", "slug": "time1", "field_id": "time1", "old_slug": "timesec1", 'linked': False, "default_units": "ymdhms", "available_units": ['ymdhms', 'ydhms', 'jd', 'jed', 'mjd', 'mjed', 'et'], "type": "range_time"}}}}
        self._run_json_equal(url, expected)
        url = '/api/fields/time1.json'
        expected = {"data": {"General Constraints": {"time1": {"label": "Observation Start Time", "search_label": "Observation Time", "full_label": "Observation Start Time", "full_search_label": "Observation Time [General]", "category": "General Constraints", "slug": "time1", "field_id": "time1", "old_slug": "timesec1", 'linked': False, "default_units": "ymdhms", "available_units": ['ymdhms', 'ydhms', 'jd', 'jed', 'mjd', 'mjed', 'et'], "type": "range_time"}}}}
        self._run_json_equal(url, expected)
        url = '/api/fields/time1.json'
        expected = {"data": {"General Constraints": {"time1": {"label": "Observation Start Time", "search_label": "Observation Time", "full_label": "Observation Start Time", "full_search_label": "Observation Time [General]", "category": "General Constraints", "slug": "time1", "field_id": "time1", "old_slug": "timesec1", 'linked': False, "default_units": "ymdhms", "available_units": ['ymdhms', 'ydhms', 'jd', 'jed', 'mjd', 'mjed', 'et'], "type": "range_time"}}}}
        self._run_json_equal(url, expected)

    def test__api_fields_time1_json(self):
        "[test_metadata_api.py] /api/fields: time1 json"
        url = '/api/fields/time1.json'
        expected = {"data": {"General Constraints": {"time1": {"label": "Observation Start Time", "search_label": "Observation Time", "full_label": "Observation Start Time", "full_search_label": "Observation Time [General]", "category": "General Constraints", "slug": "time1", "field_id": "time1", "old_slug": "timesec1", 'linked': False, "default_units": "ymdhms", "available_units": ['ymdhms', 'ydhms', 'jd', 'jed', 'mjd', 'mjed', 'et'], "type": "range_time"}}}}
        self._run_json_equal(url, expected)

    def test__api_fields_time1_csv(self):
        "[test_metadata_api.py] /api/fields: time1 csv"
        url = '/api/fields/time1.csv'
        self._run_html_equal_file(url, 'api_fields_time1_csv.csv')

    def test__api_fields_all_json(self):
        "[test_metadata_api.py] /api/fields: all json and collapse"
        url = '/api/fields.json'
        print(url)
        response = self._get_response(url)
        self.assertEqual(response.status_code, 200)
        jdata = json.loads(response.content)
        num_fields = len(jdata['data'])
        url = '/api/fields.json?collapse=1'
        print(url)
        response = self._get_response(url)
        self.assertEqual(response.status_code, 200)
        jdata = json.loads(response.content)
        num_fields_collapse = len(jdata['data'])
        self.assertLess(num_fields_collapse, num_fields)

    def test__api_fields_all_csv(self):
        "[test_metadata_api.py] /api/fields: all csv and collapse"
        url = '/api/fields.csv'
        print(url)
        response = self._get_response(url)
        self.assertEqual(response.status_code, 200)
        num_fields = len(self._cleanup_csv(response.content).split('\\n'))
        url = '/api/fields.csv?collapse=1'
        print(url)
        response = self._get_response(url)
        self.assertEqual(response.status_code, 200)
        num_fields_collapse = len(self._cleanup_csv(response.content)
                                  .split('\\n'))
        self.assertLess(num_fields_collapse, num_fields)

    def test__api_fields_all_bad_collapse(self):
        "[test_metadata_api.py] /api/fields: all json bad collapse"
        url = '/api/fields.json?collapse=X'
        self._run_status_equal(url, 404,
                        HTTP404_BAD_COLLAPSE('X', '/api/fields.json'))

    def test__api_fields_all_cache(self):
        "[test_metadata_api.py] /api/fields: all json cache"
        url = '/api/fields.json'
        print(url)
        response = self._get_response(url)
        self.assertEqual(response.status_code, 200)
        jdata1 = json.loads(response.content)
        url = '/api/fields.json'
        print(url)
        response = self._get_response(url)
        self.assertEqual(response.status_code, 200)
        jdata2 = json.loads(response.content)
        url = '/api/fields.json?collapse=1'
        print(url)
        response = self._get_response(url)
        self.assertEqual(response.status_code, 200)
        jdatac1 = json.loads(response.content)
        url = '/api/fields.json'
        print(url)
        response = self._get_response(url)
        self.assertEqual(response.status_code, 200)
        jdata3 = json.loads(response.content)
        url = '/api/fields.json?collapse=1'
        print(url)
        response = self._get_response(url)
        self.assertEqual(response.status_code, 200)
        jdatac2 = json.loads(response.content)
        self.assertEqual(jdata1, jdata2)
        self.assertEqual(jdata2, jdata3)
        self.assertEqual(jdatac1, jdatac2)
        self.assertNotEqual(jdata1, jdatac1)
