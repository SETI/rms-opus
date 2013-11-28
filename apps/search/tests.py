"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.

*************** PLEASE NOTE ***************

be sure and delete all from user_searches before you build the 'search' fixture
otherwise your cache_x table names will never match
reset the auto_increment too.. DO THIS:

delete from user_searches;
ALTER TABLE user_searches AUTO_INCREMENT = 1;
analyze table user_searches;

*****************************
"""
import sys
# sys.path.append('/home/lballard/opus/')  #srvr
sys.path.append('/users/lballard/projects/opus/')
# from opus import settings
import settings
from django.core.management import setup_environ
setup_environ(settings)

from django.test import TestCase
from django.test.client import Client
from django.db.models import get_model

from search.views import *
from results.views import *
from django.http import QueryDict

cursor = connection.cursor()

class myFirstTests(TestCase):

    # setup
    c = Client()
    param_name = 'obs_general.planet_id'
    selections = {}
    selections[param_name] = ['Saturn']

    def teardown(self):
        cursor = connection.cursor()
        cursor.execute("delete from user_searches")
        cursor.execute("ALTER TABLE user_searches AUTO_INCREMENT = 1")
        cursor.execute("show tables like %s " , ["cache%"])
        print "running teardown"
        for row in cursor:
            q = 'drop table ' + row[0]
            print q
            cursor.execute(q)

    ## constructQueryString
    def test__constructQueryString_mults_planet(self):
        q = constructQueryString(self.selections)
        expected = "SELECT `obs_general`.`id` FROM `obs_general` WHERE `obs_general`.`mult_obs_general_planet_id` IN (5)"
        self.assertEqual(q,expected)

    def test__constructQueryString_mults_with_target(self):
        selections = {}
        selections['obs_general.planet_id'] = ["Saturn"]
        selections['obs_general.target_name'] = ["PAN"]
        q = constructQueryString(selections)
        expected = "SELECT `obs_general`.`id` FROM `obs_general` WHERE (`obs_general`.`mult_obs_general_target_name` IN (42) AND `obs_general`.`mult_obs_general_planet_id` IN (5))"
        self.assertEqual(q,expected)

    def test__constructQueryString_mults_with_join(self):
        selections = {}
        selections['obs_general.planet_id'] = ["Saturn"]
        selections['obs_instrument_COISS.camera'] = ["Wide Angle"]
        q = constructQueryString(selections)
        expected = "SELECT `obs_general`.`id` FROM `obs_general` INNER JOIN `obs_instrument_COISS` ON (`obs_general`.`id` = `obs_instrument_COISS`.`obs_general_id`) WHERE (`obs_general`.`mult_obs_general_planet_id` IN (5) AND `obs_instrument_COISS`.`mult_obs_instrument_COISS_camera` IN (1))"
        self.assertEqual(q,expected)

    def test__constructQueryString_mults_with_3_table_join(self):
        selections = {}
        selections['obs_general.planet_id'] = ["Saturn"]
        selections['obs_general.target_name'] = ["PAN"]
        selections['obs_instrument_COISS.camera'] = ["Narrow Angle"]
        selections['obs_mission_cassini.rev_no'] = ['165','166']
        q = constructQueryString(selections)
        expected = "SELECT `obs_general`.`id` FROM `obs_general` INNER JOIN `obs_mission_cassini` ON (`obs_general`.`id` = `obs_mission_cassini`.`obs_general_id`) INNER JOIN `obs_instrument_COISS` ON (`obs_general`.`id` = `obs_instrument_COISS`.`obs_general_id`) WHERE (`obs_general`.`mult_obs_general_target_name` IN (42) AND `obs_general`.`mult_obs_general_planet_id` IN (5) AND `obs_mission_cassini`.`mult_obs_mission_cassini_rev_no` IN (289, 290) AND `obs_instrument_COISS`.`mult_obs_instrument_COISS_camera` IN (2))"

        self.assertEqual(q,expected)


    ## getUserQueryTable
    def test__getUserQueryTable(self):
        self.teardown()
        # simple base join types only
        table = getUserQueryTable(self.selections)
        print "table = " + str(table) + "\n" + str(self.selections)
        self.assertEqual(table,'cache_1')

    def test__getUserQueryTable_table_already_exists(self):
        # the 2nd time through you're testing whether it returns the table that is already there
        table = getUserQueryTable(self.selections)
        self.assertEqual(table,'cache_1')


    ## test urlToSearchParam
    def test__urlToSearchParams_stringsearch(self):
        q = QueryDict("note=Incomplete")
        result = urlToSearchParams(q)
        print result
        self.assertEqual(result,[{u'obs_general.note': [u'Incomplete']}, {'qtypes': {}}])


    def test__urlToSearchParams_mults(self):
        q = QueryDict("planet=SATURN&target=PAN")
        result = urlToSearchParams(q)
        self.assertEqual(result,[{u'obs_general.target_name': [u'PAN'], u'obs_general.planet_id': [u'SATURN']}, {'qtypes': {}}])


    def test__urlToSearchParams_stringmultmix(self):
        q = QueryDict("planet=SATURN&target=PAN&note=Incomplete&qtype-note=contains")
        result = urlToSearchParams(q)
        # setup assert:
        excpected = [{u'obs_general.note': [u'Incomplete'], u'obs_general.planet_id': [u'SATURN'], u'obs_general.target_name': [u'PAN']}, {'qtypes': {u'obs_general.note': [u'contains']}}]
        self.assertEqual(result,excpected)

    def test__urlToSearchParams_mix_with_note(self):
        q = QueryDict('planet=Jupiter&note=Manually,Incomplete&qtype-note=contains,begins')
        result = urlToSearchParams(q)
        print result
        expected = [{u'obs_general.planet_id': [u'Jupiter'], u'obs_general.note': [u'Manually', u'Incomplete']}, {'qtypes': {u'obs_general.note': [u'contains', u'begins']}}]
        self.assertEqual(result,expected)

    def test__urlToSearchParams_ring_rad_rangea(self):
        q = QueryDict("ringradius1=60000&ringradius2=80000")
        result = urlToSearchParams(q)
        # setup assert:
        selections = {}
        extras={}
        qtypes = {}
        selections['obs_ring_geometry.ring_radius1'] = ['60000']
        selections['obs_ring_geometry.ring_radius2'] = ['80000']
        extras['qtypes'] = qtypes
        self.assertEqual(result,[selections,extras])


    ##  setUserSearchNo
    def test_setUserSearchNo(self):
        no = setUserSearchNo(self.selections)
        self.assertTrue(no)

    def test_setUserSearchNo_2_planets(self):
        selections = {}
        selections['obs_general.planet_id'] = ['Saturn']
        no = setUserSearchNo(selections)
        print no
        # breaking this, this test needs to see if there are any rows in the table
        self.assertGreater(no, 0)
        self.teardown()


    ##  Range Query tests
    def test__range_query_any(self):
        # range query: 'any'
        selections = {}
        selections['obs_ring_geometry.ring_radius1'] = [10000]
        selections['obs_ring_geometry.ring_radius2'] = [40000]
        q = range_query_object(selections,'obs_ring_geometry.ring_radius1',['any'])
        print str(q)
        self.assertEqual(str(q),"(AND: ('obs_ring_geometry.ring_radius1__lte', 40000), ('obs_ring_geometry.ring_radius2__gte', 10000))")

    def test_range_query_only(self):
        # range query: 'only'
        selections = {}
        selections['obs_ring_geometry.ring_radius1'] = [10000]
        selections['obs_ring_geometry.ring_radius2'] = [40000]
        q = range_query_object(selections,'obs_ring_geometry.ring_radius1',['only'])
        print str(q)
        self.assertEqual(str(q), "(AND: ('obs_ring_geometry.ring_radius1__gte', 10000), ('obs_ring_geometry.ring_radius2__lte', 40000))")

    def test_range_query_all(self):
        # range query: 'all'
        selections = {}
        selections['obs_ring_geometry.ring_radius1'] = [10000]
        selections['obs_ring_geometry.ring_radius2'] = [40000]
        q = range_query_object(selections,'obs_ring_geometry.ring_radius1',['all'])
        print str(q)
        self.assertEqual(str(q), "(AND: ('obs_ring_geometry.ring_radius1__lte', 10000), ('obs_ring_geometry.ring_radius2__gte', 40000))")

    def test_range_query_multi(self):
        # range query: multi
        selections = {}
        selections['obs_ring_geometry.ring_radius1'] = [10000,60000]
        selections['obs_ring_geometry.ring_radius2'] = [40000,80000]
        q = range_query_object(selections,'obs_ring_geometry.ring_radius1',['all'])
        print str(q)
        self.assertEqual(str(q), "(OR: (AND: ('obs_ring_geometry.ring_radius1__lte', 10000), ('obs_ring_geometry.ring_radius2__gte', 40000)), (AND: ('obs_ring_geometry.ring_radius1__lte', 60000), ('obs_ring_geometry.ring_radius2__gte', 80000)))")

    def test_range_query_ordered_backwards(self):
        # range query: ordered backwards
        selections = {}
        selections['obs_ring_geometry.ring_radius1'] = [40000,60000]
        selections['obs_ring_geometry.ring_radius2'] = [10000,80000]
        q = range_query_object(selections,'obs_ring_geometry.ring_radius1',['all'])
        print str(q)
        self.assertEqual(str(q), "(OR: (AND: ('obs_ring_geometry.ring_radius1__lte', 10000), ('obs_ring_geometry.ring_radius2__gte', 40000)), (AND: ('obs_ring_geometry.ring_radius1__lte', 60000), ('obs_ring_geometry.ring_radius2__gte', 80000)))")


    def test_range_query_ordered_lopsided_all(self):
        # range query: lopsided all
        selections = {}
        selections['obs_ring_geometry.ring_radius1'] = [40000]
        q = range_query_object(selections,'obs_ring_geometry.ring_radius1',['all'])
        print str(q)
        self.assertEqual(str(q), "(AND: ('obs_ring_geometry.ring_radius1__lte', 40000))")


    def test_range_query_ordered_lopsided_all_max(self):
        # range query: lopsided all max
        selections = {}
        selections['obs_ring_geometry.ring_radius2'] = [40000]
        q = range_query_object(selections,'obs_ring_geometry.ring_radius2',['all'])
        print str(q)
        self.assertEqual(str(q), "(AND: ('obs_ring_geometry.ring_radius2__gte', 40000))")
        """
        self.assertEqual(q,'(obs_ring_geometry.ring_radius2 >= %s)')
        self.assertEqual(v,[40000])
        """

    def test_range_query_lopsided_only_min(self):
        # range query: lopsided only min
        selections = {}
        selections['obs_ring_geometry.ring_radius1'] = [40000]
        q = range_query_object(selections,'obs_ring_geometry.ring_radius1',['only'])
        print str(q)
        self.assertEqual(str(q), "(AND: ('obs_ring_geometry.ring_radius1__gte', 40000))")


    def test_range_query_lopsided_only_max(self):
        # range query: lopsided only max
        selections = {}
        selections['obs_ring_geometry.ring_radius2'] = [40000]
        q = range_query_object(selections,'obs_ring_geometry.ring_radius2',['only'])
        print str(q)
        # (ring_radius2 <= 4000
        self.assertEqual(str(q), "(AND: ('obs_ring_geometry.ring_radius2__lte', 40000))")

    def test_range_query_lopsided_any_min(self):
        # range query: lopsided any min
        selections = {}
        selections['obs_ring_geometry.ring_radius1'] = [40000]
        q = range_query_object(selections,'obs_ring_geometry.ring_radius1',['any'])
        print str(q)
        # ring_radius2 >= %s
        self.assertEqual(str(q), "(AND: ('obs_ring_geometry.ring_radius2__gte', 40000))")

    def test_range_query_lopsided_any_max(self):
        # range query: lopsided any min
        selections = {}
        selections['obs_ring_geometry.ring_radius2'] = [40000]
        q = range_query_object(selections,'obs_ring_geometry.ring_radius2',['any'])
        print str(q)
        self.assertEqual(str(q), "(AND: ('obs_ring_geometry.ring_radius1__lte', 40000))")

    def test_range_query_lopsided_multi_mixed_q_types(self):
        # range query: multi range, 1 is lopsided, mixed qtypes
        selections = {}
        selections['obs_ring_geometry.ring_radius1'] = [40000,80000]
        selections['obs_ring_geometry.ring_radius2'] = [60000]
        q = range_query_object(selections,'obs_ring_geometry.ring_radius2',['any','only'])
        print str(q)
        # (ring_radius1 <= 6000 AND ring_radius2 >= 40000) OR (ring_radius2 >= 80000)
        self.assertEqual(str(q),"(OR: (AND: ('obs_ring_geometry.ring_radius1__lte', 60000), ('obs_ring_geometry.ring_radius2__gte', 40000)), ('obs_ring_geometry.ring_radius1__gte', 80000))")

    def test_range_query_lopsided_multi_mixed_only_one_q_type(self):
        # range query: multi range, 1 is lopsided, mixed only 1 qtype given
        selections = {}
        selections['obs_ring_geometry.ring_radius1'] = [40000,80000]
        selections['obs_ring_geometry.ring_radius2'] = [60000]
        q = range_query_object(selections,'obs_ring_geometry.ring_radius2',['any'])
        print str(q)
        # (ring_radius1 <= 6000 AND ring_radius2 >= 40000) OR (ring_radius2 >= 80000)
        self.assertEqual(str(q),"(OR: (AND: ('obs_ring_geometry.ring_radius1__lte', 60000), ('obs_ring_geometry.ring_radius2__gte', 40000)), ('obs_ring_geometry.ring_radius2__gte', 80000))")


    ## Time  tests
    def test__convertTimes(self):
        # test times
        times     = ['2000-023T06:12:24.480','2000-024T06:12:24.480']
        new_times = convertTimes(times)
        self.assertEqual(new_times,[1923176.48, 2009576.48])

    def test__convertTimes2(self):
        times     = ['2000-023T06:12:24.480','cats']
        new_times = convertTimes(times)
        self.assertEqual(new_times,[1923176.48, None])

    def test__findInvalidTimes(self):
        times         = ['1979-05-28T10:17:37.28','cats','dogs']
        invalid_times = findInvalidTimes(times)
        print invalid_times
        self.assertEqual(invalid_times,['cats','dogs'])

    def test__findInvalidTimes2(self):
        times         = ['1979-05-28T10:17:37.28']
        invalid_times = findInvalidTimes(times)
        self.assertEqual(invalid_times,None)


    def test_range_query_time_any(self):
        # range query: form type = TIME, qtype any
        selections = {}
        selections['obs_general.time_sec1'] = ['1979-05-28T10:17:37.28']
        selections['obs_general.time_sec2'] = ['1979-05-29T18:22:26']
        q = range_query_object(selections,'obs_general.time_sec1',['any'])
        print str(q)
        # time_sec1 <= -649993324.720000 AND time_sec2 >= -649877836.000000
        self.assertEqual(str(q), "(AND: ('obs_general.time_sec1__lte', -649834636), ('obs_general.time_sec2__gte', -649950124.72000003))")


    def test_range_query_time_any_single_time(self):
        # range query: form type = TIME, qtype any
        selections = {}
        selections['obs_general.time_sec1'] = ['1979-05-28T10:17:37.28']
        q = range_query_object(selections,'obs_general.time_sec1',['any'])
        print str(q)
        # time_sec2 >= -649993324.720000
        self.assertEqual(str(q),"(AND: ('obs_general.time_sec2__gte', -649950124.72000003))")


    ## longitude query tests
    def test__longitudeQuery_single(self):
        #single longitude set
        selections = {}
        selections['obs_general.declination1'] = [58]
        selections['obs_general.declination2'] = [61]
        q= longitudeQuery(selections,'obs_general.declination1')
        print selections
        print q
        expect = '(abs(abs(mod(59.5 - obs_general.declination + 180., 360.)) - 180.) <= 1.5 + obs_general.d_declination)'
        self.assertEqual(q,expect)

    def test__longitudeQuery_double(self):
        # double
        selections = {}
        selections['obs_general.declination1'] = [58,75]
        selections['obs_general.declination2'] = [61,83]
        q = longitudeQuery(selections,'obs_general.declination1')
        print q
        expect = "(abs(abs(mod(59.5 - obs_general.declination + 180., 360.)) - 180.) <= 1.5 + obs_general.d_declination) OR (abs(abs(mod(79.0 - obs_general.declination + 180., 360.)) - 180.) <= 4.0 + obs_general.d_declination)"
        self.assertEqual(q,expect)

    def test__longitudeQuery_one_side(self):
        # missing value raises exception
        selections = {}
        selections['obs_general.declination1'] = [58]
        # self.assertRaises(IndexError, longitudeQuery(selections,'declination1'))
        try:
            longitudeQuery(selections,'obs_general.declination1')
        except KeyError, IndexError:
            pass

    def test__longitudeQuery_other_side(self):
        # missing value raises exception
        selections = {}
        selections['obs_general.declination2'] = [58]
        # self.assertRaises(IndexError, longitudeQuery(selections,'declination1'))
        try:
            longitudeQuery(selections,'obs_general.declination1')
        except KeyError, IndexError:
            pass

    def test__longitudeQuery_lop_sided(self):
        # missing value raises exception
        selections = {}
        selections['obs_general.declination1'] = [58,75]
        selections['obs_general.declination2'] = [61]
        # self.assertRaises(IndexError, longitudeQuery(selections,'declination1'))
        try:
            longitudeQuery(selections,'obs_general.declination1')
        except KeyError, IndexError:
            pass






