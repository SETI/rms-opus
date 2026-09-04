# opus_app/urls.py
"""The URL map: every route OPUS serves, at the site root and under the dev prefix."""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.conf import settings
from django.contrib import admin
from django.urls import include, re_path

from opus_app.apps.ui.views import MainSite

if TYPE_CHECKING:
    from django.urls import URLPattern, URLResolver

# Redundant since Django 1.7 (AdminConfig.ready() already ran this during
# django.setup()) and inert either way, because no app defines an admin module.
admin.autodiscover()

# UI resources - the homepage - opus_app.apps.ui.views
base_urlpatterns: list[URLPattern | URLResolver] = [
    re_path(r'^$', MainSite.as_view()),
    re_path(r'^opus/$', MainSite.as_view()),
    re_path(r'^', include('opus_app.apps.ui.urls')),
    re_path(r'^', include('opus_app.apps.results.urls')),
    re_path(r'^', include('opus_app.apps.metadata.urls')),
    re_path(r'^', include('opus_app.apps.search.urls')),
    re_path(r'^', include('opus_app.apps.help.urls')),
    re_path(r'^', include('opus_app.apps.cart.urls')),
]

urlpatterns = [
    re_path('^', include(base_urlpatterns)),
    re_path(f'^{settings.BASE_PATH}/', include(base_urlpatterns)),  # dev
]
