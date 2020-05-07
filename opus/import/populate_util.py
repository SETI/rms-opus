################################################################################
# populate_util.py
#
# General routines that are common to many instruments.
################################################################################

import julian

import import_util

def _time1_helper(index, column, **kwargs):
    metadata = kwargs['metadata']
    index_row = metadata[index]
    start_time = import_util.safe_column(index_row, column)

    if start_time is None:
        return None

    try:
        start_time_sec = julian.tai_from_iso(start_time)
    except Exception as e:
        import_util.log_nonrepeating_error(
            f'Bad start time format "{start_time}": {e}')
        return None

    return start_time_sec

def populate_time1_from_index(column='START_TIME', **kwargs):
    return _time1_helper('index_row', column, **kwargs)

def populate_time1_from_supp_index(column='START_TIME', **kwargs):
    return _time1_helper('supp_index_row', column, **kwargs)

def _time2_helper(index, column1, column2, **kwargs):
    metadata = kwargs['metadata']
    index_row = metadata[index]
    stop_time = import_util.safe_column(index_row, column2)

    if stop_time is None:
        return None

    try:
        stop_time_sec = julian.tai_from_iso(stop_time)
    except Exception as e:
        import_util.log_nonrepeating_error(
            f'Bad stop time format "{stop_time}": {e}')
        return None

    general_row = metadata['obs_general_row']
    start_time_sec = general_row['time1']

    if start_time_sec is not None and stop_time_sec < start_time_sec:
        start_time = import_util.safe_column(index_row, column1)
        import_util.log_warning(f'time1 ({start_time}) and time2 ({stop_time}) '
                                f'are in the wrong order - setting to time1')
        stop_time_sec = start_time_sec

    return stop_time_sec

def populate_time2_from_index(column1='START_TIME',
                              column2='STOP_TIME',
                              **kwargs):
    return _time2_helper('index_row', column1, column2, **kwargs)

def populate_time2_from_supp_index(column1='START_TIME',
                                   column2='STOP_TIME',
                                   **kwargs):
    return _time2_helper('supp_index_row', column1, column2, **kwargs)

def populate_observation_duration_from_time(**kwargs):
    metadata = kwargs['metadata']
    general_row = metadata['obs_general_row']
    start_time_sec = general_row['time1']
    stop_time_sec = general_row['time2']

    if start_time_sec is None or stop_time_sec is None:
        return None

    return max(stop_time_sec - start_time_sec, 0)

def _product_creation_time_helper(index, **kwargs):
    metadata = kwargs['metadata']
    index_row = metadata[index]
    pct = index_row['PRODUCT_CREATION_TIME']

    try:
        pct_sec = julian.tai_from_iso(pct)
    except Exception as e:
        import_util.log_nonrepeating_error(
            f'Bad product creation time format "{pct}": {e}')
        return None

    return pct_sec

def populate_product_creation_time_from_index(**kwargs):
    return _product_creation_time_helper('index_row', **kwargs)

def populate_product_creation_time_from_index_label(**kwargs):
    return _product_creation_time_helper('index_label', **kwargs)

def populate_product_creation_time_from_supp_index(**kwargs):
    return _product_creation_time_helper('supp_index_row', **kwargs)

def _data_set_id_helper(index, **kwargs):
    metadata = kwargs['metadata']
    index_label = metadata[index]
    dsi = index_label['DATA_SET_ID']
    return (dsi, dsi)

def populate_data_set_id_from_index(**kwargs):
    return _data_set_id_helper('index_row', **kwargs)

def populate_data_set_id_from_index_label(**kwargs):
    return _data_set_id_helper('index_label', **kwargs)

def populate_data_set_id_from_supp_index(**kwargs):
    return _data_set_id_helper('supp_index_row', **kwargs)

def populate_product_id_from_index(**kwargs):
    metadata = kwargs['metadata']
    index_row = metadata['index_row']
    product_id = index_row['PRODUCT_ID']

    return product_id

def populate_product_id_from_supp_index(**kwargs):
    metadata = kwargs['metadata']
    supp_index_row = metadata.get('supp_index_row', None)
    if supp_index_row is None: # Needed for UVIS?
        return None
    product_id = supp_index_row['PRODUCT_ID']

    return product_id
