#!/usr/bin/env python3

import sys
import os
import os.path
from abc import ABCMeta,abstractmethod
from datetime import datetime
from time import mktime, time
from threading import Lock
import pickle
from collections import namedtuple
import re
from PyQt4.QtCore import QUrl

assert(sys.version_info.major == 3)

CACHE_DIR = 'screen_content_cache'

TimeConstraintSpec = namedtuple('TimeConstraintSpec', ['days','begin','end'])

class TimeConstraint(metaclass=ABCMeta):
    _dowmap = {}
    _revdow = {}
    for i,dayletter in enumerate('MTWRF'):
        _dowmap[dayletter] = i+1
        _dowmap[dayletter.lower()] = i+1
        _revdow[i+1] = dayletter
    print (_dowmap)

    def __init__(self, s):
        self.__constraint = TimeConstraint.parse_constraint(s)

    @abstractmethod
    def should_display(self, now):
        '''
        Predicate function that returns T/F depending whether the
        content item should be displayed now, given the time
        constraint.  now is a datetime object.
        '''
        pass

    @staticmethod
    def parse_constraint(s):
        days = '([mM]?[tT]?[wW]?[rR]?[fF]?):?'
        mobj = re.fullmatch(days + '(\d{2}):(\d{2})-(\d{2}):(\d{2})', s)
        if not mobj:
            mobj = re.fullmatch(days + '(\d{2})(\d{2})-(\d{2})(\d{2})', s)

        if not mobj:
            raise Exception("Can't parse time constraint string {}.  Should be in the format [MTWRF:]HH:MM-HH:MM or [MTWRF:]HHMM-HHMM".format(s))

        days = tuple([ TimeConstraint._dowmap[letter] for letter in mobj.groups()[0] ])
        begin = int(mobj.groups()[1]) * 60 + int(mobj.groups()[2])
        end = int(mobj.groups()[3]) * 60 + int(mobj.groups()[4])
        return TimeConstraintSpec(days, begin, end)

    def now_matches_constraint(self, now):
        dow = now.weekday()
        hourmin = now.hour * 60 + now.minute
        return (not self.__constraint.days or dow in self.__constraint.days) and  self.__constraint.begin <= hourmin < self.__constraint.end

    def __str__(self):
        print (self.__constraint)
        dow = ''.join([ TimeConstraint._revdow[dow] for dow in self.__constraint.days ])
        begin = '{:02d}:{:02d}'.format(self.__constraint.begin // 60, self.__constraint.begin % 60)
        end = '{:02d}:{:02d}'.format(self.__constraint.end // 60, self.__constraint.end % 60)
        return "{}: {}:{}-{}".format(self.__class__.__name__, dow, begin, end)

class Only(TimeConstraint):
    def __init__(self, s):
        TimeConstraint.__init__(self, s)

    def should_display(self, now):
        return self.now_matches_constraint(now)

class Except(TimeConstraint):
    def __init__(self, s):
        TimeConstraint.__init__(self, s)
        
    def should_display(self, now):
        return not self.now_matches_constraint(now)

class ContentItem(metaclass=ABCMeta):
    def __init__(self, name, **kwargs):
        self.__display_duration = int(kwargs.get('duration', 10))

        # datetime object
        expiretime = kwargs.get('expiry', None)
        if expiretime:
            self.__expire_datetime = datetime.strptime(expiretime, '%Y%m%d%H%M%S')
        else:
            self.__expire_datetime = None

        # hour*60 + min
        self.__display_time_begin = kwargs.get('begin', None)
        if self.__display_time_begin:
            self.__display_time_begin = int(self.__display_time_begin)
        self.__display_time_end = kwargs.get('end', None)
        if self.__display_time_end:
            self.__display_time_end = int(self.__display_time_end)

        self.__display_count = 0
        self.__name = name

    @abstractmethod
    def renderSelf(self, webview):
        '''
        Method which is invoked when the content item should display itself.
        webview is a QWebView object 
        (see http://qt-project.org/doc/qt-4.8/qwebview.html).
        '''
        pass

    @property
    def name(self):
        return self.__name

    @property
    def display_duration(self):
        '''
        Get the number of seconds this content item should be displayed.
        '''
        return self.__display_duration

    @property
    def display_count(self):
        '''
        Get the number of times this content item has been displayed on
        screen.
        '''
        return self.__display_count

    @property
    def expiry(self):
        '''
        Return the expiration time of this content item or None if no
        expiration exists.
        '''
        return self.__expire_datetime

    @property
    def display_time_window(self):
        '''
        Return a 2-tuple of the time window in which this content item
        should be displayed.  If there is no time window defined for
        a content item, return None,None.
        '''
        return (self.__display_time_begin,self.__display_time_end)

    def __str__(self):
        return "{} ({}) duration:{}".format(self.__class__.__name__, self.name, self.display_duration)

    @abstractmethod
    def contentRemoved(self):
        '''
        This method is called when the content is removed from the content
        queue.  It must be overridden by derived classes.  The main purpose
        of this method is to have a hook for removing any file resources (e.g.,
        images files) that may have been created when the content object
        was instantiated.
        '''
        pass

class URLContent(ContentItem):
    def __init__(self, url, name, **kwargs):
        super(URLContent, self).__init__(name, **kwargs)
        self.__url = url

    def renderSelf(self, webview):
        webview.load(QUrl(self.__url))

    def contentRemoved(self):
        pass

    def __str__(self):
        return '{} {}'.format(ContentItem.__str__(self), str(self.__url))

class ImageContent(ContentItem):
    def __init__(self, filename, name, content, **kwargs):
        super(ImageContent, self).__init__(name, **kwargs)
        # NB: filename should be an absolute path
        absfile = self.__write_data(filename, content)
        self.__filename = absfile

    def __write_data(self, filename, content):
        outpath = os.path.join(os.getcwd(), CACHE_DIR, filename)
        with open(outpath, 'wb') as outfile:
            outfile.write(content)
        return outpath
        
    def renderSelf(self, webview):
        webview.load(QUrl.fromLocalFile(self.__filename))

    def contentRemoved(self):
        os.unlink(self.__filename)

    def __str__(self):
        return '{} {}'.format(ContentItem.__str__(self), self.__filename)

class HTMLContent(ContentItem):
    def __init__(self, htmltext, name, **kwargs):
        super(HTMLContent, self).__init__(name, **kwargs)
        self.__text = htmltext

    def renderSelf(self, webview):
        webview.setHtml(self.__text)

    def contentRemoved(self):
        pass

    def __str__(self):
        return '{} {}...'.format(ContentItem.__str__(self), self.__text[:20])

class NoSuitableContentException(Exception):
    '''
    Exception is raised when no content items exist in the content queue,
    or none of them can currently be displayed due to time-window display
    constraints.
    '''
    pass

class ContentQueue(object):
    SAVE_FILE = 'content_queue.bin'

    def __init__(self):
        self.__queue = []
        self.__qlock = Lock()
        self.__create_cache_dir()
        self.__restore_content()
        self.__save_content()

    def add_content(self, content):
        with self.__qlock:
            self.__queue.append(content)
        self.__save_content()

    def get_content(self, name):
        with self.__qlock:
            for i in range(len(self.__queue)):
                if self.__queue[i].name == name:
                    return self.__queue[i]

    def __create_cache_dir(self):
        try:
            os.makedirs(os.path.join(os.getcwd(), CACHE_DIR))
        except FileExistsError:
            pass

    def __restore_content(self):
        '''
        Read saved content queue state from 'pickle' file.
        '''
        try:
            pfile = open(ContentQueue.SAVE_FILE, 'rb')
        except FileNotFoundError:
            self.__queue = []
            return
            
        with pfile:
            self.__queue = pickle.load(pfile)

    def __save_content(self):
        '''
        Save current content queue data to 'pickle' file.
        '''
        with open(ContentQueue.SAVE_FILE, 'wb') as pfile:
            pickle.dump(self.__queue, pfile)

    def shutdown(self):
        self.__save_content()

    def __expire_content(self):
        now = datetime.now()
        killlist = []
        with self.__qlock:
            for i in range(len(self.__queue)):
                if self.__queue[i].expiry and self.__queue[i].expiry >= now:
                    killlist.append(i)
            for i in killlist:
                self.__queue[i].contentRemoved()
                del self.__queue[i]
            if killlist:
                self.__save_content()
        
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
                
                begin,end = xnext.display_time_window
                if begin == end == None:
                    return xnext                    
                elif begin <= hrmin <= end:
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

            if killidx != -1:
                self.__queue[i].contentRemoved()
                del self.__queue[i]
                self.__save_content()

    def list_content(self):
        with self.__qlock:
            return [ str(c) for c in self.__queue ]


if __name__ == '__main__':
    q = ContentQueue()
    q.shutdown()

    o = Only('w:0945-1100')
    print (o)
    print (o.should_display(datetime.now()))
    e = Except('t:0945-1000')
    print (e)
    print (e.should_display(datetime.now()))
