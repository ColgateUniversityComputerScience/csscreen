from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Screen, ScreenGroup


@login_required
def index(request):
    screens = Screen.get_all_and_ping()
    context = {'screens': screens}

    return render(request, "screens/index.html", context)
