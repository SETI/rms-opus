# ui/urls.py
from django.conf.urls import url
from django.contrib import admin
from django.conf.urls.static import static
from django.conf.urls import include
from django.conf import settings
from django.contrib.staticfiles.storage import staticfiles_storage
from django.views.generic.base import RedirectView

from ui.views import (
    api_about,
    get_table_headers,
    get_browse_headers,
    get_menu,
    api_get_widget,
    get_column_chooser,
    api_init_detail_page
)

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^about/$', api_about),
    url(r'^__table_headers.html$', get_table_headers),
    url(r'^__browse_headers.html$', get_browse_headers),
    url(r'^__menu.html$', get_menu),
    url(r'^__forms/widget/(?P<slug>[-\w]+).(?P<fmt>[json|zip|html|csv]+)$', api_get_widget),
    url(r'^__forms/column_chooser.html$', get_column_chooser),
    url(r'^__initdetail/(?P<opus_id>[-\w]+).html$', api_init_detail_page),
    url(r'^favicon.ico$',
        RedirectView.as_view(
            url=staticfiles_storage.url('favicon.ico'),
            permanent=False),
        name="favicon"
    ),
]
