## Dependencies

see requirements.txt

memcached daemon must be running on server OR if it's not then comment out the cache_backend line in settings.py

see also the doc/ directory


## This is how the project is organized into separate apps:

### search

this is the api that does all the querying of the database for searching

### metadata

information about the data, range endpoints, nulls, total result counts, etc

### paraminfo

information about every searchable parameter (type, default widget, how to query etc..)

### results

handles returning results

### ui

drives the OPUS user interface

### guide

a guide for using the API for querying opus from script or command line





