# opus/application/test_api/test_results_contents.py

import json
import logging
import requests
from unittest import TestCase

from django.core.cache import cache
from rest_framework.test import RequestsClient

from api_test_helper import ApiTestHelper

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


            #################################
            ######### RESULTS TESTS #########
            #################################

    def test__results_contents_co_cirs_0408010657_fp3(self):
        "[test_results_contents.py] co-cirs-0408010657-fp3"
        url = "/api/metadata_v2/co-cirs-0408010657-fp3.json"
        self._run_json_equal_file(url, "results_co_cirs_0408010657_fp3.json")

    def test__results_contents_co_cirs_0408031652_fp1(self):
        "[test_results_contents.py] co-cirs-0408031652-fp1"
        url = "/api/metadata_v2/co-cirs-0408031652-fp1.json"
        self._run_json_equal_file(url, "results_co_cirs_0408031652_fp1.json")

    def test__results_contents_co_cirs_0408041543_fp3(self):
        "[test_results_contents.py] co-cirs-0408041543-fp3"
        url = "/api/metadata_v2/co-cirs-0408041543-fp3.json"
        self._run_json_equal_file(url, "results_co_cirs_0408041543_fp3.json")

    def test__results_contents_co_cirs_0408152208_fp3(self):
        "[test_results_contents.py] co-cirs-0408152208-fp3"
        url = "/api/metadata_v2/co-cirs-0408152208-fp3.json"
        self._run_json_equal_file(url, "results_co_cirs_0408152208_fp3.json")

    def test__results_contents_co_cirs_0408161433_fp4(self):
        "[test_results_contents.py] co-cirs-0408161433-fp4"
        url = "/api/metadata_v2/co-cirs-0408161433-fp4.json"
        self._run_json_equal_file(url, "results_co_cirs_0408161433_fp4.json")

    def test__results_contents_co_cirs_0408220524_fp4(self):
        "[test_results_contents.py] co-cirs-0408220524-fp4"
        url = "/api/metadata_v2/co-cirs-0408220524-fp4.json"
        self._run_json_equal_file(url, "results_co_cirs_0408220524_fp4.json")

    def test__results_contents_co_iss_n1460961193(self):
        "[test_results_contents.py] co-iss-n1460961193"
        url = "/api/metadata_v2/co-iss-n1460961193.json"
        self._run_json_equal_file(url, "results_co_iss_n1460961193.json")

    def test__results_contents_co_iss_n1461527506(self):
        "[test_results_contents.py] co-iss-n1461527506"
        url = "/api/metadata_v2/co-iss-n1461527506.json"
        self._run_json_equal_file(url, "results_co_iss_n1461527506.json")

    def test__results_contents_co_iss_n1461810160(self):
        "[test_results_contents.py] co-iss-n1461810160"
        url = "/api/metadata_v2/co-iss-n1461810160.json"
        self._run_json_equal_file(url, "results_co_iss_n1461810160.json")

    def test__results_contents_co_iss_n1462660850(self):
        "[test_results_contents.py] co-iss-n1462660850"
        url = "/api/metadata_v2/co-iss-n1462660850.json"
        self._run_json_equal_file(url, "results_co_iss_n1462660850.json")

    def test__results_contents_co_iss_n1463306217(self):
        "[test_results_contents.py] co-iss-n1463306217"
        url = "/api/metadata_v2/co-iss-n1463306217.json"
        self._run_json_equal_file(url, "results_co_iss_n1463306217.json")

    def test__results_contents_co_iss_n1481652288(self):
        "[test_results_contents.py] co-iss-n1481652288"
        url = "/api/metadata_v2/co-iss-n1481652288.json"
        self._run_json_equal_file(url, "results_co_iss_n1481652288.json")

    def test__results_contents_co_iss_n1481663213(self):
        "[test_results_contents.py] co-iss-n1481663213"
        url = "/api/metadata_v2/co-iss-n1481663213.json"
        self._run_json_equal_file(url, "results_co_iss_n1481663213.json")

    def test__results_contents_co_iss_n1481666413(self):
        "[test_results_contents.py] co-iss-n1481666413"
        url = "/api/metadata_v2/co-iss-n1481666413.json"
        self._run_json_equal_file(url, "results_co_iss_n1481666413.json")

    def test__results_contents_co_iss_n1482859953(self):
        "[test_results_contents.py] co-iss-n1482859953"
        url = "/api/metadata_v2/co-iss-n1482859953.json"
        self._run_json_equal_file(url, "results_co_iss_n1482859953.json")

    def test__results_contents_co_iss_w1481834905(self):
        "[test_results_contents.py] co-iss-w1481834905"
        url = "/api/metadata_v2/co-iss-w1481834905.json"
        self._run_json_equal_file(url, "results_co_iss_w1481834905.json")

    def test__results_contents_co_uvis_euv2001_001_05_59(self):
        "[test_results_contents.py] co-uvis-euv2001_001_05_59"
        url = "/api/metadata_v2/co-uvis-euv2001_001_05_59.json"
        self._run_json_equal_file(url, "results_co_uvis_euv2001_001_05_59.json")

    def test__results_contents_co_uvis_euv2001_002_12_27(self):
        "[test_results_contents.py] co-uvis-euv2001_002_12_27"
        url = "/api/metadata_v2/co-uvis-euv2001_002_12_27.json"
        self._run_json_equal_file(url, "results_co_uvis_euv2001_002_12_27.json")

    def test__results_contents_co_uvis_euv2001_010_20_59(self):
        "[test_results_contents.py] co-uvis-euv2001_010_20_59"
        url = "/api/metadata_v2/co-uvis-euv2001_010_20_59.json"
        self._run_json_equal_file(url, "results_co_uvis_euv2001_010_20_59.json")

    def test__results_contents_co_uvis_fuv2001_013_06_07(self):
        "[test_results_contents.py] co-uvis-fuv2001_013_06_07"
        url = "/api/metadata_v2/co-uvis-fuv2001_013_06_07.json"
        self._run_json_equal_file(url, "results_co_uvis_fuv2001_013_06_07.json")

    def test__results_contents_co_uvis_hdac2001_022_04_45(self):
        "[test_results_contents.py] co-uvis-hdac2001_022_04_45"
        url = "/api/metadata_v2/co-uvis-hdac2001_022_04_45.json"
        self._run_json_equal_file(url, "results_co_uvis_hdac2001_022_04_45.json")

    def test__results_contents_co_uvis_hsp2001_087_04_00(self):
        "[test_results_contents.py] co-uvis-hsp2001_087_04_00"
        url = "/api/metadata_v2/co-uvis-hsp2001_087_04_00.json"
        self._run_json_equal_file(url, "results_co_uvis_hsp2001_087_04_00.json")

    def test__results_contents_co_vims_v1484504730_vis(self):
        "[test_results_contents.py] co-vims-v1484504730_vis"
        url = "/api/metadata_v2/co-vims-v1484504730_vis.json"
        self._run_json_equal_file(url, "results_co_vims_v1484504730_vis.json")

    def test__results_contents_co_vims_v1484580518_vis(self):
        "[test_results_contents.py] co-vims-v1484580518_vis"
        url = "/api/metadata_v2/co-vims-v1484580518_vis.json"
        self._run_json_equal_file(url, "results_co_vims_v1484580518_vis.json")

    def test__results_contents_co_vims_v1484860325_ir(self):
        "[test_results_contents.py] co-vims-v1484860325_ir"
        url = "/api/metadata_v2/co-vims-v1484860325_ir.json"
        self._run_json_equal_file(url, "results_co_vims_v1484860325_ir.json")

    def test__results_contents_co_vims_v1485757341_ir(self):
        "[test_results_contents.py] co-vims-v1485757341_ir"
        url = "/api/metadata_v2/co-vims-v1485757341_ir.json"
        self._run_json_equal_file(url, "results_co_vims_v1485757341_ir.json")

    def test__results_contents_co_vims_v1485803787_ir(self):
        "[test_results_contents.py] co-vims-v1485803787_ir"
        url = "/api/metadata_v2/co-vims-v1485803787_ir.json"
        self._run_json_equal_file(url, "results_co_vims_v1485803787_ir.json")

    def test__results_contents_co_vims_v1487262184_ir(self):
        "[test_results_contents.py] co-vims-v1487262184_ir"
        url = "/api/metadata_v2/co-vims-v1487262184_ir.json"
        self._run_json_equal_file(url, "results_co_vims_v1487262184_ir.json")

    def test__results_contents_co_vims_v1490874999_001_vis(self):
        "[test_results_contents.py] co-vims-v1490874999_001_vis"
        url = "/api/metadata_v2/co-vims-v1490874999_001_vis.json"
        self._run_json_equal_file(url, "results_co_vims_v1490874999_001_vis.json")

    def test__results_contents_go_ssi_c0347769100(self):
        "[test_results_contents.py] go-ssi-c0347769100"
        url = "/api/metadata_v2/go-ssi-c0347769100.json"
        self._run_json_equal_file(url, "results_go_ssi_c0347769100.json")

    def test__results_contents_go_ssi_c0349673988(self):
        "[test_results_contents.py] go-ssi-c0349673988"
        url = "/api/metadata_v2/go-ssi-c0349673988.json"
        self._run_json_equal_file(url, "results_go_ssi_c0349673988.json")

    def test__results_contents_go_ssi_c0349761213(self):
        "[test_results_contents.py] go-ssi-c0349761213"
        url = "/api/metadata_v2/go-ssi-c0349761213.json"
        self._run_json_equal_file(url, "results_go_ssi_c0349761213.json")

    def test__results_contents_go_ssi_c0359986600(self):
        "[test_results_contents.py] go-ssi-c0359986600"
        url = "/api/metadata_v2/go-ssi-c0359986600.json"
        self._run_json_equal_file(url, "results_go_ssi_c0359986600.json")

    def test__results_contents_hst_05642_wfpc2_u2fi0c05t(self):
        "[test_results_contents.py] hst-05642-wfpc2-u2fi0c05t"
        url = "/api/metadata_v2/hst-05642-wfpc2-u2fi0c05t.json"
        self._run_json_equal_file(url, "results_hst_05642_wfpc2_u2fi0c05t.json")

    def test__results_contents_hst_05642_wfpc2_u2fi0o0bt(self):
        "[test_results_contents.py] hst-05642-wfpc2-u2fi0o0bt"
        url = "/api/metadata_v2/hst-05642-wfpc2-u2fi0o0bt.json"
        self._run_json_equal_file(url, "results_hst_05642_wfpc2_u2fi0o0bt.json")

    def test__results_contents_hst_05642_wfpc2_u2fi1901t(self):
        "[test_results_contents.py] hst-05642-wfpc2-u2fi1901t"
        url = "/api/metadata_v2/hst-05642-wfpc2-u2fi1901t.json"
        self._run_json_equal_file(url, "results_hst_05642_wfpc2_u2fi1901t.json")

    def test__results_contents_hst_07243_nicmos_n4be03seq(self):
        "[test_results_contents.py] hst-07243-nicmos-n4be03seq"
        url = "/api/metadata_v2/hst-07243-nicmos-n4be03seq.json"
        self._run_json_equal_file(url, "results_hst_07243_nicmos_n4be03seq.json")

    def test__results_contents_hst_07243_nicmos_n4be05blq(self):
        "[test_results_contents.py] hst-07243-nicmos-n4be05blq"
        url = "/api/metadata_v2/hst-07243-nicmos-n4be05blq.json"
        self._run_json_equal_file(url, "results_hst_07243_nicmos_n4be05blq.json")

    def test__results_contents_hst_07308_stis_o43b2sxgq(self):
        "[test_results_contents.py] hst-07308-stis-o43b2sxgq"
        url = "/api/metadata_v2/hst-07308-stis-o43b2sxgq.json"
        self._run_json_equal_file(url, "results_hst_07308_stis_o43b2sxgq.json")

    def test__results_contents_hst_07308_stis_o43ba6bxq(self):
        "[test_results_contents.py] hst-07308-stis-o43ba6bxq"
        url = "/api/metadata_v2/hst-07308-stis-o43ba6bxq.json"
        self._run_json_equal_file(url, "results_hst_07308_stis_o43ba6bxq.json")

    def test__results_contents_hst_07308_stis_o43bd9bhq(self):
        "[test_results_contents.py] hst-07308-stis-o43bd9bhq"
        url = "/api/metadata_v2/hst-07308-stis-o43bd9bhq.json"
        self._run_json_equal_file(url, "results_hst_07308_stis_o43bd9bhq.json")

    def test__results_contents_hst_09975_acs_j8n460zvq(self):
        "[test_results_contents.py] hst-09975-acs-j8n460zvq"
        url = "/api/metadata_v2/hst-09975-acs-j8n460zvq.json"
        self._run_json_equal_file(url, "results_hst_09975_acs_j8n460zvq.json")

    def test__results_contents_hst_11559_wfc3_ib4v22gxq(self):
        "[test_results_contents.py] hst-11559-wfc3-ib4v22gxq"
        url = "/api/metadata_v2/hst-11559-wfc3-ib4v22gxq.json"
        self._run_json_equal_file(url, "results_hst_11559_wfc3_ib4v22gxq.json")

    def test__results_contents_nh_lorri_lor_0299075349(self):
        "[test_results_contents.py] nh-lorri-lor_0299075349"
        url = "/api/metadata_v2/nh-lorri-lor_0299075349.json"
        self._run_json_equal_file(url, "results_nh_lorri_lor_0299075349.json")

    def test__results_contents_nh_lorri_lor_0329817268(self):
        "[test_results_contents.py] nh-lorri-lor_0329817268"
        url = "/api/metadata_v2/nh-lorri-lor_0329817268.json"
        self._run_json_equal_file(url, "results_nh_lorri_lor_0329817268.json")

    def test__results_contents_nh_lorri_lor_0330787458(self):
        "[test_results_contents.py] nh-lorri-lor_0330787458"
        url = "/api/metadata_v2/nh-lorri-lor_0330787458.json"
        self._run_json_equal_file(url, "results_nh_lorri_lor_0330787458.json")

    def test__results_contents_nh_mvic_mc1_0005261846(self):
        "[test_results_contents.py] nh-mvic-mc1_0005261846"
        url = "/api/metadata_v2/nh-mvic-mc1_0005261846.json"
        self._run_json_equal_file(url, "results_nh_mvic_mc1_0005261846.json")

    def test__results_contents_nh_mvic_mp1_0012448104(self):
        "[test_results_contents.py] nh-mvic-mp1_0012448104"
        url = "/api/metadata_v2/nh-mvic-mp1_0012448104.json"
        self._run_json_equal_file(url, "results_nh_mvic_mp1_0012448104.json")

    def test__results_contents_lick1m_ccdc_occ_1989_184_28sgr_i(self):
        "[test_results_contents.py] lick1m-ccdc-occ-1989-184-28sgr-i"
        url = "/api/metadata_v2/lick1m-ccdc-occ-1989-184-28sgr-i.json"
        self._run_json_equal_file(url, "results_lick1m_ccdc_occ_1989_184_28sgr_i.json")

    def test__results_contents_mcd27m_iirar_occ_1989_184_28sgr_i(self):
        "[test_results_contents.py] mcd27m-iirar-occ-1989-184-28sgr-i"
        url = "/api/metadata_v2/mcd27m-iirar-occ-1989-184-28sgr-i.json"
        self._run_json_equal_file(url, "results_mcd27m_iirar_occ_1989_184_28sgr_i.json")

    def test__results_contents_eso1m_apph_occ_1989_184_28sgr_e(self):
        "[test_results_contents.py] eso1m-apph-occ-1989-184-28sgr-e"
        url = "/api/metadata_v2/eso1m-apph-occ-1989-184-28sgr-e.json"
        self._run_json_equal_file(url, "results_eso1m_apph_occ_1989_184_28sgr_e.json")

    def test__results_contents_co_rss_occ_2005_123_k26_i(self):
        "[test_results_contents.py] co-rss-occ-2005-123-k26-i"
        url = "/api/metadata_v2/co-rss-occ-2005-123-k26-i.json"
        self._run_json_equal_file(url, "results_co_rss_occ_2005_123_k26_i.json")

    def test__results_contents_co_rss_occ_2008_217_s63_i(self):
        "[test_results_contents.py] co-rss-occ-2008-217-s63-i"
        url = "/api/metadata_v2/co-rss-occ-2008-217-s63-i.json"
        self._run_json_equal_file(url, "results_co_rss_occ_2008_217_s63_i.json")

    def test__results_contents_co_rss_occ_2010_170_x34_e(self):
        "[test_results_contents.py] co-rss-occ-2010-170-x34-e"
        url = "/api/metadata_v2/co-rss-occ-2010-170-x34-e.json"
        self._run_json_equal_file(url, "results_co_rss_occ_2010_170_x34_e.json")

    def test__results_contents_co_uvis_occ_2005_175_126tau_i(self):
        "[test_results_contents.py] co-uvis-occ-2005-175-126tau-i"
        url = "/api/metadata_v2/co-uvis-occ-2005-175-126tau-i.json"
        self._run_json_equal_file(url, "results_co_uvis_occ_2005_175_126tau_i.json")

    def test__results_contents_co_uvis_occ_2009_015_gamcas_e(self):
        "[test_results_contents.py] co-uvis-occ-2009-015-gamcas-e"
        url = "/api/metadata_v2/co-uvis-occ-2009-015-gamcas-e.json"
        self._run_json_equal_file(url, "results_co_uvis_occ_2009_015_gamcas_e.json")

    def test__results_contents_co_vims_occ_2006_204_alpori_i(self):
        "[test_results_contents.py] co-vims-occ-2006-204-alpori-i"
        url = "/api/metadata_v2/co-vims-occ-2006-204-alpori-i.json"
        self._run_json_equal_file(url, "results_co_vims_occ_2006_204_alpori_i.json")

    def test__results_contents_co_vims_occ_2014_175_l2pup_e(self):
        "[test_results_contents.py] co-vims-occ-2014-175-l2pup-e"
        url = "/api/metadata_v2/co-vims-occ-2014-175-l2pup-e.json"
        self._run_json_equal_file(url, "results_co_vims_occ_2014_175_l2pup_e.json")
