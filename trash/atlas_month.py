#!/bin/env python

# Atlas accounting info for the last month

import os
import sys
sys.path.append("..")

os.environ['DJANGO_SETTINGS_MODULE']="goove.settings"
from goove.trq.models import JobSlot, Node, NodeProperty, NodeState, SubCluster, Job, RunningJob, TorqueServer, GridUser, User, Group, JobState, Queue, AccountingEvent
from django.db.models import Avg, Max, Min, Count, Sum
from trq.helpers import secondsToHours
from django.db.models.sql.aggregates import Aggregate
import datetime, time


def print_jobs(jobs):
	res = jobs.aggregate(Sum('walltime'), Sum('cput'), Count('pk'))
	cnt = res['pk__count']
	walltime = secondsToHours(res['walltime__sum']).split('h')[0]
	cputime = secondsToHours(res['cput__sum']).split('h')[0]
	print "Group: %s, Count: %d, Walltime(h): %s, Cputime(h): %s " % (gr.name, cnt, walltime, cputime)

start = '2011-02-01 00:00'
end = '2011-03-01 00:00'

ts = TorqueServer.objects.get(name='torque.farm.particle.cz')

n = 'atlas'
for n in ['atlas', 'atlasplt', 'atlasprd', 'atlassgm']:
	gr = Group.objects.get(name=n, server=ts)
	jobs=Job.objects.filter(start_time__gte=start, comp_time__lte=end, job_owner__group=gr)
	print_jobs(jobs)


gr = Group.objects.get(name='users', server=ts)
jobs=Job.objects.filter(start_time__gte=start, comp_time__lte=end, job_owner__group=gr, queue__name__contains='atlas')
print_jobs(jobs)
