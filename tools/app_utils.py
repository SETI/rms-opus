from django.http import HttpResponse
from django.utils import simplejson
from django.http import Http404
from StringIO import StringIO
from zipfile import ZipFile
from django.http import HttpResponse
from django.shortcuts import render_to_response
from datetime import datetime
import random, string, csv, settings, re
from django.core import serializers

import logging
log = logging.getLogger(__name__)


def responseFormats(data, fmt, **kwargs):
    """
    this is REALLY AWEFUL.

    returns data in response format fmt

    data is a dictionary,

    data can contain dictionary objects or or strings vars

    for fmt=csv or fmt = html it looks for the first it finds

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

        try:
            return HttpResponse(simplejson.dumps(data), mimetype='application/json')
        except:
            data = serializers.serialize('json',data)
            return HttpResponse(data, mimetype='application/json')

    elif fmt == 'html':
        try: path = data['path']
        except: path = ''

        for d in data:
            if type(data[d]).__name__ in ['list']:

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
                if 'table_headers' in kwargs:
                    returndata['table_headers'] = kwargs['table_headers']
                if 'checkboxes' in kwargs:
                    returndata['checkboxes'] = kwargs['checkboxes']
                if 'collection' in kwargs:
                    returndata['collection'] = kwargs['collection']

                return render_to_response(kwargs['template'],returndata)

                # if type(data[d][0]).__name__ == 'dict':
                #     return render_to_response(kwargs['template'],returndata)
                # else:
                #     return render_to_response(kwargs['template'],returndata)


        return render_to_response(kwargs['template'],{'data':data})


    elif fmt == 'zip':
        return zipped(simplejson.dumps(data))

    elif fmt == 'raw':
        return data

    # data is a list of dictionaries
    # like: [{ring_obs_id=something1, planet=SAt, target = Pan}, {ring_obs_id=something21, planet=Sat, target = Pan}]
    # each row is one dictionary
    elif fmt == 'csv':   # must pass a list of dicts

        for d in data:
            if type(data[d]).__name__ == 'list':
                if type(data[d][0]).__name__ in ['dict', 'SortedDict']:
                    return dictToCSV(data[d])
                else:
                    return listToCSV(data[d],['filename'])

    raise Http404



# data is a list of dictionaries
# like: [{ring_obs_id=something1, planet=SAt, target = Pan}, {ring_obs_id=something21, planet=Sat, target = Pan}]
# each row is one dictionary
def dictToCSV(data):
    filename = downloadFileName()
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename=' + filename + '.csv'
    writer = csv.writer(response)
    writer.writerow([k for k,v in data[0].items()])   # first row
    for obs in data:
        writer.writerow([v for k,v in obs.items()])
    return response


# field names = list, data = list of lists or for a single column csv a list of non-list values
def listToCSV(data,field_names):
    filename = downloadFileName()
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename=' + filename + '.csv'
    writer = csv.writer(response)
    writer.writerow([label for label in field_names])   # first row
    for obs in data:
        if type(obs).__name__ == 'list':
            writer.writerow([v for v in obs])
        else:
            writer.writerow([obs])

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

    response = HttpResponse(mimetype="application/zip")
    response["Content-Disposition"] = "attachment; filename=" + filename + ".zip"

    in_memory.seek(0)
    response.write(in_memory.read())

    return response

def downloadFileName():
    randstr = random.choice(string.ascii_lowercase) + random.choice(string.ascii_lowercase) + random.choice(string.ascii_lowercase)
    return 'ringdata_' + randstr + '_' + 'T'.join(str(datetime.utcnow()).split(' '))


def getMultName(param_name):
    """ mult foreign key tables are named like so """
    return 'mult_' + str(param_name);

def getUserSearchTableName(no):
    """ a bit of text manipulation, user search tables are stored like so: """
    return 'cache_' + str(no);

def stripNumericSuffix(name):
    try:    return re.match("(.*)[1|2]",name).group(1)
    except: return name

def getNumericSuffix(name):
    try:    return re.match(".*(1|2)",name).group(1)
    except: return

def sortDict(mydict):
    newdict={}
    for key in sorted(mydict.iterkeys()):
        newdict[key] = mydict[key]
    return newdict



