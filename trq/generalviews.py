from django.http import HttpResponse
from django.shortcuts import render_to_response
from models import Node
from models import SubCluster
from models import NodeProperty
from models import NodeState
from models import Job
from models import User
from models import Queue
from models import TorqueServer
from models import AccountingEvent


from django import forms

def overview(request):
    info = []
    for c in (Node, SubCluster, NodeProperty, User, Queue, Job):
        item = {}
        item['name'] = c.get_overview_name()
        item['count'] = c.objects.all().count()
        item['url'] = c.get_overview_url()
        info.append(item)

    queues=[]
    
    queues.append(
        {'name':'asdf','Q':'123','R':'234','C_in_last_24h':'233','C_in_last_week':'2345'}
    )
    

    return render_to_response(
        'trq/overview.html', 
        { 'info': info,
          'queues' : queues,
          'starttime' : AccountingEvent.objects.all().order_by('timestamp')[0].timestamp,
          'endtime' : AccountingEvent.objects.all().order_by('-timestamp')[0].timestamp
        }
        )

# vi:ts=4:sw=4:expandtab
