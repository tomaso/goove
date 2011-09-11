from django.http import HttpResponse,HttpResponseNotFound
from django.shortcuts import render_to_response
from django.utils import simplejson

from models import Node,SubCluster,BatchServer,Queue,Job

import live_updaters

testvar = 0
pbs_data_nodes = {}

def nodes_overview(request, batchserver_name=None,subcluster_name=None):
    l = []
    if request.GET.has_key('subcluster_name') and not subcluster_name:
        subcluster_name = request.GET['subcluster_name']
    if request.GET.has_key('batchserver_name') and not batchserver_name:
        batchserver_name = request.GET['batchserver_name']

    if not subcluster_name or not batchserver_name:
        return HttpResponseNotFound()

    updated_nodes = live_updaters.update_all_nodes(batchserver_name)

    ns = Node.objects.filter(server__name=batchserver_name, subcluster__name=subcluster_name)

    for n in ns:
        th = "<table style='border: 1px'><tr>"
        c = 0
        for jobid in updated_nodes[batchserver_name]['nodes'][n]['jobs']:
            th += "<td><a href='#'>%s</a>&nbsp;</td>" % jobid
            if c%2 == 1:
                th += "</tr><tr>"
            c += 1
        th += "</tr></table>"

        l.append({
            'name': n.name, 
            'shortname': n.shortname(), 
            'state': " ".join([un.name for un in updated_nodes[batchserver_name]['nodes'][n]['state']]),
            'ttiphtml': th,
#            'jobs': [ j.job.jobid for j in n.jobslot_set.all() ]
            })
    return HttpResponse(simplejson.dumps(l))


def nodes_list(request, batchserver_name=None):
    """ Return the list of nodes with properties """
    l = []
    if request.GET.has_key('batchserver_name') and not batchserver_name:
        batchserver_name = request.GET['batchserver_name']

    if not batchserver_name:
        return HttpResponseNotFound()
    
    updated_nodes = live_updaters.update_all_nodes(batchserver_name)

    ns = Node.objects.filter(server__name=batchserver_name)

    for n in ns:
        if not n.isactive:
            continue
        l.append({
            'name': n.name,
            'state': ",".join([un.name for un in updated_nodes[batchserver_name]['nodes'][n]['state']]),
            'properties': ",".join([un.name for un in updated_nodes[batchserver_name]['nodes'][n]['properties']]),
            'subcluster': n.subcluster.name,
            'cputmult': n.cputmult,
            'wallmult': n.wallmult
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
    global testvar

    l = []
    if request.GET.has_key('batchserver_name') and not batchserver_name:
        batchserver_name = request.GET['batchserver_name']
    if batchserver_name:
        live_updaters.update_all_queues(batchserver_name)
        ql = Queue.objects.filter(server__name=batchserver_name, obsolete=False)
    else:
        ql = Queue.objects.filter(obsolete=False)

    testvar += 1
    print testvar


    for i in ql:
        l.append({
            'name': i.name,
            'Q': i.state_count_queued,
            'W': i.state_count_waiting,
            'R': i.state_count_running,
            'started': i.started,
            'enabled': i.enabled,
            'queue_type': i.queue_type,
            'max_running': i.max_running,
            'total_jobs': i.total_jobs
            })
    return HttpResponse(simplejson.dumps(l))


def jobs_list(request, batchserver_name=None):
    if request.GET.has_key('batchserver_name') and not batchserver_name:
        batchserver_name = request.GET['batchserver_name']
    if not batchserver_name:
        return HttpResponseNotFound()

    updated_jobs = live_updaters.update_all_jobs(batchserver_name)
    
    l = []
    for jobid,data in updated_jobs[batchserver_name]['jobs'].items():
        l.append({
            'jobid': jobid,
            'job_name': data['Job_Name'],
            'queue': data['queue'].name,
            'job_state': data['job_state'].name
            })
    return HttpResponse(simplejson.dumps(l))


# vi:ts=4:sw=4:expandtab
