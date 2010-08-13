from django.http import HttpResponse
from helpers import render_to_response_with_config,getJobState
from models import Node
from models import SubCluster
from models import NodeProperty
from models import NodeState
from models import Job
from models import User
from models import Queue
from models import TorqueServer
from models import AccountingEvent
from models import SubmitHost


from django import forms

def overview(request):
    info = []
    for c in (TorqueServer, Node, SubCluster, NodeProperty, User, Queue, Job, SubmitHost):
        item = {}
        item['name'] = c.get_overview_name()
        item['count'] = c.objects.all().count()
        item['url'] = c.get_overview_url()
        info.append(item)

    tsdata = {}
    for ts in TorqueServer.objects.all():
        tsdata[ts] = {'queues':[],'starttime':0,'endtime':0}
        qdb=Queue.objects.filter(server=ts)
        for q in qdb:
            numsq = Job.objects.filter(queue=q,job_state__shortname='Q').count()
            numsr = Job.objects.filter(queue=q,job_state__shortname='R').count()
            tsdata[ts]['queues'].append(
                {'queue':q,'Q':numsq,'R':numsr}
            )
        tsdata[ts]['starttime'] = Job.objects.filter(job_state=getJobState('C')).order_by('comp_time').filter(server=ts)[0].comp_time
        tsdata[ts]['endtime'] = Job.objects.filter(job_state=getJobState('C')).order_by('-comp_time').filter(server=ts)[0].comp_time

    print tsdata
    return render_to_response_with_config(
        'trq/overview.html', 
        { 'info': info,
          'tsdata' : tsdata
        }
    )

# vi:ts=4:sw=4:expandtab
