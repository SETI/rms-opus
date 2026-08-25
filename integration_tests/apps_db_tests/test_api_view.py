# integration_tests/apps_db_tests/test_api_view.py

"""Tests for the @api_view decorator in opus_app.apps.tools.app_utils.

These need no database: they drive the decorator with handlers written here, not
with real API endpoints. They live in this suite rather than in `tests/` because
the 100% branch-coverage gate measures `src/opus_app/apps/*`, and every branch of
the decorator has to be exercised by the suite that gate reads. PR-18 creates the
holdings-free Django suite these could later move to.

What is worth pinning here, and why:

* **The status each kind of failure produces.** The decorator is the single place
  that decides what an OPUS API call returns when it goes wrong, so the mapping
  from `Http404` / `Http400Error` / any other exception to 404 / 400 / 500 is the
  whole contract.
* **That the API-call record is closed on every one of those paths.** The
  hand-written pairs this decorator replaces could not guarantee it, and a record
  that is never closed leaks an entry in `_API_START_TIMES` for the life of the
  process.
* **That an exception Django answers itself is not absorbed.** A `DisallowedHost`
  turned into a generic 500 would lose both the 400 Django gives it and the
  `django.security.*` record an operator watches for.
* **That an unhandled exception is logged with its traceback.** A 500 whose only
  record is "something failed" is what issue #512 is about; the traceback is the
  point of catching it centrally rather than letting it reach Django.
* **Fault injection firing before the handler.** The knobs used to fire at a
  hundred interior points; the decorator now consults them once, and a handler
  that was not supposed to run must not have run.
* **That `api_code` is supplied only to handlers that ask for it.** The wrapper
  inspects the handler's signature once, at decoration time, and a mistake there
  would be a TypeError on every request to half the API.
"""

import logging
from unittest import TestCase

from django.conf import settings
from django.core.exceptions import BadRequest, PermissionDenied, SuspiciousOperation
from django.http import Http404, HttpResponse
from django.test import RequestFactory

from opus_app.apps.tools import app_utils
from opus_app.apps.tools.app_utils import (
    HTTP400_BAD_LIMIT,
    Http400Error,
    api_view,
)


