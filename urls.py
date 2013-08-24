#!/usr/bin/python
# -*- coding: utf-8 -*-

# uncomment maintenance.html line to close the tool

from django.conf.urls.defaults import *

# from django.views.generic import list_detail

from django.conf import settings
from django.contrib import admin
admin.autodiscover()

from paraminfo.models import *

# from django.views.generic.simple import direct_to_template

# -------- OPUS Apps -------------------------------------

# results - getting data

base_urlpatterns = patterns(  # all files one ring_obs_id
                         # all files from search
    'results.views',
    (r'^api/data.(json|zip|html|csv)$', 'getData'),
    (r'^api/detail/(?P<ring_obs_id>\w+).(?P<fmt>[json|zip|html|csv]+)$', 'getDetail'),
    (r'^api/images/(thumb|small|med|full).(json|zip|html|csv)$',
     'getImages'),
    (r'^api/image/(?P<size>[thumb|small|med|full]+)/(?P<ring_obs_id>\w+).(?P<fmt>[json|zip|html|csv]+)$', 'getImage'),
    (r'^api/files/(?P<ring_obs_id>\w+).(?P<fmt>[json|zip|html|csv]+)$',
     'getFiles'),
    (r'^api/files.(?P<fmt>[json|zip|html|csv]+)$', 'getFiles'),
)

# metadata - getting information about a data

base_urlpatterns += patterns(  # returns mult values+counts
                          # returns mult values+counts
                          # indie field info
                          # list of all params
    'metadata.views',
    (r'^api/meta/result_count.(?P<fmt>[json|zip|html|csv]+)$',
     'getResultCount'),
    (r'^api/meta/mults/(?P<slug>[-\sa-zA-Z]+).(?P<fmt>[json|zip|html|csv]+)$', 'getValidMults'),
    (r'^api/meta/range/endpoints/(?P<slug>[-\sa-zA-Z1-9]+).(?P<fmt>[json|zip|html|csv]+)$', 'getRangeEndpoints'),
    (r'^api/fields/(?P<field>\w+).(?P<fmt>[json|zip|html|csv]+)$',
     'getFields'),
    (r'^api/fields.(?P<fmt>[json|zip|html|csv]+)$', 'getFields'),
    (r'^api/category/(?P<category>\w+).(?P<fmt>[json|zip|html|csv]+)$',
     'getCats'),
    (r'^api/categories.(?P<fmt>[json|zip|html|csv]+)$', 'getCats'),
)

    #   (r'^api/meta/histogram/(?P<fmt>[labels|ids]+)/.(?P<fmt>[json|zip|html|csv]+)$', 'getValidMults'),   # returns mult values+counts

# making downloads
base_urlpatterns += patterns('downloads.views',
                        (r'^zip/(?P<ring_obs_ids>\w+).(?P<fmt>[json]+)$', 'create_download'),
                        (r'^collections/download/(?P<collection_name>[default]+).zip$', 'create_download'),
                        (r'^collections/download/info/$',
                        'get_download_info'))

# UI resources - the homepage
base_urlpatterns += patterns(  # (r'^$', direct_to_template, {'template': 'maintenance.html'}),
    'ui.views',
    (r'^$', 'mainSite'),
    (r'^table_headers.html$', 'getDataTable'),
    (r'^menu.html$', 'getMenuLabels'),
    (r'^quick.html$', 'getQuickPage'),
    (r'^forms/widget/(?P<slug>[-\sa-zA-Z0-9]+).(?P<fmt>[json|zip|html|csv]+)$', 'getWidget'),
    (r'^forms/column_chooser.html$', 'getColumnChooser'),
    (r'^api/detailpage/(?P<ring_obs_id>\w+).(?P<fmt>[json|zip|html|csv]+)$', 'getDetailPage'),
    (r'^api/detailquick/(?P<ring_obs_id>\w+).(?P<fmt>[json|zip|html|csv]+)$', 'getDetailQuick'),
)

# guide - app runs guide to  api

base_urlpatterns += patterns('guide.views',
                        (r'^api/$', 'guide'),
                        (r'^api/guide.html$', 'guide'))  # api help pages

# user_collections - all your carts are belong to us

base_urlpatterns += patterns(
    'user_collections.views',
    (r'^collections/(?P<collection>[default]+)/(?P<action>[add|remove|addrange|removerange]+).json$', 'edit_collection'),
    (r'^collections/(?P<collection_name>[default]+)/view.html$',
     'view_collection'),
    (r'^collections/(?P<collection>[default]+)/status.json$',
     'collection_status'),
    (r'^collections/reset.html$', 'reset_sess'),
    (r'^collections/(?P<collection>[default]+)/(?P<action>[addrange|removerange]+)/test.html$', 'edit_collection_range'),
)

# mobile - mobile volumes browser

base_urlpatterns += patterns('mobile.views', (r'^mobile.html$', 'menus'),
                        (r'^mobile/gallery/(?P<volume_id>\w+)/(?P<page>\w+).json$', 'gallery'),
                        (r'^mobile/image/(?P<ring_obs_id>\w+).html$',
                        'image'),
                        (r'^mobile/detail/(?P<ring_obs_id>\w+).html$',
                        'detail'))  # api help pages

# django admin

base_urlpatterns += patterns('', (r'^admin/doc/',
                        include('django.contrib.admindocs.urls')),
                        (r'^admin/', include(admin.site.urls)))  # Uncomment the admin/doc line below and add 'django.contrib.admindocs'

                                                                 # to INSTALLED_APPS to enable admin documentation:
                                                                 # Uncomment the next line to enable the admin:

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
