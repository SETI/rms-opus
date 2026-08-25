################################################################################
#
# tools/app_utils.py
#
################################################################################

import csv
import datetime
import functools
import importlib.metadata
import inspect
import json
import logging
import random
import string
import time
from urllib.parse import quote

from django.conf import settings
from django.core.exceptions import (
    BadRequest,
    MultipleObjectsReturned,
    ObjectDoesNotExist,
    PermissionDenied,
    SuspiciousOperation,
)
from django.http import Http404, HttpResponse, HttpResponseServerError
from django.template import loader
from django.utils.html import escape

from opus_app.apps.search.models import ObsGeneral

log = logging.getLogger(__name__)


def csv_response(filename, data, column_names=None):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename={filename}.csv'
    writer = csv.writer(response)
    if column_names:
        writer.writerow(column_names)
    writer.writerows(data)
    return response

def json_response(data):
    return HttpResponse(json.dumps(data), content_type='application/json')

def download_filename(opus_id, file_type):
    """Create a unique filename for a user's cart or CSV file."""
    random_ascii = random.choice(string.ascii_letters).lower()
    timestamp = "T".join(str(datetime.datetime.now()).split(' '))
    # Windows doesn't like ':' in filenames
    timestamp = timestamp.replace(':', '-')
    # And we don't want a period to confuse the suffix later
    timestamp = timestamp.replace('.', '-')
    if file_type is None: # pragma: no cover - future use
        file_type = ''
    if file_type: # pragma: no cover - future use
        file_type += '-'
    root = f'pdsrms-{timestamp}-{file_type}{random_ascii}'
    if opus_id:
        root += f'_{opus_id}'
    return root

def strip_numeric_suffix(name):
    """Strip a trailing 1 or 2, if any, from a slug."""
    if len(name) > 0 and name[-1] in ['1', '2']:
        return name[:-1]
    return name

def get_numeric_suffix(name):
    """Get a trailing 1 or 2, if any, from a slug."""
    if len(name) > 0 and name[-1] in ['1', '2']: # pragma: no cover -
        # Generalization not currently needed
        return name[-1]
    return None # pragma: no cover - see above

def sort_dictionary(old_dict):
    """Sort a dictionary by key."""
    new_dict = {}
    for key in sorted(old_dict.keys()):
        new_dict[key] = old_dict[key]
    return new_dict

def get_session_id(request):
    """Get the current session id, or create one if none available.

    The caller can override the sessionid (only for internal testing
    purposes) by specifying the __sessionid=<S> parameter."""
    session_id = None
    if request.GET is not None: # pragma: no cover - only happens with real web browser
        session_id = request.GET.get('__sessionid', None)
    if session_id is None: # pragma: no cover - only happens with real web browser
        if not request.session.get('has_session'):
            request.session['has_session'] = True
        if not request.session.session_key:
            request.session.create()
        session_id = request.session.session_key
    return session_id

def get_reqno(request):
    """Get the reqno, if any, and return it as an int if possible."""
    reqno = request.GET.get('reqno', None)
    try:
        reqno = int(reqno)
        if reqno < 0:
            reqno = None
    except Exception:
        reqno = None
    return reqno


_API_CALL_NUMBER = 0
_API_START_TIMES = {}

def enter_api_call(name, request, kwargs=None):
    """Record the entry into an API."""
    global _API_CALL_NUMBER
    _API_CALL_NUMBER += 1
    if settings.OPUS_LOG_API_CALLS: # pragma: no cover - internal debugging
        s = 'API ' + str(_API_CALL_NUMBER) + ' '
        if request and request.path:
            s += request.path
        if kwargs:
            s += ' ' + str(kwargs)
        if request and request.GET:
            s += ' ' + json.dumps(request.GET, sort_keys=True,
                                  indent=4,
                                  separators=(',', ': '))
        getattr(log, settings.OPUS_LOG_API_CALLS.lower())(s)
    _API_START_TIMES[_API_CALL_NUMBER] = time.time()
    return _API_CALL_NUMBER

