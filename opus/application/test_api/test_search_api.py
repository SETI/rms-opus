# opus/application/test_api/test_search_api.py

import json
import requests
import sys
from unittest import TestCase

from django.db import connection
from django.test.client import Client
from rest_framework.test import RequestsClient

from search.views import *

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
        url = '/opus/__api/normalizeinput.json?COISSmissinglines='
        expected = {"COISSmissinglines": ""}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_int_zero(self):
        "/api/normalizeinput: integer zero"
        url = '/opus/__api/normalizeinput.json?COISSmissinglines=0'
        expected = {"COISSmissinglines": "0"}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_int_neg(self):
        "/api/normalizeinput: integer negative"
        url = '/opus/__api/normalizeinput.json?COISSmissinglines=-1234567890'
        expected = {"COISSmissinglines": "-1234567890"}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_int_pos(self):
        "/api/normalizeinput: integer positive"
        url = '/opus/__api/normalizeinput.json?COISSmissinglines=1234567890'
        expected = {"COISSmissinglines": "1234567890"}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_int_spaces(self):
        "/api/normalizeinput: integer spaces"
        url = '/opus/__api/normalizeinput.json?COISSmissinglines=+1234+'
        expected = {"COISSmissinglines": "1234"}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_int_underscores(self):
        "/api/normalizeinput: integer underscores"
        url = '/opus/__api/normalizeinput.json?COISSmissinglines=_12_34_'
        expected = {"COISSmissinglines": "1234"}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_int_commas(self):
        "/api/normalizeinput: integer commas"
        url = '/opus/__api/normalizeinput.json?COISSmissinglines=,1,2,3,4,'
        expected = {"COISSmissinglines": "1234"}
        self._run_json_equal(url, expected)

    def test__api_normalizeinput_int_mixed_delim(self):
        "/api/normalizeinput: integer mixed delimiters"
        url = '/opus/__api/normalizeinput.json?COISSmissinglines=+,1_23_,+'
        expected = {"COISSmissinglines": "1234"}
        self._run_json_equal(url, expected)
