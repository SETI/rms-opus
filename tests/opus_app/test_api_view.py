"""Tests for the @api_view decorator in opus_app.apps.tools.app_utils.

These need no database: they drive the decorator with handlers written here, not
with real API endpoints. The 100% branch-coverage gate measures
`src/opus_app/apps/*`, so every branch of the decorator has to be exercised by
the suite that gate reads -- which is why the integration coverage invocation runs
`tests/opus_app` alongside `integration_tests` in a single pass. Living here rather
than in `integration_tests/` is what also puts them in the holdings-free run on the
GitHub-hosted CI.

What is worth pinning here, and why:

* **The status each kind of failure produces.** The decorator is the single place
  that decides what an OPUS API call returns when it goes wrong, so the mapping
  from `Http404` / `Http400Error` / any other exception to 404 / 400 / 500 is the
  whole contract.
* **That the API-call record is closed on every one of those paths.** The
  hand-written pairs this decorator replaces could not guarantee it, and a record
  that is never closed leaks an entry in `_API_START_TIMES` for the life of the
  process.
* **That neither error body can be made to carry markup.** The request path and the
  offending value both reach the page, and the 500 page is built as raw HTML rather
  than through a template, so it escapes for itself while the 400 page relies on the
  template engine. Both are pinned, because "escaped somewhere" is the property that
  matters and the two get it from different places.
* **That an exception Django answers itself is not absorbed.** Turning one into a
  generic 500 would lose both the response Django gives it and, for a
  `SuspiciousOperation`, the `django.security.*` record an operator watches for.
  `Http404` is the live case, raised by handlers throughout the app; the other
  three are guards no handler reaches today, which is what makes a test for them
  worth having.
* **That an unhandled exception is logged with its traceback.** A 500 whose only
  record is "something failed" is what issue #512 is about; the traceback is the
  point of catching it centrally rather than letting it reach Django.
* **Fault injection firing before the handler.** The decorator consults the knobs
  once, in one place, and a handler that was not supposed to run must not have run.
* **That `api_code` is supplied only to handlers that ask for it.** The wrapper
  inspects the handler's signature once, at decoration time, and a mistake there
  would be a TypeError on every request to half the API.
"""

import logging
from unittest import TestCase

from django.conf import settings
from django.core.exceptions import BadRequest, PermissionDenied, SuspiciousOperation
from django.http import Http404, HttpRequest, HttpResponse
from django.test import RequestFactory

from opus_app.apps.tools import app_utils
from opus_app.apps.tools.app_utils import (
    Http400Error,
    api_view,
    http400_bad_limit,
)


