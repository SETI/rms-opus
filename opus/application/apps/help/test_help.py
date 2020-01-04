# help/test_help.py

import logging
import sys
from unittest import TestCase

from django.core.cache import cache
from django.http import Http404
from django.test import RequestFactory
from django.test.client import Client

from help.views import *

class helpTests(TestCase):

    def setUp(self):
        self.maxDiff = None
        logging.disable(logging.ERROR)
        cache.clear()
        self.factory = RequestFactory()

    def tearDown(self):
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
        request = self.factory.get('__help/about.html')
        request.GET = None
        with self.assertRaises(Http404):
            api_about(request)


            ##########################################
            ######### api_volumes UNIT TESTS #########
            ##########################################

    def test__api_volumes_no_request(self):
        "[test_help.py] api_volumes: no request"
        with self.assertRaises(Http404):
            api_volumes(None)

    def test__api_volumes_no_get(self):
        "[test_help.py] api_volumes: no GET"
        c = Client()
        request = self.factory.get('__help/volumes.html')
        request.GET = None
        with self.assertRaises(Http404):
            api_volumes(request)


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
        request = self.factory.get('__help/faq.html')
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
        request = self.factory.get('__help/guide.html')
        request.GET = None
        with self.assertRaises(Http404):
            api_guide(request)


            #################################################
            ######### api_gettingstarted UNIT TESTS #########
            #################################################

    def test__api_gettingstarted_no_request(self):
        "[test_help.py] api_gettingstarted: no request"
        with self.assertRaises(Http404):
            api_gettingstarted(None)

    def test__api_gettingstarted_no_get(self):
        "[test_help.py] api_gettingstarted: no GET"
        c = Client()
        request = self.factory.get('__help/gettingstarted.html')
        request.GET = None
        with self.assertRaises(Http404):
            api_gettingstarted(request)


            #########################################
            ######### api_splash UNIT TESTS #########
            #########################################

    def test__api_splash_no_request(self):
        "[test_help.py] api_splash: no request"
        with self.assertRaises(Http404):
            api_splash(None)

    def test__api_splash_no_get(self):
        "[test_help.py] api_splash: no GET"
        c = Client()
        request = self.factory.get('__help/splash.html')
        request.GET = None
        with self.assertRaises(Http404):
            api_splash(request)


            ##############################################
            ######### api_citing_opus UNIT TESTS #########
            ##############################################

    def test__api_citing_opus_no_request(self):
        "[test_help.py] api_citing_opus: no request"
        with self.assertRaises(Http404):
            api_citing_opus(None)

    def test__api_citing_opus_no_get(self):
        "[test_help.py] api_citing_opus: no GET"
        c = Client()
        request = self.factory.get('__help/citing.html')
        request.GET = None
        with self.assertRaises(Http404):
            api_citing_opus(request)
