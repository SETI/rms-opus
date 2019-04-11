# opus/application/test_api/test_return_formats.py

import logging
import requests
import sys
from unittest import TestCase

from rest_framework.test import APIClient, CoreAPIClient, RequestsClient

import settings

##################
### Test cases ###
##################
class ApiReturnFormatTests(TestCase):

    def setUp(self):
        self.maxDiff = None
        settings.CACHE_KEY_PREFIX = 'opustest:' + settings.DB_SCHEMA_NAME
        logging.disable(logging.ERROR)
        if settings.TEST_GO_LIVE: # pragma: no cover
            self.client = requests.Session()
        else:
            self.client = RequestsClient()

    def tearDown(self):
        logging.disable(logging.NOTSET)

    # FOR DEBUGGING PURPOSE: just run one single api call
    # def test_api_call_without_runserver(self):
    #     # client = APIClient()
    #     # response = client.get('/opus/__api/metadata/co-iss-n1867600335.json', {"cats": "PDS Constraints"})
    #     client = RequestsClient()
    #     response = client.get('https://tools.pds-rings.seti.org/opus/__api/metadata/vg-iss-2-s-c4362550.html', params={"cats": "PDS Constraints"})
    # #     # client = CoreAPIClient()
    # #     # schema = client.get('https://tools.pds-rings.seti.org/opus/api/metadata/vg-iss-2-s-c4362550.html')
    # #     # response = client.action(schema, params = {"cats": "PDS Constraints"})
    # #
    #     try:
    #         self.assertEqual(response.status_code, 200)
    #         # print(response.json())
    #         print(response.client)
    #     except Exception as e:
    #         raise

    ###############################
    ### API return format tests ###
    ###############################
    def test_all_api_calls(self):
        """[test_return_formats.py] API Calls: check different formats to see if response is 200
           Raise error when any response status code is NOT 200
        """
        api_public = ApiFormats(target=settings.TEST_GO_LIVE)
        api_internal = ApiFormats(target=settings.TEST_GO_LIVE or "internal")
        test_dict =  {**api_internal.api_dict, **api_public.api_dict}

        target_dict = test_dict
        error_flag = None

        for api_url in target_dict:
            flag = 0
            for target_format in target_dict[api_url]["support_format"]:
            # for target_format in ApiFormats.formats:

                try:
                    self._one_api_call(api_url, target_dict, target_format)

                except Exception as e: # pragma: no cover
                    error_flag = 1
                    if not flag:
                        flag = 1
                        print("---------------------------------------------------")
                        print(f"Testing API: {target_dict[api_url]['api']}")
                    print(f"{target_format}: return format error, status code: {e.args[0]}")
        if error_flag: # pragma: no cover
            raise Exception("API return formats test failed")

    ########################
    ### Helper functions ###
    ########################
    def _one_api_call(self, api_url_base, api_dict, format):
        """Check single api call to see if response is 200.
           api_url_base: a string of api url
           api_dict: a dictionary containing the payload
           format: a return format string that concatenates with api_url_base
        """
        if settings.TEST_GO_LIVE: # pragma: no cover
            client = requests.Session()
        else:
            client = RequestsClient()

        api_url = api_url_base + format
        payload = api_dict[api_url_base]["payload"]
        print("Testing URL", api_url, "Payload", payload)
        response = client.get(api_url, params=payload)
        # response = client.get("https://tools.pds-rings.seti.org/opus/api/meta/mults/planet.json", params={'target': 'Jupiter'})

        try:
            self.assertEqual(response.status_code, 200)
            # print(response.url)
        except Exception as e: # pragma: no cover
            # print(response.url)
            raise


