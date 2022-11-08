from django import template

import urllib

register = template.Library()

@register.filter(name='encode_value')
def encode_value(value):
    "Encode a search value for use in an OPUS URL."
    if value is None: # pragma: no cover - not currently used
        value = 'NULL'
    return urllib.parse.quote_plus(value, "-_.!~*'()")
