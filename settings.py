import os
import sys
from collections import OrderedDict
from secrets import *

BASE_PATH = 'opus'  # production base path is handled by apache, local is not.
PROJECT_ROOT = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'apps'))
sys.path.insert(0, os.path.join(PROJECT_ROOT, '../pds-tools'))
sys.path.insert(0, os.path.join(PROJECT_ROOT, '../pds-webserver/python'))

import opus_support
import julian

ALLOWED_HOSTS = ('127.0.0.1',
                 'localhost',
                 'pds-rings-tools.seti.org',
                 'tools.pds-rings.seti.org')

OPUS_DB = 'opus_new'

DEBUG = True

SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_SAVE_EVERY_REQUEST = True

ADMINS = (
    ('Robert French', 'rfrench@seti.org'),
)
MANAGERS = ADMINS

STATIC_URL = '/static_media/'

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/Los_Angeles'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
STATICFILES_DIRS = [
    (os.path.join(PROJECT_ROOT, 'static_media/')),
    'static_media/',
]

ADMIN_MEDIA_PREFIX = ''

MIDDLEWARE_CLASSES = (
    'django.middleware.gzip.GZipMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'last_modified.middleware.CacheControlMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.cache.UpdateCacheMiddleware',
    'django.middleware.cache.FetchFromCacheMiddleware',
    # prod remove:
    #'debug_toolbar.middleware.DebugToolbarMiddleware',
)

ROOT_URLCONF = 'urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            PROJECT_ROOT + '/apps/',
            PROJECT_ROOT + '/apps/ui/templates/',
            PROJECT_ROOT + '/apps/dictionary/templates/',
            PROJECT_ROOT + '/apps/results/templates/',
            PROJECT_ROOT + '/apps/metadata/templates/',
            PROJECT_ROOT + '/apps/quide/templates/',
            PROJECT_ROOT + '/apps/search/templates/',
        ],
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
            ],
            'loaders': [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
            ]
        },
    },
]

#DATABASE_ROUTERS = ['dictionary.router.DictionaryRouter']

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.sites',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_nose',
    'django_memcached',
    'django.contrib.admindocs',
    'storages',
    'search',
    'paraminfo',
    'metadata',
    'guide',
    'results',
    'ui',
    'user_collections',
    'tools',
    'dictionary',
    'metrics'
)


# https://github.com/edavis/django-infinite-memcached/tree/
CACHES = {
    "default": {
	"BACKEND":"django.core.cache.backends.memcached.MemcachedCache",
        "LOCATION": "127.0.0.1:11211",
	"TIMEOUT": None,
    },
}

# for last_modified middleware
LAST_MODIFIED_FUNC = 'tools.last_mod.last_mod'
CACHE_MAX_AGE = 3600 * 24 * 120  # the last number is the number of days


INTERNAL_IPS = ('127.0.0.1',)


TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

#CACHE_BACKEND = 'dummy://'  # turns off caching
#CACHE_BACKEND = "memcached://127.0.0.1:11211/?timeout=0"
# CACHE_BACKEND = "memcached://127.0.0.1:11211"


#CACHE_MIDDLEWARE_SECONDS = 0


DEBUG_TOOLBAR_CONFIG = { 'INTERCEPT_REDIRECTS': False }

DEBUG_TOOLBAR_PANELS = (
    'debug_toolbar.panels.version.VersionDebugPanel',
    'debug_toolbar.panels.timer.TimerDebugPanel',
    'debug_toolbar.panels.headers.HeaderDebugPanel',
    'debug_toolbar.panels.request_vars.RequestVarsDebugPanel',
    'debug_toolbar.panels.sql.SQLDebugPanel',
    'debug_toolbar.panels.cache.CacheDebugPanel',
    'debug_toolbar.panels.logger.LoggingPanel',
)


LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format' : "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            'datefmt' : "%d/%b/%Y %H:%M:%S"
        },
    },
    'handlers': {
        'null': {
            'level':'DEBUG',
            'class':'logging.NullHandler',
        },
        'logfile': {
            'level':'DEBUG',
            'class':'logging.handlers.RotatingFileHandler',
            'filename': PROJECT_ROOT + "/logs/opus_log.txt",
            'maxBytes': 50000,
            'backupCount': 2,
            'formatter': 'standard',
        },
        'console':{
            'level':'INFO',
            'class':'logging.StreamHandler',
            'formatter': 'standard'
        },
    },
    'loggers': {
        'django': {
            'handlers':['console'],
            'propagate': True,
            'level':'WARN',
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'results': {
            'handlers': ['console', 'logfile'],
            'level': 'DEBUG',
        },
        'search': {
            'handlers': ['console', 'logfile'],
            'level': 'DEBUG',
        },
        'guide': {
            'handlers': ['console', 'logfile'],
            'level': 'DEBUG',
        },
        'metadata': {
            'handlers': ['console', 'logfile'],
            'level': 'DEBUG',
        },
        'paraminfo': {
            'handlers': ['console', 'logfile'],
            'level': 'DEBUG',
        },
        'ui': {
            'handlers': ['console', 'logfile'],
            'level': 'DEBUG',
        },
        'testbed': {
            'handlers': ['console', 'logfile'],
            'level': 'DEBUG',
        },
        'user_collections': {
            'handlers': ['console', 'logfile'],
            'level': 'DEBUG',
        },
        'tools': {
            'handlers': ['console', 'logfile'],
            'level': 'DEBUG',
        },
        'dictionary': {
            'handlers': ['console', 'logfile'],
            'level': 'DEBUG',
        },
        'metrics': {
            'handlers': ['console', 'logfile'],
            'level': 'DEBUG',
        },
        'search.forms': {
            'handlers': ['console', 'logfile'],
            'level': 'DEBUG',
        },
    }
}


