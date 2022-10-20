# opus/application/test_api/test_search_api.py

import json
import logging
import requests
from unittest import TestCase

from django.core.cache import cache
from rest_framework.test import RequestsClient

from tools.app_utils import (HTTP404_BAD_LIMIT,
                               HTTP404_BAD_OR_MISSING_REQNO,
                               HTTP404_SEARCH_PARAMS_INVALID,
                               HTTP404_UNKNOWN_CATEGORY,
                               HTTP404_UNKNOWN_OPUS_ID,
                               HTTP404_UNKNOWN_RING_OBS_ID,
                               HTTP404_UNKNOWN_SLUG)

from .api_test_helper import ApiTestHelper

import settings

class ApiSearchTests(TestCase, ApiTestHelper):

    def setUp(self):
        self.maxDiff = None
        settings.OPUS_FAKE_API_DELAYS = 0
        settings.OPUS_FAKE_SERVER_ERROR404_PROBABILITY = 0
        settings.OPUS_FAKE_SERVER_ERROR500_PROBABILITY = 0
        settings.CACHE_KEY_PREFIX = 'opustest:' + settings.DB_SCHEMA_NAME
        logging.disable(logging.ERROR)
        self.search_count_threshold = settings.STRINGCHOICE_FULL_SEARCH_COUNT_THRESHOLD
        self.search_time_threshold  = settings.STRINGCHOICE_FULL_SEARCH_TIME_THRESHOLD
        self.search_time_threshold2 = settings.STRINGCHOICE_FULL_SEARCH_TIME_THRESHOLD2
        settings.STRINGCHOICE_FULL_SEARCH_COUNT_THRESHOLD = 1000000000
        settings.STRINGCHOICE_FULL_SEARCH_TIME_THRESHOLD  = 1000000
        settings.STRINGCHOICE_FULL_SEARCH_TIME_THRESHOLD2 = 1000000
        if settings.TEST_GO_LIVE: # pragma: no cover - remote server
            self.client = requests.Session()
        else:
            self.client = RequestsClient()
        cache.clear()

    def tearDown(self):
        logging.disable(logging.NOTSET)
        settings.STRINGCHOICE_FULL_SEARCH_COUNT_THRESHOLD = self.search_count_threshold
        settings.STRINGCHOICE_FULL_SEARCH_TIME_THRESHOLD  = self.search_time_threshold
        settings.STRINGCHOICE_FULL_SEARCH_TIME_THRESHOLD2 = self.search_time_threshold2

    def _run_stringsearchchoices_subset(self, url, expected):
        # Ignore any returned choices that aren't in the expected set
        # to handle databases that have more stuff in them than we're expecting
        print(url)
        response = self._get_response(url)
        self.assertEqual(response.status_code, 200)
        jdata = json.loads(response.content)
        if 'full_search' not in expected:
            if 'full_search' in jdata: # pragma: no cover - for future test cases
                del jdata['full_search']
        new_choices = []
        for choice in jdata['choices']:
            if choice in expected['choices']: # pragma: no cover - for future test cases
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
        "[test_search_api.py] /api/normalizeinput: empty no reqno"
        url = '/__api/normalizeinput.json'
        self._run_status_equal(url, 404,
                    HTTP404_BAD_OR_MISSING_REQNO('/__api/normalizeinput.json'))

    def test__api_normalizeinput_empty_reqno(self):
        "[test_search_api.py] /api/normalizeinput: empty"
        url = '/__api/normalizeinput.json?reqno=1'
        expected = {"reqno": 1}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_empty_reqno_bad(self):
        "[test_search_api.py] /api/normalizeinput: empty reqno bad"
        url = '/__api/normalizeinput.json?reqno=X'
        self._run_status_equal(url, 404,
                    HTTP404_BAD_OR_MISSING_REQNO('/__api/normalizeinput.json'))

    def test__api_normalizeinput_bad_slug(self):
        "[test_search_api.py] /api/normalizeinput: bad slug"
        url = '/__api/normalizeinput.json?fredethel=1234&reqno=123'
        self._run_status_equal(url, 404,
                    HTTP404_SEARCH_PARAMS_INVALID('/__api/normalizeinput.json'))

    def test__api_normalizeinput_string_empty(self):
        "[test_search_api.py] /api/normalizeinput: string empty"
        url = '/__api/normalizeinput.json?note=&reqno=123'
        expected = {"note": "", "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_string(self):
        "[test_search_api.py] /api/normalizeinput: string"
        url = '/__api/normalizeinput.json?note=FRED&reqno=123'
        expected = {"note": "FRED", "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_string_regex_good(self):
        "[test_search_api.py] /api/normalizeinput: string regex good"
        url = r'/opus/__api/normalizeinput.json?note=^\d$&reqno=123'
        expected = {"note": r"^\d$", "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_string_regex_bad(self):
        "[test_search_api.py] /api/normalizeinput: string regex bad"
        url = r'/opus/__api/normalizeinput.json?note=^\d($&qtype-note=regex&reqno=123'
        expected = {"note": None, "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_int_empty(self):
        "[test_search_api.py] /api/normalizeinput: integer empty"
        url = '/__api/normalizeinput.json?levels1=&reqno=123'
        expected = {"levels1": "", "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_int_zero(self):
        "[test_search_api.py] /api/normalizeinput: integer zero"
        url = '/__api/normalizeinput.json?levels1=0&reqno=123'
        expected = {"levels1": "0", "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_int_neg(self):
        "[test_search_api.py] /api/normalizeinput: integer negative"
        url = '/__api/normalizeinput.json?levels1=-1234567890&reqno=123'
        expected = {"levels1": "-1234567890", "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_int_pos(self):
        "[test_search_api.py] /api/normalizeinput: integer positive"
        url = '/__api/normalizeinput.json?levels1=1234567890&reqno=123'
        expected = {"levels1": "1234567890", "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_int_spaces(self):
        "[test_search_api.py] /api/normalizeinput: integer spaces"
        url = '/__api/normalizeinput.json?levels1=+1234+&reqno=123'
        expected = {"levels1": "1234", "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_int_underscores(self):
        "[test_search_api.py] /api/normalizeinput: integer underscores"
        url = '/__api/normalizeinput.json?levels1=_12_34_&reqno=123'
        expected = {"levels1": "1234", "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_int_commas(self):
        "[test_search_api.py] /api/normalizeinput: integer commas"
        url = '/__api/normalizeinput.json?levels1=,1,2,3,4,&reqno=123'
        expected = {"levels1": "1234", "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_int_mixed_delim(self):
        "[test_search_api.py] /api/normalizeinput: integer mixed delimiters"
        url = '/__api/normalizeinput.json?levels1=+,1_23_,4+&reqno=123'
        expected = {"levels1": "1234", "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_int_bad_val1(self):
        "[test_search_api.py] /api/normalizeinput: integer bad value 1X1"
        url = '/__api/normalizeinput.json?levels1=1X1&reqno=123'
        expected = {"levels1": None, "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_int_bad_val2(self):
        "[test_search_api.py] /api/normalizeinput: integer bad value 1.2"
        url = '/__api/normalizeinput.json?levels1=1.2&reqno=123'
        expected = {"levels1": None, "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_int_large_val(self):
        "[test_search_api.py] /api/normalizeinput: integer large value 1e1234"
        url = '/__api/normalizeinput.json?levels1=1e1234&reqno=123'
        expected = {"levels1": None, "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_int_inf(self):
        "[test_search_api.py] /api/normalizeinput: integer inf"
        url = '/__api/normalizeinput.json?levels1=inf&reqno=123'
        expected = {"levels1": None, "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_int_ninf(self):
        "[test_search_api.py] /api/normalizeinput: integer -inf"
        url = '/__api/normalizeinput.json?levels1=-inf&reqno=123'
        expected = {"levels1": None, "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_int_nan(self):
        "[test_search_api.py] /api/normalizeinput: integer nan"
        url = '/__api/normalizeinput.json?levels1=nan&reqno=123'
        expected = {"levels1": None, "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_float_empty(self):
        "[test_search_api.py] /api/normalizeinput: float empty"
        url = '/__api/normalizeinput.json?rightasc1=&reqno=123'
        expected = {"rightasc1": "", "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_float_zero(self):
        "[test_search_api.py] /api/normalizeinput: float zero"
        url = '/__api/normalizeinput.json?rightasc1=0&reqno=123'
        expected = {"rightasc1": "0", "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_float_neg(self):
        "[test_search_api.py] /api/normalizeinput: float negative"
        url = '/__api/normalizeinput.json?rightasc1=-123456&reqno=123'
        expected = {"rightasc1": "-123456", "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_float_pos(self):
        "[test_search_api.py] /api/normalizeinput: float positive"
        url = '/__api/normalizeinput.json?rightasc1=567890&reqno=123'
        expected = {"rightasc1": "567890", "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_float_spaces(self):
        "[test_search_api.py] /api/normalizeinput: float spaces"
        url = '/__api/normalizeinput.json?rightasc1=+1234+&reqno=123'
        expected = {"rightasc1": "1234", "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_float_underscores(self):
        "[test_search_api.py] /api/normalizeinput: float underscores"
        url = '/__api/normalizeinput.json?rightasc1=_12_34_&reqno=123'
        expected = {"rightasc1": "1234", "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_float_commas(self):
        "[test_search_api.py] /api/normalizeinput: float commas"
        url = '/__api/normalizeinput.json?rightasc1=,1,2,3,4,&reqno=123'
        expected = {"rightasc1": "1234", "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_float_mixed_delim(self):
        "[test_search_api.py] /api/normalizeinput: float mixed delimiters"
        url = '/__api/normalizeinput.json?rightasc1=+,1_23_,4+&reqno=123'
        expected = {"rightasc1": "1234", "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_float_exponent1(self):
        "[test_search_api.py] /api/normalizeinput: float mixed delimiters"
        url = '/__api/normalizeinput.json?rightasc1=1.123e12&reqno=123'
        expected = {"rightasc1": "1.123e+12", "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_float_exponent2(self):
        "[test_search_api.py] /api/normalizeinput: float mixed delimiters"
        url = '/__api/normalizeinput.json?rightasc1=1123000000000&reqno=123'
        expected = {"rightasc1": "1.123e+12", "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_float_bad_val1(self):
        "[test_search_api.py] /api/normalizeinput: float bad value 1X1"
        url = '/__api/normalizeinput.json?rightasc1=1X1&reqno=123'
        expected = {"rightasc1": None, "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_float_bad_val2(self):
        "[test_search_api.py] /api/normalizeinput: float bad value 1.22h+1"
        url = '/__api/normalizeinput.json?rightasc1=1.22h+1&reqno=123'
        expected = {"rightasc1": None, "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_float_large_val(self):
        "[test_search_api.py] /api/normalizeinput: float large value 1e1234"
        url = '/__api/normalizeinput.json?rightasc1=1e1234&reqno=123'
        expected = {"rightasc1": None, "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_float_inf(self):
        "[test_search_api.py] /api/normalizeinput: float inf"
        url = '/__api/normalizeinput.json?rightasc1=inf&reqno=123'
        expected = {"rightasc1": None, "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_float_ninf(self):
        "[test_search_api.py] /api/normalizeinput: float -inf"
        url = '/__api/normalizeinput.json?rightasc1=-inf&reqno=123'
        expected = {"rightasc1": None, "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_float_nan(self):
        "[test_search_api.py] /api/normalizeinput: float nan"
        url = '/__api/normalizeinput.json?rightasc1=nan&reqno=123'
        expected = {"rightasc1": None, "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_time1(self):
        "[test_search_api.py] /api/normalizeinput: time 2012-01-04T01:02:03.123"
        url = '/__api/normalizeinput.json?time1=2012-01-04T01:02:03.123&reqno=123'
        expected = {"time1": "2012-01-04T01:02:03.123", "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_time2(self):
        "[test_search_api.py] /api/normalizeinput: time 2012-01-04T01:02:03"
        url = '/__api/normalizeinput.json?time1=2012-01-04T01:02:03&reqno=123'
        expected = {"time1": "2012-01-04T01:02:03.000", "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_time3(self):
        "[test_search_api.py] /api/normalizeinput: time 2012-01-04"
        url = '/__api/normalizeinput.json?time1=2012-01-04&reqno=123'
        expected = {"time1": "2012-01-04T00:00:00.000", "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_time4(self):
        "[test_search_api.py] /api/normalizeinput: time July 4 2001"
        url = '/__api/normalizeinput.json?time1=July+4+2001&reqno=123'
        expected = {"time1": "2001-07-04T00:00:00.000", "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_time5(self):
        "[test_search_api.py] /api/normalizeinput: time July 4 2001 6:05"
        url = '/__api/normalizeinput.json?time1=July+4+2001+6:05&reqno=123'
        expected = {"time1": "2001-07-04T06:05:00.000", "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_cassini_orbit_int1(self):
        "[test_search_api.py] /api/normalizeinput: cassini revnoint A"
        url = '/__api/normalizeinput.json?CASSINIrevnoint2=A&reqno=123'
        expected = {"CASSINIrevnoint2": "00A", "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_cassini_orbit_int2(self):
        "[test_search_api.py] /api/normalizeinput: cassini revnoint 00A"
        url = '/__api/normalizeinput.json?CASSINIrevnoint1=00A&reqno=123'
        expected = {"CASSINIrevnoint1": "00A", "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_cassini_orbit_int3(self):
        "[test_search_api.py] /api/normalizeinput: cassini revnoint 004"
        url = '/__api/normalizeinput.json?CASSINIrevnoint2=004&reqno=123'
        expected = {"CASSINIrevnoint2": "004", "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_cassini_orbit_int_bad(self):
        "[test_search_api.py] /api/normalizeinput: cassini revnoint bad value 00D"
        url = '/__api/normalizeinput.json?CASSINIrevnoint1=00D&reqno=123'
        expected = {"CASSINIrevnoint1": None, "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_cassini_sclk1(self):
        "[test_search_api.py] /api/normalizeinput: cassini sclk1 1/1294561143"
        url = '/__api/normalizeinput.json?CASSINIspacecraftclockcount1=1/1294561143&reqno=123'
        expected = {"CASSINIspacecraftclockcount1": "1294561143.000", "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_cassini_sclk1_bad(self):
        "[test_search_api.py] /api/normalizeinput: cassini sclk1 bad value 2/1294561143"
        url = '/__api/normalizeinput.json?CASSINIspacecraftclockcount1=2/1294561143&reqno=123'
        expected = {"CASSINIspacecraftclockcount1": None, "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_cassini_sclk2(self):
        "[test_search_api.py] /api/normalizeinput: cassini sclk2 1/1294561143"
        url = '/__api/normalizeinput.json?CASSINIspacecraftclockcount2=1/1294561143&reqno=123'
        expected = {"CASSINIspacecraftclockcount2": "1294561143.000", "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_cassini_sclk2_bad(self):
        "[test_search_api.py] /api/normalizeinput: cassini sclk2 bad value 2/1294561143"
        url = '/__api/normalizeinput.json?CASSINIspacecraftclockcount2=2/1294561143&reqno=123'
        expected = {"CASSINIspacecraftclockcount2": None, "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_unit1(self):
        "[test_search_api.py] /api/normalizeinput: wavelength with cm values & unit: cm"
        url = '/__api/normalizeinput.json?wavelength1_01=0.000039&wavelength2_01=0.00007&unit-wavelength_01=cm&reqno=123'
        expected = {"wavelength1_01": "0.000039", "wavelength2_01": "0.00007", "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_unit2(self):
        "[test_search_api.py] /api/normalizeinput: wavelength with cm values & no unit (default unit)"
        url = '/__api/normalizeinput.json?wavelength1_01=0.000039&wavelength2_01=0.00007&reqno=123'
        expected = {"wavelength1_01": "0", "wavelength2_01": "0.0001", "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_unit3(self):
        "[test_search_api.py] /api/normalizeinput: wavelength with cm values & unit: microns"
        url = '/__api/normalizeinput.json?wavelength1_01=0.000039&wavelength2_01=0.00007&unit-wavelength_01=microns&reqno=123'
        expected = {"wavelength1_01": "0", "wavelength2_01": "0.0001", "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_unit4(self):
        "[test_search_api.py] /api/normalizeinput: wavelength with cm values & unit: microns & sourceunit: cm"
        url = '/__api/normalizeinput.json?wavelength1=0.000075&wavelength2=0.03&qtype-wavelength=any&unit-wavelength=microns&sourceunit-wavelength=cm&reqno=123'
        expected = {"wavelength1": "0.75", "wavelength2": "300", "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_unit5(self):
        "[test_search_api.py] /api/normalizeinput: wavelength with microns values & unit: cm & sourceunit: microns"
        url = '/__api/normalizeinput.json?wavelength1=0.75&wavelength2=300&qtype-wavelength=any&unit-wavelength=cm&sourceunit-wavelength=microns&reqno=123'
        expected = {"wavelength1": "0.000075", "wavelength2": "0.03", "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_unit6(self):
        "[test_search_api.py] /api/normalizeinput: wavelength with microns values & unit: microns & sourceunit: microns"
        url = '/__api/normalizeinput.json?wavelength1=0.75&wavelength2=300&qtype-wavelength=any&unit-wavelength=microns&sourceunit-wavelength=microns&reqno=123'
        expected = {"wavelength1": "0.75", "wavelength2": "300", "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_unit7(self):
        "[test_search_api.py] /api/normalizeinput: wavelength with cm values & no unit (default unit) & sourceunit: cm"
        url = '/__api/normalizeinput.json?wavelength1=0.000075&wavelength2=0.03&qtype-wavelength=any&sourceunit-wavelength=cm&reqno=123'
        expected = {"wavelength1": "0.75", "wavelength2": "300", "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_unit8(self):
        "[test_search_api.py] /api/normalizeinput: wavelength with cm values & no unit (default unit) & sourceunit: cm diff order"
        url = '/__api/normalizeinput.json?sourceunit-wavelength=cm&wavelength1=0.000075&wavelength2=0.03&qtype-wavelength=any&reqno=123'
        expected = {"wavelength1": "0.75", "wavelength2": "300", "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_unit9(self):
        "[test_search_api.py] /api/normalizeinput: sourceunit with numeric suffix"
        url = '/__api/normalizeinput.json?sourceunit-wavelength1=cm&wavelength1=0.000075&wavelength2=0.03&qtype-wavelength=any&reqno=123'
        self._run_status_equal(url, 404,
                    HTTP404_SEARCH_PARAMS_INVALID('/__api/normalizeinput.json'))

    def test__api_normalizeinput_unit10(self):
        "[test_search_api.py] /api/normalizeinput: sourceunit bad value"
        url = '/__api/normalizeinput.json?sourceunit-wavelength=fred&wavelength1=0.000075&wavelength2=0.03&qtype-wavelength=any&reqno=123'
        expected = {"wavelength1": "0.0001", "wavelength2": "0.03", "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_unit_overflow(self):
        "[test_search_api.py] /api/normalizeinput: wavelength overflow basic unit"
        url = '/__api/normalizeinput.json?wavelength1=1e307&unit-wavelength=cm&reqno=123'
        expected = {"wavelength1": None, "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_unit_overflow_conversion(self):
        "[test_search_api.py] /api/normalizeinput: wavelength overflow unit conversion"
        url = '/__api/normalizeinput.json?wavelength1=1e307&sourceunit-wavelength=cm&unit-wavelength=microns&reqno=123'
        expected = {"wavelength1": None, "reqno": 123}
        self._run_json_equal(url, expected)


            ########################################################
            ######### /__api/stringsearchchoices API TESTS #########
            ########################################################

    def test__api_stringsearchchoices_bad_slug(self):
        "[test_search_api.py] /api/stringsearchchoices: bad slug"
        url = '/__api/stringsearchchoices/fredethel.json?reqno=123'
        self._run_status_equal(url, 404,
                    HTTP404_UNKNOWN_SLUG('fredethel',
                                '/__api/stringsearchchoices/fredethel.json'))

    def test__api_stringsearchchoices_bad_limit(self):
        "[test_search_api.py] /api/stringsearchchoices: bad limit"
        url = '/__api/stringsearchchoices/volumeid.json?limit=0A&reqno=123'
        self._run_status_equal(url, 404,
                    HTTP404_BAD_LIMIT('0A',
                                '/__api/stringsearchchoices/volumeid.json'))

    def test__api_stringsearchchoices_bad_limit_val_n1(self):
        "[test_search_api.py] /api/stringsearchchoices: bad limit -1"
        url = '/__api/stringsearchchoices/volumeid.json?limit=-1&reqno=123'
        self._run_status_equal(url, 404,
                    HTTP404_BAD_LIMIT('-1',
                                '/__api/stringsearchchoices/volumeid.json'))

    def test__api_stringsearchchoices_bad_limit_val_0(self):
        "[test_search_api.py] /api/stringsearchchoices: bad limit 0"
        url = '/__api/stringsearchchoices/volumeid.json?limit=0&reqno=123'
        self._run_status_equal(url, 404,
                    HTTP404_BAD_LIMIT('0',
                                '/__api/stringsearchchoices/volumeid.json'))

    def test__api_stringsearchchoices_bad_limit_val_1000000000001(self):
        "[test_search_api.py] /api/stringsearchchoices: bad limit 1000000000001"
        url = '/__api/stringsearchchoices/volumeid.json?limit=1000000000001&reqno=123'
        self._run_status_equal(url, 404,
                    HTTP404_BAD_LIMIT('1000000000001',
                                '/__api/stringsearchchoices/volumeid.json'))

    def test__api_stringsearchchoices_bad_search(self):
        "[test_search_api.py] /api/stringsearchchoices: bad search"
        url = '/__api/stringsearchchoices/volumeid.json?fredethel=2&reqno=123'
        self._run_status_equal(url, 404,
                    HTTP404_SEARCH_PARAMS_INVALID(
                            '/__api/stringsearchchoices/volumeid.json'))

    def test__api_stringsearchchoices_bad_search2(self):
        "[test_search_api.py] /api/stringsearchchoices: bad search2"
        url = '/__api/stringsearchchoices/volumeid.json?missionid=A&reqno=123'
        self._run_status_equal(url, 404,
                    HTTP404_SEARCH_PARAMS_INVALID(
                            '/__api/stringsearchchoices/volumeid.json'))

    def test__api_stringsearchchoices_opusid_COISS_2002_regex_good(self):
        "[test_search_api.py] /api/stringsearchchoices: opusid volumeid COISS_2002 regex good"
        url = r'/opus/__api/stringsearchchoices/opusid.json?volumeid=COISS_2002&opusid=co-iss-n14609\d0&qtype-opusid=regex&reqno=123'
        expected = {'choices': ['<b>co-iss-n1460960</b>653',
                                '<b>co-iss-n1460960</b>868',
                                '<b>co-iss-n1460960</b>908',
                                '<b>co-iss-n1460960</b>944',
                                '<b>co-iss-n1460960</b>992',
                                '<b>co-iss-n1460970</b>939',
                                '<b>co-iss-n1460980</b>093',
                                '<b>co-iss-n1460980</b>638',
                                '<b>co-iss-n1460980</b>902',
                                '<b>co-iss-n1460980</b>958'],
                    'full_search': False,
                    'truncated_results': False, "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_stringsearchchoices_opusid_COISS_2002_regex_bad(self):
        "[test_search_api.py] /api/stringsearchchoices: opusid volumeid COISS_2002 regex bad"
        url = r'/opus/__api/stringsearchchoices/opusid.json?volumeid=COISS_2002&opusid=co-iss-n14609\d0\&qtype-opusid=regex&reqno=123'
        expected = {'choices': [],
                    'full_search': True,
                    'truncated_results': False, "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_stringsearchchoices_volumeid_empty_bigcache(self):
        "[test_search_api.py] /api/stringsearchchoices: volumeid empty"
        settings.STRINGCHOICE_FULL_SEARCH_COUNT_THRESHOLD = 1
        url = '/__api/stringsearchchoices/volumeid.json?volumeid=&reqno=123&limit=10000'
        expected = {'choices': ['COISS_2002', 'GO_0017'],
                    # 'full_search': False,
                    'truncated_results': False, "reqno": 123}
        self._run_stringsearchchoices_subset(url, expected)

    def test__api_stringsearchchoices_volumeid_none(self):
        "[test_search_api.py] /api/stringsearchchoices: volumeid none"
        url = '/__api/stringsearchchoices/volumeid.json?volumeid=BAD_VOLUME&reqno=123'
        expected = {'choices': [],
                    # 'full_search': False,
                    'truncated_results': False, "reqno": 123}
        self._run_json_equal(url, expected, ignore=['full_search'])

    def test__api_stringsearchchoices_volumeid_none_no_reqno(self):
        "[test_search_api.py] /api/stringsearchchoices: volumeid none no reqno"
        url = '/__api/stringsearchchoices/volumeid.json?volumeid=BAD_VOLUME'
        self._run_status_equal(url, 404,
                    HTTP404_BAD_OR_MISSING_REQNO(
                            '/__api/stringsearchchoices/volumeid.json'))

    def test__api_stringsearchchoices_volumeid_GO_0017(self):
        "[test_search_api.py] /api/stringsearchchoices: volumeid GO_0017"
        url = '/__api/stringsearchchoices/volumeid.json?volumeid=GO_0017&reqno=123'
        expected = {'choices': ['<b>GO_0017</b>'],
                    # 'full_search': False,
                    'truncated_results': False, "reqno": 123}
        self._run_json_equal(url, expected, ignore=['full_search'])

    def test__api_stringsearchchoices_volumeid_O_0017(self):
        "[test_search_api.py] /api/stringsearchchoices: volumeid O_0017"
        url = '/__api/stringsearchchoices/volumeid.json?volumeid=O_0017&reqno=123'
        expected = {'choices': ['G<b>O_0017</b>'],
                    # 'full_search': False,
                    'truncated_results': False, "reqno": 123}
        self._run_json_equal(url, expected, ignore=['full_search'])

    def test__api_stringsearchchoices_volumeid_COISS_2002(self):
        "[test_search_api.py] /api/stringsearchchoices: volumeid COISS_2002"
        url = '/__api/stringsearchchoices/volumeid.json?volumeid=COISS_2002&reqno=123'
        expected = {'choices': ['<b>COISS_2002</b>'],
                    # 'full_search': False,
                    'truncated_results': False, "reqno": 123}
        self._run_json_equal(url, expected, ignore=['full_search'])

    def test__api_stringsearchchoices_datasetid_empty_COISS_2002(self):
        "[test_search_api.py] /api/stringsearchchoices: datasetid empty volumeid COISS_2002"
        url = '/__api/stringsearchchoices/datasetid.json?volumeid=COISS_2002&datasetid=&reqno=123'
        expected = {'choices': ['CO-S-ISSNA/ISSWA-2-EDR-V1.0'],
                    'full_search': False,
                    'truncated_results': False, "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_stringsearchchoices_datasetid_empty2_COISS_2002(self):
        "[test_search_api.py] /api/stringsearchchoices: datasetid empty2 volumeid COISS_2002"
        url = '/__api/stringsearchchoices/datasetid.json?volumeid=COISS_2002&reqno=123'
        expected = {'choices': ['CO-S-ISSNA/ISSWA-2-EDR-V1.0'],
                    'full_search': False,
                    'truncated_results': False, "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_stringsearchchoices_datasetid_begin_COISS_2002(self):
        "[test_search_api.py] /api/stringsearchchoices: datasetid CO-S volumeid COISS_2002"
        url = '/__api/stringsearchchoices/datasetid.json?volumeid=COISS_2002&datasetid=CO-S&reqno=123'
        expected = {'choices': ['<b>CO-S</b>-ISSNA/ISSWA-2-EDR-V1.0'],
                    'full_search': False,
                    'truncated_results': False, "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_stringsearchchoices_datasetid_middle_COISS_2002(self):
        "[test_search_api.py] /api/stringsearchchoices: datasetid ISSWA volumeid COISS_2002"
        url = '/__api/stringsearchchoices/datasetid.json?volumeid=COISS_2002&datasetid=ISSWA&reqno=123'
        expected = {'choices': ['CO-S-ISSNA/<b>ISSWA</b>-2-EDR-V1.0'],
                    'full_search': False,
                    'truncated_results': False, "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_stringsearchchoices_datasetid_end_COISS_2002(self):
        "[test_search_api.py] /api/stringsearchchoices: datasetid V1.0 volumeid COISS_2002"
        url = '/__api/stringsearchchoices/datasetid.json?volumeid=COISS_2002&datasetid=V1.0&reqno=123'
        expected = {'choices': ['CO-S-ISSNA/ISSWA-2-EDR-<b>V1.0</b>'],
                    'full_search': False,
                    'truncated_results': False, "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_stringsearchchoices_datasetid_COISS_2002_begins_good(self):
        "[test_search_api.py] /api/stringsearchchoices: datasetid CO-S volumeid COISS_2002 begins good"
        url = '/__api/stringsearchchoices/datasetid.json?volumeid=COISS_2002&datasetid=CO-S&qtype-datasetid=begins&reqno=123'
        expected = {'choices': ['<b>CO-S</b>-ISSNA/ISSWA-2-EDR-V1.0'],
                    'full_search': False,
                    'truncated_results': False, "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_stringsearchchoices_datasetid_COISS_2002_begins_bad(self):
        "[test_search_api.py] /api/stringsearchchoices: datasetid CO-S volumeid COISS_2002 begins bad"
        url = '/__api/stringsearchchoices/datasetid.json?volumeid=COISS_2002&datasetid=O-S&qtype-datasetid=begins&reqno=123'
        expected = {'choices': [],
                    'full_search': False,
                    'truncated_results': False, "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_stringsearchchoices_datasetid_COISS_2002_contains_good(self):
        "[test_search_api.py] /api/stringsearchchoices: datasetid ISSNA volumeid COISS_2002 contains good"
        url = '/__api/stringsearchchoices/datasetid.json?volumeid=COISS_2002&datasetid=ISSNA&qtype-datasetid=contains&reqno=123'
        expected = {'choices': ['CO-S-<b>ISSNA</b>/ISSWA-2-EDR-V1.0'],
                    'full_search': False,
                    'truncated_results': False, "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_stringsearchchoices_datasetid_COISS_2002_contains_bad(self):
        "[test_search_api.py] /api/stringsearchchoices: datasetid ISSNAISSWA volumeid COISS_2002 contains bad"
        url = '/__api/stringsearchchoices/datasetid.json?volumeid=COISS_2002&datasetid=ISSNAISSWA&qtype-datasetid=contains&reqno=123'
        expected = {'choices': [],
                    'full_search': False,
                    'truncated_results': False, "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_stringsearchchoices_datasetid_COISS_2002_ends_good(self):
        "[test_search_api.py] /api/stringsearchchoices: datasetid V1.0 volumeid COISS_2002 ends good"
        url = '/__api/stringsearchchoices/datasetid.json?volumeid=COISS_2002&datasetid=V1.0&qtype-datasetid=ends&reqno=123'
        expected = {'choices': ['CO-S-ISSNA/ISSWA-2-EDR-<b>V1.0</b>'],
                    'full_search': False,
                    'truncated_results': False, "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_stringsearchchoices_datasetid_COISS_2002_ends_bad(self):
        "[test_search_api.py] /api/stringsearchchoices: datasetid O-S volumeid COISS_2002 ends bad"
        url = '/__api/stringsearchchoices/datasetid.json?volumeid=COISS_2002&datasetid=O-S&qtype-datasetid=ends&reqno=123'
        expected = {'choices': [],
                    'full_search': False,
                    'truncated_results': False, "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_stringsearchchoices_datasetid_COISS_2002_matches_good(self):
        "[test_search_api.py] /api/stringsearchchoices: datasetid ISSNA volumeid COISS_2002 matches good"
        url = '/__api/stringsearchchoices/datasetid.json?volumeid=COISS_2002&datasetid=ISSNA&qtype-datasetid=matches&reqno=123'
        expected = {'choices': ['CO-S-<b>ISSNA</b>/ISSWA-2-EDR-V1.0'],
                    'full_search': False,
                    'truncated_results': False, "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_stringsearchchoices_datasetid_COISS_2002_matches_bad(self):
        "[test_search_api.py] /api/stringsearchchoices: datasetid ISSNAX volumeid COISS_2002 matches bad"
        url = '/__api/stringsearchchoices/datasetid.json?volumeid=COISS_2002&datasetid=ISSNAX&qtype-datasetid=matches&reqno=123'
        expected = {'choices': [],
                    'full_search': False,
                    'truncated_results': False, "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_stringsearchchoices_datasetid_COISS_2002_excludes_good(self):
        "[test_search_api.py] /api/stringsearchchoices: datasetid V1 volumeid COISS_2002 excludes good"
        url = '/__api/stringsearchchoices/datasetid.json?volumeid=COISS_2002&datasetid=V1&qtype-datasetid=excludes&reqno=123'
        expected = {'choices': [],
                    'full_search': False,
                    'truncated_results': False, "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_stringsearchchoices_datasetid_COISS_2002_excludes_bad(self):
        "[test_search_api.py] /api/stringsearchchoices: datasetid V1X volumeid COISS_2002 excludes bad"
        url = '/__api/stringsearchchoices/datasetid.json?volumeid=COISS_2002&datasetid=V1X&qtype-datasetid=excludes&reqno=123'
        expected = {'choices': ['CO-S-ISSNA/ISSWA-2-EDR-V1.0'],
                    'full_search': False,
                    'truncated_results': False, "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_stringsearchchoices_datasetid_COISS_2002_regex_good(self):
        "[test_search_api.py] /api/stringsearchchoices: datasetid [A-Z]{3}NA volumeid COISS_2002 regex good"
        url = '/opus/__api/stringsearchchoices/datasetid.json?volumeid=COISS_2002&datasetid=[A-Z]{3}NA&qtype-datasetid=regex&reqno=123'
        expected = {'choices': ['CO-S-<b>ISSNA</b>/ISSWA-2-EDR-V1.0'],
                    'full_search': False,
                    'truncated_results': False, "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_stringsearchchoices_datasetid_COISS_2002_regex_bad(self):
        "[test_search_api.py] /api/stringsearchchoices: datasetid [A-Z]{3}(NA volumeid COISS_2002 regex bad"
        url = '/opus/__api/stringsearchchoices/datasetid.json?volumeid=COISS_2002&datasetid=[A-Z]{3}(NA&qtype-datasetid=regex&reqno=123'
        expected = {'choices': [],
                    'full_search': True,
                    'truncated_results': False, "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_stringsearchchoices_productid_14609_COISS_2002(self):
        "[test_search_api.py] /api/stringsearchchoices: productid 14609 volumeid COISS_2002"
        url = '/__api/stringsearchchoices/productid.json?volumeid=COISS_2002&productid=14609&reqno=123'
        expected = {'choices': ['1_N<b>14609</b>60653.122', '1_N<b>14609</b>60868.118', '1_N<b>14609</b>60908.120', '1_N<b>14609</b>60944.118', '1_N<b>14609</b>60992.120', '1_N<b>14609</b>61026.118', '1_N<b>14609</b>61061.118', '1_N<b>14609</b>61193.118', '1_N<b>14609</b>62279.118', '1_N<b>14609</b>62327.120', '1_N<b>14609</b>62415.121', '1_N<b>14609</b>64003.118', '1_N<b>14609</b>64043.120', '1_N<b>14609</b>65631.118', '1_N<b>14609</b>65679.120', '1_N<b>14609</b>65767.121', '1_N<b>14609</b>66953.122', '1_N<b>14609</b>67168.118', '1_N<b>14609</b>67208.120', '1_N<b>14609</b>67244.118', '1_N<b>14609</b>67292.120', '1_N<b>14609</b>67326.118', '1_N<b>14609</b>67361.118', '1_N<b>14609</b>67493.118', '1_N<b>14609</b>69019.122', '1_N<b>14609</b>69979.122', '1_N<b>14609</b>70939.122', '1_N<b>14609</b>71899.122', '1_N<b>14609</b>73253.122', '1_N<b>14609</b>73468.118', '1_N<b>14609</b>73508.120', '1_N<b>14609</b>73544.118', '1_N<b>14609</b>73592.120', '1_N<b>14609</b>73626.118', '1_N<b>14609</b>73661.118', '1_N<b>14609</b>73793.118', '1_N<b>14609</b>74303.122', '1_N<b>14609</b>74933.122', '1_N<b>14609</b>75548.122', '1_N<b>14609</b>79553.122', '1_N<b>14609</b>79768.118', '1_N<b>14609</b>79808.120', '1_N<b>14609</b>79844.118', '1_N<b>14609</b>79892.120', '1_N<b>14609</b>79926.118', '1_N<b>14609</b>79961.118', '1_N<b>14609</b>80093.118', '1_N<b>14609</b>80638.122', '1_N<b>14609</b>80902.123', '1_N<b>14609</b>80958.125', '1_N<b>14609</b>81222.126', '1_N<b>14609</b>81262.127', '1_N<b>14609</b>81366.128', '1_N<b>14609</b>81733.118', '1_N<b>14609</b>81997.120', '1_N<b>14609</b>82134.118', '1_N<b>14609</b>82398.120', '1_N<b>14609</b>82871.118', '1_N<b>14609</b>83007.120', '1_N<b>14609</b>83208.118', '1_N<b>14609</b>83728.120', '1_N<b>14609</b>84033.118', '1_N<b>14609</b>84297.120', '1_N<b>14609</b>84498.118', '1_N<b>14609</b>84762.120', '1_N<b>14609</b>84899.118', '1_N<b>14609</b>85164.118', '1_N<b>14609</b>85853.122', '1_N<b>14609</b>86068.118', '1_N<b>14609</b>86108.120', '1_N<b>14609</b>86144.118', '1_N<b>14609</b>86192.120', '1_N<b>14609</b>86226.118', '1_N<b>14609</b>86261.118', '1_N<b>14609</b>86393.118', '1_N<b>14609</b>88537.122'],
                    'full_search': False,
                    'truncated_results': False, "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_stringsearchchoices_productid_14609_COISS_2002_limit76(self):
        "[test_search_api.py] /api/stringsearchchoices: productid 14609 volumeid COISS_2002 limit 76"
        url = '/__api/stringsearchchoices/productid.json?volumeid=COISS_2002&productid=14609&limit=76&reqno=123'
        expected = {'choices': ['1_N<b>14609</b>60653.122', '1_N<b>14609</b>60868.118', '1_N<b>14609</b>60908.120', '1_N<b>14609</b>60944.118', '1_N<b>14609</b>60992.120', '1_N<b>14609</b>61026.118', '1_N<b>14609</b>61061.118', '1_N<b>14609</b>61193.118', '1_N<b>14609</b>62279.118', '1_N<b>14609</b>62327.120', '1_N<b>14609</b>62415.121', '1_N<b>14609</b>64003.118', '1_N<b>14609</b>64043.120', '1_N<b>14609</b>65631.118', '1_N<b>14609</b>65679.120', '1_N<b>14609</b>65767.121', '1_N<b>14609</b>66953.122', '1_N<b>14609</b>67168.118', '1_N<b>14609</b>67208.120', '1_N<b>14609</b>67244.118', '1_N<b>14609</b>67292.120', '1_N<b>14609</b>67326.118', '1_N<b>14609</b>67361.118', '1_N<b>14609</b>67493.118', '1_N<b>14609</b>69019.122', '1_N<b>14609</b>69979.122', '1_N<b>14609</b>70939.122', '1_N<b>14609</b>71899.122', '1_N<b>14609</b>73253.122', '1_N<b>14609</b>73468.118', '1_N<b>14609</b>73508.120', '1_N<b>14609</b>73544.118', '1_N<b>14609</b>73592.120', '1_N<b>14609</b>73626.118', '1_N<b>14609</b>73661.118', '1_N<b>14609</b>73793.118', '1_N<b>14609</b>74303.122', '1_N<b>14609</b>74933.122', '1_N<b>14609</b>75548.122', '1_N<b>14609</b>79553.122', '1_N<b>14609</b>79768.118', '1_N<b>14609</b>79808.120', '1_N<b>14609</b>79844.118', '1_N<b>14609</b>79892.120', '1_N<b>14609</b>79926.118', '1_N<b>14609</b>79961.118', '1_N<b>14609</b>80093.118', '1_N<b>14609</b>80638.122', '1_N<b>14609</b>80902.123', '1_N<b>14609</b>80958.125', '1_N<b>14609</b>81222.126', '1_N<b>14609</b>81262.127', '1_N<b>14609</b>81366.128', '1_N<b>14609</b>81733.118', '1_N<b>14609</b>81997.120', '1_N<b>14609</b>82134.118', '1_N<b>14609</b>82398.120', '1_N<b>14609</b>82871.118', '1_N<b>14609</b>83007.120', '1_N<b>14609</b>83208.118', '1_N<b>14609</b>83728.120', '1_N<b>14609</b>84033.118', '1_N<b>14609</b>84297.120', '1_N<b>14609</b>84498.118', '1_N<b>14609</b>84762.120', '1_N<b>14609</b>84899.118', '1_N<b>14609</b>85164.118', '1_N<b>14609</b>85853.122', '1_N<b>14609</b>86068.118', '1_N<b>14609</b>86108.120', '1_N<b>14609</b>86144.118', '1_N<b>14609</b>86192.120', '1_N<b>14609</b>86226.118', '1_N<b>14609</b>86261.118', '1_N<b>14609</b>86393.118', '1_N<b>14609</b>88537.122'],
                    'full_search': False,
                    'truncated_results': False, "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_stringsearchchoices_productid_14609_COISS_2002_limit75(self):
        "[test_search_api.py] /api/stringsearchchoices: productid 14609 volumeid COISS_2002 limit 75"
        url = '/__api/stringsearchchoices/productid.json?volumeid=COISS_2002&productid=14609&limit=75&reqno=123'
        expected = {'choices': ['1_N<b>14609</b>60653.122', '1_N<b>14609</b>60868.118', '1_N<b>14609</b>60908.120', '1_N<b>14609</b>60944.118', '1_N<b>14609</b>60992.120', '1_N<b>14609</b>61026.118', '1_N<b>14609</b>61061.118', '1_N<b>14609</b>61193.118', '1_N<b>14609</b>62279.118', '1_N<b>14609</b>62327.120', '1_N<b>14609</b>62415.121', '1_N<b>14609</b>64003.118', '1_N<b>14609</b>64043.120', '1_N<b>14609</b>65631.118', '1_N<b>14609</b>65679.120', '1_N<b>14609</b>65767.121', '1_N<b>14609</b>66953.122', '1_N<b>14609</b>67168.118', '1_N<b>14609</b>67208.120', '1_N<b>14609</b>67244.118', '1_N<b>14609</b>67292.120', '1_N<b>14609</b>67326.118', '1_N<b>14609</b>67361.118', '1_N<b>14609</b>67493.118', '1_N<b>14609</b>69019.122', '1_N<b>14609</b>69979.122', '1_N<b>14609</b>70939.122', '1_N<b>14609</b>71899.122', '1_N<b>14609</b>73253.122', '1_N<b>14609</b>73468.118', '1_N<b>14609</b>73508.120', '1_N<b>14609</b>73544.118', '1_N<b>14609</b>73592.120', '1_N<b>14609</b>73626.118', '1_N<b>14609</b>73661.118', '1_N<b>14609</b>73793.118', '1_N<b>14609</b>74303.122', '1_N<b>14609</b>74933.122', '1_N<b>14609</b>75548.122', '1_N<b>14609</b>79553.122', '1_N<b>14609</b>79768.118', '1_N<b>14609</b>79808.120', '1_N<b>14609</b>79844.118', '1_N<b>14609</b>79892.120', '1_N<b>14609</b>79926.118', '1_N<b>14609</b>79961.118', '1_N<b>14609</b>80093.118', '1_N<b>14609</b>80638.122', '1_N<b>14609</b>80902.123', '1_N<b>14609</b>80958.125', '1_N<b>14609</b>81222.126', '1_N<b>14609</b>81262.127', '1_N<b>14609</b>81366.128', '1_N<b>14609</b>81733.118', '1_N<b>14609</b>81997.120', '1_N<b>14609</b>82134.118', '1_N<b>14609</b>82398.120', '1_N<b>14609</b>82871.118', '1_N<b>14609</b>83007.120', '1_N<b>14609</b>83208.118', '1_N<b>14609</b>83728.120', '1_N<b>14609</b>84033.118', '1_N<b>14609</b>84297.120', '1_N<b>14609</b>84498.118', '1_N<b>14609</b>84762.120', '1_N<b>14609</b>84899.118', '1_N<b>14609</b>85164.118', '1_N<b>14609</b>85853.122', '1_N<b>14609</b>86068.118', '1_N<b>14609</b>86108.120', '1_N<b>14609</b>86144.118', '1_N<b>14609</b>86192.120', '1_N<b>14609</b>86226.118', '1_N<b>14609</b>86261.118', '1_N<b>14609</b>86393.118'],
                    'full_search': False,
                    'truncated_results': True, "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_stringsearchchoices_productid_14609_COISS_2002_limit3(self):
        "[test_search_api.py] /api/stringsearchchoices: productid 14609 volumeid COISS_2002 limit 3"
        url = '/__api/stringsearchchoices/productid.json?volumeid=COISS_2002&productid=14609&limit=3&reqno=123'
        expected = {'choices': ['1_N<b>14609</b>60653.122', '1_N<b>14609</b>60868.118', '1_N<b>14609</b>60908.120'],
                    'full_search': False,
                    'truncated_results': True, "reqno": 123}
        self._run_json_equal(url, expected)

    def test__api_stringsearchchoices_volumeid_002_COISS(self):
        "[test_search_api.py] /api/stringsearchchoices: volumeid 002 instrumentid COISS"
        # The time constraint eliminates COISS_1002 as a result
        url = '/__api/stringsearchchoices/volumeid.json?volumeid=002&instrument=Cassini+ISS&time1=2004-02-06T02:07:06.418&reqno=123'
        expected = {'choices': ['COISS_2<b>002</b>'],
                    # 'full_search': False,
                    'truncated_results': False, "reqno": 123}
        self._run_stringsearchchoices_subset(url, expected)

    def test__api_stringsearchchoices_volumeid_002_COUVIS(self):
        "[test_search_api.py] /api/stringsearchchoices: volumeid 002 instrumentid COUVIS"
        # The time constraint eliminates COUVIS_002x as results
        url = '/__api/stringsearchchoices/volumeid.json?volumeid=002&instrument=Cassini+UVIS&time2=2007-04-05T03:56:00.537&reqno=123'
        expected = {'choices': ['COUVIS_0<b>002</b>'],
                    # 'full_search': False,
                    'truncated_results': False, "reqno": 123}
        self._run_stringsearchchoices_subset(url, expected)

    def test__api_stringsearchchoices_volumeid_002_COISS_bigcache(self):
        "[test_search_api.py] /api/stringsearchchoices: volumeid 002 instrumentid COISS bigcache"
        settings.STRINGCHOICE_FULL_SEARCH_COUNT_THRESHOLD = 1
        url = '/__api/stringsearchchoices/volumeid.json?volumeid=002&instrument=Cassini+ISS&reqno=123'
        expected = {'choices': ['COISS_2<b>002</b>', 'COUVIS_0<b>002</b>'],
                    'full_search': True,
                    'truncated_results': False, "reqno": 123}
        self._run_stringsearchchoices_subset(url, expected)

    def test__api_stringsearchchoices_volumeid_002_COUVIS_bigcache(self):
        "[test_search_api.py] /api/stringsearchchoices: volumeid 002 instrumentid COUVIS bigcache"
        settings.STRINGCHOICE_FULL_SEARCH_COUNT_THRESHOLD = 1
        # The time constraints eliminate COISS_1002 and COUVIS_002x as results
        url = '/__api/stringsearchchoices/volumeid.json?volumeid=002&instrument=Cassini+UVIS&reqno=123'
        expected = {'choices': ['COISS_2<b>002</b>', 'COUVIS_0<b>002</b>'],
                    'full_search': True,
                    'truncated_results': False, "reqno": 123}
        self._run_stringsearchchoices_subset(url, expected)

    def test__api_stringsearchchoices_volumeid_002_COISS_timeout(self):
        "[test_search_api.py] /api/stringsearchchoices: volumeid 002 instrumentid COISS timeout"
        settings.STRINGCHOICE_FULL_SEARCH_TIME_THRESHOLD = 1
        url = '/__api/stringsearchchoices/volumeid.json?volumeid=002&instrument=Cassini+ISS&reqno=123'
        expected = {'choices': ['COISS_2<b>002</b>', 'COUVIS_0<b>002</b>'],
                    'full_search': True,
                    'truncated_results': False, "reqno": 123}
        self._run_stringsearchchoices_subset(url, expected)

    def test__api_stringsearchchoices_volumeid_002_COUVIS_timeout(self):
        "[test_search_api.py] /api/stringsearchchoices: volumeid 002 instrumentid COUVIS timeout"
        settings.STRINGCHOICE_FULL_SEARCH_TIME_THRESHOLD = 1
        url = '/__api/stringsearchchoices/volumeid.json?volumeid=002&instrument=Cassini+UVIS&reqno=123'
        expected = {'choices': ['COISS_2<b>002</b>', 'COUVIS_0<b>002</b>'],
                    'full_search': True,
                    'truncated_results': False, "reqno": 123}
        self._run_stringsearchchoices_subset(url, expected)

    def test__api_stringsearchchoices_volumeid_O_0017_cache(self):
        "[test_search_api.py] /api/stringsearchchoices: volumeid O_0017 cached reqno"
        # Make sure that reqno isn't cached along with the rest of the result
        url = '/__api/stringsearchchoices/volumeid.json?volumeid=O_0017&reqno=5&reqno=123'
        expected = {'choices': ['G<b>O_0017</b>'],
                    # 'full_search': False,
                    'truncated_results': False,
                    'reqno': 5, "reqno": 123}
        self._run_json_equal(url, expected, ignore=['full_search'])
        url = '/__api/stringsearchchoices/volumeid.json?volumeid=O_0017&reqno=100&reqno=123'
        expected = {'choices': ['G<b>O_0017</b>'],
                    # 'full_search': False,
                    'truncated_results': False,
                    'reqno': 100, "reqno": 123}
        self._run_json_equal(url, expected, ignore=['full_search'])

    def test__api_stringsearchchoices_underscore(self):
        "[test_search_api.py] /api/stringsearchchoices: underscore"
        url = '/__api/stringsearchchoices/volumeid.json?volumeid=____&reqno=123'
        expected = {'choices': [],
                    # 'full_search': False,
                    'truncated_results': False, "reqno": 123}
        self._run_json_equal(url, expected, ignore=['full_search'])

    def test__api_stringsearchchoices_percent(self):
        "[test_search_api.py] /api/stringsearchchoices: percent"
        url = '/__api/stringsearchchoices/volumeid.json?volumeid=%%&reqno=123'
        expected = {'choices': [],
                    # 'full_search': False,
                    'truncated_results': False, "reqno": 123}
        self._run_json_equal(url, expected, ignore=['full_search'])

    def test__api_stringsearchchoices_lower_case(self):
        "[test_search_api.py] /api/stringsearchchoices: lower_case"
        url = '/__api/stringsearchchoices/volumeid.json?volumeid=coiss_2002&reqno=123'
        expected = {'choices': ['<b>COISS_2002</b>'],
                    # 'full_search': False,
                    'truncated_results': False, "reqno": 123}
        self._run_json_equal(url, expected, ignore=['full_search'])

    def test__api_stringsearchchoices_parens(self):
        "[test_search_api.py] /api/stringsearchchoices: parens"
        url = '/__api/stringsearchchoices/volumeid.json?volumeid=coiss_)&reqno=123'
        expected = {'choices': [],
                    # 'full_search': False,
                    'truncated_results': False, "reqno": 123}
        self._run_json_equal(url, expected, ignore=['full_search'])

    def test__api_stringsearchchoices_parens2(self):
        "[test_search_api.py] /api/stringsearchchoices: parens 2"
        url = '/__api/stringsearchchoices/volumeid.json?volumeid=coiss_()&reqno=123'
        expected = {'choices': [],
                    # 'full_search': False,
                    'truncated_results': False, "reqno": 123}
        self._run_json_equal(url, expected, ignore=['full_search'])

    def test__api_stringsearchchoices_backslash(self):
        "[test_search_api.py] /api/stringsearchchoices: backslash"
        url = '/__api/stringsearchchoices/volumeid.json?volumeid=\\1&reqno=123'
        expected = {'choices': [],
                    # 'full_search': False,
                    'truncated_results': False, "reqno": 123}
        self._run_json_equal(url, expected, ignore=['full_search'])