########################################
### Api url and payload for the test ###
########################################
class ApiFormats:
    formats = ["json", "html", "csv", "zip"]
    # slugs for testing
    payload_for_result_count = {"planet": "Saturn", "target": "Pan", "limit": 2}
    payload_for_mults = {"planet": "Jupiter", "target": "Jupiter", "limit": 2}
    payload_for_endpoints = {"planet": "Jupiter", "target": "Callisto", "limit": 2}
    payload_for_all_categories = {"planet": "Jupiter", "target": "Callisto", "mission": "Galileo", "limit": 2}
    payload_for_data = {"planet": "Saturn", "target": "Pan", "instrument": "Cassini ISS", "limit": 2}
    payload_for_metadata = {"cats": "PDS Constraints"}
    payload_for_images = {"planet": "Jupiter", "limit": 2}
    payload_for_files = {"planet": "Jupiter", "limit": 2}

    def __init__(self, target="production"):
        self.target = target
        self.api_base = self.build_api_base()
        self.api_data_base = self.build_api_data_base()
        self.api_images_size_base = self.build_api_images_size_base()
        self.api_images_base = self.build_api_images_base()
        self.api_all_files_base = self.build_api_all_files_base()
        self.api_result_count_base = self.build_api_result_count_base()
        self.api_mults_base = self.build_api_mults_base()
        self.api_endpoints_base = self.build_api_endpoints_base()
        self.api_all_categories_base = self.build_api_all_categories_base()
        self.api_fields_base = self.build_api_fields_base()
        self.api_all_fields_base = self.build_api_all_fields_base()

        self.api_metadata_base = self.build_api_metadata_base("co-iss-n1867600335")
        self.api_metadata_v2_base = self.build_api_metadata_v2_base("vg-iss-2-s-c4362550")
        self.api_images_with_opus_id_base = self.build_api_images_with_opus_id_base("go-ssi-c0349542178")
        self.api_files_with_opus_id_base = self.build_api_files_with_opus_id_base("vg-iss-2-n-c0898429")
        self.api_categories_with_opus_id_base = self.build_api_categories_with_opus_id_base("vg-iss-2-s-c4360511")

        self.api_dict = self.build_api_dict()

    #################
    ### Build API ###
    #################
    def build_api_base(self):
        """build up base api depending on target site: dev/production
        """
        if (not self.target or self.target == "production"
            or self.target == "internal"): # pragma: no cover
            return "https://tools.pds-rings.seti.org/opus/api/"
        elif self.target == "dev": # pragma: no cover
            return "http://dev.pds-rings.seti.org/opus/api/"
        else: # pragma: no cover
            assert False, self.target

    def build_api_data_base(self):
        """api/data.[fmt]
        """
        return self.api_base + "data."

    def build_api_metadata_base(self, opus_id):
        """api/metadata/[opus_id].[fmt]
        """
        return self.api_base + f"metadata/{opus_id}."

    def build_api_metadata_v2_base(self, opus_id):
        """api/metadata_v2/[opus_id].[fmt]
        """
        return self.api_base + f"metadata_v2/{opus_id}."

    def build_api_images_size_base(self):
        """api/images/[size].[fmt]
        """
        return self.api_base + "images/thumb."

    def build_api_images_base(self):
        """api/images.[fmt]
        """
        return self.api_base + "images."

    def build_api_images_with_opus_id_base(self, opus_id):
        """api/image/[size]/[opus_id].[fmt]
        """
        return self.api_base + f"image/full/{opus_id}."

    def build_api_files_with_opus_id_base(self, opus_id):
        """api/files/[opus_id].[fmt]
        """
        return self.api_base + f"files/{opus_id}."

    def build_api_all_files_base(self):
        """api/files.[fmt]
        """
        return self.api_base + "files."

    def build_api_result_count_base(self):
        """api/meta/result_count.[fmt]
        """
        return self.api_base + "meta/result_count."

    def build_api_mults_base(self):
        """api/meta/mults/[param].[fmt]
        """
        return self.api_base + "meta/mults/planet." # use planet

    def build_api_endpoints_base(self):
        """api/meta/range/endpoints/[param].[fmt]
        """
        return self.api_base + "meta/range/endpoints/wavelength1." # use wavelength1

    def build_api_categories_with_opus_id_base(self, opus_id):
        """api/categories/[opus_id].json
        """
        return self.api_base + f"categories/{opus_id}."

    def build_api_all_categories_base(self):
        """api/categories.json
        """
        return self.api_base + "categories."

    def build_api_fields_base(self):
        """api/fields/[field].[fmt]
        """
        return self.api_base + "fields/mission." # use mission

    def build_api_all_fields_base(self):
        """api/fields.[fmt]
        """
        return self.api_base + "fields."

    def build_api_dict(self):
        """Test info for each api.
           ex:
           {'api': 'api/data.[fmt]',
            'payload': {'planet': 'Saturn',
                        'target': 'Pan',
                        'instrument': 'Cassini ISS',
                        'limit': 2},
            'support_format': ['json', 'html', 'csv']
           }
        """
        return {
            self.api_data_base: {
                "api": "api/data.[fmt]",
                "payload": ApiFormats.payload_for_data,
                "support_format": ["json", "html", "csv"]
            },
            self.api_metadata_base: {
                "api": "api/metadata/[opus_id].[fmt]",
                "payload": ApiFormats.payload_for_metadata,
                "support_format": ["json", "html", "csv"]
            },
            self.api_metadata_v2_base: {
                "api": "api/metadata_v2/[opus_id].[fmt]",
                "payload": ApiFormats.payload_for_metadata,
                "support_format": ["json", "html", "csv"]
            },
            self.api_images_size_base: {
                "api": "api/images/[size].[fmt]",
                "payload": ApiFormats.payload_for_images,
                "support_format": ["json", "html"]
            },
            self.api_images_base: {
                "api": "api/images.[fmt]",
                "payload": ApiFormats.payload_for_images,
                "support_format": ["json", "html"]
            },
            self.api_images_with_opus_id_base: {
                "api": "api/image/[size]/[opus_id].[fmt]",
                "payload": None,
                "support_format": ["json", "html"]
            },
            self.api_files_with_opus_id_base: {
                "api": "api/files/[opus_id].[fmt]",
                "payload": None,
                "support_format": ["json"]
            },
            self.api_all_files_base: {
                "api": "api/files.[fmt]",
                "payload": ApiFormats.payload_for_files,
                "support_format": ["json"]
            },
            self.api_result_count_base: {
                "api": "api/meta/result_count.[fmt]",
                "payload": ApiFormats.payload_for_result_count,
                "support_format": ["json", "html", "csv"]
            },
            self.api_mults_base: {
                "api": "api/meta/mults/[param].[fmt]",
                "payload": ApiFormats.payload_for_mults,
                "support_format": ["json", "html", "csv"]
            },
            self.api_endpoints_base: {
                "api": "api/meta/range/endpoints/[param].[fmt]",
                "payload": ApiFormats.payload_for_endpoints,
                "support_format": ["json", "html", "csv"]
            },
            self.api_categories_with_opus_id_base: {
                "api": "api/categories/[opus_id].json",
                "payload": None,
                "support_format": ["json"]
            },
            self.api_all_categories_base: {
                "api": "api/categories.json",
                "payload": ApiFormats.payload_for_all_categories,
                "support_format": ["json"]
            },
            self.api_fields_base: {
                "api": "api/fields/[field].[fmt]",
                "payload": None,
                "support_format": ["json", "html"]
            },
            self.api_all_fields_base: {
                "api": "api/fields.[fmt]",
                "payload": None,
                "support_format": ["json", "html"]
            },
        }
