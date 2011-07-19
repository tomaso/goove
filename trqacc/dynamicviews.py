from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.utils import simplejson

from models import Node,SubCluster,BatchServer,Queue,Job

import live_updaters

def nodes_overview(request, subcluster_name=None):
    l = []
    if request.GET.has_key('subcluster_name') and not subcluster_name:
        subcluster_name = request.GET['subcluster_name']
    if subcluster_name:
        ns = Node.objects.filter(subcluster__name=subcluster_name)
    else:
        ns = Node.objects.all()

    for n in ns:
        th = "<table style='border: 1px'><tr>"
        c = 0
        for x in n.jobslot_set.all():
            jobid = x.job.jobid
            th += "<td><a href='#'>%s</a>&nbsp;</td>" % jobid
            if c%2 == 1:
                th += "</tr><tr>"
            c += 1
        th += "</tr></table>"

        l.append({
            'name': n.name, 
            'shortname': n.shortname(), 
            'state': n.state.replace(',',' '),
            'ttiphtml': th,
#            'jobs': [ j.job.jobid for j in n.jobslot_set.all() ]
            })
    return HttpResponse(simplejson.dumps(l))


def nodes_list(request, batchserver_name=None):
    """ Return the list of nodes with properties """
    l = []
    if request.GET.has_key('batchserver_name') and not batchserver_name:
        batchserver_name = request.GET['batchserver_name']
    if batchserver_name:
        live_updaters.update_nodes_all(batchserver_name)
        ns = Node.objects.filter(server__name=batchserver_name)
    else:
        ns = Node.objects.all()

    for n in ns:
        l.append({
            'name': n.name,
            'state': n.state,
            'properties': n.properties,
            'subcluster': n.subcluster.name
            })
    return HttpResponse(simplejson.dumps(l))


def subclusters_list(request, batchserver_name=None):
    """ Return just the list of subcluster names (optionally withing given batch server) """
    l = []
    if request.GET.has_key('batchserver_name') and not batchserver_name:
        batchserver_name = request.GET['batchserver_name']
    if batchserver_name:
        scl = SubCluster.objects.filter(server__name=batchserver_name)
    else:
        scl = SubCluster.objects.all()

    for i in scl.values_list('name'):
        l.append({'name': i[0]})
    return HttpResponse(simplejson.dumps(l))


def batchservers_list(request):
    """ Return the list of batchserver hostnames """
    bs = []
    for i in BatchServer.objects.values_list('name'):
        bs.append({'name': i[0]})
    return HttpResponse(simplejson.dumps(bs))


def queues_list(request, batchserver_name=None):
    l = []
    if request.GET.has_key('batchserver_name') and not batchserver_name:
        batchserver_name = request.GET['batchserver_name']
    if batchserver_name:
        live_updaters.update_queues_all(batchserver_name)
        ql = Queue.objects.filter(server__name=batchserver_name)
    else:
        ql = Queue.objects.all()


    for i in ql:
        l.append({
            'name': i.name,
            'state_count': "Q: %d, W: %d, R: %d" % (i.state_count_queued, i.state_count_waiting, i.state_count_running),
            'started': i.started,
            'enabled': i.enabled,
            'queue_type': i.queue_type,
            'max_running': i.max_running,
            'total_jobs': i.total_jobs
            })
    return HttpResponse(simplejson.dumps(l))


def jobs_list(request, batchserver_name=None):
    l = []
    if request.GET.has_key('batchserver_name') and not batchserver_name:
        batchserver_name = request.GET['batchserver_name']
    if batchserver_name:
        jl = Job.objects.filter(server__name=batchserver_name)
    else:
        jl = Job.objects.all()
    
    for i in jl:
        l.append({
            'jobid': i.jobid,
            'job_name': i.job_name,
            'queue': i.queue.name,
            'job_state': i.job_state.name
            })
    return HttpResponse(simplejson.dumps(l))


# vi:ts=4:sw=4:expandtab
