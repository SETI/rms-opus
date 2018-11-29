# opus/application/test_api/test_vims_image_downlinks.py

import logging
import requests
import sys
from unittest import TestCase

from rest_framework.test import APIClient
from rest_framework.test import RequestsClient

from test_return_formats import ApiFormats

##################
### Test cases ###
##################
class ApiVimsDownlinksTests(TestCase):
    GO_LIVE = False
    LIVE_TARGET = "production"

    # disable error logging and trace output before test
    # def setUp(self):
    #     sys.tracebacklimit = 0 # default: 1000
    #     logging.disable(logging.CRITICAL)
    #
    # # enable error logging and trace output after test
    # def teardown(self):
    #     sys.tracebacklimit = 1000 # default: 1000
    #     logging.disable(logging.NOTSET)

    ###############################
    ### API VIMS downlink tests ###
    ###############################
    def test_check_and_compare_vims_downlinks_for_v1_and_v2(self):
        """Check the number of VIMS downlinks to see if they are valid.
           Check if any image numbers from 001 > ones in 002
           Check if image counts for each primary filespec are all > 0
        """
        api_public = ApiForVimsDownlinks(target=ApiVimsDownlinksTests.LIVE_TARGET)
        api_internal = ApiForVimsDownlinks(target=f"internal-{ApiVimsDownlinksTests.LIVE_TARGET}")
        test_dict =  [api_internal.api_dict, api_public.api_dict]

        image_count = {}
        error_msg = []
        test_data_not_available = ""

        for target_dict in test_dict:
            for primary_filespec in target_dict:
                try:
                    image_count = self._collect_vims_image_numbers_for_single_primary_filespec(primary_filespec, target_dict)
                except Exception as error:
                    error_msg.append(error)

                # print(image_count)
                primary_filespec_object = target_dict[primary_filespec]
                v1_ir_id = primary_filespec_object["images_with_opus_id"][0]
                v1_vis_id = primary_filespec_object["images_with_opus_id"][1]
                v2_ir_id = primary_filespec_object["images_with_opus_id"][2]
                v2_vis_id = primary_filespec_object["images_with_opus_id"][3]

                if not error_msg:
                    for v1_id in [v1_ir_id, v1_vis_id]:
                        for image, v1_count in image_count[v1_id].items():
                            if v1_id == v1_ir_id:
                                v2_id = v2_ir_id
                            else:
                                v2_id = v2_vis_id
                            v2_count = image_count[v2_id][image]

                            if not v1_count:
                                error_msg.append(f"{v1_id} is missing downlinks for image: {images}")
                            if not v2_count:
                                error_msg.append(f"{v2_id} is missing downlinks for image: {image}")
                            if v2_count >= v1_count:
                                error_msg.append(f"{v1_id} is missing downlinks for image: {image}")

        if error_msg:
            for e in error_msg:
                if e.args[0] in ["No VIMS data in test db",
                                 "VIMS image data is not fully available in test db"] :
                    test_data_not_available = e.args[0]
                else:
                    raise Exception("VIMS downlinks test failed")
        if test_data_not_available:
            print(test_data_not_available)


    ########################
    ### Helper functions ###
    ########################
    def _collect_vims_image_numbers_for_single_primary_filespec(self, primary_filespec, api_dict):
        """Collect vims image numbers for ONE primary_filespecself.
           return an image_count object to store the numbers
           ex:
           {'co-vims-v1490874598_001_ir': {
                'browse-thumb': 2,
                'browse-small': 2,
                'browse-medium': 2,
                'browse-full': 2,
                'covims-raw': 7,
                'covims-thumb': 2,
                'covims-medium': 2,
                'covims-full': 2}
           }
        """

        if not ApiVimsDownlinksTests.GO_LIVE:
            client = RequestsClient()
            # raise Exception("Test db has no VIMS data")
        else:
            client = requests.Session()

        format = "json"
        primary_filespec_object = api_dict[primary_filespec]
        api_url = primary_filespec_object["url"] + format
        payload = primary_filespec_object["payload"]
        response = client.get(api_url, params=payload)
        test_url = response.url
        image_count = {}
        response_images = [
                            "browse-thumb",
                            "browse-small",
                            "browse-medium",
                            "browse-full",
                            "covims-raw",
                            "covims-thumb",
                            "covims-medium",
                            "covims-full",
                          ]
        # print(test_url)
        if response.status_code == 200:
            data_object = response.json()["data"]
            # When test db return empty object, we would NOT proceed to count the number of images
            if not data_object and not ApiVimsDownlinksTests.GO_LIVE:
                raise Exception("No VIMS data in test db")

            for image_id in primary_filespec_object["images_with_opus_id"]:
                # When image is not fully available in test db, we would NOT proceed to count the number of images
                for image_key in response_images:
                    available_image_in_test_db = data_object[image_id].keys()
                    if image_key not in available_image_in_test_db:
                        raise Exception("VIMS image data is not fully available in test db")

                image_count[image_id] = {
                    "browse-thumb": len(data_object[image_id]["browse-thumb"]),
                    "browse-small": len(data_object[image_id]["browse-small"]),
                    "browse-medium": len(data_object[image_id]["browse-medium"]),
                    "browse-full": len(data_object[image_id]["browse-full"]),
                    "covims-raw": len(data_object[image_id]["covims-raw"]),
                    "covims-thumb": len(data_object[image_id]["covims-thumb"]),
                    "covims-medium": len(data_object[image_id]["covims-medium"]),
                    "covims-full": len(data_object[image_id]["covims-full"]),
                }
            return image_count
        else:
            raise Exception(f"{format}: Error, http status code: {http_status_code}")


