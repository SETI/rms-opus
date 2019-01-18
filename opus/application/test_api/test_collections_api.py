# opus/application/test_api/test_collections_api.py

import json
import requests
from unittest import TestCase

from django.db import connection
from rest_framework.test import RequestsClient

import settings

import logging
log = logging.getLogger(__name__)

cursor = connection.cursor()

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_COOKIE_NAME = 'opus-test-cookie'
settings.CACHE_BACKEND = 'dummy:///'

# url(r'^__collections/view.(?P<fmt>html|json)$', api_view_collection),
# url(r'^__collections/status.json$', api_collection_status),
# url(r'^__collections/data.csv$', api_get_collection_csv),
# url(r'^__collections/(?P<action>[add|remove|addrange|removerange|addall]+).json$', api_edit_collection),
# url(r'^__collections/reset.json$', api_reset_session),
# url(r'^__collections/download.zip$', api_create_download),
# url(r'^__zip/(?P<opus_id>[-\w]+).json$', api_create_download),

class ApiCollectionsTests(TestCase):

    # disable error logging and trace output before test
    def setUp(self):
        self.maxDiff = None
        settings.CACHE_KEY_PREFIX = 'opustest:' + settings.OPUS_SCHEMA_NAME
        logging.disable(logging.ERROR)
        if settings.TEST_GO_LIVE:
            self.client = requests.Session()
        else:
            self.client = RequestsClient()

    # enable error logging and trace output after test
    def tearDown(self):
        logging.disable(logging.NOTSET)

    def _get_response(self, url):
        if not settings.TEST_GO_LIVE or settings.TEST_GO_LIVE == "production":
            url = "https://tools.pds-rings.seti.org" + url
        else:
            url = "http://dev.pds-rings.seti.org" + url
        return self.client.get(url)

    def _run_status_equal(self, url, expected):
        print(url)
        response = self._get_response(url)
        self.assertEqual(response.status_code, expected)

    def _run_json_equal(self, url, expected):
        print(url)
        response = self._get_response(url)
        self.assertEqual(response.status_code, 200)
        jdata = json.loads(response.content)
        print('Got:')
        print(str(jdata))
        print('Expected:')
        print(str(expected))
        self.assertEqual(expected, jdata)

    def _run_html_equal(self, url, expected):
        print(url)
        response = self._get_response(url)
        self.assertEqual(response.status_code, 200)
        print('Got:')
        print(str(response.content))
        print('Expected:')
        print(str(expected))
        self.assertEqual(expected, response.content)

    def _run_csv_equal(self, url, expected):
        print(url)
        response = self._get_response(url)
        self.assertEqual(response.status_code, 200)
        print('Got:')
        print(str(response.content))
        print('Expected:')
        print(str(expected))
        self.assertEqual(expected, response.content)


            ##############################################
            ######### /api/meta/reset: API TESTS #########
            ##############################################

    def test__api_collections_reset(self):
        "/collections/reset.json"
        url = '/opus/__collections/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__collections/status.json'
        expected = {'count': 0, 'reqno': None}
        self._run_json_equal(url, expected)


            ##############################################
            ######### /api/meta/add: API TESTS #########
            ##############################################

    def test__api_collections_add_missing(self):
        "/collections/add: Missing OPUSID no reqno no download"
        url = '/opus/__collections/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__collections/add.json'
        expected = {'count': 0, 'err': 'No opusid specified', 'reqno': None}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/status.json'
        expected = {'count': 0, 'reqno': None}
        self._run_json_equal(url, expected)

    def test__api_collections_add_empty(self):
        "/collections/add: Empty OPUSID no reqno no download"
        url = '/opus/__collections/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__collections/add.json?opusid='
        expected = {'count': 0, 'err': 'No opusid specified', 'reqno': None}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/status.json'
        expected = {'count': 0, 'reqno': None}
        self._run_json_equal(url, expected)

    def test__api_collections_add_one(self):
        "/collections/add: Good OPUSID no reqno no download"
        url = '/opus/__collections/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__collections/add.json?opusid=co-iss-n1460961026'
        expected = {'count': 1, 'err': False, 'reqno': None}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/status.json'
        expected = {'count': 1, 'reqno': None}
        self._run_json_equal(url, expected)

    def test__api_collections_add_duplicate(self):
        "/collections/add: Duplicate OPUSID no reqno no download"
        url = '/opus/__collections/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__collections/add.json?opusid=co-iss-n1460961026'
        expected = {'count': 1, 'err': False, 'reqno': None}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/add.json?opusid=co-iss-n1460961026'
        expected = {'count': 1, 'err': False, 'reqno': None}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/status.json'
        expected = {'count': 1, 'reqno': None}
        self._run_json_equal(url, expected)

    def test__api_collections_add_bad(self):
        "/collections/add: Bad OPUSID no reqno no download"
        url = '/opus/__collections/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__collections/add.json?opusid=co-iss-xn1460961026'
        expected = {'count': 0, 'err': 'opusid not found', 'reqno': None}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/status.json'
        expected = {'count': 0, 'reqno': None}
        self._run_json_equal(url, expected)

    def test__api_collections_add_good_bad(self):
        "/collections/add: Good+bad OPUSID no reqno no download"
        url = '/opus/__collections/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__collections/add.json?opusid=co-iss-n1460961026'
        expected = {'count': 1, 'err': False, 'reqno': None}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/add.json?opusid=co-iss-xn1460961026'
        expected = {'count': 1, 'err': 'opusid not found', 'reqno': None}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/status.json'
        expected = {'count': 1, 'reqno': None}
        self._run_json_equal(url, expected)

    def test__api_collections_add_mixture(self):
        "/collections/add: Mixture no reqno no download"
        url = '/opus/__collections/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__collections/add.json?opusid=vg-iss-2-s-c4360010'
        expected = {'count': 1, 'err': False, 'reqno': None}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/add.json?opusid=WOOHOO'
        expected = {'count': 1, 'err': 'opusid not found', 'reqno': None}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/add.json?opusid=vg-iss-2-s-c4360010'
        expected = {'count': 1, 'err': False, 'reqno': None}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/add.json?opusid=vg-iss-2-s-c4360010'
        expected = {'count': 1, 'err': False, 'reqno': None}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/add.json?opusid=hst-12003-wfc3-ibcz21ff'
        expected = {'count': 2, 'err': False, 'reqno': None}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/add.json?opusid=nh-mvic-mpf_000526016'
        expected = {'count': 2, 'err': 'opusid not found', 'reqno': None}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/status.json'
        expected = {'count': 2, 'reqno': None}
        self._run_json_equal(url, expected)

    def test__api_collections_add_missing_reqno(self):
        "/collections/add: Missing OPUSID with reqno no download"
        url = '/opus/__collections/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__collections/add.json?reqno=124'
        expected = {'count': 0, 'err': 'No opusid specified', 'reqno': 124}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/status.json?reqno=456'
        expected = {'count': 0, 'reqno': 456}
        self._run_json_equal(url, expected)

    def test__api_collections_add_one_reqno(self):
        "/collections/add: Good OPUSID with reqno no download"
        url = '/opus/__collections/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__collections/add.json?opusid=co-iss-n1460961026&reqno=12345'
        expected = {'count': 1, 'err': False, 'reqno': 12345}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/status.json?reqno=789'
        expected = {'count': 1, 'reqno': 789}
        self._run_json_equal(url, expected)

    def test__api_collections_add_bad_reqno(self):
        "/collections/add: Bad OPUSID with reqno no download"
        url = '/opus/__collections/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__collections/add.json?opusid=co-iss-xn1460961026&reqno=101010101'
        expected = {'count': 0, 'err': 'opusid not found', 'reqno': 101010101}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/status.json?reqno=0'
        expected = {'count': 0, 'reqno': 0}
        self._run_json_equal(url, expected)

    def test__api_collections_add_missing_download(self):
        "/collections/add: Missing OPUSID no reqno with download"
        url = '/opus/__collections/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__collections/add.json?download=1'
        expected = {"err": "No opusid specified", "count": 0, "reqno": None, "total_download_count": 0, "total_download_size": 0, "total_download_size_pretty": "0B", "product_cat_list": []}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/status.json'
        expected = {'count': 0, 'reqno': None}
        self._run_json_equal(url, expected)

    def test__api_collections_add_download_one(self):
        "/collections/add: Good OPUSID with reqno with download"
        url = '/opus/__collections/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__collections/add.json?opusid=co-iss-n1460960653&download=1&reqno=101010101'
        expected = {"err": False, "count": 1, "reqno": 101010101, "total_download_count": 21, "total_download_size": 13717790, "total_download_size_pretty": "13M", "product_cat_list": [["Metadata Products", [{"slug_name": "inventory", "product_type": "Target Body Inventory", "product_count": 1, "download_count": 2, "download_size": 409019, "download_size_pretty": "399K"}, {"slug_name": "planet-geometry", "product_type": "Planet Geometry Index", "product_count": 1, "download_count": 2, "download_size": 1368541, "download_size_pretty": "1M"}, {"slug_name": "moon-geometry", "product_type": "Moon Geometry Index", "product_count": 1, "download_count": 2, "download_size": 4095042, "download_size_pretty": "3M"}, {"slug_name": "ring-geometry", "product_type": "Ring Geometry Index", "product_count": 1, "download_count": 2, "download_size": 2235923, "download_size_pretty": "2M"}]], ["Browse Products", [{"slug_name": "browse-thumb", "product_type": "Browse Image (thumbnail)", "product_count": 1, "download_count": 1, "download_size": 999, "download_size_pretty": "999B"}, {"slug_name": "browse-small", "product_type": "Browse Image (small)", "product_count": 1, "download_count": 1, "download_size": 2977, "download_size_pretty": "2K"}, {"slug_name": "browse-medium", "product_type": "Browse Image (medium)", "product_count": 1, "download_count": 1, "download_size": 7860, "download_size_pretty": "7K"}, {"slug_name": "browse-full", "product_type": "Browse Image (full-size)", "product_count": 1, "download_count": 1, "download_size": 23371, "download_size_pretty": "22K"}]], ["Cassini ISS-Specific Products", [{"slug_name": "coiss-raw", "product_type": "Raw image", "product_count": 1, "download_count": 4, "download_size": 1104427, "download_size_pretty": "1M"}, {"slug_name": "coiss-calib", "product_type": "Calibrated image", "product_count": 1, "download_count": 2, "download_size": 4206293, "download_size_pretty": "4M"}, {"slug_name": "coiss-thumb", "product_type": "Extra preview (thumbnail)", "product_count": 1, "download_count": 1, "download_size": 564, "download_size_pretty": "564B"}, {"slug_name": "coiss-medium", "product_type": "Extra preview (medium)", "product_count": 1, "download_count": 1, "download_size": 2849, "download_size_pretty": "2K"}, {"slug_name": "coiss-full", "product_type": "Extra preview (full)", "product_count": 1, "download_count": 1, "download_size": 259925, "download_size_pretty": "253K"}]]]}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/status.json?reqno=0'
        expected = {'count': 1, 'reqno': 0}
        self._run_json_equal(url, expected)

    def test__api_collections_add_download_two(self):
        "/collections/add: Two OPUSIDs with reqno with download"
        url = '/opus/__collections/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__collections/add.json?opusid=co-iss-n1460960868&download=0&reqno=101010100'
        expected = {'count': 1, 'err': False, 'reqno': 101010100}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/add.json?opusid=co-iss-n1460960653&download=1&reqno=101010101'
        expected = {"err": False, "count": 2, "reqno": 101010101, "total_download_count": 32, "total_download_size": 19532454, "total_download_size_pretty": "18M", "product_cat_list": [["Metadata Products", [{"slug_name": "inventory", "product_type": "Target Body Inventory", "product_count": 2, "download_count": 2, "download_size": 409019, "download_size_pretty": "399K"}, {"slug_name": "planet-geometry", "product_type": "Planet Geometry Index", "product_count": 2, "download_count": 2, "download_size": 1368541, "download_size_pretty": "1M"}, {"slug_name": "moon-geometry", "product_type": "Moon Geometry Index", "product_count": 2, "download_count": 2, "download_size": 4095042, "download_size_pretty": "3M"}, {"slug_name": "ring-geometry", "product_type": "Ring Geometry Index", "product_count": 2, "download_count": 2, "download_size": 2235923, "download_size_pretty": "2M"}]], ["Browse Products", [{"slug_name": "browse-thumb", "product_type": "Browse Image (thumbnail)", "product_count": 2, "download_count": 2, "download_size": 3061, "download_size_pretty": "2K"}, {"slug_name": "browse-small", "product_type": "Browse Image (small)", "product_count": 2, "download_count": 2, "download_size": 9179, "download_size_pretty": "8K"}, {"slug_name": "browse-medium", "product_type": "Browse Image (medium)", "product_count": 2, "download_count": 2, "download_size": 23847, "download_size_pretty": "23K"}, {"slug_name": "browse-full", "product_type": "Browse Image (full-size)", "product_count": 2, "download_count": 2, "download_size": 59567, "download_size_pretty": "58K"}]], ["Cassini ISS-Specific Products", [{"slug_name": "coiss-raw", "product_type": "Raw image", "product_count": 2, "download_count": 6, "download_size": 2185416, "download_size_pretty": "2M"}, {"slug_name": "coiss-calib", "product_type": "Calibrated image", "product_count": 2, "download_count": 4, "download_size": 8412579, "download_size_pretty": "8M"}, {"slug_name": "coiss-thumb", "product_type": "Extra preview (thumbnail)", "product_count": 2, "download_count": 2, "download_size": 1322, "download_size_pretty": "1K"}, {"slug_name": "coiss-medium", "product_type": "Extra preview (medium)", "product_count": 2, "download_count": 2, "download_size": 7589, "download_size_pretty": "7K"}, {"slug_name": "coiss-full", "product_type": "Extra preview (full)", "product_count": 2, "download_count": 2, "download_size": 721369, "download_size_pretty": "704K"}]]]}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/status.json?reqno=0'
        expected = {'count': 2, 'reqno': 0}
        self._run_json_equal(url, expected)


            ###############################################
            ######### /api/meta/remove: API TESTS #########
            ###############################################

    def test__api_collections_remove_missing(self):
        "/collections/remove: Missing OPUSID no reqno no download"
        url = '/opus/__collections/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__collections/remove.json'
        expected = {'count': 0, 'err': 'No opusid specified', 'reqno': None}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/status.json'
        expected = {'count': 0, 'reqno': None}
        self._run_json_equal(url, expected)

    def test__api_collections_remove_empty(self):
        "/collections/remove: Empty OPUSID no reqno no download"
        url = '/opus/__collections/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__collections/remove.json?opusid='
        expected = {'count': 0, 'err': 'No opusid specified', 'reqno': None}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/status.json'
        expected = {'count': 0, 'reqno': None}
        self._run_json_equal(url, expected)

    def test__api_collections_remove_one(self):
        "/collections/remove: Add+remove good OPUSID no reqno no download"
        url = '/opus/__collections/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__collections/add.json?opusid=co-vims-v1484504505_ir'
        expected = {'count': 1, 'err': False, 'reqno': None}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/remove.json?opusid=co-vims-v1484504505_ir'
        expected = {'count': 0, 'err': False, 'reqno': None}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/status.json'
        expected = {'count': 0, 'reqno': None}
        self._run_json_equal(url, expected)

    def test__api_collections_remove_duplicate(self):
        "/collections/remove: Duplicate OPUSID no reqno no download"
        url = '/opus/__collections/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__collections/add.json?opusid=co-vims-v1484528864_ir'
        expected = {'count': 1, 'err': False, 'reqno': None}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/remove.json?opusid=co-vims-v1484528864_ir'
        expected = {'count': 0, 'err': False, 'reqno': None}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/remove.json?opusid=co-vims-v1484528864_ir'
        expected = {'count': 0, 'err': False, 'reqno': None}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/status.json'
        expected = {'count': 0, 'reqno': None}
        self._run_json_equal(url, expected)

    def test__api_collections_remove_bad(self):
        "/collections/remove: Bad OPUSID no reqno no download"
        url = '/opus/__collections/reset.json'
        self._run_status_equal(url, 200)
        # Removing an unknown opusid doesn't throw an error
        url = '/opus/__collections/remove.json?opusid=co-vims-v1484528864_irx'
        expected = {'count': 0, 'err': False, 'reqno': None}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/status.json'
        expected = {'count': 0, 'reqno': None}
        self._run_json_equal(url, expected)

    def test__api_collections_remove_good_bad(self):
        "/collections/remove: Good+bad OPUSID no reqno no download"
        url = '/opus/__collections/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__collections/add.json?opusid=co-vims-v1484528864_ir'
        expected = {'count': 1, 'err': False, 'reqno': None}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/remove.json?opusid=co-iss-xn1460961026'
        expected = {'count': 1, 'err': False, 'reqno': None}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/remove.json?opusid=co-vims-v1484528864_ir'
        expected = {'count': 0, 'err': False, 'reqno': None}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/status.json'
        expected = {'count': 0, 'reqno': None}
        self._run_json_equal(url, expected)

    def test__api_collections_remove_mixture(self):
        "/collections/remove: Mixture no reqno no download"
        url = '/opus/__collections/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__collections/add.json?opusid=vg-iss-2-s-c4360010'
        expected = {'count': 1, 'err': False, 'reqno': None}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/add.json?opusid=co-vims-v1484528864_ir'
        expected = {'count': 2, 'err': False, 'reqno': None}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/add.json?opusid=go-ssi-c0347174400'
        expected = {'count': 3, 'err': False, 'reqno': None}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/remove.json?opusid=WOOHOO'
        expected = {'count': 3, 'err': False, 'reqno': None}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/remove.json?opusid=co-vims-v1484528864_ir'
        expected = {'count': 2, 'err': False, 'reqno': None}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/remove.json?opusid=vg-iss-2-s-c4360010'
        expected = {'count': 1, 'err': False, 'reqno': None}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/remove.json?opusid=nh-mvic-mpf_000526016x'
        expected = {'count': 1, 'err': False, 'reqno': None}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/add.json?opusid=co-vims-v1484528864_ir'
        expected = {'count': 2, 'err': False, 'reqno': None}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/remove.json?opusid=co-vims-v1484528864_ir'
        expected = {'count': 1, 'err': False, 'reqno': None}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/status.json'
        expected = {'count': 1, 'reqno': None}
        self._run_json_equal(url, expected)

    def test__api_collections_remove_missing_reqno(self):
        "/collections/remove: Missing OPUSID with reqno no download"
        url = '/opus/__collections/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__collections/remove.json?reqno=124'
        expected = {'count': 0, 'err': 'No opusid specified', 'reqno': 124}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/status.json?reqno=456'
        expected = {'count': 0, 'reqno': 456}
        self._run_json_equal(url, expected)

    def test__api_collections_remove_one_reqno(self):
        "/collections/remove: Good OPUSID with reqno no download"
        url = '/opus/__collections/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__collections/add.json?opusid=co-iss-n1460961026'
        expected = {'count': 1, 'err': False, 'reqno': None}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/remove.json?opusid=co-iss-n1460961026&reqno=123456'
        expected = {'count': 0, 'err': False, 'reqno': 123456}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/status.json?reqno=789'
        expected = {'count': 0, 'reqno': 789}
        self._run_json_equal(url, expected)

    def test__api_collections_remove_bad_reqno(self):
        "/collections/remove: Bad OPUSID with reqno no download"
        url = '/opus/__collections/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__collections/add.json?opusid=co-iss-xn1460961026'
        expected = {'count': 0, 'err': 'opusid not found', 'reqno': None}
        self._run_json_equal(url, expected)
        # Removing an unknown opusid doesn't throw an error
        url = '/opus/__collections/remove.json?opusid=co-iss-xn1460961026&reqno=101010101'
        expected = {'count': 0, 'err': False, 'reqno': 101010101}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/status.json?reqno=0'
        expected = {'count': 0, 'reqno': 0}
        self._run_json_equal(url, expected)

    def test__api_collections_remove_missing_download(self):
        "/collections/remove: Missing OPUSID no reqno with download"
        url = '/opus/__collections/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__collections/remove.json?download=1'
        expected = {"err": "No opusid specified", "count": 0, "reqno": None, "total_download_count": 0, "total_download_size": 0, "total_download_size_pretty": "0B", "product_cat_list": []}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/status.json'
        expected = {'count': 0, 'reqno': None}
        self._run_json_equal(url, expected)

    def test__api_collections_remove_one_reqno_download(self):
        "/collections/remove: Good OPUSID with reqno with download"
        url = '/opus/__collections/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__collections/add.json?opusid=co-iss-n1460961026'
        expected = {'count': 1, 'err': False, 'reqno': None}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/remove.json?opusid=co-iss-n1460961026&reqno=123456&download=1'
        expected = {'count': 0, 'err': False, 'reqno': 123456, "total_download_count": 0, "total_download_size": 0, "total_download_size_pretty": "0B", "product_cat_list": []}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/status.json?reqno=789'
        expected = {'count': 0, 'reqno': 789}
        self._run_json_equal(url, expected)

    def test__api_collections_add_two_remove_one_reqno_download(self):
        "/collections/remove: Two OPUSIDs remove one with reqno with download"
        url = '/opus/__collections/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__collections/add.json?opusid=co-iss-n1460960868&download=0&reqno=101010100'
        expected = {'count': 1, 'err': False, 'reqno': 101010100}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/add.json?opusid=co-iss-n1460960653&download=&reqno=101010101'
        expected = {"err": False, "count": 2, "reqno": 101010101}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/remove.json?opusid=co-iss-n1460960868&download=1&reqno=101010102'
        expected = {'count': 1, 'err': False, 'reqno': 101010102, "total_download_count": 21, "total_download_size": 13717790, "total_download_size_pretty": "13M", "product_cat_list": [["Metadata Products", [{"slug_name": "inventory", "product_type": "Target Body Inventory", "product_count": 1, "download_count": 2, "download_size": 409019, "download_size_pretty": "399K"}, {"slug_name": "planet-geometry", "product_type": "Planet Geometry Index", "product_count": 1, "download_count": 2, "download_size": 1368541, "download_size_pretty": "1M"}, {"slug_name": "moon-geometry", "product_type": "Moon Geometry Index", "product_count": 1, "download_count": 2, "download_size": 4095042, "download_size_pretty": "3M"}, {"slug_name": "ring-geometry", "product_type": "Ring Geometry Index", "product_count": 1, "download_count": 2, "download_size": 2235923, "download_size_pretty": "2M"}]], ["Browse Products", [{"slug_name": "browse-thumb", "product_type": "Browse Image (thumbnail)", "product_count": 1, "download_count": 1, "download_size": 999, "download_size_pretty": "999B"}, {"slug_name": "browse-small", "product_type": "Browse Image (small)", "product_count": 1, "download_count": 1, "download_size": 2977, "download_size_pretty": "2K"}, {"slug_name": "browse-medium", "product_type": "Browse Image (medium)", "product_count": 1, "download_count": 1, "download_size": 7860, "download_size_pretty": "7K"}, {"slug_name": "browse-full", "product_type": "Browse Image (full-size)", "product_count": 1, "download_count": 1, "download_size": 23371, "download_size_pretty": "22K"}]], ["Cassini ISS-Specific Products", [{"slug_name": "coiss-raw", "product_type": "Raw image", "product_count": 1, "download_count": 4, "download_size": 1104427, "download_size_pretty": "1M"}, {"slug_name": "coiss-calib", "product_type": "Calibrated image", "product_count": 1, "download_count": 2, "download_size": 4206293, "download_size_pretty": "4M"}, {"slug_name": "coiss-thumb", "product_type": "Extra preview (thumbnail)", "product_count": 1, "download_count": 1, "download_size": 564, "download_size_pretty": "564B"}, {"slug_name": "coiss-medium", "product_type": "Extra preview (medium)", "product_count": 1, "download_count": 1, "download_size": 2849, "download_size_pretty": "2K"}, {"slug_name": "coiss-full", "product_type": "Extra preview (full)", "product_count": 1, "download_count": 1, "download_size": 259925, "download_size_pretty": "253K"}]]]}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/status.json?reqno=789'
        expected = {'count': 1, 'reqno': 789}
        self._run_json_equal(url, expected)


            #################################################
            ######### /api/meta/addrange: API TESTS #########
            #################################################

    def test__api_collections_addrange_missing(self):
        "/collections/addrange: Missing range no reqno no download"
        url = '/opus/__collections/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__collections/addrange.json'
        expected = {'count': 0, 'err': 'no range given', 'reqno': None}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/status.json'
        expected = {'count': 0, 'reqno': None}
        self._run_json_equal(url, expected)

    def test__api_collections_addrange_empty(self):
        "/collections/addrange: Empty range no reqno no download"
        url = '/opus/__collections/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__collections/addrange.json?range='
        expected = {'count': 0, 'err': 'no range given', 'reqno': None}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/status.json'
        expected = {'count': 0, 'reqno': None}
        self._run_json_equal(url, expected)

    def test__api_collections_addrange_bad_range1(self):
        "/collections/addrange: Bad range 1 no reqno no download"
        url = '/opus/__collections/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__collections/addrange.json?range=co-vims-v1484504505_ir'
        expected = {'count': 0, 'err': 'bad range', 'reqno': None}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/status.json'
        expected = {'count': 0, 'reqno': None}
        self._run_json_equal(url, expected)

    def test__api_collections_addrange_bad_range2(self):
        "/collections/addrange: Bad range 2 no reqno no download"
        url = '/opus/__collections/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__collections/addrange.json?range=co-vims-v1484504505_ir,'
        expected = {'count': 0, 'err': 'bad range', 'reqno': None}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/status.json'
        expected = {'count': 0, 'reqno': None}
        self._run_json_equal(url, expected)

    def test__api_collections_addrange_bad_range3(self):
        "/collections/addrange: Bad range 4 no reqno no download"
        url = '/opus/__collections/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__collections/addrange.json?range=,co-vims-v1484504505_ir'
        expected = {'count': 0, 'err': 'bad range', 'reqno': None}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/status.json'
        expected = {'count': 0, 'reqno': None}
        self._run_json_equal(url, expected)

    def test__api_collections_addrange_bad_range4(self):
        "/collections/addrange: Bad range 4 no reqno no download"
        url = '/opus/__collections/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__collections/addrange.json?range=co-vims-v1484504505_ir,co-vims-v1484504505_ir,co-vims-v1484504505_ir'
        expected = {'count': 0, 'err': 'bad range', 'reqno': None}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/status.json'
        expected = {'count': 0, 'reqno': None}
        self._run_json_equal(url, expected)

    def test__api_collections_addrange_one(self):
        "/collections/addrange: One good OPUSID no reqno no download"
        url = '/opus/__collections/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__collections/addrange.json?volumeid=COVIMS_0006&range=co-vims-v1484504505_ir,co-vims-v1484504505_ir'
        expected = {'count': 1, 'err': False, 'reqno': None}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/status.json'
        expected = {'count': 1, 'reqno': None}
        self._run_json_equal(url, expected)

    def test__api_collections_addrange_duplicate(self):
        "/collections/addrange: Duplicate OPUSID no reqno no download"
        url = '/opus/__collections/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__collections/add.json?opusid=co-vims-v1484528864_ir'
        expected = {'count': 1, 'err': False, 'reqno': None}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/addrange.json?volumeid=COVIMS_0006&range=co-vims-v1484528864_ir,co-vims-v1484528864_ir'
        expected = {'count': 1, 'err': False, 'reqno': None}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/status.json'
        expected = {'count': 1, 'reqno': None}
        self._run_json_equal(url, expected)

    def test__api_collections_addrange_bad(self):
        "/collections/addrange: Bad OPUSID no reqno no download"
        url = '/opus/__collections/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__collections/addrange.json?volumeid=COVIMS_0006&range=co-vims-v1484528864_irx,co-vims-v1484528864_ir'
        expected = {'count': 0, 'err': 'opusid not found', 'reqno': None}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/status.json'
        expected = {'count': 0, 'reqno': None}
        self._run_json_equal(url, expected)

    def test__api_collections_addrange_bad2(self):
        "/collections/addrange: Bad OPUSID 2 no reqno no download"
        url = '/opus/__collections/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__collections/addrange.json?volumeid=COVIMS_0006&range=co-vims-v1484528864_ir,co-vims-v1484528864_irx'
        expected = {'count': 0, 'err': 'opusid not found', 'reqno': None}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/status.json'
        expected = {'count': 0, 'reqno': None}
        self._run_json_equal(url, expected)

    def test__api_collections_addrange_multi(self):
        "/collections/addrange: Multiple no reqno no download"
        url = '/opus/__collections/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__collections/addrange.json?volumeid=COVIMS_0006&range=co-vims-v1488642557_ir,co-vims-v1488646261_ir'
        expected = {'count': 17, 'err': False, 'reqno': None}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/status.json'
        expected = {'count': 17, 'reqno': None}
        self._run_json_equal(url, expected)

    def test__api_collections_addrange_multi_reverse(self):
        "/collections/addrange: Multiple reversed no reqno no download"
        url = '/opus/__collections/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__collections/addrange.json?volumeid=COVIMS_0006&range=co-vims-v1488646261_ir,co-vims-v1488642557_ir'
        expected = {'count': 17, 'err': False, 'reqno': None}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/status.json'
        expected = {'count': 17, 'reqno': None}
        self._run_json_equal(url, expected)

    def test__api_collections_addrange_multi_sort(self):
        "/collections/addrange: Multiple nonstandard sort no reqno no download"
        url = '/opus/__collections/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__collections/addrange.json?volumeid=COVIMS_0006&instrument=Cassini+VIMS&primaryfilespec=8864&order=COVIMSswathlength1,-time1,-opusid&range=co-vims-v1488649724_vis,co-vims-v1488647527_ir'
        expected = {'count': 10, 'err': False, 'reqno': None}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/status.json'
        expected = {'count': 10, 'reqno': None}
        self._run_json_equal(url, expected)

    def test__api_collections_addrange_duplicate(self):
        "/collections/addrange: Duplicate no reqno no download"
        url = '/opus/__collections/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__collections/addrange.json?volumeid=COVIMS_0006&range=co-vims-v1488642557_ir,co-vims-v1488646261_ir'
        expected = {'count': 17, 'err': False, 'reqno': None}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/addrange.json?volumeid=COVIMS_0006&range=co-vims-v1488642557_ir,co-vims-v1488646261_ir'
        expected = {'count': 17, 'err': False, 'reqno': None}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/status.json'
        expected = {'count': 17, 'reqno': None}
        self._run_json_equal(url, expected)

    def test__api_collections_addrange_duplicate2(self):
        "/collections/addrange: Duplicate 2 no reqno no download"
        url = '/opus/__collections/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__collections/addrange.json?volumeid=COVIMS_0006&range=co-vims-v1488642557_ir,co-vims-v1488646261_ir'
        expected = {'count': 17, 'err': False, 'reqno': None}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/addrange.json?volumeid=COVIMS_0006&range=co-vims-v1488644667_vis,co-vims-v1488647105_vis'
        expected = {'count': 22, 'err': False, 'reqno': None}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/status.json'
        expected = {'count': 22, 'reqno': None}
        self._run_json_equal(url, expected)

    def test__api_collections_addrange_duplicate3(self):
        "/collections/addrange: Duplicate 3 no reqno no download"
        url = '/opus/__collections/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__collections/addrange.json?volumeid=COVIMS_0006&range=co-vims-v1488642557_ir,co-vims-v1488646261_ir'
        expected = {'count': 17, 'err': False, 'reqno': None}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/addrange.json?volumeid=COVIMS_0006&range=co-vims-v1488642979_ir,co-vims-v1488647105_vis'
        expected = {'count': 22, 'err': False, 'reqno': None}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/status.json'
        expected = {'count': 22, 'reqno': None}
        self._run_json_equal(url, expected)

    def test__api_collections_addrange_duplicate4(self):
        "/collections/addrange: Duplicate 4 no reqno no download"
        url = '/opus/__collections/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__collections/add.json?opusid=co-vims-v1488642557_ir'
        expected = {'count': 1, 'err': False, 'reqno': None}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/addrange.json?volumeid=COVIMS_0006&range=co-vims-v1488642557_ir,co-vims-v1488646261_ir'
        expected = {'count': 17, 'err': False, 'reqno': None}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/status.json'
        expected = {'count': 17, 'reqno': None}
        self._run_json_equal(url, expected)

    def test__api_collections_addrange_duplicate5(self):
        "/collections/addrange: Duplicate 5 no reqno no download"
        url = '/opus/__collections/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__collections/addrange.json?volumeid=COVIMS_0006&range=co-vims-v1488642557_ir,co-vims-v1488646261_ir'
        expected = {'count': 17, 'err': False, 'reqno': None}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/add.json?opusid=co-vims-v1488642557_ir'
        expected = {'count': 17, 'err': False, 'reqno': None}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/status.json'
        expected = {'count': 17, 'reqno': None}
        self._run_json_equal(url, expected)

    def test__api_collections_addrange_missing_reqno(self):
        "/collections/addrange: Missing range with reqno no download"
        url = '/opus/__collections/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__collections/addrange.json?reqno=124'
        expected = {'count': 0, 'err': 'no range given', 'reqno': 124}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/status.json?reqno=456'
        expected = {'count': 0, 'reqno': 456}
        self._run_json_equal(url, expected)

    def test__api_collections_addrange_one_reqno(self):
        "/collections/addrange: One good OPUSID with reqno no download"
        url = '/opus/__collections/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__collections/addrange.json?volumeid=COVIMS_0006&range=co-vims-v1484504505_ir,co-vims-v1484504505_ir&reqno=567'
        expected = {'count': 1, 'err': False, 'reqno': 567}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/status.json'
        expected = {'count': 1, 'reqno': None}
        self._run_json_equal(url, expected)

    def test__api_collections_addrange_missing_download(self):
        "/collections/addrange: Missing range no reqno with download"
        url = '/opus/__collections/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__collections/addrange.json?download=1'
        expected = {"err": "no range given", "count": 0, "reqno": None, "total_download_count": 0, "total_download_size": 0, "total_download_size_pretty": "0B", "product_cat_list": []}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/status.json'
        expected = {'count': 0, 'reqno': None}
        self._run_json_equal(url, expected)

    def test__api_collections_addrange_multi_reqno_download(self):
        "/collections/addrange: Multiple with reqno with download"
        url = '/opus/__collections/reset.json'
        self._run_status_equal(url, 200)
        url = '/opus/__collections/addrange.json?volumeid=COVIMS_0006&range=co-vims-v1488642557_ir,co-vims-v1488646261_ir&reqno=1234567&download=1'
        expected = {"err": False, "count": 17, "reqno": 1234567, "total_download_count": 92, "total_download_size": 9224834, "total_download_size_pretty": "8M", "product_cat_list": [["Metadata Products", [{"slug_name": "inventory", "product_type": "Target Body Inventory", "product_count": 17, "download_count": 2, "download_size": 415545, "download_size_pretty": "405K"}, {"slug_name": "planet-geometry", "product_type": "Planet Geometry Index", "product_count": 17, "download_count": 2, "download_size": 1527684, "download_size_pretty": "1M"}, {"slug_name": "moon-geometry", "product_type": "Moon Geometry Index", "product_count": 17, "download_count": 2, "download_size": 481067, "download_size_pretty": "469K"}, {"slug_name": "ring-geometry", "product_type": "Ring Geometry Index", "product_count": 17, "download_count": 2, "download_size": 2448696, "download_size_pretty": "2M"}]], ["Browse Products", [{"slug_name": "browse-thumb", "product_type": "Browse Image (thumbnail)", "product_count": 17, "download_count": 9, "download_size": 82840, "download_size_pretty": "80K"}, {"slug_name": "browse-small", "product_type": "Browse Image (small)", "product_count": 17, "download_count": 9, "download_size": 227327, "download_size_pretty": "221K"}, {"slug_name": "browse-medium", "product_type": "Browse Image (medium)", "product_count": 17, "download_count": 9, "download_size": 233338, "download_size_pretty": "227K"}, {"slug_name": "browse-full", "product_type": "Browse Image (full-size)", "product_count": 17, "download_count": 9, "download_size": 233338, "download_size_pretty": "227K"}]], ["Cassini VIMS-Specific Products", [{"slug_name": "covims-raw", "product_type": "Raw cube", "product_count": 17, "download_count": 21, "download_size": 2919003, "download_size_pretty": "2M"}, {"slug_name": "covims-thumb", "product_type": "Extra preview (thumbnail)", "product_count": 17, "download_count": 9, "download_size": 17411, "download_size_pretty": "17K"}, {"slug_name": "covims-medium", "product_type": "Extra preview (medium)", "product_count": 17, "download_count": 9, "download_size": 183437, "download_size_pretty": "179K"}, {"slug_name": "covims-full", "product_type": "Extra preview (full)", "product_count": 17, "download_count": 9, "download_size": 455148, "download_size_pretty": "444K"}]]]}
        self._run_json_equal(url, expected)
        url = '/opus/__collections/status.json'
        expected = {'count': 17, 'reqno': None}
        self._run_json_equal(url, expected)


    # ########################
    # ### Error Conditions ###
    # ########################
    #
    # def test__api_meta_range_endpoints_bad_slug(self):
    #     "/api/meta/range/endpoints: bad slug name"
    #     url = '/opus/__api/meta/range/endpoints/badslug.json?instrument=Cassini+ISS'
    #     self._run_status_equal(url, 404)
    #
    #
    #         ##############################################
    #         ######### /api/meta/mults UNIT TESTS #########
    #         ##############################################
    #
    # def test__api_meta_mults_COISS_2111(self):
    #     "/api/meta/meta/mults: for COISS_2111"
    #     url = '/opus/api/meta/mults/target.json?volumeid=COISS_2111&planet=Saturn'
    #     self._run_mults_equal(url, 2, 'Polydeuces')
    #
    # def test__api_meta_mults_bad_param(self):
    #     "/api/meta/mults: bad parameter"
    #     url = '/opus/api/meta/mults/target.json?volumeid=COISS_2111&planetx=Saturn'
    #     self._run_status_equal(url, 404)
