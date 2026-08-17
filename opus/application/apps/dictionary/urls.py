from django.contrib.staticfiles.storage import staticfiles_storage
from django.urls import re_path
from django.views.generic.base import RedirectView

urlpatterns = [
    re_path(r'^favicon.ico$',
        RedirectView.as_view(
            url=staticfiles_storage.url('favicon.ico'),
            permanent=False),
        name='favicon'),
]
