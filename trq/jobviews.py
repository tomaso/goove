from django.core.paginator import Paginator
from django.http import HttpResponse
from models import JobState
from models import Job
from models import Queue
from models import User
from models import Group
from models import GridUser
from models import Node
from models import TorqueServer
from models import AccountingEvent
from models import SubmitHost
from helpers import BooleanListForm,UpdateRunningJob,render_to_response_with_config
from django import forms
import colorsys
import matplotlib
matplotlib.use('Agg')
from pylab import *
import datetime
from datetime import date
from django.db.models import Avg, Max, Min, Count, Sum


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

class FairshareForm(forms.Form):
    """
    Form to select fairshare view parameters.
    """
    timescale = forms.ChoiceField(
        label="Time to inspect",
        initial=60,
        choices=[ (0,"Other"), (60,"Hour"), (1440,"Day"), (10080,"7 days"), (40320, "28 days") ]
    )
    minutes = forms.IntegerField(
        label="Minutes", 
        initial=60,
        widget=forms.TextInput(attrs={'title':'Time to inspect in minutes'})
    )
    entity = forms.ChoiceField(
        label="Fairshare entity",
        initial=0,
        choices=[ (0,'Queue'), (1,'Group'), (2,'User') ]
    )

class CompletedForm(forms.Form):
    """
    Form with filters on completed jobs.
    """
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
        choices=[ (0,'Any') ]+[ (q.pk,q.name) for q in Queue.objects.all() ]
    )
    user = forms.ChoiceField(
        label="User",
        initial=0,
        choices=[ (0,'Any') ]+[ (u.pk,u.name) for u in User.objects.all() ]
    )
    group = forms.ChoiceField(
        label="Group",
        initial=0,
        choices=[ (0,'Any') ]+[ (g.pk,g.name) for g in Group.objects.all() ]
    )
    griduser = forms.ChoiceField(
        label="Grid user",
        initial=0,
        choices=[ (0,'Any') ]+[ (gu.pk,gu.dn) for gu in GridUser.objects.all() ]
    )
    node = forms.ChoiceField(
        label="Node",
        initial=0,
        choices=[ (0,'Any') ]+[ (n.pk,n.name) for n in Node.objects.all() ]
    )
    submithost = forms.ChoiceField(
        label="Submit host",
        initial=0,
        choices=[ (0,'Any') ]+[ (sh.pk,sh.name) for sh in SubmitHost.objects.all() ]
    )
    job_state = forms.ChoiceField(
        label="Finished status",
        initial=0,
        choices=[ (0,'Any') ]+[ (js.pk,js.name) for js in JobState.objects.filter(terminal=True) ]
    )
    exitstatus = forms.ChoiceField(
        label="Exit status",
        initial=0,
        choices=[ (0, 'Any'), (1,'=0'), (2,'>0') ]
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
        return render_to_response_with_config(
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
    comp_form.data['group'] = request.POST['group']
    comp_form.data['griduser'] = request.POST['griduser']
    comp_form.data['node'] = request.POST['node']
    comp_form.data['submithost'] = request.POST['submithost']
    comp_form.data['exitstatus'] = request.POST['exitstatus']
    comp_form.data['job_state'] = request.POST['job_state']
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

    if comp_form.data['group'] != '0':
        args['job_owner__group__pk'] = comp_form.data['group']

    if comp_form.data['griduser'] != '0':
        args['job_gridowner__pk'] = comp_form.data['griduser']

    if comp_form.data['node'] != '0':
        args['jobslots__node__pk'] = comp_form.data['node']

    if comp_form.data['submithost'] != '0':
        args['submithost__pk'] = comp_form.data['submithost']

    if comp_form.data['exitstatus'] == '1':
        args['exit_status__exact'] = 0
    elif comp_form.data['exitstatus'] == '2':
        args['exit_status__gt'] = 0

    if comp_form.data['job_state'] != '0':
        args['job_state__pk'] = comp_form.data['job_state']

    object_list = Job.objects.filter(**args)
        
    page = int(comp_form.data['page'])
    paginator = Paginator(object_list, 50)
    if page>paginator.num_pages:
        page=1
    jobs_page = paginator.page(page)

    return render_to_response_with_config(
        'trq/jobs_completed_listing.html',
        {'jobs_page':jobs_page, 'paginator':paginator,
        'comp_form':comp_form}
        )


def job_detail(request, servername=None, jobid=None):
    select_form = JobSelectForm()
    if not request.POST and jobid==None:
        return render_to_response_with_config(
            'trq/job_detail.html',
            {'select_form':select_form, 'unknownjob': False, 'job':None, 'accevents':[]}
        )
    try:
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
    except Job.DoesNotExist:
        return render_to_response_with_config(
            'trq/job_detail.html',
            {'select_form':select_form, 'unknownjob': True, 'job':None, 'accevents':[]}
        )
        

    if job.job_state.shortname=='R':
        UpdateRunningJob(job)

    accevents = AccountingEvent.objects.filter(job=job)
    return render_to_response_with_config(
        'trq/job_detail.html',
        {'select_form':select_form, 'unknownjob': False, 'job':job, 'accevents':accevents}
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
    return render_to_response_with_config(
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
    return render_to_response_with_config_with_config(
        'trq/jobs_suspicious.html', 
        {'suspicion_form':sf, 'suspicious_jobs':jobs}
        )

def report_form(request):
    """
    View form for reporting job data. This report is than returned as html or pdf.
    """
    pass

def report_output(request):
    """
    Render the actual report.
    """
    pass

def fairshare(request):
    """ View info about total used walltime and cputime.
    Compare it with walltime/cputime per entity (queue, unix group, unix user).
    """
    fs_form = FairshareForm()
    if not request.POST:
        return render_to_response_with_config(
            'trq/jobs_fairshare.html',
            {'fs_form':fs_form}
        )

    fs_form.data['timescale'] = request.POST['timescale']
    fs_form.data['minutes'] = request.POST['minutes']
    fs_form.data['entity'] = request.POST['entity']
    fs_form.is_bound = True

    minutes = int(request.POST['timescale'])
    if minutes == 0:
        minutes = int(request.POST['minutes'])
        
    endtime = datetime.datetime.now()
    starttime = datetime.datetime.fromtimestamp(int(endtime.strftime("%s"))-60*minutes)

    # Job.objects.filter(comp_time__range=("2010-01-01", "2010-01-02")).values('queue__name').annotate(Sum('walltime'))
    if request.POST['entity']=='0':  # Queue
        entity_name = 'queue__name'
        entity_color = 'queue__color'
    elif request.POST['entity']=='1':  # Group
        entity_name = 'job_owner__group__name'
        entity_color = 'job_owner__group__color'
    else: # request.POST['entity']=='2':  # User
        entity_name = 'job_owner__name'
        entity_color = 'job_owner__color'


    result = []
    total_sum = 0
    for j in Job.objects.filter(comp_time__range=(starttime, endtime)).values(entity_name, entity_color).annotate(Sum('walltime')):
        secs = int(j['walltime__sum'])
        tstr = "%d %d:%d:%d" % ((secs/86400), (secs/3600)%24, (secs/60)%60, secs%60)
        result.append({
            'entity_name':j[entity_name], 
            'walltime__sum':j['walltime__sum'], 
            'walltime__str':tstr,
            'entity_color':j[entity_color]
        })
        total_sum += int(j['walltime__sum'])

    total_str = "%d %d:%d:%d" % ((total_sum/86400), (total_sum/3600)%24, (total_sum/60)%60, total_sum%60)
    total = {'entity_name':'total', 'walltime__sum':total_sum, 'walltime__str':total_str}
    for row in result:
        if total_sum==0:
            row['percentage'] = 0
        else:
            row['percentage'] = 100*float(row['walltime__sum'])/total_sum

    return render_to_response_with_config(
        'trq/jobs_fairshare.html',
        {'fs_form':fs_form, 'result':result, 'total':total}
    )


# vi:ts=4:sw=4:expandtab
