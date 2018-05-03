# from django.shortcuts import render
from dictionary.models import *
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse

import string

import logging
log = logging.getLogger(__name__)

def get_def(term, context):
    """ get a dictionary definition for tool tips

        """
    try:
        definition = Definition.objects.using('dictionary').select_related().filter(context=context,term=term).values('definition', 'term', 'context__description').first()
        #definition = Definition.objects.using('dictionary').get(context=context,term=term).values('definition', 'term', 'import_date', 'context__description')
        return definition
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
    """
        Produce an alphabetical list of definitions on click of menu/alpha char
    """
    definitionList = Definition.objects.using('dictionary').select_related().filter(term__istartswith=alpha).values('definition', 'term', 'import_date', 'context__description').order_by('term')
    return JsonResponse(list(definitionList), safe=False)

def display_definitions(request):
    alphabetlist = list(string.ascii_uppercase)
    return render(request, 'dictionary/dictionary.html', {'alphabetlist':alphabetlist})

def search_definitions(request, slug):
    """
        User can search the definition database for words w/in the definitions.
        Not currently enabled to search on term
    """
    try:
        definitionList = Definition.objects.using('dictionary').select_related("context").filter(definition__icontains=slug).values('definition', 'term', 'import_date', 'context__description').order_by('term')
        #log.info(definitionList.query)
        return JsonResponse(list(definitionList), safe=False)
    except Definition.DoesNotExist:
        log.info(definitionList.query)
        return JsonResponse({"error":"Search string '"+slug+"' not found"})

def test_get_def(request, term, context):
    definition = get_def(term, context)
    return JsonResponse(list(definition), safe=False)

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
