#!/bin/env python


import os
import sys
sys.path.append("..")

os.environ['DJANGO_SETTINGS_MODULE']="goove.settings"
from goove.trq.models import JobSlot, Node, NodeProperty, NodeState, SubCluster, Job, RunningJob, TorqueServer, GridUser, User, Group, JobState, Queue, AccountingEvent
from django.db.models import Avg, Max, Min, Count, Sum
from trq.helpers import secondsToHours
from django.db.models.sql.aggregates import Aggregate
import datetime, time

SERVER='torque.farm.particle.cz'


def period_overview(start, end, users):
	#head="%16s %16s %16s %16s %16s %16s" % ("name", "count", "walltime", "cput", "jobslots", "slots*walltime")
	head="%s;%s;%s;%s" % ("name", "count", "walltime", "cput")
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
#		for j in jobs:
#			c = j.jobslots.count()
#			sw += c*j.walltime
#			s += c
		tot_c += res['pk__count']
		tot_s += s
		tot_sw += sw
		#print "%16s %16s %16s %16s %16s %16s" % (u.name, res['pk__count'], res['walltime__sum'], res['cput__sum'], s, sw)
		print "%s;%s;%s;%s" % (u.name, res['pk__count'], res['walltime__sum'], res['cput__sum'])

	print "-" * len(head)
	#print "%16s %16s %16s %16s %16s %16s" % ("", tot_c, "", "", tot_s, tot_sw)
	print "%s;%s;%s;%s" % ("", tot_c, "", "")
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


def period_overview_pergroup(start, end, groups):
	head="%s;%s;%s;%s;%s;%s" % ("name", "count", "walltime", "cput", "jobslots", "slots*walltime")
	print head
	print "-" * len(head)
	tot_c=0
	tot_sw=0
	tot_s=0
	for g in groups:
		jobs1=Job.objects.filter(start_time__gte=start, start_time__lte=end, job_owner__group=g).exclude(comp_time=None)
		jobs2=Job.objects.filter(comp_time__gte=start, comp_time__lte=end, job_owner__group=g)
		jobs = jobs1 | jobs2
		res = jobs.aggregate(Sum('walltime'), Sum('cput'), Count('pk'))
		s = 0
		sw = 0
#		for j in jobs:
#			c = j.jobslots.count()
#			sw += c*j.walltime
#			s += c
		tot_c += res['pk__count']
		tot_s += s
		tot_sw += sw
		#print "%16s %16s %16s %16s %16s %16s" % (g.name, res['pk__count'], res['walltime__sum'], res['cput__sum'], s, sw)
		print "%s;%s;%s;%s" % (g.name, res['pk__count'], res['walltime__sum'], res['cput__sum'])

	print "-" * len(head)
	#print "%16s %16s %16s %16s %16s %16s" % ("", tot_c, "", "", tot_s, tot_sw)
	print "%s;%s;%s;%s" % ("", tot_c, "", "")
	print "-" * len(head)

def period_overview_perqueue(start, end, queues):
	head="%s;%s;%s;%s;%s;%s" % ("name", "count", "walltime", "cput", "jobslots", "slots*walltime")
	print head
	print "-" * len(head)
	tot_c=0
	tot_sw=0
	tot_s=0
	for q in queues:
		jobs1=Job.objects.filter(start_time__gte=start, start_time__lte=end, queue=q).exclude(comp_time=None)
		jobs2=Job.objects.filter(comp_time__gte=start, comp_time__lte=end, queue=q)
		jobs = jobs1 | jobs2
		res = jobs.aggregate(Sum('walltime'), Sum('cput'), Count('pk'))
		s = 0
		sw = 0
