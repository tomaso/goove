from django.http import HttpResponse
from helpers import render_to_response_with_config,getColorArray
from models import Node
from models import SubCluster
from models import NodeProperty
from models import NodeState
from models import Job
from models import JobState
from models import Queue
from models import TorqueServer
from django import forms
import matplotlib
matplotlib.use('Agg')
from pylab import *
from datetime import date
from time import time
import numpy as np
import colorsys
from django.db import connection, transaction
from django.db.models import Avg, Max, Min, Count, Sum

class QueueSelectForm(forms.Form):
    queue = forms.ChoiceField(
        label="Queue",
        initial=Queue.objects.all()[0],
        choices=[ (q['pk'],"%s@%s" % (q['name'],q['server__name'])) for q in Queue.objects.values('pk','name','server__name') ]
    )

def queues_overview(request):
    servers_name = TorqueServer.objects.all().values_list('name')
    job_states_name = JobState.objects.all().values_list('name')

    restable = {}
    for sn in servers_name:
        restable[sn[0]] = {}
        queues_name = Queue.objects.filter(server__name=sn[0]).values_list('name')
        for qn in queues_name:
            restable[sn[0]][qn[0]] = {}
            for jsn in job_states_name:
                restable[sn[0]][qn[0]][jsn[0]] = 0
    queue_results = Job.objects.all().values('server__name', 'queue__name','job_state__name').annotate(Count('job_state'))
    for qr in queue_results:
        restable[qr['server__name']][qr['queue__name']][qr['job_state__name']] += qr['job_state__count']

    return render_to_response_with_config(
        'trq/queues_overview.html',
        {'restable':restable
        }
    )
    

def queue_detail(request, servername=None, queuename=None):
    queue_form = QueueSelectForm()
        
    queue = None
    if queuename and servername:
        queue = Queue.objects.get(name=queuename, server__name=servername)
    if request.POST.has_key('queue'):
        queue = Queue.objects.get(pk=request.POST['queue'])

    if not queue:
        return render_to_response_with_config(
            'trq/queue_detail.html',
            {'queue':None, 'queue_form':queue_form}
            )

    queue_form.data['queue'] = queue.pk
    queue_form.is_bound = True

    running_jobs = Job.objects.filter(queue=queue, job_state__shortname="R")
    return render_to_response_with_config(
        'trq/queue_detail.html',
        {'queue':queue, 'running_jobs':running_jobs, 'queue_form':queue_form}
        )

class QueuesStatsForm(forms.Form):
    """
    Form with options for queues statistics.
    """
    graph_type = forms.ChoiceField(
        label="Graph type", choices=(('bars','Aggregated bars'),('pie','Pie chart')))
    wfrom = forms.DateField(
        label="Start", 
        initial=date.fromordinal(date.today().toordinal()-1).isoformat(),
        widget=forms.DateInput(attrs={'class':'vDateField'})
    )
    wto = forms.DateField(
        label="End", 
        initial=date.today().isoformat(),
        widget=forms.DateInput(attrs={'class':'vDateField'})
    )
    aggregation = forms.ChoiceField(
        label="Aggregate", choices=(('day','day'),('week','week'),('month','month')))
    data_type = forms.ChoiceField(
        label="Data", choices=(('jobcount','Number of jobs'),('walltime','Wall time'),('cputime','CPU time')))
    

