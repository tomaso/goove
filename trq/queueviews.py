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
import numpy as np
import colorsys

def queues_overview(request):
    queues = Queue.objects.all()
    job_states = JobState.objects.all()
    return render_to_response(
        'trq/queues_overview.html',
        {'queues_list':queues, 'job_states':job_states}
        )


def queue_detail(request, queuename):
    queue = Queue.objects.get(name=queuename)
    running_jobs = Job.objects.filter(queue=queue)
    return render_to_response(
        'trq/queue_detail.html',
        {'queue':queue, 'running_jobs':running_jobs}
        )

class QueuesStatsForm(forms.Form):
    """
    Form with options for queues statistics.
    """
    wfrom = forms.DateField(
        label="Start", widget=forms.DateInput(attrs={'class':'vDateField'}))
    wto = forms.DateField(
        label="End", widget=forms.DateInput(attrs={'class':'vDateField'}))
    

def queues_stats(request):
    stat_form = QueuesStatsForm()
    for q in Queue.objects.all():
        stat_form.fields['queue_'+q.name] = forms.BooleanField(label=q.name, required=False)
    if request.POST:
        stat_form.data['wfrom'] = request.POST['wfrom']
        stat_form.data['wto'] = request.POST['wto']
        stat_form.is_bound = True

    graph_data = None
    if request.POST:
        graph_data = request.POST
    return render_to_response(
        'trq/queues_stats.html',
        {'stat_form':stat_form, 'graph_data':graph_data}
        )

# TODO: make two variants: full big pic
# and smaller with just few values as a preview
def graph(request):
    sfrom = request.GET['wfrom'].split('-')
    dfrom = date(int(sfrom[0]), int(sfrom[1]), int(sfrom[2]))
    sto = request.GET['wto'].split('-')
    dto = date(int(sto[0]), int(sto[1]), int(sto[2]))
    N = (dto-dfrom).days

    queue_names = []
    for key,val in request.GET.items():
        if key.startswith('queue_'):
            queue_names.append(key[len('queue_'):])

    fig = figure(1, figsize=(8,6))
    ax = axes([0.1, 0.2, 0.8, 0.8])
    menMeans   = (20, 35, 30, 35, 30)
    womenMeans = (25, 32, 34, 20, 30)
    ind = np.arange(N)    # the x locations for the groups
    width = 1       # the width of the bars: can also be len(x) sequence
    bars = []
    i = 0
    fromdates = []
    todates = []
    for j in range(0,N):
        f = date.fromordinal(dfrom.toordinal()+j).isoformat()
        t = date.fromordinal(dfrom.toordinal()+j+1).isoformat()
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
            val = Job.objects.filter(queue__name=q, comp_time__gte=f, comp_time__lte=t).count()
            values.append(val)

        b = bar(ind, values, width, color=c, bottom=tempsum, linewidth=0)
        bars.append(b)
        for j in range(0,N):
            tempsum[j] += values[j]

    ylabel('Number of jobs')
    title('Completed jobs per day')
    xticks(ind+width/2.0, fromdates, rotation=90)
    gmax = int(max(tempsum)*1.2)
    if gmax==0:
        yticks((0,1))
    else:
        yticks(np.arange(0, gmax, gmax/5))
    print bars
    legend( (b[0] for b in bars), queue_names )
    response = HttpResponse(mimetype='image/png')
    fig.savefig(response)
    fig.clear()
    return response


# vi:ts=4:sw=4:expandtab
