## Import from OPUS 1:

Once you've imported the new PDS volumes into the Observations database
using the legacy system (see https://github.com/basilleaf/opus_admin)
use this procedure to import the new volumes into OPUS production:

## On dev:


1. Run build_db.py for the volumes you wish to deploy. This will build an
	 opus-structured database named opus_new_import but with only the volumes listed

	 for new geo import, go ahead and re-import all impacted volumes,
	 (this uses 'replace into')

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
	..running this script directly operates on the local database:
	..later it is run in a fab file and that acts on the remote database

		sudo python drop_cache_tables.py

- run the tests
	NOTE: this is run on local machine for now, pds-dev not happy

		 cd ../deploy
		 fab cache_reboot tests

- run the api endpoint tests

		cd ../tests
		python api_tests.py


## 	If tests all pass on dev, the next steps describe how to deploy to production

1. Transfer the new data database to production
	 ..this is run on pds-dev, it only operates one way, from pds-dev to pds-tools

	 Note: if you get paramiko errors here, activate the virtualenv in opus_admmin/import

		cd import
		fab dump transfer build import_new_volumes

- maybe take a look here at opus in pds-tools database:

	use opus;
	call vols('obs_general');
	call vols('images');

	you should see the new volumes there.

- look good? time to deploy:
	maybe make sure nobody is using opus at the moment (apache access logs)
	and then:

	drop all cache tables production
	..this is run on pds-dev, it only operates one direction, from pds-dev to pds-tools
	  so this will drop all cache tables on pds-tools

		fab drop_all_cache_tables


- Refresh the caches as you would in a [deploy](../deploy/README.md)

	Locally (laptop):

		cd deploy
		fab cache_reboot tests


- The release is now public! Manually make sure your most recent blog post links are still working.. (todo: script this!)

    open http://ringsnodesearchtool.blogspot.com/


- Run the API endpoint tests:

    In the local repo or anywhere:

        cd tests
        source venv/bin/activate
        python api_tests.py


- Do a blog post!

	open http://ringsnodesearchtool.blogspot.com/

- Take a backup of opus on dev

		mysqldump opus --opt > opus.deploy.date.sql -p
