"""The obs class for VGISS_5xxx through VGISS_8xxx.

Voyager ISS images of the four outer planets. The supplemental index names the volume in
a column of its own, which is why the OPUS id is derived from it separately.
"""

from typing import cast

from opus_import.import_util import IndexRow
from opus_import.obs.field_types import FloatField, IntField, MultFieldRet, StrField, as_int
from opus_import.obs.obs_type_image import EIGHT_BIT_IMAGE_LEVELS
from opus_import.obs.obs_volume_voyager_common import ObsVolumeVoyagerCommon

# Data from: https://pds-rings.seti.org/voyager/iss/inst_cat_wa1.html#inst_info
# (WL MIN, WL MAX)
_VGISS_FILTER_WAVELENGTHS = {
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


class ObsVolumeVGISS5678xxx(ObsVolumeVoyagerCommon):
    """The Voyager ISS images of VGISS_5xxx through VGISS_8xxx.

    Its ``field_obs_*`` methods each fill the schema column their name ends in,
    declaring the type `opus_import.obs.field_types` gives that column.
    """

    #############################
    ### OVERRIDE FROM ObsBase ###
    #############################


    @property
    def instrument_id(self) -> str | None:
        """The OPUS instrument id, ``VGISS``."""
        return 'VGISS'

    def opus_id_from_supp_index_row(self, supp_row: IndexRow) -> str | None:
        """Return the OPUS id a supplemental index row describes.

        The supplemental index for these volumes names the volume in a different column
        from
        every other index, which is why this exists alongside
        `opus_import.obs.obs_base.ObsBase.opus_id_from_index_row`.

        Parameters:
            supp_row: The supplemental index row to read.

        Returns:
            The OPUS id, or the file's own name if ``pdsfile`` could not derive one, which
            is logged as an error.
        """
        bundle_id = supp_row['VOLUME_NAME']
        filespec = supp_row['FILE_SPECIFICATION_NAME']
        full_filespec = bundle_id + '/' + filespec
        pdsf = self._pdsfile_from_filespec(full_filespec)
        opus_id = pdsf.opus_id
        if not opus_id:
            self._log_nonrepeating_error(
                        'Unable to create OPUS_ID from supplemental index')
            return cast(str | None, filespec.split('/')[-1])
        return cast(str | None, opus_id)

    def convert_filespec_from_lbl(self, filespec: str) -> str:
        """Convert a ``.LBL`` file specification to the ``.IMG`` data file.

        Parameters:
            filespec: The path, relative to the holdings root.

        Returns:
            The same path with ``.LBL`` replaced by ``.IMG``, which is the file
            this bundle's observations are identified by.
        """
        return filespec.replace('.LBL', '.IMG')


    ################################
    ### OVERRIDE FROM ObsGeneral ###
    ################################

    def field_obs_general_observation_duration(self) -> FloatField:
        exposure = self._index_col('EXPOSURE_DURATION')
        if exposure is None or exposure < 0:
            # There's one exposure somewhere that has duration -0.09999
            return None
        return cast(FloatField, exposure)

    def field_obs_general_right_asc1(self) -> FloatField:
        return self._ring_geo_index_col('MINIMUM_RIGHT_ASCENSION')

    def field_obs_general_right_asc2(self) -> FloatField:
        return self._ring_geo_index_col('MAXIMUM_RIGHT_ASCENSION')

    def field_obs_general_declination1(self) -> FloatField:
        return self._ring_geo_index_col('MINIMUM_DECLINATION')

    def field_obs_general_declination2(self) -> FloatField:
        return self._ring_geo_index_col('MAXIMUM_DECLINATION')

    def field_obs_general_ring_obs_id(self) -> StrField:
        filename = self._index_col('PRODUCT_ID')
        image_num = filename[1:8]
        inst_host_num = self._index_col('INSTRUMENT_HOST_NAME')[-1]
        camera = self._index_col('INSTRUMENT_NAME')[0]
        planet = self._planet_id()
        if planet is None:
            pl_str = ''
        else:
            pl_str = planet[0]

        return f'{pl_str}_IMG_VG{inst_host_num}_ISS_{image_num}_{camera}'

    def field_obs_general_quantity(self) -> MultFieldRet:
        filter_name = self._index_col('FILTER_NAME')
        if filter_name == 'UV':
            return self._create_mult('EMISSION')
        return self._create_mult('REFLECT')

    def field_obs_general_observation_type(self) -> MultFieldRet:
        return self._create_mult('IMG')


    ############################
    ### OVERRIDE FROM ObsPds ###
    ############################

    def field_obs_pds_note(self) -> StrField:
        return cast(StrField, self._index_col('NOTE'))


    ##################################
    ### OVERRIDE FROM ObsTypeImage ###
    ##################################

    def field_obs_type_image_image_type_id(self) -> MultFieldRet:
        return self._create_mult('FRAM')

    def field_obs_type_image_duration(self) -> FloatField:
        return self.field_obs_general_observation_duration()

    def field_obs_type_image_levels(self) -> IntField:
        return EIGHT_BIT_IMAGE_LEVELS

    def _vgiss_pixel_size_helper(self) -> tuple[int, int]:
        """Return the two dimensions of the image, in pixels.

        Returns:
            The number of lines and the number of samples, from the window the
            supplemental
            index records.
        """
        line1 = self._supp_index_col('FIRST_LINE')
        line2 = self._supp_index_col('LAST_LINE')
        sample1 = self._supp_index_col('FIRST_SAMPLE')
        sample2 = self._supp_index_col('LAST_SAMPLE')
        # int() because the index columns arrive from numpy, which does not subclass
        # int; see opus_import.obs.field_types.as_int.
        return int(line2-line1+1), int(sample2-sample1+1)

    def field_obs_type_image_greater_pixel_size(self) -> IntField:
        pix1, pix2 = self._vgiss_pixel_size_helper()
        return max(pix1, pix2)

    def field_obs_type_image_lesser_pixel_size(self) -> IntField:
        pix1, pix2 = self._vgiss_pixel_size_helper()
        return min(pix1, pix2)


    ###################################
    ### OVERRIDE FROM ObsWavelength ###
    ###################################

    def _vgiss_wavelength_helper(self) -> tuple[int, int] | None:
        """Look up this observation's filter wavelengths.

        Returns:
            The minimum and maximum wavelength in nanometres, or None for a filter this
            pipeline does not describe, which is logged as an error.
        """
        filter_name = self._index_col('FILTER_NAME')
        if filter_name not in _VGISS_FILTER_WAVELENGTHS:
            self._log_nonrepeating_error(f'Unknown VGISS filter name "{filter_name}"')
            return None
        return _VGISS_FILTER_WAVELENGTHS[filter_name]

    def field_obs_wavelength_wavelength1(self) -> FloatField:
        wavelengths = self._vgiss_wavelength_helper()
        if wavelengths is None:
            return None
        return wavelengths[0] / 1000 # microns

    def field_obs_wavelength_wavelength2(self) -> FloatField:
        wavelengths = self._vgiss_wavelength_helper()
        if wavelengths is None:
            return None
        return wavelengths[1] / 1000 # microns

    def field_obs_wavelength_wave_res1(self) -> FloatField:
        return self._wave_res_from_full_bandwidth()

    def field_obs_wavelength_wave_res2(self) -> FloatField:
        return self.field_obs_wavelength_wave_res1()

    def field_obs_wavelength_wave_no_res1(self) -> FloatField:
        return self._wave_no_res_from_full_bandwidth()

    def field_obs_wavelength_wave_no_res2(self) -> FloatField:
        return self.field_obs_wavelength_wave_no_res1()


    ############################################
    ### OVERRIDE FROM ObsVolumeVoyagerCommon ###
    ############################################

    def _mission_phase_name(self) -> str | None:
        """Return the mission phase this observation belongs to.

        Returns:
            The phase the index records, which these volumes carry as a column.
        """
        return cast(str | None, self._index_col('MISSION_PHASE_NAME'))

    def field_obs_mission_voyager_mission_phase_name(self) -> MultFieldRet:
        return self._create_mult(self._mission_phase_name())


    ##############################################
    ### FIELD METHODS FOR obs_instrument_vgiss ###
    ##############################################

    def field_obs_instrument_vgiss_opus_id(self) -> StrField:
        return self.opus_id

    def field_obs_instrument_vgiss_bundle_id(self) -> StrField:
        return self.bundle

    def field_obs_instrument_vgiss_image_id(self) -> StrField:
        return cast(StrField, self._index_col('IMAGE_ID'))

    def field_obs_instrument_vgiss_scan_mode(self) -> MultFieldRet:
        return self._create_mult(self._index_col('SCAN_MODE'))

    def field_obs_instrument_vgiss_shutter_mode(self) -> MultFieldRet:
        return self._create_mult(self._index_col('SHUTTER_MODE'))

    def field_obs_instrument_vgiss_gain_mode(self) -> MultFieldRet:
        return self._create_mult(self._index_col('GAIN_MODE'))

    def field_obs_instrument_vgiss_edit_mode(self) -> MultFieldRet:
        return self._create_mult(self._index_col('EDIT_MODE'))

    def field_obs_instrument_vgiss_filter_name(self) -> MultFieldRet:
        return self._create_mult(self._index_col('FILTER_NAME'))

    def field_obs_instrument_vgiss_filter_number(self) -> MultFieldRet:
        # as_int because the labels declare this column ASCII_INTEGER, so it arrives as
        # a numpy integer, which is not an `int`; see field_types.as_int.
        return self._create_mult(as_int(self._index_col('FILTER_NUMBER')))

    def field_obs_instrument_vgiss_camera(self) -> MultFieldRet:
        camera = self._index_col('INSTRUMENT_NAME')
        assert camera in ['NARROW ANGLE CAMERA', 'WIDE ANGLE CAMERA']
        return self._create_mult(camera[0])

    def field_obs_instrument_vgiss_usable_lines(self) -> IntField:
        line1 = self._supp_index_col('FIRST_LINE')
        line2 = self._supp_index_col('LAST_LINE')
        return as_int(line2-line1+1)

    def field_obs_instrument_vgiss_usable_samples(self) -> IntField:
        sample1 = self._supp_index_col('FIRST_SAMPLE')
        sample2 = self._supp_index_col('LAST_SAMPLE')
        return as_int(sample2-sample1+1)
