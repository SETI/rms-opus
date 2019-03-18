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
        sys.tracebacklimit = 0 # default: 1000
        logging.disable(logging.ERROR)
        cache.clear()
        self.factory = RequestFactory()
        
    def tearDown(self):
        sys.tracebacklimit = 1000 # default: 1000
        logging.disable(logging.NOTSET)


            ############################################
            ######### api_view_cart UNIT TESTS #########
            ############################################

    def test__api_view_cart_no_request(self):
        "[test_cart.py] api_view_cart: no request"
        with self.assertRaises(Http404):
            api_view_cart(None)

    def test__api_view_cart_no_get(self):
        "[test_cart.py] api_view_cart: no GET"
        c = Client()
        request = self.factory.get('/__cart/view.html')
        request.GET = None
        with self.assertRaises(Http404):
            api_view_cart(request)


            ##############################################
            ######### api_cart_status UNIT TESTS #########
            ##############################################

    def test__api_cart_status_no_request(self):
        "[test_cart.py] api_cart_status: no request"
        with self.assertRaises(Http404):
            api_cart_status(None)

    def test__api_cart_status_no_get(self):
        "[test_cart.py] api_cart_status: no GET"
        c = Client()
        request = self.factory.get('/__cart/status.json')
        request.GET = None
        with self.assertRaises(Http404):
            api_cart_status(request)


            ###############################################
            ######### api_get_cart_csv UNIT TESTS #########
            ###############################################

    def test__api_get_cart_csv_no_request(self):
        "[test_cart.py] api_get_cart_csv: no request"
        with self.assertRaises(Http404):
            api_get_cart_csv(None)

    def test__api_get_cart_csv_no_get(self):
        "[test_cart.py] api_get_cart_csv: no GET"
        c = Client()
        request = self.factory.get('/__cart/data.csv')
        request.GET = None
        with self.assertRaises(Http404):
            api_get_cart_csv(request)


            ############################################
            ######### api_edit_cart UNIT TESTS #########
            ############################################

    def test__api_edit_cart_no_request(self):
        "[test_cart.py] api_edit_cart: no request"
        with self.assertRaises(Http404):
            api_edit_cart(None)

    def test__api_edit_cart_no_get(self):
        "[test_cart.py] api_edit_cart: no GET"
        c = Client()
        request = self.factory.get('/__cart/add.json')
        request.GET = None
        with self.assertRaises(Http404):
            api_edit_cart(request)


            ################################################
            ######### api_reset_session UNIT TESTS #########
            ################################################

    def test__api_reset_session_no_request(self):
        "[test_cart.py] api_reset_session: no request"
        with self.assertRaises(Http404):
            api_reset_session(None)

    def test__api_reset_session_no_get(self):
        "[test_cart.py] api_reset_session: no GET"
        c = Client()
        request = self.factory.get('/__cart/reset.json')
        request.GET = None
        with self.assertRaises(Http404):
            api_reset_session(request)


            ##################################################
            ######### api_create_download UNIT TESTS #########
            ##################################################

    def test__api_create_download_no_request(self):
        "[test_cart.py] api_create_download: no request"
        with self.assertRaises(Http404):
            api_create_download(None)

    def test__api_create_download_no_get(self):
        "[test_cart.py] api_create_download: no GET"
        c = Client()
        request = self.factory.get('/__cart/download.json')
        request.GET = None
        with self.assertRaises(Http404):
            api_create_download(request)
