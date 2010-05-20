from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import render_to_response
from models import JobState
from models import Job
from models import Queue
from models import User
from models import Node
from models import TorqueServer
from models import AccountingEvent
from helpers import BooleanListForm
from django import forms
import colorsys
import matplotlib
matplotlib.use('Agg')
from pylab import *
import datetime
from datetime import date


class JobsStatsForm(forms.Form):
    """
    Form with options to query job statistics.
    """
    wfrom = forms.DateField(
        label="Start", widget=forms.DateInput(attrs={'class':'vDateField'}))
    wto = forms.DateField(
        label="End", widget=forms.DateInput(attrs={'class':'vDateField'}))

class WalltimeLow():
    description = 'Big difference between recorded walltime and current-start time'
    label = 'Walltime'

    def isProblem(self,j):
        """
        Test if the job j is problematic. This routine does not
        check the status of the job (it is expected to be Running)
        """
        if j.walltime and j.start_time:
            walldays = j.walltime/(60*60*24)
            nowdays = (datetime.datetime.now() - j.start_time).days
            return (walldays + 1 <= nowdays)

        return False


wl = WalltimeLow()

class SuspicionForm(forms.Form):
    """
    Form to filter what kind of suspicious jobs user wants to see.
    """
    # this should be kinda dynamic
    susp1 = forms.BooleanField(
        label=wl.label,
        initial=True,
        widget=forms.CheckboxInput(attrs={'title':wl.description})
    )


class CompletedForm(forms.Form):
    """
    Form with filters on completed jobs.
    """
    # TODO: many more fields here
    wfrom = forms.DateField(
        label="Completed after", 
        initial=date.fromordinal(date.today().toordinal()-1).isoformat(),
        widget=forms.DateInput(attrs={'class':'vDateField'})
    )
    wto = forms.DateField(
        label="Completed before", 
        initial=date.today().isoformat(),
        widget=forms.DateInput(attrs={'class':'vDateField'})
    )
    mineff = forms.IntegerField(
        label="Minimum Efficiency",
        initial=0
    )
    maxeff = forms.IntegerField(
        label="Maximum Efficiency",
        initial=100
    )
    minwalltime = forms.IntegerField(
        label="Minimum Walltime", 
        initial=0,
        widget=forms.TextInput(attrs={'title':'Minimum walltime in seconds'})
    )
    mincput = forms.IntegerField(
        label="Minimum CPUTime",
        initial=0,
        widget=forms.TextInput(attrs={'title':'Minimum CPU time in seconds'})
    )
    queue = forms.ChoiceField(
        label="Queue", 
        initial=0,
        choices=[ (0,'All') ]+[ (q.pk,q.name) for q in Queue.objects.all() ]
    )
    user = forms.ChoiceField(
        label="User",
        initial=0,
        choices=[ (0,'All') ]+[ (u.pk,u.name) for u in User.objects.all() ]
    )
    node = forms.ChoiceField(
        label="Node",
        initial=0,
        choices=[ (0,'All') ]+[ (n.pk,n.name) for n in Node.objects.all() ]
    )
    page = forms.IntegerField(
        initial=1,
        widget=forms.HiddenInput()
    )

class JobSelectForm(forms.Form):
    server = forms.ChoiceField(
        label="Server",
        initial=TorqueServer.objects.all()[0],
        choices=[ (ts.pk,ts.name) for ts in TorqueServer.objects.all() ]
    )
    jobid = forms.IntegerField(
        label="Job ID",
        initial=1
    )
    


def jobs_completed_listing(request):
    comp_form = CompletedForm()
    if not request.POST:
        return render_to_response(
            'trq/jobs_completed_listing.html',
            {'jobs_page':[], 'paginator':None,
            'comp_form':comp_form}
        )

    comp_form.data['wfrom'] = request.POST['wfrom']
    comp_form.data['wto'] = request.POST['wto']
    comp_form.data['mineff'] = request.POST['mineff']
    comp_form.data['maxeff'] = request.POST['maxeff']
    comp_form.data['minwalltime'] = request.POST['minwalltime']
    comp_form.data['mincput'] = request.POST['mincput']
    comp_form.data['queue'] = request.POST['queue']
    comp_form.data['user'] = request.POST['user']
    comp_form.data['node'] = request.POST['node']
    comp_form.data['page'] = request.POST['page']
    if request.POST['submit']=='>>':
        comp_form.data['page'] = int(comp_form.data['page']) + 1
    elif request.POST['submit']=='<<':
        comp_form.data['page'] = int(comp_form.data['page']) - 1

    comp_form.is_bound = True

    args = { 
        'job_state__shortname':'C', 
        'comp_time__range':(comp_form.data['wfrom'], comp_form.data['wto']), 
        'efficiency__range':(comp_form.data['mineff'], comp_form.data['maxeff']),
        'walltime__gte':comp_form.data['minwalltime'],
        'cput__gte':comp_form.data['mincput']
    }
    if comp_form.data['queue'] != '0':
        args['queue__pk'] = comp_form.data['queue']

    if comp_form.data['user'] != '0':
        args['job_owner__pk'] = comp_form.data['user']

    if comp_form.data['node'] != '0':
        args['exec_host__pk'] = comp_form.data['node']

    object_list = Job.objects.filter(**args)
        
    page = int(comp_form.data['page'])
    paginator = Paginator(object_list, 50)
    if page>paginator.num_pages:
        page=1
    jobs_page = paginator.page(page)

    return render_to_response(
        'trq/jobs_completed_listing.html',
        {'jobs_page':jobs_page, 'paginator':paginator,
        'comp_form':comp_form}
        )


def job_detail(request, servername=None, jobid=None):
    select_form = JobSelectForm()
    if not request.POST and jobid==None:
        return render_to_response(
            'trq/job_detail.html',
            {'select_form':select_form, 'job':None, 'accevents':[]}
        )

    if request.POST:
        server = TorqueServer.objects.get(pk=request.POST['server'])
        job = Job.objects.get(jobid=request.POST['jobid'], server=server)
        select_form.data['server'] = request.POST['server']
        select_form.data['jobid'] = request.POST['jobid']
    else:
        server = TorqueServer.objects.get(name=servername)
        job = Job.objects.get(jobid=jobid, server=server)
        select_form.data['server'] = server.pk
        select_form.data['jobid'] = jobid
    select_form.is_bound = True

    accevents = AccountingEvent.objects.filter(job=job)
    return render_to_response(
        'trq/job_detail.html',
        {'select_form':select_form, 'job':job, 'accevents':accevents}
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
    response = HttpResponse(mimetype='image/png')
    fig.savefig(response)
    fig.clear()
    return response

def suspicious(request):
    """
    Get lists of suspicious jobs (various reasons)
    and render page with them.
    """
    current_date = datetime.date.today()
    jobs = []
    for j in Job.objects.filter(job_state__shortname="R"):
        if wl.isProblem(j):
            jobs.append(j)
    sf = SuspicionForm()
    print sf
    print jobs
    return render_to_response(
        'trq/jobs_suspicious.html', 
        {'suspicion_form':sf, 'suspicious_jobs':jobs}
        )

# vi:ts=4:sw=4:expandtab
