################################################################################
# obs_instrument_vgiss.py
#
# Defines the ObsInstrumentVGISS class, which encapsulates fields in the
# obs_instrument_vgiss table.
################################################################################

from obs_mission_voyager import ObsMissionVoyager


# Data from: https://pds-rings.seti.org/voyager/iss/inst_cat_wa1.html#inst_info
# (WL MIN, WL MAX)
_VGISS_FILTER_WAVELENGTHS = { # XXX
    'CLEAR':  (280, 640),
    'VIOLET': (350, 450),
    'GREEN':  (530, 640),
    'ORANGE': (590, 640),
    'SODIUM': (588, 590),
    'UV':     (280, 370),
    'BLUE':   (430, 530),
    'CH4_JS': (614, 624),
    'CH4_U':  (536, 546),
}


class ObsInstrumentVGISS(ObsMissionVoyager):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    #############################
    ### OVERRIDE FROM ObsBase ###
    #############################

    @property
    def instrument_id(self):
        return 'VGISS'

    def opus_id_from_supp_index_row(self, supp_row):
        volume_id = supp_row['VOLUME_NAME']
        filespec = supp_row['FILE_SPECIFICATION_NAME']
        full_filespec = volume_id + '/' + filespec
        pdsf = self._pdsfile_from_filespec(full_filespec)
        opus_id = pdsf.opus_id
        if not opus_id:
            self._log_nonrepeating_error(
                        'Unable to create OPUS_ID from supplemental index')
            return filespec.split('/')[-1]
        return opus_id

    def convert_filespec_from_lbl(self, filespec):
        return filespec.replace('.LBL', '.IMG')


    ################################
    ### OVERRIDE FROM ObsGeneral ###
    ################################

    def field_obs_general_observation_duration(self):
        exposure = self._index_col('EXPOSURE_DURATION')
        if exposure is None or exposure < 0:
            # There's one exposure somewhere that has duration -0.09999
            return None
        return exposure

    def field_obs_general_right_asc1(self):
        return self._ring_geo_index_col('MINIMUM_RIGHT_ASCENSION')

    def field_obs_general_right_asc2(self):
        return self._ring_geo_index_col('MAXIMUM_RIGHT_ASCENSION')

    def field_obs_general_declination1(self):
        return self._ring_geo_index_col('MINIMUM_DECLINATION')

    def field_obs_general_declination2(self):
        return self._ring_geo_index_col('MAXIMUM_DECLINATION')

    def field_obs_general_ring_obs_id(self):
        filename = self._index_col('PRODUCT_ID')
        image_num = filename[1:8]
        inst_host_num = self._index_col('INSTRUMENT_HOST_NAME')[-1]
        camera = self._index_col('INSTRUMENT_NAME')[0]
        planet = self.field_obs_general_planet_id()
        if planet is None:
            pl_str = ''
        else:
            pl_str = planet[0]

        return f'{pl_str}_IMG_VG{inst_host_num}_ISS_{image_num}_{camera}'

    def field_obs_general_quantity(self):
        filter_name = self._index_col('FILTER_NAME')
        if filter_name == 'UV':
            return 'EMISSION'
        return 'REFLECT'

    def field_obs_general_observation_type(self):
        return 'IMG'


    ############################
    ### OVERRIDE FROM ObsPds ###
    ############################

    def field_obs_pds_note(self):
        return self._index_col('NOTE')


    ##################################
    ### OVERRIDE FROM ObsTypeImage ###
    ##################################

    def field_obs_type_image_image_type_id(self):
        return 'FRAM'

    def field_obs_type_image_duration(self):
        return self.field_obs_general_observation_duration()

    def field_obs_type_image_levels(self):
        return 256

    def _vgiss_pixel_size_helper(self):
        line1 = self._supp_index_col('FIRST_LINE')
        line2 = self._supp_index_col('LAST_LINE')
        sample1 = self._supp_index_col('FIRST_SAMPLE')
        sample2 = self._supp_index_col('LAST_SAMPLE')
        return line2-line1+1, sample2-sample1+1

    def field_obs_type_image_greater_pixel_size(self):
        pix1, pix2 = self._vgiss_pixel_size_helper()
        return max(pix1, pix2)

    def field_obs_type_image_lesser_pixel_size(self):
        pix1, pix2 = self._vgiss_pixel_size_helper()
        return min(pix1, pix2)


    ###################################
    ### OVERRIDE FROM ObsWavelength ###
    ###################################

    def _vgiss_wavelength_helper(self):
        filter_name = self._index_col('FILTER_NAME')
        if filter_name not in _VGISS_FILTER_WAVELENGTHS:
            self._log_nonrepeating_error(f'Unknown VGISS filter name "{filter_name}"')
            return 0
        return _VGISS_FILTER_WAVELENGTHS[filter_name]

    def field_obs_wavelength_wavelength1(self):
        return self._vgiss_wavelength_helper()[0] / 1000 # microns

    def field_obs_wavelength_wavelength2(self):
        return self._vgiss_wavelength_helper()[1] / 1000 # microns

    def field_obs_wavelength_wave_res1(self):
        return self._wave_res_from_full_bandwidth()

    def field_obs_wavelength_wave_res2(self):
        return self.field_obs_wavelength_wave_res1()

    def field_obs_wavelength_wave_no_res1(self):
        return self._wave_no_res_from_full_bandwidth()

    def field_obs_wavelength_wave_no_res2(self):
        return self.field_obs_wavelength_wave_no_res1()


    #######################################
    ### OVERRIDE FROM ObsMissionVoyager ###
    #######################################

    def field_obs_mission_voyager_mission_phase_name(self):
        return self._index_col('MISSION_PHASE_NAME')


    ####################################
    ### FIELD METHODS FOR THIS TABLE ###
    ####################################

    def field_obs_instrument_vgiss_opus_id(self):
        return self.opus_id

    def field_obs_instrument_vgiss_volume_id(self):
        return self.volume

    def field_obs_instrument_vgiss_instrument_id(self):
        return self.instrument_id

    def field_obs_instrument_vgiss_image_id(self):
        return self._index_col('IMAGE_ID')

    def field_obs_instrument_vgiss_scan_mode(self):
        return self._index_col('SCAN_MODE')

    def field_obs_instrument_vgiss_shutter_mode(self):
        return self._index_col('SHUTTER_MODE')

    def field_obs_instrument_vgiss_gain_mode(self):
        return self._index_col('GAIN_MODE')

    def field_obs_instrument_vgiss_edit_mode(self):
        return self._index_col('EDIT_MODE')

    def field_obs_instrument_vgiss_filter_name(self):
        return self._index_col('FILTER_NAME')

    def field_obs_instrument_vgiss_filter_number(self):
        return self._index_col('FILTER_NUMBER')

    def field_obs_instrument_vgiss_camera(self):
        camera = self._index_col('INSTRUMENT_NAME')
        assert camera in ['NARROW ANGLE CAMERA', 'WIDE ANGLE CAMERA']
        return camera[0]

    def field_obs_instrument_vgiss_usable_lines(self):
        line1 = self._supp_index_col('FIRST_LINE')
        line2 = self._supp_index_col('LAST_LINE')
        return line2-line1+1

    def field_obs_instrument_vgiss_usable_samples(self):
        sample1 = self._supp_index_col('FIRST_SAMPLE')
        sample2 = self._supp_index_col('LAST_SAMPLE')
        return sample2-sample1+1
