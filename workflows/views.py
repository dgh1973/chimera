from django.core.paginator import Paginator
from django.shortcuts import render_to_response, get_object_or_404
from django.db.models import Q
from django.http import HttpResponseRedirect

from chimera.workflows.models import Workflow
from chimera.workflows.models import WorkflowPart
from chimera.workflows.models import WorkflowStage
from chimera.workflows.models import WorkflowOutput
from chimera.workflows.models import WorkflowSchedule
from chimera.workflows.models import WorkflowForm
from chimera.workflows.models import WorkflowPartForm
from chimera.workflows.models import WorkflowStageForm
from chimera.workflows.models import WorkflowScheduleForm
from chimera.tags.models import Tag

from chimera import settings

from datetime import datetime
import re


def index(request):
    paginator = Paginator(Workflow.objects.all(), settings.PAGINATION)
    page = int(request.GET.get('page', '1'))
    pages = paginator.page(page)
    list = pages.object_list
    count = paginator.count
    page_total = paginator.num_pages
    return render_to_response('base_workflows.html', {'pages': pages,
                                                      'count': count,
                                                      'list': list,
                                                      'page_total': page_total})
def partindex(request):
    paginator = Paginator(WorkflowPart.objects.all(), settings.PAGINATION)
    page = int(request.GET.get('page', '1'))
    pages = paginator.page(page)
    list = pages.object_list
    count = paginator.count
    page_total = paginator.num_pages
    return render_to_response('base_workflows_parts.html', {'pages': pages,
                                                            'count': count,
                                                            'list': list,
                                                            'page_total': page_total})

def outputindex(request):
    paginator = Paginator(WorkflowOutput.objects.all(), settings.PAGINATION)
    page = int(request.GET.get('page', '1'))
    pages = paginator.page(page)
    list = pages.object_list
    count = paginator.count
    page_total = paginator.num_pages
    return render_to_response('base_workflows_output.html', {'list': list,
                                                             'pages': pages,
                                                             'page_total': page_total,
                                                             'count': count})

def graphserveroutput(request, id):
    my_wfo = WorkflowOutput.objects.get(pk=id)
    list = my_wfo._graph_output(id)
    stage = my_wfo.stage
    server = my_wfo.server
    if list is not None:
        return render_to_response('base_workflows_output_graph.html', {'list': list,
                                                                       'stage': stage,
                                                                       'server': server})
    else:
        return HttpResponseRedirect('/chimera/workflows/viewoutput/' + id)

def graphstageoutput(request, id):
    my_wfo = WorkflowOutput.objects.get(pk=id)
    list = my_wfo._graph_output(id, all=True)
    stage = my_wfo.stage
    if list is not None:
        return render_to_response('base_workflows_output_graph.html', {'list': list,
                                                                       'stage': stage})
    else:
        return HttpResponseRedirect('/chimera/workflows/viewoutput/' + id)

def scheduleindex(request):
    paginator = Paginator(WorkflowSchedule.objects.all(), settings.PAGINATION)
    page = int(request.GET.get('page', '1'))
    pages = paginator.page(page)
    list = pages.object_list
    count = paginator.count
    page_total = paginator.num_pages
    return render_to_response('base_workflows_schedules.html', {'pages': pages,
                                                                'count': count,
                                                                'list': list,
                                                                'page_total': page_total})

def delete(request, id):
    w = get_object_or_404(Workflow, pk=id)
    w.delete()
    return HttpResponseRedirect('/chimera/workflows/')

def deletepart(request, id):
    w = get_object_or_404(WorkflowPart, pk=id)
    w.delete()
    return HttpResponseRedirect('/chimera/workflows/parts/')

def deletestage(request, id):
    w = get_object_or_404(WorkflowStage, pk=id)
    wid = w.workflow.id
    w.delete()
    return HttpResponseRedirect('/chimera/workflows/viewstages/%d/' % wid)

def deleteschedule(request, id):
    w = get_object_or_404(WorkflowSchedule, pk=id)
    w.delete()
    return HttpResponseRedirect('/chimera/workflows/schedules/')

def edit(request, id):
    w = get_object_or_404(Workflow, pk=id)
    form = WorkflowForm(instance=w)
    return render_to_response('base_workflows_edit.html', {'form': form,
                                                           'workflow': w,
                                                           'undo': 'Delete'})

def editpart(request, id):
    w = get_object_or_404(WorkflowPart, pk=id)
    form = WorkflowPartForm(instance=w)
    return render_to_response('base_workflows_parts_edit.html', {'form': form,
                                                                 'workflowpart': w,
                                                                 'undo': 'Delete'})

def editstage(request, id):
    w = get_object_or_404(WorkflowStage, pk=id)
    form = WorkflowStageForm(instance=w)
    return render_to_response('base_workflows_stages_edit.html', {'form': form,
                                                                  'workflowstage': w,
                                                                  'undo': 'Delete'})

