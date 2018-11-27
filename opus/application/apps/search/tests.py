# search/tests.py

# These tests require the following volumes, imported in this order:
# COISS_2002,COISS_2008,COISS_2111,COUVIS_0002,GO_0017,VGISS_6210,VGISS_8201,HSTI1_2003

from unittest import TestCase

from django.apps import apps
from django.conf import settings
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

    def setUp(self):
        print('Running setup')
        cursor = connection.cursor()
        cursor.execute('DELETE FROM user_searches')
        cursor.execute("ALTER TABLE user_searches AUTO_INCREMENT = 1")
        cursor.execute("SHOW TABLES LIKE %s" , ["cache_%"])
        for row in cursor:
            q = 'DROP TABLE ' + row[0]
            print(q)
            cursor.execute(q)

    def teardown(self):
        assert False
        print('Running teardown')
        cursor = connection.cursor()
        cursor.execute('DELETE FROM user_searches')
        cursor.execute("ALTER TABLE user_searches AUTO_INCREMENT = 1")
        cursor.execute("SHOW TABLES LIKE %s" , ["cache_%"])
        for row in cursor:
            q = 'DROP TABLE ' + row[0]
            print(q)
            cursor.execute(q)


            #############################################
            ######### DATABASE INTEGRITY CHECKS #########
            #############################################

    def test__pds_image_wl_volume_counts_match_obs_general(self):
        """Volumes in obs_general = obs_pds, obs_type_image, obs_wavelength.
           Test that the observation count per volume is the same in
           obs_general, obs_pds, obs_type_image, and obs_wavelength, since
           these tables should all include the exact same set of observations.
        """
        obs = (ObsGeneral.objects.values_list('volume_id')
               .annotate(Count('volume_id'))
               .order_by('volume_id'))
        pds = (ObsPds.objects.values_list('volume_id')
               .annotate(Count('volume_id'))
               .order_by('volume_id'))
        self.assertEqual(list(obs), list(pds))
        img = (ObsTypeImage.objects.values_list('volume_id')
               .annotate(Count('volume_id'))
               .order_by('volume_id'))
        self.assertEqual(list(obs), list(img))
        wl = (ObsWavelength.objects.values_list('volume_id')
               .annotate(Count('volume_id'))
               .order_by('volume_id'))
        self.assertEqual(list(obs), list(wl))

    def test__cassini_counts_match_obs_general(self):
        """Volumes in obs_general = obs_mission_cassini.
           Test that the observation count per volume is the same in
           obs_general for mission_id='CO' and obs_mission_cassini.
        """
        obs = (ObsGeneral.objects.values_list('volume_id')
               .filter(mission_id='CO')
               .annotate(Count('volume_id'))
               .order_by('volume_id'))
        ref = (ObsMissionCassini.objects.values_list('volume_id')
               .annotate(Count('volume_id'))
               .order_by('volume_id'))
        try:
            self.assertEqual(list(obs), list(ref))
        except Exception as e:
            if e.args[0] != MYSQL_TABLE_NOT_EXISTS:
                raise

    def test__galileo_counts_match_obs_general(self):
        """Volumes in obs_general = obs_mission_galileo.
           Test that the observation count per volume is the same in
           obs_general for mission_id='GO' and obs_mission_galileo.
        """
        obs = (ObsGeneral.objects.values_list('volume_id')
               .filter(mission_id='GO')
               .annotate(Count('volume_id'))
               .order_by('volume_id'))
        ref = (ObsMissionGalileo.objects.values_list('volume_id')
               .annotate(Count('volume_id'))
               .order_by('volume_id'))
        try:
            self.assertEqual(list(obs), list(ref))
        except Exception as e:
            if e.args[0] != MYSQL_TABLE_NOT_EXISTS:
                raise

    def test__hubble_counts_match_obs_general(self):
        """Volumes in obs_general = obs_mission_hubble.
           Test that the observation count per volume is the same in
           obs_general for mission_id='HST' and obs_mission_hubble.
        """
        obs = (ObsGeneral.objects.values_list('volume_id')
               .filter(mission_id='HST')
               .annotate(Count('volume_id'))
               .order_by('volume_id'))
        ref = (ObsMissionHubble.objects.values_list('volume_id')
               .annotate(Count('volume_id'))
               .order_by('volume_id'))
        try:
            self.assertEqual(list(obs), list(ref))
        except Exception as e:
            if e.args[0] != MYSQL_TABLE_NOT_EXISTS:
                raise

    def test__nh_counts_match_obs_general(self):
        """Volumes in obs_general = obs_mission_new_horizons.
           Test that the observation count per volume is the same in
           obs_general for mission_id='NH' and obs_mission_newhorizons.
        """
        obs = (ObsGeneral.objects.values_list('volume_id')
               .filter(mission_id='NH')
               .annotate(Count('volume_id'))
               .order_by('volume_id'))
        ref = (ObsMissionNewHorizons.objects.values_list('volume_id')
               .annotate(Count('volume_id'))
               .order_by('volume_id'))
        try:
            self.assertEqual(list(obs), list(ref))
        except Exception as e:
            if e.args[0] != MYSQL_TABLE_NOT_EXISTS:
                raise

    def test__voyager_counts_match_obs_general(self):
        """Volumes in obs_general = obs_mission_voyager.
           Test that the observation count per volume is the same in
           obs_general for mission_id='VG' and obs_mission_voyager.
        """
        obs = (ObsGeneral.objects.values_list('volume_id')
               .filter(mission_id='VG')
               .annotate(Count('volume_id'))
               .order_by('volume_id'))
        ref = (ObsMissionVoyager.objects.values_list('volume_id')
               .annotate(Count('volume_id'))
               .order_by('volume_id'))
        try:
           self.assertEqual(list(obs), list(ref))
        except Exception as e:
            if e.args[0] != MYSQL_TABLE_NOT_EXISTS:
                raise

    def test__COCIRS_counts_match_obs_general(self):
        """Volumes in obs_general = obs_instrument_cocirs.
           Test that the observation count per volume is the same in
           obs_general for instrument_id='COCIRS' and obs_instrument_cocirs.
        """
        obs = (ObsGeneral.objects.values_list('volume_id')
               .filter(instrument_id='COCIRS')
               .annotate(Count('volume_id'))
               .order_by('volume_id'))
        ref = (ObsInstrumentCocirs.objects.values_list('volume_id')
               .annotate(Count('volume_id'))
               .order_by('volume_id'))
        try:
            self.assertEqual(list(obs), list(ref))
        except Exception as e:
            if e.args[0] != MYSQL_TABLE_NOT_EXISTS:
                raise

    def test__COISS_counts_match_obs_general(self):
        """Volumes in obs_general = obs_instrument_coiss.
           Test that the observation count per volume is the same in
           obs_general for instrument_id='COISS' and obs_instrument_coiss.
        """
        obs = (ObsGeneral.objects.values_list('volume_id')
               .filter(instrument_id='COISS')
               .annotate(Count('volume_id'))
               .order_by('volume_id'))
        ref = (ObsInstrumentCoiss.objects.values_list('volume_id')
               .annotate(Count('volume_id'))
               .order_by('volume_id'))
        try:
            self.assertEqual(list(obs), list(ref))
        except Exception as e:
            if e.args[0] != MYSQL_TABLE_NOT_EXISTS:
                raise

    def test__COUVIS_counts_match_obs_general(self):
        """Volumes in obs_general = obs_instrument_couvis.
           Test that the observation count per volume is the same in
           obs_general for instrument_id='COUVIS' and obs_instrument_couvis.
        """
        obs = (ObsGeneral.objects.values_list('volume_id')
               .filter(instrument_id='COUVIS')
               .annotate(Count('volume_id'))
               .order_by('volume_id'))
        ref = (ObsInstrumentCouvis.objects.values_list('volume_id')
               .annotate(Count('volume_id'))
               .order_by('volume_id'))
        try:
            self.assertEqual(list(obs), list(ref))
        except Exception as e:
            if e.args[0] != MYSQL_TABLE_NOT_EXISTS:
                raise

    def test__COVIMS_counts_match_obs_general(self):
        """Volumes in obs_general = obs_instrument_covims.
           Test that the observation count per volume is the same in
           obs_general for instrument_id='COVIMS' and obs_instrument_covims.
        """
        obs = (ObsGeneral.objects.values_list('volume_id')
               .filter(instrument_id='COVIMS')
               .annotate(Count('volume_id'))
               .order_by('volume_id'))
        ref = (ObsInstrumentCovims.objects.values_list('volume_id')
               .annotate(Count('volume_id'))
               .order_by('volume_id'))
        try:
            self.assertEqual(list(obs), list(ref))
        except Exception as e:
            if e.args[0] != MYSQL_TABLE_NOT_EXISTS:
                raise

    def test__GOSSI_counts_match_obs_general(self):
        """Volumes in obs_general = obs_instrument_gossi.
           Test that the observation count per volume is the same in
           obs_general for instrument_id='GOSSI' and obs_instrument_gossi.
        """
        obs = (ObsGeneral.objects.values_list('volume_id')
               .filter(instrument_id='GOSSI')
               .annotate(Count('volume_id'))
               .order_by('volume_id'))
        ref = (ObsInstrumentGossi.objects.values_list('volume_id')
               .annotate(Count('volume_id'))
               .order_by('volume_id'))
        try:
            self.assertEqual(list(obs), list(ref))
        except Exception as e:
            if e.args[0] != MYSQL_TABLE_NOT_EXISTS:
                raise

    def test__nhlorri_counts_match_obs_general(self):
        """Volumes in obs_general = obs_instrument_nhlorri.
           Test that the observation count per volume is the same in
           obs_general for instrument_id='NHLORRI' and obs_instrument_nhlorri.
        """
        obs = (ObsGeneral.objects.values_list('volume_id')
               .filter(instrument_id='NHLORRI')
               .annotate(Count('volume_id'))
               .order_by('volume_id'))
        ref = (ObsInstrumentNhlorri.objects.values_list('volume_id')
               .annotate(Count('volume_id'))
               .order_by('volume_id'))
        try:
            self.assertEqual(list(obs), list(ref))
        except Exception as e:
            if e.args[0] != MYSQL_TABLE_NOT_EXISTS:
                raise

    def test__nhmvic_counts_match_obs_general(self):
        """Volumes in obs_general = obs_instrument_nhmvic.
           Test that the observation count per volume is the same in
           obs_general for instrument_id='NHMVIC' and obs_instrument_nhmvic.
        """
        obs = (ObsGeneral.objects.values_list('volume_id')
               .filter(instrument_id='NHMVIC')
               .annotate(Count('volume_id'))
               .order_by('volume_id'))
        ref = (ObsInstrumentNhmvic.objects.values_list('volume_id')
               .annotate(Count('volume_id'))
               .order_by('volume_id'))
        try:
            self.assertEqual(list(obs), list(ref))
        except Exception as e:
            if e.args[0] != MYSQL_TABLE_NOT_EXISTS:
                raise

    def test__vgiss_counts_match_obs_general(self):
        """Volumes in obs_general = obs_instrument_vgiss.
           Test that the observation count per volume is the same in
           obs_general for instrument_id='VGISS' and obs_instrument_vgiss.
        """
        obs = (ObsGeneral.objects.values_list('volume_id')
               .filter(instrument_id='VGISS')
               .annotate(Count('volume_id'))
               .order_by('volume_id'))
        ref = (ObsInstrumentVgiss.objects.values_list('volume_id')
               .annotate(Count('volume_id'))
               .order_by('volume_id'))
        try:
            self.assertEqual(list(obs), list(ref))
        except Exception as e:
            if e.args[0] != MYSQL_TABLE_NOT_EXISTS:
                raise

    def test__mult_field_matches_id_fields_in_mult_tables(self):
        """Check the obs_general target_name mult to make sure there are no
        references to an id in the mult table that don't have entries.
        """
        cursor = connection.cursor()
        q = """SELECT COUNT(*) FROM obs_general
               WHERE mult_obs_general_target_name NOT IN
                   (SELECT id FROM mult_obs_general_target_name)"""
        cursor.execute(q)
        result = cursor.fetchone()
        cursor.close()
        self.assertEqual(result[0], 0)

    def test__all_sfc_geo_models_should_have_same_fields_as_each_other(self):
        """Find all surface geo models by inspecting the param_info table and
           check that they each have the same parameters defined in the
           Django models.
        """
        # Mimas sets the standard template
        expected_fields = sorted([n for n in ObsSurfaceGeometryMimas.__dict__])
        param_info = (ParamInfo.objects
                      .filter(category_name__contains='surface_geometry__'))
        all_category_names = sorted(list(set([p.category_name
                                              for p in param_info])))
        for cat_name in all_category_names:
            model_name = cat_name.title().replace('_','')
            print(f'Working on {model_name}')
            model = apps.get_model('search', model_name)
            fields = sorted([n for n in model.__dict__])
            print(f'Found {len(fields)} fields expected {len(expected_fields)}')
            self.assertEqual(expected_fields, fields)

    def test__partables_has_all_surface_geo_tables(self):
        """Check that the partables table has an entry for each surface_geo
           table.
           XXX NOTE: We exclude Callirrhoe and Elara from this comparison
           because of GitHub issue #465 "Missing surface geo for Callirrhoe
           and Elara in NHJULO_2001". This causes a surface_geo table to be
           created during the import of NHJULO_1001, and then have no actual
           contents when NHJULO_1001 is replaced by NHJULO_2001.
        """
        count_partables = (Partables.objects
                           .filter(partable__contains='surface_geometry__')
                           .exclude(partable__contains='callirrhoe')
                           .exclude(partable__contains='elara')
                           .values('partable').distinct().count())
        count_surface_geo = (ObsSurfaceGeometry.objects
                             .values('target_name').distinct().count())
        self.assertEqual(count_partables, count_surface_geo)

    def test__tablenames_has_all_surface_geo_tables(self):
        """Check that the table_names table has an entry for each surface_geo
           table.
        """
        count_partables = (Partables.objects
                           .filter(partable__contains='surface_geometry__')
                           .values('partable').distinct().count())
        count_tablenames = (TableNames.objects
                            .filter(table_name__contains='surface_geometry__')
                            .values('table_name').distinct().count())
        self.assertEqual(count_partables, count_tablenames)

    def test__planets_properly_ordered(self):
        "Check that the planets are properly ordered in the planet mult table."
        the_planets = [planet['label']
                       for planet in MultObsGeneralPlanetId.objects
                                        .filter(display='Y').values('label')]
        print('SELECT label FROM mult_obs_general_planet_id WHERE display = "Y" ORDER BY disp_order;')
        expect = ['Venus','Earth', 'Mars', 'Jupiter', 'Saturn', 'Uranus',
                  'Neptune', 'Pluto', 'Other']
        self.assertEqual(expect, the_planets)

    def test__surface_geometry_table_label_is_correct(self):
        "Check the label of the obs_surface_geometry table in table_names."
        label = TableNames.objects.get(table_name='obs_surface_geometry').label
        self.assertEqual(label, 'Surface Geometry Constraints')


            ###################################################
            ######### url_to_search_params UNIT TESTS #########
            ###################################################

    ####################
    ### TIME PARSING ###
    ####################

    def test__url_to_search_params_times_yd(self):
        "Check date parsing in YYYY-DDD format."
        q = QueryDict('timesec1=2000-023T06:00:00&timesec2=2000-024T06:00:00')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_general.time_sec1': [1922432.0],
                        'obs_general.time_sec2': [2008832.0]}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)

    def test__url_to_search_params_times_ymd(self):
        "Check date parsing in YYYY-MM-DD format."
        q = QueryDict('timesec1=2000-01-23T06:00:00&timesec2=2000-01-24T06:00:00')
        (selections, extras) = url_to_search_params(q)
        sel_expected = {'obs_general.time_sec1': [1922432.0],
                        'obs_general.time_sec2': [2008832.0]}
        order_expected = (['obs_general.time1', 'obs_general.opus_id'],
                          [False, False])
        qtypes_expected = {}
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras['order'], order_expected)
        self.assertEqual(extras['qtypes'], qtypes_expected)

    # XXX Eventually we need to catch bad time formats!
    # def test__url_to_search_params_times_bad(self):
    #     q = QueryDict('timesec1=2000-01T06:00:00&timesec2=2000-01-24T06:00:00')
    #     (selections, extras) = url_to_search_params(q)
    #     sel_expected = {'obs_general.time_sec1': [1922432.0],
    #                     'obs_general.time_sec2': [2008832.0]}
    #     order_expected = (['obs_general.time1', 'obs_general.opus_id'],
    #                       [False, False])
    #     qtypes_expected = {}
    #     print(selections)
    #     print(extras)
    #     self.assertEqual(selections, sel_expected)
    #     self.assertEqual(extras['order'], order_expected)
    #     self.assertEqual(extras['qtypes'], qtypes_expected)


    ####################
    ### BASIC RANGES ###
    ####################

    def test__url_to_search_params_from_url_left_side(self):
        "Check range with min only, max missing value."
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

    def test__url_to_search_params_from_url_left_side_2(self):
        "Check range with min only, max missing entirely #2."
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

    def test__url_to_search_params_from_url_left_side_ignore_ui_slugs(self):
        "Check range with min only, max missing value, ignored UI slugs."
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

    def test__url_to_search_params_from_url_right_side(self):
        "Check range with max only, min missing value."
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

    def test__url_to_search_params_from_url_right_side_2(self):
        "Check range with max only, min missing entirely."
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

    def test__url_to_search_params_from_url_both_side(self):
        "Check range with both min and max."
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

    def test__url_to_search_params_from_url_both_side_any(self):
        "Check range with qtype=any."
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

    def test__url_to_search_params_from_url_both_side_all(self):
        "Check range with qtype=all."
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

    def test__url_to_search_params_from_url_both_side_only(self):
        "Check range with qtype=only."
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

    def test__url_to_search_params_stringsearch(self):
        "Check search on a string value."
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
        "Check string search with qtype=contains"
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

    def test__url_to_search_params_mults_uc(self):
        "Check mults."
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
        "Check mults."
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
        "Check mults using a + to mean space."
        q = QueryDict('instrumentid=Cassini+ISS')
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
        "Check mults using %2B to mean plus."
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
        "Check mults from different tables."
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
        "Check mults and string searches at the same time."
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
        "Check default sort order."
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
        "Check blank sort order."
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
        "Check bad sort order."
        q = QueryDict('planet=Saturn&order=time1,-fredethel')
        (selections, extras) = url_to_search_params(q)
        sel_expected = None
        extras_expected = None
        print(selections)
        print(extras)
        self.assertEqual(selections, sel_expected)
        self.assertEqual(extras, extras_expected)

    def test__url_to_search_params_from_sort_opusid(self):
        "Check sort on opusid."
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
        "Check sort on descending opusid."
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
        "Check sort on descending opusid."
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
    #     selections = {'obs_general.planet_id': ['Saturn'], 'obs_general.time_sec2': ['2009-12-28'], 'obs_general.time_sec1': ['2009-12-23']}
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
        "Test a single column range with min only."
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
        "Test a single column range with max only."
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
        "Test a single column range with both min and max."
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
        "Test a single column range with bogus qtype=all."
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
        "Test a long range with qtype=any, min only."
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
        "Test a long range with qtype=any, max only."
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
        "Test a long range with qtype=any, both min and max."
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
        "Test a long range with qtype=all, min only."
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
        "Test a long range with qtype=all, max only."
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
        "Test a long range with qtype=all, both min and max."
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
        "Test a long range with qtype=only, min only."
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
        "Test a long range with qtype=only, max only."
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
        "Test a long range with qtype=only, both min and max."
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
        "Test a single column long range with min only."
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
        "Test a single column long range with max only."
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
        "Test a single column long range with both min and max."
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
        "Test a single column long range with bogus qtype=all."
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
        "Test a long range with qtype=any, min only."
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
        "Test a long range with qtype=any, max only."
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
        "Test a long range with qtype=any, both min and max."
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
        "Test a long range with qtype=all, min only."
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
        "Test a long range with qtype=all, max only."
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
        "Test a long range with qtype=all, both min and max."
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
        "Test a long range with qtype=only, min only."
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
        "Test a long range with qtype=only, max only."
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
        "Test a long range with qtype=only, both min and max."
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
        "Test a single column long range with both min and max."
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
        "Test a long range with qtype=any, both min and max."
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
        "Test a long range with qtype=all, both min and max."
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
        "Test a long range with qtype=only, both min and max."
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
        "Test a string query with no qtype."
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
        "Test a string query with qtype contains."
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
        "Test a string query with qtype begins."
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
        "Test a string query with qtype ends."
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
        "Test a string query with qtype matches."
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
        "Test a string query with qtype excludes."
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
        "Check construct_query_string with unknown param name."
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
        "Check construct_query_string with unknown param name #2."
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
        "Check construct_query_string with unknown param name #3."
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
        "Check construct_query_string with unknown param name #4."
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
        "Check construct_query_string with just obs_general."
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
        "Check construct_query_string with a string."
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
        "Check construct_query_string with a single column range."
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
        "Check construct_query_string with a string and qtype."
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
        "Check construct_query_string with planet_id."
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
        "Check construct_query_string with planet_id in upper case."
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
        "Check construct_query_string with planet_id empty."
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
        "Check construct_query_string with planet_id unknown planet."
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
        "Check construct_query_string with two mults."
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
        "Check construct_query_string with obs_general and obs_instrument_coiss."
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
        "Check construct_query_string with three tables."
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
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__construct_query_string_order_existing_table(self):
        "Check construct_query_string with sort order already joined."
        selections = {'obs_general.observation_duration1': [20]}
        extras = {'order': (['obs_general.time_sec1'], [False])}
        sql, params = construct_query_string(selections, extras)
        print(sql)
        print(params)
        expected = 'SELECT `obs_general`.`id` FROM `obs_general` WHERE (`obs_general`.`observation_duration` >= %s) ORDER BY obs_general.time_sec1 ASC'
        expected_params = [20]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__construct_query_string_order_existing_table_2(self):
        "Check construct_query_string with sort order already joined #2."
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
        "Check construct_query_string with complex sort order already joined."
        selections = {'obs_general.observation_duration1': [20]}
        extras = {'order': (['obs_general.time_sec1',
                             'obs_general.time_sec2'],
                            [False, True])}
        sql, params = construct_query_string(selections, extras)
        print(sql)
        print(params)
        expected = 'SELECT `obs_general`.`id` FROM `obs_general` WHERE (`obs_general`.`observation_duration` >= %s) ORDER BY obs_general.time_sec1 ASC,obs_general.time_sec2 DESC'
        expected_params = [20]
        print(expected)
        print(expected_params)
        self.assertEqual(sql, expected)
        self.assertEqual(params, expected_params)

    def test__construct_query_string_order_new_table(self):
        "Check construct_query_string with sort order not already joined."
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
    #
    #
    # ## test urlToSearchParam
    # def test__url_to_search_params_single_column_range(self):
    #     q = QueryDict('ringcenterphase1=20&ringcenterphase2=180')
    #     (selections,extras) = url_to_search_params(q)
    #     expected = {'obs_ring_geometry.ring_center_phase1': [20.0], 'obs_ring_geometry.ring_center_phase2': [180.0]}
    #     print(selections)
    #     self.assertEqual(selections,expected)
    #