def exit_api_call(api_code, ret):
    """Record the exit from an API."""
    end_time = time.time()
    delay_amount = 0.
    if settings.OPUS_FAKE_API_DELAYS is not None: # pragma: no cover - internal debugging
        if settings.OPUS_FAKE_API_DELAYS > 0:
            delay_amount = settings.OPUS_FAKE_API_DELAYS / 1000.
        elif settings.OPUS_FAKE_API_DELAYS < 0:
            delay_amount = random.uniform(0.,
                                          -settings.OPUS_FAKE_API_DELAYS/1000.)
    if settings.OPUS_LOG_API_CALLS: # pragma: no cover - internal debugging
        s = 'API ' + str(api_code) + ' EXIT'
        if api_code in _API_START_TIMES: # pragma: no cover - internal debugging
            s += ' ' + str(end_time-_API_START_TIMES[api_code]) + ' secs'
        ret_str = str(ret)
        ret_str = ' '.join(ret_str.split()) # Compress whitespace
        s += ': ' + ret_str[:240]
        if isinstance(ret, HttpResponse):
            # An archive download is megabytes of binary; decoding it to log 240
            # characters would cost more than the log line is worth.
            if ret.get('Content-Type', '').startswith(('text/',
                                                       'application/json')):
                try:
                    s += '\n' + ret.content.decode()[:240]
                except Exception:
                    s += '\n(Unable to display)'
            else:
                s += '\n(Binary content not displayed)'
        if delay_amount: # pragma: no cover - internal debugging
            s += f'\nDELAYING RETURN {delay_amount} SECONDS'
        getattr(log, settings.OPUS_LOG_API_CALLS.lower())(s)
    _API_START_TIMES.pop(api_code, None)
    if delay_amount: # pragma: no cover - internal debugging
        time.sleep(delay_amount)


################################################################################
#
# THE API VIEW DECORATOR
#
################################################################################

class Http400Error(Exception):
    """Raised by an API handler when the request itself is malformed.

    The `api_view` decorator turns it into an HTTP 400 response whose body is the
    OPUS error page, explained by the message the exception was constructed with
    (or by the class name, when it was constructed without one).

    Raise it for anything the caller supplied that is missing, unparseable, or
    unknown - a bad slug, a non-numeric limit, an unknown unit - as opposed to
    `django.http.Http404`, which means a resource named in the URL path does not
    exist.
    """


#: The error page rendered for an HTTP 400, alongside Django's own `404.html`.
_HTTP400_TEMPLATE_NAME = '400.html'

#: Exceptions Django's own handler turns into a specific response, which the
#: decorator must therefore not absorb into a generic 500 - `SuspiciousOperation`
#: also reaches the `django.security.*` logger an operator watches.
#:
#: `Http404` is the live one: the handlers raise it 49 times and it is how every
#: 404 in the API is produced. The other three are guards. No handler raises them
#: today, and the one path that looked live is not: `HttpRequest.build_absolute_uri`
#: raises `DisallowedHost` on a spoofed Host header, but
#: `CommonMiddleware.process_request` calls `get_host()` first and rejects the
#: request before any view runs. `MultiPartParserError`, which Django also handles,
#: is deliberately absent - OPUS reads no request body, so nothing can produce it.
_DJANGO_HANDLED_EXCEPTIONS = (Http404, BadRequest, PermissionDenied,
                              SuspiciousOperation)


def _request_path(r):
    """Return the request path to name in an error message.

    Parameters:
        r: An `HttpRequest`, a path already given as a string, or None when a
            handler was called without a request at all.

    Returns:
        The request's path, the given string unchanged, or a placeholder when
        there is no request.
    """
    if r is None:
        return '(no request)'
    if isinstance(r, str):
        return r
    return r.path


