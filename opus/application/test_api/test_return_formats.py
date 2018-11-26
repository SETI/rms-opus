from rest_framework.test import APIClient
from rest_framework.test import RequestsClient
from unittest import TestCase
import requests
from api_formats import ApiFormats
# stop the trace / logging
import sys
import logging

class ApiReturnFormatTests(TestCase):
    GO_LIVE = False
    LIVE_TARGET = "production"

    def setUp(self):
        sys.tracebacklimit = 0 # default: 1000
        logging.disable(logging.CRITICAL)

    def teardown(self):
        sys.tracebacklimit = 1000 # default: 1000
        logging.disable(logging.NOTSET)

    # def test_api_call_without_runserver(self):
    #     # client = APIClient()
    #     # response = client.get('/opus/api/metadata/co-iss-n1867600335.json', {"cats": "PDS Constraints"})
    #     client = RequestsClient()
    #     response = client.get('https://tools.pds-rings.seti.org/opus/api/metadata/vg-iss-2-s-c4362550.html', params={"cats": "PDS Constraints"})
    #     try:
    #         self.assertEqual(response.status_code, 200)
    #         # print(response.json())
    #     except Exception as e:
    #         print(response.url)
    #         raise

    def one_api_call(self, api_url_base, api_dict, format):

        if not ApiReturnFormatTests.GO_LIVE:
            client = RequestsClient()
        else:
            client = requests.Session()

        # work here
        api_url = api_url_base + format
        payload = api_dict[api_url_base]["payload"]
        response = client.get(api_url, params=payload)
        # response = client.get("https://tools.pds-rings.seti.org/opus/api/meta/mults/planet.json", params={'target': 'Jupiter'})

        try:
            self.assertEqual(response.status_code, 200)
        except Exception as e:
            raise

    def test_all_api_calls(self):
        api = ApiFormats(target=ApiReturnFormatTests.LIVE_TARGET)

        error_flag = None
        for api_url in api.api_dict:
            flag = 0
            for target_format in api.formats:

                try:
                    # self.assertEqual(response.status_code, 200)
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
