import sys
import json
import argparse
import os
import base64
import re
from datetime import datetime
import textwrap
import requests


def make_base_url(host='localhost', port=4443):
    return "https://{}:{}".format(host, port)

def print_content_entry(entry, index = 1):
    assert(isinstance(entry, dict))
    name = entry.pop('name')
    xtype = entry.pop('type')
    print("Name: {} {}".format(name, xtype))
    for k in sorted(entry.keys()):
        value = entry[k]
        if isinstance(value, str):
            value = textwrap.shorten(value, 60)
        print("    {}: {}".format(k, value))

def print_status(status, data):
    if status == 'success':
        print ("Operation succeeded")
    else:
        print ("Operation failed: {}".format(data['reason']))

def print_response(responsedata):
    print_status(responsedata['status'], responsedata)
    rdata = responsedata.get('content', None)
    if isinstance(rdata, str):
        print_content_entry(rdata)
    elif isinstance(rdata, list):
        for i in range(len(rdata)):
            print_content_entry(rdata[i], i+1)
    else:
        pass

def ping_screen(baseurl, password):
    response = requests.get('{}/ping?password={}'.format(baseurl, password),
        verify=False)
    print(response.json())

def list_content(baseurl, password):
    response = requests.get('{}/display?password={}'.format(baseurl, password),
        verify=False)
    print_response(response.json())

def get_content(baseurl, password, name):
    response = requests.get("{}/display/{}?password={}".format(baseurl,
        name, password), verify=False)
    print_response(response.json())

def delete_content(baseurl, password, name):
    response = requests.delete("{}/display/{}?password={}".format(
        baseurl, name, password), verify=False)
    print_response(response.json())

def check_parm(pname, params):
    if pname not in params:
        print ("Required parameter '{}' for adding content was not specified.".format(pname))
        sys.exit()

def encode_filedata(filename):
    infile = open(filename, 'rb')
    data = infile.read()
    infile.close()
    return base64.b64encode(data)

def construct_add_object(params):
    content = {}
    check_parm('name', params)
    content['name'] = params['name']
    del params['name']
    check_parm('type', params)
    content['type'] = params['type']
    if params['type'] not in ['url','image','html']:
        print ("Type parameter {} is not one of 'url','image', or 'file'".format(params['type']))
        sys.exit()

    if params['type'] == 'url':
        check_parm('content', params)
        content['content'] = base64.b64encode(params['content'].encode('ascii')).decode('ascii')
        del params['content']
    elif params['type'] == 'image':
        check_parm('content', params)
        content['content'] = encode_filedata(params['content']).decode('ascii')
        content['filename'] = os.path.basename(params['content'])
        content['caption'] = params.pop('caption', '')
        del params['content']
    elif params['type'] == 'html':
        check_parm('content', params)
        content['content'] = encode_filedata(params['content']).decode('ascii')
        del params['content']

    del params['type']

    if 'expire' in params:
        estr = params['expire']
        if len(estr) == 8:
            timespec = datetime.strptime(estr, '%Y%m%d')
        elif len(estr) == 10:
            timespec = datetime.strptime(estr, '%Y%m%d%H')
        elif len(estr) == 12:
            timespec = datetime.strptime(estr, '%Y%m%d%H%M')
        elif len(estr) == 14:
            timespec = datetime.strptime(estr, '%Y%m%d%H%M%S')
        else:
            print ("Invalid expiry time.  Must be in the form YYYYMMDD or YYYYMMDDHH or YYYYMMDDHHMM")
            sys.exit()
        content['expiry'] = datetime.strftime(timespec, '%Y%m%d%H%M%S')
        del params['expire']

    if 'duration' in params:
        dur = int(params['duration'])
        content['duration'] = dur
        del params['duration']

    content['only'] = []
    content['xexcept'] = []
    for onlystr in params.get('only',[]):
        verify_time_constraint(onlystr)
        content['only'].append(onlystr)
    for exceptstr in params.get('except',[]):
        verify_time_constraint(exceptstr)
        content['xexcept'].append(exceptstr)
    params.pop('only', None)
    params.pop('except', None)

    if params:
        print ("Unrecognized parameters to 'add' command specified: {}".format(' '.join(params.keys())))
        sys.exit()

    return content

def verify_time_constraint(xstr):
    days = '([mM]?[tT]?[wW]?[rR]?[fF]?):?'
    mobj = re.match(days + '(\d{2}):(\d{2})-(\d{2}):(\d{2})', xstr)
    if not mobj:
        mobj = re.match(days + '(\d{2})(\d{2})-(\d{2})(\d{2})', xstr)
    if not mobj:
        print ("Can't parse time constraint string {}.  Should be in the format [MTWRF:]HH:MM-HH:MM or [MTWRF:]HHMM-HHMM".format(xstr))
        sys.exit()

