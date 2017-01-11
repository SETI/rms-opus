# urls.py
from paraminfo.models import *
from django.conf.urls import url, include
from django.conf import settings
from django.contrib import admin
from django.views.generic import TemplateView

admin.autodiscover()

from ui.views import main_site

# UI resources - the homepage - ui.views
urlpatterns = [
    url(r'^$', main_site.as_view()),
    url(r'^opus/$', main_site.as_view()),

    url(r'^', include('ui.urls')),
    url(r'^', include('results.urls')),
    url(r'^', include('metadata.urls')),
    url(r'^', include('downloads.urls')),
    url(r'^', include('guide.urls')),
    url(r'^', include('user_collections.urls')),

]

# django admin
"""
urlpatterns += patterns('',
    (r'^admin/doc/',
                        include('django.contrib.admindocs.urls')),
                        (r'^admin/', include(admin.site.urls)))
"""

"""
if settings.DEBUG:
    urlpatterns += [
        (r'^static_media/(?P<path>.*)$', 'serve', {'document_root': '/Users/lballard/projects/opus/static_media/', 'show_indexes': True})
    ]

"""

"""
urlpatterns = patterns('',
    ('^', include(base_urlpatterns)), # iff you wish to maintain the un-prefixed URL's too
    ('^%s/' % settings.BASE_PATH,  include(base_urlpatterns)),
)
"""
