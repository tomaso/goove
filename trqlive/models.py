import re
from django.db import models
import datetime

# Create your models here.

class Node(models.Model):
    name = models.CharField(verbose_name="Full host name of the node", max_length=30)
    server = models.ForeignKey('BatchServer')
    subcluster = models.ForeignKey('Subcluster', null=True)
    lastupdate = models.DateTimeField(verbose_name='Last update date and time', default=datetime.datetime.now);
    state = models.CharField(verbose_name="Node state", max_length=100)
    properties = models.CharField(verbose_name="Properties list", max_length=256)

    class Meta:
        ordering = ["name"]

    def __unicode__(self):
    	return self.name

    def shortname(self):
        return self.name.split('.')[0]

    def number(self):
        return re.search('[0-9]+$', self.shortname()).group()

    def name_without_number(self):
        n = self.name
     

class JobSlot(models.Model):
    slot = models.IntegerField(verbose_name="Job slot number")
    node = models.ForeignKey('Node')

    # Current job attached to this jobslot
    job = models.ForeignKey('Job', null=True)

    class Meta:
        ordering = ['node','slot']
        unique_together = (('node', 'slot'),)

    def __unicode__(self):
    	return "%s/%d" % (self.node.name,self.slot)


class BatchServer(models.Model):
    name = models.CharField(verbose_name="Batch server full hostname", max_length=100)
    domainname = models.CharField(verbose_name="Domain name for the underlying worker nodes.", max_length=100)
    def __unicode__(self):
    	return self.name


class Subcluster(models.Model):
    name = models.CharField(verbose_name="Name of the subcluster", max_length=100)
    # TODO: foreign key BatchServer
    server = models.ForeignKey('BatchServer')


class Job(models.Model):
    jobid = models.CharField(max_length=16, db_index=True, editable=False)
    server = models.ForeignKey('BatchServer', editable=False)
    job_name = models.CharField(max_length=256)
    queue = models.ForeignKey('Queue', null=True)
    job_state = models.ForeignKey('JobState', null=True)


class JobState(models.Model):
    name = models.CharField(verbose_name="job state name", max_length=100)
    shortname = models.CharField(verbose_name="abbreviation", max_length=1)


class Queue(models.Model):
    name = models.CharField(max_length=64, editable=False)
    server = models.ForeignKey('BatchServer', editable=False)
    state_count = models.CharField(max_length=256)
    # TODO: boolean
    started = models.CharField(max_length=256)
    # TODO: boolean
    enabled = models.CharField(max_length=256)
    queue_type = models.CharField(max_length=256)
    # TODO: int
    mtime = models.CharField(max_length=256)
    # TODO: int
    max_running = models.CharField(max_length=256)
    # TODO: int
    total_jobs = models.CharField(max_length=256)
 
# vi:ts=4:sw=4:expandtab
