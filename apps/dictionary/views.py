# from django.shortcuts import render
from dictionary.models import *
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse

import string

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

def get_definition_list(request, alpha):
    definitionList = Definition.objects.using('dictionary').select_related().filter(term__term__istartswith=alpha).values('definition', 'term__term_nice', 'term__import_date', 'context__description', 'context__name').order_by('term__term')
    return JsonResponse(list(definitionList), safe=False)

def display_definitions(request):
    alphabetlist = list(string.ascii_uppercase)
    return render(request, 'dictionary/dictionary.html', {'alphabetlist':alphabetlist})

def search_definitions(request, slug):
    try:
        definitionList = Definition.objects.using('dictionary').select_related().filter(definition__icontains=slug).values('definition', 'term__term_nice', 'term__import_date', 'context__description', 'context__name').order_by('term__term')
        return JsonResponse(list(definitionList), safe=False)
    except Definition.DoesNotExist:
        return JsonResponse({"error":"Search string '"+slug+"' not found"})

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
