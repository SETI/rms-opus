from django import template
from dictionary.views import html_decode
register = template.Library()

import logging
log = logging.getLogger(__name__)


@register.filter(name='removeTags')
def removeTags(str):
    log.info("in filter = str %s", str)
    return html_decode(str)
