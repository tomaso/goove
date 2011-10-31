
from django.db import models
import datetime

# Create your models here.

class Node(models.Model):
    name = models.CharField(verbose_name="node name", max_length=30)
    np = models.IntegerField(verbose_name="number of job slots", null=True)
    properties = models.ManyToManyField('NodeProperty', null=True)
    state = models.ManyToManyField('NodeState', null=True)
    subcluster = models.ForeignKey('SubCluster', null=True)
    server = models.ForeignKey('BatchServer')
    isactive = models.BooleanField(help_text="Is this node still used?")
    cputmult = models.FloatField(default=1.0)
    wallmult = models.FloatField(default=1.0)

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

    def percentage_load(self):
        return (self.running_jobs_count()*100)/self.np
    percentage_load.short_description = "Number of job slots occupied in percents"

    def get_absolute_url(self):
        return u"/trqacc/nodes/detail/%s/" % (self.name)

    def __unicode__(self):
    	return self.name

    def get_node_links(self):
        gc = GlobalConfiguration.objects.get(pk=1)
        return [ (nl.name, nl.url.replace("<NODE>", self.name)) for nl in gc.nodelink_set.all() ]

    def shortname(self):
        return self.name.split('.')[0]

    def number(self):
        return re.search('[0-9]+$', self.shortname()).group()

    def name_without_number(self):
        n = self.name
        return n[:n.rfind(self.number())]

    @staticmethod
    def get_overview_name():
        return u'worker node'

    @staticmethod
    def get_overview_url():
        return u'/trqacc/nodes/listing/'


class NodeProperty(models.Model):
    name = models.CharField(verbose_name="property name", max_length=50)
    description = models.CharField(max_length=300)
    color = models.CharField(max_length=6, null=True, help_text="Color in HTML encoding (3 hex numbers)")

    def get_nodeslist_url(self):
        return u"/trqacc/nodes/listing/property/%s/" % (self.name)

    def __unicode__(self):
    	return self.name

    class Meta:
        verbose_name_plural = "node properties"

    @staticmethod
    def get_overview_name():
        return u'node propertie'

    @staticmethod
    def get_overview_url():
        return u'/trqacc/nodes/table/'


class JobSlot(models.Model):
    slot = models.IntegerField(verbose_name="Job slot number")
    node = models.ForeignKey('Node')
    livejob = models.ForeignKey('LiveJob', help_text='Current job occupying this jobslot', null=True)

    class Meta:
        ordering = ['node','slot']
        unique_together = (('node', 'slot'),)

    def __unicode__(self):
    	return "%s/%d" % (self.node.name,self.slot)


class NodeState(models.Model):
    name = models.CharField(verbose_name="State name", max_length=30)	
    description = models.CharField(max_length=300)
    color = models.CharField(max_length=6, null=True, help_text="Color in HTML encoding (3 hex numbers)")
    iconpath = models.CharField(max_length=512, null=True)

    def __unicode__(self):
    	return self.name


class SubCluster(models.Model):
    name = models.CharField(verbose_name="Subcluster name", max_length=30,
            help_text="Name ot this subcluster.")
    node_regexp = models.CharField(verbose_name="Regular expression for nodes", max_length=30, null=True,
            help_text="The updater daemon will automatically attach new node to this subcluster if the regexp matches.")
    color = models.CharField(max_length=6, null=True, help_text="Color in HTML encoding (3 hex numbers)")
    server = models.ForeignKey('BatchServer')
    def __unicode__(self):
    	return self.name

    def get_nodeslist_url(self):
        return u"/trqacc/nodes/listing/subcluster/%s/" % (self.name)

    @staticmethod
    def get_overview_name():
        return u'subcluster'

    @staticmethod
    def get_overview_url():
        return u'/trqacc/nodes/table/'


class SubmitHost(models.Model):
    name = models.CharField(verbose_name="Where the job was submitted from", max_length=64)
    color = models.CharField(max_length=6, null=True, help_text="Color in HTML encoding (3 hex numbers)")
    
    @staticmethod
    def get_overview_name():
        return u'submithost'

    @staticmethod
    def get_overview_url():
        return u'/trqacc/'


class LiveJob(models.Model):
    # Job info obtained from running batch system - not accounting logs
    jobid = models.CharField(max_length=16, db_index=True, editable=False)
    server = models.ForeignKey('BatchServer', editable=False)
    job_name = models.CharField(max_length=256)
    job_owner = models.ForeignKey('User', null=True)
    queue = models.ForeignKey('Queue', null=True)
    job_state = models.ForeignKey('JobState', null=True)


