"""Tests for the cart views' handling of a request that is not usable."""

import logging
from unittest import TestCase

from django.conf import settings
from django.core.cache import cache
from django.http import Http404
from django.test import RequestFactory

from opus_app.apps.cart.views import (
    api_cart_status,
    api_create_download,
    api_edit_cart,
    api_get_cart_csv,
    api_reset_session,
    api_view_cart,
)

from ._broken_requests import request_without_get, request_without_meta


class CartTests(TestCase):
    """The cart views, called directly with a request they cannot use."""

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


            ############################################
            ######### api_view_cart UNIT TESTS #########
            ############################################

    def test__api_view_cart_no_meta(self) -> None:
        "[test_cart.py] api_view_cart: no META"
        request = request_without_meta(self.factory, 'dummy')
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /__cart/view.html'):
            api_view_cart(request)

    def test__api_view_cart_no_get(self) -> None:
        "[test_cart.py] api_view_cart: no GET"
        request = request_without_get(self.factory, '/__cart/view.html')
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /__cart/view.html'):
            api_view_cart(request)


            ##############################################
            ######### api_cart_status UNIT TESTS #########
            ##############################################

    def test__api_cart_status_no_meta(self) -> None:
        "[test_cart.py] api_cart_status: no META"
        request = request_without_meta(self.factory, 'dummy')
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /__cart/status.json'):
            api_cart_status(request)

    def test__api_cart_status_no_get(self) -> None:
        "[test_cart.py] api_cart_status: no GET"
        request = request_without_get(self.factory, '/__cart/status.json')
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /__cart/status.json'):
            api_cart_status(request)


            ###############################################
            ######### api_get_cart_csv UNIT TESTS #########
            ###############################################

    def test__api_get_cart_csv_no_meta(self) -> None:
        "[test_cart.py] api_get_cart_csv: no META"
        request = request_without_meta(self.factory, 'dummy')
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /__cart/data.csv'):
            api_get_cart_csv(request)

    def test__api_get_cart_csv_no_get(self) -> None:
        "[test_cart.py] api_get_cart_csv: no GET"
        request = request_without_get(self.factory, '/__cart/data.csv')
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /__cart/data.csv'):
            api_get_cart_csv(request)


            ############################################
            ######### api_edit_cart UNIT TESTS #########
            ############################################

    def test__api_edit_cart_no_meta(self) -> None:
        "[test_cart.py] api_edit_cart: no META"
        request = request_without_meta(self.factory, 'dummy')
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /__cart/add.json'):
            api_edit_cart(request, 'add')

    def test__api_edit_cart_no_get(self) -> None:
        "[test_cart.py] api_edit_cart: no GET"
        request = request_without_get(self.factory, '/__cart/add.json')
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /__cart/add.json'):
            api_edit_cart(request, 'add')


            ################################################
            ######### api_reset_session UNIT TESTS #########
            ################################################

    def test__api_reset_session_no_meta(self) -> None:
        "[test_cart.py] api_reset_session: no META"
        request = request_without_meta(self.factory, 'dummy')
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /__cart/reset.json'):
            api_reset_session(request)

    def test__api_reset_session_no_get(self) -> None:
        "[test_cart.py] api_reset_session: no GET"
        request = request_without_get(self.factory, '/__cart/reset.json')
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /__cart/reset.json'):
            api_reset_session(request)


            ##################################################
            ######### api_create_download UNIT TESTS #########
            ##################################################

    def test__api_create_download_no_meta(self) -> None:
        "[test_cart.py] api_create_download: no META"
        request = request_without_meta(self.factory, 'dummy')
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /__cart/download.json'):
            api_create_download(request)

    def test__api_create_download_no_get(self) -> None:
        "[test_cart.py] api_create_download: no GET"
        request = request_without_get(self.factory, '/__cart/download.json')
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /__cart/download.json'):
            api_create_download(request)

    def test__api_create_download_opusid_no_get(self) -> None:
        "[test_cart.py] api_create_download: no GET"
        request = request_without_get(self.factory, '/api/download/testopusid.zip')
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /api/download/testopusid.zip'):
            api_create_download(request, 'testopusid', 'zip')
