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

class UserSelectForm(forms.Form):
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

    if not request.POST and not username:
        detailuser = None
    elif username:
        detailuser = User.objects.get(name=username)
    elif request.POST.has_key('user'):
        detailuser = User.objects.get(pk=request.POST['user'])
    if detailuser:
        user_form.data['user'] = detailuser.pk
        user_form.is_bound = True

    return render_to_response(
        'trq/user_detail.html',
        {'user':detailuser, 'user_form':user_form}
        )

# vi:ts=4:sw=4:expandtab
