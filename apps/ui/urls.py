# ui/urls.py
from django.conf.urls import url
from django.contrib import admin
from django.conf.urls.static import static
from django.conf.urls import include
from django.conf import settings
from ui import views
import dictionary


from ui.views import (
    about,
    definitions,
    home,
    get_table_headers,
    get_browse_headers,
    getMenu,
    getWidget,
    getColumnChooser,
    init_detail_page
)

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^$', views.home),
    url(r'^about/', about),
    url(r'^definitions/$', definitions),
    url(r'^table_headers.html$', get_table_headers),
    url(r'^browse_headers.html$', get_browse_headers),
    url(r'^menu.html$', getMenu),
    url(r'^forms/widget/(?P<slug>[-\sa-zA-Z0-9]+).(?P<fmt>[json|zip|html|csv]+)$', getWidget),
    url(r'^forms/column_chooser.html$', getColumnChooser),
    url(r'^api/detail/(?P<ring_obs_id>[0-9a-zA-Z\-_]+).(?P<fmt>[json|zip|html]+)$', init_detail_page),
    url(r'^dictionary/', include('dictionary.urls')),
]
