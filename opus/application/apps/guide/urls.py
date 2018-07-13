# guide/urls.py
from django.conf.urls import url
from guide.views import guide

# guide - app runs guide to  api
urlpatterns = [
    url(r'^api/$', guide),
    url(r'^api/guide.html$', guide),  # api help pages
]
