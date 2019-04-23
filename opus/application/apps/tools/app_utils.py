################################################################################
#
# tools/app_utils.py
#
################################################################################

from collections import OrderedDict
import csv
import datetime
from io import StringIO
import json
import os
import random
import string
import subprocess
import time
from zipfile import ZipFile

from django.core import serializers
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.http import Http404, HttpResponse
from django.shortcuts import render_to_response

from search.models import ObsGeneral

import settings

import opus_support

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

def response_formats(data, fmt, **kwargs):
    """
    this is REALLY AWFUL.

    returns data in response format fmt

    data is a dictionary,

    data can contain dictionary objects or strings vars

    for fmt=csv or fmt=html it looks for the first it finds

    if you *do not* want it to use a list - like that list is for something else besides data
    then define it in ignore (see fmt=html below)

    if it doesn't find a list it displays the data itself

    fmt=zip is in json format

    NOTE: I hate this. problems!!!!
    I wanted to find a way to not repeat code when I was just returning
    data in some format, but this sucks.

    """
    # these are passed kwargs that may be lists but are metadata, not data (ugh)
    ignore = ['labels','columns']

    if fmt == 'json':
        if 'path' in kwargs:
            data['path'] = kwargs['path']
        if 'order' in kwargs:
            data['order'] = kwargs['order']
        # if 'labels' in kwargs:
        #     data['columns'] = kwargs['labels']

        return HttpResponse(json.dumps(data), content_type='application/json')

    elif fmt == 'html':

        try: path = data['path']
        except: path = ''

        for d in data:
            if isinstance(data[d], list) or isinstance(data[d], tuple):
                # it's a list and apparently we assume
                # that it is the actual data not its metadata #forheadsmack#

                if d in ignore: continue
                returndata = {'data':data[d]}

                if 'size' in kwargs:
                    returndata['size'] = kwargs['size']
                if 'path' in kwargs:
                    returndata['path'] = kwargs['path']
                if 'columns_str' in kwargs:
                    returndata['columns_str'] = ','.join(kwargs['columns_str'])
                if 'labels' in kwargs:
                    returndata['labels'] = kwargs['labels']
                if 'checkboxes' in kwargs:
                    returndata['checkboxes'] = kwargs['checkboxes']
                if 'cart' in kwargs:
                    returndata['cart'] = kwargs['cart']
                if 'id_index' in kwargs:
                    returndata['id_index'] = kwargs['id_index']
                if 'page_no' in data:
                    returndata['page_no']=data['page_no']

                return render_to_response(kwargs['template'],returndata)

        return render_to_response(kwargs['template'],{'data':data})


    elif fmt == 'zip':
        return zipped(json.dumps(data))

    elif fmt == 'raw':
        return data

    # data is a list of dictionaries
    # like: [{opus_id=something1, planet=SAt, target = Pan}, {opus_id=something21, planet=Sat, target = Pan}]
    # each row is one dictionary
    elif fmt == 'csv':   # must pass a list of dicts
        if 'page' not in data:
            # Placeholder until this routine goes away
            log.error('response_formats: Tried to write CSV but no page')
            data = []
            field_names = []
        else:
            data = data['page']
            field_names = kwargs['labels']
        filename = download_file_name()
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=' + filename + '.csv'
        writer = csv.writer(response)
        writer.writerow([label for label in field_names])   # first row
        writer.writerows(data)
        return response

    raise Http404


def zipped(data):
    "Create a zip file from the given data"
    # XXX NOTE: Zip file creation is completely broken and all of this needs
    # to be rewritten. This is just a placeholder for now so that the API calls
    # don't crash. Downloading of archive zip files does not use this routine
    # and still works fine.
    filename = download_file_name()

    # in_memory = StringIO()
    # zip = ZipFile(in_memory, "a")
    # zip.writestr(filename + '.txt', str(data))
    #
    # # fix for Linux zip files read in Windows
    # for file in zip.filelist:
    #     file.create_system = 0
    #
    # zip.close()

    response = HttpResponse(content_type="application/zip")
    response["Content-Disposition"] = "attachment; filename=" + filename + ".zip"

    # in_memory.seek(0)
    # response.write(in_memory.read())

    return response

def download_file_name():
    "Create a unique download filename based on the current time"
    randstr = (random.choice(string.ascii_lowercase)
               + random.choice(string.ascii_lowercase)
               + random.choice(string.ascii_lowercase))
    return ('ringdata_' + randstr + '_'
            + 'T'.join(str(datetime.datetime.utcnow()).split(' ')))

def strip_numeric_suffix(name):
    "Strip a trailing 1 or 2, if any, from a slug"
    if len(name) > 0 and name[-1] in ['1', '2']:
        return name[:-1]
    return name

def get_numeric_suffix(name):
    "Get a trailing 1 or 2, if any, from a slug"
    if len(name) > 0 and name[-1] in ['1', '2']:
        return name[-1]
    return None

def sort_dictionary(old_dict):
    "Sort a dictionary by key and return an equivalent OrderedDict"
    new_dict = OrderedDict()
    for key in sorted(old_dict.keys()):
        new_dict[key] = old_dict[key]
    return new_dict

