import json
from django.http import HttpResponse
from django.http import Http404
from StringIO import StringIO
from zipfile import ZipFile
from django.http import HttpResponse
from django.shortcuts import render_to_response
import datetime
import random, string, csv, settings, re
from django.core import serializers
import time

import logging
log = logging.getLogger(__name__)


def responseFormats(data, fmt, **kwargs):
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
                if 'collection' in kwargs:
                    returndata['collection'] = kwargs['collection']
                if 'id_index' in kwargs:
                    returndata['id_index'] = kwargs['id_index']

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
        return listToCSV(data['page'],kwargs['labels'])

    raise Http404



# data is a list of dictionaries
# like: [{opus_id=something1, planet=SAt, target = Pan}, {opus_id=something21, planet=Sat, target = Pan}]
# each row is one dictionary
def dictToCSV(data):
    filename = downloadFileName()
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=' + filename + '.csv'
    writer = csv.writer(response)
    writer.writerow([k for k,v in data[0].items()])   # first row
    for obs in data:
        writer.writerow([v for k,v in obs.items()])
    return response


# field names = list, data = list of lists or for a single column csv a list of non-list values
def listToCSV(data,field_names):
    filename = downloadFileName()
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=' + filename + '.csv'
    writer = csv.writer(response)
    writer.writerow([label for label in field_names])   # first row
    writer.writerows(data)
    return response



def zipped(data):
    """
    the unique name is a timestamp

    """
    filename = downloadFileName()

    in_memory = StringIO()
    zip = ZipFile(in_memory, "a")
    zip.writestr(filename + '.txt', str(data))

    # fix for Linux zip files read in Windows
    for file in zip.filelist:
        file.create_system = 0

    zip.close()

    response = HttpResponse(content_type="application/zip")
    response["Content-Disposition"] = "attachment; filename=" + filename + ".zip"

    in_memory.seek(0)
    response.write(in_memory.read())

    return response

def downloadFileName():
    randstr = random.choice(string.ascii_lowercase) + random.choice(string.ascii_lowercase) + random.choice(string.ascii_lowercase)
    return 'ringdata_' + randstr + '_' + 'T'.join(str(datetime.datetime.utcnow()).split(' '))



def strip_numeric_suffix(name):
    try:    return re.match("(.*)[1|2]",name).group(1)
    except: return name

def get_numeric_suffix(name):
    try:    return re.match(".*(1|2)",name).group(1)
    except: return

def sortDict(mydict):
    newdict={}
    for key in sorted(mydict.iterkeys()):
        newdict[key] = mydict[key]
    return newdict

def get_session_id(request):
    if not request.session.get('has_session'):
        request.session['has_session'] = True
    if not request.session.session_key:
        request.session.create()
    session_id = request.session.session_key
    return session_id


_API_CALL_NUMBER = 0
_API_START_TIMES = {}

def enter_api_call(name, request):
    global _API_CALL_NUMBER
    _API_CALL_NUMBER += 1
    if settings.LOG_API_CALLS:
        print 'API', _API_CALL_NUMBER,
        print request.path, json.dumps(request.GET, sort_keys=True,
                                       indent=4,
                                       separators=(',', ': '))
    _API_START_TIMES[_API_CALL_NUMBER] = time.time()
    return _API_CALL_NUMBER

def exit_api_call(api_code, ret):
    end_time = time.time()
    if settings.LOG_API_CALLS:
        print 'API', api_code, 'EXIT',
        if api_code in _API_START_TIMES:
            print end_time-_API_START_TIMES[api_code]
        else:
            print
    if api_code in _API_START_TIMES:
        del _API_START_TIMES[api_code]
