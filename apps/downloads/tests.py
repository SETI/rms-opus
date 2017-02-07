"""
# downloads tests

"""
# from django.test import TestCase  removed because it deletes test table data after every test
from unittest import TestCase
from django.test.client import Client
from django.http import QueryDict
from search.views import *
from results.views import *

cursor = connection.cursor()

# downloads things
from downloads.views import *

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_COOKIE_NAME = 'opus-test-cookie'
settings.CACHE_BACKEND = 'dummy:///'


class downloadsTests(TestCase):

    c = Client()

    def test__get_download_info_browse_images_being_counted(self):
        ring_obs_ids = 'S_IMG_CO_ISS_1680806066_N'
        product_types=['CALIBRATED']
        files = getFiles(ring_obs_id=ring_obs_ids,fmt="raw", loc_type="path", product_types=product_types)
        product_types2=['RAW_IMAGE']
        files2 = getFiles(ring_obs_id=ring_obs_ids,fmt="raw", loc_type="path", product_types=product_types2)
        size1, file_count1 = get_download_info(files)
        size2, file_count2 = get_download_info(files2)
        self.assertNotEqual(size1, size2)

    # get_download_info(
    def test__get_download_info_COISS_CALIBRATED(self):
        ring_obs_ids = 'S_IMG_CO_ISS_1680806066_N'
        product_types = ['CALIBRATED']
        previews = 'none'
        files = getFiles(ring_obs_id=ring_obs_ids,fmt="raw",loc_type="path", product_types=product_types, previews=previews)
        print files
        size, file_count = get_download_info(files)
        print size, file_count
        self.assertEqual(size, 4226341)

    def test__get_download_info_COISS_RAW_IMAGE(self):
        ring_obs_ids = 'S_IMG_CO_ISS_1680806066_N'
        product_types = ['RAW_IMAGE']
        previews = 'none'
        files = getFiles(ring_obs_id=ring_obs_ids,fmt="raw",loc_type="path", product_types=product_types, previews=previews)
        size, file_count = get_download_info(files)
        print size, file_count
        self.assertEqual(size, 2131631)

    def test__get_download_info_COISS_both_products(self):
        ring_obs_ids = 'S_IMG_CO_ISS_1680806066_N'
        product_types = ['RAW_IMAGE','CALIBRATED']
        previews = 'none'
        files = getFiles(ring_obs_id=ring_obs_ids,fmt="raw",loc_type="path", product_types=product_types, previews=previews)
        size, file_count = get_download_info(files)
        print files
        print size, file_count
        self.assertEqual(size, 6357972)

    def test__get_download_info_COCIRS(self):
        ring_obs_ids = 'S_SPEC_CO_CIRS_1630456943_FP1'
        product_types = 'CALIBRATED_SPECTRUM'
        files = getFiles(ring_obs_id=ring_obs_ids,product_types=product_types,fmt="raw",loc_type="path")
        print files
        size, file_count = get_download_info(files)

    def test__get_download_info_COVIMS(self):
        ring_obs_ids = 'S_CUBE_CO_VIMS_1638723713_VIS'
        product_types = ['RAW_SPECTRAL_IMAGE_CUBE']
        previews = ['med']
        files = getFiles(ring_obs_id=ring_obs_ids,fmt="raw",loc_type="path", product_types=product_types, previews=previews)
        size, file_count = get_download_info(files)
        self.assertGreater(size, 0)

    def test__get_download_info_VGISS(self):
        ring_obs_ids = 'N_IMG_VG2_ISS_1120000_W'
        product_types = ['CALIBRATED_IMAGE']
        previews = ['small']
        files = getFiles(ring_obs_id=ring_obs_ids,fmt="raw",loc_type="path", product_types=product_types, previews=previews)
        size, file_count = get_download_info(files)
        self.assertGreater(size, 0)

    def test__get_download_info_empty_product_types(self):
        ring_obs_ids = 'S_IMG_CO_ISS_1680806066_N'
        product_types = ['none']
        previews = ['Full']
        files = getFiles(ring_obs_id=ring_obs_ids,fmt="raw",loc_type="path", product_types=product_types, previews=previews)
        print 'got from getFiles: '
        print files
        size, file_count = get_download_info(files)
        self.assertLess(size, 2250000)  # about 2 MB

    def test__get_file_path(self):
        f = settings.base_volumes_path + 'coiss_2xxx/coiss_2069/img.jpg'
        got = get_file_path(f)
        self.assertEqual(got, 'coiss_2069/img.jpg')

    def test__get_file_path_url(self):
        f = 'http://pds-rings.seti.org/coiss_2xxx/coiss_2069/img.jpg'
        got = get_file_path(f)
        self.assertEqual(got, 'coiss_2069/img.jpg')
