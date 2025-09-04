# opus/application/test_api/api_test_helper.py
import base64
import difflib
from io import BytesIO
import json
import os
import re
import tarfile
import zipfile
from PIL import Image, ImageChops

import settings

_RESPONSES_FILE_ROOT = 'test_api/responses/'

class ApiTestHelper:
    # If this is set to True, then instead of comparing responses to files
    # we overwrite the files with the response to update the test results.
    # Use with extreme caution!
    UPDATE_FILES = False

    def _get_response(self, url):
        if (not settings.TEST_GO_LIVE or
            settings.TEST_GO_LIVE == "production"):
            url = "https://opus.pds-rings.seti.org" + url
        else:
            url = "http://dev.pds.seti.org" + url
        return self.client.get(url)

    def _run_status_equal(self, url, expected, err_string=None):
        print(url)
        response = self._get_response(url)
        self.assertEqual(expected, response.status_code)
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
            for ignore in ignore_list:
                while ignore in data:
                    data.remove(ignore)
            for el in data:
                ApiTestHelper._depth_first_remove(el, ignore_list)

    @staticmethod
    def _print_clean_diffs(got, expected):
        if len(got) > 10000 or len(expected) > 10000:
            return # Too slow
        print('Diffs:')
        diff = difflib.SequenceMatcher(a=got, b=expected)
        for tag, i1, i2, j1, j2 in diff.get_opcodes():
            if tag == 'equal':
                continue
            print(f'{tag:7} got[{i1:5d}:{i2:5d}] --> exp[{j1:5d}:{j2:5d}] {got[i1:i2]} '
                  f'--> {expected[j1:j2]}')

    @staticmethod
    def _clean_string(s):
        s = str(s)
        if s.startswith("b'"):
            s = s[2:-1]
        return (s.replace(r'\\r', '')
                 .replace(r'\r', '')
                 .replace('\r', '')
                 .replace(r'\\n', r'\n')
                 .replace(r'\n', '\n'))

    def _run_json_equal(self, url, expected, ignore=[]):
        if not isinstance(ignore, (list, tuple)):
            ignore = [ignore]
        print(url)
        response = self._get_response(url)
        self.assertEqual(200, response.status_code)
        jdata = json.loads(response.content)
        print('Got:')
        print(jdata)
        print('Expected:')
        print(expected)
        self._depth_first_remove(jdata, ignore)
        self._depth_first_remove(expected, ignore)
        if jdata != expected:
            self._print_clean_diffs(str(jdata), str(expected))
        self.assertEqual(expected, jdata)

    def _run_json_equal_file(self, url, exp_file):
        print(url)
        response = self._get_response(url)
        self.assertEqual(200, response.status_code)
        jdata = json.loads(response.content)
        if self.UPDATE_FILES:
            with open(_RESPONSES_FILE_ROOT+exp_file, 'w') as fp:
                fp.write(json.dumps(jdata, indent=4))
            return
        with open(_RESPONSES_FILE_ROOT+exp_file, 'r') as fp:
            expected = json.loads(fp.read())
        print('Got:')
        print(jdata)
        print('Expected:')
        print(expected)
        if jdata != expected:
            self._print_clean_diffs(str(jdata), str(expected))
        self.assertEqual(expected, jdata)

    def _run_html_equal(self, url, expected):
        print(url)
        response = self._get_response(url)
        self.assertEqual(200, response.status_code)
        expected = self._clean_string(expected)
        resp = self._clean_string(str(response.content))
        print('Got:')
        print(resp)
        print('Expected:')
        print(expected)
        if resp != expected:
            self._print_clean_diffs(resp, expected)
        self.assertEqual(expected, resp)

    def _run_html_equal_file(self, url, exp_file, embedded_dynamic_image=False):
        print(url)
        response = self._get_response(url)
        self.assertEqual(200, response.status_code)
        if self.UPDATE_FILES:
            content = self._clean_string(response.content.decode())
            with open(_RESPONSES_FILE_ROOT+exp_file, 'w') as fp:
                fp.write(content)
            return
        with open(_RESPONSES_FILE_ROOT+exp_file, 'rb') as fp:
            expected = fp.read()
        expected = self._clean_string(expected)
        resp = self._clean_string(str(response.content))
        if embedded_dynamic_image:
            # extract the dynamic images and replace with generic tests.
            expected, expected_images = self.__extract_images(expected)
            resp, resp_images = self.__extract_images(resp)
        else:
            expected_images = resp_images = []
        print('Got:')
        print(resp)
        print('Expected:')
        print(expected)
        if resp != expected:
            self._print_clean_diffs(resp, expected)
        self.assertEqual(expected, resp)
        # There should be the same number of images, and they should decode identically.
        self.assertEqual(len(expected), len(resp))
        for image1, image2 in zip(expected_images, resp_images):
            self.__assert_images_identical(image1, image2)

    def _run_html_startswith(self, url, expected):
        print(url)
        response = self._get_response(url)
        self.assertEqual(200, response.status_code)
        expected = self._clean_string(expected)
        resp = self._clean_string(str(response.content))
        resp = resp[:len(expected)]
        print('Got:')
        print(resp)
        print('Expected:')
        print(expected)
        if resp != expected:
            self._print_clean_diffs(resp, expected)
        self.assertEqual(expected, resp)

    @staticmethod
    def _remove_range(s, start_str, end_str):
        ret = ''
        ind = s.find(start_str)
        if ind == -1:
            return s
        ret = s[:ind+len(start_str)]
        if end_str:
            ind = s.find(end_str)
            if ind != -1:
                ret += s[ind:]
        return ret

    def _run_html_range_file(self, url, exp_file, start_str, end_str):
        print(url)
        response = self._get_response(url)
        self.assertEqual(200, response.status_code)
        with open(_RESPONSES_FILE_ROOT+exp_file, 'r') as fp:
            expected = fp.read()
        expected = self._remove_range(expected, start_str, end_str)
        resp = self._clean_string(str(response.content))
        resp = self._remove_range(resp, start_str, end_str)
        if self.UPDATE_FILES:
            with open(_RESPONSES_FILE_ROOT+exp_file, 'w') as fp:
                fp.write(resp)
            return
        print('Got:')
        print(resp)
        print('Expected:')
        print(expected)
        if resp != expected:
            self._print_clean_diffs(resp, expected)
        self.assertEqual(expected, resp)

    def _run_html_contains(self, url, expected):
        print(url)
        response = self._get_response(url)
        self.assertEqual(200, response.status_code)
        expected = self._clean_string(expected)
        resp = self._clean_string(str(response.content))
        resp = resp[:len(expected)]
        print('Got:')
        print(resp)
        print('Expected:')
        print(expected)
        if expected not in resp:
            self._print_clean_diffs(resp, expected)
            self.assertTrue(False)

    def _run_html_not_contains(self, url, expected):
        print(url)
        response = self._get_response(url)
        self.assertEqual(200, response.status_code)
        expected = self._clean_string(expected)
        resp = self._clean_string(str(response.content))
        resp = resp[:len(expected)]
        print('Got:')
        print(resp)
        print('Expected:')
        print(expected)
        if expected in resp:
            self._print_clean_diffs(resp, expected)
            self.assertTrue(False)

    @staticmethod
    def _cleanup_csv(text):
        text = str(text)[2:-1]
        text = (text.replace('\\\\r', '').replace('\\r', '')
                .replace('\r', ''))
        return text

    def _run_csv_equal(self, url, expected):
        print(url)
        response = self._get_response(url)
        self.assertEqual(200, response.status_code)
        expected = self._cleanup_csv(expected)
        resp = self._cleanup_csv(response.content)
        print('Got:')
        print(resp)
        print('Expected:')
        print(expected)
        if resp != expected:
            self._print_clean_diffs(resp, expected)
        self.assertEqual(expected, resp)

    def _run_csv_equal_file(self, url, exp_file):
        print(url)
        response = self._get_response(url)
        self.assertEqual(200, response.status_code)
        if self.UPDATE_FILES:
            with open(_RESPONSES_FILE_ROOT+exp_file, 'w') as fp:
                fp.write(response.content.decode())
            return
        with open(_RESPONSES_FILE_ROOT+exp_file, 'rb') as fp:
            expected = fp.read()
        expected = self._cleanup_csv(expected)
        resp = self._cleanup_csv(response.content)
        print('Got:')
        print(resp)
        print('Expected:')
        print(expected)
        if resp != expected:
            self._print_clean_diffs(resp, expected)
        self.assertEqual(expected, resp)

    def _run_archive_file_equal(self, url, expected,
                                response_type='json', fmt='zip'):
        print(url)
        response = self._get_response(url)
        self.assertEqual(200, response.status_code)
        archive_file_path = None
        if response_type == 'json':
            jdata = json.loads(response.content)
            file = jdata['filename']
            path = file.replace(settings.TAR_FILE_URL_PATH, settings.TAR_FILE_PATH)
            read_mode = settings.DOWNLOAD_FORMATS[fmt][2]
            archive_file_path = path
            if fmt == 'zip':
                archive_file = zipfile.ZipFile(path, mode=read_mode)
            else:
                archive_file = tarfile.open(name=path, mode=read_mode)
        else:
            binary_stream = BytesIO(response.content)
            read_mode = settings.DOWNLOAD_FORMATS[fmt][2]
            file = response.headers['Content-Disposition']
            archive_file_path = (settings.TAR_FILE_PATH + file[file.index('=')+1::])
            if fmt == 'zip':
                archive_file = zipfile.ZipFile(binary_stream, mode=read_mode)
            else:
                archive_file = tarfile.open(mode=read_mode, fileobj=binary_stream)
        if fmt == 'zip':
            resp = archive_file.namelist()
        else:
            resp = archive_file.getnames()
        archive_file.close()
        # Remove the archive file stored under settings.TAR_FILE_PATH
        if archive_file_path and os.path.exists(archive_file_path):
            os.remove(archive_file_path)
        resp.sort()
        expected.sort()
        print('Got:')
        print(resp)
        print('Expected:')
        print(expected)
        if resp != expected:
            self._print_clean_diffs(resp, expected)
        self.assertListEqual(resp, expected)

    def __extract_images(self, data):
        """ Replaces the embedded images with in the data XXX.
          Returns the modified data, and a tuple of the bytes of the image(s)"""
        images = []

        def pull_out_image(match):
            images.append(base64.b64decode(match.group(2).encode()))
            # Return substitute value
            return f'<img class="{match.group(1)}" src="XXX" {match.group(3)}>'

        result = re.sub(
            r'<img class="([\w-]*)" src="data:image/png;charset=utf-8;base64,([^"]*)" ([^>]*)>',
            pull_out_image, data)
        return result, images

    def __assert_images_identical(self, image1, image2):
        """Verifies that two byte strings represent the same image."""
        if image1 == image2:
            # Shortcut. If both byte strings are the same, they must be identical images.
            return
        image1 = Image.open(BytesIO(image1)).convert('RGB')
        image2 = Image.open(BytesIO(image2)).convert('RGB')
        # Must be the same size
        self.assertEqual(image1.size, image2.size, "Image size mismatch")

        # getbbox returns the bounds of the non-zero elements. None if all are zero.
        difference = ImageChops.difference(image1, image2)
        self.assertIsNone(difference.getbbox(), "Images differ")
