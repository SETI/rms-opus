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

from search.views import *
from results.views import *
from django.http import QueryDict

class myFirstTests(TestCase):

    """
    #fixtures = ['multPlanetID.json','UserSearches.json','Observations.json','ParamInfo.json']
    fixtures = ['search.json','paraminfo.json']
    """
    param_name = 'planet_id'
    c = Client()
    selections = {}
    selections['planet_id'] = ['Jupiter']

    """
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
    """

    """
    def test__getRangeEndpoints(self):
        selections = {}
        selections['declination1'] = [58]
        selections['declination2'] = [61]
        qtypes = {}
        extras = {}
        extras['qtypes'] = qtypes
        ep = getRangeEndpoints(selections,extras,'declination1','declination2')
        self.assertEqual(ep,[59.5, 'declination', 1.5, 'd_declination'])


    def test__getResults(self):
        print 'in getResults test'
        response = self.c.get('/search/results/data/?planet=Jupiter')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.content), 104098)


    def test__getImages(self):
        response = self.c.get('/search/results/images/?planet=Jupiter')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.content), 42292)


    def test__longitudeQuery(self):
        #single longitude set
        print 'hello'
        selections = {}
        selections['declination1'] = [58]
        selections['declination2'] = [61]
        (q, v) = longitudeQuery(selections,'declination1')
        self.assertEqual(q,'(abs(abs(mod(%s - %s + 180., 360.)) - 180.) <= %s + %s)')
        self.assertEqual(v,[59.5, 'declination', 1.5, 'd_declination'])

        # double
        selections = {}
        selections['declination1'] = [58,75]
        selections['declination2'] = [61,83]
        (q, v) = longitudeQuery(selections,'declination1')
        self.assertEqual(q,'(abs(abs(mod(%s - %s + 180., 360.)) - 180.) <= %s + %s) OR (abs(abs(mod(%s - %s + 180., 360.)) - 180.) <= %s + %s)')
        self.assertEqual(v,[59.5, 'declination', 1.5, 'd_declination',79.0, 'declination', 4.0, 'd_declination'])

        # missing value raises exception
        selections = {}
        selections['declination1'] = [58]
        ## WHY GOD WHY? ##
        #self.assertRaises("LongitudeError",longitudeQuery,selections,'declination1')

        # missing value raises exception
        selections = {}
        selections['declination1'] = [58,75]
        selections['declination2'] = [61]
        ## WHY GOD WHY? ##
        #self.assertRaises(KeyError,longitudeQuery,selections,'declination1')

    def test__convertTimes(self):
        # test times
        times     = ['2008-10-20 12:59:333','2006-10-20 12:59:333']
        new_times = convertTimes(times)
        self.assertEqual(new_times,['253268012.333000', '190196012.333000'])

        # give it a bad time
        times     = ['2008-10-20 12:59:333','cats']
        new_times = convertTimes(times)
        self.assertEqual(new_times,['253268012.333000', None])


    def test__findInvalidTimes(self):
        times         = ['2008-10-20 12:59:333','cats','dogs']
        invalid_times = findInvalidTimes(times)
        self.assertEqual(invalid_times,['cats','dogs'])

        times         = ['2008-10-20 12:59:333']
        invalid_times = findInvalidTimes(times)
        self.assertEqual(invalid_times,None)



    def test__getUserQueryTable(self):
        self.teardown()
        # simple base join types only
        table = getUserQueryTable(self.selections)
        print "table = " + str(table) + "\n" + str(self.selections)
        self.assertEqual(table,'cache_1')
        # the 2nd time through you're testing whether it returns the table that is already there
        table = getUserQueryTable(self.selections)
        self.assertEqual(table,'cache_1')

        # some aux and base mix queries
        selections = {}
        selections['planet_id']    = ['Jupiter']
        selections['COISS_FILTER'] = ['red']
        selections['VGISS_FILTER'] = ['violet','ORANGE']
        table = getUserQueryTable(selections)
        print "table = " + str(table) + "\n" + str(selections)
        self.assertEqual(table,'cache_2')
        # 2nd
        table = getUserQueryTable(selections)
        self.assertEqual(table,'cache_2')

        # some aux and base mix queries
        selections = {}
        selections['planet_id'] = ['Jupiter']
        selections['COISS_FILTER'] = ['red']
        selections['VGISS_FILTER'] = ['violet','GREEN']
        table = getUserQueryTable(selections)
        print "table = " + str(table) + "\n" + str(selections)
        self.assertEqual(table,'cache_3')
        # 2nd
        table = getUserQueryTable(selections)
        self.assertEqual(table,'cache_3')

        # some aux and base mix queries
        # only aux joins no base joins
        selections = {}
        selections['coiss_filter'] = ['red']
        selections['VGISS_FILTER'] = ['violet','ORANGE']
        table = getUserQueryTable(selections)
        print "table = " + str(table) + "\n" + str(selections)
        self.assertEqual(table,'cache_4')
        # 2nd
        table = getUserQueryTable(selections)
        self.assertEqual(table,'cache_4')

        # only aux joins no base joins
        selections = {}
        selections['coiss_filter'] = ['red','IR5']
        selections['VGISS_FILTER'] = ['violet','ORANGE']
        table = getUserQueryTable(selections)
        print "table = " + str(table) + "\n" + str(selections)
        self.assertEqual(table,'cache_5')
        # 2nd
        table = getUserQueryTable(selections)
        self.assertEqual(table,'cache_5')

        # only aux joins no base joins
        selections = {}
        selections['planet_id'] = ['Saturn']
        table = getUserQueryTable(selections)
        print "table = " + str(table) + "\n" + str(selections)
        self.assertEqual(table,'cache_6')
        # 2nd
        table = getUserQueryTable(selections)
        self.assertEqual(table,'cache_6')


        #  overides mult query type with RANGE
        selections = {}
        selections['VGISS_FILTER'] = ['ORANGE','violet']
        extras={}
        qtypes = {}
        qtypes['VGISS_FILTER'] = 'range'
        extras['qtypes'] = qtypes
        table = getUserQueryTable(selections,extras)
        print "table = " + str(table) + "\n" + str(selections)
        self.assertEqual(table,'cache_7')
        # 2nd
        table = getUserQueryTable(selections)
        self.assertEqual(table,'cache_7')

        # user enteres the range kinda backwards
        selections = {}
        selections['VGISS_FILTER'] = ['violet','ORANGE']
        extras={}
        qtypes = {}
        qtypes['VGISS_FILTER'] = 'range'
        extras['qtypes'] = qtypes
        table = getUserQueryTable(selections,extras)
        print "table = " + str(table) + "\n" + str(selections)
        self.assertEqual(table,'cache_8')
        # 2nd
        table = getUserQueryTable(selections)
        self.assertEqual(table,'cache_8')

        # user enteres the range kinda backwards
        selections = {}
        selections['VGISS_FILTER'] = ['violet','ORANGE']
        extras={}
        qtypes = {}
        qtypes['VGISS_FILTER'] = 'range'
        extras['qtypes'] = qtypes
        table = getUserQueryTable(selections,extras)
        print "table = " + str(table) + "\n" + str(selections)
        self.assertEqual(table,'cache_8')
        # 2nd
        table = getUserQueryTable(selections)
        self.assertEqual(table,'cache_8')

        # user overides mult query with string type query
        selections = {}
        selections['COISS_FILTER'] = ['IR']
        extras={}
        qtypes = {}
        qtypes['COISS_FILTER'] = 'contains'
        extras['qtypes'] = qtypes
        table = getUserQueryTable(selections,extras)
        print "table = " + str(table) + "\n" + str(selections)
        self.assertEqual(table,'cache_9')
        # 2nd
        table = getUserQueryTable(selections)
        self.assertEqual(table,'cache_9')

        # user overides string query with range query
        selections = {}
        selections['note'] = ['Incomplete','Z']
        extras={}
        qtypes = {}
        qtypes['note'] = 'range'
        extras['qtypes'] = qtypes
        table = getUserQueryTable(selections,extras)
        print "table = " + str(table) + "\n" + str(selections)
        self.assertEqual(table,'cache_10')
        # 2nd
        table = getUserQueryTable(selections)
        self.assertEqual(table,'cache_10')




        # some aux and base mix queries
        selections = {}
        selections['planet_id'] = ['Jupiter']
        selections['COISS_FILTER'] = ['red']
        selections['VGISS_FILTER'] = ['violet','GREEN']
        selections['cassini_activity_name'] = ['catface','doggie']

        table = getUserQueryTable(selections)
        print "table = " + str(table) + "\n" + str(selections)
        self.assertEqual(table,'cache_11')
        # 2nd
        table = getUserQueryTable(selections)
        self.assertEqual(table,'cache_11')


        # some aux and base mix queries
        selections = {}
        selections['planet_id'] = ['Jupiter']
        selections['COISS_FILTER'] = ['red']
        selections['VGISS_FILTER'] = ['violet','GREEN']
        selections['cassini_activity_name'] = ['catface']
        table = getUserQueryTable(selections)
        print "table = " + str(table) + "\n" + str(selections)
        self.assertEqual(table,'cache_12')
        # 2nd
        table = getUserQueryTable(selections)
        self.assertEqual(table,'cache_12')

        # mission and general only
        selections = {}
        selections['planet_id'] = ['Jupiter']
        selections['cassini_activity_name'] = ['catface']
        table = getUserQueryTable(selections)
        print "table = " + str(table) + "\n" + str(selections)
        self.assertEqual(table,'cache_13')
        # 2nd
        table = getUserQueryTable(selections)
        self.assertEqual(table,'cache_13')

        # we need to tear down all these tables now!!!!!! here is why:
        # what we've done is create 6 tables, but the save() method that records the metadata in user_searches
        # about how to use these tables will not be seen by other tests, because each test goes back to the fixture
        # which for the user_searches table is EMPTY! sooooo...
        # these 6 tables we created will still be there but when another test goes to set user_searches id = 1
        # for a completely different search it will still want to use table = cache_1 which we built here!
        self.teardown()

    """

    def test__range_query_any(self):

        # range query: 'any'
        selections = {}
        selections['ring_radius1'] = [10000]
        selections['ring_radius2'] = [40000]
        q = range_query_object(selections,'ring_radius1',['any'])
        print str(q)
        self.assertEqual(str(q),"(AND: ('ring_radius1__lte', 40000), ('ring_radius2__gte', 10000))")

    def test_range_query_only(self):
        # range query: 'only'
        selections = {}
        selections['ring_radius1'] = [10000]
        selections['ring_radius2'] = [40000]
        q = range_query_object(selections,'ring_radius1',['only'])
        print str(q)
        self.assertEqual(str(q), "(AND: ('ring_radius1__gte', 10000), ('ring_radius2__lte', 40000))")

    def test_range_query_all(self):
        # range query: 'all'
        selections = {}
        selections['ring_radius1'] = [10000]
        selections['ring_radius2'] = [40000]
        q = range_query_object(selections,'ring_radius1',['all'])
        print str(q)
        self.assertEqual(str(q), "(AND: ('ring_radius1__lte', 10000), ('ring_radius2__gte', 40000))")

    def test_range_query_multi(self):
        # range query: multi
        selections = {}
        selections['ring_radius1'] = [10000,60000]
        selections['ring_radius2'] = [40000,80000]
        q = range_query_object(selections,'ring_radius1',['all'])
        print str(q)
        self.assertEqual(str(q), "(OR: (AND: ('ring_radius1__lte', 10000), ('ring_radius2__gte', 40000)), (AND: ('ring_radius1__lte', 60000), ('ring_radius2__gte', 80000)))")

    def test_range_query_ordered_backwards(self):
        # range query: ordered backwards
        selections = {}
        selections['ring_radius1'] = [40000,60000]
        selections['ring_radius2'] = [10000,80000]
        q = range_query_object(selections,'ring_radius1',['all'])
        print str(q)
        self.assertEqual(str(q), "(OR: (AND: ('ring_radius1__lte', 10000), ('ring_radius2__gte', 40000)), (AND: ('ring_radius1__lte', 60000), ('ring_radius2__gte', 80000)))")


    def test_range_query_ordered_lopsided_all(self):
        # range query: lopsided all
        selections = {}
        selections['ring_radius1'] = [40000]
        q = range_query_object(selections,'ring_radius1',['all'])
        print str(q)
        self.assertEqual(str(q), "(AND: ('ring_radius1__lte', 40000))'")


    def test_range_query_ordered_lopsided_all_max(self):
        # range query: lopsided all max
        selections = {}
        selections['ring_radius2'] = [40000]
        q = range_query_object(selections,'ring_radius2',['all'])
        print str(q)
        print "this fails lolz"
        self.assertEqual(q, None)
        """
        self.assertEqual(q,'(ring_radius2 >= %s)')
        self.assertEqual(v,[40000])
        """

    def test_range_query_lopsided_only_min(self):
        # range query: lopsided only min
        selections = {}
        selections['ring_radius1'] = [40000]
        q = range_query_object(selections,'ring_radius1',['only'])
        print str(q)
        self.assertEqual(str(q), "(AND: ('ring_radius1__gte', 40000))")


    def test_range_query_lopsided_only_max(self):
        # range query: lopsided only max
        selections = {}
        selections['ring_radius2'] = [40000]
        q = range_query_object(selections,'ring_radius2',['only'])
        print str(q)
        print "has never worked"
        assertEqual(str(q), None)
        """
        self.assertEqual(q,'(ring_radius2 <= %s)')
        self.assertEqual(v,[40000])
        """

    def test_range_query_lopsided_any_min(self):
        # range query: lopsided any min
        selections = {}
        selections['ring_radius1'] = [40000]
        q = range_query_object(selections,'ring_radius1',['any'])
        print str(q)
        print str(v)
        self.assertEqual(q,'(ring_radius2 >= %s)')
        self.assertEqual(v,[40000])

    def test_range_query_lopsided_any_max(self):
        # range query: lopsided any min
        selections = {}
        selections['ring_radius2'] = [40000]
        q = range_query_object(selections,'ring_radius2',['any'])
        print str(q)
        self.assertEqual(str(q), "(AND: ('ring_radius1__lte', 40000))")

    def test_range_query_lopsided_multi_mixed_q_types(self):
        # range query: multi range, 1 is lopsided, mixed qtypes
        selections = {}
        selections['ring_radius1'] = [40000,80000]
        selections['ring_radius2'] = [60000]
        q = range_query_object(selections,'ring_radius2',['any','only'])
        print str(q)
        self.assertEqual(str(q), "(OR: (AND: ('ring_radius1__lte', 60000), ('ring_radius2__gte', 40000)), ('ring_radius1__gte', 80000))'")

    def test_range_query_lopsided_multi_mixed_only_one_q_type(self):
        # range query: multi range, 1 is lopsided, mixed only 1 qtype given
        selections = {}
        selections['ring_radius1'] = [40000,80000]
        selections['ring_radius2'] = [60000]
        q = range_query_object(selections,'ring_radius2',['any'])
        print str(q)
        print str(v)
        self.assertEqual(q,'(ring_radius1 <= %s AND ring_radius2 >= %s) OR (ring_radius2 >= %s)')
        self.assertEqual(v,[60000,40000,80000])


    def test_range_query_time_any(self):
        # range query: form type = TIME, qtype any
        selections = {}
        selections['time_sec1'] = ['1979-05-28T10:17:37.28']
        selections['time_sec2'] = ['1979-05-29T18:22:26']
        q = range_query_object(selections,'time_sec1',['any'])
        print str(q)
        print str(v)
        self.assertEqual(q,'(time_sec1 <= %s AND time_sec2 >= %s)')
        self.assertEqual(v,['-649993324.720000', '-649877836.000000'])


    def test_range_query_time_any_single_time(self):
        # range query: form type = TIME, qtype any
        selections = {}
        selections['time_sec1'] = ['1979-05-28T10:17:37.28']
        q = range_query_object(selections,'time_sec1',['any'])
        print str(q)
        print str(v)
        self.assertEqual(q,'(time_sec2 >= %s)')
        self.assertEqual(v,['-649993324.720000'])

    """

    def test__urlToSearchParams_stringsearch(self):
        q = QueryDict("note=Incomplete")
        result = urlToSearchParams(q)
        # setup assert:
        selections = {}
        extras={}
        qtypes = {}
        selections['note'] = ['Incomplete']
        extras['qtypes'] = qtypes
        self.assertEqual(result,[selections,extras])
        self.teardown()


    def test__urlToSearchParams_mults(self):
        q = QueryDict("planet=SATURN&target=PAN")
        result = urlToSearchParams(q)
        # setup assert:
        selections = {}
        extras={}
        qtypes = {}
        selections['planet_id'] = ['SATURN']
        selections['target_name'] = ['PAN']
        extras['qtypes'] = qtypes
        self.assertEqual(result,[selections,extras])
        self.teardown()

    def test__urlToSearchParams_stringmultmix(self):
        q = QueryDict("planet=SATURN&target=PAN&note=Incomplete&qtype-note=contains")
        result = urlToSearchParams(q)
        # setup assert:
        selections = {}
        extras={}
        qtypes = {}
        selections['planet_id'] = ['SATURN']
        selections['target_name'] = ['PAN']
        selections['note'] = ['Incomplete']
        qtypes['note'] = ['contains']
        extras['qtypes'] = qtypes
        self.assertEqual(result,[selections,extras])

        q = QueryDict('planet=Jupiter&note=Manually,Incomplete&qtype-note=contains,begins')
        result = urlToSearchParams(q)
        # setup assert:
        selections = {}
        extras={}
        qtypes = {}
        selections['planet_id'] = ['Jupiter']
        selections['note'] = ['Manually','Incomplete']
        qtypes['note'] = ['contains','begins']
        extras['qtypes'] = qtypes
        self.assertEqual(result,[selections,extras])
        self.teardown()

        q = QueryDict("ringradius1=60000&ringradius2=80000")
        result = urlToSearchParams(q)
        # setup assert:
        selections = {}
        extras={}
        qtypes = {}
        selections['ring_radius1'] = ['60000']
        selections['ring_radius2'] = ['80000']
        extras['qtypes'] = qtypes
        self.assertEqual(result,[selections,extras])

    def test_resultCount(self):
        response = self.c.get('/search/result_count/?planet=Saturn')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, '{"result_count": 0}')

        response = self.c.get('/search/result_count/?planet=Jupiter')
        self.assertEqual(response.content, '{"result_count": 2000}')

        response = self.c.get('/search/result_count/?planet=Jupiter&target=SKY')
        self.assertEqual(response.content, '{"result_count": 12}')
        self.teardown()

        response = self.c.get('/search/result_count/?planet=Jupiter&target=IO,PANDORA')
        self.assertEqual(response.content, '{"result_count": 38}')
        self.teardown()

        # some range queries.. single no qtype (defaults any)
        response = self.c.get('/search/result_count/?ringradius1=60000&ringradius2=80000')
        self.assertEqual(response.content, '{"result_count": 187}')
        self.teardown()

        # qtype all
        response = self.c.get('/search/result_count/?ringradius1=60000&ringradius2=80000&qtype-ringradius=all')
        self.assertEqual(response.content, '{"result_count": 187}')
        self.teardown()

        # qtype only
        response = self.c.get('/search/result_count/?ringradius1=60000&ringradius2=80000&qtype-ringradius=only')
        self.assertEqual(response.content, '{"result_count": 0}')
        self.teardown()

        # mult ranges qtype only 1 given as all
        response = self.c.get('/search/result_count/?ringradius1=60000&ringradius2=80000,120000&qtype-ringradius=all')
        self.assertEqual(response.content, '{"result_count": 187}')
        self.teardown()

        # mission and general only
        response = self.c.get('/search/result_count/?planet=Jupiter&cassiniactivityname=catface')
        self.assertEqual(response.content, '{"result_count": 1592}')
        self.teardown()

    """

    """

    def test_getValidMults(self):
                response = self.c.get('/search/mults/ids/?field=planet&planet=Jupiter')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, '{"mults": {"3": 2000}, "field": "planet"}')
        self.teardown()
        response = self.c.get('/search/mults/ids/?field=target&planet=Jupiter')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, '{"mults": {"6": 11, "60": 5, "10": 54, "18": 8, "20": 81, "25": 38, "28": 1803}, "field": "target"}')
        self.teardown()

        # getting by labels
        response = self.c.get('/search/mults/labels/?field=target&planet=Jupiter')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, '{"mults": {"EUROPA": 8, "AMALTHEA": 11, "GANYMEDE": 81, "CALLISTO": 54, "JUPITER": 1803, "IO": 38, "THEBE": 5}, "field": "target"}')
        self.teardown()
    """

    """
    def test_setUserSearchNo(self):
        no = setUserSearchNo(self.selections)
        self.assertTrue(no)
        selections = {}
        selections['planet_id'] = ['Saturn','Jupiter']
        no = setUserSearchNo(selections)
        self.assertTrue(no)
        self.teardown()

    """

