from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect, Http404
from django.views import View
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from .models import Screen
from .forms import HTMLContentForm, ImageContentForm, URLContentForm


class ScreenList(ListView):
    model = Screen
    context_object_name = 'screens'


class ScreenDetail(DetailView):
    model = Screen
    context_object_name = 'screen'

    def get_object(self, queryset=None):
        obj = super(ScreenDetail, self).get_object(queryset)
        try:
            obj.fetch_current()
        except:
            pass
        return obj


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
            messages.info(request, "No screens selected.")
            return HttpResponseRedirect(reverse('screen-list'))
        screenlist = ','.join(request.GET['screen'])
        if 'action' not in request.GET:
            messages.warning(request, "No content action specified.")
            return HttpResponseRedirect(reverse('screen-list'))

        formcls = self._clsmap.get(request.GET['action'], None)
        if formcls is None:
            messages.warning(request, "Bad content action.")
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
        if 'action' not in request.POST:
            messages.warning(request, "No content action specified.")
            return HttpResponseRedirect(reverse('screen-list'))
        if 'screen' not in request.POST:
            messages.warning(request, "No screens specified for update.")
            return HttpResponseRedirect(reverse('screen-list'))
        formcls = self._clsmap.get(request.POST['action'], None)
        if formcls is None:
            messages.warning(request, "Bad content action.")
            return HttpResponseRedirect(reverse('screen-list'))

        form = formcls(request.POST, request.FILES)
        if form.is_valid():
            faillist = []
            successlist = []
            for sid in request.POST['screen']:
                s = Screen.objects.get(pk=sid)
                success, mesg = s.add_content(request.POST['action'],
                                              form.cleaned_data)
                if success:
                    smsg = f"Screen {s.name} update successful: {mesg}"
                    successlist.append(smsg)
                else:
                    smsg = f"Screen {s.name} update failed: {mesg}"
                    faillist.append(smsg)
            if faillist:
                messages.warning(request, ", ".join(faillist))
            if successlist:
                messages.success(request, ", ".join(successlist))
            return HttpResponseRedirect(reverse('screen-detail', args=[s.id]))
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


class ScreenContentDelete(DetailView):
    model = Screen

    def post(self, request, *args, **kwargs):
        pk = kwargs.get('pk', None)
        if pk is None:
            raise Http404("Screen does not exist")
        obj = Screen.objects.get(pk=pk)
        name = kwargs.get('name', None)
        if name is None:
            raise Http404("Content name not found in request")
        try:
            response = obj.delete_content(name)
            if response['status'] == 'success':
                messages.success(request, response['reason'].capitalize())
            else:
                messages.warning(request, response['reason'].capitalize())
        except Exception as e:
            messages.warning(request, f"Content not deleted: {e}")
        return HttpResponseRedirect(reverse('screen-detail',
                                            args=[obj.id]))
