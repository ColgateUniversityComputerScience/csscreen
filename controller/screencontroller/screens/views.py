from django.shortcuts import render
from django.views.generic import ListView, DetailView, FormView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import Screen, ScreenGroup


class ScreenList(ListView):
    model = Screen
    context_object_name = 'screens'
    queryset = Screen.get_all_and_ping()


class ScreenDetail(DetailView):
    model = Screen
    context_object_name = 'screen'


class ScreenCreate(CreateView):
    model = Screen
    fields = ['name', 'ipaddress', 'password', 'groups']
    success_url = reverse_lazy('screen-list')


class ScreenUpdate(UpdateView):
    model = Screen
    fields = ['name', 'ipaddress', 'password', 'groups']
    success_url = reverse_lazy('screen-list')


class ScreenDelete(DeleteView):
    model = Screen
    success_url = reverse_lazy('screen-list')


class ScreenGroupList(ListView):
    model = ScreenGroup
    context_object_name = 'screengroups'


class ScreenGroupCreate(CreateView):
    model = ScreenGroup
    fields = ['groupname']
    success_url = reverse_lazy('screengroup-list')


class ScreenGroupDelete(DeleteView):
    model = ScreenGroup
    success_url = reverse_lazy('screengroup-list')
