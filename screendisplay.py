#!/usr/bin/env python3

import sys
from time import asctime
import signal
import os
from abc import ABCMeta,abstractmethod
import argparse

from screencontent import *
from screenrpc import start_rpc_server

assert(sys.version_info.major == 3)

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtWebKit import *

running = True

class Display(QWidget):
    def __init__(self, content_queue, parent=None):
        super(Display, self).__init__(parent)

        self.__content_queue = content_queue

        self.__nocontent = HTMLContent('''
        <!DOCTYPE html>
        <html lang="en">
        <head>
          <script src="https://code.jquery.com/jquery-2.1.1.min.js"></script>
            <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.2.0/css/bootstrap.min.css">
            <script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.2.0/js/bootstrap.min.js"></script>
        </head>
        <body>
          <div class="jumbotron">
          <h1><span class="alert alert-danger">No content here!</span></h1>
          <br><br>
          <p>This screen would be way more interesting if content were added, right?</p>
          </div></body></html>''', 'nocontent', duration=2)


        self.time = QLabel()
        self.time.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.time.setText('starting...')
        self.time.setAlignment(Qt.AlignLeft)
        self.time.setFont(QFont("Helvetica", 20, QFont.Bold))
        p = QPalette()
        p.setBrush(QPalette.Text,QColor("darkRed"))

        self.webview = QWebView()
        self.webview.setHtml("<h1>Starting...</h1>")

        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.time, 1)
        mainLayout.addSpacing(10)
        mainLayout.addWidget(self.webview, 100)

        self.setLayout(mainLayout)
        self.setWindowTitle("csdisplay")

        self.clock = QTimer()
        self.clock.timeout.connect(self.clock_update)
        self.clock.start(1000)

        QTimer.singleShot(1000, self.content_update)

    def stop(self):
        self.clock.stop()
        self.close()

    def clock_update(self):
        global running
        if not running:
            self.stop()
            return

        self.time.setText(asctime())

    def content_update(self):
        global running
        if not running:
            self.stop()
            return

        try:
            item = self.__content_queue.next_content()
        except NoSuitableContentException:
            item = self.__nocontent

        # as content item to render itself to the display
        item.render(self.webview)

        # display_duration is in sec
        QTimer.singleShot(item.display_duration*1000, self.content_update) 

def sigint(*args):
    global running
    running = False

def write_pid():
    with open('pid.txt', 'w') as outfile:
        outfile.write("{}\n".format(os.getpid()))

def remove_pid():
    try:
        os.unlink('pid.txt')
    except:
        pass

if __name__ == '__main__':
    # setup
    app = QApplication(sys.argv)
    signal.signal(signal.SIGINT, sigint)

    parser = argparse.ArgumentParser(description='CS screen display')
    parser.add_argument('--password', '-p', default='password', help='Specify password used to authenticate requests for modifying and querying content on the display')
    parser.add_argument('--fullscreen', default=False, action='store_true', help='Specify whether the display should go into full screen on startup')
    args = parser.parse_args()

    content_queue = ContentQueue()

    rpcserver = start_rpc_server(content_queue, args.password)

    screen = Display(content_queue)

    # block here until app dies
    if args.fullscreen:
        screen.showMaximized()
        # screen.showFullScreen()
    else:
        screen.show()

    write_pid()
    app.exec_() # block here until we die
    rpcserver.stop()
    content_queue.shutdown()
    remove_pid()
