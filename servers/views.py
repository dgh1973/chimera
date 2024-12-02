from django.core.paginator import Paginator
from django.shortcuts import render_to_response, get_object_or_404
from django.db.models import Q
from django.http import HttpResponseRedirect

from chimera.servers.models import Server
from chimera.servers.models import ServerForm
from chimera.servers.models import ServerEnv
from chimera.servers.models import ServerEnvForm
from chimera import settings

from datetime import date


def l_proto(server):
    if 'windows' in server.get_os_display().lower():
        return 'rdp://'
    else:
        #return 'ssh://%s@' % settings.CHIMERA_SSH_USER
        return 'ssh://'

def index(request):
    paginator = Paginator(Server.objects.all(), settings.PAGINATION)
    page = int(request.GET.get('page', '1'))
    pages = paginator.page(page)
    list = pages.object_list
    count = paginator.count
    page_total = paginator.num_pages
    return render_to_response('base_servers.html', {'pages': pages,
                                                    'count': count,
                                                    'list': list,
                                                    'page_total': page_total})

def envindex(request):
    paginator = Paginator(ServerEnv.objects.all(), settings.PAGINATION)
    page = int(request.GET.get('page', '1'))
    pages = paginator.page(page)
    list = pages.object_list
    count = paginator.count
    page_total = paginator.num_pages
    return render_to_response('base_serverenv.html', {'pages': pages,
                                                      'count': count,
                                                      'list': list,
                                                      'page_total': page_total})

def envview(request, id):
    paginator = Paginator(ServerEnv.objects.filter(server__id=id),
                          settings.PAGINATION)
    server = Server.objects.get(pk=id)
    page = int(request.GET.get('page', '1'))
    pages = paginator.page(page)
    list = pages.object_list
    count = paginator.count
    page_total = paginator.num_pages
    return render_to_response('base_serverenv.html', {'pages': pages,
                                                      'count': count,
                                                      'list': list,
                                                      'id': id,
                                                      'server': server,
                                                      'page_total': page_total})

def envnew(request, id=None):
    env = ServerEnv()
    if id is not None:
        env.server = Server(pk=id)
    else:
        env.server = Server(pk=1)
    env.save()
    form = ServerEnvForm(instance=env)
    return render_to_response('base_serverenv_edit.html', {'form': form,
                                                           'env': env,
                                                           'undo': 'Cancel'})

def envsubmit(request, id):
    env = get_object_or_404(ServerEnv, pk=id)
    form = ServerEnvForm(request.POST, instance=env)
    if form.is_valid():
        form.save()
    else:
        return envedit(request, id)
    render_to_response('base_serverenv_edit.html', {'form': form,
                                                    'env': env,
                                                    'undo': 'Cancel'})
    return HttpResponseRedirect('/chimera/serverenv/')

def envedit(request, id):
    env = get_object_or_404(ServerEnv, pk=id)
    form = ServerEnvForm(instance=env)
    return render_to_response('base_serverenv_edit.html', {'form': form,
                                                           'env': env,
                                                           'undo': 'Delete'})

def envdelete(request, id):
    env = get_object_or_404(ServerEnv, pk=id)
    env.delete()
    return HttpResponseRedirect('/chimera/serverenv/')

def envsearch(request):
    if request.GET.has_key('search'):
        qs = request.GET['search']
        request.session['search'] = qs
    elif request.session.has_key('search'):
        qs = request.session['search']
    try:
        results = ServerEnv.objects.filter(Q(server__name__icontains=qs) | \
                                           Q(envkey__contains=qs) | \
                                           Q(envval__icontains=qs) | \
                                           Q(type__icontains=qs))
        paginator = Paginator(results, settings.PAGINATION)
        page = int(request.GET.get('page', '1'))
        pages = paginator.page(page)
        list = pages.object_list
        count = paginator.count
        page_total = paginator.num_pages
        return render_to_response('base_serverenv.html', {'qs': qs,
                                                          'pages': pages,
                                                          'count': count,
                                                          'list': list,
                                                          'page_total': page_total})
    except:
        #raise
        return HttpResponseRedirect('/chimera/serverenv/')

def view(request, id):
    server = get_object_or_404(Server, pk=id)
    return render_to_response('base_servers_view.html', {'server': server,
                                                         'proto': l_proto(server),})

def delete(request, id):
    s = get_object_or_404(Server, pk=id)
    s.delete()
    return HttpResponseRedirect('/chimera/servers/')


def edit(request, id):
    s = get_object_or_404(Server, pk=id)
    form = ServerForm(instance=s)
    return render_to_response('base_servers_edit.html', {'form': form,
                                                         'server': s,
                                                         'undo': 'Delete'})

def new(request):
    s = Server()
    s.name = 'NEW SERVER'
    s.address = '0.0.0.0'
    s.e_addr = '0.0.0.0'
    s.updated = '1970-01-01'
    s.dob = date.today()
    s.save()
    form = ServerForm(instance=s)
    return render_to_response('base_servers_edit.html', {'form': form,
                                                         'server': s,
                                                         'undo': 'Cancel'})

def submit(request, id):
    s = get_object_or_404(Server, pk=id)
    form = ServerForm(request.POST, instance=s)
    if form.is_valid():
        form.save()
    else:
        return edit(request, id)
    render_to_response('base_servers_edit.html', {'form': form,
                                                  'server': s,
                                                  'undo': 'Cancel'})
    return HttpResponseRedirect('/chimera/servers/view/' + id)

def search(request):
    if request.GET.has_key('search'):
        qs = request.GET['search']
        request.session['search'] = qs
    elif request.session.has_key('search'):
        qs = request.session['search']
    try:
        results = Server.objects.filter(Q(name__icontains=qs) | \
                                        Q(address__contains=qs) | \
                                        Q(e_addr__contains=qs) | \
                                        Q(v_addr__contains=qs) | \
                                        Q(function__icontains=qs) | \
                                        Q(description__icontains=qs) | \
                                        Q(loc_rack__contains=qs) | \
                                        Q(loc_row__contains=qs) | \
                                        Q(loc_dc__icontains=qs) | \
                                        Q(switch_port__contains=qs) | \
                                        Q(os__icontains=qs) | \
                                        Q(make_model__icontains=qs) | \
                                        Q(serial__icontains=qs))
        paginator = Paginator(results, settings.PAGINATION)
        page = int(request.GET.get('page', '1'))
        pages = paginator.page(page)
        list = pages.object_list
        count = paginator.count
        page_total = paginator.num_pages
        return render_to_response('base_servers.html', {'qs': qs,
                                                        'pages': pages,
                                                        'count': count,
                                                        'list': list,
                                                        'page_total': page_total})
    except:
        #raise
        return HttpResponseRedirect('/chimera/servers/')