def viewstage(request, id):
    paginator = Paginator(WorkflowStage.objects.filter(workflow__id=id), settings.PAGINATION)
    page = int(request.GET.get('page', '1'))
    pages = paginator.page(page)
    list = pages.object_list
    count = paginator.count
    page_total = paginator.num_pages
    return render_to_response('base_workflows_stages.html', {'pages': pages,
                                                             'count': count,
                                                             'list': list,
                                                             'wid': id,
                                                             'w': Workflow.objects.get(pk=id),
                                                             'page_total': page_total})

def editschedule(request, id):
    w = get_object_or_404(WorkflowSchedule, pk=id)
    form = WorkflowScheduleForm(instance=w)
    return render_to_response('base_workflows_schedules_edit.html', {'form': form,
                                                                     'workflowschedule': w,
                                                                     'undo': 'Delete'})

def viewoutput(request, id):
    w = get_object_or_404(WorkflowOutput, pk=id)
    return render_to_response('base_workflows_output_view.html', {'wfo': w})

def new(request):
    w = Workflow()
    w.name = 'NEW WORKFLOW'
    w.description = 'Describe your workflow here'
    w.save()
    form = WorkflowForm(instance=w)
    return render_to_response('base_workflows_edit.html', {'form': form,
                                                           'workflow': w,
                                                           'undo': 'Cancel'})

def newpart(request):
    w = WorkflowPart()
    w.name = 'NEW WORKFLOW PART'
    w.save()
    form = WorkflowPartForm(instance=w)
    return render_to_response('base_workflows_parts_edit.html',
                              {'form': form,
                               'workflowpart': w,
                               'undo': 'Cancel'})

def newstage(request, id):
    w = WorkflowStage()
    w.part = WorkflowPart.objects.all()[0]
    w.workflow = Workflow.objects.get(pk=id)
    w.stage = 0
    w.save()
    form = WorkflowStageForm(instance=w)
    return render_to_response('base_workflows_stages_edit.html', {'form': form,
                                                                  'workflowstage': w,
                                                                  'undo': 'Cancel'})

def newschedule(request):
    w = WorkflowSchedule()
    w.name = 'NEW WORKFLOW SCHEDULE'
    t = Tag.objects.get(name='Test Servers')
    w.server_tag = t
    w.save()
    form = WorkflowScheduleForm(instance=w)
    return render_to_response('base_workflows_schedules_edit.html',
                              {'form': form,
                               'workflowschedule': w,
                               'undo': 'Cancel'})

def submit(request, id):
    w = get_object_or_404(Workflow, pk=id)
    form = WorkflowForm(request.POST, instance=w)
    if form.is_valid():
        form.save()
    else:
        return edit(request, id)
    render_to_response('base_workflows_edit.html', {'form': form,
                                                    'workflow': w,
                                                    'undo': 'Cancel'})
    return HttpResponseRedirect('/chimera/workflows/')

def submitpart(request, id):
    w = get_object_or_404(WorkflowPart, pk=id)
    form = WorkflowPartForm(request.POST, instance=w)
    if form.is_valid():
        form.save()
    else:
        return editpart(request, id)
    render_to_response('base_workflows_parts_edit.html',
                       {'form': form, 'workflowpart': w, 'undo': 'Cancel'})
    return HttpResponseRedirect('/chimera/workflows/parts/')

def submitstage(request, id):
    w = get_object_or_404(WorkflowStage, pk=id)
    wid = w.workflow.id
    form = WorkflowStageForm(request.POST, instance=w)
    if form.is_valid():
        form.save()
    else:
        return editstage(request, id)
    render_to_response('base_workflows_stages_edit.html', {'form': form,
                                                           'workflowstage': w,
                                                           'undo': 'Cancel'})
    return HttpResponseRedirect('/chimera/workflows/viewstages/%d/' % wid)

def submitschedule(request, id):
    w = get_object_or_404(WorkflowSchedule, pk=id)
    form = WorkflowScheduleForm(request.POST, instance=w)
    if form.is_valid():
        form.save()
    else:
        return editschedule(request, id)
    render_to_response('base_workflows_schedules_edit.html',
                       {'form': form, 'workflowschedule': w, 'undo': 'Cancel'})
    return HttpResponseRedirect('/chimera/workflows/schedules/')

def search(request):
    if request.GET.has_key('search'):
        qs = request.GET['search']
        request.session['search'] = qs
    elif request.session.has_key('search'):
        qs = request.session['search']
    try:
        # populate paginator object with search results
        results = Workflow.objects.filter(Q(name__icontains=qs) | \
                                          Q(description__icontains=qs))
        paginator = Paginator(results, settings.PAGINATION)
        page = int(request.GET.get('page', '1'))
        pages = paginator.page(page)
        list = pages.object_list
        count = paginator.count
        page_total = paginator.num_pages
        return render_to_response('base_workflows.html', {'qs': qs,
                                                          'list': list,
                                                          'pages': pages,
                                                          'page_total': page_total,
                                                          'count': count})
    except:
        return HttpResponseRedirect('/chimera/workflows/')


