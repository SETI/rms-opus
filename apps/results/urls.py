# results/urls.py
from django.conf.urls import url
from results.views import (
    getData,
    getImages,
    getImage,
    getFilesAPI,
    get_metadata,
    get_csv,
)
# results - getting data
urlpatterns = [
    url(r'^api/data.url(json|zip|html|csv)$', getData),
    url(r'^api/images/url(thumb|small|med|full).url(json|zip|html|csv)$',getImages),
    url(r'^api/image/url(?P<size>[thumb|small|med|full]+)/url(?P<ring_obs_id>[0-9a-zA-Z\-_]+).url(?P<fmt>[json|zip|html|csv]+)$', getImage),
    url(r'^api/files/url(?P<ring_obs_id>[0-9a-zA-Z\-_]+).url(?P<fmt>[json|zip|html|csv]+)$',getFilesAPI),
    url(r'^api/files.url(?P<fmt>[json|zip|html|csv]+)$', getFilesAPI),
    url(r'^api/metadata/url(?P<ring_obs_id>[0-9a-zA-Z\-_]+).url(?P<fmt>[json|html]+)$', get_metadata),
    url(r'^collections/data.csv$',get_csv),
]
