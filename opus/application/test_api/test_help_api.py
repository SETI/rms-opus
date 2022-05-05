# opus/application/test_api/test_help_api.py

import logging
import requests
from unittest import TestCase

from django.core.cache import cache
from rest_framework.test import RequestsClient

from .api_test_helper import ApiTestHelper

import settings

class ApiHelpTests(TestCase, ApiTestHelper):

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


            #####################################
            ######### /__help API TESTS #########
            #####################################

    def test__api_help_about(self):
        "[test_help_api.py] /__help: about"
        url = '/__help/about.html'
        self._run_status_equal(url, 200)

    def test__api_help_volumes(self):
        "[test_help_api.py] /__help: volumes"
        url = '/__help/volumes.html'
        self._run_status_equal(url, 200)

    def test__api_help_faq(self):
        "[test_help_api.py] /__help: faq"
        url = '/__help/faq.html'
        self._run_status_equal(url, 200)

    def test__api_help_apiguide(self):
        "[test_help_api.py] /__help: apiguide"
        url = '/__help/apiguide.html'
        self._run_status_equal(url, 200)

    def test__api_help_bad(self):
        "[test_help_api.py] /__help: bad"
        url = '/__help/bad.html'
        self._run_status_equal(url, 404)
