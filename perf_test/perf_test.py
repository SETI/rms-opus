# TODO: Once startobs branch is merged, add __dummy.[fmt] to test_return_formats

import numpy as np
import random
import requests
import sys
import time

# URL_PREFIX = 'http://127.0.0.1:8000/opus'
# DEFAULT_URL_PARAMS = {'ignorelog': 1}

URL_PREFIX = 'https://tools.pds-rings.seti.org/opus'
DEFAULT_URL_PARAMS = {}

# MAX_TIME = 10.
# MIN_ITERS = 2
# MAX_ITERS = 2
MAX_TIME = 600.
MIN_ITERS = 3
MAX_ITERS = 10
DUMMY_MIN_ITERS = 10
DUMMY_MAX_ITERS = 100

STD_TOLERANCE = 0.05 # Iterate until std stabilizes within 5%

CACHED_PARAMS = {}

def run_one(session, url_factory):
    "Run one server query and return how long it took."
    url, params = url_factory.__next__()
    time1 = time.time()
    r = session.get(url, params=params)
    time2 = time.time()

    if r.status_code != 200:
        print(url)
        print(r.status_code)
        return 0.

    return time2-time1

def statistical_run(session, url_factory, max_time, min_iters, max_iters):
    time_list = []
    num_times = 0 # Just so we don't call len() all the time
    while True:
        run_time = run_one(session, url_factory)
        time_list.append(run_time)
        num_times += 1
        if num_times == max_iters:
            break
        if np.sum(time_list) >= max_time:
            break
        if num_times >= 4 and num_times >= min_iters:
            old_std = np.std(time_list[1:-1])
            new_std = np.std(time_list[1:])
            if abs(new_std-old_std)/old_std <= STD_TOLERANCE:
                break

    return (time_list[0], np.mean(time_list[1:]), np.std(time_list[1:]),
            len(time_list[1:]))


def run_dummy(max_time, min_iters, max_iters):
    def _url_factory():
        url = URL_PREFIX + '/__dummy.json'
        while True:
            params = DEFAULT_URL_PARAMS
            yield url, params

    session = requests.Session()

    url_factory = _url_factory()

    ret = statistical_run(session, url_factory, max_time, min_iters, max_iters)
    return ret


def run_result_count_helper(key, base_params, max_time, min_iters, max_iters):
    def _url_factory():
        url = URL_PREFIX + '/api/meta/result_count.json'
        for params in CACHED_PARAMS[key]:
            yield url, params

    # We cache the params we generate here because each URL is unique and
    # actually doing that initial search can be really slow on the server.
    # Later when we want to do other things with the same basic search, if
    # we use the param list we cached here, the server doesn't have to do that
    # big initial search and we can just benchmark the incremental work we're
    # asking it to do.
    param_list = []
    CACHED_PARAMS[key] = param_list
    for i in range(max_iters):
        params = DEFAULT_URL_PARAMS.copy()
        params.update(base_params)
        # To get a unique search that includes all the results, we use
        # a large random negative number for observationduration1
        observationduration1 = random.uniform(-1000000., -1.)
        params['observationduration1'] = observationduration1
        param_list.append(params)

    session = requests.Session()

    url_factory = _url_factory()

    ret = statistical_run(session, url_factory, max_time, min_iters, max_iters)
    return ret

def run_result_count_1_table(max_time, min_iters, max_iters):
    return run_result_count_helper(
        'result_count_1_table',
        {},
        max_time, min_iters, max_iters)

def run_result_count_1_table_sort(max_time, min_iters, max_iters):
    return run_result_count_helper(
        'result_count_1_table_sort',
        {'order': 'target,instrument,-rightasc1,observationduration,opusid'},
        max_time, min_iters, max_iters)

def run_result_count_2_table(max_time, min_iters, max_iters):
    return run_result_count_helper(
        'result_count_2_table',
        {'datasetid': 'XYZXYZXYZ', # Join obs_pds
         'qtype-datasetid': 'excludes'},
        max_time, min_iters, max_iters)

def run_result_count_2_table_sort(max_time, min_iters, max_iters):
    return run_result_count_helper(
        'result_count_2_table_sort',
        {'order': 'target,instrument,-rightasc1,observationduration,opusid',
         'datasetid': 'XYZXYZXYZ', # Join obs_pds
         'qtype-datasetid': 'excludes'},
        max_time, min_iters, max_iters)

def run_result_count_3_table(max_time, min_iters, max_iters):
    return run_result_count_helper(
        'result_count_3_table',
        {'datasetid': 'XYZXYZXYZ', # Join obs_pds
         'qtype-datasetid': 'excludes',
         'duration1': '0.'}, # Join obs_type_image
        max_time, min_iters, max_iters)

def run_result_count_3_table_sort(max_time, min_iters, max_iters):
    return run_result_count_helper(
        'result_count_3_table_sort',
        {'order': 'target,instrument,-rightasc1,observationduration,opusid',
         'datasetid': 'XYZXYZXYZ', # Join obs_pds
         'qtype-datasetid': 'excludes',
         'duration1': '0.'}, # Join obs_type_image
        max_time, min_iters, max_iters)
    return ret

def run_result_count_4_table(max_time, min_iters, max_iters):
    return run_result_count_helper(
        'result_count_4_table',
        {'datasetid': 'XYZXYZXYZ', # Join obs_pds
         'qtype-datasetid': 'excludes',
         'duration1': '0.', # Join obs_type_image
         'wavelength1': '0.'}, # Join obs_wavelength
        max_time, min_iters, max_iters)

