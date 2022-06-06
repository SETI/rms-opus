# urls.py
from django.urls import re_path, include
from django.conf import settings
from django.contrib import admin
from django.views.generic import TemplateView

admin.autodiscover()

from ui.views import main_site

# UI resources - the homepage - ui.views
base_urlpatterns = [
    re_path(r'^$', main_site.as_view()),
    re_path(r'^opus/$', main_site.as_view()),
    re_path(r'^', include('ui.urls')),
    re_path(r'^', include('results.urls')),
    re_path(r'^', include('metadata.urls')),
    re_path(r'^', include('search.urls')),
    re_path(r'^', include('help.urls')),
    re_path(r'^', include('cart.urls')),
]

dictionary_urlpatterns = [
    re_path(r'^', include('dictionary.urls'))
]

urlpatterns = [
    re_path('^', include(base_urlpatterns)),
    re_path('^%s/' % settings.BASE_PATH, include(base_urlpatterns)),  # dev
    re_path('^dictionary/', include(dictionary_urlpatterns)),
    re_path('^__dictionary/', include(dictionary_urlpatterns)),
]
