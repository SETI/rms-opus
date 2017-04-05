## Import from OPUS 1:

1. Change the settings_local.py at the top "import settings" which databases to read from and build, then:

		sudo -b nohup python import/build_db.py all > ~/import.log.txt

	# follow it:

		tail -f ~/import.log.txt

or a smaller version:

    python import/build_db.py COCIRS_5909,COVIMS_0040,VGISS_8207,COISS_1002,COISS_2068,COISS_2069


2. Update the Image sizes

	sudo -b nohup python import/update_image_sizes.py > ~/img.log

	# you may need:

	select count(*) from images where size_thumb is null or size_thumb = 0 or size_small is null or size_small = 0 or size_med is null or size_med = 0 or size_full is null or size_full = 0 ;


3. Look at the preview image errors

	grep 'Error' ~/img.log | wc -l


5. run the tests on production

	 cd deploy
	 fab tests_prod


4. Dump the database to save it:

	cd ~/dumps/dump_and_sms/
	fab  dump_and_sms


6. Change the DATABASES NAME in settings_local.py


7. Refresh the caches as you would in a [deploy](../deploy/README.md)

    cd deploy
    fab cache_reboot


8. The release is now public! (Yes we have no development server) Manually make sure your most recent blog post links are still working.. (todo: script this!)

    open http://ringsnodesearchtool.blogspot.com/


9. Run the in-browser selenium tests

	they are in Firefox->tools


10. Run the selenium tests:

    In the local repo:

        cd tests
        source venv/bin/activate
        python api_tests.py


11. Do a blog post!

	open http://ringsnodesearchtool.blogspot.com/





---------------------------------------------
to build the NEW schema:

	build_models.py

	takes care of django files too
	so just run build_db.py and that's your db


/// old stuff: ** don't use the fab file **


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