########################################
### Api url and payload for the test ###
########################################
class ApiForVimsDownlinks(ApiFormats):
    opus_id_all = {
        "v1490874598": [
            "co-vims-v1490874598_001_ir",
            "co-vims-v1490874598_001_vis",
            "co-vims-v1490874598_002_ir",
            "co-vims-v1490874598_002_vis",
        ],
        "v1490874654": [
            "co-vims-v1490874654_001_ir",
            "co-vims-v1490874654_001_vis",
            "co-vims-v1490874654_002_ir",
            "co-vims-v1490874654_002_vis",
        ],
        "v1490874707": [
            "co-vims-v1490874707_001_ir",
            "co-vims-v1490874707_001_vis",
            "co-vims-v1490874707_002_ir",
            "co-vims-v1490874707_002_vis",
        ],
        "v1490874775": [
            "co-vims-v1490874775_001_ir",
            "co-vims-v1490874775_001_vis",
            "co-vims-v1490874775_002_ir",
            "co-vims-v1490874775_002_vis",
        ],
        "v1490874823": [
            "co-vims-v1490874823_001_ir",
            "co-vims-v1490874823_001_vis",
            "co-vims-v1490874823_002_ir",
            "co-vims-v1490874823_002_vis",
        ],
        "v1490874878": [
            "co-vims-v1490874878_001_ir",
            "co-vims-v1490874878_001_vis",
            "co-vims-v1490874878_002_ir",
            "co-vims-v1490874878_002_vis",
        ],
        "v1490874946": [
            "co-vims-v1490874946_001_ir",
            "co-vims-v1490874946_001_vis",
            "co-vims-v1490874946_002_ir",
            "co-vims-v1490874946_002_vis",
        ],
        "v1490874999": [
            "co-vims-v1490874999_001_ir",
            "co-vims-v1490874999_001_vis",
            "co-vims-v1490874999_002_ir",
            "co-vims-v1490874999_002_vis",
        ],
        "v1490875052": [
            "co-vims-v1490875052_001_ir",
            "co-vims-v1490875052_001_vis",
            "co-vims-v1490875052_002_ir",
            "co-vims-v1490875052_002_vis",
        ],
    }

    def __init__(self, target):
        super().__init__(target)

    def build_all_testing_api(self):
        self.api_dict = self.build_api_dict()

    def build_api_dict(self):
        """Test info for api calls with VIMS product.
           ex:
           {'v1490874598':
                {'api': 'api/files.[fmt]',
                 'payload': {'primaryfilespec': 'v1490874598'},
                 'images_with_opus_id': ['co-vims-v1490874598_001_ir',
                                         'co-vims-v1490874598_001_vis',
                                         'co-vims-v1490874598_002_ir',
                                         'co-vims-v1490874598_002_vis'],
                 'url': 'https://tools.pds-rings.seti.org/opus/api/files.'
                }
            }
        """
        res = {}
        url = self.build_api_all_files_base()
        for primary_filespec in ApiForVimsDownlinks.opus_id_all:
            res[primary_filespec] = {
                "api": "api/files.[fmt]",
                "payload": {"primaryfilespec": primary_filespec},
                "images_with_opus_id": ApiForVimsDownlinks.opus_id_all[primary_filespec],
                "url": url
            }
        return res
