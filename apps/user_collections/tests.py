"""
#  user_collections

"""
from django.test import TestCase
from django.test.client import Client
from django.db.models import get_model

from search.views import *
from results.views import *
from django.http import QueryDict

cursor = connection.cursor()

class user_CollectionsTests(TestCase):

    c = Client()

    def test__edit_collection(self):
        response = self.c.get('/opus/collections/default/add.json?request=1&ringobsid=S_IMG_CO_ISS_1680806160_N', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        print response.content.strip()
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.content), 42)

