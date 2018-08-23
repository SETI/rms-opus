import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from django.conf import settings
from settings import CACHES
settings.configure(CACHES=CACHES)

from django.core.cache import cache
cache.clear()
cache._cache.flush_all()  # clears memcache hopefully only on this port!
