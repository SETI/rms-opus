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
    url(r'^__help/about.(?P<fmt>html|pdf)$', api_about),
    url(r'^__help/volumes.(?P<fmt>html|pdf)$', api_volumes),
    url(r'^__help/faq.(?P<fmt>html|pdf)$', api_faq),
    url(r'^__help/gettingstarted.(?P<fmt>html|pdf)$', api_gettingstarted),
    url(r'^__help/splash.html$', api_splash),
    # We can eventually add pdf to api_guide once it's working properly
    url(r'^__help/guide.(?P<fmt>html|pdf)$', api_guide),
    url(r'^__help/citing.(?P<fmt>html|pdf)$', api_citing_opus),
]
