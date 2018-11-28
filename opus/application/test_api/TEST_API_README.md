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

# Re-import opus_small:
* go to opus/application/import
* python main_opus_import.py --do-it-all COISS_2002,COISS_2008,COISS_2111,COUVIS_0002,GO_0017,VGISS_6210,VGISS_8201,HSTI1_2003

# Import dictionary for test db: (our app didn't run the test against test db)
* in opus_secret.py: DICTIONARY_SCHEMA_NAME = 'test_dictionary'
* under pds-opus/dictionary/import: python import_dictionary.py
* mysql -u root -p test_dictionary < contexts.sql
* DICTIONARY_SCHEMA_NAME = 'dictionary'
* run the test

# How Django test work:
When running python manage.py test, Django looks for TEST_RUNNER to know what to do next, generally it has the following steps:
1. Performing global pre-test setup.
2. Looking for tests in any file below the current directory whose name matches the pattern test*.py.
  * any class that is a unittest.TestCase subclass would be collected as well
3. Creating the test databases. (seems like our app is not testing against test db)
4. Running migrate to install models and initial data into the test databases.
5. Running the system checks.
6. Running the tests that were found.
7. Destroying the test databases.
8. Performing global post-test teardown.

# How we simulate API call:
* RequestsClient(): use to test against the app
* requests.Session(): use to test against live sites, produciton and dev


 talk about what you’ve learned about how Django tests work. How it finds tests to run, how you simulate API calls, etc.
