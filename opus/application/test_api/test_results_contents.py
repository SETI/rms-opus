# opus/application/test_api/test_results_contents.py

import json
import logging
import requests
from unittest import TestCase

from django.core.cache import cache
from rest_framework.test import RequestsClient

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


            #################################
            ######### RESULTS TESTS #########
            #################################

    def test__results_contents_co_cirs_0408010657_fp3_metadata(self):
        "[test_results_contents.py] co-cirs-0408010657-fp3 metadata"
        url = "/api/metadata/co-cirs-0408010657-fp3.json"
        self._run_json_equal_file(url, "results_co_cirs_0408010657_fp3_metadata.json")

    def test__results_contents_co_cirs_0408010657_fp3_files(self):
        "[test_results_contents.py] co-cirs-0408010657-fp3 files"
        url = "/api/files/co-cirs-0408010657-fp3.json"
        self._run_json_equal_file(url, "results_co_cirs_0408010657_fp3_files.json")

    def test__results_contents_co_cirs_0408010657_fp3_images(self):
        "[test_results_contents.py] co-cirs-0408010657-fp3 images"
        url = "/api/images.json?opusid=co-cirs-0408010657-fp3"
        self._run_json_equal_file(url, "results_co_cirs_0408010657_fp3_images.json")

    def test__results_contents_co_cirs_0408031652_fp1_metadata(self):
        "[test_results_contents.py] co-cirs-0408031652-fp1 metadata"
        url = "/api/metadata/co-cirs-0408031652-fp1.json"
        self._run_json_equal_file(url, "results_co_cirs_0408031652_fp1_metadata.json")

    def test__results_contents_co_cirs_0408031652_fp1_files(self):
        "[test_results_contents.py] co-cirs-0408031652-fp1 files"
        url = "/api/files/co-cirs-0408031652-fp1.json"
        self._run_json_equal_file(url, "results_co_cirs_0408031652_fp1_files.json")

    def test__results_contents_co_cirs_0408031652_fp1_images(self):
        "[test_results_contents.py] co-cirs-0408031652-fp1 images"
        url = "/api/images.json?opusid=co-cirs-0408031652-fp1"
        self._run_json_equal_file(url, "results_co_cirs_0408031652_fp1_images.json")

    def test__results_contents_co_cirs_0408041543_fp3_metadata(self):
        "[test_results_contents.py] co-cirs-0408041543-fp3 metadata"
        url = "/api/metadata/co-cirs-0408041543-fp3.json"
        self._run_json_equal_file(url, "results_co_cirs_0408041543_fp3_metadata.json")

    def test__results_contents_co_cirs_0408041543_fp3_files(self):
        "[test_results_contents.py] co-cirs-0408041543-fp3 files"
        url = "/api/files/co-cirs-0408041543-fp3.json"
        self._run_json_equal_file(url, "results_co_cirs_0408041543_fp3_files.json")

    def test__results_contents_co_cirs_0408041543_fp3_images(self):
        "[test_results_contents.py] co-cirs-0408041543-fp3 images"
        url = "/api/images.json?opusid=co-cirs-0408041543-fp3"
        self._run_json_equal_file(url, "results_co_cirs_0408041543_fp3_images.json")

    def test__results_contents_co_cirs_0408152208_fp3_metadata(self):
        "[test_results_contents.py] co-cirs-0408152208-fp3 metadata"
        url = "/api/metadata/co-cirs-0408152208-fp3.json"
        self._run_json_equal_file(url, "results_co_cirs_0408152208_fp3_metadata.json")

    def test__results_contents_co_cirs_0408152208_fp3_files(self):
        "[test_results_contents.py] co-cirs-0408152208-fp3 files"
        url = "/api/files/co-cirs-0408152208-fp3.json"
        self._run_json_equal_file(url, "results_co_cirs_0408152208_fp3_files.json")

    def test__results_contents_co_cirs_0408152208_fp3_images(self):
        "[test_results_contents.py] co-cirs-0408152208-fp3 images"
        url = "/api/images.json?opusid=co-cirs-0408152208-fp3"
        self._run_json_equal_file(url, "results_co_cirs_0408152208_fp3_images.json")

    def test__results_contents_co_cirs_0408161433_fp4_metadata(self):
        "[test_results_contents.py] co-cirs-0408161433-fp4 metadata"
        url = "/api/metadata/co-cirs-0408161433-fp4.json"
        self._run_json_equal_file(url, "results_co_cirs_0408161433_fp4_metadata.json")

    def test__results_contents_co_cirs_0408161433_fp4_files(self):
        "[test_results_contents.py] co-cirs-0408161433-fp4 files"
        url = "/api/files/co-cirs-0408161433-fp4.json"
        self._run_json_equal_file(url, "results_co_cirs_0408161433_fp4_files.json")

    def test__results_contents_co_cirs_0408161433_fp4_images(self):
        "[test_results_contents.py] co-cirs-0408161433-fp4 images"
        url = "/api/images.json?opusid=co-cirs-0408161433-fp4"
        self._run_json_equal_file(url, "results_co_cirs_0408161433_fp4_images.json")

    def test__results_contents_co_cirs_0408220524_fp4_metadata(self):
        "[test_results_contents.py] co-cirs-0408220524-fp4 metadata"
        url = "/api/metadata/co-cirs-0408220524-fp4.json"
        self._run_json_equal_file(url, "results_co_cirs_0408220524_fp4_metadata.json")

    def test__results_contents_co_cirs_0408220524_fp4_files(self):
        "[test_results_contents.py] co-cirs-0408220524-fp4 files"
        url = "/api/files/co-cirs-0408220524-fp4.json"
        self._run_json_equal_file(url, "results_co_cirs_0408220524_fp4_files.json")

    def test__results_contents_co_cirs_0408220524_fp4_images(self):
        "[test_results_contents.py] co-cirs-0408220524-fp4 images"
        url = "/api/images.json?opusid=co-cirs-0408220524-fp4"
        self._run_json_equal_file(url, "results_co_cirs_0408220524_fp4_images.json")

    def test__results_contents_co_cirs_cube_000ph_fp3daymap001_ci004_609_f1_038e_metadata(self):
        "[test_results_contents.py] co-cirs-cube-000ph_fp3daymap001_ci004_609_f1_038e metadata"
        url = "/api/metadata/co-cirs-cube-000ph_fp3daymap001_ci004_609_f1_038e.json"
        self._run_json_equal_file(url, "results_co_cirs_cube_000ph_fp3daymap001_ci004_609_f1_038e_metadata.json")

    def test__results_contents_co_cirs_cube_000ph_fp3daymap001_ci004_609_f1_038e_files(self):
        "[test_results_contents.py] co-cirs-cube-000ph_fp3daymap001_ci004_609_f1_038e files"
        url = "/api/files/co-cirs-cube-000ph_fp3daymap001_ci004_609_f1_038e.json"
        self._run_json_equal_file(url, "results_co_cirs_cube_000ph_fp3daymap001_ci004_609_f1_038e_files.json")

    def test__results_contents_co_cirs_cube_000ph_fp3daymap001_ci004_609_f1_038e_images(self):
        "[test_results_contents.py] co-cirs-cube-000ph_fp3daymap001_ci004_609_f1_038e images"
        url = "/api/images.json?opusid=co-cirs-cube-000ph_fp3daymap001_ci004_609_f1_038e"
        self._run_json_equal_file(url, "results_co_cirs_cube_000ph_fp3daymap001_ci004_609_f1_038e_images.json")

    def test__results_contents_co_cirs_cube_000ia_presoi001____ri____699_f4_038p_metadata(self):
        "[test_results_contents.py] co-cirs-cube-000ia_presoi001____ri____699_f4_038p metadata"
        url = "/api/metadata/co-cirs-cube-000ia_presoi001____ri____699_f4_038p.json"
        self._run_json_equal_file(url, "results_co_cirs_cube_000ia_presoi001____ri____699_f4_038p_metadata.json")

    def test__results_contents_co_cirs_cube_000ia_presoi001____ri____699_f4_038p_files(self):
        "[test_results_contents.py] co-cirs-cube-000ia_presoi001____ri____699_f4_038p files"
        url = "/api/files/co-cirs-cube-000ia_presoi001____ri____699_f4_038p.json"
        self._run_json_equal_file(url, "results_co_cirs_cube_000ia_presoi001____ri____699_f4_038p_files.json")

    def test__results_contents_co_cirs_cube_000ia_presoi001____ri____699_f4_038p_images(self):
        "[test_results_contents.py] co-cirs-cube-000ia_presoi001____ri____699_f4_038p images"
        url = "/api/images.json?opusid=co-cirs-cube-000ia_presoi001____ri____699_f4_038p"
        self._run_json_equal_file(url, "results_co_cirs_cube_000ia_presoi001____ri____699_f4_038p_images.json")

    def test__results_contents_co_cirs_cube_000rb_comp001______ci005_680_f3_224r_metadata(self):
        "[test_results_contents.py] co-cirs-cube-000rb_comp001______ci005_680_f3_224r metadata"
        url = "/api/metadata/co-cirs-cube-000rb_comp001______ci005_680_f3_224r.json"
        self._run_json_equal_file(url, "results_co_cirs_cube_000rb_comp001______ci005_680_f3_224r_metadata.json")

    def test__results_contents_co_cirs_cube_000rb_comp001______ci005_680_f3_224r_files(self):
        "[test_results_contents.py] co-cirs-cube-000rb_comp001______ci005_680_f3_224r files"
        url = "/api/files/co-cirs-cube-000rb_comp001______ci005_680_f3_224r.json"
        self._run_json_equal_file(url, "results_co_cirs_cube_000rb_comp001______ci005_680_f3_224r_files.json")

    def test__results_contents_co_cirs_cube_000rb_comp001______ci005_680_f3_224r_images(self):
        "[test_results_contents.py] co-cirs-cube-000rb_comp001______ci005_680_f3_224r images"
        url = "/api/images.json?opusid=co-cirs-cube-000rb_comp001______ci005_680_f3_224r"
        self._run_json_equal_file(url, "results_co_cirs_cube_000rb_comp001______ci005_680_f3_224r_images.json")

    def test__results_contents_co_cirs_cube_127en_icyplu001____uv____699_f1_039e_metadata(self):
        "[test_results_contents.py] co-cirs-cube-127en_icyplu001____uv____699_f1_039e metadata"
        url = "/api/metadata/co-cirs-cube-127en_icyplu001____uv____699_f1_039e.json"
        self._run_json_equal_file(url, "results_co_cirs_cube_127en_icyplu001____uv____699_f1_039e_metadata.json")

    def test__results_contents_co_cirs_cube_127en_icyplu001____uv____699_f1_039e_files(self):
        "[test_results_contents.py] co-cirs-cube-127en_icyplu001____uv____699_f1_039e files"
        url = "/api/files/co-cirs-cube-127en_icyplu001____uv____699_f1_039e.json"
        self._run_json_equal_file(url, "results_co_cirs_cube_127en_icyplu001____uv____699_f1_039e_files.json")

    def test__results_contents_co_cirs_cube_127en_icyplu001____uv____699_f1_039e_images(self):
        "[test_results_contents.py] co-cirs-cube-127en_icyplu001____uv____699_f1_039e images"
        url = "/api/images.json?opusid=co-cirs-cube-127en_icyplu001____uv____699_f1_039e"
        self._run_json_equal_file(url, "results_co_cirs_cube_127en_icyplu001____uv____699_f1_039e_images.json")

    def test__results_contents_co_cirs_cube_127ic_dscal10066___sp____699_f4_039p_metadata(self):
        "[test_results_contents.py] co-cirs-cube-127ic_dscal10066___sp____699_f4_039p metadata"
        url = "/api/metadata/co-cirs-cube-127ic_dscal10066___sp____699_f4_039p.json"
        self._run_json_equal_file(url, "results_co_cirs_cube_127ic_dscal10066___sp____699_f4_039p_metadata.json")

    def test__results_contents_co_cirs_cube_127ic_dscal10066___sp____699_f4_039p_files(self):
        "[test_results_contents.py] co-cirs-cube-127ic_dscal10066___sp____699_f4_039p files"
        url = "/api/files/co-cirs-cube-127ic_dscal10066___sp____699_f4_039p.json"
        self._run_json_equal_file(url, "results_co_cirs_cube_127ic_dscal10066___sp____699_f4_039p_files.json")

    def test__results_contents_co_cirs_cube_127ic_dscal10066___sp____699_f4_039p_images(self):
        "[test_results_contents.py] co-cirs-cube-127ic_dscal10066___sp____699_f4_039p images"
        url = "/api/images.json?opusid=co-cirs-cube-127ic_dscal10066___sp____699_f4_039p"
        self._run_json_equal_file(url, "results_co_cirs_cube_127ic_dscal10066___sp____699_f4_039p_images.json")

    def test__results_contents_co_cirs_cube_128ri_lrlemp001____is____680_f3_039r_metadata(self):
        "[test_results_contents.py] co-cirs-cube-128ri_lrlemp001____is____680_f3_039r metadata"
        url = "/api/metadata/co-cirs-cube-128ri_lrlemp001____is____680_f3_039r.json"
        self._run_json_equal_file(url, "results_co_cirs_cube_128ri_lrlemp001____is____680_f3_039r_metadata.json")

    def test__results_contents_co_cirs_cube_128ri_lrlemp001____is____680_f3_039r_files(self):
        "[test_results_contents.py] co-cirs-cube-128ri_lrlemp001____is____680_f3_039r files"
        url = "/api/files/co-cirs-cube-128ri_lrlemp001____is____680_f3_039r.json"
        self._run_json_equal_file(url, "results_co_cirs_cube_128ri_lrlemp001____is____680_f3_039r_files.json")

    def test__results_contents_co_cirs_cube_128ri_lrlemp001____is____680_f3_039r_images(self):
        "[test_results_contents.py] co-cirs-cube-128ri_lrlemp001____is____680_f3_039r images"
        url = "/api/images.json?opusid=co-cirs-cube-128ri_lrlemp001____is____680_f3_039r"
        self._run_json_equal_file(url, "results_co_cirs_cube_128ri_lrlemp001____is____680_f3_039r_images.json")

    def test__results_contents_co_iss_n1460961193_metadata(self):
        "[test_results_contents.py] co-iss-n1460961193 metadata"
        url = "/api/metadata/co-iss-n1460961193.json"
        self._run_json_equal_file(url, "results_co_iss_n1460961193_metadata.json")

    def test__results_contents_co_iss_n1460961193_files(self):
        "[test_results_contents.py] co-iss-n1460961193 files"
        url = "/api/files/co-iss-n1460961193.json"
        self._run_json_equal_file(url, "results_co_iss_n1460961193_files.json")

    def test__results_contents_co_iss_n1460961193_images(self):
        "[test_results_contents.py] co-iss-n1460961193 images"
        url = "/api/images.json?opusid=co-iss-n1460961193"
        self._run_json_equal_file(url, "results_co_iss_n1460961193_images.json")

    def test__results_contents_co_iss_n1461527506_metadata(self):
        "[test_results_contents.py] co-iss-n1461527506 metadata"
        url = "/api/metadata/co-iss-n1461527506.json"
        self._run_json_equal_file(url, "results_co_iss_n1461527506_metadata.json")

    def test__results_contents_co_iss_n1461527506_files(self):
        "[test_results_contents.py] co-iss-n1461527506 files"
        url = "/api/files/co-iss-n1461527506.json"
        self._run_json_equal_file(url, "results_co_iss_n1461527506_files.json")

    def test__results_contents_co_iss_n1461527506_images(self):
        "[test_results_contents.py] co-iss-n1461527506 images"
        url = "/api/images.json?opusid=co-iss-n1461527506"
        self._run_json_equal_file(url, "results_co_iss_n1461527506_images.json")

    def test__results_contents_co_iss_n1461810160_metadata(self):
        "[test_results_contents.py] co-iss-n1461810160 metadata"
        url = "/api/metadata/co-iss-n1461810160.json"
        self._run_json_equal_file(url, "results_co_iss_n1461810160_metadata.json")

    def test__results_contents_co_iss_n1461810160_files(self):
        "[test_results_contents.py] co-iss-n1461810160 files"
        url = "/api/files/co-iss-n1461810160.json"
        self._run_json_equal_file(url, "results_co_iss_n1461810160_files.json")

    def test__results_contents_co_iss_n1461810160_images(self):
        "[test_results_contents.py] co-iss-n1461810160 images"
        url = "/api/images.json?opusid=co-iss-n1461810160"
        self._run_json_equal_file(url, "results_co_iss_n1461810160_images.json")

    def test__results_contents_co_iss_n1462660850_metadata(self):
        "[test_results_contents.py] co-iss-n1462660850 metadata"
        url = "/api/metadata/co-iss-n1462660850.json"
        self._run_json_equal_file(url, "results_co_iss_n1462660850_metadata.json")

    def test__results_contents_co_iss_n1462660850_files(self):
        "[test_results_contents.py] co-iss-n1462660850 files"
        url = "/api/files/co-iss-n1462660850.json"
        self._run_json_equal_file(url, "results_co_iss_n1462660850_files.json")

    def test__results_contents_co_iss_n1462660850_images(self):
        "[test_results_contents.py] co-iss-n1462660850 images"
        url = "/api/images.json?opusid=co-iss-n1462660850"
        self._run_json_equal_file(url, "results_co_iss_n1462660850_images.json")

    def test__results_contents_co_iss_n1463306217_metadata(self):
        "[test_results_contents.py] co-iss-n1463306217 metadata"
        url = "/api/metadata/co-iss-n1463306217.json"
        self._run_json_equal_file(url, "results_co_iss_n1463306217_metadata.json")

    def test__results_contents_co_iss_n1463306217_files(self):
        "[test_results_contents.py] co-iss-n1463306217 files"
        url = "/api/files/co-iss-n1463306217.json"
        self._run_json_equal_file(url, "results_co_iss_n1463306217_files.json")

    def test__results_contents_co_iss_n1463306217_images(self):
        "[test_results_contents.py] co-iss-n1463306217 images"
        url = "/api/images.json?opusid=co-iss-n1463306217"
        self._run_json_equal_file(url, "results_co_iss_n1463306217_images.json")

    def test__results_contents_co_iss_n1481652288_metadata(self):
        "[test_results_contents.py] co-iss-n1481652288 metadata"
        url = "/api/metadata/co-iss-n1481652288.json"
        self._run_json_equal_file(url, "results_co_iss_n1481652288_metadata.json")

    def test__results_contents_co_iss_n1481652288_files(self):
        "[test_results_contents.py] co-iss-n1481652288 files"
        url = "/api/files/co-iss-n1481652288.json"
        self._run_json_equal_file(url, "results_co_iss_n1481652288_files.json")

    def test__results_contents_co_iss_n1481652288_images(self):
        "[test_results_contents.py] co-iss-n1481652288 images"
        url = "/api/images.json?opusid=co-iss-n1481652288"
        self._run_json_equal_file(url, "results_co_iss_n1481652288_images.json")

    def test__results_contents_co_iss_n1481663213_metadata(self):
        "[test_results_contents.py] co-iss-n1481663213 metadata"
        url = "/api/metadata/co-iss-n1481663213.json"
        self._run_json_equal_file(url, "results_co_iss_n1481663213_metadata.json")

    def test__results_contents_co_iss_n1481663213_files(self):
        "[test_results_contents.py] co-iss-n1481663213 files"
        url = "/api/files/co-iss-n1481663213.json"
        self._run_json_equal_file(url, "results_co_iss_n1481663213_files.json")

    def test__results_contents_co_iss_n1481663213_images(self):
        "[test_results_contents.py] co-iss-n1481663213 images"
        url = "/api/images.json?opusid=co-iss-n1481663213"
        self._run_json_equal_file(url, "results_co_iss_n1481663213_images.json")

    def test__results_contents_co_iss_n1481666413_metadata(self):
        "[test_results_contents.py] co-iss-n1481666413 metadata"
        url = "/api/metadata/co-iss-n1481666413.json"
        self._run_json_equal_file(url, "results_co_iss_n1481666413_metadata.json")

    def test__results_contents_co_iss_n1481666413_files(self):
        "[test_results_contents.py] co-iss-n1481666413 files"
        url = "/api/files/co-iss-n1481666413.json"
        self._run_json_equal_file(url, "results_co_iss_n1481666413_files.json")

    def test__results_contents_co_iss_n1481666413_images(self):
        "[test_results_contents.py] co-iss-n1481666413 images"
        url = "/api/images.json?opusid=co-iss-n1481666413"
        self._run_json_equal_file(url, "results_co_iss_n1481666413_images.json")

    def test__results_contents_co_iss_n1482859953_metadata(self):
        "[test_results_contents.py] co-iss-n1482859953 metadata"
        url = "/api/metadata/co-iss-n1482859953.json"
        self._run_json_equal_file(url, "results_co_iss_n1482859953_metadata.json")

    def test__results_contents_co_iss_n1482859953_files(self):
        "[test_results_contents.py] co-iss-n1482859953 files"
        url = "/api/files/co-iss-n1482859953.json"
        self._run_json_equal_file(url, "results_co_iss_n1482859953_files.json")

    def test__results_contents_co_iss_n1482859953_images(self):
        "[test_results_contents.py] co-iss-n1482859953 images"
        url = "/api/images.json?opusid=co-iss-n1482859953"
        self._run_json_equal_file(url, "results_co_iss_n1482859953_images.json")

    def test__results_contents_co_iss_w1481834905_metadata(self):
        "[test_results_contents.py] co-iss-w1481834905 metadata"
        url = "/api/metadata/co-iss-w1481834905.json"
        self._run_json_equal_file(url, "results_co_iss_w1481834905_metadata.json")

    def test__results_contents_co_iss_w1481834905_files(self):
        "[test_results_contents.py] co-iss-w1481834905 files"
        url = "/api/files/co-iss-w1481834905.json"
        self._run_json_equal_file(url, "results_co_iss_w1481834905_files.json")

    def test__results_contents_co_iss_w1481834905_images(self):
        "[test_results_contents.py] co-iss-w1481834905 images"
        url = "/api/images.json?opusid=co-iss-w1481834905"
        self._run_json_equal_file(url, "results_co_iss_w1481834905_images.json")

    def test__results_contents_co_uvis_euv2001_001_05_59_metadata(self):
        "[test_results_contents.py] co-uvis-euv2001_001_05_59 metadata"
        url = "/api/metadata/co-uvis-euv2001_001_05_59.json"
        self._run_json_equal_file(url, "results_co_uvis_euv2001_001_05_59_metadata.json")

    def test__results_contents_co_uvis_euv2001_001_05_59_files(self):
        "[test_results_contents.py] co-uvis-euv2001_001_05_59 files"
        url = "/api/files/co-uvis-euv2001_001_05_59.json"
        self._run_json_equal_file(url, "results_co_uvis_euv2001_001_05_59_files.json")

    def test__results_contents_co_uvis_euv2001_001_05_59_images(self):
        "[test_results_contents.py] co-uvis-euv2001_001_05_59 images"
        url = "/api/images.json?opusid=co-uvis-euv2001_001_05_59"
        self._run_json_equal_file(url, "results_co_uvis_euv2001_001_05_59_images.json")

    def test__results_contents_co_uvis_euv2001_002_12_27_metadata(self):
        "[test_results_contents.py] co-uvis-euv2001_002_12_27 metadata"
        url = "/api/metadata/co-uvis-euv2001_002_12_27.json"
        self._run_json_equal_file(url, "results_co_uvis_euv2001_002_12_27_metadata.json")

    def test__results_contents_co_uvis_euv2001_002_12_27_files(self):
        "[test_results_contents.py] co-uvis-euv2001_002_12_27 files"
        url = "/api/files/co-uvis-euv2001_002_12_27.json"
        self._run_json_equal_file(url, "results_co_uvis_euv2001_002_12_27_files.json")

    def test__results_contents_co_uvis_euv2001_002_12_27_images(self):
        "[test_results_contents.py] co-uvis-euv2001_002_12_27 images"
        url = "/api/images.json?opusid=co-uvis-euv2001_002_12_27"
        self._run_json_equal_file(url, "results_co_uvis_euv2001_002_12_27_images.json")

    def test__results_contents_co_uvis_euv2001_010_20_59_metadata(self):
        "[test_results_contents.py] co-uvis-euv2001_010_20_59 metadata"
        url = "/api/metadata/co-uvis-euv2001_010_20_59.json"
        self._run_json_equal_file(url, "results_co_uvis_euv2001_010_20_59_metadata.json")

    def test__results_contents_co_uvis_euv2001_010_20_59_files(self):
        "[test_results_contents.py] co-uvis-euv2001_010_20_59 files"
        url = "/api/files/co-uvis-euv2001_010_20_59.json"
        self._run_json_equal_file(url, "results_co_uvis_euv2001_010_20_59_files.json")

    def test__results_contents_co_uvis_euv2001_010_20_59_images(self):
        "[test_results_contents.py] co-uvis-euv2001_010_20_59 images"
        url = "/api/images.json?opusid=co-uvis-euv2001_010_20_59"
        self._run_json_equal_file(url, "results_co_uvis_euv2001_010_20_59_images.json")

    def test__results_contents_co_uvis_fuv2001_013_06_07_metadata(self):
        "[test_results_contents.py] co-uvis-fuv2001_013_06_07 metadata"
        url = "/api/metadata/co-uvis-fuv2001_013_06_07.json"
        self._run_json_equal_file(url, "results_co_uvis_fuv2001_013_06_07_metadata.json")

    def test__results_contents_co_uvis_fuv2001_013_06_07_files(self):
        "[test_results_contents.py] co-uvis-fuv2001_013_06_07 files"
        url = "/api/files/co-uvis-fuv2001_013_06_07.json"
        self._run_json_equal_file(url, "results_co_uvis_fuv2001_013_06_07_files.json")

    def test__results_contents_co_uvis_fuv2001_013_06_07_images(self):
        "[test_results_contents.py] co-uvis-fuv2001_013_06_07 images"
        url = "/api/images.json?opusid=co-uvis-fuv2001_013_06_07"
        self._run_json_equal_file(url, "results_co_uvis_fuv2001_013_06_07_images.json")

    def test__results_contents_co_uvis_hdac2001_022_04_45_metadata(self):
        "[test_results_contents.py] co-uvis-hdac2001_022_04_45 metadata"
        url = "/api/metadata/co-uvis-hdac2001_022_04_45.json"
        self._run_json_equal_file(url, "results_co_uvis_hdac2001_022_04_45_metadata.json")

    def test__results_contents_co_uvis_hdac2001_022_04_45_files(self):
        "[test_results_contents.py] co-uvis-hdac2001_022_04_45 files"
        url = "/api/files/co-uvis-hdac2001_022_04_45.json"
        self._run_json_equal_file(url, "results_co_uvis_hdac2001_022_04_45_files.json")

    def test__results_contents_co_uvis_hdac2001_022_04_45_images(self):
        "[test_results_contents.py] co-uvis-hdac2001_022_04_45 images"
        url = "/api/images.json?opusid=co-uvis-hdac2001_022_04_45"
        self._run_json_equal_file(url, "results_co_uvis_hdac2001_022_04_45_images.json")

    def test__results_contents_co_uvis_hsp2001_087_04_00_metadata(self):
        "[test_results_contents.py] co-uvis-hsp2001_087_04_00 metadata"
        url = "/api/metadata/co-uvis-hsp2001_087_04_00.json"
        self._run_json_equal_file(url, "results_co_uvis_hsp2001_087_04_00_metadata.json")

    def test__results_contents_co_uvis_hsp2001_087_04_00_files(self):
        "[test_results_contents.py] co-uvis-hsp2001_087_04_00 files"
        url = "/api/files/co-uvis-hsp2001_087_04_00.json"
        self._run_json_equal_file(url, "results_co_uvis_hsp2001_087_04_00_files.json")

    def test__results_contents_co_uvis_hsp2001_087_04_00_images(self):
        "[test_results_contents.py] co-uvis-hsp2001_087_04_00 images"
        url = "/api/images.json?opusid=co-uvis-hsp2001_087_04_00"
        self._run_json_equal_file(url, "results_co_uvis_hsp2001_087_04_00_images.json")

    def test__results_contents_co_vims_v1484504730_vis_metadata(self):
        "[test_results_contents.py] co-vims-v1484504730_vis metadata"
        url = "/api/metadata/co-vims-v1484504730_vis.json"
        self._run_json_equal_file(url, "results_co_vims_v1484504730_vis_metadata.json")

    def test__results_contents_co_vims_v1484504730_vis_files(self):
        "[test_results_contents.py] co-vims-v1484504730_vis files"
        url = "/api/files/co-vims-v1484504730_vis.json"
        self._run_json_equal_file(url, "results_co_vims_v1484504730_vis_files.json")

    def test__results_contents_co_vims_v1484504730_vis_images(self):
        "[test_results_contents.py] co-vims-v1484504730_vis images"
        url = "/api/images.json?opusid=co-vims-v1484504730_vis"
        self._run_json_equal_file(url, "results_co_vims_v1484504730_vis_images.json")

    def test__results_contents_co_vims_v1484580518_vis_metadata(self):
        "[test_results_contents.py] co-vims-v1484580518_vis metadata"
        url = "/api/metadata/co-vims-v1484580518_vis.json"
        self._run_json_equal_file(url, "results_co_vims_v1484580518_vis_metadata.json")

    def test__results_contents_co_vims_v1484580518_vis_files(self):
        "[test_results_contents.py] co-vims-v1484580518_vis files"
        url = "/api/files/co-vims-v1484580518_vis.json"
        self._run_json_equal_file(url, "results_co_vims_v1484580518_vis_files.json")

    def test__results_contents_co_vims_v1484580518_vis_images(self):
        "[test_results_contents.py] co-vims-v1484580518_vis images"
        url = "/api/images.json?opusid=co-vims-v1484580518_vis"
        self._run_json_equal_file(url, "results_co_vims_v1484580518_vis_images.json")

    def test__results_contents_co_vims_v1484860325_ir_metadata(self):
        "[test_results_contents.py] co-vims-v1484860325_ir metadata"
        url = "/api/metadata/co-vims-v1484860325_ir.json"
        self._run_json_equal_file(url, "results_co_vims_v1484860325_ir_metadata.json")

    def test__results_contents_co_vims_v1484860325_ir_files(self):
        "[test_results_contents.py] co-vims-v1484860325_ir files"
        url = "/api/files/co-vims-v1484860325_ir.json"
        self._run_json_equal_file(url, "results_co_vims_v1484860325_ir_files.json")

    def test__results_contents_co_vims_v1484860325_ir_images(self):
        "[test_results_contents.py] co-vims-v1484860325_ir images"
        url = "/api/images.json?opusid=co-vims-v1484860325_ir"
        self._run_json_equal_file(url, "results_co_vims_v1484860325_ir_images.json")

    def test__results_contents_co_vims_v1485757341_ir_metadata(self):
        "[test_results_contents.py] co-vims-v1485757341_ir metadata"
        url = "/api/metadata/co-vims-v1485757341_ir.json"
        self._run_json_equal_file(url, "results_co_vims_v1485757341_ir_metadata.json")

    def test__results_contents_co_vims_v1485757341_ir_files(self):
        "[test_results_contents.py] co-vims-v1485757341_ir files"
        url = "/api/files/co-vims-v1485757341_ir.json"
        self._run_json_equal_file(url, "results_co_vims_v1485757341_ir_files.json")

    def test__results_contents_co_vims_v1485757341_ir_images(self):
        "[test_results_contents.py] co-vims-v1485757341_ir images"
        url = "/api/images.json?opusid=co-vims-v1485757341_ir"
        self._run_json_equal_file(url, "results_co_vims_v1485757341_ir_images.json")

    def test__results_contents_co_vims_v1485803787_ir_metadata(self):
        "[test_results_contents.py] co-vims-v1485803787_ir metadata"
        url = "/api/metadata/co-vims-v1485803787_ir.json"
        self._run_json_equal_file(url, "results_co_vims_v1485803787_ir_metadata.json")

    def test__results_contents_co_vims_v1485803787_ir_files(self):
        "[test_results_contents.py] co-vims-v1485803787_ir files"
        url = "/api/files/co-vims-v1485803787_ir.json"
        self._run_json_equal_file(url, "results_co_vims_v1485803787_ir_files.json")

    def test__results_contents_co_vims_v1485803787_ir_images(self):
        "[test_results_contents.py] co-vims-v1485803787_ir images"
        url = "/api/images.json?opusid=co-vims-v1485803787_ir"
        self._run_json_equal_file(url, "results_co_vims_v1485803787_ir_images.json")

    def test__results_contents_co_vims_v1487262184_ir_metadata(self):
        "[test_results_contents.py] co-vims-v1487262184_ir metadata"
        url = "/api/metadata/co-vims-v1487262184_ir.json"
        self._run_json_equal_file(url, "results_co_vims_v1487262184_ir_metadata.json")

    def test__results_contents_co_vims_v1487262184_ir_files(self):
        "[test_results_contents.py] co-vims-v1487262184_ir files"
        url = "/api/files/co-vims-v1487262184_ir.json"
        self._run_json_equal_file(url, "results_co_vims_v1487262184_ir_files.json")

    def test__results_contents_co_vims_v1487262184_ir_images(self):
        "[test_results_contents.py] co-vims-v1487262184_ir images"
        url = "/api/images.json?opusid=co-vims-v1487262184_ir"
        self._run_json_equal_file(url, "results_co_vims_v1487262184_ir_images.json")

    def test__results_contents_co_vims_v1490874999_001_vis_metadata(self):
        "[test_results_contents.py] co-vims-v1490874999_001_vis metadata"
        url = "/api/metadata/co-vims-v1490874999_001_vis.json"
        self._run_json_equal_file(url, "results_co_vims_v1490874999_001_vis_metadata.json")

    def test__results_contents_co_vims_v1490874999_001_vis_files(self):
        "[test_results_contents.py] co-vims-v1490874999_001_vis files"
        url = "/api/files/co-vims-v1490874999_001_vis.json"
        self._run_json_equal_file(url, "results_co_vims_v1490874999_001_vis_files.json")

    def test__results_contents_co_vims_v1490874999_001_vis_images(self):
        "[test_results_contents.py] co-vims-v1490874999_001_vis images"
        url = "/api/images.json?opusid=co-vims-v1490874999_001_vis"
        self._run_json_equal_file(url, "results_co_vims_v1490874999_001_vis_images.json")

    def test__results_contents_go_ssi_c0347769100_metadata(self):
        "[test_results_contents.py] go-ssi-c0347769100 metadata"
        url = "/api/metadata/go-ssi-c0347769100.json"
        self._run_json_equal_file(url, "results_go_ssi_c0347769100_metadata.json")

    def test__results_contents_go_ssi_c0347769100_files(self):
        "[test_results_contents.py] go-ssi-c0347769100 files"
        url = "/api/files/go-ssi-c0347769100.json"
        self._run_json_equal_file(url, "results_go_ssi_c0347769100_files.json")

    def test__results_contents_go_ssi_c0347769100_images(self):
        "[test_results_contents.py] go-ssi-c0347769100 images"
        url = "/api/images.json?opusid=go-ssi-c0347769100"
        self._run_json_equal_file(url, "results_go_ssi_c0347769100_images.json")

    def test__results_contents_go_ssi_c0349673988_metadata(self):
        "[test_results_contents.py] go-ssi-c0349673988 metadata"
        url = "/api/metadata/go-ssi-c0349673988.json"
        self._run_json_equal_file(url, "results_go_ssi_c0349673988_metadata.json")

    def test__results_contents_go_ssi_c0349673988_files(self):
        "[test_results_contents.py] go-ssi-c0349673988 files"
        url = "/api/files/go-ssi-c0349673988.json"
        self._run_json_equal_file(url, "results_go_ssi_c0349673988_files.json")

    def test__results_contents_go_ssi_c0349673988_images(self):
        "[test_results_contents.py] go-ssi-c0349673988 images"
        url = "/api/images.json?opusid=go-ssi-c0349673988"
        self._run_json_equal_file(url, "results_go_ssi_c0349673988_images.json")

    def test__results_contents_go_ssi_c0349761213_metadata(self):
        "[test_results_contents.py] go-ssi-c0349761213 metadata"
        url = "/api/metadata/go-ssi-c0349761213.json"
        self._run_json_equal_file(url, "results_go_ssi_c0349761213_metadata.json")

    def test__results_contents_go_ssi_c0349761213_files(self):
        "[test_results_contents.py] go-ssi-c0349761213 files"
        url = "/api/files/go-ssi-c0349761213.json"
        self._run_json_equal_file(url, "results_go_ssi_c0349761213_files.json")

    def test__results_contents_go_ssi_c0349761213_images(self):
        "[test_results_contents.py] go-ssi-c0349761213 images"
        url = "/api/images.json?opusid=go-ssi-c0349761213"
        self._run_json_equal_file(url, "results_go_ssi_c0349761213_images.json")

    def test__results_contents_go_ssi_c0359986600_metadata(self):
        "[test_results_contents.py] go-ssi-c0359986600 metadata"
        url = "/api/metadata/go-ssi-c0359986600.json"
        self._run_json_equal_file(url, "results_go_ssi_c0359986600_metadata.json")

    def test__results_contents_go_ssi_c0359986600_files(self):
        "[test_results_contents.py] go-ssi-c0359986600 files"
        url = "/api/files/go-ssi-c0359986600.json"
        self._run_json_equal_file(url, "results_go_ssi_c0359986600_files.json")

    def test__results_contents_go_ssi_c0359986600_images(self):
        "[test_results_contents.py] go-ssi-c0359986600 images"
        url = "/api/images.json?opusid=go-ssi-c0359986600"
        self._run_json_equal_file(url, "results_go_ssi_c0359986600_images.json")

    def test__results_contents_go_ssi_c0368977800_metadata(self):
        "[test_results_contents.py] go-ssi-c0368977800 metadata"
        url = "/api/metadata/go-ssi-c0368977800.json"
        self._run_json_equal_file(url, "results_go_ssi_c0368977800_metadata.json")

    def test__results_contents_go_ssi_c0368977800_files(self):
        "[test_results_contents.py] go-ssi-c0368977800 files"
        url = "/api/files/go-ssi-c0368977800.json"
        self._run_json_equal_file(url, "results_go_ssi_c0368977800_files.json")

    def test__results_contents_go_ssi_c0368977800_images(self):
        "[test_results_contents.py] go-ssi-c0368977800 images"
        url = "/api/images.json?opusid=go-ssi-c0368977800"
        self._run_json_equal_file(url, "results_go_ssi_c0368977800_images.json")

    def test__results_contents_go_ssi_c0248807000_metadata(self):
        "[test_results_contents.py] go-ssi-c0248807000 metadata"
        url = "/api/metadata/go-ssi-c0248807000.json"
        self._run_json_equal_file(url, "results_go_ssi_c0248807000_metadata.json")

    def test__results_contents_go_ssi_c0248807000_files(self):
        "[test_results_contents.py] go-ssi-c0248807000 files"
        url = "/api/files/go-ssi-c0248807000.json"
        self._run_json_equal_file(url, "results_go_ssi_c0248807000_files.json")

    def test__results_contents_go_ssi_c0248807000_images(self):
        "[test_results_contents.py] go-ssi-c0248807000 images"
        url = "/api/images.json?opusid=go-ssi-c0248807000"
        self._run_json_equal_file(url, "results_go_ssi_c0248807000_images.json")

    def test__results_contents_go_ssi_c0202540045_metadata(self):
        "[test_results_contents.py] go-ssi-c0202540045 metadata"
        url = "/api/metadata/go-ssi-c0202540045.json"
        self._run_json_equal_file(url, "results_go_ssi_c0202540045_metadata.json")

    def test__results_contents_go_ssi_c0202540045_files(self):
        "[test_results_contents.py] go-ssi-c0202540045 files"
        url = "/api/files/go-ssi-c0202540045.json"
        self._run_json_equal_file(url, "results_go_ssi_c0202540045_files.json")

    def test__results_contents_go_ssi_c0202540045_images(self):
        "[test_results_contents.py] go-ssi-c0202540045 images"
        url = "/api/images.json?opusid=go-ssi-c0202540045"
        self._run_json_equal_file(url, "results_go_ssi_c0202540045_images.json")

    def test__results_contents_hst_05642_wfpc2_u2fi0c05t_metadata(self):
        "[test_results_contents.py] hst-05642-wfpc2-u2fi0c05t metadata"
        url = "/api/metadata/hst-05642-wfpc2-u2fi0c05t.json"
        self._run_json_equal_file(url, "results_hst_05642_wfpc2_u2fi0c05t_metadata.json")

    def test__results_contents_hst_05642_wfpc2_u2fi0c05t_files(self):
        "[test_results_contents.py] hst-05642-wfpc2-u2fi0c05t files"
        url = "/api/files/hst-05642-wfpc2-u2fi0c05t.json"
        self._run_json_equal_file(url, "results_hst_05642_wfpc2_u2fi0c05t_files.json")

    def test__results_contents_hst_05642_wfpc2_u2fi0c05t_images(self):
        "[test_results_contents.py] hst-05642-wfpc2-u2fi0c05t images"
        url = "/api/images.json?opusid=hst-05642-wfpc2-u2fi0c05t"
        self._run_json_equal_file(url, "results_hst_05642_wfpc2_u2fi0c05t_images.json")

    def test__results_contents_hst_05642_wfpc2_u2fi0o0bt_metadata(self):
        "[test_results_contents.py] hst-05642-wfpc2-u2fi0o0bt metadata"
        url = "/api/metadata/hst-05642-wfpc2-u2fi0o0bt.json"
        self._run_json_equal_file(url, "results_hst_05642_wfpc2_u2fi0o0bt_metadata.json")

    def test__results_contents_hst_05642_wfpc2_u2fi0o0bt_files(self):
        "[test_results_contents.py] hst-05642-wfpc2-u2fi0o0bt files"
        url = "/api/files/hst-05642-wfpc2-u2fi0o0bt.json"
        self._run_json_equal_file(url, "results_hst_05642_wfpc2_u2fi0o0bt_files.json")

    def test__results_contents_hst_05642_wfpc2_u2fi0o0bt_images(self):
        "[test_results_contents.py] hst-05642-wfpc2-u2fi0o0bt images"
        url = "/api/images.json?opusid=hst-05642-wfpc2-u2fi0o0bt"
        self._run_json_equal_file(url, "results_hst_05642_wfpc2_u2fi0o0bt_images.json")

    def test__results_contents_hst_05642_wfpc2_u2fi1901t_metadata(self):
        "[test_results_contents.py] hst-05642-wfpc2-u2fi1901t metadata"
        url = "/api/metadata/hst-05642-wfpc2-u2fi1901t.json"
        self._run_json_equal_file(url, "results_hst_05642_wfpc2_u2fi1901t_metadata.json")

    def test__results_contents_hst_05642_wfpc2_u2fi1901t_files(self):
        "[test_results_contents.py] hst-05642-wfpc2-u2fi1901t files"
        url = "/api/files/hst-05642-wfpc2-u2fi1901t.json"
        self._run_json_equal_file(url, "results_hst_05642_wfpc2_u2fi1901t_files.json")

    def test__results_contents_hst_05642_wfpc2_u2fi1901t_images(self):
        "[test_results_contents.py] hst-05642-wfpc2-u2fi1901t images"
        url = "/api/images.json?opusid=hst-05642-wfpc2-u2fi1901t"
        self._run_json_equal_file(url, "results_hst_05642_wfpc2_u2fi1901t_images.json")

    def test__results_contents_hst_07181_nicmos_n4uc01b0q_metadata(self):
        "[test_results_contents.py] hst-07181-nicmos-n4uc01b0q metadata"
        url = "/api/metadata/hst-07181-nicmos-n4uc01b0q.json"
        self._run_json_equal_file(url, "results_hst_07181_nicmos_n4uc01b0q_metadata.json")

    def test__results_contents_hst_07181_nicmos_n4uc01b0q_files(self):
        "[test_results_contents.py] hst-07181-nicmos-n4uc01b0q files"
        url = "/api/files/hst-07181-nicmos-n4uc01b0q.json"
        self._run_json_equal_file(url, "results_hst_07181_nicmos_n4uc01b0q_files.json")

    def test__results_contents_hst_07181_nicmos_n4uc01b0q_images(self):
        "[test_results_contents.py] hst-07181-nicmos-n4uc01b0q images"
        url = "/api/images.json?opusid=hst-07181-nicmos-n4uc01b0q"
        self._run_json_equal_file(url, "results_hst_07181_nicmos_n4uc01b0q_images.json")

    def test__results_contents_hst_07181_nicmos_n4uc01cjq_metadata(self):
        "[test_results_contents.py] hst-07181-nicmos-n4uc01cjq metadata"
        url = "/api/metadata/hst-07181-nicmos-n4uc01cjq.json"
        self._run_json_equal_file(url, "results_hst_07181_nicmos_n4uc01cjq_metadata.json")

    def test__results_contents_hst_07181_nicmos_n4uc01cjq_files(self):
        "[test_results_contents.py] hst-07181-nicmos-n4uc01cjq files"
        url = "/api/files/hst-07181-nicmos-n4uc01cjq.json"
        self._run_json_equal_file(url, "results_hst_07181_nicmos_n4uc01cjq_files.json")

    def test__results_contents_hst_07181_nicmos_n4uc01cjq_images(self):
        "[test_results_contents.py] hst-07181-nicmos-n4uc01cjq images"
        url = "/api/images.json?opusid=hst-07181-nicmos-n4uc01cjq"
        self._run_json_equal_file(url, "results_hst_07181_nicmos_n4uc01cjq_images.json")

    def test__results_contents_hst_07316_stis_o57h02joq_metadata(self):
        "[test_results_contents.py] hst-07316-stis-o57h02joq metadata"
        url = "/api/metadata/hst-07316-stis-o57h02joq.json"
        self._run_json_equal_file(url, "results_hst_07316_stis_o57h02joq_metadata.json")

    def test__results_contents_hst_07316_stis_o57h02joq_files(self):
        "[test_results_contents.py] hst-07316-stis-o57h02joq files"
        url = "/api/files/hst-07316-stis-o57h02joq.json"
        self._run_json_equal_file(url, "results_hst_07316_stis_o57h02joq_files.json")

    def test__results_contents_hst_07316_stis_o57h02joq_images(self):
        "[test_results_contents.py] hst-07316-stis-o57h02joq images"
        url = "/api/images.json?opusid=hst-07316-stis-o57h02joq"
        self._run_json_equal_file(url, "results_hst_07316_stis_o57h02joq_images.json")

    def test__results_contents_hst_07316_stis_o57h02010_metadata(self):
        "[test_results_contents.py] hst-07316-stis-o57h02010 metadata"
        url = "/api/metadata/hst-07316-stis-o57h02010.json"
        self._run_json_equal_file(url, "results_hst_07316_stis_o57h02010_metadata.json")

    def test__results_contents_hst_07316_stis_o57h02010_files(self):
        "[test_results_contents.py] hst-07316-stis-o57h02010 files"
        url = "/api/files/hst-07316-stis-o57h02010.json"
        self._run_json_equal_file(url, "results_hst_07316_stis_o57h02010_files.json")

    def test__results_contents_hst_07316_stis_o57h02010_images(self):
        "[test_results_contents.py] hst-07316-stis-o57h02010 images"
        url = "/api/images.json?opusid=hst-07316-stis-o57h02010"
        self._run_json_equal_file(url, "results_hst_07316_stis_o57h02010_images.json")

    def test__results_contents_hst_09975_acs_j8n460zvq_metadata(self):
        "[test_results_contents.py] hst-09975-acs-j8n460zvq metadata"
        url = "/api/metadata/hst-09975-acs-j8n460zvq.json"
        self._run_json_equal_file(url, "results_hst_09975_acs_j8n460zvq_metadata.json")

    def test__results_contents_hst_09975_acs_j8n460zvq_files(self):
        "[test_results_contents.py] hst-09975-acs-j8n460zvq files"
        url = "/api/files/hst-09975-acs-j8n460zvq.json"
        self._run_json_equal_file(url, "results_hst_09975_acs_j8n460zvq_files.json")

    def test__results_contents_hst_09975_acs_j8n460zvq_images(self):
        "[test_results_contents.py] hst-09975-acs-j8n460zvq images"
        url = "/api/images.json?opusid=hst-09975-acs-j8n460zvq"
        self._run_json_equal_file(url, "results_hst_09975_acs_j8n460zvq_images.json")

    def test__results_contents_hst_11085_acs_j9xe05011_metadata(self):
        "[test_results_contents.py] hst-11085-acs-j9xe05011 metadata"
        url = "/api/metadata/hst-11085-acs-j9xe05011.json"
        self._run_json_equal_file(url, "results_hst_11085_acs_j9xe05011_metadata.json")

    def test__results_contents_hst_11085_acs_j9xe05011_files(self):
        "[test_results_contents.py] hst-11085-acs-j9xe05011 files"
        url = "/api/files/hst-11085-acs-j9xe05011.json"
        self._run_json_equal_file(url, "results_hst_11085_acs_j9xe05011_files.json")

    def test__results_contents_hst_11085_acs_j9xe05011_images(self):
        "[test_results_contents.py] hst-11085-acs-j9xe05011 images"
        url = "/api/images.json?opusid=hst-11085-acs-j9xe05011"
        self._run_json_equal_file(url, "results_hst_11085_acs_j9xe05011_images.json")

    def test__results_contents_hst_11559_wfc3_ib4v22gxq_metadata(self):
        "[test_results_contents.py] hst-11559-wfc3-ib4v22gxq metadata"
        url = "/api/metadata/hst-11559-wfc3-ib4v22gxq.json"
        self._run_json_equal_file(url, "results_hst_11559_wfc3_ib4v22gxq_metadata.json")

    def test__results_contents_hst_11559_wfc3_ib4v22gxq_files(self):
        "[test_results_contents.py] hst-11559-wfc3-ib4v22gxq files"
        url = "/api/files/hst-11559-wfc3-ib4v22gxq.json"
        self._run_json_equal_file(url, "results_hst_11559_wfc3_ib4v22gxq_files.json")

    def test__results_contents_hst_11559_wfc3_ib4v22gxq_images(self):
        "[test_results_contents.py] hst-11559-wfc3-ib4v22gxq images"
        url = "/api/images.json?opusid=hst-11559-wfc3-ib4v22gxq"
        self._run_json_equal_file(url, "results_hst_11559_wfc3_ib4v22gxq_images.json")

    def test__results_contents_hst_13667_wfc3_icok28ihq_metadata(self):
        "[test_results_contents.py] hst-13667-wfc3-icok28ihq metadata"
        url = "/api/metadata/hst-13667-wfc3-icok28ihq.json"
        self._run_json_equal_file(url, "results_hst_13667_wfc3_icok28ihq_metadata.json")

    def test__results_contents_hst_13667_wfc3_icok28ihq_files(self):
        "[test_results_contents.py] hst-13667-wfc3-icok28ihq files"
        url = "/api/files/hst-13667-wfc3-icok28ihq.json"
        self._run_json_equal_file(url, "results_hst_13667_wfc3_icok28ihq_files.json")

    def test__results_contents_hst_13667_wfc3_icok28ihq_images(self):
        "[test_results_contents.py] hst-13667-wfc3-icok28ihq images"
        url = "/api/images.json?opusid=hst-13667-wfc3-icok28ihq"
        self._run_json_equal_file(url, "results_hst_13667_wfc3_icok28ihq_images.json")

    def test__results_contents_hst_13667_wfc3_icok11rgq_metadata(self):
        "[test_results_contents.py] hst-13667-wfc3-icok11rgq metadata"
        url = "/api/metadata/hst-13667-wfc3-icok11rgq.json"
        self._run_json_equal_file(url, "results_hst_13667_wfc3_icok11rgq_metadata.json")

    def test__results_contents_hst_13667_wfc3_icok11rgq_files(self):
        "[test_results_contents.py] hst-13667-wfc3-icok11rgq files"
        url = "/api/files/hst-13667-wfc3-icok11rgq.json"
        self._run_json_equal_file(url, "results_hst_13667_wfc3_icok11rgq_files.json")

    def test__results_contents_hst_13667_wfc3_icok11rgq_images(self):
        "[test_results_contents.py] hst-13667-wfc3-icok11rgq images"
        url = "/api/images.json?opusid=hst-13667-wfc3-icok11rgq"
        self._run_json_equal_file(url, "results_hst_13667_wfc3_icok11rgq_images.json")

    def test__results_contents_nh_lorri_lor_0299075349_metadata(self):
        "[test_results_contents.py] nh-lorri-lor_0299075349 metadata"
        url = "/api/metadata/nh-lorri-lor_0299075349.json"
        self._run_json_equal_file(url, "results_nh_lorri_lor_0299075349_metadata.json")

    def test__results_contents_nh_lorri_lor_0299075349_files(self):
        "[test_results_contents.py] nh-lorri-lor_0299075349 files"
        url = "/api/files/nh-lorri-lor_0299075349.json"
        self._run_json_equal_file(url, "results_nh_lorri_lor_0299075349_files.json")

    def test__results_contents_nh_lorri_lor_0299075349_images(self):
        "[test_results_contents.py] nh-lorri-lor_0299075349 images"
        url = "/api/images.json?opusid=nh-lorri-lor_0299075349"
        self._run_json_equal_file(url, "results_nh_lorri_lor_0299075349_images.json")

    def test__results_contents_nh_lorri_lor_0329817268_metadata(self):
        "[test_results_contents.py] nh-lorri-lor_0329817268 metadata"
        url = "/api/metadata/nh-lorri-lor_0329817268.json"
        self._run_json_equal_file(url, "results_nh_lorri_lor_0329817268_metadata.json")

    def test__results_contents_nh_lorri_lor_0329817268_files(self):
        "[test_results_contents.py] nh-lorri-lor_0329817268 files"
        url = "/api/files/nh-lorri-lor_0329817268.json"
        self._run_json_equal_file(url, "results_nh_lorri_lor_0329817268_files.json")

    def test__results_contents_nh_lorri_lor_0329817268_images(self):
        "[test_results_contents.py] nh-lorri-lor_0329817268 images"
        url = "/api/images.json?opusid=nh-lorri-lor_0329817268"
        self._run_json_equal_file(url, "results_nh_lorri_lor_0329817268_images.json")

    def test__results_contents_nh_lorri_lor_0330787458_metadata(self):
        "[test_results_contents.py] nh-lorri-lor_0330787458 metadata"
        url = "/api/metadata/nh-lorri-lor_0330787458.json"
        self._run_json_equal_file(url, "results_nh_lorri_lor_0330787458_metadata.json")

    def test__results_contents_nh_lorri_lor_0330787458_files(self):
        "[test_results_contents.py] nh-lorri-lor_0330787458 files"
        url = "/api/files/nh-lorri-lor_0330787458.json"
        self._run_json_equal_file(url, "results_nh_lorri_lor_0330787458_files.json")

    def test__results_contents_nh_lorri_lor_0330787458_images(self):
        "[test_results_contents.py] nh-lorri-lor_0330787458 images"
        url = "/api/images.json?opusid=nh-lorri-lor_0330787458"
        self._run_json_equal_file(url, "results_nh_lorri_lor_0330787458_images.json")

    def test__results_contents_nh_mvic_mc0_0032528036_metadata(self):
        "[test_results_contents.py] nh-mvic-mc0_0032528036 metadata"
        url = "/api/metadata/nh-mvic-mc0_0032528036.json"
        self._run_json_equal_file(url, "results_nh_mvic_mc0_0032528036_metadata.json")

    def test__results_contents_nh_mvic_mc0_0032528036_files(self):
        "[test_results_contents.py] nh-mvic-mc0_0032528036 files"
        url = "/api/files/nh-mvic-mc0_0032528036.json"
        self._run_json_equal_file(url, "results_nh_mvic_mc0_0032528036_files.json")

    def test__results_contents_nh_mvic_mc0_0032528036_images(self):
        "[test_results_contents.py] nh-mvic-mc0_0032528036 images"
        url = "/api/images.json?opusid=nh-mvic-mc0_0032528036"
        self._run_json_equal_file(url, "results_nh_mvic_mc0_0032528036_images.json")

    def test__results_contents_nh_mvic_mc1_0005261846_metadata(self):
        "[test_results_contents.py] nh-mvic-mc1_0005261846 metadata"
        url = "/api/metadata/nh-mvic-mc1_0005261846.json"
        self._run_json_equal_file(url, "results_nh_mvic_mc1_0005261846_metadata.json")

    def test__results_contents_nh_mvic_mc1_0005261846_files(self):
        "[test_results_contents.py] nh-mvic-mc1_0005261846 files"
        url = "/api/files/nh-mvic-mc1_0005261846.json"
        self._run_json_equal_file(url, "results_nh_mvic_mc1_0005261846_files.json")

    def test__results_contents_nh_mvic_mc1_0005261846_images(self):
        "[test_results_contents.py] nh-mvic-mc1_0005261846 images"
        url = "/api/images.json?opusid=nh-mvic-mc1_0005261846"
        self._run_json_equal_file(url, "results_nh_mvic_mc1_0005261846_images.json")

    def test__results_contents_nh_mvic_mp1_0012448104_metadata(self):
        "[test_results_contents.py] nh-mvic-mp1_0012448104 metadata"
        url = "/api/metadata/nh-mvic-mp1_0012448104.json"
        self._run_json_equal_file(url, "results_nh_mvic_mp1_0012448104_metadata.json")

    def test__results_contents_nh_mvic_mp1_0012448104_files(self):
        "[test_results_contents.py] nh-mvic-mp1_0012448104 files"
        url = "/api/files/nh-mvic-mp1_0012448104.json"
        self._run_json_equal_file(url, "results_nh_mvic_mp1_0012448104_files.json")

    def test__results_contents_nh_mvic_mp1_0012448104_images(self):
        "[test_results_contents.py] nh-mvic-mp1_0012448104 images"
        url = "/api/images.json?opusid=nh-mvic-mp1_0012448104"
        self._run_json_equal_file(url, "results_nh_mvic_mp1_0012448104_images.json")

    def test__results_contents_vg_iss_2_s_c4360353_metadata(self):
        "[test_results_contents.py] vg-iss-2-s-c4360353 metadata"
        url = "/api/metadata/vg-iss-2-s-c4360353.json"
        self._run_json_equal_file(url, "results_vg_iss_2_s_c4360353_metadata.json")

    def test__results_contents_vg_iss_2_s_c4360353_files(self):
        "[test_results_contents.py] vg-iss-2-s-c4360353 files"
        url = "/api/files/vg-iss-2-s-c4360353.json"
        self._run_json_equal_file(url, "results_vg_iss_2_s_c4360353_files.json")

    def test__results_contents_vg_iss_2_s_c4360353_images(self):
        "[test_results_contents.py] vg-iss-2-s-c4360353 images"
        url = "/api/images.json?opusid=vg-iss-2-s-c4360353"
        self._run_json_equal_file(url, "results_vg_iss_2_s_c4360353_images.json")

    def test__results_contents_mcd2m7_iirar_occ_1989_184_28sgr_i_metadata(self):
        "[test_results_contents.py] mcd2m7-iirar-occ-1989-184-28sgr-i metadata"
        url = "/api/metadata/mcd2m7-iirar-occ-1989-184-28sgr-i.json"
        self._run_json_equal_file(url, "results_mcd2m7_iirar_occ_1989_184_28sgr_i_metadata.json")

    def test__results_contents_mcd2m7_iirar_occ_1989_184_28sgr_i_files(self):
        "[test_results_contents.py] mcd2m7-iirar-occ-1989-184-28sgr-i files"
        url = "/api/files/mcd2m7-iirar-occ-1989-184-28sgr-i.json"
        self._run_json_equal_file(url, "results_mcd2m7_iirar_occ_1989_184_28sgr_i_files.json")

    def test__results_contents_mcd2m7_iirar_occ_1989_184_28sgr_i_images(self):
        "[test_results_contents.py] mcd2m7-iirar-occ-1989-184-28sgr-i images"
        url = "/api/images.json?opusid=mcd2m7-iirar-occ-1989-184-28sgr-i"
        self._run_json_equal_file(url, "results_mcd2m7_iirar_occ_1989_184_28sgr_i_images.json")

    def test__results_contents_esosil1m04_apph_occ_1989_184_28sgr_e_metadata(self):
        "[test_results_contents.py] esosil1m04-apph-occ-1989-184-28sgr-e metadata"
        url = "/api/metadata/esosil1m04-apph-occ-1989-184-28sgr-e.json"
        self._run_json_equal_file(url, "results_esosil1m04_apph_occ_1989_184_28sgr_e_metadata.json")

    def test__results_contents_esosil1m04_apph_occ_1989_184_28sgr_e_files(self):
        "[test_results_contents.py] esosil1m04-apph-occ-1989-184-28sgr-e files"
        url = "/api/files/esosil1m04-apph-occ-1989-184-28sgr-e.json"
        self._run_json_equal_file(url, "results_esosil1m04_apph_occ_1989_184_28sgr_e_files.json")

    def test__results_contents_esosil1m04_apph_occ_1989_184_28sgr_e_images(self):
        "[test_results_contents.py] esosil1m04-apph-occ-1989-184-28sgr-e images"
        url = "/api/images.json?opusid=esosil1m04-apph-occ-1989-184-28sgr-e"
        self._run_json_equal_file(url, "results_esosil1m04_apph_occ_1989_184_28sgr_e_images.json")

    def test__results_contents_lick1m_ccdc_occ_1989_184_28sgr_i_metadata(self):
        "[test_results_contents.py] lick1m-ccdc-occ-1989-184-28sgr-i metadata"
        url = "/api/metadata/lick1m-ccdc-occ-1989-184-28sgr-i.json"
        self._run_json_equal_file(url, "results_lick1m_ccdc_occ_1989_184_28sgr_i_metadata.json")

    def test__results_contents_lick1m_ccdc_occ_1989_184_28sgr_i_files(self):
        "[test_results_contents.py] lick1m-ccdc-occ-1989-184-28sgr-i files"
        url = "/api/files/lick1m-ccdc-occ-1989-184-28sgr-i.json"
        self._run_json_equal_file(url, "results_lick1m_ccdc_occ_1989_184_28sgr_i_files.json")

    def test__results_contents_lick1m_ccdc_occ_1989_184_28sgr_i_images(self):
        "[test_results_contents.py] lick1m-ccdc-occ-1989-184-28sgr-i images"
        url = "/api/images.json?opusid=lick1m-ccdc-occ-1989-184-28sgr-i"
        self._run_json_equal_file(url, "results_lick1m_ccdc_occ_1989_184_28sgr_i_images.json")

    def test__results_contents_co_rss_occ_2005_123_rev007_k26_i_metadata(self):
        "[test_results_contents.py] co-rss-occ-2005-123-rev007-k26-i metadata"
        url = "/api/metadata/co-rss-occ-2005-123-rev007-k26-i.json"
        self._run_json_equal_file(url, "results_co_rss_occ_2005_123_rev007_k26_i_metadata.json")

    def test__results_contents_co_rss_occ_2005_123_rev007_k26_i_files(self):
        "[test_results_contents.py] co-rss-occ-2005-123-rev007-k26-i files"
        url = "/api/files/co-rss-occ-2005-123-rev007-k26-i.json"
        self._run_json_equal_file(url, "results_co_rss_occ_2005_123_rev007_k26_i_files.json")

    def test__results_contents_co_rss_occ_2005_123_rev007_k26_i_images(self):
        "[test_results_contents.py] co-rss-occ-2005-123-rev007-k26-i images"
        url = "/api/images.json?opusid=co-rss-occ-2005-123-rev007-k26-i"
        self._run_json_equal_file(url, "results_co_rss_occ_2005_123_rev007_k26_i_images.json")

    def test__results_contents_co_rss_occ_2008_217_rev079c_s63_i_metadata(self):
        "[test_results_contents.py] co-rss-occ-2008-217-rev079c-s63-i metadata"
        url = "/api/metadata/co-rss-occ-2008-217-rev079c-s63-i.json"
        self._run_json_equal_file(url, "results_co_rss_occ_2008_217_rev079c_s63_i_metadata.json")

    def test__results_contents_co_rss_occ_2008_217_rev079c_s63_i_files(self):
        "[test_results_contents.py] co-rss-occ-2008-217-rev079c-s63-i files"
        url = "/api/files/co-rss-occ-2008-217-rev079c-s63-i.json"
        self._run_json_equal_file(url, "results_co_rss_occ_2008_217_rev079c_s63_i_files.json")

    def test__results_contents_co_rss_occ_2008_217_rev079c_s63_i_images(self):
        "[test_results_contents.py] co-rss-occ-2008-217-rev079c-s63-i images"
        url = "/api/images.json?opusid=co-rss-occ-2008-217-rev079c-s63-i"
        self._run_json_equal_file(url, "results_co_rss_occ_2008_217_rev079c_s63_i_images.json")

    def test__results_contents_co_rss_occ_2010_170_rev133_x34_e_metadata(self):
        "[test_results_contents.py] co-rss-occ-2010-170-rev133-x34-e metadata"
        url = "/api/metadata/co-rss-occ-2010-170-rev133-x34-e.json"
        self._run_json_equal_file(url, "results_co_rss_occ_2010_170_rev133_x34_e_metadata.json")

    def test__results_contents_co_rss_occ_2010_170_rev133_x34_e_files(self):
        "[test_results_contents.py] co-rss-occ-2010-170-rev133-x34-e files"
        url = "/api/files/co-rss-occ-2010-170-rev133-x34-e.json"
        self._run_json_equal_file(url, "results_co_rss_occ_2010_170_rev133_x34_e_files.json")

    def test__results_contents_co_rss_occ_2010_170_rev133_x34_e_images(self):
        "[test_results_contents.py] co-rss-occ-2010-170-rev133-x34-e images"
        url = "/api/images.json?opusid=co-rss-occ-2010-170-rev133-x34-e"
        self._run_json_equal_file(url, "results_co_rss_occ_2010_170_rev133_x34_e_images.json")

    def test__results_contents_co_uvis_occ_2005_139_126tau_e_metadata(self):
        "[test_results_contents.py] co-uvis-occ-2005-139-126tau-e metadata"
        url = "/api/metadata/co-uvis-occ-2005-139-126tau-e.json"
        self._run_json_equal_file(url, "results_co_uvis_occ_2005_139_126tau_e_metadata.json")

    def test__results_contents_co_uvis_occ_2005_139_126tau_e_files(self):
        "[test_results_contents.py] co-uvis-occ-2005-139-126tau-e files"
        url = "/api/files/co-uvis-occ-2005-139-126tau-e.json"
        self._run_json_equal_file(url, "results_co_uvis_occ_2005_139_126tau_e_files.json")

    def test__results_contents_co_uvis_occ_2005_139_126tau_e_images(self):
        "[test_results_contents.py] co-uvis-occ-2005-139-126tau-e images"
        url = "/api/images.json?opusid=co-uvis-occ-2005-139-126tau-e"
        self._run_json_equal_file(url, "results_co_uvis_occ_2005_139_126tau_e_images.json")

    def test__results_contents_co_uvis_occ_2005_175_126tau_i_metadata(self):
        "[test_results_contents.py] co-uvis-occ-2005-175-126tau-i metadata"
        url = "/api/metadata/co-uvis-occ-2005-175-126tau-i.json"
        self._run_json_equal_file(url, "results_co_uvis_occ_2005_175_126tau_i_metadata.json")

    def test__results_contents_co_uvis_occ_2005_175_126tau_i_files(self):
        "[test_results_contents.py] co-uvis-occ-2005-175-126tau-i files"
        url = "/api/files/co-uvis-occ-2005-175-126tau-i.json"
        self._run_json_equal_file(url, "results_co_uvis_occ_2005_175_126tau_i_files.json")

    def test__results_contents_co_uvis_occ_2005_175_126tau_i_images(self):
        "[test_results_contents.py] co-uvis-occ-2005-175-126tau-i images"
        url = "/api/images.json?opusid=co-uvis-occ-2005-175-126tau-i"
        self._run_json_equal_file(url, "results_co_uvis_occ_2005_175_126tau_i_images.json")

    def test__results_contents_co_uvis_occ_2009_015_gamcas_e_metadata(self):
        "[test_results_contents.py] co-uvis-occ-2009-015-gamcas-e metadata"
        url = "/api/metadata/co-uvis-occ-2009-015-gamcas-e.json"
        self._run_json_equal_file(url, "results_co_uvis_occ_2009_015_gamcas_e_metadata.json")

    def test__results_contents_co_uvis_occ_2009_015_gamcas_e_files(self):
        "[test_results_contents.py] co-uvis-occ-2009-015-gamcas-e files"
        url = "/api/files/co-uvis-occ-2009-015-gamcas-e.json"
        self._run_json_equal_file(url, "results_co_uvis_occ_2009_015_gamcas_e_files.json")

    def test__results_contents_co_uvis_occ_2009_015_gamcas_e_images(self):
        "[test_results_contents.py] co-uvis-occ-2009-015-gamcas-e images"
        url = "/api/images.json?opusid=co-uvis-occ-2009-015-gamcas-e"
        self._run_json_equal_file(url, "results_co_uvis_occ_2009_015_gamcas_e_images.json")

    def test__results_contents_co_uvis_occ_2009_062_thehya_e_metadata(self):
        "[test_results_contents.py] co-uvis-occ-2009-062-thehya-e metadata"
        url = "/api/metadata/co-uvis-occ-2009-062-thehya-e.json"
        self._run_json_equal_file(url, "results_co_uvis_occ_2009_062_thehya_e_metadata.json")

    def test__results_contents_co_uvis_occ_2009_062_thehya_e_files(self):
        "[test_results_contents.py] co-uvis-occ-2009-062-thehya-e files"
        url = "/api/files/co-uvis-occ-2009-062-thehya-e.json"
        self._run_json_equal_file(url, "results_co_uvis_occ_2009_062_thehya_e_files.json")

    def test__results_contents_co_uvis_occ_2009_062_thehya_e_images(self):
        "[test_results_contents.py] co-uvis-occ-2009-062-thehya-e images"
        url = "/api/images.json?opusid=co-uvis-occ-2009-062-thehya-e"
        self._run_json_equal_file(url, "results_co_uvis_occ_2009_062_thehya_e_images.json")

    def test__results_contents_co_vims_occ_2006_204_alpori_i_metadata(self):
        "[test_results_contents.py] co-vims-occ-2006-204-alpori-i metadata"
        url = "/api/metadata/co-vims-occ-2006-204-alpori-i.json"
        self._run_json_equal_file(url, "results_co_vims_occ_2006_204_alpori_i_metadata.json")

    def test__results_contents_co_vims_occ_2006_204_alpori_i_files(self):
        "[test_results_contents.py] co-vims-occ-2006-204-alpori-i files"
        url = "/api/files/co-vims-occ-2006-204-alpori-i.json"
        self._run_json_equal_file(url, "results_co_vims_occ_2006_204_alpori_i_files.json")

    def test__results_contents_co_vims_occ_2006_204_alpori_i_images(self):
        "[test_results_contents.py] co-vims-occ-2006-204-alpori-i images"
        url = "/api/images.json?opusid=co-vims-occ-2006-204-alpori-i"
        self._run_json_equal_file(url, "results_co_vims_occ_2006_204_alpori_i_images.json")

    def test__results_contents_co_vims_occ_2014_175_l2pup_e_metadata(self):
        "[test_results_contents.py] co-vims-occ-2014-175-l2pup-e metadata"
        url = "/api/metadata/co-vims-occ-2014-175-l2pup-e.json"
        self._run_json_equal_file(url, "results_co_vims_occ_2014_175_l2pup_e_metadata.json")

    def test__results_contents_co_vims_occ_2014_175_l2pup_e_files(self):
        "[test_results_contents.py] co-vims-occ-2014-175-l2pup-e files"
        url = "/api/files/co-vims-occ-2014-175-l2pup-e.json"
        self._run_json_equal_file(url, "results_co_vims_occ_2014_175_l2pup_e_files.json")

    def test__results_contents_co_vims_occ_2014_175_l2pup_e_images(self):
        "[test_results_contents.py] co-vims-occ-2014-175-l2pup-e images"
        url = "/api/images.json?opusid=co-vims-occ-2014-175-l2pup-e"
        self._run_json_equal_file(url, "results_co_vims_occ_2014_175_l2pup_e_images.json")

    def test__results_contents_vg_pps_2_s_occ_1981_238_delsco_e_metadata(self):
        "[test_results_contents.py] vg-pps-2-s-occ-1981-238-delsco-e metadata"
        url = "/api/metadata/vg-pps-2-s-occ-1981-238-delsco-e.json"
        self._run_json_equal_file(url, "results_vg_pps_2_s_occ_1981_238_delsco_e_metadata.json")

    def test__results_contents_vg_pps_2_s_occ_1981_238_delsco_e_files(self):
        "[test_results_contents.py] vg-pps-2-s-occ-1981-238-delsco-e files"
        url = "/api/files/vg-pps-2-s-occ-1981-238-delsco-e.json"
        self._run_json_equal_file(url, "results_vg_pps_2_s_occ_1981_238_delsco_e_files.json")

    def test__results_contents_vg_pps_2_s_occ_1981_238_delsco_e_images(self):
        "[test_results_contents.py] vg-pps-2-s-occ-1981-238-delsco-e images"
        url = "/api/images.json?opusid=vg-pps-2-s-occ-1981-238-delsco-e"
        self._run_json_equal_file(url, "results_vg_pps_2_s_occ_1981_238_delsco_e_images.json")

    def test__results_contents_vg_pps_2_u_occ_1986_024_sigsgr_delta_e_metadata(self):
        "[test_results_contents.py] vg-pps-2-u-occ-1986-024-sigsgr-delta-e metadata"
        url = "/api/metadata/vg-pps-2-u-occ-1986-024-sigsgr-delta-e.json"
        self._run_json_equal_file(url, "results_vg_pps_2_u_occ_1986_024_sigsgr_delta_e_metadata.json")

    def test__results_contents_vg_pps_2_u_occ_1986_024_sigsgr_delta_e_files(self):
        "[test_results_contents.py] vg-pps-2-u-occ-1986-024-sigsgr-delta-e files"
        url = "/api/files/vg-pps-2-u-occ-1986-024-sigsgr-delta-e.json"
        self._run_json_equal_file(url, "results_vg_pps_2_u_occ_1986_024_sigsgr_delta_e_files.json")

    def test__results_contents_vg_pps_2_u_occ_1986_024_sigsgr_delta_e_images(self):
        "[test_results_contents.py] vg-pps-2-u-occ-1986-024-sigsgr-delta-e images"
        url = "/api/images.json?opusid=vg-pps-2-u-occ-1986-024-sigsgr-delta-e"
        self._run_json_equal_file(url, "results_vg_pps_2_u_occ_1986_024_sigsgr_delta_e_images.json")

    def test__results_contents_vg_pps_2_n_occ_1989_236_sigsgr_i_metadata(self):
        "[test_results_contents.py] vg-pps-2-n-occ-1989-236-sigsgr-i metadata"
        url = "/api/metadata/vg-pps-2-n-occ-1989-236-sigsgr-i.json"
        self._run_json_equal_file(url, "results_vg_pps_2_n_occ_1989_236_sigsgr_i_metadata.json")

    def test__results_contents_vg_pps_2_n_occ_1989_236_sigsgr_i_files(self):
        "[test_results_contents.py] vg-pps-2-n-occ-1989-236-sigsgr-i files"
        url = "/api/files/vg-pps-2-n-occ-1989-236-sigsgr-i.json"
        self._run_json_equal_file(url, "results_vg_pps_2_n_occ_1989_236_sigsgr_i_files.json")

    def test__results_contents_vg_pps_2_n_occ_1989_236_sigsgr_i_images(self):
        "[test_results_contents.py] vg-pps-2-n-occ-1989-236-sigsgr-i images"
        url = "/api/images.json?opusid=vg-pps-2-n-occ-1989-236-sigsgr-i"
        self._run_json_equal_file(url, "results_vg_pps_2_n_occ_1989_236_sigsgr_i_images.json")

    def test__results_contents_vg_uvs_1_s_occ_1980_317_iother_e_metadata(self):
        "[test_results_contents.py] vg-uvs-1-s-occ-1980-317-iother-e metadata"
        url = "/api/metadata/vg-uvs-1-s-occ-1980-317-iother-e.json"
        self._run_json_equal_file(url, "results_vg_uvs_1_s_occ_1980_317_iother_e_metadata.json")

    def test__results_contents_vg_uvs_1_s_occ_1980_317_iother_e_files(self):
        "[test_results_contents.py] vg-uvs-1-s-occ-1980-317-iother-e files"
        url = "/api/files/vg-uvs-1-s-occ-1980-317-iother-e.json"
        self._run_json_equal_file(url, "results_vg_uvs_1_s_occ_1980_317_iother_e_files.json")

    def test__results_contents_vg_uvs_1_s_occ_1980_317_iother_e_images(self):
        "[test_results_contents.py] vg-uvs-1-s-occ-1980-317-iother-e images"
        url = "/api/images.json?opusid=vg-uvs-1-s-occ-1980-317-iother-e"
        self._run_json_equal_file(url, "results_vg_uvs_1_s_occ_1980_317_iother_e_images.json")

    def test__results_contents_vg_rss_2_u_occ_1986_024_s43_four_i_metadata(self):
        "[test_results_contents.py] vg-rss-2-u-occ-1986-024-s43-four-i metadata"
        url = "/api/metadata/vg-rss-2-u-occ-1986-024-s43-four-i.json"
        self._run_json_equal_file(url, "results_vg_rss_2_u_occ_1986_024_s43_four_i_metadata.json")

    def test__results_contents_vg_rss_2_u_occ_1986_024_s43_four_i_files(self):
        "[test_results_contents.py] vg-rss-2-u-occ-1986-024-s43-four-i files"
        url = "/api/files/vg-rss-2-u-occ-1986-024-s43-four-i.json"
        self._run_json_equal_file(url, "results_vg_rss_2_u_occ_1986_024_s43_four_i_files.json")

    def test__results_contents_vg_rss_2_u_occ_1986_024_s43_four_i_images(self):
        "[test_results_contents.py] vg-rss-2-u-occ-1986-024-s43-four-i images"
        url = "/api/images.json?opusid=vg-rss-2-u-occ-1986-024-s43-four-i"
        self._run_json_equal_file(url, "results_vg_rss_2_u_occ_1986_024_s43_four_i_images.json")

    def test__results_contents_vg_uvs_2_n_occ_1989_236_sigsgr_i_metadata(self):
        "[test_results_contents.py] vg-uvs-2-n-occ-1989-236-sigsgr-i metadata"
        url = "/api/metadata/vg-uvs-2-n-occ-1989-236-sigsgr-i.json"
        self._run_json_equal_file(url, "results_vg_uvs_2_n_occ_1989_236_sigsgr_i_metadata.json")

    def test__results_contents_vg_uvs_2_n_occ_1989_236_sigsgr_i_files(self):
        "[test_results_contents.py] vg-uvs-2-n-occ-1989-236-sigsgr-i files"
        url = "/api/files/vg-uvs-2-n-occ-1989-236-sigsgr-i.json"
        self._run_json_equal_file(url, "results_vg_uvs_2_n_occ_1989_236_sigsgr_i_files.json")

    def test__results_contents_vg_uvs_2_n_occ_1989_236_sigsgr_i_images(self):
        "[test_results_contents.py] vg-uvs-2-n-occ-1989-236-sigsgr-i images"
        url = "/api/images.json?opusid=vg-uvs-2-n-occ-1989-236-sigsgr-i"
        self._run_json_equal_file(url, "results_vg_uvs_2_n_occ_1989_236_sigsgr_i_images.json")

    def test__results_contents_vg_iss_2_s_prof_metadata(self):
        "[test_results_contents.py] vg-iss-2-s-prof metadata"
        url = "/api/metadata/vg-iss-2-s-prof.json"
        self._run_json_equal_file(url, "results_vg_iss_2_s_prof_metadata.json")

    def test__results_contents_vg_iss_2_s_prof_files(self):
        "[test_results_contents.py] vg-iss-2-s-prof files"
        url = "/api/files/vg-iss-2-s-prof.json"
        self._run_json_equal_file(url, "results_vg_iss_2_s_prof_files.json")

    def test__results_contents_vg_iss_2_s_prof_images(self):
        "[test_results_contents.py] vg-iss-2-s-prof images"
        url = "/api/images.json?opusid=vg-iss-2-s-prof"
        self._run_json_equal_file(url, "results_vg_iss_2_s_prof_images.json")

    def test__results_contents_kao0m91_vis_occ_1977_069_u0_ringpl_i_metadata(self):
        "[test_results_contents.py] kao0m91-vis-occ-1977-069-u0-ringpl-i metadata"
        url = "/api/metadata/kao0m91-vis-occ-1977-069-u0-ringpl-i.json"
        self._run_json_equal_file(url, "results_kao0m91_vis_occ_1977_069_u0_ringpl_i_metadata.json")

    def test__results_contents_kao0m91_vis_occ_1977_069_u0_ringpl_i_files(self):
        "[test_results_contents.py] kao0m91-vis-occ-1977-069-u0-ringpl-i files"
        url = "/api/files/kao0m91-vis-occ-1977-069-u0-ringpl-i.json"
        self._run_json_equal_file(url, "results_kao0m91_vis_occ_1977_069_u0_ringpl_i_files.json")

    def test__results_contents_kao0m91_vis_occ_1977_069_u0_ringpl_i_images(self):
        "[test_results_contents.py] kao0m91-vis-occ-1977-069-u0-ringpl-i images"
        url = "/api/images.json?opusid=kao0m91-vis-occ-1977-069-u0-ringpl-i"
        self._run_json_equal_file(url, "results_kao0m91_vis_occ_1977_069_u0_ringpl_i_images.json")

    def test__results_contents_kao0m91_vis_occ_1977_069_u0_uranus_e_metadata(self):
        "[test_results_contents.py] kao0m91-vis-occ-1977-069-u0-uranus-e metadata"
        url = "/api/metadata/kao0m91-vis-occ-1977-069-u0-uranus-e.json"
        self._run_json_equal_file(url, "results_kao0m91_vis_occ_1977_069_u0_uranus_e_metadata.json")

    def test__results_contents_kao0m91_vis_occ_1977_069_u0_uranus_e_files(self):
        "[test_results_contents.py] kao0m91-vis-occ-1977-069-u0-uranus-e files"
        url = "/api/files/kao0m91-vis-occ-1977-069-u0-uranus-e.json"
        self._run_json_equal_file(url, "results_kao0m91_vis_occ_1977_069_u0_uranus_e_files.json")

    def test__results_contents_kao0m91_vis_occ_1977_069_u0_uranus_e_images(self):
        "[test_results_contents.py] kao0m91-vis-occ-1977-069-u0-uranus-e images"
        url = "/api/images.json?opusid=kao0m91-vis-occ-1977-069-u0-uranus-e"
        self._run_json_equal_file(url, "results_kao0m91_vis_occ_1977_069_u0_uranus_e_images.json")

    def test__results_contents_kao0m91_vis_occ_1977_069_u0_eta_e_metadata(self):
        "[test_results_contents.py] kao0m91-vis-occ-1977-069-u0-eta-e metadata"
        url = "/api/metadata/kao0m91-vis-occ-1977-069-u0-eta-e.json"
        self._run_json_equal_file(url, "results_kao0m91_vis_occ_1977_069_u0_eta_e_metadata.json")

    def test__results_contents_kao0m91_vis_occ_1977_069_u0_eta_e_files(self):
        "[test_results_contents.py] kao0m91-vis-occ-1977-069-u0-eta-e files"
        url = "/api/files/kao0m91-vis-occ-1977-069-u0-eta-e.json"
        self._run_json_equal_file(url, "results_kao0m91_vis_occ_1977_069_u0_eta_e_files.json")

    def test__results_contents_kao0m91_vis_occ_1977_069_u0_eta_e_images(self):
        "[test_results_contents.py] kao0m91-vis-occ-1977-069-u0-eta-e images"
        url = "/api/images.json?opusid=kao0m91-vis-occ-1977-069-u0-eta-e"
        self._run_json_equal_file(url, "results_kao0m91_vis_occ_1977_069_u0_eta_e_images.json")
