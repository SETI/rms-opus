# opus/application/test_api/test_return_formats.py

import logging
import requests
import sys
from unittest import TestCase

from django.core.cache import cache
from rest_framework.test import RequestsClient

from api_test_helper import ApiTestHelper

import settings

class ApiReturnFormatTests(TestCase, ApiTestHelper):

    def setUp(self):
        self.maxDiff = None
        settings.CACHE_KEY_PREFIX = 'opustest:' + settings.DB_SCHEMA_NAME
        # logging.disable(logging.ERROR)
        if settings.TEST_GO_LIVE: # pragma: no cover
            self.client = requests.Session()
        else:
            self.client = RequestsClient()
        cache.clear()

    def tearDown(self):
        logging.disable(logging.NOTSET)

    def _test_return_formats(self, url, good_formats):
        formats = ('csv', 'json', 'html', 'zip')
        ret_status_list = []
        expected_status_list = []
        for format in formats:
            actual_url = url.replace('[fmt]', format)
            print(actual_url)
            response = self._get_response(actual_url)
            ret_status_list.append(response.status_code)
            if format in good_formats:
                expected_status_list.append(200)
            else:
                expected_status_list.append(404)
        print('Formats:', formats)
        print('Got:', ret_status_list)
        print('Expected:', expected_status_list)
        self.assertEqual(ret_status_list, expected_status_list)


            ###########################################
            ######### API Return Format Tests #########
            ###########################################

    # metadata/urls.py

    def test__api_retfmt_result_count(self):
        "[test_return_formats.py] return formats /api/meta/result_count.[fmt]"
        self._test_return_formats('/api/meta/result_count.[fmt]?planet=Saturn&target=Pan', ('json', 'html', 'csv'))

    def test__api_retfmt_result_count_pvt(self):
        "[test_return_formats.py] return formats /__api/meta/result_count.[fmt]"
        self._test_return_formats('/__api/meta/result_count.[fmt]?planet=Saturn&target=Pan&reqno=1', ('json'))

    def test__api_retfmt_mults(self):
        "[test_return_formats.py] return formats /api/meta/mults/slug.[fmt]"
        self._test_return_formats('/api/meta/mults/planet.[fmt]?target=Jupiter', ('json', 'html', 'csv'))

    def test__api_retfmt_mults_pvt(self):
        "[test_return_formats.py] return formats /__api/meta/mults/slug.[fmt]"
        self._test_return_formats('/__api/meta/mults/planet.[fmt]?target=Jupiter&reqno=1', ('json'))

    def test__api_retfmt_endpoints(self):
        "[test_return_formats.py] return formats /api/meta/range/endpoints/slug.[fmt]"
        self._test_return_formats('/api/meta/range/endpoints/wavelength1.[fmt]?planet=Jupiter&target=Callisto', ('json', 'html', 'csv'))

    def test__api_retfmt_endpoints_pvt(self):
        "[test_return_formats.py] return formats /__api/meta/range/endpoints/slug.[fmt]"
        self._test_return_formats('/__api/meta/range/endpoints/wavelength1.[fmt]?planet=Jupiter&target=Callisto&reqno=1', ('json'))

    def test__api_retfmt_fields_slug(self):
        "[test_return_formats.py] return formats /api/fields/slug.[fmt]"
        self._test_return_formats('/api/fields/mission.[fmt]', ('json', 'csv'))

    def test__api_retfmt_fields(self):
        "[test_return_formats.py] return formats /api/fields.[fmt]"
        self._test_return_formats('/api/fields/mission.[fmt]', ('json', 'csv'))

    # results/urls.py

    def test__api_retfmt_dataimages_pvt(self):
        "[test_return_formats.py] return formats /__api/dataimages.[fmt]"
        self._test_return_formats('/__api/dataimages.[fmt]?target=Jupiter&limit=2&reqno=1', ('json',))

    def test__api_retfmt_data(self):
        "[test_return_formats.py] return formats /api/data.[fmt]"
        self._test_return_formats('/api/data.[fmt]', ('json', 'html', 'csv'))

    def test__api_retfmt_data_pvt(self):
        "[test_return_formats.py] return formats /__api/data.[fmt]"
        self._test_return_formats('/__api/data.[fmt]', ('csv',))

    def test__api_retfmt_metadata(self):
        "[test_return_formats.py] return formats /api/metadata/opusid.[fmt]"
        self._test_return_formats('/api/metadata/vg-iss-2-s-c4362550.[fmt]', ('csv', 'json', 'html'))

    def test__api_retfmt_metadata_v2(self):
        "[test_return_formats.py] return formats /api/metadata_v2/opusid.[fmt]"
        self._test_return_formats('/api/metadata_v2/vg-iss-2-s-c4362550.[fmt]', ('csv', 'json', 'html'))

    def test__api_retfmt_metadata_v2_pvt(self):
        "[test_return_formats.py] return formats /__api/metadata_v2/opusid.[fmt]"
        self._test_return_formats('/__api/metadata_v2/vg-iss-2-s-c4362550.[fmt]', ('csv', 'json', 'html'))

    def test__api_retfmt_images(self):
        "[test_return_formats.py] return formats /api/images.[fmt]"
        self._test_return_formats('/api/images.[fmt]?target=Jupiter&limit=2', ('csv', 'json', 'html', 'zip'))

    def test__api_retfmt_image(self):
        "[test_return_formats.py] return formats /api/image/small/opusid.[fmt]"
        self._test_return_formats('/api/image/small/vg-iss-2-s-c4362550.[fmt]', ('csv', 'json', 'html', 'zip'))

    def test__api_retfmt_files_opusid(self):
        "[test_return_formats.py] return formats /api/files/opusid.[fmt]"
        self._test_return_formats('/api/files/vg-iss-2-s-c4362550.[fmt]', ('json',))

    def test__api_retfmt_files(self):
        "[test_return_formats.py] return formats /api/files.[fmt]"
        self._test_return_formats('/api/files.[fmt]?target=Jupiter&limit=2', ('json',))

    def test__api_retfmt_categories_opusid(self):
        "[test_return_formats.py] return formats /api/categories/opusid.[fmt]"
        self._test_return_formats('/api/categories/vg-iss-2-s-c4362550.[fmt]', ('json',))

    def test__api_retfmt_categories_opusid_pvt(self):
        "[test_return_formats.py] return formats /__api/categories/opusid.[fmt]"
        self._test_return_formats('/__api/categories/vg-iss-2-s-c4362550.[fmt]', ('json',))

    def test__api_retfmt_categories(self):
        "[test_return_formats.py] return formats /api/categories.[fmt]"
        self._test_return_formats('/api/categories.[fmt]?target=Jupiter', ('json',))

class ApiFormats:
    # slugs for testing
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
