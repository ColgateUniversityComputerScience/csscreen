from datetime import datetime
from django.db import models
import requests


class ScreenNotAccessible(Exception):
    pass


class Screen(models.Model):
    """Represents a deployed screen."""

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
        for s in screens:
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
        if response.status_code != 200:
            raise \
              ScreenNotAccessible(
                f"Status code failure: {response.status_code}")
        return response.json()

    def fetch_current(self):
        self._cache = {}
        rdata = self._remote_call('get', 'display')
        self._update_status = rdata['status']
        if rdata['status'] == 'success':
            self.lastfetch = datetime.now()
        else:
            raise \
              ScreenNotAccessible("Connection succeeded but call failed.")
        self._cache = rdata['content']
        return self._cache

    def ping(self):
        # check if we should return cached value
        now = datetime.now()
        if hasattr(self, '_last_ping'):
            delta = now - self._last_ping
            if delta.total_seconds() < 60:
                return self._ping_up

        self._ping_up = False
        self._last_ping = datetime.now()
        try:
            rdata = self._remote_call('get', 'ping')
            self._ping_up = True
        except:
            pass
        return self._ping_up

    def isup(self):
        return getattr(self, "_ping_up", False)

    def pingtime(self):
        return getattr(self, "_last_ping", None)

    def add_content(self, xtype, formdata):
        return True, "success"

    def __str__(self):
        return f"{self.name} @{self.ipaddress}"
