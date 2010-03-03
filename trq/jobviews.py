from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import render_to_response
from models import JobState
from models import Job
from models import Queue
from models import User
from models import TorqueServer
from helpers import BooleanListForm
from django import forms
import colorsys
import matplotlib
matplotlib.use('Agg')
from pylab import *
import StringIO


class JobsStatsForm(forms.Form):
    """
    Form with options to query job statistics.
    """
    wfrom = forms.DateField(
        label="Start", widget=forms.DateInput(attrs={'class':'vDateField'}))
    wto = forms.DateField(
        label="End", widget=forms.DateInput(attrs={'class':'vDateField'}))

def jobs_overview(request, page=1):
    state_list = []
    if request.POST:
        for key,val in request.POST.items():
            prefix, attr = key.split("_", 1)
            if prefix == "jobstates":
                if 'on' in val:
                    state_list.append(attr)
        request.session['state_list'] = state_list
    else:
        state_list = request.session.get('state_list', [])

    if len(state_list)==0:
        object_list = Job.objects.all()
    else:
        object_list = Job.objects.filter(
            job_state__name__in=state_list).distinct()
        
    paginator = Paginator(object_list, 20)
        
    if int(page)>paginator.num_pages:
        page=1
    jobs_page = paginator.page(page)

    states = [x.name for x in JobState.objects.all()]
    states_form = BooleanListForm('jobstates_')
    states_form.setFields(states)
    if request.POST:
        states_form.setData(request.POST, useprefix=False)
    else:
        states_form.setData( dict(zip(state_list, len(state_list)*[True])) )

    return render_to_response(
        'trq/jobs_overview.html',
        {'jobs_page':jobs_page, 'paginator':paginator,
        'states_form':states_form}
        )


def job_detail(request, servername, jobid):
    server = TorqueServer.objects.get(name=servername)
    job = Job.objects.get(jobid=jobid, server=server)
    return render_to_response(
        'trq/job_detail.html',
        {'job':job}
        )

def stats(request):
    jobs = dfrom = dto = None
    if request.POST:
        if request.POST.has_key('wfrom'):
            dfrom = request.POST['wfrom']
        if request.POST.has_key('wto'):
            dto = request.POST['wto']
    jobs=[]
    graph_data = {}
    if dfrom and dto:
        jobs=Job.objects.filter(start_time__gte=dfrom, 
            comp_time__lte=dto)
        for q in Queue.objects.all().order_by('name'):
            graph_data[q.name] = jobs.filter(queue=q).count()
    query_form = JobsStatsForm()
    if request.POST:
        query_form.data['wfrom'] = request.POST['wfrom']
        query_form.data['wto'] = request.POST['wto']
        query_form.is_bound = True
    return render_to_response(
        'trq/jobs_stats.html', 
        {'query_form':query_form, 'jobs':jobs, 'graph_data':graph_data}
        )

def graph(request):
    fig = figure(1, figsize=(4,4))
    ax = axes([0.1, 0.1, 0.8, 0.8])
    labels = []
    fracs = []
    others = 0
    totalval = 100
    totalval = sum([int(i) for i in request.GET.values()])
    for k,v in request.GET.items():
        if float(v)<(totalval/20):
            others += float(v)
        else:
            labels.append(k)
            fracs.append(v)
    labels.append('others')
    fracs.append(others)
    colors = []
    for i in range(0,len(fracs)):
        c = colorsys.hsv_to_rgb(float(i)/len(fracs),1,1)
        colors.append( c )
    pie(fracs, labels=labels, colors=colors, autopct='%1.1f%%')
#    legend(labels, 'best')
    response = HttpResponse(mimetype='image/png')
    fig.savefig(response)
    fig.clear()
    return response

# vi:ts=4:sw=4:expandtab
