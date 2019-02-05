# opus/application/test_api/api_test_helper.py

import json
import requests

import settings

_RESPONSES_FILE_ROOT = 'test_api/responses/'

class ApiTestHelper:
    def _get_response(self, url):
        if not settings.TEST_GO_LIVE or settings.TEST_GO_LIVE == "production":
            url = "https://tools.pds-rings.seti.org" + url
        else:
            url = "http://dev.pds-rings.seti.org" + url
        return self.client.get(url)

    def _run_status_equal(self, url, expected, err_string=None):
        print(url)
        response = self._get_response(url)
        self.assertEqual(response.status_code, expected)
        # XXX Fix this once we have a proper 404 page
        # if err_string:
        #     print(response.content)
        #     self.assertEqual(response.content, err_string)

    def _run_json_equal(self, url, expected):
        print(url)
        response = self._get_response(url)
        self.assertEqual(response.status_code, 200)
        jdata = json.loads(response.content)
        print('Got:')
        print(jdata)
        print('Expected:')
        print(expected)
        self.assertEqual(expected, jdata)

    def _run_json_equal_file(self, url, exp_file):
        with open(_RESPONSES_FILE_ROOT+exp_file, 'r') as fp:
            expected = json.loads(fp.read())
        print(url)
        response = self._get_response(url)
        self.assertEqual(response.status_code, 200)
        jdata = json.loads(response.content)
        print('Got:')
        print(jdata)
        print('Expected:')
        print(expected)
        self.assertEqual(expected, jdata)

    def _run_html_equal(self, url, expected):
        print(url)
        response = self._get_response(url)
        self.assertEqual(response.status_code, 200)
        expected = str(expected)[2:-1].replace('\r', '')
        resp = str(response.content)[2:-1].replace('\r', '')[:len(expected)]
        print('Got:')
        print(resp)
        print('Expected:')
        print(expected)
        self.assertEqual(expected, resp)

    def _run_html_equal_file(self, url, exp_file):
        with open(_RESPONSES_FILE_ROOT+exp_file, 'rb') as fp:
            expected = fp.read()
        print(url)
        response = self._get_response(url)
        self.assertEqual(response.status_code, 200)
        expected = str(expected)[2:-1].replace('\r', '')
        resp = str(response.content)[2:-1].replace('\r', '')[:len(expected)]
        print('Got:')
        print(resp)
        print('Expected:')
        print(expected)
        self.assertEqual(expected, resp)

    def _run_html_startswith(self, url, expected):
        print(url)
        response = self._get_response(url)
        self.assertEqual(response.status_code, 200)
        # Strip off b'...''
        expected = str(expected)[2:-1].replace('\r', '')
        resp = str(response.content)[2:-1].replace('\r', '')[:len(expected)]
        print('Got:')
        print(resp)
        print('Expected:')
        print(expected)
        self.assertEqual(expected, resp)

    def _run_csv_equal(self, url, expected):
        print(url)
        response = self._get_response(url)
        self.assertEqual(response.status_code, 200)
        expected = str(expected)[2:-1].replace('\r', '')
        resp = str(response.content)[2:-1].replace('\r', '')[:len(expected)]
        print('Got:')
        print(resp)
        print('Expected:')
        print(expected)
        self.assertEqual(expected, resp)

    def _run_csv_equal_file(self, url, exp_file):
        with open(_RESPONSES_FILE_ROOT+exp_file, 'rb') as fp:
            expected = fp.read()
        print(url)
        response = self._get_response(url)
        self.assertEqual(response.status_code, 200)
        expected = str(expected)[2:-1].replace('\r', '')
        resp = str(response.content)[2:-1].replace('\r', '')[:len(expected)]
        print('Got:')
        print(resp)
        print('Expected:')
        print(expected)
        self.assertEqual(expected, resp)