def queues_stats(request):
    stat_form = QueuesStatsForm()
    queues_form = forms.Form()


    for ts in TorqueServer.objects.all():
        ch = []
        for q in Queue.objects.filter(server=ts).order_by('name'):
            ch.append(('queue_'+str(q.pk),q.name))
        queues_form.fields['server_'+str(ts.pk)] = forms.MultipleChoiceField(
            choices=ch, label=ts.name, widget=forms.SelectMultiple(attrs={'class':'dropdown_qlist'})) 
        queues_form.is_bound = True

    if request.POST:
        stat_form.data['graph_type'] = request.POST['graph_type']
        stat_form.data['wfrom'] = request.POST['wfrom']
        stat_form.data['wto'] = request.POST['wto']
        stat_form.data['aggregation'] = request.POST['aggregation']
        stat_form.data['data_type'] = request.POST['data_type']
        stat_form.is_bound = True
        for ts in TorqueServer.objects.all():
            if request.POST.has_key('server_'+str(ts.pk)):
                queues_form.data['server_'+str(ts.pk)] = request.POST.getlist('server_'+str(ts.pk))
        queues_form.is_bound = True
        

    graph_data = False
    graph_values = False
    if request.POST:
        graph_data = request.POST
        graph_values = get_graph_values(graph_data)
    return render_to_response_with_config(
        'trq/queues_stats.html',
        {'stat_form':stat_form, 'queues_form':queues_form,
        'graph_data':graph_data, 'graph_values':graph_values}
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
    
    totalval = sum([int(i) for i in queue_vals.values()])
    for k,v in queue_vals.items():
        if float(v)<(totalval/100):
            others += float(v)
        else:
            labels.append(k)
            fracs.append(v)
    labels.append('others')
    fracs.append(others)
    colors = getColorArray(len(fracs))
    title("Completed jobs between %s and %s" % (dfrom, dto))
    pie(fracs, labels=labels, colors=colors, autopct='%1.1f%%')
    response = HttpResponse(mimetype='image/png')
    fig.savefig(response, dpi=dpi)
    fig.clear()
    return response 

def get_graph_values(items):
    """ This function just returns the raw data that can be used for 
    drawing the graph. It takes the parameters for the query from request.POST object. """
    sfrom = items['wfrom'].split('-')
    dfrom = date(int(sfrom[0]), int(sfrom[1]), int(sfrom[2]))
    sto = items['wto'].split('-')
    dto = date(int(sto[0]), int(sto[1]), int(sto[2]))
    graph_type = items['graph_type']
    aggregation = items['aggregation']
    data_type = items['data_type']
    graph_values = {}
    if data_type == 'jobcount':
        graph_values['ylabel']='Number of jobs'
        graph_values['title']='Completed jobs per time unit'
        data_type_arg=Count("pk")
        data_type_res='pk__count'
    elif data_type == 'cputime':
        graph_values['ylabel']='Wall time'
        graph_values['title']='Wall time of completed jobs'
        data_type_arg=Sum("cput")
        data_type_res='cput__sum'
    elif data_type == 'walltime':
        graph_values['ylabel']='CPU time'
        graph_values['title']='CPU time of completed jobs'
        data_type_arg=Sum("walltime")
        data_type_res='walltime__sum'

    queue_pks = []
    for ts in TorqueServer.objects.all():
        for q in items.getlist('server_'+str(ts.pk)):
            if q.startswith('queue_'):
                queue_pks.append(q[len('queue_'):])
    queue_pks.sort()
    

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

    graph_values['values'] = []
    queue_names = {}
    for q in Queue.objects.all().values('pk','name','server__name'): 
        queue_names[q['pk']]="%s@%s" % (q['name'], q['server__name'])
    graph_values['queues']  = []
    for pk in queue_pks:
        graph_values['queues'].append(queue_names[int(pk)])
    graph_values['queues_colors'] = []
    for q in queue_pks:
        graph_values['queues_colors'].append(Queue.objects.get(pk=q).color)
    
    for j in range(0,N):
        rr = {}
        rr['date'] = fromdates[j]
        out = Job.objects.filter(comp_time__range=(fromdates[j], todates[j])).values('queue__pk').annotate(data_type_arg)
        od = {}
        for i in out:
            od[str(i['queue__pk'])]=i[data_type_res]
        rr['queues'] = []
        for q in queue_pks:
            if od.has_key(q):
                rr['queues'].append(od[q])
            else:
                rr['queues'].append(0)
        graph_values['values'].append(rr)

    return graph_values
    

# TODO: make two variants: full big pic
# and smaller with just few values as a preview
def graph(request):
    graph_values = get_graph_values(request)
    figsize = 10
    dpi = 60

#    if graph_type=='pie':
#        return graph_pie(dfrom, dto, data_type, queue_names, figsize, dpi)
        
    xtick_width = 30

    fig = figure(1, figsize=(figsize,figsize))
    ax = axes([0.1, 0.2, 0.7, 0.75])
    ind = np.arange(N)    # the x locations for the groups
    width = 1       # the width of the bars: can also be len(x) sequence
    bars = []


        

    tempsum = [0]*N
    i = 0
    for q in queue_names:
        c = colorsys.hsv_to_rgb(float(i)/len(queue_names),1,1)
        i += 1
        values = []
        for j in range(0,N):
            f = fromdates[j]
            t = todates[j]
            if (not rr.has_key(q)) or (not rr[q].has_key(f)):
                val = 0
            else:
                val = rr[q][f]
#            if data_type == 'jobcount':
#                val = Job.objects.filter(queue__name=q, comp_time__gte=f, comp_time__lte=t).count()
#            elif data_type == 'cputime':
#                val = (Job.objects.filter(queue__name=q, comp_time__gte=f, comp_time__lte=t).aggregate(Sum("cput"))['cput__sum'] or 0)
#            elif data_type == 'walltime':
#                val = (Job.objects.filter(queue__name=q, comp_time__gte=f, comp_time__lte=t).aggregate(Sum("walltime"))['walltime__sum'] or 0)
#                
            values.append(val)

        b = bar(ind, values, width, color=c, bottom=tempsum, linewidth=0)
        bars.append(b)
        for j in range(0,N):
            tempsum[j] += values[j]

    ylabel(graph_values['ylabel'])
    title(graph_values['title'])
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
