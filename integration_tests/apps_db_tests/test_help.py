"""Tests for the help views' handling of a request that is not usable."""

import logging
from unittest import TestCase

from django.conf import settings
from django.core.cache import cache
from django.http import Http404
from django.test import RequestFactory

from opus_app.apps.help.views import (
    api_about,
    api_bundles,
    api_citing_opus,
    api_faq,
    api_gettingstarted,
    api_splash,
)

from ._broken_requests import request_without_get, request_without_meta


class HelpTests(TestCase):
    """The help views, called directly with a request they cannot use."""

    def setUp(self) -> None:
        """Turn off fault injection and error logging for one test.

        The `OPUS_FAKE_*` knobs are turned all the way up by other tests and are global,
        so every suite resets them; a suite that did not would see its own API calls
        fail at random.

        It also empties the cache, so a response another test cached cannot answer this
        one, and builds the request factory these tests call the views with.
        """
        self.maxDiff = None
        settings.OPUS_FAKE_API_DELAYS = 0
        settings.OPUS_FAKE_SERVER_ERROR404_PROBABILITY = 0
        settings.OPUS_FAKE_SERVER_ERROR500_PROBABILITY = 0
        logging.disable(logging.ERROR)
        cache.clear()
        self.factory = RequestFactory()

    def tearDown(self) -> None:
        """Restore logging after one test."""
        logging.disable(logging.NOTSET)

        ########################################
        ######### api_about UNIT TESTS #########
        ########################################

    def test__api_about_no_meta(self) -> None:
        "[test_help.py] api_about: no META"
        request = request_without_meta(self.factory, 'dummy')
        with self.assertRaisesRegex(
            Http404, r'Internal error \(No request was provided\) for /__help/about.html'
        ):
            api_about(request, 'html')

    def test__api_about_no_get(self) -> None:
        "[test_help.py] api_about: no GET"
        request = request_without_get(self.factory, '__help/about.html')
        with self.assertRaisesRegex(
            Http404, r'Internal error \(No request was provided\) for /__help/about.html'
        ):
            api_about(request, 'html')

            ##########################################
            ######### api_bundles UNIT TESTS #########
            ##########################################

    def test__api_bundles_no_meta(self) -> None:
        "[test_help.py] api_bundles: no META"
        request = request_without_meta(self.factory, 'dummy')
        with self.assertRaisesRegex(
            Http404, r'Internal error \(No request was provided\) for /__help/bundles.html'
        ):
            api_bundles(request, 'html')

    def test__api_bundles_no_get(self) -> None:
        "[test_help.py] api_bundles: no GET"
        request = request_without_get(self.factory, '__help/bundles.html')
        with self.assertRaisesRegex(
            Http404, r'Internal error \(No request was provided\) for /__help/bundles.html'
        ):
            api_bundles(request, 'html')

            ######################################
            ######### api_faq UNIT TESTS #########
            ######################################

    def test__api_faq_no_meta(self) -> None:
        "[test_help.py] api_faq: no META"
        request = request_without_meta(self.factory, 'dummy')
        with self.assertRaisesRegex(
            Http404, r'Internal error \(No request was provided\) for /__help/faq.html'
        ):
            api_faq(request, 'html')

    def test__api_faq_no_get(self) -> None:
        "[test_help.py] api_faq: no GET"
        request = request_without_get(self.factory, '__help/faq.html')
        with self.assertRaisesRegex(
            Http404, r'Internal error \(No request was provided\) for /__help/faq.html'
        ):
            api_faq(request, 'html')

            #################################################
            ######### api_gettingstarted UNIT TESTS #########
            #################################################

    def test__api_gettingstarted_no_meta(self) -> None:
        "[test_help.py] api_gettingstarted: no META"
        request = request_without_meta(self.factory, 'dummy')
        with self.assertRaisesRegex(
            Http404, r'Internal error \(No request was provided\) for /__help/gettingstarted.html'
        ):
            api_gettingstarted(request, 'html')

    def test__api_gettingstarted_no_get(self) -> None:
        "[test_help.py] api_gettingstarted: no GET"
        request = request_without_get(self.factory, '__help/gettingstarted.html')
        with self.assertRaisesRegex(
            Http404, r'Internal error \(No request was provided\) for /__help/gettingstarted.html'
        ):
            api_gettingstarted(request, 'html')

            #########################################
            ######### api_splash UNIT TESTS #########
            #########################################

    def test__api_splash_no_meta(self) -> None:
        "[test_help.py] api_splash: no META"
        request = request_without_meta(self.factory, 'dummy')
        with self.assertRaisesRegex(
            Http404, r'Internal error \(No request was provided\) for /__help/splash.html'
        ):
            api_splash(request)

    def test__api_splash_no_get(self) -> None:
        "[test_help.py] api_splash: no GET"
        request = request_without_get(self.factory, '__help/splash.html')
        with self.assertRaisesRegex(
            Http404, r'Internal error \(No request was provided\) for /__help/splash.html'
        ):
            api_splash(request)

            ##############################################
            ######### api_citing_opus UNIT TESTS #########
            ##############################################

    def test__api_citing_opus_no_meta(self) -> None:
        "[test_help.py] api_citing_opus: no META"
        request = request_without_meta(self.factory, 'dummy')
        with self.assertRaisesRegex(
            Http404, r'Internal error \(No request was provided\) for /__help/citing.html'
        ):
            api_citing_opus(request, 'html')

    def test__api_citing_opus_no_get(self) -> None:
        "[test_help.py] api_citing_opus: no GET"
        request = request_without_get(self.factory, '__help/citing.html')
        with self.assertRaisesRegex(
            Http404, r'Internal error \(No request was provided\) for /__help/citing.html'
        ):
            api_citing_opus(request, 'html')
