### Database Schema and Caching Strategies

There is a big flat table in the OPUS 2 database (minus all the surface geometry fields) but it is not used for search queries. It's used as a tool for displaying the data as an html table. It is a way to return data quickly, not to search it. It provides a big easy target for fetching rows we already know we want.

The actual tables used for searching look like this:

     obs_CO
     obs_CO_COCIRS
     obs_CO_COISS
     obs_GO
     obs_GO_GOSSI
     obs_VG
     obs_VG_VGISS
     obs_CO_COVIMS
     obs_NH
     obs_NH_NHJULO

There is a bit of de-normalization in the collection of tables that are used for search queries, evident in how they are named. During a user's search these tables are joined together by joins and by UNION queries when needed (UNION to provide cross mission/instrument searching).

The Big Table is a collection of all fields from the tables above, and does not include fields from the surface geometry tables. Since  surface geometry tables are sharded into separate targets, they are stored as separate tables and are joined in when the user wants them, they look like this:

    obs_surface_geometry__aegaeon
    obs_surface_geometry__albiorix
    obs_surface_geometry__anthe
    obs_surface_geometry__atlas
    obs_surface_geometry__… etc ..


Here is how the Big denormalized table comes into play:

Every observation in the database has a unique ID. When a user issues a search, a single-column table of unique IDs is created in a separate 'cache' database that correspond to the result rows for that search. In this way I am using MySQL as a cache layer, to make common searches quicker and so it remembers what queries it has done before, and can just return the IDs of the results when asked again, rather than repeating sometimes complicated or sweeping queries on data that hasn't changed. We get to do this because our data doesn't change between releases. This technique has been in use in OPUS 1 for several years, seems to be working well for us, so I implemented the same technique in OPUS 2.

When user wants to browse the results of their search, the cache table of IDs is joined with the Big table for fetching the data fields from it, and if there is a surface geometry table constrained or selected in 'column chooser' that table is joined into the query as well. There are no range queries or search queries of any kind against this table, only a speedy foreign key join with the single-column search result table.

The big flat table is not really as part of the actual OPUS schema, it's part of a caching technique to speed things up and ease the technical debt of more and more scripted parts. If we were to release the OPUS database publicly, that table would not be a part of it.
