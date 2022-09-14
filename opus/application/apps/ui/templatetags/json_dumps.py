from django import template
import json

register = template.Library()

@register.filter(name='json_dumps')
def json_dumps(data):
    "Convert python object into json string"
    return json.dumps(data)
