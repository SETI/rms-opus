# opus/application/test_api/test_help_api.py

import json
import requests
from unittest import TestCase

from rest_framework.test import RequestsClient

from api_test_helper import ApiTestHelper

import settings

import logging
log = logging.getLogger(__name__)

settings.CACHE_BACKEND = 'dummy:///'


class ApiHelpTests(TestCase, ApiTestHelper):
    # disable error logging and trace output before test
    def setUp(self):
        settings.CACHE_KEY_PREFIX = 'opustest:' + settings.OPUS_SCHEMA_NAME
        # logging.disable(logging.ERROR)
        if settings.TEST_GO_LIVE:
            self.client = requests.Session()
        else:
            self.client = RequestsClient()

    # enable error logging and trace output after test
    def tearDown(self):
        logging.disable(logging.NOTSET)


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

    def test__api_help_faq(self):
        "/__help: faq"
        url = '/opus/__help/faq.html'
        self._run_status_equal(url, 200)

    def test__api_help_guide(self):
        "/__help: guide"
        url = '/opus/__help/guide.html'
        self._run_status_equal(url, 200)

    def test__api_help_tutorial(self):
        "/__help: tutorial"
        url = '/opus/__help/tutorial.html'
        self._run_status_equal(url, 200)

    def test__api_help_bad(self):
        "/__help: bad"
        url = '/opus/__help/bad.html'
        self._run_status_equal(url, 404)
