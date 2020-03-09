# opus/application/test_api/api_test_helper.py

import json

import settings

_RESPONSES_FILE_ROOT = 'test_api/responses/'

class ApiTestHelper:
    def _get_response(self, url):
        if (not settings.TEST_GO_LIVE or
            settings.TEST_GO_LIVE == "production"): # pragma: no cover
            url = "https://tools.pds-rings.seti.org" + url
        else: # pragma: no cover
            url = "http://dev.pds-rings.seti.org" + url
        return self.client.get(url)

    def _run_status_equal(self, url, expected, err_string=None):
        print(url)
        response = self._get_response(url)
        self.assertEqual(response.status_code, expected)
        if err_string:
            ret_string = response.content.decode()
            ret_string = ret_string.replace('&quot;', '"')
            print(ret_string)
            print(err_string)
            self.assertTrue(err_string in ret_string)

    @staticmethod
    def _depth_first_remove(data, ignore_list):
        if isinstance(data, dict):
            for ignore in ignore_list:
                if ignore in data:
                    del data[ignore]
            for key in data:
                ApiTestHelper._depth_first_remove(data[key], ignore_list)
        if isinstance(data, list):
            for ignore in ignore_list: # pragma: no cover
                while ignore in data:
                    data.remove(ignore)
            for el in data:
                ApiTestHelper._depth_first_remove(el, ignore_list)

    def _run_json_equal(self, url, expected, ignore=[]):
        if not isinstance(ignore, (list, tuple)):
            ignore = [ignore]
        print(url)
        response = self._get_response(url)
        self.assertEqual(response.status_code, 200)
        jdata = json.loads(response.content)
        print('Got:')
        print(jdata)
        print('Expected:')
        print(expected)
        self._depth_first_remove(jdata, ignore)
        self._depth_first_remove(expected, ignore)
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
        expected = str(expected)[2:-1]
        expected = (expected.replace('\\\\r', '').replace('\\r', '')
                    .replace('\r', ''))
        resp = str(response.content)[2:-1]
        resp = resp.replace('\\\\r', '').replace('\\r', '').replace('\r', '')
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
        expected = str(expected)[2:-1]
        expected = (expected.replace('\\\\r', '').replace('\\r', '')
                    .replace('\r', ''))
        resp = str(response.content)[2:-1]
        resp = resp.replace('\\\\r', '').replace('\\r', '').replace('\r', '')
        print('Got:')
        print(resp)
        print('Expected:')
        print(expected)
        self.assertEqual(expected, resp)

    def _run_html_startswith(self, url, expected):
        print(url)
        response = self._get_response(url)
        self.assertEqual(response.status_code, 200)
        expected = str(expected)[2:-1]
        expected = (expected.replace('\\\\r', '').replace('\\r', '')
                    .replace('\r', ''))
        resp = str(response.content)[2:-1]
        resp = resp.replace('\\\\r', '').replace('\\r', '').replace('\r', '')
        resp = resp[:len(expected)]
        print('Got:')
        print(resp)
        print('Expected:')
        print(expected)
        self.assertEqual(expected, resp)

    @staticmethod
    def _cleanup_csv(text):
        text = str(text)[2:-1]
        text = (text.replace('\\\\r', '').replace('\\r', '')
                .replace('\r', ''))
        return text

    def _run_csv_equal(self, url, expected):
        print(url)
        response = self._get_response(url)
        self.assertEqual(response.status_code, 200)
        expected = self._cleanup_csv(expected)
        resp = self._cleanup_csv(response.content)
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
        expected = self._cleanup_csv(expected)
        resp = self._cleanup_csv(response.content)
        print('Got:')
        print(resp)
        print('Expected:')
        print(expected)
        self.assertEqual(expected, resp)
