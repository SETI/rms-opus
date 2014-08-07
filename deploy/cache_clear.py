import sys
base_path = '/home/django/djcode/opus/'
sys.path.append(base_path)

from django.conf import settings
from settings import CACHES

settings.configure(CACHES=CACHES) # include any other settings you might need

from django.core.cache import cache
cache.clear()

