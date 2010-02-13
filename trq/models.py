from django.db import models

# Create your models here.
class Node(models.Model):
    name = models.CharField(verbose_name="Node name", max_length=30)
    np = models.IntegerField(verbose_name="Number of job slots")
    properties = models.ManyToManyField('NodeProperty')
    state = models.ManyToManyField('NodeState')
    subcluster = models.ForeignKey('SubCluster')

    class Meta:
        ordering = ["name"]

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
    job_owner = models.ForeignKey('User', null=True)
    cput = models.IntegerField('CPU time in seconds', null=True)
    walltime = models.IntegerField('Wall time in seconds', null=True)
    job_state = models.ForeignKey('JobState', null=True)
    queue = models.ForeignKey('Queue', null=True)
    ctime = models.DateTimeField('ctime', null=True)
    exec_host = models.ForeignKey('Node', null=True)
    mtime = models.DateTimeField('mtime', null=True)
    qtime = models.DateTimeField('qtime', null=True)
    etime = models.DateTimeField('etime', null=True)
    start_time = models.DateTimeField('start_time', null=True)
    
class TorqueServer(models.Model):
    name = models.CharField(verbose_name="Torque server name", max_length=100)
    def __unicode__(self):
    	return self.name

class User(models.Model):
    name = models.CharField(verbose_name="User name", max_length=100)
    def __unicode__(self):
    	return self.name

class JobState(models.Model):
    name = models.CharField(verbose_name="Job state name", max_length=100)
    shortname = models.CharField(verbose_name="Abbreviation", max_length=1)
    def __unicode__(self):
    	return self.name

class Queue(models.Model):
    name = models.CharField(verbose_name="Queue name", max_length=100)
    def __unicode__(self):
    	return self.name

# vi:ts=4:sw=4:expandtab
