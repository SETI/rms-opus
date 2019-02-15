# ui/test_ui.py

import logging
from unittest import TestCase
from django.test.client import Client

import settings

from ui.views import *

class uiTests(TestCase):
    def setUp(self):
        self.maxDiff = None
        logging.disable(logging.ERROR)

    # enable error logging and trace output after test
    def tearDown(self):
        logging.disable(logging.NOTSET)


            ###################################################
            ######### api_last_blog_update UNIT TESTS #########
            ###################################################

    def test__api_last_blog_update_no_request(self):
        "api_last_blog_update: no request"
        with self.assertRaises(Http404):
            api_last_blog_update(None)

    def test__api_last_blog_update_no_get(self):
        "api_last_blog_update: no GET"
        c = Client()
        response = c.get('__lastblogupdate.json')
        request = response.wsgi_request
        request.GET = None
        with self.assertRaises(Http404):
            api_last_blog_update(request)

    def test__api_last_blog_update_ok(self):
        "api_last_blog_update: normal"
        settings.OPUS_LAST_BLOG_UPDATE_FILE = 'test_api/data/lastblogupdate.txt'
        c = Client()
        response = c.get('__lastblogupdate.json')
        request = response.wsgi_request
        ret = api_last_blog_update(request)
        print(ret)
        self.assertEqual(ret.content, b'{"lastupdate": "2019-JAN-01"}')

    def test__api_last_blog_update_bad(self):
        "api_last_blog_update: missing"
        settings.OPUS_LAST_BLOG_UPDATE_FILE = 'test_api/data/xyxyxyxyxyx.txt'
        c = Client()
        response = c.get('__lastblogupdate.json')
        request = response.wsgi_request
        ret = api_last_blog_update(request)
        print(ret)
        print(ret.content)
        self.assertEqual(ret.content, b'{"lastupdate": null}')
