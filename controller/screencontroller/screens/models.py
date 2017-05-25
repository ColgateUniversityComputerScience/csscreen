# import http.client
# import json
import requests
from datetime import datetime

from django.db import models


class ScreenNotAccessible(Exception):
    pass


class Screen(models.Model):
    """Represents a deployed screen."""

    name = models.CharField(max_length=100)
    ipaddress = models.GenericIPAddressField()
    port = models.SmallIntegerField(default=4443)
    password = models.CharField(max_length=100)
    lastfetch = models.DateTimeField(null=True)
    lastupdate = models.DateTimeField(auto_now=True)

    def _remote_call(self, xtype):
        xpass = "?password={}".format(self.password)
        if xtype == 'list':
            response = \
                requests.get("https://{}:{}/display{}".format(
                             self.ipaddress, self.port, xpass),
                             verify=False)
        if response.status_code != 200:
            raise \
              ScreenNotAccessible(
                "Status code failure: {}".format(response.status_code))
        return response.json()

    def fetch_current(self):
        self._cache = {}
        rdata = self._remote_call('list')
        self._update_status = rdata['status']
        if rdata['status'] == 'success':
            self.lastfetch = datetime.now()
        else:
            raise \
              ScreenNotAccessible("Connection succeeded but call failed.")
        self._cache = rdata['content']
        return self._cache


class ScreenGroup(models.Model):
    """Represents an arbitrary group of screens."""

    groupname = models.CharField(max_length=100)
    screens = models.ManyToManyField(Screen)
