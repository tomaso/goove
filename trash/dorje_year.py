#!/bin/env python


import os
import sys
sys.path.append("..")

os.environ['DJANGO_SETTINGS_MODULE']="goove.settings"
from goove.trq.models import JobSlot, Node, NodeProperty, NodeState, SubCluster, Job, RunningJob, BatchServer, GridUser, User, Group, JobState, Queue, AccountingEvent
from django.db.models import Avg, Max, Min, Count, Sum
from trq.helpers import secondsToHours
from django.db.models.sql.aggregates import Aggregate
import datetime, time



def period_overview(start, end, users):
	head="%16s %16s %16s %16s %16s %16s" % ("name", "count", "walltime", "cput", "jobslots", "slots*walltime")
	print head
	print "-" * len(head)
	tot_c=0
	tot_sw=0
	tot_s=0
	for u in users:
		jobs1=Job.objects.filter(start_time__gte=start, start_time__lte=end, job_owner=u).exclude(comp_time=None)
		jobs2=Job.objects.filter(comp_time__gte=start, comp_time__lte=end, job_owner=u)
		jobs = jobs1 | jobs2
#		jl1 = list(jobs1)
#		jl2 = list(jobs2)
#		jl = list(jl1)
#		jl.extend(jl2)
#		jls = list(set(jl))
#		print jobs1.count(), jobs2.count(), jobs.count()
#		print len(jl1), len(jl2), len(jls)
		res = jobs.aggregate(Sum('walltime'), Sum('cput'), Count('pk'))
		s = 0
		sw = 0
		for j in jobs:
			c = j.jobslots.count()
			sw += c*j.walltime
			s += c
		tot_c += res['pk__count']
		tot_s += s
		tot_sw += sw
		print "%16s %16s %16s %16s %16s %16s" % (u.name, res['pk__count'], res['walltime__sum'], res['cput__sum'], s, sw)

	print "-" * len(head)
	print "%16s %16s %16s %16s %16s %16s" % ("", tot_c, "", "", tot_s, tot_sw)
	print "-" * len(head)

#	jobs=Job.objects.filter(start_time__gte=start, comp_time__lte=end,server=ts)
#	res = jobs.aggregate(Sum('walltime'), Sum('cput'), Count('pk'))
#	s = 0
#	sw = 0
#	for j in jobs:
#		c = j.jobslots.count()
#		sw += c*j.walltime
#		s += c
#	print "%16s %16s %16s %16s %16s %16s" % ('total', res['pk__count'], res['walltime__sum'], res['cput__sum'], s, sw)


def month_overview(start, end, m, ts):
	jobs=Job.objects.filter(start_time__gte=start, comp_time__lte=end,server=ts)
	res = jobs.aggregate(Sum('walltime'), Sum('cput'), Count('pk'))
	s = 0
	sw = 0
	for j in jobs:
		c = j.jobslots.count()
		sw += c*j.walltime
		s += c
	print "%16s %16s %16s %16s %16s %16s" % (m+1, res['pk__count'], res['walltime__sum'], res['cput__sum'], s, sw)



if __name__=="__main__":
	start = '2010-01-01 00:00'
	end = '2011-01-01 00:00'
	ts = BatchServer.objects.get(name='service0.dorje.fzu.cz')
	users = User.objects.filter(server__name='service0.dorje.fzu.cz')
	period_overview(start, end, users)

#	months = ['2010-01-01 00:00', '2010-02-01 00:00','2010-03-01 00:00', '2010-04-01 00:00','2010-05-01 00:00', '2010-06-01 00:00','2010-07-01 00:00', '2010-08-01 00:00','2010-09-01 00:00', '2010-10-01 00:00', '2010-11-01 00:00', '2010-12-01 00:00','2011-01-01 00:00']
#	print "%16s %16s %16s %16s %16s %16s" % ("month", "count", "walltime", "cput", "jobslots", "slots*walltime")
#	for m in range(0,12):
#		start = months[m]
#		end = months[m+1]
#		month_overview(start, end, m, ts)
