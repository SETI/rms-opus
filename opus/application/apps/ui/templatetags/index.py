from django import template
from dictionary.views import html_decode
register = template.Library()

@register.filter
def index(List, i):
    return List[int(i)]

@register.filter(name='removeTags')
def removeTags(str):
    return html_decode(str)
