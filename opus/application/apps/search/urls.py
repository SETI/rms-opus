# search/urls.py
from django.urls import re_path
from search.views import (
    api_normalize_input,
    api_string_search_choices,
)

urlpatterns = [
    re_path(r'^__api/normalizeinput.json$', api_normalize_input),
    re_path(r'^__api/stringsearchchoices/(?P<slug>\w+).json$', api_string_search_choices),
]
