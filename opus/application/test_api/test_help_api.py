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

    def test__api_help_about_pdf(self):
        "[test_help_api.py] /__help: about pdf"
        url = '/__help/about.pdf'
        self._run_status_equal(url, 200)

    def test__api_help_volumes(self):
        "[test_help_api.py] /__help: volumes"
        url = '/__help/volumes.html'
        self._run_status_equal(url, 200)

    def test__api_help_volumes_pdf(self):
        "[test_help_api.py] /__help: volumes pdf"
        url = '/__help/volumes.pdf'
        self._run_status_equal(url, 200)

    def test__api_help_faq(self):
        "[test_help_api.py] /__help: faq"
        url = '/__help/faq.html'
        self._run_status_equal(url, 200)

    def test__api_help_faq_pdf(self):
        "[test_help_api.py] /__help: faq pdf"
        url = '/__help/faq.pdf'
        self._run_status_equal(url, 200)

    def test__api_help_gettingstarted(self):
        "[test_help_api.py] /__help: gettingstarted"
        url = '/__help/gettingstarted.html'
        self._run_status_equal(url, 200)

    def test__api_help_gettingstarted_pdf(self):
        "[test_help_api.py] /__help: gettingstarted pdf"
        url = '/__help/gettingstarted.pdf'
        self._run_status_equal(url, 200)

    def test__api_help_splash(self):
        "[test_help_api.py] /__help: splash"
        url = '/__help/splash.html'
        self._run_status_equal(url, 200)

    def test__api_help_citing(self):
        "[test_help_api.py] /__help: citing"
        url = '/__help/citing.html'
        self._run_status_equal(url, 200)

    def test__api_help_citing_qr(self):
        "[test_help_api.py] /__help: citing qr"
        url = '/__help/citing.html?searchurl=fred&stateurl=george'
        self._run_status_equal(url, 200)

    def test__api_help_citing_pdf(self):
        "[test_help_api.py] /__help: citing pdf"
        url = '/__help/citing.pdf'
        self._run_status_equal(url, 200)

    def test__api_help_apiguide(self):
        "[test_help_api.py] /__help: apiguide"
        url = '/__help/apiguide.html'
        self._run_status_equal(url, 200)

    def test__api_help_apiguide_exp(self):
        "[test_help_api.py] /help: apiguide pdf"
        url = '/apiguide.pdf'
        self._run_status_equal(url, 200)

    def test__api_help_apiguide_pdf(self):
        "[test_help_api.py] /__help: apiguide pdf"
        url = '/__help/apiguide.pdf'
        self._run_status_equal(url, 200)

    def test__api_help_bad(self):
        "[test_help_api.py] /__help: bad"
        url = '/__help/bad.html'
        self._run_status_equal(url, 404)
