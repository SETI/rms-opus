"""
Tightens up response content by removed superflous line breaks and whitespace.
By Doug Van Horn

---- CHANGES ----
v1.1 - 31st May 2011
Cal Leeming [Simplicity Media Ltd]
Modified regex to strip leading/trailing white space from every line, not just those with blank \n.

---- TODO ----
* Ensure whitespace isn't stripped from within <pre> or <code> or <textarea> tags.

"""

import re

class StripWhitespaceMiddleware(object):
    """
    Strips leading and trailing whitespace from response content.
    """

    def __init__(self, get_response):
        self.whitespace = re.compile('^\s*\n', re.MULTILINE)
        self.get_response = get_response
        self.whitespace_lead = re.compile('^\s+', re.MULTILINE)
        self.whitespace_trail = re.compile('\s+$', re.MULTILINE)


    def __call__(self, request):
        response = self.get_response(request)
        if "text" in response['Content-Type']:
        #Use next line instead to avoid failure on cached / HTTP 304 NOT MODIFIED responses without Content-Type
        #if response.status_code == 200 and "text" in response['Content-Type']:
            if hasattr(self, 'whitespace_lead'): # pragma: no cover
                response.content = self.whitespace_lead.sub('', response.content.decode()).encode()
            if hasattr(self, 'whitespace_trail'): # pragma: no cover
                response.content = self.whitespace_trail.sub('\n', response.content.decode()).encode()
            if hasattr(self, 'whitespace'): # pragma: no cover
                response.content = self.whitespace.sub('', response.content.decode()).encode()
            return response
        else:
            return response
