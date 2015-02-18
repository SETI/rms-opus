"""
#  user_collections

"""
from django.test import TestCase, RequestFactory
from django.test.client import Client
from django.db.models import get_model
from django.contrib.auth.models import AnonymousUser, User
from django.utils.importlib import import_module
from search.views import *
from results.views import *
from django.http import QueryDict

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_COOKIE_NAME = 'opus-test-cookie'

cursor = connection.cursor()

class test_session(dict):
    session_key = 'test_key'

class user_CollectionsTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()

    def test__edit_collection(self):
        request = self.factory.get('/opus/collections/default/add.json?request=1&ringobsid=S_IMG_CO_ISS_1680806160_N', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        request.user = AnonymousUser()
        request.session = test_session()
        response = edit_collection(request, ring_obs_id = 'S_IMG_CO_ISS_1680806160_N', action = 'add')
        self.assertEqual(response.status_code, 200)
        expected = '{"count": 1, "request_no": 1, "err": false}'
        self.assertEqual(expected, response.content)


