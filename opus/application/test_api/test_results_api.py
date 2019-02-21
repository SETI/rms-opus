# opus/application/test_api/test_results_api.py

import json
import requests
from unittest import TestCase

from rest_framework.test import RequestsClient

from api_test_helper import ApiTestHelper

import settings

import logging
log = logging.getLogger(__name__)

settings.CACHE_BACKEND = 'dummy:///'

class ApiResultsTests(TestCase, ApiTestHelper):
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


            #############################################
            ######### /api/dataimages API TESTS #########
            #############################################

# reqno
    def test__api_dataimages_no_results_default(self):
        "/__api/dataimages: no results default cols"
        url = '/opus/__api/dataimages.json?opusid=notgoodid'
        self._run_status_equal(url, 404, settings.HTTP404_MISSING_REQNO)

    def test__api_dataimages_no_results_default_reqno(self):
        "/__api/dataimages: no results default cols reqno"
        url = '/opus/__api/dataimages.json?opusid=notgoodid&reqno=5'
        self._run_status_equal(url, 200)

    def test__api_dataimages_no_results_default_reqno_bad(self):
        "/__api/dataimages: no results default cols reqno bad"
        url = '/opus/__api/dataimages.json?opusid=notgoodid&reqno=-1'
        self._run_status_equal(url, 404, settings.HTTP404_MISSING_REQNO)

    def test__api_dataimages_no_results_default_reqno_bad_2(self):
        "/__api/dataimages: no results default cols reqno bad 2"
        url = '/opus/__api/dataimages.json?opusid=notgoodid&reqno=1.0'
        self._run_status_equal(url, 404, settings.HTTP404_MISSING_REQNO)


            #######################################
            ######### /api/data API TESTS #########
            #######################################

    def test__api_data_CASSINIrevno_sort(self):
        "/api/data: CASSINIrevno sort"
        url = '/opus/api/data.json?instrument=Cassini+ISS,Cassini+VIMS&CASSINIrevno=000,00A,00B,00C,003&CASSINItargetcode=RI+(Rings+-+general)&limit=5000&order=time1&cols=opusid,CASSINIrevno&order=-CASSINIrevnoint1'
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
        "/api/data: no results default cols json"
        url = '/opus/api/data.json?opusid=notgoodid'
        expected = {}
        self._run_json_equal_file(url, 'api_data_no_results_default_json.json')

    def test__api_data_no_results_default_csv(self):
        "/api/data: no results default cols csv"
        url = '/opus/api/data.csv?opusid=notgoodid'
        expected = b'OPUS ID,Instrument Name,Planet,Intended Target Name,Observation Start Time,Observation Duration (secs)\n'
        self._run_csv_equal(url, expected)

    def test__api_data_no_results_default_html(self):
        "/api/data: no results default cols html"
        url = '/opus/api/data.html?opusid=notgoodid'
        self._run_html_equal_file(url, 'api_data_no_results_default_html.html')

    def test__api_data_no_results_empty_cols_json(self):
        "/api/data: no results empty cols json"
        url = '/opus/api/data.json?opusid=notgoodid&cols='
        expected = {"limit": 100, "page": [], "order": "time1,opusid", "count": 0, "labels": [], "columns": [], "start_obs": 1}
        self._run_json_equal(url, expected)

    def test__api_data_no_results_empty_cols_csv(self):
        "/api/data: no results empty cols csv"
        url = '/opus/api/data.csv?opusid=notgoodid&cols='
        expected = b''
        self._run_csv_equal(url, expected)

    def test__api_data_no_results_empty_cols_html(self):
        "/api/data: no results empty cols html"
        url = '/opus/api/data.html?opusid=notgoodid&cols='
        expected = b'<table>\n<tr>\n</tr>\n</table>\n'
        self._run_html_equal(url, expected)

    def test__api_data_coiss_2002_more_cols_json(self):
        "/api/data: coiss_2002 more cols json"
        url = '/opus/api/data.json?cols=opusid,instrument,planet,target,time1,observationduration,CASSINIspacecraftclockcount1,CASSINIobsname,CASSINIactivityname,CASSINImissionphasename,CASSINItargetcode,CASSINIrevnoint1,CASSINIprimeinst,CASSINIisprime,CASSINIsequenceid,CASSINIspacecraftclockcount2,CASSINIert1,CASSINIert2,COISScamera,COISSfilter,COISSshuttermode,COISSshutterstate,COISScompressiontype,COISSdataconversiontype,COISSgainmode,COISSinstrumentmode,COISSmissinglines1,COISSimagenumber1,COISStargetdesc,COISSimageobservationtype&volumeid=COISS_2002'
        self._run_json_equal_file(url, 'api_data_coiss_2002_more_cols_json.json')

    def test__api_data_coiss_2002_more_cols_csv(self):
        "/api/data: coiss_2002 more cols csv"
        url = '/opus/api/data.csv?cols=opusid,instrument,planet,target,time1,observationduration,CASSINIspacecraftclockcount1,CASSINIobsname,CASSINIactivityname,CASSINImissionphasename,CASSINItargetcode,CASSINIrevnoint1,CASSINIprimeinst,CASSINIisprime,CASSINIsequenceid,CASSINIspacecraftclockcount2,CASSINIert1,CASSINIert2,COISScamera,COISSfilter,COISSshuttermode,COISSshutterstate,COISScompressiontype,COISSdataconversiontype,COISSgainmode,COISSinstrumentmode,COISSmissinglines1,COISSimagenumber1,COISStargetdesc,COISSimageobservationtype&volumeid=COISS_2002'
        self._run_csv_equal_file(url, 'api_data_coiss_2002_more_cols_csv.csv')

    def test__api_data_coiss_2002_more_cols_html(self):
        "/api/data: coiss_2002 more cols html"
        url = '/opus/api/data.html?cols=opusid,instrument,planet,target,time1,observationduration,CASSINIspacecraftclockcount1,CASSINIobsname,CASSINIactivityname,CASSINImissionphasename,CASSINItargetcode,CASSINIrevnoint1,CASSINIprimeinst,CASSINIisprime,CASSINIsequenceid,CASSINIspacecraftclockcount2,CASSINIert1,CASSINIert2,COISScamera,COISSfilter,COISSshuttermode,COISSshutterstate,COISScompressiontype,COISSdataconversiontype,COISSgainmode,COISSinstrumentmode,COISSmissinglines1,COISSimagenumber1,COISStargetdesc,COISSimageobservationtype&volumeid=COISS_2002'
        self._run_html_equal_file(url, 'api_data_coiss_2002_more_cols_html.html')

    def test__api_data_bad_cols_json(self):
        "/api/data: bad cols 1 json"
        url = '/opus/api/data.json?volumeid=COISS_2002&cols=observationduration,fredethel,volumeid'
        self._run_status_equal(url, 404, settings.HTTP404_UNKNOWN_SLUG)

    def test__api_data_bad_cols_csv(self):
        "/api/data: bad cols 1 csv"
        url = '/opus/api/data.csv?volumeid=COISS_2002&cols=observationduration,fredethel,volumeid'
        self._run_status_equal(url, 404, settings.HTTP404_UNKNOWN_SLUG)

    def test__api_data_bad_cols_html(self):
        "/api/data: bad cols 1 html"
        url = '/opus/api/data.html?volumeid=COISS_2002&cols=observationduration,fredethel,volumeid'
        self._run_status_equal(url, 404, settings.HTTP404_UNKNOWN_SLUG)

    def test__api_data_bad_cols2_json(self):
        "/api/data: bad cols 2 json"
        url = '/opus/api/data.json?volumeid=COISS_2002&cols=,observationduration,volumeid'
        self._run_status_equal(url, 404, settings.HTTP404_UNKNOWN_SLUG)

    def test__api_data_bad_cols3_json(self):
        "/api/data: bad cols 3 json"
        url = '/opus/api/data.json?volumeid=COISS_2002&cols=observationduration,,volumeid'
        self._run_status_equal(url, 404, settings.HTTP404_UNKNOWN_SLUG)

    def test__api_data_bad_cols4_json(self):
        "/api/data: bad cols 4 json"
        url = '/opus/api/data.json?volumeid=COISS_2002&cols=observationduration,volumeid,'
        self._run_status_equal(url, 404, settings.HTTP404_UNKNOWN_SLUG)



            ################################################
            ######### /api/metadata[_v2] API TESTS #########
            ################################################

    # All metadata
    def test__api_metadata_vg_iss_2_s_c4360845_default_json(self):
        "/api/metadata: vg-iss-2-s-c4360845 default json"
        url = '/opus/api/metadata/vg-iss-2-s-c4360845.json'
        self._run_json_equal_file(url, 'api_metadata_vg_iss_2_s_c4360845_default_json.json')

    def test__api_metadata2_vg_iss_2_s_c4360845_default_json(self):
        "/api/metadata_v2: vg-iss-2-s-c4360845 default json"
        url = '/opus/api/metadata_v2/vg-iss-2-s-c4360845.json'
        self._run_json_equal_file(url, 'api_metadata2_vg_iss_2_s_c4360845_default_json.json')

    def test__api_metadata_vg_iss_2_s_c4360845_default_html(self):
        "/api/metadata: vg-iss-2-s-c4360845 default html"
        url = '/opus/api/metadata/vg-iss-2-s-c4360845.html'
        self._run_html_equal_file(url, 'api_metadata_vg_iss_2_s_c4360845_default_html.html')

    def test__api_metadata2_vg_iss_2_s_c4360845_default_html(self):
        "/api/metadata_v2: vg-iss-2-s-c4360845 default html"
        url = '/opus/api/metadata_v2/vg-iss-2-s-c4360845.html'
        self._run_html_equal_file(url, 'api_metadata2_vg_iss_2_s_c4360845_default_html.html')

    def test__api_metadata2_vg_iss_2_s_c4360845_default_html_private(self):
        "/api/metadata_v2: vg-iss-2-s-c4360845 default html private"
        url = '/opus/__api/metadata_v2/vg-iss-2-s-c4360845.html'
        expected = b'<ul id="detail__data_general_constraints">\n<li>\nPlanet: Saturn\n<i class="fa fa-info-circle"'
        self._run_html_startswith(url, expected)

    def test__api_metadata_vg_iss_2_s_c4360845_default_csv(self):
        "/api/metadata: vg-iss-2-s-c4360845 default csv"
        url = '/opus/api/metadata/vg-iss-2-s-c4360845.csv'
        self._run_csv_equal_file(url, 'api_metadata_vg_iss_2_s_c4360845_default_csv.csv')

    def test__api_metadata2_vg_iss_2_s_c4360845_default_csv(self):
        "/api/metadata_v2: vg-iss-2-s-c4360845 default csv"
        url = '/opus/api/metadata_v2/vg-iss-2-s-c4360845.csv'
        self._run_csv_equal_file(url, 'api_metadata2_vg_iss_2_s_c4360845_default_csv.csv')

    # Specified columns, empty
    def test__api_metadata_vg_iss_2_s_c4360845_cols_empty_json(self):
        "/api/metadata: vg-iss-2-s-c4360845 cols empty json"
        url = '/opus/api/metadata/vg-iss-2-s-c4360845.json?cols='
        expected = []
        self._run_json_equal(url, expected)

    def test__api_metadata2_vg_iss_2_s_c4360845_cols_empty_json(self):
        "/api/metadata_v2: vg-iss-2-s-c4360845 cols empty json"
        url = '/opus/api/metadata_v2/vg-iss-2-s-c4360845.json?cols='
        expected = []
        self._run_json_equal(url, expected)

    def test__api_metadata_vg_iss_2_s_c4360845_cols_empty_html(self):
        "/api/metadata: vg-iss-2-s-c4360845 cols empty html"
        url = '/opus/api/metadata/vg-iss-2-s-c4360845.html?cols='
        expected = b'<dl>\n</dl>\n'
        self._run_html_equal(url, expected)

    def test__api_metadata2_vg_iss_2_s_c4360845_cols_empty_html(self):
        "/api/metadata_v2: vg-iss-2-s-c4360845 cols empty html"
        url = '/opus/api/metadata_v2/vg-iss-2-s-c4360845.html?cols='
        expected = b'<dl>\n</dl>\n'
        self._run_html_equal(url, expected)

    def test__api_metadata2_vg_iss_2_s_c4360845_cols_empty_html_private(self):
        "/api/metadata_v2: vg-iss-2-s-c4360845 cols empty html private"
        url = '/opus/__api/metadata_v2/vg-iss-2-s-c4360845.html?cols='
        expected = b'<ul class="columns_metadata">\n</ul>\n'
        self._run_html_equal(url, expected)

    def test__api_metadata_vg_iss_2_s_c4360845_cols_empty_csv(self):
        "/api/metadata: vg-iss-2-s-c4360845 cols empty csv"
        url = '/opus/api/metadata/vg-iss-2-s-c4360845.csv?cols='
        expected = b''
        self._run_csv_equal(url, expected)

    def test__api_metadata2_vg_iss_2_s_c4360845_cols_empty_csv(self):
        "/api/metadata_v2: vg-iss-2-s-c4360845 cols empty csv"
        url = '/opus/api/metadata_v2/vg-iss-2-s-c4360845.csv?cols='
        expected = b''
        self._run_csv_equal(url, expected)

    # Specified columns, opusid only
    def test__api_metadata_vg_iss_2_s_c4360845_cols_opusid_json(self):
        "/api/metadata: vg-iss-2-s-c4360845 cols opusid json"
        url = '/opus/api/metadata/vg-iss-2-s-c4360845.json?cols=opusid'
        expected = [{"opusid": "vg-iss-2-s-c4360845"}]
        self._run_json_equal(url, expected)

    def test__api_metadata2_vg_iss_2_s_c4360845_cols_opusid_json(self):
        "/api/metadata_v2: vg-iss-2-s-c4360845 cols opusid json"
        url = '/opus/api/metadata_v2/vg-iss-2-s-c4360845.json?cols=opusid'
        expected = [{"opusid": "vg-iss-2-s-c4360845"}]
        self._run_json_equal(url, expected)

    def test__api_metadata2_nh_lorri_lor_0284457489_cols_opusid_json(self):
        "/api/metadata_v2: nh-lorri-lor_0284457489 cols opusid json"
        # Check an OPUS ID with a _ in it which can screw up database searches
        url = '/opus/api/metadata_v2/nh-lorri-lor_0284457489.json?cols=opusid'
        expected = [{"opusid": "nh-lorri-lor_0284457489"}]
        self._run_json_equal(url, expected)

    def test__api_metadata_vg_iss_2_s_c4360845_cols_opusid_html(self):
        "/api/metadata: vg-iss-2-s-c4360845 cols opusid html"
        url = '/opus/api/metadata/vg-iss-2-s-c4360845.html?cols=opusid'
        expected = b'<dl>\n<dt>OPUS ID</dt><dd>vg-iss-2-s-c4360845</dd>\n</dl>\n'
        self._run_html_equal(url, expected)

    def test__api_metadata2_vg_iss_2_s_c4360845_cols_opusid_html(self):
        "/api/metadata_v2: vg-iss-2-s-c4360845 cols opusid html"
        url = '/opus/api/metadata_v2/vg-iss-2-s-c4360845.html?cols=opusid'
        expected = b'<dl>\n<dt>OPUS ID</dt><dd>vg-iss-2-s-c4360845</dd>\n</dl>\n'
        self._run_html_equal(url, expected)

    def test__api_metadata2_vg_iss_2_s_c4360845_cols_opusid_html_private(self):
        "/api/metadata_v2: vg-iss-2-s-c4360845 cols opusid html private"
        url = '/opus/__api/metadata_v2/vg-iss-2-s-c4360845.html?cols=opusid'
        expected = b'<ul class="columns_metadata">\n<li>\nOPUS ID: vg-iss-2-s-c4360845\n<i class="fa fa-info-circle" data-toggle="tooltip"\n'
        self._run_html_startswith(url, expected)

    def test__api_metadata_vg_iss_2_s_c4360845_cols_opusid_csv(self):
        "/api/metadata: vg-iss-2-s-c4360845 cols opusid csv"
        url = '/opus/api/metadata/vg-iss-2-s-c4360845.csv?cols=opusid'
        expected = b'OPUS ID\nvg-iss-2-s-c4360845\n'
        self._run_csv_equal(url, expected)

    def test__api_metadata2_vg_iss_2_s_c4360845_cols_opusid_csv(self):
        "/api/metadata_v2: vg-iss-2-s-c4360845 cols opusid csv"
        url = '/opus/api/metadata_v2/vg-iss-2-s-c4360845.csv?cols=opusid'
        expected = b'OPUS ID\nvg-iss-2-s-c4360845\n'
        self._run_csv_equal(url, expected)

    # Specified columns, all Voyager or Cassini slugs
    def test__api_metadata_vg_iss_2_s_c4365507_cols_all_voyager_json(self):
        "/api/metadata: vg-iss-2-s-c4365507 cols all voyager json"
        url = '/opus/api/metadata/vg-iss-2-s-c4365507.json?cols=opusid,VOYAGERmissionphasename,VOYAGERspacecraftclockcount1,VOYAGERspacecraftclockcount2,VOYAGERert1,VGISScamera,VGISSfilter,VGISSfilternumber,VGISSshuttermode,VGISSeditmode,VGISSgainmode,VGISSscanmode,VGISSimageid,VGISSusablelines1,VGISSusablesamples1'
        self._run_json_equal_file(url, 'api_metadata_vg_iss_2_s_c4365507_cols_all_voyager_json.json')

    def test__api_metadata2_vg_iss_2_s_c4365507_cols_all_voyager_json(self):
        "/api/metadata_v2: vg-iss-2-s-c4365507 cols all voyager json"
        url = '/opus/api/metadata_v2/vg-iss-2-s-c4365507.json?cols=opusid,VOYAGERmissionphasename,VOYAGERspacecraftclockcount1,VOYAGERspacecraftclockcount2,VOYAGERert1,VGISScamera,VGISSfilter,VGISSfilternumber,VGISSshuttermode,VGISSeditmode,VGISSgainmode,VGISSscanmode,VGISSimageid,VGISSusablelines1,VGISSusablesamples1'
        self._run_json_equal_file(url, 'api_metadata2_vg_iss_2_s_c4365507_cols_all_voyager_json.json')

    def test__api_metadata_vg_iss_2_s_c4365507_cols_all_cassini_json(self):
        "/api/metadata: vg-iss-2-s-c4365507 cols all cassini json"
        url = '/opus/api/metadata/vg-iss-2-s-c4365507.json?cols=opusid,volumeid,greaterpixelsize1,lesserpixelsize1,wavelength1,wavelength2,CASSINIobsname,CASSINIactivityname,CASSINImissionphasename,CASSINItargetcode,CASSINIrevnoint1,CASSINIprimeinst,CASSINIisprime,CASSINIsequenceid,CASSINIspacecraftclockcount1,CASSINIspacecraftclockcount2,CASSINIert1,CASSINIert2'
        self._run_json_equal_file(url, 'api_metadata_vg_iss_2_s_c4365507_cols_all_cassini_json.json')

    def test__api_metadata2_vg_iss_2_s_c4365507_cols_all_cassini_json(self):
        "/api/metadata_v2: vg-iss-2-s-c4365507 cols all cassini json"
        url = '/opus/api/metadata_v2/vg-iss-2-s-c4365507.json?cols=opusid,volumeid,greaterpixelsize1,lesserpixelsize1,wavelength1,wavelength2,CASSINIobsname,CASSINIactivityname,CASSINImissionphasename,CASSINItargetcode,CASSINIrevnoint1,CASSINIprimeinst,CASSINIisprime,CASSINIsequenceid,CASSINIspacecraftclockcount1,CASSINIspacecraftclockcount2,CASSINIert1,CASSINIert2'
        self._run_json_equal_file(url, 'api_metadata2_vg_iss_2_s_c4365507_cols_all_cassini_json.json')

    def test__api_metadata_vg_iss_2_s_c4365507_cols_all_voyager_html(self):
        "/api/metadata: vg-iss-2-s-c4365507 cols all voyager html"
        url = '/opus/api/metadata/vg-iss-2-s-c4365507.html?cols=opusid,VOYAGERmissionphasename,VOYAGERspacecraftclockcount1,VOYAGERspacecraftclockcount2,VOYAGERert1,VGISScamera,VGISSfilter,VGISSfilternumber,VGISSshuttermode,VGISSeditmode,VGISSgainmode,VGISSscanmode,VGISSimageid,VGISSusablelines1,VGISSusablesamples1'
        self._run_html_equal_file(url, 'api_metadata_vg_iss_2_s_c4365507_cols_all_voyager_html.html')

    def test__api_metadata2_vg_iss_2_s_c4365507_cols_all_voyager_html(self):
        "/api/metadata_v2: vg-iss-2-s-c4365507 cols all voyager html"
        url = '/opus/api/metadata_v2/vg-iss-2-s-c4365507.html?cols=opusid,VOYAGERmissionphasename,VOYAGERspacecraftclockcount1,VOYAGERspacecraftclockcount2,VOYAGERert1,VGISScamera,VGISSfilter,VGISSfilternumber,VGISSshuttermode,VGISSeditmode,VGISSgainmode,VGISSscanmode,VGISSimageid,VGISSusablelines1,VGISSusablesamples1'
        self._run_html_equal_file(url, 'api_metadata2_vg_iss_2_s_c4365507_cols_all_voyager_html.html')

    def test__api_metadata_vg_iss_2_s_c4365507_cols_all_cassini_html(self):
        "/api/metadata: vg-iss-2-s-c4365507 cols all cassini html"
        url = '/opus/api/metadata/vg-iss-2-s-c4365507.html?cols=opusid,volumeid,greaterpixelsize1,lesserpixelsize1,wavelength1,wavelength2,CASSINIobsname,CASSINIactivityname,CASSINImissionphasename,CASSINItargetcode,CASSINIrevnoint1,CASSINIprimeinst,CASSINIisprime,CASSINIsequenceid,CASSINIspacecraftclockcount1,CASSINIspacecraftclockcount2,CASSINIert1,CASSINIert2'
        self._run_html_equal_file(url, 'api_metadata_vg_iss_2_s_c4365507_cols_all_cassini_html.html')

    def test__api_metadata2_vg_iss_2_s_c4365507_cols_all_cassini_html(self):
        "/api/metadata_v2: vg-iss-2-s-c4365507 cols all cassini html"
        url = '/opus/api/metadata_v2/vg-iss-2-s-c4365507.html?cols=opusid,volumeid,greaterpixelsize1,lesserpixelsize1,wavelength1,wavelength2,CASSINIobsname,CASSINIactivityname,CASSINImissionphasename,CASSINItargetcode,CASSINIrevnoint1,CASSINIprimeinst,CASSINIisprime,CASSINIsequenceid,CASSINIspacecraftclockcount1,CASSINIspacecraftclockcount2,CASSINIert1,CASSINIert2'
        self._run_html_equal_file(url, 'api_metadata2_vg_iss_2_s_c4365507_cols_all_cassini_html.html')

    def test__api_metadata_vg_iss_2_s_c4365507_cols_all_voyager_csv(self):
        "/api/metadata: vg-iss-2-s-c4365507 cols all voyager csv"
        url = '/opus/api/metadata/vg-iss-2-s-c4365507.csv?cols=opusid,VOYAGERmissionphasename,VOYAGERspacecraftclockcount1,VOYAGERspacecraftclockcount2,VOYAGERert1,VGISScamera,VGISSfilter,VGISSfilternumber,VGISSshuttermode,VGISSeditmode,VGISSgainmode,VGISSscanmode,VGISSimageid,VGISSusablelines1,VGISSusablesamples1'
        self._run_csv_equal_file(url, 'api_metadata_vg_iss_2_s_c4365507_cols_all_voyager_csv.csv')

    def test__api_metadata2_vg_iss_2_s_c4365507_cols_all_voyager_csv(self):
        "/api/metadata_v2: vg-iss-2-s-c4365507 cols all voyager csv"
        url = '/opus/api/metadata_v2/vg-iss-2-s-c4365507.csv?cols=opusid,VOYAGERmissionphasename,VOYAGERspacecraftclockcount1,VOYAGERspacecraftclockcount2,VOYAGERert1,VGISScamera,VGISSfilter,VGISSfilternumber,VGISSshuttermode,VGISSeditmode,VGISSgainmode,VGISSscanmode,VGISSimageid,VGISSusablelines1,VGISSusablesamples1'
        self._run_csv_equal_file(url, 'api_metadata2_vg_iss_2_s_c4365507_cols_all_voyager_csv.csv')

    def test__api_metadata_vg_iss_2_s_c4365507_cols_all_cassini_csv(self):
        "/api/metadata: vg-iss-2-s-c4365507 cols all cassini csv"
        url = '/opus/api/metadata/vg-iss-2-s-c4365507.csv?cols=opusid,volumeid,greaterpixelsize1,lesserpixelsize1,wavelength1,wavelength2,CASSINIobsname,CASSINIactivityname,CASSINImissionphasename,CASSINItargetcode,CASSINIrevnoint1,CASSINIprimeinst,CASSINIisprime,CASSINIsequenceid,CASSINIspacecraftclockcount1,CASSINIspacecraftclockcount2,CASSINIert1,CASSINIert2'
        self._run_csv_equal_file(url, 'api_metadata_vg_iss_2_s_c4365507_cols_all_cassini_csv.csv')

    def test__api_metadata2_vg_iss_2_s_c4365507_cols_all_cassini_csv(self):
        "/api/metadata_v2: vg-iss-2-s-c4365507 cols all cassini csv"
        url = '/opus/api/metadata_v2/vg-iss-2-s-c4365507.csv?cols=opusid,volumeid,greaterpixelsize1,lesserpixelsize1,wavelength1,wavelength2,CASSINIobsname,CASSINIactivityname,CASSINImissionphasename,CASSINItargetcode,CASSINIrevnoint1,CASSINIprimeinst,CASSINIisprime,CASSINIsequenceid,CASSINIspacecraftclockcount1,CASSINIspacecraftclockcount2,CASSINIert1,CASSINIert2'
        self._run_csv_equal_file(url, 'api_metadata2_vg_iss_2_s_c4365507_cols_all_cassini_csv.csv')

    # Specified cats, empty
    def test__api_metadata_hst_09975_acs_j8n410lb_cats_empty_json(self):
        "/api/metadata: hst-09975-acs-j8n410lb cats empty json"
        url = '/opus/api/metadata/hst-09975-acs-j8n410lb.json?cats='
        expected = {}
        self._run_json_equal(url, expected)

    def test__api_metadata2_hst_09975_acs_j8n410lb_cats_empty_json(self):
        "/api/metadata_v2: hst-09975-acs-j8n410lb cats empty json"
        url = '/opus/api/metadata_v2/hst-09975-acs-j8n410lb.json?cats='
        expected = {}
        self._run_json_equal(url, expected)

    def test__api_metadata_hst_09975_acs_j8n410lb_cats_empty_html(self):
        "/api/metadata: hst-09975-acs-j8n410lb cats empty html"
        url = '/opus/api/metadata/hst-09975-acs-j8n410lb.html?cats='
        expected = b'<dl>\n</dl>\n'
        self._run_html_equal(url, expected)

    def test__api_metadata2_hst_09975_acs_j8n410lb_cats_empty_html(self):
        "/api/metadata_v2: hst-09975-acs-j8n410lb cats empty html"
        url = '/opus/api/metadata_v2/hst-09975-acs-j8n410lb.html?cats='
        expected = b'<dl>\n</dl>\n'
        self._run_html_equal(url, expected)

    def test__api_metadata_hst_09975_acs_j8n410lb_cats_empty_csv(self):
        "/api/metadata: hst-09975-acs-j8n410lb cats empty csv"
        url = '/opus/api/metadata/hst-09975-acs-j8n410lb.csv?cats='
        expected = b''
        self._run_csv_equal(url, expected)

    def test__api_metadata2_hst_09975_acs_j8n410lb_cats_empty_csv(self):
        "/api/metadata_v2: hst-09975-acs-j8n410lb cats empty csv"
        url = '/opus/api/metadata_v2/hst-09975-acs-j8n410lb.csv?cats='
        expected = b''
        self._run_csv_equal(url, expected)

    # Specified cats, PDS Constraints only
    def test__api_metadata_hst_09975_acs_j8n410lb_cats_pds_constraints_json(self):
        "/api/metadata: hst-09975-acs-j8n410lb cats PDS Constraints json"
        url = '/opus/api/metadata/hst-09975-acs-j8n410lb.json?cats=PDS+Constraints'
        expected = [{"opusid": "hst-09975-acs-j8n410lb"}]
        self._run_json_equal_file(url, 'api_metadata_hst_09975_acs_j8n410lb_cats_pds_constraints_json.json')

    def test__api_metadata_hst_09975_acs_j8n410lb_cats_pds_constraints_lc_json(self):
        "/api/metadata: hst-09975-acs-j8n410lb cats pds constraints json"
        url = '/opus/api/metadata/hst-09975-acs-j8n410lb.json?cats=pds+CONSTRAINTS'
        expected = [{"opusid": "hst-09975-acs-j8n410lb"}]
        self._run_json_equal_file(url, 'api_metadata_hst_09975_acs_j8n410lb_cats_pds_constraints_json.json')

    def test__api_metadata_hst_09975_acs_j8n410lb_cats_pds_constraints_table_json(self):
        "/api/metadata: hst-09975-acs-j8n410lb cats pds constraints json"
        url = '/opus/api/metadata/hst-09975-acs-j8n410lb.json?cats=obs_pds'
        expected = [{"opusid": "hst-09975-acs-j8n410lb"}]
        self._run_json_equal_file(url, 'api_metadata_hst_09975_acs_j8n410lb_cats_pds_constraints_json.json')

    def test__api_metadata_hst_09975_acs_j8n410lb_cats_pds_constraints_table2_json(self):
        "/api/metadata: hst-09975-acs-j8n410lb cats pds constraints dup json"
        url = '/opus/api/metadata/hst-09975-acs-j8n410lb.json?cats=obs_pds,obs_pds'
        expected = [{"opusid": "hst-09975-acs-j8n410lb"}]
        self._run_json_equal_file(url, 'api_metadata_hst_09975_acs_j8n410lb_cats_pds_constraints_json.json')

    def test__api_metadata2_hst_09975_acs_j8n410lb_cats_pds_constraints_json(self):
        "/api/metadata_v2: hst-09975-acs-j8n410lb cats PDS Constraints json"
        url = '/opus/api/metadata_v2/hst-09975-acs-j8n410lb.json?cats=PDS+Constraints'
        expected = [{"opusid": "hst-09975-acs-j8n410lb"}]
        self._run_json_equal_file(url, 'api_metadata2_hst_09975_acs_j8n410lb_cats_pds_constraints_json.json')

    def test__api_metadata_hst_09975_acs_j8n410lb_cats_pds_constraints_html(self):
        "/api/metadata: hst-09975-acs-j8n410lb cats PDS Constraints html"
        url = '/opus/api/metadata/hst-09975-acs-j8n410lb.html?cats=PDS+Constraints'
        expected = b'<dl>\n<dt>OPUS ID</dt><dd>hst-09975-acs-j8n410lb</dd>\n</dl>\n'
        self._run_html_equal_file(url, 'api_metadata_hst_09975_acs_j8n410lb_cats_pds_constraints_html.html')

    def test__api_metadata2_hst_09975_acs_j8n410lb_cats_pds_constraints_html(self):
        "/api/metadata_v2: hst-09975-acs-j8n410lb cats PDS Constraints html"
        url = '/opus/api/metadata_v2/hst-09975-acs-j8n410lb.html?cats=PDS+Constraints'
        expected = b'<dl>\n<dt>OPUS ID</dt><dd>hst-09975-acs-j8n410lb</dd>\n</dl>\n'
        self._run_html_equal_file(url, 'api_metadata2_hst_09975_acs_j8n410lb_cats_pds_constraints_html.html')

    def test__api_metadata_hst_09975_acs_j8n410lb_cats_pds_constraints_csv(self):
        "/api/metadata: hst-09975-acs-j8n410lb cats PDS Constraints csv"
        url = '/opus/api/metadata/hst-09975-acs-j8n410lb.csv?cats=PDS+Constraints'
        expected = b'OPUS ID\nhst-09975-acs-j8n410lb\n'
        self._run_csv_equal_file(url, 'api_metadata_hst_09975_acs_j8n410lb_cats_pds_constraints_csv.csv')

    def test__api_metadata2_hst_09975_acs_j8n410lb_cats_pds_constraints_csv(self):
        "/api/metadata_v2: hst-09975-acs-j8n410lb cats PDS Constraints csv"
        url = '/opus/api/metadata_v2/hst-09975-acs-j8n410lb.csv?cats=PDS+Constraints'
        expected = b'OPUS ID\nhst-09975-acs-j8n410lb\n'
        self._run_csv_equal_file(url, 'api_metadata2_hst_09975_acs_j8n410lb_cats_pds_constraints_csv.csv')

    # Specified cats, PDS, Hubble Constraints
    def test__api_metadata_hst_09975_acs_j8n410lb_cats_pds_hubble_constraints_json(self):
        "/api/metadata: hst-09975-acs-j8n410lb cats PDS, Hubble Constraints json"
        url = '/opus/api/metadata/hst-09975-acs-j8n410lb.json?cats=PDS+Constraints,Hubble+Mission+Constraints'
        expected = [{"opusid": "hst-09975-acs-j8n410lb"}]
        self._run_json_equal_file(url, 'api_metadata_hst_09975_acs_j8n410lb_cats_pds_hubble_constraints_json.json')

    def test__api_metadata_hst_09975_acs_j8n410lb_cats_pds_hubble_constraints_lc_json(self):
        "/api/metadata: hst-09975-acs-j8n410lb cats PDS, Hubble Constraints json"
        url = '/opus/api/metadata/hst-09975-acs-j8n410lb.json?cats=PDS+Constraints,Hubble+Mission+Constraints'
        expected = [{"opusid": "hst-09975-acs-j8n410lb"}]
        self._run_json_equal_file(url, 'api_metadata_hst_09975_acs_j8n410lb_cats_pds_hubble_constraints_json.json')

    def test__api_metadata_hst_09975_acs_j8n410lb_cats_pds_hubble_constraints_table_json(self):
        "/api/metadata: hst-09975-acs-j8n410lb cats PDS, Hubble Constraints json"
        url = '/opus/api/metadata/hst-09975-acs-j8n410lb.json?cats=obs_pds,obs_mission_hubble'
        expected = [{"opusid": "hst-09975-acs-j8n410lb"}]
        self._run_json_equal_file(url, 'api_metadata_hst_09975_acs_j8n410lb_cats_pds_hubble_constraints_json.json')

    def test__api_metadata_hst_09975_acs_j8n410lb_cats_pds_hubble_constraints_table2_json(self):
        "/api/metadata: hst-09975-acs-j8n410lb cats PDS, Hubble Constraints rev json"
        url = '/opus/api/metadata/hst-09975-acs-j8n410lb.json?cats=obs_mission_hubble,obs_pds'
        expected = [{"opusid": "hst-09975-acs-j8n410lb"}]
        self._run_json_equal_file(url, 'api_metadata_hst_09975_acs_j8n410lb_cats_pds_hubble_constraints_json.json')

    def test__api_metadata2_hst_09975_acs_j8n410lb_cats_pds_hubble_constraints_json(self):
        "/api/metadata_v2: hst-09975-acs-j8n410lb cats PDS, Hubble Constraints json"
        url = '/opus/api/metadata_v2/hst-09975-acs-j8n410lb.json?cats=PDS+Constraints,Hubble+Mission+Constraints'
        expected = [{"opusid": "hst-09975-acs-j8n410lb"}]
        self._run_json_equal_file(url, 'api_metadata2_hst_09975_acs_j8n410lb_cats_pds_hubble_constraints_json.json')

    def test__api_metadata_hst_09975_acs_j8n410lb_cats_pds_hubble_constraints_html(self):
        "/api/metadata: hst-09975-acs-j8n410lb cats PDS, Hubble Constraints html"
        url = '/opus/api/metadata/hst-09975-acs-j8n410lb.html?cats=PDS+Constraints,Hubble+Mission+Constraints'
        expected = b'<dl>\n<dt>OPUS ID</dt><dd>hst-09975-acs-j8n410lb</dd>\n</dl>\n'
        self._run_html_equal_file(url, 'api_metadata_hst_09975_acs_j8n410lb_cats_pds_hubble_constraints_html.html')

    def test__api_metadata2_hst_09975_acs_j8n410lb_cats_pds_hubble_constraints_html(self):
        "/api/metadata_v2: hst-09975-acs-j8n410lb cats PDS, Hubble Constraints html"
        url = '/opus/api/metadata_v2/hst-09975-acs-j8n410lb.html?cats=PDS+Constraints,Hubble+Mission+Constraints'
        expected = b'<dl>\n<dt>OPUS ID</dt><dd>hst-09975-acs-j8n410lb</dd>\n</dl>\n'
        self._run_html_equal_file(url, 'api_metadata2_hst_09975_acs_j8n410lb_cats_pds_hubble_constraints_html.html')

    def test__api_metadata_hst_09975_acs_j8n410lb_cats_pds_hubble_constraints_csv(self):
        "/api/metadata: hst-09975-acs-j8n410lb cats PDS, Hubble Constraints csv"
        url = '/opus/api/metadata/hst-09975-acs-j8n410lb.csv?cats=PDS+Constraints,Hubble+Mission+Constraints'
        expected = b'OPUS ID\nhst-09975-acs-j8n410lb\n'
        self._run_csv_equal_file(url, 'api_metadata_hst_09975_acs_j8n410lb_cats_pds_hubble_constraints_csv.csv')

    def test__api_metadata2_hst_09975_acs_j8n410lb_cats_pds_hubble_constraints_csv(self):
        "/api/metadata_v2: hst-09975-acs-j8n410lb cats PDS, Hubble Constraints csv"
        url = '/opus/api/metadata_v2/hst-09975-acs-j8n410lb.csv?cats=PDS+Constraints,Hubble+Mission+Constraints'
        expected = b'OPUS ID\nhst-09975-acs-j8n410lb\n'
        self._run_csv_equal_file(url, 'api_metadata2_hst_09975_acs_j8n410lb_cats_pds_hubble_constraints_csv.csv')

    # Bad queries
    def test__api_metadata_bad_opusid_json(self):
        "/api/metadata: bad opusid json"
        url = '/opus/api/metadata/vg-iss-2-s-c4360845x.json'
        self._run_status_equal(url, 404, settings.HTTP404_UNKNOWN_OPUS_ID)

    def test__api_metadata2_bad_opusid_json(self):
        "/api/metadata_v2: bad opusid json"
        url = '/opus/api/metadata_v2/vg-iss-2-s-,c4360845.json'
        self._run_status_equal(url, 404, settings.HTTP404_UNKNOWN_OPUS_ID)

    def test__api_metadata_bad_opusid_html(self):
        "/api/metadata: bad opusid html"
        url = '/opus/api/metadata/vg-iss-2s-c4360845.html'
        self._run_status_equal(url, 404, settings.HTTP404_UNKNOWN_OPUS_ID)

    def test__api_metadata2_bad_opusid_html(self):
        "/api/metadata_v2: bad opusid html"
        url = '/opus/api/metadata_v2/,,,.html'
        self._run_status_equal(url, 404, settings.HTTP404_UNKNOWN_OPUS_ID)

    def test__api_metadata_bad_opusid_csv(self):
        "/api/metadata: bad opusid csv"
        url = '/opus/api/metadata/0124.csv'
        self._run_status_equal(url, 404, settings.HTTP404_UNKNOWN_OPUS_ID)

    def test__api_metadata2_bad_opusid_csv(self):
        "/api/metadata_v2: bad opusid csv"
        url = '/opus/api/metadata_v2/1.csv'
        self._run_status_equal(url, 404, settings.HTTP404_UNKNOWN_OPUS_ID)

    def test__api_metadata_bad_cols_json(self):
        "/api/metadata: bad cols 1 json"
        url = '/opus/api/metadata/vg-iss-2-s-c4360845.json?cols=observationduration,fredethel,volumeid'
        self._run_status_equal(url, 404, settings.HTTP404_UNKNOWN_SLUG)

    def test__api_metadata_bad_cols_csv(self):
        "/api/metadata: bad cols 1 csv"
        url = '/opus/api/metadata/vg-iss-2-s-c4360845.csv?cols=observationduration,fredethel,volumeid'
        self._run_status_equal(url, 404, settings.HTTP404_UNKNOWN_SLUG)

    def test__api_metadata_bad_cols_html(self):
        "/api/metadata: bad cols 1 html"
        url = '/opus/api/metadata/vg-iss-2-s-c4360845.html?cols=observationduration,fredethel,volumeid'
        self._run_status_equal(url, 404, settings.HTTP404_UNKNOWN_SLUG)

    def test__api_metadata_bad_cols2_json(self):
        "/api/metadata: bad cols 2 json"
        url = '/opus/api/metadata/vg-iss-2-s-c4360845.json?cols=,observationduration,volumeid'
        self._run_status_equal(url, 404, settings.HTTP404_UNKNOWN_SLUG)

    def test__api_metadata_bad_cols3_json(self):
        "/api/metadata: bad cols 3 json"
        url = '/opus/api/metadata/vg-iss-2-s-c4360845.json?cols=observationduration,,volumeid'
        self._run_status_equal(url, 404, settings.HTTP404_UNKNOWN_SLUG)

    def test__api_metadata_bad_cols4_json(self):
        "/api/metadata: bad cols 4 json"
        url = '/opus/api/metadata/vg-iss-2-s-c4360845.json?cols=observationduration,volumeid,'
        self._run_status_equal(url, 404, settings.HTTP404_UNKNOWN_SLUG)

    def test__api_metadata_bad_cats_json(self):
        "/api/metadata: bad cats 1 json"
        url = '/opus/api/metadata/vg-iss-2-s-c4360845.json?cats=obs_pds,whatever,obs_general'
        self._run_status_equal(url, 404, settings.HTTP404_UNKNOWN_CATEGORY)

    def test__api_metadata_bad_cats2_json(self):
        "/api/metadata: bad cats 2 json"
        url = '/opus/api/metadata/vg-iss-2-s-c4360845.json?cats=,obs_pds,obs_general'
        self._run_status_equal(url, 404, settings.HTTP404_UNKNOWN_CATEGORY)

    def test__api_metadata_bad_cats3_json(self):
        "/api/metadata: bad cats 3 json"
        url = '/opus/api/metadata/vg-iss-2-s-c4360845.json?cats=obs_pds,,obs_general'
        self._run_status_equal(url, 404, settings.HTTP404_UNKNOWN_CATEGORY)

    def test__api_metadata_bad_cats4_json(self):
        "/api/metadata: bad cats 4 json"
        url = '/opus/api/metadata/vg-iss-2-s-c4360845.json?cats=obs_pds,obs_general,'
        self._run_status_equal(url, 404, settings.HTTP404_UNKNOWN_CATEGORY)


            ########################################
            ######### /api/files API TESTS #########
            ########################################

    def test__api_files_COISS_no_versions_w1866145657(self):
        "/api/files: COISS no versions w1866145657"
        url = '/opus/api/files/co-iss-w1866145657.json'
        self._run_json_equal_file(url, 'api_files_COISS_no_versions_w1866145657.json')

    def test__api_files_COISS_versions_n1461112307(self):
        "/api/files: COISS versions n1461112307"
        url = '/opus/api/files/co-iss-n1461112307.json'
        self._run_json_equal_file(url, 'api_files_COISS_versions_n1461112307.json')

    def test__api_files_COVIMS_no_versions_v1487539692_ir(self):
        "/api/files: COVIMS no versions v1487539692_ir"
        url = '/opus/api/files/co-vims-v1487539692_ir.json'
        self._run_json_equal_file(url, 'api_files_COVIMS_no_versions_v1487539692_ir.json')

    def test__api_files_COVIMS_no_versions_v1487539692_vis(self):
        "/api/files: COVIMS no versions v1487539692_vis"
        url = '/opus/api/files/co-vims-v1487539692_vis.json'
        self._run_json_equal_file(url, 'api_files_COVIMS_no_versions_v1487539692_vis.json')

    def test__api_files_GOSSI_versions_c0368388622(self):
        "/api/files: GOSSI versions c0368388622"
        url = '/opus/api/files/go-ssi-c0368388622.json'
        self._run_json_equal_file(url, 'api_files_GOSSI_versions_c0368388622.json')

    def test__api_files_VGISS_no_versions_c0948955(self):
        "/api/files: VGISS no versions c0948955"
        url = '/opus/api/files/vg-iss-2-n-c0948955.json'
        self._run_json_equal_file(url, 'api_files_VGISS_no_versions_c0948955.json')

    def test__api_files_HSTWFC3_no_versions_ib4v21gc(self):
        "/api/files: HSTWFC3 no versions ib4v21gc"
        url = '/opus/api/files/hst-11559-wfc3-ib4v21gc.json'
        self._run_json_equal_file(url, 'api_files_HSTWFC3_no_versions_ib4v21gc.json')

    def test__api_files_HSTWFC3_versions_ib4v12n6(self):
        "/api/files: HSTWFC3 versions ib4v12n6"
        url = '/opus/api/files/hst-11559-wfc3-ib4v12n6.json'
        self._run_json_equal_file(url, 'api_files_HSTWFC3_versions_ib4v12n6.json')

    ##################################
    ### General / OBSERVATION TIME ###
    ##################################
