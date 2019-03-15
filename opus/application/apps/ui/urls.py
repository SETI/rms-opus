# ui/urls.py
from django.conf.urls import url
from django.contrib import admin
from django.contrib.staticfiles.storage import staticfiles_storage
from django.views.generic.base import RedirectView

from ui.views import (
    api_last_blog_update,
    api_get_table_headers,
    api_get_browse_headers,
    api_get_menu,
    api_get_widget,
    api_get_metadata_selector,
    api_init_detail_page,
    api_normalize_url
)

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^__lastblogupdate.json$', api_last_blog_update),
    url(r'^__browse_headers.html$', api_get_browse_headers),
    url(r'^__table_headers.html$', api_get_table_headers),
    url(r'^__menu.html$', api_get_menu),
    url(r'^__forms/widget/(?P<slug>[-\w]+).html$', api_get_widget),
    url(r'^__forms/metadata_selector.html$', api_get_metadata_selector),
    url(r'^__initdetail/(?P<opus_id>[-\w]+).html$', api_init_detail_page),
    url(r'^__normalizeurl.json$', api_normalize_url)
]