def add_content(baseurl, password, args):
    # assume that args is a list of strings in the form:
    #   name=x type=url|image|html expire=YYYYMMDDHHMMSS begin=HHMM end=HHMM duration=int
    #   no spaces between argument key/value pairs
    params = {'except':[], 'only':[]}
    for kvstr in args:
        try:
            args = kvstr.split('=')
        except Exception as e:
            print ("Arguments to the 'add' action must be key=value pairs with no spaces (exception text: {})".format(str(e)))
            sys.exit()

        if len(args) < 2:
            print ("Argument {} doesn't appear to follow key=value format".format(kvstr))
            sys.exit()
        k = args[0]
        v = '='.join(args[1:]) # there may be more than 1 = in the k=v string
                               # the value may have an embedded = (e.g., for
                               # a URL with query string

        if k == 'except' or k == 'only':
            params[k].append(v)
        else:
            params[k] = v

    content = construct_add_object(params)
    xdata = json.dumps(content)
    response = requests.post("{}/display?password={}".format(baseurl, password),
        verify=False, data=xdata)
    print_response(response.json())

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--password', '-p', default='password', help='Specify password used to authenticate requests for modifying and querying content on the display')
    parser.add_argument('--host', '-H', default='localhost', help='Specify hostname or IP address of display server')
    parser.add_argument('--port', '-P', default=4443, help='Specify port number of display server')
    parser.add_argument('action', nargs=1, type=str, choices=['ping','get','show','list','delete','add','help'], help="Query action.  Must be one of ping, get, show, list, delete, add, or help.  The 'help' action gives detailed help on actions and arguments.")
    parser.add_argument('action_args', nargs='*', help='''Any arguments to the specified action.  Use the option --actions to show detailed help for valid action/argument combinations.''')
    args = parser.parse_args()

    baseurl = make_base_url(args.host, args.port)
    action = args.action[0]

    if action == 'help':
        print ('''
The following are the valid combinations of action and arguments:
    ping
    get <name>
    show <name>
        The get/show action requires the name of the content item for which
        to display details.

    list
        The list action lists all content items installed in the display app.

    delete <name>
        The delete action requires the name of the content item to delete.
        Once deleted, all resources (e.g., files, etc.) consumed by the
        content item are purged.

    add name=<name> type=<image|html|url> content=<filename or url> duration=<seconds> expire=YYYYMMDD[HH[MM[SS]]] only=[MTWRF:]HH:MM-HH:MM except=[MTWRF:]HH:MM-HH:MM
        The add action uploads and installs a new content item in the display
        app.  All arguments to the add command must be of the form "key=value",
        and there cannot be any spaces within the key or value (or the space
        must be escaped).  The only required arguments are name, type, and
        content.  For image and html content types, the content argument must
        be a file containing either an image or html text, respectively.
        For the url content type, the content argument must be a valid URL.

        The arguments duration, expire, only and except are optional.  If
        duration is not specified, the default display duration is 12 seconds.
        The expire argument can be used to specify an expiration date and time
        for the content, after which time it will be purged from the display
        app.  The expire argument can specify just the date as YYYYMMDD on which
        content expires, in which case the content will expire at midnight
        (time 00:00) on that day.  The hour (HH), minute (MM) and second (SS)
        can also optionally be specified to give an expiration time on the
        given date.

        The only and except arguments can be used to specify *time constraints*
        on displaying content.  The *only* argument can be used to specify that
        the content should *only* be displayed in a time range, and optionally
        on a given set of days of the week.  The *except* argument can be
        used to specify that the content should be displayed normally in
        rotation, *except* for particular time ranges, and optionally on some
        days of the week.  The argument format for only and except is as
        follows: the day of the week is first optionally specified using
        a single-letter abbreviation for the day of week (MTWRF).  Following
        the day of week, a time range in the form HHMM-HHMM (or HH:MM-HH:MM)
        can be given to specify the time of day constraint.  The hour must
        be given in 24-hour format (i.e., 00-23).  Multiple except and/or
        only contraints can be given, but the app does *not* validate that
        the contraints are reasonable.
        Examples:
           only=MWF:08:20-9:10  --  Specifies that a content item should
                                    only be displayed Monday, Wednesday,
                                    and Friday between 8:20am and 9:10am.
           except=14:45-16:45   --  Specifies that a content item should
                                    be displayed any time *except* during
                                    the time window of 2:45pm-4:45pm on
                                    any day of the week.

        Content-specific options:
            * For image content, one additional option is caption=<caption>.
        ''')
    elif action == 'ping':
        ping_screen(baseurl, args.password)
    elif action == 'list':
        list_content(baseurl, args.password)
    elif action == 'get' or action == 'show':
        if len(args.action_args) != 1:
            print ("For 'get' action, the name of the content item to get information about is required.")
            sys.exit()
        get_content(baseurl, args.password, args.action_args[0])
    elif action == 'delete':
        if len(args.action_args) != 1:
            print ("For 'delete' action, the name of the content item to delete is required.")
            sys.exit()
        delete_content(baseurl, args.password, args.action_args[0])
    elif action == 'add':
        add_content(baseurl, args.password, args.action_args)
