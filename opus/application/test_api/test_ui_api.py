# opus/application/test_api/test_ui_api.py

import json
import requests
from unittest import TestCase

from rest_framework.test import RequestsClient

from api_test_helper import ApiTestHelper

import settings

import logging
log = logging.getLogger(__name__)

settings.CACHE_BACKEND = 'dummy:///'

class ApiSearchTests(TestCase, ApiTestHelper):

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
        if 'reqno' not in expected:
            if 'reqno' in jdata:
                del jdata['reqno']
        if 'full_search' not in expected:
            if 'full_search' in jdata:
                del jdata['full_search']

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
        if 'reqno' not in expected:
            if 'reqno' in jdata:
                del jdata['reqno']
        if 'full_search' not in expected:
            if 'full_search' in jdata:
                del jdata['full_search']
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


            #####################################
            ######### /__help API TESTS #########
            #####################################

    def test__api_help_about(self):
        "/__help: about"
        url = '/opus/__help/about.html'
        self._run_status_equal(url, 200)

    def test__api_help_datasets(self):
        "/__help: datasets"
        url = '/opus/__help/datasets.html'
        self._run_status_equal(url, 200)

    def test__api_help_tutorial(self):
        "/__help: tutorial"
        url = '/opus/__help/tutorial.html'
        self._run_status_equal(url, 200)

    def test__api_help_bad(self):
        "/__help: bad"
        url = '/opus/__help/bad.html'
        self._run_status_equal(url, 404)
