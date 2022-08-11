# opus/application/test_api/test_results_api.py

import json
import logging
import requests
from unittest import TestCase

from django.core.cache import cache
from rest_framework.test import RequestsClient

from tools.app_utils import (HTTP404_BAD_OR_MISSING_REQNO,
                             HTTP404_UNKNOWN_CATEGORY,
                             HTTP404_UNKNOWN_OPUS_ID,
                             HTTP404_UNKNOWN_RING_OBS_ID,
                             HTTP404_UNKNOWN_SLUG)

from .api_test_helper import ApiTestHelper

import settings

class ApiResultsTests(TestCase, ApiTestHelper):

    def setUp(self):
        self.UPDATE_FILES = False
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


            #############################################
            ######### /api/dataimages API TESTS #########
            #############################################

    # reqno

    def test__api_dataimages_no_results_default(self):
        "[test_results_api.py] /__api/dataimages: no results default cols"
        url = '/__api/dataimages.json?opusid=notgoodid'
        self._run_status_equal(url, 404,
                        HTTP404_BAD_OR_MISSING_REQNO('/__api/dataimages.json'))

    def test__api_dataimages_no_results_default_reqno(self):
        "[test_results_api.py] /__api/dataimages: no results default cols reqno"
        url = '/__api/dataimages.json?opusid=notgoodid&reqno=5'
        self._run_status_equal(url, 200)

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

    # fake
    def test__api_dataimages_no_results_default_reqno(self):
        "[test_results_api.py] /__fake/__api/dataimages: no results default cols reqno"
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
        expected = b'OPUS ID,Instrument Name,Planet,Intended Target Name(s),Observation Start Time,Observation Duration (secs)\n'
        self._run_csv_equal(url, expected)

    def test__api_data_no_results_default_html(self):
        "[test_results_api.py] /api/data: no results default cols html"
        url = '/api/data.html?opusid=notgoodid'
        self._run_html_equal_file(url, 'api_data_no_results_default_html.html')

    def test__api_data_no_results_empty_cols_json(self):
        "[test_results_api.py] /api/data: no results empty cols json"
        url = '/api/data.json?opusid=notgoodid&cols='
        expected = {"limit": 100, "available": 0, "page": [], "order": "time1,opusid", "count": 0, "labels": [], "columns": [], "start_obs": 1}
        self._run_json_equal(url, expected)

    def test__api_data_no_results_empty_cols_csv(self):
        "[test_results_api.py] /api/data: no results empty cols csv"
        url = '/api/data.csv?opusid=notgoodid&cols='
        expected = b''
        self._run_csv_equal(url, expected)

    def test__api_data_no_results_empty_cols_html(self):
        "[test_results_api.py] /api/data: no results empty cols html"
        url = '/api/data.html?opusid=notgoodid&cols='
        expected = b'<table>\n<tr>\n</tr>\n</table>\n'
        self._run_html_equal(url, expected)

    def test__api_data_coiss_2002_more_cols_json(self):
        "[test_results_api.py] /api/data: coiss_2002 more cols json"
        url = '/api/data.json?cols=opusid,instrument,planet,target,time1,observationduration,CASSINIspacecraftclockcount1,CASSINIobsname,CASSINIactivityname,CASSINImissionphasename,CASSINItargetcode,CASSINIrevnoint,CASSINIprimeinst,CASSINIisprime,CASSINIsequenceid,CASSINIspacecraftclockcount2,CASSINIert1,CASSINIert2,COISScamera,COISSfilter,COISSshuttermode,COISSshutterstate,COISScompressiontype,COISSdataconversiontype,COISSgainmode,COISSinstrumentmode,COISSmissinglines,COISSimagenumber,COISStargetdesc,COISSimageobservationtype&volumeid=COISS_2002'
        self._run_json_equal_file(url, 'api_data_coiss_2002_more_cols_json.json')

    def test__api_data_coiss_2002_more_cols_csv(self):
        "[test_results_api.py] /api/data: coiss_2002 more cols csv"
        url = '/api/data.csv?cols=opusid,instrument,planet,target,time1,observationduration,CASSINIspacecraftclockcount1,CASSINIobsname,CASSINIactivityname,CASSINImissionphasename,CASSINItargetcode,CASSINIrevnoint,CASSINIprimeinst,CASSINIisprime,CASSINIsequenceid,CASSINIspacecraftclockcount2,CASSINIert1,CASSINIert2,COISScamera,COISSfilter,COISSshuttermode,COISSshutterstate,COISScompressiontype,COISSdataconversiontype,COISSgainmode,COISSinstrumentmode,COISSmissinglines,COISSimagenumber,COISStargetdesc,COISSimageobservationtype&volumeid=COISS_2002'
        self._run_csv_equal_file(url, 'api_data_coiss_2002_more_cols_csv.csv')

    def test__api_data_coiss_2002_more_cols_html(self):
        "[test_results_api.py] /api/data: coiss_2002 more cols html"
        url = '/api/data.html?cols=opusid,instrument,planet,target,time1,observationduration,CASSINIspacecraftclockcount1,CASSINIobsname,CASSINIactivityname,CASSINImissionphasename,CASSINItargetcode,CASSINIrevnoint,CASSINIprimeinst,CASSINIisprime,CASSINIsequenceid,CASSINIspacecraftclockcount2,CASSINIert1,CASSINIert2,COISScamera,COISSfilter,COISSshuttermode,COISSshutterstate,COISScompressiontype,COISSdataconversiontype,COISSgainmode,COISSinstrumentmode,COISSmissinglines,COISSimagenumber,COISStargetdesc,COISSimageobservationtype&volumeid=COISS_2002'
        self._run_html_equal_file(url, 'api_data_coiss_2002_more_cols_html.html')

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
    def test__api_metadata_vg_iss_2_s_c4360845_default_json(self):
        "[test_results_api.py] /api/metadata: vg-iss-2-s-c4360845 default json"
        url = '/api/metadata/vg-iss-2-s-c4360845.json'
        self._run_json_equal_file(url, 'api_metadata_vg_iss_2_s_c4360845_default_json.json')

    def test__api_metadata_vg_iss_2_s_c4360845_default_json_ringobsid(self):
        "[test_results_api.py] /api/metadata: S_IMG_VG2_ISS_4360845_N default json"
        url = '/api/metadata/S_IMG_VG2_ISS_4360845_N.json'
        self._run_json_equal_file(url, 'api_metadata_vg_iss_2_s_c4360845_default_json.json')

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

    def test__api_metadata2_vg_iss_2_s_c4360845_default_json(self):
        "[test_results_api.py] /api/metadata_v2: vg-iss-2-s-c4360845 default json"
        url = '/api/metadata_v2/vg-iss-2-s-c4360845.json'
        self._run_json_equal_file(url, 'api_metadata2_vg_iss_2_s_c4360845_default_json.json')

    def test__api_metadata2_vg_iss_2_s_c4360845_default_json_ringobsid(self):
        "[test_results_api.py] /api/metadata_v2: S_IMG_VG2_ISS_4360845_N default json"
        url = '/api/metadata_v2/S_IMG_VG2_ISS_4360845_N.json'
        self._run_json_equal_file(url, 'api_metadata2_vg_iss_2_s_c4360845_default_json.json')

    def test__api_metadata_vg_iss_2_s_c4360845_default_html(self):
        "[test_results_api.py] /api/metadata: vg-iss-2-s-c4360845 default html"
        url = '/api/metadata/vg-iss-2-s-c4360845.html'
        self._run_html_equal_file(url, 'api_metadata_vg_iss_2_s_c4360845_default_html.html')

    def test__api_metadata2_vg_iss_2_s_c4360845_default_html(self):
        "[test_results_api.py] /api/metadata_v2: vg-iss-2-s-c4360845 default html"
        url = '/api/metadata_v2/vg-iss-2-s-c4360845.html'
        self._run_html_equal_file(url, 'api_metadata2_vg_iss_2_s_c4360845_default_html.html')

    def test__api_metadata2_vg_iss_2_s_c4360845_default_html_private(self):
        "[test_results_api.py] /api/metadata_v2: vg-iss-2-s-c4360845 default html private"
        url = '/__api/metadata_v2/vg-iss-2-s-c4360845.html'
        expected = b'<ul id="detail__data_general_constraints" class="op-detail-list">\n<li class="op-detail-entry">\n<i class="fas fa-info-circle op-detail-entry-icon op-detail-metadata-tooltip" data-toggle="tooltip"\ntitle="'
        self._run_html_startswith(url, expected)

    def test__api_metadata_vg_iss_2_s_c4360845_default_csv(self):
        "[test_results_api.py] /api/metadata: vg-iss-2-s-c4360845 default csv"
        url = '/api/metadata/vg-iss-2-s-c4360845.csv'
        self._run_csv_equal_file(url, 'api_metadata_vg_iss_2_s_c4360845_default_csv.csv')

    def test__api_metadata2_vg_iss_2_s_c4360845_default_csv(self):
        "[test_results_api.py] /api/metadata_v2: vg-iss-2-s-c4360845 default csv"
        url = '/api/metadata_v2/vg-iss-2-s-c4360845.csv'
        self._run_csv_equal_file(url, 'api_metadata2_vg_iss_2_s_c4360845_default_csv.csv')

    # Specified columns, empty
    def test__api_metadata_vg_iss_2_s_c4360845_cols_empty_json(self):
        "[test_results_api.py] /api/metadata: vg-iss-2-s-c4360845 cols empty json"
        url = '/api/metadata/vg-iss-2-s-c4360845.json?cols='
        expected = []
        self._run_json_equal(url, expected)

    def test__api_metadata2_vg_iss_2_s_c4360845_cols_empty_json(self):
        "[test_results_api.py] /api/metadata_v2: vg-iss-2-s-c4360845 cols empty json"
        url = '/api/metadata_v2/vg-iss-2-s-c4360845.json?cols='
        expected = []
        self._run_json_equal(url, expected)

    def test__api_metadata_vg_iss_2_s_c4360845_cols_empty_html(self):
        "[test_results_api.py] /api/metadata: vg-iss-2-s-c4360845 cols empty html"
        url = '/api/metadata/vg-iss-2-s-c4360845.html?cols='
        expected = b'<dl>\n</dl>\n'
        self._run_html_equal(url, expected)

    def test__api_metadata2_vg_iss_2_s_c4360845_cols_empty_html(self):
        "[test_results_api.py] /api/metadata_v2: vg-iss-2-s-c4360845 cols empty html"
        url = '/api/metadata_v2/vg-iss-2-s-c4360845.html?cols='
        expected = b'<dl>\n</dl>\n'
        self._run_html_equal(url, expected)

    def test__api_metadata2_vg_iss_2_s_c4360845_cols_empty_html_private(self):
        "[test_results_api.py] /api/metadata_v2: vg-iss-2-s-c4360845 cols empty html private"
        url = '/__api/metadata_v2/vg-iss-2-s-c4360845.html?cols='
        expected = b'<ul class="op-detail-list">\n</ul>\n'
        self._run_html_equal(url, expected)

    def test__api_metadata_vg_iss_2_s_c4360845_cols_empty_csv(self):
        "[test_results_api.py] /api/metadata: vg-iss-2-s-c4360845 cols empty csv"
        url = '/api/metadata/vg-iss-2-s-c4360845.csv?cols='
        expected = b''
        self._run_csv_equal(url, expected)

    def test__api_metadata2_vg_iss_2_s_c4360845_cols_empty_csv(self):
        "[test_results_api.py] /api/metadata_v2: vg-iss-2-s-c4360845 cols empty csv"
        url = '/api/metadata_v2/vg-iss-2-s-c4360845.csv?cols='
        expected = b''
        self._run_csv_equal(url, expected)

    # Specified columns, opusid only
    def test__api_metadata_vg_iss_2_s_c4360845_cols_opusid_json(self):
        "[test_results_api.py] /api/metadata: vg-iss-2-s-c4360845 cols opusid json"
        url = '/api/metadata/vg-iss-2-s-c4360845.json?cols=opusid'
        expected = [{"opusid": "vg-iss-2-s-c4360845"}]
        self._run_json_equal(url, expected)

    def test__api_metadata2_vg_iss_2_s_c4360845_cols_opusid_json(self):
        "[test_results_api.py] /api/metadata_v2: vg-iss-2-s-c4360845 cols opusid json"
        url = '/api/metadata_v2/vg-iss-2-s-c4360845.json?cols=opusid'
        expected = [{"opusid": "vg-iss-2-s-c4360845"}]
        self._run_json_equal(url, expected)

    def test__api_metadata2_nh_lorri_lor_0284457489_cols_opusid_json(self):
        "[test_results_api.py] /api/metadata_v2: nh-lorri-lor_0284457489 cols opusid json"
        # Check an OPUS ID with a _ in it which can screw up database searches
        url = '/api/metadata_v2/nh-lorri-lor_0284457489.json?cols=opusid'
        expected = [{"opusid": "nh-lorri-lor_0284457489"}]
        self._run_json_equal(url, expected)

    def test__api_metadata_vg_iss_2_s_c4360845_cols_opusid_html(self):
        "[test_results_api.py] /api/metadata: vg-iss-2-s-c4360845 cols opusid html"
        url = '/api/metadata/vg-iss-2-s-c4360845.html?cols=opusid'
        expected = b'<dl>\n<dt>OPUS ID</dt><dd>vg-iss-2-s-c4360845</dd>\n</dl>\n'
        self._run_html_equal(url, expected)

    def test__api_metadata2_vg_iss_2_s_c4360845_cols_opusid_html(self):
        "[test_results_api.py] /api/metadata_v2: vg-iss-2-s-c4360845 cols opusid html"
        url = '/api/metadata_v2/vg-iss-2-s-c4360845.html?cols=opusid'
        expected = b'<dl>\n<dt>OPUS ID</dt><dd>vg-iss-2-s-c4360845</dd>\n</dl>\n'
        self._run_html_equal(url, expected)

    def test__api_metadata2_vg_iss_2_s_c4360845_cols_opusid_html_private(self):
        "[test_results_api.py] /api/metadata_v2: vg-iss-2-s-c4360845 cols opusid html private"
        url = '/__api/metadata_v2/vg-iss-2-s-c4360845.html?cols=opusid'
        expected = b'<ul class="op-detail-list">\n<li class="op-detail-entry">\n<i class="fas fa-info-circle op-detail-entry-icon op-detail-metadata-tooltip" data-toggle="tooltip"\ntitle="A unique ID assigned to an observation by the Ring-Moon Systems Node of the PDS. The OPUS ID is useful for referencing specific observations in a mission-independent manner but should never be used outside of OPUS. To reference an observation outside of OPUS, use the Volume ID, Product ID, and/or Primary File Spec. Note: The format of the OPUS ID is not guaranteed to remain the same over time."></i>&nbsp;\n<div class="op-detail-entry-values-wrapper">\nOPUS ID:&nbsp;\n<span class="op-detail-entry-values">vg-iss-2-s-c4360845\n<a href="/opus/#'
        self._run_html_startswith(url, expected)

    def test__api_metadata_vg_iss_2_s_c4360845_cols_opusid_csv(self):
        "[test_results_api.py] /api/metadata: vg-iss-2-s-c4360845 cols opusid csv"
        url = '/api/metadata/vg-iss-2-s-c4360845.csv?cols=opusid'
        expected = b'OPUS ID\nvg-iss-2-s-c4360845\n'
        self._run_csv_equal(url, expected)

    def test__api_metadata2_vg_iss_2_s_c4360845_cols_opusid_csv(self):
        "[test_results_api.py] /api/metadata_v2: vg-iss-2-s-c4360845 cols opusid csv"
        url = '/api/metadata_v2/vg-iss-2-s-c4360845.csv?cols=opusid'
        expected = b'OPUS ID\nvg-iss-2-s-c4360845\n'
        self._run_csv_equal(url, expected)

    # Specified columns, all Voyager or Cassini slugs
    def test__api_metadata_vg_iss_2_s_c4365507_cols_all_voyager_json(self):
        "[test_results_api.py] /api/metadata: vg-iss-2-s-c4365507 cols all voyager json"
        url = '/api/metadata/vg-iss-2-s-c4365507.json?cols=opusid,VOYAGERmissionphasename,VOYAGERspacecraftclockcount1,VOYAGERspacecraftclockcount2,VOYAGERert,VGISScamera,VGISSfilter,VGISSfilternumber,VGISSshuttermode,VGISSeditmode,VGISSgainmode,VGISSscanmode,VGISSimageid,VGISSusablelines,VGISSusablesamples'
        self._run_json_equal_file(url, 'api_metadata_vg_iss_2_s_c4365507_cols_all_voyager_json.json')

    def test__api_metadata2_vg_iss_2_s_c4365507_cols_all_voyager_json(self):
        "[test_results_api.py] /api/metadata_v2: vg-iss-2-s-c4365507 cols all voyager json"
        url = '/api/metadata_v2/vg-iss-2-s-c4365507.json?cols=opusid,VOYAGERmissionphasename,VOYAGERspacecraftclockcount1,VOYAGERspacecraftclockcount2,VOYAGERert,VGISScamera,VGISSfilter,VGISSfilternumber,VGISSshuttermode,VGISSeditmode,VGISSgainmode,VGISSscanmode,VGISSimageid,VGISSusablelines,VGISSusablesamples'
        self._run_json_equal_file(url, 'api_metadata2_vg_iss_2_s_c4365507_cols_all_voyager_json.json')

    def test__api_metadata_vg_iss_2_s_c4365507_cols_all_cassini_json(self):
        "[test_results_api.py] /api/metadata: vg-iss-2-s-c4365507 cols all cassini json"
        url = '/api/metadata/vg-iss-2-s-c4365507.json?cols=opusid,volumeid,greaterpixelsize,lesserpixelsize,wavelength1,wavelength2,CASSINIobsname,CASSINIactivityname,CASSINImissionphasename,CASSINItargetcode,CASSINIrevnoint,CASSINIprimeinst,CASSINIisprime,CASSINIsequenceid,CASSINIspacecraftclockcount1,CASSINIspacecraftclockcount2,CASSINIert1,CASSINIert2'
        self._run_json_equal_file(url, 'api_metadata_vg_iss_2_s_c4365507_cols_all_cassini_json.json')

    def test__api_metadata_vg_iss_2_s_c4365507_cols_all_cassini_page_json(self):
        "[test_results_api.py] /api/metadata: vg-iss-2-s-c4365507 cols all cassini page json"
        url = '/api/metadata/vg-iss-2-s-c4365507.json?page=8&cols=opusid,volumeid,greaterpixelsize,lesserpixelsize,wavelength1,wavelength2,CASSINIobsname,CASSINIactivityname,CASSINImissionphasename,CASSINItargetcode,CASSINIrevnoint,CASSINIprimeinst,CASSINIisprime,CASSINIsequenceid,CASSINIspacecraftclockcount1,CASSINIspacecraftclockcount2,CASSINIert1,CASSINIert2'
        self._run_json_equal_file(url, 'api_metadata_vg_iss_2_s_c4365507_cols_all_cassini_json.json')

    def test__api_metadata_vg_iss_2_s_c4365507_cols_all_cassini_startobs_json(self):
        "[test_results_api.py] /api/metadata: vg-iss-2-s-c4365507 cols all cassini startobs json"
        url = '/api/metadata/vg-iss-2-s-c4365507.json?startobs=800&cols=opusid,volumeid,greaterpixelsize,lesserpixelsize,wavelength1,wavelength2,CASSINIobsname,CASSINIactivityname,CASSINImissionphasename,CASSINItargetcode,CASSINIrevnoint,CASSINIprimeinst,CASSINIisprime,CASSINIsequenceid,CASSINIspacecraftclockcount1,CASSINIspacecraftclockcount2,CASSINIert1,CASSINIert2'
        self._run_json_equal_file(url, 'api_metadata_vg_iss_2_s_c4365507_cols_all_cassini_json.json')

    def test__api_metadata_vg_iss_2_s_c4365507_cols_all_cassini_pagestartobslimit_json(self):
        "[test_results_api.py] /api/metadata: vg-iss-2-s-c4365507 cols all cassini page startobs lmiit json"
        url = '/api/metadata/vg-iss-2-s-c4365507.json?page=8&startobs=800&limit=0&cols=opusid,volumeid,greaterpixelsize,lesserpixelsize,wavelength1,wavelength2,CASSINIobsname,CASSINIactivityname,CASSINImissionphasename,CASSINItargetcode,CASSINIrevnoint,CASSINIprimeinst,CASSINIisprime,CASSINIsequenceid,CASSINIspacecraftclockcount1,CASSINIspacecraftclockcount2,CASSINIert1,CASSINIert2'
        self._run_json_equal_file(url, 'api_metadata_vg_iss_2_s_c4365507_cols_all_cassini_json.json')

    def test__api_metadata2_vg_iss_2_s_c4365507_cols_all_cassini_json(self):
        "[test_results_api.py] /api/metadata_v2: vg-iss-2-s-c4365507 cols all cassini json"
        url = '/api/metadata_v2/vg-iss-2-s-c4365507.json?cols=opusid,volumeid,greaterpixelsize,lesserpixelsize,wavelength1,wavelength2,CASSINIobsname,CASSINIactivityname,CASSINImissionphasename,CASSINItargetcode,CASSINIrevnoint,CASSINIprimeinst,CASSINIisprime,CASSINIsequenceid,CASSINIspacecraftclockcount1,CASSINIspacecraftclockcount2,CASSINIert1,CASSINIert2'
        self._run_json_equal_file(url, 'api_metadata2_vg_iss_2_s_c4365507_cols_all_cassini_json.json')

    def test__api_metadata_vg_iss_2_s_c4365507_cols_all_voyager_html(self):
        "[test_results_api.py] /api/metadata: vg-iss-2-s-c4365507 cols all voyager html"
        url = '/api/metadata/vg-iss-2-s-c4365507.html?cols=opusid,VOYAGERmissionphasename,VOYAGERspacecraftclockcount1,VOYAGERspacecraftclockcount2,VOYAGERert,VGISScamera,VGISSfilter,VGISSfilternumber,VGISSshuttermode,VGISSeditmode,VGISSgainmode,VGISSscanmode,VGISSimageid,VGISSusablelines,VGISSusablesamples'
        self._run_html_equal_file(url, 'api_metadata_vg_iss_2_s_c4365507_cols_all_voyager_html.html')

    def test__api_metadata2_vg_iss_2_s_c4365507_cols_all_voyager_html(self):
        "[test_results_api.py] /api/metadata_v2: vg-iss-2-s-c4365507 cols all voyager html"
        url = '/api/metadata_v2/vg-iss-2-s-c4365507.html?cols=opusid,VOYAGERmissionphasename,VOYAGERspacecraftclockcount1,VOYAGERspacecraftclockcount2,VOYAGERert,VGISScamera,VGISSfilter,VGISSfilternumber,VGISSshuttermode,VGISSeditmode,VGISSgainmode,VGISSscanmode,VGISSimageid,VGISSusablelines,VGISSusablesamples'
        self._run_html_equal_file(url, 'api_metadata2_vg_iss_2_s_c4365507_cols_all_voyager_html.html')

    def test__api_metadata_vg_iss_2_s_c4365507_cols_all_cassini_html(self):
        "[test_results_api.py] /api/metadata: vg-iss-2-s-c4365507 cols all cassini html"
        url = '/api/metadata/vg-iss-2-s-c4365507.html?cols=opusid,volumeid,greaterpixelsize,lesserpixelsize,wavelength1,wavelength2,CASSINIobsname,CASSINIactivityname,CASSINImissionphasename,CASSINItargetcode,CASSINIrevnoint,CASSINIprimeinst,CASSINIisprime,CASSINIsequenceid,CASSINIspacecraftclockcount1,CASSINIspacecraftclockcount2,CASSINIert1,CASSINIert2'
        self._run_html_equal_file(url, 'api_metadata_vg_iss_2_s_c4365507_cols_all_cassini_html.html')

    def test__api_metadata2_vg_iss_2_s_c4365507_cols_all_cassini_html(self):
        "[test_results_api.py] /api/metadata_v2: vg-iss-2-s-c4365507 cols all cassini html"
        url = '/api/metadata_v2/vg-iss-2-s-c4365507.html?cols=opusid,volumeid,greaterpixelsize,lesserpixelsize,wavelength1,wavelength2,CASSINIobsname,CASSINIactivityname,CASSINImissionphasename,CASSINItargetcode,CASSINIrevnoint,CASSINIprimeinst,CASSINIisprime,CASSINIsequenceid,CASSINIspacecraftclockcount1,CASSINIspacecraftclockcount2,CASSINIert1,CASSINIert2'
        self._run_html_equal_file(url, 'api_metadata2_vg_iss_2_s_c4365507_cols_all_cassini_html.html')

    def test__api_metadata_vg_iss_2_s_c4365507_cols_all_voyager_csv(self):
        "[test_results_api.py] /api/metadata: vg-iss-2-s-c4365507 cols all voyager csv"
        url = '/api/metadata/vg-iss-2-s-c4365507.csv?cols=opusid,VOYAGERmissionphasename,VOYAGERspacecraftclockcount1,VOYAGERspacecraftclockcount2,VOYAGERert,VGISScamera,VGISSfilter,VGISSfilternumber,VGISSshuttermode,VGISSeditmode,VGISSgainmode,VGISSscanmode,VGISSimageid,VGISSusablelines,VGISSusablesamples'
        self._run_csv_equal_file(url, 'api_metadata_vg_iss_2_s_c4365507_cols_all_voyager_csv.csv')

    def test__api_metadata2_vg_iss_2_s_c4365507_cols_all_voyager_csv(self):
        "[test_results_api.py] /api/metadata_v2: vg-iss-2-s-c4365507 cols all voyager csv"
        url = '/api/metadata_v2/vg-iss-2-s-c4365507.csv?cols=opusid,VOYAGERmissionphasename,VOYAGERspacecraftclockcount1,VOYAGERspacecraftclockcount2,VOYAGERert,VGISScamera,VGISSfilter,VGISSfilternumber,VGISSshuttermode,VGISSeditmode,VGISSgainmode,VGISSscanmode,VGISSimageid,VGISSusablelines,VGISSusablesamples'
        self._run_csv_equal_file(url, 'api_metadata2_vg_iss_2_s_c4365507_cols_all_voyager_csv.csv')

    def test__api_metadata_vg_iss_2_s_c4365507_cols_all_cassini_csv(self):
        "[test_results_api.py] /api/metadata: vg-iss-2-s-c4365507 cols all cassini csv"
        url = '/api/metadata/vg-iss-2-s-c4365507.csv?cols=opusid,volumeid,greaterpixelsize,lesserpixelsize,wavelength1,wavelength2,CASSINIobsname,CASSINIactivityname,CASSINImissionphasename,CASSINItargetcode,CASSINIrevnoint,CASSINIprimeinst,CASSINIisprime,CASSINIsequenceid,CASSINIspacecraftclockcount1,CASSINIspacecraftclockcount2,CASSINIert1,CASSINIert2'
        self._run_csv_equal_file(url, 'api_metadata_vg_iss_2_s_c4365507_cols_all_cassini_csv.csv')

    def test__api_metadata2_vg_iss_2_s_c4365507_cols_all_cassini_csv(self):
        "[test_results_api.py] /api/metadata_v2: vg-iss-2-s-c4365507 cols all cassini csv"
        url = '/api/metadata_v2/vg-iss-2-s-c4365507.csv?cols=opusid,volumeid,greaterpixelsize,lesserpixelsize,wavelength1,wavelength2,CASSINIobsname,CASSINIactivityname,CASSINImissionphasename,CASSINItargetcode,CASSINIrevnoint,CASSINIprimeinst,CASSINIisprime,CASSINIsequenceid,CASSINIspacecraftclockcount1,CASSINIspacecraftclockcount2,CASSINIert1,CASSINIert2'
        self._run_csv_equal_file(url, 'api_metadata2_vg_iss_2_s_c4365507_cols_all_cassini_csv.csv')

    # Specified cats, empty
    def test__api_metadata_hst_09975_acs_j8n410lbq_cats_empty_json(self):
        "[test_results_api.py] /api/metadata: hst-09975-acs-j8n410lbq cats empty json"
        url = '/api/metadata/hst-09975-acs-j8n410lbq.json?cats='
        expected = {}
        self._run_json_equal(url, expected)

    def test__api_metadata2_hst_09975_acs_j8n410lbq_cats_empty_json(self):
        "[test_results_api.py] /api/metadata_v2: hst-09975-acs-j8n410lbq cats empty json"
        url = '/api/metadata_v2/hst-09975-acs-j8n410lbq.json?cats='
        expected = {}
        self._run_json_equal(url, expected)

    def test__api_metadata_hst_09975_acs_j8n410lbq_cats_empty_html(self):
        "[test_results_api.py] /api/metadata: hst-09975-acs-j8n410lbq cats empty html"
        url = '/api/metadata/hst-09975-acs-j8n410lbq.html?cats='
        expected = b'<dl>\n</dl>\n'
        self._run_html_equal(url, expected)

    def test__api_metadata2_hst_09975_acs_j8n410lbq_cats_empty_html(self):
        "[test_results_api.py] /api/metadata_v2: hst-09975-acs-j8n410lbq cats empty html"
        url = '/api/metadata_v2/hst-09975-acs-j8n410lbq.html?cats='
        expected = b'<dl>\n</dl>\n'
        self._run_html_equal(url, expected)

    def test__api_metadata_hst_09975_acs_j8n410lbq_cats_empty_csv(self):
        "[test_results_api.py] /api/metadata: hst-09975-acs-j8n410lbq cats empty csv"
        url = '/api/metadata/hst-09975-acs-j8n410lbq.csv?cats='
        expected = b''
        self._run_csv_equal(url, expected)

    def test__api_metadata2_hst_09975_acs_j8n410lbq_cats_empty_csv(self):
        "[test_results_api.py] /api/metadata_v2: hst-09975-acs-j8n410lbq cats empty csv"
        url = '/api/metadata_v2/hst-09975-acs-j8n410lbq.csv?cats='
        expected = b''
        self._run_csv_equal(url, expected)

    # Specified cats, PDS Constraints only
    def test__api_metadata_hst_09975_acs_j8n410lbq_cats_pds_constraints_json(self):
        "[test_results_api.py] /api/metadata: hst-09975-acs-j8n410lbq cats PDS Constraints json"
        url = '/api/metadata/hst-09975-acs-j8n410lbq.json?cats=PDS+Constraints'
        self._run_json_equal_file(url, 'api_metadata_hst_09975_acs_j8n410lbq_cats_pds_constraints_json.json')

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

    def test__api_metadata2_hst_09975_acs_j8n410lbq_cats_pds_constraints_json(self):
        "[test_results_api.py] /api/metadata_v2: hst-09975-acs-j8n410lbq cats PDS Constraints json"
        url = '/api/metadata_v2/hst-09975-acs-j8n410lbq.json?cats=PDS+Constraints'
        self._run_json_equal_file(url, 'api_metadata2_hst_09975_acs_j8n410lbq_cats_pds_constraints_json.json')

    def test__api_metadata_hst_09975_acs_j8n410lbq_cats_pds_constraints_html(self):
        "[test_results_api.py] /api/metadata: hst-09975-acs-j8n410lbq cats PDS Constraints html"
        url = '/api/metadata/hst-09975-acs-j8n410lbq.html?cats=PDS+Constraints'
        self._run_html_equal_file(url, 'api_metadata_hst_09975_acs_j8n410lbq_cats_pds_constraints_html.html')

    def test__api_metadata2_hst_09975_acs_j8n410lbq_cats_pds_constraints_html(self):
        "[test_results_api.py] /api/metadata_v2: hst-09975-acs-j8n410lbq cats PDS Constraints html"
        url = '/api/metadata_v2/hst-09975-acs-j8n410lbq.html?cats=PDS+Constraints'
        self._run_html_equal_file(url, 'api_metadata2_hst_09975_acs_j8n410lbq_cats_pds_constraints_html.html')

    def test__api_metadata_hst_09975_acs_j8n410lbq_cats_pds_constraints_csv(self):
        "[test_results_api.py] /api/metadata: hst-09975-acs-j8n410lbq cats PDS Constraints csv"
        url = '/api/metadata/hst-09975-acs-j8n410lbq.csv?cats=PDS+Constraints'
        self._run_csv_equal_file(url, 'api_metadata_hst_09975_acs_j8n410lbq_cats_pds_constraints_csv.csv')

    def test__api_metadata2_hst_09975_acs_j8n410lbq_cats_pds_constraints_csv(self):
        "[test_results_api.py] /api/metadata_v2: hst-09975-acs-j8n410lbq cats PDS Constraints csv"
        url = '/api/metadata_v2/hst-09975-acs-j8n410lbq.csv?cats=PDS+Constraints'
        self._run_csv_equal_file(url, 'api_metadata2_hst_09975_acs_j8n410lbq_cats_pds_constraints_csv.csv')

    # Specified cats, PDS, Hubble Constraints
    def test__api_metadata_hst_09975_acs_j8n410lbq_cats_pds_hubble_constraints_json(self):
        "[test_results_api.py] /api/metadata: hst-09975-acs-j8n410lbq cats PDS, Hubble Constraints json"
        url = '/api/metadata/hst-09975-acs-j8n410lbq.json?cats=PDS+Constraints,Hubble+Mission+Constraints'
        self._run_json_equal_file(url, 'api_metadata_hst_09975_acs_j8n410lbq_cats_pds_hubble_constraints_json.json')

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

    def test__api_metadata2_hst_09975_acs_j8n410lbq_cats_pds_hubble_constraints_json(self):
        "[test_results_api.py] /api/metadata_v2: hst-09975-acs-j8n410lbq cats PDS, Hubble Constraints json"
        url = '/api/metadata_v2/hst-09975-acs-j8n410lbq.json?cats=PDS+Constraints,Hubble+Mission+Constraints'
        self._run_json_equal_file(url, 'api_metadata2_hst_09975_acs_j8n410lbq_cats_pds_hubble_constraints_json.json')

    def test__api_metadata_hst_09975_acs_j8n410lbq_cats_pds_hubble_constraints_html(self):
        "[test_results_api.py] /api/metadata: hst-09975-acs-j8n410lbq cats PDS, Hubble Constraints html"
        url = '/api/metadata/hst-09975-acs-j8n410lbq.html?cats=PDS+Constraints,Hubble+Mission+Constraints'
        self._run_html_equal_file(url, 'api_metadata_hst_09975_acs_j8n410lbq_cats_pds_hubble_constraints_html.html')

    def test__api_metadata2_hst_09975_acs_j8n410lbq_cats_pds_hubble_constraints_html(self):
        "[test_results_api.py] /api/metadata_v2: hst-09975-acs-j8n410lbq cats PDS, Hubble Constraints html"
        url = '/api/metadata_v2/hst-09975-acs-j8n410lbq.html?cats=PDS+Constraints,Hubble+Mission+Constraints'
        self._run_html_equal_file(url, 'api_metadata2_hst_09975_acs_j8n410lbq_cats_pds_hubble_constraints_html.html')

    def test__api_metadata_hst_09975_acs_j8n410lbq_cats_pds_hubble_constraints_csv(self):
        "[test_results_api.py] /api/metadata: hst-09975-acs-j8n410lbq cats PDS, Hubble Constraints csv"
        url = '/api/metadata/hst-09975-acs-j8n410lbq.csv?cats=PDS+Constraints,Hubble+Mission+Constraints'
        self._run_csv_equal_file(url, 'api_metadata_hst_09975_acs_j8n410lbq_cats_pds_hubble_constraints_csv.csv')

    def test__api_metadata2_hst_09975_acs_j8n410lbq_cats_pds_hubble_constraints_csv(self):
        "[test_results_api.py] /api/metadata_v2: hst-09975-acs-j8n410lbq cats PDS, Hubble Constraints csv"
        url = '/api/metadata_v2/hst-09975-acs-j8n410lbq.csv?cats=PDS+Constraints,Hubble+Mission+Constraints'
        self._run_csv_equal_file(url, 'api_metadata2_hst_09975_acs_j8n410lbq_cats_pds_hubble_constraints_csv.csv')

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
                        HTTP404_UNKNOWN_RING_OBS_ID(None,
                                '/api/metadata/S_IMG_VG2_ISS_4360846_N.json'))

    def test__api_metadata2_bad_opusid_json(self):
        "[test_results_api.py] /api/metadata_v2: bad opusid json"
        url = '/api/metadata_v2/vg-iss-2-s-,c4360845.json'
        self._run_status_equal(url, 404)

    def test__api_metadata2_bad_ringobsid_json(self):
        "[test_results_api.py] /api/metadata_v2: bad ringobsid json"
        url = '/api/metadata_v2/S_IMG_VG2_ISS_4360846_N.json'
        self._run_status_equal(url, 404,
                    HTTP404_UNKNOWN_RING_OBS_ID(None,
                            '/api/metadata_v2/S_IMG_VG2_ISS_4360846_N.json'))

    def test__api_metadata_bad_opusid_html(self):
        "[test_results_api.py] /api/metadata: bad opusid html"
        url = '/api/metadata/vg-iss-2s-c4360845.html'
        self._run_status_equal(url, 404,
                    HTTP404_UNKNOWN_OPUS_ID('vg-iss-2s-c4360845',
                            '/api/metadata/vg-iss-2s-c4360845.html'))

    def test__api_metadata2_bad_opusid_html(self):
        "[test_results_api.py] /api/metadata_v2: bad opusid html"
        url = '/api/metadata_v2/,,,.html'
        self._run_status_equal(url, 404)

    def test__api_metadata_bad_opusid_csv(self):
        "[test_results_api.py] /api/metadata: bad opusid csv"
        url = '/api/metadata/0124.csv'
        self._run_status_equal(url, 404,
                    HTTP404_UNKNOWN_OPUS_ID('0124', '/api/metadata/0124.csv'))

    def test__api_metadata2_bad_opusid_csv(self):
        "[test_results_api.py] /api/metadata_v2: bad opusid csv"
        url = '/api/metadata_v2/1.csv'
        self._run_status_equal(url, 404,
                    HTTP404_UNKNOWN_OPUS_ID('1', '/api/metadata_v2/1.csv'))

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
            HTTP404_UNKNOWN_CATEGORY('/api/metadata/vg-iss-2-s-c4360845.json'))

    def test__api_metadata_bad_cats2_json(self):
        "[test_results_api.py] /api/metadata: bad cats 2 json"
        url = '/api/metadata/vg-iss-2-s-c4360845.json?cats=,obs_pds,obs_general'
        self._run_status_equal(url, 404,
            HTTP404_UNKNOWN_CATEGORY('/api/metadata/vg-iss-2-s-c4360845.json'))

    def test__api_metadata_bad_cats3_json(self):
        "[test_results_api.py] /api/metadata: bad cats 3 json"
        url = '/api/metadata/vg-iss-2-s-c4360845.json?cats=obs_pds,,obs_general'
        self._run_status_equal(url, 404,
            HTTP404_UNKNOWN_CATEGORY('/api/metadata/vg-iss-2-s-c4360845.json'))

    def test__api_metadata_bad_cats4_json(self):
        "[test_results_api.py] /api/metadata: bad cats 4 json"
        url = '/api/metadata/vg-iss-2-s-c4360845.json?cats=obs_pds,obs_general,'
        self._run_status_equal(url, 404,
            HTTP404_UNKNOWN_CATEGORY('/api/metadata/vg-iss-2-s-c4360845.json'))


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


            #############################################
            ######### /api/categories API TESTS #########
            #############################################

    def test__api_categories_bad_opusid(self):
        "[test_results_api.py] /api/categories: Bad OPUSID"
        url = '/api/categories/co-iss-w1866145657x.json'
        expected = []
        self._run_json_equal(url, expected)

    def test__api_categories_vg_iss_2_s_c4360004(self):
        "[test_results_api.py] /api/categories: vg-iss-2-s-c4360004"
        url = '/api/categories/vg-iss-2-s-c4360004.json'
        expected = [{"table_name": "obs_general", "label": "General Constraints"}, {"table_name": "obs_pds", "label": "PDS Constraints"}, {"table_name": "obs_type_image", "label": "Image Constraints"}, {"table_name": "obs_wavelength", "label": "Wavelength Constraints"}, {"table_name": "obs_profile", "label": "Occultation/Reflectance Profiles Constraints"}, {"table_name": "obs_surface_geometry", "label": "Surface Geometry Constraints"}, {"table_name": "obs_surface_geometry__saturn", "label": "Saturn Surface Geometry Constraints"}, {"table_name": "obs_surface_geometry__titan", "label": "Titan Surface Geometry Constraints"}, {"table_name": "obs_ring_geometry", "label": "Ring Geometry Constraints"}, {"table_name": "obs_mission_voyager", "label": "Voyager Mission Constraints"}, {"table_name": "obs_instrument_vgiss", "label": "Voyager ISS Constraints"}]
        self._run_json_equal(url, expected)

    def test__api_categories_COISS_2002(self):
        "[test_results_api.py] /api/categories: COISS_2002"
        url = '/api/categories.json?volumeid=COISS_2002'
        expected = [{"table_name": "obs_general", "label": "General Constraints"}, {"table_name": "obs_pds", "label": "PDS Constraints"}, {"table_name": "obs_type_image", "label": "Image Constraints"}, {"table_name": "obs_wavelength", "label": "Wavelength Constraints"}, {"table_name": "obs_profile", "label": "Occultation/Reflectance Profiles Constraints"}, {"table_name": "obs_surface_geometry", "label": "Surface Geometry Constraints"}, {"table_name": "obs_ring_geometry", "label": "Ring Geometry Constraints"}, {"table_name": "obs_mission_cassini", "label": "Cassini Mission Constraints"}, {"table_name": "obs_instrument_coiss", "label": "Cassini ISS Constraints"}]
        self._run_json_equal(url, expected)


            ################################################
            ######### /api/product_types API TESTS #########
            ################################################

    def test__api_product_types_bad_opusid(self):
        "[test_results_api.py] /api/product_types: Bad OPUSID"
        url = '/api/product_types/co-iss-w1866145657x.json'
        expected = []
        self._run_json_equal(url, expected)

    def test__api_product_types_vg_iss_2_s_c4360004(self):
        "[test_results_api.py] /api/product_types: vg-iss-2-s-c4360004"
        url = '/api/product_types/vg-iss-2-s-c4360004.json'
        self._run_json_equal_file(url, 'api_product_types_vg_iss_2_s_c4360004.json')

    def test__api_product_types_COISS_2002(self):
        "[test_results_api.py] /api/product_types: COISS_2002"
        url = '/api/product_types.json?volumeid=COISS_2002'
        self._run_json_equal_file(url, 'api_product_types_COISS_2002.json')
