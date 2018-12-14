# search/urls.py
from django.conf.urls import url
from search.views import (
    api_normalize_input,
)

urlpatterns = [
    url(r'^__api/normalizeinput.json$', api_normalize_input),
]
