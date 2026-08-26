"""Time a target search and the metadata fetch for its results.

Hand-run against a server started separately; it is not a test the suite
collects, and its name is what the directory it sits in calls it rather than
a claim that `pytest` should pick it up.
"""

import random
import time
import urllib.parse
import urllib.request

import numpy as np

HOST = 'http://127.0.0.1:8000'

TARGET_LIST = [
    'Jupiter',         # 89973
    'Saturn',          # 412035
    'Saturn Rings',    # 317258
    'Titan',           # 197325
    'Jupiter,Saturn',  # 502008
    'Saturn,Saturn Rings',
    'Jupiter,Saturn,Saturn Rings,Titan',
    # 'Atlas,Calypso,Daphnis,Dione,Enceladus,Epimetheus,Helene,Hyperion,Hyrrokkin,Iapetus,Pandora,Pan,Pallene,Mimas,Methone,Janus,Phoebe,Polydeuces,Prometheus,Rhea,Saturn,Titan,Tethys,Telesto,Saturn+Rings,Io,Adrastea,Amalthea,Jupiter,Jupiter+Rings,Callisto,Europa,Thebe,Ganymede',
]

def run_one_test(search_params: str, columns: str, num_iterations: int,
                 randomize_search: bool = False) -> None:
    """Run one test multiple times and collect statistics.

    Parameters:
        search_params: Query string selecting the observations to search for,
            without a leading or trailing separator.
        columns: Comma-separated metadata columns to return.
        num_iterations: How many times to issue the request. With more than one and
            no randomization the first result is discarded, because it is the one
            that primed the cache.
        randomize_search: Prefix each request with a distinct random start time, so
            that successive requests are not answered from the cache.
    """
    # We have to randomize the starting date to avoid the search results being cached
    # from run to run
    time_list = []
    for iteration in range(num_iterations):
        presearch_params = ''
        if randomize_search:
            yr = random.randint(1900, 1970)
            month = random.randint(1, 12)
            day = random.randint(1, 28)
            hr = random.randint(0, 23)
            minute = random.randint(0, 59)
            sec = random.randint(0, 59)
            search_start = f'{yr:04d}-{month:02d}-{day:02d}T{hr:02d}:{minute:02d}:{sec:02d}.'
            search_start += f'{iteration:03d}'
            presearch_params = f'time1={search_start}&'
        url = f'{HOST}/api/data.json?{presearch_params}{search_params}'
        url += f'&cols={columns}&limit=10000'
        # print(url)
        request_start = time.time()
        with urllib.request.urlopen(url) as response:
            response.read()
            end_time = time.time()
            time_list.append(end_time-request_start)
    if not randomize_search and num_iterations > 1:
        # Throw away the first result because that was just priming the cache
        del time_list[0]

    print(f'{np.mean(time_list):7.3f} +/- {np.std(time_list):7.3f}')

print('--- Target search tests (1 run)')

for test_num, target in enumerate(TARGET_LIST):
    print(f'{test_num+1:3d}: ', end='')
    run_one_test(f'target={urllib.parse.quote(target)}', 'opusid', 1,
                 randomize_search=False)

print('--- Target search + time tests (10 runs)')

for test_num, target in enumerate(TARGET_LIST):
    print(f'{test_num+1:3d}: ', end='')
    run_one_test(f'target={urllib.parse.quote(target)}', 'opusid', 10,
                 randomize_search=True)

print('--- Target metadata test')
run_one_test('', 'opusid,target', 10, randomize_search=False)
