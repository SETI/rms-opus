# help/test_help.py

import logging
from unittest import TestCase

from django.core.cache import cache
from django.http import Http404
from django.test import RequestFactory

from help.views import (api_about,
                        api_bundles,
                        api_citing_opus,
                        api_api_guide,
                        api_faq,
                        api_gettingstarted,
                        api_splash)

import settings

class helpTests(TestCase):

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


            ########################################
            ######### api_about UNIT TESTS #########
            ########################################

    def test__api_about_no_meta(self):
        "[test_help.py] api_about: no META"
        request = self.factory.get('dummy')
        request.META = None
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /__help/about.html'):
            api_about(request, 'html')

    def test__api_about_no_get(self):
        "[test_help.py] api_about: no GET"
        request = self.factory.get('__help/about.html')
        request.GET = None
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /__help/about.html'):
            api_about(request, 'html')


            ##########################################
            ######### api_bundles UNIT TESTS #########
            ##########################################

    def test__api_bundles_no_meta(self):
        "[test_help.py] api_bundles: no META"
        request = self.factory.get('dummy')
        request.META = None
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /__help/bundles.html'):
            api_bundles(request, 'html')

    def test__api_bundles_no_get(self):
        "[test_help.py] api_bundles: no GET"
        request = self.factory.get('__help/bundles.html')
        request.GET = None
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /__help/bundles.html'):
            api_bundles(request, 'html')


            ######################################
            ######### api_faq UNIT TESTS #########
            ######################################

    def test__api_faq_no_meta(self):
        "[test_help.py] api_faq: no META"
        request = self.factory.get('dummy')
        request.META = None
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /__help/faq.html'):
            api_faq(request, 'html')

    def test__api_faq_no_get(self):
        "[test_help.py] api_faq: no GET"
        request = self.factory.get('__help/faq.html')
        request.GET = None
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /__help/faq.html'):
            api_faq(request, 'html')


            ########################################
            ######### api_guide UNIT TESTS #########
            ########################################

    def test__api_api_guide_no_meta(self):
        "[test_help.py] api_api_guide: no META"
        request = self.factory.get('dummy')
        request.META = None
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /__help/apiguide.html'):
            api_api_guide(request, 'html')

    def test__api_api_guide_no_get(self):
        "[test_help.py] api_api_guide: no GET"
        request = self.factory.get('__help/apiguide.html')
        request.GET = None
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /__help/apiguide.html'):
            api_api_guide(request, 'html')


            #################################################
            ######### api_gettingstarted UNIT TESTS #########
            #################################################

    def test__api_gettingstarted_no_meta(self):
        "[test_help.py] api_gettingstarted: no META"
        request = self.factory.get('dummy')
        request.META = None
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /__help/gettingstarted.html'):
            api_gettingstarted(request, 'html')

    def test__api_gettingstarted_no_get(self):
        "[test_help.py] api_gettingstarted: no GET"
        request = self.factory.get('__help/gettingstarted.html')
        request.GET = None
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /__help/gettingstarted.html'):
            api_gettingstarted(request, 'html')


            #########################################
            ######### api_splash UNIT TESTS #########
            #########################################

    def test__api_splash_no_meta(self):
        "[test_help.py] api_splash: no META"
        request = self.factory.get('dummy')
        request.META = None
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /__help/splash.html'):
            api_splash(request)

    def test__api_splash_no_get(self):
        "[test_help.py] api_splash: no GET"
        request = self.factory.get('__help/splash.html')
        request.GET = None
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /__help/splash.html'):
            api_splash(request)


            ##############################################
            ######### api_citing_opus UNIT TESTS #########
            ##############################################

    def test__api_citing_opus_no_meta(self):
        "[test_help.py] api_citing_opus: no META"
        request = self.factory.get('dummy')
        request.META = None
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /__help/citing.html'):
            api_citing_opus(request, 'html')

    def test__api_citing_opus_no_get(self):
        "[test_help.py] api_citing_opus: no GET"
        request = self.factory.get('__help/citing.html')
        request.GET = None
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /__help/citing.html'):
            api_citing_opus(request, 'html')
