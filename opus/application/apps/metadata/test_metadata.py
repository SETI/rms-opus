# metadata/test_metadata.py

import logging
from unittest import TestCase

from django.core.cache import cache
from django.http import Http404
from django.test import RequestFactory

from metadata.views import (api_get_fields,
                            api_get_mult_counts,
                            api_get_mult_counts_internal,
                            api_get_result_count_internal,
                            api_get_range_endpoints,
                            api_get_range_endpoints_internal,
                            api_get_result_count)

import settings

class MetadataTests(TestCase):

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


            ###################################################
            ######### api_get_result_count UNIT TESTS #########
            ###################################################

    def test__api_get_result_count_no_request(self):
        "[test_metadata.py] api_get_result_count: no request"
        no_request = self.factory.get('dummy')
        no_request.META = None
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /api/meta/result_count.json'):
            api_get_result_count(no_request, 'json')

    def test__api_get_result_count_no_get(self):
        "[test_metadata.py] api_get_result_count: no GET"
        request = self.factory.get('/api/meta/result_count.json')
        request.GET = None
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /api/meta/result_count.json'):
            api_get_result_count(request, 'json')

    def test__api_get_result_count_bad_fmt(self):
        "[test_metadata.py] api_get_result_count: bad fmt"
        request = self.factory.get('/api/meta/result_count.json')
        with self.assertRaisesRegex(Http404,
            r'Internal error \(Unknown return format "jsonx"\) for /api/meta/result_count.json'):
            api_get_result_count(request, 'jsonx')

    def test__api_get_result_count_no_request_internal(self):
        "[test_metadata.py] api_get_result_count: no request internal"
        no_request = self.factory.get('dummy')
        no_request.META = None
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /api/meta/result_count.json'):
            api_get_result_count_internal(no_request)

    def test__api_get_result_count_no_get_internal(self):
        "[test_metadata.py] api_get_result_count: no GET internal"
        request = self.factory.get('/__api/meta/result_count.json')
        request.GET = None
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /api/meta/result_count.json'):
            api_get_result_count_internal(request)


            ##################################################
            ######### api_get_mult_counts UNIT TESTS #########
            ##################################################

    def test__api_get_mult_counts_no_request(self):
        "[test_metadata.py] api_get_mult_counts: no request"
        no_request = self.factory.get('dummy')
        no_request.META = None
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /api/meta/mults/target.json'):
            api_get_mult_counts(no_request, 'target', 'json')

    def test__api_get_mult_counts_no_get(self):
        "[test_metadata.py] api_get_mult_counts: no GET"
        request = self.factory.get('/api/meta/mults/target.json')
        request.GET = None
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /api/meta/mults/target.json'):
            api_get_mult_counts(request, 'target', 'json')

    def test__api_get_mult_counts_bad_fmt(self):
        "[test_metadata.py] api_get_mult_counts: bad fmt"
        request = self.factory.get('/api/meta/mults/target.json')
        with self.assertRaisesRegex(Http404,
            r'Internal error \(Unknown return format "jsonx"\) for /api/meta/mults/target.json'):
            api_get_mult_counts(request, 'target', 'jsonx')

    def test__api_get_mult_counts_no_request_internal(self):
        "[test_metadata.py] api_get_mult_counts: no request internal"
        no_request = self.factory.get('dummy')
        no_request.META = None
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /api/meta/mults/target.json'):
            api_get_mult_counts_internal(no_request, 'target')

    def test__api_get_mult_counts_no_get_internal(self):
        "[test_metadata.py] api_get_mult_counts: no GET internal"
        request = self.factory.get('/__api/meta/mults/target.json')
        request.GET = None
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /api/meta/mults/target.json'):
            api_get_mult_counts_internal(request, 'target')


            ######################################################
            ######### api_get_range_endpoints UNIT TESTS #########
            ######################################################

    def test__api_get_range_endpoints_no_request(self):
        "[test_metadata.py] api_get_range_endpoints: no request"
        no_request = self.factory.get('dummy')
        no_request.META = None
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /api/meta/range/endpoints/observationduration.json'):
            api_get_range_endpoints(no_request, 'observationduration', 'json')

    def test__api_get_range_endpoints_no_get(self):
        "[test_metadata.py] api_get_range_endpoints: no GET"
        request = self.factory.get('/api/meta/range/endpoints/observationduration.json')
        request.GET = None
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /api/meta/range/endpoints/observationduration.json'):
            api_get_range_endpoints(request, 'observationduration', 'json')

    def test__api_get_range_endpoints_bad_fmt(self):
        "[test_metadata.py] api_get_range_endpoints: bad fmt"
        request = self.factory.get('/api/meta/range/endpoints/observationduration.json')
        with self.assertRaisesRegex(Http404,
            r'Internal error \(Unknown return format "jsonx"\) for /api/meta/range/endpoints/observationduration.json'):
            api_get_range_endpoints(request, 'observationduration', 'jsonx')

    def test__api_get_range_endpoints_no_request_internal(self):
        "[test_metadata.py] api_get_range_endpoints: no request internal"
        no_request = self.factory.get('dummy')
        no_request.META = None
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /api/meta/range/endpoints/observationduration.json'):
            api_get_range_endpoints_internal(no_request, 'observationduration')

    def test__api_get_range_endpoints_no_get_internal(self):
        "[test_metadata.py] api_get_range_endpoints: no GET internal"
        request = self.factory.get('/__api/meta/range/endpoints/observationduration.json')
        request.GET = None
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /api/meta/range/endpoints/observationduration.json'):
            api_get_range_endpoints_internal(request, 'observationduration')


            #############################################
            ######### api_get_fields UNIT TESTS #########
            #############################################

    def test__api_get_fields_no_request(self):
        "[test_metadata.py] api_get_fields: no request"
        no_request = self.factory.get('dummy')
        no_request.META = None
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /api/fields/None.json'):
            api_get_fields(no_request, 'json')

    def test__api_get_fields_no_get(self):
        "[test_metadata.py] api_get_fields: no GET"
        request = self.factory.get('/api/fields/rightasc1.json')
        request.GET = None
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /api/fields/None.json'):
            api_get_fields(request, 'json')
