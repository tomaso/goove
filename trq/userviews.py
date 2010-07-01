from django.http import HttpResponse
from django.shortcuts import render_to_response
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
        label="user",
        initial=User.objects.all()[0],
        choices=[ (u.pk,u.name) for u in User.objects.all() ]
    )

def users_overview(request):
    users = User.objects.all()
    job_states = JobState.objects.all()
    return render_to_response(
        'trq/users_overview.html',
        {'users_list':users, 'job_states':job_states}
        )


def user_detail(request, username=None):
    user_form = UserSelectForm()
    summary = []

    if not request.POST and not username:
        detailuser = None
    elif username:
        detailuser = User.objects.get(name=username)
    elif request.POST.has_key('user'):
        detailuser = User.objects.get(pk=request.POST['user'])
    if detailuser:
        user_form.data['user'] = detailuser.pk
        user_form.is_bound = True
    if request.POST and request.POST.has_key('summary'):
        user_form.data['summary'] = request.POST['summary']
        user_form.is_bound = True
        if request.POST['summary']:
            summary.append(('Running jobs', 
                Job.objects.filter(job_state=getJobState('R'), job_owner=detailuser).count()
                ))
            dtoday = date.today()
            summary.append(('Jobs completed today',
                Job.objects.filter(
                    job_state=getJobState('C'), 
                    job_owner=detailuser,
                    comp_time__gte=dtoday.isoformat()
                    ).count()
                ))
            summary.append(('Jobs completed this week',
                Job.objects.filter(
                    job_state=getJobState('C'), 
                    job_owner=detailuser,
                    comp_time__gte=date.fromordinal(dtoday.toordinal()-dtoday.weekday())
                    ).count()
                ))
            msummary = Job.objects.filter(
                    job_state=getJobState('C'), 
                    job_owner=detailuser,
                    comp_time__gte=date(dtoday.year, dtoday.month, 1)
                    ).aggregate(Sum('cput'), Sum('walltime'), Avg('efficiency'), Count('pk'))

            summary.append(('Jobs completed this month',msummary['pk__count']))
            summary.append(('CPU time for this month',msummary['cput__sum']))
            summary.append(('Wall time for this month',msummary['walltime__sum']))
            summary.append(('Month average efficiency',msummary['efficiency__avg']))
        

    return render_to_response(
        'trq/user_detail.html',
        {'user':detailuser, 'user_form':user_form,
        'summary':summary}
        )

# vi:ts=4:sw=4:expandtab
