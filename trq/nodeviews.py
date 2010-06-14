from django.http import HttpResponse
from django.core import serializers
from django.utils import simplejson
from django.shortcuts import render_to_response
from models import Node
from models import SubCluster
from models import NodeProperty
from models import NodeState
from models import Job
from helpers import BooleanListForm
from django import forms
from datetime import date

################
# Form classes #
################

class NodeSelectForm(forms.Form):
    node = forms.ChoiceField(
        label="Node",
        initial=Node.objects.all()[0],
        choices=[ (n.pk,n.name) for n in Node.objects.all() ]
    )

class NodeDetailForm(forms.Form):
    node = forms.ChoiceField(
        label="Node",
        initial=Node.objects.all()[0],
        choices=[ (n.pk,n.name) for n in Node.objects.all() ]
    )
    started_day_histogram = forms.BooleanField(
        label="Started 24h",
        initial=False,
        widget=forms.CheckboxInput(attrs={'title':'Display histogram of jobs started on this node in the last 24 hours'})
    )

def index(request):
    return render_to_response('trq/index.html', {})

def nodes(request):
	return render_to_response('trq/nodes.html', {})

def nodes_table(request, nodename=None):
    # Tabulka vsech uzlu s graficky naznacenim v jakem stavu jsou
    # z pohledu torque a jak moc jsou zaplnene joby.
    # Pri najeti mysi by se mel ukazat detail uzlu - nejlepe
    # v leve "formularove" oblasti - seznam bezicich jobu na uzlu (max s frontou).
#    nodes = Node.objects.all().order_by('subcluster__name', 'name')

    node_form = NodeSelectForm()
    if not request.POST and not nodename:
        detailnode = None
    elif nodename:
        detailnode = Node.objects.get(name=nodename)
    elif request.POST.has_key('node'):
        detailnode = Node.objects.get(pk=request.POST['node'])
    if detailnode:
        node_form.data['node'] = detailnode.pk
        node_form.is_bound = True

    cols = 6
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

    nodestates = NodeState.objects.all().order_by('name')
    return render_to_response(
        'trq/nodes_table.html', 
        {'sc_nodes':sc_nodes, 'nodestates':nodestates, 'colswidth':cols, 'detailnode':detailnode, 'detailform':node_form}
        )
    

def nodes_listing(request, filtertype=None, filtervalue=None):
    # Podrobny seznam uzlu s formularem na vyber podmnozin podle
    # torque vlastnosti.

    if filtertype=="subcluster":
        nodes = Node.objects.filter(subcluster__name=filtervalue).distinct()
    elif filtertype=="property":
        nodes = Node.objects.filter(properties__name=filtervalue).distinct()
    elif request.POST:
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

    if filtertype=="subcluster":
        properties_form.setData( dict(zip(properties, len(properties)*[True])) )
        states_form.setData( dict(zip(states, len(states)*[True])) )
        subcluster_form.setData( dict(zip(subclusters, len(subclusters)*[False])) )
        subcluster_form.data['subcluster_' + filtervalue] = True
        subcluster_form.is_bound = True
    elif filtertype=="property":
        subcluster_form.setData( dict(zip(subclusters, len(subclusters)*[True])) )
        states_form.setData( dict(zip(states, len(states)*[True])) )
        properties_form.setData( dict(zip(properties, len(properties)*[False])) )
        properties_form.data['properties_' + filtervalue] = True
        properties_form.is_bound = True
    elif request.POST:
        subcluster_form.setData(request.POST, useprefix=False)
        properties_form.setData(request.POST, useprefix=False)
        states_form.setData(request.POST, useprefix=False)
    else:
        subcluster_form.setData( dict(zip(subclusters, len(subclusters)*[True])) )
        properties_form.setData( dict(zip(properties, len(properties)*[True])) )
        states_form.setData( dict(zip(states, len(states)*[True])) )

    return render_to_response(
        'trq/nodes_listing.html', 
        {'nodes_list':nodes, 'subcluster_form':subcluster_form, 
        'properties_form':properties_form, 'states_form':states_form}
        )

def nodes_table_json_detail(request):
    pk = request.POST['pk']
    node = Node.objects.get(pk=pk)
    jobs = Job.objects.filter(exec_host=pk, job_state__shortname='R')
    jdata = { 'name':node.name, 'pk':node.pk, 'jobs':[] }
    for j in jobs:
        jdata['jobs'].append({"jobid":j.jobid, "joburl":j.get_absolute_url(), "queue":j.queue.name, "queueurl":j.queue.get_absolute_url() })
    data = simplejson.dumps(jdata)
    return HttpResponse(data, 'application/javascript')


def node_detail(request, nodename=None):
    # TODO:     
    # co dalsiho by u uzlu mohlo byt?
    # formular na vyber je tradicne vlevo a mohl by obsahovat zatrhavaci 
    # cudliky, kde se voli, jake detaily o uzlu clovek chce videt
    # bylo by fajn, mit moznost definovat obecne linky do jinych systemu
    # hezky by byl i histogram startovani a ukoncovani uloh
    # pripadne graf toho jakymi ulohami se uzel zaobiral poslednich X hodin

    node_form = NodeDetailForm()
    if not request.POST and not nodename:
        return render_to_response('trq/node_detail.html', 
            {'node':None, 'node_form':node_form})
        
    if nodename:
        n = Node.objects.get(name=nodename)
    if request.POST.has_key('node'):
        n = Node.objects.get(pk=request.POST['node'])
    node_form.data['node'] = n.pk
    node_form.is_bound = True

    running_jobs = Job.objects.filter(exec_host=n, job_state__shortname="R")
    for rj in running_jobs:
        UpdateRunningJob(rj)

    return render_to_response('trq/node_detail.html', 
        {'node':n, 'running_jobs': running_jobs, 'node_form':node_form
        }
    )

# vi:ts=4:sw=4:expandtab
