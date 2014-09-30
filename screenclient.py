import sys
import ssl
import http.client
import json
import argparse
import os
import base64
import re
from datetime import datetime

def get_connection(host='localhost', port=4443):
    return http.client.HTTPSConnection(host, port, check_hostname=False)

def print_response(conn):
    response = conn.getresponse()
    responsedata = response.read().decode('ascii')
    conn.close()
    print (responsedata)

def list_content(conn, password):
    conn.request('GET', '/display?password={}'.format(password)) 
    print_response(conn)

def get_content(conn, password, name):
    conn.request('GET', '/display/{}?password={}'.format(name, password)) 
    print_response(conn)

def delete_content(conn, password, name):
    conn.request('DELETE', '/display/{}?password={}'.format(name, password)) 
    print_response(conn)

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
        check_parm('url', params)
        content['content'] = base64.b64encode(params['url'].encode('ascii')).decode('ascii')
        del params['url']
    elif params['type'] == 'image':
        check_parm('file', params)
        content['content'] = encode_filedata(params['file']).decode('ascii')
        content['filename'] = os.path.basename(params['file'])
        del params['file']
    elif params['type'] == 'html':
        check_parm('file', params)
        content['content'] = encode_filedata(params['file']).decode('ascii')
        del params['file']

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

    if 'begin' in params:
        content['begin'] = parse_beginend(params['begin'])
        del params['begin']

    if 'end' in params:
        content['end'] = parse_beginend(params['end'])
        del params['end']

    if 'begin' in content and 'end' not in content or 'end' in content and 'begin' not in content:
        print ("Both 'begin' and 'end' must be specified for time-windowed content")
        sys.exit()

    if params:
        print ("Unrecognized parameters to 'add' command specified: {}".format(' '.join(params.keys())))
        sys.exit()

    return content

def parse_beginend(s):
    if re.fullmatch('\d\d\d\d', s):
        return int(s[:2]) * 60 + int(s[2:])
    elif re.fullmatch('\d\d:\d\d', s):
        return int(s[:2]) * 60 + int(s[3:])
    else:
        print ("Unrecognized format for begin or end string {}.  Must be HHMM or HH:MM".format(s))
        sys.exit()

def add_content(conn, password, args):
    # assume that args is a list of strings in the form:
    #   name=x type=url|image|html expire=YYYYMMDDHHMMSS begin=HHMM end=HHMM duration=int
    #   no spaces between argument key/value pairs
    params = {}
    for kvstr in args:
        try:
            k,v = kvstr.split('=')
        except ValueError:
            print ("Arguments to the 'add' action must be key=value pairs with no spaces")
            sys.exit()
        params[k] = v

    content = construct_add_object(params)
    xdata = json.dumps(content)
    xdata = xdata.encode('ascii')
    conn.request('POST', '/display?password={}'.format(password), body=xdata) 
    print_response(conn)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--password', '-p', default='password', help='Specify password used to authenticate requests for modifying and querying content on the display')
    parser.add_argument('--host', '-H', default='localhost', help='Specify hostname or IP address of display server')
    parser.add_argument('--port', '-P', default=4443, help='Specify port number of display server')
    parser.add_argument('action', nargs=1, type=str, choices=['get','show','list','delete','add'], help="Query action.  Must be one of get, show, list, delete, add.")
    parser.add_argument('action_args', nargs='*', help="Any arguments to the specified action")
    args = parser.parse_args()

    conn = get_connection(args.host, args.port)
    action = args.action[0]

    if action == 'list':
        list_content(conn, args.password)
    elif action == 'get' or action == 'show':
        if len(args.action_args) != 1:
            print ("For 'get' action, the name of the content item to get information about is required.")
            sys.exit()
        get_content(conn, args.password, args.action_args[0])
    elif action == 'delete':
        if len(args.action_args) != 1:
            print ("For 'delete' action, the name of the content item to delete is required.")
            sys.exit()
        delete_content(conn, args.password, args.action_args[0])
    elif action == 'add':
        add_content(conn, args.password, args.action_args)

