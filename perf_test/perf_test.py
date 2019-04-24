# TODO: Once startobs branch is merged, add __dummy.[fmt] to test_return_formats

import numpy as np
import requests
import time

URL_PREFIX = 'http://127.0.0.1:8000/opus'
MAX_TIME = 10.

DUMMY_MAX_ITERS = 100
DUMMY_MIN_ITERS = 10

STD_TOLERANCE = 0.05 # Iterate until std stabilizes within 5%

def run_one(session, url_factory):
    "Run one server query and return how long it took."
    url, params = url_factory.__next__()
    time1 = time.time()
    r = session.get(url, params=params)
    time2 = time.time()

    if r.status_code != 200:
        assert False

    return time2-time1

def statistical_run(session, url_factory, max_time, min_iters, max_iters):
    # Always treat the first one differently because there might be
    # server startup or cache effects
    initial_time = run_one(session, url_factory)

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
        if num_times >= 3 and num_times >= min_iters:
            old_std = np.std(time_list[:-1])
            new_std = np.std(time_list)
            if abs(new_std-old_std)/old_std <= STD_TOLERANCE:
                break

    return initial_time, np.mean(time_list), np.std(time_list), len(time_list)


def run_dummy(max_time, min_iters, max_iters):
    def dummy_url_factory():
        url = URL_PREFIX + '/__dummy.json'
        while True:
            yield url, {'ignorelog': 1}

    session = requests.Session()

    url_factory = dummy_url_factory()

    ret = statistical_run(session, url_factory, max_time, min_iters, max_iters)
    return ret

ret = run_dummy(MAX_TIME, DUMMY_MIN_ITERS, DUMMY_MAX_ITERS)
overhead_initial, overhead_mean, overhead_std, overhead_len = ret
print(ret)
