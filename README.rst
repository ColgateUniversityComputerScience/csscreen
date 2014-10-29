csscreen
========

This repo contains the code used to drive the Raspberry Pi screens around the CS department at Colgate University.


Installation
------------

This code has been developed and tested on Ubuntu 14.04 and on Raspberry Pi B's running Raspbian Wheezy.  It should, in theory, work on any system that supports Python3 and the PyQt4 libraries, but as always, your mileage may vary.

This code is pure Python, but it is pure *Python 3*.  At minimum Python v3.2 must be used.

For installing onto Ubuntu or Raspbian, you can do the following:

 1. Install the necessary PyQt support libraries and some X11 tools for enabling and disabling screen sleep:

        $ sudo apt-get install x11-xserver-utils python3-pyqt4

 2. Clone this repo, cd into it, and type ``./run.sh``.  That should get things running, but you will probably want to create and install crontab entries to start and stop the display server at different times of day, and to disable/enable HDMI energy saver and screen-sleep capabilities.  

Usage
-----

There are three scripts that are part of this repo, and two main Python programs.

Scripts
~~~~~~~

 * ``./run.sh``: starts the display server app in full-screen mode.  This is normally what you'd want to do when running the display server on an installed screen.  If you're just testing, it may be easier to run the app using the command ``python3 screendisplay.py``.

 * ``./kill.sh``: kills any running display server.  The script reads the pid.txt file created by the running screen app.  If the pid.txt file gets accidentally removed, ``kill.sh`` won't know how to kill the display server.  Moral of the story: don't remove pid.txt.

 * ``./clean.sh``: cleans up any cached content and resets the display server to a totally "clean" state.  Only do this if you're sure that you want a completely fresh start with the display server and content.


Display server app
~~~~~~~~~~~~~~~~~~

There are two main Python (version 3)-based programs: ``screendisplay.py`` and ``screenclient.py``.  

The ``screendisplay.py`` program is the main program that runs on the Pi to display content.  It uses the PyQt4[1]_ libraries[2]_ for GUI capabilities and displays content within a Webkit-based widget [3]_.  It also contains a server (which speaks only SSL/TLS) to handle requests for adding content to the display and for querying or deleting existing content.

There are three types of content that can currently be displayed by the display app:

 1. Images.  Any standard image file type can be displayed.  It may be automatically scaled by the webkit-based display engine.
 2. URL.  Any valid URL can be given to display.  The display engine will download and display the content fetched from the given URL.
 3. HTML text.  Any HTML text can be uploaded and displayed.  It must be *self-contained*.  That is, if any image tags are present, for example, the image must be retrievable over network.  The HTML file can include any CSS (including remotely fetched CSS) and any JavaScript.  For example, Bootstrap and JQuery work nicely with the display engine.

There are just two command-line parameters that can be specified to ``screendisplay.py``:

  1. ``--password``: specify a password that must also be given with any requests for adding/querying/deleting content.  This password defaults to "password".

  2. ``--fullscreen``: specify that the display should start in "full-screen" mode.  If this option is not specified, a "normal"-sized window is created.  

Note that the files ``screenrpc.py`` and ``screencontent.py`` are used by ``screendisplay.py``.  They are normally not run directly.

Display client app
~~~~~~~~~~~~~~~~~~

The ``screenclient.py`` program is used to interact with the display server app to add, query, and delete content.  Using this tool is currently the *only* way to add content to a given display.  The basic command-line arguments that can be given to ``screenclient.py`` are shown below (directly from running ``python3 screenclient.py --help``):

    usage: screenclient.py [-h] [--password PASSWORD] [--host HOST] [--port PORT]
                           {get,show,list,delete,add,help}
                           [action_args [action_args ...]]

    positional arguments:
      {get,show,list,delete,add,help}
                            Query action. Must be one of get, show, list, delete,
                            add, or help. The 'help' action gives detailed help on
                            actions and arguments.
      action_args           Any arguments to the specified action. Use the option
                            --actions to show detailed help for valid
                            action/argument combinations.

    optional arguments:
      -h, --help            show this help message and exit
      --password PASSWORD, -p PASSWORD
                            Specify password used to authenticate requests for
                            modifying and querying content on the display
      --host HOST, -H HOST  Specify hostname or IP address of display server
      --port PORT, -P PORT  Specify port number of display server

