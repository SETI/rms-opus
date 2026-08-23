# opus_app/urls.py
from django.conf import settings
from django.contrib import admin
from django.urls import include, re_path

from opus_app.apps.ui.views import main_site

# Redundant since Django 1.7 (AdminConfig.ready() already ran this during
# django.setup()) and inert either way, because no app defines an admin module.
admin.autodiscover()

# UI resources - the homepage - opus_app.apps.ui.views
base_urlpatterns = [
    re_path(r'^$', main_site.as_view()),
    re_path(r'^opus/$', main_site.as_view()),
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
