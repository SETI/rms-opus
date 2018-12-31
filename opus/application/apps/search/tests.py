# search/tests.py

# These tests require the following volumes, imported in this order:
# COISS_2002,COISS_2008,COISS_2111,COUVIS_0002,GO_0017,VGISS_6210,VGISS_8201,HSTI1_2003

import sys
from unittest import TestCase

from django.apps import apps
from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.db.models import Count
from django.http import QueryDict
from django.test.client import Client

from search.views import *
from tools.db_utils import MYSQL_TABLE_NOT_EXISTS

settings.CACHE_BACKEND = 'dummy:///'

class searchTests(TestCase):

    # Clean up the user_searches and cache tables before and after running
    # the tests so that the results from set_user_search_number and
    # get_user_query_table are predictable.

    def _empty_user_searches(self):
        cursor = connection.cursor()
        cursor.execute('DELETE FROM user_searches')
        cursor.execute("ALTER TABLE user_searches AUTO_INCREMENT = 1")
        cursor.execute("SHOW TABLES LIKE %s" , ["cache_%"])
        for row in cursor:
            q = 'DROP TABLE ' + row[0]
            print(q)
            cursor.execute(q)
        cache.clear()
        cache._cache.flush_all()  # clears memcache hopefully only on this port!

    def setUp(self):
        self._empty_user_searches()
        sys.tracebacklimit = 0 # default: 1000
        logging.disable(logging.ERROR)

    def tearDown(self):
        self._empty_user_searches()
        sys.tracebacklimit = 1000 # default: 1000
        logging.disable(logging.NOTSET)


            ##################################################
            ######### api_normalize_input UNIT TESTS #########
            ##################################################

    def test__api_normalize_input_no_request(self):
        "api_normalize_input: no request"
        with self.assertRaises(Http404):
            api_normalize_input(None)

    def test__api_normalize_input_no_get(self):
        "api_normalize_input: no GET"
        c = Client()
        response = c.get('/__api/normalizeinput.json')
        request = response.wsgi_request
        request.GET = None
        with self.assertRaises(Http404):
            api_normalize_input(request)


            ########################################################
            ######### api_string_search_choices UNIT TESTS #########
            ########################################################

    def test__api_string_search_choices_no_request(self):
        "api_string_search_choices: no request"
        with self.assertRaises(Http404):
            api_string_search_choices(None, 'slug')

    def test__api_string_search_choices_no_get(self):
        "api_string_search_choices: no GET"
        c = Client()
        response = c.get('/__api/stringsearchchoices/volumeid.json')
        request = response.wsgi_request
        request.GET = None
        with self.assertRaises(Http404):
            api_string_search_choices(request, 'slug')


            ###################################################
            ######### url_to_search_params UNIT TESTS #########
            ###################################################

    ####################
    ### TIME PARSING ###
    ####################

    def test__url_to_search_params_times_yd(self):
        "url_to_search_params: date parsing in YYYY-DDD format"
        # Using old slug name
        q = QueryDict('timesec1=2000-023T06:00:00&timesec2=2000-024T06:00:00')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_general.time1': [1922432.0],
                        'obs_general.time2': [2008832.0]}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)

    def test__url_to_search_params_times_ymd(self):
        "url_to_search_params: date parsing in YYYY-MM-DD format"
        # Using old slug name
        q = QueryDict('timesec1=2000-01-23T06:00:00&timesec2=2000-01-24T06:00:00')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_general.time1': [1922432.0],
                        'obs_general.time2': [2008832.0]}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)

    def test__url_to_search_params_times_expanded(self):
        "url_to_search_params: date parsing in YYYY MMM DD format"
        q = QueryDict('time1=2000+JAN+23+6:00:00&time2=2000+January+24+6:00:00')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_general.time1': [1922432.0],
                        'obs_general.time2': [2008832.0]}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)

    def test__url_to_search_params_times_expanded_2(self):
        "url_to_search_params: date parsing in YYYY/MM/DD format"
        q = QueryDict('time1=2000/1/23+06:00:00.000&time2=2000/01/24+06:00')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_general.time1': [1922432.0],
                        'obs_general.time2': [2008832.0]}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)

    def test__url_to_search_params_times_bad(self):
        "url_to_search_params: bad date format"
        q = QueryDict('time1=2000 XXX 01')
        (selections, extras) = url_to_search_params(q)
        self.assertIsNone(selections)

    def test__url_to_search_params_times_bad_2(self):
        "url_to_search_params: bad date format #2"
        q = QueryDict('time1=2000/13/23+06:00:00')
        (selections, extras) = url_to_search_params(q)
        self.assertIsNone(selections)

    def test__url_to_search_params_times_bad_3(self):
        "url_to_search_params: bad date format #3"
        q = QueryDict('time1=2000')
        (selections, extras) = url_to_search_params(q)
        self.assertIsNone(selections)

    def test__url_to_search_params_times_bad_4(self):
        "url_to_search_params: bad date format #4"
        q = QueryDict('time1=06:00:00')
        (selections, extras) = url_to_search_params(q)
        self.assertIsNone(selections)


    ####################
    ### BASIC RANGES ###
    ####################

    def test__url_to_search_params_left_side(self):
        "url_to_search_params: range with min only, max missing value"
        q = QueryDict('RINGGEOphase1=80.1&RINGGEOphase2=')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_ring_geometry.phase1': [80.1]}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)

    def test__url_to_search_params_left_side_2(self):
        "url_to_search_params: range with min only, max missing entirely #2"
        q = QueryDict('RINGGEOphase1=80.1')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_ring_geometry.phase1': [80.1]}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)

    def test__url_to_search_params_left_side_ignore_ui_slugs(self):
        "url_to_search_params: range with min only, max missing value, ignored UI slugs"
        q = QueryDict('RINGGEOphase1=80.1&widgets=fred,ethel&RINGGEOphase2=&reqno=5')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_ring_geometry.phase1': [80.1]}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)

    def test__url_to_search_params_right_side(self):
        "url_to_search_params: range with max only, min missing value"
        q = QueryDict('RINGGEOphase1=&RINGGEOphase2=90.5')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_ring_geometry.phase2': [90.5]}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)

    def test__url_to_search_params_right_side_2(self):
        "url_to_search_params: range with max only, min missing entirely"
        q = QueryDict('RINGGEOphase2=90.5')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_ring_geometry.phase2': [90.5]}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)

    def test__url_to_search_params_both_side(self):
        "url_to_search_params: range with both min and max"
        q = QueryDict('RINGGEOphase1=0&RINGGEOphase2=355.201')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_ring_geometry.phase1': [0.],
                        'obs_ring_geometry.phase2': [355.201]}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)

    def test__url_to_search_params_both_side_any(self):
        "url_to_search_params: range with qtype=any"
        q = QueryDict('RINGGEOphase1=0&RINGGEOphase2=355.201&qtype-RINGGEOphase=any')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_ring_geometry.phase1': [0.],
                        'obs_ring_geometry.phase2': [355.201]}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {'obs_ring_geometry.phase': ['any']}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)

    def test__url_to_search_params_both_side_all(self):
        "url_to_search_params: range with qtype=all"
        q = QueryDict('RINGGEOphase1=0&RINGGEOphase2=355.201&qtype-RINGGEOphase=all')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_ring_geometry.phase1': [0.],
                        'obs_ring_geometry.phase2': [355.201]}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {'obs_ring_geometry.phase': ['all']}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)

    def test__url_to_search_params_both_side_only(self):
        "url_to_search_params: range with qtype=only"
        q = QueryDict('RINGGEOphase1=0&RINGGEOphase2=355.201&qtype-RINGGEOphase=only')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_ring_geometry.phase1': [0.],
                        'obs_ring_geometry.phase2': [355.201]}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {'obs_ring_geometry.phase': ['only']}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)

    #######################
    ### NUMERIC FORMATS ###
    #######################

    def test__url_to_search_params_numeric_spaces(self):
        "url_to_search_params: numeric with spaces"
        q = QueryDict('observationduration1=+1+0+')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_general.observation_duration1': [10.]}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)

    def test__url_to_search_params_numeric_commas(self):
        "url_to_search_params: numeric with commas"
        q = QueryDict('observationduration1=,100,000.0,')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_general.observation_duration1': [100000.]}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)

    ######################
    ### STRING FORMATS ###
    ######################

    def test__url_to_search_params_stringsearch(self):
        "url_to_search_params: search on a string value"
        q = QueryDict('note=Incomplete')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_pds.note': ['Incomplete']}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)

    def test__url_to_search_params_stringsearch_contains(self):
        "url_to_search_params: string search with qtype=contains"
        q = QueryDict('note=Incomplete&qtype-note=contains')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_pds.note': ['Incomplete']}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {'obs_pds.note': ['contains']}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)

    def test__url_to_search_params_string_comma(self):
        "url_to_search_params: string with commas"
        q = QueryDict('note=,Note1,Note2,&qtype-note=ends')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_pds.note': [',Note1,Note2,']}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {'obs_pds.note': ['ends']}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)

    #############
    ### MULTS ###
    #############

    def test__url_to_search_params_mults_uc(self):
        "url_to_search_params: mults upper case"
        q = QueryDict('planet=SATURN&target=PAN')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_general.target_name': ['PAN'],
                        'obs_general.planet_id': ['SATURN']}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)

    def test__url_to_search_params_mults_lc(self):
        "url_to_search_params: mults lower case"
        q = QueryDict('planet=saturn&target=pan')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_general.target_name': ['pan'],
                        'obs_general.planet_id': ['saturn']}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)

    def test__url_to_search_params_mults_plus(self):
        "url_to_search_params: mults using a + to mean space"
        q = QueryDict('instrument=Cassini+ISS')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_general.instrument_id': ['Cassini ISS']}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)

    def test__url_to_search_params_mults_2B(self):
        "url_to_search_params: mults using %2B to mean plus"
        q = QueryDict('COISSfilter=BL1%2BGRN')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_instrument_coiss.combined_filter': ['BL1+GRN']}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)

    def test__url_to_search_params_with_join(self):
        "url_to_search_params: mults from different tables"
        q = QueryDict('planet=Saturn&RINGGEOringradius1=60000')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_general.planet_id': ['Saturn'],
                        'obs_ring_geometry.ring_radius1': [60000]}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)

    def test__url_to_search_params_stringmultmix(self):
        "url_to_search_params: mults and string searches at the same time"
        q = QueryDict('planet=SATURN&target=PAN&note=Incomplete&qtype-note=begins')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_general.planet_id': ['SATURN'],
                        'obs_general.target_name': ['PAN'],
                        'obs_pds.note': ['Incomplete']}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {'obs_pds.note': ['begins']}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)

    ##################
    ### SORT ORDER ###
    ##################

    def test__url_to_search_params_from_sort_default(self):
        "url_to_search_params: default sort order"
        q = QueryDict('planet=Saturn')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_general.planet_id': ['Saturn']}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)

    def test__url_to_search_params_from_sort_blank(self):
        "url_to_search_params: blank sort order"
        q = QueryDict('planet=Saturn&order=')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_general.planet_id': ['Saturn']}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)

    def test__url_to_search_params_from_sort_bad(self):
        "url_to_search_params: bad sort order"
        q = QueryDict('planet=Saturn&order=time1,-fredethel')
        (selections, extras) = url_to_search_params(q)
        sel_expected = None
        extras_expected = None
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras, extras_expected)

    def test__url_to_search_params_from_sort_opusid(self):
        "url_to_search_params: sort on opusid"
        q = QueryDict('planet=Saturn&order=opusid')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_general.planet_id': ['Saturn']}
        order_expected = (['obs_general.opus_id'],
                          [False])
        qtypes_expected = {}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)

    def test__url_to_search_params_from_sort_opusid_desc(self):
        "url_to_search_params: sort on descending opusid"
        q = QueryDict('planet=Saturn&order=-opusid')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_general.planet_id': ['Saturn']}
        order_expected = (['obs_general.opus_id'],
                          [True])
        qtypes_expected = {}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)

    def test__url_to_search_params_from_sort_multi(self):
        "url_to_search_params: sort on descending opusid"
        q = QueryDict('planet=Saturn&order=-opusid,RINGGEOphase1,-volumeid')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_general.planet_id': ['Saturn']}
        order_expected = (['obs_general.opus_id', 'obs_ring_geometry.phase1',
                           'obs_pds.volume_id'],
                          [True, False, True])
        qtypes_expected = {}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)


    # ##  set_user_search_number
    # def test__set_user_search_number(self):
    #     no = set_user_search_number(self.selections)
    #     self.assertTrue(no)
    #
    # def test__set_user_search_number_with_times(self):
    #     selections = {'obs_general.planet_id': ['Saturn'], 'obs_general.time_sec2': ['2009-12-28'], 'obs_general.time1': ['2009-12-23']}
    #     search_no = set_user_search_number(selections)
    #     print(search_no)
    #     self.assertGreater(len(str(search_no)), 0)
    #
    #
    # def test__set_user_search_number_2_planets(self):
    #     selections = {}
    #     selections['obs_general.planet_id'] = ['Saturn']
    #     no = set_user_search_number(selections)
    #     print(no)
    #     # breaking this, this test needs to see if there are any rows in the table
    #     self.assertGreater(no, 0)
    #


            ##############################################
            ######### get_range_query UNIT TESTS #########
            ##############################################

    def test__range_query_single_col_range_left_side(self):
        "range_query: single column range with min only"
        selections = {'obs_ring_geometry.ring_center_phase1': [20.0]}
        sql, params = get_range_query(selections, 'obs_ring_geometry.ring_center_phase1', [])
        print(sql)
        print(params)
        expected = '`obs_ring_geometry`.`ring_center_phase` >= %s'
        expected_params = [20.0]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__range_query_single_col_range_right_side(self):
        "range_query: single column range with max only"
        selections = {'obs_ring_geometry.ring_center_phase2': [180.0]}
        sql, params = get_range_query(selections, 'obs_ring_geometry.ring_center_phase1', [])
        print(sql)
        print(params)
        expected = '`obs_ring_geometry`.`ring_center_phase` <= %s'
        expected_params = [180.0]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__range_query_single_col_range_both_side(self):
        "range_query: single column range with both min and max"
        selections = {'obs_ring_geometry.ring_center_phase2': [180.0],
                      'obs_ring_geometry.ring_center_phase1': [20.0]}
        sql, params = get_range_query(selections, 'obs_ring_geometry.ring_center_phase1', ['all'])
        print(sql)
        print(params)
        expected = '`obs_ring_geometry`.`ring_center_phase` >= %s AND `obs_ring_geometry`.`ring_center_phase` <= %s'
        expected_params = [20.0,180.0]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__range_query_single_col_range_all(self):
        "range_query: single column range with bogus qtype=all"
        selections = {'obs_ring_geometry.ring_center_phase2': [180.0],
                      'obs_ring_geometry.ring_center_phase1': [20.0]}
        sql, params = get_range_query(selections, 'obs_ring_geometry.ring_center_phase1', ['all'])
        print(sql)
        print(params)
        expected = '`obs_ring_geometry`.`ring_center_phase` >= %s AND `obs_ring_geometry`.`ring_center_phase` <= %s'
        expected_params = [20.0,180.0]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__range_query_any_left_side(self):
        "range_query: long range with qtype=any, min only"
        selections = {'obs_ring_geometry.ring_radius1': [10000.]}
        sql, params = get_range_query(selections, 'obs_ring_geometry.ring_radius1', ['any'])
        print(sql)
        print(params)
        # Effectively 10000 to inf
        expected = '`obs_ring_geometry`.`ring_radius2` >= %s'
        expected_params = [10000.0]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__range_query_any_right_side(self):
        "range_query: long range with qtype=any, max only"
        selections = {'obs_ring_geometry.ring_radius2': [40000.]}
        sql, params = get_range_query(selections, 'obs_ring_geometry.ring_radius1', ['any'])
        print(sql)
        print(params)
        # Effectively -inf to 40000
        expected = '`obs_ring_geometry`.`ring_radius1` <= %s'
        expected_params = [40000.0]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__range_query_any_both_side(self):
        "range_query: long range with qtype=any, both min and max"
        selections = {'obs_ring_geometry.ring_radius1': [10000.],
                      'obs_ring_geometry.ring_radius2': [40000.]}
        sql, params = get_range_query(selections, 'obs_ring_geometry.ring_radius1', ['any'])
        print(sql)
        print(params)
        # 10000 to 40000
        expected = '`obs_ring_geometry`.`ring_radius2` >= %s AND `obs_ring_geometry`.`ring_radius1` <= %s'
        expected_params = [10000.0,40000.]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__range_query_all_left_side(self):
        "range_query: long range with qtype=all, min only"
        selections = {'obs_ring_geometry.ring_radius1': [10000.]}
        sql, params = get_range_query(selections, 'obs_ring_geometry.ring_radius1', ['all'])
        print(sql)
        print(params)
        # Effectively 10000 to inf
        expected = '`obs_ring_geometry`.`ring_radius1` <= %s'
        expected_params = [10000.0]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__range_query_all_right_side(self):
        "range_query: long range with qtype=all, max only"
        selections = {'obs_ring_geometry.ring_radius2': [40000.]}
        sql, params = get_range_query(selections, 'obs_ring_geometry.ring_radius1', ['all'])
        print(sql)
        print(params)
        # Effectively -inf to 40000
        expected = '`obs_ring_geometry`.`ring_radius2` >= %s'
        expected_params = [40000.0]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__range_query_all_both_side(self):
        "range_query: long range with qtype=all, both min and max"
        selections = {'obs_ring_geometry.ring_radius1': [10000.],
                      'obs_ring_geometry.ring_radius2': [40000.]}
        sql, params = get_range_query(selections, 'obs_ring_geometry.ring_radius1', ['all'])
        print(sql)
        print(params)
        # 10000 to 40000
        expected = '`obs_ring_geometry`.`ring_radius1` <= %s AND `obs_ring_geometry`.`ring_radius2` >= %s'
        expected_params = [10000.0,40000.]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__range_query_only_left_side(self):
        "range_query: long range with qtype=only, min only"
        selections = {'obs_ring_geometry.ring_radius1': [10000.]}
        sql, params = get_range_query(selections, 'obs_ring_geometry.ring_radius1', ['only'])
        print(sql)
        print(params)
        # Effectively 10000 to inf
        expected = '`obs_ring_geometry`.`ring_radius1` >= %s'
        expected_params = [10000.0]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__range_query_only_right_side(self):
        "range_query: long range with qtype=only, max only"
        selections = {'obs_ring_geometry.ring_radius2': [40000.]}
        sql, params = get_range_query(selections, 'obs_ring_geometry.ring_radius1', ['only'])
        print(sql)
        print(params)
        # Effectively -inf to 40000
        expected = '`obs_ring_geometry`.`ring_radius2` <= %s'
        expected_params = [40000.0]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__range_query_only_both_side(self):
        "range_query: long range with qtype=only, both min and max"
        selections = {'obs_ring_geometry.ring_radius1': [10000.],
                      'obs_ring_geometry.ring_radius2': [40000.]}
        sql, params = get_range_query(selections, 'obs_ring_geometry.ring_radius1', ['only'])
        print(sql)
        print(params)
        # 10000 to 40000
        expected = '`obs_ring_geometry`.`ring_radius1` >= %s AND `obs_ring_geometry`.`ring_radius2` <= %s'
        expected_params = [10000.0,40000.]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)


            ###################################################
            ######### get_longitude_query UNIT TESTS #########
            ###################################################

    def test__longitude_query_single_col_range_left_side(self):
        "longitude_query: single column long range with min only"
        selections = {'obs_ring_geometry.sub_solar_ring_long1': [20.0]}
        sql, params = get_longitude_query(selections, 'obs_ring_geometry.sub_solar_ring_long1', [])
        print(sql)
        print(params)
        expected = None # Can't have one-sided longitude queries
        expected_params = None
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__longitude_query_single_col_range_right_side(self):
        "longitude_query: single column long range with max only"
        selections = {'obs_ring_geometry.sub_solar_ring_long2': [180.0]}
        sql, params = get_longitude_query(selections, 'obs_ring_geometry.sub_solar_ring_long1', [])
        print(sql)
        print(params)
        expected = None # Can't have one-sided longitude queries
        expected_params = None
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__longitude_query_single_col_range_both_side(self):
        "longitude_query: single column long range with both min and max"
        selections = {'obs_ring_geometry.sub_solar_ring_long2': [180.0],
                      'obs_ring_geometry.sub_solar_ring_long1': [20.0]}
        sql, params = get_longitude_query(selections, 'obs_ring_geometry.sub_solar_ring_long1', ['all'])
        print(sql)
        print(params)
        expected = '(`obs_ring_geometry`.`sub_solar_ring_long` >= %s AND `obs_ring_geometry`.`sub_solar_ring_long` <= %s)'
        expected_params = [20.0,180.0]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__longitude_query_single_col_range_all(self):
        "longitude_query: single column long range with bogus qtype=all"
        selections = {'obs_ring_geometry.sub_solar_ring_long2': [180.0],
                      'obs_ring_geometry.sub_solar_ring_long1': [20.0]}
        sql, params = get_longitude_query(selections, 'obs_ring_geometry.sub_solar_ring_long1', ['all'])
        print(sql)
        print(params)
        expected = '(`obs_ring_geometry`.`sub_solar_ring_long` >= %s AND `obs_ring_geometry`.`sub_solar_ring_long` <= %s)'
        expected_params = [20.0,180.0]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__longitude_query_any_left_side(self):
        "longitude_query: long range with qtype=any, min only"
        selections = {'obs_ring_geometry.J2000_longitude1': [240.]}
        sql, params = get_longitude_query(selections, 'obs_ring_geometry.J2000_longitude1', ['any'])
        print(sql)
        print(params)
        expected = None # Can't have one-sided longitude queries
        expected_params = None
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__longitude_query_any_right_side(self):
        "longitude_query: long range with qtype=any, max only"
        selections = {'obs_ring_geometry.J2000_longitude2': [310.5]}
        sql, params = get_longitude_query(selections, 'obs_ring_geometry.J2000_longitude1', ['any'])
        print(sql)
        print(params)
        expected = None # Can't have one-sided longitude queries
        expected_params = None
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__longitude_query_any_both_side(self):
        "longitude_query: long range with qtype=any, both min and max"
        selections = {'obs_ring_geometry.J2000_longitude1': [240.],
                      'obs_ring_geometry.J2000_longitude2': [310.5]}
        sql, params = get_longitude_query(selections, 'obs_ring_geometry.J2000_longitude1', ['any'])
        print(sql)
        print(params)
        # 240 to 310.5
        expected = 'ABS(MOD(%s - obs_ring_geometry.J2000_longitude + 540., 360.) - 180.) <= %s + obs_ring_geometry.d_j2000_longitude'
        expected_params = [275.25, 35.25]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__longitude_query_all_left_side(self):
        "longitude_query: long range with qtype=all, min only"
        selections = {'obs_ring_geometry.J2000_longitude1': [240.]}
        sql, params = get_longitude_query(selections, 'obs_ring_geometry.J2000_longitude1', ['all'])
        print(sql)
        print(params)
        expected = None # Can't have one-sided longitude queries
        expected_params = None
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__longitude_query_all_right_side(self):
        "longitude_query: long range with qtype=all, max only"
        selections = {'obs_ring_geometry.J2000_longitude2': [310.5]}
        sql, params = get_longitude_query(selections, 'obs_ring_geometry.J2000_longitude1', ['all'])
        print(sql)
        print(params)
        expected = None # Can't have one-sided longitude queries
        expected_params = None
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__longitude_query_all_both_side(self):
        "longitude_query: long range with qtype=all, both min and max"
        selections = {'obs_ring_geometry.J2000_longitude1': [240.],
                      'obs_ring_geometry.J2000_longitude2': [310.5]}
        sql, params = get_longitude_query(selections, 'obs_ring_geometry.J2000_longitude1', ['all'])
        print(sql)
        print(params)
        # 240 to 310.5
        expected = 'ABS(MOD(%s - obs_ring_geometry.J2000_longitude + 540., 360.) - 180.) <= obs_ring_geometry.d_j2000_longitude - %s'
        expected_params = [275.25, 35.25]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__longitude_query_only_left_side(self):
        "longitude_query: long range with qtype=only, min only"
        selections = {'obs_ring_geometry.J2000_longitude1': [240.]}
        sql, params = get_longitude_query(selections, 'obs_ring_geometry.J2000_longitude1', ['only'])
        print(sql)
        print(params)
        expected = None # Can't have one-sided longitude queries
        expected_params = None
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__longitude_query_only_right_side(self):
        "longitude_query: long range with qtype=only, max only"
        selections = {'obs_ring_geometry.J2000_longitude2': [310.5]}
        sql, params = get_longitude_query(selections, 'obs_ring_geometry.J2000_longitude1', ['only'])
        print(sql)
        print(params)
        expected = None # Can't have one-sided longitude queries
        expected_params = None
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__longitude_query_only_both_side(self):
        "longitude_query: long range with qtype=only, both min and max"
        selections = {'obs_ring_geometry.J2000_longitude1': [240.],
                      'obs_ring_geometry.J2000_longitude2': [310.5]}
        sql, params = get_longitude_query(selections, 'obs_ring_geometry.J2000_longitude1', ['only'])
        print(sql)
        print(params)
        # 240 to 310.5
        expected = 'ABS(MOD(%s - obs_ring_geometry.J2000_longitude + 540., 360.) - 180.) <= %s - obs_ring_geometry.d_j2000_longitude'
        expected_params = [275.25, 35.25]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__longitude_query_single_col_range_both_side_wrap(self):
        "longitude_query: single column long range with both min and max"
        selections = {'obs_ring_geometry.sub_solar_ring_long1': [180.0],
                      'obs_ring_geometry.sub_solar_ring_long2': [20.0]}
        sql, params = get_longitude_query(selections, 'obs_ring_geometry.sub_solar_ring_long1', ['all'])
        print(sql)
        print(params)
        expected = '(`obs_ring_geometry`.`sub_solar_ring_long` >= %s OR `obs_ring_geometry`.`sub_solar_ring_long` <= %s)'
        expected_params = [180.0,20.0]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__longitude_query_any_both_side_wrap(self):
        "longitude_query: long range with qtype=any, both min and max"
        selections = {'obs_ring_geometry.J2000_longitude1': [240.],
                      'obs_ring_geometry.J2000_longitude2': [30.5]}
        sql, params = get_longitude_query(selections, 'obs_ring_geometry.J2000_longitude1', ['any'])
        print(sql)
        print(params)
        # 240 to 30.5
        expected = 'ABS(MOD(%s - obs_ring_geometry.J2000_longitude + 540., 360.) - 180.) <= %s + obs_ring_geometry.d_j2000_longitude'
        expected_params = [315.25, 75.25]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__longitude_query_all_both_side_wrap(self):
        "longitude_query: long range with qtype=all, both min and max"
        selections = {'obs_ring_geometry.J2000_longitude1': [240.],
                      'obs_ring_geometry.J2000_longitude2': [30.5]}
        sql, params = get_longitude_query(selections, 'obs_ring_geometry.J2000_longitude1', ['all'])
        print(sql)
        print(params)
        # 240 to 30.5
        expected = 'ABS(MOD(%s - obs_ring_geometry.J2000_longitude + 540., 360.) - 180.) <= obs_ring_geometry.d_j2000_longitude - %s'
        expected_params = [315.25, 75.25]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__longitude_query_only_both_side_wrap(self):
        "longitude_query: long range with qtype=only, both min and max"
        selections = {'obs_ring_geometry.J2000_longitude1': [240.],
                      'obs_ring_geometry.J2000_longitude2': [30.5]}
        sql, params = get_longitude_query(selections, 'obs_ring_geometry.J2000_longitude1', ['only'])
        print(sql)
        print(params)
        # 240 to 30.5
        expected = 'ABS(MOD(%s - obs_ring_geometry.J2000_longitude + 540., 360.) - 180.) <= %s - obs_ring_geometry.d_j2000_longitude'
        expected_params = [315.25, 75.25]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)


            ###############################################
            ######### get_string_query UNIT TESTS #########
            ###############################################

    def test__string_query(self):
        "string_query: string query with no qtype"
        selections = {'obs_pds.volume_id': ['ISS']}
        sql, params = get_string_query(selections, 'obs_pds.volume_id', [])
        print(sql)
        print(params)
        expected = '`obs_pds`.`volume_id` LIKE %s'
        expected_params = ['%ISS%']
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__string_query_contains(self):
        "string_query: string query with qtype contains"
        selections = {'obs_pds.volume_id': ['ISS']}
        sql, params = get_string_query(selections, 'obs_pds.volume_id',
                                       ['contains'])
        print(sql)
        print(params)
        expected = '`obs_pds`.`volume_id` LIKE %s'
        expected_params = ['%ISS%']
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__string_query_begins(self):
        "string_query: string query with qtype begins"
        selections = {'obs_pds.volume_id': ['ISS']}
        sql, params = get_string_query(selections, 'obs_pds.volume_id',
                                       ['begins'])
        print(sql)
        print(params)
        expected = '`obs_pds`.`volume_id` LIKE %s'
        expected_params = ['ISS%']
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__string_query_ends(self):
        "string_query: string query with qtype ends"
        selections = {'obs_pds.volume_id': ['ISS']}
        sql, params = get_string_query(selections, 'obs_pds.volume_id',
                                       ['ends'])
        print(sql)
        print(params)
        expected = '`obs_pds`.`volume_id` LIKE %s'
        expected_params = ['%ISS']
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__string_query_matches(self):
        "string_query: string query with qtype matches"
        selections = {'obs_pds.volume_id': ['ISS']}
        sql, params = get_string_query(selections, 'obs_pds.volume_id',
                                       ['matches'])
        print(sql)
        print(params)
        expected = '`obs_pds`.`volume_id` = %s'
        expected_params = ['ISS']
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__string_query_excludes(self):
        "string_query: string query with qtype excludes"
        selections = {'obs_pds.volume_id': ['ISS']}
        sql, params = get_string_query(selections, 'obs_pds.volume_id',
                                       ['excludes'])
        print(sql)
        print(params)
        expected = '`obs_pds`.`volume_id` NOT LIKE %s'
        expected_params = ['%ISS%']
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)


            #####################################################
            ######### construct_query_string UNIT TESTS #########
            #####################################################

    def test__construct_query_string_bad_paraminfo(self):
        "construct_query_string: construct_query_string with unknown param name"
        selections = {'obs_general.observation_durationx': [20]}
        extras = {}
        sql, params = construct_query_string(selections, extras)
        print(sql)
        print(params)
        expected = None
        expected_params = None
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__construct_query_string_bad_paraminfo_2(self):
        "construct_query_string: construct_query_string with unknown param name #2"
        selections = {'obs_general_observation_durationx': [20]}
        extras = {}
        sql, params = construct_query_string(selections, extras)
        print(sql)
        print(params)
        expected = None
        expected_params = None
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__construct_query_string_bad_paraminfo_3(self):
        "construct_query_string: construct_query_string with unknown param name #3"
        selections = {'obs_general.': [20]}
        extras = {}
        sql, params = construct_query_string(selections, extras)
        print(sql)
        print(params)
        expected = None
        expected_params = None
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__construct_query_string_bad_paraminfo_4(self):
        "construct_query_string: construct_query_string with unknown param name #4"
        selections = {'.observation_duration': [20]}
        extras = {}
        sql, params = construct_query_string(selections, extras)
        print(sql)
        print(params)
        expected = None
        expected_params = None
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__construct_query_string_nojoin(self):
        "construct_query_string: construct_query_string with just obs_general"
        selections = {'obs_general.observation_duration1': [20]}
        extras = {}
        sql, params = construct_query_string(selections, extras)
        print(sql)
        print(params)
        expected = 'SELECT `obs_general`.`id` FROM `obs_general` WHERE (`obs_general`.`observation_duration` >= %s)'
        expected_params = [20]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__construct_query_string_string(self):
        "construct_query_string: construct_query_string with a string"
        selections = {'obs_pds.primary_file_spec': ['C11399XX']}
        extras = {}
        sql, params = construct_query_string(selections, extras)
        print(sql)
        print(params)
        expected = 'SELECT `obs_general`.`id` FROM `obs_general` LEFT JOIN `obs_pds` ON `obs_general`.`id`=`obs_pds`.`obs_general_id` WHERE (`obs_pds`.`primary_file_spec` LIKE %s)'
        expected_params = ['%C11399XX%']
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__construct_query_string_single_column_range(self):
        "construct_query_string: construct_query_string with a single column range"
        selections = {'obs_ring_geometry.ring_center_phase1': [20.0],
                      'obs_ring_geometry.ring_center_phase2': [180.0]}
        extras = {}
        sql, params = construct_query_string(selections, extras)
        print(sql)
        print(params)
        expected = 'SELECT `obs_general`.`id` FROM `obs_general` LEFT JOIN `obs_ring_geometry` ON `obs_general`.`id`=`obs_ring_geometry`.`obs_general_id` WHERE (`obs_ring_geometry`.`ring_center_phase` >= %s AND `obs_ring_geometry`.`ring_center_phase` <= %s)'
        expected_params = [20.0, 180.0]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__construct_query_string_string_with_qtype(self):
        "construct_query_string: construct_query_string with a string and qtype"
        selections = {'obs_pds.primary_file_spec': ['C11399XX']}
        extras = {'qtypes': {'obs_pds.primary_file_spec': ['begins']}}
        sql, params = construct_query_string(selections, extras)
        print(sql)
        print(params)
        expected = 'SELECT `obs_general`.`id` FROM `obs_general` LEFT JOIN `obs_pds` ON `obs_general`.`id`=`obs_pds`.`obs_general_id` WHERE (`obs_pds`.`primary_file_spec` LIKE %s)'
        expected_params = ['C11399XX%']
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__construct_query_string_mults_planet(self):
        "construct_query_string: construct_query_string with planet_id"
        selections = {'obs_general.planet_id': ['Saturn']}
        extras = {}
        sql, params = construct_query_string(selections, extras)
        print(sql)
        print(params)
        expected = 'SELECT `obs_general`.`id` FROM `obs_general` WHERE (`obs_general`.`mult_obs_general_planet_id` IN (%s))'
        expected_params = [4]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__construct_query_string_mults_planet_uc(self):
        "construct_query_string: construct_query_string with planet_id in upper case"
        selections = {'obs_general.planet_id': ['SATURN']}
        extras = {}
        sql, params = construct_query_string(selections, extras)
        print(sql)
        print(params)
        expected = 'SELECT `obs_general`.`id` FROM `obs_general` WHERE (`obs_general`.`mult_obs_general_planet_id` IN (%s))'
        expected_params = [4]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__construct_query_string_mults_empty(self):
        "construct_query_string: construct_query_string with planet_id empty"
        selections = {'obs_general.planet_id': []}
        extras = {}
        sql, params = construct_query_string(selections, extras)
        print(sql)
        print(params)
        expected = 'SELECT `obs_general`.`id` FROM `obs_general`'
        expected_params = []
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__construct_query_string_mults_planet_bad(self):
        "construct_query_string: construct_query_string with planet_id unknown planet"
        selections = {'obs_general.planet_id': ['Jupiter','SaturnX']}
        extras = {}
        sql, params = construct_query_string(selections, extras)
        print(sql)
        print(params)
        expected = None
        expected_params = None
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__construct_query_string_mults_planet_instrumentCOISS(self):
        "construct_query_string: construct_query_string with two mults"
        selections = {'obs_general.planet_id': ['Saturn'],
                      'obs_general.instrument_id': ['COISS']}
        extras = {}
        sql, params = construct_query_string(selections, extras)
        print(sql)
        print(params)
        expected = 'SELECT `obs_general`.`id` FROM `obs_general` WHERE (`obs_general`.`mult_obs_general_instrument_id` IN (%s)) AND (`obs_general`.`mult_obs_general_planet_id` IN (%s))'
        expected_params = [1, 4]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__construct_query_string_mults_with_join(self):
        "construct_query_string: construct_query_string with obs_general and obs_instrument_coiss"
        selections = {'obs_general.planet_id': ['Saturn'],
                      'obs_instrument_coiss.camera': ['Wide Angle']}
        extras = {}
        sql, params = construct_query_string(selections, extras)
        print(sql)
        print(params)
        expected = 'SELECT `obs_general`.`id` FROM `obs_general` LEFT JOIN `obs_instrument_coiss` ON `obs_general`.`id`=`obs_instrument_coiss`.`obs_general_id` WHERE (`obs_general`.`mult_obs_general_planet_id` IN (%s)) AND (`obs_instrument_coiss`.`mult_obs_instrument_coiss_camera` IN (%s))'
        expected_params = [4, 1]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__construct_query_string_mults_with_3_table_join(self):
        "construct_query_string: construct_query_string with three tables"
        selections = {'obs_general.planet_id': ['Saturn'],
                      'obs_instrument_coiss.camera': ['Narrow Angle'],
                      'obs_mission_cassini.rev_no': ['00A','00C']}
        extras = {}
        sql, params = construct_query_string(selections, extras)
        print(sql)
        print(params)
        expected = 'SELECT `obs_general`.`id` FROM `obs_general` LEFT JOIN `obs_instrument_coiss` ON `obs_general`.`id`=`obs_instrument_coiss`.`obs_general_id` LEFT JOIN `obs_mission_cassini` ON `obs_general`.`id`=`obs_mission_cassini`.`obs_general_id` WHERE (`obs_general`.`mult_obs_general_planet_id` IN (%s)) AND (`obs_instrument_coiss`.`mult_obs_instrument_coiss_camera` IN (%s)) AND (`obs_mission_cassini`.`mult_obs_mission_cassini_rev_no` IN (%s,%s))'
        expected_params = [4, 0, 2, 4]
        print(expected)
        print(expected_params)
        print('NOTE: This test requires one of COISS or COVIMS to be imported before COUVIS due to a bad observation name in COUVIS!')
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__construct_query_string_order_existing_table(self):
        "construct_query_string: construct_query_string with sort order already joined"
        selections = {'obs_general.observation_duration1': [20]}
        extras = {'order': (['obs_general.time1'], [False])}
        sql, params = construct_query_string(selections, extras)
        print(sql)
        print(params)
        expected = 'SELECT `obs_general`.`id` FROM `obs_general` WHERE (`obs_general`.`observation_duration` >= %s) ORDER BY obs_general.time1 ASC'
        expected_params = [20]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__construct_query_string_order_existing_table_2(self):
        "construct_query_string: construct_query_string with sort order already joined #2"
        selections = {'obs_general.observation_duration1': [20],
                      'obs_pds.volume_id': ['COISS']}
        extras = {'qtypes': {'obs_pds.volume_id': ['begins']},
                  'order': (['obs_pds.data_set_id'], [True])}
        sql, params = construct_query_string(selections, extras)
        print(sql)
        print(params)
        expected = 'SELECT `obs_general`.`id` FROM `obs_general` LEFT JOIN `obs_pds` ON `obs_general`.`id`=`obs_pds`.`obs_general_id` WHERE (`obs_general`.`observation_duration` >= %s) AND (`obs_pds`.`volume_id` LIKE %s) ORDER BY obs_pds.data_set_id DESC'
        expected_params = [20, 'COISS%']
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__construct_query_string_order_existing_table_multi(self):
        "construct_query_string: construct_query_string with complex sort order already joined"
        selections = {'obs_general.observation_duration1': [20]}
        extras = {'order': (['obs_general.time1',
                             'obs_general.time2'],
                            [False, True])}
        sql, params = construct_query_string(selections, extras)
        print(sql)
        print(params)
        expected = 'SELECT `obs_general`.`id` FROM `obs_general` WHERE (`obs_general`.`observation_duration` >= %s) ORDER BY obs_general.time1 ASC,obs_general.time2 DESC'
        expected_params = [20]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__construct_query_string_order_new_table(self):
        "construct_query_string: construct_query_string with sort order not already joined"
        selections = {'obs_general.observation_duration1': [20]}
        extras = {'order': (['obs_pds.volume_id'], [False])}
        sql, params = construct_query_string(selections, extras)
        print(sql)
        print(params)
        expected = 'SELECT `obs_general`.`id` FROM `obs_general` LEFT JOIN `obs_pds` ON `obs_general`.`id`=`obs_pds`.`obs_general_id` WHERE (`obs_general`.`observation_duration` >= %s) ORDER BY obs_pds.volume_id ASC'
        expected_params = [20]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)


    # def test__range_query_time_any(self):
    #     # range query: form type = TIME, qtype any
    #     selections = {}
    #     selections['obs_general.time_sec1'] = ['1979-05-28T10:17:37.28']
    #     selections['obs_general.time_sec2'] = ['1979-05-29T18:22:26']
    #     q = str(get_range_query(selections,'obs_general.time_sec1',['any']))
    #     print(q)
    #     # time_sec1 <= -649993324.720000 AND time_sec2 >= -649877836.000000
    #     try:
    #         # julian module behaves a bit differently on the production server
    #         # so try both possible results before failing this test
    #         expected = "(AND: ('time_sec1__lte', -649834636.0), ('time_sec2__gte', -649950124.72000003))"
    #         print('expected:')
    #         print(expected)
    #         self.assertEqual('".join(q.split()),"".join(expected.split()))  # strips all whitespace b4 compare
    #     except AssertionError:
    #         expected = "(AND: ('time_sec1__lte', -649834636.0), ('time_sec2__gte', -649950124.72))"
    #         print('expected:')
    #         print(expected)
    #         self.assertEqual('".join(q.split()),"".join(expected.split()))  # strips all whitespace b4 compare
    #
    #
    # def test__range_query_time_any_single_time(self):
    #     # range query: form type = TIME, qtype any
    #     selections = {}
    #     selections['obs_general.time_sec1'] = ['1979-05-28T10:17:37.28']
    #     q = str(get_range_query(selections,'obs_general.time_sec1',['any']))
    #     print(str(q))
    #     # time_sec2 >= -649993324.720000
    #     try:
    #         # julian module behaves a bit differently on the production server
    #         # so try both possible results before failing this test
    #         expected = "(AND: ('time_sec2__gte', -649950124.72000003))"
    #         print('expected:')
    #         print(expected)
    #         self.assertEqual('".join(q.split()),"".join(expected.split()))  # strips all whitespace b4 compare
    #     except AssertionError:
    #         expected = "(AND: ('time_sec2__gte', -649950124.72))"
    #         print('expected:')
    #         print(expected)
    #         self.assertEqual('".join(q.split()),"".join(expected.split()))  # strips all whitespace b4 compare
    #

    # ## get_user_query_table
    #
    # def test__get_user_query_table(self):
    #     # simple base join types only
    #     table = get_user_query_table(self.selections)
    #     print('table = " + str(table) + "\n" + str(self.selections))
    #     self.assertEqual(table.split('_')[0],'cache')
    #
    # def test__get_user_query_table_with_times(self):
    #     selections = {'obs_general.planet_id': ['Saturn'], 'obs_general.time_sec2': ['2009-12-28'], 'obs_general.time_sec1': ['2009-12-23']}
    #     table = get_user_query_table(selections)
    #     print(table)
    #     self.assertGreater(len(table), 0)
    #
    # def test__get_user_query_table_table_already_exists(self):
    #     # the 2nd time through yo're testing whether it returns the table that is already there
    #     table = get_user_query_table(self.selections)
    #     self.assertEqual(table.split('_')[0],'cache')
