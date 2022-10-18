from django.urls import re_path

from django.contrib.staticfiles.storage import staticfiles_storage
from django.views.generic.base import RedirectView

# from dictionary.views import (
#     api_get_definition_list,
#     api_search_definitions,
#     api_display_definitions,
#     api_display_definition,
# )

urlpatterns = [
    #     # List all definitions that start with a given letter.
    #     # Requires ?alpha=<letter>
    #     re_path(r'^list.json$', api_get_definition_list, name='list'),

    #     # Search for a given term anywhere in the definitions.
    #     # Requires ?term=<term>
    #     re_path(r'^search.json$', api_search_definitions, name='search'),

    #     # Display all definitions with an alpha bar
    #     re_path(r'^$', api_display_definitions, name='definitions'),
    #     re_path(r'^definitions.html^$', api_display_definitions, name='definitions'),

    #     # Display a single definition. Requires ?term=<term>
    #     re_path(r'^definition.html$', api_display_definition, name='definition'),
    re_path(r'^favicon.ico$',
        RedirectView.as_view(
            url=staticfiles_storage.url('favicon.ico'),
            permanent=False),
        name='favicon'),
]
