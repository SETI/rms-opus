### Search App

This is the main place where searching the data and facilitating the user's
exploring the data itself is handled.

It also handles the way the interface keeps track of user-defined result sets:

  When a user does a search, it is registered in the `user_searches` table, and
  the first request for it queries the PDS data and writes the ids of the matching
  observations, in sort order, into the `search_results` table under the search's
  id. Those rows are used for subsequent queries against the set, and are re-used
  whenever the same query is issued again, until `opus_manage prune` removes the
  search.
