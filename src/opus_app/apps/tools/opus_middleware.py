"""Tighten up response content by removing superfluous line breaks and whitespace.

By Doug Van Horn

---- CHANGES ----
v1.1 - 31st May 2011
Cal Leeming [Simplicity Media Ltd]
Modified regex to strip leading/trailing white space from every line, not just
those with blank \n.

---- TODO ----
* Ensure whitespace isn't stripped from within <pre> or <code> or <textarea> tags.

"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

    from django.http import HttpRequest, HttpResponse


class StripWhitespaceMiddleware:
    """Strips leading and trailing whitespace from response content."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        """Remember the rest of the chain and compile the patterns to strip with.

        Parameters:
            get_response: What produces the response this middleware rewrites,
                which is the next handler in the middleware chain.
        """
        self.whitespace = re.compile(r'^\s*\n', re.MULTILINE)
        self.get_response = get_response
        self.whitespace_lead = re.compile(r'^\s+', re.MULTILINE)
        self.whitespace_trail = re.compile(r'\s+$', re.MULTILINE)


    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Answer a request, stripping the whitespace out of a text response.

        Parameters:
            request: The request being served.

        Returns:
            The response the rest of the chain produced. A response whose content
            type mentions `text` has the leading whitespace of every line removed,
            the trailing whitespace of every line replaced with a newline, and its
            blank lines dropped; a response whose content begins with
            `<!--NOSTRIP-->` has that marker removed and nothing else touched.

        Raises:
            KeyError: If the response carries no Content-Type header at all, which
                a cached 304 response does not.
        """
        response = self.get_response(request)
        if "text" in response['Content-Type']:
            # Use next line instead to avoid failure on cached / HTTP 304 NOT MODIFIED responses without Content-Type
            # if response.status_code == 200 and "text" in response['Content-Type']:
            decoded = response.content.decode()
            orig_decoded = decoded
            if decoded.startswith('<!--NOSTRIP-->'):
                decoded = decoded[14:]
            else:
                decoded = self.whitespace_lead.sub('', decoded)
                decoded = self.whitespace_trail.sub('\n', decoded)
                decoded = self.whitespace.sub('', decoded)
            if decoded != orig_decoded:
                response.content = decoded.encode()
        return response
