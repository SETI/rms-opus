"""Shared assertion helpers for the golden-response API suite.

Every test in `integration_tests/test_api` drives one OPUS API URL and compares the
response against a value written into the test or a file under `responses/`. The
comparison is what varies -- JSON, HTML, CSV, an archive's member list, an embedded
PNG -- so it lives here once and the suites mix it in.

The mix-in is also where the suite's two runtime-injected settings are read; see
`go_live_target` for why they are read through a function rather than off
`django.conf.settings` directly.
"""

import base64
import difflib
import json
import os
import re
import tarfile
import zipfile
from collections.abc import Sequence
from io import BytesIO
from typing import TYPE_CHECKING, Any

import requests
from django.conf import settings
from PIL import Image, ImageChops
from PIL.Image import Image as PILImage

# Relative to the working directory: the whole suite is run from the repository
# root (see run_coverage.sh and integration_tests/test_api/TEST_API_README.md).
_RESPONSES_FILE_ROOT = 'integration_tests/test_api/responses/'


def go_live_target() -> str | None:
    """Which remote server the API suite runs against, or None for the local one.

    `TEST_GO_LIVE` is not a configured setting: `manage.py` sets it to None before
    handing off to the test runner, and the `api-livetest-*` verbs load
    `enable_livetests_dev`/`enable_livetests_pro`, whose module bodies set it to
    ``'dev'`` or ``'production'``. It is therefore absent from the settings module
    that django-stubs resolves attribute types against, and reading it through
    `getattr` is what states that -- the alternative is thirty identical
    suppressions saying the same thing thirty times.

    Reading it through a function rather than caching it in a module constant is
    load-bearing: the value is assigned after this module is imported.

    Returns:
        The target name a live test run was started with, or None when the suite is
        running against the locally imported database.
    """
    return getattr(settings, 'TEST_GO_LIVE', None)


def result_counts_against_internal_db() -> bool:
    """Whether the result-count suite checks the internal database's own counts.

    Injected exactly like `go_live_target`'s setting: `manage.py` sets it False and
    the `api-internal-db-result-counts` verb sets it True.

    Returns:
        True when the recorded counts are checked against the local import rather
        than against the public server.
    """
    return bool(getattr(settings, 'TEST_RESULT_COUNTS_AGAINST_INTERNAL_DB', False))


if TYPE_CHECKING:
    # `ApiTestHelper` is a mix-in: its bodies call `self.assertEqual` and friends,
    # which the concrete suite supplies by also inheriting `TestCase`. Declaring that
    # base only while type checking is what lets those resolve without making the
    # helper a `TestCase` at run time, which would collect it as an (empty) test class
    # in each of the seven modules that import it. The suites list this mix-in
    # *before* `TestCase` so the two orders agree: with the base in place, the reverse
    # order has no consistent MRO.
    from unittest import TestCase as _ApiTestHelperBase
else:
    _ApiTestHelperBase = object


