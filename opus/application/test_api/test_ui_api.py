# opus/application/test_api/test_ui_api.py

import json
import requests
from unittest import TestCase

from rest_framework.test import RequestsClient

from api_test_helper import ApiTestHelper

import settings

import logging
log = logging.getLogger(__name__)

settings.CACHE_BACKEND = 'dummy:///'

class ApiUITests(TestCase, ApiTestHelper):

    # disable error logging and trace output before test
    def setUp(self):
        settings.CACHE_KEY_PREFIX = 'opustest:' + settings.OPUS_SCHEMA_NAME
        # logging.disable(logging.ERROR)
        if settings.TEST_GO_LIVE:
            self.client = requests.Session()
        else:
            self.client = RequestsClient()
        self.default_url_slugs = {
            "cols": settings.DEFAULT_COLUMNS,
            "widgets": settings.DEFAULT_WIDGETS,
            "order": settings.DEFAULT_SORT_ORDER,
            "view": "gallery",
            "browse": "gallery",
            "startobs": 1,
            "cart_browse": "gallery",
            "detail": ""
        }

    # enable error logging and trace output after test
    def tearDown(self):
        logging.disable(logging.NOTSET)

    def _run_url_slugs_equal(self, url, expected):
        print(url)
        response = self._get_response(url)
        self.assertEqual(response.status_code, 200)
        jdata = json.loads(response.content)
        slug_data = {}
        for slug_dict in jdata['new_slugs']:
            slug_data.update(slug_dict)
        print('Got:')
        print(slug_data)
        print('Expected:')
        print(expected)
        print('Message:')
        print(jdata['msg'])
        self.assertEqual(expected, slug_data)


            #####################################
            ######### /__help API TESTS #########
            #####################################

    def test__api_help_about(self):
        "/__help: about"
        url = '/opus/__help/about.html'
        self._run_status_equal(url, 200)

    def test__api_help_datasets(self):
        "/__help: datasets"
        url = '/opus/__help/datasets.html'
        self._run_status_equal(url, 200)

    def test__api_help_tutorial(self):
        "/__help: tutorial"
        url = '/opus/__help/tutorial.html'
        self._run_status_equal(url, 200)

    def test__api_help_bad(self):
        "/__help: bad"
        url = '/opus/__help/bad.html'
        self._run_status_equal(url, 404)


            ###############################################
            ######### /__lastblogupdate API TESTS #########
            ###############################################

    def test__api_lastblogupdate(self):
        "/__lastblogupdate: normal"
        url = '/opus/__lastblogupdate.json'
        self._run_status_equal(url, 200)


            #############################################
            ######### /__normalizeurl API TESTS #########
            #############################################

    def test__api_normalizeurl_empty(self):
        "/__normalizeurl: empty"
        url = '/opus/__normalizeurl.json'
        self._run_url_slugs_equal(url, self.default_url_slugs)

    ### view=

    def test__api_normalizeurl_view_search(self):
        "/__normalizeurl: view search"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?view=search'
        new_slugs['view'] = 'search'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_view_browse(self):
        "/__normalizeurl: view browse"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?view=browse'
        new_slugs['view'] = 'browse'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_view_collection(self):
        "/__normalizeurl: view collection"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?view=collection'
        new_slugs['view'] = 'cart'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_view_cart(self):
        "/__normalizeurl: view cart"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?view=cart'
        new_slugs['view'] = 'cart'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_view_detail(self):
        "/__normalizeurl: view detail"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?view=detail'
        new_slugs['view'] = 'detail'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_view_badval(self):
        "/__normalizeurl: view badval"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?view=badval'
        new_slugs['view'] = 'gallery'
        self._run_url_slugs_equal(url, new_slugs)

    ### browse=

    def test__api_normalizeurl_browse_gallery(self):
        "/__normalizeurl: browse gallery"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?browse=gallery'
        new_slugs['browse'] = 'gallery'

    def test__api_normalizeurl_browse_data(self):
        "/__normalizeurl: browse data"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?browse=data'
        new_slugs['browse'] = 'data'

    def test__api_normalizeurl_browse_badval(self):
        "/__normalizeurl: browse badval"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?browse=badval'
        new_slugs['browse'] = 'gallery'

    ### colls_browse=

    def test__api_normalizeurl_colls_browse_gallery(self):
        "/__normalizeurl: colls_browse gallery"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?colls_browse=gallery'
        new_slugs['cart_browse'] = 'gallery'

    def test__api_normalizeurl_colls_browse_data(self):
        "/__normalizeurl: colls_browse data"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?colls_browse=data'
        new_slugs['cart_browse'] = 'gallery'
        # new_slugs['cart_browse'] = 'data'

    def test__api_normalizeurl_colls_browse_badval(self):
        "/__normalizeurl: colls_browse badval"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?colls_browse=badval'
        new_slugs['cart_browse'] = 'gallery'

    ### cart_browse=

    def test__api_normalizeurl_cart_browse_gallery(self):
        "/__normalizeurl: cart_browse gallery"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?cart_browse=gallery'
        new_slugs['cart_browse'] = 'gallery'

    def test__api_normalizeurl_cart_browse_data(self):
        "/__normalizeurl: cart_browse data"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?cart_browse=data'
        new_slugs['cart_browse'] = 'gallery'
        # new_slugs['cart_browse'] = 'data'

    def test__api_normalizeurl_cart_browse_badval(self):
        "/__normalizeurl: cart_browse badval"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?cart_browse=badval'
        new_slugs['cart_browse'] = 'gallery'

    ### page=

    def test__api_normalizeurl_page_0(self):
        "/__normalizeurl: page 0"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?page=0'
        new_slugs['startobs'] = 1
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_page_n100(self):
        "/__normalizeurl: page -100"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?page=-100'
        new_slugs['startobs'] = 1
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_page_1000000000000000000000000(self):
        "/__normalizeurl: page 1000000000000000000000000"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?page=1000000000000000000000000'
        new_slugs['startobs'] = 1
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_page_1(self):
        "/__normalizeurl: page 1"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?page=1'
        new_slugs['startobs'] = 1
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_page_2(self):
        "/__normalizeurl: page 2"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?page=2'
        new_slugs['startobs'] = 101
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_page_100(self):
        "/__normalizeurl: page 100"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?page=100'
        new_slugs['startobs'] = 9901
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_page_105(self):
        "/__normalizeurl: page 10.5"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?page=10.5'
        new_slugs['startobs'] = 1
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_page_1e2(self):
        "/__normalizeurl: page 1e2"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?page=1e2'
        new_slugs['startobs'] = 1
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_page_XXX(self):
        "/__normalizeurl: page XXX"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?page=XXX'
        new_slugs['startobs'] = 1
        self._run_url_slugs_equal(url, new_slugs)

    ### startobs=

    def test__api_normalizeurl_startobs_0(self):
        "/__normalizeurl: startobs 0"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?startobs=0'
        new_slugs['startobs'] = 1
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_startobs_n100(self):
        "/__normalizeurl: startobs -100"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?startobs=-100'
        new_slugs['startobs'] = 1
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_startobs_1000000000000000000000000(self):
        "/__normalizeurl: startobs 1000000000000000000000000"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?startobs=1000000000000000000000000'
        new_slugs['startobs'] = 1
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_startobs_1(self):
        "/__normalizeurl: startobs 1"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?startobs=1'
        new_slugs['startobs'] = 1
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_startobs_2(self):
        "/__normalizeurl: startobs 2"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?startobs=2'
        new_slugs['startobs'] = 2
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_startobs_100(self):
        "/__normalizeurl: startobs 100"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?startobs=100'
        new_slugs['startobs'] = 100
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_startobs_105(self):
        "/__normalizeurl: startobs 10.5"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?startobs=10.5'
        new_slugs['startobs'] = 1
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_startobs_1e2(self):
        "/__normalizeurl: startobs 1e2"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?startobs=1e2'
        new_slugs['startobs'] = 1
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_startobs_XXX(self):
        "/__normalizeurl: startobs XXX"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?startobs=XXX'
        new_slugs['startobs'] = 1
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_page_startobs(self):
        "/__normalizeurl: page and startobs"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?page=10&startobs=5'
        new_slugs['startobs'] = 5
        self._run_url_slugs_equal(url, new_slugs)

    # detail=

    def test__api_normalizeurl_detail_opusid(self):
        "/__normalizeurl: detail opusid"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?detail=co-iss-n1460961026'
        new_slugs['detail'] = 'co-iss-n1460961026'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_detail_ringobsid(self):
        "/__normalizeurl: detail ringobsid"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?detail=S_IMG_CO_ISS_1460961026_N'
        new_slugs['detail'] = 'co-iss-n1460961026'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_detail_badval(self):
        "/__normalizeurl: detail badval"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?detail=XXX'
        new_slugs['detail'] = ''
        self._run_url_slugs_equal(url, new_slugs)

    # reqno=

    def test__api_normalizeurl_reqno(self):
        "/__normalizeurl: reqno"
        # Should be ignored
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?reqno=5'
        self._run_url_slugs_equal(url, new_slugs)

    # lonely qtype

    def test__api_normalizeurl_lonely_qtype_bad_slug(self):
        "/__normalizeurl: lonely qtype bad slug"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?qtype-fredethel=any'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_lonely_qtype_not_used(self):
        "/__normalizeurl: lonely qtype not used"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?qtype-rightasc=any'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_lonely_qtype_used_any(self):
        "/__normalizeurl: lonely qtype not used"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=rightasc&qtype-rightasc=any'
        new_slugs['widgets'] = 'rightasc'
        new_slugs['qtype-rightasc'] = 'all'
        self._run_url_slugs_equal(url, new_slugs)
