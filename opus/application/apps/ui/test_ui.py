# ui/test_ui.py

import logging
import sys
from unittest import TestCase

from django.core.cache import cache
from django.http import Http404
from django.test import RequestFactory

from ui.views import (api_last_blog_update,
                      api_normalize_url)

import settings

class uiTests(TestCase):

    def setUp(self):
        self.maxDiff = None
        sys.tracebacklimit = 0 # default: 1000
        settings.OPUS_FAKE_API_DELAYS = 0
        settings.OPUS_FAKE_SERVER_ERROR404_PROBABILITY = 0
        settings.OPUS_FAKE_SERVER_ERROR500_PROBABILITY = 0
        logging.disable(logging.ERROR)
        cache.clear()
        self.factory = RequestFactory()

    def tearDown(self):
        sys.tracebacklimit = 1000 # default: 1000
        logging.disable(logging.NOTSET)


            ###################################################
            ######### api_last_blog_update UNIT TESTS #########
            ###################################################

    def test__api_last_blog_update_no_request(self):
        "[test_ui.py] api_last_blog_update: no request"
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /__lastblogupdate.json'):
            api_last_blog_update(None)

    def test__api_last_blog_update_no_get(self):
        "[test_ui.py] api_last_blog_update: no GET"
        request = self.factory.get('__lastblogupdate.json')
        request.GET = None
        with self.assertRaises(Http404):
            api_last_blog_update(request)

    def test__api_last_blog_update_ok(self):
        "[test_ui.py] api_last_blog_update: normal"
        settings.OPUS_LAST_BLOG_UPDATE_FILE = 'test_api/data/lastblogupdate.txt'
        request = self.factory.get('__lastblogupdate.json')
        ret = api_last_blog_update(request)
        print(ret)
        self.assertEqual(ret.content, b'{"lastupdate": "2019-JAN-01"}')

    def test__api_last_blog_update_bad(self):
        "[test_ui.py] api_last_blog_update: missing"
        settings.OPUS_LAST_BLOG_UPDATE_FILE = 'test_api/data/xyxyxyxyxyx.txt'
        request = self.factory.get('__lastblogupdate.json')
        ret = api_last_blog_update(request)
        print(ret)
        print(ret.content)
        self.assertEqual(ret.content, b'{"lastupdate": null}')


            ################################################
            ######### api_normalize_url UNIT TESTS #########
            ################################################

    def test__api_normalize_url_no_request(self):
        "[test_ui.py] api_normalize_url: no request"
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /__normalizeurl.json'):
            api_normalize_url(None)

    def test__api_normalize_url_no_get(self):
        "[test_ui.py] api_normalize_url: no GET"
        request = self.factory.get('__normalizeurl.json')
        request.GET = None
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /__normalizeurl.json'):
            api_normalize_url(request)
