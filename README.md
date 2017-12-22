## run all the tests

    REUSE_DB=1 python manage.py test apps


## Install

• install the dependencies

  	pip install -r requirements.txt


• build the databases (which are not in this repo)

  opus requires its 3 databases:

   opus (or opus_small)

   dictionary

   opus_metrics


• Run the tests

	 REUSE_DB=1 python manage.py test apps

  The tests run against the same database as the production app.
  To run the tests for the first time after installing,
  you will need to run migrate:

  	python manage.py migrate

If you are starting with a dump of an opus database, you might need to drop the following tables for the migrate to work:

	  drop table django_admin_log;
	  drop table django_content_type;
	  drop table django_session;
	  drop table django_site;


## Dependencies

see requirements.txt

memcached daemon must be running on production server OR if it's not then comment out the cache_backend line in settings.py

see also apps/README.md (probably deprecated)

some possibly useful tidbits are also in the /doc directory )
