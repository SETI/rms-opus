# from django.shortcuts import render
from dictionary.models import *
from search.views import get_param_info_by_slug

def get_dictionary_info(slug):
    param_info = get_param_info_by_slug(slug)
    definition = {}
    definition['def'] = get_def(param_info.dict_name, param_info.dict_context)
    definition['more_info'] = get_more_info_url(param_info.dict_more_info_name, param_info.dict_more_info_context)
    return definition

def get_def(term, context):

    try:
         definition = Definition.objects.using('dictionary').get(context__name=context,term__term=term).definition
         return html_decode(definition)
    except Definition.DoesNotExist:
        raise False

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