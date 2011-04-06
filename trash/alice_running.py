#!/bin/env python

# Distribution of alice jobs in time and on nodes

import os
import sys
sys.path.append("..")

os.environ['DJANGO_SETTINGS_MODULE']="goove.settings"
from goove.trq.models import JobSlot, Node, NodeProperty, NodeState, SubCluster, Job, RunningJob, TorqueServer, GridUser, User, Group, JobState, Queue, AccountingEvent
from django.db.models import Avg, Max, Min, Count, Sum
from trq.helpers import secondsToHours
from django.db.models.sql.aggregates import Aggregate
import datetime, time


def get_count(q, n, t):
	""" return number of running jobs in queue q, on node n, at time t
	"""
  	c = Job.objects.filter(start_time__lte=t, comp_time__gte=t, queue=q, jobslots__node=n).aggregate(Count('jobslots'))['jobslots__count']
	return c
	

start=int(datetime.datetime(2010, 11, 17, 0, 0).strftime("%s"))
end=int(datetime.datetime(2010, 11, 23, 23, 59).strftime("%s"))
q = Queue.objects.get(name='gridalice', server__name='torque.farm.particle.cz')

result = {}
nodelist = map(lambda x: x[0], Node.objects.filter(server__name='torque.farm.particle.cz').values_list('name'))

for node in nodelist:
	result[node] = {}

for secs in range(start,end,10*60):
	struct = time.localtime(secs)
	t = "%d-%d-%d %d:%d" % (struct.tm_year, struct.tm_mon, struct.tm_mday, struct.tm_hour, struct.tm_min)
	jobs = Job.objects.filter(start_time__lte=t, comp_time__gte=t, queue=q)
	print "%s, jobs: %d" % (t, jobs.count())
	
	for node in nodelist:
		result[node][t] = 0

	for j in jobs:
		# we rely on the fact that alice jobs are one-slot only
		nn = j.jobslots.all()[0].node.name
		result[nn][t] += 1


#	print "Node: %s, Time: %s, Count: %d" % (node.name, t, c)
