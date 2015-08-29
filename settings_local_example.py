from secrets import *
import os
import sys

DEBUG = True

BASE_PATH = 'opus'

DATABASES = {
    'default': {
        'NAME': '',  # local database name
        'ENGINE': 'django.db.backends.mysql',
        'USER': DB_USER,
        'PASSWORD': DB_PASS,
        'OPTIONS':{ 'unix_socket': '/private/tmp/mysql.sock'}
    }
}

# for local laptop dev, remove all below for production
MEDIA_ROOT = os.path.join( '', 'static_media' )  # first arg is local media path
MEDIA_URL = '/static_media/'

ADMIN_MEDIA_PREFIX = 'http://pds-rings.seti.org:/~lballard/django_opus/static_media/admin/'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    '/users/lballard/projects/opus/apps/',
    '/users/lballard/projects/opus/apps/ui/templates/',
    '/users/lballard/projects/opus/apps/results/templates/',
    '/users/lballard/projects/opus/apps/metadata/templates/',
    '/users/lballard/projects/opus/apps/quide/templates/',
    '/users/lballard/projects/opus/apps/mobile/templates/',
)

# pip install django-infinite-memcached
"""
CACHES = {
    "default": {
        "BACKEND": "infinite_memcached.cache.MemcachedCache",
        "LOCATION": "127.0.0.1:11212",
    },
}
"""
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
   }
}



