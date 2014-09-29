#!/usr/bin/env python3

import sys
from abc import ABCMeta,abstractmethod
from datetime import datetime
from time import mktime, time
from threading import Lock
from PyQt4.QtCore import QUrl

assert(sys.version_info.major == 3)

class ContentItem(metaclass=ABCMeta):
    def __init__(self, name, description, **kwargs):
        self.__display_duration = int(kwargs.get('display_duration', 10))

        # datetime object
        self.__expire_datetime = kwargs.get('expire_datetime', None)

        # hour*60 + min
        self.__display_time_begin = kwargs.get('display_time_begin', None)
        self.__display_time_end = kwargs.get('display_time_end', None)

        self.__display_count = 0
        self.__name = name
        self.__description = description

    @abstractmethod
    def renderSelf(self, webview):
        pass

    @property
    def name(self):
        return self.__name

    @property
    def description(self):
        return self.__description

    @property
    def display_duration(self):
        return self.__display_duration

    @property
    def display_count(self):
        return self.__display_count

    @property
    def expiry(self):
        return self.__expire_datetime

    @property
    def display_time_window(self):
        return (display_time_begin,display_time_end)

    def __str__(self):
        return "{} (name: {}) {}".format(self.__class__.__name__, self.name, self.description)

class URLContent(ContentItem):
    def __init__(self, url, name, desc, **kwargs):
        super(URLContent, self).__init__(name, desc, **kwargs)
        self.__url = QUrl(url)

    def renderSelf(self, webview):
        webview.load(self.__url)

class ImageContent(ContentItem):
    def __init__(self, filename, name, desc, **kwargs):
        super(ImageContent, self).__init__(name, desc, **kwargs)
        self.__imageurl = QUrl.fromLocalFile(os.path.join(os.getcwd(), filename))

    def renderSelf(self, webview):
        webview.load(self.__imageurl)

class HTMLContent(ContentItem):
    def __init__(self, htmltext, name, desc, **kwargs):
        super(HTMLContent, self).__init__(name, desc, **kwargs)
        self.__text = htmltext

    def renderSelf(self, webview):
        webview.setHtml(self.__text)


class NoSuitableContentException(Exception):
    pass

class ContentQueue(object):
    def __init__(self):
        self.__queue = []
        self.__qlock = Lock()

    def add_content(self, content):
        with self.__qlock:
            self.__queue.append(content)

    def get_content(self, name):
        with self.__qlock:
            for i in range(len(self.__queue)):
                if self.__queue[i].name == name:
                    return self.__queue[i]

    def __expire_content(self):
        now = datetime.now()
        killlist = []
        with self.__qlock:
            for i in range(len(self.__queue)):
                if self.__queue[i].expiry >= now:
                    killlist.append(i)
            for i in killlist:
                del self.__queue[i]
        
    def next_content(self):
        self.__expire_content()

        if not len(self.__queue):
            raise NoSuitableContentException()

        with self.__qlock:
            maxiter = len(self.__queue)
            i = 0

            now = datetime.now()
            hrmin = now.hour * 60 + now.minute


            while True:
                xnext = self.__queue.pop(0)
                self.__queue.append(xnext)
                i += 1 
                
                window = xnext.display_time_window()
                if window == (None,None):
                    return xnext                    
                elif window[0] <= hrmin <= window[1]:
                    return xnext

                if i == maxiter:
                    raise NoSuitableContentException()

    def remove_content(self, name):
        with self.__qlock:
            killidx = -1
            for i in range(len(self.__queue)):
                if self.__queue[i].name == name:
                    killidx = i
                    break
            del self.__queue[i]

    def list_content(self):
        with self.__qlock:
            return [ str(c) for c in self.__queue ]
