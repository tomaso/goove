#!/bin/env python

# Atlas accounting info for the last month

import os
import sys
sys.path.append(os.path.abspath(os.getcwd()+'/..'))

os.environ['DJANGO_SETTINGS_MODULE']="goove.settings"
from goove.trqacc.models import JobSlot, Node, NodeProperty, NodeState, SubCluster, Job, BatchServer, GridUser, User, Group, JobState, Queue, AccountingEvent
from django.db.models import Avg, Max, Min, Count, Sum
from goove.trqacc.helpers import secondsToHours
from django.db.models.sql.aggregates import Aggregate
import datetime, time


def print_jobs(jobs):
	res = jobs.aggregate(Sum('walltime'), Sum('cput'), Count('pk'))
	cnt = res['pk__count']
	walltime = secondsToHours(res['walltime__sum']).split('h')[0]
	cputime = secondsToHours(res['cput__sum']).split('h')[0]
	print "Group: %s, Count: %d, Walltime(h): %s, Cputime(h): %s " % (gr.name, cnt, walltime, cputime)

start = '2011-06-01 00:00'
end = '2011-07-01 00:00'

ts = BatchServer.objects.get(name='torque.farm.particle.cz')

for n in ['atlasprd', 'atlasplt', 'atlas', 'atlassgm']:
	gr = Group.objects.get(name=n, server=ts)
	jobs=Job.objects.filter(start_time__gte=start, comp_time__lte=end, job_owner__group=gr)
	print_jobs(jobs)


gr = Group.objects.get(name='users', server=ts)
jobs=Job.objects.filter(start_time__gte=start, comp_time__lte=end, job_owner__group=gr, queue__name__contains='atlas')
print_jobs(jobs)
