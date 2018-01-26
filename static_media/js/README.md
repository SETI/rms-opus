# The Javascript Front End

OPUS is a single page app written in vanilla javascript with jQuery. There is no framework to handle changes, so there's a lot of code for keeping track of UI elements that change with changing data.

The scripts are divided into subject areas, or areas of the interface. The areas are Search, Browse (which includes Gallery and Table) and Detail. Each script defines a namespace for methods in that script. Each of the namespace objects begin with a method that define all behaviors for the components in that namespace, followed by methods that perform actions.

## opus.js

This script contains the "opus" object and all the document.ready() init functions go here. The opus object contains all variables that need to be tracked globally for the entire application, as well as the main load() loop.

When user makes any change to the interface, such as changing a query, the load() will send an ajax request to the server to get information it needs to update any other components in the application, such as the result count, result hinting (green numbers), results tab changes etc. Load is set on an interval timer, it watches for changes to the URL hash to know whether to fire an ajax call and initiate re-rendering or updating of the user interface. It's also where all behaviors for all other apps are initiated on load.

## hash.js

Defines the o_hash object. Every change a user makes causes a hash update. (This is how you can bookmark any point in your session and share it as a permalink) This object contains all things about keeping track of and updating the URL hash. Things like updating the hash with user query changes, getting the current hash (usually used for sending hash info back to server in ajax calls), getting the search query out of the current hash, initiating a search based on starting with a hash (aka permalinks).

## browse.js

Defines the o_browse object. All the things that happen on the browse tab, such as rendering the gallery or table view, handling clicks of thumbnails and thumbnail tool links, displaying larger images (colorbox) and metadata box, adding range selections, toggling gallery vs table view, results tab pagination, the column chooser interface, the infinite scroll handling.

## collections.js

Defines the o_collections object. All things having to do with a user collection, adding to cart, editing collection, collections tab interface behaviors, fetching and displaying download links, deleting a collection.

## detail.js

Defines the o_detail object. Rendering the Detail tab. Not much interaction on that tab so this is just a fetch/display method.

## menu.js

Defines the o_menu object. This builds the menu that contains the categories and search params that are displayed on the search tab, and also in the column chooser.

## search.js
Defines the o_search object. Renders the search tab itself, and handles requests for the widget hinting (range endpoints, mult counts.. aka green numbers) Widgets themselves have their own script widgets.js (and these two could probably be combined.)

## widgets.js
Defines the o_widgets object. All widget behaviors such as fetching/rendering widgets, closing/opening, grouping in group widgets, adjust width/height/scrolls.  

## utils.js

Defines the o_utils object. Just a couple of utility helper methods used throughout the app, such as areObjectsEqual and addCommas.
