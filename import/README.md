# Once you deploy a database to OPUS 1 this procedure will magically update OPUS 2 with the same data.

1. backup the opus databased to a dump file

```
mysqldump --opt opus > opus.sql -p
```

- make database backup copies of a few utility tables

```
mysql opus < backup_util_tables.sql -p -v
```

- rsync local to pds-tools at ~/lballard/opus

```
git push
sudo bash -v deploy/deploy_opus_local.bash
```

- then run the fab file:

```
cd import
fab -H lballard@pds-rings-tools.seti.org deploy_opus2:volumes=COISS_2060\,NHJULO_1001\,COCIRS_5403

# or

cd import
fab -H lballard@pds-rings-tools.seti.org deploy_opus2:volumes=all

```
The fab file does the following on the server specified on the command line:

1.  generates the django models for the 'search' app at search/models.py by reading tables from OPUS1

-  django uses the search/models.py spec to generate the OPUS2 table schema.

-  rmakes it's own custom text dump of the OPUS1 database

-  imports the text dump into the OPUS2 schema


To deploy, be sure and reset the memcached, kill what is currently running then
issue the same commands again, find them like so:

```
ps aux | grep memcache
```


