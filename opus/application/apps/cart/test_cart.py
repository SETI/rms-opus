"""
#  cart

"""
from django.test import RequestFactory
# from django.test import TestCase  # removed because it deletes test table data after every test
from unittest import TestCase
from django.test.client import Client
from django.contrib.auth.models import AnonymousUser, User
from importlib import import_module
from search.views import *
from results.views import *
from django.http import QueryDict

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_COOKIE_NAME = 'opus-test-cookie'

cursor = connection.cursor()

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_COOKIE_NAME = 'opus-test-cookie'
settings.CACHE_BACKEND = 'dummy:///'

class test_session(dict):
    """
    extends a dict object and adds a session_key attribute for use in this test suite

    because in django tests:

    session and authentication attributes must be supplied by the test itself if required for the view to function properly.
    ( via http://stackoverflow.com/questions/14714585/using-session-object-in-django-unit-test )

    in most cases a request.session = {} in the test itself would suffice
    but in cart views we also want to receive a string from request.session.session_key
    because that's how cart tables are named

    extends the dict because that is how real sessions are interacted with

    """
    session_key = 'test_key'
    has_session = True


class cartTests(TestCase):

    def _empty_cart(self):
        cursor = connection.cursor()
        cursor.execute('DELETE FROM cart')
        cache.clear()
        cache._cache.flush_all()  # clears memcache hopefully only on this port!

    def setUp(self):
        self._empty_cart()
        sys.tracebacklimit = 0 # default: 1000
        logging.disable(logging.ERROR)

    def tearDown(self):
        self._empty_cart()
        sys.tracebacklimit = 1000 # default: 1000
        logging.disable(logging.NOTSET)

    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()
