import unittest
import json
import requests
import csv
from config import API_ENDPOINT

filename = 'result_counts.csv'

class APIEndpointTests(unittest.TestCase):

    def test_all_the_things_in_loop(self):

        count = 0
        with open(filename, 'rb') as csvfile:

            filereader = csv.reader(csvfile)
            for row in filereader:

                q_str, expected, info = row

                url_hash = q_str.split('#/')[1].strip()
                api_url = API_ENDPOINT + url_hash

                data = json.loads(requests.get(api_url).text)

                result_count = data['data'][0]['result_count']

                msg = "\n\n checking url: %s \n expected >= %s \n got: %s" % (api_url, expected, result_count)
                # print msg

                try:
                    assert result_count >= int(expected)
                except AssertionError:
                    raise AssertionError(msg)

                count = count+1

        print "\n ALL TESTS PASS WOOT! \n Actual Number of Tests Run: %s " % str(count)

if __name__ == '__main__':
    unittest.main()
