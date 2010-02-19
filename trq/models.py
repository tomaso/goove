from django.db import models

# Create your models here.
class Node(models.Model):
    name = models.CharField(verbose_name="node name", max_length=30)
    np = models.IntegerField(verbose_name="number of job slots")
    properties = models.ManyToManyField('NodeProperty')
    state = models.ManyToManyField('NodeState')
    subcluster = models.ForeignKey('SubCluster')

    class Meta:
        ordering = ["name"]

    def get_nodeproperties(self):
    	return ",".join([ i.name for i in self.properties.all() ])
    get_nodeproperties.short_description = "node properties"

    def get_nodestates(self):
    	return ",".join([ i.name for i in self.state.all() ])
    get_nodestates.short_description = "node state"

    def get_absolute_url(self):
        return u"/trq/nodes/%s/" % (self.name)

    def __unicode__(self):
    	return self.name

class NodeProperty(models.Model):
    name = models.CharField(verbose_name="property name", max_length=50)
    description = models.CharField(max_length=300)

    def __unicode__(self):
    	return self.name

    class Meta:
        verbose_name_plural = "node properties"

class NodeState(models.Model):
    name = models.CharField(verbose_name="State name", max_length=30)	
    description = models.CharField(max_length=300)

    def __unicode__(self):
    	return self.name

class SubCluster(models.Model):
    name = models.CharField(verbose_name="Subcluster name", max_length=30)	
    def __unicode__(self):
    	return self.name

class Job(models.Model):
    jobid = models.IntegerField(db_index=True, editable=False)
    server = models.ForeignKey('TorqueServer', editable=False)
    job_owner = models.ForeignKey('User', null=True)
    cput = models.IntegerField('CPU time in seconds', null=True)
    walltime = models.IntegerField('Wall time in seconds', null=True)
    job_state = models.ForeignKey('JobState', null=True)
    queue = models.ForeignKey('Queue', null=True)
    ctime = models.DateTimeField(verbose_name='Creation time', null=True,
        help_text="The time that the job was created.")
    # TODO: will not work for multinode and multislot jobs - we should redesign
    exec_host = models.ForeignKey('Node', null=True)
    mtime = models.DateTimeField(verbose_name='modified time', null=True,
        help_text="The time that the job was last modified, changed state or changed locations.")
    qtime = models.DateTimeField(verbose_name='queued time', null=True,
        help_text="The time that the job entered the current queue.")
    etime = models.DateTimeField(verbose_name='Eligible time', null=True,
        help_text="The time that the job became eligible to run, i.e. in a queued state while residing in an execution queue.")
    start_time = models.DateTimeField(verbose_name='Start time', null=True)
    comp_time = models.DateTimeField(verbose_name='Completion time', null=True)

    def get_absolute_url(self):
        return u"/trq/jobs/%s/%d/" % (server,jobid)

    def __unicode__(self):
    	return "%s.%s" % (self.jobid, self.server)

    class Meta:
        ordering = ['jobid']
        unique_together = (('jobid', 'server'),)
    
class TorqueServer(models.Model):
    name = models.CharField(verbose_name="torque server name", max_length=100)
    def __unicode__(self):
    	return self.name

class User(models.Model):
    name = models.CharField(verbose_name="user name", max_length=100)
    def __unicode__(self):
    	return self.name

    class Meta:
        ordering = ['name']

class JobState(models.Model):
    name = models.CharField(verbose_name="job state name", max_length=100)
    shortname = models.CharField(verbose_name="abbreviation", max_length=1)
    def __unicode__(self):
    	return self.name

class Queue(models.Model):
    name = models.CharField(verbose_name="queue name", max_length=100)
    def __unicode__(self):
    	return self.name

# vi:ts=4:sw=4:expandtab
