from django.db import models

# Create your models here.
class Node(models.Model):
    name = models.CharField(verbose_name="node name", max_length=30)
    np = models.IntegerField(verbose_name="number of job slots", null=True)
    properties = models.ManyToManyField('NodeProperty', null=True)
    state = models.ManyToManyField('NodeState', null=True)
    subcluster = models.ForeignKey('SubCluster', null=True)

    class Meta:
        ordering = ["name"]

    def get_nodeproperties(self):
    	return ",".join([ i.name for i in self.properties.all() ])
    get_nodeproperties.short_description = "node properties"

    def get_nodestates(self):
    	return ",".join([ i.name for i in self.state.all() ])
    get_nodestates.short_description = "node state"

    def running_jobs_count(self):
        # we relly on the fact that jobstates are filled from initial data
        js = JobState.objects.get(shortname="R")
        return len(self.job_set.filter(job_state=js))
    running_jobs_count.short_description = "number of running jobs"

    def running_jobs(self):
        # we relly on the fact that jobstates are filled from initial data
        js = JobState.objects.get(shortname="R")
        return self.job_set.filter(job_state=js)
    running_jobs_count.short_description = "running jobs"

    def get_absolute_url(self):
        return u"/trq/nodes/detail/%s/" % (self.name)

    def __unicode__(self):
    	return self.name

class NodeProperty(models.Model):
    name = models.CharField(verbose_name="property name", max_length=50)
    description = models.CharField(max_length=300)
    color = models.CharField(max_length=6, null=True, help_text="Color in HTML encoding (3 hex numbers)")

    def __unicode__(self):
    	return self.name

    class Meta:
        verbose_name_plural = "node properties"

class NodeState(models.Model):
    name = models.CharField(verbose_name="State name", max_length=30)	
    description = models.CharField(max_length=300)
    color = models.CharField(max_length=6, null=True, help_text="Color in HTML encoding (3 hex numbers)")

    def __unicode__(self):
    	return self.name

class SubCluster(models.Model):
    name = models.CharField(verbose_name="Subcluster name", max_length=30)	
    color = models.CharField(max_length=6, null=True, help_text="Color in HTML encoding (3 hex numbers)")
    def __unicode__(self):
    	return self.name

class Job(models.Model):
    jobid = models.IntegerField(db_index=True, editable=False)
    server = models.ForeignKey('TorqueServer', editable=False)
    job_owner = models.ForeignKey('User', null=True)
    cput = models.IntegerField('CPU time in seconds', null=True)
    walltime = models.IntegerField('Wall time in seconds', null=True)
    job_state = models.ForeignKey('JobState', null=True)
    # TODO: job can be moved from queue to queue during its lifetime
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
        return u"/trq/jobs/%s/%d/" % (self.server,self.jobid)

    def __unicode__(self):
    	return "%s.%s" % (self.jobid, self.server)

    def efficiency(self):
        return 100*self.cput/self.walltime

    class Meta:
        ordering = ['jobid']
        unique_together = (('jobid', 'server'),)
    
class TorqueServer(models.Model):
    name = models.CharField(verbose_name="torque server name", max_length=100)
    def __unicode__(self):
    	return self.name

class User(models.Model):
    name = models.CharField(verbose_name="user name", max_length=100)
    color = models.CharField(max_length=6, null=True, help_text="Color in HTML encoding (3 hex numbers)")
    def __unicode__(self):
    	return self.name

    def get_absolute_url(self):
        return u"/trq/users/%s/" % (self.name)

    def get_user_numbers(self):
        job_states = JobState.objects.all().order_by('name')
        unums = {}
        for js in job_states:
            unums[js] = Job.objects.filter(job_owner=self,job_state=js).count()
        return unums

    class Meta:
        ordering = ['name']

class JobState(models.Model):
    name = models.CharField(verbose_name="job state name", max_length=100)
    shortname = models.CharField(verbose_name="abbreviation", max_length=1)
    color = models.CharField(max_length=6, null=True, help_text="Color in HTML encoding (3 hex numbers)")
    def __unicode__(self):
    	return self.name

    class Meta:
        ordering = ['name']

class Queue(models.Model):
    name = models.CharField(verbose_name="queue name", max_length=100)
    color = models.CharField(max_length=6, null=True, help_text="Color in HTML encoding (3 hex numbers)")
    def __unicode__(self):
    	return self.name

    def get_absolute_url(self):
        return u"/trq/queues/%s/" % (self.name)

    def get_queue_numbers(self):
        job_states = JobState.objects.all().order_by('name')
        qnums = {}
        for js in job_states:
            qnums[js] = Job.objects.filter(queue=self,job_state=js).count()
        return qnums

EVENT_CHOICES = (
    ('Q', 'Queued'),
    ('S', 'Started'),
    ('E', 'Exited'),
    ('D', 'Deleted'),
)

class AccountingEvent(models.Model):
    """
    Event parsed from accounting records. More than one event of the same type of the same job
    means some kind of problems.
    """
    timestamp = models.DateTimeField(verbose_name='time stamp')
    type = models.CharField(max_length=1, choices=EVENT_CHOICES)
    job = models.ForeignKey('Job')

 
# vi:ts=4:sw=4:expandtab
