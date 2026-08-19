* Run all tests including API tests, DB integrity, internal app tests (but not including result count tests)
        python manage.py test -b

* Run API tests only:
  * Against the internal database (not including result count tests):
        python manage.py test -b api-all
  * Against the production site:
        python manage.py test -b api-livetest-pro api-all
  * Against the dev server:
        python manage.py test -b api-livetest-dev api-all

* Run DB integrity tests only against internal database:
        python manage.py test -b test_db_data.test_local_db_integrity

* Run standalone result counts tests only:
  * Against the internal database (this is not expected to pass unless you have a full local database):
        python manage.py test api-internal-db-result-counts
  * Against the production site:
        python manage.py test api-livetest-pro api-result-counts
  * Against the dev server:
        python manage.py test api-livetest-dev api-result-counts
