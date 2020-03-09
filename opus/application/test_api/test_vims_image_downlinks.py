# opus/application/test_api/test_vims_image_downlinks.py

import json
import logging
import requests
from unittest import TestCase

from rest_framework.test import RequestsClient

import settings

##################
### Test cases ###
##################
class ApiVimsDownlinksTests(TestCase):

    # disable error logging and trace output before test
    def setUp(self):
        settings.OPUS_FAKE_API_DELAYS = None
        settings.OPUS_FAKE_SERVER_ERROR404_PROBABILITY = 0
        settings.OPUS_FAKE_SERVER_ERROR500_PROBABILITY = 0
        settings.CACHE_KEY_PREFIX = 'opustest:' + settings.DB_SCHEMA_NAME
        logging.disable(logging.ERROR)

    # enable error logging and trace output after test
    def tearDown(self):
        logging.disable(logging.NOTSET)

    ###############################
    ### API VIMS downlink tests ###
    ###############################
    def test_check_and_compare_vims_downlinks_for_v1_and_v2(self):
        """[test_vims_image_downlinks.py] Check the number of VIMS downlinks to see if they are valid
           Check if any image numbers from 001 > ones in 002
           Check if image counts for each primary filespec are all > 0
        """
        api_public = ApiForVimsDownlinks(target=settings.TEST_GO_LIVE)
        api_internal = ApiForVimsDownlinks(target="internal")
        test_dict =  [api_internal.api_dict, api_public.api_dict]

        image_count = {}
        error_msg = []
        test_data_not_available = ""

        for target_dict in test_dict:
            for primary_filespec in target_dict:
                try:
                    image_count = self._collect_vims_image_numbers_for_single_primary_filespec(primary_filespec, target_dict)
                except Exception as error: # pragma: no cover
                    error_msg.append(error)

                # print(image_count)
                primary_filespec_object = target_dict[primary_filespec]
                v1_ir_id = primary_filespec_object["images_with_opus_id"][0]
                v1_vis_id = primary_filespec_object["images_with_opus_id"][1]
                v2_ir_id = primary_filespec_object["images_with_opus_id"][2]
                v2_vis_id = primary_filespec_object["images_with_opus_id"][3]

                if not error_msg: # pragma: no cover
                    for v1_id in [v1_ir_id, v1_vis_id]:
                        for image, v1_count in image_count[v1_id].items():
                            if v1_id == v1_ir_id:
                                v2_id = v2_ir_id
                            else:
                                v2_id = v2_vis_id
                            v2_count = image_count[v2_id][image]

                            if not v1_count: # pragma: no cover
                                error_msg.append(f"{v1_id} is missing downlinks for image: {images}")
                            if not v2_count: # pragma: no cover
                                error_msg.append(f"{v2_id} is missing downlinks for image: {image}")
                            if v2_count >= v1_count: # pragma: no cover
                                error_msg.append(f"{v1_id} is missing downlinks for image: {image}")

        if error_msg: # pragma: no cover
            for e in error_msg:
                if e.args[0] in ["No VIMS data in test db",
                                 "VIMS image data is not fully available in test db"] :
                    test_data_not_available = e.args[0]
                else:
                    raise Exception("VIMS downlinks test failed")
        if test_data_not_available: # pragma: no cover
            print(test_data_not_available)


    ########################
    ### Helper functions ###
    ########################
    def _collect_vims_image_numbers_for_single_primary_filespec(self, primary_filespec, api_dict):
        """Collect vims image numbers for ONE primary_filespecself.
           return an image_count object to store the numbers
           ex:
           {'co-vims-v1490874598_001_ir': {
                'browse_thumb': 2,
                'browse_small': 2,
                'browse_medium': 2,
                'browse_full': 2,
                'covims_raw': 7,
                'covims_thumb': 2,
                'covims_medium': 2,
                'covims_full': 2}
           }
        """

        if settings.TEST_GO_LIVE: # pragma: no cover
            client = requests.Session()
        else:
            client = RequestsClient()
            # raise Exception("Test db has no VIMS data")

        format = "json"
        primary_filespec_object = api_dict[primary_filespec]
        api_url = primary_filespec_object["url"] + format
        payload = primary_filespec_object["payload"]
        response = client.get(api_url, params=payload)
        test_url = response.url
        image_count = {}
        response_images = [
                            "browse_thumb",
                            "browse_small",
                            "browse_medium",
                            "browse_full",
                            "covims_raw",
                            "covims_thumb",
                            "covims_medium",
                            "covims_full",
                          ]
        # print(test_url)
        if response.status_code == 200: # pragma: no cover
            data_object = response.json()["data"]
            # When test db return empty object, we would NOT proceed to count the number of images
            if not data_object and not settings.TEST_GO_LIVE: # pragma: no cover
                raise Exception("No VIMS data in test db")

            for image_id in primary_filespec_object["images_with_opus_id"]:
                # When image is not fully available in test db, we would NOT proceed to count the number of images
                for image_key in response_images:
                    available_image_in_test_db = data_object[image_id].keys()
                    if image_key not in available_image_in_test_db: # pragma: no cover
                        raise Exception("VIMS image data is not fully available in test db")

                image_count[image_id] = {
                    "browse_thumb": len(data_object[image_id]["browse_thumb"]),
                    "browse_small": len(data_object[image_id]["browse_small"]),
                    "browse_medium": len(data_object[image_id]["browse_medium"]),
                    "browse_full": len(data_object[image_id]["browse_full"]),
                    "covims_raw": len(data_object[image_id]["covims_raw"]),
                    "covims_thumb": len(data_object[image_id]["covims_thumb"]),
                    "covims_medium": len(data_object[image_id]["covims_medium"]),
                    "covims_full": len(data_object[image_id]["covims_full"]),
                }
            return image_count
        else: # pragma: no cover
            raise Exception(f"{format}: Error, http status code: {http_status_code}")


########################################
### Api url and payload for the test ###
########################################
class ApiForVimsDownlinks:
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

    def __init__(self, target="production"):
        self.target = target
        self.api_base = self.build_api_base()
        self.api_all_files_base = self.build_api_all_files_base()
        self.api_dict = self.build_api_dict()

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

    def build_api_all_files_base(self):
        """api/files.[fmt]
        """
        return self.api_base + "files."

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