def _http400_response(request, exception):
    """Render the OPUS error page for an HTTP 400.

    This mirrors what Django's own `page_not_found` view does for `Http404`: the
    page names the request path and the exception's message, falling back to the
    exception's class name when it carries no message.

    Parameters:
        request: The request being answered, or None.
        exception: The `Http400Error` describing what was wrong with the request.

    Returns:
        An `HttpResponse` with status 400 holding the rendered error page.
    """
    message = exception.args[0] if exception.args else None
    if not isinstance(message, str):
        message = type(exception).__name__
    context = {'request_path': quote(_request_path(request)),
               'exception': message}
    body = loader.render_to_string(_HTTP400_TEMPLATE_NAME, context, request)
    return HttpResponse(body, content_type='text/html; charset=utf-8', status=400)


def _log_injected_fault(kind):
    """Note an injected fault in the API-call log, if that log is enabled.

    Parameters:
        kind: The kind of fault being injected, for the log line.
    """
    if settings.OPUS_LOG_API_CALLS:
        getattr(log, settings.OPUS_LOG_API_CALLS.lower())(f'Faking {kind} error')


def _injected_fault_response(request):
    """Return an injected fault, if the fault-injection knobs call for one.

    `OPUS_FAKE_SERVER_ERROR404_PROBABILITY` and
    `OPUS_FAKE_SERVER_ERROR500_PROBABILITY` are debugging knobs that make a
    random fraction of API calls fail, so the front end's error handling can be
    exercised against a live server. They are consulted once per API call, before
    the handler runs.

    Parameters:
        request: The request being answered, or None.

    Returns:
        An `HttpResponse` with status 500 when a 500 was injected, or None when no
        fault was injected and the handler should run.

    Raises:
        Http404: When a 404 was injected.
    """
    if random.random() < settings.OPUS_FAKE_SERVER_ERROR404_PROBABILITY:
        _log_injected_fault('HTTP404')
        raise Http404(HTTP404_FAKE_ERROR(request))
    if random.random() < settings.OPUS_FAKE_SERVER_ERROR500_PROBABILITY:
        _log_injected_fault('HTTP500')
        return HttpResponseServerError(HTTP500_FAKE_ERROR(request))
    return None


def api_view(handler):
    """Wrap an OPUS API handler with the standard entry, exit, and error handling.

    The decorated function is what `urls.py` routes to. Around every call the
    wrapper:

    * records the call with `enter_api_call` and its result with `exit_api_call`,
      which is also where the `OPUS_FAKE_API_DELAYS` knob delays the response;
    * consults the fault-injection knobs before the handler runs, so an injected
      404 or 500 replaces the call entirely;
    * turns an `Http400Error` raised anywhere inside the handler into an HTTP 400
      response; and
    * turns any other unhandled exception into an HTTP 500 response, logged with
      its traceback.

    An exception Django's own handler answers specifically - `Http404`,
    `BadRequest`, `PermissionDenied`, `SuspiciousOperation` - is re-raised rather
    than absorbed, so a 404 keeps both the status and the body it has always had
    and a suspicious request still reaches the `django.security.*` logger.

    The handler is called with the request and the URL's own keyword arguments.
    A handler that needs the API call number - to pass on to the search helpers,
    which log against it - declares an `api_code` parameter, and the wrapper
    supplies it as an extra keyword argument; a handler that does not declare one
    is called without it.

    Parameters:
        handler: The API handler to wrap. Its `__name__` is the name the call is
            logged under.

    Returns:
        The wrapped view function.
    """
    wants_api_code = 'api_code' in inspect.signature(handler).parameters

    @functools.wraps(handler)
    def wrapper(request, *args, **kwargs):
        api_code = enter_api_call(handler.__name__, request, kwargs)
        if wants_api_code:
            kwargs['api_code'] = api_code
        try:
            ret = _injected_fault_response(request)
            if ret is None:
                ret = handler(request, *args, **kwargs)
        except _DJANGO_HANDLED_EXCEPTIONS as exc:
            exit_api_call(api_code, exc)
            raise
        except Http400Error as exc:
            ret = _http400_response(request, exc)
            exit_api_call(api_code, ret)
            return ret
        except Exception:
            log.exception('%s: Unhandled exception', handler.__name__)
            ret = HttpResponseServerError(HTTP500_INTERNAL_ERROR(request))
            exit_api_call(api_code, ret)
            return ret
        exit_api_call(api_code, ret)
        return ret

    return wrapper


