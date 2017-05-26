from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from models import Screen, ScreenGroup


@login_required
def index(request):
    screens = Screen.objects.all().prefetch_related('groups')
