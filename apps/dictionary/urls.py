from django.conf.urls import url
from django.contrib import admin

from dictionary import views

from django.conf.urls.static import static
from django.conf import settings

from views import (
    display_definitions,
    search_definitions,
    get_definition_list,
)

urlpatterns = [
    url(r'^list.json/(?P<alpha>[A-Z]+)/$', get_definition_list, name='list'),
    url(r'^search.json/(?P<slug>.+)/$', search_definitions, name='search'),
    url(r'^$', display_definitions),
    url(r'^(?P<slug>[-\sa-zA-Z0-9]+)$', display_definitions, name='dictionary'),
]
