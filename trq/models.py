from django.db import models

# Create your models here.
class Node(models.Model):
    ordering = ['name']
    name = models.CharField(verbose_name="Node name", max_length=30)
    np = models.IntegerField(verbose_name="Number of job slots")
    properties = models.ManyToManyField('NodeProperty')
    state = models.ManyToManyField('NodeState')
    subcluster = models.ForeignKey('SubCluster')

    def get_nodeproperties(self):
    	return ",".join([ i.name for i in self.properties.all() ])
    get_nodeproperties.short_description = "Node properties"

    def get_nodestates(self):
    	return ",".join([ i.name for i in self.state.all() ])
    get_nodestates.short_description = "Node state"

    def __unicode__(self):
    	return self.name

class NodeProperty(models.Model):
    name = models.CharField(verbose_name="Property name", max_length=50)
    description = models.CharField(verbose_name="Description", max_length=300)

    def __unicode__(self):
    	return self.name

class NodeState(models.Model):
    name = models.CharField(verbose_name="State name", max_length=30)	
    description = models.CharField(verbose_name="Description", max_length=300)

    def __unicode__(self):
    	return self.name

class SubCluster(models.Model):
    name = models.CharField(verbose_name="Subcluster name", max_length=30)	
    
    def __unicode__(self):
    	return self.name

class Job(models.Model):
    jobid = models.IntegerField()
    server = models.ForeignKey('TorqueServer')
    job_owner = models.ForeignKey('User')
    cput = models.IntegerField('CPU time in seconds')
    walltime = models.IntegerField('Wall time in seconds')
    job_state = models.ForeignKey('JobState')
    queue = models.ForeignKey('Queue')
    ctime = models.DateTimeField('ctime')
    exec_host = models.ForeignKey('Node')
    mtime = models.DateTimeField('mtime')
    qtime = models.DateTimeField('qtime')
    etime = models.DateTimeField('etime')
    start_time = models.DateTimeField('start_time')
    
class TorqueServer(models.Model):
    name = models.CharField(verbose_name="Torque server name", max_length=100)

class User(models.Model):
    name = models.CharField(varbose_name="User name", max_length=100)

class JobState(models.Model):
    name = models.CharField(varbose_name="Job state name", max_length=100)
    shortname = models.CharField(varbose_name="Abbreviation", max_length=1)

class Queue(models.Model):
    name = models.CharField(varbose_name="Queue name", max_length=100)

# vi:ts=4:sw=4:expandtab
