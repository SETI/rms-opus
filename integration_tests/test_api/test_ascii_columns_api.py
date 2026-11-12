"""The identifier and string columns held in ASCII, as the public API reaches them.

Every ``opus_id`` and ``bundle_id`` column, and every column searched as a string, is in
the ASCII character set and compares without case. What is worth pinning, and why:

* **Case never matters.** An OPUS ID given in any case finds its observation, as it did
  under the schema's case-insensitive utf8mb4 collation.
* **Accents do not matter either.** MySQL refuses to compare an ASCII column with text
  holding any other character, so every request that compares a caller's text with one of
  these columns folds it first (`sql_builder.ascii_comparable`), as the schema's
  accent-blind utf8mb4 collation compared it: ``VGÍSS_6210`` is ``VGISS_6210``.
* **Text with no ASCII form finds nothing and is no error.** Each such request answers as
  it answers for an OPUS ID or a string the database does not hold.
* **A session key is ASCII and fits the cart's column**, or the request is refused.
"""

import json
import logging
from typing import Any
from unittest import TestCase

import requests
from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.test import Client
from rest_framework.test import RequestsClient

from opus_app.apps.tools.app_utils import http400_bad_session_id

from .api_test_helper import ApiTestHelper, go_live_target

#: An OPUS ID the test database holds.
OPUS_ID = 'vg-iss-2-s-c4360845'

#: That OPUS ID with a letter appended that has no ASCII form, as it travels in a URL. A
#: URL's OPUS ID is word characters and hyphens, and a sharp s is a word character.
NON_ASCII_OPUS_ID = OPUS_ID + '%C3%9F'

#: The OPUS ID's decoded form, as the API echoes it.
NON_ASCII_OPUS_ID_TEXT = OPUS_ID + '\u00df'

#: The cart's answer when an OPUS ID it was given is not in the database.
CART_NOT_FOUND = 'Internal Error: One or more OPUS_IDs not found; nothing added to cart'