class ApiViewTests(TestCase):
    #: Settings these tests move and must put back: two of them are turned all
    #: the way up here, and a suite that does not reset them in its own setUp
    #: would then see every one of its API calls fail.
    """What the `api_view` decorator does around an OPUS API handler."""

    _MUTATED_SETTINGS = (
        'OPUS_FAKE_API_DELAYS',
        'OPUS_FAKE_SERVER_ERROR404_PROBABILITY',
        'OPUS_FAKE_SERVER_ERROR500_PROBABILITY',
        'OPUS_LOG_API_CALLS',
    )

    def setUp(self) -> None:
        """Record the settings this suite moves, then turn off fault injection.

        The saved values go back in `tearDown`: two of these knobs are turned all the
        way up here, and a suite that ran afterwards without resetting them would see
        every one of its API calls fail.
        """
        self._saved_settings = {name: getattr(settings, name) for name in self._MUTATED_SETTINGS}
        settings.OPUS_FAKE_API_DELAYS = 0
        settings.OPUS_FAKE_SERVER_ERROR404_PROBABILITY = 0
        settings.OPUS_FAKE_SERVER_ERROR500_PROBABILITY = 0
        settings.OPUS_LOG_API_CALLS = False
        self.factory = RequestFactory()
        self.maxDiff = None
        logging.disable(logging.CRITICAL)

    def tearDown(self) -> None:
        """Put back every setting this suite moved, and restore logging."""
        for name, value in self._saved_settings.items():
            setattr(settings, name, value)
        logging.disable(logging.NOTSET)

    def _request(self, path: str = '/__api/fake.json') -> HttpRequest:
        """Build a GET request for one path.

        Parameters:
            path: The request path the handler under test will see.

        Returns:
            A request the decorated handlers can be called with.
        """
        return self.factory.get(path)

    def test__api_view_returns_the_handler_response(self) -> None:
        "[test_api_view.py] api_view: a handler that succeeds"

        @api_view
        def handler(request: HttpRequest) -> HttpResponse:
            """Answer 200 with a body the test can recognize."""
            return HttpResponse('ok')

        response = handler(self._request())
        self.assertEqual(200, response.status_code)
        self.assertEqual(b'ok', response.content)

    def test__api_view_passes_url_arguments_through(self) -> None:
        "[test_api_view.py] api_view: positional and keyword URL arguments"

        @api_view
        def handler(request: HttpRequest, size: str, fmt: str | None = None) -> HttpResponse:
            """Answer with the URL arguments given, so the test can read them back."""
            return HttpResponse(f'{size}/{fmt}')

        response = handler(self._request(), 'thumb', fmt='json')
        self.assertEqual(b'thumb/json', response.content)

    def test__api_view_supplies_api_code_when_asked(self) -> None:
        "[test_api_view.py] api_view: a handler that declares api_code gets one"
        seen = []

        @api_view
        def handler(request: HttpRequest, api_code: int) -> HttpResponse:
            """Record the API call number the wrapper supplied, and answer 200."""
            seen.append(api_code)
            return HttpResponse('ok')

        handler(self._request())
        handler(self._request())
        # The API call number increments by exactly one per call, which is what
        # makes it usable for correlating a slow query with its request.
        self.assertEqual([seen[0], seen[0] + 1], seen)

    def test__api_view_omits_api_code_when_not_asked(self) -> None:
        "[test_api_view.py] api_view: a handler with no api_code parameter"

        @api_view
        def handler(request: HttpRequest, **kwargs: str) -> HttpResponse:
            """Report the keyword arguments it got; api_code must not be one."""
            return HttpResponse(repr(sorted(kwargs)))

        response = handler(self._request(), slug='time')
        self.assertEqual(b"['slug']", response.content)

    def test__api_view_reraises_http404(self) -> None:
        "[test_api_view.py] api_view: Http404 reaches Django unchanged"

        @api_view
        def handler(request: HttpRequest) -> HttpResponse:
            """Raise the exception Django answers with its own 404 page."""
            raise Http404('no such thing')

        with self.assertRaisesRegex(Http404, 'no such thing'):
            handler(self._request())

    def test__api_view_turns_http400error_into_a_400(self) -> None:
        "[test_api_view.py] api_view: Http400Error becomes a 400 naming the problem"

        @api_view
        def handler(request: HttpRequest) -> HttpResponse:
            """Raise a bad-request error carrying a message the 400 page must show."""
            raise Http400Error(http400_bad_limit('x', request))

        response = handler(self._request('/api/data.json'))
        self.assertEqual(400, response.status_code)
        body = response.content.decode()
        self.assertIn('Badly formatted limit &quot;x&quot; for /api/data.json', body)
        self.assertIn('/api/data.json', body)

    def test__http400_body_falls_back_to_the_exception_name(self) -> None:
        "[test_api_view.py] api_view: an Http400Error carrying no message"

        @api_view
        def handler(request: HttpRequest) -> HttpResponse:
            """Raise the bad-request class itself, with no message to fall back on."""
            raise Http400Error

        response = handler(self._request())
        self.assertEqual(400, response.status_code)
        self.assertIn('Http400Error', response.content.decode())

    def test__api_view_turns_any_other_exception_into_a_500(self) -> None:
        "[test_api_view.py] api_view: an unhandled exception becomes a 500"

        @api_view
        def handler(request: HttpRequest) -> HttpResponse:
            """Raise an exception the wrapper knows nothing about."""
            raise RuntimeError('boom')

        response = handler(self._request('/api/data.json'))
        self.assertEqual(500, response.status_code)
        self.assertIn(
            'Unspecified internal server error for /api/data.json', response.content.decode()
        )

    def test__api_view_logs_an_unhandled_exception_with_its_traceback(self) -> None:
        "[test_api_view.py] api_view: the 500 log record carries exc_info"

        @api_view
        def handler(request: HttpRequest) -> HttpResponse:
            """Raise an exception the wrapper knows nothing about, to be logged."""
            raise RuntimeError('boom')

        logging.disable(logging.NOTSET)
        try:
            with self.assertLogs('opus_app.apps.tools.app_utils', level='ERROR') as captured:
                handler(self._request())
        finally:
            logging.disable(logging.CRITICAL)
        self.assertEqual(1, len(captured.records))
        record = captured.records[0]
        self.assertIsNotNone(record.exc_info)
        # The handler name is interpolated with %r, like every other value
        # a log message in this app carries, so it is quoted.
        self.assertIn("'handler': Unhandled exception", record.getMessage())

    def test__the_500_body_escapes_the_request_path(self) -> None:
        "[test_api_view.py] api_view: a hostile request path cannot inject HTML"

        # The 500 body is the one error page OPUS builds as raw HTML rather than
        # through a template, so it is the one that has to escape for itself. The
        # path is caller-controlled and lands in the message verbatim.
        @api_view
        def handler(request: HttpRequest) -> HttpResponse:
            """Raise, so the 500 page is built from this test's request path."""
            raise RuntimeError('boom')

        response = handler(self._request('/api/data<script>alert(1)</script>.json'))
        body = response.content.decode()
        self.assertEqual(500, response.status_code)
        self.assertNotIn('<script>', body)
        self.assertIn('&lt;script&gt;alert(1)&lt;/script&gt;', body)
        # The div the Django debug page uses is still real markup, not escaped.
        self.assertIn('<div id="info">', body)

    def test__the_400_body_escapes_the_message(self) -> None:
        "[test_api_view.py] api_view: a hostile value cannot inject HTML into a 400"

        # The 400 page renders through 400.html, so the template engine escapes it.
        # This pins that the escaping happens somewhere, not where: an unescaped
        # 400 would be the same defect as an unescaped 500.
        @api_view
        def handler(request: HttpRequest) -> HttpResponse:
            """Raise a bad-request error whose message is markup the page must escape."""
            raise Http400Error(http400_bad_limit('<script>alert(1)</script>', request))

        response = handler(self._request('/api/data.json'))
        body = response.content.decode()
        self.assertEqual(400, response.status_code)
        self.assertNotIn('<script>', body)
        self.assertIn('&lt;script&gt;alert(1)&lt;/script&gt;', body)

    def test__api_view_handles_a_missing_request(self) -> None:
        "[test_api_view.py] api_view: a handler called with no request at all"

        @api_view
        def handler(request: HttpRequest) -> HttpResponse:
            """Raise, so the wrapper builds its 500 page with no request to name."""
            raise RuntimeError('boom')

        response = handler(None)
        self.assertEqual(500, response.status_code)
        self.assertIn(
            'Unspecified internal server error for (no request)', response.content.decode()
        )

    def test__api_view_injects_a_404_before_the_handler_runs(self) -> None:
        "[test_api_view.py] api_view: OPUS_FAKE_SERVER_ERROR404_PROBABILITY"
        ran = []

        @api_view
        def handler(request: HttpRequest) -> HttpResponse:
            # Never reached: the injection replaces the call.
            """Record that it ran, which the injected 404 must stop from happening."""
            ran.append(True)
            return HttpResponse('ok')

        settings.OPUS_FAKE_SERVER_ERROR404_PROBABILITY = 1
        with self.assertRaisesRegex(Http404, 'Fake HTTP404 error'):
            handler(self._request())
        self.assertEqual([], ran)

    def test__api_view_injects_a_500_before_the_handler_runs(self) -> None:
        "[test_api_view.py] api_view: OPUS_FAKE_SERVER_ERROR500_PROBABILITY"
        ran = []

        @api_view
        def handler(request: HttpRequest) -> HttpResponse:
            # Never reached: the injection replaces the call.
            """Record that it ran, which the injected 500 must stop from happening."""
            ran.append(True)
            return HttpResponse('ok')

        settings.OPUS_FAKE_SERVER_ERROR500_PROBABILITY = 1
        response = handler(self._request())
        self.assertEqual(500, response.status_code)
        self.assertIn('Fake HTTP500 error', response.content.decode())
        self.assertEqual([], ran)

    def test__api_view_notes_an_injected_fault_in_the_api_call_log(self) -> None:
        "[test_api_view.py] api_view: injection with OPUS_LOG_API_CALLS enabled"

        @api_view
        def handler(request: HttpRequest) -> HttpResponse:
            """Answer 200, which the injected fault replaces before this is reached."""
            return HttpResponse('ok')  # Never reached.

        settings.OPUS_LOG_API_CALLS = 'error'
        settings.OPUS_FAKE_SERVER_ERROR500_PROBABILITY = 1
        logging.disable(logging.NOTSET)
        try:
            with self.assertLogs('opus_app.apps.tools.app_utils', level='ERROR') as captured:
                handler(self._request())
        finally:
            logging.disable(logging.CRITICAL)
        self.assertIn('Faking HTTP500 error', [record.getMessage() for record in captured.records])

    def test__api_view_keeps_the_handler_name_and_docstring(self) -> None:
        "[test_api_view.py] api_view: the wrapper is transparent to introspection"

        @api_view
        def api_something(request: HttpRequest) -> HttpResponse:
            "A docstring Sphinx would have to find."
            return HttpResponse('ok')  # Never called.

        self.assertEqual('api_something', api_something.__name__)
        self.assertEqual('A docstring Sphinx would have to find.', api_something.__doc__)

    def test__api_view_reraises_what_django_answers_itself(self) -> None:
        "[test_api_view.py] api_view: SuspiciousOperation and friends are not absorbed"
        # Django turns each of these into a specific response of its own, and
        # SuspiciousOperation also reaches the django.security.* logger; a generic
        # 500 here would lose both. No handler in the app raises one today -
        # build_absolute_uri's DisallowedHost looks like a live case but
        # CommonMiddleware rejects a spoofed Host before any view runs - so this
        # test is what stops the guard from silently rotting.
        for exception_class in (BadRequest, PermissionDenied, SuspiciousOperation):
            with self.subTest(exception_class=exception_class.__name__):

                @api_view
                def handler(
                    request: HttpRequest, raises: type[Exception] = exception_class
                ) -> HttpResponse:
                    """Raise the exception class this round of the loop is checking."""
                    raise raises('nope')

                with self.assertRaises(exception_class):
                    handler(self._request())

    def test__api_view_closes_the_api_call_record_on_every_path(self) -> None:
        "[test_api_view.py] api_view: no path leaves an entry in _API_START_TIMES"

        @api_view
        def ok_handler(request: HttpRequest) -> HttpResponse:
            """Leave through the wrapper's success path."""
            return HttpResponse('ok')

        @api_view
        def http404_handler(request: HttpRequest) -> HttpResponse:
            """Leave through the wrapper's re-raise path."""
            raise Http404('gone')

        @api_view
        def http400_handler(request: HttpRequest) -> HttpResponse:
            """Leave through the wrapper's 400 path."""
            raise Http400Error('bad')

        @api_view
        def boom_handler(request: HttpRequest) -> HttpResponse:
            """Leave through the wrapper's 500 path."""
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

    def test__exit_api_call_does_not_decode_a_binary_body(self) -> None:
        "[test_api_view.py] exit_api_call: an archive is not decoded to log 240 chars"
        settings.OPUS_LOG_API_CALLS = 'error'

        @api_view
        def handler(request: HttpRequest) -> HttpResponse:
            """Answer with bytes that are not text, so decoding them would fail."""
            return HttpResponse(b'PK\x03\x04\xff\xfe not text', content_type='application/zip')

        logging.disable(logging.NOTSET)
        try:
            with self.assertLogs('opus_app.apps.tools.app_utils', level='ERROR') as captured:
                handler(self._request())
        finally:
            logging.disable(logging.CRITICAL)
        messages = [record.getMessage() for record in captured.records]
        exit_lines = [m for m in messages if 'EXIT' in m]
        self.assertEqual(1, len(exit_lines))
        self.assertIn('(Binary content not displayed)', exit_lines[0])

    def test__exit_api_call_still_logs_a_text_body(self) -> None:
        "[test_api_view.py] exit_api_call: a JSON body is still shown"
        settings.OPUS_LOG_API_CALLS = 'error'

        @api_view
        def handler(request: HttpRequest) -> HttpResponse:
            """Answer with a short JSON body, which the call log is expected to show."""
            return HttpResponse('{"a": 1}', content_type='application/json')

        logging.disable(logging.NOTSET)
        try:
            with self.assertLogs('opus_app.apps.tools.app_utils', level='ERROR') as captured:
                handler(self._request())
        finally:
            logging.disable(logging.CRITICAL)
        exit_lines = [
            record.getMessage() for record in captured.records if 'EXIT' in record.getMessage()
        ]
        self.assertEqual(1, len(exit_lines))
        self.assertIn('{"a": 1}', exit_lines[0])