def get_session_id(request):
    """Get the current session id, or create one if none available.

    The caller can override the sessionid (only for internal testing
    purposes) by specifying the __sessionid=<S> parameter."""
    session_id = None
    if request.GET is not None:
        session_id = request.GET.get('__sessionid', None)
    if session_id is None:
        if not request.session.get('has_session'):
            request.session['has_session'] = True
        if not request.session.session_key:
            request.session.create()
        session_id = request.session.session_key
    return session_id

def get_reqno(request):
    "Get the reqno, if any, and return it as an int if possible."
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
    "Record the entry into an API"
    if name is None:
        return None
    global _API_CALL_NUMBER
    _API_CALL_NUMBER += 1
    if settings.OPUS_LOG_API_CALLS:
        s = 'API ' + str(_API_CALL_NUMBER) + ' '
        if request and request.path:
            s += request.path
        if kwargs:
            s += ' ' + str(kwargs)
        if request and request.GET:
            s += ' ' + json.dumps(request.GET, sort_keys=True,
                                  indent=4,
                                  separators=(',', ': '))
        log.debug(s)
    _API_START_TIMES[_API_CALL_NUMBER] = time.time()
    return _API_CALL_NUMBER

def exit_api_call(api_code, ret):
    "Record the exit into an API"
    if api_code is None:
        return
    end_time = time.time()
    delay_amount = 0.
    if settings.OPUS_FAKE_API_DELAYS is not None:
        if settings.OPUS_FAKE_API_DELAYS > 0:
            delay_amount = settings.OPUS_FAKE_API_DELAYS / 1000.
        elif settings.OPUS_FAKE_API_DELAYS < 0:
            delay_amount = random.uniform(0.,
                                          -settings.OPUS_FAKE_API_DELAYS/1000.)
    if settings.OPUS_LOG_API_CALLS:
        s = 'API ' + str(api_code) + ' EXIT'
        if api_code in _API_START_TIMES:
            s += ' ' + str(end_time-_API_START_TIMES[api_code]) + ' secs'
        ret_str = str(ret)
        ret_str = ' '.join(ret_str.split()) # Compress whitespace
        s += ': ' + ret_str[:240]
        if isinstance(ret, HttpResponse):
            s += '\n' + ret.content.decode()[:240]
        if delay_amount:
            s += f'\nDELAYING RETURN {delay_amount} SECONDS'
        log.debug(s)
    if api_code in _API_START_TIMES:
        del _API_START_TIMES[api_code]
    if delay_amount:
        time.sleep(delay_amount)

def parse_form_type(s):
    """Parse the ParamInfo FORM_TYPE with its subfields.

    Subfields are:
        TYPE:function
        TYPE%format
    """
    if s is None:
        return None, None, None

    form_type = s
    form_type_func = None
    form_type_format = None

    if s.find(':') != -1:
        form_type, form_type_func = s.split(':')
    elif s.find('%') != -1:
        form_type, form_type_format = s.split('%')

    if form_type in settings.RANGE_FORM_TYPES:
        return form_type, form_type_func, form_type_format
    return form_type, None, None

def is_old_format_ring_obs_id(s):
    "Return True if the string is a valid old-format ringobsid"
    return len(s) > 2 and (s[0] == '_' or s[1] == '_')

def convert_ring_obs_id_to_opus_id(ring_obs_id, force_ring_obs_id_fmt=False):
    "Given an old-format ringobsid, return the new opusid"
    if (not force_ring_obs_id_fmt and
        not is_old_format_ring_obs_id(ring_obs_id)):
        return ring_obs_id
    try:
        return ObsGeneral.objects.get(ring_obs_id=ring_obs_id).opus_id
    except ObjectDoesNotExist:
        log.error('No matching RING_OBS_ID for "%s"', ring_obs_id)
        return None
    except MultipleObjectsReturned:
        log.error('More than one matching RING_OBS_ID for "%s"', ring_obs_id)
        return (ObsGeneral.objects.filter(ring_obs_id=ring_obs_id)
                .first().opus_id)

    return None

def get_mult_name(param_qualified_name):
    "Returns mult widget foreign key table name"
    return 'mult_' + '_'.join(param_qualified_name.split('.'))

def format_metadata_number_or_func(val, form_type_func, form_type_format):
    if val is None:
        return None
    if form_type_func:
        if form_type_func in opus_support.RANGE_FUNCTIONS:
            func = opus_support.RANGE_FUNCTIONS[form_type_func][0]
            return func(val)
        else:
            log.error('Unknown RANGE function "%s"', form_type_func)
        return None
    if form_type_format is None:
        return str(val)
    if abs(val) > settings.THRESHOLD_FOR_EXPONENTIAL:
        form_type_format = form_type_format.replace('f', 'e')
    try:
        return format(val, form_type_format)
    except TypeError:
        return str(val)

def get_latest_git_commit_id():
    curcwd = os.getcwd()
    try:
        os.chdir(settings.PDS_OPUS_PATH)
        # decode here to convert byte object to string
        ret = (subprocess.check_output(['git', 'log', '--format=%H', '-n', '1'])
               .strip().decode('utf8'))
    except:
        log.warning('Unable to get the latest git commit id')
        ret = str(random.getrandbits(128))
    os.chdir(curcwd)
    return ret

def cols_to_slug_list(slugs):
    if not slugs:
        return []
    return slugs.split(',')
