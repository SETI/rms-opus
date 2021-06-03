# ui/urls.py
from django.conf.urls import url
from django.contrib import admin

from ui.views import (
    api_notifications,
    api_get_menu,
    api_get_widget,
    api_get_metadata_selector,
    api_init_detail_page,
    api_normalize_url,
    api_dummy
)

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^__notifications.json$', api_notifications),
    url(r'^__menu.json$', api_get_menu),
    url(r'^__metadata_selector.json$', api_get_metadata_selector),
    url(r'^__widget/(?P<slug>[-\w]+).html$', api_get_widget),
    url(r'^__initdetail/(?P<opus_id>[-\w]+).html$', api_init_detail_page),
    url(r'^__normalizeurl.json$', api_normalize_url),
    url(r'^__dummy.json$', api_dummy),
    url(r'^__fake/__viewmetadatamodal/(?P<opus_id>[-\w]+).json$', api_dummy),
    url(r'^__fake/__selectmetadatamodal.json$', api_dummy)
]
