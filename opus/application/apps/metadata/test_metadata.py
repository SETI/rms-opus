# metadata/test_metadata.py

import json
import sys
from unittest import TestCase

from django.conf import settings
from django.http import Http404
from django.test.client import Client
from metadata.views import *

import logging

settings.CACHE_BACKEND = 'dummy:///'

class MetadataTests(TestCase):
    # disable error logging and trace output before test
    def setUp(self):
        logging.disable(logging.ERROR)

    # enable error logging and trace output after test
    def tearDown(self):
        logging.disable(logging.NOTSET)


            ###################################################
            ######### api_get_result_count UNIT TESTS #########
            ###################################################

    def test__api_get_result_count_no_request(self):
        "api_get_result_count: no request"
        with self.assertRaises(Http404):
            api_get_result_count(None, 'json')

    def test__api_get_result_count_no_get(self):
        "api_get_result_count: no GET"
        c = Client()
        response = c.get('/api/meta/result_count.json')
        request = response.wsgi_request
        request.GET = None
        with self.assertRaises(Http404):
            api_get_result_count(request, 'json')

    def test__api_get_result_count_bad_fmt(self):
        "api_get_result_count: bad fmt"
        c = Client()
        response = c.get('/api/meta/result_count.json')
        request = response.wsgi_request
        with self.assertRaises(Http404):
            api_get_result_count(request, 'jsonx')

    def test__api_get_result_count_no_request_internal(self):
        "api_get_result_count: no request internal"
        with self.assertRaises(Http404):
            api_get_result_count_internal(None)

    def test__api_get_result_count_no_get_internal(self):
        "api_get_result_count: no GET internal"
        c = Client()
        response = c.get('/__api/meta/result_count.json')
        request = response.wsgi_request
        request.GET = None
        with self.assertRaises(Http404):
            api_get_result_count_internal(request)


            ##################################################
            ######### api_get_mult_counts UNIT TESTS #########
            ##################################################

    def test__api_get_mult_counts_no_request(self):
        "api_get_mult_counts: no request"
        with self.assertRaises(Http404):
            api_get_mult_counts(None, 'target', 'json')

    def test__api_get_mult_counts_no_get(self):
        "api_get_mult_counts: no GET"
        c = Client()
        response = c.get('/api/meta/mult_counts.json')
        request = response.wsgi_request
        request.GET = None
        with self.assertRaises(Http404):
            api_get_mult_counts(request, 'target', 'json')

    def test__api_get_mult_counts_bad_fmt(self):
        "api_get_mult_counts: bad fmt"
        c = Client()
        response = c.get('/api/meta/mult_counts.json')
        request = response.wsgi_request
        with self.assertRaises(Http404):
            api_get_mult_counts(request, 'target', 'jsonx')

    def test__api_get_mult_counts_no_request_internal(self):
        "api_get_mult_counts: no request internal"
        with self.assertRaises(Http404):
            api_get_mult_counts_internal(None, 'target')

    def test__api_get_mult_counts_no_get_internal(self):
        "api_get_mult_counts: no GET internal"
        c = Client()
        response = c.get('/__api/meta/mult_counts.json')
        request = response.wsgi_request
        request.GET = None
        with self.assertRaises(Http404):
            api_get_mult_counts_internal(request, 'target')


            ######################################################
            ######### api_get_range_endpoints UNIT TESTS #########
            ######################################################

    def test__api_get_range_endpoints_no_request(self):
        "api_get_range_endpoints: no request"
        with self.assertRaises(Http404):
            api_get_range_endpoints(None, 'observationduration', 'json')

    def test__api_get_range_endpoints_no_get(self):
        "api_get_range_endpoints: no GET"
        c = Client()
        response = c.get('/api/meta/range/endpoints/observationduration.json')
        request = response.wsgi_request
        request.GET = None
        with self.assertRaises(Http404):
            api_get_range_endpoints(request, 'observationduration', 'json')

    def test__api_get_range_endpoints_bad_fmt(self):
        "api_get_range_endpoints: bad fmt"
        c = Client()
        response = c.get('/api/meta/range/endpoints/observationduration.json')
        request = response.wsgi_request
        with self.assertRaises(Http404):
            api_get_range_endpoints(request, 'observationduration', 'jsonx')

    def test__api_get_range_endpoints_no_request_internal(self):
        "api_get_range_endpoints: no request internal"
        with self.assertRaises(Http404):
            api_get_range_endpoints_internal(None, 'observationduration')

    def test__api_get_range_endpoints_no_get_internal(self):
        "api_get_range_endpoints: no GET internal"
        c = Client()
        response = c.get('/__api/meta/range/endpoints/observationduration.json')
        request = response.wsgi_request
        request.GET = None
        with self.assertRaises(Http404):
            api_get_range_endpoints_internal(request, 'observationduration')
