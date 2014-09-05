import sys
import os

base_path = '/'.join(os.path.realpath(__file__).split('/')[:-2])
sys.path.append(base_path)

from django.conf import settings
from settings import CACHES

settings.configure(CACHES=CACHES) # include any other settings you might need

from django.core.cache import cache
cache.clear()
cache._cache.flush_all()  # clears memcache hopefully only on this port!
