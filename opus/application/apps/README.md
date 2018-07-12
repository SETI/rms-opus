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

## dictionary
connects a database named dictionary that is an extendable version of the PDS Data Dictionary, provides content for 'info' icons and 'get more info' links

## user_collections
Everything to do with users creating "collections" aka the shopping cart. Initiating a collection, adding/editing the cart. Displaying the contents.   

## downloads
Creating downloadable zip files, fetching and zipping and making manifest files.

## metrics
counting unique users and query activity for metrics reporting 

## tools
A small number of utilities or helpers that are used throughout the project.
