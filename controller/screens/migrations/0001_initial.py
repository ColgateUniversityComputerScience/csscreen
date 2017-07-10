# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-05-24 00:31
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Screen',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('ipaddress', models.GenericIPAddressField()),
                ('password', models.CharField(max_length=100)),
                ('lastfetch', models.DateTimeField()),
                ('lastupdate', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='ScreenGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('groupname', models.CharField(max_length=100)),
                ('screens', models.ManyToManyField(to='screens.Screen')),
            ],
        ),
    ]