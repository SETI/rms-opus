"""Django settings for the OPUS web application.

Every value this deployment can vary -- credentials, hosts, paths, log levels and
the fault-injection knobs -- comes from the TOML file named by `OPUS_CONFIG`,
read once through `opus_config.get_config`; the rest are fixed application
settings written out below. Nothing here reads the environment directly and
there is no default configuration path. Every management command and the wsgi entry
point load this module, so a missing or invalid configuration file fails at startup
rather than at first request.
"""

from pathlib import Path

from opus_config import get_config

# Module-level helpers in this file are lower-case on purpose. Django treats every
# upper-case name here as a setting, and its only test is str.isupper(), which a
# leading underscore does not defeat: '_HAS_MEMCACHE'.isupper() is True, so the
# earlier spelling published these two internals as settings and listed them in
# `manage.py diffsettings`.

# First check to see if we have the memcache package installed
_has_memcache = False
try:  # pragma: no cover
    # An optional accelerator rather than a declared dependency: OPUS runs
    # without it, on Django's local-memory cache. It is not in the project's
    # requirements and ships no stubs, so the checker cannot see it either.
    import pymemcache  # type: ignore[import-not-found]

    _has_memcache = True
except ImportError:  # pragma: no cover
    pass

# Now check to see if memcached is actually running
if _has_memcache:
    try:
        _memcache_client = pymemcache.client.base.Client(('127.0.0.1', 11211))
        _memcache_client.set('__test_key__', 'test_val')
    except ConnectionRefusedError:
        _has_memcache = False

BASE_PATH = 'opus'  # production base path is handled by apache, local is not.

# The directory this package was installed into (src/opus_app in a development
# checkout). Templates and static files travel with the package, so they are
# always found relative to this, never relative to the working directory.
BASE_DIR = Path(__file__).resolve().parent

################################################################################
# Settings supplied by the installation's configuration file, which the
# OPUS_CONFIG environment variable names.
#
# Every name the application reads is assigned explicitly below, so nothing
# enters this namespace unannounced. The configuration file has no default
# location: importing this module without OPUS_CONFIG set raises ConfigError
# rather than starting the site against another installation's settings.
################################################################################

_config = get_config()

# Django core.
SECRET_KEY = _config.django.secret_key
DEBUG = _config.django.debug
ALLOWED_HOSTS = list(_config.django.allowed_hosts)
# Only a deployed server sets static_root, because collectstatic never runs on a
# development or test installation. None is Django's own default.
STATIC_ROOT = _config.paths.static_root

# Database. The engine follows the configured brand (see _db_engines below), so
# the web application and the import pipeline cannot disagree about which
# database they are talking to.
DB_HOST_NAME = _config.database.host
DB_SCHEMA_NAME = _config.database.schema
DB_USER = _config.database.user
DB_PASSWORD = _config.database.password

# Roots of the PDS3 and PDS4 holdings served to users.
PDS3_DATA_DIR = _config.paths.pds3_holdings
PDS4_DATA_DIR = _config.paths.pds4_holdings

# Static files and public URLs.
OPUS_STATIC_ROOT = _config.paths.opus_static_root
CACHE_SERVER_PREFIX = _config.django.cache_server_prefix
PUBLIC_OPUS_URL = _config.django.public_url
PRODUCT_HTTP_PATH = _config.django.product_http_path
VIEWMASTER_ROOT_PATH = _config.django.viewmaster_url

# Cart downloads.
TAR_FILE_PATH = _config.paths.tar_dir
MANIFEST_FILE_PATH = _config.paths.manifest_dir
TAR_FILE_URL_PATH = _config.django.tar_file_url

# Site content maintained outside the repository.
OPUS_LAST_BLOG_UPDATE_FILE = _config.paths.last_blog_update_file
OPUS_NOTIFICATION_FILE = _config.paths.notification_file

# Logging.
OPUS_LOG_FILE = _config.paths.opus_log_file
OPUS_LOG_FILE_LEVEL = _config.django.log_file_level
OPUS_LOG_CONSOLE_LEVEL = _config.django.log_console_level
OPUS_LOG_DJANGO_LEVEL = _config.django.log_django_level
OPUS_LOG_API_CALLS = _config.django.log_api_calls

