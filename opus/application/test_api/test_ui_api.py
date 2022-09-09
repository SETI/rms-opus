# opus/application/test_api/test_ui_api.py

import json
import logging
import requests
from unittest import TestCase

from django.core.cache import cache
from rest_framework.test import RequestsClient

from .api_test_helper import ApiTestHelper

import settings

class ApiUITests(TestCase, ApiTestHelper):

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

    def _run_url_slugs_equal(self, url, expected, msg_contains=None):
        print(url)
        response = self._get_response(url)
        self.assertEqual(response.status_code, 200)
        jdata = json.loads(response.content)
        slug_data = {}
        for slug_dict in jdata['new_slugs']:
            slug_data.update(slug_dict)
        print('Got:')
        print(slug_data)
        print(jdata['msg'])
        print('Expected:')
        print(expected)
        print(msg_contains)
        self.assertEqual(expected, slug_data)
        if msg_contains:
            self.assertTrue(jdata['msg'] is not None and
                            msg_contains in jdata['msg'])
        else:
            self.assertIsNone(jdata['msg'])


            ##############################################
            ######### /__notifications API TESTS #########
            ##############################################

    def test__api_notifications(self):
        "[test_ui_api.py] /__notifications: normal"
        url = '/__notifications.json'
        self._run_status_equal(url, 200)


            ######################################
            ######### /__dummy API TESTS #########
            ######################################

    def test__api_dummy(self):
        "[test_ui_api.py] /__dummy: normal"
        url = '/__dummy.json'
        self._run_status_equal(url, 200)


            #############################################
            ######### /__normalizeurl API TESTS #########
            #############################################

    ### Empty

    def test__api_normalizeurl_empty(self):
        "[test_ui_api.py] /__normalizeurl: empty"
        url = '/__normalizeurl.json'
        self._run_url_slugs_equal(url, self.default_url_slugs)

    ### view=

    def test__api_normalizeurl_view_search(self):
        "[test_ui_api.py] /__normalizeurl: view search"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?view=search'
        new_slugs['view'] = 'search'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_view_browse(self):
        "[test_ui_api.py] /__normalizeurl: view browse"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?view=browse'
        new_slugs['view'] = 'browse'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_view_collection(self):
        "[test_ui_api.py] /__normalizeurl: view collection"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?view=collection'
        new_slugs['view'] = 'cart'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='previous version')

    def test__api_normalizeurl_view_cart(self):
        "[test_ui_api.py] /__normalizeurl: view cart"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?view=cart'
        new_slugs['view'] = 'cart'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_view_detail(self):
        "[test_ui_api.py] /__normalizeurl: view detail"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?view=detail'
        new_slugs['view'] = 'detail'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_view_badval(self):
        "[test_ui_api.py] /__normalizeurl: view badval"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?view=badval'
        new_slugs['view'] = 'search'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='not one of')

    ### browse=

    def test__api_normalizeurl_browse_gallery(self):
        "[test_ui_api.py] /__normalizeurl: browse gallery"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?browse=gallery'
        new_slugs['browse'] = 'gallery'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_browse_data(self):
        "[test_ui_api.py] /__normalizeurl: browse data"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?browse=data'
        new_slugs['browse'] = 'data'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_browse_badval(self):
        "[test_ui_api.py] /__normalizeurl: browse badval"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?browse=badval'
        new_slugs['browse'] = 'gallery'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='The value for "browse" was not either "gallery" or "data"; it has been set to "gallery".')

    ### colls_browse=

    def test__api_normalizeurl_colls_browse_gallery(self):
        "[test_ui_api.py] /__normalizeurl: colls_browse gallery"
        # This is really just testing the default, because we don't pay
        # attention to colls_browse in normalizeurl
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?colls_browse=gallery'
        new_slugs['cart_browse'] = 'gallery'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_colls_browse_data(self):
        "[test_ui_api.py] /__normalizeurl: colls_browse data"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?colls_browse=data'
        new_slugs['cart_browse'] = 'gallery'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_colls_browse_badval(self):
        "[test_ui_api.py] /__normalizeurl: colls_browse badval"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?colls_browse=badval'
        new_slugs['cart_browse'] = 'gallery'
        self._run_url_slugs_equal(url, new_slugs)

    ### cart_browse=

    def test__api_normalizeurl_cart_browse_gallery(self):
        "[test_ui_api.py] /__normalizeurl: cart_browse gallery"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?cart_browse=gallery'
        new_slugs['cart_browse'] = 'gallery'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_cart_browse_data(self):
        "[test_ui_api.py] /__normalizeurl: cart_browse data"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?cart_browse=data'
        new_slugs['cart_browse'] = 'data'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_cart_browse_badval(self):
        "[test_ui_api.py] /__normalizeurl: cart_browse badval"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?cart_browse=badval'
        new_slugs['cart_browse'] = 'gallery'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='The value for "cart_browse" was not either "gallery" or "data"; it has been set to "gallery".')

    ### page=

    def test__api_normalizeurl_page_0(self):
        "[test_ui_api.py] /__normalizeurl: page 0"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?page=0'
        new_slugs['startobs'] = 1
        self._run_url_slugs_equal(url, new_slugs, msg_contains='The value for the "page" term was not between 1 and 20000; it has been set to 1.')

    def test__api_normalizeurl_page_n100(self):
        "[test_ui_api.py] /__normalizeurl: page -100"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?page=-100'
        new_slugs['startobs'] = 1
        self._run_url_slugs_equal(url, new_slugs, msg_contains='The value for the "page" term was not between 1 and 20000; it has been set to 1.')

    def test__api_normalizeurl_page_1000000000000000000000000(self):
        "[test_ui_api.py] /__normalizeurl: page 1000000000000000000000000"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?page=1000000000000000000000000'
        new_slugs['startobs'] = 1
        self._run_url_slugs_equal(url, new_slugs, msg_contains='The value for the "page" term was not between 1 and 20000; it has been set to 1.')

    def test__api_normalizeurl_page_1(self):
        "[test_ui_api.py] /__normalizeurl: page 1"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?page=1'
        new_slugs['startobs'] = 1
        self._run_url_slugs_equal(url, new_slugs, msg_contains='previous version')

    def test__api_normalizeurl_page_2(self):
        "[test_ui_api.py] /__normalizeurl: page 2"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?page=2'
        new_slugs['startobs'] = 101
        self._run_url_slugs_equal(url, new_slugs, msg_contains='previous version')

    def test__api_normalizeurl_page_100(self):
        "[test_ui_api.py] /__normalizeurl: page 100"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?page=100'
        new_slugs['startobs'] = 9901
        self._run_url_slugs_equal(url, new_slugs, msg_contains='previous version')

    def test__api_normalizeurl_page_105(self):
        "[test_ui_api.py] /__normalizeurl: page 10.5"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?page=10.5'
        new_slugs['startobs'] = 1
        self._run_url_slugs_equal(url, new_slugs, msg_contains='The value for the "page" term was not a valid integer; it has been set to 1.')

    def test__api_normalizeurl_page_1e2(self):
        "[test_ui_api.py] /__normalizeurl: page 1e2"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?page=1e2'
        new_slugs['startobs'] = 1
        self._run_url_slugs_equal(url, new_slugs, msg_contains='The value for the "page" term was not a valid integer; it has been set to 1.')

    def test__api_normalizeurl_page_XXX(self):
        "[test_ui_api.py] /__normalizeurl: page XXX"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?page=XXX'
        new_slugs['startobs'] = 1
        self._run_url_slugs_equal(url, new_slugs, msg_contains='The value for the "page" term was not a valid integer; it has been set to 1.')

    ### startobs=

    def test__api_normalizeurl_startobs_0(self):
        "[test_ui_api.py] /__normalizeurl: startobs 0"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?startobs=0'
        new_slugs['startobs'] = 1
        self._run_url_slugs_equal(url, new_slugs, msg_contains='The value for the "startobs" term was not between 1 and 10000000; it has been set to 1.')

    def test__api_normalizeurl_startobs_n100(self):
        "[test_ui_api.py] /__normalizeurl: startobs -100"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?startobs=-100'
        new_slugs['startobs'] = 1
        self._run_url_slugs_equal(url, new_slugs, msg_contains='not between')

    def test__api_normalizeurl_startobs_1000000000000000000000000(self):
        "[test_ui_api.py] /__normalizeurl: startobs 1000000000000000000000000"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?startobs=1000000000000000000000000'
        new_slugs['startobs'] = 1
        self._run_url_slugs_equal(url, new_slugs, msg_contains='The value for the "startobs" term was not between 1 and 10000000; it has been set to 1.')

    def test__api_normalizeurl_startobs_1(self):
        "[test_ui_api.py] /__normalizeurl: startobs 1"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?startobs=1'
        new_slugs['startobs'] = 1
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_startobs_2(self):
        "[test_ui_api.py] /__normalizeurl: startobs 2"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?startobs=2'
        new_slugs['startobs'] = 2
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_startobs_100(self):
        "[test_ui_api.py] /__normalizeurl: startobs 100"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?startobs=100'
        new_slugs['startobs'] = 100
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_startobs_105(self):
        "[test_ui_api.py] /__normalizeurl: startobs 10.5"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?startobs=10.5'
        new_slugs['startobs'] = 1
        self._run_url_slugs_equal(url, new_slugs, msg_contains='The value for the "startobs" term was not a valid integer; it has been set to 1.')

    def test__api_normalizeurl_startobs_1e2(self):
        "[test_ui_api.py] /__normalizeurl: startobs 1e2"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?startobs=1e2'
        new_slugs['startobs'] = 1
        self._run_url_slugs_equal(url, new_slugs, msg_contains='The value for the "startobs" term was not a valid integer; it has been set to 1.')

    def test__api_normalizeurl_startobs_XXX(self):
        "[test_ui_api.py] /__normalizeurl: startobs XXX"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?startobs=XXX'
        new_slugs['startobs'] = 1
        self._run_url_slugs_equal(url, new_slugs, msg_contains='The value for the "startobs" term was not a valid integer; it has been set to 1.')

    def test__api_normalizeurl_page_startobs(self):
        "[test_ui_api.py] /__normalizeurl: page and startobs"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?page=10&startobs=5'
        new_slugs['startobs'] = 5
        self._run_url_slugs_equal(url, new_slugs, msg_contains='previous version')

    ### detail=

    def test__api_normalizeurl_detail_opusid(self):
        "[test_ui_api.py] /__normalizeurl: detail opusid"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?detail=co-iss-n1460961026'
        new_slugs['detail'] = 'co-iss-n1460961026'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_detail_opusid_bad(self):
        "[test_ui_api.py] /__normalizeurl: detail opusid bad"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?detail=co-iss-n1460961027'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='The OPUS_ID specified for the "detail" tab was not found in the current database; it has been ignored.')

    def test__api_normalizeurl_detail_ringobsid(self):
        "[test_ui_api.py] /__normalizeurl: detail ringobsid"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?detail=S_IMG_CO_ISS_1460961026_N'
        new_slugs['detail'] = 'co-iss-n1460961026'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='You appear to be using an obsolete RINGOBS_ID (S_IMG_CO_ISS_1460961026_N) instead of the equivalent new OPUS_ID (co-iss-n1460961026); it has been converted for you.')

    def test__api_normalizeurl_detail_ringobsid_bad(self):
        "[test_ui_api.py] /__normalizeurl: detail ringobsid bad"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?detail=S_IMG_CO_ISS_14609610267_N'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='You appear to be using an obsolete RINGOBS_ID (S_IMG_CO_ISS_14609610267_N), but it could not be converted to a new OPUS_ID. It has been ignored.')

    def test__api_normalizeurl_detail_badval(self):
        "[test_ui_api.py] /__normalizeurl: detail badval"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?detail=XXX'
        new_slugs['detail'] = ''
        self._run_url_slugs_equal(url, new_slugs, msg_contains='The OPUS_ID specified for the "detail" tab was not found in the current database; it has been ignored.')

    ### reqno= (an ignored slug)

    def test__api_normalizeurl_reqno_5(self):
        "[test_ui_api.py] /__normalizeurl: reqno 5"
        # Should be ignored
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?reqno=5'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_reqno_XXX(self):
        "[test_ui_api.py] /__normalizeurl: reqno XXX"
        # Should be ignored
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?reqno=XXX'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_reqno(self):
        "[test_ui_api.py] /__normalizeurl: reqno empty"
        # Should be ignored
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?reqno='
        self._run_url_slugs_equal(url, new_slugs)

    ### Lonely qtype - these are qtypes without matching searches or widgets

    def test__api_normalizeurl_lonely_qtype_bad_slug(self):
        "[test_ui_api.py] /__normalizeurl: lonely qtype bad slug"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?qtype-fredethel=any'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Search term "qtype-fredethel" is unknown; it has been ignored.')

    def test__api_normalizeurl_lonely_qtype_not_used(self):
        "[test_ui_api.py] /__normalizeurl: lonely qtype not used"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?qtype-rightasc=any'
        new_slugs['widgets'] = 'rightasc'
        new_slugs['qtype-rightasc'] = 'any'
        new_slugs['unit-rightasc'] = 'degrees'
        self._run_url_slugs_equal(url, new_slugs)

    # Lonely qtype - these are qtypes without matching searches but with
    # widgets

    def test__api_normalizeurl_lonely_qtype_used_any(self):
        "[test_ui_api.py] /__normalizeurl: lonely qtype used any"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=rightasc&qtype-rightasc=any'
        new_slugs['widgets'] = 'rightasc'
        new_slugs['qtype-rightasc'] = 'any'
        new_slugs['unit-rightasc'] = 'degrees'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_lonely_qtype_used_any_clause_1(self):
        "[test_ui_api.py] /__normalizeurl: lonely qtype used only _1"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=rightasc&qtype-rightasc_1=only'
        new_slugs['widgets'] = 'rightasc'
        new_slugs['qtype-rightasc'] = 'only'
        new_slugs['unit-rightasc'] = 'degrees'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_lonely_qtype_used_any_clause_2(self):
        "[test_ui_api.py] /__normalizeurl: lonely qtype used only _2"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=rightasc&qtype-rightasc_2=only'
        new_slugs['widgets'] = 'rightasc'
        new_slugs['qtype-rightasc'] = 'only'
        new_slugs['unit-rightasc'] = 'degrees'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_lonely_qtype_used_any_clause_1_2(self):
        "[test_ui_api.py] /__normalizeurl: lonely qtype used all/only _1_2"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=rightasc&qtype-rightasc_1=all&qtype-rightasc_2=only'
        new_slugs['widgets'] = 'rightasc'
        new_slugs['qtype-rightasc_01'] = 'all'
        new_slugs['qtype-rightasc_02'] = 'only'
        new_slugs['unit-rightasc_01'] = 'degrees'
        new_slugs['unit-rightasc_02'] = 'degrees'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_lonely_qtype_used_any_clause_10_20(self):
        "[test_ui_api.py] /__normalizeurl: lonely qtype used all/only _10_20"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=rightasc&qtype-rightasc_10=all&qtype-rightasc_20=only'
        new_slugs['widgets'] = 'rightasc'
        new_slugs['qtype-rightasc_01'] = 'all'
        new_slugs['qtype-rightasc_02'] = 'only'
        new_slugs['unit-rightasc_01'] = 'degrees'
        new_slugs['unit-rightasc_02'] = 'degrees'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_lonely_qtype_used_any_bad(self):
        "[test_ui_api.py] /__normalizeurl: lonely qtype used any bad"
        # Single column range doesn't take qtypes
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=observationduration&qtype-observationduration=any'
        new_slugs['widgets'] = 'observationduration'
        new_slugs['unit-observationduration'] = 'seconds'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Search term "qtype-observationduration" is a query type for a field that does not allow query types; it has been ignored.')

    def test__api_normalizeurl_lonely_qtype_used_any_bad_clause(self):
        "[test_ui_api.py] /__normalizeurl: lonely qtype used any bad _2"
        # Single column range doesn't take qtypes
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=observationduration&qtype-observationduration_2=any'
        new_slugs['widgets'] = 'observationduration'
        new_slugs['unit-observationduration'] = 'seconds'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Search term "qtype-observationduration_2" is a query type for a field that does not allow query types; it has been ignored.')

    def test__api_normalizeurl_lonely_qtype_used_all(self):
        "[test_ui_api.py] /__normalizeurl: lonely qtype used all"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=rightasc&qtype-rightasc=all'
        new_slugs['widgets'] = 'rightasc'
        new_slugs['qtype-rightasc'] = 'all'
        new_slugs['unit-rightasc'] = 'degrees'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_lonely_qtype_used_only(self):
        "[test_ui_api.py] /__normalizeurl: lonely qtype used only"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=rightasc&qtype-rightasc=only'
        new_slugs['widgets'] = 'rightasc'
        new_slugs['qtype-rightasc'] = 'only'
        new_slugs['unit-rightasc'] = 'degrees'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_lonely_qtype_used_multi_badval_XXX(self):
        "[test_ui_api.py] /__normalizeurl: lonely qtype used multi badval XXX"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=rightasc&qtype-rightasc=XXX'
        new_slugs['widgets'] = 'rightasc'
        new_slugs['qtype-rightasc'] = 'any'
        new_slugs['unit-rightasc'] = 'degrees'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Query type "qtype-rightasc" has an illegal value; it has been set to the default.')

    def test__api_normalizeurl_lonely_qtype_used_badval_contains(self):
        "[test_ui_api.py] /__normalizeurl: lonely qtype used badval contains"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=rightasc&qtype-rightasc=contains'
        new_slugs['widgets'] = 'rightasc'
        new_slugs['qtype-rightasc'] = 'any'
        new_slugs['unit-rightasc'] = 'degrees'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Query type "qtype-rightasc" has an illegal value; it has been set to the default.')

    def test__api_normalizeurl_lonely_qtype_used_badval_contains_2(self):
        "[test_ui_api.py] /__normalizeurl: lonely qtype used badval contains _2"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=rightasc&qtype-rightasc_2=contains'
        new_slugs['widgets'] = 'rightasc'
        new_slugs['qtype-rightasc'] = 'any'
        new_slugs['unit-rightasc'] = 'degrees'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Query type "qtype-rightasc_2" has an illegal value; it has been set to the default.')

    def test__api_normalizeurl_lonely_qtype_used_contains(self):
        "[test_ui_api.py] /__normalizeurl: lonely qtype used contains"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=volumeid&qtype-volumeid=contains'
        new_slugs['widgets'] = 'volumeid'
        new_slugs['qtype-volumeid'] = 'contains'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_lonely_qtype_used_matches(self):
        "[test_ui_api.py] /__normalizeurl: lonely qtype used matches"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=volumeid&qtype-volumeid=matches'
        new_slugs['widgets'] = 'volumeid'
        new_slugs['qtype-volumeid'] = 'matches'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_lonely_qtype_used_excludes(self):
        "[test_ui_api.py] /__normalizeurl: lonely qtype used excludes"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=volumeid&qtype-volumeid=excludes'
        new_slugs['widgets'] = 'volumeid'
        new_slugs['qtype-volumeid'] = 'excludes'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_lonely_qtype_used_begins(self):
        "[test_ui_api.py] /__normalizeurl: lonely qtype used begins"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=volumeid&qtype-volumeid=begins'
        new_slugs['widgets'] = 'volumeid'
        new_slugs['qtype-volumeid'] = 'begins'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_lonely_qtype_used_ends(self):
        "[test_ui_api.py] /__normalizeurl: lonely qtype used ends"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=volumeid&qtype-volumeid=ends'
        new_slugs['widgets'] = 'volumeid'
        new_slugs['qtype-volumeid'] = 'ends'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_lonely_qtype_used_string_badval_XXX(self):
        "[test_ui_api.py] /__normalizeurl: lonely qtype used string badval XXX"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=volumeid&qtype-volumeid=XXX'
        new_slugs['widgets'] = 'volumeid'
        new_slugs['qtype-volumeid'] = 'contains'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Query type "qtype-volumeid" has an illegal value; it has been set to the default.')

    def test__api_normalizeurl_lonely_qtype_used_badval_any(self):
        "[test_ui_api.py] /__normalizeurl: lonely qtype used badval any"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=volumeid&qtype-volumeid=any'
        new_slugs['widgets'] = 'volumeid'
        new_slugs['qtype-volumeid'] = 'contains'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Query type "qtype-volumeid" has an illegal value; it has been set to the default.')

    ### Lonely unit - these are units without matching searches or widgets

    def test__api_normalizeurl_lonely_unit_bad_slug(self):
        "[test_ui_api.py] /__normalizeurl: lonely unit bad slug"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?unit-fredethel=km'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Search term "unit-fredethel" is unknown; it has been ignored.')

    def test__api_normalizeurl_lonely_unit_not_used(self):
        "[test_ui_api.py] /__normalizeurl: lonely unit not used"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?unit-rightasc=degrees'
        new_slugs['widgets'] = 'rightasc'
        new_slugs['qtype-rightasc'] = 'any'
        new_slugs['unit-rightasc'] = 'degrees'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_lonely_unit_not_used_not_default(self):
        "[test_ui_api.py] /__normalizeurl: lonely unit not used not default unit"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?unit-observationduration=milliseconds'
        new_slugs['widgets'] = 'observationduration'
        new_slugs['unit-observationduration'] = 'milliseconds'
        self._run_url_slugs_equal(url, new_slugs)

    # Lonely unit - these are units without matching searches but with
    # widgets

    def test__api_normalizeurl_lonely_unit_used_degrees(self):
        "[test_ui_api.py] /__normalizeurl: lonely unit used degrees"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=observationduration&unit-observationduration=seconds'
        new_slugs['widgets'] = 'observationduration'
        new_slugs['unit-observationduration'] = 'seconds'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_lonely_unit_used_any_clause_1_not_default(self):
        "[test_ui_api.py] /__normalizeurl: lonely unit used only _1 not default"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=observationduration&unit-observationduration_1=milliseconds'
        new_slugs['widgets'] = 'observationduration'
        new_slugs['unit-observationduration'] = 'milliseconds'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_lonely_unit_used_any_clause_2_not_default(self):
        "[test_ui_api.py] /__normalizeurl: lonely unit used only _2 not default"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=observationduration&unit-observationduration_2=milliseconds'
        new_slugs['widgets'] = 'observationduration'
        new_slugs['unit-observationduration'] = 'milliseconds'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_lonely_unit_used_any_clause_1_2_not_default(self):
        "[test_ui_api.py] /__normalizeurl: lonely unit used all/only _1_2 not default"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=observationduration&unit-observationduration_1=seconds&unit-observationduration_2=milliseconds'
        new_slugs['widgets'] = 'observationduration'
        new_slugs['unit-observationduration_01'] = 'seconds'
        new_slugs['unit-observationduration_02'] = 'seconds'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='<li>Search term "unit-observationduration_2" is a unit that is inconsistent with the units for previous instances of this search field; it has been ignored.</li>')

    def test__api_normalizeurl_lonely_unit_used_any_clause_10_20(self):
        "[test_ui_api.py] /__normalizeurl: lonely unit used all/only _10_20"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=observationduration&unit-observationduration_10=milliseconds&unit-observationduration_20=seconds'
        new_slugs['widgets'] = 'observationduration'
        new_slugs['unit-observationduration_01'] = 'milliseconds'
        new_slugs['unit-observationduration_02'] = 'milliseconds'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='<li>Search term "unit-observationduration_20" is a unit that is inconsistent with the units for previous instances of this search field; it has been ignored.</li>')

    def test__api_normalizeurl_lonely_unit_used_any_bad(self):
        "[test_ui_api.py] /__normalizeurl: lonely unit used any bad"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=planet&unit-planet=seconds'
        new_slugs['widgets'] = 'planet'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Search term "unit-planet" is a unit for a field that does not allow units; it has been ignored.')

    def test__api_normalizeurl_lonely_unit_used_any_bad_clause(self):
        "[test_ui_api.py] /__normalizeurl: lonely unit used any bad _2"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=volumeid&unit-volumeid_2=seconds'
        new_slugs['widgets'] = 'volumeid'
        new_slugs['qtype-volumeid'] = 'contains'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Search term "unit-volumeid_2" is a unit for a field that does not allow units; it has been ignored.')

    def test__api_normalizeurl_lonely_unit_used_multi_badval_XXX(self):
        "[test_ui_api.py] /__normalizeurl: lonely unit used multi badval XXX"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=observationduration&unit-observationduration=XXX'
        new_slugs['widgets'] = 'observationduration'
        new_slugs['unit-observationduration'] = 'seconds'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Unit "unit-observationduration" has an illegal value; it has been set to the default.')

    ### widgets=

    def test__api_normalizeurl_widgets_empty(self):
        "[test_ui_api.py] /__normalizeurl: widgets empty"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets='
        new_slugs['widgets'] = ''
        self._run_url_slugs_equal(url, new_slugs)

    # Empty widgets

    # Also tests mult widget
    def test__api_normalizeurl_widgets_empty_1(self):
        "[test_ui_api.py] /__normalizeurl: widgets ,instrument"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=,instrument'
        new_slugs['widgets'] = 'instrument'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_widgets_empty_2(self):
        "[test_ui_api.py] /__normalizeurl: widgets instrument,"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=instrument,'
        new_slugs['widgets'] = 'instrument'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_widgets_empty_3(self):
        "[test_ui_api.py] /__normalizeurl: widgets ,,instrument,,"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=,,instrument,,'
        new_slugs['widgets'] = 'instrument'
        self._run_url_slugs_equal(url, new_slugs)

    # Old defaults

    def test__api_normalizeurl_widgets_default(self):
        "[test_ui_api.py] /__normalizeurl: widgets default"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=instrument,observationtype,target'
        new_slugs['widgets'] = settings.DEFAULT_WIDGETS
        self._run_url_slugs_equal(url, new_slugs)

    # Something that has an old_slug

    def test__api_normalizeurl_widgets_ringobsid(self):
        "[test_ui_api.py] /__normalizeurl: widgets ringobsid"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=ringobsid'
        new_slugs['widgets'] = 'opusid'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_widgets_instrument(self):
        "[test_ui_api.py] /__normalizeurl: widgets instrument"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=instrument'
        new_slugs['widgets'] = 'instrument'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_widgets_instrumentid(self):
        "[test_ui_api.py] /__normalizeurl: widgets instrumentid"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=instrumentid'
        new_slugs['widgets'] = 'instrument'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='previous version')

    def test__api_normalizeurl_widgets_instrument_instrument(self):
        "[test_ui_api.py] /__normalizeurl: widgets instrument,instrument"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=instrument,instrument'
        new_slugs['widgets'] = 'instrument'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='duplicated')

    def test__api_normalizeurl_widgets_instrument_instrumentid(self):
        "[test_ui_api.py] /__normalizeurl: widgets instrument,instrumentid"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=instrument,instrumentid'
        new_slugs['widgets'] = 'instrument'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='duplicated')

    def test__api_normalizeurl_widgets_instrumentid_instrument(self):
        "[test_ui_api.py] /__normalizeurl: widgets instrumentid,instrument"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=instrumentid,instrument'
        new_slugs['widgets'] = 'instrument'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='duplicated')

    def test__api_normalizeurl_widgets_instrumentid_instrumentid(self):
        "[test_ui_api.py] /__normalizeurl: widgets instrumentid,instrumentid"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=instrumentid,instrumentid'
        new_slugs['widgets'] = 'instrument'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='duplicated')

    # Something that doesn't have an old slug

    # Also tests string widget
    def test__api_normalizeurl_widgets_productid(self):
        "[test_ui_api.py] /__normalizeurl: widgets productid"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=productid'
        new_slugs['widgets'] = 'productid'
        self._run_url_slugs_equal(url, new_slugs)

    # Bad widgets

    def test__api_normalizeurl_widgets_bad_1(self):
        "[test_ui_api.py] /__normalizeurl: widgets bad 1"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=XXX'
        new_slugs['widgets'] = ''
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Search field "XXX" is unknown')

    def test__api_normalizeurl_widgets_bad_2(self):
        "[test_ui_api.py] /__normalizeurl: widgets bad 2"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=XXX,productid'
        new_slugs['widgets'] = 'productid'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Search field "XXX" is unknown')

    # Not searchable

    def test__api_normalizeurl_widgets_not_searchable(self):
        "[test_ui_api.py] /__normalizeurl: widgets not searchable"
        url = '/__normalizeurl.json?widgets=**previewimages'
        new_slugs = dict(self.default_url_slugs)
        new_slugs['widgets'] = ''
        self._run_url_slugs_equal(url, new_slugs, msg_contains='not searchable')

    # Searched but not in widget list

    def test__api_normalizeurl_widgets_searched_1(self):
        "[test_ui_api.py] /__normalizeurl: widgets searched not widget 1"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?instrument=COISS'
        new_slugs['instrument'] = 'COISS'
        new_slugs['widgets'] = 'instrument'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_widgets_searched_2(self):
        "[test_ui_api.py] /__normalizeurl: widgets searched not widget 2"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?rightasc1=10.'
        new_slugs['qtype-rightasc'] = 'any'
        new_slugs['unit-rightasc'] = 'degrees'
        new_slugs['rightasc1'] = '10'
        new_slugs['widgets'] = 'rightasc'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_widgets_searched_3(self):
        "[test_ui_api.py] /__normalizeurl: widgets searched not widget 3"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?rightasc2=10.'
        new_slugs['qtype-rightasc'] = 'any'
        new_slugs['unit-rightasc'] = 'degrees'
        new_slugs['rightasc2'] = '10'
        new_slugs['widgets'] = 'rightasc'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_widgets_searched_4(self):
        "[test_ui_api.py] /__normalizeurl: widgets searched not widget 4"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?rightasc2=10.&rightasc1=5.'
        new_slugs['qtype-rightasc'] = 'any'
        new_slugs['unit-rightasc'] = 'degrees'
        new_slugs['rightasc1'] = '5'
        new_slugs['rightasc2'] = '10'
        new_slugs['widgets'] = 'rightasc'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_widgets_searched_5(self):
        "[test_ui_api.py] /__normalizeurl: widgets searched not widget 5"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?rightasc2=10.&rightasc1=5.&widgets=instrument'
        new_slugs['qtype-rightasc'] = 'any'
        new_slugs['unit-rightasc'] = 'degrees'
        new_slugs['rightasc1'] = '5'
        new_slugs['rightasc2'] = '10'
        new_slugs['widgets'] = 'instrument,rightasc'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_widgets_searched_clause_1(self):
        "[test_ui_api.py] /__normalizeurl: widgets searched not widget clause"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?rightasc2_20=10.&rightasc1_20=5.&widgets=instrument'
        new_slugs['qtype-rightasc'] = 'any'
        new_slugs['unit-rightasc'] = 'degrees'
        new_slugs['rightasc1'] = '5'
        new_slugs['rightasc2'] = '10'
        new_slugs['widgets'] = 'instrument,rightasc'
        self._run_url_slugs_equal(url, new_slugs)

    # Searched but in widget list

    def test__api_normalizeurl_widgets_searched_6(self):
        "[test_ui_api.py] /__normalizeurl: widgets searched not widget 6"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?instrument=COISS&widgets=instrument'
        new_slugs['instrument'] = 'COISS'
        new_slugs['widgets'] = 'instrument'
        self._run_url_slugs_equal(url, new_slugs)

    # Single-column range with '1' suffix

    def test__api_normalizeurl_widgets_observationduration(self):
        "[test_ui_api.py] /__normalizeurl: widgets observationduration"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=observationduration'
        new_slugs['widgets'] = 'observationduration'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_widgets_observationduration1(self):
        "[test_ui_api.py] /__normalizeurl: widgets observationduration1"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=observationduration1'
        new_slugs['widgets'] = 'observationduration'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='previous version')

    # Multi-column range with '1' suffix

    def test__api_normalizeurl_widgets_rightasc(self):
        "[test_ui_api.py] /__normalizeurl: widgets rightasc"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=rightasc'
        new_slugs['widgets'] = 'rightasc'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_widgets_rightasc1(self):
        "[test_ui_api.py] /__normalizeurl: widgets rightasc1"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=rightasc1'
        new_slugs['widgets'] = 'rightasc'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='previous version')

    ### cols=

    def test__api_normalizeurl_cols_empty(self):
        "[test_ui_api.py] /__normalizeurl: cols empty"
        # It's not OK to have empty columns
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?cols='
        new_slugs['cols'] = settings.DEFAULT_COLUMNS
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Your selected metadata list is empty; it has been replaced with the defaults.')

    # Empty cols

    # Also tests mult field
    def test__api_normalizeurl_cols_empty_1(self):
        "[test_ui_api.py] /__normalizeurl: cols ,instrument"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?cols=,instrument'
        new_slugs['cols'] = 'instrument'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_cols_empty_2(self):
        "[test_ui_api.py] /__normalizeurl: cols instrument,"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?cols=instrument,'
        new_slugs['cols'] = 'instrument'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_cols_empty_3(self):
        "[test_ui_api.py] /__normalizeurl: cols ,,instrument,,"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?cols=,,instrument,,'
        new_slugs['cols'] = 'instrument'
        self._run_url_slugs_equal(url, new_slugs)

    # Old defaults

    def test__api_normalizeurl_cols_default(self):
        "[test_ui_api.py] /__normalizeurl: cols default"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?cols=ringobsid,planet,target,phase1,phase2,time1,time2'
        new_slugs['cols'] = settings.DEFAULT_COLUMNS
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Your URL uses the old defaults for selected metadata; they have been replaced with the new defaults.')

    # Something that has an old_slug

    def test__api_normalizeurl_cols_instrument(self):
        "[test_ui_api.py] /__normalizeurl: cols instrument"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?cols=instrument'
        new_slugs['cols'] = 'instrument'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_cols_instrumentid(self):
        "[test_ui_api.py] /__normalizeurl: cols instrumentid"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?cols=instrumentid'
        new_slugs['cols'] = 'instrument'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='previous version')

    def test__api_normalizeurl_cols_instrument_instrument(self):
        "[test_ui_api.py] /__normalizeurl: cols instrument,instrument"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?cols=instrument,instrument'
        new_slugs['cols'] = 'instrument'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Selected metadata field "Instrument Name" is duplicated in the list of selected metadata; only one copy is being used.')

    def test__api_normalizeurl_cols_instrument_instrumentid(self):
        "[test_ui_api.py] /__normalizeurl: cols instrument,instrumentid"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?cols=instrument,instrumentid'
        new_slugs['cols'] = 'instrument'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Selected metadata field "Instrument Name" is duplicated in the list of selected metadata; only one copy is being used.')

    def test__api_normalizeurl_cols_instrumentid_instrument(self):
        "[test_ui_api.py] /__normalizeurl: cols instrumentid,instrument"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?cols=instrumentid,instrument'
        new_slugs['cols'] = 'instrument'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Selected metadata field "Instrument Name" is duplicated in the list of selected metadata; only one copy is being used.')

    def test__api_normalizeurl_cols_instrumentid_instrumentid(self):
        "[test_ui_api.py] /__normalizeurl: cols instrumentid,instrumentid"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?cols=instrumentid,instrumentid'
        new_slugs['cols'] = 'instrument'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Selected metadata field "Instrument Name" is duplicated in the list of selected metadata; only one copy is being used.')

    def test__api_normalizeurl_cols_time1_time1_units_1(self):
        "[test_ui_api.py] /__normalizeurl: cols time1,time1:jd"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?cols=time1,time1:jd'
        new_slugs['cols'] = 'time1'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Selected metadata field "Observation Start Time" is duplicated in the list of selected metadata; only one copy is being used.')

    # Something that doesn't have an old slug

    # Also tests string field
    def test__api_normalizeurl_cols_productid(self):
        "[test_ui_api.py] /__normalizeurl: cols productid"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?cols=productid'
        new_slugs['cols'] = 'productid'
        self._run_url_slugs_equal(url, new_slugs)

    # Bad cols

    def test__api_normalizeurl_cols_bad_1(self):
        "[test_ui_api.py] /__normalizeurl: cols bad 1"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?cols=XXX'
        new_slugs['cols'] = settings.DEFAULT_COLUMNS
        self._run_url_slugs_equal(url, new_slugs, msg_contains='><li>Selected metadata field "XXX" is unknown; it has been removed.</li><li>Your new selected metadata list is empty; it has been replaced with the defaults.</li>')

    def test__api_normalizeurl_cols_bad_2(self):
        "[test_ui_api.py] /__normalizeurl: cols bad 2"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?cols=XXX,productid'
        new_slugs['cols'] = 'productid'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Selected metadata field "XXX" is unknown; it has been removed.')

    # Good units

    def test__api_normalizeurl_cols_units_good_1(self):
        "[test_ui_api.py] /__normalizeurl: cols units good 1"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?cols=time1:YMDHMS,time2:Et,observationduration'
        new_slugs['cols'] = 'time1:ymdhms,time2:et,observationduration'
        self._run_url_slugs_equal(url, new_slugs)

    # Bad units

    def test__api_normalizeurl_cols_units_bad_1(self):
        "[test_ui_api.py] /__normalizeurl: cols units bad 1"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?cols=instrument:seconds'
        new_slugs['cols'] = 'instrument'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='><li>Selected metadata field "Instrument Name" has invalid units "seconds"; units have been removed.</li>')

    def test__api_normalizeurl_cols_units_bad_2(self):
        "[test_ui_api.py] /__normalizeurl: cols units bad 2"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?cols=time2:hours'
        new_slugs['cols'] = 'time2'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='><li>Selected metadata field "Observation Stop Time" has invalid units "hours"; units have been removed.</li>')

    # Not viewable

    def test__api_normalizeurl_cols_ringobsid(self):
        "[test_ui_api.py] /__normalizeurl: cols ringobsid"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?cols=ringobsid'
        new_slugs['cols'] = 'opusid'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_cols_not_viewable(self):
        "[test_ui_api.py] /__normalizeurl: cols not viewable"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?cols=**filespec'
        new_slugs['cols'] = settings.DEFAULT_COLUMNS
        self._run_url_slugs_equal(url, new_slugs, msg_contains='<li>Selected metadata field "**filespec" is not displayable; it has been removed.</li><li>Your new selected metadata list is empty; it has been replaced with the defaults.</li>')

    # Single-column range with '1' suffix

    def test__api_normalizeurl_cols_observationduration(self):
        "[test_ui_api.py] /__normalizeurl: cols observationduration"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?cols=observationduration'
        new_slugs['cols'] = 'observationduration'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_cols_observationduration_units(self):
        "[test_ui_api.py] /__normalizeurl: cols observationduration units"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?cols=observationduration:microseconds'
        new_slugs['cols'] = 'observationduration:microseconds'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_cols_observationduration1(self):
        "[test_ui_api.py] /__normalizeurl: cols observationduration1"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?cols=observationduration1'
        new_slugs['cols'] = 'observationduration'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='previous version')

    # Multi-column range with '1' suffix

    def test__api_normalizeurl_cols_rightasc(self):
        "[test_ui_api.py] /__normalizeurl: cols rightasc"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?cols=rightasc'
        new_slugs['cols'] = settings.DEFAULT_COLUMNS
        self._run_url_slugs_equal(url, new_slugs, msg_contains='<li>Selected metadata field "rightasc" is unknown; it has been removed.</li><li>Your new selected metadata list is empty; it has been replaced with the defaults.</li>')

    def test__api_normalizeurl_cols_rightasc1(self):
        "[test_ui_api.py] /__normalizeurl: cols rightasc1"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?cols=rightasc1'
        new_slugs['cols'] = 'rightasc1'
        self._run_url_slugs_equal(url, new_slugs)

    ### order=

    def test__api_normalizeurl_order_empty(self):
        "[test_ui_api.py] /__normalizeurl: order empty"
        # It's not OK to have empty columns
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?order='
        new_slugs['order'] = settings.DEFAULT_SORT_ORDER
        self._run_url_slugs_equal(url, new_slugs, msg_contains='The "order" field is empty; it has been set to the default.')

    # Empty order

    def test__api_normalizeurl_order_empty_1(self):
        "[test_ui_api.py] /__normalizeurl: order ,instrument"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?order=,instrument'
        new_slugs['order'] = 'instrument,opusid'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_order_empty_2(self):
        "[test_ui_api.py] /__normalizeurl: order instrument,"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?order=instrument,'
        new_slugs['order'] = 'instrument,opusid'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_order_empty_3(self):
        "[test_ui_api.py] /__normalizeurl: order ,,instrument,,"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?order=,,instrument,,'
        new_slugs['order'] = 'instrument,opusid'
        self._run_url_slugs_equal(url, new_slugs)

    # OPUS ID not last
    def test__api_normalizeurl_order_opusid_not_last_1(self):
        "[test_ui_api.py] /__normalizeurl: order opusid,instrument"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?order=opusid,instrument'
        new_slugs['order'] = 'opusid'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='We found the following issues with your bookmarked URL:</p><ul><li>Fields after "opusid" in the sort order have been removed.</li></ul><p>We strongly recommend that you replace your old bookmark with the updated URL in your browser so that you will not see this message in the future.')

    def test__api_normalizeurl_order_opusid_not_last_2(self):
        "[test_ui_api.py] /__normalizeurl: order opusid,instrument,time"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?order=opusid,instrument,time'
        new_slugs['order'] = 'opusid'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='We found the following issues with your bookmarked URL:</p><ul><li>Fields after "opusid" in the sort order have been removed.</li></ul><p>We strongly recommend that you replace your old bookmark with the updated URL in your browser so that you will not see this message in the future.')

    def test__api_normalizeurl_order_opusid_not_last_3(self):
        "[test_ui_api.py] /__normalizeurl: order instrument,opusid,time"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?order=instrument,opusid,time'
        new_slugs['order'] = 'instrument,opusid'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='We found the following issues with your bookmarked URL:</p><ul><li>Fields after "opusid" in the sort order have been removed.</li></ul><p>We strongly recommend that you replace your old bookmark with the updated URL in your browser so that you will not see this message in the future.')

    def test__api_normalizeurl_order_opusid_dec_not_last_1(self):
        "[test_ui_api.py] /__normalizeurl: order -opusid,instrument"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?order=-opusid,instrument'
        new_slugs['order'] = '-opusid'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='We found the following issues with your bookmarked URL:</p><ul><li>Fields after "opusid" in the sort order have been removed.</li></ul><p>We strongly recommend that you replace your old bookmark with the updated URL in your browser so that you will not see this message in the future.')

    def test__api_normalizeurl_order_opusid_dec_not_last_2(self):
        "[test_ui_api.py] /__normalizeurl: order -opusid,instrument,time"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?order=-opusid,instrument,time'
        new_slugs['order'] = '-opusid'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='We found the following issues with your bookmarked URL:</p><ul><li>Fields after "opusid" in the sort order have been removed.</li></ul><p>We strongly recommend that you replace your old bookmark with the updated URL in your browser so that you will not see this message in the future.')

    def test__api_normalizeurl_order_opusid_dec_not_last_3(self):
        "[test_ui_api.py] /__normalizeurl: order instrument,-opusid,time"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?order=instrument,-opusid,time'
        new_slugs['order'] = 'instrument,-opusid'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='We found the following issues with your bookmarked URL:</p><ul><li>Fields after "opusid" in the sort order have been removed.</li></ul><p>We strongly recommend that you replace your old bookmark with the updated URL in your browser so that you will not see this message in the future.')

    # Old defaults

    def test__api_normalizeurl_order_default(self):
        "[test_ui_api.py] /__normalizeurl: order default"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?order=time1'
        new_slugs['order'] = settings.DEFAULT_SORT_ORDER
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_order_default_2(self):
        "[test_ui_api.py] /__normalizeurl: order default 2"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?order=-time1'
        new_slugs['order'] = '-time1,opusid'
        self._run_url_slugs_equal(url, new_slugs)

    # Something that has an old_slug

    def test__api_normalizeurl_order_instrument(self):
        "[test_ui_api.py] /__normalizeurl: order instrument"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?order=instrument'
        new_slugs['order'] = 'instrument,opusid'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_order_instrumentid(self):
        "[test_ui_api.py] /__normalizeurl: order instrumentid"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?order=instrumentid'
        new_slugs['order'] = 'instrument,opusid'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='previous version')

    def test__api_normalizeurl_order_instrument_instrument(self):
        "[test_ui_api.py] /__normalizeurl: order instrument,instrument"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?order=instrument,instrument'
        new_slugs['order'] = 'instrument,opusid'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Sort order metadata field "Instrument Name" is duplicated in the list of sort orders; only one copy is being used.')

    def test__api_normalizeurl_order_instrument_instrumentid(self):
        "[test_ui_api.py] /__normalizeurl: order instrument,instrumentid"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?order=instrument,instrumentid'
        new_slugs['order'] = 'instrument,opusid'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Sort order metadata field "Instrument Name" is duplicated in the list of sort orders; only one copy is being used.')

    def test__api_normalizeurl_order_instrumentid_instrument(self):
        "[test_ui_api.py] /__normalizeurl: order instrumentid,instrument"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?order=instrumentid,instrument'
        new_slugs['order'] = 'instrument,opusid'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Sort order metadata field "Instrument Name" is duplicated in the list of sort orders; only one copy is being used.')

    def test__api_normalizeurl_order_instrumentid_instrument_2(self):
        "[test_ui_api.py] /__normalizeurl: order instrumentid,instrument 2"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?order=instrumentid,-instrument'
        new_slugs['order'] = 'instrument,opusid'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Sort order metadata field "Instrument Name" is duplicated in the list of sort orders; only one copy is being used.')

    def test__api_normalizeurl_order_instrumentid_instrument_3(self):
        "[test_ui_api.py] /__normalizeurl: order instrumentid,instrument 3"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?order=-instrumentid,instrument'
        new_slugs['order'] = '-instrument,opusid'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Sort order metadata field "Instrument Name" is duplicated in the list of sort orders; only one copy is being used.')

    def test__api_normalizeurl_order_instrumentid_instrumentid(self):
        "[test_ui_api.py] /__normalizeurl: order instrumentid,instrumentid"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?order=instrumentid,instrumentid'
        new_slugs['order'] = 'instrument,opusid'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Sort order metadata field "Instrument Name" is duplicated in the list of sort orders; only one copy is being used.')

    # Something that doesn't have an old slug

    def test__api_normalizeurl_order_productid(self):
        "[test_ui_api.py] /__normalizeurl: order productid"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?order=productid'
        new_slugs['order'] = 'productid,opusid'
        self._run_url_slugs_equal(url, new_slugs)

    # Bad order

    def test__api_normalizeurl_order_bad_1(self):
        "[test_ui_api.py] /__normalizeurl: order bad 1"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?order=XXX'
        new_slugs['order'] = settings.DEFAULT_SORT_ORDER
        self._run_url_slugs_equal(url, new_slugs, msg_contains='<li>Sort order metadata field "XXX" is unknown; it has been removed.</li><li>The "order" field is empty; it has been set to the default.</li>')

    def test__api_normalizeurl_order_bad_2(self):
        "[test_ui_api.py] /__normalizeurl: order bad 2"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?order=XXX,productid'
        new_slugs['order'] = 'productid,opusid'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Sort order metadata field "XXX" is unknown; it has been removed.')

    # Not viewable

    def test__api_normalizeurl_order_ringobsid(self):
        "[test_ui_api.py] /__normalizeurl: order ringobsid"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?order=ringobsid'
        new_slugs['order'] = 'opusid'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_order_not_viewable(self):
        "[test_ui_api.py] /__normalizeurl: order not viewable"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?order=**filespec'
        new_slugs['order'] = settings.DEFAULT_SORT_ORDER
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Sort order metadata field "**filespec" is not displayable; it has been removed.')

    # Single-column range with '1' suffix

    def test__api_normalizeurl_order_observationduration(self):
        "[test_ui_api.py] /__normalizeurl: order observationduration"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?order=observationduration'
        new_slugs['order'] = 'observationduration,opusid'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_order_observationduration1(self):
        "[test_ui_api.py] /__normalizeurl: order observationduration1"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?order=observationduration1'
        new_slugs['order'] = 'observationduration,opusid'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='previous version')

    # Multi-column range with '1' suffix

    def test__api_normalizeurl_order_rightasc(self):
        "[test_ui_api.py] /__normalizeurl: order rightasc"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?order=rightasc'
        new_slugs['order'] = settings.DEFAULT_SORT_ORDER
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Sort order metadata field "rightasc" is unknown; it has been removed.')

    def test__api_normalizeurl_order_rightasc1(self):
        "[test_ui_api.py] /__normalizeurl: order rightasc1"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?order=rightasc1'
        new_slugs['order'] = 'rightasc1,opusid'
        self._run_url_slugs_equal(url, new_slugs)

    ### Search slugs

    # Multi-column ranges

    def test__api_normalizeurl_search_multi_empty(self):
        "[test_ui_api.py] /__normalizeurl: search multi empty"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=rightasc&rightasc1='
        new_slugs['rightasc1'] = ''
        new_slugs['qtype-rightasc'] = 'any'
        new_slugs['unit-rightasc'] = 'degrees'
        new_slugs['widgets'] = 'rightasc'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_multi_good_1(self):
        "[test_ui_api.py] /__normalizeurl: search multi good 1"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=rightasc&rightasc1=10.'
        new_slugs['rightasc1'] = '10'
        new_slugs['qtype-rightasc'] = 'any'
        new_slugs['unit-rightasc'] = 'degrees'
        new_slugs['widgets'] = 'rightasc'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_multi_good_2(self):
        "[test_ui_api.py] /__normalizeurl: search multi good 2"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=rightasc&rightasc2=10.'
        new_slugs['rightasc2'] = '10'
        new_slugs['qtype-rightasc'] = 'any'
        new_slugs['unit-rightasc'] = 'degrees'
        new_slugs['widgets'] = 'rightasc'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_multi_good_12(self):
        "[test_ui_api.py] /__normalizeurl: search multi good 12"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=rightasc&rightasc1=10.&rightasc2=20.'
        new_slugs['rightasc1'] = '10'
        new_slugs['rightasc2'] = '20'
        new_slugs['qtype-rightasc'] = 'any'
        new_slugs['unit-rightasc'] = 'degrees'
        new_slugs['widgets'] = 'rightasc'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_multi_good_1_qtype_only(self):
        "[test_ui_api.py] /__normalizeurl: search multi good 1 qtype only"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=rightasc&rightasc1=10.&qtype-rightasc=only'
        new_slugs['rightasc1'] = '10'
        new_slugs['qtype-rightasc'] = 'only'
        new_slugs['unit-rightasc'] = 'degrees'
        new_slugs['widgets'] = 'rightasc'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_multi_good_1_qtype_bad(self):
        "[test_ui_api.py] /__normalizeurl: search multi good 1 qtype bad"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=rightasc&rightasc1=10.&qtype-rightasc=XXX'
        new_slugs['rightasc1'] = '10'
        new_slugs['qtype-rightasc'] = 'any'
        new_slugs['unit-rightasc'] = 'degrees'
        new_slugs['widgets'] = 'rightasc'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Query type "qtype-rightasc" has an illegal value; it has been set to the default.')

    def test__api_normalizeurl_search_multi_good_2_qtype_all(self):
        "[test_ui_api.py] /__normalizeurl: search multi good 2 qtype all"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=rightasc&rightasc2=10.&qtype-rightasc=all'
        new_slugs['rightasc2'] = '10'
        new_slugs['qtype-rightasc'] = 'all'
        new_slugs['unit-rightasc'] = 'degrees'
        new_slugs['widgets'] = 'rightasc'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_multi_good_12_qtype_any(self):
        "[test_ui_api.py] /__normalizeurl: search multi good 12 qtype any"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=rightasc&rightasc1=10.&rightasc2=20.&qtype-rightasc=any'
        new_slugs['rightasc1'] = '10'
        new_slugs['rightasc2'] = '20'
        new_slugs['qtype-rightasc'] = 'any'
        new_slugs['unit-rightasc'] = 'degrees'
        new_slugs['widgets'] = 'rightasc'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_multi_good_12_qtype_only(self):
        "[test_ui_api.py] /__normalizeurl: search multi good 12 qtype only"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=rightasc&rightasc1=10.&rightasc2=20.&qtype-rightasc=only'
        new_slugs['rightasc1'] = '10'
        new_slugs['rightasc2'] = '20'
        new_slugs['qtype-rightasc'] = 'only'
        new_slugs['unit-rightasc'] = 'degrees'
        new_slugs['widgets'] = 'rightasc'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_multi_good_1_clause_1(self):
        "[test_ui_api.py] /__normalizeurl: search multi good 1 _1"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=rightasc&rightasc1_1=10.'
        new_slugs['rightasc1'] = '10'
        new_slugs['qtype-rightasc'] = 'any'
        new_slugs['unit-rightasc'] = 'degrees'
        new_slugs['widgets'] = 'rightasc'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_multi_good_1_clause_2(self):
        "[test_ui_api.py] /__normalizeurl: search multi good 1 _2"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=rightasc&rightasc1_2=10.'
        new_slugs['rightasc1'] = '10'
        new_slugs['qtype-rightasc'] = 'any'
        new_slugs['unit-rightasc'] = 'degrees'
        new_slugs['widgets'] = 'rightasc'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_multi_good_1_clause_1_2(self):
        "[test_ui_api.py] /__normalizeurl: search multi good 1 _1_2"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=rightasc&rightasc1_2=10.&rightasc1_1=20.'
        new_slugs['rightasc1_01'] = '20'
        new_slugs['rightasc1_02'] = '10'
        new_slugs['qtype-rightasc_01'] = 'any'
        new_slugs['qtype-rightasc_02'] = 'any'
        new_slugs['unit-rightasc_01'] = 'degrees'
        new_slugs['unit-rightasc_02'] = 'degrees'
        new_slugs['widgets'] = 'rightasc'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_multi_good_1_clause_10_20(self):
        "[test_ui_api.py] /__normalizeurl: search multi good 1 _10_20"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=rightasc&rightasc1_20=10.&rightasc1_10=20.'
        new_slugs['rightasc1_01'] = '20'
        new_slugs['rightasc1_02'] = '10'
        new_slugs['qtype-rightasc_01'] = 'any'
        new_slugs['qtype-rightasc_02'] = 'any'
        new_slugs['unit-rightasc_01'] = 'degrees'
        new_slugs['unit-rightasc_02'] = 'degrees'
        new_slugs['widgets'] = 'rightasc'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_multi_good_2_clause_1(self):
        "[test_ui_api.py] /__normalizeurl: search multi good 2 _1"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=rightasc&rightasc2_1=10.'
        new_slugs['rightasc2'] = '10'
        new_slugs['qtype-rightasc'] = 'any'
        new_slugs['unit-rightasc'] = 'degrees'
        new_slugs['widgets'] = 'rightasc'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_multi_good_2_clause_2(self):
        "[test_ui_api.py] /__normalizeurl: search multi good 2 _2"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=rightasc&rightasc2_2=10.'
        new_slugs['rightasc2'] = '10'
        new_slugs['qtype-rightasc'] = 'any'
        new_slugs['unit-rightasc'] = 'degrees'
        new_slugs['widgets'] = 'rightasc'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_multi_good_2_clause_1_2(self):
        "[test_ui_api.py] /__normalizeurl: search multi good 2 _1_2"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=rightasc&rightasc2_2=10.&rightasc2_1=20.'
        new_slugs['rightasc2_01'] = '20'
        new_slugs['rightasc2_02'] = '10'
        new_slugs['qtype-rightasc_01'] = 'any'
        new_slugs['qtype-rightasc_02'] = 'any'
        new_slugs['unit-rightasc_01'] = 'degrees'
        new_slugs['unit-rightasc_02'] = 'degrees'
        new_slugs['widgets'] = 'rightasc'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_multi_good_2_clause_10_20(self):
        "[test_ui_api.py] /__normalizeurl: search multi good 2 _10_20"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=rightasc&rightasc2_20=10.&rightasc2_10=20.'
        new_slugs['rightasc2_01'] = '20'
        new_slugs['rightasc2_02'] = '10'
        new_slugs['qtype-rightasc_01'] = 'any'
        new_slugs['qtype-rightasc_02'] = 'any'
        new_slugs['unit-rightasc_01'] = 'degrees'
        new_slugs['unit-rightasc_02'] = 'degrees'
        new_slugs['widgets'] = 'rightasc'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_multi_good_12_clause_01(self):
        "[test_ui_api.py] /__normalizeurl: search multi good 12 _01"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=rightasc&rightasc1_01=10.&rightasc2_01=20.'
        new_slugs['rightasc1'] = '10'
        new_slugs['rightasc2'] = '20'
        new_slugs['qtype-rightasc'] = 'any'
        new_slugs['unit-rightasc'] = 'degrees'
        new_slugs['widgets'] = 'rightasc'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_multi_good_12_clause_01_1(self):
        "[test_ui_api.py] /__normalizeurl: search multi good 12 _01_1"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=rightasc&rightasc1_01=10.&rightasc2_1=20.'
        new_slugs['rightasc1_01'] = '10'
        new_slugs['rightasc2_02'] = '20'
        new_slugs['qtype-rightasc_01'] = 'any'
        new_slugs['qtype-rightasc_02'] = 'any'
        new_slugs['unit-rightasc_01'] = 'degrees'
        new_slugs['unit-rightasc_02'] = 'degrees'
        new_slugs['widgets'] = 'rightasc'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_multi_good_1_clause_bad_0(self):
        "[test_ui_api.py] /__normalizeurl: search multi bad 1 _0"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=rightasc&rightasc1_0=10.'
        new_slugs['widgets'] = 'rightasc'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Search term "rightasc1_0" is unknown; it has been ignored.')

    def test__api_normalizeurl_search_multi_good_1_clause_bad_n1(self):
        "[test_ui_api.py] /__normalizeurl: search multi bad 1 -1"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=rightasc&rightasc1_-1=10.'
        new_slugs['widgets'] = 'rightasc'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Search term "rightasc1_-1" is unknown; it has been ignored.')

    def test__api_normalizeurl_search_multi_good_1_clause_bad_XXX(self):
        "[test_ui_api.py] /__normalizeurl: search multi bad 1 _XXX"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=rightasc&rightasc1_XXX=10.'
        new_slugs['widgets'] = 'rightasc'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Search term "rightasc1_XXX" is unknown; it has been ignored.')

    def test__api_normalizeurl_search_multi_good_12_clause_01_XXX(self):
        "[test_ui_api.py] /__normalizeurl: search multi good 12 _01_XXX"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=rightasc&rightasc1_01=10.&rightasc2_XXX=20.'
        new_slugs['rightasc1'] = '10'
        new_slugs['qtype-rightasc'] = 'any'
        new_slugs['unit-rightasc'] = 'degrees'
        new_slugs['widgets'] = 'rightasc'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Search term "rightasc2_XXX" is unknown; it has been ignored.')

    def test__api_normalizeurl_search_multi_good_12_clause_XXX_01(self):
        "[test_ui_api.py] /__normalizeurl: search multi good 12 _XXX_01"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=rightasc&rightasc1_XXX=10.&rightasc2_01=20.'
        new_slugs['rightasc2'] = '20'
        new_slugs['qtype-rightasc'] = 'any'
        new_slugs['unit-rightasc'] = 'degrees'
        new_slugs['widgets'] = 'rightasc'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Search term "rightasc1_XXX" is unknown; it has been ignored.')

    def test__api_normalizeurl_search_multi_good_12_clause_1_01_XXX_qtypes(self):
        "[test_ui_api.py] /__normalizeurl: search multi good 12 _1_01_XXX qtypes"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=rightasc&rightasc1_1=10.&rightasc2_01=20.&qtype-rightasc_1=only&qtype-rightasc_XXX=only'
        new_slugs['rightasc2_01'] = '20'
        new_slugs['rightasc1_02'] = '10'
        new_slugs['qtype-rightasc_01'] = 'any'
        new_slugs['qtype-rightasc_02'] = 'only'
        new_slugs['unit-rightasc_01'] = 'degrees'
        new_slugs['unit-rightasc_02'] = 'degrees'
        new_slugs['widgets'] = 'rightasc'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Search term "qtype-rightasc_XXX" is unknown; it has been ignored.')

    def test__api_normalizeurl_search_multi_good_12_clause_1_02_XXX_qtypes(self):
        "[test_ui_api.py] /__normalizeurl: search multi good 12 _1_02_XXX qtypes"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=rightasc&rightasc1_1=10.&rightasc2_02=20.&qtype-rightasc_1=only&qtype-rightasc_XXX=only'
        new_slugs['rightasc1_01'] = '10'
        new_slugs['rightasc2_02'] = '20'
        new_slugs['qtype-rightasc_01'] = 'only'
        new_slugs['qtype-rightasc_02'] = 'any'
        new_slugs['unit-rightasc_01'] = 'degrees'
        new_slugs['unit-rightasc_02'] = 'degrees'
        new_slugs['widgets'] = 'rightasc'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Search term "qtype-rightasc_XXX" is unknown; it has been ignored.')

    def test__api_normalizeurl_search_SURFACEGEO_good_1_clause_bad_0(self):
        "[test_ui_api.py] /__normalizeurl: search SURFACEGEO good 1 bad _0"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?surfacegeometrytargetname=Pan&SURFACEGEOpan_planetographiclatitude1_0=8'
        new_slugs['surfacegeometrytargetname'] = 'Pan'
        new_slugs['widgets'] = 'surfacegeometrytargetname'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Search term "SURFACEGEOpan_planetographiclatitude1_0" is unknown; it has been ignored.')

    def test__api_normalizeurl_search_SURFACEGEO_good_1_clause_bad_XXX(self):
        "[test_ui_api.py] /__normalizeurl: search SURFACEGEO good 1 bad _XXX"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?surfacegeometrytargetname=Pan&SURFACEGEOpan_planetographiclatitude1_XXX=8'
        new_slugs['surfacegeometrytargetname'] = 'Pan'
        new_slugs['widgets'] = 'surfacegeometrytargetname'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Search term "SURFACEGEOpan_planetographiclatitude1_XXX" is unknown; it has been ignored.')

    def test__api_normalizeurl_search_SURFACEGEO_good_12_clause_01_XXX(self):
        "[test_ui_api.py] /__normalizeurl: search SURFACEGEO good 12 bad _01_XXX"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?surfacegeometrytargetname=Pan&SURFACEGEOpan_planetographiclatitude1_01=8&SURFACEGEOpan_planetographiclatitude2_XXX=18'
        new_slugs['surfacegeometrytargetname'] = 'Pan'
        new_slugs['SURFACEGEOpan_planetographiclatitude1'] = '8'
        new_slugs['qtype-SURFACEGEOpan_planetographiclatitude'] = 'any'
        new_slugs['unit-SURFACEGEOpan_planetographiclatitude'] = 'degrees'
        new_slugs['widgets'] = 'SURFACEGEOpan_planetographiclatitude,surfacegeometrytargetname'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Search term "SURFACEGEOpan_planetographiclatitude2_XXX" is unknown; it has been ignored.')

    def test__api_normalizeurl_search_SURFACEGEO_good_1_clause_10(self):
        "[test_ui_api.py] /__normalizeurl: search SURFACEGEO good 1 _10"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?surfacegeometrytargetname=Pan&SURFACEGEOpan_planetographiclatitude1_10=8'
        new_slugs['surfacegeometrytargetname'] = 'Pan'
        new_slugs['SURFACEGEOpan_planetographiclatitude1'] = '8'
        new_slugs['qtype-SURFACEGEOpan_planetographiclatitude'] = 'any'
        new_slugs['unit-SURFACEGEOpan_planetographiclatitude'] = 'degrees'
        new_slugs['widgets'] = 'SURFACEGEOpan_planetographiclatitude,surfacegeometrytargetname'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_SURFACEGEO_good_1_clause_01_1(self):
        "[test_ui_api.py] /__normalizeurl: search SURFACEGEO good 1 _01_1"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?surfacegeometrytargetname=Pan&SURFACEGEOpan_planetographiclatitude1_01=8&SURFACEGEOpan_planetographiclatitude1_1=18'
        new_slugs['surfacegeometrytargetname'] = 'Pan'
        new_slugs['SURFACEGEOpan_planetographiclatitude1_01'] = '8'
        new_slugs['SURFACEGEOpan_planetographiclatitude1_02'] = '18'
        new_slugs['qtype-SURFACEGEOpan_planetographiclatitude_01'] = 'any'
        new_slugs['qtype-SURFACEGEOpan_planetographiclatitude_02'] = 'any'
        new_slugs['unit-SURFACEGEOpan_planetographiclatitude_01'] = 'degrees'
        new_slugs['unit-SURFACEGEOpan_planetographiclatitude_02'] = 'degrees'
        new_slugs['widgets'] = 'SURFACEGEOpan_planetographiclatitude,surfacegeometrytargetname'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_SURFACEGEO_good_12_clause_1_02_XXX_qtypes(self):
        "[test_ui_api.py] /__normalizeurl: search SURFACEGEO good 12 _1_02_XXX qtypes"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?surfacegeometrytargetname=Pan&SURFACEGEOpan_planetographiclatitude1_1=8&SURFACEGEOpan_planetographiclatitude2_02=18&qtype-SURFACEGEOpan_planetographiclatitude_1=only&qtype-SURFACEGEOpan_planetographiclatitude_XXX=only'
        new_slugs['surfacegeometrytargetname'] = 'Pan'
        new_slugs['SURFACEGEOpan_planetographiclatitude1_01'] = '8'
        new_slugs['SURFACEGEOpan_planetographiclatitude2_02'] = '18'
        new_slugs['qtype-SURFACEGEOpan_planetographiclatitude_01'] = 'only'
        new_slugs['qtype-SURFACEGEOpan_planetographiclatitude_02'] = 'any'
        new_slugs['unit-SURFACEGEOpan_planetographiclatitude_01'] = 'degrees'
        new_slugs['unit-SURFACEGEOpan_planetographiclatitude_02'] = 'degrees'
        new_slugs['widgets'] = 'SURFACEGEOpan_planetographiclatitude,surfacegeometrytargetname'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Search term "qtype-SURFACEGEOpan_planetographiclatitude_XXX" is unknown; it has been ignored.')

    def test__api_normalizeurl_search_SURFACEGEO_good_12_clause_1_02_XXX_units(self):
        "[test_ui_api.py] /__normalizeurl: search SURFACEGEO good 12 _1_02_XXX unit"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?surfacegeometrytargetname=Pan&SURFACEGEOpan_planetographiclatitude1_1=8&SURFACEGEOpan_planetographiclatitude2_02=18&unit-SURFACEGEOpan_planetographiclatitude_1=degrees&unit-SURFACEGEOpan_planetographiclatitude_XXX=degrees'
        new_slugs['surfacegeometrytargetname'] = 'Pan'
        new_slugs['SURFACEGEOpan_planetographiclatitude1_01'] = '8'
        new_slugs['SURFACEGEOpan_planetographiclatitude2_02'] = '18'
        new_slugs['qtype-SURFACEGEOpan_planetographiclatitude_01'] = 'any'
        new_slugs['qtype-SURFACEGEOpan_planetographiclatitude_02'] = 'any'
        new_slugs['unit-SURFACEGEOpan_planetographiclatitude_01'] = 'degrees'
        new_slugs['unit-SURFACEGEOpan_planetographiclatitude_02'] = 'degrees'
        new_slugs['widgets'] = 'SURFACEGEOpan_planetographiclatitude,surfacegeometrytargetname'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Search term "unit-SURFACEGEOpan_planetographiclatitude_XXX" is unknown; it has been ignored.')

    def test__api_normalizeurl_search_multi_complicated_clause(self):
        "[test_ui_api.py] /__normalizeurl: search multi good complicated clause"
        new_slugs = dict(self.default_url_slugs)
        # _0 is bad
        # No clause is 10
        # _01 is 21/11
        # _1 is 12
        # _12 is 22
        # qtype_20 is None
        url = '/__normalizeurl.json?widgets=rightasc&rightasc1_0=10.&rightasc2_0=20.&qtype-rightasc_0=only&rightasc1=10.&rightasc1_01=21.&rightasc2_01=11.&rightasc2_1=12.&qtype-rightasc_1=only&rightasc1_12=22.&qtype-rightasc_20=all'
        new_slugs['rightasc1_01'] = '10'
        new_slugs['rightasc1_02'] = '21'
        new_slugs['rightasc2_02'] = '11'
        new_slugs['rightasc2_03'] = '12'
        new_slugs['rightasc1_04'] = '22'
        new_slugs['qtype-rightasc_01'] = 'any'
        new_slugs['qtype-rightasc_02'] = 'any'
        new_slugs['qtype-rightasc_03'] = 'only'
        new_slugs['qtype-rightasc_04'] = 'any'
        new_slugs['qtype-rightasc_05'] = 'all'
        new_slugs['unit-rightasc_01'] = 'degrees'
        new_slugs['unit-rightasc_02'] = 'degrees'
        new_slugs['unit-rightasc_03'] = 'degrees'
        new_slugs['unit-rightasc_04'] = 'degrees'
        new_slugs['unit-rightasc_05'] = 'degrees'
        new_slugs['widgets'] = 'rightasc'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='<li>Search term "qtype-rightasc_0" is unknown; it has been ignored.</li><li>Search term "rightasc1_0" is unknown; it has been ignored.</li><li>Search term "rightasc2_0" is unknown; it has been ignored.</li>')

    def test__api_normalizeurl_search_multi_complicated_clause_2(self):
        "[test_ui_api.py] /__normalizeurl: search multi good complicated clause 2"
        new_slugs = dict(self.default_url_slugs)
        # No clause is 10
        # _01 is 21/11
        # _1 is 12
        # _12 is 22
        # qtype_20 is None
        url = '/__normalizeurl.json?widgets=rightasc&rightasc1_01=21.&rightasc2_01=11.&rightasc2_02=12.&qtype-rightasc_02=only&rightasc1_12=22.&qtype-rightasc_20=all&unit-rightasc_01=radians&unit-rightasc_20=fred'
        new_slugs['rightasc1_01'] = '21'
        new_slugs['rightasc2_01'] = '11'
        new_slugs['rightasc2_02'] = '12'
        new_slugs['rightasc1_03'] = '22'
        new_slugs['qtype-rightasc_01'] = 'any'
        new_slugs['qtype-rightasc_02'] = 'only'
        new_slugs['qtype-rightasc_03'] = 'any'
        new_slugs['qtype-rightasc_04'] = 'all'
        new_slugs['unit-rightasc_01'] = 'radians'
        new_slugs['unit-rightasc_02'] = 'radians'
        new_slugs['unit-rightasc_03'] = 'radians'
        new_slugs['unit-rightasc_04'] = 'radians'
        new_slugs['widgets'] = 'rightasc'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='<li>No unit specified for "qtype-rightasc_02" but units were specified for other instances of this search field; the previous units have been used.</li><li>Unit "unit-rightasc_20" has an illegal value; it has been set to the default.</li><li>Search term "unit-rightasc_20" is a unit that is inconsistent with the units for previous instances of this search field; it has been ignored.</li><li>No unit specified for "rightasc1_12" but units were specified for other instances of this search field; the previous units have been used.</li>')

    def test__api_normalizeurl_search_multi_good_1_unit_only(self):
        "[test_ui_api.py] /__normalizeurl: search multi good 1 unit only"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=rightasc&rightasc1=10.&unit-rightasc=degrees'
        new_slugs['rightasc1'] = '10'
        new_slugs['qtype-rightasc'] = 'any'
        new_slugs['unit-rightasc'] = 'degrees'
        new_slugs['widgets'] = 'rightasc'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_multi_good_1_unit_bad(self):
        "[test_ui_api.py] /__normalizeurl: search multi good 1 unit bad"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=rightasc&rightasc1=10.&unit-rightasc=XXX'
        new_slugs['rightasc1'] = '10'
        new_slugs['qtype-rightasc'] = 'any'
        new_slugs['unit-rightasc'] = 'degrees'
        new_slugs['widgets'] = 'rightasc'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Unit "unit-rightasc" has an illegal value; it has been set to the default.')

    # Single column ranges

    def test__api_normalizeurl_search_single_empty(self):
        "[test_ui_api.py] /__normalizeurl: search single empty"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=observationduration&observationduration1='
        new_slugs['observationduration1'] = ''
        new_slugs['unit-observationduration'] = 'seconds'
        new_slugs['widgets'] = 'observationduration'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_single_empty_12(self):
        "[test_ui_api.py] /__normalizeurl: search single empty 12"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=observationduration&observationduration1=&observationduration2='
        new_slugs['observationduration1'] = ''
        new_slugs['observationduration2'] = ''
        new_slugs['unit-observationduration'] = 'seconds'
        new_slugs['widgets'] = 'observationduration'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_single_good_1(self):
        "[test_ui_api.py] /__normalizeurl: search single good 1"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=observationduration&observationduration1=10.'
        new_slugs['observationduration1'] = '10'
        new_slugs['unit-observationduration'] = 'seconds'
        new_slugs['widgets'] = 'observationduration'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_single_good_2(self):
        "[test_ui_api.py] /__normalizeurl: search single good 2"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=observationduration&observationduration2=10.'
        new_slugs['observationduration2'] = '10'
        new_slugs['unit-observationduration'] = 'seconds'
        new_slugs['widgets'] = 'observationduration'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_single_good_12(self):
        "[test_ui_api.py] /__normalizeurl: search single good 12"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=observationduration&observationduration1=10.&observationduration2=20.'
        new_slugs['observationduration1'] = '10'
        new_slugs['observationduration2'] = '20'
        new_slugs['unit-observationduration'] = 'seconds'
        new_slugs['widgets'] = 'observationduration'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_single_good_1_qtype_only(self):
        "[test_ui_api.py] /__normalizeurl: search single good 1 qtype only"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=observationduration&observationduration1=10.&qtype-observationduration=only'
        new_slugs['observationduration1'] = '10'
        new_slugs['unit-observationduration'] = 'seconds'
        new_slugs['widgets'] = 'observationduration'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Search term "qtype-observationduration" is a query type for a field that does not allow query types; it has been ignored.')

    def test__api_normalizeurl_search_single_good_2_qtype_all(self):
        "[test_ui_api.py] /__normalizeurl: search single good 2 qtype"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=observationduration&observationduration2=10.&qtype-observationduration=all'
        new_slugs['observationduration2'] = '10'
        new_slugs['unit-observationduration'] = 'seconds'
        new_slugs['widgets'] = 'observationduration'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='does not allow query')

    def test__api_normalizeurl_search_single_good_12_qtype_any(self):
        "[test_ui_api.py] /__normalizeurl: search single good 12 qtype any"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=observationduration&observationduration1=10.&observationduration2=20.&qtype-observationduration=any'
        new_slugs['observationduration1'] = '10'
        new_slugs['observationduration2'] = '20'
        new_slugs['unit-observationduration'] = 'seconds'
        new_slugs['widgets'] = 'observationduration'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Search term "qtype-observationduration" is a query type for a field that does not allow query types; it has been ignored.')

    def test__api_normalizeurl_search_single_good_12_qtype_only(self):
        "[test_ui_api.py] /__normalizeurl: search single good 12 qtype only"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=observationduration&observationduration1=10.&observationduration2=20.&qtype-observationduration=only'
        new_slugs['observationduration1'] = '10'
        new_slugs['observationduration2'] = '20'
        new_slugs['unit-observationduration'] = 'seconds'
        new_slugs['widgets'] = 'observationduration'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Search term "qtype-observationduration" is a query type for a field that does not allow query types; it has been ignored.')

    def test__api_normalizeurl_search_single_good_1_clause_1(self):
        "[test_ui_api.py] /__normalizeurl: search single good 1 _1"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=observationduration&observationduration1_1=10.'
        new_slugs['observationduration1'] = '10'
        new_slugs['unit-observationduration'] = 'seconds'
        new_slugs['widgets'] = 'observationduration'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_single_good_1_clause_2(self):
        "[test_ui_api.py] /__normalizeurl: search single good 1 _2"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=observationduration&observationduration1_2=10.'
        new_slugs['observationduration1'] = '10'
        new_slugs['unit-observationduration'] = 'seconds'
        new_slugs['widgets'] = 'observationduration'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_single_good_1_clause_1_2(self):
        "[test_ui_api.py] /__normalizeurl: search single good 1 _1_2"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=observationduration&observationduration1_2=10.&observationduration1_1=20.'
        new_slugs['observationduration1_01'] = '20'
        new_slugs['observationduration1_02'] = '10'
        new_slugs['unit-observationduration_01'] = 'seconds'
        new_slugs['unit-observationduration_02'] = 'seconds'
        new_slugs['widgets'] = 'observationduration'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_single_good_1_clause_10_20(self):
        "[test_ui_api.py] /__normalizeurl: search single good 1 _10_20"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=observationduration&observationduration1_20=10.&observationduration1_10=20.'
        new_slugs['observationduration1_01'] = '20'
        new_slugs['observationduration1_02'] = '10'
        new_slugs['unit-observationduration_01'] = 'seconds'
        new_slugs['unit-observationduration_02'] = 'seconds'
        new_slugs['widgets'] = 'observationduration'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_single_good_2_clause_1(self):
        "[test_ui_api.py] /__normalizeurl: search single good 2 _1"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=observationduration&observationduration2_1=10.'
        new_slugs['observationduration2'] = '10'
        new_slugs['unit-observationduration'] = 'seconds'
        new_slugs['widgets'] = 'observationduration'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_single_good_2_clause_2(self):
        "[test_ui_api.py] /__normalizeurl: search single good 2 _2"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=observationduration&observationduration2_2=10.'
        new_slugs['observationduration2'] = '10'
        new_slugs['unit-observationduration'] = 'seconds'
        new_slugs['widgets'] = 'observationduration'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_single_good_2_clause_1_2(self):
        "[test_ui_api.py] /__normalizeurl: search single good 2 _1_2"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=observationduration&observationduration2_2=10.&observationduration2_1=20.'
        new_slugs['observationduration2_01'] = '20'
        new_slugs['observationduration2_02'] = '10'
        new_slugs['unit-observationduration_01'] = 'seconds'
        new_slugs['unit-observationduration_02'] = 'seconds'
        new_slugs['widgets'] = 'observationduration'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_single_good_2_clause_10_20(self):
        "[test_ui_api.py] /__normalizeurl: search single good 2 _10_20"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=observationduration&observationduration2_20=10.&observationduration2_10=20.'
        new_slugs['observationduration2_01'] = '20'
        new_slugs['observationduration2_02'] = '10'
        new_slugs['unit-observationduration_01'] = 'seconds'
        new_slugs['unit-observationduration_02'] = 'seconds'
        new_slugs['widgets'] = 'observationduration'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_single_good_12_clause_01(self):
        "[test_ui_api.py] /__normalizeurl: search single good 12 _01"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=observationduration&observationduration1_01=10.&observationduration2_01=20.'
        new_slugs['observationduration1'] = '10'
        new_slugs['observationduration2'] = '20'
        new_slugs['unit-observationduration'] = 'seconds'
        new_slugs['widgets'] = 'observationduration'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_single_good_12_clause_01_1(self):
        "[test_ui_api.py] /__normalizeurl: search single good 12 _01_1"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=observationduration&observationduration1_01=10.&observationduration2_1=20.'
        new_slugs['observationduration1_01'] = '10'
        new_slugs['observationduration2_02'] = '20'
        new_slugs['unit-observationduration_01'] = 'seconds'
        new_slugs['unit-observationduration_02'] = 'seconds'
        new_slugs['widgets'] = 'observationduration'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_single_good_1_clause_bad_0(self):
        "[test_ui_api.py] /__normalizeurl: search single bad 1 _0"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=observationduration&observationduration1_0=10.'
        new_slugs['widgets'] = 'observationduration'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Search term "observationduration1_0" is unknown; it has been ignored.')

    def test__api_normalizeurl_search_single_good_1_clause_bad_n1(self):
        "[test_ui_api.py] /__normalizeurl: search single bad 1 -1"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=observationduration&observationduration1_-1=10.'
        new_slugs['widgets'] = 'observationduration'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Search term "observationduration1_-1" is unknown; it has been ignored.')

    def test__api_normalizeurl_search_single_good_1_clause_bad_XXX(self):
        "[test_ui_api.py] /__normalizeurl: search single bad 1 _XXX"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=observationduration&observationduration1_XXX=10.'
        new_slugs['widgets'] = 'observationduration'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Search term "observationduration1_XXX" is unknown; it has been ignored.')

    def test__api_normalizeurl_search_single_good_12_clause_01_XXX(self):
        "[test_ui_api.py] /__normalizeurl: search single good 12 _01_XXX"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=observationduration&observationduration1_01=10.&observationduration2_XXX=20.'
        new_slugs['observationduration1'] = '10'
        new_slugs['unit-observationduration'] = 'seconds'
        new_slugs['widgets'] = 'observationduration'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Search term "observationduration2_XXX" is unknown; it has been ignored.')

    def test__api_normalizeurl_search_single_good_12_clause_XXX_01(self):
        "[test_ui_api.py] /__normalizeurl: search single good 12 _XXX_01"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=observationduration&observationduration1_XXX=10.&observationduration2_01=20.'
        new_slugs['observationduration2'] = '20'
        new_slugs['unit-observationduration'] = 'seconds'
        new_slugs['widgets'] = 'observationduration'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Search term "observationduration1_XXX" is unknown; it has been ignored.')

    def test__api_normalizeurl_search_single_good_12_clause_1_01_XXX_qtypes(self):
        "[test_ui_api.py] /__normalizeurl: search single good 12 _1_01_XXX qtypes"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=observationduration&observationduration1_1=10.&observationduration2_01=20.&qtype-observationduration_1=only&qtype-observationduration_XXX=only'
        new_slugs['observationduration2_01'] = '20'
        new_slugs['observationduration1_02'] = '10'
        new_slugs['unit-observationduration_01'] = 'seconds'
        new_slugs['unit-observationduration_02'] = 'seconds'
        new_slugs['widgets'] = 'observationduration'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='<li>Search term "qtype-observationduration_1" is a query type for a field that does not allow query types; it has been ignored.</li><li>Search term "qtype-observationduration_XXX" is unknown; it has been ignored.</li>')

    def test__api_normalizeurl_search_single_good_12_clause_1_02_XXX_qtypes(self):
        "[test_ui_api.py] /__normalizeurl: search single good 12 _1_02_XXX qtypes"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=observationduration&observationduration1_1=10.&observationduration2_02=20.&qtype-observationduration_1=only&qtype-observationduration_XXX=only'
        new_slugs['observationduration1_01'] = '10'
        new_slugs['observationduration2_02'] = '20'
        new_slugs['unit-observationduration_01'] = 'seconds'
        new_slugs['unit-observationduration_02'] = 'seconds'
        new_slugs['widgets'] = 'observationduration'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='<li>Search term "qtype-observationduration_1" is a query type for a field that does not allow query types; it has been ignored.</li><li>Search term "qtype-observationduration_XXX" is unknown; it has been ignored.</li>')

    def test__api_normalizeurl_search_single_good_12_clause_1_01_XXX_units(self):
        "[test_ui_api.py] /__normalizeurl: search single good 12 _1_01_XXX units"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=observationduration&observationduration1_1=10.&observationduration2_01=20.&unit-observationduration_1=seconds&unit-observationduration_XXX=milliseconds'
        new_slugs['observationduration2_01'] = '20'
        new_slugs['observationduration1_02'] = '10'
        new_slugs['unit-observationduration_01'] = 'seconds'
        new_slugs['unit-observationduration_02'] = 'seconds'
        new_slugs['widgets'] = 'observationduration'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Search term "unit-observationduration_XXX" is unknown; it has been ignored.')

    def test__api_normalizeurl_search_single_good_12_clause_1_02_XXX_units(self):
        "[test_ui_api.py] /__normalizeurl: search single good 12 _1_02_XXX units"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=observationduration&observationduration1_1=10.&observationduration2_02=20.&unit-observationduration_1=milliseconds&unit-observationduration_XXX=milliseconds'
        new_slugs['observationduration1_01'] = '10'
        new_slugs['observationduration2_02'] = '20'
        new_slugs['unit-observationduration_01'] = 'milliseconds'
        new_slugs['unit-observationduration_02'] = 'milliseconds'
        new_slugs['widgets'] = 'observationduration'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Search term "unit-observationduration_XXX" is unknown; it has been ignored.')

    # Strings

    def test__api_normalizeurl_search_string_good(self):
        "[test_ui_api.py] /__normalizeurl: search string good"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=volumeid&volumeid=COISS'
        new_slugs['volumeid'] = 'COISS'
        new_slugs['qtype-volumeid'] = 'contains'
        new_slugs['widgets'] = 'volumeid'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_string_empty(self):
        "[test_ui_api.py] /__normalizeurl: search string empty"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=volumeid&volumeid='
        new_slugs['volumeid'] = ''
        new_slugs['qtype-volumeid'] = 'contains'
        new_slugs['widgets'] = 'volumeid'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_string_bad_1(self):
        "[test_ui_api.py] /__normalizeurl: search string bad 1"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=volumeid&volumeid1=COISS'
        new_slugs['widgets'] = 'volumeid'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Search term "volumeid1" is unknown; it has been ignored.')

    def test__api_normalizeurl_search_string_bad_2(self):
        "[test_ui_api.py] /__normalizeurl: search string bad 2"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=volumeid&volumeid2=COISS'
        new_slugs['widgets'] = 'volumeid'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Search term "volumeid2" is unknown; it has been ignored.')

    def test__api_normalizeurl_search_string_good_qtype_contains(self):
        "[test_ui_api.py] /__normalizeurl: search string good qtype contains"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=volumeid&volumeid=COISS&qtype-volumeid=contains'
        new_slugs['volumeid'] = 'COISS'
        new_slugs['qtype-volumeid'] = 'contains'
        new_slugs['widgets'] = 'volumeid'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_string_good_qtype_matches(self):
        "[test_ui_api.py] /__normalizeurl: search string good qtype matches"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=volumeid&volumeid=COISS&qtype-volumeid=matches'
        new_slugs['volumeid'] = 'COISS'
        new_slugs['qtype-volumeid'] = 'matches'
        new_slugs['widgets'] = 'volumeid'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_string_good_qtype_begins(self):
        "[test_ui_api.py] /__normalizeurl: search string good qtype begins"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=volumeid&volumeid=COISS&qtype-volumeid=begins'
        new_slugs['volumeid'] = 'COISS'
        new_slugs['qtype-volumeid'] = 'begins'
        new_slugs['widgets'] = 'volumeid'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_string_good_qtype_ends(self):
        "[test_ui_api.py] /__normalizeurl: search string good qtype ends"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=volumeid&volumeid=COISS&qtype-volumeid=ends'
        new_slugs['volumeid'] = 'COISS'
        new_slugs['qtype-volumeid'] = 'ends'
        new_slugs['widgets'] = 'volumeid'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_string_good_qtype_excludes(self):
        "[test_ui_api.py] /__normalizeurl: search string good qtype excludes"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=volumeid&volumeid=COISS&qtype-volumeid=excludes'
        new_slugs['volumeid'] = 'COISS'
        new_slugs['qtype-volumeid'] = 'excludes'
        new_slugs['widgets'] = 'volumeid'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_string_clause(self):
        "[test_ui_api.py] /__normalizeurl: search string clause"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=volumeid&volumeid_03=COISS&volumeid_04=COUVIS&qtype-volumeid_02=ends&qtype-volumeid_04=matches'
        new_slugs['volumeid_02'] = 'COISS'
        new_slugs['volumeid_03'] = 'COUVIS'
        new_slugs['qtype-volumeid_01'] = 'ends'
        new_slugs['qtype-volumeid_02'] = 'contains'
        new_slugs['qtype-volumeid_03'] = 'matches'
        new_slugs['widgets'] = 'volumeid'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_single_missing_lines(self):
        "[test_ui_api.py] /__normalizeurl: search single missing lines"
        new_slugs = dict(self.default_url_slugs)
        # Doesn't have a unit
        url = '/__normalizeurl.json?widgets=COISSmissinglines&COISSmissinglines1=10&COISSmissinglines2=20'
        new_slugs['COISSmissinglines1'] = '10'
        new_slugs['COISSmissinglines2'] = '20'
        new_slugs['widgets'] = 'COISSmissinglines'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_single_missing_lines_unit(self):
        "[test_ui_api.py] /__normalizeurl: search single missing lines unit"
        new_slugs = dict(self.default_url_slugs)
        # Doesn't have a unit
        url = '/__normalizeurl.json?widgets=COISSmissinglines&COISSmissinglines1=10&COISSmissinglines2=20&unit-COISSmissinglines=degrees'
        new_slugs['COISSmissinglines1'] = '10'
        new_slugs['COISSmissinglines2'] = '20'
        new_slugs['widgets'] = 'COISSmissinglines'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Search term "unit-COISSmissinglines" is a unit for a field that does not allow units; it has been ignored.')

    def test__api_normalizeurl_search_single_missing_lines_floating(self):
        "[test_ui_api.py] /__normalizeurl: search single missing lines floating point"
        new_slugs = dict(self.default_url_slugs)
        # Doesn't have a unit
        url = '/__normalizeurl.json?widgets=COISSmissinglines&COISSmissinglines1=10.&COISSmissinglines2=20.'
        new_slugs['widgets'] = 'COISSmissinglines'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Search query for "Missing Lines [Cassini ISS]" minimum had an illegal value; it has been ignored.')

    # Mult field

    def test__api_normalizeurl_search_mult_empty(self):
        "[test_ui_api.py] /__normalizeurl: search mult empty"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=instrument&instrument='
        new_slugs['instrument'] = ''
        new_slugs['widgets'] = 'instrument'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_mult_good(self):
        "[test_ui_api.py] /__normalizeurl: search mult good"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=instrument&instrument=COISS'
        new_slugs['instrument'] = 'COISS'
        new_slugs['widgets'] = 'instrument'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_mult_bad_1(self):
        "[test_ui_api.py] /__normalizeurl: search mult bad 1"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=instrument&instrument1=COISS'
        new_slugs['widgets'] = 'instrument'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Search term "instrument1" is unknown; it has been ignored.')

    def test__api_normalizeurl_search_mult_bad_2(self):
        "[test_ui_api.py] /__normalizeurl: search mult bad 2"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=instrument&instrument2=COISS'
        new_slugs['widgets'] = 'instrument'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Search term "instrument2" is unknown; it has been ignored.')

    def test__api_normalizeurl_search_mult_bad_12(self):
        "[test_ui_api.py] /__normalizeurl: search mult bad 12"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=instrument&instrument1=COISS&instrument2=COISS'
        new_slugs['widgets'] = 'instrument'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='<li>Search term "instrument1" is unknown; it has been ignored.</li><li>Search term "instrument2" is unknown; it has been ignored.</li>')

    def test__api_normalizeurl_search_mult_bad_val(self):
        "[test_ui_api.py] /__normalizeurl: search mult bad val"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=instrument&instrument=COISS,XXX'
        new_slugs['widgets'] = 'instrument'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Search query for "Instrument Name" had an illegal value; it has been ignored.')

    def test__api_normalizeurl_search_mult_bad_qtype_only(self):
        "[test_ui_api.py] /__normalizeurl: search mult bad qtype only"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=instrument&instrument=COISS&qtype-instrument=only'
        new_slugs['instrument'] = 'COISS'
        new_slugs['widgets'] = 'instrument'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Search term "qtype-instrument" is a query type for a field that does not allow query types; it has been ignored.')

    def test__api_normalizeurl_search_mult_clause_1(self):
        "[test_ui_api.py] /__normalizeurl: search mult clause 1"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=instrument&instrument_01=COISS'
        new_slugs['widgets'] = 'instrument'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Search field "Instrument Name" has a clause number but none is permitted; it has been removed.')

    def test__api_normalizeurl_search_mult_clause_2(self):
        "[test_ui_api.py] /__normalizeurl: search mult clause 2"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=instrument&instrument_01=COISS&instrument=COUVIS'
        new_slugs['instrument'] = 'COUVIS'
        new_slugs['widgets'] = 'instrument'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Search field "Instrument Name" has a clause number but none is permitted; it has been removed.')

    ### Bad values

    # Multi-column ranges

    def test__api_normalizeurl_search_multi_bad_1(self):
        "[test_ui_api.py] /__normalizeurl: search multi bad 1"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=rightasc&rightasc1=10.X'
        new_slugs['qtype-rightasc'] = 'any'
        new_slugs['unit-rightasc'] = 'degrees'
        new_slugs['widgets'] = 'rightasc'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Search query for "Right Ascension [General]" minimum had an illegal value; it has been ignored.')

    def test__api_normalizeurl_search_multi_bad_2(self):
        "[test_ui_api.py] /__normalizeurl: search multi bad 2"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=rightasc&rightasc2=10.X'
        new_slugs['qtype-rightasc'] = 'any'
        new_slugs['unit-rightasc'] = 'degrees'
        new_slugs['widgets'] = 'rightasc'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Search query for "Right Ascension [General]" maximum had an illegal value; it has been ignored.')

    def test__api_normalizeurl_search_multi_good_1_bad_2(self):
        "[test_ui_api.py] /__normalizeurl: search multi good 1 bad 2"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=rightasc&rightasc1=10.&rightasc2=20.X'
        new_slugs['rightasc1'] = '10'
        new_slugs['qtype-rightasc'] = 'any'
        new_slugs['unit-rightasc'] = 'degrees'
        new_slugs['widgets'] = 'rightasc'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Search query for "Right Ascension [General]" maximum had an illegal value; it has been ignored.')

    def test__api_normalizeurl_search_multi_bad_1_good_2(self):
        "[test_ui_api.py] /__normalizeurl: search multi bad 1 good 2"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=rightasc&rightasc1=10.X&rightasc2=20.'
        new_slugs['rightasc2'] = '20'
        new_slugs['qtype-rightasc'] = 'any'
        new_slugs['unit-rightasc'] = 'degrees'
        new_slugs['widgets'] = 'rightasc'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Search query for "Right Ascension [General]" minimum had an illegal value; it has been ignored.')

    def test__api_normalizeurl_search_multi_bad_1_bad_2(self):
        "[test_ui_api.py] /__normalizeurl: search multi bad 1 bad 2"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=rightasc&rightasc1=10.X&rightasc2=20.X'
        new_slugs['qtype-rightasc'] = 'any'
        new_slugs['unit-rightasc'] = 'degrees'
        new_slugs['widgets'] = 'rightasc'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='<li>Search query for "Right Ascension [General]" minimum had an illegal value; it has been ignored.</li><li>Search query for "Right Ascension [General]" maximum had an illegal value; it has been ignored.</li>')

    def test__api_normalizeurl_search_multi_good_1_bad_qtype(self):
        "[test_ui_api.py] /__normalizeurl: search multi good 1 bad qtype"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=rightasc&rightasc1=10.&qtype-rightasc=XXX'
        new_slugs['rightasc1'] = '10'
        new_slugs['qtype-rightasc'] = 'any'
        new_slugs['unit-rightasc'] = 'degrees'
        new_slugs['widgets'] = 'rightasc'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Query type "qtype-rightasc" has an illegal value; it has been set to the default.')

    # Single column ranges

    def test__api_normalizeurl_search_single_bad_1(self):
        "[test_ui_api.py] /__normalizeurl: search single bad 1"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=observationduration&observationduration1=10.X'
        new_slugs['widgets'] = 'observationduration'
        new_slugs['unit-observationduration'] = 'seconds'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Search query for "Observation Duration [General]" minimum had an illegal value; it has been ignored.')

    def test__api_normalizeurl_search_single_bad_2(self):
        "[test_ui_api.py] /__normalizeurl: search single bad 2"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=observationduration&observationduration2=10.X'
        new_slugs['widgets'] = 'observationduration'
        new_slugs['unit-observationduration'] = 'seconds'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Search query for "Observation Duration [General]" maximum had an illegal value; it has been ignored.')

    def test__api_normalizeurl_search_single_good_1_bad_2(self):
        "[test_ui_api.py] /__normalizeurl: search single good 1 bad 2"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=observationduration&observationduration1=10.&observationduration2=20.X'
        new_slugs['observationduration1'] = '10'
        new_slugs['unit-observationduration'] = 'seconds'
        new_slugs['widgets'] = 'observationduration'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Search query for "Observation Duration [General]" maximum had an illegal value; it has been ignored.')

    def test__api_normalizeurl_search_single_bad_1_good_2(self):
        "[test_ui_api.py] /__normalizeurl: search single bad 1 good 2"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=observationduration&observationduration1=10.X&observationduration2=20.'
        new_slugs['observationduration2'] = '20'
        new_slugs['unit-observationduration'] = 'seconds'
        new_slugs['widgets'] = 'observationduration'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Search query for "Observation Duration [General]" minimum had an illegal value; it has been ignored.')

    def test__api_normalizeurl_search_single_bad_1_bad_2(self):
        "[test_ui_api.py] /__normalizeurl: search single bad 1 bad 2"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=observationduration&observationduration1=10.X&observationduration2=20.X'
        new_slugs['widgets'] = 'observationduration'
        new_slugs['unit-observationduration'] = 'seconds'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Search query for "Observation Duration [General]" minimum had an illegal value; it has been ignored.')

    def test__api_normalizeurl_search_single_good_1_bad_qtype(self):
        "[test_ui_api.py] /__normalizeurl: search single good 1 bad qtype"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=observationduration&observationduration1=10.&qtype-observationduration=XXX'
        new_slugs['observationduration1'] = '10'
        new_slugs['unit-observationduration'] = 'seconds'
        new_slugs['widgets'] = 'observationduration'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Search term "qtype-observationduration" is a query type for a field that does not allow query types; it has been ignored.')

    def test__api_normalizeurl_search_string_bad_qtype(self):
        "[test_ui_api.py] /__normalizeurl: search string bad qtype"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=volumeid&volumeid=COISS&qtype-volumeid=XXX'
        new_slugs['volumeid'] = 'COISS'
        new_slugs['qtype-volumeid'] = 'contains'
        new_slugs['widgets'] = 'volumeid'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Query type "volumeid" has an illegal value; it has been set to the default.')

    # Old slugs and duplicates

    def test__api_normalizeurl_search_multi_old_1(self):
        "[test_ui_api.py] /__normalizeurl: search multi old 1"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=RINGGEOringradius&ringradius1=10.'
        new_slugs['RINGGEOringradius1'] = '10'
        new_slugs['qtype-RINGGEOringradius'] = 'any'
        new_slugs['unit-RINGGEOringradius'] = 'km'
        new_slugs['widgets'] = 'RINGGEOringradius'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='previous version')

    def test__api_normalizeurl_search_mult_old_2(self):
        "[test_ui_api.py] /__normalizeurl: search multi old 2"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=RINGGEOringradius&ringradius2=10.'
        new_slugs['RINGGEOringradius2'] = '10'
        new_slugs['qtype-RINGGEOringradius'] = 'any'
        new_slugs['unit-RINGGEOringradius'] = 'km'
        new_slugs['widgets'] = 'RINGGEOringradius'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='previous version')

    def test__api_normalizeurl_search_multi_old_12(self):
        "[test_ui_api.py] /__normalizeurl: search multi old 12"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=RINGGEOringradius&ringradius1=10.&ringradius2=20.'
        new_slugs['RINGGEOringradius1'] = '10'
        new_slugs['RINGGEOringradius2'] = '20'
        new_slugs['qtype-RINGGEOringradius'] = 'any'
        new_slugs['unit-RINGGEOringradius'] = 'km'
        new_slugs['widgets'] = 'RINGGEOringradius'
        self._run_url_slugs_equal(url, new_slugs, msg_contains='previous version')

    def test__api_normalizeurl_search_multi_mix_new_old(self):
        "[test_ui_api.py] /__normalizeurl: search multi mix new 1 old 2"
        url = '/__normalizeurl.json?widgets=RINGGEOringradius&RINGGEOringradius1=10.&ringradius2=20.'
        new_slugs = dict(self.default_url_slugs)
        new_slugs['RINGGEOringradius1'] = '10'
        new_slugs['RINGGEOringradius2'] = '20'
        new_slugs['qtype-RINGGEOringradius'] = 'any'
        new_slugs['unit-RINGGEOringradius'] = 'km'
        new_slugs['widgets'] = 'RINGGEOringradius'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_multi_mix_old_new(self):
        "[test_ui_api.py] /__normalizeurl: search multi mix old 1 new 2"
        url = '/__normalizeurl.json?widgets=RINGGEOringradius&ringradius1=10.&RINGGEOringradius2=20.'
        new_slugs = dict(self.default_url_slugs)
        new_slugs['RINGGEOringradius1'] = '10'
        new_slugs['RINGGEOringradius2'] = '20'
        new_slugs['qtype-RINGGEOringradius'] = 'any'
        new_slugs['unit-RINGGEOringradius'] = 'km'
        new_slugs['widgets'] = 'RINGGEOringradius'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_multi_dup_old_1(self):
        "[test_ui_api.py] /__normalizeurl: search multi dup old 1"
        url = '/__normalizeurl.json?widgets=RINGGEOringradius&ringradius1=10.&RINGGEOringradius1=20.'
        new_slugs = dict(self.default_url_slugs)
        new_slugs['RINGGEOringradius1'] = '20' # Parsed in alphabetical order
        new_slugs['qtype-RINGGEOringradius'] = 'any'
        new_slugs['unit-RINGGEOringradius'] = 'km'
        new_slugs['widgets'] = 'RINGGEOringradius'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_multi_dup_old_2(self):
        "[test_ui_api.py] /__normalizeurl: search multi dup old 2"
        url = '/__normalizeurl.json?widgets=RINGGEOringradius&RINGGEOringradius2=10.&ringradius2=20.'
        new_slugs = dict(self.default_url_slugs)
        new_slugs['RINGGEOringradius2'] = '10'
        new_slugs['qtype-RINGGEOringradius'] = 'any'
        new_slugs['unit-RINGGEOringradius'] = 'km'
        new_slugs['widgets'] = 'RINGGEOringradius'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_multi_old_1_old_qtype(self):
        "[test_ui_api.py] /__normalizeurl: search multi old 1 old qtype"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=RINGGEOringradius&ringradius1=10.&qtype-ringradius=only'
        new_slugs['RINGGEOringradius1'] = '10'
        new_slugs['qtype-RINGGEOringradius'] = 'only'
        new_slugs['unit-RINGGEOringradius'] = 'km'
        new_slugs['widgets'] = 'RINGGEOringradius'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_multi_old_1_new_qtype(self):
        "[test_ui_api.py] /__normalizeurl: search multi old 1 new qtype"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=RINGGEOringradius&ringradius1=10.&qtype-RINGGEOringradius=only'
        new_slugs['RINGGEOringradius1'] = '10'
        new_slugs['qtype-RINGGEOringradius'] = 'only'
        new_slugs['unit-RINGGEOringradius'] = 'km'
        new_slugs['widgets'] = 'RINGGEOringradius'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_multi_new_1_old_qtype(self):
        "[test_ui_api.py] /__normalizeurl: search multi new 1 old qtype"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=RINGGEOringradius&RINGGEOringradius1=10.&qtype-ringradius=only'
        new_slugs['RINGGEOringradius1'] = '10'
        new_slugs['qtype-RINGGEOringradius'] = 'only'
        new_slugs['unit-RINGGEOringradius'] = 'km'
        new_slugs['widgets'] = 'RINGGEOringradius'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_multi_new_1_new_qtype(self):
        "[test_ui_api.py] /__normalizeurl: search multi new 1 new qtype"
        new_slugs = dict(self.default_url_slugs)
        url = '/__normalizeurl.json?widgets=RINGGEOringradius&RINGGEOringradius1=10.&qtype-RINGGEOringradius=only'
        new_slugs['RINGGEOringradius1'] = '10'
        new_slugs['qtype-RINGGEOringradius'] = 'only'
        new_slugs['unit-RINGGEOringradius'] = 'km'
        new_slugs['widgets'] = 'RINGGEOringradius'
        self._run_url_slugs_equal(url, new_slugs)

    # Slug that can't be searched

    def test__api_normalizeurl_search_not_searchable(self):
        "[test_ui_api.py] /__normalizeurl: search not searchable"
        url = '/__normalizeurl.json?**previewimages=XXX'
        new_slugs = dict(self.default_url_slugs)
        self._run_url_slugs_equal(url, new_slugs, msg_contains='Search field "**previewimages" is not searchable; it has been removed.')

    # Convert ringobsid to opusid

    def test__api_normalizeurl_search_ringobsid(self):
        "[test_ui_api.py] /__normalizeurl: search ringobsid"
        url = '/__normalizeurl.json?ringobsid=S_IMG_VG2_ISS_4360845_N'
        new_slugs = dict(self.default_url_slugs)
        new_slugs['opusid'] = 'vg-iss-2-s-c4360845'
        new_slugs['qtype-opusid'] = 'contains'
        new_slugs['widgets'] = 'opusid'
        self._run_url_slugs_equal(url, new_slugs)

    def test__api_normalizeurl_search_ringobsid_bad(self):
        "[test_ui_api.py] /__normalizeurl: search ringobsid bad"
        url = '/__normalizeurl.json?ringobsid=S_IMG_VG2_ISS_4360846_N'
        new_slugs = dict(self.default_url_slugs)
        self._run_url_slugs_equal(url, new_slugs, msg_contains='RING OBS ID "S_IMG_VG2_ISS_4360846_N" not found; the ringobsid search term has been removed.')

    def test__api_normalizeurl_search_ringobsid_bad_2(self):
        "[test_ui_api.py] /__normalizeurl: search ringobsid bad 2"
        url = '/__normalizeurl.json?ringobsid=XXX'
        new_slugs = dict(self.default_url_slugs)
        self._run_url_slugs_equal(url, new_slugs, msg_contains='RING OBS ID "XXX" not found; the ringobsid search term has been removed.')

    ### Real-world tests

    def test__api_normalizeurl_real_1(self):
        "[test_ui_api.py] /__normalizeurl: real 1"
        url = '/__normalizeurl.json?planet=Saturn&typeid=Image&missionid=Voyager&timesec1=1980-09-27T02:16&timesec2=1980-09-28T02:17&qtype-volumeid=contains&view=detail&browse=gallery&colls_browse=gallery&page=1&gallery_data_viewer=true&limit=100&order=time1&cols=ringobsid,planet,target,phase1,phase2,time1,time2&widgets=timesec1&widgets2=&detail=S_IMG_CO_ISS_1460961026_N'
        expected = {'new_url': 'mission=Voyager&observationtype=Image&planet=Saturn&time1=1980-09-27T02:16:00.000&time2=1980-09-28T02:17:00.000&qtype-time=any&unit-time=ymdhms&qtype-volumeid=contains&cols=opusid,instrument,planet,target,time1,observationduration&widgets=time,mission,planet,observationtype,volumeid&order=time1,opusid&view=detail&browse=gallery&cart_browse=gallery&startobs=1&cart_startobs=1&detail=co-iss-n1460961026', 'new_slugs': [{'mission': 'Voyager'}, {'observationtype': 'Image'}, {'planet': 'Saturn'}, {'time1': '1980-09-27T02:16:00.000'}, {'time2': '1980-09-28T02:17:00.000'}, {'qtype-time': 'any'}, {'unit-time': 'ymdhms'}, {'qtype-volumeid': 'contains'}, {'cols': 'opusid,instrument,planet,target,time1,observationduration'}, {'widgets': 'time,mission,planet,observationtype,volumeid'}, {'order': 'time1,opusid'}, {'view': 'detail'}, {'browse': 'gallery'}, {'cart_browse': 'gallery'}, {'startobs': 1}, {'cart_startobs': 1}, {'detail': 'co-iss-n1460961026'}], 'msg': '<p>Your bookmarked URL is from a previous version of OPUS. It has been adjusted to conform to the current version.</p><p>We found the following issues with your bookmarked URL:</p><ul><li>Your URL uses the old defaults for selected metadata; they have been replaced with the new defaults.</li><li>You appear to be using an obsolete RINGOBS_ID (S_IMG_CO_ISS_1460961026_N) instead of the equivalent new OPUS_ID (co-iss-n1460961026); it has been converted for you.</li></ul><p>We strongly recommend that you replace your old bookmark with the updated URL in your browser so that you will not see this message in the future.</p>'}
        self._run_json_equal(url, expected)

    def test__api_normalizeurl_real_2(self):
        "[test_ui_api.py] /__normalizeurl: real 2"
        url = '/__normalizeurl.json?planet=Jupiter&target=EUROPA&missionid=Voyager&view=detail&browse=data&colls_browse=gallery&page=1&gallery_data_viewer=true&limit=100&order=time1&cols=ringobsid,planet,target,phase1,phase2,time1,time2&widgets=missionid,planet,target&widgets2=&detail=S_IMG_CO_ISS_1460961026_N'
        expected = {'new_url': 'mission=Voyager&planet=Jupiter&target=EUROPA&cols=opusid,instrument,planet,target,time1,observationduration&widgets=mission,planet,target&order=time1,opusid&view=detail&browse=data&cart_browse=gallery&startobs=1&cart_startobs=1&detail=co-iss-n1460961026', 'new_slugs': [{'mission': 'Voyager'}, {'planet': 'Jupiter'}, {'target': 'EUROPA'}, {'cols': 'opusid,instrument,planet,target,time1,observationduration'}, {'widgets': 'mission,planet,target'}, {'order': 'time1,opusid'}, {'view': 'detail'}, {'browse': 'data'}, {'cart_browse': 'gallery'}, {'startobs': 1}, {'cart_startobs': 1}, {'detail': 'co-iss-n1460961026'}], 'msg': '<p>Your bookmarked URL is from a previous version of OPUS. It has been adjusted to conform to the current version.</p><p>We found the following issues with your bookmarked URL:</p><ul><li>Your URL uses the old defaults for selected metadata; they have been replaced with the new defaults.</li><li>You appear to be using an obsolete RINGOBS_ID (S_IMG_CO_ISS_1460961026_N) instead of the equivalent new OPUS_ID (co-iss-n1460961026); it has been converted for you.</li></ul><p>We strongly recommend that you replace your old bookmark with the updated URL in your browser so that you will not see this message in the future.</p>'}
        self._run_json_equal(url, expected)

    def test__api_normalizeurl_real_3(self):
        "[test_ui_api.py] /__normalizeurl: real 3"
        url = '/__normalizeurl.json?mission=Cassini&target=Jupiter,Ganymede,Europa,Callisto,Io&instrument=Cassini+ISS&view=browse&browse=gallery&colls_browse=gallery&page=1&gallery_data_viewer=true&limit=100&order=time1&cols=opusid,instrumentid,planet,target,time1,observationduration&widgets=instrument,mission,planet,target&widgets2=&detail='
        expected = {'new_url': 'instrument=Cassini ISS&mission=Cassini&target=Callisto,Europa,Ganymede,Io,Jupiter&cols=opusid,instrument,planet,target,time1,observationduration&widgets=instrument,mission,planet,target&order=time1,opusid&view=browse&browse=gallery&cart_browse=gallery&startobs=1&cart_startobs=1&detail=', 'new_slugs': [{'instrument': 'Cassini ISS'}, {'mission': 'Cassini'}, {'target': 'Callisto,Europa,Ganymede,Io,Jupiter'}, {'cols': 'opusid,instrument,planet,target,time1,observationduration'}, {'widgets': 'instrument,mission,planet,target'}, {'order': 'time1,opusid'}, {'view': 'browse'}, {'browse': 'gallery'}, {'cart_browse': 'gallery'}, {'startobs': 1}, {'cart_startobs': 1}, {'detail': ''}], 'msg': '<p>Your bookmarked URL is from a previous version of OPUS. It has been adjusted to conform to the current version.</p><p>We strongly recommend that you replace your old bookmark with the updated URL in your browser so that you will not see this message in the future.</p>'}
        self._run_json_equal(url, expected)

    def test__api_normalizeurl_real_4(self):
        "[test_ui_api.py] /__normalizeurl: real 4"
        url = '/__normalizeurl.json?mission=Voyager&observationtype=Image&planet=Saturn&time1=1980-09-27T02:16:00.000&time2=1980-09-28T02:17:00.000&qtype-time=any&cols=opusid,instrument,planet,target,time1,observationduration&widgets=time,mission,planet,observationtype&order=time1,opusid&view=detail&browse=gallery&startobs=1&cart_browse=gallery&detail=co-iss-n1460961026'
        expected = {'new_url': 'mission=Voyager&observationtype=Image&planet=Saturn&time1=1980-09-27T02:16:00.000&time2=1980-09-28T02:17:00.000&qtype-time=any&unit-time=ymdhms&cols=opusid,instrument,planet,target,time1,observationduration&widgets=time,mission,planet,observationtype&order=time1,opusid&view=detail&browse=gallery&cart_browse=gallery&startobs=1&cart_startobs=1&detail=co-iss-n1460961026', 'new_slugs': [{'mission': 'Voyager'}, {'observationtype': 'Image'}, {'planet': 'Saturn'}, {'time1': '1980-09-27T02:16:00.000'}, {'time2': '1980-09-28T02:17:00.000'}, {'qtype-time': 'any'}, {'unit-time': 'ymdhms'}, {'cols': 'opusid,instrument,planet,target,time1,observationduration'}, {'widgets': 'time,mission,planet,observationtype'}, {'order': 'time1,opusid'}, {'view': 'detail'}, {'browse': 'gallery'}, {'cart_browse': 'gallery'}, {'startobs': 1}, {'cart_startobs': 1}, {'detail': 'co-iss-n1460961026'}], 'msg': None}
        self._run_json_equal(url, expected)

    def test__api_normalizeurl_real_5(self):
        "[test_ui_api.py] /__normalizeurl: real 5"
        url = '/__normalizeurl.json?mission=Voyager&observationtype=Image&planet=Saturn&time1=1980-09-27T02:16:00.000&time2=1980-09-28T02:17:00.000&qtype-time=any&cols=opusid,instrument,planet,target,time1,observationduration&widgets=time,mission,planet,observationtype&order=time1,opusid&view=detail&browse=gallery&startobs=1&cart_browse=gallery&detail='
        expected = {'new_url': 'mission=Voyager&observationtype=Image&planet=Saturn&time1=1980-09-27T02:16:00.000&time2=1980-09-28T02:17:00.000&qtype-time=any&unit-time=ymdhms&cols=opusid,instrument,planet,target,time1,observationduration&widgets=time,mission,planet,observationtype&order=time1,opusid&view=detail&browse=gallery&cart_browse=gallery&startobs=1&cart_startobs=1&detail=', 'new_slugs': [{'mission': 'Voyager'}, {'observationtype': 'Image'}, {'planet': 'Saturn'}, {'time1': '1980-09-27T02:16:00.000'}, {'time2': '1980-09-28T02:17:00.000'}, {'qtype-time': 'any'}, {'unit-time': 'ymdhms'}, {'cols': 'opusid,instrument,planet,target,time1,observationduration'}, {'widgets': 'time,mission,planet,observationtype'}, {'order': 'time1,opusid'}, {'view': 'detail'}, {'browse': 'gallery'}, {'cart_browse': 'gallery'}, {'startobs': 1}, {'cart_startobs': 1}, {'detail': ''}], 'msg': None}
        self._run_json_equal(url, expected)

    def test__api_normalizeurl_real_6(self):
        "[test_ui_api.py] /__normalizeurl: real 6"
        url = '/__normalizeurl.json?SURFACEGEOplutocenterresolution2=5&SURFACEGEOplutophase1=160&surfacegeometrytargetname=Pluto&qtype-SURFACEGEOplutophase=any&cols=opusid,instrument,time1,SURFACEGEOplutoplanetographiclatitude1,SURFACEGEOplutoplanetographiclatitude2,SURFACEGEOplutoIAUwestlongitude1,SURFACEGEOplutoIAUwestlongitude2,SURFACEGEOplutocenterdistance,SURFACEGEOplutocenterresolution,SURFACEGEOplutophase1,SURFACEGEOplutophase2&widgets=SURFACEGEOplutocenterresolution,SURFACEGEOplutophase,surfacegeometrytargetname&order=time1,opusid&view=search&browse=gallery&cart_browse=gallery&startobs=1&cart_startobs=1&detail='
        expected = {"new_url": "surfacegeometrytargetname=Pluto&SURFACEGEOpluto_centerresolution2=5&unit-SURFACEGEOpluto_centerresolution=km_pixel&SURFACEGEOpluto_phase1=160&qtype-SURFACEGEOpluto_phase=any&unit-SURFACEGEOpluto_phase=degrees&cols=opusid,instrument,time1,SURFACEGEOpluto_planetographiclatitude1,SURFACEGEOpluto_planetographiclatitude2,SURFACEGEOpluto_IAUwestlongitude1,SURFACEGEOpluto_IAUwestlongitude2,SURFACEGEOpluto_centerdistance,SURFACEGEOpluto_centerresolution,SURFACEGEOpluto_phase1,SURFACEGEOpluto_phase2&widgets=SURFACEGEOpluto_centerresolution,SURFACEGEOpluto_phase,surfacegeometrytargetname&order=time1,opusid&view=search&browse=gallery&cart_browse=gallery&startobs=1&cart_startobs=1&detail=", "new_slugs": [{"surfacegeometrytargetname": "Pluto"}, {"SURFACEGEOpluto_centerresolution2": "5"}, {"unit-SURFACEGEOpluto_centerresolution": "km_pixel"}, {"SURFACEGEOpluto_phase1": "160"}, {"qtype-SURFACEGEOpluto_phase": "any"}, {"unit-SURFACEGEOpluto_phase": "degrees"}, {"cols": "opusid,instrument,time1,SURFACEGEOpluto_planetographiclatitude1,SURFACEGEOpluto_planetographiclatitude2,SURFACEGEOpluto_IAUwestlongitude1,SURFACEGEOpluto_IAUwestlongitude2,SURFACEGEOpluto_centerdistance,SURFACEGEOpluto_centerresolution,SURFACEGEOpluto_phase1,SURFACEGEOpluto_phase2"}, {"widgets": "SURFACEGEOpluto_centerresolution,SURFACEGEOpluto_phase,surfacegeometrytargetname"}, {"order": "time1,opusid"}, {"view": "search"}, {"browse": "gallery"}, {"cart_browse": "gallery"}, {"startobs": 1}, {"cart_startobs": 1}, {"detail": ""}], "msg": "<p>Your bookmarked URL is from a previous version of OPUS. It has been adjusted to conform to the current version.</p><p>We strongly recommend that you replace your old bookmark with the updated URL in your browser so that you will not see this message in the future.</p>"}
        self._run_json_equal(url, expected)

    def test__api_normalizeurl_real_7(self):
        "[test_ui_api.py] /__normalizeurl: real 7"
        url = '/__normalizeurl.json?wavelength1_06=7&wavelength2_06=8&wavelength1_08=5&wavelength1_09=10&qtype-wavelength_09=all&qtype-wavelength=any&cols=opusid,instrument,planet,target,time1,observationduration&widgets=wavelength,planet,target&order=time1,opusid&view=search&browse=gallery&cart_browse=gallery&startobs=1&cart_startobs=1&detail='
        expected = {"new_url": "qtype-wavelength_01=any&unit-wavelength_01=microns&wavelength1_02=7&wavelength2_02=8&qtype-wavelength_02=any&unit-wavelength_02=microns&wavelength1_03=5&qtype-wavelength_03=any&unit-wavelength_03=microns&wavelength1_04=10&qtype-wavelength_04=all&unit-wavelength_04=microns&cols=opusid,instrument,planet,target,time1,observationduration&widgets=wavelength,planet,target&order=time1,opusid&view=search&browse=gallery&cart_browse=gallery&startobs=1&cart_startobs=1&detail=", "new_slugs": [{"qtype-wavelength_01": "any"}, {"unit-wavelength_01": "microns"}, {"wavelength1_02": "7"}, {"wavelength2_02": "8"}, {"qtype-wavelength_02": "any"}, {"unit-wavelength_02": "microns"}, {"wavelength1_03": "5"}, {"qtype-wavelength_03": "any"}, {"unit-wavelength_03": "microns"}, {"wavelength1_04": "10"}, {"qtype-wavelength_04": "all"}, {"unit-wavelength_04": "microns"}, {"cols": "opusid,instrument,planet,target,time1,observationduration"}, {"widgets": "wavelength,planet,target"}, {"order": "time1,opusid"}, {"view": "search"}, {"browse": "gallery"}, {"cart_browse": "gallery"}, {"startobs": 1}, {"cart_startobs": 1}, {"detail": ""}], "msg": None}
        self._run_json_equal(url, expected)

    def test__api_normalizeurl_real_8(self):
        "[test_ui_api.py] /__normalizeurl: real 8"
        url = '/__normalizeurl.json?qtype-RINGGEOringradius=any&qtype-VOYAGERspacecraftclockcount_01=any&VOYAGERspacecraftclockcount1_02=00004:00:001&VOYAGERspacecraftclockcount2_02=00005:00:001&qtype-VOYAGERspacecraftclockcount_02=any&qtype-VOYAGERspacecraftclockcount_03=any&mission=Voyager&qtype-volumeid=contains&wavelength1_01=0.5750&wavelength2_01=0.5850&qtype-wavelength_01=any&wavelength1_02=30.0000&wavelength2_02=300.0000&qtype-wavelength_02=any&wavelength2_03=300.0000&qtype-wavelength_03=any&wavelength1_04=0.7500&wavelength2_04=300.0000&qtype-wavelength_04=any&qtype-wavelength_05=any&qtype-wavelength_06=any&cols=opusid,instrument,planet,target,time1,observationduration&widgets=VOYAGERspacecraftclockcount,mission,volumeid,RINGGEOringradius,observationduration,wavelength,planet,target&order=time1,opusid&view=search&browse=gallery&cart_browse=gallery&startobs=1&cart_startobs=1&detail='
        expected = {"new_url": "mission=Voyager&qtype-RINGGEOringradius=any&unit-RINGGEOringradius=km&qtype-volumeid=contains&qtype-VOYAGERspacecraftclockcount_01=any&VOYAGERspacecraftclockcount1_02=00004:00:001&VOYAGERspacecraftclockcount2_02=00005:00:001&qtype-VOYAGERspacecraftclockcount_02=any&qtype-VOYAGERspacecraftclockcount_03=any&wavelength1_01=0.575&wavelength2_01=0.585&qtype-wavelength_01=any&unit-wavelength_01=microns&wavelength1_02=30&wavelength2_02=300&qtype-wavelength_02=any&unit-wavelength_02=microns&wavelength2_03=300&qtype-wavelength_03=any&unit-wavelength_03=microns&wavelength1_04=0.75&wavelength2_04=300&qtype-wavelength_04=any&unit-wavelength_04=microns&qtype-wavelength_05=any&unit-wavelength_05=microns&qtype-wavelength_06=any&unit-wavelength_06=microns&cols=opusid,instrument,planet,target,time1,observationduration&widgets=VOYAGERspacecraftclockcount,mission,volumeid,RINGGEOringradius,observationduration,wavelength,planet,target&order=time1,opusid&view=search&browse=gallery&cart_browse=gallery&startobs=1&cart_startobs=1&detail=", "new_slugs": [{"mission": "Voyager"}, {"qtype-RINGGEOringradius": "any"}, {"unit-RINGGEOringradius": "km"}, {"qtype-volumeid": "contains"}, {"qtype-VOYAGERspacecraftclockcount_01": "any"}, {"VOYAGERspacecraftclockcount1_02": "00004:00:001"}, {"VOYAGERspacecraftclockcount2_02": "00005:00:001"}, {"qtype-VOYAGERspacecraftclockcount_02": "any"}, {"qtype-VOYAGERspacecraftclockcount_03": "any"}, {"wavelength1_01": "0.575"}, {"wavelength2_01": "0.585"}, {"qtype-wavelength_01": "any"}, {"unit-wavelength_01": "microns"}, {"wavelength1_02": "30"}, {"wavelength2_02": "300"}, {"qtype-wavelength_02": "any"}, {"unit-wavelength_02": "microns"}, {"wavelength2_03": "300"}, {"qtype-wavelength_03": "any"}, {"unit-wavelength_03": "microns"}, {"wavelength1_04": "0.75"}, {"wavelength2_04": "300"}, {"qtype-wavelength_04": "any"}, {"unit-wavelength_04": "microns"}, {"qtype-wavelength_05": "any"}, {"unit-wavelength_05": "microns"}, {"qtype-wavelength_06": "any"}, {"unit-wavelength_06": "microns"}, {"cols": "opusid,instrument,planet,target,time1,observationduration"}, {"widgets": "VOYAGERspacecraftclockcount,mission,volumeid,RINGGEOringradius,observationduration,wavelength,planet,target"}, {"order": "time1,opusid"}, {"view": "search"}, {"browse": "gallery"}, {"cart_browse": "gallery"}, {"startobs": 1}, {"cart_startobs": 1}, {"detail": ""}], "msg": None}
        self._run_json_equal(url, expected)

    def test__api_normalizeurl_real_9(self):
        "[test_ui_api.py] /__normalizeurl: real 9"
        url = '/opus/__normalizeurl.json?surfacegeometrytargetname=Triton&SURFACEGEOtriton_centerresolution2_102=70&unit-SURFACEGEOtriton_centerresolution_102=km%2Fpixel&time1_101=1989-08-16T00:00:00.000&time2_101=1989-08-26T00:00:00.000&qtype-time_101=any&reqno=68'
        expected = {"new_url": "surfacegeometrytargetname=Triton&SURFACEGEOtriton_centerresolution2=70&unit-SURFACEGEOtriton_centerresolution=km_pixel&time1=1989-08-16T00:00:00.000&time2=1989-08-26T00:00:00.000&qtype-time=any&unit-time=ymdhms&cols=opusid,instrument,planet,target,time1,observationduration&widgets=SURFACEGEOtriton_centerresolution,surfacegeometrytargetname,time&order=time1,opusid&view=search&browse=gallery&cart_browse=gallery&startobs=1&cart_startobs=1&detail=", "new_slugs": [{"surfacegeometrytargetname": "Triton"}, {"SURFACEGEOtriton_centerresolution2": "70"}, {"unit-SURFACEGEOtriton_centerresolution": "km_pixel"}, {"time1": "1989-08-16T00:00:00.000"}, {"time2": "1989-08-26T00:00:00.000"}, {"qtype-time": "any"}, {"unit-time": "ymdhms"}, {"cols": "opusid,instrument,planet,target,time1,observationduration"}, {"widgets": "SURFACEGEOtriton_centerresolution,surfacegeometrytargetname,time"}, {"order": "time1,opusid"}, {"view": "search"}, {"browse": "gallery"}, {"cart_browse": "gallery"}, {"startobs": 1}, {"cart_startobs": 1}, {"detail": ""}], "msg": None}
        self._run_json_equal(url, expected)

