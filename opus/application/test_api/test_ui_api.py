# opus/application/test_api/test_ui_api.py

import json
import logging
import requests
import sys
from unittest import TestCase

from django.core.cache import cache
from rest_framework.test import RequestsClient

from api_test_helper import ApiTestHelper

import settings

class ApiUITests(TestCase, ApiTestHelper):

    def setUp(self):
        self.maxDiff = None
        settings.CACHE_KEY_PREFIX = 'opustest:' + settings.DB_SCHEMA_NAME
        logging.disable(logging.ERROR)
        if settings.TEST_GO_LIVE: # pragma: no cover
            self.client = requests.Session()
        else:
            self.client = RequestsClient()
        cache.clear()
        self.default_url_slugs = {
            "cols": settings.DEFAULT_COLUMNS,
            "widgets": settings.DEFAULT_WIDGETS,
            "order": settings.DEFAULT_SORT_ORDER,
            "view": "search",
            "browse": "gallery",
            "startobs": 1,
            "cart_browse": "gallery",
            "cart_startobs": 1,
            "detail": ""
        }

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


            ###############################################
            ######### /__lastblogupdate API TESTS #########
            ###############################################

    def test__api_lastblogupdate(self):
        "[test_ui_api.py] /__lastblogupdate: normal"
        url = '/opus/__lastblogupdate.json'
        self._run_status_equal(url, 200)


            ######################################
            ######### /__dummy API TESTS #########
            ######################################

    def test__api_dummy(self):
        "[test_ui_api.py] /__dummy: normal"
        url = '/opus/__dummy.json'
        self._run_status_equal(url, 200)


            #############################################
            ######### /__normalizeurl API TESTS #########
            #############################################

    ### Empty

    def test__api_normalizeurl_empty(self):
        "[test_ui_api.py] /__normalizeurl: empty"
        url = '/opus/__normalizeurl.json'
        self._run_url_slugs_equal(url, self.default_url_slugs)

    ### view=

    def test__api_normalizeurl_view_search(self):
        "[test_ui_api.py] /__normalizeurl: view search"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?view=search'
        new_slugs['view'] = 'search'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_view_browse(self):
        "[test_ui_api.py] /__normalizeurl: view browse"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?view=browse'
        new_slugs['view'] = 'browse'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_view_collection(self):
        "[test_ui_api.py] /__normalizeurl: view collection"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?view=collection'
        new_slugs['view'] = 'cart'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_view_cart(self):
        "[test_ui_api.py] /__normalizeurl: view cart"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?view=cart'
        new_slugs['view'] = 'cart'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_view_detail(self):
        "[test_ui_api.py] /__normalizeurl: view detail"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?view=detail'
        new_slugs['view'] = 'detail'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_view_badval(self):
        "[test_ui_api.py] /__normalizeurl: view badval"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?view=badval'
        new_slugs['view'] = 'search'
        self._run_url_slugs_equal(url, new_slugs)

    ### browse=

    def test__api_normalizeurl_browse_gallery(self):
        "[test_ui_api.py] /__normalizeurl: browse gallery"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?browse=gallery'
        new_slugs['browse'] = 'gallery'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_browse_data(self):
        "[test_ui_api.py] /__normalizeurl: browse data"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?browse=data'
        new_slugs['browse'] = 'data'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_browse_badval(self):
        "[test_ui_api.py] /__normalizeurl: browse badval"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?browse=badval'
        new_slugs['browse'] = 'gallery'
        self._run_url_slugs_equal(url, new_slugs)

    ### colls_browse=

    def test__api_normalizeurl_colls_browse_gallery(self):
        "[test_ui_api.py] /__normalizeurl: colls_browse gallery"
        # This is really just testing the default, because we don't pay
        # attention to colls_browse in normalizeurl
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?colls_browse=gallery'
        new_slugs['cart_browse'] = 'gallery'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_colls_browse_data(self):
        "[test_ui_api.py] /__normalizeurl: colls_browse data"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?colls_browse=data'
        new_slugs['cart_browse'] = 'gallery'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_colls_browse_badval(self):
        "[test_ui_api.py] /__normalizeurl: colls_browse badval"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?colls_browse=badval'
        new_slugs['cart_browse'] = 'gallery'
        self._run_url_slugs_equal(url, new_slugs)

    ### cart_browse=

    def test__api_normalizeurl_cart_browse_gallery(self):
        "[test_ui_api.py] /__normalizeurl: cart_browse gallery"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?cart_browse=gallery'
        new_slugs['cart_browse'] = 'gallery'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_cart_browse_data(self):
        "[test_ui_api.py] /__normalizeurl: cart_browse data"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?cart_browse=data'
        new_slugs['cart_browse'] = 'data'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_cart_browse_badval(self):
        "[test_ui_api.py] /__normalizeurl: cart_browse badval"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?cart_browse=badval'
        new_slugs['cart_browse'] = 'gallery'
        self._run_url_slugs_equal(url, new_slugs)

    ### page=

    def test__api_normalizeurl_page_0(self):
        "[test_ui_api.py] /__normalizeurl: page 0"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?page=0'
        new_slugs['startobs'] = 1
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_page_n100(self):
        "[test_ui_api.py] /__normalizeurl: page -100"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?page=-100'
        new_slugs['startobs'] = 1
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_page_1000000000000000000000000(self):
        "[test_ui_api.py] /__normalizeurl: page 1000000000000000000000000"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?page=1000000000000000000000000'
        new_slugs['startobs'] = 1
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_page_1(self):
        "[test_ui_api.py] /__normalizeurl: page 1"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?page=1'
        new_slugs['startobs'] = 1
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_page_2(self):
        "[test_ui_api.py] /__normalizeurl: page 2"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?page=2'
        new_slugs['startobs'] = 101
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_page_100(self):
        "[test_ui_api.py] /__normalizeurl: page 100"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?page=100'
        new_slugs['startobs'] = 9901
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_page_105(self):
        "[test_ui_api.py] /__normalizeurl: page 10.5"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?page=10.5'
        new_slugs['startobs'] = 1
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_page_1e2(self):
        "[test_ui_api.py] /__normalizeurl: page 1e2"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?page=1e2'
        new_slugs['startobs'] = 1
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_page_XXX(self):
        "[test_ui_api.py] /__normalizeurl: page XXX"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?page=XXX'
        new_slugs['startobs'] = 1
        self._run_url_slugs_equal(url, new_slugs)

    ### startobs=

    def test__api_normalizeurl_startobs_0(self):
        "[test_ui_api.py] /__normalizeurl: startobs 0"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?startobs=0'
        new_slugs['startobs'] = 1
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_startobs_n100(self):
        "[test_ui_api.py] /__normalizeurl: startobs -100"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?startobs=-100'
        new_slugs['startobs'] = 1
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_startobs_1000000000000000000000000(self):
        "[test_ui_api.py] /__normalizeurl: startobs 1000000000000000000000000"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?startobs=1000000000000000000000000'
        new_slugs['startobs'] = 1
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_startobs_1(self):
        "[test_ui_api.py] /__normalizeurl: startobs 1"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?startobs=1'
        new_slugs['startobs'] = 1
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_startobs_2(self):
        "[test_ui_api.py] /__normalizeurl: startobs 2"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?startobs=2'
        new_slugs['startobs'] = 2
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_startobs_100(self):
        "[test_ui_api.py] /__normalizeurl: startobs 100"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?startobs=100'
        new_slugs['startobs'] = 100
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_startobs_105(self):
        "[test_ui_api.py] /__normalizeurl: startobs 10.5"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?startobs=10.5'
        new_slugs['startobs'] = 1
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_startobs_1e2(self):
        "[test_ui_api.py] /__normalizeurl: startobs 1e2"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?startobs=1e2'
        new_slugs['startobs'] = 1
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_startobs_XXX(self):
        "[test_ui_api.py] /__normalizeurl: startobs XXX"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?startobs=XXX'
        new_slugs['startobs'] = 1
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_page_startobs(self):
        "[test_ui_api.py] /__normalizeurl: page and startobs"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?page=10&startobs=5'
        new_slugs['startobs'] = 5
        self._run_url_slugs_equal(url, new_slugs)

    # detail=

    def test__api_normalizeurl_detail_opusid(self):
        "[test_ui_api.py] /__normalizeurl: detail opusid"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?detail=co-iss-n1460961026'
        new_slugs['detail'] = 'co-iss-n1460961026'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_detail_opusid_bad(self):
        "[test_ui_api.py] /__normalizeurl: detail opusid bad"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?detail=co-iss-n1460961027'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_detail_ringobsid(self):
        "[test_ui_api.py] /__normalizeurl: detail ringobsid"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?detail=S_IMG_CO_ISS_1460961026_N'
        new_slugs['detail'] = 'co-iss-n1460961026'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_detail_ringobsid_bad(self):
        "[test_ui_api.py] /__normalizeurl: detail ringobsid bad"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?detail=S_IMG_CO_ISS_14609610267_N'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_detail_badval(self):
        "[test_ui_api.py] /__normalizeurl: detail badval"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?detail=XXX'
        new_slugs['detail'] = ''
        self._run_url_slugs_equal(url, new_slugs)

    # reqno= (an ignored slug)

    def test__api_normalizeurl_reqno_5(self):
        "[test_ui_api.py] /__normalizeurl: reqno 5"
        # Should be ignored
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?reqno=5'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_reqno_XXX(self):
        "[test_ui_api.py] /__normalizeurl: reqno XXX"
        # Should be ignored
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?reqno=XXX'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_reqno(self):
        "[test_ui_api.py] /__normalizeurl: reqno empty"
        # Should be ignored
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?reqno='
        self._run_url_slugs_equal(url, new_slugs)

    # lonely qtype - these are qtypes without matching searches or widgets

    def test__api_normalizeurl_lonely_qtype_bad_slug(self):
        "[test_ui_api.py] /__normalizeurl: lonely qtype bad slug"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?qtype-fredethel=any'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_lonely_qtype_not_used(self):
        "[test_ui_api.py] /__normalizeurl: lonely qtype not used"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?qtype-rightasc=any'
        self._run_url_slugs_equal(url, new_slugs)

    # Lonely qtype - these are qtypes wiithout matching searches but with
    # widgets
    def test__api_normalizeurl_lonely_qtype_used_any(self):
        "[test_ui_api.py] /__normalizeurl: lonely qtype used any"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=rightasc&qtype-rightasc=any'
        new_slugs['widgets'] = 'rightasc'
        new_slugs['qtype-rightasc'] = 'any'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_lonely_qtype_used_any_bad(self):
        "[test_ui_api.py] /__normalizeurl: lonely qtype used any bad"
        # Single column range doesn't take qtypes
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=observationduration&qtype-observationduration=any'
        new_slugs['widgets'] = 'observationduration'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_lonely_qtype_used_all(self):
        "[test_ui_api.py] /__normalizeurl: lonely qtype used all"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=rightasc&qtype-rightasc=all'
        new_slugs['widgets'] = 'rightasc'
        new_slugs['qtype-rightasc'] = 'all'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_lonely_qtype_used_only(self):
        "[test_ui_api.py] /__normalizeurl: lonely qtype used only"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=rightasc&qtype-rightasc=only'
        new_slugs['widgets'] = 'rightasc'
        new_slugs['qtype-rightasc'] = 'only'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_lonely_qtype_used_multi_badval_XXX(self):
        "[test_ui_api.py] /__normalizeurl: lonely qtype used multi badval XXX"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=rightasc&qtype-rightasc=XXX'
        new_slugs['widgets'] = 'rightasc'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_lonely_qtype_used_badval_contains(self):
        "[test_ui_api.py] /__normalizeurl: lonely qtype used badval contains"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=rightasc&qtype-rightasc=contains'
        new_slugs['widgets'] = 'rightasc'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_lonely_qtype_used_contains(self):
        "[test_ui_api.py] /__normalizeurl: lonely qtype used contains"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=volumeid&qtype-volumeid=contains'
        new_slugs['widgets'] = 'volumeid'
        new_slugs['qtype-volumeid'] = 'contains'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_lonely_qtype_used_matches(self):
        "[test_ui_api.py] /__normalizeurl: lonely qtype used matches"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=volumeid&qtype-volumeid=matches'
        new_slugs['widgets'] = 'volumeid'
        new_slugs['qtype-volumeid'] = 'matches'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_lonely_qtype_used_excludes(self):
        "[test_ui_api.py] /__normalizeurl: lonely qtype used excludes"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=volumeid&qtype-volumeid=excludes'
        new_slugs['widgets'] = 'volumeid'
        new_slugs['qtype-volumeid'] = 'excludes'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_lonely_qtype_used_begins(self):
        "[test_ui_api.py] /__normalizeurl: lonely qtype used begins"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=volumeid&qtype-volumeid=begins'
        new_slugs['widgets'] = 'volumeid'
        new_slugs['qtype-volumeid'] = 'begins'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_lonely_qtype_used_ends(self):
        "[test_ui_api.py] /__normalizeurl: lonely qtype used ends"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=volumeid&qtype-volumeid=ends'
        new_slugs['widgets'] = 'volumeid'
        new_slugs['qtype-volumeid'] = 'ends'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_lonely_qtype_used_string_badval_XXX(self):
        "[test_ui_api.py] /__normalizeurl: lonely qtype used string badval XXX"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=volumeid&qtype-volumeid=XXX'
        new_slugs['widgets'] = 'volumeid'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_lonely_qtype_used_badval_any(self):
        "[test_ui_api.py] /__normalizeurl: lonely qtype used badval any"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=volumeid&qtype-volumeid=any'
        new_slugs['widgets'] = 'volumeid'
        self._run_url_slugs_equal(url, new_slugs)

    ### widgets=

    def test__api_normalizeurl_widgets_empty(self):
        "[test_ui_api.py] /__normalizeurl: widgets empty"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets='
        new_slugs['widgets'] = ''
        self._run_url_slugs_equal(url, new_slugs)

    # Empty widgets

    # Also tests mult widget
    def test__api_normalizeurl_widgets_empty_1(self):
        "[test_ui_api.py] /__normalizeurl: widgets ,instrument"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=,instrument'
        new_slugs['widgets'] = 'instrument'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_widgets_empty_2(self):
        "[test_ui_api.py] /__normalizeurl: widgets instrument,"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=instrument,'
        new_slugs['widgets'] = 'instrument'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_widgets_empty_3(self):
        "[test_ui_api.py] /__normalizeurl: widgets ,,instrument,,"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=,,instrument,,'
        new_slugs['widgets'] = 'instrument'
        self._run_url_slugs_equal(url, new_slugs)

    # Old defaults

    def test__api_normalizeurl_widgets_default(self):
        "[test_ui_api.py] /__normalizeurl: widgets default"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=planet,target'
        new_slugs['widgets'] = settings.DEFAULT_WIDGETS
        self._run_url_slugs_equal(url, new_slugs)

    # Something that has an old_slug

    def test__api_normalizeurl_widgets_ringobsid(self):
        "[test_ui_api.py] /__normalizeurl: widgets ringobsid"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=ringobsid'
        new_slugs['widgets'] = 'opusid'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_widgets_instrument(self):
        "[test_ui_api.py] /__normalizeurl: widgets instrument"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=instrument'
        new_slugs['widgets'] = 'instrument'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_widgets_instrumentid(self):
        "[test_ui_api.py] /__normalizeurl: widgets instrumentid"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=instrumentid'
        new_slugs['widgets'] = 'instrument'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_widgets_instrument_instrument(self):
        "[test_ui_api.py] /__normalizeurl: widgets instrument,instrument"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=instrument,instrument'
        new_slugs['widgets'] = 'instrument'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_widgets_instrument_instrumentid(self):
        "[test_ui_api.py] /__normalizeurl: widgets instrument,instrumentid"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=instrument,instrumentid'
        new_slugs['widgets'] = 'instrument'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_widgets_instrumentid_instrument(self):
        "[test_ui_api.py] /__normalizeurl: widgets instrumentid,instrument"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=instrumentid,instrument'
        new_slugs['widgets'] = 'instrument'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_widgets_instrumentid_instrumentid(self):
        "[test_ui_api.py] /__normalizeurl: widgets instrumentid,instrumentid"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=instrumentid,instrumentid'
        new_slugs['widgets'] = 'instrument'
        self._run_url_slugs_equal(url, new_slugs)

    # Something that doesn't have an old slug

    # Also tests string widget
    def test__api_normalizeurl_widgets_productid(self):
        "[test_ui_api.py] /__normalizeurl: widgets productid"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=productid'
        new_slugs['widgets'] = 'productid'
        self._run_url_slugs_equal(url, new_slugs)

    # Bad widgets

    def test__api_normalizeurl_widgets_bad_1(self):
        "[test_ui_api.py] /__normalizeurl: widgets bad 1"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=XXX'
        new_slugs['widgets'] = ''
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_widgets_bad_2(self):
        "[test_ui_api.py] /__normalizeurl: widgets bad 2"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=XXX,productid'
        new_slugs['widgets'] = 'productid'
        self._run_url_slugs_equal(url, new_slugs)

    # Not searchable

    def test__api_normalizeurl_widgets_not_searchable(self):
        "[test_ui_api.py] /__normalizeurl: widgets not searchable"
        url = '/opus/__normalizeurl.json?widgets=**previewimages'
        new_slugs = dict(self.default_url_slugs)
        new_slugs['widgets'] = ''
        self._run_url_slugs_equal(url, new_slugs)

    # Searched but not in widget list

    def test__api_normalizeurl_widgets_searched_1(self):
        "[test_ui_api.py] /__normalizeurl: widgets searched not widget 1"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?instrument=COISS'
        new_slugs['instrument'] = 'COISS'
        new_slugs['widgets'] = 'instrument'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_widgets_searched_2(self):
        "[test_ui_api.py] /__normalizeurl: widgets searched not widget 2"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?rightasc1=10.'
        new_slugs['qtype-rightasc'] = 'any'
        new_slugs['rightasc1'] = '10.000000'
        new_slugs['widgets'] = 'rightasc'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_widgets_searched_3(self):
        "[test_ui_api.py] /__normalizeurl: widgets searched not widget 3"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?rightasc2=10.'
        new_slugs['qtype-rightasc'] = 'any'
        new_slugs['rightasc2'] = '10.000000'
        new_slugs['widgets'] = 'rightasc'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_widgets_searched_4(self):
        "[test_ui_api.py] /__normalizeurl: widgets searched not widget 4"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?rightasc2=10.&rightasc1=5.'
        new_slugs['qtype-rightasc'] = 'any'
        new_slugs['rightasc1'] = '5.000000'
        new_slugs['rightasc2'] = '10.000000'
        new_slugs['widgets'] = 'rightasc'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_widgets_searched_5(self):
        "[test_ui_api.py] /__normalizeurl: widgets searched not widget 5"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?rightasc2=10.&rightasc1=5.&widgets=instrument'
        new_slugs['qtype-rightasc'] = 'any'
        new_slugs['rightasc1'] = '5.000000'
        new_slugs['rightasc2'] = '10.000000'
        new_slugs['widgets'] = 'instrument,rightasc'
        self._run_url_slugs_equal(url, new_slugs)

    # Searched but in widget list

    def test__api_normalizeurl_widgets_searched_6(self):
        "[test_ui_api.py] /__normalizeurl: widgets searched not widget 6"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?instrument=COISS&widgets=instrument'
        new_slugs['instrument'] = 'COISS'
        new_slugs['widgets'] = 'instrument'
        self._run_url_slugs_equal(url, new_slugs)

    # Single-column range with '1' suffix

    def test__api_normalizeurl_widgets_observationduration(self):
        "[test_ui_api.py] /__normalizeurl: widgets observationduration"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=observationduration'
        new_slugs['widgets'] = 'observationduration'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_widgets_observationduration1(self):
        "[test_ui_api.py] /__normalizeurl: widgets observationduration1"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=observationduration1'
        new_slugs['widgets'] = 'observationduration'
        self._run_url_slugs_equal(url, new_slugs)

    # Multi-column range with '1' suffix

    def test__api_normalizeurl_widgets_rightasc(self):
        "[test_ui_api.py] /__normalizeurl: widgets rightasc"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=rightasc'
        new_slugs['widgets'] = 'rightasc'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_widgets_rightasc1(self):
        "[test_ui_api.py] /__normalizeurl: widgets rightasc1"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=rightasc1'
        new_slugs['widgets'] = 'rightasc'
        self._run_url_slugs_equal(url, new_slugs)

    ### cols=

    def test__api_normalizeurl_cols_empty(self):
        "[test_ui_api.py] /__normalizeurl: cols empty"
        # It's not OK to have empty columns
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?cols='
        new_slugs['cols'] = settings.DEFAULT_COLUMNS
        self._run_url_slugs_equal(url, new_slugs)

    # Empty cols

    # Also tests mult field
    def test__api_normalizeurl_cols_empty_1(self):
        "[test_ui_api.py] /__normalizeurl: cols ,instrument"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?cols=,instrument'
        new_slugs['cols'] = 'instrument'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_cols_empty_2(self):
        "[test_ui_api.py] /__normalizeurl: cols instrument,"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?cols=instrument,'
        new_slugs['cols'] = 'instrument'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_cols_empty_3(self):
        "[test_ui_api.py] /__normalizeurl: cols ,,instrument,,"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?cols=,,instrument,,'
        new_slugs['cols'] = 'instrument'
        self._run_url_slugs_equal(url, new_slugs)

    # Old defaults

    def test__api_normalizeurl_cols_default(self):
        "[test_ui_api.py] /__normalizeurl: cols default"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?cols=ringobsid,planet,target,phase1,phase2,time1,time2'
        new_slugs['cols'] = settings.DEFAULT_COLUMNS
        self._run_url_slugs_equal(url, new_slugs)

    # Something that has an old_slug

    def test__api_normalizeurl_cols_instrument(self):
        "[test_ui_api.py] /__normalizeurl: cols instrument"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?cols=instrument'
        new_slugs['cols'] = 'instrument'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_cols_instrumentid(self):
        "[test_ui_api.py] /__normalizeurl: cols instrumentid"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?cols=instrumentid'
        new_slugs['cols'] = 'instrument'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_cols_instrument_instrument(self):
        "[test_ui_api.py] /__normalizeurl: cols instrument,instrument"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?cols=instrument,instrument'
        new_slugs['cols'] = 'instrument'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_cols_instrument_instrumentid(self):
        "[test_ui_api.py] /__normalizeurl: cols instrument,instrumentid"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?cols=instrument,instrumentid'
        new_slugs['cols'] = 'instrument'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_cols_instrumentid_instrument(self):
        "[test_ui_api.py] /__normalizeurl: cols instrumentid,instrument"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?cols=instrumentid,instrument'
        new_slugs['cols'] = 'instrument'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_cols_instrumentid_instrumentid(self):
        "[test_ui_api.py] /__normalizeurl: cols instrumentid,instrumentid"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?cols=instrumentid,instrumentid'
        new_slugs['cols'] = 'instrument'
        self._run_url_slugs_equal(url, new_slugs)

    # Something that doesn't have an old slug

    # Also tests string field
    def test__api_normalizeurl_cols_productid(self):
        "[test_ui_api.py] /__normalizeurl: cols productid"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?cols=productid'
        new_slugs['cols'] = 'productid'
        self._run_url_slugs_equal(url, new_slugs)

    # Bad cols

    def test__api_normalizeurl_cols_bad_1(self):
        "[test_ui_api.py] /__normalizeurl: cols bad 1"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?cols=XXX'
        new_slugs['cols'] = settings.DEFAULT_COLUMNS
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_cols_bad_2(self):
        "[test_ui_api.py] /__normalizeurl: cols bad 2"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?cols=XXX,productid'
        new_slugs['cols'] = 'productid'
        self._run_url_slugs_equal(url, new_slugs)

    # Not viewable

    def test__api_normalizeurl_cols_ringobsid(self):
        "[test_ui_api.py] /__normalizeurl: cols ringobsid"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?cols=ringobsid'
        new_slugs['cols'] = 'opusid'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_cols_not_viewable(self):
        "[test_ui_api.py] /__normalizeurl: cols not viewable"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?cols=**filespec'
        new_slugs['cols'] = settings.DEFAULT_COLUMNS
        self._run_url_slugs_equal(url, new_slugs)

    # Single-column range with '1' suffix

    def test__api_normalizeurl_cols_observationduration(self):
        "[test_ui_api.py] /__normalizeurl: cols observationduration"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?cols=observationduration'
        new_slugs['cols'] = 'observationduration'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_cols_observationduration1(self):
        "[test_ui_api.py] /__normalizeurl: cols observationduration1"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?cols=observationduration1'
        new_slugs['cols'] = 'observationduration'
        self._run_url_slugs_equal(url, new_slugs)

    # Multi-column range with '1' suffix

    def test__api_normalizeurl_cols_rightasc(self):
        "[test_ui_api.py] /__normalizeurl: cols rightasc"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?cols=rightasc'
        new_slugs['cols'] = settings.DEFAULT_COLUMNS
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_cols_rightasc1(self):
        "[test_ui_api.py] /__normalizeurl: cols rightasc1"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?cols=rightasc1'
        new_slugs['cols'] = 'rightasc1'
        self._run_url_slugs_equal(url, new_slugs)

    ### order=

    def test__api_normalizeurl_order_empty(self):
        "[test_ui_api.py] /__normalizeurl: order empty"
        # It's not OK to have empty columns
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?order='
        new_slugs['order'] = settings.DEFAULT_SORT_ORDER
        self._run_url_slugs_equal(url, new_slugs)

    # Empty order

    def test__api_normalizeurl_order_empty_1(self):
        "[test_ui_api.py] /__normalizeurl: order ,instrument"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?order=,instrument'
        new_slugs['order'] = 'instrument'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_order_empty_2(self):
        "[test_ui_api.py] /__normalizeurl: order instrument,"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?order=instrument,'
        new_slugs['order'] = 'instrument'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_order_empty_3(self):
        "[test_ui_api.py] /__normalizeurl: order ,,instrument,,"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?order=,,instrument,,'
        new_slugs['order'] = 'instrument'
        self._run_url_slugs_equal(url, new_slugs)

    # Old defaults

    def test__api_normalizeurl_order_default(self):
        "[test_ui_api.py] /__normalizeurl: order default"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?order=time1'
        new_slugs['order'] = settings.DEFAULT_SORT_ORDER
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_order_default_2(self):
        "[test_ui_api.py] /__normalizeurl: order default 2"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?order=-time1'
        new_slugs['order'] = '-time1'
        self._run_url_slugs_equal(url, new_slugs)

    # Something that has an old_slug

    def test__api_normalizeurl_order_instrument(self):
        "[test_ui_api.py] /__normalizeurl: order instrument"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?order=instrument'
        new_slugs['order'] = 'instrument'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_order_instrumentid(self):
        "[test_ui_api.py] /__normalizeurl: order instrumentid"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?order=instrumentid'
        new_slugs['order'] = 'instrument'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_order_instrument_instrument(self):
        "[test_ui_api.py] /__normalizeurl: order instrument,instrument"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?order=instrument,instrument'
        new_slugs['order'] = 'instrument'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_order_instrument_instrumentid(self):
        "[test_ui_api.py] /__normalizeurl: order instrument,instrumentid"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?order=instrument,instrumentid'
        new_slugs['order'] = 'instrument'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_order_instrumentid_instrument(self):
        "[test_ui_api.py] /__normalizeurl: order instrumentid,instrument"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?order=instrumentid,instrument'
        new_slugs['order'] = 'instrument'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_order_instrumentid_instrument_2(self):
        "[test_ui_api.py] /__normalizeurl: order instrumentid,instrument 2"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?order=instrumentid,-instrument'
        new_slugs['order'] = 'instrument'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_order_instrumentid_instrument_3(self):
        "[test_ui_api.py] /__normalizeurl: order instrumentid,instrument 3"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?order=-instrumentid,instrument'
        new_slugs['order'] = '-instrument'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_order_instrumentid_instrumentid(self):
        "[test_ui_api.py] /__normalizeurl: order instrumentid,instrumentid"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?order=instrumentid,instrumentid'
        new_slugs['order'] = 'instrument'
        self._run_url_slugs_equal(url, new_slugs)

    # Something that doesn't have an old slug

    def test__api_normalizeurl_order_productid(self):
        "[test_ui_api.py] /__normalizeurl: order productid"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?order=productid'
        new_slugs['order'] = 'productid'
        self._run_url_slugs_equal(url, new_slugs)

    # Bad order

    def test__api_normalizeurl_order_bad_1(self):
        "[test_ui_api.py] /__normalizeurl: order bad 1"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?order=XXX'
        new_slugs['order'] = settings.DEFAULT_SORT_ORDER
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_order_bad_2(self):
        "[test_ui_api.py] /__normalizeurl: order bad 2"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?order=XXX,productid'
        new_slugs['order'] = 'productid'
        self._run_url_slugs_equal(url, new_slugs)

    # Not viewable

    def test__api_normalizeurl_order_ringobsid(self):
        "[test_ui_api.py] /__normalizeurl: order ringobsid"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?order=ringobsid'
        new_slugs['order'] = 'opusid'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_order_not_viewable(self):
        "[test_ui_api.py] /__normalizeurl: order not viewable"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?order=**filespec'
        new_slugs['order'] = settings.DEFAULT_SORT_ORDER
        self._run_url_slugs_equal(url, new_slugs)

    # Single-column range with '1' suffix

    def test__api_normalizeurl_order_observationduration(self):
        "[test_ui_api.py] /__normalizeurl: order observationduration"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?order=observationduration'
        new_slugs['order'] = 'observationduration'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_order_observationduration1(self):
        "[test_ui_api.py] /__normalizeurl: order observationduration1"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?order=observationduration1'
        new_slugs['order'] = 'observationduration'
        self._run_url_slugs_equal(url, new_slugs)

    # Multi-column range with '1' suffix

    def test__api_normalizeurl_order_rightasc(self):
        "[test_ui_api.py] /__normalizeurl: order rightasc"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?order=rightasc'
        new_slugs['order'] = settings.DEFAULT_SORT_ORDER
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_order_rightasc1(self):
        "[test_ui_api.py] /__normalizeurl: order rightasc1"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?order=rightasc1'
        new_slugs['order'] = 'rightasc1'
        self._run_url_slugs_equal(url, new_slugs)

    ### Search slugs

    # Multi-column ranges

    def test__api_normalizeurl_search_multi_good_1(self):
        "[test_ui_api.py] /__normalizeurl: search multi good 1"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=rightasc&rightasc1=10.'
        new_slugs['rightasc1'] = '10.000000'
        new_slugs['qtype-rightasc'] = 'any'
        new_slugs['widgets'] = 'rightasc'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_multi_good_2(self):
        "[test_ui_api.py] /__normalizeurl: search multi good 2"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=rightasc&rightasc2=10.'
        new_slugs['rightasc2'] = '10.000000'
        new_slugs['qtype-rightasc'] = 'any'
        new_slugs['widgets'] = 'rightasc'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_multi_good_12(self):
        "[test_ui_api.py] /__normalizeurl: search multi good 12"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=rightasc&rightasc1=10.&rightasc2=20.'
        new_slugs['rightasc1'] = '10.000000'
        new_slugs['rightasc2'] = '20.000000'
        new_slugs['qtype-rightasc'] = 'any'
        new_slugs['widgets'] = 'rightasc'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_multi_good_1_qtype_only(self):
        "[test_ui_api.py] /__normalizeurl: search multi good 1 qtype only"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=rightasc&rightasc1=10.&qtype-rightasc=only'
        new_slugs['rightasc1'] = '10.000000'
        new_slugs['qtype-rightasc'] = 'only'
        new_slugs['widgets'] = 'rightasc'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_multi_good_2_qtype_all(self):
        "[test_ui_api.py] /__normalizeurl: search multi good 2 qtype all"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=rightasc&rightasc2=10.&qtype-rightasc=all'
        new_slugs['rightasc2'] = '10.000000'
        new_slugs['qtype-rightasc'] = 'all'
        new_slugs['widgets'] = 'rightasc'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_multi_good_12_qtype_any(self):
        "[test_ui_api.py] /__normalizeurl: search multi good 12 qtype any"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=rightasc&rightasc1=10.&rightasc2=20.&qtype-rightasc=any'
        new_slugs['rightasc1'] = '10.000000'
        new_slugs['rightasc2'] = '20.000000'
        new_slugs['qtype-rightasc'] = 'any'
        new_slugs['widgets'] = 'rightasc'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_multi_good_12_qtype_only(self):
        "[test_ui_api.py] /__normalizeurl: search multi good 12 qtype only"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=rightasc&rightasc1=10.&rightasc2=20.&qtype-rightasc=only'
        new_slugs['rightasc1'] = '10.000000'
        new_slugs['rightasc2'] = '20.000000'
        new_slugs['qtype-rightasc'] = 'only'
        new_slugs['widgets'] = 'rightasc'
        self._run_url_slugs_equal(url, new_slugs)

    # Single column ranges

    def test__api_normalizeurl_search_single_good_1(self):
        "[test_ui_api.py] /__normalizeurl: search single good 1"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=observationduration&observationduration1=10.'
        new_slugs['observationduration1'] = '10.0000'
        new_slugs['widgets'] = 'observationduration'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_single_good_2(self):
        "[test_ui_api.py] /__normalizeurl: search single good 2"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=observationduration&observationduration2=10.'
        new_slugs['observationduration2'] = '10.0000'
        new_slugs['widgets'] = 'observationduration'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_single_good_12(self):
        "[test_ui_api.py] /__normalizeurl: search single good 12"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=observationduration&observationduration1=10.&observationduration2=20.'
        new_slugs['observationduration1'] = '10.0000'
        new_slugs['observationduration2'] = '20.0000'
        new_slugs['widgets'] = 'observationduration'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_single_good_1_qtype_only(self):
        "[test_ui_api.py] /__normalizeurl: search single good 1 qtype only"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=observationduration&observationduration1=10.&qtype-observationduration=only'
        new_slugs['observationduration1'] = '10.0000'
        new_slugs['widgets'] = 'observationduration'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_single_good_2_qtype_all(self):
        "[test_ui_api.py] /__normalizeurl: search single good 2 qtype"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=observationduration&observationduration2=10.&qtype-observationduration=all'
        new_slugs['observationduration2'] = '10.0000'
        new_slugs['widgets'] = 'observationduration'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_single_good_12_qtype_any(self):
        "[test_ui_api.py] /__normalizeurl: search single good 12 qtype any"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=observationduration&observationduration1=10.&observationduration2=20.&qtype-observationduration=any'
        new_slugs['observationduration1'] = '10.0000'
        new_slugs['observationduration2'] = '20.0000'
        new_slugs['widgets'] = 'observationduration'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_single_good_12_qtype_only(self):
        "[test_ui_api.py] /__normalizeurl: search single good 12 qtype only"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=observationduration&observationduration1=10.&observationduration2=20.&qtype-observationduration=only'
        new_slugs['observationduration1'] = '10.0000'
        new_slugs['observationduration2'] = '20.0000'
        new_slugs['widgets'] = 'observationduration'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_string_good(self):
        "[test_ui_api.py] /__normalizeurl: search string good"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=volumeid&volumeid=COISS'
        new_slugs['volumeid'] = 'COISS'
        new_slugs['qtype-volumeid'] = 'contains'
        new_slugs['widgets'] = 'volumeid'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_string_bad_1(self):
        "[test_ui_api.py] /__normalizeurl: search string bad 1"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=volumeid&volumeid1=COISS'
        new_slugs['widgets'] = 'volumeid'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_string_bad_2(self):
        "[test_ui_api.py] /__normalizeurl: search string bad 2"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=volumeid&volumeid2=COISS'
        new_slugs['widgets'] = 'volumeid'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_string_good_qtype_contains(self):
        "[test_ui_api.py] /__normalizeurl: search string good qtype contains"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=volumeid&volumeid=COISS&qtype-volumeid=contains'
        new_slugs['volumeid'] = 'COISS'
        new_slugs['qtype-volumeid'] = 'contains'
        new_slugs['widgets'] = 'volumeid'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_string_good_qtype_matches(self):
        "[test_ui_api.py] /__normalizeurl: search string good qtype matches"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=volumeid&volumeid=COISS&qtype-volumeid=matches'
        new_slugs['volumeid'] = 'COISS'
        new_slugs['qtype-volumeid'] = 'matches'
        new_slugs['widgets'] = 'volumeid'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_string_good_qtype_begins(self):
        "[test_ui_api.py] /__normalizeurl: search string good qtype begins"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=volumeid&volumeid=COISS&qtype-volumeid=begins'
        new_slugs['volumeid'] = 'COISS'
        new_slugs['qtype-volumeid'] = 'begins'
        new_slugs['widgets'] = 'volumeid'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_string_good_qtype_ends(self):
        "[test_ui_api.py] /__normalizeurl: search string good qtype ends"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=volumeid&volumeid=COISS&qtype-volumeid=ends'
        new_slugs['volumeid'] = 'COISS'
        new_slugs['qtype-volumeid'] = 'ends'
        new_slugs['widgets'] = 'volumeid'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_string_good_qtype_excludes(self):
        "[test_ui_api.py] /__normalizeurl: search string good qtype excludes"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=volumeid&volumeid=COISS&qtype-volumeid=excludes'
        new_slugs['volumeid'] = 'COISS'
        new_slugs['qtype-volumeid'] = 'excludes'
        new_slugs['widgets'] = 'volumeid'
        self._run_url_slugs_equal(url, new_slugs)

    # Mult field

    def test__api_normalizeurl_search_mult_good(self):
        "[test_ui_api.py] /__normalizeurl: search mult good"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=instrument&instrument=COISS'
        new_slugs['instrument'] = 'COISS'
        new_slugs['widgets'] = 'instrument'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_mult_bad_1(self):
        "[test_ui_api.py] /__normalizeurl: search mult bad 1"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=instrument&instrument1=COISS'
        new_slugs['widgets'] = 'instrument'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_mult_bad_2(self):
        "[test_ui_api.py] /__normalizeurl: search mult bad 2"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=instrument&instrument2=COISS'
        new_slugs['widgets'] = 'instrument'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_mult_bad_12(self):
        "[test_ui_api.py] /__normalizeurl: search mult bad 12"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=instrument&instrument1=COISS&instrument2=COISS'
        new_slugs['widgets'] = 'instrument'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_mult_bad_qtype_only(self):
        "[test_ui_api.py] /__normalizeurl: search mult bad qtype only"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=instrument&instrument=COISS&qtype-instrument=only'
        new_slugs['instrument'] = 'COISS'
        new_slugs['widgets'] = 'instrument'
        self._run_url_slugs_equal(url, new_slugs)

    # Multi-column ranges

    def test__api_normalizeurl_search_multi_bad_1(self):
        "[test_ui_api.py] /__normalizeurl: search multi bad 1"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=rightasc&rightasc1=10.X'
        new_slugs['qtype-rightasc'] = 'any'
        new_slugs['widgets'] = 'rightasc'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_multi_bad_2(self):
        "[test_ui_api.py] /__normalizeurl: search multi bad 2"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=rightasc&rightasc2=10.X'
        new_slugs['qtype-rightasc'] = 'any'
        new_slugs['widgets'] = 'rightasc'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_multi_good_1_bad_2(self):
        "[test_ui_api.py] /__normalizeurl: search multi good 1 bad 2"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=rightasc&rightasc1=10.&rightasc2=20.X'
        new_slugs['rightasc1'] = '10.000000'
        new_slugs['qtype-rightasc'] = 'any'
        new_slugs['widgets'] = 'rightasc'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_multi_bad_1_good_2(self):
        "[test_ui_api.py] /__normalizeurl: search multi bad 1 good 2"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=rightasc&rightasc1=10.X&rightasc2=20.'
        new_slugs['rightasc2'] = '20.000000'
        new_slugs['qtype-rightasc'] = 'any'
        new_slugs['widgets'] = 'rightasc'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_multi_bad_1_bad_2(self):
        "[test_ui_api.py] /__normalizeurl: search multi bad 1 bad 2"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=rightasc&rightasc1=10.X&rightasc2=20.X'
        new_slugs['qtype-rightasc'] = 'any'
        new_slugs['widgets'] = 'rightasc'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_multi_good_1_bad_qtype(self):
        "[test_ui_api.py] /__normalizeurl: search multi good 1 bad qtype"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=rightasc&rightasc1=10.&qtype-rightasc=XXX'
        new_slugs['rightasc1'] = '10.000000'
        new_slugs['qtype-rightasc'] = 'any'
        new_slugs['widgets'] = 'rightasc'
        self._run_url_slugs_equal(url, new_slugs)

    # Single column ranges

    def test__api_normalizeurl_search_single_bad_1(self):
        "[test_ui_api.py] /__normalizeurl: search single bad 1"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=observationduration&observationduration1=10.X'
        new_slugs['widgets'] = 'observationduration'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_single_bad_2(self):
        "[test_ui_api.py] /__normalizeurl: search single bad 2"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=observationduration&observationduration2=10.X'
        new_slugs['widgets'] = 'observationduration'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_single_good_1_bad_2(self):
        "[test_ui_api.py] /__normalizeurl: search single good 1 bad 2"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=observationduration&observationduration1=10.&observationduration2=20.X'
        new_slugs['observationduration1'] = '10.0000'
        new_slugs['widgets'] = 'observationduration'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_single_bad_1_good_2(self):
        "[test_ui_api.py] /__normalizeurl: search single bad 1 good 2"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=observationduration&observationduration1=10.X&observationduration2=20.'
        new_slugs['observationduration2'] = '20.0000'
        new_slugs['widgets'] = 'observationduration'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_single_bad_1_bad_2(self):
        "[test_ui_api.py] /__normalizeurl: search single bad 1 bad 2"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=observationduration&observationduration1=10.X&observationduration2=20.X'
        new_slugs['widgets'] = 'observationduration'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_single_good_1_bad_qtype(self):
        "[test_ui_api.py] /__normalizeurl: search single good 1 bad qtype"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=observationduration&observationduration1=10.&qtype-observationduration=XXX'
        new_slugs['observationduration1'] = '10.0000'
        new_slugs['widgets'] = 'observationduration'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_string_bad_qtype(self):
        "[test_ui_api.py] /__normalizeurl: search string bad qtype"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=volumeid&volumeid=COISS&qtype-volumeid=XXX'
        new_slugs['volumeid'] = 'COISS'
        new_slugs['qtype-volumeid'] = 'contains'
        new_slugs['widgets'] = 'volumeid'
        self._run_url_slugs_equal(url, new_slugs)

    # Old slugs and duplicates

    def test__api_normalizeurl_search_multi_old_1(self):
        "[test_ui_api.py] /__normalizeurl: search multi old 1"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=RINGGEOringradius&ringradius1=10.'
        new_slugs['RINGGEOringradius1'] = '10.000000'
        new_slugs['qtype-RINGGEOringradius'] = 'any'
        new_slugs['widgets'] = 'RINGGEOringradius'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_mult_old_2(self):
        "[test_ui_api.py] /__normalizeurl: search multi old 2"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=RINGGEOringradius&ringradius2=10.'
        new_slugs['RINGGEOringradius2'] = '10.000000'
        new_slugs['qtype-RINGGEOringradius'] = 'any'
        new_slugs['widgets'] = 'RINGGEOringradius'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_multi_old_12(self):
        "[test_ui_api.py] /__normalizeurl: search multi old 12"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=RINGGEOringradius&ringradius1=10.&ringradius2=20.'
        new_slugs['RINGGEOringradius1'] = '10.000000'
        new_slugs['RINGGEOringradius2'] = '20.000000'
        new_slugs['qtype-RINGGEOringradius'] = 'any'
        new_slugs['widgets'] = 'RINGGEOringradius'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_multi_mix_new_old(self):
        "[test_ui_api.py] /__normalizeurl: search multi mix new 1 old 2"
        url = '/opus/__normalizeurl.json?widgets=RINGGEOringradius&RINGGEOringradius1=10.&ringradius2=20.'
        new_slugs = dict(self.default_url_slugs)
        new_slugs['RINGGEOringradius1'] = '10.000000'
        new_slugs['RINGGEOringradius2'] = '20.000000'
        new_slugs['qtype-RINGGEOringradius'] = 'any'
        new_slugs['widgets'] = 'RINGGEOringradius'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_multi_mix_old_new(self):
        "[test_ui_api.py] /__normalizeurl: search multi mix old 1 new 2"
        url = '/opus/__normalizeurl.json?widgets=RINGGEOringradius&ringradius1=10.&RINGGEOringradius2=20.'
        new_slugs = dict(self.default_url_slugs)
        new_slugs['RINGGEOringradius1'] = '10.000000'
        new_slugs['RINGGEOringradius2'] = '20.000000'
        new_slugs['qtype-RINGGEOringradius'] = 'any'
        new_slugs['widgets'] = 'RINGGEOringradius'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_multi_dup_old_1(self):
        "[test_ui_api.py] /__normalizeurl: search multi dup old 1"
        url = '/opus/__normalizeurl.json?widgets=RINGGEOringradius&ringradius1=10.&RINGGEOringradius1=20.'
        new_slugs = dict(self.default_url_slugs)
        new_slugs['RINGGEOringradius1'] = '20.000000' # Parsed in alphabetical order
        new_slugs['qtype-RINGGEOringradius'] = 'any'
        new_slugs['widgets'] = 'RINGGEOringradius'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_multi_dup_old_2(self):
        "[test_ui_api.py] /__normalizeurl: search multi dup old 2"
        url = '/opus/__normalizeurl.json?widgets=RINGGEOringradius&RINGGEOringradius2=10.&ringradius2=20.'
        new_slugs = dict(self.default_url_slugs)
        new_slugs['RINGGEOringradius2'] = '10.000000'
        new_slugs['qtype-RINGGEOringradius'] = 'any'
        new_slugs['widgets'] = 'RINGGEOringradius'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_multi_old_1_old_qtype(self):
        "[test_ui_api.py] /__normalizeurl: search multi old 1 old qtype"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=RINGGEOringradius&ringradius1=10.&qtype-ringradius=only'
        new_slugs['RINGGEOringradius1'] = '10.000000'
        new_slugs['qtype-RINGGEOringradius'] = 'only'
        new_slugs['widgets'] = 'RINGGEOringradius'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_multi_old_1_new_qtype(self):
        "[test_ui_api.py] /__normalizeurl: search multi old 1 new qtype"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=RINGGEOringradius&ringradius1=10.&qtype-RINGGEOringradius=only'
        new_slugs['RINGGEOringradius1'] = '10.000000'
        new_slugs['qtype-RINGGEOringradius'] = 'only'
        new_slugs['widgets'] = 'RINGGEOringradius'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_multi_new_1_old_qtype(self):
        "[test_ui_api.py] /__normalizeurl: search multi new 1 old qtype"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=RINGGEOringradius&RINGGEOringradius1=10.&qtype-ringradius=only'
        new_slugs['RINGGEOringradius1'] = '10.000000'
        new_slugs['qtype-RINGGEOringradius'] = 'only'
        new_slugs['widgets'] = 'RINGGEOringradius'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_multi_new_1_new_qtype(self):
        "[test_ui_api.py] /__normalizeurl: search multi new 1 new qtype"
        new_slugs = dict(self.default_url_slugs)
        url = '/opus/__normalizeurl.json?widgets=RINGGEOringradius&RINGGEOringradius1=10.&qtype-RINGGEOringradius=only'
        new_slugs['RINGGEOringradius1'] = '10.000000'
        new_slugs['qtype-RINGGEOringradius'] = 'only'
        new_slugs['widgets'] = 'RINGGEOringradius'
        self._run_url_slugs_equal(url, new_slugs)

    # Slug that can't be searched

    def test__api_normalizeurl_search_not_searchable(self):
        "[test_ui_api.py] /__normalizeurl: search not searchable"
        url = '/opus/__normalizeurl.json?**previewimages=XXX'
        new_slugs = dict(self.default_url_slugs)
        self._run_url_slugs_equal(url, new_slugs)

    # Convert ringobsid to opusid

    def test__api_normalizeurl_search_ringobsid(self):
        "[test_ui_api.py] /__normalizeurl: search ringobsid"
        url = '/opus/__normalizeurl.json?ringobsid=S_IMG_VG2_ISS_4360845_N'
        new_slugs = dict(self.default_url_slugs)
        new_slugs['opusid'] = 'vg-iss-2-s-c4360845'
        new_slugs['qtype-opusid'] = 'contains'
        new_slugs['widgets'] = 'opusid'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_ringobsid_bad(self):
        "[test_ui_api.py] /__normalizeurl: search ringobsid bad"
        url = '/opus/__normalizeurl.json?ringobsid=S_IMG_VG2_ISS_4360846_N'
        new_slugs = dict(self.default_url_slugs)
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_ringobsid_bad_2(self):
        "[test_ui_api.py] /__normalizeurl: search ringobsid bad 2"
        url = '/opus/__normalizeurl.json?ringobsid=XXX'
        new_slugs = dict(self.default_url_slugs)
        self._run_url_slugs_equal(url, new_slugs)

    ### Real-world tests

    def test__api_normalizeurl_real_1(self):
        "[test_ui_api.py] /__normalizeurl: real 1"
        url = '/opus/__normalizeurl.json?planet=Saturn&typeid=Image&missionid=Voyager&timesec1=1980-09-27T02:16&timesec2=1980-09-28T02:17&qtype-volumeid=contains&view=detail&browse=gallery&colls_browse=gallery&page=1&gallery_data_viewer=true&limit=100&order=time1&cols=ringobsid,planet,target,phase1,phase2,time1,time2&widgets=timesec1&widgets2=&detail=S_IMG_CO_ISS_1460961026_N'
        expected = {'new_url': 'mission=Voyager&planet=Saturn&time1=1980-09-27T02:16:00.000&time2=1980-09-28T02:17:00.000&qtype-time=any&observationtype=Image&cols=opusid,instrument,planet,target,time1,observationduration&widgets=time,mission,planet,observationtype&order=time1,opusid&view=detail&browse=gallery&cart_browse=gallery&startobs=1&cart_startobs=1&detail=co-iss-n1460961026', 'new_slugs': [{'mission': 'Voyager'}, {'planet': 'Saturn'}, {'time1': '1980-09-27T02:16:00.000'}, {'time2': '1980-09-28T02:17:00.000'}, {'qtype-time': 'any'}, {'observationtype': 'Image'}, {'cols': 'opusid,instrument,planet,target,time1,observationduration'}, {'widgets': 'time,mission,planet,observationtype'}, {'order': 'time1,opusid'}, {'view': 'detail'}, {'browse': 'gallery'}, {'cart_browse': 'gallery'}, {'startobs': 1}, {'cart_startobs': 1}, {'detail': 'co-iss-n1460961026'}], 'msg': '<p>Your bookmarked URL is from a previous version of OPUS. It has been adjusted to conform to the current version.</p><p>We found the following issues with your bookmarked URL:</p><ul><li>Your URL uses the old defaults for selected metadata; they have been replaced with the new defaults.</li><li>You appear to be using an obsolete RINGOBS_ID (S_IMG_CO_ISS_1460961026_N) instead of the equivalent new OPUS_ID (co-iss-n1460961026); it has been converted for you.</li><li>Search query type "Volume ID" refers to a search field that is not being used; it has been ignored.</li></ul><p>We strongly recommend that you replace your old bookmark with the updated URL in your browser so that you will not see this message in the future.</p>'}
        self._run_json_equal(url, expected)

    def test__api_normalizeurl_real_2(self):
        "[test_ui_api.py] /__normalizeurl: real 2"
        url = '/opus/__normalizeurl.json?planet=Jupiter&target=EUROPA&missionid=Voyager&view=detail&browse=data&colls_browse=gallery&page=1&gallery_data_viewer=true&limit=100&order=time1&cols=ringobsid,planet,target,phase1,phase2,time1,time2&widgets=missionid,planet,target&widgets2=&detail=S_IMG_CO_ISS_1460961026_N'
        expected = {'new_url': 'mission=Voyager&planet=Jupiter&target=EUROPA&cols=opusid,instrument,planet,target,time1,observationduration&widgets=mission,planet,target&order=time1,opusid&view=detail&browse=data&cart_browse=gallery&startobs=1&cart_startobs=1&detail=co-iss-n1460961026', 'new_slugs': [{'mission': 'Voyager'}, {'planet': 'Jupiter'}, {'target': 'EUROPA'}, {'cols': 'opusid,instrument,planet,target,time1,observationduration'}, {'widgets': 'mission,planet,target'}, {'order': 'time1,opusid'}, {'view': 'detail'}, {'browse': 'data'}, {'cart_browse': 'gallery'}, {'startobs': 1}, {'cart_startobs': 1}, {'detail': 'co-iss-n1460961026'}], 'msg': '<p>Your bookmarked URL is from a previous version of OPUS. It has been adjusted to conform to the current version.</p><p>We found the following issues with your bookmarked URL:</p><ul><li>Your URL uses the old defaults for selected metadata; they have been replaced with the new defaults.</li><li>You appear to be using an obsolete RINGOBS_ID (S_IMG_CO_ISS_1460961026_N) instead of the equivalent new OPUS_ID (co-iss-n1460961026); it has been converted for you.</li></ul><p>We strongly recommend that you replace your old bookmark with the updated URL in your browser so that you will not see this message in the future.</p>'}
        self._run_json_equal(url, expected)

    def test__api_normalizeurl_real_3(self):
        "[test_ui_api.py] /__normalizeurl: real 3"
        url = '/opus/__normalizeurl.json?mission=Cassini&target=Jupiter,Ganymede,Europa,Callisto,Io&instrument=Cassini+ISS&view=browse&browse=gallery&colls_browse=gallery&page=1&gallery_data_viewer=true&limit=100&order=time1&cols=opusid,instrumentid,planet,target,time1,observationduration&widgets=instrument,mission,planet,target&widgets2=&detail='
        expected = {'new_url': 'instrument=Cassini ISS&mission=Cassini&target=Callisto,Europa,Ganymede,Io,Jupiter&cols=opusid,instrument,planet,target,time1,observationduration&widgets=instrument,mission,planet,target&order=time1,opusid&view=browse&browse=gallery&cart_browse=gallery&startobs=1&cart_startobs=1&detail=', 'new_slugs': [{'instrument': 'Cassini ISS'}, {'mission': 'Cassini'}, {'target': 'Callisto,Europa,Ganymede,Io,Jupiter'}, {'cols': 'opusid,instrument,planet,target,time1,observationduration'}, {'widgets': 'instrument,mission,planet,target'}, {'order': 'time1,opusid'}, {'view': 'browse'}, {'browse': 'gallery'}, {'cart_browse': 'gallery'}, {'startobs': 1}, {'cart_startobs': 1}, {'detail': ''}], 'msg': '<p>Your bookmarked URL is from a previous version of OPUS. It has been adjusted to conform to the current version.</p><p>We strongly recommend that you replace your old bookmark with the updated URL in your browser so that you will not see this message in the future.</p>'}
        self._run_json_equal(url, expected)

    def test__api_normalizeurl_real_4(self):
        "[test_ui_api.py] /__normalizeurl: real 4"
        url = '/opus/__normalizeurl.json?mission=Voyager&observationtype=Image&planet=Saturn&time1=1980-09-27T02:16:00.000&time2=1980-09-28T02:17:00.000&qtype-time=any&cols=opusid,instrument,planet,target,time1,observationduration&widgets=time,mission,planet,observationtype&order=time1,opusid&view=detail&browse=gallery&startobs=1&cart_browse=gallery&detail=co-iss-n1460961026'
        expected = {'new_url': 'mission=Voyager&observationtype=Image&planet=Saturn&time1=1980-09-27T02:16:00.000&time2=1980-09-28T02:17:00.000&qtype-time=any&cols=opusid,instrument,planet,target,time1,observationduration&widgets=time,mission,planet,observationtype&order=time1,opusid&view=detail&browse=gallery&cart_browse=gallery&startobs=1&cart_startobs=1&detail=co-iss-n1460961026', 'new_slugs': [{'mission': 'Voyager'}, {'observationtype': 'Image'}, {'planet': 'Saturn'}, {'time1': '1980-09-27T02:16:00.000'}, {'time2': '1980-09-28T02:17:00.000'}, {'qtype-time': 'any'}, {'cols': 'opusid,instrument,planet,target,time1,observationduration'}, {'widgets': 'time,mission,planet,observationtype'}, {'order': 'time1,opusid'}, {'view': 'detail'}, {'browse': 'gallery'}, {'cart_browse': 'gallery'}, {'startobs': 1}, {'cart_startobs': 1}, {'detail': 'co-iss-n1460961026'}], 'msg': None}
        self._run_json_equal(url, expected)

    def test__api_normalizeurl_real_5(self):
        "[test_ui_api.py] /__normalizeurl: real 5"
        url = '/opus/__normalizeurl.json?mission=Voyager&observationtype=Image&planet=Saturn&time1=1980-09-27T02:16:00.000&time2=1980-09-28T02:17:00.000&qtype-time=any&cols=opusid,instrument,planet,target,time1,observationduration&widgets=time,mission,planet,observationtype&order=time1,opusid&view=detail&browse=gallery&startobs=1&cart_browse=gallery&detail='
        expected = {'new_url': 'mission=Voyager&observationtype=Image&planet=Saturn&time1=1980-09-27T02:16:00.000&time2=1980-09-28T02:17:00.000&qtype-time=any&cols=opusid,instrument,planet,target,time1,observationduration&widgets=time,mission,planet,observationtype&order=time1,opusid&view=detail&browse=gallery&cart_browse=gallery&startobs=1&cart_startobs=1&detail=', 'new_slugs': [{'mission': 'Voyager'}, {'observationtype': 'Image'}, {'planet': 'Saturn'}, {'time1': '1980-09-27T02:16:00.000'}, {'time2': '1980-09-28T02:17:00.000'}, {'qtype-time': 'any'}, {'cols': 'opusid,instrument,planet,target,time1,observationduration'}, {'widgets': 'time,mission,planet,observationtype'}, {'order': 'time1,opusid'}, {'view': 'detail'}, {'browse': 'gallery'}, {'cart_browse': 'gallery'}, {'startobs': 1}, {'cart_startobs': 1}, {'detail': ''}], 'msg': None}
        self._run_json_equal(url, expected)

    def test__api_normalizeurl_real_6(self):
        "[test_ui_api.py] /__normalizeurl: real 6"
        url = '/opus/__normalizeurl.json?SURFACEGEOplutocenterresolution2=5.00000&SURFACEGEOplutophase1=160.000&surfacegeometrytargetname=Pluto&qtype-SURFACEGEOplutophase=any&cols=opusid,instrument,time1,SURFACEGEOplutoplanetographiclatitude1,SURFACEGEOplutoplanetographiclatitude2,SURFACEGEOplutoIAUwestlongitude1,SURFACEGEOplutoIAUwestlongitude2,SURFACEGEOplutocenterdistance,SURFACEGEOplutocenterresolution,SURFACEGEOplutophase1,SURFACEGEOplutophase2&widgets=SURFACEGEOplutocenterresolution,SURFACEGEOplutophase,surfacegeometrytargetname&order=time1,opusid&view=search&browse=gallery&cart_browse=gallery&startobs=1&cart_startobs=1&detail='
        expected = {"new_url": "SURFACEGEOplutocenterresolution2=5.00000&SURFACEGEOplutophase1=160.000&qtype-SURFACEGEOplutophase=any&surfacegeometrytargetname=Pluto&cols=opusid,instrument,time1,SURFACEGEOplutoplanetographiclatitude1,SURFACEGEOplutoplanetographiclatitude2,SURFACEGEOplutoIAUwestlongitude1,SURFACEGEOplutoIAUwestlongitude2,SURFACEGEOplutocenterdistance,SURFACEGEOplutocenterresolution,SURFACEGEOplutophase1,SURFACEGEOplutophase2&widgets=SURFACEGEOplutocenterresolution,SURFACEGEOplutophase,surfacegeometrytargetname&order=time1,opusid&view=search&browse=gallery&cart_browse=gallery&startobs=1&cart_startobs=1&detail=", "new_slugs": [{"SURFACEGEOplutocenterresolution2": "5.00000"}, {"SURFACEGEOplutophase1": "160.000"}, {"qtype-SURFACEGEOplutophase": "any"}, {"surfacegeometrytargetname": "Pluto"}, {"cols": "opusid,instrument,time1,SURFACEGEOplutoplanetographiclatitude1,SURFACEGEOplutoplanetographiclatitude2,SURFACEGEOplutoIAUwestlongitude1,SURFACEGEOplutoIAUwestlongitude2,SURFACEGEOplutocenterdistance,SURFACEGEOplutocenterresolution,SURFACEGEOplutophase1,SURFACEGEOplutophase2"}, {"widgets": "SURFACEGEOplutocenterresolution,SURFACEGEOplutophase,surfacegeometrytargetname"}, {"order": "time1,opusid"}, {"view": "search"}, {"browse": "gallery"}, {"cart_browse": "gallery"}, {"startobs": 1}, {"cart_startobs": 1}, {"detail": ""}], "msg": None}
        self._run_json_equal(url, expected)

