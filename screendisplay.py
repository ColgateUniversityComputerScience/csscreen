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
            <style>
            body { font-family: Helvetica, sans-serif }
            h1 { color: red; background-color: white; }
            </style>
            <h1>No content added!</h1>
            <p>This screen would be way more interesting if content were added, right?</p>
            ''', 'No content!', 'No content added to queue')


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
        self.contenttimer.stop()
        self.close()

    def clock_update(self):
        if not running:
            self.stop()
            return

        self.time.setText(asctime())

    def content_update(self):
        if not running:
            self.stop()
            return

        try:
            item = self.__content_queue.next_content()
        except NoSuitableContentException:
            item = self.__nocontent

        # as content item to render itself to the display
        item.renderSelf(self.webview)

        # display_duration is in sec
        QTimer.singleShot(item.display_duration*1000, self.content_update) 

def sigint(*args):
    global running
    running = False

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

    app.exec_() # block here until we die
    rpcserver.stop()
