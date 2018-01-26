## How the Apps are Organized:

### search

This is the search api, where the querying of mission data happens. Methods in here perform all user data queries, and handle the different types of queries (range, multi-choice, longitude, etc). Includes creating/editing of user cache tables (cache_\*) which are representations of query results. 

### metadata

handles the metadata for the feedabck hinting in the user interface, these are things that change wrt the query being performed: range endpoints and mult hinting (green numbers), null counts, total result counts. 

### paraminfo

Static information about every searchable parameter, such as data type, label, default widget, query type, etc..

### results

handles the returning of result sets, whether it's tablular data returned to display the results or gallery tab, or json/csv data returned by API calls. 

### ui

Views that drive the OPUS user interface, this is where html is created for interface components, such as widgets, menus, gallery templates etc. Most templates for the entire ui are in ui/templates.

### guide

An API guide, a guide to the underlying http endpoints that are publicly available. This is for people using the API for querying opus from script or command line. 

### dictionary 

This app feeds content to the 'read more' and 'more info' links that appear throughout the tool.

### user_collections

User collections aka the shopping cart methods, methods that edit and create the cart. 

### downloads

These methods handle the preparing of zip files and download links at the point where a user moves to download their cart. It collects files found in the cart, creates manifest files, and creates zipped files for users to download. See the user_collections app for methods related to editing cart contents. 

### metrics

User metrics data model, and the method that edit/update data in that model. 

### tools

A few utilities or helpers that are used throughout the project. 


