from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import render_to_response
from models import JobState
from models import Job
from models import User
from models import TorqueServer
from helpers import BooleanListForm
from django import forms

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

# vi:ts=4:sw=4:expandtab