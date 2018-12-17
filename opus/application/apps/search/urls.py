# search/urls.py
from django.conf.urls import url
from search.views import (
    api_normalize_input,
    api_string_search_choices,
)

urlpatterns = [
    url(r'^__api/normalizeinput.json$', api_normalize_input),
    url(r'^__api/stringsearchchoices/(?P<slug>\w+).json$', api_string_search_choices),
]
