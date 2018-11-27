# File structure:
* opus/application/test_api
  * api_for_test_cases: directory to save testing params for test cases
    * api_*.py: api for each test case if needed, it's named the same as the corresponding test
  * test_*.py: files for test cases
  * enable_*.py: files for enabling live test against either production or dev sites

# Install rest framework
  * pip install djangorestframework

# Run api test with manage.py:
* Run all tests against the app including db search test
  * python manage.py test -s -v 2
* Run api tests:
  * against app:
    * python manage.py test -s -v 2 app
  * against production site:
    * python manage.py test -s -v 2 live-pro
  * against dev site:
    * python manage.py test -s -v 2 live-dev

# Re-import test db:
* go to opus/application/import
* python main_opus_import.py --do-it-all COISS_2002,COISS_2008,COISS_2111,COUVIS_0002,GO_0017,VGISS_6210,VGISS_8201,HSTI1_2003



python import_dictionary.py
mysql -u root -p test_dictionary < contexts.sql


 talk about what you’ve learned about how Django tests work. How it finds tests to run, how you simulate API calls, etc.
