# cart/test_cart.py

import logging
import sys
from unittest import TestCase

from django.core.cache import cache
from django.http import Http404
from django.test import RequestFactory
from django.test.client import Client

from cart.views import *

class cartTests(TestCase):

    def setUp(self):
        self.maxDiff = None
        settings.OPUS_FAKE_API_DELAYS = 0
        settings.OPUS_FAKE_SERVER_ERROR404_PROBABILITY = 0
        settings.OPUS_FAKE_SERVER_ERROR500_PROBABILITY = 0
        logging.disable(logging.ERROR)
        cache.clear()
        self.factory = RequestFactory()

    def tearDown(self):
        logging.disable(logging.NOTSET)


            ############################################
            ######### api_view_cart UNIT TESTS #########
            ############################################

    def test__api_view_cart_no_request(self):
        "[test_cart.py] api_view_cart: no request"
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /__cart/view.html'):
            api_view_cart(None)

    def test__api_view_cart_no_get(self):
        "[test_cart.py] api_view_cart: no GET"
        c = Client()
        request = self.factory.get('/__cart/view.html')
        request.GET = None
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /__cart/view.html'):
            api_view_cart(request)


            ##############################################
            ######### api_cart_status UNIT TESTS #########
            ##############################################

    def test__api_cart_status_no_request(self):
        "[test_cart.py] api_cart_status: no request"
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /__cart/status.json'):
            api_cart_status(None)

    def test__api_cart_status_no_get(self):
        "[test_cart.py] api_cart_status: no GET"
        c = Client()
        request = self.factory.get('/__cart/status.json')
        request.GET = None
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /__cart/status.json'):
            api_cart_status(request)


            ###############################################
            ######### api_get_cart_csv UNIT TESTS #########
            ###############################################

    def test__api_get_cart_csv_no_request(self):
        "[test_cart.py] api_get_cart_csv: no request"
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /__cart/data.csv'):
            api_get_cart_csv(None)

    def test__api_get_cart_csv_no_get(self):
        "[test_cart.py] api_get_cart_csv: no GET"
        c = Client()
        request = self.factory.get('/__cart/data.csv')
        request.GET = None
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /__cart/data.csv'):
            api_get_cart_csv(request)


            ############################################
            ######### api_edit_cart UNIT TESTS #########
            ############################################

    def test__api_edit_cart_no_request(self):
        "[test_cart.py] api_edit_cart: no request"
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /__cart/add.json'):
            api_edit_cart(None, 'add')

    def test__api_edit_cart_no_get(self):
        "[test_cart.py] api_edit_cart: no GET"
        c = Client()
        request = self.factory.get('/__cart/add.json')
        request.GET = None
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /__cart/add.json'):
            api_edit_cart(request, 'add')


            ################################################
            ######### api_reset_session UNIT TESTS #########
            ################################################

    def test__api_reset_session_no_request(self):
        "[test_cart.py] api_reset_session: no request"
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /__cart/reset.json'):
            api_reset_session(None)

    def test__api_reset_session_no_get(self):
        "[test_cart.py] api_reset_session: no GET"
        c = Client()
        request = self.factory.get('/__cart/reset.json')
        request.GET = None
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /__cart/reset.json'):
            api_reset_session(request)


            ##################################################
            ######### api_create_download UNIT TESTS #########
            ##################################################

    def test__api_create_download_no_request(self):
        "[test_cart.py] api_create_download: no request"
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /__cart/download.json'):
            api_create_download(None)

    def test__api_create_download_no_get(self):
        "[test_cart.py] api_create_download: no GET"
        c = Client()
        request = self.factory.get('/__cart/download.json')
        request.GET = None
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /__cart/download.json'):
            api_create_download(request)

    def test__api_create_download_opusid_no_get(self):
        "[test_cart.py] api_create_download: no GET"
        c = Client()
        request = self.factory.get('/api/download/testopusid.zip')
        request.GET = None
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /api/download/testopusid.zip'):
            api_create_download(request, 'testopusid')
