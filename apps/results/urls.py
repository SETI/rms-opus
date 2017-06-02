# results/urls.py
from django.conf.urls import url
from results.views import (
    getData,
    getImages,
    getImage,
    getFilesAPI,
    get_metadata,
    get_csv,
    get_categories,
)
# results - getting data
urlpatterns = [
    url(r'^api/data.(json|zip|html|csv)$', getData),
    url(r'^api/images/(thumb|small|med|full).(json|zip|html|csv)$',getImages),
    url(r'^api/image/(?P<size>[thumb|small|med|full]+)/(?P<ring_obs_id>[0-9a-zA-Z\-_]+).(?P<fmt>[json|zip|html|csv]+)$', getImage),
    url(r'^api/files/(?P<ring_obs_id>[0-9a-zA-Z\-_]+).(?P<fmt>[json|zip|html|csv]+)$',getFilesAPI),
    url(r'^api/files.(?P<fmt>[json|zip|html|csv]+)$', getFilesAPI),
    url(r'^api/metadata/(?P<ring_obs_id>[0-9a-zA-Z\-_]+).(?P<fmt>[json|html]+)$', get_metadata),
    url(r'^api/categories.json$', get_categories),
    url(r'^collections/data.csv$',get_csv),
]
