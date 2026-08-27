"""Tests for StripWhitespaceMiddleware.

These need no database: the middleware is driven with a handler written here rather
than through a real endpoint. They live in `tests/opus_app` for the reason
`test_api_view.py` gives -- the 100% branch-coverage gate measures
`src/opus_app/apps/*`, so every branch has to be reached by the suite that gate
reads, and living here also puts them in the holdings-free run.

What is worth pinning, and why:

* **The `<!--NOSTRIP-->` escape hatch.** It is the only way a view can say "return my
  content exactly as I wrote it", and until this suite existed the only thing
  exercising it was one template. A template that stops using it should not silently
  retire a documented behavior of the middleware.
* **That a response with no `Content-Type` raises.** The middleware's docstring says
  so, and the alternative reading -- that such a response passes through untouched --
  is what a reader would otherwise assume.
"""

from __future__ import annotations

import pytest
from django.http import HttpRequest, HttpResponse
from django.test import RequestFactory

from opus_app.apps.tools.opus_middleware import StripWhitespaceMiddleware

#: Content with whitespace of every kind the middleware claims to remove: an indented
#: line, a blank line, and trailing spaces inside a tag it must not reach into.
SPACED = '<html>\n    <body>\n\n        <p>  Text  </p>\n    </body>\n</html>\n'


def _run(response: HttpResponse) -> HttpResponse:
    """Pass one response through the middleware.

    Parameters:
        response: What the rest of the chain produces.

    Returns:
        What the middleware answers with.
    """
    def chain(_request: HttpRequest) -> HttpResponse:
        return response

    return StripWhitespaceMiddleware(chain)(RequestFactory().get('/'))


def test_strips_whitespace_from_a_text_response() -> None:
    """Leading and trailing whitespace goes, and so do the blank lines."""
    response = _run(HttpResponse(SPACED, content_type='text/html'))
    assert (response.content.decode()
            == '<html>\n<body>\n<p>  Text  </p>\n</body>\n</html>\n')


def test_nostrip_marker_is_removed_and_nothing_else_is_touched() -> None:
    """A response opting out keeps its content exactly, minus the marker itself."""
    response = _run(HttpResponse('<!--NOSTRIP-->' + SPACED, content_type='text/html'))
    assert response.content.decode() == SPACED


def test_a_response_that_needs_no_change_is_left_alone() -> None:
    """Content the patterns do not match is not re-encoded."""
    response = _run(HttpResponse('<p>x</p>', content_type='text/html'))
    assert response.content == b'<p>x</p>'


def test_a_non_text_response_is_untouched() -> None:
    """Only a response whose content type mentions text is rewritten."""
    response = _run(HttpResponse(SPACED, content_type='application/zip'))
    assert response.content.decode() == SPACED


def test_a_response_without_a_content_type_raises() -> None:
    """The middleware reads Content-Type unconditionally, as its docstring says.

    This pins current behaviour, it does not endorse it: a 304 carries no
    Content-Type, so one reaching this middleware raises rather than passing
    through. The source has carried a commented-out status-code guard for that
    case for years. Fixing it changes production response handling, which is out
    of scope for a documentation PR -- issue #1475 tracks it, and this test is
    what will fail, informatively, when it is fixed.
    """
    response = HttpResponse(status=304)
    del response.headers['Content-Type']
    with pytest.raises(KeyError):
        _run(response)
