import re
from django.db import models
import datetime

# Create your models here.

class BatchServer(models.Model):
    name = models.CharField(verbose_name="Batch server full hostname", max_length=100)
    domainname = models.CharField(verbose_name="Domain name for the underlying worker nodes.", max_length=100)
    def __unicode__(self):
    	return self.name

class Subcluster(models.Model):
    name = models.CharField(verbose_name="Name of the subcluster", max_length=100)
    

class Node(models.Model):
    name = models.CharField(verbose_name="Full host name of the node", max_length=30)
    server = models.ForeignKey('BatchServer')
    subcluster = models.ForeignKey('Subcluster', null=True)
    lastupdate = models.DateTimeField(verbose_name='Last update date and time', default=datetime.datetime.now);
    state = models.CharField(verbose_name="Node state", max_length=100)

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
        return n[:n.rfind(self.number())]

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


class Job(models.Model):
    jobid = models.CharField(max_length=16, db_index=True, editable=False)
    server = models.ForeignKey('BatchServer', editable=False)


 
# vi:ts=4:sw=4:expandtab
