from django.http import HttpResponse
from helpers import render_to_response_with_config
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

    tsqueues = {}
    for ts in TorqueServer.objects.all():
        tsqueues[ts]=[]
        qdb=Queue.objects.filter(server=ts)
        for q in qdb:
            numsq = Job.objects.filter(queue=q,job_state__shortname='Q').count()
            numsr = Job.objects.filter(queue=q,job_state__shortname='R').count()
            tsqueues[ts].append(
                {'queue':q,'Q':numsq,'R':numsr}
            )

    return render_to_response_with_config(
        'trq/overview.html', 
        { 'info': info,
          'tsqueues' : tsqueues,
          'starttime' : AccountingEvent.objects.all().order_by('timestamp')[0].timestamp,
          'endtime' : AccountingEvent.objects.all().order_by('-timestamp')[0].timestamp
        }
        )

# vi:ts=4:sw=4:expandtab
