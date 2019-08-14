from django import template
from django.template.defaultfilters import stringfilter
register = template.Library()

@register.filter
@stringfilter
def prettify_str(value):
    """
    Replace underscore with a space and capitalize every word in a string
    """
    return value.replace('_', ' ').title()
