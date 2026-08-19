### Search App

This is the main place where searching the data and facilitating the user's
exploring the data itself is handled.

It also handles the way the interface keeps track of user-defined result sets:

  When a user does a search, the PDS data is queried and then a single column
  table of ids is made that matches the user's query results. This column of
  result ids is used for subsequent queries against the set. Queries are logged
  and these tables are re-used when the same query is issued again.
