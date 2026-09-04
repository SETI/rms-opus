"""The `encode_value` template filter.

The results templates load this filter to turn a metadata value into the query
string of an OPUS search URL, so that a link built around the value searches for
that exact value.
"""

import urllib

from django import template

register = template.Library()


@register.filter(name='encode_value')
def encode_value(value: str | None) -> str:
    """Encode a search value for use in an OPUS URL.

    Parameters:
        value: The value to encode, or None.

    Returns:
        The value percent-encoded for use in a URL, with spaces written as `+`
        and the characters `-_.!~*'()` left alone. None is encoded as the text
        `NULL`.
    """
    if value is None:  # pragma: no cover - not currently used
        value = 'NULL'
    return urllib.parse.quote_plus(value, "-_.!~*'()")
