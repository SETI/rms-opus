################################################################################
#
# tools/app_utils.py
#
################################################################################

import csv
import datetime
import json
import os
import random
import string
import subprocess
import time

from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.http import HttpResponse

from search.models import ObsGeneral

import settings

import logging
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
    except:
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
            try:
                s += '\n' + ret.content.decode()[:240]
            except:
                s += '\n(Unable to display)'
        if delay_amount: # pragma: no cover - internal debugging
            s += f'\nDELAYING RETURN {delay_amount} SECONDS'
        getattr(log, settings.OPUS_LOG_API_CALLS.lower())(s)
    if api_code in _API_START_TIMES: # pragma: no cover - internal debugging
        del _API_START_TIMES[api_code]
    if delay_amount: # pragma: no cover - internal debugging
        time.sleep(delay_amount)

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
        log.error('No matching RING_OBS_ID for "%s"', ring_obs_id)
        return None
    except MultipleObjectsReturned: # pragma: no cover - import error
        log.error('More than one matching RING_OBS_ID for "%s"', ring_obs_id)
        return (ObsGeneral.objects.filter(ring_obs_id=ring_obs_id)
                .first().opus_id)

def get_mult_name(param_qualified_name):
    """Returns mult widget foreign key table name."""
    return 'mult_' + '_'.join(param_qualified_name.split('.'))

def get_git_version(force_valid=False, use_tag=False):
    curcwd = os.getcwd()
    commit_id = 'Unknown'
    tag = None

    try:
        os.chdir(settings.PDS_OPUS_PATH)
        # decode here to convert byte object to string
        commit_id = (subprocess.check_output(['git', 'log', '--format=%H',
                                              '-n', '1'])
                     .strip().decode('utf8'))
    except: # pragma: no cover - system bug
        log.warning('Unable to get the latest git commit id')
        if not force_valid:
            commit_id = str(random.getrandbits(128))

    if use_tag: # pragma: no cover - only False when retrieving main site
        try:
            # decode here to convert byte object to string
            tag = (subprocess.check_output(['git', 'tag', '--points-at', 'HEAD'])
                   .strip().decode('utf8'))
            if '\n' in tag: # pragma: no cover - system-specific
                tag = tag[:tag.index('\n')]
        except:
            log.warning('Unable to get the current git tag')

    if tag: # pragma: no cover - depends on current git context
        if tag.startswith('v'):
            tag = tag[1:]
        ret = tag
    else:
        ret = commit_id

    os.chdir(curcwd)
    return ret

def cols_to_slug_list(slugs):
    if not slugs:
        return []
    return slugs.split(',')


def throw_random_http404_error():
    ret = random.random() < settings.OPUS_FAKE_SERVER_ERROR404_PROBABILITY
    if ret: # pragma: no cover - internal debugging
        getattr(log,
            settings.OPUS_LOG_API_CALLS.lower())('Faking HTTP404 error')
    return ret

def throw_random_http500_error():
    ret = random.random() < settings.OPUS_FAKE_SERVER_ERROR500_PROBABILITY
    if ret: # pragma: no cover - internal debugging
        getattr(log,
            settings.OPUS_LOG_API_CALLS.lower())('Faking HTTP500 error')
    return ret

def HTTP404_NO_REQUEST(s):
    return f'Internal error (No request was provided) for {s}'

def HTTP404_BAD_OR_MISSING_REQNO(r):
    if type(r) != str:
        r = r.path
    return f'Internal error (Bad or missing reqno) for {r}'

def HTTP404_MISSING_OPUS_ID(r):
    if type(r) != str:
        r = r.path
    return f'Missing OPUSID for {r}'

def HTTP404_UNKNOWN_FORMAT(fmt, r):
    if type(r) != str: # pragma: no cover - internal configuration failure
        r = r.path
    return f'Internal error (Unknown return format "{fmt}") for {r}'

def HTTP404_BAD_OR_MISSING_RANGE(r):
    if type(r) != str:
        r = r.path
    return f'Internal error (Bad or missing range) for {r}'

def HTTP404_BAD_DOWNLOAD(download, r):
    if type(r) != str:
        r = r.path
    return f'Badly formatted download argument "{download}" for {r}'

def HTTP404_BAD_RECYCLEBIN(recyclebin, r):
    if type(r) != str:
        r = r.path
    return (f'Internal error (Badly formatted recyclebin argument '
            f'"{recyclebin}") for {r}')

def HTTP404_BAD_COLLAPSE(collapse, r):
    if type(r) != str:
        r = r.path
    return f'Badly formatted collapse argument "{collapse}" for {r}'

def HTTP404_BAD_LIMIT(limit, r):
    if type(r) != str:
        r = r.path
    return f'Badly formatted limit "{limit}" for {r}'

def HTTP404_BAD_STARTOBS(startobs, r):
    if type(r) != str:
        r = r.path
    return f'Badly formatted startobs "{startobs}" for {r}'

def HTTP404_BAD_PAGENO(pageno, r):
    if type(r) != str:
        r = r.path
    return f'Badly formatted page number "{pageno}" for {r}'

def HTTP404_BAD_OFFSET(offset, r):
    if type(r) != str:
        r = r.path
    return f'Bad computed offset "{offset}" for {r}'

def HTTP404_SEARCH_PARAMS_INVALID(r):
    if type(r) != str:
        r = r.path
    return f'Search parameters invalid for {r}'

def HTTP404_UNKNOWN_SLUG(slug, r):
    if type(r) != str:
        r = r.path
    if slug is None:
        return f'Unknown metadata field slug for {r}'
    return f'Unknown metadata field "{slug}" for {r}'

def HTTP404_UNKNOWN_UNITS(units, slug, r):
    if type(r) != str:
        r = r.path
    return f'Unknown units "{units}" for metadata field "{slug}" for {r}'

def HTTP404_UNKNOWN_RING_OBS_ID(ringobsid, r):
    if type(r) != str:
        r = r.path
    return f'Unknown RINGOBSID "{ringobsid}" for {r}'

def HTTP404_UNKNOWN_OPUS_ID(opusid, r):
    if type(r) != str:
        r = r.path
    return f'Unknown OPUSID "{opusid}" for {r}'

def HTTP404_UNKNOWN_CATEGORY(r):
    if type(r) != str:
        r = r.path
    return f'Unknown category for {r}'

def HTTP404_UNKNOWN_DOWNLOAD_FILE_FORMAT(fmt, r):
    if type(r) != str:
        r = r.path
    return f'Unknown DOWNLOAD FILE FORMAT "{fmt}" for {r}'

def wrap_http500_string(s): # pragma: no cover - internal debugging
    # This duplicates the format for the Django debug page
    ret = f'<div id="info">{s}</div>'
    return ret

def HTTP500_SEARCH_CACHE_FAILED(r): # pragma: no cover - database error
    if type(r) != str:
        r = r.path
    return wrap_http500_string(f'Internal database error for {r}')

def HTTP500_DATABASE_ERROR(r): # pragma: no cover - database error
    if type(r) != str:
        r = r.path
    return wrap_http500_string(
                f'Internal database error for {r}')

def HTTP500_INTERNAL_ERROR(r): # pragma: no cover - internal error
    if type(r) != str:
        r = r.path
    return wrap_http500_string(f'Unspecified internal server error for {r}')
