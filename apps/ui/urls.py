# ui/urls.py
from django.conf.urls import url
from ui.views import (
    about,
    get_table_headers,
    get_browse_headers,
    getMenu,
    getQuickPage,
    getWidget,
    getColumnChooser,
    init_detail_page
)

urlpatterns = [
    url(r'^about/$', about),
    url(r'^table_headers.html$', get_table_headers),
    url(r'^browse_headers.html$', get_browse_headers),
    url(r'^menu.html$', getMenu),
    url(r'^forms/widget/(?P<slug>[-\sa-zA-Z0-9]+).(?P<fmt>[json|zip|html|csv]+)$', getWidget),
    url(r'^forms/column_chooser.html$', getColumnChooser),
    url(r'^api/detail/(?P<ring_obs_id>[0-9a-zA-Z\-_]+).(?P<fmt>[json|zip|html]+)$', init_detail_page),
]
