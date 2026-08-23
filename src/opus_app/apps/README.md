# Apps

The server side python code is organized into subject area "apps" as follows:

## search
Everything about performing queries against the mission data itself, based on user selections in the search tab interface, or GET vars passed directly to API endpoints.

## results
everything about returning results sets, wether its fetching tabular data or thumbnail galleries. Used for rendering the results tab table and downloadable CSV files.

## metadata
Endpoints and methods that provide metadata about the user defined result set: the result count, mult widget value counts, range endpoints.

## ui
html ui components are generated here. The menu, tabs, widget columns, browse headers, gallery html, anything you visually see that gets populated with data can be found in here. This is where most all the templates in the project live.

## guide
a simple app to render and maintain our public API guide page.

## cart
Everything to do with users creating "cart" aka the shopping cart. Initiating a cart, adding/editing the cart. Displaying the contents.   

## downloads
Creating downloadable zip files, fetching and zipping and making manifest files.

## metrics
counting unique users and query activity for metrics reporting

## tools
A small number of utilities or helpers that are used throughout the project. This
includes `dictionary.py`, which holds the two models for the database-backed dictionary
(an extendable version of the PDS Data Dictionary, populated by the import pipeline) and
the tooltip lookup that supplies the content behind the UI's 'info' icons. Until the
Django 5.2 upgrade those lived in a `dictionary` app of their own, whose browsable
dictionary site had already been removed.
