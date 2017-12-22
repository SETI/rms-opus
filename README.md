## run all the tests

    REUSE_DB=1 python manage.py test apps -x


## Install

• create a virtualenv, activate it, and install the dependencies

    virtualenv --python=/usr/local/bin/python2.7 venv --distribute
    source venv/bin/activate
  	pip install -r requirements.txt


• create the mysql databases

  	 # opus requires 3 databases which are not included in this repo.

     create database opus_small;  
     create database dictionary;
     create database opus_metrics;

• build the databases

    mysql opus_small < opus_small.sql -p  # ask Rings Node
    mysql dictionary < dictionary.sql -p
    mysql opus_metrics < opus_metrics.sql -p

• edit the config files

  - edit both settings_local.py and secrets.py

• Run the tests

	 REUSE_DB=1 python manage.py test apps

  Note the tests run against the same database as the app.
  To run the tests for the first time you will need to run migrate:

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
