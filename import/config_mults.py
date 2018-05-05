################################################################################
# mult_config.py
#
# mult_obs_<table>_<field> tables are used to store the possible values for
# each field in a table that has form type "GROUP". For most such tables,
# the mult_ tables are created and updated dynamically as new values are found.
# In this case, the mult_ value [from the field] and the display label are the
# same, and they are sorted in alphabetical order.
#
# However, some tables rarely change and have labels that differ from the
# raw database field value [for example display "Yes" instead of "Y"].
# These tables are defined by hand here, and if a value ever needs to be added,
# this file has to be edited by hand before import can proceed.
################################################################################

# Fields are:
#   Unique id [used by Django]
#   Data value as found in the obs_ table field
#   Label to display in the OPUS GUI
#   Display order
#   Whether to display or not

PREPROGRAMMED_MULT_TABLE_CONTENTS = {

    ### OBS_GENERAL ###
        #
        # "mult_obs_general_instrument_id":
        # "mult_obs_general_mission_id":
        # "mult_obs_general_inst_host_id":
        # "mult_obs_general_data_type":
        # "mult_obs_general_planet_id":
        # "mult_obs_general_target_class":
        # "mult_obs_general_quantity":
        #
        # ### OBS_TYPE_IMAGE ###
        #
        # "mult_obs_type_image_image_type_id":
        #
        # ### OBS_WAVELENGTH ###
        #
        # "mult_obs_wavelength_polarization_type":
        #
        # ### OBS_MISSION_CASSINI ###
        #
        # "mult_obs_mission_cassini_prime_inst_id":
        #
        # ### OBS_INSTRUMENT_COISS ###
        #
        # "mult_obs_instrument_coiss_data_conversion_type":
        # "mult_obs_instrument_coiss_gain_mode_id": ,
        # "mult_obs_instrument_image_observation_type":
        # "mult_obs_instrument_coiss_shutter_mode_id":
        # "mult_obs_instrument_coiss_shutter_state_id":
        # "mult_obs_instrument_coiss_instrument_mode_id":
        # "mult_obs_instrument_coiss_camera":
        #
        # ### OBS_INSTRUMENT_COUVIS ###
        #
        # "mult_obs_instrument_couvis_observation_type":
        # "mult_obs_instrument_couvis_compression_type":
        # "mult_obs_instrument_couvis_occultation_port_state":
        # "mult_obs_instrument_couvis_slit_state":
        # "mult_obs_instrument_couvis_channel":
        #
        # ### OBS_INSTRUMENT_COVIMS ###
        #
        # "mult_obs_instrument_covims_instrument_mode_id":
        # "mult_obs_instrument_covims_ir_sampling_mode_id":
        # "mult_obs_instrument_covims_vis_sampling_mode_id":
        # "mult_obs_instrument_covims_channel":
        #
        # ### OBS_INSTRUMENT_GOSSI ###
        #
        # "mult_obs_instrument_gossi_filter_name":
        # "mult_obs_instrument_gossi_gain_mode_id":
        # "mult_obs_instrument_gossi_obstruction_id":
        # "mult_obs_instrument_gossi_compression_type":
        #
        # ### OBS_MISSION_HUBBLE ###
        #
        # "mult_obs_mission_hubble_detector_id":
        # "mult_obs_mission_hubble_fine_guidance_system_lock_type":
        # "mult_obs_mission_hubble_gain_mode_id":
        # "mult_obs_mission_hubble_instrument_mode_id":
        # "mult_obs_mission_hubble_targeted_detector_id":


    ### OBS_MISSION_VOYAGER ###
    # 
    # "mult_obs_mission_voyager_spacecraft_name": [
    #     [   0, "VG1", "Voyager 1",   10, "Y", null],
    #     [   1, "VG2", "Voyager 2",   20, "Y", null],
    # ],
    #
    # ### OBS_INSTRUMENT_VGISS ###
    #
    # "mult_obs_instrument_vgiss_camera": [
    #     [   0, "N", "Narrow Angle",   10, "Y", null],
    #     [   1, "W",   "Wide Angle",   20, "Y", null],
    # ],
}
