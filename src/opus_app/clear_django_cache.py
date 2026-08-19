"""Empty the Django cache. Run after a deploy: python -m opus_app.clear_django_cache"""
import os

from django.conf import settings

from opus_app.settings import CACHES

os.environ['DJANGO_SETTINGS_MODULE'] = 'opus_app.settings'

settings.configure(CACHES=CACHES)

from django.core.cache import cache  # noqa: E402  (must follow settings.configure)

cache.clear()
