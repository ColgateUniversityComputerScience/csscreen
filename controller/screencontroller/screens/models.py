from datetime import datetime
from django.db import models
import requests


class ScreenNotAccessible(Exception):
    pass


class ScreenGroup(models.Model):
    """Represents an arbitrary group of screens."""

    groupname = models.CharField(max_length=100)

    class Meta:
        ordering = ('groupname',)

    def __str__(self):
        return self.groupname


class Screen(models.Model):
    """Represents a deployed screen."""

    name = models.CharField(max_length=100)
    ipaddress = models.GenericIPAddressField()
    port = models.SmallIntegerField(default=4443)
    password = models.CharField(max_length=100)
    lastfetch = models.DateTimeField(null=True, blank=True, editable=False)
    lastupdate = models.DateTimeField(auto_now=True, editable=False)
    groups = models.ManyToManyField(ScreenGroup, blank=True)

    class Meta:
        ordering = ('name',)

    @staticmethod
    def get_all_and_ping():
        screens = Screen.objects.all().prefetch_related('groups')
        for s in screens:
            s.ping()
        return screens

    def group_list(self):
        return [ g.groupname for g in self.groups.all() ]

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

    def __str__(self):
        return f"{self.name} @{self.ipaddress}"
