# opus/application/test_api/test_metadata_api.py

import json
import logging
import requests
import sys
from unittest import TestCase

from django.core.cache import cache
from rest_framework.test import RequestsClient

from api_test_helper import ApiTestHelper

import settings

class ApiMetadataTests(TestCase, ApiTestHelper):

    def setUp(self):
        self.maxDiff = None
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
        url = '/opus/api/meta/result_count.json?volumeid=COISS_2111&target=PAN&reqno=1'
        self._run_result_count_equal(url, 56)
        url = '/opus/api/meta/result_count.json?volumeid=COISS_2111&target=PAN&reqno=2'
        self._run_result_count_equal(url, 56)
        url = '/opus/api/meta/result_count.json?volumeid=COISS_2111&target=PAN&reqno=3'
        self._run_result_count_equal(url, 56)
        url = '/opus/api/meta/result_count.json?volumeid=COISS_2111&target=PAN&reqno=1'
        self._run_result_count_equal(url, 56)
        url = '/opus/api/meta/result_count.json?volumeid=COISS_2111&target=PAN&reqno=2'
        self._run_result_count_equal(url, 56)
        url = '/opus/api/meta/result_count.json?volumeid=COISS_2111&target=PAN&reqno=3'
        self._run_result_count_equal(url, 56)

    # No arguments
    def test__api_meta_result_count_all(self):
        "[test_metadata_api.py] /api/meta/result_count: no search criteria"
        url = '/opus/api/meta/result_count.json'
        self._run_result_count_greater_equal(url, 26493) # Assume required volumes

    def test__api_meta_result_count_all_internal(self):
        "[test_metadata_api.py] /api/meta/result_count: no search criteria internal"
        url = '/opus/__api/meta/result_count.json?reqno=1'
        self._run_result_count_greater_equal(url, 26493, 1) # Assume required volumes

    # Extra args
    def test__api_meta_result_count_with_url_cruft(self):
        "[test_metadata_api.py] /api/meta/result_count: with extra URL cruft"
        url = '/opus/api/meta/result_count.json?volumeid=COISS_2111&timesec1=2017-03-01T00:00:00&timesec2=2017-03-15T12:00:00&view=search&browse=data&colls_browse=gallery&page=1&gallery_data_viewer=true&limit=100&order=time1&cols=opusid,instrumentid,planet,target,time1,observationduration&widgets=timesec1,COISSshuttermode,volumeid,planet,target&widgets2=&detail='
        self._run_result_count_equal(url, 1321)

    # Mults
    def test__api_meta_result_count_planet(self):
        "[test_metadata_api.py] /api/meta/result_count: planet=Saturn"
        url = '/opus/api/meta/result_count.json?planet=Saturn'
        self._run_result_count_greater_equal(url, 15486) # Assume required volumes

    def  test__api_meta_result_count_target_pan(self):
        "[test_metadata_api.py] /api/meta/result_count: with target=Pan"
        url = '/opus/api/meta/result_count.json?volumeid=COISS_2111&target=PAN'
        self._run_result_count_equal(url, 56)

    def  test__api_meta_result_count_target_s_rings(self):
        "[test_metadata_api.py] /api/meta/result_count: with target=S Rings"
        url = '/opus/api/meta/result_count.json?planet=Saturn&volumeid=COISS_2111&target=S+Rings'
        self._run_result_count_equal(url, 1040)

    def  test__api_meta_result_count_multi_target(self):
        "[test_metadata_api.py] /api/meta/result_count: with target=Iapetus,Methone"
        url = '/opus/api/meta/result_count.json?planet=Saturn&volumeid=COISS_2111&target=Iapetus,Methone'
        self._run_result_count_equal(url, 129)

    # Strings
    def test__api_meta_result_count_string_no_qtype(self):
        "[test_metadata_api.py] /api/meta/result_count: primaryfilespec=1866365558 no qtype"
        url = '/opus/api/meta/result_count.json?primaryfilespec=1866365558'
        self._run_result_count_equal(url, 2) # BOTSIM

    def test__api_meta_result_count_string_contains(self):
        "[test_metadata_api.py] /api/meta/result_count: primaryfilespec=1866365558 qtype=contains"
        url = '/opus/api/meta/result_count.json?primaryfilespec=1866365558&qtype-primaryfilespec=contains'
        self._run_result_count_equal(url, 2) # BOTSIM

    def test__api_meta_result_count_string_begins(self):
        "[test_metadata_api.py] /api/meta/result_count: primaryfilespec=1866365558 qtype=begins"
        url = '/opus/api/meta/result_count.json?primaryfilespec=1866365558&qtype-primaryfilespec=begins'
        self._run_result_count_equal(url, 0)

    def test__api_meta_result_count_string_ends(self):
        "[test_metadata_api.py] /api/meta/result_count: primaryfilespec=1866365558_1.IMG qtype=ends"
        url = '/opus/api/meta/result_count.json?primaryfilespec=1866365558_1.IMG&qtype-primaryfilespec=ends'
        self._run_result_count_equal(url, 2)

    # Times
    def test__api_meta_result_count_times(self):
        "[test_metadata_api.py] /api/meta/result_count: time range"
        url = '/opus/api/meta/result_count.json?planet=Saturn&volumeid=COISS_2111&timesec1=2017-03-01T00:00:00&timesec2=2017-03-15T12:00:00'
        self._run_result_count_equal(url, 1321)

    # 1-column numeric range
    def test__api_meta_result_count_obs_duration(self):
        "[test_metadata_api.py] /api/meta/result_count: with observation duration"
        url = '/opus/api/meta/result_count.json?volumeid=COISS_2002&observationduration1=.01&observationduration2=.02'
        self._run_result_count_equal(url, 2)

    # 2-column numeric range
    def test__api_meta_result_count_ring_rad_range(self):
        "[test_metadata_api.py] /api/meta/result_count: with ring radius range, no qtype"
        url = '/opus/api/meta/result_count.json?volumeid=COISS_2111&RINGGEOringradius1=70000&RINGGEOringradius2=80000'
        self._run_result_count_equal(url, 490)

    def test__api_meta_result_count_ring_rad_range_all(self):
        "[test_metadata_api.py] /api/meta/result_count: with ring radius range, qtype=all"
        url = '/opus/api/meta/result_count.json?volumeid=COISS_2111&RINGGEOringradius1=70000&RINGGEOringradius2=80000&qtype-RINGGEOringradius=all'
        self._run_result_count_equal(url, 217)

    def test__api_meta_result_count_ring_rad_range_only(self):
        "[test_metadata_api.py] /api/meta/result_count: with ring radius range, qtype=only"
        url = '/opus/api/meta/result_count.json?volumeid=COISS_2111&RINGGEOringradius1=70000&RINGGEOringradius2=80000&qtype-RINGGEOringradius=only'
        self._run_result_count_equal(url, 26)

    # Voyager spacecraft clock count
    def test__api_meta_result_count_voyager_sclk_any(self):
        "[test_metadata_api.py] /api/meta/result_count: voyager sclk any"
        url = '/opus/api/meta/result_count.json?instrument=Voyager+ISS&insthost=Voyager+2&VOYAGERspacecraftclockcount1=43600:00:775&VOYAGERspacecraftclockcount2=43600:06:780&qtype-VOYAGERspacecraftclockcount=any'
        self._run_result_count_equal(url, 3)

    def test__api_meta_result_count_voyager_sclk_all(self):
        "[test_metadata_api.py] /api/meta/result_count: voyager sclk all"
        url = '/opus/api/meta/result_count.json?instrument=Voyager+ISS&insthost=Voyager+2&VOYAGERspacecraftclockcount1=43600:00:775&VOYAGERspacecraftclockcount2=43600:06:780&qtype-VOYAGERspacecraftclockcount=all'
        self._run_result_count_equal(url, 0)

    def test__api_meta_result_count_voyager_sclk_only(self):
        "[test_metadata_api.py] /api/meta/result_count: voyager sclk only"
        url = '/opus/api/meta/result_count.json?instrument=Voyager+ISS&insthost=Voyager+2&VOYAGERspacecraftclockcount1=43600:00:775&VOYAGERspacecraftclockcount2=43600:06:780&qtype-VOYAGERspacecraftclockcount=only'
        self._run_result_count_equal(url, 1)

    # Other return formats
    def test__api_meta_result_count_html(self):
        "[test_metadata_api.py] /api/meta/result_count: primaryfilespec=1866365558 no qtype html"
        url = '/opus/api/meta/result_count.html?primaryfilespec=1866365558'
        expected = b'<dl>\n<dt>result_count</dt><dd>2</dd>\n</dl>\n'
        self._run_html_equal(url, expected) # BOTSIM

    def test__api_meta_result_count_csv(self):
        "[test_metadata_api.py] /api/meta/result_count: primaryfilespec=1866365558 no qtype csv"
        url = '/opus/api/meta/result_count.csv?primaryfilespec=1866365558'
        expected = b'result count,2\n'
        self._run_csv_equal(url, expected) # BOTSIM

    def test__api_meta_result_count_html_internal(self):
        "[test_metadata_api.py] /api/meta/result_count: primaryfilespec=1866365558 no qtype html internal"
        url = '/opus/__api/meta/result_count.html?primaryfilespec=1866365558'
        expected = b'<dl>\n<dt>result_count</dt><dd>2</dd>\n</dl>\n'
        self._run_status_equal(url, 404)

    def test__api_meta_result_count_csv_internal(self):
        "[test_metadata_api.py] /api/meta/result_count: primaryfilespec=1866365558 no qtype csv internal"
        url = '/opus/__api/meta/result_count.csv?primaryfilespec=1866365558'
        expected = b'result count,2\n'
        self._run_status_equal(url, 404)

    # reqno
    def test__api_meta_result_count_string_no_qtype_reqno(self):
        "[test_metadata_api.py] /api/meta/result_count: primaryfilespec=1866365558 no qtype reqno"
        url = '/opus/api/meta/result_count.json?primaryfilespec=1866365558&reqno=12345'
        self._run_result_count_equal(url, 2) # BOTSIM

    def test__api_meta_result_count_string_no_qtype_reqno_internal(self):
        "[test_metadata_api.py] /api/meta/result_count: primaryfilespec=1866365558 no qtype reqno internal"
        url = '/opus/__api/meta/result_count.json?primaryfilespec=1866365558&reqno=12345'
        self._run_result_count_equal(url, 2, 12345) # BOTSIM

    def test__api_meta_result_count_string_no_qtype_reqno_bad_internal(self):
        "[test_metadata_api.py] /api/meta/result_count: primaryfilespec=1866365558 no qtype reqno bad internal"
        url = '/opus/__api/meta/result_count.json?primaryfilespec=1866365558&reqno=NaN'
        self._run_status_equal(url, 404,
                               settings.HTTP404_MISSING_REQNO)

    def test__api_meta_result_count_string_no_qtype_reqno_bad_internal_2(self):
        "[test_metadata_api.py] /api/meta/result_count: primaryfilespec=1866365558 no qtype reqno bad internal 2"
        url = '/opus/__api/meta/result_count.json?primaryfilespec=1866365558&reqno=-1'
        self._run_status_equal(url, 404,
                               settings.HTTP404_MISSING_REQNO)

    def test__api_meta_result_count_html_reqno(self):
        "[test_metadata_api.py] /api/meta/result_count: primaryfilespec=1866365558 no qtype reqno html"
        url = '/opus/api/meta/result_count.html?primaryfilespec=1866365558&reqno=100'
        expected = b'<dl>\n<dt>result_count</dt><dd>2</dd>\n</dl>\n'
        self._run_html_equal(url, expected) # BOTSIM

    def test__api_meta_result_count_csv_reqno(self):
        "[test_metadata_api.py] /api/meta/result_count: primaryfilespec=1866365558 no qtype reqno csv"
        url = '/opus/api/meta/result_count.csv?primaryfilespec=1866365558&reqno=NaN'
        expected = b'result count,2\n'
        self._run_csv_equal(url, expected) # BOTSIM

    # Bad queries
    def test__api_meta_result_count_bad_slug(self):
        "[test_metadata_api.py] /api/meta/result_count: with bad slug"
        url = '/opus/api/meta/result_count.json?volumeid=COISS_2111&RINGGEOringradius1=70000&RINGGEOringradius3=80000&qtype-RINGGEOringradius=only'
        self._run_status_equal(url, 404,
                               settings.HTTP404_SEARCH_PARAMS_INVALID)

    def test__api_meta_result_count_bad_value(self):
        "[test_metadata_api.py] /api/meta/result_count: with bad value"
        url = '/opus/api/meta/result_count.json?observationduration=1X2'
        self._run_status_equal(url, 404,
                               settings.HTTP404_SEARCH_PARAMS_INVALID)


            ##############################################
            ######### /api/meta/mults: API TESTS #########
            ##############################################

    # Caching (only visible through code coverage)
    def test__api_meta_mults_cache(self):
        "[test_metadata_api.py] /api/meta/meta/mults: cache"
        url = '/opus/__api/meta/mults/target.json?volumeid=COISS_2111&reqno=1'
        expected = {"field": "target", "mults": {"Atlas": 2, "Daphnis": 4, "Enceladus": 271, "Epimetheus": 27, "Hyrrokkin": 140, "Iapetus": 127, "Janus": 4, "Methone": 2, "Pallene": 2, "Pan": 56,
                    "Polydeuces": 2, "Prometheus": 4, "Saturn": 1483, "Saturn Rings": 1040, "Sky": 90, "Telesto": 2, "Tethys": 11, "Titan": 384, "Unknown": 16}, "reqno": 1}
        self._run_json_equal(url, expected)
        url = '/opus/__api/meta/mults/target.json?volumeid=COISS_2111&reqno=2'
        expected = {"field": "target", "mults": {"Atlas": 2, "Daphnis": 4, "Enceladus": 271, "Epimetheus": 27, "Hyrrokkin": 140, "Iapetus": 127, "Janus": 4, "Methone": 2, "Pallene": 2, "Pan": 56,
                    "Polydeuces": 2, "Prometheus": 4, "Saturn": 1483, "Saturn Rings": 1040, "Sky": 90, "Telesto": 2, "Tethys": 11, "Titan": 384, "Unknown": 16}, "reqno": 2}
        self._run_json_equal(url, expected)
        url = '/opus/__api/meta/mults/target.json?volumeid=COISS_2111&reqno=3'
        expected = {"field": "target", "mults": {"Atlas": 2, "Daphnis": 4, "Enceladus": 271, "Epimetheus": 27, "Hyrrokkin": 140, "Iapetus": 127, "Janus": 4, "Methone": 2, "Pallene": 2, "Pan": 56,
                    "Polydeuces": 2, "Prometheus": 4, "Saturn": 1483, "Saturn Rings": 1040, "Sky": 90, "Telesto": 2, "Tethys": 11, "Titan": 384, "Unknown": 16}, "reqno": 3}
        self._run_json_equal(url, expected)
        url = '/opus/__api/meta/mults/target.json?volumeid=COISS_2111&reqno=1'
        expected = {"field": "target", "mults": {"Atlas": 2, "Daphnis": 4, "Enceladus": 271, "Epimetheus": 27, "Hyrrokkin": 140, "Iapetus": 127, "Janus": 4, "Methone": 2, "Pallene": 2, "Pan": 56,
                    "Polydeuces": 2, "Prometheus": 4, "Saturn": 1483, "Saturn Rings": 1040, "Sky": 90, "Telesto": 2, "Tethys": 11, "Titan": 384, "Unknown": 16}, "reqno": 1}
        self._run_json_equal(url, expected)
        url = '/opus/__api/meta/mults/target.json?volumeid=COISS_2111&reqno=2'
        expected = {"field": "target", "mults": {"Atlas": 2, "Daphnis": 4, "Enceladus": 271, "Epimetheus": 27, "Hyrrokkin": 140, "Iapetus": 127, "Janus": 4, "Methone": 2, "Pallene": 2, "Pan": 56,
                    "Polydeuces": 2, "Prometheus": 4, "Saturn": 1483, "Saturn Rings": 1040, "Sky": 90, "Telesto": 2, "Tethys": 11, "Titan": 384, "Unknown": 16}, "reqno": 2}
        self._run_json_equal(url, expected)
        url = '/opus/__api/meta/mults/target.json?volumeid=COISS_2111&reqno=3'
        expected = {"field": "target", "mults": {"Atlas": 2, "Daphnis": 4, "Enceladus": 271, "Epimetheus": 27, "Hyrrokkin": 140, "Iapetus": 127, "Janus": 4, "Methone": 2, "Pallene": 2, "Pan": 56,
                    "Polydeuces": 2, "Prometheus": 4, "Saturn": 1483, "Saturn Rings": 1040, "Sky": 90, "Telesto": 2, "Tethys": 11, "Titan": 384, "Unknown": 16}, "reqno": 3}
        self._run_json_equal(url, expected)

    # Unrelated constraints
    def test__api_meta_mults_COISS_2111(self):
        "[test_metadata_api.py] /api/meta/meta/mults: for COISS_2111"
        url = '/opus/api/meta/mults/target.json?volumeid=COISS_2111'
        expected = {"field": "target", "mults": {"Atlas": 2, "Daphnis": 4, "Enceladus": 271, "Epimetheus": 27, "Hyrrokkin": 140, "Iapetus": 127, "Janus": 4, "Methone": 2, "Pallene": 2, "Pan": 56,
                    "Polydeuces": 2, "Prometheus": 4, "Saturn": 1483, "Saturn Rings": 1040, "Sky": 90, "Telesto": 2, "Tethys": 11, "Titan": 384, "Unknown": 16}}
        self._run_json_equal(url, expected)

    def test__api_meta_mults_COISS_2111_internal(self):
        "[test_metadata_api.py] /api/meta/meta/mults: for COISS_2111 internal"
        url = '/opus/__api/meta/mults/target.json?volumeid=COISS_2111&reqno=1'
        expected = {"field": "target", "mults": {"Atlas": 2, "Daphnis": 4, "Enceladus": 271, "Epimetheus": 27, "Hyrrokkin": 140, "Iapetus": 127, "Janus": 4, "Methone": 2, "Pallene": 2, "Pan": 56,
                    "Polydeuces": 2, "Prometheus": 4, "Saturn": 1483, "Saturn Rings": 1040, "Sky": 90, "Telesto": 2, "Tethys": 11, "Titan": 384, "Unknown": 16}, "reqno": 1}
        self._run_json_equal(url, expected)

    def test__api_meta_mults_COISS_2111_saturn(self):
        "[test_metadata_api.py] /api/meta/meta/mults: for COISS_2111 planet Saturn"
        url = '/opus/api/meta/mults/target.json?volumeid=COISS_2111&planet=Saturn'
        expected = {"field": "target", "mults": {"Atlas": 2, "Daphnis": 4, "Enceladus": 271, "Epimetheus": 27, "Hyrrokkin": 140, "Iapetus": 127, "Janus": 4, "Methone": 2, "Pallene": 2, "Pan": 56,
                    "Polydeuces": 2, "Prometheus": 4, "Saturn": 1483, "Saturn Rings": 1040, "Sky": 90, "Telesto": 2, "Tethys": 11, "Titan": 384, "Unknown": 16}}
        self._run_json_equal(url, expected)

    def test__api_meta_mults_COISS_2111_jupiter(self):
        "[test_metadata_api.py] /api/meta/meta/mults: for COISS_2111 planet Jupiter"
        url = '/opus/api/meta/mults/target.json?volumeid=COISS_2111&planet=Jupiter'
        expected = {"field": "target", "mults": {}}
        self._run_json_equal(url, expected)

    # Related constraint
    def test__api_meta_mults_COISS_2111_pan(self):
        "[test_metadata_api.py] /api/meta/meta/mults: for COISS_2111 target Pan"
        url = '/opus/api/meta/mults/target.json?volumeid=COISS_2111&planet=Saturn&target=Pan'
        expected = {"field": "target", "mults": {"Atlas": 2, "Daphnis": 4, "Enceladus": 271, "Epimetheus": 27, "Hyrrokkin": 140, "Iapetus": 127, "Janus": 4, "Methone": 2, "Pallene": 2, "Pan": 56,
                    "Polydeuces": 2, "Prometheus": 4, "Saturn": 1483, "Saturn Rings": 1040, "Sky": 90, "Telesto": 2, "Tethys": 11, "Titan": 384, "Unknown": 16}}
        self._run_json_equal(url, expected)

    def test__api_meta_mults_COISS_2111_dione(self):
        "[test_metadata_api.py] /api/meta/meta/mults: for COISS_2111 target Dione targetclass"
        url = '/opus/api/meta/mults/target.json?volumeid=COISS_2111&targetclass=Regular+Satellite&target=Dione'
        expected = {"field": "target", "mults": {"Atlas": 2, "Daphnis": 4, "Enceladus": 271, "Epimetheus": 27, "Iapetus": 127, "Janus": 4, "Methone": 2, "Pallene": 2, "Pan": 56, "Polydeuces": 2, "Prometheus": 4, "Telesto": 2, "Tethys": 11, "Titan": 384}}
        self._run_json_equal(url, expected)

    def test__api_meta_mults_COISS_2111_dione_2(self):
        "[test_metadata_api.py] /api/meta/meta/mults: for COISS_2111 target Dione targetclass 2"
        url = '/opus/api/meta/mults/targetclass.json?volumeid=COISS_2111&targetclass=Regular+Satellite&target=Dione'
        expected = {"field": "targetclass", "mults": {}}
        self._run_json_equal(url, expected)

    def test__api_meta_mults_COISS_2111_daphnis(self):
        "[test_metadata_api.py] /api/meta/meta/mults: for COISS_2111 target Daphnis targetclass"
        url = '/opus/api/meta/mults/targetclass.json?volumeid=COISS_2111&targetclass=Regular+Satellite&target=Daphnis'
        expected = {"field": "targetclass", "mults": {"Regular Satellite": 4}}
        self._run_json_equal(url, expected)

    def test__api_meta_mults_COISS_2111_imagetype(self):
        "[test_metadata_api.py] /api/meta/meta/mults: for COISS_2111 imagetype"
        # This joins in a non-obs_general table
        url = '/opus/api/meta/mults/imagetype.json?volumeid=COISS_2111'
        expected = {"field": "imagetype", "mults": {"Frame": 3667}}
        self._run_json_equal(url, expected)

    # Other return formats
    def test__api_meta_mults_NHPELO_2001_json(self):
        "[test_metadata_api.py] /api/meta/meta/mults: for NHPELO_2001 target"
        url = '/opus/api/meta/mults/target.json?instrument=New+Horizons+LORRI&volumeid=NHPELO_2001'
        expected = {"field": "target", "mults": {"2002 Ms4": 60, "2010 Jj124": 90, "Arawn": 290, "Calibration": 6, "Charon": 490, "Chiron": 90, "Hd 205905": 10, "Hd 37962": 10, "Hydra": 143, "Ixion": 60,
                    "Kerberos": 10, "Ngc 3532": 45, "Nix": 102, "Pluto": 5265, "Quaoar": 96, "Styx": 6}}
        self._run_json_equal(url, expected)

    def test__api_meta_mults_NHPELO_2001_csv(self):
        "[test_metadata_api.py] /api/meta/meta/mults: for NHPELO_2001 target csv"
        url = '/opus/api/meta/mults/target.csv?instrument=New+Horizons+LORRI&volumeid=NHPELO_2001'
        expected = b'2002 Ms4,2010 Jj124,Arawn,Calibration,Charon,Chiron,Hd 205905,Hd 37962,Hydra,Ixion,Kerberos,Ngc 3532,Nix,Pluto,Quaoar,Styx\n60,90,290,6,490,90,10,10,143,60,10,45,102,5265,96,6\n'
        self._run_csv_equal(url, expected)

    def test__api_meta_mults_NHPELO_2001_html(self):
        "[test_metadata_api.py] /api/meta/meta/mults: for NHPELO_2001 target html"
        url = '/opus/api/meta/mults/target.html?instrument=New+Horizons+LORRI&volumeid=NHPELO_2001'
        expected = b'<dl>\n<dt>2002 Ms4</dt><dd>60</dd>\n<dt>2010 Jj124</dt><dd>90</dd>\n<dt>Arawn</dt><dd>290</dd>\n<dt>Calibration</dt><dd>6</dd>\n<dt>Charon</dt><dd>490</dd>\n<dt>Chiron</dt><dd>90</dd>\n<dt>Hd 205905</dt><dd>10</dd>\n<dt>Hd 37962</dt><dd>10</dd>\n<dt>Hydra</dt><dd>143</dd>\n<dt>Ixion</dt><dd>60</dd>\n<dt>Kerberos</dt><dd>10</dd>\n<dt>Ngc 3532</dt><dd>45</dd>\n<dt>Nix</dt><dd>102</dd>\n<dt>Pluto</dt><dd>5265</dd>\n<dt>Quaoar</dt><dd>96</dd>\n<dt>Styx</dt><dd>6</dd>\n</dl>\n'
        self._run_html_equal(url, expected)

    def test__api_meta_mults_NHPELO_2001_csv_internal(self):
        "[test_metadata_api.py] /api/meta/meta/mults: for NHPELO_2001 target csv internal"
        url = '/opus/__api/meta/mults/target.csv?instrument=New+Horizons+LORRI&volumeid=NHPELO_2001'
        self._run_status_equal(url, 404)

    def test__api_meta_mults_NHPELO_2001_html_internal(self):
        "[test_metadata_api.py] /api/meta/meta/mults: for NHPELO_2001 target html internal"
        url = '/opus/__api/meta/mults/target.html?instrument=New+Horizons+LORRI&volumeid=NHPELO_2001'
        self._run_status_equal(url, 404)

    # reqno
    def test__api_meta_mults_COISS_2111_saturn_reqno(self):
        "[test_metadata_api.py] /api/meta/meta/mults: for COISS_2111 planet Saturn reqno"
        url = '/opus/api/meta/mults/target.json?volumeid=COISS_2111&planet=Saturn&reqno=98765'
        expected = {"field": "target", "mults": {"Atlas": 2, "Daphnis": 4, "Enceladus": 271, "Epimetheus": 27, "Hyrrokkin": 140, "Iapetus": 127, "Janus": 4, "Methone": 2, "Pallene": 2, "Pan": 56,
                    "Polydeuces": 2, "Prometheus": 4, "Saturn": 1483, "Saturn Rings": 1040, "Sky": 90, "Telesto": 2, "Tethys": 11, "Titan": 384, "Unknown": 16}}
        self._run_json_equal(url, expected)

    def test__api_meta_mults_COISS_2111_saturn_reqno_internal(self):
        "[test_metadata_api.py] /api/meta/meta/mults: for COISS_2111 planet Saturn reqno internal"
        url = '/opus/__api/meta/mults/target.json?volumeid=COISS_2111&planet=Saturn&reqno=98765'
        expected = {"field": "target", "mults": {"Atlas": 2, "Daphnis": 4, "Enceladus": 271, "Epimetheus": 27, "Hyrrokkin": 140, "Iapetus": 127, "Janus": 4, "Methone": 2, "Pallene": 2, "Pan": 56,
                    "Polydeuces": 2, "Prometheus": 4, "Saturn": 1483, "Saturn Rings": 1040, "Sky": 90, "Telesto": 2, "Tethys": 11, "Titan": 384, "Unknown": 16}, "reqno": 98765}
        self._run_json_equal(url, expected)

    def test__api_meta_mults_COISS_2111_saturn_reqno_bad_internal(self):
        "[test_metadata_api.py] /api/meta/meta/mults: for COISS_2111 planet Saturn reqno bad internal"
        url = '/opus/__api/meta/mults/target.json?volumeid=COISS_2111&planet=Saturn&reqno=NaN'
        self._run_status_equal(url, 404, settings.HTTP404_MISSING_REQNO)

    def test__api_meta_mults_COISS_2111_saturn_reqno_bad_internal_2(self):
        "[test_metadata_api.py] /api/meta/meta/mults: for COISS_2111 planet Saturn reqno bad internal 2"
        url = '/opus/__api/meta/mults/target.json?volumeid=COISS_2111&planet=Saturn&reqno=-101010'
        self._run_status_equal(url, 404, settings.HTTP404_MISSING_REQNO)

    def test__api_meta_mults_NHPELO_2001_csv_reqno(self):
        "[test_metadata_api.py] /api/meta/meta/mults: for NHPELO_2001 target reqno csv"
        url = '/opus/api/meta/mults/target.csv?instrument=New+Horizons+LORRI&volumeid=NHPELO_2001&reqno=NaN'
        expected = b'2002 Ms4,2010 Jj124,Arawn,Calibration,Charon,Chiron,Hd 205905,Hd 37962,Hydra,Ixion,Kerberos,Ngc 3532,Nix,Pluto,Quaoar,Styx\n60,90,290,6,490,90,10,10,143,60,10,45,102,5265,96,6\n'
        self._run_csv_equal(url, expected)

    def test__api_meta_mults_NHPELO_2001_html_reqno(self):
        "[test_metadata_api.py] /api/meta/meta/mults: for NHPELO_2001 target reqno html"
        url = '/opus/api/meta/mults/target.html?instrument=New+Horizons+LORRI&volumeid=NHPELO_2001&reqno=5'
        expected = b'<dl>\n<dt>2002 Ms4</dt><dd>60</dd>\n<dt>2010 Jj124</dt><dd>90</dd>\n<dt>Arawn</dt><dd>290</dd>\n<dt>Calibration</dt><dd>6</dd>\n<dt>Charon</dt><dd>490</dd>\n<dt>Chiron</dt><dd>90</dd>\n<dt>Hd 205905</dt><dd>10</dd>\n<dt>Hd 37962</dt><dd>10</dd>\n<dt>Hydra</dt><dd>143</dd>\n<dt>Ixion</dt><dd>60</dd>\n<dt>Kerberos</dt><dd>10</dd>\n<dt>Ngc 3532</dt><dd>45</dd>\n<dt>Nix</dt><dd>102</dd>\n<dt>Pluto</dt><dd>5265</dd>\n<dt>Quaoar</dt><dd>96</dd>\n<dt>Styx</dt><dd>6</dd>\n</dl>\n'
        self._run_html_equal(url, expected)

    # Bad queries
    def test__api_meta_mults_bad_param(self):
        "[test_metadata_api.py] /api/meta/mults: bad parameter"
        url = '/opus/api/meta/mults/target.json?volumeid=COISS_2111&planetx=Saturn'
        self._run_status_equal(url, 404, settings.HTTP404_SEARCH_PARAMS_INVALID)

    def test__api_meta_mults_bad_slug(self):
        "[test_metadata_api.py] /api/meta/mults: bad slug"
        url = '/opus/api/meta/mults/targetx.json?volumeid=COISS_2111&planet=Saturn'
        self._run_status_equal(url, 404, settings.HTTP404_UNKNOWN_SLUG)


            ########################################################
            ######### /api/meta/range/endpoints: API TESTS #########
            ########################################################

    # Caching (only visible through code coverage)
    def test__api_meta_range_endpoints_cache(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: cache"
        url = '/opus/__api/meta/range/endpoints/timesec1.json?volumeid=COISS_2111&reqno=1'
        expected = {"max": "2017-03-31T13:05:35.059", "nulls": 0, "min": "2017-02-17T23:59:39.059", "reqno": 1}
        self._run_json_equal(url, expected)
        url = '/opus/__api/meta/range/endpoints/timesec1.json?volumeid=COISS_2111&reqno=2'
        expected = {"max": "2017-03-31T13:05:35.059", "nulls": 0, "min": "2017-02-17T23:59:39.059", "reqno": 2}
        self._run_json_equal(url, expected)
        url = '/opus/__api/meta/range/endpoints/timesec1.json?volumeid=COISS_2111&reqno=3'
        expected = {"max": "2017-03-31T13:05:35.059", "nulls": 0, "min": "2017-02-17T23:59:39.059", "reqno": 3}
        self._run_json_equal(url, expected)
        url = '/opus/__api/meta/range/endpoints/timesec1.json?volumeid=COISS_2111&reqno=1'
        expected = {"max": "2017-03-31T13:05:35.059", "nulls": 0, "min": "2017-02-17T23:59:39.059", "reqno": 1}
        self._run_json_equal(url, expected)
        url = '/opus/__api/meta/range/endpoints/timesec1.json?volumeid=COISS_2111&reqno=2'
        expected = {"max": "2017-03-31T13:05:35.059", "nulls": 0, "min": "2017-02-17T23:59:39.059", "reqno": 2}
        self._run_json_equal(url, expected)
        url = '/opus/__api/meta/range/endpoints/timesec1.json?volumeid=COISS_2111&reqno=3'
        expected = {"max": "2017-03-31T13:05:35.059", "nulls": 0, "min": "2017-02-17T23:59:39.059", "reqno": 3}
        self._run_json_equal(url, expected)

    # General / Observation Time (string return)
    def test__api_meta_range_endpoints_times_COISS(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: times COISS"
        url = '/opus/api/meta/range/endpoints/timesec1.json?volumeid=COISS_2111'
        expected = {"max": "2017-03-31T13:05:35.059", "nulls": 0, "min": "2017-02-17T23:59:39.059"}
        self._run_json_equal(url, expected)

    def test__api_meta_range_endpoints_times_COISS_internal(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: times COISS internal"
        url = '/opus/__api/meta/range/endpoints/timesec1.json?volumeid=COISS_2111&reqno=1'
        expected = {"max": "2017-03-31T13:05:35.059", "nulls": 0, "min": "2017-02-17T23:59:39.059", "reqno": 1}
        self._run_json_equal(url, expected)

    def test__api_meta_range_endpoints_times_COUVIS(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: times COUVIS"
        url = '/opus/api/meta/range/endpoints/timesec1.json?volumeid=COUVIS_0002'
        expected = {"max": "2001-04-01T00:07:19.842", "nulls": 0, "min": "2001-01-01T02:12:02.721"}
        self._run_json_equal(url, expected)

    def test__api_meta_range_endpoints_times_COVIMS(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: times COVIMS"
        url = '/opus/api/meta/range/endpoints/timesec1.json?volumeid=COVIMS_0006'
        expected = {"max": "2005-04-01T00:06:46.867", "nulls": 0, "min": "2005-01-15T17:55:38.899"}
        self._run_json_equal(url, expected)

    def test__api_meta_range_endpoints_times_GOSSI(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: times GOSSI"
        url = '/opus/api/meta/range/endpoints/timesec1.json?volumeid=GO_0017'
        expected = {"max": "1996-12-14T17:30:37.354", "nulls": 0, "min": "1996-06-03T17:05:38.002"}
        self._run_json_equal(url, expected)

    def test__api_meta_range_endpoints_times_VGISS(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: times VGISS"
        url = '/opus/api/meta/range/endpoints/timesec1.json?volumeid=VGISS_6210'
        expected = {"max": "1981-08-15T22:17:36.000", "nulls": 0, "min": "1981-08-12T14:55:10.080"}
        self._run_json_equal(url, expected)

    def test__api_meta_range_endpoints_times_HSTI(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: times HSTI"
        url = '/opus/api/meta/range/endpoints/timesec1.json?volumeid=HSTI1_2003'
        expected = {"max": "2009-08-08T23:13:10.000", "nulls": 0, "min": "2009-07-23T18:12:25.000"}
        self._run_json_equal(url, expected)

    def test__api_meta_range_endpoints_times_HSTI_html(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: times HSTI html"
        url = '/opus/api/meta/range/endpoints/timesec1.html?volumeid=HSTI1_2003'
        expected = b'<dl>\n<dt>min</dt><dd>2009-07-23T18:12:25.000</dd>\n<dt>max</dt><dd>2009-08-08T23:13:10.000</dd>\n<dt>nulls</dt><dd>0</dd>\n</dl>\n'
        self._run_html_equal(url, expected)

    def test__api_meta_range_endpoints_times_HSTI_csv(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: times HSTI csv"
        url = '/opus/api/meta/range/endpoints/timesec1.csv?volumeid=HSTI1_2003'
        expected = b'min,max,nulls\n2009-07-23T18:12:25.000,2009-08-08T23:13:10.000,0\n'
        self._run_csv_equal(url, expected)

    # General / Observation Duration (floating point return)
    def test__api_meta_range_endpoints_observation_duration_VGISS(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: observation duration VGISS"
        url = '/opus/api/meta/range/endpoints/observationduration.json?volumeid=VGISS_6210'
        expected = {'min': '0.2400', 'max': '15.3600', 'nulls': 0}
        self._run_json_equal(url, expected)

    # General / Right Ascension (floating point return with nulls)
    def test__api_meta_range_endpoints_right_ascension_hst(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: right ascension HSTJ"
        url = '/opus/api/meta/range/endpoints/rightasc.json?volumeid=HSTJ0_9975'
        expected = {"min": None, "max": None, "nulls": 75}
        self._run_json_equal(url, expected)

    def test__api_meta_range_endpoints_right_ascension_hst_html(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: right ascension HSTJ html"
        url = '/opus/api/meta/range/endpoints/rightasc.html?volumeid=HSTJ0_9975'
        expected = b'<dl>\n<dt>min</dt><dd>None</dd>\n<dt>max</dt><dd>None</dd>\n<dt>nulls</dt><dd>75</dd>\n</dl>\n'
        self._run_html_equal(url, expected)

    def test__api_meta_range_endpoints_right_ascension_hst_csv(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: right ascension HSTJ csv"
        url = '/opus/api/meta/range/endpoints/rightasc.csv?volumeid=HSTJ0_9975'
        expected = b'min,max,nulls\n,,75\n'
        self._run_csv_equal(url, expected)

    # Image / Pixel Size (integer return)
    def test__api_meta_range_endpoints_COISS_greaterpixelsize(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: greaterpixelsize COISS"
        url = '/opus/api/meta/range/endpoints/greaterpixelsize.json?instrument=Cassini+ISS'
        expected = {'max': '1024', 'min': '256', 'nulls': 0}
        self._run_json_equal(url, expected)

    def test__api_meta_range_endpoints_COISS_lesserpixelsize(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: lesserpixelsize COISS"
        url = '/opus/api/meta/range/endpoints/lesserpixelsize.json?instrument=Cassini+ISS'
        expected = {'min': '256', 'max': '1024', 'nulls': 0}
        self._run_json_equal(url, expected)

    def test__api_meta_range_endpoints_GOSSI_greaterpixelsize(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: greaterpixelsize GOSSI"
        url = '/opus/api/meta/range/endpoints/greaterpixelsize.json?instrument=Galileo+SSI'
        expected = {'min': '800', 'max': '800', 'nulls': 0}
        self._run_json_equal(url, expected)

    def test__api_meta_range_endpoints_GOSSI_lesserpixelsize(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: lesserpixelsize GOSSI"
        url = '/opus/api/meta/range/endpoints/lesserpixelsize.json?instrument=Galileo+SSI'
        expected = {'min': '800', 'max': '800', 'nulls': 0}
        self._run_json_equal(url, expected)

    def test__api_meta_range_endpoints_GOSSI_lesserpixelsize_html(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: lesserpixelsize GOSSI html"
        url = '/opus/api/meta/range/endpoints/lesserpixelsize.html?instrument=Galileo+SSI'
        expected = b'<dl>\n<dt>min</dt><dd>800</dd>\n<dt>max</dt><dd>800</dd>\n<dt>nulls</dt><dd>0</dd>\n</dl>\n'
        self._run_html_equal(url, expected)

    def test__api_meta_range_endpoints_GOSSI_lesserpixelsize_csv(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: lesserpixelsize GOSSI csv"
        url = '/opus/api/meta/range/endpoints/lesserpixelsize.csv?instrument=Galileo+SSI'
        expected = b'min,max,nulls\n800,800,0\n'
        self._run_csv_equal(url, expected)

    # We don't do greater/lesserpixelsize for VGISS because it can change in
    # different volumes.

    # Image / Intensity Levels (integer return)
    def test__api_meta_range_endpoints_COISS_levels1(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: levels1 COISS"
        url = '/opus/api/meta/range/endpoints/levels.json?instrument=Cassini+ISS'
        expected = {'min': '4096', 'max': '4096', 'nulls': 0}
        self._run_json_equal(url, expected)

    def test__api_meta_range_endpoints_COVIMS_levels1(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: levels1 COVIMS"
        url = '/opus/api/meta/range/endpoints/levels.json?instrument=Cassini+VIMS'
        expected = {'min': '4096', 'max': '4096', 'nulls': 0}
        self._run_json_equal(url, expected)

    def test__api_meta_range_endpoints_GOSSI_levels1(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: levels1 GOSSI"
        url = '/opus/api/meta/range/endpoints/levels.json?instrument=Galileo+SSI'
        expected = {'min': '256', 'max': '256', 'nulls': 0}
        self._run_json_equal(url, expected)

    def test__api_meta_range_endpoints_VGISS_levels1(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: levels1 VGISS"
        url = '/opus/api/meta/range/endpoints/levels.json?instrument=Voyager+ISS'
        expected = {'min': '256', 'max': '256', 'nulls': 0}
        self._run_json_equal(url, expected)

    def test__api_meta_range_endpoints_VGISS_levels_constrained(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: levels1 VGISS constrained"
        url = '/opus/api/meta/range/endpoints/levels.json?instrument=Voyager+ISS&levels1=5&levels2=10'
        expected = {'min': '256', 'max': '256', 'nulls': 0}
        self._run_json_equal(url, expected)

    # reqno
    def test__api_meta_range_endpoints_GOSSI_lesserpixelsize_reqno(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: greaterpixelsize GOSSI reqno"
        url = '/opus/api/meta/range/endpoints/lesserpixelsize.json?instrument=Galileo+SSI&reqno=12345'
        expected = {'min': '800', 'max': '800', 'nulls': 0}
        self._run_json_equal(url, expected)

    def test__api_meta_range_endpoints_GOSSI_lesserpixelsize_reqno_internal(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: greaterpixelsize GOSSI reqno internal"
        url = '/opus/__api/meta/range/endpoints/lesserpixelsize.json?instrument=Galileo+SSI&reqno=12345'
        expected = {'min': '800', 'max': '800', 'nulls': 0, 'reqno': 12345}
        self._run_json_equal(url, expected)

    def test__api_meta_range_endpoints_GOSSI_lesserpixelsize_reqno_bad_internal(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: greaterpixelsize GOSSI reqno bad internal"
        url = '/opus/__api/meta/range/endpoints/lesserpixelsize.json?instrument=Galileo+SSI&reqno=NaN'
        self._run_status_equal(url, 404, settings.HTTP404_MISSING_REQNO)

    def test__api_meta_range_endpoints_GOSSI_lesserpixelsize_reqno_bad_internal_2(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: greaterpixelsize GOSSI reqno bad internal 2"
        url = '/opus/__api/meta/range/endpoints/lesserpixelsize.json?instrument=Galileo+SSI&reqno=-101010'
        self._run_status_equal(url, 404, settings.HTTP404_MISSING_REQNO)

    def test__api_meta_range_endpoints_GOSSI_lesserpixelsize_html_reqno(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: greaterpixelsize GOSSI html reqno"
        url = '/opus/api/meta/range/endpoints/lesserpixelsize.html?instrument=Galileo+SSI&reqno=1e38'
        expected = b'<dl>\n<dt>min</dt><dd>800</dd>\n<dt>max</dt><dd>800</dd>\n<dt>nulls</dt><dd>0</dd>\n</dl>\n'
        self._run_html_equal(url, expected)

    def test__api_meta_range_endpoints_GOSSI_lesserpixelsize_csv_reqno(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: greaterpixelsize GOSSI csv reqno"
        url = '/opus/api/meta/range/endpoints/lesserpixelsize.csv?instrument=Galileo+SSI&reqno=12345'
        expected = b'min,max,nulls\n800,800,0\n'
        self._run_csv_equal(url, expected)

    # Bad queries
    def test__api_meta_range_endpoints_bad_search(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: bad search"
        url = '/opus/__api/meta/range/endpoints/lesserpixelsize.json?observationduration=1x2'
        self._run_status_equal(url, 404, settings.HTTP404_SEARCH_PARAMS_INVALID)

    def test__api_meta_range_endpoints_bad_slug(self):
        "[test_metadata_api.py] /api/meta/range/endpoints: bad slug name"
        url = '/opus/__api/meta/range/endpoints/badslug.json?instrument=Cassini+ISS'
        self._run_status_equal(url, 404, settings.HTTP404_UNKNOWN_SLUG)


            ##########################################
            ######### /api/fields: API TESTS #########
            ##########################################

    # Test caching (only visible with code coverage)
    def test__api_fields_time1_cache(self):
        "[test_metadata_api.py] /api/fields: time1 json cache"
        url = '/opus/api/fields/time1.json'
        expected = {"data": {"time1": {"label": "Observation Start Time", "search_label": "Observation Time", "full_label": "Observation Start Time", "full_search_label": "Observation Time [General]", "category": "General Constraints", "slug": "time1", "old_slug": "timesec1"}}}
        self._run_json_equal(url, expected)
        url = '/opus/api/fields/time1.json'
        expected = {"data": {"time1": {"label": "Observation Start Time", "search_label": "Observation Time", "full_label": "Observation Start Time", "full_search_label": "Observation Time [General]", "category": "General Constraints", "slug": "time1", "old_slug": "timesec1"}}}
        self._run_json_equal(url, expected)
        url = '/opus/api/fields/time1.json'
        expected = {"data": {"time1": {"label": "Observation Start Time", "search_label": "Observation Time", "full_label": "Observation Start Time", "full_search_label": "Observation Time [General]", "category": "General Constraints", "slug": "time1", "old_slug": "timesec1"}}}
        self._run_json_equal(url, expected)
        url = '/opus/api/fields/time1.json'
        expected = {"data": {"time1": {"label": "Observation Start Time", "search_label": "Observation Time", "full_label": "Observation Start Time", "full_search_label": "Observation Time [General]", "category": "General Constraints", "slug": "time1", "old_slug": "timesec1"}}}
        self._run_json_equal(url, expected)
        url = '/opus/api/fields/time1.json'
        expected = {"data": {"time1": {"label": "Observation Start Time", "search_label": "Observation Time", "full_label": "Observation Start Time", "full_search_label": "Observation Time [General]", "category": "General Constraints", "slug": "time1", "old_slug": "timesec1"}}}
        self._run_json_equal(url, expected)
        url = '/opus/api/fields/time1.json'
        expected = {"data": {"time1": {"label": "Observation Start Time", "search_label": "Observation Time", "full_label": "Observation Start Time", "full_search_label": "Observation Time [General]", "category": "General Constraints", "slug": "time1", "old_slug": "timesec1"}}}
        self._run_json_equal(url, expected)

    def test__api_fields_time1_json(self):
        "[test_metadata_api.py] /api/fields: time1 json"
        url = '/opus/api/fields/time1.json'
        expected = {"data": {"time1": {"label": "Observation Start Time", "search_label": "Observation Time", "full_label": "Observation Start Time", "full_search_label": "Observation Time [General]", "category": "General Constraints", "slug": "time1", "old_slug": "timesec1"}}}
        self._run_json_equal(url, expected)

    def test__api_fields_time1_csv(self):
        "[test_metadata_api.py] /api/fields: time1 csv"
        url = '/opus/api/fields/time1.csv'
        self._run_html_equal_file(url, 'api_fields_time1_csv.csv')

    def test__api_fields_all_json(self):
        "[test_metadata_api.py] /api/fields: all json and collapse"
        url = '/opus/api/fields.json'
        print(url)
        response = self._get_response(url)
        self.assertEqual(response.status_code, 200)
        jdata = json.loads(response.content)
        num_fields = len(jdata['data'])
        url = '/opus/api/fields.json?collapse=1'
        print(url)
        response = self._get_response(url)
        self.assertEqual(response.status_code, 200)
        jdata = json.loads(response.content)
        num_fields_collapse = len(jdata['data'])
        self.assertLess(num_fields_collapse, num_fields)

    def test__api_fields_all_csv(self):
        "[test_metadata_api.py] /api/fields: all csv and collapse"
        url = '/opus/api/fields.csv'
        print(url)
        response = self._get_response(url)
        self.assertEqual(response.status_code, 200)
        num_fields = len(self._cleanup_csv(response.content).split('\\n'))
        url = '/opus/api/fields.csv?collapse=1'
        print(url)
        response = self._get_response(url)
        self.assertEqual(response.status_code, 200)
        num_fields_collapse = len(self._cleanup_csv(response.content)
                                  .split('\\n'))
        self.assertLess(num_fields_collapse, num_fields)

    def test__api_fields_all_bad_collapse(self):
        "[test_metadata_api.py] /api/fields: all json bad collapse"
        url = '/opus/api/fields.json?collapse=X'
        self._run_status_equal(url, 404)

    def test__api_fields_all_cache(self):
        "[test_metadata_api.py] /api/fields: all json cache"
        url = '/opus/api/fields.json'
        print(url)
        response = self._get_response(url)
        self.assertEqual(response.status_code, 200)
        jdata1 = json.loads(response.content)
        url = '/opus/api/fields.json'
        print(url)
        response = self._get_response(url)
        self.assertEqual(response.status_code, 200)
        jdata2 = json.loads(response.content)
        url = '/opus/api/fields.json?collapse=1'
        print(url)
        response = self._get_response(url)
        self.assertEqual(response.status_code, 200)
        jdatac1 = json.loads(response.content)
        url = '/opus/api/fields.json'
        print(url)
        response = self._get_response(url)
        self.assertEqual(response.status_code, 200)
        jdata3 = json.loads(response.content)
        url = '/opus/api/fields.json?collapse=1'
        print(url)
        response = self._get_response(url)
        self.assertEqual(response.status_code, 200)
        jdatac2 = json.loads(response.content)
        self.assertEqual(jdata1, jdata2)
        self.assertEqual(jdata2, jdata3)
        self.assertEqual(jdatac1, jdatac2)
        self.assertNotEqual(jdata1, jdatac1)
