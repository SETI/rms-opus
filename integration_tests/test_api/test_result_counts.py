"""Compare result counts against a recorded table of them.

The recorded counts are in `data/result_counts.csv`. They are counts over the whole
archive rather than over whatever this installation imported, so the comparison only
runs when something says which archive to ask.

`api-result-counts` is the verb that selects this module, and on its own it checks
nothing: both flags are off and the guard around the comparison is false. It is
combined with a verb that sets one -- `manage.py test api-livetest-pro
api-result-counts` for the public server, `api-livetest-dev` for the development one
(see TEST_API_README.md) -- or replaced by `api-internal-db-result-counts`, which
selects this module and sets the internal-database flag by itself.
"""

import csv
import json
import logging
from unittest import TestCase

import requests
from django.conf import settings
from rest_framework.test import RequestsClient

from .api_test_helper import go_live_target


##################
### Test cases ###
##################
class APIResultCountsTests(TestCase):
    """Result counts for each recorded search, checked against `result_counts.csv`."""

    filename = "integration_tests/test_api/data/result_counts.csv"

    # disable error logging and trace output before test
    def setUp(self) -> None:
        """Turn off fault injection and error logging for one test.

        The `OPUS_FAKE_*` knobs are turned all the way up by other tests and are global,
        so every suite resets them; a suite that did not would see its own API calls
        fail at random.

        It also gives the cache a key prefix of this run's own schema.
        """
        self.maxDiff = None
        settings.OPUS_FAKE_API_DELAYS = 0
        settings.OPUS_FAKE_SERVER_ERROR404_PROBABILITY = 0
        settings.OPUS_FAKE_SERVER_ERROR500_PROBABILITY = 0
        settings.CACHE_KEY_PREFIX = 'opustest:' + settings.DB_SCHEMA_NAME
        logging.disable(logging.DEBUG)

    # enable error logging and trace output after test
    def tearDown(self) -> None:
        """Restore logging after one test."""
        logging.disable(logging.NOTSET)

    def test_api_result_counts_from_csv(self) -> None:
        """[test_result_counts.py] Compare result counts of API calls between csv and live server
           Result counts from live server should always be greater or equal.
           Expected values in csv is obtain from production site on 12/12/18.
           Example of return json:
           {
               "data": [
                   {
                   "result_count": 1411270
                   }
               ]
           }
        """
        api_public = ApiForResultCounts(target=go_live_target())
        if go_live_target():
            client = requests.Session()
        else:
            client = RequestsClient()

        if go_live_target() or settings.TEST_RESULT_COUNTS_AGAINST_INTERNAL_DB:
            error_flag = []
            count = 0
            with open(self.filename) as csvfile:

                filereader = csv.reader(csvfile)
                for row in filereader:
                    if len(row) != 3:
                        if len(row) == 0:
                            continue
                        msg = 'Bad results_count line: '+str(row)
                        error_flag.append(msg)
                        msg += ' ==> FAIL!'
                        continue

                    q_str, expected, _info = row

                    if q_str.find('#/') == -1:
                        msg = 'Bad results_count line: '+str(row)
                        error_flag.append(msg)
                        msg += ' ==> FAIL!'
                        continue

                    url_hash = q_str.split("#/")[1].strip()
                    api_url = api_public.result_counts_api + url_hash

                    # If current api return has error, we test the next api
                    try:
                        data = json.loads(client.get(api_url).text)
                    except Exception as error:
                        error_flag.append(f"Return error:\n{api_url}\n{error}")
                        continue

                    result_count = data["data"][0]["result_count"]

                    comparison = '>='
                    if expected[0] == '=':
                        comparison = '='
                        expected = expected[1:]

                    msg = "checking: "+api_url+"\n"
                    msg += f"result: expected {comparison} {expected} :: got {result_count}"

                    if ((comparison == '>=' and
                         int(result_count) < int(expected)) or
                        (comparison == '=' and
                         int(result_count) != int(expected))):
                        error_flag.append(msg)
                        msg += ' ==> FAIL!'
                    else:
                        msg += ' - OK'

                    print(msg)

                    count = count+1

            if error_flag:
                print("============================")
                print("Result counts error summary:")
                print("============================")
                for e in error_flag:
                    print(e+'\n')
                raise Exception("API result counts test failed")
            else:
                print(f"Pass! No result counts failed! \
                      \nActual Number of Tests Run: {count}")



########################################
### Api url and payload for the test ###
########################################
class ApiForResultCounts:
    """The result-count endpoint of whichever server this run checks against."""

    # we need https and no need to specify port number
    api_base_url = "{}://{}.seti.org/opus/api/meta/result_count.json?"

    def __init__(self, target: str | None = "production") -> None:
        """Choose the server whose result counts are compared with the recorded ones.

        Parameters:
            target: ``'production'`` (or None) for the public server and ``'dev'``
                for the development one.

        Raises:
            AssertionError: If `target` names neither.
        """
        self.target = target
        if not self.target or self.target == "production":
            self.result_counts_api = self.api_base_url.format("https", "opus.pds-rings")
        elif self.target == "dev":
            self.result_counts_api = self.api_base_url.format("http", "dev.pds")
        else:
            raise AssertionError(self.target)
