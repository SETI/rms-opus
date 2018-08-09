import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
import django.core.cache as cache
cache.cache.clear()
