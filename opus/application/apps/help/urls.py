# help/urls.py
from django.urls import re_path

from help.views import (
    api_about,
    api_bundles,
    api_faq,
    api_gettingstarted,
    api_splash,
    api_api_guide,
    api_citing_opus,
)

urlpatterns = [
    re_path(r'^__help/about.(?P<fmt>html|pdf)$', api_about),
    re_path(r'^__help/bundles.(?P<fmt>html|pdf)$', api_bundles),
    re_path(r'^__help/faq.(?P<fmt>html|pdf)$', api_faq),
    re_path(r'^__help/gettingstarted.(?P<fmt>html|pdf)$', api_gettingstarted),
    re_path(r'^__help/splash.html$', api_splash),
    re_path(r'^apiguide.(?P<fmt>pdf)$', api_api_guide), # Public entrypoint
    re_path(r'^__help/apiguide.(?P<fmt>html|pdf)$', api_api_guide),
    re_path(r'^__help/citing.(?P<fmt>html|pdf)$', api_citing_opus),
]