################################################################################
#
# MISCELLANEOUS SUPPORT ROUTINES
#
################################################################################

def is_old_format_ring_obs_id(s):
    """Return True if the string is a valid old-format ringobsid."""
    return len(s) > 2 and (s[0] == '_' or s[1] == '_')

def convert_ring_obs_id_to_opus_id(ring_obs_id, force_ring_obs_id_fmt=False):
    """Given an old-format ringobsid, return the new opusid."""
    if (not force_ring_obs_id_fmt and
        not is_old_format_ring_obs_id(ring_obs_id)):
        return ring_obs_id
    try:
        return ObsGeneral.objects.get(ring_obs_id=ring_obs_id).opus_id
    except ObjectDoesNotExist:
        log.error('No matching RING_OBS_ID for %r', ring_obs_id)
        return None
    except MultipleObjectsReturned: # pragma: no cover - import error
        log.exception('More than one matching RING_OBS_ID for %r', ring_obs_id)
        return (ObsGeneral.objects.filter(ring_obs_id=ring_obs_id)
                .first().opus_id)

def get_mult_name(param_qualified_name):
    """Returns mult widget foreign key table name."""
    return 'mult_' + '_'.join(param_qualified_name.split('.'))

def get_git_version():
    """Return the version of the OPUS distribution this site is running.

    It identifies the deployed code on the About page and is the cache-busting
    suffix on every static asset URL, so it changes exactly when a new release is
    installed.

    Returns:
        The version of the installed ``rms-opus`` distribution, for example
        ``3.23.0``.

    Raises:
        importlib.metadata.PackageNotFoundError: If ``rms-opus`` is not installed,
            which means the site is being run from a source tree that was never
            installed and cannot serve static assets either.
    """
    return importlib.metadata.version('rms-opus')

def cols_to_slug_list(slugs):
    if not slugs:
        return []
    return slugs.split(',')


################################################################################
#
# ERROR MESSAGES
#
# The message text an error page shows the user. The HTTP400_/HTTP404_/HTTP500_
# prefix records which status the message is raised with: an HTTP400_ message
# accompanies `Http400Error` (the request itself was malformed), an HTTP404_
# message accompanies `Http404` (something named in the URL path does not exist),
# and an HTTP500_ message accompanies `HttpResponseServerError`. Each takes the
# request, or a path given as a string when the request is not available.
#
################################################################################

def HTTP404_NO_REQUEST(s):
    """The handler was called with no request, or one with no GET or META."""
    return f'Internal error (No request was provided) for {_request_path(s)}'

def HTTP400_BAD_OR_MISSING_REQNO(r):
    """The reqno parameter is absent or is not a non-negative integer."""
    return f'Internal error (Bad or missing reqno) for {_request_path(r)}'

def HTTP400_MISSING_OPUS_ID(r):
    """An OPUS ID is required but none was given."""
    return f'Missing OPUSID for {_request_path(r)}'

def HTTP404_UNKNOWN_FORMAT(fmt, r):
    """The requested return format is not one this endpoint can produce."""
    return f'Internal error (Unknown return format "{fmt}") for {_request_path(r)}'

def HTTP400_BAD_OR_MISSING_RANGE(r):
    """The range parameter is absent or is not a pair of OPUS IDs."""
    return f'Internal error (Bad or missing range) for {_request_path(r)}'

def HTTP400_BAD_DOWNLOAD(download, r):
    """The download parameter is not 0 or 1."""
    return f'Badly formatted download argument "{download}" for {_request_path(r)}'

def HTTP400_BAD_RECYCLEBIN(recyclebin, r):
    """The recyclebin parameter is not 0 or 1."""
    return (f'Internal error (Badly formatted recyclebin argument '
            f'"{recyclebin}") for {_request_path(r)}')

def HTTP400_BAD_COLLAPSE(collapse, r):
    """The collapse parameter is not an integer."""
    return f'Badly formatted collapse argument "{collapse}" for {_request_path(r)}'

