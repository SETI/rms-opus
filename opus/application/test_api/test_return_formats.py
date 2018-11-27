import logging
import requests
import sys
from unittest import TestCase

from rest_framework.test import APIClient
from rest_framework.test import CoreAPIClient
from rest_framework.test import RequestsClient

from api_for_test_cases.api_return_formats import ApiFormats


class ApiReturnFormatTests(TestCase):
    GO_LIVE = False
    LIVE_TARGET = "production"

    # disable error logging and trace output before test
    def setUp(self):
        sys.tracebacklimit = 0 # default: 1000
        logging.disable(logging.CRITICAL)

    # enable error logging and trace output after test
    def teardown(self):
        sys.tracebacklimit = 1000 # default: 1000
        logging.disable(logging.NOTSET)

    # FOR DEBUGGING PURPOSE: just run one single api call
    # def test_api_call_without_runserver(self):
    #     client = APIClient()
    #     response = client.get('/opus/api/metadata/co-iss-n1867600335.html', {"cats": "PDS Constraints"})
    #     # client = RequestsClient()
    #     # response = client.get('https://tools.pds-rings.seti.org/opus/api/metadata/vg-iss-2-s-c4362550.html', params={"cats": "PDS Constraints"})
    #     # client = CoreAPIClient()
    #     # schema = client.get('https://tools.pds-rings.seti.org/opus/api/metadata/vg-iss-2-s-c4362550.html')
    #     # response = client.action(schema, params = {"cats": "PDS Constraints"})
    #
    #     try:
    #         self.assertEqual(response.status_code, 200)
    #         # print(response.json())
    #     except Exception as e:
    #         print(response.url)
    #         raise

    ###############################
    ### API return format tests ###
    ###############################
    def test_all_api_calls(self):
        """Check all api calls with different formats to see if response is 200.
           Raise error when any response status code is NOT 200
        """
        api = ApiFormats(target=ApiReturnFormatTests.LIVE_TARGET)

        error_flag = None
        for api_url in api.api_dict:
            flag = 0
            for target_format in api.api_dict[api_url]["support_format"]:
                
                try:
                    self.one_api_call(api_url, api.api_dict, target_format)

                except Exception as e:
                    error_flag = 1
                    if not flag:
                        flag = 1
                        print("---------------------------------------------------")
                        print("Testing API: %s" %(api.api_dict[api_url]["api"]))
                    print("%s: return format error, status code: %s" %(target_format, e.args[0]))
        if error_flag:
            raise Exception("API return formats test failed")

    ########################
    ### Helper functions ###
    ########################
    def one_api_call(self, api_url_base, api_dict, format):
        """Check single api call to see if response is 200.
           api_url_base: a string of api url
           api_dict: a dictionary containing the payload
           format: a return format string that concatenates with api_url_base
        """
        if not ApiReturnFormatTests.GO_LIVE:
            client = RequestsClient()
        else:
            client = requests.Session()

        api_url = api_url_base + format
        payload = api_dict[api_url_base]["payload"]
        response = client.get(api_url, params=payload)
        # response = client.get("https://tools.pds-rings.seti.org/opus/api/meta/mults/planet.json", params={'target': 'Jupiter'})

        try:
            self.assertEqual(response.status_code, 200)
        except Exception as e:
            raise
