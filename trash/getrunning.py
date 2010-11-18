import os
import sys
sys.path.append("..")

os.environ['DJANGO_SETTINGS_MODULE']="goove.settings"
from goove.trq.models import JobSlot, Node, NodeProperty, NodeState, SubCluster, Job, RunningJob, TorqueServer, GridUser, User, Group, JobState, Queue, AccountingEvent
from django.db.models import Avg, Max, Min, Count, Sum
from trq.helpers import secondsToHours
from django.db.models.sql.aggregates import Aggregate
import datetime, time

start=int(datetime.datetime(2010, 5, 1, 0, 0).strftime("%s"))
end=int(datetime.datetime(2010, 6, 30, 23, 59).strftime("%s"))

q=Queue.objects.get(name='solid', server__name='torque.farm.particle.cz')
res = []
for secs in range(start,end,60):
  struct = time.localtime(secs)
  timestr = "%d-%d-%d %d:%d" % (struct.tm_year, struct.tm_mon, struct.tm_mday, struct.tm_hour, struct.tm_min)
  c = Job.objects.filter(start_time__lte=timestr, comp_time__gte=timestr, queue=q).aggregate(Count('jobslots'))['jobslots__count']
  res.append(c)
