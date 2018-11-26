# Run test with manage.py
* Run all tests against the app
  * python manage.py test -s -v 2
* Run api tests:
  * against app:
    * python manage.py test -s -v 2 app
  * against production site:
    * python manage.py test -s -v 2 live-pro
  * against dev site:
    * python manage.py test -s -v 2 live-dev
