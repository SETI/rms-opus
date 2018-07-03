detail.html - The top of the detail tab (not including any actual metadata). Used in ui/views.py::init_detail_page

detail_metadata.html - The rest of the detail tab (the metadata under each heading). Used in results/views.py::api_get_metadata and _get_metadata_by_slugs

gallery.html - A series of images with overlays for details, selection, and expanded view. Used in results/views.py:get_images






main.html - pass javascript vars here

base.html - no layout, headers and libs

base_opus.html - banner, tabs, footer

gallery.html - the thumbnail gallery






quick_page.html - basic simplified search page (mock)







not used:

base_debug.html - extend this instead of base.html, same as base.html but adds a debug div at bottom

menu.html - this is just a print out of the categories, groups, and param_names, todo: extend to api