The following are the valid combinations of action and arguments:

    get <name>
    show <name>
        The get/show action requires the name of the content item for which 
        to display details.

    list
        The list action lists all content items installed in the display app.

    delete <name>
        The delete action requires the name of the content item to delete.  
        Once deleted, all resources (e.g., files, etc.) consumed by the 
        content item are purged.

    add name=<name> type=<image|html|url> content=<filename or url> duration=<seconds> expire=YYYYMMDD[HH[MM[SS]]] only=[MTWRF:]HH:MM-HH:MM except=[MTWRF:]HH:MM-HH:MM
        The add action uploads and installs a new content item in the display 
        app.  All arguments to the add command must be of the form "key=value",
        and there cannot be any spaces within the key or value (or the space
        must be escaped).  The only required arguments are name, type, and 
        content.  For image and html content types, the content argument must
        be a file containing either an image or html text, respectively.
        For the url content type, the content argument must be a valid URL.

        The arguments duration, expire, only and except are optional.  If
        duration is not specified, the default display duration is 12 seconds.
        The expire argument can be used to specify an expiration date and time
        for the content, after which time it will be purged from the display
        app.  The expire argument can specify just the date as YYYYMMDD on which
        content expires, in which case the content will expire at midnight
        (time 00:00) on that day.  The hour (HH), minute (MM) and second (SS)
        can also optionally be specified to give an expiration time on the
        given date.
        
        The only and except arguments can be used to specify *time constraints*
        on displaying content.  The *only* argument can be used to specify that
        the content should *only* be displayed in a time range, and optionally
        on a given set of days of the week.  The *except* argument can be
        used to specify that the content should be displayed normally in
        rotation, *except* for particular time ranges, and optionally on some
        days of the week.  The argument format for only and except is as
        follows: the day of the week is first optionally specified using
        a single-letter abbreviation for the day of week (MTWRF).  Following
        the day of week, a time range in the form HHMM-HHMM (or HH:MM-HH:MM)
        can be given to specify the time of day constraint.  The hour must
        be given in 24-hour format (i.e., 00-23).  Multiple except and/or
        only contraints can be given, but the app does *not* validate that
        the contraints are reasonable.
        Examples:
           only=MWF:08:20-9:10  --  Specifies that a content item should 
                                    only be displayed Monday, Wednesday,
                                    and Friday between 8:20am and 9:10am.
           except=14:45-16:45   --  Specifies that a content item should
                                    be displayed any time *except* during
                                    the time window of 2:45pm-4:45pm on
                                    any day of the week.

Here are a few full examples of using screenclient.py:

 * ``python3 screenclient.py --host 149.43.200.200 list``: list all content installed on the display server located at (totally fake) IP address 149.43.200.200.  Note that the host defaults to ``localhost``, so if you are running ``screenclient.py`` on the Pi itself, you don't need to specify host or port.  The remaining examples don't specify the host or port for clarity.

 * ``python3 screenclient.py show directory``: display the details of the content item named "directory".

 * ``python3 screenclient.py delete directory``: delete the content item named "directory".

 * ``python3 screenclient.py add name=teaalert type=html content=tea.html only=T:11:10-12:10``: upload a new HTML content item, but *only* display it on Tuesdays between 11:10am and 12:10pm.  Note that the file tea.html must exist (perhaps obvious, but worth stating).

 * ``python3 screenclient.py add name=directory type=image content=directory.png duration=20``: upload a new image content item, and display it for 20 seconds on screen. 


Footnotes
~~~~~~~~~

.. [1] http://www.riverbankcomputing.com/software/pyqt/download
.. [2] http://qt-project.org/doc/qt-4.8/
.. [3] http://qt-project.org/doc/qt-4.8/qwebview.html

License
-------

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
