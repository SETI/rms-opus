## Import from OPUS 1:

Once you've imported the new PDS volumes into the Observations database
using the legacy system (see https://github.com/basilleaf/opus_imports_doc)
use this procedure to import the new volumes into OPUS production:

## On dev:


1. Run build_db.py for the volumes you wish to deploy. This will build an
	 opus-structured database named opus_new_import but with only the volumes listed

	 for new geo import, go ahead and re-import the volumes, it will do a
	 replace into

 			sudo -b nohup python import/build_db.py COUVIS_0057,COISS_2108,COISS_2109,COVIMS_0084,COVIMS_0085,COVIMS_0086 > ~/import.log.txt

	Check it out:

			call vols('opus_new_import.obs_general');

- Update Image Sizes

	this will update image file sizes in the new volumes db only

		sudo -b nohup python update_image_sizes.py > ~/img.log

 	If you need to look at the preview image errors

		grep 'Error' ~/img.log | wc -l

- Use import_new_volumes.py to import the volumes from step 1 from the
	 opus_new_import into opus db local

	 	sudo python import_new_volumes.py

	Check it out:

			call vols('opus.obs_general');
			call vols('opus.images');

- Drop all the cache tables in opus db locally

		python drop_cache_tables.py

- run the tests

		 cd deploy
		 fab cache_reboot tests


## 	If tests all pass on dev, the next steps describe how to deploy to production

1. Transfer the new data to production

		cd import
		fab dump transfer build import_new_volumes

- drop all cache tables production

		fab drop_all_cache_tables


- Refresh the caches as you would in a [deploy](../deploy/README.md)

	Locally:

		cd deploy
		fab cache_reboot tests



- The release is now public! (Yes we have no development server) Manually make sure your most recent blog post links are still working.. (todo: script this!)

    open http://ringsnodesearchtool.blogspot.com/


- Run the in-browser selenium tests

	they are in Firefox->tools


- Run the selenium tests:

    In the local repo:

        cd tests
        source venv/bin/activate
        python api_tests.py


- Do a blog post!

	open http://ringsnodesearchtool.blogspot.com/

- Take a backup of opus on dev

		mysqldump opus --opt > opus.deploy.date.sql -p