def HTTP400_BAD_LIMIT(limit, r):
    """The limit parameter is not an integer in the permitted range."""
    return f'Badly formatted limit "{limit}" for {_request_path(r)}'

def HTTP400_BAD_STARTOBS(startobs, r):
    """The startobs parameter is not an integer."""
    return f'Badly formatted startobs "{startobs}" for {_request_path(r)}'

def HTTP400_BAD_PAGENO(pageno, r):
    """The page parameter is not an integer."""
    return f'Badly formatted page number "{pageno}" for {_request_path(r)}'

def HTTP400_BAD_OFFSET(offset, r):
    """The offset computed from startobs or page is outside the permitted range."""
    return f'Bad computed offset "{offset}" for {_request_path(r)}'

def HTTP400_SEARCH_PARAMS_INVALID(r):
    """The search parameters in the query string could not be parsed."""
    return f'Search parameters invalid for {_request_path(r)}'

def HTTP400_UNKNOWN_SLUG(slug, r):
    """A metadata field slug the caller supplied does not exist."""
    if slug is None:
        return f'Unknown metadata field slug for {_request_path(r)}'
    return f'Unknown metadata field "{slug}" for {_request_path(r)}'

def HTTP400_UNKNOWN_UNITS(units, slug, r):
    """The requested units are not valid for the given metadata field."""
    return (f'Unknown units "{units}" for metadata field "{slug}" for '
            f'{_request_path(r)}')

def HTTP404_UNKNOWN_RING_OBS_ID(ringobsid, r):
    """The old-format ringobsid in the URL path names no observation."""
    return f'Unknown RINGOBSID "{ringobsid}" for {_request_path(r)}'

def HTTP404_UNKNOWN_OPUS_ID(opusid, r):
    """The OPUS ID in the URL path names no observation."""
    return f'Unknown OPUSID "{opusid}" for {_request_path(r)}'

def HTTP400_UNKNOWN_CATEGORY(r):
    """A category named in the cats parameter does not exist."""
    return f'Unknown category for {_request_path(r)}'

def HTTP400_UNKNOWN_DOWNLOAD_FILE_FORMAT(fmt, r):
    """The requested archive format is not one OPUS can create."""
    return f'Unknown DOWNLOAD FILE FORMAT "{fmt}" for {_request_path(r)}'

def HTTP404_FAKE_ERROR(r):
    """A 404 injected by OPUS_FAKE_SERVER_ERROR404_PROBABILITY."""
    return f'Fake HTTP404 error for {_request_path(r)}'

def wrap_http500_string(s):
    """Wrap an internal-error message the way the Django debug page does.

    This is the one place in OPUS where an error message becomes raw HTML instead
    of going through a template, so it is also the one place that has to escape.
    The messages it wraps name the request path, which the caller controls.

    Escaping here rather than in `_request_path` is deliberate: that helper also
    feeds the HTTP400_/HTTP404_ builders, whose messages are rendered by
    `400.html` and Django's `404.html` and are therefore escaped by the template
    engine - escaping them a second time at the source would show the user
    `&amp;lt;` where they typed `<`.

    Parameters:
        s: The message to wrap. Any HTML in it is escaped, not honored.

    Returns:
        The message wrapped in the div the Django debug page uses.
    """
    return f'<div id="info">{escape(s)}</div>'

def HTTP500_SEARCH_CACHE_FAILED(r): # pragma: no cover - database error
    """The search cache table could not be found or created."""
    return wrap_http500_string(f'Internal database error for {_request_path(r)}')

def HTTP500_DATABASE_ERROR(r): # pragma: no cover - database error
    """A database query failed."""
    return wrap_http500_string(f'Internal database error for {_request_path(r)}')

def HTTP500_INTERNAL_ERROR(r):
    """Something failed that is not the caller's fault and has no better message."""
    return wrap_http500_string(
                f'Unspecified internal server error for {_request_path(r)}')

def HTTP500_FAKE_ERROR(r):
    """A 500 injected by OPUS_FAKE_SERVER_ERROR500_PROBABILITY."""
    return wrap_http500_string(f'Fake HTTP500 error for {_request_path(r)}')
