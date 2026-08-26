"""Requests with a piece missing, for the API views' "no request" guard tests.

Every OPUS API view starts by checking that what it was handed looks like a request:
`get_reqno`, `url_to_search_params` and the rest read `request.GET`, and the error
pages read `request.META`, so a view called with either one absent answers
`Internal error (No request was provided)` rather than raising `AttributeError`
somewhere further in. Django itself never builds such a request -- the views are
guarded because this suite also calls them directly, and these are the requests that
hold the guard in place.

Building the malformed request here rather than at each test is what keeps the type
suppression to one site with one reason: assigning None to `META` or `GET` is
precisely the type error the guard exists to survive, so the checker is right about
it everywhere and there is nothing to fix at the call sites.
"""

from django.http import HttpRequest
from django.test import RequestFactory


def request_without_meta(factory: RequestFactory, path: str) -> HttpRequest:
    """A GET request whose `META` is None.

    Parameters:
        factory: The suite's request factory.
        path: The request path the view will report in its error.

    Returns:
        The request, ready to be passed straight to a view.
    """
    request = factory.get(path)
    request.META = None  # type: ignore[assignment]
    return request


def request_without_get(factory: RequestFactory, path: str) -> HttpRequest:
    """A GET request whose `GET` query mapping is None.

    Parameters:
        factory: The suite's request factory.
        path: The request path the view will report in its error.

    Returns:
        The request, ready to be passed straight to a view.
    """
    request = factory.get(path)
    request.GET = None  # type: ignore[assignment]
    return request
