"""screencontroller URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from screens.views import ScreenList, ScreenDetail, ScreenCreate, \
    ScreenUpdate, ScreenDelete, ScreenContentUpdate, ScreenContentDelete

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^accounts/', include('django.contrib.auth.urls')),
    url(r'^$', login_required(ScreenList.as_view()), name='screen-list'),
    url(r'^screen/(?P<pk>[0-9]+)/$',
        login_required(ScreenDetail.as_view()),
        name='screen-detail'),
    url(r'^screen/create/$',
        login_required(ScreenCreate.as_view()),
        name='screen-create'),
    url(r'^screen/(?P<pk>[0-9]+)/update/$',
        login_required(ScreenUpdate.as_view()),
        name='screen-update'),
    url(r'^screen/(?P<pk>[0-9]+)/delete/$',
        login_required(ScreenDelete.as_view()),
        name='screen-delete'),
    url(r'^screen/content/update/$',
        login_required(ScreenContentUpdate.as_view()),
        name='screencontent-update'),
    url(r'^screen/(?P<pk>[0-9]+)/delete/(?P<name>[a-zA-Z0-9_-]+)/$',
        login_required(ScreenContentDelete.as_view()),
        name='screencontent-delete'),
]
