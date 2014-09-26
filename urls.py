#!/usr/bin/python
# -*- coding: utf-8 -*-

# uncomment maintenance.html line to close the tool

from django.conf.urls import patterns, url, include

# from django.views.generic import list_detail

from django.conf import settings
from django.contrib import admin
from django.conf.urls import patterns, url, include
admin.autodiscover()

from paraminfo.models import *
from ui.views import main_site
# from django.views.generic.simple import direct_to_template

# -------- OPUS Apps -------------------------------------

# results - getting data

base_urlpatterns = patterns( 'results.views',
    (r'^api/data.(json|zip|html|csv)$', 'getData'),
    (r'^api/detail/(?P<ring_obs_id>[0-9a-zA-Z\-_]+).(?P<fmt>[json|zip|html]+)$', 'getDetail'),
    (r'^api/images/(thumb|small|med|full).(json|zip|html|csv)$','getImages'),
    (r'^api/image/(?P<size>[thumb|small|med|full]+)/(?P<ring_obs_id>\w+).(?P<fmt>[json|zip|html|csv]+)$', 'getImage'),
    (r'^api/files/(?P<ring_obs_id>\w+).(?P<fmt>[json|zip|html|csv]+)$','getFiles'),
    (r'^api/files.(?P<fmt>[json|zip|html|csv]+)$', 'getFiles'),
)


# metadata - getting information about a data
base_urlpatterns += patterns('metadata.views',
    (r'^api/meta/result_count.(?P<fmt>[json|zip|html|csv]+)$', 'getResultCount'),
    (r'^api/meta/mults/(?P<slug>[-\sa-zA-Z]+).(?P<fmt>[json|zip|html|csv]+)$', 'getValidMults'),
    (r'^api/meta/range/endpoints/(?P<slug>[-\sa-zA-Z0-9]+).(?P<fmt>[json|zip|html|csv]+)$', 'getRangeEndpoints'),
    (r'^api/fields/(?P<field>\w+).(?P<fmt>[json|zip|html|csv]+)$','getFields'),
    (r'^api/fields.(?P<fmt>[json|zip|html|csv]+)$', 'getFields'),
    # (r'^api/category/(?P<category>\w+).(?P<fmt>[json|zip|html|csv]+)$','getCats'),
    # (r'^api/categories.(?P<fmt>[json|zip|html|csv]+)$', 'getCats'),
    # (r'^api/meta/histogram/(?P<fmt>[labels|ids]+)/.(?P<fmt>[json|zip|html|csv]+)$', 'getValidMults'),   # returns mult values+counts
)


# making downloads
base_urlpatterns += patterns('downloads.views',
    (r'^zip/(?P<ring_obs_ids>\w+).(?P<fmt>[json]+)$', 'create_download'),
    (r'^collections/download/(?P<collection_name>[default]+).zip$', 'create_download'),
    (r'^collections/download/info/$','get_download_info'))


# UI resources - the homepage
base_urlpatterns += patterns('ui.views',
    # (r'^$', direct_to_template, {'template': 'maintenance.html'}),
    (r'^$', main_site.as_view()),
    (r'^opus/$', main_site.as_view()),
    (r'^table_headers.html$', 'get_table_headers'),
    (r'^browse_headers.html$', 'get_browse_headers'),
    (r'^menu.html$', 'getMenu'),
    (r'^quick.html$', 'getQuickPage'),
    (r'^forms/widget/(?P<slug>[-\sa-zA-Z0-9]+).(?P<fmt>[json|zip|html|csv]+)$', 'getWidget'),
    (r'^forms/column_chooser.html$', 'getColumnChooser'),
    # (r'^api/detailquick/(?P<ring_obs_id>\w+).(?P<fmt>[json|zip|html|csv]+)$', 'getDetailQuick'),
)


# guide - app runs guide to  api
base_urlpatterns += patterns('guide.views',
    (r'^api/$', 'guide'),
    (r'^developer/$', 'guide'),  # api help pages
    (r'^api/guide.html$', 'guide'))  # api help pages


# user_collections - all your carts are belong to us
base_urlpatterns += patterns('user_collections.views',
    (r'^collections/(?P<collection>[default]+)/(?P<action>[add|remove|addrange|removerange]+).json$', 'edit_collection'),
    (r'^collections/(?P<collection_name>[default]+)/view.html$','view_collection'),
    (r'^collections/(?P<collection>[default]+)/status.json$','collection_status'),
    (r'^collections/reset.html$', 'reset_sess'),
    (r'^collections/(?P<collection>[default]+)/(?P<action>[addrange|removerange]+)/test.html$', 'edit_collection_range'),
)


# mobile - mobile volumes browser
base_urlpatterns += patterns('mobile.views',
    (r'^mobile.html$', 'menus'),
    (r'^mobile/gallery/(?P<volume_id>\w+)/(?P<page>\w+).json$', 'gallery'),
    (r'^mobile/image/(?P<ring_obs_id>\w+).html$', 'image'),
    (r'^mobile/detail/(?P<ring_obs_id>\w+).html$', 'detail'))  # api help pages


# django admin
base_urlpatterns += patterns('', (r'^admin/doc/',
                        include('django.contrib.admindocs.urls')),
                        (r'^admin/', include(admin.site.urls)))

if settings.DEBUG:
    base_urlpatterns += patterns('django.views.static',
                            (r'^static_media/(?P<path>.*)$', 'serve', {'document_root': '/Users/lballard/projects/opus/static_media/', 'show_indexes': True}))

# ------------- this is a stupid test ------------------------------------------------------------------------

from django.http import HttpResponse


def test2(request):
    return HttpResponse('dogs')


def testy(request):
    return test2(request)


base_urlpatterns += patterns('', (r'^test$', testy))  # api help pages


urlpatterns = patterns('',
    ('^', include(base_urlpatterns)), # iff you wish to maintain the un-prefixed URL's too
    ('^%s/' % settings.BASE_PATH,  include(base_urlpatterns)),
)
# ------ end test --------