class ApiAsciiColumnsTests(ApiTestHelper, TestCase):
    """Lookups and searches on the ASCII columns."""

    def setUp(self) -> None:
        """Turn off fault injection and error logging, and empty the caches.

        The `OPUS_FAKE_*` knobs are global and other suites turn them up, so every suite
        resets them; the cache is given this run's schema as its key prefix. Every stored
        search is removed, so each search here is built by the code under test rather than
        read back from an earlier build.
        """
        with connection.cursor() as cursor:
            cursor.execute('DELETE FROM search_results')
            cursor.execute('DELETE FROM user_searches')
        self.maxDiff = None
        settings.OPUS_FAKE_API_DELAYS = 0
        settings.OPUS_FAKE_SERVER_ERROR404_PROBABILITY = 0
        settings.OPUS_FAKE_SERVER_ERROR500_PROBABILITY = 0
        settings.CACHE_KEY_PREFIX = 'opustest:' + settings.DB_SCHEMA_NAME
        logging.disable(logging.ERROR)
        if go_live_target():  # pragma: no cover - remote server
            self.client = requests.Session()
        else:
            self.client = RequestsClient()
        cache.clear()

    def tearDown(self) -> None:
        """Restore logging after one test."""
        logging.disable(logging.NOTSET)

    @staticmethod
    def _path_response(path: str) -> Any:
        """Fetch a URL whose path holds a character outside ASCII, in process.

        The requests-based client puts such a path in the WSGI environment undecoded,
        which Django refuses; Django's own client encodes it as a server does.

        Parameters:
            path: Path of the endpoint, beginning with a slash, percent-encoded.

        Returns:
            The response.
        """
        print(path)
        host = next((h for h in settings.ALLOWED_HOSTS if h != '*'), 'localhost')
        return Client().get(path, HTTP_HOST=host)

    def _json(self, url: str) -> Any:
        """Return the decoded document one URL answers with 200.

        Parameters:
            url: Path of the API endpoint.

        Returns:
            The decoded JSON.
        """
        print(url)
        response = self._get_response(url)
        self.assertEqual(200, response.status_code)
        return json.loads(response.content)

    def _count(self, query: str) -> int:
        """Return the result count of a search.

        Parameters:
            query: The search's query string, without the ``?``.

        Returns:
            How many observations the search finds.
        """
        data = self._json(f'/api/meta/result_count.json?{query}')
        return int(data['data'][0]['result_count'])

    ##############################
    ######### CASE TESTS #########
    ##############################

    def test__api_metadata_opusid_in_mixed_case(self) -> None:
        "[test_ascii_columns_api.py] /api/metadata: an OPUS ID in mixed case finds its observation"
        url = '/api/metadata/VG-ISS-2-s-C4360845.json'
        self._run_json_equal_file(url, 'api_metadata_vg_iss_2_s_c4360845_default_json.json')

    def test__api_result_count_opusid_in_mixed_case(self) -> None:
        "[test_ascii_columns_api.py] /api/meta/result_count: an OPUS ID matches in any case"
        self.assertEqual(self._count('opusid=VG-ISS-2-S-C4360845&qtype-opusid=matches'), 1)

    def test__api_result_count_bundleid_in_lower_case(self) -> None:
        "[test_ascii_columns_api.py] /api/meta/result_count: a bundle ID matches in any case"
        count = self._count('bundleid=VGISS_6210&qtype-bundleid=matches')
        self.assertGreater(count, 0)
        self.assertEqual(self._count('bundleid=vgiss_6210&qtype-bundleid=matches'), count)

    ################################
    ######### ACCENT TESTS #########
    ################################

    def test__api_metadata_opusid_with_accents(self) -> None:
        "[test_ascii_columns_api.py] /api/metadata: an OPUS ID with accents finds its observation"
        plain = self._path_response(f'/api/metadata/{OPUS_ID}.json')
        accented = self._path_response('/api/metadata/vg-%C3%AD%C5%9B%C5%9B-2-s-c4360845.json')
        self.assertEqual(plain.status_code, 200)
        self.assertEqual(accented.status_code, 200)
        self.assertEqual(json.loads(accented.content), json.loads(plain.content))

    def test__api_result_count_bundleid_with_accents(self) -> None:
        "[test_ascii_columns_api.py] /api/meta/result_count: a bundle ID with an accent matches"
        count = self._count('bundleid=VGISS_6210&qtype-bundleid=matches')
        self.assertGreater(count, 0)
        self.assertEqual(self._count('bundleid=VG%C3%8DSS_6210&qtype-bundleid=matches'), count)
        self.assertEqual(
            self._count('bundleid=v%C7%B5iss&qtype-bundleid=begins'),
            self._count('bundleid=VGISS&qtype-bundleid=begins'),
        )

    ##################################
    ######### SESSION TESTS ##########
    ##################################

    def test__api_cart_status_session_id_outside_ascii_is_refused(self) -> None:
        "[test_ascii_columns_api.py] /__cart/status: a __sessionid outside ASCII is a 400"
        url = '/__cart/status.json?reqno=1&__sessionid=sess%C3%A9'
        self._run_status_equal(url, 400, http400_bad_session_id('/__cart/status.json'))

    def test__api_cart_status_session_id_too_long_is_refused(self) -> None:
        "[test_ascii_columns_api.py] /__cart/status: a __sessionid longer than the column is a 400"
        self._json(f'/__cart/status.json?reqno=1&__sessionid={"s" * 40}')
        url = f'/__cart/status.json?reqno=1&__sessionid={"s" * 41}'
        self._run_status_equal(url, 400, http400_bad_session_id('/__cart/status.json'))

    ###################################
    ######### NON-ASCII TESTS #########
    ###################################

    def test__api_metadata_non_ascii_opusid_is_unknown(self) -> None:
        "[test_ascii_columns_api.py] /api/metadata: an OPUS ID outside ASCII is unknown"
        response = self._path_response(f'/api/metadata/{NON_ASCII_OPUS_ID}.json')
        self.assertEqual(response.status_code, 404)
        self.assertIn(
            f'Unknown OPUSID &quot;{NON_ASCII_OPUS_ID_TEXT}&quot;', response.content.decode()
        )

    def test__api_files_non_ascii_opusid_has_no_files(self) -> None:
        "[test_ascii_columns_api.py] /api/files: an OPUS ID outside ASCII has no files"
        response = self._path_response(f'/api/files/{NON_ASCII_OPUS_ID}.json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            json.loads(response.content),
            {'data': {NON_ASCII_OPUS_ID_TEXT: {}}, 'versions': {NON_ASCII_OPUS_ID_TEXT: {}}},
        )

    def test__api_categories_non_ascii_opusid_is_unknown(self) -> None:
        "[test_ascii_columns_api.py] /api/categories: an OPUS ID outside ASCII has none"
        response = self._path_response(f'/api/categories/{NON_ASCII_OPUS_ID}.json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), [])

    def test__api_product_types_non_ascii_opusid_is_unknown(self) -> None:
        "[test_ascii_columns_api.py] /api/product_types: an OPUS ID outside ASCII has none"
        response = self._path_response(f'/api/product_types/{NON_ASCII_OPUS_ID}.json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), [])

    def test__api_image_non_ascii_opusid_has_no_image(self) -> None:
        "[test_ascii_columns_api.py] /api/image: an OPUS ID outside ASCII has no image"
        response = self._path_response(f'/api/image/thumb/{NON_ASCII_OPUS_ID}.json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content)['data'], [])

    def test__api_initdetail_non_ascii_opusid_is_not_found(self) -> None:
        "[test_ascii_columns_api.py] /__initdetail: an OPUS ID outside ASCII is not found"
        response = self._path_response(f'/__initdetail/{NON_ASCII_OPUS_ID}.html')
        self.assertEqual(response.status_code, 404)

    def test__api_normalizeurl_non_ascii_detail_is_ignored(self) -> None:
        "[test_ascii_columns_api.py] /__normalizeurl: a detail OPUS ID outside ASCII is ignored"
        data = self._json(f'/__normalizeurl.json?detail={NON_ASCII_OPUS_ID}')
        self.assertIn('was not found in the current database', data['msg'])

    def test__api_result_count_non_ascii_strings_match_nothing(self) -> None:
        "[test_ascii_columns_api.py] /api/meta/result_count: each string query type, outside ASCII"
        everything = self._count('')
        self.assertGreater(everything, 0)
        for query, count in (
            (f'opusid={NON_ASCII_OPUS_ID}&qtype-opusid=matches', 0),
            (f'opusid={NON_ASCII_OPUS_ID}&qtype-opusid=contains', 0),
            ('bundleid=VG%E2%82%AC&qtype-bundleid=begins', 0),
            ('bundleid=%E2%82%AC0&qtype-bundleid=ends', 0),
            ('bundleid=VG_%E2%82%AC&qtype-bundleid=regex', 0),
            ('bundleid=%E2%82%AC&qtype-bundleid=excludes', everything),
            ('productid=%E2%82%AC&qtype-productid=contains', 0),
        ):
            with self.subTest(query=query):
                self.assertEqual(self._count(query), count)

    def test__api_stringsearchchoices_non_ascii_has_no_choices(self) -> None:
        "[test_ascii_columns_api.py] /__api/stringsearchchoices: text outside ASCII has none"
        data = self._json('/__api/stringsearchchoices/bundleid.json?bundleid=VG%E2%82%AC&reqno=1')
        self.assertEqual(data['choices'], [])

    def test__api_cart_non_ascii_opusid_is_not_found(self) -> None:
        "[test_ascii_columns_api.py] /__cart: adding or removing an OPUS ID outside ASCII"
        self._json('/__cart/reset.json?reqno=1')
        data = self._json(f'/__cart/add.json?opusid={NON_ASCII_OPUS_ID}&reqno=2')
        self.assertEqual(data['error'], CART_NOT_FOUND)
        data = self._json(f'/__cart/remove.json?opusid={NON_ASCII_OPUS_ID}&recyclebin=1&reqno=3')
        self.assertIn('not found', data['error'])
        data = self._json(f'/__cart/remove.json?opusid={NON_ASCII_OPUS_ID}&reqno=4')
        self.assertEqual(data['count'], 0)
        data = self._json(
            f'/__cart/addrange.json?range={NON_ASCII_OPUS_ID},{OPUS_ID}&bundleid=VGISS_6210&reqno=5'
        )
        self.assertIn('not found', data['error'])
        self.assertEqual(self._json('/__cart/status.json?reqno=6')['count'], 0)
