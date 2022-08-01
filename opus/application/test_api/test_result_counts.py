# opus/application/test_api/test_result_counts.py

import csv
import json
import logging
import requests
from unittest import TestCase

from rest_framework.test import APIClient, RequestsClient

import settings

##################
### Test cases ###
##################
class APIResultCountsTests(TestCase):
    filename = "test_api/data/result_counts.csv"

    # disable error logging and trace output before test
    def setUp(self):
        self.maxDiff = None
        settings.OPUS_FAKE_API_DELAYS = 0
        settings.OPUS_FAKE_SERVER_ERROR404_PROBABILITY = 0
        settings.OPUS_FAKE_SERVER_ERROR500_PROBABILITY = 0
        settings.CACHE_KEY_PREFIX = 'opustest:' + settings.DB_SCHEMA_NAME
        logging.disable(logging.DEBUG)

    # enable error logging and trace output after test
    def tearDown(self):
        logging.disable(logging.NOTSET)

    def test_api_result_counts_from_csv(self):
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
        api_public = ApiForResultCounts(target=settings.TEST_GO_LIVE)
        if settings.TEST_GO_LIVE:
            client = requests.Session()
        else:
            client = RequestsClient()

        if settings.TEST_GO_LIVE or settings.TEST_RESULT_COUNTS_AGAINST_INTERNAL_DB:
            error_flag = []
            count = 0
            with open(self.filename, "r") as csvfile:

                filereader = csv.reader(csvfile)
                for row in filereader:
                    if len(row) != 3:
                        if len(row) == 0:
                            continue
                        msg = 'Bad results_count line: '+str(row)
                        error_flag.append(msg)
                        msg += ' ==> FAIL!'
                        continue

                    q_str, expected, info = row

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
    # we need https and no need to specify port number
    api_base_url = "{}://{}.seti.org/opus/api/meta/result_count.json?"

    def __init__(self, target="production"):
        self.target = target
        if not self.target or self.target == "production":
            self.result_counts_api = self.api_base_url.format("https", "opus.pds-rings")
        elif self.target == "dev":
            self.result_counts_api = self.api_base_url.format("http", "dev.pds")
        else:
            assert False, self.target
