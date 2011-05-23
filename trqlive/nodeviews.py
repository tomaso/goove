from django.http import HttpResponse
from django.core import serializers
from django.utils import simplejson
from django.shortcuts import render_to_response

from models import Node


def node_detail(request, nodename=None):
    if nodename:
        n = Node.objects.get(name=nodename)
    if request.POST.has_key('node'):
        n = Node.objects.get(pk=request.POST['node'])
    return render_to_response('trqlive/node_detail.html', {'node':n})

def node_overview(request):
    nodes = Node.objects.all()
    return render_to_response('trqlive/node_overview.html', {'nodes':nodes})

# vi:ts=4:sw=4:expandtab