# Fault injection (see opus_app.apps.tools.app_utils).
OPUS_FAKE_API_DELAYS = _config.django.fake_api_delays
OPUS_FAKE_SERVER_ERROR404_PROBABILITY = _config.django.fake_error404_probability
OPUS_FAKE_SERVER_ERROR500_PROBABILITY = _config.django.fake_error500_probability

SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_SAVE_EVERY_REQUEST = True

# The on-disk directory is opus_app/static/; the public URL namespace is
# /static_media/ and must stay that way, because it is hardcoded in
# static/js/opus.js, embedded in the golden API fixtures, and aliased in the
# production Apache configuration.
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

# Datetimes are stored and handled in UTC. This is Django's own default from 5.0
# onwards and is stated here rather than inherited, because the value decides how
# every DateTimeField in the database is interpreted. Nothing in the web
# application reads or writes one through the ORM today — the columns are filled
# by the import pipeline and by the cart's raw SQL — so the setting is a
# statement of intent for code added later.
USE_TZ = True

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# File and static-file storage backends. These are Django's own defaults, named
# explicitly because STORAGES replaced the removed DEFAULT_FILE_STORAGE and
# STATICFILES_STORAGE settings and is the only supported way to change them.
# staticfiles deliberately stays on the plain backend rather than a manifest one:
# OPUS's asset URLs are cache-busted by the ?version= suffix that
# apps.tools.app_utils supplies, and a manifest backend would require every
# template- and JavaScript-referenced asset to survive collectstatic first.
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
    },
}

# This governs the contrib tables `migrate` creates AND the 19 OPUS models that
# do not declare a primary key of their own — among them ParamInfo, Cart,
# UserSearches, TableNames, Partables and the generated ZZ* duplicates — for
# which Django synthesizes `id`. Do NOT read it as "contrib only".
#
# It stays AutoField. Every one of those tables already exists with a 32-bit
# AUTO_INCREMENT `id` column — some created by the import pipeline (cart,
# param_info, user_searches, table_names, partables, definitions, contexts) and
# the rest by `migrate` (the contrib tables, which the generated ZZ* models also
# map). BigAutoField would make Django's idea of the column disagree with the
# column, and would generate migrations altering the contrib tables on the
# deployed servers for no benefit.
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

MIDDLEWARE = [
    'django.middleware.cache.UpdateCacheMiddleware',
    'django.middleware.gzip.GZipMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.cache.FetchFromCacheMiddleware',
    'opus_app.apps.tools.opus_middleware.StripWhitespaceMiddleware',
]

ROOT_URLCONF = 'opus_app.urls'

FORM_RENDERER = 'django.forms.renderers.TemplatesSetting'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # The apps/<app>/templates directories are reachable through the
        # app_directories loader below as well; this project lists them here
        # too.
        'DIRS': [
            BASE_DIR / 'templates',
            BASE_DIR / 'apps',
            BASE_DIR / 'apps/ui/templates',
            BASE_DIR / 'apps/results/templates',
            BASE_DIR / 'apps/metadata/templates',
            BASE_DIR / 'apps/search/templates',
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
                'django.template.context_processors.request',
            ],
            'loaders': [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
            ],
        },
    },
]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'django.forms',
    # Django derives each app label from the last component of these paths, so
    # the labels are 'search', 'paraminfo', 'metadata', ...
    'opus_app.apps.search',
    'opus_app.apps.paraminfo',
    'opus_app.apps.metadata',
    'opus_app.apps.help',
    'opus_app.apps.results',
    'opus_app.apps.ui',
    'opus_app.apps.cart',
    'opus_app.apps.tools',
]

if _has_memcache:  # pragma: no cover
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.memcached.PyMemcacheCache',
            'LOCATION': '127.0.0.1:11211',
            'TIMEOUT': None,
        },
    }
else:
    CACHES = {  # pragma: no cover
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            #    'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        }
    }

CACHE_KEY_PREFIX = 'opus:' + DB_SCHEMA_NAME

# A Django setting in its own right, and easy to mistake for debugging-tool
# configuration: it is what lets django.template.context_processors.debug expose
# `debug` and `sql_queries` to a template, which it does only when DEBUG is on and
# the request comes from an address listed here.
INTERNAL_IPS = ['127.0.0.1']


LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format': '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s',
            'datefmt': '%d/%b/%Y %H:%M:%S',
        },
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        },
        'logfile': {
            'level': OPUS_LOG_FILE_LEVEL,
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': OPUS_LOG_FILE,
            'maxBytes': 50000,
            'backupCount': 2,
            'formatter': 'standard',
        },
        'console': {
            'level': OPUS_LOG_CONSOLE_LEVEL,
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'propagate': True,
            'level': OPUS_LOG_DJANGO_LEVEL,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': OPUS_LOG_DJANGO_LEVEL,
            'propagate': False,
        },
        # Each key must be a prefix of the app modules' __name__ (they call
        # logging.getLogger(__name__), giving e.g. 'opus_app.apps.cart.views').
        # A key that prefixes no real logger name silently stops that app's
        # records reaching the log file.
        'opus_app.apps.results': {
            'handlers': ['console', 'logfile'],
            'level': 'DEBUG',
        },
        'opus_app.apps.search': {
            'handlers': ['console', 'logfile'],
            'level': 'DEBUG',
        },
        'opus_app.apps.help': {
            'handlers': ['console', 'logfile'],
            'level': 'DEBUG',
        },
        'opus_app.apps.metadata': {
            'handlers': ['console', 'logfile'],
            'level': 'DEBUG',
        },
        'opus_app.apps.paraminfo': {
            'handlers': ['console', 'logfile'],
            'level': 'DEBUG',
        },
        'opus_app.apps.ui': {
            'handlers': ['console', 'logfile'],
            'level': 'DEBUG',
        },
        'opus_app.apps.cart': {
            'handlers': ['console', 'logfile'],
            'level': 'DEBUG',
        },
        'opus_app.apps.tools': {
            'handlers': ['console', 'logfile'],
            'level': 'DEBUG',
        },
        'opus_app.apps.search.forms': {
            'handlers': ['console', 'logfile'],
            'level': 'DEBUG',
        },
    },
}


# Only MySQL is implemented; the PostgreSQL entry is the same placeholder as
# opus_import.importdb.postgresql, kept so that adding the backend is a
# configuration change rather than a settings change. The loader accepts no other
# brand, so this lookup cannot fail for a valid configuration.
_db_engines = {
    'MySQL': 'django.db.backends.mysql',
    'PostgreSQL': 'django.db.backends.postgresql',
}

DATABASES = {
    'default': {
        'NAME': DB_SCHEMA_NAME,  # local database name
        'HOST': DB_HOST_NAME,
        'ENGINE': _db_engines[_config.database.brand],
        'USER': DB_USER,
        'PASSWORD': DB_PASSWORD,
        # 'OPTIONS':{ 'unix_socket': '/private/tmp/mysql.sock'}
        'TEST': {
            'NAME': DB_SCHEMA_NAME,  # use same database for test as prod YES
        },
    },
}

################################################################################
# From here on, the configuration is for the OPUS apps, not Django itself.
################################################################################

# Tables in which every observation in the database appears.
# These tables are ALWAYS shown to the user and are not triggered.
BASE_TABLES = [
    'obs_general',
    'obs_pds',
    'obs_ring_geometry',
    'obs_surface_geometry_name',
    'obs_surface_geometry',
    'obs_wavelength',
    'obs_type_image',
    'obs_profile',
]

# These slugs may show up in the hash but are not actually database
# queries and thus should be ignored when creating SQL
SLUGS_NOT_IN_DB = (
    'browse',
    'order',
    'page',
    'startobs',
    'cart_browse',
    'cart_order',
    'cart_page',
    'cart_startobs',
    'colls_browse',
    'colls_order',
    'colls_page',
    'colls_startobs',
    'cols',
    'col_chooser',
    'detail',
    'download',
    'expanded_cats',
    'gallery_data_viewer',
    'ignorelog',
    'limit',
    'loc_type',
    'range',
    'recyclebin',
    'reqno',
    'request',
    'types',
    'url_cols',
    'units',
    'unselected_types',
    'view',
    'widgets',
    'widgets2',
    '__sessionid',
)

# The columns selected when OPUS is first initialized
DEFAULT_COLUMNS = 'opusid,instrument,planet,target,time1,observationduration'

# The search widgets selected when OPUS is first intialized
DEFAULT_WIDGETS = 'instrument,observationtype,target'

