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
        self.whitespace = re.compile(r'^\s*\n', re.MULTILINE)
        self.get_response = get_response
        self.whitespace_lead = re.compile(r'^\s+', re.MULTILINE)
        self.whitespace_trail = re.compile(r'\s+$', re.MULTILINE)


    def __call__(self, request):
        response = self.get_response(request)
        if "text" in response['Content-Type']:
            # Use next line instead to avoid failure on cached / HTTP 304 NOT MODIFIED responses without Content-Type
            # if response.status_code == 200 and "text" in response['Content-Type']:
            decoded = response.content.decode()
            orig_decoded = decoded
            if decoded.startswith('<!--NOSTRIP-->'):
                decoded = decoded[14:]
            else:
                decoded = self.whitespace_lead.sub('', decoded)
                decoded = self.whitespace_trail.sub('\n', decoded)
                decoded = self.whitespace.sub('', decoded)
            if decoded != orig_decoded:
                response.content = decoded.encode()
        return response
