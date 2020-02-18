# urls.py
from django.conf.urls import url, include
from django.conf import settings
from django.contrib import admin
from django.views.generic import TemplateView

admin.autodiscover()

from ui.views import main_site

# UI resources - the homepage - ui.views
base_urlpatterns = [
    url(r'^$', main_site.as_view()),
    url(r'^opus/$', main_site.as_view()),
    url(r'^', include('ui.urls')),
    url(r'^', include('results.urls')),
    url(r'^', include('metadata.urls')),
    url(r'^', include('search.urls')),
    url(r'^', include('help.urls')),
    url(r'^', include('cart.urls')),
]

dictionary_urlpatterns = [
    url(r'^', include('dictionary.urls'))
]

urlpatterns = [
    url('^', include(base_urlpatterns)),
    url('^%s/' % settings.BASE_PATH, include(base_urlpatterns)),  # dev
    url('^dictionary/', include(dictionary_urlpatterns)),
    url('^__dictionary/', include(dictionary_urlpatterns)),
]
