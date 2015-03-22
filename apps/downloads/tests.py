"""
# downloads tests

"""
# from django.test import TestCase  removed because it deletes test table data after every test
from unittest import TestCase
from django.test.client import Client
from django.db.models import get_model

from search.views import *
from results.views import *
from django.http import QueryDict

cursor = connection.cursor()

# downloads things
from downloads.views import *


class downloadsTests(TestCase):

    c = Client()

    def test__get_download_size_browse_images_being_counted(self):
        ring_obs_ids = 'S_IMG_CO_ISS_1680806066_N'
        files = getFiles(ring_obs_ids,"raw", "path")
        product_types=['CALIBRATED']
        size1 = get_download_size(files, product_types, ['Full'])
        size2 = get_download_size(files, product_types, ['Med'])
        self.assertNotEqual(size1, size2)

    # get_download_size(
    def test__get_download_size_COISS(self):
        ring_obs_ids = 'S_IMG_CO_ISS_1680806066_N'
        files = getFiles(ring_obs_id=ring_obs_ids,fmt="raw",loc_type="path")
        size = get_download_size(files, 'CALIBRATED', ['Full'])
        self.assertGreater(size, 0)

    def test__get_download_size_COCIRS(self):
        ring_obs_ids = 'S_SPEC_CO_CIRS_1630456943_FP1'
        files = getFiles(ring_obs_id=ring_obs_ids,fmt="raw",loc_type="path")
        print files
        size = get_download_size(files, 'CALIBRATED_SPECTRUM', [])
        self.assertGreater(size, 0)

    def test__get_download_size_COVIMS(self):
        ring_obs_ids = 'S_CUBE_CO_VIMS_1638723713_VIS'
        files = getFiles(ring_obs_id=ring_obs_ids,fmt="raw",loc_type="path")
        size = get_download_size(files, 'RAW_SPECTRAL_IMAGE_CUBE', ['med'])
        self.assertGreater(size, 0)

    def test__get_download_size_VGISS(self):
        ring_obs_ids = 'N_IMG_VG2_ISS_1120000_W'
        files = getFiles(ring_obs_id=ring_obs_ids,fmt="raw",loc_type="path")
        size = get_download_size(files, 'CALIBRATED_IMAGE', ['small'])
        self.assertGreater(size, 0)

    def test__get_download_size_empty_product_types(self):
        ring_obs_ids = 'S_IMG_CO_ISS_1680806066_N'
        files = getFiles(ring_obs_id=ring_obs_ids,fmt="raw",loc_type="path")
        size = get_download_size(files, '', [])
        self.assertLess(size, 2250000)  # about 2 MB

