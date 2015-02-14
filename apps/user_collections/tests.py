"""
#  user_collections

"""
from django.test import TestCase
from django.test.client import Client
from django.db.models import get_model
from  django.utils.importlib import import_module
from search.views import *
from results.views import *
from django.http import QueryDict

cursor = connection.cursor()

class user_CollectionsTests(TestCase):

    def setUp(self):
        self.client = Client()
        """
        set up sessions for anonymous users
        """
        engine = import_module(settings.SESSION_ENGINE)
        settings
        store = engine.SessionStore()
        store.save()
        self.client.cookies[settings.SESSION_COOKIE_NAME] = store.session_key

    def test__edit_collection(self):
        response = self.client.get('/opus/collections/default/add.json?request=1&ringobsid=S_IMG_CO_ISS_1680806160_N', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        print response.content
        self.assertGreater(len(response.content), 42)

