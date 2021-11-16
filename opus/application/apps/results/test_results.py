# results/test_results.py

import logging
from unittest import TestCase

from django.core.cache import cache
from django.db import connection
from django.http import Http404, QueryDict
from django.test import RequestFactory

from results.views import (api_get_categories_for_opus_id,
                           api_get_categories_for_search,
                           api_get_data,
                           api_get_data_and_images,
                           api_get_files,
                           api_get_image,
                           api_get_images,
                           api_get_images_by_size,
                           api_get_metadata,
                           api_get_metadata_v2,
                           api_get_product_types_for_opus_id,
                           api_get_product_types_for_search,
                           get_triggered_tables,
                           url_to_search_params)

import settings

cursor = connection.cursor()

class resultsTests(TestCase):

    def _empty_user_searches(self):
        cursor = connection.cursor()
        cursor.execute('DELETE FROM user_searches')
        cursor.execute("ALTER TABLE user_searches AUTO_INCREMENT = 1")
        cursor.execute("SHOW TABLES LIKE %s", ["cache_%"])
        for row in cursor:
            q = 'DROP TABLE ' + row[0]
            print(q)
            cursor.execute(q)
        cache.clear()
        self.factory = RequestFactory()

    def setUp(self):
        settings.OPUS_FAKE_API_DELAYS = 0
        settings.OPUS_FAKE_SERVER_ERROR404_PROBABILITY = 0
        settings.OPUS_FAKE_SERVER_ERROR500_PROBABILITY = 0
        self._empty_user_searches()
        self.maxDiff = None
        logging.disable(logging.ERROR)

    def tearDown(self):
        self._empty_user_searches()
        logging.disable(logging.NOTSET)


            ######################################################
            ######### api_get_data_and_images UNIT TESTS #########
            ######################################################

    def test__api_get_data_and_images_no_request(self):
        "[test_results.py] api_get_data_and_images: no request"
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /__api/dataimages.json'):
            api_get_data_and_images(None)

    def test__api_get_data_and_images_no_get(self):
        "[test_results.py] api_get_data_and_images: no GET"
        request = self.factory.get('/__api/dataimages.json')
        request.GET = None
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /__api/dataimages.json'):
            api_get_data_and_images(request)


            ###########################################
            ######### api_get_data UNIT TESTS #########
            ###########################################

    def test__api_get_data_no_request(self):
        "[test_results.py] api_get_data: no request"
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /api/data.json'):
            api_get_data(None, 'json')

    def test__api_get_data_no_get(self):
        "[test_results.py] api_get_data: no GET"
        request = self.factory.get('/__api/data.json')
        request.GET = None
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /api/data.json'):
            api_get_data(request, 'json')



            ###############################################
            ######### api_get_metadata UNIT TESTS #########
            ###############################################

    def test__api_get_metadata_no_request(self):
        "[test_results.py] api_get_metadata: no request"
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /api/metadata_v2/vg-iss-2-s-c4360845.json'):
            api_get_metadata(None, 'vg-iss-2-s-c4360845', 'json')

    def test__api_get_metadata_no_get(self):
        "[test_results.py] api_get_metadata: no GET"
        request = self.factory.get('/api/metadata/vg-iss-2-s-c4360845.json')
        request.GET = None
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /api/metadata_v2/vg-iss-2-s-c4360845.json'):
            api_get_metadata(request, 'vg-iss-2-s-c4360845', 'json')


            ##################################################
            ######### api_get_metadata_v2 UNIT TESTS #########
            ##################################################

    def test__api_get_metadata_v2_no_request(self):
        "[test_results.py] api_get_metadata_v2: no request"
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /api/metadata_v2/vg-iss-2-s-c4360845.json'):
            api_get_metadata_v2(None, 'vg-iss-2-s-c4360845', 'json')

    def test__api_get_metadata_v2_no_get(self):
        "[test_results.py] api_get_metadata_v2: no GET"
        request = self.factory.get('/api/metadata_v2/vg-iss-2-s-c4360845.json')
        request.GET = None
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /api/metadata_v2/vg-iss-2-s-c4360845.json'):
            api_get_metadata_v2(request, 'vg-iss-2-s-c4360845', 'json')


            #############################################
            ######### api_get_images UNIT TESTS #########
            #############################################

    def test__api_get_images_no_request(self):
        "[test_results.py] api_get_images: no request"
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /api/images/None.json'):
            api_get_images(None, 'json')

    def test__api_get_images_no_get(self):
        "[test_results.py] api_get_images: no GET"
        request = self.factory.get('/api/images.json')
        request.GET = None
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /api/images/None.json'):
            api_get_images(request, 'json')


            #####################################################
            ######### api_get_images_by_size UNIT TESTS #########
            #####################################################

    def test__api_get_images_by_size_no_request(self):
        "[test_results.py] api_get_images_by_size: no request"
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /api/images/small.json'):
            api_get_images_by_size(None, 'small', 'json')

    def test__api_get_images_by_size_no_get(self):
        "[test_results.py] api_get_images_by_size: no GET"
        request = self.factory.get('/api/images/small.json')
        request.GET = None
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /api/images/small.json'):
            api_get_images_by_size(request, 'small', 'json')


            ############################################
            ######### api_get_image UNIT TESTS #########
            ############################################

    def test__api_get_image_no_request(self):
        "[test_results.py] api_get_image: no request"
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /api/images/small.json'):
            api_get_image(None, 'vg-iss-2-s-c4360845', 'small', 'json')

    def test__api_get_image_no_get(self):
        "[test_results.py] api_get_image: no GET"
        request = self.factory.get('/api/image/small/vg-iss-2-s-c4360845.json')
        request.GET = None
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /api/images/small.json'):
            api_get_image(request, 'vg-iss-2-s-c4360845', 'small', 'json')


            ############################################
            ######### api_get_files UNIT TESTS #########
            ############################################

    def test__api_get_files_no_request(self):
        "[test_results.py] api_get_files: no request"
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /api/files/vg-iss-2-s-c4360845.json'):
            api_get_files(None, 'vg-iss-2-s-c4360845')

    def test__api_get_files_no_get(self):
        "[test_results.py] api_get_files: no GET"
        request = self.factory.get('/api/files/vg-iss-2-s-c4360845.json')
        request.GET = None
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /api/files/vg-iss-2-s-c4360845.json'):
            api_get_files(request, 'vg-iss-2-s-c4360845')


            #############################################################
            ######### api_get_categories_for_opus_id UNIT TESTS #########
            #############################################################

    def test__api_get_categories_for_opus_id_no_request(self):
        "[test_results.py] api_get_categories_for_opus_id: no request"
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /api/categories/vg-iss-2-s-c4360845.json'):
            api_get_categories_for_opus_id(None, 'vg-iss-2-s-c4360845')

    def test__api_get_categories_for_opus_id_no_get(self):
        "[test_results.py] api_get_categories_for_opus_id: no GET"
        request = self.factory.get('/api/categories/vg-iss-2-s-c4360845.json')
        request.GET = None
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /api/categories/vg-iss-2-s-c4360845.json'):
            api_get_categories_for_opus_id(request, 'vg-iss-2-s-c4360845')



            ############################################################
            ######### api_get_categories_for_search UNIT TESTS #########
            ############################################################

    def test__api_get_categories_for_search_no_request(self):
        "[test_results.py] api_get_categories_for_search: no request"
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /api/categories.json'):
            api_get_categories_for_search(None)

    def test__api_get_categories_for_search_no_get(self):
        "[test_results.py] api_get_categories_for_search: no GET"
        request = self.factory.get('/api/categories.json')
        request.GET = None
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /api/categories.json'):
            api_get_categories_for_search(request)


            ################################################################
            ######### api_get_product_types_for_opus_id UNIT TESTS #########
            ################################################################

    def test__api_get_product_types_for_opus_id_no_request(self):
        "[test_results.py] api_get_product_types_for_opus_id: no request"
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /api/product_types/vg-iss-2-s-c4360845.json'):
            api_get_product_types_for_opus_id(None, 'vg-iss-2-s-c4360845')

    def test__api_get_product_types_for_opus_id_no_get(self):
        "[test_results.py] api_get_product_types_for_opus_id: no GET"
        request = self.factory.get('/api/product_types/vg-iss-2-s-c4360845.json')
        request.GET = None
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /api/product_types/vg-iss-2-s-c4360845.json'):
            api_get_product_types_for_opus_id(request, 'vg-iss-2-s-c4360845')



            ###############################################################
            ######### api_get_product_types_for_search UNIT TESTS #########
            ###############################################################

    def test__api_get_product_types_for_search_no_request(self):
        "[test_results.py] api_get_product_types_for_search: no request"
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /api/product_types.json'):
            api_get_product_types_for_search(None)

    def test__api_get_product_types_for_search_no_get(self):
        "[test_results.py] api_get_product_types_for_search: no GET"
        request = self.factory.get('/api/product_types.json')
        request.GET = None
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /api/product_types.json'):
            api_get_product_types_for_search(request)


            ###################################################
            ######### get_triggered_tables UNIT TESTS #########
            ###################################################

    def _test_triggered_tables(self, q, expected):
        (selections,extras) = url_to_search_params(q)
        print(selections)
        partables = get_triggered_tables(selections, extras)
        print('partables:')
        print(partables)
        print('expected:')
        print(expected)
        self.assertEqual(partables, expected)

    def test__get_triggered_tables_cassini(self):
        "[test_results.py] get_triggered_tables: tables triggered by mission Cassini"
        q = QueryDict('mission=Cassini')
        expected = ['obs_general', 'obs_pds', 'obs_type_image',
                    'obs_wavelength', 'obs_profile',
                    'obs_surface_geometry_name',
                    'obs_surface_geometry',
                    'obs_ring_geometry',
                    'obs_mission_cassini']
        self._test_triggered_tables(q, expected)

    def test__get_triggered_tables_cocirs(self):
        "[test_results.py] get_triggered_tables: tables triggered by instrument COCIRS"
        q = QueryDict('planet=SATURN&instrument=COCIRS')
        expected = ['obs_general', 'obs_pds', 'obs_type_image',
                    'obs_wavelength', 'obs_profile',
                    'obs_surface_geometry_name',
                    'obs_surface_geometry',
                    'obs_ring_geometry',
                    'obs_mission_cassini', 'obs_instrument_cocirs']
        self._test_triggered_tables(q, expected)

    def test__get_triggered_tables_cocirs_volume_5201(self):
        "[test_results.py] get_triggered_tables: tables triggered by volume COCIRS_5201"
        q = QueryDict('volumeid=COCIRS_5201&qtype-volumeid=begins')
        expected = ['obs_general', 'obs_pds', 'obs_type_image',
                    'obs_wavelength', 'obs_profile',
                    'obs_surface_geometry_name',
                    'obs_surface_geometry',
                    'obs_ring_geometry',
                    'obs_mission_cassini', 'obs_instrument_cocirs']
        self._test_triggered_tables(q, expected)

    def test__get_triggered_tables_cocirs_volume_0406(self):
        "[test_results.py] get_triggered_tables: tables triggered by volume COCIRS_0406"
        q = QueryDict('volumeid=COCIRS_0406&qtype-volumeid=begins')
        expected = ['obs_general', 'obs_pds', 'obs_type_image',
                    'obs_wavelength', 'obs_profile',
                    'obs_surface_geometry_name',
                    'obs_surface_geometry',
                    'obs_ring_geometry',
                    'obs_mission_cassini', 'obs_instrument_cocirs']
        self._test_triggered_tables(q, expected)

    def test__get_triggered_tables_coiss(self):
        "[test_results.py] get_triggered_tables: tables triggered by instrument COISS"
        q = QueryDict('planet=SATURN&instrument=COISS')
        expected = ['obs_general', 'obs_pds', 'obs_type_image',
                    'obs_wavelength', 'obs_profile',
                    'obs_surface_geometry_name',
                    'obs_surface_geometry',
                    'obs_ring_geometry',
                    'obs_mission_cassini', 'obs_instrument_coiss']
        self._test_triggered_tables(q, expected)

    def test__get_triggered_tables_coiss_volume(self):
        "[test_results.py] get_triggered_tables: tables triggered by volume COISS"
        q = QueryDict('planet=SATURN&volumeid=COISS&qtype-volumeid=begins')
        expected = ['obs_general', 'obs_pds', 'obs_type_image',
                    'obs_wavelength', 'obs_profile',
                    'obs_surface_geometry_name',
                    'obs_surface_geometry',
                    'obs_ring_geometry',
                    'obs_mission_cassini', 'obs_instrument_coiss']
        self._test_triggered_tables(q, expected)

    def test__get_triggered_tables_couvis(self):
        "[test_results.py] get_triggered_tables: tables triggered by instrument COUVIS"
        q = QueryDict('instrument=COUVIS')
        expected = ['obs_general', 'obs_pds', 'obs_type_image',
                    'obs_wavelength', 'obs_profile',
                    'obs_surface_geometry_name',
                    'obs_surface_geometry',
                    'obs_ring_geometry',
                    'obs_mission_cassini', 'obs_instrument_couvis']
        self._test_triggered_tables(q, expected)

    def test__get_triggered_tables_couvis_volume(self):
        "[test_results.py] get_triggered_tables: tables triggered by volume COUVIS"
        q = QueryDict('volumeid=COUVIS&qtype-volumeid=begins')
        expected = ['obs_general', 'obs_pds', 'obs_type_image',
                    'obs_wavelength', 'obs_profile',
                    'obs_surface_geometry_name',
                    'obs_surface_geometry',
                    'obs_ring_geometry',
                    'obs_mission_cassini', 'obs_instrument_couvis']
        self._test_triggered_tables(q, expected)

    def test__get_triggered_tables_covims(self):
        "[test_results.py] get_triggered_tables: tables triggered by instrument COVIMS"
        q = QueryDict('instrument=COVIMS')
        expected = ['obs_general', 'obs_pds', 'obs_type_image',
                    'obs_wavelength', 'obs_profile',
                    'obs_surface_geometry_name',
                    'obs_surface_geometry',
                    'obs_ring_geometry',
                    'obs_mission_cassini', 'obs_instrument_covims']
        self._test_triggered_tables(q, expected)

    def test__get_triggered_tables_galileo(self):
        "[test_results.py] get_triggered_tables: tables triggered by mission Galileo"
        q = QueryDict('mission=Galileo')
        expected = ['obs_general', 'obs_pds', 'obs_type_image',
                    'obs_wavelength', 'obs_profile',
                    'obs_surface_geometry_name',
                    'obs_surface_geometry',
                    'obs_ring_geometry',
                    'obs_mission_galileo',
                    'obs_instrument_gossi']
        self._test_triggered_tables(q, expected)

    def test__get_triggered_tables_gossi(self):
        "[test_results.py] get_triggered_tables: tables triggered by instrument GOSSI"
        q = QueryDict('instrument=Galileo+SSI')
        expected = ['obs_general', 'obs_pds', 'obs_type_image',
                    'obs_wavelength', 'obs_profile',
                    'obs_surface_geometry_name',
                    'obs_surface_geometry',
                    'obs_ring_geometry',
                    'obs_mission_galileo',
                    'obs_instrument_gossi']
        self._test_triggered_tables(q, expected)

    def test__get_triggered_tables_voyager(self):
        "[test_results.py] get_triggered_tables: tables triggered by mission Voyager"
        q = QueryDict('mission=Voyager')
        expected = ['obs_general', 'obs_pds', 'obs_type_image',
                    'obs_wavelength', 'obs_profile',
                    'obs_surface_geometry_name',
                    'obs_surface_geometry',
                    'obs_ring_geometry',
                    'obs_mission_voyager']
        self._test_triggered_tables(q, expected)

    def test__get_triggered_tables_vgiss(self):
        "[test_results.py] get_triggered_tables: tables triggered by instrument VGISS"
        q = QueryDict('instrument=Voyager+ISS')
        expected = ['obs_general', 'obs_pds', 'obs_type_image',
                    'obs_wavelength', 'obs_profile',
                    'obs_surface_geometry_name',
                    'obs_surface_geometry',
                    'obs_ring_geometry',
                    'obs_mission_voyager',
                    'obs_instrument_vgiss']
        self._test_triggered_tables(q, expected)

    def test__get_triggered_tables_vguvs(self):
        "[test_results.py] get_triggered_tables: tables triggered by instrument VGUVS"
        q = QueryDict('instrument=Voyager+UVS')
        expected = ['obs_general', 'obs_pds', 'obs_type_image',
                    'obs_wavelength', 'obs_profile',
                    'obs_surface_geometry_name',
                    'obs_surface_geometry',
                    'obs_ring_geometry',
                    'obs_mission_voyager']
        self._test_triggered_tables(q, expected)

    def test__get_triggered_tables_vgpps(self):
        "[test_results.py] get_triggered_tables: tables triggered by instrument VGPPS"
        q = QueryDict('instrument=Voyager+PPS')
        expected = ['obs_general', 'obs_pds', 'obs_type_image',
                    'obs_wavelength', 'obs_profile',
                    'obs_surface_geometry_name',
                    'obs_surface_geometry',
                    'obs_ring_geometry',
                    'obs_mission_voyager']
        self._test_triggered_tables(q, expected)

    def test__get_triggered_tables_vgrss(self):
        "[test_results.py] get_triggered_tables: tables triggered by instrument VGRSS"
        q = QueryDict('instrument=Voyager+RSS')
        expected = ['obs_general', 'obs_pds', 'obs_type_image',
                    'obs_wavelength', 'obs_profile',
                    'obs_surface_geometry_name',
                    'obs_surface_geometry',
                    'obs_ring_geometry',
                    'obs_mission_voyager']
        self._test_triggered_tables(q, expected)

    def test__get_triggered_tables_vgiss_obs_volume(self):
        "[test_results.py] get_triggered_tables: tables triggered by volume VGISS_6210"
        q = QueryDict('volumeid=VGISS_6210')
        expected = ['obs_general', 'obs_pds', 'obs_type_image',
                    'obs_wavelength', 'obs_profile',
                    'obs_surface_geometry_name',
                    'obs_surface_geometry',
                    'obs_ring_geometry',
                    'obs_mission_voyager', 'obs_instrument_vgiss']
        self._test_triggered_tables(q, expected)

    def test__get_triggered_tables_vgpps_volume(self):
        "[test_results.py] get_triggered_tables: tables triggered by volume VG_2801"
        q = QueryDict('volumeid=VG_2801')
        expected = ['obs_general', 'obs_pds', 'obs_type_image',
                    'obs_wavelength', 'obs_profile',
                    'obs_surface_geometry_name',
                    'obs_surface_geometry',
                    'obs_ring_geometry',
                    'obs_mission_voyager']
        self._test_triggered_tables(q, expected)

    def test__get_triggered_tables_vguvs_volume(self):
        "[test_results.py] get_triggered_tables: tables triggered by volume VG_2802"
        q = QueryDict('volumeid=VG_2802')
        expected = ['obs_general', 'obs_pds', 'obs_type_image',
                    'obs_wavelength', 'obs_profile',
                    'obs_surface_geometry_name',
                    'obs_surface_geometry',
                    'obs_ring_geometry',
                    'obs_mission_voyager']
        self._test_triggered_tables(q, expected)

    def test__get_triggered_tables_vgrss_volume(self):
        "[test_results.py] get_triggered_tables: tables triggered by volume VG_2803"
        q = QueryDict('volumeid=VG_2803')
        expected = ['obs_general', 'obs_pds', 'obs_type_image',
                    'obs_wavelength', 'obs_profile',
                    'obs_surface_geometry_name',
                    'obs_surface_geometry',
                    'obs_ring_geometry',
                    'obs_mission_voyager']
        self._test_triggered_tables(q, expected)

    def test__get_triggered_tables_vgiss_prof_volume(self):
        "[test_results.py] get_triggered_tables: tables triggered by volume VG_2810"
        q = QueryDict('volumeid=VG_2810')
        expected = ['obs_general', 'obs_pds', 'obs_type_image',
                    'obs_wavelength', 'obs_profile',
                    'obs_surface_geometry_name',
                    'obs_surface_geometry',
                    'obs_ring_geometry',
                    'obs_mission_voyager', 'obs_instrument_vgiss']
        self._test_triggered_tables(q, expected)

    def test__get_triggered_tables_hubble(self):
        "[test_results.py] get_triggered_tables: tables triggered by mission Hubble"
        q = QueryDict('mission=Hubble')
        expected = ['obs_general', 'obs_pds', 'obs_type_image',
                    'obs_wavelength', 'obs_profile',
                    'obs_surface_geometry_name',
                    'obs_surface_geometry',
                    'obs_ring_geometry',
                    'obs_mission_hubble']
        self._test_triggered_tables(q, expected)

    def test__get_triggered_tables_hstacs(self):
        "[test_results.py] get_triggered_tables: tables triggered by instrument HSTACS"
        q = QueryDict('instrument=Hubble+ACS')
        expected = ['obs_general', 'obs_pds', 'obs_type_image',
                    'obs_wavelength', 'obs_profile',
                    'obs_surface_geometry_name',
                    'obs_surface_geometry',
                    'obs_ring_geometry',
                    'obs_mission_hubble']
        self._test_triggered_tables(q, expected)

    def test__get_triggered_tables_hstnicmos(self):
        "[test_results.py] get_triggered_tables: tables triggered by instrument HSTNICMOS"
        q = QueryDict('instrument=Hubble+NICMOS')
        expected = ['obs_general', 'obs_pds', 'obs_type_image',
                    'obs_wavelength', 'obs_profile',
                    'obs_surface_geometry_name',
                    'obs_surface_geometry',
                    'obs_ring_geometry',
                    'obs_mission_hubble']
        self._test_triggered_tables(q, expected)

    def test__get_triggered_tables_hststis(self):
        "[test_results.py] get_triggered_tables: tables triggered by instrument HSTSTIS"
        q = QueryDict('instrument=Hubble+STIS')
        expected = ['obs_general', 'obs_pds', 'obs_type_image',
                    'obs_wavelength', 'obs_profile',
                    'obs_surface_geometry_name',
                    'obs_surface_geometry',
                    'obs_ring_geometry',
                    'obs_mission_hubble']
        self._test_triggered_tables(q, expected)

    def test__get_triggered_tables_hstwfc3(self):
        "[test_results.py] get_triggered_tables: tables triggered by instrument HSTWFC3"
        q = QueryDict('instrument=Hubble+WFC3')
        expected = ['obs_general', 'obs_pds', 'obs_type_image',
                    'obs_wavelength', 'obs_profile',
                    'obs_surface_geometry_name',
                    'obs_surface_geometry',
                    'obs_ring_geometry',
                    'obs_mission_hubble']
        self._test_triggered_tables(q, expected)

    def test__get_triggered_tables_hstwfc3_filespec(self):
        "[test_results.py] get_triggered_tables: tables triggered by filespec IB4V12N4Q"
        q = QueryDict('primaryfilespec=IB4V12N4Q')
        expected = ['obs_general', 'obs_pds', 'obs_type_image',
                    'obs_wavelength', 'obs_profile',
                    'obs_surface_geometry_name',
                    'obs_surface_geometry',
                    'obs_ring_geometry',
                    'obs_mission_hubble']
        self._test_triggered_tables(q, expected)

    def test__get_triggered_tables_hstwfpc2(self):
        "[test_results.py] get_triggered_tables: tables triggered by instrument HSTWFPC2"
        q = QueryDict('instrument=Hubble+WFPC2')
        expected = ['obs_general', 'obs_pds', 'obs_type_image',
                    'obs_wavelength', 'obs_profile',
                    'obs_surface_geometry_name',
                    'obs_surface_geometry',
                    'obs_ring_geometry',
                    'obs_mission_hubble']
        self._test_triggered_tables(q, expected)

    def test__get_triggered_tables_newhorizons(self):
        "[test_results.py] get_triggered_tables: tables triggered by mission New Horizons"
        q = QueryDict('mission=New+Horizons')
        expected = ['obs_general', 'obs_pds', 'obs_type_image',
                    'obs_wavelength', 'obs_profile',
                    'obs_surface_geometry_name',
                    'obs_surface_geometry',
                    'obs_ring_geometry',
                    'obs_mission_new_horizons']
        self._test_triggered_tables(q, expected)

    def test__get_triggered_tables_nhlorri(self):
        "[test_results.py] get_triggered_tables: tables triggered by instrument NHLORRI"
        q = QueryDict('instrument=New+Horizons+LORRI')
        expected = ['obs_general', 'obs_pds', 'obs_type_image',
                    'obs_wavelength', 'obs_profile',
                    'obs_surface_geometry_name',
                    'obs_surface_geometry',
                    'obs_ring_geometry',
                    'obs_mission_new_horizons',
                    'obs_instrument_nhlorri']
        self._test_triggered_tables(q, expected)

    def test__get_triggered_tables_nhmvic(self):
        "[test_results.py] get_triggered_tables: tables triggered by instrument NHMVIC"
        q = QueryDict('instrument=New+Horizons+MVIC')
        expected = ['obs_general', 'obs_pds', 'obs_type_image',
                    'obs_wavelength', 'obs_profile',
                    'obs_surface_geometry_name',
                    'obs_surface_geometry',
                    'obs_ring_geometry',
                    'obs_mission_new_horizons',
                    'obs_instrument_nhmvic']
        self._test_triggered_tables(q, expected)



    # def test__get_metadata(self):
    #     response = self.client.get('/opus/api/metadata/S_IMG_CO_ISS_1686170143_N.json')
    #     data = json.loads(response.content)
    #     expected = {'Cassini Mission Constraints': {'prime': 'Y', 'rev_no': '149', 'cassini_target_name': 'Iapetus', 'obs_name': 'ISS_149IA_IAPETUS157_PRIME', 'spacecraft_clock_count2': 1686170143.126, 'spacecraft_clock_count1': 1686170142.001, 'prime_inst_id': 'COISS', 'ert_sec2': 360915801.835, 'activity_name': 'IAPETUS', 'ert_sec1': 360915694.139}, 'Cassini ISS Constraints': {'DELAYED_READOUT_FLAG': 'NO', 'IMAGE_OBSERVATION_TYPE': 'SCIENCE', 'OPTICS_TEMPERATURE_front': 0.627499, 'INST_CMPRS_PARAM_MALGO': -2147483648, 'INST_CMPRS_PARAM_QF': -2147483648, 'VALID_MAXIMUM_minimum_full_well_saturation_level': 4095, 'LIGHT_FLOOD_STATE_FLAG': 'ON', 'MISSING_LINES': 0, 'ANTIBLOOMING_STATE_FLAG': 'OFF', 'FILTER_NAME': 'IR2  ,CL2', 'INST_CMPRS_RATE_actual_average': 2.514053, 'FILTER_TEMPERATURE': 0.248629, 'INST_CMPRS_PARAM_GOB': -2147483648, 'EXPECTED_MAXIMUM_full_well_DN': 0.227162, 'TELEMETRY_FORMAT_ID': 'S_N_ER_3', 'camera': 'N', 'MISSING_PACKET_FLAG': 'NO', 'GAIN_MODE_ID': '29 ELECTRONS PER DN', 'DATA_CONVERSION_TYPE': '12BIT', 'OPTICS_TEMPERATURE_rear': 1.820474, 'CALIBRATION_LAMP_STATE_FLAG': 'N/A', 'VALID_MAXIMUM_maximum_DN_saturation_level': 4095, 'SHUTTER_MODE_ID': 'NACONLY', 'INST_CMPRS_RATIO': 6.364224, 'SHUTTER_STATE_ID': 'ENABLED', 'INST_CMPRS_RATE_expected_average': 3.30956, 'FILTER': 'IR2', 'INST_CMPRS_TYPE': 'LOSSLESS', 'EXPECTED_MAXIMUM_max_DN': 0.250449, 'INST_CMPRS_PARAM_TB': -2147483648}, 'Image Constraints': {'duration': 1.5, 'greater_pixel_size': 1024.0, 'lesser_pixel_size': 1024.0, 'levels': '4096', 'image_type_id': 'FRAM'}, 'General Constraints': {'instrument_id': 'COISS', 'mission_id': 'CO', 'inst_host_id': 'CO', 'is_image': 1, 'type_id': 'IMG', 'target_name': 'IAPETUS', 'primary_file_spec': 'COISS_2068/data/1686113920_1686232684/N1686170143_1.IMG', 'time1': 360791252.345, 'observation_duration': 1.5, 'note': 'N/A', 'class_id': 'R', 'volume_id_list': 'COISS_2068', 'opus_id': 'S_IMG_CO_ISS_1686170143_N', 'time2': 360791253.845, 'declination2': 84.37116, 'planet_id': 'SAT', 'right_asc2': 298.703957, 'target_class': 'MOON', 'right_asc1': 294.729581, 'quantity': 'REFLECT', 'declination1': 83.967892}, 'Iapetus Surface Geometry': {'sub_observer_planetocentric_latitude': -80.121, 'Observer_longitude2': 37.652, 'Observer_longitude1': -132.845, 'coarsest_resolution1': 5.18978, 'sub_observer_IAU_longitude': 300.233, 'coarsest_resolution2': 77.92939, 'd_IAU_west_longitude': 85.2485, 'IAU_west_longitude': 252.63750000000002, 'sub_observer_planetographic_latitude': -80.976, 'planetocentric_latitude2': 3.096, 'Observer_longitude': -47.5965, 'planetocentric_latitude1': -77.022, 'sub_solar_planetographic_latitude': 12.945, 'd_solar_hour_angle': 180.0, 'emission2': 87.526, 'emission1': 0.54, 'solar_hour_angle': 180.0, 'd_Observer_longitude': 85.2485, 'range_to_body2': 866581.981, 'range_to_body1': 865897.624, 'center_resolution': 5.16977, 'phase1': 94.986, 'phase2': 95.085, 'planetographic_latitude2': 3.395, 'planetographic_latitude1': -78.131, 'center_distance': 866610.707, 'IAU_west_longitude1': 167.389, 'IAU_west_longitude2': 337.886, 'solar_hour_angle1': 0.0, 'finest_resolution1': 5.16553, 'finest_resolution2': 5.16946, 'solar_hour_angle2': 360.0, 'sub_solar_planetocentric_latitude': 11.838, 'center_phase_angle': 95.035, 'sub_solar_IAU_longitude': 253.148, 'incidence1': 10.542, 'incidence2': 178.553}, 'Ring Geometry Constraints': {'longitude_WRT_observer2': None, 'edge_on_solar_hour_angle1': None, 'J2000_longitude2': None, 'edge_on_solar_hour_angle2': None, 'ring_center_distance': 3568906.674, 'longitude_WRT_observer1': None, 'ring_center_phase': 74.661, 'north_based_emission2': None, 'north_based_emission1': None, 'emission1': None, 'J2000_longitude1': None, 'north_based_incidence1': None, 'projected_radial_resolution1': None, 'range_to_ring_intercept2': None, 'range_to_ring_intercept1': None, 'projected_radial_resolution2': None, 'edge_on_altitude2': None, 'edge_on_altitude1': None, 'edge_on_radius1': None, 'edge_on_radius2': None, 'ring_azimuth_WRT_observer2': None, 'ring_azimuth_WRT_observer1': None, 'emission2': None, 'solar_ring_elev2': None, 'solar_ring_elev1': None, 'observer_ring_elevation1': None, 'ring_radius1': None, 'observer_ring_elevation2': -999.0, 'sub_observer_ring_long': 89.703, 'ring_center_north_based_incidence': 80.192, 'range_to_edge_on_point2': None, 'ring_center_emission': 89.642, 'observer_ring_opening_angle': 0.359, 'ring_radius2': None, 'ring_center_north_based_emission': 89.642, 'resolution1': None, 'resolution2': None, 'edge_on_radial_resolution1': None, 'edge_on_radial_resolution2': None, 'phase1': None, 'phase2': None, 'range_to_edge_on_point1': None, 'sub_solar_ring_long': 15.211, 'solar_hour_angle1': None, 'solar_ring_opening_angle': 9.807, 'north_based_incidence2': None, 'solar_hour_angle2': None, 'edge_on_J2000_longitude2': None, 'edge_on_J2000_longitude1': None, 'incidence1': None, 'incidence2': None, 'ring_center_incidence': 80.192}, 'Saturn Surface Geometry': {'sub_observer_planetocentric_latitude': 0.359, 'Observer_longitude2': None, 'Observer_longitude1': None, 'coarsest_resolution1': None, 'sub_observer_IAU_longitude': 327.771, 'coarsest_resolution2': None, 'd_IAU_west_longitude': None, 'IAU_west_longitude': None, 'sub_observer_planetographic_latitude': 0.441, 'planetocentric_latitude2': None, 'Observer_longitude': None, 'planetocentric_latitude1': None, 'sub_solar_planetographic_latitude': 11.994, 'd_solar_hour_angle': None, 'emission2': None, 'emission1': None, 'solar_hour_angle': None, 'd_Observer_longitude': None, 'range_to_body2': None, 'range_to_body1': None, 'center_resolution': 21.29031, 'phase1': None, 'phase2': None, 'planetographic_latitude2': None, 'planetographic_latitude1': None, 'center_distance': 3568906.674, 'IAU_west_longitude1': None, 'IAU_west_longitude2': None, 'solar_hour_angle1': None, 'finest_resolution1': None, 'finest_resolution2': None, 'solar_hour_angle2': None, 'sub_solar_planetocentric_latitude': 9.807, 'center_phase_angle': 74.661, 'sub_solar_IAU_longitude': 42.262, 'incidence1': None, 'incidence2': None}, 'Wavelength Constraints': {'wavelength2': 0.862, 'wave_no1': None, 'wavelength1': 0.862, 'wave_no_res1': None, 'wave_no_res2': None, 'spec_size': None, 'polarization_type': 'NONE', 'wave_no2': None, 'wave_res1': None, 'wave_res2': None, 'spec_flag': 'N'}}
    #     self.assertEqual(data['Cassini Mission Constraints'],expected['Cassini Mission Constraints'])
    #
    # def test__metadata_S_IMG_CO_ISS_1686170088_N(self):
    #     opus_id = 'S_IMG_CO_ISS_1686170088_N'
    #     detail, all_info = get_metadata({},opus_id=opus_id,fmt='raw')
    #     print(detail['Cassini Mission Constraints'])
    #     expected = {'General Constraints': {'instrument_id': 'COISS', 'note': 'N/A', 'time1': 360791198.385, 'is_image': 1, 'type_id': 'IMG', 'target_name': 'IAPETUS', 'primary_file_spec': 'COISS_2068/data/1686113920_1686232684/N1686170088_1.IMG', 'inst_host_id': 'CO', 'class_id': 'R', 'observation_duration': 0.46000003814697266, 'mission_id': 'CO', 'time2': 360791198.845, 'volume_id_list': 'COISS_2068', 'opus_id': 'S_IMG_CO_ISS_1686170088_N', 'declination1': 83.960869, 'declination2': 84.364349, 'planet_id': 'SAT', 'right_asc2': 298.739665, 'target_class': 'MOON', 'right_asc1': 294.767913, 'quantity': 'REFLECT'}, 'Ring Geometry Constraints': {'edge_on_altitude2': None, 'edge_on_solar_hour_angle1': None, 'resolution1': None, 'edge_on_solar_hour_angle2': None, 'ring_center_distance': 3568988.32, 'edge_on_altitude1': None, 'ring_center_phase': 74.66, 'north_based_emission2': None, 'north_based_emission1': None, 'range_to_edge_on_point2': None, 'resolution2': None, 'solar_ring_opening_angle': 9.807, 'projected_radial_resolution1': None, 'range_to_ring_intercept2': None, 'range_to_ring_intercept1': None, 'projected_radial_resolution2': None, 'longitude_WRT_observer2': None, 'longitude_WRT_observer1': None, 'edge_on_radius1': None, 'edge_on_radius2': None, 'ring_azimuth_WRT_observer2': None, 'ring_azimuth_WRT_observer1': None, 'emission2': None, 'solar_ring_elev2': None, 'solar_ring_elev1': None, 'observer_ring_elevation1': None, 'phase1': None, 'observer_ring_elevation2': -999.0, 'sub_observer_ring_long': 89.701, 'ring_center_north_based_incidence': 80.192, 'emission1': None, 'ring_center_emission': 89.642, 'observer_ring_opening_angle': 0.359, 'phase2': None, 'ring_center_north_based_emission': 89.642, 'J2000_longitude2': None, 'J2000_longitude1': None, 'edge_on_radial_resolution1': None, 'edge_on_radial_resolution2': None, 'ring_radius1': None, 'ring_radius2': None, 'range_to_edge_on_point1': None, 'sub_solar_ring_long': 15.211, 'solar_hour_angle1': None, 'north_based_incidence1': None, 'north_based_incidence2': None, 'solar_hour_angle2': None, 'edge_on_J2000_longitude2': None, 'edge_on_J2000_longitude1': None, 'incidence1': None, 'incidence2': None, 'ring_center_incidence': 80.192}, 'Wavelength Constraints': {'wavelength2': 0.65, 'wave_no1': None, 'wavelength1': 0.65, 'wave_no_res1': None, 'wave_no_res2': None, 'spec_size': None, 'polarization_type': 'NONE', 'wave_no2': None, 'wave_res1': None, 'wave_res2': None, 'spec_flag': 'N'}, 'Image Constraints': {'duration': 0.46, 'greater_pixel_size': 1024.0, 'lesser_pixel_size': 1024.0, 'levels': '4096', 'image_type_id': 'FRAM'}, 'Cassini Mission Constraints': {'prime': 'Y', 'rev_no': '149', 'cassini_target_name': 'Iapetus', 'obs_name': 'ISS_149IA_IAPETUS157_PRIME', 'spacecraft_clock_count2': 1686170088.126, 'spacecraft_clock_count1': 1686170088.011, 'prime_inst_id': 'COISS', 'ert_sec2': 360915687.179, 'activity_name': 'IAPETUS', 'ert_sec1': 360915573.146}, 'Cassini ISS Constraints': {'DELAYED_READOUT_FLAG': 'NO', 'IMAGE_OBSERVATION_TYPE': 'SCIENCE', 'OPTICS_TEMPERATURE_front': 0.627499, 'INST_CMPRS_PARAM_GOB': -2147483648L, 'INST_CMPRS_PARAM_QF': -2147483648L, 'VALID_MAXIMUM_minimum_full_well_saturation_level': 4095L, 'LIGHT_FLOOD_STATE_FLAG': 'ON', 'MISSING_LINES': 0L, 'ANTIBLOOMING_STATE_FLAG': 'OFF', 'FILTER_NAME': 'RED  ,CL2', 'INST_CMPRS_RATE_actual_average': 2.482697, 'FILTER_TEMPERATURE': -0.468354, 'EXPECTED_MAXIMUM_full_well_DN': 0.185018, 'TELEMETRY_FORMAT_ID': 'S_N_ER_3', 'camera': 'N', 'INST_CMPRS_PARAM_MALGO': -2147483648L, 'MISSING_PACKET_FLAG': 'NO', 'GAIN_MODE_ID': '29 ELECTRONS PER DN', 'DATA_CONVERSION_TYPE': '12BIT', 'OPTICS_TEMPERATURE_rear': 1.820474, 'SHUTTER_STATE_ID': 'ENABLED', 'VALID_MAXIMUM_maximum_DN_saturation_level': 4095L, 'SHUTTER_MODE_ID': 'NACONLY', 'INST_CMPRS_RATIO': 6.444606, 'CALIBRATION_LAMP_STATE_FLAG': 'N/A', 'INST_CMPRS_RATE_expected_average': 3.21233, 'FILTER': 'RED', 'INST_CMPRS_TYPE': 'LOSSLESS', 'EXPECTED_MAXIMUM_max_DN': 0.203985, 'INST_CMPRS_PARAM_TB': -2147483648L}, 'Iapetus Surface Geometry': {'sub_observer_planetocentric_latitude': -80.13, 'Observer_longitude2': 41.472, 'Observer_longitude1': -131.232, 'coarsest_resolution1': 5.19282, 'sub_observer_IAU_longitude': 300.222, 'coarsest_resolution2': 269.02888, 'd_IAU_west_longitude': 86.352, 'IAU_west_longitude': 255.342, 'sub_observer_planetographic_latitude': -80.984, 'planetocentric_latitude2': 4.194, 'Observer_longitude': -44.879999999999995, 'planetocentric_latitude1': -76.873, 'sub_solar_planetographic_latitude': 12.945, 'd_solar_hour_angle': 180.0, 'emission2': 88.898, 'd_Observer_longitude': 86.352, 'phase1': 94.991, 'emission1': 1.084, 'range_to_body2': 866579.954, 'range_to_body1': 865886.822, 'center_resolution': 5.1697, 'solar_hour_angle': 180.0, 'phase2': 95.09, 'planetographic_latitude2': 4.598, 'planetographic_latitude1': -77.994, 'center_distance': 866599.797, 'IAU_west_longitude1': 168.99, 'IAU_west_longitude2': 341.694, 'solar_hour_angle1': 0.0, 'finest_resolution1': 5.16547, 'finest_resolution2': 5.16958, 'solar_hour_angle2': 360.0, 'incidence2': 177.831, 'center_phase_angle': 95.04, 'sub_solar_IAU_longitude': 253.146, 'incidence1': 7.753, 'sub_solar_planetocentric_latitude': 11.838}, 'Saturn Surface Geometry': {'sub_observer_planetocentric_latitude': 0.359, 'Observer_longitude2': None, 'Observer_longitude1': None, 'coarsest_resolution1': None, 'sub_observer_IAU_longitude': 327.261, 'coarsest_resolution2': None, 'd_IAU_west_longitude': None, 'IAU_west_longitude': None, 'sub_observer_planetographic_latitude': 0.441, 'planetocentric_latitude2': None, 'Observer_longitude': None, 'planetocentric_latitude1': None, 'sub_solar_planetographic_latitude': 11.994, 'd_solar_hour_angle': None, 'emission2': None, 'd_Observer_longitude': None, 'phase1': None, 'emission1': None, 'range_to_body2': None, 'range_to_body1': None, 'center_resolution': 21.2908, 'solar_hour_angle': None, 'phase2': None, 'planetographic_latitude2': None, 'planetographic_latitude1': None, 'center_distance': 3568988.32, 'IAU_west_longitude1': None, 'IAU_west_longitude2': None, 'solar_hour_angle1': None, 'finest_resolution1': None, 'finest_resolution2': None, 'solar_hour_angle2': None, 'incidence2': None, 'center_phase_angle': 74.66, 'sub_solar_IAU_longitude': 41.751, 'incidence1': None, 'sub_solar_planetocentric_latitude': 9.807}}
    #     self.assertEqual(detail['Cassini Mission Constraints'],expected['Cassini Mission Constraints'])
    #
    # def test__metadata_COISS_2111_1866071296_1866225122_W1866145657_1(self):
    #     opus_id = 'COISS_2111-1866071296_1866225122-W1866145657_1'
    #     detail, all_info = get_metadata(None, {}, opus_id=opus_id, fmt='raw')
    #     print(detail)
    #     print(detail['Cassini Mission Constraints'])
    #     expected = {'CASSINIobsname': "IOSIC_262RB_COMPLITB2001_SI",
    #                 'CASSINIactivityname': "COMPLITB2",
    #                 'CASSINImissionphasename': "Extended-Extended Mission",
    #                 'CASSINItargetcode': "RB (Ring B)",
    #                 'CASSINIrevno':	"262",
    #                 'CASSINIrevnoint': 262,
    #                 'CASSINIprimeinst': "ISS",
    #                 'CASSINIisprime': "Yes",
    #                 'CASSINIsequenceid': "S98",
    #                 'CASSINIspacecraftclockcount1': "1/1866145657.111",
    #                 'CASSINIspacecraftclockcount2': "1/1866145657.118",
    #                 'CASSINIspacecraftclockcountdec1': 1866145657.4335938,
    #                 'CASSINIspacecraftclockcountdec2': 1866145657.4609375,
    #                 'CASSINIert1': "2017-051T12:10:38.016",
    #                 'CASSINIert2': "2017-051T12:11:25.846",
    #                 'CASSINIertsec1': 540907875.016,
    #                 'CASSINIertsec2': 540907922.846}
    #     self.assertEqual(detail['Cassini Mission Constraints'], expected)
    #
    # def test__metadata_html__S_IMG_CO_ISS_1686170088_N(self):
    #     response = self.client.get('/opus/api/__detail/COISS_2111-1866071296_1866225122-W1866145657_1.html')
    #     print('hello1')
    #     print(response.content.strip())
    #     print('hello2')
    #
    #     self.assertEqual(response.status_code, 200)
    #     self.assertGreater(len(response.content), 2000)
    # #
    # def test__getImageSingle(self):
    #     response = self.client.get('/opus/api/image/thumb/S_IMG_CO_ISS_1686170143_N.html')
    #     content = response.content
    #     content = ' '.join([s.strip() for s in content.splitlines()]).strip()
    #     print(content)
    #     self.assertEqual(response.status_code, 200)
    #     self.assertGreater(len(content), 50)
    # #
    # def test__getImages(self):
    #     response = self.client.get('/opus/api/images/small.json?planet=Saturn')
    #     self.assertEqual(response.status_code, 200)
    #     self.assertGreater(len(response.content), 12000)
    #
    # def test__get_base_path_previews(self):
    #     opus_id = 'S_SPEC_CO_CIRS_1633035651_FP4'
    #     preview = get_base_path_previews(opus_id)
    #     self.assertEqual(preview, 'COCIRS_5xxx/')
    #
    # def test__getPage_no_selections(self):
    #     request = self.factory.get('some_request?', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    #     request.user = AnonymousUser()
    #     request.session = test_session()
    #     response = getPage(request)
    #     result_count = len(response[2])
    #     self.assertGreater(result_count, 99)
    #
    # def test__getPage_no_selections_big_limit(self):
    #     request = self.factory.get('some_request?limit=6000', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    #     request.user = AnonymousUser()
    #     request.session = test_session()
    #     response = getPage(request)
    #     result_count = len(response[2])
    #     self.assertGreater(result_count, 5999)
