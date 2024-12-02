from django.core.paginator import Paginator
from django.shortcuts import render_to_response, get_object_or_404
from django.db.models import Q
from django.http import HttpResponseRedirect

from chimera.notes.models import Note, NoteForm
from chimera import settings


def index(request):
    paginator = Paginator(Note.objects.all(), settings.PAGINATION)
    page = int(request.GET.get('page', '1'))
    pages = paginator.page(page)
    list = pages.object_list
    count = paginator.count
    page_total = paginator.num_pages
    return render_to_response('base_notes.html', {'pages': pages,
                                                  'count': count,
                                                  'list': list,
                                                  'page_total': page_total})

def edit(request, id):
    n = get_object_or_404(Note, pk=id)
    form = NoteForm(instance=n)
    return render_to_response('base_notes_edit.html', {'form': form,
                                                       'note': n,
                                                       'undo': 'Delete'})

def view(request, id):
    n = get_object_or_404(Note, pk=id)
    return render_to_response('base_notes_view.html', {'note': n})

def delete(request, id):
    n = get_object_or_404(Note, pk=id)
    n.delete()
    return HttpResponseRedirect('/chimera/notes/')

def new(request):
    n = Note()
    n.title = 'NEW NOTE'
    n.save()
    form = NoteForm(request.POST, instance=n)
    return render_to_response('base_notes_edit.html', {'form': form,
                                                       'note': n,
                                                       'undo': 'Cancel'})

def submit(request, id):
    n = get_object_or_404(Note, pk=id)
    form = NoteForm(request.POST, instance=n)
    if form.is_valid():
        form.save()
        render_to_response('base_notes_edit.html', {'form': form})
    return HttpResponseRedirect('/chimera/notes/view/' + id)

def search(request):
    if request.GET.has_key('search'):
        qs = request.GET['search']
        request.session['search'] = qs
    elif request.session.has_key('search'):
        qs = request.session['search']
    try:
        results = Note.objects.filter(Q(title__icontains=qs) | \
                                      Q(content__contains=qs))
        paginator = Paginator(results, settings.PAGINATION)
        page = int(request.GET.get('page', '1'))
        pages = paginator.page(page)
        list = pages.object_list
        count = paginator.count
        page_total = paginator.num_pages
        return render_to_response('base_notes.html', {'qs': qs,
                                                      'pages': pages,
                                                      'count': count,
                                                      'list': list,
                                                      'page_total': page_total})
    except:
        #raise
        return HttpResponseRedirect('/chimera/notes/')