#		for j in jobs:
#			c = j.jobslots.count()
#			sw += c*j.walltime
#			s += c
		tot_c += res['pk__count']
		tot_s += s
		tot_sw += sw
		#print "%16s %16s %16s %16s %16s %16s" % (g.name, res['pk__count'], res['walltime__sum'], res['cput__sum'], s, sw)
		print "%s;%s;%s;%s" % (q.name, res['pk__count'], res['walltime__sum'], res['cput__sum'])

	print "-" * len(head)
	#print "%16s %16s %16s %16s %16s %16s" % ("", tot_c, "", "", tot_s, tot_sw)
	print "%s;%s;%s;%s" % ("", tot_c, "", "")
	print "-" * len(head)

def period_overview_pergriduser(start, end, gridusers):
	head="%s;%s;%s;%s;%s;%s" % ("name", "count", "walltime", "cput", "jobslots", "slots*walltime")
	print head
	print "-" * len(head)
	tot_c=0
	tot_sw=0
	tot_s=0
	for q in gridusers:
		jobs1=Job.objects.filter(start_time__gte=start, start_time__lte=end, job_gridowner=q).exclude(comp_time=None)
		jobs2=Job.objects.filter(comp_time__gte=start, comp_time__lte=end, job_gridowner=q)
		jobs = jobs1 | jobs2
		res = jobs.aggregate(Sum('walltime'), Sum('cput'), Count('pk'))
		s = 0
		sw = 0
		tot_c += res['pk__count']
		tot_s += s
		tot_sw += sw
		print "%s;%s;%s;%s" % (q.dn, res['pk__count'], res['walltime__sum'], res['cput__sum'])

	print "-" * len(head)
	print "%s;%s;%s;%s" % ("", tot_c, "", "")
	print "-" * len(head)


def month_overview_pergroup(start, end, m, ts):
	groups = Group.objects.filter(server=ts)
	res=Job.objects.filter(start_time__gte=start, comp_time__lte=end,server=ts).values('job_owner__group__name').annotate(Sum('walltime'))
	print "%d;" % (m+1),
	for g in groups:
		found = False
		for r in res:
			if r['job_owner__group__name']==g.name:
				print "%d;" % (r['walltime__sum']),
				found = True
		if not found:
			print "0;",

	print
#	res = jobs.aggregate(Sum('walltime'))
#	s = 0
#	sw = 0
#	for j in jobs:
#		c = j.jobslots.count()
#		sw += c*j.walltime
#		s += c
#	print "%s;%s;%s;%s;%s;%s" % (m+1, res['pk__count'], res['walltime__sum'], res['cput__sum'], s, sw)

if __name__=="__main__":
	start = '2010-01-01 00:00'
	end = '2011-04-01 00:00'
	ts = TorqueServer.objects.get(name='torque.farm.particle.cz')
	users = User.objects.filter(server__name='torque.farm.particle.cz')
	gridusers = GridUser.objects.all()
	groups = Group.objects.filter(server__name='torque.farm.particle.cz')
	queues = Queue.objects.filter(server__name='torque.farm.particle.cz')
#	period_overview_perqueue(start, end, queues)
#	period_overview_pergroup(start, end, groups)
#	period_overview(start, end, users)
#	period_overview_pergriduser(start, end, gridusers)

	months = ['2010-01-01 00:00', '2010-02-01 00:00','2010-03-01 00:00', '2010-04-01 00:00','2010-05-01 00:00', '2010-06-01 00:00','2010-07-01 00:00', '2010-08-01 00:00','2010-09-01 00:00', '2010-10-01 00:00', '2010-11-01 00:00', '2010-12-01 00:00','2011-01-01 00:00']
	months = ['2011-01-01 00:00', '2011-02-01 00:00','2011-03-01 00:00', '2011-04-01 00:00']
#	print "%16s %16s %16s %16s %16s %16s" % ("month", "count", "walltime", "cput", "jobslots", "slots*walltime")
	print ";",
	for g in groups:
		print "%s;" % g.name,
	print
	for m in range(0,3):
		start = months[m]
		end = months[m+1]
		month_overview_pergroup(start, end, m, ts)