class Job(models.Model):
    jobid = models.CharField(max_length=16, db_index=True, editable=False)
    server = models.ForeignKey('BatchServer', editable=False)
    job_owner = models.ForeignKey('User', null=True)
    job_gridowner = models.ForeignKey('GridUser', null=True)
    cput = models.IntegerField('CPU time in seconds', null=True)
    walltime = models.IntegerField('Wall time in seconds', null=True)
    efficiency = models.IntegerField('Efficiency in percent', null=True)
    job_state = models.ForeignKey('JobState', null=True)
    # TODO: job can be moved from queue to queue during its lifetime
    queue = models.ForeignKey('Queue', null=True)
    ctime = models.DateTimeField(verbose_name='Creation time', null=True,
        help_text="The time that the job was created.")
    # TODO: will not work for multinode and multislot jobs - we should redesign
    jobslots = models.ManyToManyField('JobSlot', null=True)
    mtime = models.DateTimeField(verbose_name='modified time', null=True,
        help_text="The time that the job was last modified, changed state or changed locations.")
    qtime = models.DateTimeField(verbose_name='queued time', null=True,
        help_text="The time that the job entered the current queue.")
    etime = models.DateTimeField(verbose_name='Eligible time', null=True,
        help_text="The time that the job became eligible to run, i.e. in a queued state while residing in an execution queue.")
    start_time = models.DateTimeField(verbose_name='Start time', null=True, db_index=True)
    comp_time = models.DateTimeField(verbose_name='Completion time', null=True, db_index=True)
    submithost = models.ForeignKey('SubmitHost', null=True)
    exit_status = models.IntegerField('Exit status', null=True)

    def get_absolute_url(self):
        return u"/trqacc/jobs/detail/%s/%s/" % (self.server,self.jobid)

    def __unicode__(self):
    	return "%s.%s" % (self.jobid, self.server)

    def running_days(self):
        diff = datetime.datetime.now() - self.start_time
        return diff.days

    def running_seconds(self):
        diff = datetime.datetime.now() - self.start_time
        return diff.days*24*60*60+diff.seconds

    def exec_hosts(self):
        """ Return string with hosts used by this job """
        return ",".join([ js.node.name for js in self.jobslots.all() ])
       

    class Meta:
        ordering = ['jobid']
        unique_together = (('jobid', 'server'),)

    @staticmethod
    def get_overview_name():
        return u'job'

    @staticmethod
    def get_overview_url():
        return u'/trqacc/jobs/detail/'

BATCHSYSTEM_CHOICES=(
        (1,'Torque'),
        (2,'PBSPro'),
)
    
class BatchServer(models.Model):
    name = models.CharField(help_text="Batch server full hostname", max_length=100)
    domainname = models.CharField(help_text="Domain name for the underlying worker nodes.", max_length=256)
    isactive = models.BooleanField(help_text="Is this server still used?")
    systemtype = models.IntegerField(help_text="Type of the batch system running", choices=BATCHSYSTEM_CHOICES)
    accountingdir = models.CharField(help_text="Path to the directory where accounting logs are stored", max_length=256)
    lastacc_update = models.DateTimeField(help_text="Time of the last update of the accounting data for this batch server", null=True)
    queues_lastupdate = models.DateTimeField(help_text='Last update of the queues information', default=datetime.datetime.now, null=True);
    nodes_lastupdate = models.DateTimeField(help_text='Last update of the nodes information', default=datetime.datetime.now, null=True);

    def __unicode__(self):
    	return self.name

    @staticmethod
    def get_overview_name():
        return u'batch server'

    @staticmethod
    def get_overview_url():
        return u'/trqacc/'


class User(models.Model):
    name = models.CharField(verbose_name="user name", max_length=100)
    color = models.CharField(max_length=6, null=True, help_text="Color in HTML encoding (3 hex numbers)")
    group = models.ForeignKey('Group', null=True)
    server = models.ForeignKey('BatchServer')
    def __unicode__(self):
    	return "%s@%s" % (self.name,self.server.name)

    def get_absolute_url(self):
        return u"/trqacc/users/user_detail/%s/%s/" % (self.server.name, self.name)

    def get_user_numbers(self):
        job_states = JobState.objects.all().order_by('name')
        unums = {}
        for js in job_states:
            unums[js] = Job.objects.filter(job_owner=self,job_state=js).count()
        return unums

    class Meta:
        ordering = ['name']

    @staticmethod
    def get_overview_name():
        return u'user'

    @staticmethod
    def get_overview_url():
        return u'/trqacc/users/'


class Group(models.Model):
    name = models.CharField(verbose_name="group name", max_length=100)
    server = models.ForeignKey('BatchServer')
    color = models.CharField(max_length=6, null=True, help_text="Color in HTML encoding (3 hex numbers)")
    def __unicode__(self):
    	return self.name

    def get_absolute_url(self):
        return u"/trqacc/users/group_detail/%s/" % (self.name)

    def get_group_numbers(self):
        job_states = JobState.objects.all().order_by('name')
        unums = {}
        for js in job_states:
            unums[js] = Job.objects.filter(job_owner_group=self,job_state=js).count()
        return unums

    class Meta:
        ordering = ['name']

    @staticmethod
    def get_overview_name():
        return u'group'

    @staticmethod
    def get_overview_url():
        return u'/trqacc/group/'


