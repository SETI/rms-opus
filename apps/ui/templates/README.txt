choose_columns.html - Displays the column choose modal dialog. Used in ui/views.py::get_column_chooser

detail.html - The top of the detail tab (not including any actual metadata). Used in ui/views.py::init_detail_page

detail_metadata.html - The rest of the detail tab (the metadata under each heading). Used in results/views.py::api_get_metadata and _get_metadata_by_slugs

gallery.html - A series of images with overlays for details, selection, and expanded view. Used in results/views.py:get_images

menu.html - The search page side menu including all sub-menus. This is also used for "choose columns". Used in ui/views.py::get_menu

table_headers.html - The header for the "view table" browse mode. Used in 


main.html - pass javascript vars here

base.html - no layout, headers and libs

base_opus.html - banner, tabs, footer

gallery.html - the thumbnail gallery






quick_page.html - basic simplified search page (mock)







not used:

base_debug.html - extend this instead of base.html, same as base.html but adds a debug div at bottom

menu.html - this is just a print out of the categories, groups, and param_names, todo: extend to api
