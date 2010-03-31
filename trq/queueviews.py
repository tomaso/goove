from django.http import HttpResponse
from django.shortcuts import render_to_response
from models import Node
from models import SubCluster
from models import NodeProperty
from models import NodeState
from models import Job
from models import JobState
from models import Queue
from django import forms
import matplotlib
matplotlib.use('Agg')
from pylab import *
from datetime import date
from time import time
import numpy as np
import colorsys
from django.db.models import Sum

def queues_overview(request):
    queues = Queue.objects.all()
    job_states = JobState.objects.all()
    return render_to_response(
        'trq/queues_overview.html',
        {'queues_list':queues, 'job_states':job_states}
        )


def queue_detail(request, queuename):
    queue = Queue.objects.get(name=queuename)
    running_jobs = Job.objects.filter(queue=queue, job_state__shortname="R")
    return render_to_response(
        'trq/queue_detail.html',
        {'queue':queue, 'running_jobs':running_jobs}
        )

class QueuesStatsForm(forms.Form):
    """
    Form with options for queues statistics.
    """
    graph_type = forms.ChoiceField(
        label="Graph type", choices=(('bars','Aggregated bars'),('pie','Pie chart')))
    wfrom = forms.DateField(
        label="Start", widget=forms.DateInput(attrs={'class':'vDateField'}))
    wto = forms.DateField(
        label="End", widget=forms.DateInput(attrs={'class':'vDateField'}))
    aggregation = forms.ChoiceField(
        label="Aggregate", choices=(('day','day'),('week','week'),('month','month')))
    data_type = forms.ChoiceField(
        label="Data", choices=(('jobcount','Number of jobs'),('walltime','Wall time'),('cputime','CPU time')))
    

def queues_stats(request):
    stat_form = QueuesStatsForm()
    for q in Queue.objects.all():
        stat_form.fields['queue_'+q.name] = forms.BooleanField(label=q.name, required=False)
        stat_form.data['queue_'+q.name] = True
        stat_form.is_bound = True
    if request.POST:
        stat_form.data['graph_type'] = request.POST['graph_type']
        stat_form.data['wfrom'] = request.POST['wfrom']
        stat_form.data['wto'] = request.POST['wto']
        stat_form.data['aggregation'] = request.POST['aggregation']
        stat_form.data['data_type'] = request.POST['data_type']
        for q in Queue.objects.all():
            if request.POST.has_key('queue_'+q.name):
                stat_form.data['queue_'+q.name] = request.POST['queue_'+q.name]
            else:
                stat_form.data['queue_'+q.name] = False
        stat_form.is_bound = True
        

    graph_data = False
    if request.POST:
        graph_data = request.POST
    return render_to_response(
        'trq/queues_stats.html',
        {'stat_form':stat_form, 'graph_data':graph_data}
        )


def nextmonth(indate):
    """ Return date representing the first day of the next month.
    """
    m = indate.month + 1
    y = indate.year
    if m > 12:
        m = 1
        y = y + 1
    return date(y,m,1)



def graph_pie(dfrom, dto, data_type, queue_names, figsize, dpi):
    fig = figure(1, figsize=(figsize,figsize))
    ax = axes([0.1, 0.1, 0.8, 0.8])
    labels = []
    fracs = []
    queue_vals = {}
    others = 0
    for q in queue_names:
        if data_type == 'jobcount':
            val = Job.objects.filter(queue__name=q, comp_time__gte=dfrom, comp_time__lte=dto).count()
        elif data_type == 'cputime':
            val = (Job.objects.filter(queue__name=q, comp_time__gte=dfrom, comp_time__lte=dto).aggregate(Sum("cput"))['cput__sum'] or 0)
        elif data_type == 'walltime':
            val = (Job.objects.filter(queue__name=q, comp_time__gte=dfrom, comp_time__lte=dto).aggregate(Sum("walltime"))['walltime__sum'] or 0)
        queue_vals[q] = val

    print queue_vals
    totalval = sum([int(i) for i in queue_vals.values()])
    for k,v in queue_vals.items():
        if float(v)<(totalval/100):
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
    title("Completed jobs between %s and %s" % (dto, dfrom))
    pie(fracs, labels=labels, colors=colors, autopct='%1.1f%%')
    response = HttpResponse(mimetype='image/png')
    fig.savefig(response, dpi=dpi)
    fig.clear()
    return response 

    

