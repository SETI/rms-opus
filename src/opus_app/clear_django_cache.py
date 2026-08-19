"""Empty the Django cache. Run after a deploy: python -m opus_app.clear_django_cache"""
from django.conf import settings

from opus_app.settings import CACHES

# CACHES is the only setting the cache backend needs, so configure() is used
# instead of DJANGO_SETTINGS_MODULE: this never loads the app registry.
settings.configure(CACHES=CACHES)

from django.core.cache import cache  # noqa: E402  (must follow settings.configure)

cache.clear()
