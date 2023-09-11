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

    def test__api_get_data_and_images_no_meta(self):
        "[test_results.py] api_get_data_and_images: no META"
        request = self.factory.get('dummy')
        request.META = None
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /__api/dataimages.json'):
            api_get_data_and_images(request)

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

    def test__api_get_data_no_meta(self):
        "[test_results.py] api_get_data: no META"
        request = self.factory.get('dummy')
        request.META = None
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /api/data.json'):
            api_get_data(request, 'json')

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

    def test__api_get_metadata_no_meta(self):
        "[test_results.py] api_get_metadata: no META"
        request = self.factory.get('dummy')
        request.META = None
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /api/metadata/vg-iss-2-s-c4360845.json'):
            api_get_metadata(request, 'vg-iss-2-s-c4360845', 'json')

    def test__api_get_metadata_no_get(self):
        "[test_results.py] api_get_metadata: no GET"
        request = self.factory.get('/api/metadata/vg-iss-2-s-c4360845.json')
        request.GET = None
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /api/metadata/vg-iss-2-s-c4360845.json'):
            api_get_metadata(request, 'vg-iss-2-s-c4360845', 'json')


            #############################################
            ######### api_get_images UNIT TESTS #########
            #############################################

    def test__api_get_images_no_meta(self):
        "[test_results.py] api_get_images: no META"
        request = self.factory.get('dummy')
        request.META = None
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /api/images/None.json'):
            api_get_images(request, 'json')

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

    def test__api_get_images_by_size_no_meta(self):
        "[test_results.py] api_get_images_by_size: no META"
        request = self.factory.get('dummy')
        request.META = None
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /api/images/small.json'):
            api_get_images_by_size(request, 'small', 'json')

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

    def test__api_get_image_no_meta(self):
        "[test_results.py] api_get_image: no META"
        request = self.factory.get('dummy')
        request.META = None
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /api/image/small/vg-iss-2-s-c4360845.json'):
            api_get_image(request, 'vg-iss-2-s-c4360845', 'small', 'json')

    def test__api_get_image_no_get(self):
        "[test_results.py] api_get_image: no GET"
        request = self.factory.get('/api/image/small/vg-iss-2-s-c4360845.json')
        request.GET = None
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /api/image/small/vg-iss-2-s-c4360845.json'):
            api_get_image(request, 'vg-iss-2-s-c4360845', 'small', 'json')


            ############################################
            ######### api_get_files UNIT TESTS #########
            ############################################

    def test__api_get_files_no_meta(self):
        "[test_results.py] api_get_files: no META"
        request = self.factory.get('dummy')
        request.META = None
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /api/files/vg-iss-2-s-c4360845.json'):
            api_get_files(request, 'vg-iss-2-s-c4360845')

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

    def test__api_get_categories_for_opus_id_no_meta(self):
        "[test_results.py] api_get_categories_for_opus_id: no META"
        request = self.factory.get('dummy')
        request.META = None
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /api/categories/vg-iss-2-s-c4360845.json'):
            api_get_categories_for_opus_id(request, 'vg-iss-2-s-c4360845')

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

    def test__api_get_categories_for_search_no_meta(self):
        "[test_results.py] api_get_categories_for_search: no META"
        request = self.factory.get('dummy')
        request.META = None
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /api/categories.json'):
            api_get_categories_for_search(request)

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

    def test__api_get_product_types_for_opus_id_no_meta(self):
        "[test_results.py] api_get_product_types_for_opus_id: no META"
        request = self.factory.get('dummy')
        request.META = None
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /api/product_types/vg-iss-2-s-c4360845.json'):
            api_get_product_types_for_opus_id(request, 'vg-iss-2-s-c4360845')

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

    def test__api_get_product_types_for_search_no_meta(self):
        "[test_results.py] api_get_product_types_for_search: no META"
        request = self.factory.get('dummy')
        request.META = None
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /api/product_types.json'):
            api_get_product_types_for_search(request)

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

    def test__get_triggered_tables_no_selections(self):
        "[test_results.py] get_triggered_tables: no selections"
        partables = get_triggered_tables({}, {})
        expected = sorted(settings.BASE_TABLES)
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

    def test__get_triggered_tables_cocirs_volume_5408(self):
        "[test_results.py] get_triggered_tables: tables triggered by volume COCIRS_5408"
        q = QueryDict('bundleid=COCIRS_5408&qtype-bundleid=begins')
        expected = ['obs_general', 'obs_pds', 'obs_type_image',
                    'obs_wavelength', 'obs_profile',
                    'obs_surface_geometry_name',
                    'obs_surface_geometry',
                    'obs_ring_geometry',
                    'obs_mission_cassini', 'obs_instrument_cocirs']
        self._test_triggered_tables(q, expected)

    def test__get_triggered_tables_cocirs_volume_0406(self):
        "[test_results.py] get_triggered_tables: tables triggered by volume COCIRS_0406"
        q = QueryDict('bundleid=COCIRS_0406&qtype-bundleid=begins')
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
        q = QueryDict('planet=SATURN&bundleid=COISS&qtype-bundleid=begins')
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
        q = QueryDict('bundleid=COUVIS&qtype-bundleid=begins')
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
        q = QueryDict('bundleid=VGISS_6210')
        expected = ['obs_general', 'obs_pds', 'obs_type_image',
                    'obs_wavelength', 'obs_profile',
                    'obs_surface_geometry_name',
                    'obs_surface_geometry',
                    'obs_ring_geometry',
                    'obs_mission_voyager', 'obs_instrument_vgiss']
        self._test_triggered_tables(q, expected)

    def test__get_triggered_tables_vgpps_volume(self):
        "[test_results.py] get_triggered_tables: tables triggered by volume VG_2801"
        q = QueryDict('bundleid=VG_2801')
        expected = ['obs_general', 'obs_pds', 'obs_type_image',
                    'obs_wavelength', 'obs_profile',
                    'obs_surface_geometry_name',
                    'obs_surface_geometry',
                    'obs_ring_geometry',
                    'obs_mission_voyager']
        self._test_triggered_tables(q, expected)

    def test__get_triggered_tables_vguvs_volume(self):
        "[test_results.py] get_triggered_tables: tables triggered by volume VG_2802"
        q = QueryDict('bundleid=VG_2802')
        expected = ['obs_general', 'obs_pds', 'obs_type_image',
                    'obs_wavelength', 'obs_profile',
                    'obs_surface_geometry_name',
                    'obs_surface_geometry',
                    'obs_ring_geometry',
                    'obs_mission_voyager']
        self._test_triggered_tables(q, expected)

    def test__get_triggered_tables_vgrss_volume(self):
        "[test_results.py] get_triggered_tables: tables triggered by volume VG_2803"
        q = QueryDict('bundleid=VG_2803')
        expected = ['obs_general', 'obs_pds', 'obs_type_image',
                    'obs_wavelength', 'obs_profile',
                    'obs_surface_geometry_name',
                    'obs_surface_geometry',
                    'obs_ring_geometry',
                    'obs_mission_voyager']
        self._test_triggered_tables(q, expected)

    def test__get_triggered_tables_vgiss_prof_volume(self):
        "[test_results.py] get_triggered_tables: tables triggered by volume VG_2810"
        q = QueryDict('bundleid=VG_2810')
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

    def test__get_triggered_tables_nhmvic_cached(self):
        "[test_results.py] get_triggered_tables: tables triggered by instrument NHMVIC cached"
        q = QueryDict('instrument=New+Horizons+MVIC')
        expected = ['obs_general', 'obs_pds', 'obs_type_image',
                    'obs_wavelength', 'obs_profile',
                    'obs_surface_geometry_name',
                    'obs_surface_geometry',
                    'obs_ring_geometry',
                    'obs_mission_new_horizons',
                    'obs_instrument_nhmvic']
        self._test_triggered_tables(q, expected)
        self._test_triggered_tables(q, expected)
        self._test_triggered_tables(q, expected)
        self._test_triggered_tables(q, expected)
