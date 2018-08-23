# guide/urls.py
from django.conf.urls import url

from guide.views import api_guide

urlpatterns = [
    url(r'^api/$', api_guide),
    url(r'^api/guide.html$', api_guide),  # api help pages
]