def run_result_count_4_table_sort(max_time, min_iters, max_iters):
    return run_result_count_helper(
        'result_count_4_table_sort',
        {'order': 'target,instrument,-rightasc1,observationduration,opusid',
         'datasetid': 'XYZXYZXYZ', # Join obs_pds
         'qtype-datasetid': 'excludes',
         'duration1': '0.', # Join obs_type_image
         'wavelength1': '0.'}, # Join obs_wavelength
        max_time, min_iters, max_iters)

def run_dataimages_helper(key, base_params, max_time, min_iters, max_iters):
    def _url_factory():
        url = URL_PREFIX + '/__api/dataimages.json'
        for params in CACHED_PARAMS[key]:
            yield url, params

    # We cache the params we generate here because each URL is unique and
    # actually doing that initial search can be really slow on the server.
    # Later when we want to do other things with the same basic search, if
    # we use the param list we cached here, the server doesn't have to do that
    # big initial search and we can just benchmark the incremental work we're
    # asking it to do.
    param_list = []
    CACHED_PARAMS[key] = param_list
    for i in range(max_iters):
        params = DEFAULT_URL_PARAMS.copy()
        params.update(base_params)
        params['startobs'] = 1291
        params['limit'] = 100
        params['reqno'] = 1
        param_list.append(params)

    session = requests.Session()

    url_factory = _url_factory()

    ret = statistical_run(session, url_factory, max_time, min_iters, max_iters)
    return ret

def run_dataimages_1_table(max_time, min_iters, max_iters):
    return run_dataimages_helper(
        'result_count_1_table_sort',
        {'cols': 'time1'}, # obs_general
        max_time, min_iters, max_iters)

def run_dataimages_2_table(max_time, min_iters, max_iters):
    return run_dataimages_helper(
        'result_count_1_table_sort',
        {'cols': 'time1,volumeid'}, # Add obs_pds
        max_time, min_iters, max_iters)

def run_dataimages_3_table(max_time, min_iters, max_iters):
    return run_dataimages_helper(
        'result_count_1_table_sort',
        {'cols': 'time1,volumeid,greaterpixelsize'}, # Add obs_type_image
        max_time, min_iters, max_iters)

def run_dataimages_4_table(max_time, min_iters, max_iters):
    return run_dataimages_helper(
        'result_count_1_table_sort',
        {'cols': 'time1,volumeid,greaterpixelsize,waveno1'}, # Add obs_wavelength
        max_time, min_iters, max_iters)

def run_dataimages_6_table(max_time, min_iters, max_iters):
    return run_dataimages_helper(
        'result_count_1_table_sort',
        {'cols': 'time1,volumeid,greaterpixelsize,waveno1,CASSINIprimeinst,'
                +'COISSmissinglines'}, # Add obs_mission_cassini and
                                          # obs_instrument_coiss
        max_time, min_iters, max_iters)

def run_dataimages_8_table(max_time, min_iters, max_iters):
    return run_dataimages_helper(
        'result_count_1_table_sort',
        {'cols': 'time1,volumeid,greaterpixelsize,waveno1,CASSINIprimeinst,'
                +'COISSmissinglines,SURFACEGEOsaturnrangetobody1,'
                +'SURFACEGEOenceladusrangetobody1'}, # Add surfacegeo_saturn
                                                     # and surfacegeo_enceladus
        max_time, min_iters, max_iters)


ret = run_dummy(
        MAX_TIME, DUMMY_MIN_ITERS, DUMMY_MAX_ITERS)
overhead_initial, overhead_mean, overhead_std, overhead_len = ret

BENCHMARK_FUNCS = (
    (run_result_count_1_table,
     'result_count 1 table '),
    (run_result_count_2_table,
     'result_count 2 tables'),
    (run_result_count_3_table,
     'result_count 3 tables'),
    (run_result_count_4_table,
     'result_count 4 tables'),
    (run_result_count_1_table_sort,
     'result_count 1 table  w/sort'),
    (run_result_count_2_table_sort,
     'result_count 2 tables w/sort'),
    (run_result_count_3_table_sort,
     'result_count 3 tables w/sort'),
    (run_result_count_4_table_sort,
     'result_count 4 tables w/sort'),
    (run_dataimages_1_table,
     'dataimages 1 table '),
    (run_dataimages_2_table,
     'dataimages 2 tables'),
    (run_dataimages_3_table,
     'dataimages 3 tables'),
    (run_dataimages_4_table,
     'dataimages 4 tables'),
    (run_dataimages_6_table,
     'dataimages 6 tables'),
    (run_dataimages_8_table,
     'dataimages 8 tables'),
)

results = []

for func, title in BENCHMARK_FUNCS:
    print(f'Running {title}... ', end='')
    sys.stdout.flush()
    ret = func(MAX_TIME, MIN_ITERS, MAX_ITERS)
    results.append((title, ret))
    print(f'{ret[1]:7.3f}')

print()
print(f'{"Test":40s}  Mean      Std    #')

for title, ret in results:
    initial, mean, std, len = ret
    real_mean = mean-overhead_initial
    print(f'{title:40s}{real_mean:7.3f} +/- {std:5.3f} ({len})')
