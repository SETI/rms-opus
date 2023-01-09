# opus/application/test_api/test_results_api.py

import json
import logging
import requests
from unittest import TestCase

from django.core.cache import cache
from rest_framework.test import RequestsClient
from opus.application.apps.tools.app_utils import (HTTP404_BAD_LIMIT,
                                                   HTTP404_BAD_OFFSET,
                                                   HTTP404_BAD_PAGENO,
                                                   HTTP404_BAD_STARTOBS,
                                                   HTTP404_SEARCH_PARAMS_INVALID)

from tools.app_utils import (HTTP404_BAD_OR_MISSING_REQNO,
                             HTTP404_UNKNOWN_CATEGORY,
                             HTTP404_UNKNOWN_OPUS_ID,
                             HTTP404_UNKNOWN_RING_OBS_ID,
                             HTTP404_UNKNOWN_SLUG)

from .api_test_helper import ApiTestHelper

import settings

class ApiResultsTests(TestCase, ApiTestHelper):

    def setUp(self):
        # self.UPDATE_FILES = True
        self.maxDiff = None
        settings.OPUS_FAKE_API_DELAYS = 0
        settings.OPUS_FAKE_SERVER_ERROR404_PROBABILITY = 0
        settings.OPUS_FAKE_SERVER_ERROR500_PROBABILITY = 0
        settings.CACHE_KEY_PREFIX = 'opustest:' + settings.DB_SCHEMA_NAME
        logging.disable(logging.ERROR)
        if settings.TEST_GO_LIVE: # pragma: no cover - remote server
            self.client = requests.Session()
        else:
            self.client = RequestsClient()
        cache.clear()

    def tearDown(self):
        logging.disable(logging.NOTSET)


            #############################################
            ######### /api/dataimages API TESTS #########
            #############################################

    def test__api_dataimages_bad_cols(self):
        "[test_results_api.py] /__api/dataimages: bad cols"
        url = '/__api/dataimages.json?cols=xxx,yyy'
        self._run_status_equal(url, 404,
                               HTTP404_UNKNOWN_SLUG('xxx', '/__api/dataimages.json'))

    def test__api_dataimages_bad_order(self):
        "[test_results_api.py] /__api/dataimages: bad order"
        url = '/__api/dataimages.json?order=xxx'
        self._run_status_equal(url, 404,
                               HTTP404_SEARCH_PARAMS_INVALID('/__api/dataimages.json'))

    def test__api_dataimages_bad_search(self):
        "[test_results_api.py] /__api/dataimages: bad search"
        url = '/__api/dataimages.json?time1=xxx-yyy'
        self._run_status_equal(url, 404,
                               HTTP404_SEARCH_PARAMS_INVALID('/__api/dataimages.json'))

    def test__api_dataimages_no_results_default(self):
        "[test_results_api.py] /__api/dataimages: no results default cols"
        url = '/__api/dataimages.json?opusid=notgoodid'
        self._run_status_equal(url, 404,
                               HTTP404_BAD_OR_MISSING_REQNO('/__api/dataimages.json'))

    def test__api_dataimages_no_results_default_reqno(self):
        "[test_results_api.py] /__api/dataimages: no results default cols reqno"
        url = '/__api/dataimages.json?opusid=notgoodid&reqno=5'
        self._run_json_equal_file(url, 'api_dataimages_no_results_default_reqno.json')

    def test__api_dataimages_no_results_default_reqno_bad(self):
        "[test_results_api.py] /__api/dataimages: no results default cols reqno bad"
        url = '/__api/dataimages.json?opusid=notgoodid&reqno=-1'
        self._run_status_equal(url, 404,
                               HTTP404_BAD_OR_MISSING_REQNO('/__api/dataimages.json'))

    def test__api_dataimages_no_results_default_reqno_bad_2(self):
        "[test_results_api.py] /__api/dataimages: no results default cols reqno bad 2"
        url = '/__api/dataimages.json?opusid=notgoodid&reqno=1.0'
        self._run_status_equal(url, 404,
                               HTTP404_BAD_OR_MISSING_REQNO('/__api/dataimages.json'))

    def test__api_dataimages_corss_cols_units(self):
        "[test_results_api.py] /__api/dataimages: corss search & cols & units"
        url = '/__api/dataimages.json?instrument=Cassini+RSS&occdir=Ingress&cols=opusid,instrument,target,time1:ydhms,observationduration:milliseconds,RINGGEOringradius1:saturnradii,RINGGEOringradius2:saturnradii,RINGGEOsolarringelevation1&order=RINGGEOringradius1,-RINGGEOsolarringelevation1,opusid&startobs=5&limit=40&reqno=12'
        self._run_json_equal_file(url, 'api_dataimages_corss_cols_units.json')

    def test__api_dataimages_corss_cols_units_page(self):
        "[test_results_api.py] /__api/dataimages: corss search & cols & units"
        url = '/__api/dataimages.json?instrument=Cassini+RSS&cols=opusid,instrument,target,time1:ydhms,observationduration:milliseconds,RINGGEOringradius1:saturnradii,RINGGEOringradius2:saturnradii,RINGGEOsolarringelevation1&order=RINGGEOringradius1,-RINGGEOsolarringelevation1,opusid&page=1&limit=40&reqno=12'
        self._run_json_equal_file(url, 'api_dataimages_corss_cols_units_page.json')

    def test__api_dataimages_corss_cols_units_cart(self):
        "[test_results_api.py] /__api/dataimages: cart"
        url = '/__cart/reset.json?reqno=42'
        expected = {'recycled_count': 0, 'count': 0, 'reqno': 42}
        self._run_json_equal(url, expected)
        url = '/__cart/addall.json?instrument=Cassini+RSS&reqno=456'
        expected = {'recycled_count': 0, 'count': 204, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/__api/dataimages.json?cols=opusid,instrument,target,time1:ydhms,observationduration:milliseconds,RINGGEOringradius1:saturnradii,RINGGEOringradius2:saturnradii,RINGGEOsolarringelevation1&order=RINGGEOringradius1,-RINGGEOsolarringelevation1,opusid&limit=40&reqno=12&view=cart'
        self._run_json_equal_file(url, 'api_dataimages_corss_cols_units_cart.json')

    def test__api_dataimages_corss_cols_units_cart_recycle(self):
        "[test_results_api.py] /__api/dataimages: cart"
        url = '/__cart/reset.json?reqno=42'
        expected = {'recycled_count': 0, 'count': 0, 'reqno': 42}
        self._run_json_equal(url, expected)
        url = '/__cart/addall.json?instrument=Cassini+RSS&reqno=456'
        expected = {'recycled_count': 0, 'count': 204, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/__cart/remove.json?opusid=co-rss-occ-2005-123-rev007-s43-i&reqno=456&recyclebin=1'
        expected = {'recycled_count': 1, 'count': 203, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/__api/dataimages.json?cols=opusid,instrument,target,time1:ydhms,observationduration:milliseconds,RINGGEOringradius1:saturnradii,RINGGEOringradius2:saturnradii,RINGGEOsolarringelevation1&order=RINGGEOringradius1,-RINGGEOsolarringelevation1,opusid&limit=4000&reqno=12&view=cart'
        self._run_json_equal_file(url, 'api_dataimages_corss_cols_units_cart_recycle.json')

    def test__api_dataimages_corss_startobs_cart(self):
        "[test_results_api.py] /__api/dataimages: cart startobs"
        url = '/__cart/reset.json?reqno=42'
        expected = {'recycled_count': 0, 'count': 0, 'reqno': 42}
        self._run_json_equal(url, expected)
        url = '/__cart/addall.json?instrument=Cassini+RSS&reqno=456'
        expected = {'recycled_count': 0, 'count': 204, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/__api/dataimages.json?cols=opusid,instrument,target,time1:ydhms,observationduration:milliseconds,RINGGEOringradius1:saturnradii,RINGGEOringradius2:saturnradii,RINGGEOsolarringelevation1&order=RINGGEOringradius1,-RINGGEOsolarringelevation1,opusid&cart_startobs=10&limit=40&reqno=12&view=cart'
        self._run_json_equal_file(url, 'api_dataimages_corss_startobs_cart.json')

    def test__api_dataimages_corss_page_cart(self):
        "[test_results_api.py] /__api/dataimages: cart page"
        url = '/__cart/reset.json?reqno=42'
        expected = {'recycled_count': 0, 'count': 0, 'reqno': 42}
        self._run_json_equal(url, expected)
        url = '/__cart/addall.json?instrument=Cassini+RSS&reqno=456'
        expected = {'recycled_count': 0, 'count': 204, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/__api/dataimages.json?cols=opusid,instrument,target,time1:ydhms,observationduration:milliseconds,RINGGEOringradius1:saturnradii,RINGGEOringradius2:saturnradii,RINGGEOsolarringelevation1&order=RINGGEOringradius1,-RINGGEOsolarringelevation1,opusid&page=3&limit=40&reqno=12&view=cart'
        self._run_json_equal_file(url, 'api_dataimages_corss_page_cart.json')

    # fake
    def test__api_dataimages_no_results_default_reqno_fake(self):
        "[test_results_api.py] /__fake/__api/dataimages: fake no results default cols reqno"
        url = '/__fake/__api/dataimages.json?opusid=notgoodid&reqno=5'
        self._run_status_equal(url, 200)


            #######################################
            ######### /api/data API TESTS #########
            #######################################

    def test__api_data_CASSINIrevno_sort(self):
        "[test_results_api.py] /api/data: CASSINIrevno sort"
        url = '/api/data.json?instrument=Cassini+ISS,Cassini+VIMS&CASSINIrevno=000,00A,00B,00C,003&CASSINItargetcode=RI+(Rings+-+general)&limit=5000&order=time1&cols=opusid,CASSINIrevno&order=-CASSINIrevnoint'
        print(url)
        response = self._get_response(url)
        self.assertEqual(response.status_code, 200)
        jdata = json.loads(response.content)
        rev_no_map = {
            '000': 0,
            '00A': 1,
            '00B': 2,
            '00C': 3,
            '003': 4
        }
        rev_nos = [rev_no_map[x[1]] for x in jdata['page']]
        rev_nos2 = rev_nos[:]
        rev_nos2.sort(reverse=True)
        self.assertEqual(rev_nos, rev_nos2)

    def test__api_data_no_results_default_json(self):
        "[test_results_api.py] /api/data: no results default cols json"
        url = '/api/data.json?opusid=notgoodid'
        expected = {}
        self._run_json_equal_file(url, 'api_data_no_results_default_json.json')

    def test__api_data_no_results_default_csv(self):
        "[test_results_api.py] /api/data: no results default cols csv"
        url = '/api/data.csv?opusid=notgoodid'
        self._run_csv_equal_file(url, 'api_data_no_results_default_csv.csv')

    def test__api_data_no_results_default_html(self):
        "[test_results_api.py] /api/data: no results default cols html"
        url = '/api/data.html?opusid=notgoodid'
        self._run_html_equal_file(url, 'api_data_no_results_default_html.html')

    def test__api_data_no_results_empty_cols_json(self):
        "[test_results_api.py] /api/data: no results empty cols json"
        url = '/api/data.json?opusid=notgoodid&cols='
        self._run_json_equal_file(url, 'api_data_no_results_empty_cols_json.json')

    def test__api_data_no_results_empty_cols_csv(self):
        "[test_results_api.py] /api/data: no results empty cols csv"
        url = '/api/data.csv?opusid=notgoodid&cols='
        self._run_csv_equal_file(url, 'api_data_no_results_empty_cols_csv.csv')

    def test__api_data_no_results_empty_cols_html(self):
        "[test_results_api.py] /api/data: no results empty cols html"
        url = '/api/data.html?opusid=notgoodid&cols='
        self._run_html_equal_file(url, 'api_data_no_results_empty_cols_html.html')

    def test__api_data_coiss_2002_more_cols_json(self):
        "[test_results_api.py] /api/data: coiss_2002 more cols json"
        url = '/api/data.json?cols=opusid,instrument,planet,target,time1,observationduration,CASSINIspacecraftclockcount1,CASSINIobsname,CASSINIactivityname,CASSINImissionphasename,CASSINItargetcode,CASSINIrevnoint,CASSINIprimeinst,CASSINIisprime,CASSINIsequenceid,CASSINIspacecraftclockcount2,CASSINIert1,CASSINIert2,COISScamera,COISSfilter,COISSshuttermode,COISSshutterstate,COISScompressiontype,COISSdataconversiontype,COISSgainmode,COISSinstrumentmode,COISSmissinglines,COISSimagenumber,COISStargetdesc,COISSimageobservationtype&volumeid=COISS_2002'
        self._run_json_equal_file(url, 'api_data_coiss_2002_more_cols_json.json')

    def test__api_data_coiss_2002_more_cols_good_startobs_json(self):
        "[test_results_api.py] /api/data: coiss_2002 more cols json good startobs"
        url = '/api/data.json?startobs=52&limit=50&cols=opusid,instrument,planet,target,time1,observationduration,CASSINIspacecraftclockcount1,CASSINIobsname,CASSINIactivityname,CASSINImissionphasename,CASSINItargetcode,CASSINIrevnoint,CASSINIprimeinst,CASSINIisprime,CASSINIsequenceid,CASSINIspacecraftclockcount2,CASSINIert1,CASSINIert2,COISScamera,COISSfilter,COISSshuttermode,COISSshutterstate,COISScompressiontype,COISSdataconversiontype,COISSgainmode,COISSinstrumentmode,COISSmissinglines,COISSimagenumber,COISStargetdesc,COISSimageobservationtype&volumeid=COISS_2002'
        self._run_json_equal_file(url, 'api_data_coiss_2002_more_cols_good_startobs_json.json')

    def test__api_data_coiss_2002_more_cols_bad_startobs_json(self):
        "[test_results_api.py] /api/data: coiss_2002 more cols json bad startobs"
        url = '/api/data.json?startobs=5x2&cols=opusid,instrument,planet,target,time1,observationduration,CASSINIspacecraftclockcount1,CASSINIobsname,CASSINIactivityname,CASSINImissionphasename,CASSINItargetcode,CASSINIrevnoint,CASSINIprimeinst,CASSINIisprime,CASSINIsequenceid,CASSINIspacecraftclockcount2,CASSINIert1,CASSINIert2,COISScamera,COISSfilter,COISSshuttermode,COISSshutterstate,COISScompressiontype,COISSdataconversiontype,COISSgainmode,COISSinstrumentmode,COISSmissinglines,COISSimagenumber,COISStargetdesc,COISSimageobservationtype&volumeid=COISS_2002'
        self._run_status_equal(url, 404,
                               HTTP404_BAD_STARTOBS('5x2', '/api/data.json'))

    def test__api_data_coiss_2002_more_cols_good_page_json(self):
        "[test_results_api.py] /api/data: coiss_2002 more cols json good page"
        url = '/api/data.json?page=5&limit=50&cols=opusid,instrument,planet,target,time1,observationduration,CASSINIspacecraftclockcount1,CASSINIobsname,CASSINIactivityname,CASSINImissionphasename,CASSINItargetcode,CASSINIrevnoint,CASSINIprimeinst,CASSINIisprime,CASSINIsequenceid,CASSINIspacecraftclockcount2,CASSINIert1,CASSINIert2,COISScamera,COISSfilter,COISSshuttermode,COISSshutterstate,COISScompressiontype,COISSdataconversiontype,COISSgainmode,COISSinstrumentmode,COISSmissinglines,COISSimagenumber,COISStargetdesc,COISSimageobservationtype&volumeid=COISS_2002'
        self._run_json_equal_file(url, 'api_data_coiss_2002_more_cols_good_page_json.json')

    def test__api_data_coiss_2002_more_cols_bad_page_json(self):
        "[test_results_api.py] /api/data: coiss_2002 more cols json bad startobs"
        url = '/api/data.json?page=inf&cols=opusid,instrument,planet,target,time1,observationduration,CASSINIspacecraftclockcount1,CASSINIobsname,CASSINIactivityname,CASSINImissionphasename,CASSINItargetcode,CASSINIrevnoint,CASSINIprimeinst,CASSINIisprime,CASSINIsequenceid,CASSINIspacecraftclockcount2,CASSINIert1,CASSINIert2,COISScamera,COISSfilter,COISSshuttermode,COISSshutterstate,COISScompressiontype,COISSdataconversiontype,COISSgainmode,COISSinstrumentmode,COISSmissinglines,COISSimagenumber,COISStargetdesc,COISSimageobservationtype&volumeid=COISS_2002'
        self._run_status_equal(url, 404,
                               HTTP404_BAD_PAGENO('inf', '/api/data.json'))

    def test__api_data_coiss_2002_more_cols_bad_offset_json(self):
        "[test_results_api.py] /api/data: coiss_2002 more cols json bad startobs"
        url = '/api/data.json?page=10000000000000000000&cols=opusid,instrument,planet,target,time1,observationduration,CASSINIspacecraftclockcount1,CASSINIobsname,CASSINIactivityname,CASSINImissionphasename,CASSINItargetcode,CASSINIrevnoint,CASSINIprimeinst,CASSINIisprime,CASSINIsequenceid,CASSINIspacecraftclockcount2,CASSINIert1,CASSINIert2,COISScamera,COISSfilter,COISSshuttermode,COISSshutterstate,COISScompressiontype,COISSdataconversiontype,COISSgainmode,COISSinstrumentmode,COISSmissinglines,COISSimagenumber,COISStargetdesc,COISSimageobservationtype&volumeid=COISS_2002'
        self._run_status_equal(url, 404,
                               HTTP404_BAD_OFFSET('999999999999999999900',
                                                  '/api/data.json'))

    def test__api_data_coiss_2002_more_cols_csv(self):
        "[test_results_api.py] /api/data: coiss_2002 more cols csv"
        url = '/api/data.csv?cols=opusid,instrument,planet,target,time1,observationduration,CASSINIspacecraftclockcount1,CASSINIobsname,CASSINIactivityname,CASSINImissionphasename,CASSINItargetcode,CASSINIrevnoint,CASSINIprimeinst,CASSINIisprime,CASSINIsequenceid,CASSINIspacecraftclockcount2,CASSINIert1,CASSINIert2,COISScamera,COISSfilter,COISSshuttermode,COISSshutterstate,COISScompressiontype,COISSdataconversiontype,COISSgainmode,COISSinstrumentmode,COISSmissinglines,COISSimagenumber,COISStargetdesc,COISSimageobservationtype&volumeid=COISS_2002'
        self._run_csv_equal_file(url, 'api_data_coiss_2002_more_cols_csv.csv')

    def test__api_data_coiss_2002_more_cols_units_csv(self):
        "[test_results_api.py] /api/data: coiss_2002 more cols units csv"
        url = '/api/data.csv?cols=opusid,instrument,planet,target,time1:jd,observationduration:milliseconds,CASSINIspacecraftclockcount1,CASSINIobsname,CASSINIactivityname,CASSINImissionphasename,CASSINItargetcode,CASSINIrevnoint,CASSINIprimeinst,CASSINIisprime,CASSINIsequenceid,CASSINIspacecraftclockcount2,CASSINIert1,CASSINIert2,COISScamera,COISSfilter,COISSshuttermode,COISSshutterstate,COISScompressiontype,COISSdataconversiontype,COISSgainmode,COISSinstrumentmode,COISSmissinglines,COISSimagenumber,COISStargetdesc,COISSimageobservationtype&volumeid=COISS_2002'
        self._run_csv_equal_file(url, 'api_data_coiss_2002_more_cols_units_csv.csv')

    def test__api_data_coiss_2002_more_cols_html(self):
        "[test_results_api.py] /api/data: coiss_2002 more cols html"
        url = '/api/data.html?cols=opusid,instrument,planet,target,time1,observationduration,CASSINIspacecraftclockcount1,CASSINIobsname,CASSINIactivityname,CASSINImissionphasename,CASSINItargetcode,CASSINIrevnoint,CASSINIprimeinst,CASSINIisprime,CASSINIsequenceid,CASSINIspacecraftclockcount2,CASSINIert1,CASSINIert2,COISScamera,COISSfilter,COISSshuttermode,COISSshutterstate,COISScompressiontype,COISSdataconversiontype,COISSgainmode,COISSinstrumentmode,COISSmissinglines,COISSimagenumber,COISStargetdesc,COISSimageobservationtype&volumeid=COISS_2002'
        self._run_html_equal_file(url, 'api_data_coiss_2002_more_cols_html.html')

    def test__api_data_coiss_2002_more_cols_units_html(self):
        "[test_results_api.py] /api/data: coiss_2002 more cols units html"
        url = '/api/data.html?cols=opusid,instrument,planet,target,time1:jd,observationduration:milliseconds,CASSINIspacecraftclockcount1,CASSINIobsname,CASSINIactivityname,CASSINImissionphasename,CASSINItargetcode,CASSINIrevnoint,CASSINIprimeinst,CASSINIisprime,CASSINIsequenceid,CASSINIspacecraftclockcount2,CASSINIert1,CASSINIert2,COISScamera,COISSfilter,COISSshuttermode,COISSshutterstate,COISScompressiontype,COISSdataconversiontype,COISSgainmode,COISSinstrumentmode,COISSmissinglines,COISSimagenumber,COISStargetdesc,COISSimageobservationtype&volumeid=COISS_2002'
        self._run_html_equal_file(url, 'api_data_coiss_2002_more_cols_units_html.html')

    def test__api_data_coiss_2002_more_cols_units_json(self):
        "[test_results_api.py] /api/data: coiss_2002 more cols units json"
        url = '/api/data.json?cols=opusid,instrument,planet,target,time1:jd,observationduration:milliseconds,CASSINIspacecraftclockcount1,CASSINIobsname,CASSINIactivityname,CASSINImissionphasename,CASSINItargetcode,CASSINIrevnoint,CASSINIprimeinst,CASSINIisprime,CASSINIsequenceid,CASSINIspacecraftclockcount2,CASSINIert1,CASSINIert2,COISScamera,COISSfilter,COISSshuttermode,COISSshutterstate,COISScompressiontype,COISSdataconversiontype,COISSgainmode,COISSinstrumentmode,COISSmissinglines,COISSimagenumber,COISStargetdesc,COISSimageobservationtype&volumeid=COISS_2002'
        self._run_json_equal_file(url, 'api_data_coiss_2002_more_cols_units_json.json')

    def test__api_data_gossi_cols_units_order_target_json(self):
        "[test_results_api.py] /api/data: gossi cols units order target json"
        url = '/api/data.json?duration1=0.5&duration2=15&unit-duration=seconds&GOSSIfilter=Methane+%5BIR-8890%5D&instrument=Galileo+SSI&cols=opusid,target,time1,time1:et,observationduration:milliseconds,duration,GOSSIfilter,wavelength1:angstroms,wavelength2:nm&order=target,-observationduration,time1,opusid'
        self._run_json_equal_file(url, 'api_data_gossi_cols_units_order_target_json.json')

    def test__api_data_gossi_order_target_cart_json(self):
        "[test_results_api.py] /api/data: gossi order target cart json"
        url = '/__cart/addall.json?volumeid=GO_0017&order=target,-observationduration,time1,opusid&reqno=456'
        expected = {'recycled_count': 0, 'count': 479, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/__cart/remove.json?opusid=go-ssi-c0347996200&recyclebin=1&reqno=456'
        expected = {'recycled_count': 1, 'count': 478, 'error': False, 'reqno': 456}
        self._run_json_equal(url, expected)
        url = '/api/data.json?order=target,-observationduration,time1,opusid&view=cart&limit=all&reqno=456'
        self._run_json_equal_file(url, 'api_data_gossi_order_target_cart_json.json')

    def test__api_data_limit_all_csv(self):
        "[test_results_api.py] /api/data: limit all"
        url = '/api/data.csv?volumeid=CORSS_8001&cols=time1,time2&limit=all'
        self._run_csv_equal_file(url, 'api_data_limit_all_csv.csv')

    def test__api_data_limit_bad_csv(self):
        "[test_results_api.py] /api/data: limit bad"
        url = '/api/data.csv?volumeid=CORSS_8001&cols=time1,time2&limit=3x2'
        self._run_status_equal(url, 404,
                               HTTP404_BAD_LIMIT('3x2', '/api/data.csv'))

    def test__api_data_limit_big_csv(self):
        "[test_results_api.py] /api/data: limit big"
        url = '/api/data.csv?volumeid=CORSS_8001&cols=time1,time2&limit=999999999999999999999999'
        self._run_status_equal(url, 404,
                               HTTP404_BAD_LIMIT('999999999999999999999999',
                                                 '/api/data.csv'))

    def test__api_data_good_regex_opusid_csv(self):
        "[test_results_api.py] /api/data: good regex opusid csv"
        url = r'/api/data.csv?opusid=co-iss-n14609\d0\d5.*&qtype-opusid=regex'
        self._run_csv_equal_file(url, 'api_data_good_regex_opusid_csv.csv')

    def test__api_data_bad_regex_opusid_csv(self):
        "[test_results_api.py] /api/data: bad regex csv"
        url = r'/api/data.csv?opusid=[a-z]*(&qtype-opusid=regex'
        self._run_status_equal(url, 404,
                               HTTP404_SEARCH_PARAMS_INVALID('/api/data.csv'))

    def test__api_data_bad_cols_json(self):
        "[test_results_api.py] /api/data: bad cols 1 json"
        url = '/api/data.json?volumeid=COISS_2002&cols=observationduration,fredethel,volumeid'
        self._run_status_equal(url, 404,
                               HTTP404_UNKNOWN_SLUG(None, '/api/data.json'))

    def test__api_data_bad_cols_csv(self):
        "[test_results_api.py] /api/data: bad cols 1 csv"
        url = '/api/data.csv?volumeid=COISS_2002&cols=observationduration,fredethel,volumeid'
        self._run_status_equal(url, 404,
                               HTTP404_UNKNOWN_SLUG(None, '/api/data.csv'))

    def test__api_data_bad_cols_html(self):
        "[test_results_api.py] /api/data: bad cols 1 html"
        url = '/api/data.html?volumeid=COISS_2002&cols=observationduration,fredethel,volumeid'
        self._run_status_equal(url, 404,
                               HTTP404_UNKNOWN_SLUG(None, '/api/data.html'))

    def test__api_data_bad_cols2_json(self):
        "[test_results_api.py] /api/data: bad cols 2 json"
        url = '/api/data.json?volumeid=COISS_2002&cols=,observationduration,volumeid'
        self._run_status_equal(url, 404,
                               HTTP404_UNKNOWN_SLUG(None, '/api/data.json'))

    def test__api_data_bad_cols3_json(self):
        "[test_results_api.py] /api/data: bad cols 3 json"
        url = '/api/data.json?volumeid=COISS_2002&cols=observationduration,,volumeid'
        self._run_status_equal(url, 404,
                               HTTP404_UNKNOWN_SLUG(None, '/api/data.json'))

    def test__api_data_bad_cols4_json(self):
        "[test_results_api.py] /api/data: bad cols 4 json"
        url = '/api/data.json?volumeid=COISS_2002&cols=observationduration,volumeid,'
        self._run_status_equal(url, 404,
                               HTTP404_UNKNOWN_SLUG(None, '/api/data.json'))


            ################################################
            ######### /api/metadata[_v2] API TESTS #########
            ################################################

    # All metadata
    def test__api_metadata_vg_iss_2_s_c4360845_default_page_json(self):
        "[test_results_api.py] /api/metadata: vg-iss-2-s-c4360845 default page json"
        url = '/api/metadata/vg-iss-2-s-c4360845.json?page=5'
        self._run_json_equal_file(url, 'api_metadata_vg_iss_2_s_c4360845_default_json.json')

    def test__api_metadata_vg_iss_2_s_c4360845_default_startobs_json(self):
        "[test_results_api.py] /api/metadata: vg-iss-2-s-c4360845 default startobs json"
        url = '/api/metadata/vg-iss-2-s-c4360845.json?startobs=500'
        self._run_json_equal_file(url, 'api_metadata_vg_iss_2_s_c4360845_default_json.json')

    def test__api_metadata_vg_iss_2_s_c4360845_default_page_startobs_limit_json(self):
        "[test_results_api.py] /api/metadata: vg-iss-2-s-c4360845 default page startobs limit json"
        url = '/api/metadata/vg-iss-2-s-c4360845.json?page=8&startobs=500&limit=500'
        self._run_json_equal_file(url, 'api_metadata_vg_iss_2_s_c4360845_default_json.json')

    def test__api_metadata_vg_iss_2_s_c4360845_default_json(self):
        "[test_results_api.py] /api/metadata_v2: vg-iss-2-s-c4360845 default json"
        url = '/api/metadata/vg-iss-2-s-c4360845.json'
        self._run_json_equal_file(url, 'api_metadata_vg_iss_2_s_c4360845_default_json.json')

    def test__api_metadata_vg_iss_2_s_c4360845_default_json_ringobsid(self):
        "[test_results_api.py] /api/metadata_v2: S_IMG_VG2_ISS_4360845_N default json"
        url = '/api/metadata/S_IMG_VG2_ISS_4360845_N.json'
        self._run_json_equal_file(url, 'api_metadata_vg_iss_2_s_c4360845_default_json.json')

    def test__api_metadata_vg_iss_2_s_c4360845_default_html(self):
        "[test_results_api.py] /api/metadata_v2: vg-iss-2-s-c4360845 default html"
        url = '/api/metadata/vg-iss-2-s-c4360845.html'
        self._run_html_equal_file(url, 'api_metadata_vg_iss_2_s_c4360845_default_html.html')

    def test__api_metadata_vg_iss_2_s_c4360845_default_html_private(self):
        "[test_results_api.py] /api/metadata_v2: vg-iss-2-s-c4360845 default html private"
        url = '/__api/metadata/vg-iss-2-s-c4360845.html'
        self._run_html_equal_file(url, 'api_metadata_vg_iss_2_s_c4360845_default_html_private.html')
 
    def test__api_metadata_vg_iss_2_s_c4360845_default_csv(self):
        "[test_results_api.py] /api/metadata_v2: vg-iss-2-s-c4360845 default csv"
        url = '/api/metadata/vg-iss-2-s-c4360845.csv'
        self._run_csv_equal_file(url, 'api_metadata_vg_iss_2_s_c4360845_default_csv.csv')

    # Specified columns, empty
    def test__api_metadata_vg_iss_2_s_c4360845_cols_empty_json(self):
        "[test_results_api.py] /api/metadata_v2: vg-iss-2-s-c4360845 cols empty json"
        url = '/api/metadata/vg-iss-2-s-c4360845.json?cols='
        self._run_json_equal_file(url, 'api_metadata_vg_iss_2_s_c4360845_cols_empty_json.json')

    def test__api_metadata_vg_iss_2_s_c4360845_cols_empty_html(self):
        "[test_results_api.py] /api/metadata_v2: vg-iss-2-s-c4360845 cols empty html"
        url = '/api/metadata/vg-iss-2-s-c4360845.html?cols='
        self._run_html_equal_file(url, 'api_metadata_vg_iss_2_s_c4360845_cols_empty_html.html')

    def test__api_metadata_vg_iss_2_s_c4360845_cols_empty_html_private(self):
        "[test_results_api.py] /api/metadata_v2: vg-iss-2-s-c4360845 cols empty html private"
        url = '/__api/metadata/vg-iss-2-s-c4360845.html?cols='
        self._run_html_equal_file(url, 'api_metadata_vg_iss_2_s_c4360845_cols_empty_html_private.html')

    def test__api_metadata_vg_iss_2_s_c4360845_cols_empty_csv(self):
        "[test_results_api.py] /api/metadata_v2: vg-iss-2-s-c4360845 cols empty csv"
        url = '/api/metadata/vg-iss-2-s-c4360845.csv?cols='
        self._run_csv_equal_file(url, 'api_metadata_vg_iss_2_s_c4360845_cols_empty_csv.csv')

    # Specified columns, opusid only
    def test__api_metadata_vg_iss_2_s_c4360845_cols_opusid_json(self):
        "[test_results_api.py] /api/metadata_v2: vg-iss-2-s-c4360845 cols opusid json"
        url = '/api/metadata/vg-iss-2-s-c4360845.json?cols=opusid'
        self._run_json_equal_file(url, 'api_metadata_vg_iss_2_s_c4360845_cols_opusid_json.json')

    def test__api_metadata_nh_lorri_lor_0284457489_cols_opusid_json(self):
        "[test_results_api.py] /api/metadata_v2: nh-lorri-lor_0284457489 cols opusid json"
        # Check an OPUS ID with a _ in it which can screw up database searches
        url = '/api/metadata/nh-lorri-lor_0284457489.json?cols=opusid'
        self._run_json_equal_file(url, 'api_metadata_nh_lorri_lor_0284457489_cols_opusid_json.json')

    def test__api_metadata_vg_iss_2_s_c4360845_cols_opusid_html(self):
        "[test_results_api.py] /api/metadata_v2: vg-iss-2-s-c4360845 cols opusid html"
        url = '/api/metadata/vg-iss-2-s-c4360845.html?cols=opusid'
        self._run_html_equal_file(url, 'api_metadata_vg_iss_2_s_c4360845_cols_opusid_html.html')

    def test__api_metadata_vg_iss_2_s_c4360845_cols_opusid_html_private(self):
        "[test_results_api.py] /api/metadata_v2: vg-iss-2-s-c4360845 cols opusid html private"
        url = '/__api/metadata/vg-iss-2-s-c4360845.html?cols=opusid'
        self._run_html_equal_file(url, 'api_metadata_vg_iss_2_s_c4360845_cols_opusid_html_private.html')

    def test__api_metadata_vg_iss_2_s_c4360845_cols_opusid_csv(self):
        "[test_results_api.py] /api/metadata_v2: vg-iss-2-s-c4360845 cols opusid csv"
        url = '/api/metadata/vg-iss-2-s-c4360845.csv?cols=opusid'
        self._run_csv_equal_file(url, 'api_metadata_vg_iss_2_s_c4360845_cols_opusid_csv.csv')

    # Specified columns, all Voyager or Cassini slugs
    def test__api_metadata_vg_iss_2_s_c4365507_cols_all_voyager_json(self):
        "[test_results_api.py] /api/metadata_v2: vg-iss-2-s-c4365507 cols all voyager json"
        url = '/api/metadata/vg-iss-2-s-c4365507.json?cols=opusid,VOYAGERmissionphasename,VOYAGERspacecraftclockcount1,VOYAGERspacecraftclockcount2,VOYAGERert,VGISScamera,VGISSfilter,VGISSfilternumber,VGISSshuttermode,VGISSeditmode,VGISSgainmode,VGISSscanmode,VGISSimageid,VGISSusablelines,VGISSusablesamples'
        self._run_json_equal_file(url, 'api_metadata_vg_iss_2_s_c4365507_cols_all_voyager_json.json')

    def test__api_metadata_vg_iss_2_s_c4365507_cols_all_cassini_startobs_json(self):
        "[test_results_api.py] /api/metadata: vg-iss-2-s-c4365507 cols all cassini startobs json"
        url = '/api/metadata/vg-iss-2-s-c4365507.json?startobs=800&cols=opusid,volumeid,greaterpixelsize,lesserpixelsize,wavelength1,wavelength2,CASSINIobsname,CASSINIactivityname,CASSINImissionphasename,CASSINItargetcode,CASSINIrevnoint,CASSINIprimeinst,CASSINIisprime,CASSINIsequenceid,CASSINIspacecraftclockcount1,CASSINIspacecraftclockcount2,CASSINIert1,CASSINIert2'
        self._run_json_equal_file(url, 'api_metadata_vg_iss_2_s_c4365507_cols_all_cassini_json.json')

    def test__api_metadata_vg_iss_2_s_c4365507_cols_all_cassini_pagestartobslimit_json(self):
        "[test_results_api.py] /api/metadata: vg-iss-2-s-c4365507 cols all cassini page startobs limit json"
        url = '/api/metadata/vg-iss-2-s-c4365507.json?page=8&startobs=800&limit=0&cols=opusid,volumeid,greaterpixelsize,lesserpixelsize,wavelength1,wavelength2,CASSINIobsname,CASSINIactivityname,CASSINImissionphasename,CASSINItargetcode,CASSINIrevnoint,CASSINIprimeinst,CASSINIisprime,CASSINIsequenceid,CASSINIspacecraftclockcount1,CASSINIspacecraftclockcount2,CASSINIert1,CASSINIert2'
        self._run_json_equal_file(url, 'api_metadata_vg_iss_2_s_c4365507_cols_all_cassini_json.json')

    def test__api_metadata_vg_iss_2_s_c4365507_cols_all_cassini_json(self):
        "[test_results_api.py] /api/metadata_v2: vg-iss-2-s-c4365507 cols all cassini json"
        url = '/api/metadata/vg-iss-2-s-c4365507.json?cols=opusid,volumeid,greaterpixelsize,lesserpixelsize,wavelength1,wavelength2,CASSINIobsname,CASSINIactivityname,CASSINImissionphasename,CASSINItargetcode,CASSINIrevnoint,CASSINIprimeinst,CASSINIisprime,CASSINIsequenceid,CASSINIspacecraftclockcount1,CASSINIspacecraftclockcount2,CASSINIert1,CASSINIert2'
        self._run_json_equal_file(url, 'api_metadata_vg_iss_2_s_c4365507_cols_all_cassini_json.json')

    def test__api_metadata_vg_iss_2_s_c4365507_cols_all_cassini_page_json(self):
        "[test_results_api.py] /api/metadata: vg-iss-2-s-c4365507 cols all cassini page json"
        url = '/api/metadata/vg-iss-2-s-c4365507.json?page=8&cols=opusid,volumeid,greaterpixelsize,lesserpixelsize,wavelength1,wavelength2,CASSINIobsname,CASSINIactivityname,CASSINImissionphasename,CASSINItargetcode,CASSINIrevnoint,CASSINIprimeinst,CASSINIisprime,CASSINIsequenceid,CASSINIspacecraftclockcount1,CASSINIspacecraftclockcount2,CASSINIert1,CASSINIert2'
        self._run_json_equal_file(url, 'api_metadata_vg_iss_2_s_c4365507_cols_all_cassini_json.json')

    def test__api_metadata_vg_iss_2_s_c4365507_cols_all_voyager_html(self):
        "[test_results_api.py] /api/metadata_v2: vg-iss-2-s-c4365507 cols all voyager html"
        url = '/api/metadata/vg-iss-2-s-c4365507.html?cols=opusid,VOYAGERmissionphasename,VOYAGERspacecraftclockcount1,VOYAGERspacecraftclockcount2,VOYAGERert,VGISScamera,VGISSfilter,VGISSfilternumber,VGISSshuttermode,VGISSeditmode,VGISSgainmode,VGISSscanmode,VGISSimageid,VGISSusablelines,VGISSusablesamples'
        self._run_html_equal_file(url, 'api_metadata_vg_iss_2_s_c4365507_cols_all_voyager_html.html')

    def test__api_metadata_vg_iss_2_s_c4365507_cols_all_cassini_html(self):
        "[test_results_api.py] /api/metadata_v2: vg-iss-2-s-c4365507 cols all cassini html"
        url = '/api/metadata/vg-iss-2-s-c4365507.html?cols=opusid,volumeid,greaterpixelsize,lesserpixelsize,wavelength1,wavelength2,CASSINIobsname,CASSINIactivityname,CASSINImissionphasename,CASSINItargetcode,CASSINIrevnoint,CASSINIprimeinst,CASSINIisprime,CASSINIsequenceid,CASSINIspacecraftclockcount1,CASSINIspacecraftclockcount2,CASSINIert1,CASSINIert2'
        self._run_html_equal_file(url, 'api_metadata_vg_iss_2_s_c4365507_cols_all_cassini_html.html')

    def test__api_metadata_vg_iss_2_s_c4365507_cols_all_voyager_csv(self):
        "[test_results_api.py] /api/metadata_v2: vg-iss-2-s-c4365507 cols all voyager csv"
        url = '/api/metadata/vg-iss-2-s-c4365507.csv?cols=opusid,VOYAGERmissionphasename,VOYAGERspacecraftclockcount1,VOYAGERspacecraftclockcount2,VOYAGERert,VGISScamera,VGISSfilter,VGISSfilternumber,VGISSshuttermode,VGISSeditmode,VGISSgainmode,VGISSscanmode,VGISSimageid,VGISSusablelines,VGISSusablesamples'
        self._run_csv_equal_file(url, 'api_metadata_vg_iss_2_s_c4365507_cols_all_voyager_csv.csv')

    def test__api_metadata_vg_iss_2_s_c4365507_cols_all_cassini_csv(self):
        "[test_results_api.py] /api/metadata_v2: vg-iss-2-s-c4365507 cols all cassini csv"
        url = '/api/metadata/vg-iss-2-s-c4365507.csv?cols=opusid,volumeid,greaterpixelsize,lesserpixelsize,wavelength1,wavelength2,CASSINIobsname,CASSINIactivityname,CASSINImissionphasename,CASSINItargetcode,CASSINIrevnoint,CASSINIprimeinst,CASSINIisprime,CASSINIsequenceid,CASSINIspacecraftclockcount1,CASSINIspacecraftclockcount2,CASSINIert1,CASSINIert2'
        self._run_csv_equal_file(url, 'api_metadata_vg_iss_2_s_c4365507_cols_all_cassini_csv.csv')

    # Specified cats, empty
    def test__api_metadata_hst_09975_acs_j8n410lbq_cats_empty_json(self):
        "[test_results_api.py] /api/metadata_v2: hst-09975-acs-j8n410lbq cats empty json"
        url = '/api/metadata/hst-09975-acs-j8n410lbq.json?cats='
        self._run_json_equal_file(url, 'api_metadata_hst_09975_acs_j8n410lbq_cats_empty_json.json')

    def test__api_metadata_hst_09975_acs_j8n410lbq_cats_empty_html(self):
        "[test_results_api.py] /api/metadata_v2: hst-09975-acs-j8n410lbq cats empty html"
        url = '/api/metadata/hst-09975-acs-j8n410lbq.html?cats='
        self._run_html_equal_file(url, 'api_metadata_hst_09975_acs_j8n410lbq_cats_empty_html.html')

    def test__api_metadata_hst_09975_acs_j8n410lbq_cats_empty_csv(self):
        "[test_results_api.py] /api/metadata_v2: hst-09975-acs-j8n410lbq cats empty csv"
        url = '/api/metadata/hst-09975-acs-j8n410lbq.csv?cats='
        self._run_csv_equal_file(url, 'api_metadata_hst_09975_acs_j8n410lbq_cats_empty_csv.csv')

    # Specified cats, PDS Constraints only
    def test__api_metadata_hst_09975_acs_j8n410lbq_cats_pds_constraints_lc_json(self):
        "[test_results_api.py] /api/metadata: hst-09975-acs-j8n410lbq cats pds constraints json"
        url = '/api/metadata/hst-09975-acs-j8n410lbq.json?cats=pds+CONSTRAINTS'
        self._run_json_equal_file(url, 'api_metadata_hst_09975_acs_j8n410lbq_cats_pds_constraints_json.json')

    def test__api_metadata_hst_09975_acs_j8n410lbq_cats_pds_constraints_table_json(self):
        "[test_results_api.py] /api/metadata: hst-09975-acs-j8n410lbq cats pds constraints json"
        url = '/api/metadata/hst-09975-acs-j8n410lbq.json?cats=obs_pds'
        self._run_json_equal_file(url, 'api_metadata_hst_09975_acs_j8n410lbq_cats_pds_constraints_json.json')

    def test__api_metadata_hst_09975_acs_j8n410lbq_cats_pds_constraints_table2_json(self):
        "[test_results_api.py] /api/metadata: hst-09975-acs-j8n410lbq cats pds constraints dup json"
        url = '/api/metadata/hst-09975-acs-j8n410lbq.json?cats=obs_pds,obs_pds'
        self._run_json_equal_file(url, 'api_metadata_hst_09975_acs_j8n410lbq_cats_pds_constraints_json.json')

    def test__api_metadata_hst_09975_acs_j8n410lbq_cats_pds_constraints_json(self):
        "[test_results_api.py] /api/metadata_v2: hst-09975-acs-j8n410lbq cats PDS Constraints json"
        url = '/api/metadata/hst-09975-acs-j8n410lbq.json?cats=PDS+Constraints'
        self._run_json_equal_file(url, 'api_metadata_hst_09975_acs_j8n410lbq_cats_pds_constraints_json.json')

    def test__api_metadata_hst_09975_acs_j8n410lbq_cats_pds_constraints_html(self):
        "[test_results_api.py] /api/metadata_v2: hst-09975-acs-j8n410lbq cats PDS Constraints html"
        url = '/api/metadata/hst-09975-acs-j8n410lbq.html?cats=PDS+Constraints'
        self._run_html_equal_file(url, 'api_metadata_hst_09975_acs_j8n410lbq_cats_pds_constraints_html.html')

    def test__api_metadata_hst_09975_acs_j8n410lbq_cats_pds_constraints_csv(self):
        "[test_results_api.py] /api/metadata_v2: hst-09975-acs-j8n410lbq cats PDS Constraints csv"
        url = '/api/metadata/hst-09975-acs-j8n410lbq.csv?cats=PDS+Constraints'
        self._run_csv_equal_file(url, 'api_metadata_hst_09975_acs_j8n410lbq_cats_pds_constraints_csv.csv')

    # Specified cats, PDS, Hubble Constraints
    def test__api_metadata_hst_09975_acs_j8n410lbq_cats_pds_hubble_constraints_lc_json(self):
        "[test_results_api.py] /api/metadata: hst-09975-acs-j8n410lbq cats PDS, Hubble Constraints json"
        url = '/api/metadata/hst-09975-acs-j8n410lbq.json?cats=PDS+Constraints,Hubble+Mission+Constraints'
        self._run_json_equal_file(url, 'api_metadata_hst_09975_acs_j8n410lbq_cats_pds_hubble_constraints_json.json')

    def test__api_metadata_hst_09975_acs_j8n410lbq_cats_pds_hubble_constraints_table_json(self):
        "[test_results_api.py] /api/metadata: hst-09975-acs-j8n410lbq cats PDS, Hubble Constraints json"
        url = '/api/metadata/hst-09975-acs-j8n410lbq.json?cats=obs_pds,obs_mission_hubble'
        self._run_json_equal_file(url, 'api_metadata_hst_09975_acs_j8n410lbq_cats_pds_hubble_constraints_json.json')

    def test__api_metadata_hst_09975_acs_j8n410lbq_cats_pds_hubble_constraints_table2_json(self):
        "[test_results_api.py] /api/metadata: hst-09975-acs-j8n410lbq cats PDS, Hubble Constraints rev json"
        url = '/api/metadata/hst-09975-acs-j8n410lbq.json?cats=obs_mission_hubble,obs_pds'
        self._run_json_equal_file(url, 'api_metadata_hst_09975_acs_j8n410lbq_cats_pds_hubble_constraints_json.json')

    def test__api_metadata_hst_09975_acs_j8n410lbq_cats_pds_hubble_constraints_json(self):
        "[test_results_api.py] /api/metadata_v2: hst-09975-acs-j8n410lbq cats PDS, Hubble Constraints json"
        url = '/api/metadata/hst-09975-acs-j8n410lbq.json?cats=PDS+Constraints,Hubble+Mission+Constraints'
        self._run_json_equal_file(url, 'api_metadata_hst_09975_acs_j8n410lbq_cats_pds_hubble_constraints_json.json')

    def test__api_metadata_hst_09975_acs_j8n410lbq_cats_pds_hubble_constraints_html(self):
        "[test_results_api.py] /api/metadata_v2: hst-09975-acs-j8n410lbq cats PDS, Hubble Constraints html"
        url = '/api/metadata/hst-09975-acs-j8n410lbq.html?cats=PDS+Constraints,Hubble+Mission+Constraints'
        self._run_html_equal_file(url, 'api_metadata_hst_09975_acs_j8n410lbq_cats_pds_hubble_constraints_html.html')

    def test__api_metadata_hst_09975_acs_j8n410lbq_cats_pds_hubble_constraints_csv(self):
        "[test_results_api.py] /api/metadata_v2: hst-09975-acs-j8n410lbq cats PDS, Hubble Constraints csv"
        url = '/api/metadata/hst-09975-acs-j8n410lbq.csv?cats=PDS+Constraints,Hubble+Mission+Constraints'
        self._run_csv_equal_file(url, 'api_metadata_hst_09975_acs_j8n410lbq_cats_pds_hubble_constraints_csv.csv')

    # Bad queries
    def test__api_metadata_bad_opusid_json(self):
        "[test_results_api.py] /api/metadata: bad opusid json"
        url = '/api/metadata/vg-iss-2-s-c4360845x.json'
        self._run_status_equal(url, 404,
                               HTTP404_UNKNOWN_OPUS_ID('vg-iss-2-s-c4360845x',
                                   '/api/metadata/vg-iss-2-s-c4360845x.json'))

    def test__api_metadata_bad_ringobsid_json(self):
        "[test_results_api.py] /api/metadata: bad ringobsid json"
        url = '/api/metadata/S_IMG_VG2_ISS_4360846_N.json'
        self._run_status_equal(url, 404,
                               HTTP404_UNKNOWN_RING_OBS_ID('S_IMG_VG2_ISS_4360846_N',
                                   '/api/metadata/S_IMG_VG2_ISS_4360846_N.json'))

    def test__api_metadata2_bad_opusid_json(self):
        "[test_results_api.py] /api/metadata_v2: bad opusid json"
        url = '/api/metadata_v2/vg-iss-2-s-,c4360845.json'
        self._run_status_equal(url, 404)

    def test__api_metadata2_bad_ringobsid_json(self):
        "[test_results_api.py] /api/metadata_v2: bad ringobsid json"
        url = '/api/metadata_v2/S_IMG_VG2_ISS_4360846_N.json'
        self._run_status_equal(url, 404,
                               HTTP404_UNKNOWN_RING_OBS_ID('S_IMG_VG2_ISS_4360846_N',
                                   '/api/metadata_v2/S_IMG_VG2_ISS_4360846_N.json'))

    def test__api_metadata_bad_opusid_html(self):
        "[test_results_api.py] /api/metadata: bad opusid html"
        url = '/api/metadata/vg-iss-2s-c4360845.html'
        self._run_status_equal(url, 404,
                               HTTP404_UNKNOWN_OPUS_ID('vg-iss-2s-c4360845',
                                   '/api/metadata/vg-iss-2s-c4360845.html'))

    def test__api_metadata_bad_opusid_html_v2(self):
        "[test_results_api.py] /api/metadata_v2: bad opusid html v2"
        url = '/api/metadata/,,,.html'
        self._run_status_equal(url, 404)

    def test__api_metadata_bad_opusid_csv(self):
        "[test_results_api.py] /api/metadata: bad opusid csv"
        url = '/api/metadata/0124.csv'
        self._run_status_equal(url, 404,
                               HTTP404_UNKNOWN_OPUS_ID('0124', '/api/metadata/0124.csv'))

    def test__api_metadata_bad_opusid_csv_v2(self):
        "[test_results_api.py] /api/metadata_v2: bad opusid csv v2"
        url = '/api/metadata/1.csv'
        self._run_status_equal(url, 404,
                               HTTP404_UNKNOWN_OPUS_ID('1', '/api/metadata/1.csv'))

    def test__api_metadata_bad_cols_json(self):
        "[test_results_api.py] /api/metadata: bad cols 1 json"
        url = '/api/metadata/vg-iss-2-s-c4360845.json?cols=observationduration,fredethel,volumeid'
        self._run_status_equal(url, 404,
                               HTTP404_UNKNOWN_SLUG('fredethel',
                                   '/api/metadata/vg-iss-2-s-c4360845.json'))

    def test__api_metadata_bad_cols_csv(self):
        "[test_results_api.py] /api/metadata: bad cols 1 csv"
        url = '/api/metadata/vg-iss-2-s-c4360845.csv?cols=observationduration,fredethel,volumeid'
        self._run_status_equal(url, 404,
                               HTTP404_UNKNOWN_SLUG('fredethel',
                                   '/api/metadata/vg-iss-2-s-c4360845.csv'))

    def test__api_metadata_bad_cols_html(self):
        "[test_results_api.py] /api/metadata: bad cols 1 html"
        url = '/api/metadata/vg-iss-2-s-c4360845.html?cols=observationduration,fredethel,volumeid'
        self._run_status_equal(url, 404,
                               HTTP404_UNKNOWN_SLUG('fredethel',
                                   '/api/metadata/vg-iss-2-s-c4360845.html'))

    def test__api_metadata_bad_cols2_json(self):
        "[test_results_api.py] /api/metadata: bad cols 2 json"
        url = '/api/metadata/vg-iss-2-s-c4360845.json?cols=,observationduration,volumeid'
        self._run_status_equal(url, 404,
                               HTTP404_UNKNOWN_SLUG('',
                                   '/api/metadata/vg-iss-2-s-c4360845.json'))

    def test__api_metadata_bad_cols3_json(self):
        "[test_results_api.py] /api/metadata: bad cols 3 json"
        url = '/api/metadata/vg-iss-2-s-c4360845.json?cols=observationduration,,volumeid'
        self._run_status_equal(url, 404,
                               HTTP404_UNKNOWN_SLUG('',
                                   '/api/metadata/vg-iss-2-s-c4360845.json'))

    def test__api_metadata_bad_cols4_json(self):
        "[test_results_api.py] /api/metadata: bad cols 4 json"
        url = '/api/metadata/vg-iss-2-s-c4360845.json?cols=observationduration,volumeid,'
        self._run_status_equal(url, 404,
                               HTTP404_UNKNOWN_SLUG('',
                                   '/api/metadata/vg-iss-2-s-c4360845.json'))

    def test__api_metadata_bad_cats_json(self):
        "[test_results_api.py] /api/metadata: bad cats 1 json"
        url = '/api/metadata/vg-iss-2-s-c4360845.json?cats=obs_pds,whatever,obs_general'
        self._run_status_equal(url, 404,
                               HTTP404_UNKNOWN_CATEGORY(
                                   '/api/metadata/vg-iss-2-s-c4360845.json'))

    def test__api_metadata_bad_cats2_json(self):
        "[test_results_api.py] /api/metadata: bad cats 2 json"
        url = '/api/metadata/vg-iss-2-s-c4360845.json?cats=,obs_pds,obs_general'
        self._run_status_equal(url, 404,
                               HTTP404_UNKNOWN_CATEGORY(
                                   '/api/metadata/vg-iss-2-s-c4360845.json'))

    def test__api_metadata_bad_cats3_json(self):
        "[test_results_api.py] /api/metadata: bad cats 3 json"
        url = '/api/metadata/vg-iss-2-s-c4360845.json?cats=obs_pds,,obs_general'
        self._run_status_equal(url, 404,
                               HTTP404_UNKNOWN_CATEGORY(
                                   '/api/metadata/vg-iss-2-s-c4360845.json'))

    def test__api_metadata_bad_cats4_json(self):
        "[test_results_api.py] /api/metadata: bad cats 4 json"
        url = '/api/metadata/vg-iss-2-s-c4360845.json?cats=obs_pds,obs_general,'
        self._run_status_equal(url, 404,
                               HTTP404_UNKNOWN_CATEGORY(
                                   '/api/metadata/vg-iss-2-s-c4360845.json'))


            ########################################
            ######### /api/files API TESTS #########
            ########################################

    def test__api_files_COISS_versions_w1866145657(self):
        "[test_results_api.py] /api/files: COISS versions w1866145657"
        url = '/api/files/co-iss-w1866145657.json'
        self._run_json_equal_file(url, 'api_files_COISS_versions_w1866145657.json')

    def test__api_files_COISS_versions_n1461112307(self):
        "[test_results_api.py] /api/files: COISS versions n1461112307"
        url = '/api/files/co-iss-n1461112307.json'
        self._run_json_equal_file(url, 'api_files_COISS_versions_n1461112307.json')

    def test__api_files_COVIMS_versions_v1487539692_ir(self):
        "[test_results_api.py] /api/files: COVIMS versions v1487539692_ir"
        url = '/api/files/co-vims-v1487539692_ir.json'
        self._run_json_equal_file(url, 'api_files_COVIMS_versions_v1487539692_ir.json')

    def test__api_files_COVIMS_versions_v1487539692_vis(self):
        "[test_results_api.py] /api/files: COVIMS versions v1487539692_vis"
        url = '/api/files/co-vims-v1487539692_vis.json'
        self._run_json_equal_file(url, 'api_files_COVIMS_versions_v1487539692_vis.json')

    def test__api_files_GOSSI_versions_c0368388622(self):
        "[test_results_api.py] /api/files: GOSSI versions c0368388622"
        url = '/api/files/go-ssi-c0368388622.json'
        self._run_json_equal_file(url, 'api_files_GOSSI_versions_c0368388622.json')

    def test__api_files_VGISS_no_versions_c0948955(self):
        "[test_results_api.py] /api/files: VGISS no versions c0948955"
        url = '/api/files/vg-iss-2-n-c0948955.json'
        self._run_json_equal_file(url, 'api_files_VGISS_no_versions_c0948955.json')

    def test__api_files_HSTWFC3_no_versions_ib4v21gcq(self):
        "[test_results_api.py] /api/files: HSTWFC3 no versions ib4v21gcq"
        url = '/api/files/hst-11559-wfc3-ib4v21gcq.json'
        self._run_json_equal_file(url, 'api_files_HSTWFC3_no_versions_ib4v21gcq.json')

    def test__api_files_HSTWFC3_versions_ib4v12n6q(self):
        "[test_results_api.py] /api/files: HSTWFC3 versions ib4v12n6q"
        url = '/api/files/hst-11559-wfc3-ib4v12n6q.json'
        self._run_json_equal_file(url, 'api_files_HSTWFC3_versions_ib4v12n6q.json')

    def test__api_files_bad_ringobsid(self):
        "[test_results_api.py] /api/files: bad ringobsid"
        url = '/api/files/N_1_BAD.json'
        self._run_status_equal(url, 404,
                               HTTP404_UNKNOWN_RING_OBS_ID('N_1_BAD',
                                                           '/api/files/N_1_BAD.json'))

    def test__api_files_bad_search(self):
        "[test_results_api.py] /api/files: bad search"
        url = '/api/files.json?instrument=fred'
        self._run_status_equal(url, 404,
                               HTTP404_SEARCH_PARAMS_INVALID('/api/files.json'))

    def test__api_files_COISS_2002_order_startobs_limit(self):
        "[test_results_api.py] /api/files: COISS 2002 order startobs limit"
        url = '/api/files.json?instrument=Cassini+ISS&volumeid=COISS_2002&order=-time1,opusid&startobs=10&limit=5'
        self._run_json_equal_file(url, 'api_files_COISS_2002_order_startobs_limit.json')

    def test__api_files_COISS_2002_order_page_limit(self):
        "[test_results_api.py] /api/files: COISS 2002 order startobs limit"
        url = '/api/files.json?instrument=Cassini+ISS&volumeid=COISS_2002&order=-time1,opusid&page=2&limit=5'
        self._run_json_equal_file(url, 'api_files_COISS_2002_order_page_limit.json')

    def test__api_files_COISS_2002_empty_order_startobs_limit(self):
        "[test_results_api.py] /api/files: COISS 2002 empty order startobs limit"
        url = '/api/files.json?instrument=Cassini+ISS&volumeid=COISS_2002&order=&startobs=10&limit=5'
        self._run_json_equal_file(url, 'api_files_COISS_2002_empty_order_startobs_limit.json')


            ########################################################
            ######### /api/image and /api/images API TESTS #########
            ########################################################

    def test__api_image_COISS_w1866145657_thumb_json(self):
        "[test_results_api.py] /api/image: COISS w1866145657"
        url = '/api/image/thumb/co-iss-w1866145657.json'
        self._run_json_equal_file(url, 'api_image_COISS_w1866145657_thumb_json.json')

    def test__api_image_COISS_w1866145657_small_json(self):
        "[test_results_api.py] /api/image: COISS w1866145657"
        url = '/api/image/small/co-iss-w1866145657.json'
        self._run_json_equal_file(url, 'api_image_COISS_w1866145657_small_json.json')

    def test__api_image_COISS_w1866145657_med_json(self):
        "[test_results_api.py] /api/image: COISS w1866145657"
        url = '/api/image/med/co-iss-w1866145657.json'
        self._run_json_equal_file(url, 'api_image_COISS_w1866145657_med_json.json')

    def test__api_image_COISS_w1866145657_full_json(self):
        "[test_results_api.py] /api/image: COISS w1866145657"
        url = '/api/image/full/co-iss-w1866145657.json'
        self._run_json_equal_file(url, 'api_image_COISS_w1866145657_full_json.json')

    def test__api_image_COISS_w1866145657_thumb_html(self):
        "[test_results_api.py] /api/image: COISS w1866145657"
        url = '/api/image/thumb/co-iss-w1866145657.html'
        self._run_html_equal_file(url, 'api_image_COISS_w1866145657_thumb_html.html')

    def test__api_image_COISS_w1866145657_small_csv(self):
        "[test_results_api.py] /api/image: COISS w1866145657"
        url = '/api/image/small/co-iss-w1866145657.csv'
        self._run_csv_equal_file(url, 'api_image_COISS_w1866145657_small_csv.csv')

    def test__api_images_bad_search(self):
        "[test_results_api.py] /api/images: bad search"
        url = '/api/images.json?instrument=fred'
        self._run_status_equal(url, 404,
                               HTTP404_SEARCH_PARAMS_INVALID('/api/images.json'))

    def test__api_images_no_results(self):
        "[test_results_api.py] /api/images: no results"
        url = '/api/images.json?opusid=fred'
        self._run_json_equal_file(url, 'api_images_no_results.json')

    def test__api_images_COCIRS_5408_limit(self):
        "[test_results_api.py] /api/images: COCIRS 5408 limit"
        url = '/api/images.json?volumeid=COCIRS_5408&limit=20'
        self._run_json_equal_file(url, 'api_images_COCIRS_5408_limit.json')

    def test__api_images_COISS_2002_order_startobs_limit_json(self):
        "[test_results_api.py] /api/images: COISS 2002 order startobs limit json"
        url = '/api/images.json?instrument=Cassini+ISS&volumeid=COISS_2002&order=-time1,opusid&startobs=10&limit=5'
        self._run_json_equal_file(url, 'api_images_COISS_2002_order_startobs_limit_json.json')

    def test__api_images_COISS_2002_order_page_limit_json(self):
        "[test_results_api.py] /api/images: COISS 2002 order page limit json"
        url = '/api/images.json?instrument=Cassini+ISS&volumeid=COISS_2002&order=-time1,opusid&page=2&limit=5'
        self._run_json_equal_file(url, 'api_images_COISS_2002_order_page_limit_json.json')

    def test__api_images_COISS_2002_order_startobs_limit_csv(self):
        "[test_results_api.py] /api/images: COISS 2002 order startobs limit csv"
        url = '/api/images.csv?instrument=Cassini+ISS&volumeid=COISS_2002&order=-time1,opusid&startobs=10&limit=5'
        self._run_csv_equal_file(url, 'api_images_COISS_2002_order_startobs_limit_csv.csv')

    def test__api_images_COISS_2002_order_startobs_limit_thumb_json(self):
        "[test_results_api.py] /api/images: COISS 2002 order startobs limit thumb json"
        url = '/api/images/thumb.json?instrument=Cassini+ISS&volumeid=COISS_2002&order=-time1,opusid&startobs=10&limit=5'
        self._run_json_equal_file(url, 'api_images_COISS_2002_order_startobs_limit_thumb_json.json')

    def test__api_images_COISS_2002_order_startobs_limit_thumb_html(self):
        "[test_results_api.py] /api/images: COISS 2002 order startobs limit thumb html"
        url = '/api/images/thumb.html?instrument=Cassini+ISS&volumeid=COISS_2002&order=-time1,opusid&startobs=10&limit=5'
        self._run_html_equal_file(url, 'api_images_COISS_2002_order_startobs_limit_thumb_html.html')

    def test__api_images_COISS_2002_order_startobs_limit_thumb_csv(self):
        "[test_results_api.py] /api/images: COISS 2002 order startobs limit thumb csv"
        url = '/api/images/thumb.csv?instrument=Cassini+ISS&volumeid=COISS_2002&order=-time1,opusid&startobs=10&limit=5'
        self._run_csv_equal_file(url, 'api_images_COISS_2002_order_startobs_limit_thumb_csv.csv')

    def test__api_images_COISS_2002_order_startobs_limit_small_json(self):
        "[test_results_api.py] /api/images: COISS 2002 order startobs limit small json"
        url = '/api/images/small.json?instrument=Cassini+ISS&volumeid=COISS_2002&order=-time1,opusid&startobs=10&limit=5'
        self._run_json_equal_file(url, 'api_images_COISS_2002_order_startobs_limit_small_json.json')

    def test__api_images_COISS_2002_order_startobs_limit_med_json(self):
        "[test_results_api.py] /api/images: COISS 2002 order startobs limit med json"
        url = '/api/images/med.json?instrument=Cassini+ISS&volumeid=COISS_2002&order=-time1,opusid&startobs=10&limit=5'
        self._run_json_equal_file(url, 'api_images_COISS_2002_order_startobs_limit_med_json.json')

    def test__api_images_COISS_2002_order_startobs_limit_full_json(self):
        "[test_results_api.py] /api/images: COISS 2002 order startobs limit full json"
        url = '/api/images/full.json?instrument=Cassini+ISS&volumeid=COISS_2002&order=-time1,opusid&startobs=10&limit=5'
        self._run_json_equal_file(url, 'api_images_COISS_2002_order_startobs_limit_full_json.json')


            #############################################
            ######### /api/categories API TESTS #########
            #############################################

    def test__api_categories_bad_opusid(self):
        "[test_results_api.py] /api/categories: Bad OPUSID"
        url = '/api/categories/co-iss-w1866145657x.json'
        self._run_json_equal_file(url, 'api_categories_bad_opusid.json')

    def test__api_categories_bad_ringobsid(self):
        "[test_results_api.py] /api/categories: Bad ringobsid"
        url = '/api/categories/_123.json'
        self._run_status_equal(url, 404,
                               HTTP404_UNKNOWN_RING_OBS_ID(
                                    '_123',
                                    '/api/categories/_123.json'))

    def test__api_categories_vg_iss_2_s_c4360004(self):
        "[test_results_api.py] /api/categories: vg-iss-2-s-c4360004"
        url = '/api/categories/vg-iss-2-s-c4360004.json'
        self._run_json_equal_file(url, 'api_categories_vg_iss_2_s_c4360004.json')

    def test__api_categories_COISS_2002(self):
        "[test_results_api.py] /api/categories: COISS_2002"
        url = '/api/categories.json?volumeid=COISS_2002'
        self._run_json_equal_file(url, 'api_categories_COISS_2002.json')

    def test__api_categories_bad_search(self):
        "[test_results_api.py] /api/categories: bad search"
        url = '/api/categories.json?volumeidx=COISS_2002'
        self._run_status_equal(url, 404,
                               HTTP404_SEARCH_PARAMS_INVALID('/api/categories.json'))

    def test__api_categories_empty_search(self):
        "[test_results_api.py] /api/categories: empty search"
        url = '/api/categories.json'
        self._run_json_equal_file(url, 'api_categories_empty_search.json')


            ################################################
            ######### /api/product_types API TESTS #########
            ################################################

    def test__api_product_types_bad_opusid(self):
        "[test_results_api.py] /api/product_types: Bad OPUSID"
        url = '/api/product_types/co-iss-w1866145657x.json'
        self._run_json_equal_file(url, 'api_product_types_bad_opusid.json')

    def test__api_product_types_bad_ringobsid(self):
        "[test_results_api.py] /api/product_types: Bad ringobsid"
        url = '/api/product_types/_N_1_2_3.json'
        self._run_status_equal(url, 404,
                               HTTP404_UNKNOWN_RING_OBS_ID(
                                   '_N_1_2_3',
                                   '/api/product_types/_N_1_2_3.json'))

    def test__api_product_types_vg_iss_2_s_c4360004(self):
        "[test_results_api.py] /api/product_types: vg-iss-2-s-c4360004"
        url = '/api/product_types/vg-iss-2-s-c4360004.json'
        self._run_json_equal_file(url, 'api_product_types_vg_iss_2_s_c4360004.json')

    def test__api_product_types_COISS_2002(self):
        "[test_results_api.py] /api/product_types: COISS_2002"
        url = '/api/product_types.json?volumeid=COISS_2002'
        self._run_json_equal_file(url, 'api_product_types_COISS_2002.json')

    def test__api_product_types_COISS_2002_cache(self):
        "[test_results_api.py] /api/product_types: COISS_2002 cache"
        url = '/api/product_types.json?volumeid=COISS_2002'
        self._run_json_equal_file(url, 'api_product_types_COISS_2002.json')
        self._run_json_equal_file(url, 'api_product_types_COISS_2002.json')
        self._run_json_equal_file(url, 'api_product_types_COISS_2002.json')
        self._run_json_equal_file(url, 'api_product_types_COISS_2002.json')

    def test__api_product_types_bad_search(self):
        "[test_results_api.py] /api/product_types: bad search"
        url = '/api/product_types.json?volumeidx=COISS_2002'
        self._run_status_equal(url, 404,
                               HTTP404_SEARCH_PARAMS_INVALID('/api/product_types.json'))

    def test__api_product_types_empty_search(self):
        "[test_results_api.py] /api/protect_types: empty search"
        url = '/api/product_types.json'
        self._run_json_equal_file(url, 'api_product_types_empty_search.json')
