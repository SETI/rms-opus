"""Tests for the metadata views: bad requests, and the mult and range endpoints."""

import logging
from unittest import TestCase

from django.conf import settings
from django.core.cache import cache
from django.http import Http404
from django.test import RequestFactory

from opus_app.apps.metadata.views import (
    api_get_fields,
    api_get_mult_counts,
    api_get_mult_counts_internal,
    api_get_range_endpoints,
    api_get_range_endpoints_internal,
    api_get_result_count,
    api_get_result_count_internal,
)

from ._broken_requests import request_without_get, request_without_meta


class MetadataTests(TestCase):
    """The metadata views: their guards, their mults and their range endpoints."""

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


            ###################################################
            ######### api_get_result_count UNIT TESTS #########
            ###################################################

    def test__api_get_result_count_no_meta(self) -> None:
        "[test_metadata.py] api_get_result_count: no META"
        request = request_without_meta(self.factory, 'dummy')
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /api/meta/result_count.json'):
            api_get_result_count(request, 'json')

    def test__api_get_result_count_no_get(self) -> None:
        "[test_metadata.py] api_get_result_count: no GET"
        request = request_without_get(self.factory, '/api/meta/result_count.json')
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /api/meta/result_count.json'):
            api_get_result_count(request, 'json')

    def test__api_get_result_count_bad_fmt(self) -> None:
        "[test_metadata.py] api_get_result_count: bad fmt"
        request = self.factory.get('/api/meta/result_count.json')
        with self.assertRaisesRegex(Http404,
            r'Internal error \(Unknown return format "jsonx"\) for /api/meta/result_count.json'):
            api_get_result_count(request, 'jsonx')

    def test__api_get_result_count_no_meta_internal(self) -> None:
        "[test_metadata.py] api_get_result_count: no META internal"
        request = request_without_meta(self.factory, 'dummy')
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /api/meta/result_count.json'):
            api_get_result_count_internal(request)

    def test__api_get_result_count_no_get_internal(self) -> None:
        "[test_metadata.py] api_get_result_count: no GET internal"
        request = request_without_get(self.factory, '/__api/meta/result_count.json')
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /api/meta/result_count.json'):
            api_get_result_count_internal(request)


            ##################################################
            ######### api_get_mult_counts UNIT TESTS #########
            ##################################################

    def test__api_get_mult_counts_no_meta(self) -> None:
        "[test_metadata.py] api_get_mult_counts: no META"
        request = request_without_meta(self.factory, 'dummy')
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /api/meta/mults/target.json'):
            api_get_mult_counts(request, 'target', 'json')

    def test__api_get_mult_counts_no_get(self) -> None:
        "[test_metadata.py] api_get_mult_counts: no GET"
        request = request_without_get(self.factory, '/api/meta/mults/target.json')
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /api/meta/mults/target.json'):
            api_get_mult_counts(request, 'target', 'json')

    def test__api_get_mult_counts_bad_fmt(self) -> None:
        "[test_metadata.py] api_get_mult_counts: bad fmt"
        request = self.factory.get('/api/meta/mults/target.json')
        with self.assertRaisesRegex(Http404,
            r'Internal error \(Unknown return format "jsonx"\) for /api/meta/mults/target.json'):
            api_get_mult_counts(request, 'target', 'jsonx')

    def test__api_get_mult_counts_no_meta_internal(self) -> None:
        "[test_metadata.py] api_get_mult_counts: no META internal"
        request = request_without_meta(self.factory, 'dummy')
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /api/meta/mults/target.json'):
            api_get_mult_counts_internal(request, 'target')

    def test__api_get_mult_counts_no_get_internal(self) -> None:
        "[test_metadata.py] api_get_mult_counts: no GET internal"
        request = request_without_get(self.factory, '/__api/meta/mults/target.json')
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /api/meta/mults/target.json'):
            api_get_mult_counts_internal(request, 'target')


            ######################################################
            ######### api_get_range_endpoints UNIT TESTS #########
            ######################################################

    def test__api_get_range_endpoints_no_meta(self) -> None:
        "[test_metadata.py] api_get_range_endpoints: no META"
        request = request_without_meta(self.factory, 'dummy')
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /api/meta/range/endpoints/observationduration.json'):
            api_get_range_endpoints(request, 'observationduration', 'json')

    def test__api_get_range_endpoints_no_get(self) -> None:
        "[test_metadata.py] api_get_range_endpoints: no GET"
        request = request_without_get(self.factory, '/api/meta/range/endpoints/observationduration.json')
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /api/meta/range/endpoints/observationduration.json'):
            api_get_range_endpoints(request, 'observationduration', 'json')

    def test__api_get_range_endpoints_bad_fmt(self) -> None:
        "[test_metadata.py] api_get_range_endpoints: bad fmt"
        request = self.factory.get('/api/meta/range/endpoints/observationduration.json')
        with self.assertRaisesRegex(Http404,
            r'Internal error \(Unknown return format "jsonx"\) for /api/meta/range/endpoints/observationduration.json'):
            api_get_range_endpoints(request, 'observationduration', 'jsonx')

    def test__api_get_range_endpoints_no_meta_internal(self) -> None:
        "[test_metadata.py] api_get_range_endpoints: no META internal"
        request = request_without_meta(self.factory, 'dummy')
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /api/meta/range/endpoints/observationduration.json'):
            api_get_range_endpoints_internal(request, 'observationduration')

    def test__api_get_range_endpoints_no_get_internal(self) -> None:
        "[test_metadata.py] api_get_range_endpoints: no GET internal"
        request = request_without_get(self.factory, '/__api/meta/range/endpoints/observationduration.json')
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /api/meta/range/endpoints/observationduration.json'):
            api_get_range_endpoints_internal(request, 'observationduration')


            #############################################
            ######### api_get_fields UNIT TESTS #########
            #############################################

    def test__api_get_fields_no_meta(self) -> None:
        "[test_metadata.py] api_get_fields: no META"
        request = request_without_meta(self.factory, 'dummy')
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /api/fields/None.json'):
            api_get_fields(request, 'json')

    def test__api_get_fields_no_get(self) -> None:
        "[test_metadata.py] api_get_fields: no GET"
        request = request_without_get(self.factory, '/api/fields/rightasc1.json')
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /api/fields/None.json'):
            api_get_fields(request, 'json')
