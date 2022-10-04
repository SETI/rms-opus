# search/test_search.py

# These tests require the following volumes, imported in this order:
# COISS_2002,COISS_2008,COISS_2111,COUVIS_0002,GO_0017,VGISS_6210,VGISS_8201,HSTI1_2003

import logging
from unittest import TestCase

from django.core.cache import cache
from django.db import connection
from django.http import Http404, QueryDict
from django.test import RequestFactory

from search.views import (api_normalize_input,
                          api_string_search_choices,
                          construct_query_string,
                          get_longitude_query,
                          get_range_query,
                          get_string_query,
                          set_user_search_number,
                          url_to_search_params)
import settings

class searchTests(TestCase):

    def _empty_user_searches(self):
        cursor = connection.cursor()
        cursor.execute('DELETE FROM user_searches')
        cursor.execute("ALTER TABLE user_searches AUTO_INCREMENT = 1")
        cursor.execute("SHOW TABLES LIKE %s", ["cache_%"])
        for row in cursor: # pragma: no cover
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


            ##################################################
            ######### api_normalize_input UNIT TESTS #########
            ##################################################

    def test__api_normalize_input_no_request(self):
        "[test_search.py] api_normalize_input: no request"
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /__api/normalizeinput.json'):
            api_normalize_input(None)

    def test__api_normalize_input_no_get(self):
        "[test_search.py] api_normalize_input: no GET"
        request = self.factory.get('/__api/normalizeinput.json')
        request.GET = None
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /__api/normalizeinput.json'):
            api_normalize_input(request)


            ########################################################
            ######### api_string_search_choices UNIT TESTS #########
            ########################################################

    def test__api_string_search_choices_no_request(self):
        "[test_search.py] api_string_search_choices: no request"
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /__api/stringsearchchoices/slug.json'):
            api_string_search_choices(None, 'slug')

    def test__api_string_search_choices_no_get(self):
        "[test_search.py] api_string_search_choices: no GET"
        request = self.factory.get('/__api/stringsearchchoices/volumeid.json')
        request.GET = None
        with self.assertRaisesRegex(Http404,
            r'Internal error \(No request was provided\) for /__api/stringsearchchoices/slug.json'):
            api_string_search_choices(request, 'slug')


            ###################################################
            ######### url_to_search_params UNIT TESTS #########
            ###################################################

    ####################
    ### TIME PARSING ###
    ####################

    def test__url_to_search_params_times_yd(self):
        "[test_search.py] url_to_search_params: date parsing in YYYY-DDD format oldslug"
        # Using old slug name
        q = QueryDict('timesec1=2000-023T06:00:00&timesec2=2000-024T06:00:00')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_general.time1': [1922432.0],
                        'obs_general.time2': [2008832.0]}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {'obs_general.time': ['any']}
        units_expected = {'obs_general.time': ['ymdhms']}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)

    def test__url_to_search_params_times_yd_any(self):
        "[test_search.py] url_to_search_params: date parsing in YYYY-DDD format any"
        q = QueryDict('time1=2000-023T06:00:00&time2=2000-024T06:00:00&qtype-time=any')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_general.time1': [1922432.0],
                        'obs_general.time2': [2008832.0]}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {'obs_general.time': ['any']}
        units_expected = {'obs_general.time': ['ymdhms']}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)

    def test__url_to_search_params_times_yd_all(self):
        "[test_search.py] url_to_search_params: date parsing in YYYY-DDD format all"
        q = QueryDict('time1=2000-023T06:00:00&time2=2000-024T06:00:00&qtype-time=all')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_general.time1': [1922432.0],
                        'obs_general.time2': [2008832.0]}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {'obs_general.time': ['all']}
        units_expected = {'obs_general.time': ['ymdhms']}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)

    def test__url_to_search_params_times_yd_only(self):
        "[test_search.py] url_to_search_params: date parsing in YYYY-DDD format only"
        q = QueryDict('time1=2000-023T06:00:00&time2=2000-024T06:00:00&qtype-time=only')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_general.time1': [1922432.0],
                        'obs_general.time2': [2008832.0]}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {'obs_general.time': ['only']}
        units_expected = {'obs_general.time': ['ymdhms']}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)

    def test__url_to_search_params_times_ymd(self):
        "[test_search.py] url_to_search_params: date parsing in YYYY-MM-DD format"
        # Using old slug name
        q = QueryDict('timesec1=2000-01-23T06:00:00&timesec2=2000-01-24T06:00:00')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_general.time1': [1922432.0],
                        'obs_general.time2': [2008832.0]}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {'obs_general.time': ['any']}
        units_expected = {'obs_general.time': ['ymdhms']}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)

    def test__url_to_search_params_times_expanded(self):
        "[test_search.py] url_to_search_params: date parsing in YYYY MMM DD format"
        q = QueryDict('time1=2000+JAN+23+6:00:00&time2=2000+January+24+6:00:00')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_general.time1': [1922432.0],
                        'obs_general.time2': [2008832.0]}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {'obs_general.time': ['any']}
        units_expected = {'obs_general.time': ['ymdhms']}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)

    def test__url_to_search_params_times_expanded_2(self):
        "[test_search.py] url_to_search_params: date parsing in YYYY/MM/DD format"
        q = QueryDict('time1=2000/1/23+06:00:00.000&time2=2000/01/24+06:00')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_general.time1': [1922432.0],
                        'obs_general.time2': [2008832.0]}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {'obs_general.time': ['any']}
        units_expected = {'obs_general.time': ['ymdhms']}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)

    def test__url_to_search_params_times_multi_1(self):
        "[test_search.py] url_to_search_params: date parsing multi 1"
        # Using old slug name
        q = QueryDict('time1_1=2000-01-23T06:00:00&time2_1=2000-01-24T06:00:00')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_general.time1': [1922432.0],
                        'obs_general.time2': [2008832.0]}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {'obs_general.time': ['any']}
        units_expected = {'obs_general.time': ['ymdhms']}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)

    def test__url_to_search_params_times_multi_2(self):
        "[test_search.py] url_to_search_params: date parsing multi 2"
        # Using old slug name
        q = QueryDict('time1=2000-01-23T06:00:00&time2=2000-01-24T06:00:00&time1_2=2000-01-24T06:00:01')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_general.time1': [1922432.0, 2008833.0],
                        'obs_general.time2': [2008832.0, None]}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {'obs_general.time': ['any', 'any']}
        units_expected = {'obs_general.time': ['ymdhms', 'ymdhms']}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)

    def test__url_to_search_params_times_multi_3(self):
        "[test_search.py] url_to_search_params: date parsing multi 3 oldslug"
        # Using old slug name
        q = QueryDict('timesec1=2000-01-23T06:00:00&timesec2=2000-01-24T06:00:00&timesec1_2=2000-01-24T06:00:01&timesec2_2=2000-01-24T06:00:02')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_general.time1': [1922432.0, 2008833.0],
                        'obs_general.time2': [2008832.0, 2008834.0]}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {'obs_general.time': ['any', 'any']}
        units_expected = {'obs_general.time': ['ymdhms', 'ymdhms']}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)

    def test__url_to_search_params_times_multi_4(self):
        "[test_search.py] url_to_search_params: date parsing multi 4 all/only"
        # Using old slug name
        q = QueryDict('time1=2000-01-23T06:00:00&time2=2000-01-24T06:00:00&time1_2=2000-01-24T06:00:01&time2_2=2000-01-24T06:00:02&qtype-time=all&qtype-time_2=only')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_general.time1': [1922432.0, 2008833.0],
                        'obs_general.time2': [2008832.0, 2008834.0]}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {'obs_general.time': ['all', 'only']}
        units_expected = {'obs_general.time': ['ymdhms', 'ymdhms']}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)

    def test__url_to_search_params_times_multi_4_bad_case(self):
        "[test_search.py] url_to_search_params: date parsing multi 4 all/only"
        # Using old slug name
        q = QueryDict('time1=2000-01-23T06:00:00&time2=2000-01-24T06:00:00&time1_2=2000-01-24T06:00:01&time2_2=2000-01-24T06:00:02&qtype-time=AlL&qtype-time_2=ONly')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_general.time1': [1922432.0, 2008833.0],
                        'obs_general.time2': [2008832.0, 2008834.0]}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {'obs_general.time': ['all', 'only']}
        units_expected = {'obs_general.time': ['ymdhms', 'ymdhms']}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)

    def test__url_to_search_params_times_multi_5(self):
        "[test_search.py] url_to_search_params: date parsing multi 5 none/only"
        # Using old slug name
        q = QueryDict('time1=2000-01-23T06:00:00&time2=2000-01-24T06:00:00&time1_2=2000-01-24T06:00:01&time2_2=2000-01-24T06:00:02&qtype-time_2=only')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_general.time1': [1922432.0, 2008833.0],
                        'obs_general.time2': [2008832.0, 2008834.0]}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {'obs_general.time': ['any', 'only']}
        units_expected = {'obs_general.time': ['ymdhms', 'ymdhms']}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)

    def test__url_to_search_params_times_multi_6(self):
        "[test_search.py] url_to_search_params: date parsing multi 6 only/none"
        # Using old slug name
        q = QueryDict('time1=2000-01-23T06:00:00&time2=2000-01-24T06:00:00&time1_20=2000-01-24T06:00:01&time2_20=2000-01-24T06:00:02&qtype-time=only')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_general.time1': [1922432.0, 2008833.0],
                        'obs_general.time2': [2008832.0, 2008834.0]}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {'obs_general.time': ['only', 'any']}
        units_expected = {'obs_general.time': ['ymdhms', 'ymdhms']}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)

    def test__url_to_search_params_times_multi_7(self):
        "[test_search.py] url_to_search_params: date parsing multi 7"
        # Using old slug name
        q = QueryDict('time1_1=&time2_2=&time1_3=2000-01-24T06:00:00&time2_3=2000-01-24T06:00:00&qtype-time_1=only')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_general.time1': [2008832.0],
                        'obs_general.time2': [2008832.0]}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {'obs_general.time': ['any']}
        units_expected = {'obs_general.time': ['ymdhms']}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)

    def test__url_to_search_params_times_multi_8(self):
        "[test_search.py] url_to_search_params: date parsing multi 8"
        # Using old slug name
        q = QueryDict('time1_1=&time2_2=&time1_3=2000-01-24T06:00:00&time2_3=&qtype-time_3=only')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_general.time1': [2008832.0],
                        'obs_general.time2': [None]}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {'obs_general.time': ['only']}
        units_expected = {'obs_general.time': ['ymdhms']}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)

    def test__url_to_search_params_times_bad(self):
        "[test_search.py] url_to_search_params: bad date format"
        q = QueryDict('time1=2000 XXX 01')
        (selections, extras) = url_to_search_params(q)
        self.assertIsNone(selections)

    def test__url_to_search_params_times_bad_2(self):
        "[test_search.py] url_to_search_params: bad date format #2"
        q = QueryDict('time1=2000/13/23+06:00:00')
        (selections, extras) = url_to_search_params(q)
        self.assertIsNone(selections)

    def test__url_to_search_params_times_bad_3(self):
        "[test_search.py] url_to_search_params: bad date format #3"
        q = QueryDict('time1=2000-')
        (selections, extras) = url_to_search_params(q)
        self.assertIsNone(selections)

    def test__url_to_search_params_times_bad_4(self):
        "[test_search.py] url_to_search_params: bad date format #4"
        q = QueryDict('time1=06:00:00')
        (selections, extras) = url_to_search_params(q)
        self.assertIsNone(selections)

    def test__url_to_search_params_times_bad_qtype(self):
        "[test_search.py] url_to_search_params: bad qtype"
        q = QueryDict('time1=2000-023T06:00:00&time2=2000-024T06:00:00&qtype-time=contains')
        (selections, extras) = url_to_search_params(q)
        self.assertIsNone(selections)

    def test__url_to_search_params_times_bad_qtype_2(self):
        "[test_search.py] url_to_search_params: bad qtype 2"
        q = QueryDict('time1=2000-023T06:00:00&time2=2000-024T06:00:00&time1_2=2000-023T06:00:00&qtype-time=fred&qtype-time_2=all')
        (selections, extras) = url_to_search_params(q)
        self.assertIsNone(selections)

    def test__url_to_search_params_times_bad_qtype_3(self):
        "[test_search.py] url_to_search_params: bad qtype slug 3"
        q = QueryDict('qtype-time1=all')
        (selections, extras) = url_to_search_params(q)
        self.assertIsNone(selections)

    def test__url_to_search_params_times_bad_qtype_4(self):
        "[test_search.py] url_to_search_params: bad qtype slug 4"
        q = QueryDict('qtype-XXX=all')
        (selections, extras) = url_to_search_params(q)
        self.assertIsNone(selections)

    def test__url_to_search_params_times_bad_unit_1(self):
        "[test_search.py] url_to_search_params: bad unit slug 1"
        q = QueryDict('unit-time1=secs')
        (selections, extras) = url_to_search_params(q)
        self.assertIsNone(selections)

    def test__url_to_search_params_times_bad_clause_1(self):
        "[test_search.py] url_to_search_params: bad clause 1"
        q = QueryDict('time1_0=2000-023T06:00:00')
        (selections, extras) = url_to_search_params(q)
        self.assertIsNone(selections)

    def test__url_to_search_params_times_bad_clause_2(self):
        "[test_search.py] url_to_search_params: bad clause 2"
        q = QueryDict('time1_-1=2000-023T06:00:00')
        (selections, extras) = url_to_search_params(q)
        self.assertIsNone(selections)

    def test__url_to_search_params_times_bad_clause_3(self):
        "[test_search.py] url_to_search_params: bad clause 3"
        q = QueryDict('time1_XX=2000-023T06:00:00')
        (selections, extras) = url_to_search_params(q)
        self.assertIsNone(selections)


    ####################
    ### BASIC RANGES ###
    ####################

    def test__url_to_search_params_qtype_only(self):
        "[test_search.py] url_to_search_params: range with qtype only"
        q = QueryDict('qtype-RINGGEOphase=only')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {}
        units_expected = {}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)

    def test__url_to_search_params_qtype_only_bad_slug(self):
        "[test_search.py] url_to_search_params: qtype only bad slug"
        q = QueryDict('qtype-RINGGEOphaseX=only')
        (selections, extras) = url_to_search_params(q)
        print(selections)
        print(extras)
        self.assertIsNone(selections)
        self.assertIsNone(extras)

    def test__url_to_search_params_unit_only(self):
        "[test_search.py] url_to_search_params: range with unit only"
        q = QueryDict('unit-RINGGEOphase=degrees')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {}
        units_expected = {}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)

    def test__url_to_search_params_unit_only_bad_case(self):
        "[test_search.py] url_to_search_params: range with unit only bad case"
        q = QueryDict('unit-RINGGEOphase=DeGreeS')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {}
        units_expected = {}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)

    def test__url_to_search_params_unit_only_bad_slug(self):
        "[test_search.py] url_to_search_params: unit only bad slug"
        q = QueryDict('unit-RINGGEOphaseX=only')
        (selections, extras) = url_to_search_params(q)
        print(selections)
        print(extras)
        self.assertIsNone(selections)
        self.assertIsNone(extras)

    def test__url_to_search_params_both_empty_min(self):
        "[test_search.py] url_to_search_params: range with only missing min value"
        q = QueryDict('RINGGEOphase1=')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {}
        units_expected = {}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)

    def test__url_to_search_params_both_empty_min_empty_ok(self):
        "[test_search.py] url_to_search_params: range with only missing min value allow_empty"
        q = QueryDict('RINGGEOphase1=')
        (selections, extras) = url_to_search_params(q, allow_empty=True)
        sel_expected = {'obs_ring_geometry.phase1': [None],
                        'obs_ring_geometry.phase2': [None]}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {'obs_ring_geometry.phase': ['any']}
        units_expected = {'obs_ring_geometry.phase': ['degrees']}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)

    def test__url_to_search_params_both_empty_max(self):
        "[test_search.py] url_to_search_params: range with only missing max value"
        q = QueryDict('RINGGEOphase2=')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {}
        units_expected = {}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)

    def test__url_to_search_params_both_empty_max_empty_ok(self):
        "[test_search.py] url_to_search_params: range with only missing max value allow_empty"
        q = QueryDict('RINGGEOphase2=')
        (selections, extras) = url_to_search_params(q, allow_empty=True)
        sel_expected = {'obs_ring_geometry.phase1': [None],
                        'obs_ring_geometry.phase2': [None]}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {'obs_ring_geometry.phase': ['any']}
        units_expected = {'obs_ring_geometry.phase': ['degrees']}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)

    def test__url_to_search_params_both_empty_min_max(self):
        "[test_search.py] url_to_search_params: range with both missing"
        q = QueryDict('RINGGEOphase1=&RINGGEOphase2=')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {}
        units_expected = {}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)

    def test__url_to_search_params_both_empty_min_max_empty_ok(self):
        "[test_search.py] url_to_search_params: range with both missing allow_empty"
        q = QueryDict('RINGGEOphase1=&RINGGEOphase2=')
        (selections, extras) = url_to_search_params(q, allow_empty=True)
        sel_expected = {'obs_ring_geometry.phase1': [None],
                        'obs_ring_geometry.phase2': [None]}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {'obs_ring_geometry.phase': ['any']}
        units_expected = {'obs_ring_geometry.phase': ['degrees']}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)

    def test__url_to_search_params_both_empty_qtype(self):
        "[test_search.py] url_to_search_params: range with both missing with qtype"
        q = QueryDict('qtype-RINGGEOphase=only')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {}
        units_expected = {}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)

    def test__url_to_search_params_both_empty_qtype_empty_ok(self):
        "[test_search.py] url_to_search_params: range with both missing with qtype allow_empty"
        q = QueryDict('qtype-RINGGEOphase=only')
        (selections, extras) = url_to_search_params(q, allow_empty=True)
        sel_expected = {'obs_ring_geometry.phase1': [None],
                        'obs_ring_geometry.phase2': [None]}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {'obs_ring_geometry.phase': ['only']}
        units_expected = {'obs_ring_geometry.phase': ['degrees']}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)

    def test__url_to_search_params_left_side(self):
        "[test_search.py] url_to_search_params: range with min only, max missing value"
        q = QueryDict('RINGGEOphase1=80.1&RINGGEOphase2=')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_ring_geometry.phase1': [80.1],
                        'obs_ring_geometry.phase2': [None]}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {'obs_ring_geometry.phase': ['any']}
        units_expected = {'obs_ring_geometry.phase': ['degrees']}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)

    def test__url_to_search_params_left_side_2(self):
        "[test_search.py] url_to_search_params: range with min only, max missing entirely #2"
        q = QueryDict('RINGGEOphase1=80.1')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_ring_geometry.phase1': [80.1],
                        'obs_ring_geometry.phase2': [None]}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {'obs_ring_geometry.phase': ['any']}
        units_expected = {'obs_ring_geometry.phase': ['degrees']}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)

    def test__url_to_search_params_left_side_ignore_ui_slugs(self):
        "[test_search.py] url_to_search_params: range with min only, max missing value, ignored UI slugs"
        q = QueryDict('RINGGEOphase1=80.1&widgets=fred,ethel&RINGGEOphase2=&reqno=5')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_ring_geometry.phase1': [80.1],
                        'obs_ring_geometry.phase2': [None]}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {'obs_ring_geometry.phase': ['any']}
        units_expected = {'obs_ring_geometry.phase': ['degrees']}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)

    def test__url_to_search_params_right_side(self):
        "[test_search.py] url_to_search_params: range with max only, min missing value"
        q = QueryDict('RINGGEOphase1=&RINGGEOphase2=90.5')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_ring_geometry.phase1': [None],
                        'obs_ring_geometry.phase2': [90.5]}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {'obs_ring_geometry.phase': ['any']}
        units_expected = {'obs_ring_geometry.phase': ['degrees']}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)

    def test__url_to_search_params_right_side_2(self):
        "[test_search.py] url_to_search_params: range with max only, min missing entirely"
        q = QueryDict('RINGGEOphase2=90.5')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_ring_geometry.phase1': [None],
                        'obs_ring_geometry.phase2': [90.5]}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {'obs_ring_geometry.phase': ['any']}
        units_expected = {'obs_ring_geometry.phase': ['degrees']}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)

    def test__url_to_search_params_both_side(self):
        "[test_search.py] url_to_search_params: range with both min and max"
        q = QueryDict('RINGGEOphase1=0&RINGGEOphase2=355.201')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_ring_geometry.phase1': [0.],
                        'obs_ring_geometry.phase2': [355.201]}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {'obs_ring_geometry.phase': ['any']}
        units_expected = {'obs_ring_geometry.phase': ['degrees']}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)

    def test__url_to_search_params_both_side_any(self):
        "[test_search.py] url_to_search_params: range with qtype=any"
        q = QueryDict('RINGGEOphase1=0&RINGGEOphase2=355.201&qtype-RINGGEOphase=any')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_ring_geometry.phase1': [0.],
                        'obs_ring_geometry.phase2': [355.201]}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {'obs_ring_geometry.phase': ['any']}
        units_expected = {'obs_ring_geometry.phase': ['degrees']}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)

    def test__url_to_search_params_both_side_all(self):
        "[test_search.py] url_to_search_params: range with qtype=all"
        q = QueryDict('RINGGEOphase1=0&RINGGEOphase2=355.201&qtype-RINGGEOphase=all')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_ring_geometry.phase1': [0.],
                        'obs_ring_geometry.phase2': [355.201]}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {'obs_ring_geometry.phase': ['all']}
        units_expected = {'obs_ring_geometry.phase': ['degrees']}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)

    def test__url_to_search_params_both_side_only(self):
        "[test_search.py] url_to_search_params: range with qtype=only"
        q = QueryDict('RINGGEOphase1=0&RINGGEOphase2=355.201&qtype-RINGGEOphase=only')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_ring_geometry.phase1': [0.],
                        'obs_ring_geometry.phase2': [355.201]}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {'obs_ring_geometry.phase': ['only']}
        units_expected = {'obs_ring_geometry.phase': ['degrees']}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)

    def test__url_to_search_params_range_multi_1(self):
        "[test_search.py] url_to_search_params: range multi 1"
        q = QueryDict('RINGGEOphase1=0&RINGGEOphase2=355.201&RINGGEOphase1_1=10&RINGGEOphase2_1=255.201')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_ring_geometry.phase1': [0., 10.],
                        'obs_ring_geometry.phase2': [355.201, 255.201]}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {'obs_ring_geometry.phase': ['any', 'any']}
        units_expected = {'obs_ring_geometry.phase': ['degrees', 'degrees']}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)

    def test__url_to_search_params_range_multi_2(self):
        "[test_search.py] url_to_search_params: range multi 2"
        q = QueryDict('RINGGEOphase1=0&RINGGEOphase2=355.201&RINGGEOphase1_1=10&RINGGEOphase2_2=255.201')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_ring_geometry.phase1': [0., 10., None],
                        'obs_ring_geometry.phase2': [355.201, None, 255.201]}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {'obs_ring_geometry.phase': ['any', 'any', 'any']}
        units_expected = {'obs_ring_geometry.phase': ['degrees', 'degrees', 'degrees']}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)

    def test__url_to_search_params_range_multi_3(self):
        "[test_search.py] url_to_search_params: range multi 3"
        q = QueryDict('RINGGEOphase1=0&RINGGEOphase2=355.201&RINGGEOphase1_1=10&RINGGEOphase2_1=255.201&qtype-RINGGEOphase=only&qtype-RINGGEOphase_1=all&qtype-RINGGEOphase_2=only')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_ring_geometry.phase1': [0., 10.],
                        'obs_ring_geometry.phase2': [355.201, 255.201]}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {'obs_ring_geometry.phase': ['only', 'all']}
        units_expected = {'obs_ring_geometry.phase': ['degrees', 'degrees']}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)

    def test__url_to_search_params_range_multi_4(self):
        "[test_search.py] url_to_search_params: range multi 4"
        q = QueryDict('RINGGEOphase1=0&RINGGEOphase2=355.201&RINGGEOphase1_1=10&RINGGEOphase2_1=255.201&qtype-RINGGEOphase=only&qtype-RINGGEOphase_2=only')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_ring_geometry.phase1': [0., 10.],
                        'obs_ring_geometry.phase2': [355.201, 255.201]}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {'obs_ring_geometry.phase': ['only', 'any']}
        units_expected = {'obs_ring_geometry.phase': ['degrees', 'degrees']}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)

    def test__url_to_search_params_range_multi_5(self):
        "[test_search.py] url_to_search_params: range multi 5"
        q = QueryDict('RINGGEOphase1_10=10&RINGGEOphase2_10=255.201&qtype-RINGGEOphase=only&qtype-RINGGEOphase_10=only')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_ring_geometry.phase1': [10.],
                        'obs_ring_geometry.phase2': [255.201]}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {'obs_ring_geometry.phase': ['only']}
        units_expected = {'obs_ring_geometry.phase': ['degrees']}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)

    def test__url_to_search_params_range_return_pretty1(self):
        "[test_search.py] url_to_search_params: range return_slugs pretty, with wavelength cm values and unit: cm"
        q = QueryDict('wavelength1_01=0.000039&wavelength2_01=0.00007&unit-wavelength_01=cm')
        (selections, extras) = url_to_search_params(q, return_slugs=True, pretty_results=True)
        sel_expected = {'wavelength1_01': '0.000039',
                        'wavelength2_01': '0.00007'}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {'obs_wavelength.wavelength': ['any']}
        units_expected = {'obs_wavelength.wavelength': ['cm']}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)

    def test__url_to_search_params_range_return_pretty2(self):
        "[test_search.py] url_to_search_params: range return_slugs pretty, with wavelength cm values and no unit (default unit)"
        q = QueryDict('wavelength1_01=0.000039&wavelength2_01=0.00007')
        (selections, extras) = url_to_search_params(q, return_slugs=True, pretty_results=True)
        sel_expected = {'wavelength1_01': '0',
                        'wavelength2_01': '0.0001'}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {'obs_wavelength.wavelength': ['any']}
        units_expected = {'obs_wavelength.wavelength': ['microns']}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)


    #######################
    ### NUMERIC FORMATS ###
    #######################

    def test__url_to_search_params_numeric_spaces(self):
        "[test_search.py] url_to_search_params: numeric with spaces"
        q = QueryDict('observationduration1=+1+0+')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_general.observation_duration1': [10.],
                        'obs_general.observation_duration2': [None]}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {}
        units_expected = {'obs_general.observation_duration': ['seconds']}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)

    def test__url_to_search_params_numeric_commas(self):
        "[test_search.py] url_to_search_params: numeric with commas"
        q = QueryDict('observationduration1=,100,000.0,')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_general.observation_duration1': [100000.],
                        'obs_general.observation_duration2': [None]}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {}
        units_expected = {'obs_general.observation_duration': ['seconds']}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)

    def test__url_to_search_params_numeric_bad_1(self):
        "[test_search.py] url_to_search_params: numeric bad 1"
        q = QueryDict('observationduration1=XXX"&observationduration2=10.')
        (selections, extras) = url_to_search_params(q)
        print(selections)
        print(extras)
        self.assertIsNone(selections)

    def test__url_to_search_params_numeric_bad_2(self):
        "[test_search.py] url_to_search_params: numeric bad 2"
        q = QueryDict('observationduration1=10."&observationduration2=XXX')
        (selections, extras) = url_to_search_params(q)
        print(selections)
        print(extras)
        self.assertIsNone(selections)

    def test__url_to_search_params_numeric_bad_12(self):
        "[test_search.py] url_to_search_params: numeric bad 12"
        q = QueryDict('observationduration1=XXX"&observationduration2=XXX')
        (selections, extras) = url_to_search_params(q)
        print(selections)
        print(extras)
        self.assertIsNone(selections)

    ###################
    ### ALLOW EMPTY ###
    ###################

    def test__url_to_search_params_range_input_allow_empty_1(self):
        "[test_search.py] url_to_search_params: search allowing empty range input set 1"
        q = QueryDict('wavelength1_02=0.0100&wavelength2_03=0.4000')
        (selections, extras) = url_to_search_params(q, allow_empty=True)
        sel_expected = {'obs_wavelength.wavelength1': [None, 0.01, None],
                        'obs_wavelength.wavelength2': [None, None, 0.4]}
        qtypes_expected = {'obs_wavelength.wavelength': [None, 'any', 'any']}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)

    def test__url_to_search_params_range_input_allow_empty_2(self):
        "[test_search.py] url_to_search_params: search allowing empty range input set 2"
        q = QueryDict('qtype-wavelength_03=any')
        (selections, extras) = url_to_search_params(q, allow_empty=True)
        sel_expected = {'obs_wavelength.wavelength1': [None, None, None],
                        'obs_wavelength.wavelength2': [None, None, None]}
        qtypes_expected = {'obs_wavelength.wavelength': [None, None, 'any']}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)

    def test__url_to_search_params_range_input_allow_empty_3(self):
        "[test_search.py] url_to_search_params: search allowing empty range input set 3"
        q = QueryDict('wavelength1_03=0.0100')
        (selections, extras) = url_to_search_params(q, allow_empty=True)
        sel_expected = {'obs_wavelength.wavelength1': [None, None, 0.01],
                        'obs_wavelength.wavelength2': [None, None, None]}
        qtypes_expected = {'obs_wavelength.wavelength': [None, None, 'any']}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)

    def test__url_to_search_params_range_input_allow_empty_4(self):
        "[test_search.py] url_to_search_params: search allowing empty range input set 4"
        q = QueryDict('wavelength2_03=0.4000')
        (selections, extras) = url_to_search_params(q, allow_empty=True)
        sel_expected = {'obs_wavelength.wavelength1': [None, None, None],
                        'obs_wavelength.wavelength2': [None, None, 0.4]}
        qtypes_expected = {'obs_wavelength.wavelength': [None, None, 'any']}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)

    def test__url_to_search_params_string_input_allow_empty_1(self):
        "[test_search.py] url_to_search_params: search allowing empty string input set 1"
        q = QueryDict('volumeid_03=COISS')
        (selections, extras) = url_to_search_params(q, allow_empty=True)
        sel_expected = {'obs_pds.volume_id': [None, None, 'COISS']}
        qtypes_expected = {'obs_pds.volume_id': [None, None, 'contains']}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)

    def test__url_to_search_params_string_input_allow_empty_2(self):
        "[test_search.py] url_to_search_params: search allowing empty string input set 2"
        q = QueryDict('qtype-volumeid_03=contains')
        (selections, extras) = url_to_search_params(q, allow_empty=True)
        sel_expected = {'obs_pds.volume_id': [None, None, None]}
        qtypes_expected = {'obs_pds.volume_id': [None, None, 'contains']}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)


    ######################
    ### STRING FORMATS ###
    ######################

    def test__url_to_search_params_stringsearch_empty(self):
        "[test_search.py] url_to_search_params: search on a string value empty"
        q = QueryDict('note=')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {}
        units_expected = {}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)

    def test__url_to_search_params_stringsearch_empty_empty_ok(self):
        "[test_search.py] url_to_search_params: search on a string value empty allow_empty"
        q = QueryDict('note=')
        (selections, extras) = url_to_search_params(q, allow_empty=True)
        sel_expected = {'obs_pds.note': [None]}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {'obs_pds.note': ['contains']}
        units_expected = {}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)

    def test__url_to_search_params_stringsearch_missing_qtype(self):
        "[test_search.py] url_to_search_params: search on a missing string with qtype"
        q = QueryDict('qtype-note=matches')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {}
        units_expected = {}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)

    def test__url_to_search_params_stringsearch_missing_qtype_empty_ok(self):
        "[test_search.py] url_to_search_params: search on a missing string with qtype allow_empty"
        q = QueryDict('qtype-note=matches')
        (selections, extras) = url_to_search_params(q, allow_empty=True)
        sel_expected = {'obs_pds.note': [None]}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {'obs_pds.note': ['matches']}
        units_expected = {}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)

    def test__url_to_search_params_stringsearch_note(self):
        "[test_search.py] url_to_search_params: search on a string value note"
        q = QueryDict('note=Incomplete')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_pds.note': ['Incomplete']}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {'obs_pds.note': ['contains']}
        units_expected = {}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)

    def test__url_to_search_params_stringsearch_opusid(self):
        "[test_search.py] url_to_search_params: search on a string value opusid"
        q = QueryDict('opusid=XXX')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_general.opus_id': ['XXX']}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {'obs_general.opus_id': ['contains']}
        units_expected = {}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)

    def test__url_to_search_params_stringsearch_contains(self):
        "[test_search.py] url_to_search_params: string search with qtype=contains"
        q = QueryDict('note=Incomplete&qtype-note=contains')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_pds.note': ['Incomplete']}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {'obs_pds.note': ['contains']}
        units_expected = {}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)

    def test__url_to_search_params_stringsearch_contains_units(self):
        "[test_search.py] url_to_search_params: string search with units"
        q = QueryDict('note=Incomplete&unit-note=fred')
        (selections, extras) = url_to_search_params(q)
        sel_expected = None
        extras_expected = None
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras, extras_expected)

    def test__url_to_search_params_stringsearch_one_comma(self):
        "[test_search.py] url_to_search_params: string with one comma"
        q = QueryDict('note=,')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_pds.note': [',']}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {'obs_pds.note': ['contains']}
        units_expected = {}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)

    def test__url_to_search_params_stringsearch_commas(self):
        "[test_search.py] url_to_search_params: string with commas"
        q = QueryDict('note=,Note1,Note2,&qtype-note=ends')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_pds.note': [',Note1,Note2,']}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {'obs_pds.note': ['ends']}
        units_expected = {}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)

    def test__url_to_search_params_stringsearch_one_space(self):
        "[test_search.py] url_to_search_params: string with one space"
        q = QueryDict('note=+')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_pds.note': [' ']}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {'obs_pds.note': ['contains']}
        units_expected = {}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)

    def test__url_to_search_params_stringsearch_spaces(self):
        "[test_search.py] url_to_search_params: string with spaces"
        q = QueryDict('note=++++')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_pds.note': ['    ']}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {'obs_pds.note': ['contains']}
        units_expected = {}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)

    def test__url_to_search_params_stringsearch_multi_1(self):
        "[test_search.py] url_to_search_params: search on a string value multi 1"
        q = QueryDict('note=Incomplete&note_2=Fred')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_pds.note': ['Incomplete', 'Fred']}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {'obs_pds.note': ['contains', 'contains']}
        units_expected = {}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)

    def test__url_to_search_params_stringsearch_multi_2(self):
        "[test_search.py] url_to_search_params: search on a string value multi 2"
        q = QueryDict('note=Incomplete&note_2=Fred&qtype-note=ends&qtype-note_2=matches')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_pds.note': ['Incomplete', 'Fred']}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {'obs_pds.note': ['ends', 'matches']}
        units_expected = {}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)


    #############
    ### MULTS ###
    #############

    def test__url_to_search_params_mults_empty(self):
        "[test_search.py] url_to_search_params: mults empty"
        q = QueryDict('planet=&target=')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {}
        units_expected = {}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)

    def test__url_to_search_params_mults_empty_return_pretty(self):
        "[test_search.py] url_to_search_params: mults empty return_slugs pretty"
        q = QueryDict('planet=&target=')
        (selections, extras) = url_to_search_params(q, return_slugs=True, pretty_results=True)
        sel_expected = {'planet': '',
                        'target': ''}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {}
        units_expected = {}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)

    def test__url_to_search_params_mults_empty_comma(self):
        "[test_search.py] url_to_search_params: mults empty comma"
        q = QueryDict('planet=,&target=,,')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {}
        units_expected = {}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)

    def test__url_to_search_params_mults_empty_comma_return_pretty(self):
        "[test_search.py] url_to_search_params: mults empty comma return_slugs pretty"
        q = QueryDict('planet=,&target=,,')
        (selections, extras) = url_to_search_params(q, return_slugs=True, pretty_results=True)
        sel_expected = {'planet': '',
                        'target': ''}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {}
        units_expected = {}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)

    def test__url_to_search_params_mults_uc(self):
        "[test_search.py] url_to_search_params: mults upper case"
        q = QueryDict('planet=SATURN&target=PAN')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_general.target_name': ['PAN'],
                        'obs_general.planet_id': ['SATURN']}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {}
        units_expected = {}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)

    def test__url_to_search_params_mults_lc(self):
        "[test_search.py] url_to_search_params: mults lower case"
        q = QueryDict('planet=saturn&target=pan')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_general.target_name': ['pan'],
                        'obs_general.planet_id': ['saturn']}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {}
        units_expected = {}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)

    def test__url_to_search_params_mults_lc_dual(self):
        "[test_search.py] url_to_search_params: mults lower case dual"
        q = QueryDict('planet=saturn,jupiter')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_general.planet_id': ['jupiter','saturn']}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {}
        units_expected = {}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)

    def test__url_to_search_params_mults_lc_dual_pretty(self):
        "[test_search.py] url_to_search_params: mults lower case dual pretty"
        q = QueryDict('planet=saturn,jupiter')
        (selections, extras) = url_to_search_params(q, pretty_results=True)
        sel_expected = {'obs_general.planet_id': 'jupiter,saturn'}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {}
        units_expected = {}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)

    def test__url_to_search_params_mults_lc_dual_slug(self):
        "[test_search.py] url_to_search_params: mults lower case dual return_slug"
        q = QueryDict('planet=saturn,jupiter')
        (selections, extras) = url_to_search_params(q, return_slugs=True)
        sel_expected = {'planet': ['jupiter','saturn']}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {}
        units_expected = {}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)

    def test__url_to_search_params_mults_lc_dual_slug_pretty(self):
        "[test_search.py] url_to_search_params: mults lower case dual return_slug pretty"
        q = QueryDict('planet=saturn,jupiter')
        (selections, extras) = url_to_search_params(q, return_slugs=True, pretty_results=True)
        sel_expected = {'planet': 'jupiter,saturn'}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {}
        units_expected = {}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)

    def test__url_to_search_params_mults_duplicate(self):
        "[test_search.py] url_to_search_params: mults duplicate"
        # Mult items are sorted and uniquified before looking up
        q = QueryDict('planet=SATURN,SATURN')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_general.planet_id': ['SATURN']}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {}
        units_expected = {}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)

    def test__url_to_search_params_mults_lc_qtype(self):
        "[test_search.py] url_to_search_params: mults lower case qtype"
        q = QueryDict('planet=saturn&target=pan&qtype-planet=only')
        (selections, extras) = url_to_search_params(q)
        print(selections)
        print(extras)
        self.assertIsNone(selections)
        self.assertIsNone(extras)

    def test__url_to_search_params_mults_lc_unit(self):
        "[test_search.py] url_to_search_params: mults lower case unit"
        q = QueryDict('planet=saturn&target=pan&unit-planet=km')
        (selections, extras) = url_to_search_params(q)
        print(selections)
        print(extras)
        self.assertIsNone(selections)
        self.assertIsNone(extras)

    def test__url_to_search_params_mults_plus(self):
        "[test_search.py] url_to_search_params: mults using a + to mean space"
        q = QueryDict('instrument=Cassini+ISS')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_general.instrument_id': ['Cassini ISS']}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {}
        units_expected = {}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)

    def test__url_to_search_params_mults_2B(self):
        "[test_search.py] url_to_search_params: mults using %2B to mean plus"
        q = QueryDict('COISSfilter=BL1%2BGRN')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_instrument_coiss.combined_filter': ['BL1+GRN']}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {}
        units_expected = {}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)

    def test__url_to_search_params_with_join(self):
        "[test_search.py] url_to_search_params: mults from different tables"
        q = QueryDict('planet=Saturn&RINGGEOringradius1=60000')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_general.planet_id': ['Saturn'],
                        'obs_ring_geometry.ring_radius1': [60000],
                        'obs_ring_geometry.ring_radius2': [None]}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {'obs_ring_geometry.ring_radius': ['any']}
        units_expected = {'obs_ring_geometry.ring_radius': ['km']}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)

    def test__url_to_search_params_stringmultmix(self):
        "[test_search.py] url_to_search_params: mults and string searches at the same time"
        q = QueryDict('planet=SATURN&target=PAN&note=Incomplete&qtype-note=begins')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_general.planet_id': ['SATURN'],
                        'obs_general.target_name': ['PAN'],
                        'obs_pds.note': ['Incomplete']}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {'obs_pds.note': ['begins']}
        units_expected = {}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)

    def test__url_to_search_params_mults_bad_1(self):
        "[test_search.py] url_to_search_params: mult bad val"
        q = QueryDict('planet=XXX&target=PAN')
        (selections, extras) = url_to_search_params(q)
        print(selections)
        print(extras)
        self.assertIsNone(selections)
        self.assertIsNone(extras)

    def test__url_to_search_params_mults_bad_1_allow(self):
        "[test_search.py] url_to_search_params: mult bad val allow_errors"
        q = QueryDict('planet=SATURN,XXX&target=PAN')
        (selections, extras) = url_to_search_params(q, allow_errors=True)
        sel_expected = {'obs_general.planet_id': None,
                        'obs_general.target_name': ['PAN']}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {}
        units_expected = {}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)

    def test__url_to_search_params_mults_bad_2(self):
        "[test_search.py] url_to_search_params: mult bad val 2"
        q = QueryDict('planet=SATURN,XXX&target=PAN')
        (selections, extras) = url_to_search_params(q)
        print(selections)
        print(extras)
        self.assertIsNone(selections)
        self.assertIsNone(extras)

    def test__url_to_search_params_mults_bad_3(self):
        "[test_search.py] url_to_search_params: mult bad qtype"
        q = QueryDict('qtype-planet=contains')
        (selections, extras) = url_to_search_params(q)
        print(selections)
        print(extras)
        self.assertIsNone(selections)
        self.assertIsNone(extras)

    def test__url_to_search_params_mults_bad_4(self):
        "[test_search.py] url_to_search_params: mult bad clause"
        q = QueryDict('planet_1=SATURN')
        (selections, extras) = url_to_search_params(q)
        print(selections)
        print(extras)
        self.assertIsNone(selections)
        self.assertIsNone(extras)

    def test__url_to_search_params_mults_bad_5(self):
        "[test_search.py] url_to_search_params: mult bad units"
        q = QueryDict('unit-planet=fred')
        (selections, extras) = url_to_search_params(q)
        print(selections)
        print(extras)
        self.assertIsNone(selections)
        self.assertIsNone(extras)


    ##################
    ### SORT ORDER ###
    ##################

    def test__url_to_search_params_from_sort_default(self):
        "[test_search.py] url_to_search_params: default sort order"
        q = QueryDict('planet=Saturn')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_general.planet_id': ['Saturn']}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {}
        units_expected = {}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)

    def test__url_to_search_params_from_sort_blank(self):
        "[test_search.py] url_to_search_params: blank sort order"
        q = QueryDict('planet=Saturn&order=')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_general.planet_id': ['Saturn']}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {}
        units_expected = {}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)

    def test__url_to_search_params_from_sort_bad(self):
        "[test_search.py] url_to_search_params: bad sort order"
        q = QueryDict('planet=Saturn&order=time1,-fredethel')
        (selections, extras) = url_to_search_params(q)
        print(selections)
        print(extras)
        self.assertIsNone(selections)
        self.assertIsNone(extras)

    def test__url_to_search_params_from_sort_opusid(self):
        "[test_search.py] url_to_search_params: sort on opusid"
        q = QueryDict('planet=Saturn&order=opusid')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_general.planet_id': ['Saturn']}
        order_expected = (['obs_general.opus_id'],
                          [False])
        qtypes_expected = {}
        units_expected = {}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)

    def test__url_to_search_params_from_sort_opusid_desc(self):
        "[test_search.py] url_to_search_params: sort on descending opusid"
        q = QueryDict('planet=Saturn&order=-opusid')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_general.planet_id': ['Saturn']}
        order_expected = (['obs_general.opus_id'],
                          [True])
        qtypes_expected = {}
        units_expected = {}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)

    def test__url_to_search_params_from_sort_multi(self):
        "[test_search.py] url_to_search_params: sort on descending opusid"
        q = QueryDict('planet=Saturn&order=-opusid,RINGGEOphase1,-volumeid')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_general.planet_id': ['Saturn']}
        order_expected = (['obs_general.opus_id', 'obs_ring_geometry.phase1',
                           'obs_pds.volume_id'],
                          [True, False, True])
        qtypes_expected = {}
        units_expected = {}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)
        self.assertEqual(extras['units'], units_expected)


            ##############################################
            ######### get_range_query UNIT TESTS #########
            ##############################################

    def test__range_query_single_col_range_left_side(self):
        "[test_search.py] range_query: single column range with min only"
        selections = {'obs_type_image.duration1': [20.0],
                      'obs_type_image.duration2': [None]}
        sql, params = get_range_query(selections, 'obs_type_image.duration1', [], [])
        print(sql)
        print(params)
        expected = '`obs_type_image`.`duration` >= %s'
        expected_params = [20.0]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__range_query_single_col_range_right_side(self):
        "[test_search.py] range_query: single column range with max only"
        selections = {'obs_type_image.duration1': [None],
                      'obs_type_image.duration2': [180.0]}
        sql, params = get_range_query(selections, 'obs_type_image.duration1', [], [])
        print(sql)
        print(params)
        expected = '`obs_type_image`.`duration` <= %s'
        expected_params = [180.0]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__range_query_single_col_range_both_side(self):
        "[test_search.py] range_query: single column range with both min and max"
        selections = {'obs_type_image.duration2': [180.0],
                      'obs_type_image.duration1': [20.0]}
        sql, params = get_range_query(selections, 'obs_type_image.duration1', ['any'], [])
        print(sql)
        print(params)
        expected = '`obs_type_image`.`duration` >= %s AND `obs_type_image`.`duration` <= %s'
        expected_params = [20.0,180.0]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__range_query_single_col_range_all(self):
        "[test_search.py] range_query: single column range with bogus qtype=all"
        selections = {'obs_type_image.duration2': [180.0],
                      'obs_type_image.duration1': [20.0]}
        sql, params = get_range_query(selections, 'obs_type_image.duration1', ['all'], [])
        print(sql)
        print(params)
        self.assertIsNone(sql)
        self.assertIsNone(params)

    def test__range_query_no_qtype_left_side(self):
        "[test_search.py] range_query: multi column range with no qtype, min only"
        selections = {'obs_ring_geometry.ring_radius1': [10000.],
                      'obs_ring_geometry.ring_radius2': [None]}
        sql, params = get_range_query(selections, 'obs_ring_geometry.ring_radius1', [], [])
        print(sql)
        print(params)
        # Effectively 10000 to inf
        expected = '`obs_ring_geometry`.`ring_radius2` >= %s'
        expected_params = [10000.0]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__range_query_any_left_side(self):
        "[test_search.py] range_query: multi column range with qtype=any, min only"
        selections = {'obs_ring_geometry.ring_radius1': [10000.],
                      'obs_ring_geometry.ring_radius2': [None]}
        sql, params = get_range_query(selections, 'obs_ring_geometry.ring_radius1', ['any'], [])
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
        "[test_search.py] range_query: multi column range with qtype=any, max only"
        selections = {'obs_ring_geometry.ring_radius1': [None],
                      'obs_ring_geometry.ring_radius2': [40000.]}
        sql, params = get_range_query(selections, 'obs_ring_geometry.ring_radius1', ['any'], [])
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
        "[test_search.py] range_query: multi column range with qtype=any, both min and max"
        selections = {'obs_ring_geometry.ring_radius1': [10000.],
                      'obs_ring_geometry.ring_radius2': [40000.]}
        sql, params = get_range_query(selections, 'obs_ring_geometry.ring_radius1', ['any'], [])
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
        "[test_search.py] range_query: multi column range with qtype=all, min only"
        selections = {'obs_ring_geometry.ring_radius1': [10000.],
                      'obs_ring_geometry.ring_radius2': [None]}
        sql, params = get_range_query(selections, 'obs_ring_geometry.ring_radius1', ['all'], [])
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
        "[test_search.py] range_query: multi column range with qtype=all, max only"
        selections = {'obs_ring_geometry.ring_radius1': [None],
                      'obs_ring_geometry.ring_radius2': [40000.]}
        sql, params = get_range_query(selections, 'obs_ring_geometry.ring_radius1', ['all'], [])
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
        "[test_search.py] range_query: multi column range with qtype=all, both min and max"
        selections = {'obs_ring_geometry.ring_radius1': [10000.],
                      'obs_ring_geometry.ring_radius2': [40000.]}
        sql, params = get_range_query(selections, 'obs_ring_geometry.ring_radius1', ['all'], [])
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
        "[test_search.py] range_query: multi column range with qtype=only, min only"
        selections = {'obs_ring_geometry.ring_radius1': [10000.],
                      'obs_ring_geometry.ring_radius2': [None]}
        sql, params = get_range_query(selections, 'obs_ring_geometry.ring_radius1', ['only'], [])
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
        "[test_search.py] range_query: multi column range with qtype=only, max only"
        selections = {'obs_ring_geometry.ring_radius1': [None],
                      'obs_ring_geometry.ring_radius2': [40000.]}
        sql, params = get_range_query(selections, 'obs_ring_geometry.ring_radius1', ['only'], [])
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
        "[test_search.py] range_query: multi column range with qtype=only, both min and max"
        selections = {'obs_ring_geometry.ring_radius1': [10000.],
                      'obs_ring_geometry.ring_radius2': [40000.]}
        sql, params = get_range_query(selections, 'obs_ring_geometry.ring_radius1', ['only'], [])
        print(sql)
        print(params)
        # 10000 to 40000
        expected = '`obs_ring_geometry`.`ring_radius1` >= %s AND `obs_ring_geometry`.`ring_radius2` <= %s'
        expected_params = [10000.0,40000.]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__range_query_clause_1(self):
        "[test_search.py] range_query: clause 1 second all None"
        selections = {'obs_ring_geometry.ring_radius1': [10000., None],
                      'obs_ring_geometry.ring_radius2': [40000., None]}
        sql, params = get_range_query(selections, 'obs_ring_geometry.ring_radius1', ['only', 'any'], [])
        print(sql)
        print(params)
        # 10000 to 40000
        expected = '`obs_ring_geometry`.`ring_radius1` >= %s AND `obs_ring_geometry`.`ring_radius2` <= %s'
        expected_params = [10000.0,40000.]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__range_query_clause_2(self):
        "[test_search.py] range_query: clause 2 second part None"
        selections = {'obs_ring_geometry.ring_radius1': [10000., None],
                      'obs_ring_geometry.ring_radius2': [40000., 50000.]}
        sql, params = get_range_query(selections, 'obs_ring_geometry.ring_radius1', ['only', 'any'], [])
        print(sql)
        print(params)
        # 10000 to 40000
        expected = '(`obs_ring_geometry`.`ring_radius1` >= %s AND `obs_ring_geometry`.`ring_radius2` <= %s) OR (`obs_ring_geometry`.`ring_radius1` <= %s)'
        expected_params = [10000.0,40000.,50000.]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__range_query_clause_3(self):
        "[test_search.py] range_query: clause 3 some each None"
        selections = {'obs_ring_geometry.ring_radius1': [10000., None, 60000.],
                      'obs_ring_geometry.ring_radius2': [40000., 50000., None]}
        sql, params = get_range_query(selections, 'obs_ring_geometry.ring_radius1', ['only', 'any', 'all'], [])
        print(sql)
        print(params)
        # 10000 to 40000
        expected = '(`obs_ring_geometry`.`ring_radius1` >= %s AND `obs_ring_geometry`.`ring_radius2` <= %s) OR (`obs_ring_geometry`.`ring_radius1` <= %s) OR (`obs_ring_geometry`.`ring_radius1` <= %s)'
        expected_params = [10000.0,40000.,50000.,60000.]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__range_query_clause_4(self):
        "[test_search.py] range_query: clause 4 wrote qtype len"
        selections = {'obs_ring_geometry.ring_radius1': [10000., None, 60000.],
                      'obs_ring_geometry.ring_radius2': [40000., 50000., None]}
        sql, params = get_range_query(selections, 'obs_ring_geometry.ring_radius1', ['only', 'any'], [])
        print(sql)
        print(params)
        expected = None
        expected_params = None
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__range_query_clause_5(self):
        "[test_search.py] range_query: clause 5 qtype any second part both None"
        selections = {'obs_ring_geometry.ring_radius1': [10000., None],
                      'obs_ring_geometry.ring_radius2': [40000., None]}
        sql, params = get_range_query(selections, 'obs_ring_geometry.ring_radius1', ['any', 'any'], [])
        print(sql)
        print(params)
        # 10000 to 40000
        expected = '`obs_ring_geometry`.`ring_radius2` >= %s AND `obs_ring_geometry`.`ring_radius1` <= %s'
        expected_params = [10000.0,40000.]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__range_query_clause_6(self):
        "[test_search.py] range_query: clause 6 qtype all second part both None"
        selections = {'obs_ring_geometry.ring_radius1': [10000., None],
                      'obs_ring_geometry.ring_radius2': [40000., None]}
        sql, params = get_range_query(selections, 'obs_ring_geometry.ring_radius1', ['any', 'all'], [])
        print(sql)
        print(params)
        # 10000 to 40000
        expected = '`obs_ring_geometry`.`ring_radius2` >= %s AND `obs_ring_geometry`.`ring_radius1` <= %s'
        expected_params = [10000.0,40000.]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__range_query_clause_7(self):
        "[test_search.py] range_query: clause 7 qtype only second part both None"
        selections = {'obs_ring_geometry.ring_radius1': [10000., None],
                      'obs_ring_geometry.ring_radius2': [40000., None]}
        sql, params = get_range_query(selections, 'obs_ring_geometry.ring_radius1', ['any', 'only'], [])
        print(sql)
        print(params)
        # 10000 to 40000
        expected = '`obs_ring_geometry`.`ring_radius2` >= %s AND `obs_ring_geometry`.`ring_radius1` <= %s'
        expected_params = [10000.0,40000.]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__range_query_any_left_side_units_default(self):
        "[test_search.py] range_query: multi column range with qtype=any, min only, units default"
        selections = {'obs_ring_geometry.ring_radius1': [10000.],
                      'obs_ring_geometry.ring_radius2': [None]}
        sql, params = get_range_query(selections, 'obs_ring_geometry.ring_radius1', ['any'], ['km'])
        print(sql)
        print(params)
        # Effectively 10000 to inf
        expected = '`obs_ring_geometry`.`ring_radius2` >= %s'
        expected_params = [10000.0]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__range_query_any_right_side_units_default(self):
        "[test_search.py] range_query: multi column range with qtype=any, max only, units default"
        selections = {'obs_ring_geometry.ring_radius1': [None],
                      'obs_ring_geometry.ring_radius2': [40000.]}
        sql, params = get_range_query(selections, 'obs_ring_geometry.ring_radius1', ['any'], ['km'])
        print(sql)
        print(params)
        # Effectively -inf to 40000
        expected = '`obs_ring_geometry`.`ring_radius1` <= %s'
        expected_params = [40000.0]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__range_query_any_both_side_units_default(self):
        "[test_search.py] range_query: multi column range with qtype=any, both min and max, units default"
        selections = {'obs_ring_geometry.ring_radius1': [10000.],
                      'obs_ring_geometry.ring_radius2': [40000.]}
        sql, params = get_range_query(selections, 'obs_ring_geometry.ring_radius1', ['any'], ['km'])
        print(sql)
        print(params)
        # 10000 to 40000
        expected = '`obs_ring_geometry`.`ring_radius2` >= %s AND `obs_ring_geometry`.`ring_radius1` <= %s'
        expected_params = [10000.0,40000.]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__range_query_any_left_side_units_m(self):
        "[test_search.py] range_query: multi column range with qtype=any, min only, units m"
        selections = {'obs_ring_geometry.ring_radius1': [10000000.],
                      'obs_ring_geometry.ring_radius2': [None]}
        sql, params = get_range_query(selections, 'obs_ring_geometry.ring_radius1', ['any'], ['m'])
        print(sql)
        print(params)
        # Effectively 10000 to inf
        expected = '`obs_ring_geometry`.`ring_radius2` >= %s'
        expected_params = [10000.0]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__range_query_any_left_side_unit_overflow(self):
        "[test_search.py] range_query: multi column range with qtype=any, min only, unit overflow"
        selections = {'obs_ring_geometry.ring_radius1': [1e307],
                      'obs_ring_geometry.ring_radius2': [None]}
        sql, params = get_range_query(selections, 'obs_ring_geometry.ring_radius1', ['any'], ['saturnradii'])
        print(sql)
        print(params)
        self.assertIsNone(sql)
        self.assertIsNone(params)

    def test__range_query_any_right_side_units_m(self):
        "[test_search.py] range_query: multi column range with qtype=any, max only, units default"
        selections = {'obs_ring_geometry.ring_radius1': [None],
                      'obs_ring_geometry.ring_radius2': [40000000.]}
        sql, params = get_range_query(selections, 'obs_ring_geometry.ring_radius1', ['any'], ['m'])
        print(sql)
        print(params)
        # Effectively -inf to 40000
        expected = '`obs_ring_geometry`.`ring_radius1` <= %s'
        expected_params = [40000.0]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__range_query_any_right_side_unit_overflow(self):
        "[test_search.py] range_query: multi column range with qtype=any, max only, unit overflow"
        selections = {'obs_ring_geometry.ring_radius1': [None],
                      'obs_ring_geometry.ring_radius2': [1e307]}
        sql, params = get_range_query(selections, 'obs_ring_geometry.ring_radius1', ['any'], ['saturnradii'])
        print(sql)
        print(params)
        self.assertIsNone(sql)
        self.assertIsNone(params)

    def test__range_query_any_both_side_units_m(self):
        "[test_search.py] range_query: multi column range with qtype=any, both min and max, units default"
        selections = {'obs_ring_geometry.ring_radius1': [10000000.],
                      'obs_ring_geometry.ring_radius2': [40000000.]}
        sql, params = get_range_query(selections, 'obs_ring_geometry.ring_radius1', ['any'], ['m'])
        print(sql)
        print(params)
        # 10000 to 40000
        expected = '`obs_ring_geometry`.`ring_radius2` >= %s AND `obs_ring_geometry`.`ring_radius1` <= %s'
        expected_params = [10000.0,40000.]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__range_query_clause_3_units_default(self):
        "[test_search.py] range_query: clause 3 some each None units default"
        selections = {'obs_ring_geometry.ring_radius1': [10000., None, 60000.],
                      'obs_ring_geometry.ring_radius2': [40000., 50000., None]}
        sql, params = get_range_query(selections, 'obs_ring_geometry.ring_radius1', ['only', 'any', 'all'], ['km', 'km', 'km'])
        print(sql)
        print(params)
        # 10000 to 40000
        expected = '(`obs_ring_geometry`.`ring_radius1` >= %s AND `obs_ring_geometry`.`ring_radius2` <= %s) OR (`obs_ring_geometry`.`ring_radius1` <= %s) OR (`obs_ring_geometry`.`ring_radius1` <= %s)'
        expected_params = [10000.0,40000.,50000.,60000.]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__range_query_clause_3_units_various(self):
        "[test_search.py] range_query: clause 3 some each None units various"
        # We don't use 6xxx as the last value here because the floating point inaccuracy makes the assert fail
        selections = {'obs_ring_geometry.ring_radius1': [10000000., None, 80000000.],
                      'obs_ring_geometry.ring_radius2': [40000000., 50000., None]}
        sql, params = get_range_query(selections, 'obs_ring_geometry.ring_radius1', ['only', 'any', 'all'], ['m', 'km', 'm'])
        print(sql)
        print(params)
        # 10000 to 40000
        expected = '(`obs_ring_geometry`.`ring_radius1` >= %s AND `obs_ring_geometry`.`ring_radius2` <= %s) OR (`obs_ring_geometry`.`ring_radius1` <= %s) OR (`obs_ring_geometry`.`ring_radius1` <= %s)'
        expected_params = [10000.0,40000.,50000.,80000.]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__range_query_bad_none(self):
        "[test_search.py] range_query: no selections"
        selections = None
        sql, params = get_range_query(selections, 'obs_ring_geometry.ring_radius1', [], [])
        print(sql)
        print(params)
        self.assertIsNone(sql)
        self.assertIsNone(params)

    def test__range_query_bad_param(self):
        "[test_search.py] range_query: bad param"
        selections = {'obs_ring_geometry.ring_radius3': [100000.],
                      'obs_ring_geometry.ring_radius2': [200000.]}
        sql, params = get_range_query(selections, 'obs_ring_geometry.ring_radius1', [], [])
        print(sql)
        print(params)
        self.assertIsNone(sql)
        self.assertIsNone(params)

    def test__range_query_bad_param_2(self):
        "[test_search.py] range_query: bad param 2"
        selections = {'obs_ring_geometry.ring_radius1': [100000.],
                      'obs_ring_geometry.ring_radius2': [200000.]}
        sql, params = get_range_query(selections, 'obs_ring_geometry.ring_radius3', [], [])
        print(sql)
        print(params)
        self.assertIsNone(sql)
        self.assertIsNone(params)

    def test__range_query_clause_bad_length_qtypes(self):
        "[test_search.py] range_query: inconsistent length qtypes"
        selections = {'obs_ring_geometry.ring_radius1': [10000000., None, 8000000000.],
                      'obs_ring_geometry.ring_radius2': [40000000., 50000., None]}
        sql, params = get_range_query(selections, 'obs_ring_geometry.ring_radius1', ['only', 'all'], ['m', 'km', 'cm'])
        print(sql)
        print(params)
        self.assertIsNone(sql)
        self.assertIsNone(params)

    def test__range_query_clause_bad_length_units(self):
        "[test_search.py] range_query: inconsistent length units"
        selections = {'obs_ring_geometry.ring_radius1': [10000000., None, 8000000000.],
                      'obs_ring_geometry.ring_radius2': [40000000., 50000., None]}
        sql, params = get_range_query(selections, 'obs_ring_geometry.ring_radius1', ['only', 'all', 'all'], ['m', 'cm'])
        print(sql)
        print(params)
        self.assertIsNone(sql)
        self.assertIsNone(params)

    def test__range_query_bad_qtype(self):
        "[test_search.py] range_query: bad qtype"
        selections = {'obs_ring_geometry.ring_radius1': [10000000., None, 8000000000.],
                      'obs_ring_geometry.ring_radius2': [40000000., 50000., None]}
        sql, params = get_range_query(selections, 'obs_ring_geometry.ring_radius1', ['only', 'some', 'all'], ['m', 'km', 'cm'])
        print(sql)
        print(params)
        self.assertIsNone(sql)
        self.assertIsNone(params)

    def test__range_query_bad_unit(self):
        "[test_search.py] range_query: bad unit"
        selections = {'obs_ring_geometry.ring_radius1': [10000000., None, 8000000000.],
                      'obs_ring_geometry.ring_radius2': [40000000., 50000., None]}
        sql, params = get_range_query(selections, 'obs_ring_geometry.ring_radius1', ['only', 'all', 'all'], ['m', 'fred', 'cm'])
        print(sql)
        print(params)
        self.assertIsNone(sql)
        self.assertIsNone(params)


            ###################################################
            ######### get_longitude_query UNIT TESTS ##########
            ###################################################

    def test__longitude_query_single_col_range_left_side_no_right(self):
        "[test_search.py] longitude_query: single column long range with min only"
        selections = {'obs_type_image.duration1': [20.0]}
        sql, params = get_longitude_query(selections, 'obs_type_image.duration1', [], [])
        print(sql)
        print(params)
        expected = None # Can't have one-sided longitude queries
        expected_params = None
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__longitude_query_single_col_range_left_side(self):
        "[test_search.py] longitude_query: single column long range with min only"
        selections = {'obs_type_image.duration1': [20.0],
                      'obs_type_image.duration2': [None]}
        sql, params = get_longitude_query(selections, 'obs_type_image.duration1', [], [])
        print(sql)
        print(params)
        expected = '`obs_type_image`.`duration` >= %s'
        expected_params = [20.0]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__longitude_query_single_col_range_right_side(self):
        "[test_search.py] longitude_query: single column long range with max only"
        selections = {'obs_type_image.duration1': [None],
                      'obs_type_image.duration2': [180.0]}
        sql, params = get_longitude_query(selections, 'obs_type_image.duration1', [], [])
        print(sql)
        print(params)
        expected = '`obs_type_image`.`duration` <= %s'
        expected_params = [180.0]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__longitude_query_single_col_range_both_side(self):
        "[test_search.py] longitude_query: single column long range with both min and max"
        selections = {'obs_type_image.duration2': [180.0],
                      'obs_type_image.duration1': [20.0]}
        sql, params = get_longitude_query(selections, 'obs_type_image.duration1', [], [])
        print(sql)
        print(params)
        expected = '`obs_type_image`.`duration` >= %s AND `obs_type_image`.`duration` <= %s'
        expected_params = [20.0,180.0]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__longitude_query_single_col_range_all(self):
        "[test_search.py] longitude_query: single column long range with bogus qtype=all"
        selections = {'obs_type_image.duration2': [180.0],
                      'obs_type_image.duration1': [20.0]}
        sql, params = get_longitude_query(selections, 'obs_type_image.duration1', ['all'], [])
        print(sql)
        print(params)
        self.assertIsNone(sql)
        self.assertIsNone(params)

    def test__longitude_query_single_col_range_clause_1(self):
        "[test_search.py] longitude_query: single column long range clause 1 second both None"
        selections = {'obs_type_image.duration2': [180.0, None],
                      'obs_type_image.duration1': [20.0, None]}
        sql, params = get_longitude_query(selections, 'obs_type_image.duration1', ['any', 'any'], [])
        print(sql)
        print(params)
        expected = '`obs_type_image`.`duration` >= %s AND `obs_type_image`.`duration` <= %s'
        expected_params = [20.0,180.0]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__longitude_query_single_col_range_clause_2(self):
        "[test_search.py] longitude_query: single column long range clause 2 second one None"
        selections = {'obs_type_image.duration2': [180.0, None],
                      'obs_type_image.duration1': [20.0, 30.]}
        sql, params = get_longitude_query(selections, 'obs_type_image.duration1', ['any', 'any'], [])
        print(sql)
        print(params)
        expected = '(`obs_type_image`.`duration` >= %s AND `obs_type_image`.`duration` <= %s) OR (`obs_type_image`.`duration` >= %s)'
        expected_params = [20.0, 180.0, 30.0]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__longitude_query_single_col_range_clause_3(self):
        "[test_search.py] longitude_query: single column long range clause 3 second both OK"
        selections = {'obs_type_image.duration2': [180.0, 280.0],
                      'obs_type_image.duration1': [20.0, 220.0]}
        sql, params = get_longitude_query(selections, 'obs_type_image.duration1', ['any', 'any'], [])
        print(sql)
        print(params)
        expected = '(`obs_type_image`.`duration` >= %s AND `obs_type_image`.`duration` <= %s) OR (`obs_type_image`.`duration` >= %s AND `obs_type_image`.`duration` <= %s)'
        expected_params = [20.0,180.0,220.0,280.0]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__longitude_query_any_left_side_no_right(self):
        "[test_search.py] longitude_query: long range with qtype=any, min only"
        selections = {'obs_ring_geometry.J2000_longitude1': [240.]}
        sql, params = get_longitude_query(selections, 'obs_ring_geometry.J2000_longitude1', ['any'], [])
        print(sql)
        print(params)
        expected = None # Can't have one-sided longitude queries
        expected_params = None
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__longitude_query_any_left_side(self):
        "[test_search.py] longitude_query: long range with qtype=any, min only"
        selections = {'obs_ring_geometry.J2000_longitude1': [240.],
                      'obs_ring_geometry.J2000_longitude2': [None]}
        sql, params = get_longitude_query(selections, 'obs_ring_geometry.J2000_longitude1', ['any'], [])
        print(sql)
        print(params)
        expected = '`obs_ring_geometry`.`j2000_longitude2` >= %s'
        expected_params = [240.0]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__longitude_query_any_right_side(self):
        "[test_search.py] longitude_query: long range with qtype=any, max only"
        selections = {'obs_ring_geometry.J2000_longitude1': [None],
                      'obs_ring_geometry.J2000_longitude2': [310.5]}
        sql, params = get_longitude_query(selections, 'obs_ring_geometry.J2000_longitude1', ['any'], [])
        print(sql)
        print(params)
        expected = '`obs_ring_geometry`.`j2000_longitude1` <= %s'
        expected_params = [310.5]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__longitude_query_any_both_side(self):
        "[test_search.py] longitude_query: long range with qtype=any, both min and max"
        selections = {'obs_ring_geometry.J2000_longitude1': [240.],
                      'obs_ring_geometry.J2000_longitude2': [310.5]}
        sql, params = get_longitude_query(selections, 'obs_ring_geometry.J2000_longitude1', ['any'], [])
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
        "[test_search.py] longitude_query: long range with qtype=all, min only"
        selections = {'obs_ring_geometry.J2000_longitude1': [240.],
                      'obs_ring_geometry.J2000_longitude2': [None]}
        sql, params = get_longitude_query(selections, 'obs_ring_geometry.J2000_longitude1', ['all'], [])
        print(sql)
        print(params)
        expected = '`obs_ring_geometry`.`j2000_longitude1` <= %s'
        expected_params = [240.0]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__longitude_query_all_right_side(self):
        "[test_search.py] longitude_query: long range with qtype=all, max only"
        selections = {'obs_ring_geometry.J2000_longitude1': [None],
                      'obs_ring_geometry.J2000_longitude2': [310.5]}
        sql, params = get_longitude_query(selections, 'obs_ring_geometry.J2000_longitude1', ['all'], [])
        print(sql)
        print(params)
        expected = '`obs_ring_geometry`.`j2000_longitude2` >= %s'
        expected_params = [310.5]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__longitude_query_all_both_side(self):
        "[test_search.py] longitude_query: long range with qtype=all, both min and max"
        selections = {'obs_ring_geometry.J2000_longitude1': [240.],
                      'obs_ring_geometry.J2000_longitude2': [310.5]}
        sql, params = get_longitude_query(selections, 'obs_ring_geometry.J2000_longitude1', ['all'], [])
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
        "[test_search.py] longitude_query: long range with qtype=only, min only"
        selections = {'obs_ring_geometry.J2000_longitude1': [240.],
                      'obs_ring_geometry.J2000_longitude2': [None]}
        sql, params = get_longitude_query(selections, 'obs_ring_geometry.J2000_longitude1', ['only'], [])
        print(sql)
        print(params)
        expected = '`obs_ring_geometry`.`j2000_longitude1` >= %s'
        expected_params = [240.0]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__longitude_query_only_right_side(self):
        "[test_search.py] longitude_query: long range with qtype=only, max only"
        selections = {'obs_ring_geometry.J2000_longitude1': [None],
                      'obs_ring_geometry.J2000_longitude2': [310.5]}
        sql, params = get_longitude_query(selections, 'obs_ring_geometry.J2000_longitude1', ['only'], [])
        print(sql)
        print(params)
        expected = '`obs_ring_geometry`.`j2000_longitude2` <= %s'
        expected_params = [310.5]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__longitude_query_only_both_side(self):
        "[test_search.py] longitude_query: long range with qtype=only, both min and max"
        selections = {'obs_ring_geometry.J2000_longitude1': [240.],
                      'obs_ring_geometry.J2000_longitude2': [310.5]}
        sql, params = get_longitude_query(selections, 'obs_ring_geometry.J2000_longitude1', ['only'], [])
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
        "[test_search.py] longitude_query: single column long range with both min and max"
        selections = {'obs_type_image.duration1': [180.0],
                      'obs_type_image.duration2': [20.0]}
        sql, params = get_longitude_query(selections, 'obs_type_image.duration1', ['any'], [])
        print(sql)
        print(params)
        expected = '`obs_type_image`.`duration` >= %s OR `obs_type_image`.`duration` <= %s'
        expected_params = [180.0,20.0]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__longitude_query_any_both_side_wrap(self):
        "[test_search.py] longitude_query: long range with qtype=any, both min and max"
        selections = {'obs_ring_geometry.J2000_longitude1': [240.],
                      'obs_ring_geometry.J2000_longitude2': [30.5]}
        sql, params = get_longitude_query(selections, 'obs_ring_geometry.J2000_longitude1', ['any'], [])
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
        "[test_search.py] longitude_query: long range with qtype=all, both min and max"
        selections = {'obs_ring_geometry.J2000_longitude1': [240.],
                      'obs_ring_geometry.J2000_longitude2': [30.5]}
        sql, params = get_longitude_query(selections, 'obs_ring_geometry.J2000_longitude1', ['all'], [])
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
        "[test_search.py] longitude_query: long range with qtype=only, both min and max"
        selections = {'obs_ring_geometry.J2000_longitude1': [240.],
                      'obs_ring_geometry.J2000_longitude2': [30.5]}
        sql, params = get_longitude_query(selections, 'obs_ring_geometry.J2000_longitude1', ['only'], [])
        print(sql)
        print(params)
        # 240 to 30.5
        expected = 'ABS(MOD(%s - obs_ring_geometry.J2000_longitude + 540., 360.) - 180.) <= %s - obs_ring_geometry.d_j2000_longitude'
        expected_params = [315.25, 75.25]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__longitude_query_all_clause_1(self):
        "[test_search.py] longitude_query: long range with qtype=all, clause 1 second both None"
        selections = {'obs_ring_geometry.J2000_longitude1': [240., None],
                      'obs_ring_geometry.J2000_longitude2': [310.5, None]}
        sql, params = get_longitude_query(selections, 'obs_ring_geometry.J2000_longitude1', ['all', 'all'], [])
        print(sql)
        print(params)
        # 240 to 310.5
        expected = 'ABS(MOD(%s - obs_ring_geometry.J2000_longitude + 540., 360.) - 180.) <= obs_ring_geometry.d_j2000_longitude - %s'
        expected_params = [275.25, 35.25]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__longitude_query_all_clause_2(self):
        "[test_search.py] longitude_query: long range with qtype=all, clause 2 second one None"
        selections = {'obs_ring_geometry.J2000_longitude1': [240., 20.],
                      'obs_ring_geometry.J2000_longitude2': [310.5, None]}
        sql, params = get_longitude_query(selections, 'obs_ring_geometry.J2000_longitude1', ['all'], [])
        print(sql)
        print(params)
        expected = None
        expected_params = None
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__longitude_query_only_all_both_side_clause_3(self):
        "[test_search.py] longitude_query: long range with qtype=only, clause 3 both OK"
        selections = {'obs_ring_geometry.J2000_longitude1': [240., 250.],
                      'obs_ring_geometry.J2000_longitude2': [30.5, 40.5]}
        sql, params = get_longitude_query(selections, 'obs_ring_geometry.J2000_longitude1', ['only', 'all'], [])
        print(sql)
        print(params)
        # 240 to 30.5
        expected = '(ABS(MOD(%s - obs_ring_geometry.J2000_longitude + 540., 360.) - 180.) <= %s - obs_ring_geometry.d_j2000_longitude) OR (ABS(MOD(%s - obs_ring_geometry.J2000_longitude + 540., 360.) - 180.) <= obs_ring_geometry.d_j2000_longitude - %s)'
        expected_params = [315.25, 75.25, 325.25, 75.25]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__longitude_query_all_clause_4(self):
        "[test_search.py] longitude_query: long range with qtype=all, clause 4 wrote qtype len"
        selections = {'obs_ring_geometry.J2000_longitude1': [240., None],
                      'obs_ring_geometry.J2000_longitude2': [310.5, None]}
        # Inconsistent qtype length
        sql, params = get_longitude_query(selections, 'obs_ring_geometry.J2000_longitude1', ['all'], [])
        print(sql)
        print(params)
        expected = None
        expected_params = None
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__longitude_query_single_col_range_left_side_units_default(self):
        "[test_search.py] longitude_query: single column long range with min only units default"
        selections = {'obs_type_image.duration1': [20.0],
                      'obs_type_image.duration2': [None]}
        sql, params = get_longitude_query(selections, 'obs_type_image.duration1', [], ['seconds'])
        print(sql)
        print(params)
        expected = '`obs_type_image`.`duration` >= %s'
        expected_params = [20.0]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__longitude_query_single_col_range_right_side_units_default(self):
        "[test_search.py] longitude_query: single column long range with max only units default"
        selections = {'obs_type_image.duration1': [None],
                      'obs_type_image.duration2': [180.0]}
        sql, params = get_longitude_query(selections, 'obs_type_image.duration1', [], ['seconds'])
        print(sql)
        print(params)
        expected = '`obs_type_image`.`duration` <= %s'
        expected_params = [180.0]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__longitude_query_single_col_range_both_side_units_default(self):
        "[test_search.py] longitude_query: single column long range with both min and max units default"
        selections = {'obs_type_image.duration2': [180.0],
                      'obs_type_image.duration1': [20.0]}
        sql, params = get_longitude_query(selections, 'obs_type_image.duration1', [], ['seconds'])
        print(sql)
        print(params)
        expected = '`obs_type_image`.`duration` >= %s AND `obs_type_image`.`duration` <= %s'
        expected_params = [20.0,180.0]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__longitude_query_bad_none_single(self):
        "[test_search.py] longitude_query: no selections single column"
        selections = None
        sql, params = get_longitude_query(selections, 'obs_type_image.duration1', [], [])
        print(sql)
        print(params)
        self.assertIsNone(sql)
        self.assertIsNone(params)

    def test__longitude_query_bad_param_single(self):
        "[test_search.py] longitude_query: bad param single column"
        selections = {'obs_type_image.duration1': [20.0],
                      'obs_type_image.duration2': [30.0]}
        sql, params = get_longitude_query(selections, 'obs_type_image.duration3', [], [])
        print(sql)
        print(params)
        self.assertIsNone(sql)
        self.assertIsNone(params)

    def test__longitude_query_bad_qtype_single(self):
        "[test_search.py] longitude_query: bad qtype single column"
        selections = {'obs_type_image.duration1': [20.0, 30.0, 40.0],
                      'obs_type_image.duration2': [25.0, 35.0, 45.0]}
        sql, params = get_longitude_query(selections, 'obs_type_image.duration1', ['any', 'only', 'any'], ['degrees', 'degrees', 'degrees'])
        print(sql)
        print(params)
        self.assertIsNone(sql)
        self.assertIsNone(params)

    def test__longitude_query_bad_qtype_single_min(self):
        "[test_search.py] longitude_query: bad qtype single column"
        selections = {'obs_type_image.duration1': [20.0, 30.0, 40.0],
                      'obs_type_image.duration2': [25.0, None, 45.0]}
        sql, params = get_longitude_query(selections, 'obs_type_image.duration1', ['any', 'only', 'any'], ['seconds', 'seconds', 'seconds'])
        print(sql)
        print(params)
        self.assertIsNone(sql)
        self.assertIsNone(params)

    def test__longitude_query_bad_unit_single(self):
        "[test_search.py] longitude_query: bad unit single column"
        selections = {'obs_type_image.duration1': [10000000., 40000., 8000000000.],
                      'obs_type_image.duration2': [40000000., 50000., None]}
        sql, params = get_longitude_query(selections, 'obs_type_image.duration1', ['any', 'any', 'any'], ['seconds', 'km', 'seconds'])
        print(sql)
        print(params)
        self.assertIsNone(sql)
        self.assertIsNone(params)

    def test__longitude_query_bad_unit_single_min(self):
        "[test_search.py] longitude_query: bad unit single column min"
        selections = {'obs_type_image.duration1': [10000000., 40000., 8000000000.],
                      'obs_type_image.duration2': [40000000., None,   9000000000.]}
        sql, params = get_longitude_query(selections, 'obs_type_image.duration1', ['any', 'any', 'any'], ['seconds', 'km', 'seconds'])
        print(sql)
        print(params)
        self.assertIsNone(sql)
        self.assertIsNone(params)

    def test__longitude_query_bad_none(self):
        "[test_search.py] longitude_query: no selections"
        selections = None
        sql, params = get_longitude_query(selections, 'obs_ring_geometry.J2000_longitude1', [], [])
        print(sql)
        print(params)
        self.assertIsNone(sql)
        self.assertIsNone(params)

    def test__longitude_query_bad_param(self):
        "[test_search.py] longitude_query: bad param"
        selections = {'obs_ring_geometry.J2000_longitude1': [20.0],
                      'obs_ring_geometry.J2000_longitude2': [30.0]}
        sql, params = get_longitude_query(selections, 'obs_ring_geometry.J2000_longitude3', [], [])
        print(sql)
        print(params)
        self.assertIsNone(sql)
        self.assertIsNone(params)

    def test__longitude_query_clause_bad_length_qtypes(self):
        "[test_search.py] longitude_query: inconsistent length qtypes"
        selections = {'obs_ring_geometry.J2000_longitude1': [20.0, 30.0, 40.0],
                      'obs_ring_geometry.J2000_longitude2': [25.0, 35.0, 45.0]}
        sql, params = get_longitude_query(selections, 'obs_ring_geometry.J2000_longitude1', ['only', 'all'], ['degrees', 'degrees', 'degrees'])
        print(sql)
        print(params)
        self.assertIsNone(sql)
        self.assertIsNone(params)

    def test__longitude_query_clause_bad_length_units(self):
        "[test_search.py] longitude_query: inconsistent length units"
        selections = {'obs_ring_geometry.J2000_longitude1': [20.0, 30.0, 40.0],
                      'obs_ring_geometry.J2000_longitude2': [25.0, 35.0, 45.0]}
        sql, params = get_longitude_query(selections, 'obs_ring_geometry.J2000_longitude1', ['only', 'all', 'all'], ['degrees', 'degrees'])
        print(sql)
        print(params)
        self.assertIsNone(sql)
        self.assertIsNone(params)

    def test__longitude_query_bad_qtype(self):
        "[test_search.py] longitude_query: bad qtype"
        selections = {'obs_ring_geometry.J2000_longitude1': [20.0, 30.0, 40.0],
                      'obs_ring_geometry.J2000_longitude2': [25.0, 35.0, 45.0]}
        sql, params = get_longitude_query(selections, 'obs_ring_geometry.J2000_longitude1', ['only', 'many', 'all'], ['degrees', 'degrees', 'degrees'])
        print(sql)
        print(params)
        self.assertIsNone(sql)
        self.assertIsNone(params)

    def test__longitude_query_bad_qtype_max(self):
        "[test_search.py] longitude_query: bad qtype max"
        selections = {'obs_ring_geometry.J2000_longitude1': [20.0, None, 40.0],
                      'obs_ring_geometry.J2000_longitude2': [25.0, 35.0, 45.0]}
        sql, params = get_longitude_query(selections, 'obs_ring_geometry.J2000_longitude1', ['only', 'many', 'all'], ['degrees', 'degrees', 'degrees'])
        print(sql)
        print(params)
        self.assertIsNone(sql)
        self.assertIsNone(params)

    def test__longitude_query_bad_unit(self):
        "[test_search.py] longitude_query: bad unit"
        selections = {'obs_ring_geometry.J2000_longitude1': [10000000., None, 8000000000.],
                      'obs_ring_geometry.J2000_longitude2': [40000000., 50000., None]}
        sql, params = get_range_query(selections, 'obs_ring_geometry.J2000_longitude1', ['only', 'all', 'all'], ['degrees', 'km', 'degrees'])
        print(sql)
        print(params)
        self.assertIsNone(sql)
        self.assertIsNone(params)

    def test__longitude_query_bad_unit_max(self):
        "[test_search.py] longitude_query: bad unit"
        selections = {'obs_ring_geometry.J2000_longitude1': [10000000., 50000., 8000000000.],
                      'obs_ring_geometry.J2000_longitude2': [40000000., None,   9000000000.]}
        sql, params = get_range_query(selections, 'obs_ring_geometry.J2000_longitude1', ['only', 'all', 'all'], ['degrees', 'km', 'degrees'])
        print(sql)
        print(params)
        self.assertIsNone(sql)
        self.assertIsNone(params)


            ###############################################
            ######### get_string_query UNIT TESTS #########
            ###############################################

    def test__string_query(self):
        "[test_search.py] string_query: string query with no qtype"
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
        "[test_search.py] string_query: string query with qtype contains"
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
        "[test_search.py] string_query: string query with qtype begins"
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
        "[test_search.py] string_query: string query with qtype ends"
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
        "[test_search.py] string_query: string query with qtype matches"
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
        "[test_search.py] string_query: string query with qtype excludes"
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

    def test__string_query_regex(self):
        "[test_search.py] string_query: string query with qtype regex"
        selections = {'obs_pds.volume_id': [r'^COISS.\d\d\d\d$']}
        sql, params = get_string_query(selections, 'obs_pds.volume_id',
                                       ['regex'])
        print(sql)
        print(params)
        expected = '`obs_pds`.`volume_id` RLIKE %s'
        expected_params = [r'^COISS.\d\d\d\d$']
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__string_query_ends_special_chars(self):
        "[test_search.py] string_query: string query with qtype matches special chars"
        selections = {'obs_pds.volume_id': ['ISS_\\%\\X\\']}
        sql, params = get_string_query(selections, 'obs_pds.volume_id',
                                       ['ends'])
        print(sql)
        print(params)
        expected = '`obs_pds`.`volume_id` LIKE %s'
        expected_params = ['%ISS\\_\\\\\\%\\\\X\\\\']
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__string_query_matches_special_chars(self):
        "[test_search.py] string_query: string query with qtype matches special chars"
        selections = {'obs_pds.volume_id': ['ISS_\\%\\X\\']}
        sql, params = get_string_query(selections, 'obs_pds.volume_id',
                                       ['matches'])
        print(sql)
        print(params)
        expected = '`obs_pds`.`volume_id` = %s'
        expected_params = ['ISS_\\\\%\\\\X\\\\']
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__string_query_clause(self):
        "[test_search.py] string_query: string query with qtype clause"
        selections = {'obs_pds.volume_id': ['ISS', 'COUVIS']}
        sql, params = get_string_query(selections, 'obs_pds.volume_id',
                                       ['excludes', 'matches'])
        print(sql)
        print(params)
        expected = '(`obs_pds`.`volume_id` NOT LIKE %s) OR (`obs_pds`.`volume_id` = %s)'
        expected_params = ['%ISS%', 'COUVIS']
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__string_query_bad_none(self):
        "[test_search.py] string_query: no selections"
        selections = None
        sql, params = get_string_query(selections, 'obs_pds.volume_id', [])
        print(sql)
        print(params)
        self.assertIsNone(sql)
        self.assertIsNone(params)

    def test__string_query_bad_param(self):
        "[test_search.py] string_query: bad param"
        selections = {'obs_pds.volume_id': ['ISS', 'COUVIS']}
        sql, params = get_string_query(selections, 'obs_pds.note', [])
        print(sql)
        print(params)
        self.assertIsNone(sql)
        self.assertIsNone(params)

    def test__string_query_bad_param_2(self):
        "[test_search.py] string_query: bad param 2"
        selections = {'obs_pds.volume_idXX': ['ISS']}
        sql, params = get_string_query(selections, 'obs_pds.volume_id', [])
        print(sql)
        print(params)
        self.assertIsNone(sql)
        self.assertIsNone(params)

    def test__string_query_bad_param_3(self):
        "[test_search.py] string_query: bad param 3"
        selections = {'obs_pds.volume_id': ['ISS', 'COUVIS']}
        sql, params = get_string_query(selections, 'obs_pds.noteXXX', [])
        print(sql)
        print(params)
        self.assertIsNone(sql)
        self.assertIsNone(params)

    def test__string_query_clause_bad_length(self):
        "[test_search.py] string_query: string query with qtype clause inconsistent length"
        selections = {'obs_pds.volume_id': ['ISS', 'COUVIS']}
        sql, params = get_string_query(selections, 'obs_pds.volume_id',
                                       ['excludes', 'matches', 'excludes'])
        print(sql)
        print(params)
        self.assertIsNone(sql)
        self.assertIsNone(params)

    def test__string_query_bad_qtype(self):
        "[test_search.py] string_query: string query with bad qtype"
        selections = {'obs_pds.volume_id': ['ISS']}
        sql, params = get_string_query(selections, 'obs_pds.volume_id',
                                       ['excludesXXX'])
        print(sql)
        print(params)
        self.assertIsNone(sql)
        self.assertIsNone(params)


            #####################################################
            ######### construct_query_string UNIT TESTS #########
            #####################################################

    def test__construct_query_string_bad_paraminfo(self):
        "[test_search.py] construct_query_string: unknown param name"
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
        "[test_search.py] construct_query_string: unknown param name #2"
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
        "[test_search.py] construct_query_string: unknown param name #3"
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
        "[test_search.py] construct_query_string: unknown param name #4"
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
        "[test_search.py] construct_query_string: just obs_general"
        selections = {'obs_general.observation_duration1': [20],
                      'obs_general.observation_duration2': [None]}
        extras = {}
        sql, params = construct_query_string(selections, extras)
        print(sql)
        print(params)
        expected = 'SELECT `obs_general`.`id` FROM `obs_general` WHERE `obs_general`.`observation_duration` >= %s'
        expected_params = [20]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__construct_query_string_nojoin_unit_overflow(self):
        "[test_search.py] construct_query_string: just obs_general, unit overflow"
        selections = {'obs_general.observation_duration1': [1e307],
                      'obs_general.observation_duration2': [None]}
        extras = {'units': {'obs_general.observation_duration': 'days'}}
        sql, params = construct_query_string(selections, extras)
        print(sql)
        print(params)
        self.assertIsNone(sql)
        self.assertIsNone(params)

    def test__construct_query_string_string(self):
        "[test_search.py] construct_query_string: a string"
        selections = {'obs_pds.primary_filespec': ['C11399XX']}
        extras = {}
        sql, params = construct_query_string(selections, extras)
        print(sql)
        print(params)
        expected = 'SELECT `obs_general`.`id` FROM `obs_general` LEFT JOIN `obs_pds` ON `obs_general`.`id`=`obs_pds`.`obs_general_id` WHERE `obs_pds`.`primary_filespec` LIKE %s'
        expected_params = ['%C11399XX%']
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__construct_query_string_single_column_range(self):
        "[test_search.py] construct_query_string: a single column range"
        selections = {'obs_type_image.duration1': [20.0],
                      'obs_type_image.duration2': [180.0]}
        extras = {}
        sql, params = construct_query_string(selections, extras)
        print(sql)
        print(params)
        expected = 'SELECT `obs_general`.`id` FROM `obs_general` LEFT JOIN `obs_type_image` ON `obs_general`.`id`=`obs_type_image`.`obs_general_id` WHERE `obs_type_image`.`duration` >= %s AND `obs_type_image`.`duration` <= %s'
        expected_params = [20.0, 180.0]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__construct_query_string_single_column_range_unit_overflow(self):
        "[test_search.py] construct_query_string: a single column range, unit overflow"
        selections = {'obs_type_image.duration1': [20.0],
                      'obs_type_image.duration2': [1e307]}
        extras = {'units': {'obs_type_image.duration': 'msecs'}}
        sql, params = construct_query_string(selections, extras)
        print(sql)
        print(params)
        self.assertIsNone(sql)
        self.assertIsNone(params)

    def test__construct_query_string_longitude_range(self):
        "[test_search.py] construct_query_string: a single column range"
        selections = {'obs_ring_geometry.J2000_longitude1': [240.],
                      'obs_ring_geometry.J2000_longitude2': [310.5]}
        extras = {}
        sql, params = construct_query_string(selections, extras)
        print(sql)
        print(params)
        # 240 to 310.5
        expected = 'SELECT `obs_general`.`id` FROM `obs_general` LEFT JOIN `obs_ring_geometry` ON `obs_general`.`id`=`obs_ring_geometry`.`obs_general_id` WHERE ABS(MOD(%s - obs_ring_geometry.J2000_longitude + 540., 360.) - 180.) <= %s + obs_ring_geometry.d_j2000_longitude'
        expected_params = [275.25, 35.25]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__construct_query_string_longitude_range_bad_qtype(self):
        "[test_search.py] construct_query_string: a single column range"
        selections = {'obs_ring_geometry.J2000_longitude1': [240.],
                      'obs_ring_geometry.J2000_longitude2': [310.5]}
        extras = {'qtypes': {'obs_ring_geometry.J2000_longitude': ['fred']}}
        sql, params = construct_query_string(selections, extras)
        print(sql)
        print(params)
        self.assertIsNone(sql)
        self.assertIsNone(params)

    def test__construct_query_string_longitude_range_unit_overflow(self):
        "[test_search.py] construct_query_string: a single column range, unit overflow"
        selections = {'obs_ring_geometry.J2000_longitude1': [1e307],
                      'obs_ring_geometry.J2000_longitude2': [310.5]}
        extras = {'units': {'obs_ring_geometry.J2000_longitude': ['radians']}}
        sql, params = construct_query_string(selections, extras)
        print(sql)
        print(params)
        self.assertIsNone(sql)
        self.assertIsNone(params)

    def test__construct_query_string_single_column_range_clause(self):
        "[test_search.py] construct_query_string: a single column range clause"
        selections = {'obs_type_image.duration1': [20.0, 200.0],
                      'obs_type_image.duration2': [180.0, 300.0]}
        extras = {}
        sql, params = construct_query_string(selections, extras)
        print(sql)
        print(params)
        expected = 'SELECT `obs_general`.`id` FROM `obs_general` LEFT JOIN `obs_type_image` ON `obs_general`.`id`=`obs_type_image`.`obs_general_id` WHERE (`obs_type_image`.`duration` >= %s AND `obs_type_image`.`duration` <= %s) OR (`obs_type_image`.`duration` >= %s AND `obs_type_image`.`duration` <= %s)'
        expected_params = [20.0, 180.0, 200.0, 300.0]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__construct_query_string_string_with_qtype(self):
        "[test_search.py] construct_query_string: a string and qtype"
        selections = {'obs_pds.primary_filespec': ['C11399XX']}
        extras = {'qtypes': {'obs_pds.primary_filespec': ['begins']}}
        sql, params = construct_query_string(selections, extras)
        print(sql)
        print(params)
        expected = 'SELECT `obs_general`.`id` FROM `obs_general` LEFT JOIN `obs_pds` ON `obs_general`.`id`=`obs_pds`.`obs_general_id` WHERE `obs_pds`.`primary_filespec` LIKE %s'
        expected_params = ['C11399XX%']
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__construct_query_string_string_with_qtype_clause(self):
        "[test_search.py] construct_query_string: a string and qtype clause"
        selections = {'obs_pds.primary_filespec': ['C11399XX', 'C11399YY']}
        extras = {'qtypes': {'obs_pds.primary_filespec': ['begins', 'ends']}}
        sql, params = construct_query_string(selections, extras)
        print(sql)
        print(params)
        expected = 'SELECT `obs_general`.`id` FROM `obs_general` LEFT JOIN `obs_pds` ON `obs_general`.`id`=`obs_pds`.`obs_general_id` WHERE (`obs_pds`.`primary_filespec` LIKE %s) OR (`obs_pds`.`primary_filespec` LIKE %s)'
        expected_params = ['C11399XX%', '%C11399YY']
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__construct_query_string_mults_planet(self):
        "[test_search.py] construct_query_string: planet_id"
        selections = {'obs_general.planet_id': ['Saturn']}
        extras = {}
        sql, params = construct_query_string(selections, extras)
        print(sql)
        print(params)
        expected = 'SELECT `obs_general`.`id` FROM `obs_general` WHERE `obs_general`.`planet_id` IN (%s)'
        expected_params = [4]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__construct_query_string_mults_planet_uc(self):
        "[test_search.py] construct_query_string: planet_id in upper case"
        selections = {'obs_general.planet_id': ['SATURN']}
        extras = {}
        sql, params = construct_query_string(selections, extras)
        print(sql)
        print(params)
        expected = 'SELECT `obs_general`.`id` FROM `obs_general` WHERE `obs_general`.`planet_id` IN (%s)'
        expected_params = [4]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__construct_query_string_mults_empty(self):
        "[test_search.py] construct_query_string: planet_id empty"
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
        "[test_search.py] construct_query_string: planet_id unknown planet"
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
        "[test_search.py] construct_query_string: two mults"
        selections = {'obs_general.planet_id': ['Saturn'],
                      'obs_general.instrument_id': ['COISS']}
        extras = {}
        sql, params = construct_query_string(selections, extras)
        print(sql)
        print(params)
        expected = 'SELECT `obs_general`.`id` FROM `obs_general` WHERE (`obs_general`.`instrument_id` IN (%s)) AND (`obs_general`.`planet_id` IN (%s))'
        expected_params = [1, 4]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__construct_query_string_mults_with_join(self):
        "[test_search.py] construct_query_string: obs_general and obs_instrument_coiss"
        selections = {'obs_general.planet_id': ['Saturn'],
                      'obs_instrument_coiss.camera': ['Wide Angle']}
        extras = {}
        sql, params = construct_query_string(selections, extras)
        print(sql)
        print(params)
        expected = 'SELECT `obs_general`.`id` FROM `obs_general` LEFT JOIN `obs_instrument_coiss` ON `obs_general`.`id`=`obs_instrument_coiss`.`obs_general_id` WHERE (`obs_general`.`planet_id` IN (%s)) AND (`obs_instrument_coiss`.`camera` IN (%s))'
        expected_params = [4, 1]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__construct_query_string_mults_with_3_table_join(self):
        "[test_search.py] construct_query_string: three tables"
        selections = {'obs_general.planet_id': ['Saturn'],
                      'obs_instrument_coiss.camera': ['Narrow Angle'],
                      'obs_mission_cassini.rev_no': ['00A','00C']}
        extras = {}
        sql, params = construct_query_string(selections, extras)
        print(sql)
        print(params)
        expected = 'SELECT `obs_general`.`id` FROM `obs_general` LEFT JOIN `obs_instrument_coiss` ON `obs_general`.`id`=`obs_instrument_coiss`.`obs_general_id` LEFT JOIN `obs_mission_cassini` ON `obs_general`.`id`=`obs_mission_cassini`.`obs_general_id` WHERE (`obs_general`.`planet_id` IN (%s)) AND (`obs_instrument_coiss`.`camera` IN (%s)) AND (`obs_mission_cassini`.`rev_no` IN (%s,%s))'
        expected_params = [4, 0, 2, 4]
        print(expected)
        print(expected_params)
        print('NOTE: This test requires one of COISS or COVIMS to be imported before COUVIS due to a bad observation name in COUVIS!')
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__construct_query_string_order_existing_table(self):
        "[test_search.py] construct_query_string: sort order already joined"
        selections = {'obs_general.observation_duration1': [20],
                      'obs_general.observation_duration2': [None]}
        extras = {'order': (['obs_general.time1'], [False])}
        sql, params = construct_query_string(selections, extras)
        print(sql)
        print(params)
        expected = 'SELECT `obs_general`.`id` FROM `obs_general` WHERE `obs_general`.`observation_duration` >= %s ORDER BY obs_general.time1 ASC'
        expected_params = [20]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__construct_query_string_order_existing_table_2(self):
        "[test_search.py] construct_query_string: sort order already joined #2"
        selections = {'obs_general.observation_duration1': [20],
                      'obs_general.observation_duration2': [None],
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
        "[test_search.py] construct_query_string: complex sort order already joined"
        selections = {'obs_general.observation_duration1': [20],
                      'obs_general.observation_duration2': [None]}
        extras = {'order': (['obs_general.time1',
                             'obs_general.time2'],
                            [False, True])}
        sql, params = construct_query_string(selections, extras)
        print(sql)
        print(params)
        expected = 'SELECT `obs_general`.`id` FROM `obs_general` WHERE `obs_general`.`observation_duration` >= %s ORDER BY obs_general.time1 ASC,obs_general.time2 DESC'
        expected_params = [20]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__construct_query_string_order_new_table(self):
        "[test_search.py] construct_query_string: sort order not already joined"
        selections = {'obs_general.observation_duration1': [20],
                      'obs_general.observation_duration2': [None]}
        extras = {'order': (['obs_pds.volume_id'], [False])}
        sql, params = construct_query_string(selections, extras)
        print(sql)
        print(params)
        expected = 'SELECT `obs_general`.`id` FROM `obs_general` LEFT JOIN `obs_pds` ON `obs_general`.`id`=`obs_pds`.`obs_general_id` WHERE `obs_general`.`observation_duration` >= %s ORDER BY obs_pds.volume_id ASC'
        expected_params = [20]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__construct_query_string_order_new_table_2(self):
        "[test_search.py] construct_query_string: sort order not already joined 2"
        selections = {'obs_general.observation_duration1': [20],
                      'obs_general.observation_duration2': [None]}
        extras = {'order': (['obs_instrument_coiss.data_conversion_type'], [False])}
        sql, params = construct_query_string(selections, extras)
        print(sql)
        print(params)
        expected = 'SELECT `obs_general`.`id` FROM `obs_general` LEFT JOIN `obs_instrument_coiss` ON `obs_general`.`id`=`obs_instrument_coiss`.`obs_general_id` LEFT JOIN `mult_obs_instrument_coiss_data_conversion_type` ON `obs_instrument_coiss`.`data_conversion_type`=`mult_obs_instrument_coiss_data_conversion_type`.`id` WHERE `obs_general`.`observation_duration` >= %s ORDER BY mult_obs_instrument_coiss_data_conversion_type.label ASC'
        expected_params = [20]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__construct_query_string_order_bad(self):
        "[test_search.py] construct_query_string: sort order bad"
        selections = {'obs_general.observation_duration1': [20],
                      'obs_general.observation_duration2': [None]}
        extras = {'order': (['obs_general.time3'], [False])}
        sql, params = construct_query_string(selections, extras)
        print(sql)
        print(params)
        self.assertIsNone(sql)
        self.assertIsNone(params)

    def test__construct_query_string_mults_multigroup_target_single(self):
        "[test_search.py] construct_query_string: obs_general intended_target single"
        selections = {'obs_general.target_name': ['Saturn']}
        extras = {}
        sql, params = construct_query_string(selections, extras)
        print(sql)
        print(params)
        expected = 'SELECT `obs_general`.`id` FROM `obs_general` WHERE JSON_CONTAINS(`obs_general`.`target_name`,%s)'
        expected_params = ['1']
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__construct_query_string_mults_multigroup_target_dual(self):
        "[test_search.py] construct_query_string: obs_general intended_target dual"
        selections = {'obs_general.target_name': ['Saturn', 'Jupiter']}
        extras = {}
        sql, params = construct_query_string(selections, extras)
        print(sql)
        print(params)
        expected = 'SELECT `obs_general`.`id` FROM `obs_general` WHERE JSON_CONTAINS(`obs_general`.`target_name`,%s) OR JSON_CONTAINS(`obs_general`.`target_name`,%s)'
        expected_params = ['1', '19']
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__construct_query_string_mults_multigroup_target_order(self):
        "[test_search.py] construct_query_string: obs_general intended_target sort"
        selections = {}
        extras = {'order': (['obs_general.target_name'], [False])}
        sql, params = construct_query_string(selections, extras)
        print(sql)
        print(params)
        expected = 'SELECT `obs_general`.`id` FROM `obs_general` LEFT JOIN `mult_obs_general_target_name` ON JSON_EXTRACT(`obs_general`.`target_name`, "$[0]")=`mult_obs_general_target_name`.`id` ORDER BY mult_obs_general_target_name.label ASC'
        expected_params = []
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)


            #####################################################
            ######### set_user_search_number UNIT TESTS #########
            #####################################################

    def test__set_user_search_number_dead_qtype_str(self):
        "[test_search.py] set_user_search_number: dead qtype string"
        selections = {'obs_pds.volume_id': ['FRED']}
        extras = {'qtypes': {'obs_pds.volume_id': ['excludes']},
                  'units': {},
                  'order': (['obs_pds.volume_id'], [False])}
        num1 = set_user_search_number(selections, extras)
        extras = {'qtypes': {'obs_pds.volume_id': ['excludes'],
                             'obs_pds.data_set_id': ['matches']}, # goes away
                  'units': {},
                  'order': (['obs_pds.volume_id'], [False])}
        num2 = set_user_search_number(selections, extras)
        self.assertEqual(num1, (1, True))
        self.assertEqual(num2, (1, False))

    def test__set_user_search_number_dead_qtype_num_1(self):
        "[test_search.py] set_user_search_number: dead qtype numeric 1"
        selections = {'obs_general.declination1': ['1']}
        extras = {'qtypes': {'obs_general.declination1': ['any']},
                  'units': {'obs_general.declination1': ['degrees']},
                  'order': (['obs_general.time1'], [False])}
        num1 = set_user_search_number(selections, extras)
        extras = {'qtypes': {'obs_general.declination1': ['any'],
                             'obs_general.right_asc1': ['only']}, # goes away
                  'units': {'obs_general.declination1': ['degrees']},
                  'order': (['obs_general.time1'], [False])}
        num2 = set_user_search_number(selections, extras)
        self.assertEqual(num1, (1, True))
        self.assertEqual(num2, (1, False))

    def test__set_user_search_number_dead_qtype_num_2(self):
        "[test_search.py] set_user_search_number: dead qtype numeric 2"
        selections = {'obs_general.declination2': ['1']}
        extras = {'qtypes': {'obs_general.declination1': ['any']},
                  'units': {'obs_general.declination1': ['degrees']},
                  'order': (['obs_general.time1'], [False])}
        num1 = set_user_search_number(selections, extras)
        extras = {'qtypes': {'obs_general.declination1': ['any'],
                             'obs_general.right_asc1': ['only']}, # goes away
                  'units': {'obs_general.declination1': ['degrees']},
                  'order': (['obs_general.time1'], [False])}
        num2 = set_user_search_number(selections, extras)
        self.assertEqual(num1, (1, True))
        self.assertEqual(num2, (1, False))

    def test__set_user_search_number_dead_unit_num_1(self):
        "[test_search.py] set_user_search_number: dead unit numeric 1"
        selections = {'obs_general.declination1': ['1']}
        extras = {'qtypes': {'obs_general.declination1': ['any']},
                  'units': {'obs_general.declination1': ['degrees']},
                  'order': (['obs_general.time1'], [False])}
        num1 = set_user_search_number(selections, extras)
        extras = {'qtypes': {'obs_general.declination1': ['any']},
                  'units': {'obs_general.declination1': ['degrees'],
                            'obs_general.right_asc1': ['degrees']}, # goes away
                  'order': (['obs_general.time1'], [False])}
        num2 = set_user_search_number(selections, extras)
        self.assertEqual(num1, (1, True))
        self.assertEqual(num2, (1, False))

    def test__set_user_search_number_dead_unit_num_2(self):
        "[test_search.py] set_user_search_number: dead unit numeric 2"
        selections = {'obs_general.declination2': ['1']}
        extras = {'qtypes': {'obs_general.declination1': ['any']},
                  'units': {'obs_general.declination1': ['degrees']},
                  'order': (['obs_general.time1'], [False])}
        num1 = set_user_search_number(selections, extras)
        extras = {'qtypes': {'obs_general.declination1': ['any']},
                  'units': {'obs_general.declination1': ['degrees'],
                            'obs_general.right_asc1': ['degrees']}, # goes away
                  'order': (['obs_general.time1'], [False])}
        num2 = set_user_search_number(selections, extras)
        self.assertEqual(num1, (1, True))
        self.assertEqual(num2, (1, False))

    def test__set_user_search_number_qtype_num_1(self):
        "[test_search.py] set_user_search_number: qtype numeric 1"
        # No qtype vs. used qtype means different search
        selections = {'obs_general.declination1': ['1']}
        extras = {'qtypes': {},
                  'units': {'obs_general.declination1': ['degrees']},
                  'order': (['obs_general.time1'], [False])}
        num1 = set_user_search_number(selections, extras)
        extras = {'qtypes': {'obs_general.declination1': ['any']},
                  'units': {'obs_general.declination1': ['degrees']},
                  'order': (['obs_general.time1'], [False])}
        num2 = set_user_search_number(selections, extras)
        self.assertEqual(num1, (1, True))
        self.assertEqual(num2, (2, True))

    def test__set_user_search_number_qtype_num_2(self):
        "[test_search.py] set_user_search_number: qtype numeric 2"
        # No qtype vs. used qtype means different search
        selections = {'obs_general.declination2': ['1']}
        extras = {'qtypes': {},
                  'units': {'obs_general.declination1': ['degrees']},
                  'order': (['obs_general.time1'], [False])}
        num1 = set_user_search_number(selections, extras)
        extras = {'qtypes': {'obs_general.declination1': ['any']},
                  'units': {'obs_general.declination1': ['degrees']},
                  'order': (['obs_general.time1'], [False])}
        num2 = set_user_search_number(selections, extras)
        self.assertEqual(num1, (1, True))
        self.assertEqual(num2, (2, True))

    def test__set_user_search_number_unit_num_1(self):
        "[test_search.py] set_user_search_number: unit numeric 1"
        # No units vs. used units means different search
        selections = {'obs_general.declination1': ['1']}
        extras = {'qtypes': {'obs_general.declination1': ['any']},
                  'units': {},
                  'order': (['obs_general.time1'], [False])}
        num1 = set_user_search_number(selections, extras)
        extras = {'qtypes': {'obs_general.declination1': ['any']},
                  'units': {'obs_general.declination1': ['degrees']},
                  'order': (['obs_general.time1'], [False])}
        num2 = set_user_search_number(selections, extras)
        self.assertEqual(num1, (1, True))
        self.assertEqual(num2, (2, True))

    def test__set_user_search_number_unit_num_2(self):
        "[test_search.py] set_user_search_number: unit numeric 2"
        # No units vs. used units means different search
        selections = {'obs_general.declination2': ['1']}
        extras = {'qtypes': {'obs_general.declination1': ['any']},
                  'units': {},
                  'order': (['obs_general.time1'], [False])}
        num1 = set_user_search_number(selections, extras)
        extras = {'qtypes': {'obs_general.declination1': ['any']},
                  'units': {'obs_general.declination1': ['degrees']},
                  'order': (['obs_general.time1'], [False])}
        num2 = set_user_search_number(selections, extras)
        self.assertEqual(num1, (1, True))
        self.assertEqual(num2, (2, True))


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
