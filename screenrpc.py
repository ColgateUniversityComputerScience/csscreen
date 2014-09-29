import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
import ssl
import json
from PyQt4.QtCore import QTimer, QThread
from time import sleep

class MyRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # valid GET requests: 
        #    /display
        #    /display/{name}
        
        print ("GET received: {}".format(self.path))
        response_data = {}

        questionmark = self.path.find('?')
        if questionmark == -1:
            # failure: no required query parm
            response_data['status'] = 'failure'
            response_data['reason'] = 'required query parameter not specified'

        path = self.path[:questionmark]
        queryparms = self.path[(questionmark+1):].split('=')
        if len(queryparms) != 2 or queryparms[0] != 'password':
            # failure: not expected.  we just one one parameter (password)
            response_data['status'] = 'failure'
            response_data['reason'] = 'invalid number of query parameters'

        elif queryparms[1] != self.server.password:
            # failure: wrong password
            response_data['status'] = 'failure'
            response_data['reason'] = 'authentication failed'

        elif path == '/display':
            # list content
            response_data = {
                'status':'success',
                'content':self.server.content_queue.list_content()
            }
        elif path.startswith('/display/'):
            xname = path[9:] # slice off '/display/'
            contentitem = self.server.content_queue.get_content(xname)
            if contentitem:
                response_data['status'] = 'success'
                response_data['content'] = str(contentitem) # FIXME -- send back more detail?
            else:
                response_data['status'] = 'failure'
                response_data['reason'] = "no content object named '{}'".format(xname)
        else:
            response_data['status'] = 'failure'
            response_data['reason'] = 'invalid request path'

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        output = json.dumps(response_data)
        self.send_header('Content-Length', len(output))
        self.end_headers()
        self.wfile.write(output.encode('utf-8'))

    def do_DELETE(self):
        # valid DELETE request:
        #   /display/{name}
        pass

    def do_POST(self):
        # valid POST requests:
        #   /display

        #print (self.command, self.path)
        #print (self.client_address)
        xlen = int(self.headers['Content-Length'])
        indata = self.rfile.read(xlen).decode('utf-8')
        indata = json.loads(indata)
        print ("Got json data: <{}>".format(indata))       
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        output = json.dumps({'status':'Success'})
        self.send_header('Content-length', len(output))
        self.end_headers()
        self.wfile.write(output.encode('utf-8'))

    def log_message(self, fmt, *args):
        print ("Log: {}".format('/'.join(args)))


class ScreenRpcServer(QThread):
    def __init__(self, content_queue, password):
        QThread.__init__(self)
        
        self.__content_queue = content_queue
        self.__httpd = HTTPServer(('localhost', 4443), MyRequestHandler)
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

