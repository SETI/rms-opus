# from django.shortcuts import render
from dictionary.models import *


import logging
log = logging.getLogger(__name__)


def get_def(term, context):
    """ get a dictionary definition
        the dictionary is a database that is more or less a database normalization
        of the PDS Data Dictionary, a datad one. The django app that ran its
        admin broke, but could be revived. you can kindof get an idea of how
        it worked by looking at its schema

            desc dicitonary;  # mysql

        """
    try:
         definition = Definition.objects.using('dictionary').get(context__name=context,term__term=term).definition
         return html_decode(definition)
    except Definition.DoesNotExist:
        return False

def get_more_info_url(term, context):
    """
        given a term and context, return the url of the page for this definition.
        the dictionary database could also be a web interface. It was a list of
        terms in each context, clickable to definitions and other info about the
        term. A way to navigate and extend the PDS Data Dictionary.
    """
    if get_def(term, context):
        return "http://pds-rings.seti.org/dictionary/index.php?term=%s&context=%s" % (term, context)
    else:
        return False

def html_decode(s):
    """
    Returns the ASCII decoded version of the given HTML string. This does
    NOT remove normal HTML tags like <p>.

    this seems like a util! #todo 
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
