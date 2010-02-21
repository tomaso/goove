from django.http import HttpResponse
from django.shortcuts import render_to_response
from models import Node
from models import SubCluster
from models import NodeProperty
from models import NodeState
from models import Job
from models import Queue

def queues_overview(request):
    queues = Queue.objects.all()
    return render_to_response(
        'trq/queues_overview.html',
        {'queues_list':queues}
        )


def queue_detail(request, queuename):
    queue = Queue.objects.get(name=queuename)
    running_jobs = Job.objects.filter(queue=queue)
    return render_to_response(
        'trq/queue_detail.html',
        {'queue':queue, 'running_jobs':running_jobs}
        )

# vi:ts=4:sw=4:expandtab
