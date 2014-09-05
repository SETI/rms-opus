import sys
from settings import PROJECT_ROOT
sys.path.append(PROJECT_ROOT)

from django.conf import settings
from settings import CACHES

settings.configure(CACHES=CACHES) # include any other settings you might need

from django.core.cache import cache
cache.clear()
cache._cache.flush_all()  # clears memcache hopefully only on this port!
