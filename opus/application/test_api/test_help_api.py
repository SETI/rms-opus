# opus/application/test_api/test_help_api.py

import logging
import requests
import sys
from unittest import TestCase

from django.core.cache import cache
from rest_framework.test import RequestsClient

from api_test_helper import ApiTestHelper

import settings

class ApiHelpTests(TestCase, ApiTestHelper):

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


            #####################################
            ######### /__help API TESTS #########
            #####################################

    def test__api_help_about(self):
        "[test_help_api.py] /__help: about"
        url = '/opus/__help/about.html'
        self._run_status_equal(url, 200)

    def test__api_help_volumes(self):
        "[test_help_api.py] /__help: volumes"
        url = '/opus/__help/volumes.html'
        self._run_status_equal(url, 200)

    def test__api_help_faq(self):
        "[test_help_api.py] /__help: faq"
        url = '/opus/__help/faq.html'
        self._run_status_equal(url, 200)

    def test__api_help_guide(self):
        "[test_help_api.py] /__help: guide"
        url = '/opus/__help/guide.html'
        self._run_status_equal(url, 200)

    def test__api_help_tutorial(self):
        "[test_help_api.py] /__help: tutorial"
        url = '/opus/__help/tutorial.html'
        self._run_status_equal(url, 200)

    def test__api_help_bad(self):
        "[test_help_api.py] /__help: bad"
        url = '/opus/__help/bad.html'
        self._run_status_equal(url, 404)
