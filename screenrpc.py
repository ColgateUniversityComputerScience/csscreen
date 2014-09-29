import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
import ssl
import json
from PyQt4.QtCore import QTimer, QThread
from time import sleep

class MyRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        #print (self.command, self.path)
        #print (self.client_address)
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        output = json.dumps({'status':'Success'})
        self.send_header('Content-Length', len(output))
        self.end_headers()
        self.wfile.write(output.encode('utf-8'))

    def do_POST(self):
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

