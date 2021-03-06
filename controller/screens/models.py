import base64
import json
from django.db import models
import django.utils.timezone as tz
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _
import requests
requests.packages.urllib3.disable_warnings()


class ScreenNotAccessible(Exception):
    pass


class Screen(models.Model):
    """Represents a deployed screen."""

    STALE_WINDOW = 180
    name = models.CharField(
        max_length=100,
        help_text="A unique name for the screen")
    ipaddress = models.GenericIPAddressField(
        verbose_name="IP address")
    port = models.SmallIntegerField(default=4443)
    password = models.CharField(max_length=100)
    lastfetch = models.DateTimeField(null=True, blank=True, editable=False)
    lastupdate = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        ordering = ('name',)

    @staticmethod
    def get_all_and_ping():
        screens = Screen.objects.all()
        # print("In get all and ping {}".format(screens))
        for s in screens:
            # print("Pinging {}".format(s))
            s.ping()
        return screens

    def _remote_call(self, xtype, command):
        xpass = "?password={}".format(self.password)
        starturl = f"https://{self.ipaddress}:{self.port}"
        if xtype == 'get':
            response = \
                requests.get(f"{starturl}/{command}{xpass}",
                             verify=False,
                             timeout=1.0)
        elif xtype == 'delete':
            xurl = f"{starturl}/display/{command}{xpass}"
            response = requests.delete(xurl, verify=False, timeout=1.0)
        elif xtype == 'add':
            xurl = f"{starturl}/display{xpass}"
            xtype, formdata = command
            # print(f"Add: {xurl} {xtype}")
            xdata = self._construct_add_object(xtype, formdata)
            # print(xdata)
            response = requests.post(xurl, verify=False, data=xdata)
        if response.status_code != 200:
            raise \
              ScreenNotAccessible(
                f"Status code failure: {response.status_code}")
        return response.json()

    def fetch_current(self, force=False):
        now = tz.now()
        if hasattr(self, "lastfetch") and hasattr(self, "_cache"):
            timediff = (now - self.lastfetch)
            if timediff.total_seconds() < self.STALE_WINDOW:
                return self._cache
        rdata = self._remote_call('get', 'display')
        self._update_status = rdata['status']
        if rdata['status'] == 'success':
            self.lastfetch = tz.now()
            self.save()
        else:
            raise \
              ScreenNotAccessible("Connection succeeded but call failed.")
        self._cache = rdata['content']
        return self._cache

    def ping(self):
        now = tz.now()
        if hasattr(self, '_last_ping'):
            delta = now - self._last_ping
            if delta.total_seconds() < self.STALE_WINDOW:
                return self._ping_up
        self._last_ping = tz.now()
        try:
            rdata = self._remote_call('get', 'ping')
            if rdata['status'] == 'success':
                self._ping_up = True
                self._content_count = int(rdata['content']['display_items'])
            else:
                self._ping_up = False
        except Exception as e:
            self._ping_up = False
        return self._ping_up

    def content_cache(self):
        return getattr(self, "_cache", {})

    def isup(self):
        return getattr(self, "_ping_up", False)

    def content_count(self):
        return getattr(self, "_content_count", 0)

    def pingtime(self):
        return getattr(self, "_last_ping", None)

    def add_content(self, xtype, formdata):
        response = self._remote_call('add', (xtype, formdata))
        return response['status'] == 'success', response['reason']

    def delete_content(self, xname):
        response = self._remote_call('delete', xname)
        return response

    def __str__(self):
        return f"{self.name} @{self.ipaddress}"

    @staticmethod
    def _construct_add_object(xtype, formdata):
        content = {}
        if xtype not in ['url', 'image', 'html']:
            raise ValidationError(_('Invalid content type'), code='invalid')

        name = formdata.pop('content_name', None)
        if name is None:
            raise ValidationError(_('Missing content name'), code='invalid')

        content['name'] = name
        content['type'] = xtype

        if xtype == 'url':
            urlc = formdata.pop('url', None)
            if urlc is None:
                raise ValidationError(_('Missing URL'), code='invalid')
            content['content'] = \
                base64.b64encode(urlc.encode('utf8')).decode('utf8')
        elif xtype == 'image':
            # print(formdata)
            inmemfile = formdata.pop('content_file')
            if not inmemfile.content_type.startswith('image'):
                raise ValidationError(_('Not an image file type.'))
            content['content'] = \
                base64.b64encode(inmemfile.read()).decode('utf8')
            content['filename'] = inmemfile.name
            caption = formdata.pop('image_caption', None)
            if caption is not None:
                content['caption'] = caption
        elif xtype == 'html':
            # print(formdata)
            inmemfile = formdata.pop('content_file')
            if not inmemfile.content_type.startswith('text/html'):
                raise ValidationError(_('Not an HTML file type.'))
            content['content'] = \
                base64.b64encode(inmemfile.read()).decode('utf8')
            content['filename'] = inmemfile.name

            for i, inmemfile in enumerate(formdata.pop('html_assets', [])):
                xfiledata = base64.b64encode(inmemfile.read()).decode('utf8')
                content[f"assetname_{i}"] = inmemfile.name
                content[f"assetcontent_{i}"] = xfiledata

        timespec = formdata.pop('expire', None)
        if timespec is not None:
            content['expiry'] = tz.datetime.strftime(timespec, '%Y%m%d%H%M%S')

        duration = formdata.pop('duration', None)
        if duration is not None:
            content['duration'] = int(duration)

        content['only'] = []
        content['xexcept'] = []

        onlystr = formdata.pop('xonly', None)
        if onlystr is not None and onlystr:
            olist = onlystr.split(',')
            content['only'] = olist

        exceptstr = formdata.pop('xexcept', None)
        if exceptstr is not None and exceptstr:
            elist = exceptstr.split(',')
            content['xexcept'] = elist

        return json.dumps(content)
