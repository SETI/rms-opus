# help/urls.py
from django.conf.urls import url

from help.views import (
    api_about,
    api_volumes,
    api_faq,
    api_tutorial,
    api_gettingstarted,
    api_splash,
    api_guide
)

urlpatterns = [
    url(r'^__help/about.html$', api_about),
    url(r'^__help/volumes.html$', api_volumes),
    url(r'^__help/faq.html$', api_faq),
    url(r'^__help/tutorial.html$', api_tutorial),
    url(r'^__help/gettingstarted.html$', api_gettingstarted),
    url(r'^__help/splash.html$', api_gettingstarted),
    url(r'^__help/guide.html$', api_guide),  # api help pages
]
