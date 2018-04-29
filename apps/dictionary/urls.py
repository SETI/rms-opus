from django.conf.urls import url
from django.contrib import admin

from dictionary import views

from django.conf.urls.static import static
from django.conf import settings

from views import (
    display_definitions,
    search_definitions,
    get_definition_list,
    test_get_def,
)

urlpatterns = [
    url(r'^list.json/(?P<alpha>[A-Z]+)/$', get_definition_list, name='list'),
    url(r'^search.json/(?P<slug>.+)/$', search_definitions, name='search'),
    url(r'^test.json/(?P<term>[0-9a-zA-Z\-_]+).(?P<context>[0-9a-zA-Z\-_]+)$', test_get_def, name='test'),
    url(r'^$', display_definitions),
    url(r'^(?P<slug>[-\sa-zA-Z0-9]+)$', display_definitions, name='dictionary'),
]
