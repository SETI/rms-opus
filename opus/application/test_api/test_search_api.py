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

class ApiSearchTests(TestCase):
    GO_LIVE = False
    LIVE_TARGET = "production"

    # disable error logging and trace output before test
    def setUp(self):
        logging.disable(logging.ERROR)

    # enable error logging and trace output after test
    def teardown(self):
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


            ################################################
            ######### /api/normalizeinput API TESTS #########
            ################################################

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

    def test__api_normalizeinput_cassini_orbit1(self):
        "/api/normalizeinput: cassini revno A"
        url = '/opus/__api/normalizeinput.json?CASSINIrevnoint1=A'
        expected = {"CASSINIrevnoint1": "00A"}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_cassini_orbit2(self):
        "/api/normalizeinput: cassini revno 00A"
        url = '/opus/__api/normalizeinput.json?CASSINIrevnoint1=00A'
        expected = {"CASSINIrevnoint1": "00A"}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_cassini_orbit3(self):
        "/api/normalizeinput: cassini revno 004"
        url = '/opus/__api/normalizeinput.json?CASSINIrevnoint1=004'
        expected = {"CASSINIrevnoint1": "004"}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_cassini_orbit_bad(self):
        "/api/normalizeinput: cassini revno bad value 00D"
        url = '/opus/__api/normalizeinput.json?CASSINIrevnoint1=00D'
        expected = {"CASSINIrevnoint1": None}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_cassini_sclk(self):
        "/api/normalizeinput: cassini sclk 1/1294561143"
        url = '/opus/__api/normalizeinput.json?CASSINIspacecraftclockcountdec1=1/1294561143'
        expected = {"CASSINIspacecraftclockcountdec1": "1294561143.000"}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_cassini_sclk_bad(self):
        "/api/normalizeinput: cassini sclk bad value 2/1294561143"
        url = '/opus/__api/normalizeinput.json?CASSINIspacecraftclockcountdec1=2/1294561143'
        expected = {"CASSINIspacecraftclockcountdec1": None}
        self._run_json_equal(url, expected)
