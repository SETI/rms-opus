# help/urls.py
from django.conf.urls import url

from help.views import (
    api_about,
    api_volumes,
    api_faq,
    api_gettingstarted,
    api_splash,
    api_guide,
    api_citing_opus,
)

urlpatterns = [
    url(r'^__help/about.html$', api_about),
    url(r'^__help/volumes.html$', api_volumes),
    url(r'^__help/faq.html$', api_faq),
    url(r'^__help/gettingstarted.html$', api_gettingstarted),
    url(r'^__help/splash.html$', api_splash),
    url(r'^__help/guide.html$', api_guide),  # api help pages
    url(r'^__help/citing.html$', api_citing_opus),
]