os.environ['REUSE_DB'] = "1"  # for test runner

DATABASES = {
    'default': {
        'NAME': OPUS_DB,  # local database name
        'ENGINE': 'django.db.backends.mysql',
        'USER': DB_USER,
        'PASSWORD': DB_PASS,
        # 'OPTIONS':{ 'unix_socket': '/private/tmp/mysql.sock'}
        'TEST': {
                    'NAME': OPUS_DB,  # use same database for test as prod YES
                },
    },
    'dictionary': {
        'NAME': 'dictionary',
        'ENGINE': 'django.db.backends.mysql',
        'USER': DB_USER,
        'PASSWORD': DB_PASS,
        # 'OPTIONS':{ 'init_command': 'SET storage_engine=MYISAM;'},
    },
    'metrics': {
        'NAME': 'opus_metrics',
        'ENGINE': 'django.db.backends.mysql',
        'USER': DB_USER,
        'PASSWORD': DB_PASS,
        # 'OPTIONS':{ 'unix_socket': '/private/var/mysql/mysql.sock'},
    }
}

################################################################################
# From here on, the configuration is for the OPUS apps, not Django itself.
################################################################################

import pdsfile

PDS_DATA_DIR = '/pdsdata/holdings'

pdsfile.preload(PDS_DATA_DIR)
pdsfile.use_pickles()

# Tables in which every observation in the database appears.
# These tables are ALWAYS shown to the user and are not triggered.
BASE_TABLES = ['obs_general', 'obs_pds', 'obs_ring_geometry',
               'obs_surface_geometry', 'obs_wavelength', 'obs_type_image']

# These slugs may show up in the hash but are not actually database
# queries and thus should be ignored when creating SQL
SLUGS_NOT_IN_DB = ('browse', 'col_chooser', 'colls_browse', 'cols', 'detail',
                   'gallery_data_viewer', 'limit', 'order', 'page',
                   'reqno', 'view', 'widgets', 'widgets2')


TAR_FILE_URI_PATH = 'http://pds-rings-downloads.seti.org/opus/'
PRODUCT_HTTP_PATH = 'https://pds-rings.seti.org/'
DEFAULT_COLUMNS = 'opusid,planet,target,time1,time2'
DEFAULT_SORT_ORDER = 'time1' # This must be a slug
IMAGE_COLUMNS   = ['thumb.jpg','small.jpg','med.jpg','full.jpg']
RANGE_FIELDS    = ['LONG','RANGE']

THUMBNAIL_IMAGE_SIZE = 100 # Pixels
PREVIEW_SIZE_TO_PDS_TYPE = {
    'thumb': 'Browse Image (thumbnail)',
    'small': 'Browse Image (small)',
    'med': 'Browse Image (medium)',
    'full': 'Browse Image (full-size)'
}

PREVIEW_GUIDES = {
    'COCIRS': 'https://pds-rings.seti.org/cassini/cirs/COCIRS_previews.txt',
    'COUVIS': 'https://pds-rings.seti.org/cassini/uvis/UVIS_previews.txt',
    'COVIMS': 'https://pds-rings.seti.org/cassini/vims/COVIMS_previews.txt'
}

MULT_FIELDS	= ['GROUP','TARGETS']
DEFAULT_PAGE_LIMIT = 100
MULT_FORM_TYPES = ('GROUP','TARGETS');
ERROR_LOG_PATH = PROJECT_ROOT + "logs/opus_log.txt"

THUMBNAIL_NOT_FOUND = 'https://tools.pds-rings.seti.org/assets/static_media/img/thumbnail_not_found.png'

# FILE_HTTP_PATH  = 'https://pds-rings.seti.org/holdings/volumes/'
# DERIVED_HTTP_PATH  = 'https://pds-rings.seti.org/holdings/calibrated/'
MAX_CUM_DOWNLOAD_SIZE = 5*1024*1024*1024 # 5 gigs max cum downloads

LOG_API_CALLS = True
