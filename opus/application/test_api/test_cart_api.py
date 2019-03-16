# opus/application/test_api/test_cart_api.py

import logging
import requests
import sys
from unittest import TestCase

import django.conf
from rest_framework.test import RequestsClient

from api_test_helper import ApiTestHelper

import settings

django.conf.settings.CACHE_BACKEND = 'dummy:///'

class ApiCartTests(TestCase, ApiTestHelper):

    def setUp(self):
        self.maxDiff = None
        sys.tracebacklimit = 0 # default: 1000
        settings.CACHE_KEY_PREFIX = 'opustest:' + settings.OPUS_SCHEMA_NAME
        logging.disable(logging.ERROR)
        if settings.TEST_GO_LIVE:
            self.client = requests.Session()
        else:
            self.client = RequestsClient()

    def tearDown(self):
        sys.tracebacklimit = 1000 # default: 1000
        logging.disable(logging.NOTSET)


            ##################################################
            ######### /__cart/status.json: API TESTS #########
            ##################################################

    def test__api_cart_status_no_reqno(self):
        "[test_cart_api.py] /__cart/status: no reqno"
        url = '/opus/__cart/status.json'
        self._run_status_equal(url, 404, settings.HTTP404_MISSING_REQNO)

    # We don't bother otherwise testing this separately because it's used
    # extensively in all the tests below


            #################################################
            ######### /__cart/reset.json: API TESTS #########
            #################################################

    def test__api_cart_reset(self):
        "[test_cart_api.py] /__cart/reset"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/status.json?reqno=1'
        expected = {'count': 0, 'reqno': 1}
        self._run_json_equal(url, expected)


            ###############################################
            ######### /__cart/add.json: API TESTS #########
            ###############################################

    def test__api_cart_add_no_reqno(self):
        "[test_cart_api.py] /__cart/add: no reqno"
        url = '/opus/__cart/add.json?opusid=co-iss-n1460961026'
        self._run_status_equal(url, 404, settings.HTTP404_MISSING_REQNO)

    def test__api_cart_add_missing(self):
        "[test_cart_api.py] /__cart/add: missing OPUSID no download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/add.json?reqno=456'
        expected = {'count': 0, 'error': 'No opusid specified', 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/status.json?reqno=456'
        expected = {'count': 0, 'reqno': 456}
        self._run_json_equal(url, expected)

    def test__api_cart_add_empty(self):
        "[test_cart_api.py] /__cart/add: empty OPUSID no download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/add.json?opusid=&reqno=456'
        expected = {'count': 0, 'error': 'No opusid specified', 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/status.json?reqno=456'
        expected = {'count': 0, 'reqno': 456}
        self._run_json_equal(url, expected)

    def test__api_cart_add_one(self):
        "[test_cart_api.py] /__cart/add: good OPUSID no download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/add.json?opusid=co-iss-n1460961026&reqno=456'
        expected = {'count': 1, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/status.json?reqno=456'
        expected = {'count': 1, 'reqno': 456}
        self._run_json_equal(url, expected)

    def test__api_cart_add_duplicate(self):
        "[test_cart_api.py] /__cart/add: duplicate OPUSID no download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/add.json?opusid=co-iss-n1460961026&reqno=456'
        expected = {'count': 1, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/add.json?opusid=co-iss-n1460961026&reqno=456'
        expected = {'count': 1, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/status.json?reqno=456'
        expected = {'count': 1, 'reqno': 456}
        self._run_json_equal(url, expected)

    def test__api_cart_add_bad(self):
        "[test_cart_api.py] /__cart/add: bad OPUSID no download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/add.json?opusid=co-iss-xn1460961026&reqno=456'
        expected = {'count': 0, 'error': 'opusid not found', 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/status.json?reqno=456'
        expected = {'count': 0, 'reqno': 456}
        self._run_json_equal(url, expected)

    def test__api_cart_add_good_bad(self):
        "[test_cart_api.py] /__cart/add: good+bad OPUSID no download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/add.json?opusid=co-iss-n1460961026&reqno=456'
        expected = {'count': 1, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/add.json?opusid=co-iss-xn1460961026&reqno=456'
        expected = {'count': 1, 'error': 'opusid not found', 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/status.json?reqno=456'
        expected = {'count': 1, 'reqno': 456}
        self._run_json_equal(url, expected)

    def test__api_cart_add_mixture(self):
        "[test_cart_api.py] /__cart/add: mixture no download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/add.json?opusid=vg-iss-2-s-c4360010&reqno=456'
        expected = {'count': 1, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/add.json?opusid=WOOHOO&reqno=456'
        expected = {'count': 1, 'error': 'opusid not found', 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/add.json?opusid=vg-iss-2-s-c4360010&reqno=456'
        expected = {'count': 1, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/add.json?opusid=vg-iss-2-s-c4360010&reqno=456'
        expected = {'count': 1, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/add.json?opusid=hst-12003-wfc3-ibcz21ff&reqno=456'
        expected = {'count': 2, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/add.json?opusid=nh-mvic-mpf_000526016&reqno=456'
        expected = {'count': 2, 'error': 'opusid not found', 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/status.json?reqno=456'
        expected = {'count': 2, 'reqno': 456}
        self._run_json_equal(url, expected)

    def test__api_cart_add_missing(self):
        "[test_cart_api.py] /__cart/add: missing OPUSID no download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/add.json?reqno=124'
        expected = {'count': 0, 'error': 'No opusid specified', 'reqno': 124}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/status.json?reqno=456'
        expected = {'count': 0, 'reqno': 456}
        self._run_json_equal(url, expected)

    def test__api_cart_add_one(self):
        "[test_cart_api.py] /__cart/add: good OPUSID no download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/add.json?opusid=co-iss-n1460961026&reqno=12345'
        expected = {'count': 1, 'error': False, 'reqno': 12345}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/status.json?reqno=789'
        expected = {'count': 1, 'reqno': 789}
        self._run_json_equal(url, expected)

    def test__api_cart_add_bad(self):
        "[test_cart_api.py] /__cart/add: bad OPUSID no download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/add.json?opusid=co-iss-xn1460961026&reqno=101010101'
        expected = {'count': 0, 'error': 'opusid not found', 'reqno': 101010101}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/status.json?reqno=0'
        expected = {'count': 0, 'reqno': 0}
        self._run_json_equal(url, expected)

    def test__api_cart_add_missing_download(self):
        "[test_cart_api.py] /__cart/add: missing OPUSID with download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/add.json?download=1&reqno=456'
        expected = {"error": "No opusid specified", "count": 0, "reqno": 456, "total_download_count": 0, "total_download_size": 0, "total_download_size_pretty": "0B", "product_cat_list": []}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/status.json?reqno=456'
        expected = {'count': 0, 'reqno': 456}
        self._run_json_equal(url, expected)

    def test__api_cart_add_download_one(self):
        "[test_cart_api.py] /__cart/add: good OPUSID with download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/add.json?opusid=co-iss-n1460960653&download=1&reqno=101010101'
        expected = {"error": False, "count": 1, "reqno": 101010101, "total_download_count": 21, "total_download_size": 13717790, "total_download_size_pretty": "13M", "product_cat_list": [["Metadata Products", [{"slug_name": "inventory", "product_type": "Target Body Inventory", "product_count": 1, "download_count": 2, "download_size": 409019, "download_size_pretty": "399K"}, {"slug_name": "planet-geometry", "product_type": "Planet Geometry Index", "product_count": 1, "download_count": 2, "download_size": 1368541, "download_size_pretty": "1M"}, {"slug_name": "moon-geometry", "product_type": "Moon Geometry Index", "product_count": 1, "download_count": 2, "download_size": 4095042, "download_size_pretty": "3M"}, {"slug_name": "ring-geometry", "product_type": "Ring Geometry Index", "product_count": 1, "download_count": 2, "download_size": 2235923, "download_size_pretty": "2M"}]], ["Browse Products", [{"slug_name": "browse-thumb", "product_type": "Browse Image (thumbnail)", "product_count": 1, "download_count": 1, "download_size": 999, "download_size_pretty": "999B"}, {"slug_name": "browse-small", "product_type": "Browse Image (small)", "product_count": 1, "download_count": 1, "download_size": 2977, "download_size_pretty": "2K"}, {"slug_name": "browse-medium", "product_type": "Browse Image (medium)", "product_count": 1, "download_count": 1, "download_size": 7860, "download_size_pretty": "7K"}, {"slug_name": "browse-full", "product_type": "Browse Image (full-size)", "product_count": 1, "download_count": 1, "download_size": 23371, "download_size_pretty": "22K"}]], ["Cassini ISS-Specific Products", [{"slug_name": "coiss-raw", "product_type": "Raw image", "product_count": 1, "download_count": 4, "download_size": 1104427, "download_size_pretty": "1M"}, {"slug_name": "coiss-calib", "product_type": "Calibrated image", "product_count": 1, "download_count": 2, "download_size": 4206293, "download_size_pretty": "4M"}, {"slug_name": "coiss-thumb", "product_type": "Extra preview (thumbnail)", "product_count": 1, "download_count": 1, "download_size": 564, "download_size_pretty": "564B"}, {"slug_name": "coiss-medium", "product_type": "Extra preview (medium)", "product_count": 1, "download_count": 1, "download_size": 2849, "download_size_pretty": "2K"}, {"slug_name": "coiss-full", "product_type": "Extra preview (full)", "product_count": 1, "download_count": 1, "download_size": 259925, "download_size_pretty": "253K"}]]]}
        self._run_json_equal(url, expected, ignore='tooltip')
        url = '/opus/__cart/status.json?reqno=0'
        expected = {'count': 1, 'reqno': 0}
        self._run_json_equal(url, expected)

    def test__api_cart_add_download_two(self):
        "[test_cart_api.py] /__cart/add: two OPUSIDs with download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/add.json?opusid=co-iss-n1460960868&download=0&reqno=101010100'
        expected = {'count': 1, 'error': False, 'reqno': 101010100}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/add.json?opusid=co-iss-n1460960653&download=1&reqno=101010101'
        expected = {"error": False, "count": 2, "reqno": 101010101, "total_download_count": 32, "total_download_size": 19532454, "total_download_size_pretty": "18M", "product_cat_list": [["Metadata Products", [{"slug_name": "inventory", "product_type": "Target Body Inventory", "product_count": 2, "download_count": 2, "download_size": 409019, "download_size_pretty": "399K"}, {"slug_name": "planet-geometry", "product_type": "Planet Geometry Index", "product_count": 2, "download_count": 2, "download_size": 1368541, "download_size_pretty": "1M"}, {"slug_name": "moon-geometry", "product_type": "Moon Geometry Index", "product_count": 2, "download_count": 2, "download_size": 4095042, "download_size_pretty": "3M"}, {"slug_name": "ring-geometry", "product_type": "Ring Geometry Index", "product_count": 2, "download_count": 2, "download_size": 2235923, "download_size_pretty": "2M"}]], ["Browse Products", [{"slug_name": "browse-thumb", "product_type": "Browse Image (thumbnail)", "product_count": 2, "download_count": 2, "download_size": 3061, "download_size_pretty": "2K"}, {"slug_name": "browse-small", "product_type": "Browse Image (small)", "product_count": 2, "download_count": 2, "download_size": 9179, "download_size_pretty": "8K"}, {"slug_name": "browse-medium", "product_type": "Browse Image (medium)", "product_count": 2, "download_count": 2, "download_size": 23847, "download_size_pretty": "23K"}, {"slug_name": "browse-full", "product_type": "Browse Image (full-size)", "product_count": 2, "download_count": 2, "download_size": 59567, "download_size_pretty": "58K"}]], ["Cassini ISS-Specific Products", [{"slug_name": "coiss-raw", "product_type": "Raw image", "product_count": 2, "download_count": 6, "download_size": 2185416, "download_size_pretty": "2M"}, {"slug_name": "coiss-calib", "product_type": "Calibrated image", "product_count": 2, "download_count": 4, "download_size": 8412579, "download_size_pretty": "8M"}, {"slug_name": "coiss-thumb", "product_type": "Extra preview (thumbnail)", "product_count": 2, "download_count": 2, "download_size": 1322, "download_size_pretty": "1K"}, {"slug_name": "coiss-medium", "product_type": "Extra preview (medium)", "product_count": 2, "download_count": 2, "download_size": 7589, "download_size_pretty": "7K"}, {"slug_name": "coiss-full", "product_type": "Extra preview (full)", "product_count": 2, "download_count": 2, "download_size": 721369, "download_size_pretty": "704K"}]]]}
        self._run_json_equal(url, expected, ignore='tooltip')
        url = '/opus/__cart/status.json?reqno=0'
        expected = {'count': 2, 'reqno': 0}
        self._run_json_equal(url, expected)


            ##################################################
            ######### /__cart/remove.json: API TESTS #########
            ##################################################

    def test__api_cart_remove_no_reqno(self):
        "[test_cart_api.py] /__cart/remove: no reqno"
        url = '/opus/__cart/remove.json?opusid=co-iss-n1460961026'
        self._run_status_equal(url, 404, settings.HTTP404_MISSING_REQNO)

    def test__api_cart_remove_missing(self):
        "[test_cart_api.py] /__cart/remove: missing OPUSID no download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/remove.json?reqno=456'
        expected = {'count': 0, 'error': 'No opusid specified', 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/status.json?reqno=456'
        expected = {'count': 0, 'reqno': 456}
        self._run_json_equal(url, expected)

    def test__api_cart_remove_empty(self):
        "[test_cart_api.py] /__cart/remove: empty OPUSID no download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/remove.json?opusid=&reqno=456'
        expected = {'count': 0, 'error': 'No opusid specified', 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/status.json?reqno=456'
        expected = {'count': 0, 'reqno': 456}
        self._run_json_equal(url, expected)

    def test__api_cart_remove_one(self):
        "[test_cart_api.py] /__cart/remove: add+remove good OPUSID no download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/add.json?opusid=co-vims-v1484504505_ir&reqno=456'
        expected = {'count': 1, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/remove.json?opusid=co-vims-v1484504505_ir&reqno=456'
        expected = {'count': 0, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/status.json?reqno=456'
        expected = {'count': 0, 'reqno': 456}
        self._run_json_equal(url, expected)

    def test__api_cart_remove_duplicate(self):
        "[test_cart_api.py] /__cart/remove: duplicate OPUSID no download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/add.json?opusid=co-vims-v1484528864_ir&reqno=456'
        expected = {'count': 1, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/remove.json?opusid=co-vims-v1484528864_ir&reqno=456'
        expected = {'count': 0, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/remove.json?opusid=co-vims-v1484528864_ir&reqno=456'
        expected = {'count': 0, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/status.json?reqno=456'
        expected = {'count': 0, 'reqno': 456}
        self._run_json_equal(url, expected)

    def test__api_cart_remove_bad(self):
        "[test_cart_api.py] /__cart/remove: bad OPUSID no download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        # Removing an unknown opusid doesn't throw an error
        url = '/opus/__cart/remove.json?opusid=co-vims-v1484528864_irx&reqno=456'
        expected = {'count': 0, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/status.json?reqno=456'
        expected = {'count': 0, 'reqno': 456}
        self._run_json_equal(url, expected)

    def test__api_cart_remove_good_bad(self):
        "[test_cart_api.py] /__cart/remove: good+bad OPUSID no download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/add.json?opusid=co-vims-v1484528864_ir&reqno=456'
        expected = {'count': 1, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/remove.json?opusid=co-iss-xn1460961026&reqno=456'
        expected = {'count': 1, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/remove.json?opusid=co-vims-v1484528864_ir&reqno=456'
        expected = {'count': 0, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/status.json?reqno=456'
        expected = {'count': 0, 'reqno': 456}
        self._run_json_equal(url, expected)

    def test__api_cart_remove_mixture(self):
        "[test_cart_api.py] /__cart/remove: mixture no download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/add.json?opusid=vg-iss-2-s-c4360010&reqno=456'
        expected = {'count': 1, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/add.json?opusid=co-vims-v1484528864_ir&reqno=456'
        expected = {'count': 2, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/add.json?opusid=go-ssi-c0347174400&reqno=456'
        expected = {'count': 3, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/remove.json?opusid=WOOHOO&reqno=456'
        expected = {'count': 3, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/remove.json?opusid=co-vims-v1484528864_ir&reqno=456'
        expected = {'count': 2, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/remove.json?opusid=vg-iss-2-s-c4360010&reqno=456'
        expected = {'count': 1, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/remove.json?opusid=nh-mvic-mpf_000526016x&reqno=456'
        expected = {'count': 1, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/add.json?opusid=co-vims-v1484528864_ir&reqno=456'
        expected = {'count': 2, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/remove.json?opusid=co-vims-v1484528864_ir&reqno=456'
        expected = {'count': 1, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/status.json?reqno=456'
        expected = {'count': 1, 'reqno': 456}
        self._run_json_equal(url, expected)

    def test__api_cart_remove_missing(self):
        "[test_cart_api.py] /__cart/remove: missing OPUSID no download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/remove.json?reqno=124'
        expected = {'count': 0, 'error': 'No opusid specified', 'reqno': 124}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/status.json?reqno=456'
        expected = {'count': 0, 'reqno': 456}
        self._run_json_equal(url, expected)

    def test__api_cart_remove_one(self):
        "[test_cart_api.py] /__cart/remove: good OPUSID no download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/add.json?opusid=co-iss-n1460961026&reqno=456'
        expected = {'count': 1, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/remove.json?opusid=co-iss-n1460961026&reqno=123456'
        expected = {'count': 0, 'error': False, 'reqno': 123456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/status.json?reqno=789'
        expected = {'count': 0, 'reqno': 789}
        self._run_json_equal(url, expected)

    def test__api_cart_remove_bad(self):
        "[test_cart_api.py] /__cart/remove: bad OPUSID no download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/add.json?opusid=co-iss-xn1460961026&reqno=456'
        expected = {'count': 0, 'error': 'opusid not found', 'reqno': 456}
        self._run_json_equal(url, expected)
        # Removing an unknown opusid doesn't throw an error
        url = '/opus/__cart/remove.json?opusid=co-iss-xn1460961026&reqno=101010101'
        expected = {'count': 0, 'error': False, 'reqno': 101010101}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/status.json?reqno=0'
        expected = {'count': 0, 'reqno': 0}
        self._run_json_equal(url, expected)

    def test__api_cart_remove_missing_download(self):
        "[test_cart_api.py] /__cart/remove: missing OPUSID with download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/remove.json?download=1&reqno=456'
        expected = {"error": "No opusid specified", "count": 0, "reqno": 456, "total_download_count": 0, "total_download_size": 0, "total_download_size_pretty": "0B", "product_cat_list": []}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/status.json?reqno=456'
        expected = {'count': 0, 'reqno': 456}
        self._run_json_equal(url, expected)

    def test__api_cart_remove_one_download(self):
        "[test_cart_api.py] /__cart/remove: good OPUSID with download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/add.json?opusid=co-iss-n1460961026&reqno=456'
        expected = {'count': 1, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/remove.json?opusid=co-iss-n1460961026&reqno=123456&download=1'
        expected = {'count': 0, 'error': False, 'reqno': 123456, "total_download_count": 0, "total_download_size": 0, "total_download_size_pretty": "0B", "product_cat_list": []}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/status.json?reqno=789'
        expected = {'count': 0, 'reqno': 789}
        self._run_json_equal(url, expected)

    def test__api_cart_add_two_remove_one_download(self):
        "[test_cart_api.py] /__cart/remove: two OPUSIDs remove one with download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/add.json?opusid=co-iss-n1460960868&download=0&reqno=101010100'
        expected = {'count': 1, 'error': False, 'reqno': 101010100}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/add.json?opusid=co-iss-n1460960653&download=&reqno=101010101'
        expected = {"error": False, "count": 2, "reqno": 101010101}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/remove.json?opusid=co-iss-n1460960868&download=1&reqno=101010102'
        expected = {'count': 1, 'error': False, 'reqno': 101010102, "total_download_count": 21, "total_download_size": 13717790, "total_download_size_pretty": "13M", "product_cat_list": [["Metadata Products", [{"slug_name": "inventory", "product_type": "Target Body Inventory", "product_count": 1, "download_count": 2, "download_size": 409019, "download_size_pretty": "399K"}, {"slug_name": "planet-geometry", "product_type": "Planet Geometry Index", "product_count": 1, "download_count": 2, "download_size": 1368541, "download_size_pretty": "1M"}, {"slug_name": "moon-geometry", "product_type": "Moon Geometry Index", "product_count": 1, "download_count": 2, "download_size": 4095042, "download_size_pretty": "3M"}, {"slug_name": "ring-geometry", "product_type": "Ring Geometry Index", "product_count": 1, "download_count": 2, "download_size": 2235923, "download_size_pretty": "2M"}]], ["Browse Products", [{"slug_name": "browse-thumb", "product_type": "Browse Image (thumbnail)", "product_count": 1, "download_count": 1, "download_size": 999, "download_size_pretty": "999B"}, {"slug_name": "browse-small", "product_type": "Browse Image (small)", "product_count": 1, "download_count": 1, "download_size": 2977, "download_size_pretty": "2K"}, {"slug_name": "browse-medium", "product_type": "Browse Image (medium)", "product_count": 1, "download_count": 1, "download_size": 7860, "download_size_pretty": "7K"}, {"slug_name": "browse-full", "product_type": "Browse Image (full-size)", "product_count": 1, "download_count": 1, "download_size": 23371, "download_size_pretty": "22K"}]], ["Cassini ISS-Specific Products", [{"slug_name": "coiss-raw", "product_type": "Raw image", "product_count": 1, "download_count": 4, "download_size": 1104427, "download_size_pretty": "1M"}, {"slug_name": "coiss-calib", "product_type": "Calibrated image", "product_count": 1, "download_count": 2, "download_size": 4206293, "download_size_pretty": "4M"}, {"slug_name": "coiss-thumb", "product_type": "Extra preview (thumbnail)", "product_count": 1, "download_count": 1, "download_size": 564, "download_size_pretty": "564B"}, {"slug_name": "coiss-medium", "product_type": "Extra preview (medium)", "product_count": 1, "download_count": 1, "download_size": 2849, "download_size_pretty": "2K"}, {"slug_name": "coiss-full", "product_type": "Extra preview (full)", "product_count": 1, "download_count": 1, "download_size": 259925, "download_size_pretty": "253K"}]]]}
        self._run_json_equal(url, expected, ignore='tooltip')
        url = '/opus/__cart/status.json?reqno=789'
        expected = {'count': 1, 'reqno': 789}
        self._run_json_equal(url, expected)


            ####################################################
            ######### /__cart/addrange.json: API TESTS #########
            ####################################################

    def test__api_cart_addrange_no_reqno(self):
        "[test_cart_api.py] /__cart/addrange: no reqno"
        url = '/opus/__cart/addrange.json?volumeid=COVIMS_0006&range=co-vims-v1484504505_ir,co-vims-v1484504505_ir'
        self._run_status_equal(url, 404, settings.HTTP404_MISSING_REQNO)

    def test__api_cart_addrange_missing(self):
        "[test_cart_api.py] /__cart/addrange: missing range no download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/addrange.json?reqno=456'
        expected = {'count': 0, 'error': 'no range given', 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/status.json?reqno=456'
        expected = {'count': 0, 'reqno': 456}
        self._run_json_equal(url, expected)

    def test__api_cart_addrange_empty(self):
        "[test_cart_api.py] /__cart/addrange: empty range no download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/addrange.json?range=&reqno=456'
        expected = {'count': 0, 'error': 'no range given', 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/status.json?reqno=456'
        expected = {'count': 0, 'reqno': 456}
        self._run_json_equal(url, expected)

    def test__api_cart_addrange_bad_range1(self):
        "[test_cart_api.py] /__cart/addrange: bad range 1 no download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/addrange.json?range=co-vims-v1484504505_ir&reqno=456'
        expected = {'count': 0, 'error': 'bad range', 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/status.json?reqno=456'
        expected = {'count': 0, 'reqno': 456}
        self._run_json_equal(url, expected)

    def test__api_cart_addrange_bad_range2(self):
        "[test_cart_api.py] /__cart/addrange: bad range 2 no download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/addrange.json?range=co-vims-v1484504505_ir,&reqno=456'
        expected = {'count': 0, 'error': 'bad range', 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/status.json?reqno=456'
        expected = {'count': 0, 'reqno': 456}
        self._run_json_equal(url, expected)

    def test__api_cart_addrange_bad_range3(self):
        "[test_cart_api.py] /__cart/addrange: bad range 3 no download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/addrange.json?range=,co-vims-v1484504505_ir&reqno=456'
        expected = {'count': 0, 'error': 'bad range', 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/status.json?reqno=456'
        expected = {'count': 0, 'reqno': 456}
        self._run_json_equal(url, expected)

    def test__api_cart_addrange_bad_range4(self):
        "[test_cart_api.py] /__cart/addrange: bad range 4 no download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/addrange.json?range=co-vims-v1484504505_ir,co-vims-v1484504505_ir,co-vims-v1484504505_ir&reqno=456'
        expected = {'count': 0, 'error': 'bad range', 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/status.json?reqno=456'
        expected = {'count': 0, 'reqno': 456}
        self._run_json_equal(url, expected)

    def test__api_cart_addrange_one(self):
        "[test_cart_api.py] /__cart/addrange: one good OPUSID no download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/addrange.json?volumeid=COVIMS_0006&range=co-vims-v1484504505_ir,co-vims-v1484504505_ir&reqno=456'
        expected = {'count': 1, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/status.json?reqno=456'
        expected = {'count': 1, 'reqno': 456}
        self._run_json_equal(url, expected)

    def test__api_cart_addrange_duplicate(self):
        "[test_cart_api.py] /__cart/addrange: duplicate OPUSID no download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/add.json?opusid=co-vims-v1484528864_ir&reqno=456'
        expected = {'count': 1, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/addrange.json?volumeid=COVIMS_0006&range=co-vims-v1484528864_ir,co-vims-v1484528864_ir&reqno=456'
        expected = {'count': 1, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/status.json?reqno=456'
        expected = {'count': 1, 'reqno': 456}
        self._run_json_equal(url, expected)

    def test__api_cart_addrange_duplicate2(self):
        "[test_cart_api.py] /__cart/addrange: duplicate 2 no download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/addrange.json?volumeid=COVIMS_0006&range=co-vims-v1488642557_ir,co-vims-v1488646261_ir&reqno=456'
        expected = {'count': 17, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/addrange.json?volumeid=COVIMS_0006&range=co-vims-v1488642557_ir,co-vims-v1488646261_ir&reqno=456'
        expected = {'count': 17, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/status.json?reqno=456'
        expected = {'count': 17, 'reqno': 456}
        self._run_json_equal(url, expected)

    def test__api_cart_addrange_duplicate3(self):
        "[test_cart_api.py] /__cart/addrange: duplicate 3 no download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/addrange.json?volumeid=COVIMS_0006&range=co-vims-v1488642557_ir,co-vims-v1488646261_ir&reqno=456'
        expected = {'count': 17, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/addrange.json?volumeid=COVIMS_0006&range=co-vims-v1488644667_vis,co-vims-v1488647105_vis&reqno=456'
        expected = {'count': 22, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/status.json?reqno=456'
        expected = {'count': 22, 'reqno': 456}
        self._run_json_equal(url, expected)

    def test__api_cart_addrange_duplicate4(self):
        "[test_cart_api.py] /__cart/addrange: duplicate 4 no download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/addrange.json?volumeid=COVIMS_0006&range=co-vims-v1488642557_ir,co-vims-v1488646261_ir&reqno=456'
        expected = {'count': 17, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/addrange.json?volumeid=COVIMS_0006&range=co-vims-v1488642979_ir,co-vims-v1488647105_vis&reqno=456'
        expected = {'count': 22, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/status.json?reqno=456'
        expected = {'count': 22, 'reqno': 456}
        self._run_json_equal(url, expected)

    def test__api_cart_addrange_duplicate5(self):
        "[test_cart_api.py] /__cart/addrange: duplicate 5 no download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/add.json?opusid=co-vims-v1488642557_ir&reqno=456'
        expected = {'count': 1, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/addrange.json?volumeid=COVIMS_0006&range=co-vims-v1488642557_ir,co-vims-v1488646261_ir&reqno=456'
        expected = {'count': 17, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/status.json?reqno=456'
        expected = {'count': 17, 'reqno': 456}
        self._run_json_equal(url, expected)

    def test__api_cart_addrange_duplicate6(self):
        "[test_cart_api.py] /__cart/addrange: duplicate 6 no download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/addrange.json?volumeid=COVIMS_0006&range=co-vims-v1488642557_ir,co-vims-v1488646261_ir&reqno=456'
        expected = {'count': 17, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/add.json?opusid=co-vims-v1488642557_ir&reqno=456'
        expected = {'count': 17, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/status.json?reqno=456'
        expected = {'count': 17, 'reqno': 456}
        self._run_json_equal(url, expected)

    def test__api_cart_addrange_bad_opusid(self):
        "[test_cart_api.py] /__cart/addrange: bad OPUSID no download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/addrange.json?volumeid=COVIMS_0006&range=co-vims-v1484528864_irx,co-vims-v1484528864_ir&reqno=456'
        expected = {'count': 0, 'error': 'opusid not found', 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/status.json?reqno=456'
        expected = {'count': 0, 'reqno': 456}
        self._run_json_equal(url, expected)

    def test__api_cart_addrange_bad_opusid2(self):
        "[test_cart_api.py] /__cart/addrange: bad OPUSID 2 no download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/addrange.json?volumeid=COVIMS_0006&range=co-vims-v1484528864_ir,co-vims-v1484528864_irx&reqno=456'
        expected = {'count': 0, 'error': 'opusid not found', 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/status.json?reqno=456'
        expected = {'count': 0, 'reqno': 456}
        self._run_json_equal(url, expected)

    def test__api_cart_addrange_not_search(self):
        "[test_cart_api.py] /__cart/addrange: OPUSID not in search no download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/addrange.json?volumeid=COVIMS_0006&range=vg-iss-2-s-c4360001,vg-iss-2-s-c4360001&reqno=456'
        expected = {'count': 0, 'error': 'opusid not found', 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/status.json?reqno=456'
        expected = {'count': 0, 'reqno': 456}
        self._run_json_equal(url, expected)

    def test__api_cart_addrange_bad_search(self):
        "[test_cart_api.py] /__cart/addrange: bad search no download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/addrange.json?volumeidXX=COVIMS_0006&range=vg-iss-2-s-c4360001,vg-iss-2-s-c4360001&reqno=456'
        expected = {'count': 0, 'error': 'bad search', 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/status.json?reqno=456'
        expected = {'count': 0, 'reqno': 456}
        self._run_json_equal(url, expected)

    def test__api_cart_addrange_multi(self):
        "[test_cart_api.py] /__cart/addrange: multiple no download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/addrange.json?volumeid=COVIMS_0006&range=co-vims-v1488642557_ir,co-vims-v1488646261_ir&reqno=456'
        expected = {'count': 17, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/status.json?reqno=456'
        expected = {'count': 17, 'reqno': 456}
        self._run_json_equal(url, expected)

    def test__api_cart_addrange_multi_reverse(self):
        "[test_cart_api.py] /__cart/addrange: multiple reversed no download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/addrange.json?volumeid=COVIMS_0006&range=co-vims-v1488646261_ir,co-vims-v1488642557_ir&reqno=456'
        expected = {'count': 17, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/status.json?reqno=456'
        expected = {'count': 17, 'reqno': 456}
        self._run_json_equal(url, expected)

    def test__api_cart_addrange_multi_sort(self):
        "[test_cart_api.py] /__cart/addrange: multiple nonstandard sort no download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/addrange.json?volumeid=COVIMS_0006&instrument=Cassini+VIMS&primaryfilespec=8864&order=COVIMSswathlength,-time1,-opusid&range=co-vims-v1488649724_vis,co-vims-v1488647527_ir&reqno=456'
        expected = {'count': 10, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/status.json?reqno=456'
        expected = {'count': 10, 'reqno': 456}
        self._run_json_equal(url, expected)

    def test__api_cart_addrange_missing(self):
        "[test_cart_api.py] /__cart/addrange: missing range no download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/addrange.json?reqno=124'
        expected = {'count': 0, 'error': 'no range given', 'reqno': 124}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/status.json?reqno=456'
        expected = {'count': 0, 'reqno': 456}
        self._run_json_equal(url, expected)

    def test__api_cart_addrange_one(self):
        "[test_cart_api.py] /__cart/addrange: one good OPUSID no download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/addrange.json?volumeid=COVIMS_0006&range=co-vims-v1484504505_ir,co-vims-v1484504505_ir&reqno=567'
        expected = {'count': 1, 'error': False, 'reqno': 567}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/status.json?reqno=456'
        expected = {'count': 1, 'reqno': 456}
        self._run_json_equal(url, expected)

    def test__api_cart_addrange_missing_download(self):
        "[test_cart_api.py] /__cart/addrange: missing range with download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/addrange.json?download=1&reqno=456'
        expected = {"error": "no range given", "count": 0, "reqno": 456, "total_download_count": 0, "total_download_size": 0, "total_download_size_pretty": "0B", "product_cat_list": []}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/status.json?reqno=456'
        expected = {'count': 0, 'reqno': 456}
        self._run_json_equal(url, expected)

    def test__api_cart_addrange_multi_download(self):
        "[test_cart_api.py] /__cart/addrange: multiple with download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/addrange.json?volumeid=COVIMS_0006&range=co-vims-v1488642557_ir,co-vims-v1488646261_ir&reqno=1234567&download=1'
        expected = {"error": False, "count": 17, "reqno": 1234567, "total_download_count": 92, "total_download_size": 9224834, "total_download_size_pretty": "8M", "product_cat_list": [["Metadata Products", [{"slug_name": "inventory", "product_type": "Target Body Inventory", "product_count": 17, "download_count": 2, "download_size": 415545, "download_size_pretty": "405K"}, {"slug_name": "planet-geometry", "product_type": "Planet Geometry Index", "product_count": 17, "download_count": 2, "download_size": 1527684, "download_size_pretty": "1M"}, {"slug_name": "moon-geometry", "product_type": "Moon Geometry Index", "product_count": 17, "download_count": 2, "download_size": 481067, "download_size_pretty": "469K"}, {"slug_name": "ring-geometry", "product_type": "Ring Geometry Index", "product_count": 17, "download_count": 2, "download_size": 2448696, "download_size_pretty": "2M"}]], ["Browse Products", [{"slug_name": "browse-thumb", "product_type": "Browse Image (thumbnail)", "product_count": 17, "download_count": 9, "download_size": 82840, "download_size_pretty": "80K"}, {"slug_name": "browse-small", "product_type": "Browse Image (small)", "product_count": 17, "download_count": 9, "download_size": 227327, "download_size_pretty": "221K"}, {"slug_name": "browse-medium", "product_type": "Browse Image (medium)", "product_count": 17, "download_count": 9, "download_size": 233338, "download_size_pretty": "227K"}, {"slug_name": "browse-full", "product_type": "Browse Image (full-size)", "product_count": 17, "download_count": 9, "download_size": 233338, "download_size_pretty": "227K"}]], ["Cassini VIMS-Specific Products", [{"slug_name": "covims-raw", "product_type": "Raw cube", "product_count": 17, "download_count": 21, "download_size": 2919003, "download_size_pretty": "2M"}, {"slug_name": "covims-thumb", "product_type": "Extra preview (thumbnail)", "product_count": 17, "download_count": 9, "download_size": 17411, "download_size_pretty": "17K"}, {"slug_name": "covims-medium", "product_type": "Extra preview (medium)", "product_count": 17, "download_count": 9, "download_size": 183437, "download_size_pretty": "179K"}, {"slug_name": "covims-full", "product_type": "Extra preview (full)", "product_count": 17, "download_count": 9, "download_size": 455148, "download_size_pretty": "444K"}]]]}
        self._run_json_equal(url, expected, ignore='tooltip')
        url = '/opus/__cart/status.json?reqno=456'
        expected = {'count': 17, 'reqno': 456}
        self._run_json_equal(url, expected)


            #######################################################
            ######### /__cart/removerange.json: API TESTS #########
            #######################################################

    def test__api_cart_removerange_no_reqno(self):
        "[test_cart_api.py] /__cart/removerange: no reqno"
        url = '/opus/__cart/removerange.json?volumeid=COVIMS_0006&range=co-vims-v1484504505_ir,co-vims-v1484504505_ir'
        self._run_status_equal(url, 404, settings.HTTP404_MISSING_REQNO)

    def test__api_cart_removerange_missing(self):
        "[test_cart_api.py] /__cart/removerange: missing range no download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/removerange.json?reqno=456'
        expected = {'count': 0, 'error': 'no range given', 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/status.json?reqno=456'
        expected = {'count': 0, 'reqno': 456}
        self._run_json_equal(url, expected)

    def test__api_cart_removerange_empty(self):
        "[test_cart_api.py] /__cart/removerange: empty range no download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/removerange.json?range=&reqno=456'
        expected = {'count': 0, 'error': 'no range given', 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/status.json?reqno=456'
        expected = {'count': 0, 'reqno': 456}
        self._run_json_equal(url, expected)

    def test__api_cart_removerange_bad_range1(self):
        "[test_cart_api.py] /__cart/removerange: bad range 1 no download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/removerange.json?range=co-vims-v1484504505_ir&reqno=456'
        expected = {'count': 0, 'error': 'bad range', 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/status.json?reqno=456'
        expected = {'count': 0, 'reqno': 456}
        self._run_json_equal(url, expected)

    def test__api_cart_removerange_bad_range2(self):
        "[test_cart_api.py] /__cart/removerange: bad range 2 no download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/removerange.json?range=co-vims-v1484504505_ir,&reqno=456'
        expected = {'count': 0, 'error': 'bad range', 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/status.json?reqno=456'
        expected = {'count': 0, 'reqno': 456}
        self._run_json_equal(url, expected)

    def test__api_cart_removerange_bad_range3(self):
        "[test_cart_api.py] /__cart/removerange: bad range 3 no download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/removerange.json?range=,co-vims-v1484504505_ir&reqno=456'
        expected = {'count': 0, 'error': 'bad range', 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/status.json?reqno=456'
        expected = {'count': 0, 'reqno': 456}
        self._run_json_equal(url, expected)

    def test__api_cart_removerange_bad_range4(self):
        "[test_cart_api.py] /__cart/removerange: bad range 4 no download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/removerange.json?range=co-vims-v1484504505_ir,co-vims-v1484504505_ir,co-vims-v1484504505_ir&reqno=456'
        expected = {'count': 0, 'error': 'bad range', 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/status.json?reqno=456'
        expected = {'count': 0, 'reqno': 456}
        self._run_json_equal(url, expected)

    def test__api_cart_removerange_one(self):
        "[test_cart_api.py] /__cart/removerange: one good OPUSID no download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/add.json?opusid=co-vims-v1484504505_ir&reqno=456'
        expected = {'count': 1, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/removerange.json?volumeid=COVIMS_0006&range=co-vims-v1484504505_ir,co-vims-v1484504505_ir&reqno=456'
        expected = {'count': 0, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/status.json?reqno=456'
        expected = {'count': 0, 'reqno': 456}
        self._run_json_equal(url, expected)

    def test__api_cart_removerange_duplicate(self):
        "[test_cart_api.py] /__cart/removerange: duplicate OPUSID no download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/add.json?opusid=co-vims-v1484528864_ir&reqno=456'
        expected = {'count': 1, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/removerange.json?volumeid=COVIMS_0006&range=co-vims-v1484528864_ir,co-vims-v1484528864_ir&reqno=456'
        expected = {'count': 0, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/removerange.json?volumeid=COVIMS_0006&range=co-vims-v1484528864_ir,co-vims-v1484528864_ir&reqno=456'
        expected = {'count': 0, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/status.json?reqno=456'
        expected = {'count': 0, 'reqno': 456}
        self._run_json_equal(url, expected)

    def test__api_cart_removerange_duplicate2(self):
        "[test_cart_api.py] /__cart/removerange: duplicate 2 no download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/addrange.json?volumeid=COVIMS_0006&range=co-vims-v1488642557_ir,co-vims-v1488646261_ir&reqno=456'
        expected = {'count': 17, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/removerange.json?volumeid=COVIMS_0006&range=co-vims-v1488642557_ir,co-vims-v1488646261_ir&reqno=456'
        expected = {'count': 0, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/removerange.json?volumeid=COVIMS_0006&range=co-vims-v1488642557_ir,co-vims-v1488646261_ir&reqno=456'
        expected = {'count': 0, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/status.json?reqno=456'
        expected = {'count': 0, 'reqno': 456}
        self._run_json_equal(url, expected)

    def test__api_cart_removerange_duplicate3(self):
        "[test_cart_api.py] /__cart/removerange: duplicate 3 no download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/addrange.json?volumeid=COVIMS_0006&range=co-vims-v1488642557_ir,co-vims-v1488646261_ir&reqno=456'
        expected = {'count': 17, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/removerange.json?volumeid=COVIMS_0006&range=co-vims-v1488644667_vis,co-vims-v1488647105_vis&reqno=456'
        expected = {'count': 11, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/removerange.json?volumeid=COVIMS_0006&range=co-vims-v1488644667_vis,co-vims-v1488647105_vis&reqno=456'
        expected = {'count': 11, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/status.json?reqno=456'
        expected = {'count': 11, 'reqno': 456}
        self._run_json_equal(url, expected)

    def test__api_cart_removerange_bad_opusid(self):
        "[test_cart_api.py] /__cart/removerange: bad OPUSID no download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/removerange.json?volumeid=COVIMS_0006&range=co-vims-v1484528864_irx,co-vims-v1484528864_ir&reqno=456'
        expected = {'count': 0, 'error': 'opusid not found', 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/status.json?reqno=456'
        expected = {'count': 0, 'reqno': 456}
        self._run_json_equal(url, expected)

    def test__api_cart_removerange_bad_opusid2(self):
        "[test_cart_api.py] /__cart/removerange: bad OPUSID 2 no download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/addrange.json?volumeid=COVIMS_0006&range=co-vims-v1484528864_ir,co-vims-v1484528864_irx&reqno=456'
        expected = {'count': 0, 'error': 'opusid not found', 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/status.json?reqno=456'
        expected = {'count': 0, 'reqno': 456}
        self._run_json_equal(url, expected)

    def test__api_cart_removerange_not_search(self):
        "[test_cart_api.py] /__cart/removerange: OPUSID not in search no download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/removerange.json?volumeid=COVIMS_0006&range=vg-iss-2-s-c4360001,vg-iss-2-s-c4360001&reqno=456'
        expected = {'count': 0, 'error': 'opusid not found', 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/status.json?reqno=456'
        expected = {'count': 0, 'reqno': 456}
        self._run_json_equal(url, expected)

    def test__api_cart_removerange_bad_search(self):
        "[test_cart_api.py] /__cart/removerange: bad search no download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/removerange.json?volumeidXX=COVIMS_0006&range=vg-iss-2-s-c4360001,vg-iss-2-s-c4360001&reqno=456'
        expected = {'count': 0, 'error': 'bad search', 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/status.json?reqno=456'
        expected = {'count': 0, 'reqno': 456}
        self._run_json_equal(url, expected)

    def test__api_cart_removerange_multi(self):
        "[test_cart_api.py] /__cart/removerange: multiple no download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/addrange.json?volumeid=COVIMS_0006&range=co-vims-v1488642557_ir,co-vims-v1488646261_ir&reqno=456'
        expected = {'count': 17, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/removerange.json?volumeid=COVIMS_0006&range=co-vims-v1488642979_vis,co-vims-v1488644245_vis&reqno=456'
        expected = {'count': 10, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/status.json?reqno=456'
        expected = {'count': 10, 'reqno': 456}
        self._run_json_equal(url, expected)

    def test__api_cart_removerange_multi_reverse(self):
        "[test_cart_api.py] /__cart/removerange: multiple reversed no download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/addrange.json?volumeid=COVIMS_0006&range=co-vims-v1488642557_ir,co-vims-v1488646261_ir&reqno=456'
        expected = {'count': 17, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/removerange.json?volumeid=COVIMS_0006&range=co-vims-v1488644245_vis,co-vims-v1488642979_vis&reqno=456'
        expected = {'count': 10, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/status.json?reqno=456'
        expected = {'count': 10, 'reqno': 456}
        self._run_json_equal(url, expected)

    def test__api_cart_removerange_multi_sort(self):
        "[test_cart_api.py] /__cart/removerange: multiple nonstandard sort no download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/addrange.json?volumeid=COVIMS_0006&order=COVIMSswathlength,-time1,opusid&range=co-vims-v1490784910_ir,co-vims-v1490782254_vis&reqno=456'
        expected = {'count': 10, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        # Note sort reverses opusid! This leaves two observations behind
        # because _ir and _vis are in a different order for each observation
        # pair
        url = '/opus/__cart/removerange.json?volumeid=COVIMS_0006&order=COVIMSswathlength,-time1,-opusid&range=co-vims-v1490784910_ir,co-vims-v1490782254_vis&reqno=456'
        expected = {'count': 2, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/status.json?reqno=456'
        expected = {'count': 2, 'reqno': 456}
        self._run_json_equal(url, expected)

    def test__api_cart_removerange_missing(self):
        "[test_cart_api.py] /__cart/removerange: missing range no download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/removerange.json?reqno=124'
        expected = {'count': 0, 'error': 'no range given', 'reqno': 124}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/status.json?reqno=456'
        expected = {'count': 0, 'reqno': 456}
        self._run_json_equal(url, expected)

    def test__api_cart_removerange_one(self):
        "[test_cart_api.py] /__cart/removerange: one good OPUSID no download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/removerange.json?volumeid=COVIMS_0006&range=co-vims-v1484504505_ir,co-vims-v1484504505_ir&reqno=567'
        expected = {'count': 0, 'error': False, 'reqno': 567}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/status.json?reqno=456'
        expected = {'count': 0, 'reqno': 456}
        self._run_json_equal(url, expected)

    def test__api_cart_removerange_missing_download(self):
        "[test_cart_api.py] /__cart/removerange: missing range with download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/removerange.json?download=1&reqno=456'
        expected = {"error": "no range given", "count": 0, "reqno": 456, "total_download_count": 0, "total_download_size": 0, "total_download_size_pretty": "0B", "product_cat_list": []}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/status.json?reqno=456'
        expected = {'count': 0, 'reqno': 456}
        self._run_json_equal(url, expected)

    def test__api_cart_removerange_multi_download(self):
        "[test_cart_api.py] /__cart/removerange: multiple with download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/addrange.json?volumeid=COVIMS_0006&range=co-vims-v1488642557_ir,co-vims-v1488646261_ir&reqno=1234567'
        expected = {"error": False, "count": 17, "reqno": 1234567}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/removerange.json?volumeid=COVIMS_0006&range=co-vims-v1488642135_ir,co-vims-v1488643823_ir&reqno=12345678&download=1'
        expected = {"error": False, "count": 10, "reqno": 12345678, "total_download_count": 65, "total_download_size": 7770738, "total_download_size_pretty": "7M", "product_cat_list": [["Metadata Products", [{"slug_name": "inventory", "product_type": "Target Body Inventory", "product_count": 10, "download_count": 2, "download_size": 415545, "download_size_pretty": "405K"}, {"slug_name": "planet-geometry", "product_type": "Planet Geometry Index", "product_count": 10, "download_count": 2, "download_size": 1527684, "download_size_pretty": "1M"}, {"slug_name": "moon-geometry", "product_type": "Moon Geometry Index", "product_count": 10, "download_count": 2, "download_size": 481067, "download_size_pretty": "469K"}, {"slug_name": "ring-geometry", "product_type": "Ring Geometry Index", "product_count": 10, "download_count": 2, "download_size": 2448696, "download_size_pretty": "2M"}]], ["Browse Products", [{"slug_name": "browse-thumb", "product_type": "Browse Image (thumbnail)", "product_count": 10, "download_count": 6, "download_size": 54402, "download_size_pretty": "53K"}, {"slug_name": "browse-small", "product_type": "Browse Image (small)", "product_count": 10, "download_count": 6, "download_size": 149668, "download_size_pretty": "146K"}, {"slug_name": "browse-medium", "product_type": "Browse Image (medium)", "product_count": 10, "download_count": 6, "download_size": 153800, "download_size_pretty": "150K"}, {"slug_name": "browse-full", "product_type": "Browse Image (full-size)", "product_count": 10, "download_count": 6, "download_size": 153800, "download_size_pretty": "150K"}]], ["Cassini VIMS-Specific Products", [{"slug_name": "covims-raw", "product_type": "Raw cube", "product_count": 10, "download_count": 15, "download_size": 1948066, "download_size_pretty": "1M"}, {"slug_name": "covims-thumb", "product_type": "Extra preview (thumbnail)", "product_count": 10, "download_count": 6, "download_size": 11718, "download_size_pretty": "11K"}, {"slug_name": "covims-medium", "product_type": "Extra preview (medium)", "product_count": 10, "download_count": 6, "download_size": 122860, "download_size_pretty": "119K"}, {"slug_name": "covims-full", "product_type": "Extra preview (full)", "product_count": 10, "download_count": 6, "download_size": 303432, "download_size_pretty": "296K"}]]]}
        self._run_json_equal(url, expected, ignore='tooltip')
        url = '/opus/__cart/status.json?reqno=456'
        expected = {'count': 10, 'reqno': 456}
        self._run_json_equal(url, expected)


            ##################################################
            ######### /__cart/addall.json: API TESTS #########
            ##################################################

    def test__api_cart_addall_no_reqno(self):
        "[test_cart_api.py] /__cart/addall: no reqno"
        url = '/opus/__cart/addall.json?volumeid=VGISS_6210'
        self._run_status_equal(url, 404, settings.HTTP404_MISSING_REQNO)

    def test__api_cart_addall_one(self):
        "[test_cart_api.py] /__cart/addall: one time no download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/addall.json?volumeid=VGISS_6210&reqno=456'
        expected = {'count': 906, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/status.json?reqno=456'
        expected = {'count': 906, 'reqno': 456}
        self._run_json_equal(url, expected)

    def test__api_cart_addall_duplicate(self):
        "[test_cart_api.py] /__cart/addall: twice no download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/addall.json?volumeid=VGISS_6210&reqno=456'
        expected = {'count': 906, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/status.json?reqno=456'
        expected = {'count': 906, 'reqno': 456}
        self._run_json_equal(url, expected)

    def test__api_cart_addall_duplicate2(self):
        "[test_cart_api.py] /__cart/addall: add plus addall no download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/addrange.json?volumeid=VGISS_6210&range=vg-iss-2-s-c4360037,vg-iss-2-s-c4365644&reqno=456'
        expected = {'count': 597, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/addall.json?volumeid=VGISS_6210&reqno=456'
        expected = {'count': 906, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/status.json?reqno=456'
        expected = {'count': 906, 'reqno': 456}
        self._run_json_equal(url, expected)

    def test__api_cart_addall_bad_search(self):
        "[test_cart_api.py] /__cart/addall: bad search no download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/addall.json?volumeidXX=COVIMS_0006&reqno=456'
        expected = {'count': 0, 'error': 'bad search', 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/status.json?reqno=456'
        expected = {'count': 0, 'reqno': 456}
        self._run_json_equal(url, expected)

    def test__api_cart_addall_multi(self):
        "[test_cart_api.py] /__cart/addall: multiple no download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/addrange.json?volumeid=COVIMS_0006&range=co-vims-v1484506475_ir,co-vims-v1484509868_vis&reqno=456'
        expected = {'count': 10, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/addall.json?volumeid=COVIMS_0006&reqno=456'
        expected = {'count': 3544, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/removerange.json?volumeid=COVIMS_0006&range=co-vims-v1485893300_vis,co-vims-v1485894711_vis&reqno=456'
        expected = {'count': 3531, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/addall.json?volumeid=VGISS_6210&reqno=456'
        expected = {'count': 3531+906, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/status.json?reqno=456'
        expected = {'count': 3531+906, 'reqno': 456}
        self._run_json_equal(url, expected)

    def test__api_cart_addall_one(self):
        "[test_cart_api.py] /__cart/addall: one time no download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/addall.json?volumeid=VGISS_6210&reqno=987'
        expected = {'count': 906, 'error': False, 'reqno': 987}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/status.json?reqno=456'
        expected = {'count': 906, 'reqno': 456}
        self._run_json_equal(url, expected)

    def test__api_cart_addall_one_download(self):
        "[test_cart_api.py] /__cart/addall: one time with download"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/addall.json?volumeid=VGISS_8201&productid=12&reqno=9878&download=1'
        expected = {'count': 34, 'error': False, 'reqno': 9878, "total_download_count": 620, "total_download_size": 169444386, "total_download_size_pretty": "161M", "product_cat_list": [["Metadata Products", [{"slug_name": "inventory", "product_type": "Target Body Inventory", "product_count": 34, "download_count": 2, "download_size": 93792, "download_size_pretty": "91K"}, {"slug_name": "planet-geometry", "product_type": "Planet Geometry Index", "product_count": 34, "download_count": 2, "download_size": 307087, "download_size_pretty": "299K"}, {"slug_name": "moon-geometry", "product_type": "Moon Geometry Index", "product_count": 34, "download_count": 2, "download_size": 1775739, "download_size_pretty": "1M"}, {"slug_name": "ring-geometry", "product_type": "Ring Geometry Index", "product_count": 34, "download_count": 2, "download_size": 509807, "download_size_pretty": "497K"}]], ["Browse Products", [{"slug_name": "browse-thumb", "product_type": "Browse Image (thumbnail)", "product_count": 34, "download_count": 34, "download_size": 49298, "download_size_pretty": "48K"}, {"slug_name": "browse-small", "product_type": "Browse Image (small)", "product_count": 34, "download_count": 34, "download_size": 117246, "download_size_pretty": "114K"}, {"slug_name": "browse-medium", "product_type": "Browse Image (medium)", "product_count": 34, "download_count": 34, "download_size": 428816, "download_size_pretty": "418K"}, {"slug_name": "browse-full", "product_type": "Browse Image (full-size)", "product_count": 34, "download_count": 34, "download_size": 2020408, "download_size_pretty": "1M"}]], ["Voyager ISS-Specific Products", [{"slug_name": "vgiss-raw", "product_type": "Raw Image", "product_count": 34, "download_count": 68, "download_size": 28148748, "download_size_pretty": "26M"}, {"slug_name": "vgiss-cleaned", "product_type": "Cleaned Image", "product_count": 34, "download_count": 68, "download_size": 21936280, "download_size_pretty": "20M"}, {"slug_name": "vgiss-calib", "product_type": "Calibrated Image", "product_count": 34, "download_count": 68, "download_size": 43769972, "download_size_pretty": "41M"}, {"slug_name": "vgiss-geomed", "product_type": "Geometrically Corrected Image", "product_count": 34, "download_count": 68, "download_size": 68190894, "download_size_pretty": "65M"}, {"slug_name": "vgiss-resloc", "product_type": "Reseau Table", "product_count": 34, "download_count": 102, "download_size": 672296, "download_size_pretty": "656K"}, {"slug_name": "vgiss-geoma", "product_type": "Geometric Tiepoint Table", "product_count": 34, "download_count": 102, "download_size": 1424003, "download_size_pretty": "1M"}]]]}
        self._run_json_equal(url, expected, ignore='tooltip')
        url = '/opus/__cart/status.json?reqno=456'
        expected = {'count': 34, 'reqno': 456}
        self._run_json_equal(url, expected)


            ###############################################
            ######### /__cart/data.csv: API TESTS #########
            ###############################################

    def test__api_cart_datacsv_empty(self):
        "[test_cart_api.py] /__cart/datacsv: empty"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/data.csv?cols=opusid,instrument,planet'
        expected = b'OPUS ID,Instrument Name,Planet\n'
        self._run_csv_equal(url, expected)
        url = '/opus/__cart/status.json?reqno=456'
        expected = {'count': 0, 'reqno': 456}
        self._run_json_equal(url, expected)

    def test__api_cart_datacsv_multi(self):
        "[test_cart_api.py] /__cart/datacsv: multiple"
        url = '/opus/__cart/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__cart/addrange.json?volumeid=COVIMS_0006&range=co-vims-v1488549680_ir,co-vims-v1488550102_ir&reqno=456'
        expected = {'count': 3, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/opus/__cart/data.csv?cols=opusid,instrument,planet,target,time1,observationduration,COVIMSchannel,CASSINIspacecraftclockcount1'
        expected = b'OPUS ID,Instrument Name,Planet,Intended Target Name,Observation Start Time,Observation Duration (secs),Channel [Cassini VIMS],Spacecraft Clock Start Count [Cassini]\nco-vims-v1488549680_ir,Cassini VIMS,Saturn,Saturn Rings,2005-03-03T13:34:47.689,415.5770,IR,1488549680.211\nco-vims-v1488549680_vis,Cassini VIMS,Saturn,Saturn Rings,2005-03-03T13:34:47.689,415.5770,VIS,1488549680.211\nco-vims-v1488550102_ir,Cassini VIMS,Saturn,Saturn Rings,2005-03-03T13:41:49.683,415.5770,IR,1488550102.209\n'
        self._run_csv_equal(url, expected)
        url = '/opus/__cart/status.json?reqno=456'
        expected = {'count': 3, 'reqno': 456}
        self._run_json_equal(url, expected)


            ####################################################
            ######### /__cart/download.json: API TESTS #########
            ####################################################

    # XXX Need to implement tests


            ##################################################
            ######### /__zip/<opusid>.zip: API TESTS #########
            ##################################################

    # XXX Need to implement tests
