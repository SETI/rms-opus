## run all the tests

    REUSE_DB=1 python manage.py test apps

best to create the test database manually:

    mysqldump opus_small --opt > opus_small.sql
    mysql test_opus_small < opus_small.sql



## Dependencies

see requirements.txt

memcached daemon must be running on server OR if it's not then comment out the cache_backend line in settings.py

see also apps/README.md 

some useful tidbits are also in the /doc directory





