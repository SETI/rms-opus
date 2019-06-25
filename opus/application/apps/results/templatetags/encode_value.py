from django import template

register = template.Library()

@register.filter(name='encode_value')
def encode_value(value):
    "Encode a search value for use in an OPUS URL."
    value = str(value).replace(' ', '%20').replace('+', '%2B')
    return value