# TODO: make two variants: full big pic
# and smaller with just few values as a preview
def graph(request):
    sfrom = request.GET['wfrom'].split('-')
    dfrom = date(int(sfrom[0]), int(sfrom[1]), int(sfrom[2]))
    sto = request.GET['wto'].split('-')
    dto = date(int(sto[0]), int(sto[1]), int(sto[2]))
    graph_type = request.GET['graph_type']
    aggregation = request.GET['aggregation']
    data_type = request.GET['data_type']

    queue_names = []
    for key,val in request.GET.items():
        if key.startswith('queue_'):
            queue_names.append(key[len('queue_'):])
    figsize = 10
    dpi = 60

    if graph_type=='pie':
        return graph_pie(dfrom, dto, data_type, queue_names, figsize, dpi)

    if aggregation=='day':
        N = (dto-dfrom).days+1
    elif aggregation=='week':
        dfrom = date.fromordinal(dfrom.toordinal()-dfrom.weekday())
        dto = date.fromordinal(dto.toordinal()+(6-dto.weekday()))
        N = ((dto-dfrom).days+1)/7
    else: # month
        dfrom = date(dfrom.year, dfrom.month, 1)
        dto = nextmonth(dto)
        N = (dto.year-dfrom.year)*12+(dto.month-dfrom.month+1)
        
    xtick_width = 30

    fig = figure(1, figsize=(figsize,figsize))
    ax = axes([0.1, 0.2, 0.7, 0.75])
    menMeans   = (20, 35, 30, 35, 30)
    womenMeans = (25, 32, 34, 20, 30)
    ind = np.arange(N)    # the x locations for the groups
    width = 1       # the width of the bars: can also be len(x) sequence
    bars = []
    i = 0
    fromdates = []
    todates = []
    for j in range(0,N):
        if aggregation=='day':
            f = date.fromordinal(dfrom.toordinal()+j).isoformat()
            t = date.fromordinal(dfrom.toordinal()+j+1).isoformat()
        elif aggregation=='week':
            f = date.fromordinal(dfrom.toordinal()+j*7).isoformat()
            t = date.fromordinal(dfrom.toordinal()+(j+1)*7).isoformat()
        else:
            if j==0:
                f = dfrom
            else:
                f = todates[-1]
            t = nextmonth(f)
        fromdates.append(f)
        todates.append(t)

    tempsum = [0]*N
    for q in queue_names:
        c = colorsys.hsv_to_rgb(float(i)/len(queue_names),1,1)
        i += 1
        values = []
        for j in range(0,N):
            f = fromdates[j]
            t = todates[j]
            if data_type == 'jobcount':
                val = Job.objects.filter(queue__name=q, comp_time__gte=f, comp_time__lte=t).count()
            elif data_type == 'cputime':
                val = (Job.objects.filter(queue__name=q, comp_time__gte=f, comp_time__lte=t).aggregate(Sum("cput"))['cput__sum'] or 0)
            elif data_type == 'walltime':
                val = (Job.objects.filter(queue__name=q, comp_time__gte=f, comp_time__lte=t).aggregate(Sum("walltime"))['walltime__sum'] or 0)
                
            values.append(val)

        b = bar(ind, values, width, color=c, bottom=tempsum, linewidth=0)
        bars.append(b)
        for j in range(0,N):
            tempsum[j] += values[j]

    if data_type == 'jobcount':
        ylabel('Number of jobs')
        title('Completed jobs per time unit')
    elif data_type == 'cputime':
        ylabel('Wall time')
        title('Wall time of completed jobs')
    elif data_type == 'walltime':
        ylabel('CPU time')
        title('CPU time of completed jobs')
    nth = int(1.0+((1.0*N)/(figsize*dpi/xtick_width)))
    arr = ind+width/2.0
    xticks(arr[::nth], fromdates[::nth], rotation=90)
    gmax = int(max(tempsum)*1.2)
    if gmax==0:
        yticks((0,1))
    else:
        yticks(np.arange(0, gmax, gmax/5))
    legend( (b[0] for b in bars), queue_names , (1.01, 0.0) )
    response = HttpResponse(mimetype='image/png')
    fig.savefig(response, dpi=dpi)
    fig.clear()
    return response


# vi:ts=4:sw=4:expandtab
