### Querying data

When a user does a search, the metadata is queried and then a single column table of ids is made that matches the user's query results. This column of result ids is used for subsequent queries against the set. Queries are logged and these tables are re-used when the same query is issued again, until the database
is re-deployed and all these tables are destroyed.

a query comes through as param=value.