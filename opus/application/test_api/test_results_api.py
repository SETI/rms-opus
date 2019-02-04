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
        settings.CACHE_KEY_PREFIX = 'opustest:' + settings.OPUS_SCHEMA_NAME
        logging.disable(logging.ERROR)
        if settings.TEST_GO_LIVE:
            self.client = requests.Session()
        else:
            self.client = RequestsClient()

    # enable error logging and trace output after test
    def tearDown(self):
        logging.disable(logging.NOTSET)


            #######################################
            ######### /api/data API TESTS #########
            #######################################

    def test__api_data_CASSINIrevno_sort(self):
        "/api/data: CASSINIrevno sort"
        url = '/opus/__api/data.json?instrument=Cassini+ISS,Cassini+VIMS&CASSINIrevno=000,00A,00B,00C,003&CASSINItargetcode=RI+(Rings+-+general)&limit=5000&order=time1&cols=opusid,CASSINIrevno&order=-CASSINIrevnoint1'
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


            #######################################
            ######### /api/data API TESTS #########
            #######################################


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
        url = '/opus/__api/files/co-iss-w1866145657.json'
        expected = {"data": {"co-iss-w1866145657": {"inventory": ["https://pds-rings.seti.org/holdings/metadata/COISS_2xxx/COISS_2111/COISS_2111_inventory.tab", "https://pds-rings.seti.org/holdings/metadata/COISS_2xxx/COISS_2111/COISS_2111_inventory.lbl"], "planet-geometry": ["https://pds-rings.seti.org/holdings/metadata/COISS_2xxx/COISS_2111/COISS_2111_saturn_summary.tab", "https://pds-rings.seti.org/holdings/metadata/COISS_2xxx/COISS_2111/COISS_2111_saturn_summary.lbl"], "moon-geometry": ["https://pds-rings.seti.org/holdings/metadata/COISS_2xxx/COISS_2111/COISS_2111_moon_summary.tab", "https://pds-rings.seti.org/holdings/metadata/COISS_2xxx/COISS_2111/COISS_2111_moon_summary.lbl"], "ring-geometry": ["https://pds-rings.seti.org/holdings/metadata/COISS_2xxx/COISS_2111/COISS_2111_ring_summary.tab", "https://pds-rings.seti.org/holdings/metadata/COISS_2xxx/COISS_2111/COISS_2111_ring_summary.lbl"], "browse-thumb": ["https://pds-rings.seti.org/holdings/previews/COISS_2xxx/COISS_2111/data/1866071296_1866225122/W1866145657_1_thumb.jpg"], "browse-small": ["https://pds-rings.seti.org/holdings/previews/COISS_2xxx/COISS_2111/data/1866071296_1866225122/W1866145657_1_small.jpg"], "browse-medium": ["https://pds-rings.seti.org/holdings/previews/COISS_2xxx/COISS_2111/data/1866071296_1866225122/W1866145657_1_med.jpg"], "browse-full": ["https://pds-rings.seti.org/holdings/previews/COISS_2xxx/COISS_2111/data/1866071296_1866225122/W1866145657_1_full.jpg"], "coiss-raw": ["https://pds-rings.seti.org/holdings/volumes/COISS_2xxx/COISS_2111/data/1866071296_1866225122/W1866145657_1.IMG", "https://pds-rings.seti.org/holdings/volumes/COISS_2xxx/COISS_2111/data/1866071296_1866225122/W1866145657_1.LBL", "https://pds-rings.seti.org/holdings/volumes/COISS_2xxx/COISS_2111/label/prefix3.fmt", "https://pds-rings.seti.org/holdings/volumes/COISS_2xxx/COISS_2111/label/tlmtab.fmt"], "coiss-calib": ["https://pds-rings.seti.org/holdings/calibrated/COISS_2xxx/COISS_2111/data/1866071296_1866225122/W1866145657_1_CALIB.IMG", "https://pds-rings.seti.org/holdings/calibrated/COISS_2xxx/COISS_2111/data/1866071296_1866225122/W1866145657_1_CALIB.LBL"], "coiss-thumb": ["https://pds-rings.seti.org/holdings/volumes/COISS_2xxx/COISS_2111/extras/thumbnail/1866071296_1866225122/W1866145657_1.IMG.jpeg_small"], "coiss-medium": ["https://pds-rings.seti.org/holdings/volumes/COISS_2xxx/COISS_2111/extras/browse/1866071296_1866225122/W1866145657_1.IMG.jpeg"], "coiss-full": ["https://pds-rings.seti.org/holdings/volumes/COISS_2xxx/COISS_2111/extras/tiff/1866071296_1866225122/W1866145657_1.IMG.tiff"]}}, "versions": {"co-iss-w1866145657": {"Current": {"inventory": ["https://pds-rings.seti.org/holdings/metadata/COISS_2xxx/COISS_2111/COISS_2111_inventory.tab", "https://pds-rings.seti.org/holdings/metadata/COISS_2xxx/COISS_2111/COISS_2111_inventory.lbl"], "planet-geometry": ["https://pds-rings.seti.org/holdings/metadata/COISS_2xxx/COISS_2111/COISS_2111_saturn_summary.tab", "https://pds-rings.seti.org/holdings/metadata/COISS_2xxx/COISS_2111/COISS_2111_saturn_summary.lbl"], "moon-geometry": ["https://pds-rings.seti.org/holdings/metadata/COISS_2xxx/COISS_2111/COISS_2111_moon_summary.tab", "https://pds-rings.seti.org/holdings/metadata/COISS_2xxx/COISS_2111/COISS_2111_moon_summary.lbl"], "ring-geometry": ["https://pds-rings.seti.org/holdings/metadata/COISS_2xxx/COISS_2111/COISS_2111_ring_summary.tab", "https://pds-rings.seti.org/holdings/metadata/COISS_2xxx/COISS_2111/COISS_2111_ring_summary.lbl"], "browse-thumb": ["https://pds-rings.seti.org/holdings/previews/COISS_2xxx/COISS_2111/data/1866071296_1866225122/W1866145657_1_thumb.jpg"], "browse-small": ["https://pds-rings.seti.org/holdings/previews/COISS_2xxx/COISS_2111/data/1866071296_1866225122/W1866145657_1_small.jpg"], "browse-medium": ["https://pds-rings.seti.org/holdings/previews/COISS_2xxx/COISS_2111/data/1866071296_1866225122/W1866145657_1_med.jpg"], "browse-full": ["https://pds-rings.seti.org/holdings/previews/COISS_2xxx/COISS_2111/data/1866071296_1866225122/W1866145657_1_full.jpg"], "coiss-raw": ["https://pds-rings.seti.org/holdings/volumes/COISS_2xxx/COISS_2111/data/1866071296_1866225122/W1866145657_1.IMG", "https://pds-rings.seti.org/holdings/volumes/COISS_2xxx/COISS_2111/data/1866071296_1866225122/W1866145657_1.LBL", "https://pds-rings.seti.org/holdings/volumes/COISS_2xxx/COISS_2111/label/prefix3.fmt", "https://pds-rings.seti.org/holdings/volumes/COISS_2xxx/COISS_2111/label/tlmtab.fmt"], "coiss-calib": ["https://pds-rings.seti.org/holdings/calibrated/COISS_2xxx/COISS_2111/data/1866071296_1866225122/W1866145657_1_CALIB.IMG", "https://pds-rings.seti.org/holdings/calibrated/COISS_2xxx/COISS_2111/data/1866071296_1866225122/W1866145657_1_CALIB.LBL"], "coiss-thumb": ["https://pds-rings.seti.org/holdings/volumes/COISS_2xxx/COISS_2111/extras/thumbnail/1866071296_1866225122/W1866145657_1.IMG.jpeg_small"], "coiss-medium": ["https://pds-rings.seti.org/holdings/volumes/COISS_2xxx/COISS_2111/extras/browse/1866071296_1866225122/W1866145657_1.IMG.jpeg"], "coiss-full": ["https://pds-rings.seti.org/holdings/volumes/COISS_2xxx/COISS_2111/extras/tiff/1866071296_1866225122/W1866145657_1.IMG.tiff"]}}}}
        self._run_json_equal(url, expected)

    def test__api_files_COISS_versions_n1461112307(self):
        "/api/files: COISS versions n1461112307"
        url = '/opus/__api/files/co-iss-n1461112307.json'
        expected = {"data": {"co-iss-n1461112307": {"inventory": ["https://pds-rings.seti.org/holdings/metadata/COISS_2xxx/COISS_2002/COISS_2002_inventory.tab", "https://pds-rings.seti.org/holdings/metadata/COISS_2xxx/COISS_2002/COISS_2002_inventory.lbl"], "planet-geometry": ["https://pds-rings.seti.org/holdings/metadata/COISS_2xxx/COISS_2002/COISS_2002_saturn_summary.tab", "https://pds-rings.seti.org/holdings/metadata/COISS_2xxx/COISS_2002/COISS_2002_saturn_summary.lbl"], "moon-geometry": ["https://pds-rings.seti.org/holdings/metadata/COISS_2xxx/COISS_2002/COISS_2002_moon_summary.tab", "https://pds-rings.seti.org/holdings/metadata/COISS_2xxx/COISS_2002/COISS_2002_moon_summary.lbl"], "ring-geometry": ["https://pds-rings.seti.org/holdings/metadata/COISS_2xxx/COISS_2002/COISS_2002_ring_summary.tab", "https://pds-rings.seti.org/holdings/metadata/COISS_2xxx/COISS_2002/COISS_2002_ring_summary.lbl"], "browse-thumb": ["https://pds-rings.seti.org/holdings/previews/COISS_2xxx/COISS_2002/data/1461048995_1461193970/N1461112307_1_thumb.jpg"], "browse-small": ["https://pds-rings.seti.org/holdings/previews/COISS_2xxx/COISS_2002/data/1461048995_1461193970/N1461112307_1_small.jpg"], "browse-medium": ["https://pds-rings.seti.org/holdings/previews/COISS_2xxx/COISS_2002/data/1461048995_1461193970/N1461112307_1_med.jpg"], "browse-full": ["https://pds-rings.seti.org/holdings/previews/COISS_2xxx/COISS_2002/data/1461048995_1461193970/N1461112307_1_full.jpg"], "coiss-raw": ["https://pds-rings.seti.org/holdings/volumes/COISS_2xxx/COISS_2002/data/1461048995_1461193970/N1461112307_1.IMG", "https://pds-rings.seti.org/holdings/volumes/COISS_2xxx/COISS_2002/data/1461048995_1461193970/N1461112307_1.LBL", "https://pds-rings.seti.org/holdings/volumes/COISS_2xxx/COISS_2002/label/prefix2.fmt", "https://pds-rings.seti.org/holdings/volumes/COISS_2xxx/COISS_2002/label/tlmtab.fmt"], "coiss-calib": ["https://pds-rings.seti.org/holdings/calibrated/COISS_2xxx/COISS_2002/data/1461048995_1461193970/N1461112307_1_CALIB.IMG", "https://pds-rings.seti.org/holdings/calibrated/COISS_2xxx/COISS_2002/data/1461048995_1461193970/N1461112307_1_CALIB.LBL"], "coiss-thumb": ["https://pds-rings.seti.org/holdings/volumes/COISS_2xxx/COISS_2002/extras/thumbnail/1461048995_1461193970/N1461112307_1.IMG.jpeg_small"], "coiss-medium": ["https://pds-rings.seti.org/holdings/volumes/COISS_2xxx/COISS_2002/extras/browse/1461048995_1461193970/N1461112307_1.IMG.jpeg"], "coiss-full": ["https://pds-rings.seti.org/holdings/volumes/COISS_2xxx/COISS_2002/extras/full/1461048995_1461193970/N1461112307_1.IMG.png"]}}, "versions": {"co-iss-n1461112307": {"Current": {"inventory": ["https://pds-rings.seti.org/holdings/metadata/COISS_2xxx/COISS_2002/COISS_2002_inventory.tab", "https://pds-rings.seti.org/holdings/metadata/COISS_2xxx/COISS_2002/COISS_2002_inventory.lbl"], "planet-geometry": ["https://pds-rings.seti.org/holdings/metadata/COISS_2xxx/COISS_2002/COISS_2002_saturn_summary.tab", "https://pds-rings.seti.org/holdings/metadata/COISS_2xxx/COISS_2002/COISS_2002_saturn_summary.lbl"], "moon-geometry": ["https://pds-rings.seti.org/holdings/metadata/COISS_2xxx/COISS_2002/COISS_2002_moon_summary.tab", "https://pds-rings.seti.org/holdings/metadata/COISS_2xxx/COISS_2002/COISS_2002_moon_summary.lbl"], "ring-geometry": ["https://pds-rings.seti.org/holdings/metadata/COISS_2xxx/COISS_2002/COISS_2002_ring_summary.tab", "https://pds-rings.seti.org/holdings/metadata/COISS_2xxx/COISS_2002/COISS_2002_ring_summary.lbl"], "browse-thumb": ["https://pds-rings.seti.org/holdings/previews/COISS_2xxx/COISS_2002/data/1461048995_1461193970/N1461112307_1_thumb.jpg"], "browse-small": ["https://pds-rings.seti.org/holdings/previews/COISS_2xxx/COISS_2002/data/1461048995_1461193970/N1461112307_1_small.jpg"], "browse-medium": ["https://pds-rings.seti.org/holdings/previews/COISS_2xxx/COISS_2002/data/1461048995_1461193970/N1461112307_1_med.jpg"], "browse-full": ["https://pds-rings.seti.org/holdings/previews/COISS_2xxx/COISS_2002/data/1461048995_1461193970/N1461112307_1_full.jpg"], "coiss-raw": ["https://pds-rings.seti.org/holdings/volumes/COISS_2xxx/COISS_2002/data/1461048995_1461193970/N1461112307_1.IMG", "https://pds-rings.seti.org/holdings/volumes/COISS_2xxx/COISS_2002/data/1461048995_1461193970/N1461112307_1.LBL", "https://pds-rings.seti.org/holdings/volumes/COISS_2xxx/COISS_2002/label/prefix2.fmt", "https://pds-rings.seti.org/holdings/volumes/COISS_2xxx/COISS_2002/label/tlmtab.fmt"], "coiss-calib": ["https://pds-rings.seti.org/holdings/calibrated/COISS_2xxx/COISS_2002/data/1461048995_1461193970/N1461112307_1_CALIB.IMG", "https://pds-rings.seti.org/holdings/calibrated/COISS_2xxx/COISS_2002/data/1461048995_1461193970/N1461112307_1_CALIB.LBL"], "coiss-thumb": ["https://pds-rings.seti.org/holdings/volumes/COISS_2xxx/COISS_2002/extras/thumbnail/1461048995_1461193970/N1461112307_1.IMG.jpeg_small"], "coiss-medium": ["https://pds-rings.seti.org/holdings/volumes/COISS_2xxx/COISS_2002/extras/browse/1461048995_1461193970/N1461112307_1.IMG.jpeg"], "coiss-full": ["https://pds-rings.seti.org/holdings/volumes/COISS_2xxx/COISS_2002/extras/full/1461048995_1461193970/N1461112307_1.IMG.png"]}, "1.0": {"coiss-calib": ["https://pds-rings.seti.org/holdings/calibrated/COISS_2xxx_v1.0/COISS_2002/data/1461048995_1461193970/N1461112307_1_CALIB.IMG", "https://pds-rings.seti.org/holdings/calibrated/COISS_2xxx_v1.0/COISS_2002/data/1461048995_1461193970/N1461112307_1_CALIB.LBL"]}}}}
        self._run_json_equal(url, expected)

    def test__api_files_COVIMS_no_versions_v1487539692_ir(self):
        "/api/files: COVIMS no versions v1487539692_ir"
        url = '/opus/__api/files/co-vims-v1487539692_ir.json'
        expected = {"data": {"co-vims-v1487539692_ir": {"inventory": ["https://pds-rings.seti.org/holdings/metadata/COVIMS_0xxx/COVIMS_0006/COVIMS_0006_inventory.tab", "https://pds-rings.seti.org/holdings/metadata/COVIMS_0xxx/COVIMS_0006/COVIMS_0006_inventory.lbl"], "planet-geometry": ["https://pds-rings.seti.org/holdings/metadata/COVIMS_0xxx/COVIMS_0006/COVIMS_0006_saturn_summary.tab", "https://pds-rings.seti.org/holdings/metadata/COVIMS_0xxx/COVIMS_0006/COVIMS_0006_saturn_summary.lbl"], "moon-geometry": ["https://pds-rings.seti.org/holdings/metadata/COVIMS_0xxx/COVIMS_0006/COVIMS_0006_moon_summary.tab", "https://pds-rings.seti.org/holdings/metadata/COVIMS_0xxx/COVIMS_0006/COVIMS_0006_moon_summary.lbl"], "ring-geometry": ["https://pds-rings.seti.org/holdings/metadata/COVIMS_0xxx/COVIMS_0006/COVIMS_0006_ring_summary.tab", "https://pds-rings.seti.org/holdings/metadata/COVIMS_0xxx/COVIMS_0006/COVIMS_0006_ring_summary.lbl"], "browse-thumb": ["https://pds-rings.seti.org/holdings/previews/COVIMS_0xxx/COVIMS_0006/data/2005050T195627_2005051T095112/v1487539692_1_thumb.png"], "browse-small": ["https://pds-rings.seti.org/holdings/previews/COVIMS_0xxx/COVIMS_0006/data/2005050T195627_2005051T095112/v1487539692_1_small.png"], "browse-medium": ["https://pds-rings.seti.org/holdings/previews/COVIMS_0xxx/COVIMS_0006/data/2005050T195627_2005051T095112/v1487539692_1_med.png"], "browse-full": ["https://pds-rings.seti.org/holdings/previews/COVIMS_0xxx/COVIMS_0006/data/2005050T195627_2005051T095112/v1487539692_1_full.png"], "covims-raw": ["https://pds-rings.seti.org/holdings/volumes/COVIMS_0xxx/COVIMS_0006/data/2005050T195627_2005051T095112/v1487539692_1.qub", "https://pds-rings.seti.org/holdings/volumes/COVIMS_0xxx/COVIMS_0006/data/2005050T195627_2005051T095112/v1487539692_1.lbl", "https://pds-rings.seti.org/holdings/volumes/COVIMS_0xxx/COVIMS_0006/label/band_bin_center.fmt", "https://pds-rings.seti.org/holdings/volumes/COVIMS_0xxx/COVIMS_0006/label/core_description.fmt", "https://pds-rings.seti.org/holdings/volumes/COVIMS_0xxx/COVIMS_0006/label/suffix_description.fmt"], "covims-thumb": ["https://pds-rings.seti.org/holdings/volumes/COVIMS_0xxx/COVIMS_0006/extras/thumbnail/2005050T195627_2005051T095112/v1487539692_1.qub.jpeg_small"], "covims-medium": ["https://pds-rings.seti.org/holdings/volumes/COVIMS_0xxx/COVIMS_0006/extras/browse/2005050T195627_2005051T095112/v1487539692_1.qub.jpeg"], "covims-full": ["https://pds-rings.seti.org/holdings/volumes/COVIMS_0xxx/COVIMS_0006/extras/tiff/2005050T195627_2005051T095112/v1487539692_1.qub.tiff"]}}, "versions": {"co-vims-v1487539692_ir": {"Current": {"inventory": ["https://pds-rings.seti.org/holdings/metadata/COVIMS_0xxx/COVIMS_0006/COVIMS_0006_inventory.tab", "https://pds-rings.seti.org/holdings/metadata/COVIMS_0xxx/COVIMS_0006/COVIMS_0006_inventory.lbl"], "planet-geometry": ["https://pds-rings.seti.org/holdings/metadata/COVIMS_0xxx/COVIMS_0006/COVIMS_0006_saturn_summary.tab", "https://pds-rings.seti.org/holdings/metadata/COVIMS_0xxx/COVIMS_0006/COVIMS_0006_saturn_summary.lbl"], "moon-geometry": ["https://pds-rings.seti.org/holdings/metadata/COVIMS_0xxx/COVIMS_0006/COVIMS_0006_moon_summary.tab", "https://pds-rings.seti.org/holdings/metadata/COVIMS_0xxx/COVIMS_0006/COVIMS_0006_moon_summary.lbl"], "ring-geometry": ["https://pds-rings.seti.org/holdings/metadata/COVIMS_0xxx/COVIMS_0006/COVIMS_0006_ring_summary.tab", "https://pds-rings.seti.org/holdings/metadata/COVIMS_0xxx/COVIMS_0006/COVIMS_0006_ring_summary.lbl"], "browse-thumb": ["https://pds-rings.seti.org/holdings/previews/COVIMS_0xxx/COVIMS_0006/data/2005050T195627_2005051T095112/v1487539692_1_thumb.png"], "browse-small": ["https://pds-rings.seti.org/holdings/previews/COVIMS_0xxx/COVIMS_0006/data/2005050T195627_2005051T095112/v1487539692_1_small.png"], "browse-medium": ["https://pds-rings.seti.org/holdings/previews/COVIMS_0xxx/COVIMS_0006/data/2005050T195627_2005051T095112/v1487539692_1_med.png"], "browse-full": ["https://pds-rings.seti.org/holdings/previews/COVIMS_0xxx/COVIMS_0006/data/2005050T195627_2005051T095112/v1487539692_1_full.png"], "covims-raw": ["https://pds-rings.seti.org/holdings/volumes/COVIMS_0xxx/COVIMS_0006/data/2005050T195627_2005051T095112/v1487539692_1.qub", "https://pds-rings.seti.org/holdings/volumes/COVIMS_0xxx/COVIMS_0006/data/2005050T195627_2005051T095112/v1487539692_1.lbl", "https://pds-rings.seti.org/holdings/volumes/COVIMS_0xxx/COVIMS_0006/label/band_bin_center.fmt", "https://pds-rings.seti.org/holdings/volumes/COVIMS_0xxx/COVIMS_0006/label/core_description.fmt", "https://pds-rings.seti.org/holdings/volumes/COVIMS_0xxx/COVIMS_0006/label/suffix_description.fmt"], "covims-thumb": ["https://pds-rings.seti.org/holdings/volumes/COVIMS_0xxx/COVIMS_0006/extras/thumbnail/2005050T195627_2005051T095112/v1487539692_1.qub.jpeg_small"], "covims-medium": ["https://pds-rings.seti.org/holdings/volumes/COVIMS_0xxx/COVIMS_0006/extras/browse/2005050T195627_2005051T095112/v1487539692_1.qub.jpeg"], "covims-full": ["https://pds-rings.seti.org/holdings/volumes/COVIMS_0xxx/COVIMS_0006/extras/tiff/2005050T195627_2005051T095112/v1487539692_1.qub.tiff"]}}}}
        self._run_json_equal(url, expected)

    def test__api_files_COVIMS_no_versions_v1487539692_vis(self):
        "/api/files: COVIMS no versions v1487539692_vis"
        url = '/opus/__api/files/co-vims-v1487539692_vis.json'
        expected = {"data": {"co-vims-v1487539692_vis": {"inventory": ["https://pds-rings.seti.org/holdings/metadata/COVIMS_0xxx/COVIMS_0006/COVIMS_0006_inventory.tab", "https://pds-rings.seti.org/holdings/metadata/COVIMS_0xxx/COVIMS_0006/COVIMS_0006_inventory.lbl"], "planet-geometry": ["https://pds-rings.seti.org/holdings/metadata/COVIMS_0xxx/COVIMS_0006/COVIMS_0006_saturn_summary.tab", "https://pds-rings.seti.org/holdings/metadata/COVIMS_0xxx/COVIMS_0006/COVIMS_0006_saturn_summary.lbl"], "moon-geometry": ["https://pds-rings.seti.org/holdings/metadata/COVIMS_0xxx/COVIMS_0006/COVIMS_0006_moon_summary.tab", "https://pds-rings.seti.org/holdings/metadata/COVIMS_0xxx/COVIMS_0006/COVIMS_0006_moon_summary.lbl"], "ring-geometry": ["https://pds-rings.seti.org/holdings/metadata/COVIMS_0xxx/COVIMS_0006/COVIMS_0006_ring_summary.tab", "https://pds-rings.seti.org/holdings/metadata/COVIMS_0xxx/COVIMS_0006/COVIMS_0006_ring_summary.lbl"], "browse-thumb": ["https://pds-rings.seti.org/holdings/previews/COVIMS_0xxx/COVIMS_0006/data/2005050T195627_2005051T095112/v1487539692_1_thumb.png"], "browse-small": ["https://pds-rings.seti.org/holdings/previews/COVIMS_0xxx/COVIMS_0006/data/2005050T195627_2005051T095112/v1487539692_1_small.png"], "browse-medium": ["https://pds-rings.seti.org/holdings/previews/COVIMS_0xxx/COVIMS_0006/data/2005050T195627_2005051T095112/v1487539692_1_med.png"], "browse-full": ["https://pds-rings.seti.org/holdings/previews/COVIMS_0xxx/COVIMS_0006/data/2005050T195627_2005051T095112/v1487539692_1_full.png"], "covims-raw": ["https://pds-rings.seti.org/holdings/volumes/COVIMS_0xxx/COVIMS_0006/data/2005050T195627_2005051T095112/v1487539692_1.qub", "https://pds-rings.seti.org/holdings/volumes/COVIMS_0xxx/COVIMS_0006/data/2005050T195627_2005051T095112/v1487539692_1.lbl", "https://pds-rings.seti.org/holdings/volumes/COVIMS_0xxx/COVIMS_0006/label/band_bin_center.fmt", "https://pds-rings.seti.org/holdings/volumes/COVIMS_0xxx/COVIMS_0006/label/core_description.fmt", "https://pds-rings.seti.org/holdings/volumes/COVIMS_0xxx/COVIMS_0006/label/suffix_description.fmt"], "covims-thumb": ["https://pds-rings.seti.org/holdings/volumes/COVIMS_0xxx/COVIMS_0006/extras/thumbnail/2005050T195627_2005051T095112/v1487539692_1.qub.jpeg_small"], "covims-medium": ["https://pds-rings.seti.org/holdings/volumes/COVIMS_0xxx/COVIMS_0006/extras/browse/2005050T195627_2005051T095112/v1487539692_1.qub.jpeg"], "covims-full": ["https://pds-rings.seti.org/holdings/volumes/COVIMS_0xxx/COVIMS_0006/extras/tiff/2005050T195627_2005051T095112/v1487539692_1.qub.tiff"]}}, "versions": {"co-vims-v1487539692_vis": {"Current": {"inventory": ["https://pds-rings.seti.org/holdings/metadata/COVIMS_0xxx/COVIMS_0006/COVIMS_0006_inventory.tab", "https://pds-rings.seti.org/holdings/metadata/COVIMS_0xxx/COVIMS_0006/COVIMS_0006_inventory.lbl"], "planet-geometry": ["https://pds-rings.seti.org/holdings/metadata/COVIMS_0xxx/COVIMS_0006/COVIMS_0006_saturn_summary.tab", "https://pds-rings.seti.org/holdings/metadata/COVIMS_0xxx/COVIMS_0006/COVIMS_0006_saturn_summary.lbl"], "moon-geometry": ["https://pds-rings.seti.org/holdings/metadata/COVIMS_0xxx/COVIMS_0006/COVIMS_0006_moon_summary.tab", "https://pds-rings.seti.org/holdings/metadata/COVIMS_0xxx/COVIMS_0006/COVIMS_0006_moon_summary.lbl"], "ring-geometry": ["https://pds-rings.seti.org/holdings/metadata/COVIMS_0xxx/COVIMS_0006/COVIMS_0006_ring_summary.tab", "https://pds-rings.seti.org/holdings/metadata/COVIMS_0xxx/COVIMS_0006/COVIMS_0006_ring_summary.lbl"], "browse-thumb": ["https://pds-rings.seti.org/holdings/previews/COVIMS_0xxx/COVIMS_0006/data/2005050T195627_2005051T095112/v1487539692_1_thumb.png"], "browse-small": ["https://pds-rings.seti.org/holdings/previews/COVIMS_0xxx/COVIMS_0006/data/2005050T195627_2005051T095112/v1487539692_1_small.png"], "browse-medium": ["https://pds-rings.seti.org/holdings/previews/COVIMS_0xxx/COVIMS_0006/data/2005050T195627_2005051T095112/v1487539692_1_med.png"], "browse-full": ["https://pds-rings.seti.org/holdings/previews/COVIMS_0xxx/COVIMS_0006/data/2005050T195627_2005051T095112/v1487539692_1_full.png"], "covims-raw": ["https://pds-rings.seti.org/holdings/volumes/COVIMS_0xxx/COVIMS_0006/data/2005050T195627_2005051T095112/v1487539692_1.qub", "https://pds-rings.seti.org/holdings/volumes/COVIMS_0xxx/COVIMS_0006/data/2005050T195627_2005051T095112/v1487539692_1.lbl", "https://pds-rings.seti.org/holdings/volumes/COVIMS_0xxx/COVIMS_0006/label/band_bin_center.fmt", "https://pds-rings.seti.org/holdings/volumes/COVIMS_0xxx/COVIMS_0006/label/core_description.fmt", "https://pds-rings.seti.org/holdings/volumes/COVIMS_0xxx/COVIMS_0006/label/suffix_description.fmt"], "covims-thumb": ["https://pds-rings.seti.org/holdings/volumes/COVIMS_0xxx/COVIMS_0006/extras/thumbnail/2005050T195627_2005051T095112/v1487539692_1.qub.jpeg_small"], "covims-medium": ["https://pds-rings.seti.org/holdings/volumes/COVIMS_0xxx/COVIMS_0006/extras/browse/2005050T195627_2005051T095112/v1487539692_1.qub.jpeg"], "covims-full": ["https://pds-rings.seti.org/holdings/volumes/COVIMS_0xxx/COVIMS_0006/extras/tiff/2005050T195627_2005051T095112/v1487539692_1.qub.tiff"]}}}}
        self._run_json_equal(url, expected)

    def test__api_files_GOSSI_versions_c0368388622(self):
        "/api/files: GOSSI versions c0368388622"
        url = '/opus/__api/files/go-ssi-c0368388622.json'
        expected = {"data": {"go-ssi-c0368388622": {"browse-thumb": ["https://pds-rings.seti.org/holdings/previews/GO_0xxx/GO_0017/C3/JUPITER/C0368388622R_thumb.jpg"], "browse-small": ["https://pds-rings.seti.org/holdings/previews/GO_0xxx/GO_0017/C3/JUPITER/C0368388622R_small.jpg"], "browse-medium": ["https://pds-rings.seti.org/holdings/previews/GO_0xxx/GO_0017/C3/JUPITER/C0368388622R_med.jpg"], "browse-full": ["https://pds-rings.seti.org/holdings/previews/GO_0xxx/GO_0017/C3/JUPITER/C0368388622R_full.jpg"], "gossi-raw": ["https://pds-rings.seti.org/holdings/volumes/GO_0xxx/GO_0017/C3/JUPITER/C0368388622R.IMG", "https://pds-rings.seti.org/holdings/volumes/GO_0xxx/GO_0017/C3/JUPITER/C0368388622R.LBL", "https://pds-rings.seti.org/holdings/volumes/GO_0xxx/GO_0017/LABEL/RLINEPRX.FMT", "https://pds-rings.seti.org/holdings/volumes/GO_0xxx/GO_0017/LABEL/RTLMTAB.FMT"]}}, "versions": {"go-ssi-c0368388622": {"Current": {"browse-thumb": ["https://pds-rings.seti.org/holdings/previews/GO_0xxx/GO_0017/C3/JUPITER/C0368388622R_thumb.jpg"], "browse-small": ["https://pds-rings.seti.org/holdings/previews/GO_0xxx/GO_0017/C3/JUPITER/C0368388622R_small.jpg"], "browse-medium": ["https://pds-rings.seti.org/holdings/previews/GO_0xxx/GO_0017/C3/JUPITER/C0368388622R_med.jpg"], "browse-full": ["https://pds-rings.seti.org/holdings/previews/GO_0xxx/GO_0017/C3/JUPITER/C0368388622R_full.jpg"], "gossi-raw": ["https://pds-rings.seti.org/holdings/volumes/GO_0xxx/GO_0017/C3/JUPITER/C0368388622R.IMG", "https://pds-rings.seti.org/holdings/volumes/GO_0xxx/GO_0017/C3/JUPITER/C0368388622R.LBL", "https://pds-rings.seti.org/holdings/volumes/GO_0xxx/GO_0017/LABEL/RLINEPRX.FMT", "https://pds-rings.seti.org/holdings/volumes/GO_0xxx/GO_0017/LABEL/RTLMTAB.FMT"]}, "1": {"browse-thumb": ["https://pds-rings.seti.org/holdings/previews/GO_0xxx_v1/GO_0017/C3/JUPITER/C036838/8622R_thumb.jpg"], "browse-small": ["https://pds-rings.seti.org/holdings/previews/GO_0xxx_v1/GO_0017/C3/JUPITER/C036838/8622R_small.jpg"], "browse-medium": ["https://pds-rings.seti.org/holdings/previews/GO_0xxx_v1/GO_0017/C3/JUPITER/C036838/8622R_med.jpg"], "browse-full": ["https://pds-rings.seti.org/holdings/previews/GO_0xxx_v1/GO_0017/C3/JUPITER/C036838/8622R_full.jpg"], "gossi-raw": ["https://pds-rings.seti.org/holdings/volumes/GO_0xxx_v1/GO_0017/C3/JUPITER/C036838/8622R.IMG", "https://pds-rings.seti.org/holdings/volumes/GO_0xxx_v1/GO_0017/C3/JUPITER/C036838/8622R.LBL", "https://pds-rings.seti.org/holdings/volumes/GO_0xxx_v1/GO_0017/LABEL/RLINEPRX.FMT", "https://pds-rings.seti.org/holdings/volumes/GO_0xxx_v1/GO_0017/LABEL/RTLMTAB.FMT"]}}}}
        self._run_json_equal(url, expected)

    def test__api_files_VGISS_no_versions_c0948955(self):
        "/api/files: VGISS no versions c0948955"
        url = '/opus/__api/files/vg-iss-2-n-c0948955.json'
        expected = {"data": {"vg-iss-2-n-c0948955": {"inventory": ["https://pds-rings.seti.org/holdings/metadata/VGISS_8xxx/VGISS_8201/VGISS_8201_inventory.tab", "https://pds-rings.seti.org/holdings/metadata/VGISS_8xxx/VGISS_8201/VGISS_8201_inventory.lbl"], "planet-geometry": ["https://pds-rings.seti.org/holdings/metadata/VGISS_8xxx/VGISS_8201/VGISS_8201_neptune_summary.tab", "https://pds-rings.seti.org/holdings/metadata/VGISS_8xxx/VGISS_8201/VGISS_8201_neptune_summary.lbl"], "moon-geometry": ["https://pds-rings.seti.org/holdings/metadata/VGISS_8xxx/VGISS_8201/VGISS_8201_moon_summary.tab", "https://pds-rings.seti.org/holdings/metadata/VGISS_8xxx/VGISS_8201/VGISS_8201_moon_summary.lbl"], "ring-geometry": ["https://pds-rings.seti.org/holdings/metadata/VGISS_8xxx/VGISS_8201/VGISS_8201_ring_summary.tab", "https://pds-rings.seti.org/holdings/metadata/VGISS_8xxx/VGISS_8201/VGISS_8201_ring_summary.lbl"], "browse-thumb": ["https://pds-rings.seti.org/holdings/previews/VGISS_8xxx/VGISS_8201/DATA/C09489XX/C0948955_thumb.jpg"], "browse-small": ["https://pds-rings.seti.org/holdings/previews/VGISS_8xxx/VGISS_8201/DATA/C09489XX/C0948955_small.jpg"], "browse-medium": ["https://pds-rings.seti.org/holdings/previews/VGISS_8xxx/VGISS_8201/DATA/C09489XX/C0948955_med.jpg"], "browse-full": ["https://pds-rings.seti.org/holdings/previews/VGISS_8xxx/VGISS_8201/DATA/C09489XX/C0948955_full.jpg"], "vgiss-raw": ["https://pds-rings.seti.org/holdings/volumes/VGISS_8xxx/VGISS_8201/DATA/C09489XX/C0948955_RAW.IMG", "https://pds-rings.seti.org/holdings/volumes/VGISS_8xxx/VGISS_8201/DATA/C09489XX/C0948955_RAW.LBL"], "vgiss-cleaned": ["https://pds-rings.seti.org/holdings/volumes/VGISS_8xxx/VGISS_8201/DATA/C09489XX/C0948955_CLEANED.IMG", "https://pds-rings.seti.org/holdings/volumes/VGISS_8xxx/VGISS_8201/DATA/C09489XX/C0948955_CLEANED.LBL"], "vgiss-calib": ["https://pds-rings.seti.org/holdings/volumes/VGISS_8xxx/VGISS_8201/DATA/C09489XX/C0948955_CALIB.IMG", "https://pds-rings.seti.org/holdings/volumes/VGISS_8xxx/VGISS_8201/DATA/C09489XX/C0948955_CALIB.LBL"], "vgiss-geomed": ["https://pds-rings.seti.org/holdings/volumes/VGISS_8xxx/VGISS_8201/DATA/C09489XX/C0948955_GEOMED.IMG", "https://pds-rings.seti.org/holdings/volumes/VGISS_8xxx/VGISS_8201/DATA/C09489XX/C0948955_GEOMED.LBL"], "vgiss-resloc": ["https://pds-rings.seti.org/holdings/volumes/VGISS_8xxx/VGISS_8201/DATA/C09489XX/C0948955_RESLOC.TAB", "https://pds-rings.seti.org/holdings/volumes/VGISS_8xxx/VGISS_8201/DATA/C09489XX/C0948955_RESLOC.LBL", "https://pds-rings.seti.org/holdings/volumes/VGISS_8xxx/VGISS_8201/DATA/C09489XX/C0948955_RESLOC.DAT"], "vgiss-geoma": ["https://pds-rings.seti.org/holdings/volumes/VGISS_8xxx/VGISS_8201/DATA/C09489XX/C0948955_GEOMA.TAB", "https://pds-rings.seti.org/holdings/volumes/VGISS_8xxx/VGISS_8201/DATA/C09489XX/C0948955_GEOMA.LBL", "https://pds-rings.seti.org/holdings/volumes/VGISS_8xxx/VGISS_8201/DATA/C09489XX/C0948955_GEOMA.DAT"]}}, "versions": {"vg-iss-2-n-c0948955": {"Current": {"inventory": ["https://pds-rings.seti.org/holdings/metadata/VGISS_8xxx/VGISS_8201/VGISS_8201_inventory.tab", "https://pds-rings.seti.org/holdings/metadata/VGISS_8xxx/VGISS_8201/VGISS_8201_inventory.lbl"], "planet-geometry": ["https://pds-rings.seti.org/holdings/metadata/VGISS_8xxx/VGISS_8201/VGISS_8201_neptune_summary.tab", "https://pds-rings.seti.org/holdings/metadata/VGISS_8xxx/VGISS_8201/VGISS_8201_neptune_summary.lbl"], "moon-geometry": ["https://pds-rings.seti.org/holdings/metadata/VGISS_8xxx/VGISS_8201/VGISS_8201_moon_summary.tab", "https://pds-rings.seti.org/holdings/metadata/VGISS_8xxx/VGISS_8201/VGISS_8201_moon_summary.lbl"], "ring-geometry": ["https://pds-rings.seti.org/holdings/metadata/VGISS_8xxx/VGISS_8201/VGISS_8201_ring_summary.tab", "https://pds-rings.seti.org/holdings/metadata/VGISS_8xxx/VGISS_8201/VGISS_8201_ring_summary.lbl"], "browse-thumb": ["https://pds-rings.seti.org/holdings/previews/VGISS_8xxx/VGISS_8201/DATA/C09489XX/C0948955_thumb.jpg"], "browse-small": ["https://pds-rings.seti.org/holdings/previews/VGISS_8xxx/VGISS_8201/DATA/C09489XX/C0948955_small.jpg"], "browse-medium": ["https://pds-rings.seti.org/holdings/previews/VGISS_8xxx/VGISS_8201/DATA/C09489XX/C0948955_med.jpg"], "browse-full": ["https://pds-rings.seti.org/holdings/previews/VGISS_8xxx/VGISS_8201/DATA/C09489XX/C0948955_full.jpg"], "vgiss-raw": ["https://pds-rings.seti.org/holdings/volumes/VGISS_8xxx/VGISS_8201/DATA/C09489XX/C0948955_RAW.IMG", "https://pds-rings.seti.org/holdings/volumes/VGISS_8xxx/VGISS_8201/DATA/C09489XX/C0948955_RAW.LBL"], "vgiss-cleaned": ["https://pds-rings.seti.org/holdings/volumes/VGISS_8xxx/VGISS_8201/DATA/C09489XX/C0948955_CLEANED.IMG", "https://pds-rings.seti.org/holdings/volumes/VGISS_8xxx/VGISS_8201/DATA/C09489XX/C0948955_CLEANED.LBL"], "vgiss-calib": ["https://pds-rings.seti.org/holdings/volumes/VGISS_8xxx/VGISS_8201/DATA/C09489XX/C0948955_CALIB.IMG", "https://pds-rings.seti.org/holdings/volumes/VGISS_8xxx/VGISS_8201/DATA/C09489XX/C0948955_CALIB.LBL"], "vgiss-geomed": ["https://pds-rings.seti.org/holdings/volumes/VGISS_8xxx/VGISS_8201/DATA/C09489XX/C0948955_GEOMED.IMG", "https://pds-rings.seti.org/holdings/volumes/VGISS_8xxx/VGISS_8201/DATA/C09489XX/C0948955_GEOMED.LBL"], "vgiss-resloc": ["https://pds-rings.seti.org/holdings/volumes/VGISS_8xxx/VGISS_8201/DATA/C09489XX/C0948955_RESLOC.TAB", "https://pds-rings.seti.org/holdings/volumes/VGISS_8xxx/VGISS_8201/DATA/C09489XX/C0948955_RESLOC.LBL", "https://pds-rings.seti.org/holdings/volumes/VGISS_8xxx/VGISS_8201/DATA/C09489XX/C0948955_RESLOC.DAT"], "vgiss-geoma": ["https://pds-rings.seti.org/holdings/volumes/VGISS_8xxx/VGISS_8201/DATA/C09489XX/C0948955_GEOMA.TAB", "https://pds-rings.seti.org/holdings/volumes/VGISS_8xxx/VGISS_8201/DATA/C09489XX/C0948955_GEOMA.LBL", "https://pds-rings.seti.org/holdings/volumes/VGISS_8xxx/VGISS_8201/DATA/C09489XX/C0948955_GEOMA.DAT"]}}}}
        self._run_json_equal(url, expected)

    def test__api_files_HSTWFC3_no_versions_ibcz21fl(self):
        "/api/files: HSTWFC3 no versions ibcz21fl"
        url = '/opus/__api/files/hst-12003-wfc3-ibcz21fl.json'
        expected = {"data": {"hst-12003-wfc3-ibcz21fl": {"browse-thumb": ["https://pds-rings.seti.org/holdings/previews/HSTIx_xxxx/HSTI1_2003/DATA/VISIT_21/IBCZ21FLQ_thumb.jpg"], "browse-small": ["https://pds-rings.seti.org/holdings/previews/HSTIx_xxxx/HSTI1_2003/DATA/VISIT_21/IBCZ21FLQ_small.jpg"], "browse-medium": ["https://pds-rings.seti.org/holdings/previews/HSTIx_xxxx/HSTI1_2003/DATA/VISIT_21/IBCZ21FLQ_med.jpg"], "browse-full": ["https://pds-rings.seti.org/holdings/previews/HSTIx_xxxx/HSTI1_2003/DATA/VISIT_21/IBCZ21FLQ_full.jpg"], "hst-text": ["https://pds-rings.seti.org/holdings/volumes/HSTIx_xxxx/HSTI1_2003/DATA/VISIT_21/IBCZ21FLQ.ASC", "https://pds-rings.seti.org/holdings/volumes/HSTIx_xxxx/HSTI1_2003/DATA/VISIT_21/IBCZ21FLQ.LBL"], "hst-tiff": ["https://pds-rings.seti.org/holdings/volumes/HSTIx_xxxx/HSTI1_2003/DATA/VISIT_21/IBCZ21FLQ_RAW.TIF", "https://pds-rings.seti.org/holdings/volumes/HSTIx_xxxx/HSTI1_2003/DATA/VISIT_21/IBCZ21FLQ.LBL"], "hst-raw": ["https://pds-rings.seti.org/holdings/volumes/HSTIx_xxxx/HSTI1_2003/DATA/VISIT_21/IBCZ21FLQ_RAW.JPG", "https://pds-rings.seti.org/holdings/volumes/HSTIx_xxxx/HSTI1_2003/DATA/VISIT_21/IBCZ21FLQ.LBL"], "hst-calib": ["https://pds-rings.seti.org/holdings/volumes/HSTIx_xxxx/HSTI1_2003/DATA/VISIT_21/IBCZ21FLQ_FLT.JPG", "https://pds-rings.seti.org/holdings/volumes/HSTIx_xxxx/HSTI1_2003/DATA/VISIT_21/IBCZ21FLQ.LBL"], "hst-1d-spectrum": ["https://pds-rings.seti.org/holdings/volumes/HSTIx_xxxx/HSTI1_2003/DATA/VISIT_21/IBCZ21FLQ_DRZ.JPG", "https://pds-rings.seti.org/holdings/volumes/HSTIx_xxxx/HSTI1_2003/DATA/VISIT_21/IBCZ21FLQ.LBL"]}}, "versions": {"hst-12003-wfc3-ibcz21fl": {"Current": {"browse-thumb": ["https://pds-rings.seti.org/holdings/previews/HSTIx_xxxx/HSTI1_2003/DATA/VISIT_21/IBCZ21FLQ_thumb.jpg"], "browse-small": ["https://pds-rings.seti.org/holdings/previews/HSTIx_xxxx/HSTI1_2003/DATA/VISIT_21/IBCZ21FLQ_small.jpg"], "browse-medium": ["https://pds-rings.seti.org/holdings/previews/HSTIx_xxxx/HSTI1_2003/DATA/VISIT_21/IBCZ21FLQ_med.jpg"], "browse-full": ["https://pds-rings.seti.org/holdings/previews/HSTIx_xxxx/HSTI1_2003/DATA/VISIT_21/IBCZ21FLQ_full.jpg"], "hst-text": ["https://pds-rings.seti.org/holdings/volumes/HSTIx_xxxx/HSTI1_2003/DATA/VISIT_21/IBCZ21FLQ.ASC", "https://pds-rings.seti.org/holdings/volumes/HSTIx_xxxx/HSTI1_2003/DATA/VISIT_21/IBCZ21FLQ.LBL"], "hst-tiff": ["https://pds-rings.seti.org/holdings/volumes/HSTIx_xxxx/HSTI1_2003/DATA/VISIT_21/IBCZ21FLQ_RAW.TIF", "https://pds-rings.seti.org/holdings/volumes/HSTIx_xxxx/HSTI1_2003/DATA/VISIT_21/IBCZ21FLQ.LBL"], "hst-raw": ["https://pds-rings.seti.org/holdings/volumes/HSTIx_xxxx/HSTI1_2003/DATA/VISIT_21/IBCZ21FLQ_RAW.JPG", "https://pds-rings.seti.org/holdings/volumes/HSTIx_xxxx/HSTI1_2003/DATA/VISIT_21/IBCZ21FLQ.LBL"], "hst-calib": ["https://pds-rings.seti.org/holdings/volumes/HSTIx_xxxx/HSTI1_2003/DATA/VISIT_21/IBCZ21FLQ_FLT.JPG", "https://pds-rings.seti.org/holdings/volumes/HSTIx_xxxx/HSTI1_2003/DATA/VISIT_21/IBCZ21FLQ.LBL"], "hst-1d-spectrum": ["https://pds-rings.seti.org/holdings/volumes/HSTIx_xxxx/HSTI1_2003/DATA/VISIT_21/IBCZ21FLQ_DRZ.JPG", "https://pds-rings.seti.org/holdings/volumes/HSTIx_xxxx/HSTI1_2003/DATA/VISIT_21/IBCZ21FLQ.LBL"]}}}}
        self._run_json_equal(url, expected)

    def test__api_files_HSTWFC3_versions_ib4v12n6(self):
        "/api/files: HSTWFC3 versions ib4v12n6"
        url = '/opus/__api/files/hst-11559-wfc3-ib4v12n6.json'
        expected = {"data": {"hst-11559-wfc3-ib4v12n6": {"browse-thumb": ["https://pds-rings.seti.org/holdings/previews/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_12/IB4V12N6Q_thumb.jpg"], "browse-small": ["https://pds-rings.seti.org/holdings/previews/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_12/IB4V12N6Q_small.jpg"], "browse-medium": ["https://pds-rings.seti.org/holdings/previews/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_12/IB4V12N6Q_med.jpg"], "browse-full": ["https://pds-rings.seti.org/holdings/previews/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_12/IB4V12N6Q_full.jpg"], "hst-text": ["https://pds-rings.seti.org/holdings/volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_12/IB4V12N6Q.ASC", "https://pds-rings.seti.org/holdings/volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_12/IB4V12N6Q.LBL"], "hst-tiff": ["https://pds-rings.seti.org/holdings/volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_12/IB4V12N6Q_RAW.TIF", "https://pds-rings.seti.org/holdings/volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_12/IB4V12N6Q.LBL"], "hst-raw": ["https://pds-rings.seti.org/holdings/volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_12/IB4V12N6Q_RAW.JPG", "https://pds-rings.seti.org/holdings/volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_12/IB4V12N6Q.LBL"], "hst-calib": ["https://pds-rings.seti.org/holdings/volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_12/IB4V12N6Q_FLT.JPG", "https://pds-rings.seti.org/holdings/volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_12/IB4V12N6Q.LBL"], "hst-1d-spectrum": ["https://pds-rings.seti.org/holdings/volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_12/IB4V12N6Q_DRZ.JPG", "https://pds-rings.seti.org/holdings/volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_12/IB4V12N6Q.LBL"]}}, "versions": {"hst-11559-wfc3-ib4v12n6": {"Current": {"browse-thumb": ["https://pds-rings.seti.org/holdings/previews/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_12/IB4V12N6Q_thumb.jpg"], "browse-small": ["https://pds-rings.seti.org/holdings/previews/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_12/IB4V12N6Q_small.jpg"], "browse-medium": ["https://pds-rings.seti.org/holdings/previews/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_12/IB4V12N6Q_med.jpg"], "browse-full": ["https://pds-rings.seti.org/holdings/previews/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_12/IB4V12N6Q_full.jpg"], "hst-text": ["https://pds-rings.seti.org/holdings/volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_12/IB4V12N6Q.ASC", "https://pds-rings.seti.org/holdings/volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_12/IB4V12N6Q.LBL"], "hst-tiff": ["https://pds-rings.seti.org/holdings/volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_12/IB4V12N6Q_RAW.TIF", "https://pds-rings.seti.org/holdings/volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_12/IB4V12N6Q.LBL"], "hst-raw": ["https://pds-rings.seti.org/holdings/volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_12/IB4V12N6Q_RAW.JPG", "https://pds-rings.seti.org/holdings/volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_12/IB4V12N6Q.LBL"], "hst-calib": ["https://pds-rings.seti.org/holdings/volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_12/IB4V12N6Q_FLT.JPG", "https://pds-rings.seti.org/holdings/volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_12/IB4V12N6Q.LBL"], "hst-1d-spectrum": ["https://pds-rings.seti.org/holdings/volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_12/IB4V12N6Q_DRZ.JPG", "https://pds-rings.seti.org/holdings/volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_12/IB4V12N6Q.LBL"]}, "1.1": {"hst-text": ["https://pds-rings.seti.org/holdings/volumes/HSTIx_xxxx_v1.1/HSTI1_1559/DATA/VISIT_12/IB4V12N6Q.ASC", "https://pds-rings.seti.org/holdings/volumes/HSTIx_xxxx_v1.1/HSTI1_1559/DATA/VISIT_12/IB4V12N6Q.LBL"], "hst-tiff": ["https://pds-rings.seti.org/holdings/volumes/HSTIx_xxxx_v1.1/HSTI1_1559/DATA/VISIT_12/IB4V12N6Q_RAW.TIF", "https://pds-rings.seti.org/holdings/volumes/HSTIx_xxxx_v1.1/HSTI1_1559/DATA/VISIT_12/IB4V12N6Q.LBL"], "hst-raw": ["https://pds-rings.seti.org/holdings/volumes/HSTIx_xxxx_v1.1/HSTI1_1559/DATA/VISIT_12/IB4V12N6Q_RAW.JPG", "https://pds-rings.seti.org/holdings/volumes/HSTIx_xxxx_v1.1/HSTI1_1559/DATA/VISIT_12/IB4V12N6Q.LBL"], "hst-calib": ["https://pds-rings.seti.org/holdings/volumes/HSTIx_xxxx_v1.1/HSTI1_1559/DATA/VISIT_12/IB4V12N6Q_FLT.JPG", "https://pds-rings.seti.org/holdings/volumes/HSTIx_xxxx_v1.1/HSTI1_1559/DATA/VISIT_12/IB4V12N6Q.LBL"], "hst-1d-spectrum": ["https://pds-rings.seti.org/holdings/volumes/HSTIx_xxxx_v1.1/HSTI1_1559/DATA/VISIT_12/IB4V12N6Q_DRZ.JPG", "https://pds-rings.seti.org/holdings/volumes/HSTIx_xxxx_v1.1/HSTI1_1559/DATA/VISIT_12/IB4V12N6Q.LBL"]}, "1.0": {"hst-text": ["https://pds-rings.seti.org/holdings/volumes/HSTIx_xxxx_v1.0/HSTI1_1559/DATA/VISIT_12/IB4V12N6Q.ASC", "https://pds-rings.seti.org/holdings/volumes/HSTIx_xxxx_v1.0/HSTI1_1559/DATA/VISIT_12/IB4V12N6Q.LBL"], "hst-tiff": ["https://pds-rings.seti.org/holdings/volumes/HSTIx_xxxx_v1.0/HSTI1_1559/DATA/VISIT_12/IB4V12N6Q_RAW.TIF", "https://pds-rings.seti.org/holdings/volumes/HSTIx_xxxx_v1.0/HSTI1_1559/DATA/VISIT_12/IB4V12N6Q.LBL"], "hst-raw": ["https://pds-rings.seti.org/holdings/volumes/HSTIx_xxxx_v1.0/HSTI1_1559/DATA/VISIT_12/IB4V12N6Q_RAW.JPG", "https://pds-rings.seti.org/holdings/volumes/HSTIx_xxxx_v1.0/HSTI1_1559/DATA/VISIT_12/IB4V12N6Q.LBL"], "hst-calib": ["https://pds-rings.seti.org/holdings/volumes/HSTIx_xxxx_v1.0/HSTI1_1559/DATA/VISIT_12/IB4V12N6Q_FLT.JPG", "https://pds-rings.seti.org/holdings/volumes/HSTIx_xxxx_v1.0/HSTI1_1559/DATA/VISIT_12/IB4V12N6Q.LBL"], "hst-1d-spectrum": ["https://pds-rings.seti.org/holdings/volumes/HSTIx_xxxx_v1.0/HSTI1_1559/DATA/VISIT_12/IB4V12N6Q_DRZ.JPG", "https://pds-rings.seti.org/holdings/volumes/HSTIx_xxxx_v1.0/HSTI1_1559/DATA/VISIT_12/IB4V12N6Q.LBL"]}}}}
        self._run_json_equal(url, expected)

    ##################################
    ### General / OBSERVATION TIME ###
    ##################################
