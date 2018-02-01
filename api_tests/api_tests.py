# -*- coding: utf-8 -*-
import sys
import unittest
import json
import requests
import csv

filename = 'result_counts.csv'
endpoint_url = "https://{}.pds-rings.seti.org/opus/api/meta/result_count.json?"

class APIEndpointTests(unittest.TestCase):

    def __init__(self, server_name):

        # which endpoint to test, dev or tools
        self.API_ENDPOINT = endpoint_url.format('dev')
        if 'tools' in server_name:
            self.API_ENDPOINT = endpoint_url.format('tools')

        # ignore SSL errors when contacting dev server  ¯\_(ツ)_/¯
        self.verify = True
        if 'dev' in self.API_ENDPOINT:
            self.verify = False

    def test_all_the_things_in_loop(self):

        count = 0
        with open(filename, 'rb') as csvfile:

            filereader = csv.reader(csvfile)
            for row in filereader:

                q_str, expected, info = row

                url_hash = q_str.split('#/')[1].strip()
                api_url = self.API_ENDPOINT + url_hash

                data = json.loads(requests.get(api_url, verify=self.verify).text)

                result_count = data['data'][0]['result_count']

                msg = """checking: \n{}
                          result: expected >= {} :: got: {} \n
                      """.format(api_url, expected, result_count)

                print(msg)

                try:
                    assert result_count >= int(expected)
                except AssertionError:
                    raise AssertionError(msg)

                count = count+1

        print "\n ALL TESTS PASS WOOT! \n Actual Number of Tests Run: %s " % str(count)

if __name__ == '__main__':
    server_name = raw_input("dev or prod server?")
    my_tests = APIEndpointTests(server_name)
    my_tests.test_all_the_things_in_loop()