def searchpart(request):
    if request.GET.has_key('search'):
        qs = request.GET['search']
        request.session['search'] = qs
    elif request.session.has_key('search'):
        qs = request.session['search']
    try:
        # populate paginator object with search results
        results = WorkflowPart.objects.filter(Q(name__icontains=qs) | \
                                              Q(object__icontains=qs) | \
                                              Q(desc__icontains=qs))
        paginator = Paginator(results, settings.PAGINATION)
        page = int(request.GET.get('page', '1'))
        pages = paginator.page(page)
        list = pages.object_list
        count = paginator.count
        page_total = paginator.num_pages
        return render_to_response('base_workflows_parts.html', {'qs': qs,
                                                                'list': list,
                                                                'pages': pages,
                                                                'page_total': page_total,
                                                                'count': count})
    except:
        return HttpResponseRedirect('/chimera/workflows/parts/')


def searchstage(request):
    if request.GET.has_key('search'):
        qs = request.GET['search']
        request.session['search'] = qs
    elif request.session.has_key('search'):
        qs = request.session['search']
    try:
        # populate paginator object with search results
        results = WorkflowStage.objects.filter(Q(workflow__name__icontains=qs) | \
                                               Q(part__name__icontains=qs) | \
                                               Q(args__icontains=qs) | \
                                               Q(server__name__icontains=qs) | \
                                               Q(runas__icontains=qs))
        paginator = Paginator(results, settings.PAGINATION)
        page = int(request.GET.get('page', '1'))
        pages = paginator.page(page)
        list = pages.object_list
        count = paginator.count
        page_total = paginator.num_pages
        return render_to_response('base_workflows_stages.html', {'qs': qs,
                                                                 'list': list,
                                                                 'pages': pages,
                                                                 'page_total': page_total,
                                                                 'count': count})
    except:
        return HttpResponseRedirect('/chimera/workflows/stages')

def searchoutput(request):
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
        # populate paginator object with search results
        if op and q:
            if op == 'date':
                if q == 'today':
                    q = datetime.today()
                else:
                    q = datetime.strptime(q, "%Y-%m-%d")
                q_year  = q.year
                q_month = q.month
                q_day   = q.day
                paginator = Paginator(WorkflowOutput.objects.filter(Q(date__year=q_year) & \
                                                                    Q(date__month=q_month) & \
                                                                    Q(date__day=q_day)),
                                                                    settings.PAGINATION)
            elif op == 'server':
                paginator = Paginator(WorkflowOutput.objects.filter(Q(server__name__icontains=q)), 
                                                                    settings.PAGINATION)
            elif op == 'workflow':
                paginator = Paginator(WorkflowOutput.objects.filter(Q(stage__workflow__name__icontains=q)), 
                                                                    settings.PAGINATION)
            elif op == 'part':
                paginator = Paginator(WorkflowOutput.objects.filter(Q(part_args__icontains=q)), 
                                                                    settings.PAGINATION)
            elif op == 'retval':
                paginator = Paginator(WorkflowOutput.objects.filter(Q(retval__icontains=q)), 
                                                                    settings.PAGINATION)
            elif op == 'stdout':
                paginator = Paginator(WorkflowOutput.objects.filter(Q(stdout__icontains=q)), 
                                                                    settings.PAGINATION)
            elif op == 'stderr':
                paginator = Paginator(WorkflowOutput.objects.filter(Q(stderr__icontains=q)), 
                                                                    settings.PAGINATION)
        else:
            paginator = Paginator(WorkflowOutput.objects.filter(Q(server__name__icontains=qs) | \
                                                                Q(stage__workflow__name__icontains=qs) | \
                                                                Q(part_args__icontains=qs) | \
                                                                Q(stdin__icontains=qs) | \
                                                                Q(retval__icontains=qs) | \
                                                                Q(stdout__icontains=qs) | \
                                                                Q(stderr__icontains=qs)),
                                                                settings.PAGINATION)
        page = int(request.GET.get('page', '1'))
        pages = paginator.page(page)
        list = pages.object_list
        count = paginator.count
        page_total = paginator.num_pages
        return render_to_response('base_workflows_output.html', {'qs': qs,
                                                                 'list': list,
                                                                 'pages': pages,
                                                                 'page_total': page_total,
                                                                 'count': count})
    except:
        return HttpResponseRedirect('/chimera/workflows/output/')

def searchschedule(request):
    if request.GET.has_key('search'):
        qs = request.GET['search']
        request.session['search'] = qs
    elif request.session.has_key('search'):
        qs = request.session['search']
    try:
        # populate paginator object with search results
        results = WorkflowSchedule.objects.filter(Q(name__icontains=qs))
        paginator = Paginator(results, settings.PAGINATION)
        page = int(request.GET.get('page', '1'))
        pages = paginator.page(page)
        list = pages.object_list
        count = paginator.count
        page_total = paginator.num_pages
        return render_to_response('base_workflows_schedules.html', {'qs': qs,
                                                                    'list': list,
                                                                    'pages': pages,
                                                                    'page_total': page_total,
                                                                    'count': count})
    except:
        return HttpResponseRedirect('/chimera/workflows/schedules/')

