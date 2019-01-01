# opus/application/test_api/test_search_api.py

import json
import requests
import sys
from unittest import TestCase

from django.db import connection
from django.test.client import Client
from rest_framework.test import RequestsClient

from search.views import *

import settings

import logging
log = logging.getLogger(__name__)

cursor = connection.cursor()

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_COOKIE_NAME = 'opus-test-cookie'
settings.CACHE_BACKEND = 'dummy:///'

# url(r'^__api/normalizeinput.json$', api_normalize_input),
# url(r'^__api/stringsearchchoices/(?P<slug>\w+).json$', api_string_search_choices),

class ApiSearchTests(TestCase):
    GO_LIVE = False
    LIVE_TARGET = "production"

    # disable error logging and trace output before test
    def setUp(self):
        self.search_count_threshold = settings.STRINGCHOICE_FULL_SEARCH_COUNT_THRESHOLD
        self.search_time_threshold = settings.STRINGCHOICE_FULL_SEARCH_TIME_THRESHOLD
        self.search_time_threshold2 = settings.STRINGCHOICE_FULL_SEARCH_TIME_THRESHOLD2
        self.search_count_threshold = 1000000000
        self.search_time_threshold = 1000000
        self.search_time_threshold2 = 1000000
        logging.disable(logging.ERROR)

    # enable error logging and trace output after test
    def tearDown(self):
        settings.STRINGCHOICE_FULL_SEARCH_COUNT_THRESHOLD = self.search_count_threshold
        settings.STRINGCHOICE_FULL_SEARCH_TIME_THRESHOLD = self.search_time_threshold
        settings.STRINGCHOICE_FULL_SEARCH_TIME_THRESHOLD2 = self.search_time_threshold2
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
        if 'versions' in jdata:
            del jdata['versions']
        if 'versions' in expected:
            del expected['versions']
        print('Got:')
        print(str(jdata))
        print('Expected:')
        print(str(expected))
        self.assertEqual(expected, jdata)

    def _run_stringsearchchoices_subset(self, url, expected):
        # Ignore any returned choices that aren't in the expected set
        # to handle databases that have more stuff in them than we're expecting
        print(url)
        response = self._get_response(url)
        self.assertEqual(response.status_code, 200)
        jdata = json.loads(response.content)
        if 'versions' in jdata:
            del jdata['versions']
        if 'versions' in expected:
            del expected['versions']
        new_choices = []
        for choice in jdata['choices']:
            if choice in expected['choices']:
                new_choices.append(choice)
        print('Got:')
        print(str(jdata))
        print('Expected:')
        print(str(expected))
        print('Restricted Got:')
        print(new_choices)
        jdata['choices'] = new_choices
        self.assertEqual(expected, jdata)

            ###################################################
            ######### /__api/normalizeinput API TESTS #########
            ###################################################

    def test__api_normalizeinput_empty(self):
        "/api/normalizeinput: empty"
        url = '/opus/__api/normalizeinput.json'
        expected = {}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_bad_slug(self):
        "/api/normalizeinput: bad slug"
        url = '/opus/__api/normalizeinput.json?fredethel=1234'
        self._run_status_equal(url, 404)

    def test__api_normalizeinput_int_empty(self):
        "/api/normalizeinput: integer empty"
        url = '/opus/__api/normalizeinput.json?levels='
        expected = {"levels": ""}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_int_zero(self):
        "/api/normalizeinput: integer zero"
        url = '/opus/__api/normalizeinput.json?levels=0'
        expected = {"levels": "0"}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_int_neg(self):
        "/api/normalizeinput: integer negative"
        url = '/opus/__api/normalizeinput.json?levels=-1234567890'
        expected = {"levels": "-1234567890"}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_int_pos(self):
        "/api/normalizeinput: integer positive"
        url = '/opus/__api/normalizeinput.json?levels=1234567890'
        expected = {"levels": "1234567890"}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_int_spaces(self):
        "/api/normalizeinput: integer spaces"
        url = '/opus/__api/normalizeinput.json?levels=+1234+'
        expected = {"levels": "1234"}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_int_underscores(self):
        "/api/normalizeinput: integer underscores"
        url = '/opus/__api/normalizeinput.json?levels=_12_34_'
        expected = {"levels": "1234"}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_int_commas(self):
        "/api/normalizeinput: integer commas"
        url = '/opus/__api/normalizeinput.json?levels=,1,2,3,4,'
        expected = {"levels": "1234"}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_int_mixed_delim(self):
        "/api/normalizeinput: integer mixed delimiters"
        url = '/opus/__api/normalizeinput.json?levels=+,1_23_,4+'
        expected = {"levels": "1234"}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_int_bad_val1(self):
        "/api/normalizeinput: integer bad value 1X1"
        url = '/opus/__api/normalizeinput.json?levels=1X1'
        expected = {"levels": None}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_int_bad_val2(self):
        "/api/normalizeinput: integer bad value 1.2"
        url = '/opus/__api/normalizeinput.json?levels=1.2'
        expected = {"levels": None}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_int_large_val(self):
        "/api/normalizeinput: integer large value 1e1234"
        url = '/opus/__api/normalizeinput.json?levels=1e1234'
        expected = {"levels": None}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_int_inf(self):
        "/api/normalizeinput: integer inf"
        url = '/opus/__api/normalizeinput.json?levels=inf'
        expected = {"levels": None}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_int_ninf(self):
        "/api/normalizeinput: integer -inf"
        url = '/opus/__api/normalizeinput.json?levels=-inf'
        expected = {"levels": None}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_int_nan(self):
        "/api/normalizeinput: integer nan"
        url = '/opus/__api/normalizeinput.json?levels=nan'
        expected = {"levels": None}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_float_empty(self):
        "/api/normalizeinput: float empty"
        url = '/opus/__api/normalizeinput.json?rightasc1='
        expected = {"rightasc1": ""}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_float_zero(self):
        "/api/normalizeinput: float zero"
        url = '/opus/__api/normalizeinput.json?rightasc1=0'
        expected = {"rightasc1": "0.000000"}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_float_neg(self):
        "/api/normalizeinput: float negative"
        url = '/opus/__api/normalizeinput.json?rightasc1=-123456'
        expected = {"rightasc1": "-123456.000000"}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_float_pos(self):
        "/api/normalizeinput: float positive"
        url = '/opus/__api/normalizeinput.json?rightasc1=567890'
        expected = {"rightasc1": "567890.000000"}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_float_spaces(self):
        "/api/normalizeinput: float spaces"
        url = '/opus/__api/normalizeinput.json?rightasc1=+1234+'
        expected = {"rightasc1": "1234.000000"}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_float_underscores(self):
        "/api/normalizeinput: float underscores"
        url = '/opus/__api/normalizeinput.json?rightasc1=_12_34_'
        expected = {"rightasc1": "1234.000000"}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_float_commas(self):
        "/api/normalizeinput: float commas"
        url = '/opus/__api/normalizeinput.json?rightasc1=,1,2,3,4,'
        expected = {"rightasc1": "1234.000000"}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_float_mixed_delim(self):
        "/api/normalizeinput: float mixed delimiters"
        url = '/opus/__api/normalizeinput.json?rightasc1=+,1_23_,4+'
        expected = {"rightasc1": "1234.000000"}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_float_exponent1(self):
        "/api/normalizeinput: float mixed delimiters"
        url = '/opus/__api/normalizeinput.json?rightasc1=1.123e12'
        expected = {"rightasc1": "1.123000e+12"}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_float_exponent2(self):
        "/api/normalizeinput: float mixed delimiters"
        url = '/opus/__api/normalizeinput.json?rightasc1=1123000000000'
        expected = {"rightasc1": "1.123000e+12"}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_float_bad_val1(self):
        "/api/normalizeinput: float bad value 1X1"
        url = '/opus/__api/normalizeinput.json?rightasc1=1X1'
        expected = {"rightasc1": None}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_float_bad_val2(self):
        "/api/normalizeinput: float bad value 1.22h+1"
        url = '/opus/__api/normalizeinput.json?rightasc1=1.22h+1'
        expected = {"rightasc1": None}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_float_large_val(self):
        "/api/normalizeinput: float large value 1e1234"
        url = '/opus/__api/normalizeinput.json?rightasc1=1e1234'
        expected = {"rightasc1": None}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_float_inf(self):
        "/api/normalizeinput: float inf"
        url = '/opus/__api/normalizeinput.json?rightasc1=inf'
        expected = {"rightasc1": None}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_int_ninf(self):
        "/api/normalizeinput: float -inf"
        url = '/opus/__api/normalizeinput.json?rightasc1=-inf'
        expected = {"rightasc1": None}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_float_nan(self):
        "/api/normalizeinput: float nan"
        url = '/opus/__api/normalizeinput.json?rightasc1=nan'
        expected = {"rightasc1": None}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_time1(self):
        "/api/normalizeinput: time 2012-01-04T01:02:03.123"
        url = '/opus/__api/normalizeinput.json?timesec1=2012-01-04T01:02:03.123'
        expected = {"timesec1": "2012-01-04T01:02:03.123"}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_time2(self):
        "/api/normalizeinput: time 2012-01-04T01:02:03"
        url = '/opus/__api/normalizeinput.json?timesec1=2012-01-04T01:02:03'
        expected = {"timesec1": "2012-01-04T01:02:03.000"}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_time3(self):
        "/api/normalizeinput: time 2012-01-04"
        url = '/opus/__api/normalizeinput.json?timesec1=2012-01-04'
        expected = {"timesec1": "2012-01-04T00:00:00.000"}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_time4(self):
        "/api/normalizeinput: time July 4 2001"
        url = '/opus/__api/normalizeinput.json?timesec1=July+4+2001'
        expected = {"timesec1": "2001-07-04T00:00:00.000"}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_time5(self):
        "/api/normalizeinput: time July 4 2001 6:05"
        url = '/opus/__api/normalizeinput.json?timesec1=July+4+2001+6:05'
        expected = {"timesec1": "2001-07-04T06:05:00.000"}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_cassini_orbit_int1(self):
        "/api/normalizeinput: cassini revnoint A"
        url = '/opus/__api/normalizeinput.json?CASSINIrevnoint2=A'
        expected = {"CASSINIrevnoint2": "00A"}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_cassini_orbit_int2(self):
        "/api/normalizeinput: cassini revnoint 00A"
        url = '/opus/__api/normalizeinput.json?CASSINIrevnoint1=00A'
        expected = {"CASSINIrevnoint1": "00A"}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_cassini_orbit_int3(self):
        "/api/normalizeinput: cassini revnoint 004"
        url = '/opus/__api/normalizeinput.json?CASSINIrevnoint2=004'
        expected = {"CASSINIrevnoint2": "004"}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_cassini_orbit_int_bad(self):
        "/api/normalizeinput: cassini revnoint bad value 00D"
        url = '/opus/__api/normalizeinput.json?CASSINIrevnoint1=00D'
        expected = {"CASSINIrevnoint1": None}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_cassini_sclk1(self):
        "/api/normalizeinput: cassini sclk1 1/1294561143"
        url = '/opus/__api/normalizeinput.json?CASSINIspacecraftclockcount1=1/1294561143'
        expected = {"CASSINIspacecraftclockcount1": "1294561143.000"}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_cassini_sclk1_bad(self):
        "/api/normalizeinput: cassini sclk1 bad value 2/1294561143"
        url = '/opus/__api/normalizeinput.json?CASSINIspacecraftclockcount1=2/1294561143'
        expected = {"CASSINIspacecraftclockcount1": None}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_cassini_sclk2(self):
        "/api/normalizeinput: cassini sclk2 1/1294561143"
        url = '/opus/__api/normalizeinput.json?CASSINIspacecraftclockcount2=1/1294561143'
        expected = {"CASSINIspacecraftclockcount2": "1294561143.000"}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_cassini_sclk2_bad(self):
        "/api/normalizeinput: cassini sclk2 bad value 2/1294561143"
        url = '/opus/__api/normalizeinput.json?CASSINIspacecraftclockcount2=2/1294561143'
        expected = {"CASSINIspacecraftclockcount2": None}
        self._run_json_equal(url, expected)


            ########################################################
            ######### /__api/stringsearchchoices API TESTS #########
            ########################################################

    def test__api_stringsearchchoices_bad_slug(self):
        "/api/stringsearchchoices: bad slug"
        url = '/opus/__api/stringsearchchoices/fredethel.json'
        self._run_status_equal(url, 404)

    def test__api_stringsearchchoices_bad_limit(self):
        "/api/stringsearchchoices: bad limit"
        url = '/opus/__api/stringsearchchoices/volumeid.json&limit=0A'
        self._run_status_equal(url, 404)

    def test__api_stringsearchchoices_bad_limit_val_n1(self):
        "/api/stringsearchchoices: bad limit -1"
        url = '/opus/__api/stringsearchchoices/volumeid.json&limit=-1'
        self._run_status_equal(url, 404)

    def test__api_stringsearchchoices_bad_limit_val_0(self):
        "/api/stringsearchchoices: bad limit 0"
        url = '/opus/__api/stringsearchchoices/volumeid.json&limit=0'
        self._run_status_equal(url, 404)

    def test__api_stringsearchchoices_bad_limit_val_1000000000001(self):
        "/api/stringsearchchoices: bad limit 1000000000001"
        url = '/opus/__api/stringsearchchoices/volumeid.json&limit=1000000000001'
        self._run_status_equal(url, 404)

    def test__api_stringsearchchoices_bad_search(self):
        "/api/stringsearchchoices: bad search"
        url = '/opus/__api/stringsearchchoices/volumeid.json?fredethel=2'
        self._run_status_equal(url, 404)

    def test__api_stringsearchchoices_bad_search2(self):
        "/api/stringsearchchoices: bad search2"
        url = '/opus/__api/stringsearchchoices/volumeid.json?missionid=A'
        self._run_status_equal(url, 404)

    def test__api_stringsearchchoices_volumeid_none(self):
        "/api/stringsearchchoices: volumeid none"
        url = '/opus/__api/stringsearchchoices/volumeid.json?volumeid=BAD_VOLUME'
        expected = {'choices': [],
                    'full_search': False}
        self._run_json_equal(url, expected)

    def test__api_stringsearchchoices_volumeid_GO_0017(self):
        "/api/stringsearchchoices: volumeid GO_0017"
        url = '/opus/__api/stringsearchchoices/volumeid.json?volumeid=GO_0017'
        expected = {'choices': ['<b>GO_0017</b>'],
                    'full_search': False}
        self._run_json_equal(url, expected)

    def test__api_stringsearchchoices_volumeid_O_0017(self):
        "/api/stringsearchchoices: volumeid O_0017"
        url = '/opus/__api/stringsearchchoices/volumeid.json?volumeid=O_0017'
        expected = {'choices': ['G<b>O_0017</b>'],
                    'full_search': False}
        self._run_json_equal(url, expected)

    def test__api_stringsearchchoices_volumeid_O_0017(self):
        "/api/stringsearchchoices: volumeid O_0017"
        url = '/opus/__api/stringsearchchoices/volumeid.json?volumeid=O_0017'
        expected = {'choices': ['G<b>O_0017</b>'],
                    'full_search': False}
        self._run_json_equal(url, expected)

    def test__api_stringsearchchoices_volumeid_COISS_2002(self):
        "/api/stringsearchchoices: volumeid COISS_2002"
        url = '/opus/__api/stringsearchchoices/volumeid.json?volumeid=COISS_2002'
        expected = {'choices': ['<b>COISS_2002</b>'],
                    'full_search': False}
        self._run_json_equal(url, expected)

    def test__api_stringsearchchoices_datasetid_empty_COISS_2002(self):
        "/api/stringsearchchoices: datasetid empty volumeid COISS_2002"
        url = '/opus/__api/stringsearchchoices/datasetid.json?volumeid=COISS_2002&datasetid='
        expected = {'choices': ['CO-S-ISSNA/ISSWA-2-EDR-V1.0'],
                    'full_search': False}
        self._run_json_equal(url, expected)

    def test__api_stringsearchchoices_datasetid_empty2_COISS_2002(self):
        "/api/stringsearchchoices: datasetid empty2 volumeid COISS_2002"
        url = '/opus/__api/stringsearchchoices/datasetid.json?volumeid=COISS_2002'
        expected = {'choices': ['CO-S-ISSNA/ISSWA-2-EDR-V1.0'],
                    'full_search': False}
        self._run_json_equal(url, expected)

    def test__api_stringsearchchoices_datasetid_begin_COISS_2002(self):
        "/api/stringsearchchoices: datasetid CO-S volumeid COISS_2002"
        url = '/opus/__api/stringsearchchoices/datasetid.json?volumeid=COISS_2002&datasetid=CO-S'
        expected = {'choices': ['<b>CO-S</b>-ISSNA/ISSWA-2-EDR-V1.0'],
                    'full_search': False}
        self._run_json_equal(url, expected)

    def test__api_stringsearchchoices_datasetid_middle_COISS_2002(self):
        "/api/stringsearchchoices: datasetid ISSWA volumeid COISS_2002"
        url = '/opus/__api/stringsearchchoices/datasetid.json?volumeid=COISS_2002&datasetid=ISSWA'
        expected = {'choices': ['CO-S-ISSNA/<b>ISSWA</b>-2-EDR-V1.0'],
                    'full_search': False}
        self._run_json_equal(url, expected)

    def test__api_stringsearchchoices_datasetid_end_COISS_2002(self):
        "/api/stringsearchchoices: datasetid V1.0 volumeid COISS_2002"
        url = '/opus/__api/stringsearchchoices/datasetid.json?volumeid=COISS_2002&datasetid=V1.0'
        expected = {'choices': ['CO-S-ISSNA/ISSWA-2-EDR-<b>V1.0</b>'],
                    'full_search': False}
        self._run_json_equal(url, expected)

    def test__api_stringsearchchoices_productid_14609_COISS_2002(self):
        "/api/stringsearchchoices: productid 14609 volumeid COISS_2002"
        url = '/opus/__api/stringsearchchoices/productid.json?volumeid=COISS_2002&productid=14609'
        expected = {'choices': ['1_N<b>14609</b>60653.122', '1_N<b>14609</b>60868.118', '1_N<b>14609</b>60908.120', '1_N<b>14609</b>60944.118', '1_N<b>14609</b>60992.120', '1_N<b>14609</b>61026.118', '1_N<b>14609</b>61061.118', '1_N<b>14609</b>61193.118', '1_N<b>14609</b>62279.118', '1_N<b>14609</b>62327.120', '1_N<b>14609</b>62415.121', '1_N<b>14609</b>64003.118', '1_N<b>14609</b>64043.120', '1_N<b>14609</b>65631.118', '1_N<b>14609</b>65679.120', '1_N<b>14609</b>65767.121', '1_N<b>14609</b>66953.122', '1_N<b>14609</b>67168.118', '1_N<b>14609</b>67208.120', '1_N<b>14609</b>67244.118', '1_N<b>14609</b>67292.120', '1_N<b>14609</b>67326.118', '1_N<b>14609</b>67361.118', '1_N<b>14609</b>67493.118', '1_N<b>14609</b>69019.122', '1_N<b>14609</b>69979.122', '1_N<b>14609</b>70939.122', '1_N<b>14609</b>71899.122', '1_N<b>14609</b>73253.122', '1_N<b>14609</b>73468.118', '1_N<b>14609</b>73508.120', '1_N<b>14609</b>73544.118', '1_N<b>14609</b>73592.120', '1_N<b>14609</b>73626.118', '1_N<b>14609</b>73661.118', '1_N<b>14609</b>73793.118', '1_N<b>14609</b>74303.122', '1_N<b>14609</b>74933.122', '1_N<b>14609</b>75548.122', '1_N<b>14609</b>79553.122', '1_N<b>14609</b>79768.118', '1_N<b>14609</b>79808.120', '1_N<b>14609</b>79844.118', '1_N<b>14609</b>79892.120', '1_N<b>14609</b>79926.118', '1_N<b>14609</b>79961.118', '1_N<b>14609</b>80093.118', '1_N<b>14609</b>80638.122', '1_N<b>14609</b>80902.123', '1_N<b>14609</b>80958.125', '1_N<b>14609</b>81222.126', '1_N<b>14609</b>81262.127', '1_N<b>14609</b>81366.128', '1_N<b>14609</b>81733.118', '1_N<b>14609</b>81997.120', '1_N<b>14609</b>82134.118', '1_N<b>14609</b>82398.120', '1_N<b>14609</b>82871.118', '1_N<b>14609</b>83007.120', '1_N<b>14609</b>83208.118', '1_N<b>14609</b>83728.120', '1_N<b>14609</b>84033.118', '1_N<b>14609</b>84297.120', '1_N<b>14609</b>84498.118', '1_N<b>14609</b>84762.120', '1_N<b>14609</b>84899.118', '1_N<b>14609</b>85164.118', '1_N<b>14609</b>85853.122', '1_N<b>14609</b>86068.118', '1_N<b>14609</b>86108.120', '1_N<b>14609</b>86144.118', '1_N<b>14609</b>86192.120', '1_N<b>14609</b>86226.118', '1_N<b>14609</b>86261.118', '1_N<b>14609</b>86393.118', '1_N<b>14609</b>88537.122'],
                    'full_search': False}
        self._run_json_equal(url, expected)

    def test__api_stringsearchchoices_productid_14609_COISS_2002_limit3(self):
        "/api/stringsearchchoices: productid 14609 volumeid COISS_2002 limit 3"
        url = '/opus/__api/stringsearchchoices/productid.json?volumeid=COISS_2002&productid=14609&limit=3'
        expected = {'choices': ['1_N<b>14609</b>60653.122', '1_N<b>14609</b>60868.118', '1_N<b>14609</b>60908.120'],
                    'full_search': False}
        self._run_json_equal(url, expected)

    def test__api_stringsearchchoices_volumeid_002_COISS(self):
        "/api/stringsearchchoices: volumeid 002 instrumentid COISS"
        # The time constraint eliminates COISS_1002 as a result
        url = '/opus/__api/stringsearchchoices/volumeid.json?volumeid=002&instrument=Cassini+ISS&timesec1=2004-02-06T02:07:06.418'
        expected = {'choices': ['COISS_2<b>002</b>'],
                    'full_search': False}
        self._run_json_equal(url, expected)

    def test__api_stringsearchchoices_volumeid_002_COUVIS(self):
        "/api/stringsearchchoices: volumeid 002 instrumentid COUVIS"
        # The time constraint eliminates COUVIS_002x as results
        url = '/opus/__api/stringsearchchoices/volumeid.json?volumeid=002&instrument=Cassini+UVIS&timesec2=2007-04-05T03:56:00.537'
        expected = {'choices': ['COUVIS_0<b>002</b>'],
                    'full_search': False}
        self._run_json_equal(url, expected)

    def test__api_stringsearchchoices_volumeid_002_COISS_bigcache(self):
        "/api/stringsearchchoices: volumeid 002 instrumentid COISS bigcache"
        settings.STRINGCHOICE_FULL_SEARCH_COUNT_THRESHOLD = 1
        url = '/opus/__api/stringsearchchoices/volumeid.json?volumeid=002&instrument=Cassini+ISS'
        expected = {'choices': ['COISS_2<b>002</b>', 'COUVIS_0<b>002</b>'],
                    'full_search': True}
        self._run_stringsearchchoices_subset(url, expected)

    def test__api_stringsearchchoices_volumeid_002_COUVIS_bigcache(self):
        "/api/stringsearchchoices: volumeid 002 instrumentid COUVIS bigcache"
        settings.STRINGCHOICE_FULL_SEARCH_COUNT_THRESHOLD = 1
        # The time constraints eliminate COISS_1002 and COUVIS_002x as results
        url = '/opus/__api/stringsearchchoices/volumeid.json?volumeid=002&instrument=Cassini+UVIS'
        expected = {'choices': ['COISS_2<b>002</b>', 'COUVIS_0<b>002</b>'],
                    'full_search': True}
        self._run_stringsearchchoices_subset(url, expected)

    def test__api_stringsearchchoices_volumeid_002_COISS_timeout(self):
        "/api/stringsearchchoices: volumeid 002 instrumentid COISS timeout"
        settings.STRINGCHOICE_FULL_SEARCH_TIME_THRESHOLD = 1
        url = '/opus/__api/stringsearchchoices/volumeid.json?volumeid=002&instrument=Cassini+ISS'
        expected = {'choices': ['COISS_2<b>002</b>', 'COUVIS_0<b>002</b>'],
                    'full_search': True}
        self._run_stringsearchchoices_subset(url, expected)

    def test__api_stringsearchchoices_volumeid_002_COUVIS_timeout(self):
        "/api/stringsearchchoices: volumeid 002 instrumentid COUVIS timeout"
        settings.STRINGCHOICE_FULL_SEARCH_TIME_THRESHOLD = 1
        url = '/opus/__api/stringsearchchoices/volumeid.json?volumeid=002&instrument=Cassini+UVIS'
        expected = {'choices': ['COISS_2<b>002</b>', 'COUVIS_0<b>002</b>'],
                    'full_search': True}
        self._run_stringsearchchoices_subset(url, expected)
