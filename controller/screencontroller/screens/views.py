from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.views import View
from django.views.generic import ListView, DetailView, FormView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from .models import Screen
from .forms import HTMLContentForm, ImageContentForm, URLContentForm


class ScreenList(ListView):
    model = Screen
    context_object_name = 'screens'
    queryset = Screen.get_all_and_ping()


class ScreenDetail(DetailView):
    model = Screen
    context_object_name = 'screen'


class ScreenCreate(CreateView):
    model = Screen
    fields = ['name', 'ipaddress', 'password']
    success_url = reverse_lazy('screen-list')


class ScreenUpdate(UpdateView):
    model = Screen
    fields = ['name', 'ipaddress', 'password']
    success_url = reverse_lazy('screen-list')


class ScreenContentUpdate(View):
    _clsmap = {
        'html': HTMLContentForm,
        'image': ImageContentForm,
        'url': URLContentForm,
    }

    def get(self, request):
        if 'screen' not in request.GET:
            messages.error(request, "No screens selected.")
            return HttpResponseRedirect(reverse('screen-list'))
        screenlist = ','.join(request.GET['screen'])
        if 'action' not in request.GET:
            messages.error(request, "No content action specified.")
            return HttpResponseRedirect(reverse('screen-list'))

        formcls = self._clsmap.get(request.GET['action'], None)
        if formcls is None:
            messages.error(request, "Bad content action.")
            return HttpResponseRedirect(reverse('screen-list'))

        print(request.GET)
        form = formcls(initial={'content_type': request.GET['action']})
        print("Rendering cls {}".format(formcls))
        form.content_type = request.GET['action']

        context = {'form': form,
                   'screen': screenlist,
                   'action': request.GET['action']}
        return render(request,
                      "screens/screen_content_update.html",
                      context=context)

    def post(self, request):
        print(request.path)
        print(request.POST)
        print(request.FILES)
        if 'action' not in request.POST:
            messages.error(request, "No content action specified.")
            return HttpResponseRedirect(reverse('screen-list'))
        formcls = self._clsmap.get(request.POST['action'], None)
        if formcls is None:
            messages.error(request, "Bad content action.")
            return HttpResponseRedirect(reverse('screen-list'))

        form = formcls(request.POST, request.FILES)
        if form.is_valid():
            messages.success(request, "Content successfully updated.")
            print(form.cleaned_data)
            return HttpResponseRedirect(reverse('screen-list'))
        else:
            messages.warning(request, "Invalid form content.")
            context = {'form': form,
                       'screen': request.POST['screen'],
                       'action': request.POST['action']}
            return render(request,
                          "screens/screen_content_update.html",
                          context=context)


class ScreenDelete(DeleteView):
    model = Screen
    success_url = reverse_lazy('screen-list')
