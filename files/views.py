from django.core.paginator import Paginator
from django.shortcuts import render_to_response, get_object_or_404
from django.db.models import Q
from django.http import HttpResponseRedirect

from chimera.files.models import File, FileDelta, FileForm
from chimera.servers.models import Server
from chimera import settings

from datetime import datetime
import re


def index(request):
    paginator = Paginator(File.objects.all(), settings.PAGINATION)
    page = int(request.GET.get('page', '1'))
    pages = paginator.page(page)
    list = pages.object_list
    count = paginator.count
    page_total = paginator.num_pages
    return render_to_response('base_files.html', {'pages': pages,
                                                  'count': count,
                                                  'list': list,
                                                  'page_total': page_total})

def view(request, id):
    file = get_object_or_404(File, pk=id)
    return render_to_response('base_files_view.html', {'file': file})

def edit(request, id):
    f = get_object_or_404(File, pk=id)
    form = FileForm(instance=f)
    return render_to_response('base_files_edit.html', {'form': form,
                                                       'file': f,
                                                       'undo': 'Delete'})

def new(request):
    file = File()
    server = Server.objects.all()[0]
    file.server = server
    file.path = '/path/to/file'
    file.save()
    form = FileForm(instance=file)
    return render_to_response('base_files_edit.html', {'form': form,
                                                       'file': file,
                                                       'undo': 'Cancel'})

def delete(request, id):
    f = File.objects.get(pk=id)
    f.delete()
    return HttpResponseRedirect('/chimera/files/')

def submit(request, id):
    f = get_object_or_404(File, pk=id)
    form = FileForm(request.POST, instance=f)
    form.save()
    render_to_response('base_files_edit.html', {'form': form})
    return HttpResponseRedirect('/chimera/files/view/' + id)

def search(request):
    if request.GET.has_key('search'):
        qs = request.GET['search']
        request.session['search'] = qs
    elif request.session.has_key('search'):
        qs = request.session['search']
    # Search operator parsing logic goes here
    op = ''
    if re.match('\w+:', qs):
        op,q = qs.split(':', 1)
    try:
        if op and q:
            if op == 'server':
                paginator = Paginator(File.objects.filter(Q(server__name__icontains=q)),
                                                          settings.PAGINATION)
            if op == 'path':
                paginator = Paginator(File.objects.filter(Q(path__icontains=q)),
                                                          settings.PAGINATION)
            if op == 'owner':
                paginator = Paginator(File.objects.filter(Q(owner__icontains=q)),
                                                          settings.PAGINATION)
            if op == 'group':
                paginator = Paginator(File.objects.filter(Q(group__icontains=q)),
                                                          settings.PAGINATION)
            if op == 'content':
                paginator = Paginator(File.objects.filter(Q(content__icontains=q)),
                                                          settings.PAGINATION)
            if op == 'mode':
                paginator = Paginator(File.objects.filter(Q(mode__contains=q)),
                                                          settings.PAGINATION)

        else:
            paginator = Paginator(File.objects.filter(Q(server__name__icontains=qs) | \
                                                      Q(path__icontains=qs) | \
                                                      Q(owner__icontains=qs) | \
                                                      Q(group__icontains=qs) | \
                                                      Q(content__icontains=qs) | \
                                                      Q(mode__contains=qs)),
                                                      settings.PAGINATION)
        page = int(request.GET.get('page', '1'))
        pages = paginator.page(page)
        list = pages.object_list
        count = paginator.count
        page_total = paginator.num_pages
        return render_to_response('base_files.html', {'qs': qs,
                                                      'pages': pages,
                                                      'count': count,
                                                      'list': list,
                                                      'page_total': page_total})
    except:
        return HttpResponseRedirect('/chimera/files/')

def deltaindex(request):
    paginator = Paginator(FileDelta.objects.all(), settings.PAGINATION)
    page = int(request.GET.get('page', '1'))
    pages = paginator.page(page)
    list = pages.object_list
    count = paginator.count
    page_total = paginator.num_pages
    return render_to_response('base_file_deltas.html', {'pages': pages,
                                                        'count': count,
                                                        'list': list,
                                                        'page_total': page_total})

def deltaview(request, id):
    filedelta = get_object_or_404(FileDelta, pk=id)
    return render_to_response('base_file_deltas_view.html', {'filedelta': filedelta})

def deltarevert(request, id):
    filedelta = get_object_or_404(FileDelta, pk=id)
    filedelta._revert_delta(id=filedelta.id)
    return render_to_response('base_file_deltas_view.html', {'filedelta': filedelta})

def deltasearch(request):
    if request.GET.has_key('search'):
        qs = request.GET['search']
        request.session['search'] = qs
    elif request.session.has_key('search'):
        qs = request.session['search']
    # Search operator parsing logic goes here
    op = ''
    if re.match('\w+:', qs):
        op,q = qs.split(':', 1)
    try:
        if op and q:
            if op == 'date':
                if q == 'today':
                    q = datetime.today()
                else:
                    q = datetime.strptime(q, "%Y-%m-%d")
                q_year  = q.year
                q_month = q.month
                q_day   = q.day
                paginator = Paginator(FileDelta.objects.filter(Q(date__year=q_year) & \
                                                               Q(date__month=q_month) & \
                                                               Q(date__day=q_day)),
                                                               settings.PAGINATION)
            elif op == 'server':
                paginator = Paginator(FileDelta.objects.filter(Q(file__server__name__icontains=q)),
                                                               settings.PAGINATION)
            elif op == 'path':
                paginator = Paginator(FileDelta.objects.filter(Q(file__path__name__icontains=q)),
                                                               settings.PAGINATION)
            elif op == 'content':
                paginator = Paginator(FileDelta.objects.filter(Q(content__icontains=q)),
                                                               settings.PAGINATION)
        else:
            paginator = Paginator(FileDelta.objects.filter(Q(file__server__name__icontains=qs) | \
                                                           Q(file__path__icontains=qs) | \
                                                           Q(content__icontains=qs)),
                                                           settings.PAGINATION)
        page = int(request.GET.get('page', '1'))
        pages = paginator.page(page)
        list = pages.object_list
        count = paginator.count
        page_total = paginator.num_pages
        return render_to_response('base_file_deltas.html', {'qs': qs,
                                                            'pages': pages,
                                                            'count': count,
                                                            'list': list,
                                                            'page_total': page_total})
    except:
        #raise
        return HttpResponseRedirect('/chimera/filedeltas/')
