from django.conf.urls import url
from django.contrib import admin

from dictionary import views

from django.conf.urls.static import static
from django.conf import settings
from django.contrib.staticfiles.storage import staticfiles_storage
from django.views.generic.base import RedirectView

from views import (
    display_definitions,
    search_definitions,
    get_definition_list,
    test_get_def,
)

urlpatterns = [
    url(r'^list.json/(?P<alpha>[A-Z]+)/$', get_definition_list, name='list'),
    url(r'^search.json/(?P<slug>.+)/$', search_definitions, name='search'),
    url(r'^test.json/(?P<term>[-\w]+).(?P<context>[-\w]+)$', test_get_def, name='test'),
    url(r'^$', display_definitions),
    url(r'^(?P<slug>[-\w]+)$', display_definitions, name='dictionary'),
    url(
        r'^favicon.ico$',
        RedirectView.as_view(
            url=staticfiles_storage.url('favicon.ico'),
            permanent=False),
        name="favicon"
    ),
]
