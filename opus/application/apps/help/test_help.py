# help/test_help.py

import logging
import sys
from unittest import TestCase

import django.conf
from django.http import Http404
from django.test.client import Client

from help.views import *

django.conf.settings.CACHE_BACKEND = 'dummy:///'

class helpTests(TestCase):

    def setUp(self):
        self.maxDiff = None
        sys.tracebacklimit = 0 # default: 1000
        logging.disable(logging.ERROR)

    def tearDown(self):
        sys.tracebacklimit = 1000 # default: 1000
        logging.disable(logging.NOTSET)


            ########################################
            ######### api_about UNIT TESTS #########
            ########################################

    def test__api_about_no_request(self):
        "[test_help.py] api_about: no request"
        with self.assertRaises(Http404):
            api_about(None)

    def test__api_about_no_get(self):
        "[test_help.py] api_about: no GET"
        c = Client()
        response = c.get('__help/about.html')
        request = response.wsgi_request
        request.GET = None
        with self.assertRaises(Http404):
            api_about(request)


            ###########################################
            ######### api_datasets UNIT TESTS #########
            ###########################################

    def test__api_datasets_no_request(self):
        "[test_help.py] api_datasets: no request"
        with self.assertRaises(Http404):
            api_datasets(None)

    def test__api_datasets_no_get(self):
        "[test_help.py] api_datasets: no GET"
        c = Client()
        response = c.get('__help/datasets.html')
        request = response.wsgi_request
        request.GET = None
        with self.assertRaises(Http404):
            api_datasets(request)


            ######################################
            ######### api_faq UNIT TESTS #########
            ######################################

    def test__api_faq_no_request(self):
        "[test_help.py] api_faq: no request"
        with self.assertRaises(Http404):
            api_faq(None)

    def test__api_faq_no_get(self):
        "[test_help.py] api_faq: no GET"
        c = Client()
        response = c.get('__help/faq.html')
        request = response.wsgi_request
        request.GET = None
        with self.assertRaises(Http404):
            api_faq(request)


            ########################################
            ######### api_guide UNIT TESTS #########
            ########################################

    def test__api_guide_no_request(self):
        "[test_help.py] api_guide: no request"
        with self.assertRaises(Http404):
            api_guide(None)

    def test__api_guide_no_get(self):
        "[test_help.py] api_guide: no GET"
        c = Client()
        response = c.get('__help/guide.html')
        request = response.wsgi_request
        request.GET = None
        with self.assertRaises(Http404):
            api_guide(request)


            ###########################################
            ######### api_tutorial UNIT TESTS #########
            ###########################################

    def test__api_tutorial_no_request(self):
        "[test_help.py] api_tutorial: no request"
        with self.assertRaises(Http404):
            api_tutorial(None)

    def test__api_tutorial_no_get(self):
        "[test_help.py] api_tutorial: no GET"
        c = Client()
        response = c.get('__help/tutorial.html')
        request = response.wsgi_request
        request.GET = None
        with self.assertRaises(Http404):
            api_tutorial(request)
