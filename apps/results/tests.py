"""
# results tests

"""
import json
from django.test import RequestFactory

# from django.test import TestCase  removed because it deletes test table data after every test
from unittest import TestCase
from django.test.client import Client
from django.http import QueryDict
from django.contrib.auth.models import AnonymousUser, User

from search.views import *
from results.views import *

from django.conf import settings

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_COOKIE_NAME = 'opus-test-cookie'
settings.CACHE_BACKEND = 'dummy:///'

cursor = connection.cursor()

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


class resultsTests(TestCase):

    param_name = 'obs_general.planet_id'
    selections = {}
    selections[param_name] = ['Jupiter']

    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()

    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()

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

    def test__no_images_are_without_size(self):
        where = " size_thumb is null  or size_small is null  or size_med is null  or size_full is null"
        # where += " or size_thumb = 0 or size_small = 0 or size_med = 0 or size_full = 0"
        query = Image.objects.extra(where=[where])
        print query.query
        count = query.count()
        self.assertEqual(count, 0)

    def test__images_has_all_volumes(self):
        img_vols = Image.objects.all().values_list('volume_id', flat=True)
        all_vols = ObsGeneral.objects.all().values_list('volume_id',flat=True)
        print """if this fails there are volumes in obs_general
               that do not appear in images

               select distinct volume_id from obs_general
               where volume_id not in (select distinct volume_id from images);

               """
        self.assertEqual(set([]), set(all_vols) - set(img_vols))

    def test__files_has_all_volumes(self):
        file_vols = Files.objects.all().values_list('volume_id', flat=True)
        all_vols = ObsGeneral.objects.all().values_list('volume_id',flat=True)
        print """if this fails there are volumes in obs_general
               that do not appear in files

               select distinct volume_id from obs_general
               where volume_id not in (select distinct volume_id from files);


               """
        self.assertEqual(set([]), set(all_vols) - set(file_vols))

    # >>>>>>> master

    def test__get_base_path_previews(self):
        ring_obs_id = 'S_SPEC_CO_CIRS_1633035651_FP4'
        preview = get_base_path_previews(ring_obs_id)
        self.assertEqual(preview, 'COCIRS_5xxx/')

    def test__getPage_no_selections(self):
        request = self.factory.get('some_request?', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        request.user = AnonymousUser()
        request.session = test_session()
        response = getPage(request)
        result_count = len(response[2])
        self.assertGreater(result_count, 99)

    def test__getPage_no_selections_big_limit(self):
        request = self.factory.get('some_request?limit=6000', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        request.user = AnonymousUser()
        request.session = test_session()
        response = getPage(request)
        result_count = len(response[2])
        self.assertGreater(result_count, 5999)


    def test__getFiles(self):
        ring_obs_id = 'S_IMG_CO_ISS_1688230146_N'
        product_types = ['CALIBRATED','RAW_IMAGE']
        files = getFiles(ring_obs_id, fmt='raw', loc_type="path", product_types=product_types)
        print files[ring_obs_id]
        expected = {'S_IMG_CO_ISS_1688230146_N': {u'RAW_IMAGE': [u'/volumes/TINY/pdsdata/volumes/COISS_2xxx/COISS_2069/data/1688230146_1688906749/N1688230146_1.LBL', u'/volumes/TINY/pdsdata/volumes/COISS_2xxx/COISS_2069/data/1688230146_1688906749/N1688230146_1.IMG', u'/volumes/TINY/pdsdata/volumes/COISS_2xxx/COISS_2069/LABEL/TLMTAB.FMT', u'/volumes/TINY/pdsdata/volumes/COISS_2xxx/COISS_2069/LABEL/PREFIX3.FMT'], u'CALIBRATED': [u'/volumes/TINY/pdsdata/volumes/derived/COISS_2xxx/COISS_2069/data/1688230146_1688906749/N1688230146_1_CALIB.LBL', u'/volumes/TINY/pdsdata/volumes/derived/COISS_2xxx/COISS_2069/data/1688230146_1688906749/N1688230146_1_CALIB.IMG', u'/volumes/TINY/pdsdata/volumes/COISS_2xxx/COISS_2xxx/COISS_2069/LABEL/TLMTAB.FMT', u'/volumes/TINY/pdsdata/volumes/COISS_2xxx/COISS_2xxx/COISS_2069/LABEL/PREFIX3.FMT']}}
        print 'expected:'
        print expected[ring_obs_id]
        self.assertEqual(len(files[ring_obs_id]['CALIBRATED']), len(expected[ring_obs_id]['CALIBRATED']))

    def test__get_triggered_tables(self):
        q = QueryDict("planet=Saturn")
        (selections,extras) = urlToSearchParams(q)
        partables = get_triggered_tables(selections, extras)
        print selections
        print sorted(partables)
        try:
            # local database is smaller and saturn will trigger the mission cassini table:
            expected = sorted([u'obs_general', u'obs_mission_cassini', u'obs_ring_geometry', u'obs_surface_geometry', u'obs_wavelength'])
            self.assertEqual(sorted(partables), expected)
        except:
            # local database is smaller and saturn will trigger the mission cassini table, production will not:
            expected = sorted([u'obs_general', u'obs_ring_geometry', u'obs_surface_geometry', u'obs_wavelength'])
            self.assertEqual(sorted(partables), expected)


    def test__get_triggered_tables_COISS(self):
        q = QueryDict("planet=SATURN&instrumentid=COISS")
        (selections,extras) = urlToSearchParams(q)
        print selections
        partables = get_triggered_tables(selections, extras)
        expected = sorted([u'obs_general', u'obs_type_image', u'obs_wavelength', u'obs_ring_geometry', u'obs_mission_cassini', u'obs_instrument_COISS','obs_surface_geometry'])
        print 'partables:'
        print partables
        print 'expected:'
        print expected
        self.assertEqual(partables, expected)

    def test__get_triggered_tables_target(self):
        selections, extras = {}, {}
        selections['obs_general.planet_id'] = ["Saturn"]
        selections['obs_general.target_name'] = ["PANDORA"]
        selections['obs_general.instrument_id'] = ["COISS"]
        partables = get_triggered_tables(selections, extras)
        print selections
        expected = sorted([u'obs_general', u'obs_type_image', u'obs_wavelength', u'obs_ring_geometry', u'obs_mission_cassini', u'obs_instrument_COISS','obs_surface_geometry'])
        print 'partables:'
        print partables
        print 'expected:'
        print expected
        self.assertEqual(partables, expected)

    def test__get_triggered_tables_target_def(self):
        selections, extras = {}, {}
        selections['obs_general.target_name'] = ["NEPTUNE"]
        partables = get_triggered_tables(selections, extras)
        expected = sorted([u'obs_general', u'obs_ring_geometry', u'obs_surface_geometry', u'obs_type_image', u'obs_wavelength'])
        print 'partables:'
        print partables
        print 'expected:'
        print expected
        print 'selections:'
        print selections
        self.assertEqual(sorted(partables), expected)

    def test__get_metadata(self):
        response = self.client.get('/opus/api/metadata/S_IMG_CO_ISS_1686170143_N.json')
        data = json.loads(response.content)
        print data['Cassini Mission Constraints']
        expected = {"General Constraints": {"is_image": 1, "planet_id": "SAT", "target_name": "IAPETUS", "mission_id": "CO", "inst_host_id": "CO", "instrument_id": "COISS", "time_sec2": 360791253.845, "time2": "2011-158T19:46:59.845", "target_class": "MOON", "quantity": "REFLECT", "type_id": "IMG", "ring_obs_id": "S_IMG_CO_ISS_1686170143_N", "note": "N/A", "right_asc2": 298.703957, "declination2": 84.37116, "observation_duration": 1.5, "volume_id_list": "COISS_2068", "primary_file_spec": "COISS_2068/data/1686113920_1686232684/N1686170143_1.IMG"}, "Saturn Surface Geometry": {"Observer_longitude": None, "d_Observer_longitude": None, "solar_hour_angle": None, "d_solar_hour_angle": None, "IAU_west_longitude": None, "d_IAU_west_longitude": None, "planetocentric_latitude2": None, "sub_solar_planetocentric_latitude": 9.807, "sub_observer_planetocentric_latitude": 0.358, "planetographic_latitude2": None, "sub_solar_planetographic_latitude": 11.994, "sub_observer_planetographic_latitude": 0.44, "IAU_west_longitude2": None, "Observer_longitude2": None, "sub_solar_IAU_longitude": 42.254, "sub_observer_IAU_longitude": 327.762, "finest_resolution2": None, "coarsest_resolution2": None, "center_resolution": 21.29031, "solar_hour_angle2": None, "phase2": None, "center_phase_angle": 74.661, "incidence2": None, "emission2": None, "range_to_body2": None, "center_distance": 3568906.674}, "Iapetus Surface Geometry": {"Observer_longitude": -47.5735, "d_Observer_longitude": 85.18350000000001, "solar_hour_angle": 180.0, "d_solar_hour_angle": 180.0, "IAU_west_longitude": 252.66, "d_IAU_west_longitude": 85.184, "planetocentric_latitude2": 5.298, "sub_solar_planetocentric_latitude": 11.838, "sub_observer_planetocentric_latitude": -80.121, "planetographic_latitude2": 5.828, "sub_solar_planetographic_latitude": 12.991, "sub_observer_planetographic_latitude": -81.009, "IAU_west_longitude2": 337.844, "Observer_longitude2": 37.61, "sub_solar_IAU_longitude": 253.148, "sub_observer_IAU_longitude": 300.233, "finest_resolution2": 5.16964, "coarsest_resolution2": 134.66413, "center_resolution": 5.16977, "solar_hour_angle2": 360.0, "phase2": 95.085, "center_phase_angle": 95.035, "incidence2": 178.952, "emission2": 88.387, "range_to_body2": 866598.415, "center_distance": 866610.707}, "Ring Geometry Constraints": {"ring_radius2": None, "resolution2": None, "projected_radial_resolution2": None, "range_to_ring_intercept2": None, "ring_center_distance": 3568906.674, "J2000_longitude2": None, "solar_hour_angle2": None, "longitude_WRT_observer2": None, "ring_azimuth_WRT_observer2": None, "sub_solar_ring_long": 15.211, "sub_observer_ring_long": 89.702, "solar_ring_elev2": None, "observer_ring_elevation2": -999.0, "phase2": None, "incidence2": None, "emission2": None, "north_based_incidence2": None, "north_based_emission2": None, "ring_center_phase": 74.661, "ring_center_incidence": 80.192, "ring_center_emission": 89.643, "ring_center_north_based_incidence": 80.192, "ring_center_north_based_emission": 89.643, "solar_ring_opening_angle": 9.807, "observer_ring_opening_angle": 0.358, "edge_on_radius2": None, "edge_on_altitude2": None, "edge_on_radial_resolution2": None, "range_to_edge_on_point2": None, "edge_on_J2000_longitude2": None, "edge_on_solar_hour_angle2": None}, "Wavelength Constraints": {"wavelength2": 0.862, "spec_flag": "N", "wave_res2": None, "wave_no2": None, "wave_no_res2": None, "spec_size": None, "polarization_type": "NONE"}, "Image Constraints": {"duration": 1.5, "image_type_id": "FRAM", "greater_pixel_size": 1024.0, "lesser_pixel_size": 1024.0, "levels": "4096"}, "Cassini Mission Constraints": {"cassini_target_name": "Iapetus", "rev_no": "149", "obs_name": "ISS_149IA_IAPETUS157_PRIME", "activity_name": "IAPETUS", "spacecraft_clock_count2": 1686170143.126, "prime": "Y", "prime_inst_id": "COISS", "ert_sec2": 360915801.835}, "Cassini ISS Constraints": {"FILTER_NAME": "IR2  ,CL2", "INST_CMPRS_RATE_expected_average": 3.30956, "INST_CMPRS_RATE_actual_average": 2.514053, "VALID_MAXIMUM_minimum_full_well_saturation_level": 4095, "VALID_MAXIMUM_maximum_DN_saturation_level": 4095, "ANTIBLOOMING_STATE_FLAG": "OFF", "CALIBRATION_LAMP_STATE_FLAG": "N/A", "DELAYED_READOUT_FLAG": "NO", "FILTER_TEMPERATURE": 0.248629, "LIGHT_FLOOD_STATE_FLAG": "ON", "MISSING_PACKET_FLAG": "NO", "camera": "N", "FILTER": "IR2", "IMAGE_OBSERVATION_TYPE": "SCIENCE", "SHUTTER_MODE_ID": "NACONLY", "DATA_CONVERSION_TYPE": "12BIT", "GAIN_MODE_ID": "29 ELECTRONS PER DN", "INST_CMPRS_TYPE": "LOSSLESS", "SHUTTER_STATE_ID": "ENABLED", "INST_CMPRS_RATIO": 6.364224, "TELEMETRY_FORMAT_ID": "S_N_ER_3", "MISSING_LINES": 0, "OPTICS_TEMPERATURE_front": 0.627499, "INST_CMPRS_PARAM_QF": -2147483648, "INST_CMPRS_PARAM_TB": -2147483648, "INST_CMPRS_PARAM_GOB": -2147483648, "EXPECTED_MAXIMUM_full_well_DN": 0.227162, "OPTICS_TEMPERATURE_rear": 1.820474, "EXPECTED_MAXIMUM_max_DN": 0.250449, "INST_CMPRS_PARAM_MALGO": -2147483648}}
        self.assertEqual(data['Cassini Mission Constraints'],expected['Cassini Mission Constraints'])

    def test__metadata_S_IMG_CO_ISS_1686170088_N(self):
        ring_obs_id = 'S_IMG_CO_ISS_1686170088_N'
        detail, all_info = get_metadata({},ring_obs_id=ring_obs_id,fmt='raw')
        print detail['Cassini Mission Constraints']
        expected = {u'General Constraints': {u'instrument_id': u'COISS', u'note': u'N/A', u'time_sec1': 360791198.385, u'is_image': 1, u'type_id': u'IMG', u'target_name': u'IAPETUS', u'primary_file_spec': u'COISS_2068/data/1686113920_1686232684/N1686170088_1.IMG', u'inst_host_id': u'CO', u'class_id': u'R', u'observation_duration': 0.46000003814697266, u'mission_id': u'CO', u'time_sec2': 360791198.845, u'volume_id_list': u'COISS_2068', u'ring_obs_id': u'S_IMG_CO_ISS_1686170088_N', u'declination1': 83.960869, u'declination2': 84.364349, u'planet_id': u'SAT', u'right_asc2': 298.739665, u'target_class': u'MOON', u'right_asc1': 294.767913, u'quantity': u'REFLECT'}, u'Ring Geometry Constraints': {u'edge_on_altitude2': None, u'edge_on_solar_hour_angle1': None, u'resolution1': None, u'edge_on_solar_hour_angle2': None, u'ring_center_distance': 3568988.32, u'edge_on_altitude1': None, u'ring_center_phase': 74.66, u'north_based_emission2': None, u'north_based_emission1': None, u'range_to_edge_on_point2': None, u'resolution2': None, u'solar_ring_opening_angle': 9.807, u'projected_radial_resolution1': None, u'range_to_ring_intercept2': None, u'range_to_ring_intercept1': None, u'projected_radial_resolution2': None, u'longitude_WRT_observer2': None, u'longitude_WRT_observer1': None, u'edge_on_radius1': None, u'edge_on_radius2': None, u'ring_azimuth_WRT_observer2': None, u'ring_azimuth_WRT_observer1': None, u'emission2': None, u'solar_ring_elev2': None, u'solar_ring_elev1': None, u'observer_ring_elevation1': None, u'phase1': None, u'observer_ring_elevation2': -999.0, u'sub_observer_ring_long': 89.701, u'ring_center_north_based_incidence': 80.192, u'emission1': None, u'ring_center_emission': 89.642, u'observer_ring_opening_angle': 0.359, u'phase2': None, u'ring_center_north_based_emission': 89.642, u'J2000_longitude2': None, u'J2000_longitude1': None, u'edge_on_radial_resolution1': None, u'edge_on_radial_resolution2': None, u'ring_radius1': None, u'ring_radius2': None, u'range_to_edge_on_point1': None, u'sub_solar_ring_long': 15.211, u'solar_hour_angle1': None, u'north_based_incidence1': None, u'north_based_incidence2': None, u'solar_hour_angle2': None, u'edge_on_J2000_longitude2': None, u'edge_on_J2000_longitude1': None, u'incidence1': None, u'incidence2': None, u'ring_center_incidence': 80.192}, u'Wavelength Constraints': {u'wavelength2': 0.65, u'wave_no1': None, u'wavelength1': 0.65, u'wave_no_res1': None, u'wave_no_res2': None, u'spec_size': None, u'polarization_type': u'NONE', u'wave_no2': None, u'wave_res1': None, u'wave_res2': None, u'spec_flag': u'N'}, u'Image Constraints': {u'duration': 0.46, u'greater_pixel_size': 1024.0, u'lesser_pixel_size': 1024.0, u'levels': u'4096', u'image_type_id': u'FRAM'}, u'Cassini Mission Constraints': {u'prime': u'Y', u'rev_no': u'149', u'cassini_target_name': u'Iapetus', u'obs_name': u'ISS_149IA_IAPETUS157_PRIME', u'spacecraft_clock_count2': 1686170088.126, u'spacecraft_clock_count1': 1686170088.011, u'prime_inst_id': u'COISS', u'ert_sec2': 360915687.179, u'activity_name': u'IAPETUS', u'ert_sec1': 360915573.146}, u'Cassini ISS Constraints': {u'DELAYED_READOUT_FLAG': u'NO', u'IMAGE_OBSERVATION_TYPE': u'SCIENCE', u'OPTICS_TEMPERATURE_front': 0.627499, u'INST_CMPRS_PARAM_GOB': -2147483648L, u'INST_CMPRS_PARAM_QF': -2147483648L, u'VALID_MAXIMUM_minimum_full_well_saturation_level': 4095L, u'LIGHT_FLOOD_STATE_FLAG': u'ON', u'MISSING_LINES': 0L, u'ANTIBLOOMING_STATE_FLAG': u'OFF', u'FILTER_NAME': u'RED  ,CL2', u'INST_CMPRS_RATE_actual_average': 2.482697, u'FILTER_TEMPERATURE': -0.468354, u'EXPECTED_MAXIMUM_full_well_DN': 0.185018, u'TELEMETRY_FORMAT_ID': u'S_N_ER_3', u'camera': u'N', u'INST_CMPRS_PARAM_MALGO': -2147483648L, u'MISSING_PACKET_FLAG': u'NO', u'GAIN_MODE_ID': u'29 ELECTRONS PER DN', u'DATA_CONVERSION_TYPE': u'12BIT', u'OPTICS_TEMPERATURE_rear': 1.820474, u'SHUTTER_STATE_ID': u'ENABLED', u'VALID_MAXIMUM_maximum_DN_saturation_level': 4095L, u'SHUTTER_MODE_ID': u'NACONLY', u'INST_CMPRS_RATIO': 6.444606, u'CALIBRATION_LAMP_STATE_FLAG': u'N/A', u'INST_CMPRS_RATE_expected_average': 3.21233, u'FILTER': u'RED', u'INST_CMPRS_TYPE': u'LOSSLESS', u'EXPECTED_MAXIMUM_max_DN': 0.203985, u'INST_CMPRS_PARAM_TB': -2147483648L}, u'Iapetus Surface Geometry': {u'sub_observer_planetocentric_latitude': -80.13, u'Observer_longitude2': 41.472, u'Observer_longitude1': -131.232, u'coarsest_resolution1': 5.19282, u'sub_observer_IAU_longitude': 300.222, u'coarsest_resolution2': 269.02888, u'd_IAU_west_longitude': 86.352, u'IAU_west_longitude': 255.342, u'sub_observer_planetographic_latitude': -80.984, u'planetocentric_latitude2': 4.194, u'Observer_longitude': -44.879999999999995, u'planetocentric_latitude1': -76.873, u'sub_solar_planetographic_latitude': 12.945, u'd_solar_hour_angle': 180.0, u'emission2': 88.898, u'd_Observer_longitude': 86.352, u'phase1': 94.991, u'emission1': 1.084, u'range_to_body2': 866579.954, u'range_to_body1': 865886.822, u'center_resolution': 5.1697, u'solar_hour_angle': 180.0, u'phase2': 95.09, u'planetographic_latitude2': 4.598, u'planetographic_latitude1': -77.994, u'center_distance': 866599.797, u'IAU_west_longitude1': 168.99, u'IAU_west_longitude2': 341.694, u'solar_hour_angle1': 0.0, u'finest_resolution1': 5.16547, u'finest_resolution2': 5.16958, u'solar_hour_angle2': 360.0, u'incidence2': 177.831, u'center_phase_angle': 95.04, u'sub_solar_IAU_longitude': 253.146, u'incidence1': 7.753, u'sub_solar_planetocentric_latitude': 11.838}, u'Saturn Surface Geometry': {u'sub_observer_planetocentric_latitude': 0.359, u'Observer_longitude2': None, u'Observer_longitude1': None, u'coarsest_resolution1': None, u'sub_observer_IAU_longitude': 327.261, u'coarsest_resolution2': None, u'd_IAU_west_longitude': None, u'IAU_west_longitude': None, u'sub_observer_planetographic_latitude': 0.441, u'planetocentric_latitude2': None, u'Observer_longitude': None, u'planetocentric_latitude1': None, u'sub_solar_planetographic_latitude': 11.994, u'd_solar_hour_angle': None, u'emission2': None, u'd_Observer_longitude': None, u'phase1': None, u'emission1': None, u'range_to_body2': None, u'range_to_body1': None, u'center_resolution': 21.2908, u'solar_hour_angle': None, u'phase2': None, u'planetographic_latitude2': None, u'planetographic_latitude1': None, u'center_distance': 3568988.32, u'IAU_west_longitude1': None, u'IAU_west_longitude2': None, u'solar_hour_angle1': None, u'finest_resolution1': None, u'finest_resolution2': None, u'solar_hour_angle2': None, u'incidence2': None, u'center_phase_angle': 74.66, u'sub_solar_IAU_longitude': 41.751, u'incidence1': None, u'sub_solar_planetocentric_latitude': 9.807}}
        self.assertEqual(detail['Cassini Mission Constraints'],expected['Cassini Mission Constraints'])

    def test__metadata_J_IMG_CO_ISS_1353756055_W(self):
        ring_obs_id = 'J_IMG_CO_ISS_1353756055_W'
        detail, all_info = get_metadata({},ring_obs_id=ring_obs_id,fmt='raw')
        print detail
        print detail['Cassini Mission Constraints']
        expected = {u'prime': u'Y', u'rev_no': u'C23', u'cassini_target_name': u'Jupiter', u'obs_name': u'ISS_C23JU_6ATM2X2B079_PRIME', u'spacecraft_clock_count2': 1353756055.118, u'spacecraft_clock_count1': 1353756055.023, u'prime_inst_id': u'COISS', u'ert_sec2': 28391712.071, u'activity_name': u'6ATM2X2B', u'ert_sec1': 28391711.382}
        self.assertEqual(detail['Cassini Mission Constraints'],expected)

    def test__metadata_html__S_IMG_CO_ISS_1686170088_N(self):
        response = self.client.get('/opus/api/detail/S_IMG_CO_ISS_1686170143_N.html')
        print 'hello1'
        print response.content.strip()
        print 'hello2'

        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.content), 2000)

    def test__getImageSingle(self):
        response = self.client.get('/opus/api/image/thumb/S_IMG_CO_ISS_1686170143_N.html')
        content = response.content
        content = ' '.join([s.strip() for s in content.splitlines()]).strip()
        print content
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(content), 50)

    def test__getImages(self):
        response = self.client.get('/opus/api/images/small.json?planet=Saturn')
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.content), 12000)
