#!/usr/bin/env python3

import sys
import time
import signal
import os
from abc import ABCMeta,abstractmethod

assert(sys.version_info.major == 3)

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtWebKit import *

running = True

class ContentItem(metaclass=ABCMeta):
    def __init__(self):
        pass

    @abstractmethod
    def renderSelf(self, webview):
        pass

class URLContent(ContentItem):
    def __init__(self, url):
        self.__url = QUrl(url)

    def renderSelf(self, webview):
        webview.load(self.__url)

class ImageContent(ContentItem):
    def __init__(self, filename):
        self.__imageurl = QUrl.fromLocalFile(os.path.join(os.getcwd(), filename))

    def renderSelf(self, webview):
        webview.load(self.__imageurl)

class HTMLContent(ContentItem):
    def __init__(self, htmltext):
        self.__text = htmltext

    def renderSelf(self, webview):
        webview.setHtml(self.__text)


class Display(QWidget):
    def __init__(self, parent=None):
        super(Display, self).__init__(parent)

        self.time = QLabel()
        self.time.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.time.setText('starting...')
        self.time.setAlignment(Qt.AlignLeft)
        self.time.setFont(QFont("Helvetica", 20, QFont.Bold))
        p = QPalette()
        p.setBrush(QPalette.Text,QColor("darkRed"))

        self.webview = QWebView()
        self.webview.setHtml("<h1>Starting...</h1>")

        self.content = [
            URLContent("http://cs.colgate.edu/cs/events_only"),
            URLContent("http://cs.colgate.edu/cs/highlights_only"),
            ImageContent('myschedule.png'),
            HTMLContent('''
           <html>
           <style>
           body {
               font-family: Helvetica;
               font-size: 16pt;
               background-color: #eeeeee;
               color: black;
           }
           </style>
           <h1>Go to Wales, Spring 2016!</h1>
           <br>
           <p>Prof. Sommers will be leading the 2016 study group to Cardiff,
           Wales.  There will be two required courses for the Wales group: 
           a course in Welsh language and culture taught by Cardiff University 
           professors, and a course on web application development taught by 
           Prof. Sommers.  If you're interested and have any questions, please
           send email to jsommers@colgate.edu or talk to me!
           </html>
           '''),
        ]

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

        self.time.setText(time.asctime())

    def content_update(self):
        if not running:
            self.stop()
            return
        item = self.content.pop(0)
        self.content.append(item)
        item.renderSelf(self.webview)

def sigint(*args):
    global running
    running = False

if __name__ == '__main__':
    signal.signal(signal.SIGINT, sigint)
    app = QApplication(sys.argv)
    screen = Display()
    screen.showMaximized()
    # screen.showFullScreen()
    sys.exit(app.exec_())
