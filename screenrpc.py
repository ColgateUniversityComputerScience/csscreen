import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
import ssl
import json
from urllib.parse import urlparse, parse_qs
from time import sleep
import base64
from PyQt4.QtCore import QTimer, QThread
from screencontent import URLContent, ImageContent, HTMLContent

class MyRequestHandler(BaseHTTPRequestHandler):
    def __verify_password(self):
        parsed_path = urlparse(self.path)
        queryparms = parse_qs(parsed_path.query)
        failmsg = ''
        if 'password' not in queryparms:
            # failure: no required query parm
            failmsg = 'required query parameter not specified'
        elif not (queryparms['password'] and queryparms['password'][0] == self.server.password):
            failmsg = 'authentication failed'

        if failmsg:
            response_data = {
                'status':'failure',
                'reason':failmsg
            }
            self.__do_response(response_data)
            return False

        return True

    def __do_response(self, response_data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        output = json.dumps(response_data)
        self.send_header('Content-Length', len(output))
        self.end_headers()
        self.wfile.write(output.encode('ascii'))

    def do_GET(self):
        # valid GET requests: 
        #    /display
        #    /display/{name}
        # print ("GET received: {}".format(self.path))

        if not self.__verify_password():
            return

        parsed_path = urlparse(self.path)
        response_data = { 'status':'success' }

        if parsed_path.path == '/display':
            # list content
            response_data['content'] = self.server.content_queue.list_content()
        elif parsed_path.path.startswith('/display/'):
            xname = parsed_path.path[9:] # slice off '/display/'
            contentitem = self.server.content_queue.get_content(xname)
            if contentitem:
                response_data['content'] = str(contentitem) # FIXME -- send back more detail?
            else:
                response_data['status'] = 'failure'
                response_data['reason'] = "no content object named '{}'".format(xname)
        else:
            self.send_error(404)
            return

        self.__do_response(response_data)

    def do_DELETE(self):
        # valid DELETE request:
        #   /display/{name}
        # print ("DELETE received: {}".format(self.path))

        if not self.__verify_password():
            return

        parsed_path = urlparse(self.path)
        response_data = { 'status':'success' }
        if parsed_path.path.startswith('/display/'):
            xname = parsed_path.path[9:] # slice off '/display/'
            contentitem = self.server.content_queue.get_content(xname)
            if contentitem:
                self.server.content_queue.remove_content(xname)
                response_data['reason'] = "content item '{}' deleted".format(xname)
            else:
                response_data['status'] = 'failure'
                response_data['reason'] = "no content object named '{}'".format(xname)
        else:
            self.send_error(404)
            return

        self.__do_response(response_data)


    def do_POST(self):
        # valid POST requests:
        #   /display
        # print ("POST received: {}".format(self.path))

        if not self.__verify_password():
            return

        parsed_path = urlparse(self.path)
        response_data = { 'status':'success' }
        if parsed_path.path != '/display':
            self.send_error(404)
            return
        else:
            xlen = int(self.headers['Content-Length'])
            indata = self.rfile.read(xlen).decode('ascii')
            contentspec = json.loads(indata)
            # print ("Got json data for new content: <{}>".format(contentspec))

            name = contentspec.get('name', '')
            xtype = contentspec.get('type', '')
            item = None
            contentspec.pop('name', '')
            contentspec.pop('type', '')
            content = base64.b64decode(contentspec.get('content', '').encode('utf-8'))
            contentspec.pop('content','')

            errorstr = ''

            try:
                if xtype == 'url':
                    item = URLContent(content.decode('ascii'), name, **contentspec)
                elif xtype == 'image':
                    xfilename = contentspec.get('filename', '')
                    contentspec.pop('filename', '')
                    item = ImageContent(xfilename, name, content=content, **contentspec)
                elif xtype == 'html':
                    item = HTMLContent(content.decode('ascii'), name, **contentspec)

            except Exception as e:
                errorstr = str(e)

            if errorstr or not (name and xtype and item):
                response_data['status'] = 'failure'
                response_data['reason'] = "failed to create content for specification {} {}".format(contentspec, errorstr)
            else:
                self.server.content_queue.add_content(item)
                response_data['reason'] = "Create item: {}".format(str(item))

        self.__do_response(response_data)

    def log_message(self, fmt, *args):
        pass
        # print (fmt % args)

class ScreenRpcServer(QThread):
    def __init__(self, content_queue, password):
        QThread.__init__(self)
        
        self.__content_queue = content_queue
        self.__httpd = HTTPServer(('0.0.0.0', 4443), MyRequestHandler)
        self.__httpd.socket = ssl.wrap_socket(self.__httpd.socket, certfile='server.pem', server_side=True)
        self.__httpd.timeout = 0.0

        # make content_queue available inside request handlers
        self.__httpd.content_queue = self.__content_queue
        self.__httpd.password = password

        self.__stopped = False

    def stop(self):
        self.__stopped = True

    def request_check(self):
        if self.__stopped:
            return
        self.__httpd.handle_request()
        QTimer.singleShot(100, self.request_check)

def start_rpc_server(content_queue, rpc_password):
    rpcserver = ScreenRpcServer(content_queue, rpc_password)
    QTimer.singleShot(100, rpcserver.request_check)
    return rpcserver

