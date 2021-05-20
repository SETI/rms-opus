# cart/urls.py
from django.conf.urls import url
from cart.views import (
    api_view_cart,
    api_cart_status,
    api_get_cart_csv,
    api_edit_cart,
    api_reset_session,
    api_create_download
)

urlpatterns = [
    url(r'^__cart/view.json$', api_view_cart),
    url(r'^__cart/status.json$', api_cart_status),
    url(r'^__cart/data.csv$', api_get_cart_csv),
    url(r'^__cart/(?P<action>add|remove|addrange|removerange|addall).json$', api_edit_cart),
    url(r'^__cart/reset.json$', api_reset_session),
    url(r'^__cart/download.json$', api_create_download),
    url(r'^api/download/(?P<opus_id>[-\w]+).(?P<fmt>zip|tar|tgz)$', api_create_download),
    url(r'^__api/download/(?P<opus_id>[-\w]+).(?P<fmt>zip|tar|tgz)$', api_create_download),
]
