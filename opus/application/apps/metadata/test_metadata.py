# metadata/test_metadata.py

import logging
import sys
from unittest import TestCase

from django.core.cache import cache
from django.http import Http404
from django.test import RequestFactory
from django.test.client import Client

from metadata.views import *

class MetadataTests(TestCase):

    def setUp(self):
        self.maxDiff = None
        logging.disable(logging.ERROR)
        cache.clear()
        self.factory = RequestFactory()

    def tearDown(self):
        logging.disable(logging.NOTSET)


            ###################################################
            ######### api_get_result_count UNIT TESTS #########
            ###################################################

    def test__api_get_result_count_no_request(self):
        "[test_metadata.py] api_get_result_count: no request"
        with self.assertRaises(Http404):
            api_get_result_count(None, 'json')

    def test__api_get_result_count_no_get(self):
        "[test_metadata.py] api_get_result_count: no GET"
        c = Client()
        request = self.factory.get('/api/meta/result_count.json')
        request.GET = None
        with self.assertRaises(Http404):
            api_get_result_count(request, 'json')

    def test__api_get_result_count_bad_fmt(self):
        "[test_metadata.py] api_get_result_count: bad fmt"
        c = Client()
        request = self.factory.get('/api/meta/result_count.json')
        with self.assertRaises(Http404):
            api_get_result_count(request, 'jsonx')

    def test__api_get_result_count_no_request_internal(self):
        "[test_metadata.py] api_get_result_count: no request internal"
        with self.assertRaises(Http404):
            api_get_result_count_internal(None)

    def test__api_get_result_count_no_get_internal(self):
        "[test_metadata.py] api_get_result_count: no GET internal"
        c = Client()
        request = self.factory.get('/__api/meta/result_count.json')
        request.GET = None
        with self.assertRaises(Http404):
            api_get_result_count_internal(request)


            ##################################################
            ######### api_get_mult_counts UNIT TESTS #########
            ##################################################

    def test__api_get_mult_counts_no_request(self):
        "[test_metadata.py] api_get_mult_counts: no request"
        with self.assertRaises(Http404):
            api_get_mult_counts(None, 'target', 'json')

    def test__api_get_mult_counts_no_get(self):
        "[test_metadata.py] api_get_mult_counts: no GET"
        c = Client()
        request = self.factory.get('/api/meta/mult_counts.json')
        request.GET = None
        with self.assertRaises(Http404):
            api_get_mult_counts(request, 'target', 'json')

    def test__api_get_mult_counts_bad_fmt(self):
        "[test_metadata.py] api_get_mult_counts: bad fmt"
        c = Client()
        request = self.factory.get('/api/meta/mult_counts.json')
        with self.assertRaises(Http404):
            api_get_mult_counts(request, 'target', 'jsonx')

    def test__api_get_mult_counts_no_request_internal(self):
        "[test_metadata.py] api_get_mult_counts: no request internal"
        with self.assertRaises(Http404):
            api_get_mult_counts_internal(None, 'target')

    def test__api_get_mult_counts_no_get_internal(self):
        "[test_metadata.py] api_get_mult_counts: no GET internal"
        c = Client()
        request = self.factory.get('/__api/meta/mult_counts.json')
        request.GET = None
        with self.assertRaises(Http404):
            api_get_mult_counts_internal(request, 'target')


            ######################################################
            ######### api_get_range_endpoints UNIT TESTS #########
            ######################################################

    def test__api_get_range_endpoints_no_request(self):
        "[test_metadata.py] api_get_range_endpoints: no request"
        with self.assertRaises(Http404):
            api_get_range_endpoints(None, 'observationduration', 'json')

    def test__api_get_range_endpoints_no_get(self):
        "[test_metadata.py] api_get_range_endpoints: no GET"
        c = Client()
        request = self.factory.get('/api/meta/range/endpoints/observationduration.json')
        request.GET = None
        with self.assertRaises(Http404):
            api_get_range_endpoints(request, 'observationduration', 'json')

    def test__api_get_range_endpoints_bad_fmt(self):
        "[test_metadata.py] api_get_range_endpoints: bad fmt"
        c = Client()
        request = self.factory.get('/api/meta/range/endpoints/observationduration.json')
        with self.assertRaises(Http404):
            api_get_range_endpoints(request, 'observationduration', 'jsonx')

    def test__api_get_range_endpoints_no_request_internal(self):
        "[test_metadata.py] api_get_range_endpoints: no request internal"
        with self.assertRaises(Http404):
            api_get_range_endpoints_internal(None, 'observationduration')

    def test__api_get_range_endpoints_no_get_internal(self):
        "[test_metadata.py] api_get_range_endpoints: no GET internal"
        c = Client()
        request = self.factory.get('/__api/meta/range/endpoints/observationduration.json')
        request.GET = None
        with self.assertRaises(Http404):
            api_get_range_endpoints_internal(request, 'observationduration')


            #############################################
            ######### api_get_fields UNIT TESTS #########
            #############################################

    def test__api_get_fields_no_request(self):
        "[test_metadata.py] api_get_fields: no request"
        with self.assertRaises(Http404):
            api_get_fields(None)

    def test__api_get_fields_no_get(self):
        "[test_metadata.py] api_get_fields: no GET"
        c = Client()
        request = self.factory.get('/api/fields/rightasc1.json')
        request.GET = None
        with self.assertRaises(Http404):
            api_get_fields(request)
