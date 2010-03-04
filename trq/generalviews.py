from django.http import HttpResponse
from django.shortcuts import render_to_response
from models import Node
from models import SubCluster
from models import NodeProperty
from models import NodeState
from models import Job
from django import forms

def overview(request):
    return render_to_response(
        'trq/overview.html', 
        {}
        )

# vi:ts=4:sw=4:expandtab