# http://pds-rings-tools.seti.org/#/planet=Saturn&typeid=Image&missionid=Voyager&timesec1=1980-09-27T02:16&timesec2=1980-09-28T02:17&qtype-volumeid=contains&view=detail&browse=gallery&colls_browse=gallery&page=1&gallery_data_viewer=true&limit=100&order=time1&cols=ringobsid,planet,target,phase1,phase2,time1,time2&widgets=timesec1&widgets2=&detail=S_IMG_VG1_ISS_3353709_N
# http://pds-rings-tools.seti.org/#/planet=Jupiter&target=EUROPA&missionid=Voyager&view=detail&browse=data&colls_browse=gallery&page=1&gallery_data_viewer=true&limit=100&order=time1&cols=ringobsid,planet,target,phase1,phase2,time1,time2&widgets=missionid,planet,target&widgets2=&detail=J_IMG_VG2_ISS_2076737_N
# https://opus.pds-rings.seti.org/#/mission=Cassini&target=Jupiter,Ganymede,Europa,Callisto,Io&instrument=Cassini+ISS&view=browse&browse=gallery&colls_browse=gallery&page=1&gallery_data_viewer=true&limit=100&order=time1&cols=opusid,instrumentid,planet,target,time1,observationduration&widgets=instrument,mission,planet,target&widgets2=&detail=
