# Run api test with manage.py:
* Run all tests against the app including db search and every test in Django app
  * python manage.py test -s -v 2
* Run api tests:
  * against internal database:
    * python manage.py test -s -v 2 api-internal-db
  * against production site:
    * python manage.py test -s -v 2 api-live-pro
  * against dev site:
    * python manage.py test -s -v 2 api-live-dev
