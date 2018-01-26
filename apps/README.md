## How the Apps are Organized:

### search

This is the search api, it performs all user data queries, and handles the different types of queries (range, multi-choice, longitude, etc).

### metadata

handles the metadata for the feedabck hinting the user sees in the interface, things that change wrt the query being performed: range endpoints and mult hinting (green numbers), nulls counts, total result counts. 

### paraminfo

Static information about every searchable parameter (data type, label, default widget, query type, etc..)

### results

handles returning result sets, like data tables/csv, or gallery data. 

### ui

Views that drive the OPUS user interface, this is where html is created for a lot of interface components, such as widgets, menus, gallery templates and the like. Most templates for the application are in ui/templates.

### guide

An API guide, for people using the API for querying opus from script or command line





