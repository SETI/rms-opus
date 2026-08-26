################################################################################
#
# tools/app_utils.py
#
################################################################################

"""Helpers shared by every OPUS app: the API-view decorator, the API-call log,
and the text of every error message the API can return.

`api_view` is the piece to read first. Every routed handler is wrapped in it, and
it is what turns an exception into a response, records the call, and applies the
fault-injection knobs.
"""

from __future__ import annotations

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
from typing import TYPE_CHECKING, Any
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

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Sequence

    from django.http import HttpRequest

log = logging.getLogger(__name__)


def csv_response(filename: str, data: Iterable[Iterable[Any]],
                 column_names: Sequence[str] | None = None) -> HttpResponse:
    """Return a CSV file as a downloadable response.

    Parameters:
        filename: The download's file name, without the `.csv` suffix.
        data: The rows, each an iterable of cell values.
        column_names: A header row, written before the data when given.

    Returns:
        An `HttpResponse` carrying the CSV as an attachment.
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename={filename}.csv'
    writer = csv.writer(response)
    if column_names:
        writer.writerow(column_names)
    writer.writerows(data)
    return response

def json_response(data: Any) -> HttpResponse:
    """Return a value as a JSON response.

    Parameters:
        data: Anything `json.dumps` accepts.

    Returns:
        An `HttpResponse` holding the serialized value.
    """
    return HttpResponse(json.dumps(data), content_type='application/json')

def download_filename(opus_id: str | None, file_type: str | None) -> str:
    """Create a unique filename for a user's cart or CSV file.

    Parameters:
        opus_id: The observation the download is for, appended to the name; omit
            it for a whole-cart download.
        file_type: A word identifying the kind of download, included in the name.

    Returns:
        The file name, without a suffix. It carries a timestamp and a random
        letter, so two downloads in the same second do not collide.
    """
    # A salt that keeps two downloads in the same second from colliding.
    # It names a temporary file; it guards nothing and is not a secret.
    random_ascii = random.choice(string.ascii_letters).lower()  # nosec B311
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

def strip_numeric_suffix(name: str) -> str:
    """Strip a trailing 1 or 2, if any, from a slug.

    Parameters:
        name: The slug.

    Returns:
        The slug without its trailing 1 or 2, or unchanged if it has neither.
    """
    if len(name) > 0 and name[-1] in ['1', '2']:
        return name[:-1]
    return name

def get_numeric_suffix(name: str) -> str | None:
    """Get a trailing 1 or 2, if any, from a slug.

    Parameters:
        name: The slug.

    Returns:
        The trailing `'1'` or `'2'`, or None if the slug ends with neither.
    """
    if len(name) > 0 and name[-1] in ['1', '2']: # pragma: no cover -
        # Generalization not currently needed
        return name[-1]
    return None # pragma: no cover - see above

def sort_dictionary(old_dict: dict[str, Any]) -> dict[str, Any]:
    """Sort a dictionary by key.

    Parameters:
        old_dict: The dictionary to sort.

    Returns:
        A new dictionary with the same items in sorted key order.
    """
    new_dict = {}
    for key in sorted(old_dict.keys()):
        new_dict[key] = old_dict[key]
    return new_dict

def get_session_id(request: HttpRequest) -> str | None:
    """Get the current session id, or create one if none available.

    The caller can override the sessionid (only for internal testing
    purposes) by specifying the __sessionid=<S> parameter.

    Parameters:
        request: The request whose session is wanted.

    Returns:
        The session id. It is None only where Django could not create a session
        key at all.
    """
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

def get_reqno(request: HttpRequest) -> int | None:
    """Get the reqno, if any, and return it as an int if possible.

    Parameters:
        request: The request to read `?reqno=` from.

    Returns:
        The request number, or None if it is absent, not an integer, or
        negative. Every API handler treats None as a bad request.
    """
    raw_reqno = request.GET.get('reqno', None)
    reqno: int | None
    try:
        reqno = int(raw_reqno)  # type: ignore[arg-type]  # None is caught below
        if reqno < 0:
            reqno = None
    except Exception:
        reqno = None
    return reqno


_API_CALL_NUMBER = 0
_API_START_TIMES: dict[int, float] = {}

def enter_api_call(name: str, request: HttpRequest | None,
                   kwargs: dict[str, Any] | None = None) -> int:
    """Record the entry into an API.

    Parameters:
        name: The handler's name. It is **not** interpolated into the log line;
            the parameter is read by nothing today.
        request: The request being served, whose path and query string are
            logged.
        kwargs: The URL's keyword arguments, logged when there are any.

    Returns:
        The API call number, which the matching `exit_api_call` is given so the
        two lines can be paired and the call timed.
    """
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
            # settings.OPUS_LOG_API_CALLS is `bool | str`, and a configuration
            # file saying `log_api_calls = true` reaches here as True, where
            # `.lower()` raises. That is issue #1468, a real crash rather than a
            # typing artifact, and deciding what `true` should mean belongs to
            # opus_config rather than here, so the declaration is left honest and
            # the fault is recorded instead of being cast away.
        getattr(log, settings.OPUS_LOG_API_CALLS.lower())(s)  # type: ignore[union-attr]
    _API_START_TIMES[_API_CALL_NUMBER] = time.time()
    return _API_CALL_NUMBER

def exit_api_call(api_code: int, ret: Any) -> None:
    """Record the exit from an API.

    The `OPUS_FAKE_API_DELAYS` knob is applied here, after the log line is
    written, so a delayed response is still recorded at the time it was produced.

    Parameters:
        api_code: The call number `enter_api_call` returned.
        ret: What the handler produced -- a response, or the exception that
            ended the call. Only the first 240 characters are logged, and a
            response whose content type is neither text nor JSON is logged as a
            note rather than decoded.
    """
    end_time = time.time()
    delay_amount = 0.
    if settings.OPUS_FAKE_API_DELAYS is not None: # pragma: no cover - internal debugging
        if settings.OPUS_FAKE_API_DELAYS > 0:
            delay_amount = settings.OPUS_FAKE_API_DELAYS / 1000.
        elif settings.OPUS_FAKE_API_DELAYS < 0:
            # Fault injection: a jittered artificial delay, off unless a
            # configuration file asks for it.
            delay_amount = random.uniform(0.,  # nosec B311
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
            # settings.OPUS_LOG_API_CALLS is `bool | str`, and a configuration
            # file saying `log_api_calls = true` reaches here as True, where
            # `.lower()` raises. That is issue #1468, a real crash rather than a
            # typing artifact, and deciding what `true` should mean belongs to
            # opus_config rather than here, so the declaration is left honest and
            # the fault is recorded instead of being cast away.
        getattr(log, settings.OPUS_LOG_API_CALLS.lower())(s)  # type: ignore[union-attr]
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


def _request_path(r: HttpRequest | str | None) -> str:
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


def _http400_response(request: HttpRequest | None,
                      exception: Http400Error) -> HttpResponse:
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


def _log_injected_fault(kind: str) -> None:
    """Note an injected fault in the API-call log, if that log is enabled.

    Parameters:
        kind: The kind of fault being injected, for the log line.
    """
    if settings.OPUS_LOG_API_CALLS:
        # settings.OPUS_LOG_API_CALLS is `bool | str`, and a configuration
        # file saying `log_api_calls = true` reaches here as True, where
        # `.lower()` raises. That is issue #1468, a real crash rather than a
        # typing artifact, and deciding what `true` should mean belongs to
        # opus_config rather than here, so the declaration is left honest and
        # the fault is recorded instead of being cast away.
        getattr(log,
                settings.OPUS_LOG_API_CALLS.lower())(  # type: ignore[union-attr]
                    f'Faking {kind} error')


def _injected_fault_response(request: HttpRequest | None) -> HttpResponse | None:
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
    # Fault injection: rolls against a configured probability that is 0
    # in every deployment except a deliberate error-handling test.
    if random.random() < settings.OPUS_FAKE_SERVER_ERROR404_PROBABILITY:  # nosec B311
        _log_injected_fault('HTTP404')
        raise Http404(http404_fake_error(request))
    # Fault injection, as directly above.
    if random.random() < settings.OPUS_FAKE_SERVER_ERROR500_PROBABILITY:  # nosec B311
        _log_injected_fault('HTTP500')
        return HttpResponseServerError(http500_fake_error(request))
    return None


def api_view(handler: Callable[..., HttpResponse]) -> Callable[..., HttpResponse]:
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
    def wrapper(request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """Record the call, run the handler, and answer with what it produced.

        Parameters:
            request: The request being served.
            *args: Positional arguments from the URL pattern.
            **kwargs: Keyword arguments from the URL pattern.

        Returns:
            The handler's response, or the 400 or 500 response the error
            handling above produced in its place.

        Raises:
            Http404: Raised by the handler, or injected by the fault knobs, and
                re-raised for Django to answer.
            BadRequest: Re-raised, as above.
            PermissionDenied: Re-raised, as above.
            SuspiciousOperation: Re-raised, as above.
        """
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
            log.exception('%r: Unhandled exception', handler.__name__)
            ret = HttpResponseServerError(http500_internal_error(request))
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

def is_old_format_ring_obs_id(s: str) -> bool:
    """Return True if the string is a valid old-format ringobsid.

    Parameters:
        s: The identifier to test.

    Returns:
        True if it has the shape of an old-format ringobsid.
    """
    return len(s) > 2 and (s[0] == '_' or s[1] == '_')

def convert_ring_obs_id_to_opus_id(ring_obs_id: str,
                                   force_ring_obs_id_fmt: bool = False) -> str | None:
    """Given an old-format ringobsid, return the new opusid.

    Parameters:
        ring_obs_id: The identifier to convert.
        force_ring_obs_id_fmt: Treat the argument as a ringobsid even when it
            does not look like one.

    Returns:
        The opusid, the argument unchanged when it is not an old-format
        ringobsid, or None when no observation has that ringobsid.
    """
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
        first = ObsGeneral.objects.filter(ring_obs_id=ring_obs_id).first()
        # Reached only from MultipleObjectsReturned, so the queryset has at
        # least two rows and .first() cannot be None.
        assert first is not None
        return first.opus_id

def get_mult_name(param_qualified_name: str) -> str:
    """Returns mult widget foreign key table name.

    Parameters:
        param_qualified_name: The field's `<table>.<column>` name.

    Returns:
        The name of the `mult_` table holding that field's values.
    """
    return 'mult_' + '_'.join(param_qualified_name.split('.'))

def get_git_version() -> str:
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

def cols_to_slug_list(slugs: str | None) -> list[str]:
    """Split a comma-separated `?cols=` value into slugs.

    Parameters:
        slugs: The parameter's value, or None if it was absent.

    Returns:
        The slugs, or an empty list if the value was absent or empty.
    """
    if not slugs:
        return []
    return slugs.split(',')


################################################################################
#
# ERROR MESSAGES
#
# The message text an error page shows the user. The http400_/http404_/http500_
# prefix records which status the message is raised with: an http400_ message
# accompanies `Http400Error` (the request itself was malformed), an http404_
# message accompanies `Http404` (something named in the URL path does not exist),
# and an http500_ message accompanies `HttpResponseServerError`. Each takes the
# request, or a path given as a string when the request is not available.
#
################################################################################

def http404_no_request(s: HttpRequest | str | None) -> str:
    """The handler was called with no request, or one with no GET or META."""
    return f'Internal error (No request was provided) for {_request_path(s)}'

def http400_bad_or_missing_reqno(r: HttpRequest | str | None) -> str:
    """The reqno parameter is absent or is not a non-negative integer."""
    return f'Internal error (Bad or missing reqno) for {_request_path(r)}'

def http400_missing_opus_id(r: HttpRequest | str | None) -> str:
    """An OPUS ID is required but none was given."""
    return f'Missing OPUSID for {_request_path(r)}'

def http404_unknown_format(fmt: object, r: HttpRequest | str | None) -> str:
    """The requested return format is not one this endpoint can produce."""
    return f'Internal error (Unknown return format "{fmt}") for {_request_path(r)}'

def http400_bad_or_missing_range(r: HttpRequest | str | None) -> str:
    """The range parameter is absent or is not a pair of OPUS IDs."""
    return f'Internal error (Bad or missing range) for {_request_path(r)}'

def http400_bad_download(download: object, r: HttpRequest | str | None) -> str:
    """The download parameter is not 0 or 1."""
    return f'Badly formatted download argument "{download}" for {_request_path(r)}'

def http400_bad_recyclebin(recyclebin: object, r: HttpRequest | str | None) -> str:
    """The recyclebin parameter is not 0 or 1."""
    return (f'Internal error (Badly formatted recyclebin argument '
            f'"{recyclebin}") for {_request_path(r)}')

def http400_bad_collapse(collapse: object, r: HttpRequest | str | None) -> str:
    """The collapse parameter is not an integer."""
    return f'Badly formatted collapse argument "{collapse}" for {_request_path(r)}'

def http400_bad_limit(limit: object, r: HttpRequest | str | None) -> str:
    """The limit parameter is not an integer in the permitted range."""
    return f'Badly formatted limit "{limit}" for {_request_path(r)}'

def http400_bad_startobs(startobs: object, r: HttpRequest | str | None) -> str:
    """The startobs parameter is not an integer."""
    return f'Badly formatted startobs "{startobs}" for {_request_path(r)}'

def http400_bad_pageno(pageno: object, r: HttpRequest | str | None) -> str:
    """The page parameter is not an integer."""
    return f'Badly formatted page number "{pageno}" for {_request_path(r)}'

def http400_bad_offset(offset: object, r: HttpRequest | str | None) -> str:
    """The offset computed from startobs or page is outside the permitted range."""
    return f'Bad computed offset "{offset}" for {_request_path(r)}'

def http400_search_params_invalid(r: HttpRequest | str | None) -> str:
    """The search parameters in the query string could not be parsed."""
    return f'Search parameters invalid for {_request_path(r)}'

def http400_unknown_slug(slug: object, r: HttpRequest | str | None) -> str:
    """A metadata field slug the caller supplied does not exist."""
    if slug is None:
        return f'Unknown metadata field slug for {_request_path(r)}'
    return f'Unknown metadata field "{slug}" for {_request_path(r)}'

def http400_unknown_units(units: object, slug: object, r: HttpRequest | str | None) -> str:
    """The requested units are not valid for the given metadata field."""
    return (f'Unknown units "{units}" for metadata field "{slug}" for '
            f'{_request_path(r)}')

def http404_unknown_ring_obs_id(ringobsid: object, r: HttpRequest | str | None) -> str:
    """The old-format ringobsid in the URL path names no observation."""
    return f'Unknown RINGOBSID "{ringobsid}" for {_request_path(r)}'

def http404_unknown_opus_id(opusid: object, r: HttpRequest | str | None) -> str:
    """The OPUS ID in the URL path names no observation."""
    return f'Unknown OPUSID "{opusid}" for {_request_path(r)}'

def http400_unknown_category(r: HttpRequest | str | None) -> str:
    """A category named in the cats parameter does not exist."""
    return f'Unknown category for {_request_path(r)}'

def http400_unknown_download_file_format(fmt: object, r: HttpRequest | str | None) -> str:
    """The requested archive format is not one OPUS can create."""
    return f'Unknown DOWNLOAD FILE FORMAT "{fmt}" for {_request_path(r)}'

def http404_fake_error(r: HttpRequest | str | None) -> str:
    """A 404 injected by OPUS_FAKE_SERVER_ERROR404_PROBABILITY."""
    return f'Fake HTTP404 error for {_request_path(r)}'

def wrap_http500_string(s: str) -> str:
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

def http500_search_cache_failed(r: HttpRequest | str | None) -> str: # pragma: no cover - database error
    """The search cache table could not be found or created."""
    return wrap_http500_string(f'Internal database error for {_request_path(r)}')

def http500_database_error(r: HttpRequest | str | None) -> str: # pragma: no cover - database error
    """A database query failed."""
    return wrap_http500_string(f'Internal database error for {_request_path(r)}')

def http500_internal_error(r: HttpRequest | str | None) -> str:
    """Something failed that is not the caller's fault and has no better message."""
    return wrap_http500_string(
                f'Unspecified internal server error for {_request_path(r)}')

def http500_fake_error(r: HttpRequest | str | None) -> str:
    """A 500 injected by OPUS_FAKE_SERVER_ERROR500_PROBABILITY."""
    return wrap_http500_string(f'Fake HTTP500 error for {_request_path(r)}')
