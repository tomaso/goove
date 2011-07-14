import os
import sys
sys.path.append("..")

os.environ['DJANGO_SETTINGS_MODULE']="goove.settings"
from goove.trq.models import JobSlot, Node, NodeProperty, NodeState, SubCluster, Job, RunningJob, BatchServer, GridUser, User, Group, JobState, Queue, AccountingEvent
from django.db.models import Avg, Max, Min, Count, Sum
from trq.helpers import secondsToHours
from django.db.models.sql.aggregates import Aggregate

class SumTimeDiff(Aggregate):
    sql_function = 'SUM'

    def __init__(self, lookup, **extra):
        self.lookup = lookup
        self.extra = extra
	# this is not perfect but I don't know how to do it right 
    	self.sql_template = '%(function)s(unix_timestamp(%(field)s)-unix_timestamp(' + extra['diff'] + '))'

    def _default_alias(self):
        return '%s__%s__%s' % (self.lookup, self.extra['diff'], self.__class__.__name__.lower())
    default_alias = property(_default_alias)

    def add_to_query(self, query, alias, col, source, is_summary):
        super(SumTimeDiff, self).__init__(col, source, is_summary, **self.extra)
        query.aggregate_select[alias] = self 

class AvgTimeDiff(Aggregate):
    sql_function = 'AVG'

    def __init__(self, lookup, **extra):
        self.lookup = lookup
        self.extra = extra
	# this is not perfect but I don't know how to do it right 
        if extra.has_key('mult'):
	    self.sql_template = '%(function)s(' + extra['mult'] + '*(unix_timestamp(%(field)s)-unix_timestamp(' + extra['diff'] + ')))'
        else:
            self.sql_template = '%(function)s(unix_timestamp(%(field)s)-unix_timestamp(' + extra['diff'] + '))'

    def _default_alias(self):
        return '%s__%s__%s' % (self.lookup, self.extra['diff'], self.__class__.__name__.lower())
    default_alias = property(_default_alias)

    def add_to_query(self, query, alias, col, source, is_summary):
        super(AvgTimeDiff, self).__init__(col, source, is_summary, **self.extra)
        query.aggregate_select[alias] = self 


def do_agg(jobs, header):
  print header
  print "-"*len(header)

  count_jobs = sum_cput = sum_walltime = sum_realwalltime = sum_realwalltime_slots = sum_waittime = 0
  for j in jobs:
    count_jobs += 1
    sum_cput += j.cput
    sum_walltime += j.walltime
    realwalltime = tosec(j.comp_time - j.start_time)
    sum_realwalltime += realwalltime
    sum_realwalltime_slots += (j.jobslots.count()*realwalltime)
    sum_waittime += tosec(j.start_time - j.qtime)

  avg_waittime = sum_waittime/count_jobs

  print "Job count: %d" % count_jobs
  print "Cputime: %s" % secondsToHours(sum_cput)
  print "Walltime: %s" % secondsToHours(sum_walltime)
  print "Real walltime: %s" % secondsToHours(sum_realwalltime)
  print "Real walltime*jobslots: %s" % secondsToHours(sum_realwalltime_slots)
  print "Avg wait time: %s" % secondsToHours(avg_waittime)
  print

def print_summary(start, end, snodes, neg_snodes, comment):
#  alljobs = Job.objects.filter(jobslots__node__in=snodes,comp_time__range=(start,end)).exclude(jobslots__node__in=neg_snodes)
  alljobs = Job.objects.filter(jobslots__node__in=snodes,comp_time__range=(start,end)).distinct()
  sq = Queue.objects.get(name='solid',server__name='torque.farm.particle.cz')
  isq = Queue.objects.get(name='isolid',server__name='torque.farm.particle.cz')
  nisolidjobs = alljobs.filter(queue=sq)
  isolidjobs = alljobs.filter(queue=isq)
  solidjobs = nisolidjobs  #|isolidjobs

  str = "Summary from %s to %s for %s:" % (start, end, comment)
  print
  print str
  print "=" * len(str)

  do_agg(alljobs, "All jobs")
  do_agg(solidjobs, "Solid jobs")
  return
  # this is damn slow :(
  # see http://groups.google.com/group/django-users/browse_thread/thread/87cc286019c7d57c
  agg = Job.objects.filter(pk__in=alljobs).aggregate(
    Sum("walltime"), Sum("cput"), 
    Count("pk"), SumTimeDiff("comp_time", diff="start_time"),
    AvgTimeDiff("start_time", diff="qtime")
    )
  solidagg = Job.objects.filter(pk__in=solidjobs).aggregate(
    Sum("walltime"), Sum("cput"), 
    Count("pk"), SumTimeDiff("comp_time", diff="start_time"),
    AvgTimeDiff("start_time", diff="qtime")
    )

  print "All jobs"
  print "--------"

  print "Job count: %d\nCputime: %s\nWalltime: %s\nReal walltime: %s\nAverage wait time: %s" % (agg['pk__count'], secondsToHours(agg['cput__sum']), secondsToHours(agg['walltime__sum']), secondsToHours(int(agg['comp_time__start_time__sumtimediff'])), secondsToHours(int(agg['start_time__qtime__avgtimediff'])) )
  print "Jobs real walltime * jobslots: %s" % secondsToHours(sum([j.jobslots.count()*tosec(j.comp_time-j.start_time) for j in alljobs]))
  print

  print "Solid jobs"
  print "--------"

  print "Job count: %d\nCputime: %s\nWalltime: %s\nReal walltime: %s\nAverage wait time: %s" % (solidagg['pk__count'], secondsToHours(solidagg['cput__sum']), secondsToHours(solidagg['walltime__sum']), secondsToHours(int(solidagg['comp_time__start_time__sumtimediff'])), secondsToHours(int(solidagg['start_time__qtime__avgtimediff'])) )
  print "Jobs real walltime * jobslots: %s" % secondsToHours(sum([j.jobslots.count()*tosec(j.comp_time-j.start_time) for j in solidjobs]))
  print
  

def tosec(diff):
  return diff.days*86400+diff.seconds

sp = NodeProperty.objects.get(name='solid')
isp = NodeProperty.objects.get(name='isolid')
snodes = Node.objects.filter(properties=sp)
#snodes = Node.objects.filter(name='golias160', server__name='torque.farm.particle.cz')
isnodes = Node.objects.filter(properties=isp)
both_snodes = snodes   #|isnodes
neg_both_snodes=Node.objects.exclude(properties=sp).exclude(properties=isp)
print_summary('2010-05-01', '2010-07-01', both_snodes, neg_both_snodes, 'all nodes with solid or isolid property')
print_summary('2010-07-01', '2010-09-01', both_snodes, neg_both_snodes, 'all nodes with solid or isolid property')

gsnodes = Node.objects.filter(properties__name='solid').filter(name__startswith='golias')
gisnodes = Node.objects.filter(properties__name='isolid').filter(name__startswith='golias')
both_gsnodes = gsnodes  #|gisnodes
neg_both_gsnodes = Node.objects.exclude(name__startswith='golias')
print_summary('2010-05-01', '2010-07-01', both_gsnodes, neg_both_gsnodes, 'only golias* nodes (no iberis)')
print_summary('2010-07-01', '2010-09-01', both_gsnodes, neg_both_gsnodes, 'only golias* nodes (no iberis)')


  