# http://pds-rings-tools.seti.org/opus/#/planet=Saturn&typeid=Image&missionid=Voyager&timesec1=1980-09-27T02:16&timesec2=1980-09-28T02:17&qtype-volumeid=contains&view=detail&browse=gallery&colls_browse=gallery&page=1&gallery_data_viewer=true&limit=100&order=time1&cols=ringobsid,planet,target,phase1,phase2,time1,time2&widgets=timesec1&widgets2=&detail=S_IMG_VG1_ISS_3353709_N
# http://pds-rings-tools.seti.org/opus/#/planet=Jupiter&target=EUROPA&missionid=Voyager&view=detail&browse=data&colls_browse=gallery&page=1&gallery_data_viewer=true&limit=100&order=time1&cols=ringobsid,planet,target,phase1,phase2,time1,time2&widgets=missionid,planet,target&widgets2=&detail=J_IMG_VG2_ISS_2076737_N
# https://tools.pds-rings.seti.org/opus/#/mission=Cassini&target=Jupiter,Ganymede,Europa,Callisto,Io&instrument=Cassini+ISS&view=browse&browse=gallery&colls_browse=gallery&page=1&gallery_data_viewer=true&limit=100&order=time1&cols=opusid,instrumentid,planet,target,time1,observationduration&widgets=instrument,mission,planet,target&widgets2=&detail=
