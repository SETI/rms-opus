from secrets import *
import os
import sys

DEBUG = True

sys.path.append('<full path to django project dir')
ALLOWED_HOSTS = ['127.0.0.1', 'localhost','pds-rings-tools.seti.org','tools.pds-rings.seti.org']
TIME_LIB_PATH          = "<path to timeconvert dir"
sys.path.append(TIME_LIB_PATH)

# import settings
opus1 = 'Observations'
opus2 = 'opus2'  # test suite will run against this

os.environ['REUSE_DB'] = "1"  # for test runner

DATABASES = {
    'default': {
        'NAME': 'opus_small',  # local database name
        'ENGINE': 'django.db.backends.mysql',
        'USER': DB_USER,
        'PASSWORD': DB_PASS,
        # 'OPTIONS':{ 'unix_socket': '/private/tmp/mysql.sock'}
        'TEST': {
                    'NAME': opus2,  # use same database for test as prod YES
                },
    },
    'dictionary': {
        'NAME': 'dictionary',
        'ENGINE': 'django.db.backends.mysql',
        'USER': DB_USER,
        'PASSWORD': DB_PASS,
        'OPTIONS':{ 'init_command': 'SET storage_engine=MYISAM;'},
    },
    'metrics': {
        'NAME': 'opus_metrics',
        'ENGINE': 'django.db.backends.mysql',
        'USER': DB_USER,
        'PASSWORD': DB_PASS,
        # 'OPTIONS':{ 'unix_socket': '/private/var/mysql/mysql.sock'},
    }
}

# django-infinite-memcached
"""
CACHES = {
    "default": {
        "BACKEND": "infinite_memcached.cache.MemcachedCache",
        "LOCATION": "127.0.0.1:11212",
    },
}
"""
"""
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
   }
}
"""
