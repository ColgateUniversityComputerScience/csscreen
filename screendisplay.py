#!/usr/bin/env python3

import sys
from time import asctime
import signal
import os
from abc import ABCMeta,abstractmethod

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
        mainLayout.addWidget(self.time)
        mainLayout.addWidget(self.webview)

        self.setLayout(mainLayout)
        self.setWindowTitle("csdisplay")

        self.clock = QTimer()
        self.clock.timeout.connect(self.clock_update)
        self.clock.start(1000)

        self.contenttimer = QTimer()
        self.contenttimer.timeout.connect(self.content_update)
        self.contenttimer.start(12000)

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
            item = HTMLContent('''
            <h1 style="text-color: red; background: white;">No content added!</h1>
            <p>This screen would be way more interesting if content were added, right?</p>
            ''', 'No content!', 'No content added to queue')

        item.renderSelf(self.webview)

def sigint(*args):
    global running
    running = False

if __name__ == '__main__':
    # setup
    app = QApplication(sys.argv)
    signal.signal(signal.SIGINT, sigint)

    content_queue = ContentQueue()

    rpcserver = start_rpc_server(content_queue)

    screen = Display(content_queue)

    # block here until app dies
    screen.show()
    # screen.showMaximized()
    # screen.showFullScreen()

    # cleanup
    app.exec_()
    rpcserver.stop()
