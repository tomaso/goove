from django.http import HttpResponse
from helpers import render_to_response_with_config,getJobState
from models import Node
from models import SubCluster
from models import NodeProperty
from models import NodeState
from models import Job
from models import User
from models import Queue
from models import BatchServer
from models import AccountingEvent
from models import SubmitHost


from django import forms

def personal(request):

    return render_to_response_with_config(
        'trqacc/config_personal.html', 
        { 'session': request.session }
    )

# vi:ts=4:sw=4:expandtab
