from django.db import models
import django.utils.timezone as tz
import requests
requests.packages.urllib3.disable_warnings()


class ScreenNotAccessible(Exception):
    pass


class Screen(models.Model):
    """Represents a deployed screen."""

    STALE_WINDOW = 180
    name = models.CharField(max_length=100)
    ipaddress = models.GenericIPAddressField()
    port = models.SmallIntegerField(default=4443)
    password = models.CharField(max_length=100)
    lastfetch = models.DateTimeField(null=True, blank=True, editable=False)
    lastupdate = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        ordering = ('name',)

    @staticmethod
    def get_all_and_ping():
        screens = Screen.objects.all()
        print("In get all and ping {}".format(screens))
        for s in screens:
            print("Pinging {}".format(s))
            s.ping()
        return screens

    def _remote_call(self, xtype, command):
        xpass = "?password={}".format(self.password)
        if xtype == 'get':
            response = \
                requests.get(
                  f"https://{self.ipaddress}:{self.port}/{command}{xpass}",
                  verify=False,
                  timeout=1.0)
        elif xtype == 'delete':
            response = \
                requests.delete(
                  f"https://{self.ipaddress}:{self.port}/{command}{xpass}",
                  verify=False,
                  timeout=1.0)
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
        return True, "success"

    def delete_content(self, xname):
        response = self._remote_call('delete', xname)
        return response

    def __str__(self):
        return f"{self.name} @{self.ipaddress}"