class GridUser(models.Model):
    dn = models.CharField(verbose_name="Distinguished name", max_length=512)
    color = models.CharField(max_length=6, null=True, help_text="Color in HTML encoding (3 hex numbers)")
    def __unicode__(self):
    	return self.dn

    def get_absolute_url(self):
        return u"/trqacc/users/griduser_detail/%s/" % (self.dn)

    def get_user_numbers(self):
        job_states = JobState.objects.all().order_by('name')
        unums = {}
        for js in job_states:
            unums[js] = Job.objects.filter(job_gridowner=self,job_state=js).count()
        return unums

    class Meta:
        ordering = ['dn']

    @staticmethod
    def get_overview_name():
        return u'grid user'

    @staticmethod
    def get_overview_url():
        return u'/trqacc/gridusers/'
    

class JobState(models.Model):
    name = models.CharField(verbose_name="job state name", max_length=100)
    shortname = models.CharField(verbose_name="abbreviation", max_length=1)
    color = models.CharField(max_length=6, null=True, help_text="Color in HTML encoding (3 hex numbers)")
    terminal = models.BooleanField(help_text="Whether this state is terminal.")
    def __unicode__(self):
    	return self.name

    class Meta:
        ordering = ['name']


class Queue(models.Model):
    name = models.CharField(verbose_name="queue name", max_length=100)
    color = models.CharField(max_length=6, null=True, help_text="Color in HTML encoding (3 hex numbers)")
    server = models.ForeignKey('BatchServer', editable=False)
    started = models.BooleanField()
    enabled = models.BooleanField()
    queue_type = models.CharField(max_length=256)
    # TODO: not sure what mtime is in pbs.py output
    mtime = models.IntegerField(null=True)
    max_running = models.IntegerField(null=True)
    total_jobs = models.IntegerField(null=True)
    state_count_transit = models.IntegerField(default=0)
    state_count_queued = models.IntegerField(default=0)
    state_count_held = models.IntegerField(default=0)
    state_count_waiting = models.IntegerField(default=0)
    state_count_running = models.IntegerField(default=0)
    state_count_exiting = models.IntegerField(default=0)

    obsolete = models.BooleanField(default=False)


    def __unicode__(self):
    	return self.name

    def get_absolute_url(self):
        return u"/trqacc/queues/detail/%s/%s" % (self.server.name, self.name)

    @staticmethod
    def get_overview_name():
        return u'queue'

    @staticmethod
    def get_overview_url():
        return u'/trqacc/queues/table/'


EVENT_CHOICES = (
    ('Q', 'Queued'),
    ('S', 'Started'),
    ('R', 'Rerun'),
    ('C', 'Checkpoint'),
    ('T', 'Restart'),
    ('E', 'Exited'),
    ('D', 'Deleted'),
    ('A', 'Aborted'),
)

class AccountingEvent(models.Model):
    """
    Event parsed from accounting records. More than one event of the same type of the same job
    means some kind of problems.
    """
    timestamp = models.DateTimeField(verbose_name='time stamp')
    type = models.CharField(max_length=1, choices=EVENT_CHOICES)
    job = models.ForeignKey('Job', null=True)
    full_jobname = models.CharField(max_length=100)
    attributes = models.ManyToManyField('EventAttribute', through='EventAttributeValue')


class EventAttributeValue(models.Model):
    ae = models.ForeignKey('AccountingEvent')
    ea = models.ForeignKey('EventAttribute')
    value = models.CharField(verbose_name="Value of the attribute", max_length=100)


class EventAttribute(models.Model):
    name = models.CharField(verbose_name="Attribute name", max_length=1024)


class NodeLink(models.Model):
    """
    Link to another system with information about a node.
    The <NODE> string in url is replaced with the actual name.
    """
    name = models.CharField(max_length=40)
    url = models.CharField(max_length=512)
    config = models.ForeignKey("GlobalConfiguration")


GRAPH_CHOICES = (
    ('Matplotlib', 'Matplotlib'),
    ('Google', 'Google visualization'),
)

class GlobalConfiguration(models.Model):
    """
    Object with global configuration.
    """
    livestatus = models.BooleanField(help_text="Should the node status be periodically updated and overview shown.")
    max_lastupdate = models.IntegerField(default=300, help_text="Maximum age of the queue and node information before an update from pbs is requested.")
    graphtype = models.CharField(max_length=20, choices=GRAPH_CHOICES, help_text="What framework for graphs should be used.")
    dpmtransfers = models.BooleanField(help_text="Should the dpm transfers be watched.")


    
# The only instance of GlobalConfiguration    
#globalConfiguration = GlobalConfiguration.objects.get(pk=1)
 
# vi:ts=4:sw=4:expandtab
