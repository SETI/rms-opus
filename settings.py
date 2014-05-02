# Django settings for opus project.
import os
import sys
PROJECT_ROOT = os.path.dirname(__file__)
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'apps'))
from secrets import *

TIME_LIB_PATH          = "/library/webserver/bin/timeconvert/"
sys.path.append(TIME_LIB_PATH)

DEBUG = False
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Lisa Ballard', 'lballard@seti.org'),
)

def custom_show_toolbar(request):
    return True # Always show toolbar, for example purposes only.

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'NAME': 'opus',
        'ENGINE': 'django.db.backends.mysql',
        'USER': DB_USER,
        'PASSWORD': DB_PASS,
        # 'STORAGE_ENGINE': 'MYISAM',
        'OPTIONS':{ 'init_command': 'SET storage_engine=MYISAM;'},
        # 'TEST_NAME': 'test_opus',
        # 'OPTIONS':{ 'unix_socket': '/private/var/mysql/mysql.sock'}
    }
}


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

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
# MEDIA_URL = 'http://pds-rings.seti.org:/~lballard/django_opus/static_media/'
# MEDIA_URL = 'https://s3.amazonaws.com/%s/' % AWS_STORAGE_BUCKET_NAME
MEDIA_URL = 'http://s3.amazonaws.com/%s/' % AWS_STORAGE_BUCKET_NAME
STATIC_URL = MEDIA_URL

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/static/admin/'
ADMIN_MEDIA_PREFIX = 'https://s3.amazonaws.com/%s/admin/' % AWS_STORAGE_BUCKET_NAME

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    #'django.template.loaders.eggs.Loader',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.messages.context_processors.messages',
    "django.contrib.auth.context_processors.auth",
    "ui.context_processors.admin_media",
    'django.core.context_processors.static',
    )



MIDDLEWARE_CLASSES = (
    'django.middleware.gzip.GZipMiddleware',
    'django.middleware.cache.UpdateCacheMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.cache.FetchFromCacheMiddleware',
    # prod remove:
    #'debug_toolbar.middleware.DebugToolbarMiddleware',
)

ROOT_URLCONF = 'urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    '/home/django/djcode/opus',
    '/home/django/djcode/opus/ui/templates/',
    '/home/django/djcode/opus/results/templates/',
    '/home/django/djcode/opus/metadata/templates/',
    '/home/django/djcode/opus/quide/templates/',
    '/home/django/djcode/opus/mobile/templates/',
)

INSTALLED_APPS = (
    # prod remove
    'django_nose',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django_memcached',
    # 'debug_toolbar',
    # 'django.contrib.messages',
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.admindocs',
    'django.contrib.staticfiles',
    # 'south',
    'storages',
    'search',
    'paraminfo',
    'metadata',
    'guide',
    'results',
    'ui',
    'user_collections',
    'tools',
)

STATICFILES_DIRS = (os.path.join(PROJECT_ROOT, 'static_media'),)
STATICFILES_STORAGE = 'storages.backends.s3boto.S3BotoStorage'

# https://github.com/edavis/django-infinite-memcached/tree/
CACHES = {
    "default": {
        "BACKEND": "infinite_memcached.cache.MemcachedCache",
        "LOCATION": "127.0.0.1:11211",
    },
}

INTERNAL_IPS = ("127.0.0.1",)

## App constants

BASE_TABLES = ['obs_general', 'obs_ring_geometry','obs_surface_geometry','obs_wavelength']  # tables in which every observation in the database appears:
TAR_FILE_URI_PATH = 'http://pds-rings-downloads.seti.org/opus/'
IMAGE_HTTP_PATH = 'http://pds-rings.seti.org/browse/'
DEFAULT_COLUMNS = 'ringobsid,planet,target,phase1'
IMAGE_COLUMNS   = ['thumb.jpg','small.jpg','med.jpg','large.jpg']
RANGE_FIELDS    = ['TIME','LONG','RANGE']
MULT_FIELDS	= ['GROUP','TARGETS']
DEFAULT_LIMIT = 100
MULT_FORM_TYPES = ('GROUP','TARGETS');
ERROR_LOG_PATH = PROJECT_ROOT + "logs/opus_log.txt"
IMAGE_TYPES = ['Thumb','Small','Med','Full']


FILE_HTTP_PATH  = 'http://pds-rings.seti.org/volumes/'
DERIVED_HTTP_PATH  = 'http://pds-rings.seti.org/derived/'
IMAGE_HTTP_PATH = 'http://pds-rings.seti.org/browse/'
MAX_CUM_DOWNLAOD_SIZE = 5*1024*1024*1024 # 5 gigs max cum downloads



TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
SOUTH_TESTS_MIGRATE = False

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
            'class':'django.utils.log.NullHandler',
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
        'downloads': {
            'handlers': ['console', 'logfile'],
            'level': 'DEBUG',
        },
    }
}


BASE_PATH = ''  # production base path is handled by apache, local is not.
try:
    from settings_local import *
except ImportError:
    pass

