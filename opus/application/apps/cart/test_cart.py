# cart/test_cart.py

import logging
import sys
from unittest import TestCase

import django.conf
from django.http import Http404
from django.test.client import Client

from cart.views import *

django.conf.settings.CACHE_BACKEND = 'dummy:///'

class cartTests(TestCase):

    def setUp(self):
        self.maxDiff = None
        sys.tracebacklimit = 0 # default: 1000
        logging.disable(logging.ERROR)

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
        response = c.get('/__cart/view.html')
        request = response.wsgi_request
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
        response = c.get('/__cart/status.json')
        request = response.wsgi_request
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
        response = c.get('/__cart/data.csv')
        request = response.wsgi_request
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
        response = c.get('/__cart/add.json')
        request = response.wsgi_request
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
        response = c.get('/__cart/reset.json')
        request = response.wsgi_request
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
        response = c.get('/__cart/download.json')
        request = response.wsgi_request
        request.GET = None
        with self.assertRaises(Http404):
            api_create_download(request)
