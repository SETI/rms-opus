# from django.shortcuts import render
from dictionary.models import *


import logging
log = logging.getLogger(__name__)


def get_def(term, context):

    try:
         definition = Definition.objects.using('dictionary').get(context__name=context,term__term=term).definition
         return html_decode(definition)
    except Definition.DoesNotExist:
        if not term:
            term = ''
        if not context: 
            context = ''
        log.debug("could not find dictionary def for %s in %s" % (term, context))
        return False

def get_more_info_url(term, context):

    if get_def(term, context):
        return "http://pds-rings.seti.org/dictionary/index.html?term=%s&context=%s" % (term, context)
    else:
        return False

def html_decode(s):
    """
    Returns the ASCII decoded version of the given HTML string. This does
    NOT remove normal HTML tags like <p>.
    """
    htmlCodes = (
            ("'", '&#39;'),
            ('"', '&quot;'),
            ('>', '&gt;'),
            ('<', '&lt;'),
            ('&', '&amp;')
        )
    for code in htmlCodes:
        s = s.replace(code[1], code[0])
    return s