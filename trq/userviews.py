from django.http import HttpResponse
from helpers import render_to_response_with_config
from django import forms
from models import Node
from models import SubCluster
from models import NodeProperty
from models import NodeState
from models import Job
from models import JobState
from models import User
from models import Group
from models import GridUser
from helpers import getJobState
from datetime import date
from django.db.models import Sum,Avg,Count

from common_forms import CommonUserForm

class UserSelectForm(CommonUserForm):
    user = forms.ChoiceField(
        label="unix user",
        initial=User.objects.all()[0],
        choices=[ (u['pk'],"%s@%s" % (u['name'],u['server__name'])) for u in User.objects.values('pk','name','server__name') ]
    )

class GridUserSelectForm(CommonUserForm):
    user = forms.ChoiceField(
        label="grid user",
        initial=GridUser.objects.all()[0],
        choices=[ (gu.pk,gu.dn) for gu in GridUser.objects.all() ]
    )

class GroupSelectForm(CommonUserForm):
    user = forms.ChoiceField(
        label="unix group",
        initial=Group.objects.all()[0],
        choices=[ (g.pk,g.name) for g in Group.objects.all() ]
    )

def users_overview(request):
    users = User.objects.all()
    job_states = JobState.objects.all()
    return render_to_response_with_config(
        'trq/users_overview.html',
        {'users_list':users, 'job_states':job_states}
        )

def create_summary(addfilter):
    """ Create summary list. The additional filter is used
    to get data only for given entity (user, group, grid user).
    Currently summary contains:
    - Running jobs for the given entity
    - Jobs completed since last midnight to this moment
    - Week statistics (since last monday):
      - Number of completed jobs
      - CPU time in total for this week
      - Total wall time
      - Average efficiency
    - Month statistics (since the 1st day of current month):
      - Number of completed jobs
      - CPU time in total for this month
      - Total wall time
      - Average efficiency
    """
    summary = []
    summary.append(('Running jobs', 
        Job.objects.filter(
            job_state=getJobState('R'), 
            **addfilter
            ).count()
        ))
    dtoday = date.today()
    summary.append(('Jobs completed today',
        Job.objects.filter(
            job_state=getJobState('C'), 
            comp_time__gte=dtoday.isoformat(),
            **addfilter
            ).count()
        ))
    wsummary = Job.objects.filter(
            job_state=getJobState('C'), 
            comp_time__gte=date.fromordinal(dtoday.toordinal()-dtoday.weekday()),
            **addfilter
            ).aggregate(Sum('cput'), Sum('walltime'), Avg('efficiency'), Count('pk'))
    summary.append(('Jobs completed this week',wsummary['pk__count']))
    summary.append(('CPU time for this week',wsummary['cput__sum']))
    summary.append(('Wall time for this week',wsummary['walltime__sum']))
    summary.append(('Weekly average efficiency',wsummary['efficiency__avg']))

    msummary = Job.objects.filter(
            job_state=getJobState('C'), 
            comp_time__gte=date(dtoday.year, dtoday.month, 1),
            **addfilter
            ).aggregate(Sum('cput'), Sum('walltime'), Avg('efficiency'), Count('pk'))
    summary.append(('Jobs completed this month',msummary['pk__count']))
    summary.append(('CPU time for this month',msummary['cput__sum']))
    summary.append(('Wall time for this month',msummary['walltime__sum']))
    summary.append(('Monthly average efficiency',msummary['efficiency__avg']))
    return summary
    

def user_detail(request, servername=None, username=None):
    user_form = UserSelectForm()
    summary = []

    if not request.POST and not username:
        detailuser = None
    elif request.POST.has_key('user'):
        detailuser = User.objects.get(pk=request.POST['user'])
    elif username:
        detailuser = User.objects.get(name=username, server__name=servername)

    if detailuser:
        user_form.data['user'] = detailuser.pk
        user_form.is_bound = True
    if request.POST and request.POST.has_key('summary'):
        user_form.data['summary'] = request.POST['summary']
        user_form.is_bound = True
        if request.POST['summary']:
            summary = create_summary({'job_owner': detailuser})
        
    return render_to_response_with_config(
        'trq/user_detail.html',
        {'user':detailuser, 'user_form':user_form,
        'summary':summary}
        )

def griduser_detail(request, gridusername=None):
    griduser_form = GridUserSelectForm()
    summary = []

    if not request.POST and not gridusername:
        detailuser = None
    elif gridusername:
        detailuser = GridUser.objects.get(dn=gridusername)
    elif request.POST.has_key('user'):
        detailuser = GridUser.objects.get(pk=request.POST['user'])
    if detailuser:
        griduser_form.data['user'] = detailuser.pk
        griduser_form.is_bound = True
    if request.POST and request.POST.has_key('summary'):
        griduser_form.data['summary'] = request.POST['summary']
        griduser_form.is_bound = True
        if request.POST['summary']:
            summary = create_summary({'job_gridowner': detailuser})

    return render_to_response_with_config(
        'trq/user_detail.html',
        {'user':detailuser, 'user_form':griduser_form,
        'summary':summary}
        )

def group_detail(request, groupname=None):
    group_form = GroupSelectForm()
    summary = []

    if not request.POST and not groupname:
        detailgroup = None
    elif groupname:
        detailgroup = Group.objects.get(name=groupname)
    elif request.POST.has_key('user'):
        detailgroup = Group.objects.get(pk=request.POST['user'])

    if detailgroup:
        group_form.data['user'] = detailgroup.pk
        group_form.is_bound = True
    if request.POST and request.POST.has_key('summary'):
        group_form.data['summary'] = request.POST['summary']
        group_form.is_bound = True
        if request.POST['summary']:
            summary = create_summary({'job_owner__group': detailgroup})
        

    return render_to_response_with_config(
        'trq/user_detail.html',
        {'user':detailgroup, 'user_form':group_form,
        'summary':summary}
        )
# vi:ts=4:sw=4:expandtab
