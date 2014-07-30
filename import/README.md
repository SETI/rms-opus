# hold up, this is all changed, currently working on:

run in this order:
build_db.py
build_models.py

to build the NEW schema

takes care of django files too
so just run build_db.py and that's your db


/// old stuff:


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

- then build the opus 2 database:

```
cd import
fab -H lballard@pds-rings-tools.seti.org build_opus2:volumes=COISS_2060\,NHJULO_1001\,COCIRS_5403

# or

cd import
fab -H lballard@pds-rings-tools.seti.org build_opus2:volumes=all > log.txt

```
The fab file does the following on the server specified on the command line:

1.  generates the django models for the 'search' app at search/models.py by reading tables from OPUS1

-  django uses the search/models.py spec to generate the OPUS2 table schema.

-  rmakes it's own custom text dump of the OPUS1 database



- then import the data

```
fab -H lballard@pds-rings-tools.seti.org import_data:volumes=COISS_2060\,NHJULO_1001\,COCIRS_5403

# or

fab -H lballard@pds-rings-tools.seti.org import_data:volumes=all > log.txt

```



- To deploy, be sure and reset the memcached, kill what is currently running then issue the same commands again, find them like so:

```
ps aux | grep memcache
```

- you might need this:


```
DELIMITER //
CREATE PROCEDURE `vols` (IN my_table VARCHAR(200))
BEGIN
    SET @sql = CONCAT('SELECT volume_id,count(*) FROM ',my_table,' group by volume_id order by volume_id');
    PREPARE s1 from @sql;
    EXECUTE s1;
END //
DELIMITER ;
```

