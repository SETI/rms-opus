import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from django.conf import settings
from settings import CACHES
settings.configure(CACHES=CACHES)

from django.core.cache import cache
cache.clear()
