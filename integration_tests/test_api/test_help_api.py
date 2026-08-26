# integration_tests/test_api/test_help_api.py

import logging
import platform
from unittest import TestCase

import requests
from django.conf import settings
from django.core.cache import cache
from rest_framework.test import RequestsClient

from .api_test_helper import ApiTestHelper, go_live_target


class ApiHelpTests(ApiTestHelper, TestCase):

    def setUp(self) -> None:
        # self.UPDATE_FILES = True
        self.maxDiff = None
        settings.OPUS_FAKE_API_DELAYS = 0
        settings.OPUS_FAKE_SERVER_ERROR404_PROBABILITY = 0
        settings.OPUS_FAKE_SERVER_ERROR500_PROBABILITY = 0
        settings.CACHE_KEY_PREFIX = 'opustest:' + settings.DB_SCHEMA_NAME
        logging.disable(logging.ERROR)
        if go_live_target(): # pragma: no cover - remote server
            self.client = requests.Session()
        else:
            self.client = RequestsClient()
        cache.clear()

    def tearDown(self) -> None:
        logging.disable(logging.NOTSET)


            #####################################
            ######### /__help API TESTS #########
            #####################################

    def test__api_help_about(self) -> None:
        "[test_help_api.py] /__help: about"
        url = '/__help/about.html'
        # Remove the GIT version number, host name, and database schema name.
        self._run_html_range_file(url, 'api_help_about.html',
                                  '<p><small>OPUS version', None)

    def test__api_help_about_pdf(self) -> None:
        "[test_help_api.py] /__help: about pdf"
        if platform.system() == 'Linux': # pragma: no cover
            url = '/__help/about.pdf'
            self._run_status_equal(url, 200)

    def test__api_help_bundles(self) -> None:
        "[test_help_api.py] /__help: bundles"
        url = '/__help/bundles.html'
        self._run_html_equal_file(url, 'api_help_bundles.html')

    def test__api_help_bundles_pdf(self) -> None:
        "[test_help_api.py] /__help: bundles pdf"
        if platform.system() == 'Linux': # pragma: no cover
            url = '/__help/bundles.pdf'
            self._run_status_equal(url, 200)

    def test__api_help_faq(self) -> None:
        "[test_help_api.py] /__help: faq"
        url = '/__help/faq.html'
        self._run_html_equal_file(url, 'api_help_faq.html')

    def test__api_help_faq_pdf(self) -> None:
        "[test_help_api.py] /__help: faq pdf"
        if platform.system() == 'Linux': # pragma: no cover
            url = '/__help/faq.pdf'
            self._run_status_equal(url, 200)

    def test__api_help_gettingstarted(self) -> None:
        "[test_help_api.py] /__help: gettingstarted"
        url = '/__help/gettingstarted.html'
        self._run_html_equal_file(url, 'api_help_gettingstarted.html')

    def test__api_help_gettingstarted_pdf(self) -> None:
        "[test_help_api.py] /__help: gettingstarted pdf"
        if platform.system() == 'Linux': # pragma: no cover
            url = '/__help/gettingstarted.pdf'
            self._run_status_equal(url, 200)

    def test__api_help_splash(self) -> None:
        "[test_help_api.py] /__help: splash"
        url = '/__help/splash.html'
        self._run_html_equal_file(url, 'api_help_splash.html')

    def test__api_help_citing(self) -> None:
        "[test_help_api.py] /__help: citing"
        url = '/__help/citing.html'
        self._run_status_equal(url, 200)

    def test__api_help_citing_qr(self) -> None:
        "[test_help_api.py] /__help: citing qr"
        url = '/__help/citing.html?searchurl=fred&stateurl=george'
        self._run_html_equal_file(url, 'api_help_citing_qr.html', embedded_dynamic_image=True)

    def test__api_help_citing_pdf(self) -> None:
        "[test_help_api.py] /__help: citing pdf"
        if platform.system() == 'Linux': # pragma: no cover
            url = '/__help/citing.pdf'
            self._run_status_equal(url, 200)

    def test__api_help_apiguide(self) -> None:
        "[test_help_api.py] /__help: apiguide"
        url = '/__help/apiguide.html'
        # Remove the "produced on" date
        self._run_html_range_file(url, 'api_help_apiguide.html',
                    'It was produced on ',
                    '<h1 class="op-help-api-guide-no-count">Table of Contents</h1>')

    def test__api_help_apiguide_exp(self) -> None:
        "[test_help_api.py] /help: apiguide pdf"
        if platform.system() == 'Linux': # pragma: no cover
            url = '/apiguide.pdf'
            self._run_status_equal(url, 200)

    def test__api_help_apiguide_pdf(self) -> None:
        "[test_help_api.py] /__help: apiguide pdf"
        if platform.system() == 'Linux': # pragma: no cover
            url = '/__help/apiguide.pdf'
            self._run_status_equal(url, 200)

    def test__api_help_bad(self) -> None:
        "[test_help_api.py] /__help: bad"
        url = '/__help/bad.html'
        self._run_status_equal(url, 404)
