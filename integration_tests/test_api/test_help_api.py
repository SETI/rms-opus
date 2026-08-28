"""Golden-response tests for the help pages."""

import logging
import platform
from unittest import TestCase

import requests
from django.conf import settings
from django.core.cache import cache
from rest_framework.test import RequestsClient

from .api_test_helper import ApiTestHelper, go_live_target


class ApiHelpTests(ApiTestHelper, TestCase):
    """The help pages, one recorded response per request."""

    def setUp(self) -> None:
        # self.UPDATE_FILES = True
        """Turn off fault injection and error logging for one test.

        The `OPUS_FAKE_*` knobs are turned all the way up by other tests and are global,
        so every suite resets them; a suite that did not would see its own API calls
        fail at random.

        It also gives the cache a key prefix of this run's own schema, empties it, and
        chooses the client: a plain session for a live server, otherwise one that drives
        the WSGI application in process.
        """
        self.maxDiff = None
        settings.OPUS_FAKE_API_DELAYS = 0
        settings.OPUS_FAKE_SERVER_ERROR404_PROBABILITY = 0
        settings.OPUS_FAKE_SERVER_ERROR500_PROBABILITY = 0
        settings.CACHE_KEY_PREFIX = 'opustest:' + settings.DB_SCHEMA_NAME
        logging.disable(logging.ERROR)
        if go_live_target():  # pragma: no cover - remote server
            self.client = requests.Session()
        else:
            self.client = RequestsClient()
        cache.clear()

    def tearDown(self) -> None:
        """Restore logging after one test."""
        logging.disable(logging.NOTSET)

        #####################################
        ######### /__help API TESTS #########
        #####################################

    def test__api_help_about(self) -> None:
        "[test_help_api.py] /__help: about"
        url = '/__help/about.html'
        # Remove the GIT version number, host name, and database schema name.
        self._run_html_range_file(url, 'api_help_about.html', '<p><small>OPUS version', None)

    def test__api_help_about_pdf(self) -> None:
        "[test_help_api.py] /__help: about pdf"
        if platform.system() == 'Linux':  # pragma: no cover
            url = '/__help/about.pdf'
            self._run_status_equal(url, 200)

    def test__api_help_bundles(self) -> None:
        "[test_help_api.py] /__help: bundles"
        url = '/__help/bundles.html'
        self._run_html_equal_file(url, 'api_help_bundles.html')

    def test__api_help_bundles_pdf(self) -> None:
        "[test_help_api.py] /__help: bundles pdf"
        if platform.system() == 'Linux':  # pragma: no cover
            url = '/__help/bundles.pdf'
            self._run_status_equal(url, 200)

    def test__api_help_faq(self) -> None:
        "[test_help_api.py] /__help: faq"
        url = '/__help/faq.html'
        self._run_html_equal_file(url, 'api_help_faq.html')

    def test__api_help_faq_pdf(self) -> None:
        "[test_help_api.py] /__help: faq pdf"
        if platform.system() == 'Linux':  # pragma: no cover
            url = '/__help/faq.pdf'
            self._run_status_equal(url, 200)

    def test__api_help_gettingstarted(self) -> None:
        "[test_help_api.py] /__help: gettingstarted"
        url = '/__help/gettingstarted.html'
        self._run_html_equal_file(url, 'api_help_gettingstarted.html')

    def test__api_help_gettingstarted_pdf(self) -> None:
        "[test_help_api.py] /__help: gettingstarted pdf"
        if platform.system() == 'Linux':  # pragma: no cover
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
        if platform.system() == 'Linux':  # pragma: no cover
            url = '/__help/citing.pdf'
            self._run_status_equal(url, 200)

    def test__api_help_apiguide_redirect(self) -> None:
        """[test_help_api.py] /apiguide.pdf: redirects to the published guide

        The guide is documentation rather than a page this application renders, so
        the entry point that used to return a PDF of it answers 302 instead. The
        target is a setting, and it is asserted here rather than being spelled out
        again, so that moving the guide is one edit.
        """
        self._run_redirect_equal('/apiguide.pdf', settings.API_GUIDE_URL)

    def test__api_help_apiguide_internal_gone(self) -> None:
        """[test_help_api.py] /__help/apiguide.html: no longer served"""
        self._run_status_equal('/__help/apiguide.html', 404)

    def test__api_help_bad(self) -> None:
        "[test_help_api.py] /__help: bad"
        url = '/__help/bad.html'
        self._run_status_equal(url, 404)
