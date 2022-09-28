from django import template
import json

register = template.Library()

@register.filter(name='json_dumps')
def json_dumps(data):
    "Convert the given python object into a json string."
    return json.dumps(data)
