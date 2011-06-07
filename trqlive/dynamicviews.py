from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.utils import simplejson

from models import Node,Subcluster

def nodes_overview(request, subcluster_name=None):
    l = []
    if request.GET.has_key('subcluster_name') and not subcluster_name:
        subcluster_name = request.GET['subcluster_name']
    if subcluster_name:
        qs = Node.objects.filter(subcluster__name=subcluster_name)
    else:
        qs = Node.objects.all()

    for n in qs:
        l.append({'name': n.name, 'state': n.state.replace(',',' ')})
    return HttpResponse(simplejson.dumps(l))


def subclusters_list(request):
    """ Return just the list of subcluster names """
    l = []
    for i in Subcluster.objects.values_list('name'):
        l.append({'name': i[0]})
    return HttpResponse(simplejson.dumps(l))


# vi:ts=4:sw=4:expandtab
