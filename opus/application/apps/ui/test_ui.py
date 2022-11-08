# ui/test_ui.py

import logging
import sys
from unittest import TestCase

from django.core.cache import cache
from django.http import Http404
from django.test import RequestFactory

from ui.views import (api_notifications,
                      api_normalize_url)

import json
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


            ################################################
            ######### api_notifications UNIT TESTS #########
            ################################################

    def test__api_notifications_no_meta(self):
        "[test_ui.py] api_notifications: no META"
        request = self.factory.get('dummy')
        request.META = None
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /__notifications.json'):
            api_notifications(request)

    def test__api_notifications_no_get(self):
        "[test_ui.py] api_notifications: no GET"
        request = self.factory.get('__notifications.json')
        request.GET = None
        with self.assertRaises(Http404):
            api_notifications(request)

    # tests specific for blog update file
    def test__api_notifications_blog_update_file_ok(self):
        "[test_ui.py] api_notifications: blog update file ok"
        settings.OPUS_LAST_BLOG_UPDATE_FILE = 'test_api/data/lastblogupdate.txt'
        settings.OPUS_NOTIFICATION_FILE = 'test_api/data/xyxyxyxyxyx.html'
        request = self.factory.get('__notifications.json')
        ret = api_notifications(request)
        print(ret)
        self.assertEqual(ret.content, b'{"lastupdate": "2019-JAN-01", "notification": null, "notification_mdate": null}')

    def test__api_notifications_blog_update_file_empty(self):
        "[test_ui.py] api_notifications: blog update file empty"
        settings.OPUS_LAST_BLOG_UPDATE_FILE = 'test_api/data/lastblogupdate_empty.txt'
        settings.OPUS_NOTIFICATION_FILE = 'test_api/data/xyxyxyxyxyx.html'
        request = self.factory.get('__notifications.json')
        ret = api_notifications(request)
        print(ret)
        self.assertEqual(ret.content, b'{"lastupdate": null, "notification": null, "notification_mdate": null}')

    # tests specific for notification file
    def test__api_notifications_notification_file_empty(self):
        "[test_ui.py] api_notifications: notification file empty"
        settings.OPUS_LAST_BLOG_UPDATE_FILE = 'test_api/data/lastblogupdate.txt'
        settings.OPUS_NOTIFICATION_FILE = 'test_api/data/notification.html'
        request = self.factory.get('__notifications.json')
        ret = api_notifications(request)
        data = json.loads(ret.content)
        print(data)
        self.assertEqual(data['lastupdate'], "2019-JAN-01")
        self.assertIsNone(data['notification'])
        self.assertIsNotNone(data['notification_mdate'])

    def test__api_notifications_notification_not_empty(self):
        "[test_ui.py] api_notifications: notification file not empty"
        settings.OPUS_NOTIFICATION_FILE = 'test_api/data/test_ui_notification.html'
        request = self.factory.get('__notifications.json')
        ret = api_notifications(request)
        data = json.loads(ret.content)
        print(data)
        self.assertEqual(data['notification'], "<div><p>test</p></div>")
        self.assertIsNotNone(data['notification_mdate'])

    # a few combination tests
    def test__api_notifications_files_missing(self):
        "[test_ui.py] api_notifications: missing last blog update and notification files"
        settings.OPUS_LAST_BLOG_UPDATE_FILE = 'test_api/data/xyxyxyxyxyx.txt'
        settings.OPUS_NOTIFICATION_FILE = 'test_api/data/xyxyxyxyxyx.html'
        request = self.factory.get('__notifications.json')
        ret = api_notifications(request)
        print(ret)
        self.assertEqual(ret.content, b'{"lastupdate": null, "notification": null, "notification_mdate": null}')

    def test__api_notifications_blog_update_file_empty_notification_file_not_empty(self):
        "[test_ui.py] api_notifications: blog update file empty, notification file not empty"
        settings.OPUS_LAST_BLOG_UPDATE_FILE = 'test_api/data/lastblogupdate_empty.txt'
        settings.OPUS_NOTIFICATION_FILE = 'test_api/data/test_ui_notification.html'
        request = self.factory.get('__notifications.json')
        ret = api_notifications(request)
        data = json.loads(ret.content)
        print(data)
        self.assertIsNone(data['lastupdate'])
        self.assertEqual(data['notification'], "<div><p>test</p></div>")
        self.assertIsNotNone(data['notification_mdate'])

    def test__api_notifications_blog_update_file_missing_notification_file_empty(self):
        "[test_ui.py] api_notifications: blog update missing, notification file empty"
        settings.OPUS_LAST_BLOG_UPDATE_FILE = 'test_api/data/xyxyxyxyxyx.txt'
        settings.OPUS_NOTIFICATION_FILE = 'test_api/data/notification.html'
        request = self.factory.get('__notifications.json')
        ret = api_notifications(request)
        data = json.loads(ret.content)
        print(data)
        self.assertIsNone(data['lastupdate'])
        self.assertIsNone(data['notification'])
        self.assertIsNotNone(data['notification_mdate'])

    def test__api_notifications_blog_update_file_missing_notification_file_not_empty(self):
        "[test_ui.py] api_notifications: blog update missing, notification file empty"
        settings.OPUS_LAST_BLOG_UPDATE_FILE = 'test_api/data/xyxyxyxyxyx.txt'
        settings.OPUS_NOTIFICATION_FILE = 'test_api/data/test_ui_notification.html'
        request = self.factory.get('__notifications.json')
        ret = api_notifications(request)
        data = json.loads(ret.content)
        print(data)
        self.assertIsNone(data['lastupdate'])
        self.assertEqual(data['notification'], "<div><p>test</p></div>")
        self.assertIsNotNone(data['notification_mdate'])


            ################################################
            ######### api_normalize_url UNIT TESTS #########
            ################################################

    def test__api_normalize_url_no_meta(self):
        "[test_ui.py] api_normalize_url: no META"
        request = self.factory.get('dummy')
        request.META = None
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /__normalizeurl.json'):
            api_normalize_url(request)

    def test__api_normalize_url_no_get(self):
        "[test_ui.py] api_normalize_url: no GET"
        request = self.factory.get('__normalizeurl.json')
        request.GET = None
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /__normalizeurl.json'):
            api_normalize_url(request)
