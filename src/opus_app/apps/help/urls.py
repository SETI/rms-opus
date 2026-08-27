# help/urls.py
"""The URL routes for the help pages."""

from django.conf import settings
from django.urls import re_path
from django.views.generic.base import RedirectView

from opus_app.apps.help.views import (
    api_about,
    api_bundles,
    api_citing_opus,
    api_faq,
    api_gettingstarted,
    api_splash,
)

urlpatterns = [
    re_path(r'^__help/about.(?P<fmt>html|pdf)$', api_about),
    re_path(r'^__help/bundles.(?P<fmt>html|pdf)$', api_bundles),
    re_path(r'^__help/faq.(?P<fmt>html|pdf)$', api_faq),
    re_path(r'^__help/gettingstarted.(?P<fmt>html|pdf)$', api_gettingstarted),
    re_path(r'^__help/splash.html$', api_splash),
    # Public entrypoint. The API guide is published as documentation rather than
    # rendered here, so this answers 302 and points at it. The pattern keeps the
    # capture group it has always had so that the set of URLs it matches does not
    # change.
    #
    # RedirectView passes the captured group through `url % kwargs`, so
    # API_GUIDE_URL must contain no `%` at all -- not merely no format specifier. A
    # percent-encoded target would raise ValueError when this route is requested,
    # which no test of another URL would catch. RedirectView also drops the query
    # string by default, which is right here: nothing meaningful can be passed on to
    # a guide.
    re_path(r'^apiguide.(?P<fmt>pdf)$',
            RedirectView.as_view(url=settings.API_GUIDE_URL, permanent=False)),
    re_path(r'^__help/citing.(?P<fmt>html|pdf)$', api_citing_opus),
]
