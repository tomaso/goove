from django.http import HttpResponse
from django.shortcuts import render_to_response
from models import Node
from models import SubCluster
from models import NodeProperty
from models import NodeState
from models import Job
from models import JobState
from models import User

def users_overview(request):
    users = User.objects.all()
    job_states = JobState.objects.all()
    return render_to_response(
        'trq/users_overview.html',
        {'users_list':users, 'job_states':job_states}
        )


def user_detail(request, username):
    user = User.objects.get(name=username)
    jobs = Job.objects.filter(job_owner=user)
    return render_to_response(
        'trq/user_detail.html',
        {'user':user, 'jobs':jobs}
        )

# vi:ts=4:sw=4:expandtab
