# opus/application/test_api/test_result_counts.py

import csv
import json
import logging
import requests
import settings
import sys
from unittest import TestCase

from rest_framework.test import APIClient, CoreAPIClient, RequestsClient

##################
### Test cases ###
##################
class APIResultCountsTests(TestCase):
    filename = "test_api/csv/result_counts_new_slugs.csv"
    GO_LIVE = False
    LIVE_TARGET = "production"

    # disable error logging and trace output before test
    def setUp(self):
        sys.tracebacklimit = 0 # default: 1000
        logging.disable(logging.DEBUG)

    # enable error logging and trace output after test
    def teardown(self):
        sys.tracebacklimit = 1000 # default: 1000
        logging.disable(logging.NOTSET)

    def test_api_result_counts_from_csv(self):
        """Result Counts: compare result counts of API calls between csv and live server
           Result counts from live server should always be larger
           Expected values in csv is obtain from production site on 12/12/18
           Example of return json:
           {
               "data": [
                   {
                   "result_count": 1411270
                   }
               ]
           }
        """
        api_public = ApiForResultCounts(target=self.LIVE_TARGET)
        if self.GO_LIVE:
            client = requests.Session()
        else:
            client = RequestsClient()

        if self.GO_LIVE or settings.TEST_RESULT_COUNTS_AGAINST_INTERNAL_DB:
            error_flag = []
            count = 0
            with open(self.filename, "r") as csvfile:

                filereader = csv.reader(csvfile)
                for row in filereader:
                    q_str, expected, info = row

                    url_hash = q_str.split("#/")[1].strip()
                    api_url = api_public.result_counts_api + url_hash

                    # if current api return has error, we test the next api
                    try:
                        # data = json.loads(requests.get(api_url).text)
                        data = json.loads(client.get(api_url).text)
                    except Exception as error:
                        error_flag.append(Exception(f"Return error:\n{api_url}"))
                        continue

                    result_count = data["data"][0]["result_count"]

                    msg = """checking: \n{}
                              result: expected >= {} :: got: {} \n
                          """.format(api_url, expected, result_count)

                    print(msg)

                    try:
                        assert result_count >= int(expected)
                    except Exception as error:
                        error_flag.append(AssertionError(msg))
                        # raise AssertionError(msg)

                    count = count+1
            if error_flag:
                print("============================")
                print("Result counts error summary:")
                print("============================")
                for e in error_flag:
                    print(f"{e.args[0].strip()}\n")
                raise Exception("API result counts test failed")
            else:
                print(f"Pass! No result counts failed! \
                      \nActual Number of Tests Run: {count}")



########################################
### Api url and payload for the test ###
########################################
class ApiForResultCounts:
    # we need https and no need to specify port number
    api_base_url = "{}://{}.pds-rings.seti.org/opus/api/meta/result_count.json?"

    def __init__(self, target="production"):
        self.target = target
        if self.target == "production":
            self.result_counts_api = self.api_base_url.format("https", "tools")
        elif self.target == "dev":
            self.result_counts_api = self.api_base_url.format("http", "dev")