class ApiTestHelper(_ApiTestHelperBase):
    """Response-comparison helpers mixed into every `test_api` suite."""

    # Set by each suite's setUp, to a RequestsClient that drives the WSGI application
    # in process or -- on the live-server path -- to a plain session that goes over
    # the network. RequestsClient is a requests.Session subclass, so both answer with
    # a requests.Response and the assertions below do not care which is in place.
    client: requests.Session

    # If this is set to True, then instead of comparing responses to files
    # we overwrite the files with the response to update the test results.
    # Use with extreme caution!
    UPDATE_FILES = False

    def _get_response(self, url: str) -> requests.Response:
        """Fetch one API URL, from the local test client or a live server.

        Parameters:
            url: Path of the API endpoint, beginning with a slash.

        Returns:
            The response, whichever client answered it.
        """
        target = go_live_target()
        if not target or target == "production":
            url = "https://opus.pds-rings.seti.org" + url
        else:
            url = "http://dev.pds.seti.org" + url
        return self.client.get(url)

    def _run_status_equal(self, url: str, expected: int,
                          err_string: str | None = None) -> None:
        """Assert one URL's status code, and optionally text in its error body.

        Parameters:
            url: Path of the API endpoint.
            expected: The status code the endpoint must answer with.
            err_string: Text the response body must contain, or None to check only
                the status code.
        """
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
    def _depth_first_remove(data: Any, ignore_list: list[str]) -> None:
        """Delete named keys and values from a decoded JSON structure, in place.

        Used to drop the parts of a response that vary from run to run before
        comparing it with a recorded one.

        Parameters:
            data: Any part of a decoded JSON document; anything that is neither a
                dict nor a list is left alone.
            ignore_list: Dictionary keys to delete, and list elements to remove.
        """
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
    def _print_clean_diffs(got: Sequence[Any], expected: Sequence[Any]) -> None:
        """Print the differing runs between two responses, to explain a failure.

        Parameters:
            got: The response the server produced, as text or as a list of an
                archive's member names.
            expected: The recorded response it was compared against, in the same
                form.
        """
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
    def _clean_string(s: object) -> str:
        """Normalize a response body's line endings and escaping for comparison.

        A response reaches this either as text or as the ``str()`` of a bytes
        object, whose leading ``b'`` and trailing quote are stripped here.

        Parameters:
            s: The response body, in any of those forms.

        Returns:
            The body with carriage returns removed and escaped newlines unescaped.
        """
        s = str(s)
        if s.startswith("b'"):
            s = s[2:-1]
        return (s.replace(r'\\r', '')
                 .replace(r'\r', '')
                 .replace('\r', '')
                 .replace(r'\\n', r'\n')
                 .replace(r'\n', '\n'))

    def _run_json_equal(self, url: str, expected: Any,
                        ignore: str | list[str] | tuple[str, ...] | None = None) -> None:
        """Assert one URL answers 200 with a given JSON document.

        Parameters:
            url: Path of the API endpoint.
            expected: The decoded document the response must equal.
            ignore: Keys to drop from both documents before comparing, given as a
                sequence or as a single key.
        """
        ignore_list: list[str]
        if ignore is None:
            ignore_list = []
        elif not isinstance(ignore, (list, tuple)):
            ignore_list = [ignore]
        else:
            ignore_list = list(ignore)
        print(url)
        response = self._get_response(url)
        self.assertEqual(200, response.status_code)
        jdata = json.loads(response.content)
        print('Got:')
        print(jdata)
        print('Expected:')
        print(expected)
        self._depth_first_remove(jdata, ignore_list)
        self._depth_first_remove(expected, ignore_list)
        if jdata != expected:
            self._print_clean_diffs(str(jdata), str(expected))
        self.assertEqual(expected, jdata)

    def _run_json_equal_file(self, url: str, exp_file: str) -> None:
        """Assert one URL answers 200 with the JSON document recorded in a file.

        Parameters:
            url: Path of the API endpoint.
            exp_file: Name of the recorded response, under `responses/`.
        """
        print(url)
        response = self._get_response(url)
        self.assertEqual(200, response.status_code)
        jdata = json.loads(response.content)
        if self.UPDATE_FILES:
            with open(_RESPONSES_FILE_ROOT+exp_file, 'w') as fp:
                fp.write(json.dumps(jdata, indent=4))
            return
        with open(_RESPONSES_FILE_ROOT+exp_file) as fp:
            expected = json.loads(fp.read())
        print('Got:')
        print(jdata)
        print('Expected:')
        print(expected)
        if jdata != expected:
            self._print_clean_diffs(str(jdata), str(expected))
        self.assertEqual(expected, jdata)

    def _run_html_equal(self, url: str, expected: object) -> None:
        """Assert one URL answers 200 with a given HTML body.

        Parameters:
            url: Path of the API endpoint.
            expected: The body the response must equal once normalized, as text or
                as the bytes it was recorded in.
        """
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

    def _run_html_equal_file(self, url: str, exp_file: str,
                             embedded_dynamic_image: bool = False) -> None:
        """Assert one URL answers 200 with the HTML body recorded in a file.

        Parameters:
            url: Path of the API endpoint.
            exp_file: Name of the recorded response, under `responses/`.
            embedded_dynamic_image: Compare base64 PNGs in the body as decoded
                images rather than as text, for responses whose images are
                generated per request.
        """
        print(url)
        response = self._get_response(url)
        self.assertEqual(200, response.status_code)
        if self.UPDATE_FILES:
            content = self._clean_string(response.content.decode())
            with open(_RESPONSES_FILE_ROOT+exp_file, 'w') as fp:
                fp.write(content)
            return
        with open(_RESPONSES_FILE_ROOT+exp_file, 'rb') as fp:
            expected_bytes = fp.read()
        expected = self._clean_string(expected_bytes)
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
        # strict=False: a length mismatch between the two image lists is
        # ignored rather than raising.
        for image1, image2 in zip(expected_images, resp_images, strict=False):
            self.__assert_images_identical(image1, image2)

    def _run_html_startswith(self, url: str, expected: str) -> None:
        """Assert one URL answers 200 with an HTML body starting with given text.

        Parameters:
            url: Path of the API endpoint.
            expected: The text the normalized body must begin with.
        """
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
    def _remove_range(s: str, start_str: str, end_str: str | None) -> str:
        """Cut the text between two markers out of a response body.

        Used where part of a page varies from run to run and only the surrounding
        text is worth comparing.

        Parameters:
            s: The response body.
            start_str: Marker after which the cut begins; if it is absent, `s` is
                returned unchanged.
            end_str: Marker at which the cut ends, or None to cut to the end. If it
                is absent from `s` the cut also runs to the end.

        Returns:
            The body with that range removed.
        """
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

    def _run_html_range_file(self, url: str, exp_file: str, start_str: str,
                             end_str: str | None) -> None:
        """Assert one URL matches a recorded response outside a varying range.

        Parameters:
            url: Path of the API endpoint.
            exp_file: Name of the recorded response, under `responses/`.
            start_str: Marker after which both bodies are cut.
            end_str: Marker at which both cuts end, or None to cut to the end.
        """
        print(url)
        response = self._get_response(url)
        self.assertEqual(200, response.status_code)
        with open(_RESPONSES_FILE_ROOT+exp_file) as fp:
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

    def _run_html_contains(self, url: str, expected: str) -> None:
        """Assert one URL answers 200 with a body whose start is given text.

        Parameters:
            url: Path of the API endpoint.
            expected: The text sought. Note that the response is truncated to this
                text's length first, so this asserts the body *starts with* it.
        """
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

    def _run_html_not_contains(self, url: str, expected: str) -> None:
        """Assert one URL answers 200 with a body whose start is not given text.

        Parameters:
            url: Path of the API endpoint.
            expected: The text that must be absent. As in `_run_html_contains`, the
                response is truncated to this text's length before the check.
        """
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
    def _cleanup_csv(text: object) -> str:
        """Normalize a CSV response body for comparison.

        Parameters:
            text: The response body **as bytes**, either the response's own or the
                literal a test recorded. The first two and the last character of its
                ``str()`` are dropped unconditionally -- they are the ``b'`` and the
                closing quote -- so passing text here silently loses three
                characters. Every call site passes bytes.

        Returns:
            The body with that wrapper and its carriage returns removed.
        """
        text = str(text)[2:-1]
        text = (text.replace('\\\\r', '').replace('\\r', '')
                .replace('\r', ''))
        return text

    def _run_csv_equal(self, url: str, expected: object) -> None:
        """Assert one URL answers 200 with a given CSV body.

        Parameters:
            url: Path of the API endpoint.
            expected: The body the response must equal, once normalized.
        """
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

    def _run_csv_equal_file(self, url: str, exp_file: str) -> None:
        """Assert one URL answers 200 with the CSV body recorded in a file.

        Parameters:
            url: Path of the API endpoint.
            exp_file: Name of the recorded response, under `responses/`.
        """
        print(url)
        response = self._get_response(url)
        self.assertEqual(200, response.status_code)
        if self.UPDATE_FILES:
            with open(_RESPONSES_FILE_ROOT+exp_file, 'w') as fp:
                fp.write(response.content.decode())
            return
        with open(_RESPONSES_FILE_ROOT+exp_file, 'rb') as fp:
            expected_bytes = fp.read()
        expected = self._cleanup_csv(expected_bytes)
        resp = self._cleanup_csv(response.content)
        print('Got:')
        print(resp)
        print('Expected:')
        print(expected)
        if resp != expected:
            self._print_clean_diffs(resp, expected)
        self.assertEqual(expected, resp)

    def _run_archive_file_equal(self, url: str, expected: list[str],
                                response_type: str = 'json', fmt: str = 'zip') -> None:
        """Assert a download URL produces an archive holding exactly named members.

        The archive is read either from the path the JSON response names or from the
        response body itself, and is deleted afterwards when it was written to disk.

        Parameters:
            url: Path of the download endpoint.
            expected: The member names the archive must hold. Sorted in place.
            response_type: ``'json'`` when the response names a file to open,
                anything else when the response body is the archive.
            fmt: Key into ``settings.DOWNLOAD_FORMATS``; ``'zip'`` selects the zip
                reader and every other value the tar reader.
        """
        print(url)
        response = self._get_response(url)
        self.assertEqual(200, response.status_code)
        archive_file_path = None
        archive_file: zipfile.ZipFile | tarfile.TarFile
        # DOWNLOAD_FORMATS records (content type, write mode, read mode) per format.
        # Both readers below declare `mode` as a set of literal strings, and this
        # value comes from configuration, so it is a plain string at this point; the
        # reader itself is what rejects a mode it does not know.
        read_mode: Any = settings.DOWNLOAD_FORMATS[fmt][2]
        if response_type == 'json':
            jdata = json.loads(response.content)
            file = jdata['filename']
            path = file.replace(settings.TAR_FILE_URL_PATH, settings.TAR_FILE_PATH)
            archive_file_path = path
            if fmt == 'zip':
                archive_file = zipfile.ZipFile(path, mode=read_mode)
            else:
                # SIM115 suppressed: the archive is opened in one of four
                # branches and closed once, below, where the branches rejoin.
                archive_file = tarfile.open(name=path, mode=read_mode)  # noqa: SIM115
        else:
            binary_stream = BytesIO(response.content)
            file = response.headers['Content-Disposition']
            archive_file_path = (settings.TAR_FILE_PATH + file[file.index('=')+1::])
            if fmt == 'zip':
                archive_file = zipfile.ZipFile(binary_stream, mode=read_mode)
            else:
                # SIM115 suppressed for the same reason as above.
                archive_file = tarfile.open(mode=read_mode, fileobj=binary_stream)  # noqa: SIM115
        # Asking the object rather than re-deriving the format from `fmt`: every
        # branch above opens a ZipFile exactly when fmt == 'zip', so this selects
        # the same reader and narrows the union for the checker at the same time.
        if isinstance(archive_file, zipfile.ZipFile):
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

    def __extract_images(self, data: str) -> tuple[str, list[bytes]]:
        """Replace each embedded base64 PNG in an HTML body with a fixed marker.

        Parameters:
            data: The HTML body.

        Returns:
            The body with every embedded image's data replaced by ``XXX``, and the
            decoded bytes of the images that were removed, in document order.
        """
        images: list[bytes] = []

        def pull_out_image(match: re.Match[str]) -> str:
            """Record one image's bytes and return its replacement tag."""
            images.append(base64.b64decode(match.group(2).encode()))
            # Return substitute value
            return f'<img class="{match.group(1)}" src="XXX" {match.group(3)}>'

        result = re.sub(
            r'<img class="([^"]*)" src="data:image/png;charset=utf-8;base64,([^"]*)" ([^>]*)>',
            pull_out_image, data)
        return result, images

    def __assert_images_identical(self, image1: bytes, image2: bytes) -> None:
        """Assert two encoded images decode to the same picture.

        Parameters:
            image1: One encoded image.
            image2: The other.
        """
        if image1 == image2:
            # Shortcut. If both byte strings are the same, they must be identical images.
            return
        decoded1: PILImage = Image.open(BytesIO(image1)).convert('RGB')
        decoded2: PILImage = Image.open(BytesIO(image2)).convert('RGB')
        # Must be the same size
        self.assertEqual(decoded1.size, decoded2.size, "Image size mismatch")

        # getbbox returns the bounds of the non-zero elements. None if all are zero.
        difference = ImageChops.difference(decoded1, decoded2)
        self.assertIsNone(difference.getbbox(), "Images differ")
