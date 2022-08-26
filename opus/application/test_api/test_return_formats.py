# opus/application/test_api/test_return_formats.py

import logging
import requests
from unittest import TestCase

from django.core.cache import cache
from rest_framework.test import RequestsClient

from .api_test_helper import ApiTestHelper

import settings

class ApiReturnFormatTests(TestCase, ApiTestHelper):

    def setUp(self):
        self.maxDiff = None
        settings.OPUS_FAKE_API_DELAYS = 0
        settings.OPUS_FAKE_SERVER_ERROR404_PROBABILITY = 0
        settings.OPUS_FAKE_SERVER_ERROR500_PROBABILITY = 0
        settings.CACHE_KEY_PREFIX = 'opustest:' + settings.DB_SCHEMA_NAME
        logging.disable(logging.ERROR)
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

    # cart/urls.py

    def test__api_retfmt_cart_view(self):
        "[test_return_formats.py] return formats /__cart/view.[fmt]"
        self._run_status_equal('/opus/__cart/reset.json?reqno=1', 200)
        self._test_return_formats('/__cart/view.[fmt]?reqno=1', ('json',))

    def test__api_retfmt_cart_status(self):
        "[test_return_formats.py] return formats /__cart/status.[fmt]"
        self._run_status_equal('/__cart/reset.json?reqno=1', 200)
        self._test_return_formats('/__cart/status.[fmt]?reqno=1', ('json',))

    def test__api_retfmt_cart_data(self):
        "[test_return_formats.py] return formats /__cart/data.[fmt]"
        self._run_status_equal('/__cart/reset.json?reqno=1', 200)
        self._test_return_formats('/__cart/data.[fmt]', ('csv',))

    def test__api_retfmt_cart_add(self):
        "[test_return_formats.py] return formats /__cart/add.[fmt]"
        self._run_status_equal('/__cart/reset.json?reqno=1', 200)
        self._test_return_formats('/__cart/add.[fmt]?opusid=vg-iss-2-s-c4362550&reqno=1', ('json',))

    def test__api_retfmt_cart_remove(self):
        "[test_return_formats.py] return formats /__cart/remove.[fmt]"
        self._run_status_equal('/__cart/reset.json?reqno=1', 200)
        self._test_return_formats('/__cart/remove.[fmt]?opusid=vg-iss-2-s-c4362550&reqno=1', ('json',))

    def test__api_retfmt_cart_addrange(self):
        "[test_return_formats.py] return formats /__cart/addrange.[fmt]"
        self._run_status_equal('/__cart/reset.json?reqno=1', 200)
        self._test_return_formats('/__cart/addrange.[fmt]?volumeid=COVIMS_0006&range=co-vims-v1488549680_ir,co-vims-v1488550102_ir&reqno=1', ('json',))

    def test__api_retfmt_cart_removerange(self):
        "[test_return_formats.py] return formats /__cart/removerange.[fmt]"
        self._run_status_equal('/__cart/reset.json?reqno=1', 200)
        self._test_return_formats('/__cart/removerange.[fmt]?volumeid=COVIMS_0006&range=co-vims-v1488549680_ir,co-vims-v1488550102_ir&reqno=1', ('json',))

    def test__api_retfmt_cart_addall(self):
        "[test_return_formats.py] return formats /__cart/addall.[fmt]"
        self._run_status_equal('/__cart/reset.json?reqno=1', 200)
        self._test_return_formats('/__cart/addall.[fmt]?volumeid=COVIMS_0006&reqno=1', ('json',))

    def test__api_retfmt_cart_reset(self):
        "[test_return_formats.py] return formats /__cart/reset.[fmt]"
        self._test_return_formats('/__cart/reset.[fmt]?reqno=1', ('json',))

    def test__api_retfmt_cart_download(self):
        "[test_return_formats.py] return formats /__cart/download.[fmt]"
        self._run_status_equal('/__cart/reset.json?reqno=1', 200)
        self._test_return_formats('/__cart/download.[fmt]', ('json',))

    def test__api_retfmt_cart_download_opusid(self):
        "[test_return_formats.py] return formats /api/download/opusid.[fmt]"
        self._test_return_formats('/api/download/co-vims-v1488549680_ir.[fmt]', ('zip',))

    def test__api_retfmt_cart_download_opusid_pvt(self):
        "[test_return_formats.py] return formats /__api/download/opusid.[fmt]"
        self._test_return_formats('/__api/download/co-vims-v1488549680_ir.[fmt]', ('zip',))

    # help/urls.py

    def test__api_retfmt_help_about(self):
        "[test_return_formats.py] return formats /__help/about.[fmt]"
        self._test_return_formats('/__help/about.[fmt]', ('html',))

    def test__api_retfmt_help_volumes(self):
        "[test_return_formats.py] return formats /__help/volumes.[fmt]"
        self._test_return_formats('/__help/volumes.[fmt]', ('html',))

    def test__api_retfmt_help_faq(self):
        "[test_return_formats.py] return formats /__help/faq.[fmt]"
        self._test_return_formats('/__help/faq.[fmt]', ('html',))

    def test__api_retfmt_help_gettingstarted(self):
        "[test_return_formats.py] return formats /__help/gettingstarted.[fmt]"
        self._test_return_formats('/__help/gettingstarted.[fmt]', ('html',))

    def test__api_retfmt_help_splash(self):
        "[test_return_formats.py] return formats /__help/splash.[fmt]"
        self._test_return_formats('/__help/splash.[fmt]', ('html',))

    def test__api_retfmt_help_apiguide(self):
        "[test_return_formats.py] return formats /__help/apiguide.[fmt]"
        self._test_return_formats('/__help/apiguide.[fmt]', ('html',))

    def test__api_retfmt_help_citing(self):
        "[test_return_formats.py] return formats /__help/citing.[fmt]"
        self._test_return_formats('/__help/citing.[fmt]', ('html',))

    # metadata/urls.py

    def test__api_retfmt_metadata_result_count(self):
        "[test_return_formats.py] return formats /api/meta/result_count.[fmt]"
        self._test_return_formats('/api/meta/result_count.[fmt]?planet=Saturn&target=Pan', ('json', 'html', 'csv'))

    def test__api_retfmt_metadata_result_count_pvt(self):
        "[test_return_formats.py] return formats /__api/meta/result_count.[fmt]"
        self._test_return_formats('/__api/meta/result_count.[fmt]?planet=Saturn&target=Pan&reqno=1', ('json'))

    def test__api_retfmt_metadata_mults(self):
        "[test_return_formats.py] return formats /api/meta/mults/slug.[fmt]"
        self._test_return_formats('/api/meta/mults/planet.[fmt]?target=Jupiter', ('json', 'html', 'csv'))

    def test__api_retfmt_metadata_mults_pvt(self):
        "[test_return_formats.py] return formats /__api/meta/mults/slug.[fmt]"
        self._test_return_formats('/__api/meta/mults/planet.[fmt]?target=Jupiter&reqno=1', ('json'))

    def test__api_retfmt_metadata_endpoints(self):
        "[test_return_formats.py] return formats /api/meta/range/endpoints/slug.[fmt]"
        self._test_return_formats('/api/meta/range/endpoints/wavelength1.[fmt]?planet=Jupiter&target=Callisto', ('json', 'html', 'csv'))

    def test__api_retfmt_metadata_endpoints_pvt(self):
        "[test_return_formats.py] return formats /__api/meta/range/endpoints/slug.[fmt]"
        self._test_return_formats('/__api/meta/range/endpoints/wavelength1.[fmt]?planet=Jupiter&target=Callisto&reqno=1', ('json'))

    def test__api_retfmt_metadata_fields_slug(self):
        "[test_return_formats.py] return formats /api/fields/slug.[fmt]"
        self._test_return_formats('/api/fields/mission.[fmt]', ('json', 'csv'))

    def test__api_retfmt_metadata_fields(self):
        "[test_return_formats.py] return formats /api/fields.[fmt]"
        self._test_return_formats('/api/fields/mission.[fmt]', ('json', 'csv'))

    # results/urls.py

    def test__api_retfmt_results_dataimages_pvt(self):
        "[test_return_formats.py] return formats /__api/dataimages.[fmt]"
        self._test_return_formats('/__api/dataimages.[fmt]?target=Jupiter&limit=2&reqno=1', ('json',))

    def test__api_retfmt_results_dataimages_fake_pvt(self):
        "[test_return_formats.py] return formats /__fake/__api/dataimages.[fmt]"
        self._test_return_formats('/__fake/__api/dataimages.[fmt]?target=Jupiter&limit=2&reqno=1', ('json',))

    def test__api_retfmt_results_data(self):
        "[test_return_formats.py] return formats /api/data.[fmt]"
        self._test_return_formats('/api/data.[fmt]', ('json', 'html', 'csv'))

    def test__api_retfmt_results_data_pvt(self):
        "[test_return_formats.py] return formats /__api/data.[fmt]"
        self._test_return_formats('/__api/data.[fmt]', ('csv',))

    def test__api_retfmt_results_metadata(self):
        "[test_return_formats.py] return formats /api/metadata/opusid.[fmt]"
        self._test_return_formats('/api/metadata/vg-iss-2-s-c4362550.[fmt]', ('csv', 'json', 'html'))

    def test__api_retfmt_results_metadata_v2(self):
        "[test_return_formats.py] return formats /api/metadata_v2/opusid.[fmt]"
        self._test_return_formats('/api/metadata_v2/vg-iss-2-s-c4362550.[fmt]', ('csv', 'json', 'html'))

    def test__api_retfmt_results_metadata_pvt(self):
        "[test_return_formats.py] return formats /__api/metadata/opusid.[fmt]"
        self._test_return_formats('/__api/metadata/vg-iss-2-s-c4362550.[fmt]', ('csv', 'json', 'html'))

    def test__api_retfmt_results_images(self):
        "[test_return_formats.py] return formats /api/images.[fmt]"
        self._test_return_formats('/api/images.[fmt]?target=Jupiter&limit=2', ('csv', 'json'))

    def test__api_retfmt_results_image(self):
        "[test_return_formats.py] return formats /api/image/small/opusid.[fmt]"
        self._test_return_formats('/api/image/small/vg-iss-2-s-c4362550.[fmt]', ('csv', 'json', 'html'))

    def test__api_retfmt_results_files_opusid(self):
        "[test_return_formats.py] return formats /api/files/opusid.[fmt]"
        self._test_return_formats('/api/files/vg-iss-2-s-c4362550.[fmt]', ('json',))

    def test__api_retfmt_results_files(self):
        "[test_return_formats.py] return formats /api/files.[fmt]"
        self._test_return_formats('/api/files.[fmt]?target=Jupiter&limit=2', ('json',))

    def test__api_retfmt_results_categories_opusid(self):
        "[test_return_formats.py] return formats /api/categories/opusid.[fmt]"
        self._test_return_formats('/api/categories/vg-iss-2-s-c4362550.[fmt]', ('json',))

    def test__api_retfmt_results_categories_opusid_pvt(self):
        "[test_return_formats.py] return formats /__api/categories/opusid.[fmt]"
        self._test_return_formats('/__api/categories/vg-iss-2-s-c4362550.[fmt]', ('json',))

    def test__api_retfmt_results_categories(self):
        "[test_return_formats.py] return formats /api/categories.[fmt]"
        self._test_return_formats('/api/categories.[fmt]?target=Jupiter', ('json',))

    def test__api_retfmt_results_product_types_opusid(self):
        "[test_return_formats.py] return formats /api/product_types/opusid.[fmt]"
        self._test_return_formats('/api/product_types/vg-iss-2-s-c4362550.[fmt]', ('json',))

    def test__api_retfmt_results_product_types(self):
        "[test_return_formats.py] return formats /api/product_types.[fmt]"
        self._test_return_formats('/api/product_types.[fmt]?target=Jupiter', ('json',))

    # search/urls.py

    def test__api_retfmt_search_normalizeinput_pvt(self):
        "[test_return_formats.py] return formats /__api/normalizeinput.[fmt]"
        self._test_return_formats('/__api/normalizeinput.[fmt]?target=Jupiter&reqno=1', ('json',))

    def test__api_retfmt_search_stringsearchchoices_pvt(self):
        "[test_return_formats.py] return formats /__api/stringsearchchoices.[fmt]"
        self._test_return_formats('/__api/stringsearchchoices/volumeid.[fmt]?volumeid=COISS_2002&reqno=1&target=Jupiter', ('json',))

    # ui/urls.py

    def test__api_retfmt_ui_lastblogupdate_pvt(self):
        "[test_return_formats.py] return formats /__notifications.[fmt]"
        self._test_return_formats('/__notifications.[fmt]', ('json',))

    def test__api_retfmt_ui_menu_pvt(self):
        "[test_return_formats.py] return formats /__menu.[fmt]"
        self._test_return_formats('/__menu.[fmt]?reqno=1', ('json',))

    def test__api_retfmt_ui_metadataselector_pvt(self):
        "[test_return_formats.py] return formats /__metadata_selector.[fmt]"
        self._test_return_formats('/__metadata_selector.[fmt]?reqno=1', ('json',))

    def test__api_retfmt_ui_widget_pvt(self):
        "[test_return_formats.py] return formats /__widget/slug.[fmt]"
        self._test_return_formats('/__widget/planet.[fmt]', ('html',))

    def test__api_retfmt_ui_initdetail_pvt(self):
        "[test_return_formats.py] return formats /__initdetail/opusid.[fmt]"
        self._test_return_formats('/__initdetail/vg-iss-2-s-c4362550.[fmt]', ('html',))

    def test__api_retfmt_ui_normalizeurl_pvt(self):
        "[test_return_formats.py] return formats /__normalizeurl.[fmt]"
        self._test_return_formats('/__normalizeurl.[fmt]', ('json',))

    def test__api_retfmt_ui_fake_viewmetadatamodal_pvt(self):
        "[test_return_formats.py] return formats /__fake/__viewmetadatamodal/opusid.[fmt]"
        self._test_return_formats('/__fake/__viewmetadatamodal/vg-iss-2-s-c4362550.[fmt]', ('json',))

    def test__api_retfmt_ui_fake_selectmetadatamodal_pvt(self):
        "[test_return_formats.py] return formats /__fake/__selectmetadatamodal.[fmt]"
        self._test_return_formats('/__fake/__selectmetadatamodal.[fmt]', ('json',))