# The sort order to be used if there is no order specified in the URL, or
# the order slug has no value.
DEFAULT_SORT_ORDER = 'time1,opusid'  # This must be a list of slugs

# The sort order to append after all other sort orders to ensure the ordering
# is always deterministic. This field should be unique for all observations.
FINAL_SORT_ORDER = 'opusid'  # This must be a slug

IMAGE_COLUMNS = ['thumb.jpg', 'small.jpg', 'med.jpg', 'full.jpg']

THUMBNAIL_IMAGE_SIZE = 100  # Pixels
PREVIEW_SIZE_TO_PDS_TYPE = {
    'thumb': ('Browse Image (thumbnail)', 'Browse Diagram (thumbnail)'),
    'small': ('Browse Image (small)', 'Browse Diagram (small)'),
    'med': ('Browse Image (medium)', 'Browse Diagram (medium)'),
    'full': ('Browse Image (full-size)', 'Browse Diagram (full-size)'),
}

PREVIEW_GUIDES = {
    'Cassini CIRS': 'https://pds-rings.seti.org/cassini/cirs/COCIRS_previews.txt',
    'Cassini UVIS': 'https://pds-rings.seti.org/cassini/uvis/UVIS_previews.txt',
    'Cassini VIMS': 'https://pds-rings.seti.org/cassini/vims/COVIMS_previews.txt',
}

# Browse products displayed in OPUS detail tab
DISPLAYED_BROWSE_PRODUCTS = ['browse_medium', 'diagram_medium', 'browse_full', 'diagram_full']

RANGE_FORM_TYPES = ('LONG', 'RANGE')
MULT_FORM_TYPES = ('GROUP', 'MULTIGROUP')

# First one in list is the default
STRING_QTYPES = ('contains', 'begins', 'ends', 'matches', 'excludes', 'regex')
RANGE_QTYPES = ('any', 'all', 'only')

DEFAULT_PAGE_LIMIT = 100
DEFAULT_STRINGCHOICE_LIMIT = 100

SQL_MAX_LIMIT = 100000000  # Max size for a LIMIT clause

# More than this many rows in the cache table -> don't join it
STRINGCHOICE_FULL_SEARCH_COUNT_THRESHOLD = 100000
# Timeout for SELECT when joined with cache table
STRINGCHOICE_FULL_SEARCH_TIME_THRESHOLD = 500  # ms
# Timeout for SELECT When not joined with cache table
STRINGCHOICE_FULL_SEARCH_TIME_THRESHOLD2 = 500  # ms

THUMBNAIL_NOT_FOUND = 'https://opus.pds-rings.seti.org/static_media/img/thumbnail_not_found.png'

MAX_SELECTIONS_ALLOWED = 10000
MAX_SELECTIONS_FOR_DATA_DOWNLOAD = 10000
MAX_SELECTIONS_FOR_URL_DOWNLOAD = 10000
MAX_DOWNLOAD_SIZE = 3 * 1024 * 1024 * 1024  # 3 gig max for any single download
MAX_CUM_DOWNLOAD_SIZE = 50 * 1024 * 1024 * 1024  # 50 gigs max cum downloads for a session

TEST_RESULT_COUNTS_AGAINST_INTERNAL_DB = False

# Where the public API guide is published. The Help menu opens it, and the
# apiguide.pdf entry point redirects to it rather than serving a document of its own.
API_GUIDE_URL = 'https://rms-opus.readthedocs.io/en/latest/api_guide.html'

OPUS_FILE_VERSION = ''

# OPUS supported cart download formats, a dictionary keyed by format, and value
# is a tuple containing MIME type & accessing (w/r) modes for the format.
DOWNLOAD_FORMATS = {
    'zip': ('application/zip', 'w', 'r'),
    'tar': ('application/x-tar', 'w', 'r'),
    'tgz': ('application/gzip', 'w:gz', 'r:gz'),  # same as .tar.gz, we will use .tgz here
}

# We don't want to have these characters in HTML class or ID for customized tooltips.
INVALID_CLASS_CHAR = r'~!@$%^&*()+=,./;:"?><[]\{}|`# '

PDS3_HOLDINGS_DIR = '/holdings'
PDS4_HOLDINGS_DIR = '/pds4-holdings'
