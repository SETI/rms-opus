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

class test_session(dict):
    """
    extends a dict object and adds a session_key attribute for use in this test suite

    because in django tests:

    session and authentication attributes must be supplied by the test itself if required for the view to function properly.
    ( via http://stackoverflow.com/questions/14714585/using-session-object-in-django-unit-test )

    in most cases a request.session = {} in the test itself would suffice
    but in user_collections views we also want to receive a string from request.session.session_key
    because that's how user collections tables are named

    extends the dict because that is how real sessions are interacted with

    """
    session_key = 'test_key'
    has_session = True


class downloadsTests(TestCase):

    session_id = test_session().session_key  #
    c = Client()
    colls_table_name = 'colls_test_key'
    session_id = test_session().session_key
    # factory = RequestFactory()

    def emptycollection(self):
        test_db = settings.DATABASES['default']['TEST']['NAME']
        cursor = connection.cursor()
        table_name = 'colls_' + test_session().session_key
        query = 'delete from %s.%s' % (test_db, table_name)
        print query
        cursor.execute(query)


    def test__get_download_info_COVIMS(self):
        self.emptycollection()
        ring_obs_id_list = 'S_CUBE_CO_VIMS_1638723713_VIS'
        bulk_add_to_collection(ring_obs_id_list, self.session_id)

        product_types = ['RAW_SPECTRAL_IMAGE_CUBE']
        previews = ['med']
        size, file_count =  get_download_info(product_types, previews, self.colls_table_name)
        print size, file_count
        self.assertEqual(size, 3198205)
        self.assertEqual(file_count, 6)

    def test__get_download_info_VGISS(self):
        self.emptycollection()
        ring_obs_id_list = 'N_IMG_VG2_ISS_1120000_W'
        bulk_add_to_collection(ring_obs_id_list, self.session_id)
        product_types = ['CALIBRATED_IMAGE']
        previews = ['small']
        size, file_count =  get_download_info(product_types, previews, self.colls_table_name)
        print size, file_count
        self.assertEqual(size, 1290929)
        self.assertEqual(file_count, 3)

    def test__get_download_info_empty_product_types(self):
        self.emptycollection()
        ring_obs_id_list = 'S_IMG_CO_ISS_1680806066_N'
        bulk_add_to_collection(ring_obs_id_list, self.session_id)
        product_types = None
        previews = ['Full']
        size, file_count =  get_download_info(product_types, previews, self.colls_table_name)
        print size, file_count
        self.assertEqual(size, 19750)
        self.assertEqual(file_count, 1)

    def test__get_download_info_COCIRS(self):
        self.emptycollection()
        ring_obs_id_list = 'S_SPEC_CO_CIRS_1630456943_FP1'
        bulk_add_to_collection(ring_obs_id_list, self.session_id)

        product_types = 'CALIBRATED_SPECTRUM'
        previews = None
        size, file_count =  get_download_info(product_types, previews, self.colls_table_name)
        print size, file_count
        self.assertEqual(size, 11766917)
        self.assertEqual(file_count, 2)

    def test__get_download_info_browse_images_being_counted(self):
        self.emptycollection()
        ring_obs_id_list = ['S_IMG_CO_ISS_1692988072_N','S_IMG_CO_ISS_1692988234_N','S_IMG_CO_ISS_1692988460_N','S_IMG_CO_ISS_1692988500_N']
        bulk_add_to_collection(ring_obs_id_list, self.session_id)
        previews = None
        product_types=['CALIBRATED']

        size1, file_count1 = get_download_info(product_types, previews, self.colls_table_name)

        product_types2=['RAW_IMAGE']
        size2, file_count2 = get_download_info(product_types2, previews, self.colls_table_name)
        # tf?
        self.assertNotEqual(size1, size2)
        self.assertNotEqual(file_count1, file_count2)

    # get_download_info(
    def test__get_download_info_COISS_CALIBRATED(self):
        self.emptycollection()
        ring_obs_id_list = ['S_IMG_CO_ISS_1692988072_N','S_IMG_CO_ISS_1692988234_N','S_IMG_CO_ISS_1692988460_N','S_IMG_CO_ISS_1692988500_N']
        bulk_add_to_collection(ring_obs_id_list, self.session_id)

        ring_obs_ids = 'S_IMG_CO_ISS_1680806066_N'
        product_types = ['CALIBRATED']
        previews = None
        size, file_count =  get_download_info(product_types, previews, self.colls_table_name)
        print size, file_count
        self.assertEqual(size, 16905314)
        self.assertEqual(file_count, 16)

    def test__get_download_info_COISS_RAW_IMAGE(self):
        self.emptycollection()
        ring_obs_id_list = 'S_IMG_CO_ISS_1680806066_N'
        bulk_add_to_collection(ring_obs_id_list, self.session_id)

        product_types = ['RAW_IMAGE']
        previews = None
        size, file_count =  get_download_info(product_types, previews, self.colls_table_name)
        print size, file_count
        self.assertEqual(size, 2131631)

    def test__get_download_info_COISS_both_products(self):
        self.emptycollection()
        ring_obs_id_list = 'S_IMG_CO_ISS_1680806066_N'
        bulk_add_to_collection(ring_obs_id_list, self.session_id)

        product_types = ['RAW_IMAGE','CALIBRATED']
        previews = 'none'
        size, file_count =  get_download_info(product_types, previews, self.colls_table_name)
        print size, file_count
        self.assertEqual(size, 6357972)


    def test__get_file_path(self):
        f = settings.FILE_PATH + 'coiss_2xxx/coiss_2069/img.jpg'
        print 'FILE_PATH = %s ' % settings.FILE_PATH
        print 'sent %s' % f
        got = get_file_path(f)
        print 'got %s' % got
        self.assertEqual(got, 'coiss_2069/img.jpg')

    def test__get_file_path_url(self):
        f = 'http://pds-rings.seti.org/coiss_2xxx/coiss_2069/img.jpg'
        got = get_file_path(f)
        self.assertEqual(got, 'coiss_2069/img.jpg')
