from rest_framework.test import APIClient
from rest_framework.test import RequestsClient
from unittest import TestCase
import requests
from api_formats_vims import ApiForVimsDownlinks
# stop the trace / logging
import sys
import logging

class ApiVimsDownlinksTests(TestCase):
    GO_LIVE = False
    LIVE_TARGET = "production"

    def setUp(self):
        sys.tracebacklimit = 0 # default: 1000
        logging.disable(logging.CRITICAL)

    def teardown(self):
        sys.tracebacklimit = 1000 # default: 1000
        logging.disable(logging.NOTSET)

    def collect_vims_image_numbers_for_single_primary_filespec(self, primary_filespec, api_dict):

        if not ApiVimsDownlinksTests.GO_LIVE:
            # client = RequestsClient()
            raise Exception("Test db has no VIMs data")
        else:
            client = requests.Session()

        format = "json"
        primary_filespec_object = api_dict[primary_filespec]
        api_url = primary_filespec_object["url"] + format
        payload = primary_filespec_object["payload"]
        response = client.get(api_url, params=payload)
        test_url = response.url
        image_count = {}

        if response.status_code == 200:
            data_object = response.json()["data"]
            for image_id in primary_filespec_object["images_with_opus_id"]:
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
            raise Exception("%s: Error, http status code: %s" %(format, http_status_code))

    # check if any image numbers from 001 > ones in 002
    # check if image counts for each primary filespec are all > 0
    def test_check_and_compare_vims_downlinks_for_v1_and_v2(self):
        api = ApiForVimsDownlinks(target=ApiVimsDownlinksTests.LIVE_TARGET)
        image_count = {}
        error_msg = []

        for primary_filespec in api.api_dict:
            try:
                image_count = self.collect_vims_image_numbers_for_single_primary_filespec(primary_filespec, api.api_dict)
            except Exception as error:
                error_msg.append(error)

            # print(image_count)
            primary_filespec_object = api.api_dict[primary_filespec]
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

                        if not v1_count > 0:
                            error_msg.append("%s is missing downlinks for image: %s" %(v1_id, image))
                        if not v2_count > 0:
                            error_msg.append("%s is missing downlinks for image: %s" %(v2_id, image))
                        if v2_count >= v1_count:
                            error_msg.append("%s is missing downlinks for image: %s" %(v1_id, image))

        if error_msg and ApiVimsDownlinksTests.GO_LIVE:
            for e in error_msg:
                raise Exception("VIMS downlinks test failed")
