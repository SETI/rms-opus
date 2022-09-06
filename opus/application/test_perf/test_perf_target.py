# Test the performance of searching by Intended Target Name and returning metadata for
# Intended Target Name.

import random
import time
import urllib.request
import urllib.parse

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

def run_one_test(search_params, columns, num_iterations, randomize_search=False):
    """Run one test multiple times and collect statistics."""
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
            min = random.randint(0, 59)
            sec = random.randint(0, 59)
            start_time = f'{yr:04d}-{month:02d}-{day:02d}T{hr:02d}:{min:02d}:{sec:02d}.'
            start_time += f'{iteration:03d}'
            presearch_params = f'time1={start_time}&'
        url = f'{HOST}/api/data.json?{presearch_params}{search_params}'
        url += f'&cols={columns}&limit=10000'
        # print(url)
        start_time = time.time()
        with urllib.request.urlopen(url) as response:
            html = response.read()
            # print(html)
            end_time = time.time()
            time_list.append(end_time-start_time)
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
