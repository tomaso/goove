from django.http import HttpResponse
from django.shortcuts import render_to_response
from models import Node
from models import SubCluster
from models import NodeProperty
from models import NodeState
from models import Job
from helpers import BooleanListForm
from django import forms

def index(request):
    return render_to_response('trq/index.html', {})

def nodes(request):
	return render_to_response('trq/nodes.html', {})

def nodes_overview(request):
#    nodes = Node.objects.all().order_by('subcluster__name', 'name')
    cols = 10
    sc = SubCluster.objects.all()
    sc_nodes = []
    for s in sc:
        sn = { 'subcluster': s, 'rows' : [] }
        nodes = Node.objects.filter(subcluster=s)
        i = 0
        while i<len(nodes):
            sn['rows'].append(nodes[i:i+cols])
            i = i + cols
        sn['rows'][-1].extend([None]*(i-len(nodes)))
        sc_nodes.append(sn)

    print sc_nodes

    nodestates = NodeState.objects.all().order_by('name')
    return render_to_response(
        'trq/nodes_overview.html', 
        {'sc_nodes':sc_nodes, 'nodestates':nodestates, 'colswidth':cols}
        )
    

def nodes_table_list(request):
    if request.POST:
        sc_list = []
        prop_list = []
        state_list = []
        for key,val in request.POST.items():
            prefix, attr = key.split("_", 1)
            if prefix == "subcluster":
                if 'on' in val:
                    sc_list.append(attr)
            elif prefix == "properties":
                if 'on' in val:
                    prop_list.append(attr)
            elif prefix == "nodestates":
                if 'on' in val:
                    state_list.append(attr)

        nodes = Node.objects.filter(
            subcluster__name__in=sc_list, 
            properties__name__in=prop_list,
            state__name__in=state_list
            ).distinct()
    else:
        nodes = Node.objects.all()


    subclusters = [x.name for x in SubCluster.objects.all()]
    properties = [x.name for x in NodeProperty.objects.all()]
    states = [x.name for x in NodeState.objects.all()]
    
    subcluster_form = BooleanListForm('subcluster_')
    subcluster_form.setFields(subclusters)

    properties_form = BooleanListForm('properties_')
    properties_form.setFields(properties)

    states_form = BooleanListForm('nodestates_')
    states_form.setFields(states)

    if request.POST:
        subcluster_form.setData(request.POST, useprefix=False)
        properties_form.setData(request.POST, useprefix=False)
        states_form.setData(request.POST, useprefix=False)
    else:
        subcluster_form.setData( dict(zip(subclusters, len(subclusters)*[True])) )
        properties_form.setData( dict(zip(properties, len(properties)*[True])) )
        states_form.setData( dict(zip(states, len(states)*[True])) )

    return render_to_response(
        'trq/nodes_table_list.html', 
        {'nodes_list':nodes, 'subcluster_form':subcluster_form, 
        'properties_form':properties_form, 'states_form':states_form}
        )


def node_detail(request, nodename):
    n = Node.objects.get(name=nodename)
    running_jobs = Job.objects.filter(exec_host=n, job_state__shortname="R")
#    completed_jobs = Job.objects.filter(exec_host=n, job_state__shortname="C")
    completed_jobs = []
    
    return render_to_response('trq/node_detail.html', 
        {'node':n, 'running_jobs': running_jobs, 'completed_jobs': completed_jobs})

# vi:ts=4:sw=4:expandtab
