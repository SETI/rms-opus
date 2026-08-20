# cart/urls.py
from django.urls import re_path

from opus_app.apps.cart.views import (
    api_cart_status,
    api_create_download,
    api_edit_cart,
    api_get_cart_csv,
    api_reset_session,
    api_view_cart,
)

urlpatterns = [
    re_path(r'^__cart/view.json$', api_view_cart),
    re_path(r'^__cart/status.json$', api_cart_status),
    re_path(r'^__cart/data.csv$', api_get_cart_csv),
    re_path(r'^__cart/(?P<action>add|remove|addrange|removerange|addall).json$', api_edit_cart),
    re_path(r'^__cart/reset.json$', api_reset_session),
    re_path(r'^__cart/download.json$', api_create_download),
    re_path(r'^api/download/(?P<opus_id>[-\w]+).(?P<fmt>zip|tar|tgz)$', api_create_download),
    re_path(r'^__api/download/(?P<opus_id>[-\w]+).(?P<fmt>zip|tar|tgz)$', api_create_download),
]