class ApiViewTests(TestCase):

    #: Settings these tests move and must put back: two of them are turned all
    #: the way up here, and a suite that does not reset them in its own setUp
    #: would then see every one of its API calls fail.
    _MUTATED_SETTINGS = ('OPUS_FAKE_API_DELAYS',
                         'OPUS_FAKE_SERVER_ERROR404_PROBABILITY',
                         'OPUS_FAKE_SERVER_ERROR500_PROBABILITY',
                         'OPUS_LOG_API_CALLS')

    def setUp(self):
        self._saved_settings = {name: getattr(settings, name)
                                for name in self._MUTATED_SETTINGS}
        settings.OPUS_FAKE_API_DELAYS = 0
        settings.OPUS_FAKE_SERVER_ERROR404_PROBABILITY = 0
        settings.OPUS_FAKE_SERVER_ERROR500_PROBABILITY = 0
        settings.OPUS_LOG_API_CALLS = False
        self.factory = RequestFactory()
        self.maxDiff = None
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        for name, value in self._saved_settings.items():
            setattr(settings, name, value)
        logging.disable(logging.NOTSET)

    def _request(self, path='/__api/fake.json'):
        return self.factory.get(path)

    def test__api_view_returns_the_handler_response(self):
        "[test_api_view.py] api_view: a handler that succeeds"
        @api_view
        def handler(request):
            return HttpResponse('ok')

        response = handler(self._request())
        self.assertEqual(200, response.status_code)
        self.assertEqual(b'ok', response.content)

    def test__api_view_passes_url_arguments_through(self):
        "[test_api_view.py] api_view: positional and keyword URL arguments"
        @api_view
        def handler(request, size, fmt=None):
            return HttpResponse(f'{size}/{fmt}')

        response = handler(self._request(), 'thumb', fmt='json')
        self.assertEqual(b'thumb/json', response.content)

    def test__api_view_supplies_api_code_when_asked(self):
        "[test_api_view.py] api_view: a handler that declares api_code gets one"
        seen = []

        @api_view
        def handler(request, api_code):
            seen.append(api_code)
            return HttpResponse('ok')

        handler(self._request())
        handler(self._request())
        # The API call number increments by exactly one per call, which is what
        # makes it usable for correlating a slow query with its request.
        self.assertEqual([seen[0], seen[0]+1], seen)

    def test__api_view_omits_api_code_when_not_asked(self):
        "[test_api_view.py] api_view: a handler with no api_code parameter"
        @api_view
        def handler(request, **kwargs):
            return HttpResponse(repr(sorted(kwargs)))

        response = handler(self._request(), slug='time')
        self.assertEqual(b"['slug']", response.content)

    def test__api_view_reraises_http404(self):
        "[test_api_view.py] api_view: Http404 reaches Django unchanged"
        @api_view
        def handler(request):
            raise Http404('no such thing')

        with self.assertRaisesRegex(Http404, 'no such thing'):
            handler(self._request())

    def test__api_view_turns_http400error_into_a_400(self):
        "[test_api_view.py] api_view: Http400Error becomes a 400 naming the problem"
        @api_view
        def handler(request):
            raise Http400Error(HTTP400_BAD_LIMIT('x', request))

        response = handler(self._request('/api/data.json'))
        self.assertEqual(400, response.status_code)
        body = response.content.decode()
        self.assertIn('Badly formatted limit &quot;x&quot; for /api/data.json',
                      body)
        self.assertIn('/api/data.json', body)

    def test__http400_body_falls_back_to_the_exception_name(self):
        "[test_api_view.py] api_view: an Http400Error carrying no message"
        @api_view
        def handler(request):
            raise Http400Error

        response = handler(self._request())
        self.assertEqual(400, response.status_code)
        self.assertIn('Http400Error', response.content.decode())

    def test__api_view_turns_any_other_exception_into_a_500(self):
        "[test_api_view.py] api_view: an unhandled exception becomes a 500"
        @api_view
        def handler(request):
            raise RuntimeError('boom')

        response = handler(self._request('/api/data.json'))
        self.assertEqual(500, response.status_code)
        self.assertIn('Unspecified internal server error for /api/data.json',
                      response.content.decode())

    def test__api_view_logs_an_unhandled_exception_with_its_traceback(self):
        "[test_api_view.py] api_view: the 500 log record carries exc_info"
        @api_view
        def handler(request):
            raise RuntimeError('boom')

        logging.disable(logging.NOTSET)
        try:
            with self.assertLogs('opus_app.apps.tools.app_utils',
                                 level='ERROR') as captured:
                handler(self._request())
        finally:
            logging.disable(logging.CRITICAL)
        self.assertEqual(1, len(captured.records))
        record = captured.records[0]
        self.assertIsNotNone(record.exc_info)
        self.assertIn('handler: Unhandled exception', record.getMessage())

    def test__api_view_handles_a_missing_request(self):
        "[test_api_view.py] api_view: a handler called with no request at all"
        @api_view
        def handler(request):
            raise RuntimeError('boom')

        response = handler(None)
        self.assertEqual(500, response.status_code)
        self.assertIn('Unspecified internal server error for (no request)',
                      response.content.decode())

    def test__api_view_injects_a_404_before_the_handler_runs(self):
        "[test_api_view.py] api_view: OPUS_FAKE_SERVER_ERROR404_PROBABILITY"
        ran = []

        @api_view
        def handler(request):
            # Never reached: the injection replaces the call.
            ran.append(True)
            return HttpResponse('ok')

        settings.OPUS_FAKE_SERVER_ERROR404_PROBABILITY = 1
        with self.assertRaisesRegex(Http404, 'Fake HTTP404 error'):
            handler(self._request())
        self.assertEqual([], ran)

    def test__api_view_injects_a_500_before_the_handler_runs(self):
        "[test_api_view.py] api_view: OPUS_FAKE_SERVER_ERROR500_PROBABILITY"
        ran = []

        @api_view
        def handler(request):
            # Never reached: the injection replaces the call.
            ran.append(True)
            return HttpResponse('ok')

        settings.OPUS_FAKE_SERVER_ERROR500_PROBABILITY = 1
        response = handler(self._request())
        self.assertEqual(500, response.status_code)
        self.assertIn('Fake HTTP500 error', response.content.decode())
        self.assertEqual([], ran)

    def test__api_view_notes_an_injected_fault_in_the_api_call_log(self):
        "[test_api_view.py] api_view: injection with OPUS_LOG_API_CALLS enabled"
        @api_view
        def handler(request):
            return HttpResponse('ok')  # Never reached.

        settings.OPUS_LOG_API_CALLS = 'error'
        settings.OPUS_FAKE_SERVER_ERROR500_PROBABILITY = 1
        logging.disable(logging.NOTSET)
        try:
            with self.assertLogs('opus_app.apps.tools.app_utils',
                                 level='ERROR') as captured:
                handler(self._request())
        finally:
            logging.disable(logging.CRITICAL)
        self.assertIn('Faking HTTP500 error',
                      [record.getMessage() for record in captured.records])

    def test__api_view_keeps_the_handler_name_and_docstring(self):
        "[test_api_view.py] api_view: the wrapper is transparent to introspection"
        @api_view
        def api_something(request):
            "A docstring Sphinx would have to find."
            return HttpResponse('ok')  # Never called.

        self.assertEqual('api_something', api_something.__name__)
        self.assertEqual('A docstring Sphinx would have to find.',
                         api_something.__doc__)

    def test__api_view_reraises_what_django_answers_itself(self):
        "[test_api_view.py] api_view: SuspiciousOperation and friends are not absorbed"
        # Django turns each of these into a specific response of its own, and
        # SuspiciousOperation also reaches the django.security.* logger; a generic
        # 500 here would lose both. DisallowedHost, which
        # HttpRequest.build_absolute_uri raises on a spoofed Host header, is a
        # SuspiciousOperation, so this is the reachable case.
        for exception_class in (BadRequest, PermissionDenied, SuspiciousOperation):
            with self.subTest(exception_class=exception_class.__name__):
                @api_view
                def handler(request, raises=exception_class):
                    raise raises('nope')

                with self.assertRaises(exception_class):
                    handler(self._request())

    def test__api_view_closes_the_api_call_record_on_every_path(self):
        "[test_api_view.py] api_view: no path leaves an entry in _API_START_TIMES"
        @api_view
        def ok_handler(request):
            return HttpResponse('ok')

        @api_view
        def http404_handler(request):
            raise Http404('gone')

        @api_view
        def http400_handler(request):
            raise Http400Error('bad')

        @api_view
        def boom_handler(request):
            raise RuntimeError('boom')

        app_utils._API_START_TIMES.clear()
        ok_handler(self._request())
        with self.assertRaises(Http404):
            http404_handler(self._request())
        http400_handler(self._request())
        boom_handler(self._request())
        # Every one of the four exits recorded its call, so nothing is left open.
        # The hand-written pairs this replaces could not promise that: a raise
        # past exit_api_call leaked the entry for the life of the process.
        self.assertEqual({}, app_utils._API_START_TIMES)

    def test__exit_api_call_does_not_decode_a_binary_body(self):
        "[test_api_view.py] exit_api_call: an archive is not decoded to log 240 chars"
        settings.OPUS_LOG_API_CALLS = 'error'

        @api_view
        def handler(request):
            return HttpResponse(b'PK\x03\x04\xff\xfe not text',
                                content_type='application/zip')

        logging.disable(logging.NOTSET)
        try:
            with self.assertLogs('opus_app.apps.tools.app_utils',
                                 level='ERROR') as captured:
                handler(self._request())
        finally:
            logging.disable(logging.CRITICAL)
        messages = [record.getMessage() for record in captured.records]
        exit_lines = [m for m in messages if 'EXIT' in m]
        self.assertEqual(1, len(exit_lines))
        self.assertIn('(Binary content not displayed)', exit_lines[0])

    def test__exit_api_call_still_logs_a_text_body(self):
        "[test_api_view.py] exit_api_call: a JSON body is still shown"
        settings.OPUS_LOG_API_CALLS = 'error'

        @api_view
        def handler(request):
            return HttpResponse('{"a": 1}', content_type='application/json')

        logging.disable(logging.NOTSET)
        try:
            with self.assertLogs('opus_app.apps.tools.app_utils',
                                 level='ERROR') as captured:
                handler(self._request())
        finally:
            logging.disable(logging.CRITICAL)
        exit_lines = [record.getMessage() for record in captured.records
                      if 'EXIT' in record.getMessage()]
        self.assertEqual(1, len(exit_lines))
        self.assertIn('{"a": 1}', exit_lines[0])
